"""E4's registered read: Track A against Track B (`PREREG_PHASE_9_STAGE2_E4.md` 3).

    python -u -m tools.phase9.e9_5_e4_analyse

What this does, and why each step is the way it is:

*   **The registered family is not in `question_families()`, and left alone the failure is silent.**  Section 3
    registers (Track A - Track B) within arm, one family per model, m = 72, decided `bh_within`.  The shared dict
    holds neither `static - static_B` nor `memory - memory_B`.  A frame carrying Track A beside a Track B
    relabelled as section 3 words it therefore fires exactly one tier-C family and reports `bh_within`, the
    registered rule -- while the only contrast it computes is `memory - static` **within Track A**, which is not
    E4's question at all.  The right-looking rule on the wrong question is worse than an error, so the family is
    passed explicitly through `run_stats_v21(families=...)`.  Estimator, bootstrap, BH step and rule logic are
    untouched; only the list of contrasts asked for changes.

*   **Track B is the headline's rows**, filtered to seeds 10001-10060 and relabelled, as section 3 directs.  The
    relabelling is what stops `seed_level_pairs` averaging the two tracks together: it groups on
    (Model, Persona, Scenario_Cell, Seed, Arm) and **ignores `Setting`**, so Track A's `static` and Track B's
    `static` would collapse into one mean with no error.  Under `static` against `static_B` they stay apart, and
    that is checked per model rather than assumed.

*   **One model at a time**, section 3's family being per model, with no claim about models in general.

Preconditions are reported per model and cell before any claim: the parse-fallback share, the zero-trade share
and the static arm's mean cash share.
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd

from tools.stats_v2 import run_stats_v21, scenario_cell

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E94 = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4")
OUT = os.path.join(E94, "stats_e4_track_a")

E4_MANIFEST = "e9_4_stage2_track_a"
HEADLINE = ("e9_4_stage1_headline_open", "e9_4_stage1_headline_open_b2")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SEEDS = range(10001, 10061)

# Section 3's family, written here because the shared dict does not hold it.  Two contrasts x 3 personas
# x 4 scenarios x 3 tier-C metrics = 72, in ONE question key so BH runs within one family.
E4_FAMILY = {"E4": [("static", "static_B"), ("memory", "memory_B")]}
RELABEL = {"static": "static_B", "memory": "memory_B"}


def _slug(model: str) -> str:
    return model.replace("/", "_").replace("|", "_").replace(".", "_")


def frames(per_run: pd.DataFrame, model: str):
    """Track A beside a relabelled Track B for one model, or (None, reason)."""
    a = per_run[(per_run["Manifest"] == E4_MANIFEST) & (per_run["Model"] == model)
                & (per_run["Persona"].isin(PERSONAS))]
    b = per_run[(per_run["Manifest"].isin(HEADLINE)) & (per_run["Model"] == model)
                & (per_run["Seed"].isin(SEEDS)) & (per_run["Persona"].isin(PERSONAS))
                & (per_run["Scenario"].isin(sorted(set(a["Scenario"]))))].copy()
    if a.empty or b.empty:
        return None, f"no rows (Track A {len(a)}, Track B {len(b)})"
    b = b[b["Arm"].isin(RELABEL)].copy()
    b["Arm"] = b["Arm"].map(RELABEL)
    return pd.concat([a, b], ignore_index=True), ""


def pairing_check(df: pd.DataFrame) -> dict:
    """The two tracks must not share an arm label on one key, or they are averaged with no error."""
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    g = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed", "Arm"])["Setting"].nunique()
    paired = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed"])["Arm"].nunique()
    return {"keys_with_two_settings": int((g > 1).sum()),
            "keys_with_four_arms": int((paired == 4).sum()),
            "keys_total": int(len(paired))}


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
    if E4_MANIFEST not in set(per_run["Manifest"]):
        raise SystemExit(f"{E4_MANIFEST} is not in per_run.csv -- score it first")
    os.makedirs(OUT, exist_ok=True)
    models = sorted(per_run[per_run["Manifest"] == E4_MANIFEST]["Model"].unique())
    print(f"E4 models present: {len(models)}")

    summary = {"models": {}, "family": {k: [list(x) for x in v] for k, v in E4_FAMILY.items()},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for model in models:
        df, why = frames(per_run, model)
        print(f"\n=== {model} ===")
        if df is None:
            print(f"  SKIPPED: {why}")
            summary["models"][model] = {"skipped": why}
            continue

        pc = pairing_check(df)
        print(f"  pairing: {pc['keys_with_four_arms']} of {pc['keys_total']} keys carry all four arms; "
              f"{pc['keys_with_two_settings']} keys carry two settings (0 required)")
        if pc["keys_with_two_settings"]:
            print("  REFUSING: the two tracks would be averaged silently")
            summary["models"][model] = {"skipped": "track labels collide"}
            continue

        pre = preconditions(df)
        pre.to_csv(os.path.join(OUT, f"{_slug(model)}_preconditions.csv"), index=False)
        print(f"  preconditions: worst fallback={pre['max_fallback_share'].max():.4%}; "
              f"zero-trade max={pre['zero_trade_share'].max():.2%}; "
              f"score errors={int(pre['score_errors'].sum())}")

        res = run_stats_v21(df, os.path.join(OUT, _slug(model)), families=E4_FAMILY)
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
            print(f"      {r['contrast']:22s} {r['Persona']:5s} {r['Scenario_Cell']:15s} {r['metric']:17s} "
                  f"est={r['estimate']:+.4f} q={r['q_bh_within_family']:.4g}")

        bm = tc[tc["metric"] == "band_mas"]
        summary["models"][model] = {
            "n_confirmatory_tests": int(len(tc)), "m_family": m_fam, "decision_rule": rule,
            "n_claims": int(len(claims)),
            "band_mas_cells": int(len(bm)),
            "band_mas_negative": int((bm["estimate"] < 0).sum()),
            "band_mas_negative_and_claimed": int(((bm["estimate"] < 0) & bm["claim"]).sum()),
            "max_fallback_share": float(pre["max_fallback_share"].max()),
            "max_zero_trade_share": float(pre["zero_trade_share"].max()),
            "n_score_errors": int(pre["score_errors"].sum()),
            "pairing": pc,
        }

    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), indent=1)
    print(f"\nwritten -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
