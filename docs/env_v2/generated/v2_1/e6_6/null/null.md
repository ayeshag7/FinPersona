# E6.6 / E6.7 — target-permutation nulls of the L2 and L2b selectivities — Phase-5 hand-over state

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_after.pkl`: 1600 paths, 288000 modelled rows; leakage_audit._models()['gbt'] (HistGradientBoosting), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 40 target permutations (seed 660001); 500-resample paired cluster bootstrap over paths for the measured selectivity. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=True.

| statistic | population | control | full | measured selectivity [paired CI] | half-width | null median | null p95 | draws | derived margin | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| L2 R²(x) selectivity | all | +0.4059 | +0.4322 | +0.0263 [+0.0106, +0.0402] | 0.0148 | -0.0481 | -0.0362 | 40 | -0.0214 | **FAIL** |
| L2 R²(x) selectivity | calm | +0.2912 | +0.4000 | +0.1088 [+0.0849, +0.1307] | 0.0229 | -0.0692 | -0.0542 | 20 | -0.0313 | **FAIL** |
| L2b macro-class accuracy selectivity | all | +0.6582 | +0.6877 | +0.0295 [+0.0237, +0.0352] | 0.0057 | -0.0129 | -0.0081 | 20 | -0.0023 | **FAIL** |

The null's location is reported before the rule that uses it is final (rule 11): a null median far from zero means the selectivity statistic is biased under no information, and the margin absorbs that bias only if it is derived from this null rather than stated.
