"""
Moment vectors for v2.1 Phase 2 (E2.1, E2.3, E2.4).

FW's nine (Franke & Westerhoff 2012, section 2, read at source; returns in percentage points, r = 100 dlog P):
    m1 ACF(1) of raw returns
    m2 1/Hill  = gamma-hat on the largest 5 % of |r|   (their Table A1 row "1/Hill")
    m3 mean |r|
    m4..m9 ACF of |r| at lags 1, 5, 10, 25, 50, 100, each SMOOTHED by the centred three-lag average
           (footnote 9: at lag tau the mean of tau-1, tau, tau+1; at tau = 1 the mean of lags 1 and 2)

Persistence-carrying (PLAN section 6, E2.3):
    VR(k) at k = 20, 60, 120, 250, 500 (Lo-MacKinlay overlapping estimator with the small-sample correction,
        tools/phase1/e1_2_vr.vr_moments -- shared with E1.2 so the two phases use one estimator)
    ACF of log(P / SMA250) at lags 20, 60, 120

Panel convention: the moment vector is computed per stock (or per simulated path) and POOLED as the
cross-sectional mean, exactly as E1.2 pooled its variance ratios.

Empirical anchors read at source (never used as tolerances):
  FW 2012 Table A1, S&P 500 1980-2007, T = 6866 (measured [lower, upper] 95 % CI):
    rAC-1 -0.008 [-0.042, 0.027] | 1/Hill 0.301 [0.269, 0.334] | vMean 0.713 [0.672, 0.754]
    vAC-1 0.193 [0.106, 0.280] | vAC-5 0.187 [0.142, 0.231] | vAC-10 0.159 [0.118, 0.200]
    vAC-25 0.128 [0.095, 0.162] | vAC-50 0.112 [0.074, 0.148] | vAC-100 0.074 [0.041, 0.105]
  FW 2012 Table 4, DCA-HPM moment coverage ratios (%) over 5,000 MC runs of T' = 6750:
    joint 10.1; per moment 98.1 / 79.5 / 75.8 / 98.5 / 65.5 / 73.7 / 59.5 / 39.4 / 32.4
"""
from __future__ import annotations

import os
import sys
from typing import Dict, Optional, Sequence, Tuple

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

FW_LAGS = (1, 5, 10, 25, 50, 100)
VR_KS = (20, 60, 120, 250, 500)
ACF_LAGS = (20, 60, 120)
FW_NAMES = ["rAC1", "invHill", "vMean"] + [f"vAC{l}" for l in FW_LAGS]
PERS_NAMES = [f"VR{k}" for k in VR_KS] + [f"acfSMA{l}" for l in ACF_LAGS]
ALL_NAMES = FW_NAMES + PERS_NAMES
# FW 2012 Table A1 (read at source): measured value and the 95 % CI bounds
FW_TABLE_A1 = {
    "rAC1": (-0.008, -0.042, 0.027), "invHill": (0.301, 0.269, 0.334), "vMean": (0.713, 0.672, 0.754),
    "vAC1": (0.193, 0.106, 0.280), "vAC5": (0.187, 0.142, 0.231), "vAC10": (0.159, 0.118, 0.200),
    "vAC25": (0.128, 0.095, 0.162), "vAC50": (0.112, 0.074, 0.148), "vAC100": (0.074, 0.041, 0.105)}
# FW 2012 Table 4, DCA-HPM column (5,000 MC runs, T' = 6750)
FW_TABLE_4_DCA_HPM = {"joint": 10.1, "rAC1": 98.1, "invHill": 79.5, "vMean": 75.8, "vAC1": 98.5,
                      "vAC5": 65.5, "vAC10": 73.7, "vAC25": 59.5, "vAC50": 39.4, "vAC100": 32.4}


def _acf(a: np.ndarray, lag: int) -> np.ndarray:
    """ACF at `lag` for each column of (T, N), demeaned, denominator = full-sample variance."""
    d = a - a.mean(axis=0)
    num = (d[:-lag] * d[lag:]).sum(axis=0)
    den = (d * d).sum(axis=0)
    return num / np.maximum(den, 1e-300)


def _needed_lags(lags: Sequence[int]) -> Sequence[int]:
    need = set()
    for l in lags:
        need |= {1, 2} if l == 1 else {l - 1, l, l + 1}
    return sorted(need)


def fw_moments(r: np.ndarray, tail_frac: float = 0.05, cols: Optional[Sequence[int]] = None) -> np.ndarray:
    """FW's nine moments per column of `r` (T, N) with r in percentage points.  Returns (N, 9), or (N, len(cols))
    if `cols` selects a subset of the nine (only the ACF lags those columns need are computed)."""
    from tools.phase2.fw_pure import hill_gamma
    idx = list(range(9)) if cols is None else list(cols)
    lags = [FW_LAGS[j - 3] for j in idx if j >= 3]
    v = np.abs(r) if (0 in idx or any(j >= 2 for j in idx)) else None
    acfs = {l: _acf(v, l) for l in _needed_lags(lags)} if lags else {}
    got = {}
    if 0 in idx:
        got[0] = _acf(r, 1)
    if 1 in idx:
        got[1] = hill_gamma(r, tail_frac)
    if 2 in idx:
        got[2] = v.mean(axis=0)
    for j in idx:
        if j >= 3:
            l = FW_LAGS[j - 3]
            got[j] = (acfs[1] + acfs[2]) / 2.0 if l == 1 else (acfs[l - 1] + acfs[l] + acfs[l + 1]) / 3.0
    return np.stack([got[j] for j in idx], axis=1)


def persistence_moments(logP: np.ndarray, ks: Sequence[int] = VR_KS,
                        acf_lags: Sequence[int] = ACF_LAGS, sma: int = 250) -> np.ndarray:
    """VR(k) and the ACF of log(P/SMA250) per column of `logP` (T, N).  Returns (N, len(ks)+len(acf_lags))."""
    from tools.phase1.e1_2_vr import vr_moments
    R = np.diff(logP, axis=0)
    vr = vr_moments(R, tuple(ks))[:, 1:]                     # drop Var(r_1): FW's vMean already carries the scale
    P = np.exp(logP - logP[0])                               # level-free: the SMA ratio is invariant to the start
    cs = np.cumsum(P, axis=0)
    m = (cs[sma:] - cs[:-sma]) / float(sma)
    d = np.log(P[sma:] / m)
    ac = np.stack([_acf(d, l) for l in acf_lags], axis=1)
    return np.concatenate([vr, ac], axis=1)


def moment_matrix(logP: np.ndarray) -> np.ndarray:
    """The full 17-moment vector per column of `logP` (T, N).  Returns (N, 17)."""
    r = 100.0 * np.diff(logP, axis=0)
    return np.concatenate([fw_moments(r), persistence_moments(logP)], axis=1)


def pooled(logP: np.ndarray) -> np.ndarray:
    """Cross-sectional mean of the 17 moments (the SMM target / simulated counterpart)."""
    return moment_matrix(logP).mean(axis=0)


# ------------------------------------------------------------------------------- block bootstrap of the panel
# Block lengths follow FW 2012 Appendix A2 (250 d for the five short-memory moments, 750 d for the four
# long-memory ACF(|r|) moments) and extend it to the persistence moments, whose longest horizon is VR(500):
# 1250 d (five years).  Stocks are resampled with replacement; the time blocks are SHARED across the resampled
# stocks so the cross-sectional (market-factor) dependence survives, as E1.2's joint bootstrap did.
BLOCK_OF = {"short": 250, "long": 750, "pers": 1250}
GROUP_OF = ["short"] * 5 + ["long"] * 4 + ["pers"] * 8      # rAC1, invHill, vMean, vAC1, vAC5 | vAC10..100 | VR/acf


def block_indices(T: int, block: int, rng: np.random.Generator) -> np.ndarray:
    from tools.phase1.e1_2_vr import block_indices as bi
    return bi(T, block, rng)


def pooled_cols(logP: np.ndarray, cols: Sequence[int]) -> np.ndarray:
    """Pooled (cross-sectional mean) values of the moments in `cols` only -- the columns not asked for are never
    computed, which is what makes the block bootstrap affordable."""
    cols = list(cols)
    fw_c = [j for j in cols if j < 9]
    pe_c = [j - 9 for j in cols if j >= 9]
    parts = {}
    if fw_c:
        r = 100.0 * np.diff(logP, axis=0)
        m = fw_moments(r, cols=fw_c).mean(axis=0)
        parts.update(dict(zip(fw_c, m)))
    if pe_c:
        ks = [VR_KS[j] for j in pe_c if j < len(VR_KS)]
        ls = [ACF_LAGS[j - len(VR_KS)] for j in pe_c if j >= len(VR_KS)]
        m = persistence_moments(logP, ks=ks, acf_lags=ls).mean(axis=0)
        order = [j for j in pe_c if j < len(VR_KS)] + [j for j in pe_c if j >= len(VR_KS)]
        parts.update({9 + j: v for j, v in zip(order, m)})
    return np.array([parts[j] for j in cols])


def rechain(logP: np.ndarray, ti: np.ndarray) -> np.ndarray:
    """Re-chain the resampled blocks in log-RETURN space so no artificial jump is introduced at a block join."""
    R = np.diff(logP, axis=0)
    Rb = R[np.clip(ti[:-1], 0, R.shape[0] - 1)]
    return np.vstack([np.zeros((1, logP.shape[1])), np.cumsum(Rb, axis=0)])


def bootstrap_moments(logP: np.ndarray, n_boot: int, seed: int = 0) -> np.ndarray:
    """(n_boot, 17) pooled moment vectors under the joint stock x block bootstrap.  Each moment group uses its
    own block length; the same stock resample is used for all three groups within one replicate."""
    rng = np.random.default_rng(seed)
    T, N = logP.shape
    out = np.empty((n_boot, len(ALL_NAMES)))
    groups = {g: [j for j, gg in enumerate(GROUP_OF) if gg == g] for g in BLOCK_OF}
    for b in range(n_boot):
        si = rng.integers(0, N, N)
        for g, cols in groups.items():
            ti = block_indices(T, BLOCK_OF[g], rng)
            out[b, cols] = pooled_cols(rechain(logP, ti)[:, si], cols)
    return out
