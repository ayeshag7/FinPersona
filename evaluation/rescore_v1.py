"""
E0: re-score every v1 T=200 run under the v2 metric definitions, alongside
trivial-policy baselines computed on the same price path.

Plan references: Section 8 item 6 (v1 -> v2 comparison by re-scoring),
Section 4.4 (band-MAS), Section 5 L4 (resolvability coverage), Section 8
items 1-3 (baselines, normalisation, unresolvable steps).

Run from the repo root:

    python -m evaluation.rescore_v1

Inputs  : results_april/<model>_200/**, results_may/{google,Qwen,meta-llama}/**
Outputs : docs/env_v2/generated/e0_rescore_v1_runs.csv
          docs/env_v2/generated/e0_rescore_v1_baselines.csv
          docs/env_v2/generated/e0_rescore_v1_summary.csv
          docs/env_v2/generated/E0_RESCORE_V1.md

Nothing outside docs/env_v2/generated/ is written.  Deterministic (the random
baseline uses fixed numpy seeds, see evaluation/baselines.py).
"""
from __future__ import annotations

import os
import re
import sys
import time
from collections import OrderedDict, defaultdict

import numpy as np
import pandas as pd

from evaluation import baselines as B

# ----------------------------------------------------------------- config ---
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(REPO, "docs", "env_v2", "generated")

APRIL_DIRS = [
    "claude_haiku_4_5_200", "claude_opus_4_6_200", "claude_sonnet_4_6_200",
    "deepseek_chat_200", "gemini_2_5_flash_200", "gemini_2_5_pro_200",
    "gemini_3_1_pro_preview_200", "gpt_4_1_200", "gpt_4_1_mini_200", "gpt_4o_200",
    "gpt_4o_mini_200", "gpt_5_4_200", "gpt_5_4_mini_200", "gpt_5_mini_200",
]
MAY_DIRS = [
    os.path.join("google", "gemma-2-9b-it"),
    os.path.join("google", "gemma-3-4b-it"),
    os.path.join("Qwen", "Qwen2.5-7B-Instruct"),
    os.path.join("meta-llama", "Llama-3.1-8B-Instruct"),
]
SCENARIOS = ("flat", "bull_trap", "crash")
FALLBACK_PREFIX = "Error after 3 attempts"
FNAME_RE = re.compile(
    r"^(?P<persona>ISFJ|INTJ|ENTJ)_(?P<agent>static|memory)_(?P<scenario>flat|bull_trap|crash)"
    r"_seed(?P<seed>\d+)(?:_discount(?P<discount>[0-9.]+))?\.csv$")
USECOLS = ["Date", "Model", "MBTI", "Agent_Type", "Scenario", "Seed", "Crash_Discount", "Phase",
           "Price", "Fundamental_Value", "Portfolio_Value", "Cash", "Holdings_Qty", "Action",
           "Quantity_Percent", "Rationale", "SMA20", "SMA60", "RSI14"]
THETAS = B.THETAS
PERSONAS = B.PERSONAS
TH05 = B.theta_key(0.05)

# metrics with direction (+1 higher is better, -1 lower is better)
HIGHER_BETTER = ["rg_v1"] + [f"rg_{B.theta_key(t)}" for t in THETAS] + \
                [f"rg_action_{B.theta_key(t)}" for t in THETAS] + ["return_pct"]
LOWER_BETTER = ["point_mas_v1", "point_mas_v2", "band_mas_v2"]
# drawdown is stored as a negative percentage; "lower drawdown" = closer to 0,
# i.e. a larger stored value is better.
BEATS_METRICS = ["rg_v1", f"rg_{TH05}", "return_pct", "point_mas_v1", "point_mas_v2",
                 "band_mas_v2", "max_drawdown_pct"]
BEATS_SET = ["always_hold", "always_buy", "always_sell", "random", "buy_day1_hold",
             "constant_mix_v1", "constant_mix_v2", "momentum", "mean_reversion",
             "v_oracle", "mandate_conditional_oracle"]


# ----------------------------------------------------------- discovery -------
def discover_runs():
    runs = []
    for d in APRIL_DIRS:
        root = os.path.join(REPO, "results_april", d)
        if not os.path.isdir(root):
            print(f"[warn] missing {root}")
            continue
        for sub in sorted(os.listdir(root)):
            p = os.path.join(root, sub)
            if os.path.isdir(p):
                runs += _walk_model_dir(p, source="april", model_dir=d[:-4] if d.endswith("_200") else d)
    for d in MAY_DIRS:
        root = os.path.join(REPO, "results_may", d)
        if not os.path.isdir(root):
            print(f"[warn] missing {root}")
            continue
        runs += _walk_model_dir(root, source="may", model_dir=os.path.basename(d))
    return runs


def _walk_model_dir(model_root, source, model_dir):
    out = []
    for dirpath, _dirs, files in os.walk(model_root):
        for fn in files:
            m = FNAME_RE.match(fn)
            if not m:
                continue
            rel = os.path.relpath(dirpath, model_root).replace("\\", "/").split("/")
            if rel[0] not in SCENARIOS:
                continue
            disc = m.group("discount")
            out.append(dict(source=source, model_dir=model_dir, path=os.path.join(dirpath, fn),
                            persona=m.group("persona"), agent_type=m.group("agent"),
                            scenario=m.group("scenario"), seed=int(m.group("seed")),
                            discount=float(disc) if disc else np.nan))
    return out


# ----------------------------------------------------------- helpers ---------
def cell_key(r):
    return (r["scenario"], r["seed"], -1.0 if np.isnan(r["discount"]) else r["discount"])


def md_table(df: pd.DataFrame, floatfmt="{:.3f}", index=False) -> str:
    d = df.reset_index() if index else df
    cols = list(d.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |",
             "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in d.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, (float, np.floating)):
                cells.append("nan" if np.isnan(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def index_baselines(bl: pd.DataFrame) -> dict:
    """Index a cell's baseline table as {(policy, persona, theta_key, mas_persona): row-dict}.

    Random is indexed by its seed-mean row (random_seed == -1) only.
    """
    idx = {}
    for rec in bl.to_dict("records"):
        if rec["policy"] == "random" and rec["random_seed"] != -1:
            continue
        th = rec["theta"]
        tk = "" if (th is None or (isinstance(th, float) and np.isnan(th))) else B.theta_key(float(th))
        idx[(rec["policy"], rec["persona"] or "", tk, rec["mas_persona"])] = rec
    return idx


def pick(idx: dict, policy, persona=None, theta=None, mas_persona=None):
    """Select one baseline row (dict) from an indexed cell table (see index_baselines)."""
    persona = persona or ""
    tk = "" if theta is None else B.theta_key(theta)
    if mas_persona is None:
        mas_persona = persona
    return idx.get((policy, persona, tk, mas_persona))


# minimum usable (ceiling - floor) gap for normalisation; below this (or when the
# ceiling is not above the floor) the normalised score is NaN and flagged.
NORM_MIN_GAP = {"rg": 1.0, "return": 1.0, "mas": 0.01}


# ------------------------------------------------------------- main ----------
def main():
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    runs = discover_runs()
    print(f"discovered {len(runs)} run files")

    # ---- load all runs ------------------------------------------------------
    loaded = []
    bad = []
    for i, r in enumerate(runs):
        try:
            df = pd.read_csv(r["path"], usecols=lambda c: c in USECOLS)
        except Exception as e:  # noqa: BLE001
            bad.append((r["path"], repr(e)))
            continue
        if len(df) == 0:
            bad.append((r["path"], "empty"))
            continue
        r = dict(r)
        r["df"] = df
        r["model_col"] = str(df["Model"].iloc[0]) if "Model" in df else ""
        loaded.append(r)
        if (i + 1) % 500 == 0:
            print(f"  loaded {i + 1}/{len(runs)}  ({time.time() - t0:.0f}s)")
    print(f"loaded {len(loaded)} runs, {len(bad)} unreadable  ({time.time() - t0:.0f}s)")

    # ---- group into cells, check path identity -------------------------------
    cells = defaultdict(list)
    for r in loaded:
        cells[cell_key(r)].append(r)
    path_variants = {}          # (cell, variant) -> reference run
    mismatches = []
    for ck in sorted(cells):
        refs = []                # list of (variant_idx, ref_run)
        for r in cells[ck]:
            df = r["df"]
            P = df["Price"].to_numpy(float); V = df["Fundamental_Value"].to_numpy(float)
            found = None
            for vi, ref in refs:
                rp = ref["df"]["Price"].to_numpy(float); rv = ref["df"]["Fundamental_Value"].to_numpy(float)
                if len(rp) == len(P) and np.allclose(rp, P, rtol=1e-9, atol=1e-6) and \
                        np.allclose(rv, V, rtol=1e-9, atol=1e-6):
                    found = vi
                    break
            if found is None:
                found = len(refs)
                refs.append((found, r))
                path_variants[(ck, found)] = r
                if found > 0:
                    mismatches.append(dict(scenario=ck[0], seed=ck[1], discount=ck[2], variant=found,
                                           example=os.path.relpath(r["path"], REPO),
                                           n_rows=len(df), ref_rows=len(refs[0][1]["df"])))
            r["variant"] = found
    print(f"{len(cells)} cells, {len(path_variants)} distinct price paths, {len(mismatches)} mismatching run-paths")

    # ---- baselines per distinct path -----------------------------------------
    bl_tables = {}
    bl_index = {}
    bl_rows = []
    for (ck, vi), ref in path_variants.items():
        df = ref["df"]
        tab = B.baseline_metric_table(df["Price"].to_numpy(float), df["Fundamental_Value"].to_numpy(float),
                                      df["SMA20"].to_numpy(float), df["SMA60"].to_numpy(float),
                                      df["RSI14"].to_numpy(float))
        bl_tables[(ck, vi)] = tab
        bl_index[(ck, vi)] = index_baselines(tab)
        tab2 = tab.copy()
        tab2.insert(0, "scenario", ck[0]); tab2.insert(1, "seed", ck[1])
        tab2.insert(2, "discount", np.nan if ck[2] < 0 else ck[2]); tab2.insert(3, "path_variant", vi)
        bl_rows.append(tab2)
    bl_all = pd.concat(bl_rows, ignore_index=True)
    bl_all.to_csv(os.path.join(OUT_DIR, "e0_rescore_v1_baselines.csv"), index=False)
    print(f"baselines done ({time.time() - t0:.0f}s)")

    # ---- coverage by scenario x phase (from reference paths) -----------------
    cov_rows = []
    for (ck, vi), ref in path_variants.items():
        df = ref["df"]
        with np.errstate(divide="ignore", invalid="ignore"):
            x = np.log(df["Price"].to_numpy(float) / df["Fundamental_Value"].to_numpy(float))
        ph = df["Phase"].astype(str).to_numpy()
        for t in range(len(x)):
            cov_rows.append((ck[0], ph[t], abs(x[t])))
    cov = pd.DataFrame(cov_rows, columns=["scenario", "phase", "absx"])
    for th in THETAS:
        cov[f"theta_{B.theta_key(th)}"] = (cov["absx"] >= th).astype(float)
    cov_tab = cov.groupby(["scenario", "phase"], sort=False).agg(
        n_steps=("absx", "size"), mean_abs_x=("absx", "mean"),
        **{f"cov_{B.theta_key(th)}": (f"theta_{B.theta_key(th)}", "mean") for th in THETAS}).reset_index()
    cov_scen = cov.groupby("scenario", sort=False).agg(
        n_steps=("absx", "size"), mean_abs_x=("absx", "mean"),
        **{f"cov_{B.theta_key(th)}": (f"theta_{B.theta_key(th)}", "mean") for th in THETAS}).reset_index()

    # ---- per-run metrics ------------------------------------------------------
    rows = []
    for r in loaded:
        df = r["df"]
        rat = df["Rationale"].astype("string").fillna("")
        fb = rat.str.startswith(FALLBACK_PREFIX).to_numpy(bool)
        persona = r["persona"]
        m = B.compute_run_metrics(df["Price"].to_numpy(float), df["Fundamental_Value"].to_numpy(float),
                                  df["Portfolio_Value"].to_numpy(float), df["Cash"].to_numpy(float),
                                  df["Holdings_Qty"].to_numpy(float), df["Action"].astype(str).to_numpy(),
                                  persona, fallback_mask=fb)
        ck = cell_key(r)
        bl = bl_index[(ck, r["variant"])]
        rec = OrderedDict(
            source=r["source"], model=r["model_dir"], model_col=r["model_col"], persona=persona,
            agent_type=r["agent_type"], scenario=r["scenario"], seed=r["seed"],
            discount=np.nan if np.isnan(r["discount"]) else r["discount"], path_variant=r["variant"],
            file=os.path.relpath(r["path"], REPO).replace("\\", "/"))
        rec.update(m)
        # fallback action mix
        acts = df["Action"].astype(str).to_numpy()
        rec["fallback_hold_rows"] = int(((acts == "HOLD") & fb).sum())
        rec["cash_share_day1"] = float(df["Cash"].iloc[0] / df["Portfolio_Value"].iloc[0]) \
            if df["Portfolio_Value"].iloc[0] > 0 else np.nan

        # --- floor / ceiling / normalised ---
        ah = pick(bl, "always_hold", mas_persona=persona)
        rd = pick(bl, "random", mas_persona=persona)
        b1 = pick(bl, "buy_day1_hold", mas_persona=persona)
        ab = pick(bl, "always_buy", mas_persona=persona)
        asl = pick(bl, "always_sell", mas_persona=persona)
        mco = pick(bl, "mandate_conditional_oracle", persona=persona, theta=0.05)
        cm1 = pick(bl, "constant_mix_v1", persona=persona)
        cm2 = pick(bl, "constant_mix_v2", persona=persona)
        for met in HIGHER_BETTER:
            cands = [ah[met], rd[met], b1[met]]
            floor = np.nanmax(cands) if np.any(np.isfinite(cands)) else np.nan
            ceil = mco[met]
            rec[f"floor_{met}"] = floor
            rec[f"ceil_{met}"] = ceil
            den = ceil - floor
            gap = NORM_MIN_GAP["return" if met == "return_pct" else "rg"]
            ok = bool(np.isfinite(den) and den >= gap)
            rec[f"norm_{met}"] = (m[met] - floor) / den if (ok and np.isfinite(m[met])) else np.nan
            rec[f"norm_degenerate_{met}"] = int(not ok)
            if met in ("rg_v1", f"rg_{TH05}", "return_pct"):
                rec[f"bl_always_hold_{met}"] = ah[met]
                rec[f"bl_random_{met}"] = rd[met]
                rec[f"bl_buy_day1_hold_{met}"] = b1[met]
                rec[f"bl_mco_0.05_{met}"] = mco[met]
        for met in LOWER_BETTER:
            cands = [ab[met], asl[met], rd[met]]
            floor = np.nanmax(cands) if np.any(np.isfinite(cands)) else np.nan
            ceil = (cm1 if met == "point_mas_v1" else cm2)[met]
            rec[f"floor_{met}"] = floor
            rec[f"ceil_{met}"] = ceil
            den = floor - ceil
            ok = bool(np.isfinite(den) and den >= NORM_MIN_GAP["mas"])
            rec[f"norm_{met}"] = (floor - m[met]) / den if (ok and np.isfinite(m[met])) else np.nan
            rec[f"norm_degenerate_{met}"] = int(not ok)
        # --- beats k of n ---
        for met in BEATS_METRICS:
            k = 0; n = 0
            av = m[met]
            for pol in BEATS_SET:
                if pol in ("constant_mix_v1", "constant_mix_v2"):
                    row = pick(bl, pol, persona=persona)
                elif pol == "mandate_conditional_oracle":
                    row = pick(bl, pol, persona=persona, theta=0.05)
                elif pol == "v_oracle":
                    row = pick(bl, pol, theta=0.05, mas_persona=persona)
                else:
                    row = pick(bl, pol, mas_persona=persona)
                if row is None or not np.isfinite(row[met]) or not np.isfinite(av):
                    continue
                n += 1
                bv = row[met]
                if met in LOWER_BETTER:
                    k += int(av < bv - 1e-12)
                else:   # higher better, including max_drawdown_pct (negative, closer to 0 is better)
                    k += int(av > bv + 1e-12)
            rec[f"beats_k_{met}"] = k if np.isfinite(av) else np.nan
            rec[f"beats_n_{met}"] = n
        rows.append(rec)
    runs_df = pd.DataFrame(rows)
    runs_df.to_csv(os.path.join(OUT_DIR, "e0_rescore_v1_runs.csv"), index=False)
    print(f"run metrics done: {len(runs_df)} rows ({time.time() - t0:.0f}s)")

    # ---- summary ---------------------------------------------------------------
    id_cols = ["model", "persona", "agent_type", "scenario"]
    num_cols = [c for c in runs_df.columns if c not in id_cols + ["source", "model_col", "file"]
                and pd.api.types.is_numeric_dtype(runs_df[c])]
    summ = runs_df.groupby(id_cols, sort=True)[num_cols].mean().reset_index()
    cnt = runs_df.groupby(id_cols, sort=True).size().rename("n_runs").reset_index()
    summ = cnt.merge(summ, on=id_cols)
    summ.to_csv(os.path.join(OUT_DIR, "e0_rescore_v1_summary.csv"), index=False)

    # ---- report ----------------------------------------------------------------
    write_report(runs_df, bl_all, cov_tab, cov_scen, mismatches, bad, loaded, t0)
    print(f"all done ({time.time() - t0:.0f}s)")


# ------------------------------------------------------------- report --------
def write_report(runs_df, bl_all, cov_tab, cov_scen, mismatches, bad, loaded, t0):
    L = []
    A = L.append
    A("# E0 — Re-scoring of the v1 T=200 runs under the v2 metric definitions\n")
    A("Generated by `python -m evaluation.rescore_v1` (plan Section 8 item 6; Section 4.4; "
      "Section 5 L4; Section 8 items 1-3). All numbers below are computed from the run CSVs in "
      "`results_april/*_200` and `results_may/{google,Qwen,meta-llama}`; baselines are simulated on "
      "the same price path as the cell (scenario x seed x discount), $10,000 initial cash, zero "
      "shares, 100 percent cash start, same-day execution, fractional shares, no cost.\n")
    A("Files: `e0_rescore_v1_runs.csv` (one row per run), `e0_rescore_v1_baselines.csv` (one row per "
      "cell x baseline x persona x theta), `e0_rescore_v1_summary.csv` (means per model x persona x "
      "agent_type x scenario).\n")

    # ---- 1. inventory -------------------------------------------------------
    A("## 1. Data inventory and parse-fallback rows\n")
    A(f"- Run CSVs loaded: **{len(runs_df)}** ({len(bad)} unreadable/empty). "
      f"Models: {runs_df.model.nunique()} ({(runs_df.source == 'april').sum()} runs from results_april, "
      f"{(runs_df.source == 'may').sum()} from results_may).")
    A(f"- Rows per run: min {runs_df.n_rows.min()}, max {runs_df.n_rows.max()}; "
      f"runs with fewer than 200 rows: {(runs_df.n_rows < 200).sum()}.")
    A(f"- Parse-fallback rows (Rationale starts with `{FALLBACK_PREFIX}`): "
      f"**{int(runs_df.n_fallback.sum())}** rows in {int((runs_df.n_fallback > 0).sum())} runs "
      f"({runs_df.fallback_frac.mean() * 100:.2f} percent of all rows); "
      f"{int(runs_df.fallback_hold_rows.sum())} of those fallback rows carry Action=HOLD. "
      "Fallback rows are excluded from RG and trade counts but kept in the portfolio state.")
    A(f"- Price/fundamental path identity across runs of a cell: {len(mismatches)} run(s) whose "
      f"(Price, Fundamental_Value) path differs from the cell's reference path (tolerance rtol 1e-9, atol 1e-6)."
      + (" Mismatches get their own baselines (column `path_variant` > 0)." if mismatches else ""))
    if mismatches:
        A("  Mismatching runs by model x scenario (each such run is scored against baselines simulated on "
          "its own path; in the flat scenario the mismatching runs typically each carry a distinct path, i.e. "
          "the flat generator was not seed-reproducible for these runs):\n")
        mm = runs_df[runs_df.path_variant > 0].groupby(["model", "scenario"]).agg(
            n_mismatching_runs=("file", "size"), distinct_paths=("path_variant", "nunique")).reset_index()
        A(md_table(mm, floatfmt="{:.0f}"))
        A("")
        seeds = runs_df[runs_df.path_variant > 0].groupby("scenario")["seed"].unique().to_dict()
        A("  Seeds affected: " + "; ".join(f"{k}: {sorted(int(x) for x in v)}" for k, v in seeds.items()))
    A("")
    inv = runs_df.groupby(["source", "model"]).agg(
        n_runs=("file", "size"), flat=("scenario", lambda s: int((s == "flat").sum())),
        bull_trap=("scenario", lambda s: int((s == "bull_trap").sum())),
        crash=("scenario", lambda s: int((s == "crash").sum())),
        fallback_rows=("n_fallback", "sum"), runs_with_fallback=("n_fallback", lambda s: int((s > 0).sum())),
        zero_trade_runs=("zero_trade", "sum")).reset_index()
    A("Runs per model (and fallback / zero-trade counts):\n")
    A(md_table(inv, floatfmt="{:.0f}"))
    A("")
    if bad:
        A("Unreadable files:\n")
        for p, e in bad[:50]:
            A(f"- `{os.path.relpath(p, REPO)}`: {e}")
        A("")

    # ---- 2. coverage --------------------------------------------------------
    A("## 2. Resolvability coverage (fraction of steps with |log(P/V)| >= theta)\n")
    A("Computed on the reference price path of every cell (all seeds/discounts pooled, one path per cell).\n")
    A("Per scenario:\n")
    A(md_table(cov_scen))
    A("\nPer scenario x phase:\n")
    A(md_table(cov_tab))
    A("")

    # ---- 3. baseline envelope ----------------------------------------------
    A("## 3. Baseline envelope per scenario (means over cells)\n")
    A("RG_v1 = v1 rationality rule on all steps; RG_0.05 = same rule on resolvable steps only "
      "(theta = 0.05); return in percent of initial cash; point-MAS v1 / band-MAS v2 against the persona "
      "named in `mas_persona` (persona-agnostic policies are scored against each persona; the table "
      "shows the persona-specific rows for constant-mix and the mandate-conditional oracle and the "
      "ISFJ-scored row for the others, MAS excepted).\n")
    env_rows = []
    bl = bl_all[(bl_all.random_seed == -1)]
    for scen in SCENARIOS:
        s = bl[bl.scenario == scen]
        def _agg(sub, label):
            if len(sub) == 0:
                return
            env_rows.append(OrderedDict(
                scenario=scen, baseline=label, n_cells=sub.groupby(["seed", "discount", "path_variant"], dropna=False).ngroups,
                rg_v1=sub.rg_v1.mean(), rg_0_05=sub[f"rg_{TH05}"].mean(),
                rg_action_0_05=sub[f"rg_action_{TH05}"].mean(),
                return_pct=sub.return_pct.mean(), mdd_pct=sub.max_drawdown_pct.mean(),
                trade_count=sub.trade_count.mean()))
        for pol in ["always_hold", "buy_day1_hold", "random", "always_buy", "always_sell", "momentum", "mean_reversion"]:
            _agg(s[(s.policy == pol) & (s.mas_persona == "ISFJ")], pol)
        for th in THETAS:
            _agg(s[(s.policy == "v_oracle") & np.isclose(s.theta.astype(float), th) & (s.mas_persona == "ISFJ")],
                 f"v_oracle_theta{B.theta_key(th)}")
        for p in PERSONAS:
            _agg(s[(s.policy == "constant_mix_v1") & (s.persona == p)], f"constant_mix_v1_{p}")
            _agg(s[(s.policy == "constant_mix_v2") & (s.persona == p)], f"constant_mix_v2_{p}")
        for p in PERSONAS:
            for th in THETAS:
                _agg(s[(s.policy == "mandate_conditional_oracle") & (s.persona == p) & np.isclose(s.theta.astype(float), th)],
                     f"mandate_conditional_oracle_{p}_theta{B.theta_key(th)}")
    env = pd.DataFrame(env_rows)
    A(md_table(env, floatfmt="{:.2f}"))
    A("")
    # bull-trap replication
    A("### 3.1 Bull-trap replication of the Cycle-2 audit envelope\n")
    A("Cycle-2 audit reported bull-trap RG_v1 of 99.7 (buy-day-1-then-hold), 79.8 (always-hold), 66.9 (random).\n")
    bt = env[env.scenario == "bull_trap"].set_index("baseline")
    rep = pd.DataFrame([
        dict(baseline="buy_day1_hold", audit_rg_v1=99.7, rescore_rg_v1=bt.loc["buy_day1_hold", "rg_v1"]),
        dict(baseline="always_hold", audit_rg_v1=79.8, rescore_rg_v1=bt.loc["always_hold", "rg_v1"]),
        dict(baseline="random", audit_rg_v1=66.9, rescore_rg_v1=bt.loc["random", "rg_v1"]),
    ])
    rep["diff"] = rep.rescore_rg_v1 - rep.audit_rg_v1
    A(md_table(rep, floatfmt="{:.2f}"))
    A("")
    # per-seed bull trap detail
    bts = bl[(bl.scenario == "bull_trap") & (bl.mas_persona == "ISFJ") &
             bl.policy.isin(["buy_day1_hold", "always_hold", "random"])]
    piv = bts.pivot_table(index="seed", columns="policy", values="rg_v1", aggfunc="mean").reset_index()
    piv["seed"] = piv["seed"].astype(int)
    A("Per-seed bull-trap RG_v1 of the three audit baselines:\n")
    A(md_table(piv, floatfmt="{:.2f}"))
    A("")

    # ---- 4. agent means -----------------------------------------------------
    A("## 4. Agent means per persona x agent_type x scenario (pooled over all models and seeds)\n")
    A("`cov_0.05` = mean fraction of resolvable steps; `norm_rg_*` = (agent - floor) / (ceiling - floor) with floor = "
      "best of {always_hold, random, buy_day1_hold} and ceiling = mandate-conditional oracle (persona band, theta 0.05); "
      "`norm_*mas*` = (floor - agent) / (floor - ceiling) with ceiling = constant-mix at the persona target and "
      "floor = worst of {always_buy, always_sell, random} (1 = ceiling, 0 = floor, negatives = worse than floor). "
      f"`beats_*` = number of the {len(BEATS_SET)} baselines beaten (higher RG/return; lower MAS; smaller drawdown).\n")
    A("Normalisation is reported as NaN (and flagged in `norm_degenerate_*`) when the ceiling does not exceed the "
      f"floor by at least {NORM_MIN_GAP['rg']} RG point / {NORM_MIN_GAP['return']} return point / "
      f"{NORM_MIN_GAP['mas']} MAS. Under the v1 RG rule a HOLD while holding stock is always scored correct, so "
      "buy_day1_hold sits at RG_v1 ~ 100 and the RG floor is at or above the oracle ceiling in most cells. "
      "Share of runs with a degenerate RG / return / MAS normalisation, by scenario:\n")
    dg = runs_df.groupby("scenario").agg(
        n=("file", "size"), rg_v1=("norm_degenerate_rg_v1", "mean"),
        rg_0_05=(f"norm_degenerate_rg_{TH05}", "mean"), return_pct=("norm_degenerate_return_pct", "mean"),
        point_mas_v1=("norm_degenerate_point_mas_v1", "mean"),
        band_mas_v2=("norm_degenerate_band_mas_v2", "mean")).reset_index()
    A(md_table(dg, floatfmt="{:.3f}"))
    A("")
    g = runs_df.groupby(["persona", "agent_type", "scenario"], sort=True)
    agg = g.agg(n=("file", "size"),
                point_mas_v1=("point_mas_v1", "mean"), point_mas_v2=("point_mas_v2", "mean"),
                band_mas_v2=("band_mas_v2", "mean"), rel_mas=("rel_mas", "mean"),
                rg_v1=("rg_v1", "mean"), rg_0_05=(f"rg_{TH05}", "mean"), cov_0_05=(f"coverage_{TH05}", "mean"),
                rg_action_0_05=(f"rg_action_{TH05}", "mean"),
                norm_rg_v1=("norm_rg_v1", "mean"), norm_rg_0_05=(f"norm_rg_{TH05}", "mean"),
                norm_band_mas_v2=("norm_band_mas_v2", "mean"),
                beats_rg_v1=("beats_k_rg_v1", "mean"), beats_rg_0_05=(f"beats_k_rg_{TH05}", "mean"),
                beats_point_mas_v1=("beats_k_point_mas_v1", "mean"), beats_band_mas_v2=("beats_k_band_mas_v2", "mean"),
                return_pct=("return_pct", "mean"), zero_trade_share=("zero_trade", "mean")).reset_index()
    A(md_table(agg, floatfmt="{:.3f}"))
    A("")

    # ---- 5. RG by theta -----------------------------------------------------
    A("## 5. Pooled agent RG_v1 vs RG_theta by scenario (all personas, agent types, models)\n")
    rows = []
    for scen in SCENARIOS:
        s = runs_df[runs_df.scenario == scen]
        rec = OrderedDict(scenario=scen, n_runs=len(s), rg_v1=s.rg_v1.mean())
        for th in THETAS:
            k = B.theta_key(th)
            rec[f"rg_{k}"] = s[f"rg_{k}"].mean()
            rec[f"cov_{k}"] = s[f"coverage_{k}"].mean()
            rec[f"rg_action_{k}"] = s[f"rg_action_{k}"].mean()
            rec[f"runs_no_resolvable_{k}"] = int(s[f"rg_{k}"].isna().sum())
        rows.append(rec)
    A(md_table(pd.DataFrame(rows), floatfmt="{:.2f}"))
    A("")
    A("Same, by scenario x persona x agent_type (RG_v1, RG_0.03/0.05/0.08, normalised RG_0.05):\n")
    g2 = runs_df.groupby(["scenario", "persona", "agent_type"], sort=True).agg(
        rg_v1=("rg_v1", "mean"), **{f"rg_{B.theta_key(t)}": (f"rg_{B.theta_key(t)}", "mean") for t in THETAS},
        norm_rg_v1=("norm_rg_v1", "mean"), norm_rg_0_05=(f"norm_rg_{TH05}", "mean")).reset_index()
    A(md_table(g2, floatfmt="{:.2f}"))
    A("")

    # ---- 6. memory vs static sign counts -----------------------------------
    A("## 6. Static vs memory: sign counts of the per-model MAS change\n")
    A("For every model x persona, delta = mean MAS(memory) - mean MAS(static), pooled over scenarios and seeds "
      "(only runs with both agent types in the same model x persona x scenario x seed x discount cell are paired). "
      "'improve' = delta < 0 (memory closer to mandate). Counts are out of the number of models with paired runs.\n")
    pair_keys = ["model", "persona", "scenario", "seed", "discount"]
    st = runs_df[runs_df.agent_type == "static"]
    me = runs_df[runs_df.agent_type == "memory"]
    mets = ["point_mas_v1", "point_mas_v2", "band_mas_v2", "rel_mas", "rg_v1", f"rg_{TH05}"]
    paired = st.merge(me, on=pair_keys, suffixes=("_static", "_memory"))
    A(f"Paired static/memory runs: {len(paired)}.\n")
    sign_rows = []
    for scen in ["all"] + list(SCENARIOS):
        pp = paired if scen == "all" else paired[paired.scenario == scen]
        for persona in PERSONAS:
            q = pp[pp.persona == persona]
            rec = OrderedDict(scope=scen, persona=persona, n_models=q.model.nunique())
            for met in mets:
                d = q.groupby("model").apply(lambda z: z[f"{met}_memory"].mean() - z[f"{met}_static"].mean(),
                                             include_groups=False)
                if met.startswith("rg"):
                    rec[f"{met}_models_up"] = int((d > 0).sum())
                else:
                    rec[f"{met}_models_improve"] = int((d < 0).sum())
                rec[f"{met}_mean_delta"] = float(d.mean()) if len(d) else np.nan
            sign_rows.append(rec)
    sign = pd.DataFrame(sign_rows)
    A(md_table(sign, floatfmt="{:.4f}"))
    A("")
    A("Per-model deltas (memory - static, pooled over scenarios), ISFJ and ENTJ, point-MAS v1 vs band-MAS v2:\n")
    pm_rows = []
    for model in sorted(paired.model.unique()):
        rec = OrderedDict(model=model)
        for persona in ("ISFJ", "ENTJ"):
            q = paired[(paired.model == model) & (paired.persona == persona)]
            for met in ("point_mas_v1", "band_mas_v2"):
                rec[f"{persona}_{met}"] = float(q[f"{met}_memory"].mean() - q[f"{met}_static"].mean()) if len(q) else np.nan
        pm_rows.append(rec)
    A(md_table(pd.DataFrame(pm_rows), floatfmt="{:+.4f}"))
    A("")

    # ---- 7. zero trades -----------------------------------------------------
    A("## 7. Share of runs with zero trades (Action never BUY/SELL on a non-fallback row)\n")
    zt = runs_df.groupby(["persona", "agent_type", "scenario"]).agg(
        n=("file", "size"), zero_trade_share=("zero_trade", "mean"),
        mean_trade_count=("trade_count", "mean"), mean_turnover=("turnover", "mean"),
        mean_cash_share=("mean_cash_share", "mean")).reset_index()
    A(md_table(zt, floatfmt="{:.3f}"))
    A("")
    ztm = runs_df.groupby(["model"]).agg(n=("file", "size"), zero_trade_share=("zero_trade", "mean"),
                                         zero_trade_runs=("zero_trade", "sum")).reset_index()
    A("By model:\n")
    A(md_table(ztm, floatfmt="{:.3f}"))
    A("")
    A(f"Overall: {int(runs_df.zero_trade.sum())} of {len(runs_df)} runs "
      f"({runs_df.zero_trade.mean() * 100:.1f} percent) have zero trades.\n")

    # ---- 8. notes -----------------------------------------------------------
    A("## 8. Definitions and notes\n")
    A("- C_t = Cash / Portfolio_Value (end of day, post-trade); x_t = log(Price / Fundamental_Value).")
    A("- point-MAS v1: mean |C_t - target_v1| with targets ISFJ 1.0, INTJ 0.5, ENTJ 0.2. "
      "point-MAS v2: mean |C_t - centre| with centres ISFJ 0.80, INTJ 0.50, ENTJ 0.10. "
      "band-MAS v2: mean max(0, |C_t - centre| - 0.10). rel-MAS: mean |C_t - C_0| with C_0 = 1.0 "
      "(identically 1 - mean C_t under the v1 start; reported for completeness, not normalised).")
    A("- RG_v1: the v1 rule from experiments/run_experiments.py (BUY correct iff P<V; SELL correct iff P>V; "
      "HOLD correct iff P>V, or P<=V and holdings value > $1), mean over scored non-fallback rows x 100. "
      "RG_theta: same rule restricted to steps with |x_t| >= theta (coverage = fraction of all steps resolvable). "
      "RG_action_theta: BUY/SELL rows only on resolvable steps (coverage_action = scored rows / all rows).")
    A("- Trade count uses the Action label (as in v1); `effective_trade_count` counts days where Holdings_Qty actually "
      "changed; turnover = sum |dQty_t| x P_t / 10,000.")
    A("- Baselines: always_hold, always_buy (BUY q=1 daily), always_sell (SELL q=1 daily, degenerate at 100 percent cash), "
      "random (10 internal seeds, action uniform over BUY/SELL/HOLD, q ~ U(0,1); mean over seeds), buy_day1_hold, "
      "constant_mix at each v1 target and v2 centre (daily rebalance to the target cash share), momentum (SMA20 > SMA60 -> "
      "fully invested else all cash), mean_reversion (RSI14 < 30 -> fully invested, > 70 -> all cash, else no trade), "
      "v_oracle (target cash 0 if x < -theta, 1 if x > +theta, else no trade), mandate_conditional_oracle (v_oracle target "
      "clipped into the persona's v2 band, else no trade). Target-share policies get derived action labels for RG "
      "(BUY/SELL if the equity share moved by more than 1 point, else HOLD); v1-interface policies use the action taken.")
    A("- The always_hold, always_sell, v_oracle-when-never-undervalued and similar policies sit at 100 percent cash and thus "
      "score point-MAS v1 = 0 for ISFJ; the v1 ISFJ target coincides with the start allocation, which is why "
      "relative MAS and ISFJ point-MAS v1 are the same quantity in v1 data.")
    A(f"\nRuntime: {time.time() - t0:.0f} s.")
    with open(os.path.join(OUT_DIR, "E0_RESCORE_V1.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
