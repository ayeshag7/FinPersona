"""
Observables v2 (plan Section 3 rows: Sentiment, Earnings/PE, Dividend, Implied
volatility, Volume, Technical indicators).  Every field is a function of the
price path, the hidden value path, the GARCH state or its own noise -- NEVER of
the phase label -- so that the composite phase clock (L2b) is passable.

v2 constants (DESIGN, in force until v2.1 Phase 5 is applied -- see envs/v2/observables_params.py):
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

v2.1 Phase 5 (PREREG_PHASE_5.md): every block takes an optional `params` section dict from
envs/v2/observables_params.resolve().  With `params is None`, or with the section's design set to "v2", the block
runs the v2 code above VERBATIM (same RNG call sequence), which tests/test_v2_1_phase_5.py proves against the
committed HEAD on random inputs.  The v2.1 designs:
  multiple   A: k per seed by inverse CDF from a FIT quantile grid of the EDGAR trailing P/E cross-section (E5.1);
             B: k_t = exp(mu_k + z_t), mu_k from the between-stock grid, z_t a daily log-AR(1) with FIT persistence and
             the within-stock dispersion net of x and of the EPS noise.
  eps        FIT seasonal-RW noise s_EPS; a two-state loss chain with a FIT loss-size grid; P/E is NaN (rendered "n/m")
             when the trailing EPS is <= 0 and capped at the FIT P99; announcement lags by inverse CDF from the FIT
             8-K grid (E5.2).
  dividend   Lintner at quarterly frequency with FIT speed and target payout; a per-seed payer draw (E5.3).
  analyst    A: F = V e^u at a LIT sd; C: F = SMA250(P) e^u -- a trend-follower's estimate, level-free and x-free by
             construction (E5.4).
  sentiment  A: returns-only AR(1) with FIT loadings on the standardised return; B: A + a FIT valuation link on x;
             C: a weekly survey-style AR(1) with AAII's persistence and loading (E5.5).
  volume     A: log-volume AR(1) + FIT |r|/sigma elasticity + FIT noise; B: A + a FIT run-up loading on the trailing
             252-day return (E5.6).  The v2 |x| loading is dominated and retrievable only as design "v2".
"""
from __future__ import annotations

import math
from collections import deque
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
TRAIL_WINDOW = 252        # v2.1 Phase 5: the past-only window of the volume and sentiment standardisations
ANALYST_PROXY_WINDOW = 250


def _v2(params: Optional[Dict], section: str) -> bool:
    """True when the block must run its v2 code path."""
    return params is None or str(params.get(section, {}).get("design", "v2")) == "v2"


def grid_draw(rng: np.random.Generator, grid) -> float:
    """Inverse-CDF draw from an empirical quantile grid (the Phase-4 schedule sampler's form): one uniform."""
    g = np.asarray(grid, float)
    u = float(rng.random())
    return float(np.interp(u * (len(g) - 1), np.arange(len(g)), g))


# --------------------------------------------------------------------------
# sentiment (stepped inside the generator loop; feeds back through b_pred)
# --------------------------------------------------------------------------
class SentimentState:
    def __init__(self, rng: np.random.Generator, lag: int = 0, params: Optional[Dict] = None):
        self.rng = rng
        self.lag = int(abs(lag))
        self.s = 0.0
        self.m_prev = 0.0
        self.raw = 0.0
        self.p = None if _v2(params, "sentiment") else dict(params["sentiment"])
        if self.p is not None:
            self.design = str(self.p["design"])
            self.scale = float(self.p["s_raw"])            # DESIGN rendering constant: sd(tanh(scale * raw)) = SENT_SD_REF
            self._r = deque(maxlen=TRAIL_WINDOW)           # past-only trailing sd of the daily return
            self._ss = 0.0
            self.z_prev = 0.0
            self.week = deque(maxlen=5)                     # design C: the 5-day return window
            self.n_steps = 0
            self._rw = deque(maxlen=52)                     # design C: trailing sd of the weekly return
            self.spread = 0.0
            self.zw_prev = 0.0

    def _sigma(self) -> float:
        n = len(self._r)
        if n < 20:
            return SIGMA_R_REF
        return math.sqrt(max(self._ss / n, 1e-12))

    def step(self, x_lagged: float, ret20: float, r: float) -> float:
        if self.p is None:
            m = 0.6 * math.tanh(2.0 * x_lagged) + 0.3 * math.tanh(ret20 / 0.15)
            raw = m + SENT_RHO * (self.raw - self.m_prev) + SENT_B_RET * (r / SIGMA_R_REF) + SENT_EPS * self.rng.normal()
            self.raw = raw
            self.m_prev = m
            self.s = math.tanh(raw)
            return self.s
        # ---- v2.1 designs: the standardisation uses the PAST returns only (the sd before today's return enters)
        sigma = self._sigma()
        z = r / sigma
        if len(self._r) == self._r.maxlen:
            old = self._r[0]
            self._ss -= old * old
        self._r.append(r)
        self._ss += r * r
        p = self.p
        if self.design in ("A", "B"):
            raw = (float(p["rho"]) * self.raw + float(p["b0"]) * z + float(p["b1"]) * self.z_prev
                   + float(p["sd_e"]) * self.rng.normal())
            if self.design == "B":
                raw += float(p["c_val"]) * x_lagged      # the valuation link, in raw-sd units per unit x (DESIGN transfer)
            self.raw = raw
            self.z_prev = z
            self.s = math.tanh(self.scale * raw)
            return self.s
        if self.design == "C":
            self.week.append(r)
            self.n_steps += 1
            if self.n_steps % int(p.get("update_days", 5)) == 0 and len(self.week) == 5:
                rw = float(sum(self.week))
                sw = (math.sqrt(sum(v * v for v in self._rw) / len(self._rw)) if len(self._rw) >= 8
                      else sigma * math.sqrt(5.0))
                self._rw.append(rw)
                zw = rw / max(sw, 1e-9)
                self.spread = (float(p["rho_w"]) * self.spread + float(p["b0_w"]) * zw + float(p["b1_w"]) * self.zw_prev
                               + float(p["sd_e_w"]) * self.rng.normal())
                self.zw_prev = zw
                self.s = math.tanh(self.scale * self.spread)
            return self.s
        raise ValueError(f"unknown sentiment design {self.design!r}")


# --------------------------------------------------------------------------
# post-hoc observables from the generated arrays (one asset)
# --------------------------------------------------------------------------
def announcement_schedule(day: np.ndarray, rng: np.random.Generator, q_phase: int = 0,
                          params: Optional[Dict] = None) -> Dict[int, int]:
    """v2.1 Phase 1: {quarter-end day: announcement day} for every quarter end on the timeline plus the four pre-history
    quarters, lags U(25, 35) drawn from the `announce` stream (shared by the V jump of jump_placement 'V_announce'/'both'
    and the EPS field, so that the field carries the jump).  v2.1 Phase 5 (E5.2): with params['eps']['design'] != 'v2'
    the lag is drawn by inverse CDF from the FIT 8-K announcement-lag grid (trading days)."""
    L = len(day)
    # v2.1 Phase 4 (E4.7d): `q_phase` shifts the quarter grid per seed.  With q_phase = 0 the grid is the v2
    # one (quarter ends at day % 63 == 0, identical for every seed, so `days_since_eps_announcement` is a
    # deterministic function of the day index and therefore a clock).  REG-9 asks for it to be randomised.
    q_ends = [int(day[i]) for i in range(L) if (day[i] - q_phase) % QUARTER_DAYS == 0]
    first = int(day[0]); pre = []
    d = ((first - q_phase) // QUARTER_DAYS) * QUARTER_DAYS + q_phase
    while len(pre) < 4:
        d -= QUARTER_DAYS
        pre.append(d)
    out = {}
    grid = None if _v2(params, "eps") else params["eps"].get("lag_grid_td")
    for dq in sorted(pre) + q_ends:
        if grid is None:
            out[dq] = dq + int(rng.integers(ANN_LAG[0], ANN_LAG[1] + 1))
        else:
            out[dq] = dq + int(round(grid_draw(rng, grid)))
    return out


def _multiple_path(L: int, rng_mult: np.random.Generator, params: Optional[Dict]) -> np.ndarray:
    """The hidden multiple over the timeline: a constant (v2, design A) or a daily log-AR(1) (design B)."""
    if _v2(params, "multiple"):
        return np.full(L, float(rng_mult.uniform(*K_RANGE)))
    m = params["multiple"]
    width = str(m.get("width", "P10-P90"))
    if m["design"] == "A":
        return np.full(L, grid_draw(rng_mult, m["grid_A"][width]))
    if m["design"] == "B":
        mu = grid_draw(rng_mult, m["grid_B_log_between"][width])
        rho = float(m["rho_d"]); sd = float(m["s_w"])
        z = np.empty(L)
        e = rng_mult.normal(0.0, 1.0, L)
        z[0] = e[0] * sd
        inn = sd * math.sqrt(max(1.0 - rho * rho, 0.0))
        for t in range(1, L):
            z[t] = rho * z[t - 1] + inn * e[t]
        return np.exp(mu + z)
    raise ValueError(f"unknown multiple design {m['design']!r}")


def earnings_block(day: np.ndarray, V: np.ndarray, P: np.ndarray, rng_mult: np.random.Generator,
                   rng_eps: np.random.Generator, rng_div: np.random.Generator,
                   ann: Optional[Dict[int, int]] = None, ann_jumps: Optional[Dict[int, float]] = None,
                   q_phase: int = 0, params: Optional[Dict] = None) -> Dict[str, np.ndarray]:
    """`ann` = announcement_schedule() (v2.1 Phase 1; if None the lags are drawn here from rng_eps as v2 did);
    `ann_jumps` = {announcement day: log V jump J} -- the announced quarterly EPS of that quarter is computed from
    V(quarter end) e^J, so the EPS field carries the announcement jump (variants 'V_announce' and 'both').
    v2.1 Phase 5: `params` switches the multiple (E5.1), the EPS/loss process and the "n/m" rendering (E5.2) and the
    dividend process (E5.3); each is v2 when its section's design is "v2"."""
    L = len(day)
    v2_mult, v2_eps, v2_div = _v2(params, "multiple"), _v2(params, "eps"), _v2(params, "dividend")
    if v2_mult and v2_eps and v2_div:
        return _earnings_block_v2(day, V, P, rng_mult, rng_eps, rng_div, ann, ann_jumps, q_phase)
    k_path = _multiple_path(L, rng_mult, params)
    ep = None if v2_eps else params["eps"]
    dp = None if v2_div else params["dividend"]
    q_end_idx = [i for i in range(L) if (day[i] - q_phase) % QUARTER_DAYS == 0]
    first = day[0]
    pre = []
    d = ((first - q_phase) // QUARTER_DAYS) * QUARTER_DAYS + q_phase
    while len(pre) < 4:
        d -= QUARTER_DAYS
        pre.append(d)
    ann_jumps = ann_jumps or {}

    def _ann_day(dq: int) -> int:
        if ann is not None:
            return int(ann[dq])
        if ep is None:
            return dq + int(rng_eps.integers(ANN_LAG[0], ANN_LAG[1] + 1))
        return dq + int(round(grid_draw(rng_eps, ep["lag_grid_td"])))

    # the loss chain (E5.2): a two-state Markov chain independent of x and of the phase label (DESIGN, stated)
    loss = False
    if ep is not None:
        loss = bool(rng_eps.random() < float(ep["p_loss"]))

    def _eps_q(v_i: float, k_i: float, a: int) -> float:
        nonlocal loss
        base = v_i * math.exp(ann_jumps.get(a, 0.0)) / (4.0 * k_i)
        if ep is None:
            return base * math.exp(rng_eps.normal(0.0, EPS_NOISE_SD))
        p_next = float(ep["p_loss_given_loss"]) if loss else float(ep["p_loss_given_profit"])
        loss = bool(rng_eps.random() < p_next)
        if loss:
            return -abs(base) * grid_draw(rng_eps, ep["loss_size_grid"])
        return base * math.exp(rng_eps.normal(0.0, float(ep["s_eps"])))

    payer = True
    if dp is not None:
        payer = bool(rng_div.random() < float(dp["payer_share"]))
        c, tau = float(dp["c_speed"]), float(dp["tau"])
    else:
        c, tau = 1.0 - DPS_STICKY, PAYOUT
    eps_ann = []   # (announce_day, eps_q, dps_q)
    dps_prev = tau * max(V[0] / (4.0 * k_path[0]), 0.0) if payer else 0.0

    def _dps(eps_q: float, prev: float) -> float:
        if not payer:
            return 0.0
        if dp is None:
            return DPS_STICKY * prev + (1 - DPS_STICKY) * PAYOUT * eps_q
        return (1.0 - c) * prev + c * tau * max(eps_q, 0.0)

    for dq in sorted(pre):
        a = _ann_day(dq)
        eps_q = _eps_q(V[0], k_path[0], a)
        dps_q = _dps(eps_q, dps_prev)
        dps_prev = dps_q
        eps_ann.append((a, eps_q, dps_q))
    for i in q_end_idx:
        a = _ann_day(int(day[i]))
        eps_q = _eps_q(V[i], k_path[i], a)
        dps_q = _dps(eps_q, dps_prev)
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
    cap = float(ep["pe_cap"]) if ep is not None else PE_CAP
    with np.errstate(divide="ignore", invalid="ignore"):
        pe = np.where(trailing > 0, P / trailing, np.nan)          # trailing EPS <= 0 -> undefined, rendered "n/m"
    pe = np.minimum(pe, cap)
    if ep is None:
        pe = np.where(np.isnan(pe), PE_CAP, pe)                   # the v2 rendering of a non-positive trailing EPS
    pe_nm = np.isnan(pe).astype(float)
    dy = np.where(P > 0, 4.0 * dps / P * 100.0, np.nan)
    return {"hidden_multiple": k_path, "trailing_eps": trailing, "last_quarter_eps": last_eps,
            "reported_PE": pe, "pe_nm": pe_nm, "dps_quarterly": dps, "dividend_yield": dy,
            "days_since_eps_announcement": day - last_ann_day}


def _earnings_block_v2(day, V, P, rng_mult, rng_eps, rng_div, ann, ann_jumps, q_phase):
    """The committed v2 construction, verbatim (v2.1 Phase 4 state)."""
    L = len(day)
    k = float(rng_mult.uniform(*K_RANGE))
    # quarter ends at days congruent to 0 mod 63 (day 0 is a quarter end), on the full timeline
    q_end_idx = [i for i in range(L) if (day[i] - q_phase) % QUARTER_DAYS == 0]
    # pre-history quarters (before the simulated range) use the first simulated V (burn-in only)
    first = day[0]
    pre = []
    d = ((first - q_phase) // QUARTER_DAYS) * QUARTER_DAYS + q_phase
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
            "reported_PE": pe, "pe_nm": np.zeros(L), "dps_quarterly": dps, "dividend_yield": dy,
            "days_since_eps_announcement": day - last_ann_day}


def analyst_block(day: np.ndarray, V: np.ndarray, rng: np.random.Generator, params: Optional[Dict] = None,
                  P: Optional[np.ndarray] = None) -> Dict[str, np.ndarray]:
    """v2: F_t = V_t e^{u_t}.  v2.1 Phase 5 (E5.4): design A keeps the form at a LIT sd; design C replaces V by the
    trailing 250-day mean of the observed price (a trend-follower's estimate, level-free and x-free by construction);
    design B is A's form kept in the frame and NOT rendered (`field` = hidden)."""
    L = len(day)
    if _v2(params, "analyst"):
        sd, rho, upd = ANALYST_SD, ANALYST_RHO, ANALYST_UPDATE_DAYS
        base = V
    else:
        a = params["analyst"]
        sd, rho, upd = float(a["sd"]), float(a["rho"]), int(a.get("update_days", ANALYST_UPDATE_DAYS))
        if a["design"] == "C":
            if P is None:
                raise ValueError("analyst design C needs the price path")
            base = pd.Series(P).rolling(ANALYST_PROXY_WINDOW, min_periods=1).mean().to_numpy()
        else:
            base = V
    u = np.zeros(L)
    sd_inn = sd * math.sqrt(1 - rho ** 2)
    u_state = rng.normal(0.0, sd)
    for i in range(L):
        if i % upd == 0:
            # AR(1) per update with innovation sd ANALYST_SD sqrt(1 - rho^2): stationary sd = ANALYST_SD (Phase 0 fix, item 68)
            u_state = rho * u_state + rng.normal(0.0, sd_inn)
        u[i] = u_state
    return {"analyst_fair_value": base * np.exp(u), "analyst_error_u": u}


def volume_block(day: np.ndarray, r: np.ndarray, x: np.ndarray, rng: np.random.Generator, lag: int = 0,
                 params: Optional[Dict] = None) -> Dict[str, np.ndarray]:
    L = len(day)
    lag = int(abs(lag))
    logv = np.zeros(L)
    prev = VOL_MU
    if _v2(params, "volume"):
        for i in range(L):
            xl = x[max(i - lag, 0)]
            cur = (VOL_MU + VOL_RHO * (prev - VOL_MU) + VOL_B_ABS_R * (abs(r[i]) / SIGMA_R_REF - 1.0)
                   + VOL_B_ABS_X * abs(xl) + VOL_EPS * rng.normal())
            logv[i] = cur; prev = cur
    else:
        vp = params["volume"]
        rho, beta, sd_e = float(vp["rho_v"]), float(vp["beta_absr"]), float(vp["sd_e"])
        beta_ru = float(vp.get("beta_ru", 0.0)) if vp["design"] == "B" else 0.0
        rs = pd.Series(r)
        # past-only standardisation: the sd and the mean |z| of the PREVIOUS days (the burn-in makes them warm)
        sigma = rs.shift(1).rolling(TRAIL_WINDOW, min_periods=20).std().to_numpy()
        sigma = np.where(np.isfinite(sigma) & (sigma > 0), sigma, SIGMA_R_REF)
        absz = np.abs(r) / sigma
        mz = pd.Series(absz).shift(1).rolling(TRAIL_WINDOW, min_periods=20).mean().to_numpy()
        a_t = np.where(np.isfinite(mz), absz - mz, 0.0)
        lp = np.cumsum(r)
        ret252 = lp - np.concatenate([np.full(min(TRAIL_WINDOW, L), np.nan), lp[:-TRAIL_WINDOW]])[:L] if L > TRAIL_WINDOW \
            else np.full(L, np.nan)
        ru = np.where(np.isfinite(ret252), np.maximum(ret252, 0.0), 0.0)
        lv = 0.0
        for i in range(L):
            lv = rho * lv + beta * a_t[i] + beta_ru * ru[i] + sd_e * rng.normal()
            logv[i] = VOL_MU + lv
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
