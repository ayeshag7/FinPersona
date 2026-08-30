"""
Numbers that the documents state, checked against the code and the generated files (v2.1 plan, Phase 0, item 0.4 /
"Tests" of Section 4; weakness items 71, 72, 44, 39).

The canonical values live in docs/env_v2/generated/v2_1/phase0_numbers.json (written by tools/verify_v2_findings.py).
Documents that describe the environment (spec, calibration report, status notes) must not carry a stale phrase; the
signed record (DECISION_LOG.md) keeps its history, so every line of it that carries a stale phrase must carry a
"[Phase 0 correction" marker.
"""
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs", "env_v2")
NUMBERS = os.path.join(DOCS, "generated", "v2_1", "phase0_numbers.json")


@pytest.fixture(scope="module")
def num():
    if not os.path.exists(NUMBERS):
        pytest.skip("phase0_numbers.json not generated yet (python -m tools.verify_v2_findings)")
    return json.load(open(NUMBERS, encoding="utf-8"))


def _read(rel):
    return open(os.path.join(DOCS, rel), encoding="utf-8").read()


def test_code_constants_match_canonical_numbers(num):
    from envs.v2.generator import GenConfig, HAZARD_H0, HAZARD_B, G_MAX_CAL
    from envs.v2.garch import OMEGA_MULT
    from envs.v2 import mispricing as mp, events as ev, observables as obs
    cfg = GenConfig()
    assert cfg.jump_rate == num["jump_rate"] == 0.010 and cfg.jump_mean == num["jump_mean"] and cfg.jump_sd == num["jump_sd"]
    assert OMEGA_MULT["sustained-bull"] == num["sustained_bull_variance_multiplier"] == 1.0
    assert (HAZARD_H0, HAZARD_B, G_MAX_CAL) == (num["hazard_h0"], num["hazard_b"], num["g_max"]) and ev.G_MAX == num["g_max"]
    assert mp.HALF_LIFE_FALLBACK_DAYS == 150.0 and abs(num["pull_rate_half_life_days"] - 150.0) < 0.5
    assert abs(mp.load_params(mp.ENGINE_DEFAULT).phi - num["phi_live"]) < 1e-9
    assert obs.ANALYST_SD == num["analyst_sd_documented"] == 0.15 and obs.ANALYST_RHO == num["analyst_rho"]
    # v2.1 Phase 1: burn-in and jump placement moved to params/value.json; the Phase-1 numbers file is canonical for them
    # (phase0_numbers.json keeps the frozen v2 values 260 d / x_negmean for the record)
    from envs.v2 import value_params as VP
    num1 = json.load(open(os.path.join(DOCS, "generated", "v2_1", "phase1_numbers.json"), encoding="utf-8"))
    assert cfg.burn_in == VP.BURN_IN["days"]["default"] == num1["value_json"]["burn_in"]["days"]["default"]
    assert cfg.jump_placement == num1["value_json"]["jump"]["placement"] and num["burn_in"] == 260


def test_long_pilot_numbers_are_the_documented_ones(num):
    assert 141 <= num["long_pilot_half_life_min"] and num["long_pilot_half_life_max"] <= 156
    assert abs(num["long_pilot_half_life_mean"] - num["pull_rate_half_life_days"]) <= 8.0
    # the sd(x) discrepancy explained: raw-weight pilot / engine pilot = w_bar
    ratio = num["sd_x_raw_200k_e017"] / num["sd_x_engine_200k_e017"]
    assert abs(ratio - num["w_bar_20k"]) < 0.01
    assert 0.16 <= num["sd_x_engine_200k_e016"] <= 0.17 and 0.12 <= num["sd_x_raw_200k_e017"] <= 0.14


def test_analyst_before_after(num):
    assert 0.31 <= num["analyst_sd_bench_before"] <= 0.38          # the sqrt(5) defect: 0.15 * sqrt(5) = 0.335
    if "analyst_sd_bench_after" in num:
        assert abs(num["analyst_sd_bench_after"] / 0.15 - 1.0) <= 0.10


STALE = [
    (r"'sustained-bull': 0\.25\}\.", "sustained-bull multiplier 0.25 as the value in force"),
    (r"sustained-bull 0\.25\) scale", "sustained-bull multiplier 0.25 as the value in force"),
    (r"\b18[78](\.5)? d\b(?!.*(withdrawn|sampling error|short pilot))", "the withdrawn 187/188-d half-life"),
    (r"fw_single_stock_fallback`:", "the pre-Phase-0 engine name as the engine in force"),
]
DESCRIPTIVE = ["spec/E1_V2_GENERATOR_SPEC.md", "spec/CALIBRATION_REPORT.md", "status/E1_E4_STATUS.md", "status/PILOT_NOTES.md", "generated/README.md", "README.md"]


@pytest.mark.parametrize("rel", DESCRIPTIVE)
def test_descriptive_documents_carry_no_stale_statement(rel):
    text = _read(rel)
    for pat, what in STALE:
        for m in re.finditer(pat, text):
            line = text[text.rfind("\n", 0, m.start()) + 1: text.find("\n", m.end())]
            assert "Phase 0" in line, (rel, what, line[:160])


def test_decision_log_stale_lines_are_annotated():
    text = _read("decisions/DECISION_LOG.md")
    for line in text.splitlines():
        if re.search(r"60-120 d window|\| on, 0\.008/day|~70-day realised|72 d realised", line):
            assert "[Phase 0 correction" in line, line[:160]


def test_canonical_statements_present(num):
    spec = _read("spec/E1_V2_GENERATOR_SPEC.md"); cal = _read("spec/CALIBRATION_REPORT.md")
    for text in (spec, cal):
        assert "150-day PULL-RATE half-life" in text or "Pull-rate half-life ln2/(mu n_bar phi) = 150.0 d" in text
        assert "147 d" in text and "fw_fallback_hl150" in text
        assert "sustained-bull **1.0**" in text or "'sustained-bull': 1.0}" in text
    assert "0.010/day" in spec and "sqrt(5)" in spec
    pilot = _read("status/PILOT_NOTES.md")
    assert "normalised against constant-mix" in pilot and "three** scenarios" in pilot


def test_sensitivity_counts_in_calibration_report_match_csvs(num):
    cal = _read("spec/CALIBRATION_REPORT.md")
    want = {"fw_index": (8, 7), "pruna": (7, 8), "hl60": (7, 8), "omega_mode": (7, 8), "panic3": (9, 6), "panic6": (8, 7)}
    for k, (p, f) in want.items():
        csv = tuple(num["sensitivity_counts_csv"][f"checklist_v2_sens_{k}"])
        assert csv == (p, f), (k, csv)
    for row, (p, f) in (("`fw_index`", (8, 7)), ("`pruna`", (7, 8)), ("`fw_hl60`", (7, 8)), ("`scale_mode = omega`", (7, 8)), ("panic multiplier 3", (9, 6)), ("panic multiplier 6", (8, 7))):
        line = [ln for ln in cal.splitlines() if ln.startswith(f"| {row}")]
        assert line and f"| {p} / {f} |" in line[0], (row, line)
