"""v2.1 Phase 9, stage 2, E7 -- the OCEAN vocabulary gradient (PREREG_PHASE_9_STAGE2_E7.md).

What is locked here, in the order the build landed:

* the counterpart map: an OCEAN persona's mandate is its MBTI counterpart's, byte for byte, at every wording level and
  in every arm kind, so a vocabulary contrast attributes to the persona TEXT alone;
* that the map moved no MBTI prompt: every prompt hash every manifest on disk stores still recomputes;
* the manifest stage: the OCEAN pair under the slice's three arms at common start, no NONE cells, on CAUSAL_OPEN;
* the statistics trap, stated as a test: the shared family dict fires the wrong contrasts on both E7 frame shapes;
* the analysis: the registered family recovers a planted vocabulary effect at m = 72 under bh_within, the interaction
  read recovers a planted interaction and refuses cells at the floor, the predictions mark floor cells degenerate
  and per-step predictions unevaluated;
* the per-step script: identification on the frames it builds, and a known-answer share recovery on an OCEAN frame.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
LEVELS = ("original", "rewritten", "paraphrase", "abbreviated", "no_action_clauses", "no_delimiter", "defensive", "numeric_only")
PAIRS = (("O1_conservative", "ISFJ"), ("O2_aggressive", "ENTJ"))
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")


# ================================================================================================ the counterpart map
def test_ocean_mandate_is_its_counterparts_at_every_wording_level():
    """E7's premise: the directive is byte-identical across the vocabulary gradient.  Before MANDATE_COUNTERPART, O1 at
    the default `rewritten` wording carried v1's "Buy insurance (puts/hedges)" while ISFJ carried the cash-cushion
    rewrite, and the paraphrase / abbreviated / no-action-clause levels fell through to the v1 text too."""
    from agent import v2_prompts as P
    from agent.prompt_matching import UnannotatedClause

    def block(kind, persona, level, pv):
        try:
            return ("ok", P.mandate_block(kind, persona, level, pv))
        except UnannotatedClause as exc:     # the matched placebo at a wording whose clauses are not annotated
            return ("raise", type(exc).__name__)

    for ocean, mbti in PAIRS:
        for level in LEVELS:
            assert P.mandate_text(ocean, level) == P.mandate_text(mbti, level), (ocean, level)
            for kind in ("mandate", "wrapper_only", "placebo_declarative", "placebo_directive"):
                for pv in ("v2", "v2_1"):
                    assert block(kind, ocean, level, pv) == block(kind, mbti, level, pv), (ocean, level, kind, pv)
        if ocean == "O1_conservative":    # the single-asset rewrite reached O1: the cash cushion, no puts or hedges
            assert "Keep a large cash cushion" in P.mandate_text(ocean) and "puts/hedges" not in P.mandate_text(ocean)
            assert "puts/hedges" in P.mandate_text(ocean, "original")      # v1's text is still the `original` level
        # the persona TEXT is the thing that differs
        assert P.system_prompt(ocean) != P.system_prompt(mbti)
        assert "Openness to Experience" in P.system_prompt(ocean) and "Openness to Experience" not in P.system_prompt(mbti)
    assert P.MANDATE_COUNTERPART == {"O1_conservative": "ISFJ", "O2_aggressive": "ENTJ"}


def test_ocean_swapped_arm_follows_the_counterpart():
    """`swapped` gives O1 the O2 mandate and ISFJ the ENTJ mandate: the same bytes."""
    from agent import v2_prompts as P
    from experiments.arms_v2 import build_config
    for ocean, mbti in PAIRS:
        co = build_config("m", ocean, "swapped", "flat", 1, factors={"start_design": "common"})
        cm = build_config("m", mbti, "swapped", "flat", 1, factors={"start_design": "common"})
        assert co.start_design == cm.start_design == "common"
        assert P.mandate_block("mandate", co.mandate_persona) == P.mandate_block("mandate", cm.mandate_persona)
        assert co.mandate_persona != cm.mandate_persona      # O2 against ENTJ: different labels, one text


def test_no_mbti_prompt_hash_moved():
    """`agent/v2_prompts.py` is one of the eight sources the manifest fingerprint hashes, so the map moved every
    manifest's source hash for that file.  What must NOT have moved is any prompt: every (configuration, persona,
    arm) prompt hash that every manifest on disk stores recomputes to the same value with the map in place."""
    import glob
    from tools.phase9 import e9_runner as R
    paths = sorted(glob.glob(os.path.join(GEN, "e9_4", "manifest_*.json")))
    if not paths:
        pytest.skip("no manifest on disk")
    moved, total = [], 0
    for p in paths:
        m = R.load_manifest(p)
        cur = R.fingerprint(m)
        total += len(m["fingerprint"]["prompt_hash"])
        moved += [(os.path.basename(p), k) for k, v in m["fingerprint"]["prompt_hash"].items() if cur["prompt_hash"].get(k) != v]
        assert cur["Env_Code_Hash"] == m["fingerprint"]["Env_Code_Hash"], os.path.basename(p)
    assert total > 0 and not moved, moved


# ================================================================================================ the manifest stage
def test_e7_cells_are_the_ocean_pair_at_common_start():
    from tools.phase9.e9_4_grid import OCEAN_MANIFEST, OCEAN_PERSONAS, SLICE_ARMS, STAGE2_MANIFESTS, cells_for
    assert STAGE2_MANIFESTS["ocean_open"] == OCEAN_MANIFEST == "manifest_ocean_open.json"
    assert OCEAN_PERSONAS == ("O1_conservative", "O2_aggressive")
    seeds = list(range(10001, 10004))
    cells = cells_for("ocean", seeds)
    assert len(cells) == 2 * 3 * 4 * len(seeds)
    assert {c["persona"] for c in cells} == set(OCEAN_PERSONAS)          # no NONE cell: E3's trader is the reference
    assert {c["arm"] for c in cells} == set(SLICE_ARMS)
    assert {c["scenario"] for c in cells} == set(SCENARIOS)
    assert all(c["setting"] == "common_start" and c["factors"] == {"start_design": "common"} for c in cells)
    # the slice's cells for the same seeds, with the personas swapped for the pair, are these cells
    sl = [{**c, "persona": {"ISFJ": "O1_conservative", "ENTJ": "O2_aggressive"}[c["persona"]]}
          for c in cells_for("slice", seeds) if c["persona"] in ("ISFJ", "ENTJ")]
    assert sorted(map(json.dumps, sl), key=str) == sorted(map(json.dumps, cells), key=str)


def test_e7_manifest_on_disk_is_its_cells_and_roster():
    """The written manifest: CAUSAL_OPEN (the six E3 ran, so the reference and the MBTI side exist for every E7 model),
    the stage-2 seeds, its own subdir, one prompt hash per (configuration, persona, arm) -- and the hash it stores is
    the hash a run produces, end to end."""
    from langchain_core.runnables import RunnableLambda
    from agent.v2_agent import V2Agent
    from simulation.provenance import agent_provenance
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    from tools.phase9.e9_4_grid import OCEAN_MANIFEST, OUT, S_STAGE2, SLICE_OPEN_MANIFEST, cells_for
    path = os.path.join(OUT, OCEAN_MANIFEST)
    if not os.path.exists(path):
        pytest.skip("manifest_ocean_open.json is not written yet")
    m = R.load_manifest(path)
    seeds = list(range(10001, 10001 + S_STAGE2))
    assert m["name"] == "e9_4_stage2_ocean" and m["subdir"] == "stage2_ocean" and m["seeds"] == seeds
    assert m["configs"] == list(RO.CAUSAL_OPEN) and m["cells"] == cells_for("ocean", seeds)
    for key in m["configs"]:
        hashes = {k: v for k, v in m["fingerprint"]["prompt_hash"].items() if k.startswith(key + "|")}
        assert len(hashes) == 6, key
    key = m["configs"][0]
    mc = RO.by_key(key)
    cell = next(c for c in m["cells"] if c["persona"] == "O1_conservative" and c["arm"] == "memory")
    cfg = R.cfg_for(mc, cell, m["subdir"])
    assert cfg.start_design == "common" and cfg.persona == "O1_conservative" and cfg.mandate_block == "mandate"
    ag = V2Agent(persona=cfg.persona, model_name=cfg.model_name, mandate_block=cfg.mandate_block,
                 mandate_persona=cfg.mandate_persona, wording=cfg.wording, track=cfg.track,
                 action_interface=cfg.action_interface, n_assets=cfg.n_assets, disclose_horizon=cfg.disclose_horizon,
                 T=cfg.T, cost_visible=cfg.cost_visible, cost_bp=cfg.cost_bp, objective=cfg.objective,
                 mandate_in_system=cfg.mandate_in_system, temperature=cfg.temperature,
                 liquidity_condition=cfg.liquidity_condition, llm=RunnableLambda(lambda x: None),
                 placebo_version=cfg.placebo_version)
    assert agent_provenance(ag)["Prompt_Hash"] == m["fingerprint"]["prompt_hash"][R.prompt_key(key, cell)]
    # the mandate block an O1 memory run injects is ISFJ's, byte for byte; the system prompt is not
    from agent import v2_prompts as P
    assert ag.core_mandate == P.mandate_block("mandate", "ISFJ", cfg.wording, cfg.placebo_version)
    sl = os.path.join(OUT, SLICE_OPEN_MANIFEST)
    if os.path.exists(sl):
        s = R.load_manifest(sl)
        assert m["fingerprint"]["Env_Code_Hash"] == s["fingerprint"]["Env_Code_Hash"]
        assert m["fingerprint"]["prompt_hash"][f"{key}|O1_conservative|memory"] != s["fingerprint"]["prompt_hash"][f"{key}|ISFJ|memory"]
        assert m["seeds"] == s["seeds"] and m["configs"] == s["configs"]


def test_e7_verify_stage_reads_the_manifest(tmp_path):
    """`--stages verify --only ocean_open` plans 1,440 runs per configuration under the common-start rule and reports
    them missing, never passed, while no run exists; the report goes to tmp_path, not to the tracked verify.json."""
    from tools.phase9.e9_4_grid import OCEAN_MANIFEST, OUT, stage_verify
    if not os.path.exists(os.path.join(OUT, OCEAN_MANIFEST)):
        pytest.skip("manifest_ocean_open.json is not written yet")
    report = tmp_path / "verify_ocean_open.json"
    stage_verify(only=("ocean_open",), out_path=str(report))
    v = json.load(open(report, encoding="utf-8"))
    assert v["rows"] and all(r["manifest"] == "ocean_open" and r["planned"] == 1440 for r in v["rows"])
    assert all(r["verified"] + r["missing"] == 1440 and r["mismatched"] == 0 for r in v["rows"])


# ================================================================================================ synthetic tables
def synth_per_run(seed: int = 0, n_seeds: int = 10, voc_effect: float = 0.0, interaction: float = 0.0,
                  memory_effect: float = 0.03, floor_cells=(), model: str = "vllm/x/y|default") -> pd.DataFrame:
    """A per_run.csv-shaped table for one model: E7's OCEAN rows and E3's slice rows on shared paths, with a planted
    vocabulary effect (OCEAN - MBTI, every arm), a planted vocabulary x arm interaction (on the memory arm only) and a
    planted mandate effect (memory - static, both vocabularies).  `floor_cells` pins both static arms of a (persona
    category, scenario) at exactly 0."""
    rng = np.random.default_rng(seed)
    path = {(sc, s): rng.normal(0, 0.02) for sc in SCENARIOS for s in range(10001, 10001 + n_seeds)}
    cat = {"O1_conservative": "conservative", "ISFJ": "conservative", "O2_aggressive": "aggressive", "ENTJ": "aggressive",
           "INTJ": "balanced"}
    rows = []
    for manifest, personas, voc in (("e9_4_stage2_ocean", ("O1_conservative", "O2_aggressive"), "ocean"),
                                    ("e9_4_stage2_slice", ("ISFJ", "INTJ", "ENTJ"), "mbti")):
        for p in personas:
            for a in ("static", "memory", "swapped"):
                for sc in SCENARIOS:
                    for s in range(10001, 10001 + n_seeds):
                        y = 0.10 + {"static": 0.0, "memory": memory_effect, "swapped": 0.25}[a] + path[(sc, s)]
                        y += (voc_effect if voc == "ocean" else 0.0) + (interaction if (voc == "ocean" and a == "memory") else 0.0)
                        y += rng.normal(0, 0.004)
                        if (cat[p], sc) in floor_cells and a == "static":
                            y = 0.0
                        y = max(y, 0.0)
                        rows.append({"Manifest": manifest, "Setting": "common_start", "Model": model, "Persona": p, "Arm": a,
                                     "Scenario": sc, "Seed": s, "Decode_Replicate": 0, "score_error": "",
                                     "band_mas": y, "v21_mcr_D_0.05": y * 0.5 + rng.normal(0, 0.003),
                                     "v21_mcr_D_0.002": y * 0.4 + rng.normal(0, 0.003),
                                     "turnover": 0.3, "mdd_pct": -2.0, "return_pct": 1.0, "fallback_share": 0.0,
                                     "trade_count": 5})
    for sc in SCENARIOS:
        for s in range(10001, 10001 + n_seeds):
            rows.append({"Manifest": "e9_4_stage2_slice", "Setting": "common_start", "Model": model, "Persona": "NONE",
                         "Arm": "trader", "Scenario": sc, "Seed": s, "Decode_Replicate": 0, "score_error": "",
                         "band_mas": 0.0, "v21_mcr_D_0.05": 0.5, "v21_mcr_D_0.002": 0.5, "turnover": 1.0, "mdd_pct": -5.0,
                         "return_pct": 0.0, "fallback_share": 0.0, "trade_count": 90})
    return pd.DataFrame(rows)


def test_e7_registered_family_is_absent_from_the_shared_dict():
    """The trap E3 and E4 hit, stated for E7 before it can bite.  On the raw OCEAN frame the shared dict fires Q1's
    memory - static and Q2's swapped - memory (two families, by_across); on the frame section 3 words it fires the same
    two WITHIN the OCEAN rows and would report them under bh_within -- the registered rule on the wrong question.  The
    registered contrasts are in neither list."""
    from tools.phase9.e9_5_e7_analyse import E7_FAMILY, frames
    from tools.stats_v2 import question_families
    qf = question_families()

    def fires(arms):
        return sorted(f"{a} - {r}" for pairs in qf.values() for a, r in pairs if a in arms and r in arms)

    registered = sorted(f"{a} - {r}" for a, r in E7_FAMILY["E7"])
    assert registered == ["memory - memory_M", "static - static_M", "swapped - swapped_M"]
    raw = fires({"static", "memory", "swapped"})
    assert raw == ["memory - static", "swapped - memory"]
    df, why = frames(synth_per_run(n_seeds=3), "vllm/x/y|default")
    assert df is not None, why
    assert set(df["Arm"]) == {"static", "memory", "swapped", "static_M", "memory_M", "swapped_M"}
    worded = fires(set(df["Arm"]))
    assert worded == ["memory - static", "swapped - memory"]
    assert not set(registered) & set(raw) and not set(registered) & set(worded)


def test_e7_frames_relabel_and_pair_without_collision():
    from tools.phase9.e9_5_e7_analyse import frames, pairing_check
    df, why = frames(synth_per_run(n_seeds=4), "vllm/x/y|default")
    assert df is not None, why
    assert set(df["Persona"]) == {"conservative", "aggressive"}          # INTJ and NONE never enter an E7 frame
    assert set(df["Vocabulary"]) == {"ocean", "mbti"}
    pc = pairing_check(df)
    assert pc["keys_with_two_manifests"] == 0 and pc["keys_with_six_arms"] == pc["keys_total"] == 2 * 4 * 4
    # one persona label without the suffix would collapse the two vocabularies into one mean: the check sees it
    bad = df.copy()
    bad["Arm"] = bad["Arm"].str.replace("_M", "", regex=False)
    assert pairing_check(bad)["keys_with_two_manifests"] > 0


def test_e7_registered_family_recovers_a_planted_vocabulary_effect(tmp_path):
    """m = 72 under bh_within, and `static - static_M` on band-MAS estimates the planted OCEAN - MBTI difference."""
    from tools.phase9.e9_5_e7_analyse import E7_FAMILY, frames
    from tools.stats_v2 import run_stats_v21
    df, _ = frames(synth_per_run(n_seeds=10, voc_effect=0.04), "vllm/x/y|default")
    t = run_stats_v21(df, str(tmp_path / "e7"), n_boot=199, families=E7_FAMILY)["contrasts"]
    tc = t[t["tier"] == "C"]
    assert len(tc) == 72 and sorted(set(tc["m_family"])) == [72] and set(tc["decision_rule"]) == {"bh_within"}
    assert set(tc["contrast"]) == {"static - static_M", "memory - memory_M", "swapped - swapped_M"}
    st = tc[(tc["contrast"] == "static - static_M") & (tc["metric"] == "band_mas")]
    assert len(st) == 8 and np.allclose(st["estimate"], 0.04, atol=0.01)
    assert st["claim"].all()
    # without the family argument the same frame answers a different question under the same rule
    t0 = run_stats_v21(df, str(tmp_path / "shared"), n_boot=199)["contrasts"]
    assert set(t0[t0["tier"] == "C"]["contrast"]) == {"memory - static", "swapped - memory"}
    assert set(t0["decision_rule"]) == {"by_across"}


def test_e7_interaction_reads_against_the_margin_and_refuses_the_floor():
    from tools.phase9.e9_5_e7_analyse import ADMIT, MARGIN, frames, interaction
    # no interaction, an admitted mandate effect: inside the margin, signs agree
    df, _ = frames(synth_per_run(n_seeds=12, memory_effect=0.03, interaction=0.0), "vllm/x/y|default")
    i = interaction(df, "band_mas")
    assert len(i) == 8 and i["admitted"].all() and i["inside_margin_90"].all() and i["signs_agree"].all()
    assert np.allclose(i["estimate"], 0.0, atol=0.01) and (i["lo90"] >= i["lo95"]).all() and (i["hi90"] <= i["hi95"]).all()
    # a planted interaction twice the margin: outside
    df, _ = frames(synth_per_run(n_seeds=12, memory_effect=0.03, interaction=2 * MARGIN + 0.01), "vllm/x/y|default")
    i = interaction(df, "band_mas")
    assert i["admitted"].all() and not i["inside_margin_90"].any()
    # no mandate effect in either vocabulary: not admitted, whatever the interval says
    df, _ = frames(synth_per_run(n_seeds=12, memory_effect=0.0, interaction=0.0), "vllm/x/y|default")
    i = interaction(df, "band_mas")
    assert not i["admitted"].any() and (i[["effect_ocean", "effect_mbti"]].abs() < ADMIT).all().all()


def test_e7_equivalence_marks_floor_and_underpowered_cells():
    from tools.phase9.e9_5_e7_analyse import DELTA, equivalence, frames
    df, _ = frames(synth_per_run(n_seeds=10, voc_effect=0.0, floor_cells=(("conservative", "flat"),)), "vllm/x/y|default")
    e = equivalence(df, mdd=0.04)
    assert len(e) == 8 and int(e["degenerate"].sum()) == 1 and not e["underpowered"].any()
    deg = e[e["degenerate"]].iloc[0]
    assert deg["Persona"] == "conservative" and deg["Scenario_Cell"] == "flat"
    assert deg["static_ocean"] == 0.0 and deg["static_mbti"] == 0.0 and deg["inside_delta_90"]
    assert e[~e["degenerate"]]["inside_delta_90"].all()
    e2 = equivalence(df, mdd=0.093)
    assert e2["underpowered"].all() and (e2["mdd_S60"] > DELTA).all()


def test_e7_predictions_are_unevaluated_without_the_per_step_summary_and_count_only_admitted_cells():
    from tools.phase9.e9_5_e7_analyse import (DEGENERATE, UNEVALUATED, equivalence, frames, interaction, pooled_effects,
                                              predictions)
    model = "vllm/x/y|default"
    df, _ = frames(synth_per_run(n_seeds=10, memory_effect=0.03, floor_cells=(("aggressive", "crash"),)), model)
    eq = equivalence(df, mdd=0.04); eq.insert(0, "Model", model)
    it = interaction(df, "band_mas"); it.insert(0, "Model", model)
    w = pooled_effects(df); w.insert(0, "Model", model)
    assert len(w) == 4 and (w["n_pairs"] == 40).all()
    cons = w[w["Persona"] == "conservative"]["estimate"]; aggr = w[w["Persona"] == "aggressive"]["estimate"]
    assert np.allclose(cons, 0.03, atol=0.01)                      # the planted mandate effect
    assert (aggr > 0.045).all() and (aggr < 0.07).all()             # one static cell pinned at 0 lifts the pooled effect
    preds = {p.pid: p for p in predictions([model], eq, it, w, salience=None)}
    assert set(preds) == {"P1", "P2", "P3", "P4", "P5"}
    assert preds["P1"].verdict == UNEVALUATED and preds["P5"].verdict == UNEVALUATED
    assert preds["P2"].stat["degenerate"] == 1 and preds["P2"].stat["counted"] == 7
    assert preds["P4"].stat["admitted"] == 8 and preds["P4"].verdict == "holds"
    # P3 is per model over six: one synthetic model cannot reach the five-model bar, and that is the honest verdict
    assert preds["P3"].stat["models_rising_pooled"] == 1 and preds["P3"].stat["agree"] == 4 and preds["P3"].verdict == "fails"
    # with a per-step summary P1 and P5 are evaluated from it; an unreadable frame (R2 below 0.5) counts for nothing
    good = {"identified": True, "windows": [{"r2": 0.8, "S_persona": 0.7, "S_directive": 0.1}] * 8}
    bad = {"identified": True, "windows": [{"r2": 0.1, "S_persona": 0.9, "S_directive": 0.0}] * 8}
    summ = {"models": {model: {"ocean": good, "mbti_pair": good, "gate": {"ocean": {"auc": 0.6}, "mbti_pair": {"auc": 0.65}}}}}
    preds = {p.pid: p for p in predictions([model], eq, it, w, salience=summ)}
    assert preds["P1"].verdict == "fails" and preds["P1"].stat == {**preds["P1"].stat, "dominate": 1, "invariant": 1, "readable": 1}
    assert preds["P5"].verdict == "fails" and preds["P5"].stat["close"] == 1
    summ["models"][model]["ocean"] = bad
    preds = {p.pid: p for p in predictions([model], eq, it, w, salience=summ)}
    assert preds["P1"].stat["readable"] == 0 and preds["P1"].stat["unreadable"] == ["y"]
    # a frame with no admitted interaction cell is degenerate, never a pass
    it0 = it.copy(); it0["admitted"] = False
    preds = {p.pid: p for p in predictions([model], eq, it0, w, salience=None)}
    assert preds["P4"].verdict == DEGENERATE


def test_e7_analysis_end_to_end_on_a_synthetic_per_run(tmp_path, monkeypatch):
    """`main()` on a per_run.csv holding one model's E7 and E3 rows writes the family at m = 72, the exploratory
    within-OCEAN family at m = 48 with no claim, the equivalence and interaction tables, and predictions.csv."""
    from tools.phase9 import e9_5_e7_analyse as M
    e94 = tmp_path / "e9_4"; e94.mkdir()
    synth_per_run(n_seeds=8, voc_effect=0.0, memory_effect=0.03).to_csv(e94 / "per_run.csv", index=False)
    monkeypatch.setattr(M, "E94", str(e94))
    monkeypatch.setattr(M, "OUT", str(e94 / "stats_e7_ocean"))
    monkeypatch.setattr(M, "NOISE", str(e94 / "absent.csv"))
    assert M.main() == 0
    s = json.load(open(e94 / "stats_e7_ocean" / "summary.json", encoding="utf-8"))
    r = s["models"]["vllm/x/y|default"]
    assert r["n_confirmatory_tests"] == 72 and r["m_family"] == [72] and r["decision_rule"] == "bh_within"
    assert r["n_exploratory_within_ocean"] == 48 and r["pairing"]["keys_with_two_manifests"] == 0
    w = pd.read_csv(e94 / "stats_e7_ocean" / "vllm_x_y_default_within_ocean_v21_contrasts.csv")
    assert not w["claim"].any() and w["role"].str.startswith("exploratory").all()
    p = pd.read_csv(e94 / "stats_e7_ocean" / "predictions.csv")
    assert list(p["prediction"]) == ["P1", "P2", "P3", "P4", "P5"]
    assert set(p[p["prediction"].isin(["P1", "P5"])]["verdict"]) == {"unevaluated"}
    assert p.set_index("prediction").loc["P4", "verdict"] == "holds"


# ================================================================================================ the per-step script
def _per_step_frame(rng, personas, n_seeds=10, n_days=25, planted=0.3, with_trader=True):
    """A per-STEP frame of the shape runner_v2 writes, with a planted persona effect on the cash share."""
    from evaluation.salience import MARKET_FEATURES
    from evaluation.targets import centre
    swap = {"O1_conservative": "O2_aggressive", "O2_aggressive": "O1_conservative", "ISFJ": "ENTJ", "ENTJ": "ISFJ"}
    cells = [(p, a, mb, (swap[p] if a == "swapped" else p)) for p in personas
             for a, mb in (("static", "none"), ("memory", "mandate"), ("swapped", "mandate"))]
    if with_trader:
        cells.append(("NONE", "trader", "none", "NONE"))
    rows = []
    for sc in ("flat", "crash"):
        market = {(s, t): {f: rng.normal() for f in MARKET_FEATURES} for s in range(n_seeds) for t in range(1, n_days + 1)}
        for p, arm, mb, mp in cells:
            lvl = 0.5 if p == "NONE" else 0.5 + planted * (centre(p) - 0.5) / 0.35
            for s in range(n_seeds):
                for t in range(1, n_days + 1):
                    mk = market[(s, t)]
                    y = float(np.clip(lvl + 0.03 * mk["obs_RSI14"] + rng.normal(0, 0.03), 0, 1))
                    rows.append({"Model": "m", "Persona": p, "Arm": arm, "Scenario": sc, "Crash_Discount": 0.7,
                                 "Mandate_Block": mb, "Mandate_Persona": mp, "Seed": 10001 + s, "Decode_Replicate": 0,
                                 "Day": t, "Start_Design": "common", "Start_Cash_Share": 0.5, "Target_Cash_Share": y,
                                 "Cash_Share": y, "Parse_Status": "ok", **mk})
    return pd.DataFrame(rows)


def test_e7_salience_frames_are_identified_only_with_the_reference():
    """The OCEAN pair plus NONE is identified (persona rank 2, directive rank 2); the pair alone fails clause (iv); the
    pooled frame is identified either way, but relabelling the directive by category -- one text after the counterpart
    map -- drops the persona-to-directive canonical correlation from about 0.8 to under 0.4, which is why the two
    per-vocabulary frames are the registered read and the pooled frame a check."""
    from evaluation.salience import identification_check
    from tools.phase9.e9_5_e7_salience import CATEGORY, frames_for
    rng = np.random.default_rng(7)
    ocean = _per_step_frame(rng, ("O1_conservative", "O2_aggressive"), n_seeds=4, n_days=2, with_trader=False)
    mbti = _per_step_frame(rng, ("ISFJ", "ENTJ"), n_seeds=4, n_days=2, with_trader=False)
    trader = _per_step_frame(rng, (), n_seeds=4, n_days=2, with_trader=True)
    fr = frames_for("m", ocean, mbti, trader)
    assert set(fr) == {"ocean", "mbti_pair", "pooled"}
    o = identification_check(fr["ocean"])
    assert o["identified"] and o["ranks"]["persona"] == 2 and o["ranks"]["directive"] == 2 and o["ranks"]["start"] == 0
    assert not o["identified_as_registered"] and o["failing_clauses_as_registered"] == ["i_every_block_varies"]
    alone = identification_check(ocean)
    assert not alone["identified"] and alone["failing_clauses"] == ["iv_reference_levels_present"]
    assert set(fr["pooled"]["Mandate_Persona"]) == {"conservative", "aggressive", "NONE"}
    pooled = identification_check(fr["pooled"])
    assert pooled["identified"] and pooled["ranks"]["directive"] == 2
    raw = pd.concat([ocean, mbti, trader], ignore_index=True)
    assert identification_check(raw)["max_canonical_corr"]["persona~directive"] > 0.7
    assert pooled["max_canonical_corr"]["persona~directive"] < 0.4
    assert CATEGORY["O1_conservative"] == CATEGORY["ISFJ"] == "conservative"


def test_e7_known_answer_shares_on_an_ocean_frame():
    """A planted persona effect on an OCEAN-labelled common-start frame is recovered as the persona share, with the
    directive share near zero -- the known-answer recovery Phase 8 ran on the MBTI labels (E8.4), on the labels E7 uses."""
    from evaluation.salience import salience_by_window
    from tools.phase9.e9_5_e7_salience import frames_for
    rng = np.random.default_rng(11)
    ocean = _per_step_frame(rng, ("O1_conservative", "O2_aggressive"), n_seeds=10, n_days=25, with_trader=False)
    trader = _per_step_frame(rng, (), n_seeds=10, n_days=25, with_trader=True)
    d = frames_for("m", ocean, pd.DataFrame(columns=ocean.columns), trader)["ocean"]
    out = salience_by_window(d, window=25, identification="v2_1", n_boot=0, null_reps=0, n_estimators=40, n_repeats=3)
    assert len(out) == 1 and out["status"].iloc[0] == "IDENTIFIED"
    assert out["S_persona"].iloc[0] > 0.8 and out["S_directive"].iloc[0] < 0.1 and out["r2"].iloc[0] > 0.5
    assert pd.isna(out["S_start"].iloc[0])        # constant at common start: not a share


def test_e7_gate_and_cash_share_precondition_on_a_synthetic_frame():
    from tools.phase9.e9_5_e7_salience import gate, mean_cash_share
    rng = np.random.default_rng(3)
    ocean = _per_step_frame(rng, ("O1_conservative", "O2_aggressive"), n_seeds=12, n_days=3, with_trader=True)
    g = gate(ocean, ("O1_conservative", "O2_aggressive"))
    assert g["persona_arms"]["n"] == 2 * 3 * 2 * 12 and g["static_arm_only"]["n"] == 2 * 2 * 12
    assert 0.0 <= g["auc"] <= 1.0 and g["auc"] > 0.9 and g["null"].startswith("NOT COMPUTABLE")
    assert "kw_p" in g["persona_arms"] and "band_hit" in g["persona_arms"]
    mcs = mean_cash_share(ocean)
    assert set(mcs["Arm"]) == {"static", "memory", "swapped", "trader"}
    assert set(mcs["Scenario_Cell"]) == {"flat", "crash_d0.7"} and (mcs["size"] == 12).all()
    st = mcs[mcs["Arm"] == "static"].groupby("Persona")["mean"].mean()       # one row per persona x scenario cell
    assert st["O1_conservative"] > 0.6 > 0.4 > st["O2_aggressive"]
