"""
E3.5 panel side (PREREG_PHASE_3.md section 7.1): the IV premium pi and the noise eps, FIT on the five CBOE
single-stock VIX histories against the same past-only GJR filter the generator will run.

    python -m tools.phase3.e3_5_premium

Per name (VXAPL/AAPL, VXAZN/AMZN, VXGOG/GOOG, VXGS/GS, VXIBM/IBM; IV clipped to the price panel,
2011-01-07..2024-12-31): a GJR-GARCH(1,1) filter with the ADOPTED shape (E3.1 medians alpha 0.027, gamma 0.058,
beta 0.932) and per-name omega = sample unconditional variance x (1 - persistence), run on the full 2000-2024
demeaned daily log returns (11 years of warm-up before the first IV date); 21-day mean-variance forecast
sigma2_fc,t from the state after day t; relative level l_t = sigma2_fc,t / uncond.

Fit: y_t = log(IV_t/100) - log sqrt(252 sigma2_fc,t) = log(1 + pi_t) + eps_t on the family
  M0: y = a;  M1: y = a + b log l;  M2: y = a + b log l + c (log l)^2
selected by leave-one-name-out CV MSE with the 1-SE rule (fewer parameters win inside one SE). eps: pooled
residual AR(1) rho and innovation sd (per-name, medians; AR(1) adopted iff the median rho's stock-bootstrap
95 % interval excludes 0 -- with 5 names the interval is the min-max range and is stated as such).

Output: docs/env_v2/generated/v2_1/e3_5/premium.{json,md}
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GEN = os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1")
OUT = os.path.join(GEN, "e3_5")
NAMES = {"VXAPL": "AAPL", "VXAZN": "AMZN", "VXGOG": "GOOG", "VXGS": "GS", "VXIBM": "IBM"}
SHAPE = {"alpha": 0.027, "gamma": 0.058, "beta": 0.932}     # E3.1 set-A full-sample medians (adopted, PREREG 3.2)
IV_START, IV_END = "2011-01-07", "2024-12-31"
HORIZON = 21


def gjr_filter_forecast(r: np.ndarray, alpha: float, gamma: float, beta: float, omega: float, h0: float):
    """Past-only filter: h_{t+1} = omega + alpha e_t^2 + gamma e_t^2 1[e_t<0] + beta h_t; the forecast after
    observing day t is the mean conditional variance over the next HORIZON days."""
    pers = alpha + gamma / 2.0 + beta
    uncond = omega / (1.0 - pers)
    n = len(r)
    fc = np.empty(n)
    h = h0
    for t in range(n):
        e = r[t]
        lev = gamma * e * e if e < 0 else 0.0
        h = omega + alpha * e * e + lev + beta * h        # h_{t+1}: conditional variance of day t+1
        v = h
        tot = 0.0
        for _ in range(HORIZON):
            tot += v
            v = uncond + pers * (v - uncond)
        fc[t] = tot / HORIZON
    return fc, uncond


def load_name(vx: str, tick: str):
    iv = pd.read_parquet(os.path.join(ROOT, "datasets", "05_implied_vol", "cboe", f"{vx}.parquet"))
    iv["DATE"] = pd.to_datetime(iv["DATE"])
    iv = iv[(iv["DATE"] >= IV_START) & (iv["DATE"] <= IV_END)].set_index("DATE")["CLOSE"].astype(float)
    px = pd.read_parquet(os.path.join(ROOT, "datasets", "01_prices", "daily", f"{tick}.parquet"),
                         columns=["Date", "Adj Close"])
    px = px[(px["Date"] >= "2000-01-03") & (px["Date"] <= IV_END)].set_index("Date")["Adj Close"].astype(float).ffill()
    r = np.log(px).diff().dropna()
    r = r - r.mean()                                       # full-sample demeaning (offline fit; stated)
    omega = float(r.var() * (1.0 - (SHAPE["alpha"] + SHAPE["gamma"] / 2 + SHAPE["beta"])))
    fc, uncond = gjr_filter_forecast(r.to_numpy(), SHAPE["alpha"], SHAPE["gamma"], SHAPE["beta"], omega,
                                     h0=float(r.var()))
    fc_s = pd.Series(fc, index=r.index)
    df = pd.DataFrame({"iv": iv}).join(fc_s.rename("fc"), how="inner").dropna()
    df = df[df["fc"] > 0]
    df["y"] = np.log(df["iv"] / 100.0) - np.log(np.sqrt(252.0 * df["fc"]))
    df["logl"] = np.log(df["fc"] / uncond)
    df["name"] = tick
    return df


def ols(X, y):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b


def design(df, k):
    cols = [np.ones(len(df))]
    if k >= 1:
        cols.append(df["logl"].to_numpy())
    if k >= 2:
        cols.append(df["logl"].to_numpy() ** 2)
    return np.column_stack(cols)


def main():
    t0 = time.time()
    frames = [load_name(vx, t) for vx, t in NAMES.items()]
    data = pd.concat(frames)
    names = sorted(data["name"].unique())
    cv = {}
    for k in (0, 1, 2):
        errs = []
        for held in names:
            tr, te = data[data["name"] != held], data[data["name"] == held]
            b = ols(design(tr, k), tr["y"].to_numpy())
            e = te["y"].to_numpy() - design(te, k) @ b
            errs.append(float(np.mean(e ** 2)))
        cv[k] = {"per_name_mse": dict(zip(names, np.round(errs, 5))), "mean_mse": float(np.mean(errs)),
                 "se_mse": float(np.std(errs, ddof=1) / math.sqrt(len(errs)))}
    best = min(cv, key=lambda k: cv[k]["mean_mse"])
    adopt = best
    for k in range(best):                                   # 1-SE rule: smallest family within one SE of the best
        if cv[k]["mean_mse"] <= cv[best]["mean_mse"] + cv[best]["se_mse"]:
            adopt = k
            break
    b = ols(design(data, adopt), data["y"].to_numpy())
    data["resid"] = data["y"].to_numpy() - design(data, adopt) @ b
    per_name = {}
    rhos, sds = [], []
    for t, g in data.groupby("name"):
        e = g["resid"].to_numpy()
        rho = float(np.corrcoef(e[:-1], e[1:])[0, 1])
        inn = e[1:] - rho * e[:-1]
        bn = ols(design(g, adopt), g["y"].to_numpy())
        per_name[t] = {"n": int(len(g)), "coef": [float(x) for x in bn], "rho_eps": round(rho, 4),
                       "sd_eps_innov": round(float(np.std(inn, ddof=1)), 4),
                       "resid_sd": round(float(np.std(e, ddof=1)), 4),
                       "mean_iv": round(float(g["iv"].mean()), 2), "min_iv": round(float(g["iv"].min()), 2),
                       "mean_premium": round(float(np.expm1(np.median(g["y"]))), 4)}
        rhos.append(rho)
        sds.append(float(np.std(inn, ddof=1)))
    rho_med, sd_med = float(np.median(rhos)), float(np.median(sds))
    out = {
        "design": {"names": NAMES, "iv_window": [IV_START, IV_END], "filter_shape": SHAPE,
                   "omega_rule": "per-name sample unconditional variance x (1 - persistence); returns demeaned "
                                 "by the full-sample mean (offline fit only; the generator filter uses mean 0)",
                   "horizon_days": HORIZON, "family": {0: "const", 1: "a + b log l", 2: "a + b log l + c (log l)^2"},
                   "selection": "leave-one-name-out CV MSE, 1-SE rule"},
        "cv": cv, "cv_best": best, "adopted_family": adopt,
        "pooled_coef": [float(x) for x in b],
        "per_name": per_name,
        "eps": {"rho_median": round(rho_med, 4), "rho_range": [round(min(rhos), 4), round(max(rhos), 4)],
                "sd_innov_median": round(sd_med, 4), "sd_innov_range": [round(min(sds), 4), round(max(sds), 4)],
                "adopt_ar1": bool(min(rhos) > 0 or max(rhos) < 0),
                "note": "with 5 names the 'interval' is the min-max range across names (stated as such)"},
        "pooled": {"n_days": int(len(data)), "mean_y": round(float(data["y"].mean()), 4),
                   "median_premium": round(float(np.expm1(np.median(data["y"]))), 4),
                   "min_iv_pooled": round(float(data["iv"].min()), 2),
                   "corr_logl_y": round(float(np.corrcoef(data["logl"], data["y"])[0, 1]), 3)},
        "literature_beside": {
            "Carr & Wu 2009 (RFS, read by the plan's pass)": "individual-stock log VRPs negative for 21 of 35 names",
            "Christensen & Prabhala 1998 (JFE)": "log RV on log IV slope 0.76, R^2 39 % (S&P 100, monthly)",
            "Goyal & Saretto 2009 (JFE)": "sorts on log(RV/IV)"},
        "caveat": "five mega-caps (REG-15 / plan section 3): the premium of the median S&P name may differ; "
                  "stated wherever the fit is quoted",
        "seconds": round(time.time() - t0),
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "premium.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    L = ["# E3.5 IV premium fitted on the five CBOE single-stock VIX histories (PREREG_PHASE_3.md section 7.1)", "",
         f"Filter: GJR({SHAPE['alpha']}, {SHAPE['gamma']}, {SHAPE['beta']}), per-name omega from the sample "
         f"unconditional variance; y = log(IV/100) - log sqrt(252 fc); {len(data):,} pooled days, {IV_START}..{IV_END}.", "",
         "| family | CV MSE (mean over held-out names) | SE |", "|---|---|---|"]
    for k in (0, 1, 2):
        mark = " **adopted**" if k == adopt else (" (best raw)" if k == best and k != adopt else "")
        L.append(f"| M{k}: {out['design']['family'][k]} | {cv[k]['mean_mse']:.5f} | {cv[k]['se_mse']:.5f}{mark} |")
    L += ["", f"Pooled coefficients (M{adopt}): {np.round(b, 4).tolist()}; median premium "
          f"{out['pooled']['median_premium']:+.3f}; corr(log l, y) = {out['pooled']['corr_logl_y']}.",
          f"eps: AR(1) rho median {rho_med:.3f} (range {out['eps']['rho_range']}), innovation sd median "
          f"{sd_med:.4f} (range {out['eps']['sd_innov_range']}); adopt AR(1) = {out['eps']['adopt_ar1']}.",
          f"Pooled minimum IV {out['pooled']['min_iv_pooled']} (the floor-replacement anchor).", "",
          "| name | n | coef | rho_eps | sd_eps | mean IV | min IV | median premium |", "|---|---|---|---|---|---|---|---|"]
    for t, d in per_name.items():
        L.append(f"| {t} | {d['n']} | {np.round(d['coef'], 3).tolist()} | {d['rho_eps']} | {d['sd_eps_innov']} | "
                 f"{d['mean_iv']} | {d['min_iv']} | {d['mean_premium']:+.3f} |")
    L += ["", out["caveat"] + ".", "",
          "Literature beside (not tolerances): " + "; ".join(f"{k}: {v}" for k, v in out["literature_beside"].items()) + "."]
    with open(os.path.join(OUT, "premium.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
