"""
v2.1 Phase 8 -- E8.3's validation on simulated data with known answers, BEFORE any real contrast
(PREREG_PHASE_8.md 3.8).  Staged and resumable; each stage its own files.

    python -u -m tools.phase8.e8_3_simulate --stages paths,mixed,recovery,multiplicity,null --workers 7 [--datasets 300]

(a) `mixed`     -- the mixed model and the intervals.  Estimators: E0 the v2 `tools.stats_v2.mixed_effects` (seeds
                   nested in models, intercepts only), E1 the crossed model of PREREG 3.2 (implemented here first --
                   the simulation is built before stats_v2 is touched), E2 the two-way pigeonhole cluster bootstrap
                   of 3.3, E3 the v2 run-level `bootstrap_ci`.  Size at beta = 0, power at beta = 0.05, with Wilson
                   intervals; E1's variance components against the planted; boundary shares.  The path effect is REAL:
                   the per-(scenario, seed, persona) band-MAS of the level-free observables oracle in
                   `e7_rescore/cells.parquet` at theta 0.05, half-width 0.10, centred within scenario x persona.
(a') `recovery` -- a large all-Gaussian design in E1's own parameterisation (M = 12, S = 20): the 5th-95th
                   percentile band of each estimated component over 100 datasets, which `test_mixed_model_crossed`
                   reads (a derived band, not a typed tolerance).
(b) `multiplicity` -- z-statistics with tier C's correlation measured on the same cell frame with e7_8's construction;
                   FDR / power / FWER for the v2 procedure, BH within family, BY across.
(c) `null`      -- AR(1) daily series at phi in {0.90, 0.97, 0.99, phi_pilot}; N0 circular shift of window means
                   (v2), N1 permutation of window means, N2 day-block permutation with a random offset, N3 the
                   path-level sign-flip of paired trend differences.

Outputs: docs/env_v2/generated/v2_1/e8_3/{paths.json, mixed.{csv,json}, recovery_band.json, multiplicity.{csv,json},
null.{csv,json}} and per-condition caches under e8_3/_cache/.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from typing import Dict, List

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e8_3")
CACHE = os.path.join(OUT, "_cache")
CELLS = os.path.join(GEN, "e7_rescore", "cells.parquet")
PATH_POLICY = "L5_full_level_free"          # the level-free observables oracle; verified against Phase 7's published mean
PUBLISHED_CHECK = {"scenario": "flat", "theta": 0.05, "half_width": 0.10, "mcr": 0.0770}   # PHASE_7_REPORT.md section 2
PERSONAS = ("ENTJ", "INTJ", "ISFJ")         # sorted: ENTJ is the treatment-coding reference in E0 and E1
SCEN = ("bull_trap", "flat")                # sorted: bull_trap is the reference scenario
ALPHA = 0.05
SIGMA_M, SIGMA_EPS = 0.05, 0.03             # DESIGN values for the simulation (PREREG 3.8), on the pilot's sigma_d scale
BETA_POWER = 0.05                           # D12
N_BOOT_E2 = 1999
N_BOOT_E3 = 1000


def wilson(k: int, n: int, z: float = 1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, c - h, c + h)


# ============================================================================================ real path effects
def stage_paths():
    cols = ["scenario", "seed", "persona", "policy", "theta", "half_width", "band_mas", "mcr", "mcr_D"]
    t = pd.read_parquet(CELLS, columns=cols)
    t["scenario"] = t["scenario"].astype(str)
    chk = t[(t.policy == PATH_POLICY) & (t.scenario == PUBLISHED_CHECK["scenario"]) & np.isclose(t.theta, PUBLISHED_CHECK["theta"])
            & np.isclose(t.half_width, PUBLISHED_CHECK["half_width"])]["mcr"].mean()
    if round(float(chk), 4) != PUBLISHED_CHECK["mcr"]:
        raise SystemExit(f"{PATH_POLICY} flat MCR at theta 0.05 is {chk:.4f}, not the published observables-oracle "
                         f"{PUBLISHED_CHECK['mcr']}: the label is not the observables oracle")
    sel = t[(t.policy == PATH_POLICY) & np.isclose(t.theta, 0.05) & np.isclose(t.half_width, 0.10) & t.scenario.isin(SCEN)]
    out = {}
    for (sc, p), g in sel.groupby(["scenario", "persona"], observed=True):
        v = g.sort_values("seed")["band_mas"].to_numpy(float)
        out[f"{sc}|{p}"] = {"mean": float(v.mean()), "centred": (v - v.mean()).tolist(), "sd": float(v.std(ddof=1)), "n": int(len(v))}
    os.makedirs(OUT, exist_ok=True)
    json.dump({"policy": PATH_POLICY, "published_check": {**PUBLISHED_CHECK, "measured": float(chk)}, "paths": out},
              open(os.path.join(OUT, "paths.json"), "w", encoding="utf-8"))
    print("paths: policy", PATH_POLICY, "check", round(float(chk), 4), {k: round(v["sd"], 4) for k, v in out.items()})


def _paths():
    return json.load(open(os.path.join(OUT, "paths.json"), encoding="utf-8"))["paths"]


# ============================================================================================ data-generating process
def simulate(rng, M, S, R, beta, s_ma, rho, paths, gaussian_paths: float = 0.0, interaction: bool = False,
             s_m: float = SIGMA_M, s_eps: float = SIGMA_EPS) -> pd.DataFrame:
    """One dataset.  Arms static/memory, 3 personas, 2 scenarios, S paths per scenario, M models, R replicates.
    Model: (u_m, slope_m) bivariate normal (sd s_m, s_ma, corr rho), slope on memory -- or, if `interaction`, an iid
    N(0, s_ma^2) effect per (model, arm) level, E1's own parameterisation.  Path effect: the real centred band-MAS per
    (scenario, seed, persona), or, if `gaussian_paths` > 0, a N(0, gaussian_paths^2) intercept shared by personas."""
    rows = []
    cov = np.array([[s_m ** 2, rho * s_m * s_ma], [rho * s_m * s_ma, s_ma ** 2]])
    uv = rng.multivariate_normal([0.0, 0.0], cov, size=M) if s_ma > 0 else np.column_stack([rng.normal(0, s_m, M), np.zeros(M)])
    inter = rng.normal(0, s_ma, size=(M, 2)) if interaction else None
    for c in SCEN:
        idx = rng.choice(100, S, replace=False)
        gp = rng.normal(0, gaussian_paths, S) if gaussian_paths > 0 else None
        for p in PERSONAS:
            info = paths[f"{c}|{p}"]
            w = gp if gp is not None else np.asarray(info["centred"])[idx]
            for m in range(M):
                for k in range(S):
                    for a, arm in enumerate(("static", "memory")):
                        mu = info["mean"] + w[k] + uv[m, 0] + (inter[m, a] if interaction else uv[m, 1] * a) + beta * a
                        for r in range(R):
                            rows.append((f"m{m}", p, arm, c, k, f"{c}|{k}", r, mu + rng.normal(0, s_eps)))
    return pd.DataFrame(rows, columns=["Model", "Persona", "Arm", "Scenario", "Seed", "Path", "Decode_Replicate", "y"])


# ============================================================================================ estimators
def fit_e0(d: pd.DataFrame) -> Dict[str, float]:
    from tools.stats_v2 import mixed_effects
    t = mixed_effects(d.rename(columns={"y": "m"}).assign(Crash_Discount=0.7), "m")
    row = t[t.term == "Arm[T.memory]"]
    if row.empty or not np.isfinite(row["p"].iloc[0]):
        return {"e0_p": float("nan"), "e0_coef": float("nan"), "e0_ok": False}
    return {"e0_p": float(row["p"].iloc[0]), "e0_coef": float(row["coef"].iloc[0]), "e0_ok": True}


def fit_e1(d: pd.DataFrame) -> Dict[str, float]:
    """PREREG 3.2, implemented here first."""
    import statsmodels.formula.api as smf
    vc = {"model": "0 + C(Model)", "model_arm": "0 + C(Model):C(Arm)", "path": "0 + C(Path)"}
    if d["Decode_Replicate"].nunique() > 1:
        vc["path_arm"] = "0 + C(Path):C(Arm)"
    try:
        md = smf.mixedlm("y ~ C(Arm, Treatment('static')) * C(Persona) * C(Scenario)", d, groups=np.ones(len(d)),
                         re_formula="0", vc_formula=vc)
        r = md.fit(reml=True, method="lbfgs", maxiter=400)
        name = "C(Arm, Treatment('static'))[T.memory]"
        out = {"e1_p": float(r.pvalues[name]), "e1_coef": float(r.params[name]), "e1_se": float(r.bse[name]),
               "e1_converged": bool(r.converged), "e1_ok": True, "e1_scale": float(r.scale)}
        for nm, v in zip(r.model.exog_vc.names, np.asarray(r.vcomp, float)):
            out[f"e1_vc_{nm}"] = float(v)
        return out
    except Exception as e:                                   # noqa: BLE001
        return {"e1_p": float("nan"), "e1_ok": False, "e1_error": f"{type(e).__name__}: {str(e)[:80]}"}


def paired_cell(d: pd.DataFrame, persona="ENTJ", scenario="bull_trap"):
    """(model x path) matrix of replicate-mean memory - static in one contrast cell."""
    g = d[(d.Persona == persona) & (d.Scenario == scenario)].groupby(["Model", "Path", "Arm"])["y"].mean().unstack("Arm")
    diff = (g["memory"] - g["static"]).unstack("Path")
    return diff.to_numpy(float)


def e2_pigeonhole(D: np.ndarray, rng, n_boot=N_BOOT_E2):
    """Two-way cluster bootstrap by model and path (PREREG 3.3): weights = model draw counts x path draw counts."""
    M, S = D.shape
    wm = rng.multinomial(M, np.full(M, 1.0 / M), size=n_boot).astype(float)
    ws = rng.multinomial(S, np.full(S, 1.0 / S), size=n_boot).astype(float)
    num = np.einsum("bm,ms,bs->b", wm, D, ws)
    den = wm.sum(1) * ws.sum(1)
    stat = num / den
    lo, hi = np.percentile(stat, [2.5, 97.5])
    return float(D.mean()), float(lo), float(hi)


def e3_run_bootstrap(d: pd.DataFrame, persona="ENTJ", scenario="bull_trap", seed=0):
    from tools.stats_v2 import bootstrap_ci, cliffs_delta
    c = d[(d.Persona == persona) & (d.Scenario == scenario)]
    a = c[c.Arm == "memory"]["y"].to_numpy(); b = c[c.Arm == "static"]["y"].to_numpy()
    lo, hi = bootstrap_ci(a, b, cliffs_delta, N_BOOT_E3, seed=seed)
    return float(cliffs_delta(a, b)), float(lo), float(hi)


def conditions() -> List[dict]:
    out = []
    for M in (3, 6):
        for S in (5, 10):
            for s_ma, rho in ((0.0, 0.0), (0.03, 0.0), (0.03, 0.5)):
                for beta in (0.0, BETA_POWER):
                    out.append({"M": M, "S": S, "R": 1, "s_ma": s_ma, "rho": rho, "beta": beta})
    for beta in (0.0, BETA_POWER):
        out.append({"M": 6, "S": 5, "R": 3, "s_ma": 0.03, "rho": 0.0, "beta": beta})
    return out


def cond_key(c):
    return f"M{c['M']}_S{c['S']}_R{c['R']}_sma{c['s_ma']}_rho{c['rho']}_beta{c['beta']}"


def _mixed_task(args):
    c, i = args
    warnings.filterwarnings("ignore")
    paths = _paths()
    rng = np.random.default_rng([8, 3, abs(hash(cond_key(c))) % (2 ** 31), i])
    d = simulate(rng, c["M"], c["S"], c["R"], c["beta"], c["s_ma"], c["rho"], paths)
    t0 = time.time()
    out = {"cond": cond_key(c), "i": i, **c}
    out.update(fit_e0(d)); out["t_e0"] = time.time() - t0
    t1 = time.time(); out.update(fit_e1(d)); out["t_e1"] = time.time() - t1
    m, lo, hi = e2_pigeonhole(paired_cell(d), np.random.default_rng([9, i]))
    out.update({"e2_est": m, "e2_lo": lo, "e2_hi": hi, "e2_reject": bool(lo > 0 or hi < 0),
                "e2_covers": bool(lo <= c["beta"] <= hi)})
    dl, dlo, dhi = e3_run_bootstrap(d, seed=i)
    out.update({"e3_delta": dl, "e3_lo": dlo, "e3_hi": dhi, "e3_reject": bool(dlo > 0 or dhi < 0)})
    return out


def _run_pool(tasks, fn, workers):
    if workers <= 1:
        return [fn(t) for t in tasks]
    from multiprocessing import Pool
    with Pool(workers) as pool:
        return list(pool.imap_unordered(fn, tasks, chunksize=1))


def stage_mixed(n_datasets: int, workers: int):
    os.makedirs(CACHE, exist_ok=True)
    for c in conditions():
        f = os.path.join(CACHE, f"mixed_{cond_key(c)}.csv")
        if os.path.exists(f) and os.path.getsize(f) > 0 and len(pd.read_csv(f)) >= n_datasets:
            print("cached", cond_key(c), flush=True); continue
        t0 = time.time()
        res = _run_pool([(c, i) for i in range(n_datasets)], _mixed_task, workers)
        pd.DataFrame(res).sort_values("i").to_csv(f, index=False)
        print(f"{cond_key(c)}: {n_datasets} datasets in {time.time() - t0:.0f}s", flush=True)
    summarise_mixed()


def summarise_mixed():
    rows = []
    for c in conditions():
        f = os.path.join(CACHE, f"mixed_{cond_key(c)}.csv")
        if not os.path.exists(f):
            continue
        t = pd.read_csv(f)
        n = len(t)
        r = {**c, "n_datasets": n}
        for e in ("e0", "e1"):
            ok = t[f"{e}_ok"].astype(bool)
            k = int(((t[f"{e}_p"] <= ALPHA) & ok).sum())
            p, lo, hi = wilson(k, n)
            r.update({f"{e}_reject": p, f"{e}_reject_lo": lo, f"{e}_reject_hi": hi, f"{e}_fit_fail": int((~ok).sum())})
        for e in ("e2", "e3"):
            k = int(t[f"{e}_reject"].astype(bool).sum())
            p, lo, hi = wilson(k, n)
            r.update({f"{e}_reject": p, f"{e}_reject_lo": lo, f"{e}_reject_hi": hi})
        r["e2_coverage"] = float(t["e2_covers"].mean())
        if "e1_converged" in t:
            r["e1_nonconverged"] = int((~t["e1_converged"].fillna(False).astype(bool)).sum())
        for nm in ("model", "model_arm", "path", "path_arm"):
            col = f"e1_vc_{nm}"
            if col in t:
                v = t[col].dropna()
                r[f"e1_vc_{nm}_median"] = float(v.median()) if len(v) else float("nan")
                r[f"e1_vc_{nm}_at_boundary"] = float((v < 1e-8).mean()) if len(v) else float("nan")
        r["planted_model_var"] = SIGMA_M ** 2
        r["planted_slope_var"] = c["s_ma"] ** 2
        r["planted_resid_var"] = SIGMA_EPS ** 2
        r["t_e1_median_s"] = float(t["t_e1"].median())
        rows.append(r)
    s = pd.DataFrame(rows)
    s.to_csv(os.path.join(OUT, "mixed.csv"), index=False)
    # the adoption rule (PREREG 3.8(a)): size holds iff the Wilson interval of the size contains 0.05 or lies below
    verdict = {}
    for e in ("e0", "e1", "e2", "e3"):
        sz = s[s.beta == 0.0]
        verdict[e] = {cond_key(dict(r)): bool(r[f"{e}_reject_lo"] <= ALPHA) for _, r in sz.iterrows()}
    json.dump({"alpha": ALPHA, "planted": {"sigma_M": SIGMA_M, "sigma_eps": SIGMA_EPS, "beta_power": BETA_POWER},
               "path_policy": PATH_POLICY, "size_holds": verdict, "table": json.loads(s.to_json(orient="records"))},
              open(os.path.join(OUT, "mixed.json"), "w", encoding="utf-8"), indent=1)
    show = ["M", "S", "R", "s_ma", "rho", "beta", "n_datasets", "e0_reject", "e1_reject", "e2_reject", "e3_reject",
            "e2_coverage", "e1_fit_fail", "e1_vc_model_arm_at_boundary", "t_e1_median_s"]
    print(s[[c for c in show if c in s]].round(3).to_string(index=False))


# ============================================================================================ (a'') UNREGISTERED sensitivity
# Added after `paths` showed that the registered real path effect is almost empty: the observables oracle's band-MAS
# has an sd of 0.0003-0.0005 across seeds within scenario x persona (it rarely leaves its band), ~100x below the
# planted replicate noise, so the registered conditions barely exercise path clustering.  This stage plants a
# Gaussian path intercept at the recovery design's sd (0.04), shared by personas.  Disclosed as unregistered in
# PREREG_PHASE_8_ADDENDUM.md; it adds conditions, it replaces none.
GPATH_SD = 0.04


def gpath_conditions() -> List[dict]:
    return [{"M": M, "S": 10, "R": 1, "s_ma": s_ma, "rho": 0.0, "beta": beta, "gpath": GPATH_SD}
            for M in (3, 6) for s_ma in (0.0, 0.03) for beta in (0.0, BETA_POWER)]


def _gpath_task(args):
    c, i = args
    warnings.filterwarnings("ignore")
    rng = np.random.default_rng([8, 4, abs(hash(cond_key(c) + "gpath")) % (2 ** 31), i])
    d = simulate(rng, c["M"], c["S"], c["R"], c["beta"], c["s_ma"], c["rho"], _paths(), gaussian_paths=c["gpath"])
    out = {"cond": cond_key(c), "i": i, **c}
    out.update(fit_e0(d)); out.update(fit_e1(d))
    m, lo, hi = e2_pigeonhole(paired_cell(d), np.random.default_rng([9, 4, i]))
    out.update({"e2_est": m, "e2_lo": lo, "e2_hi": hi, "e2_reject": bool(lo > 0 or hi < 0), "e2_covers": bool(lo <= c["beta"] <= hi)})
    dl, dlo, dhi = e3_run_bootstrap(d, seed=i)
    out.update({"e3_delta": dl, "e3_lo": dlo, "e3_hi": dhi, "e3_reject": bool(dlo > 0 or dhi < 0), "t_e1": 0.0})
    return out


def stage_mixed_gpath(n_datasets: int, workers: int):
    os.makedirs(CACHE, exist_ok=True)
    rows = []
    for c in gpath_conditions():
        f = os.path.join(CACHE, f"gpath_{cond_key(c)}.csv")
        if not (os.path.exists(f) and len(pd.read_csv(f)) >= n_datasets):
            t0 = time.time()
            pd.DataFrame(_run_pool([(c, i) for i in range(n_datasets)], _gpath_task, workers)).sort_values("i").to_csv(f, index=False)
            print(f"gpath {cond_key(c)}: {n_datasets} datasets in {time.time() - t0:.0f}s", flush=True)
        t = pd.read_csv(f)
        r = {**c, "n_datasets": len(t)}
        for e in ("e0", "e1"):
            ok = t[f"{e}_ok"].astype(bool)
            p, lo, hi = wilson(int(((t[f"{e}_p"] <= ALPHA) & ok).sum()), len(t))
            r.update({f"{e}_reject": p, f"{e}_reject_lo": lo, f"{e}_reject_hi": hi})
        for e in ("e2", "e3"):
            p, lo, hi = wilson(int(t[f"{e}_reject"].astype(bool).sum()), len(t))
            r.update({f"{e}_reject": p, f"{e}_reject_lo": lo, f"{e}_reject_hi": hi})
        r["e2_coverage"] = float(t["e2_covers"].mean())
        for nm in ("model", "model_arm", "path"):
            v = t.get(f"e1_vc_{nm}")
            if v is not None:
                r[f"e1_vc_{nm}_median"] = float(v.dropna().median())
        rows.append(r)
    s = pd.DataFrame(rows)
    s.to_csv(os.path.join(OUT, "mixed_gpath.csv"), index=False)
    json.dump({"registered": False, "reason": "the registered real path effect is ~100x below the replicate noise",
               "gpath_sd": GPATH_SD, "table": json.loads(s.to_json(orient="records"))},
              open(os.path.join(OUT, "mixed_gpath.json"), "w", encoding="utf-8"), indent=1)
    print(s[["M", "s_ma", "beta", "e0_reject", "e1_reject", "e2_reject", "e3_reject", "e2_coverage"]].round(3).to_string(index=False))


# ============================================================================================ (a''') UNREGISTERED: persona x path
# Added after E8.5 measured Flash's band-MAS variance sitting in persona x path (ICC 0.82) and persona x path x arm
# (0.11) -- components no E8.3 condition planted and E1 does not carry; on Flash's own rows E1's arm SE is 2.27x the
# paired SE at R = 1.  The components are READ from e8_5/components_reml_persona_path.json and the seed count from
# e8_5/power.json, never typed.  Its adoption rule was fixed in PREREG_PHASE_8_ADDENDUM.md 17 before this stage ran.
PP_COMPONENTS_FILE = os.path.join(GEN, "e8_5", "components_reml_persona_path.json")
PP_POWER_FILE = os.path.join(GEN, "e8_5", "power.json")
PP_ALPHA_BONF = ALPHA / 36                          # m(Q1, C) for E8.5's cell structure (PREREG 5.5)


def _pp_components() -> Dict[str, float]:
    return json.load(open(PP_COMPONENTS_FILE, encoding="utf-8"))["band_mas"]["components"]


def _pp_seeds() -> int:
    return int(json.load(open(PP_POWER_FILE, encoding="utf-8"))["sized_band_mas"]["1"]["appA_bonf"])


def pp_conditions() -> List[dict]:
    S = _pp_seeds()
    return [{"M": M, "S": S, "R": 1, "s_ma": s_ma, "rho": 0.0, "beta": beta, "shared": shared}
            for shared in (True, False) for M in (3, 6) for s_ma in (0.0, 0.03) for beta in (0.0, BETA_POWER)]


def pp_key(c) -> str:
    return cond_key(c) + ("_shared" if c["shared"] else "_modelspecific")


def simulate_pp(rng, M, S, R, beta, s_ma, shared, comp, paths) -> pd.DataFrame:
    """One dataset with E8.5's five measured components: path and path x arm (shared by personas and models), persona x
    path and persona x path x arm (shared by models if `shared`, else drawn per model), replicate noise.  Model
    intercept sd SIGMA_M and an iid model x arm effect of sd s_ma (E1's parameterisation); cell means as `simulate`."""
    sd = {k: float(np.sqrt(max(float(v), 0.0))) for k, v in comp.items()}
    u = rng.normal(0, SIGMA_M, M)
    inter = rng.normal(0, s_ma, size=(M, 2)) if s_ma > 0 else np.zeros((M, 2))
    n_draw = 1 if shared else M
    rows = []
    for c in SCEN:
        for k in range(S):
            pth, pa = rng.normal(0, sd["path"]), rng.normal(0, sd["path_arm"], 2)
            for p in PERSONAS:
                mean = paths[f"{c}|{p}"]["mean"]
                pp = rng.normal(0, sd["persona_path"], n_draw)
                ppa = rng.normal(0, sd["persona_path_arm"], (n_draw, 2))
                for m in range(M):
                    j = 0 if shared else m
                    for a, arm in enumerate(("static", "memory")):
                        mu = mean + pth + pa[a] + pp[j] + ppa[j, a] + u[m] + inter[m, a] + beta * a
                        for r in range(R):
                            rows.append((f"m{m}", p, arm, c, k, f"{c}|{k}", r, mu + rng.normal(0, sd["replicate"])))
    return pd.DataFrame(rows, columns=["Model", "Persona", "Arm", "Scenario", "Seed", "Path", "Decode_Replicate", "y"])


FIT_METHODS = ("lbfgs", "powell")


def _fit_best(md, maxiter: int = 400):
    """REML by lbfgs and by Powell; the fit with the higher restricted log-likelihood is kept.  On a difference-model
    dataset with no model variance planted, lbfgs reported convergence at a local optimum (REML log-likelihood 1300.6,
    model component 0.00069, SE 0.0114) that Powell and Nelder-Mead escaped (1309.9, 0.0, 0.0037); addendum 17.
    Returns (result, winning method, {method: llf})."""
    best, best_m, info = None, None, {}
    for m in FIT_METHODS:
        try:
            r = md.fit(reml=True, method=m, maxiter=maxiter if m == "lbfgs" else 4 * maxiter)
        except Exception:                                    # noqa: BLE001 -- the other method may still fit
            continue
        info[m] = float(r.llf)
        if best is None or (np.isfinite(r.llf) and r.llf > best.llf):
            best, best_m = r, m
    if best is None:
        raise RuntimeError("no REML fit returned")
    return best, best_m, info


def fit_e1_best(d: pd.DataFrame) -> Dict[str, float]:
    """E1 exactly as registered (fit_e1's formula and components) at the better of the two optima (E1-best)."""
    import statsmodels.formula.api as smf
    vc = {"model": "0 + C(Model)", "model_arm": "0 + C(Model):C(Arm)", "path": "0 + C(Path)"}
    if d["Decode_Replicate"].nunique() > 1:
        vc["path_arm"] = "0 + C(Path):C(Arm)"
    try:
        md = smf.mixedlm("y ~ C(Arm, Treatment('static')) * C(Persona) * C(Scenario)", d, groups=np.ones(len(d)),
                         re_formula="0", vc_formula=vc)
        r, meth, info = _fit_best(md)
        name = "C(Arm, Treatment('static'))[T.memory]"
        return {"e1b_p": float(r.pvalues[name]), "e1b_coef": float(r.params[name]), "e1b_se": float(r.bse[name]),
                "e1b_converged": bool(r.converged), "e1b_ok": True, "e1b_method": meth,
                "e1b_llf_gap": info.get("powell", np.nan) - info.get("lbfgs", np.nan)}
    except Exception as e:                                   # noqa: BLE001
        return {"e1b_p": float("nan"), "e1b_ok": False, "e1b_error": f"{type(e).__name__}: {str(e)[:80]}"}


def fit_e1_amended(d: pd.DataFrame) -> Dict[str, float]:
    """E1-amended (addendum 17): E1 fitted on the seed-level differences dy = replicate-mean(memory) - replicate-mean(
    static) per (model, persona, path) -- the pairing P8-1 fixes and the plug-ins use.  Fixed effects C(Persona) *
    C(Scenario), so the intercept is the memory - static effect in the reference cell (E1's estimand); variance
    components model (= model x arm), path (= path x arm) and persona x path (= persona x path x arm).  Every persona x
    path and model x persona x path intercept cancels in the difference, shared across models or not.  (A first form
    that added those intercepts to E1 on the runs took 425-516 s per fit and did not always converge; addendum 17.)"""
    import statsmodels.formula.api as smf
    g = d.groupby(["Model", "Persona", "Scenario", "Path", "Arm"], observed=True)["y"].mean().unstack("Arm")
    dd = (g["memory"] - g["static"]).rename("dy").reset_index()
    dd["PP"] = dd["Persona"].astype(str) + "|" + dd["Path"].astype(str)
    vc = {"model": "0 + C(Model)", "path": "0 + C(Path)", "persona_path": "0 + C(PP)"}
    try:
        r, meth, info = _fit_best(smf.mixedlm("dy ~ C(Persona) * C(Scenario)", dd, groups=np.ones(len(dd)),
                                              re_formula="0", vc_formula=vc))
        name = "Intercept"
        out = {"e1a_p": float(r.pvalues[name]), "e1a_coef": float(r.params[name]), "e1a_se": float(r.bse[name]),
               "e1a_converged": bool(r.converged), "e1a_ok": True, "e1a_method": meth,
               "e1a_llf_gap": info.get("powell", np.nan) - info.get("lbfgs", np.nan)}
        for nm, v in zip(r.model.exog_vc.names, np.asarray(r.vcomp, float)):
            out[f"e1a_vc_{nm}"] = float(v)
        return out
    except Exception as e:                                   # noqa: BLE001
        return {"e1a_p": float("nan"), "e1a_ok": False, "e1a_error": f"{type(e).__name__}: {str(e)[:80]}"}


def _pp_task(args):
    import zlib
    c, i, comp = args
    warnings.filterwarnings("ignore")
    rng = np.random.default_rng([8, 5, zlib.crc32(pp_key(c).encode()), i])
    d = simulate_pp(rng, c["M"], c["S"], c["R"], c["beta"], c["s_ma"], c["shared"], comp, _paths())
    out = {"cond": pp_key(c), "i": i, **c}
    t0 = time.time(); out.update(fit_e1(d)); out["t_e1"] = time.time() - t0
    t2 = time.time(); out.update(fit_e1_best(d)); out["t_e1b"] = time.time() - t2
    t1 = time.time(); out.update(fit_e1_amended(d)); out["t_e1a"] = time.time() - t1
    m, lo, hi = e2_pigeonhole(paired_cell(d), np.random.default_rng([9, 5, zlib.crc32(pp_key(c).encode()), i]))
    out.update({"e2_est": m, "e2_lo": lo, "e2_hi": hi, "e2_reject": bool(lo > 0 or hi < 0), "e2_covers": bool(lo <= c["beta"] <= hi)})
    return out


def stage_mixed_pp(n_datasets: int, workers: int):
    os.makedirs(CACHE, exist_ok=True)
    comp = _pp_components()
    rows = []
    for c in pp_conditions():
        f = os.path.join(CACHE, f"pp_{pp_key(c)}.csv")
        if not (os.path.exists(f) and len(pd.read_csv(f)) >= n_datasets):
            t0 = time.time()
            pd.DataFrame(_run_pool([(c, i, comp) for i in range(n_datasets)], _pp_task, workers)).sort_values("i").to_csv(f, index=False)
            print(f"pp {pp_key(c)}: {n_datasets} datasets in {time.time() - t0:.0f}s", flush=True)
        t = pd.read_csv(f)
        r = {**c, "n_datasets": len(t)}
        for e in ("e1", "e1b", "e1a"):
            ok = t[f"{e}_ok"].astype(bool)
            if f"{e}_llf_gap" in t:
                r[f"{e}_lbfgs_local_share"] = float((t[f"{e}_llf_gap"] > 1.0).mean())
            for lab, a in (("", ALPHA), ("_bonf", PP_ALPHA_BONF)):
                p, lo, hi = wilson(int(((t[f"{e}_p"] <= a) & ok).sum()), len(t))
                r.update({f"{e}_reject{lab}": p, f"{e}_reject{lab}_lo": lo, f"{e}_reject{lab}_hi": hi})
            r[f"{e}_fit_fail"] = int((~ok).sum())
            r[f"{e}_se_median"] = float(t[f"{e}_se"].median()) if f"{e}_se" in t else float("nan")
            r[f"{e}_coef_sd"] = float(t[f"{e}_coef"].std(ddof=1)) if f"{e}_coef" in t else float("nan")
            r[f"{e}_se_over_sd"] = r[f"{e}_se_median"] / r[f"{e}_coef_sd"] if r[f"{e}_coef_sd"] > 0 else float("nan")
            r[f"{e}_nonconverged"] = int((~t[f"{e}_converged"].fillna(False).astype(bool)).sum()) if f"{e}_converged" in t else -1
        p, lo, hi = wilson(int(t["e2_reject"].astype(bool).sum()), len(t))
        r.update({"e2_reject": p, "e2_reject_lo": lo, "e2_reject_hi": hi, "e2_coverage": float(t["e2_covers"].mean())})
        r["t_e1a_median_s"] = float(t["t_e1a"].median())
        rows.append(r)
    s = pd.DataFrame(rows)
    s.to_csv(os.path.join(OUT, "mixed_pp.csv"), index=False)
    # the rule of addendum 17: at M = 6, in both readings and both model x arm settings, (a) E1-amended's size holds and
    # (b) its power at alpha' is not below the registered E1's
    m6 = s[s.M == 6]
    size_ok = {pp_key(dict(r)): bool(r["e1a_reject_lo"] <= ALPHA) for _, r in m6[m6.beta == 0.0].iterrows()}
    pw = m6[m6.beta == BETA_POWER]
    power_ok = {pp_key(dict(r)): bool(r["e1a_reject_bonf"] >= r["e1_reject_bonf"]) for _, r in pw.iterrows()}
    adopt = bool(size_ok) and all(size_ok.values()) and bool(power_ok) and all(power_ok.values())
    json.dump({"registered": False, "addendum": 17, "components": comp, "seeds": int(s["S"].iloc[0]) if len(s) else None,
               "alpha": ALPHA, "alpha_bonferroni": PP_ALPHA_BONF, "size_holds_M6": size_ok, "power_not_below_M6": power_ok,
               "adopt_e1_amended": adopt, "table": json.loads(s.to_json(orient="records"))},
              open(os.path.join(OUT, "mixed_pp.json"), "w", encoding="utf-8"), indent=1)
    show = ["shared", "M", "s_ma", "beta", "n_datasets", "e1_reject", "e1_reject_bonf", "e1b_reject", "e1b_reject_bonf",
            "e1a_reject", "e1a_reject_bonf", "e2_reject", "e1_se_over_sd", "e1b_se_over_sd", "e1a_se_over_sd",
            "e1b_lbfgs_local_share", "e1a_lbfgs_local_share", "e1a_fit_fail", "t_e1a_median_s"]
    print(s[[c for c in show if c in s]].round(3).to_string(index=False))
    print("adopt E1-amended:", adopt, "| size", size_ok, "| power", power_ok)


def stage_optimizer_example():
    """The dataset that exposed lbfgs's local optimum (addendum 17), kept as a file: E1-amended's difference model on one
    model-specific dataset (M = 6, the sized seeds, model x arm sd 0, generator seed [8, 5, 0, 0]) fitted by five
    optimizers, and a moment (two-way ANOVA without replication) estimate on the reference cell beside.
    -> e8_3/optimizer_example.json"""
    import statsmodels.formula.api as smf
    comp = _pp_components()
    S = _pp_seeds()
    d = simulate_pp(np.random.default_rng([8, 5, 0, 0]), 6, S, 1, 0.0, 0.0, False, comp, _paths())
    g = d.groupby(["Model", "Persona", "Scenario", "Path", "Arm"], observed=True)["y"].mean().unstack("Arm")
    dd = (g["memory"] - g["static"]).rename("dy").reset_index()
    dd["PP"] = dd["Persona"].astype(str) + "|" + dd["Path"].astype(str)
    vc = {"model": "0 + C(Model)", "path": "0 + C(Path)", "persona_path": "0 + C(PP)"}
    md = smf.mixedlm("dy ~ C(Persona) * C(Scenario)", dd, groups=np.ones(len(dd)), re_formula="0", vc_formula=vc)
    fits = {}
    for method in ("lbfgs", "powell", "nm", "bfgs", "cg"):
        try:
            r = md.fit(reml=True, method=method, maxiter=2000)
            fits[method] = {"llf": float(r.llf), "converged": bool(r.converged), "residual": float(r.scale),
                            "se_intercept": float(r.bse["Intercept"]),
                            "vc": dict(zip(r.model.exog_vc.names, map(float, r.vcomp)))}
        except Exception as e:                               # noqa: BLE001
            fits[method] = {"error": f"{type(e).__name__}: {str(e)[:80]}"}
        print(method, fits[method], flush=True)
    c = dd[(dd.Persona == PERSONAS[0]) & (dd.Scenario == SCEN[0])].pivot(index="Model", columns="Path", values="dy").to_numpy()
    M, P = c.shape
    gm = c.mean()
    ms_m = P * ((c.mean(1) - gm) ** 2).sum() / (M - 1)
    ms_p = M * ((c.mean(0) - gm) ** 2).sum() / (P - 1)
    res = c - c.mean(1, keepdims=True) - c.mean(0, keepdims=True) + gm
    ms_e = (res ** 2).sum() / ((M - 1) * (P - 1))
    anova = {"model_var": float((ms_m - ms_e) / P), "path_var": float((ms_p - ms_e) / M), "residual": float(ms_e),
             "planted_residual_2_ppa_plus_rep": float(2 * (comp["persona_path_arm"] + comp["replicate"]))}
    print("ANOVA reference cell", anova)
    json.dump({"registered": False, "addendum": 17, "dataset": {"M": 6, "S": S, "R": 1, "s_ma": 0.0, "beta": 0.0,
               "reading": "model-specific", "generator_seed": [8, 5, 0, 0]}, "fits": fits, "anova_reference_cell": anova},
              open(os.path.join(OUT, "optimizer_example.json"), "w", encoding="utf-8"), indent=1)


def stage_mixed_tref():
    """POST HOC (addendum 17), computed after the normal-reference rates of `mixed_pp` and `mixed_optimizer` were read:
    the same cached estimates and SEs referred to a t distribution with M - 1 df, the model-level degrees of freedom
    that bound every arm contrast when the arm effect varies by model.  No refit; adopts nothing; for Phase 9's
    pre-registration."""
    from scipy import stats as st
    rows = []
    for kind, conds, keyf, prefix in (("pp", pp_conditions(), pp_key, "pp_"), ("opt", OPT_CONDITIONS, cond_key, "opt_")):
        for c in conds:
            f = os.path.join(CACHE, f"{prefix}{keyf(c)}.csv")
            if not os.path.exists(f):
                continue
            t = pd.read_csv(f)
            r = {"cache": kind, **c, "n_datasets": len(t)}
            for e in ("e1", "e1b", "e1a"):
                if f"{e}_coef" not in t:
                    continue
                se = t[f"{e}_se"].astype(float)
                ok = t[f"{e}_ok"].astype(bool) & np.isfinite(se) & (se > 0)
                p = 2 * st.t.sf((t[f"{e}_coef"].astype(float) / se).abs(), c["M"] - 1)
                for lab, a in (("", ALPHA), ("_bonf", PP_ALPHA_BONF)):
                    pr, lo, hi = wilson(int(((p <= a) & ok).sum()), len(t))
                    r.update({f"{e}_t_reject{lab}": pr, f"{e}_t_reject{lab}_lo": lo, f"{e}_t_reject{lab}_hi": hi})
            rows.append(r)
    s = pd.DataFrame(rows)
    json.dump({"registered": False, "post_hoc": True, "addendum": 17, "reference": "t with M - 1 df on |coef / SE|",
               "note": "computed after the normal-reference rates were read; adopts nothing",
               "table": json.loads(s.to_json(orient="records"))},
              open(os.path.join(OUT, "mixed_tref_posthoc.json"), "w", encoding="utf-8"), indent=1)
    show = ["cache", "shared", "M", "S", "s_ma", "beta", "e1_t_reject", "e1_t_reject_lo", "e1b_t_reject", "e1b_t_reject_lo",
            "e1a_t_reject", "e1a_t_reject_lo", "e1_t_reject_bonf", "e1a_t_reject_bonf"]
    print(s[[c for c in show if c in s]].round(3).to_string(index=False))


# the optimizer on E8.3's own conditions (addendum 17): how often does lbfgs stop at a local optimum, and does it flip E1's decision?
OPT_CONDITIONS = [{"M": M, "S": 10, "R": 1, "s_ma": 0.03, "rho": 0.0, "beta": beta} for M in (3, 6) for beta in (0.0, BETA_POWER)]


def _opt_task(args):
    import zlib
    c, i = args
    warnings.filterwarnings("ignore")
    rng = np.random.default_rng([8, 6, zlib.crc32(cond_key(c).encode()), i])
    d = simulate(rng, c["M"], c["S"], c["R"], c["beta"], c["s_ma"], c["rho"], _paths())
    return {"cond": cond_key(c), "i": i, **c, **fit_e1(d), **fit_e1_best(d)}


def stage_mixed_optimizer(n_datasets: int, workers: int):
    os.makedirs(CACHE, exist_ok=True)
    rows = []
    for c in OPT_CONDITIONS:
        f = os.path.join(CACHE, f"opt_{cond_key(c)}.csv")
        if not (os.path.exists(f) and len(pd.read_csv(f)) >= n_datasets):
            t0 = time.time()
            pd.DataFrame(_run_pool([(c, i) for i in range(n_datasets)], _opt_task, workers)).sort_values("i").to_csv(f, index=False)
            print(f"opt {cond_key(c)}: {n_datasets} datasets in {time.time() - t0:.0f}s", flush=True)
        t = pd.read_csv(f)
        both = t["e1_ok"].astype(bool) & t["e1b_ok"].astype(bool)
        r = {**c, "n_datasets": len(t), "lbfgs_local_share": float((t["e1b_llf_gap"] > 1.0).mean()),
             "llf_gap_max": float(t["e1b_llf_gap"].max()),
             "decision_flips": int(((t["e1_p"] <= ALPHA) != (t["e1b_p"] <= ALPHA))[both].sum())}
        for e in ("e1", "e1b"):
            p, lo, hi = wilson(int(((t[f"{e}_p"] <= ALPHA) & t[f"{e}_ok"].astype(bool)).sum()), len(t))
            r.update({f"{e}_reject": p, f"{e}_reject_lo": lo, f"{e}_reject_hi": hi})
        rows.append(r)
    s = pd.DataFrame(rows)
    json.dump({"registered": False, "addendum": 17, "methods": list(FIT_METHODS), "local_optimum_rule": "llf(powell) - llf(lbfgs) > 1",
               "table": json.loads(s.to_json(orient="records"))},
              open(os.path.join(OUT, "mixed_optimizer.json"), "w", encoding="utf-8"), indent=1)
    print(s.round(3).to_string(index=False))


# ============================================================================================ (a') recovery band
RECOVERY ={"M": 12, "S": 20, "R": 1, "s_m": 0.05, "s_ma": 0.03, "s_path": 0.04, "s_eps": 0.03, "beta": 0.05}


def _recovery_task(i):
    warnings.filterwarnings("ignore")
    c = RECOVERY
    d = simulate(np.random.default_rng([8, 12, i]), c["M"], c["S"], c["R"], c["beta"], c["s_ma"], 0.0, _paths(),
                 gaussian_paths=c["s_path"], interaction=True, s_m=c["s_m"], s_eps=c["s_eps"])
    return {"i": i, **fit_e1(d)}


def stage_recovery(n: int, workers: int):
    f = os.path.join(CACHE, "recovery.csv")
    os.makedirs(CACHE, exist_ok=True)
    if not (os.path.exists(f) and len(pd.read_csv(f)) >= n):
        t0 = time.time()
        pd.DataFrame(_run_pool(list(range(n)), _recovery_task, workers)).sort_values("i").to_csv(f, index=False)
        print(f"recovery: {n} datasets in {time.time() - t0:.0f}s", flush=True)
    t = pd.read_csv(f)
    planted = {"model": RECOVERY["s_m"] ** 2, "model_arm": RECOVERY["s_ma"] ** 2, "path": RECOVERY["s_path"] ** 2,
               "residual": RECOVERY["s_eps"] ** 2}
    band = {}
    for nm in ("model", "model_arm", "path"):
        v = t[f"e1_vc_{nm}"].dropna()
        band[nm] = {"planted": planted[nm], "p05": float(v.quantile(0.05)), "p50": float(v.median()),
                    "p95": float(v.quantile(0.95)), "n": int(len(v)),
                    "planted_inside_p05_p95": bool(v.quantile(0.05) <= planted[nm] <= v.quantile(0.95))}
    v = t["e1_scale"].dropna()
    band["residual"] = {"planted": planted["residual"], "p05": float(v.quantile(0.05)), "p50": float(v.median()),
                        "p95": float(v.quantile(0.95)), "n": int(len(v)),
                        "planted_inside_p05_p95": bool(v.quantile(0.05) <= planted["residual"] <= v.quantile(0.95))}
    k = int((t["e1_p"] <= ALPHA).sum())
    doc = {"design": RECOVERY, "band": band, "power_at_beta": wilson(k, len(t)),
           "test_seed": [8, 12, 10_000], "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(doc, open(os.path.join(OUT, "recovery_band.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(band, indent=1))


# ============================================================================================ (b) multiplicity
def tier_c_correlation() -> Dict:
    """Tier C's correlation with E7.8's OWN construction (rule 13, P6-7): a cell is scenario x persona x policy, the
    metric is its mean over seeds (`tools/phase7/e7_8_validity._cell_frame`), at half-width 0.10 and the exact theta.
    The first draft of this stage correlated the 60,000 seed-level rows instead and read |r|(band-MAS, D) = 0.033
    against E7.8's 0.069; that run is superseded and disclosed (PREREG_PHASE_8_ADDENDUM.md).  The check below refuses
    to proceed unless the band-MAS--D pair reproduces `e7_8/matrix.json`."""
    from tools.phase7.e7_8_validity import _abs_corr, _cell_frame
    cols = ["scenario", "seed", "persona", "policy", "theta", "half_width", "band_mas", "mcr_D"]
    t = pd.read_parquet(CELLS, columns=cols)
    t["policy"] = t["policy"].astype(str)
    t = t[t["half_width"] == 0.10]
    key = ["scenario", "persona", "policy"]
    a = _cell_frame(t[t["theta"] == 0.05], ["band_mas", "mcr_D"]).set_index(key).rename(columns={"mcr_D": "D_0.05"})
    b = _cell_frame(t[t["theta"] == 0.002], ["mcr_D"]).set_index(key).rename(columns={"mcr_D": "D_0.002"})
    j = a.join(b, how="inner")
    names = list(j.columns)
    C = np.eye(len(names))
    for i in range(len(names)):
        for k in range(i + 1, len(names)):
            r = _abs_corr(j[names[i]].to_numpy(float), j[names[k]].to_numpy(float))
            sign = np.sign(np.corrcoef(j[names[i]], j[names[k]])[0, 1])
            C[i, k] = C[k, i] = sign * r
    mx = json.load(open(os.path.join(GEN, "e7_8", "matrix.json"), encoding="utf-8"))["A_decomposition"]["matrix"]
    ref = mx.get("band_mas|mcr_D", mx.get("mcr_D|band_mas"))
    if ref is None or abs(abs(C[0, 1]) - ref) > 1e-12:
        raise SystemExit(f"tier C's |r|(band-MAS, D at 0.05) = {abs(C[0, 1]):.6f} does not reproduce e7_8/matrix.json ({ref}); "
                         f"the construction differs from E7.8's")
    return {"names": names, "corr": C.tolist(), "n_cells": int(len(j)), "construction": "E7.8 _cell_frame (means over seeds)",
            "check_band_mas_D_0.05_abs_r": float(abs(C[0, 1])), "e7_8_reference": float(ref)}


def bh(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg rejections (boolean) at ALPHA along the last axis."""
    n = p.shape[-1]
    order = np.argsort(p, axis=-1)
    ps = np.take_along_axis(p, order, -1)
    crit = ALPHA * np.arange(1, n + 1) / n
    below = ps <= crit
    kmax = np.where(below.any(-1), n - np.argmax(below[..., ::-1], -1), 0)
    rej_sorted = np.arange(n) < kmax[..., None]
    out = np.zeros_like(rej_sorted)
    np.put_along_axis(out, order, rej_sorted, -1)
    return out


def by(p: np.ndarray) -> np.ndarray:
    n = p.shape[-1]
    c = np.sum(1.0 / np.arange(1, n + 1))
    return bh(np.minimum(p * c, 1.0))


def stage_multiplicity(reps: int = 5000):
    from scipy import stats
    tc = tier_c_correlation()
    C = np.asarray(tc["corr"])
    L = np.linalg.cholesky(C)
    grids = {"e8_5": {"Q1": 1 * 3 * 4},                                     # contrast cells per family
             "reviewer": {"Q1": 2 * 3 * 5, "Q2": 2 * 3 * 5, "Q3": 3 * 3 * 5, "Q4": 1 * 3 * 5}}
    rng = np.random.default_rng(88)
    rows = []
    for gname, fams in grids.items():
        cells = sum(fams.values())
        fam_of_cell = np.concatenate([[i] * n for i, n in enumerate(fams.values())])
        for pi1 in (0.0, 0.1, 0.3):
            V = {"v2": [], "bh_within": [], "by_across": []}
            TP = {k: [] for k in V}; FW = {k: [] for k in V}
            for _ in range(reps):
                z = rng.standard_normal((cells, 3)) @ L.T
                nonnull = rng.random((cells, 3)) < pi1
                z = z + 3.0 * nonnull
                p = 2 * stats.norm.sf(np.abs(z))
                rej = {"v2": bh(p)}                                            # BH across the metrics within a contrast cell
                r_fam = np.zeros_like(nonnull)
                for f in range(len(fams)):
                    sel = fam_of_cell == f
                    r_fam[sel] = bh(p[sel].reshape(1, -1)).reshape(-1, 3)
                rej["bh_within"] = r_fam
                rej["by_across"] = by(p.reshape(1, -1)).reshape(-1, 3)
                for k, rr in rej.items():
                    nr = rr.sum(); fp = (rr & ~nonnull).sum(); tp = (rr & nonnull).sum()
                    V[k].append(fp / max(nr, 1)); FW[k].append(fp > 0)
                    TP[k].append(tp / nonnull.sum() if nonnull.sum() else np.nan)
            for k in V:
                fdr = float(np.mean(V[k])); mc = 1.96 * float(np.std(V[k], ddof=1)) / np.sqrt(reps)
                rows.append({"grid": gname, "families": json.dumps(fams), "n_tests": cells * 3, "pi1": pi1, "procedure": k,
                             "fdr": fdr, "fdr_mc_halfwidth": mc, "fwer": float(np.mean(FW[k])),
                             "power": float(np.nanmean(TP[k])) if pi1 > 0 else float("nan"),
                             "fdr_holds": bool(fdr <= ALPHA + mc)})
    s = pd.DataFrame(rows)
    s.to_csv(os.path.join(OUT, "multiplicity.csv"), index=False)
    json.dump({"tier_c": tc, "reps": reps, "shift": 3.0, "table": json.loads(s.to_json(orient="records"))},
              open(os.path.join(OUT, "multiplicity.json"), "w", encoding="utf-8"), indent=1)
    print("tier C |r|:", np.round(np.abs(C), 3).tolist(), "n cells", tc["n_cells"])
    print(s.round(4).to_string(index=False))


# ============================================================================================ (c) the temporal null
W, NW, T = 25, 8, 200
_J = np.arange(NW) - (NW - 1) / 2
_CW = _J / np.sum(_J ** 2)                                  # OLS slope of window means on window index = CW . means


def phi_pilot() -> Dict:
    import glob
    phis = []
    for f in glob.glob(os.path.join(ROOT, "results_v2_pilot", "main", "*", "*", "*", "*.csv")):
        c = pd.read_csv(f, usecols=["Day", "Cash_Share"])
        if len(c) < T:
            continue
        x = c.sort_values("Day")["Cash_Share"].to_numpy(float)
        x = x - x.mean()
        den = np.sum(x * x)
        if den > 0:
            phis.append(float(np.sum(x[1:] * x[:-1]) / den))
    return {"median": float(np.median(phis)), "n_runs": len(phis), "p10": float(np.percentile(phis, 10)),
            "p90": float(np.percentile(phis, 90)), "note": "lag-1 autocorrelation of daily Cash_Share, pilot main T = 200 runs"}


def ar1(rng, n, phi):
    e = rng.standard_normal((n, T))
    y = np.empty((n, T))
    y[:, 0] = e[:, 0] / np.sqrt(max(1 - phi ** 2, 1e-12))
    for t in range(1, T):
        y[:, t] = phi * y[:, t - 1] + e[:, t]
    return y


def slopes_of(y):
    return (y.reshape(y.shape[0], NW, W).mean(2)) @ _CW


def null_p(y, rng, kind, n_draw=999):
    obs = slopes_of(y).mean()
    n = y.shape[0]
    if kind == "N0":
        m = y.reshape(n, NW, W).mean(2)
        k = rng.integers(1, NW, size=(n_draw, n))
        idx = (np.arange(NW)[None, None, :] + k[..., None]) % NW
        null = (np.take_along_axis(np.broadcast_to(m, (n_draw, n, NW)), idx, 2) @ _CW).mean(1)
    elif kind == "N1":
        m = y.reshape(n, NW, W).mean(2)
        idx = np.argsort(rng.random((n_draw, n, NW)), axis=2)
        null = (np.take_along_axis(np.broadcast_to(m, (n_draw, n, NW)), idx, 2) @ _CW).mean(1)
    elif kind == "N2":
        # rotate each run's days by a random offset in [0, 24] (y[(t + off) % T], i.e. np.roll(y, -off)), cut into eight
        # 25-day blocks, permute the blocks; vectorised over draws and runs
        off = rng.integers(0, W, size=(n_draw, n))
        idx = (np.arange(T)[None, None, :] + off[..., None]) % T
        yy = np.take_along_axis(np.broadcast_to(y, (n_draw, n, T)), idx, 2)
        m = yy.reshape(n_draw, n, NW, W).mean(3)
        perm = np.argsort(rng.random((n_draw, n, NW)), axis=2)
        null = (np.take_along_axis(m, perm, 2) @ _CW).mean(1)
    else:
        raise ValueError(kind)
    return float((np.sum(np.abs(null) >= abs(obs)) + 1) / (n_draw + 1))


def signflip_p(diff, rng, n_draw=999):
    obs = diff.mean()
    s = rng.choice([-1.0, 1.0], size=(n_draw, len(diff)))
    null = (s * diff).mean(1)
    return float((np.sum(np.abs(null) >= abs(obs)) + 1) / (n_draw + 1))


def stage_null(reps: int = 1000):
    pp = phi_pilot()
    phis = [0.90, 0.97, 0.99, round(pp["median"], 4)]
    rng = np.random.default_rng(1234)
    rows = []
    for phi in phis:
        for n_runs in (3, 36):
            rej = {"N0": 0, "N1": 0, "N2": 0, "N3": 0}
            t0 = time.time()
            for _ in range(reps):
                y = ar1(rng, n_runs, phi)
                for k in ("N0", "N1", "N2"):
                    rej[k] += null_p(y, rng, k) <= ALPHA
                a, b = ar1(rng, n_runs, phi), ar1(rng, n_runs, phi)   # stateful vs stateless on the same path, no trend difference
                rej["N3"] += signflip_p(slopes_of(a) - slopes_of(b), rng) <= ALPHA
            for k, v in rej.items():
                p, lo, hi = wilson(int(v), reps)
                rows.append({"phi": phi, "phi_is_pilot": phi == phis[-1], "n_runs": n_runs, "null": k, "size": p,
                             "size_lo": lo, "size_hi": hi, "size_holds": bool(lo <= ALPHA), "reps": reps})
            print(f"phi {phi} n_runs {n_runs}: " + ", ".join(f"{k} {v / reps:.3f}" for k, v in rej.items()) +
                  f" ({time.time() - t0:.0f}s)", flush=True)
    s = pd.DataFrame(rows)
    s.to_csv(os.path.join(OUT, "null.csv"), index=False)
    exact_n0_values = NW                                         # one run: the circular shift has at most 8 rotations
    json.dump({"phi_pilot": pp, "reps": reps, "draws": 999, "exact_N0_distinct_values_per_run": exact_n0_values,
               "min_p_N0_one_run_exact": 1.0 / NW, "table": json.loads(s.to_json(orient="records"))},
              open(os.path.join(OUT, "null.json"), "w", encoding="utf-8"), indent=1)
    print(s.round(3).to_string(index=False))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="paths,mixed,recovery,multiplicity,null")
    ap.add_argument("--datasets", type=int, default=300)
    ap.add_argument("--recovery", type=int, default=100)
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--null-reps", type=int, default=1000)
    ap.add_argument("--mult-reps", type=int, default=5000)
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    for st in [s.strip() for s in a.stages.split(",") if s.strip()]:
        t0 = time.time()
        if st == "paths":
            stage_paths()
        elif st == "mixed":
            stage_mixed(a.datasets, a.workers)
        elif st == "summary":
            summarise_mixed()
        elif st == "mixed_gpath":
            stage_mixed_gpath(a.datasets, a.workers)
        elif st == "mixed_pp":
            stage_mixed_pp(a.datasets, a.workers)
        elif st == "mixed_optimizer":
            stage_mixed_optimizer(a.datasets, a.workers)
        elif st == "mixed_tref":
            stage_mixed_tref()
        elif st == "optimizer_example":
            stage_optimizer_example()
        elif st == "recovery":
            stage_recovery(a.recovery, a.workers)
        elif st == "multiplicity":
            stage_multiplicity(a.mult_reps)
        elif st == "null":
            stage_null(a.null_reps)
        else:
            raise SystemExit(f"unknown stage {st}")
        print(f"[stage {st}] {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
