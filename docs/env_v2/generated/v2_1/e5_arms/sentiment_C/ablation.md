# E5.7(a) per-field-group ablation -- sentiment_C

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_sentiment_C.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4095 [+0.3944, +0.4244].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | -0.0009 [-0.0021, +0.0003] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.3052 [+0.2745, +0.3356].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | +0.0073 [+0.0006, +0.0146] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3874 [+0.3699, +0.4044].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | +0.0000 [-0.0014, +0.0014] | n/a | 0.1363 -> 0.1361 |

## R2(log V), population CALM

BASE (level-free control) +0.4257 [+0.4063, +0.4436].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | -0.0013 [-0.0040, +0.0018] | n/a | 0.1051 -> 0.1047 |

