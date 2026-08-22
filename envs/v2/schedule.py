"""
Scheduled regime sequence (v2 plan 2.1 block 6; decision 3: design-choice
durations with quoted empirical anchors, not a fitted chain).

Orderings
  setup_first : calm L1 ~ U(0.25 T, 0.55 T), then the event, then resolution to T
  event_first : calm setup ~ U(5, 20) d, then the event, then resolution to T
  phase_free  : calm for the whole horizon (the flat control; also T = 800)
Scenarios
  flat            : calm throughout (no scripted event)
  crash           : deterioration (Ld ~ U(15, 40) d, V drifts down by D_V ~ U(10, 30)%)
                    -> panic (Lp ~ U(15, 70) d, x pulled to ln(delta), front-loaded)
                    -> stabilisation (x pulled to ln(delta_end), delta_end ~ U(delta, 1))
  bull_trap       : mania (super-exponential drift, hazard top) -> blow-off (last third
                    of the realised mania run, labelled ex post) -> post-top (reversal
                    leg of -30..-50% over 10..30 d, then post-top label to T)
  sustained_bull  : no scripted mispricing event; V drift mu_V ~ U(0.0015, 0.0025)/day
                    for the whole horizon (complementary no-mispricing control)
Per-observable onset jitter (+/- 5 d, E2) is drawn here so it is part of the seed.

Anchors (plan Section 3 'Phases' row): Ang & Timmermann 2012; Pagan & Sossounov
2003 (bull ~25 m, bear ~15 m); Hamilton 1989; 2008/2020 crash legs 23-120 d to trough.
The durations below are DESIGN CHOICES scaled to a 200-day benchmark horizon.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

import numpy as np

SCENARIOS = ("flat", "crash", "bull_trap", "sustained_bull")
ORDERINGS = ("setup_first", "event_first", "phase_free")
JITTERED_OBSERVABLES = ("sentiment", "volume", "iv")


@dataclass
class Schedule:
    scenario: str
    ordering: str
    T: int
    setup_len: int                      # calm days before the event (T if no event)
    event_start: int                    # 1-based day of the first event day (T+1 if none)
    # crash parameters
    delta: float = 1.0                  # panic discount target (P/V)
    D_V: float = 0.0                    # fundamental drop over the deterioration phase
    det_len: int = 0                    # deterioration length (days)
    panic_len: int = 0
    delta_end: float = 1.0              # stabilisation target
    # bubble parameters
    kappa: float = 0.0                  # daily compounding of the mania drift
    g0: float = 0.002
    post_top_len: int = 0               # reversal leg length (days)
    post_top_drop: float = 0.0          # reversal size as a price fraction (0.30..0.50)
    # sustained bull
    mu_bull: float = 0.0
    # jitter per observable (days; E2)
    jitter: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


def draw_schedule(scenario: str, T: int, rng: np.random.Generator, ordering: str = "setup_first",
                  delta: Optional[float] = None, min_resolution: int = 10) -> Schedule:
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS}")
    if ordering not in ORDERINGS:
        raise ValueError(f"ordering must be one of {ORDERINGS}")
    jitter = {k: int(rng.integers(-5, 6)) for k in JITTERED_OBSERVABLES}

    if scenario == "flat" or ordering == "phase_free":
        return Schedule(scenario, ordering if scenario != "flat" else "phase_free", T,
                        setup_len=T, event_start=T + 1, jitter=jitter,
                        mu_bull=float(rng.uniform(0.0015, 0.0025)) if scenario == "sustained_bull" else 0.0)

    if scenario == "sustained_bull":
        # no event: the whole horizon is the 'episode'
        return Schedule(scenario, "phase_free", T, setup_len=T, event_start=T + 1,
                        mu_bull=float(rng.uniform(0.0015, 0.0025)), jitter=jitter)

    if ordering == "setup_first":
        setup = int(rng.integers(int(round(0.25 * T)), int(round(0.55 * T)) + 1))
    else:  # event_first
        setup = int(rng.integers(5, 21))

    if scenario == "crash":
        d = float(delta if delta is not None else 0.70)
        det = int(rng.integers(15, 41))
        pan = int(rng.integers(15, 71))
        # keep at least `min_resolution` stabilisation days inside the horizon
        overflow = setup + det + pan + min_resolution - T
        if overflow > 0:
            pan = max(15, pan - overflow)
            overflow = setup + det + pan + min_resolution - T
            if overflow > 0:
                setup = max(5, setup - overflow)
        return Schedule(scenario, ordering, T, setup_len=setup, event_start=setup + 1,
                        delta=d, D_V=float(rng.uniform(0.10, 0.30)), det_len=det, panic_len=pan,
                        delta_end=float(rng.uniform(d, 1.0)), jitter=jitter)

    # bull_trap
    return Schedule(scenario, ordering, T, setup_len=setup, event_start=setup + 1,
                    kappa=float(rng.uniform(0.02, 0.04)), g0=0.002,
                    post_top_len=int(rng.integers(10, 31)),
                    post_top_drop=float(rng.uniform(0.30, 0.50)), jitter=jitter)
