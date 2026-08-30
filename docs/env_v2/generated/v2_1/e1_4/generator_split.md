# E1.4 generator side and the rule (PREREG_PHASE_1.md section 5.2-5.3)

200 flat paths (seeds 70000-70199, T = 200) per variant, GJR-GARCH-t residuals per path; window = the 10 trading days ending on each EPS announcement day; KS distances to the panel's window / other-day residual pools (E1.4 panel side, 415 stocks) with a 1000-resample bootstrap over stocks and paths; rule: both upper limits < 0.1 and the 95 % interval of E[x] inside +/- 0.02.

| variant | window share | q (jumps in window) | rate in / out | kurtosis in / out | KS window (upper) | KS other (upper) | KS pass | E[x] [CI] | E[x] pass | kurt > 1.5 share | median kurt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| current_x_negmean | 0.151 | 0.191 | 0.0055 / 0.0041 | 6.2 / 5.9 | 0.017 (0.028) | 0.015 (0.019) | True | -0.0690 [-0.0881, -0.0476] | False | 0.78 | 3.19 |
| B_x_zero | 0.151 | 0.213 | 0.0038 / 0.0025 | 3.1 / 3.2 | 0.015 (0.029) | 0.020 (0.025) | True | +0.0104 [-0.0085, +0.0299] | False | 0.65 | 2.22 |
| A_V_announce | 0.151 | 0.277 | 0.0055 / 0.0025 | 3.2 / 2.7 | 0.016 (0.031) | 0.020 (0.024) | True | +0.0103 [-0.0088, +0.0300] | False | 0.67 | 2.39 |
| C_both | 0.151 | 0.270 | 0.0052 / 0.0025 | 3.1 / 3.0 | 0.016 (0.031) | 0.020 (0.024) | True | +0.0083 [-0.0104, +0.0282] | False | 0.66 | 2.36 |

**Decision (pre-registered rule): None -- no variant meets the KS rule and C fails the E[x] rule: none adopted, team asked.**
Panel: window share 0.145; q 0.43, rate ratio 4.5, kurtosis in/out 16.2 / 15.0 (e1_4/panel_split.md).
