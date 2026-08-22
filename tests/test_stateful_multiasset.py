"""
E5 stateful arm and the 3-asset configuration, offline (fake LLM).
"""
import json

import numpy as np
import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from agent.stateful_agent import StatefulV2Agent
from experiments.arms_v2 import build_config, THREE_ASSET, ARMS
from simulation.runner_v2 import run_simulation_v2


def fake_chat(target=0.4, weights=None):
    def _run(messages):
        text = "\n".join(m.content for m in messages) if isinstance(messages, list) else str(messages)
        if "Do not trade now" in text:
            return AIMessage(content="restated")
        payload = {"target_cash_share": target, "rationale": "t"}
        if weights is not None:
            payload["target_weights"] = weights
        return AIMessage(content=json.dumps(payload))
    return RunnableLambda(_run)


def test_stateful_context_grows_then_plateaus():
    a = StatefulV2Agent("ISFJ", "fake", mandate_block="none", context_mode="rolling", window=5, llm=fake_chat())
    assert "CORE MANDATE." in a.full_system_prompt          # Path B: mandate at t = 0
    obs = {"date": "Day-1", "price": 100.0, "SMA20": 100.0, "SMA50": 100.0, "RSI14": 50.0}
    toks, offs, turns = [], [], []
    for d in range(1, 10):
        obs["date"] = f"Day-{d}"
        a.decide(obs, {"cash": 5000.0, "holdings_value": 5000.0, "cash_share": 0.5})
        toks.append(a.last_context_tokens); offs.append(a.last_mandate_offset); turns.append(a.last_n_turns)
    assert turns == [0, 1, 2, 3, 4, 5, 5, 5, 5]
    assert toks[5] > toks[0] and abs(toks[8] - toks[5]) < 0.2 * toks[5]   # grows, then plateaus
    assert offs[5] > offs[0] and all(o > 0 for o in offs)
    b = StatefulV2Agent("ISFJ", "fake", context_mode="full", token_budget=2000, llm=fake_chat())
    for d in range(1, 12):
        obs["date"] = f"Day-{d}"; b.decide(obs, {"cash": 1.0, "holdings_value": 0.0, "cash_share": 1.0})
    assert b.last_context_tokens <= 2000 + 2500 and b.last_n_turns < 11   # budget binds (system prompt excluded)


def test_stateful_arm_end_to_end(tmp_path):
    cfg = build_config("fake", "ENTJ", "stateful_memory", "flat", 2, T=25, output_dir=str(tmp_path))
    assert cfg.context_mode == "rolling" and cfg.mandate_in_system
    cfg.agent_llm = fake_chat(0.1)
    df = run_simulation_v2(cfg, verbose=False)
    assert df is not None and df["Context_Mode"].iloc[0] == "rolling"
    assert df["Context_Turns"].iloc[-1] == 20 and df["Context_Tokens"].iloc[-1] > df["Context_Tokens"].iloc[0]
    assert df["Mandate_Offset_Tokens"].iloc[-1] > df["Mandate_Offset_Tokens"].iloc[0]
    assert "stateful_full_static" in ARMS


def test_three_asset_end_to_end(tmp_path):
    cfg = build_config("fake", "INTJ", "static", "crash", 4, T=20, output_dir=str(tmp_path), **THREE_ASSET)
    cfg.agent_llm = fake_chat(0.5, weights=[0.5, 0.3, 0.2])
    df = run_simulation_v2(cfg, verbose=False)
    assert df is not None and "x_asset2" in df.columns and "weight_asset2" in df.columns
    w = df[["weight_asset0", "weight_asset1", "weight_asset2"]].iloc[0].to_numpy()
    assert np.allclose(w / w.sum(), [0.5, 0.3, 0.2], atol=0.02) and abs(df["Cash_Share"].iloc[0] - 0.5) < 0.01
    assert cfg.run_id().endswith("_N3__seed4__rep0")
