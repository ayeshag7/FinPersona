"""E3's registered read: the common-start slice (`PREREG_PHASE_9_STAGE2_E3.md` 3).

    python -u -m tools.phase9.e9_5_e3_analyse

What this does, and why each step is the way it is:

*   **The registered family is not in `question_families()`.**  Section 3 registers {`memory`, `swapped`} -
    `static`, one family per model, m = 72, decided `bh_within`.  The shared dict holds `memory - static` in Q1
    and `swapped - memory` in Q2 -- and **no `swapped - static` at all**.  Left to the dict this frame fires two
    tier-C families, the rule flips to `by_across`, and the contrast E3 registered is never computed while a
    different question is answered in its place.  The registered family is therefore passed explicitly through
    `run_stats_v21(families=...)`, which leaves the estimator, the bootstrap, the BH step and the rule logic
    untouched and changes only which contrasts are asked for.

*   **The `trader` arm is held out of the confirmatory frame.**  It is the NONE reference for the salience
    shares, not a member of section 3's family, and `seed_level_pairs` would not pair it with anything here.

*   **One model at a time**, section 3's family being per model, with no claim about models in general.

**What this file does NOT do, and why.**  Section 3 also registers the salience shares
(`evaluation/salience.py` `salience_by_window`, seed-cluster bootstrap at 200 refits) and the persona side of the
day-1 gate (`tools/report_v2.py` `gate_tables`), and section 3's preconditions include **the static arm's mean
cash share per cell**.  All three read the per-STEP run series, and `per_run.csv` is one row per run: it carries
`band_mas`, the MCR family, turnover, drawdown, return, fallback share and trade count, and **no cash share**.
Those parts need the run CSVs themselves, which live on the cluster and in the archived run tarballs, so they
belong in a job where the runs are -- as the scoring did -- not here.  Predictions P1, P2 and P4 depend on them
and are left unevaluated rather than approximated.
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd

from tools.phase9.e9_5_predictions import UNEVALUATED, Prediction, verdict_of
from tools.phase9.e9_5_predictions import write as write_predictions
from tools.stats_v2 import run_stats_v21, scenario_cell

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E94 = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4")
OUT = os.path.join(E94, "stats_e3_slice")

E3_MANIFEST = "e9_4_stage2_slice"
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
CONFIRMATORY_ARMS = ("static", "memory", "swapped")

# Section 3's family, written here because the shared dict does not hold it.  Two contrasts x 3 personas
# x 4 scenarios x 3 tier-C metrics = 72, in ONE question key so BH runs within one family.
E3_FAMILY = {"E3": [("memory", "static"), ("swapped", "static")]}


def _slug(model: str) -> str:
    return model.replace("/", "_").replace("|", "_").replace(".", "_")


def frame(per_run: pd.DataFrame, model: str):
    d = per_run[(per_run["Manifest"] == E3_MANIFEST) & (per_run["Model"] == model)
                & (per_run["Persona"].isin(PERSONAS)) & (per_run["Arm"].isin(CONFIRMATORY_ARMS))]
    return (None, f"no rows") if d.empty else (d, "")


def key_collision(df: pd.DataFrame) -> int:
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    g = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed", "Arm"])["Setting"].nunique()
    return int((g > 1).sum())


def preconditions(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    return d.groupby(["Persona", "Scenario_Cell", "Arm"]).agg(
        n=("band_mas", "size"),
        fallback_share=("fallback_share", "mean"),
        max_fallback_share=("fallback_share", "max"),
        zero_trade_share=("trade_count", lambda s: float((s == 0).mean())),
        score_errors=("score_error", lambda s: int((s.fillna("") != "").sum())),
    ).reset_index()


def main() -> int:
    per_run = pd.read_csv(os.path.join(E94, "per_run.csv"))
    if E3_MANIFEST not in set(per_run["Manifest"]):
        raise SystemExit(f"{E3_MANIFEST} is not in per_run.csv -- score it first")
    os.makedirs(OUT, exist_ok=True)
    models = sorted(per_run[per_run["Manifest"] == E3_MANIFEST]["Model"].unique())
    print(f"E3 models present: {len(models)}")

    summary = {"models": {}, "family": {k: [list(x) for x in v] for k, v in E3_FAMILY.items()},
               "not_computed_here": ["salience shares (per-step)", "day-1 gate AUC (per-step)",
                                     "static-arm mean cash share (per-step)", "P1", "P2", "P4"],
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for model in models:
        df, why = frame(per_run, model)
        print(f"\n=== {model} ===")
        if df is None:
            print(f"  SKIPPED: {why}")
            summary["models"][model] = {"skipped": why}
            continue

        bad = key_collision(df)
        if bad:
            print(f"  REFUSING: {bad} keys carry two settings and would be averaged silently")
            summary["models"][model] = {"skipped": f"{bad} cross-setting key collisions"}
            continue

        pre = preconditions(df)
        pre.to_csv(os.path.join(OUT, f"{_slug(model)}_preconditions.csv"), index=False)
        print(f"  preconditions: worst fallback={pre['max_fallback_share'].max():.4%}; "
              f"zero-trade max={pre['zero_trade_share'].max():.2%}; "
              f"score errors={int(pre['score_errors'].sum())}  "
              f"(mean cash share needs the per-step series, see the module docstring)")

        res = run_stats_v21(df, os.path.join(OUT, _slug(model)), families=E3_FAMILY)
        t = res["contrasts"]
        tc = t[t["tier"] == "C"]
        rule = str(t["decision_rule"].iloc[0]) if len(t) else "none"
        m_fam = sorted(set(int(x) for x in tc["m_family"])) if len(tc) else []
        claims = tc[tc["claim"]]
        print(f"  confirmatory: {len(tc)} tests, m_family={m_fam}, rule={rule}")
        if rule != "bh_within" or m_fam != [72]:
            print(f"  WARNING: section 3 registers one family of 72 under bh_within; got {m_fam} under {rule}")
        print(f"  claims at q<=0.05: {len(claims)} of {len(tc)}")
        for _, r in claims.sort_values("q_bh_within_family").head(6).iterrows():
            print(f"      {r['contrast']:20s} {r['Persona']:5s} {r['Scenario_Cell']:15s} {r['metric']:17s} "
                  f"est={r['estimate']:+.4f} q={r['q_bh_within_family']:.4g}")

        # P3: ISFJ's band-MAS rises under memory (worsens) at common start too.
        isfj = tc[(tc["Persona"] == "ISFJ") & (tc["metric"] == "band_mas")
                  & (tc["contrast"] == "memory - static")]
        summary["models"][model] = {
            "n_confirmatory_tests": int(len(tc)), "m_family": m_fam, "decision_rule": rule,
            "n_claims": int(len(claims)),
            "isfj_band_mas_cells": int(len(isfj)),
            "isfj_band_mas_rises_under_memory": int((isfj["estimate"] > 0).sum()),
            "isfj_band_mas_rises_and_claimed": int(((isfj["estimate"] > 0) & isfj["claim"]).sum()),
            "max_fallback_share": float(pre["max_fallback_share"].max()),
            "max_zero_trade_share": float(pre["zero_trade_share"].max()),
            "n_score_errors": int(pre["score_errors"].sum()),
        }

    # Section 4's four.  Three of them read the per-STEP series and `per_run.csv` is one row per run, so
    # they are recorded `unevaluated` with the reason rather than approximated by something the frame
    # happens to carry -- an approximated prediction that holds is worse than none.
    rows = [v for v in summary["models"].values() if "isfj_band_mas_cells" in v]
    up = sum(1 for v in rows if v["isfj_band_mas_cells"]
             and v["isfj_band_mas_rises_under_memory"] == v["isfj_band_mas_cells"])
    per_step = ("reads the per-STEP run series; per_run.csv is one row per run and carries no cash share. "
                "The runs are on the cluster and in the archived tarballs")
    summary["predictions"] = write_predictions("E3", [
        Prediction("P1", "the persona share dominates the directive share",
                   "the persona share is the larger of the two", UNEVALUATED,
                   f"salience shares: {per_step}"),
        Prediction("P2", "the swapped mandate moves behaviour toward the text, not the label",
                   "the swapped arm tracks the text", UNEVALUATED, f"salience shares: {per_step}"),
        Prediction("P3", "ISFJ worsens under memory at common start too",
                   "its band-MAS rises under memory in at least five of the six models",
                   verdict_of(up >= 5),
                   f"rises in every cell in {up} of {len(rows)} models; "
                   f"{sum(v['isfj_band_mas_rises_under_memory'] for v in rows)} of "
                   f"{sum(v['isfj_band_mas_cells'] for v in rows)} cells positive",
                   {"models_rising_everywhere": up, "models": len(rows), "threshold": 5,
                    "cells_positive": sum(v["isfj_band_mas_rises_under_memory"] for v in rows),
                    "cells": sum(v["isfj_band_mas_cells"] for v in rows)}),
        Prediction("P4", "the persona side of the day-1 gate separates poorly",
                   "macro one-versus-rest AUC of the day-1 cash share", UNEVALUATED,
                   f"day-1 cash share: {per_step}"),
    ], OUT)

    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), indent=1)
    print(f"\nwritten -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
