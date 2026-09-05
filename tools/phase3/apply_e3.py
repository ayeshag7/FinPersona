"""
Apply Phase 3's decisions to the generator (PREREG_PHASE_3.md section 11).

Writes `envs/v2/params/volatility.json` (the volatility block in force, every entry with provenance), updates
`value.json` (sigma_V from the section-9 refit; the jump entry re-fitted) and `mispricing.json` (structural
sigma_V/h and the garch_shape now APPLIED; sbar now governed by volatility.json's identity value).

Applying changes every path, so the execution-order rule follows: re-freeze, regenerate hashes, checklist and
the level-free audit on the state handed over (tools/phase2/after_state.py with the Phase-3 labels).

    python -m tools.phase3.apply_e3 [--dry-run]      # first pass (before e3_5_audit exists)
    python -m tools.phase3.apply_e3 --add-tz         # second pass: insert e3_5/audit.json's T_z into the iv entry
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
TODAY = date.today().isoformat()
SURVIVOR = ("set A has no delistings by construction (REG-15): tails, drawdown depths and episode multipliers "
            "understate the full universe (the delisted tail is 4.7 % recoverable, E1.0); set B's fatter tails "
            "(nu 4.33 vs 4.86) give the direction; the WRDS re-run (D1 = C) is the remedy")


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def entry(value, label, source, interval=None, n=None, gap=None, **extra):
    d = {"value": value, "label": label, "source": source, "date": TODAY,
         "interval": interval, "n": n, "survivor_vs_literature_gap": gap}
    d.update(extra)
    return d


def add_tz(dry):
    vol = jload(os.path.join(PARAMS, "volatility.json"))
    aud = jload(os.path.join(GEN, "e3_5", "audit.json"))
    tz = {k: v["T_z"] for k, v in aud["transitions"].items()}
    vol["iv"]["value"]["T_z"] = tz
    vol["iv"]["tz_provenance"] = {"source": "e3_5/audit.json", "n_seeds": aud["design"]["seeds"],
                                  "rule": "T_z = P95 over seeds of the SAME filter's forecast z at the "
                                          "transition (PREREG 7.2(3)); test_iv_continuity gates on it",
                                  "z_iv_measured": {k: v["z_iv_mean"] for k, v in aud["transitions"].items()},
                                  "onset_delta_auc": aud["onset_auc"]}
    if dry:
        print(json.dumps(vol["iv"]["value"], indent=1))
        return
    with open(os.path.join(PARAMS, "volatility.json"), "w", encoding="utf-8") as fh:
        json.dump(vol, fh, indent=1)
    print("T_z written into volatility.json:", tz)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--add-tz", action="store_true")
    ap.add_argument("--refit", default="smm_ar1c_full_p3.json")
    a = ap.parse_args()
    if a.add_tz:
        add_tz(a.dry_run)
        return
    e31s = jload(os.path.join(GEN, "e3_1", "summary.json"))["summary"]["A|full"]
    conf = jload(os.path.join(GEN, "e3_1", "confirm.json"))
    rec = jload(os.path.join(GEN, "e3_2", "recovery.json"))
    adoption = jload(os.path.join(GEN, "e3_2", "adoption.json"))
    det = jload(os.path.join(GEN, "e3_2", "detection.json"))
    e33 = jload(os.path.join(GEN, "e3_3", "episodes.json"))
    blk = jload(os.path.join(GEN, "e3_4", "block.json"))
    cal = jload(os.path.join(GEN, "e3_4", "calibration.json"))
    mc = jload(os.path.join(GEN, "e3_4", "mechanism_c.json"))
    dec = jload(os.path.join(GEN, "e3_4", "decision.json"))
    prem = jload(os.path.join(GEN, "e3_5", "premium.json"))
    rf = jload(os.path.join(GEN, "e2_3", a.refit))
    q = det["design"]["q_ann_held"]
    lam, sJ, nu = adoption["lam"]["value"], adoption["sJ"]["value"], adoption["nu"]["value"]
    ci = {"nu": adoption["nu"]["ci95"], "lam": adoption["lam"]["ci95"], "sJ": adoption["sJ"]["ci95"]}
    rci = rf.get("bootstrap_refits", {}).get("ci95", {})
    arms = jload(os.path.join(GEN, "e3_4", "arms.json"))["arms"]
    adopted = dec["decision"]["adopted"]
    mode = {"A_variance": "variance", "B_omega_ramp": "omega", "C_switching": "switching"}[adopted.split(" ")[0]]
    mult_x = dict(cal["mult_x"])
    # the blow-off label is assigned EX POST (events.relabel_blowoff), so a blow-off multiplier never reaches
    # the GARCH driver -- inert in v2 (OMEGA_MULT 2.0) and inert now (the calibration diverged 2.2 -> 9.3 with
    # the realised ratio unmoved at ~1.1, which is how the defect surfaced). Recorded as mania's value with the
    # inertness documented; the in-run label during those days IS mania.
    mult_x["blow-off"] = mult_x["mania"]
    mech_val = {"scale_mode": mode, "mult": mult_x, "ramp_days": 0}
    if mode == "omega":
        mech_val["ramp_days"] = int(arms["B_omega_ramp"].get("ramp_days_fit", 0))
    if mode == "switching":
        mech_val["switching"] = mc["switching"]
    pers = 0.027 + 0.058 / 2 + 0.932
    s_A = blk["s_A"]
    filter_omega = s_A ** 2 * (1.0 - (blk["shape"]["alpha"] + blk["shape"]["gamma"] / 2 + blk["shape"]["beta"]))
    coef = prem["pooled_coef"]
    vol = {
        "_note": "v2.1 Phase 3 volatility-block parameters in force (PREREG_PHASE_3.md; PHASE_3_REPORT.md). "
                 "Every entry: value + provenance + what it is conditional on. Loader "
                 "envs/v2/volatility_params.py; envs/v2/garch.py reads its defaults from here.",
        "garch_shape": entry(
            {"alpha": blk["shape"]["alpha"], "gamma": blk["shape"]["gamma"], "beta": blk["shape"]["beta"],
             "df": nu},
            "FIT: alpha/gamma/beta = E3.1 set-A full-sample per-stock medians (the plan's own adoption rule); "
            "df = E3.2's mixture-fit DIFFUSIVE tail, net of jumps (E3.1's per-stock QML median nu 4.86 "
            "[4.73, 5.02] is the TOTAL tail including jump days and is the sensitivity anchor). CONDITIONAL: "
            "df is conditional on the jump block fitted jointly with it.",
            "e3_1/summary.md; e3_2/adoption.json (ADDENDUM 3); e3_2/recovery.json (usable = %s)" % rec["usable"],
            interval={"alpha": e31s["alpha"]["ci95"], "gamma": e31s["gamma"]["ci95"],
                      "beta": e31s["beta"]["ci95"], "df": ci["nu"]},
            n=417, gap=SURVIVOR,
            e3_1_qml_nu_total_tail={"median": e31s["nu"]["median"], "ci95": e31s["nu"]["ci95"]},
            persistence_alpha_gamma_beta=round(pers, 4)),
        "shape_sensitivity_sets": entry(
            {k: conf["shape_sensitivity_sets"][k] for k in ("P25", "P75")},
            "DESIGN (PREREG 3.2): quantiles of (alpha, gamma, nu, persistence) with beta derived, so both sets "
            "are stationary (the raw per-parameter P75s give persistence 1.028); run through Phase 6's "
            "checklist and Phase 9's grid, not here",
            "e3_1/confirm.json", n=417),
        "sbar": entry(
            blk["sbar"],
            "FIT by the variance-accounting identity (PREREG 3.4): the generator's free-running unconditional "
            "daily return sd equals E3.1's per-stock median 0.0218 -- sbar^2 = (s_A^2 - sigma_V^2)(1+rho)/2 - "
            "lambda sigma_J^2, every input FIT. CONDITIONAL on (sigma_V, h) of the section-9 refit and on the "
            "jump block. WHICH QUANTITY IS WHICH: 0.0218 = the panel's TOTAL-return unconditional sd (E3.1); "
            "0.0087 = E2.3's engine-conditional x-innovation scale under a 17-moment objective the model fails "
            "(not a measurement of the panel's volatility); 0.017 = v2's CAL, superseded by this entry.",
            "e3_1/summary.md; e3_2/adoption.json; e2_3/%s; PREREG_PHASE_3.md 3.4" % a.refit,
            interval=None, n=417, gap=SURVIVOR,
            inputs={"s_A": s_A, "sigma_V": blk["sigma_V"], "h": blk["h"], "jump_rate": lam, "jump_sd": sJ},
            s_A_ci=e31s["uncond_sd"]["ci95"],
            sbar_fitted_not_applied_phase2=0.008698868151339125,
            v2_cal_superseded=0.017),
        "jumps": entry(
            {"placement": "x_zero", "jump_rate_x": lam, "jump_sd": sJ,
             "p_ann": lam * q / (4.0 / 252.0), "lam_res": lam * (1.0 - q), "q_panel": q},
            "FIT, WEAKLY IDENTIFIED (E3.2 / ADDENDUM 3: the mixture fit's triple with recovery-informed "
            "widened intervals; the model as a whole is REJECTED -- J 790 -- and the recovery grid rates the "
            "estimator class lam +/-59 pct, sJ +/-28 pct; what is robust is rare-and-very-large, lam 0 "
            "excluded). placement x_zero is E1.4's decision (kept); q is "
            "E1.4's FIT (kept); p_ann / lam_res are mechanical derivations from (lambda, q). The observed "
            "negative share of exceedance-day returns ({:.3f}) is a known simplification of the mean-zero "
            "placement, guarded by test_flat_x_equivalence.".format(det["sizes_at_4"]["neg_share"]),
            "e3_2/adoption.json (ADDENDUM 3); e3_2/detection.md; e3_2/recovery.json",
            interval={"lam": ci["lam"], "sJ": ci["sJ"]}, n=det["design"]["n_days"], gap=SURVIVOR,
            detection={"observed_share_at_4": det["observed_share"]["4.0"],
                       "expected_t_tail_at_4": det["expected_t_tail_share"]["4.0"],
                       "excess_at_4": det["excess_share"]["4.0"],
                       "excess_ci95_at_4": det["excess_ci95"]["4.0"]},
            literature_beside="ABD 2007 (index futures): 14.4 % jump share of RV, 27.9 % of days -- anchors, "
                              "never tolerances",
            v2_cal_superseded={"jump_rate_x": 0.010, "jump_sd": 0.03}),
        "phase_multipliers": entry(
            {k: e33["multipliers"][f"mu_{k}"]["median"] for k in
             ("deterioration", "panic", "stabilisation", "mania", "blow-off", "post-top")},
            "FIT (E3.3): RV(window)/median own RV21 per episode, medians over episodes with stock-bootstrap "
            "CIs; the UNCONDITIONAL reference of ADDENDUM 1 (the registered pre-event-window ratios are in "
            "e3_3/episodes.md beside). TOTAL-return ratios; the x-innovation multipliers in force are "
            "mechanism.mult (closed-loop calibrated, e3_4/calibration.json). sustained-bull = 1.0 (DESIGN, "
            "review R1-D5: a volatility reduction would be a scenario clock).",
            "e3_3/episodes.{json,md}",
            interval={k: e33["multipliers"][f"mu_{k}"]["ci95"] for k in
                      ("deterioration", "panic", "stabilisation", "mania", "blow-off", "post-top")},
            n={"drawdowns": e33["drawdowns"]["n_episodes"], "runups": e33["runups"]["n_episodes"],
               "stocks": 417}, gap=SURVIVOR,
            literature_beside="Ang & Timmermann 2012 variance ratio ~4.0; Ang & Bekaert 2002 7.04 vs 3.77 % "
                              "(monthly, index); Schwert 1989 +76..+227 %; the plan's index examples 2020 ~10 d "
                              "/ 2008 ~30 d are not a sample"),
        "mechanism": entry(
            mech_val,
            f"FIT decision (E3.4 / REG-6, all three mechanisms run at 200 crash seeds each): adopted "
            f"{adopted!r} — NO mechanism lands the rise time inside either empirical CI (fast-crash [29, 35] d "
            "vs generator 75.5 / 103 / 80 d for A/B/C), because the onset-to-panic gap is the SCHEDULE "
            "template's, handed to Phase 4; REG-6's consequence keeps A. mult = the x-innovation multipliers "
            "whose generator-REALISED total ratios match E3.3's FIT medians (closed loop, e3_4/calibration.json "
            "verify block: deterioration 1.34, panic 7.54, stabilisation 3.12, mania 1.19 — all inside the "
            "CIs). TWO DOCUMENTED SHORTFALLS: (i) blow-off is an EX-POST label (events.relabel_blowoff), so its "
            "multiplier never reaches the GARCH driver — inert in v2 too (OMEGA_MULT 2.0 was dead code); "
            "recorded at mania's value; the empirical blow-off target 1.65 [1.58, 1.71] vs the achievable ~1.19 "
            "is Phase 4's (it owns the event/relabel machinery). (ii) post-top is DRIFT-dominated: the scripted "
            "reversal leg floors the realised ratio at 1.59 against the target 1.16 [1.13, 1.20] whatever the "
            "innovation multiplier (driven to 0.35); Phase 4 owns the post-top drift shape (E4.8).",
            "e3_4/decision.{json,md}; e3_4/arms.json; e3_4/calibration.json; e3_4/mechanism_c.json",
            interval=None, n=200,
            empirical_cis=dec["empirical_cis"], verdicts_summary={
                r: {m: v[m]["passes"] for m in ("A_variance", "B_omega_ramp", "C_switching")}
                for r, v in dec["verdicts"].items()},
            calibration_verify=cal["verify"],
            b_arm_note="B (omega + FIT ramp 20 d) comes closest to the POOLED rise CI (103 vs [107, 131]) but "
                       "censors 35 % of decays beyond 250 d; C (switching, v_ratio 16.2, p_exit 1/64) rises no "
                       "faster and decays slower; all three arms' full statistics are in arms.json"),
        "iv": entry(
            {"mode": "v21_filter", "horizon": 21,
             "filter": {"alpha": blk["shape"]["alpha"], "gamma": blk["shape"]["gamma"],
                        "beta": blk["shape"]["beta"], "omega": filter_omega},
             "premium": {"family": prem["adopted_family"], "coef": coef},
             "eps": {"rho": prem["eps"]["rho_median"], "sd_innov": prem["eps"]["sd_innov_median"]}},
            "FIT (E3.5): IV_t = sqrt(252 fc_t) (1+pi) exp(eps_t), fc from a PAST-ONLY GJR filter on observed "
            "returns (omega anchored at the identity's unconditional return variance s_A^2); the premium is "
            "the CONSTANT the leave-one-name-out CV adopts on the five CBOE single-stock VIX histories "
            "(log(1+pi) = %.4f; the level-dependent families lose by the 1-SE rule); eps AR(1) FIT from the "
            "residuals. The v2 stress trigger, whole-path quantile (the look-ahead), sigma_V add-on, w^2 "
            "factor and CAL floor 12 are REMOVED; the pooled CBOE minimum %.2f is the anchor the generator's "
            "minimum is reported against. CONDITIONAL: five mega-caps (stated wherever quoted)." % (
                coef[0], prem["pooled"]["min_iv_pooled"]),
            "e3_5/premium.{json,md}; datasets/05_implied_vol/cboe",
            interval={"rho_range": prem["eps"]["rho_range"], "sd_range": prem["eps"]["sd_innov_range"]},
            n=prem["pooled"]["n_days"],
            gap="five mega-caps (VXAPL/VXAZN/VXGOG/VXGS/VXIBM); the median S&P name's premium may differ",
            cv=prem["cv"], per_name_median_premium={k: v["mean_premium"] for k, v in prem["per_name"].items()}),
        "engine_refit": entry(
            {"sigma_V": rf["params"]["sigma_V"], "h": rf["params"]["h"], "J": rf["J"], "df": rf["df"],
             "chi2_accept": rf["chi2_accept"], "fw_bootstrap_p": rf["fw_bootstrap"]["p_value"]},
            "FIT (section 9: Phase 2's SMM re-launched ONCE on this volatility block, sbar eliminated by the "
            "identity, free = (sigma_V, h)); the unconstrained sensitivity and the Phase-2 values are in the "
            "report. These values also govern value.json sigma_V and mispricing.json structural/half_life.",
            f"e2_3/{a.refit}", interval=rci or None, n=417, gap=SURVIVOR),
    }
    out = os.path.join(PARAMS, "volatility.json")
    print(json.dumps({k: (v["value"] if isinstance(v, dict) and "value" in v else "...") for k, v in vol.items()},
                     indent=1))
    if a.dry_run:
        print("(dry run: nothing written)")
        return
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(vol, fh, indent=1)
    print("written", out)

    # ---- value.json: sigma_V (refit) and the jump block
    vp = os.path.join(PARAMS, "value.json")
    v = jload(vp)
    prev_sv = dict(v["sigma_V"])
    v["sigma_V"] = {
        "value": float(rf["params"]["sigma_V"]),
        "label": "FIT, CONDITIONAL ON THE ENGINE AND ON THE PHASE-3 VOLATILITY BLOCK (section-9 refit: "
                 "sigma_V and h re-identified with the E3.1 shape, E3.2 jumps and the identity-constrained "
                 "sbar in the simulator; PREREG_PHASE_3.md section 9). Phase 2's engine-conditional value "
                 "(0.01220 [0.01066, 0.01419], old GARCH shape) and Phase 1's estimator values are recorded "
                 "below. Quote as 'sigma_V of the adopted engine under the Phase-3 volatility block'.",
        "source": f"e2_3/{a.refit}; e2_4/decision.json",
        "date": TODAY,
        "interval": (rci or {}).get("sigma_V"),
        "n": 417,
        "previous_phase2": {"value": prev_sv["value"], "interval": prev_sv.get("interval")},
        "phase1_estimator_C": prev_sv.get("phase1_estimator_C"),
        "phase1_estimators_on_the_same_panel": prev_sv.get("phase1_estimators_on_the_same_panel"),
        "conditional_on": {"engine": "ar1_fit", "volatility_block": "envs/v2/params/volatility.json (Phase 3)",
                           "moment_set": "FW's nine plus the eight persistence-carrying moments"},
    }
    jv = dict(v["jump"])
    jv["value"] = dict(jv["value"])
    jv["value"].update({"jump_rate_x": lam, "jump_sd": sJ, "p_ann": lam * q / (4.0 / 252.0),
                        "lam_res": lam * (1.0 - q)})
    jv["label"] = ("FIT: placement 'x_zero' E1.4 (kept; KS rule), rate and size E3.2 (mixture fit, recovery-"
                   "gated), p_ann/lam_res derived from (lambda, q = %.4f E1.4 FIT). v2's CAL 0.010/0.03 "
                   "superseded (E3.2). E[x] guard: test_flat_x_equivalence at 1,000 flat paths." % q)
    jv["source"] = "e3_2/adoption.json; e3_2/detection.md; e1_4/generator_split.json"
    jv["date"] = TODAY
    jv["interval"] = {"lam": ci["lam"], "sJ": ci["sJ"], "q": jv["interval"]["q"] if isinstance(jv.get("interval"), dict) else None}
    jv["previous"] = {"jump_rate_x": 0.010, "jump_sd": 0.03, "label": "CAL (v2 E1 calibration)"}
    v["jump"] = jv
    with open(vp, "w", encoding="utf-8") as fh:
        json.dump(v, fh, indent=1)
    print("value.json: sigma_V %.6g -> %.6g; jumps (%.4g, %.4g) -> (%.4g, %.4g)"
          % (prev_sv["value"], rf["params"]["sigma_V"], 0.010, 0.03, lam, sJ))

    # ---- mispricing.json: structural / half_life / garch_shape / applied
    mp = os.path.join(PARAMS, "mispricing.json")
    m = jload(mp)
    prev_st = dict(m["structural"]["value"])
    m["structural"]["value"] = {"sigma_V": float(rf["params"]["sigma_V"]), "h": float(rf["params"]["h"]),
                                "sbar_by_identity": blk["sbar"]}
    m["structural"]["label"] = ("FIT (section-9 refit, v2.1 Phase 3: Phase 2's SMM re-launched on the Phase-3 "
                                "volatility block -- E3.1 shape + E3.2 jumps in the simulator, sbar eliminated "
                                "by PREREG 3.4's identity, free = (sigma_V, h), df = 15). CONDITIONAL on that "
                                "block; the Phase-2 fit (old shape, sbar free) is recorded under previous.")
    m["structural"]["source"] = f"e2_3/{a.refit}"
    m["structural"]["date"] = TODAY
    m["structural"]["interval"] = rci or None
    m["structural"]["previous_phase2"] = {"value": prev_st, "J": m["structural"].get("J"),
                                          "interval": m["structural"].get("interval")}
    m["structural"]["J"] = rf["J"]
    m["structural"]["df"] = rf["df"]
    m["structural"]["chi2_crit_95"] = rf["chi2_crit_95"]
    m["structural"]["chi2_accept"] = rf["chi2_accept"]
    m["structural"]["fw_bootstrap_p"] = rf["fw_bootstrap"]["p_value"]
    m["structural"]["accept_fw_p"] = rf["accept_fw_p"]
    m["half_life"]["value"] = float(rf["params"]["h"])
    m["half_life"]["interval"] = (rci or {}).get("h")
    m["half_life"]["date"] = TODAY
    m["half_life"]["label"] = ("FIT (section-9 refit; conditional on the Phase-3 volatility block). Phase 2's "
                               "7.498 [3.81, 23.61] under the old shape recorded in structural.previous_phase2.")
    m["half_life"]["source"] = f"e2_3/{a.refit}; e2_2/persistence.md"
    m["garch_shape"]["value"] = {"alpha": blk["shape"]["alpha"], "gamma": blk["shape"]["gamma"],
                                 "beta": blk["shape"]["beta"], "df": nu}
    m["garch_shape"]["label"] = ("FIT and NOW APPLIED (v2.1 Phase 3): alpha/gamma/beta = E3.1 medians; df = "
                                 "E3.2's diffusive tail. The generator runs this shape (volatility.json; "
                                 "test_garch_params_in_force), closing DECISION_LOG P2-12.")
    m["garch_shape"]["date"] = TODAY
    m["applied"]["value"]["half_life_days"] = float(rf["params"]["h"])
    m["applied"]["value"]["sigma_V_to_value_json"] = float(rf["params"]["sigma_V"])
    m["applied"]["value"]["sbar_to_volatility_json"] = blk["sbar"]
    m["applied"]["label"] = ("WHICH fitted quantities govern the generator (v2.1 Phase 3): engine name, units, "
                             "half-life and sigma_V (section-9 refit), and -- new -- sbar, now APPLIED through "
                             "volatility.json's identity value (P2-9's hand-over executed). The GARCH shape is "
                             "applied (P2-12 closed).")
    m["applied"]["date"] = TODAY
    m["applied"]["sbar_fitted_not_applied"] = 0.008698868151339125
    m["applied"]["sbar_in_force"] = blk["sbar"]
    m["applied"]["sbar_in_force_source"] = "envs/v2/params/volatility.json (E3.1 identity, PREREG 3.4)"
    with open(mp, "w", encoding="utf-8") as fh:
        json.dump(m, fh, indent=1)
    print("mispricing.json: structural (sigma_V, h) %.6g/%.4g -> %.6g/%.4g; garch_shape applied"
          % (prev_st["sigma_V"], prev_st["h"], rf["params"]["sigma_V"], rf["params"]["h"]))
    print("execution-order rule now applies: re-freeze, hashes, checklist, level-free audit (after_state)")


if __name__ == "__main__":
    main()
