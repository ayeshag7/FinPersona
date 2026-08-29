"""Record which data hosts are reachable from this machine, and how they fail.

Written so the E1.0 failures are evidence, not assertion.  Re-run this from any
machine to see whether the blocked sources have become available.

A host that resolves to 146.112.61.106 is being intercepted by this network's
Cisco Umbrella DNS filter, which serves a block page under a certificate that
does not match the requested host.  That is a local network policy and is NOT
worked around anywhere in these tools.
"""
from __future__ import annotations

import socket
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from common import MANIFESTS, UA, now  # noqa: E402

UMBRELLA_BLOCK = "146.112.61."

HOSTS = [
    # (need, host, a URL that would be fetched if it were reachable)
    ("#1", "query1.finance.yahoo.com", "https://query1.finance.yahoo.com/v8/finance/chart/AAPL"),
    ("#2", "raw.githubusercontent.com", "https://raw.githubusercontent.com/fja05680/sp500/master/sp500.csv"),
    ("#2", "en.wikipedia.org", "https://en.wikipedia.org/w/api.php?action=query&format=json"),
    ("#3", "data.sec.gov", "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"),
    ("#3", "www.sec.gov", "https://www.sec.gov/include/ticker.txt"),
    ("#3", "www.sec.gov", "https://www.sec.gov/files/company_tickers.json"),
    ("#4", "shillerdata.com", "https://shillerdata.com/"),
    ("#5", "cdn.cboe.com", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"),
    ("#5", "cdn.cboe.com", "https://cdn.cboe.com/api/global/us_indices/daily_prices/VXAPL_History.csv"),
    ("#5", "www.cboe.com", "https://www.cboe.com/"),
    ("#5", "fred.stlouisfed.org", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"),
    ("#6", "www.frbsf.org", "https://www.frbsf.org/wp-content/uploads/news_sentiment_data.xlsx"),
    ("#6", "www.aaii.com", "https://www.aaii.com/sentimentsurvey/sent_results"),
    ("#6", "pages.stern.nyu.edu", "https://pages.stern.nyu.edu/~jwurgler/data/SENTIMENT.xlsx"),
    ("#7", "mba.tuck.dartmouth.edu", "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"),
    ("#8", "stooq.com", "https://stooq.com/q/d/l/?s=aapl.us&i=d"),
    ("#8", "api.nasdaq.com", "https://api.nasdaq.com/api/quote/AAPL/historical"),
    ("#8", "www.nasdaqtrader.com", "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"),
    ("#8", "api.tiingo.com", "https://api.tiingo.com/tiingo/daily/aapl/prices"),
    ("#8", "eodhd.com", "https://eodhd.com/"),
    ("#8", "data.nasdaq.com", "https://data.nasdaq.com/"),
    ("#8", "finnhub.io", "https://finnhub.io/"),
    ("#8", "api.polygon.io", "https://api.polygon.io/"),
    ("#8", "www.alphavantage.co", "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo"),
    ("#8", "api.marketstack.com", "https://api.marketstack.com/v1/eod?symbols=AAPL"),
]


def main() -> int:
    rows = []
    for need, host, url in HOSTS:
        try:
            ips = sorted({ai[4][0] for ai in socket.getaddrinfo(host, 443, socket.AF_INET)})
        except Exception as e:
            ips = ["DNS_FAIL:" + type(e).__name__]
        blocked = any(str(i).startswith(UMBRELLA_BLOCK) for i in ips)
        status, detail = "", ""
        if blocked:
            status, detail = "DNS_FILTER_BLOCK", "resolves to the Umbrella block page; not circumvented"
        else:
            try:
                r = requests.get(url, headers={"User-Agent": UA}, timeout=30, stream=True)
                status = "HTTP_%d" % r.status_code
                detail = "%s bytes" % r.headers.get("Content-Length", "?")
                r.close()
            except Exception as e:
                status, detail = "REQUEST_FAIL", "%s: %s" % (type(e).__name__, str(e)[:120])
        rows.append({"utc": now(), "need": need, "host": host, "url": url,
                     "resolved_ips": ",".join(map(str, ips))[:80],
                     "status": status, "detail": detail})
        print("%-6s %-26s %-18s %s" % (need, host, status, detail[:60]), flush=True)

    df = pd.DataFrame(rows)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    df.to_csv(MANIFESTS / "reachability_probe.csv", index=False)
    nb = (df.status == "DNS_FILTER_BLOCK").sum()
    print("\n%d of %d probed endpoints are DNS-filter blocked on this machine." % (nb, len(df)))
    print("-> %s" % (MANIFESTS / "reachability_probe.csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
