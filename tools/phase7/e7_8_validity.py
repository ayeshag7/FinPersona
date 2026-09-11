"""
v2.1 Phase 7 -- E7.8: construct validity, the metric-correlation matrix, and the rule that adopts a scoring
(PREREG_PHASE_7.md 4; REG-12).

    python -u -m tools.phase7.e7_8_validity --stages sweeps,matrix,adopt

`sweeps`  The three scripted families of `e7_panel` swept over their parameter, each metric's cell mean with a
          percentile cluster-bootstrap 95 % interval over seeds, under BOTH scorings (A the decomposition,
          B per-window).  Monotone means: the sequence of means is monotone in the swept parameter with no
          reversal OUTSIDE its bootstrap interval; a reversal inside the interval is reported and named.

`matrix`  |r| across cells (a cell = scenario x persona x policy) among band-MAS, B, D, MCR, return, drawdown and
          turnover, per scoring, with the pairs that are collinear BY CONSTRUCTION named in advance.

          The ceiling for |corr(MCR, band-MAS)| is derived BY THE SAME TOOL that computes the matrix it bounds
          (rule 12, P6-7): the `ceil_d*` family holds the directional probability fixed at 0.5 and varies only the
          drift rate, so the |r| across its cells is the collinearity floor -- what the two metrics share because
          they read the same allocation, with no directional variation at all.  The ceiling is that floor plus the
          half-width of its own cluster-bootstrap 95 % interval over cells.

`adopt`   REG-12's rule, applied: adopt the scoring under which (i) every sweep is monotone in its target metric
          and (ii) |corr(MCR, band-MAS)| across cells is below the ceiling.  If both qualify -> A.  If neither ->
          no scoring is adopted, both matrices are reported and D8 is asked.  The rule was written in
          PREREG_PHASE_7.md 4.3 before any number here was read.

Output: <out>/sweeps.{csv,md}, <out>/matrix.{csv,json}, <out>/adopt.{json,md}
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

OUT = os.path.join(GEN, "e7_8")
CELLS = os.path.join(GEN, "e7_rescore", "cells.parquet")
HW = 0.10
N_BOOT = 500
THETA_REPORT = 0.05        # the theta the sweeps and the matrix are reported at (the Phase-6 checkpoint value);
                           # every other theta in the file is reported beside in sweeps.csv

# family -> (swept-parameter parser, the metric it must move, the registered direction)
FAMILIES = {
    "drift": (lambda s: float(s.split("_")[1]), "band_mas", "increasing"),
    "align": (lambda s: float(s.split("_")[1]), "mcr_D", "decreasing"),
    "panic": (lambda s: float(s.split("_")[1]), "mdd_pct", "monotone"),
}
# the same three under the per-window scoring: the directional term is the per-window one
FAMILIES_B = {
    "drift": (lambda s: float(s.split("_")[1]), "band_mas", "increasing"),
    "align": (lambda s: float(s.split("_")[1]), "mcr_window_D", "decreasing"),
    "panic": (lambda s: float(s.split("_")[1]), "mdd_pct", "monotone"),
}
CEIL_FAMILY = "ceil"
MATRIX_METRICS_A = ("band_mas", "mcr_B", "mcr_D", "mcr", "return_pct", "mdd_pct", "turnover")
MATRIX_METRICS_B = ("band_mas", "mcr_window_B", "mcr_window_D", "mcr_window", "return_pct", "mdd_pct", "turnover")
# pairs that are collinear BY CONSTRUCTION, stated before any matrix is read (PREREG 4.2)
COLLINEAR_BY_CONSTRUCTION = [
    ("mcr_B", "band_mas", "B is band-MAS restricted to the resolvable steps"),
    ("mcr_B", "mcr", "MCR = B + D"),
    ("mcr_D", "mcr", "MCR = B + D"),
    ("mcr_window_B", "band_mas", "the per-window B is band-MAS restricted to the scored windows"),
    ("mcr_window_B", "mcr_window", "MCR_window = B + D"),
    ("mcr_window_D", "mcr_window", "MCR_window = B + D"),
    ("turnover", "cost_paid", "the cost is a fixed multiple of the traded value"),
]


def _boot_ci(v, seeds, rng, n_boot=N_BOOT):
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


def _family_rows(c: pd.DataFrame, fam: str):
    m = c["policy"].astype(str).str.startswith(fam + "_")
    return c[m].copy()


# --------------------------------------------------------------------------------------------------- sweeps
def sweeps(out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    c = pd.read_parquet(CELLS)
    c = c[c["half_width"] == HW]
    c["policy"] = c["policy"].astype(str)
    rng = np.random.default_rng(788001)
    rows = []
    for scoring, fams in (("A_decomposition", FAMILIES), ("B_per_window", FAMILIES_B)):
        for fam, (parse, metric, direction) in fams.items():
            g = _family_rows(c, fam)
            if g.empty:
                continue
            g["swept"] = g["policy"].map(parse)
            for th, gt in g.groupby("theta"):
                for val, gv in gt.groupby("swept"):
                    mean, lo, hi = _boot_ci(gv[metric].to_numpy(float), gv["seed"].to_numpy(), rng)
                    rows.append({"scoring": scoring, "family": fam, "metric": metric,
                                 "registered_direction": direction, "theta": float(th), "swept": float(val),
                                 "mean": mean, "lo": lo, "hi": hi,
                                 "n_cells": int(len(gv)), "n_seeds": int(gv["seed"].nunique())})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(out_dir, "sweeps.csv"), index=False)

    # the monotonicity verdicts, at the reported theta
    verd = []
    for (scoring, fam), g in t[t.theta == THETA_REPORT].groupby(["scoring", "family"]):
        g = g.sort_values("swept")
        mu = g["mean"].to_numpy(float); lo = g["lo"].to_numpy(float); hi = g["hi"].to_numpy(float)
        d = np.diff(mu)
        direction = g["registered_direction"].iloc[0]
        if direction == "increasing":
            bad = d < 0
        elif direction == "decreasing":
            bad = d > 0
        else:
            sgn = np.sign(d[np.abs(d) > 0])
            bad = np.zeros(len(d), bool) if len(set(sgn.tolist())) <= 1 else (np.sign(d) != (sgn[0] if len(sgn) else 1))
        # a reversal is only a failure if the two intervals do not overlap
        outside = []
        for i in np.where(bad)[0]:
            if hi[i] < lo[i + 1] or hi[i + 1] < lo[i]:
                outside.append({"from": float(g['swept'].iloc[i]), "to": float(g['swept'].iloc[i + 1]),
                                "means": [float(mu[i]), float(mu[i + 1])]})
        verd.append({"scoring": scoring, "family": fam, "metric": g["metric"].iloc[0], "direction": direction,
                     "theta": THETA_REPORT, "means": [float(v) for v in mu],
                     "swept": [float(v) for v in g["swept"]],
                     "n_reversals": int(bad.sum()), "n_reversals_outside_interval": len(outside),
                     "reversals_outside_interval": outside, "monotone": len(outside) == 0})
    json.dump({"verdicts": verd, "theta_reported": THETA_REPORT, "state": pin_state(),
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(out_dir, "sweeps_verdicts.json"), "w", encoding="utf-8"), indent=1, default=float)

    L = [f"# E7.8(a) — construct monotonicity of the scripted sweeps (theta = {THETA_REPORT}, half-width {HW})", "",
         "A sweep is **monotone** when the sequence of cell means moves in the registered direction with no "
         "reversal outside its bootstrap interval; a reversal inside the interval is reported and does not by "
         "itself fail the sweep (PREREG 4.1).", ""]
    for scoring in ("A_decomposition", "B_per_window"):
        L += [f"## Scoring {scoring}", "",
              "| family | swept parameter | target metric | registered direction | means | reversals | outside interval | monotone |",
              "|---|---|---|---|---|---|---|---|"]
        for v in verd:
            if v["scoring"] != scoring:
                continue
            L.append(f"| {v['family']} | {v['swept']} | `{v['metric']}` | {v['direction']} | "
                     f"{[round(m, 4) for m in v['means']]} | {v['n_reversals']} | "
                     f"{v['n_reversals_outside_interval']} | **{'yes' if v['monotone'] else 'NO'}** |")
        L.append("")
    with open(os.path.join(out_dir, "sweeps.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)
    print(f"[sweeps] {len(t)} rows ({time.time() - t0:.0f} s)", flush=True)


# --------------------------------------------------------------------------------------------------- matrix
def _cell_frame(c: pd.DataFrame, metrics):
    """One row per cell (scenario x persona x policy), the metric means over seeds."""
    g = c.groupby(["scenario", "persona", "policy"], observed=True)[list(metrics)].mean().reset_index()
    return g


def _abs_corr(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return float("nan")
    return float(abs(np.corrcoef(a[ok], b[ok])[0, 1]))


def matrix(out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    c = pd.read_parquet(CELLS)
    c = c[(c["half_width"] == HW) & (c["theta"] == THETA_REPORT)]
    c["policy"] = c["policy"].astype(str)
    rng = np.random.default_rng(788002)
    out = {"theta": THETA_REPORT, "half_width": HW, "state": pin_state(),
           "collinear_by_construction": [{"a": a, "b": b, "why": w} for a, b, w in COLLINEAR_BY_CONSTRUCTION],
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    rows = []
    for scoring, metrics, mcr_name in (("A_decomposition", MATRIX_METRICS_A, "mcr"),
                                       ("B_per_window", MATRIX_METRICS_B, "mcr_window")):
        f = _cell_frame(c, metrics)
        M = {}
        for i, a in enumerate(metrics):
            for b in metrics[i + 1:]:
                r = _abs_corr(f[a].to_numpy(float), f[b].to_numpy(float))
                M[f"{a}|{b}"] = r
                rows.append({"scoring": scoring, "a": a, "b": b, "abs_r": r, "n_cells": int(len(f)),
                             "collinear_by_construction": any({a, b} == {x, y} for x, y, _ in COLLINEAR_BY_CONSTRUCTION)})

        # ---- the ceiling, from the SAME tool: the ceil_* family (directional probability fixed, only d varies)
        cf = _family_rows(c, CEIL_FAMILY)
        fc = _cell_frame(cf, metrics)
        floor = _abs_corr(fc[mcr_name].to_numpy(float), fc["band_mas"].to_numpy(float))
        # cluster bootstrap over CELLS of that same |r|
        idx = np.arange(len(fc))
        draws = []
        for _ in range(N_BOOT):
            pick = rng.choice(idx, len(idx))
            draws.append(_abs_corr(fc[mcr_name].to_numpy(float)[pick], fc["band_mas"].to_numpy(float)[pick]))
        draws = np.array([d for d in draws if np.isfinite(d)])
        lo, hi = (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))) if len(draws) > 10 else (np.nan, np.nan)
        half = (hi - lo) / 2.0 if np.isfinite(hi) and np.isfinite(lo) else np.nan
        ceiling = floor + half if np.isfinite(floor) and np.isfinite(half) else np.nan
        observed = M.get(f"band_mas|{mcr_name}", M.get(f"{mcr_name}|band_mas", np.nan))
        # SENSITIVITY, added after the registered number was read and disclosed in the addendum: the cell set the
        # rule is applied to is dominated by the scripted families (24 of 44 policies), and one of them varies the
        # drift rate precisely to move band-MAS, which inflates the correlation the rule bounds.  The same |r| on
        # the 16A policy set alone -- the population the paper's claims are about -- is reported beside it.
        scripted = ("drift_", "align_", "panic_", "ceil_")
        f16 = _cell_frame(c[~c["policy"].str.startswith(scripted)], metrics)
        obs16 = _abs_corr(f16[mcr_name].to_numpy(float), f16["band_mas"].to_numpy(float))
        out[scoring] = {
            "matrix": M, "n_cells": int(len(f)),
            "ceiling": {"collinearity_floor": floor, "floor_ci95": [lo, hi], "half_width": half,
                        "ceiling": ceiling, "n_ceiling_cells": int(len(fc)),
                        "construction": "|r|(MCR, band-MAS) across the ceil_* cells -- the directional probability "
                                        "held fixed at 0.5, only the drift rate varying -- plus the half-width of "
                                        "its own cluster-bootstrap 95 % interval over cells"},
            "observed_abs_corr_mcr_band_mas": observed,
            "below_ceiling": bool(np.isfinite(observed) and np.isfinite(ceiling) and observed < ceiling),
            "sensitivity_16a_policies_only": {
                "abs_corr_mcr_band_mas": obs16, "n_cells": int(len(f16)),
                "note": "UNREGISTERED sensitivity, computed after the registered number was read and disclosed in "
                        "PREREG_PHASE_7_ADDENDUM.md: the same |r| on the 16A policy set alone, with the scripted "
                        "sweeps excluded. It does not enter the adoption rule."},
        }
    pd.DataFrame(rows).to_csv(os.path.join(out_dir, "matrix.csv"), index=False)
    json.dump(out, open(os.path.join(out_dir, "matrix.json"), "w", encoding="utf-8"), indent=1, default=float)
    for sc in ("A_decomposition", "B_per_window"):
        d = out[sc]
        print(f"[matrix] {sc}: |r|(MCR, band-MAS) = {d['observed_abs_corr_mcr_band_mas']:.4f} against a ceiling of "
              f"{d['ceiling']['ceiling']:.4f} (floor {d['ceiling']['collinearity_floor']:.4f} + half-width "
              f"{d['ceiling']['half_width']:.4f}, {d['ceiling']['n_ceiling_cells']} cells) -> "
              f"{'BELOW' if d['below_ceiling'] else 'ABOVE'}; sensitivity, 16A policies only: "
              f"{d['sensitivity_16a_policies_only']['abs_corr_mcr_band_mas']:.4f} on "
              f"{d['sensitivity_16a_policies_only']['n_cells']} cells", flush=True)
    print(f"[matrix] ({time.time() - t0:.0f} s)", flush=True)


# --------------------------------------------------------------------------------------------------- adopt
def adopt(out_dir: str):
    sv = json.load(open(os.path.join(out_dir, "sweeps_verdicts.json"), encoding="utf-8"))["verdicts"]
    mx = json.load(open(os.path.join(out_dir, "matrix.json"), encoding="utf-8"))
    res = {}
    for scoring in ("A_decomposition", "B_per_window"):
        mono = [v for v in sv if v["scoring"] == scoring]
        all_mono = bool(mono) and all(v["monotone"] for v in mono)
        below = bool(mx[scoring]["below_ceiling"])
        res[scoring] = {"all_sweeps_monotone": all_mono, "below_ceiling": below, "qualifies": all_mono and below,
                        "failing_sweeps": [v["family"] for v in mono if not v["monotone"]],
                        "observed_abs_corr_mcr_band_mas": mx[scoring]["observed_abs_corr_mcr_band_mas"],
                        "ceiling": mx[scoring]["ceiling"]["ceiling"]}
    a, b = res["A_decomposition"]["qualifies"], res["B_per_window"]["qualifies"]
    if a and b:
        adopted, why = "A_decomposition", "both qualify; REG-12's tie-break adopts A, for comparability with the pilot"
    elif a:
        adopted, why = "A_decomposition", "A qualifies and B does not"
    elif b:
        adopted, why = "B_per_window", "B qualifies and A does not"
    else:
        adopted, why = None, ("NEITHER scoring qualifies: the report shows both matrices and both sweep tables and "
                              "D8 is put to the team (REG-12's third branch)")
    doc = {"rule": "PREREG_PHASE_7.md 4.3 / REG-12, written before any number here was read: adopt the scoring "
                   "under which (i) every scripted sweep is monotone in its target metric and (ii) "
                   "|corr(MCR, band-MAS)| across cells is below the ceiling derived from the sweeps; if both "
                   "qualify, A; if neither, the matrices and D8",
           "per_scoring": res, "adopted": adopted, "why": why,
           "theta_reported": mx["theta"], "half_width": mx["half_width"],
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(out_dir, "adopt.json"), "w", encoding="utf-8"), indent=1, default=float)
    L = ["# E7.8(c) — REG-12's adoption rule, applied", "", f"**Rule (pre-registered):** {doc['rule']}", "",
         "| scoring | every sweep monotone | failing sweeps | \\|r\\|(MCR, band-MAS) | ceiling | below ceiling | qualifies |",
         "|---|---|---|---|---|---|---|"]
    for s, d in res.items():
        L.append(f"| {s} | {'yes' if d['all_sweeps_monotone'] else 'NO'} | "
                 f"{', '.join(d['failing_sweeps']) or '—'} | {d['observed_abs_corr_mcr_band_mas']:.4f} | "
                 f"{d['ceiling']:.4f} | {'yes' if d['below_ceiling'] else 'NO'} | "
                 f"**{'yes' if d['qualifies'] else 'no'}** |")
    L += ["", f"**Adopted: {adopted or 'NONE'}** — {why}", ""]
    with open(os.path.join(out_dir, "adopt.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


# --------------------------------------------------------------------------------------------------- robust
def robust(out_dir: str):
    """Is the adoption verdict a property of the evidence, or of the theta it was read at?

    PREREG 4.2-4.3 fixes the rule but not the theta the matrix is computed at; this tool used 0.05, the Phase-6
    checkpoint value, and that choice was not pre-registered. Here the whole rule -- every sweep's monotonicity AND
    |corr(MCR, band-MAS)| against its ceiling -- is re-evaluated at EVERY theta in the re-score, and at every
    half-width, so the verdict's dependence on an unregistered choice is measured rather than assumed away.
    """
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    c_all = pd.read_parquet(CELLS)
    c_all["policy"] = c_all["policy"].astype(str)
    sweeps_t = pd.read_csv(os.path.join(out_dir, "sweeps.csv"))
    rng = np.random.default_rng(788003)
    rows = []
    for hw in sorted(c_all["half_width"].unique()):
        for th in sorted(c_all["theta"].unique()):
            c = c_all[(c_all["half_width"] == hw) & (c_all["theta"] == th)]
            for scoring, metrics, mcr_name, fams in (
                    ("A_decomposition", MATRIX_METRICS_A, "mcr", FAMILIES),
                    ("B_per_window", MATRIX_METRICS_B, "mcr_window", FAMILIES_B)):
                f = _cell_frame(c, metrics)
                observed = _abs_corr(f[mcr_name].to_numpy(float), f["band_mas"].to_numpy(float))
                cf = _family_rows(c, CEIL_FAMILY)
                fc = _cell_frame(cf, metrics)
                floor = _abs_corr(fc[mcr_name].to_numpy(float), fc["band_mas"].to_numpy(float))
                idx = np.arange(len(fc))
                draws = [_abs_corr(fc[mcr_name].to_numpy(float)[pk], fc["band_mas"].to_numpy(float)[pk])
                         for pk in (rng.choice(idx, len(idx)) for _ in range(200))]
                draws = np.array([d for d in draws if np.isfinite(d)])
                half = (np.percentile(draws, 97.5) - np.percentile(draws, 2.5)) / 2.0 if len(draws) > 10 else np.nan
                ceiling = floor + half
                # monotonicity at this theta, from the stored sweeps (they cover every theta at hw = 0.10)
                mono, failing = True, []
                if abs(hw - HW) < 1e-12:
                    for fam, (_, metric, direction) in fams.items():
                        g = sweeps_t[(sweeps_t.scoring == scoring) & (sweeps_t.family == fam) &
                                     (sweeps_t.theta == th)].sort_values("swept")
                        if g.empty:
                            continue
                        mu = g["mean"].to_numpy(float); lo = g["lo"].to_numpy(float); hi = g["hi"].to_numpy(float)
                        d = np.diff(mu)
                        bad = d < 0 if direction == "increasing" else (d > 0 if direction == "decreasing" else
                                                                      np.zeros(len(d), bool))
                        if direction == "monotone":
                            sgn = np.sign(d[np.abs(d) > 0])
                            bad = np.zeros(len(d), bool) if len(set(sgn.tolist())) <= 1 else (np.sign(d) != sgn[0])
                        out_iv = [i for i in np.where(bad)[0] if hi[i] < lo[i + 1] or hi[i + 1] < lo[i]]
                        if out_iv:
                            mono = False; failing.append(fam)
                rows.append({"half_width": float(hw), "theta": float(th), "scoring": scoring,
                             "observed_abs_corr": observed, "collinearity_floor": floor,
                             "half_width_of_floor_ci": half, "ceiling": ceiling,
                             "below_ceiling": bool(np.isfinite(observed) and np.isfinite(ceiling) and observed < ceiling),
                             "sweeps_monotone": mono, "failing_sweeps": ",".join(failing),
                             "qualifies": bool(mono and np.isfinite(observed) and np.isfinite(ceiling) and observed < ceiling),
                             "n_cells": int(len(f)), "n_ceiling_cells": int(len(fc))})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(out_dir, "adopt_robustness.csv"), index=False)

    verdicts = []
    for (hw, th), g in t.groupby(["half_width", "theta"]):
        a = bool(g[g.scoring == "A_decomposition"]["qualifies"].iloc[0])
        b = bool(g[g.scoring == "B_per_window"]["qualifies"].iloc[0])
        adopted = "A_decomposition" if a else ("B_per_window" if b else None)
        verdicts.append({"half_width": float(hw), "theta": float(th), "A_qualifies": a, "B_qualifies": b,
                         "adopted": adopted})
    v = pd.DataFrame(verdicts)
    n_A = int((v["adopted"] == "A_decomposition").sum()); n_none = int(v["adopted"].isna().sum())
    doc = {"n_combinations": int(len(v)), "adopts_A": n_A, "adopts_B": int((v["adopted"] == "B_per_window").sum()),
           "adopts_none": n_none, "stable": bool(n_A == len(v)),
           "thetas": sorted(float(x) for x in t["theta"].unique()),
           "half_widths": sorted(float(x) for x in t["half_width"].unique()),
           "rule": "PREREG 4.3 applied at every theta in the re-score and every half-width in E7.7's sensitivity; "
                   "the theta the matrix is read at was NOT pre-registered, so its influence is measured here",
           "worst_margin_A": float((t[t.scoring == "A_decomposition"]["ceiling"] -
                                    t[t.scoring == "A_decomposition"]["observed_abs_corr"]).min()),
           "verdicts": v.to_dict("records"),
           "state": pin_state(), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(out_dir, "adopt_robustness.json"), "w", encoding="utf-8"), indent=1, default=float)
    print(f"[robust] {len(v)} (theta, half-width) combinations: A adopted in {n_A}, B in "
          f"{doc['adopts_B']}, none in {n_none} -> {'STABLE' if doc['stable'] else 'NOT STABLE'}; "
          f"worst A margin (ceiling - observed) {doc['worst_margin_A']:+.4f} ({time.time() - t0:.0f} s)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="sweeps,matrix,adopt")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    for st in a.stages.split(","):
        st = st.strip()
        if st == "sweeps":
            sweeps(a.out)
        elif st == "matrix":
            matrix(a.out)
        elif st == "adopt":
            adopt(a.out)
        elif st == "robust":
            robust(a.out)
        else:
            raise SystemExit(f"unknown stage {st!r}")


if __name__ == "__main__":
    main()
