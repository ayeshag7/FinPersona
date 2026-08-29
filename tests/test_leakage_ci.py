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
    return la.run_audit(panel, rendered_market_fields("v2"))


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
@pytest.mark.xfail(strict=True, reason="known defect (registry; items 5, 21, 32): after the v2.1 Phase-0 analyst fix (sd 0.15 as "
                                       "documented, not 0.335) the k*analyst candidate lands inside the 1 % floor on about as many "
                                       "steps as price itself, so amendment A6's L1 rule is marginal: PASS by 0.26 pp at 50 seeds, "
                                       "FAIL at these 8 CI seeds. The rule is re-derived from the x noise floor in Phase 6 (E6.5) "
                                       "after Phase 5 decides the analyst field; the rule is not moved here.")
def test_v2_L1_no_algebraic_inversion(v2_audit):
    assert bool(v2_audit["L1"]["pass"].all()), v2_audit["L1"].to_string()


@pytest.mark.xfail(strict=True, reason="Pre-registered L2 absolute thresholds fail by construction: with a smooth V and a "
                   "persistent dominant x, price history alone predicts x (calm R2 ~0.8) and V (MAPE ~4%). Reported, not "
                   "re-gated (integrity review 23 Aug 2026 withdrew amendment A8 as a gate). If this starts passing, the "
                   "generator changed: revisit.")
def test_v2_L2_surrogate_thresholds(v2_audit):
    v = v2_audit["L2_verdict"]
    assert v["mode"] == "absolute" and v["pass"], v


def test_v2_L2_selectivity_reported_and_no_spurious_fit(v2_audit):
    """Exploratory selectivity of the non-price fields is computed (reported, no gate) and the
    shuffled-V control shows no spurious fit."""
    v = v2_audit["L2_verdict"]
    assert not np.isnan(v["max_selectivity_R2_x"]) and not np.isnan(v["max_MAPE_gain_V"])
    assert v["max_R2_shuffledV"] < 0.1


def test_v2_L2b_phase_clock_selectivity(v2_audit):
    assert v2_audit["L2b"]["pass"], v2_audit["L2b"]


def test_v2_phase_time_separability():
    try:
        from envs.synthetic_market import checklist_paths  # type: ignore
    except ImportError:
        pytest.skip("v2 generator not available yet")
    row = sf.item15_phase_time(checklist_paths(N_SEEDS_CI, T_CI))
    assert row["pass"], row["statistic"]
