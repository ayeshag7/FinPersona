# E5.7(a) per-field-group ablation -- sentiment_B_half

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_sentiment_B_half.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4062 [+0.3912, +0.4218].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | +0.0205 [+0.0168, +0.0236] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.2903 [+0.2606, +0.3195].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | +0.0056 [+0.0010, +0.0109] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3891 [+0.3715, +0.4062].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | +0.0004 [-0.0003, +0.0011] | n/a | 0.1360 -> 0.1359 |

## R2(log V), population CALM

BASE (level-free control) +0.4304 [+0.4111, +0.4494].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | -0.0014 [-0.0030, +0.0000] | n/a | 0.1046 -> 0.1044 |

