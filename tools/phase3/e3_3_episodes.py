"""
E3.3 (PREREG_PHASE_3.md section 5): phase variance multipliers from the panel's own event windows, and the
rise-time / decay-half-life inputs to E3.4 (REG-6).

    python -m tools.phase3.e3_3_episodes

Set A (417 names), Adj Close (ffilled), 2000-2024, the shared estimator of tools/phase3/episodes.py.
Statistics: medians over episodes with 1,000-resample STOCK-bootstrap 95 % CIs (stocks resampled with all their
episodes, so within-stock and cross-time clustering survives in the interval).

Outputs: docs/env_v2/generated/v2_1/e3_3/{episodes.json,episodes.md,dd_episodes.csv,ru_episodes.csv,market.csv}
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase1.panel import DEFAULT, analysis_sets, load_prices  # noqa: E402
from tools.phase3.episodes import (drawdown_episodes, runup_episodes, dd_windows, runup_windows,  # noqa: E402
                                   episode_multipliers, rise_decay, _rv, MIN_CALM)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_3")
N_BOOT = 1000
SEED_BOOT = 202001
MARKET_WINDOWS = {"2008Q4": ("2008-10-01", "2008-12-31"), "2011Q3": ("2011-07-01", "2011-09-30"),
                  "2018Q4": ("2018-10-01", "2018-12-31"), "2020Q1": ("2020-01-01", "2020-03-31"),
                  "2022H1": ("2022-01-03", "2022-06-30")}
LIT = {"Ang & Timmermann 2012 (monthly S&P, read by the plan's pass)": "sigma 4.89 % vs 2.45 % -> variance ratio ~ 4.0",
       "Ang & Bekaert 2002 (monthly)": "7.04 % vs 3.77 %",
       "Schwert 1989 (JF; index, monthly)": "recession/expansion volatility +76 % (1859-1986) to +227 % (1927-86)",
       "GSY 2019 (JFE; industry, monthly)": "40 run-ups >= 100 %, 21 crashed; volatility rises in run-ups that crash",
       "plan's two index examples (not a sample)": "onset->peak-RV 2020 ~ 10 trading days, 2008 ~ 30"}


def collect():
    sets = analysis_sets(write=False)
    A = sets["A"]
    prices = load_prices(A).ffill()
    dd_rows, ru_rows, mk_rows = [], [], []
    dates = prices.index
    mk_idx = {k: (dates.searchsorted(pd.Timestamp(lo)), dates.searchsorted(pd.Timestamp(hi), side="right"))
              for k, (lo, hi) in MARKET_WINDOWS.items()}
    from tools.phase3.episodes import rolling_rv, _rv as rv_win
    for t in A:
        p = prices[t].to_numpy(float)
        if not np.isfinite(p).any():
            continue
        logp = np.log(p)
        r = np.diff(logp)
        rv21 = rolling_rv(r)
        rv_uncond = float(np.nanmedian(rv21))              # ADDENDUM section 1: the corrected reference
        for ep in drawdown_episodes(p):
            win = dd_windows(ep, logp)
            if win is None:
                continue
            mult = episode_multipliers(win, r, ["deterioration", "panic", "stabilisation"])
            row = {"ticker": t, "peak": int(ep["peak"]), "trough": int(ep["trough"]), "depth": ep["depth"],
                   "peak_date": str(dates[ep["peak"]].date()), "trough_date": str(dates[ep["trough"]].date()),
                   "truncated_stab": bool(ep["trough"] + 60 > len(r)), "rv_uncond": rv_uncond,
                   "span": int(ep["trough"] - ep["peak"])}
            if mult:
                row.update(mult)
                if rv_uncond > 0:
                    row["calm_over_uncond"] = mult["rv_calm"] / rv_uncond
                    for k in ("deterioration", "panic", "stabilisation"):
                        rw = rv_win(r, *win[k])
                        row[f"mu_{k}"] = rw / rv_uncond if np.isfinite(rw) else np.nan
            rd = rise_decay(ep, p, r, mult["rv_calm"] if mult else float("nan"))
            if rd:
                row.update({k: rd[k] for k in ("rise", "decay_half_life", "censored", "stress_spell",
                                               "rv_peak_over_calm")})
            rdu = rise_decay(ep, p, r, rv_uncond)
            if rdu:
                row["decay_half_life_uncond"] = rdu["decay_half_life"]
                row["stress_spell_uncond"] = rdu["stress_spell"]
            dd_rows.append(row)
        for ep in runup_episodes(p):
            win = runup_windows(ep, logp)
            if win is None:
                continue
            mult = episode_multipliers(win, r, ["mania", "blow-off", "post-top"])
            row = {"ticker": t, "top": int(ep["top"]), "start": int(ep["start"]), "runup": ep["runup"],
                   "top_date": str(dates[ep["top"]].date()), "rv_uncond": rv_uncond}
            if mult:
                row.update(mult)
                if rv_uncond > 0:
                    row["calm_over_uncond"] = mult["rv_calm"] / rv_uncond
                    for k in ("mania", "blow-off", "post-top"):
                        rw = rv_win(r, *win[k])
                        row[f"mu_{k}"] = rw / rv_uncond if np.isfinite(rw) else np.nan
            ru_rows.append(row)
        for k, (lo, hi) in mk_idx.items():
            rv_w = _rv(r, lo - 1, hi - 1)
            rv_c = _rv(r, lo - 1 - 120, lo - 1, min_n=MIN_CALM)
            if np.isfinite(rv_w) and np.isfinite(rv_c) and rv_c > 0:
                from tools.phase3.episodes import rolling_rv
                rvroll = rolling_rv(r)[max(lo - 1, 20):hi - 1]
                mk_rows.append({"ticker": t, "window": k, "m": rv_w / rv_c,
                                "m_peak21": float(np.nanmax(rvroll) / rv_c) if np.isfinite(rvroll).any() else np.nan})
    return pd.DataFrame(dd_rows), pd.DataFrame(ru_rows), pd.DataFrame(mk_rows)


def boot_median(df: pd.DataFrame, col: str, seed_off: int = 0):
    """Median over episodes; CI from a stock bootstrap (stocks resampled with all their episodes)."""
    d = df[np.isfinite(df[col].astype(float))]
    if len(d) < 5:
        return None
    stocks = d["ticker"].unique()
    by = {t: g[col].to_numpy(float) for t, g in d.groupby("ticker")}
    rng = np.random.default_rng(SEED_BOOT + seed_off)
    meds = []
    for _ in range(N_BOOT):
        ss = rng.choice(stocks, len(stocks), replace=True)
        v = np.concatenate([by[t] for t in ss])
        meds.append(np.median(v))
    v = d[col].to_numpy(float)
    return {"median": float(np.median(v)), "ci95": [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))],
            "p25_75": [float(np.percentile(v, 25)), float(np.percentile(v, 75))],
            "n_episodes": int(len(d)), "n_stocks": int(d["ticker"].nunique())}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    dd, ru, mk = collect()
    dd.to_csv(os.path.join(OUT, "dd_episodes.csv"), index=False)
    ru.to_csv(os.path.join(OUT, "ru_episodes.csv"), index=False)
    mk.to_csv(os.path.join(OUT, "market.csv"), index=False)
    out = {"design": {"panel": "set A (417), Adj Close ffilled, 2000-2024", "estimator": "tools/phase3/episodes.py",
                      "spec": DEFAULT.to_dict()["source_note"], "n_boot": N_BOOT, "seed_boot": SEED_BOOT,
                      "survivorship": "set A has no delistings (REG-15): depths and multipliers understate the "
                                      "full universe's crashes; the delisted tail is 4.7 % recoverable (E1.0)"},
           "drawdowns": {"n_episodes": int(len(dd)), "n_stocks": int(dd["ticker"].nunique()),
                         "depth": boot_median(dd, "depth", 1)},
           "multipliers": {}, "rise_decay": {}, "runups": {"n_episodes": int(len(ru)),
                                                           "n_stocks": int(ru["ticker"].nunique()) if len(ru) else 0},
           "market_windows": {}, "literature_beside": LIT}
    for k in ("deterioration", "panic", "stabilisation"):
        out["multipliers"][f"m_{k}"] = boot_median(dd, f"m_{k}", 2 + hash(k) % 100)
        out["multipliers"][f"mu_{k}"] = boot_median(dd, f"mu_{k}", 102 + hash(k) % 100)
    for k in ("mania", "blow-off", "post-top"):
        out["multipliers"][f"m_{k}"] = boot_median(ru, f"m_{k}", 200 + hash(k) % 100)
        out["multipliers"][f"mu_{k}"] = boot_median(ru, f"mu_{k}", 250 + hash(k) % 100)
    out["multipliers"]["calm_over_uncond_dd"] = boot_median(dd, "calm_over_uncond", 290)
    out["multipliers"]["calm_over_uncond_ru"] = boot_median(ru, "calm_over_uncond", 291)
    out["rise_decay"]["rise"] = boot_median(dd, "rise", 300)
    out["rise_decay"]["decay_half_life"] = boot_median(dd, "decay_half_life", 301)
    out["rise_decay"]["censored_share"] = (float(np.mean(dd["censored"].astype(float)))
                                           if "censored" in dd and np.isfinite(dd["censored"].astype(float)).any() else None)
    out["rise_decay"]["stress_spell"] = boot_median(dd, "stress_spell", 302)
    out["rise_decay"]["rv_peak_over_calm"] = boot_median(dd, "rv_peak_over_calm", 303)
    out["rise_decay"]["decay_half_life_uncond_ref"] = boot_median(dd, "decay_half_life_uncond", 304)
    # ADDENDUM section 2: the fast-crash subpopulation (peak->trough <= 126 trading days)
    fast = dd[dd["span"] <= 126]
    out["rise_decay_fast"] = {"definition": "drawdown episodes with peak->trough span <= 126 trading days "
                                            "(ADDENDUM section 2; the crash type the scenario template contains)",
                              "n_episodes": int(len(fast)), "n_stocks": int(fast["ticker"].nunique()),
                              "rise": boot_median(fast, "rise", 310),
                              "decay_half_life": boot_median(fast, "decay_half_life", 311),
                              "stress_spell": boot_median(fast, "stress_spell", 312),
                              "depth": boot_median(fast, "depth", 313),
                              "rv_peak_over_calm": boot_median(fast, "rv_peak_over_calm", 314)}
    for k in MARKET_WINDOWS:
        g = mk[mk["window"] == k]
        out["market_windows"][k] = {"m": boot_median(g, "m", 400 + hash(k) % 100),
                                    "m_peak21": boot_median(g, "m_peak21", 500 + hash(k) % 100)}
    out["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "episodes.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)

    def f(d, dp=2):
        if d is None:
            return "n/a"
        return (f"{d['median']:.{dp}f} [{d['ci95'][0]:.{dp}f}, {d['ci95'][1]:.{dp}f}] "
                f"(IQR {d['p25_75'][0]:.{dp}f}-{d['p25_75'][1]:.{dp}f}; n={d['n_episodes']}/{d['n_stocks']})")
    L = ["# E3.3 phase variance multipliers and rise/decay from panel event windows (PREREG_PHASE_3.md section 5)", "",
         f"{out['design']['panel']}; windows per PREREG 5.1; medians over episodes with {N_BOOT}-resample stock-bootstrap "
         "95 % CIs (n = episodes/stocks). Multipliers are RV(window)/RV(pre-event calm) per episode - TOTAL-return "
         "variance ratios (the x-innovation mapping is PREREG 5.3). " + out["design"]["survivorship"] + ".", "",
         "| statistic | vs UNCONDITIONAL ref (ADDENDUM 1, adopted) | vs pre-event window (as first registered) |",
         "|---|---|---|",
         f"| drawdown depth | {f(out['drawdowns']['depth'])} | (same) |"]
    for k in ("deterioration", "panic", "stabilisation", "mania", "blow-off", "post-top"):
        L.append(f"| m_{k} | {f(out['multipliers'][f'mu_{k}'])} | {f(out['multipliers'][f'm_{k}'])} |")
    L += [f"| pre-event calm / unconditional (dd) | {f(out['multipliers']['calm_over_uncond_dd'])} | |",
          f"| pre-event calm / unconditional (ru) | {f(out['multipliers']['calm_over_uncond_ru'])} | |",
          f"| rise time (onset -> RV21 peak, d) | {f(out['rise_decay']['rise'], 1)} | (reference-free) |",
          f"| decay half-life (d) | {f(out['rise_decay']['decay_half_life_uncond_ref'], 1)} | {f(out['rise_decay']['decay_half_life'], 1)} |",
          f"| censored share (decay) | {out['rise_decay']['censored_share']:.3f} | |",
          f"| stress spell (d) | {f(out['rise_decay']['stress_spell'], 1)} | |",
          f"| RV21 peak / calm | {f(out['rise_decay']['rv_peak_over_calm'], 2)} | |", "",
          f"Fast-crash subpopulation (ADDENDUM 2: span <= 126 d; n = {out['rise_decay_fast']['n_episodes']}"
          f"/{out['rise_decay_fast']['n_stocks']}): rise {f(out['rise_decay_fast']['rise'], 1)}; decay "
          f"{f(out['rise_decay_fast']['decay_half_life'], 1)}; stress spell {f(out['rise_decay_fast']['stress_spell'], 1)}; "
          f"depth {f(out['rise_decay_fast']['depth'])}.", "",
          "Market-wide windows (per-stock RV ratio to own 120-d pre-window calm):", "",
          "| window | m | peak-21d m |", "|---|---|---|"]
    for k in MARKET_WINDOWS:
        L.append(f"| {k} | {f(out['market_windows'][k]['m'])} | {f(out['market_windows'][k]['m_peak21'])} |")
    L += ["", "Literature beside (not tolerances): " + "; ".join(f"{k}: {v}" for k, v in LIT.items()) + "."]
    with open(os.path.join(OUT, "episodes.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L[4:]))


if __name__ == "__main__":
    main()
