"""Basic quality checks on every downloaded series (E1.0 step 4).

Checks only; nothing is cleaned, filled or dropped.  Per the plan, anomalies are
reported so that later phases can decide what to do about them.

Price checks per ticker: date range, duplicate dates, calendar gaps, non-positive
prices, |daily return| > 50 %, zero-volume days, NaNs.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, MANIFESTS  # noqa: E402

warnings.filterwarnings("ignore")
GAP_DAYS = 7  # calendar days between consecutive rows that counts as a gap


def check_prices() -> pd.DataFrame:
    rows = []
    for p in sorted((DATASETS / "01_prices" / "daily").glob("*.parquet")):
        df = pd.read_parquet(p)
        d = pd.to_datetime(df["Date"])
        px = pd.to_numeric(df.get("Adj Close"), errors="coerce")
        cl = pd.to_numeric(df.get("Close"), errors="coerce")
        vol = pd.to_numeric(df.get("Volume"), errors="coerce")
        ret = px / px.shift(1) - 1
        gaps = d.diff().dt.days
        rows.append({
            "ticker": p.stem, "n_rows": len(df),
            "first": str(d.min())[:10], "last": str(d.max())[:10],
            "dup_dates": int(d.duplicated().sum()),
            "gaps_gt_%dd" % GAP_DAYS: int((gaps > GAP_DAYS).sum()),
            "max_gap_days": int(gaps.max()) if len(df) > 1 and pd.notna(gaps.max()) else 0,
            "nan_adjclose": int(px.isna().sum()), "nan_close": int(cl.isna().sum()),
            "nonpos_adjclose": int((px <= 0).sum()), "nonpos_close": int((cl <= 0).sum()),
            "abs_ret_gt_50pct": int((ret.abs() > 0.50).sum()),
            "max_abs_ret": round(float(ret.abs().max()), 4) if ret.notna().any() else np.nan,
            "zero_volume_days": int((vol == 0).sum()),
            "nan_volume": int(vol.isna().sum()),
        })
    out = pd.DataFrame(rows)
    out.to_csv(MANIFESTS / "quality_prices.csv", index=False)
    return out


def check_generic(path: Path, datecol: str, valcols: list[str], label: str) -> dict:
    if not path.exists():
        return {"series": label, "status": "missing"}
    df = pd.read_csv(path)
    if datecol not in df.columns:
        datecol = df.columns[0]
    raw = df[datecol]
    if "shiller" in label.lower():
        # Shiller writes the period as a fractional year: 1871.01 = Jan 1871,
        # 2026.10 = Oct 2026. Parse it as YYYY.MM rather than as a date string.
        s = raw.astype(str).str.strip()
        yr = pd.to_numeric(s.str.split(".").str[0], errors="coerce")
        mo = pd.to_numeric(s.str.split(".").str[1].str.pad(2, "right", "0"), errors="coerce")
        d = pd.to_datetime(dict(year=yr, month=mo.clip(1, 12), day=1), errors="coerce")
    elif datecol == "yearmo":
        # Baker-Wurgler writes the period as an integer YYYYMM (195801); parsed as a
        # plain number pandas would read it as epoch nanoseconds.
        d = pd.to_datetime(raw.astype("Int64").astype(str), format="%Y%m", errors="coerce")
    else:
        d = pd.to_datetime(raw, errors="coerce")
    rec = {"series": label, "status": "ok", "file": path.name, "n_rows": len(df),
           "first": str(d.min())[:10], "last": str(d.max())[:10],
           "dup_dates": int(d.duplicated().sum()), "unparsed_dates": int(d.isna().sum())}
    for c in valcols:
        if c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce")
            rec["nan_" + c] = int(v.isna().sum())
            rec["nonpos_" + c] = int((v <= 0).sum())
    return rec


def check_parquet(path: Path, datecol: str, valcols: list[str], label: str) -> dict:
    """Same checks as check_generic, for the Parquet series (CBOE)."""
    if not path.exists():
        return {"series": label, "status": "missing"}
    df = pd.read_parquet(path)
    d = pd.to_datetime(df[datecol], errors="coerce")
    rec = {"series": label, "status": "ok", "file": path.name, "n_rows": len(df),
           "first": str(d.min())[:10], "last": str(d.max())[:10],
           "dup_dates": int(d.duplicated().sum()), "unparsed_dates": int(d.isna().sum())}
    for c in valcols:
        if c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce")
            rec["nan_" + c] = int(v.isna().sum())
            rec["nonpos_" + c] = int((v <= 0).sum())
    return rec


def main() -> int:
    MANIFESTS.mkdir(parents=True, exist_ok=True)

    px = check_prices()
    print("== #1 prices: %d tickers checked" % len(px))
    if len(px):
        print("   duplicate dates      : %d tickers (%d rows)"
              % ((px.dup_dates > 0).sum(), px.dup_dates.sum()))
        print("   non-positive adjclose: %d tickers" % (px.nonpos_adjclose > 0).sum())
        print("   |ret| > 50%%          : %d tickers, %d day-observations"
              % ((px.abs_ret_gt_50pct > 0).sum(), px.abs_ret_gt_50pct.sum()))
        print("   zero-volume days     : %d tickers, %d day-observations"
              % ((px.zero_volume_days > 0).sum(), px.zero_volume_days.sum()))
        print("   calendar gaps > %dd   : %d tickers" % (GAP_DAYS, (px["gaps_gt_%dd" % GAP_DAYS] > 0).sum()))
        print("   NaN adj close        : %d tickers" % (px.nan_adjclose > 0).sum())

    others = []
    iv = DATASETS / "05_implied_vol"
    for f in sorted(iv.glob("*.csv")):
        if f.name != "retrieval_log.csv":
            others.append(check_generic(f, "Date", ["Close", "Open", "High", "Low"], "#5 " + f.stem))
    for f in sorted((iv / "fred").glob("*.csv")):
        others.append(check_generic(f, "observation_date", [f.stem], "#5 fred/" + f.stem))
    for f in sorted((iv / "cboe").glob("*.parquet")):
        others.append(check_parquet(f, "DATE", ["OPEN", "HIGH", "LOW", "CLOSE"],
                                    "#5 cboe/" + f.stem))
    others.append(check_generic(DATASETS / "06_sentiment" / "sf_fed_news_sentiment.csv",
                                "date", ["News Sentiment"], "#6 sf_fed_news_sentiment"))
    others.append(check_generic(DATASETS / "06_sentiment" / "bw_SENTIMENT_DATA.csv",
                                "yearmo", ["SENT", "SENT_ORTH"], "#6 baker_wurgler"))
    others.append(check_generic(DATASETS / "06_sentiment" / "aaii_sentiment_weekly.csv",
                                "Date", ["Bullish", "Neutral", "Bearish"], "#6 aaii_weekly"))
    others.append(check_generic(DATASETS / "04_shiller" / "shiller_monthly.csv",
                                "Date", [], "#4 shiller_monthly"))

    od = pd.DataFrame(others)
    od.to_csv(MANIFESTS / "quality_other.csv", index=False)
    print("\n== other series")
    cols = [c for c in ["series", "status", "n_rows", "first", "last", "dup_dates"] if c in od.columns]
    print(od[cols].to_string(index=False))

    # -------- need #8 cross-check panel, aggregate (per-ticker detail is in
    # -------- _manifests/source_agreement.csv, which compares it with need #1)
    xc = sorted((DATASETS / "08_price_crosscheck" / "daily").glob("*.parquet"))
    if xc:
        n = dup = nonpos = 0
        lo, hi = "9999", "0000"
        for p in xc:
            df = pd.read_parquet(p)
            d = pd.to_datetime(df["Date"], errors="coerce")
            n += len(df)
            dup += int(d.duplicated().sum())
            nonpos += int((pd.to_numeric(df["Close"], errors="coerce") <= 0).sum())
            lo, hi = min(lo, str(d.min())[:10]), max(hi, str(d.max())[:10])
        print("\n== #8 cross-check panel (Nasdaq): %d tickers, %s rows, %s..%s"
              % (len(xc), "{:,}".format(n), lo, hi))
        print("   duplicate dates: %d   non-positive closes: %d" % (dup, nonpos))

    # -------- survivorship accounting for REG-15 (numbers only, no decision) ----
    uni = pd.read_csv(DATASETS / "02_constituents" / "universe_2000_2024.csv").fillna("")
    log = pd.read_csv(DATASETS / "01_prices" / "retrieval_log.csv").fillna("")
    m = uni.merge(log[["ticker", "status", "n_rows", "first", "last"]], on="ticker", how="left")
    m["retrieved"] = m.status == "ok"
    m["left_index"] = m.exit_hint != ""
    fullhist = pd.to_datetime(m["first"], errors="coerce").le("2000-01-10") & \
        pd.to_datetime(m["last"], errors="coerce").ge("2024-12-24")
    m["full_history"] = fullhist.fillna(False)
    m.to_csv(MANIFESTS / "survivorship_accounting.csv", index=False)

    print("\n== survivorship (need #1 x #2)")
    print("   universe (in index at any time 2000-2024): %d" % len(m))
    print("   retrieved from Yahoo                     : %d (%.1f%%)"
          % (m.retrieved.sum(), 100 * m.retrieved.mean()))
    print("   with full 2000-2024 history              : %d (%.1f%%)"
          % (m.full_history.sum(), 100 * m.full_history.mean()))
    g = m.groupby("left_index").agg(n=("ticker", "size"), retrieved=("retrieved", "sum"),
                                    full=("full_history", "sum"))
    g["retrieved_pct"] = (100 * g.retrieved / g.n).round(1)
    g.index = ["still in index at 2024-12-31", "left the index during 2000-2024"]
    print(g.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
