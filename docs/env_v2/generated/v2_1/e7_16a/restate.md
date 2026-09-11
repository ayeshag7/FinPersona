# 16A re-stated under the Phase-7 scorings (theta = 0.05) — a reported consequence, beside the Phase-6 verdict

**The Phase-6 verdict stands** (`e6_16a/16A.json`, DECISION_LOG P6-11): G1 FAIL, G2 FAIL, G3 PASS, G4a FAIL, G4b FAIL. Nothing below replaces it; the decomposition is reported because it says *where* each failure sits.

| statistic the gate is read on | G1 (oracle < observables < trivial, 4 of 4) | G2 (rule above the observables oracle, ≥ 3 of 4) | G4a (observables oracle beats price-only, 4 of 4) |
|---|---|---|---|
| MCR — the Phase-6 statistic | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** |
| B, the band-violation term | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** |
| D, the directional term | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** |
| MCR per 25-day window (REG-12 B) | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** |

## G3 — the oracle's target switches per run

| reading | flat | bull_trap | crash | sustained_bull | verdict |
|---|---|---|---|---|---|
| daily | median 2, share 0.76 | median 2, share 0.61 | median 4, share 0.90 | median 2, share 0.77 | **PASS** |
| per_window | median 2, share 0.60 | median 1, share 0.39 | median 2, share 0.63 | median 2, share 0.57 | **FAIL** |

The best trivial policy per scenario, which is what G1's third leg is measured against:

| statistic | flat | bull_trap | crash | sustained_bull |
|---|---|---|---|---|
| MCR — the Phase-6 statistic | band_hi | band_hi | band_lo | band_hi |
| B, the band-violation term | always_hold | band_lo | band_lo | band_hi |
| D, the directional term | band_hi | band_hi | band_lo | band_hi |
| MCR per 25-day window (REG-12 B) | band_hi | band_hi | band_lo | band_hi |

