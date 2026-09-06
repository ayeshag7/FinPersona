"""
E4.20 -- closing the loop between the depth the panel asks for and the depth the generator realises.

    python -m tools.phase4.e4_20_depth_cal [--seeds 400] [--verify-seeds 1200] [--out DIR]

E4.19 found the cause of the coverage shortfall that blocks D5, and it is not the dynamics formulation: in
ALL SEVEN arms the realised depth median lands between -0.50 and -0.56 while the panel's dd30_fast median is
**-0.3693**.  Every arm sits at the panel's P10 rather than its P50, so roughly half of all paths fall below
the box floor and depth-only failure runs 4-7x duration-only failure.

The TARGET depth is drawn correctly -- it is an inverse-CDF sample from the panel's own grid.  What overshoots
is the REALISED drawdown: the panic leg is front-loaded and the GJR innovation carries price past the target.
`depth_gain` scales the target to close that loop, exactly as E4.13's multiplier closed the blow-off loop.

The loop is run on the DEPLOYED state with `schedule_mode` pinned (P4-19), and the adopted value is verified
at a larger, DISJOINT seed block so the number reported is not the number fitted.

Output: <out>/depth_cal.{json,md}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
SEED0 = 460000
VERIFY_SEED0 = 480000          # disjoint from the fitting block
N_BOOT = 2000


def _one(args):
    warnings.filterwarnings("ignore")
    from envs.v2.generator import generate, GenConfig
    seed, gain = args
    r = generate(GenConfig(scenario="crash", seed=seed, T=200, delta=0.70,
                           schedule_mode="v21", depth_gain=gain))
    m = r.day >= 1
    P = r.P[0, m]
    return float((P / np.maximum.accumulate(P) - 1).min())


def realised(gain, seeds, seed0, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return np.asarray(list(ex.map(_one, [(s, gain) for s in range(seed0, seed0 + seeds)],
                                      chunksize=8)), float)


def boot_median_ci(v, n_boot=N_BOOT, seed=420):
    rng = np.random.default_rng(seed)
    b = [float(np.median(v[rng.integers(0, len(v), len(v))])) for _ in range(n_boot)]
    return float(np.median(v)), [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=400)
    ap.add_argument("--verify-seeds", type=int, default=1200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--iters", type=int, default=6)
    ap.add_argument("--out", default=os.path.join(GEN, "e4_20"))
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)

    from envs.v2 import events_params as EP
    if not EP.PRESENT:
        raise SystemExit("events.json is absent: this calibrates the DEPLOYED state and there is none")

    e41 = json.load(open(os.path.join(GEN, "e4_1", "episodes4.json"), encoding="utf-8"))
    q = e41["panel_families"]["dd30_fast"]["quantiles"]["depth"]
    target = float(q["p50"])
    box = [float(q["p10"]), float(q["p90"])]
    print("[target] panel dd30_fast depth p50 = %.4f  (box [%.4f, %.4f])" % (target, box[0], box[1]),
          flush=True)

    res = {"what": "E4.20: closed-loop calibration of the crash depth, the cause E4.19 identified for the "
                   "coverage shortfall that blocks D5.",
           "target": {"panel_depth_p50": target, "panel_box": box,
                      "source": "e4_1/episodes4.json panel_families.dd30_fast"},
           "design": {"seeds_per_iteration": a.seeds, "seed0": SEED0,
                      "verify_seeds": a.verify_seeds, "verify_seed0": VERIFY_SEED0,
                      "schedule_mode": "v21 (pinned)", "delta": 0.70, "n_boot": N_BOOT},
           "loop": []}

    # secant iteration on gain -> realised median depth (monotone: a smaller gain gives a shallower crash)
    gain = 1.0
    v = realised(gain, a.seeds, SEED0, a.workers)
    cur = float(np.median(v))
    res["uncalibrated"] = {"gain": 1.0, "realised_depth_p50": cur}
    print("[loop] gain %.5f -> realised %.4f (target %.4f)" % (gain, cur, target), flush=True)
    res["loop"].append({"iteration": 0, "gain": gain, "realised_depth_p50": cur})

    lo_g, hi_g = 0.20, 1.20
    for i in range(1, a.iters + 1):
        # realised depth is monotone increasing (less negative) as gain falls; bisect on that
        mid = 0.5 * (lo_g + hi_g)
        v = realised(mid, a.seeds, SEED0, a.workers)
        cur = float(np.median(v))
        print("[loop] gain %.5f -> realised %.4f (target %.4f)" % (mid, cur, target), flush=True)
        res["loop"].append({"iteration": i, "gain": mid, "realised_depth_p50": cur})
        if cur < target:      # too deep -> reduce the gain
            hi_g = mid
        else:
            lo_g = mid
        gain = mid

    # ---- verification on a DISJOINT, larger seed block ----
    vv = realised(gain, a.verify_seeds, VERIFY_SEED0, a.workers)
    med, ci = boot_median_ci(vv)
    inbox = float(np.mean((vv >= box[0]) & (vv <= box[1])))
    v0 = realised(1.0, a.verify_seeds, VERIFY_SEED0, a.workers)
    med0, ci0 = boot_median_ci(v0)
    inbox0 = float(np.mean((v0 >= box[0]) & (v0 <= box[1])))
    res["adopted"] = {
        "depth_gain": gain,
        "verified_on_disjoint_seeds": a.verify_seeds,
        "realised_depth_p50": med, "ci95": ci,
        "share_inside_panel_depth_box": inbox,
        "uncalibrated_realised_depth_p50": med0, "uncalibrated_ci95": ci0,
        "uncalibrated_share_inside_panel_depth_box": inbox0,
        "target_inside_ci": bool(ci[0] <= target <= ci[1])}
    res["seconds"] = round(time.time() - t0)

    with open(os.path.join(a.out, "depth_cal.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    L = ["# E4.20 the crash depth, calibrated closed-loop", "", res["what"], "",
         "Panel target (dd30_fast): depth p50 **%.4f**, box [%.4f, %.4f]." % (target, box[0], box[1]), "",
         "| | depth_gain | realised depth p50 | 95 %% CI | share inside the panel's depth box |",
         "|---|---|---|---|---|",
         "| uncalibrated | 1.0 | %.4f | [%.4f, %.4f] | %.3f |" % (med0, ci0[0], ci0[1], inbox0),
         "| **calibrated** | **%.5f** | **%.4f** | [%.4f, %.4f] | **%.3f** |"
         % (gain, med, ci[0], ci[1], inbox), "",
         "Target inside the calibrated CI: **%s**. Verified at %d seeds DISJOINT from the %d used to fit "
         "(seed blocks %d and %d), so the number reported is not the number fitted."
         % (res["adopted"]["target_inside_ci"], a.verify_seeds, a.seeds, VERIFY_SEED0, SEED0), "",
         "## The loop", "", "| iteration | gain | realised depth p50 |", "|---|---|---|"]
    for it in res["loop"]:
        L.append("| %d | %.5f | %.4f |" % (it["iteration"], it["gain"], it["realised_depth_p50"]))
    L.append("")
    with open(os.path.join(a.out, "depth_cal.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
