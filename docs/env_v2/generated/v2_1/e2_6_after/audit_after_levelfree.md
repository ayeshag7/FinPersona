# Section 5 leakage / phase-clock / resolvability audit (v2, stored panel sep_phase2_after.pkl, 1600 paths, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): LEVEL-FREE (returns, log P/SMA, RSI, MACD/P, trend; no price level -- v2.1 Phase 1, E1.6). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * P (price itself) | 1.0029 | 0.0348 | 8.0733 | 0.0025 | 0.0050 | 0.0133 | 0.1937 | 0.3478 | 0.5974 | 0.8063 | 0.6387 | True |
| k * P * dividend_yield | 0.5128 | 0.1516 | 1.4329 | 0.0147 | 0.0294 | 0.0740 | 0.0338 | 0.0679 | 0.1683 | 0.9662 | 0.6387 | True |
| k * P / reported_PE | 17.8318 | 0.1534 | 1.2878 | 0.0148 | 0.0293 | 0.0737 | 0.0337 | 0.0677 | 0.1703 | 0.9663 | 0.6387 | True |
| k * analyst_fair_value | 2.2855 | 0.6796 | 7.1718 | 0.0902 | 0.1855 | 0.4071 | 0.0059 | 0.0114 | 0.0284 | 0.9941 | 0.6387 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.346, sign accuracy on resolvable steps = 0.842 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.779, MAPE(V) = 8.9% -> FAIL (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.575 (worst phase group), MAPE(V) gain = 7.8%, max shuffled-V R2 = -0.002. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119113 | -0.319 | -0.611 | -0.105 | 0.764 | 12808.000 | 0.743 | 0.782 | -0.002 | nan | nan | nan | 0.192 | -0.511 |
| full | ridge | x | event | 112896 | -278.998 | -1058.422 | 0.649 | 0.886 | 77737.000 | 0.874 | 0.897 | -1.322 | nan | nan | nan | 0.543 | -279.541 |
| full | ridge | x | resolution | 55991 | -437250153100618629120.000 | -1323995976712259108864.000 | 0.175 | 0.848 | 34670.000 | 0.831 | 0.866 | -610924475852161408.000 | nan | nan | nan | -0.348 | -437250153100618629120.000 |
| full | ridge | x | all | 288000 | -56756160214273368064.000 | -210510488804486479872.000 | 0.560 | 0.863 | 125215.000 | 0.854 | 0.871 | -165785730178072480.000 | nan | nan | nan | 0.449 | -56756160214273368064.000 |
| full | ridge | logV | calm | 119113 | 0.417 | 0.366 | 0.465 | nan | nan | nan | nan | -0.011 | 0.093 | 0.089 | 0.097 | 0.275 | 0.142 |
| full | ridge | logV | event | 112896 | -54.671 | -209.134 | 0.569 | nan | nan | nan | nan | -5.651 | 0.097 | 0.094 | 0.101 | 0.493 | -55.165 |
| full | ridge | logV | resolution | 55991 | -35689048929998020608.000 | -128169277085901160448.000 | 0.166 | nan | nan | nan | nan | -2471701921368807424.000 | 0.151 | 0.141 | 0.162 | -0.921 | -35689048929998020608.000 |
| full | ridge | logV | all | 288000 | -5720640683357138944.000 | -22048437353853931520.000 | 0.578 | nan | nan | nan | nan | -670902815298634240.000 | 0.106 | 0.103 | 0.109 | 0.343 | -5720640683357138944.000 |
| full | gbt | x | calm | 119113 | 0.346 | 0.206 | 0.446 | 0.842 | 12808.000 | 0.825 | 0.858 | -0.029 | nan | nan | nan | 0.339 | 0.007 |
| full | gbt | x | event | 112896 | 0.779 | 0.764 | 0.793 | 0.931 | 77737.000 | 0.921 | 0.939 | -0.053 | nan | nan | nan | 0.552 | 0.226 |
| full | gbt | x | resolution | 55991 | 0.467 | 0.383 | 0.546 | 0.892 | 34670.000 | 0.875 | 0.908 | -0.037 | nan | nan | nan | -0.178 | 0.645 |
| full | gbt | x | all | 288000 | 0.731 | 0.719 | 0.743 | 0.911 | 125215.000 | 0.904 | 0.919 | -0.039 | nan | nan | nan | 0.487 | 0.244 |
| full | gbt | logV | calm | 119113 | 0.521 | 0.479 | 0.562 | nan | nan | nan | nan | -0.062 | 0.083 | 0.080 | 0.086 | 0.331 | 0.190 |
| full | gbt | logV | event | 112896 | 0.601 | 0.564 | 0.634 | nan | nan | nan | nan | -0.050 | 0.089 | 0.086 | 0.092 | 0.477 | 0.124 |
| full | gbt | logV | resolution | 55991 | 0.297 | 0.208 | 0.370 | nan | nan | nan | nan | -0.057 | 0.129 | 0.120 | 0.140 | -0.613 | 0.910 |
| full | gbt | logV | all | 288000 | 0.637 | 0.614 | 0.658 | nan | nan | nan | nan | -0.054 | 0.094 | 0.092 | 0.097 | 0.402 | 0.235 |
| full | mlp | x | calm | 119113 | 0.159 | -0.036 | 0.295 | 0.835 | 12808.000 | 0.819 | 0.849 | -0.123 | nan | nan | nan | 0.228 | -0.069 |
| full | mlp | x | event | 112896 | -891.034 | -3376.700 | 0.764 | 0.929 | 77737.000 | 0.920 | 0.937 | -17.949 | nan | nan | nan | 0.611 | -891.645 |
| full | mlp | x | resolution | 55991 | -1326600315329719828480.000 | -4016953379539661094912.000 | 0.370 | 0.897 | 34670.000 | 0.881 | 0.912 | -221392332047432515584.000 | nan | nan | nan | -0.107 | -1326600315329719828480.000 |
| full | mlp | x | all | 288000 | -172196028985341575168.000 | -638680807423255773184.000 | 0.697 | 0.910 | 125215.000 | 0.903 | 0.917 | -60078930989158580224.000 | nan | nan | nan | 0.531 | -172196028985341575168.000 |
| full | mlp | logV | calm | 119113 | 0.515 | 0.475 | 0.550 | nan | nan | nan | nan | -0.139 | 0.084 | 0.081 | 0.087 | 0.375 | 0.139 |
| full | mlp | logV | event | 112896 | -8218.787 | -31219.373 | 0.598 | nan | nan | nan | nan | -2433.432 | inf | 0.088 | 0.095 | 0.503 | -8219.289 |
| full | mlp | logV | resolution | 55991 | -2777167323680446873600.000 | -9973578419556094836736.000 | 0.284 | nan | nan | nan | nan | -946208882648704745472.000 | inf | 0.125 | 0.136 | -0.530 | -2777167323680446873600.000 |
| full | mlp | logV | all | 288000 | -445155498749719937024.000 | -1715713968098222014464.000 | 0.631 | nan | nan | nan | nan | -256832831556823121920.000 | inf | 0.093 | 0.098 | 0.435 | -445155498749719937024.000 |
| price_only | ridge | x | calm | 119113 | 0.192 | 0.032 | 0.303 | 0.763 | 12808.000 | 0.746 | 0.781 | nan | nan | nan | nan | 0.192 | nan |
| price_only | ridge | x | event | 112896 | 0.543 | 0.524 | 0.563 | 0.842 | 77737.000 | 0.830 | 0.853 | nan | nan | nan | nan | 0.543 | nan |
| price_only | ridge | x | resolution | 55991 | -0.348 | -0.460 | -0.247 | 0.617 | 34670.000 | 0.595 | 0.639 | nan | nan | nan | nan | -0.348 | nan |
| price_only | ridge | x | all | 288000 | 0.449 | 0.423 | 0.469 | 0.772 | 125215.000 | 0.762 | 0.780 | nan | nan | nan | nan | 0.449 | nan |
| price_only | ridge | logV | calm | 119113 | 0.275 | 0.237 | 0.310 | nan | nan | nan | nan | nan | 0.092 | 0.087 | 0.096 | 0.275 | nan |
| price_only | ridge | logV | event | 112896 | 0.493 | 0.454 | 0.528 | nan | nan | nan | nan | nan | 0.095 | 0.091 | 0.098 | 0.493 | nan |
| price_only | ridge | logV | resolution | 55991 | -0.921 | -1.264 | -0.679 | nan | nan | nan | nan | nan | 0.257 | 0.221 | 0.320 | -0.921 | nan |
| price_only | ridge | logV | all | 288000 | 0.343 | 0.283 | 0.384 | nan | nan | nan | nan | nan | 0.125 | 0.117 | 0.137 | 0.343 | nan |
| price_only | gbt | x | calm | 119113 | 0.339 | 0.208 | 0.434 | 0.827 | 12808.000 | 0.812 | 0.840 | nan | nan | nan | nan | 0.339 | nan |
| price_only | gbt | x | event | 112896 | 0.552 | 0.533 | 0.572 | 0.848 | 77737.000 | 0.837 | 0.858 | nan | nan | nan | nan | 0.552 | nan |
| price_only | gbt | x | resolution | 55991 | -0.178 | -0.364 | -0.013 | 0.638 | 34670.000 | 0.616 | 0.657 | nan | nan | nan | nan | -0.178 | nan |
| price_only | gbt | x | all | 288000 | 0.487 | 0.472 | 0.501 | 0.787 | 125215.000 | 0.779 | 0.795 | nan | nan | nan | nan | 0.487 | nan |
| price_only | gbt | logV | calm | 119113 | 0.331 | 0.296 | 0.365 | nan | nan | nan | nan | nan | 0.089 | 0.085 | 0.093 | 0.331 | nan |
| price_only | gbt | logV | event | 112896 | 0.477 | 0.447 | 0.505 | nan | nan | nan | nan | nan | 0.098 | 0.094 | 0.102 | 0.477 | nan |
| price_only | gbt | logV | resolution | 55991 | -0.613 | -0.776 | -0.488 | nan | nan | nan | nan | nan | 0.217 | 0.206 | 0.231 | -0.613 | nan |
| price_only | gbt | logV | all | 288000 | 0.402 | 0.384 | 0.419 | nan | nan | nan | nan | nan | 0.117 | 0.114 | 0.121 | 0.402 | nan |
| price_only | mlp | x | calm | 119113 | 0.228 | 0.084 | 0.330 | 0.777 | 12808.000 | 0.758 | 0.793 | nan | nan | nan | nan | 0.228 | nan |
| price_only | mlp | x | event | 112896 | 0.611 | 0.595 | 0.631 | 0.875 | 77737.000 | 0.866 | 0.884 | nan | nan | nan | nan | 0.611 | nan |
| price_only | mlp | x | resolution | 55991 | -0.107 | -0.263 | 0.033 | 0.668 | 34670.000 | 0.649 | 0.688 | nan | nan | nan | nan | -0.107 | nan |
| price_only | mlp | x | all | 288000 | 0.531 | 0.516 | 0.544 | 0.808 | 125215.000 | 0.799 | 0.816 | nan | nan | nan | nan | 0.531 | nan |
| price_only | mlp | logV | calm | 119113 | 0.375 | 0.342 | 0.406 | nan | nan | nan | nan | nan | 0.088 | 0.085 | 0.092 | 0.375 | nan |
| price_only | mlp | logV | event | 112896 | 0.503 | 0.469 | 0.534 | nan | nan | nan | nan | nan | 0.095 | 0.092 | 0.099 | 0.503 | nan |
| price_only | mlp | logV | resolution | 55991 | -0.530 | -0.686 | -0.399 | nan | nan | nan | nan | nan | 0.207 | 0.196 | 0.221 | -0.530 | nan |
| price_only | mlp | logV | all | 288000 | 0.435 | 0.414 | 0.454 | nan | nan | nan | nan | nan | 0.114 | 0.111 | 0.118 | 0.435 | nan |

## L2b composite phase clock

Macro-class accuracy: full 78.2%, price-only 62.8%, day-only 48.4%, majority class 41.4%. Selectivity = +15.4% vs margin 10% -> FAIL.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 40.4%; accuracy price-only 57.5%, price+IV 69.1%, full 67.8%; recall of sustained-bull days: price-only 58.0%, price+IV 51.2%, full 56.2% (reported; no pre-registered threshold).

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 40000 | 0.019 | 0.309 | 0.133 | 0.046 |
| bull_trap | calm | 17747 | 0.022 | 0.378 | 0.204 | 0.100 |
| bull_trap | mania | 39953 | 0.087 | 0.806 | 0.687 | 0.532 |
| bull_trap | blow-off | 19779 | 0.148 | 0.969 | 0.942 | 0.887 |
| sustained_bull | sustained-bull | 40000 | 0.010 | 0.112 | 0.027 | 0.003 |
| crash | calm | 50368 | 0.019 | 0.309 | 0.130 | 0.041 |
| crash | deterioration | 22109 | 0.024 | 0.419 | 0.208 | 0.084 |
| crash | panic | 34053 | 0.125 | 0.887 | 0.811 | 0.687 |
| crash | stabilisation | 53470 | 0.067 | 0.763 | 0.616 | 0.419 |
| bull_trap | post-top | 2521 | 0.095 | 0.808 | 0.686 | 0.549 |
| flat | ALL | 40000 | 0.019 | 0.309 | 0.133 | 0.046 |
| bull_trap | ALL | 80000 | 0.087 | 0.751 | 0.643 | 0.524 |
| sustained_bull | ALL | 40000 | 0.010 | 0.112 | 0.027 | 0.003 |
| crash | ALL | 160000 | 0.042 | 0.599 | 0.448 | 0.311 |
