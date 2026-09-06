"""
E4.9 -- every Phase-4 number re-measured ON THE DEPLOYED STATE, with no configuration overrides.

    python -m tools.phase4.e4_9_deployed [--seeds 500] [--workers 3] [--stages ...]

WHY THIS EXISTS.  A timestamp audit of the phase's own outputs found that `envs/v2/params/events.json` was
written at 14:47:39, while `e4_3/hazard.json` (14:18), `e4_5/control.json` (14:41) and `e4_8/labels.json`
(14:45) were all produced BEFORE it -- and none of those three tools pins `schedule_mode`, so all three ran
under the v2 schedule (events.json absent => events_params.PRESENT is False => the v2 DESIGN ranges).  Their
numbers were then quoted in the parameter file and the phase report as properties of the DEPLOYED state.

That is an inference, not a measurement, and the Phase-4 checklist already contradicted one instance of it
(topped share 15 % deployed against E4.3's calibrated 0.108) which the report explained away as "a different
seed block" without testing the explanation.

This module measures, on the state that is actually in force:
  hazard    the topped share under the panel's own rule, against the panel CI the mapping was adopted by
  posttop   the post-top/mania realised variance ratio, against the panel target the half-life was fitted to
  blowoff   the blow-off/mania ratio, blow-off day counts and the share of paths carrying the label
  control   the incumbent definition's rejection rate, realised sd(x) and accepted-vs-rejected selection
  crash     rise time, depth and duration, as a consistency check against e4_2's pinned v21_empirical arm

Nothing here is a re-calibration.  It is the measurement that says whether a re-calibration is needed.

Output: docs/env_v2/generated/v2_1/e4_9/deployed.{json,md}
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
OUT = os.path.join(GEN, "e4_9")
SEED_BULL = 280000
SEED_CRASH = 281000
SEED_SB = 282000
N_BOOT = 2000


def _bull(args):
    """One bull-trap path on the DEPLOYED configuration.  No config is passed at all."""
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from tools.phase3.episodes import _rv
    seed = args
    env = SyntheticMarketEnv("bull_trap", 200, seed)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    V = d["fundamental_value"].to_numpy(float)
    day = d["day"].to_numpy(int)
    ph = d["phase"].to_numpy(object)[1:]
    r = np.diff(np.log(p))
    m = env.event_meta
    ev = int(env.schedule.event_start)
    out = {"seed": seed, "topped_hazard": bool(m.get("topped")),
           "top_day": m.get("top_day"), "top_day_realised": m.get("top_day_realised"),
           "top_day_offset": m.get("top_day_offset"),
           "blowoff_days": m.get("blowoff_days"), "mania_days": m.get("mania_days"),
           "cap_binding_share": m.get("cap_binding_share"),
           "attempts": int(env.attempts), "rejected": int(env.attempts > 1),
           "peak_pv": float(np.nanmax(p / np.maximum(V, 1e-12))),
           "schedule_mode": env.schedule.mode, "kappa": float(env.schedule.kappa)}
    calm = _rv(r, 0, max(ev - 2, 0), min_n=30)
    out["rv_calm"] = float(calm) if np.isfinite(calm) else None
    for k in ("mania", "blow-off", "post-top"):
        sel = ph == k
        if sel.sum() >= 10:
            out["rv_" + k] = float(np.mean(r[sel] ** 2))
            out["n_" + k] = int(sel.sum())
    # the topped OUTCOME by the panel's own rule: a >= 40 % drawdown within 200 days of the realised top
    td = m.get("top_day_realised") or m.get("top_day")
    if td is not None:
        i = int(np.argmax(day >= td))
        seg = p[i:]
        if len(seg) > 1:
            out["post_top_drop"] = float(np.nanmin(seg) / p[i] - 1.0)
            out["topped_panel_rule"] = bool(out["post_top_drop"] <= -0.40)
    return out


def _crash(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from tools.phase3.episodes import drawdown_episodes, rise_decay, _rv
    seed = args
    env = SyntheticMarketEnv("crash", 200, seed, crash_discount=0.70)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    r = np.diff(np.log(p))
    s = env.schedule
    ev = int(s.event_start)
    out = {"seed": seed, "det_len": int(s.det_len), "panic_len": int(s.panic_len),
           "front_load": float(s.front_load), "delta": float(s.delta), "D_V": float(s.D_V),
           "setup_len": int(s.setup_len), "schedule_mode": s.mode,
           "rejected": int(env.attempts > 1)}
    rv_calm = _rv(r, 0, max(ev - 2, 0), min_n=30)
    if np.isfinite(rv_calm) and rv_calm > 0:
        eps = [e for e in drawdown_episodes(p, depth_thr=-0.30) if (e["trough"] - e["peak"]) <= 126]
        if eps:
            e0 = min(eps, key=lambda e: e["depth"])
            out["depth"] = float(e0["depth"])
            out["duration"] = int(e0["trough"] - e0["peak"])
            rd = rise_decay(e0, p, r, rv_calm)
            if rd:
                out["rise"] = rd["rise"]
                out["onset_lag_before_event"] = int(ev - rd["onset"])
    return out


def _sb(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from envs.v2.generator import check_validity
    seed = args
    env = SyntheticMarketEnv("sustained_bull", 200, seed, config={"reject": False})
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    x = d["x"].to_numpy(float)
    V = d["fundamental_value"].to_numpy(float)
    iv = (d["implied_volatility"].to_numpy(float) if "implied_volatility" in d
          else np.full(len(p), np.nan))
    r = np.diff(np.log(p))
    reason = check_validity(env.result)
    return {"seed": seed, "accepted": reason is None, "reason": reason,
            "sd_r": float(np.std(r, ddof=1)),
            "acf1": float(np.corrcoef(r[:-1], r[1:])[0, 1]) if len(r) > 3 else float("nan"),
            "iv_mean": float(np.nanmean(iv)), "sd_x": float(np.std(x, ddof=1)),
            "mean_x": float(np.mean(x)), "V_growth": float(V[-1] / V[0])}


def pmap(fn, items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items, chunksize=4))


def share_ci(flags, n_boot=N_BOOT, seed=400090):
    f = np.asarray([bool(x) for x in flags], bool)
    n = len(f)
    if n == 0:
        return None, None, 0
    rng = np.random.default_rng(seed)
    bs = [float(f[rng.integers(0, n, n)].mean()) for _ in range(n_boot)]
    return float(f.mean()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], n


def pooled_ratio(rows, num, den, n_boot=N_BOOT, seed=400091):
    """Pooled-mean variance ratio with a path-cluster bootstrap."""
    pairs = [(r.get("rv_" + num), r.get("n_" + num), r.get("rv_" + den), r.get("n_" + den))
             for r in rows]
    pairs = [(a, b, c, d) for a, b, c, d in pairs if a is not None and c is not None]
    if len(pairs) < 20:
        return None, None, len(pairs)
    A = np.array([[a * b, b, c * d, d] for a, b, c, d in pairs], float)
    pt = (A[:, 0].sum() / A[:, 1].sum()) / (A[:, 2].sum() / A[:, 3].sum())
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(A), len(A))
        S = A[idx]
        bs.append((S[:, 0].sum() / S[:, 1].sum()) / (S[:, 2].sum() / S[:, 3].sum()))
    return float(pt), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], len(pairs)


def boot_median(v, n_boot=N_BOOT, seed=400092):
    v = np.asarray([x for x in v if x is not None and np.isfinite(x)], float)
    if len(v) < 20:
        return None, None, len(v)
    rng = np.random.default_rng(seed)
    b = [float(np.median(v[rng.integers(0, len(v), len(v))])) for _ in range(n_boot)]
    return float(np.median(v)), [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))], int(len(v))


def ks(a, b):
    a = np.sort(np.asarray([v for v in a if np.isfinite(v)], float))
    b = np.sort(np.asarray([v for v in b if np.isfinite(v)], float))
    if len(a) < 3 or len(b) < 3:
        return float("nan")
    allv = np.concatenate([a, b])
    return float(np.max(np.abs(np.searchsorted(a, allv, "right") / len(a) -
                               np.searchsorted(b, allv, "right") / len(b))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    from envs.v2 import events_params as EP
    if not EP.PRESENT:
        raise SystemExit("events.json is absent: this module measures the DEPLOYED state and there is none")

    e41 = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    e43 = json.load(open(os.path.join(GEN, "e4_3", "hazard.json"), encoding="utf-8"))
    e48 = json.load(open(os.path.join(GEN, "e4_8", "labels.json"), encoding="utf-8"))
    e45 = json.load(open(os.path.join(GEN, "e4_5", "control.json"), encoding="utf-8"))
    panel_topped = e41["runups"]["topped_share_200d"]
    panel_pt_over_mania = e48["panel_targets"]["post_top_over_mania"]
    panel_bo_over_mania = e48["panel_targets"]["blowoff_over_mania"]

    res = {"design": {"purpose": "every Phase-4 number re-measured on the DEPLOYED state, no config overrides",
                      "seeds": a.seeds, "seed_bull": SEED_BULL, "seed_crash": SEED_CRASH, "seed_sb": SEED_SB,
                      "n_boot": N_BOOT,
                      "deployed": {"schedule_mode": "v21 (events.json present)",
                                   "hazard": {"mapping": EP.HAZARD_MAPPING, "h0": EP.HAZARD_H0,
                                              "b": EP.HAZARD_B},
                                   "blowoff": {"mode": EP.BLOWOFF_MODE, "g": EP.BLOWOFF_G_THRESHOLD},
                                   "post_top": {"mode": EP.POST_TOP_MODE, "half_life": EP.POST_TOP_HALF_LIFE},
                                   "control": EP.CONTROL_DEF, "dynamics": EP.DYNAMICS},
                      "why": "e4_3, e4_5 and e4_8 were produced BEFORE events.json existed and none of those "
                             "tools pins schedule_mode, so all three ran under the v2 schedule; their numbers "
                             "were nevertheless quoted as deployed properties"},
           "as_calibrated_vs_deployed": {}}

    # ------------------------------------------------------------------ bull-trap
    print(f"[bull] {a.seeds} seeds on the deployed state ...", flush=True)
    B = pmap(_bull, list(range(SEED_BULL, SEED_BULL + a.seeds)), a.workers)
    assert all(r["schedule_mode"] == "v21" for r in B), "the deployed schedule is not v21"
    tp, tci, n = share_ci([r.get("topped_panel_rule", False) for r in B])
    th, thci, _ = share_ci([r["topped_hazard"] for r in B])
    pt_r, pt_ci, n_pt = pooled_ratio(B, "post-top", "mania")
    bo_r, bo_ci, n_bo = pooled_ratio(B, "blow-off", "mania")
    pv, pv_ci, _ = boot_median([r["peak_pv"] for r in B])
    bod = np.array([r["blowoff_days"] or 0 for r in B], float)
    res["as_calibrated_vs_deployed"]["hazard_topped_share"] = {
        "as_calibrated_e4_3": e43["arms"]["A_no_scaling"]["topped_share_panel_rule"],
        "deployed": tp, "deployed_ci95": tci, "n": n,
        "panel_target": panel_topped["point"], "panel_ci95": panel_topped["ci95"],
        "inside_panel_ci_as_calibrated": e43["arms"]["A_no_scaling"]["inside_panel_ci"],
        "inside_panel_ci_deployed": bool(panel_topped["ci95"][0] <= tp <= panel_topped["ci95"][1]),
        "topped_share_hazard_fired_deployed": th,
        "verdict": None}
    h = res["as_calibrated_vs_deployed"]["hazard_topped_share"]
    h["verdict"] = ("HOLDS" if h["inside_panel_ci_deployed"] else
                    "DOES NOT HOLD ON THE DEPLOYED STATE -- the adopted mapping must be re-calibrated under "
                    "the v21 schedule, not re-labelled")
    res["as_calibrated_vs_deployed"]["post_top_ratio"] = {
        "as_calibrated_e4_8": e48["posttop"]["best"]["ratio"],
        "half_life_in_force": EP.POST_TOP_HALF_LIFE,
        "deployed": pt_r, "deployed_ci95": pt_ci, "n": n_pt,
        "panel_target": panel_pt_over_mania,
        "panel_ci95_on_ratio": e48["posttop"].get("target_ci_on_ratio"),
        "verdict": None}
    p_ = res["as_calibrated_vs_deployed"]["post_top_ratio"]
    lo, hi = (p_["panel_ci95_on_ratio"] or [None, None])
    # The verdict must respect the DEPLOYED estimate's own precision. A point-in-interval rule applied to an
    # estimate whose CI spans half the range is not a test -- it is a coin flip dressed as one. The bull arm
    # contributes only the paths that carry both a mania and a post-top segment, so n here is a fraction of
    # the seed count and the interval is wide; e4_11 measures the same quantity at 1500 seeds per arm.
    target = e48["panel_targets"]["post_top_over_mania"]
    contains = bool(pt_ci and pt_ci[0] <= target <= pt_ci[1])
    point_inside = bool(lo is not None and pt_r is not None and lo <= pt_r <= hi)
    p_["deployed_ci_contains_panel_target"] = contains
    p_["point_inside_panel_ci"] = point_inside
    p_["n_paths_contributing"] = n_pt
    if point_inside:
        p_["verdict"] = "HOLDS"
    elif contains:
        p_["verdict"] = (f"UNDECIDED AT THIS n -- the deployed estimate is {pt_r:.4f} "
                         f"[{pt_ci[0]:.4f}, {pt_ci[1]:.4f}] on {n_pt} contributing paths, and that interval "
                         f"CONTAINS the panel target {target:.4f}. The point sits outside the panel's own "
                         f"narrower CI, but this arm cannot resolve the difference; e4_11's 1500-seed search "
                         f"is the measurement that decides it.")
    else:
        p_["verdict"] = ("DOES NOT HOLD ON THE DEPLOYED STATE -- the deployed CI excludes the panel target; "
                         "the half-life must be re-searched under the v21 schedule")
    res["as_calibrated_vs_deployed"]["blowoff_ratio"] = {
        "deployed": bo_r, "deployed_ci95": bo_ci, "n": n_bo,
        "panel_target": panel_bo_over_mania,
        "blowoff_days_median": float(np.median(bod)),
        "share_of_paths_with_blowoff": float((bod > 0).mean()),
        "note": "the label is alive; the multiplier still sits at mania's value in volatility.json, so a "
                "ratio near 1.0 is the expected consequence and is what needs the closed loop"}
    res["as_calibrated_vs_deployed"]["peak_pv"] = {"deployed_median": pv, "ci95": pv_ci,
                                                  "as_calibrated_e4_3": e43["arms"]["A_no_scaling"]["peak_pv_median"],
                                                  "status": "reported outcome, not a target (PREREG section 5)"}
    off = pd.Series([r["top_day_offset"] for r in B]).dropna().astype(float)
    res["as_calibrated_vs_deployed"]["top_day_offset"] = {
        "n": int(len(off)), "median": (float(off.median()) if len(off) else None),
        "share_nonzero": (float((off != 0).mean()) if len(off) else None)}
    res["as_calibrated_vs_deployed"]["bull_rejection_rate"] = float(np.mean([r["rejected"] for r in B]))
    pd.DataFrame(B).to_csv(os.path.join(OUT, "bull_deployed.csv"), index=False)
    print(f"    topped(panel rule) {tp:.3f} {[round(v,3) for v in tci]} vs as-calibrated "
          f"{h['as_calibrated_e4_3']:.3f}, panel {panel_topped['point']:.3f} "
          f"{[round(v,4) for v in panel_topped['ci95']]} -> {h['verdict'][:40]}", flush=True)
    print(f"    post-top/mania {pt_r} {pt_ci} vs as-calibrated {p_['as_calibrated_e4_8']:.4f}, "
          f"panel {panel_pt_over_mania:.4f} -> {p_['verdict'][:40]}", flush=True)
    print(f"    blow-off/mania {bo_r} (panel {panel_bo_over_mania:.3f}); "
          f"blow-off on {float((bod>0).mean()):.3f} of paths, median {np.median(bod):.0f} d", flush=True)

    # ------------------------------------------------------------------ crash
    print(f"[crash] {a.seeds} seeds on the deployed state ...", flush=True)
    C = pmap(_crash, list(range(SEED_CRASH, SEED_CRASH + a.seeds)), a.workers)
    assert all(r["schedule_mode"] == "v21" for r in C), "the deployed schedule is not v21"
    rise, rise_ci, n_rise = boot_median([r.get("rise") for r in C])
    dep, dep_ci, _ = boot_median([r.get("depth") for r in C])
    dur, dur_ci, _ = boot_median([r.get("duration") for r in C])
    e42 = json.load(open(os.path.join(GEN, "e4_2", "schedule.json"), encoding="utf-8"))
    ref = e42["arms"]["v21_empirical"]
    res["as_calibrated_vs_deployed"]["crash"] = {
        "rise_median_deployed": rise, "rise_ci95": rise_ci, "n": n_rise,
        "rise_median_e4_2_pinned_arm": ref["rise_median"], "rise_ci95_e4_2": ref["rise_ci95"],
        "depth_deployed": dep, "depth_e4_2": ref["depth_median"],
        "duration_deployed": dur, "duration_e4_2": ref["duration_median"],
        "rejection_deployed": float(np.mean([r["rejected"] for r in C])),
        "rejection_e4_2": ref["rejection_rate"],
        "panel_rise_ci": [29.0, 35.0],
        "consistency": ("CONSISTENT with the pinned arm" if (rise_ci and ref["rise_ci95"] and
                        not (rise_ci[1] < ref["rise_ci95"][0] or rise_ci[0] > ref["rise_ci95"][1]))
                        else "INCONSISTENT with the pinned arm"),
        "criterion": ("MET" if (rise_ci and not (rise_ci[1] < 29 or rise_ci[0] > 35)) else "NOT MET")}
    pd.DataFrame(C).to_csv(os.path.join(OUT, "crash_deployed.csv"), index=False)
    cc = res["as_calibrated_vs_deployed"]["crash"]
    print(f"    rise {rise} {rise_ci} vs e4_2's pinned arm {ref['rise_median']} {ref['rise_ci95']} "
          f"-> {cc['consistency']}; criterion {cc['criterion']}", flush=True)

    # ------------------------------------------------------------------ control (incumbent definition)
    print(f"[control] {a.seeds} seeds on the deployed definition {EP.CONTROL_DEF} ...", flush=True)
    S = pmap(_sb, list(range(SEED_SB, SEED_SB + a.seeds)), a.workers)
    acc = [r for r in S if r["accepted"]]
    rej = [r for r in S if not r["accepted"]]
    prev = e45["definitions"][EP.CONTROL_DEF]
    res["as_calibrated_vs_deployed"]["control"] = {
        "definition_in_force": EP.CONTROL_DEF,
        "v_threshold_in_force": EP.CONTROL_V_THRESHOLD,
        "rejection_deployed": float(len(rej) / max(len(S), 1)),
        "rejection_e4_5": prev["rejection_rate"],
        "sd_x_median_deployed": float(np.median([r["sd_x"] for r in S])),
        "sd_x_median_e4_5": prev["i_realised_x"]["sd_x_median"],
        "n_accepted": len(acc), "n_rejected": len(rej),
        "ks_sd_r": (ks([r["sd_r"] for r in acc], [r["sd_r"] for r in rej]) if len(rej) >= 3 else None),
        "ks_iv": (ks([r["iv_mean"] for r in acc], [r["iv_mean"] for r in rej]) if len(rej) >= 3 else None),
        "ks_sd_r_e4_5": prev["ii_selection"].get("sd_r", {}).get("ks"),
        "ks_iv_e4_5": prev["ii_selection"].get("iv_mean", {}).get("ks"),
    }
    pd.DataFrame(S).to_csv(os.path.join(OUT, "control_deployed.csv"), index=False)
    cd = res["as_calibrated_vs_deployed"]["control"]
    print(f"    rejection {cd['rejection_deployed']:.3f} (e4_5 {cd['rejection_e4_5']:.3f}); "
          f"KS sd_r {cd['ks_sd_r']} (e4_5 {cd['ks_sd_r_e4_5']})", flush=True)

    moved = [k for k, v in res["as_calibrated_vs_deployed"].items()
             if isinstance(v, dict) and str(v.get("verdict", "")).startswith("DOES NOT HOLD")]
    undecided = [k for k, v in res["as_calibrated_vs_deployed"].items()
                 if isinstance(v, dict) and str(v.get("verdict", "")).startswith("UNDECIDED")]
    res["undecided_at_this_n"] = undecided
    res["summary"] = {"entries_that_do_not_hold_on_the_deployed_state": moved,
                      "consequence": ("each of these was adopted on a measurement taken under the v2 schedule "
                                      "and must be RE-CALIBRATED under the deployed schedule, not re-labelled"
                                      if moved else
                                      "every adopted value re-measures inside the interval it was adopted by")}
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(OUT, "deployed.json"), "w", encoding="utf-8"), indent=1, default=str)
    print(f"\nENTRIES THAT DO NOT HOLD: {moved or 'none'}", flush=True)
    print(f"wrote {OUT}/deployed.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
