# Section 5 leakage / phase-clock / resolvability audit (v2, stored panel sep_phase3_after.pkl, 1600 paths, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): LEVEL-FREE (returns, log P/SMA, RSI, MACD/P, trend; no price level -- v2.1 Phase 1, E1.6). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * P (price itself) | 1.0015 | 0.0601 | 1.1852 | 0.0041 | 0.0083 | 0.0224 | 0.1196 | 0.2275 | 0.4489 | 0.8804 | 0.6717 | True |
| k * P * dividend_yield | 0.5138 | 0.1623 | 1.3019 | 0.0158 | 0.0317 | 0.0802 | 0.0318 | 0.0636 | 0.1582 | 0.9682 | 0.6717 | True |
| k * P / reported_PE | 17.8390 | 0.1643 | 1.2636 | 0.0158 | 0.0317 | 0.0795 | 0.0316 | 0.0627 | 0.1579 | 0.9684 | 0.6717 | True |
| k * analyst_fair_value | 2.2998 | 0.6716 | 6.8440 | 0.0834 | 0.1748 | 0.4041 | 0.0056 | 0.0128 | 0.0309 | 0.9944 | 0.6717 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.213, sign accuracy on resolvable steps = 0.834 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.877, MAPE(V) = 11.2% -> PASS (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.794 (worst phase group), MAPE(V) gain = 5.8%, max shuffled-V R2 = -0.002. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119419 | -1.339 | -1.636 | -1.083 | 0.762 | 32735.000 | 0.745 | 0.780 | -0.008 | nan | nan | nan | -0.582 | -0.757 |
| full | ridge | x | event | 111857 | 0.723 | 0.704 | 0.741 | 0.929 | 88353.000 | 0.922 | 0.936 | -0.002 | nan | nan | nan | 0.484 | 0.239 |
| full | ridge | x | resolution | 56724 | 0.496 | 0.458 | 0.532 | 0.889 | 44223.000 | 0.878 | 0.901 | -0.005 | nan | nan | nan | -0.235 | 0.731 |
| full | ridge | x | all | 288000 | 0.653 | 0.636 | 0.669 | 0.885 | 165311.000 | 0.880 | 0.892 | -0.003 | nan | nan | nan | 0.427 | 0.226 |
| full | ridge | logV | calm | 119419 | 0.369 | 0.323 | 0.413 | nan | nan | nan | nan | -0.007 | 0.108 | 0.104 | 0.112 | 0.245 | 0.125 |
| full | ridge | logV | event | 111857 | 0.456 | 0.401 | 0.503 | nan | nan | nan | nan | -0.006 | 0.125 | 0.120 | 0.130 | 0.415 | 0.041 |
| full | ridge | logV | resolution | 56724 | 0.278 | 0.219 | 0.318 | nan | nan | nan | nan | -0.005 | 0.157 | 0.149 | 0.166 | -0.330 | 0.608 |
| full | ridge | logV | all | 288000 | 0.514 | 0.489 | 0.535 | nan | nan | nan | nan | -0.004 | 0.125 | 0.121 | 0.128 | 0.352 | 0.161 |
| full | gbt | x | calm | 119419 | 0.213 | 0.141 | 0.270 | 0.834 | 32735.000 | 0.819 | 0.848 | -0.047 | nan | nan | nan | -0.823 | 1.036 |
| full | gbt | x | event | 111857 | 0.877 | 0.868 | 0.885 | 0.947 | 88353.000 | 0.942 | 0.952 | -0.047 | nan | nan | nan | 0.514 | 0.363 |
| full | gbt | x | resolution | 56724 | 0.677 | 0.647 | 0.703 | 0.919 | 44223.000 | 0.910 | 0.928 | -0.043 | nan | nan | nan | 0.135 | 0.542 |
| full | gbt | x | all | 288000 | 0.843 | 0.836 | 0.851 | 0.917 | 165311.000 | 0.913 | 0.922 | -0.043 | nan | nan | nan | 0.485 | 0.358 |
| full | gbt | logV | calm | 119419 | 0.519 | 0.483 | 0.553 | nan | nan | nan | nan | -0.041 | 0.094 | 0.090 | 0.098 | 0.287 | 0.232 |
| full | gbt | logV | event | 111857 | 0.543 | 0.502 | 0.582 | nan | nan | nan | nan | -0.073 | 0.112 | 0.107 | 0.116 | 0.368 | 0.175 |
| full | gbt | logV | resolution | 56724 | 0.420 | 0.370 | 0.463 | nan | nan | nan | nan | -0.073 | 0.137 | 0.129 | 0.145 | -0.103 | 0.523 |
| full | gbt | logV | all | 288000 | 0.610 | 0.587 | 0.631 | nan | nan | nan | nan | -0.061 | 0.109 | 0.107 | 0.112 | 0.392 | 0.219 |
| full | mlp | x | calm | 119419 | -0.475 | -0.712 | -0.295 | 0.834 | 32735.000 | 0.820 | 0.848 | -0.163 | nan | nan | nan | -1.114 | 0.639 |
| full | mlp | x | event | 111857 | 0.798 | 0.784 | 0.812 | 0.938 | 88353.000 | 0.932 | 0.943 | -0.168 | nan | nan | nan | 0.564 | 0.234 |
| full | mlp | x | resolution | 56724 | 0.596 | 0.565 | 0.627 | 0.921 | 44223.000 | 0.913 | 0.930 | -0.171 | nan | nan | nan | 0.207 | 0.390 |
| full | mlp | x | all | 288000 | 0.752 | 0.738 | 0.764 | 0.913 | 165311.000 | 0.908 | 0.918 | -0.165 | nan | nan | nan | 0.517 | 0.234 |
| full | mlp | logV | calm | 119419 | 0.489 | 0.452 | 0.528 | nan | nan | nan | nan | -0.104 | 0.097 | 0.093 | 0.100 | 0.304 | 0.186 |
| full | mlp | logV | event | 111857 | 0.478 | 0.426 | 0.526 | nan | nan | nan | nan | -0.171 | 0.120 | 0.115 | 0.125 | 0.376 | 0.102 |
| full | mlp | logV | resolution | 56724 | 0.344 | 0.276 | 0.392 | nan | nan | nan | nan | -0.123 | 0.145 | 0.138 | 0.153 | -0.072 | 0.416 |
| full | mlp | logV | all | 288000 | 0.567 | 0.542 | 0.591 | nan | nan | nan | nan | -0.134 | 0.115 | 0.112 | 0.118 | 0.405 | 0.162 |
| price_only | ridge | x | calm | 119419 | -0.582 | -0.716 | -0.470 | 0.722 | 32735.000 | 0.702 | 0.741 | nan | nan | nan | nan | -0.582 | nan |
| price_only | ridge | x | event | 111857 | 0.484 | 0.455 | 0.512 | 0.911 | 88353.000 | 0.904 | 0.917 | nan | nan | nan | nan | 0.484 | nan |
| price_only | ridge | x | resolution | 56724 | -0.235 | -0.318 | -0.153 | 0.646 | 44223.000 | 0.629 | 0.663 | nan | nan | nan | nan | -0.235 | nan |
| price_only | ridge | x | all | 288000 | 0.427 | 0.414 | 0.442 | 0.802 | 165311.000 | 0.794 | 0.811 | nan | nan | nan | nan | 0.427 | nan |
| price_only | ridge | logV | calm | 119419 | 0.245 | 0.207 | 0.282 | nan | nan | nan | nan | nan | 0.110 | 0.106 | 0.114 | 0.245 | nan |
| price_only | ridge | logV | event | 111857 | 0.415 | 0.369 | 0.451 | nan | nan | nan | nan | nan | 0.124 | 0.119 | 0.129 | 0.415 | nan |
| price_only | ridge | logV | resolution | 56724 | -0.330 | -0.440 | -0.244 | nan | nan | nan | nan | nan | 0.227 | 0.214 | 0.238 | -0.330 | nan |
| price_only | ridge | logV | all | 288000 | 0.352 | 0.336 | 0.367 | nan | nan | nan | nan | nan | 0.138 | 0.135 | 0.142 | 0.352 | nan |
| price_only | gbt | x | calm | 119419 | -0.823 | -1.018 | -0.669 | 0.713 | 32735.000 | 0.692 | 0.732 | nan | nan | nan | nan | -0.823 | nan |
| price_only | gbt | x | event | 111857 | 0.514 | 0.482 | 0.542 | 0.911 | 88353.000 | 0.904 | 0.918 | nan | nan | nan | nan | 0.514 | nan |
| price_only | gbt | x | resolution | 56724 | 0.135 | 0.064 | 0.192 | 0.771 | 44223.000 | 0.756 | 0.787 | nan | nan | nan | nan | 0.135 | nan |
| price_only | gbt | x | all | 288000 | 0.485 | 0.471 | 0.500 | 0.834 | 165311.000 | 0.827 | 0.841 | nan | nan | nan | nan | 0.485 | nan |
| price_only | gbt | logV | calm | 119419 | 0.287 | 0.254 | 0.319 | nan | nan | nan | nan | nan | 0.107 | 0.103 | 0.111 | 0.287 | nan |
| price_only | gbt | logV | event | 111857 | 0.368 | 0.318 | 0.408 | nan | nan | nan | nan | nan | 0.130 | 0.125 | 0.135 | 0.368 | nan |
| price_only | gbt | logV | resolution | 56724 | -0.103 | -0.177 | -0.046 | nan | nan | nan | nan | nan | 0.199 | 0.188 | 0.211 | -0.103 | nan |
| price_only | gbt | logV | all | 288000 | 0.392 | 0.374 | 0.408 | nan | nan | nan | nan | nan | 0.134 | 0.131 | 0.137 | 0.392 | nan |
| price_only | mlp | x | calm | 119419 | -1.114 | -1.348 | -0.933 | 0.695 | 32735.000 | 0.672 | 0.714 | nan | nan | nan | nan | -1.114 | nan |
| price_only | mlp | x | event | 111857 | 0.564 | 0.536 | 0.592 | 0.914 | 88353.000 | 0.908 | 0.920 | nan | nan | nan | nan | 0.564 | nan |
| price_only | mlp | x | resolution | 56724 | 0.207 | 0.146 | 0.261 | 0.802 | 44223.000 | 0.788 | 0.817 | nan | nan | nan | nan | 0.207 | nan |
| price_only | mlp | x | all | 288000 | 0.517 | 0.503 | 0.532 | 0.840 | 165311.000 | 0.834 | 0.848 | nan | nan | nan | nan | 0.517 | nan |
| price_only | mlp | logV | calm | 119419 | 0.304 | 0.270 | 0.334 | nan | nan | nan | nan | nan | 0.107 | 0.103 | 0.110 | 0.304 | nan |
| price_only | mlp | logV | event | 111857 | 0.376 | 0.324 | 0.419 | nan | nan | nan | nan | nan | 0.129 | 0.124 | 0.135 | 0.376 | nan |
| price_only | mlp | logV | resolution | 56724 | -0.072 | -0.145 | -0.017 | nan | nan | nan | nan | nan | 0.195 | 0.184 | 0.205 | -0.072 | nan |
| price_only | mlp | logV | all | 288000 | 0.405 | 0.386 | 0.423 | nan | nan | nan | nan | nan | 0.133 | 0.129 | 0.136 | 0.405 | nan |

## L2b composite phase clock

Macro-class accuracy: full 78.3%, price-only 65.6%, day-only 48.9%, majority class 41.5%. Selectivity = +12.7% vs margin 10% -> FAIL.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 39.7%; accuracy price-only 53.7%, price+IV 53.7%, full 66.5%; recall of sustained-bull days: price-only 34.5%, price+IV 34.7%, full 59.6% (reported; no pre-registered threshold).

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 40000 | 0.039 | 0.597 | 0.383 | 0.186 |
| bull_trap | calm | 18218 | 0.037 | 0.579 | 0.373 | 0.181 |
| bull_trap | mania | 39225 | 0.150 | 0.885 | 0.815 | 0.707 |
| bull_trap | blow-off | 19418 | 0.365 | 0.999 | 0.998 | 0.995 |
| sustained_bull | sustained-bull | 40000 | 0.014 | 0.170 | 0.040 | 0.003 |
| crash | calm | 50275 | 0.037 | 0.581 | 0.371 | 0.181 |
| crash | deterioration | 22157 | 0.043 | 0.634 | 0.430 | 0.229 |
| crash | panic | 33983 | 0.169 | 0.904 | 0.843 | 0.751 |
| crash | stabilisation | 53585 | 0.125 | 0.869 | 0.787 | 0.667 |
| bull_trap | post-top | 3139 | 0.088 | 0.765 | 0.654 | 0.529 |
| flat | ALL | 40000 | 0.039 | 0.597 | 0.383 | 0.186 |
| bull_trap | ALL | 80000 | 0.151 | 0.838 | 0.752 | 0.650 |
| sustained_bull | ALL | 40000 | 0.014 | 0.170 | 0.040 | 0.003 |
| crash | ALL | 160000 | 0.073 | 0.754 | 0.619 | 0.472 |
