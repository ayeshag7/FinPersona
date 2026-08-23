"""
Evaluation layer v2 -- per-run metrics (plan Sections 4.4, 5 (L4), 8 items 1-5; E4).

Inputs are per-day arrays from a run CSV (or a baseline trajectory):
    cash_share C_t, portfolio value, price P_t, value V_t (-> x_t), action labels,
    traded value / cost, parse status.
Outputs (dict):
    point_mas_v1, point_mas_v2, band_mas, relative_mas (common-start only),
    rg_v1 (v1 rule, all rows), rg_theta_{0.03,0.05,0.08} (+ coverage, v1 rule on
    resolvable rows only), rg_action_theta (BUY/SELL rows only),
    mcr_theta (mandate-conditional regret: mean |C_t - c*_t| over resolvable steps,
    c* = V-oracle target clipped to the persona's band), return_pct, mdd_pct,
    trade_count, turnover, cost_paid, zero_trade, fallback_share, n_scored.
Rows with Parse_Status == 'fallback' are excluded from action-based metrics and
counted (plan 8.5); unresolvable steps are never scored right/wrong (8.3).
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

from evaluation.targets import band, centre, V1_POINT_TARGETS, HALF_WIDTH

THETAS = (0.03, 0.05, 0.08)


def v1_rule(action: np.ndarray, x: np.ndarray, holdings_value: np.ndarray) -> np.ndarray:
    """v1 rationality indicator per row (nan where not applicable)."""
    out = np.full(len(action), np.nan)
    over = x > 0
    for i, a in enumerate(action):
        if a == "BUY":
            out[i] = 0.0 if over[i] else 1.0
        elif a == "SELL":
            out[i] = 1.0 if over[i] else 0.0
        elif a == "HOLD":
            out[i] = 1.0 if over[i] else (1.0 if holdings_value[i] > 1.0 else 0.0)
    return out


def oracle_target(x: np.ndarray, theta: float, persona: Optional[str], prev_target: float = 0.5) -> np.ndarray:
    """Mandate-conditional oracle cash share: V-oracle (0 if x < -theta, 1 if x > theta,
    unchanged otherwise) clipped to the persona's band (no band for the trader)."""
    lo, hi = band(persona) if persona and persona not in ("NONE", "TRADER") else (0.0, 1.0)
    out = np.empty(len(x)); cur = min(max(prev_target, lo), hi)
    for i, xi in enumerate(x):
        if xi < -theta:
            cur = lo
        elif xi > theta:
            cur = hi
        out[i] = cur
    return out


def score_run(df: pd.DataFrame, persona: str, start_cash_share: Optional[float] = None,
              initial_value: float = 10000.0) -> Dict[str, float]:
    d = df.reset_index(drop=True)
    C = d["Cash_Share"].to_numpy(dtype=float)
    P = d["Price"].to_numpy(dtype=float)
    V = d["Fundamental_Value"].to_numpy(dtype=float)
    x = d["x"].to_numpy(dtype=float) if "x" in d else np.log(P / V)
    pv = d["Portfolio_Value"].to_numpy(dtype=float)
    act = d["Action"].to_numpy(dtype=object)
    hv = d["Holdings_Value"].to_numpy(dtype=float) if "Holdings_Value" in d else (pv - d["Cash"].to_numpy(dtype=float))
    fb = d["Parse_Status"].eq("fallback").to_numpy() if "Parse_Status" in d else np.zeros(len(d), bool)
    ok = ~fb
    tv = d["Traded_Value"].to_numpy(dtype=float) if "Traded_Value" in d else np.where(np.isin(act, ["BUY", "SELL"]), 1.0, 0.0)
    cost = d["Cost_Paid"].to_numpy(dtype=float) if "Cost_Paid" in d else np.zeros(len(d))
    out: Dict[str, float] = {}
    is_persona = persona in V1_POINT_TARGETS
    out["point_mas_v1"] = float(np.mean(np.abs(C - V1_POINT_TARGETS[persona]))) if is_persona else np.nan
    c2 = centre(persona) if persona not in ("NONE", "TRADER") else 0.5
    out["point_mas_v2"] = float(np.mean(np.abs(C - c2)))
    out["band_mas"] = float(np.mean(np.maximum(0.0, np.abs(C - c2) - HALF_WIDTH)))
    c0 = start_cash_share if start_cash_share is not None else (d["Start_Cash_Share"].iloc[0] if "Start_Cash_Share" in d else C[0])
    out["relative_mas"] = float(np.mean(np.abs(C - c0)))
    out["mean_cash_share"] = float(C.mean())
    y = v1_rule(act, x, hv)
    valid = ok & ~np.isnan(y)
    out["rg_v1"] = float(100 * y[valid].mean()) if valid.any() else np.nan
    for th in THETAS:
        res = np.abs(x) >= th
        sel = valid & res
        out[f"rg_theta_{th}"] = float(100 * y[sel].mean()) if sel.any() else np.nan
        out[f"coverage_{th}"] = float(res.mean())
        sel_a = sel & np.isin(act, ["BUY", "SELL"])
        out[f"rg_action_{th}"] = float(100 * y[sel_a].mean()) if sel_a.any() else np.nan
        c_star = oracle_target(x, th, persona, prev_target=C[0])
        sel_m = ok & res
        out[f"mcr_{th}"] = float(np.mean(np.abs(C[sel_m] - c_star[sel_m]))) if sel_m.any() else np.nan
    out["return_pct"] = float((pv[-1] / initial_value - 1) * 100)
    out["mdd_pct"] = float((pv / np.maximum.accumulate(pv) - 1).min() * 100)
    out["trade_count"] = int(((tv > 0) & ok).sum())
    out["turnover"] = float(tv.sum() / initial_value)
    out["cost_paid"] = float(cost.sum())
    out["zero_trade"] = bool(out["trade_count"] == 0)
    out["fallback_share"] = float(fb.mean())
    out["n_rows"] = int(len(d))
    return out


# ---------------------------------------------------------------------------
# multi-asset (N > 1) oracle and regrets (methods review, 23 Aug 2026)
# ---------------------------------------------------------------------------
def multi_asset_oracle(X: np.ndarray, theta: float, persona: Optional[str], prev_target: float = 0.5):
    """X: (T, N) per-asset x. Existence-based cash rule: band-low if ANY asset is undervalued
    (x_i < -theta), band-high if ALL assets are overvalued (x_i > theta), unchanged otherwise.
    Sleeve weights w*: equal over undervalued assets; if none, equal over not-overvalued; if all
    overvalued, equal over all. Returns (c*, W*)."""
    lo, hi = band(persona) if persona and persona not in ("NONE", "TRADER") else (0.0, 1.0)
    T, N = X.shape
    c = np.empty(T); W = np.empty((T, N)); cur = min(max(prev_target, lo), hi)
    for t in range(T):
        under = X[t] < -theta; over = X[t] > theta
        if under.any():
            cur = lo
        elif over.all():
            cur = hi
        c[t] = cur
        if under.any():
            w = under.astype(float)
        elif (~over).any():
            w = (~over).astype(float)
        else:
            w = np.ones(N)
        W[t] = w / w.sum()
    return c, W


def multi_asset_regrets(df: pd.DataFrame, persona: Optional[str], theta: float = 0.05) -> Dict[str, float]:
    """Per-run multi-asset metrics from the runner's per-asset columns (x_asset{i}, weight_asset{i}):
    mcr_multi (cash vs the existence-rule oracle on resolvable steps), weights_tv_regret (total-variation
    distance 1/2 sum |w - w*| masked by the oracle sleeve size 1 - c*), per-asset coverage, and
    spread-resolvability (max_i x_i - min_i x_i >= theta: a relative-allocation decision is only
    resolvable when assets differ)."""
    xs = sorted([c for c in df.columns if c.startswith("x_asset")], key=lambda c: int(c[7:]))
    ws = [c.replace("x_asset", "weight_asset") for c in xs]
    if not xs or any(w not in df.columns for w in ws):
        return {}
    X = df[xs].to_numpy(dtype=float); Wagent = df[ws].to_numpy(dtype=float)
    C = df["Cash_Share"].to_numpy(dtype=float)
    c0 = float(df["Start_Cash_Share"].iloc[0]) if "Start_Cash_Share" in df else C[0]
    c_star, W_star = multi_asset_oracle(X, theta, persona, c0)
    ok = ~df["Parse_Status"].eq("fallback").to_numpy() if "Parse_Status" in df else np.ones(len(df), bool)
    res_cash = ok & ((X < -theta).any(axis=1) | (X > theta).all(axis=1))
    spread = (X.max(axis=1) - X.min(axis=1)) >= theta
    sleeve = 1.0 - c_star
    # agent sleeve weights normalised (weight_asset are portfolio shares; normalise within the sleeve)
    sw = Wagent.sum(axis=1, keepdims=True); Wn = np.where(sw > 1e-12, Wagent / np.maximum(sw, 1e-12), 1.0 / X.shape[1])
    tv = 0.5 * np.abs(Wn - W_star).sum(axis=1)
    m_w = ok & spread & (sleeve > 0.05)
    out = {"mcr_multi": float(np.mean(np.abs(C[res_cash] - c_star[res_cash]))) if res_cash.any() else np.nan,
           "coverage_multi_cash": float(res_cash.mean()),
           "weights_tv_regret": float(np.average(tv[m_w], weights=sleeve[m_w])) if m_w.any() else np.nan,
           "coverage_spread": float(spread.mean())}
    for i, c in enumerate(xs):
        out[f"coverage_asset{i}"] = float((np.abs(X[:, i]) >= theta).mean())
    return out


# ---------------------------------------------------------------------------
# normalisation and 'beats k of n' (plan 8.2)
# ---------------------------------------------------------------------------
HIGHER_BETTER = {"rg_v1": True, "rg_theta_0.05": True, "rg_action_0.05": True, "return_pct": True,
                 "mdd_pct": True, "point_mas_v1": False, "point_mas_v2": False, "band_mas": False,
                 "relative_mas": False, "mcr_0.05": False}


def normalise(agent_val: float, floor: float, ceiling: float) -> float:
    if any(np.isnan(v) for v in (agent_val, floor, ceiling)) or ceiling == floor:
        return np.nan
    return float((agent_val - floor) / (ceiling - floor))


def floors_and_ceilings(baselines: Dict[str, Dict[str, float]], persona: str) -> Dict[str, Dict[str, float]]:
    """baselines: {policy_name: metrics}. Returns {metric: {floor, ceiling, degenerate}} using:
    RG/return-type: floor = best of {always_hold, random, buy_day1_hold}, ceiling = mandate_conditional_oracle;
    MAS-type: ceiling = constant_mix (0 by construction), floor = worst of {always_buy, always_sell, random}."""
    out = {}
    trivial = [baselines[k] for k in ("always_hold", "random", "buy_day1_hold") if k in baselines]
    worst_pool = [baselines[k] for k in ("always_buy", "always_sell", "random") if k in baselines]
    mco = baselines.get("mandate_conditional_oracle", {})
    cmix = baselines.get("constant_mix", {})
    for m, hb in HIGHER_BETTER.items():
        if hb:
            vals = [b.get(m, np.nan) for b in trivial]
            floor = np.nanmax(vals) if vals else np.nan
            ceiling = mco.get(m, np.nan)
        else:
            vals = [b.get(m, np.nan) for b in worst_pool]
            floor = np.nanmax(vals) if vals else np.nan      # worst = largest deviation
            ceiling = cmix.get(m, np.nan)
        degenerate = (not np.isnan(floor)) and (not np.isnan(ceiling)) and ((ceiling <= floor) if hb else (ceiling >= floor))
        out[m] = {"floor": float(floor) if floor == floor else np.nan, "ceiling": float(ceiling) if ceiling == ceiling else np.nan,
                  "degenerate": bool(degenerate)}
    return out


def beats_k_of_n(agent: Dict[str, float], baselines: Dict[str, Dict[str, float]]) -> Dict[str, int]:
    out = {}
    for m, hb in HIGHER_BETTER.items():
        a = agent.get(m, np.nan)
        if np.isnan(a):
            out[m] = -1; continue
        k = 0
        for b in baselines.values():
            v = b.get(m, np.nan)
            if np.isnan(v):
                continue
            k += int(a > v) if hb else int(a < v)
        out[m] = k
    return out
