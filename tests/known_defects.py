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

V2_DEFECTS = [
    {"test": "tests/test_v2_1_phase_1.py::test_flat_x_equivalence", "items": [4, 13],
     "phase": 2, "reason": "Phase 1 removed the jump bias (E1.4: placement x_zero, E[x] -0.069 -> +0.013); the residual +0.013 "
                           "[+0.004, +0.021] at 1,000 seeds is the calm engine's own (jumps off: +0.011 [+0.003, +0.020]) and "
                           "fails the +/- 0.02 equivalence margin by its upper limit; owned by the engine re-fit (Phase 2)"},
    {"test": "tests/test_v2_1_stats.py::test_fundamentalist_share", "items": [2, 11],
     "phase": 2, "reason": "FW switching inert at price_scale = 100: n_f > 0.99 on ~98 % of days"},
    {"test": "tests/test_v2_1_stats.py::test_iv_continuity", "items": [46, 25],
     "phase": 3, "reason": "the phase multiplier enters IV deterministically: one-day log-IV step of z ~ 7"},
    {"test": "tests/test_v2_1_stats.py::test_sustained_bull_selection", "items": [18, 42],
     "phase": 4, "reason": "rejection sampling keeps the quiet sub-population of sustained-bull draws"},
    {"test": "tests/test_leakage_ci.py::test_v2_L2_surrogate_thresholds", "items": [5, 32, 1, 3],
     "phase": 6, "reason": "pre-registered L2 absolute gate fails (anchor + field channels); gate re-derived in Phase 6 after Phases 1 and 5"},
    {"test": "tests/test_leakage_ci.py::test_v2_L2b_phase_clock_selectivity", "items": [16],
     "phase": 6, "reason": "with the level-free control (v2.1 Phase 1) the macro-phase selectivity of the non-price fields is +11.7 pp on "
                           "the published 1,600-path audit against the pre-registered 10 pp margin (the v2 level control passed at "
                           "+8.6 pp only because the price level itself carried the phase); gate re-derived in Phase 6 with the "
                           "level-free reference"},
]

# Documented v1 baseline defects (E0). Permanent: they describe the frozen v1 generator and are never emptied.
V1_BASELINE_XFAILS = [
    "tests/test_leakage_ci.py::test_v1_L1_no_algebraic_inversion",
    "tests/test_leakage_ci.py::test_v1_L2_surrogate_thresholds",
]


def registry_ids():
    return {d["test"] for d in V2_DEFECTS} | set(V1_BASELINE_XFAILS)
