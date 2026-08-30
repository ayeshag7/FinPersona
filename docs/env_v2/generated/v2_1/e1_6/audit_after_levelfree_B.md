# Section 5 leakage / phase-clock / resolvability audit (v2, stored panel sep_after.pkl, 1600 paths, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): LEVEL-FREE (returns, log P/SMA, RSI, MACD/P, trend; no price level -- v2.1 Phase 1, E1.6). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * analyst_fair_value | 0.9941 | 0.1051 | 0.7160 | 0.0101 | 0.0196 | 0.0489 | 0.0497 | 0.1028 | 0.2561 | 0.9503 | 0.7282 | True |
| k * P (price itself) | 1.0091 | 0.1257 | 2.3720 | 0.0071 | 0.0147 | 0.0440 | 0.0696 | 0.1337 | 0.2730 | 0.9304 | 0.7282 | True |
| k * P * dividend_yield | 0.5182 | 0.1351 | 0.8572 | 0.0137 | 0.0277 | 0.0695 | 0.0368 | 0.0732 | 0.1783 | 0.9632 | 0.7282 | True |
| k * P / reported_PE | 17.9463 | 0.1372 | 0.9336 | 0.0135 | 0.0276 | 0.0685 | 0.0373 | 0.0729 | 0.1832 | 0.9627 | 0.7282 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.811, sign accuracy on resolvable steps = 0.900 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.944, MAPE(V) = 6.5% -> FAIL (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.728 (worst phase group), MAPE(V) gain = 13.7%, max shuffled-V R2 = -0.003. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119663 | 0.568 | 0.508 | 0.620 | 0.877 | 65439.000 | 0.862 | 0.890 | -0.003 | nan | nan | nan | -0.000 | 0.568 |
| full | ridge | x | event | 94915 | 0.894 | 0.886 | 0.901 | 0.939 | 82348.000 | 0.933 | 0.944 | -0.003 | nan | nan | nan | 0.634 | 0.260 |
| full | ridge | x | resolution | 73422 | 0.889 | 0.878 | 0.899 | 0.968 | 64304.000 | 0.962 | 0.974 | -0.004 | nan | nan | nan | 0.144 | 0.745 |
| full | ridge | x | all | 288000 | 0.852 | 0.841 | 0.861 | 0.928 | 212091.000 | 0.923 | 0.934 | -0.003 | nan | nan | nan | 0.410 | 0.441 |
| full | ridge | logV | calm | 119663 | 0.727 | 0.693 | 0.756 | nan | nan | nan | nan | -0.004 | 0.083 | 0.080 | 0.086 | 0.093 | 0.634 |
| full | ridge | logV | event | 94915 | 0.761 | 0.735 | 0.784 | nan | nan | nan | nan | -0.004 | 0.090 | 0.087 | 0.094 | 0.324 | 0.437 |
| full | ridge | logV | resolution | 73422 | 0.713 | 0.683 | 0.739 | nan | nan | nan | nan | -0.007 | 0.098 | 0.094 | 0.103 | -0.361 | 1.074 |
| full | ridge | logV | all | 288000 | 0.777 | 0.762 | 0.790 | nan | nan | nan | nan | -0.004 | 0.089 | 0.087 | 0.092 | 0.204 | 0.573 |
| full | gbt | x | calm | 119663 | 0.811 | 0.786 | 0.834 | 0.900 | 65439.000 | 0.887 | 0.912 | -0.022 | nan | nan | nan | 0.083 | 0.728 |
| full | gbt | x | event | 94915 | 0.944 | 0.940 | 0.948 | 0.945 | 82348.000 | 0.939 | 0.950 | -0.040 | nan | nan | nan | 0.680 | 0.264 |
| full | gbt | x | resolution | 73422 | 0.944 | 0.938 | 0.949 | 0.978 | 64304.000 | 0.973 | 0.984 | -0.051 | nan | nan | nan | 0.408 | 0.536 |
| full | gbt | x | all | 288000 | 0.928 | 0.923 | 0.932 | 0.941 | 212091.000 | 0.936 | 0.946 | -0.037 | nan | nan | nan | 0.527 | 0.401 |
| full | gbt | logV | calm | 119663 | 0.896 | 0.882 | 0.908 | nan | nan | nan | nan | -0.028 | 0.049 | 0.047 | 0.051 | 0.197 | 0.699 |
| full | gbt | logV | event | 94915 | 0.877 | 0.862 | 0.891 | nan | nan | nan | nan | -0.035 | 0.065 | 0.063 | 0.067 | 0.343 | 0.534 |
| full | gbt | logV | resolution | 73422 | 0.903 | 0.892 | 0.913 | nan | nan | nan | nan | -0.065 | 0.056 | 0.054 | 0.058 | -0.096 | 0.998 |
| full | gbt | logV | all | 288000 | 0.908 | 0.900 | 0.915 | nan | nan | nan | nan | -0.040 | 0.056 | 0.055 | 0.058 | 0.301 | 0.606 |
| full | mlp | x | calm | 119663 | 0.754 | 0.723 | 0.780 | 0.910 | 65439.000 | 0.901 | 0.920 | -0.142 | nan | nan | nan | 0.075 | 0.679 |
| full | mlp | x | event | 94915 | 0.908 | 0.890 | 0.920 | 0.946 | 82348.000 | 0.941 | 0.950 | -0.161 | nan | nan | nan | 0.708 | 0.200 |
| full | mlp | x | resolution | 73422 | 0.900 | 0.891 | 0.909 | 0.975 | 64304.000 | 0.970 | 0.980 | -0.229 | nan | nan | nan | 0.510 | 0.390 |
| full | mlp | x | all | 288000 | 0.888 | 0.877 | 0.896 | 0.944 | 212091.000 | 0.939 | 0.948 | -0.177 | nan | nan | nan | 0.571 | 0.316 |
| full | mlp | logV | calm | 119663 | 0.852 | 0.833 | 0.869 | nan | nan | nan | nan | -0.122 | 0.059 | 0.057 | 0.062 | 0.210 | 0.642 |
| full | mlp | logV | event | 94915 | 0.802 | 0.757 | 0.838 | nan | nan | nan | nan | -0.164 | 0.191 | 0.078 | 0.420 | 0.354 | 0.447 |
| full | mlp | logV | resolution | 73422 | 0.843 | 0.822 | 0.860 | nan | nan | nan | nan | -0.213 | 0.071 | 0.069 | 0.074 | -0.041 | 0.883 |
| full | mlp | logV | all | 288000 | 0.857 | 0.840 | 0.872 | nan | nan | nan | nan | -0.162 | 0.106 | 0.068 | 0.180 | 0.321 | 0.536 |
| price_only | ridge | x | calm | 119663 | -0.000 | -0.044 | 0.038 | 0.577 | 65439.000 | 0.559 | 0.594 | nan | nan | nan | nan | -0.000 | nan |
| price_only | ridge | x | event | 94915 | 0.634 | 0.614 | 0.655 | 0.836 | 82348.000 | 0.826 | 0.846 | nan | nan | nan | nan | 0.634 | nan |
| price_only | ridge | x | resolution | 73422 | 0.144 | -0.034 | 0.243 | 0.630 | 64304.000 | 0.617 | 0.645 | nan | nan | nan | nan | 0.144 | nan |
| price_only | ridge | x | all | 288000 | 0.410 | 0.356 | 0.449 | 0.694 | 212091.000 | 0.685 | 0.702 | nan | nan | nan | nan | 0.410 | nan |
| price_only | ridge | logV | calm | 119663 | 0.093 | 0.046 | 0.137 | nan | nan | nan | nan | nan | 0.146 | 0.141 | 0.151 | 0.093 | nan |
| price_only | ridge | logV | event | 94915 | 0.324 | 0.282 | 0.362 | nan | nan | nan | nan | nan | 0.151 | 0.144 | 0.158 | 0.324 | nan |
| price_only | ridge | logV | resolution | 73422 | -0.361 | -0.844 | -0.120 | nan | nan | nan | nan | nan | 0.215 | 0.206 | 0.226 | -0.361 | nan |
| price_only | ridge | logV | all | 288000 | 0.204 | 0.104 | 0.262 | nan | nan | nan | nan | nan | 0.165 | 0.160 | 0.170 | 0.204 | nan |
| price_only | gbt | x | calm | 119663 | 0.083 | 0.040 | 0.119 | 0.567 | 65439.000 | 0.547 | 0.585 | nan | nan | nan | nan | 0.083 | nan |
| price_only | gbt | x | event | 94915 | 0.680 | 0.659 | 0.701 | 0.821 | 82348.000 | 0.811 | 0.831 | nan | nan | nan | nan | 0.680 | nan |
| price_only | gbt | x | resolution | 73422 | 0.408 | 0.380 | 0.435 | 0.766 | 64304.000 | 0.753 | 0.781 | nan | nan | nan | nan | 0.408 | nan |
| price_only | gbt | x | all | 288000 | 0.527 | 0.505 | 0.546 | 0.726 | 212091.000 | 0.717 | 0.735 | nan | nan | nan | nan | 0.527 | nan |
| price_only | gbt | logV | calm | 119663 | 0.197 | 0.155 | 0.238 | nan | nan | nan | nan | nan | 0.136 | 0.131 | 0.141 | 0.197 | nan |
| price_only | gbt | logV | event | 94915 | 0.343 | 0.309 | 0.374 | nan | nan | nan | nan | nan | 0.147 | 0.141 | 0.155 | 0.343 | nan |
| price_only | gbt | logV | resolution | 73422 | -0.096 | -0.153 | -0.043 | nan | nan | nan | nan | nan | 0.203 | 0.195 | 0.214 | -0.096 | nan |
| price_only | gbt | logV | all | 288000 | 0.301 | 0.282 | 0.319 | nan | nan | nan | nan | nan | 0.157 | 0.153 | 0.162 | 0.301 | nan |
| price_only | mlp | x | calm | 119663 | 0.075 | 0.020 | 0.118 | 0.596 | 65439.000 | 0.581 | 0.611 | nan | nan | nan | nan | 0.075 | nan |
| price_only | mlp | x | event | 94915 | 0.708 | 0.685 | 0.731 | 0.831 | 82348.000 | 0.822 | 0.840 | nan | nan | nan | nan | 0.708 | nan |
| price_only | mlp | x | resolution | 73422 | 0.510 | 0.477 | 0.538 | 0.788 | 64304.000 | 0.777 | 0.801 | nan | nan | nan | nan | 0.510 | nan |
| price_only | mlp | x | all | 288000 | 0.571 | 0.545 | 0.593 | 0.746 | 212091.000 | 0.737 | 0.754 | nan | nan | nan | nan | 0.571 | nan |
| price_only | mlp | logV | calm | 119663 | 0.210 | 0.165 | 0.252 | nan | nan | nan | nan | nan | 0.135 | 0.130 | 0.139 | 0.210 | nan |
| price_only | mlp | logV | event | 94915 | 0.354 | 0.315 | 0.390 | nan | nan | nan | nan | nan | 0.145 | 0.139 | 0.152 | 0.354 | nan |
| price_only | mlp | logV | resolution | 73422 | -0.041 | -0.125 | 0.019 | nan | nan | nan | nan | nan | 0.193 | 0.184 | 0.204 | -0.041 | nan |
| price_only | mlp | logV | all | 288000 | 0.321 | 0.295 | 0.343 | nan | nan | nan | nan | nan | 0.153 | 0.149 | 0.158 | 0.321 | nan |

## L2b composite phase clock

Macro-class accuracy: full 87.3%, price-only 72.2%, day-only 53.5%, majority class 41.5%. Selectivity = +15.1% vs margin 10% -> FAIL.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 47.0%; accuracy price-only 73.9%, price+IV 78.2%, full 82.5%; recall of sustained-bull days: price-only 75.9%, price+IV 77.7%, full 85.8% (reported; no pre-registered threshold).

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 40000 | 0.112 | 0.863 | 0.764 | 0.630 |
| bull_trap | calm | 18375 | 0.110 | 0.864 | 0.757 | 0.618 |
| bull_trap | mania | 28016 | 0.178 | 0.907 | 0.847 | 0.759 |
| bull_trap | blow-off | 13813 | 0.606 | 0.998 | 0.996 | 0.994 |
| bull_trap | post-top | 19796 | 0.263 | 0.941 | 0.903 | 0.842 |
| sustained_bull | sustained-bull | 40000 | 0.014 | 0.173 | 0.046 | 0.005 |
| crash | calm | 50322 | 0.104 | 0.865 | 0.753 | 0.603 |
| crash | deterioration | 22112 | 0.108 | 0.851 | 0.749 | 0.620 |
| crash | panic | 33940 | 0.209 | 0.937 | 0.893 | 0.823 |
| crash | stabilisation | 53626 | 0.179 | 0.919 | 0.866 | 0.782 |
| flat | ALL | 40000 | 0.112 | 0.863 | 0.764 | 0.630 |
| bull_trap | ALL | 80000 | 0.219 | 0.921 | 0.866 | 0.788 |
| sustained_bull | ALL | 40000 | 0.014 | 0.173 | 0.046 | 0.005 |
| crash | ALL | 160000 | 0.147 | 0.896 | 0.820 | 0.712 |
