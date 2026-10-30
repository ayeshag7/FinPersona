"""
v2.1 Phase 9 -- which of the nine open-weight stage-1 models carry the later experiments E2-E8 (GRID_EXPERIMENT_PLAN.md
3; E9, the mechanistic appendix, is out of scope).

The rule is `docs/env_v2/generated/v2_1/e9_4/selection/CRITERIA.md`, written before any stage-1 behaviour statistic was
computed.  This script implements it as written and stamps its sha256 into `selection.json`.  Analysis only -- no model
call, no cluster job -- and it writes nothing outside the selection directory (and `--cache`).  It reads:

* results_v2/phase9/stage1_open/default/default/<slug>/ -- the 9 x 2,928 runs (CSV, meta.json, usage.json), read-only;
* e9_4/ledger_default_<slug>.jsonl and e9_4/verify.json;
* e9_4/cluster_logs/vllm_srv_*.log.gz -- two numbers per model, the served length and the KV-cache size in tokens.
  Nothing else from those logs (path, host, account, job) reaches any output;
* Meta's tokenizer_config.json for Llama 3.1, when the local Hugging Face cache holds it, only to check NATIVE_WINDOW.

It reuses, unmodified, `evaluation.metrics_v2.score_run(scoring="v2_1")` (as e9_4_grid's score stage),
`evaluation.targets.band_mas`, and `tools.stats_v2.seed_level_pairs` / `pigeonhole_ci`.

    python -u -m tools.phase9.e9_4_select [--workers 8] [--cache DIR]

`--cache DIR` keeps the per-group extraction (~0.7 GB) so that a second run skips the 7.5 GB of CSVs.  `--seeds` and
`--out` exist for a smoke run on fewer seeds; the selection is read only from the full 122.

Outputs, in docs/env_v2/generated/v2_1/e9_4/selection/: per_run.csv, shared_paths.csv, usability.csv, persona.csv,
effects_cells.csv, effects_pooled.csv, market.csv, noise_seeds.csv, cost.csv, context_e6.csv, context_e6_detail.csv,
profiles.csv, distance.csv, noise_floor.csv, path_agreement.csv, redundancy_pairs.csv, gates.csv, requirements.csv,
subsets.csv, best_by_k.csv, assignments.csv, assignment_costs.csv, robustness.csv, losses.csv, loss_cells.csv,
subset_costs.csv, selection.json.  The report is docs/env_v2/v2_1/HEADLINE_MODEL_SELECTION.md.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import itertools
import json
import os
import pickle
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
E94 = os.path.join(GEN, "e9_4")
OUT = os.path.join(E94, "selection")
CRITERIA = os.path.join(OUT, "CRITERIA.md")
SUBDIR = "stage1_open"
RUNS = os.path.join(ROOT, "results_v2", "phase9", SUBDIR, "default", "default")
MANIFESTS = ("manifest_headline_open.json", "manifest_headline_open_b2.json")
SERVER_LOGS = os.path.join(E94, "cluster_logs")

LABEL = {"vllm/google/gemma-4-31b-it|default": "Gemma 4 31B", "vllm/google/gemma-4-e4b-it|default": "Gemma 4 E4B",
         "vllm/openai/gpt-oss-20b|default": "gpt-oss-20b", "vllm/meta/muse-glimmer-30b|default": "Muse Glimmer 30B",
         "vllm/allenai/olmo-3.1-32b-instruct|default": "OLMo 3.1 32B",
         "vllm/mistralai/ministral-3-14b-instruct-2512|default": "Ministral 3 14B",
         "vllm/meta-llama/llama-3.1-8b-instruct|default": "Llama 3.1 8B",
         "vllm/meta-llama/llama-3.1-70b-instruct|default": "Llama 3.1 70B", "vllm/microsoft/phi-4|default": "Phi-4"}
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
ARMS = ("static", "memory")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
SEEDS = tuple(range(10001, 10123))
TIER_C = ("band_mas", "v21_mcr_D_0.05", "v21_mcr_D_0.002")          # PREREG_PHASE_9_STAGE1_OPEN.md 3
EFFECT_METRICS = TIER_C + ("mean_cash_share",)
DELTA = 0.05                  # D12: the band-MAS margin of the headline
ALPHA_FAMILY = 0.05 / 36      # P9-14: each model's own family of 36
POWER = 0.80
N_BOOT, N_NULL, N_SPLITS, N_SEL_BOOT = 1999, 199, 100, 200
G2_MAX, G3_MAX = 0.01, 0.5                                          # DESIGN (CRITERIA 3, step 1)
G2_SENS, G3_SENS = (0.005, 0.02), (0.25, 0.75)
# GRID_EXPERIMENT_PLAN.md 3, runs per model per seed: E2 3 personas x 3 arms x 2 scenarios; E3 3 x 3 x 4 + the NONE
# trader's 4; E4 3 x 2 x 4; E5 12 generator levels x 3 x 2 x 4; E7 the plan's ~480 at S = 60.  E8 is "small", unpriced.
RUNS_PER_SEED = {"E2": 18, "E3": 40, "E4": 24, "E5": 288, "E7": 8}
CORE_EXPERIMENTS = ("E2", "E3", "E4", "E5")
PLAN_M = {"core": 6, "E6": 4, "E7": 3, "E8": 3}
S_PLAN = 60
KEY_SEP = ";"                  # model keys contain "|", so subsets join them with ";"
CHANGE_DAY = 0.01
E6_SAMPLE_SEEDS = 12           # the first 12 seeds: 288 runs per model rendered for X
RENDER_DAYS = tuple(range(1, 201, 20))
CONTEXT_LEVELS = (5, 20, 50, "full")
# CRITERIA 2 X.  Phi-4: its roster entry ("a 16,384-token context") and the length it was served at.  Llama 3.1:
# `model_max_length` of Meta's tokenizer_config.json, the file served for both sizes (PREREG_PHASE_9_STAGE1_OPEN_B2.md 1).
# The other six are known only to be >= 32,768: vLLM 0.29.0 served them there without VLLM_ALLOW_LONG_MAX_MODEL_LEN.
NATIVE_WINDOW = {"vllm/microsoft/phi-4|default": (16384, "roster entry; served at 16,384"),
                 "vllm/meta-llama/llama-3.1-8b-instruct|default": (131072, "model_max_length, Meta's tokenizer_config.json"),
                 "vllm/meta-llama/llama-3.1-70b-instruct|default": (131072, "model_max_length, Meta's tokenizer_config.json")}
SERVED_FLOOR = 32768
LLAMA_TOKENIZER_CONFIG_SHA256 = "177c7b61e616fecb84c17ce0591acb92c6c4d60e9ac5ababfb940ff23bbcd424"
OBS = ("ret_1d", "price_sma20", "price_sma50", "trend_strength", "trend_regime", "RSI14", "macd_hist", "volume_ratio",
       "news_sentiment", "sentiment_MA5", "implied_volatility", "reported_PE", "dividend_yield", "fair_value_gap")
OBS_COLS = ("obs_SMA20", "obs_SMA50", "obs_trend_strength", "obs_trend_regime", "obs_RSI14", "obs_MACD", "obs_MACD_signal",
            "obs_volume_ratio", "obs_news_sentiment", "obs_sentiment_MA5", "obs_implied_volatility", "obs_reported_PE",
            "obs_dividend_yield", "obs_analyst_fair_value")
CSV_COLS = ("Day", "Price", "Fundamental_Value", "x", "Portfolio_Value", "Cash", "Holdings_Value", "Cash_Share",
            "Cash_Share_Pre", "Target_Cash_Share", "Action", "Traded_Value", "Cost_Paid", "Parse_Status",
            "Start_Cash_Share", "Gen_Config_Hash") + OBS_COLS
RUN_METRICS = ("band_mas", "point_mas_v2", "mean_cash_share", "v21_mcr_0.05", "v21_mcr_B_0.05", "v21_mcr_D_0.05",
               "v21_mcr_0.002", "v21_mcr_B_0.002", "v21_mcr_D_0.002", "turnover", "return_pct", "mdd_pct",
               "trade_count", "zero_trade", "fallback_share")


def models() -> tuple:
    from tools.phase9 import e9_roster as RO
    return tuple(RO.HEADLINE_OPEN) + tuple(RO.HEADLINE_OPEN_B2)


def slug(key: str) -> str:
    return key.split("|")[0].replace("/", "_")


def cell(persona: str, arm: str, scenario: str, seed: int) -> dict:
    return {"persona": persona, "arm": arm, "scenario": scenario, "seed": seed, "rep": 0, "setting": "default"}


def run_base(key: str, persona: str, arm: str, scenario: str, seed: int) -> str:
    """The run's path without extension, by the runner's own naming (`e9_runner.cfg_for` / `run_paths`)."""
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    csv = R.run_paths(R.cfg_for(RO.by_key(key), cell(persona, arm, scenario, seed), SUBDIR))["csv"]
    if not os.path.normpath(csv).startswith(os.path.normpath(RUNS)):
        raise SystemExit(f"the runner places {LABEL[key]} outside {os.path.relpath(RUNS, ROOT)}")
    return csv[:-len(".csv")]


def check_manifests() -> None:
    """The cells read here are exactly both stage-1 manifests' cells, for exactly their nine configurations."""
    want = {(p, a, sc, s) for p in PERSONAS for a in ARMS for sc in SCENARIOS for s in SEEDS}
    configs = []
    for f in MANIFESTS:
        with open(os.path.join(E94, f), encoding="utf-8") as fh:
            m = json.load(fh)
        got = {(c["persona"], c["arm"], c["scenario"], int(c["seed"])) for c in m["cells"]}
        if got != want or m["subdir"] != SUBDIR or len(m["cells"]) != len(want):
            raise SystemExit(f"{f}: its cells are not the {len(want)} this analysis reads")
        configs += m["configs"]
    if sorted(configs) != sorted(models()):
        raise SystemExit("the two manifests' configurations are not the nine models read here")


def sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ======================================================================================================================
# extraction: one task per model x persona x arm (488 runs), run in worker processes
# ======================================================================================================================
def features(d: pd.DataFrame) -> np.ndarray:
    """CRITERIA 2 M: the 14 rendered observables, in OBS order."""
    P = d["Price"].to_numpy(float)
    col = {c: pd.to_numeric(d[c], errors="coerce").to_numpy(float) for c in OBS_COLS}
    ret = np.r_[0.0, np.diff(np.log(P))]
    return np.column_stack([ret, P / col["obs_SMA20"] - 1, P / col["obs_SMA50"] - 1, col["obs_trend_strength"],
                            col["obs_trend_regime"], col["obs_RSI14"], (col["obs_MACD"] - col["obs_MACD_signal"]) / P,
                            col["obs_volume_ratio"], col["obs_news_sentiment"], col["obs_sentiment_MA5"],
                            col["obs_implied_volatility"], col["obs_reported_PE"], col["obs_dividend_yield"],
                            col["obs_analyst_fair_value"] / P - 1])


def market_stats(y: np.ndarray, c: np.ndarray, X: np.ndarray, rng) -> dict:
    """One run's sufficient statistics for the pooled within-run regressions y ~ c and y ~ c + X, and the X'y and X'c
    of N_NULL circular shifts of the X rows (y and c stay aligned).  X'X is unchanged by a circular shift of demeaned
    rows, so these are all a null draw changes."""
    ok = np.isfinite(y) & np.isfinite(c) & np.isfinite(X).all(axis=1)
    y, c, X = y[ok], c[ok], X[ok]
    n = len(y)
    k = X.shape[1]
    if n < 3:
        return {"n": n, "ZZ": np.zeros((k + 1, k + 1)), "Zy": np.zeros(k + 1), "yy": 0.0,
                "Xy_null": np.zeros((N_NULL, k), np.float32), "Xc_null": np.zeros((N_NULL, k), np.float32)}
    y = y - y.mean()
    c = c - c.mean()
    X = X - X.mean(axis=0)
    Z = np.column_stack([c, X])
    FX = np.fft.rfft(X, axis=0)
    # [s, j] = sum_t X[(t + s) mod n, j] * y[t]: the circular cross-correlation, every shift at once
    Xy_all = np.fft.irfft(FX * np.conj(np.fft.rfft(y))[:, None], n=n, axis=0)
    Xc_all = np.fft.irfft(FX * np.conj(np.fft.rfft(c))[:, None], n=n, axis=0)
    s = rng.integers(1, n, size=N_NULL)
    return {"n": n, "ZZ": Z.T @ Z, "Zy": Z.T @ y, "yy": float(y @ y),
            "Xy_null": Xy_all[s].astype(np.float32), "Xc_null": Xc_all[s].astype(np.float32)}


_RENDER = {}


def _renderer():
    """The harness's own prompt pieces (no client is built), and the harness's own token counter."""
    if not _RENDER:
        from langchain_core.output_parsers import PydanticOutputParser
        from agent import v2_prompts as P
        from agent.render import render_v2_input
        from agent.schemas import TargetAllocation
        from agent.stateful_agent import count_tokens
        _RENDER.update(P=P, render=render_v2_input, count=count_tokens,
                       fi=PydanticOutputParser(pydantic_object=TargetAllocation).get_format_instructions())
    return _RENDER


def render_sample(base: str, persona: str, arm: str, rendered_fields: list) -> dict:
    """CRITERIA 2 X, for one sampled run: o200k counts of the stage-1 prompt and of the stateful turn pieces on the
    RENDER_DAYS, and of the reply the stateful history would keep (the parser's JSON, without reasoning) on every
    non-fallback day."""
    R = _renderer()
    P, count = R["P"], (lambda t: R["count"](t)[0])
    d = pd.read_csv(base + ".csv", dtype=str, keep_default_na=False)
    block = P.mandate_block("mandate", persona, "rewritten", "v2_1") if arm == "memory" else ""
    sys1 = P.system_prompt(persona, mandate_in_system=False)
    stage1, human_nb, human_cur = [], [], []
    for day in RENDER_DAYS:
        r = d.iloc[day - 1]
        ms = {k: (r["Date"] if k == "date" else r["Price"] if k == "price" else r[f"obs_{k}"]) for k in rendered_fields}
        ps = {"cash": float(r["Cash"]), "holdings_value": float(r["Holdings_Value"]),
              "cash_share": float(r["Cash_Share_Pre"])}
        inp = R["render"](ms, ps)
        hum = P.HUMAN_TEMPLATE_V2.format(input_data=inp, mandate_block=block, format_instructions=R["fi"])
        stage1.append(count(sys1) + count(hum))
        human_cur.append(count(hum))
        human_nb.append(count(P.HUMAN_TEMPLATE_V2.format(input_data=inp, mandate_block="", format_instructions=R["fi"])))
    ok = d["Parse_Status"] != "fallback"
    replies = [count(json.dumps({"target_cash_share": float(t), "rationale": str(ra)}))
               for t, ra in zip(d.loc[ok, "Target_Cash_Share"], d.loc[ok, "Rationale"])]
    return {"o200k_stage1_prompt": float(np.median(stage1)), "o200k_human_nb": float(np.median(human_nb)),
            "o200k_human_cur": float(np.median(human_cur)), "o200k_reply_mean": float(np.mean(replies)),
            "o200k_reply_max": float(np.max(replies)), "n_render_days": len(stage1), "n_replies": len(replies)}


def extract_group(task: tuple) -> dict:
    """Every run of one model x persona x arm: the score_run row, the per-run descriptives of CRITERIA 2 U, P, M and the
    shared-path check, the usage tokens, the market sufficient statistics and, for the sampled seeds, the X counts."""
    from evaluation.metrics_v2 import score_run
    from evaluation.targets import band_mas
    key, persona, arm, seeds = task
    rows, stats = [], []
    mi, pi, ai = models().index(key), PERSONAS.index(persona), ARMS.index(arm)
    for sc in SCENARIOS:
        for seed in seeds:
            base = run_base(key, persona, arm, sc, seed)
            d = pd.read_csv(base + ".csv", usecols=list(CSV_COLS))
            sco = score_run(d, persona, scoring="v2_1")
            fb = d["Parse_Status"].eq("fallback").to_numpy()
            ps = d["Parse_Status"].astype(str)
            y = d["Target_Cash_Share"].to_numpy(float)
            yk = y[~fb & np.isfinite(y)]
            C = d["Cash_Share"].to_numpy(float)
            P = d["Price"].to_numpy(float)
            with open(base + ".usage.json", encoding="utf-8") as fh:
                u = json.load(fh)
            calls = u.get("calls") or []
            row = {"Model": key, "Persona": persona, "Arm": arm, "Scenario": sc, "Seed": seed, "n_days": len(d),
                   **{m: sco.get(m) for m in RUN_METRICS},
                   "n_fallback": int(fb.sum()), "n_retry": int(ps.str.startswith("ok_retry").sum()),
                   "in_band_days": int(sum(band_mas(cv, persona) == 0.0 for cv in C)),
                   "target_distinct": int(len(np.unique(np.round(yk, 9)))) if len(yk) else 0,
                   "target_sd": float(yk.std()) if len(yk) else np.nan,
                   "change_day_share": float(np.mean(np.abs(np.diff(yk)) >= CHANGE_DAY)) if len(yk) > 1 else np.nan,
                   "gen_config_hash": str(d["Gen_Config_Hash"].iloc[0]),
                   "price_sha": hashlib.sha256(np.round(P, 10).tobytes()).hexdigest()[:16],
                   "usage_status": u.get("status"), "n_calls": len(calls),
                   "in_per_call_median": float(np.median([c_["in"] for c_ in calls])) if calls else np.nan,
                   "out_per_call_max": float(max(c_["out"] for c_ in calls)) if calls else np.nan,
                   "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
                   "reasoning_tokens": u.get("reasoning_tokens")}
            row["constant_target"] = bool(row["target_distinct"] == 1)
            rng = np.random.default_rng([20261028, mi, pi, ai, SCENARIOS.index(sc), seed])
            st = market_stats(y[~fb], d["Cash_Share_Pre"].to_numpy(float)[~fb], features(d)[~fb], rng)
            if seed in seeds[:E6_SAMPLE_SEEDS]:
                with open(base + ".meta.json", encoding="utf-8") as fh:
                    rendered = json.load(fh)["env_metadata"]["rendered_fields"]
                row.update(render_sample(base, persona, arm, rendered))
            rows.append(row)
            stats.append(st)
    return {"task": (key, persona, arm), "rows": rows, "stats": stats}


def extract(seeds, workers: int, cache: str | None) -> tuple:
    tasks = [(k, p, a, tuple(seeds)) for k in models() for p in PERSONAS for a in ARMS]
    done, todo = {}, []
    for t in tasks:
        f = os.path.join(cache, f"{slug(t[0])}__{t[1]}__{t[2]}__{len(seeds)}.pkl") if cache else None
        if f and os.path.exists(f):
            with open(f, "rb") as fh:
                done[t[:3]] = pickle.load(fh)
        else:
            todo.append((t, f))
    print(f"extract: {len(done)} groups from cache, {len(todo)} to read", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for (t, f), res in zip(todo, ex.map(extract_group, [t for t, _ in todo])):
            done[t[:3]] = res
            if f:
                os.makedirs(cache, exist_ok=True)
                with open(f, "wb") as fh:
                    pickle.dump(res, fh, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"  {LABEL[t[0]]:17s} {t[1]} {t[2]:6s} {len(res['rows'])} runs  ({time.time() - t0:.0f}s)", flush=True)
    rows, stats = [], {}
    for t in tasks:
        res = done[t[:3]]
        rows += res["rows"]
        stats[t[:3]] = res["stats"]
    return pd.DataFrame(rows), stats


# ======================================================================================================================
# shared paths, U, P
# ======================================================================================================================
def shared_paths(pr: pd.DataFrame) -> pd.DataFrame:
    g = pr.groupby(["Scenario", "Seed"]).agg(n_runs=("Model", "size"), n_gen_hash=("gen_config_hash", "nunique"),
                                             n_price_sha=("price_sha", "nunique")).reset_index()
    g["shared"] = (g["n_gen_hash"] == 1) & (g["n_price_sha"] == 1)
    return g


def usability(pr: pd.DataFrame) -> pd.DataFrame:
    g = pr.assign(degenerate=pr["zero_trade"].astype(bool) | pr["constant_target"]).groupby(
        ["Model", "Persona", "Arm", "Scenario"], sort=False)
    t = g.agg(n_runs=("Seed", "size"), n_decisions=("n_days", "sum"), n_fallback=("n_fallback", "sum"),
              n_retry=("n_retry", "sum"), zero_trade_share=("zero_trade", "mean"),
              constant_target_share=("constant_target", "mean"), degenerate_share=("degenerate", "mean"),
              median_distinct_targets=("target_distinct", "median"), mean_cash_share=("mean_cash_share", "mean"),
              band_mas=("band_mas", "mean")).reset_index()
    t["fallback_share"] = t["n_fallback"] / t["n_decisions"]
    t.insert(1, "label", t["Model"].map(LABEL))
    return t


def boot_mean_ci(v: np.ndarray, n_boot: int = N_BOOT, seed: int = 0) -> tuple:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(n_boot, len(v)))
    b = v[idx].mean(axis=1)
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def persona_table(pr: pd.DataFrame) -> pd.DataFrame:
    """CRITERIA 2 P: band-MAS and in-band share per persona, and the separation ratio and ordering share per arm."""
    from evaluation.targets import centre
    spread = centre("ISFJ") - centre("ENTJ")
    out = []
    for (key, arm), g in pr.groupby(["Model", "Arm"], sort=False):
        w = g.pivot_table(index=["Scenario", "Seed"], columns="Persona", values="mean_cash_share")
        sep = ((w["ISFJ"] - w["ENTJ"]) / spread).to_numpy()
        lo, hi = boot_mean_ci(sep)
        row = {"Model": key, "label": LABEL[key], "Arm": arm, "n_paths": len(w),
               "separation_ratio": float(sep.mean()), "sep_ci_lo": lo, "sep_ci_hi": hi,
               "ordering_share": float(((w["ISFJ"] > w["INTJ"]) & (w["INTJ"] > w["ENTJ"])).mean())}
        for p in PERSONAS:
            gp = g[g["Persona"] == p]
            row[f"n_runs_{p}"] = len(gp)
            row[f"band_mas_{p}"] = float(gp["band_mas"].mean())
            row[f"in_band_share_{p}"] = float(gp["in_band_days"].sum() / gp["n_days"].sum())
            row[f"mean_cash_share_{p}"] = float(gp["mean_cash_share"].mean())
        out.append(row)
    return pd.DataFrame(out)


# ======================================================================================================================
# E, N
# ======================================================================================================================
def effects(pr: pd.DataFrame) -> tuple:
    """CRITERIA 2 E: memory - static on the same seed, per cell and pooled, by the registered pairing and bootstrap."""
    from tools import stats_v2 as SV
    cells, pooled = [], []
    for metric in EFFECT_METRICS:
        pairs = SV.seed_level_pairs(pr, metric, "memory", "static")
        for (key, p, sc), g in pairs.groupby(["Model", "Persona", "Scenario_Cell"], sort=False):
            b = SV.pigeonhole_ci(g, n_boot=N_BOOT, seed=0)
            sd = float(g["d"].std(ddof=1))
            cells.append({"Model": key, "label": LABEL[key], "Persona": p, "Scenario": sc, "metric": metric,
                          "n_pairs": len(g), "mean_d": b["estimate"], "ci_lo": b["ci_lo"], "ci_hi": b["ci_hi"],
                          "p_boot": b["p_boot"], "sigma_d": sd, "std_effect": b["estimate"] / sd if sd > 0 else np.nan,
                          "excludes_0": bool(b["ci_lo"] > 0 or b["ci_hi"] < 0)})
        for key, g in pairs.groupby("Model", sort=False):
            b = SV.pigeonhole_ci(g, n_boot=N_BOOT, seed=0)
            pooled.append({"Model": key, "label": LABEL[key], "metric": metric, "n_pairs": len(g),
                           "n_paths": b["n_paths"], "mean_d": b["estimate"], "ci_lo": b["ci_lo"], "ci_hi": b["ci_hi"],
                           "p_boot": b["p_boot"], "excludes_0": bool(b["ci_lo"] > 0 or b["ci_hi"] < 0)})
    return pd.DataFrame(cells), pd.DataFrame(pooled)


def seeds_needed(sigma: float) -> int:
    from scipy import stats
    z = stats.norm.ppf(1 - ALPHA_FAMILY / 2) + stats.norm.ppf(POWER)
    return int(np.ceil(z * z * sigma * sigma / (DELTA * DELTA)))


def noise_table(cells: pd.DataFrame) -> pd.DataFrame:
    """CRITERIA 2 N: sigma_d per cell, the largest and RMS over 12 cells, its 90 % limit, the seeds and the MDDs."""
    from scipy import stats
    z = stats.norm.ppf(1 - ALPHA_FAMILY / 2) + stats.norm.ppf(POWER)
    out = []
    for key, g in cells.groupby("Model", sort=False):
        row = {"Model": key, "label": LABEL[key]}
        for metric, tag in zip(TIER_C, ("bm", "D05", "D002")):
            c = g[g["metric"] == metric]
            n = int(c["n_pairs"].min())
            smax = float(c["sigma_d"].max())
            row.update({f"n_cells_{tag}": len(c), f"n_pairs_per_cell_{tag}": n,
                        f"sigma_max_{tag}": smax, f"sigma_rms_{tag}": float(np.sqrt((c["sigma_d"] ** 2).mean())),
                        f"sigma_max_cell_{tag}": "|".join(c.loc[c["sigma_d"].idxmax(), ["Persona", "Scenario"]]),
                        f"sigma_limit90_{tag}": smax * float(np.sqrt((n - 1) / stats.chi2.ppf(0.10, n - 1)))})
            row[f"mdd_S60_{tag}"] = z * smax / np.sqrt(60)          # band-MAS's beside D's: a descriptive, not N2's rule
            row[f"mdd_S122_{tag}"] = z * smax / np.sqrt(122)
        row["S_point_bm"] = seeds_needed(row["sigma_max_bm"])
        row["S_limit_bm"] = seeds_needed(row["sigma_limit90_bm"])
        out.append(row)
    return pd.DataFrame(out)


# ======================================================================================================================
# M: market responsiveness (pooled within-run regressions with the circular-shift null)
# ======================================================================================================================
def stack_stats(sts: list) -> dict:
    return {"n": np.array([s["n"] for s in sts], float), "ZZ": np.stack([s["ZZ"] for s in sts]),
            "Zy": np.stack([s["Zy"] for s in sts]), "yy": np.array([s["yy"] for s in sts]),
            "Xy_null": np.stack([s["Xy_null"] for s in sts]),            # float32: summed in float64 by einsum
            "Xc_null": np.stack([s["Xc_null"] for s in sts])}


def _dss(ZZ: np.ndarray, Zy: np.ndarray, yy: np.ndarray) -> tuple:
    """Batched over leading axes: SSE of y ~ c and the incremental SS of X beyond c."""
    scc, scy = ZZ[..., 0, 0], Zy[..., 0]
    sse_red = yy - np.where(scc > 0, scy * scy / np.where(scc > 0, scc, 1.0), 0.0)
    k = ZZ.shape[-1]
    ridge = 1e-10 * np.trace(ZZ, axis1=-2, axis2=-1)[..., None, None] * np.eye(k) + 1e-300 * np.eye(k)
    b = np.linalg.solve(ZZ + ridge, Zy[..., None])[..., 0]
    sse_full = yy - np.einsum("...k,...k->...", b, Zy)
    return sse_red, np.maximum(sse_red - sse_full, 0.0)


def market_fit(S: dict, W: np.ndarray) -> dict:
    """The pooled fit for every weight vector in W (K x runs): observed and N_NULL null incremental SS.
    Returns arrays of length K."""
    n = W @ S["n"]
    ZZ = np.einsum("kr,rij->kij", W, S["ZZ"])
    Zy = W @ S["Zy"]
    yy = W @ S["yy"]
    sse_red, dss = _dss(ZZ, Zy, yy)
    Xy = np.einsum("kr,rbj->kbj", W, S["Xy_null"])
    Xc = np.einsum("kr,rbj->kbj", W, S["Xc_null"])
    ZZn = np.repeat(ZZ[:, None], N_NULL, axis=1)
    ZZn[:, :, 0, 1:] = Xc
    ZZn[:, :, 1:, 0] = Xc
    Zyn = np.concatenate([np.repeat(Zy[:, None, :1], N_NULL, axis=1), Xy], axis=2)
    _, dss_null = _dss(ZZn, Zyn, np.repeat(yy[:, None], N_NULL, axis=1))
    excess = np.maximum(dss - dss_null.mean(axis=1), 0.0)
    return {"N": n, "sse_red": sse_red, "dss": dss, "dss_null_mean": dss_null.mean(axis=1),
            "p": (1 + (dss_null >= dss[:, None]).sum(axis=1)) / (N_NULL + 1),
            "partial_r2": np.where(sse_red > 0, dss / np.where(sse_red > 0, sse_red, 1.0), np.nan),
            "excess_partial_r2": np.where(sse_red > 0, (dss - dss_null.mean(axis=1)) / np.where(sse_red > 0, sse_red, 1.0), np.nan),
            "amplitude": np.sqrt(dss / np.maximum(n, 1)), "excess_amplitude": np.sqrt(excess / np.maximum(n, 1))}


def market_table(pr: pd.DataFrame, stats: dict) -> pd.DataFrame:
    out = []
    for key in models():
        scopes = [((p, a), [(p, a)]) for p in PERSONAS for a in ARMS] + \
                 [(("pooled", a), [(p, a) for p in PERSONAS]) for a in ARMS] + \
                 [(("pooled", "pooled"), [(p, a) for p in PERSONAS for a in ARMS])]
        for (p, a), gs in scopes:
            S = stack_stats([s for g in gs for s in stats[(key, *g)]])
            f = market_fit(S, np.ones((1, len(S["n"]))))
            sub = pr[(pr["Model"] == key) & pr["Persona"].isin([g[0] for g in gs]) & pr["Arm"].isin([g[1] for g in gs])]
            out.append({"Model": key, "label": LABEL[key], "Persona": p, "Arm": a, "n_runs": len(S["n"]),
                        "n_days": int(S["n"].sum()), "partial_r2": float(f["partial_r2"][0]),
                        "null_mean_partial_r2": float(f["dss_null_mean"][0] / f["sse_red"][0]) if f["sse_red"][0] > 0 else np.nan,
                        "excess_partial_r2": float(f["excess_partial_r2"][0]), "p_null": float(f["p"][0]),
                        "n_null": N_NULL, "amplitude": float(f["amplitude"][0]),
                        "excess_amplitude": float(f["excess_amplitude"][0]),
                        "median_target_sd": float(sub["target_sd"].median()),
                        "change_day_share": float(sub["change_day_share"].mean()),
                        "median_distinct_targets": float(sub["target_distinct"].median())})
    return pd.DataFrame(out)


# ======================================================================================================================
# C: cost from the ledgers
# ======================================================================================================================
def _utc(s: str) -> float:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def cost_table() -> pd.DataFrame:
    out = []
    for key in models():
        with open(os.path.join(E94, f"ledger_default_{slug(key)}.jsonl"), encoding="utf-8") as fh:
            led = [json.loads(line) for line in fh if line.strip()]
        ends = np.array([_utc(r["utc"]) for r in led])
        secs = np.array([float(r["seconds"]) for r in led])
        iv = sorted(zip(ends - secs, ends))
        busy, cur_s, cur_e = 0.0, None, None
        for s, e in iv:
            if cur_e is None or s > cur_e:
                busy += (cur_e - cur_s) if cur_e is not None else 0.0
                cur_s, cur_e = s, e
            else:
                cur_e = max(cur_e, e)
        busy += cur_e - cur_s
        ok = [r for r in led if r["status"] == "ok"]
        n_ok = len({r["run_key"] for r in ok})
        tok = {k: np.array([float(r.get(k) or 0) for r in ok]) for k in ("input_tokens", "output_tokens", "reasoning_tokens")}
        gpuh = busy / 3600.0 / n_ok
        row = {"Model": key, "label": LABEL[key], "n_ledger_rows": len(led), "n_runs_ok": n_ok, "gpus": 1,
               "busy_hours": busy / 3600.0, "span_hours": (ends.max() - (ends - secs).min()) / 3600.0,
               "gpu_hours_per_run": gpuh, "mean_concurrency": float(secs.sum() / busy),
               "mean_run_seconds": float(secs.mean()),
               "input_tokens_per_run": float(tok["input_tokens"].mean()),
               "output_tokens_per_run": float(tok["output_tokens"].mean()),
               "reasoning_tokens_per_run": float(tok["reasoning_tokens"].mean()),
               "output_tokens_per_gpu_second": float(tok["output_tokens"].sum() / busy),
               "input_tokens_per_gpu_second": float(tok["input_tokens"].sum() / busy)}
        for e, r in RUNS_PER_SEED.items():
            row[f"gpu_hours_{e}_S60"] = r * S_PLAN * gpuh
        row["gpu_hours_E2_E5_S60"] = sum(RUNS_PER_SEED[e] for e in CORE_EXPERIMENTS) * S_PLAN * gpuh
        out.append(row)
    return pd.DataFrame(out)


# ======================================================================================================================
# X: context capacity for E6
# ======================================================================================================================
def server_capacity() -> dict:
    """The served length and KV-cache tokens of each model's stage-1 server, and only those two numbers."""
    out = {}
    for f in sorted(glob.glob(os.path.join(SERVER_LOGS, "vllm_srv_*.log.gz"))):
        name = kv = maxlen = None
        with gzip.open(f, "rt", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if name is None:
                    m = re.search(r"'served_model_name': \['([^']+)'\]", line)
                    name = m.group(1) if m else None
                if kv is None:
                    m = re.search(r"GPU KV cache size: ([\d,]+) tokens", line)
                    kv = int(m.group(1).replace(",", "")) if m else None
                if maxlen is None:
                    m = re.search(r"Using max model len (\d+)", line)
                    maxlen = int(m.group(1)) if m else None
                if name and kv and maxlen:
                    break
        if name:
            key = f"vllm/{name}|default"
            if key in out:
                raise SystemExit(f"two stage-1 server logs name {LABEL.get(key, key)}; the capacity would be ambiguous")
            out[key] = {"kv_tokens": kv, "served_max_len": maxlen}
    return out


def native_windows() -> dict:
    """NATIVE_WINDOW, with the Llama value re-read from Meta's file when the local cache holds it."""
    out = {k: {"native_window": v[0], "native_source": v[1], "checked_against_file": False}
           for k, v in NATIVE_WINDOW.items()}
    hub = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
    for key in [k for k in out if "llama" in k]:
        size = "8B" if "8b" in key else "70B"
        for f in glob.glob(os.path.join(hub, f"models--meta-llama--Llama-3.1-{size}-Instruct", "snapshots", "*",
                                        "tokenizer_config.json")):
            if sha256_file(f) == LLAMA_TOKENIZER_CONFIG_SHA256:
                with open(f, encoding="utf-8") as fh:
                    mml = int(json.load(fh)["model_max_length"])
                if mml != out[key]["native_window"]:
                    raise SystemExit(f"{LABEL[key]}: model_max_length {mml} in Meta's file, {out[key]['native_window']} here")
                out[key]["checked_against_file"] = True
    return out


def context_table(pr: pd.DataFrame) -> pd.DataFrame:
    """CRITERIA 2 X: the per-call context at each E6 level, each model's own tokens, against its windows and KV cache."""
    import inspect
    from agent import v2_prompts as P
    from agent.stateful_agent import StatefulV2Agent, count_tokens
    from experiments.arms_v2 import ARMS as ARM_DEFS, CONTEXT_LEVELS as LEVEL_ARMS
    from simulation.runner_v2 import RunConfig
    budget = int(inspect.signature(StatefulV2Agent.__init__).parameters["token_budget"].default)
    default_window = RunConfig.__dataclass_fields__["context_window"].default
    windows = {lvl: (ARM_DEFS[arms[1]].get("context_window", default_window) if lvl != "full" else None)
               for lvl, arms in LEVEL_ARMS.items()}
    if tuple(windows) != CONTEXT_LEVELS:
        raise SystemExit(f"experiments.arms_v2.CONTEXT_LEVELS is {tuple(windows)}, CRITERIA reads {CONTEXT_LEVELS}")
    sys_st = {p: count_tokens(P.system_prompt(p, mandate_in_system=True))[0] for p in PERSONAS}
    cap, nat = server_capacity(), native_windows()
    smp = pr.dropna(subset=["o200k_stage1_prompt"])
    measured_out = (pr.groupby(["Model", "Persona", "Arm"])["output_tokens"].sum()
                    / pr.groupby(["Model", "Persona", "Arm"])["n_calls"].sum())

    def fit(need, nw):
        if nw is not None:
            return need <= nw["native_window"], "native"
        return (True, "served floor") if need <= SERVED_FLOOR else (None, "unread")

    out = []
    for key in models():
        m = smp[smp["Model"] == key]
        rho_pa = (m.groupby(["Persona", "Arm"])["in_per_call_median"].median()
                  / m.groupby(["Persona", "Arm"])["o200k_stage1_prompt"].median())
        rho = float(rho_pa.median())
        run_max = pr.loc[pr["Model"] == key, "out_per_call_max"]
        out_max = float(run_max.max())
        c = cap.get(key, {})
        nw = nat.get(key)
        kv = c.get("kv_tokens")
        for lvl in CONTEXT_LEVELS:
            res = {}
            # CRITERIA's history reply (the rebuilt JSON) and, added after the smoke run as a disclosed bound, the
            # measured per-call output -- the whole content for a model without reasoning, an overstatement for one with
            for variant in ("rebuilt", "upper"):
                worst, worst_turns = 0.0, 0
                for p in PERSONAS:
                    for a in ARMS:
                        g = m[(m["Persona"] == p) & (m["Arm"] == a)]
                        reply = (float(g["o200k_reply_mean"].mean()) if variant == "rebuilt"
                                 else float(measured_out[(key, p, a)]) / rho)
                        turn = float(g["o200k_human_nb"].median()) + reply
                        turns = (windows[lvl] if lvl != "full" else min(199, int(budget // turn)))
                        ctx = rho * (sys_st[p] + turns * turn + float(g["o200k_human_cur"].median()))
                        if ctx > worst:
                            worst, worst_turns = ctx, turns
                res[variant] = (worst, worst_turns, worst + out_max)
            ctx, turns, need = res["rebuilt"]
            ctx_u, turns_u, need_u = res["upper"]
            fits, basis = fit(need, nw)
            fits_u, _ = fit(need_u, nw)
            out.append({"Model": key, "label": LABEL[key], "level": str(lvl), "turns_in_history": turns,
                        "rho_tokens_per_o200k": rho, "n_sample_runs": len(m),
                        "context_tokens": ctx, "largest_output_per_call": out_max,
                        "run_max_output_median": float(run_max.median()),
                        "run_max_output_p99": float(run_max.quantile(0.99)), "n_runs_output": int(run_max.notna().sum()),
                        "need_tokens": need,
                        "native_window": nw["native_window"] if nw else np.nan,
                        "native_source": nw["native_source"] if nw else "not read; >= 32,768 (served)",
                        "native_checked_against_file": nw["checked_against_file"] if nw else False,
                        "served_max_len_stage1": c.get("served_max_len"), "fits_window": fits, "fit_basis": basis,
                        "kv_tokens": kv, "max_concurrent_runs": int(kv // need) if kv else np.nan,
                        "kv_bound_at_64": bool(kv is not None and kv // need < 64),
                        "turns_in_history_upper": turns_u, "context_tokens_upper": ctx_u, "need_tokens_upper": need_u,
                        "fits_window_upper": fits_u,
                        "max_concurrent_runs_upper": int(kv // need_u) if kv else np.nan})
    return pd.DataFrame(out)


def context_detail(pr: pd.DataFrame) -> pd.DataFrame:
    smp = pr.dropna(subset=["o200k_stage1_prompt"])
    g = smp.groupby(["Model", "Persona", "Arm"], sort=False).agg(
        n_runs=("Seed", "size"), native_in_per_call=("in_per_call_median", "median"),
        o200k_stage1_prompt=("o200k_stage1_prompt", "median"), o200k_human_nb=("o200k_human_nb", "median"),
        o200k_human_cur=("o200k_human_cur", "median"), o200k_reply_mean=("o200k_reply_mean", "mean"),
        o200k_reply_max=("o200k_reply_max", "max"), n_replies=("n_replies", "sum")).reset_index()
    g["rho"] = g["native_in_per_call"] / g["o200k_stage1_prompt"]
    out_mean = (pr.groupby(["Model", "Persona", "Arm"])["output_tokens"].sum()
                / pr.groupby(["Model", "Persona", "Arm"])["n_calls"].sum()).rename("measured_out_per_call")
    g = g.merge(out_mean.reset_index(), on=["Model", "Persona", "Arm"])
    g.insert(1, "label", g["Model"].map(LABEL))
    return g


# ======================================================================================================================
# R: profiles, distances, noise floors
# ======================================================================================================================
class Profiles:
    """Per model, the arrays the four profile blocks are computed from, indexed by path (scenario x seed), so that any
    path weighting -- a half-split, a bootstrap draw -- applies to every model and both arms of a pair at once."""

    def __init__(self, pr: pd.DataFrame, stats: dict, seeds):
        self.seeds = tuple(seeds)
        self.paths = [(sc, s) for sc in SCENARIOS for s in self.seeds]
        self.npath = len(self.paths)
        self.m = {}
        idx = pd.MultiIndex.from_tuples([(p, a, sc, s) for p in PERSONAS for a in ARMS for sc, s in self.paths])
        for key in models():
            d = pr[pr["Model"] == key].set_index(["Persona", "Arm", "Scenario", "Seed"]).reindex(idx)
            if d["mean_cash_share"].isna().any():
                raise SystemExit(f"{LABEL[key]}: a planned run is missing from the profile")
            shape = (len(PERSONAS), len(ARMS), self.npath)
            cash = d["mean_cash_share"].to_numpy(float).reshape(shape)
            eff = {}
            for metric in ("band_mas", "v21_mcr_D_0.05"):
                v = d[metric].to_numpy(float).reshape(shape)
                eff[metric] = v[:, 1] - v[:, 0]                                         # memory - static, (3, npath)
            mk = {}
            for p in PERSONAS:
                for a in ARMS:
                    sts = stats[(key, p, a)]                                           # ordered scenario-major, as paths
                    mk[(p, a)] = stack_stats(sts)
            self.m[key] = {"cash": cash, "eff": eff, "mk": mk}
        self.sc_index = np.array([SCENARIOS.index(sc) for sc, _ in self.paths])

    def blocks(self, key: str, W: np.ndarray) -> list:
        """The four blocks for every weight vector in W (K x npath): [(K, 24), (K, 12), (K, 12), (K, 6)]."""
        a = self.m[key]
        K = W.shape[0]
        onehot = np.eye(len(SCENARIOS))[self.sc_index]                                  # (npath, 4)
        Wsc = W[:, :, None] * onehot[None]                                             # (K, npath, 4)
        den = Wsc.sum(axis=1)                                                          # (K, 4)
        cash = np.einsum("kps,ijp->kijs", Wsc, a["cash"]) / den[:, None, None, :]      # (K, 3, 2, 4)
        b1 = cash.reshape(K, -1)

        def effect_block(e):
            # a pair whose metric is undefined (D on a path with no resolvable day) is left out, as seed_level_pairs does
            ok = np.isfinite(e)
            return (np.einsum("kps,ip->kis", Wsc, np.where(ok, e, 0.0))
                    / np.einsum("kps,ip->kis", Wsc, ok.astype(float))).reshape(K, -1)
        b2 = effect_block(a["eff"]["band_mas"])
        b3 = effect_block(a["eff"]["v21_mcr_D_0.05"])
        b4 = np.column_stack([market_fit(a["mk"][(p, ar)], W)["excess_amplitude"] for p in PERSONAS for ar in ARMS])
        return [b1, b2, b3, b4]


def block_distance(A: list, B: list) -> np.ndarray:
    """CRITERIA 2 R2: the mean over blocks of each block's RMS difference (row-wise for K x f blocks)."""
    return np.mean([np.sqrt(np.mean((a - b) ** 2, axis=-1)) for a, b in zip(A, B)], axis=0)


def half_split_weights(seeds, n_splits: int, rng) -> tuple:
    """W1, W2 (n_splits x npath): each split sends every path of a seed to the same half."""
    S = len(seeds)
    W1 = np.zeros((n_splits, len(SCENARIOS) * S))
    for i in range(n_splits):
        h = np.zeros(S)
        h[rng.permutation(S)[:S // 2]] = 1.0
        W1[i] = np.tile(h, len(SCENARIOS))
    return W1, 1.0 - W1


def redundancy(prof: Profiles) -> tuple:
    keys = models()
    full = {k: prof.blocks(k, np.ones((1, prof.npath))) for k in keys}
    D = pd.DataFrame(0.0, index=keys, columns=keys)
    for a, b in itertools.combinations(keys, 2):
        D.loc[a, b] = D.loc[b, a] = float(block_distance(full[a], full[b])[0])
    W1, W2 = half_split_weights(prof.seeds, N_SPLITS, np.random.default_rng(0))
    floors = []
    for k in keys:
        dh = block_distance(prof.blocks(k, W1), prof.blocks(k, W2)) / np.sqrt(2)
        floors.append({"Model": k, "label": LABEL[k], "n_splits": N_SPLITS, "seeds_per_half": len(prof.seeds) // 2,
                       "floor_p95": float(np.percentile(dh, 95)), "floor_mean": float(dh.mean())})
        print(f"  floor {LABEL[k]:17s} {floors[-1]['floor_p95']:.4f}", flush=True)
    return D, pd.DataFrame(floors), full


def path_agreement(pr: pd.DataFrame) -> pd.DataFrame:
    """CRITERIA 2 R4: correlation over matched runs of within-cell-demeaned run-mean cash share."""
    v = pr.pivot_table(index=["Persona", "Arm", "Scenario", "Seed"], columns="Model", values="mean_cash_share")
    v = v - v.groupby(level=["Persona", "Arm", "Scenario"]).transform("mean")
    c = v[list(models())].corr()
    c.attrs["n"] = len(v)
    return c


# ======================================================================================================================
# the rule: gates, requirements, subsets, assignments
# ======================================================================================================================
def gates(pr: pd.DataFrame, usab: pd.DataFrame, g2: float = G2_MAX, g3: float = G3_MAX) -> pd.DataFrame:
    with open(os.path.join(E94, "verify.json"), encoding="utf-8") as fh:
        ver = {r["config"]: r for r in json.load(fh)["rows"] if r["manifest"].startswith("headline_open")}
    planned = len(PERSONAS) * len(ARMS) * len(SCENARIOS) * pr["Seed"].nunique()
    out = []
    for key in models():
        v = ver.get(key, {})
        p = pr[pr["Model"] == key]
        u = usab[usab["Model"] == key]
        g1 = (v.get("verified") == v.get("planned") == 2928 and v.get("mismatched") == 0 and v.get("missing") == 0
              and len(p) == planned and bool((p["usage_status"] == "ok").all()) and bool((p["n_days"] == 200).all()))
        degenerate = float((p["zero_trade"].astype(bool) | p["constant_target"]).mean())
        out.append({"Model": key, "label": LABEL[key], "n_runs": len(p), "verified": v.get("verified"),
                    "G1_complete": bool(g1), "max_cell_fallback_share": float(u["fallback_share"].max()),
                    "n_fallback": int(p["n_fallback"].sum()), "G2_fallback": bool(u["fallback_share"].max() <= g2),
                    "degenerate_share": degenerate, "G3_decides": bool(degenerate <= g3),
                    "eligible": bool(g1 and u["fallback_share"].max() <= g2 and degenerate <= g3),
                    "g2_threshold": g2, "g3_threshold": g3})
    return pd.DataFrame(out)


def context_status(fits: list, concurrent: list) -> str:
    """R_context: every level fits a known window and one B200's KV cache ("met"); some level fits neither ("not met");
    otherwise a window above 32,768 was not read ("conditional")."""
    known = [f for f in fits if f is not None and f == f]
    kv = [c for c in concurrent if c == c]                       # NaN: no server log was read for this model
    if len(known) == len(fits) and all(bool(f) for f in known) and len(kv) == len(concurrent) and all(c >= 1 for c in kv):
        return "met"
    if any(not bool(f) for f in known) or any(c < 1 for c in kv):
        return "not met"
    return "conditional"


def requirements(pooled: pd.DataFrame, pers: pd.DataFrame, market: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    out = []
    for key in models():
        e = pooled[(pooled["Model"] == key) & (pooled["metric"] == "band_mas")].iloc[0]
        st = pers[(pers["Model"] == key) & (pers["Arm"] == "static")].iloc[0]
        mk = market[(market["Model"] == key) & (market["Persona"] == "pooled") & (market["Arm"].isin(ARMS))]
        cx = ctx[ctx["Model"] == key]
        r_ctx = context_status(cx["fits_window"].tolist(), cx["max_concurrent_runs"].tolist())
        r_ctx_u = context_status(cx["fits_window_upper"].tolist(), cx["max_concurrent_runs_upper"].tolist())
        out.append({"Model": key, "label": LABEL[key],
                    "R_effect": bool(e["excludes_0"]), "effect_band_mas": e["mean_d"], "effect_ci_lo": e["ci_lo"],
                    "effect_ci_hi": e["ci_hi"], "effect_n_pairs": int(e["n_pairs"]),
                    "R_persona": bool(st["sep_ci_lo"] > 0), "static_separation": st["separation_ratio"],
                    "static_sep_ci_lo": st["sep_ci_lo"], "static_sep_n_paths": int(st["n_paths"]),
                    "R_headroom": bool(max(st[f"band_mas_{p}"] for p in PERSONAS) >= DELTA),
                    "static_band_mas_max_persona": max(st[f"band_mas_{p}"] for p in PERSONAS),
                    "R_market": bool((mk["p_null"] < 0.05).all() and len(mk) == 2),
                    "market_p_static": float(mk.loc[mk["Arm"] == "static", "p_null"].iloc[0]),
                    "market_p_memory": float(mk.loc[mk["Arm"] == "memory", "p_null"].iloc[0]),
                    "R_context": r_ctx, "R_context_upper": r_ctx_u,
                    "full_need_tokens": float(cx.loc[cx["level"] == "full", "need_tokens"].iloc[0]),
                    "full_max_concurrent": cx.loc[cx["level"] == "full", "max_concurrent_runs"].iloc[0]})
    return pd.DataFrame(out)


EXPERIMENT_REQ = {"E2": ("R_effect",), "E3": ("R_persona", "R_effect"), "E4": ("R_headroom",), "E5": ("R_market",),
                  "E6": ("R_effect", "R_context"), "E7": ("R_persona",), "E8": ("R_effect",)}


def meets(req: pd.DataFrame, key: str, exp: str, context_ok=("met",)) -> bool:
    """`context_ok=("met", "conditional")` reads E6 as if every unread window sufficed -- reported as such, never as
    the rule's assignment."""
    r = req.set_index("Model").loc[key]
    return all((r[c] in context_ok) if c == "R_context" else bool(r[c]) for c in EXPERIMENT_REQ[exp])


class Coverage:
    """CRITERIA 3 step 2: L(S) = max_m max(0, min_{s in S} [d(m, s) - floor_ms]) over the models to cover, the mean
    excess over the excluded ones, and the tie tolerance delta = the median floor."""

    def __init__(self, D: pd.DataFrame, floors: pd.Series):
        self.D = D
        self.keys = list(D.index)
        self.ix = {k: i for i, k in enumerate(self.keys)}
        f = floors.reindex(self.keys).to_numpy(float)
        self.F = np.sqrt((f[:, None] ** 2 + f[None, :] ** 2) / 2)                     # floor_ms
        self.E = D.to_numpy(float) - self.F                                            # d(m, s) - floor_ms
        self.delta = float(np.median(f))

    def pair_floor(self, a: str, b: str) -> float:
        return float(self.F[self.ix[a], self.ix[b]])

    def excess(self, m: str, S) -> tuple:
        js = [self.ix[s] for s in S]
        j = js[int(np.argmin(self.E[self.ix[m], js]))]
        return max(0.0, float(self.E[self.ix[m], j])), self.keys[j]

    def loss(self, S, cover) -> tuple:
        js = [self.ix[s] for s in S]
        ex = [max(0.0, float(self.E[self.ix[m], js].min())) for m in cover if m not in S]
        return (max(ex) if ex else 0.0), (float(np.mean(ex)) if ex else 0.0)


def implied_cost(S, cost: pd.DataFrame, noise: pd.DataFrame, exps=CORE_EXPERIMENTS) -> tuple:
    c = cost.set_index("Model")["gpu_hours_per_run"]
    s_impl = int(max(noise.set_index("Model").loc[list(S), "S_limit_bm"]))
    per_seed = sum(RUNS_PER_SEED[e] for e in exps)
    return s_impl, float(sum(per_seed * s_impl * c[m] for m in S)), float(sum(per_seed * S_PLAN * c[m] for m in S))


def redundancy_pairs(cov: Coverage, pa: pd.DataFrame) -> pd.DataFrame:
    """Every pair: the profile distance, the pair floor, the excess over it, and the path-level agreement (R2-R4)."""
    rows = []
    for a, b in itertools.combinations(cov.keys, 2):
        d, f = float(cov.D.loc[a, b]), cov.pair_floor(a, b)
        rows.append({"model_a": LABEL[a], "model_b": LABEL[b], "distance": d, "pair_floor": f, "excess": d - f,
                     "distance_over_floor": d / f, "indistinguishable_at_122": bool(d <= f),
                     "path_agreement_r": float(pa.loc[a, b]), "n_matched_runs": int(pa.attrs.get("n", 0))})
    return pd.DataFrame(rows).sort_values("excess")


def subset_costs(subsets: dict, cost: pd.DataFrame, noise: pd.DataFrame) -> pd.DataFrame:
    """GPU-hours of E2, E3, E4, E5 and E7 for each subset at four seed counts: the plan's 60, stage 1's 122, the
    subset's implied S (one S for all members, CRITERIA C3), and each member at its own implied S but never below the
    plan's 60.  E6 is sized by its own pilot and E8 is unpriced (CRITERIA C3)."""
    c = cost.set_index("Model")["gpu_hours_per_run"]
    s_own = noise.set_index("Model")["S_limit_bm"]
    rows = []
    for name, S in subsets.items():
        s_impl = int(max(s_own[list(S)]))
        for basis, seeds_of in (("S = 60 (plan)", lambda m: S_PLAN), ("S = 122 (stage 1)", lambda m: len(SEEDS)),
                                (f"S = {s_impl} (implied, common)", lambda m: s_impl),
                                ("own implied S, at least 60", lambda m: max(int(s_own[m]), S_PLAN))):
            row = {"subset": name, "members": " + ".join(LABEL[m] for m in S), "n_models": len(S), "seed_basis": basis}
            for e in ("E2", "E3", "E4", "E5", "E7"):
                row[f"runs_{e}"] = int(sum(RUNS_PER_SEED[e] * seeds_of(m) for m in S))
                row[f"gpu_hours_{e}"] = float(sum(RUNS_PER_SEED[e] * seeds_of(m) * c[m] for m in S))
            row["gpu_hours_E2_E5"] = sum(row[f"gpu_hours_{e}"] for e in CORE_EXPERIMENTS)
            row["runs_E2_E5"] = sum(row[f"runs_{e}"] for e in CORE_EXPERIMENTS)
            rows.append(row)
    return pd.DataFrame(rows)


def enumerate_subsets(cov: Coverage, eligible: list, cost: pd.DataFrame, noise: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in range(1, len(eligible) + 1):
        for S in itertools.combinations(eligible, k):
            L, Lmean = cov.loss(S, eligible)
            s_impl, gh_impl, gh60 = implied_cost(S, cost, noise)
            rows.append({"k": k, "members": " + ".join(LABEL[m] for m in S), "keys": KEY_SEP.join(S),
                         "coverage_loss": L, "mean_excess": Lmean, "S_implied": s_impl,
                         "gpu_hours_E2_E5_S_implied": gh_impl, "gpu_hours_E2_E5_S60": gh60})
    return pd.DataFrame(rows)


def pick(sub: pd.DataFrame, k: int, delta: float, loss_col: str = "coverage_loss",
         cost_col: str = "gpu_hours_E2_E5_S_implied") -> pd.Series:
    """The rule's choice at size k: minimum loss, ties within delta, then the lowest cost, then alphabetical."""
    s = sub[sub["k"] == k]
    tied = s[s[loss_col] <= s[loss_col].min() + delta]
    return tied.sort_values([cost_col, "members"]).iloc[0]


def ordered(sub: pd.DataFrame, k: int, delta: float) -> pd.DataFrame:
    """Every k-subset in the rule's order: those tied with the best by cost (so the first row is `pick`'s), then the
    rest by loss and cost."""
    s = sub[sub["k"] == k].copy()
    s["tied_with_best"] = s["coverage_loss"] <= s["coverage_loss"].min() + delta
    cost = "gpu_hours_E2_E5_S_implied"
    return pd.concat([s[s["tied_with_best"]].sort_values([cost, "members"]),
                      s[~s["tied_with_best"]].sort_values(["coverage_loss", cost, "members"])])


def choose_within(cov: Coverage, pool: list, cover: list, k: int, tiebreak) -> tuple:
    """E6-E8: the k-subset of `pool` that best covers `cover` (the core), ties within delta by `tiebreak` (lower first)."""
    if len(pool) <= k:
        return tuple(pool), (cov.loss(tuple(pool), cover)[0] if pool else np.nan)
    cands = [(cov.loss(S, cover)[0], S) for S in itertools.combinations(pool, k)]
    best = min(c[0] for c in cands)
    tied = [S for L, S in cands if L <= best + cov.delta]
    S = min(tied, key=lambda S: (tiebreak(S), " + ".join(LABEL[m] for m in S)))
    return S, cov.loss(S, cover)[0]


def assign_experiments(core: list, eligible: list, req: pd.DataFrame, cov: Coverage, cost: pd.DataFrame,
                       ctx: pd.DataFrame) -> pd.DataFrame:
    """CRITERIA 3 step 3 for one core."""
    out = []
    ccost = cost.set_index("Model")["gpu_hours_per_run"]
    for e in CORE_EXPERIMENTS:
        ok = [m for m in core if meets(req, m, e)]
        top = []
        extra = [m for m in eligible if m not in core and meets(req, m, e)]
        need = min(PLAN_M["core"] - len(ok), len(extra))
        if need > 0:                       # the top-up that, WITH the qualifying core members, covers the nine best
            cands = [(cov.loss(tuple(ok) + T, eligible)[0], T) for T in itertools.combinations(extra, need)]
            lo = min(c[0] for c in cands)
            top = list(min([T for L, T in cands if L <= lo + cov.delta],
                           key=lambda T: (sum(ccost[m] for m in T), " + ".join(LABEL[m] for m in T))))
        for m in core:
            out.append({"experiment": e, "Model": m, "label": LABEL[m], "role": "core" if m in ok else "core, excluded",
                        "requirement": "+".join(EXPERIMENT_REQ[e]), "meets": m in ok})
        for m in top:
            out.append({"experiment": e, "Model": m, "label": LABEL[m], "role": "top-up",
                        "requirement": "+".join(EXPERIMENT_REQ[e]), "meets": True})
    full_conc = ctx[ctx["level"] == "full"].set_index("Model")["max_concurrent_runs"]
    e6_tb = lambda S: (-min(full_conc[m] for m in S), sum(ccost[m] for m in S))       # noqa: E731
    gh_tb = lambda S: sum(ccost[m] for m in S)                                         # noqa: E731
    for name, e, tb, ctx_ok in (("E6", "E6", e6_tb, ("met",)),
                                ("E6 if the unread windows suffice", "E6", e6_tb, ("met", "conditional")),
                                ("E7", "E7", gh_tb, ("met",)), ("E8", "E8", gh_tb, ("met",))):
        pool = [m for m in core if meets(req, m, e, ctx_ok)]
        S, L = choose_within(cov, pool, core, PLAN_M[e], tb)
        for m in core:
            out.append({"experiment": name, "Model": m, "label": LABEL[m],
                        "role": "chosen" if m in S else ("eligible, not chosen" if m in pool else "excluded"),
                        "requirement": "+".join(EXPERIMENT_REQ[e]), "meets": m in pool,
                        "coverage_of_core": L if m in S else np.nan})
    return pd.DataFrame(out)


def assignment_costs(assign: pd.DataFrame, cost: pd.DataFrame, noise: pd.DataFrame) -> pd.DataFrame:
    """GPU-hours of each priced experiment on the models it is assigned, at the four seed bases of `subset_costs`
    (the implied S is common within the experiment)."""
    c = cost.set_index("Model")["gpu_hours_per_run"]
    s_own = noise.set_index("Model")["S_limit_bm"]
    rows = []
    for e in ("E2", "E3", "E4", "E5", "E7"):
        S = assign[(assign["experiment"] == e) & assign["role"].isin(["core", "top-up", "chosen"])]["Model"].tolist()
        if not S:
            continue
        s_impl = int(max(s_own[S]))
        for basis, seeds_of in (("S = 60 (plan)", lambda m: S_PLAN), ("S = 122 (stage 1)", lambda m: len(SEEDS)),
                                ("implied S, common", lambda m: s_impl),
                                ("own implied S, at least 60", lambda m: max(int(s_own[m]), S_PLAN))):
            rows.append({"experiment": e, "models": " + ".join(LABEL[m] for m in S), "n_models": len(S),
                         "seed_basis": basis, "S_implied_common": s_impl,
                         "runs": int(sum(RUNS_PER_SEED[e] * seeds_of(m) for m in S)),
                         "gpu_hours": float(sum(RUNS_PER_SEED[e] * seeds_of(m) * c[m] for m in S))})
    return pd.DataFrame(rows)


# ======================================================================================================================
# Step 5: what a subset loses against all nine
# ======================================================================================================================
def losses(name: str, S, cov: Coverage, eligible: list, cells: pd.DataFrame, cost: pd.DataFrame, noise: pd.DataFrame,
           pers: pd.DataFrame, market: pd.DataFrame, pooled: pd.DataFrame) -> tuple:
    S = list(S)
    rows = []
    for m in eligible:
        if m in S:
            continue
        ex, best = cov.excess(m, S)
        rows.append({"subset": name, "what": "excluded model", "item": LABEL[m], "nearest_member": LABEL[best],
                     "distance": float(cov.D.loc[m, best]), "pair_floor": cov.pair_floor(m, best), "excess": ex})
    cell_rows = []
    for metric in ("band_mas", "v21_mcr_D_0.05"):
        c = cells[cells["metric"] == metric]
        for (p, sc), g in c.groupby(["Persona", "Scenario"], sort=False):
            g9 = g[g["Model"].isin(eligible)]
            gs = g[g["Model"].isin(S)]
            sig = g9[g9["excludes_0"]]
            both9 = bool((sig["mean_d"] > 0).any() and (sig["mean_d"] < 0).any())
            sigs = gs[gs["excludes_0"]]
            cell_rows.append({"subset": name, "metric": metric, "Persona": p, "Scenario": sc, "n_models_all": len(g9),
                              "n_models_subset": len(gs), "mean_all": g9["mean_d"].mean(), "mean_subset": gs["mean_d"].mean(),
                              "gap": gs["mean_d"].mean() - g9["mean_d"].mean(),
                              "se_all_across_models": g9["mean_d"].std(ddof=1) / np.sqrt(len(g9)),
                              "sd_all": g9["mean_d"].std(ddof=1), "sd_subset": gs["mean_d"].std(ddof=1),
                              "all_both_signs": both9,
                              "subset_keeps_both": bool((sigs["mean_d"] > 0).any() and (sigs["mean_d"] < 0).any()),
                              "n_sig_pos_all": int((sig["mean_d"] > 0).sum()), "n_sig_neg_all": int((sig["mean_d"] < 0).sum()),
                              "n_sig_pos_subset": int((sigs["mean_d"] > 0).sum()),
                              "n_sig_neg_subset": int((sigs["mean_d"] < 0).sum())})
    lc = pd.DataFrame(cell_rows)
    for metric, g in lc.groupby("metric", sort=False):
        rows.append({"subset": name, "what": f"cross-model mean effect, {metric}", "item": "max |gap| / RMS gap",
                     "value": float(g["gap"].abs().max()), "value2": float(np.sqrt((g["gap"] ** 2).mean())),
                     "reference": float(g["se_all_across_models"].median()), "n_cells": len(g),
                     "note": "reference = median over cells of the nine's SE across models"})
        rows.append({"subset": name, "what": f"between-model sd of effects, {metric}", "item": "subset / all, median over cells",
                     "value": float((g["sd_subset"] / g["sd_all"]).median()), "n_cells": len(g)})
        rows.append({"subset": name, "what": f"cells with significant effects of both signs, {metric}",
                     "item": "in all / kept by subset", "value": int(g["all_both_signs"].sum()),
                     "value2": int((g["all_both_signs"] & g["subset_keeps_both"]).sum()), "n_cells": len(g)})
    summ = {"static separation ratio": pers[pers["Arm"] == "static"].set_index("Model")["separation_ratio"],
            "excess amplitude (pooled)": market[(market["Persona"] == "pooled") & (market["Arm"] == "pooled")].set_index("Model")["excess_amplitude"],
            "static band-MAS (pooled)": pers[pers["Arm"] == "static"].set_index("Model")[[f"band_mas_{p}" for p in PERSONAS]].mean(axis=1),
            "pooled band-MAS effect": pooled[pooled["metric"] == "band_mas"].set_index("Model")["mean_d"],
            "sigma_d max, band-MAS": noise.set_index("Model")["sigma_max_bm"],
            "GPU-hours per run": cost.set_index("Model")["gpu_hours_per_run"]}
    for what, s in summ.items():
        rows.append({"subset": name, "what": f"range of {what}", "item": "subset min..max / all min..max",
                     "value": float(s[S].min()), "value2": float(s[S].max()),
                     "reference": float(s[eligible].min()), "reference2": float(s[eligible].max())})
    s_impl, gh, gh60 = implied_cost(S, cost, noise)
    s_all, gh_all, gh60_all = implied_cost(eligible, cost, noise)
    rows.append({"subset": name, "what": "E2-E5 GPU-hours at the implied S", "item": f"S = {s_impl} (all nine: {s_all})",
                 "value": gh, "reference": gh_all, "value2": gh_all - gh})
    rows.append({"subset": name, "what": "E2-E5 GPU-hours at S = 60", "item": "subset / all", "value": gh60,
                 "reference": gh60_all, "value2": gh60_all - gh60})
    return pd.DataFrame(rows), lc


# ======================================================================================================================
def write(df: pd.DataFrame, name: str, out: str, index: bool = False):
    df.to_csv(os.path.join(out, name), index=index, float_format="%.6g")


def in_model_order(df: pd.DataFrame) -> pd.DataFrame:
    order = {k: i for i, k in enumerate(models())}
    return df.sort_values("Model", key=lambda s: s.map(order), kind="stable")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cache", default=None, help="directory for the per-group extraction (optional)")
    ap.add_argument("--seeds", type=int, default=len(SEEDS), help="smoke runs only: the first N seeds")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    seeds = SEEDS[:a.seeds]
    if not os.path.exists(CRITERIA):
        raise SystemExit(f"{os.path.relpath(CRITERIA, ROOT)} is missing: the rule is fixed there before anything runs")
    crit_sha = sha256_file(CRITERIA)
    check_manifests()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    pr, stats = extract(seeds, a.workers, a.cache)
    keys = list(models())
    print(f"extracted {len(pr)} runs in {time.time() - t0:.0f}s", flush=True)

    sp = shared_paths(pr)
    usab = usability(pr)
    pers = persona_table(pr)
    cells, pooled = effects(pr)
    noise = noise_table(cells)
    market = market_table(pr, stats)
    cost = cost_table()
    ctx = context_table(pr)
    ctxd = context_detail(pr)
    print(f"measured U, P, E, N, M, C, X ({time.time() - t0:.0f}s)", flush=True)
    prof = Profiles(pr, stats, seeds)
    D, floors, full_profiles = redundancy(prof)
    pa = path_agreement(pr)
    print(f"measured R ({time.time() - t0:.0f}s)", flush=True)

    gt = gates(pr, usab)
    sens = pd.concat([gates(pr, usab, g2, g3).assign(scenario=f"G2 {g2} / G3 {g3}")
                      for g2 in (G2_MAX,) + G2_SENS for g3 in (G3_MAX,) + G3_SENS])
    req = requirements(pooled, pers, market, ctx)
    eligible = [k for k in keys if bool(gt.set_index("Model").loc[k, "eligible"])]
    fl = floors.set_index("Model")["floor_p95"]
    cov = Coverage(D, fl)
    sub = enumerate_subsets(cov, eligible, cost, noise)
    best = pd.DataFrame([{**pick(sub, k, cov.delta).to_dict(), "L_star": float(sub[sub["k"] == k]["coverage_loss"].min()),
                          "n_tied": int((sub[sub["k"] == k]["coverage_loss"] <= sub[sub["k"] == k]["coverage_loss"].min() + cov.delta).sum()),
                          "n_subsets": int((sub["k"] == k).sum())}
                         for k in range(1, len(eligible) + 1)])
    Lstar = best.set_index("k")["L_star"]
    k_core = PLAN_M["core"]
    if len(eligible) >= 6 and Lstar.get(5, np.inf) <= Lstar.get(6, np.inf) + cov.delta:
        k_core = 5
    k_core = min(k_core, len(eligible))
    core_row = pick(sub, k_core, cov.delta)
    core = core_row["keys"].split(KEY_SEP)

    # Step 4 (ii) first, because a different core under another gate threshold is carried through Step 3 and Step 5 too
    gate_cores = {}
    for scen, g in sens.groupby("scenario", sort=False):
        el_keys = g[g["eligible"]]["Model"].tolist()
        if set(el_keys) != set(eligible) and len(el_keys) >= k_core:
            alt = pick(enumerate_subsets(cov, el_keys, cost, noise), k_core, cov.delta)
            gate_cores[scen] = (el_keys, alt)
    variants = {"rule": (core, eligible)}
    for scen, (el_keys, alt) in gate_cores.items():
        ks = alt["keys"].split(KEY_SEP)
        if set(ks) != set(core) and not any(set(ks) == set(v[0]) for v in variants.values()):
            variants[f"core at {scen.split(' / ')[1]}"] = (ks, el_keys)
    assign = pd.concat([assign_experiments(c, el, req, cov, cost, ctx).assign(core_variant=v)
                        for v, (c, el) in variants.items()], ignore_index=True)
    assign_cost = pd.concat([assignment_costs(assign[assign["core_variant"] == v], cost, noise).assign(core_variant=v)
                             for v in variants], ignore_index=True)

    # Step 4 (i): path bootstrap of the profiles, floors fixed
    rng = np.random.default_rng(0)
    Wb = rng.multinomial(prof.npath, np.full(prof.npath, 1.0 / prof.npath), size=N_SEL_BOOT).astype(float)
    bl = {k: prof.blocks(k, Wb) for k in keys}
    picks = []
    combos = list(itertools.combinations(eligible, k_core))
    s_cost = {S: implied_cost(S, cost, noise)[1] for S in combos}
    for b in range(N_SEL_BOOT):
        Db = pd.DataFrame(0.0, index=keys, columns=keys)
        for x, y in itertools.combinations(keys, 2):
            Db.loc[x, y] = Db.loc[y, x] = float(block_distance([v[b:b + 1] for v in bl[x]], [v[b:b + 1] for v in bl[y]])[0])
        cb = Coverage(Db, fl)
        Ls = {S: cb.loss(S, eligible)[0] for S in combos}
        m0 = min(Ls.values())
        tied = [S for S in combos if Ls[S] <= m0 + cov.delta]
        picks.append(min(tied, key=lambda S: (s_cost[S], " + ".join(LABEL[m] for m in S))))
    freq = pd.Series([m for S in picks for m in S]).value_counts().reindex(keys, fill_value=0) / N_SEL_BOOT
    rob = [{"check": "bootstrap: share of draws whose chosen core contains the model", "item": LABEL[k],
            "value": float(freq[k]), "n": N_SEL_BOOT} for k in keys]
    rob.append({"check": "bootstrap: share of draws choosing exactly the core", "item": core_row["members"],
                "value": float(np.mean([set(S) == set(core) for S in picks])), "n": N_SEL_BOOT})
    top_alt = pd.Series([" + ".join(LABEL[m] for m in S) for S in picks]).value_counts().head(5)
    for members, n in top_alt.items():
        rob.append({"check": "bootstrap: most frequent chosen cores", "item": members, "value": n / N_SEL_BOOT,
                    "n": N_SEL_BOOT})
    med = pick(sub, k_core, cov.delta, loss_col="mean_excess")
    rob.append({"check": "k-median objective (mean excess): its core", "item": med["members"],
                "value": float(set(med["keys"].split(KEY_SEP)) == set(core)), "n": int((sub["k"] == k_core).sum()),
                "note": "value 1 = the same core"})
    for scen, g in sens.groupby("scenario", sort=False):
        el = g[g["eligible"]]["label"].tolist()
        rob.append({"check": "gate thresholds: eligible models", "item": scen, "value": len(el),
                    "note": ", ".join(el), "n": len(g)})
        if scen in gate_cores:                                          # Step 4 (ii): the core the rule picks there
            el_keys, alt = gate_cores[scen]
            rob.append({"check": "gate thresholds: the core with this eligible set", "item": scen,
                        "value": float(set(alt["keys"].split(KEY_SEP)) == set(core)), "n": len(el_keys),
                        "note": f"{alt['members']}; coverage loss {alt['coverage_loss']:.4f}, S {alt['S_implied']}"})
    for _, r in req.iterrows():        # added after the smoke run: the history reply as the measured per-call output
        rob.append({"check": "E6 R_context with the measured output as the history reply (upper bound)",
                    "item": r["label"], "value": float(r["R_context"] == r["R_context_upper"]),
                    "note": f"rule: {r['R_context']}; upper: {r['R_context_upper']}", "n": len(CONTEXT_LEVELS)})
    rob = pd.DataFrame(rob)

    # Step 5 and the alternatives
    alts = {"recommended core": core}
    for v, (c, _) in variants.items():
        if v != "rule":
            alts[v] = c
    o6 = ordered(sub, k_core, cov.delta)
    for i, (_, r) in enumerate(o6.iloc[1:3].iterrows(), start=2):
        alts[f"alternative {i}: next by the rule at k = {k_core}"] = r["keys"].split(KEY_SEP)
    cheap = sub[sub["k"] == k_core].sort_values("gpu_hours_E2_E5_S_implied").iloc[0]
    alts[f"cheapest {k_core}"] = cheap["keys"].split(KEY_SEP)
    if set(med["keys"].split(KEY_SEP)) != set(core):
        alts[f"k-median best {k_core}"] = med["keys"].split(KEY_SEP)
    for kk in (k_core - 1, k_core + 1):
        if 1 <= kk <= len(eligible):
            alts[f"best at k = {kk}"] = pick(sub, kk, cov.delta)["keys"].split(KEY_SEP)
    loss_rows, loss_cells = [], []
    for name, S in alts.items():
        lr, lc = losses(name, S, cov, eligible, cells, cost, noise, pers, market, pooled)
        lr.insert(1, "members", " + ".join(LABEL[m] for m in S))
        loss_rows.append(lr)
        loss_cells.append(lc)
    loss_df, loss_cell_df = pd.concat(loss_rows, ignore_index=True), pd.concat(loss_cells, ignore_index=True)
    alts["all nine"] = eligible
    subset_cost = subset_costs(alts, cost, noise)

    # ---------------------------------------------------------------------------------------------------- outputs
    out = a.out
    keep = [c for c in pr.columns if c not in ("gen_config_hash", "price_sha")]
    pr[keep].to_csv(os.path.join(out, "per_run.csv"), index=False)                    # full precision: an input to re-use
    write(sp, "shared_paths.csv", out)
    write(usab, "usability.csv", out)
    write(pers, "persona.csv", out)
    write(in_model_order(cells), "effects_cells.csv", out)
    write(in_model_order(pooled), "effects_pooled.csv", out)
    write(in_model_order(noise), "noise_seeds.csv", out)
    write(market, "market.csv", out)
    write(cost, "cost.csv", out)
    write(ctx, "context_e6.csv", out)
    write(ctxd, "context_e6_detail.csv", out)
    write(D.rename(index=LABEL, columns=LABEL), "distance.csv", out, index=True)
    write(floors, "noise_floor.csv", out)
    write(pa.rename(index=LABEL, columns=LABEL), "path_agreement.csv", out, index=True)
    write(redundancy_pairs(cov, pa), "redundancy_pairs.csv", out)
    write(pd.concat([gt.assign(scenario="registered"), sens]), "gates.csv", out)
    write(req, "requirements.csv", out)
    write(sub, "subsets.csv", out)
    write(best, "best_by_k.csv", out)
    write(assign, "assignments.csv", out)
    write(assign_cost, "assignment_costs.csv", out)
    write(rob, "robustness.csv", out)
    write(loss_df, "losses.csv", out)
    write(loss_cell_df, "loss_cells.csv", out)
    write(subset_cost, "subset_costs.csv", out)
    profiles = pd.DataFrame([{"Model": k, "label": LABEL[k], "block": b, "values": json.dumps([round(float(x), 6) for x in v[0]])}
                             for k in keys for b, v in zip(("cash", "effect_band_mas", "effect_D_0.05", "amplitude"),
                                                           full_profiles[k])])
    write(profiles, "profiles.csv", out)
    sel = {"criteria": os.path.relpath(CRITERIA, ROOT).replace(os.sep, "/"), "criteria_sha256": crit_sha,
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "inputs": {"runs": int(len(pr)), "models": len(keys), "seeds": len(seeds),
                      "shared_paths": int(sp["shared"].sum()), "paths": int(len(sp)),
                      "runs_per_path": int(sp["n_runs"].min())},
           "eligible": [LABEL[k] for k in eligible],
           "delta_median_floor": cov.delta,
           "k_core": int(k_core), "k_rule": "plan's 6 unless L*(5) <= L*(6) + delta",
           "L_star_by_k": {int(k): float(v) for k, v in Lstar.items()},
           "core": [LABEL[k] for k in core],
           "core_coverage_loss": float(core_row["coverage_loss"]), "core_S_implied": int(core_row["S_implied"]),
           "core_gpu_hours_E2_E5_S_implied": float(core_row["gpu_hours_E2_E5_S_implied"]),
           "core_gpu_hours_E2_E5_S60": float(core_row["gpu_hours_E2_E5_S60"]),
           "assignments": {v: {e: [LABEL[m] for m in assign[(assign["core_variant"] == v) & (assign["experiment"] == e)
                                                             & assign["role"].isin(["core", "top-up", "chosen"])]["Model"]]
                               for e in assign["experiment"].unique()}
                           for v in variants},
           "core_variants": {v: [LABEL[m] for m in c] for v, (c, _) in variants.items()},
           "requirements": {LABEL[r["Model"]]: {c: (r[c] if isinstance(r[c], str) else bool(r[c]))
                                                for c in ("R_effect", "R_persona", "R_headroom", "R_market",
                                                          "R_context", "R_context_upper")}
                            for _, r in req.iterrows()},
           "path_agreement_n_matched_runs": int(pa.attrs.get("n", 0)),
           "alternatives": {n: [LABEL[m] for m in S] for n, S in alts.items()},
           "bootstrap_core_share": float(np.mean([set(S) == set(core) for S in picks])),
           "n_bootstrap": N_SEL_BOOT}
    with open(os.path.join(out, "selection.json"), "w", encoding="utf-8") as fh:
        json.dump(sel, fh, indent=1)
    print(json.dumps({k: sel[k] for k in ("eligible", "k_core", "core", "assignments", "bootstrap_core_share")}, indent=1))
    print(f"done in {time.time() - t0:.0f}s -> {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
