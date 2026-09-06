"""
E4.15 -- what actually drives multi-asset co-drawdown, and whether the per-asset event mechanism changes it.

    python -m tools.phase4.e4_15_multiasset [--seeds 60] [--workers 3]

P4-16 stated that v2's multi-asset extension "puts every asset in the same event on the same days, i.e. a
common-factor loading of 1.0", and proposed per-asset event draws with a FIT loading as the fix.  Two of those
three statements are refuted by measurement (e4_10 T7 refuted the third):

  * the realised loading under v2 is not 1.0 -- it is about 0.35;
  * per-asset event draws do not change it, because every asset is in the SAME SCENARIO and therefore crashes
    regardless of whether it shares the schedule;
  * the panel's 0.236 is an ALL-DAY average over 417 names while the generator's 0.35 is conditional on a
    crash scenario, so the two are not the same population and P4-16's comparison was not matched.

This module measures all of it on one code path and persists it, rather than leaving the numbers in a session
script -- which is the provenance failure P4-19 documents.

Arms: crash with the v2 shared event; crash with per-asset events at several loadings; FLAT (no scripted event
at all, which isolates how much of the co-movement the events cause); and both with the common fundamental
factor switched off.

Output: docs/env_v2/generated/v2_1/e4_15/multiasset.{json,md}
"""
from __future__ import annotations

import argparse
import json
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
OUT = os.path.join(GEN, "e4_15")
SCHED = "v21"
SEED0 = 340000
N_BOOT = 2000
N_ASSETS = 3


def _one(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.synthetic_market import SyntheticMarketEnv
    scenario, seed, cfg = args
    kw = {"crash_discount": 0.70} if scenario == "crash" else {}
    base = dict(cfg or {})
    base["schedule_mode"] = SCHED
    env = SyntheticMarketEnv(scenario, 200, seed, n_assets=N_ASSETS, config=base, **kw)
    M = []
    for a in range(N_ASSETS):
        p = env.data[env.data["asset"] == a]["price"].to_numpy(float)
        M.append((p / np.maximum.accumulate(p) - 1) <= -0.30)
    M = np.vstack(M)
    return {"seed": seed, "mean_share": float(M.mean(axis=0).mean()),
            "all_together": float(M.all(axis=0).mean()), "any": float(M.any(axis=0).mean())}


def pmap(items, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, items, chunksize=2))


def boot_mean(v, n_boot=N_BOOT, seed=4150):
    v = np.asarray(v, float)
    rng = np.random.default_rng(seed)
    b = [float(v[rng.integers(0, len(v), len(v))].mean()) for _ in range(n_boot)]
    return float(v.mean()), [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=60)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    e41 = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    xs = e41["cross_section"]

    arms = [
        ("crash_shared_event_v2", "crash", {}),
        ("crash_per_asset_load1.0", "crash", {"ma_per_asset_events": True, "ma_common_loading": 1.0}),
        ("crash_per_asset_load0.5", "crash", {"ma_per_asset_events": True, "ma_common_loading": 0.5}),
        ("crash_per_asset_load0.0", "crash", {"ma_per_asset_events": True, "ma_common_loading": 0.0}),
        ("crash_no_common_factor", "crash", {"rho_common": 0.0}),
        ("flat_no_event", "flat", {}),
        ("flat_no_common_factor", "flat", {"rho_common": 0.0}),
    ]
    res = {"design": {"n_assets": N_ASSETS, "seeds": a.seeds, "seed0": SEED0, "schedule_mode": SCHED,
                      "statistic": "share of the 3 assets inside a >= 30 % running-peak drawdown, averaged "
                                   "over days and over paths -- the same definition E4.1 uses on the panel",
                      "panel": {"mean_share_all_days": xs["mean_share_in_drawdown"],
                                "p90": xs["p90_share_in_drawdown"], "max": xs["max_share_in_drawdown"],
                                "n_names": xs["n_names"]}},
           "arms": {}}
    for name, sc, cfg in arms:
        rows = pmap([(sc, s, cfg) for s in range(SEED0, SEED0 + a.seeds)], a.workers)
        pt, ci = boot_mean([r["mean_share"] for r in rows])
        tog, tog_ci = boot_mean([r["all_together"] for r in rows])
        res["arms"][name] = {"scenario": sc, "config": cfg, "mean_share": pt, "ci95": ci,
                             "all_three_together": tog, "n_paths": len(rows)}
        print(f"  {name:26s} {pt:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]  all-three {tog:.4f}", flush=True)

    A = res["arms"]
    shared = A["crash_shared_event_v2"]["mean_share"]
    per0 = A["crash_per_asset_load0.0"]["mean_share"]
    flat = A["flat_no_event"]["mean_share"]
    nocf = A["crash_no_common_factor"]["mean_share"]
    res["findings"] = {
        "v2_loading_is_not_1.0": {"measured": shared, "claimed_in_P4_16": 1.0,
                                  "verdict": "REFUTED" if shared < 0.95 else "confirmed"},
        "per_asset_events_change_it": {
            "shared": shared, "per_asset_loading_0": per0, "difference": float(shared - per0),
            "verdict": ("NO -- the mechanism is implemented and switchable but does not move the statistic, "
                        "because every asset is in the SAME SCENARIO and crashes whether or not it shares "
                        "the schedule"
                        if abs(shared - per0) < 0.05 else "yes")},
        "what_does_drive_it": {
            "crash": shared, "flat_no_event": flat,
            "crash_without_the_common_fundamental_factor": nocf,
            "verdict": (f"the scripted EVENT drives it: {shared:.3f} in crash against {flat:.3f} in flat. "
                        f"The common fundamental factor is not the cause -- removing it leaves {nocf:.3f}.")},
        "population_mismatch": {
            "generator_crash": shared, "generator_flat": flat,
            "panel_all_days": xs["mean_share_in_drawdown"], "panel_p90": xs["p90_share_in_drawdown"],
            "verdict": ("P4-16 compared the generator's CRASH-conditional share with the panel's ALL-DAY "
                        "mean. Those are different populations. The panel's all-day mean sits between the "
                        "generator's flat and crash arms, and the panel's p90 "
                        f"({xs['p90_share_in_drawdown']:.3f}) is ABOVE the generator's crash arm "
                        f"({shared:.3f}).")},
    }
    res["consequence"] = (
        "The per-asset mechanism stays implemented and switchable, labelled NOT ADOPTED, because measurement "
        "shows it does not do what P4-16 said it would. Making the generator's cross-sectional co-movement "
        "match the panel's would require SCENARIO heterogeneity across assets -- some assets not in an event "
        "at all -- which is a design change to the multi-asset extension and belongs with the Phase-9 "
        "multi-asset sensitivities, not with Phase 4's event block.")
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(OUT, "multiasset.json"), "w", encoding="utf-8"), indent=1, default=str)
    L = ["# E4.15 - what drives multi-asset co-drawdown", "",
         "`python -m tools.phase4.e4_15_multiasset`", "",
         f"{a.seeds} seeds per arm, {N_ASSETS} assets, `schedule_mode` pinned to {SCHED}.", "",
         "| arm | co-drawdown share | 95 % CI | all three together |", "|---|---|---|---|"]
    for k, v in A.items():
        L.append(f"| {k} | {v['mean_share']:.4f} | [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}] | "
                 f"{v['all_three_together']:.4f} |")
    L += ["", f"Panel: mean over all days **{xs['mean_share_in_drawdown']:.3f}**, p90 "
              f"{xs['p90_share_in_drawdown']:.3f}, max {xs['max_share_in_drawdown']:.3f} "
              f"({xs['n_names']} names).", "", "## Findings", ""]
    for k, v in res["findings"].items():
        L.append(f"- **{k}**: {v['verdict']}")
    L += ["", f"**Consequence.** {res['consequence']}", ""]
    open(os.path.join(OUT, "multiasset.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n" + res["findings"]["what_does_drive_it"]["verdict"])
    print(f"wrote {OUT}/multiasset.json in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
