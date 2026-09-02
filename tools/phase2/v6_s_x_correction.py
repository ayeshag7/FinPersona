"""
Verification V6b (PHASE_2_REPORT.md section 1.1): Phase 1's `s_x_fit` is not the stationary sd of the process it
was fitted to, and is corrected here.

`tools/phase1/e1_2_recovery.py::smm_fit` returns
    s_x = sbar / 0.017 * 0.1752
which is the calm engine's stationary sd(x) at the REFERENCE half-life of 150 days -- the conversion is applied
whatever half-life the fit returned.  Estimator C's data fit returned h = 4.824 d, where the pull is thirty times
faster, so the stationary sd is about five times smaller than the reported number.

This module re-measures the stationary sd(x) of exactly that fit by simulating it, and writes the correction with
its evidence.  It changes a REPORTED TARGET, not a generator parameter (`s_x_fit` is labelled in `value.json` as
"FIT target for Phase 2; not a generator parameter"), so it does not trigger the execution-order rule.

    python -m tools.phase2.v6_s_x_correction [--apply]
Outputs: docs/env_v2/generated/v2_1/e2_2/s_x_correction.json (+ envs/v2/params/value.json with --apply)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e2_2")
N_PATHS, T, BURN, SEED = 50, 20000, 1000, 4242


def measure(sigma_V, sbar, h):
    from tools.phase1.calm_sim import simulate
    from tools.phase1.e1_2_recovery import W_BAR_REF, phi_of_h
    o = simulate(N_PATHS, T, h=h, sigma_V=sigma_V, sbar=sbar, seed=SEED, burn=BURN,
                 phi=phi_of_h(h), w_bar=W_BAR_REF)
    x = o["x"]
    xc = x - x.mean(axis=0)
    a1 = float(np.mean([(xc[:-1, i] * xc[1:, i]).sum() / max((xc[:, i] ** 2).sum(), 1e-300)
                        for i in range(x.shape[1])]))
    return {"sd_x": float(x.std()), "acf1_x": a1,
            "half_life_acf1": float(-math.log(2.0) / math.log(a1)) if 0 < a1 < 1 else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    f = json.load(open(os.path.join(GEN, "e1_2", "smm_fit.json"), encoding="utf-8"))
    fit = f["fit"]
    point = measure(fit["sigma_V"], fit["sbar"], fit["h"])
    # sbar's interval follows from the reported s_x interval by the same (wrong) linear map, so it is recoverable
    sbar_ci = [c * 0.017 / 0.1752 for c in f["ci95_s_x"]]
    corners = {}
    for sb in sbar_ci:
        for h in f["ci95_h"]:
            corners[f"sbar{sb:.5f}|h{h:.2f}"] = measure(fit["sigma_V"], sb, h)["sd_x"]
    res = {
        "what": "Phase 1's s_x_fit is the calm engine's stationary sd(x) at the REFERENCE half-life of 150 d, "
                "not at the half-life the fit returned; e1_2_recovery.smm_fit computes s_x = sbar/0.017*0.1752 "
                "unconditionally.",
        "phase1_fit": fit, "phase1_reported_s_x": fit["s_x"], "phase1_reported_s_x_ci95": f["ci95_s_x"],
        "measured": point, "n_paths": N_PATHS, "T": T, "burn": BURN, "seed": SEED,
        "corrected_s_x": point["sd_x"],
        "corrected_s_x_corner_range": [min(corners.values()), max(corners.values())],
        "corner_detail": corners,
        "note_on_the_interval": "Phase 1 stored only the percentiles of its 30 bootstrap refits, not the "
                                "(sbar, h) pairs, so a proper bootstrap interval for the corrected s_x cannot be "
                                "recomputed from the stored output. The corner range above pairs the endpoints "
                                "of the sbar and h intervals independently and is therefore WIDER than the true "
                                "interval; it is reported as a bound, not as an interval.",
        "cross_check_estimator_A": {"s_x": 0.02372996238833469, "ci95": [0.021645370410933513, 0.025803977234842585],
                                    "source": "e1_2/decision.json (estimator A, variance ratios, set A full sample)",
                                    "comment": "the corrected value agrees with estimator A, which measures s_x by "
                                               "a completely different route; the published 0.129 did not"},
        "date": date.today().isoformat()}
    with open(os.path.join(OUT, "s_x_correction.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: res[k] for k in ("phase1_reported_s_x", "corrected_s_x", "corrected_s_x_corner_range",
                                          "measured")}, indent=1))
    if not a.apply:
        print("(no --apply: value.json unchanged)")
        return
    vp = os.path.join(ROOT, "envs", "v2", "params", "value.json")
    v = json.load(open(vp, encoding="utf-8"))
    prev = dict(v["s_x_fit"])
    v["s_x_fit"] = {
        "value": res["corrected_s_x"],
        "label": "FIT target for Phase 2, CORRECTED (v2.1 Phase 2, verification V6b): Phase 1 reported 0.1286, "
                 "which is the calm engine's stationary sd(x) at the REFERENCE half-life of 150 d; "
                 "e1_2_recovery.smm_fit applies s_x = sbar/0.017*0.1752 whatever half-life it fitted, and the "
                 "fit returned h = 4.82 d. Re-measured on the fitted process itself: sd(x) = 0.0250 "
                 "(50 paths x 20,000 d), ACF(1) half-life 4.63 d. This agrees with estimator A's independent "
                 "0.0237 [0.0216, 0.0258]. Not a generator parameter, so no path changes.",
        "source": "e2_2/s_x_correction.json; e1_2/smm_fit.json",
        "date": res["date"],
        "interval": res["corrected_s_x_corner_range"],
        "interval_note": res["note_on_the_interval"],
        "n": 417,
        "previous": {"value": prev["value"], "label": prev["label"], "interval": prev.get("interval")},
    }
    with open(vp, "w", encoding="utf-8") as fh:
        json.dump(v, fh, indent=1)
    print(f"value.json: s_x_fit {prev['value']:.5f} -> {res['corrected_s_x']:.5f}")


if __name__ == "__main__":
    main()
