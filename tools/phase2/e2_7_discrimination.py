"""
E2.7 (post-review extension, PREREG_PHASE_2_ADDENDUM.md section 4.1): does the benchmark still discriminate
between policies under the adopted engine?

Phase 2 reports that the resolvable share in flat falls from 0.73 to 0.13.  If |x| >= theta on one day in eight,
the mandate-conditional oracle and the trivial policies converge and the metric cannot rank agents -- which no
amount of leakage work or persona design would fix.  This module reads the L5 runs (`tools/l5_report.py`, 40
training seeds disjoint from the 50 scored seeds, three personas x four scenarios) on the handed-over state and
on the state Phase 1 handed over, and reports the ordering and the SPREAD with cluster-bootstrap intervals over
seeds -- the shape 16A's G1 is written in.

No pass/fail: G1 is Phase 6's gate on the Phase-6 frozen generator.  What is reported is the ordering, the gaps
and their intervals, per scenario, before and after.

    python -m tools.phase2.e2_7_discrimination [--n-boot 2000]
Outputs: docs/env_v2/generated/v2_1/e2_7/discrimination.json, discrimination.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e2_7")
SCEN = ("flat", "crash", "bull_trap", "sustained_bull")
TRIVIAL = ("always_hold", "constant_mix")
ORACLE = "mandate_conditional_oracle"
L5S = ("L5_full", "L5_price_only", "L5_level_free")
MCR = "mcr_0.05"


def _boot_mean(v, n_boot, rng):
    idx = rng.integers(0, len(v), (n_boot, len(v)))
    return v[idx].mean(axis=1)


def summarise(csv, label, n_boot, seed=11):
    d = pd.read_csv(csv)
    rng = np.random.default_rng(seed)
    out = {"label": label, "file": os.path.relpath(csv, ROOT), "n_rows": int(len(d)),
           "n_seeds": int(d["seed"].nunique()), "personas": sorted(d["persona"].unique().tolist()),
           "scenarios": {}}
    for sc in SCEN:
        s = d[d.scenario == sc]
        if s.empty:
            continue
        # cluster the bootstrap by seed: every policy is resampled on the same seeds, so the gaps are paired
        # MCR is UNDEFINED on a run with no resolvable step (|x| >= theta never occurs), and every policy is
        # undefined on exactly the same runs.  Those persona x seed cells are dropped from the means and their
        # share is reported, because at the fitted coverage it is not negligible.
        s = s.copy()
        s["cell"] = s["persona"].astype(str) + "|" + s["seed"].astype(str)
        undefined = sorted(s.loc[s[MCR].isna(), "cell"].unique())
        n_cells = int(s["cell"].nunique())
        s = s[~s["cell"].isin(undefined)]
        cells = np.sort(s["cell"].unique())
        by = {p: s[s.policy == p].set_index("cell")[MCR].reindex(cells).to_numpy() for p in s.policy.unique()}
        cov = float(s["coverage_0.05"].mean())
        seeds = cells
        idx = rng.integers(0, len(cells), (n_boot, len(cells)))

        def stat(v):
            b = v[idx].mean(axis=1)
            return {"mean": float(np.mean(v)), "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]}

        l5_best = min((p for p in L5S if p in by), key=lambda p: np.mean(by[p]))
        triv_best = min((p for p in TRIVIAL if p in by), key=lambda p: np.mean(by[p]))
        gap_oracle_l5 = by[l5_best] - by[ORACLE]
        gap_l5_triv = by[triv_best] - by[l5_best]
        row = {"coverage_0.05": cov,
               "n_cells": n_cells, "n_cells_undefined_mcr": len(undefined),
               "share_runs_with_no_resolvable_step": len(undefined) / max(n_cells, 1),
               "oracle": stat(by[ORACLE]), "L5_best_policy": l5_best, "L5_best": stat(by[l5_best]),
               "trivial_best_policy": triv_best, "trivial_best": stat(by[triv_best]),
               "per_policy": {p: stat(v) for p, v in sorted(by.items())},
               "gap_oracle_to_L5": stat(gap_oracle_l5), "gap_L5_to_trivial": stat(gap_l5_triv)}
        row["ordering_holds"] = bool(row["oracle"]["mean"] < row["L5_best"]["mean"] < row["trivial_best"]["mean"])
        row["gaps_both_positive_at_95"] = bool(row["gap_oracle_to_L5"]["ci95"][0] > 0
                                               and row["gap_L5_to_trivial"]["ci95"][0] > 0)
        out["scenarios"][sc] = row
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    res = {"what": "E2.7: the policy spread (16A G1's shape) on the handed-over state, beside Phase 1's, on the "
                   "same L5 design (40 training seeds, 50 scored seeds, three personas x four scenarios).",
           "rule": "no pass/fail -- G1 is Phase 6's gate on the Phase-6 frozen generator; the ordering, the gaps "
                   "and their cluster-bootstrap intervals are reported, and a collapse in any scenario is stated "
                   "as a finding for the team rather than repaired here.",
           "states": {}}
    for key, csv, label in (("phase2_after", os.path.join(OUT, "l5_phase2_after.csv"),
                             "Phase 2 hand-over (engine ar1_fit, sigma_V 0.0122)"),
                            ("phase1_after", os.path.join(GEN, "e1_6", "l5_after.csv"),
                             "Phase 1 hand-over (engine fw_fallback_hl150, sigma_V 0.006)")):
        if os.path.exists(csv):
            res["states"][key] = summarise(csv, label, a.n_boot)
    with open(os.path.join(OUT, "discrimination.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    L = ["# E2.7 does the benchmark still discriminate? (post-review extension; "
         "PREREG_PHASE_2_ADDENDUM.md section 4.1)", "", res["what"], "", f"**Rule:** {res['rule']}", "",
         "MCR at theta = 0.05, averaged over three personas and 50 scored seeds; intervals are a "
         f"{a.n_boot}-resample cluster bootstrap over seeds, with every policy resampled on the same seeds so "
         "the gaps are paired.", ""]
    for key, st in res["states"].items():
        L += [f"## {st['label']}", "",
              "| scenario | coverage | runs with NO resolvable step | mandate oracle | best L5 | best trivial | gap oracle->L5 | gap L5->trivial | ordering | both gaps > 0 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for sc, r in st["scenarios"].items():
            L.append(
                f"| {sc} | {r['coverage_0.05']:.3f} | "
                f"{r['n_cells_undefined_mcr']}/{r['n_cells']} ({r['share_runs_with_no_resolvable_step']:.0%}) | "
                f"{r['oracle']['mean']:.4f} | "
                f"{r['L5_best']['mean']:.4f} ({r['L5_best_policy'].replace('L5_', '')}) | "
                f"{r['trivial_best']['mean']:.4f} ({r['trivial_best_policy']}) | "
                f"{r['gap_oracle_to_L5']['mean']:.4f} [{r['gap_oracle_to_L5']['ci95'][0]:.4f}, "
                f"{r['gap_oracle_to_L5']['ci95'][1]:.4f}] | "
                f"{r['gap_L5_to_trivial']['mean']:.4f} [{r['gap_L5_to_trivial']['ci95'][0]:.4f}, "
                f"{r['gap_L5_to_trivial']['ci95'][1]:.4f}] | "
                f"{'yes' if r['ordering_holds'] else '**no**'} | "
                f"{'yes' if r['gaps_both_positive_at_95'] else '**no**'} |")
        L.append("")
    if len(res["states"]) == 2:
        a2, a1 = res["states"]["phase2_after"], res["states"]["phase1_after"]
        L += ["## The change, scenario by scenario", "",
              "| scenario | coverage before -> after | runs with no resolvable step | gap L5->trivial before -> after |",
              "|---|---|---|---|"]
        for sc in SCEN:
            if sc in a1["scenarios"] and sc in a2["scenarios"]:
                L.append(f"| {sc} | {a1['scenarios'][sc]['coverage_0.05']:.3f} -> "
                         f"{a2['scenarios'][sc]['coverage_0.05']:.3f} | "
                         f"{a1['scenarios'][sc]['share_runs_with_no_resolvable_step']:.0%} -> "
                         f"{a2['scenarios'][sc]['share_runs_with_no_resolvable_step']:.0%} | "
                         f"{a1['scenarios'][sc]['gap_L5_to_trivial']['mean']:.4f} -> "
                         f"{a2['scenarios'][sc]['gap_L5_to_trivial']['mean']:.4f} |")
    with open(os.path.join(OUT, "discrimination.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L[6:]))
    print("written", OUT)


if __name__ == "__main__":
    main()
