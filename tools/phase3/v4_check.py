"""
Verification V4 (PREREG_PHASE_3.md section 1): the section-3.4 identity reproduces the target unconditional
daily return sd in a long free-running simulation at the adopted block (engines.py's ar1 simulator with the
block's shape, jumps and identity sbar -- the exact structure the refit ran).

    python -m tools.phase3.v4_check [--n-paths 50] [--T 20000]

Output: docs/env_v2/generated/v2_1/e3_4/v4_uncond_check.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-paths", type=int, default=50)
    ap.add_argument("--T", type=int, default=20000)
    a = ap.parse_args()
    from tools.phase2.engines import simulate, DEFAULTS
    blk = json.load(open(os.path.join(GEN, "e3_4", "block.json"), encoding="utf-8"))
    p = dict(DEFAULTS)
    p.update({"price_scale": 1.0, "sigma_V": blk["sigma_V"], "h": blk["h"],
              "garch_shape": {"alpha": blk["shape"]["alpha"], "gamma": blk["shape"]["gamma"],
                              "beta": blk["shape"]["beta"], "df": blk["nu"]},
              "jump_rate": blk["jump_rate"], "jump_sd": blk["jump_sd"],
              "sbar_identity": {"s_A": blk["s_A"]}})
    out = simulate("ar1c", a.n_paths, a.T, p, seed=270001, burn=500)
    r = np.diff(out["logP"], axis=0)
    sd = float(r.std(ddof=1))
    per_path = r.std(axis=0, ddof=1)
    se = float(per_path.std(ddof=1) / math.sqrt(a.n_paths))
    res = {"target_s_A": blk["s_A"], "measured_uncond_sd": sd,
           "per_path_median": float(np.median(per_path)), "se_of_mean_over_paths": se,
           "n_paths": a.n_paths, "T": a.T, "seed": 270001,
           "sbar_identity_value": blk["sbar"],
           "agree_within_3se": bool(abs(sd - blk["s_A"]) <= 3 * se + 1e-6),
           "sd_x": float(out["x"].std())}
    with open(os.path.join(GEN, "e3_4", "v4_uncond_check.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
