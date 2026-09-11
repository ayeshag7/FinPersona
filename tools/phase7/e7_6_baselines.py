"""
v2.1 Phase 7 -- E7.6: the baselines on the run's own path, and the reproducibility test that has to come first
(PREREG_PHASE_7.md 7; weakness 56).

    python -u -m tools.phase7.e7_6_baselines --stages repro,baselines --results results_v2_pilot

`repro`  For every pilot run, rebuild the environment from its own `meta.json` -- the scalar arguments in
         `env_metadata` plus the full `env_metadata.gen_config` -- and compare the regenerated path against the
         columns the run actually logged (`Price`, `Fundamental_Value`, `x`).  This is the test of whether a v2
         path regenerates under the v2.1 switches at all.  It runs BEFORE any pilot number moves: if a cell does
         not reproduce, its baselines may not be rebuilt on a path the agent never saw, and the report says so.

         Also recomputes `Gen_Config_Hash` from the stored metadata and compares it with the stored value, which
         tests the provenance function against its own record rather than the path.

`baselines`  Rebuild `report_v2.cell_baselines` from `meta.json` (`from_meta=True`) instead of from the seven run-CSV
         columns, and report where the two agree -- for the cells that reproduced.

Output: <out>/repro.{csv,md,json}, <out>/baselines_compare.{csv,md}
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from tools.phase5.common import GEN, pin_state  # noqa: E402

OUT = os.path.join(GEN, "e7_6")
# The columns of the regenerated path that the run also logs, so the comparison is on the agent's own numbers.
COMPARE = (("price", "Price"), ("fundamental_value", "Fundamental_Value"), ("x", "x"))
TOL = 1e-9


def env_from_meta(meta: dict, engine_override: str = None):
    """Rebuild the environment from a run's `meta.json`, using every field the metadata carries.

    `env_metadata.gen_config` is the generator's full configuration AS IT WAS AT RUN TIME.  The pilot's 27 keys are
    restored; the 23 GenConfig fields v2.1 added afterwards are NOT in the record and therefore take today's
    defaults.  That is precisely what the test measures -- whether a path recorded under v2 comes back under the
    v2.1 switches -- and the result is reported, not worked around by guessing values the record does not hold.
    """
    from envs.synthetic_market import SyntheticMarketEnv
    em = meta["env_metadata"]
    gc = dict(em.get("gen_config") or {})
    kw = dict(scenario=em["scenario"], n_days=int(em["n_days"]), seed=int(em["seed"]),
              start_price=float(em.get("start_price", 100.0)),
              crash_discount=float(em.get("crash_discount", 0.70)),
              ordering=str(em.get("ordering", "setup_first")),
              n_assets=int(em.get("n_assets", 1)),
              engine=str(engine_override or em.get("engine", "fw_single")),
              disclose_horizon=bool(em.get("disclose_horizon", False)),
              field_order=str(em.get("field_order", "canonical")))
    if gc.get("b_pred") is not None:
        kw["b_pred"] = float(gc["b_pred"])
    # the scalar arguments above are already inside gen_config; pass the rest through `config`
    drop = {"scenario", "T", "seed", "ordering", "delta", "n_assets", "start_price", "engine", "b_pred"}
    cfg = {k: v for k, v in gc.items() if k not in drop}
    if cfg:
        kw["config"] = cfg
    return SyntheticMarketEnv(**kw)


def _col_hash(a) -> str:
    arr = np.ascontiguousarray(np.asarray(a, dtype=float))
    return hashlib.sha256(arr.tobytes()).hexdigest()[:24]


def repro(results: str, out: str):
    from simulation.provenance import generator_config_hash
    os.makedirs(out, exist_ok=True)
    metas = sorted(glob.glob(os.path.join(results, "**", "*.meta.json"), recursive=True))
    print(f"[repro] {len(metas)} pilot runs under {results}", flush=True)
    rows = []
    for mp in metas:
        meta = json.load(open(mp, encoding="utf-8"))
        csvp = mp.replace(".meta.json", ".csv")
        run = pd.read_csv(csvp) if os.path.exists(csvp) else None
        em = meta["env_metadata"]
        r = {"file": os.path.relpath(csvp, ROOT), "env_version": em.get("env_version"),
             "scenario": em.get("scenario"), "seed": em.get("seed"), "engine": em.get("engine"),
             "persona": meta["run_config"].get("persona"), "arm": meta["run_config"].get("arm"),
             "start_design": meta["run_config"].get("start_design"),
             "gen_config_keys": len(em.get("gen_config") or {}),
             "stored_gen_config_hash": meta.get("provenance", {}).get("Gen_Config_Hash")}
        # (a) the provenance function against its own record
        try:
            r["recomputed_gen_config_hash"] = generator_config_hash(em)
            r["gen_config_hash_matches"] = bool(r["recomputed_gen_config_hash"] == r["stored_gen_config_hash"])
        except Exception as e:
            r["recomputed_gen_config_hash"] = f"ERROR: {e}"; r["gen_config_hash_matches"] = False
        # (b) the path itself, two readings
        #     as_recorded  -- the engine the run recorded (`fw_single` for the pilot)
        #     fallback     -- ENGINE_DEFAULT, the documented CAL fallback the generator names in its own error
        #                     message when the recorded engine has no accepted estimate.  Reported as a MAGNITUDE
        #                     so "the path does not reproduce" is not only a missing file but a measured distance.
        from envs.v2.mispricing import ENGINE_DEFAULT
        for tag, override in (("as_recorded", None), ("fallback", ENGINE_DEFAULT)):
            try:
                env = env_from_meta(meta, engine_override=override)
                d = env.data[env.data["asset"] == 0].reset_index(drop=True)
                r[f"regen_ok_{tag}"] = True
                r[f"regen_start_price_{tag}"] = float(d["price"].iloc[0])
                for gen_col, run_col in COMPARE:
                    if run is None or run_col not in run.columns:
                        r[f"max_abs_diff_{tag}_{gen_col}"] = np.nan
                        continue
                    n = min(len(d), len(run))
                    a = d[gen_col].to_numpy(float)[:n]; b = run[run_col].to_numpy(float)[:n]
                    r[f"max_abs_diff_{tag}_{gen_col}"] = float(np.max(np.abs(a - b)))
                    r[f"hash_match_{tag}_{gen_col}"] = bool(_col_hash(a) == _col_hash(b))
                    r["n_compared"] = int(n)
            except Exception as e:
                r[f"regen_ok_{tag}"] = False
                # the repository root is stripped so the recorded message is the same on any machine
                msg = str(e)[:300].replace(ROOT, "<repo>").replace(ROOT.replace("\\", "/"), "<repo>")
                r[f"regen_error_{tag}"] = f"{type(e).__name__}: {msg}"
        for tag in ("as_recorded", "fallback"):
            diffs = [r.get(f"max_abs_diff_{tag}_{c}") for c, _ in COMPARE]
            diffs = [v for v in diffs if v is not None and np.isfinite(v)]
            r[f"worst_abs_diff_{tag}"] = float(max(diffs)) if diffs else np.nan
            r[f"path_reproduces_{tag}"] = bool(r.get(f"regen_ok_{tag}") and diffs and max(diffs) <= TOL)
        # the registered verdict is the AS-RECORDED reading: it is the run's own configuration
        r["path_reproduces"] = bool(r["path_reproduces_as_recorded"])
        r["worst_abs_diff"] = r["worst_abs_diff_as_recorded"]
        rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(out, "repro.csv"), index=False)
    n_rep = int(t["path_reproduces"].sum()); n = len(t)

    def _uniq(col, k=6):
        return sorted(set(round(float(v), k) for v in t[col].dropna()))[:10] if col in t else []

    def _errs(col):
        return sorted(set(str(v) for v in t[col].dropna()))[:3] if col in t else []

    summ = {"n_runs": n, "n_path_reproduces": n_rep,
            "n_path_reproduces_under_fallback_engine": int(t.get("path_reproduces_fallback", pd.Series(dtype=bool)).sum()),
            "n_regen_ok_as_recorded": int(t.get("regen_ok_as_recorded", pd.Series(dtype=bool)).sum()),
            "n_regen_ok_fallback": int(t.get("regen_ok_fallback", pd.Series(dtype=bool)).sum()),
            "n_gen_config_hash_matches": int(t["gen_config_hash_matches"].sum()),
            "tolerance": TOL, "state": pin_state(),
            "recorded_engines": sorted(set(str(v) for v in t["engine"].dropna())),
            "regen_error_as_recorded": _errs("regen_error_as_recorded"),
            "regen_error_fallback": _errs("regen_error_fallback"),
            "worst_abs_diff_fallback_median": float(t["worst_abs_diff_fallback"].median()) if "worst_abs_diff_fallback" in t and t["worst_abs_diff_fallback"].notna().any() else float("nan"),
            "worst_abs_diff_fallback_min": float(t["worst_abs_diff_fallback"].min()) if "worst_abs_diff_fallback" in t and t["worst_abs_diff_fallback"].notna().any() else float("nan"),
            "regen_start_price_unique_fallback": _uniq("regen_start_price_fallback"),
            "consequence": ("PREREG_PHASE_7.md 7: where the path does not reproduce, the pilot is re-scored on its "
                            "LOGGED COLUMNS ONLY and the baselines are rebuilt only for the cells whose path matches"),
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(summ, open(os.path.join(out, "repro.json"), "w", encoding="utf-8"), indent=1, default=float)

    L = ["# E7.6 — do the pilot's paths regenerate under the v2.1 switches?", "",
         f"{n} pilot runs (`{results}`), every one recorded with `env_version = "
         f"{sorted(set(t['env_version'].dropna()))}` and `engine = {sorted(set(t['engine'].dropna()))}`. "
         f"Each environment is rebuilt from its own `meta.json` and the regenerated path compared with the columns "
         f"the run logged, at a tolerance of {TOL:g}.", "",
         f"- **paths that reproduce under the recorded engine: {n_rep} of {n}**",
         f"- environments that could be CONSTRUCTED at all under the recorded engine: "
         f"{summ['n_regen_ok_as_recorded']} of {n}",
         f"- under the documented CAL fallback engine: constructed {summ['n_regen_ok_fallback']} of {n}, "
         f"reproducing {summ['n_path_reproduces_under_fallback_engine']} of {n}",
         f"- `Gen_Config_Hash` recomputed from the stored metadata matches the stored value in "
         f"{int(t['gen_config_hash_matches'].sum())} of {n}", ""]
    if summ["regen_error_as_recorded"]:
        L += ["The generator's own refusal, verbatim:", "", "```",
              summ["regen_error_as_recorded"][0], "```", ""]
    if summ["n_regen_ok_fallback"]:
        L += [f"Under the fallback engine the path is constructible but distant: the worst absolute difference "
              f"against the run's logged price / V / x has median **{summ['worst_abs_diff_fallback_median']:.4g}** "
              f"and minimum **{summ['worst_abs_diff_fallback_min']:.4g}** over {n} runs, and the regenerated day-1 "
              f"price takes the values {summ['regen_start_price_unique_fallback']} against the pilot's 100.0. "
              f"So the non-reproduction is a measured distance, not only a missing file.", "",
              "| scenario | seed | n runs | worst abs diff, fallback engine (price / V / x) |", "|---|---|---|---|"]
        for (sc, seed), g in t.groupby(["scenario", "seed"]):
            L.append(f"| {sc} | {seed} | {len(g)} | {g['worst_abs_diff_fallback'].max():.4g} |")
    L += ["", "The 27 keys the pilot's `gen_config` carries are restored exactly; the 23 `GenConfig` fields v2.1 "
              "added after the pilot are not in the record and take today's defaults. That is what the test "
              "measures. Guessing values the record does not hold would be a different experiment.", ""]
    with open(os.path.join(out, "repro.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L[:14]), flush=True)
    return t


def baselines(results: str, out: str, repro_table: pd.DataFrame = None):
    """Rebuild the per-cell baselines from `meta.json` and compare with the seven-column path, on the cells that
    reproduced.  Where nothing reproduces, that is the result and the comparison table says so."""
    from tools.report_v2 import cell_baselines
    os.makedirs(out, exist_ok=True)
    if repro_table is None:
        repro_table = pd.read_csv(os.path.join(out, "repro.csv"))
    ok = repro_table[repro_table["path_reproduces"] == True]  # noqa: E712
    rows = []
    for _, r in repro_table.iterrows():
        csvp = os.path.join(ROOT, r["file"])
        if not os.path.exists(csvp):
            continue
        df = pd.read_csv(csvp)
        df["__file"] = csvp          # `cell_baselines(from_meta=True)` locates meta.json from it, as load_runs does
        try:
            a = cell_baselines(df, from_meta=False)
            b = cell_baselines(df, from_meta=True)
        except Exception as e:
            msg = str(e)[:400].replace(ROOT, "<repo>").replace(ROOT.replace("\\", "/"), "<repo>")
            rows.append({"file": r["file"], "error": f"{type(e).__name__}: {msg}"}); continue
        for pol in sorted(set(a) & set(b)):
            for m in ("mcr_0.05", "band_mas", "return_pct", "mdd_pct", "turnover"):
                va, vb = a[pol].get(m, np.nan), b[pol].get(m, np.nan)
                rows.append({"file": r["file"], "scenario": r["scenario"], "seed": r["seed"],
                             "persona": r["persona"], "policy": pol, "metric": m,
                             "from_columns": va, "from_meta": vb,
                             "abs_diff": float(abs(va - vb)) if np.isfinite(va) and np.isfinite(vb) else np.nan,
                             "path_reproduces": bool(r["path_reproduces"])})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(out, "baselines_compare.csv"), index=False)
    n_err = int(t["error"].notna().sum()) if "error" in t.columns else 0
    L = ["# E7.6 — baselines rebuilt from `meta.json` against the seven-column path", "",
         f"{len(ok)} of {len(repro_table)} cells reproduce their path; the comparison is reported for every cell, "
         f"with the reproducing flag beside, so a difference is never read as an improvement on a path the agent "
         f"never saw.", ""]
    if n_err:
        errs = sorted(set(str(e) for e in t["error"].dropna()))
        L += [f"**`cell_baselines(from_meta=True)` could not be built for {n_err} of {len(repro_table)} cells**, "
              f"and the reason is E7.6's own finding rather than a defect in the rebuild: the environment the "
              f"metadata names cannot be constructed. The distinct failures, verbatim:", ""]
        for e in errs[:3]:
            L += ["```", e[:400], "```"]
        L += ["", "So the switch is correct and untestable on this pilot: it is tested instead on a freshly "
                  "generated cell whose configuration the seven run-CSV columns cannot express "
                  "(`tests/test_v2_1_phase_7.py::test_baselines_same_path_hash`).", ""]
    if not t.empty and "abs_diff" in t:
        g = t.groupby(["metric", "path_reproduces"])["abs_diff"].agg(["max", "mean", "size"]).reset_index()
        L += ["| metric | path reproduces | max abs diff | mean | n |", "|---|---|---|---|---|"]
        for _, r in g.iterrows():
            L.append(f"| {r['metric']} | {r['path_reproduces']} | {r['max']:.4g} | {r['mean']:.4g} | {int(r['size'])} |")
    with open(os.path.join(out, "baselines_compare.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="repro,baselines")
    ap.add_argument("--results", default=os.path.join(ROOT, "results_v2_pilot"))
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    t = None
    for st in a.stages.split(","):
        st = st.strip()
        if st == "repro":
            t = repro(a.results, a.out)
        elif st == "baselines":
            baselines(a.results, a.out, t)
        else:
            raise SystemExit(f"unknown stage {st!r}")


if __name__ == "__main__":
    main()
