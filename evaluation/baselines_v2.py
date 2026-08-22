"""
Rule-based baselines inside the v2 environment (plan Section 8 item 1; E4).

Every baseline is simulated on the SAME price path as the cell, with PortfolioV2,
the cell's start allocation, cost tier and execution rule, and returns a DataFrame
in the run-CSV column convention so `metrics_v2.score_run` applies unchanged:
    always_hold, always_buy (fully invested), always_sell (all cash), random (k seeds,
    v1 interface BUY/SELL/HOLD with q ~ U(0,1)), buy_day1_hold, constant_mix (daily
    rebalance to the persona's band centre), momentum (SMA20 > SMA50 -> invested,
    else cash), mean_reversion (RSI < 30 -> invested, RSI > 70 -> cash, else unchanged),
    v_oracle (cash 0 if x < -theta, 1 if x > theta, unchanged otherwise),
    mandate_conditional_oracle (v_oracle clipped to the band).
The observables oracle (L5) and the no-mandate trader are LLM/surrogate-based and
live elsewhere (evaluation/salience.py, experiments/arms_v2.py 'trader').
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from envs.synthetic_market import SyntheticMarketEnv
from evaluation.targets import band, centre
from simulation.portfolio_v2 import PortfolioV2

THETA = 0.05


def _frame(env: SyntheticMarketEnv, port_rows: List[Dict]) -> pd.DataFrame:
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    df = pd.DataFrame(port_rows)
    df["Price"] = d["price"].values[: len(df)]
    df["Fundamental_Value"] = d["fundamental_value"].values[: len(df)]
    df["x"] = d["x"].values[: len(df)]
    df["Phase"] = d["phase"].values[: len(df)]
    df["Parse_Status"] = "ok"
    return df


def _run_policy(env: SyntheticMarketEnv, start_cash_share: float, policy: Callable, cost_bp: float = 5.0,
                interface: str = "target", initial_value: float = 10000.0) -> pd.DataFrame:
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    P = d["price"].to_numpy(dtype=float)
    port = PortfolioV2(initial_value, start_cash_share, P[0])
    rows = []
    state = {}
    for t in range(len(P)):
        row = d.iloc[t]
        st = port.get_state(P[t])
        if interface == "target":
            tgt = policy(t, row, st, state)
            rec = port.retarget(tgt, P[t], t + 1, cost_bp=cost_bp)
            action = rec["derived_action"]
        else:
            a, q = policy(t, row, st, state)
            rec = port.execute_v1_action(a, q, P[t], t + 1, cost_bp=cost_bp)
            action = rec["derived_action"]
        st2 = port.get_state(P[t])
        rows.append({"Day": t + 1, "Cash_Share": st2["cash_share"], "Portfolio_Value": st2["total_value"],
                     "Cash": st2["cash"], "Holdings_Value": st2["holdings_value"], "Action": action,
                     "Traded_Value": rec["traded_value"], "Cost_Paid": rec["cost_paid"],
                     "Start_Cash_Share": start_cash_share})
    return _frame(env, rows)


def baseline_policies(persona: Optional[str], start_cash_share: float, theta: float = THETA,
                      random_seeds: int = 10) -> Dict[str, tuple]:
    lo, hi = band(persona) if persona and persona not in ("NONE", "TRADER") else (0.0, 1.0)
    c = centre(persona) if persona and persona not in ("NONE", "TRADER") else 0.5
    pol: Dict[str, tuple] = {
        "always_hold": (lambda t, r, st, s: st["cash_share"], "target"),
        "always_buy": (lambda t, r, st, s: 0.0, "target"),
        "always_sell": (lambda t, r, st, s: 1.0, "target"),
        "buy_day1_hold": (lambda t, r, st, s: 0.0 if t == 0 else st["cash_share"], "target"),
        "constant_mix": (lambda t, r, st, s: c, "target"),
        "momentum": (lambda t, r, st, s: 0.0 if r["SMA20"] > r["SMA50"] else 1.0, "target"),
        "mean_reversion": (lambda t, r, st, s: 0.0 if r["RSI14"] < 30 else (1.0 if r["RSI14"] > 70 else st["cash_share"]), "target"),
        "v_oracle": (lambda t, r, st, s: 0.0 if r["x"] < -theta else (1.0 if r["x"] > theta else st["cash_share"]), "target"),
        "mandate_conditional_oracle": (lambda t, r, st, s: lo if r["x"] < -theta else (hi if r["x"] > theta else min(max(st["cash_share"], lo), hi)), "target"),
    }
    for k in range(random_seeds):
        rng = np.random.default_rng(1000 + k)
        def _rand(t, r, st, s, rng=rng):
            a = ["BUY", "SELL", "HOLD"][rng.integers(3)]
            return a, float(rng.random())
        pol[f"random_{k}"] = (_rand, "v1")
    return pol


def run_baselines(env: SyntheticMarketEnv, persona: Optional[str], start_cash_share: float, cost_bp: float = 5.0,
                  theta: float = THETA, random_seeds: int = 10) -> Dict[str, pd.DataFrame]:
    out = {}
    for name, (fn, iface) in baseline_policies(persona, start_cash_share, theta, random_seeds).items():
        out[name] = _run_policy(env, start_cash_share, fn, cost_bp=cost_bp, interface=iface)
    return out


def baseline_metrics(env: SyntheticMarketEnv, persona: Optional[str], start_cash_share: float, cost_bp: float = 5.0,
                     theta: float = THETA, random_seeds: int = 10) -> Dict[str, Dict[str, float]]:
    """Per-policy metrics; the k random seeds are averaged into one 'random' entry."""
    from evaluation.metrics_v2 import score_run
    trajs = run_baselines(env, persona, start_cash_share, cost_bp, theta, random_seeds)
    scored = {name: score_run(df, persona if persona else "TRADER", start_cash_share) for name, df in trajs.items()}
    rand = [v for k, v in scored.items() if k.startswith("random_")]
    out = {k: v for k, v in scored.items() if not k.startswith("random_")}
    if rand:
        keys = rand[0].keys()
        out["random"] = {k: (float(np.nanmean([r[k] for r in rand])) if isinstance(rand[0][k], (int, float, np.floating, np.integer)) and not isinstance(rand[0][k], bool) else rand[0][k]) for k in keys}
    return out
