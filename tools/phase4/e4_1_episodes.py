"""
E4.1 (PREREG_PHASE_4.md section 3): the episode tables every later Phase-4 experiment is defined by.

    python -m tools.phase4.e4_1_episodes [--stages panel,index,xsec,pv] [--workers 3]

D4 (team, 5 Sep 2026): the SINGLE-STOCK PANEL is primary; index episodes are published beside it.

Families, all built from the SHARED estimator of tools/phase3/episodes.py so the generator can be measured the
same way later:
  dd20 / dd30    running-peak drawdowns of >= 20 % / >= 30 % (dd30 is Phase 3's inherited family, verified in E4.0)
  ps_primary / ps_sensitive   Pagan-Sossounov bear phases at two censoring settings (168/126/336 and 84/63/168
                 trading days).  Pagan & Sossounov's own 25/15-MONTH durations were NOT read from the paper and
                 are NOT quoted; the constants above are this phase's stated choices and both are reported.
  runup          GSY-style run-ups of >= 100 % in 504 trading days (inherited, verified in E4.0)

Quantities per episode: depth, peak-to-trough duration, deterioration length (peak -> first -10 %), front-loading
(share of the log decline in the first third), recovery share at 60/120/200 d; for run-ups the 200-day outcome
(post-top drop, its length, whether it topped) and a CORRECTED calm reference (E4.0c found E3.3's run-up calm
window sits at a post-crash trough, sd 0.0413 against the drawdown family's 0.0217).

Every quantity is reported as empirical P10 / P50 / P90 with a 1,000-resample STOCK bootstrap on each quantile,
n stated as (episodes, stocks).

Output: docs/env_v2/generated/v2_1/e4_1/{episodes4.json, episodes4.md, dd20.csv, dd30.csv, ps_primary.csv,
        ps_sensitive.csv, runup4.csv, index_shiller.csv}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase1.panel import analysis_sets, load_prices, shiller, DEFAULT  # noqa: E402
from tools.phase3.episodes import (drawdown_episodes, runup_episodes, ps_bear_episodes,  # noqa: E402
                                   deterioration_length, front_loading, recovery_shares,
                                   runup_outcome, clean_runup_calm, dd_windows, runup_windows,
                                   episode_multipliers, rise_decay, rolling_rv, _rv, PS_SETTINGS)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e4_1")
N_BOOT = 1000
SEED_BOOT = 400020
QUANTS = (10, 50, 90)
FAMILIES = ("dd20", "dd30", "ps_primary", "ps_sensitive")


def quantile_table(df: pd.DataFrame, cols, n_boot=N_BOOT, seed=SEED_BOOT):
    """P10/P50/P90 of each column with a stock-cluster bootstrap CI on every quantile."""
    tick = df["ticker"].to_numpy()
    stocks = np.array(sorted(set(tick.tolist())))
    idx_by = {t: np.where(tick == t)[0] for t in stocks}
    rng = np.random.default_rng(seed)
    boot_rows = [np.concatenate([idx_by[t] for t in rng.choice(stocks, len(stocks), replace=True)])
                 for _ in range(n_boot)]
    out = {}
    for c in cols:
        v = pd.to_numeric(df[c], errors="coerce").to_numpy(float)
        ok = np.isfinite(v)
        if ok.sum() < 20:
            out[c] = {"n_episodes": int(ok.sum()), "note": "too few finite values"}
            continue
        pt = {f"p{q}": float(np.percentile(v[ok], q)) for q in QUANTS}
        bs = {q: [] for q in QUANTS}
        for ri in boot_rows:
            vv = v[ri]
            vv = vv[np.isfinite(vv)]
            if len(vv) < 20:
                continue
            for q in QUANTS:
                bs[q].append(np.percentile(vv, q))
        ci = {f"p{q}_ci95": [float(np.percentile(bs[q], 2.5)), float(np.percentile(bs[q], 97.5))]
              for q in QUANTS if bs[q]}
        out[c] = {**pt, **ci, "mean": float(np.mean(v[ok])),
                  "n_episodes": int(ok.sum()),
                  "n_stocks": int(len(set(tick[ok].tolist())))}
    return out


def collect_panel(workers=3):
    sets = analysis_sets(write=False)
    A = sets["A"]
    prices = load_prices(A).ffill()
    dates = prices.index
    rows = {f: [] for f in FAMILIES}
    ru_rows = []
    dd_mask_by_day = np.zeros(len(dates), float)   # for the cross-sectional correlation
    dd_count = np.zeros(len(dates), float)
    n_live = np.zeros(len(dates), float)
    for t in A:
        p = prices[t].to_numpy(float)
        if not np.isfinite(p).any():
            continue
        logp = np.log(np.where(np.isfinite(p) & (p > 0), p, np.nan))
        r = np.diff(logp)
        live = np.isfinite(p)
        n_live += live
        fam_eps = {
            "dd20": drawdown_episodes(p, depth_thr=-0.20),
            "dd30": drawdown_episodes(p, depth_thr=-0.30),
            "ps_primary": ps_bear_episodes(p, **PS_SETTINGS["primary"]),
            "ps_sensitive": ps_bear_episodes(p, **PS_SETTINGS["sensitive"]),
        }
        for fam, eps in fam_eps.items():
            for e in eps:
                rec = recovery_shares(e, p)
                row = {"ticker": t, "peak": e["peak"], "trough": e["trough"], "depth": e["depth"],
                       "peak_date": str(dates[e["peak"]].date()), "trough_date": str(dates[e["trough"]].date()),
                       "duration": int(e["trough"] - e["peak"]),
                       "det_len": deterioration_length(e, p),
                       "front_load": front_loading(e, p), **rec}
                # panic length = duration - deterioration length (E4.2 draws panic_len from this)
                row["panic_len"] = (row["duration"] - row["det_len"]) if row["det_len"] is not None else None
                w = dd_windows(e, logp)
                if w:
                    m = episode_multipliers(w, r, ["deterioration", "panic", "stabilisation"])
                    if m:
                        row.update(m)
                        rd = rise_decay(e, p, r, m["rv_calm"])
                        if rd:
                            row.update({"rise": rd["rise"], "onset": rd["onset"],
                                        "decay_half_life": rd["decay_half_life"],
                                        "stress_spell": rd["stress_spell"]})
                rows[fam].append(row)
                if fam == "dd30":
                    dd_count[e["peak"]:e["trough"] + 1] += 1
        for e in runup_episodes(p):
            oc = runup_outcome(e, p, horizon=200, drop_thr=-0.40)
            row = {"ticker": t, "top": e["top"], "start": e["start"], "runup": e["runup"],
                   "top_date": str(dates[e["top"]].date()), "start_date": str(dates[e["start"]].date()),
                   "runup_len": int(e["top"] - e["start"]), **oc,
                   "rv_calm_clean": clean_runup_calm(e, r)}
            w = runup_windows(e, logp)
            if w:
                m = episode_multipliers(w, r, ["mania", "blow-off", "post-top"])
                if m:
                    row["rv_calm_e33"] = m["rv_calm"]
                    for k in ("mania", "blow-off", "post-top"):
                        row["rv_" + k] = m["m_" + k] * m["rv_calm"]
            ru_rows.append(row)
    dd_share = np.divide(dd_count, np.maximum(n_live, 1), out=np.zeros_like(dd_count), where=n_live > 0)
    return rows, ru_rows, dates, dd_share, n_live, len(A)


def index_episodes_shiller():
    """Index episodes computed AT FIRST HAND from the Shiller monthly series (datasets/04_shiller).

    Citation status, stated per the plan's Section 1 rule: Mishkin & White (2002, NBER w8992) and
    Barro & Ursua (NBER w14760 / Research in Economics 71(3)) were NOT read at source in this phase and
    therefore NO number from either is quoted here.  The index table below is this phase's own computation
    on data it holds, and is published beside the panel as D4 directs, not used to set any parameter."""
    sh = shiller()
    if not {"P", "CPI"}.issubset(sh.columns):
        return {"error": "the Shiller file does not carry both P and CPI", "columns": list(sh.columns)}
    # REAL price, deflated to the last available CPI -- the series the plan names for the cumulative-decline
    # shapes.  Nominal P would attribute inflation to the episodes.
    cpi = pd.to_numeric(sh["CPI"], errors="coerce")
    nom = pd.to_numeric(sh["P"], errors="coerce")
    ok = cpi.notna() & nom.notna()
    sh = sh[ok].copy()
    cpi, nom = cpi[ok], nom[ok]
    col = "real_price (P / CPI x CPI_last)"
    p = (nom / cpi * float(cpi.iloc[-1])).to_numpy(float)
    idx = sh.index
    eps20 = drawdown_episodes(p, depth_thr=-0.20)
    eps30 = drawdown_episodes(p, depth_thr=-0.30)
    rows = []
    for fam, eps in (("dd20", eps20), ("dd30", eps30)):
        for e in eps:
            rec = recovery_shares(e, p, horizons=(3, 6, 12))     # months, not days
            rows.append({"family": fam, "peak_i": e["peak"], "trough_i": e["trough"], "depth": e["depth"],
                         "peak": str(idx[e["peak"]])[:10], "trough": str(idx[e["trough"]])[:10],
                         "duration_months": int(e["trough"] - e["peak"]),
                         "det_len_months": deterioration_length(e, p),
                         "front_load": front_loading(e, p), **rec})
    df = pd.DataFrame(rows)
    summ = {}
    for fam in ("dd20", "dd30"):
        d = df[df["family"] == fam]
        summ[fam] = {"n_episodes": int(len(d)),
                     "series": col, "frequency": "monthly",
                     "span": [str(idx[0])[:10], str(idx[-1])[:10]],
                     **{c: {f"p{q}": (float(np.nanpercentile(pd.to_numeric(d[c], errors="coerce"), q))
                                      if pd.to_numeric(d[c], errors="coerce").notna().sum() >= 5 else None)
                            for q in QUANTS}
                        for c in ("depth", "duration_months", "det_len_months", "front_load")}}
    return {"table": df, "summary": summ,
            "citation_status": {
                "Mishkin & White (2002, NBER w8992)": "NOT READ AT SOURCE IN THIS PHASE - no number quoted",
                "Barro & Ursua (NBER w14760 / Research in Economics 71(3))": "NOT READ AT SOURCE IN THIS PHASE - no number quoted",
                "Pagan & Sossounov (2003, JAE)": "algorithm applied; their 25/15-month durations NOT read and NOT quoted",
                "Shiller monthly series": "held on disk (datasets/04_shiller), computed at first hand here"}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="panel,index,xsec")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    jpath = os.path.join(OUT, "episodes4.json")
    res = json.load(open(jpath, encoding="utf-8")) if os.path.exists(jpath) else {}
    res.setdefault("design", {})
    res["design"].update({"prereg": "PREREG_PHASE_4.md section 3", "n_boot": N_BOOT, "quantiles": list(QUANTS),
                          "families": list(FAMILIES), "ps_settings": PS_SETTINGS,
                          "primary_population": "single-stock panel (D4, team 5 Sep 2026)",
                          "panel": "analysis set A, Adj Close ffilled, 2000-2024"})
    stages = [s.strip() for s in a.stages.split(",")]

    def save():
        with open(jpath, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, default=str)

    if "panel" in stages:
        print("[panel] collecting four drawdown families and the run-ups ...", flush=True)
        rows, ru_rows, dates, dd_share, n_live, n_names = collect_panel(a.workers)
        cols_dd = ["depth", "duration", "det_len", "panic_len", "front_load",
                   "rec60", "rec120", "rec200", "rise", "decay_half_life", "stress_spell"]
        res["panel_families"] = {}
        for fam in FAMILIES:
            df = pd.DataFrame(rows[fam])
            df.to_csv(os.path.join(OUT, f"{fam}.csv"), index=False)
            res["panel_families"][fam] = {
                "n_episodes": int(len(df)), "n_stocks": int(df["ticker"].nunique()) if len(df) else 0,
                "quantiles": quantile_table(df, cols_dd) if len(df) else {}}
            print(f"    {fam:14s} {len(df):5d} episodes / "
                  f"{df['ticker'].nunique() if len(df) else 0} stocks", flush=True)
        ru = pd.DataFrame(ru_rows)
        ru.to_csv(os.path.join(OUT, "runup4.csv"), index=False)
        cols_ru = ["runup", "runup_len", "post_drop", "post_len"]
        res["runups"] = {"n_episodes": int(len(ru)), "n_stocks": int(ru["ticker"].nunique()) if len(ru) else 0,
                         "quantiles": quantile_table(ru, cols_ru) if len(ru) else {}}
        # the topped share -- REG-18's decision input
        tp = ru["topped"].dropna().astype(bool).to_numpy() if "topped" in ru else np.array([], bool)
        if len(tp):
            tick = ru.loc[ru["topped"].notna(), "ticker"].to_numpy()
            stocks = np.array(sorted(set(tick.tolist())))
            idx_by = {t: np.where(tick == t)[0] for t in stocks}
            rng = np.random.default_rng(SEED_BOOT + 1)
            bs = [float(tp[np.concatenate([idx_by[t] for t in rng.choice(stocks, len(stocks), replace=True)])].mean())
                  for _ in range(N_BOOT)]
            res["runups"]["topped_share_200d"] = {
                "point": float(tp.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                "n_episodes": int(len(tp)), "n_stocks": int(len(stocks)),
                "definition": "deepest drawdown within 200 trading days of the top is <= -40 % (GSY's crash "
                              "threshold at the benchmark's own horizon; both numbers stated)",
                "survivorship": "REG-15: the survivor panel understates crash frequency and depth"}
            print(f"    topped share (200 d, -40 %) {tp.mean():.3f} "
                  f"[{np.percentile(bs, 2.5):.3f}, {np.percentile(bs, 97.5):.3f}] n={len(tp)}/{len(stocks)}",
                  flush=True)
        # the corrected run-up calm reference E4.0c asked for
        c_clean = pd.to_numeric(ru.get("rv_calm_clean"), errors="coerce").dropna()
        c_e33 = pd.to_numeric(ru.get("rv_calm_e33"), errors="coerce").dropna()
        res["runup_calm_reference"] = {
            "e3_3_window_120d_before_start": {"pooled_mean_sd": float(math.sqrt(c_e33.mean())) if len(c_e33) else None,
                                              "n": int(len(c_e33))},
            "corrected_window_120d_after_start": {"pooled_mean_sd": float(math.sqrt(c_clean.mean())) if len(c_clean) else None,
                                                  "n": int(len(c_clean))},
            "why": "E4.0c: E3.3's run-up calm window sits at a post-crash trough, so it cannot serve as the "
                   "run-up population's calm reference; the corrected window is the quiet start of the run-up "
                   "itself"}
        for k in ("mania", "blow-off", "post-top"):
            v = pd.to_numeric(ru.get("rv_" + k), errors="coerce")
            m = v.notna() & pd.to_numeric(ru.get("rv_calm_clean"), errors="coerce").notna()
            if m.sum() > 20:
                res["runup_calm_reference"].setdefault("ratios_on_corrected_reference", {})[k] = {
                    "pooled_mean_ratio": float(v[m].mean() / pd.to_numeric(ru.loc[m, "rv_calm_clean"]).mean()),
                    "n": int(m.sum())}
        res["cross_section"] = {
            "n_names": int(n_names),
            "mean_share_in_drawdown": float(np.nanmean(dd_share)),
            "p90_share_in_drawdown": float(np.nanpercentile(dd_share, 90)),
            "max_share_in_drawdown": float(np.nanmax(dd_share)),
            "definition": "share of live names inside a >= 30 % running-peak drawdown on each day; the "
                          "common-factor loading E4.8 replaces the shared multi-asset event with"}
        pd.DataFrame({"date": [str(d.date()) for d in dates], "share_in_drawdown": dd_share,
                      "n_live": n_live}).to_csv(os.path.join(OUT, "xsec_drawdown_share.csv"), index=False)
        print(f"    cross-sectional drawdown share: mean {res['cross_section']['mean_share_in_drawdown']:.3f} "
              f"p90 {res['cross_section']['p90_share_in_drawdown']:.3f} "
              f"max {res['cross_section']['max_share_in_drawdown']:.3f}", flush=True)
        save()

    if "index" in stages:
        print("[index] Shiller monthly, computed at first hand ...", flush=True)
        ix = index_episodes_shiller()
        if "table" in ix:
            ix["table"].to_csv(os.path.join(OUT, "index_shiller.csv"), index=False)
            res["index_shiller"] = {"summary": ix["summary"], "citation_status": ix["citation_status"]}
            for fam in ("dd20", "dd30"):
                print(f"    {fam}: {ix['summary'][fam]['n_episodes']} index episodes "
                      f"({ix['summary'][fam]['span'][0]} to {ix['summary'][fam]['span'][1]})", flush=True)
        else:
            res["index_shiller"] = ix
            print(f"    FAILED: {ix.get('error')}", flush=True)
        save()

    res["seconds"] = round(time.time() - t0, 1)
    save()
    print(f"wrote {jpath} in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
