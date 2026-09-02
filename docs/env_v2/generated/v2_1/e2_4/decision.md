# E2.4 engine decision (PREREG_PHASE_2.md section 6)

Three candidates in one scaffolding (`tools/phase2/engines.py`): `ar1` = AR(1)+GJR-GARCH-t (REG-4 B, the simple one), `fw_v2` = the incumbent FW form driven by one GARCH innovation through the unit-mean weight (REG-4 A), `fw_plus` = FW's own two independent Gaussian demand noises with a stochastic fundamental (REG-4 C, Pruna et al. 2016). Rule (asymmetric, ties to the simpler model): a FW engine is adopted only if it is **accepted at (a)** and **beats `ar1` at (b) by more than one bootstrap sd** on the persistence-carrying moments.

## (a) SMM acceptance on the full sample

The two criteria are different tests and the column headings say so: the chi-square compares J with chi2_0.95(17 - p); Franke-Westerhoff's bootstrap p is the share of model replicates whose J falls below the DATA bootstrap's own 95th percentile, which carries no degrees-of-freedom penalty, is evaluated in-sample at that window's optimum, and has a yardstick that moves with the window length (`e2_3/weight_calibration.json`). On the full sample the weight matrix is well calibrated (the data bootstrap's J median is 14.2 against a chi-square(17) median of 16.3), so both criteria are meaningful there -- and both reject every engine.

| engine | free p | J | df | chi2 crit (5 %) | chi2 accept | FW bootstrap p | FW: not rejected at 5 %? |
|---|---|---|---|---|---|---|---|
| `ar1` | 3 | 80.4 | 14 | 23.7 | **no** | 0.000 (SE 0.000) | no |
| `fw_v2` | 7 | 29.2 | 10 | 18.3 | **no** | 0.005 (SE 0.005) | no |
| `fw_plus` | 8 | 110.3 | 9 | 16.9 | **no** | 0.000 (SE 0.000) | no |

## (b) Held-out prediction: fit 2000-2016, predict 2017-2024

| engine | D (8 persistence moments) | 95 % MC interval | D (all 17) | beats `ar1` by > 1 sd? |
|---|---|---|---|---|
| `ar1` | 1.512 | [1.335, 1.689] | 2.069 | - |
| `fw_v2` | 1.510 | [1.334, 1.687] | 2.069 | no |
| `fw_plus` | 1.488 | [1.286, 1.823] | 2.334 | no |

Per-moment held-out residuals in bootstrap-sd units (m_sim - m_test) / sd_boot:

| moment | `ar1` | `fw_v2` | `fw_plus` |
|---|---|---|---|
| rAC1 | +1.99 | +2.00 | +2.01 |
| invHill | -2.64 | -2.64 | -3.14 |
| vMean | -2.92 | -2.93 | -3.18 |
| vAC1 | -2.66 | -2.66 | -3.05 |
| vAC5 | -2.37 | -2.37 | -2.77 |
| vAC10 | -2.78 | -2.78 | -3.31 |
| vAC25 | -3.76 | -3.75 | -4.85 |
| vAC50 | -3.16 | -3.16 | -4.34 |
| vAC100 | -0.79 | -0.79 | -1.14 |
| VR20 | -5.33 | -5.33 | -4.80 |
| VR60 | -2.82 | -2.82 | -1.67 |
| VR120 | +0.04 | +0.03 | +0.79 |
| VR250 | -0.40 | -0.41 | +0.21 |
| VR500 | +1.18 | +1.17 | +1.71 |
| acfSMA20 | +0.81 | +0.80 | +1.20 |
| acfSMA60 | +0.87 | +0.87 | +1.04 |
| acfSMA120 | +0.19 | +0.19 | +0.29 |

Full-sample residuals at the optimum, in bootstrap-sd units:

| moment | `ar1` | `fw_v2` | `fw_plus` |
|---|---|---|---|
| rAC1 | +4.11 | +3.63 | +4.31 |
| invHill | -5.51 | -3.00 | -6.64 |
| vMean | -3.54 | -0.63 | -4.26 |
| vAC1 | -6.26 | -2.67 | -7.32 |
| vAC5 | -5.22 | -2.57 | -6.21 |
| vAC10 | -5.09 | -2.64 | -6.08 |
| vAC25 | -4.71 | -2.25 | -5.65 |
| vAC50 | -4.80 | -2.44 | -5.57 |
| vAC100 | -3.79 | -2.10 | -4.13 |
| VR20 | +0.56 | +0.17 | +0.75 |
| VR60 | -1.76 | -1.29 | +0.09 |
| VR120 | -1.32 | -1.73 | +0.00 |
| VR250 | -0.74 | -1.99 | +0.44 |
| VR500 | +0.01 | -1.63 | +0.88 |
| acfSMA20 | -1.39 | -1.59 | -0.42 |
| acfSMA60 | -0.53 | -1.54 | -0.01 |
| acfSMA120 | +0.19 | -1.12 | +0.41 |

## Decision

**Adopted: `ar1`** — no FW engine met both legs of the asymmetric rule; ties go to the simpler model.

| engine | accepted at (a)? | D | needed at or below |
|---|---|---|---|
| `fw_v2` | False (chi2 False) | 1.510 | 0.512 |
| `fw_plus` | False (chi2 False) | 1.488 | 0.512 |
