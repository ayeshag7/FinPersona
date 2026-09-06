# Section 5 leakage / phase-clock / resolvability audit (v2, stored panel sep_phase4_after.pkl, 1600 paths, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): LEVEL-FREE (returns, log P/SMA, RSI, MACD/P, trend; no price level -- v2.1 Phase 1, E1.6). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * P (price itself) | 0.9992 | 0.0572 | 1.7406 | 0.0040 | 0.0081 | 0.0218 | 0.1226 | 0.2326 | 0.4602 | 0.8774 | 0.6613 | True |
| k * P * dividend_yield | 0.5146 | 0.1617 | 1.4914 | 0.0153 | 0.0301 | 0.0759 | 0.0318 | 0.0661 | 0.1671 | 0.9682 | 0.6613 | True |
| k * P / reported_PE | 17.8403 | 0.1638 | 1.4345 | 0.0156 | 0.0303 | 0.0775 | 0.0314 | 0.0651 | 0.1640 | 0.9686 | 0.6613 | True |
| k * analyst_fair_value | 2.3176 | 0.6759 | 6.9046 | 0.0855 | 0.1752 | 0.4039 | 0.0056 | 0.0119 | 0.0298 | 0.9944 | 0.6613 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.226, sign accuracy on resolvable steps = 0.824 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.858, MAPE(V) = 11.4% -> PASS (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.688 (worst phase group), MAPE(V) gain = 4.8%, max shuffled-V R2 = -0.002. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119588 | -1.177 | -1.456 | -0.943 | 0.756 | 33009.000 | 0.738 | 0.773 | -0.005 | nan | nan | nan | -0.462 | -0.715 |
| full | ridge | x | event | 95420 | 0.674 | 0.652 | 0.696 | 0.922 | 76532.000 | 0.915 | 0.929 | -0.005 | nan | nan | nan | 0.399 | 0.274 |
| full | ridge | x | resolution | 72992 | 0.600 | 0.561 | 0.631 | 0.874 | 52302.000 | 0.865 | 0.885 | -0.009 | nan | nan | nan | 0.119 | 0.480 |
| full | ridge | x | all | 288000 | 0.604 | 0.583 | 0.620 | 0.873 | 161843.000 | 0.866 | 0.879 | -0.002 | nan | nan | nan | 0.364 | 0.240 |
| full | ridge | logV | calm | 119588 | 0.357 | 0.309 | 0.405 | nan | nan | nan | nan | -0.004 | 0.110 | 0.106 | 0.114 | 0.219 | 0.138 |
| full | ridge | logV | event | 95420 | 0.464 | 0.406 | 0.513 | nan | nan | nan | nan | -0.010 | 0.130 | 0.125 | 0.136 | 0.394 | 0.070 |
| full | ridge | logV | resolution | 72992 | 0.301 | 0.243 | 0.345 | nan | nan | nan | nan | -0.004 | 0.150 | 0.143 | 0.158 | -0.233 | 0.534 |
| full | ridge | logV | all | 288000 | 0.513 | 0.491 | 0.534 | nan | nan | nan | nan | -0.005 | 0.127 | 0.124 | 0.130 | 0.338 | 0.176 |
| full | gbt | x | calm | 119588 | 0.226 | 0.162 | 0.282 | 0.824 | 33009.000 | 0.809 | 0.838 | -0.043 | nan | nan | nan | -0.662 | 0.888 |
| full | gbt | x | event | 95420 | 0.858 | 0.848 | 0.868 | 0.941 | 76532.000 | 0.936 | 0.947 | -0.062 | nan | nan | nan | 0.436 | 0.422 |
| full | gbt | x | resolution | 72992 | 0.760 | 0.733 | 0.783 | 0.911 | 52302.000 | 0.903 | 0.920 | -0.055 | nan | nan | nan | 0.317 | 0.442 |
| full | gbt | x | all | 288000 | 0.821 | 0.811 | 0.830 | 0.908 | 161843.000 | 0.903 | 0.913 | -0.048 | nan | nan | nan | 0.421 | 0.400 |
| full | gbt | logV | calm | 119588 | 0.495 | 0.459 | 0.535 | nan | nan | nan | nan | -0.036 | 0.097 | 0.093 | 0.100 | 0.294 | 0.201 |
| full | gbt | logV | event | 95420 | 0.568 | 0.525 | 0.609 | nan | nan | nan | nan | -0.072 | 0.114 | 0.110 | 0.119 | 0.385 | 0.183 |
| full | gbt | logV | resolution | 72992 | 0.470 | 0.419 | 0.509 | nan | nan | nan | nan | -0.057 | 0.127 | 0.120 | 0.134 | 0.040 | 0.430 |
| full | gbt | logV | all | 288000 | 0.619 | 0.597 | 0.639 | nan | nan | nan | nan | -0.054 | 0.110 | 0.107 | 0.113 | 0.416 | 0.203 |
| full | mlp | x | calm | 119588 | -0.406 | -0.638 | -0.229 | 0.835 | 33009.000 | 0.820 | 0.847 | -0.148 | nan | nan | nan | -0.803 | 0.397 |
| full | mlp | x | event | 95420 | 0.767 | 0.750 | 0.786 | 0.932 | 76532.000 | 0.926 | 0.939 | -0.195 | nan | nan | nan | 0.481 | 0.286 |
| full | mlp | x | resolution | 72992 | 0.707 | 0.677 | 0.735 | 0.908 | 52302.000 | 0.899 | 0.917 | -0.150 | nan | nan | nan | 0.337 | 0.370 |
| full | mlp | x | all | 288000 | 0.723 | 0.707 | 0.739 | 0.905 | 161843.000 | 0.900 | 0.910 | -0.157 | nan | nan | nan | 0.446 | 0.277 |
| full | mlp | logV | calm | 119588 | 0.452 | 0.415 | 0.494 | nan | nan | nan | nan | -0.137 | 0.100 | 0.096 | 0.103 | 0.326 | 0.126 |
| full | mlp | logV | event | 95420 | 0.510 | 0.457 | 0.558 | nan | nan | nan | nan | -0.163 | 0.121 | 0.116 | 0.126 | 0.371 | 0.139 |
| full | mlp | logV | resolution | 72992 | 0.417 | 0.365 | 0.461 | nan | nan | nan | nan | -0.139 | 0.132 | 0.126 | 0.138 | 0.037 | 0.380 |
| full | mlp | logV | all | 288000 | 0.578 | 0.555 | 0.601 | nan | nan | nan | nan | -0.145 | 0.115 | 0.112 | 0.118 | 0.420 | 0.158 |
| price_only | ridge | x | calm | 119588 | -0.462 | -0.584 | -0.359 | 0.708 | 33009.000 | 0.688 | 0.727 | nan | nan | nan | nan | -0.462 | nan |
| price_only | ridge | x | event | 95420 | 0.399 | 0.365 | 0.431 | 0.904 | 76532.000 | 0.896 | 0.912 | nan | nan | nan | nan | 0.399 | nan |
| price_only | ridge | x | resolution | 72992 | 0.119 | 0.064 | 0.167 | 0.652 | 52302.000 | 0.636 | 0.669 | nan | nan | nan | nan | 0.119 | nan |
| price_only | ridge | x | all | 288000 | 0.364 | 0.350 | 0.376 | 0.783 | 161843.000 | 0.774 | 0.791 | nan | nan | nan | nan | 0.364 | nan |
| price_only | ridge | logV | calm | 119588 | 0.219 | 0.180 | 0.258 | nan | nan | nan | nan | nan | 0.112 | 0.108 | 0.116 | 0.219 | nan |
| price_only | ridge | logV | event | 95420 | 0.394 | 0.349 | 0.432 | nan | nan | nan | nan | nan | 0.132 | 0.126 | 0.138 | 0.394 | nan |
| price_only | ridge | logV | resolution | 72992 | -0.233 | -0.332 | -0.161 | nan | nan | nan | nan | nan | 0.208 | 0.197 | 0.219 | -0.233 | nan |
| price_only | ridge | logV | all | 288000 | 0.338 | 0.323 | 0.351 | nan | nan | nan | nan | nan | 0.143 | 0.139 | 0.147 | 0.338 | nan |
| price_only | gbt | x | calm | 119588 | -0.662 | -0.814 | -0.537 | 0.678 | 33009.000 | 0.656 | 0.699 | nan | nan | nan | nan | -0.662 | nan |
| price_only | gbt | x | event | 95420 | 0.436 | 0.400 | 0.468 | 0.904 | 76532.000 | 0.897 | 0.911 | nan | nan | nan | nan | 0.436 | nan |
| price_only | gbt | x | resolution | 72992 | 0.317 | 0.282 | 0.349 | 0.760 | 52302.000 | 0.746 | 0.775 | nan | nan | nan | nan | 0.317 | nan |
| price_only | gbt | x | all | 288000 | 0.421 | 0.406 | 0.435 | 0.811 | 161843.000 | 0.804 | 0.819 | nan | nan | nan | nan | 0.421 | nan |
| price_only | gbt | logV | calm | 119588 | 0.294 | 0.262 | 0.324 | nan | nan | nan | nan | nan | 0.108 | 0.104 | 0.111 | 0.294 | nan |
| price_only | gbt | logV | event | 95420 | 0.385 | 0.335 | 0.432 | nan | nan | nan | nan | nan | 0.133 | 0.127 | 0.139 | 0.385 | nan |
| price_only | gbt | logV | resolution | 72992 | 0.040 | -0.021 | 0.087 | nan | nan | nan | nan | nan | 0.175 | 0.166 | 0.185 | 0.040 | nan |
| price_only | gbt | logV | all | 288000 | 0.416 | 0.399 | 0.432 | nan | nan | nan | nan | nan | 0.133 | 0.130 | 0.137 | 0.416 | nan |
| price_only | mlp | x | calm | 119588 | -0.803 | -0.978 | -0.662 | 0.678 | 33009.000 | 0.658 | 0.697 | nan | nan | nan | nan | -0.803 | nan |
| price_only | mlp | x | event | 95420 | 0.481 | 0.446 | 0.513 | 0.903 | 76532.000 | 0.896 | 0.910 | nan | nan | nan | nan | 0.481 | nan |
| price_only | mlp | x | resolution | 72992 | 0.337 | 0.296 | 0.371 | 0.790 | 52302.000 | 0.777 | 0.804 | nan | nan | nan | nan | 0.337 | nan |
| price_only | mlp | x | all | 288000 | 0.446 | 0.430 | 0.462 | 0.821 | 161843.000 | 0.814 | 0.828 | nan | nan | nan | nan | 0.446 | nan |
| price_only | mlp | logV | calm | 119588 | 0.326 | 0.298 | 0.356 | nan | nan | nan | nan | nan | 0.107 | 0.104 | 0.111 | 0.326 | nan |
| price_only | mlp | logV | event | 95420 | 0.371 | 0.314 | 0.426 | nan | nan | nan | nan | nan | 0.136 | 0.130 | 0.142 | 0.371 | nan |
| price_only | mlp | logV | resolution | 72992 | 0.037 | -0.027 | 0.087 | nan | nan | nan | nan | nan | 0.175 | 0.166 | 0.184 | 0.037 | nan |
| price_only | mlp | logV | all | 288000 | 0.420 | 0.401 | 0.438 | nan | nan | nan | nan | nan | 0.134 | 0.131 | 0.137 | 0.420 | nan |

## L2b composite phase clock

Macro-class accuracy: full 78.3%, price-only 67.5%, day-only 51.0%, majority class 41.5%. Selectivity = +10.7% vs margin 10% -> FAIL.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 37.5%; accuracy price-only 55.7%, price+IV 55.5%, full 64.4%; recall of sustained-bull days: price-only 40.3%, price+IV 40.5%, full 59.8% (reported; no pre-registered threshold).

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 40000 | 0.039 | 0.597 | 0.383 | 0.186 |
| bull_trap | calm | 18228 | 0.038 | 0.585 | 0.378 | 0.186 |
| bull_trap | mania | 22399 | 0.079 | 0.801 | 0.679 | 0.494 |
| bull_trap | blow-off | 33048 | 0.323 | 0.997 | 0.993 | 0.984 |
| sustained_bull | sustained-bull | 40000 | 0.014 | 0.170 | 0.040 | 0.003 |
| crash | calm | 50364 | 0.038 | 0.584 | 0.375 | 0.184 |
| crash | deterioration | 7902 | 0.039 | 0.606 | 0.393 | 0.193 |
| crash | panic | 35067 | 0.116 | 0.853 | 0.759 | 0.631 |
| crash | stabilisation | 66667 | 0.088 | 0.811 | 0.691 | 0.534 |
| bull_trap | post-top | 6325 | 0.249 | 0.990 | 0.984 | 0.965 |
| flat | ALL | 40000 | 0.039 | 0.597 | 0.383 | 0.186 |
| bull_trap | ALL | 80000 | 0.158 | 0.848 | 0.764 | 0.664 |
| sustained_bull | ALL | 40000 | 0.014 | 0.170 | 0.040 | 0.003 |
| crash | ALL | 160000 | 0.065 | 0.738 | 0.592 | 0.428 |
