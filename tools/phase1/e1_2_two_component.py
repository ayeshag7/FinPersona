"""
EXPLORATORY (not pre-registered; PHASE_1_REPORT.md says so wherever it is cited): a two-component transitory model on the
pooled variance-ratio curve of set A, to see whether estimator A (fast transitory component, h ~ 5 d) and estimator B
(slow P/V_hat mean reversion, h ~ 256 d) can be the same process seen at two horizons.

Model: log P = log V + x1 + x2, log V a random walk (daily variance sigma_V^2), x_i independent AR(1)s with stationary sd
s_i and half-life h_i. Var(r_k) = k sigma_V^2 + 2 sum_i s_i^2 (1 - rho_i^k); VR(k) = Var(r_k) / (k Var(r_1)).
Fits: (i) free (5 parameters, 8 moments); (ii) h2 fixed at estimator B's median-unbiased 256 d (EarningsPerShareBasic,
sector multiple); (iii) h2 fixed at 150 d (the engine's fw_fallback_hl150 half-life). Weighted minimum distance with the
stock-bootstrap 1/Var weights stored in vr_fit.json. Intervals: none (exploratory); the J statistics are reported.

    python -m tools.phase1.e1_2_two_component
Outputs: docs/env_v2/generated/v2_1/e1_2/vr_two_component_exploratory.{json,md}
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from scipy.optimize import minimize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_2")


def model(theta, ks):
    sV, s1, h1, s2, h2 = np.exp(theta)
    r1, r2 = 2 ** (-1 / h1), 2 ** (-1 / h2)
    v1 = sV ** 2 + 2 * s1 ** 2 * (1 - r1) + 2 * s2 ** 2 * (1 - r2)
    vr = [(k * sV ** 2 + 2 * s1 ** 2 * (1 - r1 ** k) + 2 * s2 ** 2 * (1 - r2 ** k)) / (k * v1) for k in ks]
    return np.array([v1] + vr)


def fit(M, w, ks, h2_fixed=None, starts=None):
    def obj(th):
        full = th if h2_fixed is None else np.append(th, np.log(h2_fixed))
        d = model(full, ks) - M
        return float(d @ (w * d))
    best = None
    for s0 in starts:
        x0 = np.log(s0) if h2_fixed is None else np.log(s0)[:4]
        r = minimize(obj, x0, method="Nelder-Mead", options={"maxiter": 20000, "xatol": 1e-9, "fatol": 1e-12})
        if best is None or r.fun < best.fun:
            best = r
    th = best.x if h2_fixed is None else np.append(best.x, np.log(h2_fixed))
    sV, s1, h1, s2, h2 = np.exp(th)
    return {"sigma_V": sV, "s_1": s1, "h_1": h1, "s_2": s2, "h_2": h2, "s_x_total": float(np.sqrt(s1 ** 2 + s2 ** 2)),
            "J": float(best.fun), "model_moments": model(th, ks).tolist()}


def main():
    d = json.load(open(os.path.join(OUT, "vr_fit.json"), encoding="utf-8"))
    f = d["periods"]["full"]; ks = f["ks"]
    names = ["var1"] + [f"VR{k}" for k in ks]
    M = np.array([f["pooled_moments"][n] for n in names])
    sd = np.array([(f["pooled_moments_ci_stock"][n][1] - f["pooled_moments_ci_stock"][n][0]) / 3.92 for n in names])
    w = 1.0 / sd ** 2
    starts = [(0.017, 0.02, 5, 0.17, 256), (0.02, 0.03, 8, 0.1, 200), (0.01, 0.02, 5, 0.3, 500), (0.015, 0.01, 3, 0.2, 150)]
    one = fit(M, w, ks, h2_fixed=1e6, starts=[(0.02, 0.024, 5, 1e-6, 1e6)])   # one-component check (s_2 -> 0)
    res = {"note": "EXPLORATORY, not pre-registered: two-component transitory model on the pooled VR curve of set A (full sample); "
                   "no intervals; weights = stock-bootstrap 1/Var of each pooled moment (vr_fit.json)",
           "moments": dict(zip(names, M.tolist())), "moment_sd": dict(zip(names, sd.tolist())),
           "one_component_reference": {"sigma_V": one["sigma_V"], "s_x": one["s_1"], "h": one["h_1"], "J": one["J"]},
           "free_fit": fit(M, w, ks, starts=starts),
           "h2_fixed_256": fit(M, w, ks, h2_fixed=256.0, starts=starts),
           "h2_fixed_150": fit(M, w, ks, h2_fixed=150.0, starts=starts)}
    with open(os.path.join(OUT, "vr_two_component_exploratory.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    L = ["# E1.2 exploratory two-component fit on the pooled VR curve (NOT pre-registered; no intervals)", "",
         "log P = log V + x1 + x2; V random walk; x_i AR(1) with sd s_i, half-life h_i. Set A, full sample, 8 moments, stock-bootstrap weights.", "",
         "| fit | sigma_V/day | s_1 | h_1 (d) | s_2 | h_2 (d) | s_x total | J |", "|---|---|---|---|---|---|---|---|"]
    o = res["one_component_reference"]
    L.append(f"| one component (estimator A) | {o['sigma_V']:.5f} | {o['s_x']:.3f} | {o['h']:.1f} | - | - | {o['s_x']:.3f} | {o['J']:.2f} |")
    for k, lab in (("free_fit", "two components, free"), ("h2_fixed_256", "h_2 = 256 d (estimator B)"), ("h2_fixed_150", "h_2 = 150 d (engine)")):
        r = res[k]
        L.append(f"| {lab} | {r['sigma_V']:.5f} | {r['s_1']:.3f} | {r['h_1']:.1f} | {r['s_2']:.3f} | {r['h_2']:.0f} | {r['s_x_total']:.3f} | {r['J']:.2f} |")
    L += ["", "Reading: the VR curve alone prefers a second component of about two months (free fit) and fits worse the longer h_2 is "
          "forced (J rises from 8.6 to 15.5 at 150 d and 18.6 at 256 d, against 84.4 for one component); over the 500-day horizon of the "
          "curve a component with a one-year half-life is close to a random walk, so sigma_V and s_2 trade off and the curve cannot "
          "settle them. This is why the pre-registered decomposition needs estimator B (a level anchor) or C (persistence-carrying "
          "moments), and why the recovery study decides which is usable. sigma_V under every two-component fit (0.016-0.019) is "
          "2.7-3.2 x v2's stipulated 0.006."]
    with open(os.path.join(OUT, "vr_two_component_exploratory.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
