# E4.6 - event dynamics: four formulations (REG-8)

`python -m tools.phase4.e4_6_dynamics` - PREREG_PHASE_4.md section 8.

1000 crash and 1000 bull seeds per formulation. All four run; none was skipped.

Panel box (E4.1 dd30_fast): depth [-0.538, -0.312], duration [22, 113].
Panel self-coverage 0.643 (n = 642), so the registered rejection ceiling is **0.357**.

| formulation | script share | coverage | 95 % CI | verdict | rejection crash | rejection bull | rise | depth |
|---|---|---|---|---|---|---|---|---|
| A_lam0.02 | 0.047 | 0.474 | [0.439, 0.509] | **FAIL** | 0.061 | 0.113 | 60.0 | -0.523 |
| A_lam0.05 | 0.062 | 0.480 | [0.445, 0.515] | **FAIL** | 0.044 | 0.113 | 59.0 | -0.522 |
| A_lam0.1 | 0.080 | 0.520 | [0.485, 0.555] | **FAIL** | 0.027 | 0.113 | 59.0 | -0.514 |
| A_lam0.25 | 0.130 | 0.562 | [0.527, 0.597] | **FAIL** | 0.012 | 0.113 | 58.0 | -0.509 |
| B_shifted_pstar | 0.039 | 0.521 | [0.486, 0.556] | **FAIL** | 0.126 | 0.113 | 60.0 | -0.501 |
| C_scripted_no_feedback | 0.014 | 0.462 | [0.427, 0.496] | **FAIL** | 0.086 | 0.113 | 56.0 | -0.528 |
| D_unscripted_regime | 0.030 | 0.323 | [0.288, 0.359] | **FAIL** | 0.048 | 0.113 | 57.0 | -0.558 |

## Decision

- rule: adopt the LOWEST script share among formulations with coverage >= 0.7 (DESIGN margin) and rejection below the ceiling 0.357
- eligible: **none**
- undecided at this n: **none**
- **STOP FOR D5 - no formulation qualifies**

- phi_regime FIT from the panel: {"front_load_p50": 0.2716707068805604, "panic_len_p50": 39.0, "rec60_p50": 0.569144168907215, "formula": "phi = 1 - (1 - front_load)^(3 / phase_length)", "source": "e4_1/episodes4.json panel_families.dd30_fast"}
