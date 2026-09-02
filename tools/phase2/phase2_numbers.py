"""
Collect every Phase-2 number the report, the tests and the decision log cite into
docs/env_v2/generated/v2_1/phase2_numbers.json (the Phase-2 counterpart of phase0_numbers.json and
phase1_numbers.json; PREREG_PHASE_2.md section 10). Every entry names its source file; a missing output is
recorded as null, never invented.

    python -m tools.phase2.phase2_numbers
"""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")


def load(*p):
    f = os.path.join(GEN, *p)
    return json.load(open(f, encoding="utf-8")) if os.path.exists(f) else None


def main():
    num = {"_note": "v2.1 Phase 2 canonical numbers; each block names its source under docs/env_v2/generated/v2_1/",
           "_sources": {}}

    r = load("e2_1", "fw_repro.json")
    num["_sources"]["e2_1"] = "e2_1/fw_repro.json"
    num["e2_1"] = None if r is None else {
        "published_target_fw_table4_joint_mcr_pct": r["design"]["targets"]["fw_table4_joint_mcr_pct"],
        "sabcemm_dca_hpm": r["design"]["targets"]["sabcemm_dca_hpm"],
        "plan_stated_target_WRONG": r["design"]["targets"]["plan_stated_target"],
        "joint_mcr_pct": {k: v["joint_mcr_pct"] for k, v in r["armA"].items()},
        "joint_mcr_ci95_pct": {k: v["joint_mcr_ci95_pct"] for k, v in r["armA"].items()},
        "confirmed": {k: v["confirmed"] for k, v in r["armA"].items()},
        "chartist_share": {k: v["chartist_share_mean"] for k, v in r["armB"].items()},
        "excess_kurtosis": {k: v["excess_kurtosis_mean"] for k, v in r["armB"].items()},
        "diagnostic_mu_doubled": {k: {"chartist_share": v.get("chartist_share_mean"),
                                      "excess_kurtosis": v.get("excess_kurtosis_mean"),
                                      "joint_mcr_pct": v.get("joint_mcr_pct")}
                                  for k, v in r["diagnostic"].items()},
        "n_runs": r["design"]["n_runs"]}

    dm = load("e2_3", "data_moments.json")
    num["_sources"]["e2_3_data"] = "e2_3/data_moments.json"
    num["e2_3_data"] = None if dm is None else {
        "moment_names": dm["moment_names"], "n_stocks": dm["n_stocks"], "n_boot": dm["n_boot"],
        "block_days": dm["block_days"], "shrink": dm["shrink"],
        "periods": {k: {"window": v["window"], "n_days": v["n_days"], "moments": v["moments"],
                        "boot_sd": v["boot_sd"], "cond_number": v["cond_number"]}
                    for k, v in dm["periods"].items()}}

    fits = {}
    for f in sorted(glob.glob(os.path.join(GEN, "e2_3", "smm_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        fits[f"{d['engine']}|{d['period']}"] = {
            "params": d["params"], "J": d["J"], "J_single_crn": d["J_single_crn"], "df": d["df"],
            "chi2_crit_95": d["chi2_crit_95"], "chi2_accept": d["chi2_accept"],
            "fw_bootstrap_p": d["fw_bootstrap"].get("p_value"), "accept_fw_p": d["accept_fw_p"],
            "n_paths": d["n_paths"], "K_report": d["K_report"], "n_evaluations": d["n_evaluations"],
            "de_maxiter": d["de_maxiter"], "start_J_best": d["start_J_best"], "end_J": d["end_J"],
            "max_sim_se_over_boot_sd": max(d["sim_se_over_boot_sd"]),
            "resid_over_bootsd": d["resid_over_bootsd"],
            "ci95": d.get("bootstrap_refits", {}).get("ci95"),
            "n_bootstrap_refits": d.get("bootstrap_refits", {}).get("n"), "seconds": d["seconds"]}
    num["_sources"]["e2_3_fits"] = "e2_3/smm_<engine>_<period>.json"
    num["e2_3_fits"] = fits

    d4 = load("e2_4", "decision.json")
    num["_sources"]["e2_4"] = "e2_4/decision.json"
    num["e2_4"] = None if d4 is None else {
        "decision": d4.get("decision"),
        "heldout": {k: {"D_persistence": v["D_persistence"], "D_persistence_ci95": v["D_persistence_ci95"],
                        "D_all17": v["D_all17"]} for k, v in d4.get("heldout", {}).items()}}

    d2 = load("e2_2", "persistence.json")
    num["_sources"]["e2_2"] = "e2_2/persistence.json"
    num["e2_2"] = None if d2 is None else {"reg5": d2["reg5"], "e2_6_levels": d2["e2_6_levels"],
                                           "recovery_verdicts": d2["recovery_verdicts"]}

    d5 = load("e2_5", "hl_table.json")
    num["_sources"]["e2_5"] = "e2_5/hl_table.json"
    num["e2_5"] = None if d5 is None else {
        "design": d5["design"],
        "naive_median": {k: v["naive"]["median"] for k, v in d5["cells"].items()},
        "median_unbiased_median": {k: v["median_unbiased"]["median"] for k, v in d5["cells"].items()},
        "share_ge_60d": {k: v["naive"]["share_ge_60d"] for k, v in d5["cells"].items()},
        "share_censored": {k: v["median_unbiased"]["share_at_grid_top"] for k, v in d5["cells"].items()}}
    num["e2_5_engine_check_V4"] = load("e2_5", "v4_engine_half_life_check.json")

    d6 = load("e2_6", "sweep.json")
    num["_sources"]["e2_6"] = "e2_6/sweep.json"
    num["e2_6"] = None if d6 is None else {
        "design": d6.get("design"), "calibration": d6.get("calibration"),
        "switches": {k: {sc: {"median": s["median_switches"], "share_ge2": s["share_ge2"],
                              "wilson": s["share_ge2_wilson"], "sd_x_200": s["mean_sd_x_200"],
                              "coverage": s["mean_coverage"]}
                         for sc, s in v["switch"].items()}
                     for k, v in d6.get("cells", {}).items() if "switch" in v},
        "checklist_passes": {k: (v["checklist"]["n_pass"], v["checklist"]["n_items"])
                             for k, v in d6.get("cells", {}).items() if "checklist" in v}}

    num["_sources"]["power"] = "e2_0/power.json"
    num["power"] = load("e2_0", "power.json")

    mis = os.path.join(ROOT, "envs", "v2", "params", "mispricing.json")
    num["mispricing_json"] = (json.load(open(mis, encoding="utf-8")) if os.path.exists(mis) else None)
    v = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "value.json"), encoding="utf-8"))
    num["value_json_sigma_V"] = {"value": v["sigma_V"]["value"], "label": v["sigma_V"]["label"][:200]}

    out = os.path.join(GEN, "phase2_numbers.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(num, fh, indent=1)
    print("written", out)


if __name__ == "__main__":
    main()
