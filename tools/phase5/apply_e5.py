"""
Write envs/v2/params/observables.json from the Phase-5 generated results, with provenance on every entry.

    python -m tools.phase5.apply_e5 --decisions <json> [--dry-run]

Follows tools/phase4/apply_e4.py's pattern.  Every entry carries label / source / date / interval / n / status and,
where it is not obvious, what the fit is CONDITIONAL on.  No entry ships with "interval": null, and every status is a
term the file's own `_status_key` declares -- envs/v2/observables_params.py raises otherwise.

`--decisions` names the design adopted per block and the evidence file that decided it (written by the phase after
the contests of PREREG_PHASE_5.md sections 4-9 are run); the numbers come from tools/phase5/e5_params.sections(),
so the deployed file cannot differ from the arms that were measured.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase5.e5_params import sections, GEN, ANALYST_LIT_ANCHOR  # noqa: E402

DEST = os.path.join(ROOT, "envs", "v2", "params", "observables.json")
TODAY = str(date.today())

STATUS_KEY = {
    "ADOPTED": "a pre-registered rule decided it on data",
    "INCUMBENT": "the phase stopped for a team decision; the v2 behaviour stays and is labelled as the incumbent, not as a result",
    "NOT DONE": "the experiment did not run or did not conclude; the v2 behaviour stays",
    "PROVISIONAL": "a design carried as the default pending a decision the entry names (a team decision, or a Phase-9 LLM-side test); "
                   "its generator-side audit is done and recorded, the decision that would confirm or replace it is not the phase's to take",
    "TESTED, NOT ADOPTED": "the mechanism is implemented and switchable, and measurement does not support adopting it. Distinct from NOT DONE: the experiment ran and concluded",
    "TESTED, REJECTED": "the entry's central claim was tested and refuted; the v2 behaviour stays in force only for want of an identified replacement",
    "IN FORCE, ADOPTION WITHDRAWN": "the value is deployed and stays deployed, but the evidence that ADOPTED it no longer stands and the criterion that would re-decide it is not currently evaluable",
}


def load(rel):
    return json.load(open(os.path.join(GEN, rel), encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    dec = json.load(open(a.decisions, encoding="utf-8"))
    S = sections(dec["design"])
    e51 = load("e5_1/multiple.json"); e52 = load("e5_2/eps.json"); e53 = load("e5_3/dividends.json")
    e55 = load("e5_5/sentiment.json"); e56 = load("e5_6/volume.json")
    m = S["multiple"]; ep = S["eps"]; dv = S["dividend"]; an = S["analyst"]; se = S["sentiment"]; vo = S["volume"]
    pooled = e51["cross_section_pooled"]
    out = {
        "_note": ("v2.1 Phase 5 (observables). Written by tools/phase5/apply_e5.py from the E5.1-E5.6 result files through "
                  "tools/phase5/e5_params.sections(), the same function that built the arms. Read by envs/v2/observables_params.py, "
                  "which raises if any entry lacks provenance, ships a null interval or carries an undeclared status. Every "
                  "value is FIT, LIT, DESIGN, PROVISIONAL or INCUMBENT and says which."),
        "_status_key": STATUS_KEY,
        "multiple": {
            "value": m, "status": dec["status"]["multiple"],
            "label": dec["label"]["multiple"],
            "source": "e5_1/multiple.json; e5_arms/stats.json (KS check); e5_arms/multiple_*/ablation.json",
            "date": TODAY,
            "n": {"stocks": e51["data"]["n_stocks_with_pe"], "stock_months_positive": e51["data"]["n_stock_months_positive"],
                  "stocks_ar1": e51["persistence"]["n_stocks"]},
            "interval": {"p10_p90_pooled": [pooled["p10"]["value"], pooled["p90"]["value"]],
                         "p10_ci": pooled["p10"]["ci95"], "p90_ci": pooled["p90"]["ci95"],
                         "rho_q_ci": e51["persistence"]["rho_q_quarterly"]["ci95"]},
            "v2_before": {"k_range": [14.0, 22.0], "label": "DESIGN (weakness item 20)"},
            "survivor_vs_literature_gap": "REG-15: set A is survivor-only; the P/E tails and the n/m share are understated relative to the full universe",
            "conditional_on": "design B's within-stock sd is net of the engine's stationary sd(x) and of E5.2's EPS noise (PREREG section 4.2)",
        },
        "eps": {
            "value": ep, "status": dec["status"]["eps"],
            "label": dec["label"]["eps"],
            "source": "e5_2/eps.json (EDGAR basic EPS; 8-K Item 2.02 dates from tools/phase5/fetch_8k.py); e5_2/clock.json",
            "date": TODAY,
            "n": {"quarters": e52["data"]["n_quarters"], "stocks": e52["data"]["n_stocks_with_quarters"],
                  "seasonal_pairs": e52["log_seasonal_change"]["n_pairs"], "loss_quarters": e52["loss_process"]["n_quarters"],
                  "announcement_filings": e52["announcement_lags"]["announcement_8k"]["n_filings"],
                  "announcement_stocks": e52["announcement_lags"]["announcement_8k"]["n_stocks"]},
            "interval": {"s_eps": e52["log_seasonal_change"]["s_EPS_from_robust_sd"]["ci95"],
                         "p_loss": e52["loss_process"]["p_loss"]["ci95"],
                         "nm_share_data": e52["nm_frequency"]["share_ttm_nonpositive"]["ci95"],
                         "lag_p50_td": e52["announcement_lags"]["announcement_8k"]["p50_td"]["ci95"],
                         "pe_cap_p99": pooled["p99"]["ci95"]},
            "v2_before": {"noise_sd": 0.10, "lag": [25, 35], "pe_cap": 200.0, "negative_eps": "impossible; P/E of a non-positive trailing EPS rendered as 200",
                          "label": "DESIGN (weakness item 22)"},
            "design_choices_stated": ("the loss chain is independent of x and of the phase label (a label-tied loss rate would be a phase clock; a "
                                      "V-tied one a hidden-state channel); the level L_q for the residual is the mean |EPS| of the four preceding "
                                      "quarters; trading days = calendar days x 252/365"),
            "survivor_vs_literature_gap": "REG-15: delisted loss-makers are absent, so the loss frequencies are understated",
        },
        "dividend": {
            "value": dv, "status": dec["status"]["dividend"],
            "label": dec["label"]["dividend"],
            "source": "e5_3/dividends.json (EDGAR DPS declared / cash paid)",
            "date": TODAY,
            "n": {"stocks_set_A": e53["payer_share"]["n_set_A"], "stocks_reporting_dps": e53["payer_share"]["n_with_dps_concept"],
                  "payers_set_A": e53["payer_share"]["n_payers_set_A"],
                  "lintner_quarters": e53["stickiness"]["n_quarters"], "payout_stock_years": e53["payout"]["n_stock_years"],
                  "crash_episodes": e53["crash_behaviour"]["n_episodes"]},
            "interval": {"c_speed": e53["stickiness"]["c_speed"]["ci95"], "tau": e53["stickiness"]["tau_target_payout"]["ci95"],
                         "payout_median": e53["payout"]["median"]["ci95"]},
            "v2_before": {"payout": 0.35, "sticky": 0.7, "payer_share": 1.0, "label": "DESIGN (weakness item 22; Lintner's annual speed applied per quarter)"},
            "D10": dec.get("D10", "undecided: both rendering variants carried; the field is rendered under field = 'shown' and omitted under 'hidden'; "
                                  "paying dividends into the agent's cash is the harness half of D10 (simulation/, Phase 7/8)"),
            "crash_behaviour_reported": e53["crash_behaviour"],
        },
        "analyst": {
            "value": an, "status": dec["status"]["analyst"],
            "label": dec["label"]["analyst"],
            "source": "PREREG_PHASE_5.md section 7 (LIT: Bradshaw, Brown & Huang 2013; Bilinski, Lyssimachou & Walker 2013, both read per LOG 4.3); "
                      "e5_arms/analyst_*/ablation.json; e5_7a/baseline/ablation.json (permutation null margin)",
            "date": TODAY,
            "n": {"note": "no free target-price data: the sd is LIT and the phase states plainly that no free data can fit it",
                  "arms_measured": 5, "paths_per_arm": 1600},
            "interval": {"lit_bracket_phase9": [0.30, 0.60], "anchor_mapping": "E|u| = sd sqrt(2/pi), 45 % -> 0.564 if a mean absolute log error",
                         "persistence": "DESIGN, rho 0.95 per 5-day update (no free data)"},
            "v2_before": {"sd": 0.15, "label": "DESIGN, below every read value (weakness item 21)"},
            "horizon_mismatch": "the read anchor is a 12-month target-price error; the field is a fair-value estimate",
            "decision_pending": dec.get("analyst_pending", ""),
        },
        "sentiment": {
            "value": se, "status": dec["status"]["sentiment"],
            "label": dec["label"]["sentiment"],
            "source": "e5_5/sentiment.json (SF Fed daily index deconvolved at lam = 0.95; FF daily market; Shiller CAPE; AAII weekly); "
                      "e5_arms/stats.json (rule i); e5_arms/sentiment_*/ablation.json (rule ii); e5_7c/*/onset.json",
            "date": TODAY,
            "n": {"sf_fed_calendar_days": e55["deconvolution"]["n_days"], "trading_days_aligned": e55["loadings_market_daily"]["full"]["n"],
                  "windows_200d": e55["loadings_market_daily"]["window_200d"]["n_windows"],
                  "aaii_weeks": e55["aaii_weekly"]["n_weeks"], "cape_months": e55["valuation_link_monthly"]["trailing_120m_mean"]["n_months"]},
            "interval": {"rho_window": e55["loadings_market_daily"]["window_200d"]["rho"]["ci95"],
                         "b1_window": e55["loadings_market_daily"]["window_200d"]["b1_per_sd"]["ci95"],
                         "c_val_full_per_sd_per_unit_logdev": e55["valuation_link_monthly"]["trailing_120m_mean"]["ci95_per_sd_raw_daily"],
                         "rho_w_aaii": e55["aaii_weekly"]["window_fits_40w"]["rho"]["ci95"]},
            "v2_before": {"construction": "m_t = 0.6 tanh(2 x_{t-j}) + 0.3 tanh(ret20/0.15); AR 0.85; return 0.25 r/sigma; noise 0.25",
                          "label": "DESIGN (weakness item 23); sentiment read x directly"},
            "design_choices_stated": ("the deconvolution kernel (geometric weights, 5 % depreciation) is LIT read at source; the market-level "
                                      "loadings transfer to a single stock per sd of the standardised return (DESIGN); the valuation coefficient "
                                      "transfers from the log-CAPE deviation to x = log(P/V) (DESIGN); S_raw is a rendering constant with "
                                      "sd(tanh(S z)) = 0.35 (DESIGN); b_pred stays the LIT Tetlock value in every design and the reverse "
                                      "regression on the SF Fed index does NOT reproduce it (reported)"),
            "D15": dec.get("D15", "the team records the default after these results; the rule's selection is recorded here, not the decision"),
        },
        "volume": {
            "value": vo, "status": dec["status"]["volume"],
            "label": dec["label"]["volume"],
            "source": "e5_6/volume.json (set A daily volume); e5_arms/stats.json; e5_arms/volume_*/ablation.json; e5_7c/*/onset.json",
            "date": TODAY,
            "n": {"stocks": e56["data"]["n_stocks"], "runup_episodes": e56["runup_turnover_ratio"]["n_episodes"],
                  "runup_stocks": e56["runup_turnover_ratio"]["n_stocks"]},
            "interval": {"rho_v": e56["design_A"]["rho_v"]["ci95"], "beta_absr": e56["design_A"]["beta_absr_per_sd_z"]["ci95"],
                         "sd_e": e56["design_A"]["sd_e"]["ci95"], "runup_log_ratio": e56["runup_turnover_ratio"]["log_ratio_ci95_stock_boot"],
                         "beta_ru": e56["design_B"]["beta_ru_per_unit_pos_ret252"]["ci95"]},
            "v2_before": {"rho": 0.65, "b_absr": 0.25, "b_absx": 1.2, "sd_e": 0.30,
                          "label": "DESIGN (weakness item 24); the |x| loading has no read source and is DOMINATED"},
            "design_choices_stated": "log volume detrended by its trailing 252-day mean (no shares outstanding in the panel); past-only standardisation",
        },
        "audit_bounds": {
            "value": {"no_field_deterministic_R2": 0.20, "onset_rule": "dAUC <= circular-shift null p95 (measured)",
                      "l2b_margin_phase6_owned": 0.10},
            "status": "PROVISIONAL",
            "label": ("PROVISIONAL bound for test_no_field_is_deterministic_in_x: 0.20 is evaluation/leakage_audit.L2_SELECTIVITY_R2, amendment A8's "
                      "reference value (the plan's own number, not a new stipulation), applied per field group to the add-one R2(x) on all rows; "
                      "Phase 6 derives the margin that replaces it. The onset rule's threshold is the measured null, not a number."),
            "source": "evaluation/leakage_audit.py L2_SELECTIVITY_R2; PREREG_PHASE_5.md section 11",
            "date": TODAY, "n": {"paths": 1600}, "interval": "none: a provisional reference bound, owned by Phase 6",
        },
    }
    if a.dry_run:
        print(json.dumps(out, indent=1)[:4000]); print("\n(dry run; nothing written)"); return
    with open(DEST, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {DEST}")
    import importlib
    import envs.v2.observables_params as OP
    importlib.reload(OP)
    print(f"loader: PRESENT={OP.PRESENT} {OP.summary()} PE_CAP={OP.PE_CAP}")


if __name__ == "__main__":
    main()
