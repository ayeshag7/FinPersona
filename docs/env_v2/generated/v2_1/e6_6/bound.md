# E6.6 — the analytic level-free bound at the adopted parameters, the sweep check, and the calm-channel ladder

## The bound at the parameters in force

σ_V = 0.014573/day (`value.json`), h = 22.38 d, interval [18.75, 32.64] (`mispricing.json`), sbar = 0.015088, λ = 0.000583, σ_J = 0.2303 (`docs/env_v2/generated/v2_1/e3_4/block.json`).

**s_x is derived, not read**: var(innovation) = sbar^2 (+ lambda sigma_J^2); s_x = sqrt(var / (1 - rho^2)); E3.8's construction. No parameter file stores a stationary sd(x). → **0.0616** without the jumps, **0.0656** with them. Realised on the generator's own paths: flat pooled 0.0640 (per-path median 0.0460, P10–P90 [0.0302, 0.0788], n = 200), all calm rows pooled 0.0633 (n = 148,329 rows).

| h | s_x | value | window average | day 200 | steady state |
|---|---|---|---|---|---|
| h = 22.38 | identity_no_jumps | 0.0616 | 0.1633 | 0.1840 | 0.1840 |
| h = 22.38 | identity_with_jumps | 0.0656 | 0.1773 | 0.2005 | 0.2006 |
| h = 22.38 | realised_flat_pooled | 0.0640 | 0.1716 | 0.1938 | 0.1939 |
| h = 22.38 | realised_all_calm_pooled | 0.0633 | 0.1695 | 0.1913 | 0.1913 |
| h_lo = 18.75 | identity_no_jumps | 0.0616 | 0.1869 | 0.2073 | 0.2073 |
| h_lo = 18.75 | identity_with_jumps | 0.0656 | 0.2021 | 0.2250 | 0.2250 |
| h_lo = 18.75 | realised_flat_pooled | 0.0640 | 0.1960 | 0.2178 | 0.2178 |
| h_lo = 18.75 | realised_all_calm_pooled | 0.0633 | 0.1937 | 0.2151 | 0.2151 |
| h_hi = 32.64 | identity_no_jumps | 0.0616 | 0.1188 | 0.1399 | 0.1401 |
| h_hi = 32.64 | identity_with_jumps | 0.0656 | 0.1300 | 0.1537 | 0.1540 |
| h_hi = 32.64 | realised_flat_pooled | 0.0640 | 0.1255 | 0.1481 | 0.1484 |
| h_hi = 32.64 | realised_all_calm_pooled | 0.0633 | 0.1238 | 0.1460 | 0.1462 |
| plan v2 row h = 150 | sigma_V 0.006 s_x 0.13 | 0.130 | 0.1370 | 0.2345 | 0.3959 |
| plan v2 row h = 150 | sigma_V 0.006 s_x 0.165 | 0.165 | 0.1503 | 0.2599 | 0.4773 |

**Adopted row** (s_x with the jumps, FIT h): window average **0.1773**, day 200 **0.2005**, steady state 0.2006. At h = 22 d the day-200 value and the steady state coincide: the filter has converged long before the window ends, so the ceiling for a reader with the whole history is the steady state, and the window average is the ceiling for the average day.

## The check against Phase 1's sweep

40 points of `docs/env_v2/generated/v2_1/e1_3/sweep.json` (h = 150 d, 200 seeds each): the surrogate's calm R²(x) CI lower end exceeds the window-average bound at **0** points and the day-200 bound at **0**. the bound is valid at a point when the surrogate's CI lower end does not exceed it; the count is the instrument's validation across the sweep (Appendix B's check).

| σ_V | V innov. | s_x | surrogate calm R² [CI] | bound: window / day 200 / steady | point gap |
|---|---|---|---|---|---|
| 0.004 | gaussian | 0.100 | 0.159 [0.073, 0.195] | 0.145 / 0.251 / 0.445 | +0.014 |
| 0.004 | gaussian | 0.130 | 0.156 [0.093, 0.178] | 0.157 / 0.274 / 0.533 | -0.001 |
| 0.004 | gaussian | 0.165 | 0.151 [0.099, 0.169] | 0.165 / 0.288 / 0.607 | -0.014 |
| 0.004 | gaussian | 0.200 | 0.136 [0.100, 0.153] | 0.169 / 0.297 / 0.662 | -0.033 |
| 0.004 | t5 | 0.100 | 0.165 [0.070, 0.204] | 0.145 / 0.251 / 0.445 | +0.020 |
| 0.004 | t5 | 0.130 | 0.154 [0.095, 0.175] | 0.157 / 0.274 / 0.533 | -0.003 |
| 0.004 | t5 | 0.165 | 0.162 [0.109, 0.180] | 0.165 / 0.288 / 0.607 | -0.003 |
| 0.004 | t5 | 0.200 | 0.140 [0.106, 0.158] | 0.169 / 0.297 / 0.662 | -0.029 |
| 0.006 | gaussian | 0.100 | 0.152 [0.045, 0.196] | 0.118 / 0.199 / 0.308 | +0.034 |
| 0.006 | gaussian | 0.130 | 0.141 [0.074, 0.165] | 0.137 / 0.235 / 0.396 | +0.004 |
| 0.006 | gaussian | 0.165 | 0.145 [0.089, 0.164] | 0.150 / 0.260 / 0.477 | -0.005 |
| 0.006 | gaussian | 0.200 | 0.131 [0.095, 0.148] | 0.158 / 0.276 / 0.541 | -0.028 |
| 0.006 | t5 | 0.100 | 0.159 [0.057, 0.199] | 0.118 / 0.199 / 0.308 | +0.041 |
| 0.006 | t5 | 0.130 | 0.161 [0.084, 0.188] | 0.137 / 0.235 / 0.396 | +0.024 |
| 0.006 | t5 | 0.165 | 0.153 [0.092, 0.173] | 0.150 / 0.260 / 0.477 | +0.003 |
| 0.006 | t5 | 0.200 | 0.140 [0.101, 0.156] | 0.158 / 0.276 / 0.541 | -0.019 |
| 0.010 | gaussian | 0.100 | 0.110 [-0.021, 0.165] | 0.074 / 0.120 / 0.162 | +0.036 |
| 0.010 | gaussian | 0.130 | 0.131 [0.033, 0.169] | 0.097 / 0.161 / 0.231 | +0.034 |
| 0.010 | gaussian | 0.165 | 0.126 [0.060, 0.147] | 0.117 / 0.198 / 0.304 | +0.009 |
| 0.010 | gaussian | 0.200 | 0.119 [0.072, 0.135] | 0.132 / 0.224 / 0.369 | -0.013 |
| 0.010 | t5 | 0.100 | 0.116 [-0.033, 0.178] | 0.074 / 0.120 / 0.162 | +0.042 |
| 0.010 | t5 | 0.130 | 0.138 [0.035, 0.177] | 0.097 / 0.161 / 0.231 | +0.041 |
| 0.010 | t5 | 0.165 | 0.145 [0.061, 0.176] | 0.117 / 0.198 / 0.304 | +0.028 |
| 0.010 | t5 | 0.200 | 0.127 [0.068, 0.146] | 0.132 / 0.224 / 0.369 | -0.005 |
| 0.015 | gaussian | 0.100 | 0.013 [-0.242, 0.123] | 0.043 / 0.068 / 0.086 | -0.030 |
| 0.015 | gaussian | 0.130 | 0.078 [-0.102, 0.151] | 0.062 / 0.100 / 0.131 | +0.016 |
| 0.015 | gaussian | 0.165 | 0.105 [-0.012, 0.149] | 0.082 / 0.135 / 0.185 | +0.023 |
| 0.015 | gaussian | 0.200 | 0.104 [0.025, 0.128] | 0.099 / 0.165 / 0.238 | +0.005 |
| 0.015 | t5 | 0.100 | -0.001 [-0.301, 0.121] | 0.043 / 0.068 / 0.086 | -0.043 |
| 0.015 | t5 | 0.130 | 0.077 [-0.117, 0.155] | 0.062 / 0.100 / 0.131 | +0.015 |
| 0.015 | t5 | 0.165 | 0.116 [-0.020, 0.170] | 0.082 / 0.135 / 0.185 | +0.033 |
| 0.015 | t5 | 0.200 | 0.117 [0.024, 0.149] | 0.099 / 0.165 / 0.238 | +0.017 |
| 0.020 | gaussian | 0.100 | -0.109 [-0.467, 0.044] | 0.027 / 0.042 / 0.052 | -0.136 |
| 0.020 | gaussian | 0.130 | 0.016 [-0.219, 0.115] | 0.041 / 0.065 / 0.082 | -0.025 |
| 0.020 | gaussian | 0.165 | 0.088 [-0.082, 0.155] | 0.058 / 0.093 / 0.121 | +0.030 |
| 0.020 | gaussian | 0.200 | 0.096 [-0.019, 0.136] | 0.074 / 0.120 / 0.162 | +0.022 |
| 0.020 | t5 | 0.100 | -0.148 [-0.613, 0.048] | 0.027 / 0.042 / 0.052 | -0.175 |
| 0.020 | t5 | 0.130 | -0.006 [-0.316, 0.122] | 0.041 / 0.065 / 0.082 | -0.047 |
| 0.020 | t5 | 0.165 | 0.066 [-0.136, 0.149] | 0.058 / 0.093 / 0.121 | +0.009 |
| 0.020 | t5 | 0.200 | 0.093 [-0.046, 0.148] | 0.074 / 0.120 / 0.162 | +0.019 |

## The calm-channel ladder on the Phase-5 state

| rung | arm | population | n paths | level-free R²(x) [CI] | best | realised sd(x) | Gaussian bound (window) | excess over bound | increment |
|---|---|---|---|---|---|---|---|---|---|
| 1 | E3.8: exact (the bound's model) | all rows (no phases) | 200 | 0.1453 [0.1076, 0.1759] | ridge | 0.0618 | 0.1633 | -0.0180 | — |
| 2 | E3.8: + GJR-t innovation (block in force) | all rows (no phases) | 200 | 0.1454 [0.0962, 0.1838] | ridge | 0.0618 | 0.1633 | -0.0179 | +0.0001 |
| 3 | E3.8: + jumps (FIT lambda, sigma_J) | all rows (no phases) | 200 | 0.1918 [0.1047, 0.2882] | mlp | 0.0662 | 0.1773 | +0.0146 | +0.0465 |
| 4 | E3.8: + GJR-t + jumps (the Phase-3 x innovation) | all rows (no phases) | 200 | 0.2025 [0.1409, 0.2625] | ridge | 0.0691 | 0.1773 | +0.0252 | +0.0107 |
| 5 | generator flat, feedback OFF (b_pred = b_rev = 0) | flat paths, calm rows | 200 | 0.2204 [0.1599, 0.2801] | ridge | 0.0639 | 0.1714 | +0.0490 | +0.0179 |
| 6 | generator flat, as deployed (feedback ON) | flat paths, calm rows | 200 | 0.2217 [0.1611, 0.2813] | ridge | 0.0640 | 0.1716 | +0.0501 | +0.0014 |
| 7 | generator, every calm row of the SEP panel (flat + pre-event calm) | all scenarios, calm rows | 1600 | 0.2912 [0.2637, 0.3179] | gbt | 0.0633 | 0.1695 | +0.1217 | +0.0694 |

1 -> 4 the volatility block's nonlinear allowance (E3.8); 4 -> 5 the process-to-generator step at flat (same parameters; the generator's V has drift and t innovations, and jumps are placed at x_zero); 5 -> 6 the sentiment feedback's share; 6 -> 7 the events' share (the pre-event calm of crash and bull-trap paths). The rule that reads this against G4's second clause is PREREG_PHASE_6's.

