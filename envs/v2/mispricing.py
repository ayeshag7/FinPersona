"""
Mispricing process x_t = log P_t - log V_t (v2 plan 2.1 blocks 2-3, Section 2.2;
decision 2: Franke-Westerhoff functional form, parameters re-estimated on single
stocks, index parameters as sensitivity, AR(1) fallback behind a flag).

Calm-phase recursion (Franke & Westerhoff 2012, DCA-HPM, with ONE innovation):
    x_{t+1} = x_t + mu * ( n_f phi (-x_t) + n_c chi (x_t - x_{t-1}) ) + d_t + w_t e_t
    n_f     = 1 / (1 + exp(-beta a_{t-1})),   n_c = 1 - n_f
    a_t     = alpha_0 + alpha_n (n_f - n_c) + alpha_p (s x_t)^2
    w_t     = (n_f sigma_f + n_c sigma_c) / w_bar,  w_bar = pilot mean of the numerator (unit mean)
where e_t is the GJR-GARCH-t innovation (garch.py), d_t the scripted event drift
(events.py), and s = `price_scale` converts x to the units FW use for the
misalignment term (FW work in log price x 100, i.e. percent units; the linear
terms are unit-free).  sigma_f / sigma_c enter ONLY through the unit-mean weight
w_t (chartist-dominated days are noisier), never as a second noise source.

Parameter sets
  fw_index_2012   : FW 2012 Table (S&P 500 1980-2007, J-test p = 32.6%) -- provenance
                    for the functional form; index-level persistence (half-life ~580 d).
  pruna_2016      : Pruna, Polukarov & Jennings 2016 re-estimate (random-walk fundamental).
  fw_single_stock : re-estimated on ~10 large-cap single stocks by SMM
                    (tools/calibrate_fw.py writes envs/v2/params/fw_single_stock.json).
                    If the file is absent the DOCUMENTED FALLBACK is used: the index
                    set with phi raised so that the calm mispricing half-life is ~150 d (realised ~60-70 d)
                    (mu * n_bar * phi = ln 2 / 150 at the realised share n_bar), published as a design
                    choice, not an estimate (DECISION_LOG.md row 2).
  ar1             : x_{t+1} = rho x_t + d_t + e_t with rho = 1 - ln2/150 (flag).
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, asdict
from typing import Optional

PARAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")
HALF_LIFE_FALLBACK_DAYS = 150.0  # design choice: the REALISED half-life (sample ACF on T=800 paths, with GARCH-t+jumps noise) must clear the plan's 60 d floor; the pilot/stationary value is ~150 d


@dataclass
class FWParams:
    phi: float = 0.12
    chi: float = 1.50
    sigma_f: float = 0.758
    sigma_c: float = 2.087
    alpha_0: float = -0.327
    alpha_n: float = 1.79
    alpha_p: float = 18.43
    beta: float = 1.0
    mu: float = 0.01
    price_scale: float = 100.0      # FW units: log price x 100
    name: str = "fw_index_2012"
    source: str = "Franke & Westerhoff 2012, JEDC 36:1193-1211, DCA-HPM column"

    def to_dict(self):
        return asdict(self)


FW_INDEX_2012 = FWParams()
PRUNA_2016 = FWParams(phi=0.121, chi=1.555, sigma_f=0.592, sigma_c=1.917, alpha_0=-0.301,
                      alpha_n=1.990, alpha_p=22.741, name="pruna_2016",
                      source="Pruna, Polukarov & Jennings 2016, arXiv:1604.08824, Table 1")


_PILOT_CACHE: dict = {}


def pilot_stats(params: "FWParams", engine: str = "fw_single", n_steps: int = 20000, sd_e: float = 0.016,
                seed: int = 12345) -> dict:
    """Long calm-phase simulation with Gaussian innovations of sd `sd_e` (the
    unconditional GARCH scale) to obtain the realised mean fundamentalist share
    n_bar and the mean raw weight w_bar = E[n_f sigma_f + n_c sigma_c].  Used to
    (i) normalise the weight to unit mean and (ii) set the fallback phi at the
    realised share.  Deterministic (fixed seed); cached per parameter set."""
    import numpy as np
    key = (params.name, round(params.phi, 6), round(params.alpha_p, 6), engine)
    if key in _PILOT_CACHE:
        return _PILOT_CACHE[key]
    rng = np.random.default_rng(seed)
    st = MispricingState(params, engine, x0=0.0, w_norm=1.0)
    e = rng.normal(0.0, sd_e, n_steps)
    nfs = np.empty(n_steps); ws = np.empty(n_steps); xs = np.empty(n_steps)
    for i in range(n_steps):
        nfs[i] = st.n_f; ws[i] = st.raw_weight(); xs[i] = st.x
        st.step(e[i], 0.0)
    out = {"n_bar": float(nfs[2000:].mean()), "w_bar": float(ws[2000:].mean()),
           "sd_x": float(xs[2000:].std()), "acf1_x": float(np.corrcoef(xs[2000:-1], xs[2001:])[0, 1])}
    _PILOT_CACHE[key] = out
    return out


def fallback_single_stock(half_life_days: float = None) -> FWParams:
    """Index set with phi raised so that mu * n_bar * phi = ln2 / 90 (calm
    half-life ~90 d) at the REALISED fundamentalist share n_bar (fixed point of
    three pilot iterations)."""
    hl = float(half_life_days) if half_life_days else HALF_LIFE_FALLBACK_DAYS
    target = math.log(2.0) / hl
    base = FW_INDEX_2012
    n_bar = 0.5
    phi = target / (base.mu * n_bar)
    for _ in range(3):
        trial = FWParams(phi=phi, name="fw_single_stock_fallback_trial")
        n_bar = pilot_stats(trial)["n_bar"]
        phi = target / (base.mu * max(n_bar, 1e-3))
    return FWParams(phi=phi, name="fw_single_stock_fallback" if not half_life_days else f"fw_fallback_hl{int(hl)}",
                    source=("DESIGN CHOICE (no SMM estimate available): FW 2012 functional form with phi set for a "
                            f"~{hl:.0f}-day stationary calm half-life at the realised fundamentalist share "
                            f"n_bar={n_bar:.3f}; see DECISION_LOG.md row 2"))


def load_params(engine: str = "fw_single") -> FWParams:
    if engine == "fw_index":
        return FW_INDEX_2012
    if engine == "pruna":
        return PRUNA_2016
    if engine == "fw_single":
        path = os.path.join(PARAM_DIR, "fw_single_stock.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            d.setdefault("name", "fw_single_stock")
            return FWParams(**{k: v for k, v in d.items() if k in FWParams.__dataclass_fields__})
        return fallback_single_stock()
    if engine == "ar1":
        return FWParams(name="ar1")
    if engine.startswith("fw_hl"):          # half-life sensitivities, e.g. fw_hl60, fw_hl300
        return fallback_single_stock(float(engine[5:]))
    raise ValueError(f"unknown mispricing engine {engine!r}")


class MispricingState:
    """One-step FW recursion (or AR(1) fallback) for one asset."""

    def __init__(self, params: FWParams, engine: str = "fw_single", x0: float = 0.0,
                 w_norm: Optional[float] = None):
        self.p = params
        self.engine = engine
        self.x = float(x0)
        self.x_prev = float(x0)
        self.n_f = 0.5
        self.rho_ar1 = 1.0 - math.log(2.0) / HALF_LIFE_FALLBACK_DAYS
        # unit-mean normalisation of the FW weight (pilot mean of n_f sigma_f + n_c sigma_c)
        self.w_norm = float(w_norm) if w_norm is not None else (
            pilot_stats(params, engine)["w_bar"] if engine != "ar1" else 1.0)

    def raw_weight(self) -> float:
        p = self.p
        return self.n_f * p.sigma_f + (1.0 - self.n_f) * p.sigma_c

    def weight(self) -> float:
        return self.raw_weight() / self.w_norm

    def step(self, e: float, d: float) -> float:
        """Advance x by one day given the GARCH innovation e and the scripted drift d."""
        p = self.p
        if self.engine == "ar1":
            x_new = self.rho_ar1 * self.x + d + e
            self.x_prev, self.x = self.x, x_new
            return x_new
        n_f, n_c = self.n_f, 1.0 - self.n_f
        d_f = p.phi * (-self.x)
        d_c = p.chi * (self.x - self.x_prev)
        w = self.weight()
        x_new = self.x + p.mu * (n_f * d_f + n_c * d_c) + d + w * e
        # update the population shares for the next step (uses the current x)
        a = p.alpha_0 + p.alpha_n * (n_f - n_c) + p.alpha_p * (p.price_scale * self.x) ** 2
        a = max(min(a, 50.0), -50.0)
        self.n_f = 1.0 / (1.0 + math.exp(-p.beta * a))
        self.x_prev, self.x = self.x, x_new
        return x_new
