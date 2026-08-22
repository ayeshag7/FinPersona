"""
Core path generator v2: fundamental V, mispricing x, price P = V exp(x), phases,
GARCH state, event metadata, rejection sampling; N-asset capable.

    log V_t = log V_{t-1} + mu_V,t + sigma_V z_t,     z ~ t(5) (common factor across assets)
    x_{t+1} = x_t + FW(x_t, x_{t-1}) + d_t + w_t e_t,  e_t ~ GJR-GARCH(1,1)-t(5)
    log P_t = log V_t + x_t

A 260-day burn-in precedes day 1 (plan conventions) so the FW state, the GARCH
state and any trailing windows are warm at t = 1.  V is rescaled so V_1 = start
price.  All randomness comes from envs.v2.rng.Streams (named streams, attempt
index for rejection sampling); nothing touches numpy's global RNG.

Rejection criteria (plan 2.1 block 7; decision 7), evaluated on days 1..T:
    crash          : min_{panic} x <= -0.10 and realised MDD >= 20%
    bull_trap      : max x >= +0.30
    sustained_bull : x in [-0.10, +0.15] throughout and V_T / V_1 >= 1.2
    flat           : none
The attempt count and reasons are logged (rate target < 5% per scenario).
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

import numpy as np

from envs.v2.rng import Streams, standardised_t
from envs.v2.schedule import Schedule, draw_schedule
from envs.v2.garch import GJRParams, GJRGarch
from envs.v2.mispricing import FWParams, MispricingState, load_params
from envs.v2.events import make_driver, relabel_blowoff, MU_V_BASE, G_MAX
from envs.v2.observables import SentimentState, SENT_SD_REF

BURN_IN = 260
MAX_ATTEMPTS = 50

# hazard top calibration (tools/calibrate_hazard.py; ~50% topped in T=200, peak P/V 1.6-2.5).
# Defaults are overridden by envs/v2/params/hazard.json when the calibration has been run.
HAZARD_H0 = 0.0015
HAZARD_B = 6.0
try:
    import json as _json
    from envs.v2.mispricing import PARAM_DIR as _PD
    with open(os.path.join(_PD, "hazard.json"), encoding="utf-8") as _fh:
        _hz = _json.load(_fh)
    HAZARD_H0, HAZARD_B = float(_hz["h0"]), float(_hz["b"])
    _G_MAX_CAL = float(_hz.get("g_max", 0.02))
except Exception:  # no calibration file yet
    _G_MAX_CAL = 0.02


@dataclass
class GenConfig:
    scenario: str = "flat"
    T: int = 200
    seed: int = 42
    ordering: str = "setup_first"          # setup_first | event_first | phase_free
    delta: float = 0.70                    # crash panic discount {0.55, 0.70, 0.85}
    n_assets: int = 1
    start_price: float = 100.0
    mu_V: float = MU_V_BASE
    sigma_V: float = 0.006
    df_V: float = 5.0
    rho_common: float = 0.3                # common-factor share of V shocks (N > 1)
    engine: str = "fw_single"              # fw_single | fw_index | pruna | ar1
    garch: Dict = field(default_factory=dict)   # overrides for GJRParams
    jumps: bool = True                      # rare jumps on by default (E1 calibration; plan block 4 'optional')
    jump_rate: float = 0.010               # plan 0.004 'optional'; E1 calibration 0.010 (checklist 2, 8)
    jump_mean: float = -0.04
    jump_sd: float = 0.03
    hazard_h0: float = HAZARD_H0
    hazard_b: float = HAZARD_B
    g_max: float = _G_MAX_CAL               # cap on the compounding mania drift (calibrated with the hazard)
    lam_panic: float = 0.10                # error-correction gain of the panic target path
    burn_in: int = BURN_IN
    reject: bool = True
    max_attempts: int = MAX_ATTEMPTS
    # per-asset volatility/omega scaling (index 0 = the scenario asset; e.g. a
    # low-volatility 'defensive' risky asset gets 0.5)
    asset_vol_scale: List[float] = field(default_factory=list)
    # sentiment predictive component (decision 10): next-day return per +1 sd of sentiment, and the
    # amount reversed over days 2-5 (Tetlock 2007)
    b_pred: float = 0.0008
    b_rev: float = 0.0006

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d


@dataclass
class PathResult:
    cfg: GenConfig
    schedule: Schedule
    params: FWParams
    garch_params: GJRParams
    day: np.ndarray            # (L,) day index, 1..T for the benchmark part, <=0 burn-in
    V: np.ndarray              # (N, L)
    x: np.ndarray              # (N, L)
    P: np.ndarray              # (N, L)
    sigma: np.ndarray          # (N, L) GARCH conditional sd of e
    e: np.ndarray              # (N, L) realised innovation
    n_f: np.ndarray            # (N, L) fundamentalist share
    w: np.ndarray              # (N, L) FW innovation weight
    fvar21: np.ndarray         # (N, L) 21-day-ahead mean GARCH variance forecast (for IV)
    sent: np.ndarray           # (N, L) news sentiment (tanh-squashed)
    phase: np.ndarray          # (L,) phase label per day (asset-shared schedule)
    event_meta: Dict
    attempts: int
    rejections: List[str]

    @property
    def L(self) -> int:
        return len(self.day)

    def bench(self, arr: np.ndarray) -> np.ndarray:
        """Slice an (N, L) or (L,) array to benchmark days 1..T."""
        m = self.day >= 1
        return arr[..., m]


def _simulate_once(cfg: GenConfig, attempt: int) -> PathResult:
    B, T = cfg.burn_in, cfg.T
    L = B + T
    N = max(1, cfg.n_assets)
    st = Streams(cfg.seed, attempt)
    sched = draw_schedule(cfg.scenario, T, st.get("schedule"), cfg.ordering, delta=cfg.delta)
    params = load_params(cfg.engine)
    gp = GJRParams(**cfg.garch) if cfg.garch else GJRParams()
    day = np.arange(L) - B + 1
    vol_scale = list(cfg.asset_vol_scale) + [1.0] * (N - len(cfg.asset_vol_scale))

    # common fundamental factor
    f_common = standardised_t(st.get("fundamental_common", -1), cfg.df_V, L)

    V = np.zeros((N, L)); x = np.zeros((N, L)); sig = np.zeros((N, L)); e_arr = np.zeros((N, L))
    nf = np.zeros((N, L)); phases = np.empty(L, dtype=object)
    w_arr = np.ones((N, L)); fvar = np.zeros((N, L)); sent = np.zeros((N, L))
    meta_assets = []
    for a in range(N):
        driver = make_driver(sched, cfg.hazard_h0, cfg.hazard_b, cfg.g_max, cfg.lam_panic)
        z_i = standardised_t(st.get("fundamental", a), cfg.df_V, L)
        z = (math.sqrt(cfg.rho_common) * f_common + math.sqrt(1 - cfg.rho_common) * z_i) if N > 1 else z_i
        eta = standardised_t(st.get("garch", a), gp.df, L)
        u_haz = st.get("hazard", a).random(L)
        jumps = None
        if cfg.jumps:
            rj = st.get("jump", a)
            jumps = np.where(rj.random(L) < cfg.jump_rate, rj.normal(cfg.jump_mean, cfg.jump_sd, L), 0.0)
        garch = GJRGarch(GJRParams(**{**asdict(gp), "sbar": gp.sbar * vol_scale[a]}))
        ms = MispricingState(params, cfg.engine, x0=0.0)
        sentiment = SentimentState(st.get("sentiment", a), lag=sched.jitter.get("sentiment", 0))
        pending = np.zeros(L + 8)          # sentiment -> future-return drifts (b_pred, reversal)
        logP_hist = []
        logV = math.log(cfg.start_price)
        sigV = cfg.sigma_V * vol_scale[a]
        for i in range(L):
            d_i = int(day[i])
            drift, mu_v, ph = driver.begin(d_i, ms.x)
            if a == 0:
                phases[i] = ph
            # record the state AT day i
            V[a, i] = math.exp(logV); x[a, i] = ms.x; nf[a, i] = ms.n_f; w_arr[a, i] = ms.weight()
            logP = logV + ms.x
            logP_hist.append(logP)
            r_i = logP - logP_hist[-2] if i > 0 else 0.0
            ret20 = logP - logP_hist[max(0, i - 20)]
            x_lag = x[a, max(0, i - sentiment.lag)]
            s_i = sentiment.step(x_lag, ret20, r_i)
            sent[a, i] = s_i
            if cfg.b_pred:
                s_std = s_i / SENT_SD_REF
                pending[i] += cfg.b_pred * s_std                 # next-day return
                pending[i + 1:i + 5] -= (cfg.b_rev / 4.0) * s_std  # reversal over days 2-5
            # innovations for the transition i -> i+1
            sigma_i, e_i = garch.step(eta[i], ph)
            sig[a, i] = sigma_i; e_arr[a, i] = e_i
            fvar[a, i] = garch.forecast_var(21, ph)
            if i + 1 < L:
                extra = jumps[i] if jumps is not None else 0.0
                x_new = ms.step(e_i + extra, drift + pending[i])
                logV += mu_v + sigV * z[i]
                driver.end(int(day[i + 1]), x_new, u_haz[i])
        # rescale V so that V_1 = start price (GBM is scale-free)
        V[a] *= cfg.start_price / V[a, B]
        meta_assets.append(driver.meta())
    phases = relabel_blowoff(phases, day, sched, meta_assets[0].get("top_day"))
    P = V * np.exp(x)
    meta = {"assets": meta_assets, **meta_assets[0]}
    return PathResult(cfg, sched, params, gp, day, V, x, P, sig, e_arr, nf, w_arr, fvar, sent, phases, meta, attempt + 1, [])


def check_validity(res: PathResult) -> Optional[str]:
    """Return None if the path satisfies its scenario criterion, else the reason."""
    cfg = res.cfg
    m = res.day >= 1
    x = res.x[0, m]; P = res.P[0, m]; V = res.V[0, m]; ph = res.phase[m]
    if cfg.scenario == "crash":
        panic = ph == "panic"
        if panic.sum() == 0 or x[panic].min() > -0.10:
            return "crash: min x over panic > -0.10"
        mdd = (P / np.maximum.accumulate(P) - 1).min()
        if mdd > -0.20:
            return f"crash: MDD {mdd:.2%} > -20%"
    elif cfg.scenario == "bull_trap":
        if x.max() < 0.30:
            return f"bull_trap: max x {x.max():.2f} < 0.30"
    elif cfg.scenario == "sustained_bull":
        if x.min() < -0.10 or x.max() > 0.15:
            return f"sustained_bull: x range [{x.min():.2f}, {x.max():.2f}] outside [-0.10, 0.15]"
        if V[-1] / V[0] < 1.2:
            return f"sustained_bull: V_T/V_1 {V[-1]/V[0]:.2f} < 1.2"
    return None


def generate(cfg: GenConfig) -> PathResult:
    rejections: List[str] = []
    for k in range(cfg.max_attempts):
        res = _simulate_once(cfg, k)
        reason = check_validity(res) if cfg.reject else None
        if reason is None:
            res.rejections = rejections
            res.attempts = k + 1
            return res
        rejections.append(reason)
    res.rejections = rejections
    res.attempts = cfg.max_attempts
    res.event_meta["accepted"] = False
    return res
