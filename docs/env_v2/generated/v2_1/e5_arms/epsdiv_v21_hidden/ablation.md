# E5.7(a) per-field-group ablation -- epsdiv_v21_hidden

Panel `docs\env_v2\generated\v2_1\_panels\sep_phase5_epsdiv_v21_hidden.pkl`: 1600 paths, 288000 modelled rows; estimator leakage_audit._models()['gbt'] (HistGradientBoosting 200/0.08/6), 5-fold GroupKFold by path; L2b: HistGradientBoostingClassifier 200/0.1/4; 500-resample paired cluster bootstrap over paths. State: events_json=True, control=A, dynamics=A, blowoff=dynamic, post_top=decay/40.0, randomise_eps_quarter=True, depth_mode=centred, volatility_json=True, iv=v21, observables_json=False.

## R2(x), population ALL

BASE (level-free control) +0.4137 [+0.3988, +0.4287].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| VAL | +0.0515 [+0.0399, +0.0628] | n/a |

## R2(x), population CALM

BASE (level-free control) +0.3213 [+0.2910, +0.3498].

| group | add-one delta [paired CI] | drop-one delta [paired CI] |
|---|---|---|
| VAL | +0.0231 [+0.0120, +0.0359] | n/a |

## R2(log V), population ALL

BASE (level-free control) +0.3811 [+0.3631, +0.3982].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| VAL | +0.0750 [+0.0598, +0.0888] | n/a | 0.1377 -> 0.1307 |

## R2(log V), population CALM

BASE (level-free control) +0.4150 [+0.3953, +0.4337].

| group | add-one delta [paired CI] | drop-one delta [paired CI] | MAPE(V) base -> +G |
|---|---|---|---|
| VAL | +0.0471 [+0.0337, +0.0613] | n/a | 0.1067 -> 0.1040 |

