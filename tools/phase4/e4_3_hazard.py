"""
E4.3 (PREREG_PHASE_4.md section 5; REG-18): the bubble hazard re-fitted, and the horizon-scaling assumption
decided by measurement rather than stated.

    python -m tools.phase4.e4_3_hazard [--seeds 500] [--pilot 200] [--workers 3]

Phase 3 measured the trigger: at the engine in force the topped share is 8 % against v2's 40-60 % target, and
the CAL (h0, b) = (3e-4, 6.0) was grid-searched against an engine whose x moved four times as far.
PREREG section 5 RETIRES the 40-60 % topped band and the P/V 1.6-2.5 band as targets; the topped share is an
OUTCOME, and the yardstick is the panel's own.

Panel (E4.1, n = 3201 run-ups / 398 stocks): topped share within 200 trading days at a -40 % threshold is
**0.110 [0.0966, 0.1245]**.  REG-18's rule is decidable at this n -- the fallback branch it registers for
n < 30 is not needed.

Three mappings of GSY's two-year, industry-level crash probabilities to a daily single-stock hazard
h_t = h0 exp(b x_t):

  A  no time scaling: the cumulative hazard over the mania equals the GSY probability at the peak run-up
  B  scaled by (mania length / 504 trading days)
  C  h0 AND b fitted directly on the panel's own run-ups; GSY used only as the industry cross-check

b under A and B comes from a logit of GSY's crash indicator on the log run-up through their three published
points (20 / 53 / 80 % at 50 / 100 / 150 % net-of-market run-ups; read).  The horizon scaling is DESIGN and is
bracketed {0.5x, 1x, 2x}.

h0 is not stipulated under any mapping: a pilot with the hazard switched off records E[sum_t exp(b x_t)] over
the mania window, and h0 = -ln(1 - P_target) / that expectation.

Rule (REG-18): adopt the mapping whose topped share lies inside the panel's CI.  The uncapped mania run is
included (item 41).  `tools/calibrate_hazard.py`'s arbitrary score and rejection penalty are not used.

Output: docs/env_v2/generated/v2_1/e4_3/{hazard.json, hazard.md}
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
OUT = os.path.join(GEN, "e4_3")
SEED0 = 230000
PILOT_SEED0 = 231000
GSY_RUNUP = [0.50, 1.00, 1.50]        # net-of-market run-ups (GSY 2019, JFE, read)
GSY_P = [0.20, 0.53, 0.80]            # crash probability within two years, crash = >= 40 % drawdown
GSY_WINDOW_DAYS = 504                 # two years of trading days
SCHED = "v21"                         # the schedule this module measures, PINNED (see addendum section 5)
N_BOOT = 2000


def logit_fit(x, y, w=None, iters=60):
    X = np.column_stack([np.ones(len(x)), np.asarray(x, float)])
    y = np.asarray(y, float)
    beta = np.zeros(2)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-X @ beta))
        W = np.clip(p * (1 - p), 1e-9, None)
        beta = beta + np.linalg.solve(X.T @ (X * W[:, None]) + 1e-9 * np.eye(2), X.T @ (y - p))
    return float(beta[0]), float(beta[1])


def gsy_slope():
    x = np.log(1.0 + np.array(GSY_RUNUP))
    y = np.log(np.array(GSY_P) / (1 - np.array(GSY_P)))
    b, a = np.polyfit(x, y, 1)
    fitted = [float(1 / (1 + math.exp(-(a + b * xi)))) for xi in x]
    return float(a), float(b), fitted


def panel_fit():
    ru = pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    d = ru[ru["topped"].notna()].copy()
    lr = np.log(pd.to_numeric(d["runup"], errors="coerce").to_numpy(float))
    y = d["topped"].astype(bool).to_numpy(float)
    a, b = logit_fit(lr, y)
    tick = d["ticker"].to_numpy()
    stocks = np.array(sorted(set(tick.tolist())))
    idx_by = {t: np.where(tick == t)[0] for t in stocks}
    rng = np.random.default_rng(400050)
    bs = [float(y[np.concatenate([idx_by[t] for t in rng.choice(stocks, len(stocks), replace=True)])].mean())
          for _ in range(N_BOOT)]
    return {"intercept": a, "b": b, "topped_share": float(y.mean()),
            "topped_ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
            "n_episodes": int(len(d)), "n_stocks": int(len(stocks)),
            "median_runup": float(pd.to_numeric(d["runup"], errors="coerce").median()),
            "median_runup_len": float(pd.to_numeric(d["runup_len"], errors="coerce").median()),
            "horizon_days": 200, "crash_threshold": -0.40,
            "survivorship": "REG-15: the survivor panel understates crash frequency and depth, so this share "
                            "is a LOWER bound on the true single-stock rate"}


def _pilot(args):
    """One bull-trap path with the hazard effectively OFF: records sum_t exp(b x_t) over the mania run and the
    realised peak run-up, so h0 can be solved rather than stipulated."""
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    seed, b = args
    # PIN the schedule being measured.  The first pass did not, so it silently measured the v2 ranges and its
    # numbers were then quoted as deployed properties (PREREG_PHASE_4_ADDENDUM section 5).
    env = SyntheticMarketEnv("bull_trap", 200, seed,
                             config={"hazard_h0": 0.0, "hazard_b": float(b), "schedule_mode": SCHED})
    d = env.data[env.data["asset"] == 0]
    ph = d["phase"].to_numpy(object)
    x = d["x"].to_numpy(float)
    p = d["price"].to_numpy(float)
    m = np.isin(ph, ["mania", "blow-off"])
    if not m.any():
        return None
    s = float(np.exp(np.clip(b * x[m], -50, 50)).sum())
    return {"seed": seed, "sum_exp_bx": s, "mania_days": int(m.sum()),
            "peak_runup": float(np.nanmax(p) / p[0]), "max_x": float(np.nanmax(x[m]))}


def _run(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    seed, h0, b = args
    env = SyntheticMarketEnv("bull_trap", 200, seed,
                             config={"hazard_h0": float(h0), "hazard_b": float(b), "schedule_mode": SCHED})
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    x = d["x"].to_numpy(float)
    V = d["fundamental_value"].to_numpy(float)
    meta = env.event_meta
    ph = d["phase"].to_numpy(object)
    mania = np.isin(ph, ["mania", "blow-off"])
    out = {"seed": seed, "topped": bool(meta.get("topped")), "top_day": meta.get("top_day"),
           "top_day_realised": meta.get("top_day_realised"), "top_day_offset": meta.get("top_day_offset"),
           "attempts": int(env.attempts), "rejected": int(env.attempts > 1),
           "mania_days": int(mania.sum()), "max_x": float(np.nanmax(x)),
           "peak_pv": float(np.nanmax(p / np.maximum(V, 1e-12))),
           "cap_hits": meta.get("cap_hits"), "cap_binding_share": meta.get("cap_binding_share")}
    # the topped OUTCOME measured the way the panel measures it: a >= 40 % drawdown within 200 days of the top
    td = meta.get("top_day_realised") or meta.get("top_day")
    if td is not None:
        i = int(np.argmax(d["day"].to_numpy(int) >= td))
        seg = p[i:]
        if len(seg) > 1:
            out["post_top_drop"] = float(np.nanmin(seg) / p[i] - 1.0)
            out["topped_panel_rule"] = bool(out["post_top_drop"] <= -0.40)
    return out


def pmap(fn, items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return [r for r in ex.map(fn, items, chunksize=4) if r is not None]


def share_ci(flags):
    f = np.asarray([bool(x) for x in flags], bool)
    n = len(f)
    p = float(f.mean())
    se = math.sqrt(max(p * (1 - p), 1e-12) / max(n, 1))
    return p, [max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)], n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--pilot", type=int, default=200)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    a_gsy, b_gsy, fitted = gsy_slope()
    pan = panel_fit()
    print(f"[fits] GSY b {b_gsy:.4f} (reproduces {['%.2f' % f for f in fitted]}); "
          f"panel b {pan['b']:.4f}, topped {pan['topped_share']:.4f} {pan['topped_ci95']}", flush=True)

    mappings = {}
    # ---- pilots, one per distinct b, with the hazard off
    for tag, b in (("gsy", b_gsy), ("panel", pan["b"])):
        rows = pmap(_pilot, [(s, b) for s in range(PILOT_SEED0, PILOT_SEED0 + a.pilot)], a.workers)
        mania_len = float(np.median([r["mania_days"] for r in rows]))
        mappings[tag] = {"b": b, "E_sum_exp_bx": float(np.mean([r["sum_exp_bx"] for r in rows])),
                         "median_mania_days": mania_len, "n_pilot": len(rows),
                         "median_peak_runup": float(np.median([r["peak_runup"] for r in rows]))}
        print(f"    pilot[{tag}] E[sum exp(b x)] {mappings[tag]['E_sum_exp_bx']:.2f} over "
              f"{mania_len:.0f} mania days, median peak run-up {mappings[tag]['median_peak_runup']:.3f}",
              flush=True)

    def p_gsy(runup):
        return 1.0 / (1.0 + math.exp(-(a_gsy + b_gsy * math.log(max(runup, 1e-6)))))

    def p_panel(runup):
        return 1.0 / (1.0 + math.exp(-(pan["intercept"] + pan["b"] * math.log(max(runup, 1e-6)))))

    arms = {}
    g = mappings["gsy"]
    pnl = mappings["panel"]
    L_over_2y = g["median_mania_days"] / GSY_WINDOW_DAYS
    # A: no scaling.  B: scaled by mania length / two years, bracketed {0.5x, 1x, 2x} (the DESIGN assumption).
    P_A = p_gsy(g["median_peak_runup"])
    arms["A_no_scaling"] = {"b": b_gsy, "P_target": P_A,
                            "h0": -math.log(max(1 - P_A, 1e-9)) / g["E_sum_exp_bx"],
                            "note": "cumulative hazard over the mania equals GSY's probability at the peak run-up"}
    for k in (0.5, 1.0, 2.0):
        P_B = min(P_A * L_over_2y * k, 0.999)
        arms[f"B_scaled_{k:g}x"] = {"b": b_gsy, "P_target": P_B,
                                    "h0": -math.log(max(1 - P_B, 1e-9)) / g["E_sum_exp_bx"],
                                    "note": f"GSY probability scaled by (mania length / 504 d) x {k:g} "
                                            f"(the DESIGN horizon assumption, bracketed as REG-18 requires)"}
    P_C = p_panel(pan["median_runup"])
    arms["C_panel_fit"] = {"b": pan["b"], "P_target": P_C,
                           "h0": -math.log(max(1 - P_C, 1e-9)) / pnl["E_sum_exp_bx"],
                           "note": "h0 AND b fitted on the panel's own run-ups; GSY is the industry cross-check"}
    arms["v2_incumbent"] = {"b": 6.0, "P_target": None, "h0": 0.0003,
                            "note": "the CAL grid search against the OLD engine, kept as the incumbent arm"}

    seeds = list(range(SEED0, SEED0 + a.seeds))
    res = {"design": {"prereg": "PREREG_PHASE_4.md section 5, REG-18", "seeds": a.seeds, "seed0": SEED0,
                      "pilot_seeds": a.pilot, "scenario": "bull_trap", "T": 200,
                      "targets_retired": "the 40-60 % topped band and the P/V 1.6-2.5 band are retired as "
                                         "TARGETS by PREREG section 5; the topped share is an outcome and the "
                                         "yardstick is the panel's own",
                      "gsy": {"runups": GSY_RUNUP, "probabilities": GSY_P, "intercept": a_gsy, "b": b_gsy,
                              "fitted_at_points": fitted, "window_days": GSY_WINDOW_DAYS,
                              "citation": "Greenwood, Shleifer & You (2019, JFE) -- READ; industry level, "
                                          "monthly, crash = >= 40 % drawdown within two years",
                              "transfer_assumption": "the industry-level relation is applied to a single "
                                                     "stock; this is the DESIGN assumption REG-18 exists to "
                                                     "bracket, and the panel fit below is what tests it"}},
           "panel_fit": pan, "pilots": mappings, "arms": {}}
    for name, spec in arms.items():
        rows = pmap(_run, [(s, spec["h0"], spec["b"]) for s in seeds], a.workers)
        df = pd.DataFrame(rows)
        tp, tci, n = share_ci(df["topped"])
        tp2, tci2, _ = share_ci(df.get("topped_panel_rule", df["topped"]).fillna(False))
        inside = bool(pan["topped_ci95"][0] <= tp2 <= pan["topped_ci95"][1])
        pv = pd.to_numeric(df["peak_pv"], errors="coerce")
        off = pd.to_numeric(df.get("top_day_offset"), errors="coerce").dropna()
        res["arms"][name] = {
            **spec, "n_paths": int(len(df)),
            "topped_share_hazard_fired": tp, "ci95": tci,
            "topped_share_panel_rule": tp2, "panel_rule_ci95": tci2,
            "inside_panel_ci": inside, "verdict": "INSIDE" if inside else "OUTSIDE",
            "peak_pv_median": float(pv.median()), "peak_pv_p10_p90": [float(pv.quantile(0.1)), float(pv.quantile(0.9))],
            "rejection_rate": float(df["rejected"].mean()),
            "cap_binding_share_median": float(pd.to_numeric(df["cap_binding_share"], errors="coerce").median()),
            "top_day_offset": {"n": int(len(off)), "median": (float(off.median()) if len(off) else None),
                               "share_nonzero": (float((off != 0).mean()) if len(off) else None)},
        }
        df.to_csv(os.path.join(OUT, f"paths_{name}.csv"), index=False)
        print(f"    {name:18s} h0 {spec['h0']:.3e} b {spec['b']:.3f} -> topped(panel rule) {tp2:.3f} "
              f"{[round(v,3) for v in tci2]}  {'INSIDE' if inside else 'OUTSIDE'}  peakP/V {pv.median():.2f}",
              flush=True)

    winners = [k for k, v in res["arms"].items() if v["verdict"] == "INSIDE" and k != "v2_incumbent"]
    res["decision"] = {
        "rule": "REG-18: adopt the mapping whose topped share lies inside the panel's CI "
                f"{[round(v, 4) for v in pan['topped_ci95']]}",
        "panel_n": f"{pan['n_episodes']} run-ups / {pan['n_stocks']} stocks -- far above REG-18's n < 30 "
                   "fallback threshold, so the rule is decidable and the {0.5x, 1x, 2x} bracket is a "
                   "sensitivity rather than the verdict",
        "mappings_inside": winners,
        "adopted": (winners[0] if len(winners) == 1 else None),
        "note": ("more than one mapping qualifies; the report states which and the team is asked, as the rule "
                 "does not discriminate" if len(winners) > 1 else
                 ("no mapping qualifies; reported as such" if not winners else "")),
    }
    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "hazard.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)

    L = ["# E4.3 - the bubble hazard, re-fitted (REG-18)", "",
         "`python -m tools.phase4.e4_3_hazard` - PREREG_PHASE_4.md section 5.", "",
         "**The 40-60 % topped band and the P/V 1.6-2.5 band are retired as targets.** The yardstick is the "
         "panel's own topped share:", "",
         f"- panel: **{pan['topped_share']:.4f} [{pan['topped_ci95'][0]:.4f}, {pan['topped_ci95'][1]:.4f}]**, "
         f"n = {pan['n_episodes']} run-ups / {pan['n_stocks']} stocks, 200-day horizon, -40 % threshold",
         f"- {pan['survivorship']}", "",
         "## The two slopes", "",
         f"| source | b | topped/crash share | n |", "|---|---|---|---|",
         f"| GSY 2019 (read; industry, 2 y, -40 %) | {b_gsy:.4f} | 20 / 53 / 80 % at 50 / 100 / 150 % | 3 published points |",
         f"| panel (single stock, 200 d, -40 %) | {pan['b']:.4f} | {pan['topped_share']:.4f} | {pan['n_episodes']} / {pan['n_stocks']} |",
         "",
         f"The industry relation is **{b_gsy / pan['b']:.1f}x steeper** than the single-stock one. That gap is "
         "what REG-18's horizon/level transfer assumption has to carry, and it is now measured rather than "
         "assumed.", "",
         "## The mappings", "",
         "| mapping | b | h0 | topped (panel rule) | 95 % CI | inside panel CI | peak P/V median | rejection |",
         "|---|---|---|---|---|---|---|---|"]
    for name, v in res["arms"].items():
        L.append(f"| {name} | {v['b']:.3f} | {v['h0']:.3e} | {v['topped_share_panel_rule']:.3f} | "
                 f"[{v['panel_rule_ci95'][0]:.3f}, {v['panel_rule_ci95'][1]:.3f}] | **{v['verdict']}** | "
                 f"{v['peak_pv_median']:.2f} | {v['rejection_rate']:.3f} |")
    L += ["", "## Decision", "", f"- rule: {res['decision']['rule']}",
          f"- n: {res['decision']['panel_n']}",
          f"- mappings inside the panel CI: **{res['decision']['mappings_inside'] or 'none'}**",
          f"- adopted: **{res['decision']['adopted'] or 'not decided by the rule -- see note'}**",
          (f"- note: {res['decision']['note']}" if res["decision"]["note"] else ""), ""]
    with open(os.path.join(OUT, "hazard.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"wrote {OUT}/hazard.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
