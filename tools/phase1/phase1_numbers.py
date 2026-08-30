"""
Collect every Phase-1 number the report, the tests and the decision log cite into
docs/env_v2/generated/v2_1/phase1_numbers.json (the Phase-1 counterpart of phase0_numbers.json; PREREG_PHASE_1.md
section 10). Every entry names its source file. Missing outputs are recorded as null, never invented.

    python -m tools.phase1.phase1_numbers
"""
from __future__ import annotations

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
    num = {"_note": "v2.1 Phase 1 canonical numbers; each block names its source under docs/env_v2/generated/v2_1/"}
    v = json.load(open(os.path.join(ROOT, "envs", "v2", "params", "value.json"), encoding="utf-8"))
    num["value_json"] = {k: (v[k]["value"] if isinstance(v[k], dict) and "value" in v[k] else None) for k in v if not k.startswith("_")}
    num["value_json_labels"] = {k: v[k]["label"] for k in v if isinstance(v[k], dict) and "label" in v[k]}
    sets = load("e1_0_analysis_sets.json")
    if sets:
        num["analysis_sets"] = {"A": sets.get("n_A", sets.get("A", {}).get("n") if isinstance(sets.get("A"), dict) else None),
                                "B": sets.get("n_B", sets.get("B", {}).get("n") if isinstance(sets.get("B"), dict) else None), "source": "e1_0_analysis_sets.json"}
    g = load("e3_1", "summary.json")
    if g:
        num["e3_1"] = {"source": "e3_1/summary.json", "summary": g if len(json.dumps(g)) < 20000 else "see file"}
    vr = load("e1_2", "vr_fit.json")
    if vr:
        f = vr["periods"]["full"]
        num["e1_2_A"] = {"source": "e1_2/vr_fit.json", "sigma_V": f["fit"]["sigma_V"], "sigma_V_ci_stock": f["ci_stock_bootstrap"]["sigma_V"],
                         "sigma_V_ci_block": f["ci_block_bootstrap"]["sigma_V"], "s_x": f["fit"]["s_x"], "h_days": f["fit"]["h_days"],
                         "h_ci_stock": f["ci_stock_bootstrap"]["h_days"], "h_ci_block": f["ci_block_bootstrap"]["h_days"], "n_stocks": f["n_stocks"], "J": f["fit"]["J"]}
    pv = load("e1_2", "pv_fit.json")
    if pv:
        b = pv["variants"]["EarningsPerShareBasic|sector"]
        num["e1_2_B"] = {"source": "e1_2/pv_fit.json (EarningsPerShareBasic|sector)", "h_days": b["h_days_median_unbiased"]["median"],
                         "h_ci": b["h_days_median_unbiased"]["ci95"], "h_ols": b["h_days_ols"]["median"], "s_x": b["s_x"]["median"], "s_x_ci": b["s_x"]["ci95"],
                         "n_stocks": b["n_stocks"], "share_undefined_months": b["share_undefined_months"]}
    smm = load("e1_2", "smm_fit.json")
    if smm:
        num["e1_2_C"] = {"source": "e1_2/smm_fit.json", **smm["fit"], "ci95_h": smm["ci95_h"], "ci95_sigma_V": smm["ci95_sigma_V"], "ci95_s_x": smm["ci95_s_x"],
                         "n_boot_refits": smm["n_boot_refits"]}
    misc = load("e1_2", "misc_fits.json")
    if misc:
        num["e1_2_misc"] = {"source": "e1_2/misc_fits.json", **{k: misc[k] for k in misc if k in ("mu_V", "df_V", "vhat_noise", "start_price_range")}}
    two = load("e1_2", "vr_two_component_exploratory.json")
    if two:
        num["e1_2_two_component_exploratory"] = {"source": "e1_2/vr_two_component_exploratory.json (NOT pre-registered)",
                                                 **{k: two[k] for k in ("one_component_reference", "free_fit", "h2_fixed_256", "h2_fixed_150")}}
    rec = load("e1_2", "recovery.json")
    if rec:
        num["e1_2_recovery"] = {"source": "e1_2/recovery.json", "design": rec["design"],
                                "cells": {k: {e: (c[e]["usable"] if c.get(e) else None) for e in ("A", "B_rho0.0", "B_rho0.9", "C")} for k, c in rec["cells"].items()}}
    dec = load("e1_2", "decision.json")
    if dec:
        num["e1_2_decision"] = {"source": "e1_2/decision.json", **dec["decision"]}
    ps = load("e1_4", "panel_split.json")
    if ps:
        num["e1_4_panel"] = {"source": "e1_4/panel_split.json", **{k: ps[k] for k in ps if len(json.dumps(ps[k])) < 4000}}
    gs = load("e1_4", "generator_split.json")
    if gs:
        num["e1_4_generator"] = {"source": "e1_4/generator_split.json",
                                 "variants": {k: {kk: r[kk] for kk in ("E_x", "E_x_ci95", "E_x_pass", "ks_window", "ks_window_upper95", "ks_other", "ks_other_upper95", "ks_pass",
                                                                       "q_share_of_jumps_in_window", "share_kurt_gt_1p5", "median_kurt")} for k, r in gs["variants"].items()},
                                 "script_decision": gs["decision"]}
    for name in ("B_x_zero", "A_V_announce", "C_both", "current_x_negmean", "jumps_off"):
        c = load("e1_4", f"confirm_{name}.json")
        if c:
            num.setdefault("e1_4_confirm", {"source": "e1_4/confirm_<variant>.json"})[name] = c["full"]
    for suffix in ("", "_n500"):
        b = load("e1_5", f"burn_in{suffix}.json")
        if b:
            num[f"e1_5{suffix or '_n2000'}"] = {"source": f"e1_5/burn_in{suffix}.json", "n_paths": b["design"].get("n_paths", 500), "decision": b["decision"],
                                                  "options": {e: {o: {"pass": r["pass"], "ks": {vv: (r[vv]["ks"], r[vv]["ks_upper95"]) for vv in ("x", "sigma2", "n_f")},
                                                                     "sd_ratio_x": r["x"]["sd_ratio_vs_ref"]} for o, r in er["options"].items()} for e, er in b["engines"].items()}}
    sp = load("e1_1", "start_price.json")
    if sp:
        num["e1_1"] = {"source": "e1_1/start_price.json", "design": sp["design"],
                       "mechanisms": {m: {"attacker_pass": r["attacker"]["attacker_pass"],
                                          "delta_by_scenario": {sc: (r["attacker"][f"{sc}|all"]["delta_level_minus_levelfree"], r["attacker"][f"{sc}|all"]["delta_ci95"]) for sc in sp["design"]["scenarios"]},
                                          "rule100_pass": {sc: r["rule100"][sc]["pass"] for sc in sp["design"]["scenarios"]},
                                          "day1_price_sd": r["day1_price_sd"]} for m, r in sp["mechanisms"].items()}}
    sw = load("e1_3", "sweep.json")
    if sw:
        num["e1_3"] = {"source": "e1_3/sweep.json", "design": sw["design"], "n_grid_points": len(sw["grid"])}
    fz = load("e1_6", "frozen_equivalent_check.json")
    if fz:
        num["frozen_equivalent_check"] = {"source": "e1_6/frozen_equivalent_check.json", "n_configs": fz["n_configs"], "hidden_columns_identical": fz["hidden_columns_identical"],
                                          "all_columns_identical": fz["all_columns_identical"], "differing_columns": fz["differing_columns"]}
    with open(os.path.join(GEN, "phase1_numbers.json"), "w", encoding="utf-8") as fh:
        json.dump(num, fh, indent=1, default=str)
    print("written", sorted(k for k in num if not k.startswith("_")))


if __name__ == "__main__":
    main()
