"""E7's per-STEP reads (`PREREG_PHASE_9_STAGE2_E7.md` 3): the salience shares on each vocabulary frame, the day-1 gate's
persona side on each pair, and the static arm's mean cash share -- computed where the run CSVs are.

    python -u -m tools.phase9.e9_5_e7_salience --results results_v2/phase9 [--models key,key] [--n_boot 200] [--n_jobs 4]

Why a script of its own.  `per_run.csv` is one row per run; the shares, the gate and the cash-share precondition read
every day of every run.  Stage 2's runs live on the cluster and in the archived tarballs (STAGE2_OPERATIONS.md 8), so
this runs there -- or on a machine the archives of BOTH `stage2_ocean` and `stage2_slice` have been unpacked on -- and
writes `salience_summary.json` into `stats_e7_ocean/`, which `e9_5_e7_analyse.py` reads for P1 and P5.

The frames, per model, every run at common start:

*   **ocean** -- O1_conservative and O2_aggressive under static, memory and swapped, plus E3's NONE trader.
*   **mbti_pair** -- ISFJ and ENTJ under the same three arms, plus the same NONE trader (E3's rows; INTJ has no OCEAN
    counterpart and is left out, so the two frames have the same shape).
*   **pooled** -- both pairs and NONE, with `Mandate_Persona` relabelled by risk category: after E7's counterpart map
    the conservative mandate is one text whichever vocabulary carries it, and labelling it twice (mandate:ISFJ and
    mandate:O1_conservative) puts a persona-to-directive canonical correlation of 0.82 into the design against 0.37
    relabelled (measured on the synthetic frame in tests/test_v2_1_e7.py).  Secondary; the two per-vocabulary frames
    are the registered read because each is identified on its own.

Each frame goes through `identification_check` first and `salience_by_window(identification="v2_1")` only if it is
identified, with the seed-cluster bootstrap at `--n_boot` refits per window and the P8-18 fold fix.  Parse-fallback
rows are dropped as `tools/report_v2.salience_tables` drops them, and the share dropped is recorded.

The day-1 gate is `evaluation/salience.separability_gate` on the pair's day-1 cash share -- the two persona labels
only, every persona arm, as `tools/report_v2.gate_tables` populates its persona side -- with the static-arm-only AUC
beside.  Its null needs two no-persona labels (P8-14) and this design has one, so it is NOT COMPUTABLE and is written
as such.  No pass or fail of the gate is claimed.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E94 = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4")
OUT = os.path.join(E94, "stats_e7_ocean")
RESULTS = os.path.join(ROOT, "results_v2", "phase9")

OCEAN_SUBDIR, SLICE_SUBDIR, SETTING = "stage2_ocean", "stage2_slice", "common_start"
ARMS = ("static", "memory", "swapped")
PAIRS = {"ocean": ("O1_conservative", "O2_aggressive"), "mbti_pair": ("ISFJ", "ENTJ")}
CATEGORY = {"O1_conservative": "conservative", "ISFJ": "conservative", "O2_aggressive": "aggressive", "ENTJ": "aggressive"}
EXPECTED_RUNS = {"ocean": 2 * 3 * 4 * 60, "mbti_pair": 2 * 3 * 4 * 60, "trader": 4 * 60}
USECOLS = ("Model", "Persona", "Arm", "Scenario", "Seed", "Crash_Discount", "Decode_Replicate", "Day", "Start_Design",
           "Start_Cash_Share", "Mandate_Block", "Mandate_Persona", "Cash_Share", "Target_Cash_Share", "Parse_Status")


def _slug(model: str) -> str:
    return model.replace("/", "_").replace("|", "_").replace(".", "_")


def _dir_slug(model: str) -> str:
    """The run directory's model component: `RunConfig.model_name.replace('/', '_')` (the configuration's model, without
    its tag)."""
    return model.split("|")[0].replace("/", "_")


def run_files(results: str, subdir: str, model: str) -> List[str]:
    pat = os.path.join(results, subdir, SETTING, "*", _dir_slug(model), "*", "seed*", "*.csv")
    return sorted(f for f in glob.glob(pat) if ".contaminated." not in os.path.basename(f))


def load_runs(files: List[str], personas) -> pd.DataFrame:
    from evaluation.salience import MARKET_FEATURES
    cols = set(USECOLS) | set(MARKET_FEATURES)
    parts = []
    for f in files:
        head = pd.read_csv(f, nrows=1)
        if head.empty or str(head["Persona"].iloc[0]) not in personas:
            continue
        parts.append(pd.read_csv(f, usecols=lambda c: c in cols))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def n_runs(d: pd.DataFrame) -> int:
    if d.empty:
        return 0
    keys = [k for k in ("Persona", "Arm", "Scenario", "Crash_Discount", "Seed", "Decode_Replicate") if k in d.columns]
    return int(d.drop_duplicates(subset=keys).shape[0])


def frames_for(model: str, ocean: pd.DataFrame, mbti: pd.DataFrame, trader: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    o = pd.concat([ocean, trader], ignore_index=True)
    m = pd.concat([mbti, trader], ignore_index=True)
    pooled = pd.concat([ocean, mbti, trader], ignore_index=True)
    pooled["Mandate_Persona"] = pooled["Mandate_Persona"].map(lambda p: CATEGORY.get(p, p))
    out = {"ocean": o, "mbti_pair": m, "pooled": pooled}
    for k in out:
        out[k]["Model"] = model
    return out


def drop_fallbacks(d: pd.DataFrame):
    if "Parse_Status" not in d.columns:
        return d, 0.0
    fb = d["Parse_Status"].astype(str) == "fallback"
    return d[~fb].reset_index(drop=True), float(fb.mean())


def gate(d: pd.DataFrame, pair) -> dict:
    """The day-1 gate's persona side on one pair: every persona arm, as report_v2.gate_tables populates it, with the
    static arm alone beside.  The null is NOT COMPUTABLE with one no-persona label (P8-14)."""
    from evaluation.salience import separability_gate
    day1 = d[(d["Day"] == 1) & d["Persona"].isin(pair)].rename(columns={"Cash_Share": "C1"})
    out = {"persona_arms": separability_gate(day1, order=pair) if len(day1) else {"n": 0},
           "static_arm_only": separability_gate(day1[day1["Arm"] == "static"], order=pair) if len(day1) else {"n": 0},
           "null": "NOT COMPUTABLE: one no-persona label (NONE); P8-14"}
    out["auc"] = out["persona_arms"].get("auc")
    return out


def mean_cash_share(d: pd.DataFrame) -> pd.DataFrame:
    """Per persona x scenario cell x arm: the mean over runs of each run's mean cash share (the precondition)."""
    from tools.stats_v2 import scenario_cell
    x = d.copy()
    x["Scenario_Cell"] = scenario_cell(x)
    per_run = x.groupby(["Persona", "Scenario_Cell", "Arm", "Seed", "Decode_Replicate"])["Cash_Share"].mean().reset_index()
    return per_run.groupby(["Persona", "Scenario_Cell", "Arm"])["Cash_Share"].agg(["mean", "std", "size"]).reset_index()


def _jsonable(x):
    return json.loads(json.dumps(x, default=lambda v: float(v) if isinstance(v, (np.floating, np.integer)) else str(v)))


def analyse_model(model: str, results: str, n_boot: int, n_jobs: int, out_dir: str) -> dict:
    from evaluation.salience import identification_check, salience_by_window
    ocean = load_runs(run_files(results, OCEAN_SUBDIR, model), PAIRS["ocean"])
    slice_files = run_files(results, SLICE_SUBDIR, model)
    mbti = load_runs(slice_files, PAIRS["mbti_pair"])
    trader = load_runs(slice_files, ("NONE",))
    counts = {"ocean": n_runs(ocean), "mbti_pair": n_runs(mbti), "trader": n_runs(trader)}
    rec = {"runs": counts, "expected": EXPECTED_RUNS}
    short = [k for k, v in counts.items() if v != EXPECTED_RUNS[k]]
    if short:
        rec["skipped"] = f"incomplete: {short} ({counts} against {EXPECTED_RUNS}); verify the stage first"
        print(f"  SKIPPED: {rec['skipped']}")
        return rec
    fr = frames_for(model, ocean, mbti, trader)
    rec["frames"] = {}
    for name, d in fr.items():
        d, dropped = drop_fallbacks(d)
        chk = identification_check(d)
        r = {"identified": bool(chk["identified"]), "failing_clauses": chk["failing_clauses"],
             "identified_as_registered": bool(chk["identified_as_registered"]), "ranks": chk["ranks"],
             "max_canonical_corr": chk["max_canonical_corr"], "n_runs": chk["n_runs"], "fallback_rows_dropped": dropped,
             "windows": []}
        json.dump(_jsonable(chk), open(os.path.join(out_dir, f"{_slug(model)}_identification_{name}.json"), "w",
                                       encoding="utf-8"), indent=1)
        print(f"  {name}: identified={r['identified']} ranks={chk['ranks']} dropped={dropped:.4%}")
        if r["identified"]:
            sw = salience_by_window(d, identification="v2_1", n_boot=n_boot, n_jobs=n_jobs)
            sw.to_csv(os.path.join(out_dir, f"{_slug(model)}_salience_{name}.csv"), index=False)
            r["windows"] = [{k: (None if pd.isna(v) else float(v)) for k, v in row.items()
                             if k in ("window_start", "window_end", "r2", "S_persona", "S_directive", "S_market",
                                      "S_persona_lo", "S_persona_hi", "S_directive_lo", "S_directive_hi",
                                      "S_persona_null_mean", "n")} for _, row in sw.iterrows()]
            for w in r["windows"]:
                print(f"    window {int(w['window_start'])}-{int(w['window_end'])}: R2={w['r2']} "
                      f"S_persona={w['S_persona']} [{w.get('S_persona_lo')}, {w.get('S_persona_hi')}] "
                      f"S_directive={w['S_directive']} null={w.get('S_persona_null_mean')}")
        rec["frames"][name] = r
    rec["ocean"], rec["mbti_pair"], rec["pooled"] = rec["frames"]["ocean"], rec["frames"]["mbti_pair"], rec["frames"]["pooled"]
    rec["gate"] = {name: _jsonable(gate(fr[name], PAIRS[name])) for name in PAIRS}
    rows = []
    for name in PAIRS:
        g = rec["gate"][name]
        rows.append({"frame": name, "population": "persona arms", **{k: v for k, v in g["persona_arms"].items()}})
        rows.append({"frame": name, "population": "static arm only", **{k: v for k, v in g["static_arm_only"].items()}})
    pd.DataFrame(rows).to_csv(os.path.join(out_dir, f"{_slug(model)}_gate.csv"), index=False)
    for name in PAIRS:
        print(f"  gate {name}: AUC={rec['gate'][name]['auc']} (persona arms), "
              f"{rec['gate'][name]['static_arm_only'].get('auc')} (static only); null NOT COMPUTABLE")
    mcs = mean_cash_share(pd.concat([ocean, mbti, trader], ignore_index=True))
    mcs.to_csv(os.path.join(out_dir, f"{_slug(model)}_mean_cash_share.csv"), index=False)
    rec["static_mean_cash_share"] = {f"{r.Persona}|{r.Scenario_Cell}": float(r["mean"])
                                     for _, r in mcs[mcs["Arm"] == "static"].iterrows()}
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", default=RESULTS, help="the results root holding stage2_ocean/ and stage2_slice/")
    ap.add_argument("--models", default="", help="comma list of configuration keys; default e9_roster.CAUSAL_OPEN")
    ap.add_argument("--n_boot", type=int, default=200, help="seed-cluster bootstrap refits per window (registered: 200)")
    ap.add_argument("--n_jobs", type=int, default=1)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    from tools.phase9 import e9_roster as RO
    models = [m for m in a.models.split(",") if m] or list(RO.CAUSAL_OPEN)
    os.makedirs(a.out, exist_ok=True)
    doc = {"models": {}, "n_boot": a.n_boot, "results_root": os.path.abspath(a.results),
           "frames": "ocean = O1/O2 x {static, memory, swapped} + NONE trader; mbti_pair = ISFJ/ENTJ likewise; pooled = "
                     "both with Mandate_Persona by category",
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for model in models:
        print(f"\n=== {model} ===", flush=True)
        doc["models"][model] = analyse_model(model, a.results, a.n_boot, a.n_jobs, a.out)
        json.dump(doc, open(os.path.join(a.out, "salience_summary.json"), "w", encoding="utf-8"), indent=1)
    print(f"\nwritten -> {os.path.join(a.out, 'salience_summary.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
