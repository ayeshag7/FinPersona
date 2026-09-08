"""
v2.1 Phase 6 -- E6.1: empirical reference distributions for every checklist statistic.

Plan Section 10.2 (E6.1). Every non-overlapping 200-day window of every name in analysis set A, every
checklist statistic, P10/P50/P90 published per statistic and per sub-period, survivorship stated per item
(REG-15).

Three rules this module exists to honour:

  * **Like for like.** Every statistic is computed with the SAME function the audit applies to the
    generator (`evaluation.stylized_facts`), at the SAME horizon the benchmark runs (T = 200). E6.9 shows
    several of these estimators are biased at T = 200 (the Hill index at a 5 % tail depth misses a
    Student-t index by ~20 %; the sample ACF of a near-unit-root process is biased down). A criterion
    built by comparing generator windows with real windows measured the same way is immune to that bias;
    an absolute band is not. That is the argument for REG-14's B/C over A, and it only holds if the two
    sides use one estimator -- hence the import rather than a re-implementation.

  * **T = 200 is the criterion horizon.** "What the agent experiences" is 200 days, so the reference
    distribution is over 200-day windows, not over whole histories. Longer horizons are descriptive
    (plan 10.2 E6.3) and are not produced here.

  * **Survivorship is stated, not assumed away.** Set A is the flag-free names with a COMPLETE 2000-2024
    history in a `yfinance` panel: survivors by construction. REG-15 says the tails, the drawdowns and the
    loss frequencies are understated, and the size of the gap is a deliverable rather than an assumption.
    Every output carries the accounting (how many names were dropped, how many left the index) so that no
    percentile can be quoted without it.

Usage:
    python -u tools/phase6/e6_1_reference.py --out docs/env_v2/generated/v2_1/e6_1
    python -u tools/phase6/e6_1_reference.py --limit 5          # smoke run on five names
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from evaluation.stylized_facts import (  # noqa: E402
    acf, arch_lm_p, garch_fit, hill_index, ljung_box_p, mdd,
)
from tools.phase1.panel import DEFAULT as SPEC  # noqa: E402

OUT_DEFAULT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e6_1")
SETS_JSON = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_0_analysis_sets.json")
T_WINDOW = 200
ACF_LAGS = (1, 5, 10, 20, 50)


def window_stats(px: np.ndarray, vol: np.ndarray, with_garch: bool = True) -> Dict[str, float]:
    """Every checklist statistic that a real price/volume window can carry.

    `px` is the adjusted close over T_WINDOW + 1 days, so that len(r) == T_WINDOW.
    Statistics the generator defines on hidden state (x, phase, IV, sentiment) have no real-data
    counterpart and are absent by design -- they are named in the output's `not_in_reference` list.
    """
    r = np.diff(np.log(px))
    a = np.abs(r)
    out: Dict[str, float] = {}

    # item 1 -- no linear autocorrelation
    out["lb_p_r"] = ljung_box_p(r, 10)
    out["acf1_r"] = acf(r, 1)
    out["abs_acf1_r"] = abs(out["acf1_r"]) if out["acf1_r"] == out["acf1_r"] else np.nan

    # item 2 -- heavy tails
    out["kurtosis"] = float(stats.kurtosis(r))
    out["jb_p"] = float(stats.jarque_bera(r)[1])
    out["hill"] = hill_index(r)

    # item 3 -- volatility clustering
    out["lb_p_absr"] = ljung_box_p(a, 10)
    out["lb_p_r2"] = ljung_box_p(r ** 2, 10)
    out["arch_lm_p"] = arch_lm_p(r, 5)
    out["acf1_absr"] = acf(a, 1)

    # item 4 -- ACF|r| decay
    for L in ACF_LAGS:
        out[f"acf{L}_absr"] = acf(a, L)

    # items 5 and 6 -- GARCH persistence, leverage
    if with_garch:
        al, _, be = garch_fit(r)
        out["garch_alpha"], out["garch_beta"] = al, be
        out["garch_persistence"] = al + be if (al == al and be == be) else np.nan
        _, gam, _ = garch_fit(r, o=1)
        out["gjr_gamma"] = gam
    out["leverage_corr"] = float(np.corrcoef(r[:-1], a[1:])[0, 1])

    # item 7 -- volume / volatility
    v = np.asarray(vol[1:], float)          # align with r
    ok = np.isfinite(v) & (v > 0)
    if ok.sum() > 30:
        out["volume_absr_spearman"] = float(stats.spearmanr(v[ok], a[ok])[0])
        lv = np.log(v[ok])
        out["logvolume_acf1"] = acf(lv, 1)
        out["logvolume_shapiro_p"] = float(stats.shapiro(lv)[1]) if len(lv) <= 5000 else np.nan
    else:
        out["volume_absr_spearman"] = out["logvolume_acf1"] = out["logvolume_shapiro_p"] = np.nan

    # item 8 -- gain/loss asymmetry
    out["skew"] = float(stats.skew(r))
    out["worst_day"] = float(r.min())
    out["best_day"] = float(r.max())
    out["worst_over_best"] = float(abs(r.min()) / r.max()) if r.max() > 0 else np.nan

    # items 10 and 20 -- magnitudes
    out["mdd"] = mdd(px)
    out["daily_sigma"] = float(np.std(r, ddof=1))
    return out


# statistics the generator's checklist defines on hidden or synthetic state; there is no real-window
# counterpart, so no reference distribution can exist for them and none is invented.
NOT_IN_REFERENCE = {
    9: "mispricing persistence -- x is hidden state; no real-data counterpart",
    11: "bubble shape -- defined on the generator's P/V and phase labels",
    12: "sentiment dynamics -- the field is generated; item 12's b_pred is LIT (Phase 5 found the free "
        "sentiment source does not reproduce Tetlock's 8.1 bp), so the criterion tests fidelity to the "
        "configured value, not to the world (E6.8)",
    13: "IV realism -- handled from the index VIX/RV relation and the five single-stock IV histories, "
        "not from the price panel (separate E6.1 block)",
    15: "phase/time separability -- defined on generator phase labels",
    17: "conditioning / rejection rate -- a property of the sampler",
}


def ticker_windows(path: str, ticker: str, with_garch: bool = True, cache_dir: Optional[str] = None) -> List[Dict]:
    """One name's windows. With `cache_dir` the result is written as <cache_dir>/<ticker>.json and read back on
    a re-run, so a two-hour job survives a laptop sleep (rule 14: resumable and staged)."""
    cache = os.path.join(cache_dir, f"{ticker}.json") if cache_dir else None
    if cache and os.path.exists(cache):
        with open(cache, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
        if isinstance(rows, list) and rows:          # emptiness, not presence (P5-12)
            return rows
    rows = _ticker_windows(path, ticker, with_garch)
    if cache:
        os.makedirs(cache_dir, exist_ok=True)
        tmp = cache + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rows, fh)
        os.replace(tmp, cache)
    return rows


def _ticker_windows(path: str, ticker: str, with_garch: bool = True) -> List[Dict]:
    d = pd.read_parquet(path, columns=["Date", "Adj Close", "Volume"])
    d = d[(d["Date"] >= SPEC.start) & (d["Date"] <= SPEC.end)].reset_index(drop=True)
    d = d[np.isfinite(d["Adj Close"]) & (d["Adj Close"] > 0)].reset_index(drop=True)
    rows = []
    n_full = (len(d) - 1) // T_WINDOW
    for w in range(n_full):
        lo = w * T_WINDOW
        seg = d.iloc[lo:lo + T_WINDOW + 1]
        if len(seg) < T_WINDOW + 1:
            break
        try:
            s = window_stats(seg["Adj Close"].to_numpy(float), seg["Volume"].to_numpy(float), with_garch)
        except Exception as e:                                  # a window that cannot be measured is
            s = {"error": type(e).__name__}                     # recorded, never silently dropped
        s.update({"ticker": ticker, "window": w,
                  "start": str(seg["Date"].iloc[0].date()), "end": str(seg["Date"].iloc[-1].date()),
                  "mid": str(seg["Date"].iloc[len(seg) // 2].date())})
        rows.append(s)
    return rows


def assign_sub_period(mid: str) -> str:
    m = pd.Timestamp(mid)
    for name, lo, hi in SPEC.sub_periods:
        if pd.Timestamp(lo) <= m <= pd.Timestamp(hi):
            return name
    return "outside"


def summarise(df: pd.DataFrame, stat_cols: List[str]) -> pd.DataFrame:
    """P10/P50/P90 with the n each is computed on, overall and per sub-period.

    The n is carried per statistic, not per table: a statistic that is undefined on some windows (a
    GARCH fit that did not converge, a Shapiro test on a window with no volume) has a smaller n than its
    neighbours, and the rule of this programme is that numbers carry their n.
    """
    rows = []
    for scope, sub in [("all", df)] + [(p, df[df["sub_period"] == p]) for p in
                                       sorted(df["sub_period"].unique())]:
        for c in stat_cols:
            v = pd.to_numeric(sub[c], errors="coerce").to_numpy(float)
            v = v[np.isfinite(v)]
            if v.size == 0:
                rows.append({"scope": scope, "statistic": c, "n": 0})
                continue
            rows.append({"scope": scope, "statistic": c, "n": int(v.size),
                         "p10": float(np.percentile(v, 10)), "p25": float(np.percentile(v, 25)),
                         "p50": float(np.percentile(v, 50)), "p75": float(np.percentile(v, 75)),
                         "p90": float(np.percentile(v, 90)),
                         "mean": float(v.mean()), "sd": float(v.std(ddof=1)) if v.size > 1 else np.nan,
                         "n_windows_scope": int(len(sub))})
    return pd.DataFrame(rows)


def survivorship_block() -> Dict:
    """REG-15's accounting, read from the E1.0 outputs -- never restated from memory."""
    with open(SETS_JSON, "r", encoding="utf-8") as fh:
        s = json.load(fh)
    return {
        "analysis_set": "A (flag-free names with a complete 2000-01-03..2024-12-31 history)",
        "n_A": s["n_A"], "n_B": s["n_B"], "n_price_files": s["n_files"],
        "n_flagged_out": s["n_flagged"], "n_duplicate_spellings": s["n_duplicates"],
        "A_left_index": s["A_left_index"],
        "source": s["spec"]["source_note"],
        "caveat": (
            "Set A is survivor-biased by construction: a name qualifies only by having a complete "
            "2000-2024 history in a yfinance panel, so firms that were delisted, acquired or went to "
            "zero are absent. REG-15's reading is that the tails, the drawdowns and the loss "
            "frequencies of this reference distribution are UNDERSTATED. Every percentile below "
            "inherits that bias. It bites hardest on the items that are about disaster -- MDD (item "
            "10/20), the worst day, the Hill index and the kurtosis (item 2) -- and least on the "
            "items about ordinary dynamics (ACF, GARCH persistence, volume-volatility). A generator "
            "whose crash windows are deeper than this reference's P90 is not thereby unrealistic; the "
            "comparison has to be read with the literature's full-universe values beside it, which is "
            "why they are carried in the report rather than left to the reader."),
        "sets_json": os.path.relpath(SETS_JSON, ROOT).replace("\\", "/"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--limit", type=int, default=None, help="use only the first N names (smoke runs)")
    ap.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    ap.add_argument("--no-garch", action="store_true", help="skip the two arch fits per window")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)

    with open(SETS_JSON, "r", encoding="utf-8") as fh:
        sets = json.load(fh)
    tickers = sets["A"][: a.limit] if a.limit else sets["A"]
    print(f"set A: {len(sets['A'])} names; running {len(tickers)}", flush=True)

    from joblib import Parallel, delayed
    from threadpoolctl import threadpool_limits

    t0 = time.time()
    with threadpool_limits(limits=2):
        cache_dir = os.path.join(a.out, "cache")
        chunks = Parallel(n_jobs=a.n_jobs, backend="loky", verbose=5)(
            delayed(ticker_windows)(SPEC.path(SPEC.price_dir, f"{t}.parquet"), t, not a.no_garch, cache_dir)
            for t in tickers)
    rows = [r for c in chunks for r in c]
    df = pd.DataFrame(rows)
    df["sub_period"] = df["mid"].map(assign_sub_period)
    secs = time.time() - t0
    print(f"{len(df)} windows from {len(tickers)} names in {secs:.0f}s", flush=True)

    meta_cols = {"ticker", "window", "start", "end", "mid", "sub_period", "error"}
    stat_cols = [c for c in df.columns if c not in meta_cols]
    summ = summarise(df, stat_cols)

    df.to_csv(os.path.join(a.out, "windows.csv"), index=False)
    summ.to_csv(os.path.join(a.out, "reference_percentiles.csv"), index=False)

    meta = {
        "T_window": T_WINDOW, "n_names": len(tickers), "n_windows": int(len(df)),
        "n_errors": int(df["error"].notna().sum()) if "error" in df.columns else 0,
        "windows_per_name": {"min": int(df.groupby("ticker")["window"].count().min()),
                             "median": float(df.groupby("ticker")["window"].count().median()),
                             "max": int(df.groupby("ticker")["window"].count().max())},
        "sub_periods": {n: int((df["sub_period"] == n).sum()) for n in df["sub_period"].unique()},
        "panel_spec": SPEC.to_dict(),
        "survivorship": survivorship_block(),
        "not_in_reference": NOT_IN_REFERENCE,
        "estimators": "evaluation.stylized_facts (the audit's own functions), imported not re-implemented",
        "seconds": round(secs, 1),
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "numpy": np.__version__, "pandas": pd.__version__,
    }
    with open(os.path.join(a.out, "reference.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "percentiles": summ.to_dict(orient="records")}, fh, indent=1)
    print(json.dumps({k: meta[k] for k in
                      ("n_names", "n_windows", "n_errors", "windows_per_name", "sub_periods")}, indent=1))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
