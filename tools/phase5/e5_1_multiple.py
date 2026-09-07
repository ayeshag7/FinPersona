"""
E5.1 -- the trailing P/E cross-section and the quarterly persistence of log P/E (PREREG_PHASE_5.md section 4.1).

    python -m tools.phase5.e5_1_multiple

Data: Phase 1's monthly trailing P/E panel (`tools.phase1.e1_2_pv.monthly_pe_panel`, REUSED UNCHANGED: EDGAR basic
EPS deduplicated on (concept, start, end) keeping the earliest filing, Q4 derived from FY where needed, trailing-4Q
as known at each month-end from filings, consecutive quarters within 400 days; set A; 2009-06 .. 2024-12).

Fits:
  cross-section     pooled stock-months with EPS_ttm > 0: P5/P10/P25/P50/P75/P90/P95 pooled and by year, with a
                    1,000-resample STOCK bootstrap on each pooled quantile; the n/m share (EPS_ttm <= 0)
  persistence       per stock, log P/E at quarter-end months (Mar/Jun/Sep/Dec), OLS AR(1) with intercept
                    (>= 20 quarters): median rho_q with a stock bootstrap; converted to a daily rho_d = rho_q^(1/63)
  decomposition     var(log P/E pooled) = between-stock (variance of stock means) + within-stock (stock-demeaned)
  design grids      the 33-point empirical quantile grids the generator samples by inverse CDF (design A: the pooled
                    P/E truncated to each width; design B: the between-stock stock-mean log P/E truncated to the
                    same quantile band) and design B's within-stock sd NET of the engine's sd(x) and of E5.2's EPS
                    noise (the net-of-x correction is applied by apply_e5.py once E5.2's s_EPS exists; here the gross
                    within-stock sd and the engine's sd(x) are recorded)
  cross-check       Damodaran pedata.xls industry current P/E (Jan 2026), median and IQR across industries -- reported only

Output: docs/env_v2/generated/v2_1/e5_1/multiple.{json,md}, pe_panel_monthly.csv (stock x month trailing P/E)
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

from tools.phase1.panel import DEFAULT, analysis_sets, load_prices  # noqa: E402
from tools.phase1.e1_2_pv import monthly_pe_panel  # noqa: E402
from tools.phase5.common import GEN  # noqa: E402

OUT = os.path.join(GEN, "e5_1")
QS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
WIDTHS = {"P10-P90": (0.10, 0.90), "P25-P75": (0.25, 0.75), "P5-P95": (0.05, 0.95)}
N_BOOT = 1000
GRID_Q = np.linspace(0.0, 1.0, 33)
MIN_QUARTERS = 20


def stock_boot_quantiles(pe_long: pd.DataFrame, qs, n_boot=N_BOOT, seed=510001):
    """Pooled quantiles with a stock-cluster bootstrap (resample stocks with replacement, pool their months)."""
    stocks = pe_long["ticker"].unique()
    by = {t: g["pe"].to_numpy(float) for t, g in pe_long.groupby("ticker")}
    rng = np.random.default_rng(seed)
    point = {f"p{int(q * 100)}": float(np.quantile(pe_long["pe"], q)) for q in qs}
    draws = {k: [] for k in point}
    for _ in range(n_boot):
        pick = rng.choice(stocks, len(stocks), replace=True)
        v = np.concatenate([by[t] for t in pick])
        for q in qs:
            draws[f"p{int(q * 100)}"].append(float(np.quantile(v, q)))
    return {k: {"value": point[k], "ci95": [float(np.percentile(draws[k], 2.5)), float(np.percentile(draws[k], 97.5))]}
            for k in point}


def ar1_by_stock(lpe_q: pd.DataFrame):
    rows = []
    for t in lpe_q.columns:
        y = lpe_q[t].dropna()
        if len(y) < MIN_QUARTERS:
            continue
        # longest run of consecutive quarters
        idx = y.index.to_period("Q").astype(int)
        gaps = np.where(np.diff(idx) != 1)[0]
        start, best = 0, (0, 0)
        for g in list(gaps) + [len(idx) - 1]:
            if g + 1 - start > best[1] - best[0]:
                best = (start, g + 1)
            start = g + 1
        y = y.iloc[best[0]:best[1]].to_numpy(float)
        if len(y) < MIN_QUARTERS:
            continue
        a, b = y[:-1] - y[:-1].mean(), y[1:] - y[1:].mean()
        rho = float((a * b).sum() / (a * a).sum())
        rows.append({"ticker": t, "n_quarters": int(len(y)), "rho_q": rho, "sd_within": float(y.std(ddof=1)),
                     "mean_log_pe": float(y.mean())})
    return pd.DataFrame(rows)


def boot_median(v, n_boot=N_BOOT, seed=510002):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    m = np.median(v[rng.integers(0, len(v), (n_boot, len(v)))], axis=1)
    return {"median": float(np.median(v)), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))],
            "iqr": [float(np.percentile(v, 25)), float(np.percentile(v, 75))], "n": int(len(v))}


def damodaran_pe():
    p = os.path.join(DEFAULT.root, "07_factors_valuation", "pedata.xls")
    try:
        x = pd.read_excel(p, sheet_name="Industry Averages", header=None)
    except Exception as exc:  # pragma: no cover
        return {"error": str(exc)}
    # find the header row (contains 'Industry Name') and the 'Current PE' column
    hdr = None
    for i in range(min(15, len(x))):
        row = [str(v) for v in x.iloc[i].tolist()]
        if any("Industry" in v for v in row):
            hdr = i; break
    if hdr is None:
        return {"error": "header row not found"}
    cols = [str(v).strip() for v in x.iloc[hdr].tolist()]
    body = x.iloc[hdr + 1:].copy(); body.columns = cols
    cand = [c for c in cols if "Current PE" in c or c == "Current PE"]
    if not cand:
        cand = [c for c in cols if "PE" in c]
    c = cand[0]
    v = pd.to_numeric(body[c], errors="coerce").dropna()
    v = v[(v > 0) & (v < 500)]
    return {"column": c, "n_industries": int(len(v)), "median": float(v.median()),
            "iqr": [float(v.quantile(0.25)), float(v.quantile(0.75))], "date_updated": "2026-01-05",
            "note": "industry-level current P/E, Damodaran (Jan 2026 update); cross-check only, no parameter taken"}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    A = analysis_sets(write=False)["A"]
    pe = monthly_pe_panel(A, concept="EarningsPerShareBasic")      # stock x month, NaN where EPS_ttm <= 0 or unknown
    prices = load_prices(A).ffill().resample("ME").last().reindex(pe.index)
    # undefined months: EPS_ttm <= 0 (P/E NaN) among months where the trailing EPS is KNOWN. monthly_pe_panel puts
    # NaN for both 'unknown' and 'non-positive'; recover the split from log E = log P - log PE where defined and
    # from the EPS table where not.  The simpler, exact statistic: recompute the known/positive flags here.
    from tools.phase1.panel import quarterly_eps
    known = pd.DataFrame(False, index=pe.index, columns=pe.columns)
    positive = pd.DataFrame(False, index=pe.index, columns=pe.columns)
    for t in A:
        q = quarterly_eps(t, "EarningsPerShareBasic", DEFAULT)
        if q is None or len(q) < 8 or t not in pe.columns:
            continue
        q = q.sort_values("end").reset_index(drop=True)
        for me in pe.index:
            kn = q[q["filed"] <= me]
            if len(kn) >= 4:
                last4 = kn.iloc[-4:]
                if (last4["end"].iloc[-1] - last4["end"].iloc[0]).days <= 400:
                    known.loc[me, t] = True
                    positive.loc[me, t] = bool(last4["eps"].sum() > 0)
    n_known = int(known.to_numpy().sum()); n_pos = int(positive.to_numpy().sum())
    nm_share = 1.0 - n_pos / n_known
    nm_by_year = {}
    for y, g in known.groupby(known.index.year):
        k = int(g.to_numpy().sum()); p_ = int(positive.loc[g.index].to_numpy().sum())
        nm_by_year[int(y)] = {"n_known": k, "share_nm": (1.0 - p_ / k) if k else None}
    pe.to_csv(os.path.join(OUT, "pe_panel_monthly.csv"))

    long = pe.stack().rename("pe").reset_index()
    long.columns = ["month", "ticker", "pe"]
    long = long[np.isfinite(long["pe"]) & (long["pe"] > 0)]
    pooled = stock_boot_quantiles(long, QS)
    by_year = {}
    for y, g in long.groupby(long["month"].dt.year):
        by_year[int(y)] = {f"p{int(q * 100)}": float(np.quantile(g["pe"], q)) for q in (0.10, 0.25, 0.50, 0.75, 0.90)}
        by_year[int(y)]["n"] = int(len(g)); by_year[int(y)]["n_stocks"] = int(g["ticker"].nunique())

    lpe = np.log(pe)
    qe = lpe[lpe.index.month.isin([3, 6, 9, 12])]
    ar = ar1_by_stock(qe)
    ar.to_csv(os.path.join(OUT, "ar1_by_stock.csv"), index=False)
    rho = boot_median(ar["rho_q"])
    rho_d = {"median": float(np.sign(rho["median"]) * abs(rho["median"]) ** (1 / 63.0)),
             "ci95": [float(max(rho["ci95"][0], 1e-6) ** (1 / 63.0)), float(max(rho["ci95"][1], 1e-6) ** (1 / 63.0))]}
    # dispersion decomposition on the monthly log P/E panel (stock-demeaned within; variance of stock means between)
    stock_means = lpe.mean(axis=0).dropna()
    within = (lpe - lpe.mean(axis=0)).stack().dropna()
    decomp = {"var_pooled": float(lpe.stack().dropna().var(ddof=1)), "var_between": float(stock_means.var(ddof=1)),
              "var_within": float(within.var(ddof=1)), "sd_pooled": float(lpe.stack().dropna().std(ddof=1)),
              "sd_between": float(stock_means.std(ddof=1)), "sd_within": float(within.std(ddof=1)),
              "n_stocks": int(len(stock_means)), "n_stock_months": int(len(within))}
    # the quarter-end version (what design B's AR(1) describes)
    within_q = (qe - qe.mean(axis=0)).stack().dropna()
    decomp["sd_within_quarterly"] = float(within_q.std(ddof=1))
    # the engine's STATIONARY sd(x), from the three parameter files in force (no file records it directly):
    # x_{t+1} = rho x_t + e_t with rho = 2^(-1/h) (mispricing.json), unconditional innovation variance sbar^2
    # (volatility.json's identity-anchored sbar) plus the jump variance lambda sigma_J^2 (value.json / volatility.json)
    mp = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "mispricing.json"), encoding="utf-8"))
    vol = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "volatility.json"), encoding="utf-8"))
    h = float(mp["half_life"]["value"]); rho_x = 2.0 ** (-1.0 / h)
    sbar = float(vol["sbar"]["value"]); jm = vol["jumps"]["value"]
    var_inn = sbar ** 2 + float(jm["jump_rate_x"]) * float(jm["jump_sd"]) ** 2
    sd_x_engine = float(np.sqrt(var_inn / (1.0 - rho_x ** 2)))
    sd_x_note = (f"analytic stationary sd of the AR(1) engine: rho = 2^(-1/{h:.2f}) = {rho_x:.5f}, innovation variance "
                 f"sbar^2 + lambda sigma_J^2 = {sbar:.5f}^2 + {jm['jump_rate_x']:.6f} x {jm['jump_sd']:.4f}^2; E3.8's "
                 f"200-path realised sd(x) for the same stack is 0.0691 (e3_8/decomposition.json)")

    # design grids
    grids = {"A": {}, "B_between": {}}
    for w, (lo, hi) in WIDTHS.items():
        qlo, qhi = np.quantile(long["pe"], lo), np.quantile(long["pe"], hi)
        v = long.loc[(long["pe"] >= qlo) & (long["pe"] <= qhi), "pe"].to_numpy(float)
        grids["A"][w] = {"grid": [float(x) for x in np.quantile(v, GRID_Q)], "n": int(len(v)),
                         "truncation": [float(qlo), float(qhi)]}
        sm = np.exp(stock_means.to_numpy(float))
        blo, bhi = np.quantile(sm, lo), np.quantile(sm, hi)
        vb = sm[(sm >= blo) & (sm <= bhi)]
        grids["B_between"][w] = {"grid_log": [float(x) for x in np.quantile(np.log(vb), GRID_Q)], "n": int(len(vb)),
                                 "truncation": [float(blo), float(bhi)]}

    res = {"what": "E5.1: the trailing P/E cross-section and the quarterly persistence of log P/E (PREREG section 4.1)",
           "data": {"panel": "Phase 1 monthly_pe_panel (EDGAR basic EPS x Yahoo month-end close), set A, 2009-06..2024-12",
                    "n_stocks_with_pe": int(pe.notna().any().sum()), "n_stock_months_positive": int(len(long)),
                    "n_stock_months_known": n_known, "survivor_caveat": "set A is survivor-only (REG-15): loss-makers that "
                    "delisted are absent, so the n/m share and the P/E tails are understated relative to the full universe"},
           "cross_section_pooled": pooled, "cross_section_by_year": by_year,
           "nm_share": {"value": float(nm_share), "n_known": n_known,
                        "se": float(np.sqrt(nm_share * (1 - nm_share) / n_known)), "by_year": nm_by_year,
                        "phase1_reference": 0.195},
           "persistence": {"rho_q_quarterly": rho, "rho_d_daily_equivalent": rho_d, "n_stocks": int(len(ar)),
                           "min_quarters": MIN_QUARTERS, "sd_within_by_stock": boot_median(ar["sd_within"])},
           "dispersion": decomp,
           "engine": {"sd_x_stationary": sd_x_engine, "note": sd_x_note,
                      "source": "envs/v2/params/mispricing.json (half_life), volatility.json (sbar, jumps)"},
           "design_grids": grids, "widths": WIDTHS, "grid_quantiles": [float(q) for q in GRID_Q],
           "pe_cap_p99": pooled["p99"],
           "v2_incumbent": {"k_range": [14.0, 22.0], "label": "DESIGN, weakness item 20"},
           "damodaran_crosscheck": damodaran_pe(),
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "multiple.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    L = ["# E5.1 the trailing P/E cross-section and persistence (PREREG_PHASE_5.md section 4.1)", "",
         f"{res['data']['panel']}; {res['data']['n_stocks_with_pe']} stocks, {res['data']['n_stock_months_positive']} "
         f"stock-months with EPS_ttm > 0 of {n_known} with a known trailing EPS. Pooled quantiles carry a "
         f"{N_BOOT}-resample stock bootstrap. {res['data']['survivor_caveat']}.", "",
         "| quantile | trailing P/E | 95 % CI |", "|---|---|---|"]
    for k, v in pooled.items():
        L.append(f"| {k} | {v['value']:.2f} | [{v['ci95'][0]:.2f}, {v['ci95'][1]:.2f}] |")
    L += ["", f"n/m share (EPS_ttm <= 0 among known): **{nm_share:.4f}** (se {res['nm_share']['se']:.4f}, "
              f"n = {n_known}); Phase 1 reported 0.195 on the same set.", "",
          "| year | P10 | P25 | P50 | P75 | P90 | n | n/m share |", "|---|---|---|---|---|---|---|---|"]
    for y, v in by_year.items():
        nmy = nm_by_year.get(y, {}).get("share_nm")
        L.append(f"| {y} | {v['p10']:.1f} | {v['p25']:.1f} | {v['p50']:.1f} | {v['p75']:.1f} | {v['p90']:.1f} | {v['n']} | "
                 f"{nmy if nmy is None else f'{nmy:.3f}'} |")
    L += ["", f"Quarterly AR(1) of log P/E (per stock, >= {MIN_QUARTERS} quarters, n = {len(ar)}): median rho_q "
              f"**{rho['median']:.4f}** [{rho['ci95'][0]:.4f}, {rho['ci95'][1]:.4f}], IQR {rho['iqr'][0]:.3f}-{rho['iqr'][1]:.3f}; "
              f"daily equivalent rho_d = rho_q^(1/63) = {rho_d['median']:.5f}.", "",
          f"Dispersion of log P/E: pooled sd {decomp['sd_pooled']:.4f}; between-stock sd {decomp['sd_between']:.4f}; "
          f"within-stock sd {decomp['sd_within']:.4f} (quarter-end months {decomp['sd_within_quarterly']:.4f}); the "
          f"engine's stationary sd(x) is {sd_x_engine}.", "",
          f"P/E cap (P99 of the pooled cross-section): {pooled['p99']['value']:.1f}.", "",
          f"Damodaran industry current P/E (Jan 2026, cross-check only): median {res['damodaran_crosscheck'].get('median')}, "
          f"IQR {res['damodaran_crosscheck'].get('iqr')}, n industries {res['damodaran_crosscheck'].get('n_industries')}.", "",
          "Design grids (33-point quantile grids, inverse-CDF sampled): see multiple.json `design_grids`."]
    with open(os.path.join(OUT, "multiple.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L[:12]))
    print(f"wrote {OUT}/multiple.json in {res['seconds']} s")


if __name__ == "__main__":
    main()
