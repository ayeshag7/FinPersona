"""
FX3 (PREREG_PHASE_3.md sections 2 and 4.3): the E[x] guard re-measured on the Phase-3 block in force -- the
exact e2_4_flat_x design (1,000 flat paths, T = 200, rejection off, TOST +/- 0.02) at fresh seeds 240000+.

    python -m tools.phase3.e3_4_flat_x_p3 [--n 1000] [--workers 3]

Output: docs/env_v2/generated/v2_1/e3_4/flat_x_p3.json (the stored reference test_flat_x_equivalence prefers)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

import tools.phase2.e2_4_flat_x as F  # noqa: E402

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e3_4")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    F.SEED0 = 240000
    t0 = time.time()
    res = {"engine": "ar1_fit (Phase-3 volatility block in force)", "T": 200, "seed0": 240000,
           "design": "same design as e2_4/flat_x.json (1,000 flat paths, rejection off, TOST +/- 0.02), "
                     "seeds FX3 240000+",
           "phase2_reference": {"jumps_on_E_x": -0.00013, "jumps_off_E_x": -0.00029}}
    for k, jumps in (("jumps_on", True), ("jumps_off", False)):
        res[k] = F.run(a.n, a.workers, jumps)
        print(k, json.dumps(res[k]), flush=True)
    res["seconds"] = round(time.time() - t0)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "flat_x_p3.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("written", os.path.join(OUT, "flat_x_p3.json"))


if __name__ == "__main__":
    main()
