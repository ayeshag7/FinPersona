"""
v2.1 Phase 9 -- E9.1: the parameter list by REG-16 (i)'s pre-registered ranking rule, computed offline before any
LLM run (PREREG_PHASE_9.md 1).

    python -u -m tools.phase9.e9_1_ranking --stages candidates,calibrate,reference,panels,rank --workers 6

`candidates`  the candidate table read from the parameter files (value, interval, levels, override) and checked
              against the pre-registration's table; refuses on a mismatch.
`calibrate`   the half-life levels' matched sd(x): `tools.phase2.e2_6_sweep.calibrate` (T = 5,000 flat paths, jumps and
              rejection off, 20 paths, sbar scaled then confirmed), target = the default engine's stationary sd(x).
`reference`   the default panel, then the two reference rows (PREREG 1.3): L5_full_level_free's flat MCR at theta 0.05
              = 0.0770 to four decimals, and the L5 policies against e6_16a/runs.csv row by row (worst <= 1e-12).
              Nothing else runs if either fails.
`panels`      one panel per non-default level: seeds 0-99 x 4 scenarios x 3 personas, the pickled Phase-6 oracles,
              E7.8's scripted families keyed on zlib.crc32; per (level, scenario, seed, persona, policy) the MCR at both
              co-primary theta and band-MAS, by `evaluation.scoring.regret_terms_batch`; sd(x) and sd(r) per path.
`rank`        E(level, outcome) = mean over the 12 cells of |mean paired seed difference| / sd over seeds at the
              default; E(j, k) = max over j's levels; oracle = mean of O1 and O2; scripted = O3; ranks, rank-sum,
              the data-driven six, the five-of-six rule; a 1,000-resample seed bootstrap of every E and of the
              top-six membership, reported beside.

Outputs: docs/env_v2/generated/v2_1/e9_1/{candidates.json, calibration.json, reference.json, panel_<level>.parquet,
effects.csv, ranking.json, ranking.md}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e9_1")
PARAMS = os.path.join(ROOT, "envs", "v2", "params")
E6_16A = os.path.join(GEN, "e6_16a")
SCENARIOS = ("flat", "bull_trap", "crash", "sustained_bull")
PERSONAS = ("ISFJ", "INTJ", "ENTJ")
SEEDS = tuple(range(0, 100))                     # e7_panel's scored seeds
T = 200
COST_BP = 5.0
THETAS = (0.05, 0.002)                           # co-primary (P7-4); read back from scoring.json in `rank`
N_BOOT = 1000
TARGET_SEEDS_SDX = tuple(range(133900, 133920))  # the default engine's stationary sd(x) (PREREG 1.3)
PLAN_SIX = ("sigma_V", "half_life", "garch_set", "pe_dispersion", "analyst_sd", "sentiment_loading")
# the pre-registration's table (PREREG_PHASE_9.md 1.1): the in-force values it states, checked against the files
PREREG_IN_FORCE = {"sigma_V": 0.014573, "half_life": 22.38, "analyst_sd": 0.564, "mu_V": 2.281e-4, "jump_rate": 5.83e-4,
                   "jump_sd": 0.2303, "sbar": 0.015088, "blowoff_g": 0.00984, "s_eps": 0.1707, "p_loss": 0.0975,
                   "pe_cap": 191.5, "div_c_speed": 0.697, "div_tau": 0.406, "sent_rho": 0.211, "sent_b1": 0.111,
                   "vol_rho_v": 0.526, "vol_beta_absr": 0.203, "vol_sd_e": 0.347}


def _j(name):
    return json.load(open(os.path.join(PARAMS, name), encoding="utf-8"))


def _rel_ok(a, b, decimals_of_b) -> bool:
    return abs(a - b) <= 0.5 * 10 ** (-decimals_of_b) + 1e-15


def _decimals(v: float) -> int:
    s = f"{v:.10g}"
    if "e" in s:
        mant, exp = s.split("e")
        d = len(mant.split(".")[1]) if "." in mant else 0
        return d - int(exp)
    return len(s.split(".")[1]) if "." in s else 0


# ============================================================================================ candidates
def candidate_table() -> List[dict]:
    val, mp, vol, ev, ob = _j("value.json"), _j("mispricing.json"), _j("volatility.json"), _j("events.json"), _j("observables.json")
    rows = []

    def add(name, plan, value, low, high, itype, source, cfg_low, cfg_high, level_names=("low", "high")):
        rows.append({"candidate": name, "plan_six": plan, "in_force": value, "levels": {level_names[0]: low, level_names[1]: high},
                     "interval_type": itype, "source": source,
                     "config": {level_names[0]: cfg_low, level_names[1]: cfg_high}})

    sv = val["sigma_V"]
    add("sigma_V", True, sv["value"], sv["interval"][0], sv["interval"][1], "30-refit CI95", "value.json sigma_V",
        {"sigma_V": sv["interval"][0]}, {"sigma_V": sv["interval"][1]})
    hl = mp["half_life"]
    add("half_life", True, hl["value"], hl["interval"][0], hl["interval"][1], "30-refit CI95, matched sd(x)",
        "mispricing.json half_life", {"half_life": hl["interval"][0]}, {"half_life": hl["interval"][1]})   # engine + sbar at `calibrate`
    sets = vol["shape_sensitivity_sets"]["value"]
    gs = lambda q: {"garch": {"alpha": sets[q]["alpha"], "gamma": sets[q]["gamma"], "beta": sets[q]["beta"], "df": sets[q]["nu"]}}  # noqa: E731
    add("garch_set", True, vol["garch_shape"]["value"], "P25", "P75", "per-stock quartile sets",
        "volatility.json shape_sensitivity_sets", gs("P25"), gs("P75"))
    add("pe_dispersion", True, ob["multiple"]["value"]["width"], "P25-P75", "P5-P95", "stored grids", "observables.json multiple",
        {"obs_overrides": {"multiple": {"width": "P25-P75"}}}, {"obs_overrides": {"multiple": {"width": "P5-P95"}}})
    an = ob["analyst"]
    lo, hi = an["interval"]["lit_bracket_phase9"]
    add("analyst_sd", True, an["value"]["sd"], lo, hi, "recorded LIT bracket", "observables.json analyst",
        {"obs_overrides": {"analyst": {"sd": lo}}}, {"obs_overrides": {"analyst": {"sd": hi}}})
    se = ob["sentiment"]["value"]
    cf = se["c_val_full"]
    add("sentiment_loading", True, 0.0 if se["design"] == "A" else se["c_val"], 0.5 * cf, cf, "plan's levels on the stored FIT",
        "observables.json sentiment", {"obs_overrides": {"sentiment": {"design": "B", "c_val": 0.5 * cf}}},
        {"obs_overrides": {"sentiment": {"design": "B", "c_val": cf}}}, level_names=("half", "full"))
    mu = val["mu_V"]
    add("mu_V", False, mu["value"], mu["interval"][0], mu["interval"][1], "CI", "value.json mu_V",
        {"mu_V": mu["interval"][0]}, {"mu_V": mu["interval"][1]})
    ju = val["jump"]
    add("jump_rate", False, ju["value"]["jump_rate_x"], ju["interval"]["lam"][0], ju["interval"]["lam"][1], "CI", "value.json jump",
        {"jump_rate": ju["interval"]["lam"][0]}, {"jump_rate": ju["interval"]["lam"][1]})
    add("jump_sd", False, ju["value"]["jump_sd"], ju["interval"]["sJ"][0], ju["interval"]["sJ"][1], "CI", "value.json jump",
        {"jump_sd": ju["interval"]["sJ"][0]}, {"jump_sd": ju["interval"]["sJ"][1]})
    sb = vol["sbar"]
    add("sbar", False, sb["value"], sb["interval"][0], sb["interval"][1], "CI", "volatility.json sbar",
        {"garch": {"sbar": sb["interval"][0]}}, {"garch": {"sbar": sb["interval"][1]}})
    bo = ev["blowoff"]
    add("blowoff_g", False, bo["value"]["g_threshold"], bo["interval"][0], bo["interval"][1], "CI", "events.json blowoff",
        {"blowoff_g": bo["interval"][0]}, {"blowoff_g": bo["interval"][1]})
    for name, blk, k, ik in (("s_eps", "eps", "s_eps", "s_eps"), ("p_loss", "eps", "p_loss", "p_loss"), ("pe_cap", "eps", "pe_cap", "pe_cap_p99"),
                             ("div_c_speed", "dividend", "c_speed", "c_speed"), ("div_tau", "dividend", "tau", "tau"),
                             ("sent_rho", "sentiment", "rho", "rho_window"), ("sent_b1", "sentiment", "b1", "b1_window"),
                             ("vol_rho_v", "volume", "rho_v", "rho_v"), ("vol_beta_absr", "volume", "beta_absr", "beta_absr"),
                             ("vol_sd_e", "volume", "sd_e", "sd_e")):
        b = ob[blk]
        lo, hi = b["interval"][ik]
        add(name, False, b["value"][k], lo, hi, "CI", f"observables.json {blk}.{ik}",
            {"obs_overrides": {blk: {k: lo}}}, {"obs_overrides": {blk: {k: hi}}})
    return rows


def stage_candidates() -> int:
    rows = candidate_table()
    bad = []
    for r in rows:
        want = PREREG_IN_FORCE.get(r["candidate"])
        if want is not None and not _rel_ok(float(r["in_force"]), want, _decimals(want)):
            bad.append((r["candidate"], r["in_force"], want))
    os.makedirs(OUT, exist_ok=True)
    json.dump({"registered": "PREREG_PHASE_9.md 1.1-1.2", "candidates": rows, "mismatch_with_prereg": bad,
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "candidates.json"), "w", encoding="utf-8"), indent=1, default=str)
    for r in rows:
        print(f"{r['candidate']:>18} plan={r['plan_six']!s:5} in_force={r['in_force']!s:.40} levels={r['levels']} [{r['interval_type']}]")
    if bad:
        print("REFUSED: the parameter files differ from the pre-registration's table:", bad)
        return 2
    print(f"{len(rows)} candidates; the files agree with the pre-registration's table")
    return 0


# ============================================================================================ half-life calibration
def _fmt(h: float) -> str:
    from tools.phase2.e2_6_sweep import _fmt as f
    return f(h)


def stage_calibrate(workers: int):
    from tools.phase2.e2_6_sweep import _sd_x_job, calibrate
    vol = _j("volatility.json")
    sbar_ref = float(vol["sbar"]["value"])
    hl = [r for r in candidate_table() if r["candidate"] == "half_life"][0]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        tgt = list(ex.map(_sd_x_job, [("ar1_fit", sbar_ref, s, 5000) for s in TARGET_SEEDS_SDX]))
    target = float(np.mean(tgt))
    levels = [float(hl["levels"]["low"]), float(hl["levels"]["high"])]
    cal = calibrate("ar1_fit_hl{h}", levels, sbar_ref, workers, target_sd=target)
    cal["target_engine"] = "ar1_fit"; cal["target_seeds"] = list(TARGET_SEEDS_SDX); cal["target_sd_per_path"] = tgt
    cal["engine_names"] = {lab: f"ar1_fit_hl{_fmt(h)}" for lab, h in zip(("low", "high"), levels)}
    cal["construction"] = "tools.phase2.e2_6_sweep.calibrate (PREREG_PHASE_9.md 1.3)"
    json.dump(cal, open(os.path.join(OUT, "calibration.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(cal["levels"], indent=1), "target", target)


def level_configs() -> Dict[str, dict]:
    """{level key: GenConfig override}.  The half-life levels need `calibrate`'s file."""
    out = {"default": {}}
    cal = json.load(open(os.path.join(OUT, "calibration.json"), encoding="utf-8")) if os.path.exists(os.path.join(OUT, "calibration.json")) else None
    for r in candidate_table():
        for lab, cfg in r["config"].items():
            if r["candidate"] == "half_life":
                if cal is None:
                    continue
                h = float(r["levels"][lab])
                c = cal["levels"][_fmt(h)]
                out[f"half_life__{lab}"] = {"engine": cal["engine_names"][lab], "garch": {"sbar": c["sbar_matched_sd"]}}
                out[f"half_life_unmatched__{lab}"] = {"engine": cal["engine_names"][lab]}       # sensitivity, not ranked
            else:
                out[f"{r['candidate']}__{lab}"] = cfg
    return out


# ============================================================================================ one path
_ORACLES: dict = {}


def _init(oracle_paths):
    import warnings
    warnings.filterwarnings("ignore")
    os.environ["OMP_NUM_THREADS"] = "1"
    from tools.phase7 import e7_panel as P
    P._load_oracles(oracle_paths)
    _ORACLES.update(P._ORACLES)


def scripted_policies_crc(persona: str, scenario: str, seed: int, x: np.ndarray):
    """E7.8's drift / align / panic families exactly as `tools.phase7.e7_panel.scripted_policies` defines them, with
    the per-(scenario, seed, persona) key taken from zlib.crc32 instead of Python's per-process salted hash
    (PREREG_PHASE_9.md 0, finding 3).  The ceiling family is not an E7.8 sweep and is not built."""
    from evaluation.scoring import centre_and_hw
    from tools.phase7.e7_panel import ALIGN_PROBS, ALIGN_REF_THETA, DRIFT_RATES, PANIC_DD, PANIC_K
    c2, hw = centre_and_hw(persona)
    lo, hi = c2 - hw, c2 + hw
    key = zlib.crc32(f"{scenario}|{int(seed)}|{persona}".encode()) % (2 ** 31)
    out = {}
    direction = 1.0 if np.random.default_rng(700000 + key).random() < 0.5 else -1.0
    for d in DRIFT_RATES:
        out[f"drift_{d:.3f}"] = (lambda t, r, st, s, d=d: float(min(max(c2 + direction * d * t, 0.0), 1.0)))
    tgt = np.empty(len(x)); cur = c2
    for i, xi in enumerate(x):
        if xi < -ALIGN_REF_THETA:
            cur = lo
        elif xi > ALIGN_REF_THETA:
            cur = hi
        tgt[i] = cur
    for p in ALIGN_PROBS:
        u = np.random.default_rng(710000 + key).random(len(x))
        series = np.where(u < p, tgt, np.where(np.isclose(tgt, hi), lo, hi))
        out[f"align_{p:.1f}"] = (lambda t, r, st, s, series=series: float(series[t]))
    for k in PANIC_K:
        def pol(t, r, st, s, k=k):
            peak = s.setdefault("peak", st["total_value"])
            peak = s["peak"] = max(peak, st["total_value"])
            dd = st["total_value"] / peak - 1.0 if peak > 0 else 0.0
            return float(c2 + k * (1.0 - c2)) if dd < PANIC_DD else float(c2)
        out[f"panic_{k:.2f}"] = pol
    return out


def _path(args):
    level, config, sc, seed = args
    from envs.synthetic_market import SyntheticMarketEnv
    from evaluation.scoring import regret_terms_batch
    from evaluation.targets import centre
    from tools.phase7 import e7_panel as P
    env = SyntheticMarketEnv(sc, T, seed, config=config or None)
    d = env.data[env.data["asset"] == 0].reset_index(drop=True)
    x = d["x"].to_numpy(float)
    price = d["price"].to_numpy(float)
    f = P._render_frame(env)
    xh = {k: P._predict_from_frame(o, f) for k, o in _ORACLES.items()}
    rows = []
    for persona in PERSONAS:
        c0 = centre(persona)
        pols = {f"L5_{k}": (lambda t, r, st, s, tg=o.policy(persona, xh[k], c0): float(tg[t])) for k, o in _ORACLES.items()}
        pols.update(scripted_policies_crc(persona, sc, seed, x))
        names = list(pols)
        C = np.array([[row[1] for row in P._rows_from_policy(env, persona, c0, pols[nm], COST_BP)] for nm in names])
        res = {th: regret_terms_batch(C, x, th, persona, C[:, 0]) for th in THETAS}
        for i, nm in enumerate(names):
            rows.append({"level": level, "scenario": sc, "seed": seed, "persona": persona, "policy": nm,
                         **{f"mcr_{th}": float(res[th]["mcr"][i]) for th in THETAS},
                         "band_mas": float(res[THETAS[0]]["band_mas"][i]),
                         "sd_x": float(x.std()), "sd_r": float(np.diff(np.log(price)).std())})
    return rows


def run_panel(level: str, config: dict, workers: int) -> str:
    fpath = os.path.join(OUT, f"panel_{level}.parquet")
    if os.path.exists(fpath):
        return fpath
    oracle_paths = {fs: os.path.join(E6_16A, f"oracle_{fs}.pkl") for fs in ("full_level_free", "level_free")}
    jobs = [(level, config, sc, s) for sc in SCENARIOS for s in SEEDS]
    t0 = time.time(); buf = []
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(oracle_paths,)) as ex:
        for i, rows in enumerate(ex.map(_path, jobs, chunksize=2), 1):
            buf.extend(rows)
            if i % 100 == 0 or i == len(jobs):
                el = time.time() - t0
                print(f"  [{level}] {i}/{len(jobs)} paths ({el:.0f} s; ETA {el / i * (len(jobs) - i):.0f} s)", flush=True)
    df = pd.DataFrame(buf)
    for c in ("level", "scenario", "persona", "policy"):
        df[c] = df[c].astype("category")
    df.to_parquet(fpath, index=False)
    return fpath


def stage_reference(workers: int) -> int:
    run_panel("default", {}, workers)
    p = pd.read_parquet(os.path.join(OUT, "panel_default.parquet"))
    flat = float(p[(p.policy == "L5_full_level_free") & (p.scenario == "flat")]["mcr_0.05"].mean())
    ok_a = round(flat, 4) == 0.0770
    ref = pd.read_csv(os.path.join(E6_16A, "runs.csv"))
    ref = ref[ref.policy.isin(["L5_full_level_free", "L5_level_free"])]
    m = ref.merge(p[p.policy.isin(["L5_full_level_free", "L5_level_free"])].astype({"scenario": str, "persona": str, "policy": str}),
                  on=["scenario", "seed", "persona", "policy"], how="inner", suffixes=("_16a", "_here"))
    worst = float((m["mcr_0.05_16a"] - m["mcr_0.05_here"]).abs().max()) if len(m) else float("nan")
    ok_b = bool(len(m) == 2 * len(SCENARIOS) * len(SEEDS) * len(PERSONAS) and worst <= 1e-12)
    doc = {"registered": "PREREG_PHASE_9.md 1.3", "flat_L5_full_level_free_mcr_0.05": flat, "published": 0.0770, "row_a_pass": ok_a,
           "rows_compared_with_e6_16a": int(len(m)), "worst_abs_diff": worst, "row_b_pass": ok_b, "pass": bool(ok_a and ok_b),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(OUT, "reference.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(doc, indent=1))
    if not doc["pass"]:
        print("STOP: a reference row does not reproduce; no level panel runs (PREREG 1.3)")
        return 2
    return 0


def stage_panels(workers: int):
    if not json.load(open(os.path.join(OUT, "reference.json"), encoding="utf-8"))["pass"]:
        raise SystemExit("the reference rows have not passed (PREREG 1.3)")
    levels = level_configs()
    todo = [k for k in levels if k != "default"]
    t0 = time.time()
    for i, lv in enumerate(todo, 1):
        run_panel(lv, levels[lv], workers)
        el = time.time() - t0
        print(f"[panels] {i}/{len(todo)} levels done ({el / 3600:.2f} h; ETA {el / i * (len(todo) - i) / 3600:.2f} h)", flush=True)


# ============================================================================================ the statistic and the rule
OUTCOMES = {"O1": ("L5_full_level_free", "mcr_0.05"), "O2": ("L5_full_level_free", "mcr_0.002"), "O3": ("scripted", "band_mas")}


def outcome_array(panel: pd.DataFrame, k: str) -> np.ndarray:
    """(12 cells, 100 seeds) of outcome k; O3 is the mean band-MAS over the scripted policies."""
    pol, col = OUTCOMES[k]
    q = panel[~panel.policy.astype(str).str.startswith("L5_")] if pol == "scripted" else panel[panel.policy.astype(str) == pol]
    g = q.groupby(["scenario", "persona", "seed"], observed=True)[col].mean()
    arr = g.unstack("seed").reindex(index=pd.MultiIndex.from_product([SCENARIOS, PERSONAS]), columns=list(SEEDS))
    return arr.to_numpy(float)


MIN_SEEDS_PER_CELL = 50          # DESIGN (PREREG_PHASE_9_ADDENDUM.md 4)
MAX_CELLS_DROPPED = 2            # DESIGN (idem): above this a level's outcome is NOT DEFINED


def effects_from(y0: np.ndarray, y1: np.ndarray, idx=None, diagnostics: bool = False):
    """E = mean over cells of |mean paired seed difference| / sd over seeds at the default (PREREG 1.4), on the seeds
    where BOTH the default and the level are defined (addendum 4).  A cell with fewer than MIN_SEEDS_PER_CELL defined
    seeds is dropped; a level that loses more than MAX_CELLS_DROPPED cells is NOT DEFINED (NaN).  The point estimate
    and every bootstrap draw call this one function."""
    if idx is not None:
        y0, y1 = y0[:, idx], y1[:, idx]
    ok = np.isfinite(y0) & np.isfinite(y1)
    n_ok = ok.sum(axis=1)
    d = np.where(ok, y1 - y0, np.nan)
    with np.errstate(invalid="ignore"):
        md = np.nanmean(d, axis=1)
        sd = np.array([np.std(y0[c][ok[c]], ddof=1) if n_ok[c] > 1 else np.nan for c in range(y0.shape[0])])
        e = np.abs(md) / np.where(sd > 0, sd, np.nan)
    used = (n_ok >= MIN_SEEDS_PER_CELL) & np.isfinite(e)
    value = float(np.mean(e[used])) if (y0.shape[0] - used.sum()) <= MAX_CELLS_DROPPED and used.any() else float("nan")
    if not diagnostics:
        return value
    return value, {"cells_used": int(used.sum()), "cells_total": int(y0.shape[0]),
                   "seeds_min": int(n_ok.min()), "seeds_median": float(np.median(n_ok)),
                   "defined": bool(np.isfinite(value))}


def stage_rank():
    from evaluation import scoring_params as SP
    SP.load()
    from evaluation.metrics_v2 import thetas_in_force
    if sorted(float(t) for t in thetas_in_force()) != sorted(THETAS):
        raise SystemExit(f"the co-primary theta in force {thetas_in_force()} is not this tool's {THETAS}")
    cands = candidate_table()
    levels = level_configs()
    base = pd.read_parquet(os.path.join(OUT, "panel_default.parquet"))
    Y0 = {k: outcome_array(base, k) for k in OUTCOMES}
    rng = np.random.default_rng(9101)
    boot_idx = rng.integers(0, len(SEEDS), size=(N_BOOT, len(SEEDS)))
    rows, E_boot = [], {}
    for c in cands + [{"candidate": "half_life_unmatched", "plan_six": False, "levels": {"low": None, "high": None}}]:
        name = c["candidate"]
        labs = [l for l in levels if l.startswith(name + "__")]
        per_level = {}
        for lv in labs:
            p = pd.read_parquet(os.path.join(OUT, f"panel_{lv}.parquet"))
            Y1 = {k: outcome_array(p, k) for k in OUTCOMES}
            per_level[lv] = {}
            for k in OUTCOMES:
                v, diag = effects_from(Y0[k], Y1[k], diagnostics=True)
                per_level[lv][k] = v
                per_level[lv][f"{k}_diagnostics"] = diag
            per_level[lv]["boot"] = {k: np.array([effects_from(Y0[k], Y1[k], b) for b in boot_idx]) for k in OUTCOMES}
            per_level[lv]["sd_x"] = float(p.groupby(["scenario", "seed"], observed=True)["sd_x"].first().mean())
            per_level[lv]["sd_r"] = float(p.groupby(["scenario", "seed"], observed=True)["sd_r"].first().mean())
            # the coverage a level leaves the yardstick, reported as a result of its own (addendum 4)
            for th in THETAS:
                cov = p[p.policy.astype(str) == OUTCOMES["O1"][0]].groupby(["scenario", "seed", "persona"], observed=True)[f"mcr_{th}"].first()
                per_level[lv][f"cells_with_a_resolvable_day_theta_{th}"] = float(np.isfinite(cov).mean())
        # the maximum over levels ignores an undefined level explicitly, never implicitly (addendum 4)
        E, Eb = {}, {}
        for k in OUTCOMES:
            vals = [per_level[lv][k] for lv in labs]
            E[k] = float(np.nanmax(vals)) if any(np.isfinite(v) for v in vals) else float("nan")
            stack = np.stack([per_level[lv]["boot"][k] for lv in labs])
            Eb[k] = np.nanmax(stack, axis=0) if np.isfinite(stack).any() else np.full(stack.shape[1], np.nan)
        undefined = {f"{lv}|{k}": per_level[lv][f"{k}_diagnostics"] for lv in labs for k in OUTCOMES
                     if not per_level[lv][f"{k}_diagnostics"]["defined"]}
        r = {"candidate": name, "plan_six": bool(c["plan_six"]), "ranked": name != "half_life_unmatched",
             "E_O1": E["O1"], "E_O2": E["O2"], "E_O3": E["O3"],
             "E_oracle": float(np.nanmean([E["O1"], E["O2"]])) if np.isfinite([E["O1"], E["O2"]]).any() else float("nan"),
             "E_scripted": E["O3"], "levels_not_defined": undefined,
             **{f"level_{lv}": {k: per_level[lv][k] for k in ("O1", "O2", "O3", "sd_x", "sd_r")}
                | {f"{k}_diagnostics": per_level[lv][f"{k}_diagnostics"] for k in OUTCOMES}
                | {f"cells_with_a_resolvable_day_theta_{th}": per_level[lv][f"cells_with_a_resolvable_day_theta_{th}"] for th in THETAS}
                for lv in labs}}
        for k, v in (("E_oracle", 0.5 * (Eb["O1"] + Eb["O2"])), ("E_scripted", Eb["O3"])):
            r[f"{k}_ci95"] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
        E_boot[name] = {"oracle": 0.5 * (Eb["O1"] + Eb["O2"]), "scripted": Eb["O3"]}
        rows.append(r)
    t = pd.DataFrame(rows)
    ranked = t[t.ranked].copy()

    def order(df, oracle, scripted, plan):
        r_or = (-oracle).argsort(kind="stable").argsort() + 1
        r_sc = (-scripted).argsort(kind="stable").argsort() + 1
        score = r_or + r_sc
        # ties: plan's six first, then the larger oracle effect
        key = np.lexsort((-oracle, ~plan, score))
        return r_or, r_sc, score, [df["candidate"].iloc[i] for i in key]

    r_or, r_sc, score, ordered = order(ranked, ranked.E_oracle.to_numpy(), ranked.E_scripted.to_numpy(), ranked.plan_six.to_numpy())
    ranked["rank_oracle"], ranked["rank_scripted"], ranked["rank_sum"] = r_or, r_sc, score
    six = ordered[:6]
    shared = sorted(set(six) & set(PLAN_SIX))
    run_plan = len(shared) >= 5
    further = [p for p in six if p not in PLAN_SIX] if run_plan else []
    names = ranked["candidate"].tolist()
    top_share = {n: 0 for n in names}
    for b in range(N_BOOT):
        o = np.array([E_boot[n]["oracle"][b] for n in names]); s = np.array([E_boot[n]["scripted"][b] for n in names])
        _, _, _, ob = order(ranked, o, s, ranked.plan_six.to_numpy())
        for n in ob[:6]:
            top_share[n] += 1
    ranked["top_six_share_boot"] = ranked["candidate"].map(lambda n: top_share[n] / N_BOOT)
    decision = {"data_driven_six": six, "shared_with_plan": shared, "n_shared": len(shared),
                "run": "plan's six" if run_plan else "data-driven six",
                "list_run": list(PLAN_SIX) if run_plan else six, "further_cell": further,
                "reason": ("the data-driven six share >= 5 parameters with the plan's six (REG-16 (i))" if run_plan else
                           f"the data-driven six share only {len(shared)} parameters with the plan's six (REG-16 (i))")}
    t = t.merge(ranked[["candidate", "rank_oracle", "rank_scripted", "rank_sum", "top_six_share_boot"]], on="candidate", how="left")
    t.to_csv(os.path.join(OUT, "effects.csv"), index=False)
    json.dump({"registered": "PREREG_PHASE_9.md 1.4-1.5", "decision": decision, "n_boot": N_BOOT, "seeds": len(SEEDS),
               "table": json.loads(t.to_json(orient="records")), "scoring_json_sha256": SP.SHA256,
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "ranking.json"), "w", encoding="utf-8"), indent=1, default=float)
    show = t.sort_values("rank_sum")[["candidate", "plan_six", "E_oracle", "E_scripted", "rank_oracle", "rank_scripted",
                                      "rank_sum", "top_six_share_boot"]]
    print(show.round(4).to_string(index=False))
    print(json.dumps(decision, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="candidates,calibrate,reference,panels,rank")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(argv)
    for st in [x.strip() for x in a.stages.split(",") if x.strip()]:
        if st == "candidates":
            if stage_candidates() != 0:
                return 2
        elif st == "calibrate":
            stage_calibrate(a.workers)
        elif st == "reference":
            if stage_reference(a.workers) != 0:
                return 2
        elif st == "panels":
            stage_panels(a.workers)
        elif st == "rank":
            stage_rank()
        else:
            raise SystemExit(f"unknown stage {st!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
