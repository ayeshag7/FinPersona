# Section 5 leakage / phase-clock / resolvability audit (v2, 20 seeds, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 30000 steps.

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|
| k * P (price itself) | 1.0422 | 0.1305 | 2.1840 | 0.9661 | 0.6726 | True |
| k * P * dividend_yield | 0.5200 | 0.1625 | 0.7843 | 0.9666 | 0.6726 | True |
| k * P / reported_PE | 18.1296 | 0.1639 | 0.7728 | 0.9801 | 0.6726 | True |
| k * analyst_fair_value | 1.0254 | 0.2699 | 1.5535 | 0.9805 | 0.6726 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.931, sign accuracy on resolvable steps = 0.983 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.974, MAPE(V) = 4.1% -> FAIL (R2 < 0.90, MAPE >= 10%).

Selectivity (amendment A8, gating): max R2(x) gain of the full set over price-only = 0.103 (<= 0.2), max MAPE(V) gain = 2.2% (<= 5%), max shuffled-V R2 = -0.004 (< 0.1) -> PASS.

| feature_set | model | target | phase_group | n | R2 | sign_acc_resolvable | n_resolvable | R2_shuffledV | MAPE_V | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 11099 | 0.610 | 0.942 | 5923.000 | -0.043 | nan | 0.479 | 0.131 |
| full | ridge | x | event | 9348 | 0.926 | 0.962 | 8097.000 | -0.055 | nan | 0.912 | 0.013 |
| full | ridge | x | resolution | 6553 | 0.890 | 0.988 | 5625.000 | -0.065 | nan | 0.847 | 0.043 |
| full | ridge | x | all | 27000 | 0.878 | 0.964 | 19645.000 | -0.050 | nan | 0.842 | 0.035 |
| full | ridge | logV | calm | 11099 | 0.403 | nan | nan | -0.004 | 0.068 | 0.187 | 0.217 |
| full | ridge | logV | event | 9348 | 0.315 | nan | nan | -0.029 | 0.075 | 0.266 | 0.048 |
| full | ridge | logV | resolution | 6553 | 0.402 | nan | nan | -0.059 | 0.085 | 0.028 | 0.373 |
| full | ridge | logV | all | 27000 | 0.607 | nan | nan | -0.022 | 0.075 | 0.475 | 0.132 |
| full | gbt | x | calm | 11099 | 0.931 | 0.983 | 5923.000 | -0.165 | nan | 0.828 | 0.103 |
| full | gbt | x | event | 9348 | 0.974 | 0.992 | 8097.000 | -0.223 | nan | 0.948 | 0.026 |
| full | gbt | x | resolution | 6553 | 0.941 | 0.988 | 5625.000 | -0.326 | nan | 0.882 | 0.059 |
| full | gbt | x | all | 27000 | 0.962 | 0.988 | 19645.000 | -0.236 | nan | 0.919 | 0.043 |
| full | gbt | logV | calm | 11099 | 0.907 | nan | nan | -0.208 | 0.021 | 0.735 | 0.172 |
| full | gbt | logV | event | 9348 | 0.760 | nan | nan | -0.279 | 0.041 | 0.538 | 0.222 |
| full | gbt | logV | resolution | 6553 | 0.773 | nan | nan | -0.307 | 0.047 | 0.566 | 0.207 |
| full | gbt | logV | all | 27000 | 0.890 | nan | nan | -0.252 | 0.035 | 0.766 | 0.124 |
| full | mlp | x | calm | 11099 | 0.888 | 0.975 | 5923.000 | -0.479 | nan | 0.810 | 0.078 |
| full | mlp | x | event | 9348 | 0.954 | 0.985 | 8097.000 | -0.754 | nan | 0.947 | 0.007 |
| full | mlp | x | resolution | 6553 | 0.889 | 0.986 | 5625.000 | -0.758 | nan | 0.874 | 0.015 |
| full | mlp | x | all | 27000 | 0.932 | 0.982 | 19645.000 | -0.666 | nan | 0.914 | 0.018 |
| full | mlp | logV | calm | 11099 | 0.690 | nan | nan | -0.435 | 0.048 | 0.626 | 0.064 |
| full | mlp | logV | event | 9348 | 0.318 | nan | nan | -0.709 | 0.069 | 0.450 | -0.132 |
| full | mlp | logV | resolution | 6553 | 0.238 | nan | nan | -0.741 | 0.085 | 0.435 | -0.196 |
| full | mlp | logV | all | 27000 | 0.655 | nan | nan | -0.604 | 0.064 | 0.697 | -0.042 |
| price_only | ridge | x | calm | 11099 | 0.479 | 0.944 | 5923.000 | nan | nan | 0.479 | nan |
| price_only | ridge | x | event | 9348 | 0.912 | 0.951 | 8097.000 | nan | nan | 0.912 | nan |
| price_only | ridge | x | resolution | 6553 | 0.847 | 0.983 | 5625.000 | nan | nan | 0.847 | nan |
| price_only | ridge | x | all | 27000 | 0.842 | 0.958 | 19645.000 | nan | nan | 0.842 | nan |
| price_only | ridge | logV | calm | 11099 | 0.187 | nan | nan | nan | 0.079 | 0.187 | nan |
| price_only | ridge | logV | event | 9348 | 0.266 | nan | nan | nan | 0.078 | 0.266 | nan |
| price_only | ridge | logV | resolution | 6553 | 0.028 | nan | nan | nan | 0.114 | 0.028 | nan |
| price_only | ridge | logV | all | 27000 | 0.475 | nan | nan | nan | 0.087 | 0.475 | nan |
| price_only | gbt | x | calm | 11099 | 0.828 | 0.979 | 5923.000 | nan | nan | 0.828 | nan |
| price_only | gbt | x | event | 9348 | 0.948 | 0.983 | 8097.000 | nan | nan | 0.948 | nan |
| price_only | gbt | x | resolution | 6553 | 0.882 | 0.986 | 5625.000 | nan | nan | 0.882 | nan |
| price_only | gbt | x | all | 27000 | 0.919 | 0.983 | 19645.000 | nan | nan | 0.919 | nan |
| price_only | gbt | logV | calm | 11099 | 0.735 | nan | nan | nan | 0.038 | 0.735 | nan |
| price_only | gbt | logV | event | 9348 | 0.538 | nan | nan | nan | 0.059 | 0.538 | nan |
| price_only | gbt | logV | resolution | 6553 | 0.566 | nan | nan | nan | 0.069 | 0.566 | nan |
| price_only | gbt | logV | all | 27000 | 0.766 | nan | nan | nan | 0.053 | 0.766 | nan |
| price_only | mlp | x | calm | 11099 | 0.810 | 0.970 | 5923.000 | nan | nan | 0.810 | nan |
| price_only | mlp | x | event | 9348 | 0.947 | 0.981 | 8097.000 | nan | nan | 0.947 | nan |
| price_only | mlp | x | resolution | 6553 | 0.874 | 0.983 | 5625.000 | nan | nan | 0.874 | nan |
| price_only | mlp | x | all | 27000 | 0.914 | 0.978 | 19645.000 | nan | nan | 0.914 | nan |
| price_only | mlp | logV | calm | 11099 | 0.626 | nan | nan | nan | 0.053 | 0.626 | nan |
| price_only | mlp | logV | event | 9348 | 0.450 | nan | nan | nan | 0.066 | 0.450 | nan |
| price_only | mlp | logV | resolution | 6553 | 0.435 | nan | nan | nan | 0.079 | 0.435 | nan |
| price_only | mlp | logV | all | 27000 | 0.697 | nan | nan | nan | 0.064 | 0.697 | nan |

## L2b composite phase clock

Macro-class accuracy: full 88.6%, price-only 81.1%, day-only 51.5%, majority class 41.1%. Selectivity = +7.5% vs margin 10% -> PASS.

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 3800 | 0.117 | 0.867 | 0.776 | 0.656 |
| bull_trap | calm | 1537 | 0.125 | 0.891 | 0.813 | 0.700 |
| bull_trap | mania | 2836 | 0.149 | 0.909 | 0.833 | 0.727 |
| bull_trap | blow-off | 1397 | 0.588 | 0.999 | 0.999 | 0.996 |
| bull_trap | post-top | 1630 | 0.198 | 0.907 | 0.844 | 0.762 |
| sustained_bull | sustained-bull | 3800 | 0.008 | 0.063 | 0.014 | 0.002 |
| crash | calm | 4635 | 0.123 | 0.904 | 0.821 | 0.704 |
| crash | deterioration | 2132 | 0.122 | 0.878 | 0.790 | 0.661 |
| crash | panic | 3263 | 0.261 | 0.961 | 0.933 | 0.876 |
| crash | stabilisation | 4970 | 0.191 | 0.913 | 0.866 | 0.797 |
| flat | ALL | 3800 | 0.117 | 0.867 | 0.776 | 0.656 |
| bull_trap | ALL | 7400 | 0.198 | 0.922 | 0.862 | 0.780 |
| sustained_bull | ALL | 3800 | 0.008 | 0.063 | 0.014 | 0.002 |
| crash | ALL | 15000 | 0.165 | 0.916 | 0.856 | 0.766 |
