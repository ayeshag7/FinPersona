"""Ingest files a HUMAN downloaded manually, and check them like any other series.

Some sources disallow automated fetching in `robots.txt` even though the file itself is
public and free.  `robots.txt` binds crawlers, not people, so the route is: a person
downloads the file in a browser, drops it in the right folder, and this script parses,
checks and documents it exactly as the automated fetchers do.

Currently handled
-----------------
  AAII weekly sentiment survey  (need #6)
      download : https://www.aaii.com/files/surveys/sentiment.xls
      reason    : www.aaii.com/robots.txt has "Disallow: /files/*" for User-agent: *
      drop at   : datasets/06_sentiment/sentiment.xls   (.xlsx or .csv also accepted)

Run with no arguments; it reports what it found and what is still missing.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, log_attempt, write_attempts  # noqa: E402

warnings.filterwarnings("ignore")

AAII_DIR = DATASETS / "06_sentiment"
# Preferred name first. NB: this folder already holds Baker-Wurgler's SENTIMENT.xlsx,
# and Windows paths are case-insensitive, so a bare "sentiment.xlsx" would collide with
# it. Candidates are therefore content-checked, not trusted by name.
AAII_NAMES = ["aaii_sentiment.xls", "aaii_sentiment.xlsx", "aaii_sentiment.csv",
              "sentiment.xls", "sentiment.csv", "sentiment.xlsx"]
AAII_URL = "https://www.aaii.com/files/surveys/sentiment.xls"
BW_FILES = {"sentiment.xlsx"}  # Baker-Wurgler's file, already in this folder


def _candidates(folder: Path, names: list[str]) -> list[Path]:
    seen, out = set(), []
    for n in names:
        p = folder / n
        if not p.exists() or p.stat().st_size <= 1000:
            continue
        real = p.resolve()
        if real in seen:
            continue
        # Skip the Baker-Wurgler workbook that shares this name case-insensitively.
        if real.name.lower() in BW_FILES and real.stat().st_size < 200_000:
            continue
        seen.add(real)
        out.append(p)
    return out


def _read_any(p: Path) -> list[tuple[str, pd.DataFrame]]:
    if p.suffix.lower() == ".csv":
        return [("csv", pd.read_csv(p, header=None))]
    xl = pd.ExcelFile(p)
    return [(s, xl.parse(s, header=None)) for s in xl.sheet_names]


def _locate_header(df: pd.DataFrame) -> int | None:
    """AAII's workbook carries title rows above the real header. Find the row that
    names the three survey columns; do not assume a fixed offset."""
    want = ("bullish", "neutral", "bearish")
    for i in range(min(len(df), 40)):
        cells = [str(x).strip().lower() for x in df.iloc[i].tolist()]
        if sum(any(w == c or w in c for c in cells) for w in want) >= 2:
            return i
    return None


def ingest_aaii() -> bool:
    cands = _candidates(AAII_DIR, AAII_NAMES)
    if not cands:
        print("AAII  : NOT FOUND")
        print("        download %s" % AAII_URL)
        print("        save to  %s" % (AAII_DIR / "aaii_sentiment.xls"))
        print("        (robots.txt forbids a script from fetching it; a person may)")
        return False

    best, src = None, None
    for cand in cands:
        print("AAII  : trying %s (%s bytes)" % (cand.name, "{:,}".format(cand.stat().st_size)))
        try:
            sheets = _read_any(cand)
        except Exception as e:
            print("        unreadable: %s" % type(e).__name__)
            continue
        for sheet, raw in sheets:
            h = _locate_header(raw)
            if h is None:
                continue
            df = raw.iloc[h + 1:].copy()
            df.columns = [str(c).strip() for c in raw.iloc[h].tolist()]
            df = df.loc[:, [c for c in df.columns if c and c.lower() != "nan"]]
            datecol = df.columns[0]
            df[datecol] = pd.to_datetime(df[datecol], errors="coerce")
            df = df.dropna(subset=[datecol])
            if len(df) > 50 and (best is None or len(df) > len(best[1])):
                best, src = (sheet, df, datecol), cand
    if best is None:
        print("        PARSE FAILED - no Bullish/Neutral/Bearish header row in any candidate")
        print("        (the file in this folder is probably not the AAII survey)")
        log_attempt("#6", "aaii/manual-ingest", AAII_URL, "FAIL",
                    "no candidate file parsed as the AAII survey")
        return False

    sheet, df, datecol = best
    print("        parsed from %s" % src.name)
    out = AAII_DIR / "aaii_sentiment_weekly.csv"
    df.to_csv(out, index=False)

    d = pd.to_datetime(df[datecol], errors="coerce")
    gaps = d.sort_values().diff().dt.days
    print("        sheet '%s': %d rows, %s -> %s"
          % (sheet, len(df), str(d.min())[:10], str(d.max())[:10]))
    print("        columns: %s" % ", ".join(map(str, list(df.columns)[:8])))
    print("        duplicate dates: %d | gaps > 14d: %d | median spacing: %.0f d"
          % (int(d.duplicated().sum()), int((gaps > 14).sum()),
             float(gaps.median()) if gaps.notna().any() else -1))
    print("        -> %s" % out.relative_to(DATASETS.parent))
    log_attempt("#6", "aaii/manual-ingest", AAII_URL, "OK",
                "%d weekly rows %s..%s (downloaded manually; robots.txt forbids scripted fetch)"
                % (len(df), str(d.min())[:10], str(d.max())[:10]))
    return True


def main() -> int:
    print("Manual-download ingest\n" + "-" * 60)
    got = ingest_aaii()
    print("-" * 60)
    if got:
        print("Done. Re-run quality_checks.py and write_readmes.py to refresh the panel docs.")
    else:
        print("Nothing ingested. Place the file(s) above and re-run.")
    write_attempts("manual_ingest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
