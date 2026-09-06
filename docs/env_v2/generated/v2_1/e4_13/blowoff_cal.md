# E4.13 - the blow-off multiplier's closed loop

`python -m tools.phase4.e4_13_blowoff_cal` - P4-11's outstanding half.

Panel target (corrected reference): **1.2895 [1.2146, 1.3713]**, n = 3125 run-ups / 394 stocks.

| | multiplier | realised blow-off/mania | 95 % CI | inside the panel CI |
|---|---|---|---|---|
| incumbent (mania's value) | 1.3451 | 1.0160 | [0.9375, 1.0965] | **False** |
| **calibrated** | **2.0764** | **1.3136** | [1.2139, 1.4119] | **True** |

## Closed loop

| iteration | multiplier | realised |
|---|---|---|
| 0 | 1.3451 | 1.0288 |
| 1 | 1.6859 | 1.1436 |
| 2 | 1.9008 | 1.2216 |
| 3 | 2.0064 | 1.2601 |
| 4 | 2.0531 | 1.2789 |
| 5 | 2.0701 | 1.2856 |

Verified at 1200 seeds. Verdict: **CALIBRATED**.
