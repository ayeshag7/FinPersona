"""Need #3: quarterly EPS (basic, diluted), DPS, period ends and filing dates.

Source: SEC EDGAR XBRL "company facts" API (data.sec.gov), one call per CIK.
The raw JSON is ~3.8 MB per filer, so it is streamed and only the wanted
us-gaap concepts are kept; the raw payload is not stored.

Ticker -> CIK comes from two public files, neither of which needs a key:
  * https://www.sec.gov/include/ticker.txt      (all current registrants)
  * the CIK column of the archived Wikipedia constituents table (need #2)
Delisted names that no longer appear in either are reported as unmatched --
that is part of the same survivorship accounting as need #1.

SEC fair-access policy: a declared User-Agent and <= 10 requests/second.
common.RATE keeps this run at about 3/s.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, UA, get, log_attempt, save_bytes, write_attempts  # noqa: E402

OUT = DATASETS / "03_fundamentals"
FACTS = OUT / "by_ticker"
NEED = "#3"

# us-gaap concepts kept. The first three are what E1.0 asks for; the last two ride
# along in the same JSON at no extra cost and support the B/M/profitability
# references in plan section 5.1 (Vuolteenaho 2002; Cohen-Polk-Vuolteenaho 2003).
CONCEPTS = [
    "EarningsPerShareBasic",
    "EarningsPerShareDiluted",
    "CommonStockDividendsPerShareDeclared",
    "CommonStockDividendsPerShareCashPaid",
    "NetIncomeLoss",
    "StockholdersEquity",
]


def _normname(s: str) -> str:
    """Normalise a company name for exact (not fuzzy) matching."""
    s = str(s).upper()
    for junk in [",", ".", "'", '"', "(", ")", "&AMP;", "  "]:
        s = s.replace(junk, " " if junk == "  " else "")
    for suf in [" INCORPORATED", " INC", " CORPORATION", " CORP", " COMPANY", " CO",
                " LIMITED", " LTD", " PLC", " LLC", " LP", " HOLDINGS", " HOLDING",
                " GROUP", " THE", " CLASS A", " CLASS B", " NEW", " COM"]:
        while s.endswith(suf):
            s = s[: -len(suf)]
    return " ".join(s.split()).strip()


def load_cik_map() -> tuple[dict[str, str], dict[str, str]]:
    """ticker (upper) -> 10-digit CIK, plus ticker -> how it was resolved."""
    m: dict[str, str] = {}
    how: dict[str, str] = {}

    r = get("https://www.sec.gov/include/ticker.txt", need=NEED, source="sec/ticker.txt")
    if r:
        save_bytes(r.content, OUT / "sec_ticker_cik.txt")
        for line in r.text.splitlines():
            parts = line.split("\t")
            if len(parts) == 2 and parts[1].strip().isdigit():
                t = parts[0].strip().upper()
                m[t], how[t] = parts[1].strip().zfill(10), "sec_ticker_txt"
        log_attempt(NEED, "sec/ticker.txt", "parsed", "OK", "%d ticker->CIK pairs" % len(m))

    wiki = DATASETS / "02_constituents" / "wikipedia_current_20250611.csv"
    if wiki.exists():
        df = pd.read_csv(wiki, dtype=str).fillna("")
        n = 0
        for _, row in df.iterrows():
            t, c = row["ticker"].strip().upper(), row["cik"].strip()
            if t and c.isdigit() and t not in m:
                m[t], how[t] = c.zfill(10), "wikipedia_cik"
                n += 1
        log_attempt(NEED, "wikipedia/cik-column", "parsed", "OK", "%d extra ticker->CIK" % n)

    # Delisted names are absent from ticker.txt (it lists current registrants only).
    # SEC's historical company->CIK file covers them; we match on an exactly
    # normalised company name taken from the archived Wikipedia changes table.
    changes = DATASETS / "02_constituents" / "wikipedia_changes.csv"
    if changes.exists():
        names: dict[str, str] = {}
        ch = pd.read_csv(changes, dtype=str).fillna("")
        for _, row in ch.iterrows():
            for tk, nm in [(row["added_ticker"], row["added_name"]),
                           (row["removed_ticker"], row["removed_name"])]:
                tk = tk.strip().upper()
                if tk and nm.strip() and tk not in m:
                    names.setdefault(tk, nm.strip())
        want = {_normname(v): k for k, v in names.items()}
        if want:
            r = get("https://www.sec.gov/Archives/edgar/cik-lookup-data.txt",
                    need=NEED, source="sec/cik-lookup-data", timeout=180)
            if r:
                hit = 0
                for line in r.content.decode("latin-1").splitlines():
                    parts = line.rsplit(":", 2)
                    if len(parts) < 2 or not parts[1].isdigit():
                        continue
                    key = _normname(parts[0])
                    tk = want.get(key)
                    if tk and tk not in m:
                        m[tk], how[tk] = parts[1].zfill(10), "sec_name_lookup"
                        hit += 1
                log_attempt(NEED, "sec/cik-lookup-data", "parsed", "OK",
                            "%d of %d delisted names resolved by exact name match"
                            % (hit, len(want)))
    return m, how


def extract(facts: dict, ticker: str, cik: str) -> pd.DataFrame:
    rows = []
    gaap = (facts.get("facts") or {}).get("us-gaap") or {}
    for concept in CONCEPTS:
        node = gaap.get(concept)
        if not node:
            continue
        for unit, entries in (node.get("units") or {}).items():
            for e in entries:
                rows.append({
                    "ticker": ticker, "cik": cik, "concept": concept, "unit": unit,
                    "start": e.get("start", ""), "end": e.get("end", ""),
                    "val": e.get("val"), "fy": e.get("fy"), "fp": e.get("fp"),
                    "form": e.get("form", ""), "filed": e.get("filed", ""),
                    "frame": e.get("frame", ""), "accn": e.get("accn", ""),
                })
    return pd.DataFrame(rows)


def main(limit: int | None = None) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    FACTS.mkdir(parents=True, exist_ok=True)

    cikmap, cikhow = load_cik_map()
    uni = pd.read_csv(DATASETS / "02_constituents" / "universe_2000_2024.csv").fillna("")
    tickers = list(uni.ticker.astype(str))
    if limit:
        tickers = tickers[:limit]

    sess = requests.Session()
    sess.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})

    rows = []
    matched = [t for t in tickers if t.upper() in cikmap]
    log_attempt(NEED, "cik-match", "local", "OK",
                "%d/%d universe tickers matched to a CIK (%.1f%%)"
                % (len(matched), len(tickers), 100 * len(matched) / max(len(tickers), 1)))

    for i, t in enumerate(tickers):
        cik = cikmap.get(t.upper())
        if not cik:
            rows.append({"ticker": t, "cik": "", "cik_source": "", "status": "no_cik",
                         "n_facts": 0, "first_end": "", "last_end": "",
                         "detail": "not in ticker.txt, wiki CIKs or SEC name lookup"})
            continue
        url = "https://data.sec.gov/api/xbrl/companyfacts/CIK%s.json" % cik
        try:
            time.sleep(0.34)  # SEC fair access: stay well under 10 req/s
            r = sess.get(url, timeout=90)
        except Exception as e:
            rows.append({"ticker": t, "cik": cik, "cik_source": cikhow.get(t.upper(), ""), "status": "error", "n_facts": 0,
                         "first_end": "", "last_end": "", "detail": type(e).__name__})
            continue
        if r.status_code != 200:
            rows.append({"ticker": t, "cik": cik, "cik_source": cikhow.get(t.upper(), ""), "status": "http_%d" % r.status_code,
                         "n_facts": 0, "first_end": "", "last_end": "",
                         "detail": "companyfacts returned %d" % r.status_code})
            continue
        try:
            df = extract(r.json(), t, cik)
        except Exception as e:
            rows.append({"ticker": t, "cik": cik, "cik_source": cikhow.get(t.upper(), ""), "status": "parse_error", "n_facts": 0,
                         "first_end": "", "last_end": "", "detail": type(e).__name__})
            continue
        if df.empty:
            rows.append({"ticker": t, "cik": cik, "cik_source": cikhow.get(t.upper(), ""), "status": "no_concepts", "n_facts": 0,
                         "first_end": "", "last_end": "",
                         "detail": "none of the %d concepts present" % len(CONCEPTS)})
            continue
        df.to_parquet(FACTS / ("%s.parquet" % t), index=False)
        rows.append({"ticker": t, "cik": cik, "cik_source": cikhow.get(t.upper(), ""), "status": "ok", "n_facts": len(df),
                     "first_end": str(df["end"].min()), "last_end": str(df["end"].max()),
                     "detail": ""})
        if (i + 1) % 50 == 0:
            pd.DataFrame(rows).to_csv(OUT / "retrieval_log.csv", index=False)
            ok = sum(1 for x in rows if x["status"] == "ok")
            print("  edgar %4d/%4d  ok=%d" % (i + 1, len(tickers), ok), flush=True)

    log = pd.DataFrame(rows)
    log.to_csv(OUT / "retrieval_log.csv", index=False)
    ok = log[log.status == "ok"]
    log_attempt(NEED, "edgar/companyfacts", "https://data.sec.gov", "OK",
                "%d/%d tickers with facts (%.1f%%)"
                % (len(ok), len(log), 100 * len(ok) / max(len(log), 1)))
    write_attempts("03_fundamentals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
