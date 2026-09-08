# E6.3 — power analysis per checklist item (pilot: docs/env_v2/generated/v2_1/_panels/sep_phase5_after.pkl)

1600 paths (bull_trap 400, crash 800, flat 200, sustained_bull 200); per-seed statistics with the checklist's own helpers and masks; Appendix A's share and median rules; bands = **v2 numeric criteria (REG-14 A)**; planned n = 200 seeds per scenario.

| criterion | item | scenario | kind | pilot n | observed | band / p0 | cross-seed sd | n required | at planned n |
|---|---|---|---|---|---|---|---|---|---|
| `item1_lb_p_share` | 1 | all | share | 1000 | share 0.951 | p0 0.8 (design p1 0.75) | — | 419 | design power 0.55; share CI [0.912, 0.973] → **decidable** |
| `item1_abs_acf1` | 1 | all | band | 1000 | median 0.06204 | [-0.15, 0.15] | 0.07021 | 9 | half-width 0.01216 vs w/5 0.06; to edge 0.08796 → **decidable** (inside) |
| `item2_kurt_share` | 2 | all | share | 1600 | share 0.560 | p0 0.8 (design p1 0.56) | — | 21 | design power 1.00; share CI [0.491, 0.627] → **decidable** |
| `item2_hill` | 2 | all | band | 1600 | median 3.844 | [2.5, 5] | 1.493 | 54 | half-width 0.2587 vs w/5 0.5; to edge 1.156 → **decidable** (inside) |
| `item3_lb_absr_share` | 3 | all | share | 1600 | share 0.463 | p0 0.8 (design p1 0.4625) | — | 11 | design power 1.00; share CI [0.395, 0.532] → **decidable** |
| `item3_acf1_absr` | 3 | all | band | 1600 | median 0.09141 | [0.1, 0.4] | 0.1208 | 25 | half-width 0.02092 vs w/5 0.06; to edge 0.008587 → undecidable (OUTSIDE) |
| `item5_persistence` | 5 | all | band | 1600 | median 0.9747 | [0.9, 0.995] | 0.2129 | 754 | half-width 0.03688 vs w/5 0.019; to edge 0.0203 → undecidable (inside) |
| `item6_lev_share` | 6 | all | share | 1600 | share 0.610 | p0 0.7 (design p1 0.61) | — | 168 | design power 0.86; share CI [0.541, 0.675] → **decidable** |
| `item6_gamma` | 6 | all | band | 1600 | median 0.05911 | [0, +∞] | 0.2223 | 85 | half-width 0.03851 (one-sided); to edge 0.05911 → **decidable** (inside) |
| `item7_spearman` | 7 | all | band | 1600 | median 0.3251 | [0.2, 0.5] | 0.08611 | 13 | half-width 0.01492 vs w/5 0.06; to edge 0.1251 → **decidable** (inside) |
| `item7_logvol_ac1` | 7 | all | band | 1600 | median 0.5539 | [0.5, 0.8] | 0.07242 | 9 | half-width 0.01255 vs w/5 0.06; to edge 0.05392 → **decidable** (inside) |
| `item7_shapiro_share` | 7 | all | share | 1600 | share 0.752 | p0 0.5 (design p1 0.45) | — | 617 | design power 0.41; share CI [0.688, 0.807] → **decidable** |
| `item8_skew` | 8 | crash | band | 800 | median 0.04011 | [−∞, 0] | 0.7373 | 2028 | half-width 0.1277 (one-sided); to edge 0.04011 → undecidable (OUTSIDE) |
| `item8_worst_share` | 8 | crash | share | 800 | share 0.501 | p0 0.7 (design p1 0.50125) | — | 35 | design power 1.00; share CI [0.433, 0.570] → **decidable** |
| `item9_acf1_x` | 9 | all | band | 1000 | median 0.9203 | [0.98, +∞] | 0.0654 | 8 | half-width 0.01133 (one-sided); to edge 0.05971 → **decidable** (OUTSIDE) |
| `item9_sd_x` | 9 | all | band | 1000 | median 0.03854 | [0.08, 0.2] | 0.02016 | 5 | half-width 0.003492 vs w/5 0.024; to edge 0.04146 → **decidable** (OUTSIDE) |
| `item12_sent_acf1` | 12 | all | band | 1600 | median 0.2034 | [0.7, 0.9] | 0.06904 | 18 | half-width 0.01196 vs w/5 0.04; to edge 0.4966 → **decidable** (OUTSIDE) |
| `item12_sent_corr` | 12 | all | band | 1600 | median 0.01736 | [0.25, 0.55] | 0.07059 | 9 | half-width 0.01223 vs w/5 0.06; to edge 0.2326 → **decidable** (OUTSIDE) |
| `item13_iv_calm` | 13 | all | band | 1249 | median 32.36 | [25, 35] | 7.64 | 88 | half-width 1.324 vs w/5 2; to edge 2.636 → **decidable** (inside) |
| `item13_iv_rv_corr` | 13 | all | band | 1600 | median 0.2295 | [0.4, 0.8] | 0.3244 | 99 | half-width 0.05619 vs w/5 0.08; to edge 0.1705 → **decidable** (OUTSIDE) |
| `item20_mdd` | 20 | crash | band | 800 | median -0.5122 | [-0.65, -0.2] | 0.09591 | 7 | half-width 0.01662 vs w/5 0.09; to edge 0.1378 → **decidable** (inside) |
| `item20_calm_sigma` | 20 | flat | band | 200 | median 0.01988 | [0.014, 0.022] | 0.004048 | 39 | half-width 0.0007013 vs w/5 0.0016; to edge 0.002118 → **decidable** (inside) |
| `item20_worst_panic` | 20 | crash | band | 800 | median -0.1245 | [-0.15, -0.06] | 0.06713 | 84 | half-width 0.01163 vs w/5 0.018; to edge 0.02546 → **decidable** (inside) |

**Maximum n required (Appendix A's precision rule, closed bands; the one-sided rule otherwise): 2028.** Two questions are answered per row: Appendix A's *design* n (the count at which the band's w/5 precision, or a 5-pp share shortfall, is resolved) and whether the *verdict on this state* is decidable at the planned n (the median's or share's interval at n clears the nearest edge / p0). An item can be undecidable by the first and decidable by the second when the pilot sits far from the edge, and the reverse when it sits on it; the pre-registration's seed count is the maximum over the items it must decide.
