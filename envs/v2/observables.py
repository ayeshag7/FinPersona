"""
Observables v2 (plan Section 3 rows: Sentiment, Earnings/PE, Dividend, Implied
volatility, Volume, Technical indicators).  Every field is a function of the
price path, the hidden value path, the GARCH state or its own noise -- NEVER of
the phase label -- so that the composite phase clock (L2b) is passable.

  EPS / P/E      hidden multiple k ~ U(14, 22) per seed; quarterly EPS_q = V(quarter end) / (4k)
                 x exp(N(0, 0.10)); announced quarter end + U(25, 35) d; trailing-4Q P/E,
                 warm from the burn-in; cap 200.
  Dividend       payout 0.35, sticky: DPS_q = 0.7 DPS_{q-1} + 0.3 x 0.35 x EPS_q; yield = 4 DPS / P.
  Analyst FV     F_t = V_t exp(u_t), u AR(1) rho = 0.95 per weekly (5-day) update, stationary sd 0.15.
                 The error sd is FIXED ex ante (not tuned to the audit). v2.1 Phase 0 removed a sqrt(5) innovation
                 scaling that had made the implemented stationary sd 0.15 sqrt(5) = 0.335 (weakness item 68); whether
                 0.15 is the right sd is Phase 5's question (the read anchor is a 45 % absolute target-price error,
                 V2_1_PLAN_VERIFICATION_LOG.md §4.3).
  Sentiment      s_t = m_t + 0.85 (s_{t-1} - m_{t-1}) + 0.25 r_t / sigma_r + 0.25 eps_t, tanh-squashed,
                 m_t = 0.6 tanh(2 x_{t-j}) + 0.3 tanh(ret20_t / 0.15), j = |jitter| days;
                 predictive component b_pred (default +8 bp next-day return per +1 sd of s,
                 6 bp reversed over days 2-5) is applied INSIDE the generator loop.
  Volume         log Vol_t = mu_v + 0.65 (log Vol_{t-1} - mu_v) + 0.25 (|r_t| / sigma - 1) + 1.2 |x_{t-j}| + 0.30 eps.
  IV             sqrt(252 (sigma_V^2 + w_t^2 fvar21_t)) x (1 + premium) x 100, premium 0.20 (0.35 when
                 the GARCH state is in its top decile -- a STATE-based, not label-based, premium),
                 floor 12.
  Technicals     SMA20, SMA50, Wilder RSI14, MACD 12/26 + signal 9, trend_strength, trend_regime (+/-2%),
                 volume_ratio (20-day), all warm from the burn-in.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

QUARTER_DAYS = 63
EPS_NOISE_SD = 0.10
ANN_LAG = (25, 35)
K_RANGE = (14.0, 22.0)
PAYOUT = 0.35
DPS_STICKY = 0.7
ANALYST_RHO = 0.95
ANALYST_SD = 0.15
ANALYST_UPDATE_DAYS = 5
SENT_RHO = 0.85
SENT_B_RET = 0.25
SENT_EPS = 0.25
SENT_SD_REF = 0.35        # reference sd of the squashed sentiment for the 'per +1 sd' convention
SIGMA_R_REF = 0.017       # reference daily return sd for standardisation
VOL_MU = math.log(1_000_000)
VOL_RHO = 0.65
VOL_B_ABS_R = 0.25
VOL_B_ABS_X = 1.2
VOL_EPS = 0.30
IV_PREMIUM = 0.20
IV_PREMIUM_STRESS = 0.35
IV_FLOOR = 12.0
PE_CAP = 200.0


# --------------------------------------------------------------------------
# sentiment (stepped inside the generator loop; feeds back through b_pred)
# --------------------------------------------------------------------------
class SentimentState:
    def __init__(self, rng: np.random.Generator, lag: int = 0):
        self.rng = rng
        self.lag = int(abs(lag))
        self.s = 0.0
        self.m_prev = 0.0
        self.raw = 0.0

    def step(self, x_lagged: float, ret20: float, r: float) -> float:
        m = 0.6 * math.tanh(2.0 * x_lagged) + 0.3 * math.tanh(ret20 / 0.15)
        raw = m + SENT_RHO * (self.raw - self.m_prev) + SENT_B_RET * (r / SIGMA_R_REF) + SENT_EPS * self.rng.normal()
        self.raw = raw
        self.m_prev = m
        self.s = math.tanh(raw)
        return self.s


# --------------------------------------------------------------------------
# post-hoc observables from the generated arrays (one asset)
# --------------------------------------------------------------------------
def announcement_schedule(day: np.ndarray, rng: np.random.Generator) -> Dict[int, int]:
    """v2.1 Phase 1: {quarter-end day: announcement day} for every quarter end on the timeline plus the four pre-history
    quarters, lags U(25, 35) drawn from the `announce` stream (shared by the V jump of jump_placement 'V_announce'/'both'
    and the EPS field, so that the field carries the jump)."""
    L = len(day)
    q_ends = [int(day[i]) for i in range(L) if day[i] % QUARTER_DAYS == 0]
    first = int(day[0]); pre = []
    d = (first // QUARTER_DAYS) * QUARTER_DAYS
    while len(pre) < 4:
        d -= QUARTER_DAYS
        pre.append(d)
    out = {}
    for dq in sorted(pre) + q_ends:
        out[dq] = dq + int(rng.integers(ANN_LAG[0], ANN_LAG[1] + 1))
    return out


def earnings_block(day: np.ndarray, V: np.ndarray, P: np.ndarray, rng_mult: np.random.Generator,
                   rng_eps: np.random.Generator, rng_div: np.random.Generator,
                   ann: Optional[Dict[int, int]] = None, ann_jumps: Optional[Dict[int, float]] = None) -> Dict[str, np.ndarray]:
    """`ann` = announcement_schedule() (v2.1 Phase 1; if None the lags are drawn here from rng_eps as v2 did);
    `ann_jumps` = {announcement day: log V jump J} -- the announced quarterly EPS of that quarter is computed from
    V(quarter end) e^J, so the EPS field carries the announcement jump (variants 'V_announce' and 'both')."""
    L = len(day)
    k = float(rng_mult.uniform(*K_RANGE))
    # quarter ends at days congruent to 0 mod 63 (day 0 is a quarter end), on the full timeline
    q_end_idx = [i for i in range(L) if day[i] % QUARTER_DAYS == 0]
    # pre-history quarters (before the simulated range) use the first simulated V (burn-in only)
    first = day[0]
    pre = []
    d = (first // QUARTER_DAYS) * QUARTER_DAYS
    while len(pre) < 4:
        d -= QUARTER_DAYS
        pre.append(d)
    ann_jumps = ann_jumps or {}
    def _ann_day(dq: int) -> int:
        if ann is not None:
            return int(ann[dq])
        return dq + int(rng_eps.integers(ANN_LAG[0], ANN_LAG[1] + 1))
    eps_ann = []   # (announce_day, eps_q, dps_q)
    dps_prev = PAYOUT * (V[0] / (4.0 * k))   # initial quarterly DPS = payout x quarterly EPS
    for dq in sorted(pre):
        a = _ann_day(dq)
        eps_q = V[0] * math.exp(ann_jumps.get(a, 0.0)) / (4.0 * k) * math.exp(rng_eps.normal(0.0, EPS_NOISE_SD))
        dps_q = DPS_STICKY * dps_prev + (1 - DPS_STICKY) * PAYOUT * eps_q
        dps_prev = dps_q
        eps_ann.append((a, eps_q, dps_q))
    for i in q_end_idx:
        a = _ann_day(int(day[i]))
        eps_q = V[i] * math.exp(ann_jumps.get(a, 0.0)) / (4.0 * k) * math.exp(rng_eps.normal(0.0, EPS_NOISE_SD))   # quarterly EPS: annual V/k over 4 quarters
        dps_q = DPS_STICKY * dps_prev + (1 - DPS_STICKY) * PAYOUT * eps_q
        dps_prev = dps_q
        eps_ann.append((a, eps_q, dps_q))
    eps_ann.sort()
    trailing = np.full(L, np.nan); dps = np.full(L, np.nan); last_ann_day = np.full(L, np.nan)
    last_eps = np.full(L, np.nan)
    for i in range(L):
        known = [e for e in eps_ann if e[0] <= day[i]]
        if len(known) >= 4:
            trailing[i] = sum(e[1] for e in known[-4:])
            dps[i] = known[-1][2]; last_ann_day[i] = known[-1][0]; last_eps[i] = known[-1][1]
    # note: quarterly EPS here is the quarter's value; trailing is the 4-quarter sum
    pe = np.where(trailing > 0, P / trailing, PE_CAP)
    pe = np.minimum(pe, PE_CAP)
    dy = np.where(P > 0, 4.0 * dps / P * 100.0, np.nan)
    return {"hidden_multiple": np.full(L, k), "trailing_eps": trailing, "last_quarter_eps": last_eps,
            "reported_PE": pe, "dps_quarterly": dps, "dividend_yield": dy,
            "days_since_eps_announcement": day - last_ann_day}


def analyst_block(day: np.ndarray, V: np.ndarray, rng: np.random.Generator) -> Dict[str, np.ndarray]:
    L = len(day)
    u = np.zeros(L)
    sd_inn = ANALYST_SD * math.sqrt(1 - ANALYST_RHO ** 2)
    u_state = rng.normal(0.0, ANALYST_SD)
    for i in range(L):
        if i % ANALYST_UPDATE_DAYS == 0:
            # AR(1) per update with innovation sd ANALYST_SD sqrt(1 - rho^2): stationary sd = ANALYST_SD (Phase 0 fix, item 68)
            u_state = ANALYST_RHO * u_state + rng.normal(0.0, sd_inn)
        u[i] = u_state
    return {"analyst_fair_value": V * np.exp(u), "analyst_error_u": u}


def volume_block(day: np.ndarray, r: np.ndarray, x: np.ndarray, rng: np.random.Generator, lag: int = 0) -> Dict[str, np.ndarray]:
    L = len(day)
    lag = int(abs(lag))
    logv = np.zeros(L)
    prev = VOL_MU
    for i in range(L):
        xl = x[max(i - lag, 0)]
        cur = (VOL_MU + VOL_RHO * (prev - VOL_MU) + VOL_B_ABS_R * (abs(r[i]) / SIGMA_R_REF - 1.0)
               + VOL_B_ABS_X * abs(xl) + VOL_EPS * rng.normal())
        logv[i] = cur; prev = cur
    vol = np.exp(logv)
    vsma = pd.Series(vol).rolling(20, min_periods=1).mean().values
    return {"volume": vol, "volume_SMA20": vsma, "volume_ratio": vol / vsma}


def iv_block(fvar21: np.ndarray, w: np.ndarray, sigma2_state: np.ndarray, sigma_V: float) -> Dict[str, np.ndarray]:
    """The v2 construction (superseded by iv_block_v21 in v2.1 Phase 3; kept for the record and the frozen
    sensitivities). Weakness 46/25: the whole-path quantile is a look-ahead and the phase multiplier enters
    fvar21 deterministically."""
    # stress premium when the GARCH conditional variance is in its top decile of the path
    thr = np.quantile(sigma2_state, 0.9)
    prem = np.where(sigma2_state >= thr, IV_PREMIUM_STRESS, IV_PREMIUM)
    iv = np.sqrt(252.0 * (sigma_V ** 2 + (w ** 2) * fvar21)) * (1.0 + prem) * 100.0
    return {"implied_volatility": np.maximum(iv, IV_FLOOR)}


def iv_filter_forecast(ret: np.ndarray, alpha: float, gamma: float, beta: float, omega: float,
                       horizon: int = 21) -> np.ndarray:
    """E3.5 (v2.1 Phase 3): past-only GJR-GARCH filter on the OBSERVED returns; fc[t] = mean conditional
    variance over days t+1..t+horizon from the state after observing day t. No phase input, no generator state,
    so IV built on it cannot carry the hidden regime except through the returns it has already produced."""
    pers = alpha + 0.5 * gamma + beta
    uncond = omega / (1.0 - pers)
    n = len(ret)
    fc = np.empty(n)
    geo = (1.0 - pers ** horizon) / ((1.0 - pers) * horizon)   # closed-form mean of the forecast path
    h = uncond
    for t in range(n):
        e = ret[t]
        lev = gamma * e * e if e < 0.0 else 0.0
        h = omega + alpha * e * e + lev + beta * h             # variance of day t+1
        fc[t] = uncond + (h - uncond) * geo
    return fc


def iv_block_v21(ret: np.ndarray, rng: np.random.Generator, ivp: Dict) -> Dict[str, np.ndarray]:
    """E3.5's construction: IV_t = sqrt(252 fc_t) * (1 + pi_t) * exp(eps_t) * 100, with fc the past-only filter
    forecast, log(1 + pi_t) a FIT polynomial in log(fc_t / uncond) (the five CBOE single-stock VIX histories),
    and eps an AR(1) noise drawn day-indexed from the 'iv' stream (altering the path after day t cannot change
    IV on days <= t: test_iv_no_lookahead). The v2 stress trigger, whole-path quantile, sigma_V add-on, w^2
    factor and the CAL floor are removed (PREREG_PHASE_3.md section 7)."""
    f = ivp["filter"]
    fc = iv_filter_forecast(np.asarray(ret, float), float(f["alpha"]), float(f["gamma"]), float(f["beta"]),
                            float(f["omega"]), int(ivp.get("horizon", 21)))
    pers = float(f["alpha"]) + 0.5 * float(f["gamma"]) + float(f["beta"])
    uncond = float(f["omega"]) / (1.0 - pers)
    logl = np.log(fc / uncond)
    coef = list(ivp["premium"]["coef"])
    log1p_pi = np.zeros(len(fc))
    for k, c in enumerate(coef):
        log1p_pi += float(c) * logl ** k
    e = ivp["eps"]
    rho, sd_inn = float(e["rho"]), float(e["sd_innov"])
    z = rng.standard_normal(len(fc))
    eps = np.empty(len(fc))
    eps[0] = z[0] * (sd_inn / math.sqrt(1.0 - rho * rho) if abs(rho) < 1 else sd_inn)
    for t in range(1, len(fc)):
        eps[t] = rho * eps[t - 1] + sd_inn * z[t]
    iv = np.sqrt(252.0 * fc) * np.exp(log1p_pi + eps) * 100.0
    return {"implied_volatility": iv, "iv_fc21": fc, "iv_eps": eps}


def technicals_block(P: np.ndarray) -> Dict[str, np.ndarray]:
    s = pd.Series(P)
    sma20 = s.rolling(20, min_periods=1).mean(); sma50 = s.rolling(50, min_periods=1).mean()
    delta = s.diff()
    gain = delta.clip(lower=0); loss = (-delta).clip(lower=0)
    # Wilder smoothing (EMA with alpha = 1/14)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = (100 - 100 / (1 + rs)).fillna(50.0)
    ema12 = s.ewm(span=12, adjust=False).mean(); ema26 = s.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26; signal = macd.ewm(span=9, adjust=False).mean()
    ts = ((sma20 - sma50) / sma50 * 100).fillna(0.0)
    regime = np.where(ts > 2.0, 1, np.where(ts < -2.0, -1, 0))
    return {"SMA20": sma20.values, "SMA50": sma50.values, "RSI14": rsi.values, "MACD": macd.values,
            "MACD_signal": signal.values, "trend_strength": ts.values, "trend_regime": regime}
