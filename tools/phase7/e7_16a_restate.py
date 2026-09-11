"""
v2.1 Phase 7 -- 16A re-stated under the Phase-7 scorings, BESIDE the Phase-6 verdict, never in place of it
(PREREG_PHASE_7.md 2.4; hard rule 2).

    python -u -m tools.phase7.e7_16a_restate

The checkpoint was computed and reported in Phase 6 (`e6_16a/16A.{json,md}`; DECISION_LOG P6-11): G1, G2, G4a and
G4b FAIL, G3 PASSES.  **That verdict stands.**  What this tool adds is what the decomposition makes visible --
G1, G2 and G4a re-computed on the band-violation term B, on the directional term D, and under the per-window
scoring, on the same seeds with the same cluster bootstrap.  It is a reported consequence of a scoring, labelled
as such.  No scoring is adopted here and no gate's verdict is replaced: the adoption rule is E7.8's.

G4b is NOT re-stated: it is a statement about a surrogate's R2 against the Appendix-B bound and has nothing to do
with a scoring (`e6_6/bound.json`).

Output: <out>/restate.{csv,json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN, pin_state  # noqa: E402

OUT = os.path.join(GEN, "e7_16a")
CELLS = os.path.join(GEN, "e7_rescore", "cells.parquet")
E6 = os.path.join(GEN, "e6_16a", "16A.json")
HW = 0.10
N_BOOT = 500
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
TRIVIAL = ("always_hold", "band_lo", "band_hi", "random")
ORACLE = "mandate_conditional_oracle"
L5_FULL = "L5_full_level_free"
L5_PRICE = "L5_level_free"
METRICS = ("mcr", "mcr_B", "mcr_D", "mcr_window")


def _boot(v, seeds, rng, n_boot=N_BOOT):
    """Percentile cluster bootstrap over seeds of a mean -- `tools/phase6/e6_16a._boot_mean`'s statistic, computed
    from per-cluster sums and counts so that 500 resamples of 100 clusters is one array op rather than 50,000
    concatenations (the un-vectorised form ran for minutes per table)."""
    v = np.asarray(v, float); seeds = np.asarray(seeds)
    ok = np.isfinite(v); v, seeds = v[ok], seeds[ok]
    if len(v) < 3:
        return (float("nan"),) * 3
    us, inv = np.unique(seeds, return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(us))
    cnts = np.bincount(inv, minlength=len(us)).astype(float)
    pick = rng.integers(0, len(us), size=(n_boot, len(us)))
    tot = cnts[pick].sum(axis=1)
    draws = np.where(tot > 0, sums[pick].sum(axis=1) / np.maximum(tot, 1e-12), np.nan)
    d = draws[np.isfinite(draws)]
    if len(d) < 10:
        return (float(np.mean(v)), float("nan"), float("nan"))
    return float(np.mean(v)), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def gate_verdicts(c: pd.DataFrame, best_rule: str, rng) -> dict:
    """G1 / G2 / G4a on one (theta, half-width) slice, for each statistic."""
    out = {}
    for metric in METRICS:
        per = {}
        for sc in SCENARIOS:
            g = c[c.scenario == sc]
            tab = {}
            for pol, gg in g.groupby("policy"):
                m, lo, hi = _boot(gg[metric].to_numpy(float), gg["seed"].to_numpy(), rng)
                tab[pol] = {"mean": m, "ci95": [lo, hi]}
            triv = min((k for k in TRIVIAL if k in tab), key=lambda k: tab[k]["mean"])
            tab["_best_trivial"] = triv
            per[sc] = tab

        def sep(x, y):
            return x["ci95"][1] < y["ci95"][0]
        G1 = {sc: bool(sep(t[ORACLE], t[L5_FULL]) and sep(t[L5_FULL], t[t["_best_trivial"]])) for sc, t in per.items()}
        G2 = {sc: bool(sep(t[L5_FULL], t[best_rule])) for sc, t in per.items()}
        G4a = {sc: bool(sep(t[L5_FULL], t[L5_PRICE])) for sc, t in per.items()}
        out[metric] = {"G1_n_pass": int(sum(G1.values())), "G1": all(G1.values()),
                       "G2_n_pass": int(sum(G2.values())), "G2": int(sum(G2.values())) >= 3,
                       "G4a_n_pass": int(sum(G4a.values())), "G4a": all(G4a.values()),
                       "best_trivial": {sc: per[sc]["_best_trivial"] for sc in SCENARIOS}}
    return out


def sensitivity(out_dir: str):
    """E7.7's half-width sensitivity {0.05, 0.10, 0.15} applied where it bites: the gates and the decomposition.

    The half-width is a DESIGN parameter (no source could be read for it), so every verdict that depends on it has
    to be shown at all three values, not only at the one in force.  The band CENTRE is unchanged; only the width
    moves, so B and D redistribute while MCR against the same oracle does not have to.
    """
    t0 = time.time()
    c_all = pd.read_parquet(CELLS)
    c_all["policy"] = c_all["policy"].astype(str); c_all["scenario"] = c_all["scenario"].astype(str)
    rules = json.load(open(os.path.join(GEN, "e6_16a", "rules.json"), encoding="utf-8"))
    best_rule = f"rule_{rules['best_family']}"
    rng = np.random.default_rng(716002)
    rows = []
    for hw in sorted(c_all["half_width"].unique()):
        for th in sorted(c_all["theta"].unique()):
            c = c_all[(c_all["half_width"] == hw) & (c_all["theta"] == th)]
            v = gate_verdicts(c, best_rule, rng)
            o = c[c.policy == ORACLE]
            g3 = all(float(np.median(o[o.scenario == sc]["oracle_switches"])) >= 2 and
                     float(np.mean(o[o.scenario == sc]["oracle_switches"] >= 2)) >= 0.5
                     for sc in SCENARIOS if sc != "flat")
            l5 = c[c.policy == L5_FULL]
            rows.append({"half_width": float(hw), "theta": float(th), "G3_daily": bool(g3),
                         "L5_mcr": float(l5["mcr"].mean()), "L5_B": float(l5["mcr_B"].mean()),
                         "L5_D": float(l5["mcr_D"].mean()),
                         **{f"{m}_{k}": v[m][k] for m in METRICS for k in ("G1", "G2", "G4a")}})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(out_dir, "half_width_sensitivity.csv"), index=False)
    gate_cols = [c for c in t.columns if c.endswith(("_G1", "_G2", "_G4a"))]
    any_pass = t[gate_cols].any().any()
    doc = {"half_widths": sorted(float(x) for x in t["half_width"].unique()),
           "thetas": sorted(float(x) for x in t["theta"].unique()),
           "n_combinations": int(len(t)),
           "any_gate_passes_anywhere": bool(any_pass),
           "gates_checked": gate_cols,
           "G3_daily_passes_at": [{"half_width": float(r["half_width"]), "theta": float(r["theta"])}
                                  for _, r in t[t["G3_daily"]].iterrows()],
           "note": "the half-width is DESIGN (E7.7); every verdict that depends on it is shown at all three values",
           "state": pin_state(), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(out_dir, "half_width_sensitivity.json"), "w", encoding="utf-8"),
              indent=1, default=float)
    print(f"[sensitivity] {len(t)} (half-width, theta) combinations x 4 statistics x 3 gates: "
          f"any gate passing anywhere = {any_pass}; G3 daily passes in "
          f"{int(t['G3_daily'].sum())} of {len(t)} ({time.time() - t0:.0f} s)", flush=True)
    for hw in doc["half_widths"]:
        g = t[t.half_width == hw]
        l5 = g[np.isclose(g.theta, 0.05)]
        print(f"   half-width {hw:.2f}: at theta 0.05 the observables oracle reads MCR {float(l5['L5_mcr'].iloc[0]):.4f} "
              f"= B {float(l5['L5_B'].iloc[0]):.4f} + D {float(l5['L5_D'].iloc[0]):.4f}; "
              f"G3 daily passes at {int(g['G3_daily'].sum())} of {len(g)} thetas", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--stages", default="restate")
    ap.add_argument("--theta", type=float, default=0.05)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if "sensitivity" in a.stages and "restate" not in a.stages:
        return sensitivity(a.out)
    t0 = time.time()
    c = pd.read_parquet(CELLS)
    c = c[(c["half_width"] == HW) & (c["theta"] == a.theta)]
    c["policy"] = c["policy"].astype(str); c["scenario"] = c["scenario"].astype(str)
    rules = json.load(open(os.path.join(GEN, "e6_16a", "rules.json"), encoding="utf-8"))
    best_rule = f"rule_{rules['best_family']}"
    e6 = json.load(open(E6, encoding="utf-8"))
    g6 = e6["summary"]["G"][str(a.theta)]
    rng = np.random.default_rng(716001)

    rows, verdicts = [], {}
    for metric in METRICS:
        per = {}
        for sc in SCENARIOS:
            g = c[c.scenario == sc]
            tab = {}
            for pol, gg in g.groupby("policy"):
                m, lo, hi = _boot(gg[metric].to_numpy(float), gg["seed"].to_numpy(), rng)
                tab[pol] = {"mean": m, "ci95": [lo, hi], "n_runs": int(len(gg)), "n_seeds": int(gg["seed"].nunique())}
                rows.append({"metric": metric, "scenario": sc, "policy": pol, "mean": m, "lo": lo, "hi": hi,
                             "n_runs": int(len(gg)), "theta": a.theta})
            triv = min((k for k in TRIVIAL if k in tab), key=lambda k: tab[k]["mean"])
            tab["_best_trivial"] = triv
            per[sc] = tab

        def sep(x, y):
            return x["ci95"][1] < y["ci95"][0]
        G1 = {sc: bool(sep(t[ORACLE], t[L5_FULL]) and sep(t[L5_FULL], t[t["_best_trivial"]])) for sc, t in per.items()}
        G2 = {sc: bool(sep(t[L5_FULL], t[best_rule])) for sc, t in per.items()}
        G4a = {sc: bool(sep(t[L5_FULL], t[L5_PRICE])) for sc, t in per.items()}
        verdicts[metric] = {
            "G1": {"per_scenario": G1, "pass": all(G1.values()), "n_pass": int(sum(G1.values()))},
            "G2": {"per_scenario": G2, "pass": int(sum(G2.values())) >= 3, "n_pass": int(sum(G2.values())),
                   "best_rule": best_rule},
            "G4a": {"per_scenario": G4a, "pass": all(G4a.values()), "n_pass": int(sum(G4a.values()))},
            "best_trivial": {sc: per[sc]["_best_trivial"] for sc in SCENARIOS},
        }

    # G3 -- the switch count, under the daily oracle and under the per-window one
    g3 = {}
    for name, col in (("daily", "oracle_switches"), ("per_window", "window_switches")):
        d = {}
        for sc in SCENARIOS:
            v = c[(c.scenario == sc) & (c.policy == ORACLE)][col].to_numpy(float)
            d[sc] = {"median_switches": float(np.median(v)), "share_ge2": float(np.mean(v >= 2)), "n_runs": int(len(v))}
        ev = [sc for sc in SCENARIOS if sc != "flat"]
        g3[name] = {"per_scenario": d,
                    "pass": all(d[sc]["median_switches"] >= 2 and d[sc]["share_ge2"] >= 0.5 for sc in ev)}

    pd.DataFrame(rows).to_csv(os.path.join(a.out, "restate.csv"), index=False)
    doc = {"meta": {"theta": a.theta, "half_width": HW, "n_boot": N_BOOT, "state": pin_state(),
                    "cells": os.path.relpath(CELLS, ROOT),
                    "rule": "PREREG_PHASE_7.md 2.4 / hard rule 2: 16A is re-computed under a scoring as a REPORTED "
                            "CONSEQUENCE, labelled as such, beside the Phase-6 verdict, with the same seeds and the "
                            "same intervals -- never as a replacement for it",
                    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
           "phase6_verdict": {"G1": g6["G1"]["pass"], "G2": g6["G2"]["pass"], "G3": g6["G3"]["pass"],
                              "G4a": g6["G4a"]["pass"], "G4b": e6["summary"].get("G4b", {}).get("pass"),
                              "source": "e6_16a/16A.json (DECISION_LOG P6-11); it stands"},
           "restated": verdicts, "G3": g3}
    json.dump(doc, open(os.path.join(a.out, "restate.json"), "w", encoding="utf-8"), indent=1, default=float)

    L = [f"# 16A re-stated under the Phase-7 scorings (theta = {a.theta}) — a reported consequence, beside the "
         f"Phase-6 verdict", "",
         "**The Phase-6 verdict stands** (`e6_16a/16A.json`, DECISION_LOG P6-11): "
         f"G1 {'PASS' if g6['G1']['pass'] else 'FAIL'}, G2 {'PASS' if g6['G2']['pass'] else 'FAIL'}, "
         f"G3 {'PASS' if g6['G3']['pass'] else 'FAIL'}, G4a {'PASS' if g6['G4a']['pass'] else 'FAIL'}, "
         f"G4b {'PASS' if e6['summary'].get('G4b', {}).get('pass') else 'FAIL'}. "
         "Nothing below replaces it; the decomposition is reported because it says *where* each failure sits.", "",
         "| statistic the gate is read on | G1 (oracle < observables < trivial, 4 of 4) | G2 (rule above the "
         "observables oracle, ≥ 3 of 4) | G4a (observables oracle beats price-only, 4 of 4) |",
         "|---|---|---|---|"]
    label = {"mcr": "MCR — the Phase-6 statistic", "mcr_B": "B, the band-violation term",
             "mcr_D": "D, the directional term", "mcr_window": "MCR per 25-day window (REG-12 B)"}
    for m in METRICS:
        v = verdicts[m]
        L.append(f"| {label[m]} | {v['G1']['n_pass']} of 4 — **{'PASS' if v['G1']['pass'] else 'FAIL'}** | "
                 f"{v['G2']['n_pass']} of 4 — **{'PASS' if v['G2']['pass'] else 'FAIL'}** | "
                 f"{v['G4a']['n_pass']} of 4 — **{'PASS' if v['G4a']['pass'] else 'FAIL'}** |")
    L += ["", "## G3 — the oracle's target switches per run", "",
          "| reading | " + " | ".join(SCENARIOS) + " | verdict |", "|---|" + "---|" * (len(SCENARIOS) + 1)]
    for name in ("daily", "per_window"):
        d = g3[name]["per_scenario"]
        L.append(f"| {name} | " + " | ".join(f"median {d[sc]['median_switches']:.0f}, share "
                                             f"{d[sc]['share_ge2']:.2f}" for sc in SCENARIOS) +
                 f" | **{'PASS' if g3[name]['pass'] else 'FAIL'}** |")
    L += ["", "The best trivial policy per scenario, which is what G1's third leg is measured against:", "",
          "| statistic | " + " | ".join(SCENARIOS) + " |", "|---|" + "---|" * len(SCENARIOS)]
    for m in METRICS:
        L.append(f"| {label[m]} | " + " | ".join(verdicts[m]["best_trivial"][sc] for sc in SCENARIOS) + " |")
    L.append("")
    with open(os.path.join(a.out, "restate.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)
    print(f"[restate] ({time.time() - t0:.0f} s)", flush=True)
    if "sensitivity" in a.stages:
        sensitivity(a.out)


if __name__ == "__main__":
    main()
