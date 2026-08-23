"""Items added after the 23 Aug reviews: multi-asset oracle/regrets, summary arm, L5 oracle, windowed stats, hl engines."""
import json

import numpy as np
import pandas as pd
import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from evaluation.metrics_v2 import multi_asset_oracle, multi_asset_regrets
from agent.stateful_agent import StatefulV2Agent
from envs.v2.mispricing import load_params
from tools.stats_v2 import window_means, windowed_trend_vs_null, paired_sign_flip, phase_time_model


def test_multi_asset_oracle_existence_rule_and_regret():
    X = np.array([[-0.1, 0.0, 0.0], [0.1, 0.1, 0.1], [0.0, 0.0, 0.0], [-0.1, 0.1, 0.0]])
    c, W = multi_asset_oracle(X, 0.05, "ISFJ", 0.8)
    assert c.tolist() == [0.7, 0.9, 0.9, 0.7]
    assert W[0].tolist() == [1.0, 0.0, 0.0] and np.allclose(W[1], 1 / 3) and np.allclose(W[2], 1 / 3) and W[3].tolist() == [1.0, 0.0, 0.0]
    df = pd.DataFrame({"x_asset0": X[:, 0], "x_asset1": X[:, 1], "x_asset2": X[:, 2],
                       "weight_asset0": [0.3, 0.1, 0.1, 0.3], "weight_asset1": [0.0, 0.0, 0.0, 0.0], "weight_asset2": [0.0, 0.0, 0.0, 0.0],
                       "Cash_Share": [0.7, 0.9, 0.9, 0.7], "Start_Cash_Share": [0.8] * 4, "Parse_Status": ["ok"] * 4})
    r = multi_asset_regrets(df, "ISFJ")
    assert r["mcr_multi"] == 0.0 and r["coverage_spread"] == 0.5 and "coverage_asset2" in r
    assert 0.0 <= r["weights_tv_regret"] <= 1.0


def test_summary_arm_uses_neutral_summariser_and_logs():
    calls = []
    def _run(messages):
        calls.append([m.content[:40] for m in messages])
        text = "\n".join(m.content for m in messages)
        if "neutral note-taker" in text:
            return AIMessage(content="The trader held mostly cash and bought a little on dips.")
        return AIMessage(content=json.dumps({"target_cash_share": 0.8, "rationale": "t"}))
    a = StatefulV2Agent("ISFJ", "fake", context_mode="summary", summary_every=3, summary_raw_turns=2, llm=RunnableLambda(_run))
    obs = {"date": "Day-1", "price": 100.0, "SMA20": 100.0, "SMA50": 100.0, "RSI14": 50.0}
    for d in range(1, 8):
        obs["date"] = f"Day-{d}"; a.decide(obs, {"cash": 8000.0, "holdings_value": 2000.0, "cash_share": 0.8})
    log = a.context_log()
    assert log["Summary_Calls"] == 2 and "mostly cash" in log["Summary_Text"] and log["Context_Turns"] == 2
    assert any("neutral note-taker" in c[0] for c in calls)   # summariser system prompt is the neutral one
    assert a.build_messages(obs, {"cash": 1.0, "holdings_value": 0.0, "cash_share": 1.0})[1].content.startswith("SUMMARY OF YOUR EARLIER STEPS")


def test_half_life_engines():
    p60, p300 = load_params("fw_hl60"), load_params("fw_hl300")
    assert p60.phi > p300.phi and p60.name == "fw_fallback_hl60"


def _per_step(trend=0.0, n_runs=6, T=100, rng=np.random.default_rng(0)):
    rows = []
    for r in range(n_runs):
        for arm in ("memory", "stateful_memory"):
            for d in range(1, T + 1):
                y = 0.2 + (trend * d / T if arm == "stateful_memory" else 0.0) + 0.02 * rng.normal()
                rows.append({"Model": "m", "Persona": "ISFJ", "Arm": arm, "Scenario": "flat", "Seed": r, "Decode_Replicate": 0,
                             "Day": d, "Phase": "calm" if d < 50 else "mania", "Ordering": "setup_first", "band_mas_t": y})
    return pd.DataFrame(rows)


def test_windowed_stats_and_sign_flip():
    d0 = _per_step(0.0)
    r0 = windowed_trend_vs_null(d0[d0.Arm == "memory"], n_perm=200)
    assert r0["n_runs"] == 6 and r0["perm_p"] > 0.05 and r0["null"] == "circular"
    d1 = _per_step(0.3)
    sf = paired_sign_flip(d1, arm="stateful_memory", reference="memory", n_perm=500)
    assert sf["n_pairs"] == 6 and sf["mean_trend_diff"] > 0 and sf["p_signflip"] < 0.05
    w = window_means(d1, "band_mas_t")
    assert {"y", "day_c", "phase", "run"} <= set(w.columns)
    me = phase_time_model(d1, "band_mas_t")
    assert len(me) and (me["term"] != "ERROR").all()


def test_l5_oracle_smoke():
    from evaluation.observables_oracle import ObservablesOracle, observables_oracle_trajectory
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.metrics_v2 import score_run
    orc = ObservablesOracle(train_seeds=[900, 901], T=80, scenarios=("flat", "crash"), deltas=(0.7,), feature_set="price_only").fit()
    assert "calm" in orc.oos or "event" in orc.oos
    env = SyntheticMarketEnv("crash", 80, 3)
    traj = observables_oracle_trajectory(env, "ISFJ", 0.8, orc)
    m = score_run(traj, "ISFJ", 0.8)
    assert 0.0 <= m["mcr_0.05"] <= 1.0 and len(traj) == 80
