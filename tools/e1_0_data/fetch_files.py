"""Needs #4, #5, #6, #7: file-served sources (Shiller, implied vol, sentiment, factors).

Each source is downloaded in the format its publisher serves and, where that is
Excel, also parsed to CSV so the panel is readable without Excel.  Parsing never
fills, interpolates or drops values; it only reshapes.

Blocked on this machine (recorded, not worked around) -- see E1_0_DATA_REPORT.md:
  * cboe.com / cdn.cboe.com  -> corporate DNS filter (Cisco Umbrella block page)
  * aaii.com                 -> corporate DNS filter
  * stooq.com                -> corporate DNS filter (and blocks scripts anyway)
  * fred.stlouisfed.org      -> resolves, but every request times out
"""
from __future__ import annotations

import io
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, get, log_attempt, save_bytes, write_attempts  # noqa: E402

warnings.filterwarnings("ignore")

SHILLER = ("https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/"
           "downloads/e27e58c1-8ae0-488c-a976-a298708c7175/ie_data.xls")
FF = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
DAM = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/"
BW = "https://pages.stern.nyu.edu/~jwurgler/data/"

# Yahoo volatility indices that stand in for the DNS-blocked CBOE files.
VOL_INDICES = ["^VIX", "^VXN", "^GVZ", "^OVX", "^VXO", "^VVIX"]
# The five CBOE single-stock VIX indices the plan names (CBOE is the only source).
SINGLE_STOCK_VIX = ["^VXAPL", "^VXAZN", "^VXGOG", "^VXGS", "^VXIBM"]


# ---------------------------------------------------------------- #4 Shiller
def need4() -> None:
    out = DATASETS / "04_shiller"
    out.mkdir(parents=True, exist_ok=True)
    r = get(SHILLER, need="#4", source="shillerdata.com/ie_data.xls")
    if not r:
        return
    save_bytes(r.content, out / "ie_data.xls")
    try:
        xl = pd.ExcelFile(io.BytesIO(r.content))
        log_attempt("#4", "shiller/sheets", "parsed", "OK", ", ".join(xl.sheet_names))
        df = xl.parse("Data", skiprows=7)
        df = df[pd.to_numeric(df.iloc[:, 0], errors="coerce").notna()]
        df.to_csv(out / "shiller_monthly.csv", index=False)
        log_attempt("#4", "shiller/Data", "parsed", "OK",
                    "%d rows, Date %s..%s, %d cols" % (len(df), df.iloc[0, 0], df.iloc[-1, 0],
                                                       df.shape[1]))
    except Exception as e:
        log_attempt("#4", "shiller/parse", "parsed", "FAIL", "%s: %s" % (type(e).__name__, e))

    # Independent transcription of the same Shiller series (datahub.io, PDDL) --
    # a cross-check on the parse above, NOT an independent measurement.
    r = get("https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv",
            need="#4", source="datahub/s-and-p-500 (Shiller-derived)")
    if r:
        save_bytes(r.content, out / "datahub_sp500_shiller_crosscheck.csv")


# ------------------------------------------------------------ #5 implied vol
def need5() -> None:
    import yfinance as yf

    out = DATASETS / "05_implied_vol"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for t in VOL_INDICES + SINGLE_STOCK_VIX:
        try:
            d = yf.Ticker(t).history(period="max", auto_adjust=False)
        except Exception as e:
            log_attempt("#5", "yahoo/" + t, "https://finance.yahoo.com", "FAIL", type(e).__name__)
            rows.append({"index": t, "status": "error", "n_rows": 0, "first": "", "last": ""})
            continue
        # Fewer than ~100 rows means Yahoo has a symbol stub but no usable history.
        if d is None or len(d) < 100:
            n = 0 if d is None else len(d)
            log_attempt("#5", "yahoo/" + t, "https://finance.yahoo.com", "FAIL",
                        "no usable history served (%d rows); Yahoo does not carry this index" % n)
            rows.append({"index": t, "status": "not_served", "n_rows": n, "first": "", "last": ""})
            continue
        d = d.reset_index()
        d["Date"] = pd.to_datetime(d["Date"]).dt.tz_localize(None)
        name = t.lstrip("^")
        d.to_csv(out / ("%s.csv" % name), index=False)
        rows.append({"index": t, "status": "ok", "n_rows": len(d),
                     "first": str(d.Date.iloc[0])[:10], "last": str(d.Date.iloc[-1])[:10]})
        log_attempt("#5", "yahoo/" + t, "https://finance.yahoo.com", "OK",
                    "%d rows %s..%s" % (len(d), str(d.Date.iloc[0])[:10], str(d.Date.iloc[-1])[:10]))
    pd.DataFrame(rows).to_csv(out / "retrieval_log.csv", index=False)
    need5_fred(out)


# FRED series worth having when the host is responding: VIXCLS is the official
# index-IV series the plan wanted, VXOCLS reaches back to 1986, and the rate
# series serve need #7. No API key is used -- these are the public no-key CSVs.
FRED_SERIES = ["VIXCLS", "VXNCLS", "VXOCLS", "DGS3MO", "DGS10", "DFF", "SP500"]


def need5_fred(out: Path) -> None:
    """FRED is intermittent from this network: it timed out on every request in one
    window on 29 Aug 2026 and served normally an hour later. Failures are logged and
    the run continues -- re-run to pick up whatever was missed."""
    d = out / "fred"
    d.mkdir(parents=True, exist_ok=True)
    for sid in FRED_SERIES:
        r = get("https://fred.stlouisfed.org/graph/fredgraph.csv", need="#5/#7",
                source="fred/" + sid, params={"id": sid}, tries=3, timeout=45)
        if r and len(r.content) > 200:
            save_bytes(r.content, d / ("%s.csv" % sid))


# -------------------------------------------------------------- #6 sentiment
def need6() -> None:
    out = DATASETS / "06_sentiment"
    out.mkdir(parents=True, exist_ok=True)

    # (a) SF Fed Daily News Sentiment Index (Shapiro, Sudhof & Wilson 2022)
    r = get("https://www.frbsf.org/wp-content/uploads/news_sentiment_data.xlsx",
            need="#6", source="frbsf/news_sentiment")
    if r:
        save_bytes(r.content, out / "sf_fed_news_sentiment.xlsx")
        try:
            xl = pd.ExcelFile(io.BytesIO(r.content))
            # The workbook carries a "Methodology" sheet first; the series is on "Data".
            sheet = next((s for s in xl.sheet_names if s.strip().lower() == "data"),
                         xl.sheet_names[-1])
            df = xl.parse(sheet)
            df.to_csv(out / "sf_fed_news_sentiment.csv", index=False)
            log_attempt("#6", "sffed/parse", "parsed", "OK",
                        "sheet=%s %d rows %s..%s cols=%s" % (
                            sheet, len(df), str(df.iloc[0, 0])[:10], str(df.iloc[-1, 0])[:10],
                            list(df.columns)[:4]))
        except Exception as e:
            log_attempt("#6", "sffed/parse", "parsed", "FAIL", str(e)[:120])

    # (b) Baker-Wurgler monthly investor sentiment
    for fn in ["Investor_Sentiment_Data_v23_POST.xlsx", "SENTIMENT.xlsx"]:
        r = get(BW + fn, need="#6", source="baker-wurgler/" + fn)
        if r:
            save_bytes(r.content, out / fn)
            try:
                xl = pd.ExcelFile(io.BytesIO(r.content))
                for sh in xl.sheet_names:
                    df = xl.parse(sh)
                    if len(df) > 10:
                        df.to_csv(out / ("bw_%s_%s.csv" % (fn.split(".")[0][:18], sh))[:120],
                                  index=False)
                log_attempt("#6", "bw/parse " + fn, "parsed", "OK", ", ".join(xl.sheet_names))
            except Exception as e:
                log_attempt("#6", "bw/parse " + fn, "parsed", "FAIL", str(e)[:120])

    # (c) AAII weekly survey -- DNS-blocked on this machine, recorded as a failure.
    get("https://www.aaii.com/sentimentsurvey/sent_results", need="#6",
        source="aaii/weekly-survey", tries=1, timeout=20)


# ---------------------------------------------------- #7 factors and valuation
def need7() -> None:
    out = DATASETS / "07_factors_valuation"
    out.mkdir(parents=True, exist_ok=True)

    for fn in ["F-F_Research_Data_Factors_daily_CSV.zip",
               "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
               "F-F_Momentum_Factor_daily_CSV.zip",
               "F-F_Research_Data_Factors_CSV.zip",
               "49_Industry_Portfolios_daily_CSV.zip"]:
        r = get(FF + fn, need="#7", source="french/" + fn)
        if r:
            save_bytes(r.content, out / fn)

    for fn in ["pedata.xls", "divfund.xls", "histretSP.xls", "betas.xls",
               "wacc.xls", "pbvdata.xls"]:
        r = get(DAM + fn, need="#7", source="damodaran/" + fn)
        if r:
            save_bytes(r.content, out / fn)


def main() -> int:
    need4()
    need5()
    need6()
    need7()
    write_attempts("files_4_5_6_7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
