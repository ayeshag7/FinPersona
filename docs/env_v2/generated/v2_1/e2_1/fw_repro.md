# E2.1 Franke-Westerhoff reproduction and the units convention (PREREG_PHASE_2.md section 3)

FW's own model (their eqs (1), (5)-(7), DCA, HPM; two independent Gaussian demand noises, no GARCH, no jumps, no drift, constant p*) at FW 2012 Table 1's DCA-HPM parameters. 200 runs, seeds 100001-100200. `price_scale` multiplies (p - p*) inside the misalignment term only.

## Arm A (primary): FW's own moment coverage criterion, T' = 6,750

| convention | joint MCR | 95 % Wilson | FW Table 4 | contains 10.1 %? |
|---|---|---|---|---|
| price_scale = 1 | 10.0 % | [6.6, 14.9] % | 10.1 % | **yes** |
| price_scale = 100 | 0.0 % | [0.0, 1.9] % | 10.1 % | no |
| scale 1, burn 500 | 11.0 % | [7.4, 16.1] % | 10.1 % | **yes** |

Per-moment coverage ratios (%) beside FW 2012 Table 4's DCA-HPM column and Table A1's measured value (reported, not a criterion -- PREREG section 3.3):

| moment | data (Table A1) | sim mean, scale 1 | coverage, scale 1 | FW Table 4 | sim mean, scale 100 | coverage, scale 100 |
|---|---|---|---|---|---|---|
| rAC1 | -0.008 | 0.0071 | 89.5 [84.5, 93.0] | 98.1 | -0.0026 | 99.5 |
| invHill | 0.301 | 0.2565 | 23.0 [17.7, 29.3] | 79.5 | 0.1658 | 0.0 |
| vMean | 0.713 | 0.7499 | 48.5 [41.7, 55.4] | 75.8 | 0.6046 | 0.0 |
| vAC1 | 0.193 | 0.1580 | 99.0 [96.4, 99.7] | 98.5 | -0.0006 | 0.0 |
| vAC5 | 0.187 | 0.1544 | 77.0 [70.7, 82.3] | 65.5 | 0.0002 | 0.0 |
| vAC10 | 0.159 | 0.1454 | 90.0 [85.1, 93.4] | 73.7 | 0.0003 | 0.0 |
| vAC25 | 0.128 | 0.1220 | 87.5 [82.2, 91.4] | 59.5 | 0.0001 | 0.0 |
| vAC50 | 0.112 | 0.0923 | 83.5 [77.7, 88.0] | 39.4 | 0.0000 | 0.0 |
| vAC100 | 0.074 | 0.0560 | 72.5 [65.9, 78.2] | 32.4 | 0.0005 | 0.0 |

## Arm B (secondary, no pass/fail): SABCEMM's summary row, 7,000 steps

| convention | mean chartist share | 95 % CI | mean excess kurtosis | 95 % CI | Hill index |
|---|---|---|---|---|---|
| price_scale = 1 | 0.2987 | [0.2917, 0.3057] | 1.781 | [1.744, 1.817] | 3.891 |
| price_scale = 100 | 0.0028 | [0.0027, 0.0030] | 0.006 | [-0.002, 0.014] | 6.025 |
| scale 1, burn 500 | 0.2841 | [0.2767, 0.2915] | 1.826 | [1.789, 1.863] | 3.880 |
| DIAGNOSTIC: scale 1, mu doubled | 0.2189 | [0.2139, 0.2239] | 1.746 | [1.706, 1.787] | 3.862 |

Published targets: SABCEMM Table 1 DCA-HPM row (read at source) chartist share **0.1674**, excess kurtosis **10.033**, Hill 2.481; the plan's stated pair (0.23 / 7.8) is a mis-transcription and is closest to SABCEMM's DCA-WP row (0.2285 / 7.7600) -- PREREG_PHASE_2.md section 3.1, decision P2-1.

Run time 6 s.
