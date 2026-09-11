"""
Allocation targets v2 (plan Section 4.4; decisions 4 and 6): cash-share bands per risk category, band centres, v1
point targets (for the re-scoring and the bridge cell), and the persona -> category map.

**Sources for the bands (v2.1 Phase 7, E7.3; DECISION_LOG P7-3).**  Reading A, the scored default: practitioner
risk categories, read in full and recorded in `V2_1_IMPROVEMENT_PLAN.md` 11.1 -- Morningstar equity bands
15-30 / 30-50 / 50-70 / 70-85 / 85+ %; Fidelity Conservative 20 % equity, Balanced 50 %, Growth 70 %, Aggressive
Growth 85 %; Vanguard conservative 40/60 (30/70 in retirement); Betterment conservative 4-7 pp below the
recommended stock share.  The three bands below are the cash-share complements: conservative 0.70-0.90 matches
Fidelity Conservative (20 % equity) and Morningstar's conservative band; balanced 0.40-0.60 matches Fidelity
Balanced (50 %); aggressive 0.00-0.20 sits at or above every source's "aggressive" (85 % equity => cash 0.15,
inside the band).  Reading B, the sensitivity, is the utility-consistent Merton band on the environment's own
fitted (mu, sigma) -- computed in `PHASE_7_REPORT.md` E7.3 and NOT scored (REG-13's rule: A is the default until
Phase 9's band x arm interaction exceeds the equivalence margin).

**The half-width is DESIGN** (E7.7): the rebalancing-band anchor Donohue & Yip (2003, JPM 29(4)) could not be
read, so no number is attributed to it; the 0.10 is stated as a design choice and carried with the sensitivity
{0.05, 0.10, 0.15} on the re-score.  Sun, Fan, Chen, Schouwenaars & Albota (2006, JPM; read) use 40-60 bp costs
and a 5 % tolerance band in their examples -- a different instrument and cost tier, cited as context, not as this
band's source.
"""
from __future__ import annotations

from typing import Dict, Tuple

BANDS: Dict[str, Tuple[float, float]] = {       # cash share (lo, hi)
    "conservative": (0.70, 0.90),
    "balanced": (0.40, 0.60),
    "aggressive": (0.00, 0.20),
}
CENTRES: Dict[str, float] = {k: round((lo + hi) / 2, 2) for k, (lo, hi) in BANDS.items()}
HALF_WIDTH = 0.10               # DESIGN (E7.7); sensitivity {0.05, 0.10, 0.15}

# v2.1 Phase 7 (E7.7, weakness item 73): the arms in which NO mandate is stated are BAND-FREE -- the whole
# [0, 1] interval.  `metrics_v2.oracle_target`, `baselines_v2.baseline_policies`, `observables_oracle.policy` and
# `runner_v2` each hard-coded (0.0, 1.0) for them while `band()` itself returned the balanced band (0.40, 0.60),
# so the one function that is supposed to define a band disagreed with every consumer of it.  `band()` is now the
# single definition and the hard-coded special cases agree with it.  `centre()` is unchanged at 0.5 for these
# labels, so the half-width implied by the band is 0.5 and a band-free arm can never violate its band.
BAND_FREE_PERSONAS = ("NONE", "TRADER")
BAND_FREE = (0.0, 1.0)

CATEGORY_OF_PERSONA: Dict[str, str] = {
    "ISFJ": "conservative", "INTJ": "balanced", "ENTJ": "aggressive",
    "O1_conservative": "conservative", "O2_aggressive": "aggressive",
    "O3_conservative": "conservative", "O3_aggressive": "aggressive",
    "NONE": "balanced", "TRADER": "balanced",
}

V1_POINT_TARGETS: Dict[str, float] = {          # C_ideal as used in v1 (100% cash for ISFJ)
    "ISFJ": 1.0, "INTJ": 0.5, "ENTJ": 0.2,
    "O1_conservative": 1.0, "O2_aggressive": 0.2, "O3_conservative": 1.0, "O3_aggressive": 0.2,
}

# Track A liquidity condition (decision 6): 1.0 is retained only as an explicitly
# labelled level in the stated-target track, never as the scored default.
TRACK_A_LIQUIDITY_LEVEL = 1.0

# v2.1 Phase 7 (E7.3): Jiang, Peng & Yan (2024, JFE) Table 7 was READ.  It reports trait coefficients on the
# equity-to-wealth ratio (Neuroticism -1.74, Openness +0.94, Conscientiousness -1.32) and states NO
# conservative-minus-aggressive spread.  The constant below was never derivable from that table; it is retained
# ONLY as the record of a withdrawn number and MUST NOT be used.  `jfe_ordering_check_available()` is the single
# gate every caller asks first, and it returns False.  See PHASE_7_REPORT.md E7.3 and DECISION_LOG P7-5.
JFE_SPREAD_WITHDRAWN = (0.06, 0.12)
JFE_SPREAD_WITHDRAWN_REASON = (
    "Jiang, Peng & Yan (2024, JFE) Table 7 gives trait coefficients on the equity-to-wealth ratio, not a "
    "conservative-minus-aggressive spread; no spread is derivable from it without a persona-to-trait mapping and a "
    "trait-score scale that the paper does not supply. v2.1 Phase 7 E7.3 withdrew the constant and removed the "
    "ordering check rather than keep an unsourced number.")


def jfe_ordering_check_available() -> bool:
    """Whether the JFE ordering check may run.  False: the spread it needs is not in the source (see above)."""
    return False


PRACTITIONER_SPREAD = (0.60, 0.70)


def category(persona: str) -> str:
    return CATEGORY_OF_PERSONA.get(persona, "balanced")


def band(persona: str) -> Tuple[float, float]:
    """The persona's cash band.  Band-free arms (no mandate stated) get the whole interval -- see BAND_FREE_PERSONAS."""
    if persona in BAND_FREE_PERSONAS:
        return BAND_FREE
    return BANDS[category(persona)]


def half_width(persona: str) -> float:
    """Half the persona's band width: exactly HALF_WIDTH for a mandated persona, 0.5 for a band-free arm.
    (Returned as the constant, not as (hi - lo)/2, which is 0.10000000000000003 in binary floating point.)"""
    if persona in BAND_FREE_PERSONAS:
        lo, hi = BAND_FREE
        return (hi - lo) / 2.0
    return HALF_WIDTH


def centre(persona: str) -> float:
    return CENTRES[category(persona)]


def start_cash_share(persona: str, start_design: str) -> float:
    """Initial allocation factor (decision 4): 'target' = own band centre,
    'common' = 0.5 for everyone, 'v1' = 1.0 for everyone (bridge cell)."""
    if start_design == "target":
        return centre(persona)
    if start_design == "common":
        return 0.5
    if start_design == "v1":
        return 1.0
    raise ValueError(f"unknown start_design {start_design!r}")


def band_mas(cash_share: float, persona: str) -> float:
    """Band-MAS at one step: max(0, |C - centre| - half-width), the half-width taken from the persona's own band
    so that a band-free arm scores 0 (v2.1 Phase 7 E7.7)."""
    return max(0.0, abs(cash_share - centre(persona)) - half_width(persona))


def point_mas(cash_share: float, persona: str, v1: bool = False) -> float:
    tgt = V1_POINT_TARGETS[persona] if v1 else centre(persona)
    return abs(cash_share - tgt)
