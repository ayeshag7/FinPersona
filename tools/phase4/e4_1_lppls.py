"""
E4.1's LPPLS stage (PREREG_PHASE_4.md section 3): the Filimonov-Sornette linearised calibration on every
panel run-up, with the registered stability DIAGNOSTIC.

    python -m tools.phase4.e4_1_lppls [--workers 3] [--restarts 20] [--limit N]

Registered protocol, fixed before any fit: window [start, top] per run-up; search tc in (end, end + 63],
m in (0.01, 0.99), omega in [1, 20]; 20 random restarts per episode with a fixed seed (the episode's top
index), Nelder-Mead, the four linear parameters solved exactly at each evaluation.

Stability is a DIAGNOSTIC, never a filter: an episode is `stable` iff the across-restart IQR of m is < 0.10
and of omega is < 2.0.  Population statistics are reported over ALL episodes and over stable ones separately.

Registered trigger for E4.4: the LPPLS route supports a super-exponential mania drift iff the stable share is
>= 0.50 AND the median m is inside (0, 1) with a CI excluding 1.0.  If not met, E4.4 reports the failure and
falls back to the scripted-drift alternative with its shape FIT from the run-up table -- NOT by relaxing this.

Resumable: results are cached per episode in lppls_fits.csv and existing rows are skipped.

Output: docs/env_v2/generated/v2_1/e4_1/{lppls_fits.csv, lppls.json, lppls.md}
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
os.environ.setdefault("OMP_NUM_THREADS", "1")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e4_1")
N_BOOT = 1000
SEED_BOOT = 400030
RESTARTS = 20


_PX_CACHE = {}


def _logp(ticker):
    """Per-worker price cache.  Without it every episode re-reads the ticker's price file, which is what
    dominates the run: the fit itself is 0.8 s but a reload per episode is far more."""
    import numpy as _np
    if ticker not in _PX_CACHE:
        from tools.phase1.panel import load_prices
        p = load_prices([ticker]).ffill()[ticker].to_numpy(float)
        _PX_CACHE[ticker] = _np.log(_np.where(_np.isfinite(p) & (p > 0), p, _np.nan))
    return _PX_CACHE[ticker]


def _fit_one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from tools.phase3.episodes import lppls_fit
    ticker, start, top, restarts = args
    try:
        lp = _logp(ticker)
        f = lppls_fit(lp, int(start), int(top), n_restarts=restarts, seed=int(top))
    except Exception as e:                                   # noqa: BLE001 - recorded, never silently dropped
        return {"ticker": ticker, "top": int(top), "error": str(e)[:120]}
    if f is None:
        return {"ticker": ticker, "top": int(top), "error": "no convergence"}
    return {"ticker": ticker, "top": int(top), **f}


def boot_share(flags, groups, n_boot=N_BOOT, seed=SEED_BOOT):
    """Stock-clustered bootstrap CI for a share."""
    flags = np.asarray(flags, bool)
    g = np.asarray(groups)
    stocks = np.array(sorted(set(g.tolist())))
    idx_by = {t: np.where(g == t)[0] for t in stocks}
    rng = np.random.default_rng(seed)
    bs = [float(flags[np.concatenate([idx_by[t] for t in rng.choice(stocks, len(stocks), replace=True)])].mean())
          for _ in range(n_boot)]
    return float(flags.mean()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], len(stocks)


def boot_median(vals, groups, n_boot=N_BOOT, seed=SEED_BOOT + 1):
    v = np.asarray(vals, float)
    g = np.asarray(groups)
    ok = np.isfinite(v)
    v, g = v[ok], g[ok]
    stocks = np.array(sorted(set(g.tolist())))
    idx_by = {t: np.where(g == t)[0] for t in stocks}
    rng = np.random.default_rng(seed)
    bs = [float(np.median(v[np.concatenate([idx_by[t] for t in rng.choice(stocks, len(stocks), replace=True)])]))
          for _ in range(n_boot)]
    return float(np.median(v)), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], int(len(v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--restarts", type=int, default=RESTARTS)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    ru = pd.read_csv(os.path.join(OUT, "runup4.csv"))
    if a.limit:
        ru = ru.head(a.limit)
    cache_p = os.path.join(OUT, "lppls_fits.csv")
    done = set()
    if os.path.exists(cache_p):
        old = pd.read_csv(cache_p)
        done = set(zip(old["ticker"].astype(str), old["top"].astype(int)))
        print(f"[cache] {len(done)} fits already on disk", flush=True)
    todo = [(str(r["ticker"]), int(r["start"]), int(r["top"]), a.restarts)
            for _, r in ru.iterrows() if (str(r["ticker"]), int(r["top"])) not in done]
    todo.sort()          # group a ticker's episodes together so the per-worker price cache actually hits
    print(f"[lppls] {len(todo)} episodes to fit at {a.restarts} restarts, {a.workers} workers", flush=True)
    rows = []
    if todo:
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for i, out in enumerate(ex.map(_fit_one, todo, chunksize=8), 1):
                rows.append(out)
                if i % 200 == 0:
                    print(f"    {i}/{len(todo)}  ({time.time() - t0:.0f} s)", flush=True)
        new = pd.DataFrame(rows)
        df = pd.concat([pd.read_csv(cache_p), new], ignore_index=True) if os.path.exists(cache_p) else new
        df.to_csv(cache_p, index=False)
    df = pd.read_csv(cache_p)
    ok = df[df.get("error").isna()] if "error" in df.columns else df
    ok = ok[np.isfinite(pd.to_numeric(ok["m"], errors="coerce"))]

    m_pt, m_ci, n_m = boot_median(ok["m"], ok["ticker"])
    w_pt, w_ci, _ = boot_median(ok["omega"], ok["ticker"])
    r2_pt, r2_ci, _ = boot_median(ok["r2"], ok["ticker"])
    s_pt, s_ci, n_st = boot_share(ok["stable"].astype(bool), ok["ticker"])
    stab = ok[ok["stable"].astype(bool)]
    res = {"design": {"prereg": "PREREG_PHASE_4.md section 3", "restarts": a.restarts,
                      "bounds": {"m": [0.01, 0.99], "omega": [1.0, 20.0], "tc_days_past_end": [0.5, 63]},
                      "seed_rule": "each episode's own top index", "n_boot": N_BOOT,
                      "method": "Filimonov & Sornette (2013) linearisation; Nelder-Mead over (tc, m, omega), "
                                "the four linear parameters solved exactly at every evaluation"},
           "n_attempted": int(len(df)), "n_converged": int(len(ok)),
           "n_failed": int(len(df) - len(ok)), "n_stocks": int(n_st),
           "all_episodes": {"m_median": m_pt, "m_ci95": m_ci,
                            "omega_median": w_pt, "omega_ci95": w_ci,
                            "r2_median": r2_pt, "r2_ci95": r2_ci, "n": n_m},
           "stable_share": {"point": s_pt, "ci95": s_ci, "n": int(len(ok))},
           }
    if len(stab) > 20:
        ms, mc, ns = boot_median(stab["m"], stab["ticker"], seed=SEED_BOOT + 2)
        ws, wc, _ = boot_median(stab["omega"], stab["ticker"], seed=SEED_BOOT + 3)
        hz, hc, _ = boot_median(stab["hazard_at_end"], stab["ticker"], seed=SEED_BOOT + 4)
        res["stable_episodes"] = {"m_median": ms, "m_ci95": mc, "omega_median": ws, "omega_ci95": wc,
                                  "hazard_at_end_median": hz, "hazard_at_end_ci95": hc, "n": ns}
    # ---- the registered E4.4 trigger
    m_excludes_1 = bool(m_ci[1] < 1.0)
    trigger = bool(s_pt >= 0.50 and 0.0 < m_pt < 1.0 and m_excludes_1)
    res["e4_4_trigger"] = {
        "rule": "supports a super-exponential mania drift iff the stable share >= 0.50 AND the median m is "
                "inside (0,1) with a CI excluding 1.0",
        "stable_share": s_pt, "stable_share_ci95": s_ci,
        "m_median": m_pt, "m_ci95": m_ci, "m_ci_excludes_1": m_excludes_1,
        "met": trigger,
        "consequence": ("E4.4 draws kappa and the mania length jointly from these fits"
                        if trigger else
                        "E4.4 reports the LPPLS route as UNSUPPORTED and uses the scripted-drift alternative "
                        "with its shape FIT from the run-up table -- the registered fallback, not a relaxed rule")}
    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "lppls.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    L = ["# E4.1 LPPLS fits on the panel's run-ups", "",
         "`python -m tools.phase4.e4_1_lppls` - PREREG_PHASE_4.md section 3.", "",
         f"{res['n_converged']} of {res['n_attempted']} run-ups converged over {n_st} stocks "
         f"at {a.restarts} restarts each.", "",
         "| statistic | all episodes | stable only |", "|---|---|---|",
         f"| m (median) | {m_pt:.3f} [{m_ci[0]:.3f}, {m_ci[1]:.3f}] | "
         f"{res.get('stable_episodes', {}).get('m_median', float('nan')):.3f} |",
         f"| omega (median) | {w_pt:.2f} [{w_ci[0]:.2f}, {w_ci[1]:.2f}] | "
         f"{res.get('stable_episodes', {}).get('omega_median', float('nan')):.2f} |",
         f"| R2 (median) | {r2_pt:.3f} [{r2_ci[0]:.3f}, {r2_ci[1]:.3f}] | - |",
         f"| stable share | {s_pt:.3f} [{s_ci[0]:.3f}, {s_ci[1]:.3f}] | - |", "",
         "## The registered E4.4 trigger", "",
         f"- rule: {res['e4_4_trigger']['rule']}",
         f"- stable share {s_pt:.3f} [{s_ci[0]:.3f}, {s_ci[1]:.3f}] (needs >= 0.50)",
         f"- median m {m_pt:.3f} [{m_ci[0]:.3f}, {m_ci[1]:.3f}] (CI must exclude 1.0: {m_excludes_1})",
         f"- **met: {trigger}**", "", f"- consequence: {res['e4_4_trigger']['consequence']}", ""]
    with open(os.path.join(OUT, "lppls.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("\n".join(L[4:]), flush=True)


if __name__ == "__main__":
    main()
