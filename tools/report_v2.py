"""
Evaluation report for v2 runs (plan Section 8; E4): per-run metrics, per-cell
baselines and normalisation, 'beats k of n', reliability accounting, stratified
bull-trap reporting (topped / un-topped), the target-free salience measure with
its permutation null, and the t = 0 gate (common-start design only).

Usage: python -m tools.report_v2 --results results_v2 --out docs/env_v2/generated/report_v2
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Dict, List

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from envs.synthetic_market import SyntheticMarketEnv  # noqa: E402
from evaluation.metrics_v2 import score_run, floors_and_ceilings, beats_k_of_n, normalise, HIGHER_BETTER, multi_asset_regrets  # noqa: E402
from evaluation.baselines_v2 import baseline_metrics  # noqa: E402
from evaluation.salience import salience_by_window, separability_gate  # noqa: E402


def load_runs(results_dir: str) -> List[pd.DataFrame]:
    files = sorted(glob.glob(os.path.join(results_dir, "**", "*.csv"), recursive=True))
    out = []
    for f in files:
        try:
            df = pd.read_csv(f)
        except Exception:
            continue
        if "Cash_Share" in df.columns and "Persona" in df.columns:
            df["__file"] = f
            out.append(df)
    return out


def _cell_key(df: pd.DataFrame) -> tuple:
    r = df.iloc[0]
    return (r["Scenario"], int(r["Seed"]), float(r["Crash_Discount"]), str(r.get("Ordering", "setup_first")),
            str(r["Persona"]), float(r["Start_Cash_Share"]), float(r["Cost_bp"]))


_BASE_CACHE: Dict[tuple, Dict] = {}


def cell_baselines(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    key = _cell_key(df)
    if key not in _BASE_CACHE:
        r = df.iloc[0]
        env = SyntheticMarketEnv(r["Scenario"], int(df["Day"].max()), int(r["Seed"]), crash_discount=float(r["Crash_Discount"]),
                                 ordering=str(r.get("Ordering", "setup_first")))
        _BASE_CACHE[key] = baseline_metrics(env, str(r["Persona"]), float(r["Start_Cash_Share"]), cost_bp=float(r["Cost_bp"]))
    return _BASE_CACHE[key]


def build_tables(runs: List[pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    rows = []
    for df in runs:
        r0 = df.iloc[0]
        persona = str(r0["Persona"])
        m = score_run(df, persona if persona != "NONE" else "TRADER", float(r0["Start_Cash_Share"]))
        if any(c.startswith("x_asset") for c in df.columns):
            m.update(multi_asset_regrets(df, persona if persona != "NONE" else "TRADER"))
        bm = cell_baselines(df)
        fc = floors_and_ceilings(bm, persona)
        bk = beats_k_of_n(m, bm)
        row = {"Model": r0["Model"], "Persona": persona, "Arm": r0["Arm"], "Scenario": r0["Scenario"], "Seed": r0["Seed"],
               "Crash_Discount": r0["Crash_Discount"], "Ordering": r0.get("Ordering", "setup_first"),
               "Decode_Replicate": r0.get("Decode_Replicate", 0), "Track": r0.get("Track", "B"),
               "Start_Design": r0.get("Start_Design", ""), "Start_Cash_Share": r0["Start_Cash_Share"],
               "Action_Interface": r0.get("Action_Interface", ""), "Cost_bp": r0["Cost_bp"], "Cost_Visible": r0.get("Cost_Visible", False),
               "Topped": r0.get("Event_Topped", None), "Env_Attempts": r0.get("Env_Attempts", 1), **m}
        for met in HIGHER_BETTER:
            row[f"norm_{met}"] = normalise(m.get(met, np.nan), fc[met]["floor"], fc[met]["ceiling"])
            row[f"degenerate_{met}"] = fc[met]["degenerate"]
            row[f"beats_{met}"] = bk[met]
            row[f"floor_{met}"] = fc[met]["floor"]; row[f"ceiling_{met}"] = fc[met]["ceiling"]
        rows.append(row)
    per_run = pd.DataFrame(rows)
    if per_run.empty:
        return {"per_run": per_run}
    n_base = len(cell_baselines(runs[0]))
    group = ["Model", "Persona", "Arm", "Scenario"]
    agg_cols = ["point_mas_v1", "point_mas_v2", "band_mas", "relative_mas", "rg_v1", "rg_theta_0.05", "coverage_0.05",
                "mcr_0.05", "norm_mcr_0.05", "norm_band_mas", "return_pct", "mdd_pct", "trade_count", "turnover",
                "zero_trade", "fallback_share", "beats_mcr_0.05", "beats_band_mas"]
    summary = per_run.groupby(group)[[c for c in agg_cols if c in per_run]].mean(numeric_only=True).reset_index()
    summary["n_runs"] = per_run.groupby(group).size().values
    summary["n_baselines"] = n_base
    strat = per_run[per_run["Scenario"] == "bull_trap"].groupby(group + ["Topped"])[["mcr_0.05", "band_mas", "rg_theta_0.05", "return_pct"]].mean().reset_index()
    reliability = per_run.groupby(["Model", "Arm"]).agg(n_runs=("fallback_share", "size"), fallback_share=("fallback_share", "mean"),
                                                         zero_trade_share=("zero_trade", "mean"), attempts_mean=("Env_Attempts", "mean")).reset_index()
    return {"per_run": per_run, "summary": summary, "bull_trap_strata": strat, "reliability": reliability}


def salience_tables(runs: List[pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    allr = pd.concat(runs, ignore_index=True)
    allr = allr[allr["Parse_Status"].astype(str) != "fallback"]
    out = {}
    if allr["Persona"].nunique() >= 2 and allr["Seed"].nunique() >= 2:
        out["salience_primary"] = salience_by_window(allr, include_state=False)
        out["salience_with_state"] = salience_by_window(allr, include_state=True, null_reps=0)
    # The t = 0 separability gate is pre-registered on the COMMON-START design (C_1 levels, PREREGISTRATION.md 4).
    # Under start-at-target every persona starts at its own centre, so C_1 - C_0 ~ 0 for a persona-consistent agent and a
    # gate that tests level ordering and band membership cannot pass (weakness item 54). v2.1 Phase 0: the gate is
    # computed on common-start cells only; the delta-C_1 table is kept as EXPLORATORY with the reason; Phase 7 (E7.5)
    # re-specifies it.
    common = allr[(allr["Start_Design"] == "common") & (allr["Day"] == 1)]
    if len(common):
        g = common.rename(columns={"Cash_Share": "C1"})
        out["gate_common_start"] = pd.DataFrame([{"Model": m, **separability_gate(dm)} for m, dm in g.groupby("Model")])
    tgt = allr[(allr["Start_Design"] == "target") & (allr["Day"] == 1)].copy()
    if len(tgt):
        tgt["C1"] = tgt["Cash_Share"] - tgt["Start_Cash_Share"]   # delta C_1 under start-at-target
        ex = pd.DataFrame([{"Model": m, **separability_gate(dm)} for m, dm in tgt.groupby("Model")])
        ex["note"] = ("EXPLORATORY, not a gate: delta C_1 fed to a level/band-membership test is ill-posed under "
                      "start-at-target (item 54); re-specified in Phase 7")
        out["exploratory_deltaC1_start_at_target"] = ex
    return out


def write_report(tables: Dict[str, pd.DataFrame], out_prefix: str):
    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    for name, df in tables.items():
        df.to_csv(f"{out_prefix}_{name}.csv", index=False)
    L = ["# v2 evaluation report", ""]
    if "summary" in tables:
        s = tables["summary"]
        L += ["## Per-cell means (model x persona x arm x scenario)", "",
              "Primary RG-type metric is the mandate-conditional regret MCR (mean |C_t - c*_t| over resolvable steps; "
              "lower is better). norm_mcr_0.05 is normalised against constant-mix (ceiling; 1.0 = as good as the "
              "constant-mix policy) and the worst of {always-buy, always-sell, random} (floor), the convention of "
              "evaluation/metrics_v2.py::floors_and_ceilings for every lower-is-better metric; the mandate-oracle "
              "convention is decided in Phase 7 (v2.1). RG_v1 is shown for comparability; its normalisation is "
              "degenerate whenever buy-and-hold scores ~100 (flagged per run).", "",
              s.round(3).to_string(index=False), ""]
    if "reliability" in tables:
        L += ["## Reliability", "", tables["reliability"].round(3).to_string(index=False), ""]
    if "bull_trap_strata" in tables:
        L += ["## Bull-trap strata (topped / un-topped)", "", tables["bull_trap_strata"].round(3).to_string(index=False), ""]
    for k in ("salience_primary", "salience_with_state", "gate_common_start", "exploratory_deltaC1_start_at_target"):
        if k in tables:
            L += [f"## {k}", "", tables[k].round(3).to_string(index=False), ""]
    with open(out_prefix + ".md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results_v2")
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "env_v2", "generated", "report_v2"))
    a = ap.parse_args()
    runs = load_runs(a.results)
    print(f"{len(runs)} runs loaded")
    tables = build_tables(runs)
    if runs:
        tables.update(salience_tables(runs))
    write_report(tables, a.out)
    print("written", a.out + ".md")
