"""
Trivial-policy baselines and shared metric definitions for FinPersona-Bench v2
re-scoring (plan Section 8 items 1-3, Section 4.4, Section 5 L4).

Pure numpy / pandas, no dependency on the simulation package, so it can be
reused by other evaluation scripts.

Conventions
-----------
* One asset, $10,000 initial cash, zero shares, same-day execution at the
  day's close ``Price_t``, fractional shares, no transaction cost.
* All baselines start at 100 percent cash (the v1 start, C_0 = 1.0).
* v1 action interface: BUY q spends ``cash * q``; SELL q sells ``qty * q``;
  HOLD does nothing.
* Target-share interface: the policy emits a target cash share c* (or NaN for
  "no trade"); the portfolio is rebalanced to c* at the close.  Derived action
  labels for RG scoring: BUY if the equity share rose by more than 1 point,
  SELL if it fell by more than 1 point, HOLD otherwise.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

INITIAL_CASH = 10_000.0

# ---------------------------------------------------------------- targets ---
V1_TARGET = {"ISFJ": 1.0, "INTJ": 0.5, "ENTJ": 0.2}
V2_BAND = {"ISFJ": (0.70, 0.90), "INTJ": (0.40, 0.60), "ENTJ": (0.00, 0.20)}
V2_CENTRE = {p: (lo + hi) / 2.0 for p, (lo, hi) in V2_BAND.items()}
V2_HALF_WIDTH = 0.10
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
THETAS = (0.03, 0.05, 0.08)
N_RANDOM_SEEDS = 10
RANDOM_SEED_BASE = 20260822
MAS_METRICS = ("point_mas_v1", "point_mas_v2", "band_mas_v2", "rel_mas")


def theta_key(th: float) -> str:
    return f"{th:.2f}"


# ================================================================ metrics ====
def v1_rationality(action: np.ndarray, price: np.ndarray, fv: np.ndarray,
                   holdings_value: np.ndarray) -> np.ndarray:
    """The v1 rule from experiments/run_experiments.py::calculate_metrics.

    Returns an array of 1/0/NaN (NaN = not scored: unknown action or V<=0).
    BUY correct iff P < V; SELL correct iff P > V; HOLD correct iff P > V or
    (P <= V and holdings value > $1).  P == V is scored exactly as the v1 code
    does (BUY -> 0, SELL -> 0, HOLD -> holdings > 1).
    """
    y = np.full(len(action), np.nan)
    ok_v = np.isfinite(fv) & (fv > 0)
    under = price < fv
    over = price > fv
    is_buy = action == "BUY"
    is_sell = action == "SELL"
    is_hold = action == "HOLD"
    m = is_buy & ok_v
    y[m] = under[m].astype(float)
    m = is_sell & ok_v
    y[m] = over[m].astype(float)
    hold_ok = np.where(over, 1.0, (holdings_value > 1.0).astype(float))
    m = is_hold & ok_v
    y[m] = hold_ok[m]
    return y


def mas_metrics(c: np.ndarray, persona) -> dict:
    """MAS family for a cash-share path ``c`` against one persona's targets."""
    out = {k: np.nan for k in MAS_METRICS}
    out["rel_mas"] = float(np.nanmean(np.abs(c - 1.0)))   # C_0 = 1.0 -> equals 1 - mean C
    if persona is None or persona not in V1_TARGET:
        return out
    t1 = V1_TARGET[persona]
    t2 = V2_CENTRE[persona]
    out["point_mas_v1"] = float(np.nanmean(np.abs(c - t1)))
    out["point_mas_v2"] = float(np.nanmean(np.abs(c - t2)))
    out["band_mas_v2"] = float(np.nanmean(np.maximum(0.0, np.abs(c - t2) - V2_HALF_WIDTH)))
    return out


def compute_run_metrics(price, fv, pv, cash, qty, action, persona,
                        fallback_mask=None, thetas=THETAS,
                        initial_cash=INITIAL_CASH) -> dict:
    """All per-run metrics (a)-(h) of the re-scoring plan for one trajectory.

    Inputs are 1-D arrays of equal length (one entry per trading day,
    end-of-day / post-trade state).  ``persona`` selects the MAS targets.
    ``fallback_mask`` marks parse-fallback rows, which are excluded from the
    action-based metrics (RG, trade counts) but kept in the portfolio state.
    """
    price = np.asarray(price, float)
    fv = np.asarray(fv, float)
    pv = np.asarray(pv, float)
    cash = np.asarray(cash, float)
    qty = np.asarray(qty, float)
    action = np.asarray(action).astype(str)
    n = len(price)
    if fallback_mask is None:
        fallback_mask = np.zeros(n, bool)
    fallback_mask = np.asarray(fallback_mask, bool)
    valid_row = ~fallback_mask

    out: dict = {"n_rows": n, "n_fallback": int(fallback_mask.sum()),
                 "fallback_frac": float(fallback_mask.mean()) if n else np.nan}

    # ---- cash share / MAS -------------------------------------------------
    with np.errstate(divide="ignore", invalid="ignore"):
        c = np.where(pv > 0, cash / pv, np.nan)
    out["mean_cash_share"] = float(np.nanmean(c))
    out.update(mas_metrics(c, persona))

    # ---- mispricing / resolvability / RG ----------------------------------
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.log(price / fv)
    holdings_value = np.maximum(0.0, pv - cash)
    y = v1_rationality(action, price, fv, holdings_value)
    scored = np.isfinite(y) & valid_row
    out["rg_v1"] = float(y[scored].mean() * 100) if scored.any() else np.nan
    out["rg_v1_n"] = int(scored.sum())
    is_trade_row = np.isin(action, ["BUY", "SELL"])
    for th in thetas:
        res = np.abs(x) >= th
        key = theta_key(th)
        out[f"coverage_{key}"] = float(res.mean()) if n else np.nan
        s = scored & res
        out[f"rg_{key}"] = float(y[s].mean() * 100) if s.any() else np.nan
        out[f"rg_{key}_n"] = int(s.sum())
        sa = s & is_trade_row
        out[f"rg_action_{key}"] = float(y[sa].mean() * 100) if sa.any() else np.nan
        out[f"rg_action_{key}_n"] = int(sa.sum())
        out[f"coverage_action_{key}"] = float(sa.sum() / n) if n else np.nan

    # ---- performance / activity ------------------------------------------
    out["final_value"] = float(pv[-1])
    out["return_pct"] = float((pv[-1] - initial_cash) / initial_cash * 100)
    rolling_max = np.maximum.accumulate(pv)
    with np.errstate(divide="ignore", invalid="ignore"):
        dd = pv / rolling_max - 1.0
    out["max_drawdown_pct"] = float(np.nanmin(dd) * 100)
    out["trade_count"] = int((is_trade_row & valid_row).sum())
    out["zero_trade"] = int(out["trade_count"] == 0)
    prev_qty = np.concatenate([[0.0], qty[:-1]])
    traded_value = np.abs(qty - prev_qty) * price
    out["effective_trade_count"] = int((traded_value > 1e-6).sum())
    out["turnover"] = float(traded_value.sum() / initial_cash)
    return out


# ============================================================ simulators =====
def simulate_v1_interface(price, actions, quantities, initial_cash=INITIAL_CASH):
    """Run the v1 fraction-of-side interface along a price path.

    ``actions`` : sequence of 'BUY'|'SELL'|'HOLD' (len T); ``quantities`` in
    [0, 1].  Returns (pv, cash, qty) arrays of end-of-day state.
    """
    price = np.asarray(price, float)
    T = len(price)
    pv = np.empty(T); cash_a = np.empty(T); qty_a = np.empty(T)
    cash = float(initial_cash); qty = 0.0
    for t in range(T):
        a = actions[t]; q = float(quantities[t])
        if a == "BUY" and q > 0 and cash > 0:
            spend = cash * q
            qty += spend / price[t]
            cash -= spend
        elif a == "SELL" and q > 0 and qty > 0:
            sold = qty * q
            cash += sold * price[t]
            qty -= sold
        pv[t] = cash + qty * price[t]
        cash_a[t] = cash; qty_a[t] = qty
    return pv, cash_a, qty_a


def simulate_target_share(price, targets, initial_cash=INITIAL_CASH, label_threshold=0.01):
    """Run a target-cash-share policy.

    ``targets`` : array-like of length T; each entry is a target cash share in
    [0, 1] or NaN meaning "no trade today" (the allocation drifts with price).
    Returns (pv, cash, qty, action_labels).
    """
    price = np.asarray(price, float)
    targets = np.asarray(targets, float)
    T = len(price)
    pv = np.empty(T); cash_a = np.empty(T); qty_a = np.empty(T)
    labels = np.empty(T, dtype=object)
    cash = float(initial_cash); qty = 0.0
    for t in range(T):
        value = cash + qty * price[t]
        e_pre = (qty * price[t]) / value if value > 0 else 0.0
        tgt = targets[t]
        if np.isfinite(tgt):
            tgt = float(min(1.0, max(0.0, tgt)))
            cash = tgt * value
            qty = (1.0 - tgt) * value / price[t]
        value = cash + qty * price[t]
        e_post = (qty * price[t]) / value if value > 0 else 0.0
        d = e_post - e_pre
        labels[t] = "BUY" if d > label_threshold else ("SELL" if d < -label_threshold else "HOLD")
        pv[t] = value; cash_a[t] = cash; qty_a[t] = qty
    return pv, cash_a, qty_a, labels


# =============================================================== policies ====
def baseline_trajectories(price, fv, sma20=None, sma60=None, rsi14=None,
                          thetas=THETAS, personas=PERSONAS,
                          n_random=N_RANDOM_SEEDS, seed_base=RANDOM_SEED_BASE):
    """Simulate every baseline policy on one price path.

    Returns a list of dicts with keys: policy, persona ('' if not
    persona-specific), theta (NaN if not theta-specific), random_seed (-1 if
    not random), interface, pv, cash, qty, action.
    """
    price = np.asarray(price, float)
    fv = np.asarray(fv, float)
    T = len(price)
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.log(price / fv)
    out = []

    def add_v1(policy, actions, quantities, rseed=-1):
        pv, cash, qty = simulate_v1_interface(price, actions, quantities)
        out.append(dict(policy=policy, persona="", theta=np.nan, random_seed=rseed,
                        interface="v1", pv=pv, cash=cash, qty=qty,
                        action=np.asarray(actions, dtype=object)))

    def add_target(policy, targets, persona="", theta=np.nan):
        pv, cash, qty, act = simulate_target_share(price, targets)
        out.append(dict(policy=policy, persona=persona, theta=theta, random_seed=-1,
                        interface="target", pv=pv, cash=cash, qty=qty, action=act))

    # ---- v1-interface policies ----------------------------------------
    add_v1("always_hold", ["HOLD"] * T, [0.0] * T)
    add_v1("always_buy", ["BUY"] * T, [1.0] * T)
    add_v1("always_sell", ["SELL"] * T, [1.0] * T)
    add_v1("buy_day1_hold", ["BUY"] + ["HOLD"] * (T - 1), [1.0] + [0.0] * (T - 1))
    for k in range(n_random):
        rng = np.random.default_rng(seed_base + k)
        acts = list(rng.choice(np.array(["BUY", "SELL", "HOLD"]), size=T))
        qs = rng.uniform(0.0, 1.0, size=T)
        add_v1("random", acts, qs, rseed=k)

    # ---- target-share policies ----------------------------------------
    for p in personas:
        add_target("constant_mix_v1", np.full(T, V1_TARGET[p]), persona=p)
        add_target("constant_mix_v2", np.full(T, V2_CENTRE[p]), persona=p)
    if sma20 is not None and sma60 is not None:
        s20 = np.asarray(sma20, float); s60 = np.asarray(sma60, float)
        tg = np.where(np.isfinite(s20) & np.isfinite(s60) & (s20 > s60), 0.0, 1.0)
        add_target("momentum", tg)
    if rsi14 is not None:
        r = np.asarray(rsi14, float)
        tg = np.where(r < 30, 0.0, np.where(r > 70, 1.0, np.nan))
        add_target("mean_reversion", tg)
    for th in thetas:
        vo = np.where(x < -th, 0.0, np.where(x > th, 1.0, np.nan))
        add_target("v_oracle", vo, theta=th)
        for p in personas:
            lo, hi = V2_BAND[p]
            mc = np.where(np.isfinite(vo), np.clip(vo, lo, hi), np.nan)
            add_target("mandate_conditional_oracle", mc, persona=p, theta=th)
    return out


def baseline_metric_table(price, fv, sma20=None, sma60=None, rsi14=None,
                          thetas=THETAS, personas=PERSONAS) -> pd.DataFrame:
    """Metrics for every baseline on one price path.

    Each baseline trajectory is scored once per persona for the MAS family
    (column ``mas_persona``) because MAS depends on the persona target while
    the trajectory itself may not.  Persona-specific policies (constant_mix_*,
    mandate_conditional_oracle) are scored only against their own persona.
    Random is reported per internal seed and as the mean over seeds
    (``random_seed`` = -1).
    """
    rows = []
    trajs = baseline_trajectories(price, fv, sma20, sma60, rsi14, thetas, personas)
    for tr in trajs:
        mps = [tr["persona"]] if tr["persona"] else list(personas)
        for mp in mps:
            m = compute_run_metrics(price, fv, tr["pv"], tr["cash"], tr["qty"], tr["action"],
                                    mp, thetas=thetas)
            rows.append(dict(policy=tr["policy"], persona=tr["persona"], theta=tr["theta"],
                             random_seed=tr["random_seed"], interface=tr["interface"],
                             mas_persona=mp, **m))
    df = pd.DataFrame(rows)
    rnd = df[df.policy == "random"]
    if len(rnd):
        id_cols = ["policy", "persona", "theta", "random_seed", "interface", "mas_persona"]
        num_cols = [c for c in df.columns if c not in id_cols]
        g = rnd.groupby("mas_persona", sort=False)[num_cols].mean().reset_index()
        g["policy"] = "random"; g["persona"] = ""; g["theta"] = np.nan
        g["random_seed"] = -1; g["interface"] = "v1"
        df = pd.concat([df, g[df.columns]], ignore_index=True)
    return df
