# E5.7(c) onset-detection audit -- sentiment_B_full

200 crash + 200 bull-trap seeds, schedule pinned v21, overrides {"multiple": {"design": "v2"}, "eps": {"design": "v2"}, "dividend": {"design": "v2"}, "analyst": {"design": "v2"}, "sentiment": {"design": "B", "rho": 0.21127624401947614, "b0": 0.011336005215507806, "b1": 0.11097693054019067, "sd_e": 0.971818924981291, "s_raw": 0.3970515881879271, "c_val": 0.9499320900953079, "c_val_full": 0.9499320900953079, "link_size": "full", "rho_w": 0.5339356961700638, "b0_w": 0.2980105377069622, "b1_w": 0.19940872764652662, "sd_e_w": 0.7593161575955316, "update_days": 5, "full_sample_fit": {"rho": 0.4026031062150719, "b0_per_sd_raw": 0.011751427478029973, "b1_per_sd_raw": 0.08442584293369898, "sd_resid_per_sd_raw": 0.9103032882304359}}, "volume": {"design": "v2"}}; 500 circular-shift null draws. Rule: dAUC (field - best price-derived reference) <= null p95.

## crash:calm->deterioration (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.578 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.613 | +0.0351 | +0.0009 | **NO** | +2 [-3.0, 5.0] |
| RSI14 | 0.578 | +0.0000 | +0.0000 | yes | +1 [-4.0, 5.0] |
| volume_ratio | 0.545 | -0.0333 | +0.0053 | yes | +5 [0.0, 8.0] |
| implied_volatility | 0.535 | -0.0435 | +0.0069 | yes | +2 [-0.25, 6.0] |
| reported_PE | 0.502 | -0.0760 | +0.0010 | yes | +5 [2.0, 8.0] |
| trend_regime | 0.502 | -0.0767 | +0.0067 | yes | -7 [-10.0, 1.0] |
| dividend_yield | 0.501 | -0.0777 | +0.0006 | yes | +5 [1.0, 8.0] |
| days_since_eps_announcement | 0.499 | -0.0789 | +0.0068 | yes | -10 [-10.0, -5.0] |
| news_sentiment | 0.497 | -0.0813 | +0.0121 | yes | +1 [-5.0, 6.0] |
| sentiment_change | 0.497 | -0.0818 | +0.0118 | yes | +0 [-6.0, 5.25] |
| MACD | 0.493 | -0.0857 | +0.0046 | yes | +7 [4.0, 9.0] |
| sentiment_MA5 | 0.490 | -0.0886 | +0.0130 | yes | -1 [-6.0, 5.0] |
| volume | 0.485 | -0.0936 | +0.0099 | yes | +3 [-1.25, 7.0] |
| SMA20 | 0.438 | -0.1399 | +0.0179 | yes | +9 [4.0, 10.0] |
| MACD_signal | 0.432 | -0.1466 | +0.0134 | yes | +8 [6.0, 10.0] |
| SMA50 | 0.423 | -0.1552 | +0.0268 | yes | +7 [-2.0, 10.0] |
| trend_strength | 0.421 | -0.1576 | +0.0222 | yes | +7 [-0.25, 10.0] |

## crash:deterioration->panic (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.734 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| MACD | 0.741 | +0.0073 | +0.0005 | **NO** | +5 [2.0, 8.0] |
| SMA20 | 0.739 | +0.0052 | +0.0062 | yes | +7 [3.0, 10.0] |
| MACD_signal | 0.734 | +0.0005 | +0.0066 | yes | +5 [2.0, 8.25] |
| volume_ratio | 0.658 | -0.0755 | +0.0042 | yes | +5 [2.0, 8.0] |
| analyst_fair_value | 0.646 | -0.0879 | +0.0054 | yes | +0 [-4.0, 3.0] |
| reported_PE | 0.633 | -0.1008 | -0.0006 | yes | +5 [3.0, 8.0] |
| dividend_yield | 0.631 | -0.1027 | -0.0003 | yes | +5 [3.0, 8.0] |
| trend_strength | 0.631 | -0.1032 | +0.0174 | yes | +5 [1.0, 9.0] |
| SMA50 | 0.594 | -0.1393 | +0.0266 | yes | +7 [3.0, 10.0] |
| implied_volatility | 0.575 | -0.1585 | +0.0095 | yes | +2 [-2.0, 5.25] |
| volume | 0.549 | -0.1848 | +0.0100 | yes | +4 [1.0, 8.0] |
| RSI14 | 0.530 | -0.2036 | +0.0000 | yes | +3 [-2.0, 6.0] |
| trend_regime | 0.513 | -0.2211 | +0.0108 | yes | -7 [-10.0, -2.0] |
| sentiment_change | 0.507 | -0.2269 | +0.0156 | yes | +1 [-5.0, 6.0] |
| news_sentiment | 0.506 | -0.2276 | +0.0155 | yes | -0 [-5.0, 6.0] |
| days_since_eps_announcement | 0.501 | -0.2329 | +0.0111 | yes | -10 [-10.0, -4.0] |
| sentiment_MA5 | 0.499 | -0.2349 | +0.0187 | yes | -1 [-5.0, 5.0] |

## crash:panic->stabilisation (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.659 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.758 | +0.0992 | +0.0009 | **NO** | -0 [-6.0, 5.0] |
| SMA20 | 0.711 | +0.0521 | -0.0003 | **NO** | -3 [-7.0, 2.0] |
| MACD | 0.709 | +0.0501 | -0.0077 | **NO** | -4 [-7.0, -1.0] |
| MACD_signal | 0.704 | +0.0452 | -0.0043 | **NO** | -4 [-7.0, 0.0] |
| dividend_yield | 0.631 | -0.0280 | -0.0079 | yes | -4 [-7.0, -1.0] |
| reported_PE | 0.630 | -0.0290 | -0.0067 | yes | -4 [-7.0, 0.0] |
| trend_strength | 0.614 | -0.0451 | +0.0084 | yes | -1 [-6.0, 5.0] |
| volume | 0.598 | -0.0610 | +0.0024 | yes | -3 [-7.0, 0.0] |
| volume_ratio | 0.550 | -0.1084 | +0.0089 | yes | -4 [-8.0, 0.0] |
| analyst_fair_value | 0.513 | -0.1455 | +0.0090 | yes | +0 [-5.0, 5.0] |
| sentiment_change | 0.505 | -0.1537 | +0.0120 | yes | -1 [-6.0, 5.0] |
| news_sentiment | 0.505 | -0.1542 | +0.0120 | yes | -1 [-6.0, 5.0] |
| days_since_eps_announcement | 0.502 | -0.1572 | +0.0066 | yes | -10 [-10.0, -3.0] |
| sentiment_MA5 | 0.501 | -0.1577 | +0.0134 | yes | -2 [-7.0, 4.0] |
| implied_volatility | 0.499 | -0.1595 | +0.0119 | yes | -3 [-7.0, 2.0] |
| trend_regime | 0.492 | -0.1668 | +0.0075 | yes | -10 [-10.0, -7.0] |
| RSI14 | 0.440 | -0.2191 | +0.0000 | yes | -3 [-7.0, 0.0] |

## bull_trap:calm->mania (n = 200 paths; 1400 positive / 31954 negative days; reference AUC 0.500 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.505 | +0.0048 | +0.0058 | yes | +0 [-5.0, 5.0] |
| trend_regime | 0.503 | +0.0037 | +0.0013 | **NO** | -7 [-10.0, -1.0] |
| implied_volatility | 0.502 | +0.0024 | +0.0069 | yes | -0 [-5.25, 5.0] |
| RSI14 | 0.500 | +0.0000 | +0.0000 | yes | +0 [-5.0, 5.0] |
| sentiment_change | 0.498 | -0.0018 | +0.0072 | yes | +0 [-5.0, 4.0] |
| news_sentiment | 0.498 | -0.0020 | +0.0071 | yes | +0 [-5.0, 4.0] |
| days_since_eps_announcement | 0.498 | -0.0020 | +0.0026 | yes | -10 [-10.0, -7.0] |
| sentiment_MA5 | 0.497 | -0.0026 | +0.0074 | yes | -1 [-6.0, 4.25] |
| MACD | 0.486 | -0.0140 | +0.0078 | yes | +0 [-5.0, 4.0] |
| reported_PE | 0.481 | -0.0185 | +0.0010 | yes | +0 [-4.0, 5.0] |
| dividend_yield | 0.480 | -0.0200 | +0.0008 | yes | +1 [-4.0, 5.0] |
| volume | 0.476 | -0.0236 | +0.0075 | yes | -1 [-6.0, 5.0] |
| trend_strength | 0.473 | -0.0267 | +0.0209 | yes | +0 [-7.0, 6.0] |
| MACD_signal | 0.471 | -0.0283 | +0.0161 | yes | +0 [-6.0, 6.0] |
| volume_ratio | 0.468 | -0.0319 | +0.0102 | yes | +1 [-4.0, 6.0] |
| SMA20 | 0.437 | -0.0625 | +0.0237 | yes | +0 [-6.0, 6.0] |
| SMA50 | 0.397 | -0.1032 | +0.0280 | yes | +0 [-6.0, 6.0] |

## bull_trap:mania->blow-off (n = 200 paths; 1400 positive / 31954 negative days; reference AUC 0.537 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.578 | +0.0405 | +0.0157 | **NO** | +3 [-5.0, 8.25] |
| SMA20 | 0.578 | +0.0405 | +0.0155 | **NO** | +1 [-6.0, 7.0] |
| volume_ratio | 0.528 | -0.0093 | +0.0073 | yes | +2 [-4.0, 7.0] |
| reported_PE | 0.525 | -0.0125 | +0.0001 | yes | +1 [-5.0, 6.0] |
| dividend_yield | 0.524 | -0.0136 | +0.0004 | yes | +2 [-5.0, 7.0] |
| trend_strength | 0.513 | -0.0238 | +0.0153 | yes | -1 [-7.0, 6.0] |
| analyst_fair_value | 0.513 | -0.0243 | +0.0069 | yes | +0 [-5.25, 6.0] |
| RSI14 | 0.511 | -0.0260 | +0.0000 | yes | +1 [-4.25, 5.0] |
| volume | 0.510 | -0.0273 | +0.0087 | yes | -1 [-6.0, 5.0] |
| implied_volatility | 0.502 | -0.0354 | +0.0093 | yes | +2 [-4.0, 6.0] |
| days_since_eps_announcement | 0.501 | -0.0365 | +0.0033 | yes | -10 [-10.0, -5.0] |
| trend_regime | 0.499 | -0.0382 | +0.0049 | yes | -10 [-10.0, -3.75] |
| news_sentiment | 0.499 | -0.0385 | +0.0097 | yes | -0 [-6.0, 5.25] |
| sentiment_MA5 | 0.497 | -0.0402 | +0.0093 | yes | -1 [-6.0, 4.0] |
| MACD_signal | 0.496 | -0.0413 | +0.0145 | yes | +2 [-5.0, 6.0] |
| sentiment_change | 0.494 | -0.0428 | +0.0097 | yes | +0 [-5.0, 5.0] |
| MACD | 0.489 | -0.0483 | +0.0103 | yes | +1 [-5.0, 8.0] |

## bull_trap:blow-off->post-top (n = 25 paths; 171 positive / 31954 negative days; reference AUC 0.581 = ref_dlogPSMA20)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.659 | +0.0783 | +0.0787 | yes | -8 [-10.0, -2.0] |
| SMA20 | 0.623 | +0.0419 | +0.0724 | yes | -1 [-6.0, 0.0] |
| MACD_signal | 0.563 | -0.0174 | +0.0598 | yes | +1 [-5.0, 8.0] |
| reported_PE | 0.563 | -0.0181 | -0.0037 | yes | -5 [-7.0, -2.0] |
| implied_volatility | 0.554 | -0.0274 | +0.0263 | yes | +1 [-8.0, 5.0] |
| dividend_yield | 0.549 | -0.0322 | -0.0004 | yes | -4 [-7.0, -2.0] |
| trend_strength | 0.534 | -0.0464 | +0.0787 | yes | -1 [-7.0, 8.0] |
| RSI14 | 0.534 | -0.0470 | +0.0000 | yes | -2 [-5.0, 1.0] |
| MACD | 0.515 | -0.0662 | +0.0316 | yes | +3 [-3.0, 8.0] |
| analyst_fair_value | 0.510 | -0.0709 | +0.0220 | yes | +3 [-5.0, 7.0] |
| volume | 0.507 | -0.0735 | +0.0204 | yes | -3 [-6.0, 2.0] |
| trend_regime | 0.496 | -0.0849 | +0.0207 | yes | -10 [-10.0, -4.0] |
| volume_ratio | 0.495 | -0.0856 | +0.0177 | yes | -5 [-8.0, 0.0] |
| days_since_eps_announcement | 0.492 | -0.0889 | +0.0161 | yes | -10 [-10.0, -10.0] |
| sentiment_change | 0.492 | -0.0892 | +0.0334 | yes | +0 [-5.0, 5.0] |
| sentiment_MA5 | 0.491 | -0.0900 | +0.0352 | yes | -3 [-7.0, 0.0] |
| news_sentiment | 0.487 | -0.0941 | +0.0306 | yes | +0 [-5.0, 5.0] |

**Verdict (as registered):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value'), ('crash:deterioration->panic', 'MACD'), ('crash:panic->stabilisation', 'MACD'), ('crash:panic->stabilisation', 'MACD_signal'), ('crash:panic->stabilisation', 'SMA20'), ('crash:panic->stabilisation', 'SMA50'), ('bull_trap:calm->mania', 'trend_regime'), ('bull_trap:mania->blow-off', 'SMA20'), ('bull_trap:mania->blow-off', 'SMA50')].

**Verdict (non-price fields, ADDENDUM 1.3):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value')].

