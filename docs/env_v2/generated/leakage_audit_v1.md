# Section 5 leakage / phase-clock / resolvability audit (v1, 30 seeds, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA60`, `trend_regime`, `RSI14`, `reported_PE`, `implied_volatility`, `volume_ratio`, `news_sentiment`; 30000 steps.

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|
| k * P / reported_PE | 15.0000 | 0.0016 | 0.0041 | 0.0000 | 0.8500 | False |
| k * P (price itself) | 1.0502 | 0.0502 | 2.0164 | 0.9031 | 0.8500 | False |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Calm: best R2(x) = 0.903, sign accuracy on resolvable steps = nan -> FAIL (criterion R2 <= 0.30, sign <= 0.70).  Event: best R2(x) = 1.000, MAPE(V) = 0.7% -> FAIL (criterion R2 < 0.90, MAPE >= 10%).

| feature_set | model | target | phase_group | n | R2 | sign_acc_resolvable | n_resolvable | R2_shuffledV | MAPE_V | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 7200 | -2.709 | nan | 0.000 | -0.083 | nan | -238.812 | 236.103 |
| full | ridge | x | event | 14400 | 0.993 | 1.000 | 12478.000 | 0.017 | nan | 0.926 | 0.066 |
| full | ridge | x | resolution | 5400 | 0.891 | 1.000 | 4350.000 | -0.017 | nan | -1.829 | 2.719 |
| full | ridge | x | all | 27000 | 0.991 | 1.000 | 16828.000 | 0.046 | nan | 0.855 | 0.136 |
| full | ridge | logV | calm | 7200 | 0.930 | nan | nan | -0.095 | 0.030 | 0.372 | 0.558 |
| full | ridge | logV | event | 14400 | 0.951 | nan | nan | 0.074 | 0.031 | 0.425 | 0.526 |
| full | ridge | logV | resolution | 5400 | 0.743 | nan | nan | -0.072 | 0.062 | -0.966 | 1.709 |
| full | ridge | logV | all | 27000 | 0.963 | nan | nan | 0.039 | 0.037 | 0.657 | 0.307 |
| full | gbt | x | calm | 7200 | 0.903 | nan | 0.000 | -0.290 | nan | -40.647 | 41.549 |
| full | gbt | x | event | 14400 | 1.000 | 1.000 | 12478.000 | -0.031 | nan | 0.981 | 0.018 |
| full | gbt | x | resolution | 5400 | 0.997 | 1.000 | 4350.000 | -0.261 | nan | 0.082 | 0.916 |
| full | gbt | x | all | 27000 | 1.000 | 1.000 | 16828.000 | -0.116 | nan | 0.964 | 0.035 |
| full | gbt | logV | calm | 7200 | 0.996 | nan | nan | -0.019 | 0.005 | 0.918 | 0.079 |
| full | gbt | logV | event | 14400 | 0.997 | nan | nan | -0.039 | 0.007 | 0.958 | 0.039 |
| full | gbt | logV | resolution | 5400 | 0.996 | nan | nan | -0.402 | 0.006 | 0.895 | 0.101 |
| full | gbt | logV | all | 27000 | 0.999 | nan | nan | -0.109 | 0.006 | 0.974 | 0.025 |
| full | mlp | x | calm | 7200 | -0.582 | nan | 0.000 | -0.275 | nan | -63.633 | 63.052 |
| full | mlp | x | event | 14400 | 1.000 | 1.000 | 12478.000 | -0.044 | nan | 0.977 | 0.022 |
| full | mlp | x | resolution | 5400 | 0.989 | 1.000 | 4350.000 | -0.134 | nan | 0.176 | 0.813 |
| full | mlp | x | all | 27000 | 0.999 | 1.000 | 16828.000 | -0.059 | nan | 0.958 | 0.042 |
| full | mlp | logV | calm | 7200 | 0.989 | nan | nan | -0.022 | 0.012 | 0.898 | 0.091 |
| full | mlp | logV | event | 14400 | 0.990 | nan | nan | -0.103 | 0.011 | 0.932 | 0.058 |
| full | mlp | logV | resolution | 5400 | 0.988 | nan | nan | -0.159 | 0.013 | 0.889 | 0.099 |
| full | mlp | logV | all | 27000 | 0.996 | nan | nan | -0.054 | 0.012 | 0.965 | 0.031 |
| price_only | ridge | x | calm | 7200 | -238.812 | nan | 0.000 | nan | nan | -238.812 | nan |
| price_only | ridge | x | event | 14400 | 0.926 | 0.997 | 12478.000 | nan | nan | 0.926 | nan |
| price_only | ridge | x | resolution | 5400 | -1.829 | 1.000 | 4350.000 | nan | nan | -1.829 | nan |
| price_only | ridge | x | all | 27000 | 0.855 | 0.998 | 16828.000 | nan | nan | 0.855 | nan |
| price_only | ridge | logV | calm | 7200 | 0.372 | nan | nan | nan | 0.100 | 0.372 | nan |
| price_only | ridge | logV | event | 14400 | 0.425 | nan | nan | nan | 0.116 | 0.425 | nan |
| price_only | ridge | logV | resolution | 5400 | -0.966 | nan | nan | nan | 0.218 | -0.966 | nan |
| price_only | ridge | logV | all | 27000 | 0.657 | nan | nan | nan | 0.132 | 0.657 | nan |
| price_only | gbt | x | calm | 7200 | -40.647 | nan | 0.000 | nan | nan | -40.647 | nan |
| price_only | gbt | x | event | 14400 | 0.981 | 1.000 | 12478.000 | nan | nan | 0.981 | nan |
| price_only | gbt | x | resolution | 5400 | 0.082 | 1.000 | 4350.000 | nan | nan | 0.082 | nan |
| price_only | gbt | x | all | 27000 | 0.964 | 1.000 | 16828.000 | nan | nan | 0.964 | nan |
| price_only | gbt | logV | calm | 7200 | 0.918 | nan | nan | nan | 0.018 | 0.918 | nan |
| price_only | gbt | logV | event | 14400 | 0.958 | nan | nan | nan | 0.028 | 0.958 | nan |
| price_only | gbt | logV | resolution | 5400 | 0.895 | nan | nan | nan | 0.044 | 0.895 | nan |
| price_only | gbt | logV | all | 27000 | 0.974 | nan | nan | nan | 0.028 | 0.974 | nan |
| price_only | mlp | x | calm | 7200 | -63.633 | nan | 0.000 | nan | nan | -63.633 | nan |
| price_only | mlp | x | event | 14400 | 0.977 | 1.000 | 12478.000 | nan | nan | 0.977 | nan |
| price_only | mlp | x | resolution | 5400 | 0.176 | 1.000 | 4350.000 | nan | nan | 0.176 | nan |
| price_only | mlp | x | all | 27000 | 0.958 | 1.000 | 16828.000 | nan | nan | 0.958 | nan |
| price_only | mlp | logV | calm | 7200 | 0.898 | nan | nan | nan | 0.031 | 0.898 | nan |
| price_only | mlp | logV | event | 14400 | 0.932 | nan | nan | nan | 0.035 | 0.932 | nan |
| price_only | mlp | logV | resolution | 5400 | 0.889 | nan | nan | nan | 0.045 | 0.889 | nan |
| price_only | mlp | logV | all | 27000 | 0.965 | nan | nan | nan | 0.036 | 0.965 | nan |

## L2b composite phase clock

Macro-class accuracy: full 99.8%, price-only 94.9%, day-only 60.0%, majority class 40.0%. Selectivity = +5.0% vs margin 10% -> PASS.

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 6000 | 0.002 | 0.000 | 0.000 | 0.000 |
| bull_trap | calm | 2400 | 0.006 | 0.002 | 0.000 | 0.000 |
| bull_trap | mania | 1800 | 0.343 | 0.966 | 0.942 | 0.900 |
| bull_trap | blow-off | 1800 | 0.677 | 1.000 | 1.000 | 1.000 |
| crash | deterioration | 7200 | 0.085 | 0.968 | 0.842 | 0.547 |
| crash | panic | 5400 | 0.087 | 0.940 | 0.822 | 0.556 |
| crash | stabilisation | 5400 | 0.089 | 0.923 | 0.806 | 0.570 |
| flat | ALL | 6000 | 0.002 | 0.000 | 0.000 | 0.000 |
| bull_trap | ALL | 6000 | 0.243 | 0.590 | 0.582 | 0.570 |
| crash | ALL | 18000 | 0.087 | 0.946 | 0.825 | 0.556 |
