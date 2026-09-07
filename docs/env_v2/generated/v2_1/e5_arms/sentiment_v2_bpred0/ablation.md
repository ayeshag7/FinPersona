# E5.7(a) per-field-group ablation -- sentiment_v2_bpred0

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_sentiment_v2_bpred0.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4054 [+0.3904, +0.4204].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | +0.0595 [+0.0529, +0.0656] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.2895 [+0.2589, +0.3192].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| SENT | +0.0215 [+0.0159, +0.0273] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3896 [+0.3721, +0.4069].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | +0.0031 [+0.0020, +0.0042] | n/a | 0.1359 -> 0.1355 |

## R2(log V), population CALM

BASE (level-free control) +0.4301 [+0.4108, +0.4492].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| SENT | +0.0022 [+0.0004, +0.0043] | n/a | 0.1046 -> 0.1040 |

