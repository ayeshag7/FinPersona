"""
E4.8 (PREREG_PHASE_4.md section 10): the label machinery and the small fixes -- three of the four measured
defects Phase 3 handed over with numbers.

    python -m tools.phase4.e4_8_labels [--seeds 500] [--workers 3] [--stages fit,blowoff,posttop,topday,xsec]

  blow-off   Phase 3 found the label is assigned EX POST by events.relabel_blowoff, so no blow-off variance
             multiplier has ever reached the GARCH driver -- dead code since v2.  Its calibration knob diverged
             2.2 -> 9.3 with the realised ratio pinned at ~1.1.  E4.8 gives the label a criterion that can be
             evaluated IN REAL TIME (the mania drift g above a FIT threshold) and measures what the multiplier
             then does.
  post-top   Phase 3 found the scripted reversal leg floors the realised variance ratio at 1.59 (n = 20)
             whatever the innovation multiplier is (it drove the multiplier to 0.35 and the ratio did not
             move): the leg is drift-dominated.  E4.8 re-derives the shape and searches the decay half-life.
  top day    recorded at the REALISED price peak as well as at the hazard firing; the off-by-one is measured,
             not asserted.
  xsec       the multi-asset shared event replaced by per-asset draws with a common-factor loading FIT from
             E4.1's cross-sectional drawdown correlation.

**The reference the targets are stated against is the corrected one.** E4.0c found E3.3's run-up "calm"
window sits at a post-crash trough (sd 0.0413 against the drawdown family's 0.0217), so the mania / blow-off /
post-top multipliers expressed against it are not comparable with the crash-side ones.  E4.1 supplies a clean
pre-run-up window; PREREG_PHASE_4_ADDENDUM section 2.5 suspended the old 1.16 post-top target until it existed.

Output: docs/env_v2/generated/v2_1/e4_8/{labels.json, labels.md}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e4_8")
SEED0 = 260000
N_BOOT = 1000
SCHED = "v21"                       # the schedule this module measures, PINNED (see addendum section 5)


def panel_targets():
    """The bubble-side ratios on the CORRECTED run-up calm reference (E4.1), with stock-bootstrap CIs."""
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    d = ru[pd.to_numeric(ru["rv_calm_clean"], errors="coerce").notna()].copy()
    out = {"reference": "120 trading days AFTER the run-up's start (the quiet beginning of the run-up), "
                        "replacing E3.3's window 120 d BEFORE the start, which sits at a post-crash trough",
           "n_episodes": int(len(d)), "n_stocks": int(d["ticker"].nunique())}
    tick = d["ticker"].to_numpy()
    stocks = np.array(sorted(set(tick.tolist())))
    idx_by = {t: np.where(tick == t)[0] for t in stocks}
    rng = np.random.default_rng(400070)
    boots = [np.concatenate([idx_by[t] for t in rng.choice(stocks, len(stocks), replace=True)])
             for _ in range(N_BOOT)]
    calm = pd.to_numeric(d["rv_calm_clean"], errors="coerce").to_numpy(float)
    for k in ("mania", "blow-off", "post-top"):
        v = pd.to_numeric(d.get("rv_" + k), errors="coerce").to_numpy(float)
        m = np.isfinite(v) & np.isfinite(calm)
        if m.sum() < 50:
            continue
        pt = float(np.mean(v[m]) / np.mean(calm[m]))
        bs = [float(np.nanmean(v[b]) / np.nanmean(calm[b])) for b in boots]
        out[k] = {"ratio_to_clean_calm": pt,
                  "ci95": [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))],
                  "n": int(m.sum())}
    if "mania" in out and "post-top" in out:
        out["post_top_over_mania"] = out["post-top"]["ratio_to_clean_calm"] / out["mania"]["ratio_to_clean_calm"]
        out["blowoff_over_mania"] = out["blow-off"]["ratio_to_clean_calm"] / out["mania"]["ratio_to_clean_calm"]
    # the blow-off drift threshold, FIT: the panel's blow-off window is the 20 d ending at the largest
    # trailing 20-day return, so its per-day drift is that return / 20
    return out


def blowoff_threshold_fit():
    """FIT g threshold for the real-time blow-off criterion, from the panel's own blow-off windows."""
    from tools.phase1.panel import analysis_sets, load_prices
    from tools.phase3.episodes import trailing_logret
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    A = analysis_sets(write=False)["A"]
    px = load_prices(A).ffill()
    vals = []
    cur = None
    for t, g in ru.groupby("ticker"):
        if t not in px.columns:
            continue
        p = px[t].to_numpy(float)
        lp = np.log(np.where(np.isfinite(p) & (p > 0), p, np.nan))
        r20 = trailing_logret(lp, 20)
        for _, row in g.iterrows():
            lo = max(int(row["start"]), int(row["top"]) - 126)
            seg = r20[lo:int(row["top"]) + 1]
            if np.isfinite(seg).any():
                vals.append(float(np.nanmax(seg)) / 20.0)
    v = np.array([x for x in vals if np.isfinite(x)], float)
    return {"g_threshold": float(np.percentile(v, 50)), "p10": float(np.percentile(v, 10)),
            "p90": float(np.percentile(v, 90)), "n": int(len(v)),
            "definition": "per-day drift of the panel's blow-off window: the largest trailing 20-day log "
                          "return inside the run-up, divided by 20; median over run-ups",
            "label": "FIT"}


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from tools.phase3.episodes import _rv
    seed, cfg = args
    env = SyntheticMarketEnv("bull_trap", 200, seed, config={**cfg, "schedule_mode": SCHED})
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    ph = d["phase"].to_numpy(object)[1:]
    r = np.diff(np.log(p))
    meta = env.event_meta
    out = {"seed": seed, "topped": bool(meta.get("topped")),
           "top_day": meta.get("top_day"), "top_day_realised": meta.get("top_day_realised"),
           "top_day_offset": meta.get("top_day_offset"),
           "blowoff_days": meta.get("blowoff_days"), "mania_days": meta.get("mania_days"),
           "cap_binding_share": meta.get("cap_binding_share")}
    ev = int(env.schedule.event_start)
    calm = _rv(r, 0, max(ev - 2, 0), min_n=30)
    out["rv_calm"] = float(calm) if np.isfinite(calm) else None
    for k in ("mania", "blow-off", "post-top"):
        m = ph == k
        if m.sum() >= 10:
            out["rv_" + k] = float(np.mean(r[m] ** 2))
            out["n_" + k] = int(m.sum())
    return out


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items, chunksize=4))


def ratios(rows):
    """Pooled-mean phase variance relative to the run's own mania, the comparable quantity on the corrected
    reference (the generator has no 'pre-run-up calm' of its own to divide by)."""
    agg = {}
    for k in ("mania", "blow-off", "post-top", "calm"):
        key = "rv_" + k if k != "calm" else "rv_calm"
        vs = [(r[key], r.get("n_" + k, 1)) for r in rows if r.get(key) is not None]
        if vs:
            s = sum(v * n for v, n in vs)
            n = sum(n for _, n in vs)
            agg[k] = s / max(n, 1)
    out = {}
    if "mania" in agg:
        for k in ("blow-off", "post-top"):
            if k in agg:
                out[f"{k}_over_mania"] = agg[k] / agg["mania"]
    if "calm" in agg:
        for k in ("mania", "blow-off", "post-top"):
            if k in agg:
                out[f"{k}_over_calm"] = agg[k] / agg["calm"]
    return out, agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--stages", default="fit,blowoff,posttop,topday,xsec")
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    jp = os.path.join(OUT, "labels.json")
    res = json.load(open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
    res.setdefault("design", {})
    res["design"].update({"prereg": "PREREG_PHASE_4.md section 10; addendum section 2.5", "seeds": a.seeds,
                          "seed0": SEED0, "scenario": "bull_trap"})
    stages = [s.strip() for s in a.stages.split(",")]

    def save():
        json.dump(res, open(jp, "w", encoding="utf-8"), indent=1, default=str)

    if "fit" in stages:
        res["panel_targets"] = panel_targets()
        res["blowoff_threshold"] = blowoff_threshold_fit()
        pt = res["panel_targets"]
        print(f"[fit] panel on the corrected reference: mania {pt['mania']['ratio_to_clean_calm']:.3f} "
              f"blow-off {pt['blow-off']['ratio_to_clean_calm']:.3f} post-top {pt['post-top']['ratio_to_clean_calm']:.3f}"
              f"  -> blow-off/mania {pt['blowoff_over_mania']:.3f}, post-top/mania {pt['post_top_over_mania']:.3f}",
              flush=True)
        print(f"[fit] blow-off g threshold {res['blowoff_threshold']['g_threshold']:.5f} "
              f"[{res['blowoff_threshold']['p10']:.5f}, {res['blowoff_threshold']['p90']:.5f}] "
              f"n={res['blowoff_threshold']['n']}", flush=True)
        save()

    seeds = list(range(SEED0, SEED0 + a.seeds))
    gthr = res["blowoff_threshold"]["g_threshold"]

    if "blowoff" in stages:
        arms = {"ex_post_v2": {"blowoff_mode": "ex_post"},
                "dynamic_FIT": {"blowoff_mode": "dynamic", "blowoff_g": gthr}}
        res["blowoff"] = {"g_threshold_fit": gthr, "arms": {}}
        for name, cfg in arms.items():
            rows = pmap([(s, cfg) for s in seeds], a.workers)
            rr, agg = ratios(rows)
            bod = np.array([r["blowoff_days"] or 0 for r in rows], float)
            res["blowoff"]["arms"][name] = {
                "ratios": rr, "pooled_variances": agg,
                "blowoff_days_median": float(np.median(bod)),
                "share_of_paths_with_blowoff": float((bod > 0).mean()),
                "n_paths": len(rows)}
            print(f"  blow-off[{name}] days {np.median(bod):.0f}, share {float((bod>0).mean()):.3f}, "
                  f"blow-off/mania {rr.get('blow-off_over_mania')}", flush=True)
        save()

    if "posttop" in stages:
        target = res["panel_targets"]["post_top_over_mania"]
        res["posttop"] = {"target_post_top_over_mania": target,
                          "target_source": "E4.1 corrected run-up calm reference",
                          "incumbent_measured_by_phase3": {"ratio": 1.59, "n": 20,
                                                           "reference": "E3.3's contaminated run-up calm"},
                          "search": []}
        best = None
        for hl in (5, 10, 20, 40, 45, 50, 55, 60, 80, 160):
            cfg = {"post_top_mode": "decay", "blowoff_mode": "dynamic", "blowoff_g": gthr,
                   "post_top_half_life": float(hl)}
            rows = pmap([(s, {**cfg}) for s in seeds[:max(100, a.seeds // 4)]], a.workers)
            rr, _ = ratios(rows)
            row = {"half_life": hl, "post_top_over_mania": rr.get("post-top_over_mania")}
            res["posttop"]["search"].append(row)
            print(f"  post-top[hl={hl}] ratio {row['post_top_over_mania']}", flush=True)
            if row["post_top_over_mania"] is not None and (
                    best is None or abs(row["post_top_over_mania"] - target) < abs(best[1] - target)):
                best = (hl, row["post_top_over_mania"])
        res["posttop"]["best"] = {"half_life": best[0], "ratio": best[1]} if best else None
        _pt = res["panel_targets"]
        _m = _pt["mania"]["ratio_to_clean_calm"]
        res["posttop"]["target_ci_on_ratio"] = [_pt["post-top"]["ci95"][0] / _m,
                                                _pt["post-top"]["ci95"][1] / _m]
        res["posttop"]["v2_linear_arm"] = None
        rows_v2 = pmap([(s, {"post_top_mode": "v2_linear", "blowoff_mode": "dynamic", "blowoff_g": gthr})
                        for s in seeds[:max(100, a.seeds // 4)]], a.workers)
        rr_v2, _ = ratios(rows_v2)
        res["posttop"]["v2_linear_arm"] = {"post_top_over_mania": rr_v2.get("post-top_over_mania"),
                                           "note": "the incumbent linear ramp, for the before/after column"}
        _lo, _hi = res["posttop"]["target_ci_on_ratio"]
        res["posttop"]["verdict_vs_panel_ci"] = (
            "MET" if (best and _lo <= best[1] <= _hi) else "CLOSEST REPORTED")
        res["posttop"]["_old_verdict"] = (
            "MET" if (best and res["panel_targets"].get("post-top") and
                      res["panel_targets"]["post-top"]["ci95"][0] <=
                      best[1] / max(res["panel_targets"]["mania"]["ratio_to_clean_calm"], 1e-9) *
                      res["panel_targets"]["mania"]["ratio_to_clean_calm"] <=
                      res["panel_targets"]["post-top"]["ci95"][1]) else "REPORTED")
        save()

    if "topday" in stages:
        rows = pmap([(s, {"blowoff_mode": "dynamic", "blowoff_g": gthr}) for s in seeds], a.workers)
        off = pd.Series([r["top_day_offset"] for r in rows]).dropna().astype(float)
        res["topday"] = {"n": int(len(off)), "median_offset": (float(off.median()) if len(off) else None),
                         "share_nonzero": (float((off != 0).mean()) if len(off) else None),
                         "p10_p90": ([float(off.quantile(0.1)), float(off.quantile(0.9))] if len(off) else None),
                         "reading": "offset = realised price peak minus the day the hazard fired; a non-zero "
                                    "distribution IS the off-by-one, measured rather than asserted"}
        print(f"  top-day offset: median {res['topday']['median_offset']} "
              f"non-zero on {res['topday']['share_nonzero']} of {res['topday']['n']} topped paths", flush=True)
        save()

    if "xsec" in stages:
        e = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
        xs = e["cross_section"]
        res["multi_asset"] = {
            "common_loading": xs["mean_share_in_drawdown"],
            "p90": xs["p90_share_in_drawdown"], "max": xs["max_share_in_drawdown"],
            "n_names": xs["n_names"],
            "label": "FIT",
            "definition": xs["definition"],
            "replaces": "the v2 multi-asset SHARED event (every asset in the same event on the same days), "
                        "which forced a cross-sectional drawdown share of 1.0 where the panel's mean is "
                        f"{xs['mean_share_in_drawdown']:.3f} and whose maximum over 25 years is "
                        f"{xs['max_share_in_drawdown']:.3f}"}
        print(f"  multi-asset common loading {xs['mean_share_in_drawdown']:.3f} "
              f"(p90 {xs['p90_share_in_drawdown']:.3f}, max {xs['max_share_in_drawdown']:.3f})", flush=True)
        save()

    res["seconds"] = round(time.time() - t0, 1)
    save()
    print(f"wrote {jp} in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
