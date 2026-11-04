"""E7's registered read: the OCEAN vocabulary gradient (`PREREG_PHASE_9_STAGE2_E7.md` 3).

    python -u -m tools.phase9.e9_5_e7_analyse

What this does, and why each step is the way it is:

*   **The registered family is not in `question_families()`, and left alone the failure is of E4's kind.**  Section 3
    registers the VOCABULARY contrast within arm -- OCEAN minus MBTI for `static`, `memory` and `swapped`, the mandate
    held byte-identical -- one family per model, m = 72, decided `bh_within`.  The shared dict holds no such pair.  On
    the raw E7 frame it fires Q1's `memory - static` and Q2's `swapped - memory` within the OCEAN rows: two tier-C
    families, `by_across`, and not one registered contrast.  On the frame section 3 words -- E3's MBTI rows beside
    E7's, relabelled `static_M` / `memory_M` / `swapped_M` -- it fires Q1 and Q2 within OCEAN again and reports them
    under `bh_within`: the registered rule on the wrong question, with nothing in the output saying so.  The family is
    therefore passed explicitly through `run_stats_v21(families=...)`, as E3 and E4 pass theirs.

*   **The MBTI side is E3's slice**, filtered to the two personas with an OCEAN counterpart and relabelled, as section 3
    directs.  INTJ has no counterpart and never enters an E7 frame.  The relabelling is what stops `seed_level_pairs`
    -- which groups on (Model, Persona, Scenario_Cell, Seed, Arm) and ignores both `Manifest` and `Setting` -- from
    averaging O1's static runs with ISFJ's: both sides carry the setting `common_start`, and under one persona label
    they would collapse into one mean with no error.  Checked per model before any test runs, never assumed.

*   **One model at a time**, section 3's family being per model, with no claim about models in general.

*   **The vocabulary x arm interaction**, (memory - static)_OCEAN - (memory - static)_MBTI on the same seed and path, is
    section 3's second registered read, against E5's equivalence margin of 0.025 (half of Delta) on the 90 % one-way
    path-bootstrap interval -- the two-one-sided-tests reading E5 registered.  It is read only on ADMITTED cells, where
    at least one vocabulary's mandate effect reaches 0.01 (E2's registered floor), so that two arms pinned at the
    metric's floor cannot be reported as "equivalent" by arithmetic -- E4's P2 lesson.

What this file does NOT do, and why.  The salience shares, the day-1 gate and the static arm's mean cash share read
the per-STEP series, which `per_run.csv` does not carry.  `tools/phase9/e9_5_e7_salience.py` computes them where the
runs are and writes `salience_summary.json` into this script's output directory; P1 and P5 are read from that file
when it exists and are reported `unevaluated` otherwise -- never approximated from something the frame happens to hold.
"""
from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from tools.phase9.e9_5_predictions import DEGENERATE, UNEVALUATED, Prediction, verdict_of
from tools.phase9.e9_5_predictions import write as write_predictions
from tools.stats_v2 import TIER_C, pigeonhole_ci, run_stats_v21, scenario_cell, seed_level_pairs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E94 = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4")
OUT = os.path.join(E94, "stats_e7_ocean")
NOISE = os.path.join(E94, "selection", "noise_seeds.csv")

E7_MANIFEST = "e9_4_stage2_ocean"
E3_MANIFEST = "e9_4_stage2_slice"
SEEDS = range(10001, 10061)
ARMS = ("static", "memory", "swapped")
# the two persona pairs of the gradient; INTJ has no OCEAN counterpart and is not in any E7 frame
PAIRS = {"conservative": ("O1_conservative", "ISFJ"), "aggressive": ("O2_aggressive", "ENTJ")}
OCEAN = {o: cat for cat, (o, _) in PAIRS.items()}
MBTI = {m: cat for cat, (_, m) in PAIRS.items()}
SUFFIX = "_M"                                   # the MBTI side's arm label, as section 3 words it
# Section 3's family, written here because the shared dict does not hold it: 3 contrasts x 2 personas x 4 scenario
# cells x 3 tier-C metrics = 72, in ONE question key so BH runs within one family.
E7_FAMILY = {"E7": [(a, a + SUFFIX) for a in ARMS]}
# Section 5's exploratory within-OCEAN family, E3's registered MBTI family on the new vocabulary: 2 x 2 x 4 x 3 = 48.
E7_WITHIN = {"E7_within_ocean": [("memory", "static"), ("swapped", "static")]}
DELTA = 0.05                                    # D12's minimum effect on band-MAS
MARGIN = 0.025                                  # E5's registered equivalence margin, half of Delta
ADMIT = 0.01                                    # E2's registered floor: a mandate effect below a fifth of Delta
FLOOR = 0.001                                   # E4's floor: a cell mean below this sits on band-MAS's floor
R2_READABLE = 0.5                               # the v1 gate's surrogate criterion (E0_SEPARABILITY_GATE_V1.md)
SHARE_TOL = 0.15                                # P1's vocabulary-invariance tolerance on S_persona
AUC_TOL = 0.10                                  # P5's tolerance on the day-1 AUC


def _slug(model: str) -> str:
    return model.replace("/", "_").replace("|", "_").replace(".", "_")


def frames(per_run: pd.DataFrame, model: str):
    """E7's OCEAN rows beside E3's relabelled MBTI rows for one model, or (None, reason)."""
    o = per_run[(per_run["Manifest"] == E7_MANIFEST) & (per_run["Model"] == model)
                & per_run["Persona"].isin(OCEAN) & per_run["Arm"].isin(ARMS)].copy()
    m = per_run[(per_run["Manifest"] == E3_MANIFEST) & (per_run["Model"] == model)
                & per_run["Persona"].isin(MBTI) & per_run["Arm"].isin(ARMS) & per_run["Seed"].isin(SEEDS)].copy()
    if o.empty or m.empty:
        return None, f"no rows (OCEAN {len(o)}, MBTI {len(m)})"
    o["Vocabulary"], m["Vocabulary"] = "ocean", "mbti"
    o["Persona"] = o["Persona"].map(OCEAN)
    m["Persona"] = m["Persona"].map(MBTI)
    m["Arm"] = m["Arm"] + SUFFIX
    return pd.concat([o, m], ignore_index=True), ""


def pairing_check(df: pd.DataFrame) -> dict:
    """Every (persona, cell, seed) key must carry all six arms, and no (key, arm) may come from two manifests."""
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    g = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed", "Arm"])["Manifest"].nunique()
    paired = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed"])["Arm"].nunique()
    return {"keys_with_two_manifests": int((g > 1).sum()), "keys_with_six_arms": int((paired == 6).sum()),
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


def cell_means(df: pd.DataFrame, metric: str = "band_mas") -> pd.DataFrame:
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    return d.groupby(["Persona", "Scenario_Cell", "Arm"])[metric].mean().unstack("Arm")


def _ci(g: pd.DataFrame, alpha: float) -> dict:
    return pigeonhole_ci(g, n_boot=1999, seed=0, alpha=alpha)


def equivalence(df: pd.DataFrame, mdd: float, metric: str = "band_mas") -> pd.DataFrame:
    """P2's table: the static-arm vocabulary contrast per cell with its 90 % (TOST) and 95 % intervals, read against
    +/- Delta; a cell is DEGENERATE when both vocabularies' static arms sit below the floor and UNDERPOWERED when the
    model's registered MDD at S = 60 exceeds Delta (a null there is uninformative, not evidence of equivalence)."""
    cm = cell_means(df, metric)
    rows = []
    for (persona, cell), g in seed_level_pairs(df, metric, "static", "static" + SUFFIX).groupby(["Persona", "Scenario_Cell"]):
        if g["Path"].nunique() < 2:
            continue
        b90, b95 = _ci(g, 0.10), _ci(g, 0.05)
        so, sm = float(cm.loc[(persona, cell), "static"]), float(cm.loc[(persona, cell), "static" + SUFFIX])
        degenerate = so < FLOOR and sm < FLOOR
        rows.append({"Persona": persona, "Scenario_Cell": cell, "metric": metric, "estimate": b95["estimate"],
                     "lo90": b90["ci_lo"], "hi90": b90["ci_hi"], "lo95": b95["ci_lo"], "hi95": b95["ci_hi"],
                     "n_pairs": b95["n_pairs"], "static_ocean": so, "static_mbti": sm,
                     "degenerate": degenerate, "underpowered": bool(mdd > DELTA), "mdd_S60": mdd,
                     "inside_delta_90": bool(b90["ci_lo"] >= -DELTA and b90["ci_hi"] <= DELTA)})
    return pd.DataFrame(rows)


def interaction_pairs(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Seed-level (memory - static)_OCEAN - (memory - static)_MBTI on the same path."""
    a = seed_level_pairs(df, metric, "memory", "static").rename(columns={"d": "d_ocean"})
    b = seed_level_pairs(df, metric, "memory" + SUFFIX, "static" + SUFFIX).rename(columns={"d": "d_mbti"})
    m = a.merge(b, on=["Model", "Persona", "Scenario_Cell", "Seed", "Path"])
    m["d"] = m["d_ocean"] - m["d_mbti"]
    return m


def interaction(df: pd.DataFrame, metric: str = "band_mas") -> pd.DataFrame:
    """P4's table: the vocabulary x arm interaction per cell, its 90 % (TOST) and 95 % intervals against E5's margin,
    and whether the cell is ADMITTED (at least one vocabulary's mandate effect reaches ADMIT)."""
    rows = []
    for (persona, cell), g in interaction_pairs(df, metric).groupby(["Persona", "Scenario_Cell"]):
        if g["Path"].nunique() < 2:
            continue
        b90, b95 = _ci(g, 0.10), _ci(g, 0.05)
        eo, em = float(g["d_ocean"].mean()), float(g["d_mbti"].mean())
        rows.append({"Persona": persona, "Scenario_Cell": cell, "metric": metric, "estimate": b95["estimate"],
                     "lo90": b90["ci_lo"], "hi90": b90["ci_hi"], "lo95": b95["ci_lo"], "hi95": b95["ci_hi"],
                     "n_pairs": b95["n_pairs"], "effect_ocean": eo, "effect_mbti": em,
                     "admitted": bool(max(abs(eo), abs(em)) >= ADMIT), "margin": MARGIN,
                     "inside_margin_90": bool(b90["ci_lo"] >= -MARGIN and b90["ci_hi"] <= MARGIN),
                     "signs_agree": bool(np.sign(eo) == np.sign(em))})
    return pd.DataFrame(rows)


def pooled_effects(df: pd.DataFrame, metric: str = "band_mas") -> pd.DataFrame:
    """P3's table: memory - static per persona and vocabulary, POOLED over the four scenario cells (240 pairs), with its
    95 % one-way path-bootstrap interval -- the pooled reading E3's section 4 used for ISFJ."""
    rows = []
    for voc, (arm, ref) in (("ocean", ("memory", "static")), ("mbti", ("memory" + SUFFIX, "static" + SUFFIX))):
        for persona, g in seed_level_pairs(df, metric, arm, ref).groupby("Persona"):
            if g["Path"].nunique() < 2:
                continue
            b = _ci(g, 0.05)
            rows.append({"Persona": persona, "Vocabulary": voc, "metric": metric, "estimate": b["estimate"],
                         "ci_lo": b["ci_lo"], "ci_hi": b["ci_hi"], "n_pairs": b["n_pairs"], "n_paths": b["n_paths"]})
    return pd.DataFrame(rows)


def read_salience_summary() -> Optional[dict]:
    p = os.path.join(OUT, "salience_summary.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def _readable(fr: dict) -> bool:
    w = fr.get("windows") or []
    return bool(w) and sum(1 for x in w if x.get("r2") is not None and x["r2"] >= R2_READABLE) * 2 >= len(w)


def _mean_share(fr: dict, key: str) -> float:
    w = [x for x in (fr.get("windows") or []) if x.get("r2") is not None and x["r2"] >= R2_READABLE]
    return float(np.mean([x[key] for x in w])) if w else float("nan")


def predictions(models: list, equiv: pd.DataFrame, inter: pd.DataFrame, pooled: pd.DataFrame,
                salience: Optional[dict]) -> List[Prediction]:
    """Section 4's five.  P1 and P5 read the per-step summary and are `unevaluated` without it."""
    per_step = ("reads the per-STEP series (tools/phase9/e9_5_e7_salience.py writes salience_summary.json where the "
                "runs are); per_run.csv is one row per run and carries no cash share")
    out = []

    # ---- P1: the shares, on the OCEAN frame, and vocabulary invariance against the MBTI pair frame ----
    if salience is None:
        out.append(Prediction("P1", "the persona share dominates the directive share on the OCEAN frame, and S_persona "
                                    "is vocabulary-invariant within 0.15 of the MBTI pair frame",
                              "S_persona > S_directive in at least five of the six models; |S_persona(OCEAN) - "
                              "S_persona(MBTI pair)| <= 0.15 in at least four", UNEVALUATED, f"salience shares: {per_step}"))
    else:
        readable, dominate, invariant, unread = 0, 0, 0, []
        for mdl in models:
            fr = (salience.get("models") or {}).get(mdl) or {}
            o, m = fr.get("ocean") or {}, fr.get("mbti_pair") or {}
            if not (o.get("identified") and m.get("identified") and _readable(o) and _readable(m)):
                unread.append(mdl.split("/")[-1].split("|")[0]); continue
            readable += 1
            sp, sd, spm = _mean_share(o, "S_persona"), _mean_share(o, "S_directive"), _mean_share(m, "S_persona")
            dominate += int(sp > sd)
            invariant += int(abs(sp - spm) <= SHARE_TOL)
        out.append(Prediction("P1", "the persona share dominates the directive share on the OCEAN frame, and S_persona "
                                    "is vocabulary-invariant within 0.15 of the MBTI pair frame",
                              "S_persona > S_directive in at least five of the six models; |S_persona(OCEAN) - "
                              "S_persona(MBTI pair)| <= 0.15 in at least four",
                              verdict_of(dominate >= 5 and invariant >= 4),
                              f"persona share dominates in {dominate} of {readable} readable models and lies within "
                              f"{SHARE_TOL} of the MBTI pair frame's in {invariant}; unreadable (surrogate OOF R2 below "
                              f"{R2_READABLE} in more than half the windows of a frame, or not identified): {unread}",
                              {"dominate": dominate, "invariant": invariant, "readable": readable, "unreadable": unread,
                               "models": len(models), "bar": [5, 4], "share_tol": SHARE_TOL, "r2_readable": R2_READABLE}))

    # ---- P2: the static arm is vocabulary-equivalent within Delta ----
    e = equiv[equiv["metric"] == "band_mas"] if len(equiv) else equiv
    counted = e[~e["degenerate"] & ~e["underpowered"]] if len(e) else e
    n_in = int(counted["inside_delta_90"].sum()) if len(counted) else 0
    n_deg = int(e["degenerate"].sum()) if len(e) else 0
    n_up = int((e["underpowered"] & ~e["degenerate"]).sum()) if len(e) else 0
    out.append(Prediction("P2", "the static arm is vocabulary-equivalent: the OCEAN - MBTI band-MAS contrast lies "
                                "inside +/- Delta",
                          "the 90 % interval lies inside +/- 0.05 in at least two thirds of the counted cells; a cell "
                          "with both static arms below the floor is degenerate and an underpowered model's cells "
                          "(MDD at S = 60 above Delta) are reported, not counted",
                          DEGENERATE if not len(counted) else verdict_of(n_in * 3 >= 2 * len(counted)),
                          f"inside in {n_in} of {len(counted)} counted cells ({len(e)} in all: {n_deg} degenerate at the "
                          f"floor, {n_up} underpowered)",
                          {"inside": n_in, "counted": int(len(counted)), "cells": int(len(e)), "degenerate": n_deg,
                           "underpowered": n_up, "delta": DELTA, "floor": FLOOR}))

    # ---- P3: the memory effect replicates with magnitude ----
    cons = pooled[(pooled["metric"] == "band_mas") & (pooled["Persona"] == "conservative")
                  & (pooled["Vocabulary"] == "ocean")] if len(pooled) else pooled
    rises = {str(r["Model"]): bool(r["estimate"] >= ADMIT) for _, r in cons.iterrows()} if len(cons) else {}
    n_rise = sum(rises.values())
    agg = inter[(inter["metric"] == "band_mas") & (inter["Persona"] == "aggressive")] if len(inter) else inter
    both = agg[(agg["effect_ocean"].abs() >= ADMIT) & (agg["effect_mbti"].abs() >= ADMIT)] if len(agg) else agg
    n_agree = int(both["signs_agree"].sum()) if len(both) else 0
    clause_a = n_rise >= 5
    clause_b = bool(len(both)) and n_agree * 3 >= 2 * len(both)
    out.append(Prediction("P3", "the memory effect replicates on the OCEAN vocabulary with magnitude: O1 worsens under "
                                "memory as ISFJ does, and O2's sign agrees with ENTJ's",
                          "O1's band-MAS memory - static, pooled over the four scenarios, is at least +0.01 in at least "
                          "five of the six models; O2's and ENTJ's memory - static agree in sign in at least two thirds "
                          "of the cells where both reach 0.01",
                          DEGENERATE if not len(both) and clause_a else verdict_of(clause_a and clause_b),
                          f"O1's pooled memory - static reaches {ADMIT} in {n_rise} of {len(rises)} models; O2 and ENTJ "
                          f"agree in sign in {n_agree} of {len(both)} aggressive cells where both effects reach {ADMIT} "
                          f"(of {len(agg)})",
                          {"models_rising_pooled": n_rise, "models": len(rises), "rising_by_model": rises,
                           "agree": n_agree, "both_admitted": int(len(both)), "aggressive_cells": int(len(agg)),
                           "admit": ADMIT, "bar": [5, "two thirds"]}))

    # ---- P4: framework independence, the vocabulary x arm interaction inside E5's margin ----
    i = inter[inter["metric"] == "band_mas"] if len(inter) else inter
    adm = i[i["admitted"]] if len(i) else i
    n_eq = int(adm["inside_margin_90"].sum()) if len(adm) else 0
    out.append(Prediction("P4", "framework independence: the vocabulary x arm interaction on band-MAS lies inside E5's "
                                "equivalence margin",
                          "the 90 % interval of (memory - static)_OCEAN - (memory - static)_MBTI lies inside +/- 0.025 "
                          "in at least two thirds of the admitted cells (at least one vocabulary's mandate effect "
                          "reaches 0.01)",
                          DEGENERATE if not len(adm) else verdict_of(n_eq * 3 >= 2 * len(adm)),
                          f"inside the margin in {n_eq} of {len(adm)} admitted cells ({len(i)} in all; "
                          f"{int(len(i) - len(adm))} not admitted: both mandate effects below {ADMIT})",
                          {"inside": n_eq, "admitted": int(len(adm)), "cells": int(len(i)), "margin": MARGIN, "admit": ADMIT}))

    # ---- P5: the day-1 gate's persona side on the OCEAN pair tracks the MBTI pair's ----
    if salience is None:
        out.append(Prediction("P5", "the day-1 gate's persona side on the OCEAN pair tracks the MBTI pair's",
                              "|AUC(O1 vs O2) - AUC(ISFJ vs ENTJ)| <= 0.10 in at least four of the six models; no "
                              "pass/fail of the gate is claimed (its null is NOT COMPUTABLE under NONE alone)",
                              UNEVALUATED, f"day-1 cash share: {per_step}"))
    else:
        close, have = 0, 0
        for mdl in models:
            g = ((salience.get("models") or {}).get(mdl) or {}).get("gate") or {}
            a, b = (g.get("ocean") or {}).get("auc"), (g.get("mbti_pair") or {}).get("auc")
            if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)):
                continue
            have += 1
            close += int(abs(a - b) <= AUC_TOL)
        out.append(Prediction("P5", "the day-1 gate's persona side on the OCEAN pair tracks the MBTI pair's",
                              "|AUC(O1 vs O2) - AUC(ISFJ vs ENTJ)| <= 0.10 in at least four of the six models; no "
                              "pass/fail of the gate is claimed (its null is NOT COMPUTABLE under NONE alone)",
                              verdict_of(close >= 4),
                              f"within {AUC_TOL} in {close} of {have} models with both AUCs computed",
                              {"close": close, "computed": have, "models": len(models), "auc_tol": AUC_TOL}))
    return out


def main() -> int:
    per_run = pd.read_csv(os.path.join(E94, "per_run.csv"))
    if E7_MANIFEST not in set(per_run["Manifest"]):
        raise SystemExit(f"{E7_MANIFEST} is not in per_run.csv -- score it first")
    if E3_MANIFEST not in set(per_run["Manifest"]):
        raise SystemExit(f"{E3_MANIFEST} is not in per_run.csv -- E7's MBTI side is E3's slice")
    os.makedirs(OUT, exist_ok=True)
    mdd = pd.read_csv(NOISE).set_index("Model")["mdd_S60_bm"].to_dict() if os.path.exists(NOISE) else {}
    models = sorted(per_run[per_run["Manifest"] == E7_MANIFEST]["Model"].unique())
    print(f"E7 models present: {len(models)}")
    salience = read_salience_summary()
    print("per-step summary:", "present" if salience else "absent (P1, P5 unevaluated)")

    summary = {"models": {}, "family": {k: [list(x) for x in v] for k, v in E7_FAMILY.items()},
               "exploratory_family": {k: [list(x) for x in v] for k, v in E7_WITHIN.items()},
               "constants": {"delta": DELTA, "margin": MARGIN, "admit": ADMIT, "floor": FLOOR,
                             "r2_readable": R2_READABLE, "share_tol": SHARE_TOL, "auc_tol": AUC_TOL},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    all_equiv, all_inter, all_within, all_pooled = [], [], [], []
    for model in models:
        df, why = frames(per_run, model)
        print(f"\n=== {model} ===")
        if df is None:
            print(f"  SKIPPED: {why}")
            summary["models"][model] = {"skipped": why}
            continue
        pc = pairing_check(df)
        print(f"  pairing: {pc['keys_with_six_arms']} of {pc['keys_total']} keys carry all six arms; "
              f"{pc['keys_with_two_manifests']} (key, arm) pairs come from two manifests (0 required)")
        if pc["keys_with_two_manifests"]:
            print("  REFUSING: the two vocabularies would be averaged silently")
            summary["models"][model] = {"skipped": "vocabulary labels collide"}
            continue
        pre = preconditions(df)
        pre.to_csv(os.path.join(OUT, f"{_slug(model)}_preconditions.csv"), index=False)
        print(f"  preconditions: worst fallback={pre['max_fallback_share'].max():.4%}; "
              f"zero-trade max={pre['zero_trade_share'].max():.2%}; score errors={int(pre['score_errors'].sum())}  "
              f"(mean cash share needs the per-step series: salience_summary.json)")

        res = run_stats_v21(df, os.path.join(OUT, _slug(model)), families=E7_FAMILY)
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
            print(f"      {r['contrast']:20s} {r['Persona']:13s} {r['Scenario_Cell']:15s} {r['metric']:17s} "
                  f"est={r['estimate']:+.4f} q={r['q_bh_within_family']:.4g}")

        # section 5: the within-OCEAN family, E3's registered MBTI family on the new vocabulary -- intervals, no claim
        ocean_only = df[df["Vocabulary"] == "ocean"]
        wres = run_stats_v21(ocean_only, os.path.join(OUT, f"{_slug(model)}_within_ocean"), families=E7_WITHIN)
        w = wres["contrasts"].copy()
        w["role"] = "exploratory (section 5): no claim is made from this family"
        w["claim"] = False
        w.to_csv(os.path.join(OUT, f"{_slug(model)}_within_ocean_v21_contrasts.csv"), index=False)
        all_within.append(w.assign(Model=model))

        eq = equivalence(df, float(mdd.get(model, float("nan"))))
        eq.insert(0, "Model", model)
        eq.to_csv(os.path.join(OUT, f"{_slug(model)}_e7_equivalence.csv"), index=False)
        inter = pd.concat([interaction(df, met) for met in TIER_C if met in df.columns], ignore_index=True)
        inter.insert(0, "Model", model)
        inter.to_csv(os.path.join(OUT, f"{_slug(model)}_e7_interaction.csv"), index=False)
        pe = pooled_effects(df)
        pe.insert(0, "Model", model)
        pe.to_csv(os.path.join(OUT, f"{_slug(model)}_e7_pooled_effects.csv"), index=False)
        all_equiv.append(eq); all_inter.append(inter); all_pooled.append(pe)
        bm = inter[inter["metric"] == "band_mas"]
        print(f"  interaction (band-MAS): {int(bm['admitted'].sum())} of {len(bm)} cells admitted, "
              f"{int((bm['admitted'] & bm['inside_margin_90']).sum())} inside the {MARGIN} margin")

        summary["models"][model] = {
            "n_confirmatory_tests": int(len(tc)), "m_family": m_fam, "decision_rule": rule,
            "n_claims": int(len(claims)),
            "claims_by_contrast": {k: int(v) for k, v in claims["contrast"].value_counts().items()},
            "n_exploratory_within_ocean": int(len(w[w["tier"] == "C"])),
            "equivalence_static_inside_delta": int(eq["inside_delta_90"].sum()) if len(eq) else 0,
            "equivalence_cells": int(len(eq)), "equivalence_degenerate": int(eq["degenerate"].sum()) if len(eq) else 0,
            "underpowered": bool(float(mdd.get(model, float("nan"))) > DELTA), "mdd_S60_band_mas": mdd.get(model),
            "interaction_admitted": int(bm["admitted"].sum()), "interaction_inside_margin": int((bm["admitted"] & bm["inside_margin_90"]).sum()),
            "pooled_memory_effect": {f"{r.Persona}|{r.Vocabulary}": float(r["estimate"]) for _, r in pe.iterrows()},
            "max_fallback_share": float(pre["max_fallback_share"].max()),
            "max_zero_trade_share": float(pre["zero_trade_share"].max()),
            "n_score_errors": int(pre["score_errors"].sum()), "pairing": pc,
        }

    equiv = pd.concat(all_equiv, ignore_index=True) if all_equiv else pd.DataFrame()
    inter = pd.concat(all_inter, ignore_index=True) if all_inter else pd.DataFrame()
    pooled = pd.concat(all_pooled, ignore_index=True) if all_pooled else pd.DataFrame()
    read = [m for m in models if "n_confirmatory_tests" in summary["models"].get(m, {})]
    if read:
        summary["predictions"] = write_predictions("E7", predictions(read, equiv, inter, pooled, salience), OUT)
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), indent=1)
    print(f"\nwritten -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
