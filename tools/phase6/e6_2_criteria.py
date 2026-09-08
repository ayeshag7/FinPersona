"""
v2.1 Phase 6 -- E6.2: the re-derived checklist criteria (REG-14 B and C), their size and power on known-answer
panels (REG-14 experiment (i)), and the concordance with the v2 criteria (REG-14 A), item by item.

Plan Section 10.2 (E6.2), 10.3 (criteria FIT from E6.1, written down before the runs, none moved after).

The three criterion forms, as REG-14 states them:
  A  the v2 numeric thresholds -- `evaluation.stylized_facts`' pass rules, read from the stored checklist
  B  KS-equivalence: the bootstrap 95 % upper limit of the two-sample KS distance between the generator's
     cross-seed distribution of the statistic and the real 200-day-window distribution is below D0 = 0.10
     ("the KS test did not reject" is NOT a criterion: at these sizes it rejects D = 0.10 with 97 % power)
  C  the P10-P90 band of the real windows with a share criterion: the generator's share inside the band
     >= 0.80 - the sampling half-width of a share at n_gen (1.96 sqrt(0.8 * 0.2 / n_gen))

Like for like.  The generator's per-path statistics are computed by `tools.phase6.e6_1_reference.window_stats`
-- the SAME function, on the SAME 200-day horizon, that produced the real reference -- on (P, volume) exactly as
on a real (Adj Close, Volume) window.  E6.9 measured the estimators' T = 200 biases (Hill at a 5 % depth, the
sample kurtosis of a heavy tail, the ACF of a persistent process); a like-for-like comparison is immune to them
because both samples carry the same bias, while an absolute band (A) is not.

Populations.  The pooled generator population is the checklist's (every scenario); E6.4 asks for the same items
on flat paths and per scenario with the regime-switching contribution quantified, so every criterion is
evaluated on: all paths, flat only, and each scenario.  For the crash-only items (8, 20) the reference is
reported twice: every real window, and the real windows that contain a crash by a stated rule (MDD <= -0.20 --
a DESIGN definition, recorded as such; survivorship understates their frequency and depth, REG-15).

Size and power (REG-14 (i)).  For every statistic and n_gen: the pass rate of B and of C when the generator
sample is a resample of the real windows (true D = 0: the criterion's SIZE), and when it is the real sample
shifted so that its true KS distance from the reference is 0.05 and 0.10 (POWER against the equivalence margin).

Outputs: <out>/criteria.{json,md}, <out>/generator_windows.csv (cached per-path statistics), and -- with
--write-criteria -- evaluation/params/phase6_criteria.json, the criteria file the tests read back.

Usage:
    python -u tools/phase6/e6_2_criteria.py --panel docs/env_v2/generated/v2_1/_panels/sep_phase5_after.pkl \
        --reference docs/env_v2/generated/v2_1/e6_1 --out docs/env_v2/generated/v2_1/e6_2 [--write-criteria]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase6.e6_1_reference import window_stats, T_WINDOW  # noqa: E402

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT_DEFAULT = os.path.join(GEN, "e6_2")
REF_DEFAULT = os.path.join(GEN, "e6_1")
PANEL_DEFAULT = os.path.join(GEN, "_panels", "sep_phase5_after.pkl")
CRITERIA_FILE = os.path.join(ROOT, "evaluation", "params", "phase6_criteria.json")
D0 = 0.10
SHARE_P0 = 0.80
N_BOOT = 500
N_SIZE = 100          # size/power simulations per (statistic, n_gen, D); the inner KS bootstrap is 50 per simulation
N_BOOT_INNER = 50
SEED = 620001
CRASH_MDD = -0.20    # DESIGN: a real window "contains a crash" when its MDD is at or below this

# item -> the statistics with a real-window counterpart; the generator population each is judged on; the reference
ITEMS: Dict[int, Dict] = {
    1:  {"stats": ["lb_p_r", "abs_acf1_r"], "pop": "all", "property": "No linear autocorrelation of returns"},
    2:  {"stats": ["kurtosis", "hill", "jb_p"], "pop": "all", "property": "Heavy tails"},
    3:  {"stats": ["lb_p_absr", "lb_p_r2", "arch_lm_p", "acf1_absr"], "pop": "all", "property": "Volatility clustering"},
    4:  {"stats": ["acf1_absr", "acf5_absr", "acf10_absr", "acf20_absr", "acf50_absr"], "pop": "all", "property": "Decay of ACF|r| (descriptive)"},
    5:  {"stats": ["garch_persistence", "garch_alpha", "garch_beta"], "pop": "all", "property": "GARCH persistence"},
    6:  {"stats": ["leverage_corr", "gjr_gamma"], "pop": "all", "property": "Leverage effect"},
    7:  {"stats": ["volume_absr_spearman", "logvolume_acf1", "logvolume_shapiro_p"], "pop": "all", "property": "Volume-volatility"},
    8:  {"stats": ["skew", "worst_over_best"], "pop": "crash", "property": "Gain/loss asymmetry in crash", "reference": "crash"},
    20: {"stats": ["mdd", "worst_day", "daily_sigma"], "pop": "crash", "property": "Magnitudes", "reference": "crash",
         "per_stat_pop": {"daily_sigma": "flat"}, "per_stat_reference": {"daily_sigma": "all"}},
}
POPS = ["all", "flat", "crash", "bull_trap", "sustained_bull"]


# --------------------------------------------------------------------------------------- generator side
def _gen_one(args):
    key, P, vol = args
    try:
        s = window_stats(P, vol)
    except Exception as e:
        s = {"error": type(e).__name__}
    s["scenario"], s["seed"] = key
    return s


def generator_windows(panel_path: str, cache: str, n_jobs: int) -> pd.DataFrame:
    if os.path.exists(cache) and os.path.getsize(cache) > 0:
        df = pd.read_csv(cache)
        if len(df):
            print(f"generator windows: cached ({len(df)} paths)", flush=True)
            return df
    panel = pd.read_pickle(panel_path)
    jobs = []
    for (sc, sd), g in panel.groupby(["scenario", "seed"], sort=False):
        g = g.sort_values("day")
        P = g["P"].to_numpy(float); v = g["volume"].to_numpy(float)
        # window_stats expects T_WINDOW + 1 prices (len(r) == T_WINDOW); a 200-day path has 200 prices -> 199 returns.
        # The first price is repeated so that the return vector has T_WINDOW entries with a leading zero -- NO: that
        # would inject a zero return.  Instead the path's 199 returns are used as they are; the one-day difference is
        # recorded in the output (`n_returns`) and is immaterial to every statistic here.
        jobs.append(((sc, sd), P, v))
    from joblib import Parallel, delayed
    from threadpoolctl import threadpool_limits
    t0 = time.time()
    with threadpool_limits(limits=2):
        rows = Parallel(n_jobs=n_jobs, backend="loky", verbose=5)(delayed(_gen_one)(j) for j in jobs)
    df = pd.DataFrame(rows)
    df["n_returns"] = T_WINDOW - 1
    df.to_csv(cache, index=False)
    print(f"generator windows: {len(df)} paths in {time.time() - t0:.0f}s", flush=True)
    return df


# --------------------------------------------------------------------------------------- criteria
def ks_distance(a: np.ndarray, b: np.ndarray) -> float:
    a = np.sort(a); b = np.sort(b)
    allv = np.concatenate([a, b])
    return float(np.max(np.abs(np.searchsorted(a, allv, "right") / len(a) - np.searchsorted(b, allv, "right") / len(b))))


def criterion_B(gen: np.ndarray, ref: np.ndarray, rng: np.random.Generator, n_boot: int = N_BOOT) -> Dict:
    d = ks_distance(gen, ref)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        draws[i] = ks_distance(rng.choice(gen, len(gen)), rng.choice(ref, len(ref)))
    up = float(np.percentile(draws, 95))
    return {"D": d, "D_upper95": up, "D0": D0, "pass": bool(up < D0), "n_gen": int(len(gen)), "n_ref": int(len(ref))}


def criterion_C(gen: np.ndarray, ref: np.ndarray) -> Dict:
    p10, p90 = float(np.percentile(ref, 10)), float(np.percentile(ref, 90))
    share = float(np.mean((gen >= p10) & (gen <= p90)))
    hw = 1.96 * math.sqrt(SHARE_P0 * (1 - SHARE_P0) / len(gen))
    thr = SHARE_P0 - hw
    return {"p10": p10, "p90": p90, "share_inside": share, "threshold": thr, "halfwidth": hw,
            "pass": bool(share >= thr), "n_gen": int(len(gen)), "n_ref": int(len(ref))}


def shifted_for_D(ref: np.ndarray, target_D: float, rng: np.random.Generator) -> np.ndarray:
    """A location shift of the reference sample whose two-sample KS distance from the reference is target_D
    (bisection on the shift, in units of the reference's IQR)."""
    iqr = float(np.subtract(*np.percentile(ref, [75, 25]))) or float(np.std(ref)) or 1.0
    lo, hi = 0.0, 5.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        d = ks_distance(ref + mid * iqr, ref)
        if d < target_D:
            lo = mid
        else:
            hi = mid
    return ref + hi * iqr


def size_power(ref: np.ndarray, n_gen: int, rng: np.random.Generator, n_sim: int = N_SIZE, n_boot: int = N_BOOT_INNER) -> Dict:
    """Pass rates of B and C when the generator sample is drawn from the reference (D = 0) and from the reference
    shifted to D = 0.05 and D = 0.10.  The bootstrap inside B uses n_boot resamples per simulation (50 here for
    tractability; the published criterion uses 500 -- the 95th percentile's resolution is stated), and the pass
    rates are over n_sim simulations, so a rate carries a binomial half-width of about 1.96 sqrt(p(1-p)/n_sim)."""
    out = {"n_gen": n_gen, "n_sim": n_sim, "n_boot_inner": n_boot}
    for label, sample in (("D0.00", ref), ("D0.05", shifted_for_D(ref, 0.05, rng)), ("D0.10", shifted_for_D(ref, 0.10, rng))):
        pb = pc = 0
        for _ in range(n_sim):
            g = rng.choice(sample, n_gen)
            pb += criterion_B(g, ref, rng, n_boot)["pass"]
            pc += criterion_C(g, ref)["pass"]
        out[label] = {"pass_rate_B": pb / n_sim, "pass_rate_C": pc / n_sim}
    return out


def evaluate(gen_df: pd.DataFrame, ref_df: pd.DataFrame, rng: np.random.Generator, with_power: bool, n_gens) -> List[Dict]:
    rows = []
    ref_all = ref_df
    ref_crash = ref_df[pd.to_numeric(ref_df["mdd"], errors="coerce") <= CRASH_MDD]
    sub_periods = sorted(ref_df["sub_period"].dropna().unique())
    for item, spec in ITEMS.items():
        for st in spec["stats"]:
            if st not in ref_df.columns or st not in gen_df.columns:
                continue
            ref_kind = spec.get("per_stat_reference", {}).get(st, spec.get("reference", "all"))
            ref_v = pd.to_numeric((ref_crash if ref_kind == "crash" else ref_all)[st], errors="coerce").to_numpy(float)
            ref_v = ref_v[np.isfinite(ref_v)]
            main_pop = spec.get("per_stat_pop", {}).get(st, spec["pop"])
            for pop in POPS:
                g = gen_df if pop == "all" else gen_df[gen_df["scenario"] == pop]
                gv = pd.to_numeric(g[st], errors="coerce").to_numpy(float)
                gv = gv[np.isfinite(gv)]
                if len(gv) < 20 or len(ref_v) < 20:
                    continue
                row = {"item": item, "property": spec["property"], "statistic": st, "population": pop,
                       "is_main_population": pop == main_pop, "reference": ref_kind,
                       "n_gen": int(len(gv)), "n_ref": int(len(ref_v)),
                       "gen_p10": float(np.percentile(gv, 10)), "gen_p50": float(np.percentile(gv, 50)), "gen_p90": float(np.percentile(gv, 90)),
                       "ref_p10": float(np.percentile(ref_v, 10)), "ref_p50": float(np.percentile(ref_v, 50)), "ref_p90": float(np.percentile(ref_v, 90)),
                       "B": criterion_B(gv, ref_v, rng), "C": criterion_C(gv, ref_v)}
                # the same C share against each sub-period's band (survivorship and regime dependence are visible here)
                row["C_by_sub_period"] = {}
                for spn in sub_periods:
                    rv = pd.to_numeric((ref_crash if ref_kind == "crash" else ref_all)
                                       .loc[lambda d: d["sub_period"] == spn, st], errors="coerce").to_numpy(float)
                    rv = rv[np.isfinite(rv)]
                    if len(rv) >= 20:
                        c = criterion_C(gv, rv); row["C_by_sub_period"][spn] = {"share_inside": c["share_inside"], "pass": c["pass"], "n_ref": c["n_ref"]}
                rows.append(row)
            if with_power:
                sp = {}
                for n_gen in n_gens:
                    sp[str(n_gen)] = size_power(ref_v, n_gen, rng)
                rows.append({"item": item, "statistic": st, "population": "size_power", "reference": ref_kind, "size_power": sp})
    return rows


def v2_verdicts(checklist_csv: str) -> Dict[int, Dict]:
    if not os.path.exists(checklist_csv):
        return {}
    d = pd.read_csv(checklist_csv)
    out = {}
    for _, r in d.iterrows():
        out[int(r["item"])] = {"pass": (None if pd.isna(r["pass"]) else str(r["pass"]) == "True"),
                               "statistic": r["statistic"], "criterion": r["criterion"], "n_seeds": int(r["n_seeds"])}
    return out


# --------------------------------------------------------------------------------------- criteria file
def write_criteria_file(ref_df: pd.DataFrame, ref_meta: Dict, rows: List[Dict], out_path: str):
    """The criteria in force: reference percentiles with their n (overall and per sub-period), D0, the share rule,
    the crash-window definition, survivorship, provenance.  A loud loader (evaluation/criteria.py) reads it."""
    stats_used = sorted({r["statistic"] for r in rows if "B" in r})
    ref_crash = ref_df[pd.to_numeric(ref_df["mdd"], errors="coerce") <= CRASH_MDD]
    def pct(df, st):
        v = pd.to_numeric(df[st], errors="coerce").to_numpy(float); v = v[np.isfinite(v)]
        return {"n": int(v.size), "p10": float(np.percentile(v, 10)), "p50": float(np.percentile(v, 50)),
                "p90": float(np.percentile(v, 90))} if v.size else {"n": 0}
    ref_block = {}
    for st in stats_used:
        blk = {"all": pct(ref_df, st), "crash_windows": pct(ref_crash, st), "by_sub_period": {}}
        for spn, g in ref_df.groupby("sub_period"):
            blk["by_sub_period"][spn] = pct(g, st)
        ref_block[st] = blk
    doc = {
        "_note": "v2.1 Phase 6 checklist criteria (REG-14 B and C), FIT from E6.1's real 200-day windows and written before "
                 "the final checklist run. Nothing here is moved after a result is seen; a criterion found wrong goes in "
                 "PREREG_PHASE_6_ADDENDUM.md and results are reported under both.",
        "_status_key": {"FIT": "derived from data by a stated rule", "DESIGN": "a stated choice with its reason",
                        "LIT": "a literature value"},
        "criterion_B": {"value": {"D0": D0, "bootstrap_resamples": N_BOOT, "rule": "bootstrap 95 % upper limit of the two-sample KS distance < D0"},
                        "status": "DESIGN", "label": "REG-14 B (the corrected equivalence form; LOG section 3)",
                        "source": "V2_1_ALTERNATIVES_REGISTER.md section 14; V2_1_IMPROVEMENT_PLAN.md Appendix A", "date": "2026-09-08",
                        "interval": "none (a rule)", "n": {"windows": int(len(ref_df))}},
        "criterion_C": {"value": {"p0": SHARE_P0, "band": "P10-P90 of the real windows", "rule": "share inside >= p0 - 1.96*sqrt(p0(1-p0)/n_gen)"},
                        "status": "DESIGN", "label": "REG-14 C", "source": "V2_1_ALTERNATIVES_REGISTER.md section 14", "date": "2026-09-08",
                        "interval": "none (a rule)", "n": {"windows": int(len(ref_df))}},
        "crash_window_rule": {"value": {"mdd_at_or_below": CRASH_MDD}, "status": "DESIGN",
                              "label": "a real window 'contains a crash' when its MDD is at or below this; the reference for items 8 and 20's crash statistics",
                              "source": "PREREG_PHASE_6.md", "date": "2026-09-08", "interval": "none (a definition)",
                              "n": {"crash_windows": int(len(ref_crash))}},
        "reference": {"value": ref_block, "status": "FIT",
                      "label": "P10/P50/P90 of every checklist statistic over the non-overlapping 200-day windows of analysis set A, "
                               "overall, on the crash windows and per sub-period, each with its n",
                      "source": "docs/env_v2/generated/v2_1/e6_1/reference.json; tools/phase6/e6_1_reference.py",
                      "date": ref_meta.get("generated_utc", "")[:10], "interval": "the P10-P90 band is the interval",
                      "n": {"names": ref_meta.get("n_names"), "windows": ref_meta.get("n_windows"),
                            "sub_periods": ref_meta.get("sub_periods")},
                      "survivorship": ref_meta.get("survivorship")},
        "items": {str(k): {"statistics": v["stats"], "population": v["pop"], "reference": v.get("reference", "all"),
                           "property": v["property"]} for k, v in ITEMS.items()},
        "not_in_reference": ref_meta.get("not_in_reference"),
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    print(f"criteria file written: {os.path.relpath(out_path, ROOT)}")


# --------------------------------------------------------------------------------------- markdown
def to_markdown(rows: List[Dict], v2: Dict[int, Dict], meta: Dict) -> str:
    L = [f"# E6.2 — re-derived checklist criteria (REG-14 B and C) on the generator, beside the v2 criteria (A)", "",
         f"Generator: `{meta['panel']}` ({meta['n_gen_paths']} paths; per-path statistics by `e6_1_reference.window_stats`, the "
         f"reference's own function). Reference: `{meta['reference']}` ({meta['n_ref_windows']} windows of {meta['n_ref_names']} names; "
         f"crash windows = MDD ≤ {CRASH_MDD}: n = {meta['n_ref_crash']}). B: bootstrap 95 % upper limit of KS D < {D0} "
         f"({N_BOOT} resamples). C: share inside the reference P10–P90 ≥ {SHARE_P0} − 1.96·sqrt({SHARE_P0}·{1-SHARE_P0:.1f}/n_gen).", "",
         "## Verdicts on the checklist's population, with the v2 criterion beside", "",
         "| item | statistic | pop | ref | n_gen / n_ref | gen P10 / P50 / P90 | ref P10 / P50 / P90 | B: D (upper) | B | C: share (thr) | C | A (v2) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    def f3(x): return f"{x:.3g}"
    for r in rows:
        if "B" not in r or not r["is_main_population"]:
            continue
        a = v2.get(r["item"], {}).get("pass")
        L.append(f"| {r['item']} | `{r['statistic']}` | {r['population']} | {r['reference']} | {r['n_gen']} / {r['n_ref']} | "
                 f"{f3(r['gen_p10'])} / {f3(r['gen_p50'])} / {f3(r['gen_p90'])} | {f3(r['ref_p10'])} / {f3(r['ref_p50'])} / {f3(r['ref_p90'])} | "
                 f"{r['B']['D']:.3f} ({r['B']['D_upper95']:.3f}) | {'**PASS**' if r['B']['pass'] else '**FAIL**'} | "
                 f"{r['C']['share_inside']:.3f} ({r['C']['threshold']:.3f}) | {'**PASS**' if r['C']['pass'] else '**FAIL**'} | "
                 f"{'PASS' if a else ('FAIL' if a is False else 'n/a')} |")
    L += ["", "## Per-scenario and flat-only (E6.4): criterion C's share inside the reference band", "",
          "| item | statistic | " + " | ".join(POPS) + " |", "|---|---|" + "---|" * len(POPS)]
    by = {}
    for r in rows:
        if "C" in r:
            by.setdefault((r["item"], r["statistic"]), {})[r["population"]] = r
    for (it, st), d in sorted(by.items()):
        cells = []
        for p in POPS:
            rr = d.get(p)
            cells.append("—" if rr is None else f"{rr['C']['share_inside']:.2f} {'✓' if rr['C']['pass'] else '✗'} (D {rr['B']['D']:.2f})")
        L.append(f"| {it} | `{st}` | " + " | ".join(cells) + " |")
    L += ["", "## Size and power of B and C on known-answer panels (REG-14 (i))", "",
          "Pass rates when the generator sample is a resample of the reference (true D = 0; the criterion's size is 1 − this) and "
          "when it is the reference shifted to a true KS distance of 0.05 and 0.10 (power against the equivalence margin is 1 − the pass rate at 0.10).", "",
          "| item | statistic | n_gen | pass rate at D = 0 (B / C) | at D = 0.05 (B / C) | at D = 0.10 (B / C) |", "|---|---|---|---|---|---|"]
    for r in rows:
        if r.get("population") == "size_power":
            for n_gen, sp in r["size_power"].items():
                L.append(f"| {r['item']} | `{r['statistic']}` | {n_gen} | {sp['D0.00']['pass_rate_B']:.2f} / {sp['D0.00']['pass_rate_C']:.2f} | "
                         f"{sp['D0.05']['pass_rate_B']:.2f} / {sp['D0.05']['pass_rate_C']:.2f} | {sp['D0.10']['pass_rate_B']:.2f} / {sp['D0.10']['pass_rate_C']:.2f} |")
    L += ["", "## Concordance (REG-14): where A and B/C agree the item is reported once; where they disagree, under both with the reason", "",
          "| item | A (v2) | B | C | reading |", "|---|---|---|---|---|"]
    per_item = {}
    for r in rows:
        if "B" in r and r["is_main_population"]:
            per_item.setdefault(r["item"], []).append(r)
    for it, rs in sorted(per_item.items()):
        a = v2.get(it, {}).get("pass")
        b = all(r["B"]["pass"] for r in rs); c = all(r["C"]["pass"] for r in rs)
        if a is None:
            reading = "no v2 verdict on this population"
        elif a == b == c:
            reading = "concordant"
        elif (not a) and (b or c):
            reading = "A fails, the like-for-like criterion passes: the v2 band is mis-specified for a 200-day window (E6.9's bias) or was stated for a different design"
        elif a and not (b or c):
            reading = "A passes, the like-for-like criterion fails: the v2 band admits a distribution the real windows do not show"
        else:
            reading = "B and C disagree: the KS distance and the band share measure different departures (a shape difference inside the band, or a tail outside it)"
        L.append(f"| {it} | {'PASS' if a else ('FAIL' if a is False else 'n/a')} | {'PASS' if b else 'FAIL'} | {'PASS' if c else 'FAIL'} | {reading} |")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default=PANEL_DEFAULT)
    ap.add_argument("--reference", default=REF_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--checklist-csv", default=os.path.join(GEN, "e5_after_checklist.csv"))
    ap.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    ap.add_argument("--no-power", action="store_true")
    ap.add_argument("--n-gens", default="200,800")
    ap.add_argument("--write-criteria", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    ref_df = pd.read_csv(os.path.join(a.reference, "windows.csv"))
    with open(os.path.join(a.reference, "reference.json"), "r", encoding="utf-8") as fh:
        ref_meta = json.load(fh)["meta"]
    gen_df = generator_windows(a.panel, os.path.join(a.out, "generator_windows.csv"), a.n_jobs)
    rng = np.random.default_rng(SEED)
    rows = evaluate(gen_df, ref_df, rng, not a.no_power, [int(x) for x in a.n_gens.split(",")])
    v2 = v2_verdicts(a.checklist_csv)
    meta = {"panel": os.path.relpath(a.panel, ROOT).replace("\\", "/"), "n_gen_paths": int(len(gen_df)),
            "reference": os.path.relpath(a.reference, ROOT).replace("\\", "/"), "n_ref_windows": int(len(ref_df)),
            "n_ref_names": int(ref_df["ticker"].nunique()),
            "n_ref_crash": int((pd.to_numeric(ref_df["mdd"], errors="coerce") <= CRASH_MDD).sum()),
            "D0": D0, "share_p0": SHARE_P0, "n_boot": N_BOOT, "seed": SEED, "crash_mdd_rule": CRASH_MDD,
            "v2_checklist": os.path.relpath(a.checklist_csv, ROOT).replace("\\", "/") if v2 else None,
            "seconds": round(time.time() - t0, 1), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(os.path.join(a.out, "criteria.json"), "w", encoding="utf-8") as fh:
        json.dump({"meta": meta, "rows": rows, "v2_verdicts": {str(k): v for k, v in v2.items()}}, fh, indent=1, default=float)
    with open(os.path.join(a.out, "criteria.md"), "w", encoding="utf-8") as fh:
        fh.write(to_markdown(rows, v2, meta))
    if a.write_criteria:
        write_criteria_file(ref_df, ref_meta, rows, CRITERIA_FILE)
    print(json.dumps({k: meta[k] for k in ("n_gen_paths", "n_ref_windows", "n_ref_crash", "seconds")}))
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
