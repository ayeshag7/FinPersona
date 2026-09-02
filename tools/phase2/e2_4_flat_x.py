"""
The inherited known defect (verification V7): E[x] in flat markets, re-measured on the engine E2.4 adopted.

Phase 1 registered `tests/test_v2_1_phase_1.py::test_flat_x_equivalence` as a strict xfail owned by Phase 2:
after E1.4 removed the negative-mean jump bias the residual was E[x] = +0.0126 [+0.0038, +0.0214] at 1,000 flat
paths, and +0.0113 [+0.0027, +0.0199] with jumps switched off entirely -- the calm engine's own bias, failing
the +/- 0.02 TOST by its upper limit.  This module re-measures it, on the same design (1,000 flat paths,
T = 200, jumps on and off, the same TOST margin), on the state Phase 2 hands over.

    python -m tools.phase2.e2_4_flat_x [--n 1000] [--workers 3]
Outputs: docs/env_v2/generated/v2_1/e2_4/flat_x.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_4")
SEED0 = 150000
MARGIN = 0.02
PHASE1 = {"jumps_on": {"E_x": 0.01256676608932963, "ci95": [0.0038467447337450517, 0.021396780677724925]},
          "jumps_off": {"E_x": 0.0113, "ci95": [0.0027, 0.0199]},
          "source": "e1_4/confirm_B_x_zero.json, e1_4/confirm_jumps_off.json (1,000 flat paths each)"}


def _job(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.v2.generator import GenConfig, generate
    seed, jumps = args
    r = generate(GenConfig(scenario="flat", T=200, seed=seed, jumps=jumps, reject=False))
    m = r.day >= 1
    return float(r.x[0, m].mean())


def run(n, workers, jumps):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        vals = np.array(list(ex.map(_job, [(SEED0 + s, jumps) for s in range(n)], chunksize=8)))
    rng = np.random.default_rng(7)
    boot = np.array([vals[rng.integers(0, n, n)].mean() for _ in range(2000)])
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    return {"n": int(n), "E_x": float(vals.mean()), "ci95": [lo, hi],
            "tost_pass": bool(-MARGIN <= lo and hi <= MARGIN), "margin": MARGIN,
            "sd_across_paths": float(vals.std(ddof=1))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    from envs.v2.mispricing import ENGINE_DEFAULT
    t0 = time.time()
    res = {"engine": ENGINE_DEFAULT, "T": 200, "seed0": SEED0,
           "design": "the same design Phase 1 used for the registered defect: flat scenario, T = 200, "
                     "rejection off, E[x] over benchmark days, 2,000-resample bootstrap over paths, TOST "
                     "against +/- 0.02",
           "phase1_incumbent": PHASE1}
    for k, jumps in (("jumps_on", True), ("jumps_off", False)):
        res[k] = run(a.n, a.workers, jumps)
        print(k, json.dumps(res[k]), flush=True)
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "flat_x.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("written", os.path.join(OUT, "flat_x.json"))


if __name__ == "__main__":
    main()
