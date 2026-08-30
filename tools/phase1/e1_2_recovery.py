"""
E1.2: estimator C on the data (light SMM, PREREG_PHASE_1.md section 4.3) and REG-5's simulation-recovery study
(section 4.4) for estimators A, B, C.

Recovery panels: 100 stocks x 6,300 days from tools/phase1/calm_sim (equivalence-checked) with known h in {30, 60, 120,
150, 250, 500} d x sigma_V in {0.006, 0.012}, sbar 0.017; V_hat = V exp(m) sampled quarterly, m an AR(1) with the FIT
stationary sd (median sd of log EPS_ttm growth, e1_2/misc_fits.json) and persistence bracketed {0, 0.9} per quarter
(DESIGN). Replications: A and B 200, C 50. Usability: median |h_hat - h| / h < 0.20 and 95 % interval coverage >= 0.90
(A, B; C's coverage is not measured in the study).

    python -m tools.phase1.e1_2_recovery [--workers 8] [--reps-ab 200] [--reps-c 50]
Outputs: docs/env_v2/generated/v2_1/e1_2/recovery.json, recovery.md, smm_fit.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy.optimize import minimize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "1")

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_2")
HS = (30, 60, 120, 150, 250, 500, 5, 10)   # ADDENDUM section 6.1: h = 5, 10 d appended (cell seeds of the original six unchanged)
SVS = (0.006, 0.012)
SBAR = 0.017
N_STOCKS, T_DAYS = 100, 6300
KS_A = (5, 10, 20, 60, 120, 250, 500)
N_BOOT_REC = 200
RHO_M = (0.0, 0.9)
# reference pilot constants of the default engine (PHASE_0 phase0_numbers.json): phi = ln2 / (h mu n_bar)
N_BAR_REF, W_BAR_REF, MU_FW = 0.9976485039121478, 0.7611251383007557, 0.01
SMM_PATHS, SMM_T, SMM_BURN = 20, 5000, 500


def phi_of_h(h: float) -> float:
    return np.log(2.0) / (h * MU_FW * N_BAR_REF)


# ------------------------------------------------------------------------------------------ estimator A on a panel
def est_A(logP: np.ndarray, n_boot: int = N_BOOT_REC, seed: int = 0):
    from tools.phase1.e1_2_vr import vr_moments, fit
    R = np.diff(logP, axis=0)
    M = vr_moments(R, KS_A)
    pooled = M.mean(axis=0)
    rng = np.random.default_rng(seed)
    N = M.shape[0]
    idxs = rng.integers(0, N, (n_boot, N))
    bp = np.stack([M[i].mean(axis=0) for i in idxs])
    w = 1.0 / np.maximum(bp.var(axis=0, ddof=1), 1e-30)
    point = fit(pooled, w, KS_A)
    hs = np.array([fit(b, w, KS_A, starts=[np.array(point["theta"])])["h"] for b in bp])
    return point, (float(np.percentile(hs, 2.5)), float(np.percentile(hs, 97.5)))


# ------------------------------------------------------------------------------------------ estimator B on a panel
def est_B(x: np.ndarray, sd_m: float, rho_m: float, tab, rng: np.random.Generator, n_boot: int = N_BOOT_REC):
    """x: (T, N) daily mispricing; monthly sampling every 21 days; V_hat measurement error m updated quarterly."""
    from tools.phase1.e1_2_pv import ols_rho, median_unbiased
    T, N = x.shape
    months = np.arange(0, T, 21)
    xm = x[months]                                     # (Tm, N)
    Tm = len(months)
    # quarterly AR(1) error with stationary sd sd_m, held within the quarter
    nq = Tm // 3 + 2
    m = np.zeros((nq, N)); m[0] = rng.normal(0, sd_m, N)
    inn = sd_m * np.sqrt(1 - rho_m ** 2)
    for q in range(1, nq):
        m[q] = rho_m * m[q - 1] + rng.normal(0, inn, N)
    u = xm - m[np.arange(Tm) // 3]
    rho = ols_rho(u)
    h = np.array([-np.log(2) / np.log(median_unbiased(float(r), Tm, tab)) * 21 if 0 < r < 1 else np.inf for r in rho])
    h = np.where(np.isfinite(h), h, np.nan)
    med = float(np.nanmedian(h))
    boots = np.array([np.nanmedian(h[rng.integers(0, N, N)]) for _ in range(n_boot)])
    return med, (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))


# ------------------------------------------------------------------------------------------ estimator C (light SMM)
def smm_fit(target: np.ndarray, w: np.ndarray, seed: int = 777, starts=None):
    from tools.phase1.calm_sim import simulate, calm_moments
    def sim_moments(theta):
        sv, sb, h = np.exp(theta)
        out = simulate(SMM_PATHS, SMM_T, h=h, sigma_V=sv, sbar=sb, seed=seed, burn=SMM_BURN, phi=phi_of_h(h), w_bar=W_BAR_REF)
        return calm_moments(out["logP"])
    def J(theta):
        m = sim_moments(theta)
        return float(((m - target) ** 2 * w).sum())
    starts = starts or [np.log([0.006, 0.017, 150.0]), np.log([0.012, 0.017, 60.0]), np.log([0.004, 0.012, 300.0]), np.log([0.010, 0.025, 120.0])]
    best = None
    for s0 in starts:
        r = minimize(J, s0, method="Nelder-Mead", options={"xatol": 2e-3, "fatol": 1e-9, "maxiter": 160, "maxfev": 160})
        if best is None or r.fun < best.fun:
            best = r
    sv, sb, h = np.exp(best.x)
    return {"sigma_V": float(sv), "sbar": float(sb), "s_x": float(sb / 0.017 * 0.1752), "h": float(h), "J": float(best.fun), "nfev": int(best.nfev)}


# ------------------------------------------------------------------------------------------ recovery cells
def cell_job(args):
    import warnings
    warnings.filterwarnings("ignore")
    from tools.phase1.calm_sim import simulate, calm_moments
    which, h, sv, rep, sd_m, tab = args
    seed = 90000 + (HS.index(h) * 2 + SVS.index(sv)) * 1000 + rep
    out = simulate(N_STOCKS, T_DAYS, h=h, sigma_V=sv, sbar=SBAR, seed=seed, burn=500, phi=phi_of_h(h), w_bar=W_BAR_REF)
    res = {"h": h, "sigma_V": sv, "rep": rep}
    if which in ("A", "AB"):
        p, ci = est_A(out["logP"], seed=seed)
        res["A"] = {"h": p["h"], "ci": ci, "sigma_V": p["sigma_V"], "s_x": p["s_x"]}
    if which in ("B", "AB"):
        rng = np.random.default_rng(seed + 1)
        for rho_m in RHO_M:
            med, ci = est_B(out["x"], sd_m, rho_m, tab, rng)
            res[f"B_rho{rho_m}"] = {"h": med, "ci": ci}
    if which == "C":
        # data-side moments of this synthetic panel with a stock-bootstrap diagonal weight (as on the real data)
        M = calm_moments(out["logP"])
        rng = np.random.default_rng(seed + 2)
        boots = np.stack([calm_moments(out["logP"][:, rng.integers(0, N_STOCKS, N_STOCKS)]) for _ in range(30)])
        w = 1.0 / np.maximum(boots.var(axis=0, ddof=1), 1e-30)
        f = smm_fit(M, w, seed=777 + rep, starts=[np.log([sv, SBAR, h * 0.7]), np.log([sv * 1.5, SBAR, h * 1.5])])
        res["C"] = {"h": f["h"], "sigma_V": f["sigma_V"], "s_x": f["s_x"], "J": f["J"]}
    return res


def _refit(args):
    import warnings
    warnings.filterwarnings("ignore")
    M, w, start = args
    return smm_fit(M, w, seed=777, starts=[np.log(start)])


def usability(rows, key, truth_key="h"):
    errs = np.array([abs(r[key]["h"] - r[truth_key]) / r[truth_key] for r in rows if np.isfinite(r[key]["h"])])
    cov = [r[key]["ci"][0] <= r[truth_key] <= r[key]["ci"][1] for r in rows if "ci" in r[key]]
    hs = np.array([r[key]["h"] for r in rows if np.isfinite(r[key]["h"])])
    return {"n": int(len(rows)), "median_rel_error": float(np.median(errs)) if len(errs) else float("nan"),
            "rmse_rel": float(np.sqrt(np.mean(errs ** 2))) if len(errs) else float("nan"),
            "median_h_hat": float(np.median(hs)) if len(hs) else float("nan"),
            "coverage": float(np.mean(cov)) if cov else None,
            "usable": bool(len(errs) and np.median(errs) < 0.20 and (not cov or np.mean(cov) >= 0.90))}


def data_moments(n_boot: int = 200):
    """Set-A calm moments and their stock-bootstrap resamples (the SMM data side). Cached in e1_2/smm_data_moments.json so
    that the fit can run on a machine without the panel (the moments are derived statistics, not the third-party data)."""
    from tools.phase1.calm_sim import calm_moments
    path = os.path.join(OUT, "smm_data_moments.json")
    if os.path.exists(path):
        d = json.load(open(path, encoding="utf-8"))
        return np.array(d["moments"]), np.array(d["boots"])
    from tools.phase1.panel import analysis_sets, load_prices
    A = analysis_sets(write=False)["A"]
    lp = np.log(load_prices(A).ffill().to_numpy())
    lp = lp - lp[0]
    M = calm_moments(lp)
    rng = np.random.default_rng(3)
    boots = np.stack([calm_moments(lp[:, rng.integers(0, lp.shape[1], lp.shape[1])]) for _ in range(n_boot)])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"set": "A", "n_stocks": int(lp.shape[1]), "n_days": int(lp.shape[0]), "n_boot": n_boot, "seed": 3,
                   "moment_names": ["var1", "VR20", "VR60", "VR120", "VR250", "VR500", "acf20", "acf60", "acf120"],
                   "moments": M.tolist(), "boots": boots.tolist()}, fh)
    return M, boots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--reps-ab", type=int, default=200)
    ap.add_argument("--reps-c", type=int, default=50)
    ap.add_argument("--skip-data-smm", action="store_true")
    ap.add_argument("--c-hs", default=None, help="comma list of grid h values for the estimator-C cells (default: all; the achieved set is stated)")
    ap.add_argument("--ab-hs", default=None, help="comma list of grid h values for the A/B cells (default: all)")
    ap.add_argument("--n-boot-refits", type=int, default=30, help="bootstrap refits for the data-side SMM interval (30 pre-registered; the achieved count is stated)")
    a = ap.parse_args()
    t0 = time.time()
    misc = json.load(open(os.path.join(OUT, "misc_fits.json"), encoding="utf-8"))
    sd_m = float(misc["vhat_noise"]["sd_log_epsttm_growth_median"])
    z = np.load(os.path.join(OUT, "andrews_median_table.npz")); tab = {k: z[k] for k in ("T", "rho", "median")}
    # extend Andrews' table to the recovery panels' monthly length (T = 300) if needed
    Tm = T_DAYS // 21 + 1
    if abs(tab["T"] - Tm).min() > 20:
        from tools.phase1.e1_2_pv import ols_rho
        rng = np.random.default_rng(555)
        med = np.empty(len(tab["rho"]))
        for j, rho in enumerate(tab["rho"]):
            e = rng.standard_normal((Tm, 20000)); y = np.empty((Tm, 20000)); y[0] = e[0] / np.sqrt(1 - rho ** 2)
            for t in range(1, Tm):
                y[t] = rho * y[t - 1] + e[t]
            med[j] = np.median(ols_rho(y))
        tab = {"T": np.append(tab["T"], Tm), "rho": tab["rho"], "median": np.vstack([tab["median"], med])}
    cache_dir = os.path.join(OUT, "cache"); os.makedirs(cache_dir, exist_ok=True)
    c_hs = [int(x) for x in a.c_hs.split(",")] if a.c_hs else list(HS)
    ab_hs = [int(x) for x in a.ab_hs.split(",")] if a.ab_hs else list(HS)
    groups = [("AB", h, sv, a.reps_ab) for h in HS if h in ab_hs for sv in SVS] + [("C", h, sv, a.reps_c) for h in HS if h in c_hs for sv in SVS]
    print(f"{sum(g[3] for g in groups)} recovery jobs in {len(groups)} cells", flush=True)
    rows = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for kind, h, sv, reps in groups:   # resumable: one cache file per (estimator set, h, sigma_V) cell
            cache = os.path.join(cache_dir, f"{kind}_h{h}_sv{sv}.json")
            if os.path.exists(cache):
                rows += json.load(open(cache, encoding="utf-8")); print(f"{kind} h={h} sv={sv}: cached", flush=True); continue
            t1 = time.time()
            cell = list(ex.map(cell_job, [(kind, h, sv, r, sd_m, tab) for r in range(reps)], chunksize=2))
            json.dump(cell, open(cache, "w", encoding="utf-8"))
            rows += cell; print(f"{kind} h={h} sv={sv}: {reps} reps in {time.time() - t1:.0f} s", flush=True)
    print(f"recovery done {time.time() - t0:.0f} s", flush=True)
    table = {}
    for h in sorted(HS):
        for sv in SVS:
            cell = [r for r in rows if r["h"] == h and r["sigma_V"] == sv]
            ab = [r for r in cell if "A" in r]; c = [r for r in cell if "C" in r]
            if not ab:
                continue
            table[f"h{h}|sv{sv}"] = {"h": h, "sigma_V": sv, "A": usability(ab, "A"),
                                     **{f"B_rho{rm}": usability(ab, f"B_rho{rm}") for rm in RHO_M},
                                     "C": usability(c, "C") if c else None,
                                     "A_sigma_V_median": float(np.median([r["A"]["sigma_V"] for r in ab])),
                                     "C_sigma_V_median": float(np.median([r["C"]["sigma_V"] for r in c])) if c else None}
    res = {"design": {"n_stocks": N_STOCKS, "T_days": T_DAYS, "hs": HS, "sigma_Vs": SVS, "sbar": SBAR, "reps_AB": a.reps_ab, "reps_C": a.reps_c, "C_cells_h": c_hs, "n_boot_refits_data": a.n_boot_refits,
                      "vhat_noise_sd": sd_m, "rho_m_bracket": RHO_M, "n_boot_interval": N_BOOT_REC,
                      "phi_rule": "phi = ln2 / (h mu n_bar_ref), n_bar_ref 0.99765, w_bar_ref 0.76113 (the default engine's pilot constants)",
                      "usability_rule": "median |h_hat - h|/h < 0.20 and coverage >= 0.90 (A, B); C: error only"},
           "cells": table, "seconds": round(time.time() - t0)}
    # estimator C on the data
    smm_path = os.path.join(OUT, "smm_fit.json")
    if not a.skip_data_smm and os.path.exists(smm_path):
        res["smm_data"] = json.load(open(smm_path, encoding="utf-8")); print("SMM on data: loaded", flush=True)
    elif not a.skip_data_smm:
        M, boots = data_moments()
        w = 1.0 / np.maximum(boots.var(axis=0, ddof=1), 1e-30)
        t1 = time.time()
        f = smm_fit(M, w)
        # interval: refit on 30 moment resamples (warm start) -- the count is compute-bound and stated
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            fb = list(ex.map(_refit, [(boots[i], w, [f["sigma_V"], f["sbar"], f["h"]]) for i in range(a.n_boot_refits)]))
        smm = {"fit": f, "moments_data": M.tolist(), "moment_names": ["var1", "VR20", "VR60", "VR120", "VR250", "VR500", "acf20", "acf60", "acf120"],
               "ci95_h": [float(np.percentile([b["h"] for b in fb], 2.5)), float(np.percentile([b["h"] for b in fb], 97.5))],
               "ci95_sigma_V": [float(np.percentile([b["sigma_V"] for b in fb], 2.5)), float(np.percentile([b["sigma_V"] for b in fb], 97.5))],
               "ci95_s_x": [float(np.percentile([b["s_x"] for b in fb], 2.5)), float(np.percentile([b["s_x"] for b in fb], 97.5))],
               "n_boot_refits": a.n_boot_refits, "weight": "diagonal 1/Var (200 stock resamples)", "simulation": f"{SMM_PATHS} paths x {SMM_T} days, CRN, burn {SMM_BURN}",
               "seconds": round(time.time() - t1)}
        res["smm_data"] = smm
        with open(os.path.join(OUT, "smm_fit.json"), "w", encoding="utf-8") as fh:
            json.dump(smm, fh, indent=1)
        print("SMM on data:", json.dumps(smm["fit"]), smm["ci95_h"], flush=True)
    with open(os.path.join(OUT, "recovery.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    L = ["# E1.2 recovery study (REG-5; PREREG_PHASE_1.md section 4.4)", "",
         f"Synthetic panels {N_STOCKS} stocks x {T_DAYS} days from the calm simulator; A and B at {a.reps_ab} replications per cell, C at {a.reps_c}; "
         f"V_hat noise sd {sd_m:.3f} (FIT), persistence in {{0, 0.9}}/quarter (DESIGN bracket). Usable = median relative error < 0.20 and coverage >= 0.90.", "",
         "| h | sigma_V | A: med rel err / RMSE / coverage / median h_hat | usable | B (white m): err / cov / h_hat | usable | B (rho_m 0.9): err / cov / h_hat | usable | C: err / RMSE / h_hat | usable |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in table.items():
        A_, B0, B9, C_ = r["A"], r["B_rho0.0"], r["B_rho0.9"], r["C"]
        L.append(f"| {r['h']} | {r['sigma_V']} | {A_['median_rel_error']:.2f} / {A_['rmse_rel']:.2f} / {A_['coverage']:.2f} / {A_['median_h_hat']:.0f} | {A_['usable']} | "
                 f"{B0['median_rel_error']:.2f} / {B0['coverage']:.2f} / {B0['median_h_hat']:.0f} | {B0['usable']} | {B9['median_rel_error']:.2f} / {B9['coverage']:.2f} / {B9['median_h_hat']:.0f} | {B9['usable']} | "
                 + (f"{C_['median_rel_error']:.2f} / {C_['rmse_rel']:.2f} / {C_['median_h_hat']:.0f} | {C_['usable']} |" if C_ else "- | - |"))
    if "smm_data" in res:
        s = res["smm_data"]
        L += ["", f"Estimator C on set A: sigma_V {s['fit']['sigma_V']:.5f} [{s['ci95_sigma_V'][0]:.5f}, {s['ci95_sigma_V'][1]:.5f}], s_x {s['fit']['s_x']:.3f} "
              f"[{s['ci95_s_x'][0]:.3f}, {s['ci95_s_x'][1]:.3f}], h {s['fit']['h']:.0f} d [{s['ci95_h'][0]:.0f}, {s['ci95_h'][1]:.0f}], J {s['fit']['J']:.2f} "
              f"({s['n_boot_refits']} bootstrap refits; {s['weight']}; {s['simulation']})."]
    with open(os.path.join(OUT, "recovery.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", OUT, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
