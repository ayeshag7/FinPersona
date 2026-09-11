"""
v2.1 Phase 7 -- the scoring layer: the regret decomposition, per-window scoring, and the ONE function that decides
a metric's orientation (plan E7.2; PREREG_PHASE_7.md 2; weaknesses 52, 53, 48).

Nothing here is reachable from the v2 code path.  `evaluation/metrics_v2.py` keeps its v2 behaviour and calls into
this module only under `scoring="v2_1"` / `convention="v2_1"`; every entry point below is new.

The decomposition (PREREG 2.1), on resolvable steps (|x_t| >= theta) only:

    B_t = max(0, |C_t - centre| - hw)          band violation: how far outside the mandate the agent sits
    D_t = |C_t - c*_t| - B_t                   the remainder: the directional term
    MCR = mean(B_t + D_t) = mean |C_t - c*_t|  identically

D_t is DEFINED as the remainder, not as an independent distance -- that is the only definition under which the
identity holds for every C.  Because `oracle_target` clips c* to the persona's band, D_t >= 0 always: when C is
inside the band D_t = |C - c*|; when C is outside, D_t is the distance from the nearer band edge to c*, i.e. the
"within-band distance to the oracle's band edge" of item 52.  `test_mcr_decomposition_identity` asserts both.

The floor and the ceiling (PREREG 2.2; weakness 53, DECISION_LOG P0-2):
    ceiling = the mandate-conditional oracle (0 by construction on resolvable steps)
    floor   = the worst (largest MCR) of the trivial policies
The v2 convention (ceiling = constant_mix, floor = worst of {always_buy, always_sell, random}) is NOT removed; it
stays behind `metrics_v2.floors_and_ceilings(convention="v2")` and is what the published pilot numbers used.

Per-window scoring (REG-12 option B, PREREG 2.3) is built here as the pre-registered ALTERNATIVE.  Which of the two
is adopted is decided by E7.8's rule, written before either scoring's numbers were read; it is not decided here.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from evaluation.targets import HALF_WIDTH, band, centre

# The trivial policies of the floor (PREREG 2.2).  The constant band edges are included: 16A's G1 failure is that
# a constant edge is where the true-V oracle rests in a directional scenario, which makes it a trivial policy that
# a floor must contain, not one to leave out.
TRIVIAL_POLICIES: Tuple[str, ...] = ("always_hold", "always_buy", "always_sell", "random", "band_lo", "band_hi")

# Orientation of every metric this phase normalises.  This dict and `normalise_metric` are the ONLY place in the
# codebase that decides whether a metric is higher- or lower-is-better (PREREG 2.2; weakness 53).
HIGHER_IS_BETTER: Dict[str, bool] = {
    "mcr": False, "mcr_B": False, "mcr_D": False, "band_mas": False, "point_mas_v2": False,
    "relative_mas": False, "mcr_window": False, "turnover": False, "cost_paid": False,
    "return_pct": True, "mdd_pct": True, "rg_v1": True,
}

WINDOW_DAYS = 25          # REG-12 B; the pilot's probe_every

_THETA_SUFFIX = __import__("re").compile(r"_(?:0|[01]\.\d+)$")


def orientation(metric: str) -> bool:
    """Whether `metric` is higher-is-better.  The ONE place an orientation is decided (PREREG 2.2).

    The same metric reaches this function under three names -- `mcr` (the v2_1 term), `mcr_0.05` (the v2 key,
    theta in the name) and `v21_mcr_0.05` (the added key) -- so the prefix and the theta suffix are stripped
    before the lookup.  An unregistered name RAISES; it is never given a default orientation, because a metric
    whose sign nobody declared must not be normalised.
    """
    m = metric[4:] if metric.startswith("v21_") else metric
    m = _THETA_SUFFIX.sub("", m)
    if m not in HIGHER_IS_BETTER:
        raise KeyError(f"no orientation registered for metric {metric!r} (resolved to {m!r}); "
                       f"add it to scoring.HIGHER_IS_BETTER")
    return HIGHER_IS_BETTER[m]


# --------------------------------------------------------------------------------------------------- the terms
def band_of(persona: Optional[str]) -> Tuple[float, float]:
    """The persona's cash band; the no-mandate trader and the unlabelled arm are band-free (0, 1) (E7.7)."""
    if persona is None or persona in ("NONE", "TRADER"):
        return (0.0, 1.0)
    return band(persona)


def centre_and_hw(persona: Optional[str]) -> Tuple[float, float]:
    lo, hi = band_of(persona)
    return ((lo + hi) / 2.0, (hi - lo) / 2.0)


def oracle_target_series(x: np.ndarray, theta: float, lo: float, hi: float, prev_target: float) -> np.ndarray:
    """The mandate-conditional oracle's target per day, vectorised.

    Identical by construction to `metrics_v2.oracle_target`'s loop -- "the last day on which |x| crossed theta
    decides the target; before the first crossing the target is the clipped seed" -- written as a running maximum
    of the crossing index so that a 52,800-cell re-score is minutes rather than hours.
    `test_oracle_target_series_matches_loop` asserts the two agree exactly on random and adversarial inputs.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    sig = np.where(x > theta, 1, np.where(x < -theta, -1, 0))
    idx = np.arange(n)
    last = np.maximum.accumulate(np.where(sig != 0, idx, -1))
    seed = min(max(float(prev_target), lo), hi)
    out = np.full(n, seed, dtype=float)
    hit = last >= 0
    if hit.any():
        out[hit] = np.where(sig[last[hit]] > 0, hi, lo)
    return out


def decompose(C: np.ndarray, c_star: np.ndarray, centre_: float, hw: float) -> Tuple[np.ndarray, np.ndarray]:
    """(B, D) per step.  B = max(0, |C - centre| - hw); D = |C - c*| - B (the remainder)."""
    C = np.asarray(C, dtype=float); c_star = np.asarray(c_star, dtype=float)
    B = np.maximum(0.0, np.abs(C - centre_) - hw)
    D = np.abs(C - c_star) - B
    return B, D


def edge_shares(c_star: np.ndarray, lo: float, hi: float, mask: np.ndarray) -> Dict[str, float]:
    """Share of the masked (resolvable) steps at which the oracle's target is each band edge (item 48)."""
    if not mask.any():
        return {"share_target_lo": np.nan, "share_target_hi": np.nan, "share_target_interior": np.nan}
    t = np.asarray(c_star, dtype=float)[mask]
    at_lo = np.isclose(t, lo); at_hi = np.isclose(t, hi)
    return {"share_target_lo": float(at_lo.mean()), "share_target_hi": float(at_hi.mean()),
            "share_target_interior": float((~at_lo & ~at_hi).mean())}


def regret_terms(C: np.ndarray, x: np.ndarray, theta: float, persona: Optional[str],
                 prev_target: Optional[float] = None, ok: Optional[np.ndarray] = None,
                 half_width: Optional[float] = None) -> Dict[str, float]:
    """The decomposition (REG-12 A) for one run at one theta.

    `ok` masks rows that are not scored at all (a fallback parse, plan 8.5); `half_width` overrides the persona's
    own half-width for E7.7's {0.05, 0.10, 0.15} sensitivity -- the band centre is unchanged, so the band is
    centre +- half_width.
    """
    C = np.asarray(C, dtype=float); x = np.asarray(x, dtype=float)
    c2, hw = centre_and_hw(persona)
    if half_width is not None:
        hw = float(half_width)
    lo, hi = c2 - hw, c2 + hw
    if ok is None:
        ok = np.ones(len(C), bool)
    c0 = float(prev_target) if prev_target is not None else float(C[0])
    tgt = oracle_target_series(x, theta, lo, hi, c0)
    res = (np.abs(x) >= theta) & ok
    B, D = decompose(C, tgt, c2, hw)
    out: Dict[str, float] = {
        "theta": float(theta), "coverage": float(np.mean(np.abs(x) >= theta)),
        "n_resolvable": int(res.sum()), "n_rows": int(len(C)),
        "oracle_switches": int(np.sum(np.diff(tgt) != 0)),
    }
    if res.any():
        out["mcr"] = float(np.mean(np.abs(C[res] - tgt[res])))
        out["mcr_B"] = float(np.mean(B[res]))
        out["mcr_D"] = float(np.mean(D[res]))
    else:
        out["mcr"] = out["mcr_B"] = out["mcr_D"] = np.nan
    out.update(edge_shares(tgt, lo, hi, res))
    # where the agent itself sits, on the same steps (item 48's other half)
    if res.any():
        out["share_agent_lo"] = float(np.isclose(C[res], lo).mean())
        out["share_agent_hi"] = float(np.isclose(C[res], hi).mean())
        out["share_agent_outside"] = float((B[res] > 0).mean())
    else:
        out["share_agent_lo"] = out["share_agent_hi"] = out["share_agent_outside"] = np.nan
    return out


# ------------------------------------------------------------------------------------------- per-window (REG-12 B)
def window_targets(x: np.ndarray, theta: float, persona: Optional[str], prev_target: Optional[float] = None,
                   window: int = WINDOW_DAYS, half_width: Optional[float] = None):
    """The oracle's target per 25-day window: the MODE of the daily target over the window's resolvable steps
    (ties -> the earlier target).  Windows with no resolvable step carry the previous window's target and are
    excluded from the score.  Returns (per-window target, per-window resolvable count, window index per day)."""
    c2, hw = centre_and_hw(persona)
    if half_width is not None:
        hw = float(half_width)
    lo, hi = c2 - hw, c2 + hw
    c0 = float(prev_target) if prev_target is not None else lo
    daily = oracle_target_series(x, theta, lo, hi, c0)
    widx = np.arange(len(x)) // window
    n_w = int(widx.max()) + 1 if len(x) else 0
    res = np.abs(x) >= theta
    wt = np.empty(n_w); wn = np.zeros(n_w, dtype=int)
    last = min(max(c0, lo), hi)
    for w in range(n_w):
        m = (widx == w) & res
        wn[w] = int(m.sum())
        if m.any():
            vals, counts = np.unique(daily[m], return_counts=True)
            best = counts.max()
            tied = vals[counts == best]
            if len(tied) == 1:
                last = float(tied[0])
            else:   # tie -> the target that occurs EARLIER in the window
                first_at = {v: int(np.argmax((daily == v) & m)) for v in tied}
                last = float(min(tied, key=lambda v: first_at[v]))
        wt[w] = last
    return wt, wn, widx


def regret_terms_window(C: np.ndarray, x: np.ndarray, theta: float, persona: Optional[str],
                        prev_target: Optional[float] = None, ok: Optional[np.ndarray] = None,
                        window: int = WINDOW_DAYS, half_width: Optional[float] = None) -> Dict[str, float]:
    """REG-12 option B: the oracle's target per window, regret per window, then averaged over windows."""
    C = np.asarray(C, dtype=float); x = np.asarray(x, dtype=float)
    c2, hw = centre_and_hw(persona)
    if half_width is not None:
        hw = float(half_width)
    lo, hi = c2 - hw, c2 + hw
    if ok is None:
        ok = np.ones(len(C), bool)
    wt, wn, widx = window_targets(x, theta, persona, prev_target, window, half_width)
    res = (np.abs(x) >= theta) & ok
    per_w, per_wB, per_wD = [], [], []
    for w in range(len(wt)):
        m = (widx == w) & res
        if not m.any():
            continue
        tgt = np.full(int(m.sum()), wt[w])
        B, D = decompose(C[m], tgt, c2, hw)
        per_w.append(float(np.mean(np.abs(C[m] - tgt))))
        per_wB.append(float(np.mean(B))); per_wD.append(float(np.mean(D)))
    out = {"theta": float(theta), "window": int(window), "n_windows": int(len(wt)),
           "n_windows_scored": int(len(per_w)), "n_resolvable": int(res.sum()),
           "coverage": float(np.mean(np.abs(x) >= theta)),
           "window_switches": int(np.sum(np.diff(wt) != 0)) if len(wt) > 1 else 0}
    out["mcr_window"] = float(np.mean(per_w)) if per_w else np.nan
    out["mcr_window_B"] = float(np.mean(per_wB)) if per_wB else np.nan
    out["mcr_window_D"] = float(np.mean(per_wD)) if per_wD else np.nan
    scored = wn > 0
    out.update({"share_window_target_lo": float(np.isclose(wt[scored], lo).mean()) if scored.any() else np.nan,
                "share_window_target_hi": float(np.isclose(wt[scored], hi).mean()) if scored.any() else np.nan})
    return out


# ------------------------------------------------------------------------------- floors, ceilings and the one sign
def normalise_metric(value: float, floor: float, ceiling: float, metric: str) -> float:
    """The ONLY place an orientation is applied (PREREG 2.2).

    Normalised so that 1.0 = the ceiling (the best attainable reference) and 0.0 = the floor (the worst reference),
    for BOTH orientations.  For a lower-is-better metric the ceiling is numerically the smaller value; the formula
    (value - floor) / (ceiling - floor) is the same in both cases because the roles, not the formula, carry the sign.
    """
    orientation(metric)          # raises on an unregistered metric before any arithmetic happens
    if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in (value, floor, ceiling)) or ceiling == floor:
        return float("nan")
    return float((value - floor) / (ceiling - floor))


def floors_and_ceilings_v21(baselines: Dict[str, Dict[str, float]], persona: str,
                            metrics: Optional[Sequence[str]] = None) -> Dict[str, Dict[str, float]]:
    """PREREG 2.2: ceiling = the mandate-conditional oracle, floor = the WORST of the trivial policies.

    'Worst' is resolved by the metric's own orientation through `HIGHER_IS_BETTER` -- the largest value for a
    lower-is-better metric, the smallest for a higher-is-better one -- so the sign lives in one place here too.
    """
    mco = baselines.get("mandate_conditional_oracle", {})
    pool = [baselines[k] for k in TRIVIAL_POLICIES if k in baselines]
    if metrics is None:
        # every key the baselines actually carry that has a registered orientation -- so the convention applies
        # to a v2 baseline dict (keys like `mcr_0.05`) and to a v2_1 one (keys like `mcr`) without a name map
        seen = []
        for b in [mco] + pool:
            for k in b:
                if k in seen:
                    continue
                try:
                    orientation(k)
                except KeyError:
                    continue
                seen.append(k)
        metrics = seen
    else:
        metrics = list(metrics)
    out: Dict[str, Dict[str, float]] = {}
    for m in metrics:
        hb = orientation(m)
        vals = [b.get(m, np.nan) for b in pool]
        vals = [v for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
        floor = (min(vals) if hb else max(vals)) if vals else np.nan
        ceiling = mco.get(m, np.nan)
        degenerate = (not np.isnan(floor)) and (not np.isnan(ceiling)) and \
                     ((ceiling <= floor) if hb else (ceiling >= floor))
        out[m] = {"floor": float(floor) if floor == floor else np.nan,
                  "ceiling": float(ceiling) if ceiling == ceiling else np.nan,
                  "degenerate": bool(degenerate), "n_trivial": len(vals),
                  "convention": "v2_1: ceiling = mandate_conditional_oracle, floor = worst trivial"}
    return out


# --------------------------------------------------------------------------------------- batch (many policies)
def regret_terms_batch(C: np.ndarray, x: np.ndarray, theta: float, persona: Optional[str],
                       prev_targets: np.ndarray, half_width: Optional[float] = None,
                       window: int = WINDOW_DAYS) -> Dict[str, np.ndarray]:
    """`regret_terms` + `regret_terms_window` for a (n_policies, n_days) matrix of cash shares that share one x.

    One construction, applied to many rows: the oracle target series is `oracle_target_series`, the terms are
    `decompose`, the window rule is `window_targets`'s.  `test_regret_terms_batch_matches_scalar` asserts it
    reproduces the per-run functions exactly, so the panel re-score and the per-run scoring cannot diverge.
    """
    C = np.atleast_2d(np.asarray(C, dtype=float))
    x = np.asarray(x, dtype=float)
    n_pol, n = C.shape
    c2, hw = centre_and_hw(persona)
    if half_width is not None:
        hw = float(half_width)
    lo, hi = c2 - hw, c2 + hw
    res = np.abs(x) >= theta
    nres = int(res.sum())
    out: Dict[str, np.ndarray] = {
        "theta": np.full(n_pol, float(theta)),
        "coverage": np.full(n_pol, float(res.mean())),
        "n_resolvable": np.full(n_pol, nres),
        "n_rows": np.full(n_pol, n),
    }
    # Each policy has its own seed target (its own day-1 share), so the target series differs by row -- but only
    # before the first resolvable step, and only through the CLIPPED seed, which takes few distinct values across
    # 44 policies.  Compute one series per distinct clipped seed and index rows into it.
    seeds = np.clip(np.asarray(prev_targets, dtype=float), lo, hi)
    uniq, inv = np.unique(seeds, return_inverse=True)
    base = np.stack([oracle_target_series(x, theta, lo, hi, float(u)) for u in uniq])
    tgt = base[inv]
    B = np.maximum(0.0, np.abs(C - c2) - hw)
    A = np.abs(C - tgt)
    D = A - B
    out["oracle_switches"] = (np.diff(tgt, axis=1) != 0).sum(axis=1).astype(float)
    if nres:
        out["mcr"] = A[:, res].mean(axis=1)
        out["mcr_B"] = B[:, res].mean(axis=1)
        out["mcr_D"] = D[:, res].mean(axis=1)
        out["share_target_lo"] = np.isclose(tgt[:, res], lo).mean(axis=1)
        out["share_target_hi"] = np.isclose(tgt[:, res], hi).mean(axis=1)
        out["share_agent_lo"] = np.isclose(C[:, res], lo).mean(axis=1)
        out["share_agent_hi"] = np.isclose(C[:, res], hi).mean(axis=1)
        out["share_agent_outside"] = (B[:, res] > 0).mean(axis=1)
    else:
        for k in ("mcr", "mcr_B", "mcr_D", "share_target_lo", "share_target_hi",
                  "share_agent_lo", "share_agent_hi", "share_agent_outside"):
            out[k] = np.full(n_pol, np.nan)
    # band-MAS over EVERY step (not only the resolvable ones): the mandate applies every day
    out["band_mas"] = B.mean(axis=1)

    # ---- per-window (REG-12 B): the modal daily target over the window's resolvable steps, ties -> earlier
    widx = np.arange(n) // window
    n_w = int(widx.max()) + 1 if n else 0
    wn = np.zeros(n_w, dtype=int)
    masks = []
    for w in range(n_w):
        m = (widx == w) & res
        masks.append(m); wn[w] = int(m.sum())
    wt_base = np.empty((len(uniq), n_w))
    for g in range(len(uniq)):
        last = float(uniq[g])
        for w in range(n_w):
            m = masks[w]
            if m.any():
                vals, counts = np.unique(base[g][m], return_counts=True)
                best = counts.max(); tied = vals[counts == best]
                if len(tied) == 1:
                    last = float(tied[0])
                else:
                    last = float(min(tied, key=lambda v: int(np.argmax((base[g] == v) & m))))
            wt_base[g, w] = last
    wt = wt_base[inv]
    scored_w = wn > 0
    if scored_w.any():
        mw = np.zeros((n_pol, n_w)); mwB = np.zeros((n_pol, n_w)); mwD = np.zeros((n_pol, n_w))
        for w in np.where(scored_w)[0]:
            m = masks[w]
            t_w = wt[:, [w]]
            Bw = np.maximum(0.0, np.abs(C[:, m] - c2) - hw)
            Aw = np.abs(C[:, m] - t_w)
            mw[:, w] = Aw.mean(axis=1); mwB[:, w] = Bw.mean(axis=1); mwD[:, w] = (Aw - Bw).mean(axis=1)
        out["mcr_window"] = mw[:, scored_w].mean(axis=1)
        out["mcr_window_B"] = mwB[:, scored_w].mean(axis=1)
        out["mcr_window_D"] = mwD[:, scored_w].mean(axis=1)
    else:
        for k in ("mcr_window", "mcr_window_B", "mcr_window_D"):
            out[k] = np.full(n_pol, np.nan)
    out["window_switches"] = (np.diff(wt, axis=1) != 0).sum(axis=1).astype(float) if n_w > 1 else np.zeros(n_pol)
    out["n_windows_scored"] = np.full(n_pol, int(scored_w.sum()))
    return out
