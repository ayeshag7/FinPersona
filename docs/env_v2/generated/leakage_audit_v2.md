# Section 5 leakage / phase-clock / resolvability audit (v2, 50 seeds, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 30000 steps.

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|
| k * analyst_fair_value | 0.9930 | 0.1008 | 0.5219 | 0.9518 | 0.6872 | True |
| k * P (price itself) | 1.0506 | 0.1236 | 2.3639 | 0.9592 | 0.6872 | True |
| k * P / reported_PE | 17.5239 | 0.1546 | 0.7136 | 0.9717 | 0.6872 | True |
| k * P * dividend_yield | 0.5019 | 0.1558 | 0.7224 | 0.9706 | 0.6872 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.918, sign accuracy on resolvable steps = 0.974 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.966, MAPE(V) = 4.5% -> FAIL (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.131 (worst phase group), MAPE(V) gain = 3.2%, max shuffled-V R2 = -0.061. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | sign_acc_resolvable | n_resolvable | R2_shuffledV | MAPE_V | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 11700 | 0.751 | 0.941 | 6978.000 | -0.068 | nan | 0.536 | 0.215 |
| full | ridge | x | event | 9239 | 0.936 | 0.965 | 8156.000 | -4.226 | nan | 0.914 | 0.022 |
| full | ridge | x | resolution | 6061 | 0.909 | 0.986 | 5077.000 | -2.487 | nan | 0.872 | 0.036 |
| full | ridge | x | all | 27000 | 0.901 | 0.962 | 20211.000 | -2.209 | nan | 0.846 | 0.055 |
| full | ridge | logV | calm | 11700 | 0.518 | nan | nan | -0.061 | 0.062 | 0.042 | 0.476 |
| full | ridge | logV | event | 9239 | -1.452 | nan | nan | -0.252 | 0.061 | 0.335 | -1.788 |
| full | ridge | logV | resolution | 6061 | -1.498 | nan | nan | -0.225 | 0.072 | -0.153 | -1.345 |
| full | ridge | logV | all | 27000 | -0.069 | nan | nan | -0.159 | 0.064 | 0.406 | -0.475 |
| full | gbt | x | calm | 11700 | 0.918 | 0.974 | 6978.000 | -0.295 | nan | 0.787 | 0.131 |
| full | gbt | x | event | 9239 | 0.966 | 0.980 | 8156.000 | -0.263 | nan | 0.926 | 0.040 |
| full | gbt | x | resolution | 6061 | 0.948 | 0.989 | 5077.000 | -0.196 | nan | 0.872 | 0.076 |
| full | gbt | x | all | 27000 | 0.954 | 0.980 | 20211.000 | -0.247 | nan | 0.892 | 0.062 |
| full | gbt | logV | calm | 11700 | 0.842 | nan | nan | -0.168 | 0.032 | 0.634 | 0.208 |
| full | gbt | logV | event | 9239 | 0.746 | nan | nan | -0.236 | 0.045 | 0.425 | 0.321 |
| full | gbt | logV | resolution | 6061 | 0.746 | nan | nan | -0.232 | 0.048 | 0.353 | 0.393 |
| full | gbt | logV | all | 27000 | 0.860 | nan | nan | -0.194 | 0.040 | 0.670 | 0.191 |
| full | mlp | x | calm | 11700 | 0.869 | 0.966 | 6978.000 | -0.547 | nan | 0.746 | 0.123 |
| full | mlp | x | event | 9239 | -0.669 | 0.964 | 8156.000 | -13.966 | nan | 0.921 | -1.590 |
| full | mlp | x | resolution | 6061 | -1.221 | 0.977 | 5077.000 | -12.862 | nan | 0.857 | -2.078 |
| full | mlp | x | all | 27000 | -0.550 | 0.968 | 20211.000 | -8.946 | nan | 0.879 | -1.429 |
| full | mlp | logV | calm | 11700 | 0.585 | nan | nan | -0.503 | 0.054 | 0.533 | 0.052 |
| full | mlp | logV | event | 9239 | -473.246 | nan | nan | -151.723 | 7672545807224251599895395800934111087178710777856.000 | 0.340 | -473.586 |
| full | mlp | logV | resolution | 6061 | -464.727 | nan | nan | -111.396 | 11671261737009542215428472832.000 | 0.162 | -464.889 |
| full | mlp | logV | all | 27000 | -177.365 | nan | nan | -83.865 | 2625431507886846605051483883675254532339880951808.000 | 0.593 | -177.958 |
| price_only | ridge | x | calm | 11700 | 0.536 | 0.955 | 6978.000 | nan | nan | 0.536 | nan |
| price_only | ridge | x | event | 9239 | 0.914 | 0.946 | 8156.000 | nan | nan | 0.914 | nan |
| price_only | ridge | x | resolution | 6061 | 0.872 | 0.983 | 5077.000 | nan | nan | 0.872 | nan |
| price_only | ridge | x | all | 27000 | 0.846 | 0.959 | 20211.000 | nan | nan | 0.846 | nan |
| price_only | ridge | logV | calm | 11700 | 0.042 | nan | nan | nan | 0.082 | 0.042 | nan |
| price_only | ridge | logV | event | 9239 | 0.335 | nan | nan | nan | 0.077 | 0.335 | nan |
| price_only | ridge | logV | resolution | 6061 | -0.153 | nan | nan | nan | 0.117 | -0.153 | nan |
| price_only | ridge | logV | all | 27000 | 0.406 | nan | nan | nan | 0.088 | 0.406 | nan |
| price_only | gbt | x | calm | 11700 | 0.787 | 0.961 | 6978.000 | nan | nan | 0.787 | nan |
| price_only | gbt | x | event | 9239 | 0.926 | 0.972 | 8156.000 | nan | nan | 0.926 | nan |
| price_only | gbt | x | resolution | 6061 | 0.872 | 0.978 | 5077.000 | nan | nan | 0.872 | nan |
| price_only | gbt | x | all | 27000 | 0.892 | 0.970 | 20211.000 | nan | nan | 0.892 | nan |
| price_only | gbt | logV | calm | 11700 | 0.634 | nan | nan | nan | 0.049 | 0.634 | nan |
| price_only | gbt | logV | event | 9239 | 0.425 | nan | nan | nan | 0.068 | 0.425 | nan |
| price_only | gbt | logV | resolution | 6061 | 0.353 | nan | nan | nan | 0.080 | 0.353 | nan |
| price_only | gbt | logV | all | 27000 | 0.670 | nan | nan | nan | 0.062 | 0.670 | nan |
| price_only | mlp | x | calm | 11700 | 0.746 | 0.954 | 6978.000 | nan | nan | 0.746 | nan |
| price_only | mlp | x | event | 9239 | 0.921 | 0.968 | 8156.000 | nan | nan | 0.921 | nan |
| price_only | mlp | x | resolution | 6061 | 0.857 | 0.976 | 5077.000 | nan | nan | 0.857 | nan |
| price_only | mlp | x | all | 27000 | 0.879 | 0.965 | 20211.000 | nan | nan | 0.879 | nan |
| price_only | mlp | logV | calm | 11700 | 0.533 | nan | nan | nan | 0.058 | 0.533 | nan |
| price_only | mlp | logV | event | 9239 | 0.340 | nan | nan | nan | 0.074 | 0.340 | nan |
| price_only | mlp | logV | resolution | 6061 | 0.162 | nan | nan | nan | 0.090 | 0.162 | nan |
| price_only | mlp | logV | all | 27000 | 0.593 | nan | nan | nan | 0.071 | 0.593 | nan |

## L2b composite phase clock

Macro-class accuracy: full 85.2%, price-only 78.3%, day-only 54.6%, majority class 43.3%. Selectivity = +6.9% vs margin 10% -> PASS.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 13320, majority 46.4%; accuracy price-only 75.3%, price+IV 78.0%, full 78.8%; recall of sustained-bull days: price-only 82.5%, price+IV 82.1%, full 85.1% (reported; no pre-registered threshold).

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 4000 | 0.115 | 0.828 | 0.717 | 0.596 |
| bull_trap | calm | 1720 | 0.149 | 0.913 | 0.848 | 0.763 |
| bull_trap | mania | 2826 | 0.135 | 0.905 | 0.815 | 0.686 |
| bull_trap | blow-off | 1395 | 0.582 | 0.993 | 0.986 | 0.981 |
| bull_trap | post-top | 1459 | 0.288 | 0.951 | 0.926 | 0.867 |
| crash | calm | 5316 | 0.137 | 0.902 | 0.824 | 0.726 |
| crash | deterioration | 2038 | 0.128 | 0.877 | 0.797 | 0.678 |
| crash | panic | 3244 | 0.259 | 0.962 | 0.936 | 0.887 |
| crash | stabilisation | 4602 | 0.170 | 0.880 | 0.810 | 0.731 |
| sustained_bull | sustained-bull | 3400 | 0.014 | 0.185 | 0.057 | 0.005 |
| flat | ALL | 4000 | 0.115 | 0.828 | 0.717 | 0.596 |
| bull_trap | ALL | 7400 | 0.206 | 0.932 | 0.877 | 0.795 |
| crash | ALL | 15200 | 0.166 | 0.905 | 0.840 | 0.755 |
| sustained_bull | ALL | 3400 | 0.014 | 0.185 | 0.057 | 0.005 |
