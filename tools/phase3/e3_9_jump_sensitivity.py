"""
E3.9d (PREREG_PHASE_3_ADDENDUM.md section 4.4): what the jump size costs across its own adopted interval.

sigma_J is the weakest-identified number in the block (a factor ~2.7 across estimators; the recovery grid rates
the estimator class at +-28 %).  It is not inert: it enters the section-3.4 identity through lambda sigma_J^2,
and E3.8 attributes the only readable volatility channel to the jump arm.  This module measures the span across
the adopted interval, holding lambda and everything else at the block in force, and re-deriving sbar from the
identity at each sigma_J so the total variance stays pinned (the honest comparison: the block is re-derived,
not just the jump term changed).

  (a) arithmetic: sbar and the jump share of x-innovation variance at each sigma_J
  (b) E3.8's JUMP ARM re-run at each: level-free calm R2(x), same 200 paths x 200 days, same features,
      estimators, GroupKFold and cluster bootstrap as tools/phase3/e3_8_decomposition.py

    python -m tools.phase3.e3_9_jump_sensitivity [--n-paths 200] [--T 200]

Output: docs/env_v2/generated/v2_1/e3_9/jump_sensitivity.{json,md}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase3.e3_8_decomposition import run_arm  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_9")
SEED0 = 290000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-paths", type=int, default=200)
    ap.add_argument("--T", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    blk = json.load(open(os.path.join(GEN, "e3_4", "block.json"), encoding="utf-8"))
    ad = json.load(open(os.path.join(GEN, "e3_2", "adoption.json"), encoding="utf-8"))
    lo, hi = ad["sJ"]["ci95"]
    adopted = ad["sJ"]["value"]
    rho = 2.0 ** (-1.0 / blk["h"])
    lam = blk["jump_rate"]

    def identity(sJ):
        return math.sqrt((blk["s_A"] ** 2 - blk["sigma_V"] ** 2) * (1.0 + rho) / 2.0 - lam * sJ ** 2)

    cells = [("interval floor (moment arithmetic)", lo),
             ("adopted (mixture optimum)", adopted),
             ("interval ceiling", hi)]
    rows = []
    for i, (label, sJ) in enumerate(cells):
        sbar = identity(sJ)
        jump_var = lam * sJ ** 2
        share = jump_var / (sbar ** 2 + jump_var)
        b = dict(blk)
        b["jump_sd"] = sJ
        b["sbar"] = sbar
        r = run_arm(f"jumps at sigma_J {sJ:.3f}", a.n_paths, a.T, b, SEED0 + 1000 * i, "gauss", True)
        r.update({"label": label, "sigma_J": sJ, "sbar_identity": sbar,
                  "jump_share_of_x_innovation_variance": share})
        rows.append(r)
        print(f"{label:38s} sigma_J {sJ:.3f}  sbar {sbar:.5f}  jump share {share:.1%}  "
              f"level-free calm R2 {r['levelfree_R2']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]",
              flush=True)

    base = [r for r in rows if r["sigma_J"] == adopted][0]
    floor_r = rows[0]
    span = base["levelfree_R2"] - floor_r["levelfree_R2"]
    errs = "conservative (it OVERSTATES the jump channel)" if span > 0 else \
           "anti-conservative (it UNDERSTATES the jump channel)"
    out = {"design": {"n_paths": a.n_paths, "T": a.T, "seed0": SEED0, "lambda_held": lam,
                      "sigma_J_interval": [lo, hi], "adopted": adopted,
                      "note": "sbar re-derived from the section-3.4 identity at each sigma_J, so the total "
                              "unconditional variance stays pinned and only the jump/diffusive SPLIT moves",
                      "arm": "E3.8's jump arm (Gaussian innovation + mean-zero jumps), identical features, "
                             "estimators, GroupKFold-by-path and cluster bootstrap"},
           "cells": rows,
           "verdict": {"span_adopted_minus_floor": span,
                       "adopted_errs": errs,
                       "rule": "ADDENDUM 4.4: descriptive; the adopted point does not move. What the run buys "
                               "is the label -- the measured span across the interval and which way the "
                               "adopted value errs for leakage."},
           "seconds": round(time.time() - t0)}
    with open(os.path.join(OUT, "jump_sensitivity.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E3.9d the jump size across its own interval (PREREG_PHASE_3_ADDENDUM.md section 4.4)", "",
         f"lambda held at {lam:.6f}; sbar re-derived from the identity at each sigma_J so the total "
         f"unconditional variance stays pinned and only the jump/diffusive split moves. E3.8's jump arm, "
         f"{a.n_paths} paths x {a.T} days.", "",
         "| sigma_J | | sbar (identity) | jump share of x-innovation var | level-free calm R2(x) [95 % CI] |",
         "|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['sigma_J']:.3f} | {r['label']} | {r['sbar_identity']:.5f} | "
                 f"{r['jump_share_of_x_innovation_variance']:.1%} | {r['levelfree_R2']:+.3f} "
                 f"[{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] |")
    L += ["", f"**Span across the interval: {span:+.3f} of level-free calm R2 between the adopted value and the "
          f"interval floor.** The adopted 0.230 is therefore the **{errs}** end for leakage — which is what the "
          "parameter file's label now says, beside 'weakly identified'."]
    with open(os.path.join(OUT, "jump_sensitivity.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
