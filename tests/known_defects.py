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
V2_DEFECTS = [
    {"test": "tests/test_leakage_ci.py::test_v2_L2_surrogate_thresholds", "items": [5, 32, 1, 3],
     "phase": 6, "reason": "pre-registered L2 absolute gate fails (anchor + field channels); gate re-derived in Phase 6 after Phases 1 and 5"},
    {"test": "tests/test_leakage_ci.py::test_v2_L2b_phase_clock_selectivity", "items": [16],
     "phase": 6, "reason": "with the level-free control (v2.1 Phase 1) the macro-phase selectivity of the non-price fields is "
                           "+10.4 pp on the 1,600-path audit of v2.1 Phase 4's POST-D14 hand-over, against the "
                           "pre-registered 10 pp margin (+10.7 pp pre-D14, +12.7 pp at Phase 3, +11.7 pp at Phase 1, "
                           "+15.4 pp at Phase 2; the v2 level control passed at +8.6 pp only because the price level "
                           "itself carried the phase). Two DIFFERENT movements, and the distinction matters: the event "
                           "redesign narrowed it 1.94 pp WITHOUT reducing the field channel -- full-field accuracy was "
                           "unchanged (0.782507 -> 0.782618) and the whole narrowing was the price-only baseline rising, "
                           "so the gap closed from the wrong side (P4-34). Adopting control definition A then narrowed it "
                           "a further 0.39 pp the RIGHT way: full-field accuracy fell 0.782618 -> 0.760160 (-2.25 pp) and "
                           "worst-group selectivity R2(x) fell 0.6878 -> 0.4821 (P4-45). Evidence: "
                           "e4_21/audit_after_levelfree.pkl (post-D14), e4_16_preD14/ (pre-D14). Gate re-derived in "
                           "Phase 6 with the level-free reference"},
]

# Documented v1 baseline defects (E0). Permanent: they describe the frozen v1 generator and are never emptied.
V1_BASELINE_XFAILS = [
    "tests/test_leakage_ci.py::test_v1_L1_no_algebraic_inversion",
    "tests/test_leakage_ci.py::test_v1_L2_surrogate_thresholds",
]


def registry_ids():
    return {d["test"] for d in V2_DEFECTS} | set(V1_BASELINE_XFAILS)
