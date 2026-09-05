"""
GJR-GARCH(1,1) with standardised Student-t(5) shocks on the x-innovation
(v2 plan 2.1 block 4; Section 3 row 'Volatility dynamics').

    sigma_t^2 = omega_t + alpha e_{t-1}^2 + gamma e_{t-1}^2 1[e_{t-1} < 0] + beta sigma_{t-1}^2
    e_t = sigma_t * eta_t,  eta_t ~ t(5)/sqrt(5/3)

alpha = 0.05, gamma = 0.08, beta = 0.89 -> persistence alpha + gamma/2 + beta = 0.98
(half-life of a variance shock ~34 days).  omega_base is chosen so that the
unconditional daily sd of the x-innovation is `sbar` (1.6%/day) in calm phases:
    omega_base = sbar^2 (1 - alpha - gamma/2 - beta)
and omega_t = omega_base * mult(phase_t) with the phase multipliers of the plan:
calm 1, deterioration 1.5, panic 4, stabilisation 1.5, mania 1.5, blow-off 2,
post-top 3, sustained-bull 1.

The recursion is stepped one observation at a time by the generator (the omega
multiplier depends on the phase, which can depend on the path through the
hazard top), so this module exposes a small stateful object.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

OMEGA_MULT = {"calm": 1.0, "deterioration": 1.5, "panic": 4.0, "stabilisation": 1.5,
              "mania": 1.5, "blow-off": 2.0, "post-top": 3.0, "sustained-bull": 1.0}   # reviewer D5: no vol reduction in the control (would be a volatility clock)

# v2.1 Phase 3: the parameters in force come from envs/v2/params/volatility.json when it exists (E3.1-E3.4 FIT;
# loader envs/v2/volatility_params.py, mispricing_params-style: absent -> the v2 CAL values below, present ->
# governs, malformed -> raises; test_garch_params_in_force enforces presence at hand-over). The v2 CAL defaults
# below are unchanged as the documented fallback and for the stored sensitivities.
from envs.v2 import volatility_params as VOLP  # noqa: E402


@dataclass
class GJRParams:
    alpha: float = VOLP.ALPHA      # v2 CAL 0.10 -> E3.1 FIT median (volatility.json)
    gamma: float = VOLP.GAMMA      # v2 CAL 0.10 -> E3.1 FIT median
    beta: float = VOLP.BETA        # v2 CAL 0.83 -> E3.1 FIT median
    sbar: float = VOLP.SBAR        # v2 CAL 0.017 -> E3.1 FIT via the variance-accounting identity (PREREG 3.4)
    df: float = VOLP.DF            # v2 CAL t(5) -> E3.2 FIT (diffusive tail net of jumps)
    panic_mult: float = VOLP.PANIC_MULT  # v2 CAL 5 -> E3.3 FIT (x-innovation scale, closed-loop calibrated)
    scale_mode: str = VOLP.SCALE_MODE    # 'variance' (A) | 'omega' (B; ramp_days > 0 adds the FIT ramp) | 'switching' (C)
    # v2.1 Phase 3 (E3.3/E3.4; None -> the v2 CAL OMEGA_MULT/panic_mult path, bit-identical to Phase 2):
    mult: Optional[Dict[str, float]] = field(default_factory=lambda: VOLP.MULT)   # FIT phase multipliers on the x-innovation variance
    ramp_days: int = VOLP.RAMP_DAYS      # mechanism B: linear ramp of the omega multiplier after a phase change
    switching: Optional[Dict] = field(default_factory=lambda: VOLP.SWITCHING)     # mechanism C: {v_ratio, p_exit, p_entry_base, p_entry: {phase: p}}

    @property
    def persistence(self) -> float:
        return self.alpha + 0.5 * self.gamma + self.beta

    @property
    def omega_base(self) -> float:
        return self.sbar ** 2 * (1.0 - self.persistence)

    def phase_mult(self, phase: str) -> float:
        if self.mult is not None:
            return float(self.mult.get(phase, 1.0))
        m = OMEGA_MULT.get(phase, 1.0)
        return self.panic_mult if phase == "panic" else m

    def omega(self, phase: str) -> float:
        return self.omega_base * self.phase_mult(phase)


class GJRGarch:
    """Stateful one-step GJR-GARCH recursion."""

    def __init__(self, params: GJRParams):
        self.p = params
        self.sigma2 = params.sbar ** 2
        self._h = params.sbar ** 2      # phase-normalised variance (scale_mode 'variance' / 'switching')
        self._m_prev = 1.0
        self.e_prev = 0.0
        # mechanism B (v2.1 Phase 3): ramped omega multiplier state
        self._m_omega = 1.0
        self._m_from = 1.0
        self._ramp_ctr = 10 ** 9
        self._last_phase: str | None = None
        # mechanism C (v2.1 Phase 3): two-regime state (0 = calm, 1 = stress)
        self.regime = 0

    def mult(self, phase: str) -> float:
        return self.p.phase_mult(phase)

    def step(self, eta: float, phase: str, u: float = None) -> tuple:
        """scale_mode 'variance' (mechanism A, in force since E1/A3): the GJR recursion runs on a
        phase-normalised variance h_t and the phase multiplier scales the WHOLE conditional variance,
        sigma_t^2 = m(phase_t) h_t -- a phase change moves the level at once and the GARCH persistence governs
        the decay of shocks within and across phases.  scale_mode 'omega' (mechanism B; the plan's literal
        reading, plus v2.1 Phase 3's FIT ramp when ramp_days > 0): only omega is multiplied, so the level
        adjusts at the GARCH persistence rate; with ramp_days = 0 and mult = None this is bit-identical to the
        v2 sensitivity.  scale_mode 'switching' (mechanism C, v2.1 Phase 3 / REG-6): sigma_t^2 = v(R_t) h_t with
        R_t a two-state Markov chain whose exit rate is FIT and whose entry probability is the only thing the
        scripted phase sets; `u` is the day's uniform draw from the 'regime' stream."""
        p = self.p
        if p.scale_mode == "omega":
            if p.ramp_days and p.ramp_days > 0:
                target = p.phase_mult(phase)
                if phase != self._last_phase:
                    self._m_from = self._m_omega
                    self._ramp_ctr = 0
                    self._last_phase = phase
                self._ramp_ctr += 1
                f = min(self._ramp_ctr / float(p.ramp_days), 1.0)
                self._m_omega = self._m_from + (target - self._m_from) * f
                omega_eff = p.omega_base * self._m_omega
            else:
                omega_eff = p.omega(phase)
            lev = p.gamma * self.e_prev ** 2 if self.e_prev < 0 else 0.0
            self.sigma2 = omega_eff + p.alpha * self.e_prev ** 2 + lev + p.beta * self.sigma2
        else:
            if p.scale_mode == "switching":
                sw = p.switching or {}
                pe = sw.get("p_entry", {}).get(phase, sw.get("p_entry_base", 0.0))
                px = sw.get("p_exit", 0.0)
                if u is not None:
                    if self.regime == 0 and u < pe:
                        self.regime = 1
                    elif self.regime == 1 and u < px:
                        self.regime = 0
                m = float(sw.get("v_ratio", 1.0)) if self.regime == 1 else 1.0
            else:
                m = self.mult(phase)
            e_n = self.e_prev / np.sqrt(self._m_prev)           # innovation in normalised units
            lev = p.gamma * e_n ** 2 if e_n < 0 else 0.0
            self._h = p.omega_base + p.alpha * e_n ** 2 + lev + p.beta * self._h
            self.sigma2 = m * self._h
            self._m_prev = m
        sigma = float(np.sqrt(self.sigma2))
        e = sigma * float(eta)
        self.e_prev = e
        return sigma, e

    def forecast_var(self, horizon: int = 21, phase: str = "calm") -> float:
        """Mean conditional variance over the next `horizon` days, iterating the recursion in expectation from
        the current state. Hidden diagnostic column only since v2.1 Phase 3 (the rendered IV is E3.5's past-only
        filter on observed returns, envs/v2/observables.py::iv_block_v21)."""
        p = self.p
        pers = p.persistence
        if p.scale_mode == "omega":
            base = self._m_omega if (p.ramp_days and p.ramp_days > 0) else p.phase_mult(phase)
            uncond = p.omega_base * base / (1.0 - pers)
            v = self.sigma2
        else:
            if p.scale_mode == "switching":
                sw = p.switching or {}
                m = float(sw.get("v_ratio", 1.0)) if self.regime == 1 else 1.0
            else:
                m = self.mult(phase)
            uncond = m * p.omega_base / (1.0 - pers)
            v = m * self._h
        total = 0.0
        for _ in range(horizon):
            total += v
            v = uncond + pers * (v - uncond)
        return total / horizon
