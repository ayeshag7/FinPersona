# Section 5 leakage / phase-clock / resolvability audit (v2, 50 seeds, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 30000 steps.

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|
| k * P (price itself) | 1.0506 | 0.1236 | 2.3639 | 0.9592 | 0.6872 | True |
| k * P / reported_PE | 17.5239 | 0.1546 | 0.7136 | 0.9717 | 0.6872 | True |
| k * P * dividend_yield | 0.5019 | 0.1558 | 0.7224 | 0.9706 | 0.6872 | True |
| k * analyst_fair_value | 0.9839 | 0.2235 | 1.5688 | 0.9762 | 0.6872 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.898, sign accuracy on resolvable steps = 0.969 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.961, MAPE(V) = 4.9% -> FAIL (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.111 (worst phase group), MAPE(V) gain = 2.9%, max shuffled-V R2 = -0.060. Interpretation: the absolute fail is a property of the price process (smooth V, persistent dominant x -> x is inferable from price history), not of the valuation fields; 'hidden value' is hidden from algebra and from the fields, NOT from price dynamics -- the rule-based baselines quantify how much a price-only policy captures.

| feature_set | model | target | phase_group | n | R2 | sign_acc_resolvable | n_resolvable | R2_shuffledV | MAPE_V | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 11700 | 0.637 | 0.930 | 6978.000 | -0.063 | nan | 0.536 | 0.101 |
| full | ridge | x | event | 9239 | 0.906 | 0.955 | 8156.000 | -4.340 | nan | 0.914 | -0.008 |
| full | ridge | x | resolution | 6061 | 0.852 | 0.982 | 5077.000 | -2.562 | nan | 0.872 | -0.021 |
| full | ridge | x | all | 27000 | 0.852 | 0.953 | 20211.000 | -2.269 | nan | 0.846 | 0.006 |
| full | ridge | logV | calm | 11700 | 0.308 | nan | nan | -0.060 | 0.070 | 0.042 | 0.267 |
| full | ridge | logV | event | 9239 | -2.044 | nan | nan | -0.273 | 0.071 | 0.335 | -2.380 |
| full | ridge | logV | resolution | 6061 | -2.256 | nan | nan | -0.241 | 0.091 | -0.153 | -2.103 |
| full | ridge | logV | all | 27000 | -0.378 | nan | nan | -0.170 | 0.075 | 0.406 | -0.784 |
| full | gbt | x | calm | 11700 | 0.898 | 0.969 | 6978.000 | -0.279 | nan | 0.787 | 0.111 |
| full | gbt | x | event | 9239 | 0.961 | 0.977 | 8156.000 | -0.254 | nan | 0.926 | 0.034 |
| full | gbt | x | resolution | 6061 | 0.942 | 0.986 | 5077.000 | -0.227 | nan | 0.872 | 0.070 |
| full | gbt | x | all | 27000 | 0.947 | 0.976 | 20211.000 | -0.248 | nan | 0.892 | 0.055 |
| full | gbt | logV | calm | 11700 | 0.805 | nan | nan | -0.175 | 0.035 | 0.634 | 0.171 |
| full | gbt | logV | event | 9239 | 0.690 | nan | nan | -0.258 | 0.049 | 0.425 | 0.266 |
| full | gbt | logV | resolution | 6061 | 0.711 | nan | nan | -0.215 | 0.051 | 0.353 | 0.358 |
| full | gbt | logV | all | 27000 | 0.832 | nan | nan | -0.198 | 0.044 | 0.670 | 0.162 |
| full | mlp | x | calm | 11700 | 0.795 | 0.961 | 6978.000 | -0.603 | nan | 0.746 | 0.048 |
| full | mlp | x | event | 9239 | 0.290 | 0.961 | 8156.000 | -43.111 | nan | 0.921 | -0.631 |
| full | mlp | x | resolution | 6061 | -0.313 | 0.974 | 5077.000 | -24.578 | nan | 0.857 | -1.170 |
| full | mlp | x | all | 27000 | 0.222 | 0.964 | 20211.000 | -22.282 | nan | 0.879 | -0.656 |
| full | mlp | logV | calm | 11700 | 0.499 | nan | nan | -0.513 | 0.059 | 0.533 | -0.034 |
| full | mlp | logV | event | 9239 | -422.581 | nan | nan | -197.702 | 104850073621555412592114768877191168.000 | 0.340 | -422.920 |
| full | mlp | logV | resolution | 6061 | -523.611 | nan | nan | -121.914 | 5008417609897018803457984908390039552.000 | 0.162 | -523.773 |
| full | mlp | logV | all | 27000 | -175.523 | nan | nan | -101.821 | 1160175146806495552750284395109154816.000 | 0.593 | -176.116 |
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

Macro-class accuracy: full 84.9%, price-only 78.3%, day-only 54.6%, majority class 43.3%. Selectivity = +6.6% vs margin 10% -> PASS.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 13320, majority 46.4%; accuracy price-only 75.3%, price+IV 78.0%, full 78.0%; recall of sustained-bull days: price-only 82.5%, price+IV 82.1%, full 84.0% (reported; no pre-registered threshold).

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
