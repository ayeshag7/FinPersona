"""
E5.3 -- dividends: payer share, payout, quarterly stickiness (Lintner at quarterly frequency) and behaviour in crash
episodes (PREREG_PHASE_5.md section 6.1).  Blocked on D10 for the RENDERING only; the process is FIT either way.

    python -m tools.phase5.e5_3_dividends

Data: EDGAR `CommonStockDividendsPerShareDeclared` (fallback `...CashPaid`) quarterly rows (80-100-day periods,
earliest filing per (start, end)), set A; quarterly basic EPS from E5.2's quarters.csv; the fast-crash episodes of
`e4_1/dd30.csv` (duration <= 126 d, the dd30_fast family) for the crash behaviour.

Fits (1,000-resample stock bootstrap where a CI is shown):
  payer share       stocks with any positive quarterly DPS in the window; share of stock-years with zero DPS
  payout            annual DPS / annual EPS per stock-year with EPS > 0 (four consecutive quarters each): median, IQR
  stickiness        dD_q = a + c (tau E_q+ - D_{q-1}) + e, pooled OLS with stock-clustered SEs (E+ = max(E, 0), quarterly
                    EPS); and the share of consecutive quarters with D_q = D_{q-1} (> 0)
  crash behaviour   P(DPS cut >= 20 % within four quarters of the episode peak | paying at the peak) vs the unconditional
                    quarterly cut rate

Output: docs/env_v2/generated/v2_1/e5_3/dividends.{json,md}, dps_quarters.csv
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

from tools.phase1.panel import DEFAULT, analysis_sets, load_edgar  # noqa: E402
from tools.phase5.common import GEN  # noqa: E402

OUT = os.path.join(GEN, "e5_3")
N_BOOT = 1000
CUT = 0.20


def quarterly_dps(ticker):
    f = load_edgar(ticker, DEFAULT)
    if f is None:
        return None
    for concept in ("CommonStockDividendsPerShareDeclared", "CommonStockDividendsPerShareCashPaid"):
        g = f[(f["concept"] == concept) & f["start"].notna() & f["end"].notna() & f["filed"].notna()].copy()
        if g.empty:
            continue
        g = g.sort_values("filed").drop_duplicates(subset=["start", "end"], keep="first")
        g["days"] = (g["end"] - g["start"]).dt.days
        q = g[g["days"].between(80, 100)][["end", "val", "filed"]].rename(columns={"val": "dps"})
        # derive missing Q4 from FY - 3Q when the three quarters exist (dividends are additive)
        fy = g[g["days"].between(350, 380)]
        rows = [q]
        for _, y in fy.iterrows():
            inside = q[(q["end"] > y["start"]) & (q["end"] <= y["end"])]
            if len(inside) == 3 and not (q["end"] == y["end"]).any():
                rows.append(pd.DataFrame({"end": [y["end"]], "dps": [float(y["val"]) - float(inside["dps"].sum())], "filed": [y["filed"]]}))
        out = pd.concat(rows, ignore_index=True).sort_values("end").drop_duplicates(subset=["end"], keep="first").reset_index(drop=True)
        out["dps"] = out["dps"].astype(float).clip(lower=0.0)
        out["concept"] = concept
        if len(out) >= 8:
            return out
    return None


def boot(by_stock, fn, n_boot=N_BOOT, seed=530001):
    keys = list(by_stock); rng = np.random.default_rng(seed)
    point = fn([by_stock[k] for k in keys]); draws = []
    for _ in range(n_boot):
        pick = rng.choice(keys, len(keys), replace=True)
        draws.append(fn([by_stock[k] for k in pick]))
    d = np.asarray(draws, float)
    return {"value": float(point), "ci95": [float(np.nanpercentile(d, 2.5)), float(np.nanpercentile(d, 97.5))]}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    A = analysis_sets(write=False)["A"]
    eq = pd.read_csv(os.path.join(GEN, "e5_2", "quarters.csv"), parse_dates=["end"])
    frames = []; payers = 0; with_dps = 0
    for t in A:
        d = quarterly_dps(t)
        if d is None:
            continue
        with_dps += 1
        if (d["dps"] > 0).any():
            payers += 1
        e = eq[eq["ticker"] == t][["end", "eps"]]
        d = d.merge(e, on="end", how="left")
        d["ticker"] = t
        d["dps_prev"] = d["dps"].shift(1)
        d["gap"] = d["end"].diff().dt.days
        frames.append(d)
    dq = pd.concat(frames, ignore_index=True)
    dq.to_csv(os.path.join(OUT, "dps_quarters.csv"), index=False)
    n_no_file = len(A) - with_dps
    # ADDENDUM 4.2(4): a name reporting neither DPS concept is a non-payer iff Yahoo's dividend column shows no cash
    # dividend in the window; the payer share is then the share of set A that paid
    have = set(dq["ticker"].unique())
    yahoo_paid, yahoo_never = [], []
    for t in [x for x in A if x not in have]:
        pp = os.path.join(DEFAULT.root, "01_prices", "daily", f"{t}.parquet")
        if os.path.exists(pp):
            dd = pd.read_parquet(pp, columns=["Date", "Dividends"])
            dd = dd[(dd["Date"] >= "2009-06-01") & (dd["Date"] <= "2024-12-31")]
            (yahoo_paid if (dd["Dividends"] > 0).any() else yahoo_never).append(t)
    n_payers_A = payers + len(yahoo_paid)
    payer_share = {"n_set_A": len(A), "n_with_dps_concept": with_dps, "n_payers_reporting": payers,
                   "n_no_concept": n_no_file, "no_concept_paid_per_yahoo": yahoo_paid, "no_concept_never_paid_per_yahoo": yahoo_never,
                   "payer_share_among_reporting": payers / with_dps,
                   "payer_share_of_set_A": n_payers_A / len(A), "n_payers_set_A": n_payers_A,
                   "note": "ADDENDUM 4.2(4): the generator's per-seed payer draw uses payer_share_of_set_A"}
    # stock-years: four consecutive quarters (gaps 75-105 d) ending each quarter -> annual sums at year-ends
    dq = dq.sort_values(["ticker", "end"]).reset_index(drop=True)
    ann = []
    for t, g in dq.groupby("ticker"):
        g = g.reset_index(drop=True)
        for i in range(3, len(g)):
            if (g["gap"].iloc[i - 2:i + 1] > 105).any() or (g["gap"].iloc[i - 2:i + 1] < 75).any():
                continue
            if g["end"].iloc[i].month != 12 and g["end"].iloc[i].month != g["end"].iloc[0].month:
                pass
            ann.append({"ticker": t, "end": g["end"].iloc[i], "dps_a": float(g["dps"].iloc[i - 3:i + 1].sum()),
                        "eps_a": float(g["eps"].iloc[i - 3:i + 1].sum()) if g["eps"].iloc[i - 3:i + 1].notna().all() else np.nan})
    an = pd.DataFrame(ann)
    an = an[an["end"].dt.month.isin([12, 3, 6, 9])]           # one year per fiscal-year-end quarter; keep all quarter-ends (rolling years)
    zero_years = float(np.mean(an["dps_a"] <= 0))
    pay = an[(an["eps_a"] > 0) & (an["dps_a"] > 0)].copy(); pay["payout"] = pay["dps_a"] / pay["eps_a"]
    by_pay = {t: g["payout"].to_numpy(float) for t, g in pay.groupby("ticker")}
    payout = {"n_stock_years": int(len(pay)), "n_stocks": int(pay["ticker"].nunique()),
              "median": boot(by_pay, lambda L: float(np.median(np.concatenate(L)))),
              "iqr": [float(pay["payout"].quantile(0.25)), float(pay["payout"].quantile(0.75))],
              "p90": float(pay["payout"].quantile(0.90)), "share_stock_years_zero_dps": zero_years,
              "v2_incumbent": 0.35}
    # Lintner at quarterly frequency, payers only (D_{q-1} > 0 or D_q > 0), consecutive quarters
    lp = dq[(dq["gap"].between(75, 105)) & dq["eps"].notna() & ((dq["dps"] > 0) | (dq["dps_prev"] > 0))].copy()
    lp["eplus"] = lp["eps"].clip(lower=0.0)
    lp["dD"] = lp["dps"] - lp["dps_prev"]
    import statsmodels.api as sm
    X = sm.add_constant(np.column_stack([lp["eplus"].to_numpy(float), lp["dps_prev"].to_numpy(float)]))
    y = lp["dD"].to_numpy(float)
    groups = pd.factorize(lp["ticker"])[0]
    fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    c_unc = -float(fit.params[2]); tau_unc = float(fit.params[1]) / c_unc if c_unc != 0 else np.nan
    c = c_unc; tau = tau_unc
    # a stock-bootstrap on (c, tau)
    by_lp = {t: g[["dD", "eplus", "dps_prev"]].to_numpy(float) for t, g in lp.groupby("ticker")}
    def lint(L):
        v = np.vstack(L); Xb = np.column_stack([np.ones(len(v)), v[:, 1], v[:, 2]])
        b = np.linalg.lstsq(Xb, v[:, 0], rcond=None)[0]; cc = -b[2]
        return np.array([cc, b[1] / cc if cc != 0 else np.nan])
    rng = np.random.default_rng(530002); keys = list(by_lp); draws = []
    for _ in range(N_BOOT):
        pick = rng.choice(keys, len(keys), replace=True); draws.append(lint([by_lp[k] for k in pick]))
    draws = np.asarray(draws)
    unchanged = float(np.mean((lp["dps"] == lp["dps_prev"]) & (lp["dps"] > 0)))
    # ADDENDUM 4.2(3): tau constrained to the FIT median payout; c from the one-parameter regression of dD_q on
    # (tau x Ebar_q - D_{q-1}), Ebar_q the trailing four-quarter mean EPS floored at 0; stock-clustered SE and stock bootstrap
    tau_c = float(pay["payout"].median())
    dq2 = dq.sort_values(["ticker", "end"]).reset_index(drop=True)
    dq2["ebar"] = dq2.groupby("ticker")["eps"].transform(lambda v: v.rolling(4, min_periods=4).mean()).clip(lower=0.0)
    lc = dq2[(dq2["gap"].between(75, 105)) & dq2["ebar"].notna() & ((dq2["dps"] > 0) | (dq2["dps_prev"] > 0))].copy()
    lc["gapv"] = tau_c * lc["ebar"] - lc["dps_prev"]; lc["dD"] = lc["dps"] - lc["dps_prev"]
    Xc = lc["gapv"].to_numpy(float)[:, None]; yc = lc["dD"].to_numpy(float)
    fitc = sm.OLS(yc, Xc).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(lc["ticker"])[0]})
    c_con = float(fitc.params[0]); c_con_se = float(fitc.bse[0])
    by_c = {t: g[["dD", "gapv"]].to_numpy(float) for t, g in lc.groupby("ticker")}
    rngc = np.random.default_rng(530003); keysc = list(by_c); dc = []
    for _ in range(N_BOOT):
        pick = rngc.choice(keysc, len(keysc), replace=True); v = np.vstack([by_c[k] for k in pick])
        dc.append(float((v[:, 1] * v[:, 0]).sum() / (v[:, 1] ** 2).sum()))
    c_con_ci = [float(np.percentile(dc, 2.5)), float(np.percentile(dc, 97.5))]
    cuts = lp[lp["dps_prev"] > 0]
    cut_rate = float(np.mean(cuts["dps"] < (1 - CUT) * cuts["dps_prev"]))
    stick = {"n_quarters": int(len(lp)), "n_stocks": int(lp["ticker"].nunique()),
             "c_speed": {"value": c_con, "ci95": c_con_ci, "se_clustered": c_con_se, "n_quarters": int(len(lc)),
                         "form": "ADDENDUM 4.2(3): tau constrained to the FIT median payout; Ebar = trailing four-quarter mean EPS floored at 0"},
             "tau_target_payout": {"value": tau_c, "ci95": [float(pay["payout"].quantile(0.25)), float(pay["payout"].quantile(0.75))],
                                   "note": "the FIT median annual payout (the interval shown is the IQR of the payout distribution; the median's bootstrap CI is under payout.median)"},
             "unconstrained_two_parameter_fit": {"c": c_unc, "c_ci95": [float(np.nanpercentile(draws[:, 0], 2.5)), float(np.nanpercentile(draws[:, 0], 97.5))],
                                                 "tau": tau_unc, "tau_ci95": [float(np.nanpercentile(draws[:, 1], 2.5)), float(np.nanpercentile(draws[:, 1], 97.5))],
                                                 "verdict": "UNIDENTIFIED (the record of why the constrained form is used)"},
             "share_quarters_dps_unchanged": unchanged, "unconditional_cut_rate_20pct": cut_rate,
             "v2_incumbent": {"speed_per_quarter": 0.3, "payout": 0.35, "label": "DESIGN, weakness item 22 (Lintner's annual speed applied per quarter)"},
             "sanity_range": "aggregate annual speed of adjustment ~0.3 (secondary sources; Lintner 1956 not readable)"}
    # crash behaviour on the fast-crash family
    dd = pd.read_csv(os.path.join(GEN, "e4_1", "dd30.csv"), parse_dates=["peak_date", "trough_date"])
    dd = dd[dd["duration"] <= 126]
    ep = []
    for _, r in dd.iterrows():
        g = dq[dq["ticker"] == r["ticker"]].sort_values("end")
        if g.empty:
            continue
        before = g[g["end"] <= r["peak_date"]]
        after = g[(g["end"] > r["peak_date"]) & (g["end"] <= r["peak_date"] + pd.Timedelta(days=400))]
        if before.empty or len(after) < 2:
            continue
        d0 = float(before["dps"].iloc[-1])
        if d0 <= 0:
            continue
        ep.append({"ticker": r["ticker"], "peak_date": r["peak_date"], "d0": d0, "min_after": float(after["dps"].min()),
                   "cut": bool(after["dps"].min() < (1 - CUT) * d0)})
    ep = pd.DataFrame(ep)
    by_ep = {t: g["cut"].to_numpy(float) for t, g in ep.groupby("ticker")} if len(ep) else {}
    crash = {"family": "dd30_fast (duration <= 126 d) with DPS coverage and a positive DPS at the peak",
             "n_episodes": int(len(ep)), "n_stocks": int(ep["ticker"].nunique()) if len(ep) else 0,
             "p_cut_within_4q": boot(by_ep, lambda L: float(np.mean(np.concatenate(L)))) if by_ep else None,
             "unconditional_4q_cut_rate": None}
    # unconditional: P(min over any 4 consecutive quarters < 0.8 x the quarter before) over all payer windows
    unc = []
    for t, g in dq[dq["dps"] > 0].groupby("ticker"):
        v = g["dps"].to_numpy(float)
        for i in range(len(v) - 4):
            unc.append(v[i + 1:i + 5].min() < (1 - CUT) * v[i])
    crash["unconditional_4q_cut_rate"] = float(np.mean(unc)) if unc else None
    crash["n_unconditional_windows"] = len(unc)

    res = {"what": "E5.3: dividends -- payer share, payout, quarterly Lintner stickiness, crash cuts (PREREG section 6.1)",
           "data": {"set": "A", "concepts": ["CommonStockDividendsPerShareDeclared", "CommonStockDividendsPerShareCashPaid (fallback)"],
                    "survivor_caveat": "set A is survivor-only (REG-15): names that cut to zero and delisted are absent, so the "
                                       "cut rates are understated"},
           "payer_share": payer_share, "payout": payout, "stickiness": stick, "crash_behaviour": crash,
           "D10": "undecided: both rendering variants are carried (PREREG section 0); the process above is FIT either way",
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "dividends.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    def f(d, dd=3):
        return f"{d['value']:.{dd}f} [{d['ci95'][0]:.{dd}f}, {d['ci95'][1]:.{dd}f}]"
    L = ["# E5.3 dividends (PREREG_PHASE_5.md section 6.1)", "",
         f"Set A. {res['data']['survivor_caveat']}.", "",
         f"- payers: {payers} of {with_dps} names reporting a DPS concept; of the {n_no_file} names with neither concept, "
         f"{len(yahoo_paid)} paid a cash dividend per Yahoo and {len(yahoo_never)} never did -> **payer share of set A "
         f"{payer_share['payer_share_of_set_A']:.3f}** ({n_payers_A}/{len(A)}); share of payer stock-years with zero DPS {zero_years:.3f}",
         f"- payout (annual DPS / annual EPS, EPS > 0; n = {payout['n_stock_years']} stock-years / {payout['n_stocks']} stocks): "
         f"median {f(payout['median'])}, IQR {payout['iqr'][0]:.3f}-{payout['iqr'][1]:.3f}, P90 {payout['p90']:.3f}; v2 used 0.35",
         f"- Lintner quarterly, tau constrained to the FIT median payout {tau_c:.3f} (n = {stick['c_speed']['n_quarters']} quarters): "
         f"**speed c = {f(stick['c_speed'])} per quarter** (clustered se {stick['c_speed']['se_clustered']:.4f}); the unconstrained "
         f"two-parameter fit is UNIDENTIFIED (c {c_unc:.3f}, tau {tau_unc:.2f} with CI [{stick['unconstrained_two_parameter_fit']['tau_ci95'][0]:.2f}, "
         f"{stick['unconstrained_two_parameter_fit']['tau_ci95'][1]:.1f}]); DPS unchanged quarter-to-quarter in {unchanged:.3f} of payer "
         f"quarters; unconditional quarterly cut (>= 20 %) rate {cut_rate:.4f}; v2 used 0.3 / 0.35",
         f"- crash behaviour ({crash['family']}, n = {crash['n_episodes']} episodes / {crash['n_stocks']} stocks): "
         f"P(cut >= 20 % within four quarters of the peak) = "
         + (f(crash['p_cut_within_4q']) if crash['p_cut_within_4q'] else 'n/a')
         + f" against an unconditional four-quarter cut rate of {crash['unconditional_4q_cut_rate']:.4f} "
           f"(n = {crash['n_unconditional_windows']} windows)", ""]
    with open(os.path.join(OUT, "dividends.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L)); print(f"wrote {OUT}/dividends.json in {res['seconds']} s")


if __name__ == "__main__":
    main()
