"""Cross-check need #1 (Yahoo) against need #8 (Nasdaq) on overlapping dates.

Both sources give split-adjusted, NOT dividend-adjusted closes, so `Close` is the
comparable field -- not Yahoo's `Adj Close`.

Output: datasets/_manifests/source_agreement.csv, one row per ticker, plus a summary.
A ticker where the two disagree badly is either a corporate-action handling difference
or -- more interestingly -- corroboration that Yahoo is serving a different company
under a reused symbol (need #1, section 1.3).
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import DATASETS, MANIFESTS  # noqa: E402

warnings.filterwarnings("ignore")

YH = DATASETS / "01_prices" / "daily"
ND = DATASETS / "08_price_crosscheck" / "daily"
TOL = 0.005  # 0.5 % relative difference counts as agreement


def main() -> int:
    rows = []
    for p in sorted(ND.glob("*.parquet")):
        t = p.stem
        q = YH / ("%s.parquet" % t)
        if not q.exists():
            continue
        a = pd.read_parquet(q)[["Date", "Close"]].rename(columns={"Close": "yahoo"})
        b = pd.read_parquet(p)[["Date", "Close"]].rename(columns={"Close": "nasdaq"})
        a["Date"] = pd.to_datetime(a["Date"]).dt.normalize()
        b["Date"] = pd.to_datetime(b["Date"]).dt.normalize()
        m = a.merge(b, on="Date", how="inner").dropna()
        m = m[(m.yahoo > 0) & (m.nasdaq > 0)]
        if len(m) < 30:
            rows.append({"ticker": t, "n_overlap": len(m), "status": "too_few_overlap"})
            continue
        rel = (m.yahoo - m.nasdaq).abs() / m.nasdaq

        # Levels can differ by a constant factor when the two sources apply a split
        # retroactively at different times. Daily RETURNS are invariant to that, so
        # they are the real test of whether both series describe the same security.
        m = m.sort_values("Date")
        ry = m.yahoo / m.yahoo.shift(1) - 1
        rn = m.nasdaq / m.nasdaq.shift(1) - 1
        ok = ry.notna() & rn.notna() & np.isfinite(ry) & np.isfinite(rn)
        ry, rn = ry[ok], rn[ok]
        dret = (ry - rn).abs()

        rows.append({
            "ticker": t, "n_overlap": len(m), "status": "compared",
            "first": str(m.Date.min())[:10], "last": str(m.Date.max())[:10],
            # return-based (headline)
            "ret_corr": round(float(ry.corr(rn)), 6) if len(ry) > 2 else np.nan,
            "pct_ret_within_10bp": round(100 * float((dret <= 0.001).mean()), 2) if len(ry) else np.nan,
            "median_abs_ret_diff": round(float(dret.median()), 6) if len(ry) else np.nan,
            # level-based (diagnostic; sensitive to split-adjustment convention)
            "pct_within_0.5pct": round(100 * float((rel <= TOL).mean()), 2),
            "median_rel_diff": round(float(rel.median()), 6),
            "max_rel_diff": round(float(rel.max()), 4),
            "corr": round(float(m.yahoo.corr(m.nasdaq)), 6),
        })

    df = pd.DataFrame(rows)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    df.to_csv(MANIFESTS / "source_agreement.csv", index=False)

    c = df[df.status == "compared"]
    print("tickers compared            : %d" % len(c))
    print("total overlapping day-pairs : {:,}".format(int(c.n_overlap.sum())))
    if len(c):
        print("\n-- RETURN agreement (split-adjustment invariant; the real test) --")
        print("median per-ticker return correlation      : %.6f" % c.ret_corr.median())
        print("median per-ticker %% of days within 10 bp  : %.2f %%"
              % c.pct_ret_within_10bp.median())
        for thr in [0.999, 0.99, 0.95, 0.90]:
            n = int((c.ret_corr >= thr).sum())
            print("  tickers with return corr >= %.3f : %3d  (%.1f %%)"
                  % (thr, n, 100 * n / len(c)))

        print("\n-- LEVEL agreement (diagnostic: differs when a split is applied "
              "retroactively by only one source) --")
        print("median per-ticker %%-within-0.5%%: %.2f %%" % c["pct_within_0.5pct"].median())

        bad = c[c.ret_corr < 0.90].sort_values("ret_corr")
        print("\ntickers whose RETURNS disagree (corr < 0.90): %d" % len(bad))
        if len(bad):
            print(bad[["ticker", "n_overlap", "ret_corr", "pct_ret_within_10bp",
                       "median_rel_diff", "corr"]].head(25).to_string(index=False))
    print("\n-> %s" % (MANIFESTS / "source_agreement.csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
