"""
v2.1 Phase 8 regression tests (plan Section 12.4; PREREG_PHASE_8.md 1, 2, 5, 7).

Two kinds of test, as in Phase 7:

* **the section's own** -- `test_stateful_no_duplicate_mandate`, `test_context_budget_parity`,
  `test_fallback_not_in_history`, `test_placebo_matching` (E8.1), and the E8.3 / E8.4 tests
  `test_mixed_model_crossed`, `test_bh_family_size_logged`, `test_salience_common_start_only`;
* **the inertness of every switch** -- `test_phase8_switches_inert` re-captures the defaults and compares them with
  the golden record written from the unmodified code before the first edit (`tests/phase8_golden.json`).

Every E8.1 test builds BOTH stateful arms itself with a deterministic fake LLM: the pilot never ran `stateful_static`,
so nothing it logged can check parity.

    python -m pytest tests/test_v2_1_phase_8.py -q
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(scope="module")
def obs():
    from tools.phase8.e8_0_golden import _observations
    return _observations(24)


@pytest.fixture(autouse=True)
def _no_retry_pause(monkeypatch):
    import agent.stateful_agent as SA
    monkeypatch.setattr(SA.time, "sleep", lambda s: None)


def _roll(obs, mandate_block, mode, harness, steps, unparseable_day="", persona="ENTJ", llm=None, **kw):
    """Run a stateful agent; return (agent, per-step logs, per-step context characters, per-step history json)."""
    from agent.stateful_agent import StatefulV2Agent
    from tools.phase8.e8_0_golden import fake_llm
    a = StatefulV2Agent(persona, "fake", mandate_block=mandate_block, context_mode=mode, harness=harness,
                        llm=llm if llm is not None else fake_llm([], unparseable_day), **kw)
    logs, chars, hist = [], [], []
    cash = 0.10
    for t in range(steps):
        port = {"cash": 10000.0 * cash, "holdings_value": 10000.0 * (1 - cash), "cash_share": cash}
        chars.append(sum(len(m.content) for m in a.build_messages(obs[t], port)))
        d = a.decide(obs[t], port)
        cash = float(d.target_cash_share)
        logs.append(a.context_log())
        hist.append(json.dumps(a.history))
    return a, logs, chars, hist


MODES = [("rolling", {"window": 5}, 12), ("rolling", {"window": 20}, 23), ("full", {"token_budget": 3000}, 14),
         ("summary", {}, 22)]


# ================================================================================================ E8.1 (a), (b)
def test_stateful_no_duplicate_mandate(obs):
    """E8.1(a)/(b), weakness 57: under v2_1 the context carries the system copy and the current turn's block only; the
    nearest copy is the injected block and its offset is the tail after it (the format instructions), constant across
    days.  Under v2 a full window replayed `window` copies (the defect, documented)."""
    from agent.stateful_agent import count_tokens
    for window, steps in ((5, 9), (20, 23)):
        a, logs, _, _ = _roll(obs, "mandate", "rolling", "v2_1", steps, window=window)
        assert logs[-1]["Context_Turns"] == window
        assert logs[-1]["Mandate_Copies_In_Context"] == 2
        assert all(a._mandate_text not in h["human"] for h in a.history), "a retained turn still carries the mandate"
        tail = count_tokens("\n\n" + a.parser.get_format_instructions())[0]
        assert {l["Mandate_Offset_Injected"] for l in logs} == {tail}
        assert all(l["Mandate_Offset_Tokens"] == l["Mandate_Offset_Injected"] < l["Mandate_Offset_System"] for l in logs)
        assert all(l["Offset_Count_Method"] == "tokenizer:o200k_base" for l in logs)
        s, slogs, _, _ = _roll(obs, "none", "rolling", "v2_1", steps, window=window)
        assert slogs[-1]["Mandate_Copies_In_Context"] == 1 and slogs[-1]["Mandate_Offset_Injected"] is None
        assert all(l["Mandate_Offset_Tokens"] == l["Mandate_Offset_System"] for l in slogs)
        # the v2 defect: a full window replays one copy per retained turn
        b, blogs, _, _ = _roll(obs, "mandate", "rolling", "v2", steps, window=window)
        port = {"cash": 1000.0, "holdings_value": 9000.0, "cash_share": 0.1}
        copies = sum(m.content.count(b._mandate_text) for m in b.build_messages(obs[steps], port))
        assert copies == window + 2
        assert "Harness_Version" not in blogs[-1], "the v2 log gained a column"


def test_context_budget_parity(obs):
    """E8.1(b), PREREG 1.3, exact: under the same replies the memory arm's retained history is byte-identical to the
    static arm's at every step in every context mode, and the contexts differ by exactly the block's characters.
    Under v2 the difference is not constant (it grows with the replayed copies, or, in `full`, the chars/4 budget
    drops more of the memory arm's turns)."""
    from agent import v2_prompts as P
    block = len(P.mandate_block("mandate", "ENTJ", "rewritten"))
    for mode, kw, steps in MODES:
        _, _, cs, hs = _roll(obs, "none", mode, "v2_1", steps, **kw)
        _, _, cm, hm = _roll(obs, "mandate", mode, "v2_1", steps, **kw)
        assert hs == hm, f"{mode} {kw}: the histories differ"
        assert {m - s for s, m in zip(cs, cm)} == {block}, f"{mode} {kw}: the contexts differ by more than the block"
        _, _, cs2, _ = _roll(obs, "none", mode, "v2", steps, **kw)
        _, _, cm2, _ = _roll(obs, "mandate", mode, "v2", steps, **kw)
        assert len({m - s for s, m in zip(cs2, cm2)}) > 1, f"{mode} {kw}: v2 was expected to be mismatched"


# ================================================================================================ E8.1 (c)
def test_fallback_not_in_history(obs):
    """E8.1(c): a parse fallback leaves "no valid answer" in the history, never the fabricated decision; under v2 the
    fabricated TargetAllocation was stored as the model's own prior turn (latent: 0 fallbacks in the pilot)."""
    from agent.stateful_agent import FALLBACK_HISTORY_TEXT
    a, logs, _, _ = _roll(obs, "mandate", "rolling", "v2_1", 7, unparseable_day="Day-4", window=5)
    assert a.history[3]["ai"] == FALLBACK_HISTORY_TEXT == "no valid answer"
    assert not any("Error after 3 attempts" in h["ai"] for h in a.history)
    assert logs[3]["History_Fallback_Turns"] == 1 and a.last_parse_status == "ok"
    b, _, _, _ = _roll(obs, "mandate", "rolling", "v2", 7, unparseable_day="Day-4", window=5)
    assert "Error after 3 attempts" in b.history[3]["ai"] and "target_cash_share" in b.history[3]["ai"]


# ================================================================================================ E8.1 (d)
def test_token_count_method_logged(obs):
    """E8.1(d): the provider's usage replaces the tokenizer count for the context and scales the offsets into the
    provider's unit; without usage the tokenizer count is used; the method reaches the log either way."""
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    def with_usage(messages):
        return AIMessage(content=json.dumps({"target_cash_share": 0.3, "rationale": "x"}),
                         usage_metadata={"input_tokens": 5000, "output_tokens": 20, "total_tokens": 5020})

    a, logs, _, _ = _roll(obs, "mandate", "rolling", "v2_1", 3, window=5, llm=RunnableLambda(with_usage))
    l = logs[-1]
    assert l["Token_Count_Method"] == "provider" and l["Context_Tokens"] == 5000
    assert l["Offset_Count_Method"] == "tokenizer:o200k_base*provider_scale"
    assert l["Token_Scale"] == pytest.approx(5000 / l["Context_Tokens_Tokenizer"], rel=0, abs=1e-12)
    assert l["Mandate_Offset_Tokens"] == min(l["Mandate_Offset_System"], l["Mandate_Offset_Injected"])
    _, logs2, _, _ = _roll(obs, "mandate", "rolling", "v2_1", 3, window=5)
    assert logs2[-1]["Token_Count_Method"] == "tokenizer:o200k_base" and logs2[-1]["Token_Scale"] is None
    assert logs2[-1]["Context_Tokens"] == logs2[-1]["Context_Tokens_Tokenizer"]


# ================================================================================================ E8.1 (e)
# The registered clause segmentation and annotation, PREREG_PHASE_8.md 1.6 (I = imperative)
_WRAP_M = [("Strictly adhere to your core mandate", 1)]
_CLOSE_M = [("Evaluate this trade ONLY through the lens of this mandate", 1)]
REGISTERED = {
    "ENTJ": _WRAP_M + [("REMINDER", 0), ("You are a MOMENTUM COMMANDER", 0), ("Your goal is GROWTH", 0), ("Be decisive", 1),
                       ("BUY", 1), ("SELL", 1), ("Do not hesitate", 1), ("Ignore small losses", 1),
                       ("CHASE THE BIG WINS", 1)] + _CLOSE_M,
    "ISFJ": _WRAP_M + [("REMINDER", 0), ("You are a GUARDIAN INVESTOR", 0), ("Your goal is SECURITY", 0),
                       ("Protect the principal", 1), ("Avoid volatility", 1),
                       ("Keep a large cash cushion instead of insurance products", 1), ("Do not take unnecessary risks", 1),
                       ("SLEEP WELL AT NIGHT", 1)] + _CLOSE_M,
    "INTJ": _WRAP_M + [("REMINDER", 0), ("You are a SYSTEM ARCHITECT", 0), ("Your goal is ALPHA", 0), ("Trust the model", 1),
                       ("Ignore the news cycle", 1), ("Plan the exit before the entry", 1), ("The market is a puzzle", 0),
                       ("SOLVE IT", 1)] + _CLOSE_M,
    "placebo_v2": [("Strictly adhere to your core procedure", 1), ("REMINDER", 0), ("You are a DILIGENT RECORD-KEEPER", 0),
                   ("Your goal is CLARITY", 0), ("Write your rationale in full sentences", 1), ("State the date first", 1),
                   ("Use plain language", 1), ("Do not use abbreviations", 1), ("KEEP IT CLEAR", 1),
                   ("Write this decision ONLY in the manner of this procedure", 1)],
}


def test_placebo_matching():
    """E8.1(e), weakness 60: the registered clause lists are what the rendered texts segment into; the v2 placebo
    matches ISFJ only (7 = 7) and misses ENTJ (8) and INTJ (6) on imperatives -- recorded as measured; the word
    criterion holds for all three (the pre-registered expectation that INTJ was at risk is disconfirmed: 49 = 49);
    the matched v2_1 placebo meets both criteria for all three using only the registered operations."""
    from agent import prompt_matching as PM
    from agent import v2_prompts as P
    for p in ("ENTJ", "ISFJ", "INTJ"):
        real = P.mandate_block("mandate", p, "rewritten")
        assert PM.clauses(real) == [c for c, _ in REGISTERED[p]], f"{p}: the rendered mandate no longer segments as registered"
        assert PM.imperatives(real) == sum(i for _, i in REGISTERED[p])
    plac = P.mandate_block("placebo_directive", "ISFJ", "rewritten")
    assert PM.clauses(plac) == [c for c, _ in REGISTERED["placebo_v2"]]
    assert PM.imperatives(plac) == 7
    v2 = {p: PM.matching(P.mandate_block("mandate", p, "rewritten"), P.mandate_block("placebo_directive", p, "rewritten"))
          for p in ("ENTJ", "ISFJ", "INTJ")}
    assert {p: r["imperatives_pass"] for p, r in v2.items()} == {"ENTJ": False, "ISFJ": True, "INTJ": False}
    assert all(r["words_pass"] for r in v2.values())
    for p in ("ENTJ", "ISFJ", "INTJ"):
        m = P.mandate_block("placebo_directive", p, "rewritten", "v2_1")
        r = PM.matching(P.mandate_block("mandate", p, "rewritten"), m)
        assert r["pass"], f"{p}: the matched placebo fails {r}"
        extra = set(PM.clauses(m)) - {c for c, _ in REGISTERED["placebo_v2"]}
        missing = {c for c, _ in REGISTERED["placebo_v2"]} - set(PM.clauses(m))
        assert extra <= {c.rstrip(".") for c in PM.ADD_ORDER} and missing <= {c.rstrip(".") for c in PM.REMOVE_ORDER}
    with pytest.raises(PM.UnannotatedClause):
        PM.imperatives("Buy the dip.")
    f = os.path.join(GEN, "e8_1", "placebo_matching.json")
    if os.path.exists(f):
        doc = json.load(open(f, encoding="utf-8"))
        assert doc["v2_pass_count"] == 1 and doc["v2_1_pass_count"] == 3


def test_placebo_version_switch_inert():
    """`placebo_version="v2"` is the published placebo for every persona; an unknown version raises."""
    from agent import v2_prompts as P
    lit = ("*** ACTIVE MEMORY REFRESH ***\nStrictly adhere to your core procedure:\n" + P.PLACEBO_DIRECTIVE +
           "\n\nWrite this decision ONLY in the manner of this procedure.")
    for p in ("ENTJ", "ISFJ", "INTJ", "O1_conservative"):
        assert P.mandate_block("placebo_directive", p) == lit
    with pytest.raises(ValueError):
        P.mandate_block("placebo_directive", "ISFJ", "rewritten", "v3")


# ================================================================================================ E8.2
def test_context_levels_registered():
    """E8.2, weakness 28: the context-length factor {5, 20, 50, full} exists in the registry, the 50 level is new, and
    every stateful arm keeps the mandate in the system prompt."""
    from experiments.arms_v2 import ARMS, CONTEXT_LEVELS, build_config
    assert set(CONTEXT_LEVELS) == {5, 20, 50, "full"}
    for level, arms in CONTEXT_LEVELS.items():
        for arm in arms:
            cfg = build_config("fake", "ISFJ", arm, "flat", 1)
            assert cfg.mandate_in_system
            if level == "full":
                assert cfg.context_mode == "full" and cfg.context_token_budget == 60000
            else:
                assert cfg.context_mode == "rolling" and cfg.context_window == level
        assert ARMS[arms[0]]["mandate_block"] == "none" and ARMS[arms[1]]["mandate_block"] == "mandate"
    assert build_config("fake", "ISFJ", "stateful_w50_memory", "flat", 1).harness_version == "v2"


# ================================================================================================ E8.5 set-up
def test_e8_5_design_registered():
    """PREREG 5.1: the design in the tool is the registered one (576 + 144 runs, seeds 2001-2008, dividends paid,
    crash at 0.70), and the launch manifest -- once written -- agrees with it."""
    from tools.phase8 import e8_5_variance_pilot as E
    m_main, c_main = E.design("main")
    m_tr, c_tr = E.design("transfer")
    assert (m_main, len(c_main), m_tr, len(c_tr)) == ("gemini-2.5-flash", 576, "gpt-5-mini", 144)
    assert E.SEEDS == tuple(range(2001, 2009)) and E.REPS == 3 and E.T == 200
    cfg = E.cfg_for(m_main, ("ISFJ", "memory", "crash", 2001, 2))
    assert cfg.dividends and cfg.crash_discount == 0.70 and cfg.temperature == 0.2 and cfg.start_design == "target"
    assert E.cfg_for(m_tr, ("ISFJ", "memory", "bull_trap", 2001, 2)).temperature == 1.0
    # P8-8: Flash with thinking off, in its own configuration directory; the gate re-set by the 125 % rule
    assert E.THINKING_BUDGET == {"gemini-2.5-flash": 0, "gpt-5-mini": None}
    assert (E.APPROVED_USD, E.GATE_USD) == (151.0, 189.0) and abs(E.GATE_USD - 1.25 * E.APPROVED_USD) < 0.5
    assert "thinking0" in E.run_paths(cfg)["csv"] and "thinking0" in E.checkpoint_path(m_main)
    mp = E.manifest_path()
    if os.path.exists(mp):
        man = json.load(open(mp, encoding="utf-8"))
        assert man["seeds"] == list(E.SEEDS) and man["design"]["main"]["n_runs"] == 576
        if "thinking_budget" in man:
            assert man["gate_usd"] == 189.0 and man["thinking_budget"]["gemini-2.5-flash"] == 0


def test_e8_5_llm_matches_factory(monkeypatch):
    """The runner's client differs from `agent.llm_factory.make_llm` only in its retry count; and the silent drop of
    temperature 0.2 for gpt-5 models, which is why the transfer check is configured and logged at 1.0, is asserted."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from agent.llm_factory import make_llm
    from tools.phase8.e8_5_variance_pilot import make_llm_with_retries
    for model, temp in (("gemini-2.5-flash", 0.2), ("gpt-5-mini", 1.0)):
        a, b = make_llm(model, temp), make_llm_with_retries(model, temp)
        assert type(a) is type(b) and b.max_retries == 8
        assert getattr(a, "model", None) == getattr(b, "model", None) or getattr(a, "model_name", None) == getattr(b, "model_name", None)
        assert a.temperature == b.temperature
    # P8-8: the factory never set a thinking budget (the pilot ran the provider default); E8.5's Flash client sets 0
    assert getattr(make_llm("gemini-2.5-flash", 0.2), "thinking_budget", None) is None
    assert make_llm_with_retries("gemini-2.5-flash", 0.2, thinking_budget=0).thinking_budget == 0
    assert make_llm("gpt-5-mini", 0.2).temperature is None, "langchain_openai no longer drops temperature for gpt-5"


def test_e8_5_power_formulas():
    """PREREG 5.5 / P8-1: the arithmetic the main grid is sized with, against hand-computed values -- Appendix A as
    written (factor 2) and the paired-correct form, the minimum detectable difference at the sized design, and the
    plug-in decomposition on a frame whose answer is known exactly."""
    import math
    import pandas as pd
    from scipy import stats
    from tools.phase8.e8_5_analyse import mdd, n_seeds, plug_ins
    z2 = (stats.norm.ppf(0.975) + stats.norm.ppf(0.80)) ** 2            # 7.8489
    assert z2 == pytest.approx(7.8489, abs=1e-4)
    assert n_seeds(0.05, 0.05, 0.05) == math.ceil(2 * z2) == 16
    assert n_seeds(0.05, 0.05, 0.05, factor2=False) == math.ceil(z2) == 8
    for sigma, alpha in ((0.05, 0.05), (0.08, 0.05 / 36)):
        n = n_seeds(sigma, 0.05, alpha)
        assert mdd(sigma, n, alpha) <= 0.05 + 1e-12 < mdd(sigma, n - 1, alpha)
    # a frame with NO replicate noise: every replicate equal, so sigma2_rep = 0 and all paired variance is seed x arm
    rows = []
    rng = np.random.default_rng(1)
    for p in ("ISFJ", "ENTJ"):
        for sc in ("flat", "crash"):
            for s in range(6):
                d = rng.normal(0, 0.03)
                for arm, v in (("static", 0.2), ("memory", 0.2 + 0.05 + d)):
                    for r in range(3):
                        rows.append({"Persona": p, "Arm": arm, "Scenario": sc, "Seed": s, "Decode_Replicate": r, "y": v})
    q = plug_ins(pd.DataFrame(rows), "y")
    assert q["sigma2_rep"] == pytest.approx(0.0, abs=1e-15)
    assert q["sigma2_int"] == pytest.approx(q["sigma_d_R"] ** 2, abs=1e-15)
    assert q["sigma_d_R1"] == pytest.approx(q["sigma_d_R3"], abs=1e-12) and q["n_pairs"] == 2 * 2 * 6


def test_transfer_ratios_fast_equals_loop():
    """Rule 18: the transfer bootstrap in array form gives the loop's ratios from the same shared seed resamples, and
    an incomplete frame falls back to the loop exactly."""
    import pandas as pd
    from tools.phase8 import e8_5_analyse as A
    from tools.phase8.e8_5_validate import simulate
    frames = [simulate(np.random.default_rng(seed), 0.03, 0.04).query("Scenario == 'bull_trap'").assign(Model=model)
              for model, seed in ((A.E.MAIN_MODEL, 1), (A.E.TRANSFER_MODEL, 2))]
    bt = pd.concat(frames, ignore_index=True)
    _, picks = A._transfer_picks(bt, np.random.default_rng(0), 30)
    loop, fast = A.transfer_ratios_loop(bt, "y", picks), A.transfer_ratios_fast(bt, "y", picks)
    assert np.allclose(loop, fast, rtol=1e-12, atol=1e-15)
    part = bt.iloc[1:]
    assert np.array_equal(A.transfer_ratios_loop(part, "y", picks[:5]), A.transfer_ratios_fast(part, "y", picks[:5]),
                          equal_nan=True)


def test_mls_limit_reduces_to_chi_square():
    """The closed-form upper limit for sigma_d(R') equals the chi-square limit MS_d df_d / chi2_{0.10}(df_d) at R' = R,
    grows as R' falls below R (more replicate variance per pair), and refuses a negative combination (R' > R)."""
    import math
    from scipy import stats
    from tools.phase8.e8_5_analyse import mls_ucl_sigma_d
    ms_d, df_d, ms_rep, df_rep = 0.0026, 84, 0.0016, 384
    chi = math.sqrt(ms_d * df_d / stats.chi2.ppf(0.10, df_d))
    assert mls_ucl_sigma_d(ms_d, df_d, ms_rep, df_rep, 3.0, 3) == pytest.approx(chi, rel=1e-12)
    u1, u2, u3 = (mls_ucl_sigma_d(ms_d, df_d, ms_rep, df_rep, 3.0, r) for r in (1, 2, 3))
    assert u1 > u2 > u3 > math.sqrt(ms_d)
    assert math.isnan(mls_ucl_sigma_d(ms_d, df_d, ms_rep, df_rep, 3.0, 4))


def test_boot_plug_ins_fast_equals_loop():
    """Rule 18: the array form of the path bootstrap gives the loop's numbers from the same generator -- on E8.5-shaped
    frames with seed x arm and replicate noise, including a scenario whose seed labels differ -- and an incomplete
    design falls back to the loop exactly."""
    import pandas as pd
    from tools.phase8.e8_5_analyse import boot_plug_ins, boot_plug_ins_fast
    from tools.phase8.e8_5_validate import simulate
    for k, (s_int, s_rep) in enumerate(((0.03, 0.04), (0.0, 0.05), (0.05, 0.02))):
        t = simulate(np.random.default_rng([7, k]), s_int, s_rep)
        t.loc[t["Scenario"] == "crash", "Seed"] += 100            # seed labels need not be shared across scenarios
        a = boot_plug_ins(t, "y", np.random.default_rng(k), n_boot=40)
        b = boot_plug_ins_fast(t, "y", np.random.default_rng(k), n_boot=40)
        assert a.keys() == b.keys()
        for key in a:
            assert b[key] == pytest.approx(a[key], rel=1e-12, abs=1e-15), key
    t = simulate(np.random.default_rng(9), 0.03, 0.04).iloc[1:]      # one run missing: not balanced
    a = boot_plug_ins(t, "y", np.random.default_rng(3), n_boot=10)
    b = boot_plug_ins_fast(t, "y", np.random.default_rng(3), n_boot=10)
    assert a == b


def test_runner_meta_with_live_client(tmp_path):
    """E8.5's smoke found a latent runner defect: the meta write used `dataclasses.asdict(cfg)`, which deep-copies
    every field -- including an injected client -- before dropping it.  A real provider client holds a thread lock, so
    every run with an injected client completed its 200 decisions, wrote its CSV, and failed on `meta.json`.  The meta
    is now built field by field; for a run without a client the JSON equals the asdict construction."""
    import copy
    import threading
    from dataclasses import asdict, replace
    from experiments.arms_v2 import build_config
    from simulation.runner_v2 import run_simulation_v2
    from tools.phase8.e8_0_golden import fake_llm
    locked = fake_llm([]).with_config(metadata={"lock": threading.RLock()})      # like a live client
    with pytest.raises(TypeError):
        copy.deepcopy(locked)
    cfg = build_config("fake", "ISFJ", "memory", "flat", 3, T=12, output_dir=str(tmp_path), dividends=True)
    df = run_simulation_v2(replace(cfg, agent_llm=locked), verbose=False)
    assert df is not None and len(df) == 12
    meta_path = os.path.join(str(tmp_path), "fake", "flat", "seed3", cfg.run_id() + ".meta.json")
    meta = json.load(open(meta_path, encoding="utf-8"))
    old = json.loads(json.dumps({k: v for k, v in asdict(replace(cfg, agent_llm=None)).items() if k != "agent_llm"}, default=str))
    assert meta["run_config"] == old


def test_l3_keeps_text_parts_only(tmp_path, monkeypatch):
    """P8-12 (iii): a model that thinks by default returns a thinking block (with a long signature) before its answer;
    the L3 probe must store the text parts only, so the 500-character cut can never remove the answer.  Before the fix
    17 of Sonnet 5's first 146 answers lost their word."""
    import pandas as pd
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda
    import agent.llm_factory as LF
    from tools.phase6 import e6_l3_probe as L3
    reply = AIMessage(content=[{"type": "thinking", "thinking": "", "signature": "E" * 900},
                               {"type": "text", "text": "UNDERVALUED"}])
    monkeypatch.setattr(LF, "make_llm", lambda model, temperature=0.0: RunnableLambda(lambda p: reply))
    out = tmp_path / "answers.csv"
    ans = L3.ask("fake-model", ["probe one", "probe two"], str(out))
    assert list(ans["raw"]) == ["UNDERVALUED", "UNDERVALUED"]
    assert [L3.parse(r) for r in ans["raw"]] == [-1, -1]
    assert "signature" not in pd.read_csv(out)["raw"].str.cat()


def test_inference_params_readable():
    """PREREG 6: `experiments/params/inference.json` loads through its loud loader, and every adopted rule in it is the
    one its result file gives by the registered adoption rule (a rule typed into the file would fail here)."""
    from experiments import inference_params as IP
    if not IP.PRESENT:
        pytest.skip("experiments/params/inference.json not written in this tree")
    doc = IP.load()
    mult = _need_gen("e8_3/multiplicity.json")
    holds = lambda grid, proc: all(r["fdr_holds"] for r in mult["table"] if r["grid"] == grid and r["procedure"] == proc)
    assert IP.decision_rule(1) == ("bh_within" if holds("e8_5", "bh_within") else "by_across")
    assert IP.decision_rule(4) == ("bh_within" if holds("reviewer", "bh_within") else "by_across")
    null = _need_gen("e8_3/null.json")
    at_pilot = [r for r in null["table"] if r["phi_is_pilot"]]
    adopted = sorted({r["null"] for r in at_pilot} - {r["null"] for r in at_pilot if not r["size_holds"]})
    assert doc["temporal_null"]["value"]["adopted"] == adopted
    assert doc["temporal_null"]["value"]["sign_flip_min_pairs_for_p_below_alpha"] == 6
    assert doc["min_effect"]["value"]["band_mas"] == 0.05 and doc["min_effect"]["status"] == "TEAM"
    pp = _need_gen("e8_3/mixed_pp.json")                            # P8-17: the mixed model's role is addendum 17's outcome
    assert doc["mixed_model"]["value"]["decides_claims"] == bool(pp["adopt_e1_amended"])
    assert doc["mixed_model"]["value"]["optimizer"].startswith("best")
    sizing = doc["main_grid_sizing"]["value"]                       # P8-16: the seed counts are the files' own
    assert sizing["seeds_per_persona_scenario_cell"] == _need_gen("e8_5/transfer.json")["band_mas_plugin"]["seeds_appA_bonf_main_grid"]
    assert sizing["flash_only_seeds"] == _need_gen("e8_5/power.json")["sized_band_mas"]["1"]["appA_bonf"]
    assert IP.SHA256 == IP.file_sha256()
    with pytest.raises(IP.InferenceParamsError):
        IP.decision_rule(0)


def test_harness_params_match_code():
    """PREREG 6: `agent/params/harness.json` is readable through its loud loader and says what the code does."""
    import inspect
    from agent import harness_params as HP
    if not HP.PRESENT:
        pytest.skip("agent/params/harness.json not written in this tree")
    doc = HP.load()
    from agent.stateful_agent import FALLBACK_HISTORY_TEXT, StatefulV2Agent
    from experiments.arms_v2 import CONTEXT_LEVELS, FACTOR_DEFAULTS
    sig = inspect.signature(StatefulV2Agent.__init__).parameters
    assert doc["context_window_default"]["value"] == sig["window"].default
    assert doc["token_budget"]["value"] == sig["token_budget"].default
    assert doc["summary_every"]["value"] == sig["summary_every"].default
    assert doc["summary_raw_turns"]["value"] == sig["summary_raw_turns"].default
    assert doc["default_harness_version"]["value"] == sig["harness"].default == "v2"
    assert doc["fallback_history_text"]["value"] == FALLBACK_HISTORY_TEXT
    assert doc["decode_temperature"]["value"] == FACTOR_DEFAULTS["temperature"]
    assert doc["context_window_levels"]["value"] == json.loads(json.dumps(list(CONTEXT_LEVELS)))
    assert doc["placebo_matching"]["value"]["v2_pass"] == 1 and doc["placebo_matching"]["value"]["v2_1_pass"] == 3
    assert HP.SHA256 == HP.file_sha256()


# ================================================================================================ E8.3
def _need_gen(rel):
    if not os.path.exists(os.path.join(GEN, rel)):
        pytest.skip(f"{rel} not generated in this working tree")
    return json.load(open(os.path.join(GEN, rel), encoding="utf-8"))


def test_stats_v21_matches_simulation():
    """Rule 13: stats_v2's crossed model and two-way bootstrap ARE the estimators the simulation validated (E1, E2) --
    same coefficient, p and variance components; same interval from the same draws."""
    _need_gen("e8_3/paths.json")
    from tools import stats_v2 as S
    from tools.phase8 import e8_3_simulate as SIM
    d = SIM.simulate(np.random.default_rng(3), 6, 5, 1, 0.05, 0.03, 0.0, SIM._paths())
    e1 = SIM.fit_e1(d)
    r = S.crossed_mixed_model(d, "y")
    term = "C(Arm, Treatment('static'))[T.memory]"
    row = r["fixed"].set_index("term").loc[term]
    assert row["coef"] == pytest.approx(e1["e1_coef"], abs=1e-10) and row["p"] == pytest.approx(e1["e1_p"], abs=1e-8)
    for k, v in r["variance_components"].items():
        assert v == pytest.approx(e1[f"e1_vc_{k}"], abs=1e-10)
    pairs = S.seed_level_pairs(d, "y", "memory", "static")
    pairs = pairs[(pairs.Persona == "ENTJ") & (pairs.Scenario_Cell == "bull_trap")]
    m, lo, hi = SIM.e2_pigeonhole(SIM.paired_cell(d), np.random.default_rng([9, 0]))
    b = S.pigeonhole_ci(pairs, rng=np.random.default_rng([9, 0]))
    assert (b["estimate"], b["ci_lo"], b["ci_hi"]) == pytest.approx((m, lo, hi), abs=1e-12)


def test_crossed_mixed_model_best_optimizer():
    """Addendum 17 / P8-17: `optimizer="best"` IS the simulation's E1-best (lbfgs and Powell, the higher REML likelihood
    kept) and never ends below lbfgs's likelihood; the default stays the lbfgs estimator P8-9 validated
    (`test_stats_v21_matches_simulation`); an unknown optimizer is refused, not silently replaced."""
    _need_gen("e8_3/paths.json")
    from tools import stats_v2 as S
    from tools.phase8 import e8_3_simulate as SIM
    d = SIM.simulate(np.random.default_rng(3), 6, 5, 1, 0.05, 0.03, 0.0, SIM._paths())
    e1b = SIM.fit_e1_best(d)
    best = S.crossed_mixed_model(d, "y", optimizer="best")
    default = S.crossed_mixed_model(d, "y")
    term = "C(Arm, Treatment('static'))[T.memory]"
    row = best["fixed"].set_index("term").loc[term]
    assert row["coef"] == pytest.approx(e1b["e1b_coef"], abs=1e-10) and row["p"] == pytest.approx(e1b["e1b_p"], abs=1e-8)
    assert best["optimizer"] == "best" and default["optimizer"] == "lbfgs"
    assert best["reml_llf"] >= default["reml_llf"] - 1e-9
    with pytest.raises(ValueError):
        S.crossed_mixed_model(d, "y", optimizer="newton")


def test_mixed_model_crossed():
    """Plan 12.4: the crossed model recovers a planted crossed structure.  Read from the simulation: in E1's own
    parameterisation (M = 12, S = 20) every planted component lies inside the 5th-95th percentile band of E1's
    estimates over its datasets (a derived band, not a typed tolerance); stats_v2's function reproduces the cached
    estimate of dataset 0 exactly; and the v2 model has no model x arm component at all."""
    import inspect
    band = _need_gen("e8_3/recovery_band.json")
    for k, b in band["band"].items():
        assert b["planted_inside_p05_p95"], f"{k}: planted {b['planted']} outside [{b['p05']}, {b['p95']}]"
    from tools import stats_v2 as S
    from tools.phase8 import e8_3_simulate as SIM
    import pandas as pd
    c = SIM.RECOVERY
    d = SIM.simulate(np.random.default_rng([8, 12, 0]), c["M"], c["S"], c["R"], c["beta"], c["s_ma"], 0.0, SIM._paths(),
                     gaussian_paths=c["s_path"], interaction=True, s_m=c["s_m"], s_eps=c["s_eps"])
    cached = pd.read_csv(os.path.join(GEN, "e8_3", "_cache", "recovery.csv")).set_index("i").loc[0]
    r = S.crossed_mixed_model(d, "y")
    for k in ("model", "model_arm", "path"):
        assert r["variance_components"][k] == pytest.approx(cached[f"e1_vc_{k}"], abs=1e-10)
    assert "C(Model):C(Arm)" not in inspect.getsource(S.mixed_effects)


def test_bh_family_size_logged():
    """Plan 12.4: every q-value carries the size of the family it was adjusted in, counted from the tests computed; BY
    across families is computed beside BH within; the v2 count function reproduces weakness 59's "roughly 840"."""
    import pandas as pd
    from tools import stats_v2 as S
    rng = np.random.default_rng(5)
    rows = []
    for mdl in ("m0", "m1"):
        for p in ("ISFJ", "ENTJ"):
            for sc in ("flat", "bull_trap"):
                for seed in range(4):
                    for arm in ("static", "memory", "placebo_directive", "swapped"):
                        rows.append({"Model": mdl, "Persona": p, "Arm": arm, "Scenario": sc, "Seed": seed, "Decode_Replicate": 0,
                                     "band_mas": rng.random(), "v21_mcr_D_0.05": rng.random(), "v21_mcr_D_0.002": rng.random(),
                                     "turnover": rng.random(), "mdd_pct": -rng.random(), "return_pct": rng.normal()})
    t = S.run_stats_v21(pd.DataFrame(rows), os.path.join(os.path.dirname(__file__), "_tmp_phase8_stats"), n_boot=199)
    con, fam = t["contrasts"], t["families"]
    for f, g in con.groupby("family"):
        assert (g["m_family"] == len(g)).all(), f"{f}: the logged family size is not the number of its tests"
    assert set(con["question"]) == {"Q1", "Q2", "Q3"}
    assert con["q_bh_within_family"].notna().all() and con["q_by_across_families"].notna().all()
    assert (con["q_by_across_families"] >= con["q_bh_within_family"] - 1e-12).all()
    assert int(fam["m"].sum()) == len(con)
    assert S.v2_family_count(8, 3, 5) == 840
    for ext in ("_v21_contrasts.csv", "_v21_families.csv", "_v21_variance_components.csv"):
        os.remove(os.path.join(os.path.dirname(__file__), "_tmp_phase8_stats" + ext))


def test_path_sign_flip_exact():
    """N3: exact over 2^n sign vectors; the smallest attainable p is 2 / 2^n, so 3 paths can never reject at 0.05 and 6
    can (the simulated size at 3 runs, 0.000, is this floor)."""
    import pandas as pd
    from tools import stats_v2 as S
    for n, floor in ((3, 0.25), (6, 0.03125)):
        pairs = pd.DataFrame({"Path": [f"p{i}" for i in range(n)], "d": np.full(n, 1.0)})
        r = S.path_sign_flip(pairs)
        assert r["exact"] and r["min_attainable_p"] == floor and r["p_signflip"] == pytest.approx(floor)


# ================================================================================================ E8.4
def _ident_frame(start: str, with_refs: bool):
    """Run-level rows of a design (the check reads one row per run)."""
    import pandas as pd
    from evaluation.targets import centre
    rows = []
    cells = [(p, a, mb, ("ENTJ" if (a == "swapped" and p == "ISFJ") else ("ISFJ" if a == "swapped" else p)))
             for p in ("ISFJ", "INTJ", "ENTJ") for a, mb in (("static", "none"), ("memory", "mandate"))
             + ((("swapped", "mandate"),) if with_refs else ())]
    if with_refs:
        cells += [(p, "static", "none", p) for p in ("NONE", "O3_conservative")]
    for p, arm, mb, mp in cells:
        for s in range(3):
            c0 = 0.5 if start == "common" else (0.5 if p in ("NONE", "O3_conservative") else centre(p))
            rows.append({"Model": "m", "Persona": p, "Arm": arm, "Mandate_Block": mb, "Mandate_Persona": mp, "Seed": s,
                         "Decode_Replicate": 0, "Start_Design": start, "Start_Cash_Share": c0, "Day": 1})
    return pd.DataFrame(rows)


def test_salience_common_start_only():
    """E8.4, weakness 55: under start-at-target the start block is in the span of the persona block, so the shares are
    NOT IDENTIFIED and `salience_by_window(identification="v2_1")` returns that verdict with the failing clauses and no
    share; a common-start design with the reference levels passes all four clauses; a common-start design without them
    fails clause (iv).  The v2 default is untouched (the golden record)."""
    from evaluation.salience import identification_check, salience_by_window
    target = identification_check(_ident_frame("target", with_refs=False))
    assert not target["identified"] and not target["identified_as_registered"]
    assert "ii_no_block_in_span_of_others" in target["failing_clauses"] and "iii_common_start" in target["failing_clauses"]
    assert target["r2_block_on_others"]["start"] == pytest.approx(1.0, abs=1e-9)
    assert target["max_canonical_corr"]["persona~start"] == pytest.approx(1.0, abs=1e-9)
    no_refs = identification_check(_ident_frame("common", with_refs=False))
    assert not no_refs["identified"] and "iv_reference_levels_present" in no_refs["failing_clauses"]
    ok = identification_check(_ident_frame("common", with_refs=True))
    assert ok["identified"], ok["failing_clauses"]
    # addendum 10: as registered, clause (i) also asked the start block to vary, which a common start forbids -- so the
    # registered verdict is NO for every design, and the start share is "not applicable" at common start
    assert not ok["identified_as_registered"] and ok["failing_clauses_as_registered"] == ["i_every_block_varies"]
    assert ok["ranks"]["start"] == 0 and not ok["start_share_applicable"]
    frame = _ident_frame("target", with_refs=False)
    out = salience_by_window(frame, identification="v2_1")
    assert (out["status"] == "NOT IDENTIFIED").all() and "S_persona" not in out.columns
    with pytest.raises(ValueError):
        salience_by_window(frame, identification="v3")


def test_identification_counts_runs_per_scenario():
    """A run is (model, persona, arm, scenario, crash discount, start design, seed, replicate): the pilot reused one
    seed across three scenarios, and counting runs without the scenario collapsed three runs into one."""
    import pandas as pd
    from evaluation.salience import identification_check
    one = _ident_frame("target", with_refs=False)
    three = pd.concat([one.assign(Scenario=sc) for sc in ("flat", "bull_trap", "crash")], ignore_index=True)
    assert identification_check(three)["n_runs"] == 3 * identification_check(one.assign(Scenario="flat"))["n_runs"]


def test_salience_bootstrap_parallel_equals_sequential():
    """Rule 18's spirit for a parallelised statistic: the seed-cluster bootstrap's refits in a process pool give the draws
    the sequential loop gives -- every resample is drawn up front in loop order and every refit carries its own seed."""
    import pandas as pd
    from evaluation import salience as S
    from tools.phase8.e8_4_salience import frame
    d = frame("B_common_start_with_references", np.random.default_rng(84))
    dw = d[(d.Day >= 1) & (d.Day < 26)]
    kw = dict(n_estimators=10, n_repeats=2)
    a = S._bootstrap_shares(dw, False, 3, 0, n_jobs=1, **kw)
    b = S._bootstrap_shares(dw, False, 3, 0, n_jobs=2, **kw)
    for k in a:
        for x, y in zip(a[k], b[k]):
            assert (np.isnan(x) and np.isnan(y)) or x == pytest.approx(y, abs=1e-12), k


def test_salience_bootstrap_copies_share_a_fold(monkeypatch):
    """Addendum 18: a seed drawn twice must fall in one cross-validation fold.  Relabelled copies in different folds put
    identical rows in train and test (measured on the known answer: S_directive 0.00094 against 0.000019, OOF R2 0.979
    against 0.968, median of 12 refits)."""
    from sklearn.model_selection import GroupKFold
    from evaluation import salience as S
    from tools.phase8.e8_4_salience import frame
    d = frame("B_common_start_with_references", np.random.default_rng(84))
    dw = d[(d.Day >= 1) & (d.Day < 26)]
    s = sorted(dw["Seed"].unique())
    pick = np.array([s[0], s[0], s[1], s[2], s[2], s[2], s[3], s[-1], s[-1]], dtype=object)   # seeds drawn 1-3 times
    b = S._boot_frame(dw, pick)
    assert b["Seed"].nunique() == len(pick)                              # copies stay distinct runs
    assert set(b["Boot_Group"]) == set(pick)                             # grouped by the original seed
    groups = b["Boot_Group"].to_numpy(dtype=object)
    original = b["Seed"].str.split("#").str[0].to_numpy(dtype=object)
    for tr, te in GroupKFold(n_splits=min(5, len(set(pick)))).split(b, groups=groups):
        assert not set(original[tr]) & set(original[te]), "a seed's copies sit in both train and test"
    seen = {}

    def spy(runs, **kw):
        seen.update(kw)
        seen["groups"] = runs[kw.get("groups_col", "Seed")].to_numpy(dtype=object)
        return {k: 0.0 for k in S._SHARE_KEYS}

    monkeypatch.setattr(S, "surrogate_shares", spy)
    S._boot_refit((dw, False, pick, 0, {}))
    assert seen["groups_col"] == "Boot_Group" and set(seen["groups"]) == set(pick)


def test_power_t_two_sided_matches_nct():
    """P8-2's model-level DESIGN table: the integral form equals scipy's noncentral t wherever that is finite, and is
    finite where scipy returned NaN (df 7, ncp 6.77 -- the M = 8, tau/sigma = 0.5 row)."""
    from scipy import stats
    from tools.phase8.e8_5_analyse import power_t_two_sided
    checked = 0
    # (1, 3.39, alpha') is the M = 2 row: tcrit ~ 458, every bit of the mass at chi-square values below 6e-5
    for df, ncp, a in ((1, 1.5, 0.05), (1, 3.39, 0.05 / 36), (2, 3.0, 0.05 / 36), (4, 3.0, 0.05 / 36), (7, 2.2, 0.05 / 36),
                       (20, 4.0, 0.01), (2, 0.5, 0.05)):
        c = stats.t.ppf(1 - a / 2, df)
        ref = 1 - stats.nct.cdf(c, df, ncp) + stats.nct.cdf(-c, df, ncp)
        if np.isfinite(ref):
            assert power_t_two_sided(c, df, ncp) == pytest.approx(ref, rel=1e-4, abs=1e-7), (df, ncp, a)
            checked += 1
    assert checked >= 5
    # where scipy returns NaN, a seeded Monte Carlo is the reference (2e6 draws: standard error < 3e-4)
    c = stats.t.ppf(1 - 0.05 / 36 / 2, 7)
    v = power_t_two_sided(c, 7, 6.77)
    rng = np.random.default_rng(20260911)
    t = (rng.standard_normal(2_000_000) + 6.77) / np.sqrt(rng.chisquare(7, 2_000_000) / 7)
    assert np.isfinite(v) and v == pytest.approx(float(np.mean(np.abs(t) > c)), abs=0.002)


def test_phase8_report_tables_match_files():
    """Rule 15: every PHASE_8_REPORT.md table is generated from its file and read back (`--check` exits 1 when stale)."""
    report = os.path.join(ROOT, "docs", "env_v2", "v2_1", "PHASE_8_REPORT.md")
    if not os.path.exists(report):
        pytest.skip("PHASE_8_REPORT.md not written yet")
    from tools.phase8.e8_report_tables import main as rt
    assert rt(["--check"]) == 0, "a PHASE_8_REPORT.md table differs from the file it is generated from"


# ================================================================================================ the switches
def test_phase8_switches_inert():
    """PREREG 7: every Phase-8 switch at its default reproduces the golden record captured from the unmodified code
    (the stateful agent in every mode and a forced fallback, every prompt block, every arm's config and prompt hash,
    stats_v2 and salience on fixed frames)."""
    from tools.phase8.e8_0_golden import main as golden
    assert golden(["--check"]) == 0, "a Phase-8 default no longer reproduces the pre-Phase-8 behaviour"
