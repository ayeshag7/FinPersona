"""
E1.2 estimator A (PREREG_PHASE_1.md section 4.1): the value-mispricing decomposition from variance ratios.

Model: log P = log V + x, log V a random walk (daily variance sigma_V^2), x an AR(1) with stationary sd s_x and
half-life h (rho = 2^(-1/h)). Moments per stock: Var(r_1) and VR(k) = Var(r_k) / (k Var(r_1)), k in {5, 10, 20, 60,
120, 250, 500} (Lo & MacKinlay 1988 overlapping estimator with the small-sample correction); pooled = cross-sectional
mean over set A. Closed form: Var(r_1) = sigma_V^2 + 2 s_x^2 (1 - rho); VR(k) = [k sigma_V^2 + 2 s_x^2 (1 - rho^k)] /
[k Var(r_1)]. Fit by weighted minimum distance in (log sigma_V, log s_x, log h), weights 1/Var_boot of each pooled
moment. Intervals: (i) cluster bootstrap over stocks (1,000); (ii) joint stock x moving-block (250-day) bootstrap over
time (500), reported beside.

    python -m tools.phase1.e1_2_vr
Outputs: docs/env_v2/generated/v2_1/e1_2/vr_fit.json, vr_fit.md, vr_moments_by_stock.csv
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from tools.phase1.panel import DEFAULT, analysis_sets, load_prices, log_returns, sub_period_mask, OUT_DIR  # noqa: E402

OUT = os.path.join(OUT_DIR, "e1_2")
KS_FULL = (5, 10, 20, 60, 120, 250, 500)
KS_SUB = (5, 10, 20, 60, 120, 250)
N_BOOT_STOCK = 1000
N_BOOT_BLOCK = 500
BLOCK = 250


# ------------------------------------------------------------------------------------------------ moments
def vr_moments(R: np.ndarray, ks: Tuple[int, ...]) -> np.ndarray:
    """R: (T, N) daily log returns (NaN -> 0 after demeaning is NOT applied; NaN rows are treated as zero-return days,
    which is what a missing quote inside a full history means). Returns (N, 1 + len(ks)): [Var1, VR(k)...]."""
    R = np.where(np.isfinite(R), R, 0.0)
    T, N = R.shape
    mu = R.mean(axis=0)
    var1 = ((R - mu) ** 2).sum(axis=0) / (T - 1)
    cs = np.vstack([np.zeros((1, N)), np.cumsum(R, axis=0)])           # cumulative log price, (T+1, N)
    out = np.empty((N, 1 + len(ks)))
    out[:, 0] = var1
    for j, k in enumerate(ks):
        d = cs[k:] - cs[:-k] - k * mu                                    # overlapping k-day sums, (T-k+1, N)
        m = k * (T - k + 1) * (1 - k / T)          # Lo-MacKinlay: sigma_c^2(k) is already per unit period
        var_k = (d ** 2).sum(axis=0) / m
        out[:, 1 + j] = var_k / var1                 # (an earlier version divided by k twice; fixed 29 Aug 2026 before any result was used)
    return out


def model_moments(theta: np.ndarray, ks: Tuple[int, ...]) -> np.ndarray:
    sv, sx, h = np.exp(theta)
    rho = 2.0 ** (-1.0 / h)
    var1 = sv ** 2 + 2 * sx ** 2 * (1 - rho)
    vr = np.array([(k * sv ** 2 + 2 * sx ** 2 * (1 - rho ** k)) / (k * var1) for k in ks])
    return np.concatenate([[var1], vr])


def fit(target: np.ndarray, w: np.ndarray, ks: Tuple[int, ...], starts=None) -> Dict[str, float]:
    """Weighted minimum distance; best of a small log grid of starts (3 sigma_V x 3 s_x x 4 h), Nelder-Mead polish."""
    def J(th):
        m = model_moments(th, ks)
        return float(((m - target) ** 2 * w).sum())
    if starts is None:
        starts = [np.log([sv, sx, h]) for sv in (0.004, 0.008, 0.016) for sx in (0.08, 0.15, 0.30) for h in (30, 100, 250, 600)]
    best = None
    for s0 in starts:
        r = minimize(J, s0, method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-12, "maxiter": 4000})
        if best is None or r.fun < best.fun:
            best = r
    sv, sx, h = np.exp(best.x)
    return {"sigma_V": float(sv), "s_x": float(sx), "h": float(h), "J": float(best.fun), "theta": best.x.tolist()}


def block_indices(T: int, block: int, rng: np.random.Generator) -> np.ndarray:
    starts = rng.integers(0, T - block + 1, int(np.ceil(T / block)))
    idx = np.concatenate([np.arange(s, s + block) for s in starts])[:T]
    return idx


def estimate(R: np.ndarray, ks: Tuple[int, ...], tickers: List[str], label: str, n_boot_stock: int = N_BOOT_STOCK,
             n_boot_block: int = N_BOOT_BLOCK, seed: int = 0) -> Dict:
    t0 = time.time()
    T, N = R.shape
    M = vr_moments(R, ks)                                  # (N, m)
    pooled = M.mean(axis=0)
    rng = np.random.default_rng(seed)
    # (i) stock-cluster bootstrap of the pooled moments -> weights, then refit per resample
    idxs = rng.integers(0, N, (n_boot_stock, N))
    boot_pooled = np.stack([M[i].mean(axis=0) for i in idxs])
    w = 1.0 / np.maximum(boot_pooled.var(axis=0, ddof=1), 1e-30)
    point = fit(pooled, w, ks)
    fits_i = np.array([[fit(bp, w, ks, starts=[np.array(point["theta"])])[k] for k in ("sigma_V", "s_x", "h")] for bp in boot_pooled])
    # (ii) joint stock x moving-block bootstrap over time (shared blocks across stocks keep the cross-section intact)
    fits_ii = []
    for b in range(n_boot_block):
        bi = block_indices(T, BLOCK, rng)
        si = rng.integers(0, N, N)
        Mb = vr_moments(R[bi][:, si], ks).mean(axis=0)
        f = fit(Mb, w, ks, starts=[np.array(point["theta"])])
        fits_ii.append([f["sigma_V"], f["s_x"], f["h"]])
    fits_ii = np.array(fits_ii)
    def ci(a):
        return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]
    out = {"label": label, "n_stocks": int(N), "T_days": int(T), "ks": list(ks), "pooled_moments": {"var1": float(pooled[0]),
           **{f"VR{k}": float(pooled[1 + j]) for j, k in enumerate(ks)}},
           "pooled_moments_ci_stock": {"var1": ci(boot_pooled[:, 0]), **{f"VR{k}": ci(boot_pooled[:, 1 + j]) for j, k in enumerate(ks)}},
           "per_stock_VR_p25_p75": {f"VR{k}": [float(np.percentile(M[:, 1 + j], 25)), float(np.percentile(M[:, 1 + j], 75))] for j, k in enumerate(ks)},
           "fit": {"sigma_V": point["sigma_V"], "s_x": point["s_x"], "h_days": point["h"], "J": point["J"],
                   "model_moments": model_moments(np.array(point["theta"]), ks).tolist(),
                   "rw_share_of_daily_var": float(point["sigma_V"] ** 2 / pooled[0])},
           "ci_stock_bootstrap": {"sigma_V": ci(fits_i[:, 0]), "s_x": ci(fits_i[:, 1]), "h_days": ci(fits_i[:, 2]), "n_boot": n_boot_stock},
           "ci_block_bootstrap": {"sigma_V": ci(fits_ii[:, 0]), "s_x": ci(fits_ii[:, 1]), "h_days": ci(fits_ii[:, 2]),
                                  "n_boot": n_boot_block, "block_days": BLOCK},
           "bootstrap_sd_stock": {"sigma_V": float(fits_i[:, 0].std()), "s_x": float(fits_i[:, 1].std()), "h_days": float(fits_i[:, 2].std())},
           "seconds": round(time.time() - t0, 1)}
    return out, M


def main():
    os.makedirs(OUT, exist_ok=True)
    sets = analysis_sets(write=False)
    A = sets["A"]
    prices = load_prices(A).ffill()
    rets = log_returns(prices)
    R = rets.to_numpy()[1:]
    idx = rets.index[1:]
    results = {"spec": DEFAULT.to_dict(), "set": "A", "n_stocks": len(A), "window": [str(idx[0].date()), str(idx[-1].date())],
               "method": __doc__.strip().split("\n\n")[1], "periods": {}}
    res, M = estimate(R, KS_FULL, A, "full 2000-2024")
    results["periods"]["full"] = res
    pd.DataFrame(M, columns=["var1"] + [f"VR{k}" for k in KS_FULL], index=A).to_csv(os.path.join(OUT, "vr_moments_by_stock.csv"))
    print(json.dumps({k: res[k] for k in ("fit", "ci_stock_bootstrap", "ci_block_bootstrap", "seconds")}, indent=1), flush=True)
    for name, m in sub_period_mask(idx).items():
        r_sub, _ = estimate(R[m], KS_SUB, A, name, n_boot_stock=500, n_boot_block=200)
        results["periods"][name] = r_sub
        print(name, json.dumps(r_sub["fit"]), r_sub["ci_stock_bootstrap"], flush=True)
    with open(os.path.join(OUT, "vr_fit.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    L = ["# E1.2 estimator A: variance-ratio decomposition (set A; PREREG_PHASE_1.md section 4.1)", "",
         f"Set A = {len(A)} flag-free full-history names, {results['window'][0]} .. {results['window'][1]}, daily log returns of Adj Close. "
         "Pooled curve = cross-sectional mean of the per-stock Lo-MacKinlay VR(k); weights = 1/Var of the pooled moment under the stock "
         "bootstrap. Intervals: (i) stock-cluster bootstrap; (ii) joint stock x 250-day moving-block bootstrap. Survivor caveat: set A "
         "has no delistings (REG-15).", "",
         "| period | n | sigma_V/day | 95 % CI (stocks) | 95 % CI (blocks) | s_x | CI (stocks) | CI (blocks) | h (days) | CI (stocks) | CI (blocks) | RW share of daily var | J |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in results["periods"].items():
        f, c1, c2 = r["fit"], r["ci_stock_bootstrap"], r["ci_block_bootstrap"]
        L.append(f"| {name} | {r['n_stocks']} | {f['sigma_V']:.5f} | [{c1['sigma_V'][0]:.5f}, {c1['sigma_V'][1]:.5f}] | [{c2['sigma_V'][0]:.5f}, {c2['sigma_V'][1]:.5f}] | "
                 f"{f['s_x']:.3f} | [{c1['s_x'][0]:.3f}, {c1['s_x'][1]:.3f}] | [{c2['s_x'][0]:.3f}, {c2['s_x'][1]:.3f}] | {f['h_days']:.0f} | [{c1['h_days'][0]:.0f}, {c1['h_days'][1]:.0f}] | "
                 f"[{c2['h_days'][0]:.0f}, {c2['h_days'][1]:.0f}] | {f['rw_share_of_daily_var']:.2f} | {f['J']:.2f} |")
    r = results["periods"]["full"]
    L += ["", "Pooled moments (full sample) with stock-bootstrap intervals and the fitted model's values:", "",
          "| moment | pooled | 95 % CI | model | per-stock P25-P75 |", "|---|---|---|---|---|"]
    for j, key in enumerate(["var1"] + [f"VR{k}" for k in KS_FULL]):
        ci = r["pooled_moments_ci_stock"][key]; pp = r["per_stock_VR_p25_p75"].get(key)
        L.append(f"| {key} | {r['pooled_moments'][key]:.5g} | [{ci[0]:.5g}, {ci[1]:.5g}] | {r['fit']['model_moments'][j]:.5g} | "
                 f"{'-' if pp is None else f'{pp[0]:.3f}-{pp[1]:.3f}'} |")
    with open(os.path.join(OUT, "vr_fit.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
