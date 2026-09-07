# E5.7(a) per-field-group ablation -- volume_A

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_volume_A.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4137 [+0.3988, +0.4287].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| VOL | +0.0042 [+0.0026, +0.0059] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.3213 [+0.2910, +0.3498].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| VOL | +0.0065 [+0.0035, +0.0092] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3811 [+0.3631, +0.3982].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| VOL | +0.0061 [+0.0043, +0.0082] | n/a | 0.1377 -> 0.1369 |

## R2(log V), population CALM

BASE (level-free control) +0.4150 [+0.3953, +0.4337].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| VOL | +0.0024 [+0.0005, +0.0045] | n/a | 0.1067 -> 0.1064 |

