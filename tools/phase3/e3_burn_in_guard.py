"""
Burn-in guard for the engine in force under the Phase-3 block (PREREG_PHASE_3.md section 11's test set;
the E1.5 construction re-run for `ar1_fit`, whose 750-day option-A burn-in E1.5 verified under the OLD block):
1,000 day-5000 reference states and 500 day-1 states, KS point distance per variable (< 0.10, the E1.5 rule).

    python -m tools.phase3.e3_burn_in_guard [--n-ref 1000] [--n-day1 500] [--workers 3]

Outputs: docs/env_v2/generated/v2_1/e1_5/reference_states_ar1_fit.npz (the fresh reference the live test uses),
         docs/env_v2/generated/v2_1/e3_4/burn_in_guard.json
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

from tools.phase1.e1_5_burn_in import _ref_job, _day1_job, ks_upper, VARS, D0, OUT as E15_OUT  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
ENGINE = "ar1_fit"
SEED0 = 255000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-ref", type=int, default=1000)
    ap.add_argument("--n-day1", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        ref = np.array(list(ex.map(_ref_job, [(s, ENGINE) for s in range(SEED0, SEED0 + a.n_ref)], chunksize=10)))
        d1 = np.array(list(ex.map(_day1_job, [(s, ENGINE, None, None) for s in
                                              range(SEED0 + 5000, SEED0 + 5000 + a.n_day1)], chunksize=10)))
    np.savez(os.path.join(E15_OUT, f"reference_states_{ENGINE}.npz"), x=ref[:, 0], sigma2=ref[:, 1],
             n_f=ref[:, 2], x_prev=ref[:, 3], h=ref[:, 4], e_prev=ref[:, 5],
             seeds=np.arange(SEED0, SEED0 + a.n_ref))
    res = {"engine": ENGINE, "block": "Phase-3 volatility block in force", "n_ref": a.n_ref, "n_day1": a.n_day1,
           "seed0": SEED0, "burn_in": "value.json option A (long, 750 d for the default engine)",
           "vars": {}}
    ok = True
    for j, v in enumerate(VARS):
        pt, _ = ks_upper(d1[:, j], ref[:, j], n_boot=1)
        res["vars"][v] = {"ks_point": round(pt, 4), "pass": bool(pt < D0)}
        ok &= pt < D0
    res["all_pass"] = bool(ok)
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(GEN, "e3_4", "burn_in_guard.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
