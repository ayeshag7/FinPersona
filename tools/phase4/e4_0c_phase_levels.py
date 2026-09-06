"""
E4.0c (PREREG_PHASE_4_ADDENDUM.md section 2.3): the level question decided CONDITIONAL ON PHASE, with one
estimator applied to both sides.

    python -m tools.phase4.e4_0c_phase_levels [--seeds 500] [--workers 3]

Sections 1 and 2 of the addendum establish that the pooled unconditional cannot decide this: the generator's
phase mix is a design choice (equal numbers of crash / bull-trap / sustained-bull / flat runs) and the panel's
is a fact about the world, so the two pooled figures are not comparable however they are weighted.  What IS
comparable is, for each phase, the realised variance relative to that side's OWN calm.

Both sides use the same estimator throughout: pooled mean of squared daily log returns over the phase's days,
divided by the pooled mean over calm days.  Generator CIs cluster by seed; panel CIs cluster by stock.

Rule (registered, addendum 2.3): the level is accepted for a phase iff the generator's ratio-to-own-calm lies
inside the panel's 95 % CI for the same ratio, AND the generator's pooled calm sd lies inside the panel's
pooled calm sd CI.  mania / blow-off / post-top are REPORTED, not tested: the panel's run-up calm window sits
at a post-crash trough (sd 0.0413 against the drawdown episodes' 0.0217), so the reference does not describe
that population; E4.1 derives a clean one.

Output: docs/env_v2/generated/v2_1/e4_0/phase_levels.{json,md}
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
SEED0 = 216000
N_BOOT = 1000
CRASH_PHASES = ("deterioration", "panic", "stabilisation")
BUBBLE_PHASES = ("mania", "blow-off", "post-top")

from tools.phase4.e4_0_level import _job  # noqa: E402  (same generator job, per-phase sums of squares)


def run(scenario, seeds, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_job, [(scenario, s, None) for s in seeds], chunksize=4))


def gen_phase_ratios(rows, n_boot=N_BOOT, seed=400010):
    """Pooled-mean variance per phase and its ratio to calm, bootstrapped by SEED (path)."""
    phases = sorted({k for r in rows for k in r["per_phase"]})
    S = np.zeros((len(rows), len(phases)))
    N = np.zeros((len(rows), len(phases)))
    for i, r in enumerate(rows):
        for j, p in enumerate(phases):
            if p in r["per_phase"]:
                S[i, j], N[i, j] = r["per_phase"][p]
    def stat(idx):
        s, n = S[idx].sum(axis=0), N[idx].sum(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            v = np.where(n > 0, s / np.maximum(n, 1), np.nan)
        return v
    v0 = stat(np.arange(len(rows)))
    ci = {}
    rng = np.random.default_rng(seed)
    B = np.array([stat(rng.integers(0, len(rows), len(rows))) for _ in range(n_boot)])
    jc = phases.index("calm") if "calm" in phases else None
    out = {}
    for j, p in enumerate(phases):
        col = B[:, j]
        row = {"var": float(v0[j]), "sd": float(math.sqrt(v0[j])) if np.isfinite(v0[j]) else None,
               "days": int(N[:, j].sum()),
               "sd_ci95": [float(math.sqrt(np.nanpercentile(col, 2.5))),
                           float(math.sqrt(np.nanpercentile(col, 97.5)))] if np.isfinite(col).any() else None}
        if jc is not None and p != "calm":
            r0 = v0[j] / v0[jc]
            rb = B[:, j] / B[:, jc]
            row["ratio_to_calm"] = float(r0)
            row["ratio_ci95"] = [float(np.nanpercentile(rb, 2.5)), float(np.nanpercentile(rb, 97.5))]
        out[p] = row
    return out


def panel_phase_ratios(n_boot=N_BOOT, seed=400011):
    """Panel side, same estimator: pooled-mean rv per phase over episodes, ratio to that family's calm,
    bootstrapped by STOCK."""
    dd = pd.read_csv(os.path.join(GEN, "e3_3", "dd_episodes.csv"))
    ru = pd.read_csv(os.path.join(GEN, "e3_3", "ru_episodes.csv"))
    res = {}
    for fam, df, phases in (("drawdown", dd, CRASH_PHASES), ("runup", ru, BUBBLE_PHASES)):
        d = df[np.isfinite(df["rv_calm"])].copy()
        for p in phases:
            d["rv_" + p] = d["m_" + p] * d["rv_calm"]
        tick = d["ticker"].to_numpy()
        stocks = np.array(sorted(set(tick.tolist())))
        idx_by = {t: np.where(tick == t)[0] for t in stocks}
        cols = {p: d["rv_" + p].to_numpy(float) for p in phases}
        calm = d["rv_calm"].to_numpy(float)

        def stat(rows_idx):
            c = np.nanmean(calm[rows_idx])
            return c, {p: np.nanmean(cols[p][rows_idx]) for p in phases}

        c0, v0 = stat(np.arange(len(d)))
        rng = np.random.default_rng(seed)
        boots = []
        for _ in range(n_boot):
            ss = rng.choice(stocks, len(stocks), replace=True)
            ridx = np.concatenate([idx_by[t] for t in ss])
            boots.append(stat(ridx))
        cb = np.array([b[0] for b in boots])
        fam_out = {"calm": {"var": float(c0), "sd": float(math.sqrt(c0)),
                            "sd_ci95": [float(math.sqrt(np.nanpercentile(cb, 2.5))),
                                        float(math.sqrt(np.nanpercentile(cb, 97.5)))],
                            "n_episodes": int(len(d)), "n_stocks": int(len(stocks))}}
        for p in phases:
            rb = np.array([b[1][p] / b[0] for b in boots])
            fam_out[p] = {"var": float(v0[p]), "sd": float(math.sqrt(v0[p])),
                          "ratio_to_calm": float(v0[p] / c0),
                          "ratio_ci95": [float(np.nanpercentile(rb, 2.5)), float(np.nanpercentile(rb, 97.5))],
                          "n_episodes": int(np.isfinite(cols[p]).sum())}
        res[fam] = fam_out
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)

    print(f"[panel] pooled-mean phase variances, stock bootstrap x {N_BOOT} ...", flush=True)
    pan = panel_phase_ratios()
    print(f"  drawdown calm sd {pan['drawdown']['calm']['sd']:.6f} "
          f"{[round(v, 6) for v in pan['drawdown']['calm']['sd_ci95']]} "
          f"n={pan['drawdown']['calm']['n_episodes']}/{pan['drawdown']['calm']['n_stocks']}", flush=True)

    print(f"[generator] {len(SCENARIOS)} scenarios x {a.seeds} seeds ...", flush=True)
    rows = []
    for i, sc in enumerate(SCENARIOS):
        r = run(sc, range(SEED0 + 1000 * i, SEED0 + 1000 * i + a.seeds), a.workers)
        rows += r
        print(f"    {sc} done ({len(r)} paths)", flush=True)
    gen = gen_phase_ratios(rows)
    print(f"  generator calm sd {gen['calm']['sd']:.6f} {[round(v, 6) for v in gen['calm']['sd_ci95']]} "
          f"days={gen['calm']['days']}", flush=True)

    # ---- the registered rule
    pc = pan["drawdown"]["calm"]
    calm_ok = bool(pc["sd_ci95"][0] <= gen["calm"]["sd"] <= pc["sd_ci95"][1])
    tested = {}
    for p in CRASH_PHASES:
        g, q = gen.get(p), pan["drawdown"][p]
        if not g or "ratio_to_calm" not in g:
            tested[p] = {"verdict": "NO GENERATOR DAYS"}
            continue
        inside = bool(q["ratio_ci95"][0] <= g["ratio_to_calm"] <= q["ratio_ci95"][1])
        tested[p] = {"generator_ratio": g["ratio_to_calm"], "generator_ci95": g["ratio_ci95"],
                     "panel_ratio": q["ratio_to_calm"], "panel_ci95": q["ratio_ci95"],
                     "generator_inside_panel_ci": inside,
                     "verdict": "ACCEPTED" if inside else "OUTSIDE"}
    reported = {}
    for p in BUBBLE_PHASES:
        g, q = gen.get(p), pan["runup"][p]
        reported[p] = {"generator_ratio": (g or {}).get("ratio_to_calm"),
                       "generator_ci95": (g or {}).get("ratio_ci95"),
                       "panel_ratio_on_contaminated_reference": q["ratio_to_calm"],
                       "panel_ci95": q["ratio_ci95"],
                       "status": "REPORTED NOT TESTED - the panel's run-up calm window sits at a post-crash "
                                 "trough (sd %.5f vs the drawdown family's %.5f); E4.1 derives a clean "
                                 "reference" % (pan["runup"]["calm"]["sd"], pan["drawdown"]["calm"]["sd"])}

    res = {"design": {"prereg": "PREREG_PHASE_4_ADDENDUM.md section 2.3", "seeds_per_scenario": a.seeds,
                      "seed0": SEED0, "scenarios": list(SCENARIOS), "n_boot": N_BOOT,
                      "estimator": "pooled mean of squared daily log returns over the phase's days, divided by "
                                   "the same quantity over calm days; generator clustered by seed, panel by stock"},
           "panel": pan, "generator": gen,
           "calm_level": {"generator_sd": gen["calm"]["sd"], "generator_ci95": gen["calm"]["sd_ci95"],
                          "panel_sd": pc["sd"], "panel_ci95": pc["sd_ci95"],
                          "ratio": gen["calm"]["sd"] / pc["sd"],
                          "generator_inside_panel_ci": calm_ok,
                          "panel_s_A_full_sample": json.load(open(os.path.join(GEN, "e3_4", "block.json"),
                                                                  encoding="utf-8"))["s_A"]},
           "tested_crash_phases": tested, "reported_bubble_phases": reported}
    n_out = sum(1 for v in tested.values() if v.get("verdict") == "OUTSIDE")
    res["verdict"] = {
        "calm_level_accepted": calm_ok,
        "crash_phases_outside": [p for p, v in tested.items() if v.get("verdict") == "OUTSIDE"],
        "level_double_count": ("WITHDRAWN - calm levels agree and the crash-side ratios that are tested agree; "
                               "the pooled +30.5 % is mean-vs-median in the calm half and the benchmark's own "
                               "scenario mix in the deployed half"
                               if calm_ok and n_out == 0 else
                               "PARTIAL - calm level %s; %d crash phase(s) outside the panel CI, handed to the "
                               "experiment that owns the shape (E4.2/E4.6), not to the level"
                               % ("accepted" if calm_ok else "REJECTED", n_out)),
        "anchor": "KEPT" if calm_ok else "REFERRED TO THE TEAM"}
    res["seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT, "phase_levels.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    L = ["# E4.0c - the level decided conditional on phase", "",
         "`python -m tools.phase4.e4_0c_phase_levels` - PREREG_PHASE_4_ADDENDUM.md section 2.3.", "",
         f"Generator: {a.seeds} seeds x 4 scenarios, seeds {SEED0}+. Panel: analysis set A.",
         "One estimator on both sides; generator CIs cluster by seed, panel CIs by stock.", "",
         "## Calm level", "",
         f"| side | pooled calm sd | 95 % CI | n |", "|---|---|---|---|",
         f"| generator | {gen['calm']['sd']:.6f} | [{gen['calm']['sd_ci95'][0]:.6f}, {gen['calm']['sd_ci95'][1]:.6f}] | {gen['calm']['days']:,} days |",
         f"| panel (drawdown episodes) | {pc['sd']:.6f} | [{pc['sd_ci95'][0]:.6f}, {pc['sd_ci95'][1]:.6f}] | {pc['n_episodes']} episodes / {pc['n_stocks']} stocks |",
         "",
         f"Ratio {res['calm_level']['ratio']:.4f}; generator inside the panel CI: **{calm_ok}**. "
         f"The panel's full-sample s_A is {res['calm_level']['panel_s_A_full_sample']:.6f}.", "",
         "## Crash-side phases, ratio to own calm (tested)", "",
         "| phase | generator | 95 % CI | panel | 95 % CI | verdict |", "|---|---|---|---|---|---|"]
    for p, v in tested.items():
        if "generator_ratio" not in v:
            L.append(f"| {p} | - | - | - | - | {v['verdict']} |"); continue
        L.append(f"| {p} | {v['generator_ratio']:.3f} | [{v['generator_ci95'][0]:.3f}, {v['generator_ci95'][1]:.3f}] | "
                 f"{v['panel_ratio']:.3f} | [{v['panel_ci95'][0]:.3f}, {v['panel_ci95'][1]:.3f}] | **{v['verdict']}** |")
    L += ["", "## Bubble-side phases (reported, not tested)", "",
          f"The panel's run-up calm reference has sd {pan['runup']['calm']['sd']:.6f} against the drawdown "
          f"family's {pan['drawdown']['calm']['sd']:.6f} - it sits at a post-crash trough, which is the "
          "contamination PREREG_PHASE_3_ADDENDUM section 1 identified. E4.1 derives a clean reference.", "",
          "| phase | generator ratio | panel ratio (contaminated ref) |", "|---|---|---|"]
    for p, v in reported.items():
        gr = "-" if v["generator_ratio"] is None else f"{v['generator_ratio']:.3f}"
        L.append(f"| {p} | {gr} | {v['panel_ratio_on_contaminated_reference']:.3f} |")
    L += ["", "## Verdict", "", f"- calm level accepted: **{calm_ok}**",
          f"- crash phases outside the panel CI: **{res['verdict']['crash_phases_outside'] or 'none'}**",
          f"- Phase 3's level double-count: **{res['verdict']['level_double_count']}**",
          f"- anchor: **{res['verdict']['anchor']}**", ""]
    with open(os.path.join(OUT, "phase_levels.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("\n".join(L[-6:]), flush=True)
    print(f"wrote {OUT}/phase_levels.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
