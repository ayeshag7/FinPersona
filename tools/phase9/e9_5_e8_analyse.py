"""v2.1 Phase 9, stage 2, E8 -- the re-injection cadence (PREREG_PHASE_9_STAGE2_E8.md).

    python -u -m tools.phase9.e9_4_grid --stages score --only cadence_open        # on the cluster; pull per_run.csv
    python -u -m tools.phase9.e9_5_e8_steps --results results_v2/phase9          # on the cluster; the per-step reading
    python -u -m tools.phase9.e9_5_e8_analyse                                     # here

What this computes, and why it is its own script rather than a call into the shared machinery:

*   **The frame.** E8's four cadence arms (memory_k2, memory_k5, memory_k10, memory_k20) come from the E8 manifest;
    the k = 1 level is the headline's `memory` arm and the never level its `static` arm, on the same models, seeds and
    paths, so neither was re-run.  `frames` takes the headline rows from the two open-weight headline manifests at the
    default setting and the first 60 seeds, and refuses a frame in which any (model, persona, cell, seed, arm) key
    comes from two manifests: `seed_level_pairs` groups on those five columns and ignores `Manifest` and `Setting`,
    so E3's common-start `static` rows or E4's Track-A ones would otherwise be averaged into the headline's without
    a word.

*   **The confirmatory family.** Section 3 registers the four (k-arm - static) contrasts per cell and metric, 4 x 12 x
    3 = 144 per model, one family under `bh_within`.  `tools.stats_v2.question_families()` is a fixed dict that holds
    `memory - static` and nothing about a cadence arm, so the family is passed explicitly, as E3, E4 and E7 pass
    theirs (`test_e8_family_is_absent_from_the_shared_dict`).

*   **Retention.** The effect at cadence k relative to the every-day effect, per cell: r(k) = d(k) / d(1) with
    d = mean over seeds of the paired (arm - static) difference, read only on ADMITTED cells (|d(1)| >= 0.01, E2's
    floor: a cell whose every-day effect is below a fifth of Delta has no effect to retain).  Pooled per model as the
    ratio of signed sums over admitted cells, with a seed-cluster bootstrap interval (admission fixed at the point
    estimate).  Under a stateless agent a non-injected day's prompt is the static arm's, so with no carry-over through
    the portfolio state r(k) would be exactly the injected share 1 / k; the distance of r(k) above 1 / k is the
    carry-over, and that is what section 4's P3 reads.

*   **The per-step reading** (P4) needs the day-level series and is computed on the cluster by
    `e9_5_e8_steps.py`; without its file P4 is `unevaluated`, never passed.
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
from tools.stats_v2 import TIER_C, run_stats_v21, scenario_cell

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E94 = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e9_4")
OUT = os.path.join(E94, "stats_e8_cadence")
E8_MANIFEST = "e9_4_stage2_cadence"
HEADLINE_MANIFESTS = ("e9_4_stage1_headline_open", "e9_4_stage1_headline_open_b2")
SEEDS = frozenset(range(10001, 10061))          # stage 2's seeds: the first 60 of the headline's 122


def _cadence_levels() -> Dict[int, str]:
    from experiments.arms_v2 import CADENCE_LEVELS
    return dict(CADENCE_LEVELS)


K_ARMS = {k: a for k, a in _cadence_levels().items() if k != 1}      # {2: memory_k2, 5: ..., 10: ..., 20: ...}
ARM_OF_K = {1: "memory", **K_ARMS}
K_OF_ARM = {a: k for k, a in ARM_OF_K.items()}
ARMS_ALL = ("static",) + tuple(ARM_OF_K[k] for k in sorted(ARM_OF_K))
# Section 3's family: the four cadence arms against static, per cell and tier-C metric, 4 x 12 x 3 = 144, one key.
E8_FAMILY = {"E8": [(a, "static") for a in K_ARMS.values()]}
DELTA = 0.05                                    # D12's minimum effect on band-MAS
ADMIT = 0.01                                    # E2's floor on the every-day effect: a fifth of Delta
RETAIN_BAR = 0.5                                # P2's DESIGN bar: half the every-day effect at one injection in five
MIN_ADMITTED = 3                                # a model is readable when at least this many of its 12 cells are admitted
N_BOOT = 999
STEPS_FILE = os.path.join(OUT, "steps_summary.csv")


def _slug(model: str) -> str:
    return model.replace("/", "_").replace("|", "_").replace(".", "_")


def frames(per_run: pd.DataFrame, model: str):
    """E8's cadence rows beside the headline's static and memory rows for one model, or (None, reason)."""
    h = per_run[per_run["Manifest"].isin(HEADLINE_MANIFESTS) & (per_run["Model"] == model)
                & (per_run["Setting"].astype(str) == "default") & per_run["Seed"].isin(SEEDS)
                & per_run["Arm"].isin(("static", "memory"))].copy()
    e = per_run[(per_run["Manifest"] == E8_MANIFEST) & (per_run["Model"] == model)
                & per_run["Arm"].isin(K_ARMS.values())].copy()
    if h.empty or e.empty:
        return None, f"no rows (headline {len(h)}, cadence {len(e)})"
    return pd.concat([h, e], ignore_index=True), ""


def pairing_check(df: pd.DataFrame) -> dict:
    """Every (persona, cell, seed) key must carry all six arms, and no (key, arm) may come from two manifests."""
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    g = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed", "Arm"])["Manifest"].nunique()
    paired = d.groupby(["Model", "Persona", "Scenario_Cell", "Seed"])["Arm"].nunique()
    return {"keys_with_two_manifests": int((g > 1).sum()), "keys_with_six_arms": int((paired == len(ARMS_ALL)).sum()),
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


def _wide(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """(Persona, Scenario_Cell, Seed) x arm, the mean over replicates; rows with every arm present."""
    d = df.copy()
    d["Scenario_Cell"] = scenario_cell(d)
    w = d.groupby(["Persona", "Scenario_Cell", "Seed", "Arm"])[metric].mean().unstack("Arm")
    return w.dropna(subset=[a for a in ARMS_ALL if a in w.columns])


def cell_effects(df: pd.DataFrame, metric: str = "band_mas") -> pd.DataFrame:
    """Per cell: the every-day effect d(1) = memory - static and each cadence's d(k), paired on seed and averaged;
    admission (|d(1)| >= ADMIT); the retention r(k) = d(k) / d(1) on admitted cells."""
    w = _wide(df, metric)
    rows = []
    for (persona, cell), g in w.groupby(level=["Persona", "Scenario_Cell"]):
        d1 = float((g["memory"] - g["static"]).mean())
        row = {"Persona": persona, "Scenario_Cell": cell, "metric": metric, "n_seeds": int(len(g)), "d_1": d1,
               "admitted": bool(abs(d1) >= ADMIT)}
        for k, a in K_ARMS.items():
            dk = float((g[a] - g["static"]).mean())
            row[f"d_{k}"] = dk
            row[f"r_{k}"] = dk / d1 if row["admitted"] else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def _pooled(w: pd.DataFrame, admitted: pd.Series, weights: Optional[pd.Series] = None) -> Dict[int, float]:
    """r_pool(k) = sum_adm d_c(k) sign(d_c(1)) / sum_adm |d_c(1)| with cell means taken under `weights` (a seed's
    multiplicity in a bootstrap draw)."""
    g = w.copy()
    wt = pd.Series(1.0, index=g.index) if weights is None else g.index.get_level_values("Seed").map(weights).astype(float)
    g["_w"] = wt.values
    num, den = {k: 0.0 for k in K_ARMS}, 0.0
    for (persona, cell), h in g.groupby(level=["Persona", "Scenario_Cell"]):
        if not admitted.get((persona, cell), False) or h["_w"].sum() <= 0:
            continue
        ww = h["_w"].values
        d1 = float(np.average(h["memory"].values - h["static"].values, weights=ww))
        s = 1.0 if d1 >= 0 else -1.0
        den += abs(d1)
        for k, a in K_ARMS.items():
            num[k] += s * float(np.average(h[a].values - h["static"].values, weights=ww))
    return {k: (num[k] / den if den > 0 else float("nan")) for k in K_ARMS}


def pooled_retention(df: pd.DataFrame, metric: str = "band_mas", n_boot: int = N_BOOT, seed: int = 0) -> pd.DataFrame:
    """Per cadence: the pooled retention over admitted cells with a 95 % seed-cluster bootstrap interval (seeds
    resampled with replacement, jointly across cells, admission fixed at the point estimate), and the injected share
    1 / k beside it."""
    w = _wide(df, metric)
    ce = cell_effects(df, metric)
    admitted = ce.set_index(["Persona", "Scenario_Cell"])["admitted"]
    point = _pooled(w, admitted)
    seeds = np.array(sorted(w.index.get_level_values("Seed").unique()))
    rng = np.random.default_rng(seed)
    draws = {k: [] for k in K_ARMS}
    if len(seeds) >= 2 and admitted.any():
        for _ in range(n_boot):
            pick = rng.choice(seeds, size=len(seeds), replace=True)
            cnt = pd.Series(pick).value_counts()
            weights = pd.Series(0.0, index=seeds); weights.loc[cnt.index] = cnt.values.astype(float)
            r = _pooled(w, admitted, weights)
            for k in K_ARMS:
                draws[k].append(r[k])
    rows = []
    for k in sorted(K_ARMS):
        arr = np.array([x for x in draws[k] if np.isfinite(x)])
        rows.append({"k": k, "arm": K_ARMS[k], "metric": metric, "estimate": point[k], "share_1_over_k": 1.0 / k,
                     "ci_lo": float(np.percentile(arr, 2.5)) if len(arr) else float("nan"),
                     "ci_hi": float(np.percentile(arr, 97.5)) if len(arr) else float("nan"),
                     "n_boot": int(len(arr)), "n_admitted_cells": int(admitted.sum()), "n_cells": int(len(admitted)),
                     "n_seeds": int(len(seeds))})
    return pd.DataFrame(rows)


def read_steps() -> Optional[pd.DataFrame]:
    return pd.read_csv(STEPS_FILE) if os.path.exists(STEPS_FILE) else None


def predictions(models: List[str], ret: pd.DataFrame, cells: pd.DataFrame, steps: Optional[pd.DataFrame]) -> List[Prediction]:
    """Section 4's four, each evaluated on the artefacts this script wrote.  A model is READABLE when at least
    MIN_ADMITTED of its cells are admitted; with no readable model P1-P3 are degenerate, not held."""
    out = []
    bm = ret[ret["metric"] == "band_mas"] if len(ret) else ret
    readable = []
    for m in models:
        g = bm[bm["Model"] == m]
        if len(g) and int(g["n_admitted_cells"].iloc[0]) >= MIN_ADMITTED:
            readable.append(m)
    nr = len(readable)

    def r_of(m, k):
        g = bm[(bm["Model"] == m) & (bm["k"] == k)]
        return float(g["estimate"].iloc[0]) if len(g) else float("nan")

    # ---- P1: the dose-response is monotone, pooled r(2) > r(20) ----
    mono = [m for m in readable if np.isfinite(r_of(m, 2)) and np.isfinite(r_of(m, 20)) and r_of(m, 2) > r_of(m, 20)]
    out.append(Prediction("P1", "the effect falls as the cadence thins: the pooled retention at k = 2 exceeds that at k = 20",
                          "r(2) > r(20) in at least two thirds of the readable models (at least 3 of 12 cells admitted)",
                          DEGENERATE if nr == 0 else verdict_of(len(mono) * 3 >= 2 * nr),
                          f"r(2) > r(20) in {len(mono)} of {nr} readable models ({len(models)} in all)",
                          {"monotone": len(mono), "readable": nr, "models": len(models), "min_admitted": MIN_ADMITTED,
                           "by_model": {m: {"r2": r_of(m, 2), "r20": r_of(m, 20)} for m in readable}}))
    # ---- P2: one injection in five keeps at least half the every-day effect ----
    keep = [m for m in readable if np.isfinite(r_of(m, 5)) and r_of(m, 5) >= RETAIN_BAR]
    out.append(Prediction("P2", "a sparse cadence keeps most of the effect: the pooled retention at k = 5 is at least 0.5",
                          f"r(5) >= {RETAIN_BAR} (a DESIGN bar) in at least half of the readable models",
                          DEGENERATE if nr == 0 else verdict_of(len(keep) * 2 >= nr),
                          f"r(5) >= {RETAIN_BAR} in {len(keep)} of {nr} readable models",
                          {"keep": len(keep), "readable": nr, "bar": RETAIN_BAR, "by_model": {m: r_of(m, 5) for m in readable}}))
    # ---- P3: carry-over through the portfolio state: r(k) above the injected share 1 / k ----
    carry = [m for m in readable if all(np.isfinite(r_of(m, k)) and r_of(m, k) > 1.0 / k for k in (5, 10, 20))]
    out.append(Prediction("P3", "the injected decision persists through the portfolio state: the pooled retention "
                                "exceeds the injected share 1 / k at k = 5, 10 and 20",
                          "r(k) > 1 / k at all three sparse cadences in at least two thirds of the readable models; "
                          "r(k) = 1 / k is what a stateless agent with no carry-over gives exactly",
                          DEGENERATE if nr == 0 else verdict_of(len(carry) * 3 >= 2 * nr),
                          f"above 1 / k at k = 5, 10 and 20 in {len(carry)} of {nr} readable models",
                          {"carry": len(carry), "readable": nr,
                           "by_model": {m: {str(k): [r_of(m, k), 1.0 / k] for k in (5, 10, 20)} for m in readable}}))
    # ---- P4: the per-step ordering on non-injected days ----
    if steps is None or steps.empty:
        out.append(Prediction("P4", "on a non-injected day the cadence arm sits between the static arm and its own "
                                    "injected days in band distance",
                              "the signed ordering static >= non-injected >= injected holds in at least two thirds of "
                              "the admitted (model, cell, k) triples",
                              UNEVALUATED, "the per-step series are on the cluster: run e9_5_e8_steps.py and pull steps_summary.csv"))
    else:
        adm = cells[(cells["metric"] == "band_mas") & cells["admitted"]][["Model", "Persona", "Scenario_Cell", "d_1"]]
        s = steps.merge(adm, on=["Model", "Persona", "Scenario_Cell"], how="inner")
        s = s[s["arm"].isin(K_ARMS.values())].dropna(subset=["dist_injected", "dist_non_injected", "dist_static"])
        sign = np.sign(s["d_1"].values)
        # the every-day effect's sign is the direction the injected days move the distance from the static arm's
        # (d_1 < 0: memory LOWERS it); "between" is read in that direction: static, then non-injected, then injected
        between = ((sign * (s["dist_non_injected"].values - s["dist_static"].values) >= 0)
                   & (sign * (s["dist_non_injected"].values - s["dist_injected"].values) <= 0))
        n_ok, n = int(between.sum()), int(len(s))
        out.append(Prediction("P4", "on a non-injected day the cadence arm sits between the static arm and its own "
                                    "injected days in band distance",
                              "the signed ordering static >= non-injected >= injected holds in at least two thirds of "
                              "the admitted (model, cell, k) triples",
                              DEGENERATE if n == 0 else verdict_of(n_ok * 3 >= 2 * n),
                              f"between in {n_ok} of {n} admitted (model, cell, k) triples",
                              {"between": n_ok, "triples": n}))
    return out


def main() -> int:
    per_run = pd.read_csv(os.path.join(E94, "per_run.csv"))
    if E8_MANIFEST not in set(per_run["Manifest"]):
        raise SystemExit(f"{E8_MANIFEST} is not in per_run.csv -- score it first")
    if not set(HEADLINE_MANIFESTS) & set(per_run["Manifest"]):
        raise SystemExit("neither open-weight headline manifest is in per_run.csv -- E8's k = 1 and never levels are its rows")
    os.makedirs(OUT, exist_ok=True)
    models = sorted(per_run[per_run["Manifest"] == E8_MANIFEST]["Model"].unique())
    steps = read_steps()
    print(f"E8 models present: {len(models)}; per-step summary: {'present' if steps is not None else 'absent (P4 unevaluated)'}")
    summary = {"models": {}, "family": {k: [list(x) for x in v] for k, v in E8_FAMILY.items()},
               "constants": {"delta": DELTA, "admit": ADMIT, "retain_bar": RETAIN_BAR, "min_admitted": MIN_ADMITTED,
                             "n_boot": N_BOOT},
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    all_cells, all_ret = [], []
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
            print("  REFUSING: two manifests would be averaged silently")
            summary["models"][model] = {"skipped": "manifest collision on a (key, arm)"}
            continue
        pre = preconditions(df)
        pre.to_csv(os.path.join(OUT, f"{_slug(model)}_preconditions.csv"), index=False)
        print(f"  preconditions: worst fallback={pre['max_fallback_share'].max():.4%}; "
              f"zero-trade max={pre['zero_trade_share'].max():.2%}; score errors={int(pre['score_errors'].sum())}")
        res = run_stats_v21(df, os.path.join(OUT, _slug(model)), families=E8_FAMILY)
        t = res["contrasts"]
        tc = t[t["tier"] == "C"]
        rule = str(t["decision_rule"].iloc[0]) if len(t) else "none"
        m_fam = sorted(set(int(x) for x in tc["m_family"])) if len(tc) else []
        claims = tc[tc["claim"]]
        print(f"  confirmatory: {len(tc)} tests, m_family={m_fam}, rule={rule}; claims at q<=0.05: {len(claims)}")
        if rule != "bh_within" or m_fam != [144]:
            print(f"  WARNING: section 3 registers one family of 144 under bh_within; got {m_fam} under {rule}")
        ce = pd.concat([cell_effects(df, met) for met in TIER_C if met in df.columns], ignore_index=True)
        ce.insert(0, "Model", model)
        ce.to_csv(os.path.join(OUT, f"{_slug(model)}_e8_cell_effects.csv"), index=False)
        ret = pd.concat([pooled_retention(df, met) for met in TIER_C if met in df.columns], ignore_index=True)
        ret.insert(0, "Model", model)
        ret.to_csv(os.path.join(OUT, f"{_slug(model)}_e8_retention.csv"), index=False)
        all_cells.append(ce); all_ret.append(ret)
        bm = ret[ret["metric"] == "band_mas"].set_index("k")
        adm = int(bm["n_admitted_cells"].iloc[0]) if len(bm) else 0
        print(f"  retention (band-MAS, {adm} of 12 cells admitted): " +
              ", ".join(f"r({k})={bm.loc[k, 'estimate']:+.3f} [{bm.loc[k, 'ci_lo']:+.3f}, {bm.loc[k, 'ci_hi']:+.3f}]" for k in bm.index))
        summary["models"][model] = {
            "n_confirmatory_tests": int(len(tc)), "m_family": m_fam, "decision_rule": rule, "n_claims": int(len(claims)),
            "claims_by_contrast": {k: int(v) for k, v in claims["contrast"].value_counts().items()},
            "admitted_cells_band_mas": adm,
            "retention_band_mas": {str(k): {"estimate": float(bm.loc[k, "estimate"]), "ci_lo": float(bm.loc[k, "ci_lo"]),
                                            "ci_hi": float(bm.loc[k, "ci_hi"]), "share": float(bm.loc[k, "share_1_over_k"])}
                                   for k in bm.index},
            "preconditions": {"max_fallback_share": float(pre["max_fallback_share"].max()),
                              "max_zero_trade_share": float(pre["zero_trade_share"].max()),
                              "score_errors": int(pre["score_errors"].sum())}}
    cells = pd.concat(all_cells, ignore_index=True) if all_cells else pd.DataFrame(columns=["Model", "metric", "admitted"])
    ret = pd.concat(all_ret, ignore_index=True) if all_ret else pd.DataFrame(columns=["Model", "metric", "k"])
    cells.to_csv(os.path.join(OUT, "cell_effects.csv"), index=False)
    ret.to_csv(os.path.join(OUT, "retention.csv"), index=False)
    preds = predictions([m for m in models if "skipped" not in summary["models"].get(m, {})], ret, cells, steps)
    write_predictions("E8", preds, OUT)
    summary["predictions"] = [{"id": p.pid, "verdict": p.verdict, "evidence": p.evidence} for p in preds]
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), indent=1)
    print("\npredictions:")
    for p in preds:
        print(f"  {p.pid}: {p.verdict:11s} {p.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
