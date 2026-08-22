"""
t = 0 separability gate on the v1 FinPersona-Bench data (v2 plan, Section 4.6).

Question: are personas behaviourally distinguishable on day 1 (before any drift)?

Run from the repo root:
    python -m evaluation.separability_gate

Inputs (read-only):
    results_april/<modeldir>_200/<model>/{flat,bull_trap}/seed<s>/<P>_<agent>_<sc>_seed<s>.csv
    results_april/<modeldir>_200/<model>/crash/discount<d>/seed<s>/<P>_<agent>_crash_seed<s>_discount<d>.csv
    results_may/{google/gemma-2-9b-it, google/gemma-3-4b-it, Qwen/Qwen2.5-7B-Instruct, meta-llama/Llama-3.1-8B-Instruct}/...
    results_ocean/{claude-sonnet-4-6, gemini-2.5-flash, gpt-4o-mini}/...   (O1/O2 all scenarios, O3 flat only)

Outputs (docs/env_v2/generated/):
    e0_gate_v1_per_model.csv            one row per (model, agent_type) + pooled rows
    e0_gate_v1_per_model_scenario.csv   one row per (model, agent_type, scenario) + pooled rows
    e0_gate_v1_ocean.csv                OCEAN O1-vs-O2 and O3cons-vs-O3aggr (ceiling) two-group stats
    e0_gate_v1_day1_actions.csv         day-1 action distribution per persona + chi-square p
    e0_gate_v1_runs_day1.csv            run-level day-1 table used for everything above
    E0_SEPARABILITY_GATE_V1.md          readable report

Definitions
    C_t      = Cash / Portfolio_Value at the end of day t (after the day's trade).
    C_1      = C_t for the row with Date == "Day-1".
    Units    = runs = (model, persona, agent_type, scenario, seed[, crash discount]) cells.
    Cliff's delta is signed so that positive = the MORE CONSERVATIVE persona holds MORE cash.
    Parse-fallback rows (Rationale starts with "Error after 3 attempts") are counted and excluded.

Gate criteria (pre-registered thresholds from the v2 plan):
    ordering   Kruskal-Wallis p < 0.01 AND every pairwise Cliff's delta >= 0.47
    band-hit   >= 80 % of runs have C_1 inside the persona's v2 band
    AUC        persona decodable from C_1 alone, macro one-vs-rest AUC >= 0.8
               (PASS flag uses the 5-fold stratified-CV multinomial logistic regression AUC;
                the in-sample sign-based one-vs-rest AUCs are reported alongside)
    surrogate  random-forest persona share >= 0.5 AND out-of-fold R2 >= 0.5

Surrogate (Section 4.5 protocol, applied to day 1):
    RandomForestRegressor(300 trees, random_state=0) predicting C_1 from persona one-hot, agent_type,
    scenario one-hot and the 12 rendered day-1 market fields. GroupKFold(5) by seed; OOF R2 on the
    concatenated held-out predictions; permutation importance (20 repeats, MSE increase, computed on each
    held-out fold and averaged over folds -- identical in definition to
    sklearn.inspection.permutation_importance(scoring="neg_mean_squared_error") but evaluated in one
    batched predict call because per-call overhead dominates on small folds). Persona share = sum of the
    persona one-hot importances / sum of all importances, negatives clipped at 0.
    Label-permutation null: persona labels shuffled across runs within the group, 20 shuffles, each
    evaluated on one rotating held-out fold with the same protocol (100 trees); null share mean reported.
    Scenario-level surrogates use 100 trees (data-poor, 15 runs per group); the tree count is
    written to the `rf_n_trees` column of every row.
"""
from __future__ import annotations

import re
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "env_v2" / "generated"
RANDOM_STATE = 0
N_TREES = 300
N_TREES_SCENARIO = 100
N_TREES_NULL = 100
N_NULL = 20
N_PERM_REPEATS = 20

APRIL_DIRS = [
    "claude_haiku_4_5_200", "claude_opus_4_6_200", "claude_sonnet_4_6_200", "deepseek_chat_200",
    "gemini_2_5_flash_200", "gemini_2_5_pro_200", "gemini_3_1_pro_preview_200", "gpt_4_1_200",
    "gpt_4_1_mini_200", "gpt_4o_200", "gpt_4o_mini_200", "gpt_5_4_200", "gpt_5_4_mini_200",
    "gpt_5_mini_200",
]
MAY_DIRS = [
    "results_may/google/gemma-2-9b-it", "results_may/google/gemma-3-4b-it",
    "results_may/Qwen/Qwen2.5-7B-Instruct", "results_may/meta-llama/Llama-3.1-8B-Instruct",
]
OCEAN_DIRS = ["results_ocean/claude-sonnet-4-6", "results_ocean/gemini-2.5-flash", "results_ocean/gpt-4o-mini"]

MBTI = ["ISFJ", "INTJ", "ENTJ"]               # conservative, balanced, aggressive
PAIRS = [("ISFJ", "INTJ"), ("INTJ", "ENTJ"), ("ISFJ", "ENTJ")]   # (more conservative, less conservative)
V1_TARGET = {"ISFJ": 1.0, "INTJ": 0.5, "ENTJ": 0.2,
             "O1_conservative": 1.0, "O2_aggressive": 0.2, "O3_conservative": 1.0, "O3_aggressive": 0.2}
RISK_CAT = {"ISFJ": "conservative", "INTJ": "balanced", "ENTJ": "aggressive",
            "O1_conservative": "conservative", "O2_aggressive": "aggressive",
            "O3_conservative": "conservative", "O3_aggressive": "aggressive"}
V2_BAND = {"conservative": (0.70, 0.90, 0.80), "balanced": (0.40, 0.60, 0.50), "aggressive": (0.00, 0.20, 0.10)}
MARKET = ["Price", "SMA20", "SMA60", "RSI14", "MACD", "Volume_Ratio", "Implied_Volatility",
          "Reported_PE", "Dividend_Yield", "Trend_Strength", "Trend_Regime", "Sentiment"]
USECOLS = ["Date", "Model", "MBTI", "Agent_Type", "Scenario", "Seed", "Crash_Discount", "Portfolio_Value",
           "Cash", "Action", "Rationale"] + MARKET
FNAME_RE = re.compile(r"^(?P<persona>[A-Z]{4}|O\d_[a-z]+)_(?P<agent>static|memory)_(?P<scenario>flat|bull_trap|crash)"
                      r"_seed(?P<seed>\d+)(?:_discount(?P<disc>[\d.]+))?\.csv$")


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------------------------
# data loading
# --------------------------------------------------------------------------------------------
def discover() -> list[tuple[str, str, Path]]:
    """Return (family, model_label, csv_path) for every run file."""
    items = []
    for d in APRIL_DIRS:
        base = REPO / "results_april" / d
        label = d[:-4] if d.endswith("_200") else d
        for p in base.rglob("*.csv"):
            if FNAME_RE.match(p.name):
                items.append(("mbti", label, p))
    for d in MAY_DIRS:
        base = REPO / d
        label = base.name
        for p in base.rglob("*.csv"):
            if FNAME_RE.match(p.name):
                items.append(("mbti", label, p))
    for d in OCEAN_DIRS:
        base = REPO / d
        label = base.name
        for p in base.rglob("*.csv"):
            if FNAME_RE.match(p.name):
                items.append(("ocean", label, p))
    return items


def load_runs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load every run; return (day-level frame for days 1-5, inventory frame)."""
    items = discover()
    rows, inv = [], []
    models = sorted({(f, m) for f, m, _ in items}, key=lambda x: (x[0], x[1]))
    for fam, model in models:
        t0 = time.time()
        paths = [p for f, m, p in items if f == fam and m == model]
        n_err_rows = n_missing_day1 = n_files = n_bad = 0
        for p in sorted(paths):
            md = FNAME_RE.match(p.name).groupdict()
            try:
                df = pd.read_csv(p, usecols=lambda c: c in USECOLS)
            except Exception as e:  # noqa: BLE001
                n_bad += 1
                log(f"    could not read {p}: {e}")
                continue
            n_files += 1
            if "Date" not in df.columns or len(df) == 0:
                n_bad += 1
                continue
            day = df["Date"].astype(str).str.extract(r"(\d+)")[0]
            day = pd.to_numeric(day, errors="coerce")
            if day.isna().all():
                day = pd.Series(np.arange(1, len(df) + 1), index=df.index, dtype=float)
            df = df.assign(day=day)
            rat = df["Rationale"].astype(str) if "Rationale" in df.columns else pd.Series("", index=df.index)
            err = rat.str.startswith("Error after 3 attempts")
            n_err_rows += int(err.sum())
            df = df.loc[~err]
            df = df.loc[df["day"].between(1, 5)]
            if not (df["day"] == 1).any():
                n_missing_day1 += 1
            for _, r in df.iterrows():
                pv = float(r["Portfolio_Value"]) if pd.notna(r["Portfolio_Value"]) else np.nan
                cash = float(r["Cash"]) if pd.notna(r["Cash"]) else np.nan
                rows.append({
                    "family": fam, "model": model, "persona": md["persona"], "agent_type": md["agent"],
                    "scenario": md["scenario"], "seed": int(md["seed"]),
                    "discount": float(md["disc"]) if md["disc"] else np.nan,
                    "run_id": f"{model}|{md['persona']}|{md['agent']}|{md['scenario']}|{md['seed']}|{md['disc'] or ''}",
                    "day": int(r["day"]), "cash_share": cash / pv if pv and pv > 0 else np.nan,
                    "action": str(r["Action"]).strip().upper() if pd.notna(r["Action"]) else "NA",
                    **{c: pd.to_numeric(r[c], errors="coerce") if c in df.columns else np.nan for c in MARKET},
                })
        inv.append({"family": fam, "model": model, "files": n_files, "unreadable": n_bad,
                    "error_rows_excluded": n_err_rows, "runs_missing_day1": n_missing_day1})
        log(f"  loaded {fam:5s} {model:28s} files={n_files:4d} err_rows={n_err_rows:4d} "
            f"missing_day1={n_missing_day1} ({time.time()-t0:.1f}s)")
    days = pd.DataFrame(rows)
    return days, pd.DataFrame(inv)


# --------------------------------------------------------------------------------------------
# statistics helpers
# --------------------------------------------------------------------------------------------
def cliffs_delta(x, y) -> float:
    """P(x > y) - P(x < y); positive if x tends to be larger."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x[~np.isnan(x)]; y = y[~np.isnan(y)]
    if len(x) == 0 or len(y) == 0:
        return np.nan
    d = x[:, None] - y[None, :]
    return float((d > 0).mean() - (d < 0).mean())


def mwu_p(x, y) -> float:
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x[~np.isnan(x)]; y = y[~np.isnan(y)]
    if len(x) == 0 or len(y) == 0:
        return np.nan
    if np.all(x == x[0]) and np.all(y == y[0]) and x[0] == y[0]:
        return 1.0
    try:
        return float(stats.mannwhitneyu(x, y, alternative="two-sided").pvalue)
    except ValueError:
        return np.nan


def kw_p(groups) -> float:
    groups = [np.asarray(g, float) for g in groups]
    groups = [g[~np.isnan(g)] for g in groups if len(g) > 0]
    groups = [g for g in groups if len(g) > 0]
    if len(groups) < 2:
        return np.nan
    allv = np.concatenate(groups)
    if np.all(allv == allv[0]):
        return 1.0   # no variation at all: cannot reject
    try:
        return float(stats.kruskal(*groups).pvalue)
    except ValueError:
        return np.nan


def safe_auc(y_bin, score) -> float:
    y_bin = np.asarray(y_bin, bool); score = np.asarray(score, float)
    ok = ~np.isnan(score)
    y_bin, score = y_bin[ok], score[ok]
    if len(y_bin) == 0 or y_bin.all() or (~y_bin).all():
        return np.nan
    return float(roc_auc_score(y_bin, score))


def lr_cv_macro_auc(c1, persona, classes) -> float:
    """Multinomial logistic regression on C_1 alone, stratified 5-fold CV, macro one-vs-rest AUC."""
    c1 = np.asarray(c1, float); persona = np.asarray(persona, object)
    ok = ~np.isnan(c1)
    c1, persona = c1[ok], persona[ok]
    present = [c for c in classes if (persona == c).sum() > 0]
    if len(present) < 2:
        return np.nan
    counts = [(persona == c).sum() for c in present]
    n_splits = int(min(5, min(counts)))
    if n_splits < 2:
        return np.nan
    if np.all(c1 == c1[0]):
        return 0.5
    X = c1.reshape(-1, 1)
    y = np.array([present.index(p) for p in persona])
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    clf = LogisticRegression(C=1.0, max_iter=2000)
    try:
        proba = cross_val_predict(clf, X, y, cv=skf, method="predict_proba")
    except Exception:  # noqa: BLE001
        return np.nan
    if proba.shape[1] != len(present):
        return np.nan
    if len(present) == 2:
        return float(roc_auc_score(y, proba[:, 1]))
    return float(roc_auc_score(y, proba, multi_class="ovr", average="macro", labels=list(range(len(present)))))


def band_of(persona):
    lo, hi, _ = V2_BAND[RISK_CAT[persona]]
    return lo, hi


def in_band(persona, c):
    lo, hi = band_of(persona)
    return (c >= lo - 1e-12) & (c <= hi + 1e-12)


def point_hit(persona, c):
    return np.abs(c - V1_TARGET[persona]) <= 0.10 + 1e-12


# --------------------------------------------------------------------------------------------
# surrogate (random forest) persona share
# --------------------------------------------------------------------------------------------
def build_features(d: pd.DataFrame, personas: list[str]):
    cols = []
    X = []
    for p in personas:
        X.append((d["persona"].values == p).astype(float)); cols.append(f"persona_{p}")
    X.append((d["agent_type"].values == "memory").astype(float)); cols.append("agent_type_memory")
    for s in ["flat", "bull_trap", "crash"]:
        X.append((d["scenario"].values == s).astype(float)); cols.append(f"scenario_{s}")
    for m in MARKET:
        v = pd.to_numeric(d[m], errors="coerce").astype(float).values
        if np.isnan(v).any():
            med = np.nanmedian(v) if not np.isnan(v).all() else 0.0
            v = np.where(np.isnan(v), med, v)
        X.append(v); cols.append(m)
    X = np.column_stack(X)
    persona_idx = [i for i, c in enumerate(cols) if c.startswith("persona_")]
    return X, cols, persona_idx


def perm_importance_batched(model, X, y, n_repeats, rng) -> np.ndarray:
    """Permutation importance = MSE(permuted) - MSE(baseline), averaged over repeats (one batched predict)."""
    n, p = X.shape
    base = float(np.mean((model.predict(X) - y) ** 2))
    blocks = []
    for j in range(p):
        for _ in range(n_repeats):
            Xp = X.copy()
            Xp[:, j] = Xp[rng.permutation(n), j]
            blocks.append(Xp)
    pred = model.predict(np.vstack(blocks)).reshape(p, n_repeats, n)
    mse_perm = ((pred - y[None, None, :]) ** 2).mean(axis=2).mean(axis=1)
    return mse_perm - base


def surrogate(d: pd.DataFrame, personas: list[str], n_trees: int, n_null: int) -> dict:
    out = {"rf_r2_oof": np.nan, "rf_persona_share": np.nan, "rf_null_persona_share": np.nan,
           "rf_n_runs": int(len(d)), "rf_n_trees": n_trees}
    d = d.loc[d["cash_share"].notna()].reset_index(drop=True)
    if len(d) < 10:
        return out
    y = d["cash_share"].astype(float).values
    X, cols, pidx = build_features(d, personas)
    groups = d["seed"].values
    n_splits = int(min(5, len(np.unique(groups))))
    if n_splits < 2:
        return out
    gkf = GroupKFold(n_splits=n_splits)
    splits = list(gkf.split(X, y, groups))
    rng = np.random.default_rng(RANDOM_STATE)
    oof = np.full(len(y), np.nan)
    imp_sum = np.zeros(X.shape[1])
    for tr, te in splits:
        rf = RandomForestRegressor(n_estimators=n_trees, random_state=RANDOM_STATE).fit(X[tr], y[tr])
        oof[te] = rf.predict(X[te])
        imp_sum += perm_importance_batched(rf, X[te], y[te], N_PERM_REPEATS, rng)
    imp = np.clip(imp_sum / n_splits, 0, None)
    out["rf_r2_oof"] = float(r2_score(y, oof)) if np.var(y) > 0 else np.nan
    out["rf_persona_share"] = float(imp[pidx].sum() / imp.sum()) if imp.sum() > 0 else np.nan
    if n_null > 0:
        null_rng = np.random.default_rng(RANDOM_STATE + 1)
        shares = []
        for s in range(n_null):
            perm = null_rng.permutation(len(y))
            Xn = X.copy()
            Xn[:, pidx] = X[perm][:, pidx]          # shuffle persona labels across runs
            tr, te = splits[s % n_splits]
            rf = RandomForestRegressor(n_estimators=N_TREES_NULL, random_state=RANDOM_STATE + s).fit(Xn[tr], y[tr])
            imp_n = np.clip(perm_importance_batched(rf, Xn[te], y[te], N_PERM_REPEATS, rng), 0, None)
            shares.append(imp_n[pidx].sum() / imp_n.sum() if imp_n.sum() > 0 else np.nan)
        out["rf_null_persona_share"] = float(np.nanmean(shares)) if np.isfinite(shares).any() else np.nan
    return out


# --------------------------------------------------------------------------------------------
# per-group MBTI statistics
# --------------------------------------------------------------------------------------------
def mbti_group_stats(d1: pd.DataFrame, d15: pd.DataFrame, n_trees: int, n_null: int) -> dict:
    """d1 = run-level day-1 frame; d15 = run-level mean over days 1-5 frame (same runs)."""
    r = {}
    r["n_runs"] = int(len(d1))
    vals = {p: d1.loc[d1["persona"] == p, "cash_share"].dropna().values for p in MBTI}
    for p in MBTI:
        v = vals[p]
        r[f"n_{p}"] = int(len(v))
        r[f"c1_mean_{p}"] = float(np.mean(v)) if len(v) else np.nan
        r[f"c1_median_{p}"] = float(np.median(v)) if len(v) else np.nan
        v5 = d15.loc[d15["persona"] == p, "cash_share_d1to5"].dropna().values
        r[f"c1to5_mean_{p}"] = float(np.mean(v5)) if len(v5) else np.nan
    r["kw_p"] = kw_p([vals[p] for p in MBTI])
    for a, b in PAIRS:
        r[f"mwu_p_{a}_vs_{b}"] = mwu_p(vals[a], vals[b])
        r[f"cliff_{a}_vs_{b}"] = cliffs_delta(vals[a], vals[b])
    med = [r[f"c1_median_{p}"] for p in MBTI]
    r["ordering_medians_cons_gt_bal_gt_aggr"] = bool(med[0] > med[1] > med[2]) if not any(np.isnan(med)) else False
    deltas = [r[f"cliff_{a}_vs_{b}"] for a, b in PAIRS]
    r["crit_ordering_pass"] = bool((r["kw_p"] < 0.01) and all(np.isfinite(deltas)) and min(deltas) >= 0.47)
    # band / point hits
    d1v = d1.loc[d1["cash_share"].notna()]
    bh = np.array([in_band(p, c) for p, c in zip(d1v["persona"], d1v["cash_share"])], bool) if len(d1v) else np.array([])
    ph = np.array([point_hit(p, c) for p, c in zip(d1v["persona"], d1v["cash_share"])], bool) if len(d1v) else np.array([])
    r["band_hit_all"] = float(bh.mean()) if len(bh) else np.nan
    r["point_hit_all"] = float(ph.mean()) if len(ph) else np.nan
    for p in MBTI:
        m = (d1v["persona"] == p).values
        r[f"band_hit_{p}"] = float(bh[m].mean()) if m.any() else np.nan
        r[f"point_hit_{p}"] = float(ph[m].mean()) if m.any() else np.nan
    r["crit_band_pass"] = bool(np.isfinite(r["band_hit_all"]) and r["band_hit_all"] >= 0.80)
    # decodability
    c = d1v["cash_share"].astype(float).values; pe = d1v["persona"].values
    r["auc_ovr_ISFJ"] = safe_auc(pe == "ISFJ", c)
    r["auc_ovr_INTJ"] = safe_auc(pe == "INTJ", -np.abs(c - V2_BAND["balanced"][2]))
    r["auc_ovr_ENTJ"] = safe_auc(pe == "ENTJ", -c)
    r["auc_ovr_macro"] = float(np.nanmean([r["auc_ovr_ISFJ"], r["auc_ovr_INTJ"], r["auc_ovr_ENTJ"]]))
    r["auc_lr_cv_macro"] = lr_cv_macro_auc(c, pe, MBTI)
    r["crit_auc_pass"] = bool(np.isfinite(r["auc_lr_cv_macro"]) and r["auc_lr_cv_macro"] >= 0.8)
    # surrogate
    r.update(surrogate(d1, MBTI, n_trees=n_trees, n_null=n_null))
    r["crit_surrogate_pass"] = bool(np.isfinite(r["rf_persona_share"]) and np.isfinite(r["rf_r2_oof"])
                                    and r["rf_persona_share"] >= 0.5 and r["rf_r2_oof"] >= 0.5)
    r["gate_pass"] = bool(r["crit_ordering_pass"] and r["crit_band_pass"] and r["crit_auc_pass"] and r["crit_surrogate_pass"])
    return r


def two_group_stats(d1: pd.DataFrame, d15: pd.DataFrame, cons: str, aggr: str) -> dict:
    r = {"persona_conservative": cons, "persona_aggressive": aggr, "n_runs": int(len(d1))}
    vals = {}
    for p in (cons, aggr):
        v = d1.loc[d1["persona"] == p, "cash_share"].dropna().values
        vals[p] = v
        r[f"n_{p}"] = int(len(v))
        r[f"c1_mean_{p}"] = float(np.mean(v)) if len(v) else np.nan
        r[f"c1_median_{p}"] = float(np.median(v)) if len(v) else np.nan
        v5 = d15.loc[d15["persona"] == p, "cash_share_d1to5"].dropna().values
        r[f"c1to5_mean_{p}"] = float(np.mean(v5)) if len(v5) else np.nan
        r[f"band_hit_{p}"] = float(np.mean(in_band(p, v))) if len(v) else np.nan
        r[f"point_hit_{p}"] = float(np.mean(point_hit(p, v))) if len(v) else np.nan
    r["mwu_p"] = mwu_p(vals[cons], vals[aggr])
    r["cliff_cons_vs_aggr"] = cliffs_delta(vals[cons], vals[aggr])
    d1v = d1.loc[d1["cash_share"].notna()]
    bh = np.array([in_band(p, c) for p, c in zip(d1v["persona"], d1v["cash_share"])], bool) if len(d1v) else np.array([])
    r["band_hit_all"] = float(bh.mean()) if len(bh) else np.nan
    c = d1v["cash_share"].astype(float).values; pe = d1v["persona"].values
    r["auc_cons_higher_cash"] = safe_auc(pe == cons, c)
    r["auc_lr_cv"] = lr_cv_macro_auc(c, pe, [cons, aggr])
    r["crit_ordering_pass"] = bool(np.isfinite(r["mwu_p"]) and r["mwu_p"] < 0.01 and r["cliff_cons_vs_aggr"] >= 0.47)
    r["crit_band_pass"] = bool(np.isfinite(r["band_hit_all"]) and r["band_hit_all"] >= 0.80)
    r["crit_auc_pass"] = bool(np.isfinite(r["auc_cons_higher_cash"]) and r["auc_cons_higher_cash"] >= 0.8)
    return r


def action_stats(d1: pd.DataFrame, personas: list[str]) -> list[dict]:
    rows = []
    acts = ["BUY", "SELL", "HOLD"]
    if len(d1) == 0:
        return rows
    tab = pd.crosstab(d1["persona"], d1["action"]).reindex(index=personas, columns=acts, fill_value=0)
    t = tab.loc[:, tab.sum(axis=0) > 0]
    t = t.loc[t.sum(axis=1) > 0]
    chi_p = np.nan
    if t.shape[0] >= 2 and t.shape[1] >= 2:
        try:
            chi_p = float(stats.chi2_contingency(t.values)[1])
        except ValueError:
            chi_p = np.nan
    for p in personas:
        n = int(tab.loc[p].sum())
        rows.append({"persona": p, "n": n,
                     **{f"p_{a.lower()}": (float(tab.loc[p, a] / n) if n else np.nan) for a in acts},
                     "chi2_p": chi_p})
    return rows


# --------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------
def fmt(x, nd=3):
    if x is None:
        return "nan"
    if isinstance(x, (bool, np.bool_)):
        return "PASS" if x else "FAIL"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return str(x)
    if not np.isfinite(xf):
        return "nan"
    return f"{xf:.{nd}f}"


def main() -> None:
    t_start = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    log("[1/6] loading runs ...")
    days, inv = load_runs()
    d1_all = days.loc[days["day"] == 1].copy()
    d15_all = (days.groupby(["family", "model", "persona", "agent_type", "scenario", "seed", "discount", "run_id"],
                            dropna=False)["cash_share"].mean().rename("cash_share_d1to5").reset_index())
    d1_all.to_csv(OUT / "e0_gate_v1_runs_day1.csv", index=False)
    n_runs_total = days["run_id"].nunique()
    log(f"      runs with any day 1-5 row: {n_runs_total}; runs with day-1 row: {d1_all['run_id'].nunique()}")

    mb1 = d1_all.loc[d1_all["family"] == "mbti"]
    mb15 = d15_all.loc[d15_all["family"] == "mbti"]
    models = sorted(mb1["model"].unique())

    # ---------------- per (model, agent_type) ----------------
    log("[2/6] per (model, agent_type) gate statistics ...")
    per_model = []
    for m in models:
        t0 = time.time()
        for at in ["static", "memory"]:
            d1 = mb1.loc[(mb1["model"] == m) & (mb1["agent_type"] == at)]
            d15 = mb15.loc[(mb15["model"] == m) & (mb15["agent_type"] == at)]
            r = {"model": m, "agent_type": at}
            r.update(mbti_group_stats(d1, d15, n_trees=N_TREES, n_null=N_NULL))
            per_model.append(r)
        rr = [x for x in per_model if x["model"] == m]
        log(f"  {m:28s} static: KW p={fmt(rr[0]['kw_p'])} share={fmt(rr[0]['rf_persona_share'])} "
            f"R2={fmt(rr[0]['rf_r2_oof'])} gate={fmt(rr[0]['gate_pass'])} | memory: KW p={fmt(rr[1]['kw_p'])} "
            f"share={fmt(rr[1]['rf_persona_share'])} R2={fmt(rr[1]['rf_r2_oof'])} gate={fmt(rr[1]['gate_pass'])} "
            f"({time.time()-t0:.0f}s)")
    log("  pooled over models ...")
    for at in ["static", "memory", "both"]:
        d1 = mb1 if at == "both" else mb1.loc[mb1["agent_type"] == at]
        d15 = mb15 if at == "both" else mb15.loc[mb15["agent_type"] == at]
        r = {"model": "POOLED", "agent_type": at}
        r.update(mbti_group_stats(d1, d15, n_trees=N_TREES, n_null=N_NULL))
        per_model.append(r)
    pm = pd.DataFrame(per_model)
    pm.to_csv(OUT / "e0_gate_v1_per_model.csv", index=False)

    # ---------------- per (model, agent_type, scenario) ----------------
    log("[3/6] per (model, agent_type, scenario) gate statistics (100-tree surrogate, no null) ...")
    per_scen = []
    for m in models:
        t0 = time.time()
        for at in ["static", "memory"]:
            for sc in ["flat", "bull_trap", "crash"]:
                d1 = mb1.loc[(mb1["model"] == m) & (mb1["agent_type"] == at) & (mb1["scenario"] == sc)]
                d15 = mb15.loc[(mb15["model"] == m) & (mb15["agent_type"] == at) & (mb15["scenario"] == sc)]
                r = {"model": m, "agent_type": at, "scenario": sc}
                r.update(mbti_group_stats(d1, d15, n_trees=N_TREES_SCENARIO, n_null=0))
                per_scen.append(r)
        log(f"  {m:28s} scenario rows done ({time.time()-t0:.0f}s)")
    for at in ["static", "memory", "both"]:
        for sc in ["flat", "bull_trap", "crash"]:
            sel = mb1["scenario"] == sc
            sel15 = mb15["scenario"] == sc
            if at != "both":
                sel = sel & (mb1["agent_type"] == at)
                sel15 = sel15 & (mb15["agent_type"] == at)
            r = {"model": "POOLED", "agent_type": at, "scenario": sc}
            r.update(mbti_group_stats(mb1.loc[sel], mb15.loc[sel15], n_trees=N_TREES_SCENARIO, n_null=0))
            per_scen.append(r)
    ps = pd.DataFrame(per_scen)
    ps.to_csv(OUT / "e0_gate_v1_per_model_scenario.csv", index=False)

    # ---------------- OCEAN ----------------
    log("[4/6] OCEAN O1-vs-O2 and O3 ceiling ...")
    oc1 = d1_all.loc[d1_all["family"] == "ocean"]
    oc15 = d15_all.loc[d15_all["family"] == "ocean"]
    ocean_rows = []
    for m in sorted(oc1["model"].unique()) + ["POOLED"]:
        for at in ["static", "memory", "both"]:
            for cons, aggr, tag in [("O1_conservative", "O2_aggressive", "O1_vs_O2"),
                                    ("O3_conservative", "O3_aggressive", "O3_numerical_only")]:
                sel = oc1["persona"].isin([cons, aggr])
                sel15 = oc15["persona"].isin([cons, aggr])
                if m != "POOLED":
                    sel = sel & (oc1["model"] == m)
                    sel15 = sel15 & (oc15["model"] == m)
                if at != "both":
                    sel = sel & (oc1["agent_type"] == at)
                    sel15 = sel15 & (oc15["agent_type"] == at)
                d1 = oc1.loc[sel]; d15 = oc15.loc[sel15]
                if len(d1) == 0:
                    continue
                r = {"model": m, "agent_type": at, "comparison": tag,
                     "scenarios": ",".join(sorted(d1["scenario"].unique()))}
                r.update(two_group_stats(d1, d15, cons, aggr))
                ocean_rows.append(r)
    oc = pd.DataFrame(ocean_rows)
    oc.to_csv(OUT / "e0_gate_v1_ocean.csv", index=False)

    # ---------------- day-1 actions ----------------
    log("[5/6] day-1 action distributions ...")
    act_rows = []
    for m in models + ["POOLED"]:
        for at in ["static", "memory", "both"]:
            sel = (mb1["model"] == m) if m != "POOLED" else pd.Series(True, index=mb1.index)
            if at != "both":
                sel = sel & (mb1["agent_type"] == at)
            for row in action_stats(mb1.loc[sel], MBTI):
                act_rows.append({"family": "mbti", "model": m, "agent_type": at, **row})
    for m in sorted(oc1["model"].unique()) + ["POOLED"]:
        for at in ["static", "memory", "both"]:
            sel = (oc1["model"] == m) if m != "POOLED" else pd.Series(True, index=oc1.index)
            if at != "both":
                sel = sel & (oc1["agent_type"] == at)
            for row in action_stats(oc1.loc[sel], ["O1_conservative", "O2_aggressive", "O3_conservative", "O3_aggressive"]):
                act_rows.append({"family": "ocean", "model": m, "agent_type": at, **row})
    ac = pd.DataFrame(act_rows)
    ac.to_csv(OUT / "e0_gate_v1_day1_actions.csv", index=False)

    # ---------------- red-team replication ----------------
    rt = {}
    for p in MBTI:
        rt[f"c1_mean_{p}"] = float(mb1.loc[mb1["persona"] == p, "cash_share"].mean())
    mbd = days.loc[(days["family"] == "mbti") & days["day"].between(1, 5)]
    rt["mwu_p_ISFJ_vs_INTJ_d1to5_runmeans"] = mwu_p(mb15.loc[mb15["persona"] == "ISFJ", "cash_share_d1to5"],
                                                    mb15.loc[mb15["persona"] == "INTJ", "cash_share_d1to5"])
    rt["mwu_p_ISFJ_vs_INTJ_d1to5_rundays"] = mwu_p(mbd.loc[mbd["persona"] == "ISFJ", "cash_share"],
                                                   mbd.loc[mbd["persona"] == "INTJ", "cash_share"])
    rt["mwu_p_ISFJ_vs_INTJ_day1"] = mwu_p(mb1.loc[mb1["persona"] == "ISFJ", "cash_share"],
                                          mb1.loc[mb1["persona"] == "INTJ", "cash_share"])
    for p in MBTI:
        rt[f"c1to5_mean_{p}"] = float(mb15.loc[mb15["persona"] == p, "cash_share_d1to5"].mean())

    # ---------------- report ----------------
    log("[6/6] writing report ...")
    write_report(inv, d1_all, pm, ps, oc, ac, rt)
    log(f"done in {(time.time()-t_start)/60:.1f} min; outputs in {OUT}")


def md_table(df: pd.DataFrame, cols: list[str], headers: list[str] | None = None, nd=3) -> str:
    headers = headers or cols
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append(v if isinstance(v, str) else fmt(v, nd))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(inv, d1_all, pm, ps, oc, ac, rt):
    L = []
    L.append("# E0 -- t = 0 separability gate on the v1 data (plan Section 4.6)\n")
    L.append(f"Generated by `python -m evaluation.separability_gate` on {pd.Timestamp.today():%Y-%m-%d}. "
             "All numbers are computed from the v1 T=200 run CSVs (results_april/*_200, results_may model dirs, results_ocean). "
             "C_1 = Cash / Portfolio_Value at the end of Day-1; units are runs (scenario x seed x crash discount cells). "
             "Cliff's delta is positive when the more conservative persona holds more cash.\n")
    L.append("Gate criteria: (i) ordering: Kruskal-Wallis p < 0.01 and every pairwise Cliff's delta >= 0.47; "
             "(ii) band-hit: >= 80 % of runs with C_1 inside the persona's v2 band "
             "(conservative [0.70,0.90], balanced [0.40,0.60], aggressive [0.00,0.20]); "
             "(iii) decodability: macro one-vs-rest AUC of persona from C_1 alone >= 0.8 "
             "(PASS flag uses the stratified 5-fold CV multinomial logistic regression AUC; the sign-based one-vs-rest "
             "AUCs -- ISFJ: score C_1, ENTJ: score -C_1, INTJ: score -|C_1 - 0.5| -- are reported alongside); "
             "(iv) surrogate: random-forest persona share >= 0.5 with out-of-fold R2 >= 0.5 "
             "(300 trees, GroupKFold by seed, permutation importance 20 repeats; features = persona one-hot, "
             "agent_type, scenario one-hot, 12 day-1 market fields; model identity is NOT a feature in the pooled fits; "
             "scenario-level fits use 100 trees). Overall gate PASS requires all four.\n")

    # inventory
    L.append("## 1. Data inventory\n")
    inv2 = inv.copy()
    runs_d1 = d1_all.groupby("model")["run_id"].nunique().rename("runs_with_day1")
    inv2 = inv2.merge(runs_d1, left_on="model", right_index=True, how="left")
    L.append(md_table(inv2, ["family", "model", "files", "unreadable", "error_rows_excluded", "runs_missing_day1", "runs_with_day1"]))
    L.append(f"\nTotal run files: {int(inv['files'].sum())}; parse-fallback rows (Rationale starting 'Error after 3 attempts') "
             f"excluded: {int(inv['error_rows_excluded'].sum())} (counted over the whole file); runs without a usable Day-1 row: "
             f"{int(inv['runs_missing_day1'].sum())}; runs with a Day-1 row: {d1_all['run_id'].nunique()}.\n")

    # headline pooled
    L.append("## 2. Pooled headline numbers (MBTI personas, all 18 models)\n")
    pooled = pm.loc[pm["model"] == "POOLED"].set_index("agent_type")
    rows = []
    for at in ["both", "static", "memory"]:
        r = pooled.loc[at]
        rows.append({"agent_type": at, "n_runs": r["n_runs"],
                     "ISFJ": r["c1_mean_ISFJ"], "INTJ": r["c1_mean_INTJ"], "ENTJ": r["c1_mean_ENTJ"],
                     "med_ISFJ": r["c1_median_ISFJ"], "med_INTJ": r["c1_median_INTJ"], "med_ENTJ": r["c1_median_ENTJ"],
                     "kw_p": r["kw_p"], "d_ISFJ_INTJ": r["cliff_ISFJ_vs_INTJ"], "d_INTJ_ENTJ": r["cliff_INTJ_vs_ENTJ"],
                     "d_ISFJ_ENTJ": r["cliff_ISFJ_vs_ENTJ"], "band_hit": r["band_hit_all"], "point_hit": r["point_hit_all"],
                     "auc_ovr": r["auc_ovr_macro"], "auc_lr": r["auc_lr_cv_macro"], "share": r["rf_persona_share"],
                     "r2": r["rf_r2_oof"], "null": r["rf_null_persona_share"], "gate": r["gate_pass"]})
    L.append(md_table(pd.DataFrame(rows), list(rows[0].keys()),
                      ["agent", "n", "C1 ISFJ", "C1 INTJ", "C1 ENTJ", "med ISFJ", "med INTJ", "med ENTJ", "KW p",
                       "delta ISFJ-INTJ", "delta INTJ-ENTJ", "delta ISFJ-ENTJ", "band-hit", "point-hit", "AUC ovr",
                       "AUC LR-CV", "RF share", "RF R2", "null share", "gate"]))
    rb = pooled.loc["both"]
    L.append("\nPer-persona band-hit (pooled, both agent types): "
             + ", ".join(f"{p} {fmt(rb[f'band_hit_{p}'])}" for p in MBTI)
             + "; point-hit (|C_1 - v1 target| <= 0.10): "
             + ", ".join(f"{p} {fmt(rb[f'point_hit_{p}'])}" for p in MBTI) + ".")
    L.append("\nPer-persona one-vs-rest AUC (pooled, both): "
             + ", ".join(f"{p} {fmt(rb[f'auc_ovr_{p}'])}" for p in MBTI) + ".")
    L.append("\nPairwise Mann-Whitney p (pooled, both): "
             + ", ".join(f"{a} vs {b} p={fmt(rb[f'mwu_p_{a}_vs_{b}'], 4)}" for a, b in PAIRS) + ".")
    L.append("\nDays 1-5 mean cash share (pooled, both): "
             + ", ".join(f"{p} {fmt(rb[f'c1to5_mean_{p}'])}" for p in MBTI) + ".\n")

    # per-model table
    L.append("## 3. Per-model gate table (MBTI)\n")
    pmm = pm.loc[pm["model"] != "POOLED"].copy()
    cols = ["model", "agent_type", "n_runs", "c1_mean_ISFJ", "c1_mean_INTJ", "c1_mean_ENTJ", "kw_p",
            "cliff_ISFJ_vs_INTJ", "cliff_INTJ_vs_ENTJ", "cliff_ISFJ_vs_ENTJ", "band_hit_all", "auc_lr_cv_macro",
            "rf_persona_share", "rf_r2_oof", "rf_null_persona_share",
            "crit_ordering_pass", "crit_band_pass", "crit_auc_pass", "crit_surrogate_pass", "gate_pass"]
    heads = ["model", "agent", "n", "C1 ISFJ", "C1 INTJ", "C1 ENTJ", "KW p", "d ISFJ-INTJ", "d INTJ-ENTJ", "d ISFJ-ENTJ",
             "band-hit", "AUC LR-CV", "RF share", "RF R2", "null share", "ordering", "band", "AUC", "surrogate", "GATE"]
    L.append(md_table(pmm, cols, heads))
    n_models = pmm["model"].nunique()
    L.append("")
    for crit, name in [("crit_ordering_pass", "ordering (KW p<0.01 & all Cliff's delta>=0.47)"),
                       ("crit_band_pass", "band-hit >= 80 %"), ("crit_auc_pass", "AUC >= 0.8"),
                       ("crit_surrogate_pass", "surrogate share>=0.5 & R2>=0.5"), ("gate_pass", "OVERALL GATE")]:
        ns = int(pmm.loc[pmm["agent_type"] == "static", crit].sum())
        nm = int(pmm.loc[pmm["agent_type"] == "memory", crit].sum())
        nany = int(pmm.groupby("model")[crit].any().sum())
        nboth = int(pmm.groupby("model")[crit].all().sum())
        L.append(f"- {name}: PASS in {ns}/{n_models} models (static), {nm}/{n_models} (memory); "
                 f"{nany}/{n_models} models pass in at least one agent type, {nboth}/{n_models} in both.")
    fails = {name: int((~pmm[crit].astype(bool)).sum()) for crit, name in
             [("crit_ordering_pass", "ordering"), ("crit_band_pass", "band-hit"), ("crit_auc_pass", "AUC"),
              ("crit_surrogate_pass", "surrogate")]}
    L.append(f"- Failures per criterion over the {len(pmm)} (model, agent_type) rows: "
             + ", ".join(f"{k} {v}" for k, v in sorted(fails.items(), key=lambda kv: -kv[1])) + ".")
    passing = pmm.loc[pmm["gate_pass"].astype(bool), ["model", "agent_type"]]
    L.append("- Rows passing the overall gate: " + (", ".join(f"{m}/{a}" for m, a in passing.values) if len(passing) else "none") + ".\n")

    # per-scenario summary
    L.append("## 4. Per-scenario summary (pooled over models; full table in e0_gate_v1_per_model_scenario.csv)\n")
    psp = ps.loc[ps["model"] == "POOLED"]
    L.append(md_table(psp, ["agent_type", "scenario", "n_runs", "c1_mean_ISFJ", "c1_mean_INTJ", "c1_mean_ENTJ", "kw_p",
                            "cliff_ISFJ_vs_INTJ", "cliff_INTJ_vs_ENTJ", "cliff_ISFJ_vs_ENTJ", "band_hit_all",
                            "auc_lr_cv_macro", "rf_persona_share", "rf_r2_oof", "gate_pass"],
                      ["agent", "scenario", "n", "C1 ISFJ", "C1 INTJ", "C1 ENTJ", "KW p", "d ISFJ-INTJ", "d INTJ-ENTJ",
                       "d ISFJ-ENTJ", "band-hit", "AUC LR-CV", "RF share", "RF R2", "gate"]))
    psm = ps.loc[ps["model"] != "POOLED"]
    L.append("\nPer-(model, agent_type, scenario) rows passing the overall gate: "
             f"{int(psm['gate_pass'].sum())}/{len(psm)}; passing the ordering criterion: "
             f"{int(psm['crit_ordering_pass'].sum())}/{len(psm)}; band-hit: {int(psm['crit_band_pass'].sum())}/{len(psm)}; "
             f"AUC: {int(psm['crit_auc_pass'].sum())}/{len(psm)}; surrogate: {int(psm['crit_surrogate_pass'].sum())}/{len(psm)}.\n")

    # OCEAN
    L.append("## 5. OCEAN ceiling comparison (O1 vs O2 prompts; O3 numerical-only arm states the target cash share)\n")
    L.append("O3_conservative target 1.0 (v2 band [0.70, 0.90]); O3_aggressive target 0.2 (band [0.00, 0.20]). O3 was run on flat only; "
             "O1/O2 on flat, bull_trap and crash (discount 0.92). Ordering criterion here = MWU p < 0.01 and Cliff's delta >= 0.47; "
             "AUC = AUC of 'conservative' from C_1 (higher cash = conservative).\n")
    occ = oc.copy()
    occ["c1_cons"] = [r[f"c1_mean_{r['persona_conservative']}"] for _, r in occ.iterrows()]
    occ["c1_aggr"] = [r[f"c1_mean_{r['persona_aggressive']}"] for _, r in occ.iterrows()]
    occ["bh_cons"] = [r[f"band_hit_{r['persona_conservative']}"] for _, r in occ.iterrows()]
    occ["bh_aggr"] = [r[f"band_hit_{r['persona_aggressive']}"] for _, r in occ.iterrows()]
    occ["ph_cons"] = [r[f"point_hit_{r['persona_conservative']}"] for _, r in occ.iterrows()]
    occ["ph_aggr"] = [r[f"point_hit_{r['persona_aggressive']}"] for _, r in occ.iterrows()]
    L.append(md_table(occ, ["model", "agent_type", "comparison", "n_runs", "c1_cons", "c1_aggr", "mwu_p", "cliff_cons_vs_aggr",
                            "auc_cons_higher_cash", "band_hit_all", "bh_cons", "bh_aggr", "ph_cons", "ph_aggr",
                            "crit_ordering_pass", "crit_band_pass", "crit_auc_pass"],
                      ["model", "agent", "comparison", "n", "C1 cons", "C1 aggr", "MWU p", "Cliff d", "AUC", "band-hit",
                       "band cons", "band aggr", "point cons", "point aggr", "ordering", "band", "AUC"]))
    L.append("")

    # red team
    L.append("## 6. Red-team replication\n")
    L.append("Cycle-2 red-team (subset): day-1 end cash ENTJ/INTJ/ISFJ = 0.88 / 0.92 / 0.92; ISFJ vs INTJ over days 1-5 Mann-Whitney p = 0.356.\n")
    L.append(f"All v1 MBTI runs (18 models, both agent types, {int(d1_all.loc[d1_all['family']=='mbti','run_id'].nunique())} runs): "
             f"day-1 mean cash share ENTJ/INTJ/ISFJ = {fmt(rt['c1_mean_ENTJ'])} / {fmt(rt['c1_mean_INTJ'])} / {fmt(rt['c1_mean_ISFJ'])}; "
             f"days 1-5 mean = {fmt(rt['c1to5_mean_ENTJ'])} / {fmt(rt['c1to5_mean_INTJ'])} / {fmt(rt['c1to5_mean_ISFJ'])}.  "
             f"ISFJ vs INTJ Mann-Whitney p: day 1 = {fmt(rt['mwu_p_ISFJ_vs_INTJ_day1'], 4)}; days 1-5 using per-run means = "
             f"{fmt(rt['mwu_p_ISFJ_vs_INTJ_d1to5_runmeans'], 4)}; days 1-5 using all run-day observations = "
             f"{fmt(rt['mwu_p_ISFJ_vs_INTJ_d1to5_rundays'], 4)}.\n")

    # actions
    L.append("## 7. Day-1 action distribution (pooled; per-model rows in e0_gate_v1_day1_actions.csv)\n")
    acp = ac.loc[(ac["model"] == "POOLED") & (ac["agent_type"] == "both")]
    L.append(md_table(acp, ["family", "persona", "n", "p_buy", "p_sell", "p_hold", "chi2_p"],
                      ["family", "persona", "n", "P(BUY)", "P(SELL)", "P(HOLD)", "chi2 p"], nd=4))
    acm = ac.loc[(ac["family"] == "mbti") & (ac["model"] != "POOLED") & (ac["agent_type"] == "both")]
    chi = acm.groupby("model")["chi2_p"].first()
    L.append(f"\nPer-model chi-square on the day-1 action x persona table (both agent types): p < 0.01 in "
             f"{int((chi < 0.01).sum())}/{int(chi.notna().sum())} models; p < 0.05 in {int((chi < 0.05).sum())}/{int(chi.notna().sum())}.\n")

    # conclusion
    L.append("## 8. Conclusion\n")
    nb = int(pmm.groupby("model")["gate_pass"].any().sum())
    worst = max(fails, key=fails.get)
    L.append(f"Under the v1 persona prompts, {nb}/{n_models} models pass the full t = 0 separability gate in at least one agent type "
             f"({int(pmm.loc[pmm['agent_type']=='static','gate_pass'].sum())} static rows, "
             f"{int(pmm.loc[pmm['agent_type']=='memory','gate_pass'].sum())} memory rows, out of {n_models} each). "
             f"Pooled over models the gate {'passes' if bool(rb['gate_pass']) else 'fails'}: KW p = {fmt(rb['kw_p'], 4)}, "
             f"Cliff's delta ISFJ-INTJ / INTJ-ENTJ / ISFJ-ENTJ = {fmt(rb['cliff_ISFJ_vs_INTJ'])} / {fmt(rb['cliff_INTJ_vs_ENTJ'])} / "
             f"{fmt(rb['cliff_ISFJ_vs_ENTJ'])}, band-hit {fmt(rb['band_hit_all'])}, LR-CV AUC {fmt(rb['auc_lr_cv_macro'])}, "
             f"surrogate persona share {fmt(rb['rf_persona_share'])} with R2 {fmt(rb['rf_r2_oof'])} (label-permutation null share "
             f"{fmt(rb['rf_null_persona_share'])}). The criterion that fails most often is "
             f"{worst} ({fails[worst]}/{len(pmm)} rows). "
             "The O3 numerical-only arm (Section 5) shows what the same statistics reach when the target is stated in the prompt.")
    (OUT / "E0_SEPARABILITY_GATE_V1.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
