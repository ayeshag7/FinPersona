"""
The grid harness on this branch: the tests of tests/test_v2_1_phase_9.py (main) that concern RUNNING the grid, and
nothing that needs the analysis tools left on main.

    python -m pytest tests/test_grid_runner.py -q
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pytestmark = pytest.mark.filterwarnings("ignore")


# ================================================================================================ the provider-options column
def test_provider_options_column_inert(tmp_path):
    """A run's CSV must say how its client was configured. Off (the default None) the log is unchanged: no column,
    every value identical; on, every row carries the JSON record and nothing else moves."""
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
    meta = json.load(open(os.path.join(str(tmp_path / "on"), "fake", "flat", "seed3", cfg.run_id() + ".meta.json"),
                          encoding="utf-8"))
    assert meta["run_config"]["provider_options"] == rec


# ================================================================================================ the roster and the runner
def test_candidate_clients_build(monkeypatch):
    """Every candidate configuration builds a client without a call, with the temperature the roster module says is
    SENT; gpt-5 models keep 1.0, the Claude 5 models none, Flash keeps thinking budget 0."""
    for k in ("GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
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
    """Every OpenRouter configuration names exactly one upstream, sends it with `allow_fallbacks: false` (measured to
    fail closed: a wrong upstream returns 404, while allow_fallbacks true routed Haiku to Azure), and carries the
    registered token cap. Every first-party configuration is unchanged: no cap, no pin."""
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
            assert cap == RO.OPENROUTER_MAX_TOKENS, f"{key}: missing the registered cap"
            assert RO.provider_options_record(mc, client)["upstream_pinned"] == mc.upstream
        else:
            assert cap is None, f"{key}: a first-party configuration must not gain a cap"
            assert not pin, f"{key}: a first-party configuration must not gain a pin"
    assert seen_openrouter == 5, f"expected the 5 OpenRouter configurations of P9-8, saw {seen_openrouter}"


def test_runner_refuses_above_cap(tmp_path, monkeypatch):
    """Never more than 15 in-flight calls per model, from one process or from several (P9-1)."""
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


# ================================================================================================ the grid
def test_grid_configs_are_the_measured_roster():
    """The grid manifest carries exactly the roster configurations the sizing MEASURED. The two that failed the smoke
    stopping rule (P9-10) are named in the manifest, neither silently included nor silently dropped; a roster member
    missing from the sizing with no registered reason is refused."""
    from tools.phase9 import e9_roster as RO
    from tools.phase9.e9_4_grid import SIZING, grid_configs
    if not os.path.exists(SIZING):
        pytest.skip("e9_2/sizing.json not present")
    d = json.load(open(SIZING, encoding="utf-8"))
    configs, left_out = grid_configs(d)
    assert set(configs) | set(left_out) == set(RO.ROSTER) and not set(configs) & set(left_out)
    assert set(left_out) == set(d["not_piloted_registered"])
    assert all(k in d["per_model_band_mas"] for k in configs)
    assert len(configs) == d["plugin_over_n_of_roster"][0]
    bad = dict(d, per_model_band_mas={k: v for k, v in d["per_model_band_mas"].items() if k != configs[0]})
    with pytest.raises(SystemExit):
        grid_configs(bad)


def test_grid_manifest_matches_runs():
    """Every planned cell has a run with the right hashes and configuration. While the manifests do not exist the test
    skips; once they do, every run ON DISK must match its manifest (prompt hash, environment code hash, harness and
    placebo versions, configuration tag, model, scenario, seed and start design), and runs still missing are counted,
    never silently passed."""
    from tools.phase9.e9_4_grid import MANIFESTS, OUT, stage_verify
    if not any(os.path.exists(os.path.join(OUT, f)) for f in MANIFESTS.values()):
        pytest.skip("stage 1's manifests are not written yet: python -m tools.phase9.e9_4_grid --stages manifest")
    assert stage_verify() == 0, "a run on disk does not match the manifest it was planned in"
    v = json.load(open(os.path.join(OUT, "verify.json"), encoding="utf-8"))
    assert v["rows"], "verify wrote no rows"


def test_grid_score_rows_scores_a_completed_run(tmp_path, monkeypatch):
    """`score`: a completed, checkpointed grid run is scored exactly as the pilots were, a planned run with no
    checkpoint contributes nothing, and a scoring failure is recorded in `score_error` rather than dropped. Proved on
    a real 12-day run driven by the fake LLM (no call is made)."""
    from dataclasses import replace
    from simulation.runner_v2 import run_simulation_v2
    from tools.phase8.e8_0_golden import fake_llm
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    from tools.phase9.e9_4_grid import score_rows
    monkeypatch.setattr(R, "RESULTS", str(tmp_path / "results"))
    mc = RO.by_key("gpt-5-mini|default")
    cells = [{"persona": "ISFJ", "arm": "static", "scenario": "flat", "seed": 3, "rep": 0, "setting": "default"},
             {"persona": "ISFJ", "arm": "memory", "scenario": "flat", "seed": 3, "rep": 0, "setting": "default"}]
    m = {"name": "t_grid", "subdir": "t_stage1", "configs": [mc.key], "cells": cells}
    cfg = R.cfg_for(mc, cells[0], m["subdir"], RO.provider_options_record(mc, None), 12)
    df = run_simulation_v2(replace(cfg, agent_llm=fake_llm([])), verbose=False)
    assert df is not None and len(df) == 12
    key = R.run_key(cells[0], R.cfg_for(mc, cells[0], m["subdir"], None, 12))
    os.makedirs(os.path.dirname(R.checkpoint_path(m["subdir"], mc)), exist_ok=True)
    with open(R.checkpoint_path(m["subdir"], mc), "a", encoding="utf-8") as fh:
        fh.write(key + "\n")
    p = R.run_paths(R.cfg_for(mc, cells[0], m["subdir"], None, 12))
    json.dump({"status": "ok"}, open(p["usage"], "w", encoding="utf-8"))
    rows = score_rows(m)
    assert len(rows) == 1 and rows[0]["Arm"] == "static" and rows[0]["score_error"] == ""
    assert np.isfinite(rows[0]["band_mas"]), rows[0]
    with open(p["csv"], "w", encoding="utf-8") as fh:
        fh.write("not,a,run\n")
    rows = score_rows(m)
    assert len(rows) == 1 and rows[0]["score_error"] != ""
