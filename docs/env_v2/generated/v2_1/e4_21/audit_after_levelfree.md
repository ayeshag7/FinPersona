# Section 5 leakage / phase-clock / resolvability audit (v2, stored panel sep_phase4_after.pkl, 1600 paths, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): LEVEL-FREE (returns, log P/SMA, RSI, MACD/P, trend; no price level -- v2.1 Phase 1, E1.6). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * P (price itself) | 0.9975 | 0.0644 | 1.7359 | 0.0055 | 0.0108 | 0.0276 | 0.0925 | 0.1844 | 0.4163 | 0.9074 | 0.6697 | True |
| k * P * dividend_yield | 0.5148 | 0.1635 | 1.6591 | 0.0154 | 0.0306 | 0.0768 | 0.0317 | 0.0653 | 0.1648 | 0.9683 | 0.6697 | True |
| k * P / reported_PE | 17.8355 | 0.1650 | 1.4339 | 0.0156 | 0.0304 | 0.0780 | 0.0314 | 0.0647 | 0.1632 | 0.9686 | 0.6697 | True |
| k * analyst_fair_value | 2.3022 | 0.6786 | 6.8521 | 0.0861 | 0.1796 | 0.4054 | 0.0055 | 0.0124 | 0.0299 | 0.9945 | 0.6697 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.233, sign accuracy on resolvable steps = 0.804 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.854, MAPE(V) = 11.8% -> PASS (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.482 (worst phase group), MAPE(V) gain = 4.6%, max shuffled-V R2 = -0.002. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119373 | -0.701 | -0.870 | -0.537 | 0.750 | 45544.000 | 0.731 | 0.768 | -0.007 | nan | nan | nan | -0.249 | -0.451 |
| full | ridge | x | event | 95758 | 0.685 | 0.664 | 0.706 | 0.921 | 76819.000 | 0.913 | 0.927 | -0.004 | nan | nan | nan | 0.423 | 0.262 |
| full | ridge | x | resolution | 72869 | 0.597 | 0.561 | 0.628 | 0.867 | 52406.000 | 0.857 | 0.878 | -0.010 | nan | nan | nan | 0.149 | 0.448 |
| full | ridge | x | all | 288000 | 0.610 | 0.590 | 0.627 | 0.860 | 174769.000 | 0.852 | 0.868 | -0.002 | nan | nan | nan | 0.378 | 0.232 |
| full | ridge | logV | calm | 119373 | 0.348 | 0.295 | 0.396 | nan | nan | nan | nan | -0.003 | 0.112 | 0.108 | 0.116 | 0.168 | 0.180 |
| full | ridge | logV | event | 95758 | 0.465 | 0.408 | 0.512 | nan | nan | nan | nan | -0.008 | 0.130 | 0.125 | 0.136 | 0.390 | 0.075 |
| full | ridge | logV | resolution | 72869 | 0.301 | 0.241 | 0.346 | nan | nan | nan | nan | -0.003 | 0.151 | 0.144 | 0.160 | -0.259 | 0.560 |
| full | ridge | logV | all | 288000 | 0.512 | 0.488 | 0.532 | nan | nan | nan | nan | -0.004 | 0.128 | 0.125 | 0.131 | 0.319 | 0.193 |
| full | gbt | x | calm | 119373 | 0.233 | 0.172 | 0.288 | 0.804 | 45544.000 | 0.788 | 0.819 | -0.045 | nan | nan | nan | -0.394 | 0.626 |
| full | gbt | x | event | 95758 | 0.854 | 0.844 | 0.864 | 0.939 | 76819.000 | 0.933 | 0.945 | -0.056 | nan | nan | nan | 0.443 | 0.411 |
| full | gbt | x | resolution | 72869 | 0.744 | 0.716 | 0.769 | 0.898 | 52406.000 | 0.889 | 0.907 | -0.045 | nan | nan | nan | 0.287 | 0.457 |
| full | gbt | x | all | 288000 | 0.805 | 0.793 | 0.815 | 0.892 | 174769.000 | 0.885 | 0.897 | -0.044 | nan | nan | nan | 0.414 | 0.391 |
| full | gbt | logV | calm | 119373 | 0.464 | 0.423 | 0.507 | nan | nan | nan | nan | -0.030 | 0.101 | 0.097 | 0.105 | 0.224 | 0.240 |
| full | gbt | logV | event | 95758 | 0.545 | 0.499 | 0.585 | nan | nan | nan | nan | -0.072 | 0.118 | 0.113 | 0.123 | 0.372 | 0.173 |
| full | gbt | logV | resolution | 72869 | 0.419 | 0.361 | 0.461 | nan | nan | nan | nan | -0.044 | 0.134 | 0.128 | 0.142 | -0.021 | 0.440 |
| full | gbt | logV | all | 288000 | 0.593 | 0.571 | 0.613 | nan | nan | nan | nan | -0.048 | 0.115 | 0.112 | 0.118 | 0.381 | 0.212 |
| full | mlp | x | calm | 119373 | -0.227 | -0.404 | -0.083 | 0.813 | 45544.000 | 0.798 | 0.827 | -0.147 | nan | nan | nan | -0.568 | 0.341 |
| full | mlp | x | event | 95758 | 0.768 | 0.752 | 0.786 | 0.928 | 76819.000 | 0.922 | 0.935 | -0.170 | nan | nan | nan | 0.502 | 0.266 |
| full | mlp | x | resolution | 72869 | 0.689 | 0.658 | 0.715 | 0.894 | 52406.000 | 0.885 | 0.903 | -0.140 | nan | nan | nan | 0.323 | 0.365 |
| full | mlp | x | all | 288000 | 0.711 | 0.694 | 0.727 | 0.888 | 174769.000 | 0.882 | 0.894 | -0.147 | nan | nan | nan | 0.446 | 0.266 |
| full | mlp | logV | calm | 119373 | 0.442 | 0.400 | 0.488 | nan | nan | nan | nan | -0.104 | 0.101 | 0.097 | 0.105 | 0.255 | 0.188 |
| full | mlp | logV | event | 95758 | 0.492 | 0.439 | 0.537 | nan | nan | nan | nan | -0.153 | 0.122 | 0.118 | 0.127 | 0.377 | 0.115 |
| full | mlp | logV | resolution | 72869 | 0.369 | 0.313 | 0.414 | nan | nan | nan | nan | -0.103 | 0.138 | 0.132 | 0.146 | -0.003 | 0.371 |
| full | mlp | logV | all | 288000 | 0.561 | 0.536 | 0.584 | nan | nan | nan | nan | -0.119 | 0.118 | 0.115 | 0.121 | 0.395 | 0.166 |
| price_only | ridge | x | calm | 119373 | -0.249 | -0.330 | -0.179 | 0.696 | 45544.000 | 0.673 | 0.717 | nan | nan | nan | nan | -0.249 | nan |
| price_only | ridge | x | event | 95758 | 0.423 | 0.388 | 0.454 | 0.906 | 76819.000 | 0.898 | 0.913 | nan | nan | nan | nan | 0.423 | nan |
| price_only | ridge | x | resolution | 72869 | 0.149 | 0.101 | 0.194 | 0.646 | 52406.000 | 0.631 | 0.663 | nan | nan | nan | nan | 0.149 | nan |
| price_only | ridge | x | all | 288000 | 0.378 | 0.363 | 0.392 | 0.773 | 174769.000 | 0.763 | 0.782 | nan | nan | nan | nan | 0.378 | nan |
| price_only | ridge | logV | calm | 119373 | 0.168 | 0.127 | 0.213 | nan | nan | nan | nan | nan | 0.116 | 0.112 | 0.121 | 0.168 | nan |
| price_only | ridge | logV | event | 95758 | 0.390 | 0.345 | 0.426 | nan | nan | nan | nan | nan | 0.133 | 0.127 | 0.139 | 0.390 | nan |
| price_only | ridge | logV | resolution | 72869 | -0.259 | -0.356 | -0.187 | nan | nan | nan | nan | nan | 0.212 | 0.201 | 0.223 | -0.259 | nan |
| price_only | ridge | logV | all | 288000 | 0.319 | 0.304 | 0.332 | nan | nan | nan | nan | nan | 0.146 | 0.141 | 0.150 | 0.319 | nan |
| price_only | gbt | x | calm | 119373 | -0.394 | -0.498 | -0.306 | 0.673 | 45544.000 | 0.650 | 0.694 | nan | nan | nan | nan | -0.394 | nan |
| price_only | gbt | x | event | 95758 | 0.443 | 0.409 | 0.475 | 0.897 | 76819.000 | 0.890 | 0.905 | nan | nan | nan | nan | 0.443 | nan |
| price_only | gbt | x | resolution | 72869 | 0.287 | 0.252 | 0.322 | 0.736 | 52406.000 | 0.722 | 0.750 | nan | nan | nan | nan | 0.287 | nan |
| price_only | gbt | x | all | 288000 | 0.414 | 0.398 | 0.428 | 0.790 | 174769.000 | 0.782 | 0.799 | nan | nan | nan | nan | 0.414 | nan |
| price_only | gbt | logV | calm | 119373 | 0.224 | 0.189 | 0.262 | nan | nan | nan | nan | nan | 0.113 | 0.108 | 0.117 | 0.224 | nan |
| price_only | gbt | logV | event | 95758 | 0.372 | 0.323 | 0.416 | nan | nan | nan | nan | nan | 0.134 | 0.128 | 0.140 | 0.372 | nan |
| price_only | gbt | logV | resolution | 72869 | -0.021 | -0.086 | 0.034 | nan | nan | nan | nan | nan | 0.183 | 0.174 | 0.193 | -0.021 | nan |
| price_only | gbt | logV | all | 288000 | 0.381 | 0.364 | 0.399 | nan | nan | nan | nan | nan | 0.138 | 0.134 | 0.141 | 0.381 | nan |
| price_only | mlp | x | calm | 119373 | -0.568 | -0.690 | -0.467 | 0.672 | 45544.000 | 0.651 | 0.693 | nan | nan | nan | nan | -0.568 | nan |
| price_only | mlp | x | event | 95758 | 0.502 | 0.469 | 0.532 | 0.900 | 76819.000 | 0.893 | 0.908 | nan | nan | nan | nan | 0.502 | nan |
| price_only | mlp | x | resolution | 72869 | 0.323 | 0.284 | 0.359 | 0.766 | 52406.000 | 0.753 | 0.781 | nan | nan | nan | nan | 0.323 | nan |
| price_only | mlp | x | all | 288000 | 0.446 | 0.429 | 0.460 | 0.801 | 174769.000 | 0.792 | 0.809 | nan | nan | nan | nan | 0.446 | nan |
| price_only | mlp | logV | calm | 119373 | 0.255 | 0.220 | 0.291 | nan | nan | nan | nan | nan | 0.112 | 0.108 | 0.116 | 0.255 | nan |
| price_only | mlp | logV | event | 95758 | 0.377 | 0.324 | 0.428 | nan | nan | nan | nan | nan | 0.135 | 0.130 | 0.141 | 0.377 | nan |
| price_only | mlp | logV | resolution | 72869 | -0.003 | -0.073 | 0.053 | nan | nan | nan | nan | nan | 0.181 | 0.172 | 0.190 | -0.003 | nan |
| price_only | mlp | logV | all | 288000 | 0.395 | 0.377 | 0.413 | nan | nan | nan | nan | nan | 0.137 | 0.134 | 0.141 | 0.395 | nan |

## L2b composite phase clock

Macro-class accuracy: full 76.0%, price-only 65.7%, day-only 50.9%, majority class 41.4%. Selectivity = +10.4% vs margin 10% -> FAIL.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 37.5%; accuracy price-only 53.5%, price+IV 53.4%, full 61.9%; recall of sustained-bull days: price-only 19.4%, price+IV 20.0%, full 47.2% (reported; no pre-registered threshold).

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 40000 | 0.039 | 0.597 | 0.383 | 0.186 |
| bull_trap | calm | 18228 | 0.038 | 0.585 | 0.378 | 0.186 |
| bull_trap | mania | 22399 | 0.079 | 0.801 | 0.679 | 0.494 |
| bull_trap | blow-off | 33048 | 0.323 | 0.997 | 0.993 | 0.984 |
| sustained_bull | sustained-bull | 40000 | 0.039 | 0.598 | 0.388 | 0.190 |
| crash | calm | 50149 | 0.038 | 0.585 | 0.375 | 0.184 |
| crash | deterioration | 7868 | 0.040 | 0.609 | 0.393 | 0.193 |
| crash | panic | 35439 | 0.116 | 0.853 | 0.760 | 0.633 |
| crash | stabilisation | 66544 | 0.089 | 0.812 | 0.694 | 0.539 |
| bull_trap | post-top | 6325 | 0.249 | 0.990 | 0.984 | 0.965 |
| flat | ALL | 40000 | 0.039 | 0.597 | 0.383 | 0.186 |
| bull_trap | ALL | 80000 | 0.158 | 0.848 | 0.764 | 0.664 |
| sustained_bull | ALL | 40000 | 0.039 | 0.598 | 0.388 | 0.190 |
| crash | ALL | 160000 | 0.066 | 0.740 | 0.594 | 0.431 |
