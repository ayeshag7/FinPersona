"""
v2.1 Phase 7 -- E7.3: the Merton table on the environment's OWN fitted risk and return, against the practitioner
bands (PREREG_PHASE_7.md 3; REG-13; D9 recorded as A, DECISION_LOG P7-3).

    python -u -m tools.phase7.e7_3_merton --seeds 500 --workers 6

One tool computes (mu, sigma) AND the comparison it feeds, so the table and the bands it is set against come from
one construction (rule 12).  Nothing here is stipulated:

  mu, sigma   annualised mean and sd of the daily TOTAL log return of the risky asset on the frozen generator --
              r_t = log((P_t + D_t) / P_{t-1}) with D_t the dividend per share paid on day t (E7.4 / D10 = pay),
              measured on the flat scenario at the registered seed count, with a cluster-bootstrap interval over
              paths.  The other three scenarios are reported beside it.  The v2 documents' "price-only drift
              6.5 %/yr, annual sigma ~ 28 %" is SUPERSEDED and reported as superseded.
  r           0 -- cash does not accrue in this environment (`simulation/portfolio_v2.py` never credits interest).
              A property of the environment, stated, not an assumption.
  w*          Merton (1969/1971) single-risky-asset CRRA share (mu - r) / (gamma sigma^2), cash share 1 - w*,
              reported clipped to [0, 1] and unclipped beside, for gamma in {2, 3, 4, 6, 8, 10}.

The JFE ordering check is NOT run: `evaluation/targets.jfe_ordering_check_available()` is False because Table 7
gives trait coefficients, not a conservative-minus-aggressive spread (PREREG 3.3).

Output: <out>/merton.{json,md,csv}
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
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN, pin_state  # noqa: E402

OUT = os.path.join(GEN, "e7_3")
SEED0 = 40000            # the Phase-6 checklist's seed block, disjoint from 16A's scored seeds 0..99
TRADING_DAYS = 252
GAMMAS = (2, 3, 4, 6, 8, 10)
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")


def _one(args):
    """Daily total and price-only log returns of one path, plus the dividend cash it paid per share."""
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from simulation.dividends import dividend_schedule
    sc, seed, T = args
    env = SyntheticMarketEnv(sc, T, seed)
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    P = d["price"].to_numpy(float)
    D = dividend_schedule(env, 1, len(P))[:, 0]
    r_price = np.diff(np.log(P))
    r_total = np.log((P[1:] + D[1:]) / P[:-1])
    return (sc, int(seed), r_total, r_price, float(D.sum()), float(P[0]), int((D != 0).sum()))


def _boot(stat, per_path, n_boot=500, seed=0):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(per_path))
    draws = np.array([stat([per_path[i] for i in rng.choice(idx, len(idx))]) for _ in range(n_boot)])
    ok = np.isfinite(draws)
    return float(np.percentile(draws[ok], 2.5)), float(np.percentile(draws[ok], 97.5))


def moments(rets, n_boot=500, seed=0):
    """Annualised (mu, sigma) pooled over paths, with a cluster-bootstrap interval over paths."""
    def mu_of(rs):
        return float(np.mean(np.concatenate(rs)) * TRADING_DAYS)

    def sd_of(rs):
        return float(np.std(np.concatenate(rs), ddof=1) * np.sqrt(TRADING_DAYS))
    mu, sd = mu_of(rets), sd_of(rets)
    mu_ci = _boot(mu_of, rets, n_boot, seed)
    sd_ci = _boot(sd_of, rets, n_boot, seed + 1)
    return {"mu": mu, "mu_ci95": list(mu_ci), "sigma": sd, "sigma_ci95": list(sd_ci),
            "n_paths": len(rets), "n_days": int(sum(len(r) for r in rets))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    from evaluation.targets import BANDS, CATEGORY_OF_PERSONA, jfe_ordering_check_available, JFE_SPREAD_WITHDRAWN_REASON

    jobs = [(sc, SEED0 + s, a.T) for sc in SCENARIOS for s in range(a.seeds)]
    print(f"[merton] {len(jobs)} paths on {a.workers} workers", flush=True)
    by_sc = {sc: {"total": [], "price": [], "div": [], "n_ex": []} for sc in SCENARIOS}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, (sc, seed, rt, rp, dsum, p0, nex) in enumerate(ex.map(_one, jobs, chunksize=8), 1):
            by_sc[sc]["total"].append(rt); by_sc[sc]["price"].append(rp)
            by_sc[sc]["div"].append(dsum / p0); by_sc[sc]["n_ex"].append(nex)
            if i % 400 == 0:
                print(f"  {i}/{len(jobs)} ({time.time() - t0:.0f} s)", flush=True)

    per_scenario = {}
    for sc in SCENARIOS:
        b = by_sc[sc]
        per_scenario[sc] = {
            "total_return": moments(b["total"], seed=hash(sc) % 1000),
            "price_only": moments(b["price"], seed=hash(sc) % 1000 + 7),
            "dividend_yield_realised_annualised": float(np.mean(b["div"]) * TRADING_DAYS / a.T),
            "payer_share": float(np.mean([n > 0 for n in b["n_ex"]])),
            "mean_ex_dates_per_path": float(np.mean(b["n_ex"])),
        }
    prim = per_scenario["flat"]["total_return"]
    mu, sig = prim["mu"], prim["sigma"]
    r_f = 0.0

    rows = []
    for g in GAMMAS:
        w = (mu - r_f) / (g * sig ** 2)
        w_lo = (prim["mu_ci95"][0] - r_f) / (g * prim["sigma_ci95"][1] ** 2)
        w_hi = (prim["mu_ci95"][1] - r_f) / (g * prim["sigma_ci95"][0] ** 2)
        rows.append({"gamma": g, "risky_share_unclipped": w, "risky_share": float(np.clip(w, 0, 1)),
                     "cash_share": float(np.clip(1 - w, 0, 1)), "cash_share_unclipped": 1 - w,
                     "cash_share_ci95_lo": float(1 - w_hi), "cash_share_ci95_hi": float(1 - w_lo)})
    mt = pd.DataFrame(rows)
    mt.to_csv(os.path.join(a.out, "merton.csv"), index=False)

    # where each persona's practitioner band sits relative to the Merton cash shares
    placement = []
    for persona, cat in (("ISFJ", "conservative"), ("INTJ", "balanced"), ("ENTJ", "aggressive")):
        lo, hi = BANDS[cat]
        inside = [int(r["gamma"]) for _, r in mt.iterrows() if lo <= r["cash_share"] <= hi]
        nearest = min(GAMMAS, key=lambda g: abs(float(mt[mt.gamma == g]["cash_share"].iloc[0]) - (lo + hi) / 2))
        placement.append({"persona": persona, "category": cat, "band": [lo, hi],
                          "gammas_inside_band": inside,
                          "nearest_gamma_to_band_centre": int(nearest),
                          "merton_cash_at_nearest_gamma": float(mt[mt.gamma == nearest]["cash_share"].iloc[0])})

    doc = {"meta": {"seeds_per_scenario": a.seeds, "seed0": SEED0, "T": a.T, "trading_days": TRADING_DAYS,
                    "risk_free": r_f, "gammas": list(GAMMAS), "state": pin_state(),
                    "dividends": "paid into cash on the generator's own ex-dates (E7.4 / D10); the price path is "
                                 "NOT ex-dividend adjusted, so the total return is the price return plus the yield",
                    "superseded": "the v2 documents' 'price-only drift 6.5 %/yr, annual sigma ~ 28 %' is superseded "
                                  "by the numbers in this file, measured on the frozen v2.1 generator",
                    "seconds": round(time.time() - t0),
                    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
           "primary_population": "flat", "per_scenario": per_scenario,
           "merton_table": mt.to_dict("records"), "placement": placement,
           "jfe_ordering_check": {"available": bool(jfe_ordering_check_available()),
                                  "reason": JFE_SPREAD_WITHDRAWN_REASON}}
    json.dump(doc, open(os.path.join(a.out, "merton.json"), "w", encoding="utf-8"), indent=1, default=float)

    L = ["# E7.3 — the Merton table on the environment's own fitted risk and return", "",
         f"Measured on the frozen v2.1 generator, {a.seeds} seeds per scenario (seeds {SEED0}..), T = {a.T}, "
         f"{TRADING_DAYS} trading days a year, dividends paid into cash on the generator's own ex-dates. "
         f"Cluster-bootstrap 95 % intervals over paths (500 resamples). Risk-free rate **0**: cash does not accrue "
         f"in this environment.", "",
         "## The environment's own (mu, sigma)", "",
         "| scenario | mu (total return) | sigma (total return) | mu (price only) | sigma (price only) | "
         "realised dividend yield | payer share |", "|---|---|---|---|---|---|---|"]
    for sc in SCENARIOS:
        p = per_scenario[sc]; tr = p["total_return"]; po = p["price_only"]
        L.append(f"| {sc}{' (primary)' if sc == 'flat' else ''} | {tr['mu']:.4f} [{tr['mu_ci95'][0]:.4f}, "
                 f"{tr['mu_ci95'][1]:.4f}] | {tr['sigma']:.4f} [{tr['sigma_ci95'][0]:.4f}, {tr['sigma_ci95'][1]:.4f}] | "
                 f"{po['mu']:.4f} | {po['sigma']:.4f} | {p['dividend_yield_realised_annualised']:.5f} | "
                 f"{p['payer_share']:.3f} |")
    L += ["", f"The v2 documents' price-only drift of 6.5 %/yr and annual sigma of about 28 % are **superseded**: "
              f"on the frozen generator the flat scenario's price-only figures are "
              f"{per_scenario['flat']['price_only']['mu']:.4f} and "
              f"{per_scenario['flat']['price_only']['sigma']:.4f}.", "",
          "## Merton cash shares (flat, total return)", "",
          "| gamma | risky share w* | cash share 1 - w* | cash share, unclipped | 95 % interval |",
          "|---|---|---|---|---|"]
    for _, r in mt.iterrows():
        L.append(f"| {int(r['gamma'])} | {r['risky_share']:.3f} | **{r['cash_share']:.3f}** | "
                 f"{r['cash_share_unclipped']:.3f} | [{r['cash_share_ci95_lo']:.3f}, {r['cash_share_ci95_hi']:.3f}] |")
    L += ["", "## Where each persona's practitioner band sits (reading A, the scored default; D9 / P7-3)", "",
          "| persona | category | practitioner cash band | gammas whose Merton cash share falls inside it | "
          "nearest gamma to the band centre | Merton cash there |", "|---|---|---|---|---|---|"]
    for p in placement:
        L.append(f"| {p['persona']} | {p['category']} | {p['band'][0]:.2f}–{p['band'][1]:.2f} | "
                 f"{p['gammas_inside_band'] or '—'} | {p['nearest_gamma_to_band_centre']} | "
                 f"{p['merton_cash_at_nearest_gamma']:.3f} |")
    L += ["", "## The JFE ordering check", "",
          f"**Not run.** {JFE_SPREAD_WITHDRAWN_REASON}", ""]
    with open(os.path.join(a.out, "merton.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
