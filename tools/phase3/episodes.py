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


def drawdown_episodes(p: np.ndarray, depth_thr: float = DD_DEPTH) -> List[Dict]:
    """Qualifying drawdown episodes on a price path (NaNs allowed; indices refer to the input array).

    v2.1 Phase 4 (E4.1) added `depth_thr` so the >= 20 % family can be built from the same code path; the
    default is DD_DEPTH, so every Phase-3 call is bit-identical."""
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
        if np.isfinite(depth) and depth <= depth_thr:
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


# ---------------------------------------------------------------------------------------------------
# v2.1 Phase 4 (E4.1) additions.  Everything above is unchanged, so Phase 3's results reproduce exactly.
# PREREG_PHASE_4.md section 3.  One code path still measures the panel and the generator.
# ---------------------------------------------------------------------------------------------------

import math as _math

# Pagan-Sossounov censoring constants, scaled to DAILY data at 21 trading days per month.
# NOTE: Pagan & Sossounov's own 25/15-month durations were NOT read from the paper and are not used or
# quoted anywhere.  These are this phase's stated choices; E4.1 reports the whole table at both settings.
PS_SETTINGS = {
    "primary":   {"window": 168, "min_phase": 126, "min_cycle": 336},   # 8 / 6 / 16 months at 21 d/month
    "sensitive": {"window": 84,  "min_phase": 63,  "min_cycle": 168},   # half of each
}


def pagan_sossounov(logp: np.ndarray, window: int = 168, min_phase: int = 126,
                    min_cycle: int = 336) -> List[Dict]:
    """Bry-Boschan / Pagan-Sossounov turning-point dating on a daily log-price series.

    Returns an alternating list of {"type": "peak"|"trough", "i": index}.  Steps: (1) candidate extrema over
    a +/- `window` neighbourhood; (2) alternation enforced by keeping the more extreme of consecutive
    same-type points; (3) phases shorter than `min_phase` and cycles shorter than `min_cycle` removed;
    (4) turning points within `window` of either end censored."""
    lp = np.asarray(logp, float)
    n = len(lp)
    if n < 2 * window + 2:
        return []
    cand = []
    for t in range(window, n - window):
        if not np.isfinite(lp[t]):
            continue
        seg = lp[t - window:t + window + 1]
        if not np.isfinite(seg).any():
            continue
        if lp[t] >= np.nanmax(seg):
            cand.append({"type": "peak", "i": t})
        elif lp[t] <= np.nanmin(seg):
            cand.append({"type": "trough", "i": t})
    if not cand:
        return []

    def _alternate(seq):
        merged = []
        for c in seq:
            if merged and merged[-1]["type"] == c["type"]:
                keep_new = (lp[c["i"]] > lp[merged[-1]["i"]]) if c["type"] == "peak" \
                    else (lp[c["i"]] < lp[merged[-1]["i"]])
                if keep_new:
                    merged[-1] = c
            else:
                merged.append(c)
        return merged

    alt = _alternate(cand)
    changed = True
    while changed and len(alt) > 2:
        changed = False
        for k in range(1, len(alt)):
            if alt[k]["i"] - alt[k - 1]["i"] < min_phase:
                a, b = alt[k - 1], alt[k]
                # drop the less extreme of the too-short pair
                if b["type"] == "peak":
                    drop = k if lp[b["i"]] <= lp[a["i"]] else k - 1
                else:
                    drop = k if lp[b["i"]] >= lp[a["i"]] else k - 1
                alt.pop(drop)
                alt = _alternate(alt)
                changed = True
                break
        if changed:
            continue
        for k in range(2, len(alt)):
            if alt[k]["i"] - alt[k - 2]["i"] < min_cycle:
                alt.pop(k - 1)
                alt = _alternate(alt)
                changed = True
                break
    return [c for c in alt if window <= c["i"] < n - window]


def ps_bear_episodes(p: np.ndarray, **kw) -> List[Dict]:
    """Peak-to-trough bear phases from the Pagan-Sossounov dating, in the same dict shape as
    `drawdown_episodes` so every downstream statistic takes either family."""
    pa = np.asarray(p, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        lp = np.log(pa)
    tp = pagan_sossounov(lp, **kw)
    out = []
    for a, b in zip(tp, tp[1:]):
        if a["type"] == "peak" and b["type"] == "trough":
            out.append({"peak": a["i"], "trough": b["i"], "recovery": None,
                        "depth": float(pa[b["i"]] / pa[a["i"]] - 1.0)})
    return out


def deterioration_length(ep: Dict, p: np.ndarray, thr: float = 0.10):
    """Days from the episode peak to the first day the price is `thr` below it -- the ONSET of E3.3's
    rise-time estimator.  This is the quantity E4.2 draws `det_len` from."""
    peak, trough = ep["peak"], ep["trough"]
    if not np.isfinite(p[peak]):
        return None
    lim = (1.0 - thr) * p[peak]
    for t in range(peak + 1, trough + 1):
        if np.isfinite(p[t]) and p[t] <= lim:
            return int(t - peak)
    return None


def front_loading(ep: Dict, p: np.ndarray):
    """Share of the episode's total LOG decline completed in the first third of peak -> trough."""
    peak, trough = ep["peak"], ep["trough"]
    n = trough - peak
    if n < 3 or not (np.isfinite(p[peak]) and np.isfinite(p[trough])) or p[peak] <= 0 or p[trough] <= 0:
        return None
    total = _math.log(p[trough]) - _math.log(p[peak])
    if total >= 0:
        return None
    t3 = peak + n // 3
    if not np.isfinite(p[t3]) or p[t3] <= 0:
        return None
    return float((_math.log(p[t3]) - _math.log(p[peak])) / total)


def recovery_shares(ep: Dict, p: np.ndarray, horizons=(60, 120, 200)) -> Dict:
    """Share of the peak-to-trough fall recovered k days after the trough (1.0 = back to the peak)."""
    peak, trough = ep["peak"], ep["trough"]
    out = {}
    denom = p[peak] - p[trough]
    for k in horizons:
        t = trough + k
        if t >= len(p) or not np.isfinite(denom) or denom <= 0 or not np.isfinite(p[t]):
            out["rec%d" % k] = None
        else:
            out["rec%d" % k] = float((p[t] - p[trough]) / denom)
    return out


def runup_outcome(ep: Dict, p: np.ndarray, horizon: int = 200, drop_thr: float = -0.40) -> Dict:
    """What happened after a run-up top: the deepest drawdown within `horizon` days, when it bottomed, and
    whether it qualifies as a crash.  GSY use -40 % within two years; both the threshold and the horizon are
    parameters and both are stated wherever the number is used (here the horizon is the benchmark's 200 d)."""
    tau = ep["top"]
    hi = min(tau + horizon, len(p) - 1)
    if hi <= tau or not np.isfinite(p[tau]) or p[tau] <= 0:
        return {"post_drop": None, "post_len": None, "topped": None}
    seg = np.asarray(p, float)[tau:hi + 1]
    if not np.isfinite(seg).any():
        return {"post_drop": None, "post_len": None, "topped": None}
    j = int(np.nanargmin(seg))
    drop = float(seg[j] / p[tau] - 1.0)
    return {"post_drop": drop, "post_len": int(j), "topped": bool(drop <= drop_thr),
            "horizon": int(horizon), "drop_thr": float(drop_thr)}


def clean_runup_calm(ep: Dict, r: np.ndarray, win: int = W_CALM, gap: int = 0):
    """E4.0c's finding: E3.3's run-up 'calm' window (120 d BEFORE the 504-day argmin) sits at a post-crash
    trough and has sd 0.0413 against the drawdown family's 0.0217, so it cannot serve as that population's
    calm reference.  This is the corrected reference: the 120 d immediately AFTER the run-up's start (the
    argmin), i.e. the quiet beginning of the run-up itself rather than the crash that preceded it."""
    start = ep["start"]
    return _rv(r, start + gap, start + gap + win, min_n=MIN_CALM)


# ------------------------------------------------------------------ LPPLS (Filimonov & Sornette 2013)

def _lppls_sse(tc, m, om, t, y):
    """Linear sub-problem: given (tc, m, omega) the four linear parameters are an exact least-squares solve.
    Returns (sse, beta)."""
    dt = tc - t
    if np.any(dt <= 1e-8):
        return np.inf, None
    f = dt ** m
    ln = np.log(dt)
    X = np.column_stack([np.ones_like(t), f, f * np.cos(om * ln), f * np.sin(om * ln)])
    if not np.isfinite(X).all():
        return np.inf, None
    try:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    except np.linalg.LinAlgError:
        return np.inf, None
    res = y - X @ beta
    return float(res @ res), beta


def lppls_fit(logp: np.ndarray, i0: int, i1: int, n_restarts: int = 20, seed: int = 0,
              tc_max_ahead: int = 63):
    """Filimonov-Sornette linearised LPPLS calibration on the window [i0, i1] of a log-price series.

        log P(t) = A + B (tc-t)^m + C1 (tc-t)^m cos(w ln(tc-t)) + C2 (tc-t)^m sin(w ln(tc-t))

    (tc, m, w) are searched by Nelder-Mead from `n_restarts` random starts with a fixed seed; the four linear
    parameters are solved exactly at each evaluation.  Search bounds m in (0.01, 0.99), w in [1, 20],
    tc in (end, end + tc_max_ahead], as PREREG_PHASE_4.md section 3 registers.

    Returns the best fit plus the ACROSS-RESTART spread of m and w -- the registered stability DIAGNOSTIC,
    never a filter: population statistics are reported over all episodes and over stable ones separately."""
    from scipy.optimize import minimize
    y = np.asarray(logp, float)[i0:i1 + 1]
    if len(y) < 40 or not np.isfinite(y).all():
        return None
    t = np.arange(len(y), dtype=float)
    T = float(len(y) - 1)
    rng = np.random.default_rng(seed)
    best, ms, ws = None, [], []
    for _ in range(n_restarts):
        x0 = np.array([T + rng.uniform(1.0, tc_max_ahead), rng.uniform(0.05, 0.95), rng.uniform(2.0, 15.0)])

        def obj(z):
            tc, m, om = z
            if not (T + 0.5 <= tc <= T + tc_max_ahead and 0.01 <= m <= 0.99 and 1.0 <= om <= 20.0):
                return 1e12
            s, _ = _lppls_sse(tc, m, om, t, y)
            return s if np.isfinite(s) else 1e12

        r = minimize(obj, x0, method="Nelder-Mead",
                     options={"maxiter": 600, "xatol": 1e-4, "fatol": 1e-12})
        if not np.isfinite(r.fun) or r.fun >= 1e11:
            continue
        ms.append(float(r.x[1]))
        ws.append(float(r.x[2]))
        if best is None or r.fun < best["sse"]:
            best = {"sse": float(r.fun), "tc": float(r.x[0]), "m": float(r.x[1]), "omega": float(r.x[2])}
    if best is None or len(ms) < 3:
        return None
    sse, beta = _lppls_sse(best["tc"], best["m"], best["omega"], t, y)
    tss = float(((y - y.mean()) ** 2).sum())
    best.update({
        "n_days": int(len(y)), "n_converged": int(len(ms)),
        "r2": float(1.0 - sse / tss) if tss > 0 else float("nan"),
        "m_iqr": float(np.percentile(ms, 75) - np.percentile(ms, 25)),
        "omega_iqr": float(np.percentile(ws, 75) - np.percentile(ws, 25)),
        "m_median_restarts": float(np.median(ms)), "omega_median_restarts": float(np.median(ws)),
        "tc_days_past_end": float(best["tc"] - T),
        # the LPPLS crash hazard is h(t) ~ (tc - t)^(m-1); at the window end that is the comparable number
        "hazard_at_end": float(max(best["tc"] - T, 1e-6) ** (best["m"] - 1.0)),
        "B": float(beta[1]) if beta is not None else None,
    })
    best["stable"] = bool(best["m_iqr"] < 0.10 and best["omega_iqr"] < 2.0)
    return best
