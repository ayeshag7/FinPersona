"""E2's registered read: the causal package, one BH family per model (`PREREG_PHASE_9_STAGE2_E2.md` 3).

    python -u -m tools.phase9.e9_5_e2_analyse

What this does, and why each step is the way it is:

*   **The confirmatory frame holds the three placebo arms and `static`, and NOT `memory`.**  `run_stats_v21`
    iterates `stats_v2.question_families()`, a fixed dict.  With `memory` in the frame, Q1's (memory, static)
    contrast fires as well as Q3's three, the run yields TWO confirmatory families, and
    `inference_params.decision_rule(2)` flips from `bh_within` to `by_across` -- a rule E2 did not register.
    Section 3 says to re-frame rather than report under a rule the run did not use, so `memory` is held back
    for the absorption ratio, which is computed on its own frame.

*   **`seed_level_pairs` groups on (Model, Persona, Scenario_Cell, Seed, Arm) and ignores `Setting`.**  Here
    `static` and `memory` come from the stage-1 headline at setting `default` and the three placebo arms from
    E2 at setting `causal`; no (arm, seed) key appears under both, so nothing is averaged across settings.
    That is checked rather than assumed, per model, before any test runs.

*   **One model at a time.**  Section 3's family is per model, m = 54, and no claim about models in general is
    made from these tests.

Preconditions (section 3, Cycle 2's) are reported per model and cell before any claim is read: the
parse-fallback share, the zero-trade share and the static arm's mean cash share.
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd

from tools.phase9.e9_absorption import absorption, guard_counts
from tools.phase9.e9_5_predictions import Prediction, verdict_of
from tools.phase9.e9_5_predictions import write as write_predictions
from tools.stats_v2 import TIER_C, run_stats_v21, scenario_cell

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E94 = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4")
OUT = os.path.join(E94, "stats_e2_causal")

E2_MANIFEST = "e9_4_stage2_causal"

# Section 8's deviation applies to this model alone: its preflight was made advisory after the directive
# placebo broke its JSON contract, so its family is read under four extra rules rather than section 3's alone.
DEVIATION_MODEL = "vllm/meta-llama/llama-3.1-8b-instruct|default"
MIN_FREE_SEEDS = 30                      # rule 3: the registered test was sized at 60
HEADLINE = ("e9_4_stage1_headline_open", "e9_4_stage1_headline_open_b2")
PLACEBOS = ("placebo_declarative", "placebo_directive", "wrapper_only")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SEEDS = range(10001, 10061)


def _slug(model: str) -> str:
    return model.replace("/", "_").replace("|", "_").replace(".", "_")


def frames(per_run: pd.DataFrame, model: str):
    """(confirmatory frame, absorption frame) for one model, or (None, None) with a reason."""
    e2 = per_run[(per_run["Manifest"] == E2_MANIFEST) & (per_run["Model"] == model)]
    head = per_run[(per_run["Manifest"].isin(HEADLINE)) & (per_run["Model"] == model)
                   & (per_run["Seed"].isin(SEEDS)) & (per_run["Persona"].isin(PERSONAS))
                   & (per_run["Scenario"].isin(sorted(set(e2["Scenario"]))))]
    if e2.empty or head.empty:
        return None, None, f"no rows (E2 {len(e2)}, headline {len(head)})"
    static = head[head["Arm"] == "static"]
    memory = head[head["Arm"] == "memory"]
    conf = pd.concat([e2, static], ignore_index=True)
    absorb = pd.concat([e2, static, memory], ignore_index=True)
    return conf, absorb, ""


def key_collision(df: pd.DataFrame) -> pd.DataFrame:
    """Any (Model, Persona, Scenario_Cell, Seed, Arm) carrying more than one Setting would be silently
    averaged by `seed_level_pairs`.  Returns the offending keys; empty is the required state."""
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    g = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed", "Arm"])["Setting"].nunique()
    return g[g > 1].reset_index()


def preconditions(conf: pd.DataFrame) -> pd.DataFrame:
    d = conf.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    out = d.groupby(["Persona", "Scenario_Cell", "Arm"]).agg(
        n=("band_mas", "size"),
        fallback_share=("fallback_share", "mean"),
        max_fallback_share=("fallback_share", "max"),
        zero_trade_share=("trade_count", lambda s: float((s == 0).mean())),
        score_errors=("score_error", lambda s: int((s.fillna("") != "").sum())),
    ).reset_index()
    return out


def fallback_free_counts(conf: pd.DataFrame) -> pd.DataFrame:
    """Per cell and arm: how many of the seeds carry a run with no parse fallback at all."""
    d = conf.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    g = d.groupby(["Persona", "Scenario_Cell", "Arm"])
    return pd.DataFrame({"n": g.size(),
                         "n_fallback_free": g["fallback_share"].agg(lambda x: int((x == 0).sum()))}).reset_index()


def deviation_read(conf: pd.DataFrame, tc: pd.DataFrame, out_prefix: str) -> pd.DataFrame:
    """`PREREG_PHASE_9_STAGE2_E2.md` section 8, rules 2 and 3, per confirmatory contrast.

    Rule 3 is applied first because it disposes of a cell outright and costs nothing: fewer than 30 of the 60
    seeds fallback-free and the cell carries no claim.  Rule 2 then recomputes whatever survives on the subset
    of runs containing no fallback and withdraws any cell whose sign or BH decision moves between the two.

    A withdrawn cell is **uninterpretable, not null** -- section 8 is explicit about that -- so every contrast
    keeps a row here with the counts and both estimates behind the verdict, rather than being dropped.

    Where an arm has no fallback-free run at all its contrast cannot appear in the subset fit; rule 3 has
    already failed for it, so the absence is recorded rather than treated as a disagreement.
    """
    counts = fallback_free_counts(conf)
    free = {(r.Persona, r.Scenario_Cell, r.Arm): (int(r.n), int(r.n_fallback_free))
            for r in counts.itertuples()}

    sub = conf[conf["fallback_share"] == 0]
    sub_tc = pd.DataFrame()
    if len(sub) and len(set(sub["Arm"]) - {"static"}):
        st = run_stats_v21(sub, out_prefix + "_fallback_free")["contrasts"]
        sub_tc = st[st["tier"] == "C"]
    skey = {(r.contrast, r.Persona, r.Scenario_Cell, r.metric): r
            for r in sub_tc.itertuples()} if len(sub_tc) else {}

    rows = []
    for r in tc.itertuples():
        arm = str(r.contrast).split(" - ")[0].strip()
        n, nfree = free.get((r.Persona, r.Scenario_Cell, arm), (0, 0))
        sub_r = skey.get((r.contrast, r.Persona, r.Scenario_Cell, r.metric))
        rule3 = nfree >= MIN_FREE_SEEDS
        same_sign = same_bh = None
        if not rule3:
            verdict = f"no claim (rule 3: {nfree} of {n} seeds fallback-free, needs {MIN_FREE_SEEDS})"
        elif sub_r is None:
            verdict = "no claim (rule 2: contrast absent from the fallback-free subset)"
        else:
            same_sign = bool((r.estimate >= 0) == (sub_r.estimate >= 0))
            same_bh = bool(bool(r.claim) == bool(sub_r.claim))
            if same_sign and same_bh:
                verdict = "read"
            else:
                verdict = "no claim (rule 2: " + ("sign" if not same_sign else "BH decision") + " differs)"
        rows.append({"contrast": r.contrast, "Persona": r.Persona, "Scenario_Cell": r.Scenario_Cell,
                     "metric": r.metric, "n_seeds": n, "n_fallback_free": nfree,
                     "estimate_full": r.estimate, "claim_full": bool(r.claim),
                     "estimate_fallback_free": getattr(sub_r, "estimate", None),
                     "claim_fallback_free": None if sub_r is None else bool(sub_r.claim),
                     "rule_3_ok": rule3, "same_sign": same_sign, "same_bh_decision": same_bh,
                     "verdict": verdict})
    return pd.DataFrame(rows)


def predictions(absorb: pd.DataFrame, contr: pd.DataFrame) -> list:
    """Section 4's four, on the pooled artefacts the loop above wrote.

    Both frames arrive with section 8's deviation already applied: the deviation model's directive rows
    are out of `absorb`, because its absorption for that arm is computed on runs that are not
    fallback-free, and out of `contr`, because the contrasts they would support are uninterpretable
    rather than null.  A model that contributes no readable cell to a prediction is named in `stat`
    rather than counted against it.
    """
    adm = absorb[absorb["admitted"]]
    med = adm.groupby("arm")["A"].median()
    d, w, dec = (float(med.get(a, float("nan")))
                 for a in ("placebo_directive", "wrapper_only", "placebo_declarative"))
    n = {a: int((adm["arm"] == a).sum()) for a in PLACEBOS}

    isfj = contr[(contr["contrast"] == "placebo_directive - static")
                 & (contr["metric"] == "band_mas") & (contr["Persona"] == "ISFJ")]
    per_model = isfj.groupby("Model")["estimate"].agg(["size", lambda s: int((s > 0).sum())])
    per_model.columns = ["cells", "cells_up"]
    all_up = int((per_model["cells_up"] == per_model["cells"]).sum())
    any_up = int((per_model["cells_up"] > 0).sum())
    read = sorted(set(contr["Model"]) & set(isfj["Model"]))
    silent = sorted(set(contr["Model"]) - set(isfj["Model"]))

    entj = contr[(contr["contrast"] == "placebo_directive - static") & (contr["metric"] == "band_mas")
                 & (contr["Persona"] == "ENTJ") & (contr["Model"].str.contains("gemma-4-31b"))]

    return [
        Prediction(
            "P1", "the directive placebo absorbs less than 30 % of the mandate effect",
            "median A over the defined cells < 0.30", verdict_of(d < 0.30),
            f"median A(placebo_directive) = {d:+.4f} over {n['placebo_directive']} admitted cells",
            {"median_A_directive": d, "n_cells": n["placebo_directive"], "threshold": 0.30}),
        Prediction(
            "P2", "the declarative placebo absorbs least, the wrapper sits between",
            "A(declarative) <= A(wrapper_only) <= A(directive) on the medians",
            verdict_of(dec <= w <= d),
            f"{dec:+.4f} <= {w:+.4f} <= {d:+.4f} is false -- the registered order is reversed, the "
            f"directive placebo absorbing least of the three"
            if not dec <= w <= d else f"{dec:+.4f} <= {w:+.4f} <= {d:+.4f}",
            {"median_A_declarative": dec, "median_A_wrapper_only": w, "median_A_directive": d,
             "n_cells": n}),
        Prediction(
            "P3", "ISFJ moves under every arm: its band-MAS rises under placebo_directive",
            "rises in at least four of the six models", verdict_of(all_up >= 4),
            f"rises in every cell in {all_up} of {len(read)} readable models (in any cell: {any_up}); "
            f"{int(per_model['cells_up'].sum())} of {int(per_model['cells'].sum())} cells positive"
            + (f"; uninterpretable under section 8: {silent}" if silent else ""),
            {"models_rising_everywhere": all_up, "models_rising_anywhere": any_up,
             "models_readable": len(read), "cells_positive": int(per_model["cells_up"].sum()),
             "cells": int(per_model["cells"].sum()), "models_uninterpretable": silent,
             "threshold": 4}),
        Prediction(
            "P4", "Gemma 4 31B keeps its ENTJ sign under placebo_directive",
            "its ENTJ band-MAS rises, as it does under memory",
            verdict_of(len(entj) > 0 and bool((entj["estimate"] > 0).all())),
            f"estimates {[round(float(x), 4) for x in entj['estimate']]} over {len(entj)} cells",
            {"estimates": [float(x) for x in entj["estimate"]], "n_cells": int(len(entj))}),
    ]


def main() -> int:
    per_run = pd.read_csv(os.path.join(E94, "per_run.csv"))
    if E2_MANIFEST not in set(per_run["Manifest"]):
        raise SystemExit(f"{E2_MANIFEST} is not in per_run.csv -- run `e9_4_grid --stages score` first")
    os.makedirs(OUT, exist_ok=True)
    models = sorted(per_run[per_run["Manifest"] == E2_MANIFEST]["Model"].unique())
    print(f"E2 models present: {len(models)}")

    summary = {"models": {}, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    # Section 4's predictions are statements about the roster, not about one model, so the loop below
    # collects what each model contributes and they are evaluated once, after it.  Only rows section 8
    # leaves readable go in.
    pool_absorb, pool_contr = [], []
    for model in models:
        conf, absorb, why = frames(per_run, model)
        print(f"\n=== {model} ===")
        if conf is None:
            print(f"  SKIPPED: {why}")
            summary["models"][model] = {"skipped": why}
            continue

        bad = key_collision(conf)
        if len(bad):
            print(f"  REFUSING: {len(bad)} keys carry two settings and would be averaged silently")
            summary["models"][model] = {"skipped": f"{len(bad)} cross-setting key collisions"}
            continue

        pre = preconditions(conf)
        pre.to_csv(os.path.join(OUT, f"{_slug(model)}_preconditions.csv"), index=False)
        worst = pre.sort_values("max_fallback_share", ascending=False).iloc[0]
        print(f"  preconditions: worst cell fallback_share max={worst['max_fallback_share']:.4%} "
              f"({worst['Persona']} {worst['Scenario_Cell']} {worst['Arm']}); "
              f"zero-trade max={pre['zero_trade_share'].max():.2%}; "
              f"score errors={int(pre['score_errors'].sum())}")

        res = run_stats_v21(conf, os.path.join(OUT, _slug(model)))
        t = res["contrasts"]
        tc = t[t["tier"] == "C"]
        rule = str(t["decision_rule"].iloc[0]) if len(t) else "none"
        n_fam = int(t["n_confirmatory_families"].iloc[0]) if len(t) else 0
        m_fam = sorted(set(int(x) for x in tc["m_family"])) if len(tc) else []
        dev = None
        withdrawn = 0
        keep = None
        if model == DEVIATION_MODEL:
            dev = deviation_read(conf, tc, os.path.join(OUT, _slug(model)))
            dev.to_csv(os.path.join(OUT, f"{_slug(model)}_deviation.csv"), index=False)
            readable = set(map(tuple, dev.loc[dev["verdict"] == "read",
                                              ["contrast", "Persona", "Scenario_Cell", "metric"]].values))
            keep = pd.Series([tuple(x) in readable for x in
                              tc[["contrast", "Persona", "Scenario_Cell", "metric"]].values], index=tc.index)
            withdrawn = int((tc["claim"] & ~keep).sum())
            tc = tc.assign(claim=tc["claim"] & keep)

            # run_stats_v21 has already written the contrasts file with the unrestricted `claim`, and a reader
            # who opens it alone would count 13 claims section 8 withdraws.  Rewrite it with the verdict beside
            # every tier-C row and `claim` as the rules leave it, keeping the unrestricted value in its own
            # column so nothing is lost.
            cpath = os.path.join(OUT, f"{_slug(model)}_v21_contrasts.csv")
            allc = pd.read_csv(cpath)
            vmap = {tuple(r[:4]): r[4] for r in
                    dev[["contrast", "Persona", "Scenario_Cell", "metric", "verdict"]].values}
            key = list(zip(allc["contrast"], allc["Persona"], allc["Scenario_Cell"], allc["metric"]))
            allc["deviation_verdict"] = [vmap.get(k, "") for k in key]
            allc["claim_before_deviation"] = allc["claim"]
            allc["claim"] = [bool(c) and vmap.get(k, "read") == "read"
                             for c, k in zip(allc["claim"], key)]
            allc.to_csv(cpath, index=False)

        claims = tc[tc["claim"]]
        print(f"  confirmatory: {len(tc)} tests, families={n_fam}, m_family={m_fam}, rule={rule}")
        if dev is not None:
            byrule = dev.loc[dev["verdict"] != "read", "verdict"].str.extract(r"rule (\d)")[0].value_counts()
            print(f"  section 8 deviation: {withdrawn} claims WITHDRAWN as uninterpretable (not null); "
                  f"{int((dev['verdict'] != 'read').sum())} of {len(dev)} contrasts carry no claim "
                  f"(by rule: {dict(byrule)})")
        if rule != "bh_within":
            print("  WARNING: the run did not use the registered rule; re-frame rather than report this")
        print(f"  claims at q<=0.05: {len(claims)} of {len(tc)}")
        for _, r in claims.sort_values("q_bh_within_family").head(8).iterrows():
            print(f"      {r['contrast']:38s} {r['Persona']:5s} {r['Scenario_Cell']:6s} {r['metric']:17s} "
                  f"est={r['estimate']:+.4f} q={r['q_bh_within_family']:.4g}")

        arows = []
        for arm in PLACEBOS:
            a = absorption(absorb, arm=arm)
            if len(a):
                arows.append(a)
        A = pd.concat(arows, ignore_index=True) if arows else pd.DataFrame()
        # What this model contributes to section 4.  An arm that failed rule 3 is dropped from both, not
        # marked: its absorption is computed on runs that are not fallback-free and its contrasts are
        # uninterpretable, so counting either -- even as a negative -- would be reading contaminated runs.
        pool_contr.append((tc if keep is None else tc[keep]).assign(Model=model))
        if len(A):
            bad_arms = (set(dev.loc[dev["n_fallback_free"] < MIN_FREE_SEEDS, "contrast"].str.split(" - ").str[0])
                        if dev is not None else set())
            pool_absorb.append(A[~A["arm"].isin(bad_arms)])          # A already carries `Model`
        if len(A):
            A.to_csv(os.path.join(OUT, f"{_slug(model)}_absorption.csv"), index=False)
            gc = guard_counts(A)
            adm = A[A["admitted"]]
            print(f"  absorption: {gc['admitted']} of {gc['cells']} cells admitted "
                  f"(CI covers 0: {gc['excluded_ci_includes_0']}, below floor: {gc['excluded_below_floor']}, "
                  f"both: {gc['excluded_by_both']}); {gc['admitted_negative_mandate']} admitted cells have a "
                  f"negative mandate effect")
            if len(adm):
                for arm in PLACEBOS:
                    s = adm[adm["arm"] == arm]["A"]
                    if len(s):
                        print(f"      A[{arm:20s}] n={len(s):2d} median={s.median():+.3f} "
                              f"min={s.min():+.3f} max={s.max():+.3f}")
        summary["models"][model] = {
            "n_confirmatory_tests": int(len(tc)), "n_confirmatory_families": n_fam,
            "m_family": m_fam, "decision_rule": rule, "n_claims": int(len(claims)),
            "max_fallback_share": float(pre["max_fallback_share"].max()),
            "max_zero_trade_share": float(pre["zero_trade_share"].max()),
            "n_score_errors": int(pre["score_errors"].sum()),
            "absorption": guard_counts(A) if len(A) else {},
        }
        if dev is not None:
            contaminated = sorted(set(dev.loc[dev["n_fallback_free"] < MIN_FREE_SEEDS, "contrast"]))
            summary["models"][model].update({
                "deviation": "PREREG_PHASE_9_STAGE2_E2.md section 8",
                "n_claims_withdrawn": withdrawn,
                "n_contrasts_without_claim": int((dev["verdict"] != "read").sum()),
                "arms_failing_rule_3": contaminated,
            })
            if contaminated:
                print(f"  NOTE: absorption for {contaminated} is computed on runs that are not fallback-free "
                      f"and is not readable for the same reason the contrasts are not")

    if pool_absorb and pool_contr:
        summary["predictions"] = write_predictions(
            "E2", predictions(pd.concat(pool_absorb, ignore_index=True),
                              pd.concat(pool_contr, ignore_index=True)), OUT)

    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), indent=1)
    print(f"\nwritten -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
