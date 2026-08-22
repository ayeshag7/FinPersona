"""
Re-estimate the Franke-Westerhoff calm-phase parameters on single stocks by the
simulated method of moments (plan Section 2.2; decision 2).

Data: daily adjusted closes of ~10 US large caps, 2000-2024, via yfinance (the
repo already depends on it). Moments (FW 2012, nine): lag-1 return ACF, mean |r|,
Hill tail index (5%), ACF of |r| at lags 1, 5, 10, 25, 50, 100. Weighting: inverse
of the bootstrap variance of the empirical moments (block bootstrap, 250-day
blocks). Parameters estimated: phi, chi, alpha_0, alpha_n, alpha_p (sigma_f,
sigma_c, beta, mu held at FW values; price_scale = 100 as in mispricing.py).
Simulation: the calm engine (mispricing.MispricingState + GJR-GARCH-t innovations)
with returns r = dV + dx, 10 x 5,000 days per evaluation, common random numbers.
Optimiser: Nelder-Mead from the index set, bounded by reflection.

Output: envs/v2/params/fw_single_stock.json (+ a report in docs/env_v2/generated/).
If the download fails or the optimiser does not converge, NOTHING is written and
the documented fallback (phi for a ~150-day calm half-life) stays in force.

Usage: python -m tools.calibrate_fw [--tickers AAPL MSFT ...] [--start 2000-01-01] [--end 2024-12-31]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from envs.v2.mispricing import FWParams, FW_INDEX_2012, MispricingState, PARAM_DIR  # noqa: E402
from envs.v2.garch import GJRParams, GJRGarch  # noqa: E402
from envs.v2.rng import standardised_t  # noqa: E402

TICKERS = ["AAPL", "MSFT", "JNJ", "XOM", "JPM", "PG", "KO", "WMT", "GE", "IBM"]
LAGS = (1, 5, 10, 25, 50, 100)


def acf(x, k):
    x = np.asarray(x, float); x = x - x.mean()
    return float((x[:-k] * x[k:]).sum() / (x * x).sum())


def hill(r, frac=0.05):
    a = np.sort(np.abs(r))[::-1]; k = max(10, int(frac * len(a)))
    return float(1.0 / np.mean(np.log(a[:k] / a[k])))


def moments(r: np.ndarray) -> np.ndarray:
    r = np.asarray(r, float) * 100.0   # percent, as in FW
    return np.array([acf(r, 1), np.mean(np.abs(r)), hill(r)] + [acf(np.abs(r), L) for L in LAGS])


def download(tickers, start, end) -> dict:
    import yfinance as yf
    out = {}
    for t in tickers:
        df = yf.download(t, start=start, end=end, progress=False, auto_adjust=True)
        if df is None or len(df) < 2000:
            continue
        px = df["Close"].to_numpy(dtype=float).ravel()
        out[t] = np.diff(np.log(px))
    return out


def empirical_targets(returns: dict, n_boot: int = 200, block: int = 250, seed: int = 0):
    rng = np.random.default_rng(seed)
    mom = np.array([moments(r) for r in returns.values()])
    target = mom.mean(axis=0)
    boots = []
    for _ in range(n_boot):
        ms = []
        for r in returns.values():
            nb = len(r) // block
            idx = rng.integers(0, len(r) - block, nb)
            rb = np.concatenate([r[i:i + block] for i in idx])
            ms.append(moments(rb))
        boots.append(np.mean(ms, axis=0))
    W = np.diag(1.0 / (np.var(boots, axis=0) + 1e-12))
    return target, W


def simulate_moments(theta, n_paths=10, n_days=5000, seed=123) -> np.ndarray:
    phi, chi, a0, an, ap = theta
    p = FWParams(phi=phi, chi=chi, alpha_0=a0, alpha_n=an, alpha_p=ap, name="smm_trial")
    gp = GJRParams()
    rng = np.random.default_rng(seed)
    ms = []
    for k in range(n_paths):
        eta = standardised_t(rng, gp.df, n_days)
        zV = standardised_t(rng, 5.0, n_days)
        g = GJRGarch(gp); st = MispricingState(p, "fw_single", w_norm=1.0)
        # unit-mean weight normalisation from this path's own pilot
        ws = []
        x_prev = 0.0; r = np.empty(n_days)
        for i in range(n_days):
            sig, e = g.step(eta[i], "calm")
            ws.append(st.raw_weight())
            x_new = st.step(e, 0.0)
            r[i] = (x_new - x_prev) + 0.00025 + 0.006 * zV[i]
            x_prev = x_new
        st.w_norm = float(np.mean(ws))
        ms.append(moments(r[500:]))
    return np.mean(ms, axis=0)


def objective(theta, target, W):
    lo = np.array([0.01, 0.0, -3.0, 0.0, 0.0]); hi = np.array([5.0, 5.0, 3.0, 10.0, 200.0])
    th = np.clip(theta, lo, hi)
    pen = float(np.sum((theta - th) ** 2)) * 1e3
    d = simulate_moments(th) - target
    return float(d @ W @ d) + pen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=TICKERS)
    ap.add_argument("--start", default="2000-01-01"); ap.add_argument("--end", default="2024-12-31")
    ap.add_argument("--maxiter", type=int, default=150)
    a = ap.parse_args()
    try:
        rets = download(a.tickers, a.start, a.end)
    except Exception as exc:
        print(f"DOWNLOAD FAILED ({exc}); the documented fallback stays in force (DECISION_LOG.md row 2)."); return 2
    if len(rets) < 5:
        print(f"only {len(rets)} usable series; fallback stays in force."); return 2
    target, W = empirical_targets(rets)
    print("empirical moments:", np.round(target, 4))
    from scipy.optimize import minimize
    x0 = np.array([FW_INDEX_2012.phi, FW_INDEX_2012.chi, FW_INDEX_2012.alpha_0, FW_INDEX_2012.alpha_n, FW_INDEX_2012.alpha_p])
    res = minimize(objective, x0, args=(target, W), method="Nelder-Mead", options={"maxiter": a.maxiter, "xatol": 1e-3, "fatol": 1e-3})
    print(res)
    j0 = objective(x0, target, W)
    # Acceptance rule (DECISION_LOG row 2): the estimate must (i) improve J by at least 20% over the index
    # starting point and (ii) reach J < 50 (the nine-moment distance in bootstrap-variance units); otherwise
    # the moments do not identify the parameters and the documented fallback stays in force.
    if not (res.fun < 0.8 * j0 and res.fun < 50.0):
        rej = os.path.join(PARAM_DIR, "fw_single_stock.REJECTED.json")
        os.makedirs(PARAM_DIR, exist_ok=True)
        with open(rej, "w", encoding="utf-8") as fh:
            json.dump({"x": res.x.tolist(), "J": float(res.fun), "J_index_start": float(j0), "target_moments": target.tolist(),
                       "sim_moments": simulate_moments(res.x).tolist(), "tickers": list(rets), "accepted": False}, fh, indent=1)
        print(f"REJECTED: J = {res.fun:.1f} (index start {j0:.1f}); written {rej}; fallback stays in force."); return 3
    phi, chi, a0, an, ap_ = res.x
    sim = simulate_moments(res.x)
    out = FWParams(phi=float(phi), chi=float(chi), alpha_0=float(a0), alpha_n=float(an), alpha_p=float(ap_),
                   name="fw_single_stock",
                   source=f"SMM on {len(rets)} single stocks ({', '.join(rets)}), {a.start}..{a.end}; FW 9-moment set; J = {res.fun:.3f}")
    os.makedirs(PARAM_DIR, exist_ok=True)
    with open(os.path.join(PARAM_DIR, "fw_single_stock.json"), "w", encoding="utf-8") as fh:
        json.dump({**asdict(out), "J": float(res.fun), "target_moments": target.tolist(), "sim_moments": sim.tolist(),
                   "tickers": list(rets)}, fh, indent=1)
    rep = os.path.join(ROOT, "docs", "env_v2", "generated", "fw_single_stock_calibration.md")
    with open(rep, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# FW single-stock SMM calibration\n\n" + json.dumps(asdict(out), indent=1) +
                 f"\n\nJ = {res.fun:.3f}\n\ntarget moments: {np.round(target, 4).tolist()}\nsimulated: {np.round(sim, 4).tolist()}\n")
    print("written", rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
