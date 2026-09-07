# E5.7(a) per-field-group ablation -- multiple_B_P10-P90

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_multiple_B_P10-P90.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4137 [+0.3988, +0.4287].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| VAL | +0.0114 [+0.0027, +0.0204] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.3213 [+0.2910, +0.3498].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| VAL | +0.0388 [+0.0272, +0.0508] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3811 [+0.3631, +0.3982].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| VAL | +0.0051 [-0.0012, +0.0121] | n/a | 0.1377 -> 0.1372 |

## R2(log V), population CALM

BASE (level-free control) +0.4150 [+0.3953, +0.4337].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| VAL | -0.0019 [-0.0134, +0.0101] | n/a | 0.1067 -> 0.1048 |

