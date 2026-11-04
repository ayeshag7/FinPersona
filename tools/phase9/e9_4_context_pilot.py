"""
v2.1 Phase 9, stage 2 -- E6's stateful sizing pilot (PREREG_PHASE_9_STAGE2_E6_PILOT.md).

E6, the context-length factor of the decay thesis (plan E8.2; levels {5, 20, 50, full}), has never been sized: no
stateful arm has run on any open-weight model, so neither the paired noise sigma_d its seed count needs nor the
GPU-hours a stateful run costs is measured (GRID_EXPERIMENT_PLAN.md 2, 4 M3; HEADLINE_MODEL_SELECTION.md 6).  This
pilot measures both, on the roster the selection's rule gives E6 once the three unread windows are read, and turns
them into E6's seed count by the rule PREREG_PHASE_9.md 2 fixed for the stage-1 pilots.

    python -u -m tools.phase9.e9_4_context_pilot --stages shape,windows,project      # before the manifest
    python -u -m tools.phase9.e9_4_grid --stages manifest_e6_pilot
    (cluster)  sbatch --export=ALL,STAGE=e6pilot --array=0-15%4 tools/cluster/stage2_b200.sbatch
    (cluster)  python -u -m tools.phase9.e9_4_grid --stages verify,score --only context_pilot
    (cluster)  python -u -m tools.phase9.e9_4_context_pilot --stages summarise --server-logs '<dir>/vllm_srv_*.log'
    (laptop)   python -u -m tools.phase9.e9_4_context_pilot --stages analyse

`shape`      PREREG_PHASE_9.md 2's shape rule on E6's own run counts: the pilot seeds S_p per cell are the value in
             {4, 8, 12, 16, 24, 32} that minimises the expected runs per model, the pilot's 96 S_p (eight arms x twelve
             cells) plus E6's runs at the chi-square 90 % limit's inflation f^2(df_d) on df_d = 12 S_p - 12 per level.
             E6's reference run count is its count at stage 2's quoted S = 60 (GRID_EXPERIMENT_PLAN.md 3), divided by
             the inflation E8.5's own sizing carried (df 84), exactly as `e9_2_pilot.stage_shape` did with stage 1's.
`windows`    The native windows of the pinned revisions, read from each model's config.json on the Hub on 4 Nov 2026
             (constants here, with the field and the revision), checked against the local Hugging Face cache when it
             holds the file; the selection's context table (`selection/context_e6.csv`) re-read against them, so
             R_context is "met" or "not met" for every model and never "conditional"; E6's roster by the selection's
             rule (CORE_OPEN members meeting R_effect and R_context); and the in-flight budget per (model, level) that
             one B200's KV cache holds at the pilot's serving length.
`project`    What the pilot and E6 are expected to cost, from Phase 8's measured tokens per run per level
             (`e8_2/context_cost.json`, v2_1 rows) and stage 1's measured input tokens per GPU-second (`selection/
             cost.csv`).  A PROJECTION, labelled so: stage 1 ran 1.8k-token prompts and the rate at 60k is not measured.
             The pilot's one registered prediction is read against it (section 4 of the pre-registration).
`summarise`  Cluster side, where the per-step CSVs are.  Per completed pilot run: the context the model saw (max and
             day-200 `Context_Tokens`, turns, mandate copies, the token-count method), the fallbacks it left in its
             history, and from `usage.json` the largest reply of any call and the calls at or above the runaway bar.
             From the servers' logs, when given: each task's KV-cache size and served length.
`analyse`    Laptop side.  Per model and level: sigma_d(R = 1) of memory - static paired on seed, with its chi-square
             90 % limit (e9_2_pilot.sigma_r1, the closed form at R' = R); per model and level above 5: the same for the
             level contrasts (the effect at L minus the effect at 5; the static arm at L minus at 5).  The plug-in is
             the maximum limit over the roster (P8-16's rule) and E6's seeds follow Appendix A at alpha' = 0.05 / 36
             with the paired-correct count beside, each quantity its own row, and the MDD at candidate seed counts.
             GPU-hours per run per level from the ledger's busy time (the union of run intervals, as cost.csv), E6's
             cost at every candidate seed count, and the gates (G2 fallback share, G3 degenerate share, the context
             against the served length, the runaway share).  The E6 pre-registration takes its decisions from these
             files; this stage decides nothing.

Outputs: docs/env_v2/generated/v2_1/e9_4/context_pilot/{shape.json, windows.json, r_context.csv, workers.csv,
         projection.{json,csv}, per_run_context.csv, servers.json, sigma.csv, contrasts.csv, sizing.json, cost.csv,
         gates.csv, summary.json}
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.phase9 import e9_4_grid as G  # noqa: E402

GEN = G.GEN
E94 = G.OUT
OUT = os.path.join(E94, "context_pilot")
SEL = os.path.join(E94, "selection")
PERSONAS, SCENARIOS = G.PERSONAS, G.SCENARIOS
N_CELLS = len(PERSONAS) * len(SCENARIOS)
ARMS = ("static", "memory")
LEVELS = (5, 20, 50, "full")
REFERENCE_LEVEL = 5                          # the level contrasts are read against the shortest window
SP_CANDIDATES = (4, 8, 12, 16, 24, 32)       # PREREG_PHASE_9.md 2
E85_DF_D = 84                                # the inflation E8.5's own sizing carried
Q = 0.90                                     # the one-sided chi-square limit
DELTA = 0.05                                 # D12: band-MAS, a quarter of a 20-pp band
FAMILY = 36                                  # alpha' = 0.05 / 36: stage 1's convention, and E6's candidate family of
                                             # three level contrasts x twelve cells (the E6 registration fixes its own)
ALPHA = 0.05 / FAMILY
CANDIDATE_SEEDS = (5, 20, 30, 40, 60)        # 5: "estimable at 5 seeds" (plan 13.1); 60: stage 2's scale
SERVED_MAX_LEN = 65536                       # the pilot serves every model at this length: the smallest native window
                                             # among the E6 candidates (OLMo 3.1 32B), so a reply is cut at the same
                                             # point on every model
RUNAWAY_TOKENS = 8192                        # the OpenRouter cap the roster already applies (e9_roster); a reply at
                                             # or above it is a runaway (HEADLINE_MODEL_SELECTION.md 3.7)
G2_FALLBACK = 0.01                           # the selection's gates, applied per (model, level)
G3_DEGENERATE = 0.5
OPERATING_POINT = 192                        # stage 2's in-flight calls per server for these models (stage2_b200.sbatch)
PROJECTION_BAR = 2.0                         # the registered prediction: measured within a factor 2 of the projection

# The native windows, read 4 Nov 2026 from config.json at the PINNED revisions on the Hub (the revisions the batch
# scripts serve).  Llama's and Phi-4's are the selection's (e9_4_select.NATIVE_WINDOW).  gpt-oss-20b, Muse Glimmer and
# Llama 3.1 70B are not read: the first fails R_effect and the other two are outside the core, so none can reach E6.
WINDOWS_READ = {
    "vllm/google/gemma-4-e4b-it|default": {
        "native_window": 131072, "hf_id": "google/gemma-4-E4B-it", "revision": "ee0ef6023621cff504d758262d4e04895a5af4a2",
        "field": "text_config.max_position_embeddings",
        "source": "config.json at the pinned revision (Hub, read 4 Nov 2026); sliding_window 512 on the local layers"},
    "vllm/google/gemma-4-31b-it|default": {
        "native_window": 262144, "hf_id": "google/gemma-4-31B-it", "revision": "842da3794eaa0b77d5f08bae87a17459d91ff475",
        "field": "text_config.max_position_embeddings",
        "source": "config.json at the pinned revision (Hub, read 4 Nov 2026); sliding_window 1024 on the local layers"},
    "vllm/allenai/olmo-3.1-32b-instruct|default": {
        "native_window": 65536, "hf_id": "allenai/Olmo-3.1-32B-Instruct", "revision": "ac0587e4a7744a551c059d8cd17ba220bc940dae",
        "field": "max_position_embeddings",
        "source": "config.json at the pinned revision (Hub, read 4 Nov 2026); YaRN factor 8 over 8,192 original "
                  "positions; sliding_window 4,096 on three layers in four"},
    "vllm/mistralai/ministral-3-14b-instruct-2512|default": {
        "native_window": 262144, "hf_id": "mistralai/Ministral-3-14B-Instruct-2512-BF16",
        "revision": "3cea74c1ebaf5ce5f5a2553de470e2ceab825142", "field": "text_config.max_position_embeddings",
        "source": "config.json at the pinned revision (Hub, read 4 Nov 2026); YaRN factor 16 over 16,384 original positions"},
    "vllm/meta-llama/llama-3.1-8b-instruct|default": {
        "native_window": 131072, "hf_id": "meta-llama/Llama-3.1-8B-Instruct", "revision": "0e9e39f249a16976918f6564b8830bc894c89659",
        "field": "model_max_length", "source": "Meta's tokenizer_config.json (HEADLINE_MODEL_SELECTION.md 3.7, checked against the file)"},
    "vllm/microsoft/phi-4|default": {
        "native_window": 16384, "hf_id": "microsoft/phi-4", "revision": "2db69c1c3e91a05d2c64a3185acfbaf36f744e25",
        "field": "max_position_embeddings", "source": "roster entry; served at 16,384 (HEADLINE_MODEL_SELECTION.md 3.7)"},
}


# One B200's KV cache at 0.90 utilisation, in tokens, as HEADLINE_MODEL_SELECTION.md 3.7 tabulates it from the stage-1
# server logs ("GPU KV cache size").  The COMMITTED selection/context_e6.csv carries no kv_tokens -- it was written on a
# machine without the logs -- which is why its R_context never left "conditional"; the document's table was written
# with them.  Used only where the CSV's column is empty, and recorded as such in windows.json.  The pilot's own servers
# re-read the number into servers.json (`--stages summarise --server-logs`).
KV_TOKENS_DOC = {
    "vllm/google/gemma-4-31b-it|default": 116137, "vllm/google/gemma-4-e4b-it|default": 2660804,
    "vllm/openai/gpt-oss-20b|default": 3139385, "vllm/meta/muse-glimmer-30b|default": 2016825,
    "vllm/allenai/olmo-3.1-32b-instruct|default": 394123, "vllm/mistralai/ministral-3-14b-instruct-2512|default": 859728,
    "vllm/meta-llama/llama-3.1-8b-instruct|default": 1169904, "vllm/meta-llama/llama-3.1-70b-instruct|default": 79952,
    "vllm/microsoft/phi-4|default": 681360,
}
# The same document's rho (each model's own tokens per o200k token) is 1.01-1.06 where the committed CSV's is 0.88-0.93,
# so its needs are about 13 % larger: OLMo's full level is 64.5k tokens there against 57.0k in the CSV.  The CSV is the
# file of record and is what the tables below read; the document's full-level need is carried beside it so the served
# length is judged against the larger of the two.
FULL_NEED_DOC = {
    "vllm/google/gemma-4-31b-it|default": 65500, "vllm/google/gemma-4-e4b-it|default": 65700,
    "vllm/openai/gpt-oss-20b|default": 95200, "vllm/meta/muse-glimmer-30b|default": 93900,
    "vllm/allenai/olmo-3.1-32b-instruct|default": 64500, "vllm/mistralai/ministral-3-14b-instruct-2512|default": 66200,
    "vllm/meta-llama/llama-3.1-8b-instruct|default": 94500, "vllm/meta-llama/llama-3.1-70b-instruct|default": 63600,
    "vllm/microsoft/phi-4|default": 63400,
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ts(s: str) -> float:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def level_arms() -> Dict:
    """level -> (static arm, memory arm), from the registry, checked against this file's LEVELS."""
    from experiments.arms_v2 import CONTEXT_LEVELS
    if tuple(CONTEXT_LEVELS) != LEVELS:
        raise SystemExit(f"experiments.arms_v2.CONTEXT_LEVELS is {tuple(CONTEXT_LEVELS)}; this pilot reads {LEVELS}")
    return dict(CONTEXT_LEVELS)


def arm_table() -> Dict[str, tuple]:
    """arm -> (level, 'static' | 'memory')."""
    out = {}
    for lvl, (s, m) in level_arms().items():
        out[s] = (lvl, "static")
        out[m] = (lvl, "memory")
    return out


def f2(df: int) -> float:
    return df / stats.chi2.ppf(1 - Q, df)


def e6_runs_per_model(seeds: int) -> int:
    """E6's run count per model at `seeds` per cell: four levels x two arms x twelve cells."""
    return len(LEVELS) * len(ARMS) * N_CELLS * seeds


# ================================================================================================ shape
def shape_table(reference_seeds: int = G.S_STAGE2) -> pd.DataFrame:
    g_ref = e6_runs_per_model(reference_seeds) / f2(E85_DF_D)
    rows = []
    for sp in SP_CANDIDATES:
        runs = len(LEVELS) * len(ARMS) * N_CELLS * sp
        pairs = N_CELLS * sp                      # per level
        df = pairs - N_CELLS                      # per level: the limit is per level, never pooled across levels
        rows.append({"seeds_per_cell": sp, "runs": runs, "pairs_per_level": pairs, "df_d_per_level": df,
                     "f2": f2(df), "f": math.sqrt(f2(df)), "expected_total_runs_per_model": runs + f2(df) * g_ref})
    return pd.DataFrame(rows)


def stage_shape() -> dict:
    t = shape_table()
    best = t.sort_values(["expected_total_runs_per_model", "seeds_per_cell"]).iloc[0]
    doc = {"registered": "PREREG_PHASE_9.md 2 (the shape rule), applied to E6's own counts; PREREG_PHASE_9_STAGE2_E6_PILOT.md 2",
           "reference_seeds": G.S_STAGE2, "e6_runs_at_reference": e6_runs_per_model(G.S_STAGE2),
           "G_ref": e6_runs_per_model(G.S_STAGE2) / f2(E85_DF_D), "e8_5_df_d": E85_DF_D, "f2_at_e8_5_df_d": f2(E85_DF_D),
           "levels": [str(l) for l in LEVELS], "cells": N_CELLS, "arms_per_level": len(ARMS),
           "table": json.loads(t.to_json(orient="records")), "chosen_seeds_per_cell": int(best["seeds_per_cell"]),
           "chosen_runs_per_model": int(best["runs"]), "chosen_pairs_per_level": int(best["pairs_per_level"]),
           "chosen_df_d_per_level": int(best["df_d_per_level"]), "chosen_f": float(best["f"]),
           "generated_utc": _utc()}
    os.makedirs(OUT, exist_ok=True)
    json.dump(doc, open(os.path.join(OUT, "shape.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(t.round(3).to_string(index=False))
    print(f"chosen: {doc['chosen_seeds_per_cell']} seeds per cell, {doc['chosen_runs_per_model']} runs per model, "
          f"df_d {doc['chosen_df_d_per_level']} per level, limit factor {doc['chosen_f']:.3f}")
    return doc


# ================================================================================================ windows
def _config_window(path: str) -> Optional[int]:
    """max_position_embeddings from a config.json, at the top level or inside text_config."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    for block in (d, d.get("text_config") or {}):
        v = block.get("max_position_embeddings")
        if v is not None:
            return int(v)
    return None


def check_cache(hf_home: str) -> dict:
    """For every window read on the Hub: the same field from the local cache's config.json at the pinned revision, when
    the cache holds it (the cluster's does; a laptop's usually does not).  A disagreement is an error, not a note."""
    out = {}
    for key, w in WINDOWS_READ.items():
        org, name = w["hf_id"].split("/", 1)
        f = os.path.join(hf_home, "hub", f"models--{org}--{name}", "snapshots", w["revision"], "config.json")
        if os.path.exists(f):
            v = _config_window(f)
            if v != w["native_window"] and w["field"] != "model_max_length":
                raise SystemExit(f"{key}: config.json in the cache says max_position_embeddings {v}, this file {w['native_window']}")
            out[key] = {"checked_against_file": True, "cache_value": v, "path": f}
        else:
            out[key] = {"checked_against_file": False, "cache_value": None, "path": f}
    return out


def context_table(windows: Dict[str, int], served_max_len: int = SERVED_MAX_LEN) -> pd.DataFrame:
    """The selection's context table re-read against known windows and the pilot's serving length.

    `need` is the selection's: the context plus the largest reply of any stage-1 call (p99 of the per-run maxima),
    each model's own tokens.  `fits_window` is the rule's criterion (need <= the native window).  The served length
    caps every reply at (served - context), so a runaway cannot overflow; what matters operationally is that the
    context plus a TYPICAL largest reply fits, and that is `fits_served`.  The in-flight budget is the KV cache over
    the context plus the typical largest reply (`workers_typical`), with the p99 case beside (`workers_p99`)."""
    cx = pd.read_csv(os.path.join(SEL, "context_e6.csv"))
    rows = []
    for _, r in cx.iterrows():
        key = r["Model"]
        nw = windows.get(key)
        served = min(nw, served_max_len) if nw else None
        typical = float(r["context_tokens"]) + float(r["run_max_output_median"])
        need = float(r["need_tokens"])
        kv_csv = float(r["kv_tokens"]) if pd.notna(r["kv_tokens"]) else None
        kv = kv_csv if kv_csv else KV_TOKENS_DOC.get(key)
        rows.append({"Model": key, "label": r["label"], "level": str(r["level"]), "context_tokens": float(r["context_tokens"]),
                     "run_max_output_median": float(r["run_max_output_median"]),
                     "largest_output_per_call": float(r["largest_output_per_call"]), "need_tokens": need,
                     "need_typical": typical, "native_window": nw, "served_len": served,
                     "fits_window": (need <= nw) if nw else None,
                     "fits_served": (typical <= served) if served else None,
                     "reply_room_at_served": (served - float(r["context_tokens"])) if served else None,
                     "full_need_doc_3_7": FULL_NEED_DOC.get(key) if str(r["level"]) == "full" else None,
                     "fits_window_doc_3_7": (FULL_NEED_DOC[key] <= nw) if (nw and str(r["level"]) == "full" and key in FULL_NEED_DOC) else None,
                     "kv_tokens": kv, "kv_source": "context_e6.csv" if kv_csv else ("HEADLINE_MODEL_SELECTION.md 3.7" if kv else None),
                     "max_concurrent_runs": int(kv // need) if kv else np.nan,
                     "workers_typical": int(min(OPERATING_POINT, kv // typical)) if kv else np.nan,
                     "workers_p99": int(min(OPERATING_POINT, kv // min(need, served or need))) if kv else np.nan})
    return pd.DataFrame(rows)


def r_context_table(ctx: pd.DataFrame) -> pd.DataFrame:
    from tools.phase9.e9_4_select import context_status
    req = pd.read_csv(os.path.join(SEL, "requirements.csv")).set_index("Model")
    out = []
    for key, g in ctx.groupby("Model", sort=False):
        g = g.set_index("level").loc[[str(l) for l in LEVELS]]
        out.append({"Model": key, "label": g["label"].iloc[0], "native_window": g["native_window"].iloc[0],
                    "R_context_selection": req.loc[key, "R_context"],
                    "R_context": context_status(g["fits_window"].tolist(), g["max_concurrent_runs"].tolist()),
                    "R_effect": bool(req.loc[key, "R_effect"]),
                    "full_need_tokens": float(g.loc["full", "need_tokens"]),
                    "full_need_doc_3_7": g.loc["full", "full_need_doc_3_7"],
                    "fits_window_doc_3_7": g.loc["full", "fits_window_doc_3_7"],
                    "full_reply_room_at_served": g.loc["full", "reply_room_at_served"],
                    "full_max_concurrent": g.loc["full", "max_concurrent_runs"]})
    return pd.DataFrame(out)


def e6_roster(rc: pd.DataFrame) -> list:
    """The selection's rule for E6 (CRITERIA; e9_4_select.EXPERIMENT_REQ): core members meeting R_effect and R_context."""
    from tools.phase9 import e9_roster as RO
    t = rc.set_index("Model")
    return [k for k in RO.CORE_OPEN if bool(t.loc[k, "R_effect"]) and t.loc[k, "R_context"] == "met"]


def stage_windows(hf_home: str = "") -> dict:
    hf_home = hf_home or os.environ.get("HF_HOME") or os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
    cache = check_cache(hf_home)
    windows = {k: w["native_window"] for k, w in WINDOWS_READ.items()}
    ctx = context_table(windows)
    rc = r_context_table(ctx)
    roster = e6_roster(rc)
    flipped = rc[(rc["R_context_selection"] == "conditional") & (rc["R_context"] != "conditional")]
    doc = {"registered": "PREREG_PHASE_9_STAGE2_E6_PILOT.md 1; HEADLINE_MODEL_SELECTION.md 3.7, 6 (the three unread windows)",
           "served_max_len": SERVED_MAX_LEN, "windows": {k: {**w, **cache[k]} for k, w in WINDOWS_READ.items()},
           "kv_tokens_source": {k: ctx.loc[ctx["Model"] == k, "kv_source"].iloc[0] for k in ctx["Model"].unique()},
           "note_committed_csv": "selection/context_e6.csv carries no kv_tokens and a rho of 0.88-0.93 where the document's "
                                 "table has the KV sizes and rho 1.01-1.06; the KV sizes are taken from the document "
                                 "(KV_TOKENS_DOC) and the document's full-level needs are checked beside the CSV's "
                                 "(fits_window_doc_3_7)",
           "r_context": json.loads(rc.to_json(orient="records")),
           "resolved_from_conditional": flipped["Model"].tolist(),
           "e6_roster": roster, "e6_roster_n": len(roster), "plan_e6_models": 4,
           "rule": "e9_4_select.EXPERIMENT_REQ['E6'] = (R_effect, R_context) over e9_roster.CORE_OPEN",
           "generated_utc": _utc()}
    os.makedirs(OUT, exist_ok=True)
    json.dump(doc, open(os.path.join(OUT, "windows.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    rc.to_csv(os.path.join(OUT, "r_context.csv"), index=False, lineterminator="\n")
    ctx.to_csv(os.path.join(OUT, "workers.csv"), index=False, lineterminator="\n")
    print(rc.to_string(index=False))
    print(ctx[ctx["Model"].isin(roster)][["label", "level", "context_tokens", "need_tokens", "served_len", "fits_served",
                                          "reply_room_at_served", "workers_typical", "workers_p99"]].to_string(index=False))
    print("E6 roster by the rule:", roster)
    return doc


def load_windows() -> dict:
    p = os.path.join(OUT, "windows.json")
    if not os.path.exists(p):
        raise SystemExit(f"{os.path.relpath(p, ROOT)} does not exist: run `e9_4_context_pilot --stages windows` first")
    return json.load(open(p, encoding="utf-8"))


# ================================================================================================ projection
def projection_table(roster: list, seeds_pilot: int) -> pd.DataFrame:
    """GPU-seconds per run per level = Phase 8's measured input tokens per run at that level (v2_1 harness, Flash's
    tokens; `e8_2/context_cost.json`) over stage 1's measured input tokens per GPU-second for the model (`cost.csv`).
    Stage 1's rate blends prefill and decode at 1.8k-token prompts; at 60k the prefill share is larger and a prefix
    cache may or may not help, so this is a projection with a stated basis, and the pilot measures the truth."""
    cc = json.load(open(os.path.join(GEN, "e8_2", "context_cost.json"), encoding="utf-8"))
    tok = {}
    for r in cc["table"]:
        if r["harness"] != "v2_1":
            continue
        lv = r["level"]
        name = {"rolling 5": "5", "rolling 20": "20", "rolling 50": "50", "full (60k)": "full", "stateless": "stateless"}.get(lv)
        if name:
            tok[name] = float(r["input_tokens_per_run"])
    cost = pd.read_csv(os.path.join(SEL, "cost.csv")).set_index("Model")
    rows = []
    for key in roster:
        rate = float(cost.loc[key, "input_tokens_per_gpu_second"])
        for lvl in LEVELS:
            gpus = tok[str(lvl)] / rate
            rows.append({"Model": key, "label": cost.loc[key, "label"], "level": str(lvl),
                         "input_tokens_per_run_v2_1": tok[str(lvl)], "x_stateless": tok[str(lvl)] / tok["stateless"],
                         "stage1_input_tokens_per_gpu_second": rate, "stage1_gpu_hours_per_run": float(cost.loc[key, "gpu_hours_per_run"]),
                         "projected_gpu_seconds_per_run": gpus, "projected_gpu_hours_per_run": gpus / 3600.0,
                         "pilot_runs": len(ARMS) * N_CELLS * seeds_pilot,
                         "pilot_gpu_hours": len(ARMS) * N_CELLS * seeds_pilot * gpus / 3600.0,
                         "e6_runs_S60": len(ARMS) * N_CELLS * G.S_STAGE2,
                         "e6_gpu_hours_S60": len(ARMS) * N_CELLS * G.S_STAGE2 * gpus / 3600.0})
    return pd.DataFrame(rows)


def stage_project() -> dict:
    shape = json.load(open(os.path.join(OUT, "shape.json"), encoding="utf-8"))
    w = load_windows()
    if not w["e6_roster"]:
        raise SystemExit("windows.json assigns no model to E6; nothing to project")
    t = projection_table(w["e6_roster"], int(shape["chosen_seeds_per_cell"]))
    per_model = t.groupby("label", sort=False)[["pilot_gpu_hours", "e6_gpu_hours_S60"]].sum()
    doc = {"basis": "e8_2/context_cost.json (v2_1 input tokens per run per level, n = 3 pilot runs on Gemini 2.5 Flash) over "
                    "selection/cost.csv input_tokens_per_gpu_second (stage 1, n = 2,928 runs per model at ~1.8k-token prompts)",
           "status": "PROJECTION: the prefill rate at 60k tokens is not measured; the pilot measures it (prediction P1 "
                     f"holds if every measured level is within a factor {PROJECTION_BAR} of this)",
           "seeds_per_cell_pilot": int(shape["chosen_seeds_per_cell"]), "roster": w["e6_roster"],
           "pilot_gpu_hours_total": float(t["pilot_gpu_hours"].sum()), "e6_gpu_hours_S60_total": float(t["e6_gpu_hours_S60"].sum()),
           "per_model": json.loads(per_model.to_json(orient="index")), "table": json.loads(t.to_json(orient="records")),
           "generated_utc": _utc()}
    json.dump(doc, open(os.path.join(OUT, "projection.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    t.to_csv(os.path.join(OUT, "projection.csv"), index=False, lineterminator="\n")
    print(t[["label", "level", "x_stateless", "projected_gpu_hours_per_run", "pilot_gpu_hours", "e6_gpu_hours_S60"]].round(4).to_string(index=False))
    print(f"pilot {doc['pilot_gpu_hours_total']:.1f} GPU-h projected; E6 at S = 60 {doc['e6_gpu_hours_S60_total']:.0f} GPU-h projected")
    return doc


# ================================================================================================ summarise (cluster)
def summarise_run(csv_path: str, usage_path: str) -> dict:
    df = pd.read_csv(csv_path)
    u = json.load(open(usage_path, encoding="utf-8"))
    calls = u.get("calls") or []
    outs = [int(c.get("out") or 0) for c in calls]
    ins = [int(c.get("in") or 0) for c in calls]
    ct = pd.to_numeric(df.get("Context_Tokens"), errors="coerce") if "Context_Tokens" in df else pd.Series(dtype=float)
    ps = df["Parse_Status"].astype(str) if "Parse_Status" in df else pd.Series(dtype=str)
    method = sorted(df["Token_Count_Method"].dropna().astype(str).unique().tolist()) if "Token_Count_Method" in df else []
    return {"n_days": int(len(df)), "context_tokens_max": float(ct.max()) if len(ct) else np.nan,
            "context_tokens_day1": float(ct.iloc[0]) if len(ct) else np.nan,
            "context_tokens_last": float(ct.iloc[-1]) if len(ct) else np.nan,
            "context_turns_max": float(pd.to_numeric(df["Context_Turns"], errors="coerce").max()) if "Context_Turns" in df else np.nan,
            "mandate_copies_max": float(pd.to_numeric(df["Mandate_Copies_In_Context"], errors="coerce").max()) if "Mandate_Copies_In_Context" in df else np.nan,
            "mandate_offset_last": float(pd.to_numeric(df["Mandate_Offset_Tokens"], errors="coerce").iloc[-1]) if "Mandate_Offset_Tokens" in df else np.nan,
            "token_count_methods": "|".join(method),
            "history_fallback_turns": float(pd.to_numeric(df["History_Fallback_Turns"], errors="coerce").iloc[-1]) if "History_Fallback_Turns" in df else np.nan,
            "n_fallback": int((ps == "fallback").sum()), "n_retry": int(ps.str.startswith("ok_retry").sum()),
            "n_calls": len(calls), "input_tokens": int(sum(ins)), "output_tokens": int(sum(outs)),
            "max_input_per_call": int(max(ins)) if ins else 0, "max_output_per_call": int(max(outs)) if outs else 0,
            "n_calls_runaway": int(sum(1 for o in outs if o >= RUNAWAY_TOKENS)), "seconds": float(u.get("seconds") or np.nan),
            "status": u.get("status")}


def stage_summarise(server_logs: str = "") -> pd.DataFrame:
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    m = R.load_manifest(os.path.join(E94, G.CONTEXT_PILOT_MANIFEST))
    at = arm_table()
    rows = []
    for key in m["configs"]:
        mc = RO.by_key(key)
        done = R.done_keys(m["subdir"], mc, m["cells"])
        for c in m["cells"]:
            cfg = R.cfg_for(mc, c, m["subdir"])
            if R.run_key(c, cfg) not in done:
                continue
            p = R.run_paths(cfg)
            lvl, kind = at[c["arm"]]
            rows.append({"Model": key, "Persona": c["persona"], "Arm": c["arm"], "Level": str(lvl), "Arm_Kind": kind,
                         "Scenario": c["scenario"], "Seed": int(c["seed"]), "run_key": R.run_key(c, cfg),
                         **summarise_run(p["csv"], p["usage"])})
    t = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    t.to_csv(os.path.join(OUT, "per_run_context.csv"), index=False, lineterminator="\n")
    servers = {}
    for f in sorted(glob.glob(server_logs)) if server_logs else []:
        name = kv = maxlen = None
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if name is None:
                    mm = re.search(r"'served_model_name': \['([^']+)'\]", line)
                    name = mm.group(1) if mm else None
                if kv is None:
                    mm = re.search(r"GPU KV cache size: ([\d,]+) tokens", line)
                    kv = int(mm.group(1).replace(",", "")) if mm else None
                if maxlen is None:
                    mm = re.search(r"Using max model len (\d+)", line)
                    maxlen = int(mm.group(1)) if mm else None
                if name and kv and maxlen:
                    break
        servers[os.path.basename(f)] = {"served_model_name": name, "kv_tokens": kv, "max_model_len": maxlen}
    json.dump({"servers": servers, "n_runs": int(len(t)), "generated_utc": _utc()},
              open(os.path.join(OUT, "servers.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"summarised {len(t)} runs; {len(servers)} server logs")
    return t


# ================================================================================================ analyse (laptop)
def pilot_keys(m: dict) -> Dict[str, tuple]:
    """run_key -> (Model, level, arm kind) for every planned run of the pilot."""
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    at = arm_table()
    out = {}
    for key in m["configs"]:
        mc = RO.by_key(key)
        for c in m["cells"]:
            cfg = R.cfg_for(mc, c, m["subdir"])
            out[R.run_key(c, cfg)] = (key, str(at[c["arm"]][0]), at[c["arm"]][1])
    return out


def frame(per_run: pd.DataFrame) -> pd.DataFrame:
    """The scored pilot rows with `Level` and `Arm` relabelled to static / memory, so e9_2_pilot.sigma_r1 reads them."""
    at = arm_table()
    t = per_run[per_run["Arm"].isin(at)].copy()
    t["Level"] = t["Arm"].map(lambda a: str(at[a][0]))
    t["Arm"] = t["Arm"].map(lambda a: at[a][1])
    return t


def paired_sigma(d: pd.Series) -> dict:
    """sigma of a paired quantity indexed by (Persona, Scenario, Seed), centred per cell, on df = pairs - cells, with the
    chi-square one-sided 90 % limit (the closed form at R' = R, P8-15)."""
    d = d.dropna()
    grp = d.groupby(level=["Persona", "Scenario"])
    df_d = int(len(d) - grp.ngroups)
    s2 = float(((d - grp.transform("mean")) ** 2).sum() / df_d) if df_d > 0 else float("nan")
    lim = math.sqrt(df_d * s2 / stats.chi2.ppf(1 - Q, df_d)) if df_d > 0 else float("nan")
    return {"n_pairs": int(len(d)), "n_cells": int(grp.ngroups), "df_d": df_d,
            "sigma": math.sqrt(s2) if np.isfinite(s2) else float("nan"), "sigma_limit90": lim,
            "mean": float(d.mean()) if len(d) else float("nan")}


def sigma_table(t: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
    """Per model, level and metric: sigma_d(R = 1) of memory - static paired on seed."""
    from tools.phase9.e9_2_pilot import sigma_r1
    rows = []
    for (model, lvl), g in t.groupby(["Model", "Level"], sort=False):
        for metric in metrics:
            if metric not in g:
                continue
            r = sigma_r1(g.dropna(subset=[metric]), metric)
            rows.append({"Model": model, "Level": lvl, "metric": metric, "quantity": "memory - static",
                         "n_pairs": r["n_pairs"], "df_d": r["df_d"], "sigma": r["sigma_d_R1"],
                         "sigma_limit90": r["sigma_d_R1_limit90"], "mean": r["mean_d"]})
    return pd.DataFrame(rows)


def contrast_table(t: pd.DataFrame, metric: str = "band_mas") -> pd.DataFrame:
    """Per model and level L above the reference: the level contrasts, paired on (persona, scenario, seed):
    the effect at L minus the effect at 5 (the decay thesis's interaction), the static arm at L minus at 5 (the thesis's
    direct reading: with the mandate in the system prompt, adherence at a longer window) and the memory arm likewise."""
    rows = []
    for model, g in t.groupby("Model", sort=False):
        w = g.groupby(["Level", "Persona", "Scenario", "Seed", "Arm"])[metric].mean().unstack("Arm")
        if not {"static", "memory"} <= set(w.columns):
            continue
        d = (w["memory"] - w["static"]).unstack("Level")
        s = w["static"].unstack("Level")
        mm = w["memory"].unstack("Level")
        ref = str(REFERENCE_LEVEL)
        for lvl in [str(l) for l in LEVELS if str(l) != ref]:
            for name, tab in (("effect(L) - effect(5)", d), ("static(L) - static(5)", s), ("memory(L) - memory(5)", mm)):
                if lvl not in tab or ref not in tab:
                    continue
                r = paired_sigma(tab[lvl] - tab[ref])
                rows.append({"Model": model, "Level": lvl, "metric": metric, "quantity": name, **r})
    return pd.DataFrame(rows)


def sizing(sig: pd.DataFrame, con: pd.DataFrame, roster: list, alpha: float = ALPHA, delta: float = DELTA) -> dict:
    """E6's seed count by PREREG_PHASE_9.md 2's rule, one row per quantity: the plug-in is the maximum limit over the
    roster, Appendix A at alpha' with the paired-correct count beside, the MDD at the candidate seed counts."""
    from tools.phase8.e8_5_analyse import mdd, n_seeds
    out = {"alpha": alpha, "family": FAMILY, "delta": delta, "candidate_seeds": list(CANDIDATE_SEEDS), "roster": roster, "rows": []}
    bm = sig[(sig["metric"] == "band_mas") & (sig["Model"].isin(roster))]
    quantities = [("memory - static", lvl, bm[bm["Level"] == lvl]) for lvl in [str(l) for l in LEVELS]]
    cb = con[(con["metric"] == "band_mas") & (con["Model"].isin(roster))]
    for q in ("effect(L) - effect(5)", "static(L) - static(5)"):
        for lvl in [str(l) for l in LEVELS if str(l) != str(REFERENCE_LEVEL)]:
            quantities.append((q, lvl, cb[(cb["quantity"] == q) & (cb["Level"] == lvl)]))
    for q, lvl, g in quantities:
        g = g.dropna(subset=["sigma_limit90"])
        if g.empty:
            out["rows"].append({"quantity": q, "Level": lvl, "n_models": 0, "plugin": None, "seeds_appA": None})
            continue
        plug = float(g["sigma_limit90"].max())
        row = {"quantity": q, "Level": lvl, "n_models": int(len(g)), "models_missing": sorted(set(roster) - set(g["Model"])),
               "plugin": plug, "plugin_model": str(g.loc[g["sigma_limit90"].idxmax(), "Model"]),
               "seeds_appA": n_seeds(plug, delta, alpha), "seeds_paired_correct": n_seeds(plug, delta, alpha, factor2=False),
               "per_model": {r["Model"]: {"sigma": r["sigma"], "sigma_limit90": r["sigma_limit90"], "n_pairs": int(r["n_pairs"]),
                                          "seeds_appA": n_seeds(float(r["sigma_limit90"]), delta, alpha),
                                          "mdd_at": {str(S): mdd(float(r["sigma_limit90"]), S, alpha) for S in CANDIDATE_SEEDS}}
                             for _, r in g.iterrows()},
               "mdd_at_plugin": {str(S): mdd(plug, S, alpha) for S in CANDIDATE_SEEDS},
               "estimable_at_5_seeds_at_plugin": bool(mdd(plug, 5, alpha) <= delta)}
        out["rows"].append(row)
    return out


def busy_seconds(starts: np.ndarray, ends: np.ndarray) -> float:
    iv = sorted(zip(starts, ends))
    busy, cur_s, cur_e = 0.0, None, None
    for s, e in iv:
        if cur_e is None or s > cur_e:
            busy += (cur_e - cur_s) if cur_e is not None else 0.0
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        busy += cur_e - cur_s
    return busy


def cost_table(ledger_rows: List[dict], keys: Dict[str, tuple], context: Optional[pd.DataFrame], seeds_pilot: int) -> pd.DataFrame:
    """Per model and level: the busy GPU time of that level's runs (the union of the attempts' intervals, as the
    selection's cost.csv), per completed run, and E6's cost at every candidate seed count."""
    rows = []
    by = {}
    for r in ledger_rows:
        k = keys.get(r.get("run_key"))
        if k:
            by.setdefault(k[:2], []).append(r)
    for (model, lvl), led in sorted(by.items()):
        ends = np.array([_ts(r["utc"]) for r in led])
        secs = np.array([float(r["seconds"]) for r in led])
        busy = busy_seconds(ends - secs, ends)
        ok = [r for r in led if r["status"] == "ok"]
        n_ok = len({r["run_key"] for r in ok})
        gpuh = busy / 3600.0 / n_ok if n_ok else float("nan")
        row = {"Model": model, "Level": lvl, "n_attempts": len(led), "n_runs_ok": n_ok,
               "n_planned": sum(1 for k in keys.values() if k[:2] == (model, lvl)),
               "busy_hours": busy / 3600.0, "gpu_hours_per_run": gpuh,
               "mean_concurrency": float(secs.sum() / busy) if busy > 0 else float("nan"),
               "mean_run_seconds": float(np.mean([float(r["seconds"]) for r in ok])) if ok else float("nan"),
               "input_tokens_per_run": float(np.mean([float(r.get("input_tokens") or 0) for r in ok])) if ok else float("nan"),
               "output_tokens_per_run": float(np.mean([float(r.get("output_tokens") or 0) for r in ok])) if ok else float("nan")}
        if context is not None and len(context):
            c = context[(context["Model"] == model) & (context["Level"] == lvl)]
            row.update({"context_tokens_max": float(c["context_tokens_max"].max()) if len(c) else float("nan"),
                        "context_tokens_last_median": float(c["context_tokens_last"].median()) if len(c) else float("nan")})
        for S in CANDIDATE_SEEDS:
            row[f"e6_gpu_hours_S{S}"] = len(ARMS) * N_CELLS * S * gpuh
        rows.append(row)
    return pd.DataFrame(rows)


def gates_table(t: pd.DataFrame, context: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Per model and level: the selection's G2 and G3 on the pilot's own runs, and the context checks the pilot adds."""
    rows = []
    for (model, lvl), g in t.groupby(["Model", "Level"], sort=False):
        cell_fb = g.groupby(["Persona", "Scenario", "Arm"])["fallback_share"].mean() if "fallback_share" in g else pd.Series(dtype=float)
        degenerate = float((g["trade_count"] == 0).mean()) if "trade_count" in g else float("nan")
        row = {"Model": model, "Level": lvl, "n_runs": int(len(g)),
               "max_cell_fallback_share": float(cell_fb.max()) if len(cell_fb) else float("nan"),
               "G2_fallback": bool(len(cell_fb) and cell_fb.max() <= G2_FALLBACK),
               "zero_trade_share": degenerate, "G3_degenerate": bool(degenerate <= G3_DEGENERATE) if np.isfinite(degenerate) else None,
               "n_score_errors": int((g["score_error"].astype(str) != "").sum()) if "score_error" in g else 0}
        if context is not None and len(context):
            c = context[(context["Model"] == model) & (context["Level"] == lvl)]
            row.update({"context_tokens_max": float(c["context_tokens_max"].max()) if len(c) else float("nan"),
                        "context_headroom_at_served": (SERVED_MAX_LEN - float(c["context_tokens_max"].max())) if len(c) else float("nan"),
                        "runaway_run_share": float((c["n_calls_runaway"] > 0).mean()) if len(c) else float("nan"),
                        "max_output_per_call": float(c["max_output_per_call"].max()) if len(c) else float("nan"),
                        "mandate_copies_max": float(c["mandate_copies_max"].max()) if len(c) else float("nan"),
                        "copies_at_most_2": bool(len(c) and c["mandate_copies_max"].max() <= 2),
                        "token_count_methods": "|".join(sorted({m for s in c["token_count_methods"].astype(str) for m in s.split("|") if m})),
                        "history_fallback_turns_total": float(c["history_fallback_turns"].sum()) if len(c) else float("nan")})
        rows.append(row)
    return pd.DataFrame(rows)


def prediction_p1(cost: pd.DataFrame, projection: Optional[pd.DataFrame]) -> dict:
    """P1: every measured GPU-hours per run per (model, level) lies within a factor PROJECTION_BAR of the projection.
    A read of the projection METHOD, which is what E6's cost will be quoted from; unevaluated without the projection."""
    if projection is None or cost.empty:
        return {"id": "P1", "verdict": "unevaluated", "reason": "no projection or no measured cost"}
    pj = projection.set_index(["Model", "level"])["projected_gpu_hours_per_run"]
    ratios = []
    for _, r in cost.iterrows():
        if (r["Model"], r["Level"]) in pj.index and np.isfinite(r["gpu_hours_per_run"]) and r["n_runs_ok"] > 0:
            ratios.append({"Model": r["Model"], "Level": r["Level"], "measured": float(r["gpu_hours_per_run"]),
                           "projected": float(pj[(r["Model"], r["Level"])]), "ratio": float(r["gpu_hours_per_run"] / pj[(r["Model"], r["Level"])])})
    if not ratios:
        return {"id": "P1", "verdict": "unevaluated", "reason": "no (model, level) with both a projection and a completed run"}
    worst = max(max(x["ratio"], 1 / x["ratio"]) for x in ratios)
    return {"id": "P1", "verdict": "holds" if worst <= PROJECTION_BAR else "fails", "bar": PROJECTION_BAR,
            "worst_factor": worst, "n_cells": len(ratios), "rows": ratios}


def prediction_p2(sig: pd.DataFrame, roster: list, bar: float = PROJECTION_BAR) -> dict:
    """P2: at the shortest window, the stateful memory - static noise sigma_d is within a factor `bar` of the model's
    stateless noise, the RMS over the twelve stage-1 cells at 122 pairs each (selection/noise_seeds.csv).  The sizing
    rule assumes nothing about this; the prediction records whether the stateful arms are a different noise regime."""
    p = os.path.join(SEL, "noise_seeds.csv")
    if not os.path.exists(p) or sig.empty:
        return {"id": "P2", "verdict": "unevaluated", "reason": "no noise_seeds.csv or no sigma rows"}
    ns = pd.read_csv(p).set_index("Model")
    rows = []
    for k in roster:
        g = sig[(sig["Model"] == k) & (sig["Level"] == str(REFERENCE_LEVEL)) & (sig["metric"] == "band_mas")]
        if g.empty or k not in ns.index or not np.isfinite(g["sigma"].iloc[0]):
            continue
        s, ref = float(g["sigma"].iloc[0]), float(ns.loc[k, "sigma_rms_bm"])
        rows.append({"Model": k, "sigma_level5": s, "n_pairs": int(g["n_pairs"].iloc[0]), "sigma_stateless_rms": ref,
                     "n_pairs_stateless": int(ns.loc[k, "n_pairs_per_cell_bm"]) * int(ns.loc[k, "n_cells_bm"]), "ratio": s / ref})
    if not rows:
        return {"id": "P2", "verdict": "unevaluated", "reason": "no roster model with a level-5 sigma and a stateless row"}
    worst = max(max(r["ratio"], 1 / r["ratio"]) for r in rows)
    return {"id": "P2", "verdict": "holds" if worst <= bar else "fails", "bar": bar, "worst_factor": worst,
            "n_models": len(rows), "rows": rows}


def stage_analyse() -> dict:
    from tools.phase8.e8_5_analyse import metric_names
    from tools.phase9 import e9_roster as RO
    from tools.phase9 import e9_runner as R
    m = R.load_manifest(os.path.join(E94, G.CONTEXT_PILOT_MANIFEST))
    scored = os.path.join(E94, "per_run_context_pilot.csv")
    if not os.path.exists(scored):
        raise SystemExit(f"{os.path.relpath(scored, ROOT)} does not exist: run `e9_4_grid --stages score --only context_pilot` "
                         f"where the runs are, and pull the file")
    per_run = pd.read_csv(scored)
    per_run = per_run[per_run["Manifest"] == m["name"]]
    cpath = os.path.join(OUT, "per_run_context.csv")
    context = pd.read_csv(cpath, dtype={"Level": str}) if os.path.exists(cpath) else None
    t = frame(per_run)
    metrics = [x for x in metric_names() if x in t.columns]
    sig = sigma_table(t, metrics)
    con = contrast_table(t, "band_mas")
    roster = list(m["configs"])
    sz = sizing(sig, con, roster)
    keys = pilot_keys(m)
    led = []
    for key in m["configs"]:
        led += [r for r in R.read_ledger(R.ledger_file(m["ledger_dir"], RO.by_key(key))) if r.get("run_key") in keys]
    cost = cost_table(led, keys, context, int(m["seeds_per_cell"]))
    gates = gates_table(t, context)
    ppath = os.path.join(OUT, "projection.csv")
    projection = pd.read_csv(ppath, dtype={"level": str}) if os.path.exists(ppath) else None
    p1 = prediction_p1(cost, projection)
    p2 = prediction_p2(sig, roster)
    planned = {k: len(m["cells"]) for k in m["configs"]}
    done = {k: len(R.done_keys(m["subdir"], RO.by_key(k), m["cells"])) for k in m["configs"]}
    scored_n = t.groupby("Model").size().to_dict()
    short = sorted(k for k in m["configs"] if done[k] < planned[k])
    summary = {"registered": "PREREG_PHASE_9_STAGE2_E6_PILOT.md", "manifest": m["name"], "seeds_per_cell": int(m["seeds_per_cell"]),
               "roster": roster, "runs_done_vs_planned": {k: [done[k], planned[k]] for k in m["configs"]},
               "runs_scored": {k: int(scored_n.get(k, 0)) for k in m["configs"]},
               "complete": not short, "unfinished_models": short, "sizing": sz,
               "cost_per_level": json.loads(cost.to_json(orient="records")) if len(cost) else [],
               "e6_gpu_hours_at": {str(S): float(cost[f"e6_gpu_hours_S{S}"].sum()) for S in CANDIDATE_SEEDS} if len(cost) else {},
               "gates": json.loads(gates.to_json(orient="records")) if len(gates) else [],
               "predictions": [p1, p2], "generated_utc": _utc()}
    os.makedirs(OUT, exist_ok=True)
    sig.to_csv(os.path.join(OUT, "sigma.csv"), index=False, lineterminator="\n")
    con.to_csv(os.path.join(OUT, "contrasts.csv"), index=False, lineterminator="\n")
    cost.to_csv(os.path.join(OUT, "cost.csv"), index=False, lineterminator="\n")
    gates.to_csv(os.path.join(OUT, "gates.csv"), index=False, lineterminator="\n")
    json.dump(sz, open(os.path.join(OUT, "sizing.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    if len(sig):
        print(sig[sig["metric"] == "band_mas"][["Model", "Level", "n_pairs", "sigma", "sigma_limit90", "mean"]].round(4).to_string(index=False))
    for r in sz["rows"]:
        print(f"{r['quantity']:24s} L={r['Level']:4s} plug-in {r.get('plugin')} -> seeds {r.get('seeds_appA')} "
              f"(paired-correct {r.get('seeds_paired_correct')}) over {r['n_models']} models")
    if len(cost):
        print(cost[["Model", "Level", "n_runs_ok", "gpu_hours_per_run", "mean_concurrency", "e6_gpu_hours_S60"]].round(4).to_string(index=False))
    print(json.dumps({k: summary[k] for k in ("complete", "unfinished_models", "e6_gpu_hours_at")}, indent=1))
    print("P1:", p1["verdict"], " P2:", p2["verdict"])
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="shape,windows,project")
    ap.add_argument("--hf-home", default="", help="windows: the Hugging Face cache to check the config files against")
    ap.add_argument("--server-logs", default="", help="summarise: a glob of the pilot tasks' vLLM server logs")
    a = ap.parse_args(argv)
    for st in [x.strip() for x in a.stages.split(",") if x.strip()]:
        if st == "shape":
            stage_shape()
        elif st == "windows":
            stage_windows(a.hf_home)
        elif st == "project":
            stage_project()
        elif st == "summarise":
            stage_summarise(a.server_logs)
        elif st == "analyse":
            stage_analyse()
        else:
            raise SystemExit(f"unknown stage {st!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
