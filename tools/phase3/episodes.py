"""
E3.3 / E3.4 shared episode estimator (PREREG_PHASE_3.md sections 5 and 6).

One code path measures the panel and the generator, so the mechanism comparison is like for like:
  * drawdown episodes: peak (new running max) -> trough (min before recovery to the prior peak or sample end),
    qualifying iff depth <= -30 %;
  * run-up episodes (GSY-style): top day tau with P_tau >= 2 x min over (tau-504, tau], a local max of
    (tau-10, tau+10), >= 252 d after the previous accepted tau;
  * windows (trading days): panic = 20 d ending at d* (the day of the smallest trailing 20-day log return,
    searched over (peak, trough+20]); deterioration = 40 d ending at d*-20; stabilisation = 60 d from trough+1;
    pre-event calm = 120 d ending at peak-1 (>= `min_calm` valid days required); mania = 40 d ending at b*-20,
    blow-off = 20 d ending at b* (b* = largest trailing 20-day return in (tau-126, tau]), post-top = 60 d from
    tau+1, run-up calm = 120 d ending at the 504-day argmin;
  * RV(window) = mean of squared daily log returns (uncentred); multipliers = RV(window)/RV(calm);
  * rise time = onset (first day P <= 0.9 x episode peak) -> day of max rolling-21d RV over [onset, trough+60];
    decay half-life = days from the RV peak to the first day rolling RV <= RV_calm + (RV_peak - RV_calm)/2,
    censored at 250 d post-peak; stress spell = days between first and last crossing of the half-way level.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

DD_DEPTH = -0.30
RUNUP_MIN = 2.0
RUNUP_WIN = 504
RUNUP_LOCAL = 10
RUNUP_GAP = 252
W_PANIC, W_DET, W_STAB, W_CALM = 20, 40, 60, 120
RV_WIN = 21
DECAY_CENSOR = 250
MIN_CALM = 60


def rolling_rv(r: np.ndarray, win: int = RV_WIN) -> np.ndarray:
    """Trailing mean of squared returns; NaN until `win` observations exist."""
    r2 = np.asarray(r, float) ** 2
    c = np.cumsum(np.insert(r2, 0, 0.0))
    out = np.full(len(r2), np.nan)
    out[win - 1:] = (c[win:] - c[:-win]) / win
    return out


def trailing_logret(logp: np.ndarray, win: int) -> np.ndarray:
    out = np.full(len(logp), np.nan)
    out[win:] = logp[win:] - logp[:-win]
    return out


def _rv(r: np.ndarray, lo: int, hi: int, min_n: int = 10) -> float:
    """RV over day indices [lo, hi) of the RETURN array; NaN if too short."""
    lo, hi = max(lo, 0), min(hi, len(r))
    if hi - lo < min_n:
        return float("nan")
    seg = r[lo:hi]
    seg = seg[np.isfinite(seg)]
    if len(seg) < min_n:
        return float("nan")
    return float(np.mean(seg ** 2))


def drawdown_episodes(p: np.ndarray) -> List[Dict]:
    """Qualifying drawdown episodes on a price path (NaNs allowed; indices refer to the input array)."""
    p = np.asarray(p, float)
    n = len(p)
    out = []
    peak_i = 0
    i = 1
    while i < n:
        if np.isfinite(p[i]) and (not np.isfinite(p[peak_i]) or p[i] >= p[peak_i]):
            peak_i = i
            i += 1
            continue
        # inside a drawdown: find recovery or end
        j = i
        trough_i = i
        while j < n and not (np.isfinite(p[j]) and p[j] >= p[peak_i]):
            if np.isfinite(p[j]) and (not np.isfinite(p[trough_i]) or p[j] < p[trough_i]):
                trough_i = j
            j += 1
        depth = p[trough_i] / p[peak_i] - 1.0 if np.isfinite(p[trough_i]) and np.isfinite(p[peak_i]) else np.nan
        if np.isfinite(depth) and depth <= DD_DEPTH:
            out.append({"peak": peak_i, "trough": trough_i, "recovery": j if j < n else None, "depth": float(depth)})
        peak_i = j if j < n else peak_i
        i = j + 1
    return out


def runup_episodes(p: np.ndarray) -> List[Dict]:
    p = np.asarray(p, float)
    n = len(p)
    out = []
    last_tau = -10 ** 9
    for tau in range(RUNUP_WIN, n):
        if not np.isfinite(p[tau]):
            continue
        w = p[tau - RUNUP_WIN:tau + 1]
        wmin = np.nanmin(w)
        if not np.isfinite(wmin) or wmin <= 0 or p[tau] < RUNUP_MIN * wmin:
            continue
        lo, hi = max(0, tau - RUNUP_LOCAL), min(n, tau + RUNUP_LOCAL + 1)
        if p[tau] < np.nanmax(p[lo:hi]):
            continue
        if tau - last_tau < RUNUP_GAP:
            continue
        start = tau - RUNUP_WIN + int(np.nanargmin(w))
        out.append({"top": tau, "start": start, "runup": float(p[tau] / wmin)})
        last_tau = tau
    return out


def dd_windows(ep: Dict, logp: np.ndarray) -> Optional[Dict]:
    """Window index ranges [lo, hi) into the RETURN array (return i = log p_i - log p_{i-1}, so the return of
    day i has index i-1 when returns are aligned r[k] = logp[k+1]-logp[k]; here we use r indices == day index of
    the day the return lands on, i.e. r = diff(logp) and r[k] is the return INTO day k+1. To keep the mapping
    simple every caller passes r = diff(logp) and windows are stated in r-indices)."""
    peak, trough = ep["peak"], ep["trough"]
    r20 = trailing_logret(logp, W_PANIC)
    hi_search = min(trough + W_PANIC, len(logp) - 1)
    if hi_search <= peak + 1:
        return None
    seg = r20[peak + 1:hi_search + 1]
    if not np.isfinite(seg).any():
        return None
    d_star = peak + 1 + int(np.nanargmin(seg))            # day index of the panic-window end
    # r-index of the return into day t is t-1
    win = {
        "panic": (d_star - W_PANIC, d_star),
        "deterioration": (d_star - W_PANIC - W_DET, d_star - W_PANIC),
        "stabilisation": (trough, trough + W_STAB),
        "calm": (peak - 1 - W_CALM, peak - 1),
        "d_star": d_star,
    }
    return win


def runup_windows(ep: Dict, logp: np.ndarray) -> Optional[Dict]:
    tau, start = ep["top"], ep["start"]
    r20 = trailing_logret(logp, W_PANIC)
    lo = max(start, tau - 126)
    seg = r20[lo:tau + 1]
    if not np.isfinite(seg).any():
        return None
    b_star = lo + int(np.nanargmax(seg))
    return {
        "blow-off": (b_star - W_PANIC, b_star),
        "mania": (b_star - W_PANIC - W_DET, b_star - W_PANIC),
        "post-top": (tau, tau + W_STAB),
        "calm": (start - W_CALM, start),
        "b_star": b_star,
    }


def episode_multipliers(win: Dict, r: np.ndarray, keys: List[str]) -> Optional[Dict]:
    calm = _rv(r, *win["calm"], min_n=MIN_CALM)
    if not np.isfinite(calm) or calm <= 0:
        return None
    out = {"rv_calm": calm}
    for k in keys:
        rv = _rv(r, *win[k])
        out[f"m_{k}"] = rv / calm if np.isfinite(rv) else float("nan")
    return out


def rise_decay(ep: Dict, p: np.ndarray, r: np.ndarray, rv_calm: float) -> Optional[Dict]:
    """Onset -> RV21-peak rise time, post-peak decay half-life (censored at DECAY_CENSOR), stress spell."""
    peak, trough = ep["peak"], ep["trough"]
    thr = 0.9 * p[peak]
    onset = None
    for t in range(peak + 1, trough + 1):
        if np.isfinite(p[t]) and p[t] <= thr:
            onset = t
            break
    if onset is None or not np.isfinite(rv_calm) or rv_calm <= 0:
        return None
    rv = rolling_rv(r)
    lo, hi = onset - 1, min(trough + W_STAB, len(r))       # r-indices
    if hi - lo < 5:
        return None
    seg = rv[lo:hi]
    if not np.isfinite(seg).any():
        return None
    pk = lo + int(np.nanargmax(seg))
    rv_peak = rv[pk]
    if not np.isfinite(rv_peak) or rv_peak <= rv_calm:
        return None
    half = rv_calm + 0.5 * (rv_peak - rv_calm)
    decay, censored = None, True
    for t in range(pk + 1, min(pk + 1 + DECAY_CENSOR, len(r))):
        if np.isfinite(rv[t]) and rv[t] <= half:
            decay, censored = t - pk, False
            break
    # stress spell: first and last crossing of the half-way level around the peak
    above = np.where(np.isfinite(rv[lo:min(pk + 1 + DECAY_CENSOR, len(r))]) &
                     (rv[lo:min(pk + 1 + DECAY_CENSOR, len(r))] >= half))[0]
    spell = int(above[-1] - above[0] + 1) if len(above) else None
    return {"onset": onset, "rise": int(pk - (onset - 1)), "rv_peak": float(rv_peak),
            "rv_peak_over_calm": float(rv_peak / rv_calm),
            "decay_half_life": (int(decay) if decay is not None else None), "censored": bool(censored),
            "stress_spell": spell}
