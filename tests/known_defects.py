"""
Known-defect registry (v2.1 plan, Phase 0, item 0.4; PREREG_PHASE_0.md §6).

Every strict-xfail test of the v2 generator is listed here with the weakness items it documents and the
phase that must make it pass (and then remove the xfail marker AND the entry). A strict xfail keeps the
suite green while the defect persists and fails loudly (XPASS) the moment the defect disappears, so a
"fixed" defect cannot go unnoticed and an unfixed one cannot be forgotten.

v2.1 acceptance rule (plan Section 16): `V2_DEFECTS` is empty.

`tests/test_v2_1_phase_0.py::test_known_defect_registry_matches_strict_xfails` asserts that the strict
xfails collected from the test files equal `V2_DEFECTS` + `V1_BASELINE_XFAILS`; `tests/conftest.py`
prints this registry with the observed outcomes at the end of every pytest session.
"""

# v2.1 Phase 3 cleared its two entries: test_garch_shape_matches_e3_1 (item 12) is HARD -- the generator runs
# the fitted shape (alpha/gamma/beta = E3.1 medians; df = E3.2's diffusive tail, volatility.json) and the
# section-9 refit re-identified the engine's (sigma_V, h) under it (DECISION_LOG P3-*); test_iv_continuity
# (items 46, 25) is HARD with the DERIVED tolerance T_z -- E3.5's IV is a past-only filter of observed returns
# (no phase input, no whole-path quantile), audited against the same filter's forecast (e3_5/audit.json).
# v2.1 Phase 6 re-expressed both entries as the DERIVED gates (PREREG_PHASE_6.md sections 7-8; the margins live in
# evaluation/params/phase6_criteria.json `gates`, written from the target-permutation nulls by
# tools/phase6/e6_criteria_extra.py --stages gates). Each test asserts the gate AS THE FILE HOLDS IT; a strict xfail
# keeps the suite green while the derived gate fails and XPASSes -- loudly -- the moment it passes, at which point the
# entry is removed. The v2 absolute thresholds and the 10 pp margin stay behind run_audit(gates="v2"), reported only.
V2_DEFECTS = [
    {"test": "tests/test_leakage_ci.py::test_v2_L2_surrogate_thresholds", "items": [5, 32, 1, 3],
     "phase": 7, "reason": "DERIVED L2 gate (Phase 6, E6.6): selectivity of the rendered fields over the level-free control "
                           "(FULL - BASE, the audit's GBT) <= the target-permutation null's p95 + the paired half-width. The "
                           "null sits entirely below zero (median -0.047 all rows / -0.069 calm-trained; p95 -0.034 / -0.054), "
                           "so the margin as registered is NEGATIVE and the measured +0.0263 [+0.0106, +0.0402] (all rows) and "
                           "+0.1088 [+0.0849, +0.1307] (calm-trained) FAIL it; under the registered centred sensitivity "
                           "(p95 - median + half-width) all rows is undecided at 20 draws (+0.0263 vs +0.0275, inside a "
                           "half-width; 40 draws pending) and calm-trained FAILS (+0.1088 vs +0.0379) -- the fields' calm "
                           "contribution (VAL, the wandering multiple). Evidence: e6_6/null/null.json; "
                           "PREREG_PHASE_6_ADDENDUM.md section 1. Owner: D17 / Phase 7 (a Phase-5 field decision or D3)"},
    {"test": "tests/test_leakage_ci.py::test_v2_L2b_phase_clock_selectivity", "items": [16],
     "phase": 7, "reason": "DERIVED L2b gate (Phase 6, E6.7): macro-class accuracy of FULL minus the level-free control <= the "
                           "label-permutation null's p95 + the paired half-width (the 10 pp margin frozen after the result "
                           "was known, weakness 32, is retired to gates='v2'). Measured +0.0181 on the Phase-5 state "
                           "(e5_after/audit_after_levelfree.pkl: 67.6 % - 65.8 %); the null and margin are e6_6/null/null.json "
                           "`macro|all` and phase6_criteria.json `gates.l2b`; the entry stands until the file's verdict is PASS, "
                           "when this xfail XPASSes and the entry is removed. History of the statistic: +10.4 pp post-D14 "
                           "(Phase 4), +1.8 pp after the Phase-5 observables redesign (P5-19)"},
]

# Documented v1 baseline defects (E0). Permanent: they describe the frozen v1 generator and are never emptied.
V1_BASELINE_XFAILS = [
    "tests/test_leakage_ci.py::test_v1_L1_no_algebraic_inversion",
    "tests/test_leakage_ci.py::test_v1_L2_surrogate_thresholds",
]


def registry_ids():
    return {d["test"] for d in V2_DEFECTS} | set(V1_BASELINE_XFAILS)
