"""
E1.4 confirmatory E[x] run (PREREG_PHASE_1_ADDENDUM.md section 2, rule new-b): 1,000 flat paths under one jump-placement
variant, the mean over paths of the path mean of x with a 1,000-resample bootstrap interval; pass iff the 95 % interval lies
inside +/- 0.02. Also reports the pre-registered 200-seed TOST (old) and the plan's two-condition reading (new-a) on the
same paths' first 200 seeds for continuity.

    python -m tools.phase1.e1_4_confirm --variant B_x_zero [--n 1000] [--workers 3]
Outputs: docs/env_v2/generated/v2_1/e1_4/confirm_<variant>.json
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
os.environ.setdefault("OMP_NUM_THREADS", "1")

from tools.phase1.e1_4_generator import OUT, VARIANTS as _V, E_X_MARGIN  # noqa: E402

# diagnostic only (not a pre-registered variant): jumps switched off, to attribute a residual E[x] to the engine or the jumps
VARIANTS = dict(_V, jumps_off={"jumps": False})

SEED0_CONFIRM = 71000
N_BOOT = 1000


def _job(args):
    import warnings
    warnings.filterwarnings("ignore")
    from envs.v2.generator import GenConfig, generate
    seed, over = args
    r = generate(GenConfig(scenario="flat", seed=seed, T=200, **over))
    m = r.day >= 1
    return float(r.x[0, m].mean())


def summarise(mx: np.ndarray, margin: float = E_X_MARGIN, seed: int = 1):
    rng = np.random.default_rng(seed)
    n = len(mx)
    bm = np.array([mx[rng.integers(0, n, n)].mean() for _ in range(N_BOOT)])
    lo, hi = float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))
    se = float(mx.std(ddof=1) / np.sqrt(n))
    xbar = float(mx.mean())
    return {"n": n, "E_x": xbar, "ci95": [lo, hi], "se": se, "sd_path_means": float(mx.std(ddof=1)),
            "pass_tost": bool(-margin <= lo and hi <= margin),
            "pass_two_condition": bool(abs(xbar) <= 1.96 * se and abs(xbar) <= margin)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=list(VARIANTS))
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    over = VARIANTS[a.variant]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        mx = np.array(list(ex.map(_job, [(s, over) for s in range(SEED0_CONFIRM, SEED0_CONFIRM + a.n)], chunksize=10)))
    out = {"variant": a.variant, "config_override": over, "seeds": [SEED0_CONFIRM, SEED0_CONFIRM + a.n - 1], "T": 200,
           "margin": E_X_MARGIN, "n_boot": N_BOOT,
           "full": summarise(mx), "first_200": summarise(mx[:200]),
           "rule": "new-b: 95 % bootstrap interval of the mean of path means inside +/- 0.02 (PREREG_PHASE_1_ADDENDUM.md)",
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, f"confirm_{a.variant}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    f = out["full"]
    print(f"{a.variant}: n={f['n']} E[x]={f['E_x']:+.4f} [{f['ci95'][0]:+.4f}, {f['ci95'][1]:+.4f}] SE={f['se']:.4f} "
          f"TOST pass={f['pass_tost']} two-condition pass={f['pass_two_condition']} ({out['seconds']} s)")


if __name__ == "__main__":
    main()
