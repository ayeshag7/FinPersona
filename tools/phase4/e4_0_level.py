"""
E4.0 (PREREG_PHASE_4.md sections 1 and 2): the inherited numbers verified before use, and the level anchoring
decided by measurement rather than by preference.

    python -m tools.phase4.e4_0_level [--seeds 200] [--workers 3] [--stages verify,a,b]

Phase 3 reported a confirmed level double-count (+30.5 % on the deployed unconditional) and left the anchor to
the team.  Its diagnostic could not separate two things:

  (1) a real, like-for-like CALM defect -- envs/v2/garch.py::GJRParams.phase_mult returns
      `self.mult.get(phase, 1.0)`, so the six event phases carry FIT multipliers and CALM falls through to a
      STIPULATED 1.0.  Because the six are ratios to the panel's UNCONDITIONAL applied to a base that equals
      the panel's unconditional, every event phase lands at its correct absolute variance and calm is the only
      phase whose level was never measured;
  (2) a SCENARIO-MIX artefact -- the deployed figure pools flat / crash / bull_trap / sustained_bull with
      EQUAL weight, which over-represents crash relative to any real all-day panel.

Stages
  verify  section 1: every inherited figure Phase 4 builds on, re-read from the generated file it cites, and
          40 inherited episode columns recomputed from the panel and required to reproduce.
  a       E4.0a (i) the like-for-like calm comparison, (ii) the FITTED calm multiplier with a stock
          bootstrap, (iii) the scenario-mix decomposition under generator and panel phase weights.
  b       E4.0a (iv) the counterfactual: the same 4-scenario panel with mult['calm'] at the fitted value.

Output: docs/env_v2/generated/v2_1/e4_0/level.{json,md}   (cached per stage; re-runnable)
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
OUT = os.path.join(GEN, "e4_0")
SCENARIOS = ("flat", "crash", "bull_trap", "sustained_bull")
SEED_BASE = 214000          # E4.0a(iii) base arm
SEED_CF = 215000            # E4.0a(iv) counterfactual arm
N_BOOT = 1000
EVENT_PHASES = ("deterioration", "panic", "stabilisation", "mania", "blow-off", "post-top")


# --------------------------------------------------------------------------- generator jobs
def _job(args):
    """One generated path -> realised daily return sd, sd(x), and PER-PHASE sums of squares."""
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    scenario, seed, cfg = args
    # PIN the schedule being measured (PREREG_PHASE_4_ADDENDUM section 5): a measurement tool must state the
    # configuration it measures.  SCHED is set by the caller; E4.0's own runs were taken under "v2" because
    # events.json did not exist yet, and e4_0c re-runs them under "v21" to confirm the finding survives.
    cfg = dict(cfg or {})
    cfg.setdefault("schedule_mode", os.environ.get("FP_SCHED", "v2"))
    kw = {"config": cfg}
    if scenario == "crash":
        env = SyntheticMarketEnv("crash", 200, seed, crash_discount=0.70, **kw)
    else:
        env = SyntheticMarketEnv(scenario, 200, seed, **kw)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    ph = d["phase"].to_numpy(object)[1:]          # phase of the day the return lands on
    r = np.diff(np.log(p))
    per_phase = {}
    for name in set(ph.tolist()):
        m = ph == name
        per_phase[str(name)] = [float((r[m] ** 2).sum()), int(m.sum())]
    return {"scenario": scenario, "seed": seed, "sd_r": float(r.std(ddof=1)),
            "sd_x": float(d["x"].to_numpy(float).std(ddof=1)),
            "n": int(len(r)), "sum2": float((r ** 2).sum()), "per_phase": per_phase,
            "attempts": int(env.attempts), "n_rejections": int(len(env.rejections))}


def run(scenario, seeds, cfg, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_job, [(scenario, s, cfg) for s in seeds], chunksize=4))


def pooled_sd(rows, n_boot=2000, seed=5):
    """Pooled daily sd over paths (sqrt of the pooled mean square) with a path-cluster bootstrap.
    Identical to tools/phase3/e3_9_level_check.py::pooled_sd so the comparison is like for like."""
    n = np.array([r["n"] for r in rows], float)
    s2 = np.array([r["sum2"] for r in rows], float)
    pt = math.sqrt(s2.sum() / n.sum())
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(rows), (n_boot, len(rows)))
    b = np.sqrt(s2[idx].sum(axis=1) / n[idx].sum(axis=1))
    return pt, [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def phase_variances(rows):
    """Realised variance and day count per phase, pooled over paths."""
    agg = {}
    for r in rows:
        for k, (s2, n) in r["per_phase"].items():
            a = agg.setdefault(k, [0.0, 0])
            a[0] += s2
            a[1] += n
    return {k: {"var": (s2 / n if n else float("nan")), "days": n} for k, (s2, n) in agg.items()}


# --------------------------------------------------------------------------- section 1: verification
def verify_inherited():
    """PREREG section 1: every inherited figure re-read from the file it cites; 40 episode columns recomputed."""
    out = {"figures": {}, "columns": {}}

    def _get(path, *keys, default="MISSING"):
        p = os.path.join(GEN, path)
        if not os.path.exists(p):
            return f"FILE MISSING: {path}"
        d = json.load(open(p, encoding="utf-8"))
        for k in keys:
            if isinstance(d, dict) and k in d:
                d = d[k]
            else:
                return default
        return d

    lvl = _get("e3_9/level_check.json")
    out["figures"]["panel_calm_sd"] = {"cited": 0.01703,
                                       "file": lvl["i_panel_calm"]["sd_calm_window"],
                                       "ci": lvl["i_panel_calm"]["ci95"],
                                       "n_episodes": lvl["i_panel_calm"]["n_episodes"],
                                       "n_stocks": lvl["i_panel_calm"]["n_stocks"],
                                       "source": "e3_9/level_check.json i_panel_calm"}
    out["figures"]["deployed_unconditional"] = {"cited": 0.02843,
                                                "file": lvl["iii_deployed_unconditional"]["pooled_sd_r"],
                                                "ci": lvl["iii_deployed_unconditional"]["ci95"],
                                                "excess_pct": lvl["iii_deployed_unconditional"]["excess_over_target_pct"],
                                                "source": "e3_9/level_check.json iii"}
    out["figures"]["flat_pooled_sd"] = {"cited": None,
                                        "file": lvl["iii_deployed_unconditional"]["per_scenario"]["flat"]["pooled_sd_r"],
                                        "ci": lvl["iii_deployed_unconditional"]["per_scenario"]["flat"]["ci95"],
                                        "source": "e3_9/level_check.json iii.per_scenario.flat"}
    cal = _get("e3_4/calibration.json")
    if isinstance(cal, dict):
        out["figures"]["phase_multiplier_targets"] = {"file": cal["targets"], "cis": cal.get("target_cis"),
                                                      "realised": {k: v.get("realised") for k, v in cal.get("verify", {}).items()},
                                                      "inside_ci": {k: v.get("inside_ci") for k, v in cal.get("verify", {}).items()},
                                                      "source": "e3_4/calibration.json"}
        out["figures"]["block_in_force"] = {"file": cal["design"]["block"], "source": "e3_4/calibration.json design.block"}
    ep = _get("e3_3/episodes.json")
    out["figures"]["episodes_json_keys"] = sorted(ep)[:40] if isinstance(ep, dict) else ep

    # ---- inherited columns recomputed from the panel for 40 random episodes
    from tools.phase1.panel import analysis_sets, load_prices
    from tools.phase3.episodes import drawdown_episodes
    dd = pd.read_csv(os.path.join(GEN, "e3_3", "dd_episodes.csv"))
    rng = np.random.default_rng(400002)
    sample = dd.iloc[rng.choice(len(dd), 40, replace=False)].copy()
    A = analysis_sets(write=False)["A"]
    prices = load_prices(A).ffill()
    ok_idx = ok_depth = 0
    bad = []
    for _, row in sample.iterrows():
        t = row["ticker"]
        if t not in prices.columns:
            bad.append({"ticker": t, "why": "ticker not in panel"})
            continue
        p = prices[t].to_numpy(float)
        eps = drawdown_episodes(p)
        match = [e for e in eps if e["peak"] == int(row["peak"]) and e["trough"] == int(row["trough"])]
        if not match:
            bad.append({"ticker": t, "peak": int(row["peak"]), "trough": int(row["trough"]),
                        "why": "episode not reproduced"})
            continue
        ok_idx += 1
        if abs(match[0]["depth"] - float(row["depth"])) <= 1e-10:
            ok_depth += 1
        else:
            bad.append({"ticker": t, "why": "depth differs",
                        "file": float(row["depth"]), "recomputed": match[0]["depth"]})
    out["columns"] = {"n_sampled": 40, "indices_reproduced": ok_idx, "depth_reproduced_to_1e-10": ok_depth,
                      "discrepancies": bad,
                      "rule": "any column that does not reproduce is recomputed for the whole table and the "
                              "discrepancy reported; E4.1 does not build on an unreproduced column",
                      "verdict": "PASS" if (ok_idx == 40 and ok_depth == 40) else "DISCREPANCY"}
    return out


# --------------------------------------------------------------------------- E4.0a
def fitted_calm_multiplier():
    """(ii) m_calm = median over panel drawdown episodes of rv_calm / rv_uncond, stock bootstrap."""
    dd = pd.read_csv(os.path.join(GEN, "e3_3", "dd_episodes.csv"))
    dd = dd[np.isfinite(dd["calm_over_uncond"])]
    by = {t: g["calm_over_uncond"].to_numpy(float) for t, g in dd.groupby("ticker")}
    stocks = np.array(sorted(by))
    rng = np.random.default_rng(400003)
    meds = [np.median(np.concatenate([by[t] for t in rng.choice(stocks, len(stocks), replace=True)]))
            for _ in range(N_BOOT)]
    pt = float(np.median(dd["calm_over_uncond"].to_numpy(float)))
    ci = [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]
    return {"m_calm_variance_ratio": pt, "ci95": ci,
            "sd_ratio": math.sqrt(pt), "sd_ratio_ci95": [math.sqrt(ci[0]), math.sqrt(ci[1])],
            "n_episodes": int(len(dd)), "n_stocks": int(len(stocks)),
            "stipulated_value_in_code": 1.0,
            "one_outside_ci": bool(not (ci[0] <= 1.0 <= ci[1])),
            "definition": "per-episode rv over the pre-event 120-day calm window divided by that stock's "
                          "median rolling-21d RV (the ADDENDUM section 1 unconditional reference) -- the SAME "
                          "reference the six event multipliers are ratios to, so m_calm is the seventh member "
                          "of that family and is directly substitutable into GJRParams.mult",
            "source": "docs/env_v2/generated/v2_1/e3_3/dd_episodes.csv column calm_over_uncond"}


def panel_phase_weights():
    """(iii) the panel's own share of days in each event window, for the mix reweighting."""
    dd = pd.read_csv(os.path.join(GEN, "e3_3", "dd_episodes.csv"))
    ru = pd.read_csv(os.path.join(GEN, "e3_3", "ru_episodes.csv"))
    from tools.phase1.panel import analysis_sets, load_prices
    A = analysis_sets(write=False)["A"]
    prices = load_prices(A).ffill()
    total_days = int(np.isfinite(prices.to_numpy(float)).sum())
    # E3.3's window lengths (tools/phase3/episodes.py): panic 20, deterioration 40, stabilisation 60,
    # mania 40, blow-off 20, post-top 60 trading days per episode
    win = {"deterioration": 40, "panic": 20, "stabilisation": 60}
    win_ru = {"mania": 40, "blow-off": 20, "post-top": 60}
    n_dd = int(np.isfinite(dd["rv_calm"]).sum())
    n_ru = int(np.isfinite(ru["rv_calm"]).sum())
    days = {k: v * n_dd for k, v in win.items()}
    days.update({k: v * n_ru for k, v in win_ru.items()})
    event_days = sum(days.values())
    days["calm"] = max(total_days - event_days, 0)
    w = {k: v / total_days for k, v in days.items()}
    return {"weights": w, "days": days, "total_panel_days": total_days,
            "n_dd_episodes": n_dd, "n_ru_episodes": n_ru,
            "caveat": "window lengths are E3.3's fixed windows, so this is the share of panel days those "
                      "windows cover, not a phase-dating of the whole panel; it is used only to show how "
                      "much of the deployed excess is a scenario-mix artefact"}


def reweight(pv, weights):
    """Pooled sd implied by per-phase variances under a given set of phase weights."""
    tot = sum(w for k, w in weights.items() if k in pv and np.isfinite(pv[k]["var"]))
    if tot <= 0:
        return float("nan")
    v = sum(w * pv[k]["var"] for k, w in weights.items() if k in pv and np.isfinite(pv[k]["var"]))
    return math.sqrt(v / tot)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--stages", default="verify,a,b")
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "level.json")
    res = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    res.setdefault("design", {})
    res["design"].update({"seeds_per_scenario": a.seeds, "seed_base": SEED_BASE, "seed_cf": SEED_CF,
                          "scenarios": list(SCENARIOS), "n_boot": N_BOOT,
                          "prereg": "PREREG_PHASE_4.md sections 1 and 2"})
    stages = [s.strip() for s in a.stages.split(",")]

    def save():
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, default=str)

    if "verify" in stages and "verification" not in res:
        print("[verify] inherited figures and 40 episode columns ...", flush=True)
        res["verification"] = verify_inherited()
        print(f"  columns verdict: {res['verification']['columns']['verdict']}", flush=True)
        save()

    if "a" in stages:
        if "ii_fitted_calm_multiplier" not in res:
            res["ii_fitted_calm_multiplier"] = fitted_calm_multiplier()
            m = res["ii_fitted_calm_multiplier"]
            print(f"[a.ii] fitted m_calm (variance ratio) {m['m_calm_variance_ratio']:.4f} "
                  f"{[round(c, 4) for c in m['ci95']]} n={m['n_episodes']}/{m['n_stocks']} "
                  f"1.0 outside CI: {m['one_outside_ci']}", flush=True)
            save()
        if "base_arm" not in res:
            print(f"[a.iii] base arm: {len(SCENARIOS)} scenarios x {a.seeds} seeds ...", flush=True)
            arm = {}
            for i, sc in enumerate(SCENARIOS):
                rows = run(sc, range(SEED_BASE + 1000 * i, SEED_BASE + 1000 * i + a.seeds), None, a.workers)
                pt, ci = pooled_sd(rows)
                arm[sc] = {"pooled_sd_r": pt, "ci95": ci,
                           "median_sd_x": float(np.median([r["sd_x"] for r in rows])),
                           "mean_attempts": float(np.mean([r["attempts"] for r in rows])),
                           "rejection_rate": float(np.mean([r["n_rejections"] > 0 for r in rows])),
                           "per_phase": phase_variances(rows), "n_paths": len(rows)}
                print(f"    {sc:15s} sd_r {pt:.5f} {[round(c, 5) for c in ci]} "
                      f"sd_x {arm[sc]['median_sd_x']:.4f} rej {arm[sc]['rejection_rate']:.3f}", flush=True)
            res["base_arm"] = arm
            save()
        if "iii_mix" not in res:
            arm = res["base_arm"]
            allrows_pv = {}
            for sc in SCENARIOS:
                for k, v in arm[sc]["per_phase"].items():
                    b = allrows_pv.setdefault(k, [0.0, 0])
                    b[0] += v["var"] * v["days"]
                    b[1] += v["days"]
            pv = {k: {"var": s2 / n, "days": n} for k, (s2, n) in allrows_pv.items() if n}
            gen_w = {k: v["days"] / sum(x["days"] for x in pv.values()) for k, v in pv.items()}
            pw = panel_phase_weights()
            blk = json.load(open(os.path.join(GEN, "e3_4", "block.json"), encoding="utf-8"))
            equal_mix = math.sqrt(np.mean([arm[sc]["pooled_sd_r"] ** 2 for sc in SCENARIOS]))
            res["iii_mix"] = {
                "target_s_A": blk["s_A"],
                "pooled_sd_equal_scenario_weights": float(equal_mix),
                "excess_equal_pct": float(100 * (equal_mix / blk["s_A"] - 1)),
                "per_phase_pooled": pv,
                "generator_phase_weights_equal_mix": gen_w,
                "panel_phase_weights": pw,
                "pooled_sd_under_panel_phase_weights": float(reweight(pv, pw["weights"])),
                "excess_panel_weighted_pct": float(100 * (reweight(pv, pw["weights"]) / blk["s_A"] - 1)),
                "reading": "the difference between the equal-weight and panel-weight figures is the part of "
                           "Phase 3's +30.5 % that is a SCENARIO-MIX artefact rather than a generator defect",
            }
            print(f"[a.iii] equal-mix {equal_mix:.5f} ({res['iii_mix']['excess_equal_pct']:+.1f} %) vs "
                  f"panel-weighted {res['iii_mix']['pooled_sd_under_panel_phase_weights']:.5f} "
                  f"({res['iii_mix']['excess_panel_weighted_pct']:+.1f} %) against target {blk['s_A']:.5f}",
                  flush=True)
            save()
        if "i_calm_like_for_like" not in res:
            lvl = json.load(open(os.path.join(GEN, "e3_9", "level_check.json"), encoding="utf-8"))
            gen = res["base_arm"]["flat"]
            pan = lvl["i_panel_calm"]
            disjoint = gen["ci95"][0] > pan["ci95"][1] or gen["ci95"][1] < pan["ci95"][0]
            res["i_calm_like_for_like"] = {
                "generator_flat_pooled_sd": gen["pooled_sd_r"], "generator_ci95": gen["ci95"],
                "panel_calm_sd": pan["sd_calm_window"], "panel_ci95": pan["ci95"],
                "ratio": gen["pooled_sd_r"] / pan["sd_calm_window"],
                "n_generator_paths": gen["n_paths"], "n_panel_episodes": pan["n_episodes"],
                "n_panel_stocks": pan["n_stocks"],
                "cis_disjoint": bool(disjoint),
                "verdict": "CONFIRMED" if disjoint else "NOT CONFIRMED",
                "rule": "PREREG section 2 E4.0a(i): confirmed iff the two 95 % CIs are disjoint"}
            print(f"[a.i] generator calm {gen['pooled_sd_r']:.5f} vs panel calm {pan['sd_calm_window']:.5f} "
                  f"ratio {res['i_calm_like_for_like']['ratio']:.3f} disjoint={disjoint}", flush=True)
            save()

    if "b" in stages and "iv_counterfactual" not in res:
        from envs.v2.volatility_params import MULT as VMULT
        m_fit = res["ii_fitted_calm_multiplier"]["m_calm_variance_ratio"]
        mult_cf = {**{k: float(v) for k, v in VMULT.items()}, "calm": float(m_fit)}
        cfg = {"garch": {"mult": mult_cf}}
        print(f"[b] counterfactual arm with mult['calm'] = {m_fit:.4f} (was the stipulated 1.0) ...", flush=True)
        arm = {}
        for i, sc in enumerate(SCENARIOS):
            rows = run(sc, range(SEED_CF + 1000 * i, SEED_CF + 1000 * i + a.seeds), cfg, a.workers)
            pt, ci = pooled_sd(rows)
            arm[sc] = {"pooled_sd_r": pt, "ci95": ci,
                       "median_sd_x": float(np.median([r["sd_x"] for r in rows])),
                       "rejection_rate": float(np.mean([r["n_rejections"] > 0 for r in rows])),
                       "per_phase": phase_variances(rows), "n_paths": len(rows)}
            print(f"    {sc:15s} sd_r {pt:.5f} sd_x {arm[sc]['median_sd_x']:.4f} "
                  f"rej {arm[sc]['rejection_rate']:.3f}", flush=True)
        blk = json.load(open(os.path.join(GEN, "e3_4", "block.json"), encoding="utf-8"))
        equal_mix = math.sqrt(np.mean([arm[sc]["pooled_sd_r"] ** 2 for sc in SCENARIOS]))
        # realised event-phase ratios under the counterfactual, against E3.3's targets
        allpv = {}
        for sc in SCENARIOS:
            for k, v in arm[sc]["per_phase"].items():
                b = allpv.setdefault(k, [0.0, 0])
                b[0] += v["var"] * v["days"]
                b[1] += v["days"]
        pv = {k: s2 / n for k, (s2, n) in allpv.items() if n}
        uncond = equal_mix ** 2
        cal = json.load(open(os.path.join(GEN, "e3_4", "calibration.json"), encoding="utf-8"))
        ratios = {}
        for k in EVENT_PHASES:
            if k in pv:
                ratios[k] = {"realised_ratio_to_equalmix_uncond": pv[k] / uncond,
                             "target": cal["targets"].get(k), "target_ci": cal["target_cis"].get(k)}
                tci = cal["target_cis"].get(k)
                ratios[k]["inside_target_ci"] = bool(tci and tci[0] <= pv[k] / uncond <= tci[1])
        res["iv_counterfactual"] = {
            "mult_calm_applied": m_fit, "arm": arm,
            "pooled_sd_equal_scenario_weights": float(equal_mix),
            "target_s_A": blk["s_A"], "excess_pct": float(100 * (equal_mix / blk["s_A"] - 1)),
            "event_ratios_before_recalibration": ratios,
            "note": "these ratios are BEFORE the one closed-loop re-calibration the pre-registration allows; "
                    "the adoption rule (PREREG section 2 E4.0b clause 2) is evaluated AFTER that re-calibration"}
        print(f"[b] counterfactual equal-mix {equal_mix:.5f} ({res['iv_counterfactual']['excess_pct']:+.1f} %) "
              f"vs target {blk['s_A']:.5f}", flush=True)
        save()

    res["seconds"] = round(time.time() - t0, 1)
    save()
    print(f"wrote {path} in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
