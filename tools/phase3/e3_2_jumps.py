"""
E3.2 (PREREG_PHASE_3.md section 4): jumps — detection, the mixture adoption fit, and its recovery gate.

    python -m tools.phase3.e3_2_jumps --stage panel      # detection stats + moment vector + sigma-hat bins
    python -m tools.phase3.e3_2_jumps --stage fit        # the (nu, lambda, sigma_J) mixture fit + 200 refits
    python -m tools.phase3.e3_2_jumps --stage recovery   # the 6-cell x 5-replicate recovery grid (gates the fit)

Model (fixed in the pre-registration): on a day with fitted conditional sd sigma-hat (percent units),
    z = T + (100 J / sigma-hat) B,   T ~ standardised t(nu),  B ~ Bernoulli(lambda_day),  J ~ N(0, sigma_J),
lambda_day = lambda q / ws inside announcement windows and lambda (1-q)/(1-ws) outside (q = 0.4345 FIT, E1.4).
Moments (9): pooled exceedance shares at |z| > {2.5, 3, 3.5, 4, 4.5, 5, 6} (full sample) + the in-window and
out-of-window shares at |z| > 4 (2009-2024). W = inverse of the 1,000-resample stock-bootstrap covariance,
shrunk 10 % toward its diagonal. Semi-analytic predictions (Gauss-Hermite over J, exact standardised-t tail,
averaged over 200 sigma-hat quantile bins); free (nu, lambda, sigma_J); DE + Nelder-Mead polish.

Known approximation (stated): the sigma-hat distribution is taken as fixed although the QML filter absorbed part
of the jumps; the recovery grid measures exactly this end to end and gates the adoption (PREREG 4.3).

Outputs: docs/env_v2/generated/v2_1/e3_2/{detection.json,detection.md,moments.json,fit.json,recovery.json}
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import differential_evolution, minimize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("OMP_NUM_THREADS", "2")

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_2")
THRESH = (2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0)
TH_SPLIT = 4.0
Q_ANN = 0.4345            # E1.4 FIT, held fixed
N_BOOT = 1000
N_REFITS = 200
SEED_BOOT = 201001
N_SIGMA_BINS = 200
GH_NODES = 20
BOUNDS = {"nu": (3.0, 40.0), "lam": (1e-5, 0.05), "sJ": (0.005, 0.25)}
LOG_PARS = ("lam", "sJ")
RECOVERY_CELLS = [
    {"nu": 5.5, "lam": 0.001, "sJ": 0.05},
    {"nu": 5.5, "lam": 0.004, "sJ": 0.03},
    {"nu": 8.0, "lam": 0.004, "sJ": 0.05},
    {"nu": 6.0, "lam": 0.010, "sJ": 0.03},
    {"nu": 10.0, "lam": 0.002, "sJ": 0.08},
    {"nu": 5.0, "lam": 0.0, "sJ": 0.03},   # the no-jump null
]
N_REPS = 5
SEED_REC0 = 200001
REC_STOCKS, REC_DAYS = 100, 6289
USABILITY_ERR = 0.20


# ------------------------------------------------------------------ panel side
def load_panel():
    """Per-stock arrays: z, sigma-hat (percent), in-window flag (NaN outside 2009-24 coverage)."""
    from tools.phase1.panel import analysis_sets, load_prices, log_returns
    fits = pd.read_csv(os.path.join(GEN, "e3_1", "garch_fits.csv"))
    fits = fits[(fits["set"] == "A") & (fits["period"] == "full") & fits["converged"]]
    mu = dict(zip(fits["ticker"], fits["mu"]))           # daily mean, already /100 in the csv
    nus = dict(zip(fits["ticker"], fits["nu"]))
    z = pd.read_parquet(os.path.join(GEN, "e3_1", "residuals.parquet"))
    z["date"] = pd.to_datetime(z["date"])
    sp = pd.read_parquet(os.path.join(GEN, "e1_4", "panel_residuals_split.parquet"))
    sets = analysis_sets(write=False)
    prices = load_prices(sets["A"]).ffill()
    rets = log_returns(prices)
    per = {}
    win_by_ticker = {}
    for t, g in sp.groupby("ticker"):
        win_by_ticker[t] = g["in_window"].to_numpy(bool)
    for t, g in z.groupby("ticker"):
        if t not in mu:
            continue
        g = g.sort_values("date")
        r = rets[t].reindex(pd.DatetimeIndex(g["date"])).to_numpy(float)
        zz = g["z"].to_numpy(float)
        sig = np.where(np.abs(zz) > 0.01, (100.0 * r - 100.0 * mu[t]) / zz, np.nan)
        dates = pd.DatetimeIndex(g["date"])
        m09 = dates >= "2009-01-01"
        win = np.full(len(zz), -1, dtype=np.int8)          # -1 = outside EDGAR coverage
        if t in win_by_ticker and win_by_ticker[t].shape[0] == int(m09.sum()):
            win[np.asarray(m09)] = win_by_ticker[t].astype(np.int8)
        per[t] = {"z": zz, "sigma": sig, "win": win, "nu_qml": float(nus[t])}
    return per


def stock_rows(per):
    """One row per stock: exceedance counts at each threshold, expected t-tail counts, split counts, sizes."""
    rows = []
    for t, d in per.items():
        zz, sig, win, nu = d["z"], d["sigma"], d["win"], d["nu_qml"]
        az = np.abs(zz)
        n = len(zz)
        c = float(math.sqrt(nu / (nu - 2.0)))
        row = {"ticker": t, "n": n, "nu_qml": nu}
        for th in THRESH:
            row[f"c{th}"] = int((az > th).sum())
            row[f"e{th}"] = float(n * 2.0 * stats.t.sf(th * c, nu))
        m_in, m_out = win == 1, win == 0
        row["n_in"], row["n_out"] = int(m_in.sum()), int(m_out.sum())
        row["c_in"], row["c_out"] = int((az[m_in] > TH_SPLIT).sum()), int((az[m_out] > TH_SPLIT).sum())
        jump = az > TH_SPLIT
        row["sizes"] = (zz[jump] * np.where(np.isfinite(sig[jump]), sig[jump], np.nan) / 100.0).tolist()
        rows.append(row)
    return pd.DataFrame(rows)


def pooled_vector(rows: pd.DataFrame) -> np.ndarray:
    v = [rows[f"c{th}"].sum() / rows["n"].sum() for th in THRESH]
    v.append(rows["c_in"].sum() / max(rows["n_in"].sum(), 1))
    v.append(rows["c_out"].sum() / max(rows["n_out"].sum(), 1))
    return np.asarray(v, float)


def sigma_bins(per, cls: str) -> np.ndarray:
    """200 quantile-bin representative sigma-hats, pooled; cls in {'all','in','out'}."""
    parts = []
    for d in per.values():
        s = d["sigma"]
        if cls == "in":
            s = s[d["win"] == 1]
        elif cls == "out":
            s = s[d["win"] == 0]
        parts.append(s[np.isfinite(s) & (s > 0.05) & (s < 50.0)])
    s = np.concatenate(parts)
    qs = (np.arange(N_SIGMA_BINS) + 0.5) / N_SIGMA_BINS
    return np.quantile(s, qs)


# ------------------------------------------------------------------ the semi-analytic model
_GH_X, _GH_W = np.polynomial.hermite.hermgauss(GH_NODES)


def model_vector(nu, lam, sJ, bins_all, bins_in, bins_out, ws_in):
    """Predicted 9-vector. Full-sample rows use the unconditional lambda on the pooled bins; the split rows use
    lambda q/ws and lambda (1-q)/(1-ws) on the per-class bins."""
    c = math.sqrt(nu / (nu - 2.0))

    def tail(u):
        return stats.t.sf(np.asarray(u) * c, nu)

    def p_exceed(th, sig, lam_day):
        base = 2.0 * float(stats.t.sf(th * c, nu))
        a = np.sqrt(2.0) * (100.0 * sJ / sig)[:, None] * _GH_X[None, :]      # (bins, nodes)
        pj = (tail(th - a) + tail(th + a)) @ _GH_W / math.sqrt(math.pi)      # (bins,)
        return (1.0 - lam_day) * base + lam_day * float(pj.mean())

    lam_in = min(lam * Q_ANN / ws_in, 1.0)
    lam_out = lam * (1.0 - Q_ANN) / (1.0 - ws_in)
    v = [p_exceed(th, bins_all, lam) for th in THRESH]
    v.append(p_exceed(TH_SPLIT, bins_in, lam_in))
    v.append(p_exceed(TH_SPLIT, bins_out, lam_out))
    return np.asarray(v, float)


def fit_mixture(m_data, W, bins_all, bins_in, bins_out, ws_in, pin_nu=None, seed=7):
    free = ["lam", "sJ"] if pin_nu is not None else ["nu", "lam", "sJ"]

    def unpack(zv):
        vals = {}
        for k, x in zip(free, zv):
            vals[k] = math.exp(x) if k in LOG_PARS else x
        if pin_nu is not None:
            vals["nu"] = pin_nu
        return vals

    def J(zv):
        p = unpack(zv)
        d = model_vector(p["nu"], p["lam"], p["sJ"], bins_all, bins_in, bins_out, ws_in) - m_data
        return float(d @ W @ d)

    bnds = [(math.log(BOUNDS[k][0]), math.log(BOUNDS[k][1])) if k in LOG_PARS else BOUNDS[k] for k in free]
    de = differential_evolution(J, bnds, seed=seed, maxiter=60, tol=1e-8, polish=False, init="sobol")
    nm = minimize(J, de.x, method="Nelder-Mead", options={"maxfev": 400, "fatol": 1e-12})
    z = nm.x if nm.fun <= de.fun else de.x
    p = unpack(z)
    return {"params": {k: float(p[k]) for k in ("nu", "lam", "sJ")}, "J": float(min(nm.fun, de.fun)),
            "n_evals": int(de.nfev + nm.nfev), "free": free}


# ------------------------------------------------------------------ stages
def stage_panel():
    t0 = time.time()
    per = load_panel()
    rows = stock_rows(per)
    m = pooled_vector(rows)
    rng = np.random.default_rng(SEED_BOOT)
    boots = np.empty((N_BOOT, 9))
    idx = np.arange(len(rows))
    for b in range(N_BOOT):
        boots[b] = pooled_vector(rows.iloc[rng.integers(0, len(rows), len(rows))])
    cov = np.cov(boots.T)
    ws_in = float(rows["n_in"].sum() / max(rows["n_in"].sum() + rows["n_out"].sum(), 1))
    # expected t-tail shares (the no-jump null under each stock's own QML nu)
    exp_share = {f"{th}": float(rows[f"e{th}"].sum() / rows["n"].sum()) for th in THRESH}
    obs_share = {f"{th}": float(v) for th, v in zip(THRESH, m[:7])}
    excess = {f"{th}": obs_share[f"{th}"] - exp_share[f"{th}"] for th in THRESH}
    # bootstrap of the excess (recompute expected under each resample)
    ex_boot = np.empty((N_BOOT, len(THRESH)))
    rng2 = np.random.default_rng(SEED_BOOT + 1)
    cn = rows[[f"c{th}" for th in THRESH]].to_numpy(float)
    en = rows[[f"e{th}" for th in THRESH]].to_numpy(float)
    nn = rows["n"].to_numpy(float)
    for b in range(N_BOOT):
        ii = rng2.integers(0, len(rows), len(rows))
        ex_boot[b] = cn[ii].sum(0) / nn[ii].sum() - en[ii].sum(0) / nn[ii].sum()
    sizes = np.concatenate([np.asarray(s, float) for s in rows["sizes"]])
    sizes = sizes[np.isfinite(sizes)]
    det = {
        "design": {"panel": "set A full-sample GJR-t residuals (e3_1), 2000-2024", "thresholds": list(THRESH),
                   "n_stocks": int(len(rows)), "n_days": int(rows["n"].sum()), "q_ann_held": Q_ANN,
                   "split_window": "2009-2024 (EDGAR), threshold 4", "n_boot": N_BOOT, "seed_boot": SEED_BOOT},
        "observed_share": obs_share,
        "expected_t_tail_share": exp_share,
        "excess_share": excess,
        "excess_ci95": {f"{th}": [float(np.percentile(ex_boot[:, i], 2.5)), float(np.percentile(ex_boot[:, i], 97.5))]
                        for i, th in enumerate(THRESH)},
        "per_year": {"observed_at_4": obs_share["4.0"] * 252, "excess_at_4": excess["4.0"] * 252},
        "split_at_4": {"share_in": float(m[7]), "share_out": float(m[8]), "ws_in": ws_in},
        "sizes_at_4": {"n": int(len(sizes)), "mean": float(np.mean(sizes)), "sd": float(np.std(sizes)),
                       "neg_share": float(np.mean(sizes < 0)),
                       "note": "returns r on exceedance days: a mixture of the diffusive move and any jump"},
        "literature_beside": {"ABD 2007 (index futures, read by the plan's pass)":
                              "14.4 % jump share of RV; 27.9 % of days — anchors, never tolerances",
                              "Lee & Mykland 2008": "beta* = 4.6 at 1 %, intraday"},
        "seconds": round(time.time() - t0),
    }
    os.makedirs(OUT, exist_ok=True)
    np.save(os.path.join(OUT, "boot_moments.npy"), boots)
    np.savez(os.path.join(OUT, "sigma_bins.npz"), all=sigma_bins(per, "all"), win=sigma_bins(per, "in"),
             out=sigma_bins(per, "out"))
    with open(os.path.join(OUT, "moments.json"), "w", encoding="utf-8") as fh:
        json.dump({"m": m.tolist(), "cov": cov.tolist(), "ws_in": ws_in,
                   "names": [f"p{th}" for th in THRESH] + ["p4_in", "p4_out"]}, fh, indent=1)
    with open(os.path.join(OUT, "detection.json"), "w", encoding="utf-8") as fh:
        json.dump(det, fh, indent=1)
    L = ["# E3.2 jump detection on the panel (PREREG_PHASE_3.md section 4.1)", "",
         f"Set A residuals (E3.1), 2000-2024, n = {det['design']['n_days']:,} stock-days over "
         f"{det['design']['n_stocks']} stocks; {N_BOOT}-resample stock bootstrap. "
         "The expected share is the no-jump null under each stock's own fitted t(nu); the excess is a LOWER "
         "bound on the jump rate (the QML nu absorbed jump mass) as the observed share is an upper bound.", "",
         "| threshold | observed share | expected t-tail | excess | excess 95 % CI |", "|---|---|---|---|---|"]
    for th in THRESH:
        L.append(f"| {th} | {obs_share[f'{th}']:.5f} | {exp_share[f'{th}']:.5f} | {excess[f'{th}']:+.5f} | "
                 f"[{det['excess_ci95'][f'{th}'][0]:+.5f}, {det['excess_ci95'][f'{th}'][1]:+.5f}] |")
    L += ["", f"Split at 4 (2009-24): in-window share {m[7]:.5f}, outside {m[8]:.5f} (window share of days "
          f"{ws_in:.3f}; E1.4's q = {Q_ANN} held). Sizes at 4: mean {det['sizes_at_4']['mean']:+.4f}, sd "
          f"{det['sizes_at_4']['sd']:.4f}, negative share {det['sizes_at_4']['neg_share']:.3f} "
          f"(n = {det['sizes_at_4']['n']:,}).", "",
          "Literature beside (not tolerances): " + "; ".join(f"{k}: {v}" for k, v in det["literature_beside"].items()) + "."]
    with open(os.path.join(OUT, "detection.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(json.dumps({k: det[k] for k in ("observed_share", "expected_t_tail_share", "excess_share", "split_at_4", "sizes_at_4")}, indent=1))


def stage_fit(pin_nu=None, tag=""):
    t0 = time.time()
    mm = json.load(open(os.path.join(OUT, "moments.json"), encoding="utf-8"))
    m, cov, ws_in = np.asarray(mm["m"]), np.asarray(mm["cov"]), mm["ws_in"]
    bins = np.load(os.path.join(OUT, "sigma_bins.npz"))
    W = np.linalg.inv(0.9 * cov + 0.1 * np.diag(np.diag(cov)))
    fit = fit_mixture(m, W, bins["all"], bins["win"], bins["out"], ws_in, pin_nu=pin_nu)
    fit["model_at_hat"] = model_vector(fit["params"]["nu"], fit["params"]["lam"], fit["params"]["sJ"],
                                       bins["all"], bins["win"], bins["out"], ws_in).tolist()
    fit["m_data"] = m.tolist()
    # refits on bootstrap moment vectors
    boots = np.load(os.path.join(OUT, "boot_moments.npy"))
    rng = np.random.default_rng(SEED_BOOT + 2)
    idx = rng.choice(len(boots), N_REFITS, replace=False)
    draws = []
    z0 = [math.log(fit["params"][{"lam": "lam", "sJ": "sJ"}.get(k, k)]) if k in LOG_PARS else fit["params"][k]
          for k in fit["free"]]
    for i, b in enumerate(idx):
        mb = boots[b]

        def Jb(zv, mb=mb):
            vals = {}
            for k, x in zip(fit["free"], zv):
                vals[k] = math.exp(x) if k in LOG_PARS else x
            if pin_nu is not None:
                vals["nu"] = pin_nu
            d = model_vector(vals["nu"], vals["lam"], vals["sJ"], bins["all"], bins["win"], bins["out"], ws_in) - mb
            return float(d @ W @ d)
        nm = minimize(Jb, z0, method="Nelder-Mead", options={"maxfev": 250})
        vals = {}
        for k, x in zip(fit["free"], nm.x):
            vals[k] = math.exp(x) if k in LOG_PARS else x
        if pin_nu is not None:
            vals["nu"] = pin_nu
        draws.append(vals)
    fit["refits"] = {"n": len(draws),
                     "ci95": {k: [float(np.percentile([d[k] for d in draws], 2.5)),
                                  float(np.percentile([d[k] for d in draws], 97.5))] for k in ("nu", "lam", "sJ")},
                     "draws": draws}
    fit["design"] = {"pin_nu": pin_nu, "n_refits": N_REFITS, "gh_nodes": GH_NODES, "sigma_bins": N_SIGMA_BINS,
                     "bounds": BOUNDS, "q_ann_held": Q_ANN}
    fit["seconds"] = round(time.time() - t0)
    name = f"fit{tag}.json"
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(fit, fh, indent=1)
    print(json.dumps({k: fit[k] for k in ("params", "J", "free")} | {"ci95": fit["refits"]["ci95"]}, indent=1))


def _one_recovery(args):
    cell_i, rep, seed = args
    import warnings
    warnings.filterwarnings("ignore")
    from arch import arch_model
    cell = RECOVERY_CELLS[cell_i]
    nu, lam, sJ = cell["nu"], cell["lam"], cell["sJ"]
    rng = np.random.default_rng(seed)
    g = {"alpha": 0.027, "gamma": 0.058, "beta": 0.932}
    pers = g["alpha"] + g["gamma"] / 2 + g["beta"]
    ws = 10.0 / 63.0
    lam_in = min(lam * Q_ANN / ws, 1.0) if lam > 0 else 0.0
    lam_out = lam * (1 - Q_ANN) / (1 - ws) if lam > 0 else 0.0
    per = {}
    for i in range(REC_STOCKS):
        sbar = rng.uniform(0.0175, 0.0275)
        omega = sbar ** 2 * (1 - pers)
        eta = rng.standard_t(nu, REC_DAYS) / math.sqrt(nu / (nu - 2))
        off = rng.integers(0, 63)
        day = np.arange(REC_DAYS)
        win = ((day + off) % 63) < 10
        lam_day = np.where(win, lam_in, lam_out)
        B = rng.random(REC_DAYS) < lam_day
        J = np.where(B, rng.normal(0.0, sJ, REC_DAYS), 0.0)
        h = sbar ** 2
        e_prev = 0.0
        r = np.empty(REC_DAYS)
        for t_ in range(REC_DAYS):
            lev = g["gamma"] * e_prev ** 2 if e_prev < 0 else 0.0
            h = omega + g["alpha"] * e_prev ** 2 + lev + g["beta"] * h
            e = math.sqrt(h) * eta[t_]
            e_prev = e
            r[t_] = e + J[t_]
        try:
            am = arch_model(100.0 * r, mean="Constant", vol="GARCH", p=1, o=1, q=1, dist="t")
            res = am.fit(disp="off", show_warning=False, options={"maxiter": 500})
            zz = np.asarray(res.std_resid, float)
            mu_hat = float(res.params["mu"]) / 100.0
            nu_hat = float(res.params["nu"])
        except Exception:
            continue
        sig = np.where(np.abs(zz) > 0.01, (100.0 * r - 100.0 * mu_hat) / zz, np.nan)
        per[i] = {"z": zz, "sigma": sig, "win": win.astype(np.int8), "nu_qml": nu_hat}
    rows = stock_rows(per)
    m = pooled_vector(rows)
    rng2 = np.random.default_rng(seed + 5000)
    boots = np.empty((300, 9))
    for b in range(300):
        boots[b] = pooled_vector(rows.iloc[rng2.integers(0, len(rows), len(rows))])
    cov = np.cov(boots.T)
    W = np.linalg.inv(0.9 * cov + 0.1 * np.diag(np.diag(cov)))
    ws_in = float(rows["n_in"].sum() / (rows["n_in"].sum() + rows["n_out"].sum()))
    b_all, b_in, b_out = (sigma_bins(per, c) for c in ("all", "in", "out"))
    fit = fit_mixture(m, W, b_all, b_in, b_out, ws_in, seed=seed % 1000)
    # a cheap lambda interval from 60 NM refits on bootstrap vectors (for the lambda=0 null rule)
    z0 = [fit["params"]["nu"], math.log(max(fit["params"]["lam"], 1e-5)), math.log(fit["params"]["sJ"])]
    lams = []
    for b in rng2.choice(300, 60, replace=False):
        mb = boots[b]

        def Jb(zv, mb=mb):
            nu_, lam_, sJ_ = zv[0], math.exp(zv[1]), math.exp(zv[2])
            if not (BOUNDS["nu"][0] <= nu_ <= BOUNDS["nu"][1]):
                return 1e9
            d = model_vector(nu_, lam_, sJ_, b_all, b_in, b_out, ws_in) - mb
            return float(d @ W @ d)
        nm = minimize(Jb, z0, method="Nelder-Mead", options={"maxfev": 200})
        lams.append(math.exp(nm.x[1]))
    return {"cell": cell_i, "rep": rep, "truth": cell, "fitted": fit["params"], "J": fit["J"],
            "n_stocks_fit": int(len(rows)), "lam_ci95": [float(np.percentile(lams, 2.5)), float(np.percentile(lams, 97.5))]}


def stage_recovery(workers=4):
    t0 = time.time()
    jobs = [(ci, rep, SEED_REC0 + ci * N_REPS + rep) for ci in range(len(RECOVERY_CELLS)) for rep in range(N_REPS)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(_one_recovery, jobs))
    cells = {}
    for r in results:
        cells.setdefault(r["cell"], []).append(r)
    summary = []
    for ci, rs in sorted(cells.items()):
        truth = RECOVERY_CELLS[ci]
        row = {"cell": truth, "n_reps": len(rs)}
        if truth["lam"] > 0:
            for k in ("nu", "lam", "sJ"):
                errs = [abs(x["fitted"][k] - truth[k]) / truth[k] for x in rs]
                row[f"med_rel_err_{k}"] = float(np.median(errs))
        else:
            row["lam_fitted"] = [x["fitted"]["lam"] for x in rs]
            row["lam_ci_includes_0ish"] = [bool(x["lam_ci95"][0] <= 1.5e-5) for x in rs]
        summary.append(row)
    pos = [r for r in summary if "med_rel_err_nu" in r]
    usable = (all(float(np.median([r[f"med_rel_err_{k}"] for r in pos])) <= USABILITY_ERR for k in ("nu", "lam", "sJ"))
              and sum(next(r for r in summary if "lam_fitted" in r)["lam_ci_includes_0ish"]) >= 4)
    out = {"design": {"cells": RECOVERY_CELLS, "n_reps": N_REPS, "stocks": REC_STOCKS, "days": REC_DAYS,
                      "seed0": SEED_REC0, "usability": f"median rel err <= {USABILITY_ERR} on nu, lam, sJ over "
                      f"lam>0 cells; lam=0 cell: 95% interval includes 0 in >= 4/5 reps"},
           "per_cell": summary, "replicates": results,
           "pooled_median_rel_err": {k: float(np.median([r[f"med_rel_err_{k}"] for r in pos])) for k in ("nu", "lam", "sJ")},
           "usable": bool(usable), "seconds": round(time.time() - t0)}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "recovery.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: out[k] for k in ("per_cell", "pooled_median_rel_err", "usable")}, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["panel", "fit", "fit-fallback", "recovery"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.stage == "panel":
        stage_panel()
    elif a.stage == "fit":
        stage_fit()
    elif a.stage == "fit-fallback":
        stage_fit(pin_nu=4.86, tag="_fallback")
    else:
        stage_recovery(a.workers)


if __name__ == "__main__":
    main()
