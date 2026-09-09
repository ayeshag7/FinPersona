# Section 5 audit on the frozen generator (Phase 6; stored panel sep_phase5_after.pkl, 1600 paths, T=200; 'n/m' as cap + indicator; derived gates)

Rendered fields audited: `price`, `SMA20`, `SMA50`, `trend_strength`, `trend_regime`, `RSI14`, `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`, `dividend_yield`, `analyst_fair_value`, `days_since_eps_announcement`, `reported_PE_nm`; 320000 steps (1600 paths; no subsampling). Price-derived control set ('price_only' in the tables): LEVEL-FREE (returns, log P/SMA, RSI, MACD/P, trend; no price level -- v2.1 Phase 1, E1.6). Intervals (columns *_lo/*_hi): percentile cluster bootstrap over paths (500 resamples).

## L1 algebraic inversion

| candidate | fitted_k | median_APE | max_APE | p5_APE | p10_APE | p25_APE | within_1pct | within_2pct | within_5pct | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k * P (price itself) | 0.9981 | 0.0626 | 1.7107 | 0.0053 | 0.0105 | 0.0270 | 0.0949 | 0.1902 | 0.4261 | 0.9051 | 0.5671 | True |
| k * P * dividend_yield | 0.4199 | 0.6184 | 16.8072 | 0.0687 | 0.1326 | 0.3158 | 0.0071 | 0.0145 | 0.0359 | 0.9929 | 0.5671 | True |
| k * P / reported_PE | 17.7520 | 0.6241 | 17.8646 | 0.0689 | 0.1340 | 0.3059 | 0.0071 | 0.0144 | 0.0358 | 0.9929 | 0.5671 | True |
| k * analyst_fair_value | 2.1745 | 0.7007 | 40.0229 | 0.0801 | 0.1566 | 0.3740 | 0.0062 | 0.0122 | 0.0301 | 0.9938 | 0.5671 | True |

## L2 statistical surrogate (held-out seeds, best model per phase group)

Absolute (plan literal, reported): calm best R2(x) = -0.614, sign accuracy on resolvable steps = 0.654 -> PASS (R2 <= 0.30, sign <= 0.70); event best R2(x) = 0.454, MAPE(V) = 12.8% -> PASS (R2 < 0.90, MAPE >= 10%).

Selectivity of the non-price fields (exploratory, NOT a gate): best-full minus best-price-only R2(x) = 0.028 (worst phase group), MAPE(V) gain = 1.7%, max shuffled-V R2 = 0.001. Interpretation (v2.1 Phase 0): the price-only strength is dominated by the fixed start price V_1 = P_1 = 100 acting as an answer key, not by price dynamics -- a level-free reader reaches R2(x) ~0.49 (sign accuracy 0.74) instead of 0.85 (0.95) on the anchored panel, and with the start price randomised the non-price fields add ~+0.6 R2(x) in calm (generated/v2_1/findings_reproduction.md, block R3; reviews C.2-C.3). The earlier reading 'hidden from the fields, NOT from price dynamics' is withdrawn. Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.

| feature_set | model | target | phase_group | n | R2 | R2_lo | R2_hi | sign_acc_resolvable | n_resolvable | sign_lo | sign_hi | R2_shuffledV | MAPE_V | MAPE_lo | MAPE_hi | R2_price_only | selectivity_R2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | ridge | x | calm | 119336 | -0.614 | -0.729 | -0.503 | 0.654 | 43344.000 | 0.630 | 0.675 | -0.010 | nan | nan | nan | -0.324 | -0.290 |
| full | ridge | x | event | 96125 | 0.435 | 0.401 | 0.470 | 0.897 | 76675.000 | 0.888 | 0.906 | -0.004 | nan | nan | nan | 0.413 | 0.022 |
| full | ridge | x | resolution | 72539 | 0.254 | 0.210 | 0.296 | 0.707 | 51897.000 | 0.692 | 0.723 | -0.011 | nan | nan | nan | 0.142 | 0.112 |
| full | ridge | x | all | 288000 | 0.392 | 0.374 | 0.410 | 0.778 | 171916.000 | 0.768 | 0.788 | -0.004 | nan | nan | nan | 0.371 | 0.021 |
| full | ridge | logV | calm | 119336 | 0.231 | 0.184 | 0.287 | nan | nan | nan | nan | -0.006 | 0.113 | 0.108 | 0.117 | 0.182 | 0.049 |
| full | ridge | logV | event | 96125 | 0.386 | 0.334 | 0.426 | nan | nan | nan | nan | -0.003 | 0.133 | 0.127 | 0.139 | 0.400 | -0.014 |
| full | ridge | logV | resolution | 72539 | -0.100 | -0.186 | -0.039 | nan | nan | nan | nan | 0.001 | 0.194 | 0.184 | 0.204 | -0.261 | 0.161 |
| full | ridge | logV | all | 288000 | 0.373 | 0.355 | 0.394 | nan | nan | nan | nan | -0.002 | 0.140 | 0.136 | 0.144 | 0.329 | 0.044 |
| full | gbt | x | calm | 119336 | -0.716 | -0.905 | -0.555 | 0.685 | 43344.000 | 0.661 | 0.708 | -0.048 | nan | nan | nan | -0.462 | -0.254 |
| full | gbt | x | event | 96125 | 0.454 | 0.419 | 0.489 | 0.891 | 76675.000 | 0.881 | 0.900 | -0.051 | nan | nan | nan | 0.433 | 0.021 |
| full | gbt | x | resolution | 72539 | 0.356 | 0.310 | 0.399 | 0.764 | 51897.000 | 0.749 | 0.781 | -0.052 | nan | nan | nan | 0.278 | 0.078 |
| full | gbt | x | all | 288000 | 0.421 | 0.398 | 0.444 | 0.800 | 171916.000 | 0.791 | 0.810 | -0.046 | nan | nan | nan | 0.406 | 0.015 |
| full | gbt | logV | calm | 119336 | 0.311 | 0.267 | 0.365 | nan | nan | nan | nan | -0.059 | 0.104 | 0.100 | 0.109 | 0.238 | 0.072 |
| full | gbt | logV | event | 96125 | 0.433 | 0.380 | 0.477 | nan | nan | nan | nan | -0.080 | 0.128 | 0.123 | 0.134 | 0.381 | 0.052 |
| full | gbt | logV | resolution | 72539 | 0.191 | 0.119 | 0.245 | nan | nan | nan | nan | -0.072 | 0.159 | 0.152 | 0.168 | -0.024 | 0.216 |
| full | gbt | logV | all | 288000 | 0.471 | 0.449 | 0.492 | nan | nan | nan | nan | -0.069 | 0.126 | 0.123 | 0.130 | 0.389 | 0.081 |
| full | mlp | x | calm | 119336 | -1.187 | -1.433 | -0.975 | 0.703 | 43344.000 | 0.681 | 0.723 | -0.141 | nan | nan | nan | -0.601 | -0.586 |
| full | mlp | x | event | 96125 | 0.439 | 0.404 | 0.477 | 0.865 | 76675.000 | 0.855 | 0.876 | -0.209 | nan | nan | nan | 0.485 | -0.046 |
| full | mlp | x | resolution | 72539 | 0.277 | 0.221 | 0.324 | 0.761 | 51897.000 | 0.748 | 0.775 | -0.195 | nan | nan | nan | 0.328 | -0.050 |
| full | mlp | x | all | 288000 | 0.365 | 0.337 | 0.391 | 0.793 | 171916.000 | 0.785 | 0.802 | -0.176 | nan | nan | nan | 0.440 | -0.075 |
| full | mlp | logV | calm | 119336 | 0.237 | 0.187 | 0.298 | nan | nan | nan | nan | -0.150 | 0.111 | 0.107 | 0.116 | 0.258 | -0.021 |
| full | mlp | logV | event | 96125 | 0.323 | 0.255 | 0.384 | nan | nan | nan | nan | -0.207 | 0.140 | 0.134 | 0.146 | 0.388 | -0.065 |
| full | mlp | logV | resolution | 72539 | 0.124 | 0.042 | 0.189 | nan | nan | nan | nan | -0.133 | 0.161 | 0.153 | 0.171 | 0.010 | 0.114 |
| full | mlp | logV | all | 288000 | 0.404 | 0.373 | 0.433 | nan | nan | nan | nan | -0.162 | 0.133 | 0.130 | 0.137 | 0.405 | -0.000 |
| price_only | ridge | x | calm | 119336 | -0.324 | -0.407 | -0.249 | 0.665 | 43344.000 | 0.640 | 0.687 | nan | nan | nan | nan | -0.324 | nan |
| price_only | ridge | x | event | 96125 | 0.413 | 0.378 | 0.445 | 0.904 | 76675.000 | 0.896 | 0.911 | nan | nan | nan | nan | 0.413 | nan |
| price_only | ridge | x | resolution | 72539 | 0.142 | 0.092 | 0.188 | 0.644 | 51897.000 | 0.628 | 0.661 | nan | nan | nan | nan | 0.142 | nan |
| price_only | ridge | x | all | 288000 | 0.371 | 0.356 | 0.385 | 0.765 | 171916.000 | 0.754 | 0.774 | nan | nan | nan | nan | 0.371 | nan |
| price_only | ridge | logV | calm | 119336 | 0.182 | 0.141 | 0.226 | nan | nan | nan | nan | nan | 0.115 | 0.110 | 0.119 | 0.182 | nan |
| price_only | ridge | logV | event | 96125 | 0.400 | 0.356 | 0.438 | nan | nan | nan | nan | nan | 0.131 | 0.125 | 0.136 | 0.400 | nan |
| price_only | ridge | logV | resolution | 72539 | -0.261 | -0.364 | -0.187 | nan | nan | nan | nan | nan | 0.210 | 0.199 | 0.222 | -0.261 | nan |
| price_only | ridge | logV | all | 288000 | 0.329 | 0.314 | 0.343 | nan | nan | nan | nan | nan | 0.144 | 0.140 | 0.148 | 0.329 | nan |
| price_only | gbt | x | calm | 119336 | -0.462 | -0.569 | -0.368 | 0.646 | 43344.000 | 0.621 | 0.667 | nan | nan | nan | nan | -0.462 | nan |
| price_only | gbt | x | event | 96125 | 0.433 | 0.398 | 0.465 | 0.896 | 76675.000 | 0.888 | 0.904 | nan | nan | nan | nan | 0.433 | nan |
| price_only | gbt | x | resolution | 72539 | 0.278 | 0.240 | 0.314 | 0.734 | 51897.000 | 0.720 | 0.748 | nan | nan | nan | nan | 0.278 | nan |
| price_only | gbt | x | all | 288000 | 0.406 | 0.390 | 0.420 | 0.784 | 171916.000 | 0.775 | 0.793 | nan | nan | nan | nan | 0.406 | nan |
| price_only | gbt | logV | calm | 119336 | 0.238 | 0.203 | 0.276 | nan | nan | nan | nan | nan | 0.111 | 0.106 | 0.115 | 0.238 | nan |
| price_only | gbt | logV | event | 96125 | 0.381 | 0.332 | 0.424 | nan | nan | nan | nan | nan | 0.133 | 0.127 | 0.139 | 0.381 | nan |
| price_only | gbt | logV | resolution | 72539 | -0.024 | -0.092 | 0.030 | nan | nan | nan | nan | nan | 0.182 | 0.173 | 0.192 | -0.024 | nan |
| price_only | gbt | logV | all | 288000 | 0.389 | 0.373 | 0.408 | nan | nan | nan | nan | nan | 0.136 | 0.132 | 0.140 | 0.389 | nan |
| price_only | mlp | x | calm | 119336 | -0.601 | -0.726 | -0.494 | 0.651 | 43344.000 | 0.629 | 0.672 | nan | nan | nan | nan | -0.601 | nan |
| price_only | mlp | x | event | 96125 | 0.485 | 0.453 | 0.517 | 0.895 | 76675.000 | 0.887 | 0.903 | nan | nan | nan | nan | 0.485 | nan |
| price_only | mlp | x | resolution | 72539 | 0.328 | 0.288 | 0.363 | 0.773 | 51897.000 | 0.760 | 0.786 | nan | nan | nan | nan | 0.328 | nan |
| price_only | mlp | x | all | 288000 | 0.440 | 0.423 | 0.455 | 0.797 | 171916.000 | 0.788 | 0.805 | nan | nan | nan | nan | 0.440 | nan |
| price_only | mlp | logV | calm | 119336 | 0.258 | 0.220 | 0.298 | nan | nan | nan | nan | nan | 0.110 | 0.106 | 0.114 | 0.258 | nan |
| price_only | mlp | logV | event | 96125 | 0.388 | 0.335 | 0.439 | nan | nan | nan | nan | nan | 0.132 | 0.127 | 0.138 | 0.388 | nan |
| price_only | mlp | logV | resolution | 72539 | 0.010 | -0.058 | 0.063 | nan | nan | nan | nan | nan | 0.177 | 0.168 | 0.186 | 0.010 | nan |
| price_only | mlp | logV | all | 288000 | 0.405 | 0.387 | 0.423 | nan | nan | nan | nan | nan | 0.134 | 0.131 | 0.138 | 0.405 | nan |

## L2b composite phase clock

Macro-class accuracy: full 67.6%, price-only 65.8%, day-only 50.8%, majority class 41.4%. Selectivity = +1.8% vs margin 10% -> PASS.

## Scenario discrimination (review D5): sustained-bull vs bull-trap mania vs calm days

n = 144000, majority 37.7%; accuracy price-only 53.8%, price+IV 53.7%, full 49.5%; recall of sustained-bull days: price-only 20.3%, price+IV 20.9%, full 20.6% (reported; no pre-registered threshold).

## L4 resolvability (|x| >= theta)

| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 40000 | 0.037 | 0.587 | 0.366 | 0.172 |
| bull_trap | calm | 18151 | 0.037 | 0.580 | 0.366 | 0.169 |
| bull_trap | mania | 22356 | 0.076 | 0.793 | 0.667 | 0.476 |
| bull_trap | blow-off | 33439 | 0.317 | 0.996 | 0.992 | 0.983 |
| sustained_bull | sustained-bull | 40000 | 0.037 | 0.584 | 0.366 | 0.174 |
| crash | calm | 50178 | 0.036 | 0.577 | 0.361 | 0.168 |
| crash | deterioration | 7849 | 0.039 | 0.594 | 0.384 | 0.182 |
| crash | panic | 35488 | 0.114 | 0.849 | 0.754 | 0.625 |
| crash | stabilisation | 66485 | 0.088 | 0.810 | 0.691 | 0.536 |
| bull_trap | post-top | 6054 | 0.246 | 0.990 | 0.978 | 0.955 |
| flat | ALL | 40000 | 0.037 | 0.587 | 0.366 | 0.172 |
| bull_trap | ALL | 80000 | 0.153 | 0.844 | 0.758 | 0.655 |
| sustained_bull | ALL | 40000 | 0.037 | 0.584 | 0.366 | 0.174 |
| crash | ALL | 160000 | 0.065 | 0.735 | 0.587 | 0.423 |

## Derived gates (PREREG_PHASE_6.md sections 6-8; re-attached from the criteria file)

L1: ceiling 0.6167 on the within-5 % share -> PASS.

- l2_all: measured +0.0263, null median -0.0481, p95 -0.0362 (40 draws), margin -0.0214 -> FAIL; centred margin +0.0267 -> PASS
- l2_calm: measured +0.1088, null median -0.0692, p95 -0.0542 (20 draws), margin -0.0313 -> FAIL; centred margin +0.0379 -> FAIL
- l2b: measured +0.0295, null median -0.0129, p95 -0.0081 (20 draws), margin -0.0023 -> FAIL; the audit's own L2b selectivity +0.0181 -> FAIL; centred margin +0.0105 -> FAIL

audit GBT all-rows selectivity (the audit's own construction): +0.0147
