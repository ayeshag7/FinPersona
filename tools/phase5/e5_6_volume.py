"""
E5.6 -- volume: log-volume persistence, the |r| elasticity, the noise sd, and the run-up turnover ratio
(PREREG_PHASE_5.md section 9.1).

    python -m tools.phase5.e5_6_volume

Data: set A daily Volume and Adj Close (Yahoo, 2000-01-03 .. 2024-12-31); the run-up episodes of `e4_1/runup4.csv`.
Per stock: lv_t = log Vol_t - trailing-252-day mean of log Vol (DESIGN detrending: no shares outstanding, so no
turnover); r_t = dlog Adj Close; sigma_t = trailing-252-day sd of r (shifted one day); a_t = |r_t| / sigma_t - mean;
lv_t = rho_v lv_{t-1} + beta a_t + sigma_e e_t by OLS (>= 1,000 days).  Medians with a 1,000-resample stock bootstrap;
sub-periods.  Run-up ratio: mean lv over [start, top] minus its mean over the 252 days before start (a log ratio),
per episode; median with an episode bootstrap clustered by stock; and the level-free form: lv_t on max(ret_252, 0)
beside the AR and |r| terms (beta_ru), pooled by stock.

Output: docs/env_v2/generated/v2_1/e5_6/volume.{json,md}, volume_by_stock.csv
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

from tools.phase1.panel import DEFAULT, analysis_sets, load_prices, sub_period_mask  # noqa: E402
from tools.phase5.common import GEN  # noqa: E402

OUT = os.path.join(GEN, "e5_6")
N_BOOT = 1000
MIN_DAYS = 1000


def per_stock(lv, a, ru):
    ok = np.isfinite(lv) & np.isfinite(a) & np.isfinite(ru)
    ok[1:] &= np.isfinite(lv[:-1])
    ok[0] = False
    if ok.sum() < MIN_DAYS:
        return None
    y = lv[ok]; X = np.column_stack([lv[np.where(ok)[0] - 1], a[ok]])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    X2 = np.column_stack([X, ru[ok]])
    b2 = np.linalg.lstsq(X2, y, rcond=None)[0]
    e2 = y - X2 @ b2
    return {"n": int(ok.sum()), "rho_v": float(b[0]), "beta_absr": float(b[1]), "sd_e": float(e.std(ddof=2)),
            "rho_v_B": float(b2[0]), "beta_absr_B": float(b2[1]), "beta_ru": float(b2[2]), "sd_e_B": float(e2.std(ddof=3)),
            "sd_lv": float(y.std(ddof=1))}


def boot_median(v, n_boot=N_BOOT, seed=560001):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    m = np.median(v[rng.integers(0, len(v), (n_boot, len(v)))], axis=1)
    return {"median": float(np.median(v)), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))],
            "iqr": [float(np.percentile(v, 25)), float(np.percentile(v, 75))], "n": int(len(v))}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    A = analysis_sets(write=False)["A"]
    px = load_prices(A, DEFAULT).ffill()
    vol = load_prices(A, DEFAULT, col="Volume")
    lp = np.log(px); r = lp.diff()
    lvol = np.log(vol.where(vol > 0))
    lv = lvol - lvol.rolling(252, min_periods=126).mean()
    sig = r.rolling(252, min_periods=126).std().shift(1)
    a = (r.abs() / sig)
    a = a - a.mean()                      # per stock demeaned |z|
    ret252 = lp - lp.shift(252)
    ru = ret252.clip(lower=0.0)
    rows = []; subs = {n: [] for n, _, _ in DEFAULT.sub_periods}
    masks = sub_period_mask(px.index, DEFAULT)
    for t in A:
        rec = per_stock(lv[t].to_numpy(float), a[t].to_numpy(float), ru[t].to_numpy(float))
        if rec:
            rec["ticker"] = t; rows.append(rec)
        for name, m in masks.items():
            rs = per_stock(lv[t].to_numpy(float)[m], a[t].to_numpy(float)[m], ru[t].to_numpy(float)[m])
            if rs:
                subs[name].append(rs)
    df = pd.DataFrame(rows); df.to_csv(os.path.join(OUT, "volume_by_stock.csv"), index=False)
    fits = {k: boot_median(df[k]) for k in ("rho_v", "beta_absr", "sd_e", "rho_v_B", "beta_absr_B", "beta_ru", "sd_e_B", "sd_lv")}
    sub = {name: {k: float(np.median([x[k] for x in L])) for k in ("rho_v", "beta_absr", "sd_e", "beta_ru")} | {"n_stocks": len(L)}
           for name, L in subs.items() if L}

    # run-up turnover ratio on E4.1's episodes: verify the index convention before use (P4-37 / P1's rule)
    ruf = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    checked = 0; bad = 0; ratios = []
    lv_full = lvol - lvol.rolling(252, min_periods=126).mean()
    for _, e in ruf.iterrows():
        t = e["ticker"]
        if t not in px.columns:
            continue
        s, tp = int(e["start"]), int(e["top"])
        p = px[t].to_numpy(float)
        if tp >= len(p) or s < 0:
            continue
        checked += 1
        if not np.isfinite(p[s]) or abs(p[tp] / p[s] - float(e["runup"])) > 1e-6 * max(1.0, float(e["runup"])):
            bad += 1
            continue
        lvt = lvol[t].to_numpy(float)
        if s - 252 < 0:
            continue
        pre = lvt[s - 252:s]; dur = lvt[s:tp + 1]
        if np.isfinite(pre).sum() < 126 or np.isfinite(dur).sum() < 20:
            continue
        ratios.append({"ticker": t, "log_ratio": float(np.nanmean(dur) - np.nanmean(pre)), "runup": float(e["runup"]),
                       "len": int(tp - s), "log_ratio_per_log_runup": float((np.nanmean(dur) - np.nanmean(pre)) / np.log(float(e["runup"])))})
    rr = pd.DataFrame(ratios)
    rng = np.random.default_rng(560002)
    by_stock = {t: g["log_ratio"].to_numpy(float) for t, g in rr.groupby("ticker")}
    keys = list(by_stock); draws = []
    for _ in range(N_BOOT):
        pick = rng.choice(keys, len(keys), replace=True)
        draws.append(np.median(np.concatenate([by_stock[k] for k in pick])))
    runup = {"n_episodes": int(len(rr)), "n_stocks": int(rr["ticker"].nunique()), "episodes_index_checked": checked,
             "episodes_index_mismatch": bad,
             "log_ratio_median": float(rr["log_ratio"].median()),
             "log_ratio_ci95_stock_boot": [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))],
             "ratio_median": float(np.exp(rr["log_ratio"].median())),
             "ratio_ci95": [float(np.exp(np.percentile(draws, 2.5))), float(np.exp(np.percentile(draws, 97.5)))],
             "log_ratio_per_log_runup_median": float(rr["log_ratio_per_log_runup"].median()),
             "runup_size_median": float(rr["runup"].median()),
             "ci_excludes_1": bool(np.percentile(draws, 2.5) > 0 or np.percentile(draws, 97.5) < 0),
             "gsy_read": "GSY 2019 (read): turnover elevated in all run-ups, whether or not they crash -- a run-up feature, not a crash predictor"}

    res = {"what": "E5.6: volume fits (PREREG section 9.1)",
           "data": {"set": "A", "n_stocks": int(len(df)), "window": [DEFAULT.start, DEFAULT.end],
                    "detrending": "log volume minus its trailing 252-day mean (DESIGN: no shares outstanding in the panel)",
                    "survivor_caveat": "set A is survivor-only (REG-15); volume dynamics of delisted names are absent"},
           "design_A": {"rho_v": fits["rho_v"], "beta_absr_per_sd_z": fits["beta_absr"], "sd_e": fits["sd_e"], "sd_lv": fits["sd_lv"]},
           "design_B": {"rho_v": fits["rho_v_B"], "beta_absr_per_sd_z": fits["beta_absr_B"], "beta_ru_per_unit_pos_ret252": fits["beta_ru"], "sd_e": fits["sd_e_B"]},
           "sub_periods": sub, "runup_turnover_ratio": runup,
           "lo_wang_read": {"weekly_turnover_ac1_vw": 0.91, "ew": 0.87, "level": "market, weekly; sanity range only"},
           "v2_incumbent": {"rho": 0.65, "b_absr": 0.25, "b_absx": 1.2, "sd_e": 0.30, "label": "DESIGN (weakness item 24); the |x| loading has no read source and is DOMINATED"},
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "volume.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    def f(d, dd=4):
        return f"{d['median']:.{dd}f} [{d['ci95'][0]:.{dd}f}, {d['ci95'][1]:.{dd}f}] (IQR {d['iqr'][0]:.{dd}f}-{d['iqr'][1]:.{dd}f})"
    L = ["# E5.6 volume fits (PREREG_PHASE_5.md section 9.1)", "",
         f"Set A, {len(df)} stocks, {DEFAULT.start}..{DEFAULT.end}; {res['data']['detrending']}. Medians over stocks with a "
         f"{N_BOOT}-resample stock bootstrap. {res['data']['survivor_caveat']}.", "",
         f"- design A: rho_v {f(fits['rho_v'])}; beta(|r|/sigma) {f(fits['beta_absr'])}; residual sd {f(fits['sd_e'])}; sd of detrended log volume {f(fits['sd_lv'])}",
         f"- design B adds beta_ru on max(ret_252, 0): rho_v {f(fits['rho_v_B'])}; beta(|r|/sigma) {f(fits['beta_absr_B'])}; **beta_ru {f(fits['beta_ru'])}**; residual sd {f(fits['sd_e_B'])}",
         "", "| sub-period | n stocks | rho_v | beta | sd_e | beta_ru |", "|---|---|---|---|---|---|"]
    for k, v in sub.items():
        L.append(f"| {k} | {v['n_stocks']} | {v['rho_v']:.4f} | {v['beta_absr']:.4f} | {v['sd_e']:.4f} | {v['beta_ru']:.4f} |")
    L += ["", f"Run-up turnover ratio ({runup['n_episodes']} episodes / {runup['n_stocks']} stocks; {checked} episodes index-checked, "
              f"{bad} mismatches): median log ratio {runup['log_ratio_median']:+.4f} {runup['log_ratio_ci95_stock_boot']} = ratio "
              f"{runup['ratio_median']:.3f} {runup['ratio_ci95']}; per unit log run-up {runup['log_ratio_per_log_runup_median']:+.4f} "
              f"(median run-up size {runup['runup_size_median']:.2f}x); CI excludes 1: **{runup['ci_excludes_1']}**. {runup['gsy_read']}.",
          "", f"v2 incumbent: rho 0.65, +0.25 |r|, +1.2 |x| (dominated: no read source), noise 0.30. Lo & Wang (read): weekly turnover AC(1) 0.91/0.87 at the market level, sanity range only.", ""]
    with open(os.path.join(OUT, "volume.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L)); print(f"wrote {OUT}/volume.json in {res['seconds']} s")


if __name__ == "__main__":
    main()
