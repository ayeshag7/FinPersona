"""v2.1 Phase 9, stage 2, E8 -- the re-injection cadence (PREREG_PHASE_9_STAGE2_E8.md).

What is locked here:

* the cadence: on an injected day the prompt is the memory arm's and on every other day the static arm's, byte for
  byte; the count is exactly T / k at every phase; the phase is seed mod k; every = 1 is byte-identical to before,
  and a run without the factor logs no new column and no new key; a stateful arm refuses it;
* the fingerprint: a cadence arm's prompt hash is the memory arm's, and the manifest on disk stores them so;
* the manifest stage, the verify stage's two cadence checks, and the shared-dict trap stated as a test;
* the analysis: the frame excludes other settings' rows, the retention recovers a planted dose-response, the
  predictions read it and fail where they should, the per-step summary is built from run CSVs, and main runs end to
  end on a synthetic grid.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import tempfile

import numpy as np
import pandas as pd
import pytest
from langchain_core.runnables import RunnableLambda

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
E94 = os.path.join(GEN, "e9_4")
MANIFEST = os.path.join(E94, "manifest_cadence_open.json")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
K = (2, 5, 10, 20)


def fake_llm(seen=None, target=0.5):
    def _run(messages):
        if seen is not None:
            seen.append(messages.to_string() if hasattr(messages, "to_string") else str(messages))
        return json.dumps({"target_cash_share": target, "rationale": "t"})
    return RunnableLambda(_run)


def _manifest():
    if not os.path.exists(MANIFEST):
        pytest.skip("manifest_cadence_open.json is not written yet")
    from tools.phase9 import e9_runner as R
    return R.load_manifest(MANIFEST)


# ================================================================================================ the cadence
def test_cadence_renders_the_memory_prompt_on_injected_days_and_the_static_prompt_otherwise():
    from agent.v2_agent import V2Agent
    mem = V2Agent("ISFJ", "fake", mandate_block="mandate", llm=fake_llm())
    sta = V2Agent("ISFJ", "fake", mandate_block="none", llm=fake_llm())
    ps = {"cash_share": 0.5, "total_value": 10000.0, "cash": 5000.0, "holdings_value": 5000.0}
    for k in K:
        for phase in (0, k - 1, (k // 2)):
            ag = V2Agent("ISFJ", "fake", mandate_block="mandate", llm=fake_llm(), mandate_every=k, mandate_phase=phase)
            days = []
            for day in range(1, 201):
                ms = {"day": day, "date": f"Day-{day}", "price": 100.0}
                ag.decide(ms, ps)
                if ag.last_mandate_injected:
                    days.append(day)
                want = (mem if ag.last_mandate_injected else sta).rendered_human_message(ms, ps)
                assert ag.rendered_human_message(ms, ps) == want, (k, phase, day)
            assert days == [d for d in range(1, 201) if (d - 1 - phase) % k == 0], (k, phase)
            assert len(days) == 200 // k == ag.mandate_injections
            assert ag.prompt_components() == mem.prompt_components()      # one prompt family, hashed as the memory arm's
    # every = 1 is the published behaviour: the block on every day
    one = V2Agent("ISFJ", "fake", mandate_block="mandate", llm=fake_llm(), mandate_every=1)
    for day in (1, 2, 3):
        one.decide({"day": day, "date": f"Day-{day}", "price": 100.0}, ps)
        assert one.last_mandate_injected
    # a static arm injects nothing at any cadence; bad arguments are refused
    none = V2Agent("ISFJ", "fake", mandate_block="none", llm=fake_llm(), mandate_every=5)
    none.decide({"day": 1, "date": "Day-1", "price": 100.0}, ps)
    assert not none.last_mandate_injected and none.mandate_injections == 0
    with pytest.raises(ValueError):
        V2Agent("ISFJ", "fake", mandate_block="mandate", llm=fake_llm(), mandate_every=5, mandate_phase=5)
    with pytest.raises(ValueError):
        V2Agent("ISFJ", "fake", mandate_block="mandate", llm=fake_llm(), mandate_every=0)


def test_runner_logs_the_cadence_and_the_default_output_is_unchanged():
    from experiments.arms_v2 import ARMS, CADENCE_LEVELS, build_config
    from simulation.runner_v2 import run_simulation_v2
    assert CADENCE_LEVELS == {1: "memory", 2: "memory_k2", 5: "memory_k5", 10: "memory_k10", 20: "memory_k20"}
    assert all(ARMS[a] == {"mandate_block": "mandate", "mandate_every": k} for k, a in CADENCE_LEVELS.items() if k != 1)
    assert ARMS["memory"] == {"mandate_block": "mandate"} and "mandate_every" not in ARMS["static"]
    tmp = tempfile.mkdtemp(prefix="fp_e8_")          # short: a run path under pytest's tmp_path exceeds 260 characters
    try:
        for arm, seed, every, days in (("memory_k5", 7, 5, [3, 8, 13, 18]), ("memory_k5", 8, 5, [4, 9, 14, 19]),
                                       ("memory_k2", 7, 2, [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]), ("memory", 7, 1, None),
                                       ("static", 7, 1, None)):
            cfg = build_config("fake", "ISFJ", arm, "flat", seed, T=20, output_dir=tmp, agent_llm=fake_llm())
            assert cfg.mandate_every == every and cfg.context_mode == "stateless"
            df = run_simulation_v2(cfg, verbose=False)
            meta = json.load(open(os.path.join(tmp, "fake", "flat", f"seed{seed}", cfg.run_id() + ".meta.json"), encoding="utf-8"))
            assert meta["run_config"]["mandate_every"] == every
            if every != 1:
                assert "Mandate_Injected" in df.columns and list(df.loc[df["Mandate_Injected"], "Day"]) == days
                assert meta["n_mandate_injections"] == 20 // every and meta["mandate_phase"] == seed % every
            else:
                assert "Mandate_Injected" not in df.columns and "n_mandate_injections" not in meta and "mandate_phase" not in meta
        cfg = build_config("fake", "ISFJ", "stateful_memory", "flat", 7, T=20, output_dir=tmp, agent_llm=fake_llm(), mandate_every=5)
        with pytest.raises(ValueError):
            run_simulation_v2(cfg, verbose=False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ================================================================================================ the fingerprint
def test_cadence_prompt_hash_is_the_memory_arms_and_the_manifest_stores_it_so():
    from tools.phase9 import e9_runner as R
    m = _manifest()
    key = m["configs"][0]
    probe = {"configs": [key], "subdir": "stage2_cadence",
             "cells": [{"persona": "ISFJ", "arm": a, "scenario": "flat", "seed": 10001, "rep": 0, "setting": "cadence"}
                       for a in ("static", "memory", "memory_k5", "memory_k20")]}
    fp = R.fingerprint(probe)["prompt_hash"]
    assert fp[f"{key}|ISFJ|memory_k5"] == fp[f"{key}|ISFJ|memory_k20"] == fp[f"{key}|ISFJ|memory"] != fp[f"{key}|ISFJ|static"]
    heads = {}
    for f in ("manifest_headline_open.json", "manifest_headline_open_b2.json"):
        heads.update(R.load_manifest(os.path.join(E94, f))["fingerprint"]["prompt_hash"])
    n = 0
    for k, v in m["fingerprint"]["prompt_hash"].items():
        cfg_key, persona, arm = k.rsplit("|", 2)
        assert arm.startswith("memory_k")
        assert heads[f"{cfg_key}|{persona}|memory"] == v, k
        n += 1
    assert n == 72


# ================================================================================================ the manifest stage
def test_cadence_cells_and_manifest_on_disk():
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    from tools.phase9.e9_4_grid import ALL_MANIFESTS, CADENCE_MANIFEST, CADENCE_SETTING, STAGE2_MANIFESTS, cells_for
    assert ALL_MANIFESTS["cadence_open"] == STAGE2_MANIFESTS["cadence_open"] == CADENCE_MANIFEST == "manifest_cadence_open.json"
    seeds = list(range(10001, 10061))
    cells = cells_for("cadence", seeds)
    assert len(cells) == 4 * 12 * 60 == 2880
    assert {c["arm"] for c in cells} == {"memory_k2", "memory_k5", "memory_k10", "memory_k20"}
    assert all(c["setting"] == CADENCE_SETTING == "cadence" and "factors" not in c for c in cells)
    assert {c["persona"] for c in cells} == set(PERSONAS) and {c["scenario"] for c in cells} == set(SCENARIOS)
    assert len(cells_for("slice", seeds)) == 2400 and len(cells_for("ocean", seeds)) == 1440      # untouched
    m = _manifest()
    assert m["name"] == "e9_4_stage2_cadence" and m["kind"] == "grid" and m["subdir"] == "stage2_cadence" and m["T"] == 200
    assert tuple(m["configs"]) == RO.CAUSAL_OPEN and len(m["cells"]) == 2880 and m["seeds"] == seeds
    assert len(m["fingerprint"]["prompt_hash"]) == 6 * 3 * 4 == 72
    assert m["fingerprint"]["Env_Code_Hash"] == "1d689aaf82a33a2e"
    R.verify_fingerprint(m)


def test_cadence_moved_three_hashed_sources_and_no_registered_prompt():
    """The consequence E8's harness change has for the two manifests registered before it (E7's, the E6 pilot's): their
    stored source hashes for agent/v2_agent.py, simulation/runner_v2.py and experiments/arms_v2.py no longer match
    the tree, so `verify_fingerprint` refuses to RUN them here and they run from a clone at their own commit
    (STAGE2_OPERATIONS.md 13).  Nothing else moved: every prompt hash and the environment hash recompute, and no
    source outside the three.  The cadence manifest's own sources are the tree's."""
    from tools.phase9 import e9_runner as R
    three = {"agent/v2_agent.py", "simulation/runner_v2.py", "experiments/arms_v2.py"}
    for f in ("manifest_ocean_open.json", "manifest_context_pilot.json"):
        p = os.path.join(E94, f)
        if not os.path.exists(p):
            pytest.skip(f"{f} is not written")
        m = R.load_manifest(p)
        cur = R.fingerprint(m)
        assert cur["prompt_hash"] == m["fingerprint"]["prompt_hash"] and cur["Env_Code_Hash"] == m["fingerprint"]["Env_Code_Hash"], f
        moved = {k for k, v in m["fingerprint"]["sources_sha256_lf"].items() if cur["sources_sha256_lf"][k] != v}
        assert moved <= three, (f, moved)
        if moved:
            with pytest.raises(SystemExit, match="REFUSING TO RUN"):
                R.verify_fingerprint(m)
    m = _manifest()
    cur = R.fingerprint(m)
    assert {k for k, v in m["fingerprint"]["sources_sha256_lf"].items() if cur["sources_sha256_lf"][k] != v} == set()


def test_cadence_checks_catch_a_run_at_the_wrong_cadence():
    from tools.phase9.e9_4_grid import cadence_checks
    k5 = {"persona": "ISFJ", "arm": "memory_k5", "scenario": "flat", "seed": 10001}
    assert cadence_checks({"mandate_every": 5}, {"n_mandate_injections": 40}, k5, 200) == {"mandate_every": True, "mandate_injections": True}
    assert cadence_checks({"mandate_every": 5}, {"n_mandate_injections": 39}, k5, 200)["mandate_injections"] is False
    assert cadence_checks({"mandate_every": 5}, {}, k5, 200)["mandate_injections"] is False
    assert cadence_checks({"mandate_every": 1}, {"n_mandate_injections": 40}, k5, 200)["mandate_every"] is False
    assert cadence_checks({}, {}, k5, 200)["mandate_every"] is False                   # an older run cannot be a k-arm
    for arm in ("static", "memory", "swapped", "stateful_memory"):
        assert cadence_checks({}, {}, {**k5, "arm": arm}, 200) == {"mandate_every": True}
        assert cadence_checks({"mandate_every": 1}, {}, {**k5, "arm": arm}, 200) == {"mandate_every": True}


def test_cadence_verify_stage_plans_it(tmp_path):
    from tools.phase9.e9_4_grid import stage_verify
    _manifest()
    report = tmp_path / "verify_cadence_open.json"
    stage_verify(only=("cadence_open",), out_path=str(report))
    v = json.load(open(report, encoding="utf-8"))
    assert len(v["rows"]) == 6 and all(r["manifest"] == "cadence_open" and r["planned"] == 2880 for r in v["rows"])
    assert all(r["verified"] + r["missing"] == 2880 and r["mismatched"] == 0 for r in v["rows"])


# ================================================================================================ the statistics trap
def test_e8_family_is_absent_from_the_shared_dict():
    from tools.phase9.e9_5_e8_analyse import ARMS_ALL, E8_FAMILY
    from tools.stats_v2 import question_families
    qf = question_families()
    fires = sorted(f"{a} - {r}" for pairs in qf.values() for a, r in pairs if a in ARMS_ALL and r in ARMS_ALL)
    assert fires == ["memory - static"]
    registered = sorted(f"{a} - {r}" for a, r in E8_FAMILY["E8"])
    assert registered == ["memory_k10 - static", "memory_k2 - static", "memory_k20 - static", "memory_k5 - static"]
    assert not set(registered) & set(fires)


# ================================================================================================ synthetic frames
def synth_per_run(model="vllm/x/y|default", n_seeds=10, d1=None, r=None, rng_seed=0, decoys=True):
    """A per_run.csv-shaped grid for one model: the headline's static and memory rows (seeds 10001..), E8's four
    cadence rows on the same paths with a planted retention r(k) of the planted every-day effect d1 per persona, and,
    when `decoys`, E3's common-start static rows and E4's Track-A static rows on the same keys, which `frames` must
    leave out."""
    rng = np.random.default_rng(rng_seed)
    d1 = d1 or {"ISFJ": 0.04, "INTJ": 0.002, "ENTJ": -0.03}
    r = r or {2: 0.8, 5: 0.6, 10: 0.4, 20: 0.2}
    rows = []
    for p in PERSONAS:
        for sc in SCENARIOS:
            base = 0.15 + rng.normal(0, 0.02)
            for s in range(10001, 10001 + n_seeds):
                path = rng.normal(0, 0.02)
                static = max(base + path + rng.normal(0, 0.004), 0.0)
                arms = {"static": static, "memory": static + d1[p] + rng.normal(0, 0.004)}
                for k, rk in r.items():
                    arms[f"memory_k{k}"] = static + rk * d1[p] + rng.normal(0, 0.004)
                for arm, y in arms.items():
                    man = "e9_4_stage1_headline_open" if arm in ("static", "memory") else "e9_4_stage2_cadence"
                    rows.append({"Manifest": man, "Setting": "default" if arm in ("static", "memory") else "cadence",
                                 "Model": model, "Persona": p, "Arm": arm, "Scenario": sc, "Seed": s, "Decode_Replicate": 0,
                                 "score_error": "", "band_mas": y, "v21_mcr_D_0.05": y * 0.5 + rng.normal(0, 0.003),
                                 "v21_mcr_D_0.002": y * 0.4 + rng.normal(0, 0.003), "turnover": 0.3, "mdd_pct": -2.0,
                                 "return_pct": 1.0, "fallback_share": 0.0, "trade_count": 5})
                if decoys:
                    for man, setting in (("e9_4_stage2_slice", "common_start"), ("e9_4_stage2_track_a", "track_a")):
                        rows.append({"Manifest": man, "Setting": setting, "Model": model, "Persona": p, "Arm": "static",
                                     "Scenario": sc, "Seed": s, "Decode_Replicate": 0, "score_error": "", "band_mas": 9.0,
                                     "v21_mcr_D_0.05": 9.0, "v21_mcr_D_0.002": 9.0, "turnover": 0.3, "mdd_pct": -2.0,
                                     "return_pct": 1.0, "fallback_share": 0.0, "trade_count": 5})
    return pd.DataFrame(rows)


def test_frames_exclude_other_settings_and_pair_without_collision():
    from tools.phase9.e9_5_e8_analyse import frames, pairing_check
    df, why = frames(synth_per_run(n_seeds=4), "vllm/x/y|default")
    assert df is not None, why
    assert set(df["Arm"]) == {"static", "memory", "memory_k2", "memory_k5", "memory_k10", "memory_k20"}
    assert (df["band_mas"] < 5).all()                                      # no decoy row (planted at 9.0) survives
    pc = pairing_check(df)
    assert pc["keys_with_two_manifests"] == 0 and pc["keys_with_six_arms"] == pc["keys_total"] == 48
    assert frames(synth_per_run(n_seeds=4), "vllm/none|default")[0] is None


def test_retention_recovers_the_planted_dose_response():
    from tools.phase9.e9_5_e8_analyse import ADMIT, cell_effects, frames, pooled_retention
    r_plant = {2: 0.8, 5: 0.6, 10: 0.4, 20: 0.2}
    df, _ = frames(synth_per_run(n_seeds=40, r=r_plant), "vllm/x/y|default")
    ce = cell_effects(df, "band_mas")
    assert len(ce) == 12 and int(ce["admitted"].sum()) == 8                 # INTJ's 0.002 is below the 0.01 floor
    assert not ce[ce["Persona"] == "INTJ"]["admitted"].any() and ce[ce["Persona"] == "INTJ"]["r_5"].isna().all()
    assert ADMIT == 0.01
    ret = pooled_retention(df, "band_mas", n_boot=199)
    assert list(ret["k"]) == [2, 5, 10, 20] and (ret["n_admitted_cells"] == 8).all() and (ret["n_cells"] == 12).all()
    for _, row in ret.iterrows():
        assert abs(row["estimate"] - r_plant[row["k"]]) < 0.08, (row["k"], row["estimate"])
        assert row["ci_lo"] <= r_plant[row["k"]] <= row["ci_hi"] and row["share_1_over_k"] == 1.0 / row["k"]
    # the sign is handled: ENTJ's negative every-day effect contributes positively to the pooled retention
    e = ce[(ce["Persona"] == "ENTJ")]
    assert (e["d_1"] < 0).all() and (e["r_5"] > 0.4).all()


def test_predictions_read_the_retention_and_fail_where_they_should():
    from tools.phase9.e9_5_e8_analyse import cell_effects, frames, pooled_retention, predictions
    model = "vllm/x/y|default"

    def tables(r, d1=None, n_seeds=20):
        df, _ = frames(synth_per_run(n_seeds=n_seeds, r=r, d1=d1), model)
        ce = cell_effects(df, "band_mas"); ce.insert(0, "Model", model)
        ret = pooled_retention(df, "band_mas", n_boot=49); ret.insert(0, "Model", model)
        return ce, ret

    ce, ret = tables({2: 0.8, 5: 0.6, 10: 0.4, 20: 0.2})
    p = {x.pid: x for x in predictions([model], ret, ce, None)}
    assert p["P1"].verdict == "holds" and p["P2"].verdict == "holds" and p["P3"].verdict == "holds"
    assert p["P4"].verdict == "unevaluated"
    # no carry-over: r(k) = 1 / k exactly -> P3 fails, P2 fails (0.2 < 0.5), P1 still holds (0.5 > 0.05)
    ce, ret = tables({2: 0.5, 5: 0.2, 10: 0.1, 20: 0.05})
    p = {x.pid: x for x in predictions([model], ret, ce, None)}
    assert p["P3"].verdict == "fails" and p["P2"].verdict == "fails" and p["P1"].verdict == "holds"
    # no admitted cell -> degenerate, never held
    ce, ret = tables({2: 0.8, 5: 0.6, 10: 0.4, 20: 0.2}, d1={"ISFJ": 0.004, "INTJ": 0.002, "ENTJ": -0.003})
    p = {x.pid: x for x in predictions([model], ret, ce, None)}
    assert p["P1"].verdict == p["P2"].verdict == p["P3"].verdict == "degenerate"
    # P4 from a per-step summary: non-injected days between static and injected in the effect's direction
    ce, ret = tables({2: 0.8, 5: 0.6, 10: 0.4, 20: 0.2})
    adm = ce[ce["admitted"]]
    steps = []
    for _, c in adm.iterrows():
        s = 1.0 if c["d_1"] > 0 else -1.0
        for arm in ("memory_k5", "memory_k20"):
            steps.append({"Model": model, "Persona": c["Persona"], "Scenario_Cell": c["Scenario_Cell"], "arm": arm,
                          "dist_static": 0.20, "dist_injected": 0.20 + s * 0.04, "dist_non_injected": 0.20 + s * 0.02})
    steps = pd.DataFrame(steps)
    assert {x.pid: x for x in predictions([model], ret, ce, steps)}["P4"].verdict == "holds"
    steps["dist_non_injected"] = steps["dist_static"] - (steps["dist_injected"] - steps["dist_static"])   # beyond static
    assert {x.pid: x for x in predictions([model], ret, ce, steps)}["P4"].verdict == "fails"


def test_steps_summary_from_synthetic_run_csvs():
    from tools.phase9 import e9_5_e8_steps as S
    root = pathlib.Path(tempfile.mkdtemp(prefix="fp_e8s_"))
    try:
        model = "vllm/x/y|default"

        def write(subdir, setting, arm, seed, cash, injected=None):
            d = root / subdir / setting / "default" / "vllm_x_y" / "flat" / f"seed{seed}"
            d.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame({"Day": range(1, len(cash) + 1), "Persona": "ISFJ", "Arm": arm, "Scenario": "flat", "Seed": seed,
                               "Crash_Discount": 0.7, "Cash_Share": cash, "Band_Lo": 0.7, "Band_Hi": 0.9})
            if injected is not None:
                df["Mandate_Injected"] = injected
            df.to_csv(d / f"run__{arm}.csv", index=False)

        inj = [True, False, False, False, False] * 2
        cash = [0.8, 0.6, 0.5, 0.5, 0.5] * 2             # inside the band when injected, 0.1-0.2 below otherwise
        write("stage2_cadence", "cadence", "memory_k5", 10001, cash, inj)
        write("stage2_cadence", "cadence", "memory_k5", 10002, cash, inj)
        write("stage1_open", "default", "static", 10001, [0.5] * 10)
        write("stage1_open", "default", "memory", 10001, [0.8] * 10)
        write("stage1_open", "default", "static", 99999, [0.0] * 10)        # not a stage-2 seed: ignored
        runs = S.collect(str(root), str(root), [model])
        assert len(runs) == 4 and runs["arm"].value_counts().to_dict() == {"memory_k5": 2, "static": 1, "memory": 1}
        k5 = runs[runs["arm"] == "memory_k5"].iloc[0]
        assert k5["n_injected"] == 2 and abs(k5["dist_injected"] - 0.0) < 1e-12
        assert abs(k5["dist_non_injected"] - np.mean([0.1, 0.2, 0.2, 0.2] * 2)) < 1e-12
        assert abs(k5["dist_after_injection"] - 0.1) < 1e-12
        agg = S.aggregate(runs)
        row = agg[agg["arm"] == "memory_k5"].iloc[0]
        assert row["n_runs"] == 2 and row["k"] == 5 and abs(row["dist_static"] - 0.2) < 1e-12 and abs(row["dist_memory"] - 0.0) < 1e-12
        assert row["Scenario_Cell"] == "flat"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_main_end_to_end_on_a_synthetic_grid(tmp_path, monkeypatch):
    from tools.phase9 import e9_5_e8_analyse as A
    e94 = tmp_path / "e9_4"; out = e94 / "stats_e8_cadence"
    out.mkdir(parents=True)
    synth_per_run(n_seeds=8).to_csv(e94 / "per_run.csv", index=False)
    monkeypatch.setattr(A, "E94", str(e94)); monkeypatch.setattr(A, "OUT", str(out))
    monkeypatch.setattr(A, "STEPS_FILE", str(out / "steps_summary.csv")); monkeypatch.setattr(A, "N_BOOT", 49)
    assert A.main() == 0
    s = json.load(open(out / "summary.json", encoding="utf-8"))
    m = s["models"]["vllm/x/y|default"]
    assert m["m_family"] == [144] and m["decision_rule"] == "bh_within" and m["n_confirmatory_tests"] == 144
    assert m["admitted_cells_band_mas"] == 8 and set(m["retention_band_mas"]) == {"2", "5", "10", "20"}
    assert [p["id"] for p in s["predictions"]] == ["P1", "P2", "P3", "P4"] and s["predictions"][3]["verdict"] == "unevaluated"
    preds = pd.read_csv(out / "predictions.csv")
    assert len(preds) == 4 and (preds["experiment"] == "E8").all()
    for f in ("cell_effects.csv", "retention.csv", "vllm_x_y_default_v21_contrasts.csv"):
        assert (out / f).exists(), f
