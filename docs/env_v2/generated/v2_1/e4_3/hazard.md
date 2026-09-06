# E4.3 - the bubble hazard, re-fitted (REG-18)

`python -m tools.phase4.e4_3_hazard` - PREREG_PHASE_4.md section 5.

**The 40-60 % topped band and the P/V 1.6-2.5 band are retired as targets.** The yardstick is the panel's own topped share:

- panel: **0.1100 [0.0962, 0.1246]**, n = 3201 run-ups / 398 stocks, 200-day horizon, -40 % threshold
- REG-15: the survivor panel understates crash frequency and depth, so this share is a LOWER bound on the true single-stock rate

## The two slopes

| source | b | topped/crash share | n |
|---|---|---|---|
| GSY 2019 (read; industry, 2 y, -40 %) | 5.4186 | 20 / 53 / 80 % at 50 / 100 / 150 % | 3 published points |
| panel (single stock, 200 d, -40 %) | 1.0735 | 0.1100 | 3201 / 398 |

The industry relation is **5.0x steeper** than the single-stock one. That gap is what REG-18's horizon/level transfer assumption has to carry, and it is now measured rather than assumed.

## The mappings

| mapping | b | h0 | topped (panel rule) | 95 % CI | inside panel CI | peak P/V median | rejection |
|---|---|---|---|---|---|---|---|
| A_no_scaling | 5.419 | 6.712e-04 | 0.108 | [0.081, 0.135] | **INSIDE** | 1.49 | 0.150 |
| B_scaled_0.5x | 5.419 | 7.087e-05 | 0.022 | [0.009, 0.035] | **OUTSIDE** | 1.50 | 0.072 |
| B_scaled_1x | 5.419 | 1.442e-04 | 0.034 | [0.018, 0.050] | **OUTSIDE** | 1.50 | 0.080 |
| B_scaled_2x | 5.419 | 2.993e-04 | 0.048 | [0.029, 0.067] | **OUTSIDE** | 1.50 | 0.110 |
| C_panel_fit | 1.074 | 6.416e-04 | 0.036 | [0.020, 0.052] | **OUTSIDE** | 1.50 | 0.104 |
| v2_incumbent | 6.000 | 3.000e-04 | 0.064 | [0.043, 0.085] | **OUTSIDE** | 1.50 | 0.108 |

## Decision

- rule: REG-18: adopt the mapping whose topped share lies inside the panel's CI [0.0962, 0.1246]
- n: 3201 run-ups / 398 stocks -- far above REG-18's n < 30 fallback threshold, so the rule is decidable and the {0.5x, 1x, 2x} bracket is a sensitivity rather than the verdict
- mappings inside the panel CI: **['A_no_scaling']**
- adopted: **A_no_scaling**

