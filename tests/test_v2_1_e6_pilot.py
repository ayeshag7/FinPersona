"""v2.1 Phase 9, stage 2 -- E6's stateful sizing pilot (PREREG_PHASE_9_STAGE2_E6_PILOT.md).

What is locked here:

* the fingerprint now hashes a stateful cell's prompt (it used to skip it, so a manifest of stateful arms would have
  carried no prompt hash and verify would have checked nothing about its prompts), built as the runner builds the
  agent; and no prompt hash any manifest on disk stores has moved;
* the manifest: the factor's eight arms on the headline's twelve cells at the shape rule's seeds, on the roster the
  selection's rule gives once the three unread windows are read; its fingerprint verifies; the verify stage plans it;
* the arm filter that gives each (model, level) its own array task partitions the manifest exactly;
* the shape rule reproduces E9.2's known answer when given E9.2's counts;
* the analysis recovers planted per-level noise, the level contrasts, the busy-time union, the gates and the
  runaway count, and runs end to end on a synthetic pilot.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
E94 = os.path.join(GEN, "e9_4")
PILOT = os.path.join(E94, "manifest_context_pilot.json")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
E6_FOUR = ("vllm/google/gemma-4-e4b-it|default", "vllm/allenai/olmo-3.1-32b-instruct|default",
           "vllm/mistralai/ministral-3-14b-instruct-2512|default", "vllm/meta-llama/llama-3.1-8b-instruct|default")


def _manifest():
    if not os.path.exists(PILOT):
        pytest.skip("manifest_context_pilot.json is not written yet")
    from tools.phase9 import e9_runner as R
    return R.load_manifest(PILOT)


# ================================================================================================ the fingerprint
def test_fingerprint_hashes_stateful_cells_as_the_runner_builds_them():
    """A stateful cell's stored hash is the hash the run's meta.json will record: the agent is constructed exactly as
    simulation/runner_v2.run_simulation_v2 constructs it.  And it is not the stateless static arm's hash -- the
    stateful arms carry the mandate in the system prompt (Path B), which is what the decay thesis is about."""
    from langchain_core.runnables import RunnableLambda
    from agent.stateful_agent import StatefulV2Agent
    from agent.v2_agent import V2Agent
    from experiments.arms_v2 import CONTEXT_LEVELS
    from simulation.provenance import agent_provenance
    from tools.phase9 import e9_runner as R
    from tools.phase9 import e9_roster as RO
    key = E6_FOUR[0]
    arms = [a for pair in CONTEXT_LEVELS.values() for a in pair]
    cells = [{"persona": p, "arm": a, "scenario": "flat", "seed": 5001, "rep": 0} for p in PERSONAS for a in arms]
    cells.append({"persona": "ISFJ", "arm": "static", "scenario": "flat", "seed": 5001, "rep": 0})
    fp = R.fingerprint({"configs": [key], "cells": cells, "subdir": "pilot_context"})
    assert len(fp["prompt_hash"]) == len(PERSONAS) * len(arms) + 1
    mc = RO.by_key(key)
    for p in PERSONAS:
        for a in arms:
            cfg = R.cfg_for(mc, {"persona": p, "arm": a, "scenario": "flat", "seed": 1}, "pilot_context")
            assert cfg.context_mode != "stateless" and cfg.mandate_in_system and cfg.harness_version == "v2_1"
            kw = dict(persona=cfg.persona, model_name=cfg.model_name, mandate_block=cfg.mandate_block,
                      mandate_persona=cfg.mandate_persona, wording=cfg.wording, track=cfg.track,
                      action_interface=cfg.action_interface, n_assets=cfg.n_assets, disclose_horizon=cfg.disclose_horizon,
                      T=cfg.T, cost_visible=cfg.cost_visible, cost_bp=cfg.cost_bp, objective=cfg.objective,
                      mandate_in_system=cfg.mandate_in_system, temperature=cfg.temperature,
                      liquidity_condition=cfg.liquidity_condition, llm=RunnableLambda(lambda m: None),
                      placebo_version=cfg.placebo_version)
            ag = StatefulV2Agent(context_mode=cfg.context_mode, window=cfg.context_window,
                                 token_budget=cfg.context_token_budget, harness=cfg.harness_version, **kw)
            assert fp["prompt_hash"][f"{key}|{p}|{a}"] == agent_provenance(ag)["Prompt_Hash"]
            kw["mandate_in_system"] = False
            assert fp["prompt_hash"][f"{key}|{p}|{a}"] != agent_provenance(V2Agent(**kw))["Prompt_Hash"]
    # the stateless static arm's hash is unchanged by the stateful branch: it is the stage-1 value
    head = R.load_manifest(os.path.join(E94, "manifest_headline_open.json"))
    assert fp["prompt_hash"][f"{key}|ISFJ|static"] == head["fingerprint"]["prompt_hash"][f"{key}|ISFJ|static"]


# ================================================================================================ the manifest stage
def test_context_pilot_cells_are_the_factor_on_the_headline_cells():
    from experiments.arms_v2 import CONTEXT_LEVELS
    from tools.phase9.e9_4_grid import (ALL_MANIFESTS, CONTEXT_PILOT_MANIFEST, CONTEXT_PILOT_SEED0, cells_for)
    assert ALL_MANIFESTS["context_pilot"] == CONTEXT_PILOT_MANIFEST == "manifest_context_pilot.json"
    seeds = list(range(CONTEXT_PILOT_SEED0, CONTEXT_PILOT_SEED0 + 8))
    cells = cells_for("context_pilot", seeds)
    arms = {a for pair in CONTEXT_LEVELS.values() for a in pair}
    assert len(cells) == 8 * 12 * 8 == 768
    assert {c["arm"] for c in cells} == arms and len(arms) == 8
    assert not any("summary" in c["arm"] for c in cells)
    assert {c["persona"] for c in cells} == set(PERSONAS) and {c["scenario"] for c in cells} == set(SCENARIOS)
    assert all(c["setting"] == "default" and c["rep"] == 0 and "factors" not in c for c in cells)
    assert len({(c["persona"], c["arm"], c["scenario"], c["seed"]) for c in cells}) == len(cells)
    # seeds disjoint from E8.5's, E9.2's and the grid's
    s = {c["seed"] for c in cells}
    assert s == set(seeds) and min(s) == 5001
    assert not (s & set(range(2001, 2009))) and not (s & set(range(3001, 3017))) and not (s & set(range(10001, 10123)))
    # the other kinds are untouched
    assert len(cells_for("slice", list(range(10001, 10061)))) == 2400
    assert len(cells_for("ocean", list(range(10001, 10061)))) == 1440


def test_pilot_manifest_on_disk_is_its_shape_its_windows_and_its_roster():
    from tools.phase9 import e9_runner as R
    from tools.phase9 import e9_4_context_pilot as CP
    m = _manifest()
    shape = json.load(open(os.path.join(CP.OUT, "shape.json"), encoding="utf-8"))
    w = CP.load_windows()
    assert m["name"] == "e9_4_context_pilot" and m["kind"] == "pilot" and m["subdir"] == "pilot_context"
    assert m["ledger_dir"] == "e9_4" and m["T"] == 200
    assert tuple(m["configs"]) == tuple(w["e6_roster"]) == E6_FOUR
    assert m["seeds_per_cell"] == shape["chosen_seeds_per_cell"] == 8 and len(m["cells"]) == 768
    assert m["seeds"] == list(range(5001, 5009))
    assert len(m["fingerprint"]["prompt_hash"]) == 4 * 3 * 8 == 96
    assert m["fingerprint"]["Env_Code_Hash"] == "1d689aaf82a33a2e"
    cur = R.fingerprint(m)
    assert cur["prompt_hash"] == m["fingerprint"]["prompt_hash"] and cur["Env_Code_Hash"] == m["fingerprint"]["Env_Code_Hash"]
    # The registered sources are b5baebb's.  E8's cadence factor (P9-38) moved three of the eight hashed sources after
    # this manifest was registered, so a tree carrying E8 REFUSES to run it (`verify_fingerprint`), which is why the
    # pilot runs from a clone pinned at its own commit (STAGE2_OPERATIONS.md 13).  Nothing of its prompts or its
    # environment moved, and nothing else may have.
    moved = {k for k, v in m["fingerprint"]["sources_sha256_lf"].items() if cur["sources_sha256_lf"][k] != v}
    assert moved <= {"agent/v2_agent.py", "simulation/runner_v2.py", "experiments/arms_v2.py"}, moved


def test_pilot_verify_stage_plans_it(tmp_path):
    from tools.phase9.e9_4_grid import stage_verify
    _manifest()
    report = tmp_path / "verify_context_pilot.json"
    stage_verify(only=("context_pilot",), out_path=str(report))
    v = json.load(open(report, encoding="utf-8"))
    assert v["rows"] and all(r["manifest"] == "context_pilot" and r["planned"] == 768 for r in v["rows"])
    assert all(r["verified"] + r["missing"] == 768 and r["mismatched"] == 0 for r in v["rows"])
    assert len(v["rows"]) == 4


# ================================================================================================ the arm filter
def test_arm_filter_partitions_the_manifest_by_level():
    from experiments.arms_v2 import CONTEXT_LEVELS
    from tools.phase9 import e9_runner as R
    from tools.phase9 import e9_roster as RO
    m = _manifest()
    mc = RO.by_key(m["configs"][0])
    keys = [R.run_key(c, R.cfg_for(mc, c, m["subdir"])) for c in m["cells"]]
    assert len(set(keys)) == len(keys)
    seen = []
    for lvl, pair in CONTEXT_LEVELS.items():
        want = R.parse_arms(",".join(pair), m["cells"])
        assert want == frozenset(pair)
        part = [k for k, c in zip(keys, m["cells"]) if c["arm"] in want]
        assert len(part) == 192, lvl
        seen += part
    assert sorted(seen) == sorted(keys)                 # disjoint and complete
    assert R.parse_arms("", m["cells"]) == frozenset()
    with pytest.raises(SystemExit):
        R.parse_arms("stateful_summary_static", m["cells"])
    # a level task combined with a shard is still disjoint from its sibling shard
    part = [k for k, c in zip(keys, m["cells"]) if c["arm"] in CONTEXT_LEVELS["full"]]
    halves = [sorted(k for k in part if R.shard_of(k, 2) == i) for i in (0, 1)]
    assert not (set(halves[0]) & set(halves[1])) and sorted(halves[0] + halves[1]) == sorted(part)


# ================================================================================================ the shape rule
def test_shape_rule_is_e9_2s_and_reproduces_its_known_answer():
    """E9.2's shape.json chose 16 seeds per cell from pilot runs 24 S_p against G_ref 4,809.5; the same arithmetic in
    this module's f2 reproduces that choice, and E6's own counts give 8."""
    from tools.phase9 import e9_4_context_pilot as CP
    from tools.phase9.e9_2_pilot import f2 as f2_e92
    e92 = json.load(open(os.path.join(GEN, "e9_2", "shape.json"), encoding="utf-8"))
    rows = {sp: 24 * sp + CP.f2(12 * sp - 12) * e92["G_ref"] for sp in CP.SP_CANDIDATES}
    assert min(rows, key=lambda s: (rows[s], s)) == e92["chosen_seeds_per_cell"] == 16
    assert all(abs(CP.f2(df) - f2_e92(df)) < 1e-12 for df in (36, 84, 132))
    assert abs(CP.f2(CP.E85_DF_D) - e92["e8_5_shape"]["f2_at_df_d"]) < 1e-9
    t = CP.shape_table()
    best = t.sort_values(["expected_total_runs_per_model", "seeds_per_cell"]).iloc[0]
    assert int(best["seeds_per_cell"]) == 8 and int(best["runs"]) == 768 and int(best["df_d_per_level"]) == 84
    assert CP.e6_runs_per_model(60) == 5760 and (t["runs"] == 96 * t["seeds_per_cell"]).all()


# ================================================================================================ the windows
def test_windows_resolve_the_conditional_models_and_give_the_plans_four():
    from tools.phase9 import e9_4_context_pilot as CP
    from tools.phase9 import e9_roster as RO
    w = CP.load_windows()
    rc = pd.DataFrame(w["r_context"]).set_index("Model")
    for k in ("vllm/google/gemma-4-e4b-it|default", "vllm/allenai/olmo-3.1-32b-instruct|default",
              "vllm/mistralai/ministral-3-14b-instruct-2512|default"):
        assert rc.loc[k, "R_context_selection"] == "conditional" and rc.loc[k, "R_context"] == "met", k
    assert rc.loc["vllm/microsoft/phi-4|default", "R_context"] == "not met"
    assert rc.loc["vllm/openai/gpt-oss-20b|default", "R_context"] == "conditional"      # not read: fails R_effect
    assert tuple(w["e6_roster"]) == E6_FOUR and w["e6_roster_n"] == w["plan_e6_models"] == 4
    assert all(k in RO.CORE_OPEN for k in w["e6_roster"])
    assert "vllm/google/gemma-4-31b-it|default" not in w["e6_roster"]                   # met, but not a core member
    # the served length is the smallest roster window, OLMo's, and every roster window holds the full level
    assert w["served_max_len"] == 65536 == w["windows"]["vllm/allenai/olmo-3.1-32b-instruct|default"]["native_window"]
    for k in E6_FOUR:
        assert w["windows"][k]["native_window"] >= 65536
        assert rc.loc[k, "full_need_tokens"] <= w["windows"][k]["native_window"]
        assert bool(rc.loc[k, "fits_window_doc_3_7"])         # under the document's larger rho too
    ctx = pd.read_csv(os.path.join(CP.OUT, "workers.csv"), dtype={"level": str})
    four = ctx[ctx["Model"].isin(E6_FOUR)]
    assert len(four) == 16 and four["fits_served"].all()
    assert (four["workers_typical"] >= 1).all() and (four["workers_typical"] <= CP.OPERATING_POINT).all()
    assert (four["workers_p99"] <= four["workers_typical"]).all()
    full = four[four["level"] == "full"].set_index("Model")
    assert full.loc["vllm/allenai/olmo-3.1-32b-instruct|default", "workers_typical"] < 10      # the KV-bound model


# ================================================================================================ synthetic analysis
def synth_pilot(models, n_seeds=8, seed0=5001, sigma_by_level=None, effect_by_level=None, rng_seed=0,
                fallback=0.0, zero_trade=0.0):
    """A per_run_context_pilot.csv-shaped table: per model, level, cell and seed, a static run and a memory run on a
    shared path, with a planted memory - static effect and a planted paired noise per level."""
    from experiments.arms_v2 import CONTEXT_LEVELS
    from tools.phase8.e8_5_analyse import metric_names
    rng = np.random.default_rng(rng_seed)
    sigma_by_level = sigma_by_level or {5: 0.02, 20: 0.03, 50: 0.04, "full": 0.06}
    effect_by_level = effect_by_level or {5: 0.01, 20: 0.02, 50: 0.03, "full": 0.05}
    rows = []
    for model in models:
        for p in PERSONAS:
            for sc in SCENARIOS:
                cell = rng.normal(0.3, 0.05)
                for s in range(seed0, seed0 + n_seeds):
                    path = rng.normal(0, 0.03)
                    for lvl, (sa, ma) in CONTEXT_LEVELS.items():
                        static = cell + path + rng.normal(0, 0.01)
                        d = effect_by_level[lvl] + rng.normal(0, sigma_by_level[lvl])
                        for arm, y in ((sa, static), (ma, static + d)):
                            r = {"Manifest": "e9_4_context_pilot", "Setting": "default", "Model": model, "Persona": p,
                                 "Arm": arm, "Scenario": sc, "Seed": s, "Decode_Replicate": 0, "score_error": ""}
                            for mt in metric_names():
                                r[mt] = y if mt == "band_mas" else y * 0.1
                            r.update({"mdd_pct": 1.0, "return_pct": 0.0, "fallback_share": fallback,
                                      "trade_count": 0 if rng.random() < zero_trade else 5})
                            rows.append(r)
    return pd.DataFrame(rows)


def test_sigma_and_contrasts_recover_planted_noise_per_level():
    from tools.phase9 import e9_4_context_pilot as CP
    sig_plant = {5: 0.02, 20: 0.03, 50: 0.04, "full": 0.06}
    t = CP.frame(synth_pilot(["m"], n_seeds=60, sigma_by_level=sig_plant))
    assert set(t["Level"]) == {"5", "20", "50", "full"} and set(t["Arm"]) == {"static", "memory"}
    sig = CP.sigma_table(t, ["band_mas"])
    assert len(sig) == 4 and (sig["n_pairs"] == 720).all() and (sig["df_d"] == 708).all()
    for lvl, s in sig_plant.items():
        r = sig[sig["Level"] == str(lvl)].iloc[0]
        assert abs(r["sigma"] - s) < 0.15 * s, (lvl, r["sigma"])
        assert r["sigma_limit90"] > r["sigma"]
        assert abs(r["mean"] - {5: 0.01, 20: 0.02, 50: 0.03, "full": 0.05}[lvl]) < 0.006
    con = CP.contrast_table(t, "band_mas")
    assert len(con) == 9 and set(con["quantity"]) == {"effect(L) - effect(5)", "static(L) - static(5)", "memory(L) - memory(5)"}
    r = con[(con["quantity"] == "effect(L) - effect(5)") & (con["Level"] == "full")].iloc[0]
    assert abs(r["sigma"] - np.hypot(0.06, 0.02)) < 0.15 * np.hypot(0.06, 0.02)      # the two levels' noises add
    assert abs(r["mean"] - 0.04) < 0.008
    r = con[(con["quantity"] == "static(L) - static(5)") & (con["Level"] == "full")].iloc[0]
    assert abs(r["sigma"] - np.hypot(0.01, 0.01)) < 0.005 and abs(r["mean"]) < 0.004   # the path cancels in the pair


def test_sizing_is_appendix_a_on_the_maximum_limit():
    from tools.phase8.e8_5_analyse import mdd, n_seeds
    from tools.phase9 import e9_4_context_pilot as CP
    t = CP.frame(synth_pilot(["a", "b"], n_seeds=8, sigma_by_level={5: 0.02, 20: 0.03, 50: 0.04, "full": 0.06}))
    sig = CP.sigma_table(t, ["band_mas"])
    con = CP.contrast_table(t, "band_mas")
    sz = CP.sizing(sig, con, ["a", "b"])
    assert sz["alpha"] == 0.05 / 36 and sz["delta"] == 0.05 and len(sz["rows"]) == 4 + 3 + 3
    full = next(r for r in sz["rows"] if r["quantity"] == "memory - static" and r["Level"] == "full")
    plug = max(sig[(sig["Level"] == "full")]["sigma_limit90"])
    assert full["plugin"] == plug and full["seeds_appA"] == n_seeds(plug, 0.05, 0.05 / 36)
    assert full["seeds_paired_correct"] == n_seeds(plug, 0.05, 0.05 / 36, factor2=False) < full["seeds_appA"]
    assert full["n_models"] == 2 and set(full["per_model"]) == {"a", "b"}
    assert abs(full["mdd_at_plugin"]["60"] - mdd(plug, 60, 0.05 / 36)) < 1e-12
    assert full["estimable_at_5_seeds_at_plugin"] == (mdd(plug, 5, 0.05 / 36) <= 0.05)
    # a roster model with no rows is named, never silently dropped
    sz2 = CP.sizing(sig, con, ["a", "b", "c"])
    assert next(r for r in sz2["rows"] if r["Level"] == "5")["models_missing"] == ["c"]


def test_cost_table_takes_the_busy_union_per_level():
    from tools.phase9 import e9_4_context_pilot as CP
    keys = {"k1": ("m", "5", "static"), "k2": ("m", "5", "memory"), "k3": ("m", "full", "static")}
    t0 = "2026-11-10T00:00:00Z"
    # two level-5 runs overlapping by 50 s: busy = 150 s, not 200; a failed attempt inside the first run's interval
    # adds to the attempts and not to the busy time or the run count; the full-level run is its own task
    led = [{"run_key": "k1", "utc": "2026-11-10T00:01:40Z", "seconds": 100.0, "status": "ok", "input_tokens": 10, "output_tokens": 1},
           {"run_key": "k2", "utc": "2026-11-10T00:02:30Z", "seconds": 100.0, "status": "ok", "input_tokens": 20, "output_tokens": 2},
           {"run_key": "k2", "utc": "2026-11-10T00:00:30Z", "seconds": 30.0, "status": "failed"},
           {"run_key": "k3", "utc": "2026-11-10T01:00:00Z", "seconds": 600.0, "status": "ok", "input_tokens": 50, "output_tokens": 5},
           {"run_key": "zz", "utc": t0, "seconds": 999.0, "status": "ok"}]
    c = CP.cost_table(led, keys, None, 8).set_index("Level")
    assert set(c.index) == {"5", "full"}
    assert abs(c.loc["5", "busy_hours"] * 3600 - 150.0) < 1e-6 and c.loc["5", "n_runs_ok"] == 2 and c.loc["5", "n_attempts"] == 3
    assert abs(c.loc["5", "gpu_hours_per_run"] - 150.0 / 3600 / 2) < 1e-9 and c.loc["5", "n_planned"] == 2
    assert abs(c.loc["full", "gpu_hours_per_run"] - 600.0 / 3600) < 1e-9
    assert abs(c.loc["full", "e6_gpu_hours_S60"] - 24 * 60 * 600.0 / 3600) < 1e-6
    assert abs(c.loc["5", "input_tokens_per_run"] - 15.0) < 1e-9


def test_gates_and_runaway_from_synthetic_frames():
    from tools.phase9 import e9_4_context_pilot as CP
    t = CP.frame(synth_pilot(["m"], n_seeds=2, fallback=0.02, zero_trade=0.9))
    ctx = pd.DataFrame([{"Model": "m", "Level": lvl, "context_tokens_max": 60000.0 if lvl == "full" else 10000.0,
                         "context_tokens_last": 1.0, "n_calls_runaway": 1 if (lvl == "50" and i == 0) else 0,
                         "max_output_per_call": 9000 if (lvl == "50" and i == 0) else 100, "mandate_copies_max": 2,
                         "token_count_methods": "provider", "history_fallback_turns": 1.0}
                        for lvl in ("5", "20", "50", "full") for i in range(4)])
    g = CP.gates_table(t, ctx).set_index("Level")
    assert not g["G2_fallback"].any() and not g["G3_degenerate"].any()         # both gates fail as planted
    assert abs(g.loc["50", "runaway_run_share"] - 0.25) < 1e-9 and g.loc["5", "runaway_run_share"] == 0
    assert g.loc["full", "context_headroom_at_served"] == 65536 - 60000 and g["copies_at_most_2"].all()
    assert (g["token_count_methods"] == "provider").all() and g.loc["5", "history_fallback_turns_total"] == 4.0
    clean = CP.gates_table(CP.frame(synth_pilot(["m"], n_seeds=2)), None).set_index("Level")
    assert clean["G2_fallback"].all() and clean["G3_degenerate"].all() and "runaway_run_share" not in clean


def test_summarise_run_reads_the_per_step_columns(tmp_path):
    from tools.phase9 import e9_4_context_pilot as CP
    df = pd.DataFrame({"Context_Tokens": [1900, 2800, 3700], "Context_Turns": [0, 1, 2], "Mandate_Copies_In_Context": [1, 2, 2],
                       "Mandate_Offset_Tokens": [400, 436, 436], "Token_Count_Method": ["provider"] * 3,
                       "History_Fallback_Turns": [0, 0, 1], "Parse_Status": ["ok", "ok_retry1", "fallback"]})
    csv = tmp_path / "r.csv"; df.to_csv(csv, index=False)
    usage = tmp_path / "r.usage.json"
    json.dump({"seconds": 12.5, "status": "ok", "calls": [{"in": 1900, "out": 90}, {"in": 2800, "out": 8192}, {"in": 3700, "out": 50}]},
              open(usage, "w"))
    s = CP.summarise_run(str(csv), str(usage))
    assert s["n_days"] == 3 and s["context_tokens_max"] == 3700 and s["context_tokens_day1"] == 1900
    assert s["mandate_copies_max"] == 2 and s["history_fallback_turns"] == 1 and s["n_fallback"] == 1 and s["n_retry"] == 1
    assert s["n_calls"] == 3 and s["max_output_per_call"] == 8192 and s["n_calls_runaway"] == 1
    assert s["input_tokens"] == 8400 and s["token_count_methods"] == "provider" and s["seconds"] == 12.5


def test_prediction_p1_reads_the_projection_within_a_factor_two():
    from tools.phase9 import e9_4_context_pilot as CP
    cost = pd.DataFrame([{"Model": "m", "Level": "5", "gpu_hours_per_run": 0.010, "n_runs_ok": 3},
                         {"Model": "m", "Level": "full", "gpu_hours_per_run": 0.150, "n_runs_ok": 3}])
    pj = pd.DataFrame([{"Model": "m", "level": "5", "projected_gpu_hours_per_run": 0.008},
                       {"Model": "m", "level": "full", "projected_gpu_hours_per_run": 0.100}])
    p = CP.prediction_p1(cost, pj)
    assert p["verdict"] == "holds" and abs(p["worst_factor"] - 1.5) < 1e-9 and p["n_cells"] == 2
    cost.loc[1, "gpu_hours_per_run"] = 0.25
    assert CP.prediction_p1(cost, pj)["verdict"] == "fails"
    assert CP.prediction_p1(cost, None)["verdict"] == "unevaluated"


def test_prediction_p2_reads_the_stateful_noise_against_the_stateless():
    from tools.phase9 import e9_4_context_pilot as CP
    ns = pd.read_csv(os.path.join(CP.SEL, "noise_seeds.csv")).set_index("Model")
    k = E6_FOUR[1]
    ref = float(ns.loc[k, "sigma_rms_bm"])
    sig = pd.DataFrame([{"Model": k, "Level": "5", "metric": "band_mas", "sigma": 1.5 * ref, "n_pairs": 96},
                        {"Model": k, "Level": "full", "metric": "band_mas", "sigma": 9 * ref, "n_pairs": 96}])
    p = CP.prediction_p2(sig, [k])
    assert p["verdict"] == "holds" and abs(p["worst_factor"] - 1.5) < 1e-9 and p["n_models"] == 1
    assert p["rows"][0]["n_pairs_stateless"] == 12 * 122
    sig.loc[0, "sigma"] = 3 * ref
    assert CP.prediction_p2(sig, [k])["verdict"] == "fails"
    assert CP.prediction_p2(sig, ["vllm/none|default"])["verdict"] == "unevaluated"


def test_projection_table_is_phase_8_tokens_over_stage_1_rates():
    from tools.phase9 import e9_4_context_pilot as CP
    t = CP.projection_table(list(E6_FOUR), 8)
    assert len(t) == 16 and set(t["level"]) == {"5", "20", "50", "full"}
    cc = json.load(open(os.path.join(GEN, "e8_2", "context_cost.json"), encoding="utf-8"))
    v21 = {r["level"]: r["input_tokens_per_run"] for r in cc["table"] if r["harness"] == "v2_1"}
    r = t[(t["Model"] == E6_FOUR[1]) & (t["level"] == "full")].iloc[0]
    assert r["input_tokens_per_run_v2_1"] == v21["full (60k)"] and abs(r["x_stateless"] - v21["full (60k)"] / v21["stateless"]) < 1e-9
    assert abs(r["projected_gpu_seconds_per_run"] - v21["full (60k)"] / r["stage1_input_tokens_per_gpu_second"]) < 1e-9
    assert r["pilot_runs"] == 192 and r["e6_runs_S60"] == 1440
    assert (t["projected_gpu_hours_per_run"] > t["stage1_gpu_hours_per_run"]).all()      # every level costs more than stateless


def test_analyse_end_to_end_on_a_synthetic_pilot(monkeypatch):
    """`stage_analyse` on one model of the real manifest at two of its seeds: a scored frame, a ledger and a per-run
    context summary written where the stage reads them, every run checkpointed and on disk, so `complete` is True
    and every table has its rows.  The tree lives under a SHORT temporary root: a run file's path under pytest's own
    tmp_path exceeds Windows' 260 characters."""
    import pathlib
    import shutil
    import tempfile
    from tools.phase9 import e9_4_context_pilot as CP
    from tools.phase9 import e9_runner as R
    from tools.phase9 import e9_roster as RO
    m = _manifest()
    key = m["configs"][1]
    small = {**m, "configs": [key], "cells": [c for c in m["cells"] if c["seed"] in (5001, 5002)], "seeds": [5001, 5002],
             "seeds_per_cell": 2}
    root = pathlib.Path(tempfile.mkdtemp(prefix="fp_e6_"))
    try:
        _analyse_end_to_end(root, small, key, monkeypatch, CP, R, RO)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _analyse_end_to_end(tmp_path, small, key, monkeypatch, CP, R, RO):
    e94 = tmp_path / "e9_4"; out = e94 / "context_pilot"; gen = tmp_path / "gen"; results = tmp_path / "results"
    out.mkdir(parents=True); (gen / "e9_4").mkdir(parents=True)
    json.dump(small, open(e94 / "manifest_context_pilot.json", "w"))
    monkeypatch.setattr(CP, "E94", str(e94)); monkeypatch.setattr(CP, "OUT", str(out))
    monkeypatch.setattr(R, "GEN", str(gen)); monkeypatch.setattr(R, "RESULTS", str(results))
    mc = RO.by_key(key)
    per_run = synth_pilot([key], n_seeds=2)
    per_run.to_csv(e94 / "per_run_context_pilot.csv", index=False)
    keys = CP.pilot_keys(small)
    assert len(keys) == 192
    led, ctx, ck = [], [], []
    t = 1_700_000_000
    for c in small["cells"]:
        cfg = R.cfg_for(mc, c, small["subdir"])
        k = R.run_key(c, cfg)
        p = R.run_paths(cfg)
        os.makedirs(p["dir"], exist_ok=True)
        for f in ("csv", "meta", "usage"):
            open(p[f], "w").write("x")
        ck.append(k)
        t += 30
        led.append({"run_key": k, "utc": pd.Timestamp(t, unit="s").strftime("%Y-%m-%dT%H:%M:%SZ"), "seconds": 60.0,
                    "status": "ok", "input_tokens": 1000, "output_tokens": 10})
        lvl, kind = keys[k][1], keys[k][2]
        ctx.append({"Model": key, "Persona": c["persona"], "Arm": c["arm"], "Level": lvl, "Arm_Kind": kind,
                    "Scenario": c["scenario"], "Seed": c["seed"], "run_key": k, "context_tokens_max": 50000.0,
                    "context_tokens_last": 50000.0, "n_calls_runaway": 0, "max_output_per_call": 120,
                    "mandate_copies_max": 2 if kind == "memory" else 1, "token_count_methods": "provider",
                    "history_fallback_turns": 0.0})
    os.makedirs(os.path.dirname(R.checkpoint_path(small["subdir"], mc)), exist_ok=True)
    open(R.checkpoint_path(small["subdir"], mc), "w").write("\n".join(ck) + "\n")
    with open(R.ledger_file("e9_4", mc), "w") as fh:
        for r in led:
            fh.write(json.dumps(r) + "\n")
    pd.DataFrame(ctx).to_csv(out / "per_run_context.csv", index=False)
    CP.projection_table([key], 2).to_csv(out / "projection.csv", index=False)
    s = CP.stage_analyse()
    assert s["complete"] and s["runs_done_vs_planned"] == {key: [192, 192]} and s["runs_scored"] == {key: 192}
    assert len(s["sizing"]["rows"]) == 10 and all(r["n_models"] == 1 for r in s["sizing"]["rows"])
    assert len(s["cost_per_level"]) == 4 and all(r["n_runs_ok"] == 48 for r in s["cost_per_level"])
    assert set(s["e6_gpu_hours_at"]) == {"5", "20", "30", "40", "60"} and s["e6_gpu_hours_at"]["60"] > 0
    assert len(s["gates"]) == 4 and all(r["G2_fallback"] and r["copies_at_most_2"] for r in s["gates"])
    assert [p["id"] for p in s["predictions"]] == ["P1", "P2"]
    assert s["predictions"][0]["verdict"] in ("holds", "fails") and s["predictions"][1]["verdict"] in ("holds", "fails")
    for f in ("sigma.csv", "contrasts.csv", "cost.csv", "gates.csv", "sizing.json", "summary.json"):
        assert (out / f).exists()
    sig = pd.read_csv(out / "sigma.csv", dtype={"Level": str})
    assert len(sig[sig["metric"] == "band_mas"]) == 4 and (sig["n_pairs"] == 24).all()
