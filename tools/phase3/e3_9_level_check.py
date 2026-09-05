"""
E3.9c (PREREG_PHASE_3_ADDENDUM.md section 4.3): the calm-window mapping that PREREG section 3.4 registered as a
reported alternative and never produced, and the level double-count check the rise/decay rule could not perform.

(i)   the panel's crisis-free calm daily sd = sqrt(median over episodes of rv_calm) from e3_3/dd_episodes.csv
      (the pre-event 120-day windows), 1,000-resample bootstrap over stocks, beside E3.1's full-sample 0.0218;
(ii)  the CALM-WINDOW MAPPING's sbar -- the identity re-evaluated with s_A replaced by (i) -- and the sd(x) it
      implies, on 200 flat paths (seeds 212000+) with everything else at the block in force;
(iii) the DEPLOYED unconditional check: the generator's realised daily return sd WITH EVENTS ON over the audit
      scenario mix (flat / crash 0.70 / bull_trap / sustained_bull, 200 seeds each, seeds 213000+), pooled,
      against the 0.0218 the identity targets -- the number V4's free run could not see.

    python -m tools.phase3.e3_9_level_check [--seeds 200] [--workers 3]

Output: docs/env_v2/generated/v2_1/e3_9/level_check.{json,md}
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
OUT = os.path.join(GEN, "e3_9")
SEED_FLAT_CALMMAP = 212000
SEED_MIX = 213000
SCENARIOS = ("flat", "crash", "bull_trap", "sustained_bull")


def _job(args):
    """One generated path -> its realised daily return sd (and sd(x)) over benchmark days."""
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    scenario, seed, cfg = args
    kw = {"config": cfg} if cfg else {}
    if scenario == "crash":
        env = SyntheticMarketEnv("crash", 200, seed, crash_discount=0.70, **kw)
    else:
        env = SyntheticMarketEnv(scenario, 200, seed, **kw)
    d = env.data[env.data["asset"] == 0]
    p = d["price"].to_numpy(float)
    r = np.diff(np.log(p))
    return {"scenario": scenario, "seed": seed, "sd_r": float(r.std(ddof=1)),
            "sd_x": float(d["x"].to_numpy(float).std(ddof=1)),
            "n": int(len(r)), "sum2": float((r ** 2).sum())}


def run(scenario, seeds, cfg, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_job, [(scenario, s, cfg) for s in seeds], chunksize=4))


def pooled_sd(rows, n_boot=2000, seed=5):
    """Pooled daily sd over paths (sqrt of the pooled mean square), with a path-cluster bootstrap."""
    n = np.array([r["n"] for r in rows], float)
    s2 = np.array([r["sum2"] for r in rows], float)
    pt = math.sqrt(s2.sum() / n.sum())
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(rows), (n_boot, len(rows)))
    b = np.sqrt(s2[idx].sum(axis=1) / n[idx].sum(axis=1))
    return pt, [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    blk = json.load(open(os.path.join(GEN, "e3_4", "block.json"), encoding="utf-8"))
    s_A_full = blk["s_A"]

    # ---- (i) the panel's crisis-free calm daily sd
    dd = pd.read_csv(os.path.join(GEN, "e3_3", "dd_episodes.csv"))
    dd = dd[np.isfinite(dd["rv_calm"])]
    by = {t: g["rv_calm"].to_numpy(float) for t, g in dd.groupby("ticker")}
    stocks = np.array(sorted(by))
    rng = np.random.default_rng(281001)
    meds = []
    for _ in range(1000):
        ss = rng.choice(stocks, len(stocks), replace=True)
        meds.append(np.median(np.concatenate([by[t] for t in ss])))
    sd_calm = math.sqrt(float(np.median(dd["rv_calm"].to_numpy(float))))
    ci_calm = [math.sqrt(float(np.percentile(meds, 2.5))), math.sqrt(float(np.percentile(meds, 97.5)))]
    print(f"(i) panel calm-window daily sd {sd_calm:.5f} {ci_calm} vs full-sample s_A {s_A_full:.5f}", flush=True)

    # ---- (ii) the calm-window mapping's sbar and its flat-arm sd(x)
    rho = 2.0 ** (-1.0 / blk["h"])
    def identity(sa):
        rad = (sa ** 2 - blk["sigma_V"] ** 2) * (1.0 + rho) / 2.0 - blk["jump_rate"] * blk["jump_sd"] ** 2
        return math.sqrt(rad) if rad > 0 else float("nan")
    sbar_calmmap = identity(sd_calm)
    print(f"(ii) calm-window-mapping sbar {sbar_calmmap:.5f} vs adopted {blk['sbar']:.5f}", flush=True)
    cfg_calmmap = {"sigma_V": blk["sigma_V"], "jump_rate": blk["jump_rate"], "jump_sd": blk["jump_sd"],
                   "engine": f"ar1_hl{blk['h']}",
                   "garch": {"alpha": blk["shape"]["alpha"], "gamma": blk["shape"]["gamma"],
                             "beta": blk["shape"]["beta"], "df": blk["nu"], "sbar": sbar_calmmap}}
    flat_cm = run("flat", range(SEED_FLAT_CALMMAP, SEED_FLAT_CALMMAP + a.seeds), cfg_calmmap, a.workers)
    sd_r_cm, ci_r_cm = pooled_sd(flat_cm)
    sdx_cm = float(np.median([r["sd_x"] for r in flat_cm]))

    # ---- (iii) the deployed unconditional check, events on, over the audit scenario mix
    mix = {}
    allrows = []
    for i, sc in enumerate(SCENARIOS):
        rows = run(sc, range(SEED_MIX + 1000 * i, SEED_MIX + 1000 * i + a.seeds), None, a.workers)
        pt, ci = pooled_sd(rows)
        mix[sc] = {"pooled_sd_r": pt, "ci95": ci, "median_sd_x": float(np.median([r["sd_x"] for r in rows])),
                   "n_paths": len(rows)}
        allrows += rows
        print(f"(iii) {sc:15s} pooled sd_r {pt:.5f} {ci}", flush=True)
    pt_all, ci_all = pooled_sd(allrows)
    half = (ci_all[1] - ci_all[0]) / 2.0
    excess = pt_all - s_A_full
    confirmed = bool(excess > half)

    out = {
        "design": {"seeds_per_cell": a.seeds, "seed_flat_calmmap": SEED_FLAT_CALMMAP, "seed_mix": SEED_MIX,
                   "scenarios": list(SCENARIOS), "block": blk},
        "i_panel_calm": {"sd_calm_window": sd_calm, "ci95": ci_calm,
                         "n_episodes": int(len(dd)), "n_stocks": int(len(stocks)),
                         "s_A_full_sample": s_A_full,
                         "ratio_full_over_calm": s_A_full / sd_calm,
                         "definition": "sqrt(median over drawdown episodes of rv_calm), the pre-event 120-day "
                                       "windows of E3.3 -- the registered crisis-free reference"},
        "ii_calm_window_mapping": {"sbar": sbar_calmmap, "sbar_adopted": blk["sbar"],
                                   "ratio": sbar_calmmap / blk["sbar"],
                                   "flat_pooled_sd_r": sd_r_cm, "flat_pooled_sd_r_ci95": ci_r_cm,
                                   "flat_median_sd_x": sdx_cm,
                                   "note": "the registered alternative of PREREG 3.4, reported not adopted"},
        "iii_deployed_unconditional": {"pooled_sd_r": pt_all, "ci95": ci_all, "target_s_A": s_A_full,
                                       "excess": excess, "excess_over_target_pct": 100.0 * excess / s_A_full,
                                       "bootstrap_half_width": half,
                                       "double_count_confirmed": confirmed,
                                       "per_scenario": mix,
                                       "rule": "ADDENDUM 4.3: confirmed if the excess exceeds the pooled "
                                               "statistic's own bootstrap half-width"},
        "seconds": round(time.time() - t0),
    }
    with open(os.path.join(OUT, "level_check.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E3.9c the calm-window mapping and the level double-count check "
         "(PREREG_PHASE_3_ADDENDUM.md section 4.3)", "",
         f"(i) **The panel's crisis-free calm daily sd is {sd_calm:.4f} [{ci_calm[0]:.4f}, {ci_calm[1]:.4f}]** "
         f"(sqrt of the median pre-event 120-day rv_calm over {len(dd)} episodes / {len(stocks)} stocks) against "
         f"the full-sample unconditional **{s_A_full:.4f}** the identity targets — the full sample is "
         f"**{s_A_full / sd_calm:.2f}x** the panel's own calm.", "",
         f"(ii) The **calm-window mapping** (the registered alternative, reported not adopted): sbar would be "
         f"**{sbar_calmmap:.5f}** against the adopted {blk['sbar']:.5f} "
         f"({sbar_calmmap / blk['sbar']:.2f}x); at that sbar the flat arm's pooled daily return sd is "
         f"{sd_r_cm:.4f} [{ci_r_cm[0]:.4f}, {ci_r_cm[1]:.4f}] and median sd(x) {sdx_cm:.4f}.", "",
         f"(iii) **The deployed check** (events on, {a.seeds} seeds per scenario over the audit mix): pooled "
         f"realised daily return sd **{pt_all:.4f} [{ci_all[0]:.4f}, {ci_all[1]:.4f}]** against the "
         f"{s_A_full:.4f} target — excess **{excess:+.4f}** ({100.0 * excess / s_A_full:+.1f} %) against a "
         f"bootstrap half-width of {half:.4f}: **double-count "
         f"{'CONFIRMED' if confirmed else 'not confirmed'}**.", "",
         "| scenario | pooled sd_r | 95 % CI | median sd(x) |", "|---|---|---|---|"]
    for sc in SCENARIOS:
        m = mix[sc]
        L.append(f"| {sc} | {m['pooled_sd_r']:.4f} | [{m['ci95'][0]:.4f}, {m['ci95'][1]:.4f}] | "
                 f"{m['median_sd_x']:.4f} |")
    with open(os.path.join(OUT, "level_check.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
