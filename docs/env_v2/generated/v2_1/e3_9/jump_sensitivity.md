# E3.9d the jump size across its own interval (PREREG_PHASE_3_ADDENDUM.md section 4.4)

lambda held at 0.000583; sbar re-derived from the identity at each sigma_J so the total unconditional variance stays pinned and only the jump/diffusive split moves. E3.8's jump arm, 200 paths x 200 days.

| sigma_J | | sbar (identity) | jump share of x-innovation var | level-free calm R2(x) [95 % CI] |
|---|---|---|---|---|
| 0.086 | interval floor (moment arithmetic) | 0.01594 | 1.7% | +0.158 [+0.119, +0.196] |
| 0.230 | adopted (mixture optimum) | 0.01509 | 11.9% | +0.176 [+0.131, +0.209] |
| 0.241 | interval ceiling | 0.01499 | 13.1% | +0.229 [+0.170, +0.279] |

**Span across the interval: +0.018 of level-free calm R2 between the adopted value and the interval floor.** The adopted 0.230 is therefore the **conservative (it OVERSTATES the jump channel)** end for leakage — which is what the parameter file's label now says, beside 'weakly identified'.
