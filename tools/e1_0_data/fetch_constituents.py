"""Need #2: historical S&P 500 constituents with add/remove dates, 2000-2024.

Three independent public sources are downloaded and cross-checked; none needs an
account or a key.  The plan's original candidate (the Wikipedia "Selected
changes" table) was removed from the live article in Aug 2025, so we read it from
the last revision that still carried it, via the MediaWiki API.

  A. fja05680/sp500             MIT           point-in-time components 1996-> + start/end
  B. hanshof/sp500_constituents MIT           daily point-in-time components 1996->
  C. Wikipedia rev 1295035732   CC BY-SA 4.0  "Selected changes" table + current list
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, get, log_attempt, save_bytes, write_attempts  # noqa: E402

OUT = DATASETS / "02_constituents"
NEED = "#2"

RAW = "https://raw.githubusercontent.com"
FJA = RAW + "/fja05680/sp500/master"
HAN = RAW + "/hanshof/sp500_constituents/main"
# Last revision of "List of S&P 500 companies" that still contains the changes table.
WIKI_OLDID = 1295035732

FILES_A = [
    ("S&P 500 Historical Components & Changes.csv", "fja_components_full.csv"),
    ("S&P 500 Historical Components & Changes (Updated).csv", "fja_components_updated.csv"),
    ("sp500_ticker_start_end.csv", "fja_ticker_start_end.csv"),
    ("sp500_changes_since_2019.csv", "fja_changes_since_2019.csv"),
    ("sp500.csv", "fja_sp500_current.csv"),
]

APOS3 = "'" * 3


def _clean(cell: str) -> str:
    """Strip wiki markup from one table cell. No value invention."""
    s = re.sub(r"<ref[^>]*?/>", "", cell)
    s = re.sub(r"<ref.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{[Nn]yse[Ss]ymbol\|([^}|]+)\}\}", r"\1", s)
    s = re.sub(r"\{\{[^}]*\|([^}|]+)\}\}", r"\1", s)
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace(APOS3, "").replace("&amp;", "&").strip()


def parse_wiki_changes(text: str) -> pd.DataFrame:
    i = text.find("==Selected changes")
    if i < 0:
        return pd.DataFrame()
    seg = text[i:]
    seg = seg[: seg.find("\n|}", seg.find('id="changes"'))]
    rows = []
    for block in seg.split("\n|-")[1:]:
        line = block.strip()
        if not line or line.startswith("!"):
            continue
        line = line.split("\n")[0]
        cells = [_clean(c) for c in line.lstrip("|").split("||")]
        if len(cells) < 5:
            continue
        d = pd.to_datetime(cells[0], errors="coerce", format="mixed")
        if pd.isna(d):
            continue
        rows.append({"date": d.date().isoformat(), "added_ticker": cells[1],
                     "added_name": cells[2], "removed_ticker": cells[3],
                     "removed_name": cells[4],
                     "reason": (cells[5] if len(cells) > 5 else "")[:300]})
    return pd.DataFrame(rows)


def parse_wiki_current(text: str) -> pd.DataFrame:
    i = text.find('id="constituents"')
    if i < 0:
        return pd.DataFrame()
    seg = text[i: text.find("\n|}", i)]
    rows = []
    for block in seg.split("\n|-")[1:]:
        # A row spans two wikitext lines: "|{{NyseSymbol|MMM}}" then "|[[3M]]|| ... ".
        flat = block.strip().replace("\n|", "||")
        cells = [_clean(c) for c in flat.lstrip("|").split("||")]
        if len(cells) >= 6 and cells[0] and not cells[0].startswith("!"):
            rows.append({"ticker": cells[0], "security": cells[1], "sector": cells[2],
                         "sub_industry": cells[3], "hq": cells[4], "date_added": cells[5],
                         "cik": cells[6] if len(cells) > 6 else ""})
    return pd.DataFrame(rows)


SUFFIX = re.compile(r"-(19|20)\d{4}$")


def norm(tk: str):
    """fja05680 marks a ticker's index exit with a -YYYYMM suffix (AAMRQ-201312).

    Return (bare_ticker, exit_hint_YYYY-MM or "").  The suffix is kept as evidence
    for the survivorship accounting, not discarded.
    """
    t = str(tk).strip().upper()
    m = SUFFIX.search(t)
    if m:
        s = m.group(0)[1:]
        return t[: m.start()], s[:4] + "-" + s[4:]
    return t, ""


def build_universe(lo="2000-01-01", hi="2024-12-31") -> pd.DataFrame:
    """Every ticker in the index at any time in the window, per source and pooled."""
    memb: dict[str, dict] = {}

    def note(tk, src, d):
        tk, hint = norm(tk)
        if not tk or tk in {"NAN", "", "N/A", "NONE"}:
            return
        e = memb.setdefault(tk, {"ticker": tk, "sources": set(), "first": None,
                                 "last": None, "exit_hint": ""})
        e["sources"].add(src)
        if hint:
            e["exit_hint"] = hint
        if d:
            e["first"] = min(e["first"] or d, d)
            e["last"] = max(e["last"] or d, d)

    # Primary point-in-time file: the "(Updated)" one runs to 2026; the other
    # stops at 2019-01-11 and is kept only as a cross-check.
    for fn, src in [("fja_components_updated.csv", "fja_pit"),
                    ("fja_components_full.csv", "fja_pit_old")]:
        p = OUT / fn
        if p.exists():
            df = pd.read_csv(p)
            df = df[(df.iloc[:, 0] >= lo) & (df.iloc[:, 0] <= hi)]
            for d, tks in zip(df.iloc[:, 0], df.iloc[:, 1]):
                for t in str(tks).split(","):
                    note(t, src, d)

    p = OUT / "fja_ticker_start_end.csv"
    if p.exists():
        df = pd.read_csv(p, dtype=str).fillna("")
        for _, row in df.iterrows():
            s = row["start_date"] or "1900-01-01"
            e = row["end_date"] or "2100-01-01"
            if s <= hi and e >= lo:
                note(row["ticker"], "fja_range", max(s, lo))

    p = OUT / "hanshof_components.csv"
    if p.exists():
        df = pd.read_csv(p)
        df = df[(df.iloc[:, 0] >= lo) & (df.iloc[:, 0] <= hi)]
        for d, tks in zip(df.iloc[:, 0], df.iloc[:, 1]):
            for t in str(tks).split(","):
                note(t, "hanshof", d)

    p = OUT / "wikipedia_changes.csv"
    if p.exists():
        df = pd.read_csv(p, dtype=str).fillna("")
        for _, row in df.iterrows():
            if lo <= row["date"] <= hi:
                note(row["added_ticker"], "wiki_changes", row["date"])
                note(row["removed_ticker"], "wiki_changes", row["date"])

    p = OUT / "wikipedia_current_20250611.csv"
    if p.exists():
        df = pd.read_csv(p, dtype=str).fillna("")
        for _, row in df.iterrows():
            da = row.get("date_added", "")
            if da and da <= hi:
                note(row["ticker"], "wiki_current", max(da, lo))
            elif not da:
                note(row["ticker"], "wiki_current", None)

    uni = pd.DataFrame([{"ticker": v["ticker"], "first_seen": v["first"],
                         "last_seen": v["last"], "exit_hint": v["exit_hint"],
                         "n_sources": len(v["sources"]),
                         "sources": "|".join(sorted(v["sources"]))} for v in memb.values()])
    if len(uni):
        uni = uni.sort_values("ticker").reset_index(drop=True)
        uni.to_csv(OUT / "universe_2000_2024.csv", index=False)
        log_attempt(NEED, "universe(union)", "derived", "OK",
                    str(len(uni)) + " distinct tickers in index at any time " + lo + ".." + hi)
    return uni


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    for remote, local in FILES_A:
        url = FJA + "/" + remote.replace(" ", "%20").replace("&", "%26")
        r = get(url, need=NEED, source="fja05680/" + local)
        if r:
            save_bytes(r.content, OUT / local)

    r = get(HAN + "/sp_500_historical_components.csv", need=NEED, source="hanshof/components")
    if r:
        save_bytes(r.content, OUT / "hanshof_components.csv")

    r = get("https://en.wikipedia.org/w/index.php", need=NEED, source="wikipedia/oldid",
            params={"oldid": WIKI_OLDID, "action": "raw"})
    if r:
        save_bytes(r.content, OUT / ("wikipedia_oldid_%d.wikitext" % WIKI_OLDID))
        ch = parse_wiki_changes(r.text)
        if len(ch):
            ch.to_csv(OUT / "wikipedia_changes.csv", index=False)
            log_attempt(NEED, "wikipedia/changes-table", "parsed", "OK",
                        "%d add/remove rows %s..%s" % (len(ch), ch.date.min(), ch.date.max()))
        cur = parse_wiki_current(r.text)
        if len(cur):
            cur.to_csv(OUT / "wikipedia_current_20250611.csv", index=False)
            log_attempt(NEED, "wikipedia/current-table", "parsed", "OK", "%d rows" % len(cur))

    build_universe()
    write_attempts("02_constituents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
