"""
Separate, named random streams per generator component (v2 plan 2.1 block 10).

Every component draws from its own numpy Generator, derived from
SeedSequence(seed, spawn_key=(attempt, asset, component_index)).  Consequences:
  * adding a new component (append to COMPONENTS) never changes an old path;
  * rejection-sampling attempt k uses fresh streams for every component;
  * asset i in a multi-asset run has its own streams; the common fundamental
    factor has asset index -1 (shared);
  * nothing touches numpy's global RNG, so concurrent generation in threads
    (the v1 defect found in E0) cannot interleave draws.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

# Fixed registry. APPEND ONLY -- never reorder or remove.
COMPONENTS = [
    "fundamental",        # 0  idiosyncratic V shocks
    "fundamental_common", # 1  common factor in V shocks (asset index -1)
    "garch",              # 2  standardised t innovations of the x process
    "schedule",           # 3  phase lengths, event parameters, jitter
    "hazard",             # 4  bubble-top uniforms
    "jump",               # 5  rare jumps
    "sentiment",          # 6  E2
    "eps",                # 7  E2 earnings noise and announcement lags
    "analyst",            # 8  E2 analyst fair-value error
    "volume",             # 9  E2
    "init_alloc",         # 10 harness: initial allocation draws
    "field_order",        # 11 harness: field-order randomisation
    "multiple",           # 12 E2 hidden valuation multiple k
    "dividend",           # 13 E2
    "announce",           # 14 v2.1 Phase 1: earnings-announcement lags (shared by the V jump and the EPS field)
    "start_price",        # 15 v2.1 Phase 1: start-price level (mechanism A) / render scale (mechanism C)
    "init_state",         # 16 v2.1 Phase 1: stored-state burn-in draw (E1.5 option B)
    "regime",             # 17 v2.1 Phase 3: two-regime switching-variance draws (E3.4 mechanism C)
    "iv",                 # 18 v2.1 Phase 3: the IV noise eps (E3.5; AR(1), day-indexed, past-only)
]
_INDEX = {name: i for i, name in enumerate(COMPONENTS)}


class Streams:
    """Named Generators for one (seed, attempt)."""

    def __init__(self, seed: int, attempt: int = 0):
        self.seed = int(seed)
        self.attempt = int(attempt)
        self._cache: Dict[tuple, np.random.Generator] = {}

    def get(self, component: str, asset: int = 0) -> np.random.Generator:
        if component not in _INDEX:
            raise KeyError(f"unknown RNG component {component!r}; append it to rng.COMPONENTS")
        key = (component, int(asset))
        if key not in self._cache:
            ss = np.random.SeedSequence(self.seed, spawn_key=(self.attempt, int(asset) + 1, _INDEX[component]))
            self._cache[key] = np.random.default_rng(ss)
        return self._cache[key]

    def __repr__(self) -> str:
        return f"Streams(seed={self.seed}, attempt={self.attempt})"


def standardised_t(rng: np.random.Generator, df: float, size) -> np.ndarray:
    """Student-t(df) scaled to unit variance (df > 2)."""
    z = rng.standard_t(df, size=size)
    return z / np.sqrt(df / (df - 2.0))
