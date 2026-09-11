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

import json
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
                     permute_persona: bool = False, groups_col: str = "Seed") -> Dict[str, float]:
    """runs: rows of one model within one window (many runs). Returns shares and OOF R2.
    `groups_col` names the cross-validation blocks (default the seed; the seed-cluster bootstrap passes the original
    seed of each resampled copy, so a seed drawn twice stays in one fold -- PREREG_PHASE_8_ADDENDUM.md 18)."""
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
    groups = d[groups_col].to_numpy(dtype=object)
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


NO_PERSONA_TEXT = ("NONE", "TRADER", "O3_conservative", "O3_aggressive")
# a run is identified by every factor that separates one run from another -- the scenario and its crash discount and
# the start design included: the pilot reused seed 42 across three scenarios, and without Scenario three runs collapsed
# into one (a first identification table read 12 runs where the pilot has 36)
RUN_KEYS = ("Model", "Persona", "Arm", "Scenario", "Crash_Discount", "Start_Design", "Seed", "Decode_Replicate")


def _blocks_run_level(runs: pd.DataFrame):
    """The persona (P), directive (D) and start (S) blocks, one row per run, as `_design` builds them."""
    keys = [k for k in RUN_KEYS if k in runs.columns]
    r = runs.drop_duplicates(subset=keys).reset_index(drop=True)
    P = pd.get_dummies(r["Persona"].astype(str), prefix="p").to_numpy(dtype=float)
    mb = r["Mandate_Block"].astype(str)
    dlab = np.where(mb == "mandate", mb + ":" + r["Mandate_Persona"].astype(str), mb)
    D = pd.get_dummies(pd.Series(dlab), prefix="d").to_numpy(dtype=float)
    S = r[["Start_Cash_Share"]].to_numpy(dtype=float)
    return r, {"persona": P, "directive": D, "start": S}


def _rank(X: np.ndarray) -> int:
    if X.size == 0:
        return 0
    Xc = X - X.mean(axis=0, keepdims=True)
    return int(np.linalg.matrix_rank(Xc, tol=1e-9 * max(1.0, float(np.abs(Xc).max()))))


def identification_check(runs: pd.DataFrame) -> Dict[str, object]:
    """v2.1 Phase 8 (E8.4, weakness 55; PREREG_PHASE_8.md 4).  The salience shares are identified only if
    (i) every block varies (rank >= 1 after centring), (ii) no block lies in the span of the others
    (rank[P, D, S] = rank P + rank D + rank S), (iii) every run is on the common-start design, and (iv) the reference
    levels are present: a run with no persona text, and a run whose directive's persona differs from its persona or
    that shows no directive.  Returns the verdict, each clause, the ranks, the R^2 of each block on the other two, and
    the largest canonical correlation between each pair of blocks -- the collinearity SHOWN, not described."""
    r, B = _blocks_run_level(runs)
    ranks = {k: _rank(v) for k, v in B.items()}
    ranks["all"] = _rank(np.hstack(list(B.values())))
    c1_registered = all(ranks[k] >= 1 for k in B)
    # PREREG_PHASE_8_ADDENDUM.md 10: AS REGISTERED, clause (i) asks the START block to vary while clause (iii) requires a
    # common start, under which it cannot -- no design could ever pass.  The reading adopted: (i) applies to the persona
    # and directive blocks; at common start the start block is constant by design and its share is not applicable.  The
    # registered verdict is returned beside, every time.
    c1 = ranks["persona"] >= 1 and ranks["directive"] >= 1
    c2 = ranks["all"] == sum(ranks[k] for k in B)
    c3 = bool((r["Start_Design"].astype(str) == "common").all()) if "Start_Design" in r else False
    no_text = r["Persona"].astype(str).isin(NO_PERSONA_TEXT)
    other = (r["Mandate_Block"].astype(str) != "mandate") | (r["Mandate_Persona"].astype(str) != r["Persona"].astype(str))
    c4 = bool(no_text.any() and (other & ~no_text).any())
    centred = {k: v - v.mean(axis=0, keepdims=True) for k, v in B.items()}
    r2, cc = {}, {}
    for k, Y in centred.items():
        Xo = np.hstack([v for kk, v in centred.items() if kk != k])
        sst = float((Y ** 2).sum())
        if sst <= 0 or Xo.size == 0:
            r2[k] = float("nan"); continue
        beta, *_ = np.linalg.lstsq(Xo, Y, rcond=None)
        r2[k] = float(1 - ((Y - Xo @ beta) ** 2).sum() / sst)
    names = list(centred)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            Qa = np.linalg.svd(centred[a], full_matrices=False)[0][:, :max(ranks[a], 0)]
            Qb = np.linalg.svd(centred[b], full_matrices=False)[0][:, :max(ranks[b], 0)]
            cc[f"{a}~{b}"] = float(np.linalg.svd(Qa.T @ Qb, compute_uv=False).max()) if Qa.size and Qb.size else float("nan")
    failing = [n for n, ok in (("i_persona_and_directive_vary", c1), ("ii_no_block_in_span_of_others", c2),
                               ("iii_common_start", c3), ("iv_reference_levels_present", c4)) if not ok]
    failing_reg = [n for n, ok in (("i_every_block_varies", c1_registered), ("ii_no_block_in_span_of_others", c2),
                                   ("iii_common_start", c3), ("iv_reference_levels_present", c4)) if not ok]
    return {"identified": bool(c1 and c2 and c3 and c4), "failing_clauses": failing,
            "identified_as_registered": bool(c1_registered and c2 and c3 and c4), "failing_clauses_as_registered": failing_reg,
            "clauses": {"i": c1, "ii": c2, "iii": c3, "iv": c4}, "clause_i_as_registered": c1_registered,
            "start_share_applicable": ranks["start"] >= 1, "ranks": ranks, "n_runs": int(len(r)),
            "r2_block_on_others": r2, "max_canonical_corr": cc,
            "personas": sorted(set(r["Persona"].astype(str))), "arms": sorted(set(r["Arm"].astype(str))) if "Arm" in r else [],
            "start_designs": sorted(set(r["Start_Design"].astype(str))) if "Start_Design" in r else []}


_SHARE_KEYS = ("S_persona", "S_directive", "S_market", "S_start", "S_state", "r2")


def _init_threads():
    """Process-pool initializer: sklearn's inner parallelism on threads (a spawned process per call on Windows re-imports
    sklearn, which made the refits crawl); with fixed random states only the order of float sums changes."""
    from joblib import parallel_config
    parallel_config(backend="threading").__enter__()


def _boot_frame(dw: pd.DataFrame, pick) -> pd.DataFrame:
    """One seed-cluster resample: each drawn copy's `Seed` relabelled `s#j`, so its runs stay distinct runs (the lag and
    permutation keys), and `Boot_Group` = the ORIGINAL seed, so every copy of a seed falls in one cross-validation fold.
    Relabelling alone put identical copies in train and test (PREREG_PHASE_8_ADDENDUM.md 18)."""
    parts = []
    for j, s in enumerate(pick):
        part = dw[dw["Seed"] == s].copy()
        part["Seed"] = f"{s}#{j}"
        part["Boot_Group"] = s
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def _boot_refit(args) -> Dict[str, float]:
    dw, include_state, pick, refit_seed, kw = args
    res = surrogate_shares(_boot_frame(dw, pick), include_state=include_state, seed=refit_seed, groups_col="Boot_Group", **kw)
    return {k: res.get(k, np.nan) for k in _SHARE_KEYS}


def _bootstrap_shares(dw: pd.DataFrame, include_state: bool, n_boot: int, seed: int, n_jobs: int = 1, **kw) -> Dict[str, tuple]:
    """Cluster bootstrap by seed (weakness 67): resample seeds with replacement, keep every copy of a seed in one
    cross-validation fold (`_boot_frame`), refit; percentile 95 % interval per share.  Every resample is drawn up front in
    the order the sequential loop draws it and every refit has its own seed, so the draws are the same for any
    `n_jobs`; `n_jobs > 1` runs the refits in a process pool."""
    rng = np.random.default_rng(seed)
    seeds = np.array(sorted(dw["Seed"].unique(), key=str), dtype=object)
    picks = [rng.choice(seeds, len(seeds), replace=True) for _ in range(n_boot)]
    tasks = [(dw, include_state, picks[b], seed + b, kw) for b in range(n_boot)]
    if n_jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=n_jobs, initializer=_init_threads) as ex:
            results = list(ex.map(_boot_refit, tasks))
    else:
        results = [_boot_refit(t) for t in tasks]
    draws = {k: [r[k] for r in results] for k in _SHARE_KEYS}
    return {k: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))) if np.isfinite(v).any() else (np.nan, np.nan)
            for k, v in ((k, np.asarray(v, float)) for k, v in draws.items())}


def salience_by_window(runs: pd.DataFrame, window: int = WINDOW, include_state: bool = False,
                       null_reps: int = 5, identification: str = "v2", n_boot: int = 200, n_jobs: int = 1, **kw) -> pd.DataFrame:
    """Per model x window: shares, R2, and the label-permutation null of S_persona.

    `identification="v2"` (default) is the published behaviour.  `"v2_1"` (v2.1 Phase 8, E8.4) evaluates
    `identification_check` first and returns NOT IDENTIFIED rows, with the failing clauses and no shares, when the
    design cannot separate the blocks (under start-at-target it never can); when identified it adds a cluster-bootstrap
    95 % interval by seed (`n_boot` refits) to every share."""
    if identification not in ("v2", "v2_1"):
        raise ValueError(f"identification must be 'v2' or 'v2_1', got {identification!r}")
    chk = None
    if identification == "v2_1":
        chk = identification_check(runs)
        if not chk["identified"]:
            return pd.DataFrame([{"Model": m, "status": "NOT IDENTIFIED", "failing_clauses": ",".join(chk["failing_clauses"]),
                                  "identified_as_registered": chk["identified_as_registered"],
                                  "n_runs": chk["n_runs"], "ranks": json.dumps(chk["ranks"]),
                                  "start_designs": ",".join(chk["start_designs"])} for m in sorted(set(runs["Model"]))])
    out = []
    for model, dm in runs.groupby("Model"):
        wmax = int(dm["Day"].max())
        for w0 in range(1, wmax + 1, window):
            dw = dm[(dm["Day"] >= w0) & (dm["Day"] < w0 + window)]
            res = surrogate_shares(dw, include_state=include_state, **kw)
            nulls = [surrogate_shares(dw, include_state=include_state, permute_persona=True, seed=s, **kw)["S_persona"]
                     for s in range(null_reps)] if not np.isnan(res["r2"]) else []
            row = {"Model": model, "window_start": w0, "window_end": min(w0 + window - 1, wmax),
                   **res, "S_persona_null_mean": float(np.nanmean(nulls)) if nulls else np.nan}
            if identification == "v2_1":
                row["status"] = "IDENTIFIED"
                row["identified_as_registered"] = chk["identified_as_registered"]
                if not chk["start_share_applicable"]:
                    row["S_start"] = np.nan              # constant at common start: not a share (addendum 10)
                if not np.isnan(res["r2"]) and n_boot > 0:
                    for k, (lo, hi) in _bootstrap_shares(dw, include_state, n_boot, kw.get("seed", 0), n_jobs=n_jobs,
                                                         **{kk: v for kk, v in kw.items() if kk != "seed"}).items():
                        row[f"{k}_lo"], row[f"{k}_hi"] = lo, hi
            out.append(row)
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
