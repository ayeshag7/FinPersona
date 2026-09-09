"""
CI tests for the Section 5 leakage (L1/L2), phase-clock (L2b) and resolvability
(L4) audits and the Section 9 phase/time separability item, run on a small
seed count so they fit in CI (the published tables use 30-50 seeds via the
CLIs).

* For the v1 generator these tests are EXPECTED TO FAIL and are marked
  xfail(strict=True): they document the defects (plan Section 1) and will
  start failing-to-fail (i.e. alert us) if someone "fixes" v1 by accident.
* For the v2 generator (envs/synthetic_market.py exporting `audit_panel` and
  `checklist_paths`) the same assertions must pass; they are skipped until
  the v2 generator exists.
"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agent.render import rendered_market_fields  # noqa: E402
from evaluation import leakage_audit as la  # noqa: E402
from evaluation import stylized_facts as sf  # noqa: E402

N_SEEDS_CI = 8
T_CI = 200


@pytest.fixture(scope="module")
def v1_audit():
    panel = la.v1_panel(N_SEEDS_CI, T_CI)
    return la.run_audit(panel, rendered_market_fields("static"))


@pytest.fixture(scope="module")
def v2_audit():
    try:
        from envs.synthetic_market import audit_panel  # type: ignore
    except ImportError:
        pytest.skip("v2 generator not available yet")
    panel = audit_panel(N_SEEDS_CI, T_CI)
    # v2.1 Phase 5: an undefined P/E (trailing EPS <= 0) is NaN in the frame and the string 'n/m' in the observation; the
    # audit-side convention (PREREG_PHASE_5.md section 10d) encodes it as the P/E cap plus a `reported_PE_nm` indicator
    # passed as a shown field -- without it the NaN APEs of the P/E candidate count as inversions inside L1's floor.
    from tools.phase5.common import encode_nm
    panel = encode_nm(panel)
    shown = list(rendered_market_fields("v2")) + (["reported_PE_nm"] if "reported_PE_nm" in panel.columns else [])
    return la.run_audit(panel, shown)


# ---------------- v1: documented failures ----------------
@pytest.mark.xfail(strict=True, reason="v1 defect 1: EPS = V/15 so P/E inverts to V exactly")
def test_v1_L1_no_algebraic_inversion(v1_audit):
    assert bool(v1_audit["L1"]["pass"].all())


@pytest.mark.xfail(strict=True, reason="v1: valuation fields reconstruct x and V")
def test_v1_L2_surrogate_thresholds(v1_audit):
    assert v1_audit["L2_verdict"]["pass"]


def test_v1_L2b_phase_clock_documented(v1_audit):
    """v1: phases are fixed day indices with deterministic ramps, so even the
    price-only classifier reads the macro phase almost perfectly (30-seed run:
    full 99.8%, price-only 94.9%, day-only 60%); the selectivity margin is
    therefore not the binding failure in v1 -- documented, not xfailed."""
    b = v1_audit["L2b"]
    assert b["acc_full"] > 0.9 and b["acc_price_only"] > 0.85


def test_v1_phase_time_confound_documented():
    """v1: phases are fixed day indices, so WITHIN a scenario the day predicts the
    macro phase perfectly (the confound, plan diagnosis 2). The plan's mixed-set
    criterion (< 80%) is met even by v1 because bull and crash assign different
    classes to the same day index, so the within-scenario number is the one that
    documents the defect."""
    paths = {"flat": [sf.from_v1_env("flat", s, T_CI) for s in range(N_SEEDS_CI)],
             "bull_trap": [sf.from_v1_env("bull_trap", s, T_CI) for s in range(N_SEEDS_CI)],
             "crash": [sf.from_v1_env("crash", s, T_CI) for s in range(N_SEEDS_CI)]}
    row = sf.item15_phase_time(paths)
    assert "within-scenario mean 100.0%" in row["statistic"], row["statistic"]


def test_v1_L4_flat_coverage_is_tiny(v1_audit):
    """Audit F-2 / plan diagnosis 9: almost no resolvable steps in flat at theta=0.05."""
    l4 = v1_audit["L4"]
    flat = l4[(l4.scenario == "flat") & (l4.phase == "ALL")].iloc[0]
    assert flat["coverage_theta_0.05"] < 0.10


def test_v1_L1_exact_inversion_documented(v1_audit):
    """The defect itself, asserted positively so the baseline number is on record."""
    l1 = v1_audit["L1"].set_index("candidate")
    pe = l1.loc["k * P / reported_PE"]
    assert abs(pe["fitted_k"] - 15.0) < 0.05
    assert pe["median_APE"] < 0.005 and not pe["pass"]   # rounding of the rendered P/E (1 dp) only


# ---------------- v2: must pass ----------------
def test_v2_L1_no_algebraic_inversion(v2_audit):
    """A6's L1 rule. v2.1 Phase 0 registered it as marginal (FAIL at these 8 CI seeds); under the Phase-1 state (mechanism B,
    x_zero jumps, 750-day burn-in) it passes at the CI seeds, so the registry entry is removed (XPASS rule) -- the rule is still
    marginal (PHASE_1_REPORT.md section 4.7) and is re-derived in Phase 6 (E6.5)."""
    assert bool(v2_audit["L1"]["pass"].all()), v2_audit["L1"].to_string()


@pytest.mark.xfail(strict=True, reason="DERIVED L2 gate (v2.1 Phase 6, E6.6): the selectivity of the rendered fields over the "
                   "level-free control must be <= the target-permutation null's p95 + the paired half-width, on all rows and "
                   "calm-trained (phase6_criteria.json `gates.l2_all` / `gates.l2_calm`, written from e6_6/null/null.json). "
                   "The null sits entirely below zero, so the registered margin is negative and both populations FAIL; the "
                   "centred sensitivity is reported beside (PREREG_PHASE_6_ADDENDUM.md section 1). The v2 absolute thresholds "
                   "are reported under gates='v2' only. An XPASS here means the derived gate passes: remove the registry entry.")
def test_v2_L2_surrogate_thresholds(v2_audit):
    """The gate as the criteria file holds it. The CI panel's own L2 verdict (v2 absolute form) is reported in the
    assertion message for the record; the derived verdict is the file's, computed on the 1,600-path panel."""
    from evaluation import criteria as CR
    v = v2_audit["L2_verdict"]
    g_all, g_calm = CR.gate("l2_all")["value"], CR.gate("l2_calm")["value"]     # CriteriaError until the nulls are written
    assert g_all["pass"] and g_calm["pass"], {"derived_all": g_all, "derived_calm": g_calm, "ci_panel_v2_absolute": v}


def test_v2_L2_selectivity_reported_and_no_spurious_fit(v2_audit):
    """Exploratory selectivity of the non-price fields is computed (reported, no gate) and the
    shuffled-V control shows no spurious fit.

    v2.1 Phase 2: the shuffled-V bound is decided on the PUBLISHED audit, not on this module's 8-seed CI panel,
    for the reason `test_v2_L2b_phase_clock_selectivity` already gives -- at 8 seeds the permutation can align
    by chance and the statistic cannot decide a 0.1 bound. On the standard evaluation panel (1,600 paths,
    288,000 rows) the value is -0.0023; on the 8-seed panel it is 0.102. The bound is unchanged; only the
    evidence it is applied to is, and the CI panel is kept as a live range guard. DECISION_LOG P2-13."""
    import json
    import pickle
    v = v2_audit["L2_verdict"]
    assert not np.isnan(v["max_selectivity_R2_x"]) and not np.isnan(v["max_MAPE_gain_V"])
    assert -1.0 < v["max_R2_shuffledV"] < 0.5, v["max_R2_shuffledV"]        # live guard on the CI panel
    published = None
    for rel in (("e2_6_after", "audit_after_levelfree.pkl"), ("e1_6", "audit_after_levelfree.pkl")):
        p = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", *rel)
        if os.path.exists(p):
            with open(p, "rb") as fh:
                published = pickle.load(fh)["L2_verdict"]
            break
    if published is None:
        pytest.skip("no published level-free audit on disk yet")
    assert published["max_R2_shuffledV"] < 0.1, json.dumps(
        {k: float(published[k]) for k in ("max_R2_shuffledV",)})


@pytest.mark.xfail(strict=True, reason="DERIVED L2b gate (v2.1 Phase 6, E6.7): the macro-class selectivity of the rendered fields "
                                       "over the level-free control must be <= the label-permutation null's p95 + the paired "
                                       "half-width (phase6_criteria.json `gates.l2b`, from e6_6/null/null.json `macro|all`); the "
                                       "10 pp margin frozen after the result was known is retired to gates='v2'. An XPASS here means "
                                       "the derived gate passes on the 1,600-path panel: remove the registry entry.")
def test_v2_L2b_phase_clock_selectivity(v2_audit):
    """The evidence is the published audit on the standard evaluation panel (1,600 paths) and the null simulated on it,
    not this module's 8-seed CI panel: at 8 seeds the statistic cannot decide a margin of a few tenths of a point. The
    file's verdict decides; the CI panel is kept as a live guard that the statistic is still computed and in range."""
    import pandas as pd
    from evaluation import criteria as CR
    g = CR.gate("l2b")["value"]                                                  # CriteriaError until the null is written
    rows = pd.read_csv(os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_6",
                                    "audit_after_levelfree_checklist_rows.csv"))
    l2b = rows[rows["item"] == 16].iloc[0]
    live = v2_audit["L2b"]
    assert 0.0 <= float(live["selectivity"]) <= 1.0, live      # live guard: the statistic is computed and in range
    assert g["pass"], {"derived_l2b": g, "ci_panel_live": live, "phase1_published_row_under_the_v2_margin": l2b.to_dict()}


def test_v2_phase_time_separability():
    try:
        from envs.synthetic_market import checklist_paths  # type: ignore
    except ImportError:
        pytest.skip("v2 generator not available yet")
    row = sf.item15_phase_time(checklist_paths(N_SEEDS_CI, T_CI))
    assert row["pass"], row["statistic"]
