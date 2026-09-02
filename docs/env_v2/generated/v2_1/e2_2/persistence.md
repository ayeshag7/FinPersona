# E2.2 firm-level persistence and REG-5's disagreement rule (PREREG_PHASE_2.md section 5)

Usability is Phase 1's full-scale recovery study (32 cells, 200/50 replications; `e1_2/recovery.md`), not repeated here:

| estimator | usable? | why |
|---|---|---|
| A | no | median relative error 0.11 -> 20.0 as h grows and interval coverage 0.00-0.01 in every cell |
| B | no | h-hat ~ 36-47 d whatever the truth, and the same on a panel with x == 0: it measures the EDGAR V-hat error, not x |
| C | **yes** | h <= 150 d (median relative error 0.03-0.16); unusable at h >= 250 |

## Estimator A (variance ratios) -- pooled fits per Phase-1 sub-period

| period | n | h (d) | 95 % CI (stocks) | 95 % CI (blocks) | sigma_V | s_x | J |
|---|---|---|---|---|---|---|---|
| full | 417 | 4.9 | [4.2, 5.6] | [0.9, 13.3] | 0.02048 | 0.024 | 80.0 |
| 2000-07 | 417 | 7.7 | [6.5, 9.0] | [3.7, 19.4] | 0.02063 | 0.034 | 17.1 |
| 2008-12 | 417 | 0.8 | [0.5, 1.0] | [0.0, 8.9] | 0.02585 | 0.012 | 38.1 |
| 2013-19 | 417 | 16.7 | [13.9, 20.0] | [8.5, 65.1] | 0.01390 | 0.032 | 3.9 |
| 2020-24 | 417 | 13.8 | [11.0, 17.0] | [2.3, 42.6] | 0.01932 | 0.050 | 94.7 |

Cross-section (descriptive; A is not usable): median h = 6.4 d, P25-P75 2.4-21.7 d over n = 417 stocks; 12% of stocks fit above 500 d. Weights: 1/Var of each moment across stocks.

## Estimator B (log(P/V-hat) AR(1), Andrews median-unbiased) -- 2009-06-30..2024-12-31

| variant | n | median h (d) | 95 % CI | P25-P75 | median h (OLS) | share at grid top |
|---|---|---|---|---|---|---|
| EarningsPerShareBasic|sector | 367 | 256 | [223, 277] | 152-626 | 167 | 0.15 |
| EarningsPerShareBasic|market | 367 | 290 | [268, 350] | 175-756 | 187 | 0.19 |
| EarningsPerShareDiluted|sector | 366 | 259 | [227, 286] | 155-596 | 168 | 0.14 |
| EarningsPerShareDiluted|market | 366 | 294 | [266, 353] | 177-780 | 186 | 0.18 |

B has no sub-period breakdown: its monthly panel starts in 2009-06 and a sub-period would leave fewer than the 60 months its own rule requires. Stated as a gap, not filled.

## Estimator C (SMM, this phase's E2.3) -- pooled fits per period

| engine | period | half-life (d) | kind | chartist share | sd(x) | J | df | chi2 accept | FW bootstrap p | FW: not rejected? |
|---|---|---|---|---|---|---|---|---|---|---|
| `ar1` | full | 7.5 | AR(1) half-life from rho = 2^(-1/h) | - | 0.023 | 80.4 | 14 | no | 0.000 | no |
| `ar1` | p1 | 13.1 | AR(1) half-life from rho = 2^(-1/h) | - | 0.049 | 100.1 | 14 | no | 0.000 | no |
| `ar1` | p2 | 8.9 | AR(1) half-life from rho = 2^(-1/h) | - | 0.028 | 74.3 | 14 | no | 0.060 | **yes** |
| `ar1` | p3 | 9.2 | AR(1) half-life from rho = 2^(-1/h) | - | 0.026 | 44.7 | 14 | no | 1.000 | **yes** |
| `ar1` | train | 5.2 | AR(1) half-life from rho = 2^(-1/h) | - | 0.017 | 70.7 | 14 | no | - | not run |
| `fw_plus` | full | 5.8 | pull-rate ln2/(mu n_bar phi) | 0.235 | 0.015 | 110.3 | 9 | no | 0.000 | no |
| `fw_plus` | train | 5.0 | pull-rate ln2/(mu n_bar phi) | 0.418 | 0.014 | 91.7 | 9 | no | - | not run |
| `fw_v2` | full | 2.4 | pull-rate ln2/(mu n_bar phi) | 0.043 | 0.080 | 29.2 | 10 | no | 0.005 | no |
| `fw_v2` | train | 5.5 | pull-rate ln2/(mu n_bar phi) | 0.000 | 0.017 | 70.8 | 10 | no | - | not run |

## REG-5's rule applied

Usable: ['C'].

Only C survived usability, so the rule reduces to 'adopt the only usable estimator'. It is therefore NOT evidence that C is right on the real panel; E2.3's acceptance test is what can reject C's model, and its verdict is reported beside.

Qualifications carried with the adoption:
- the recovery panels come from C's own model (favourable to C by construction)
- Phase 1's data-side J = 66.6 already indicated misspecification on the real panel

## The levels E2.6 sweeps

Fitted range [2.353105420106939, 23.6074232208472]; plan levels [30, 60, 120, 250, 500]; **swept levels [5, 10, 15, 30, 60, 120, 250, 500]**. Rule: the union of C's fitted interval for the adopted engine and the plan's own sweep levels; the nearest decade below is added when the fit falls below 30 d.
