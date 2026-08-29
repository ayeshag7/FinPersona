"""Need #8: an INDEPENDENT second daily price source, to cross-check need #1.

Source: Nasdaq's own public historical-quote endpoint, `api.nasdaq.com`.  No API key,
no account.  It serves roughly the last ten years, which overlaps Yahoo enough to test
the panel.  This host was DNS-filter-blocked earlier on 29 Aug 2026; the filter was
later lifted.

Still NOT usable, and not worked around -- these are site-level anti-bot measures, not
network policy:
  * stooq.com  -> serves a JavaScript proof-of-work challenge page to scripts
  * aaii.com   -> serves a JavaScript bot-challenge page to scripts

Prices here are split-adjusted but NOT dividend-adjusted, so they cross-check Yahoo's
`Close`, not its `Adj Close`.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, UA, get, log_attempt, save_bytes, write_attempts  # noqa: E402

OUT = DATASETS / "08_price_crosscheck"
DAILY = OUT / "daily"
NEED = "#8"
API = "https://api.nasdaq.com/api/quote/%s/historical"
PAUSE = 0.5


def money(s):
    """'$271.86' -> 271.86 ; '27,293,640' -> 27293640 ; '' / 'N/A' -> None."""
    t = str(s).replace("$", "").replace(",", "").strip()
    if t in ("", "N/A", "--", "nan"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def main(limit: int | None = None) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    DAILY.mkdir(parents=True, exist_ok=True)

    # Nasdaq's traded-symbol directory: carries an ETF flag, which independently
    # corroborates the ticker-reuse screen of need #1.
    r = get("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt",
            need=NEED, source="nasdaqtrader/symbol-directory")
    if r:
        save_bytes(r.content, OUT / "nasdaqtraded.txt")

    log = pd.read_csv(DATASETS / "01_prices" / "retrieval_log.csv").fillna("")
    tickers = list(log[log.status == "ok"].ticker.astype(str))
    if limit:
        tickers = tickers[:limit]

    # Resume: keep whatever a previous run already wrote. api.nasdaq.com can hang a
    # connection past the read timeout, so a run may need restarting; without this it
    # would re-download everything.
    prev_path = OUT / "retrieval_log.csv"
    rows: list[dict] = []
    done: set[str] = set()
    if prev_path.exists():
        prev = pd.read_csv(prev_path).fillna("")
        for _, r in prev.iterrows():
            if r["status"] == "ok" and (DAILY / ("%s.parquet" % r["ticker"])).exists():
                rows.append(dict(r))
                done.add(str(r["ticker"]))
    if done:
        print("resuming: %d tickers already retrieved, %d to go"
              % (len(done), len(tickers) - len(done)), flush=True)

    sess = requests.Session()
    sess.headers.update({"User-Agent": UA, "Accept": "application/json"})

    for i, t in enumerate(tickers):
        if t in done:
            continue
        sym = t.replace(".", "-")
        try:
            time.sleep(PAUSE)
            # (connect, read) timeouts: a bare read timeout is not enough here.
            resp = sess.get(API % sym, timeout=(10, 30), params={
                "assetclass": "stocks", "fromdate": "2000-01-01",
                "todate": "2026-01-01", "limit": "9999"})
        except Exception as e:
            rows.append({"ticker": t, "status": "error", "n_rows": 0, "first": "",
                         "last": "", "detail": type(e).__name__})
            continue
        if resp.status_code != 200:
            rows.append({"ticker": t, "status": "http_%d" % resp.status_code, "n_rows": 0,
                         "first": "", "last": "", "detail": ""})
            continue
        try:
            data = (resp.json().get("data") or {})
            recs = ((data.get("tradesTable") or {}).get("rows") or [])
        except Exception as e:
            rows.append({"ticker": t, "status": "parse_error", "n_rows": 0, "first": "",
                         "last": "", "detail": type(e).__name__})
            continue
        if not recs:
            rows.append({"ticker": t, "status": "no_data", "n_rows": 0, "first": "",
                         "last": "", "detail": "empty tradesTable"})
            continue
        df = pd.DataFrame(recs)
        df["Date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")
        for c in ["open", "high", "low", "close", "volume"]:
            if c in df.columns:
                df[c.capitalize()] = df[c].map(money)
        df = df.dropna(subset=["Date"]).sort_values("Date")
        keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        df[keep].to_parquet(DAILY / ("%s.parquet" % t), index=False)
        rows.append({"ticker": t, "status": "ok", "n_rows": len(df),
                     "first": str(df.Date.min())[:10], "last": str(df.Date.max())[:10],
                     "detail": ""})
        if (i + 1) % 50 == 0:
            pd.DataFrame(rows).to_csv(OUT / "retrieval_log.csv", index=False)
            ok = sum(1 for x in rows if x["status"] == "ok")
            print("  nasdaq %4d/%4d  ok=%d" % (i + 1, len(tickers), ok), flush=True)

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "retrieval_log.csv", index=False)
    ok = out[out.status == "ok"]
    log_attempt(NEED, "api.nasdaq.com", "https://api.nasdaq.com", "OK",
                "%d/%d tickers cross-check series retrieved" % (len(ok), len(out)))
    write_attempts("08_crosscheck")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
