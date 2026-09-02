"""
The three candidate mispricing engines of REG-4 / E2.4, in ONE vectorised scaffolding (v2.1 Phase 2).

Common to all three: log P = log V + x with log V a random walk, d log V = mu_V + sigma_V z, z a standardised
t(df_V) shock (Phase 1: mu_V FIT 0.0002281, df_V DESIGN t5); the sentiment feedback of the generator
(b_pred 0.0008 next-day, b_rev 0.0006 reversed over days 2-5, loading on x and the 20-day return) is part of the
calm dynamics of x under every engine and is kept on in all three so the comparison is like for like; no events,
no jumps (jumps are Phase 1's E1.4 placement and Phase 3's size re-fit).

  ar1      x_{t+1} = rho x_t + e_t,  rho = 2^(-1/h)               -- the honest AR(1)+GJR-GARCH-t (REG-4 option B)
  fw_v2    the v2 engine: FW DCA-HPM recursion driven by ONE GJR-GARCH-t innovation through the unit-mean weight
           (n_f sigma_f + n_c sigma_c) / w_bar                    -- REG-4 option A, the incumbent form
  fw_plus  FW's OWN two independent Gaussian demand noises (structural stochastic volatility, no GARCH) with a
           stochastic fundamental -- Pruna, Polukarov and Jennings (2016) FW+ -- REG-4 option C

e_t under ar1 and fw_v2 is the GJR-GARCH(1,1)-t of envs/v2/garch.py with (alpha, gamma, beta, nu) FIXED at
E3.1's set-A full-sample medians and the unconditional scale sbar free; fw_plus has no GARCH by construction.

This module is the SIMULATOR for the SMM only.  Equivalence with envs/v2/generator.py on the calm moments is
checked by tools/phase2/e2_3_smm.py --equivalence for the engine in force, as calm_sim.py was checked in Phase 1.
"""
from __future__ import annotations

import math
from typing import Dict, Optional, Sequence

import numpy as np

# E3.1 set-A full-sample medians (generated/v2_1/e3_1/summary.md), used as the fixed GARCH shape
GARCH_E31 = dict(alpha=0.027, gamma=0.058, beta=0.932, df=4.86)
MU_V_FIT = 0.0002281
DF_V = 5.0
B_PRED, B_REV = 0.0008, 0.0006
ENGINES = ("ar1", "fw_v2", "fw_plus")

# free-parameter names per engine (order fixed here and used by every optimiser and every output file)
FREE = {
    "ar1": ("sigma_V", "sbar", "h"),
    "fw_v2": ("sigma_V", "sbar", "phi", "chi", "alpha_0", "alpha_n", "alpha_p"),
    "fw_plus": ("sigma_V", "sigma_f", "sigma_c", "phi", "chi", "alpha_0", "alpha_n", "alpha_p"),
}
# parameters searched on the log scale (alpha_0 is signed and is searched on the natural scale)
LOG_PARS = {"sigma_V", "sbar", "h", "phi", "chi", "sigma_f", "sigma_c", "alpha_p", "alpha_n"}
BOUNDS = {
    "sigma_V": (0.001, 0.05), "sbar": (0.003, 0.06), "h": (2.0, 1500.0),
    "phi": (0.005, 5.0), "chi": (0.02, 4.0), "alpha_0": (-4.0, 4.0), "alpha_n": (0.02, 8.0),
    "alpha_p": (0.05, 400.0), "sigma_f": (0.05, 5.0), "sigma_c": (0.05, 8.0),
}
DEFAULTS = dict(sigma_V=0.006, sbar=0.017, h=150.0, phi=0.12, chi=1.50, alpha_0=-0.327, alpha_n=1.79,
                alpha_p=18.43, sigma_f=0.758, sigma_c=2.087, beta=1.0, mu=0.01, price_scale=1.0,
                w_bar=0.7611251383007557, mu_V=MU_V_FIT, df_V=DF_V, b_pred=B_PRED, b_rev=B_REV)


def theta_to_params(engine: str, theta: Sequence[float], base: Optional[Dict] = None) -> Dict:
    p = dict(DEFAULTS if base is None else base)
    for k, v in zip(FREE[engine], theta):
        p[k] = float(v)
    return p


def simulate(engine: str, n_paths: int, T: int, p: Dict, seed: int = 0, burn: int = 500,
             sentiment: bool = True) -> Dict[str, np.ndarray]:
    """Vectorised over paths.  Returns logP, x, logV, n_f as (T, n_paths) after `burn` warm-up steps."""
    from envs.v2.observables import SENT_RHO, SENT_B_RET, SENT_EPS, SENT_SD_REF, SIGMA_R_REF
    rng = np.random.default_rng(seed)
    n, L = n_paths, burn + T
    g = GARCH_E31
    x = np.zeros(n)
    x_prev = np.zeros(n)
    n_f = np.full(n, 0.5)
    sbar = float(p.get("sbar", 0.017))
    hvar = np.full(n, sbar ** 2)
    e_prev = np.zeros(n)
    logV = np.zeros(n)
    pers = g["alpha"] + 0.5 * g["gamma"] + g["beta"]
    omega = sbar ** 2 * (1.0 - pers)
    if engine == "fw_plus":
        zf = rng.standard_normal((L, n)) * float(p["sigma_f"]) * float(p["mu"])
        zc = rng.standard_normal((L, n)) * float(p["sigma_c"]) * float(p["mu"])
        eta = None
    else:
        eta = rng.standard_t(g["df"], (L, n)) / math.sqrt(g["df"] / (g["df"] - 2.0))
    dfv = p.get("df_V", DF_V)
    zV = (rng.standard_normal((L, n)) if dfv is None
          else rng.standard_t(dfv, (L, n)) / math.sqrt(dfv / (dfv - 2.0)))
    rho_ar1 = 2.0 ** (-1.0 / float(p["h"])) if engine == "ar1" else None
    lag = np.abs(rng.integers(-5, 6, n))
    eps_s = rng.standard_normal((L, n))
    pending = np.zeros((L + 8, n))
    s_raw = np.zeros(n)
    m_prev = np.zeros(n)
    logP_hist = np.zeros((L, n))
    x_hist = np.zeros((L, n))
    ar = np.arange(n)
    X = np.empty((T, n))
    LV = np.empty((T, n))
    NF = np.empty((T, n))
    for i in range(L):
        k = i - burn
        if k >= 0:
            X[k] = x
            LV[k] = logV
            NF[k] = n_f
        logP = logV + x
        logP_hist[i] = logP
        x_hist[i] = x
        if sentiment:
            r_i = logP - logP_hist[i - 1] if i > 0 else np.zeros(n)
            ret20 = logP - logP_hist[max(0, i - 20)]
            x_lag = x_hist[np.maximum(i - lag, 0), ar]
            m_t = 0.6 * np.tanh(2.0 * x_lag) + 0.3 * np.tanh(ret20 / 0.15)
            s_raw = m_t + SENT_RHO * (s_raw - m_prev) + SENT_B_RET * (r_i / SIGMA_R_REF) + SENT_EPS * eps_s[i]
            m_prev = m_t
            s_std = np.tanh(s_raw) / SENT_SD_REF
            pending[i] += float(p["b_pred"]) * s_std
            pending[i + 1:i + 5] -= (float(p["b_rev"]) / 4.0) * s_std
        drift = pending[i]
        if engine == "fw_plus":
            n_c = 1.0 - n_f
            d_f = float(p["phi"]) * (-x)
            d_c = float(p["chi"]) * (x - x_prev)
            x_new = x + float(p["mu"]) * (n_f * d_f + n_c * d_c) + n_f * zf[i] + n_c * zc[i] + drift
        else:
            lev = np.where(e_prev < 0, g["gamma"] * e_prev ** 2, 0.0)
            hvar = omega + g["alpha"] * e_prev ** 2 + lev + g["beta"] * hvar
            e = np.sqrt(hvar) * eta[i]
            e_prev = e
            if engine == "ar1":
                x_new = rho_ar1 * x + e + drift
            else:
                n_c = 1.0 - n_f
                w = (n_f * float(p["sigma_f"]) + n_c * float(p["sigma_c"])) / float(p["w_bar"])
                d_f = float(p["phi"]) * (-x)
                d_c = float(p["chi"]) * (x - x_prev)
                x_new = x + float(p["mu"]) * (n_f * d_f + n_c * d_c) + w * e + drift
        if engine != "ar1":
            a = (float(p["alpha_0"]) + float(p["alpha_n"]) * (2.0 * n_f - 1.0)
                 + float(p["alpha_p"]) * (float(p["price_scale"]) * x) ** 2)
            n_f = 1.0 / (1.0 + np.exp(-float(p["beta"]) * np.clip(a, -50.0, 50.0)))
        x_prev, x = x, x_new
        logV = logV + float(p["mu_V"]) + float(p["sigma_V"]) * zV[i]
    return {"x": X, "logV": LV, "logP": LV + X, "n_f": NF}


def pooled_moments(engine: str, n_paths: int, T: int, p: Dict, seed: int = 0, burn: int = 500) -> np.ndarray:
    from tools.phase2.moments import pooled
    return pooled(simulate(engine, n_paths, T, p, seed=seed, burn=burn)["logP"])
