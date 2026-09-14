"""
v2.1 Phase 9 regression tests (plan Section 13.4; PREREG_PHASE_9.md).

    python -m pytest tests/test_v2_1_phase_9.py -q
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
pytestmark = pytest.mark.filterwarnings("ignore")


# ================================================================================================ the provider-options column
def test_provider_options_column_inert(tmp_path):
    """Carried from Phase 8 (addendum 9): a run's CSV must say how its client was configured.  Off (the default None)
    the log is unchanged -- no column, every value identical; on, every row carries the JSON record and nothing else
    moves."""
    import pandas as pd
    from dataclasses import replace
    from experiments.arms_v2 import build_config
    from simulation.runner_v2 import run_simulation_v2
    from tools.phase8.e8_0_golden import fake_llm
    cfg = build_config("fake", "ISFJ", "memory", "flat", 3, T=12, output_dir=str(tmp_path / "off"), dividends=True)
    assert cfg.provider_options is None
    off = run_simulation_v2(replace(cfg, agent_llm=fake_llm([])), verbose=False)
    assert "Provider_Options" not in off.columns
    rec = {"provider": "fake", "config_tag": "t", "temperature_sent": None, "options": {"thinking_budget": 0}}
    on = run_simulation_v2(replace(cfg, agent_llm=fake_llm([]), output_dir=str(tmp_path / "on"), provider_options=rec),
                           verbose=False)
    assert list(on.columns) == list(off.columns) + ["Provider_Options"]
    assert all(json.loads(v) == rec for v in on["Provider_Options"])
    pd.testing.assert_frame_equal(on.drop(columns=["Provider_Options"]), off)
    meta = json.load(open(os.path.join(str(tmp_path / "on"), "fake", "flat", "seed3", cfg.run_id() + ".meta.json"), encoding="utf-8"))
    assert meta["run_config"]["provider_options"] == rec


# ================================================================================================ the runner
def test_candidate_clients_build(monkeypatch):
    """Every candidate configuration builds a client without a call, with the temperature the roster module says is
    SENT; gpt-5 models keep 1.0, the Claude 5 models none, Flash keeps P8-8's thinking budget 0."""
    for k in ("GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(k, "test-key")
    from tools.phase9 import e9_roster as RO
    for mc in RO.CANDIDATES:
        c = RO.make_client(mc)
        rec = RO.provider_options_record(mc, c)
        assert rec["temperature_sent"] == mc.temperature and rec["max_retries"] == 8
        if mc.temperature is not None:
            assert c.temperature == mc.temperature, mc.key
    assert RO.make_client(RO.by_key("gemini-2.5-flash|thinking0")).thinking_budget == 0
    assert RO.by_key("claude-sonnet-5").temperature is None and RO.by_key("claude-opus-5").temperature is None


def test_openrouter_configs_are_pinned_and_capped(monkeypatch):
    """P9-8 and addendum 6, 7: every OpenRouter configuration names exactly one upstream, sends it with
    `allow_fallbacks: false` (measured to fail closed: a wrong upstream returns 404, while allow_fallbacks true routed
    Haiku to Azure), and carries the registered token cap.  Every first-party configuration is UNCHANGED -- no cap, no
    pin -- so no run already on disk is affected."""
    for k in ("GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.setenv(k, "test-key")
    from tools.phase9 import e9_roster as RO
    seen_openrouter = 0
    for key in RO.ROSTER:
        mc = RO.by_key(key)
        client = RO.make_client(mc)
        cap = getattr(client, "max_tokens", None)
        pin = ((getattr(client, "extra_body", None) or {}).get("provider") or {})
        if mc.provider == "openrouter":
            seen_openrouter += 1
            assert mc.upstream, f"{key}: an OpenRouter configuration must name its upstream"
            assert pin.get("order") == [mc.upstream], f"{key}: not pinned to its upstream"
            assert pin.get("allow_fallbacks") is False, f"{key}: fallbacks must be off, or a run can be re-routed"
            assert cap == RO.OPENROUTER_MAX_TOKENS, f"{key}: missing the registered cap (addendum 7)"
            assert RO.provider_options_record(mc, client)["upstream_pinned"] == mc.upstream
        else:
            assert cap is None, f"{key}: a first-party configuration must not gain a cap"
            assert not pin, f"{key}: a first-party configuration must not gain a pin"
    assert seen_openrouter == 5, f"expected the 5 OpenRouter configurations of P9-8, saw {seen_openrouter}"


def test_runner_refuses_above_cap(tmp_path, monkeypatch):
    """P9-1: never more than 15 in-flight calls per model, from one process or from several."""
    from tools.phase9 import e9_runner as R
    monkeypatch.setattr(R, "ACTIVE", str(tmp_path / "active"))
    with pytest.raises(SystemExit):
        R.main(["run", "--manifest", "x.json", "--config", "gpt-5-mini", "--workers", "16"])
    a = R.register("gpt-5-mini", 10)
    with pytest.raises(SystemExit):
        R.register("gpt-5-mini", 6)
    b = R.register("gemini-2.5-flash", 15)                      # the cap is per model
    R.unregister(a)
    c = R.register("gpt-5-mini", 15)
    for p in (b, c):
        R.unregister(p)


# ================================================================================================ E9.3
def _refdist_inputs():
    from tools.phase9.e9_3_simulate import inputs
    return inputs()


@pytest.mark.parametrize("shared,hetero", [(True, False), (False, False), (True, True), (False, True)])
def test_refdist_vectorised_equals_long_frame(shared, hetero):
    """Rule 18: the (n, M, S) difference array equals, dataset by dataset, the memory - static pivot of a long frame of
    arm-level runs built by loops from the same draws -- in both readings, with and without heterogeneity."""
    from tools.phase9.e9_3_simulate import D_from_terms, draw_arm_terms, long_frame_from_terms, paired_matrix
    inp = _refdist_inputs()
    terms = draw_arm_terms(np.random.default_rng(5), 3, 5, 7, 0.03, shared, hetero, inp)
    D = D_from_terms(terms, 0.05)
    for i in range(3):
        np.testing.assert_allclose(paired_matrix(long_frame_from_terms(terms, 0.05, i)), D[i], rtol=0, atol=1e-15)


def test_refdist_heterogeneity_scales_variance():
    """The heterogeneous models' seed x arm and replicate variance is the measured ratio times Flash's (large-n check
    of the construction, not of a rate)."""
    from tools.phase9.e9_3_simulate import D_from_terms, draw_arm_terms
    inp = _refdist_inputs()
    D = D_from_terms(draw_arm_terms(np.random.default_rng(1), 4000, 4, 3, 0.0, False, True, inp), 0.0)
    v = D.var(axis=(0, 2))
    flash = 2 * (inp["path_arm"] + inp["persona_path_arm"] + inp["replicate"])
    gpt = 2 * (inp["path_arm"] + inp["int_ratio"] * inp["persona_path_arm"] + inp["rep_ratio"] * inp["replicate"])
    np.testing.assert_allclose(v[2:], flash, rtol=0.05)
    np.testing.assert_allclose(v[:2], gpt, rtol=0.05)


def test_refdist_bootstrap_equals_pigeonhole():
    """Rule 18: R3's array form equals `tools.stats_v2.pigeonhole_ci` on the same generator, dataset by dataset."""
    import pandas as pd
    from tools.phase9.e9_3_simulate import D_from_terms, bootstrap_R3, draw_arm_terms
    from tools.stats_v2 import pigeonhole_ci
    import tools.phase9.e9_3_simulate as E
    inp = _refdist_inputs()
    D = D_from_terms(draw_arm_terms(np.random.default_rng(2), 3, 4, 6, 0.02, False, False, inp), 0.0)
    out = bootstrap_R3(D, [np.random.default_rng([7, i]) for i in range(3)])
    for i in range(3):
        pairs = pd.DataFrame([{"Model": f"m{m:02d}", "Path": f"p{s:03d}", "d": D[i, m, s]}
                              for m in range(4) for s in range(6)])
        ref = pigeonhole_ci(pairs, n_boot=E.B, rng=np.random.default_rng([7, i]))
        assert abs(ref["ci_lo"] - out["lo"][i]) < 1e-12 and abs(ref["ci_hi"] - out["hi"][i]) < 1e-12
        assert abs(ref["p_boot"] - out["p_boot"][i]) < 1e-12 and abs(ref["estimate"] - out["est"][i]) < 1e-12


def test_refdist_anova_by_hand():
    """R4 against a hand computation of the two-way mean squares on one small matrix."""
    from tools.phase9.e9_3_simulate import analytic
    X = np.array([[0.1, 0.3, 0.2], [0.0, 0.25, 0.05]])
    r = analytic(X[None])
    M, S = X.shape
    g = X.mean(); rm = X.mean(1); cm = X.mean(0)
    ms_m = S * ((rm - g) ** 2).sum() / (M - 1); ms_s = M * ((cm - g) ** 2).sum() / (S - 1)
    ms_e = ((X - rm[:, None] - cm[None, :] + g) ** 2).sum() / ((M - 1) * (S - 1))
    num = max(ms_m + ms_s - ms_e, ms_e)
    assert abs(r["se_R4"][0] - np.sqrt(num / (M * S))) < 1e-15
    assert abs(r["se_R2"][0] - rm.std(ddof=1) / np.sqrt(M)) < 1e-15
    # R5 (addendum 1): R4's variance against t with M - 1 df
    from scipy import stats
    assert abs(r["p_R5"][0] - 2 * stats.t.sf(abs(g / np.sqrt(num / (M * S))), M - 1)) < 1e-15


# ================================================================================================ E9.1
def test_effects_from_pairwise_complete_and_undefined():
    """Addendum 4: an outcome undefined at some seeds is handled once, explicitly.  The paired difference and the
    default sd use the seeds defined in BOTH panels; a cell below the seed floor is dropped; a level that loses more
    than MAX_CELLS_DROPPED cells is NOT DEFINED; and the point estimate is the same function a bootstrap draw calls."""
    from tools.phase9.e9_1_ranking import MAX_CELLS_DROPPED, MIN_SEEDS_PER_CELL, effects_from
    rng = np.random.default_rng(0)
    y0 = rng.normal(size=(12, 100))
    y1 = y0 + 0.5
    full = effects_from(y0, y1)
    assert np.isfinite(full)
    assert effects_from(y0, y1, np.arange(100)) == full          # one function for the estimate and every draw

    above = y1.copy()
    above[0, :100 - MIN_SEEDS_PER_CELL - 10] = np.nan            # cell 0 keeps more than the floor
    v, d = effects_from(y0, above, diagnostics=True)
    assert d["cells_used"] == 12 and d["seeds_min"] == MIN_SEEDS_PER_CELL + 10 and np.isfinite(v) and d["defined"]

    below = y1.copy()
    below[0, :100 - MIN_SEEDS_PER_CELL + 10] = np.nan            # cell 0 falls below the floor and is dropped
    v, d = effects_from(y0, below, diagnostics=True)
    assert d["cells_used"] == 11 and np.isfinite(v)

    many = y1.copy()
    many[: MAX_CELLS_DROPPED + 1, :100 - MIN_SEEDS_PER_CELL + 10] = np.nan
    v, d = effects_from(y0, many, diagnostics=True)
    assert d["cells_used"] == 12 - (MAX_CELLS_DROPPED + 1) and not np.isfinite(v) and not d["defined"]


# ================================================================================================ the wall-clock tool
def test_power_fast_equals_integral():
    """Rule 18: the Gauss-Legendre power rule equals Phase 8's adaptive integral, including at two models and alpha'
    where the mass sits at chi-square values below 6e-5 (addendum 19)."""
    from scipy import stats
    from tools.phase8.e8_5_analyse import power_t_two_sided
    from tools.phase9.e9_wallclock import power_t_two_sided_fast
    a_b = 0.05 / 36
    for M, alpha, ncp in ((2, a_b, 1.2), (2, 0.05, 3.0), (3, a_b, 4.0), (8, a_b, 6.8), (14, 0.05, 2.5), (40, a_b, 5.0)):
        tc = float(stats.t.ppf(1 - alpha / 2, M - 1))
        assert abs(power_t_two_sided_fast(tc, M - 1, ncp) - power_t_two_sided(tc, M - 1, ncp)) < 1e-9


def test_grid_manifest_matches_runs():
    """Plan 13.4: every planned cell has a run with the right hashes and configuration.  While the manifests do not
    exist the test skips; once they do, every run ON DISK must match its manifest (prompt hash, environment code hash,
    harness and placebo versions, configuration tag, model, scenario, seed and start design), and runs still missing
    are counted, never silently passed."""
    from tools.phase9.e9_4_grid import MANIFESTS, OUT, stage_verify
    if not any(os.path.exists(os.path.join(OUT, f)) for f in MANIFESTS.values()):
        pytest.skip("stage 1's manifests are not written yet")
    assert stage_verify() == 0, "a run on disk does not match the manifest it was planned in"
    v = json.load(open(os.path.join(OUT, "verify.json"), encoding="utf-8"))
    assert v["rows"], "verify wrote no rows"


def test_phase9_report_tables_match_files():
    """Rule 15: every PHASE_9_REPORT.md table is generated from its file and read back (`--check` exits 1 when stale)."""
    report = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_9_REPORT.md")
    if not os.path.exists(report):
        pytest.skip("PHASE_9_REPORT.md not written yet")
    from tools.phase9.e9_report_tables import main as rt
    assert rt(["--check"]) == 0, "a PHASE_9_REPORT.md table differs from the file it is generated from"


def test_busy_seconds_union():
    from tools.phase9.e9_wallclock import busy_seconds
    assert busy_seconds([0, 5, 20], [10, 12, 30]) == 22.0
    assert busy_seconds([0], [7]) == 7.0


# ================================================================================================ E9.3 criteria (3.2, addendum 9)
def test_bh_rows_equals_stats_v2():
    """The criteria stage adjusts one family per dataset, vectorised over datasets.  It must equal the project's own
    BH, computed row by row."""
    from tools.phase9.e9_3_simulate import bh_rows
    from tools.stats_v2 import bh_adjust
    rng = np.random.default_rng(11)
    for m in (2, 3, 7, 13):
        p = rng.random((200, m)) ** 3
        ref = np.array([bh_adjust(row) for row in p])
        assert np.allclose(bh_rows(p), ref, rtol=0, atol=0)


def test_criteria_dgp_known_answers():
    """The level DGP and the three criteria on a known answer (addendum 9.1, 9.4): the default-level contrast recovers
    beta, the per-model differenced interaction recovers the true interaction, and with no level x arm x model term
    and a half-width far inside the margin the equivalence is declared at a true interaction of 0 and refused at the
    margin."""
    from tools.phase9.e9_3_simulate import crit_conditions, crit_stats, draw_levels, inputs
    inp = inputs()
    base = [c for c in crit_conditions(inp) if c["M"] == 14 and c["S"] == 93 and c["L"] == 2
            and c["tau_lam_label"] == "0" and c["beta_label"] == "delta"]
    at_zero = [c for c in base if c["int_label"] == "0"][0]
    at_margin = [c for c in base if c["int_label"] == "margin"][0]
    assert at_zero["margin"] == 0.5 * inp["delta"] == 0.025      # read from inference_params, not typed
    s0 = crit_stats(draw_levels(np.random.default_rng([9, 3, 6, 101]), 200, at_zero, inp), at_zero)
    s1 = crit_stats(draw_levels(np.random.default_rng([9, 3, 6, 102]), 200, at_margin, inp), at_margin)
    assert abs(float(np.mean(s0["est_default"])) - at_zero["beta"]) < 0.005
    assert abs(float(np.mean(s0["interaction_est"])) - 0.0) < 0.005
    assert abs(float(np.mean(s1["interaction_est"])) - at_margin["margin"]) < 0.005
    assert float(np.mean(s0["equivalence_declared"])) > 0.95
    assert float(np.mean(s1["equivalence_declared"])) < 0.05
    # a true effect of delta at every level cannot be level-dependent often at this shape
    assert float(np.mean(s0["level_dependent_plain"])) < 0.05


def test_criteria_shared_model_term_travels_across_levels():
    """addendum 9.1: the model x arm term is shared by every level, so differencing per model removes it.  The
    interaction's spread must therefore be far below the spread of the per-level contrasts themselves."""
    from tools.phase9.e9_3_simulate import crit_conditions, crit_stats, draw_levels, inputs
    inp = inputs()
    c = [x for x in crit_conditions(inp) if x["M"] == 14 and x["S"] == 93 and x["L"] == 1
         and x["tau_lam_label"] == "0" and x["beta_label"] == "0" and x["int_label"] == "0"][0]
    s = crit_stats(draw_levels(np.random.default_rng([9, 3, 6, 103]), 300, c, inp), c)
    assert float(np.std(s["interaction_est"], ddof=1)) < 0.5 * float(np.std(s["est_default"], ddof=1))


def test_uncapped_openrouter_rows_are_not_timed():
    """PREREG_PHASE_9_ADDENDUM.md 8: the first OpenRouter smoke ran with no `max_tokens` and is discarded.  Those runs
    completed all 200 calls, so no call-count filter drops them -- `read_ledgers` must, or a discarded configuration
    would be timed beside the registered one in the report's throughput table."""
    from tools.phase9.e9_roster import OPENROUTER_MAX_TOKENS
    from tools.phase9.e9_wallclock import _is_uncapped_openrouter, read_ledgers
    assert _is_uncapped_openrouter({"provider_options": {"provider": "openrouter", "max_tokens_client": None}})
    assert not _is_uncapped_openrouter({"provider_options": {"provider": "openrouter",
                                                             "max_tokens_client": OPENROUTER_MAX_TOKENS}})
    # a first-party route sends no cap by design, and must not be dropped for it
    assert not _is_uncapped_openrouter({"provider_options": {"provider": "google", "max_tokens_client": None}})
    t = read_ledgers()
    if len(t) and "provider_options" in t:
        po = [p for p in t["provider_options"] if isinstance(p, dict) and p.get("provider") == "openrouter"]
        assert po, "no OpenRouter rows survived: the ledgers or the filter are wrong"
        assert all(p.get("max_tokens_client") == OPENROUTER_MAX_TOKENS for p in po)


def test_grid_configs_are_the_measured_roster():
    """P9-10: the grid manifest carries exactly the roster configurations the sizing MEASURED.  The two that failed
    the smoke stopping rule are named in the manifest (`configs_not_piloted`), neither silently included -- they
    could not run -- nor silently dropped; and a roster member missing from the sizing with no registered reason is
    refused, as e9_4_grid's docstring always promised."""
    from tools.phase9 import e9_roster as RO
    from tools.phase9.e9_4_grid import SIZING, grid_configs
    if not os.path.exists(SIZING):
        pytest.skip("e9_2/sizing.json not written yet")
    d = json.load(open(SIZING, encoding="utf-8"))
    configs, left_out = grid_configs(d)
    assert set(configs) | set(left_out) == set(RO.ROSTER) and not set(configs) & set(left_out)
    assert set(left_out) == set(d["not_piloted_registered"])
    assert all(k in d["per_model_band_mas"] for k in configs)
    assert len(configs) == d["plugin_over_n_of_roster"][0]
    bad = dict(d, per_model_band_mas={k: v for k, v in d["per_model_band_mas"].items() if k != configs[0]})
    with pytest.raises(SystemExit):
        grid_configs(bad)
