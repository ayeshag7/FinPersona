"""Need #5: CBOE volatility index histories, including the five SINGLE-STOCK VIX indices.

On the first E1.0 run (29 Aug 2026, earlier in the day) every cboe.com host resolved to
146.112.61.106 -- this network's Cisco Umbrella DNS block page -- and nothing could be
fetched.  That filter was later lifted and the files served normally, so this script
exists to take the data properly.  Nothing was circumvented; the network changed.

CBOE publishes these as free daily CSVs.  They are index levels for reference/research;
CBOE's terms permit personal and internal research use, not redistribution, so the files
stay under the git-ignored datasets/ tree like the rest of the panel.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, get, log_attempt, save_bytes, write_attempts  # noqa: E402

OUT = DATASETS / "05_implied_vol" / "cboe"
NEED = "#5"
URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/%s_History.csv"

# The five single-stock VIX indices the plan names, first.
SINGLE_STOCK = ["VXAPL", "VXAZN", "VXGOG", "VXGS", "VXIBM"]
# Broad index IV, the VIX term structure, and the ETF/sector vol indices.
INDEX_VOL = ["VIX", "VXN", "VXO", "VXD", "RVX", "VVIX", "SKEW"]
TERM = ["VIX9D", "VIX3M", "VIX6M"]
ETF_VOL = ["VXEEM", "VXEWZ", "VXSLV", "VXGDX", "VXXLE", "VXTLT", "GVZ", "OVX", "VPD", "VPN"]

GROUPS = [("single_stock", SINGLE_STOCK), ("index", INDEX_VOL),
          ("term_structure", TERM), ("etf_sector", ETF_VOL)]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for group, symbols in GROUPS:
        for s in symbols:
            r = get(URL % s, need=NEED, source="cboe/" + s, tries=3, timeout=60)
            if not r or len(r.content) < 2000:
                rows.append({"symbol": s, "group": group, "status": "not_served",
                             "n_rows": 0, "first": "", "last": ""})
                continue
            save_bytes(r.content, OUT / ("%s_History.csv" % s))
            try:
                df = pd.read_csv(io.StringIO(r.text))
                # CBOE writes DATE as MM/DD/YYYY; parse but keep the served values.
                df["DATE"] = pd.to_datetime(df["DATE"], format="%m/%d/%Y", errors="coerce")
                df = df.dropna(subset=["DATE"])
                df.to_parquet(OUT / ("%s.parquet" % s), index=False)
                rows.append({"symbol": s, "group": group, "status": "ok", "n_rows": len(df),
                             "first": str(df.DATE.min())[:10], "last": str(df.DATE.max())[:10]})
            except Exception as e:
                rows.append({"symbol": s, "group": group, "status": "parse_error",
                             "n_rows": 0, "first": "", "last": type(e).__name__})

    log = pd.DataFrame(rows)
    log.to_csv(OUT / "retrieval_log.csv", index=False)
    ok = log[log.status == "ok"]
    ss = ok[ok.group == "single_stock"]
    log_attempt(NEED, "cboe/all", "https://cdn.cboe.com", "OK",
                "%d/%d index files, including %d/5 single-stock VIX"
                % (len(ok), len(log), len(ss)))
    print("\n" + log.to_string(index=False))
    write_attempts("05_cboe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
