"""
E2.8 (post-review extension, PREREG_PHASE_2_ADDENDUM.md section 4): is the level-free surrogate optimistically
biased, or is the excess over the Appendix-B bound a real channel?

The Appendix-B bound is EXACT for one process: log P_t = log V_t + x_t with log V a Gaussian random walk of
daily sd sigma_V and x a Gaussian AR(1) with rho = 2^(-1/h) and stationary sd s_x, read by an observer who sees
only returns.  Since E2.4 adopted an AR(1) engine, the generator is now that model plus events, jumps, GARCH and
the sentiment feedback -- so the bound is no longer an approximation, and the level-free surrogate sitting above
it (0.339 [0.208, 0.434] against 0.245 on the standard evaluation panel) has exactly two explanations:

  (a) the SURROGATE is optimistically biased -- its feature construction, lag block or cross-validation leaks;
  (b) the GENERATOR has an information channel the bound does not model (events, jumps, GARCH, sentiment).

This module distinguishes them.  It simulates the EXACT process -- nothing else -- builds the SAME level-free
feature set the audit builds (`technicals_block` on the price path, then `add_level_free_columns` and the lag
block), fits the SAME three surrogates with the SAME GroupKFold-by-path cross-validation, and compares the
measured R2(x) with the analytic bound at the same parameters.

Rule, fixed before the run: if the measured R2's 95 % interval lies ENTIRELY ABOVE the bound's window average,
explanation (a) holds and every level-free leakage number in the programme is affected; if it does not, (a) is
not supported and the generator's excess is (b), to be characterised by Phase 6.

    python -m tools.phase2.e2_8_bound_check [--n-paths 200] [--T 200]
Outputs: docs/env_v2/generated/v2_1/e2_4/bound_check.json, bound_check.md
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_4")
SEED0 = 160000
# (label, sigma_V, s_x, h) -- the parameters in force first, then two contrasting points so the check is not a
# single-point comparison: a high-bound configuration (the v2 state) and a low-bound one (the panel's own fit).
CASES = [
    ("in force (Phase 2: sigma_V 0.0122, s_x 0.0386, h 7.5)", 0.012203561517323533, 0.0386, 7.498029274686622),
    ("the v2 state Phase 1 handed over (0.006, 0.175, 150)", 0.006, 0.175, 150.0),
    ("the panel's own fit (estimator C corrected: 0.0196, 0.0250, 4.82)", 0.019572, 0.02498, 4.824),
]


def simulate_exact(n_paths: int, T: int, sigma_V: float, s_x: float, h: float, seed: int) -> pd.DataFrame:
    """The bound's model and nothing else: Gaussian random-walk log V, Gaussian AR(1) x started from its
    STATIONARY prior (which is the prior the bound's Kalman filter starts from), log P = log V + x."""
    from envs.v2.observables import technicals_block
    rng = np.random.default_rng(seed)
    rho = 2.0 ** (-1.0 / h)
    eta = rng.standard_normal((T, n_paths)) * (s_x * math.sqrt(1.0 - rho ** 2))
    x = np.empty((T, n_paths))
    x[0] = rng.standard_normal(n_paths) * s_x                      # stationary prior
    for t in range(1, T):
        x[t] = rho * x[t - 1] + eta[t]
    dlv = rng.standard_normal((T, n_paths)) * sigma_V
    logV = np.cumsum(dlv, axis=0)
    P = np.exp(logV + x) * 100.0
    V = np.exp(logV) * 100.0
    frames = []
    for i in range(n_paths):
        tech = technicals_block(P[:, i])
        frames.append(pd.DataFrame({
            "scenario": "exact", "seed": SEED0 + i, "day": np.arange(1, T + 1), "phase": "calm", "macro": "calm",
            "V": V[:, i], "P": P[:, i], "price": P[:, i], "x": x[:, i],
            **{k: tech[k] for k in ("SMA20", "SMA50", "RSI14", "MACD", "MACD_signal",
                                    "trend_strength", "trend_regime")}}))
    return pd.concat(frames, ignore_index=True)


def run_case(label, sigma_V, s_x, h, n_paths, T, seed):
    from evaluation.leakage_audit import l2_surrogate
    from tools.phase1.kalman_bound import kalman_bound
    t0 = time.time()
    panel = simulate_exact(n_paths, T, sigma_V, s_x, h, seed)
    shown = ["price", "SMA20", "SMA50", "RSI14", "MACD", "MACD_signal", "trend_strength", "trend_regime"]
    l2 = l2_surrogate(panel, shown, control="level_free")
    rows = l2[(l2.target == "x") & (l2.phase_group == "all") & (l2.feature_set == "price_only")]
    best = rows.loc[rows["R2"].idxmax()]
    full = l2[(l2.target == "x") & (l2.phase_group == "all") & (l2.feature_set == "full")]
    best_full = full.loc[full["R2"].idxmax()]
    b = kalman_bound(sigma_V, s_x, h, T=T)
    return {
        "label": label, "sigma_V": sigma_V, "s_x": s_x, "h": h, "n_paths": n_paths, "T": T, "seed": seed,
        "bound_window_avg": b["window_avg"], "bound_day_T": b["day_T"], "bound_steady_state": b["steady_state"],
        "levelfree_best_model": str(best["model"]), "levelfree_R2": float(best["R2"]),
        "levelfree_ci95": [float(best["R2_lo"]), float(best["R2_hi"])],
        "fullfield_best_model": str(best_full["model"]), "fullfield_R2": float(best_full["R2"]),
        "levelfree_all_models": {str(r["model"]): float(r["R2"]) for _, r in rows.iterrows()},
        "exceeds_bound_significantly": bool(float(best["R2_lo"]) > b["window_avg"]),
        "realised_sd_x": float(panel["x"].std()), "n_rows": int(len(panel)),
        "seconds": round(time.time() - t0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-paths", type=int, default=200)
    ap.add_argument("--T", type=int, default=200)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    res = {"what": __doc__.strip().split("\n\n")[0],
           "rule": "if the 95 % interval of the measured level-free R2(x) lies entirely above the analytic "
                   "window-average bound, the surrogate is optimistically biased (explanation a); otherwise (a) "
                   "is not supported and the generator's excess is an unmodelled channel (explanation b)",
           "design": {"process": "Gaussian random-walk log V + Gaussian AR(1) x from its stationary prior; no "
                                 "events, jumps, GARCH or sentiment feedback",
                      "features": "technicals_block on the price path, then the audit's own "
                                  "add_level_free_columns and 5-lag block -- identical to the SEP audit",
                      "estimators": "evaluation.leakage_audit.l2_surrogate, control='level_free', GroupKFold by "
                                    "path, 500-resample cluster bootstrap",
                      "n_paths": a.n_paths, "T": a.T, "seed0": SEED0},
           "cases": []}
    for i, (label, sv, sx, h) in enumerate(CASES):
        r = run_case(label, sv, sx, h, a.n_paths, a.T, SEED0 + 1000 * i)
        res["cases"].append(r)
        print(f"{label}\n   bound(window) {r['bound_window_avg']:.3f}  measured {r['levelfree_R2']:.3f} "
              f"[{r['levelfree_ci95'][0]:.3f}, {r['levelfree_ci95'][1]:.3f}] ({r['levelfree_best_model']})  "
              f"exceeds significantly: {r['exceeds_bound_significantly']}  ({r['seconds']} s)", flush=True)
    res["verdict"] = ("SURROGATE BIASED (explanation a)" if any(c["exceeds_bound_significantly"] for c in res["cases"])
                      else "surrogate not shown to be biased (explanation a not supported)")
    with open(os.path.join(OUT, "bound_check.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    L = ["# E2.8 does the level-free surrogate exceed an EXACT Appendix-B bound? "
         "(post-review extension; PREREG_PHASE_2_ADDENDUM.md section 4)", "",
         res["what"], "", f"**Rule (fixed before the run):** {res['rule']}.", "",
         f"Design: {res['design']['process']}. Features: {res['design']['features']}. "
         f"Estimators: {res['design']['estimators']}. {a.n_paths} paths x {a.T} days per case, seeds from {SEED0}.", "",
         "| configuration | sigma_V | s_x | h | bound (window avg) | bound (steady state) | measured level-free R2(x) | best model | interval entirely above the bound? |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c in res["cases"]:
        L.append(f"| {c['label']} | {c['sigma_V']:.4f} | {c['s_x']:.4f} | {c['h']:.2f} | {c['bound_window_avg']:.3f} | "
                 f"{c['bound_steady_state']:.3f} | {c['levelfree_R2']:.3f} [{c['levelfree_ci95'][0]:.3f}, "
                 f"{c['levelfree_ci95'][1]:.3f}] | {c['levelfree_best_model']} | "
                 f"{'**YES**' if c['exceeds_bound_significantly'] else 'no'} |")
    L += ["", f"**Verdict: {res['verdict']}.**", "",
          "Per-model level-free R2(x) in each case (the audit reports the best; the spread is shown so a single "
          "estimator's behaviour is visible):", "",
          "| configuration | " + " | ".join(sorted(res["cases"][0]["levelfree_all_models"])) + " |",
          "|---|" + "---|" * len(res["cases"][0]["levelfree_all_models"])]
    for c in res["cases"]:
        L.append(f"| {c['label']} | " + " | ".join(f"{c['levelfree_all_models'][m]:.3f}"
                                                   for m in sorted(c["levelfree_all_models"])) + " |")
    with open(os.path.join(OUT, "bound_check.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
