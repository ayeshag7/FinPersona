"""
Core path generator v2: fundamental V, mispricing x, price P = V exp(x), phases,
GARCH state, event metadata, rejection sampling; N-asset capable.

    log V_t = log V_{t-1} + mu_V,t + sigma_V z_t,     z_t standardised t(5) for N = 1; for N > 1 assets
                                                      z = sqrt(rho) f + sqrt(1 - rho) z_i with f (common) and z_i
                                                      independent standardised t(5) -- the mixture is NOT t(5)
                                                      (weakness item 73; documented in v2.1 Phase 0, Phase 1/4 decide)
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
from envs.v2.mispricing import FWParams, MispricingState, load_params, ENGINE_DEFAULT
from envs.v2.events import make_driver, relabel_blowoff, MU_V_BASE, G_MAX
from envs.v2.observables import SentimentState, SENT_SD_REF, announcement_schedule
from envs.v2 import value_params as VP

BURN_IN = 260          # v2 burn-in; v2.1 Phase 1: the burn-in in force is VP.burn_in_for(engine) (E1.5), see GenConfig.__post_init__
MAX_ATTEMPTS = 50
START_PRICE_MODES = ("fixed", "randomise", "normalise", "both")
JUMP_PLACEMENTS = ("x_negmean", "x_zero", "V_announce", "both")

# Bubble hazard h_t = h0 exp(b x_t) and the mania drift cap: CAL (tools/calibrate_hazard.py, 60 seeds, grid search
# to the plan's ~50 % topped / peak P/V 1.6-2.5 targets; weakness items 17, 41). The module constants ARE the
# calibrated values and envs/v2/params/hazard.json must agree with them: the loader raises at import if the file
# is missing or differs (v2.1 Phase 0, item 69: before, HAZARD_H0 = 0.0015 and G_MAX = 0.02 were silently
# overridden by the file, and a missing file would have run different parameters without warning).
HAZARD_H0 = 0.0003
HAZARD_B = 6.0
G_MAX_CAL = 0.012


def load_hazard_params(path: Optional[str] = None) -> Dict[str, float]:
    """Read hazard.json and check it against the module constants. Raises RuntimeError if the file is missing or
    disagrees (no silent override)."""
    import json as _json
    from envs.v2.mispricing import PARAM_DIR as _PD
    path = path or os.path.join(_PD, "hazard.json")
    if not os.path.exists(path):
        raise RuntimeError(f"{path} is missing: the calibrated hazard file must be present (h0 {HAZARD_H0}, b {HAZARD_B}, "
                           f"g_max {G_MAX_CAL}); regenerate it with tools/calibrate_hazard.py and log the decision")
    with open(path, encoding="utf-8") as fh:
        hz = _json.load(fh)
    got = {"h0": float(hz["h0"]), "b": float(hz["b"]), "g_max": float(hz["g_max"])}
    want = {"h0": HAZARD_H0, "b": HAZARD_B, "g_max": G_MAX_CAL}
    if any(abs(got[k] - want[k]) > 1e-12 for k in want):
        raise RuntimeError(f"{path} disagrees with the module constants: file {got} vs code {want}; a change of the "
                           f"calibrated hazard is a logged decision that must update both")
    return got


_HAZARD = load_hazard_params()


@dataclass
class GenConfig:
    scenario: str = "flat"
    T: int = 200
    seed: int = 42
    ordering: str = "setup_first"          # setup_first | event_first | phase_free
    delta: float = 0.70                    # crash panic discount {0.55, 0.70, 0.85}
    n_assets: int = 1
    start_price: float = 100.0             # the normalisation constant (P_1 under B/C, V_1 under 'fixed')
    # v2.1 Phase 1 (PREREG_PHASE_1.md section 7; D13): start_price_mode 'fixed' (v2: V_1 = P_1 = start_price), 'randomise'
    # (A: V_1 ~ LogU(range), P_1 = V_1 e^x_1), 'normalise' (B: P_1 = start_price, V_1 = start_price e^-x_1), 'both'
    # (C: B + a render scale k_render ~ LogU(range / start_price) applied to price-denominated fields at render time)
    start_price_mode: str = VP.START_PRICE_MODE
    start_price_range: tuple = VP.START_PRICE_RANGE   # FIT: P5-P95 of large-cap closes (E1.1)
    mu_V: float = VP.MU_V                  # FIT (Shiller price-only, 2000-2024; E1.2)
    sigma_V: float = VP.SIGMA_V            # value.json (E1.2 / D3)
    df_V: Optional[float] = VP.DF_V        # t(df) shocks of V; None = Gaussian (E1.3 grid / df_V decision)
    rho_common: float = 0.3                # common-factor share of V shocks (N > 1)
    engine: str = ENGINE_DEFAULT           # fw_fallback_hl150 (default) | fw_index | pruna | ar1 | fw_hl<d> | fw_single (accepted estimate only)
    garch: Dict = field(default_factory=dict)   # overrides for GJRParams
    jumps: bool = True                      # rare jumps on by default (E1 calibration; plan block 4 'optional')
    # v2.1 Phase 1 (E1.4, PREREG section 5.2): jump_placement 'x_negmean' (v2: N(jump_mean, jump_sd) in x at jump_rate),
    # 'x_zero' (B: mean-zero in x), 'V_announce' (A: with probability p_ann a N(0, jump_sd) jump in log V on each EPS
    # announcement day plus a residual Poisson component in log V at lam_res), 'both' (C: announcement jumps in V, the
    # residual component in x, mean zero). Total expected count = jump_rate under every placement (CAL; Phase 3 re-fits).
    jump_placement: str = VP.JUMP["placement"]
    jump_rate: float = VP.JUMP["jump_rate_x"]          # rate of the x-jump component ('x_negmean', 'x_zero'); CAL 0.010
    jump_mean: float = VP.JUMP["jump_mean_x"]          # 'x_negmean' only
    jump_sd: float = VP.JUMP["jump_sd"]                # CAL 0.03 (Phase 3 re-fits)
    p_ann: float = VP.JUMP["p_ann"]                    # FIT from the panel's window share of jump days (q)
    lam_res: float = VP.JUMP["lam_res"]                # (1 - q) x total rate
    hazard_h0: float = HAZARD_H0
    hazard_b: float = HAZARD_B
    g_max: float = G_MAX_CAL                # cap on the compounding mania drift (CAL, with the hazard)
    lam_panic: float = 0.10                # error-correction gain of the panic target path
    burn_in: Optional[int] = None          # None -> value.json's burn-in for the engine (E1.5); an int overrides
    burn_in_mode: Optional[str] = None     # None -> value.json's per-engine mode (E1.5): 'long' (option A) | 'stored' (option B: day-1 state drawn from a stored long-run sample)
    reject: bool = True
    max_attempts: int = MAX_ATTEMPTS
    # per-asset volatility/omega scaling (index 0 = the scenario asset; e.g. a
    # low-volatility 'defensive' risky asset gets 0.5)
    asset_vol_scale: List[float] = field(default_factory=list)
    # sentiment predictive component (decision 10): next-day return per +1 sd of sentiment, and the
    # amount reversed over days 2-5 (Tetlock 2007)
    b_pred: float = 0.0008
    b_rev: float = 0.0006
    # v2.1 Phase 3 (E3.5): None -> volatility.json's IV construction when present (v21 past-only filter),
    # else the v2 iv_block; "v2" forces the legacy construction (sensitivity)
    iv_mode: Optional[str] = None

    def __post_init__(self):
        if self.start_price_mode not in START_PRICE_MODES:
            raise ValueError(f"start_price_mode must be one of {START_PRICE_MODES}")
        if self.jump_placement not in JUMP_PLACEMENTS:
            raise ValueError(f"jump_placement must be one of {JUMP_PLACEMENTS}")
        if self.burn_in_mode is None:
            self.burn_in_mode = VP.burn_in_mode_for(self.engine)
        if self.burn_in is None:
            self.burn_in = int(VP.BURN_IN["stored_days"]) if self.burn_in_mode == "stored" else VP.burn_in_for(self.engine)
        self.start_price_range = tuple(float(v) for v in self.start_price_range)

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
    ann: List[Dict[int, int]] = field(default_factory=list)        # per asset: {quarter-end day: announcement day}
    ann_jumps: List[Dict[int, float]] = field(default_factory=list) # per asset: {announcement day: log V jump}
    k_render: float = 1.0                                           # mechanism C render scale (1.0 otherwise)

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

    def _shocks(rng, size):
        return rng.standard_normal(size) if cfg.df_V is None else standardised_t(rng, cfg.df_V, size)
    # common fundamental factor
    f_common = _shocks(st.get("fundamental_common", -1), L)

    V = np.zeros((N, L)); x = np.zeros((N, L)); sig = np.zeros((N, L)); e_arr = np.zeros((N, L))
    nf = np.zeros((N, L)); phases = np.empty(L, dtype=object)
    w_arr = np.ones((N, L)); fvar = np.zeros((N, L)); sent = np.zeros((N, L))
    meta_assets, ann_all, ann_jumps_all = [], [], []
    stored = _stored_state(cfg.engine) if cfg.burn_in_mode == "stored" else None
    for a in range(N):
        driver = make_driver(sched, cfg.hazard_h0, cfg.hazard_b, cfg.g_max, cfg.lam_panic, cfg.mu_V)
        z_i = _shocks(st.get("fundamental", a), L)
        z = (math.sqrt(cfg.rho_common) * f_common + math.sqrt(1 - cfg.rho_common) * z_i) if N > 1 else z_i
        eta = standardised_t(st.get("garch", a), gp.df, L)
        u_haz = st.get("hazard", a).random(L)
        u_reg = st.get("regime", a).random(L) if gp.scale_mode == "switching" else None   # E3.4 mechanism C
        ann = announcement_schedule(day, st.get("announce", a))      # {quarter end: announcement day}
        day_index = {int(d): i for i, d in enumerate(day)}
        jumps_x = None; jumps_V = np.zeros(L); ann_jumps: Dict[int, float] = {}
        if cfg.jumps:
            rj = st.get("jump", a)
            if cfg.jump_placement == "x_negmean":
                jumps_x = np.where(rj.random(L) < cfg.jump_rate, rj.normal(cfg.jump_mean, cfg.jump_sd, L), 0.0)
            elif cfg.jump_placement == "x_zero":
                jumps_x = np.where(rj.random(L) < cfg.jump_rate, rj.normal(0.0, cfg.jump_sd, L), 0.0)
            else:   # 'V_announce' / 'both': announcement jumps in log V (the EPS field carries them), residual in V or x
                for dq, ad in sorted(ann.items()):
                    if rj.random() < cfg.p_ann:
                        J = float(rj.normal(0.0, cfg.jump_sd))
                        ann_jumps[int(ad)] = J
                        i_ad = day_index.get(int(ad))
                        if i_ad is not None and i_ad >= 1:
                            jumps_V[i_ad - 1] += J          # applied in the transition into the announcement day
                resid = np.where(rj.random(L) < cfg.lam_res, rj.normal(0.0, cfg.jump_sd, L), 0.0)
                if cfg.jump_placement == "V_announce":
                    jumps_V += resid
                else:
                    jumps_x = resid
        ann_all.append(ann); ann_jumps_all.append(ann_jumps)
        garch = GJRGarch(GJRParams(**{**asdict(gp), "sbar": gp.sbar * vol_scale[a]}))
        ms = MispricingState(params, cfg.engine, x0=0.0)
        if stored is not None:                                        # E1.5 option B: draw the long-run state jointly
            si = int(st.get("init_state", a).integers(0, len(stored["x"])))
            ms.x = float(stored["x"][si]); ms.x_prev = float(stored["x_prev"][si]); ms.n_f = float(stored["n_f"][si])
            garch._h = float(stored["h"][si]); garch.sigma2 = garch._h; garch.e_prev = float(stored["e_prev"][si])
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
            sigma_i, e_i = garch.step(eta[i], ph, u_reg[i] if u_reg is not None else None)
            sig[a, i] = sigma_i; e_arr[a, i] = e_i
            fvar[a, i] = garch.forecast_var(21, ph)
            if i + 1 < L:
                extra = jumps_x[i] if jumps_x is not None else 0.0
                x_new = ms.step(e_i + extra, drift + pending[i])
                logV += mu_v + sigV * z[i] + jumps_V[i]
                driver.end(int(day[i + 1]), x_new, u_haz[i])
        # start-price mechanism (v2.1 Phase 1, E1.1 / D13): the GBM is scale-free, so V is rescaled after the fact
        if cfg.start_price_mode == "fixed":
            V[a] *= cfg.start_price / V[a, B]                                  # v2: V_1 = P_1 = start price (the answer key)
        elif cfg.start_price_mode == "randomise":
            lo, hi = cfg.start_price_range
            v1 = math.exp(st.get("start_price", a).uniform(math.log(lo), math.log(hi)))
            V[a] *= v1 / V[a, B]                                               # A: V_1 ~ LogU(range), P_1 = V_1 e^x_1
        else:
            V[a] *= cfg.start_price / (V[a, B] * math.exp(x[a, B]))            # B / C: P_1 = start price, V_1 = P_1 e^-x_1
        meta_assets.append(driver.meta())
    k_render = 1.0
    if cfg.start_price_mode == "both":
        lo, hi = cfg.start_price_range
        k_render = math.exp(st.get("start_price", -1).uniform(math.log(lo / cfg.start_price), math.log(hi / cfg.start_price)))
    phases = relabel_blowoff(phases, day, sched, meta_assets[0].get("top_day"))
    P = V * np.exp(x)
    meta = {"assets": meta_assets, **meta_assets[0], "start_price_mode": cfg.start_price_mode, "k_render": k_render,
            "jump_placement": cfg.jump_placement, "burn_in": cfg.burn_in, "burn_in_mode": cfg.burn_in_mode,
            "n_ann_jumps": int(sum(len(d) for d in ann_jumps_all))}
    return PathResult(cfg, sched, params, gp, day, V, x, P, sig, e_arr, nf, w_arr, fvar, sent, phases, meta, attempt + 1, [],
                      ann_all, ann_jumps_all, k_render)


_STORED_CACHE: Dict[str, Dict[str, np.ndarray]] = {}


def _stored_state(engine: str) -> Dict[str, np.ndarray]:
    """E1.5 option B: the stored long-run sample of (x, x_prev, n_f, GARCH h, e_prev) for `engine` (a hashed artefact of the
    freeze: envs/v2/params/burn_in_states_<engine>.npz). Raises if absent -- no silent fallback to a short burn-in."""
    if engine not in _STORED_CACHE:
        p = VP.stored_state_path(engine)
        if not os.path.exists(p):
            raise RuntimeError(f"burn_in_mode='stored' needs {p}; none exists for engine {engine!r} (E1.5 writes it)")
        z = np.load(p)
        _STORED_CACHE[engine] = {k: np.asarray(z[k], float) for k in ("x", "x_prev", "n_f", "h", "e_prev")}
    return _STORED_CACHE[engine]


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
