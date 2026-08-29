"""Screen the retrieved price panel for ticker reuse (E1.0 quality step).

Yahoo serves whatever company holds a ticker TODAY.  Where an S&P 500 name was
delisted and its symbol was later reassigned, yfinance returns the *new* issuer's
history under the old ticker.  Verified examples: CPWR (Compuware -> Ocean
Thermal Energy), COMS (3Com -> COMSovereign), EP (El Paso -> Empire Petroleum),
CVG (Convergys -> a mutual fund share class).

This script flags suspects; it does not delete or alter any file.  The flags are
advisory input to Phase 1, which decides what to exclude.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, MANIFESTS, log_attempt, write_attempts  # noqa: E402

warnings.filterwarnings("ignore")

# Exchange codes that are OTC / pink-sheet venues: an S&P 500 constituent does not
# trade there, so a hit is strong evidence the symbol now belongs to someone else.
OTC_CODES = {"OID", "PNK", "OTC", "OBB", "OQB", "OQX", "PK"}


GRACE_DAYS = 180


def add_history_start_flag(out: pd.DataFrame) -> pd.DataFrame:
    """Flag a series that STARTS after its name left the index.

    A continuous history of one company cannot begin more than a few months after
    that company left the S&P 500, so this is near-conclusive evidence that the
    symbol was reassigned. It catches cases the Yahoo-metadata screen misses --
    e.g. GP: the index constituent was Georgia-Pacific (gone 2005), while Yahoo
    serves GreenPower Motor from 2020, listed on Nasdaq as an ordinary EQUITY with
    no other anomaly. Found independently by the need-#8 cross-check.

    Needs no network access: it reads dates already recorded.
    """
    path = MANIFESTS / "survivorship_accounting.csv"
    if not path.exists():
        return out
    sur = pd.read_csv(path).fillna("")
    sur = sur[sur.exit_hint != ""].copy()
    exit_d = pd.to_datetime(sur.exit_hint + "-01", errors="coerce")
    start_d = pd.to_datetime(sur["first"], errors="coerce")
    sur["gap_days"] = (start_d - exit_d).dt.days
    gap = dict(zip(sur.ticker.astype(str), sur.gap_days))

    new_flags, new_counts, gaps = [], [], []
    for _, r in out.iterrows():
        g = gap.get(str(r["ticker"]))
        fl = [f for f in str(r.get("flags", "")).split(";") if f]
        if g is not None and pd.notna(g) and g > GRACE_DAYS:
            fl.append("starts_%dd_after_index_exit" % int(g))
        new_flags.append(";".join(fl))
        new_counts.append(len(fl))
        gaps.append(int(g) if (g is not None and pd.notna(g)) else "")
    out = out.copy()
    out["flags"] = new_flags
    out["n_flags"] = new_counts
    out["days_start_after_exit"] = gaps
    return out


def recompute_flags() -> int:
    """Re-derive flags from the existing screen CSV without re-querying Yahoo."""
    p = MANIFESTS / "ticker_reuse_screen.csv"
    out = add_history_start_flag(pd.read_csv(p).fillna(""))
    out.to_csv(p, index=False)
    sus = out[out.n_flags > 0]
    print("flagged: %d of %d (%.1f%%)" % (len(sus), len(out), 100 * len(sus) / max(len(out), 1)))
    print(sus["flags"].str.split(";").explode().str.replace(
        r"\(.*\)|_\d+.*", "", regex=True).value_counts().to_string())
    return 0


def main(limit: int | None = None) -> int:
    import yfinance as yf

    log = pd.read_csv(DATASETS / "01_prices" / "retrieval_log.csv").fillna("")
    ok = log[log.status == "ok"].copy()
    if limit:
        ok = ok.head(limit)
    qual = pd.read_csv(MANIFESTS / "quality_prices.csv").set_index("ticker")

    # Query Yahoo with the SYMBOL yfinance actually used (BF.B -> BF-B), not the
    # universe ticker; querying the raw ticker returns another instrument's metadata.
    ysym = dict(zip(ok.ticker.astype(str), ok.yahoo_symbol.astype(str)))

    rows = []
    for i, t in enumerate(ok.ticker.astype(str)):
        name = qtype = exch = ""
        try:
            info = yf.Ticker(ysym.get(t, t)).info or {}
            name = str(info.get("longName") or info.get("shortName") or "")
            qtype = str(info.get("quoteType") or "")
            exch = str(info.get("exchange") or "")
        except Exception as e:
            qtype = "INFO_ERROR:" + type(e).__name__
        q = qual.loc[t] if t in qual.index else None
        maxret = float(q["max_abs_ret"]) if q is not None and pd.notna(q["max_abs_ret"]) else 0.0
        zerovol = int(q["zero_volume_days"]) if q is not None else 0
        nrows = int(q["n_rows"]) if q is not None else 0

        flags = []
        if qtype and qtype != "EQUITY":
            flags.append("not_equity(%s)" % qtype)
        if exch in OTC_CODES:
            flags.append("otc_venue(%s)" % exch)
        if maxret > 1.0:
            flags.append("max_daily_ret_%.0fx" % maxret)
        if nrows and zerovol / nrows > 0.25:
            flags.append("zero_volume_%.0f%%" % (100 * zerovol / nrows))
        rows.append({"ticker": t, "yahoo_name": name, "quote_type": qtype, "exchange": exch,
                     "n_rows": nrows, "max_abs_ret": maxret, "zero_volume_days": zerovol,
                     "n_flags": len(flags), "flags": ";".join(flags)})
        time.sleep(0.15)
        if (i + 1) % 100 == 0:
            pd.DataFrame(rows).to_csv(MANIFESTS / "ticker_reuse_screen.csv", index=False)
            print("  screened %d/%d" % (i + 1, len(ok)), flush=True)

    out = add_history_start_flag(pd.DataFrame(rows))
    out.to_csv(MANIFESTS / "ticker_reuse_screen.csv", index=False)
    sus = out[out.n_flags > 0]
    log_attempt("#1", "ticker-reuse-screen", "local", "OK",
                "%d/%d retrieved tickers carry >=1 reuse/integrity flag (%.1f%%)"
                % (len(sus), len(out), 100 * len(sus) / max(len(out), 1)))
    write_attempts("01_prices_screen")
    # NB: use out["flags"], not out.flags -- DataFrame.flags is a pandas attribute.
    print("\nflag counts:")
    print(sus["flags"].str.split(";").explode().str.replace(
        r"\(.*\)|_\d+.*", "", regex=True).value_counts().to_string())
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--recompute-flags":
        raise SystemExit(recompute_flags())
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
