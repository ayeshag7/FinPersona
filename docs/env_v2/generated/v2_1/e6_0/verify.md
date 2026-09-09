# PREREG_PHASE_6 section 1 — inherited numbers verified against their files

59 rows; 0 mismatches; 0 unreadable. Generated 2026-09-09T09:29:51Z.

| inherited figure | cited | file | file value | match |
|---|---|---|---|---|
| L2b full accuracy, Phase 5 | 0.676 | `e5_after/audit_after_levelfree.pkl L2b.acc_full` | 0.676205 | OK |
| L2b price-only accuracy | 0.658 | `... L2b.acc_price_only` | 0.658153 | OK |
| L2b day-only accuracy | 0.508 | `... L2b.acc_day_only` | 0.507993 | OK |
| L2b majority class | 0.414 | `... L2b.majority_class` | 0.414361 | OK |
| L2b selectivity (+1.8 pp) | 0.018 | `... L2b.selectivity` | 0.0180521 | OK |
| L2 calm best R2(x) | -0.61 | `... L2_verdict.calm_best_R2_x` | -0.613799 | OK |
| L2 event best R2(x) | 0.45 | `... L2_verdict.event_best_R2_x` | 0.453927 | OK |
| L2 event MAPE(V) | 0.128 | `... L2_verdict.event_best_MAPE_V` | 0.128059 | OK |
| L2 max selectivity R2(x) | 0.028 | `... L2_verdict.max_selectivity_R2_x` | 0.0282014 | OK |
| L2 max MAPE(V) gain | 0.017 | `... L2_verdict.max_MAPE_gain_V` | 0.0173632 | OK |
| L2 shuffled-V R2 | 0.001 | `... L2_verdict.max_R2_shuffledV` | 0.000868784 | OK |
| audit not subsampled | False | `... subsampled` | False | OK |
| audit paths | 1600 | `... n_paths` | 1600 | OK |
| L1 price itself median APE | 0.063 | `e5_after/audit_after_levelfree_L1.csv` | 0.0625733 | OK |
| L1 price itself within-5 % | 0.426 | `... within_5pct` | 0.426109 | OK |
| calm-trained level-free R2(x), Phase 5 | 0.2912 | `e5_after/calm_trained_phase5.json headline.phase5.calm_trained_levelfree.R2` | 0.291183 | OK |
| ... CI lo | 0.2637 | `... R2_lo` | 0.263716 | OK |
| ... CI hi | 0.3179 | `... R2_hi` | 0.317897 | OK |
| calm-trained full R2(x), Phase 5 | 0.395 | `... calm_trained_full.R2` | 0.395023 | OK |
| BASE|x|all R2 (the box's reference row) | 0.4059 | `e5_7a/final/ablation.json fits.BASE|x|all.R2` | 0.40587 | OK |
| BASE|x|calm R2 | 0.2912 | `... fits.BASE|x|calm.R2` | 0.291183 | OK |
| FULL|x|all R2 | 0.432 | `... fits.FULL|x|all.R2` | 0.432167 | OK |
| VAL add-one, all rows | 0.009 | `... tables.x|all.groups.VAL.add_one.delta` | 0.00898461 | OK |
| VAL add-one, calm-trained | 0.0509 | `... tables.x|calm.groups.VAL.add_one.delta` | 0.050926 | OK |
| FULL - BASE, all rows (what 'the eighteen fields add' means) | 0.026 | `... fits.FULL|x|all.R2 - fits.BASE|x|all.R2` | 0.0262979 | OK |
| sum of per-group add-ones, all rows (informational; differs from FULL - BASE by the groups' interaction) | 0.02 | `... tables.x|all (sum over groups)` | 0.019814 | OK |
| ANALYST column-permutation null p95 | -0.0057 | `e5_7a/baseline/ablation.json null_margins.ANALYST.p95_estimate` | -0.00574454 | OK |
| SENT column-permutation null p95 | -0.0024 | `... null_margins.SENT.p95_estimate` | -0.00244397 | OK |
| E3.8 exact-Gaussian level-free R2 | 0.145 | `e3_8/decomposition.json arms[0].levelfree_R2` | 0.145274 | OK |
| E3.8 exact arm's Gaussian bound | 0.163 | `... arms[0].bound_window_avg_gaussian` | 0.163275 | OK |
| E3.8 full stack level-free R2 | 0.203 | `... arms[3].levelfree_R2` | 0.202501 | OK |
| E3.8 full stack CI lo | 0.141 | `... arms[3].ci95[0]` | 0.140909 | OK |
| E3.8 full stack CI hi | 0.262 | `... arms[3].ci95[1]` | 0.262481 | OK |
| E3.8 full stack bound (window avg) | 0.177 | `... arms[3].bound_window_avg_gaussian` | 0.177252 | OK |
| E3.8 s_x implied (with jumps) | 0.0656 | `... arms[3].s_x_implied` | 0.0656091 | OK |
| sigma_V in force | 0.014573 | `envs/v2/params/value.json sigma_V.value` | 0.0145733 | OK |
| h in force (d) | 22.381 | `envs/v2/params/mispricing.json half_life.value` | 22.3809 | OK |
| h interval lo | 18.75 | `... structural.interval.h[0]` | 18.7499 | OK |
| h interval hi | 32.64 | `... structural.interval.h[1]` | 32.6393 | OK |
| sbar in force | 0.015088 | `e3_4/block.json sbar` | 0.0150879 | OK |
| GJR alpha | 0.027 | `e3_4/block.json shape.alpha` | 0.027 | OK |
| GJR gamma | 0.058 | `... shape.gamma` | 0.058 | OK |
| GJR beta | 0.932 | `... shape.beta` | 0.932 | OK |
| jump rate | 0.000583 | `... jump_rate` | 0.000582511 | OK |
| jump sd | 0.2303 | `... jump_sd` | 0.230297 | OK |
| Kalman bound verified against LOG section 3 | True | `kalman_bound_verification.json passed` | True | OK |
| onset PASS under the non-price rule (all six transitions) | True | `e5_7c/final/onset.json verdict_nonprice.all_pass` | True | OK |
| onset under the rule as registered: number of failing (transition, field) pairs | 9 | `... verdict.failures (len)` | 9 | OK |
| L5 coverage flat, Phase 5 | 0.362 | `e5_l5/discrimination.json states.phase5_after.scenarios.flat.coverage_0.05` | 0.3621 | OK |
| L5 coverage crash, Phase 5 | 0.543 | `e5_l5/discrimination.json states.phase5_after.scenarios.crash.coverage_0.05` | 0.5435 | OK |
| L5 coverage bull_trap, Phase 5 | 0.636 | `e5_l5/discrimination.json states.phase5_after.scenarios.bull_trap.coverage_0.05` | 0.6364 | OK |
| L5 coverage sustained_bull, Phase 5 | 0.354 | `e5_l5/discrimination.json states.phase5_after.scenarios.sustained_bull.coverage_0.05` | 0.3543 | OK |
| L5 ordering oracle < L5 < trivial, flat | True | `... scenarios.flat (oracle.mean < L5_best.mean < trivial_best.mean)` | True | OK |
| L5 ordering oracle < L5 < trivial, crash | True | `... scenarios.crash (oracle.mean < L5_best.mean < trivial_best.mean)` | True | OK |
| L5 ordering oracle < L5 < trivial, bull_trap | True | `... scenarios.bull_trap (oracle.mean < L5_best.mean < trivial_best.mean)` | True | OK |
| L5 ordering oracle < L5 < trivial, sustained_bull | True | `... scenarios.sustained_bull (oracle.mean < L5_best.mean < trivial_best.mean)` | True | OK |
| audit_bounds.no_field_deterministic_R2 (PROVISIONAL) | 0.2 | `envs/v2/params/observables.json audit_bounds.value` | 0.2 | OK |
| audit_bounds.l2b_margin_phase6_owned (PROVISIONAL) | 0.1 | `... l2b_margin_phase6_owned` | 0.1 | OK |
| audit_bounds status | PROVISIONAL | `... status` | PROVISIONAL | OK |
