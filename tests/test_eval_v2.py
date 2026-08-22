"""
E4 evaluation-layer tests: per-run metrics, baselines inside the v2 env,
normalisation (MCR non-degenerate, RG_v1 degeneracy flagged), salience surrogate
(persona share high under a persona effect, ~0 under the label-permutation
null), the t=0 gate on a common-start synthetic, and the report end to end.
"""
import json

import numpy as np
import pandas as pd
import pytest
from langchain_core.runnables import RunnableLambda

from envs.synthetic_market import SyntheticMarketEnv
from evaluation.baselines_v2 import baseline_metrics
from evaluation.metrics_v2 import score_run, floors_and_ceilings, beats_k_of_n, oracle_target
from evaluation.salience import surrogate_shares, separability_gate
from experiments.arms_v2 import build_config
from simulation.runner_v2 import run_simulation_v2
from tools.report_v2 import build_tables, salience_tables, write_report, load_runs


def test_oracle_target_and_score_run():
    x = np.array([-0.1, 0.0, 0.1, 0.0])
    assert oracle_target(x, 0.05, "ISFJ", 0.8).tolist() == [0.7, 0.7, 0.9, 0.9]
    assert oracle_target(x, 0.05, "TRADER", 0.5).tolist() == [0.0, 0.0, 1.0, 1.0]
    df = pd.DataFrame({"Cash_Share": [0.8, 0.8, 0.8], "Price": [100, 110, 120], "Fundamental_Value": [100, 100, 100],
                       "x": np.log([1.0, 1.1, 1.2]), "Portfolio_Value": [10000, 10200, 10400], "Cash": [8000] * 3,
                       "Holdings_Value": [2000, 2200, 2400], "Action": ["HOLD", "HOLD", "SELL"],
                       "Traded_Value": [0, 0, 500], "Cost_Paid": [0, 0, 0.25], "Parse_Status": ["ok", "ok", "ok"],
                       "Start_Cash_Share": [0.8] * 3})
    m = score_run(df, "ISFJ", 0.8)
    assert m["band_mas"] == 0.0 and abs(m["point_mas_v1"] - 0.2) < 1e-9
    assert m["coverage_0.05"] == pytest.approx(2 / 3) and m["rg_theta_0.05"] == 100.0
    assert m["trade_count"] == 1 and not m["zero_trade"] and m["fallback_share"] == 0.0


def test_baselines_and_normalisation():
    env = SyntheticMarketEnv("crash", 120, 5)
    bm = baseline_metrics(env, "ENTJ", 0.10, random_seeds=2)
    assert {"always_hold", "always_buy", "always_sell", "buy_day1_hold", "constant_mix", "momentum",
            "mean_reversion", "v_oracle", "mandate_conditional_oracle", "random"} <= set(bm)
    assert bm["constant_mix"]["band_mas"] < 1e-6
    assert bm["mandate_conditional_oracle"]["mcr_0.05"] < bm["random"]["mcr_0.05"]
    fc = floors_and_ceilings(bm, "ENTJ")
    assert not fc["mcr_0.05"]["degenerate"] and not fc["band_mas"]["degenerate"]
    others = [v["mcr_0.05"] for kk, v in bm.items() if kk != "mandate_conditional_oracle"]
    assert bm["mandate_conditional_oracle"]["mcr_0.05"] <= min(others) + 0.02   # best or tied (narrow aggressive band)
    k = beats_k_of_n(bm["mandate_conditional_oracle"], bm)
    assert k["mcr_0.05"] >= 1 and k["band_mas"] >= 1


def _synthetic_runs(effect: float, n_seeds=6, T=50, rng=np.random.default_rng(0)):
    rows = []
    for seed in range(n_seeds):
        mk = rng.normal(size=(T, 3))
        for p, base in (("ISFJ", 0.8), ("ENTJ", 0.1)):
            for day in range(1, T + 1):
                tgt = base * effect + (1 - effect) * 0.45 + 0.1 * mk[day - 1, 0] + 0.02 * rng.normal()
                rows.append({"Model": "m", "Persona": p, "Seed": seed, "Arm": "static", "Decode_Replicate": 0,
                             "Mandate_Block": "none", "Mandate_Persona": p, "Day": day, "Target_Cash_Share": tgt,
                             "Cash_Share": tgt, "Start_Cash_Share": 0.5, "obs_price": 100 + mk[day - 1, 0],
                             "obs_RSI14": 50 + 10 * mk[day - 1, 1], "obs_news_sentiment": 0.3 * mk[day - 1, 2]})
    return pd.DataFrame(rows)


def test_salience_surrogate_and_null():
    d = _synthetic_runs(effect=1.0)
    res = surrogate_shares(d, n_estimators=100, n_repeats=5)
    assert res["r2"] > 0.5 and res["S_persona"] > 0.5, res
    null = surrogate_shares(d, n_estimators=100, n_repeats=5, permute_persona=True)
    assert null["S_persona"] < 0.25, null
    d0 = _synthetic_runs(effect=0.0)
    res0 = surrogate_shares(d0, n_estimators=100, n_repeats=5)
    assert res0["S_persona"] < 0.3


def test_separability_gate_synthetic():
    rng = np.random.default_rng(1)
    rows = []
    for p, c in (("ISFJ", 0.8), ("INTJ", 0.5), ("ENTJ", 0.1)):
        for _ in range(30):
            rows.append({"Persona": p, "C1": np.clip(c + rng.normal(0, 0.04), 0, 1)})
    g = separability_gate(pd.DataFrame(rows))
    assert g["pass"] and g["kw_p"] < 0.01 and g["auc"] > 0.9
    rows2 = [{"Persona": p, "C1": 0.9 + rng.normal(0, 0.05)} for p in ("ISFJ", "INTJ", "ENTJ") for _ in range(30)]
    assert not separability_gate(pd.DataFrame(rows2))["pass"]


def test_report_end_to_end(tmp_path):
    def fake(target):
        return RunnableLambda(lambda m: json.dumps({"target_cash_share": target, "rationale": "t"}))
    for persona, tgt in (("ISFJ", 0.8), ("ENTJ", 0.1)):
        for seed in (1, 2):
            cfg = build_config("fake", persona, "static", "crash", seed, T=30, output_dir=str(tmp_path), start_design="common")
            cfg.agent_llm = fake(tgt)
            assert run_simulation_v2(cfg, verbose=False) is not None
    runs = load_runs(str(tmp_path))
    assert len(runs) == 4
    tables = build_tables(runs)
    assert len(tables["per_run"]) == 4 and "norm_mcr_0.05" in tables["per_run"]
    assert (tables["per_run"]["Start_Cash_Share"] == 0.5).all()
    st = salience_tables(runs)
    assert "gate_common_start" in st and "salience_primary" in st
    write_report({**tables, **st}, str(tmp_path / "rep"))
    assert (tmp_path / "rep.md").exists()
