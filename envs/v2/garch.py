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

from dataclasses import dataclass

import numpy as np

OMEGA_MULT = {"calm": 1.0, "deterioration": 1.5, "panic": 4.0, "stabilisation": 1.5,
              "mania": 1.5, "blow-off": 2.0, "post-top": 3.0, "sustained-bull": 1.0}   # reviewer D5: no vol reduction in the control (would be a volatility clock)


@dataclass
class GJRParams:
    alpha: float = 0.10      # E1 calibration: plan 0.05; top of the plan's 0.05-0.10 anchor (checklist 3, 13)
    gamma: float = 0.10      # E1 calibration: plan 0.08 (checklist 6, 8)
    beta: float = 0.83       # E1 calibration: plan 0.89; persistence alpha + gamma/2 + beta = 0.98 unchanged
    sbar: float = 0.017      # unconditional daily sd of the x-innovation in calm phases (E1 calibration: 0.016 -> 0.017)
    df: float = 5.0          # Student-t df of eta (plan t(5))
    panic_mult: float = 5.0  # plan default 4, sensitivity 3..6; E1 calibration 5 (checklist 13, 20)
    scale_mode: str = "variance"   # 'variance' (regime-scaled conditional variance) | 'omega' (plan literal; sensitivity)

    @property
    def persistence(self) -> float:
        return self.alpha + 0.5 * self.gamma + self.beta

    @property
    def omega_base(self) -> float:
        return self.sbar ** 2 * (1.0 - self.persistence)

    def omega(self, phase: str) -> float:
        m = OMEGA_MULT.get(phase, 1.0)
        if phase == "panic":
            m = self.panic_mult
        return self.omega_base * m


class GJRGarch:
    """Stateful one-step GJR-GARCH recursion."""

    def __init__(self, params: GJRParams):
        self.p = params
        self.sigma2 = params.sbar ** 2
        self._h = params.sbar ** 2      # phase-normalised variance (scale_mode 'variance')
        self._m_prev = 1.0
        self.e_prev = 0.0

    def mult(self, phase: str) -> float:
        m = OMEGA_MULT.get(phase, 1.0)
        return self.p.panic_mult if phase == "panic" else m

    def step(self, eta: float, phase: str) -> tuple:
        """scale_mode 'variance' (default, E1 calibration): the GJR recursion runs on
        a phase-normalised variance h_t and the phase multiplier scales the WHOLE
        conditional variance, sigma_t^2 = m(phase_t) h_t -- a regime-switching
        variance (Hamilton-Susmel-type) in which a phase change moves the level at
        once and the GARCH persistence governs the decay of shocks within and
        across phases.  scale_mode 'omega' (plan's literal reading): only omega is
        multiplied, so the level adjusts at the GARCH persistence rate; kept as a
        sensitivity (it cannot reach the plan's own panic-vol targets inside a
        15-70-day panic)."""
        p = self.p
        m = self.mult(phase)
        if p.scale_mode == "omega":
            lev = p.gamma * self.e_prev ** 2 if self.e_prev < 0 else 0.0
            self.sigma2 = p.omega(phase) + p.alpha * self.e_prev ** 2 + lev + p.beta * self.sigma2
        else:
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
        """Mean conditional variance over the next `horizon` days (for the IV
        proxy, E2), iterating the recursion in expectation from the current state."""
        p = self.p
        pers = p.persistence
        if p.scale_mode == "omega":
            uncond = p.omega(phase) / (1.0 - pers)
            v = self.sigma2
        else:
            m = self.mult(phase)
            uncond = m * p.omega_base / (1.0 - pers)
            v = m * self._h
        total = 0.0
        for _ in range(horizon):
            total += v
            v = uncond + pers * (v - uncond)
        return total / horizon
