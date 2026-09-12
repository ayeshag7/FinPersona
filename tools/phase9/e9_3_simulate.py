"""
v2.1 Phase 9 -- E9.3: the robustness criteria's statistics, validated on simulated data with Phase 8's measured
components BEFORE any grid run (PREREG_PHASE_9.md 3).  Staged; each condition cached.

    python -u -m tools.phase9.e9_3_simulate --stages bridge,refdist,refdist_boot --workers 7

`bridge`        R3 (the two-way bootstrap) at Phase 8's mixed_pp condition (M 6, S 19, model x arm sd 0.03, equal
                heterogeneity, beta 0), 2,000 datasets per reading.  Its size's Wilson interval must overlap
                e8_3/mixed_pp.json's E2 row, or the stage stops.
`refdist`       R1 normal, R2 t(M - 1), R4 two-way ANOVA with Satterthwaite df, on 864 conditions x 10,000 datasets.
`refdist_boot`  R3 on the registered subset, 1,000 datasets, B = 1,999.

The data-generating process draws every ARM-LEVEL term and differences them (`draw_arm_terms`, `D_from_terms`); the
long-frame construction `long_frame_from_terms` + `paired_matrix` is the proof reference
(`tests/test_v2_1_phase_9.py::test_refdist_vectorised_equals_long_frame`).

Outputs: docs/env_v2/generated/v2_1/e9_3/{bridge.json, refdist.{csv,json}, refdist_boot.{csv,json}}, caches in _cache/.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import zlib
from typing import Dict, List

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e9_3")
CACHE = os.path.join(OUT, "_cache")
COMP_FILE = os.path.join(GEN, "e8_5", "components_reml_persona_path.json")
TRANSFER_FILE = os.path.join(GEN, "e8_5", "transfer.json")
MIXED_PP_FILE = os.path.join(GEN, "e8_3", "mixed_pp.json")
ALPHA = 0.05
ALPHA_PRIME = 0.05 / 36                 # E8.5's family count (P8-16); re-read at the design's count from cached p
MS = (2, 3, 4, 5, 6, 8, 10, 12, 14)
SS = (19, 47, 93)
N_DATASETS = 10_000
CHUNK = 1_000
BOOT_MS, BOOT_SS = (3, 6, 8, 12), (19, 93)
N_BOOT_DATASETS, B = 1_000, 1_999
BRIDGE_DATASETS = 2_000


def wilson(k: int, n: int, z: float = 1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, c - h, c + h)


# ============================================================================================ inputs, read not typed
def inputs() -> Dict[str, float]:
    comp = json.load(open(COMP_FILE, encoding="utf-8"))["band_mas"]["components"]
    tr = json.load(open(TRANSFER_FILE, encoding="utf-8"))["per_metric"]["band_mas"]
    from experiments import inference_params as IP
    limit = float(IP.block("sigma_plugin")["value"]["band_mas_R1_limit"])
    delta = float(IP.block("min_effect")["value"]["band_mas"])
    s_ma_p8 = max(float(r["s_ma"]) for r in json.load(open(MIXED_PP_FILE, encoding="utf-8"))["table"])
    return {"path_arm": float(comp["path_arm"]), "persona_path_arm": float(comp["persona_path_arm"]),
            "replicate": float(comp["replicate"]),
            "int_ratio": float(tr["sigma2_int_gpt5mini_bull_trap"]) / float(tr["sigma2_int_flash_bull_trap"]),
            "rep_ratio": float(tr["sigma2_rep_gpt5mini_bull_trap"]) / float(tr["sigma2_rep_flash_bull_trap"]),
            "flash_limit": limit, "delta": delta, "s_ma_p8": s_ma_p8}


def taus(inp) -> Dict[str, float]:
    return {"0": 0.0, "half_limit": 0.5 * inp["flash_limit"], "limit": inp["flash_limit"],
            "p8_sma0.03": math.sqrt(2.0) * inp["s_ma_p8"]}


# ============================================================================================ the process
def draw_arm_terms(rng, n: int, M: int, S: int, tau: float, shared: bool, hetero: bool, inp) -> Dict[str, np.ndarray]:
    """Every arm-level term of PREREG 3.1, for n datasets.  Shapes (n, ..., 2), last axis (static, memory)."""
    sd = lambda v: math.sqrt(max(v, 0.0))                               # noqa: E731
    n_het = M // 2 if hetero else 0
    k = np.ones(M); r = np.ones(M)
    if n_het:
        k[:n_het] = inp["int_ratio"]; r[:n_het] = inp["rep_ratio"]
    return {
        "b": rng.normal(0.0, tau / math.sqrt(2.0), size=(n, M, 2)),
        "g": rng.normal(0.0, sd(inp["path_arm"]), size=(n, S, 2)),
        "h": (rng.normal(0.0, sd(inp["persona_path_arm"]), size=(n, 1, S, 2)) if shared
              else rng.normal(0.0, sd(inp["persona_path_arm"]), size=(n, M, S, 2))),
        # heterogeneity: the models at GPT-5 mini's scale carry an extra model-specific seed x arm term so that their
        # seed x arm variance is int_ratio x Flash's (in the shared reading the shared part cannot differ by model)
        "h_extra": rng.normal(0.0, 1.0, size=(n, M, S, 2)) * np.sqrt(np.maximum(k - 1.0, 0.0) * inp["persona_path_arm"])[None, :, None, None],
        "e": rng.normal(0.0, 1.0, size=(n, M, S, 2)) * np.sqrt(r * inp["replicate"])[None, :, None, None],
    }


def D_from_terms(t: Dict[str, np.ndarray], beta: float) -> np.ndarray:
    """(n, M, S) seed-level memory - static differences, as array arithmetic."""
    diff = lambda a: a[..., 1] - a[..., 0]                               # noqa: E731
    return (beta + diff(t["b"])[:, :, None] + diff(t["g"])[:, None, :] + diff(t["h"]) + diff(t["h_extra"]) + diff(t["e"]))


def long_frame_from_terms(t: Dict[str, np.ndarray], beta: float, i: int = 0) -> pd.DataFrame:
    """The reference construction for dataset i: one row per (model, path, arm) with the run's value, built by loops."""
    M = t["b"].shape[1]; S = t["g"].shape[1]
    rows = []
    for m in range(M):
        for s in range(S):
            for a, arm in enumerate(("static", "memory")):
                h = t["h"][i, 0 if t["h"].shape[1] == 1 else m, s, a]
                y = beta * a + t["b"][i, m, a] + t["g"][i, s, a] + h + t["h_extra"][i, m, s, a] + t["e"][i, m, s, a]
                rows.append((f"m{m:02d}", f"p{s:03d}", arm, y))
    return pd.DataFrame(rows, columns=["Model", "Path", "Arm", "y"])


def paired_matrix(frame: pd.DataFrame) -> np.ndarray:
    g = frame.pivot_table(index=["Model", "Path"], columns="Arm", values="y")
    return (g["memory"] - g["static"]).unstack("Path").to_numpy(float)


# ============================================================================================ the candidates
def analytic(D: np.ndarray) -> Dict[str, np.ndarray]:
    n, M, S = D.shape
    rm = D.mean(axis=2)                                                  # (n, M) per-model means
    cm = D.mean(axis=1)                                                  # (n, S) per-path means
    g = rm.mean(axis=1)                                                  # grand mean
    s_m = rm.std(axis=1, ddof=1)
    se12 = s_m / math.sqrt(M)
    z = g / se12
    p1 = 2 * stats.norm.sf(np.abs(z))
    p2 = 2 * stats.t.sf(np.abs(z), M - 1)
    ms_m = S * ((rm - g[:, None]) ** 2).sum(axis=1) / (M - 1)
    ms_s = M * ((cm - g[:, None]) ** 2).sum(axis=1) / (S - 1)
    resid = D - rm[:, :, None] - cm[:, None, :] + g[:, None, None]
    ms_e = (resid ** 2).sum(axis=(1, 2)) / ((M - 1) * (S - 1))
    num = ms_m + ms_s - ms_e
    floored = num < ms_e
    numf = np.where(floored, ms_e, num)
    se4 = np.sqrt(numf / (M * S))
    df_sat = num ** 2 / (ms_m ** 2 / (M - 1) + ms_s ** 2 / (S - 1) + ms_e ** 2 / ((M - 1) * (S - 1)))
    df4 = np.where(floored, (M - 1) * (S - 1), df_sat)
    p4 = 2 * stats.t.sf(np.abs(g / se4), df4)
    # R5 (PREREG_PHASE_9_ADDENDUM.md 1): R4's two-way variance referred to t with the MODEL-level df, M - 1.  Added after
    # R1-R4's rates were read; judged only on the fresh datasets of `refdist_fresh`
    p5 = 2 * stats.t.sf(np.abs(g / se4), M - 1)
    return {"est": g, "p_R1": p1, "p_R2": p2, "se_R2": se12, "p_R4": p4, "se_R4": se4, "floored_R4": floored, "df_R4": df4,
            "p_R5": p5}


def bootstrap_R3(D: np.ndarray, rngs) -> Dict[str, np.ndarray]:
    """E2 (`tools.stats_v2.pigeonhole_ci`) for every dataset: per dataset its own generator, the model weights drawn
    first and the path weights second, exactly as `pigeonhole_ci` draws them; the statistic over all draws as array
    arithmetic.  Returns the percentile limits at both alphas and p_boot as pigeonhole_ci computes it."""
    n, M, S = D.shape
    wm = np.empty((n, B, M)); ws = np.empty((n, B, S))
    for i, rng in enumerate(rngs):
        wm[i] = rng.multinomial(M, np.full(M, 1.0 / M), size=B)
        ws[i] = rng.multinomial(S, np.full(S, 1.0 / S), size=B)
    stat = np.einsum("nbm,nms,nbs->nb", wm, D, ws, optimize=True) / (wm.sum(axis=2) * ws.sum(axis=2))
    out = {}
    for lab, a in (("", ALPHA), ("_prime", ALPHA_PRIME)):
        lo, hi = np.percentile(stat, [100 * a / 2, 100 * (1 - a / 2)], axis=1)
        out[f"lo{lab}"], out[f"hi{lab}"] = lo, hi
    out["p_boot"] = np.minimum(1.0, 2 * np.minimum((stat <= 0).mean(axis=1), (stat >= 0).mean(axis=1)) + 1.0 / (B + 1))
    out["est"] = D.mean(axis=(1, 2))
    return out


# ============================================================================================ conditions
def conditions(inp) -> List[dict]:
    return [{"M": M, "S": S, "tau_label": tl, "tau": tv, "shared": sh, "hetero": he, "beta": be}
            for M in MS for S in SS for tl, tv in taus(inp).items() for sh in (True, False) for he in (False, True)
            for be in (0.0, inp["delta"])]


def boot_conditions(inp) -> List[dict]:
    t = taus(inp)
    return [{"M": M, "S": S, "tau_label": tl, "tau": t[tl], "shared": sh, "hetero": False, "beta": be}
            for M in BOOT_MS for S in BOOT_SS for tl in ("0", "p8_sma0.03") for sh in (True, False)
            for be in (0.0, inp["delta"])]


def key(c) -> str:
    return (f"M{c['M']}_S{c['S']}_tau{c['tau_label']}_{'shared' if c['shared'] else 'modelspecific'}_"
            f"{'hetero' if c['hetero'] else 'equal'}_beta{c['beta']}")


def _analytic_task(args):
    c, inp = args[0], args[1]
    stream = args[2] if len(args) > 2 else "refdist"
    f = os.path.join(CACHE, f"{stream}_{key(c)}.parquet")
    if os.path.exists(f):
        return f
    # the registered stream [9, 3, 1, key]; the fresh stream of addendum 1 [9, 3, 5, key] shares no draw with it
    rng = np.random.default_rng([9, 3, 1 if stream == "refdist" else 5, zlib.crc32(key(c).encode())])
    parts = []
    for start in range(0, N_DATASETS, CHUNK):
        n = min(CHUNK, N_DATASETS - start)
        D = D_from_terms(draw_arm_terms(rng, n, c["M"], c["S"], c["tau"], c["shared"], c["hetero"], inp), c["beta"])
        parts.append(pd.DataFrame(analytic(D)))
    pd.concat(parts, ignore_index=True).to_parquet(f, index=False)
    return f


def summarise_analytic(c, t: pd.DataFrame) -> dict:
    r = {**{k: v for k, v in c.items()}, "n_datasets": len(t)}
    for cand in [x for x in ("R1", "R2", "R4", "R5") if f"p_{x}" in t]:
        for lab, a in (("", ALPHA), ("_prime", ALPHA_PRIME)):
            p, lo, hi = wilson(int((t[f"p_{cand}"] <= a).sum()), len(t))
            r.update({f"{cand}_reject{lab}": p, f"{cand}_reject{lab}_lo": lo, f"{cand}_reject{lab}_hi": hi})
    sd_est = float(t["est"].std(ddof=1))
    r["sd_est"] = sd_est
    r["R2_se_over_sd"] = float(t["se_R2"].median()) / sd_est if sd_est > 0 else float("nan")
    r["R4_se_over_sd"] = float(t["se_R4"].median()) / sd_est if sd_est > 0 else float("nan")
    r["R4_floor_share"] = float(t["floored_R4"].mean())
    return r


def stage_refdist(workers: int):
    inp = inputs()
    os.makedirs(CACHE, exist_ok=True)
    conds = conditions(inp)
    t0 = time.time()
    tasks = [(c, inp) for c in conds]
    done = 0
    if workers > 1:
        from multiprocessing import Pool
        with Pool(workers) as pool:
            for _ in pool.imap_unordered(_analytic_task, tasks, chunksize=1):
                done += 1
                if done % 24 == 0 or done == len(tasks):
                    el = time.time() - t0
                    print(f"[refdist] {done}/{len(tasks)} conditions ({el:.0f} s; ETA {el / done * (len(tasks) - done):.0f} s)", flush=True)
    else:
        for tk in tasks:
            _analytic_task(tk); done += 1
    rows = [summarise_analytic(c, pd.read_parquet(os.path.join(CACHE, f"refdist_{key(c)}.parquet"))) for c in conds]
    s = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    s.to_csv(os.path.join(OUT, "refdist.csv"), index=False)
    json.dump({"registered": "PREREG_PHASE_9.md 3.1", "inputs": inp, "taus": taus(inp), "alpha": ALPHA, "alpha_prime": ALPHA_PRIME,
               "n_datasets": N_DATASETS, "recommendation": recommend(s, None, inp),
               "table": json.loads(s.to_json(orient="records")), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "refdist.json"), "w", encoding="utf-8"), indent=1)
    print(f"[refdist] {len(s)} conditions in {time.time() - t0:.0f} s")


def _boot_task(args):
    c, inp, n, tag = args
    f = os.path.join(CACHE, f"{tag}_{key(c)}.parquet")
    if os.path.exists(f):
        return f
    kc = zlib.crc32((tag + key(c)).encode())
    data_rng = np.random.default_rng([9, 3, 2, kc])
    parts = []
    for start in range(0, n, 50):
        m = min(50, n - start)
        D = D_from_terms(draw_arm_terms(data_rng, m, c["M"], c["S"], c["tau"], c["shared"], c["hetero"], inp), c["beta"])
        rngs = [np.random.default_rng([9, 3, 3, kc, start + j]) for j in range(m)]
        parts.append(pd.DataFrame(bootstrap_R3(D, rngs)))
    pd.concat(parts, ignore_index=True).to_parquet(f, index=False)
    return f


def summarise_boot(c, t: pd.DataFrame) -> dict:
    r = {**c, "n_datasets": len(t), "B": B}
    for lab, a in (("", ALPHA), ("_prime", ALPHA_PRIME)):
        rej = (t[f"lo{lab}"] > 0) | (t[f"hi{lab}"] < 0)
        p, lo, hi = wilson(int(rej.sum()), len(t))
        r.update({f"R3_reject{lab}": p, f"R3_reject{lab}_lo": lo, f"R3_reject{lab}_hi": hi})
    r["R3_coverage"] = float(((t["lo"] <= c["beta"]) & (t["hi"] >= c["beta"])).mean())
    r["R3_min_attainable_p"] = 1.0 / (B + 1)
    return r


def _run_pool(tasks, fn, workers, label):
    t0 = time.time(); done = 0
    from multiprocessing import Pool
    with Pool(max(1, workers)) as pool:
        for _ in pool.imap_unordered(fn, tasks, chunksize=1):
            done += 1
            el = time.time() - t0
            print(f"[{label}] {done}/{len(tasks)} ({el:.0f} s; ETA {el / done * (len(tasks) - done):.0f} s)", flush=True)


def stage_bridge(workers: int) -> int:
    inp = inputs()
    os.makedirs(CACHE, exist_ok=True)
    ref = {("shared" if r["shared"] else "modelspecific"): r for r in json.load(open(MIXED_PP_FILE, encoding="utf-8"))["table"]
           if r["M"] == 6 and float(r["s_ma"]) == inp["s_ma_p8"] and float(r["beta"]) == 0.0}
    t = taus(inp)
    conds = [{"M": 6, "S": int(ref["shared"]["S"]), "tau_label": "p8_sma0.03", "tau": t["p8_sma0.03"], "shared": sh,
              "hetero": False, "beta": 0.0} for sh in (True, False)]
    _run_pool([(c, inp, BRIDGE_DATASETS, "bridge") for c in conds], _boot_task, min(workers, 2), "bridge")
    out, ok = [], True
    for c in conds:
        s = summarise_boot(c, pd.read_parquet(os.path.join(CACHE, f"bridge_{key(c)}.parquet")))
        r8 = ref["shared" if c["shared"] else "modelspecific"]
        overlap = not (s["R3_reject_hi"] < r8["e2_reject_lo"] or s["R3_reject_lo"] > r8["e2_reject_hi"])
        ok &= overlap
        out.append({"reading": "shared" if c["shared"] else "model-specific", "here": [s["R3_reject"], s["R3_reject_lo"], s["R3_reject_hi"]],
                    "n_here": BRIDGE_DATASETS, "phase8_e2": [r8["e2_reject"], r8["e2_reject_lo"], r8["e2_reject_hi"]],
                    "n_phase8": int(r8["n_datasets"]), "wilson_overlap": overlap})
    doc = {"registered": "PREREG_PHASE_9.md 3.1 (bridge)", "rows": out, "pass": bool(ok), "inputs": inp,
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    os.makedirs(OUT, exist_ok=True)
    json.dump(doc, open(os.path.join(OUT, "bridge.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(doc, indent=1))
    if not ok:
        print("STOP: the bridge to Phase 8 does not overlap; refdist does not run (PREREG 3.1)")
        return 2
    return 0


def stage_refdist_boot(workers: int):
    inp = inputs()
    if not json.load(open(os.path.join(OUT, "bridge.json"), encoding="utf-8"))["pass"]:
        raise SystemExit("the bridge has not passed (PREREG 3.1)")
    conds = boot_conditions(inp)
    _run_pool([(c, inp, N_BOOT_DATASETS, "boot") for c in conds], _boot_task, workers, "refdist_boot")
    s = pd.DataFrame([summarise_boot(c, pd.read_parquet(os.path.join(CACHE, f"boot_{key(c)}.parquet"))) for c in conds])
    s.to_csv(os.path.join(OUT, "refdist_boot.csv"), index=False)
    json.dump({"registered": "PREREG_PHASE_9.md 3.1", "B": B, "n_datasets": N_BOOT_DATASETS,
               "table": json.loads(s.to_json(orient="records")), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "refdist_boot.json"), "w", encoding="utf-8"), indent=1)
    print(s.round(3).to_string(index=False))


# ============================================================================================ the recommendation rule
def recommend(s: pd.DataFrame, boot: pd.DataFrame, inp, cands=("R1", "R2", "R4")) -> Dict[str, dict]:
    """PREREG 3.1: holds size at M = Wilson lower limit <= alpha at both alphas in every condition at that M;
    recommended = the size-holding candidate with the highest power at alpha' at tau = half the limit, S = 93,
    model-specific, equal heterogeneity.  R3 is judged only on its subset, and cannot be recommended at an M it was
    not run at.  `cands` is the registered set; addendum 1 applies the same rule with R5 added, on fresh datasets."""
    out = {}
    for M in MS:
        sm = s[(s.M == M) & (s.beta == 0.0)]
        holds = {c: bool(((sm[f"{c}_reject_lo"] <= ALPHA) & (sm[f"{c}_reject_prime_lo"] <= ALPHA_PRIME)).all())
                 for c in cands}
        # which conditions break it, so a failure is located and not only counted
        breaks = {c: [key(dict(r)) for _, r in sm.iterrows()
                      if not (r[f"{c}_reject_lo"] <= ALPHA and r[f"{c}_reject_prime_lo"] <= ALPHA_PRIME)] for c in cands}
        pw_row = s[(s.M == M) & (s.S == 93) & (s.tau_label == "half_limit") & (~s.shared) & (~s.hetero) & (s.beta > 0)]
        power = {c: float(pw_row[f"{c}_reject_prime"].iloc[0]) if len(pw_row) else float("nan") for c in cands}
        if boot is not None and M in BOOT_MS:
            bm = boot[(boot.M == M) & (boot.beta == 0.0)]
            holds["R3"] = bool(((bm["R3_reject_lo"] <= ALPHA) & (bm["R3_reject_prime_lo"] <= ALPHA_PRIME)).all())
        ok = [c for c, h in holds.items() if h and c in power and np.isfinite(power[c])]
        out[str(M)] = {"holds_size": holds, "n_conditions_breaking": {c: len(v) for c, v in breaks.items()},
                       "conditions_breaking": breaks, "power_alpha_prime_at_half_limit_S93": power,
                       "recommended": max(ok, key=lambda c: power[c]) if ok else None}
    return out


def stage_refdist_fresh(workers: int):
    """PREREG_PHASE_9_ADDENDUM.md 1: every analytic candidate, R5 included, on 864 conditions x 10,000 FRESH datasets
    (stream [9, 3, 5, key]).  R1, R2 and R4 are thereby replicated on independent data; R5 is judged only here."""
    inp = inputs()
    os.makedirs(CACHE, exist_ok=True)
    conds = conditions(inp)
    _run_pool([(c, inp, "fresh") for c in conds], _analytic_task, workers, "refdist_fresh")
    s = pd.DataFrame([summarise_analytic(c, pd.read_parquet(os.path.join(CACHE, f"fresh_{key(c)}.parquet"))) for c in conds])
    s.to_csv(os.path.join(OUT, "refdist_fresh.csv"), index=False)
    bp = os.path.join(OUT, "refdist_boot.csv")
    boot = pd.read_csv(bp) if os.path.exists(bp) else None
    json.dump({"registered": "PREREG_PHASE_9_ADDENDUM.md 1", "stream": [9, 3, 5], "n_datasets": N_DATASETS,
               "recommendation_registered_candidates": recommend(s, boot, inp, ("R1", "R2", "R4")),
               "recommendation_with_R5": recommend(s, boot, inp, ("R1", "R2", "R4", "R5")),
               "table": json.loads(s.to_json(orient="records")),
               "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "refdist_fresh.json"), "w", encoding="utf-8"), indent=1)
    print(f"[refdist_fresh] {len(s)} conditions written")


def stage_recommend():
    inp = inputs()
    s = pd.read_csv(os.path.join(OUT, "refdist.csv"))
    bp = os.path.join(OUT, "refdist_boot.csv")
    boot = pd.read_csv(bp) if os.path.exists(bp) else None
    rec = recommend(s, boot, inp)
    doc = json.load(open(os.path.join(OUT, "refdist.json"), encoding="utf-8"))
    doc["recommendation"] = rec
    doc["recommendation_includes_R3"] = boot is not None
    json.dump(doc, open(os.path.join(OUT, "refdist.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(rec, indent=1))


def wilson_break_threshold(n: int, p0: float) -> int:
    """The smallest rejection count k whose Wilson 95 % lower limit exceeds p0 at n datasets."""
    for k in range(n + 1):
        if wilson(k, n)[1] > p0:
            return k
    return n + 1


def stage_rule_check():
    """PREREG_PHASE_9_ADDENDUM.md 3: the recommendation rule's own false-failure rate, by exact binomial arithmetic.  A
    condition 'breaks' when its size's Wilson lower limit exceeds the nominal level; the rule needs no break in any
    null condition at an M, at both alphas.  Conditions are treated as independent."""
    from scipy.stats import binom
    inp = inputs()
    n_analytic = len([c for c in conditions(inp) if c["M"] == MS[0] and c["beta"] == 0.0])
    n_boot = len([c for c in boot_conditions(inp) if c["M"] == BOOT_MS[0] and c["beta"] == 0.0])
    rows = []
    for label, n, n_cond in (("analytic candidates (R1, R2, R4, R5)", N_DATASETS, n_analytic), ("R3 (bootstrap subset)", N_BOOT_DATASETS, n_boot)):
        q_exact = {}
        for alab, a in (("alpha", ALPHA), ("alpha_prime", ALPHA_PRIME)):
            k = wilson_break_threshold(n, a)
            for mult in (1.0, 1.1, 1.25):
                q = float(binom.sf(k - 1, n, min(a * mult, 1.0)))
                if mult == 1.0:
                    q_exact[alab] = q
                rows.append({"candidates": label, "n_datasets": n, "conditions_per_M": n_cond, "alpha": alab,
                             "nominal": a, "true_rate_over_nominal": mult, "break_count_threshold": k,
                             "p_break_one_condition": q, "expected_breaks_per_M": n_cond * q,
                             "p_at_least_one_break_per_M": 1.0 - (1.0 - q) ** n_cond})
        both = 1.0 - ((1.0 - q_exact["alpha"]) * (1.0 - q_exact["alpha_prime"])) ** n_cond
        rows.append({"candidates": label, "n_datasets": n, "conditions_per_M": n_cond, "alpha": "both",
                     "true_rate_over_nominal": 1.0, "p_at_least_one_break_per_M": both})
    t = pd.DataFrame(rows)
    exact = t[(t.true_rate_over_nominal == 1.0) & (t.alpha == "both") & (t.candidates.str.startswith("analytic"))]
    p_fail = float(exact["p_at_least_one_break_per_M"].iloc[0])
    doc = {"registered": "PREREG_PHASE_9_ADDENDUM.md 3", "table": json.loads(t.to_json(orient="records")),
           "exactly_sized_test_fails_rule_per_M_analytic": p_fail,
           "rule_unmeetable_by_construction": bool(p_fail > 0.5),
           "note": "an exactly sized test at both alphas; conditions independent; Wilson 95 % lower limit",
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    t.to_csv(os.path.join(OUT, "rule_check.csv"), index=False)
    json.dump(doc, open(os.path.join(OUT, "rule_check.json"), "w", encoding="utf-8"), indent=1)
    print(t.round(4).to_string(index=False))
    print("an exactly sized analytic test breaks the rule at a given M with probability", round(p_fail, 3),
          "-> unmeetable by construction:", doc["rule_unmeetable_by_construction"])


# ============================================================================ E9.3 `criteria` (PREREG 3.2, addendum 9)
CRIT_MS = (6, 10, 14)
CRIT_SS = (19, 47, 93)
CRIT_LS = (1, 2, 6, 12)                 # P9-6's six parameters at two non-default levels each is L = 12
N_CRIT = 2_000                          # addendum 9.5: a condition carries L + 1 matrices, not one
CHUNK_CRIT = 250
CRIT_CONF = 0.90                        # plan 13.3 (iii): a 90 % interval


def crit_conditions(inp) -> List[dict]:
    d = inp["delta"]
    margin = 0.5 * d                                                 # addendum 9.4: half of min_effect, read not typed
    return [{"M": M, "S": S, "L": L, "tau_lam_label": tl, "tau_lam": tv, "beta_label": bl, "beta": bv,
             "int_label": il, "interaction": iv * margin, "margin": margin}
            for M in CRIT_MS for S in CRIT_SS for L in CRIT_LS
            for tl, tv in (("0", 0.0), ("half_limit", 0.5 * inp["flash_limit"]))
            for bl, bv in (("0", 0.0), ("half_delta", 0.5 * d), ("delta", d))
            for il, iv in (("0", 0.0), ("margin", 1.0))]


def crit_key(c) -> str:
    return (f"M{c['M']}_S{c['S']}_L{c['L']}_taulam{c['tau_lam_label']}_beta{c['beta_label']}_int{c['int_label']}")


def draw_levels(rng, n: int, c: dict, inp) -> np.ndarray:
    """(n, L + 1, M, S) seed-level memory - static differences, level 0 the default (addendum 9.1).

    The model x arm term is drawn ONCE and shared by every level (the same model runs at all of them); the path,
    persona x path and replicate terms are drawn AFRESH per level (a generator parameter changes the path a seed
    produces); the level x arm x model term is drawn independently at every level, the default included."""
    M, S, L = c["M"], c["S"], c["L"]
    bd = rng.normal(0.0, inp["flash_limit"], size=(n, M))            # the DIFFERENCE's sd is tau (3.1's convention)
    out = np.empty((n, L + 1, M, S))
    for lev in range(L + 1):
        t = draw_arm_terms(rng, n, M, S, 0.0, False, False, inp)     # tau 0: the model x arm term is added below
        beta_l = c["beta"] + (c["interaction"] if lev > 0 else 0.0)
        D = D_from_terms(t, beta_l) + bd[:, :, None]
        if c["tau_lam"] > 0:
            D = D + rng.normal(0.0, c["tau_lam"], size=(n, M))[:, :, None]
        out[:, lev] = D
    return out


def bh_rows(p: np.ndarray) -> np.ndarray:
    """BH q-values along axis 1, one family per row -- `tools.stats_v2.bh_adjust` vectorised over datasets
    (proved equal in tests/test_v2_1_phase_9.py::test_bh_rows_equals_stats_v2)."""
    n, m = p.shape
    order = np.argsort(p, axis=1)
    ps = np.take_along_axis(p, order, axis=1)
    q = ps * m / np.arange(1, m + 1)[None, :]
    q = np.minimum.accumulate(q[:, ::-1], axis=1)[:, ::-1]
    out = np.empty_like(q)
    np.put_along_axis(out, order, q, axis=1)
    return np.clip(out, 0.0, 1.0)


def crit_stats(Dl: np.ndarray, c: dict) -> Dict[str, np.ndarray]:
    """The three criteria per dataset, at the shape of `Dl` (n, L + 1, M, S)."""
    n, lp1, M, S = Dl.shape
    est = Dl.mean(axis=(2, 3))                                       # (n, L + 1) the contrast at each level
    p = np.column_stack([analytic(Dl[:, lev])["p_R5"] for lev in range(lp1)])
    # (i) the sign criterion, both readings of addendum 9.2
    s0, sl = np.sign(est[:, :1]), np.sign(est[:, 1:])
    flip = sl != s0
    sig = p[:, 1:] <= ALPHA
    # (ii) BH over the L + 1 level tests of one conclusion
    q = bh_rows(p)
    # (iii) the interaction, estimated per model and differenced (addendum 9.4)
    rm = Dl.mean(axis=3)                                             # (n, L + 1, M) per-model means
    d = rm[:, 1:, :] - rm[:, :1, :]                                  # (n, L, M)
    ihat = d.mean(axis=2)
    ise = d.std(axis=2, ddof=1) / math.sqrt(M)
    half = stats.t.ppf(0.5 + CRIT_CONF / 2.0, M - 1) * ise
    lo, hi = ihat - half, ihat + half
    inside = (lo >= -c["margin"]) & (hi <= c["margin"])
    return {"level_dependent_plain": flip.any(axis=1), "level_dependent_significant_only": (flip & sig).any(axis=1),
            "ii_holds_alpha": (q <= ALPHA).all(axis=1), "ii_holds_alpha_prime": (q <= ALPHA_PRIME).all(axis=1),
            "equivalence_declared": inside.all(axis=1), "equivalence_any_level": inside.any(axis=1),
            "interaction_half_width": half.mean(axis=1), "interaction_est": ihat.mean(axis=1),
            "est_default": est[:, 0]}


def _crit_task(args):
    c, inp = args
    f = os.path.join(CACHE, f"criteria_{crit_key(c)}.parquet")
    if os.path.exists(f):
        return f
    rng = np.random.default_rng([9, 3, 6, zlib.crc32(crit_key(c).encode())])   # a stream no other stage draws from
    parts = []
    for start in range(0, N_CRIT, CHUNK_CRIT):
        n = min(CHUNK_CRIT, N_CRIT - start)
        parts.append(pd.DataFrame(crit_stats(draw_levels(rng, n, c, inp), c)))
    pd.concat(parts, ignore_index=True).to_parquet(f, index=False)
    return f


def summarise_criteria(c: dict, t: pd.DataFrame) -> dict:
    r = {k: v for k, v in c.items()}
    r["n_datasets"] = len(t)
    for col in ("level_dependent_plain", "level_dependent_significant_only", "ii_holds_alpha",
                "ii_holds_alpha_prime", "equivalence_declared", "equivalence_any_level"):
        p, lo, hi = wilson(int(t[col].sum()), len(t))
        r[col], r[f"{col}_lo"], r[f"{col}_hi"] = p, lo, hi
    r["interaction_half_width_median"] = float(t["interaction_half_width"].median())
    r["half_width_over_margin"] = r["interaction_half_width_median"] / c["margin"]
    r["interaction_est_mean"] = float(t["interaction_est"].mean())
    return r


def stage_criteria(workers: int):
    """PREREG_PHASE_9.md 3.2 with the constructions of addendum 9: the sign criterion's false level-dependent rate,
    the model-level test at every level under BH, and the equivalence interval's power and false-equivalence rate,
    over the shapes the design may take."""
    inp = inputs()
    os.makedirs(CACHE, exist_ok=True)
    conds = crit_conditions(inp)
    _run_pool([(c, inp) for c in conds], _crit_task, workers, "criteria")
    s = pd.DataFrame([summarise_criteria(c, pd.read_parquet(os.path.join(CACHE, f"criteria_{crit_key(c)}.parquet")))
                      for c in conds])
    os.makedirs(OUT, exist_ok=True)
    s.to_csv(os.path.join(OUT, "criteria.csv"), index=False)
    # what the stage is for: the shapes at which a criterion cannot be met (addendum 9.6)
    null = s[(s.int_label == "0") & (s.beta_label != "0")]
    at_margin = s[s.int_label == "margin"]
    doc = {"registered": ["PREREG_PHASE_9.md 3.2", "PREREG_PHASE_9_ADDENDUM.md 9"], "inputs": inp,
           "margin": 0.5 * inp["delta"], "alpha": ALPHA, "alpha_prime": ALPHA_PRIME, "n_datasets": N_CRIT,
           "conf": CRIT_CONF, "n_conditions": len(s),
           "sign_criterion_false_level_dependent_max": float(null["level_dependent_plain"].max()),
           "sign_criterion_false_level_dependent_max_significant_only": float(null["level_dependent_significant_only"].max()),
           "equivalence_power_at_zero_max": float(s[(s.int_label == "0")]["equivalence_declared"].max()),
           "equivalence_power_at_zero_min": float(s[(s.int_label == "0")]["equivalence_declared"].min()),
           "false_equivalence_at_margin_max": float(at_margin["equivalence_declared"].max()),
           "shapes_with_zero_equivalence_power": json.loads(
               s[(s.int_label == "0") & (s.equivalence_declared_hi < 0.01)][
                   ["M", "S", "L", "tau_lam_label", "beta_label", "equivalence_declared",
                    "half_width_over_margin"]].to_json(orient="records")),
           "table": json.loads(s.to_json(orient="records")),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(OUT, "criteria.json"), "w", encoding="utf-8"), indent=1)
    print(f"[criteria] {len(s)} conditions written; false level-dependent rate (plain, beta > 0, true interaction 0) "
          f"max {doc['sign_criterion_false_level_dependent_max']:.3f}; equivalence power at a true interaction of 0 "
          f"ranges {doc['equivalence_power_at_zero_min']:.3f}-{doc['equivalence_power_at_zero_max']:.3f}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="bridge,refdist,refdist_boot,recommend")
    ap.add_argument("--workers", type=int, default=7)
    a = ap.parse_args(argv)
    for st in [x.strip() for x in a.stages.split(",") if x.strip()]:
        if st == "bridge":
            if stage_bridge(a.workers) != 0:
                return 2
        elif st == "refdist":
            stage_refdist(a.workers)
        elif st == "refdist_boot":
            stage_refdist_boot(a.workers)
        elif st == "recommend":
            stage_recommend()
        elif st == "refdist_fresh":
            stage_refdist_fresh(a.workers)
        elif st == "rule_check":
            stage_rule_check()
        elif st == "criteria":
            stage_criteria(a.workers)
        else:
            raise SystemExit(f"unknown stage {st!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
