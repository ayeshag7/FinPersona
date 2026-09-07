# E5.7(a) per-field-group ablation -- analyst_A_sd0.300

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_analyst_A_sd0.300.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4137 [+0.3988, +0.4287]; FULL +0.7679 [+0.7547, +0.7809].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| ANALYST | +0.0013 [-0.0024, +0.0048] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.3213 [+0.2910, +0.3498]; FULL +0.4535 [+0.4209, +0.4856].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| ANALYST | +0.0187 [+0.0056, +0.0303] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3811 [+0.3631, +0.3982]; FULL +0.5855 [+0.5647, +0.6032].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| ANALYST | +0.0439 [+0.0305, +0.0569] | n/a | 0.1377 -> 0.1331 |

## R2(log V), population CALM

BASE (level-free control) +0.4150 [+0.3953, +0.4337]; FULL +0.5898 [+0.5597, +0.6192].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| ANALYST | +0.0396 [+0.0211, +0.0572] | n/a | 0.1067 -> 0.1028 |

