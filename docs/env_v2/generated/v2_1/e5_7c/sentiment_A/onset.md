# E5.7(c) onset-detection audit -- sentiment_A

200 crash + 200 bull-trap seeds, schedule pinned v21, overrides {"multiple": {"design": "v2"}, "eps": {"design": "v2"}, "dividend": {"design": "v2"}, "analyst": {"design": "v2"}, "sentiment": {"design": "A", "rho": 0.21127624401947614, "b0": 0.011336005215507806, "b1": 0.11097693054019067, "sd_e": 0.971818924981291, "s_raw": 0.3970515881879271, "c_val": 0.9499320900953079, "c_val_full": 0.9499320900953079, "link_size": "full", "rho_w": 0.5339356961700638, "b0_w": 0.2980105377069622, "b1_w": 0.19940872764652662, "sd_e_w": 0.7593161575955316, "update_days": 5, "full_sample_fit": {"rho": 0.4026031062150719, "b0_per_sd_raw": 0.011751427478029973, "b1_per_sd_raw": 0.08442584293369898, "sd_resid_per_sd_raw": 0.9103032882304359}}, "volume": {"design": "v2"}}; 500 circular-shift null draws. Rule: dAUC (field - best price-derived reference) <= null p95.

## crash:calm->deterioration (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.578 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.613 | +0.0351 | +0.0010 | **NO** | +2 [-3.0, 5.0] |
| RSI14 | 0.578 | +0.0000 | +0.0000 | yes | +1 [-4.0, 5.0] |
| volume_ratio | 0.545 | -0.0331 | +0.0051 | yes | +5 [0.0, 8.0] |
| implied_volatility | 0.535 | -0.0432 | +0.0069 | yes | +2 [-0.25, 6.0] |
| trend_regime | 0.502 | -0.0760 | +0.0066 | yes | -7 [-10.0, 1.0] |
| dividend_yield | 0.501 | -0.0768 | +0.0006 | yes | +4 [1.0, 8.0] |
| reported_PE | 0.500 | -0.0778 | +0.0011 | yes | +5 [2.0, 8.0] |
| days_since_eps_announcement | 0.499 | -0.0786 | +0.0066 | yes | -10 [-10.0, -5.0] |
| sentiment_change | 0.497 | -0.0813 | +0.0119 | yes | +0 [-6.0, 5.0] |
| news_sentiment | 0.497 | -0.0813 | +0.0125 | yes | +0 [-5.0, 5.0] |
| MACD | 0.493 | -0.0852 | +0.0047 | yes | +7 [4.0, 9.0] |
| sentiment_MA5 | 0.490 | -0.0885 | +0.0134 | yes | -1 [-6.0, 5.0] |
| volume | 0.485 | -0.0933 | +0.0099 | yes | +3 [-1.25, 7.0] |
| SMA20 | 0.438 | -0.1401 | +0.0173 | yes | +9 [4.0, 10.0] |
| MACD_signal | 0.432 | -0.1461 | +0.0134 | yes | +8 [6.0, 10.0] |
| SMA50 | 0.423 | -0.1553 | +0.0274 | yes | +8 [-1.25, 10.0] |
| trend_strength | 0.421 | -0.1570 | +0.0220 | yes | +7 [-0.25, 10.0] |

## crash:deterioration->panic (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.734 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| MACD | 0.741 | +0.0074 | +0.0000 | **NO** | +5 [2.0, 8.0] |
| SMA20 | 0.739 | +0.0054 | +0.0061 | yes | +7 [3.0, 9.0] |
| MACD_signal | 0.735 | +0.0007 | +0.0067 | yes | +5 [2.0, 8.25] |
| volume_ratio | 0.658 | -0.0755 | +0.0041 | yes | +5 [2.0, 8.0] |
| analyst_fair_value | 0.646 | -0.0879 | +0.0054 | yes | +0 [-4.0, 3.0] |
| reported_PE | 0.632 | -0.1022 | -0.0003 | yes | +5 [3.0, 8.0] |
| trend_strength | 0.631 | -0.1030 | +0.0172 | yes | +5 [1.0, 9.0] |
| dividend_yield | 0.631 | -0.1033 | -0.0007 | yes | +5 [2.75, 8.0] |
| SMA50 | 0.594 | -0.1399 | +0.0264 | yes | +7 [3.0, 10.0] |
| implied_volatility | 0.575 | -0.1587 | +0.0095 | yes | +2 [-2.0, 5.25] |
| volume | 0.549 | -0.1848 | +0.0102 | yes | +4 [1.0, 8.0] |
| RSI14 | 0.530 | -0.2037 | +0.0000 | yes | +3 [-2.0, 6.0] |
| trend_regime | 0.513 | -0.2211 | +0.0109 | yes | -7 [-10.0, -2.0] |
| sentiment_change | 0.506 | -0.2276 | +0.0152 | yes | +0 [-5.0, 5.0] |
| news_sentiment | 0.505 | -0.2284 | +0.0157 | yes | +0 [-5.0, 6.0] |
| days_since_eps_announcement | 0.501 | -0.2330 | +0.0111 | yes | -10 [-10.0, -4.0] |
| sentiment_MA5 | 0.500 | -0.2339 | +0.0173 | yes | -1 [-5.25, 5.0] |

## crash:panic->stabilisation (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.659 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.758 | +0.0988 | +0.0008 | **NO** | -0 [-6.0, 5.0] |
| SMA20 | 0.711 | +0.0518 | -0.0002 | **NO** | -3 [-7.0, 2.0] |
| MACD | 0.709 | +0.0499 | -0.0077 | **NO** | -4 [-7.0, -1.0] |
| MACD_signal | 0.704 | +0.0453 | -0.0043 | **NO** | -4 [-7.0, 0.0] |
| dividend_yield | 0.632 | -0.0269 | -0.0078 | yes | -4 [-7.0, -1.0] |
| reported_PE | 0.630 | -0.0288 | -0.0071 | yes | -4 [-7.0, -0.75] |
| trend_strength | 0.614 | -0.0449 | +0.0079 | yes | -1 [-6.0, 5.25] |
| volume | 0.598 | -0.0610 | +0.0025 | yes | -3 [-7.0, 0.0] |
| volume_ratio | 0.550 | -0.1085 | +0.0092 | yes | -4 [-8.0, 0.0] |
| analyst_fair_value | 0.513 | -0.1457 | +0.0084 | yes | +0 [-5.0, 5.0] |
| sentiment_change | 0.508 | -0.1504 | +0.0116 | yes | -1 [-6.0, 5.0] |
| news_sentiment | 0.508 | -0.1510 | +0.0121 | yes | -1 [-6.0, 6.0] |
| sentiment_MA5 | 0.505 | -0.1540 | +0.0125 | yes | -1 [-6.0, 4.0] |
| days_since_eps_announcement | 0.502 | -0.1573 | +0.0067 | yes | -10 [-10.0, -3.0] |
| implied_volatility | 0.499 | -0.1598 | +0.0118 | yes | -3 [-7.0, 2.0] |
| trend_regime | 0.492 | -0.1669 | +0.0076 | yes | -10 [-10.0, -6.75] |
| RSI14 | 0.440 | -0.2188 | +0.0000 | yes | -3 [-7.0, 0.0] |

## bull_trap:calm->mania (n = 200 paths; 1400 positive / 31992 negative days; reference AUC 0.499 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.505 | +0.0054 | +0.0052 | **NO** | +0 [-5.0, 4.25] |
| trend_regime | 0.503 | +0.0032 | +0.0011 | **NO** | -7 [-10.0, -1.0] |
| implied_volatility | 0.502 | +0.0030 | +0.0069 | yes | +0 [-6.0, 5.0] |
| RSI14 | 0.499 | +0.0000 | +0.0000 | yes | +0 [-4.25, 5.0] |
| days_since_eps_announcement | 0.498 | -0.0018 | +0.0022 | yes | -10 [-10.0, -7.0] |
| news_sentiment | 0.496 | -0.0034 | +0.0074 | yes | +0 [-5.0, 5.0] |
| sentiment_change | 0.496 | -0.0034 | +0.0077 | yes | +0 [-5.25, 4.0] |
| sentiment_MA5 | 0.494 | -0.0051 | +0.0072 | yes | -1 [-6.0, 4.0] |
| MACD | 0.486 | -0.0133 | +0.0075 | yes | +0 [-5.0, 4.0] |
| reported_PE | 0.481 | -0.0183 | +0.0010 | yes | +1 [-4.0, 5.0] |
| dividend_yield | 0.477 | -0.0220 | +0.0010 | yes | +1 [-4.0, 5.0] |
| volume | 0.474 | -0.0255 | +0.0082 | yes | -1 [-6.0, 5.0] |
| trend_strength | 0.474 | -0.0259 | +0.0194 | yes | +0 [-6.25, 6.0] |
| MACD_signal | 0.473 | -0.0267 | +0.0156 | yes | +0 [-6.0, 5.25] |
| volume_ratio | 0.464 | -0.0351 | +0.0105 | yes | +1 [-4.0, 5.25] |
| SMA20 | 0.438 | -0.0619 | +0.0235 | yes | +0 [-6.0, 6.0] |
| SMA50 | 0.397 | -0.1024 | +0.0283 | yes | +0 [-6.0, 6.0] |

## bull_trap:mania->blow-off (n = 200 paths; 1400 positive / 31992 negative days; reference AUC 0.535 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.578 | +0.0421 | +0.0168 | **NO** | +3 [-5.0, 8.0] |
| SMA20 | 0.577 | +0.0419 | +0.0151 | **NO** | +1 [-6.0, 7.0] |
| volume_ratio | 0.529 | -0.0068 | +0.0074 | yes | +2 [-4.0, 7.0] |
| dividend_yield | 0.523 | -0.0124 | -0.0003 | yes | +1 [-5.25, 7.0] |
| reported_PE | 0.521 | -0.0143 | +0.0000 | yes | +1 [-5.0, 6.0] |
| trend_strength | 0.513 | -0.0229 | +0.0160 | yes | -1 [-7.0, 6.0] |
| analyst_fair_value | 0.511 | -0.0249 | +0.0070 | yes | +0 [-6.0, 6.0] |
| RSI14 | 0.510 | -0.0251 | +0.0000 | yes | +1 [-5.0, 5.0] |
| volume | 0.510 | -0.0254 | +0.0082 | yes | -1 [-6.0, 5.0] |
| implied_volatility | 0.501 | -0.0340 | +0.0097 | yes | +1 [-4.0, 5.25] |
| days_since_eps_announcement | 0.501 | -0.0349 | +0.0032 | yes | -10 [-10.0, -5.0] |
| news_sentiment | 0.500 | -0.0356 | +0.0098 | yes | +0 [-6.0, 6.0] |
| trend_regime | 0.499 | -0.0367 | +0.0050 | yes | -10 [-10.0, -3.75] |
| sentiment_MA5 | 0.496 | -0.0393 | +0.0078 | yes | -1 [-6.25, 4.0] |
| sentiment_change | 0.496 | -0.0397 | +0.0101 | yes | +0 [-5.0, 5.0] |
| MACD_signal | 0.493 | -0.0420 | +0.0142 | yes | +2 [-5.0, 6.0] |
| MACD | 0.488 | -0.0479 | +0.0102 | yes | +1 [-5.0, 8.0] |

## bull_trap:blow-off->post-top (n = 23 paths; 157 positive / 31992 negative days; reference AUC 0.577 = ref_dlogPSMA20)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.658 | +0.0802 | +0.0903 | yes | -7 [-9.5, -1.0] |
| SMA20 | 0.598 | +0.0205 | +0.0835 | yes | -2 [-7.0, 0.0] |
| dividend_yield | 0.564 | -0.0136 | -0.0023 | yes | -4 [-6.5, -1.5] |
| reported_PE | 0.552 | -0.0254 | -0.0039 | yes | -5 [-8.0, -4.0] |
| implied_volatility | 0.551 | -0.0268 | +0.0231 | yes | +2 [-7.5, 5.5] |
| MACD_signal | 0.548 | -0.0295 | +0.0586 | yes | +1 [-5.5, 8.5] |
| RSI14 | 0.536 | -0.0412 | +0.0000 | yes | -2 [-5.5, 1.0] |
| trend_strength | 0.525 | -0.0524 | +0.0796 | yes | -1 [-5.5, 8.0] |
| sentiment_change | 0.513 | -0.0647 | +0.0356 | yes | +1 [-3.5, 5.0] |
| analyst_fair_value | 0.512 | -0.0653 | +0.0229 | yes | +4 [-3.5, 7.0] |
| news_sentiment | 0.509 | -0.0682 | +0.0334 | yes | +1 [-1.5, 5.0] |
| volume | 0.504 | -0.0731 | +0.0231 | yes | -3 [-6.5, 2.5] |
| MACD | 0.499 | -0.0781 | +0.0343 | yes | +3 [-3.5, 8.0] |
| trend_regime | 0.494 | -0.0835 | +0.0197 | yes | -10 [-10.0, -4.5] |
| days_since_eps_announcement | 0.492 | -0.0855 | +0.0187 | yes | -10 [-10.0, -10.0] |
| sentiment_MA5 | 0.488 | -0.0890 | +0.0375 | yes | -2 [-5.5, 2.0] |
| volume_ratio | 0.482 | -0.0956 | +0.0188 | yes | -5 [-8.5, -0.5] |

**Verdict:** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value'), ('crash:deterioration->panic', 'MACD'), ('crash:panic->stabilisation', 'MACD'), ('crash:panic->stabilisation', 'MACD_signal'), ('crash:panic->stabilisation', 'SMA20'), ('crash:panic->stabilisation', 'SMA50'), ('bull_trap:calm->mania', 'analyst_fair_value'), ('bull_trap:calm->mania', 'trend_regime'), ('bull_trap:mania->blow-off', 'SMA20'), ('bull_trap:mania->blow-off', 'SMA50')].


**Verdict (non-price fields, ADDENDUM 1.3, applied post hoc to this stored result):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value')].
