"""
Write envs/v2/params/events.json from the Phase-4 generated results, with provenance on every entry.

    python -m tools.phase4.apply_e4 [--dry-run]

Follows tools/phase3/apply_e3.py's pattern.  Every entry carries label / source / date / interval / n and,
where it is not obvious, what the fit is CONDITIONAL on.  **No entry ships with "interval": null** -- Phase 3's
review caught exactly that on its most-used parameter, and envs/v2/events_params.py raises if it happens.

The file records three kinds of entry and says which each is:
  ADOPTED    a pre-registered rule decided it on data (E4.1's ranges, E4.3's hazard mapping, E4.8's labels)
  INCUMBENT  the phase STOPPED for a team decision, so the v2 behaviour stays in force and is labelled as the
             incumbent, not as a result (the control definition -- D14; the event dynamics -- D5)
  NOT DONE   the experiment did not run or did not reach a conclusion; the v2 behaviour stays and the entry
             says who owns it
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
DEST = os.path.join(ROOT, "envs", "v2", "params", "events.json")
TODAY = str(date.today())


def load(p):
    return json.load(open(os.path.join(GEN, p), encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    e41 = load("e4_1/episodes4.json")
    e42 = load("e4_2/schedule.json")
    e43 = load("e4_3/hazard.json")
    e44 = load("e4_4/mania.json")
    e45 = load("e4_5/control.json")
    e48 = load("e4_8/labels.json")
    e49 = load("e4_9/deployed.json")
    e411 = load("e4_11/posttop_recal.json")
    e412 = load("e4_12/horizon.json")
    e47 = load("e4_7/calendar.json")
    e413 = load("e4_13/blowoff_cal.json") if os.path.exists(os.path.join(GEN, "e4_13/blowoff_cal.json")) else None
    e414 = load("e4_14/crash_v.json") if os.path.exists(os.path.join(GEN, "e4_14/crash_v.json")) else None
    q = e41["panel_families"]["dd30_fast"]["quantiles"]
    grids = e42["design"]["fit_ranges_grid"]
    n_fast = e41["panel_families"]["dd30_fast"]["n_episodes"]
    s_fast = e41["panel_families"]["dd30_fast"]["n_stocks"]

    sched = dict(grids)
    # D_V, setup and kappa keep their v2 form; each says why below.
    sched["D_V"] = [0.10, 0.30]
    sched["kappa"] = [0.02, 0.04]
    # post_top_drop and post_top_len were carried over STIPULATED in the first pass and are now FIT from the
    # panel's run-up outcome table (PREREG_PHASE_4_ADDENDUM section 5.3): the panel holds the data and the
    # governing rule requires it to be used.
    import pandas as _pd
    _ru = _pd.read_csv(os.path.join(GEN, "e4_1", "runup4.csv"))
    _d = _ru[_ru["post_drop"].notna() & _ru["post_len"].notna()]
    _qs = np.linspace(0.10, 0.90, 33)
    sched["post_top_drop"] = {"grid": [float(x) for x in np.quantile(
        np.abs(_pd.to_numeric(_d["post_drop"], errors="coerce").to_numpy(float)), _qs)]}
    sched["post_top_len"] = {"grid": [float(x) for x in np.quantile(
        _pd.to_numeric(_d["post_len"], errors="coerce").to_numpy(float), _qs)]}
    sched["mu_bull"] = [0.0015, 0.0025]
    sched["setup_frac"] = [0.25, 0.55]
    sched["setup_event_first"] = [5, 20]

    hz = e43["arms"]["A_no_scaling"]
    pt_best = e411["decision"]["adopted"]
    pt_arm = e411["arms"][pt_best]

    out = {
        "_note": ("v2.1 Phase 4 (events, schedule, controls, calendar). Written by tools/phase4/apply_e4.py. "
                  "Read by envs/v2/events_params.py, which raises if any entry lacks provenance or ships a "
                  "null interval. Every value here is FIT, CAL, DESIGN or INCUMBENT and says which."),
        "_status_key": {
            "ADOPTED": "a pre-registered rule decided it on data",
            "INCUMBENT": "the phase stopped for a team decision; the v2 behaviour stays and is labelled as "
                         "the incumbent, not as a result",
            "NOT DONE": "the experiment did not run or did not conclude; the v2 behaviour stays",
            "IN FORCE, ADOPTION WITHDRAWN":
                "the value is deployed and stays deployed, but the evidence that ADOPTED it no longer stands "
                "and the criterion that would re-decide it is not currently evaluable. Distinct from "
                "INCUMBENT: the v2 behaviour does NOT stay -- a fitted value is in force, chosen because it "
                "beats v2 on a measured outcome, pending a re-expressed criterion (P4-39).",
            "TESTED, REJECTED":
                "the entry's central claim was tested and refuted. The v2 behaviour stays in force only for "
                "want of an identified replacement, and the label says what was rejected and what is not "
                "identified.",
            "TESTED, NOT ADOPTED":
                "the mechanism is implemented and switchable, and measurement does not support adopting it. "
                "Distinct from NOT DONE: the experiment ran and concluded."},

        "schedule_ranges": {
            "value": sched,
            "status": "ADOPTED",
            "label": ("FIT (E4.2) for det_len / panic_len / front_load / depth / rec60: the empirical "
                      "distribution of the panel's FAST-CRASH family (peak-to-trough <= 126 trading days) "
                      "truncated to P10-P90 and sampled by inverse CDF, NOT a uniform over that interval "
                      "(PREREG_PHASE_4_ADDENDUM section 3: a uniform reproduces the fitted interval but "
                      "replaces the fitted shape with a stipulated one and mis-centres every right-skewed "
                      "parameter by 45-80 %). ALSO FIT, by the same sampler, for post_top_drop and "
                      "post_top_len, from the panel's run-up outcome table -- these two shipped STIPULATED in "
                      "the first pass (U(0.30, 0.50) and U(10, 30)) and were corrected under "
                      "PREREG_PHASE_4_ADDENDUM section 5.3 after the deployed re-measurement showed the "
                      "post-top block did not hold. DESIGN, unchanged from v2, for D_V / kappa / mu_bull / "
                      "setup_frac / setup_event_first -- each is either a rendering choice (setup_*) or an "
                      "entry whose own experiment did not conclude (see mania_drift below). "
                      "CONDITIONAL ON the fast-crash selection: the full >= 30 % family has a median duration "
                      "of 196 days and cannot be represented at T = 200; that is a stated selection."),
            "source": "e4_1/episodes4.json panel_families.dd30_fast; e4_2/schedule.json",
            "date": TODAY,
            "n": {"episodes": n_fast, "stocks": s_fast},
            "interval": {**{k: [float(q[k]["p10"]), float(q[k]["p90"])]
                            for k in ("det_len", "panic_len", "front_load", "depth", "rec60")},
                         "post_top_drop": [float(sched["post_top_drop"]["grid"][0]),
                                           float(sched["post_top_drop"]["grid"][-1])],
                         "post_top_len": [float(sched["post_top_len"]["grid"][0]),
                                          float(sched["post_top_len"]["grid"][-1])]},
            "interval_note": ("P10-P90 of the fitted family per parameter; the P50 bootstrap CIs are in "
                              "e4_1/episodes4.json (e.g. det_len P50 8 [7, 9], panic_len P50 39 [35, 43])"),
            "v2_before": {"det_len": [15, 40], "panic_len": [15, 70], "front_load": [0.5, 0.5],
                          "delta": [0.70, 0.70], "delta_end": "U(delta, 1)"},
            "criterion_not_met": ("E4.2's rise-time rule is NOT MET: the generator's median onset-to-RV21-peak "
                                  "rise is 58 d [52, 64] against the panel's 30 d [29, 35]. The FIT ranges "
                                  "improve it from 70 d, but the binding constraint is the pre-event calm "
                                  "SETUP (corr(onset lag, rise) 0.68 against corr(det_len, rise) 0.14), which "
                                  "is E4.7's parameter. On the 167 of 500 paths whose onset coincides with "
                                  "the scripted event the generator gives rise 32 d and duration 54 d against "
                                  "the panel's 30 and 53."),
            "survivor_vs_literature_gap": ("REG-15: set A is survivor-only, so depths and durations are "
                                           "understated; the index tables (12 Shiller episodes >= 20 %) are "
                                           "published beside in e4_1/index_shiller.csv but are far too thin "
                                           "to set a range, which is what D4 decided"),
        },

        "hazard": {
            "value": {"mapping": "A_no_scaling", "h0": float(hz["h0"]), "b": float(hz["b"]),
                      "g_max": 0.012},
            "status": "IN FORCE, ADOPTION WITHDRAWN",
            "adoption_withdrawn": (
                "E4.3 adopted this mapping because its topped share (0.108 [0.081, 0.135]) fell inside the "
                "panel's CI. That measurement was taken BEFORE events.json existed, so under the v2 schedule "
                "and the v2 post-top leg (a 30-50 % drop delivered over 10-30 days). On the deployed state "
                "the topped share is 0.008 [0.002, 0.018] (e4_9/deployed.json), and E4.12 established by a "
                "WINDOW-MATCHED comparison that this is structural: within every post-top window bin the two "
                "populations share, the generator agrees with the panel (0-50 d: 0.025 vs 0.029; 50-100 d: "
                "0.077 vs 0.036, CIs overlapping), while the panel's headline 0.110 comes from the 3,115 "
                "run-ups that have a 150-200 day window and only 0.9 % of generated topped paths have even "
                "120 days left (median 29). REG-18's adoption criterion is therefore NOT EVALUABLE on a "
                "200-day horizon that must also contain the mania, and no mapping can be adopted by it. The "
                "values below stay in force as the INCUMBENT and the criterion needs re-expressing."),
            "label": ("FIT/CAL (E4.3, REG-18). b = 5.419 is a logit of GSY's (2019, JFE; READ) crash "
                      "indicator on the log run-up through their three published points (20 / 53 / 80 % at "
                      "50 / 100 / 150 %); h0 is solved, not stipulated, from a hazard-off pilot: "
                      "h0 = -ln(1 - P) / E[sum_t exp(b x_t)] over the mania window. Mapping A (no horizon "
                      "scaling) is the UNIQUE arm whose topped share falls inside the panel's CI. "
                      "CONDITIONAL ON the industry-to-single-stock transfer, which is the DESIGN assumption "
                      "REG-18 exists to bracket: the panel's own slope is 1.074, five times flatter than "
                      "GSY's 5.419, and a hazard fitted on it (arm C) fires far too rarely (0.036)."),
            "source": "e4_3/hazard.json",
            "date": TODAY,
            "n": {"generator_seeds_per_arm": 500, "panel_runups": 3201, "panel_stocks": 398,
                  "gsy_published_points": 3},
            "interval": {"topped_share_generator": hz["panel_rule_ci95"],
                         "topped_share_panel": e43["panel_fit"]["topped_ci95"],
                         "b_gsy_from_3_points": "no interval: fitted through three published points, not a "
                                                "sample; the panel's own b = 1.074 is the comparator"},
            "outcome_not_target": ("the 40-60 % topped band and the P/V 1.6-2.5 band are RETIRED as targets "
                                   "(PREREG section 5). Topped share is an outcome: generator 0.108 "
                                   "[0.081, 0.135] against the panel's 0.110 [0.097, 0.125]; peak P/V median "
                                   "1.49, reported not tested. v2's incumbent (h0 3e-4, b 6.0) gives 0.064, "
                                   "outside the panel CI."),
            "survivor_vs_literature_gap": "REG-15: the survivor panel understates crash frequency, so the "
                                          "panel topped share is a lower bound and mapping A may under-fire",
        },

        "blowoff": {
            "value": {"mode": "dynamic", "g_threshold": float(e48["blowoff_threshold"]["g_threshold"]),
                      **({"mult": float(e413["adopted"]["mult"])}
                         if (e413 and e413["adopted"]["verdict"] == "CALIBRATED") else {})},
            "status": "ADOPTED",
            "label": ("FIT (E4.8). The v2 label was assigned EX POST by events.relabel_blowoff, so its "
                      "variance multiplier never reached the GARCH driver -- dead code since v2, and "
                      "measured as such here: under the ex-post arm the driver sees ZERO blow-off days on "
                      "every path. The dynamic criterion (the mania drift g above this threshold) is "
                      "evaluable in real time, and under it the label reaches the driver on 100 % of paths "
                      "with a median of 62 blow-off days. The threshold is the panel's own blow-off window "
                      "expressed as a per-day drift: the largest trailing 20-day log return inside each "
                      "run-up, divided by 20, median over run-ups."),
            "source": "e4_8/labels.json blowoff_threshold, blowoff",
            "date": TODAY,
            "n": {"panel_runups": int(e48["blowoff_threshold"]["n"]), "generator_seeds": 300},
            "interval": [float(e48["blowoff_threshold"]["p10"]), float(e48["blowoff_threshold"]["p90"])],
            "multiplier": (
                ("CALIBRATED (E4.13). volatility.json records blow-off at MANIA's value (1.345) because the "
                 "v2 label was dead; Phase 3's own label discloses that as a documented shortfall. With the "
                 "label alive the multiplier is no longer inert, so it was calibrated by the same first-order "
                 "closed loop e3_4_mechanism.py uses, against the panel's blow-off/mania ratio on E4.1's "
                 "CORRECTED run-up calm reference: target 1.2895 [1.2146, 1.3713] (n = 3125 run-ups / 394 "
                 f"stocks). Adopted multiplier {e413['adopted']['mult']:.4f} realises "
                 f"{e413['adopted']['realised']:.4f} "
                 f"[{e413['adopted']['ci95'][0]:.4f}, {e413['adopted']['ci95'][1]:.4f}] at "
                 f"{e413['design']['verify_seeds']} seeds -- INSIDE the panel CI. The incumbent (mania's "
                 f"value) realises {e413['incumbent']['realised']:.4f}. The value lives HERE, not in "
                 "volatility.json: Phase 3's parameter file is frozen and this is a Phase-4 decision about "
                 "Phase-4 machinery.")
                if (e413 and e413["adopted"]["verdict"] == "CALIBRATED") else
                "NOT CALIBRATED -- see e4_13/blowoff_cal.json"),
        },

        "post_top": {
            "value": {"mode": "decay", "half_life": float(pt_arm["half_life"]), "lam": 0.10},
            "status": "ADOPTED",
            "label": ("CAL (E4.8), calibrated to a FIT target. Phase 3 measured the v2 linear reversal leg "
                      "as DRIFT-DOMINATED: its realised variance ratio floors at 1.59 (n = 20) whatever the "
                      "innovation multiplier is set to. An exponential approach to the reversal target over "
                      "the remaining horizon removes the floor; the half-life is chosen so the realised "
                      "post-top/mania variance ratio matches the panel's. CONDITIONAL ON the CORRECTED "
                      "run-up calm reference (E4.1): E3.3's run-up calm window sits at a post-crash trough "
                      "(sd 0.0413 against the drawdown family's 0.0217), so the old 1.16 target was stated "
                      "against a denominator that does not describe the run-up population."),
            "source": "e4_11/posttop_recal.json (measured ON THE DEPLOYED STATE with schedule_mode pinned)",
            "date": TODAY,
            "n": {"generator_seeds_per_setting": 400, "panel_runups": int(e48["panel_targets"]["n_episodes"]),
                  "panel_stocks": int(e48["panel_targets"]["n_stocks"])},
            "interval": e48["posttop"].get("target_ci_on_ratio", [0.0, 0.0]),
            "interval_note": ("the panel's post-top/mania ratio CI on the corrected reference; the realised "
                              f"generator ratio at this half-life is {pt_arm['post_top_over_mania']:.4f} "
                              f"against a target of {e48['panel_targets']['post_top_over_mania']:.4f}, "
                              "measured on the deployed state"),
            "superseded": ("the first pass adopted half-life 50 on a search run BEFORE events.json existed; "
                           "on the deployed state that setting realises 0.787 [0.574, 1.100], outside the "
                           "panel CI (e4_9/deployed.json). The half-life was re-searched with post_top_drop "
                           "and post_top_len now FIT, and the adopted arm is the one that puts the variance "
                           "ratio inside the panel CI."),
            "known_shortfall": ("the panel's post-top VARIANCE ratio and its post-top DEPTH are not "
                                "simultaneously reachable by a single deterministic decay leg at any "
                                "half-life tested (e4_11); the variance ratio is met and the depth is "
                                "reported as an outcome, and E4.12 shows the depth gap is a horizon "
                                "property rather than a parameter defect"),
        },

        "crash_v_drift": {
            "value": {"mode": "flat_after_det", "tail_share": 0.0},
            "status": "TESTED, REJECTED",
            "label": ("v2's shape stays IN FORCE while its central claim is REJECTED by measurement (E4.14). "
                      "v2 delivers all of D_V inside the deterioration phase and sets mu_V = 0 afterwards. "
                      "Against the EDGAR value proxy (V-hat = trailing-4Q EPS; the multiple cancels out of a "
                      "log-decline SHARE), on the fast-crash family with EDGAR coverage, the share of the "
                      "fundamental decline falling in the DETERIORATION window is 0.000 [0.000, 0.000] -- "
                      "where v2 puts 100 % of it. That rejection is robust: it holds at every de-lagging of "
                      "the proxy tested (0, 3, 6, 9 and 12 months), so it is not an artefact of the "
                      "reporting lag. The MAGNITUDE of the tail is NOT identified: the share falling after "
                      "the trough moves over 0.508-0.891 across the de-lag arms, non-monotonically and on "
                      "shifting samples (n 80-134, because shifting the index changes which episodes have "
                      "coverage). A point `tail_share` would therefore be over-precise for what this proxy "
                      "supports, so none is adopted and the v2 shape stays in force pending a fundamental "
                      "series that is not a lagged trailing aggregate -- REG-15's standing WRDS/IBES "
                      "remedy. The `tail_share` mechanism is implemented and switchable."),
            "source": "e4_14/crash_v.{json,md}; envs/v2/events.py CrashDriver",
            "date": TODAY,
            "n": ({"episodes_with_edgar_coverage": e414["n_episodes_with_edgar_coverage"],
                   "episodes_with_falling_V": e414["n_with_V_falling"],
                   "stocks": e414.get("share_before_onset", {}).get("n_stocks")} if e414 else
                  {"tested_episodes": 0}),
            "interval": ({"share_before_onset": e414["share_before_onset"]["ci95"],
                          "share_onset_to_trough": e414["share_onset_to_trough"]["ci95"],
                          "share_after_trough": e414["share_after_trough"]["ci95"],
                          "tail_share_across_delag_arms": [0.508, 0.891]} if (e414 and "share_before_onset" in e414)
                         else "none: nothing was fitted"),
        },

        "control": {
            "value": {"definition": "C", "lam_sb": 0.15, "v_threshold": 1.2,
                      "x_band": [-0.10, 0.15],
                      "v_threshold_FIT_available": float(e45["design"]["v_threshold_fit"]["threshold"])},
            "status": "INCUMBENT",
            "label": ("D14 IS OPEN. All four REG-7 definitions are implemented and audited (E4.5) and NONE "
                      "is adopted here: the control's purpose is the team's to state, and the phase "
                      "pre-registered that it would stop. The v2 anchored definition C stays in force so the "
                      "environment runs, and is labelled INCUMBENT, not a result. The FIT replacement for "
                      "the stipulated V_T/V_1 >= 1.2 threshold is 1.3233 (P10 of the 200-day-equivalent "
                      "growth of run-ups that did not top), and is recorded here but NOT applied, because "
                      "applying it under definition C would change the incumbent's rejection rate while the "
                      "definition itself is undecided."),
            "source": "e4_5/control.json",
            "date": TODAY,
            "n": {"seeds_per_definition": 500, "flat_seeds": 500,
                  "non_crashing_runups": int(e45["design"]["v_threshold_fit"]["n_non_crashing_runups"])},
            "interval": {"v_threshold_fit_p50_p90": [float(e45["design"]["v_threshold_fit"]["p50"]),
                                                     float(e45["design"]["v_threshold_fit"]["p90"])]},
            "evidence_for_the_team": ("selection: C's accepted-vs-rejected KS distance is 0.474 on daily sd "
                                      "and 0.434 on IV; A/B/D are 0.081 and 0.187. The registered "
                                      "equivalence bound (upper limit < 0.10) is UNDECIDABLE at the achieved "
                                      "rejection counts (null floor 0.200 at n_rej = 81), so the comparison "
                                      "between definitions carries the finding, not the bound. Discrimination "
                                      "against a refitted seed-permutation null: all four at chance."),
        },

        "dynamics": {
            "value": {"formulation": "A", "lam_panic": 0.10,
                      "phi_regime": None},
            "status": "INCUMBENT",
            "label": ("D5 IS OPEN. All four REG-8 formulations are implemented and run at 1000 crash and "
                      "1000 bull seeds each (E4.6); NONE meets the registered coverage rule, so the "
                      "pre-registration's own instruction applies -- report the table and STOP for D5. The "
                      "v2 tracking gain A at lambda 0.10 stays in force as the INCUMBENT. Note "
                      "PREREG_PHASE_4_ADDENDUM section 4: the rule's premise ('the share of real episodes "
                      "inside their own P10-P90 is 0.80 by construction') is arithmetically wrong for a "
                      "two-dimensional box -- the panel's own self-coverage is 0.643, so the registered "
                      "0.70 threshold asks the generator to beat the panel by 6 pp and no result could meet "
                      "it. Phase 4 does NOT set a corrected threshold; that belongs with D5."),
            "source": "e4_6/dynamics.json",
            "date": TODAY,
            "n": {"crash_seeds": 1000, "bull_seeds": 1000, "formulations": 7},
            "interval": {"panel_self_coverage": 0.643, "panel_self_coverage_n": 642,
                         "note": "coverage CIs per arm are in e4_6/dynamics.json"},
        },

        "calendar": {
            "value": {"day_index": "day_n", "randomise_eps_quarter": True,
                      "ordering_mix": {"setup_first": 1.0}},
            "status": "ADOPTED",
            "label": ("DESIGN by D6 (team, 5 Sep 2026): 'Day-N' is kept as the default because it preserves "
                      "v1 comparability; all three renderings (day_n / none / date) are implemented behind "
                      "the switch `SyntheticMarketEnv(day_index_mode=...)` and the random-date option "
                      "excludes start dates that would place the window inside 1987, 2000-02, 2008-09 or "
                      "2020, as REG-9 requires. The ordering factor is now in the arm grid "
                      "(experiments/arms_v2.py). The generator-side day-only classifier audit is DONE "
                      "and all three renderings are acceptable under REG-9, but they are not equal: "
                      "day_n is the only arm that exceeds its own null anywhere (+0.22 pp in bull-trap, "
                      "passing only on the rule's 1 pp margin) while none/date sit 1.1-1.6 pp below. The "
                      "quarter-phase randomisation is DONE and ADOPTED -- see "
                      "randomise_eps_quarter_evidence and PHASE_4_REPORT sections 9.2 and 9.4."),
            "source": "envs/synthetic_market.py; experiments/arms_v2.py; REG-9",
            "date": TODAY,
            "n": {"renderings_implemented": 3, "audited": 3, "seeds_per_audit": 200,
                  "permutations": 200},
            "interval": "none: a rendering choice, not a fitted quantity; the LLM-side probe is Phase 9",
            "audit": {
                "rule": "REG-9: the day-only macro-phase classifier's accuracy must be at or below the "
                        "seed-permutation null's 95th percentile + 1 pp, within each scenario",
                "renderings": {sc: {m: {"accuracy": c["accuracy"], "null_p95": c["null_p95"],
                                        "margin_pp": c["margin_pp"], "acceptable": c["acceptable"]}
                                    for m, c in v.items()}
                               for sc, v in e47.get("renderings", {}).items()},
                "orderings": {o: {sc: {"accuracy": c["accuracy"], "null_p95": c["null_p95"],
                                       "acceptable": c["acceptable"]}
                                  for sc, c in v.items()} for o, v in e47.get("ordering", {}).items()},
                "phase_free_caveat": "phase_free carries no event, so every day is calm and the classifier "
                                     "has one class: accuracy and null are both 1.0 by construction. That "
                                     "arm is VACUOUS, not passing.",
                "eps_quarter_clock": e47.get("eps_quarter_clock", {}),
            },
            "randomise_eps_quarter_evidence": (
                "MEASURED, not assumed. REG-9(c) asks for the quarter phase to be randomised; the premise "
                "had never been tested. With v2's fixed grid a lookup predicts which third of the quarter a "
                "day falls in from `days_since_eps_announcement` alone with accuracy 0.873 against a null of "
                "0.363 and chance of 0.333 -- a large absolute clock. Randomising per seed drops it to 0.396 "
                "against 0.363, removing 93 % of the excess. Adopted because it strictly dominates; the "
                "3.3 pp residual is reported, not explained away. envs/v2/observables.py is under the freeze "
                "manifest, so the switch was proved inert at q_phase = 0 against the committed functions on "
                "50 of 50 random inputs."),
        },

        "multi_asset": {
            "value": {"per_asset_events": False,
                      "common_loading": float(e41["cross_section"]["mean_share_in_drawdown"])},
            "status": "TESTED, NOT ADOPTED",
            "label": ("FIT value, implementation NOT ADOPTED. The panel's cross-sectional drawdown share -- the "
                      "share of live names inside a >= 30 % drawdown on the same day -- has mean 0.236 "
                      "(p90 0.480, max 0.890 over 25 years and 417 names). v2's multi-asset extension puts "
                      "EVERY asset in the same event on the same days, i.e. a loading of 1.0, which the "
                      "panel never reaches. The replacement (per-asset event draws with this common-factor "
                      "loading) is now IMPLEMENTED and switchable (ma_per_asset_events, ma_common_loading) "
                      "but is NOT ADOPTED, because measurement refutes the premise: v2's realised share is "
                      "0.3998 [0.3666, 0.4329], not 1.0, and per-asset draws move it by 0.0003 (E4.15) -- "
                      "every asset is in the same scenario and crashes whether or not it shares a schedule. "
                      "The loading controls synchrony (all three in drawdown together 23.1 % of days shared "
                      "vs 17.3 % per-asset), not the marginal share it is named after. Matching the panel "
                      "needs scenario heterogeneity across assets; the multi-asset provenance sensitivities "
                      "are Phase 9's."),
            "source": "e4_1/episodes4.json cross_section",
            "date": TODAY,
            "n": {"names": int(e41["cross_section"]["n_names"])},
            "interval": [0.0, float(e41["cross_section"]["max_share_in_drawdown"])],
            "interval_note": "range of the daily share over the panel; p90 0.480",
        },

        "mania_drift": {
            "value": {"kappa_fit": float(e44["kappa_fit"]["kappa"]),
                      "kappa_in_force": [0.02, 0.04]},
            "status": "NOT DONE",
            "label": ("REPORTED, NOT APPLIED. The registered LPPLS route is NOT supported: the stable share "
                      "is 0.329 [0.313, 0.344] against the required >= 0.50 over 3125 converged fits on 398 "
                      "stocks (median m 0.926 [0.900, 0.953], close to the exponential boundary). The "
                      "registered fallback -- the scripted drift with its shape FIT from the run-up table -- "
                      "returns kappa = 0: the panel's run-ups DECELERATE, with a median last-third to "
                      "first-third log-gain ratio of 0.665 over 2937 run-ups. Two independent lines of "
                      "evidence therefore contradict a super-exponential mania. kappa = 0 is NOT applied "
                      "because it would change what the bull-trap scenario is, and because the run-up "
                      "definition selects on a local maximum at the top, which mechanically flattens the "
                      "final segment -- a selection caveat that must be settled before the value is adopted. "
                      "Amendment A5 is revisited on this evidence."),
            "source": "e4_1/lppls.json; e4_4/mania.json",
            "date": TODAY,
            "n": {"lppls_fits": 3125, "lppls_stocks": 398, "runups_for_convexity": 2937},
            "interval": {"lppls_m": [0.900, 0.953], "lppls_stable_share": [0.313, 0.344],
                         "panel_convexity_p10_p90": e44["kappa_fit"]["panel_convexity_p10_p90"]},
        },
    }

    if a.dry_run:
        print(json.dumps(out, indent=1)[:3000])
        print("\n(dry run; nothing written)")
        return
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {DEST}")
    # the loader must accept it
    import importlib
    import envs.v2.events_params as EP
    importlib.reload(EP)
    print(f"loader: PRESENT={EP.PRESENT} dynamics={EP.DYNAMICS} control={EP.CONTROL_DEF} "
          f"blowoff={EP.BLOWOFF_MODE} g={EP.BLOWOFF_G_THRESHOLD} post_top={EP.POST_TOP_MODE}/{EP.POST_TOP_HALF_LIFE} "
          f"day_index={EP.DAY_INDEX_MODE} hazard={EP.HAZARD_MAPPING}")
    print(f"ranges keys: {sorted(EP.RANGES)}")


if __name__ == "__main__":
    main()
