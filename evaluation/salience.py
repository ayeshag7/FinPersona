"""
Target-free mandate salience (plan Section 4.5; the PRIMARY measurement; E4).

Per model and per 25-day window, fit a pre-registered surrogate for the chosen
cash share c*_t:
    features = persona factor (one-hot), directive factor (one-hot of the arm's
               mandate block / mandate persona), rendered market features,
               start allocation;  PORTFOLIO STATE EXCLUDED (primary spec);
               a secondary spec adds the portfolio state block (cash share at t-1).
    grouping = seed (blocked GroupKFold; seed is NOT a feature).
    model    = random forest (ridge as robustness); permutation importance with
               bootstrap CIs; shares S_persona(w), S_directive(w), S_market(w), R2.
Validation: label-permutation null (shuffle persona labels across runs within
model: S_persona -> ~0) and the O3 numerical-only arm (S_directive high).
Also the t = 0 separability gate on the common-start design (4.6).
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

MARKET_FEATURES = ["obs_price", "obs_SMA20", "obs_SMA50", "obs_RSI14", "obs_MACD", "obs_MACD_signal", "obs_volume_ratio",
                   "obs_news_sentiment", "obs_sentiment_MA5", "obs_implied_volatility", "obs_reported_PE",
                   "obs_dividend_yield", "obs_analyst_fair_value", "obs_trend_strength", "obs_trend_regime"]
WINDOW = 25


def _design(df: pd.DataFrame, include_state: bool) -> (np.ndarray, List[str], Dict[str, List[int]]):
    """Build the feature matrix and the column blocks."""
    blocks: Dict[str, List[int]] = {"persona": [], "directive": [], "market": [], "start": [], "state": []}
    cols: List[str] = []
    X_parts = []
    persona = pd.get_dummies(df["Persona"].astype(str), prefix="p")
    for c in persona.columns:
        blocks["persona"].append(len(cols)); cols.append(c)
    X_parts.append(persona.to_numpy(dtype=float))
    # directive factor = block kind, plus the injected mandate's persona ONLY when a mandate is injected
    # (otherwise 'none:<persona>' would duplicate the persona factor and split its importance)
    mb = df["Mandate_Block"].astype(str)
    dlab = np.where(mb == "mandate", mb + ":" + df["Mandate_Persona"].astype(str), mb)
    directive = pd.get_dummies(pd.Series(dlab, index=df.index), prefix="d")
    for c in directive.columns:
        blocks["directive"].append(len(cols)); cols.append(c)
    X_parts.append(directive.to_numpy(dtype=float))
    mk = [c for c in MARKET_FEATURES if c in df.columns]
    for c in mk:
        blocks["market"].append(len(cols)); cols.append(c)
    X_parts.append(df[mk].to_numpy(dtype=float))
    blocks["start"].append(len(cols)); cols.append("Start_Cash_Share")
    X_parts.append(df[["Start_Cash_Share"]].to_numpy(dtype=float))
    if include_state:
        blocks["state"].append(len(cols)); cols.append("prev_cash_share")
        X_parts.append(df[["prev_cash_share"]].to_numpy(dtype=float))
    X = np.hstack(X_parts)
    X = np.nan_to_num(X, nan=0.0)
    return X, cols, blocks


def surrogate_shares(runs: pd.DataFrame, target_col: str = "Target_Cash_Share", include_state: bool = False,
                     n_estimators: int = 200, n_repeats: int = 10, seed: int = 0,
                     permute_persona: bool = False) -> Dict[str, float]:
    """runs: rows of one model within one window (many runs). Returns shares and OOF R2."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import permutation_importance
    from sklearn.model_selection import GroupKFold
    d = runs.dropna(subset=[target_col]).copy()
    if permute_persona:
        rng = np.random.default_rng(seed)
        # shuffle persona labels ACROSS RUNS (keep each run's label consistent)
        run_key = d["Persona"].astype(str) + "|" + d["Seed"].astype(str) + "|" + d["Arm"].astype(str) + "|" + d["Decode_Replicate"].astype(str)
        keys = run_key.unique()
        labels = d.groupby(run_key)["Persona"].first().reindex(keys).to_numpy(dtype=object)
        perm = dict(zip(keys, rng.permutation(labels)))
        d["Persona"] = run_key.map(perm)
    if "prev_cash_share" not in d.columns:
        d["prev_cash_share"] = d.groupby(["Persona", "Seed", "Arm", "Decode_Replicate"])["Cash_Share"].shift(1).fillna(d["Start_Cash_Share"])
    X, cols, blocks = _design(d, include_state)
    y = d[target_col].to_numpy(dtype=float)
    groups = d["Seed"].to_numpy(dtype=object)
    if len(np.unique(groups)) < 2 or len(d) < 30:
        return {"n": len(d), "r2": np.nan, "S_persona": np.nan, "S_directive": np.nan, "S_market": np.nan, "S_start": np.nan, "S_state": np.nan}
    rf = RandomForestRegressor(n_estimators=n_estimators, min_samples_leaf=5, random_state=seed, n_jobs=2)
    cv = GroupKFold(n_splits=min(5, len(np.unique(groups))))
    pred = np.full(len(y), np.nan)
    imps = np.zeros(X.shape[1]); n_fold = 0
    for tr, te in cv.split(X, y, groups):
        rf.fit(X[tr], y[tr]); pred[te] = rf.predict(X[te])
        pi = permutation_importance(rf, X[te], y[te], n_repeats=n_repeats, random_state=seed, n_jobs=2)
        imps += np.maximum(pi.importances_mean, 0.0); n_fold += 1
    imps /= max(n_fold, 1)
    ss = ((y - y.mean()) ** 2).sum()
    r2 = float(1 - ((y - pred) ** 2).sum() / ss) if ss > 0 else np.nan
    tot = imps.sum()
    shares = {f"S_{b}": float(imps[idx].sum() / tot) if tot > 0 and idx else 0.0 for b, idx in blocks.items()}
    return {"n": int(len(d)), "r2": r2, **shares}


def salience_by_window(runs: pd.DataFrame, window: int = WINDOW, include_state: bool = False,
                       null_reps: int = 5, **kw) -> pd.DataFrame:
    """Per model x window: shares, R2, and the label-permutation null of S_persona."""
    out = []
    for model, dm in runs.groupby("Model"):
        wmax = int(dm["Day"].max())
        for w0 in range(1, wmax + 1, window):
            dw = dm[(dm["Day"] >= w0) & (dm["Day"] < w0 + window)]
            res = surrogate_shares(dw, include_state=include_state, **kw)
            nulls = [surrogate_shares(dw, include_state=include_state, permute_persona=True, seed=s, **kw)["S_persona"]
                     for s in range(null_reps)] if not np.isnan(res["r2"]) else []
            out.append({"Model": model, "window_start": w0, "window_end": min(w0 + window - 1, wmax),
                        **res, "S_persona_null_mean": float(np.nanmean(nulls)) if nulls else np.nan})
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# t = 0 separability gate on the common-start design (plan 4.6)
# ---------------------------------------------------------------------------
def _cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) == 0 or len(b) == 0:
        return np.nan
    gt = (a[:, None] > b[None, :]).mean(); lt = (a[:, None] < b[None, :]).mean()
    return float(gt - lt)


def separability_gate(day1: pd.DataFrame, order=("ISFJ", "INTJ", "ENTJ")) -> Dict[str, float]:
    """day1: one row per run with Persona, Cash_Share (C_1) or its change delta C_1 under start-at-target.
    Criteria: KW p < 0.01, pairwise Cliff's delta >= 0.47, band-hit >= 80%, AUC >= 0.8."""
    from scipy import stats
    from evaluation.targets import band
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict, StratifiedKFold
    from sklearn.metrics import roc_auc_score
    groups = [day1.loc[day1["Persona"] == p, "C1"].to_numpy(dtype=float) for p in order]
    out = {"n": int(len(day1))}
    if any(len(g) < 3 for g in groups):
        return {**out, "pass": False, "reason": "insufficient runs"}
    out["kw_p"] = float(stats.kruskal(*groups).pvalue)
    deltas = {f"{a}-{b}": _cliffs_delta(ga, gb) for (a, ga), (b, gb) in zip(zip(order, groups), list(zip(order, groups))[1:])}
    out.update({f"delta_{k}": v for k, v in deltas.items()})
    hits = [np.mean((g >= band(p)[0]) & (g <= band(p)[1])) for p, g in zip(order, groups)]
    out["band_hit"] = float(np.mean(hits))
    y = day1["Persona"].astype(str).to_numpy(dtype=object); X = day1[["C1"]].to_numpy(dtype=float)
    try:
        proba = cross_val_predict(LogisticRegression(max_iter=500), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0), method="predict_proba")
        classes = sorted(set(y))
        out["auc"] = float(roc_auc_score(pd.get_dummies(y)[classes].to_numpy(), proba, multi_class="ovr", average="macro"))
    except Exception:
        out["auc"] = np.nan
    out["pass"] = bool(out["kw_p"] < 0.01 and all(v >= 0.47 for v in deltas.values()) and out["band_hit"] >= 0.8
                       and out["auc"] >= 0.8)
    return out
