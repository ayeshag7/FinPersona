# E5.7(a) per-field-group ablation -- sentiment_A

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_sentiment_A.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4059 [+0.3909, +0.4213].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | -0.0007 [-0.0012, -0.0002] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.2912 [+0.2619, +0.3201].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | +0.0029 [-0.0005, +0.0064] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3894 [+0.3716, +0.4068].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | +0.0001 [-0.0006, +0.0009] | n/a | 0.1360 -> 0.1359 |

## R2(log V), population CALM

BASE (level-free control) +0.4300 [+0.4105, +0.4486].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | -0.0003 [-0.0019, +0.0014] | n/a | 0.1046 -> 0.1043 |

