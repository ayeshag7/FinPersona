# E1.2 estimator A: variance-ratio decomposition (set A; PREREG_PHASE_1.md section 4.1)

Set A = 417 flag-free full-history names, 2000-01-04 .. 2024-12-31, daily log returns of Adj Close. Pooled curve = cross-sectional mean of the per-stock Lo-MacKinlay VR(k); weights = 1/Var of the pooled moment under the stock bootstrap. Intervals: (i) stock-cluster bootstrap; (ii) joint stock x 250-day moving-block bootstrap. Survivor caveat: set A has no delistings (REG-15).

| period | n | sigma_V/day | 95 % CI (stocks) | 95 % CI (blocks) | s_x | CI (stocks) | CI (blocks) | h (days) | CI (stocks) | CI (blocks) | RW share of daily var | J |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | 417 | 0.02048 | [0.01973, 0.02129] | [0.01675, 0.02430] | 0.024 | [0.022, 0.026] | [0.010, 0.042] | 5 | [4, 6] | [1, 13] | 0.74 | 80.02 |
| 2000-07 | 417 | 0.02063 | [0.01956, 0.02167] | [0.01509, 0.02322] | 0.034 | [0.030, 0.037] | [0.018, 0.060] | 8 | [6, 9] | [4, 19] | 0.68 | 17.09 |
| 2008-12 | 417 | 0.02585 | [0.02477, 0.02703] | [0.01466, 0.03369] | 0.012 | [0.011, 0.014] | [0.008, 0.047] | 1 | [1, 1] | [0, 9] | 0.79 | 38.08 |
| 2013-19 | 417 | 0.01390 | [0.01312, 0.01457] | [0.00935, 0.01489] | 0.032 | [0.029, 0.036] | [0.020, 0.102] | 17 | [14, 20] | [9, 65] | 0.70 | 3.90 |
| 2020-24 | 417 | 0.01932 | [0.01838, 0.02021] | [0.01125, 0.02280] | 0.050 | [0.043, 0.058] | [0.012, 0.107] | 14 | [11, 17] | [2, 43] | 0.61 | 94.70 |

Pooled moments (full sample) with stock-bootstrap intervals and the fitted model's values:

| moment | pooled | 95 % CI | model | per-stock P25-P75 |
|---|---|---|---|---|
| var1 | 0.00056821 | [0.00053863, 0.00059831] | 0.00056821 | - |
| VR5 | 0.92516 | [0.91825, 0.93155] | 0.93948 | 0.877-0.967 |
| VR10 | 0.8838 | [0.87421, 0.89218] | 0.88849 | 0.816-0.938 |
| VR20 | 0.86532 | [0.85358, 0.87644] | 0.83167 | 0.781-0.931 |
| VR60 | 0.78462 | [0.76699, 0.8003] | 0.77144 | 0.665-0.875 |
| VR120 | 0.76099 | [0.73987, 0.78186] | 0.75493 | 0.605-0.874 |
| VR250 | 0.72393 | [0.69902, 0.74765] | 0.74634 | 0.540-0.848 |
| VR500 | 0.67178 | [0.64338, 0.69731] | 0.74237 | 0.460-0.810 |
