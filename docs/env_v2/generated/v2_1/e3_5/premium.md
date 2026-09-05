# E3.5 IV premium fitted on the five CBOE single-stock VIX histories (PREREG_PHASE_3.md section 7.1)

Filter: GJR(0.027, 0.058, 0.932), per-name omega from the sample unconditional variance; y = log(IV/100) - log sqrt(252 fc); 17,570 pooled days, 2011-01-07..2024-12-31.

| family | CV MSE (mean over held-out names) | SE |
|---|---|---|
| M0: const | 0.04899 | 0.00862 **adopted** |
| M1: a + b log l | 0.04862 | 0.00762 |
| M2: a + b log l + c (log l)^2 | 0.04838 | 0.00754 (best raw) |

Pooled coefficients (M0): [-0.0224]; median premium -0.022; corr(log l, y) = -0.201.
eps: AR(1) rho median 0.926 (range [0.9231, 0.9308]), innovation sd median 0.0827 (range [0.0579, 0.0981]); adopt AR(1) = True.
Pooled minimum IV 5.13 (the floor-replacement anchor).

| name | n | coef | rho_eps | sd_eps | mean IV | min IV | median premium |
|---|---|---|---|---|---|---|---|
| AAPL | 3514 | [-0.052] | 0.9274 | 0.0685 | 29.67 | 12.52 | -0.044 |
| AMZN | 3514 | [-0.096] | 0.9308 | 0.0827 | 33.95 | 5.13 | -0.097 |
| GOOG | 3514 | [0.007] | 0.9243 | 0.0888 | 27.54 | 9.21 | +0.015 |
| GS | 3514 | [-0.012] | 0.9263 | 0.0579 | 29.3 | 16.16 | -0.014 |
| IBM | 3514 | [0.041] | 0.9231 | 0.0981 | 23.6 | 13.23 | +0.050 |

five mega-caps (REG-15 / plan section 3): the premium of the median S&P name may differ; stated wherever the fit is quoted.

Literature beside (not tolerances): Carr & Wu 2009 (RFS, read by the plan's pass): individual-stock log VRPs negative for 21 of 35 names; Christensen & Prabhala 1998 (JFE): log RV on log IV slope 0.76, R^2 39 % (S&P 100, monthly); Goyal & Saretto 2009 (JFE): sorts on log(RV/IV).
