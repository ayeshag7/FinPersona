"""
E2.1 (PREREG_PHASE_2.md section 3): reproduce Franke & Westerhoff's OWN model and settle the units convention.

Arm A (primary, FW's own criterion): 200 runs x 6,750 steps (their T'), FW's nine moments per run, the moment
coverage ratios against FW 2012 Table A1's 95 % intervals, and the JOINT MCR against their Table 4 DCA-HPM
column (10.1 %).  A convention is confirmed iff the 95 % Wilson interval of the joint MCR contains 10.1 %.

Arm B (secondary, reported without a pass/fail): 200 runs x 7,000 steps, SABCEMM's setting, mean chartist share
and mean excess kurtosis against SABCEMM Table 1's DCA-HPM row 0.1674 / 10.033 (read at source; the plan's
"0.23 / 7.8" is a mis-transcription -- PREREG section 3.1).

Diagnostic (pre-registered as a diagnostic, never as a fit): the one ambiguity in SABCEMM's appendix that could
double the effective price impact (their eqs (5)-(6)) is run once at mu -> 2 mu and reported.

    python -m tools.phase2.e2_1_fw_repro [--n-runs 200]
Outputs: docs/env_v2/generated/v2_1/e2_1/fw_repro.json, fw_repro.md
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

from tools.phase2.fw_pure import DCA_HPM, PureParams, excess_kurtosis, hill_index, simulate_pure  # noqa: E402
from tools.phase2.moments import FW_NAMES, FW_TABLE_4_DCA_HPM, FW_TABLE_A1, fw_moments  # noqa: E402

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_1")
SEED0 = 100001
T_FW, T_SAB = 6750, 7000
SABCEMM_DCA_HPM = {"excess_kurtosis": 10.033, "hill": 2.481, "chartist_share": 0.1674}
PLAN_TARGET = {"chartist_share": 0.23, "excess_kurtosis": 7.8}


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def arm_a(n_runs: int, price_scale: float, seed: int, burn: int = 0, mu_mult: float = 1.0):
    p = PureParams(**{**DCA_HPM, "price_scale": price_scale})
    p.mu = DCA_HPM["mu"] * mu_mult
    o = simulate_pure(n_runs, T_FW, p, seed=seed, burn=burn)
    M = fw_moments(o["r"])
    cov, inside = {}, np.ones(n_runs, bool)
    for j, nm in enumerate(FW_NAMES):
        _, lo, hi = FW_TABLE_A1[nm]
        ok = (M[:, j] >= lo) & (M[:, j] <= hi)
        inside &= ok
        lo_ci, hi_ci = wilson(int(ok.sum()), n_runs)
        cov[nm] = {"coverage_pct": float(ok.mean() * 100), "ci95_pct": [lo_ci * 100, hi_ci * 100],
                   "sim_mean": float(M[:, j].mean()),
                   "sim_ci95_mean": [float(np.percentile(M[:, j], 2.5)), float(np.percentile(M[:, j], 97.5))],
                   "fw_table4_pct": FW_TABLE_4_DCA_HPM[nm], "data": FW_TABLE_A1[nm][0]}
    lo_ci, hi_ci = wilson(int(inside.sum()), n_runs)
    return {"n_runs": n_runs, "T": T_FW, "price_scale": price_scale, "burn": burn, "mu_mult": mu_mult,
            "joint_mcr_pct": float(inside.mean() * 100), "joint_mcr_ci95_pct": [lo_ci * 100, hi_ci * 100],
            "fw_table4_joint_pct": FW_TABLE_4_DCA_HPM["joint"],
            "confirmed": bool(lo_ci * 100 <= FW_TABLE_4_DCA_HPM["joint"] <= hi_ci * 100),
            "per_moment": cov, "mean_chartist_share": float(o["n_c"].mean())}


def arm_b(n_runs: int, price_scale: float, seed: int, burn: int = 0, mu_mult: float = 1.0):
    p = PureParams(**{**DCA_HPM, "price_scale": price_scale})
    p.mu = DCA_HPM["mu"] * mu_mult
    o = simulate_pure(n_runs, T_SAB, p, seed=seed, burn=burn, p_star=1.0)
    sh = o["n_c"].mean(axis=0)
    ku = excess_kurtosis(o["r"])
    hi_ = hill_index(o["r"])

    def ci(a):
        return [float(a.mean() - 1.96 * a.std(ddof=1) / math.sqrt(len(a))),
                float(a.mean() + 1.96 * a.std(ddof=1) / math.sqrt(len(a)))]
    return {"n_runs": n_runs, "T": T_SAB, "price_scale": price_scale, "burn": burn, "mu_mult": mu_mult,
            "chartist_share_mean": float(sh.mean()), "chartist_share_ci95": ci(sh),
            "chartist_share_sd_across_runs": float(sh.std(ddof=1)),
            "excess_kurtosis_mean": float(ku.mean()), "excess_kurtosis_ci95": ci(ku),
            "excess_kurtosis_median": float(np.median(ku)),
            "hill_index_mean": float(hi_.mean()), "hill_index_ci95": ci(hi_),
            "sabcemm_dca_hpm": SABCEMM_DCA_HPM,
            "share_matches_sabcemm": bool(ci(sh)[0] <= SABCEMM_DCA_HPM["chartist_share"] <= ci(sh)[1]),
            "kurtosis_matches_sabcemm": bool(ci(ku)[0] <= SABCEMM_DCA_HPM["excess_kurtosis"] <= ci(ku)[1])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-runs", type=int, default=200)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res = {"design": {"seeds": [SEED0, SEED0 + a.n_runs - 1], "n_runs": a.n_runs, "T_armA": T_FW, "T_armB": T_SAB,
                      "params": DCA_HPM, "source": "FW 2012 Table 1 DCA-HPM (read at source 1 Sep 2026)",
                      "targets": {"fw_table4_joint_mcr_pct": FW_TABLE_4_DCA_HPM["joint"],
                                  "sabcemm_dca_hpm": SABCEMM_DCA_HPM, "plan_stated_target": PLAN_TARGET}},
           "armA": {}, "armB": {}, "diagnostic": {}}
    for s in (1.0, 100.0):
        res["armA"][f"scale{int(s)}"] = arm_a(a.n_runs, s, SEED0)
        res["armB"][f"scale{int(s)}"] = arm_b(a.n_runs, s, SEED0 + 500)
        print(f"scale {s:g}: joint MCR {res['armA'][f'scale{int(s)}']['joint_mcr_pct']:.1f}% "
              f"{res['armA'][f'scale{int(s)}']['joint_mcr_ci95_pct']} confirmed="
              f"{res['armA'][f'scale{int(s)}']['confirmed']}; share "
              f"{res['armB'][f'scale{int(s)}']['chartist_share_mean']:.4f} kurt "
              f"{res['armB'][f'scale{int(s)}']['excess_kurtosis_mean']:.3f}", flush=True)
    # burn-in immateriality (reported, no criterion)
    res["armA"]["scale1_burn500"] = arm_a(a.n_runs, 1.0, SEED0 + 1000, burn=500)
    res["armB"]["scale1_burn500"] = arm_b(a.n_runs, 1.0, SEED0 + 1500, burn=500)
    # SABCEMM excess-demand ambiguity: DIAGNOSTIC ONLY (PREREG section 3.3)
    res["diagnostic"]["mu_doubled_scale1"] = arm_b(a.n_runs, 1.0, SEED0 + 2000, mu_mult=2.0)
    res["diagnostic"]["mu_doubled_scale1_armA"] = arm_a(a.n_runs, 1.0, SEED0 + 2500, mu_mult=2.0)
    res["seconds"] = round(time.time() - t0)
    with open(os.path.join(OUT, "fw_repro.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    A1, A100 = res["armA"]["scale1"], res["armA"]["scale100"]
    B1, B100 = res["armB"]["scale1"], res["armB"]["scale100"]
    L = ["# E2.1 Franke-Westerhoff reproduction and the units convention (PREREG_PHASE_2.md section 3)", "",
         f"FW's own model (their eqs (1), (5)-(7), DCA, HPM; two independent Gaussian demand noises, no GARCH, "
         f"no jumps, no drift, constant p*) at FW 2012 Table 1's DCA-HPM parameters. {a.n_runs} runs, "
         f"seeds {SEED0}-{SEED0 + a.n_runs - 1}. `price_scale` multiplies (p - p*) inside the misalignment term "
         "only.", "",
         "## Arm A (primary): FW's own moment coverage criterion, T' = 6,750", "",
         "| convention | joint MCR | 95 % Wilson | FW Table 4 | contains 10.1 %? |", "|---|---|---|---|---|"]
    for k, r in (("price_scale = 1", A1), ("price_scale = 100", A100), ("scale 1, burn 500", res["armA"]["scale1_burn500"])):
        L.append(f"| {k} | {r['joint_mcr_pct']:.1f} % | [{r['joint_mcr_ci95_pct'][0]:.1f}, "
                 f"{r['joint_mcr_ci95_pct'][1]:.1f}] % | {r['fw_table4_joint_pct']} % | "
                 f"{'**yes**' if r['confirmed'] else 'no'} |")
    L += ["", "Per-moment coverage ratios (%) beside FW 2012 Table 4's DCA-HPM column and Table A1's measured "
              "value (reported, not a criterion -- PREREG section 3.3):", "",
          "| moment | data (Table A1) | sim mean, scale 1 | coverage, scale 1 | FW Table 4 | sim mean, scale 100 | coverage, scale 100 |",
          "|---|---|---|---|---|---|---|"]
    for nm in FW_NAMES:
        c1, c100 = A1["per_moment"][nm], A100["per_moment"][nm]
        L.append(f"| {nm} | {c1['data']:.3f} | {c1['sim_mean']:.4f} | {c1['coverage_pct']:.1f} "
                 f"[{c1['ci95_pct'][0]:.1f}, {c1['ci95_pct'][1]:.1f}] | {c1['fw_table4_pct']} | "
                 f"{c100['sim_mean']:.4f} | {c100['coverage_pct']:.1f} |")
    L += ["", "## Arm B (secondary, no pass/fail): SABCEMM's summary row, 7,000 steps", "",
          "| convention | mean chartist share | 95 % CI | mean excess kurtosis | 95 % CI | Hill index |",
          "|---|---|---|---|---|---|"]
    for k, r in (("price_scale = 1", B1), ("price_scale = 100", B100), ("scale 1, burn 500", res["armB"]["scale1_burn500"]),
                 ("DIAGNOSTIC: scale 1, mu doubled", res["diagnostic"]["mu_doubled_scale1"])):
        L.append(f"| {k} | {r['chartist_share_mean']:.4f} | [{r['chartist_share_ci95'][0]:.4f}, "
                 f"{r['chartist_share_ci95'][1]:.4f}] | {r['excess_kurtosis_mean']:.3f} | "
                 f"[{r['excess_kurtosis_ci95'][0]:.3f}, {r['excess_kurtosis_ci95'][1]:.3f}] | "
                 f"{r['hill_index_mean']:.3f} |")
    L += ["", f"Published targets: SABCEMM Table 1 DCA-HPM row (read at source) chartist share "
              f"**{SABCEMM_DCA_HPM['chartist_share']}**, excess kurtosis **{SABCEMM_DCA_HPM['excess_kurtosis']}**, "
              f"Hill {SABCEMM_DCA_HPM['hill']}; the plan's stated pair "
              f"({PLAN_TARGET['chartist_share']} / {PLAN_TARGET['excess_kurtosis']}) is a mis-transcription and is "
              "closest to SABCEMM's DCA-WP row (0.2285 / 7.7600) -- PREREG_PHASE_2.md section 3.1, decision P2-1.",
          "", f"Run time {res['seconds']} s."]
    with open(os.path.join(OUT, "fw_repro.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
