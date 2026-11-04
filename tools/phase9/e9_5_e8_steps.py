"""v2.1 Phase 9, stage 2, E8 -- the per-step reading of the cadence arms, computed where the run CSVs are.

    python -u -m tools.phase9.e9_5_e8_steps --results results_v2/phase9 --headline-results <stage-1 tree>/results_v2/phase9

Per cadence run: the band distance of the cash share on injected days, on non-injected days and on the day after an
injection; per headline static and memory run on the same seeds: the band distance over every day.  Aggregated per
(model, persona, scenario cell, arm) into `stats_e8_cadence/steps_summary.csv`, with the static arm's distance joined
onto every cadence row, which is what `e9_5_e8_analyse.predictions` reads for P4: on a non-injected day a stateless
agent sees the static arm's prompt, so where the cadence arm's non-injected days sit between the static arm and its own
injected days is the carry-over through the portfolio state, day by day.

The band distance of a day is max(Band_Lo - Cash_Share, Cash_Share - Band_Hi, 0): zero inside the band, the shortfall
outside it, the day-level quantity band-MAS averages.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from typing import List, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E94 = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4")
OUT = os.path.join(E94, "stats_e8_cadence")
CADENCE_SUBDIR, CADENCE_SETTING = "stage2_cadence", "cadence"
HEADLINE_SUBDIR, HEADLINE_SETTING = "stage1_open", "default"
SEEDS = frozenset(range(10001, 10061))


def _dir_slug(model: str) -> str:
    return model.split("|")[0].replace("/", "_")


def run_files(results: str, subdir: str, setting: str, model: str) -> List[str]:
    pat = os.path.join(results, subdir, setting, "*", _dir_slug(model), "*", "seed*", "*.csv")
    return sorted(f for f in glob.glob(pat) if ".contaminated." not in os.path.basename(f) and ".failed." not in os.path.basename(f))


def band_distance(df: pd.DataFrame) -> np.ndarray:
    c = pd.to_numeric(df["Cash_Share"], errors="coerce").values
    lo = pd.to_numeric(df["Band_Lo"], errors="coerce").values
    hi = pd.to_numeric(df["Band_Hi"], errors="coerce").values
    return np.maximum.reduce([lo - c, c - hi, np.zeros_like(c)])


def scenario_cell_of(df: pd.DataFrame) -> str:
    from tools.stats_v2 import scenario_cell
    return str(np.asarray(scenario_cell(df.iloc[:1]))[0])


def summarise_run(df: pd.DataFrame) -> dict:
    """One run's day-level reading.  A cadence run carries `Mandate_Injected`; a headline run does not."""
    dist = band_distance(df)
    out = {"n_days": int(len(df)), "dist_all": float(np.nanmean(dist)) if len(dist) else float("nan")}
    if "Mandate_Injected" in df.columns:
        inj = df["Mandate_Injected"].astype(str).str.lower().isin(("true", "1")).values
        after = np.zeros_like(inj)
        after[1:] = inj[:-1]
        after = after & ~inj                        # the day after an injection, when it is not itself injected
        out.update({"n_injected": int(inj.sum()),
                    "dist_injected": float(np.nanmean(dist[inj])) if inj.any() else float("nan"),
                    "dist_non_injected": float(np.nanmean(dist[~inj])) if (~inj).any() else float("nan"),
                    "dist_after_injection": float(np.nanmean(dist[after])) if after.any() else float("nan")})
    return out


def collect(results: str, headline_results: str, models: List[str]) -> pd.DataFrame:
    rows = []
    for model in models:
        for subdir, setting, root in ((CADENCE_SUBDIR, CADENCE_SETTING, results), (HEADLINE_SUBDIR, HEADLINE_SETTING, headline_results)):
            if not root:
                continue
            for f in run_files(root, subdir, setting, model):
                df = pd.read_csv(f)
                if df.empty or int(df["Seed"].iloc[0]) not in SEEDS:
                    continue
                arm = str(df["Arm"].iloc[0])
                if subdir == HEADLINE_SUBDIR and arm not in ("static", "memory"):
                    continue
                rows.append({"Model": model, "Persona": str(df["Persona"].iloc[0]), "Scenario_Cell": scenario_cell_of(df),
                             "arm": arm, "Seed": int(df["Seed"].iloc[0]), **summarise_run(df)})
    return pd.DataFrame(rows)


def aggregate(runs: pd.DataFrame) -> pd.DataFrame:
    """Per (model, persona, cell, arm): the means over runs, the static and memory arms' overall distance joined onto
    every row as `dist_static` and `dist_memory`."""
    if runs.empty:
        return pd.DataFrame(columns=["Model", "Persona", "Scenario_Cell", "arm", "k", "n_runs", "dist_injected",
                                     "dist_non_injected", "dist_after_injection", "dist_all", "dist_static", "dist_memory"])
    from experiments.arms_v2 import CADENCE_LEVELS
    k_of = {a: k for k, a in CADENCE_LEVELS.items()}
    cols = [c for c in ("dist_injected", "dist_non_injected", "dist_after_injection", "dist_all", "n_injected") if c in runs.columns]
    agg = runs.groupby(["Model", "Persona", "Scenario_Cell", "arm"]).agg(n_runs=("Seed", "size"), **{c: (c, "mean") for c in cols}).reset_index()
    agg["k"] = agg["arm"].map(k_of)
    ref = agg[agg["arm"].isin(("static", "memory"))].pivot_table(index=["Model", "Persona", "Scenario_Cell"], columns="arm",
                                                                 values="dist_all").reset_index()
    ref = ref.rename(columns={"static": "dist_static", "memory": "dist_memory"})
    for c in ("dist_static", "dist_memory"):
        if c not in ref.columns:
            ref[c] = np.nan
    return agg.merge(ref[["Model", "Persona", "Scenario_Cell", "dist_static", "dist_memory"]], on=["Model", "Persona", "Scenario_Cell"], how="left")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(ROOT, "results_v2", "phase9"), help="the tree holding stage2_cadence/")
    ap.add_argument("--headline-results", default="", help="the tree holding stage1_open/ (the stage-1 record); "
                                                            "defaults to --results")
    ap.add_argument("--manifest", default=os.path.join(E94, "manifest_cadence_open.json"))
    a = ap.parse_args(argv)
    m = json.load(open(a.manifest, encoding="utf-8"))
    runs = collect(a.results, a.headline_results or a.results, list(m["configs"]))
    agg = aggregate(runs)
    os.makedirs(OUT, exist_ok=True)
    runs.to_csv(os.path.join(OUT, "steps_runs.csv"), index=False, lineterminator="\n")
    agg.to_csv(os.path.join(OUT, "steps_summary.csv"), index=False, lineterminator="\n")
    json.dump({"n_runs": int(len(runs)), "n_rows": int(len(agg)), "by_arm": runs["arm"].value_counts().to_dict() if len(runs) else {},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "steps_meta.json"), "w", encoding="utf-8"), indent=1)
    print(f"{len(runs)} runs read; {len(agg)} (model, persona, cell, arm) rows written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
