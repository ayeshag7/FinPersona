# E5.1 the trailing P/E cross-section and persistence (PREREG_PHASE_5.md section 4.1)

Phase 1 monthly_pe_panel (EDGAR basic EPS x Yahoo month-end close), set A, 2009-06..2024-12; 411 stocks, 61843 stock-months with EPS_ttm > 0 of 67217 with a known trailing EPS. Pooled quantiles carry a 1000-resample stock bootstrap. set A is survivor-only (REG-15): loss-makers that delisted are absent, so the n/m share and the P/E tails are understated relative to the full universe.

| quantile | trailing P/E | 95 % CI |
|---|---|---|
| p5 | 3.86 | [3.12, 4.63] |
| p10 | 5.77 | [5.19, 6.34] |
| p25 | 9.23 | [8.68, 9.83] |
| p50 | 15.12 | [14.34, 16.06] |
| p75 | 24.42 | [23.10, 25.85] |
| p90 | 39.98 | [36.87, 43.73] |
| p95 | 58.51 | [53.09, 65.81] |
| p99 | 191.55 | [154.75, 244.68] |

n/m share (EPS_ttm <= 0 among known): **0.0800** (se 0.0010, n = 67217); Phase 1 reported 0.195 on the same set.

| year | P10 | P25 | P50 | P75 | P90 | n | n/m share |
|---|---|---|---|---|---|---|---|
| 2009 | 1.2 | 1.3 | 5.1 | 5.3 | 19.0 | 8 | 0.273 |
| 2010 | 3.9 | 6.2 | 9.5 | 14.5 | 23.9 | 1660 | 0.067 |
| 2011 | 3.7 | 6.1 | 9.5 | 14.8 | 23.7 | 3637 | 0.052 |
| 2012 | 4.0 | 6.6 | 10.2 | 16.5 | 27.5 | 4273 | 0.054 |
| 2013 | 5.5 | 8.1 | 12.5 | 19.6 | 31.1 | 4288 | 0.063 |
| 2014 | 6.2 | 9.1 | 13.8 | 21.2 | 32.3 | 4489 | 0.033 |
| 2015 | 6.1 | 9.3 | 14.0 | 21.1 | 31.7 | 4393 | 0.065 |
| 2016 | 6.3 | 10.0 | 15.2 | 22.8 | 33.9 | 4261 | 0.100 |
| 2017 | 7.8 | 11.7 | 16.8 | 23.7 | 37.2 | 4323 | 0.086 |
| 2018 | 6.1 | 10.2 | 16.4 | 27.7 | 53.4 | 4324 | 0.087 |
| 2019 | 6.6 | 9.8 | 16.0 | 25.8 | 41.7 | 4450 | 0.067 |
| 2020 | 6.4 | 9.9 | 16.8 | 27.5 | 46.6 | 4213 | 0.122 |
| 2021 | 7.9 | 12.4 | 20.8 | 33.8 | 54.0 | 4198 | 0.126 |
| 2022 | 5.6 | 9.7 | 17.2 | 27.7 | 40.6 | 4536 | 0.062 |
| 2023 | 6.3 | 10.9 | 18.1 | 27.7 | 42.8 | 4425 | 0.091 |
| 2024 | 8.6 | 13.1 | 20.9 | 32.1 | 51.4 | 4365 | 0.106 |

Quarterly AR(1) of log P/E (per stock, >= 20 quarters, n = 367): median rho_q **0.8076** [0.7814, 0.8269], IQR 0.694-0.894; daily equivalent rho_d = rho_q^(1/63) = 0.99661.

Dispersion of log P/E: pooled sd 1.0963; between-stock sd 0.8044; within-stock sd 0.7906 (quarter-end months 0.7797); the engine's stationary sd(x) is 0.0656091445844151.

P/E cap (P99 of the pooled cross-section): 191.5.

Damodaran industry current P/E (Jan 2026, cross-check only): median 34.9699254390457, IQR [21.213184478949785, 70.43922457679868], n industries 95.

Design grids (33-point quantile grids, inverse-CDF sampled): see multiple.json `design_grids`.
