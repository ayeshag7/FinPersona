"""Need #1: daily OHLCV + adjusted close for every historical S&P 500 name, 2000-2025.

Reads datasets/02_constituents/universe_2000_2024.csv (need #2) and tries every
ticker on Yahoo Finance via yfinance.  Names that no longer resolve are recorded
as failures with the reason Yahoo gives -- that record IS the survivorship
measurement REG-15 asks for, so nothing is silently dropped.

No cleaning, no filling: the frames are written as served.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, log_attempt, write_attempts  # noqa: E402

warnings.filterwarnings("ignore")

OUT = DATASETS / "01_prices"
DAILY = OUT / "daily"
NEED = "#1"
START, END = "2000-01-01", "2026-01-01"
BATCH, THREADS, PAUSE = 40, 4, 2.0
COLS = ["Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]


def yahoo_symbol(t: str) -> str:
    """Yahoo writes share classes with a dash: BRK.B -> BRK-B."""
    return str(t).strip().upper().replace(".", "-")


def main(limit: int | None = None) -> int:
    import yfinance as yf

    DAILY.mkdir(parents=True, exist_ok=True)
    uni = pd.read_csv(DATASETS / "02_constituents" / "universe_2000_2024.csv").fillna("")
    tickers = list(uni.ticker.astype(str))
    if limit:
        tickers = tickers[:limit]
    sym = {t: yahoo_symbol(t) for t in tickers}
    log_attempt(NEED, "yfinance/universe", "local", "OK", "%d tickers to try" % len(tickers))

    rows = []
    done = 0
    for i in range(0, len(tickers), BATCH):
        chunk = tickers[i: i + BATCH]
        syms = [sym[t] for t in chunk]
        t0 = time.time()
        try:
            data = yf.download(syms, start=START, end=END, auto_adjust=False, actions=True,
                               progress=False, threads=THREADS, group_by="ticker")
        except Exception as e:
            for t in chunk:
                rows.append({"ticker": t, "yahoo_symbol": sym[t], "status": "batch_error",
                             "n_rows": 0, "first": "", "last": "", "detail": type(e).__name__})
            log_attempt(NEED, "yfinance/batch", "batch", "FAIL", "%s: %s" % (type(e).__name__, e))
            continue

        for t in chunk:
            s = sym[t]
            try:
                df = data[s] if isinstance(data.columns, pd.MultiIndex) else data
                df = df.dropna(how="all")
            except Exception:
                df = pd.DataFrame()
            if df is None or df.empty or df["Close"].dropna().empty:
                rows.append({"ticker": t, "yahoo_symbol": s, "status": "no_data", "n_rows": 0,
                             "first": "", "last": "", "detail": "yfinance returned no price data"})
                continue
            df = df[[c for c in COLS if c in df.columns]].copy()
            df.index.name = "Date"
            df = df.reset_index()
            df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
            df.to_parquet(DAILY / ("%s.parquet" % t), index=False)
            rows.append({"ticker": t, "yahoo_symbol": s, "status": "ok", "n_rows": len(df),
                         "first": str(df.Date.iloc[0])[:10], "last": str(df.Date.iloc[-1])[:10],
                         "detail": ""})
            done += 1

        pd.DataFrame(rows).to_csv(OUT / "retrieval_log.csv", index=False)
        print("  batch %4d-%4d  %5.1fs  ok=%d/%d" % (i, i + len(chunk), time.time() - t0,
                                                     done, i + len(chunk)), flush=True)
        time.sleep(PAUSE)

    log = pd.DataFrame(rows)
    log.to_csv(OUT / "retrieval_log.csv", index=False)
    ok = log[log.status == "ok"]
    log_attempt(NEED, "yfinance/daily", "https://finance.yahoo.com", "OK",
                "retrieved %d/%d tickers (%.1f%%)" % (len(ok), len(log), 100 * len(ok) / max(len(log), 1)))
    write_attempts("01_prices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
