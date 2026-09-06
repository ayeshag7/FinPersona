"""
Event drivers: per-step scripted drift d_t on x, the fundamental drift mu_V,t, the phase label and the hazard
bubble top (v2 plan 2.1 blocks 1, 3, 5, 6, 7).

A driver is stepped by the generator once per day AFTER x_{t} is known:
    drift, mu_V, phase = driver.begin(day, x_t)     # used to form x_{t+1}
    driver.end(day + 1, x_{t+1}, u)                 # may flip state (hazard top)
Days are 1-based benchmark days; burn-in days are <= 0 and always calm.

v2.1 Phase 4 (REG-8, E4.6) makes the event dynamics a switch, `events_params.DYNAMICS`:

  A  tracking gain (v2, the incumbent):  d_t = (x*_{t+1} - x*_t) + lam (x*_t - x_t)   -- tracks a scripted PATH
  B  shifted perceived fundamental:      d_t = phi_regime (p* - x_t)                  -- pulls to a LEVEL
  C  scripted drift, no feedback:        d_t = (x*_{t+1} - x*_t)                      -- depth by rejection only
  D  unscripted regime switching:        d_t = phi_regime (p*_seed - x_t), p*_seed DRAWN per seed, no target;
                                         depth and duration are OUTCOMES

B and D are exact in the AR(1) engine in force: x_{t+1} = rho x_t + d_t + e_t, so a fundamentalist pull toward
a belief level p* is simply d_t = phi (p* - x_t).  No change to the mispricing engine is needed, which is why
all four formulations can be compared on one code path.

Phase 4 also fixes four measured defects (E4.8):
  * the blow-off label is assignable IN REAL TIME from the drift, so its variance multiplier reaches the GARCH
    driver.  In v2 it was assigned ex post by `relabel_blowoff`, so the multiplier was dead code since v2;
  * the top day is recorded at the REALISED price peak as well as at the hazard firing;
  * the post-top reversal leg has a decay shape whose realised variance is not drift-dominated;
  * the crash's fundamental decline can continue past the deterioration phase (item 73).

Direction and target of events are scripted BY CONSTRUCTION under A/B/C (plan 2.1 block 3); under D they are
not, which is the point of the comparison.  FW supplies persistence, clustering and overshoot.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np

from envs.v2 import events_params as EP
from envs.v2.schedule import Schedule

MU_V_BASE = 0.00025   # v2 value (~6.5%/year, stipulated). v2.1 Phase 1: the drift in force is value_params.MU_V (FIT, Shiller
                      # price-only 2000-2024), passed to every driver as `mu_V`; this constant is kept only as the documented v2 value.
LAM_PANIC = 0.10
LAM_STAB = 0.05
LAM_POSTTOP = 0.10
STAB_RAMP_DAYS = 30
G_MAX = 0.012         # CAL: cap on the compounding mania drift, calibrated jointly with the hazard (envs/v2/params/hazard.json,
                      # tools/calibrate_hazard.py); a parameter of the scripted drift, not a price clip. E4.4 tests whether the
                      # cap is needed at all once kappa and the mania length are drawn jointly from the LPPLS fits.
LAM_SB = 0.15         # sustained-bull anchoring pull on x -- REG-7 definition C ONLY (half-life ~4.6 d). Definitions A, B and D
                      # set d_t = 0 in the control; which definition is in force is events_params.CONTROL_DEF (D14 is the team's).
DYNAMICS_OPTIONS = ("A", "B", "C", "D")


def _front_loaded(frac: float, share: float = 0.5) -> float:
    """Share of the panic move completed after a fraction `frac` of the panic length.

    v2 hard-coded "half the move in the first third".  E4.2 draws `share` from the panel's own front-loading
    distribution (fast crashes: P10 0.088, P50 0.272, P90 0.574 -- the generator's 0.5 sits at about P85).
    Linear within each segment; share = 0.5 reproduces v2 exactly."""
    frac = min(max(frac, 0.0), 1.0)
    s = min(max(float(share), 1e-6), 1.0 - 1e-6)
    if frac <= 1.0 / 3.0:
        return 3.0 * s * frac
    return s + 1.5 * (1.0 - s) * (frac - 1.0 / 3.0)


class CalmDriver:
    """flat / phase-free: no event; calm dynamics throughout."""
    phase_name = "calm"

    def __init__(self, sched: Schedule, mu_V: float = MU_V_BASE):
        self.s = sched
        self.mu_V = float(mu_V)
        self.topped: Optional[bool] = None
        self.top_day: Optional[int] = None

    def begin(self, day: int, x: float) -> Tuple[float, float, str]:
        return 0.0, self.mu_V, "calm"

    def end(self, day: int, x: float, u: float) -> None:
        pass

    def meta(self) -> dict:
        return {"topped": None, "top_day": None}


class SustainedBullDriver(CalmDriver):
    """The control (REG-7).  Which definition is in force is events_params.CONTROL_DEF; D14 is the team's.

      A  same mispricing process as flat, no x-band; validity on V only (d_t = 0)
      B  band on V only, mania driver off -- identical x dynamics to A, different rejection log
      C  the anchored x of v2: d_t = -LAM_SB x, a scenario clock (recalled at 82 % from price alone)
      D  rendered-matched: the flat x process with a rising V, labelled `calm` so no phase multiplier applies
    """

    def __init__(self, sched: Schedule, mu_V: float = MU_V_BASE, definition: Optional[str] = None,
                 lam_sb: Optional[float] = None):
        super().__init__(sched, mu_V)
        self.definition = str(definition or EP.CONTROL_DEF).upper()
        self.lam_sb = float(LAM_SB if lam_sb is None else lam_sb)

    def begin(self, day: int, x: float) -> Tuple[float, float, str]:
        if day < 1:
            # the burn-in is always calm; under C the anchoring also runs in the burn-in so x_1 starts near 0
            return (-self.lam_sb * x if self.definition == "C" else 0.0), self.mu_V, "calm"
        drift = -self.lam_sb * x if self.definition == "C" else 0.0
        label = "calm" if self.definition == "D" else "sustained-bull"
        return drift, self.s.mu_bull, label

    def meta(self) -> dict:
        return {"topped": None, "top_day": None, "control_definition": self.definition}


class CrashDriver(CalmDriver):
    """deterioration -> panic -> stabilisation, under REG-8 formulation A, B, C or D."""

    def __init__(self, sched: Schedule, lam_panic: float = LAM_PANIC, mu_V: float = MU_V_BASE,
                 dynamics: Optional[str] = None, phi_regime: Optional[dict] = None,
                 rng: Optional[np.random.Generator] = None):
        super().__init__(sched, mu_V)
        self.lam_panic = lam_panic
        self.dyn = str(dynamics or EP.DYNAMICS).upper()
        if self.dyn not in DYNAMICS_OPTIONS:
            raise ValueError(f"dynamics must be one of {DYNAMICS_OPTIONS}")
        self.phi = dict(phi_regime or EP.PHI_REGIME or {})
        s = sched
        self.det_start = s.event_start
        self.panic_start = s.event_start + s.det_len
        self.stab_start = self.panic_start + s.panic_len
        # E4.8 / item 73: how the fundamental decline is spread.  v2 delivered ALL of D_V inside the
        # deterioration phase and set mu_V = 0 afterwards; `tail_share` moves that share into panic.
        tail = float(EP.CRASH_V_TAIL_SHARE) if EP.CRASH_V_MODE == "tail_share" else 0.0
        self.tail_share = min(max(tail, 0.0), 0.95)
        head = 1.0 - self.tail_share
        self.mu_det = math.log(1.0 - s.D_V * head) / max(s.det_len, 1)
        self.mu_panic_v = (math.log(max(1.0 - s.D_V, 1e-6)) - math.log(max(1.0 - s.D_V * head, 1e-6))) \
            / max(s.panic_len, 1) if self.tail_share > 0 else 0.0
        self.x_panic_entry: Optional[float] = None
        self.x_stab_entry: Optional[float] = None
        # formulation D: the belief shift is DRAWN, not scripted to a depth target
        self.p_star_D = None
        if self.dyn == "D":
            g = rng if rng is not None else np.random.default_rng(abs(hash((s.scenario, s.T, s.event_start))) % 2**32)
            lo, hi = (EP.RANGES.get("depth", [-0.54, -0.31]))
            # the belief shift is drawn from the panel's own depth range, in log terms; depth is then an
            # OUTCOME of the pull rather than a target the path is steered onto
            self.p_star_D = float(math.log(1.0 + g.uniform(min(lo, hi), max(lo, hi))))

    def phase(self, day: int) -> str:
        if day < self.det_start:
            return "calm"
        if day < self.panic_start:
            return "deterioration"
        if day < self.stab_start:
            return "panic"
        return "stabilisation"

    def _target(self, day: int, x: float) -> Tuple[float, float]:
        """(x*_t, x*_{t+1}) of the scripted target path (formulations A and C)."""
        s = self.s
        ph = self.phase(day)
        if ph == "panic":
            if self.x_panic_entry is None:
                self.x_panic_entry = x
            x0 = self.x_panic_entry
            f0 = _front_loaded((day - self.panic_start) / s.panic_len, s.front_load)
            f1 = _front_loaded((day + 1 - self.panic_start) / s.panic_len, s.front_load)
            goal = math.log(s.delta)
            return x0 + (goal - x0) * f0, x0 + (goal - x0) * f1
        if ph == "stabilisation":
            if self.x_stab_entry is None:
                self.x_stab_entry = x
            x0 = self.x_stab_entry
            goal = math.log(s.delta_end)
            k0 = min((day - self.stab_start) / STAB_RAMP_DAYS, 1.0)
            k1 = min((day + 1 - self.stab_start) / STAB_RAMP_DAYS, 1.0)
            return x0 + (goal - x0) * k0, x0 + (goal - x0) * k1
        return x, x

    def _p_star(self, ph: str) -> float:
        """The belief level the fundamentalists are pulled toward (formulations B and D)."""
        if self.dyn == "D":
            return float(self.p_star_D or 0.0)
        return math.log(self.s.delta) if ph == "panic" else math.log(self.s.delta_end)

    def _phi(self, ph: str) -> float:
        return float(self.phi.get(ph, self.phi.get("default", 0.024)))

    def begin(self, day: int, x: float) -> Tuple[float, float, str]:
        ph = self.phase(day)
        mu_v = self.mu_V
        if ph == "calm":
            return 0.0, mu_v, ph
        if ph == "deterioration":
            return 0.0, self.mu_det, ph
        # panic / stabilisation: v2 set mu_V = 0 here (item 73); E4.8's `tail_share` mode continues the decline
        mu_v = self.mu_panic_v if (ph == "panic" and self.tail_share > 0) else 0.0
        if self.dyn in ("B", "D"):
            d = self._phi(ph) * (self._p_star(ph) - x)
            return d, mu_v, ph
        xs0, xs1 = self._target(day, x)
        if self.dyn == "C":
            return (xs1 - xs0), mu_v, ph            # no error correction; depth enforced by rejection only
        lam = self.lam_panic if ph == "panic" else LAM_STAB
        return (xs1 - xs0) + lam * (xs0 - x), mu_v, ph


class BubbleDriver(CalmDriver):
    """mania (compounding drift) -> [blow-off] -> hazard top -> post-top reversal leg -> post-top."""

    def __init__(self, sched: Schedule, h0: float, b: float, g_max: float = G_MAX, mu_V: float = MU_V_BASE,
                 blowoff_mode: Optional[str] = None, blowoff_g: Optional[float] = None,
                 post_top_mode: Optional[str] = None, post_top_half_life: Optional[float] = None):
        super().__init__(sched, mu_V)
        self.h0, self.b, self.g_max = h0, b, g_max
        self.g = sched.g0
        self.top_day = None
        self.topped = False
        self.x_top: Optional[float] = None
        self.mania_days = 0
        self.cap_hits = 0
        self.bo_mode = str(blowoff_mode or EP.BLOWOFF_MODE)
        self.bo_g = blowoff_g if blowoff_g is not None else EP.BLOWOFF_G_THRESHOLD
        self.bo_days = 0
        self.pt_mode = str(post_top_mode or EP.POST_TOP_MODE)
        self.pt_hl = post_top_half_life if post_top_half_life is not None else EP.POST_TOP_HALF_LIFE

    def _leg_end(self) -> int:
        return (self.top_day or 10 ** 9) + self.s.post_top_len

    def phase(self, day: int) -> str:
        if day < self.s.event_start:
            return "calm"
        if self.top_day is None or day <= self.top_day:
            # E4.8: the blow-off label is assigned IN REAL TIME from the drift, so the phase multiplier
            # actually reaches the GARCH driver.  v2 assigned it ex post in `relabel_blowoff`, which is why
            # its multiplier has been dead code since v2 (Phase 3 measured the calibration knob diverging
            # 2.2 -> 9.3 with the realised ratio pinned at ~1.1).
            if self.bo_mode == "dynamic" and self.bo_g is not None and self.g >= self.bo_g:
                return "blow-off"
            return "mania"
        return "post-top"

    def begin(self, day: int, x: float) -> Tuple[float, float, str]:
        ph = self.phase(day)
        if ph == "calm":
            return 0.0, self.mu_V, ph
        if ph in ("mania", "blow-off"):
            d = self.g
            g_next = self.g * (1.0 + self.s.kappa)
            if g_next > self.g_max:
                self.cap_hits += 1
            self.g = min(g_next, self.g_max)
            self.mania_days += 1
            if ph == "blow-off":
                self.bo_days += 1
            return d, self.mu_V, ph
        # ---- post-top
        if self.pt_mode == "decay" and self.pt_hl:
            # E4.8: an exponential approach to the reversal target over the WHOLE remaining horizon, so the
            # daily drift is largest at the top and small afterwards.  v2's linear ramp over 10-30 days made
            # the leg drift-dominated: Phase 3 measured its realised variance ratio floored at 1.59 (n = 20)
            # whatever the innovation multiplier was set to.
            goal = self.x_top + math.log(max(1.0 - self.s.post_top_drop, 1e-6))
            k = day - self.top_day
            rho = 0.5 ** (1.0 / max(self.pt_hl, 1e-6))
            xs0 = goal + (self.x_top - goal) * (rho ** max(k - 1, 0))
            xs1 = goal + (self.x_top - goal) * (rho ** k)
            return (xs1 - xs0) + EP.POST_TOP_LAM * (xs0 - x), self.mu_V, ph
        if day <= self._leg_end():
            goal = self.x_top + math.log(1.0 - self.s.post_top_drop)
            n = self.s.post_top_len
            k0 = (day - self.top_day - 1) / n
            k1 = (day - self.top_day) / n
            xs0 = self.x_top + (goal - self.x_top) * k0
            xs1 = self.x_top + (goal - self.x_top) * k1
            d = (xs1 - xs0) + LAM_POSTTOP * (xs0 - x)
            return d, self.mu_V, ph
        return 0.0, self.mu_V, ph

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
                "x_top": self.x_top, "mania_days": self.mania_days,
                "blowoff_days": self.bo_days, "blowoff_mode": self.bo_mode,
                "cap_hits": self.cap_hits,
                "cap_binding_share": (self.cap_hits / self.mania_days) if self.mania_days else None}


def make_driver(sched: Schedule, hazard_h0: float, hazard_b: float, g_max: float = G_MAX,
                lam_panic: float = LAM_PANIC, mu_V: float = MU_V_BASE,
                rng: Optional[np.random.Generator] = None,
                dynamics: Optional[str] = None, control_definition: Optional[str] = None,
                blowoff_mode: Optional[str] = None, blowoff_g: Optional[float] = None,
                post_top_mode: Optional[str] = None, post_top_half_life: Optional[float] = None):
    """`dynamics` (REG-8) and `control_definition` (REG-7) default to events.json; E4.5 and E4.6 pass them
    per run so all four arms of each can be compared on one code path in one process."""
    if sched.scenario == "crash":
        return CrashDriver(sched, lam_panic, mu_V, dynamics=dynamics, rng=rng)
    if sched.scenario == "bull_trap":
        return BubbleDriver(sched, hazard_h0, hazard_b, g_max, mu_V, blowoff_mode=blowoff_mode,
                            blowoff_g=blowoff_g, post_top_mode=post_top_mode,
                            post_top_half_life=post_top_half_life)
    if sched.scenario == "sustained_bull":
        return SustainedBullDriver(sched, mu_V, definition=control_definition)
    return CalmDriver(sched, mu_V)


def relabel_blowoff(phases: np.ndarray, days: np.ndarray, sched: Schedule, top_day: Optional[int]) -> np.ndarray:
    """Blow-off = last third of the realised mania run (top day or horizon).

    This is the v2 EX-POST relabel.  It is a no-op when the dynamic criterion is in force (E4.8): a label
    assigned after the run cannot drive the variance, which is the defect it is kept to demonstrate.  It stays
    reachable behind the switch so the phase report can print both arms."""
    if sched.scenario != "bull_trap" or EP.BLOWOFF_MODE == "dynamic":
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


def realised_top_day(P: np.ndarray, days: np.ndarray, sched: Schedule, top_day: Optional[int]):
    """E4.8: the top day recorded at the REALISED price peak rather than at the day the hazard fired.

    v2 recorded only the hazard firing, which is off by the distance between the firing and the actual
    maximum of the path.  Both are reported; the difference is the off-by-one item's measurement."""
    if sched.scenario != "bull_trap" or top_day is None:
        return None
    m = (days >= sched.event_start) & (days <= min(top_day + sched.post_top_len, sched.T))
    if not m.any():
        return None
    idx = np.where(m)[0]
    return int(days[idx[int(np.nanargmax(P[idx]))]])
