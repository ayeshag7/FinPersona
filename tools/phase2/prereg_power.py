"""
Phase 2 pre-registration: the power / decidability check behind every criterion, as runnable code.

The rule this script exists to enforce (PHASE_2_EXECUTION_PROMPT; PREREG_PHASE_1_ADDENDUM sections 1 and 4):
before a criterion is written down, the spread of its statistic at the intended sample size is simulated, so
that a criterion whose acceptance set is empty -- or whose sample size cannot separate the alternatives -- is
found here rather than after a 20-hour run.  Every block below writes its numbers to
`generated/v2_1/e2_0/power.json`; PREREG_PHASE_2.md quotes them and fixes the design on them.

    python -m tools.phase2.prereg_power [--only PA1,PA2,...] [--workers 3]

PA1  E2.1  spread of the joint MCR and of (chartist share, excess kurtosis) over n runs of FW's own model
PA2  E2.3  simulation noise of the 17 pooled moments at n_paths x T, in units of the data bootstrap sd
PA3  E2.4b spread of the held-out distance D (bootstrap-sd units) under correct specification
PA4  E2.5  spread of the median naive / median-unbiased half-life over n seeds, per (h, T) cell
PA5  E2.6  detectable difference in an oracle-switch share at n seeds (Appendix A share formula, simulated)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase2.fw_pure import PureParams, excess_kurtosis, simulate_pure  # noqa: E402
from tools.phase2.moments import ALL_NAMES, FW_NAMES, FW_TABLE_A1, fw_moments  # noqa: E402

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_0")
PILOT_SEEDS = dict(pa1=770001, pa2=770101, pa3=770201, pa4=770301, pa5=770401)


def _ci(a, q=(2.5, 97.5)):
    return [float(np.percentile(a, q[0])), float(np.percentile(a, q[1]))]


# --------------------------------------------------------------------------------------------------- PA1
def pa1(n_pilot: int = 20, n_target: int = 200, T: int = 6750, reps: int = 12):
    """Cross-run sd of E2.1's statistics from `reps` independent pilots of `n_pilot` runs each, and the
    implied half-width at `n_target` runs.  Pilot seeds are disjoint from E2.1's registered seeds."""
    t0 = time.time()
    jm, sh, ku = [], [], []
    for r in range(reps):
        o = simulate_pure(n_pilot, T, PureParams(price_scale=1.0), seed=PILOT_SEEDS["pa1"] + r)
        M = fw_moments(o["r"])
        inside = np.ones(n_pilot, bool)
        for j, nm in enumerate(FW_NAMES):
            _, lo, hi = FW_TABLE_A1[nm]
            inside &= (M[:, j] >= lo) & (M[:, j] <= hi)
        jm.append(inside.mean())
        sh.append(o["n_c"].mean(axis=0).mean())
        ku.append(excess_kurtosis(o["r"]).mean())
    jm, sh, ku = map(np.asarray, (jm, sh, ku))
    p = float(jm.mean())
    out = {"n_pilot_runs": n_pilot, "reps": reps, "T": T, "n_target_runs": n_target,
           "joint_mcr_pilot_mean": p,
           "joint_mcr_halfwidth_at_target": 1.96 * math.sqrt(max(p * (1 - p), 1e-9) / n_target),
           "chartist_share_pilot_mean": float(sh.mean()),
           "chartist_share_sd_across_runs": float(np.std([x for x in sh], ddof=1)) * math.sqrt(n_pilot),
           "excess_kurtosis_pilot_mean": float(ku.mean()),
           "excess_kurtosis_sd_across_runs": float(np.std([x for x in ku], ddof=1)) * math.sqrt(n_pilot),
           "seconds": round(time.time() - t0)}
    out["chartist_share_halfwidth_at_target"] = 1.96 * out["chartist_share_sd_across_runs"] / math.sqrt(n_target)
    out["excess_kurtosis_halfwidth_at_target"] = 1.96 * out["excess_kurtosis_sd_across_runs"] / math.sqrt(n_target)
    return out


# --------------------------------------------------------------------------------------------------- PA2
def pa2(n_paths_grid=(20, 50, 100), T: int = 5000, n_seeds: int = 12):
    """Simulation noise of the pooled 17 moments across CRN seeds, in units of the data bootstrap sd."""
    from tools.phase2.engines import DEFAULTS, pooled_moments
    t0 = time.time()
    boot_sd = None
    bp = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_3", "data_boot_full.npy")
    if os.path.exists(bp):
        boot_sd = np.load(bp).std(axis=0, ddof=1)
    res = {"T": T, "n_seeds": n_seeds, "cells": {}, "data_boot_sd": None if boot_sd is None else boot_sd.tolist()}
    for eng in ("ar1", "fw_v2", "fw_plus"):
        p = dict(DEFAULTS)
        if eng == "fw_v2":
            p["price_scale"] = 1.0                         # E2.1 confirmed price_scale = 1 (fw_repro.json)
        for n_paths in n_paths_grid:
            M = np.stack([pooled_moments(eng, n_paths, T, p, seed=PILOT_SEEDS["pa2"] + 13 * s)
                          for s in range(n_seeds)])
            sd = M.std(axis=0, ddof=1)
            cell = {"sim_sd": sd.tolist(), "mean": M.mean(axis=0).tolist()}
            if boot_sd is not None:
                cell["sim_sd_over_boot_sd"] = (sd / boot_sd).tolist()
                cell["max_ratio_persistence"] = float((sd / boot_sd)[9:].max())
                cell["max_ratio_all"] = float((sd / boot_sd).max())
            res["cells"][f"{eng}|{n_paths}"] = cell
            print(f"  PA2 {eng} n_paths={n_paths}: "
                  + (f"max sim/boot sd {cell['max_ratio_all']:.2f} (persistence {cell['max_ratio_persistence']:.2f})"
                     if boot_sd is not None else "no data bootstrap yet"), flush=True)
    res["seconds"] = round(time.time() - t0)
    return res


# --------------------------------------------------------------------------------------------------- PA3
def pa3(n_paths: int = 417, T: int = 2012, n_seeds: int = 40):
    """E2.4(b): spread, under correct specification, of the held-out distance
        D = mean_j |m_sim,j - m_test,j| / sd_boot,j   over the eight persistence-carrying moments.
    The model here IS the data-generating process, so any D above 0 is pure noise; the pre-registered
    'more than one bootstrap sd' margin is decidable only if sd(D) is well below 1."""
    from tools.phase2.engines import DEFAULTS, pooled_moments
    t0 = time.time()
    p = dict(DEFAULTS)
    p["price_scale"] = 1.0                             # E2.1 confirmed
    M = np.stack([pooled_moments("fw_v2", n_paths, T, p, seed=PILOT_SEEDS["pa3"] + 31 * s) for s in range(n_seeds)])
    sd_between = M.std(axis=0, ddof=1)
    bp = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_3", "data_boot_test.npy")
    boot_sd = np.load(bp).std(axis=0, ddof=1) if os.path.exists(bp) else sd_between
    # the held-out arm averages k = 20 CRN replicates before computing D, so the null spread is measured on
    # the SAME statistic: two independent 20-replicate means of a correctly specified model
    k = 20
    A = M[:k].mean(axis=0)
    B = M[k:2 * k].mean(axis=0) if n_seeds >= 2 * k else M[k:].mean(axis=0)
    D = np.array([np.mean(np.abs(M[i, 9:] - A[9:]) / boot_sd[9:]) for i in range(k, n_seeds)])
    D_means = float(np.mean(np.abs(B[9:] - A[9:]) / boot_sd[9:]))
    return {"n_paths": n_paths, "T": T, "n_seeds": n_seeds, "k_replicates": k,
            "D_single_replicate_mean_null": float(D.mean()),
            "D_single_replicate_sd_null": float(D.std(ddof=1)),
            "D_20replicate_mean_null": D_means,
            "D_mean_null": float(D.mean()), "D_sd_null": float(D.std(ddof=1)),
            "D_p95_null": float(np.percentile(D, 95)),
            "sim_sd_over_boot_sd_persistence": (sd_between[9:] / boot_sd[9:]).tolist(),
            "note": "target = one simulated replicate; D is the spread a perfectly specified model still shows",
            "seconds": round(time.time() - t0)}


# --------------------------------------------------------------------------------------------------- PA4
def ar1_paths(h: float, T: int, n: int, seed: int) -> np.ndarray:
    rho = 2.0 ** (-1.0 / h)
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((T, n)) * math.sqrt(1.0 - rho ** 2)
    x = np.empty((T, n))
    x[0] = rng.standard_normal(n)
    for t in range(1, T):
        x[t] = rho * x[t - 1] + e[t]
    return x


def acf1_half_life(x: np.ndarray) -> np.ndarray:
    d = x - x.mean(axis=0)
    a = (d[:-1] * d[1:]).sum(axis=0) / np.maximum((d * d).sum(axis=0), 1e-300)
    return np.where((a > 0) & (a < 1), -math.log(2.0) / np.log(np.clip(a, 1e-9, 1 - 1e-12)), np.nan)


def pa4(hs=(30, 150, 600), Ts=(200, 800, 5000), n_seeds: int = 200, reps: int = 10):
    """Spread of the cross-seed MEDIAN naive ACF(1) half-life at `n_seeds`, per (h, T) cell."""
    t0 = time.time()
    cells = {}
    for h in hs:
        for T in Ts:
            meds = []
            for r in range(reps):
                x = ar1_paths(h, T, n_seeds, PILOT_SEEDS["pa4"] + 101 * r + h + T)
                meds.append(float(np.nanmedian(acf1_half_life(x))))
            meds = np.asarray(meds)
            cells[f"h{h}|T{T}"] = {"median_of_medians": float(np.median(meds)),
                                   "sd_of_median_at_n": float(meds.std(ddof=1)),
                                   "halfwidth95": float(1.96 * meds.std(ddof=1)),
                                   "relative_halfwidth": float(1.96 * meds.std(ddof=1) / max(np.median(meds), 1e-9))}
    return {"n_seeds": n_seeds, "reps": reps, "cells": cells, "seconds": round(time.time() - t0)}


# --------------------------------------------------------------------------------------------------- PA5
def pa5(n_grid=(100, 200), p0s=(0.23, 0.50)):
    """Appendix A share formula, checked by simulation: at n paths, the 95 % half-width of an estimated share
    and the smallest difference between two persistence levels detectable with 80 % power at alpha = 0.05."""
    rng = np.random.default_rng(PILOT_SEEDS["pa5"])
    out = {}
    z95, z80 = 1.6449, 0.8416
    for n in n_grid:
        for p0 in p0s:
            s = rng.binomial(n, p0, 20000) / n
            # smallest p1 > p0 detected with 80 % power by a one-sided two-proportion test at n vs n
            d = np.linspace(0.005, 0.4, 400)
            se = np.sqrt(p0 * (1 - p0) / n + np.clip(p0 + d, 0, 1) * (1 - np.clip(p0 + d, 0, 1)) / n)
            ok = d >= (z95 + z80) * se
            out[f"n{n}|p{p0}"] = {"halfwidth95_simulated": float(1.96 * s.std(ddof=1)),
                                  "min_detectable_difference_two_sample": float(d[ok][0]) if ok.any() else None,
                                  "min_detectable_one_sample_vs_p0": float(
                                      ((z95 * math.sqrt(p0 * (1 - p0)) + z80 * math.sqrt(p0 * (1 - p0))) / math.sqrt(n)))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="PA1,PA2,PA3,PA4,PA5")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "power.json")
    res = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    sel = [s.strip().upper() for s in a.only.split(",")]
    fns = {"PA1": pa1, "PA2": pa2, "PA3": pa3, "PA4": pa4, "PA5": pa5}
    for k in sel:
        print(f"[power] {k} ...", flush=True)
        res[k] = fns[k]()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
        print(f"[power] {k} done", flush=True)
    print("written", path)


if __name__ == "__main__":
    main()
