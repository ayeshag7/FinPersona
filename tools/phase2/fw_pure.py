"""
Franke & Westerhoff (2012, JEDC 36:1193-1211) DCA-HPM in its OWN form, vectorised over runs (v2.1 Phase 2, E2.1).

Read at source (PDF served at the Bamberg URL of PLAN section 0.2; re-read 1 Sep 2026, 36 pp.):

  eq. (1)   r_t := 100 (p_t - p_{t-1})                      -- p_t is the (natural) log price
  eq. (5)   p_t = p_{t-1} + mu (n^f_{t-1} d^f_{t-1} + n^c_{t-1} d^c_{t-1})
  eq. (6)   d^f_t = phi (p* - p_t) + eps^f_t,  eps^f_t ~ N(0, sigma_f^2)
  eq. (7)   d^c_t = chi (p_t - p_{t-1}) + eps^c_t, eps^c_t ~ N(0, sigma_c^2)
  (DCA)     n^f_t = 1 / (1 + exp(-beta a_{t-1})),  n^c_t = 1 - n^f_t
  (HPM)     a_t = alpha_n (n^f_t - n^c_t) + alpha_o + alpha_p (p_t - p*)^2
  Table 1, DCA-HPM: phi 0.12, chi 1.50, alpha_o -0.327, alpha_n 1.79, alpha_p 18.43, sigma_f 0.758,
  sigma_c 2.087; mu = 0.01 and beta = 1 are normalisations common to the DCA versions.
  Table 2: moment-specific bootstrap p-value 32.6 % (the best of the seven variants).

TWO independent Gaussian demand noises (the paper's structural stochastic volatility: sigma_t^2 =
(n^f_{t-1})^2 sigma_f^2 + (n^c_{t-1})^2 sigma_c^2), no GARCH, no jumps, no drift, p* constant.  This is NOT the
v2 engine: v2 drives ONE GJR-GARCH-t innovation through the unit-mean weight (n_f sigma_f + n_c sigma_c) / w_bar
and evaluates the misalignment term at price_scale = 100.  `price_scale` here multiplies (p_t - p*) inside the
misalignment term only, exactly as `envs/v2/mispricing.py` does, so the two conventions can be compared.

Reproduction target (SABCEMM, Glas, Trimborn, Otte et al., arXiv:1812.02726, read at source 1 Sep 2026;
Table 1, 200 runs x 7,000 time steps, parameters of their Table 9 = FW's DCA-HPM with p* = p_0 = 1):
    DCA-HPM   excess kurtosis 10.033   Hill estimator 2.481   average chartist share 0.1674
    DCA-WHP   excess kurtosis 8.01     Hill estimator 3.1192  average chartist share 0.2227
    DCA-WP    excess kurtosis 7.7600   Hill estimator 3.1314  average chartist share 0.2285
(The plan's "0.23 / 7.8" is none of the DCA-HPM figures; see PREREG_PHASE_2.md section 3.)
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Optional

import numpy as np

# FW 2012, Table 1, DCA-HPM column (read at source)
DCA_HPM = dict(phi=0.12, chi=1.50, sigma_f=0.758, sigma_c=2.087, alpha_0=-0.327, alpha_n=1.79,
               alpha_p=18.43, beta=1.0, mu=0.01)
# FW 2012, Table 1, DCA-WHP column (wealth + herding + predisposition; no misalignment term)
DCA_WHP = dict(phi=1.00, chi=0.90, sigma_f=0.741, sigma_c=1.705, alpha_0=2.100, alpha_n=1.28,
               alpha_p=0.0, beta=1.0, mu=0.01, alpha_w=2668.0, eta=0.987)
# Pruna, Polukarov & Jennings 2016 (arXiv:1604.08824), Table 1 (read at source 1 Sep 2026)
PRUNA_2016 = dict(phi=0.121, chi=1.555, sigma_f=0.592, sigma_c=1.917, alpha_0=-0.301, alpha_n=1.990,
                  alpha_p=22.741, beta=1.0, mu=0.01)


@dataclass
class PureParams:
    phi: float = 0.12
    chi: float = 1.50
    sigma_f: float = 0.758
    sigma_c: float = 2.087
    alpha_0: float = -0.327
    alpha_n: float = 1.79
    alpha_p: float = 18.43
    beta: float = 1.0
    mu: float = 0.01
    price_scale: float = 1.0

    def to_dict(self) -> Dict:
        return asdict(self)


def simulate_pure(n_runs: int, T: int, p: PureParams, seed: int = 0, burn: int = 0,
                  p_star: float = 0.0) -> Dict[str, np.ndarray]:
    """FW's own DCA-HPM.  Returns dict with `p` (T, n) log prices, `n_c` (T, n) chartist shares,
    `r` (T-1, n) returns in FW's percentage-point units (eq. 1).  `burn` steps are discarded first."""
    rng = np.random.default_rng(seed)
    n = n_runs
    L = burn + T
    zf = rng.standard_normal((L, n)) * p.sigma_f
    zc = rng.standard_normal((L, n)) * p.sigma_c
    x = np.zeros(n)              # p_t - p_star
    x_prev = np.zeros(n)
    n_f = np.full(n, 0.5)
    P = np.empty((T, n)); NC = np.empty((T, n))
    for i in range(L):
        k = i - burn
        if k >= 0:
            P[k] = p_star + x
            NC[k] = 1.0 - n_f
        d_f = p.phi * (-x) + zf[i]
        d_c = p.chi * (x - x_prev) + zc[i]
        x_new = x + p.mu * (n_f * d_f + (1.0 - n_f) * d_c)
        a = p.alpha_0 + p.alpha_n * (2.0 * n_f - 1.0) + p.alpha_p * (p.price_scale * x) ** 2
        a = np.clip(a, -50.0, 50.0)
        n_f = 1.0 / (1.0 + np.exp(-p.beta * a))
        x_prev, x = x, x_new
    return {"p": P, "n_c": NC, "r": 100.0 * np.diff(P, axis=0)}


def excess_kurtosis(r: np.ndarray) -> np.ndarray:
    """Per column (Fisher, population estimator: m4/m2^2 - 3), as `scipy.stats.kurtosis` default."""
    d = r - r.mean(axis=0)
    m2 = (d ** 2).mean(axis=0)
    m4 = (d ** 4).mean(axis=0)
    return m4 / m2 ** 2 - 3.0


def hill_index(v: np.ndarray, frac: float = 0.05) -> np.ndarray:
    """Hill TAIL INDEX 1/gamma per column, gamma = (1/k) sum_{i<=k} ln v_(i) - ln v_(k) on the largest k = frac*T
    of |r| (FW 2012 Appendix A1; their Table A1 reports 1/Hill = gamma = 0.301 for the S&P 500)."""
    g = hill_gamma(v, frac)
    return 1.0 / g


def hill_gamma(v: np.ndarray, frac: float = 0.05) -> np.ndarray:
    a = np.abs(v)
    T = a.shape[0]
    k = max(2, int(round(frac * T)))
    s = -np.sort(-a, axis=0)                      # descending
    lo = np.log(np.maximum(s[k - 1], 1e-300))
    return np.log(np.maximum(s[:k], 1e-300)).mean(axis=0) - lo
