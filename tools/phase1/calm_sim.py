"""
Vectorised (over paths) re-implementation of the v2.1 CALM generator for the E1.2 recovery study and estimator C
(PREREG_PHASE_1.md section 4.3-4.4): the FW recursion of envs/v2/mispricing.py (fallback form, phi set by the pull-rate
half-life h at the pilot n_bar), the GJR-GARCH-t of envs/v2/garch.py (alpha 0.10, gamma 0.10, beta 0.83, nu 5, sbar
free), V a random walk with standardised t(5) shocks (sigma_V free), optional mean-zero jumps, no events.

The sentiment feedback of the generator (decision 10: b_pred = 0.0008 next-day return per +1 sd of the tanh-squashed
sentiment, 0.0006 reversed over days 2-5; the sentiment itself loads on x and on returns, observables.SentimentState) is
included because it is part of the calm dynamics of x (without it sd(x) is 0.15 instead of 0.175 -- found by the
equivalence check on 29 Aug 2026). It is NOT the generator (no named streams, no burn-in convention, no observables);
its equivalence to envs.v2 on the calm moments is checked by `equivalence_check()` before it is used (pre-registered: sd(x), ACF(1) of x, return kurtosis
inside the 95 % bootstrap interval of the same statistics from envs.v2 on 100 flat T = 5,000 paths, jumps off).
"""
from __future__ import annotations

import math
from typing import Dict, Optional

import numpy as np

from envs.v2.mispricing import FW_INDEX_2012, pilot_stats, fallback_single_stock, FWParams
from envs.v2.garch import GJRParams
from envs.v2.observables import SENT_RHO, SENT_B_RET, SENT_EPS, SENT_SD_REF, SIGMA_R_REF
B_PRED, B_REV = 0.0008, 0.0006      # GenConfig defaults (decision 10)


def fw_params_for_half_life(h: float) -> FWParams:
    """The engine's own construction (fallback_single_stock) at pull-rate half-life h."""
    return fallback_single_stock(float(h))


def simulate(n_paths: int, T: int, h: float = 150.0, sigma_V: float = 0.006, sbar: float = 0.017, df_V: Optional[float] = 5.0,
             seed: int = 0, jump_rate: float = 0.0, jump_sd: float = 0.03, garch: Optional[GJRParams] = None,
             burn: int = 1000, x0: float = 0.0, b_pred: float = B_PRED, b_rev: float = B_REV,
             phi: Optional[float] = None, w_bar: Optional[float] = None) -> Dict[str, np.ndarray]:
    """Returns dict with logP (T, n), x (T, n), logV (T, n) after `burn` warm-up steps; the FW weight normalisation w_bar
    and n_bar come from the engine's cached pilot for these params (as the generator does)."""
    rng = np.random.default_rng(seed)
    if phi is not None:
        # fast path (estimator C's optimiser): phi set directly from the pull-rate half-life at the reference n_bar, and
        # the reference w_bar, instead of re-running the 20,000-step pilot for every trial value
        p = FWParams(phi=float(phi), name="calm_sim_fast")
        assert w_bar is not None
    else:
        p = fw_params_for_half_life(h)
        w_bar = pilot_stats(p, "fw_fallback_hl150")["w_bar"] if h == 150.0 else pilot_stats(p, p.name)["w_bar"]
    gp = garch or GJRParams()
    gp = GJRParams(**{**gp.__dict__, "sbar": sbar})
    L = burn + T
    n = n_paths
    x = np.full(n, x0); x_prev = np.full(n, x0); n_f = np.full(n, 0.5)
    hvar = np.full(n, gp.sbar ** 2); e_prev = np.zeros(n)
    logV = np.zeros(n)
    # sentiment feedback state (observables.SentimentState, vectorised); per-path lag |jitter| as the generator draws it
    lag = np.abs(rng.integers(-5, 6, n))
    s_raw = np.zeros(n); m_prev = np.zeros(n)
    eps_s = rng.standard_normal((L, n))
    pending = np.zeros((L + 8, n))
    logP_hist = np.zeros((L, n))
    x_hist = np.zeros((L, n))
    eta = rng.standard_t(gp.df, (L, n)) / math.sqrt(gp.df / (gp.df - 2))
    if df_V is None:
        zV = rng.standard_normal((L, n))
    else:
        zV = rng.standard_t(df_V, (L, n)) / math.sqrt(df_V / (df_V - 2))
    jumps = (rng.random((L, n)) < jump_rate) * rng.normal(0.0, jump_sd, (L, n)) if jump_rate > 0 else None
    X = np.empty((T, n)); LV = np.empty((T, n)); NF = np.empty((T, n))
    pers = gp.alpha + 0.5 * gp.gamma + gp.beta
    omega = gp.sbar ** 2 * (1 - pers)
    ar = np.arange(n)
    for i in range(L):
        k = i - burn
        if k >= 0:
            X[k] = x; LV[k] = logV; NF[k] = n_f
        # sentiment (feeds the next transitions through `pending`, as in generator._simulate_once)
        logP = logV + x
        logP_hist[i] = logP; x_hist[i] = x
        r_i = logP - logP_hist[i - 1] if i > 0 else np.zeros(n)
        ret20 = logP - logP_hist[max(0, i - 20)]
        x_lag = x_hist[np.maximum(i - lag, 0), ar]
        m_t = 0.6 * np.tanh(2.0 * x_lag) + 0.3 * np.tanh(ret20 / 0.15)
        s_raw = m_t + SENT_RHO * (s_raw - m_prev) + SENT_B_RET * (r_i / SIGMA_R_REF) + SENT_EPS * eps_s[i]
        m_prev = m_t
        s_std = np.tanh(s_raw) / SENT_SD_REF
        if b_pred:
            pending[i] += b_pred * s_std
            pending[i + 1:i + 5] -= (b_rev / 4.0) * s_std
        # GJR-GARCH step (calm: multiplier 1)
        lev = np.where(e_prev < 0, gp.gamma * e_prev ** 2, 0.0)
        hvar = omega + gp.alpha * e_prev ** 2 + lev + gp.beta * hvar
        e = np.sqrt(hvar) * eta[i]
        e_prev = e
        # FW step
        n_c = 1.0 - n_f
        w = (n_f * p.sigma_f + n_c * p.sigma_c) / w_bar
        d_f = -p.phi * x; d_c = p.chi * (x - x_prev)
        extra = jumps[i] if jumps is not None else 0.0
        x_new = x + p.mu * (n_f * d_f + n_c * d_c) + pending[i] + w * (e + extra)
        a = p.alpha_0 + p.alpha_n * (n_f - n_c) + p.alpha_p * (p.price_scale * x) ** 2
        a = np.clip(a, -50.0, 50.0)
        n_f = 1.0 / (1.0 + np.exp(-p.beta * a))
        x_prev, x = x, x_new
        logV = logV + sigma_V * zV[i]
    out = {"x": X, "logV": LV, "logP": LV + X, "n_f": NF}
    return out


def calm_moments(logP: np.ndarray, ks=(20, 60, 120, 250, 500), acf_lags=(20, 60, 120)) -> np.ndarray:
    """Moment vector used by estimator C: Var(r_1); VR(k); ACF of log(P/SMA250) at lags. logP: (T, n)."""
    from tools.phase1.e1_2_vr import vr_moments
    R = np.diff(logP, axis=0)
    m = vr_moments(R, ks).mean(axis=0)                 # [var1, VR(k)...] pooled over paths
    # log(P / SMA250): SMA of the price level
    P = np.exp(logP)
    cs = np.cumsum(P, axis=0)
    sma = (cs[250:] - cs[:-250]) / 250.0
    d = np.log(P[250:] / sma)
    acfs = []
    for L in acf_lags:
        a = d[:-L]; b = d[L:]
        a = a - a.mean(axis=0); b = b - b.mean(axis=0)
        acfs.append(float(((a * b).sum(axis=0) / np.sqrt((a * a).sum(axis=0) * (b * b).sum(axis=0))).mean()))
    return np.concatenate([m, acfs])


def equivalence_check(n_paths: int = 100, T: int = 5000, seed: int = 4242) -> Dict[str, object]:
    """Pre-registered check (section 4.3): simulator vs envs.v2 on sd(x), ACF(1) of x, return kurtosis."""
    from scipy import stats
    from envs.v2.generator import GenConfig, generate
    def stats_of(xs, rs):
        sd = np.array([x.std() for x in xs]); a1 = np.array([np.corrcoef(x[:-1], x[1:])[0, 1] for x in xs])
        ku = np.array([stats.kurtosis(r) for r in rs])
        return sd, a1, ku
    xs, rs = [], []
    for s in range(n_paths):
        r = generate(GenConfig(scenario="flat", T=T, seed=seed + s, jumps=False, reject=False))
        m = r.day >= 1
        xs.append(r.x[0, m]); rs.append(np.diff(np.log(r.P[0, m])))
    sd_g, a1_g, ku_g = stats_of(xs, rs)
    sim = simulate(n_paths, T, seed=seed)
    sd_s, a1_s, ku_s = stats_of(list(sim["x"].T), list(np.diff(sim["logP"], axis=0).T))
    rng = np.random.default_rng(0)
    out = {"n_paths": n_paths, "T": T}
    ok = True
    for name, g, s_ in (("sd_x", sd_g, sd_s), ("acf1_x", a1_g, a1_s), ("kurtosis_r", ku_g, ku_s)):
        boot = np.array([g[rng.integers(0, len(g), len(g))].mean() for _ in range(1000)])
        lo, hi = np.percentile(boot, [2.5, 97.5])
        inside = bool(lo <= s_.mean() <= hi)
        ok &= inside
        out[name] = {"generator_mean": float(g.mean()), "generator_ci95": [float(lo), float(hi)], "simulator_mean": float(s_.mean()), "inside": inside}
    out["passed"] = ok
    return out


if __name__ == "__main__":
    import json, os, sys
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, ROOT)
    r = equivalence_check()
    print(json.dumps(r, indent=1))
    with open(os.path.join(ROOT, "docs", "env_v2", "generated", "v2_1", "e1_2", "calm_sim_equivalence.json"), "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1)
