"""
E5.5 -- sentiment: the SF Fed index deconvolved and fitted, the market-return loadings, the reverse (Tetlock)
regression, the valuation link (design B) and the AAII survey (design C).  PREREG_PHASE_5.md section 8.1.

    python -m tools.phase5.e5_5_sentiment

Data: datasets/06_sentiment/sf_fed_news_sentiment.csv (daily, calendar days, 1980-01-01 -> 2026-08-23); the
Fama-French daily market factor (Mkt-RF + RF); Shiller monthly CAPE; the AAII weekly survey.

(a) Deconvolution.  The published index is a trailing geometric average with a 5 % daily depreciation (FRBSF Economic
    Letter 2020-08, read at source 6 Sep 2026): s_t = lam s_{t-1} + (1 - lam) raw_t, lam = 0.95 (LIT).  So
    raw_t = (s_t - lam s_{t-1}) / (1 - lam) on consecutive calendar days (19 gaps in 17,000 days: the previous available
    day is treated as t-1 and the count is reported).  AR(1) + white measurement noise: rho = AC(2)/AC(1), noise share
    from AC(1); moving-block bootstrap (250-day blocks).
(b) Loadings.  Trading-day alignment: raw averaged over the calendar days since the previous trading day; z = Mkt /
    trailing-252-day sd.  raw_t = c + rho raw_{t-1} + b0 z_t + b1 z_{t-1} + e, OLS, Newey-West(10); full sample and
    sub-periods; the distributed-lag form with lags 1..5 as the cross-check.  Loadings per sd of raw sentiment.
(c) Reverse.  Mkt_{t+1} = a + gamma std(raw_t) + sum_{h<=5} phi_h Mkt_{t+1-h} + e; gamma in bp per sd (Tetlock: 8.1 bp;
    days 2-5 reversal 6.8 bp).
(d) Valuation link.  Monthly mean raw on the log-CAPE deviation from its trailing 120-month mean (DESIGN; full-sample
    mean beside), NW(12).
(e) AAII.  Weekly spread (Bull - Bear): AR(1) with intercept; loading on the standardised weekly log return of the S&P
    Close AAII bundles; NW(4).
Window references for rule (i): the same 200-trading-day statistics (ACF(1), corr(s, r)) in non-overlapping windows
of the deconvolved, trading-day-aligned series; for C, 40-week windows of the AAII spread.

Output: docs/env_v2/generated/v2_1/e5_5/sentiment.{json,md}, sf_fed_raw_daily.csv
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase5.common import GEN  # noqa: E402

OUT = os.path.join(GEN, "e5_5")
DS = os.path.join(ROOT, "datasets")
LAM = 0.95
N_BOOT = 500
BLOCK = 250
SUBPERIODS = [("1980-99", "1980-01-01", "1999-12-31"), ("2000-07", "2000-01-01", "2007-12-31"), ("2008-12", "2008-01-01", "2012-12-31"),
              ("2013-19", "2013-01-01", "2019-12-31"), ("2020-26", "2020-01-01", "2026-12-31")]


def ff_daily():
    z = zipfile.ZipFile(os.path.join(DS, "07_factors_valuation", "F-F_Research_Data_Factors_daily_CSV.zip"))
    txt = z.read(z.namelist()[0]).decode("latin-1").splitlines()
    start = next(i for i, l in enumerate(txt) if l.strip().startswith(",Mkt-RF"))
    rows = []
    for l in txt[start + 1:]:
        p = [x.strip() for x in l.split(",")]
        if len(p) < 5 or not p[0].isdigit() or len(p[0]) != 8:
            break
        rows.append((pd.Timestamp(p[0]), float(p[1]), float(p[4])))
    d = pd.DataFrame(rows, columns=["date", "mkt_rf", "rf"]).set_index("date")
    d["mkt"] = (d["mkt_rf"] + d["rf"]) / 100.0
    return d


def acf(x, k):
    x = np.asarray(x, float); x = x - x.mean()
    return float((x[:-k] * x[k:]).sum() / (x * x).sum())


def block_boot(x, fn, n_boot=N_BOOT, block=BLOCK, seed=550001):
    x = np.asarray(x, float); n = len(x); rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block)); out = []
    for _ in range(n_boot):
        starts = rng.integers(0, n - block, nb)
        xb = np.concatenate([x[s:s + block] for s in starts])[:n]
        out.append(fn(xb))
    out = np.asarray(out, float)
    return [float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))]


def nw_ols(y, X, lags):
    import statsmodels.api as sm
    Xc = sm.add_constant(X)
    fit = sm.OLS(y, Xc, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return fit


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    s = pd.read_csv(os.path.join(DS, "06_sentiment", "sf_fed_news_sentiment.csv"), parse_dates=["date"]).set_index("date")["News Sentiment"]
    s = s.sort_index()
    gaps = int((s.index.to_series().diff().dt.days > 1).sum())
    raw = ((s - LAM * s.shift(1)) / (1 - LAM)).dropna()
    raw.to_frame("raw").to_csv(os.path.join(OUT, "sf_fed_raw_daily.csv"))
    x = raw.to_numpy(float)
    ac1, ac2 = acf(x, 1), acf(x, 2)
    rho_corr = ac2 / ac1
    noise_share = 1.0 - ac1 / rho_corr          # var(m)/var(raw) under AR(1)+white noise
    decon = {"lam": LAM, "lam_source": "FRBSF Economic Letter 2020-08 (read 6 Sep 2026): 'depreciation rate of 5%'",
             "n_days": int(len(x)), "calendar_gaps_treated_as_consecutive": gaps,
             "published": {"sd": float(s.std()), "ac1": acf(s.to_numpy(float), 1), "ac21": acf(s.to_numpy(float), 21),
                           "ac252": acf(s.to_numpy(float), 252)},
             "raw": {"sd": float(x.std(ddof=1)), "ac1": ac1, "ac1_ci": block_boot(x, lambda v: acf(v, 1)),
                     "ac2": ac2, "ac5": acf(x, 5), "ac21": acf(x, 21),
                     "rho_ar1_plus_noise": rho_corr, "rho_ci": block_boot(x, lambda v: acf(v, 2) / acf(v, 1)),
                     "noise_variance_share": float(noise_share),
                     "noise_share_ci": block_boot(x, lambda v: 1.0 - acf(v, 1) ** 2 / acf(v, 2)),
                     "naive_ar1_ols": ac1}}

    ff = ff_daily()
    ff = ff[(ff.index >= raw.index.min()) & (ff.index <= raw.index.max())]
    # trading-day alignment: mean of raw over calendar days since the previous trading day
    td = ff.index
    pos = np.searchsorted(raw.index.to_numpy(), td.to_numpy(), side="right")
    agg = np.full(len(td), np.nan)
    prev = 0
    for i, p in enumerate(pos):
        if p > prev:
            agg[i] = x[prev:p].mean()
        prev = p
    al = pd.DataFrame({"raw": agg, "mkt": ff["mkt"].to_numpy()}, index=td).dropna()
    al["sd252"] = al["mkt"].rolling(252, min_periods=120).std().shift(1)
    al["z"] = al["mkt"] / al["sd252"]
    al = al.dropna()
    sd_raw = float(al["raw"].std(ddof=1))
    al["raw_l1"] = al["raw"].shift(1); al["z_l1"] = al["z"].shift(1)
    for h in range(2, 6):
        al[f"z_l{h}"] = al["z"].shift(h)

    def fit_ar_form(d):
        d = d.dropna(subset=["raw", "raw_l1", "z", "z_l1"])
        fit = nw_ols(d["raw"].to_numpy(), d[["raw_l1", "z", "z_l1"]].to_numpy(), 10)
        b = fit.params; se = fit.bse
        sd_res = float(np.sqrt(fit.mse_resid))
        return {"n": int(fit.nobs), "rho": float(b[1]), "rho_se": float(se[1]), "b0": float(b[2]), "b0_se": float(se[2]),
                "b1": float(b[3]), "b1_se": float(se[3]), "sd_resid": sd_res, "sd_raw": float(d["raw"].std(ddof=1)),
                "b0_per_sd_raw": float(b[2] / d["raw"].std(ddof=1)), "b1_per_sd_raw": float(b[3] / d["raw"].std(ddof=1)),
                "sd_resid_per_sd_raw": float(sd_res / d["raw"].std(ddof=1)), "r2": float(fit.rsquared)}
    loads = {"full": fit_ar_form(al), "sub_periods": {}}
    for name, lo, hi in SUBPERIODS:
        d = al[(al.index >= lo) & (al.index <= hi)]
        if len(d) > 500:
            loads["sub_periods"][name] = fit_ar_form(d)
    dl = al.dropna(subset=["raw", "z", "z_l1", "z_l2", "z_l3", "z_l4", "z_l5"])
    fdl = nw_ols(dl["raw"].to_numpy(), dl[["z", "z_l1", "z_l2", "z_l3", "z_l4", "z_l5"]].to_numpy(), 10)
    loads["distributed_lag_no_ar"] = {"coef_per_sd_raw": [float(v / sd_raw) for v in fdl.params[1:]],
                                      "se_per_sd_raw": [float(v / sd_raw) for v in fdl.bse[1:]], "n": int(fdl.nobs)}
    # contemporaneous correlation for reference
    loads["corr_raw_mkt_full"] = float(np.corrcoef(al["raw"], al["mkt"])[0, 1])

    # (c) reverse regression
    rv = al.copy()
    rv["raw_std"] = (rv["raw"] - rv["raw"].mean()) / sd_raw
    rv["mkt_f1"] = rv["mkt"].shift(-1)
    for h in range(0, 5):
        rv[f"mkt_l{h}"] = rv["mkt"].shift(h)
    rv["mkt_f2_5"] = sum(rv["mkt"].shift(-k) for k in range(2, 6))
    d = rv.dropna(subset=["mkt_f1", "raw_std"] + [f"mkt_l{h}" for h in range(5)])
    f1 = nw_ols(d["mkt_f1"].to_numpy(), d[["raw_std"] + [f"mkt_l{h}" for h in range(5)]].to_numpy(), 10)
    d2 = rv.dropna(subset=["mkt_f2_5", "raw_std"] + [f"mkt_l{h}" for h in range(5)])
    f2 = nw_ols(d2["mkt_f2_5"].to_numpy(), d2[["raw_std"] + [f"mkt_l{h}" for h in range(5)]].to_numpy(), 10)
    reverse = {"gamma_next_day_bp_per_sd": float(1e4 * f1.params[1]), "se_bp": float(1e4 * f1.bse[1]), "n": int(f1.nobs),
               "days2_5_cumulative_bp_per_sd": float(1e4 * f2.params[1]), "se2_5_bp": float(1e4 * f2.bse[1]),
               "tetlock_2007_read": {"next_day_bp": 8.1, "reversal_days_2_5_bp": 6.8, "level": "DJIA, index, daily"},
               "b_pred_in_force": {"b_pred": 0.0008, "b_rev": 0.0006, "label": "LIT (Tetlock), unchanged in every design"}}

    # (d) valuation link, monthly
    sh = pd.read_csv(os.path.join(DS, "04_shiller", "shiller_monthly.csv"))
    yr = np.floor(sh["Date"]).astype(int); mo = np.round((sh["Date"] - yr) * 100).astype(int)
    sh["month"] = pd.to_datetime(dict(year=yr, month=mo, day=1))
    cape = pd.to_numeric(sh["CAPE"], errors="coerce"); cape.index = sh["month"]
    cape = cape.dropna()
    lc = np.log(cape)
    dev_trail = (lc - lc.rolling(120, min_periods=60).mean()).dropna()
    dev_full = lc - lc[(lc.index >= "1980-01-01")].mean()
    rm = raw.resample("MS").mean()
    def val_fit(dev):
        d = pd.concat([rm.rename("raw"), dev.rename("dev")], axis=1).dropna()
        d = d[d.index >= "1980-01-01"]
        fit = nw_ols(d["raw"].to_numpy(), d[["dev"]].to_numpy(), 12)
        return {"coef_raw_per_unit_logdev": float(fit.params[1]), "se": float(fit.bse[1]), "n_months": int(fit.nobs),
                "coef_per_sd_raw_daily": float(fit.params[1] / sd_raw), "ci95_per_sd_raw_daily": [float((fit.params[1] - 1.96 * fit.bse[1]) / sd_raw),
                                                                                               float((fit.params[1] + 1.96 * fit.bse[1]) / sd_raw)],
                "r2": float(fit.rsquared), "sd_logdev": float(d["dev"].std(ddof=1))}
    valuation = {"trailing_120m_mean": val_fit(dev_trail), "full_sample_mean_from_1980": val_fit(dev_full),
                 "transfer": "DESIGN: a market-level coefficient on the log-CAPE deviation applied to a single stock's x = log(P/V)",
                 "v2_incumbent": "m_t = 0.6 tanh(2 x) -> a loading of 1.2 per unit x in squashed units (DESIGN, weakness item 23)"}

    # (e) AAII
    aa = pd.read_csv(os.path.join(DS, "06_sentiment", "aaii_sentiment_weekly.csv"), parse_dates=["Date"])
    aa = aa.dropna(subset=["Bullish", "Bearish"]).sort_values("Date").reset_index(drop=True)
    aa["spread"] = aa["Bullish"] - aa["Bearish"]
    aa["ret"] = np.log(pd.to_numeric(aa["Close"], errors="coerce")).diff()
    aa["sd52"] = aa["ret"].rolling(52, min_periods=26).std().shift(1)
    aa["z"] = aa["ret"] / aa["sd52"]
    aa["spread_l1"] = aa["spread"].shift(1); aa["z_l1"] = aa["z"].shift(1)
    d = aa.dropna(subset=["spread", "spread_l1", "z", "z_l1"])
    fa = nw_ols(d["spread"].to_numpy(), d[["spread_l1", "z", "z_l1"]].to_numpy(), 4)
    sd_sp = float(d["spread"].std(ddof=1))
    aaii = {"n_weeks": int(fa.nobs), "rho_w": float(fa.params[1]), "rho_w_se": float(fa.bse[1]),
            "b0_per_sd": float(fa.params[2] / sd_sp), "b0_se_per_sd": float(fa.bse[2] / sd_sp),
            "b1_per_sd": float(fa.params[3] / sd_sp), "sd_resid_per_sd": float(np.sqrt(fa.mse_resid) / sd_sp),
            "sd_spread": sd_sp, "ac1_spread": acf(d["spread"].to_numpy(), 1),
            "corr_spread_ret": float(np.corrcoef(d["spread"], d["ret"])[0, 1]),
            "window_refs_40w": None}
    # window references
    def windows(series_a, series_b, w):
        n = len(series_a) // w
        out = []
        for i in range(n):
            a = series_a[i * w:(i + 1) * w]; b = series_b[i * w:(i + 1) * w]
            out.append((acf(a, 1), float(np.corrcoef(a, b)[0, 1])))
        return np.asarray(out)
    W = windows(al["raw"].to_numpy(), al["mkt"].to_numpy(), 200)
    rng = np.random.default_rng(550002)
    # LIKE-FOR-LIKE parameters (P4-1's lesson, one estimator on both sides): the generator produces 200-day paths,
    # so design A's parameters are the medians of the AR-form fit over the same non-overlapping 200-trading-day
    # windows the rule-(i) references use -- a window fit demeans the slow component the full-sample fit keeps.
    def window_fits(d, w, cols):
        n = len(d) // w; rows = []
        for i in range(n):
            g = d.iloc[i * w:(i + 1) * w].dropna(subset=cols)
            if len(g) < w // 2:
                continue
            X = np.column_stack([np.ones(len(g))] + [g[c].to_numpy(float) for c in cols[1:]])
            y = g[cols[0]].to_numpy(float)
            b = np.linalg.lstsq(X, y, rcond=None)[0]
            e = y - X @ b
            sd = float(y.std(ddof=1))
            rows.append({"rho": float(b[1]), "b0_per_sd": float(b[2] / sd), "b1_per_sd": float(b[3] / sd),
                         "sd_e_per_sd": float(e.std(ddof=len(cols)) / sd), "sd": sd})
        r = pd.DataFrame(rows)
        out = {k: {"median": float(r[k].median()), "ci95": [float(v) for v in np.percentile(
            np.median(r[k].to_numpy()[rng.integers(0, len(r), (N_BOOT, len(r)))], axis=1), [2.5, 97.5])],
                   "p10": float(r[k].quantile(0.10)), "p90": float(r[k].quantile(0.90))} for k in r.columns}
        out["n_windows"] = int(len(r))
        return out
    loads["window_200d"] = window_fits(al, 200, ["raw", "raw_l1", "z", "z_l1"])
    def med_ci(v):
        m = np.median(v[rng.integers(0, len(v), (N_BOOT, len(v)))], axis=1)
        return {"median": float(np.median(v)), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))],
                "p10": float(np.percentile(v, 10)), "p90": float(np.percentile(v, 90)), "n_windows": int(len(v))}
    refs = {"acf1_200d": med_ci(W[:, 0]), "corr_s_r_200d": med_ci(W[:, 1]),
            "note": "non-overlapping 200-trading-day windows of the deconvolved, trading-day-aligned SF Fed series vs the FF market return"}
    Wa = windows(d["spread"].to_numpy(), d["ret"].to_numpy(), 40)
    aaii["window_refs_40w"] = {"acf1_40w": med_ci(Wa[:, 0]), "corr_40w": med_ci(Wa[:, 1])}
    aaii["window_fits_40w"] = window_fits(d, 40, ["spread", "spread_l1", "z", "z_l1"])

    res = {"what": "E5.5: sentiment fits (PREREG section 8.1)", "deconvolution": decon, "loadings_market_daily": loads,
           "reverse_regression": reverse, "valuation_link_monthly": valuation, "aaii_weekly": aaii,
           "window_references_rule_i": refs, "units": "loadings per sd of the sentiment series and per sd of the standardised market return",
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "sentiment.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    L0 = loads["full"]
    L = ["# E5.5 sentiment fits (PREREG_PHASE_5.md section 8.1)", "",
         f"SF Fed daily index, {decon['n_days']} calendar days; published AC(1) {decon['published']['ac1']:.4f} (AC(21) "
         f"{decon['published']['ac21']:.3f}, AC(252) {decon['published']['ac252']:.3f}). Deconvolved with lam = {LAM} "
         f"({decon['lam_source']}; {gaps} calendar gaps treated as consecutive): raw sd {decon['raw']['sd']:.3f}, AC(1) "
         f"{decon['raw']['ac1']:.4f} {decon['raw']['ac1_ci']}, AC(2) {decon['raw']['ac2']:.4f}, AC(5) {decon['raw']['ac5']:.4f}, "
         f"AC(21) {decon['raw']['ac21']:.4f}; **AR(1)+noise persistence rho = {decon['raw']['rho_ar1_plus_noise']:.4f} "
         f"{decon['raw']['rho_ci']}**, measurement-noise variance share {decon['raw']['noise_variance_share']:.3f} "
         f"{decon['raw']['noise_share_ci']}.", "",
         f"Loadings on the standardised FF market return, AR form (n = {L0['n']} trading days): rho {L0['rho']:.4f} (se {L0['rho_se']:.4f}); "
         f"b0 {L0['b0_per_sd_raw']:+.4f} (se {L0['b0_se'] / L0['sd_raw']:.4f}) and b1 {L0['b1_per_sd_raw']:+.4f} per sd of raw; residual sd "
         f"{L0['sd_resid_per_sd_raw']:.4f} sd; R2 {L0['r2']:.3f}; corr(raw, mkt) {loads['corr_raw_mkt_full']:+.4f}.", "",
         "| sub-period | n | rho | b0 / sd | b1 / sd | resid sd / sd |", "|---|---|---|---|---|---|"]
    for k, v in loads["sub_periods"].items():
        L.append(f"| {k} | {v['n']} | {v['rho']:.4f} | {v['b0_per_sd_raw']:+.4f} | {v['b1_per_sd_raw']:+.4f} | {v['sd_resid_per_sd_raw']:.4f} |")
    W2 = loads["window_200d"]
    L += ["", f"**200-trading-day WINDOW fits (like-for-like with the benchmark path; design A's parameters), n = "
              f"{W2['n_windows']} windows:** rho {W2['rho']['median']:.4f} {W2['rho']['ci95']} (P10-P90 {W2['rho']['p10']:.3f}-"
              f"{W2['rho']['p90']:.3f}); b0 {W2['b0_per_sd']['median']:+.4f} {W2['b0_per_sd']['ci95']}; b1 "
              f"{W2['b1_per_sd']['median']:+.4f} {W2['b1_per_sd']['ci95']}; residual sd {W2['sd_e_per_sd']['median']:.4f} per sd of raw."]
    Wa2 = aaii["window_fits_40w"]
    L += [f"AAII 40-week window fits (design C's parameters), n = {Wa2['n_windows']}: rho_w {Wa2['rho']['median']:.4f} "
          f"{Wa2['rho']['ci95']}; b0 {Wa2['b0_per_sd']['median']:+.4f}; b1 {Wa2['b1_per_sd']['median']:+.4f}; residual sd "
          f"{Wa2['sd_e_per_sd']['median']:.4f} per sd."]
    L += ["", f"Reverse (Tetlock's direction): next-day market return {reverse['gamma_next_day_bp_per_sd']:+.2f} bp per sd of raw sentiment "
              f"(se {reverse['se_bp']:.2f}, n = {reverse['n']}); days 2-5 cumulative {reverse['days2_5_cumulative_bp_per_sd']:+.2f} bp "
              f"(se {reverse['se2_5_bp']:.2f}). Tetlock 2007 (read): +8.1 bp next day, 6.8 bp reversed over days 2-5 (DJIA). "
              f"b_pred stays LIT 0.0008 / 0.0006.", "",
          f"Valuation link (design B; monthly, raw on log-CAPE deviation from the trailing 120-month mean, n = "
          f"{valuation['trailing_120m_mean']['n_months']} months): coefficient {valuation['trailing_120m_mean']['coef_raw_per_unit_logdev']:+.4f} "
          f"(se {valuation['trailing_120m_mean']['se']:.4f}) raw units per unit log-deviation = "
          f"{valuation['trailing_120m_mean']['coef_per_sd_raw_daily']:+.4f} sd per unit "
          f"{valuation['trailing_120m_mean']['ci95_per_sd_raw_daily']}; full-sample-mean deviation: "
          f"{valuation['full_sample_mean_from_1980']['coef_per_sd_raw_daily']:+.4f} sd per unit. {valuation['transfer']}.", "",
          f"AAII weekly (design C; n = {aaii['n_weeks']} weeks): rho_w {aaii['rho_w']:.4f} (se {aaii['rho_w_se']:.4f}); loading on the "
          f"standardised weekly return b0 {aaii['b0_per_sd']:+.4f} per sd (se {aaii['b0_se_per_sd']:.4f}), b1 {aaii['b1_per_sd']:+.4f}; "
          f"residual sd {aaii['sd_resid_per_sd']:.4f} sd; corr(spread, weekly return) {aaii['corr_spread_ret']:+.3f}.", "",
          f"Rule (i) references (200-trading-day windows, n = {refs['acf1_200d']['n_windows']}): ACF(1) median "
          f"{refs['acf1_200d']['median']:.4f} {refs['acf1_200d']['ci95']} (P10-P90 {refs['acf1_200d']['p10']:.3f}-{refs['acf1_200d']['p90']:.3f}); "
          f"corr(s, r) median {refs['corr_s_r_200d']['median']:+.4f} {refs['corr_s_r_200d']['ci95']}. AAII 40-week windows: ACF(1) "
          f"{aaii['window_refs_40w']['acf1_40w']['median']:.3f} {aaii['window_refs_40w']['acf1_40w']['ci95']}, corr "
          f"{aaii['window_refs_40w']['corr_40w']['median']:+.3f} {aaii['window_refs_40w']['corr_40w']['ci95']}.", ""]
    with open(os.path.join(OUT, "sentiment.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L)); print(f"wrote {OUT}/sentiment.json in {res['seconds']} s")


if __name__ == "__main__":
    main()
