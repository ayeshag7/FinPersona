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
  fw_fallback_hl150 (ENGINE_DEFAULT, the engine that runs): the index set with phi raised so that the
                    PULL-RATE half-life ln2 / (mu * n_bar * phi) is 150.0 d at the realised fundamentalist share
                    n_bar of the 20,000-step pilot (phi = 0.4632). CAL: chosen so that checklist item 9 on T = 800
                    paths clears the plan's 60-d floor (DECISION_LOG.md row 2 and addendum); not an estimate.
                    v2.1 Phase 0 numbers (generated/v2_1/findings_reproduction.md): long-pilot ACF(1) half-life
                    147 d (five 200,000-step pilots, 141-155 d); sample half-life ~20 d on the 200-day windows the
                    benchmark runs (14-35 d across seed sets) and 62-72 d on T = 800 paths (both estimator-biased,
                    review B); stationary sd(x) 0.165 (sd_e 0.016) / 0.175 (sd_e 0.017) with the engine's unit-mean
                    innovation weight (0.126 / 0.134 with raw weights, which is what pilot_stats prints).
  fw_single       : the SMM single-stock estimate (tools/calibrate_fw.py). Loading it REQUIRES an accepted file
                    envs/v2/params/fw_single_stock.json carrying "accepted": true; otherwise load_params raises.
                    No accepted estimate exists (the attempt was rejected, J = 408:
                    fw_single_stock.REJECTED.json); renaming the rejected file cannot switch the engine (Phase 0,
                    weakness item 70). Before Phase 0 "fw_single" silently fell back to the engine above.
  fw_hl<days>     : the same construction at another pull-rate half-life (sensitivities, e.g. fw_hl60).
  ar1             : x_{t+1} = rho x_t + d_t + e_t with rho = 1 - ln2/150 (flag).
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, asdict
from typing import Optional

from envs.v2 import mispricing_params as MP

PARAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")
HALF_LIFE_FALLBACK_DAYS = 150.0  # CAL: pull-rate half-life ln2/(mu n_bar phi) of the v2 fallback engine (see the module docstring)
# v2.1 Phase 2: the engine that actually runs comes from envs/v2/params/mispricing.json when that file exists
# (E2.4's decision, with its provenance); until then it is v2's CAL fallback, unchanged.  The LEGACY engines
# below (fw_fallback_hl*, fw_index, pruna, ar1, fw_hl*) keep v2's price_scale = 100 deliberately, so that every
# v2 number and every Phase-1 stored artefact (params/burn_in_states_*.npz) stays reproducible; E2.1's units
# bug fix (price_scale = 1, LIT) is applied to the FITTED engine and to tools/phase2/fw_pure.py, which is what
# reproduces Franke & Westerhoff's own published statistics.  DECISION_LOG P2-2.
ENGINE_DEFAULT = MP.ENGINE


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


FW_PILOT_ENGINE = "fw_pilot"   # a non-AR(1) engine label for the FW population pilots (v2.1 Phase 2:
# ENGINE_DEFAULT is an AR(1) engine now, and using it here would make every pilot report n_bar = 0.5)


def pilot_stats(params: "FWParams", engine: str = FW_PILOT_ENGINE, n_steps: int = 20000, sd_e: float = 0.016,
                seed: int = 12345) -> dict:
    """Long calm-phase simulation with Gaussian innovations of sd `sd_e` (the
    unconditional GARCH scale) to obtain the realised mean fundamentalist share
    n_bar and the mean raw weight w_bar = E[n_f sigma_f + n_c sigma_c].  Used to
    (i) normalise the weight to unit mean and (ii) set the fallback phi at the
    realised share.  Deterministic (fixed seed); cached per parameter set.

    NOTE (v2.1 Phase 0): the pilot runs with RAW weights (w_norm = 1, weight ~ 0.76), so the `sd_x` it
    returns understates the engine's stationary sd(x) by the factor w_bar; `acf1_x` on 20,000 steps has a
    sampling SE of ~0.0007, which is why its implied half-life (188 d) differed from the pull-rate half-life
    (150 d). Use `long_pilot_stats` for reported statistics. Changing n_steps here would change w_bar and
    n_bar and hence every path: deferred to Phase 2 (PREREG_PHASE_0.md §4.5)."""
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


def long_pilot_stats(params: "FWParams", engine: str = FW_PILOT_ENGINE, n_steps: int = 200_000, sd_e: float = 0.017,
                     seed: int = 9001, w_norm: Optional[float] = None, burn: int = 5000) -> dict:
    """Long calm-engine pilot for REPORTED statistics (v2.1 Phase 0, item 71): ACF(1)-implied half-life,
    stationary sd(x), mean fundamentalist share. Unlike `pilot_stats` it uses the engine's unit-mean weight
    normalisation by default (w_norm=None -> the cached w_bar, as the generator does) and never touches the
    normalisation cache. Bartlett SE of ACF(1) at rho ~ 0.9954 over 200,000 steps is ~2.2e-4 (+/- 7 d in
    half-life per pilot)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    st = MispricingState(params, engine, x0=0.0, w_norm=w_norm)
    e = rng.normal(0.0, sd_e, n_steps)
    nfs = np.empty(n_steps); ws = np.empty(n_steps); xs = np.empty(n_steps)
    for i in range(n_steps):
        nfs[i] = st.n_f; ws[i] = st.raw_weight(); xs[i] = st.x
        st.step(e[i], 0.0)
    x = xs[burn:]; xc = x - x.mean()
    a = float((xc[:-1] * xc[1:]).sum() / (xc * xc).sum())
    return {"n_bar": float(nfs[burn:].mean()), "w_bar_raw": float(ws[burn:].mean()), "sd_x": float(x.std()),
            "acf1_x": a, "half_life": float(-math.log(2.0) / math.log(a)) if 0 < a < 1 else float("inf"),
            "share_nf_gt_099": float(np.mean(nfs[burn:] > 0.99)), "n_steps": n_steps, "sd_e": sd_e, "seed": seed,
            "w_norm": st.w_norm, "burn": burn}


def fallback_single_stock(half_life_days: float = None) -> FWParams:
    """Index set with phi raised so that mu * n_bar * phi = ln2 / hl (pull-rate half-life hl, default
    HALF_LIFE_FALLBACK_DAYS = 150 d) at the REALISED fundamentalist share n_bar (fixed point of three pilot
    iterations). Named fw_fallback_hl<hl>."""
    hl = float(half_life_days) if half_life_days else HALF_LIFE_FALLBACK_DAYS
    target = math.log(2.0) / hl
    base = FW_INDEX_2012
    n_bar = 0.5
    phi = target / (base.mu * n_bar)
    for _ in range(3):
        trial = FWParams(phi=phi, name="fw_single_stock_fallback_trial")
        n_bar = pilot_stats(trial, FW_PILOT_ENGINE)["n_bar"]
        phi = target / (base.mu * max(n_bar, 1e-3))
    return FWParams(phi=phi, name=f"fw_fallback_hl{int(hl)}",
                    source=("CAL (no accepted SMM estimate): FW 2012 functional form with phi set for a "
                            f"{hl:.0f}-day pull-rate half-life ln2/(mu n_bar phi) at the realised fundamentalist share "
                            f"n_bar={n_bar:.3f}; see DECISION_LOG.md row 2 and the v2.1 Phase 0 report"))


def fitted_params(half_life_days: Optional[float] = None) -> FWParams:
    """The engine E2.4 adopted, from envs/v2/params/mispricing.json (v2.1 Phase 2).  For the FW families the
    structural parameters are the SMM estimate and `price_scale` is E2.1's confirmed convention; for the AR(1)
    family only the innovation scale and the half-life are carried (the FW fields are unused).  A half-life
    other than the fitted one (the E2.6 sweep) rescales phi so that ln2/(mu n_bar phi) equals it, at the fitted
    engine's own realised n_bar."""
    if not MP.PRESENT:
        raise RuntimeError("envs/v2/params/mispricing.json is absent: no fitted engine exists yet "
                           "(tools/phase2/apply_e2.py writes it)")
    st = dict(MP.STRUCTURAL)
    name = MP.ENGINE if half_life_days is None else f"{MP.ENGINE}_hl{int(half_life_days)}"
    if MP.ENGINE_FAMILY == "ar1":
        p = FWParams(name=name, price_scale=MP.PRICE_SCALE,
                     source=f"FIT (E2.3 SMM, v2.1 Phase 2): AR(1)+GJR-GARCH-t, half-life "
                            f"{half_life_days or MP.HALF_LIFE:.2f} d")
        return p
    fields = {k: float(v) for k, v in st.items() if k in FWParams.__dataclass_fields__}
    p = FWParams(**{**fields, "price_scale": MP.PRICE_SCALE, "name": name,
                    "source": "FIT (E2.3 SMM on FW's nine moments plus the persistence-carrying moments, "
                              "block-bootstrap weight matrix; v2.1 Phase 2, DECISION_LOG P2-*)"})
    if half_life_days is not None:
        n_bar = pilot_stats(p, MP.ENGINE)["n_bar"]
        p = FWParams(**{**asdict(p), "phi": math.log(2.0) / (float(half_life_days) * p.mu * max(n_bar, 1e-3))})
    return p


def ar1_rho(engine: str = ENGINE_DEFAULT) -> float:
    """rho of the AR(1) engines.  v2's `ar1` keeps its historical rho = 1 - ln2/150 (a first-order
    approximation) so its stored burn-in state stays valid; the Phase-2 engines use the exact 2^(-1/h)."""
    if engine == "ar1":
        return 1.0 - math.log(2.0) / HALF_LIFE_FALLBACK_DAYS
    if engine.startswith("ar1_hl"):
        return 2.0 ** (-1.0 / float(engine[6:]))
    if MP.PRESENT and MP.ENGINE_FAMILY == "ar1":
        if engine == MP.ENGINE:
            return 2.0 ** (-1.0 / float(MP.HALF_LIFE))
        if engine.startswith(f"{MP.ENGINE}_hl"):
            return 2.0 ** (-1.0 / float(engine.split("_hl")[-1]))
    return 1.0 - math.log(2.0) / HALF_LIFE_FALLBACK_DAYS


def is_ar1(engine: str) -> bool:
    return engine == "ar1" or engine.startswith("ar1_hl") or (
        MP.PRESENT and MP.ENGINE_FAMILY == "ar1" and (engine == MP.ENGINE or engine.startswith(f"{MP.ENGINE}_hl")))


def load_params(engine: str = ENGINE_DEFAULT) -> FWParams:
    """Parameter set for a named engine. No silent fallback (v2.1 Phase 0, item 70): `fw_single` loads only an
    ACCEPTED single-stock estimate. The engine that runs by default is `mispricing.json`'s when that file exists
    (v2.1 Phase 2) and v2's CAL `fw_fallback_hl150` otherwise."""
    if MP.PRESENT and engine == MP.ENGINE:
        return fitted_params()
    if MP.PRESENT and engine.startswith(f"{MP.ENGINE}_hl"):
        return fitted_params(float(engine.split("_hl")[-1]))
    if engine.startswith("ar1_hl"):
        return FWParams(name=engine, source=f"AR(1) sensitivity at half-life {engine[6:]} d (v2.1 Phase 2)")
    if engine == "fw_index":
        return FW_INDEX_2012
    if engine == "pruna":
        return PRUNA_2016
    if engine == ENGINE_DEFAULT:
        return fallback_single_stock()
    if engine.startswith("fw_fallback_hl"):   # the v2 CAL engine by its own name, whatever ENGINE_DEFAULT is now
        return fallback_single_stock(float(engine[len("fw_fallback_hl"):]))
    if engine == "fw_single":
        path = os.path.join(PARAM_DIR, "fw_single_stock.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"engine 'fw_single' needs an accepted SMM estimate at {path}; none exists "
                                    f"(the attempt was rejected: fw_single_stock.REJECTED.json). Use engine "
                                    f"{ENGINE_DEFAULT!r} (the documented CAL fallback) explicitly.")
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        if d.get("accepted") is not True:
            raise ValueError(f"{path} is not an accepted estimate ('accepted': true missing); a renamed rejected "
                             f"file cannot switch the engine. Use engine {ENGINE_DEFAULT!r}.")
        d.setdefault("name", "fw_single_stock")
        return FWParams(**{k: v for k, v in d.items() if k in FWParams.__dataclass_fields__})
    if engine == "ar1":
        return FWParams(name="ar1")
    if engine.startswith("fw_hl"):          # half-life sensitivities, e.g. fw_hl60, fw_hl300
        return fallback_single_stock(float(engine[5:]))
    raise ValueError(f"unknown mispricing engine {engine!r}")


class MispricingState:
    """One-step FW recursion (or AR(1) fallback) for one asset."""

    def __init__(self, params: FWParams, engine: str = ENGINE_DEFAULT, x0: float = 0.0,
                 w_norm: Optional[float] = None):
        self.p = params
        self.engine = engine
        self.x = float(x0)
        self.x_prev = float(x0)
        self.n_f = 0.5
        self.is_ar1 = is_ar1(engine)
        self.rho_ar1 = ar1_rho(engine)
        # unit-mean normalisation of the FW weight (pilot mean of n_f sigma_f + n_c sigma_c).  For the FITTED
        # engine it is the constant the SMM used (recorded in params/mispricing.json), not a fresh pilot: inside
        # the fit only the product w_bar x sbar is identified, so re-deriving w_bar here would silently rescale
        # the innovation and move the engine's persistence away from the value that was fitted.
        if w_norm is not None:
            self.w_norm = float(w_norm)
        elif self.is_ar1:
            self.w_norm = 1.0
        elif MP.PRESENT and (engine == MP.ENGINE or engine.startswith(f"{MP.ENGINE}_hl")) and "w_bar" in MP.STRUCTURAL:
            self.w_norm = float(MP.STRUCTURAL["w_bar"])
        else:
            self.w_norm = pilot_stats(params, engine)["w_bar"]

    def raw_weight(self) -> float:
        p = self.p
        return self.n_f * p.sigma_f + (1.0 - self.n_f) * p.sigma_c

    def weight(self) -> float:
        return self.raw_weight() / self.w_norm

    def step(self, e: float, d: float) -> float:
        """Advance x by one day given the GARCH innovation e and the scripted drift d."""
        p = self.p
        if self.is_ar1:
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
