"""
v2.1 Phase 7 -- the pilot re-scored under the new definitions, with the old beside (plan 11.5; PREREG 7).

    python -u -m tools.phase7.e7_pilot_rescore

**On the logged columns only.**  E7.6 found that none of the 52 pilot paths regenerates: the pilot ran on engine
`fw_single`, whose SMM estimate Phase 2 rejected (`envs/v2/params/fw_single_stock.REJECTED.json`), so the
generator refuses to build it and the documented fallback engine gives a path 37-82 price units away
(`e7_6/repro.{md,json}`).  Everything below therefore comes from the run CSV's own columns -- `Cash_Share`, `x`,
`Price`, `Fundamental_Value`, `Portfolio_Value` -- which are what the agent actually did on the path it actually
saw, whatever the generator builds today.

What that costs, stated rather than worked around: **no normalised value can be recomputed**.  A normalised MCR
needs per-cell baselines simulated on the cell's own price path, and that path is not reproducible, so the
published `norm_mcr` figures are v2-era numbers that this phase can neither reproduce nor replace.  They are kept
beside the raw re-score with that annotation; they are not re-derived and not silently carried forward.

Output: <out>/pilot_rescore.{csv,md,json}
"""
from __future__ import annotations

import argparse
import glob
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

OUT = os.path.join(GEN, "e7_pilot")
RESULTS = os.path.join(ROOT, "results_v2_pilot")
HALF_WIDTHS = (0.05, 0.10, 0.15)
HW_IN_FORCE = 0.10
# the published figures this re-score is placed beside (docs/env_v2/status/PILOT_NOTES.md, 23 Aug 2026)
PUBLISHED = {("ISFJ", "static"): (0.23, 0.79), ("ISFJ", "memory"): (0.23, 0.79), ("ISFJ", "swapped"): (0.60, 0.23),
             ("ENTJ", "static"): (0.25, 0.82), ("ENTJ", "memory"): (0.26, 0.81), ("ENTJ", "swapped"): (0.94, 0.02),
             ("INTJ", "static"): (0.39, 0.38), ("INTJ", "memory"): (0.36, 0.44), ("INTJ", "swapped"): (0.48, 0.19)}


def thetas():
    from tools.phase7.e7_rescore import derived_thetas, theta_set
    th, labels = theta_set(derived_thetas())
    return th, labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=RESULTS)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    from evaluation import scoring as SC
    from evaluation.metrics_v2 import score_run

    th_list, labels = thetas()
    files = sorted(glob.glob(os.path.join(a.results, "**", "*.csv"), recursive=True))
    rows = []
    n_runs = 0
    for f in files:
        df = pd.read_csv(f)
        if "Cash_Share" not in df.columns or "Persona" not in df.columns:
            continue
        n_runs += 1
        r0 = df.iloc[0]
        persona = str(r0["Persona"])
        scored_as = persona if persona != "NONE" else "TRADER"
        v2 = score_run(df, scored_as, float(r0["Start_Cash_Share"]), scoring="v2")
        C = df["Cash_Share"].to_numpy(float); x = df["x"].to_numpy(float)
        ok = ~df["Parse_Status"].astype(str).eq("fallback").to_numpy() if "Parse_Status" in df else np.ones(len(df), bool)
        for hw in HALF_WIDTHS:
            for th in th_list:
                t = SC.regret_terms(C, x, th, scored_as, prev_target=float(C[0]), ok=ok, half_width=hw)
                w = SC.regret_terms_window(C, x, th, scored_as, prev_target=float(C[0]), ok=ok, half_width=hw)
                rows.append({
                    "file": os.path.relpath(f, ROOT), "model": r0["Model"], "persona": persona,
                    "arm": r0["Arm"], "scenario": r0["Scenario"], "seed": int(r0["Seed"]),
                    "start_design": r0.get("Start_Design", ""), "T": int(len(df)), "theta": th, "half_width": hw,
                    "theta_labels": "|".join(labels[round(float(th), 6)]),
                    "mcr": t["mcr"], "mcr_B": t["mcr_B"], "mcr_D": t["mcr_D"],
                    "coverage": t["coverage"], "n_resolvable": t["n_resolvable"],
                    "oracle_switches": t["oracle_switches"],
                    "share_target_lo": t["share_target_lo"], "share_target_hi": t["share_target_hi"],
                    "share_agent_outside": t["share_agent_outside"],
                    "mcr_window": w["mcr_window"], "mcr_window_B": w["mcr_window_B"],
                    "mcr_window_D": w["mcr_window_D"], "window_switches": w["window_switches"],
                    "band_mas_v2_key": v2["band_mas"], "mean_cash_share": v2["mean_cash_share"],
                    "return_pct": v2["return_pct"], "mdd_pct": v2["mdd_pct"], "turnover": v2["turnover"],
                    "mcr_v2_0.05": v2.get("mcr_0.05"), "coverage_v2_0.05": v2.get("coverage_0.05"),
                })
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(a.out, "pilot_rescore.csv"), index=False)

    # the headline comparison: the published (persona, arm) cells at theta 0.05, half-width 0.10
    # Two constructions, both reported.  `as_published` is every start-at-target run, which is what the published
    # table averaged -- and that INCLUDES the four T = 30 smoke runs in the ISFJ/ENTJ static and memory cells (n = 4
    # there against n = 3 elsewhere).  `T200_only` drops them.  The first is the comparability claim; the second is
    # the cleaner population, and the gap between them is a property of the published number, reported not hidden.
    base = t[(t.theta == 0.05) & (t.half_width == HW_IN_FORCE) & (t.start_design == "target")]
    comp = []
    for (persona, arm), g in base.groupby(["persona", "arm"]):
        g2 = g[g["T"] == 200]
        pub = PUBLISHED.get((persona, arm))
        comp.append({"persona": persona, "arm": arm,
                     "n_runs_as_published": int(len(g)), "n_runs_T200": int(len(g2)),
                     "mcr_as_published": float(g["mcr"].mean()),
                     "mcr_now": float(g2["mcr"].mean()), "mcr_B_now": float(g2["mcr_B"].mean()),
                     "mcr_D_now": float(g2["mcr_D"].mean()),
                     "mcr_window_now": float(g2["mcr_window"].mean()),
                     "oracle_switches_now": float(g2["oracle_switches"].mean()),
                     "share_agent_outside_now": float(g2["share_agent_outside"].mean()),
                     "mcr_published": pub[0] if pub else None,
                     "norm_mcr_published": pub[1] if pub else None})
    comp = pd.DataFrame(comp).sort_values(["persona", "arm"])
    comp.to_csv(os.path.join(a.out, "pilot_headline.csv"), index=False)

    # the per-run reproduction of the published table (the comparability claim, checked run by run)
    pubfile = os.path.join(ROOT, "docs", "env_v2", "generated", "pilot_report_per_run.csv")
    repro = {"file": os.path.relpath(pubfile, ROOT), "checked": False}
    if os.path.exists(pubfile):
        pr = pd.read_csv(pubfile)
        mine = t[(t.theta == 0.05) & (t.half_width == HW_IN_FORCE)].copy()
        # the published table carries no file column, so the runs are matched on the cell identifiers it does carry
        # n_rows distinguishes the T = 30 smoke runs from the T = 200 runs, which otherwise share every
        # identifier the published table carries
        KEY = ["Model", "Persona", "Arm", "Scenario", "Seed", "Start_Design", "Decode_Replicate", "n_rows"]
        if all(k in pr.columns for k in KEY):
            mine["Model"] = mine["model"]; mine["Persona"] = mine["persona"]; mine["Arm"] = mine["arm"]
            mine["Scenario"] = mine["scenario"]; mine["Seed"] = mine["seed"]
            mine["Start_Design"] = mine["start_design"]; mine["Decode_Replicate"] = 0
            mine["n_rows"] = mine["T"]
            m = mine.merge(pr[KEY + ["mcr_0.05", "norm_mcr_0.05"]], on=KEY, how="inner")
            d = (m["mcr"] - m["mcr_0.05"]).abs()
            repro = {"file": os.path.relpath(pubfile, ROOT), "checked": True, "n_matched": int(len(m)),
                     "n_published_rows": int(len(pr)),
                     "worst_abs_diff": float(d.max()) if len(d) else float("nan"),
                     "identical": bool(len(d) and d.max() <= 1e-12),
                     "note": "the published per-run table is reproduced run by run from the logged columns; the "
                             "PROSE figures in docs/env_v2/status/PILOT_NOTES.md are compared against that table "
                             "in prose_vs_table below"}
            prose = []
            for (persona, arm), (mcr_p, norm_p) in PUBLISHED.items():
                sub = pr[(pr.Persona == persona) & (pr.Arm == arm) & (pr.Start_Design == "target")]
                if sub.empty:
                    continue
                tv, nv = float(sub["mcr_0.05"].mean()), float(sub["norm_mcr_0.05"].mean())
                prose.append({"persona": persona, "arm": arm, "prose_mcr": mcr_p, "table_mcr": tv,
                              "prose_norm_mcr": norm_p, "table_norm_mcr": nv, "n_rows": int(len(sub)),
                              "mcr_agrees_to_2dp": bool(round(tv, 2) == mcr_p),
                              "norm_agrees_to_2dp": bool(round(nv, 2) == norm_p)})
            repro["prose_vs_table"] = prose
    json.dump(repro, open(os.path.join(a.out, "published_reproduction.json"), "w", encoding="utf-8"),
              indent=1, default=float)

    meta = {"n_runs": n_runs, "thetas": th_list, "half_widths": list(HALF_WIDTHS),
            "half_width_in_force": HW_IN_FORCE, "state": pin_state(),
            "normalisation": "NOT RECOMPUTED: a normalised value needs per-cell baselines on the cell's own price "
                             "path, and E7.6 found that none of the pilot's paths regenerates (the engine fw_single "
                             "was rejected by Phase 2's SMM). The published norm_mcr figures are v2-era numbers, "
                             "kept beside with that annotation, neither reproduced nor replaced.",
            "seconds": round(time.time() - t0),
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    meta["published_reproduction"] = repro
    meta["published_table_includes_smoke_runs"] = ("the published arm means average every start-at-target run, "
        "including the four T = 30 smoke runs, which sit in the ISFJ and ENTJ static and memory cells")
    json.dump({"meta": meta, "headline": comp.to_dict("records")},
              open(os.path.join(a.out, "pilot_rescore.json"), "w", encoding="utf-8"), indent=1, default=float)

    L = ["# The pilot re-scored under the Phase-7 definitions, with the published figures beside", "",
         f"{n_runs} runs (Gemini 2.5 Flash, seed 42, T = 200), scored on the **logged columns only**: E7.6 found "
         f"that none of the pilot's paths regenerates, so no baseline may be simulated on a path the agent never "
         f"saw and **no normalised value is recomputed**. The published `norm_mcr` figures below are v2-era "
         f"numbers, kept for the record and not carried forward.", "",
         f"theta = 0.05, half-width {HW_IN_FORCE}, start-at-target cells.", "",
         "**The published arm means include the four T = 30 smoke runs** in the ISFJ and ENTJ static and memory "
         "cells (n = 4 there against n = 3 elsewhere). `MCR as published` reproduces that construction; `MCR now` "
         "is the same statistic on the T = 200 runs only.", "",
         "| persona | arm | n (published / T200) | MCR as published | MCR published | MCR now (T200) | "
         "B (band violation) | D (directional) | MCR per window | oracle switches | share outside band | "
         "norm_MCR published (v2-era) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    def _fmt(v, spec=".2f"):
        return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else format(float(v), spec)

    for _, r in comp.iterrows():
        L.append(f"| {r['persona']} | {r['arm']} | {int(r['n_runs_as_published'])} / {int(r['n_runs_T200'])} | "
                 f"{r['mcr_as_published']:.4f} | {_fmt(r['mcr_published'])} | {r['mcr_now']:.4f} | "
                 f"{r['mcr_B_now']:.4f} | {r['mcr_D_now']:.4f} | {r['mcr_window_now']:.4f} | "
                 f"{r['oracle_switches_now']:.1f} | {r['share_agent_outside_now']:.3f} | "
                 f"{_fmt(r['norm_mcr_published'])} |")
    if repro.get("checked"):
        L += ["", f"Run by run against `generated/pilot_report_per_run.csv` (the table the published note was "
                  f"written from): {repro['n_matched']} runs matched, worst absolute difference in `mcr_0.05` "
                  f"**{repro['worst_abs_diff']:.3e}** — the Phase-7 decomposition is a decomposition of exactly the "
                  f"statistic that was published, not of a different one."]
    smoke = t[(t.theta == 0.05) & (t.half_width == HW_IN_FORCE) & (t["T"] != 200)]
    if len(smoke):
        L += ["", f"The {smoke['file'].nunique()} smoke runs (T = {sorted(set(smoke['T']))[0]}) on their own: mean "
                  f"MCR {smoke['mcr'].mean():.4f}, B {smoke['mcr_B'].mean():.4f}, D {smoke['mcr_D'].mean():.4f}.", ""]
    L += ["", "## The half-width sensitivity (E7.7), theta = 0.05", "",
          "| half-width | mean MCR | mean B | mean D |", "|---|---|---|---|"]
    for hw in HALF_WIDTHS:
        g = t[(t.theta == 0.05) & (t.half_width == hw) & (t.start_design == "target") & (t["T"] == 200)]
        L.append(f"| {hw:.2f} | {g['mcr'].mean():.4f} | {g['mcr_B'].mean():.4f} | {g['mcr_D'].mean():.4f} |")
    L.append("")
    with open(os.path.join(a.out, "pilot_rescore.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L), flush=True)
    print(f"[pilot] {len(t)} rows from {n_runs} runs ({time.time() - t0:.0f} s)", flush=True)


if __name__ == "__main__":
    main()
