"""
E2.3 data side: the 17-moment target vector and its BLOCK-BOOTSTRAP covariance matrix, per period, cached to disk.

The moments are derived statistics of the E1.0 panel, not the panel itself, so the cache can be shipped to a
compute kernel while `datasets/` never leaves this machine (the precedent is e1_2/smm_data_moments.json).

Periods (PREREG_PHASE_2.md section 4): `full` 2000-01-03..2024-12-31 and the three E2.3 sub-periods
`p1` 2000-2008, `p2` 2009-2016, `p3` 2017-2024, plus `train` (p1+p2 = 2000-2016) and `test` (= p3) for E2.4's
held-out prediction.  Set A (417 flag-free full-history names, Phase 1's exclusion rule) throughout.

    python -m tools.phase2.e2_3_data [--n-boot 500] [--periods full,p1,p2,p3,train]
Outputs: docs/env_v2/generated/v2_1/e2_3/data_moments.json (point + design)
         docs/env_v2/generated/v2_1/e2_3/data_boot_<period>.npy (n_boot x 17 bootstrap moment vectors)
         docs/env_v2/generated/v2_1/e2_3/weight_<period>.npy    (17 x 17 weight matrix W = Sigma^-1, shrunk)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase2.moments import ALL_NAMES, BLOCK_OF, GROUP_OF, bootstrap_moments, pooled  # noqa: E402

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_3")
PERIODS = {"full": ("2000-01-03", "2024-12-31"), "p1": ("2000-01-03", "2008-12-31"),
           "p2": ("2009-01-01", "2016-12-31"), "p3": ("2017-01-01", "2024-12-31"),
           "train": ("2000-01-03", "2016-12-31"), "test": ("2017-01-01", "2024-12-31")}
SHRINK = 0.10   # W = (Sigma_hat (1 - s) + s diag(Sigma_hat))^-1 : ridge toward the diagonal (PREREG section 4.3)


def weight_matrix(boot: np.ndarray, shrink: float = SHRINK):
    S = np.cov(boot, rowvar=False)
    Sd = np.diag(np.diag(S))
    Ss = (1.0 - shrink) * S + shrink * Sd
    W = np.linalg.inv(Ss)
    return W, S, Ss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=500)
    ap.add_argument("--periods", default="full,p1,p2,p3,train,test")
    ap.add_argument("--seed", type=int, default=20260901)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    from tools.phase1.panel import DEFAULT, analysis_sets, load_prices
    A = analysis_sets(write=False)["A"]
    prices = load_prices(A).ffill()
    idx = prices.index
    lp_all = np.log(prices.to_numpy())
    res = {"spec": DEFAULT.to_dict(), "set": "A", "n_stocks": len(A), "moment_names": ALL_NAMES,
           "block_days": BLOCK_OF, "moment_group": GROUP_OF, "n_boot": a.n_boot, "seed": a.seed,
           "shrink": SHRINK, "periods": {}}
    path = os.path.join(OUT, "data_moments.json")
    if os.path.exists(path):
        res = json.load(open(path, encoding="utf-8"))
    for k, name in enumerate(a.periods.split(",")):
        lo, hi = PERIODS[name]
        m = (idx >= lo) & (idx <= hi)
        lp = lp_all[np.asarray(m)]
        lp = lp - lp[0]
        bpath = os.path.join(OUT, f"data_boot_{name}.npy")
        t0 = time.time()
        M = pooled(lp)
        if os.path.exists(bpath):
            boot = np.load(bpath)
            print(f"{name}: bootstrap cached ({boot.shape[0]})", flush=True)
        else:
            boot = bootstrap_moments(lp, a.n_boot, seed=a.seed + 7919 * k)
            np.save(bpath, boot)
        W, S, Ss = weight_matrix(boot)
        np.save(os.path.join(OUT, f"weight_{name}.npy"), W)
        res["periods"][name] = {
            "window": [lo, hi], "n_days": int(lp.shape[0]), "n_stocks": int(lp.shape[1]),
            "moments": M.tolist(), "boot_mean": boot.mean(axis=0).tolist(),
            "boot_sd": boot.std(axis=0, ddof=1).tolist(),
            "cond_number": float(np.linalg.cond(Ss)), "seconds": round(time.time() - t0)}
        print(f"{name}: {lp.shape[0]} d x {lp.shape[1]} stocks, cond(Sigma_s) {np.linalg.cond(Ss):.3g}, "
              f"{time.time() - t0:.0f} s", flush=True)
        print("   " + "  ".join(f"{n}={v:.4g}+-{s:.3g}" for n, v, s in
                                zip(ALL_NAMES, M, boot.std(axis=0, ddof=1))), flush=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
    L = ["# E2.3 data moments and block-bootstrap weight matrix (set A; PREREG_PHASE_2.md section 4)", "",
         f"Set A = {len(A)} flag-free full-history names, daily log Adj Close.  Moment vector: FW's nine "
         "(returns in percentage points) plus the persistence-carrying VR(20/60/120/250/500) and the ACF of "
         "log(P/SMA250) at 20/60/120, each computed per stock and pooled as the cross-sectional mean.  "
         f"Weight matrix W = Sigma^-1 from a joint stock x block bootstrap ({a.n_boot} resamples; block "
         f"{BLOCK_OF['short']} d for the five short-memory moments, {BLOCK_OF['long']} d for the four "
         f"long-memory ACF(|r|) moments, {BLOCK_OF['pers']} d for the eight persistence moments; FW 2012 "
         f"Appendix A2 extended), shrunk {SHRINK:.0%} toward its diagonal.", "",
         "| period | window | days | " + " | ".join(ALL_NAMES) + " |",
         "|---|---|---|" + "---|" * len(ALL_NAMES)]
    for name, r in res["periods"].items():
        L.append(f"| {name} | {r['window'][0]}..{r['window'][1]} | {r['n_days']} | "
                 + " | ".join(f"{v:.4g} ({s:.3g})" for v, s in zip(r["moments"], r["boot_sd"])) + " |")
    L += ["", "Cells are `moment (bootstrap sd)`.  FW 2012 Table A1 (S&P 500, 1980-2007, read at source) beside "
              "the first nine, as an anchor and never as a tolerance: rAC1 -0.008, 1/Hill 0.301, vMean 0.713, "
              "vAC 0.193 / 0.187 / 0.159 / 0.128 / 0.112 / 0.074."]
    with open(os.path.join(OUT, "data_moments.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
