"""
v2.1 Phase 6 -- E6.1 (IV block): the empirical reference for item 13 (IV realism) from real implied-volatility
histories, on 200-day windows, with the checklist's own constructions.

Plan Section 10.2 (E6.1): "for IV items -- the VIX/RV relations at index level and the single-stock IV where
available".  Item 13 (`evaluation.stylized_facts.item13_iv`) reads, per path: the mean IV in calm days, the mean
IV in panic days, corr(IV_t, RV_{t+1..t+20}) with RV the next-20-day realised sd annualised in percent, and the
mean IV - RV gap in calm and in panic.  Real data have no phase labels, so the reference reports the same
quantities on every non-overlapping 200-day window, unconditionally and by the window's realised-volatility
tercile (the lowest tercile is the closest real analogue of "calm", the highest of "panic"; that mapping is a
DESIGN choice and is recorded as such).

Three pairs of (IV, price) series:

  index / FRED      VIX (CBOE, cboe/VIX.parquet CLOSE) against the S&P 500 (fred/SP500.csv), the exact pair the
                    VIX is defined on; FRED serves ten years (2016-2026), so n is small and is stated
  index / set-A EW  VIX against an equal-weighted index of analysis set A's daily returns (2000-2024): a
                    large-cap proxy for the S&P 500 whose realised vol is close to, not identical with, the
                    cap-weighted index's -- reported beside the exact pair with the caveat
  single stocks     the five CBOE single-stock VIX indices (VXAPL, VXAZN, VXGOG, VXGS, VXIBM; 2011-2026) against
                    their own stocks' adjusted closes (AAPL, AMZN, GOOG, GS, IBM)

Every statistic is computed by the same code path the checklist uses (`rv20` = std of the next 20 log returns
* sqrt(252) * 100; corr over days where both are defined).  Survivorship: the single stocks are five surviving
mega-caps chosen by the CBOE; the index pairs carry no survivorship in the IV series but the set-A proxy does.

Usage:
    python -u tools/phase6/e6_1_iv.py --out docs/env_v2/generated/v2_1/e6_1
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.phase1.panel import DEFAULT as SPEC, load_prices  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT_DEFAULT = os.path.join(GEN, "e6_1")
SETS_JSON = os.path.join(GEN, "e1_0_analysis_sets.json")
IV_DIR = os.path.join(SPEC.root, "05_implied_vol")
T_WINDOW = 200
SINGLE = {"VXAPL": "AAPL", "VXAZN": "AMZN", "VXGOG": "GOOG", "VXGS": "GS", "VXIBM": "IBM"}


def _iv_series(symbol: str) -> pd.Series:
    d = pd.read_parquet(os.path.join(IV_DIR, "cboe", f"{symbol}.parquet"))
    s = d.set_index(pd.to_datetime(d["DATE"]))["CLOSE"].astype(float)
    return s[s > 0].sort_index()


def _price_series(ticker: str) -> pd.Series:
    d = pd.read_parquet(os.path.join(SPEC.root, SPEC.price_dir, f"{ticker}.parquet"), columns=["Date", "Adj Close"])
    return d.set_index(pd.to_datetime(d["Date"]))["Adj Close"].astype(float).sort_index()


def _fred_sp500() -> pd.Series:
    d = pd.read_csv(os.path.join(IV_DIR, "fred", "SP500.csv"))
    d = d.rename(columns={d.columns[0]: "date", d.columns[1]: "px"})
    d["px"] = pd.to_numeric(d["px"], errors="coerce")
    d = d.dropna()
    return d.set_index(pd.to_datetime(d["date"]))["px"].sort_index()


def _ff_market_index() -> pd.Series:
    """The value-weighted US market (Fama-French daily factors: Mkt-RF + RF, percent per day) as a price index.
    Ken French's library, `07_factors_valuation/F-F_Research_Data_Factors_daily_CSV.zip`; no survivorship (the
    CRSP universe including delistings)."""
    import io
    import zipfile
    p = os.path.join(SPEC.root, "07_factors_valuation", "F-F_Research_Data_Factors_daily_CSV.zip")
    with zipfile.ZipFile(p) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        txt = z.read(name).decode("utf-8", errors="replace")
    rows = []
    for line in io.StringIO(txt):
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 5 and len(parts[0]) == 8 and parts[0].isdigit():
            try:
                rows.append((parts[0], float(parts[1]), float(parts[4])))
            except ValueError:
                continue
    d = pd.DataFrame(rows, columns=["date", "mkt_rf", "rf"])
    d["date"] = pd.to_datetime(d["date"], format="%Y%m%d")
    r = (d["mkt_rf"] + d["rf"]) / 100.0                       # simple daily return of the market
    px = (1.0 + r).cumprod() * 100.0
    return pd.Series(px.to_numpy(), index=d["date"]).sort_index()


def _setA_ew_index() -> pd.Series:
    with open(SETS_JSON, "r", encoding="utf-8") as fh:
        A = json.load(fh)["A"]
    px = load_prices(A)
    r = np.log(px).diff()
    ew = r.mean(axis=1, skipna=True)                  # equal-weighted daily log return (names present that day)
    return np.exp(ew.fillna(0.0).cumsum()) * 100.0


def window_iv_stats(iv: np.ndarray, px: np.ndarray) -> Dict[str, float]:
    """item13_iv's per-path quantities on one window of aligned (IV, price): rv20 is the std of the NEXT 20 log
    returns annualised in percent; corr over days where both are defined; the gap is IV - rv20."""
    r = np.concatenate([[np.nan], np.diff(np.log(px))])
    n = len(r)
    rv = np.array([np.std(r[i + 1:i + 21]) * np.sqrt(252) * 100 if i + 21 <= n else np.nan for i in range(n)])
    ok = np.isfinite(rv) & np.isfinite(iv)
    out = {"iv_mean": float(np.nanmean(iv)), "iv_p10": float(np.nanpercentile(iv, 10)), "iv_p90": float(np.nanpercentile(iv, 90)),
           "rv20_mean": float(np.nanmean(rv[ok])) if ok.sum() else np.nan,
           "realised_sigma_annual_pct": float(np.nanstd(r[1:], ddof=1) * np.sqrt(252) * 100),
           "iv_rv20_corr": float(np.corrcoef(iv[ok], rv[ok])[0, 1]) if ok.sum() > 30 and np.std(iv[ok]) > 0 else np.nan,
           "iv_minus_rv20_mean": float(np.mean(iv[ok] - rv[ok])) if ok.sum() else np.nan,
           "iv_acf1": float(np.corrcoef(iv[:-1], iv[1:])[0, 1]) if np.std(iv) > 0 else np.nan,
           "n_days": int(n), "n_pairs": int(ok.sum())}
    # the first-panic-day style jump statistic the audit watches (weakness 46): the largest one-day log change of IV
    dl = np.diff(np.log(iv))
    out["max_abs_dlog_iv"] = float(np.nanmax(np.abs(dl))) if len(dl) else np.nan
    return out


def windows_for_pair(iv: pd.Series, px: pd.Series, label: str) -> List[Dict]:
    j = pd.concat([iv.rename("iv"), px.rename("px")], axis=1).dropna()
    j = j[(j.index >= pd.Timestamp("2000-01-03"))]
    rows = []
    n_full = len(j) // T_WINDOW
    for w in range(n_full):
        seg = j.iloc[w * T_WINDOW:(w + 1) * T_WINDOW]
        s = window_iv_stats(seg["iv"].to_numpy(float), seg["px"].to_numpy(float))
        s.update({"pair": label, "window": w, "start": str(seg.index[0].date()), "end": str(seg.index[-1].date()),
                  "mid": str(seg.index[len(seg) // 2].date())})
        rows.append(s)
    return rows


def summarise(df: pd.DataFrame) -> Dict:
    cols = ["iv_mean", "rv20_mean", "realised_sigma_annual_pct", "iv_rv20_corr", "iv_minus_rv20_mean", "iv_acf1", "max_abs_dlog_iv"]
    out = {}
    for pair, g in df.groupby("pair"):
        blk = {"n_windows": int(len(g)), "unconditional": {}, "by_rv_tercile": {}}
        for c in cols:
            v = pd.to_numeric(g[c], errors="coerce").to_numpy(float); v = v[np.isfinite(v)]
            blk["unconditional"][c] = {"n": int(v.size), "p10": float(np.percentile(v, 10)), "p50": float(np.percentile(v, 50)),
                                       "p90": float(np.percentile(v, 90))} if v.size else {"n": 0}
        # terciles of the window's realised vol: lowest ~ "calm", highest ~ "panic" (DESIGN; the mapping is stated)
        q = g["realised_sigma_annual_pct"].quantile([1 / 3, 2 / 3]).to_numpy()
        terc = np.where(g["realised_sigma_annual_pct"] <= q[0], "low", np.where(g["realised_sigma_annual_pct"] <= q[1], "mid", "high"))
        for t in ("low", "mid", "high"):
            gg = g[terc == t]
            blk["by_rv_tercile"][t] = {"n": int(len(gg))}
            for c in ("iv_mean", "rv20_mean", "iv_minus_rv20_mean", "iv_rv20_corr"):
                v = pd.to_numeric(gg[c], errors="coerce").to_numpy(float); v = v[np.isfinite(v)]
                blk["by_rv_tercile"][t][c] = {"p10": float(np.percentile(v, 10)), "p50": float(np.percentile(v, 50)),
                                              "p90": float(np.percentile(v, 90))} if v.size else None
        out[pair] = blk
    # pooled single stocks
    ss = df[df["pair"].str.startswith("single:")]
    if len(ss):
        blk = {"n_windows": int(len(ss)), "unconditional": {}}
        for c in cols:
            v = pd.to_numeric(ss[c], errors="coerce").to_numpy(float); v = v[np.isfinite(v)]
            blk["unconditional"][c] = {"n": int(v.size), "p10": float(np.percentile(v, 10)), "p50": float(np.percentile(v, 50)),
                                       "p90": float(np.percentile(v, 90))} if v.size else {"n": 0}
        out["single:pooled"] = blk
    return out


def to_markdown(summ: Dict, meta: Dict) -> str:
    L = ["# E6.1 (IV block) — the item-13 reference from real implied-volatility histories", "",
         f"200-day windows; `item13_iv`'s constructions (rv20 = next-20-day realised sd, annualised %, corr over defined days). "
         f"Generated {meta['generated_utc']}. **Survivorship / representativeness:** {meta['caveat']}", "",
         "| pair | n windows | IV mean P10/P50/P90 | RV20 mean P50 | realised σ (ann. %) P50 | corr(IV, next-20d RV) P10/P50/P90 | IV−RV20 P10/P50/P90 | IV ACF(1) P50 | max |Δlog IV| P50 |",
         "|---|---|---|---|---|---|---|---|---|"]
    def p(b, k, f="{:.2f}"):
        x = b.get(k) or {}
        return "—" if not x or x.get("n", 1) == 0 else f"{f.format(x['p10'])} / {f.format(x['p50'])} / {f.format(x['p90'])}"
    def p50(b, k, f="{:.2f}"):
        x = b.get(k) or {}
        return "—" if not x or x.get("n", 1) == 0 else f.format(x["p50"])
    for pair, b in summ.items():
        u = b["unconditional"]
        L.append(f"| {pair} | {b['n_windows']} | {p(u, 'iv_mean')} | {p50(u, 'rv20_mean')} | {p50(u, 'realised_sigma_annual_pct')} | "
                 f"{p(u, 'iv_rv20_corr')} | {p(u, 'iv_minus_rv20_mean', '{:+.2f}')} | {p50(u, 'iv_acf1', '{:.3f}')} | {p50(u, 'max_abs_dlog_iv', '{:.3f}')} |")
    L += ["", "## By the window's realised-volatility tercile (low ≈ the real analogue of calm, high ≈ panic; a DESIGN mapping)", "",
          "| pair | tercile | n | IV mean P10/P50/P90 | IV−RV20 P50 | corr P50 |", "|---|---|---|---|---|---|"]
    for pair, b in summ.items():
        for t, bt in (b.get("by_rv_tercile") or {}).items():
            iv = bt.get("iv_mean"); gap = bt.get("iv_minus_rv20_mean"); c = bt.get("iv_rv20_corr")
            L.append(f"| {pair} | {t} | {bt['n']} | " + ("—" if not iv else f"{iv['p10']:.1f} / {iv['p50']:.1f} / {iv['p90']:.1f}") +
                     f" | " + ("—" if not gap else f"{gap['p50']:+.1f}") + " | " + ("—" if not c else f"{c['p50']:.2f}") + " |")
    L += ["", "The v2 item-13 bands (calm IV 25–35 %, panic 60–100 %, corr 0.4–0.8, IV−RV +3..+8 calm / +10..+25 panic) are to be read "
              "against these rows; the generator's single stock is compared with the single-stock pairs, its index-like "
              "properties with the VIX pairs, and the criterion in force is the pre-registration's.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DEFAULT)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    vix = _iv_series("VIX")
    rows: List[Dict] = []
    notes = {}
    try:
        sp = _fred_sp500()
        rows += windows_for_pair(vix, sp, "index:VIX vs S&P 500 (FRED, 2016-)")
        notes["fred"] = f"{len(sp)} S&P 500 closes {sp.index[0].date()} .. {sp.index[-1].date()}"
    except Exception as e:
        notes["fred"] = f"unavailable: {type(e).__name__}: {e}"
    try:
        ff = _ff_market_index()
        rows += windows_for_pair(vix, ff, "index:VIX vs FF value-weighted US market (1990-)")
        notes["ff_market"] = f"Fama-French daily Mkt-RF + RF, {len(ff)} days {ff.index[0].date()} .. {ff.index[-1].date()}"
    except Exception as e:
        notes["ff_market"] = f"unavailable: {type(e).__name__}: {e}"
    try:
        ew = _setA_ew_index()
        rows += windows_for_pair(vix, ew, "index:VIX vs set-A equal-weight proxy (2000-2024)")
        notes["setA_ew"] = f"equal-weighted index of set A's daily log returns, {len(ew)} days"
    except Exception as e:
        notes["setA_ew"] = f"unavailable: {type(e).__name__}: {e}"
    for sym, tk in SINGLE.items():
        try:
            rows += windows_for_pair(_iv_series(sym), _price_series(tk), f"single:{sym} vs {tk}")
        except Exception as e:
            notes[sym] = f"unavailable: {type(e).__name__}: {e}"
    df = pd.DataFrame(rows)
    summ = summarise(df)
    meta = {"T_window": T_WINDOW, "n_windows_total": int(len(df)), "pairs": {k: int(v) for k, v in df.groupby("pair").size().items()},
            "sources": notes, "iv_dir": os.path.relpath(IV_DIR, ROOT).replace("\\", "/"),
            "caveat": ("the five single-stock IV indices are five surviving mega-caps chosen by the CBOE (2011-2026), a small and "
                       "selected sample; the FRED index pair is exact but ten years; the set-A proxy is equal-weighted and "
                       "survivor-biased, so its realised vol is not the S&P 500's -- the three are reported side by side with their n"),
            "seconds": round(time.time() - t0, 1), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    df.to_csv(os.path.join(a.out, "iv_windows.csv"), index=False)
    with open(os.path.join(a.out, "iv_reference.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "summary": summ}, fh, indent=1)
    with open(os.path.join(a.out, "iv_reference.md"), "w", encoding="utf-8") as fh:
        fh.write(to_markdown(summ, meta))
    print(json.dumps(meta, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
