"""
v2.1 Phase 1 -- the E1.0 panel as Phase 1 uses it (PREREG_PHASE_1.md section 1).

Exclusion rule (fixed before any statistic): drop every ticker with a reuse flag (`_manifests/ticker_reuse_screen.csv`,
n_flags > 0), drop the '.'-spelled duplicates (BF.B, BRK.B), clip to 2000-01-03 .. 2024-12-31, returns = daily log
returns of `Adj Close`, no winsorising.

Analysis sets: A = flag-free names with a full 2000-2024 history (the "large-cap analysis set"); B = flag-free
shorter series with >= 1,000 trading days in the window (all of them).

D1 = C (hybrid): every loader takes a `PanelSpec`, so a CRSP/Compustat re-run is a data-path change. The spec is
recorded in every output.
"""
from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")


@dataclass
class PanelSpec:
    root: str = os.path.join(ROOT, "datasets")
    price_dir: str = "01_prices/daily"
    price_col: str = "Adj Close"          # returns; the start-price range uses `level_col`
    level_col: str = "Close"
    fundamentals_dir: str = "03_fundamentals/by_ticker"
    reuse_screen: str = "_manifests/ticker_reuse_screen.csv"
    survivorship: str = "_manifests/survivorship_accounting.csv"
    sectors_file: str = "02_constituents/wikipedia_current_20250611.csv"
    shiller_file: str = "04_shiller/shiller_monthly.csv"
    start: str = "2000-01-03"
    end: str = "2024-12-31"
    min_days_short: int = 1000
    sub_periods: Tuple[Tuple[str, str, str], ...] = (("2000-07", "2000-01-03", "2007-12-31"), ("2008-12", "2008-01-01", "2012-12-31"),
                                                     ("2013-19", "2013-01-01", "2019-12-31"), ("2020-24", "2020-01-01", "2024-12-31"))
    source_note: str = "E1.0 free panel (Yahoo via yfinance 1.6.0, SEC EDGAR company-facts, Shiller), 29 Aug 2026"

    def path(self, *parts) -> str:
        return os.path.join(self.root, *parts)

    def to_dict(self) -> Dict:
        return asdict(self)


DEFAULT = PanelSpec()


def analysis_sets(spec: PanelSpec = DEFAULT, write: bool = True) -> Dict[str, object]:
    """Apply the exclusion rule; return the sets and the accounting table (also written to
    generated/v2_1/e1_0_analysis_sets.csv / .json)."""
    screen = pd.read_csv(spec.path(spec.reuse_screen))
    surv = pd.read_csv(spec.path(spec.survivorship))
    files = {os.path.basename(p)[:-8]: p for p in glob.glob(spec.path(spec.price_dir, "*.parquet"))}
    flagged = set(screen.loc[screen["n_flags"] > 0, "ticker"])
    dotted = {t for t in files if "." in t and t.replace(".", "-") in files}
    rows = []
    for t, p in sorted(files.items()):
        s = surv[surv["ticker"] == t]
        s = s.iloc[0] if len(s) else None
        reason = None
        if t in flagged:
            reason = "reuse_flag"
        elif t in dotted:
            reason = "duplicate_spelling"
        rows.append({"ticker": t, "excluded": reason is not None, "reason": reason or "",
                     "full_history": bool(s["full_history"]) if s is not None else False,
                     "left_index": bool(s["left_index"]) if s is not None else False,
                     "n_rows": int(s["n_rows"]) if s is not None else 0,
                     "first": s["first"] if s is not None else "", "last": s["last"] if s is not None else ""})
    acc = pd.DataFrame(rows)
    kept = acc[~acc["excluded"]]
    A = sorted(kept.loc[kept["full_history"], "ticker"])
    # B: shorter, >= min_days_short trading days INSIDE the window (count rows in the window)
    B = []
    for t in sorted(kept.loc[~kept["full_history"], "ticker"]):
        d = pd.read_parquet(files[t], columns=["Date"])
        n = int(((d["Date"] >= spec.start) & (d["Date"] <= spec.end)).sum())
        if n >= spec.min_days_short:
            B.append(t)
    acc["set"] = np.where(acc["ticker"].isin(A), "A", np.where(acc["ticker"].isin(B), "B", ""))
    out = {"spec": spec.to_dict(), "n_files": len(files), "n_flagged": len(flagged & set(files)), "n_duplicates": len(dotted),
           "A": A, "B": B, "n_A": len(A), "n_B": len(B),
           "A_left_index": int(acc.loc[acc["ticker"].isin(A), "left_index"].sum()),
           "B_left_index": int(acc.loc[acc["ticker"].isin(B), "left_index"].sum())}
    if write:
        os.makedirs(OUT_DIR, exist_ok=True)
        acc.to_csv(os.path.join(OUT_DIR, "e1_0_analysis_sets.csv"), index=False)
        with open(os.path.join(OUT_DIR, "e1_0_analysis_sets.json"), "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
    out["accounting"] = acc
    return out


def load_prices(tickers: List[str], spec: PanelSpec = DEFAULT, col: Optional[str] = None) -> pd.DataFrame:
    """Wide frame (dates x tickers) of `col` (default spec.price_col) inside the window; NaN where a ticker has no row."""
    col = col or spec.price_col
    frames = []
    for t in tickers:
        d = pd.read_parquet(spec.path(spec.price_dir, f"{t}.parquet"), columns=["Date", col])
        d = d[(d["Date"] >= spec.start) & (d["Date"] <= spec.end)]
        frames.append(d.set_index("Date")[col].rename(t))
    wide = pd.concat(frames, axis=1).sort_index()
    return wide


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return np.log(prices).diff()


def sub_period_mask(index: pd.DatetimeIndex, spec: PanelSpec = DEFAULT) -> Dict[str, np.ndarray]:
    index = pd.DatetimeIndex(index)
    return {name: np.asarray((index >= pd.Timestamp(lo)) & (index <= pd.Timestamp(hi))) for name, lo, hi in spec.sub_periods}


# ----------------------------------------------------------------------------------------------------------- EDGAR
QUARTER_DAYS = (80, 100)


def load_edgar(ticker: str, spec: PanelSpec = DEFAULT) -> Optional[pd.DataFrame]:
    p = spec.path(spec.fundamentals_dir, f"{ticker}.parquet")
    if not os.path.exists(p):
        return None
    f = pd.read_parquet(p)
    f["start"] = pd.to_datetime(f["start"], errors="coerce"); f["end"] = pd.to_datetime(f["end"], errors="coerce")
    f["filed"] = pd.to_datetime(f["filed"], errors="coerce")
    return f


def quarterly_eps(ticker: str, concept: str = "EarningsPerShareBasic", spec: PanelSpec = DEFAULT) -> Optional[pd.DataFrame]:
    """Quarterly EPS per (start, end): deduplicated on (concept, start, end) keeping the EARLIEST filing (the brief's rule);
    quarterly rows = 80..100-day periods; Q4 derived as FY - (Q1 + Q2 + Q3) when the three quarters and the FY row exist
    (flag `derived_q4`; EPS is not exactly additive across share-count changes). Returns columns end, eps, filed, derived_q4."""
    f = load_edgar(ticker, spec)
    if f is None:
        return None
    f = f[(f["concept"] == concept) & f["start"].notna() & f["end"].notna() & f["filed"].notna()].copy()
    if f.empty:
        return None
    f = f.sort_values("filed").drop_duplicates(subset=["start", "end"], keep="first")
    f["days"] = (f["end"] - f["start"]).dt.days
    q = f[f["days"].between(*QUARTER_DAYS)].copy()
    fy = f[f["days"].between(350, 380)].copy()
    q["derived_q4"] = False
    rows = [q[["end", "val", "filed", "derived_q4"]].rename(columns={"val": "eps"})]
    # derive missing fourth quarters
    for _, y in fy.iterrows():
        inside = q[(q["end"] > y["start"]) & (q["end"] <= y["end"])]
        if len(inside) == 3 and not (q["end"] == y["end"]).any():
            rows.append(pd.DataFrame({"end": [y["end"]], "eps": [float(y["val"]) - float(inside["val"].sum())],
                                      "filed": [y["filed"]], "derived_q4": [True]}))
    out = pd.concat(rows, ignore_index=True).sort_values("end").drop_duplicates(subset=["end"], keep="first").reset_index(drop=True)
    out["eps"] = out["eps"].astype(float)
    return out


def filing_dates(ticker: str, spec: PanelSpec = DEFAULT) -> Optional[pd.DatetimeIndex]:
    """Unique 10-Q / 10-K filing dates (the announcement-window anchors of E1.4; 10-K/A excluded)."""
    f = load_edgar(ticker, spec)
    if f is None:
        return None
    d = f.loc[f["form"].isin(["10-Q", "10-K"]), "filed"].dropna().unique()
    return pd.DatetimeIndex(sorted(d))


def sectors(spec: PanelSpec = DEFAULT) -> Dict[str, str]:
    w = pd.read_csv(spec.path(spec.sectors_file))
    return dict(zip(w["ticker"].astype(str).str.replace(".", "-", regex=False), w["sector"]))


def shiller(spec: PanelSpec = DEFAULT) -> pd.DataFrame:
    s = pd.read_csv(spec.path(spec.shiller_file))
    s = s[["Date", "P", "D", "E", "CPI"]].dropna(subset=["P"]).copy()
    yr = np.floor(s["Date"]).astype(int); mo = np.round((s["Date"] - yr) * 100).astype(int)
    s["month"] = pd.to_datetime(dict(year=yr, month=mo, day=1))
    return s.set_index("month")


if __name__ == "__main__":
    r = analysis_sets()
    print(json.dumps({k: v for k, v in r.items() if k not in ("A", "B", "accounting")}, indent=1))
