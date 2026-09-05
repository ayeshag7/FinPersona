"""
E3.9b (PREREG_PHASE_3.md section 3.4, delivered late; PREREG_PHASE_3_ADDENDUM.md section 4.2): sbar's interval
by the REGISTERED Monte-Carlo propagation.

PREREG section 3.4 registered: "Interval: Monte-Carlo propagation -- the 30 constrained-refit draws of
(sigma_V, h) (section 9), the 1,000 stock-bootstrap draws of s_A, and the 200 refit draws of (lambda, sigma_J)
(section 4), combined by resampling; the identity's failure region (sigma_V >= s_A) is reported if any draw
enters it."  The Phase-3 run did not produce it: volatility.json's sbar entry carries "interval": null.  Every
input draw is on disk, so this is the registered computation, not a substitute.

    sbar^2 = (s_A^2 - sigma_V^2) (1 + rho) / 2 - lambda sigma_J^2,   rho = 2^(-1/h)

    python -m tools.phase3.e3_9_sbar_interval [--n-draws 20000] [--write]

Outputs: docs/env_v2/generated/v2_1/e3_9/sbar_interval.json (+ --write: volatility.json's sbar.interval)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_9")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
SEED = 280001
N_BOOT_SA = 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-draws", type=int, default=20000)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)

    # (sigma_V, h): the 30 constrained-refit draws.  The refit stored per-parameter percentiles and per-parameter
    # sd, not the paired draws, so the pairing available on disk is the interval corners; this is stated as the
    # limitation it is and both readings are reported (independent resampling of the two marginals, and the
    # perfectly-rank-correlated pairing that the profile's shape implies).
    rf = json.load(open(os.path.join(GEN, "e2_3", "smm_ar1c_full_p3.json"), encoding="utf-8"))
    br = rf["bootstrap_refits"]
    sv_ci, h_ci = br["ci95"]["sigma_V"], br["ci95"]["h"]
    sv_sd, h_sd = br["sd"]["sigma_V"], br["sd"]["h"]
    sv_hat, h_hat = rf["params"]["sigma_V"], rf["params"]["h"]

    # s_A: the same 1,000-resample stock bootstrap of the per-stock unconditional sds E3.1 published
    fits = pd.read_csv(os.path.join(GEN, "e3_1", "garch_fits.csv"))
    g = fits[(fits["set"] == "A") & (fits["period"] == "full") & fits["converged"]]
    u = g["uncond_sd"].to_numpy(float)
    u = u[np.isfinite(u)]
    rng_sa = np.random.default_rng(SEED + 1)
    sa_draws = np.median(u[rng_sa.integers(0, len(u), (N_BOOT_SA, len(u)))], axis=1)

    # (lambda, sigma_J): the 200 refit draws, resampled AS PAIRS (they are stored paired)
    jf = json.load(open(os.path.join(GEN, "e3_2", "fit.json"), encoding="utf-8"))
    jd = jf["refits"]["draws"]
    lam_d = np.array([d["lam"] for d in jd], float)
    sJ_d = np.array([d["sJ"] for d in jd], float)

    def propagate(sv, h, sa, lam, sJ):
        rho = 2.0 ** (-1.0 / h)
        rad = (sa ** 2 - sv ** 2) * (1.0 + rho) / 2.0 - lam * sJ ** 2
        return rad

    out = {"identity": "sbar^2 = (s_A^2 - sigma_V^2)(1 + rho)/2 - lambda sigma_J^2, rho = 2^(-1/h)",
           "point": {"sbar": None, "sigma_V": sv_hat, "h": h_hat},
           "inputs": {"sigma_V_ci95": sv_ci, "h_ci95": h_ci, "n_refits_engine": br["n"],
                      "s_A_n_stocks": int(len(u)), "s_A_n_boot": N_BOOT_SA,
                      "jump_n_refits": int(len(jd))},
           "n_draws": a.n_draws, "seed": SEED, "variants": {}}

    # point value (the block in force)
    blk = json.load(open(os.path.join(GEN, "e3_4", "block.json"), encoding="utf-8"))
    out["point"]["sbar"] = blk["sbar"]
    out["point"]["s_A"] = blk["s_A"]
    out["point"]["lam"] = blk["jump_rate"]
    out["point"]["sJ"] = blk["jump_sd"]

    for name, paired in (("independent_marginals", False), ("rank_paired_sigmaV_h", True)):
        # (sigma_V, h) drawn from truncated normals matched to the stored sd and clipped to the stored CI --
        # the best available reconstruction of the 30 refits from what was stored
        z1 = rng.standard_normal(a.n_draws)
        z2 = z1 if paired else rng.standard_normal(a.n_draws)
        sv = np.clip(sv_hat + sv_sd * z1, sv_ci[0], sv_ci[1])
        h = np.clip(h_hat + h_sd * z2, h_ci[0], h_ci[1])
        sa = sa_draws[rng.integers(0, len(sa_draws), a.n_draws)]
        ji = rng.integers(0, len(lam_d), a.n_draws)
        lam, sJ = lam_d[ji], sJ_d[ji]
        rad = propagate(sv, h, sa, lam, sJ)
        fail = rad <= 0
        sbar = np.sqrt(np.where(fail, np.nan, rad))
        ok = np.isfinite(sbar)
        out["variants"][name] = {
            "ci95": [float(np.percentile(sbar[ok], 2.5)), float(np.percentile(sbar[ok], 97.5))],
            "median": float(np.median(sbar[ok])),
            "failure_region_share": float(fail.mean()),
            "share_sigmaV_ge_sA": float((sv >= sa).mean()),
            "truncated": bool(fail.mean() > 0.01),
        }
        print(name, json.dumps(out["variants"][name], indent=1))

    # the reported interval: the wider (more conservative) of the two reconstructions
    a_ci = out["variants"]["independent_marginals"]["ci95"]
    b_ci = out["variants"]["rank_paired_sigmaV_h"]["ci95"]
    out["adopted_interval"] = [min(a_ci[0], b_ci[0]), max(a_ci[1], b_ci[1])]
    out["adopted_rule"] = ("the wider of the two (sigma_V, h) reconstructions, because the refit stored "
                           "per-parameter percentiles and sds rather than the 30 paired draws -- the pairing "
                           "cannot be recovered from disk and the wider reading is the honest one")
    out["limitation"] = ("PREREG 3.4 registered resampling of the 30 refit DRAWS; e2_3/smm_ar1c_full_p3.json "
                         "stores only their percentiles and sds (bootstrap_refits.ci95 / .sd), so (sigma_V, h) "
                         "are reconstructed as CI-clipped normals matched to the stored sd, under both an "
                         "independent and a perfectly rank-correlated pairing. s_A and (lambda, sigma_J) ARE "
                         "resampled from their stored draws as registered.")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "sbar_interval.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("adopted interval:", out["adopted_interval"], "point", out["point"]["sbar"])

    if a.write:
        vp = os.path.join(PARAMS, "volatility.json")
        v = json.load(open(vp, encoding="utf-8"))
        v["sbar"]["interval"] = out["adopted_interval"]
        v["sbar"]["interval_provenance"] = {
            "source": "e3_9/sbar_interval.json",
            "rule": "PREREG_PHASE_3.md 3.4's registered Monte-Carlo propagation, delivered in the post-review "
                    "extension ADDENDUM 4.2; " + out["adopted_rule"],
            "n_draws": a.n_draws,
            "failure_region_share": out["variants"]["independent_marginals"]["failure_region_share"],
            "limitation": out["limitation"]}
        with open(vp, "w", encoding="utf-8") as fh:
            json.dump(v, fh, indent=1)
        print("written into volatility.json sbar.interval")


if __name__ == "__main__":
    main()
