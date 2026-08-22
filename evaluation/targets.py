"""
Allocation targets v2 (plan Section 4.4; decisions 4 and 6): stipulated cash-share
bands per risk category, band centres, v1 point targets (for the re-scoring and
the bridge cell), and the persona -> category map.  JFE (Jiang, Peng & Yan 2024)
spreads are kept as a sensitivity/ordering check, not as point targets.
"""
from __future__ import annotations

from typing import Dict, Tuple

BANDS: Dict[str, Tuple[float, float]] = {       # cash share (lo, hi)
    "conservative": (0.70, 0.90),
    "balanced": (0.40, 0.60),
    "aggressive": (0.00, 0.20),
}
CENTRES: Dict[str, float] = {k: round((lo + hi) / 2, 2) for k, (lo, hi) in BANDS.items()}
HALF_WIDTH = 0.10

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

JFE_SPREAD = (0.06, 0.12)           # conservative-minus-aggressive cash spread implied by JFE Table 7
PRACTITIONER_SPREAD = (0.60, 0.70)


def category(persona: str) -> str:
    return CATEGORY_OF_PERSONA.get(persona, "balanced")


def band(persona: str) -> Tuple[float, float]:
    return BANDS[category(persona)]


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
    """Band-MAS at one step: max(0, |C - centre| - half-width)."""
    return max(0.0, abs(cash_share - centre(persona)) - HALF_WIDTH)


def point_mas(cash_share: float, persona: str, v1: bool = False) -> float:
    tgt = V1_POINT_TARGETS[persona] if v1 else centre(persona)
    return abs(cash_share - tgt)
