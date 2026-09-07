# E5.2 the residual clock in `days_since_eps_announcement`

200 flat seeds (326000+), quarter grid randomised per seed in both arms; the classifier and its in-time shuffle null are E4.7's, unchanged. P4-29 measured 0.3958 vs null 0.3625 at n = 150 under the v2 lag U(25, 35).

| arm | full-window accuracy | null p95 | clock | interior-days accuracy | null p95 | clock | full excess over 6 splits (pp) | interior excess over 6 splits (pp) |
|---|---|---|---|---|---|---|---|---|
| v2_lags_randomised_grid | 0.3844 | 0.3640 | True | 0.4285 | 0.4296 | False | +0.78 +/- 1.23 | -1.56 +/- 1.18 |
| fit_lags_randomised_grid | 0.3966 | 0.3636 | True | 0.4445 | 0.4299 | True | +1.47 +/- 1.63 | +0.09 +/- 1.12 |
