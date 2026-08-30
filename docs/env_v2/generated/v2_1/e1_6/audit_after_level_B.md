# Section 5 leakage / phase-clock / resolvability audit (v2, stored panel sep_after.pkl, 1600 paths, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): the v2 price-and-technicals set (contains the price level; kept for the record). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * analyst_fair_value | 0.9941 | 0.1051 | 0.7160 | 0.0101 | 0.0196 | 0.0489 | 0.0497 | 0.1028 | 0.2561 | 0.9503 | 0.7282 | True |
| k * P (price itself) | 1.0091 | 0.1257 | 2.3720 | 0.0071 | 0.0147 | 0.0440 | 0.0696 | 0.1337 | 0.2730 | 0.9304 | 0.7282 | True |
| k * P * dividend_yield | 0.5182 | 0.1351 | 0.8572 | 0.0137 | 0.0277 | 0.0695 | 0.0368 | 0.0732 | 0.1783 | 0.9632 | 0.7282 | True |
| k * P / reported_PE | 17.9463 | 0.1372 | 0.9336 | 0.0135 | 0.0276 | 0.0685 | 0.0373 | 0.0729 | 0.1832 | 0.9627 | 0.7282 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.811, sign accuracy on resolvable steps = 0.900 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.944, MAPE(V) = 6.5% -> FAIL (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.661 (worst phase group), MAPE(V) gain = 6.2%, max shuffled-V R2 = -0.003. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119663 | 0.568 | 0.508 | 0.620 | 0.877 | 65439.000 | 0.862 | 0.890 | -0.003 | nan | nan | nan | -0.123 | 0.690 |
| full | ridge | x | event | 94915 | 0.894 | 0.886 | 0.901 | 0.939 | 82348.000 | 0.933 | 0.944 | -0.003 | nan | nan | nan | 0.697 | 0.197 |
| full | ridge | x | resolution | 73422 | 0.889 | 0.878 | 0.899 | 0.968 | 64304.000 | 0.962 | 0.974 | -0.004 | nan | nan | nan | 0.742 | 0.147 |
| full | ridge | x | all | 288000 | 0.852 | 0.841 | 0.861 | 0.928 | 212091.000 | 0.923 | 0.934 | -0.003 | nan | nan | nan | 0.609 | 0.243 |
| full | ridge | logV | calm | 119663 | 0.727 | 0.693 | 0.756 | nan | nan | nan | nan | -0.004 | 0.083 | 0.080 | 0.086 | 0.318 | 0.409 |
| full | ridge | logV | event | 94915 | 0.761 | 0.735 | 0.784 | nan | nan | nan | nan | -0.004 | 0.090 | 0.087 | 0.094 | 0.415 | 0.346 |
| full | ridge | logV | resolution | 73422 | 0.713 | 0.683 | 0.739 | nan | nan | nan | nan | -0.007 | 0.098 | 0.094 | 0.103 | 0.385 | 0.328 |
| full | ridge | logV | all | 288000 | 0.777 | 0.762 | 0.790 | nan | nan | nan | nan | -0.004 | 0.089 | 0.087 | 0.092 | 0.469 | 0.308 |
| full | gbt | x | calm | 119663 | 0.811 | 0.786 | 0.834 | 0.900 | 65439.000 | 0.887 | 0.912 | -0.022 | nan | nan | nan | 0.150 | 0.661 |
| full | gbt | x | event | 94915 | 0.944 | 0.940 | 0.948 | 0.945 | 82348.000 | 0.939 | 0.950 | -0.040 | nan | nan | nan | 0.756 | 0.188 |
| full | gbt | x | resolution | 73422 | 0.944 | 0.938 | 0.949 | 0.978 | 64304.000 | 0.973 | 0.984 | -0.051 | nan | nan | nan | 0.793 | 0.152 |
| full | gbt | x | all | 288000 | 0.928 | 0.923 | 0.932 | 0.941 | 212091.000 | 0.936 | 0.946 | -0.037 | nan | nan | nan | 0.693 | 0.235 |
| full | gbt | logV | calm | 119663 | 0.896 | 0.882 | 0.908 | nan | nan | nan | nan | -0.028 | 0.049 | 0.047 | 0.051 | 0.557 | 0.338 |
| full | gbt | logV | event | 94915 | 0.877 | 0.862 | 0.891 | nan | nan | nan | nan | -0.035 | 0.065 | 0.063 | 0.067 | 0.520 | 0.357 |
| full | gbt | logV | resolution | 73422 | 0.903 | 0.892 | 0.913 | nan | nan | nan | nan | -0.065 | 0.056 | 0.054 | 0.058 | 0.673 | 0.230 |
| full | gbt | logV | all | 288000 | 0.908 | 0.900 | 0.915 | nan | nan | nan | nan | -0.040 | 0.056 | 0.055 | 0.058 | 0.640 | 0.268 |
| full | mlp | x | calm | 119663 | 0.754 | 0.723 | 0.780 | 0.910 | 65439.000 | 0.901 | 0.920 | -0.142 | nan | nan | nan | 0.137 | 0.617 |
| full | mlp | x | event | 94915 | 0.908 | 0.890 | 0.920 | 0.946 | 82348.000 | 0.941 | 0.950 | -0.161 | nan | nan | nan | 0.751 | 0.157 |
| full | mlp | x | resolution | 73422 | 0.900 | 0.891 | 0.909 | 0.975 | 64304.000 | 0.970 | 0.980 | -0.229 | nan | nan | nan | 0.789 | 0.111 |
| full | mlp | x | all | 288000 | 0.888 | 0.877 | 0.896 | 0.944 | 212091.000 | 0.939 | 0.948 | -0.177 | nan | nan | nan | 0.688 | 0.200 |
| full | mlp | logV | calm | 119663 | 0.852 | 0.833 | 0.869 | nan | nan | nan | nan | -0.122 | 0.059 | 0.057 | 0.062 | 0.521 | 0.331 |
| full | mlp | logV | event | 94915 | 0.802 | 0.757 | 0.838 | nan | nan | nan | nan | -0.164 | 0.191 | 0.078 | 0.420 | 0.503 | 0.299 |
| full | mlp | logV | resolution | 73422 | 0.843 | 0.822 | 0.860 | nan | nan | nan | nan | -0.213 | 0.071 | 0.069 | 0.074 | 0.660 | 0.183 |
| full | mlp | logV | all | 288000 | 0.857 | 0.840 | 0.872 | nan | nan | nan | nan | -0.162 | 0.106 | 0.068 | 0.180 | 0.621 | 0.236 |
| price_only | ridge | x | calm | 119663 | -0.123 | -0.212 | -0.052 | 0.585 | 65439.000 | 0.560 | 0.609 | nan | nan | nan | nan | -0.123 | nan |
| price_only | ridge | x | event | 94915 | 0.697 | 0.663 | 0.727 | 0.838 | 82348.000 | 0.826 | 0.850 | nan | nan | nan | nan | 0.697 | nan |
| price_only | ridge | x | resolution | 73422 | 0.742 | 0.719 | 0.762 | 0.919 | 64304.000 | 0.908 | 0.931 | nan | nan | nan | nan | 0.742 | nan |
| price_only | ridge | x | all | 288000 | 0.609 | 0.577 | 0.638 | 0.785 | 212091.000 | 0.772 | 0.797 | nan | nan | nan | nan | 0.609 | nan |
| price_only | ridge | logV | calm | 119663 | 0.318 | 0.271 | 0.358 | nan | nan | nan | nan | nan | 0.130 | 0.126 | 0.135 | 0.318 | nan |
| price_only | ridge | logV | event | 94915 | 0.415 | 0.366 | 0.459 | nan | nan | nan | nan | nan | 0.144 | 0.138 | 0.150 | 0.415 | nan |
| price_only | ridge | logV | resolution | 73422 | 0.385 | 0.328 | 0.436 | nan | nan | nan | nan | nan | 0.151 | 0.145 | 0.158 | 0.385 | nan |
| price_only | ridge | logV | all | 288000 | 0.469 | 0.443 | 0.494 | nan | nan | nan | nan | nan | 0.140 | 0.136 | 0.145 | 0.469 | nan |
| price_only | gbt | x | calm | 119663 | 0.150 | 0.085 | 0.203 | 0.657 | 65439.000 | 0.631 | 0.678 | nan | nan | nan | nan | 0.150 | nan |
| price_only | gbt | x | event | 94915 | 0.756 | 0.729 | 0.778 | 0.863 | 82348.000 | 0.853 | 0.873 | nan | nan | nan | nan | 0.756 | nan |
| price_only | gbt | x | resolution | 73422 | 0.793 | 0.768 | 0.813 | 0.934 | 64304.000 | 0.922 | 0.945 | nan | nan | nan | nan | 0.793 | nan |
| price_only | gbt | x | all | 288000 | 0.693 | 0.666 | 0.716 | 0.821 | 212091.000 | 0.810 | 0.830 | nan | nan | nan | nan | 0.693 | nan |
| price_only | gbt | logV | calm | 119663 | 0.557 | 0.517 | 0.593 | nan | nan | nan | nan | nan | 0.097 | 0.091 | 0.102 | 0.557 | nan |
| price_only | gbt | logV | event | 94915 | 0.520 | 0.482 | 0.554 | nan | nan | nan | nan | nan | 0.128 | 0.123 | 0.133 | 0.520 | nan |
| price_only | gbt | logV | resolution | 73422 | 0.673 | 0.637 | 0.706 | nan | nan | nan | nan | nan | 0.101 | 0.096 | 0.106 | 0.673 | nan |
| price_only | gbt | logV | all | 288000 | 0.640 | 0.616 | 0.663 | nan | nan | nan | nan | nan | 0.108 | 0.104 | 0.112 | 0.640 | nan |
| price_only | mlp | x | calm | 119663 | 0.137 | 0.073 | 0.191 | 0.659 | 65439.000 | 0.639 | 0.676 | nan | nan | nan | nan | 0.137 | nan |
| price_only | mlp | x | event | 94915 | 0.751 | 0.723 | 0.774 | 0.854 | 82348.000 | 0.845 | 0.863 | nan | nan | nan | nan | 0.751 | nan |
| price_only | mlp | x | resolution | 73422 | 0.789 | 0.763 | 0.811 | 0.931 | 64304.000 | 0.919 | 0.941 | nan | nan | nan | nan | 0.789 | nan |
| price_only | mlp | x | all | 288000 | 0.688 | 0.660 | 0.712 | 0.817 | 212091.000 | 0.807 | 0.825 | nan | nan | nan | nan | 0.688 | nan |
| price_only | mlp | logV | calm | 119663 | 0.521 | 0.472 | 0.566 | nan | nan | nan | nan | nan | 0.099 | 0.093 | 0.104 | 0.521 | nan |
| price_only | mlp | logV | event | 94915 | 0.503 | 0.461 | 0.540 | nan | nan | nan | nan | nan | 0.129 | 0.124 | 0.135 | 0.503 | nan |
| price_only | mlp | logV | resolution | 73422 | 0.660 | 0.625 | 0.694 | nan | nan | nan | nan | nan | 0.102 | 0.098 | 0.106 | 0.660 | nan |
| price_only | mlp | logV | all | 288000 | 0.621 | 0.592 | 0.647 | nan | nan | nan | nan | nan | 0.110 | 0.106 | 0.114 | 0.621 | nan |

## L2b composite phase clock

Macro-class accuracy: full 87.3%, price-only 80.5%, day-only 53.5%, majority class 41.5%. Selectivity = +6.8% vs margin 10% -> PASS.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 47.0%; accuracy price-only 76.7%, price+IV 80.8%, full 82.5%; recall of sustained-bull days: price-only 79.7%, price+IV 80.8%, full 85.8% (reported; no pre-registered threshold).

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
