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
def test_v2_L1_no_algebraic_inversion(v2_audit):
    """A6's L1 rule. v2.1 Phase 0 registered it as marginal (FAIL at these 8 CI seeds); under the Phase-1 state (mechanism B,
    x_zero jumps, 750-day burn-in) it passes at the CI seeds, so the registry entry is removed (XPASS rule) -- the rule is still
    marginal (PHASE_1_REPORT.md section 4.7) and is re-derived in Phase 6 (E6.5)."""
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


@pytest.mark.xfail(strict=True, reason="registered (Phase 6): with the level-free control (v2.1 Phase 1 default) the macro-phase "
                                       "selectivity of the non-price fields is +11.7 pp on the published 1,600-path audit against the "
                                       "pre-registered 10 pp margin (the v2 level control passed at +8.6 pp only because the price level "
                                       "itself carried the phase); the gate is re-derived in Phase 6 with the level-free reference.")
def test_v2_L2b_phase_clock_selectivity(v2_audit):
    """The evidence is the published audit on the standard evaluation panel (1,600 paths), not this module's 8-seed CI
    panel: at 8 seeds the statistic cannot decide a 10 pp margin and happens to pass. The stored result decides; the CI
    panel is kept as a live guard that the statistic is still computed and in range."""
    import pandas as pd
    rows = pd.read_csv(os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_6",
                                    "audit_after_levelfree_checklist_rows.csv"))
    l2b = rows[rows["item"] == 16].iloc[0]
    live = v2_audit["L2b"]
    assert 0.0 <= float(live["selectivity"]) <= 1.0, live      # live guard: the statistic is computed and in range
    assert bool(l2b["pass"]), l2b.to_dict()                    # the published 1,600-path result decides


def test_v2_phase_time_separability():
    try:
        from envs.synthetic_market import checklist_paths  # type: ignore
    except ImportError:
        pytest.skip("v2 generator not available yet")
    row = sf.item15_phase_time(checklist_paths(N_SEEDS_CI, T_CI))
    assert row["pass"], row["statistic"]
