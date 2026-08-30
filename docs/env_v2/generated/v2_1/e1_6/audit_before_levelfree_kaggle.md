# Section 5 leakage / phase-clock / resolvability audit (v2, 30 seeds, T=200)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): LEVEL-FREE (returns, log P/SMA, RSI, MACD/P, trend; no price level -- v2.1 Phase 1, E1.6). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * analyst_fair_value | 1.0039 | 0.0996 | 0.8095 | 0.0087 | 0.0182 | 0.0470 | 0.0557 | 0.1093 | 0.2660 | 0.9443 | 0.6777 | False |
| k * P (price itself) | 1.0545 | 0.1148 | 2.3430 | 0.0129 | 0.0244 | 0.0540 | 0.0384 | 0.0807 | 0.2277 | 0.9616 | 0.6777 | True |
| k * P * dividend_yield | 0.5223 | 0.1311 | 0.9581 | 0.0123 | 0.0247 | 0.0635 | 0.0406 | 0.0810 | 0.1986 | 0.9594 | 0.6777 | True |
| k * P / reported_PE | 18.1096 | 0.1331 | 1.0396 | 0.0125 | 0.0255 | 0.0654 | 0.0403 | 0.0783 | 0.1921 | 0.9597 | 0.6777 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = 0.928, sign accuracy on resolvable steps = 0.975 -> FAIL (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.971, MAPE(V) = 4.5% -> FAIL (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.525 (worst phase group), MAPE(V) gain = 9.6%, max shuffled-V R2 = 0.002. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119440 | 0.737 | 0.690 | 0.772 | 0.947 | 67066.000 | 0.938 | 0.954 | -0.007 | nan | nan | nan | 0.144 | 0.593 |
| full | ridge | x | event | 97998 | 0.938 | 0.934 | 0.942 | 0.971 | 86028.000 | 0.967 | 0.975 | -0.002 | nan | nan | nan | 0.609 | 0.329 |
| full | ridge | x | resolution | 70562 | 0.915 | 0.904 | 0.924 | 0.985 | 62884.000 | 0.981 | 0.989 | 0.002 | nan | nan | nan | 0.251 | 0.664 |
| full | ridge | x | all | 288000 | 0.899 | 0.893 | 0.906 | 0.968 | 215978.000 | 0.964 | 0.971 | -0.001 | nan | nan | nan | 0.444 | 0.455 |
| full | ridge | logV | calm | 119440 | 0.448 | 0.390 | 0.503 | nan | nan | nan | nan | -0.016 | 0.067 | 0.064 | 0.069 | -0.381 | 0.829 |
| full | ridge | logV | event | 97998 | 0.613 | 0.584 | 0.642 | nan | nan | nan | nan | -0.005 | 0.064 | 0.062 | 0.066 | 0.450 | 0.163 |
| full | ridge | logV | resolution | 70562 | 0.561 | 0.520 | 0.597 | nan | nan | nan | nan | -0.018 | 0.080 | 0.076 | 0.083 | -0.698 | 1.258 |
| full | ridge | logV | all | 288000 | 0.708 | 0.690 | 0.726 | nan | nan | nan | nan | -0.007 | 0.069 | 0.067 | 0.071 | 0.243 | 0.465 |
| full | gbt | x | calm | 119440 | 0.928 | 0.910 | 0.941 | 0.975 | 67066.000 | 0.968 | 0.979 | -0.006 | nan | nan | nan | 0.385 | 0.543 |
| full | gbt | x | event | 97998 | 0.971 | 0.969 | 0.973 | 0.984 | 86028.000 | 0.981 | 0.987 | -0.031 | nan | nan | nan | 0.677 | 0.294 |
| full | gbt | x | resolution | 70562 | 0.956 | 0.950 | 0.960 | 0.990 | 62884.000 | 0.988 | 0.993 | -0.035 | nan | nan | nan | 0.411 | 0.545 |
| full | gbt | x | all | 288000 | 0.960 | 0.957 | 0.963 | 0.983 | 215978.000 | 0.980 | 0.985 | -0.022 | nan | nan | nan | 0.564 | 0.396 |
| full | gbt | logV | calm | 119440 | 0.859 | 0.842 | 0.873 | nan | nan | nan | nan | -0.033 | 0.033 | 0.032 | 0.034 | -0.010 | 0.869 |
| full | gbt | logV | event | 97998 | 0.800 | 0.786 | 0.813 | nan | nan | nan | nan | -0.028 | 0.045 | 0.044 | 0.047 | 0.513 | 0.286 |
| full | gbt | logV | resolution | 70562 | 0.828 | 0.812 | 0.842 | nan | nan | nan | nan | -0.065 | 0.047 | 0.046 | 0.049 | -0.517 | 1.345 |
| full | gbt | logV | all | 288000 | 0.893 | 0.886 | 0.900 | nan | nan | nan | nan | -0.037 | 0.041 | 0.040 | 0.042 | 0.376 | 0.516 |
| full | mlp | x | calm | 119440 | 0.896 | 0.874 | 0.913 | 0.974 | 67066.000 | 0.968 | 0.978 | -0.129 | nan | nan | nan | 0.403 | 0.492 |
| full | mlp | x | event | 97998 | 0.959 | 0.956 | 0.962 | 0.981 | 86028.000 | 0.979 | 0.984 | -0.157 | nan | nan | nan | 0.712 | 0.247 |
| full | mlp | x | resolution | 70562 | 0.922 | 0.912 | 0.930 | 0.988 | 62884.000 | 0.986 | 0.991 | -0.151 | nan | nan | nan | 0.506 | 0.416 |
| full | mlp | x | all | 288000 | 0.939 | 0.935 | 0.944 | 0.981 | 215978.000 | 0.979 | 0.983 | -0.144 | nan | nan | nan | 0.612 | 0.328 |
| full | mlp | logV | calm | 119440 | 0.776 | 0.745 | 0.805 | nan | nan | nan | nan | -0.131 | 0.040 | 0.038 | 0.041 | 0.026 | 0.750 |
| full | mlp | logV | event | 97998 | 0.709 | 0.689 | 0.729 | nan | nan | nan | nan | -0.130 | 0.054 | 0.052 | 0.056 | 0.498 | 0.210 |
| full | mlp | logV | resolution | 70562 | 0.710 | 0.684 | 0.732 | nan | nan | nan | nan | -0.188 | 0.062 | 0.060 | 0.065 | -0.345 | 1.055 |
| full | mlp | logV | all | 288000 | 0.832 | 0.819 | 0.844 | nan | nan | nan | nan | -0.145 | 0.050 | 0.049 | 0.051 | 0.414 | 0.418 |
| price_only | ridge | x | calm | 119440 | 0.144 | 0.095 | 0.191 | 0.689 | 67066.000 | 0.669 | 0.712 | nan | nan | nan | nan | 0.144 | nan |
| price_only | ridge | x | event | 97998 | 0.609 | 0.581 | 0.636 | 0.880 | 86028.000 | 0.871 | 0.890 | nan | nan | nan | nan | 0.609 | nan |
| price_only | ridge | x | resolution | 70562 | 0.251 | 0.221 | 0.279 | 0.741 | 62884.000 | 0.724 | 0.757 | nan | nan | nan | nan | 0.251 | nan |
| price_only | ridge | x | all | 288000 | 0.444 | 0.422 | 0.467 | 0.780 | 215978.000 | 0.772 | 0.791 | nan | nan | nan | nan | 0.444 | nan |
| price_only | ridge | logV | calm | 119440 | -0.381 | -0.477 | -0.298 | nan | nan | nan | nan | nan | 0.093 | 0.089 | 0.096 | -0.381 | nan |
| price_only | ridge | logV | event | 97998 | 0.450 | 0.418 | 0.478 | nan | nan | nan | nan | nan | 0.077 | 0.074 | 0.080 | 0.450 | nan |
| price_only | ridge | logV | resolution | 70562 | -0.698 | -0.849 | -0.587 | nan | nan | nan | nan | nan | 0.171 | 0.165 | 0.178 | -0.698 | nan |
| price_only | ridge | logV | all | 288000 | 0.243 | 0.217 | 0.268 | nan | nan | nan | nan | nan | 0.107 | 0.104 | 0.110 | 0.243 | nan |
| price_only | gbt | x | calm | 119440 | 0.385 | 0.281 | 0.475 | 0.739 | 67066.000 | 0.715 | 0.766 | nan | nan | nan | nan | 0.385 | nan |
| price_only | gbt | x | event | 97998 | 0.677 | 0.652 | 0.698 | 0.864 | 86028.000 | 0.854 | 0.876 | nan | nan | nan | nan | 0.677 | nan |
| price_only | gbt | x | resolution | 70562 | 0.411 | 0.382 | 0.439 | 0.840 | 62884.000 | 0.825 | 0.855 | nan | nan | nan | nan | 0.411 | nan |
| price_only | gbt | x | all | 288000 | 0.564 | 0.543 | 0.584 | 0.818 | 215978.000 | 0.808 | 0.831 | nan | nan | nan | nan | 0.564 | nan |
| price_only | gbt | logV | calm | 119440 | -0.010 | -0.055 | 0.027 | nan | nan | nan | nan | nan | 0.082 | 0.080 | 0.085 | -0.010 | nan |
| price_only | gbt | logV | event | 97998 | 0.513 | 0.490 | 0.535 | nan | nan | nan | nan | nan | 0.072 | 0.069 | 0.074 | 0.513 | nan |
| price_only | gbt | logV | resolution | 70562 | -0.517 | -0.644 | -0.419 | nan | nan | nan | nan | nan | 0.157 | 0.151 | 0.164 | -0.517 | nan |
| price_only | gbt | logV | all | 288000 | 0.376 | 0.359 | 0.394 | nan | nan | nan | nan | nan | 0.097 | 0.095 | 0.100 | 0.376 | nan |
| price_only | mlp | x | calm | 119440 | 0.403 | 0.294 | 0.495 | 0.738 | 67066.000 | 0.714 | 0.763 | nan | nan | nan | nan | 0.403 | nan |
| price_only | mlp | x | event | 97998 | 0.712 | 0.686 | 0.735 | 0.871 | 86028.000 | 0.863 | 0.881 | nan | nan | nan | nan | 0.712 | nan |
| price_only | mlp | x | resolution | 70562 | 0.506 | 0.475 | 0.536 | 0.869 | 62884.000 | 0.856 | 0.881 | nan | nan | nan | nan | 0.506 | nan |
| price_only | mlp | x | all | 288000 | 0.612 | 0.589 | 0.632 | 0.829 | 215978.000 | 0.820 | 0.840 | nan | nan | nan | nan | 0.612 | nan |
| price_only | mlp | logV | calm | 119440 | 0.026 | -0.020 | 0.065 | nan | nan | nan | nan | nan | 0.083 | 0.080 | 0.085 | 0.026 | nan |
| price_only | mlp | logV | event | 97998 | 0.498 | 0.471 | 0.524 | nan | nan | nan | nan | nan | 0.072 | 0.070 | 0.075 | 0.498 | nan |
| price_only | mlp | logV | resolution | 70562 | -0.345 | -0.450 | -0.252 | nan | nan | nan | nan | nan | 0.143 | 0.137 | 0.149 | -0.345 | nan |
| price_only | mlp | logV | all | 288000 | 0.414 | 0.395 | 0.432 | nan | nan | nan | nan | nan | 0.094 | 0.092 | 0.096 | 0.414 | nan |

## L2b composite phase clock

Macro-class accuracy: full 87.2%, price-only 70.7%, day-only 52.8%, majority class 41.5%. Selectivity = +16.4% vs margin 10% -> FAIL.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 44.8%; accuracy price-only 74.3%, price+IV 78.4%, full 85.1%; recall of sustained-bull days: price-only 77.9%, price+IV 78.5%, full 91.1% (reported; no pre-registered threshold).

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 40000 | 0.114 | 0.868 | 0.775 | 0.636 |
| bull_trap | calm | 18268 | 0.111 | 0.864 | 0.768 | 0.627 |
| bull_trap | mania | 30106 | 0.152 | 0.894 | 0.821 | 0.717 |
| bull_trap | blow-off | 14860 | 0.573 | 0.997 | 0.994 | 0.989 |
| bull_trap | post-top | 16766 | 0.289 | 0.948 | 0.910 | 0.853 |
| sustained_bull | sustained-bull | 40000 | 0.014 | 0.180 | 0.050 | 0.007 |
| crash | calm | 50197 | 0.112 | 0.873 | 0.779 | 0.636 |
| crash | deterioration | 22087 | 0.119 | 0.865 | 0.782 | 0.661 |
| crash | panic | 33920 | 0.244 | 0.961 | 0.933 | 0.885 |
| crash | stabilisation | 53796 | 0.189 | 0.933 | 0.885 | 0.811 |
| flat | ALL | 40000 | 0.114 | 0.868 | 0.775 | 0.636 |
| bull_trap | ALL | 80000 | 0.208 | 0.918 | 0.860 | 0.776 |
| sustained_bull | ALL | 40000 | 0.014 | 0.180 | 0.050 | 0.007 |
| crash | ALL | 160000 | 0.161 | 0.910 | 0.848 | 0.751 |
