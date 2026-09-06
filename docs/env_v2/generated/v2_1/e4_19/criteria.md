# E4.19 the inherited criteria, re-registered against what the generator can express

E4.19: the inherited criteria re-registered against what the generator can express, plus the two untested claims behind section 5.1's D5 recommendation.

Panel family `dd30_fast`: n = 642 episodes, 313 stocks. Selection: peak-to-trough duration <= 126 trading days -- the sub-population that FITS a 200-day benchmark horizon; this is a selection and is stated as one (Phase 3 called it the fast-crash secondary population and set the rise-time target on it)

## 1. Is the coverage box a window artefact? NO

`dd30_fast` is **already** restricted to peak-to-trough duration <= 126 d -- the sub-population that fits a 200-day horizon -- so the box is window-matched on duration before any of this. Its self-coverage recomputed here: **0.6433 [0.6074, 0.6791]** (n = 642), reproducing E4.6's 0.643. The 0.70 threshold sits above it, and that is a property of putting a P10-P90 box on **two correlated quantities**, not of the horizon.

## 2. Per arm: coverage, where it fails, and the script metric

Coverage matches E4.6's estimand exactly: conditional on the path having a measurable episode. The discarded share is reported beside it, because a path with no measurable episode is a different failure from one whose episode lands outside the box.

| arm | coverage | 95 % CI | no measurable episode | fail depth only | fail duration only | fail both | script share | 95 % CI | minus unscripted null | separable |
|---|---|---|---|---|---|---|---|---|---|---|
| A_lam0.02 | 0.474 | [0.438, 0.508] | 0.211 | 0.369 | 0.084 | 0.074 | 0.0467 | [0.0439, 0.0484] | +0.0168 [+0.0138, +0.0190] | **yes** |
| A_lam0.05 | 0.480 | [0.445, 0.516] | 0.221 | 0.356 | 0.081 | 0.083 | 0.0619 | [0.0595, 0.0649] | +0.0321 [+0.0296, +0.0353] | **yes** |
| A_lam0.1 | 0.520 | [0.483, 0.555] | 0.221 | 0.318 | 0.086 | 0.076 | 0.0803 | [0.0764, 0.0837] | +0.0504 [+0.0466, +0.0540] | **yes** |
| A_lam0.25 | 0.562 | [0.527, 0.597] | 0.228 | 0.282 | 0.083 | 0.073 | 0.1304 | [0.1264, 0.1340] | +0.1005 [+0.0963, +0.1043] | **yes** |
| B_shifted_pstar | 0.521 | [0.485, 0.558] | 0.221 | 0.306 | 0.108 | 0.065 | 0.0390 | [0.0379, 0.0408] | +0.0091 [+0.0074, +0.0112] | **yes** |
| C_scripted_no_feedback | 0.462 | [0.427, 0.496] | 0.201 | 0.395 | 0.076 | 0.066 | 0.0136 | [0.0117, 0.0158] | -0.0162 [-0.0185, -0.0140] | **yes** |
| D_unscripted_regime | 0.323 | [0.291, 0.359] | 0.323 | 0.487 | 0.066 | 0.123 | 0.0299 | [0.0286, 0.0311] | +0.0000 [+0.0000, +0.0000] | no |

## 2b. Pairwise coverage differences (an overlap of CIs is not a verdict)

| comparison | difference | 95 % CI | separable |
|---|---|---|---|
| A_lam0.02 - A_lam0.05 | -0.0061 | [-0.0557, +0.0462] | no |
| A_lam0.02 - A_lam0.1 | -0.0459 | [-0.0944, +0.0003] | no |
| A_lam0.02 - A_lam0.25 | -0.0882 | [-0.1369, -0.0372] | **yes** |
| A_lam0.02 - B_shifted_pstar | -0.0472 | [-0.0980, +0.0038] | no |
| A_lam0.02 - C_scripted_no_feedback | +0.0122 | [-0.0357, +0.0611] | no |
| A_lam0.02 - D_unscripted_regime | +0.1505 | [+0.0971, +0.1987] | **yes** |
| A_lam0.05 - A_lam0.1 | -0.0398 | [-0.0912, +0.0103] | no |
| A_lam0.05 - A_lam0.25 | -0.0821 | [-0.1284, -0.0331] | **yes** |
| A_lam0.05 - B_shifted_pstar | -0.0411 | [-0.0899, +0.0077] | no |
| A_lam0.05 - C_scripted_no_feedback | +0.0183 | [-0.0298, +0.0679] | no |
| A_lam0.05 - D_unscripted_regime | +0.1566 | [+0.1070, +0.2089] | **yes** |
| A_lam0.1 - A_lam0.25 | -0.0423 | [-0.0928, +0.0107] | no |
| A_lam0.1 - B_shifted_pstar | -0.0013 | [-0.0501, +0.0488] | no |
| A_lam0.1 - C_scripted_no_feedback | +0.0581 | [+0.0085, +0.1050] | **yes** |
| A_lam0.1 - D_unscripted_regime | +0.1964 | [+0.1498, +0.2483] | **yes** |
| A_lam0.25 - B_shifted_pstar | +0.0410 | [-0.0130, +0.0903] | no |
| A_lam0.25 - C_scripted_no_feedback | +0.1003 | [+0.0518, +0.1501] | **yes** |
| A_lam0.25 - D_unscripted_regime | +0.2387 | [+0.1891, +0.2873] | **yes** |
| B_shifted_pstar - C_scripted_no_feedback | +0.0594 | [+0.0115, +0.1068] | **yes** |
| B_shifted_pstar - D_unscripted_regime | +0.1977 | [+0.1465, +0.2495] | **yes** |
| C_scripted_no_feedback - D_unscripted_regime | +0.1383 | [+0.0877, +0.1883] | **yes** |

## 3. The joint window constraint, measured on 4000 deployed draws

- setup_len p10/p50/p90: 56 / 81 / 104
- realised event length (det + panic) p10/p50/p90: 24 / 49 / 94
- headroom after a median setup and a 10-day minimum resolution: **109 d**, against the panel box's duration p90 of 113 d
- share of the panel's own target episodes that fit alongside a **median** setup: **0.871**; alongside a **p90** setup: **0.735**

## 4. E4.5's KS equivalence bound: the n at which it becomes decidable

Null floor (95th percentile of the two-sample KS statistic when both samples share a distribution) at the achieved n_acc/n_rej = 419/81: **0.159**, against a registered bound of 0.10 -- so the bound was **not decidable**.

| n_rej (n_acc scaled at the same 419:81 ratio) | null floor |
|---|---|
| 81 | 0.159 |
| 200 | 0.105 |
| 400 | 0.073 |
| 800 | 0.052 |
| 1600 | 0.037 |
| 3200 | 0.026 |
| 6400 | 0.019 |

**n_rej needed for the 0.10 bound to be decidable: 400.**

