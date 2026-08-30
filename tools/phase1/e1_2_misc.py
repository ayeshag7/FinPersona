"""
Phase 1 FIT values that need no simulation (PREREG_PHASE_1.md sections 4.5 and 7):
  * mu_V from Shiller's nominal S&P price (price-only monthly log change, 2000-2024 window adopted; 1871-2024 beside);
  * df_V from the tails of standardised quarterly EPS changes on the EDGAR sub-set (KS-equivalence to N(0,1) vs t5);
  * the start-price range (P5, P95) of unadjusted Close over set A on 40 random dates (E1.1, mechanisms A and C);
  * the V_hat measurement-noise sd for the recovery study (sd of log(EPS_ttm,q / EPS_ttm,q-4), median over stocks).

    python -m tools.phase1.e1_2_misc
Outputs: docs/env_v2/generated/v2_1/e1_2/misc_fits.json, misc_fits.md
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from tools.phase1.panel import DEFAULT, analysis_sets, load_prices, quarterly_eps, shiller, OUT_DIR  # noqa: E402

OUT = os.path.join(OUT_DIR, "e1_2")
N_BOOT = 1000
N_DATES = 40
DATE_SEED = 20260829


def ks_to(sample: np.ndarray, cdf) -> float:
    return float(stats.kstest(sample, cdf).statistic)


def ks_upper(sample: np.ndarray, cdf, clusters: np.ndarray, n_boot: int = N_BOOT, seed: int = 0):
    """Bootstrap (over clusters = stocks) 95 % upper limit of the one-sample KS distance."""
    rng = np.random.default_rng(seed)
    ug = np.unique(clusters); idx = {g: np.where(clusters == g)[0] for g in ug}
    vals = np.empty(n_boot)
    for b in range(n_boot):
        pick = ug[rng.integers(0, len(ug), len(ug))]
        s = np.concatenate([sample[idx[g]] for g in pick])
        vals[b] = ks_to(s, cdf)
    return float(ks_to(sample, cdf)), float(np.percentile(vals, 97.5))


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    out = {"spec": DEFAULT.to_dict()}
    # ---------------------------------------------------------------- mu_V (Shiller)
    sh = shiller()
    lp = np.log(sh["P"].astype(float))
    d = lp.diff().dropna()
    def mu_block(mask, label):
        x = d[mask]
        rng = np.random.default_rng(0)
        # moving-block bootstrap over months (block 12) for the mean
        T = len(x); vals = np.empty(N_BOOT); xv = x.to_numpy()
        for b in range(N_BOOT):
            starts = rng.integers(0, T - 12 + 1, int(np.ceil(T / 12)))
            idx = np.concatenate([np.arange(s, s + 12) for s in starts])[:T]
            vals[b] = xv[idx].mean()
        return {"label": label, "n_months": int(T), "mean_monthly_log_change": float(xv.mean()),
                "per_trading_day": float(xv.mean() / 21.0), "ci95_per_day": [float(np.percentile(vals, 2.5) / 21), float(np.percentile(vals, 97.5) / 21)],
                "annualised_pct": float(xv.mean() * 12 * 100)}
    out["mu_V"] = {"adopted_window": mu_block((d.index >= "2000-01-01") & (d.index <= "2024-12-01"), "2000-01..2024-12 (the panel's window; adopted)"),
                   "long_run": mu_block(d.index <= "2024-12-01", "1871-02..2024-12 (beside)"),
                   "source": "Shiller ie_data.xls via shillerdata.com (E1.0 need #4), column P (nominal S&P composite price), price-only",
                   "literature_beside": "DMS 2025 (read by the third pass, LOG 4.1): US 1900-2024 nominal equity return 9.7 %/yr (total return, incl. dividends); "
                                        "v2 used mu_V = 0.00025/day (6.5 %/yr, 'plan')"}
    # ---------------------------------------------------------------- df_V (EPS tails) and V_hat noise
    sets = analysis_sets(write=False)
    zs, cl, noise_sd = [], [], []
    n_stocks = 0
    for t in sets["A"]:
        q = quarterly_eps(t)
        if q is None or len(q) < 16:
            continue
        q = q.sort_values("end").reset_index(drop=True)
        e = q["eps"].to_numpy()
        # seasonal change scaled by the stock's own sd of the change
        dq = e[4:] - e[:-4]
        if len(dq) < 12 or dq.std() == 0:
            continue
        z = dq / dq.std(ddof=1)
        zs.append(z); cl.append(np.full(len(z), n_stocks)); n_stocks += 1
        # V_hat noise: sd of log(EPS_ttm,q / EPS_ttm,q-4) over quarters with positive ttm
        ttm = np.convolve(e, np.ones(4), mode="valid")
        ok = (ttm[4:] > 0) & (ttm[:-4] > 0)
        g = np.log(ttm[4:][ok] / ttm[:-4][ok])
        if len(g) >= 8:
            noise_sd.append(float(g.std(ddof=1)))
    z = np.concatenate(zs); c = np.concatenate(cl)
    t5 = stats.t(5, scale=1 / np.sqrt(5 / 3))
    ks_n, up_n = ks_upper(z, "norm", c)
    ks_t, up_t = ks_upper(z, t5.cdf, c)
    rng = np.random.default_rng(1)
    ug = np.unique(c); idx = {g: np.where(c == g)[0] for g in ug}
    kb = np.array([stats.kurtosis(np.concatenate([z[idx[g]] for g in ug[rng.integers(0, len(ug), len(ug))]])) for _ in range(N_BOOT)])
    verdict = "gaussian" if (up_n < 0.10 and up_t >= 0.10) else ("t5" if (up_t < 0.10 and up_n >= 0.10) else "DESIGN (both variants carried)")
    out["df_V"] = {"n_stocks": n_stocks, "n_obs": int(len(z)), "statistic": "seasonal quarterly EPS change / own sd, pooled",
                   "ks_to_normal": ks_n, "ks_to_normal_upper95": up_n, "ks_to_t5": ks_t, "ks_to_t5_upper95": up_t,
                   "excess_kurtosis": float(stats.kurtosis(z)), "excess_kurtosis_ci95": [float(np.percentile(kb, 2.5)), float(np.percentile(kb, 97.5))],
                   "rule": "FIT gaussian if only the normal upper limit < 0.10; FIT t5 if only the t5 upper limit < 0.10; else DESIGN",
                   "verdict": verdict}
    out["vhat_noise"] = {"n_stocks": len(noise_sd), "sd_log_epsttm_growth_median": float(np.median(noise_sd)),
                         "iqr": [float(np.percentile(noise_sd, 25)), float(np.percentile(noise_sd, 75))],
                         "use": "measurement-error sd (per year) of V_hat in the recovery study; persistence bracketed {0, 0.9}/quarter (DESIGN)"}
    # ---------------------------------------------------------------- start-price range
    close = load_prices(sets["A"], col=DEFAULT.level_col).ffill()
    rng = np.random.default_rng(DATE_SEED)
    dates = close.index[np.sort(rng.choice(len(close.index), N_DATES, replace=False))]
    vals = close.loc[dates].to_numpy().ravel(); vals = vals[np.isfinite(vals)]
    p5, p95 = float(np.percentile(vals, 5)), float(np.percentile(vals, 95))
    bd = np.array([[np.percentile(close.loc[dates[rng.integers(0, N_DATES, N_DATES)]].to_numpy().ravel(), q) for q in (5, 95)] for _ in range(N_BOOT)])
    out["start_price_range"] = {"P_lo": p5, "P_hi": p95, "ci95_P_lo": [float(np.percentile(bd[:, 0], 2.5)), float(np.percentile(bd[:, 0], 97.5))],
                                "ci95_P_hi": [float(np.percentile(bd[:, 1], 2.5)), float(np.percentile(bd[:, 1], 97.5))],
                                "median": float(np.median(vals)), "n_obs": int(len(vals)), "n_dates": N_DATES, "date_seed": DATE_SEED,
                                "dates": [str(x.date()) for x in dates], "column": DEFAULT.level_col, "set": "A"}
    out["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "misc_fits.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    m = out["mu_V"]; dv = out["df_V"]; sp = out["start_price_range"]
    L = ["# Phase 1 FIT values without simulation (PREREG_PHASE_1.md sections 4.5, 7)", "",
         "## mu_V (Shiller nominal S&P price, price-only)", "",
         f"- Adopted (2000-01..2024-12): {m['adopted_window']['per_trading_day']:.6f}/day [{m['adopted_window']['ci95_per_day'][0]:.6f}, "
         f"{m['adopted_window']['ci95_per_day'][1]:.6f}] (block bootstrap over months, block 12), i.e. {m['adopted_window']['annualised_pct']:.1f} %/yr; n = {m['adopted_window']['n_months']} months.",
         f"- Long run (1871-02..2024-12): {m['long_run']['per_trading_day']:.6f}/day [{m['long_run']['ci95_per_day'][0]:.6f}, {m['long_run']['ci95_per_day'][1]:.6f}], "
         f"{m['long_run']['annualised_pct']:.1f} %/yr; n = {m['long_run']['n_months']}.",
         f"- v2 value 0.00025/day (6.5 %/yr, stipulated). Literature beside: {m['literature_beside']}.", "",
         "## df_V (tails of standardised seasonal quarterly EPS changes, EDGAR sub-set)", "",
         f"- n = {dv['n_obs']} changes over {dv['n_stocks']} stocks; excess kurtosis {dv['excess_kurtosis']:.2f} [{dv['excess_kurtosis_ci95'][0]:.2f}, {dv['excess_kurtosis_ci95'][1]:.2f}].",
         f"- KS distance to N(0,1): {dv['ks_to_normal']:.3f} (bootstrap 95 % upper limit {dv['ks_to_normal_upper95']:.3f}); to t5: {dv['ks_to_t5']:.3f} (upper {dv['ks_to_t5_upper95']:.3f}).",
         f"- Rule: {dv['rule']}. **Verdict: {dv['verdict']}.**", "",
         "## V_hat measurement noise (for the recovery study)", "",
         f"- median over {out['vhat_noise']['n_stocks']} stocks of sd(log EPS_ttm,q / EPS_ttm,q-4) = {out['vhat_noise']['sd_log_epsttm_growth_median']:.3f} "
         f"(IQR {out['vhat_noise']['iqr'][0]:.3f}-{out['vhat_noise']['iqr'][1]:.3f}).", "",
         "## Start-price range (E1.1 mechanisms A and C)", "",
         f"- P5 = {sp['P_lo']:.2f} [{sp['ci95_P_lo'][0]:.2f}, {sp['ci95_P_lo'][1]:.2f}], P95 = {sp['P_hi']:.2f} [{sp['ci95_P_hi'][0]:.2f}, {sp['ci95_P_hi'][1]:.2f}] of unadjusted Close "
         f"over set A on {sp['n_dates']} random dates (seed {sp['date_seed']}), {sp['n_obs']} observations; median {sp['median']:.2f}. FIT.", ""]
    with open(os.path.join(OUT, "misc_fits.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))
    print(json.dumps({k: v for k, v in out.items() if k != "spec"}, indent=1, default=str)[:3000])


if __name__ == "__main__":
    main()
