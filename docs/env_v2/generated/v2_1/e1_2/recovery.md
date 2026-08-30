# E1.2 recovery study (REG-5; PREREG_PHASE_1.md section 4.4)

Synthetic panels 100 stocks x 6300 days from the calm simulator; A and B at 200 replications per cell, C at 50; V_hat noise sd 0.569 (FIT), persistence in {0, 0.9}/quarter (DESIGN bracket). Usable = median relative error < 0.20 and coverage >= 0.90.

| h | sigma_V | A: med rel err / RMSE / coverage / median h_hat | usable | B (white m): err / cov / h_hat | usable | B (rho_m 0.9): err / cov / h_hat | usable | C: err / RMSE / h_hat | usable |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 0.006 | 0.11 / 0.11 / 0.01 / 6 | False | 6.29 / 0.00 / 36 | False | 77.24 / 0.00 / 391 | False | 0.03 / 0.04 / 5 | True |
| 5 | 0.012 | 0.26 / 0.27 / 0.00 / 6 | False | 6.29 / 0.00 / 36 | False | 76.21 / 0.00 / 386 | False | 0.05 / 0.07 / 5 | True |
| 10 | 0.006 | 0.19 / 0.20 / 0.00 / 12 | False | 2.64 / 0.00 / 36 | False | 35.42 / 0.00 / 364 | False | 0.03 / 0.05 / 10 | True |
| 10 | 0.012 | 0.46 / 0.47 / 0.00 / 15 | False | 2.63 / 0.00 / 36 | False | 35.37 / 0.00 / 364 | False | 0.06 / 0.09 / 10 | True |
| 30 | 0.006 | 0.31 / 0.32 / 0.00 / 39 | False | 0.22 / 0.00 / 37 | False | 10.43 / 0.00 / 343 | False | 0.08 / 0.11 / 29 | True |
| 30 | 0.012 | 0.72 / 0.75 / 0.00 / 52 | False | 0.22 / 0.00 / 37 | False | 10.53 / 0.00 / 346 | False | 0.10 / 0.14 / 29 | True |
| 60 | 0.006 | 0.58 / 0.60 / 0.00 / 95 | False | 0.38 / 0.00 / 37 | False | 4.80 / 0.00 / 348 | False | 0.14 / 0.20 / 57 | True |
| 60 | 0.012 | 1.37 / 1.55 / 0.00 / 142 | False | 0.38 / 0.00 / 37 | False | 4.74 / 0.00 / 344 | False | 0.20 / 0.25 / 56 | False |
| 120 | 0.006 | 0.81 / 0.82 / 0.00 / 217 | False | 0.68 / 0.00 / 39 | False | 2.01 / 0.00 / 361 | False | 0.15 / 0.22 / 107 | True |
| 120 | 0.012 | 2.13 / 2.23 / 0.00 / 375 | False | 0.68 / 0.00 / 39 | False | 2.03 / 0.00 / 364 | False | 0.20 / 0.30 / 104 | True |
| 150 | 0.006 | 0.92 / 0.96 / 0.00 / 287 | False | 0.74 / 0.00 / 40 | False | 1.46 / 0.00 / 370 | False | 0.16 / 0.29 / 127 | True |
| 150 | 0.012 | 2.39 / 2.57 / 0.00 / 508 | False | 0.74 / 0.00 / 40 | False | 1.49 / 0.00 / 373 | False | 0.18 / 0.30 / 128 | True |
| 250 | 0.006 | 1.52 / 1.88 / 0.00 / 631 | False | 0.83 / 0.00 / 42 | False | 0.62 / 0.00 / 404 | False | 0.22 / 0.37 / 202 | False |
| 250 | 0.012 | 4.28 / 564227.22 / 0.00 / 1320 | False | 0.83 / 0.00 / 42 | False | 0.60 / 0.00 / 401 | False | 0.32 / 0.49 / 176 | False |
| 500 | 0.006 | 20.00 / 13127026.10 / 0.01 / 10502 | False | 0.91 / 0.00 / 47 | False | 0.06 / 0.89 / 475 | False | 0.43 / 180481365375979520.00 / 361 | False |
| 500 | 0.012 | 2616208.27 / 156809884.41 / 0.00 / 1308104634 | False | 0.91 / 0.00 / 47 | False | 0.07 / 0.89 / 469 | False | 0.58 / 4.45 / 357 | False |

Estimator C on set A: sigma_V 0.01957 [0.01892, 0.02036], s_x 0.129 [0.125, 0.135], h 5 d [4, 5], J 66.62 (30 bootstrap refits; diagonal 1/Var (200 stock resamples); 20 paths x 5000 days, CRN, burn 500).
