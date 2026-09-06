"""
Scheduled regime sequence (v2 plan 2.1 block 6).

v2 drew every duration from a stipulated uniform ("design-choice durations with quoted empirical anchors, not
a fitted chain").  **v2.1 Phase 4 (E4.2) replaces those with the panel's own empirical P10-P90**, read from
`envs/v2/params/events.json` through `envs/v2/events_params.py`.  The v2 ranges are kept in
`events_params.V2` and are still in force when the file is absent, so the "before" column of the phase report
is code rather than prose and every v2 result reproduces.

Orderings
  setup_first : calm L1 ~ U(0.25 T, 0.55 T), then the event, then resolution to T
  event_first : calm setup ~ U(5, 20) d, then the event, then resolution to T
  phase_free  : calm for the whole horizon (the flat control; also T = 800)
Scenarios
  flat            : calm throughout (no scripted event)
  crash           : deterioration (Ld d, V drifts down by D_V) -> panic (Lp d, x pulled to ln(delta),
                    front-loaded by `front_load`) -> stabilisation (x pulled to ln(delta_end))
  bull_trap       : mania (super-exponential drift, hazard top) -> blow-off -> post-top reversal leg
  sustained_bull  : the control; REG-7 A/B/C/D, selected by events.json (D14 is the team's)
Per-observable onset jitter (+/- 5 d, E2) is drawn here so it is part of the seed.

E4.1's fitted ranges come from the panel's FAST-CRASH sub-population (peak-to-trough <= 126 trading days,
642 episodes / 313 stocks) -- the episodes that fit a 200-day horizon.  That is a stated selection, not a
silent one: the full >= 30 % family has a median duration of 196 days and cannot be represented at T = 200.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

import numpy as np

from envs.v2 import events_params as EP

SCENARIOS = ("flat", "crash", "bull_trap", "sustained_bull")
ORDERINGS = ("setup_first", "event_first", "phase_free")
JITTERED_OBSERVABLES = ("sentiment", "volume", "iv")
SCHEDULE_MODES = ("v2", "v21")


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
    front_load: float = 0.5             # share of the panic move completed in its first third (v2: 0.5)
    # bubble parameters
    kappa: float = 0.0                  # daily compounding of the mania drift
    g0: float = 0.002
    post_top_len: int = 0               # reversal leg length (days)
    post_top_drop: float = 0.0          # reversal size as a price fraction
    # sustained bull
    mu_bull: float = 0.0
    # jitter per observable (days; E2)
    jitter: Dict[str, int] = field(default_factory=dict)
    # v2.1 Phase 4: provenance of the draw itself
    mode: str = "v2"
    truncated: Dict[str, str] = field(default_factory=dict)   # parameter -> what T=200 forced

    def to_dict(self) -> Dict:
        return asdict(self)


def _spec(R, key):
    """A range entry is either [lo, hi] (uniform -- v2 behaviour and any DESIGN range) or
    {"grid": [...]}, an equally-spaced empirical quantile grid from q = 0.10 to q = 0.90.

    PREREG_PHASE_4_ADDENDUM.md section 3: "drawn from the empirical P10-P90" means the empirical
    DISTRIBUTION truncated to that interval, not a uniform over it.  A uniform reproduces the fitted interval
    but replaces the fitted shape with a stipulated one, and mis-centres every right-skewed parameter by
    45-80 % (panel panic_len median 39; a uniform on [15, 100.9] has median 57.9)."""
    v = R.get(key)
    if isinstance(v, dict) and "grid" in v:
        return "grid", [float(z) for z in v["grid"]]
    return "uniform", [float(z) for z in v]


def _draw(rng, R, key) -> float:
    kind, v = _spec(R, key)
    if kind == "grid":
        if len(v) < 2:
            return float(v[0])
        u = float(rng.uniform(0.0, 1.0)) * (len(v) - 1)
        i = int(u)
        if i >= len(v) - 1:
            return float(v[-1])
        return float(v[i] + (v[i + 1] - v[i]) * (u - i))
    lo, hi = v[0], v[1]
    return lo if hi <= lo else float(rng.uniform(lo, hi))


def _draw_int(rng, R, key) -> int:
    kind, v = _spec(R, key)
    if kind == "grid":
        return int(round(_draw(rng, R, key)))
    lo, hi = int(round(v[0])), int(round(v[1]))
    return lo if hi <= lo else int(rng.integers(lo, hi + 1))


def _iu(rng, lo, hi) -> int:
    """Integer draw inclusive of both ends, robust to lo == hi."""
    lo, hi = int(round(lo)), int(round(hi))
    if hi <= lo:
        return lo
    return int(rng.integers(lo, hi + 1))


def _u(rng, lo, hi) -> float:
    lo, hi = float(lo), float(hi)
    return lo if hi <= lo else float(rng.uniform(lo, hi))


def draw_schedule(scenario: str, T: int, rng: np.random.Generator, ordering: str = "setup_first",
                  delta: Optional[float] = None, min_resolution: int = 10,
                  schedule_mode: Optional[str] = None,
                  ranges: Optional[Dict[str, list]] = None,
                  depth_mode: Optional[str] = None,
                  depth_gain: Optional[float] = None) -> Schedule:
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS}")
    if ordering not in ORDERINGS:
        raise ValueError(f"ordering must be one of {ORDERINGS}")
    mode = schedule_mode or ("v21" if EP.PRESENT else "v2")
    if mode not in SCHEDULE_MODES:
        raise ValueError(f"schedule_mode must be one of {SCHEDULE_MODES}")
    R = dict(EP.RANGES if mode == "v21" else EP.V2)
    if ranges:
        # E4.2's sweep passes ranges per run so the whole (det_len, front_load) surface can be published
        R.update({k: (dict(v) if isinstance(v, dict) else list(v)) for k, v in ranges.items()})
    jitter = {k: int(rng.integers(-5, 6)) for k in JITTERED_OBSERVABLES}
    trunc: Dict[str, str] = {}

    if scenario == "flat" or ordering == "phase_free":
        return Schedule(scenario, ordering if scenario != "flat" else "phase_free", T,
                        setup_len=T, event_start=T + 1, jitter=jitter, mode=mode,
                        mu_bull=_draw(rng, R, "mu_bull") if scenario == "sustained_bull" else 0.0)

    if scenario == "sustained_bull":
        # no scripted mispricing event: the whole horizon is the episode
        return Schedule(scenario, "phase_free", T, setup_len=T, event_start=T + 1,
                        mu_bull=_draw(rng, R, "mu_bull"), jitter=jitter, mode=mode)

    if ordering == "setup_first":
        f0, f1 = R["setup_frac"]
        setup = _iu(rng, round(f0 * T), round(f1 * T))
    else:  # event_first
        setup = _iu(rng, *R["setup_event_first"])

    if scenario == "crash":
        det = _draw_int(rng, R, "det_len")
        pan = _draw_int(rng, R, "panic_len")
        fl = _draw(rng, R, "front_load")
        D_V = _draw(rng, R, "D_V")
        if mode == "v21" and "depth" in R:
            # E4.2: the panel gives the episode's DEPTH; the generator needs the mispricing discount that,
            # together with the fundamental decline D_V, delivers it.  depth = (1 - D_V) * delta - 1.
            d_target = _draw(rng, R, "depth")                     # a negative number, e.g. -0.37
            dm = depth_mode or EP.DEPTH_MODE
            if dm == "centred":
                # E4.19/P4-40: drawing depth UNCONDITIONALLY discards `delta`, which is why the
                # `crash_discount` arm factor became exactly inert (checklist item 10) and why depth-only
                # failure dominates the coverage shortfall.  Shift the empirical distribution so its centre
                # tracks the severity the arm asked for, keeping its FITTED SHAPE: a pure location shift
                # changes no quantile spacing.  The shift is relative to the reference delta, so at
                # delta = reference this reduces EXACTLY to the unconditional draw.
                ref = float(R["delta"][0])
                dl = float(delta if delta is not None else ref)
                d_target = d_target + (1.0 - D_V) * (dl - ref)
            # E4.20/P4-41: the TARGET depth is drawn correctly from the panel, but the REALISED drawdown
            # overshoots it -- the panic leg's front-loading and the GARCH innovation carry price past the
            # target -- so realised depth lands near the panel's P10 instead of its P50.  `depth_gain`
            # scales the target to close that loop.  1.0 is the uncalibrated behaviour, exactly.
            g = EP.DEPTH_GAIN if depth_gain is None else float(depth_gain)
            if g != 1.0:
                d_target = d_target * g
            d = float(np.clip((1.0 + d_target) / max(1.0 - D_V, 1e-6), 0.05, 0.999))
        else:
            d = float(delta if delta is not None else R["delta"][0])
        # keep at least `min_resolution` stabilisation days inside the horizon
        overflow = setup + det + pan + min_resolution - T
        if overflow > 0:
            new_pan = max(int(_spec(R, "panic_len")[1][0]), pan - overflow)
            if new_pan != pan:
                trunc["panic_len"] = f"{pan}->{new_pan} (T={T})"
            pan = new_pan
            overflow = setup + det + pan + min_resolution - T
            if overflow > 0:
                new_setup = max(5, setup - overflow)
                if new_setup != setup:
                    trunc["setup_len"] = f"{setup}->{new_setup} (T={T})"
                setup = new_setup
                overflow = setup + det + pan + min_resolution - T
                if overflow > 0:
                    new_det = max(int(_spec(R, "det_len")[1][0]), det - overflow)
                    if new_det != det:
                        trunc["det_len"] = f"{det}->{new_det} (T={T})"
                    det = new_det
        if mode == "v21" and "rec60" in R:
            # E4.2: delta_end is the stabilisation target, set by the panel's 60-day recovery share of the
            # peak-to-trough fall.  rec = 0 -> no recovery (delta_end = delta); rec = 1 -> back to fair value.
            rec = float(np.clip(_draw(rng, R, "rec60"), 0.0, 1.0))
            de = float(np.clip(d + rec * (1.0 - d), d, 1.0))
        else:
            de = _u(rng, d, 1.0)
        return Schedule(scenario, ordering, T, setup_len=setup, event_start=setup + 1,
                        delta=d, D_V=D_V, det_len=det, panic_len=pan, delta_end=de,
                        front_load=fl, jitter=jitter, mode=mode, truncated=trunc)

    # bull_trap.  The draw ORDER is kappa -> post_top_len -> post_top_drop, exactly as v2 evaluated its
    # constructor arguments, so `schedule_mode="v2"` reproduces every v2 bull-trap path bit for bit.
    kap = _draw(rng, R, "kappa")
    ptl = _draw_int(rng, R, "post_top_len")
    ptd = _draw(rng, R, "post_top_drop")
    return Schedule(scenario, ordering, T, setup_len=setup, event_start=setup + 1,
                    kappa=kap, g0=0.002,
                    post_top_len=ptl, post_top_drop=ptd, jitter=jitter, mode=mode, truncated=trunc)
