"""
E1.2 estimator B (PREREG_PHASE_1.md section 4.2): log(P / V_hat) AR(1) with Andrews' (1993) median-unbiased correction.

V_hat = trailing-4Q EPS (EDGAR, deduplicated on (concept, start, end) keeping the earliest filing; Q4 derived from FY
where needed) x the sector-median trailing P/E of set A that month (market median where no sector / < 5 names), so
log(P/V_hat) = log(P/E_stock) - log(k_med). Monthly, 2009-06 .. 2024-12, stock needs >= 60 valid months (EPS_ttm > 0).
Per stock: OLS AR(1) with intercept -> rho_hat; Andrews' exactly median-unbiased rho from the simulated median
function of the OLS estimator (Gaussian AR(1), 20,000 replications per (T, rho) cell, rho grid 0.50..0.995, T grid),
inverted by interpolation; h = -ln 2 / ln rho_MU months x 21 days. s_x = sd of log(P/V_hat); sigma_V from the
variance of delta log V_hat (monthly / 21 -> daily; OVERSTATED by measurement noise in V_hat, stated).

    python -m tools.phase1.e1_2_pv
Outputs: docs/env_v2/generated/v2_1/e1_2/pv_fit.json, pv_fit.md, pv_by_stock.csv, andrews_median_table.npz
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from tools.phase1.panel import DEFAULT, analysis_sets, load_prices, quarterly_eps, sectors, OUT_DIR  # noqa: E402

OUT = os.path.join(OUT_DIR, "e1_2")
START, END = "2009-06-30", "2024-12-31"
MIN_MONTHS = 60
MIN_SECTOR = 5
RHO_GRID = np.concatenate([np.arange(0.50, 0.95, 0.025), np.arange(0.95, 0.9951, 0.005)])
T_GRID = (60, 80, 100, 120, 140, 160, 180, 200)
N_REP = 20000
N_BOOT = 1000


# --------------------------------------------------------------------------------------------- Andrews' median table
def ols_rho(y: np.ndarray) -> np.ndarray:
    """OLS AR(1) with intercept, vectorised over columns of y (T, n)."""
    a, b = y[:-1], y[1:]
    a = a - a.mean(axis=0); b = b - b.mean(axis=0)
    return (a * b).sum(axis=0) / (a * a).sum(axis=0)


def median_table(seed: int = 12345) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    med = np.empty((len(T_GRID), len(RHO_GRID)))
    for i, T in enumerate(T_GRID):
        for j, rho in enumerate(RHO_GRID):
            e = rng.standard_normal((T, N_REP))
            y = np.empty((T, N_REP)); y[0] = e[0] / np.sqrt(1 - rho ** 2)
            for t in range(1, T):
                y[t] = rho * y[t - 1] + e[t]
            med[i, j] = np.median(ols_rho(y))
    return {"T": np.array(T_GRID), "rho": RHO_GRID, "median": med}


def median_unbiased(rho_hat: float, T: int, tab: Dict[str, np.ndarray]) -> float:
    """Invert m_T(rho) = rho_hat at the nearest T of the table (linear interpolation in rho; clipped to the grid)."""
    i = int(np.argmin(np.abs(tab["T"] - T)))
    m = tab["median"][i]
    if rho_hat <= m[0]:
        return float(tab["rho"][0])
    if rho_hat >= m[-1]:
        return float(tab["rho"][-1])
    return float(np.interp(rho_hat, m, tab["rho"]))


# --------------------------------------------------------------------------------------------- data
def monthly_pe_panel(tickers: List[str], spec=DEFAULT, concept: str = "EarningsPerShareBasic") -> pd.DataFrame:
    prices = load_prices(tickers, spec).ffill()
    month_end = prices.resample("ME").last()
    month_end = month_end[(month_end.index >= START) & (month_end.index <= END)]
    rows = {}
    n_derived = {}
    for t in tickers:
        q = quarterly_eps(t, concept, spec)
        if q is None or len(q) < 8:
            continue
        # trailing 4Q EPS known as of the filing date: for each month-end, the last four quarters filed by then
        q = q.sort_values("end").reset_index(drop=True)
        ttm = []
        for me in month_end.index:
            known = q[q["filed"] <= me]
            if len(known) >= 4:
                last4 = known.iloc[-4:]
                # the four most recent quarters must be consecutive (ends within ~13 months)
                if (last4["end"].iloc[-1] - last4["end"].iloc[0]).days <= 400:
                    ttm.append(float(last4["eps"].sum())); continue
            ttm.append(np.nan)
        ttm = np.array(ttm)
        pe = np.where(ttm > 0, month_end[t].to_numpy() / ttm, np.nan)
        rows[t] = pe
        n_derived[t] = int(q["derived_q4"].sum())
    pe = pd.DataFrame(rows, index=month_end.index)
    pe.attrs["n_derived_q4"] = n_derived
    return pe


def log_pv(pe: pd.DataFrame, sect: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    lpe = np.log(pe)
    market_med = lpe.median(axis=1)
    sec = pd.Series({t: sect.get(t, "") for t in pe.columns})
    sec_med = pd.DataFrame(index=pe.index, columns=pe.columns, dtype=float)
    for s in sec.unique():
        cols = sec.index[sec == s]
        if s == "" or len(cols) < MIN_SECTOR:
            sec_med[cols] = np.nan
        else:
            block = lpe[cols]
            cnt = block.notna().sum(axis=1)
            med = block.median(axis=1).where(cnt >= MIN_SECTOR)
            sec_med[cols] = np.repeat(med.to_numpy()[:, None], len(cols), axis=1)
    sec_med = sec_med.where(sec_med.notna(), np.repeat(market_med.to_numpy()[:, None], pe.shape[1], axis=1))
    return {"sector": lpe - sec_med, "market": lpe.sub(market_med, axis=0)}


def per_stock(u: pd.DataFrame, tab, dV: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for t in u.columns:
        y = u[t].dropna()
        if len(y) < MIN_MONTHS:
            continue
        # use the longest run of consecutive months (gaps break the AR(1))
        idx = y.index
        gaps = np.where(np.diff(idx.to_period("M").astype(int)) != 1)[0]
        start = 0; best = (0, 0)
        for g in list(gaps) + [len(idx) - 1]:
            if g + 1 - start > best[1] - best[0]:
                best = (start, g + 1)
            start = g + 1
        y = y.iloc[best[0]:best[1]]
        if len(y) < MIN_MONTHS:
            continue
        yv = y.to_numpy()
        rho = float(ols_rho(yv[:, None])[0])
        rho_mu = median_unbiased(rho, len(yv), tab)
        h_ols = -np.log(2) / np.log(rho) * 21 if 0 < rho < 1 else np.inf
        h_mu = -np.log(2) / np.log(rho_mu) * 21 if 0 < rho_mu < 1 else np.inf
        d = dV[t].dropna()
        rows.append({"ticker": t, "n_months": int(len(yv)), "rho_ols": rho, "rho_mu": rho_mu, "h_ols_days": h_ols, "h_mu_days": h_mu,
                     "s_x": float(yv.std(ddof=1)), "sigma_V_daily": float(d.std(ddof=1) / np.sqrt(21)) if len(d) > 12 else np.nan})
    return pd.DataFrame(rows)


def _boot_median(v, n_boot=N_BOOT, seed=0):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    meds = np.median(v[rng.integers(0, len(v), (n_boot, len(v)))], axis=1)
    return float(np.median(v)), [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))], [float(np.percentile(v, 25)), float(np.percentile(v, 75))]


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    tab_path = os.path.join(OUT, "andrews_median_table.npz")
    if os.path.exists(tab_path):
        z = np.load(tab_path); tab = {k: z[k] for k in ("T", "rho", "median")}
    else:
        tab = median_table(); np.savez(tab_path, **tab)
    print(f"median table ready ({time.time() - t0:.0f} s)", flush=True)
    sets = analysis_sets(write=False)
    A = sets["A"]
    sect = sectors()
    results = {"spec": DEFAULT.to_dict(), "set": "A", "window": [START, END], "min_months": MIN_MONTHS, "n_boot_over_stocks": N_BOOT,
               "andrews": {"rho_grid": [float(RHO_GRID[0]), float(RHO_GRID[-1])], "T_grid": list(T_GRID), "n_rep": N_REP}, "variants": {}}
    for concept in ("EarningsPerShareBasic", "EarningsPerShareDiluted"):
        pe = monthly_pe_panel(A, concept=concept)
        neg_share = float(1 - pe.notna().sum().sum() / (pe.shape[0] * pe.shape[1]))
        lv = np.log(pe)                       # log V_hat differs from log P/E only by the (common) multiple; delta log V_hat = delta log EPS_ttm
        dlogV = np.log(pe.rdiv(1.0)).diff()   # placeholder replaced below
        # delta log V_hat = delta log(EPS_ttm x k_med): compute from the P/E panel: log EPS_ttm = log P - log PE
        prices = load_prices(A).ffill().resample("ME").last().reindex(pe.index)
        logE = np.log(prices) - np.log(pe)
        for variant, u in log_pv(pe, sect).items():
            kmed = np.log(pe).sub(u)          # log k_med per stock-month
            dV = (logE + kmed).diff()
            ps = per_stock(u, tab, dV)
            key = f"{concept}|{variant}"
            h_med, h_ci, h_iqr = _boot_median(ps["h_mu_days"].replace(np.inf, np.nan))
            ho_med, ho_ci, ho_iqr = _boot_median(ps["h_ols_days"].replace(np.inf, np.nan))
            sx_med, sx_ci, sx_iqr = _boot_median(ps["s_x"])
            sv_med, sv_ci, sv_iqr = _boot_median(ps["sigma_V_daily"])
            results["variants"][key] = {"n_stocks": int(len(ps)), "share_undefined_months": neg_share,
                                        "share_rho_mu_at_grid_top": float(np.mean(ps["rho_mu"] >= RHO_GRID[-1] - 1e-9)),
                                        "h_days_median_unbiased": {"median": h_med, "ci95": h_ci, "iqr": h_iqr},
                                        "h_days_ols": {"median": ho_med, "ci95": ho_ci, "iqr": ho_iqr},
                                        "s_x": {"median": sx_med, "ci95": sx_ci, "iqr": sx_iqr},
                                        "sigma_V_daily_from_dlogVhat": {"median": sv_med, "ci95": sv_ci, "iqr": sv_iqr,
                                                                        "note": "overstated: includes V_hat measurement noise"},
                                        "n_derived_q4_total": int(sum(pe.attrs["n_derived_q4"].values()))}
            if concept == "EarningsPerShareBasic":
                ps.to_csv(os.path.join(OUT, f"pv_by_stock_{variant}.csv"), index=False)
            print(key, json.dumps(results["variants"][key]), flush=True)
    results["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "pv_fit.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    L = ["# E1.2 estimator B: log(P/V_hat) AR(1) with Andrews' median-unbiased correction (PREREG_PHASE_1.md section 4.2)", "",
         f"Set A, monthly {START} .. {END}, EDGAR quarterly EPS (dedup on (concept, start, end), earliest filing; Q4 = FY - 3Q where "
         f"needed), V_hat = EPS_ttm x median trailing P/E (sector where >= {MIN_SECTOR} names, else market); a stock needs >= {MIN_MONTHS} "
         f"consecutive valid months. Medians over stocks with a {N_BOOT}-resample bootstrap. sigma_V here is the sd of delta log V_hat "
         "and is OVERSTATED by the measurement noise in V_hat. Survivor caveat: set A (REG-15).", "",
         "| EPS concept | multiple | n stocks | undefined months | h (days), median-unbiased: median [CI]; IQR | h OLS | s_x | sigma_V/day (dlog V_hat) | rho_MU at grid top |",
         "|---|---|---|---|---|---|---|---|---|"]
    for key, r in results["variants"].items():
        c, v = key.split("|")
        def f(d, dd=0):
            return f"{d['median']:.{dd}f} [{d['ci95'][0]:.{dd}f}, {d['ci95'][1]:.{dd}f}]; {d['iqr'][0]:.{dd}f}-{d['iqr'][1]:.{dd}f}"
        L.append(f"| {c} | {v} | {r['n_stocks']} | {r['share_undefined_months']:.1%} | {f(r['h_days_median_unbiased'])} | {f(r['h_days_ols'])} | "
                 f"{f(r['s_x'], 3)} | {f(r['sigma_V_daily_from_dlogVhat'], 5)} | {r['share_rho_mu_at_grid_top']:.1%} |")
    with open(os.path.join(OUT, "pv_fit.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
