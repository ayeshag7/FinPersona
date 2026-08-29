"""
E0 guards:
  * the frozen v1 generator/tracker copies are byte-identical to the tag;
  * provenance hashes are stable, sensitive to config and prompt changes, and
    the runner-facing helpers work on the v1 env and agents (offline);
  * Table 2 generated from code is in sync with the committed file.
"""
import hashlib
import json
import os
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = {
    "envs/v1/synthetic_market_v1.py": "74c0e2b49a0f701c4e3b1e31fc9b7d10b71616dfbb842532a988be0549b0c68b",
    "envs/v1/portfolio_tracker_v1.py": "e98c70739ba87c9e6776146d4505057e596359322184810589a9fe177d0c51bb",
}


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


@pytest.mark.parametrize("rel,expected", list(FROZEN.items()))
def test_frozen_copies_unchanged(rel, expected):
    assert _sha(os.path.join(ROOT, rel)) == expected, f"{rel} was modified; the v1 freeze must stay byte-identical"


def test_frozen_copy_matches_tag():
    try:
        out = subprocess.run(["git", "show", "v1-env-freeze:envs/synthetic_market.py"],
                             capture_output=True, check=True, cwd=ROOT).stdout
    except Exception as exc:
        pytest.skip(f"tag not available: {exc}")
    with open(os.path.join(ROOT, "envs/v1/synthetic_market_v1.py"), "rb") as fh:
        local = fh.read()
    assert out.replace(b"\r\n", b"\n") == local.replace(b"\r\n", b"\n")


def test_config_hash_sensitivity():
    from envs.v1.synthetic_market_v1 import SyntheticMarketEnv
    from simulation.provenance import env_provenance, generator_config_hash
    a = env_provenance(SyntheticMarketEnv(scenario="flat", n_days=50, seed=1))
    b = env_provenance(SyntheticMarketEnv(scenario="flat", n_days=50, seed=1))
    c = env_provenance(SyntheticMarketEnv(scenario="flat", n_days=50, seed=2))
    d = env_provenance(SyntheticMarketEnv(scenario="crash", n_days=50, seed=1, crash_discount=0.85))
    assert a == b
    assert a["Gen_Config_Hash"] != c["Gen_Config_Hash"] != d["Gen_Config_Hash"]
    assert a["Env_Code_Hash"] == FROZEN["envs/v1/synthetic_market_v1.py"][:16]
    assert a["Env_Version"] == "v1"
    # key order must not matter
    assert generator_config_hash({"a": 1, "b": 2}) == generator_config_hash({"b": 2, "a": 1})


def test_prompt_hash_sensitivity():
    from simulation.provenance import prompt_hash, text_hash
    h = prompt_hash("sys", "human", "fmt", "")
    assert h == prompt_hash("sys", "human", "fmt", "")
    assert h != prompt_hash("sys", "human", "fmt", "REMINDER")
    assert h != prompt_hash("sys ", "human", "fmt", "")
    assert text_hash("ab", "c") != text_hash("a", "bc")


def test_agent_provenance_offline(monkeypatch):
    """Instantiate the v1 agents with a dummy key (no API call) and check the
    prompt hash covers system + human template + format instructions (+ mandate)."""
    pytest.importorskip("langchain_google_genai")
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key-for-offline-test")
    from agent.static_agent import StaticAgent
    from agent.memory_agent import ActiveMemoryAgent
    from simulation.provenance import agent_provenance
    s = StaticAgent("ISFJ", model_name="gemini-2.5-flash")
    m = ActiveMemoryAgent("ISFJ", model_name="gemini-2.5-flash")
    ps, pm = agent_provenance(s), agent_provenance(m)
    assert ps["Temperature"] == 0.2 and pm["Temperature"] == 0.2
    assert ps["System_Prompt_Hash"] == pm["System_Prompt_Hash"]  # same persona text
    assert ps["Prompt_Hash"] != pm["Prompt_Hash"]  # memory adds the mandate wrapper + template
    s2 = StaticAgent("ENTJ", model_name="gemini-2.5-flash")
    assert agent_provenance(s2)["Prompt_Hash"] != ps["Prompt_Hash"]
    comps = m.prompt_components()
    assert "ACTIVE MEMORY REFRESH" in comps["mandate"] and "GUARDIAN INVESTOR" in comps["mandate"]
    assert len(ps["Prompt_Hash"]) == 16


def test_table2_in_sync(tmp_path):
    """The committed Table 2 must equal what the code generates now."""
    from tools.gen_table2 import write_outputs
    rows, prows = write_outputs("v1", str(tmp_path))
    gen = json.load(open(tmp_path / "table2_v1_from_code.json", encoding="utf-8"))
    committed_path = os.path.join(ROOT, "docs", "env_v2", "generated", "table2_v1_from_code.json")
    if not os.path.exists(committed_path):
        pytest.skip("committed Table 2 not present")
    committed = json.load(open(committed_path, encoding="utf-8"))
    assert gen["rows"] == committed["rows"], "run `python -m tools.gen_table2 --env v1` and commit the result"
    assert gen["portfolio"] == committed["portfolio"]
    # what the prompt renders, from the generated table
    rendered = [r["obs_key"] for r in rows if r["rendered_static"]]
    assert rendered == ["date", "price", "implied_volatility", "news_sentiment", "reported_PE",
                        "SMA20", "SMA60", "trend_regime", "volume_ratio", "RSI14"]


def test_v1_bull_trap_value_plateau_frozen():
    """E0 record of the frozen v1 generator (v2.1 Phase 0, item 0.5). tests/test_env_logic.py (written in March 2026
    against an earlier draft generator) asserted a value plateau (|V_1 - V_50| < 1) and P_50 > 140 in a 50-day bull
    trap. Neither holds on the frozen v1 at the test's own seed (42): V_1 = 100.60, V_50 = 96.32 (the v1 bull-trap
    value is a log random walk N(0.001, 0.01) in phase 1, not a plateau) and P_50 = 125.93. The v1 facts are
    asserted positively here so that the baseline is on record; the v2 contract is tested in tests/test_env_logic.py."""
    from envs.v1.synthetic_market_v1 import SyntheticMarketEnv as V1Env
    env = V1Env(scenario="bull_trap", n_days=50, start_price=100.0)
    df = env.data
    dV = abs(df.iloc[0]["fundamental_value"] - df.iloc[-1]["fundamental_value"])
    assert dV >= 1.0, f"frozen v1 bull-trap value moved by {dV:.2f} on record; the legacy plateau assertion never held on v1"
    assert abs(df.iloc[0]["fundamental_value"] - 100.598) < 0.01 and abs(df.iloc[-1]["fundamental_value"] - 96.324) < 0.01
    assert abs(df.iloc[-1]["price"] - 125.93) < 0.01
