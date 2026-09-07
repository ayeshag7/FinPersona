# E5.7(a) per-field-group ablation -- analyst_C

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_analyst_C.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4137 [+0.3988, +0.4287].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| ANALYST | -0.0017 [-0.0046, +0.0014] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.3213 [+0.2910, +0.3498].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| ANALYST | +0.0145 [+0.0031, +0.0244] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3811 [+0.3631, +0.3982].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| ANALYST | +0.0086 [+0.0016, +0.0157] | n/a | 0.1377 -> 0.1368 |

## R2(log V), population CALM

BASE (level-free control) +0.4150 [+0.3953, +0.4337].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| ANALYST | +0.0122 [+0.0016, +0.0221] | n/a | 0.1067 -> 0.1050 |

