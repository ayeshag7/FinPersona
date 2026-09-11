"""
v2.1 Phase 8 -- `experiments/params/inference.json` built from the result files (PREREG_PHASE_8.md 6), called by
`python -u -m tools.phase8.e8_write_params --files inference`.

Every adopted rule is COMPUTED from a file by the registered adoption rule, never typed:
* the multiplicity decision rule from `e8_3/multiplicity.json` (a procedure is adopted on a grid shape only if its
  FDR holds, 3.8(b), in every row of that shape);
* the temporal nulls from `e8_3/null.json` (adopted only if size holds at phi_pilot for every run count, 3.8(c));
* the interval estimators from `e8_3/mixed.json` (the per-condition size verdicts, 3.8(a));
* the plug-in sigma, the transfer ratio and the power table from `e8_5/` when they exist.
A required file that is missing stops the writer with its name; nothing is defaulted.
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
TODAY = "2026-09-10"


def _need(rel):
    p = os.path.join(GEN, rel)
    if not os.path.exists(p):
        raise SystemExit(f"inference.json needs {rel}, which does not exist yet; nothing is written")
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _maybe(rel):
    p = os.path.join(GEN, rel)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def _coverage() -> dict:
    """The known-answer coverage of both upper limits, computed from e8_5/validate.csv (never typed)."""
    import pandas as pd
    p = os.path.join(GEN, "e8_5", "validate.csv")
    if not os.path.exists(p):
        raise SystemExit("inference.json needs e8_5/validate.csv, which does not exist yet; nothing is written")
    v = pd.read_csv(p)
    g = v.groupby(["s_int", "s_rep"])
    out = {"n_datasets_per_setting": int(g.size().min()), "nominal": 0.90, "per_setting": {}}
    for (si, sr), x in g:
        out["per_setting"][f"s_int={si}|s_rep={sr}"] = {
            **{f"{name}_R{R}": float(x[f"{col}_R{R}"].mean()) for name, col in (("closed_form", "mls_covers"),
                                                                                  ("bootstrap", "covers")) for R in (1, 3)},
            "sized_too_small_closed_form": float((x["n_seeds_mls_R1"] < x["n_seeds_truth_R1"]).mean()),
            "sized_too_small_bootstrap": float((x["n_seeds_plugin_R1"] < x["n_seeds_truth_R1"]).mean())}
    for name, col in (("closed_form", "mls_covers"), ("bootstrap", "covers")):
        cov = g[f"{col}_R1"].mean()
        out[f"{name}_R1_range"] = [float(cov.min()), float(cov.max())]
    return out


def _size_rows(doc, e: str):
    """An estimator's true-null rejection rate per simulated condition, read from an e8_3 file, with its Wilson interval
    and the registered verdict (size holds iff the Wilson lower limit <= 0.05)."""
    if doc is None:
        return "pending"
    out = {}
    for r in doc["table"]:
        if r.get("beta") != 0.0 or f"{e}_reject" not in r:
            continue
        key = f"M{r['M']}_S{r['S']}_sma{r['s_ma']}" + ("" if "shared" not in r else ("_shared" if r["shared"] else "_modelspecific"))
        out[key] = {"size": r[f"{e}_reject"], "wilson95": [r[f"{e}_reject_lo"], r[f"{e}_reject_hi"]],
                    "holds": bool(r[f"{e}_reject_lo"] <= 0.05)}
    return out


def _main_grid_sizing(power, transfer) -> dict:
    """D12 sized by the registered rule (PREREG 5.5-5.6; P8-16), read from the E8.5 files -- nothing typed."""
    comps = _maybe("e8_5/components.json")
    if power is None or transfer is None or comps is None:
        return {"value": None, "status": "REGISTERED", "label": "pending E8.5's power and transfer stages",
                "source": "PREREG_PHASE_8.md 5.5-5.6", "date": TODAY, "interval": "pending E8.5", "n": "pending E8.5"}
    from tools.phase8 import e8_5_variance_pilot as E
    plug = transfer["band_mas_plugin"]
    n_pairs = {r["Model"]: int(r["n_pairs"]) for r in comps["rows"] if r["metric"] == "band_mas"}
    return {
        "value": {"R": 1, "seeds_per_persona_scenario_cell": plug["seeds_appA_bonf_main_grid"],
                  "plugin_sigma_d": plug["plugin_main_grid"], "transfer_ratio": plug["ratio"],
                  "flash_only_seeds": power["sized_band_mas"]["1"]["appA_bonf"],
                  "paired_correct_seeds": plug["seeds_paired_bonf_main_grid"],
                  "at_ratio_upper_seeds": plug["seeds_appA_bonf_at_ratio_upper"],
                  "at_bootstrap_limit_seeds": plug["seeds_appA_bonf_main_grid_bootstrap"],
                  "alpha_bonferroni": plug["alpha_bonferroni"],
                  "assumes": "an analysis that pairs within persona x path (PREREG_PHASE_8_ADDENDUM.md 17)"},
        "status": "MEASURED",
        "label": ("D12 sized by the registered rule: Flash's closed-form 90 % limit x max(1, GPT-5 mini's transfer ratio), "
                  "Appendix A as written, R = 1; whether the count is affordable is the team's (D2 for Phase 9)"),
        "source": "DECISION_LOG P8-16; docs/env_v2/generated/v2_1/e8_5/transfer.json; e8_5/power.json; e8_5/components.json",
        "date": TODAY,
        "interval": {"transfer_ratio_ci90": transfer["per_metric"]["band_mas"]["ratio_ci90"]},
        "n": {"seed_level_pairs": n_pairs, "transfer_scenario": "bull_trap", "main_model": E.MAIN_MODEL}}


def build_inference() -> dict:
    from tools.phase8.e8_write_params import STATUS_KEY
    from tools.phase8 import e8_5_variance_pilot as E
    mult = _need("e8_3/multiplicity.json")
    null = _need("e8_3/null.json")
    mixed = _need("e8_3/mixed.json")
    power = _maybe("e8_5/power.json")
    transfer = _maybe("e8_5/transfer.json")
    pp = _maybe("e8_3/mixed_pp.json")
    opt = _maybe("e8_3/mixed_optimizer.json")
    if pp is not None and pp.get("adopt_e1_amended"):
        raise SystemExit("addendum 17's rule adopted E1-amended: wire it into tools/stats_v2 before writing the parameter file")
    smoke = _maybe("e8_5/smoke.json")
    smoke0 = _need("e8_5/smoke_thinking_default.json")

    rows = mult["table"]

    def holds_everywhere(grid, proc):
        rs = [r for r in rows if r["grid"] == grid and r["procedure"] == proc]
        return bool(rs) and all(r["fdr_holds"] for r in rs)

    one = "bh_within" if holds_everywhere("e8_5", "bh_within") else "by_across"
    several = "bh_within" if holds_everywhere("reviewer", "bh_within") else "by_across"
    if not holds_everywhere("reviewer", several) or not holds_everywhere("e8_5", one):
        raise SystemExit("no simulated procedure holds its FDR on every row of a grid shape; the decision rule is undecided "
                         "and must go to the addendum, not into the parameter file")

    phi_pilot = null["phi_pilot"]["median"]
    at_pilot = [r for r in null["table"] if r["phi_is_pilot"]]
    adopted_nulls = sorted({r["null"] for r in at_pilot} - {r["null"] for r in at_pilot if not r["size_holds"]})
    alpha = mixed["alpha"]
    n_min_signflip = next(n for n in range(1, 64) if 2.0 / 2 ** n <= alpha)   # exact two-sided sign-flip floor 2 / 2^n

    size = mixed["size_holds"]
    est_verdict = {e: {"conditions": len(v), "size_holds_in": sum(v.values()),
                       "fails_in": sorted(k for k, ok in v.items() if not ok)} for e, v in size.items()}

    doc = {
        "_note": ("v2.1 Phase 8 inference parameters. Written by tools/phase8/e8_write_inference.py from the e8_3 / e8_5 "
                  "result files by the registered adoption rules; read by the loud loader experiments/inference_params.py."),
        "_status_key": STATUS_KEY,
        "min_effect": {
            "value": {"band_mas": 0.05, "D": None, "cliffs_delta": "reported, sizes nothing"}, "status": "TEAM",
            "label": ("D12: a band-MAS difference of 0.05 (half a band half-width); D gets no stipulated effect -- its minimum "
                      "detectable difference at the band-MAS-sized design is its achieved power (P8-2); Phase 9's equivalence "
                      "margin is half of D12 = 0.025"),
            "source": "DECISION_LOG P8-1, P8-2; PREREG_PHASE_8.md 5.5", "date": TODAY,
            "interval": "not applicable (a decision)", "n": "not applicable"},
        "sigma_plugin": {
            "value": {"quantile": 0.90,
                      "method_primary": "closed-form modified large-sample limit for sigma_d(R') (tools/phase8/e8_5_analyse.mls_ucl_sigma_d)",
                      "method_beside": "the registered percentile cluster bootstrap over paths within scenario, 2,000 resamples",
                      "known_answer_coverage": _coverage(),
                      "band_mas_R1_limit": (power or {}).get("sized_band_mas", {}).get("1", {}).get("sigma_limit"),
                      "band_mas_R1_bootstrap_ucl90": (power or {}).get("sized_band_mas", {}).get("1", {}).get("sigma_bootstrap_ucl90")},
            "status": "MEASURED",
            "label": ("the one-sided 90 % upper confidence limit of sigma_d, never the point estimate (P8-1); sized on the "
                      "closed-form limit because the registered bootstrap limit under-covers (P8-15, addendum 16)"),
            "source": "DECISION_LOG P8-1, P8-15; docs/env_v2/generated/v2_1/e8_5/validate.json; e8_5/power.json", "date": TODAY,
            "interval": "the bootstrap's 80 % and 95 % limits reported beside", "n": 600},
        "pairing_unit": {
            "value": "seed (replicate means per arm)", "status": "TEAM",
            "label": "replicates are exchangeable; pairing replicate k with replicate k adds noise (P8-1; plan amendment)",
            "source": "DECISION_LOG P8-1", "date": TODAY, "interval": "not applicable", "n": "not applicable"},
        "alpha_rule": {
            "value": {"alpha": alpha, "sizing": "Bonferroni within the contrast's confirmatory question family",
                      "reported_beside": "nominal alpha"},
            "status": "TEAM", "label": "the power table is computed at alpha / m(family), the nominal row beside (P8-1)",
            "source": "DECISION_LOG P8-1; PREREG_PHASE_8.md 5.5", "date": TODAY, "interval": "not applicable",
            "n": (power or {}).get("m_Q1_C", "the family size of the grid being sized")},
        "power": {
            "value": 0.80, "status": "REGISTERED", "label": "Appendix A's power, used as written (factor 2), paired-correct beside",
            "source": "V2_1_IMPROVEMENT_PLAN.md Appendix A; PREREG_PHASE_8.md 5.5", "date": TODAY,
            "interval": "not applicable", "n": "not applicable"},
        "family_definition": {
            "value": {"tier_C": ["band_mas", "mcr_D@0.05", "mcr_D@0.002"], "tier_S": ["turnover", "mdd_pct", "return_pct"],
                      "descriptive": ["mcr", "mcr_B", "point_mas_v2", "rg_theta", "per-window variants"],
                      "questions": {"Q1": ["memory-static", "path_b_memory-path_b_static"],
                                    "Q2": ["memory-placebo_directive", "swapped-memory"],
                                    "Q3": ["placebo_directive-static", "placebo_declarative-static", "wrapper_only-static"],
                                    "Q4": ["path_b_static-static"],
                                    "Q5": ["stateful_L_memory-stateful_L_static", "stateful_L_memory-memory"]},
                      "size": "m(F) = contrasts present x personas x scenario cells x metrics of the tier, from the grid run",
                      "tier_C_abs_corr": mult["tier_c"]["corr"]},
            "status": "REGISTERED",
            "label": (f"tier C carries two near-duplicate D tests: |r|(D@0.05, D@0.002) = {abs(mult['tier_c']['corr'][1][2]):.3f} "
                      f"on E7.8's cells (addendum 4)"),
            "source": "PREREG_PHASE_8.md 3.4; docs/env_v2/generated/v2_1/e8_3/multiplicity.json", "date": TODAY,
            "interval": "not applicable (a definition)", "n": mult["tier_c"]["n_cells"]},
        "multiplicity": {
            "value": {"q": 0.05, "decision_rule": {"one_family": one, "several_families": several},
                      "reported_beside": "BH within family on every grid", "withdrawn": "v2: BH across metrics within a contrast"},
            "status": "MEASURED",
            "label": ("adopted by the registered rule on the simulated FDR: on a single-family grid BH within family holds; on "
                      "a multi-family grid it does not and BY across families is the decision rule (addendum 5)"),
            "source": "docs/env_v2/generated/v2_1/e8_3/multiplicity.json; PREREG_PHASE_8_ADDENDUM.md 5", "date": TODAY,
            "interval": "Monte-Carlo half-width per row in the file", "n": mult["reps"]},
        "temporal_null": {
            "value": {"adopted": adopted_nulls, "phi_pilot": phi_pilot,
                      "sign_flip_min_pairs_for_p_below_alpha": n_min_signflip},
            "status": "MEASURED",
            "label": ("a null is used only if its simulated size holds at the pilot's persistence for every run count; the "
                      "path-level sign-flip's exact p cannot fall below 2 / 2^n, so fewer pairs than the minimum cannot reject"),
            "source": "docs/env_v2/generated/v2_1/e8_3/null.json", "date": TODAY,
            "interval": "Wilson 95 % per row in the file", "n": null["reps"]},
        "cluster_bootstrap": {
            "value": {"method": "two-way pigeonhole by model and path", "n_boot": 1999, "interval": "percentile 95 %",
                      "simulated_size": est_verdict.get("e2"),
                      "simulated_size_measured_components": _size_rows(pp, "e2")},
            "status": "MEASURED",
            "label": ("E2 of 3.8(a), the contrast interval (P8-9; addendum 17's fallback). Its size at E8.3's conditions and at "
                      "E8.5's measured components is in the file: at six models with a model x arm sd of 0.03 and the sized "
                      "seeds it does NOT hold (P8-17)"),
            "source": "docs/env_v2/generated/v2_1/e8_3/mixed.json; e8_3/mixed_pp.json; DECISION_LOG P8-17", "date": TODAY,
            "interval": "Wilson 95 % per condition in the file", "n": mixed["table"][0]["n_datasets"]},
        "mixed_model": {
            "value": {"formula": "y ~ C(Arm, Treatment(ref)) * C(Persona) * C(Scenario)", "groups": "one",
                      "re_formula": "0", "vc_formula": {"model": "0 + C(Model)", "model_arm": "0 + C(Model):C(Arm)",
                                                         "path": "0 + C(Path)", "path_arm": "0 + C(Path):C(Arm) when R >= 2"},
                      "simulated_size": est_verdict.get("e1"), "v2_simulated_size": est_verdict.get("e0"),
                      "optimizer": "best: lbfgs and Powell, the higher REML likelihood kept (tools/stats_v2.crossed_mixed_model(optimizer='best'))",
                      "decides_claims": bool(pp is not None and pp.get("adopt_e1_amended")),
                      "e1_amended_adopted": None if pp is None else bool(pp.get("adopt_e1_amended")),
                      "simulated_size_best_optimum": {**(_size_rows(opt, "e1b") if opt else {}),
                                                      **(_size_rows(pp, "e1b") if pp else {})},
                      "simulated_size_e1_amended": _size_rows(pp, "e1a")},
            "status": "MEASURED",
            "label": ("E1 of 3.2, reported DESCRIPTIVELY at the better REML optimum: addendum 17's rule did not adopt "
                      "E1-amended, so by its fallback no mixed-model p-value decides a claim (P8-17); the v2 nested "
                      "intercept-only model's size beside"),
            "source": ("docs/env_v2/generated/v2_1/e8_3/mixed.json; e8_3/recovery_band.json; e8_3/mixed_pp.json; "
                       "e8_3/mixed_optimizer.json; PREREG_PHASE_8_ADDENDUM.md 17; DECISION_LOG P8-17"), "date": TODAY,
            "interval": "Wilson 95 % per condition in the file", "n": mixed["table"][0]["n_datasets"]},
        "variance_pilot_design": {
            "value": {"model": E.MAIN_MODEL, "thinking_budget": E.THINKING_BUDGET[E.MAIN_MODEL], "personas": list(E.PERSONAS),
                      "arms": list(E.ARMS), "scenarios": list(E.SCENARIOS), "seeds": list(E.SEEDS), "reps": E.REPS, "T": E.T,
                      "crash_discount": E.CRASH_DISCOUNT, "dividends": True},
            "status": "TEAM", "label": "PREREG 5.1 as amended by P8-8 (thinking off)",
            "source": "PREREG_PHASE_8.md 5.1; PREREG_PHASE_8_ADDENDUM.md 9; DECISION_LOG P8-8", "date": TODAY,
            "interval": "not applicable", "n": len(E.PERSONAS) * len(E.ARMS) * len(E.SCENARIOS) * len(E.SEEDS) * E.REPS},
        "transfer_rule": {
            "value": {"model": E.TRANSFER_MODEL, "temperature": E.TEMPERATURE[E.TRANSFER_MODEL], "scenario": "bull_trap",
                      "plugin": "sigma_UCL(main) x max(1, ratio)",
                      "measured": (transfer or {}).get("band_mas_plugin")},
            "status": "REGISTERED" if transfer is None else "MEASURED",
            "label": "a transfer of model AND temperature (gpt-5-mini accepts only 1.0; addendum 6)",
            "source": "PREREG_PHASE_8.md 5.6; docs/env_v2/generated/v2_1/e8_5/transfer.json", "date": TODAY,
            "interval": "90 % paired path bootstrap of the ratio", "n": 24},
        "main_grid_sizing": _main_grid_sizing(power, transfer),
        "cost_gate": {
            "value": {"approved_usd": E.APPROVED_USD, "gate_usd": E.GATE_USD, "rule": "125 % of the approval",
                      "first_gate": {"projected_usd": smoke0["projected_total_usd"], "pass": smoke0["pass"]},
                      "amended_gate": None if smoke is None else {"projected_usd": smoke["projected_total_usd"], "pass": smoke["pass"]}},
            "status": "MEASURED", "label": "PREREG 5.3; the first gate stopped the registered design (addendum 8; P8-8)",
            "source": "docs/env_v2/generated/v2_1/e8_5/smoke_thinking_default.json; e8_5/smoke.json", "date": TODAY,
            "interval": "n = 2 smoke runs per model", "n": 4},
    }
    return doc
