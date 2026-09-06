"""
E4.6 (PREREG_PHASE_4.md section 8; REG-8): the four event-dynamics formulations, all implemented, all run,
decided by the pre-registered rule.

    python -m tools.phase4.e4_6_dynamics [--seeds 500] [--workers 3] [--out DIR]

  A  tracking gain lambda (the incumbent), swept over {0.02, 0.05, 0.10, 0.25}
  B  shifted perceived fundamental p* with a regime-specific pull phi_regime FIT from the panel
  C  scripted drift with no feedback plus rejection
  D  unscripted regime switching: the belief shift is DRAWN per seed, depth and duration are OUTCOMES

Statistics per formulation (500 crash + 500 bull seeds):
  script share    R^2 of the scripted drift d_t on realised delta-x over event-phase days (0 for D by
                  construction -- there is no scripted path to regress on)
  coverage        share of paths whose peak-to-trough depth AND duration fall inside E4.1's P10-P90
  rejection rate  share of attempts rejected by check_validity
  plus the realised depth/duration/rise and the phase variance ratios

Adoption rule (REG-8, unchanged): adopt the formulation with the LOWEST script share among those whose
coverage is >= 0.70 (a DESIGN margin below the 0.80 the P10-P90 box gives by construction) and whose
rejection rate is below the ceiling registered in PREREG section 8 as a formula on E4.1's output:

    ceiling = 1 - (share of real panel episodes inside their own P10-P90 on depth and duration jointly)

Registered in advance: any formulation whose coverage 95 % CI straddles 0.70 is reported UNDECIDED, not as a
pass or a fail.  If none qualifies, report the table and stop for D5 -- do not choose.

Output: docs/env_v2/generated/v2_1/e4_6/{dynamics.json, dynamics.md}
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
OUT_DEFAULT = os.path.join(GEN, "e4_6")
SEED_CRASH = 240000
SEED_BULL = 241000
COVERAGE_MIN = 0.70
EVENT_PHASES = ("deterioration", "panic", "stabilisation", "mania", "blow-off", "post-top")


def panel_box():
    """E4.1's P10-P90 box on depth and duration, and the ceiling the pre-registration defines from it."""
    e = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    q = e["panel_families"]["dd30_fast"]["quantiles"]
    box = {"depth": [q["depth"]["p10"], q["depth"]["p90"]],
           "duration": [q["duration"]["p10"], q["duration"]["p90"]]}
    df = pd.read_csv(os.path.join(GEN, "e4_1", "dd30.csv"))
    fast = df[pd.to_numeric(df["duration"], errors="coerce") <= 126]
    d = pd.to_numeric(fast["depth"], errors="coerce")
    u = pd.to_numeric(fast["duration"], errors="coerce")
    ok = d.notna() & u.notna()
    inside = ((d >= box["depth"][0]) & (d <= box["depth"][1]) &
              (u >= box["duration"][0]) & (u <= box["duration"][1]))[ok]
    self_share = float(inside.mean())
    return box, {"panel_self_coverage": self_share, "ceiling": 1.0 - self_share, "n": int(ok.sum()),
                 "rule": "PREREG section 8: ceiling = 1 - (share of real panel episodes inside their own "
                         "P10-P90 on depth and duration jointly)"}


def fit_ranges_grid():
    e2 = json.load(open(os.path.join(GEN, "e4_2", "schedule.json"), encoding="utf-8"))
    return e2["design"]["fit_ranges_grid"]


def phi_regime_fit():
    """phi_regime FIT from the panel: the exponential pull rate that reproduces the panel's own front-loading
    over its own panic length.  With a constant pull phi over a phase of length L, the share of the move
    completed after L/3 is 1 - (1 - phi)^(L/3); setting that equal to the panel's front-loading gives
    phi = 1 - (1 - fl)^(3/L).  Both inputs are E4.1 medians on the fast-crash family."""
    e = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    q = e["panel_families"]["dd30_fast"]["quantiles"]
    fl = float(q["front_load"]["p50"])
    L = float(q["panic_len"]["p50"])
    phi = 1.0 - (1.0 - fl) ** (3.0 / max(L, 1.0))
    # stabilisation pulls over the 60-day post-trough window the panel measures recovery on
    L_stab = 60.0
    fl_stab = float(q["rec60"]["p50"])
    phi_stab = 1.0 - (1.0 - min(fl_stab, 0.99)) ** (3.0 / L_stab)
    return {"panic": float(phi), "stabilisation": float(phi_stab), "default": float(phi),
            "_provenance": {"front_load_p50": fl, "panic_len_p50": L, "rec60_p50": fl_stab,
                            "formula": "phi = 1 - (1 - front_load)^(3 / phase_length)",
                            "source": "e4_1/episodes4.json panel_families.dd30_fast"}}


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    from tools.phase3.episodes import drawdown_episodes, rise_decay, _rv
    scenario, seed, cfg = args
    kw = {"crash_discount": 0.70} if scenario == "crash" else {}
    env = SyntheticMarketEnv(scenario, 200, seed, config=cfg, **kw)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    x = d["x"].to_numpy(float)
    ph = d["phase"].to_numpy(object)
    r = np.diff(np.log(p))
    ev = int(env.schedule.event_start)
    out = {"seed": seed, "scenario": scenario, "attempts": int(env.attempts),
           "rejected": int(env.attempts > 1), "accepted": bool(env.event_meta.get("accepted", True))}
    # ---- script share: R^2 of the RECORDED scripted drift d_t on the realised delta-x over event-phase days.
    # d_t is now recorded on the path (PathResult.drift), so this is measured for every formulation, including
    # B and D which have no target path to reconstruct.  For D the drift is a pull toward a DRAWN belief level,
    # so a non-zero R^2 there is not "script" in the same sense; that is stated in the report rather than
    # zeroed out by construction.
    ev_mask = np.isin(ph[1:], EVENT_PHASES)
    dx = np.diff(x)
    dsc = env.result.drift[0][env.result.day >= 1][:-1]
    m = ev_mask & np.isfinite(dx) & np.isfinite(dsc)
    if m.sum() >= 20 and np.std(dsc[m]) > 1e-15:
        c = np.corrcoef(dsc[m], dx[m])[0, 1]
        out["script_r2"] = float(c ** 2) if np.isfinite(c) else None
    else:
        out["script_r2"] = 0.0
    out["n_event_days"] = int(ev_mask.sum())
    if scenario == "crash":
        rv_calm = _rv(r, 0, max(ev - 2, 0), min_n=30)
        eps = [e for e in drawdown_episodes(p, depth_thr=-0.30) if (e["trough"] - e["peak"]) <= 126]
        if eps:
            e0 = min(eps, key=lambda e: e["depth"])
            out["depth"] = float(e0["depth"])
            out["duration"] = int(e0["trough"] - e0["peak"])
            if np.isfinite(rv_calm) and rv_calm > 0:
                rd = rise_decay(e0, p, r, rv_calm)
                if rd:
                    out["rise"] = rd["rise"]
    else:
        out["topped"] = bool(env.event_meta.get("topped"))
        out["max_x"] = float(np.nanmax(x))
    out["sd_x"] = float(np.std(x, ddof=1))
    return out


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items, chunksize=4))


def share(v):
    v = np.asarray([bool(z) for z in v], bool)
    n = len(v)
    p = float(v.mean()) if n else float("nan")
    se = math.sqrt(max(p * (1 - p), 1e-12) / max(n, 1))
    return p, [max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)], n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", default=OUT_DEFAULT)
    a = ap.parse_args()
    t0 = time.time()
    OUT = a.out
    os.makedirs(OUT, exist_ok=True)
    box, ceil = panel_box()
    RG = fit_ranges_grid()
    phi = phi_regime_fit()
    base = {"schedule_mode": "v21", "schedule_ranges": RG}
    arms = {}
    for lam in (0.02, 0.05, 0.10, 0.25):
        arms[f"A_lam{lam:g}"] = {**base, "lam_panic": lam, "events_dynamics": "A"}
    arms["B_shifted_pstar"] = {**base, "events_dynamics": "B"}
    arms["C_scripted_no_feedback"] = {**base, "events_dynamics": "C"}
    arms["D_unscripted_regime"] = {**base, "events_dynamics": "D"}

    res = {"design": {"prereg": "PREREG_PHASE_4.md section 8, REG-8", "seeds_per_scenario": a.seeds,
                      "seed_crash": SEED_CRASH, "seed_bull": SEED_BULL,
                      "coverage_min": COVERAGE_MIN, "panel_box": box, "ceiling": ceil,
                      "phi_regime_fit": phi,
                      "power": "n = 500 gives 0.78 power against a true coverage of 0.65 at p0 = 0.70 "
                               "(e4_0/power.json PP1); the plan's 200 gives 0.47, which is why this "
                               "pre-registration raised n BEFORE any run"},
           "arms": {}}
    for name, cfg in arms.items():
        cr = pmap([("crash", s, cfg) for s in range(SEED_CRASH, SEED_CRASH + a.seeds)], a.workers)
        bl = pmap([("bull_trap", s, cfg) for s in range(SEED_BULL, SEED_BULL + a.seeds)], a.workers)
        dfc, dfb = pd.DataFrame(cr), pd.DataFrame(bl)
        dfc.to_csv(os.path.join(OUT, f"crash_{name}.csv"), index=False)
        dfb.to_csv(os.path.join(OUT, f"bull_{name}.csv"), index=False)
        d = pd.to_numeric(dfc.get("depth"), errors="coerce")
        u = pd.to_numeric(dfc.get("duration"), errors="coerce")
        ok = d.notna() & u.notna()
        cov_flags = ((d >= box["depth"][0]) & (d <= box["depth"][1]) &
                     (u >= box["duration"][0]) & (u <= box["duration"][1]))[ok]
        cov, cov_ci, n_cov = share(cov_flags)
        rej_c, rej_c_ci, _ = share(dfc["rejected"].astype(bool))
        rej_b, rej_b_ci, _ = share(dfb["rejected"].astype(bool))
        sr = pd.to_numeric(dfc.get("script_r2"), errors="coerce").dropna()
        straddles = bool(cov_ci[0] <= COVERAGE_MIN <= cov_ci[1])
        res["arms"][name] = {
            "script_share_median": (float(sr.median()) if len(sr) else None),
            "script_share_mean": (float(sr.mean()) if len(sr) else None),
            "coverage": cov, "coverage_ci95": cov_ci, "n_coverage": n_cov,
            "coverage_straddles_threshold": straddles,
            "coverage_verdict": ("UNDECIDED" if straddles else ("PASS" if cov >= COVERAGE_MIN else "FAIL")),
            "rejection_crash": rej_c, "rejection_crash_ci95": rej_c_ci,
            "rejection_bull": rej_b, "rejection_bull_ci95": rej_b_ci,
            "rejection_below_ceiling": bool(max(rej_c, rej_b) < ceil["ceiling"]),
            "depth_median": (float(d.median()) if ok.any() else None),
            "duration_median": (float(u.median()) if ok.any() else None),
            "rise_median": float(pd.to_numeric(dfc.get("rise"), errors="coerce").median()),
            "topped_share_bull": float(dfb["topped"].astype(bool).mean()) if "topped" in dfb else None,
            "sd_x_crash_median": float(pd.to_numeric(dfc["sd_x"], errors="coerce").median()),
            "n_paths": {"crash": int(len(dfc)), "bull": int(len(dfb))},
        }
        v = res["arms"][name]
        print(f"  {name:24s} script {str(v['script_share_median'])[:6]:>6s}  cov {cov:.3f} "
              f"[{cov_ci[0]:.3f},{cov_ci[1]:.3f}] {v['coverage_verdict']:9s} rej {rej_c:.3f}/{rej_b:.3f} "
              f"rise {v['rise_median']}", flush=True)

    elig = {k: v for k, v in res["arms"].items()
            if v["coverage_verdict"] == "PASS" and v["rejection_below_ceiling"]}
    undec = [k for k, v in res["arms"].items() if v["coverage_verdict"] == "UNDECIDED"]
    winner = min(elig, key=lambda k: (elig[k]["script_share_median"] if elig[k]["script_share_median"] is not None else 9)) if elig else None
    res["decision"] = {
        "rule": f"adopt the LOWEST script share among formulations with coverage >= {COVERAGE_MIN} "
                f"(DESIGN margin) and rejection below the ceiling {ceil['ceiling']:.3f}",
        "ceiling": ceil, "eligible": sorted(elig), "undecided": undec, "adopted": winner,
        "if_none": "PREREG section 8: if none qualifies, report the table and STOP for D5 -- do not choose",
        "status": ("ADOPTED" if winner else ("STOP FOR D5 - no formulation qualifies" if not undec
                                             else "STOP FOR D5 - no formulation qualifies outright and "
                                                  f"{len(undec)} are undecided at this n")),
    }
    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "dynamics.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)

    L = ["# E4.6 - event dynamics: four formulations (REG-8)", "",
         "`python -m tools.phase4.e4_6_dynamics` - PREREG_PHASE_4.md section 8.", "",
         f"{a.seeds} crash and {a.seeds} bull seeds per formulation. All four run; none was skipped.", "",
         f"Panel box (E4.1 dd30_fast): depth [{box['depth'][0]:.3f}, {box['depth'][1]:.3f}], "
         f"duration [{box['duration'][0]:.0f}, {box['duration'][1]:.0f}].",
         f"Panel self-coverage {ceil['panel_self_coverage']:.3f} (n = {ceil['n']}), so the registered "
         f"rejection ceiling is **{ceil['ceiling']:.3f}**.", "",
         "| formulation | script share | coverage | 95 % CI | verdict | rejection crash | rejection bull | rise | depth |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, v in res["arms"].items():
        L.append(f"| {name} | {('%.3f' % v['script_share_median']) if v['script_share_median'] is not None else '-'} | "
                 f"{v['coverage']:.3f} | [{v['coverage_ci95'][0]:.3f}, {v['coverage_ci95'][1]:.3f}] | "
                 f"**{v['coverage_verdict']}** | {v['rejection_crash']:.3f} | {v['rejection_bull']:.3f} | "
                 f"{v['rise_median']} | {v['depth_median']:.3f} |")
    L += ["", "## Decision", "", f"- rule: {res['decision']['rule']}",
          f"- eligible: **{res['decision']['eligible'] or 'none'}**",
          f"- undecided at this n: **{res['decision']['undecided'] or 'none'}**",
          f"- **{res['decision']['status']}**", "",
          f"- phi_regime FIT from the panel: {json.dumps(phi['_provenance'])}", ""]
    with open(os.path.join(OUT, "dynamics.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"wrote {OUT}/dynamics.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
