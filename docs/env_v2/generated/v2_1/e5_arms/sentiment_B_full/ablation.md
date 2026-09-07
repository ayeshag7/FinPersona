# E5.7(a) per-field-group ablation -- sentiment_B_full

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_sentiment_B_full.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4063 [+0.3914, +0.4218].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | +0.0813 [+0.0731, +0.0883] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.2879 [+0.2576, +0.3176].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | +0.0212 [+0.0151, +0.0274] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3881 [+0.3706, +0.4052].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | +0.0027 [+0.0017, +0.0036] | n/a | 0.1362 -> 0.1358 |

## R2(log V), population CALM

BASE (level-free control) +0.4284 [+0.4089, +0.4471].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | -0.0007 [-0.0022, +0.0009] | n/a | 0.1048 -> 0.1044 |

