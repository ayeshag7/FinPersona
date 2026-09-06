# E4.20 the crash depth, calibrated closed-loop

E4.20: closed-loop calibration of the crash depth, the cause E4.19 identified for the coverage shortfall that blocks D5.

Panel target (dd30_fast): depth p50 **-0.3693**, box [-0.5377, -0.3117].

| | depth_gain | realised depth p50 | 95 %% CI | share inside the panel's depth box |
|---|---|---|---|---|
| uncalibrated | 1.0 | -0.5134 | [-0.5211, -0.5057] | 0.588 |
| **calibrated** | **0.20781** | **-0.4614** | [-0.4695, -0.4550] | **0.727** |

Target inside the calibrated CI: **False**. Verified at 1200 seeds DISJOINT from the 400 used to fit (seed blocks 480000 and 460000), so the number reported is not the number fitted.

## The loop

| iteration | gain | realised depth p50 |
|---|---|---|
| 0 | 1.00000 | -0.5126 |
| 1 | 0.70000 | -0.4674 |
| 2 | 0.45000 | -0.4510 |
| 3 | 0.32500 | -0.4507 |
| 4 | 0.26250 | -0.4510 |
| 5 | 0.23125 | -0.4510 |
| 6 | 0.21563 | -0.4510 |
| 7 | 0.20781 | -0.4510 |

