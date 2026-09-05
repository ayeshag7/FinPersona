"""
E2.3 (PREREG_PHASE_2.md section 4): the SMM done properly, for each of REG-4's three engines and each period.

  J(theta) = d' W d,  d = m_sim(theta) - m_data,  W = [(1-s) Sigma_hat + s diag(Sigma_hat)]^-1, s = 0.10
  Sigma_hat: joint stock x block bootstrap of the pooled 17-moment vector (tools/phase2/e2_3_data.py)
  m_sim:     n_paths x 5,000 days, burn 500, COMMON RANDOM NUMBERS across theta (seed SM = 110001)
  optimiser: differential evolution with an initial population containing >= 20 named starts (chartist-active
             regions included), then Nelder-Mead polish
  acceptance: chi^2 at 5 % with df = 17 - p, AND Franke-Westerhoff's bootstrap p-value (their eq. (9)):
             p = share of C model replicates at the DATA's panel size whose J is at or below the 95 % quantile
             of the J distribution of the B data bootstrap moment vectors

    python -m tools.phase2.e2_3_smm --engine fw_v2 --period full [--n-paths 20] [--maxiter 40]
    python -m tools.phase2.e2_3_smm --reference-row          # deterministic J at a fixed theta (machine check)
Outputs: docs/env_v2/generated/v2_1/e2_3/smm_<engine>_<period>.json  (one file per cell; resumable)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import differential_evolution, minimize
from scipy.stats import chi2, qmc

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

from tools.phase2.engines import BOUNDS, DEFAULTS, FREE, LOG_PARS, pooled_moments, theta_to_params  # noqa: E402
from tools.phase2.moments import ALL_NAMES  # noqa: E402

OUT = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_3")
SEED_SM, SEED_SB, SEED_MC = 110001, 112001, 113001
T_SIM, BURN = 5000, 500
K_REPORT = 20   # CRN replicates averaged for the REPORTED m_sim at theta-hat (ADDENDUM section 1)
SHRINK = 0.10

# >= 20 named starts (PREREG section 4.4).  Each dict gives the values of the free parameters it fixes; the rest
# fall back to engines.DEFAULTS.  "chartist-active" = small alpha_p / small alpha_n, where the DCA switching is live.
START_GRID = [
    dict(name="fw_table1", phi=0.12, chi=1.50, alpha_0=-0.327, alpha_n=1.79, alpha_p=18.43, sigma_f=0.758, sigma_c=2.087),
    dict(name="pruna_table1", phi=0.121, chi=1.555, alpha_0=-0.301, alpha_n=1.990, alpha_p=22.741, sigma_f=0.592, sigma_c=1.917),
    dict(name="v2_fallback_hl150", phi=0.4632, chi=1.50, alpha_0=-0.327, alpha_n=1.79, alpha_p=18.43),
    dict(name="chartist_live_lowap", alpha_p=1.0, alpha_n=0.5, phi=0.12, chi=1.50),
    dict(name="chartist_live_lowan", alpha_p=18.43, alpha_n=0.1, phi=0.12, chi=1.50),
    dict(name="chartist_live_bothlow", alpha_p=0.5, alpha_n=0.1, phi=0.05, chi=1.80),
    dict(name="chartist_strong", alpha_p=2.0, alpha_n=0.3, phi=0.02, chi=2.50),
    dict(name="fund_locked_highap", alpha_p=200.0, alpha_n=1.79, phi=0.12, chi=1.50),
    dict(name="fund_locked_fastpull", alpha_p=100.0, phi=2.0, chi=0.50),
    dict(name="fast_pull_h5", h=5.0, phi=2.77),
    dict(name="fast_pull_h10", h=10.0, phi=1.39),
    dict(name="h30", h=30.0, phi=0.463 * 5),
    dict(name="h60", h=60.0, phi=1.158),
    dict(name="h150", h=150.0, phi=0.4632),
    dict(name="h500", h=500.0, phi=0.139),
    dict(name="sv006", sigma_V=0.006), dict(name="sv012", sigma_V=0.012), dict(name="sv0196", sigma_V=0.0196),
    dict(name="sv0196_fast", sigma_V=0.0196, h=5.0, phi=2.77, alpha_p=2.0),
    dict(name="sbar012", sbar=0.012), dict(name="sbar025", sbar=0.025),
    dict(name="sbar025_sv012", sbar=0.025, sigma_V=0.012),
    dict(name="fw_bignoise", sigma_f=1.5, sigma_c=4.0, alpha_p=18.43),
    dict(name="fw_smallnoise", sigma_f=0.3, sigma_c=1.0, alpha_p=5.0),
]


def to_search(engine, vals):
    return np.array([math.log(vals[k]) if k in LOG_PARS else vals[k] for k in FREE[engine]])


def from_search(engine, z):
    return np.array([math.exp(v) if k in LOG_PARS else v for k, v in zip(FREE[engine], z)])


def search_bounds(engine):
    out = []
    for k in FREE[engine]:
        lo, hi = BOUNDS[k]
        out.append((math.log(lo), math.log(hi)) if k in LOG_PARS else (lo, hi))
    return out


def named_starts(engine, base):
    zs, names = [], []
    for s in START_GRID:
        vals = dict(base)
        vals.update({k: v for k, v in s.items() if k != "name" and k in FREE[engine]})
        z = to_search(engine, vals)
        lo = np.array([b[0] for b in search_bounds(engine)])
        hi = np.array([b[1] for b in search_bounds(engine)])
        zs.append(np.clip(z, lo, hi))
        names.append(s["name"])
    return np.array(zs), names


def load_data(period):
    d = json.load(open(os.path.join(OUT, "data_moments.json"), encoding="utf-8"))
    r = d["periods"][period]
    W = np.load(os.path.join(OUT, f"weight_{period}.npy"))
    boot = np.load(os.path.join(OUT, f"data_boot_{period}.npy"))
    return np.array(r["moments"]), W, boot, r, d


def make_J(engine, m_data, W, base, n_paths, T=T_SIM, seed=SEED_SM):
    def J(z):
        p = theta_to_params(engine, from_search(engine, np.asarray(z)), base)
        try:
            m = pooled_moments(engine, n_paths, T, p, seed=seed, burn=BURN)
        except (FloatingPointError, ValueError):
            return 1e12
        if not np.all(np.isfinite(m)):
            return 1e12
        d = m - m_data
        return float(d @ W @ d)
    return J


def fw_bootstrap_p(engine, theta, base, m_data, W, boot, n_stocks, T_days, n_mc, seed=SEED_MC):
    """FW 2012 eq. (9) at reduced counts: J of the B data-bootstrap moment vectors -> J_0.95; J of n_mc model
    replicates at the DATA's panel size -> p = share at or below J_0.95."""
    db = boot - m_data
    Jb = np.einsum("ij,jk,ik->i", db, W, db)
    J95 = float(np.percentile(Jb, 95))
    p = theta_to_params(engine, theta, base)
    Jm = []
    for c in range(n_mc):
        m = pooled_moments(engine, n_stocks, T_days, p, seed=seed + 17 * c, burn=BURN)
        d = m - m_data
        Jm.append(float(d @ W @ d))
    Jm = np.asarray(Jm)
    return {"J95_bootstrap": J95, "n_boot": int(len(Jb)), "n_mc": int(n_mc),
            "bootstrap_J_median": float(np.median(Jb)),
            "mc_J_median": float(np.median(Jm)), "mc_J_p05": float(np.percentile(Jm, 5)),
            "p_value": float((Jm <= J95).mean()),
            "p_value_mc_se": float(math.sqrt(max((Jm <= J95).mean() * (1 - (Jm <= J95).mean()), 1e-9) / n_mc))}


def profiles(engine, J, z_hat, n_grid=11, span=1.0):
    out = {}
    b = search_bounds(engine)
    for i, k in enumerate(FREE[engine]):
        lo, hi = b[i]
        centre = z_hat[i]
        half = span * math.log(10.0) if k in LOG_PARS else span * max(1.0, abs(centre))
        grid = np.clip(np.linspace(centre - half, centre + half, n_grid), lo, hi)
        vals = []
        for g in grid:
            z = z_hat.copy()
            z[i] = g
            vals.append(J(z))
        nat = [math.exp(g) if k in LOG_PARS else g for g in grid]
        out[k] = {"grid": nat, "J": vals}
    return out


def run_cell(engine, period, n_paths, maxiter, popmult, n_mc, n_refits, quick=False, base_extra=None,
             seed_sm=SEED_SM, seed_sb=SEED_SB, seed_mc=SEED_MC):
    t0 = time.time()
    m_data, W, boot, meta, dall = load_data(period)
    base = dict(DEFAULTS)
    ps = json.load(open(os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e2_1", "fw_repro.json"),
                        encoding="utf-8")) if os.path.exists(os.path.join(
        ROOT, "docs", "env_v2", "generated", "v2_1", "e2_1", "fw_repro.json")) else None
    base["price_scale"] = 1.0 if (ps and ps["armA"]["scale1"]["confirmed"]) else 100.0
    if base_extra:      # v2.1 Phase 3 (PREREG section 9): garch_shape / jump_rate / jump_sd / sbar_identity
        base.update(base_extra)
    J = make_J(engine, m_data, W, base, n_paths, seed=seed_sm)
    z0, names = named_starts(engine, base)
    J0 = [J(z) for z in z0]
    best_start = int(np.argmin(J0))
    bnds = search_bounds(engine)
    p = len(FREE[engine])
    npop = max(popmult * p, len(z0) + 4)
    lo = np.array([b[0] for b in bnds])
    hi = np.array([b[1] for b in bnds])
    fill = qmc.scale(qmc.LatinHypercube(d=p, seed=4242).random(max(0, npop - len(z0))), lo, hi)
    init = np.vstack([z0, fill]) if len(fill) else z0
    n_eval = [0]

    def Jc(z):
        n_eval[0] += 1
        return J(z)

    de = differential_evolution(Jc, bnds, init=init, strategy="best1bin", tol=0.01, mutation=(0.3, 1.0),
                                recombination=0.9, maxiter=(2 if quick else maxiter), polish=False,
                                updating="deferred", workers=1, seed=97531, disp=False)
    nm = minimize(Jc, de.x, method="Nelder-Mead",
                  options={"xatol": 1e-3, "fatol": 1e-8, "maxiter": 40 if quick else 600, "maxfev": 40 if quick else 600})
    z_hat = nm.x if nm.fun <= de.fun else de.x
    J_hat = float(min(nm.fun, de.fun))
    theta = from_search(engine, z_hat)
    pth = theta_to_params(engine, theta, base)
    # ADDENDUM section 1: the optimiser runs on ONE CRN draw (a deterministic surface); the REPORTED moment
    # vector and J at theta-hat average K independent CRN replicates, which is what brings the simulation noise
    # under the pre-registered 0.30 bootstrap-sd bound.
    M_rep = np.stack([pooled_moments(engine, n_paths, T_SIM, pth, seed=seed_sm + 1000 * k, burn=BURN)
                      for k in range(K_REPORT)])
    m_sim = M_rep.mean(axis=0)
    sim_sd = M_rep.std(axis=0, ddof=1) / math.sqrt(K_REPORT)
    d_rep = m_sim - m_data
    J_crn, J_hat = J_hat, float(d_rep @ W @ d_rep)
    df = len(ALL_NAMES) - p
    res = {"engine": engine, "period": period, "window": meta["window"], "n_stocks": meta["n_stocks"],
           "n_days_data": meta["n_days"], "free": list(FREE[engine]), "theta": theta.tolist(),
           "params": {k: float(v) for k, v in zip(FREE[engine], theta)},
           "price_scale": base["price_scale"], "n_paths": n_paths, "T_sim": T_SIM, "burn": BURN,
           "seed_crn": seed_sm, "shrink": SHRINK,
           "base_extra": base_extra,
           "J": J_hat, "J_single_crn": J_crn, "K_report": K_REPORT,
           "sim_se_over_boot_sd": (sim_sd / boot.std(axis=0, ddof=1)).tolist(),
           "df": df, "chi2_crit_95": float(chi2.ppf(0.95, df)),
           "chi2_accept": bool(J_hat <= chi2.ppf(0.95, df)),
           "start_J": {n: float(v) for n, v in zip(names, J0)}, "best_named_start": names[best_start],
           "start_J_best": float(min(J0)), "end_J": J_crn, "n_evaluations": int(n_eval[0]),
           "de_maxiter": maxiter, "de_popsize_members": int(len(init)), "de_success": bool(de.success),
           "de_message": str(de.message), "nm_nit": int(nm.nit),
           "moments_data": m_data.tolist(), "moments_sim": m_sim.tolist(), "moment_names": ALL_NAMES,
           "resid_over_bootsd": ((m_sim - m_data) / boot.std(axis=0, ddof=1)).tolist()}
    res["profiles"] = profiles(engine, J, z_hat)
    if n_mc > 0:
        res["fw_bootstrap"] = fw_bootstrap_p(engine, theta, base, m_data, W, boot, meta["n_stocks"],
                                             meta["n_days"], n_mc if not quick else 5, seed=seed_mc)
        res["accept_fw_p"] = bool(res["fw_bootstrap"]["p_value"] >= 0.05)
    else:   # ADDENDUM section 2: the held-out fits need theta-hat only; acceptance is decided on `full`
        res["fw_bootstrap"] = {"p_value": None, "n_mc": 0,
                               "note": "not computed: this cell feeds E2.4(b)'s held-out prediction only "
                                       "(PREREG_PHASE_2_ADDENDUM.md section 2)"}
        res["accept_fw_p"] = None
    if n_refits:
        rng = np.random.default_rng(seed_sb)
        pick = rng.choice(len(boot), size=min(n_refits, len(boot)), replace=False)
        fits = []
        for i in pick:
            Ji = make_J(engine, boot[i], W, base, n_paths, seed=seed_sm)
            r = minimize(Ji, z_hat, method="Nelder-Mead",
                         options={"xatol": 2e-3, "fatol": 1e-8, "maxiter": 200, "maxfev": 200})
            fits.append(from_search(engine, r.x).tolist())
        F = np.array(fits)
        res["bootstrap_refits"] = {"n": int(len(F)), "seeds": "SB 112001",
                                   "ci95": {k: [float(np.percentile(F[:, j], 2.5)), float(np.percentile(F[:, j], 97.5))]
                                            for j, k in enumerate(FREE[engine])},
                                   "sd": {k: float(F[:, j].std(ddof=1)) for j, k in enumerate(FREE[engine])}}
    res["seconds"] = round(time.time() - t0)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="fw_v2")
    ap.add_argument("--period", default="full")
    ap.add_argument("--n-paths", type=int, default=200)
    ap.add_argument("--maxiter", type=int, default=40)
    ap.add_argument("--popmult", type=int, default=8)
    ap.add_argument("--n-mc", type=int, default=200)
    ap.add_argument("--n-refits", type=int, default=0)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--reference-row", action="store_true")
    ap.add_argument("--refits-only", action="store_true")
    ap.add_argument("--refit-maxfev", type=int, default=120)
    ap.add_argument("--tag", default="")
    # v2.1 Phase 3 (PREREG section 9): extra base parameters and fresh seed blocks for the constrained re-fit
    ap.add_argument("--base-json", default=None, help="JSON file merged into the simulator base "
                                                     "(garch_shape, jump_rate, jump_sd, sbar_identity)")
    ap.add_argument("--seed-sm", type=int, default=SEED_SM)
    ap.add_argument("--seed-sb", type=int, default=SEED_SB)
    ap.add_argument("--seed-mc", type=int, default=SEED_MC)
    a = ap.parse_args()
    base_extra = json.load(open(a.base_json, encoding="utf-8")) if a.base_json else None
    os.makedirs(OUT, exist_ok=True)
    if a.reference_row:
        from tools.phase2.engines import pooled_moments as pm
        p = dict(DEFAULTS)
        p["price_scale"] = 1.0
        rows = {}
        for eng in ("ar1", "fw_v2", "fw_plus"):
            m = pm(eng, 20, 5000, p, seed=SEED_SM, burn=BURN)
            rows[eng] = [repr(float(v)) for v in m]
        print(json.dumps({"reference_row": rows, "note": "20 paths x 5000 d, burn 500, seed 110001, "
                          "engines.DEFAULTS with price_scale 1; must agree to 10 significant figures on any "
                          "machine whose SMM output is used"}, indent=1))
        with open(os.path.join(OUT, "reference_row.json"), "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)
        return
    path = os.path.join(OUT, f"smm_{a.engine}_{a.period}{a.tag}.json")
    if a.refits_only:
        r = json.load(open(path, encoding="utf-8"))
        if "bootstrap_refits" in r:
            print(f"{path}: refits already present, skipped")
            return
        m_data, W, boot, meta, _ = load_data(a.period)
        base = dict(DEFAULTS)
        base["price_scale"] = r["price_scale"]
        z_hat = to_search(a.engine, dict(zip(FREE[a.engine], r["theta"])))
        rng = np.random.default_rng(SEED_SB)
        pick = rng.choice(len(boot), size=min(a.n_refits, len(boot)), replace=False)
        t0 = time.time()
        fits = []
        for i in pick:
            Ji = make_J(a.engine, boot[i], W, base, r["n_paths"])
            q = minimize(Ji, z_hat, method="Nelder-Mead",
                         options={"xatol": 3e-3, "fatol": 1e-8, "maxiter": a.refit_maxfev, "maxfev": a.refit_maxfev})
            fits.append(from_search(a.engine, q.x).tolist())
            print(f"  refit {len(fits)}/{len(pick)} {time.time() - t0:.0f} s", flush=True)
        F = np.array(fits)
        r["bootstrap_refits"] = {"n": int(len(F)), "seeds": "SB 112001", "maxfev": a.refit_maxfev,
                                 "ci95": {k: [float(np.percentile(F[:, j], 2.5)), float(np.percentile(F[:, j], 97.5))]
                                          for j, k in enumerate(FREE[a.engine])},
                                 "sd": {k: float(F[:, j].std(ddof=1)) for j, k in enumerate(FREE[a.engine])},
                                 "seconds": round(time.time() - t0)}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(r, fh, indent=1)
        print(json.dumps(r["bootstrap_refits"]["ci95"], indent=1))
        return
    if os.path.exists(path):
        print(f"{path}: exists, skipped")
        return
    r = run_cell(a.engine, a.period, a.n_paths, a.maxiter, a.popmult, a.n_mc, a.n_refits, quick=a.quick,
                 base_extra=base_extra, seed_sm=a.seed_sm, seed_sb=a.seed_sb, seed_mc=a.seed_mc)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1)
    print(json.dumps({k: r[k] for k in ("engine", "period", "params", "J", "df", "chi2_crit_95", "chi2_accept",
                                        "start_J_best", "n_evaluations", "seconds")}, indent=1))
    print("fw bootstrap p =", r["fw_bootstrap"]["p_value"], "accept:", r["accept_fw_p"])
    print("written", path)


if __name__ == "__main__":
    main()
