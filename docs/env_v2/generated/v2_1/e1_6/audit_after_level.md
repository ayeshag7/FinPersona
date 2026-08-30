# Section 5 leakage / phase-clock / resolvability audit (v2, stored panel sep_after.pkl, 1600 paths, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): the v2 price-and-technicals set (contains the price level; kept for the record). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * P (price itself) | 1.0091 | 0.1257 | 2.3720 | 0.0071 | 0.0147 | 0.0440 | 0.0696 | 0.1337 | 0.2730 | 0.9304 | 0.7282 | True |
| k * P * dividend_yield | 0.5182 | 0.1351 | 0.8572 | 0.0137 | 0.0277 | 0.0695 | 0.0368 | 0.0732 | 0.1783 | 0.9632 | 0.7282 | True |
| k * P / reported_PE | 17.9463 | 0.1372 | 0.9336 | 0.0135 | 0.0276 | 0.0685 | 0.0373 | 0.0729 | 0.1832 | 0.9627 | 0.7282 | True |
| k * analyst_fair_value | 2.2877 | 0.6718 | 6.8025 | 0.0829 | 0.1773 | 0.4045 | 0.0069 | 0.0125 | 0.0312 | 0.9931 | 0.7282 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.823, sign accuracy on resolvable steps = 0.915 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.944, MAPE(V) = 12.2% -> FAIL (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.662 (worst phase group), MAPE(V) gain = 3.0%, max shuffled-V R2 = -0.002. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119663 | 0.422 | 0.348 | 0.484 | 0.855 | 65439.000 | 0.839 | 0.871 | -0.003 | nan | nan | nan | -0.070 | 0.491 |
| full | ridge | x | event | 94915 | 0.858 | 0.849 | 0.868 | 0.930 | 82348.000 | 0.924 | 0.936 | -0.002 | nan | nan | nan | 0.618 | 0.240 |
| full | ridge | x | resolution | 73422 | 0.842 | 0.828 | 0.856 | 0.955 | 64304.000 | 0.948 | 0.962 | -0.004 | nan | nan | nan | 0.196 | 0.647 |
| full | ridge | x | all | 288000 | 0.799 | 0.786 | 0.810 | 0.915 | 212091.000 | 0.908 | 0.921 | -0.003 | nan | nan | nan | 0.408 | 0.390 |
| full | ridge | logV | calm | 119663 | 0.184 | 0.127 | 0.241 | nan | nan | nan | nan | -0.003 | 0.135 | 0.130 | 0.141 | 0.084 | 0.100 |
| full | ridge | logV | event | 94915 | 0.355 | 0.307 | 0.397 | nan | nan | nan | nan | -0.006 | 0.146 | 0.139 | 0.153 | 0.325 | 0.030 |
| full | ridge | logV | resolution | 73422 | -0.062 | -0.134 | -0.009 | nan | nan | nan | nan | -0.005 | 0.200 | 0.192 | 0.210 | -0.138 | 0.076 |
| full | ridge | logV | all | 288000 | 0.308 | 0.282 | 0.333 | nan | nan | nan | nan | -0.004 | 0.155 | 0.151 | 0.160 | 0.252 | 0.057 |
| full | gbt | x | calm | 119663 | 0.823 | 0.799 | 0.845 | 0.915 | 65439.000 | 0.904 | 0.925 | -0.029 | nan | nan | nan | 0.161 | 0.662 |
| full | gbt | x | event | 94915 | 0.944 | 0.939 | 0.947 | 0.948 | 82348.000 | 0.942 | 0.952 | -0.062 | nan | nan | nan | 0.665 | 0.279 |
| full | gbt | x | resolution | 73422 | 0.938 | 0.931 | 0.944 | 0.970 | 64304.000 | 0.964 | 0.976 | -0.052 | nan | nan | nan | 0.371 | 0.566 |
| full | gbt | x | all | 288000 | 0.927 | 0.923 | 0.932 | 0.944 | 212091.000 | 0.940 | 0.948 | -0.047 | nan | nan | nan | 0.518 | 0.409 |
| full | gbt | logV | calm | 119663 | 0.574 | 0.536 | 0.610 | nan | nan | nan | nan | -0.042 | 0.098 | 0.095 | 0.102 | 0.285 | 0.289 |
| full | gbt | logV | event | 94915 | 0.512 | 0.483 | 0.542 | nan | nan | nan | nan | -0.071 | 0.122 | 0.117 | 0.128 | 0.368 | 0.144 |
| full | gbt | logV | resolution | 73422 | 0.169 | 0.113 | 0.220 | nan | nan | nan | nan | -0.078 | 0.172 | 0.165 | 0.180 | -0.031 | 0.200 |
| full | gbt | logV | all | 288000 | 0.529 | 0.509 | 0.551 | nan | nan | nan | nan | -0.061 | 0.125 | 0.121 | 0.129 | 0.351 | 0.178 |
| full | mlp | x | calm | 119663 | 0.715 | 0.678 | 0.747 | 0.908 | 65439.000 | 0.897 | 0.918 | -0.160 | nan | nan | nan | 0.089 | 0.627 |
| full | mlp | x | event | 94915 | 0.901 | 0.886 | 0.912 | 0.947 | 82348.000 | 0.942 | 0.952 | -0.191 | nan | nan | nan | 0.691 | 0.210 |
| full | mlp | x | resolution | 73422 | 0.889 | 0.878 | 0.898 | 0.966 | 64304.000 | 0.960 | 0.973 | -0.196 | nan | nan | nan | 0.493 | 0.395 |
| full | mlp | x | all | 288000 | 0.875 | 0.865 | 0.884 | 0.941 | 212091.000 | 0.936 | 0.945 | -0.182 | nan | nan | nan | 0.559 | 0.316 |
| full | mlp | logV | calm | 119663 | 0.487 | 0.441 | 0.533 | nan | nan | nan | nan | -0.094 | 0.108 | 0.104 | 0.112 | 0.226 | 0.261 |
| full | mlp | logV | event | 94915 | 0.478 | 0.442 | 0.510 | nan | nan | nan | nan | -0.146 | 0.128 | 0.123 | 0.133 | 0.344 | 0.134 |
| full | mlp | logV | resolution | 73422 | 0.043 | -0.025 | 0.107 | nan | nan | nan | nan | -0.153 | 0.185 | 0.178 | 0.193 | 0.023 | 0.020 |
| full | mlp | logV | all | 288000 | 0.464 | 0.440 | 0.488 | nan | nan | nan | nan | -0.127 | 0.134 | 0.130 | 0.137 | 0.337 | 0.126 |
| price_only | ridge | x | calm | 119663 | -0.070 | -0.118 | -0.027 | 0.571 | 65439.000 | 0.550 | 0.590 | nan | nan | nan | nan | -0.070 | nan |
| price_only | ridge | x | event | 94915 | 0.618 | 0.598 | 0.637 | 0.838 | 82348.000 | 0.827 | 0.848 | nan | nan | nan | nan | 0.618 | nan |
| price_only | ridge | x | resolution | 73422 | 0.196 | 0.161 | 0.233 | 0.606 | 64304.000 | 0.593 | 0.620 | nan | nan | nan | nan | 0.196 | nan |
| price_only | ridge | x | all | 288000 | 0.408 | 0.386 | 0.428 | 0.685 | 212091.000 | 0.675 | 0.695 | nan | nan | nan | nan | 0.408 | nan |
| price_only | ridge | logV | calm | 119663 | 0.084 | 0.028 | 0.136 | nan | nan | nan | nan | nan | 0.144 | 0.139 | 0.150 | 0.084 | nan |
| price_only | ridge | logV | event | 94915 | 0.325 | 0.280 | 0.366 | nan | nan | nan | nan | nan | 0.152 | 0.145 | 0.160 | 0.325 | nan |
| price_only | ridge | logV | resolution | 73422 | -0.138 | -0.210 | -0.081 | nan | nan | nan | nan | nan | 0.213 | 0.204 | 0.223 | -0.138 | nan |
| price_only | ridge | logV | all | 288000 | 0.252 | 0.230 | 0.272 | nan | nan | nan | nan | nan | 0.164 | 0.160 | 0.170 | 0.252 | nan |
| price_only | gbt | x | calm | 119663 | 0.161 | 0.120 | 0.198 | 0.650 | 65439.000 | 0.628 | 0.673 | nan | nan | nan | nan | 0.161 | nan |
| price_only | gbt | x | event | 94915 | 0.665 | 0.644 | 0.684 | 0.830 | 82348.000 | 0.821 | 0.839 | nan | nan | nan | nan | 0.665 | nan |
| price_only | gbt | x | resolution | 73422 | 0.371 | 0.333 | 0.402 | 0.715 | 64304.000 | 0.699 | 0.735 | nan | nan | nan | nan | 0.371 | nan |
| price_only | gbt | x | all | 288000 | 0.518 | 0.499 | 0.535 | 0.740 | 212091.000 | 0.730 | 0.749 | nan | nan | nan | nan | 0.518 | nan |
| price_only | gbt | logV | calm | 119663 | 0.285 | 0.239 | 0.327 | nan | nan | nan | nan | nan | 0.128 | 0.123 | 0.133 | 0.285 | nan |
| price_only | gbt | logV | event | 94915 | 0.368 | 0.332 | 0.405 | nan | nan | nan | nan | nan | 0.143 | 0.137 | 0.150 | 0.368 | nan |
| price_only | gbt | logV | resolution | 73422 | -0.031 | -0.098 | 0.024 | nan | nan | nan | nan | nan | 0.195 | 0.187 | 0.204 | -0.031 | nan |
| price_only | gbt | logV | all | 288000 | 0.351 | 0.331 | 0.372 | nan | nan | nan | nan | nan | 0.150 | 0.146 | 0.155 | 0.351 | nan |
| price_only | mlp | x | calm | 119663 | 0.089 | 0.033 | 0.136 | 0.620 | 65439.000 | 0.602 | 0.637 | nan | nan | nan | nan | 0.089 | nan |
| price_only | mlp | x | event | 94915 | 0.691 | 0.670 | 0.712 | 0.831 | 82348.000 | 0.823 | 0.840 | nan | nan | nan | nan | 0.691 | nan |
| price_only | mlp | x | resolution | 73422 | 0.493 | 0.459 | 0.523 | 0.774 | 64304.000 | 0.760 | 0.789 | nan | nan | nan | nan | 0.493 | nan |
| price_only | mlp | x | all | 288000 | 0.559 | 0.535 | 0.580 | 0.749 | 212091.000 | 0.741 | 0.757 | nan | nan | nan | nan | 0.559 | nan |
| price_only | mlp | logV | calm | 119663 | 0.226 | 0.175 | 0.272 | nan | nan | nan | nan | nan | 0.133 | 0.128 | 0.138 | 0.226 | nan |
| price_only | mlp | logV | event | 94915 | 0.344 | 0.303 | 0.381 | nan | nan | nan | nan | nan | 0.147 | 0.140 | 0.153 | 0.344 | nan |
| price_only | mlp | logV | resolution | 73422 | 0.023 | -0.036 | 0.075 | nan | nan | nan | nan | nan | 0.188 | 0.181 | 0.196 | 0.023 | nan |
| price_only | mlp | logV | all | 288000 | 0.337 | 0.314 | 0.361 | nan | nan | nan | nan | nan | 0.152 | 0.147 | 0.156 | 0.337 | nan |

## L2b composite phase clock

Macro-class accuracy: full 83.8%, price-only 71.4%, day-only 53.5%, majority class 41.5%. Selectivity = +12.4% vs margin 10% -> FAIL.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 47.0%; accuracy price-only 72.3%, price+IV 76.2%, full 80.5%; recall of sustained-bull days: price-only 74.4%, price+IV 75.7%, full 82.7% (reported; no pre-registered threshold).

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
