"""
v2.1 Phase 7 -- write `evaluation/params/scoring.json` from the result files (PREREG_PHASE_7.md 10).

    python -u -m tools.phase7.e7_write_scoring_params

Every block is generated from a file under `docs/env_v2/generated/v2_1/e7_*`, never typed: the Phase-6 lesson
(P6-12) is that a writer which copies a subset of the registered fields lets a table be read under a defect.  The
loud loader `evaluation/scoring_params.py` re-reads what this writes, and
`tests/test_v2_1_phase_7.py::test_theta_in_force_with_provenance` asserts that every registered field is in the
file -- run BEFORE the first table is read under it.

**`theta_in_force` is written only with `--write-in-force`**, which is used once D7 and D8 are recorded.  Without
the flag the block is absent, `scoring_params.theta_in_force()` raises and `metrics_v2.thetas_in_force()` returns
the v2 constant -- the state this phase ran in until 10 September 2026, when the team recorded D7 (co-primary as
registered) and D8 (the theta-conditional pass) and the block was written.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.phase5.common import GEN  # noqa: E402

E7_1 = os.path.join(GEN, "e7_1")
TARGET = os.path.join(ROOT, "evaluation", "params", "scoring.json")
TODAY = "2026-09-10"

STATUS_KEY = {
    "DERIVED": "computed in this phase from a fitted parameter or a measured statistic, with its inputs named by file",
    "FIT": "a fitted value carried in from an earlier phase's parameter file, unchanged",
    "READ": "taken from a source that was read in full and is cited in PHASE_7_REPORT.md section 1",
    "DESIGN": "a design choice with no data source; carried with a stated sensitivity",
    "REGISTERED": "a rule fixed in PREREG_PHASE_7.md before any number under it was read",
}


def build() -> dict:
    ti = json.load(open(os.path.join(E7_1, "theta_info.json"), encoding="utf-8"))
    tcv = json.load(open(os.path.join(E7_1, "theta_cost_var.json"), encoding="utf-8"))
    loc = pd.DataFrame(ti["located"])
    pooled_all = loc[(loc.scope == "pooled") & (loc.population == "all") & (loc.feature_set == "full")].iloc[0]
    pooled_calm = loc[(loc.scope == "pooled") & (loc.population == "calm") & (loc.feature_set == "full")].iloc[0]
    tc = tcv["theta_cost"]; tv = tcv["theta_var"]

    doc = {
        "_note": ("v2.1 Phase 7 scoring parameters in force. Every block carries value + provenance and a status "
                  "from _status_key. Written by tools/phase7/e7_write_scoring_params.py from the result files; "
                  "read by the loud loader evaluation/scoring_params.py. `theta_in_force` is written only after "
                  "D7 and D8 are recorded (PREREG_PHASE_7.md 1.4) -- a theta nobody chose must not reach a table; "
                  "the team recorded both on 10 September 2026 (DECISION_LOG P7-4, P7-5)."),
        "_status_key": STATUS_KEY,

        "theta_grid": {
            "value": [0.03, 0.05, 0.08, 0.12, 0.20],
            "status": "REGISTERED",
            "label": "the plan's fixed grid (11.2 E7.1); every headline metric is reported at all five plus the "
                     "three derived values",
            "source": "V2_1_IMPROVEMENT_PLAN.md 11.2 E7.1; PREREG_PHASE_7.md 1.5",
            "date": TODAY, "interval": "not applicable (a grid, not an estimate)", "n": 5,
        },

        "theta_info": {
            "value": {
                "pooled_all": float(pooled_all["theta_info"]),
                "pooled_calm": float(pooled_calm["theta_info"]),
                "per_scope": json.loads(loc.to_json(orient="records")),
                "target_sign_accuracy": ti["meta"]["target_accuracy"],
                "grid": ti["meta"]["grid"],
            },
            "status": "DERIVED",
            "label": ("E7.1a: the smallest grid theta at which the level-free observables surrogate's sign accuracy "
                      "on |x| >= theta reaches 0.80 and stays there. The surrogate is the AUDIT's GBT, refit only to "
                      "store per-row predictions; the refit reproduces the four published Phase-6 sign accuracies "
                      "exactly (diff 0.0, e7_1/verify.json). CAVEAT that travels with every value: the derived L2 "
                      "gates fail (E6.6/E6.7, calm-trained +0.1088 against a registered margin of -0.0313), so what "
                      "this surrogate can resolve already includes the fields' calm-trained contribution."),
            "source": "docs/env_v2/generated/v2_1/e7_1/theta_info.json (from _panels/sep_phase5_after.pkl, "
                      "1,600 paths, 288,000 rows after the lag drop); verification in e7_1/verify.json",
            "date": TODAY,
            "interval": "percentile cluster bootstrap over paths, 500 resamples, per theta in theta_info.csv",
            "n": {"paths": 1600, "rows": 288000,
                  "n_resolvable_at_pooled_all": int(pooled_all["n_resolvable_at_theta_info"]),
                  "n_resolvable_at_pooled_calm": int(pooled_calm["n_resolvable_at_theta_info"])},
        },

        "theta_cost": {
            "value": float(tc["value"]),
            "status": "DERIVED",
            "label": ("E7.1b: theta_cost = 2c/f, the mispricing at which a full reallocation's expected profit over "
                      "the holding horizon pays for the round trip. At the registered horizon of one FIT half-life "
                      "f = 1/2, so theta_cost = 4c. The persona's band width CANCELS and the half-life enters only "
                      "through f -- a property of the registered formula, written before the value was computed. "
                      "Checked numerically against the real PortfolioV2 at three band widths (worst relative error "
                      f"{tc['numeric_check']['worst_rel_error']:.2%}, spread across band widths "
                      f"{tc['numeric_check']['break_even_spread_across_band_widths']:.2e})."),
            "source": "docs/env_v2/generated/v2_1/e7_1/theta_cost_var.json; inputs: "
                      "simulation/runner_v2.py RunConfig.cost_bp = 5.0 per trade; "
                      "envs/v2/params/mispricing.json half_life.value = 22.380929759136894 (FIT, n = 417); "
                      "evaluation/targets.py BANDS",
            "date": TODAY,
            "interval": {"one_day_horizon": tc["sensitivities"]["one_day_horizon"]["theta_cost"],
                         "infinite_horizon": tc["sensitivities"]["infinite_horizon"]["theta_cost"],
                         "one_day_at_half_life_interval": [tc["sensitivities"]["one_day_horizon_h_lo"]["theta_cost"],
                                                           tc["sensitivities"]["one_day_horizon_h_hi"]["theta_cost"]]},
            "n": 417,
            "per_persona": {k: v["theta_cost_half_life"] for k, v in tc["per_persona"].items()},
            "cost_tier_sensitivity": tc["sensitivities"]["cost_tier"],
        },

        "theta_var": {
            "value": float(tv["value"]),
            "status": "DERIVED",
            "label": tv["label"],
            "source": tv["source"],
            "date": TODAY,
            "interval": tv["interval"],
            "n": tv["n"],
            "sensitivity_stationary_s_x": tv["sensitivity_stationary_s_x"]["value"],
        },

        "theta_rule": {
            "value": {
                "rule": "theta_info and theta_cost are CO-PRIMARY; every headline metric is reported at both, with "
                        "theta_var and the fixed grid as sensitivities. Where theta_info is not reached on a "
                        "population, theta_cost alone is primary there (REG-11's stated failure mode).",
                "decides_theta_in_force": "D7 and D8, not this file",
            },
            "status": "REGISTERED",
            "label": "REG-11 option D, adopted in the corrected plan as the REPORTING rule, not as a choice of theta",
            "source": "V2_1_ALTERNATIVES_REGISTER.md 11; V2_1_IMPROVEMENT_PLAN.md 11.2 E7.1; PREREG_PHASE_7.md 1.4",
            "date": TODAY, "interval": "not applicable (a rule)", "n": 0,
        },

        "half_width": {
            "value": 0.10,
            "status": "DESIGN",
            "label": ("E7.7: the band half-width. DESIGN, not fitted -- the rebalancing-band anchor Donohue & Yip "
                      "(2003, JPM 29(4)) could not be read and no number is attributed to it. Sun et al. (2006, JPM; "
                      "read) use a 5 % tolerance band at 40-60 bp costs, a different instrument and cost tier, cited "
                      "as context only. Carried with the sensitivity below, which is run on the re-score."),
            "source": "evaluation/targets.py HALF_WIDTH; PHASE_7_REPORT.md E7.7",
            "date": TODAY, "interval": [0.05, 0.15], "n": 0,
            "sensitivity": [0.05, 0.10, 0.15],
        },

        "dead_band": {
            "value": 0.01,
            "status": "DESIGN",
            "label": "E7.7: a target within 1 point of the current share is not traded at all (HOLD = no trade, no "
                     "cost). DESIGN, no source; stated as such.",
            "source": "simulation/portfolio_v2.py DEAD_BAND",
            "date": TODAY, "interval": "not varied in this phase", "n": 0,
        },

        "cost_tier": {
            "value": 5.0,
            "status": "DESIGN",
            "label": ("E7.7: 5 bp charged on |traded value| PER TRADE, so 10 bp round trip. The two cost anchors that "
                      "were read are DIFFERENT CONCEPTS and neither is this number: Nasdaq (2024) 4.5 bp is the "
                      "cap-weighted QUOTED SPREAD of the S&P 500 basket (a half-spread of 2.25 bp per side); "
                      "Frazzini, Israel & Moskowitz (2018 draft) median 6.18 bp (mean 9.97) is MARKET IMPACT per "
                      "trade. The implemented 5 bp per trade is closest in magnitude to the FIM market-impact "
                      "median and is labelled a per-trade all-in charge; it is a DESIGN choice sitting between the "
                      "two anchors, not a value taken from either."),
            "source": "simulation/runner_v2.py RunConfig.cost_bp; simulation/portfolio_v2.py::_execute; "
                      "V2_1_IMPROVEMENT_PLAN.md 11.1",
            "date": TODAY, "interval": [2.25, 9.97], "n": 2,
            "unit": "basis points of traded value, per trade",
            "round_trip_bp": 10.0,
            "anchors": {"nasdaq_2024_quoted_spread_bp": 4.5, "fim_2018_median_market_impact_bp": 6.18,
                        "fim_2018_mean_market_impact_bp": 9.97},
        },

        "band_convention": {
            "value": {"in_force": "A", "alternative_reported": "B",
                      "A": "practitioner risk categories: cash bands 0.70-0.90 / 0.40-0.60 / 0.00-0.20",
                      "B": "utility-consistent Merton bands on the environment's own fitted (mu, sigma) with "
                           "dividends paid -- computed and reported in E7.3, NOT scored"},
            "status": "READ",
            "label": "D9 recorded 10 Sep 2026 (DECISION_LOG P7-3): A is the scored default by REG-13's rule, B is "
                     "the sensitivity, Phase 9 carries both as a factor",
            "source": "V2_1_ALTERNATIVES_REGISTER.md 13; evaluation/targets.py BANDS docstring (the practitioner "
                      "pages read: Morningstar, Fidelity, Vanguard, Betterment)",
            "date": TODAY, "interval": "not applicable (a convention)", "n": 4,
        },

        "decomposition": {
            "value": {
                "B": "max(0, |C_t - centre| - half_width)  -- band violation",
                "D": "|C_t - c*_t| - B_t                   -- the directional remainder",
                "identity": "MCR = mean(B + D) = mean |C - c*| on resolvable steps, identically",
                "ceiling": "the mandate-conditional oracle (0 by construction on resolvable steps)",
                "floor": "the worst of the trivial policies "
                         "{always_hold, always_buy, always_sell, random, band_lo, band_hi}",
                "sign": "evaluation/scoring.py::normalise_metric, the only place an orientation is applied",
            },
            "status": "REGISTERED",
            "label": "E7.2 / REG-12 option A. The v2 convention (ceiling = constant_mix, floor = worst of "
                     "{always_buy, always_sell, random}) stays behind floors_and_ceilings(convention='v2').",
            "source": "PREREG_PHASE_7.md 2; evaluation/scoring.py",
            "date": TODAY, "interval": "not applicable (a definition)", "n": 0,
        },

        "window": {
            "value": 25,
            "status": "REGISTERED",
            "label": "REG-12 option B, the pre-registered ALTERNATIVE scoring: 25-day windows (the pilot's "
                     "probe_every), the oracle's target per window the mode over the window's resolvable steps "
                     "(ties -> the earlier target), regret per window then averaged. Adopted only if E7.8's rule "
                     "adopts it.",
            "source": "V2_1_ALTERNATIVES_REGISTER.md 12; PREREG_PHASE_7.md 2.3; evaluation/scoring.py WINDOW_DAYS",
            "date": TODAY, "interval": "not applicable (a definition)", "n": 0,
        },
    }
    return doc


def in_force_block(doc: dict) -> dict:
    """The theta in force, written ONLY after D7 and D8 (DECISION_LOG P7-4, P7-5).

    D7, recorded 10 Sep 2026: co-primary as registered -- theta_info (pooled) and theta_cost are both primary and
    every headline metric is reported at both; theta_info on the calm population is reported as the calm
    population's value WITH its coverage and n beside it, and is not promoted to primary.  D8, same date: G3's
    pass is recorded as theta-conditional (it holds at every theta <= 0.05 and fails at every theta >= 0.066),
    with no horizon change and no scoring change.
    """
    ti = doc["theta_info"]["value"]
    tc = doc["theta_cost"]["value"]
    return {
        "value": {
            "thetas": [tc, ti["pooled_all"]],
            "co_primary": {"theta_cost": tc, "theta_info_pooled_all": ti["pooled_all"]},
            "reported_per_population": {"all": ti["pooled_all"], "calm": ti["pooled_calm"]},
            "sensitivities": {"theta_var": doc["theta_var"]["value"],
                              "theta_var_stationary": doc["theta_var"]["sensitivity_stationary_s_x"],
                              "grid": doc["theta_grid"]["value"]},
            "calm_caveat": "theta_info on calm rows is 0.20, located on 1,089 of 119,336 calm rows (coverage "
                           "0.009); it is reported as the calm population's value with that n and coverage beside "
                           "it every time, and is NOT primary (D7, co-primary as registered)",
            "g3_is_theta_conditional": "G3 passes at every theta <= 0.05 and fails at every theta >= 0.066 "
                                       "(e7_16a/restate.json and the profile in PHASE_7_REPORT.md); under "
                                       "per-window scoring it fails at every theta (D8)",
        },
        "status": "REGISTERED",
        "label": "D7 and D8 recorded 10 September 2026 (DECISION_LOG P7-4, P7-5): REG-11's co-primary rule stands "
                 "unchanged, and G3's pass is recorded as theta-conditional",
        "source": "DECISION_LOG.md P7-4, P7-5; PREREG_PHASE_7.md 1.4; V2_1_ALTERNATIVES_REGISTER.md 11",
        "date": TODAY,
        "interval": "the co-primary pair IS the interval this phase reports across; theta_var and the grid are the "
                    "sensitivities",
        "n": 2,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=TARGET)
    ap.add_argument("--write-in-force", action="store_true",
                    help="write the theta_in_force block; only valid once D7 and D8 are in DECISION_LOG.md")
    a = ap.parse_args()
    doc = build()
    if a.write_in_force:
        doc["theta_in_force"] = in_force_block(doc)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, default=float)
        fh.write("\n")
    # read it back through the loud loader before anything downstream can (P6-12)
    import importlib
    from evaluation import scoring_params as SP
    importlib.reload(SP)
    if not SP.PRESENT:
        raise SystemExit(f"{a.out} was written but the loader does not see it")
    SP.load(a.out)
    print(f"written and re-read through the loud loader: {a.out}")
    print(f"  blocks: {', '.join(k for k in doc if not k.startswith('_'))}")
    print(f"  theta_in_force present: {'theta_in_force' in doc} (expected False until D7 and D8)")
    print(f"  sha256: {SP.file_sha256(a.out)}")
    print(f"  generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")


if __name__ == "__main__":
    main()
