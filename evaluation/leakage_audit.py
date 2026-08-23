"""
Section 5 of the v2 plan: leakage, phase-clock and resolvability audits, run on
the RENDERED observation fields (what get_observation() returns and the prompt
renders), not on the internal DataFrame.

Layers
  L1  algebraic inversion: can any simple formula over shown fields (with a
      free multiple prior) reproduce V?  Pass: >= 99% of steps have
      |V_hat - V| / V above the noise floor (1%).
  L2  statistical surrogate (ridge, gradient-boosted trees, small MLP) from the
      contemporaneous observation vector plus 5 lags to x = log(P/V) and to V;
      held-out seeds (GroupKFold) and a held-out scenario; price-and-technicals
      -only control; shuffled-V control (selectivity).  Per phase group.
      Pass: calm OOS R2(x) <= 0.30 and sign accuracy <= 0.70 on resolvable
      steps; event phases R2 < 0.90 and MAPE(V) >= 10%.
  L2b composite phase clock: classifier of the MACRO phase class from the full
      rendered vector vs price-derived fields only.  Pass: selectivity
      (full minus price-only accuracy) <= margin (proposed 10 pp, frozen after
      the E1 calibration run).
  L4  resolvability: fraction of steps with |x| >= theta, per scenario x phase.
  (L3, the LLM probe, and L5, the observables oracle, need model calls / the
  evaluation layer and are not part of this module.)

CI usage: tests/test_leakage_ci.py calls run_audit() on the active generator.
CLI:     python -m evaluation.leakage_audit --env v1 --seeds 30 --T 200
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import warnings
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
# Cap native thread pools: HistGradientBoosting/MLP use OpenMP/BLAS and collapse
# under oversubscription when other sklearn jobs run concurrently (100x slowdowns
# observed). 2 threads per fit is plenty for these panel sizes.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
try:
    from threadpoolctl import threadpool_limits as _tpl
    _tpl(limits=2)
except Exception:  # pragma: no cover
    pass
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from evaluation.stylized_facts import V1_PHASE_MAP, MACRO_OF, CALM, DOWN, UP, RESOLUTION  # noqa: E402

THETAS = (0.03, 0.05, 0.08)
NOISE_FLOOR = 0.01
L2B_MARGIN = 0.10
PRICE_ONLY_KEYS = {"price", "SMA20", "SMA60", "SMA50", "SMA200", "RSI14", "MACD", "MACD_signal",
                   "trend_strength", "trend_regime", "ret_1", "ret_5", "ret_20"}
N_LAGS = 5


# --------------------------------------------------------------------------
# panel construction
# --------------------------------------------------------------------------
def panel_from_env(env, scenario: str, seed: int, fields: Optional[List[str]] = None,
                   phase_map: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """One row per step with the rendered numeric fields + hidden truth."""
    rows = []
    env.reset()
    T = env.n_days
    for t in range(T):
        obs = env.get_observation()
        gt = env.get_ground_truth()
        ph = env.get_scenario_phase()
        ph = (phase_map or {}).get(ph, ph)
        row = {"scenario": scenario, "seed": seed, "day": t + 1, "phase": ph,
               "V": float(gt["fundamental_value"]), "P": float(gt["price"])}
        for k, v in obs.items():
            if fields is not None and k not in fields:
                continue
            if k == "date":
                continue
            if isinstance(v, (int, float, np.integer, np.floating)):
                row[k] = float(v)
        rows.append(row)
        env.step()
    df = pd.DataFrame(rows)
    df["macro"] = df["phase"].map(MACRO_OF).fillna("calm")
    df["x"] = np.log(df["P"] / df["V"])
    return df


def v1_panel(seeds: int, T: int, fields: Optional[List[str]] = None,
             deltas=(0.85, 0.92, 0.95)) -> pd.DataFrame:
    from envs.v1.synthetic_market_v1 import SyntheticMarketEnv
    frames = []
    for s in range(seeds):
        for sc in ("flat", "bull_trap"):
            frames.append(panel_from_env(SyntheticMarketEnv(scenario=sc, n_days=T, seed=s), sc, s, fields, V1_PHASE_MAP))
        for d in deltas:
            f = panel_from_env(SyntheticMarketEnv(scenario="crash", n_days=T, seed=s, crash_discount=d), "crash", s, fields, V1_PHASE_MAP)
            f["seed"] = s * 100 + int(round(d * 100))  # distinct group per delta path
            frames.append(f)
    return pd.concat(frames, ignore_index=True)


def add_lags_and_returns(df: pd.DataFrame, feature_keys: List[str], n_lags: int = N_LAGS) -> Tuple[pd.DataFrame, List[str]]:
    df = df.sort_values(["scenario", "seed", "day"]).reset_index(drop=True)
    g = df.groupby(["scenario", "seed"], sort=False)
    out = df.copy()
    cols = list(feature_keys)
    if "price" in df.columns:
        lp = np.log(df["price"].clip(lower=1e-6))
        for h in (1, 5, 20):
            out[f"ret_{h}"] = lp - g["price"].shift(h).pipe(lambda s: np.log(s.clip(lower=1e-6)))
            cols.append(f"ret_{h}")
    for k in feature_keys:
        for L in range(1, n_lags + 1):
            out[f"{k}_lag{L}"] = g[k].shift(L)
            cols.append(f"{k}_lag{L}")
    return out, cols


# --------------------------------------------------------------------------
# L1 algebraic inversion
# --------------------------------------------------------------------------
def l1_algebraic(df: pd.DataFrame, shown_fields: List[str]) -> pd.DataFrame:
    """Candidate inversions over shown fields with a free scalar prior k:
    V_hat = k * P / PE (trailing multiple prior), V_hat = k * DPS / payout ... etc.
    The prior k is fitted on the whole panel (the most favourable case for an
    attacker); the test is whether the best candidate reproduces V."""
    cands = []
    P = df["P"].values; V = df["V"].values
    if "reported_PE" in shown_fields and "reported_PE" in df:
        cands.append(("k * P / reported_PE", P / df["reported_PE"].replace(0, np.nan).values))
    if "dividend_yield" in shown_fields and "dividend_yield" in df:
        cands.append(("k * P * dividend_yield", P * df["dividend_yield"].values))
    if "earnings_per_share" in shown_fields and "earnings_per_share" in df:
        cands.append(("k * earnings_per_share", df["earnings_per_share"].values))
    if "analyst_fair_value" in shown_fields and "analyst_fair_value" in df:
        cands.append(("k * analyst_fair_value", df["analyst_fair_value"].values))
    if "dps" in shown_fields and "dps" in df:
        cands.append(("k * dps", df["dps"].values))
    cands.append(("k * P (price itself)", P))
    rows = []
    for name, base in cands:
        ok = np.isfinite(base) & (base > 0)
        k = np.exp(np.nanmedian(np.log(V[ok]) - np.log(base[ok])))  # log-median-optimal prior
        vhat = k * base
        ape = np.abs(vhat - V) / V
        rows.append({"candidate": name, "fitted_k": round(float(k), 4),
                     "median_APE": float(np.nanmedian(ape)), "max_APE": float(np.nanmax(ape)),
                     "share_APE_above_floor": float(np.nanmean(ape > NOISE_FLOOR)),
                     "sign_acc_PE15_rule": float(np.mean(np.sign(df["reported_PE"].values - 15) == np.sign(df["x"].values)))
                     if "reported_PE" in df else np.nan})
    out = pd.DataFrame(rows).sort_values("median_APE").reset_index(drop=True)
    # Operationalisation (PREREGISTRATION_AMENDMENTS.md, A6): a candidate 'reproduces V' if its median APE is
    # below the 1% floor, or if it lands inside the floor on more steps than price itself does (+1 pp) --
    # price is within 1% of V whenever |x| < 0.01, so the raw '>= 99% of steps above the floor' rule fails
    # for any mispricing process that ever passes through zero.
    ref = out.loc[out["candidate"] == "k * P (price itself)", "share_APE_above_floor"]
    ref_share = float(ref.iloc[0]) if len(ref) else 1.0
    out["pass"] = (out["median_APE"] >= NOISE_FLOOR) & (out["share_APE_above_floor"] >= min(0.99, ref_share - 0.01))
    out.loc[out["candidate"] == "k * P (price itself)", "pass"] = out["median_APE"] >= NOISE_FLOOR
    return out


# --------------------------------------------------------------------------
# L2 surrogate
# --------------------------------------------------------------------------
def _models():
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return {"ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
            "gbt": HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6, random_state=0),
            "mlp": make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=200,
                                                                random_state=0, early_stopping=True))}


def _oos_predictions(X, y, groups, model, n_splits=5):
    from sklearn.model_selection import GroupKFold
    from sklearn.base import clone
    pred = np.full(len(y), np.nan)
    for tr, te in GroupKFold(n_splits=min(n_splits, len(np.unique(groups)))).split(X, y, groups):
        m = clone(model).fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
    return pred


def _r2(y, p):
    ok = np.isfinite(p) & np.isfinite(y)
    if ok.sum() < 10:
        return np.nan
    ss = ((y[ok] - y[ok].mean()) ** 2).sum()
    return float(1 - ((y[ok] - p[ok]) ** 2).sum() / ss) if ss > 0 else np.nan


def l2_surrogate(df: pd.DataFrame, feature_keys: List[str], theta: float = 0.05,
                 models: Optional[Dict] = None, shuffle_seed: int = 0) -> pd.DataFrame:
    """OOS (held-out seeds) R2 of x, sign accuracy on resolvable steps, MAPE of
    V_hat, per phase group and feature set (full / price-only / shuffled-V)."""
    models = models or _models()
    dfl, cols = add_lags_and_returns(df, feature_keys)
    dfl = dfl.dropna(subset=cols).reset_index(drop=True)
    price_cols = [c for c in cols if c.split("_lag")[0] in PRICE_ONLY_KEYS]
    groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    y_x = dfl["x"].to_numpy(dtype=float); y_lv = np.log(dfl["V"].to_numpy(dtype=float))
    # shuffled-V control: permute the target across groups (keeps each path's
    # own series shape but breaks the link with the features)
    rng = np.random.default_rng(shuffle_seed)
    ug = np.unique(groups); perm = dict(zip(ug, rng.permutation(ug)))
    g_ser = pd.Series(groups)
    shuffled_x = np.empty_like(y_x); shuffled_lv = np.empty_like(y_lv)
    idx_by_g = {g: np.where(groups == g)[0] for g in ug}
    for g in ug:
        src = idx_by_g[perm[g]]; dst = idx_by_g[g]
        n = min(len(src), len(dst))
        shuffled_x[dst[:n]] = y_x[src[:n]]; shuffled_lv[dst[:n]] = y_lv[src[:n]]
        if len(dst) > n:
            shuffled_x[dst[n:]] = y_x[src[-1]]; shuffled_lv[dst[n:]] = y_lv[src[-1]]
    phase_group = dfl["macro"].replace({"down-event": "event", "up-event": "event"}).to_numpy(dtype=object)
    rows = []
    for fs_name, fcols in (("full", cols), ("price_only", price_cols)):
        X = dfl[fcols].to_numpy(dtype=float)
        for mname, model in models.items():
            for tgt_name, y, ysh in (("x", y_x, shuffled_x), ("logV", y_lv, shuffled_lv)):
                p = _oos_predictions(X, y, groups, model)
                psh = _oos_predictions(X, ysh, groups, model) if fs_name == "full" else None
                for pg in ("calm", "event", "resolution", "all"):
                    m = np.ones(len(p), bool) if pg == "all" else (phase_group == pg)
                    if m.sum() < 30:
                        continue
                    row = {"feature_set": fs_name, "model": mname, "target": tgt_name, "phase_group": pg,
                           "n": int(m.sum()), "R2": _r2(y[m], p[m])}
                    if tgt_name == "x":
                        res = m & (np.abs(y_x) >= theta)
                        row["sign_acc_resolvable"] = float(np.mean(np.sign(p[res]) == np.sign(y_x[res]))) if res.sum() > 10 else np.nan
                        row["n_resolvable"] = int(res.sum())
                    else:
                        row["MAPE_V"] = float(np.mean(np.abs(np.exp(p[m]) - np.exp(y[m])) / np.exp(y[m])))
                    if psh is not None:
                        row["R2_shuffledV"] = _r2(ysh[m], psh[m])
                    rows.append(row)
    out = pd.DataFrame(rows)
    # selectivity of valuation (non-price) fields = full R2 - price-only R2
    key = ["model", "target", "phase_group"]
    po = out[out.feature_set == "price_only"][key + ["R2"]].rename(columns={"R2": "R2_price_only"})
    out = out.merge(po, on=key, how="left")
    out["selectivity_R2"] = np.where(out["feature_set"] == "full", out["R2"] - out["R2_price_only"], np.nan)
    return out


# Selectivity of the non-price fields is REPORTED (exploratory; amendment A8 withdrawn after the
# integrity review of 23 Aug 2026 -- margins chosen after seeing the data are not a gate).  The
# pre-registered absolute thresholds remain the gate and are reported as failing by construction.
L2_SELECTIVITY_R2 = 0.20     # reference only
L2_SELECTIVITY_MAPE = 0.05   # reference only
L2_SHUFFLED_MAX = 0.10


def l2_verdict(l2: pd.DataFrame, mode: str = "absolute") -> Dict[str, object]:
    """Pass rules from Section 5 applied to the BEST (max R2) full-feature model.
    mode='absolute'   : the plan's literal thresholds (calm R2 <= 0.30 & sign <= 0.70; event R2 < 0.90 & MAPE >= 10%).
    mode='selectivity': amendment A8 -- the non-price (valuation/sentiment/volume/IV) fields must not add more than
                        L2_SELECTIVITY_R2 of R2(x) in any phase group nor more than L2_SELECTIVITY_MAPE of MAPE(V) gain
                        over the price-and-technicals-only control, and the shuffled-V control must stay below
                        L2_SHUFFLED_MAX. The absolute numbers are always reported."""
    full = l2[l2.feature_set == "full"]
    best_x = full[full.target == "x"].sort_values("R2", ascending=False).groupby("phase_group").head(1).set_index("phase_group")
    best_v = full[full.target == "logV"].sort_values("MAPE_V").groupby("phase_group").head(1).set_index("phase_group")
    calm_r2 = float(best_x.loc["calm", "R2"]) if "calm" in best_x.index else np.nan
    calm_sign = float(best_x.loc["calm", "sign_acc_resolvable"]) if "calm" in best_x.index else np.nan
    ev_r2 = float(best_x.loc["event", "R2"]) if "event" in best_x.index else np.nan
    ev_mape = float(best_v.loc["event", "MAPE_V"]) if "event" in best_v.index else np.nan
    calm_ok = (not math.isnan(calm_r2)) and calm_r2 <= 0.30 and (math.isnan(calm_sign) or calm_sign <= 0.70)
    ev_ok = (math.isnan(ev_r2) or ev_r2 < 0.90) and (math.isnan(ev_mape) or ev_mape >= 0.10)
    # selectivity of the non-price fields: best model per feature set, worst phase group
    pof = l2[l2.feature_set == "price_only"]
    best_x_full = full[full.target == "x"].groupby("phase_group")["R2"].max()
    best_x_po = pof[pof.target == "x"].groupby("phase_group")["R2"].max()
    sel_by_group = (best_x_full - best_x_po.reindex(best_x_full.index)).dropna()
    sel_r2 = float(sel_by_group.max()) if len(sel_by_group) else np.nan
    best_v_full = full[full.target == "logV"].groupby("phase_group")["MAPE_V"].min()
    best_v_po = pof[pof.target == "logV"].groupby("phase_group")["MAPE_V"].min()
    gain_by_group = (best_v_po.reindex(best_v_full.index) - best_v_full).dropna()
    sel_mape = float(gain_by_group.max()) if len(gain_by_group) else np.nan
    shuffled = float(np.nanmax(full["R2_shuffledV"])) if "R2_shuffledV" in full else np.nan
    sel_ok = ((not math.isnan(sel_r2)) and sel_r2 <= L2_SELECTIVITY_R2
              and (math.isnan(sel_mape) or sel_mape <= L2_SELECTIVITY_MAPE)
              and (math.isnan(shuffled) or shuffled < L2_SHUFFLED_MAX))
    out = {"calm_best_R2_x": calm_r2, "calm_sign_acc": calm_sign, "event_best_R2_x": ev_r2,
           "event_best_MAPE_V": ev_mape, "calm_pass_absolute": bool(calm_ok), "event_pass_absolute": bool(ev_ok),
           "pass_absolute": bool(calm_ok and ev_ok), "max_selectivity_R2_x": sel_r2, "max_MAPE_gain_V": sel_mape,
           "max_R2_shuffledV": shuffled, "pass_selectivity": bool(sel_ok), "mode": mode}
    out["pass"] = out["pass_selectivity"] if mode == "selectivity" else out["pass_absolute"]
    out["calm_pass"], out["event_pass"] = out["calm_pass_absolute"], out["event_pass_absolute"]
    return out


# --------------------------------------------------------------------------
# L2b composite phase clock
# --------------------------------------------------------------------------
def l2b_phase_clock(df: pd.DataFrame, feature_keys: List[str], margin: float = L2B_MARGIN) -> Dict[str, object]:
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GroupKFold, cross_val_predict
    dfl, cols = add_lags_and_returns(df, feature_keys)
    dfl = dfl.dropna(subset=cols).reset_index(drop=True)
    price_cols = [c for c in cols if c.split("_lag")[0] in PRICE_ONLY_KEYS]
    y = dfl["macro"].to_numpy(dtype=object)
    groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    if len(np.unique(y)) < 2:
        return {"acc_full": np.nan, "acc_price_only": np.nan, "acc_day_only": np.nan,
                "selectivity": np.nan, "margin": margin, "pass": None, "n": len(y)}
    cv = GroupKFold(n_splits=min(5, len(np.unique(groups))))
    clf = lambda: HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_depth=4, random_state=0)
    acc = {}
    for name, fc in (("full", cols), ("price_only", price_cols), ("day_only", ["day"])):
        pred = cross_val_predict(clf(), dfl[fc].to_numpy(dtype=float), y, cv=cv, groups=groups)
        acc[name] = float(np.mean(pred == y))
    majority = float(pd.Series(y).value_counts(normalize=True).iloc[0])
    sel = acc["full"] - acc["price_only"]
    return {"acc_full": acc["full"], "acc_price_only": acc["price_only"], "acc_day_only": acc["day_only"],
            "majority_class": majority, "selectivity": sel, "margin": margin, "pass": bool(sel <= margin), "n": int(len(y))}


# --------------------------------------------------------------------------
# Scenario-discrimination audit (added after review D5): price/IV-only classifier
# distinguishing sustained-bull days from bull-trap mania/blow-off days and from
# calm days. A control regime that is identifiable from volatility alone would be
# a scenario clock through a non-valuation channel.
# --------------------------------------------------------------------------
def scenario_discrimination(df: pd.DataFrame, feature_keys: List[str]) -> Dict[str, object]:
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GroupKFold, cross_val_predict
    d = df[(df["scenario"].isin(["sustained_bull", "bull_trap", "flat"]))].copy()
    lab = np.where(d["scenario"] == "sustained_bull", "sustained", np.where(d["phase"].isin(["mania", "blow-off"]), "mania", "calm"))
    d["lab"] = lab
    d = d[d["lab"].isin(["sustained", "mania", "calm"])]
    dfl, cols = add_lags_and_returns(d, feature_keys)
    dfl = dfl.dropna(subset=cols).reset_index(drop=True)
    price_iv = [c for c in cols if c.split("_lag")[0] in (PRICE_ONLY_KEYS | {"implied_volatility"})]
    price_only = [c for c in cols if c.split("_lag")[0] in PRICE_ONLY_KEYS]
    y = dfl["lab"].to_numpy(dtype=object)
    groups = (dfl["scenario"].astype(str) + "-" + dfl["seed"].astype(str)).to_numpy(dtype=object)
    if len(np.unique(y)) < 2:
        return {"n": len(y)}
    cv = GroupKFold(n_splits=min(5, len(np.unique(groups))))
    out = {"n": int(len(y)), "majority": float(pd.Series(y).value_counts(normalize=True).iloc[0])}
    for name, fc in (("price_only", price_only), ("price_iv", price_iv), ("full", cols)):
        pred = cross_val_predict(HistGradientBoostingClassifier(max_iter=200, max_depth=4, random_state=0),
                                 dfl[fc].to_numpy(dtype=float), y, cv=cv, groups=groups)
        out[f"acc_{name}"] = float(np.mean(pred == y))
        m = y == "sustained"
        out[f"recall_sustained_{name}"] = float(np.mean(pred[m] == "sustained")) if m.any() else np.nan
    return out


# --------------------------------------------------------------------------
# L4 resolvability
# --------------------------------------------------------------------------
def l4_resolvability(df: pd.DataFrame, thetas=THETAS) -> pd.DataFrame:
    rows = []
    for (sc, ph), g in df.groupby(["scenario", "phase"], sort=False):
        row = {"scenario": sc, "phase": ph, "n_steps": len(g), "median_abs_x": float(np.median(np.abs(g["x"])))}
        for th in thetas:
            row[f"coverage_theta_{th}"] = float(np.mean(np.abs(g["x"]) >= th))
        rows.append(row)
    for sc, g in df.groupby("scenario", sort=False):
        row = {"scenario": sc, "phase": "ALL", "n_steps": len(g), "median_abs_x": float(np.median(np.abs(g["x"])))}
        for th in thetas:
            row[f"coverage_theta_{th}"] = float(np.mean(np.abs(g["x"]) >= th))
        rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
MAX_ROWS = 30000


def subsample_paths(panel: pd.DataFrame, max_rows: int = MAX_ROWS, seed: int = 0) -> pd.DataFrame:
    """Keep whole (scenario, seed) paths, dropping paths at random until the
    panel has at most `max_rows` rows (keeps the fits tractable in CI)."""
    if len(panel) <= max_rows:
        return panel
    keys = panel[["scenario", "seed"]].drop_duplicates().to_numpy(dtype=object)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(keys))
    per_path = len(panel) / len(keys)
    keep = set(map(tuple, keys[order[:max(1, int(max_rows / per_path))]]))
    sc = panel["scenario"].to_numpy(dtype=object); sd = panel["seed"].to_numpy(dtype=object)
    mask = np.array([(a, b) in keep for a, b in zip(sc, sd)])
    return panel[mask].reset_index(drop=True)


def run_audit(panel: pd.DataFrame, shown_fields: List[str], theta: float = 0.05,
              margin: float = L2B_MARGIN, max_rows: int = MAX_ROWS) -> Dict[str, object]:
    panel = subsample_paths(panel, max_rows)
    feature_keys = [k for k in shown_fields if k in panel.columns and k not in ("date",)]
    l1 = l1_algebraic(panel, shown_fields)
    l2 = l2_surrogate(panel, feature_keys, theta=theta)
    l2v = l2_verdict(l2)
    l2b = l2b_phase_clock(panel, feature_keys, margin=margin)
    l4 = l4_resolvability(panel)
    sd = scenario_discrimination(panel, feature_keys) if "sustained_bull" in set(panel["scenario"]) else {}
    return {"L1": l1, "L2": l2, "L2_verdict": l2v, "L2b": l2b, "L4": l4, "scenario_discrimination": sd,
            "shown_fields": feature_keys, "n_rows": int(len(panel))}


def checklist_rows(res: Dict[str, object]) -> List[Dict]:
    """Rows for items 14 and 16 of the Section 9 checklist."""
    l1_pass = bool(res["L1"]["pass"].all())
    v = res["L2_verdict"]
    best = res["L1"].iloc[0]
    stat14 = (f"L1 best inversion '{best['candidate']}' (k={best['fitted_k']}): median APE {best['median_APE']:.2%}, "
              f"{best['share_APE_above_floor']:.0%} of steps above the 1% floor; L2 absolute (reported): calm R2(x) = {v['calm_best_R2_x']:.2f}, "
              f"calm sign acc = {v['calm_sign_acc']:.2f}, event R2(x) = {v['event_best_R2_x']:.2f}, event MAPE(V) = {v['event_best_MAPE_V']:.1%}; "
              f"L2 selectivity (A8): max non-price R2 gain {v['max_selectivity_R2_x']:.2f}, max MAPE(V) gain {v['max_MAPE_gain_V']:.1%}, "
              f"shuffled-V R2 {v['max_R2_shuffledV']:.2f}")
    r14 = {"item": 14, "property": "Value leak (L1, L2; L3 separate)", "statistic": stat14,
           "criterion": "no algebraic inversion (A6); L2 absolute: calm R2 <= 0.30 & sign <= 0.70, event R2 < 0.90 & MAPE >= 10% (gate); selectivity of non-price fields reported (exploratory)",
           "pass": bool(l1_pass and v["pass"]), "n_seeds": res["n_rows"]}
    b = res["L2b"]
    r16 = {"item": 16, "property": "Composite phase clock (L2b)",
           "statistic": f"macro-class accuracy full {b['acc_full']:.1%} vs price-only {b['acc_price_only']:.1%} "
                        f"(day-only {b['acc_day_only']:.1%}; majority {b.get('majority_class', float('nan')):.1%}); selectivity {b['selectivity']:+.1%}",
           "criterion": f"selectivity <= {b['margin']:.0%}", "pass": b["pass"], "n_seeds": b["n"]}
    return [r14, r16]


def _md_table(df, floatfmt=".3f"):
    """Pipe table without the optional `tabulate` dependency."""
    cols = list(df.columns)
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return "nan" if np.isnan(v) else format(float(v), floatfmt)
        return str(v)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(fmt(r[c]) for c in cols) + " |")
    return chr(10).join(lines)


def to_markdown(res: Dict[str, object], title: str) -> str:
    L = [f"# {title}", "", f"Rendered fields audited: {', '.join('`'+k+'`' for k in res['shown_fields'])}; {res['n_rows']} steps.", ""]
    L += ["## L1 algebraic inversion", "", _md_table(res["L1"], ".4f"), ""]
    v = res["L2_verdict"]
    L += ["## L2 statistical surrogate (held-out seeds, best model per phase group)", "",
          f"Absolute (plan literal, reported): calm best R2(x) = {v['calm_best_R2_x']:.3f}, sign accuracy on resolvable steps = {v['calm_sign_acc']:.3f} -> "
          f"{'PASS' if v['calm_pass_absolute'] else 'FAIL'} (R2 <= 0.30, sign <= 0.70); event best R2(x) = {v['event_best_R2_x']:.3f}, MAPE(V) = {v['event_best_MAPE_V']:.1%} -> "
          f"{'PASS' if v['event_pass_absolute'] else 'FAIL'} (R2 < 0.90, MAPE >= 10%).", "",
          f"Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = {v['max_selectivity_R2_x']:.3f} "
          f"(worst phase group), MAPE(V) gain = {v['max_MAPE_gain_V']:.1%}, max shuffled-V R2 = {v['max_R2_shuffledV']:.3f}. "
          f"Interpretation: the absolute fail is a property of the price process (smooth V, persistent dominant x -> x is "
          f"inferable from price history), not of the valuation fields; 'hidden value' is hidden from algebra and from the "
          f"fields, NOT from price dynamics -- the rule-based baselines quantify how much a price-only policy captures.", "",
          _md_table(res["L2"].round(3)), ""]
    b = res["L2b"]
    L += ["## L2b composite phase clock", "",
          f"Macro-class accuracy: full {b['acc_full']:.1%}, price-only {b['acc_price_only']:.1%}, day-only {b['acc_day_only']:.1%}, "
          f"majority class {b.get('majority_class', float('nan')):.1%}. Selectivity = {b['selectivity']:+.1%} vs margin {b['margin']:.0%} -> "
          f"{'PASS' if b['pass'] else 'FAIL'}.", ""]
    sd = res.get("scenario_discrimination") or {}
    if sd:
        L += ["## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days", "",
              f"n = {sd.get('n')}, majority {sd.get('majority', float('nan')):.1%}; accuracy price-only {sd.get('acc_price_only', float('nan')):.1%}, "
              f"price+IV {sd.get('acc_price_iv', float('nan')):.1%}, full {sd.get('acc_full', float('nan')):.1%}; recall of sustained-bull days: "
              f"price-only {sd.get('recall_sustained_price_only', float('nan')):.1%}, price+IV {sd.get('recall_sustained_price_iv', float('nan')):.1%}, "
              f"full {sd.get('recall_sustained_full', float('nan')):.1%} (reported; no pre-registered threshold).", ""]
    L += ["## L4 resolvability (|x| >= theta)", "", _md_table(res["L4"].round(3)), ""]
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="v1", choices=["v1", "v2"])
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from agent.render import rendered_market_fields
    if a.env == "v1":
        shown = rendered_market_fields("static")
        panel = v1_panel(a.seeds, a.T)
    else:
        from envs.synthetic_market import audit_panel  # provided by the v2 generator
        shown = rendered_market_fields("v2")
        panel = audit_panel(a.seeds, a.T)
    out = a.out or os.path.join(ROOT, "docs", "env_v2", "generated", f"leakage_audit_{a.env}.md")
    res = run_audit(panel, shown)
    import pickle  # persist the computation before any rendering step can fail
    with open(out.replace(".md", ".pkl"), "wb") as fh:
        pickle.dump(res, fh)
    res["L1"].to_csv(out.replace(".md", "_L1.csv"), index=False)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_markdown(res, f"Section 5 leakage / phase-clock / resolvability audit ({a.env}, {a.seeds} seeds, T={a.T})"))
    res["L2"].to_csv(out.replace(".md", "_L2.csv"), index=False)
    res["L4"].to_csv(out.replace(".md", "_L4.csv"), index=False)
    pd.DataFrame(checklist_rows(res)).to_csv(out.replace(".md", "_checklist_rows.csv"), index=False)
    print(res["L1"].to_string()); print(res["L2_verdict"]); print(res["L2b"]); print("written", out)
