"""
E5.2 -- EPS: the seasonal-random-walk residual, the loss process, the n/m frequency and the announcement lags
(PREREG_PHASE_5.md section 5.1).

    python -m tools.phase5.e5_2_eps

Data: EDGAR quarterly basic EPS for set A (Phase 1's `quarterly_eps`: dedup on (concept, start, end) keeping the
earliest filing, 80-100-day periods, Q4 derived from FY where needed); the 8-K Item 2.02 dates fetched by
tools/phase5/fetch_8k.py; the 10-Q/10-K filing dates already in the panel.

Fits (each with a 1,000-resample STOCK bootstrap):
  seasonal residual     eps_q = (E_q - E_{q-4}) / L_q with L_q = mean |E| over the four preceding quarters
                        (DESIGN level, defined for negative quarters): sd, robust sd (1.4826 MAD), P10/50/90, kurtosis
  log seasonal change   log(E_q / E_{q-4}) for positive pairs: sd, robust sd; the generator's multiplicative noise
                        NET of V: s_EPS = sqrt(max((s_log^2 - 252 sigma_V^2) / 2, 0))
  loss chain            P(E_q < 0), P(E_q < 0 | E_{q-1} < 0), P(E_q < 0 | E_{q-1} >= 0); loss size -E_q / L_q grid
  n/m frequency         share of stock-quarters with EPS_ttm <= 0 (four consecutive quarters)
  announcement lag      first 8-K 2.02 filing after each period end within 120 calendar days; calendar days and
                        trading-day equivalent (x 252/365, DESIGN conversion, stated); 33-point grid; P10/50/90
  filing lag (beside)   10-Q/10-K `filed` - period end; the SEC 10-Q deadlines 40/45 d as the LIT sanity bound

Output: docs/env_v2/generated/v2_1/e5_2/eps.{json,md}, quarters.csv, lags.csv
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase1.panel import DEFAULT, analysis_sets, quarterly_eps  # noqa: E402
from tools.phase5.common import GEN  # noqa: E402

OUT = os.path.join(GEN, "e5_2")
ANN_DIR = os.path.join(DEFAULT.root, "03_fundamentals", "announcements")
N_BOOT = 1000
GRID_Q = np.linspace(0.0, 1.0, 33)
CAL_TO_TRADING = 252.0 / 365.0
LEVEL_FLOOR = 1e-3
LEVEL_FLOOR_REL = 0.10        # ADDENDUM 4.2(1): the level must be >= 10 % of the stock's median |EPS|
GRID_TRUNC = (0.05, 0.95)     # ADDENDUM 4.2(2): grids over P5-P95, the truncation recorded


def robust_sd(v):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    return float(1.4826 * np.median(np.abs(v - np.median(v)))) if len(v) else float("nan")


def boot_stat(by_stock, fn, n_boot=N_BOOT, seed=520001):
    """fn(list of per-stock arrays) -> statistic; stock-cluster bootstrap."""
    keys = list(by_stock)
    rng = np.random.default_rng(seed)
    point = fn([by_stock[k] for k in keys])
    draws = []
    for _ in range(n_boot):
        pick = rng.choice(keys, len(keys), replace=True)
        draws.append(fn([by_stock[k] for k in pick]))
    draws = np.asarray(draws, float)
    return {"value": float(point), "ci95": [float(np.nanpercentile(draws, 2.5)), float(np.nanpercentile(draws, 97.5))]}


def quarters_table(A):
    rows = []
    for t in A:
        q = quarterly_eps(t, "EarningsPerShareBasic", DEFAULT)
        if q is None or len(q) < 8:
            continue
        q = q.sort_values("end").reset_index(drop=True)
        e = q["eps"].to_numpy(float); ends = q["end"].to_numpy(); filed = q["filed"].to_numpy()
        for i in range(len(q)):
            row = {"ticker": t, "end": ends[i], "eps": e[i], "filed": filed[i], "derived_q4": bool(q["derived_q4"].iloc[i]),
                   "eps_prev": np.nan, "consecutive_prev": False, "eps_lag4": np.nan, "seasonal_pair": False,
                   "level": np.nan, "eps_ttm": np.nan}
            if i >= 1:
                gap = (pd.Timestamp(ends[i]) - pd.Timestamp(ends[i - 1])).days
                if 75 <= gap <= 105:
                    row["eps_prev"] = e[i - 1]; row["consecutive_prev"] = True
            if i >= 4:
                gap4 = (pd.Timestamp(ends[i]) - pd.Timestamp(ends[i - 4])).days
                if 340 <= gap4 <= 390:
                    row["eps_lag4"] = e[i - 4]; row["seasonal_pair"] = True
                    row["level"] = float(np.mean(np.abs(e[i - 4:i])))
                    row["eps_ttm"] = float(np.sum(e[i - 3:i + 1]))
            rows.append(row)
    return pd.DataFrame(rows)


def lags_table(A, qt: pd.DataFrame):
    rows = []
    n_with_8k = 0
    for t in A:
        p = os.path.join(ANN_DIR, f"{t}.parquet")
        q = qt[qt["ticker"] == t]
        if q.empty:
            continue
        ends = pd.to_datetime(q["end"]).to_numpy()
        filed = pd.to_datetime(q["filed"]).to_numpy()
        ann = None
        if os.path.exists(p):
            a = pd.read_parquet(p)
            if len(a):
                ann = np.sort(pd.to_datetime(a["filed"]).dropna().unique())
                n_with_8k += 1
        for i in range(len(ends)):
            e = pd.Timestamp(ends[i])
            row = {"ticker": t, "end": e, "filing_lag_cal": (pd.Timestamp(filed[i]) - e).days, "ann_lag_cal": np.nan}
            if ann is not None:
                j = np.searchsorted(ann, np.datetime64(e), side="right")
                if j < len(ann):
                    lag = (pd.Timestamp(ann[j]) - e).days
                    if 0 < lag <= 120:
                        row["ann_lag_cal"] = lag
            rows.append(row)
    return pd.DataFrame(rows), n_with_8k


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    A = analysis_sets(write=False)["A"]
    qt = quarters_table(A)
    qt.to_csv(os.path.join(OUT, "quarters.csv"), index=False)
    vp = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "value.json"), encoding="utf-8"))
    sigma_V = float(vp["sigma_V"]["value"])

    med_abs = qt.groupby("ticker")["eps"].apply(lambda v: float(np.median(np.abs(v))))
    qt["level_floor_stock"] = qt["ticker"].map(med_abs) * LEVEL_FLOOR_REL
    sp_raw = qt[qt["seasonal_pair"] & (qt["level"] > LEVEL_FLOOR)].copy()
    sp_raw["eps_rel"] = (sp_raw["eps"] - sp_raw["eps_lag4"]) / sp_raw["level"]
    sp = sp_raw[sp_raw["level"] >= sp_raw["level_floor_stock"]].copy()
    n_dropped_by_floor = int(len(sp_raw) - len(sp))
    pos = sp[(sp["eps"] > 0) & (sp["eps_lag4"] > 0)].copy()
    pos["dlog"] = np.log(pos["eps"] / pos["eps_lag4"])
    by_rel = {t: g["eps_rel"].to_numpy(float) for t, g in sp.groupby("ticker")}
    by_log = {t: g["dlog"].to_numpy(float) for t, g in pos.groupby("ticker")}
    cat = lambda L: np.concatenate(L)
    seasonal = {"n_pairs": int(len(sp)), "n_stocks": int(sp["ticker"].nunique()),
                "level_floor": f"L_q >= {LEVEL_FLOOR_REL} x the stock's median |EPS| (ADDENDUM 4.2(1)); {n_dropped_by_floor} pairs dropped",
                "without_floor": {"n_pairs": int(len(sp_raw)), "sd": float(sp_raw["eps_rel"].std(ddof=1)),
                                  "robust_sd": robust_sd(sp_raw["eps_rel"]), "excess_kurtosis": float(pd.Series(sp_raw["eps_rel"]).kurt())},
                "sd": boot_stat(by_rel, lambda L: np.std(cat(L), ddof=1)),
                "robust_sd": boot_stat(by_rel, lambda L: robust_sd(cat(L))),
                "p10": float(np.percentile(sp["eps_rel"], 10)), "p50": float(np.percentile(sp["eps_rel"], 50)),
                "p90": float(np.percentile(sp["eps_rel"], 90)),
                "excess_kurtosis": float(pd.Series(sp["eps_rel"]).kurt())}
    s_log_sd = boot_stat(by_log, lambda L: np.std(cat(L), ddof=1))
    s_log_rob = boot_stat(by_log, lambda L: robust_sd(cat(L)))
    var_V_annual = 252.0 * sigma_V ** 2

    def net(s):
        return float(np.sqrt(max((s ** 2 - var_V_annual) / 2.0, 0.0)))
    log_change = {"n_pairs": int(len(pos)), "n_stocks": int(pos["ticker"].nunique()), "sd": s_log_sd, "robust_sd": s_log_rob,
                  "sigma_V_daily": sigma_V, "sd_annual_V": float(np.sqrt(var_V_annual)),
                  "s_EPS_from_robust_sd": {"value": net(s_log_rob["value"]),
                                           "ci95": [net(s_log_rob["ci95"][0]), net(s_log_rob["ci95"][1])]},
                  "s_EPS_from_sd": {"value": net(s_log_sd["value"]), "ci95": [net(s_log_sd["ci95"][0]), net(s_log_sd["ci95"][1])]},
                  "v2_incumbent_noise_sd": 0.10}

    cp = qt[qt["consecutive_prev"]].copy()
    by_loss = {t: g[["eps", "eps_prev"]].to_numpy(float) for t, g in cp.groupby("ticker")}
    def p_loss(L):
        v = np.vstack(L); return float(np.mean(v[:, 0] < 0))
    def p_ll(L):
        v = np.vstack(L); m = v[:, 1] < 0; return float(np.mean(v[m, 0] < 0)) if m.sum() else np.nan
    def p_lp(L):
        v = np.vstack(L); m = v[:, 1] >= 0; return float(np.mean(v[m, 0] < 0)) if m.sum() else np.nan
    loss = {"n_quarters": int(len(cp)), "n_stocks": int(cp["ticker"].nunique()),
            "p_loss": boot_stat(by_loss, p_loss), "p_loss_given_loss": boot_stat(by_loss, p_ll),
            "p_loss_given_profit": boot_stat(by_loss, p_lp)}
    ls = sp[sp["eps"] < 0].copy(); ls["size"] = -ls["eps"] / ls["level"]
    lo_s, hi_s = (np.quantile(ls["size"], GRID_TRUNC[0]), np.quantile(ls["size"], GRID_TRUNC[1])) if len(ls) else (None, None)
    ls_t = ls[(ls["size"] >= lo_s) & (ls["size"] <= hi_s)] if len(ls) else ls
    loss["size"] = {"n": int(len(ls)), "p10": float(np.percentile(ls["size"], 10)) if len(ls) else None,
                    "p50": float(np.percentile(ls["size"], 50)) if len(ls) else None,
                    "p90": float(np.percentile(ls["size"], 90)) if len(ls) else None,
                    "grid": [float(x) for x in np.quantile(ls_t["size"], GRID_Q)] if len(ls) else None,
                    "grid_truncation_p5_p95": [float(lo_s), float(hi_s)] if len(ls) else None,
                    "note": "size relative to the mean |EPS| of the four preceding quarters (level floor applied); the grid spans P5-P95 (ADDENDUM 4.2(2))"}
    tt = qt[np.isfinite(qt["eps_ttm"])]
    by_nm = {t: g["eps_ttm"].to_numpy(float) for t, g in tt.groupby("ticker")}
    nm = {"n_stock_quarters": int(len(tt)), "n_stocks": int(tt["ticker"].nunique()),
          "share_ttm_nonpositive": boot_stat(by_nm, lambda L: float(np.mean(cat(L) <= 0)))}
    # by year, for the record
    nm["by_year"] = {int(y): {"n": int(len(g)), "share": float(np.mean(g["eps_ttm"] <= 0))}
                     for y, g in tt.groupby(pd.to_datetime(tt["end"]).dt.year)}

    lg, n_8k = lags_table(A, qt)
    lg.to_csv(os.path.join(OUT, "lags.csv"), index=False)
    al = lg[np.isfinite(lg["ann_lag_cal"])].copy()
    al["ann_lag_td"] = np.round(al["ann_lag_cal"] * CAL_TO_TRADING)
    fl = lg[np.isfinite(lg["filing_lag_cal"]) & (lg["filing_lag_cal"] > 0) & (lg["filing_lag_cal"] <= 150)].copy()
    fl["filing_lag_td"] = np.round(fl["filing_lag_cal"] * CAL_TO_TRADING)
    by_al = {t: g["ann_lag_td"].to_numpy(float) for t, g in al.groupby("ticker")}
    def qfn(q):
        return lambda L: float(np.percentile(cat(L), q))
    lags = {"announcement_8k": {"n_filings": int(len(al)), "n_stocks": int(al["ticker"].nunique()), "n_stocks_with_8k_file": n_8k,
                                "coverage_of_set_A": n_8k / len(A),
                                "p10_td": boot_stat(by_al, qfn(10)), "p50_td": boot_stat(by_al, qfn(50)), "p90_td": boot_stat(by_al, qfn(90)),
                                "p10_cal": float(np.percentile(al["ann_lag_cal"], 10)), "p50_cal": float(np.percentile(al["ann_lag_cal"], 50)),
                                "p90_cal": float(np.percentile(al["ann_lag_cal"], 90)),
                                "grid_td": [float(x) for x in np.quantile(
                                    al.loc[al["ann_lag_td"].between(np.quantile(al["ann_lag_td"], GRID_TRUNC[0]),
                                                                    np.quantile(al["ann_lag_td"], GRID_TRUNC[1])), "ann_lag_td"], GRID_Q)],
                                "grid_truncation_p5_p95_td": [float(np.quantile(al["ann_lag_td"], GRID_TRUNC[0])),
                                                             float(np.quantile(al["ann_lag_td"], GRID_TRUNC[1]))],
                                "conversion": "trading days = calendar days x 252/365, rounded (DESIGN); the grid spans P5-P95 (ADDENDUM 4.2(2))"},
            "filing_10q_10k": {"n": int(len(fl)), "n_stocks": int(fl["ticker"].nunique()),
                               "p10_cal": float(np.percentile(fl["filing_lag_cal"], 10)), "p50_cal": float(np.percentile(fl["filing_lag_cal"], 50)),
                               "p90_cal": float(np.percentile(fl["filing_lag_cal"], 90)),
                               "p50_td": float(np.percentile(fl["filing_lag_td"], 50)),
                               "sec_deadlines_10q_cal": [40, 45], "sec_deadline_source": "SEC Form 10-Q general instructions (LIT; large accelerated 40 d, accelerated 40 d, others 45 d)"},
            "v2_incumbent": {"lag_trading_days": [25, 35], "label": "DESIGN, weakness item 22"},
            "announcement_minus_filing_cal_median": (float((lg.loc[np.isfinite(lg["ann_lag_cal"]) & np.isfinite(lg["filing_lag_cal"]), "filing_lag_cal"]
                                                            - lg.loc[np.isfinite(lg["ann_lag_cal"]) & np.isfinite(lg["filing_lag_cal"]), "ann_lag_cal"]).median())
                                                     if len(al) else None)}

    res = {"what": "E5.2: EPS seasonal residual, loss process, n/m frequency and announcement lags (PREREG section 5.1)",
           "data": {"set": "A", "n_stocks_with_quarters": int(qt["ticker"].nunique()), "n_quarters": int(len(qt)),
                    "window": "EDGAR XBRL coverage, 2009+ (period ends to 2026)",
                    "survivor_caveat": "set A is survivor-only (REG-15): loss frequencies and the residual's tails are "
                                       "understated relative to the full universe; the announcement lag is not obviously biased"},
           "seasonal_residual_relative_to_level": seasonal, "log_seasonal_change": log_change, "loss_process": loss,
           "nm_frequency": nm, "announcement_lags": lags, "grid_quantiles": [float(q) for q in GRID_Q],
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "eps.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)

    def f(d, k="value", dd=4):
        return f"{d[k]:.{dd}f} [{d['ci95'][0]:.{dd}f}, {d['ci95'][1]:.{dd}f}]"
    L = ["# E5.2 EPS: seasonal residual, losses, n/m frequency, announcement lags (PREREG_PHASE_5.md section 5.1)", "",
         f"Set A, {res['data']['n_stocks_with_quarters']} stocks, {res['data']['n_quarters']} quarters. Stock-bootstrap CIs "
         f"({N_BOOT}). {res['data']['survivor_caveat']}.", "",
         f"- seasonal residual (E_q - E_q-4)/L_q with the level floor ({seasonal['level_floor']}; without it: sd {seasonal['without_floor']['sd']:.1f}, "
         f"robust sd {seasonal['without_floor']['robust_sd']:.4f}, kurtosis {seasonal['without_floor']['excess_kurtosis']:.0f}), n = {seasonal['n_pairs']} pairs / {seasonal['n_stocks']} stocks: sd "
         f"{f(seasonal['sd'])}, robust sd {f(seasonal['robust_sd'])}, P10/P50/P90 {seasonal['p10']:.3f} / {seasonal['p50']:.3f} / "
         f"{seasonal['p90']:.3f}, excess kurtosis {seasonal['excess_kurtosis']:.1f}",
         f"- log seasonal change (positive pairs, n = {log_change['n_pairs']}): sd {f(s_log_sd)}, robust sd {f(s_log_rob)}; "
         f"V's annual sd in force {log_change['sd_annual_V']:.4f}; **s_EPS (net of V, from the robust sd) = "
         f"{f(log_change['s_EPS_from_robust_sd'])}** (from the plain sd {f(log_change['s_EPS_from_sd'])}); v2 used 0.10",
         f"- loss quarters (n = {loss['n_quarters']}): P(loss) {f(loss['p_loss'])}; P(loss | loss) {f(loss['p_loss_given_loss'])}; "
         f"P(loss | profit) {f(loss['p_loss_given_profit'])}; loss size P10/P50/P90 {loss['size']['p10']} / {loss['size']['p50']} / "
         f"{loss['size']['p90']} (n = {loss['size']['n']})",
         f"- n/m frequency, EPS_ttm <= 0 over four consecutive quarters (n = {nm['n_stock_quarters']} stock-quarters / "
         f"{nm['n_stocks']} stocks): **{f(nm['share_ttm_nonpositive'])}**",
         f"- announcement lag (8-K 2.02, {lags['announcement_8k']['n_filings']} filings / {lags['announcement_8k']['n_stocks']} stocks; "
         f"{n_8k} of {len(A)} names have an 8-K file): P10/P50/P90 = {lags['announcement_8k']['p10_cal']:.0f} / "
         f"{lags['announcement_8k']['p50_cal']:.0f} / {lags['announcement_8k']['p90_cal']:.0f} calendar days = "
         f"{f(lags['announcement_8k']['p10_td'], dd=1)} / {f(lags['announcement_8k']['p50_td'], dd=1)} / "
         f"{f(lags['announcement_8k']['p90_td'], dd=1)} trading days; v2 drew U(25, 35)",
         f"- filing lag (10-Q/10-K, n = {lags['filing_10q_10k']['n']}): P10/P50/P90 = {lags['filing_10q_10k']['p10_cal']:.0f} / "
         f"{lags['filing_10q_10k']['p50_cal']:.0f} / {lags['filing_10q_10k']['p90_cal']:.0f} calendar days (SEC 10-Q deadline 40/45); "
         f"the release precedes the filing by a median of {lags['announcement_minus_filing_cal_median']} calendar days", ""]
    with open(os.path.join(OUT, "eps.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"wrote {OUT}/eps.json in {res['seconds']} s")


if __name__ == "__main__":
    main()
