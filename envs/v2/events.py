"""
Event drivers: per-step scripted drift d_t on x, the fundamental drift mu_V,t,
the phase label and the hazard bubble top (v2 plan 2.1 blocks 1, 3, 5, 6, 7).

A driver is stepped by the generator once per day AFTER x_{t} is known:
    drift, mu_V, phase = driver.begin(day, x_t)     # used to form x_{t+1}
    driver.end(day + 1, x_{t+1}, u)                 # may flip state (hazard top)
Days are 1-based benchmark days; burn-in days are <= 0 and always calm.

Scripted targets are tracked with error correction, d_t = (x*_{t+1} - x*_t)
+ lam (x*_t - x_t), so that the realised path follows the scripted target path
x* despite the FW pull and the GARCH noise (lam documented per phase).

Direction and target of events are scripted BY CONSTRUCTION (plan 2.1 block 3);
FW supplies persistence, clustering and overshoot.  The environment is
'FW-shaped, regime-scripted', and says so.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np

from envs.v2.schedule import Schedule

MU_V_BASE = 0.00025   # ~6.5%/year price-only fundamental drift
LAM_PANIC = 0.10
LAM_STAB = 0.05
LAM_POSTTOP = 0.10
STAB_RAMP_DAYS = 30
G_MAX = 0.02          # cap on the compounding mania drift (2%/day); a parameter of the scripted drift, not a price clip
LAM_SB = 0.15         # sustained-bull anchoring pull on x (half-life ~4.6 d): keeps the no-mispricing control inside its
                      # validity band [-0.10, +0.15] with a rejection rate < 5%; documented in the generator spec


def _front_loaded(frac: float) -> float:
    """Share of the panic move completed after a fraction `frac` of the panic
    length: half the move in the first third (plan), linear within segments."""
    frac = min(max(frac, 0.0), 1.0)
    if frac <= 1.0 / 3.0:
        return 1.5 * frac
    return 0.5 + 0.75 * (frac - 1.0 / 3.0)


class CalmDriver:
    """flat / phase-free: no event; calm dynamics throughout."""
    phase_name = "calm"

    def __init__(self, sched: Schedule):
        self.s = sched
        self.topped: Optional[bool] = None
        self.top_day: Optional[int] = None

    def begin(self, day: int, x: float) -> Tuple[float, float, str]:
        return 0.0, MU_V_BASE, "calm"

    def end(self, day: int, x: float, u: float) -> None:
        pass

    def meta(self) -> dict:
        return {"topped": None, "top_day": None}


class SustainedBullDriver(CalmDriver):
    """No scripted mispricing; elevated fundamental drift for the whole horizon."""

    def begin(self, day: int, x: float) -> Tuple[float, float, str]:
        # anchoring drift toward x = 0 in the episode AND the burn-in (so x_1 starts near 0)
        return -LAM_SB * x, (self.s.mu_bull if day >= 1 else MU_V_BASE), ("sustained-bull" if day >= 1 else "calm")


class CrashDriver(CalmDriver):
    """deterioration -> panic -> stabilisation."""

    def __init__(self, sched: Schedule, lam_panic: float = LAM_PANIC):
        super().__init__(sched)
        self.lam_panic = lam_panic
        s = sched
        self.det_start = s.event_start
        self.panic_start = s.event_start + s.det_len
        self.stab_start = self.panic_start + s.panic_len
        self.mu_det = math.log(1.0 - s.D_V) / max(s.det_len, 1)   # log-linear drift delivering D_V
        self.x_panic_entry: Optional[float] = None
        self.x_stab_entry: Optional[float] = None
        self.target = float("nan")

    def phase(self, day: int) -> str:
        if day < self.det_start:
            return "calm"
        if day < self.panic_start:
            return "deterioration"
        if day < self.stab_start:
            return "panic"
        return "stabilisation"

    def _target(self, day: int, x: float) -> Tuple[float, float]:
        """(x*_t, x*_{t+1}) of the scripted path."""
        s = self.s
        if self.phase(day) == "panic":
            if self.x_panic_entry is None:
                self.x_panic_entry = x
            x0 = self.x_panic_entry
            f0 = _front_loaded((day - self.panic_start) / s.panic_len)
            f1 = _front_loaded((day + 1 - self.panic_start) / s.panic_len)
            goal = math.log(s.delta)
            return x0 + (goal - x0) * f0, x0 + (goal - x0) * f1
        if self.phase(day) == "stabilisation":
            if self.x_stab_entry is None:
                self.x_stab_entry = x
            x0 = self.x_stab_entry
            goal = math.log(s.delta_end)
            k0 = min((day - self.stab_start) / STAB_RAMP_DAYS, 1.0)
            k1 = min((day + 1 - self.stab_start) / STAB_RAMP_DAYS, 1.0)
            return x0 + (goal - x0) * k0, x0 + (goal - x0) * k1
        return x, x

    def begin(self, day: int, x: float) -> Tuple[float, float, str]:
        ph = self.phase(day)
        if ph == "calm":
            return 0.0, MU_V_BASE, ph
        if ph == "deterioration":
            return 0.0, self.mu_det, ph
        xs0, xs1 = self._target(day, x)
        lam = self.lam_panic if ph == "panic" else LAM_STAB
        d = (xs1 - xs0) + lam * (xs0 - x)
        return d, 0.0, ph          # V flat after the deterioration ("then flat")


class BubbleDriver(CalmDriver):
    """mania (compounding drift) -> hazard top -> post-top reversal leg -> post-top."""

    def __init__(self, sched: Schedule, h0: float, b: float, g_max: float = G_MAX):
        super().__init__(sched)
        self.h0, self.b, self.g_max = h0, b, g_max
        self.g = sched.g0
        self.top_day = None
        self.topped = False
        self.x_top: Optional[float] = None
        self.mania_days = 0

    def _leg_end(self) -> int:
        return (self.top_day or 10 ** 9) + self.s.post_top_len

    def phase(self, day: int) -> str:
        if day < self.s.event_start:
            return "calm"
        if self.top_day is None or day <= self.top_day:
            return "mania"           # blow-off is relabelled ex post (last third of the mania run)
        return "post-top"

    def begin(self, day: int, x: float) -> Tuple[float, float, str]:
        ph = self.phase(day)
        if ph == "calm":
            return 0.0, MU_V_BASE, ph
        if ph == "mania":
            d = self.g
            self.g = min(self.g * (1.0 + self.s.kappa), self.g_max)   # the DRIFT compounds (super-exponential), capped
            self.mania_days += 1
            return d, MU_V_BASE, ph
        # post-top: reversal leg of -post_top_drop (price fraction) over post_top_len days, then nothing
        if day <= self._leg_end():
            goal = self.x_top + math.log(1.0 - self.s.post_top_drop)
            n = self.s.post_top_len
            k0 = (day - self.top_day - 1) / n
            k1 = (day - self.top_day) / n
            xs0 = self.x_top + (goal - self.x_top) * k0
            xs1 = self.x_top + (goal - self.x_top) * k1
            d = (xs1 - xs0) + LAM_POSTTOP * (xs0 - x)
            return d, MU_V_BASE, ph
        return 0.0, MU_V_BASE, ph

    def end(self, day: int, x: float, u: float) -> None:
        # hazard evaluated on days inside the mania run, using the new x
        if self.top_day is None and day > self.s.event_start and day <= self.s.T:
            h = self.h0 * math.exp(self.b * x)
            if u < h:
                self.top_day = day
                self.topped = True
                self.x_top = x

    def meta(self) -> dict:
        return {"topped": bool(self.topped), "top_day": self.top_day,
                "x_top": self.x_top, "mania_days": self.mania_days}


def make_driver(sched: Schedule, hazard_h0: float, hazard_b: float, g_max: float = G_MAX,
                lam_panic: float = LAM_PANIC):
    if sched.scenario == "crash":
        return CrashDriver(sched, lam_panic)
    if sched.scenario == "bull_trap":
        return BubbleDriver(sched, hazard_h0, hazard_b, g_max)
    if sched.scenario == "sustained_bull":
        return SustainedBullDriver(sched)
    return CalmDriver(sched)


def relabel_blowoff(phases: np.ndarray, days: np.ndarray, sched: Schedule, top_day: Optional[int]) -> np.ndarray:
    """Blow-off = last third of the realised mania run (top day or horizon)."""
    if sched.scenario != "bull_trap":
        return phases
    end = top_day if top_day is not None else sched.T
    start = sched.event_start
    run = end - start + 1
    if run <= 0:
        return phases
    bo_start = end - run // 3 + 1
    out = phases.copy()
    mask = (days >= bo_start) & (days <= end) & (out == "mania")
    out[mask] = "blow-off"
    return out
