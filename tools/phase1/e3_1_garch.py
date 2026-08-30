"""
E3.1 (run in Phase 1 because E1.4 and E2.3 need it; PREREG_PHASE_1.md section 3): per-stock GJR-GARCH(1,1)-t fits on
the analysis set, full sample and four sub-periods; cross-sectional medians with a bootstrap over stocks; standardised
residuals stored for E1.4 and Phase 3.

    python -m tools.phase1.e3_1_garch [--sets A,B] [--workers 8]

Outputs (docs/env_v2/generated/v2_1/e3_1/): garch_fits.csv (one row per stock x period), summary.json, summary.md,
residuals.parquet (date, ticker, z; float32; full-sample fits, set A).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from tools.phase1.panel import DEFAULT, analysis_sets, load_prices, log_returns, sub_period_mask, OUT_DIR  # noqa: E402

OUT = os.path.join(OUT_DIR, "e3_1")
MIN_OBS = 500
N_BOOT = 1000
LIT = {"Engle 2001 (JEP; portfolio 50/30/20 Nasdaq/Dow/bond, daily 1990-2000; read by the third pass, LOG 4.2)": {"alpha": 0.077, "beta": 0.905},
       "plan 7.1 sanity range (read by the third pass): persistence 0.95-0.99, nu 4-8": {"persistence": [0.95, 0.99], "nu": [4, 8]}}


def fit_one(args):
    """(ticker, period, returns array) -> parameter dict (+ standardised residuals for the full sample)."""
    import warnings
    warnings.filterwarnings("ignore")
    from arch import arch_model
    ticker, period, r, keep_resid = args
    r = np.asarray(r, float)
    r = r[np.isfinite(r)]
    out = {"ticker": ticker, "period": period, "n": int(len(r)), "converged": False}
    if len(r) < MIN_OBS:
        out["reason"] = "too_short"
        return out, None
    try:
        am = arch_model(100.0 * r, mean="Constant", vol="GARCH", p=1, o=1, q=1, dist="t")
        res = am.fit(disp="off", show_warning=False, options={"maxiter": 500})
        p = res.params
        a, g, b, nu, om = float(p["alpha[1]"]), float(p["gamma[1]"]), float(p["beta[1]"]), float(p["nu"]), float(p["omega"])
        pers = a + 0.5 * g + b
        out.update({"converged": bool(res.convergence_flag == 0), "alpha": a, "gamma": g, "beta": b, "nu": nu, "omega": om,
                    "persistence": pers, "uncond_sd": float(np.sqrt(om / (1 - pers)) / 100.0) if pers < 1 else float("nan"),
                    "loglik": float(res.loglikelihood), "mu": float(p["mu"]) / 100.0, "sample_sd": float(r.std())})
        z = np.asarray(res.std_resid, float) if keep_resid else None
        return out, z
    except Exception as exc:  # pragma: no cover
        out["reason"] = f"error: {exc}"[:120]
        return out, None


def _boot_median(vals, n_boot=N_BOOT, seed=0):
    v = np.asarray(vals, float); v = v[np.isfinite(v)]
    if len(v) < 5:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    meds = np.median(v[rng.integers(0, len(v), (n_boot, len(v)))], axis=1)
    return (float(np.median(v)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)))


def summarise(fits: pd.DataFrame) -> dict:
    out = {}
    for (aset, period), g in fits.groupby(["set", "period"]):
        gc = g[g["converged"]]
        row = {"n_stocks": int(len(g)), "n_converged": int(len(gc)), "share_converged": float(len(gc) / max(len(g), 1))}
        for k in ("alpha", "gamma", "beta", "nu", "persistence", "uncond_sd", "sample_sd"):
            m, lo, hi = _boot_median(gc[k])
            row[k] = {"median": m, "ci95": [lo, hi], "p25": float(np.nanpercentile(gc[k], 25)) if len(gc) else float("nan"),
                      "p75": float(np.nanpercentile(gc[k], 75)) if len(gc) else float("nan")}
        out[f"{aset}|{period}"] = row
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", default="A,B")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    sets = analysis_sets()
    jobs, meta = [], []
    for aset in a.sets.split(","):
        tick = sets[aset]
        prices = load_prices(tick)
        rets = log_returns(prices)
        masks = sub_period_mask(rets.index)
        for t in tick:
            r = rets[t].to_numpy()
            jobs.append((t, "full", r, aset == "A")); meta.append(aset)
            for name, m in masks.items():
                jobs.append((t, name, r[m], False)); meta.append(aset)
    print(f"{len(jobs)} fits queued ({time.time() - t0:.0f} s to load)", flush=True)
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        results = list(ex.map(fit_one, jobs, chunksize=8))
    rows, resid = [], []
    dates_by_ticker = {}
    for (job, aset), (row, z) in zip(zip(jobs, meta), results):
        row["set"] = aset
        rows.append(row)
        if z is not None and aset == "A":
            t = job[0]
            if t not in dates_by_ticker:
                p = load_prices([t]); rr = log_returns(p)[t]
                dates_by_ticker[t] = rr.index[np.isfinite(rr.to_numpy())]
            resid.append(pd.DataFrame({"date": dates_by_ticker[t], "ticker": t, "z": z.astype(np.float32)}))
    fits = pd.DataFrame(rows)
    fits.to_csv(os.path.join(OUT, "garch_fits.csv"), index=False)
    if resid:
        pd.concat(resid, ignore_index=True).to_parquet(os.path.join(OUT, "residuals.parquet"), index=False, compression="zstd")
    summ = {"spec": DEFAULT.to_dict(), "model": "arch_model(100 r, mean=Constant, vol=GARCH, p=1, o=1, q=1, dist=t); persistence = alpha + gamma/2 + beta",
            "min_obs": MIN_OBS, "n_boot_over_stocks": N_BOOT, "sets": {k: sets[f"n_{k}"] for k in ("A", "B")},
            "survivorship": "set A = flag-free full-history survivors (no delistings by construction); set B = shorter flag-free series; "
                            "tails and unconditional variance are understated relative to the full universe (REG-15); the literature values "
                            "beside are index/portfolio-level and are NOT tolerances",
            "literature_beside": LIT, "summary": summarise(fits), "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summ, fh, indent=1)
    L = ["# E3.1 per-stock GJR-GARCH(1,1)-t fits (v2.1 Phase 1; PREREG_PHASE_1.md section 3)", "",
         f"Model: {summ['model']}. Sets: A = {sets['n_A']} flag-free full-history names (primary), B = {sets['n_B']} shorter flag-free series. "
         f"Windows: full 2000-01-03..2024-12-31 and four sub-periods; a fit needs >= {MIN_OBS} returns. Medians carry a {N_BOOT}-resample "
         "bootstrap over stocks (95 %). Survivor caveat: set A has no delistings by construction; tails and unconditional variance are "
         "understated relative to the full universe (REG-15). Literature beside (read by the third pass, not tolerances): Engle 2001 "
         "alpha 0.077 / beta 0.905 (portfolio, daily 1990-2000); plan sanity range persistence 0.95-0.99, nu 4-8.", "",
         "| set | period | n | converged | alpha (median [CI]; IQR) | gamma | beta | nu | persistence | uncond. daily sd | sample sd |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, r in summ["summary"].items():
        aset, per = key.split("|")
        def f(k, d=3):
            v = r[k]; return f"{v['median']:.{d}f} [{v['ci95'][0]:.{d}f}, {v['ci95'][1]:.{d}f}]; {v['p25']:.{d}f}-{v['p75']:.{d}f}"
        L.append(f"| {aset} | {per} | {r['n_stocks']} | {r['n_converged']} | {f('alpha')} | {f('gamma')} | {f('beta')} | {f('nu', 2)} | {f('persistence')} | {f('uncond_sd', 4)} | {f('sample_sd', 4)} |")
    with open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"done in {time.time() - t0:.0f} s -> {OUT}")


if __name__ == "__main__":
    main()
