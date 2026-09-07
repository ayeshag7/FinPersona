"""
E5.2 data step: earnings-announcement dates from EDGAR 8-K Item 2.02 filings (PREREG_PHASE_5.md section 5.1).

    python -m tools.phase5.fetch_8k [--limit N]

Source: the SEC submissions API, one JSON per CIK (https://data.sec.gov/submissions/CIK##########.json) plus the
paged history files it lists.  For every 8-K whose `items` carries "2.02" (Results of Operations and Financial
Condition -- the earnings release) the filing date and the report (event) date are kept.  Universe: Phase 1's set
A, CIK taken from the ticker's E1.0 fundamentals parquet.  Goes through tools/e1_0_data/common.get (declared
User-Agent, per-host throttle, attempt log); nothing else is downloaded and the raw JSON is not stored.

Output: datasets/03_fundamentals/announcements/<TICKER>.parquet (ticker, cik, form, filed, report_date, items) and
        datasets/_manifests/attempts_05_8k.json.  datasets/ is git-ignored and never leaves this machine.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "e1_0_data"))
from common import DATASETS, get, log_attempt, write_attempts  # noqa: E402  (tools/e1_0_data/common.py)

OUT = DATASETS / "03_fundamentals" / "announcements"
NEED = "#3b"


def cik_of(ticker: str):
    p = DATASETS / "03_fundamentals" / "by_ticker" / f"{ticker}.parquet"
    if not p.exists():
        return None
    f = pd.read_parquet(p, columns=["cik"])
    return str(f["cik"].iloc[0]).zfill(10) if len(f) else None


def _rows(block, ticker, cik):
    forms = block.get("form", []); dates = block.get("filingDate", []); rep = block.get("reportDate", [])
    items = block.get("items", []); acc = block.get("accessionNumber", [])
    out = []
    for i in range(len(forms)):
        if forms[i] in ("8-K", "8-K/A") and "2.02" in str(items[i] if i < len(items) else ""):
            out.append({"ticker": ticker, "cik": cik, "form": forms[i], "filed": dates[i],
                        "report_date": rep[i] if i < len(rep) else "", "items": items[i], "accn": acc[i] if i < len(acc) else ""})
    return out


def fetch_one(ticker: str, cik: str):
    r = get(f"https://data.sec.gov/submissions/CIK{cik}.json", need=NEED, source="sec/submissions", timeout=60)
    if r is None:
        return None
    d = r.json()
    rows = _rows(d.get("filings", {}).get("recent", {}), ticker, cik)
    for f in d.get("filings", {}).get("files", []):
        r2 = get(f"https://data.sec.gov/submissions/{f['name']}", need=NEED, source="sec/submissions-page", timeout=60)
        if r2 is None:
            continue
        rows += _rows(r2.json(), ticker, cik)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    from tools.phase1.panel import analysis_sets
    A = analysis_sets(write=False)["A"]
    if a.limit:
        A = A[:a.limit]
    t0 = time.time()
    done = 0; skipped = 0; failed = []
    for t in A:
        p = OUT / f"{t}.parquet"
        if p.exists() and not a.refresh:
            skipped += 1
            continue
        cik = cik_of(t)
        if cik is None:
            failed.append((t, "no CIK in the E1.0 fundamentals"))
            continue
        df = fetch_one(t, cik)
        if df is None:
            failed.append((t, "fetch failed"))
            continue
        df.to_parquet(p, index=False)
        done += 1
        if done % 25 == 0:
            print(f"  {done} fetched, {skipped} cached, {len(failed)} failed, {time.time() - t0:.0f} s", flush=True)
    write_attempts("05_8k")
    summary = {"universe": len(A), "fetched": done, "cached": skipped, "failed": failed, "seconds": round(time.time() - t0)}
    (OUT / "README.md").write_text(
        "# 8-K Item 2.02 earnings-announcement dates (E5.2)\n\n"
        "Source: SEC EDGAR submissions API (data.sec.gov/submissions), public domain; declared User-Agent, <= 3 req/s. "
        f"Fetched {time.strftime('%Y-%m-%d')} for Phase 1's set A. One parquet per ticker: ticker, cik, form, filed, "
        "report_date, items, accn -- only 8-K/8-K-A filings whose items include 2.02. Raw JSON not stored. "
        f"Universe {len(A)}: fetched {done}, cached {skipped}, failed {len(failed)}.\n", encoding="utf-8")
    json.dump(summary, open(OUT / "_summary.json", "w", encoding="utf-8"), indent=1)
    print(json.dumps(summary, indent=1)[:2000])


if __name__ == "__main__":
    main()
