"""
E3 harness tests, offline (a fake LLM returns canned JSON): arm registry, prompt
assembly per arm/track/wording, v2 agent decision parsing and fallback, runner
end-to-end on a short horizon with start design, cost, dead band, provenance
columns and the restatement probe.
"""
import json
import os

import pytest
from langchain_core.runnables import RunnableLambda

from agent.v2_agent import V2Agent
from agent import v2_prompts as P
from experiments.arms_v2 import ARMS, build_config, expand_grid
from simulation.runner_v2 import run_simulation_v2


def fake_llm(target=0.3):
    def _run(messages):
        text = messages.to_string() if hasattr(messages, "to_string") else str(messages)
        if "Do not trade now" in text:
            return "I follow the guardian mandate; I hold mostly cash because the market is volatile."
        if "target_cash_share" in text:
            return json.dumps({"target_cash_share": target, "rationale": "test"})
        return json.dumps({"action": "BUY", "quantity": 0.5, "rationale": "test"})
    return RunnableLambda(_run)


def test_arm_registry_and_grid():
    cfg = build_config("m", "ISFJ", "swapped", "flat", 1)
    assert cfg.mandate_persona == "ENTJ" and cfg.mandate_block == "mandate"
    t = build_config("m", "ISFJ", "trader", "flat", 1)
    assert t.persona == "NONE" and t.start_design == "common"
    b = build_config("m", "ENTJ", "static", "crash", 1, bridge=True)
    assert b.start_design == "v1" and b.action_interface == "v1" and b.wording == "original"
    grid = expand_grid(["m"], ["ISFJ", "ENTJ"], ["static", "memory"], ["flat", "crash"], [1, 2], reps=2,
                       crash_discounts=(0.55, 0.85))
    assert len(grid) == 2 * 2 * 2 * 2 * (1 + 2)   # crash expands over two discounts
    assert len({c.run_id() for c in grid}) == len(grid)
    assert set(ARMS) >= {"static", "memory", "placebo_declarative", "placebo_directive", "wrapper_only", "swapped", "trader"}


def test_prompt_assembly_per_arm():
    sys_b = P.system_prompt("ISFJ", track="B")
    sys_a = P.system_prompt("ISFJ", track="A")
    assert "TARGET. Your mandated cash allocation is 80%" in sys_a and "TARGET." not in sys_b
    assert "TASK." in sys_b and "Commander" not in sys_b and "dedication" in sys_b
    assert P.mandate_block("none", "ISFJ") == ""
    m = P.mandate_block("mandate", "ISFJ")
    assert "ACTIVE MEMORY REFRESH" in m and "cash cushion" in m and "puts/hedges" not in m
    assert "puts/hedges" in P.mandate_block("mandate", "ISFJ", wording="original")
    assert "RECORD-KEEPER" in P.mandate_block("placebo_directive", "ISFJ")
    w = P.mandate_block("wrapper_only", "ISFJ")
    assert "ACTIVE MEMORY REFRESH" in w and "GUARDIAN" not in w
    assert "80%" in P.mandate_text("ISFJ", "numeric_only")
    assert "BUY" not in P.mandate_text("ENTJ", "no_action_clauses")
    trader = P.system_prompt("NONE", objective="maximise")
    assert trader.startswith("You manage a single-asset portfolio") and "maximise" in trader
    pb = P.system_prompt("ENTJ", mandate_in_system=True)
    assert "CORE MANDATE." in pb and "MOMENTUM COMMANDER" in pb


def test_agent_decide_probe_and_provenance():
    a = V2Agent("ISFJ", "fake", mandate_block="mandate", llm=fake_llm(0.3))
    obs = {"date": "Day-1", "price": 100.0, "SMA20": 100.0, "SMA50": 100.0, "RSI14": 50.0}
    d = a.decide(obs, {"cash": 5000.0, "holdings_value": 5000.0, "cash_share": 0.5})
    assert d.target_cash_share == 0.3 and a.last_parse_status == "ok"
    msg = a.rendered_human_message(obs, {"cash": 5000.0, "holdings_value": 5000.0, "cash_share": 0.5})
    assert "MARKET OBSERVATION" in msg and "ACTIVE MEMORY REFRESH" in msg and "target_cash_share" in msg
    assert "guardian" in a.probe_restatement(obs, {"cash": 1.0, "holdings_value": 0.0}).lower()
    comps = a.prompt_components()
    assert comps["mandate"] and "TASK." in comps["system"]
    # fallback path
    bad = V2Agent("ISFJ", "fake", llm=RunnableLambda(lambda m: "not json"))
    d2 = bad.decide(obs, {"cash": 5000.0, "holdings_value": 5000.0, "cash_share": 0.5})
    assert bad.last_parse_status == "fallback" and abs(d2.target_cash_share - 0.5) < 1e-9
    # v1 interface
    v1 = V2Agent("ENTJ", "fake", action_interface="v1", llm=fake_llm())
    dv = v1.decide(obs, {"cash": 10000.0, "holdings_value": 0.0})
    assert dv.action == "BUY" and dv.quantity == 0.5


def test_runner_end_to_end(tmp_path):
    cfg = build_config("fake", "ISFJ", "memory", "crash", 3, T=40, output_dir=str(tmp_path), probe_every=10)
    cfg.agent_llm = fake_llm(0.3)
    df = run_simulation_v2(cfg, verbose=False)
    assert df is not None and len(df) == 40
    assert abs(df["Start_Cash_Share"].iloc[0] - 0.80) < 1e-9            # ISFJ band centre
    assert df["Action"].iloc[0] == "BUY"                                   # 0.80 -> 0.30 cash = BUY
    assert df["Cost_Paid"].iloc[0] > 0 and df["Cash_Share"].iloc[0] == pytest.approx(0.30, abs=0.01)
    # re-stating the same target = rebalancing: trades only when price drift moved the share > 1 pt
    later = df.iloc[1:]
    assert set(later["Action"]) <= {"BUY", "SELL", "HOLD"}
    assert (later.loc[later["Action"] == "HOLD", "Traded_Value"] == 0).all()
    assert (later.loc[later["Action"] != "HOLD", "Traded_Value"] > 0).all()
    assert (later["Cash_Share"] - 0.30).abs().max() < 0.02                # always re-targeted to 0.30 after trades
    assert df["Restatement_Probe"].iloc[0] and not df["Restatement_Probe"].iloc[1]
    for col in ("Env_Version", "Gen_Config_Hash", "Prompt_Hash", "Temperature", "Phase", "x", "Resolvable_0.05",
                "Parse_Status", "Band_Centre", "Traded_Value"):
        assert col in df.columns
    assert df["Env_Version"].iloc[0] == "v2" and df["Parse_Status"].eq("ok").all()
    files = list(tmp_path.rglob("*.csv"))
    assert len(files) == 1 and list(tmp_path.rglob("*.meta.json"))
    # bridge cell: v1 interface + 100% cash start
    cfg2 = build_config("fake", "ENTJ", "static", "flat", 3, T=20, output_dir=str(tmp_path), bridge=True)
    cfg2.agent_llm = fake_llm()
    df2 = run_simulation_v2(cfg2, verbose=False)
    assert df2["Start_Cash_Share"].iloc[0] == 1.0 and df2["Action"].iloc[0] == "BUY"
    assert df2["Cash_Share"].iloc[0] == pytest.approx(0.5, abs=1e-6)
