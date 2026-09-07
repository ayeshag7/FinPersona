# E5.7(c) onset-detection audit -- sentiment_C

200 crash + 200 bull-trap seeds, schedule pinned v21, overrides {"multiple": {"design": "v2"}, "eps": {"design": "v2"}, "dividend": {"design": "v2"}, "analyst": {"design": "v2"}, "sentiment": {"design": "C", "rho": 0.21127624401947614, "b0": 0.011336005215507806, "b1": 0.11097693054019067, "sd_e": 0.971818924981291, "s_raw": 0.3970515881879271, "c_val": 0.9499320900953079, "c_val_full": 0.9499320900953079, "link_size": "full", "rho_w": 0.5339356961700638, "b0_w": 0.2980105377069622, "b1_w": 0.19940872764652662, "sd_e_w": 0.7593161575955316, "update_days": 5, "full_sample_fit": {"rho": 0.4026031062150719, "b0_per_sd_raw": 0.011751427478029973, "b1_per_sd_raw": 0.08442584293369898, "sd_resid_per_sd_raw": 0.9103032882304359}}, "volume": {"design": "v2"}}; 500 circular-shift null draws. Rule: dAUC (field - best price-derived reference) <= null p95.

## crash:calm->deterioration (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.578 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.613 | +0.0350 | +0.0007 | **NO** | +2 [-3.0, 5.0] |
| RSI14 | 0.578 | +0.0000 | +0.0000 | yes | +1 [-3.0, 4.25] |
| volume_ratio | 0.544 | -0.0344 | +0.0055 | yes | +5 [0.0, 8.0] |
| implied_volatility | 0.535 | -0.0431 | +0.0067 | yes | +2 [-0.25, 6.0] |
| trend_regime | 0.503 | -0.0750 | +0.0069 | yes | -7 [-10.0, 0.25] |
| reported_PE | 0.502 | -0.0763 | +0.0013 | yes | +5 [2.0, 8.0] |
| dividend_yield | 0.500 | -0.0782 | +0.0008 | yes | +5 [2.0, 8.0] |
| days_since_eps_announcement | 0.499 | -0.0789 | +0.0066 | yes | -10 [-10.0, -5.0] |
| news_sentiment | 0.499 | -0.0796 | +0.0071 | yes | +3 [-4.0, 7.0] |
| sentiment_change | 0.493 | -0.0852 | +0.0134 | yes | +3 [-4.0, 7.0] |
| MACD | 0.493 | -0.0858 | +0.0048 | yes | +7 [4.0, 9.0] |
| sentiment_MA5 | 0.492 | -0.0860 | +0.0143 | yes | +2 [-8.0, 7.0] |
| volume | 0.485 | -0.0937 | +0.0098 | yes | +3 [-2.0, 7.0] |
| SMA20 | 0.440 | -0.1384 | +0.0173 | yes | +9 [4.0, 10.0] |
| MACD_signal | 0.433 | -0.1456 | +0.0133 | yes | +8 [6.0, 10.0] |
| SMA50 | 0.424 | -0.1542 | +0.0272 | yes | +7 [-1.0, 10.0] |
| trend_strength | 0.423 | -0.1553 | +0.0224 | yes | +6 [-0.25, 9.25] |

## crash:deterioration->panic (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.736 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| MACD | 0.742 | +0.0064 | -0.0004 | **NO** | +5 [1.75, 8.0] |
| SMA20 | 0.738 | +0.0023 | +0.0068 | yes | +7 [3.0, 9.0] |
| MACD_signal | 0.735 | -0.0009 | +0.0064 | yes | +5 [2.0, 8.0] |
| volume_ratio | 0.659 | -0.0769 | +0.0044 | yes | +5 [2.0, 8.0] |
| analyst_fair_value | 0.646 | -0.0898 | +0.0054 | yes | +0 [-4.0, 3.0] |
| reported_PE | 0.632 | -0.1035 | -0.0003 | yes | +5 [3.0, 8.0] |
| dividend_yield | 0.631 | -0.1045 | -0.0008 | yes | +5 [3.0, 8.0] |
| trend_strength | 0.630 | -0.1062 | +0.0179 | yes | +5 [1.0, 9.0] |
| SMA50 | 0.595 | -0.1411 | +0.0267 | yes | +7 [3.0, 10.0] |
| implied_volatility | 0.575 | -0.1605 | +0.0093 | yes | +2 [-2.0, 5.25] |
| volume | 0.549 | -0.1866 | +0.0098 | yes | +4 [1.0, 8.0] |
| sentiment_MA5 | 0.532 | -0.2039 | +0.0252 | yes | +0 [-6.25, 4.25] |
| RSI14 | 0.530 | -0.2059 | +0.0000 | yes | +3 [-2.0, 6.0] |
| sentiment_change | 0.526 | -0.2096 | +0.0217 | yes | +0 [-4.0, 4.25] |
| trend_regime | 0.513 | -0.2229 | +0.0115 | yes | -7 [-10.0, -2.0] |
| news_sentiment | 0.502 | -0.2342 | +0.0122 | yes | +0 [-4.0, 5.0] |
| days_since_eps_announcement | 0.501 | -0.2350 | +0.0113 | yes | -10 [-10.0, -4.0] |

## crash:panic->stabilisation (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.658 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.756 | +0.0980 | +0.0015 | **NO** | -1 [-6.0, 4.25] |
| SMA20 | 0.710 | +0.0518 | -0.0002 | **NO** | -3 [-7.0, 2.0] |
| MACD | 0.708 | +0.0505 | -0.0079 | **NO** | -4 [-7.0, -1.0] |
| MACD_signal | 0.703 | +0.0452 | -0.0038 | **NO** | -4 [-7.0, 0.0] |
| dividend_yield | 0.632 | -0.0259 | -0.0081 | yes | -4 [-7.0, -1.0] |
| reported_PE | 0.630 | -0.0281 | -0.0070 | yes | -4 [-7.0, -1.0] |
| trend_strength | 0.613 | -0.0452 | +0.0079 | yes | -1 [-6.0, 5.25] |
| volume | 0.598 | -0.0593 | +0.0024 | yes | -3 [-7.0, 0.0] |
| volume_ratio | 0.551 | -0.1071 | +0.0094 | yes | -4 [-8.0, 0.0] |
| analyst_fair_value | 0.513 | -0.1445 | +0.0085 | yes | +0 [-5.0, 5.0] |
| sentiment_MA5 | 0.509 | -0.1483 | +0.0206 | yes | +0 [-7.0, 5.0] |
| sentiment_change | 0.504 | -0.1539 | +0.0185 | yes | +1 [-4.0, 6.0] |
| days_since_eps_announcement | 0.502 | -0.1561 | +0.0066 | yes | -10 [-10.0, -3.0] |
| implied_volatility | 0.499 | -0.1582 | +0.0122 | yes | -3 [-7.0, 2.0] |
| news_sentiment | 0.498 | -0.1601 | +0.0064 | yes | +2 [-4.0, 6.0] |
| trend_regime | 0.492 | -0.1655 | +0.0082 | yes | -10 [-10.0, -7.0] |
| RSI14 | 0.439 | -0.2184 | +0.0000 | yes | -3 [-6.0, 1.0] |

## bull_trap:calm->mania (n = 200 paths; 1400 positive / 31954 negative days; reference AUC 0.500 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.504 | +0.0041 | +0.0059 | yes | +0 [-5.0, 5.0] |
| trend_regime | 0.501 | +0.0016 | +0.0017 | yes | -7 [-10.0, -1.0] |
| implied_volatility | 0.500 | +0.0003 | +0.0060 | yes | +0 [-6.0, 5.0] |
| RSI14 | 0.500 | +0.0000 | +0.0000 | yes | +0 [-5.0, 4.0] |
| news_sentiment | 0.498 | -0.0019 | +0.0021 | yes | +0 [-4.0, 5.0] |
| days_since_eps_announcement | 0.498 | -0.0021 | +0.0023 | yes | -10 [-10.0, -7.0] |
| sentiment_change | 0.485 | -0.0145 | +0.0160 | yes | +0 [-5.0, 5.0] |
| sentiment_MA5 | 0.485 | -0.0149 | +0.0194 | yes | -0 [-6.0, 5.0] |
| MACD | 0.485 | -0.0149 | +0.0079 | yes | +0 [-5.0, 4.0] |
| reported_PE | 0.479 | -0.0207 | +0.0013 | yes | +1 [-4.25, 5.0] |
| dividend_yield | 0.479 | -0.0212 | +0.0010 | yes | +1 [-4.0, 5.0] |
| volume | 0.476 | -0.0241 | +0.0074 | yes | -1 [-6.0, 5.0] |
| trend_strength | 0.471 | -0.0290 | +0.0204 | yes | +0 [-6.25, 6.0] |
| MACD_signal | 0.470 | -0.0294 | +0.0155 | yes | +0 [-6.0, 5.0] |
| volume_ratio | 0.468 | -0.0320 | +0.0109 | yes | +1 [-4.0, 6.0] |
| SMA20 | 0.437 | -0.0632 | +0.0255 | yes | -0 [-7.0, 6.0] |
| SMA50 | 0.401 | -0.0993 | +0.0280 | yes | +1 [-6.0, 7.0] |

## bull_trap:mania->blow-off (n = 200 paths; 1400 positive / 31954 negative days; reference AUC 0.537 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.582 | +0.0450 | +0.0146 | **NO** | +3 [-5.0, 8.0] |
| SMA20 | 0.577 | +0.0406 | +0.0161 | **NO** | +1 [-6.0, 7.0] |
| volume_ratio | 0.526 | -0.0107 | +0.0072 | yes | +2 [-4.25, 7.0] |
| dividend_yield | 0.524 | -0.0132 | -0.0001 | yes | +2 [-4.0, 7.0] |
| reported_PE | 0.523 | -0.0134 | +0.0001 | yes | +1 [-4.25, 7.0] |
| trend_strength | 0.516 | -0.0206 | +0.0146 | yes | -0 [-7.0, 6.0] |
| analyst_fair_value | 0.512 | -0.0247 | +0.0071 | yes | +0 [-5.25, 6.0] |
| RSI14 | 0.510 | -0.0268 | +0.0000 | yes | +1 [-4.0, 6.0] |
| volume | 0.508 | -0.0285 | +0.0078 | yes | -1 [-6.0, 5.0] |
| news_sentiment | 0.502 | -0.0351 | +0.0036 | yes | -2 [-6.0, 5.0] |
| implied_volatility | 0.500 | -0.0366 | +0.0090 | yes | +1 [-4.0, 6.0] |
| days_since_eps_announcement | 0.500 | -0.0367 | +0.0033 | yes | -10 [-10.0, -6.5] |
| trend_regime | 0.499 | -0.0379 | +0.0048 | yes | -10 [-10.0, -3.0] |
| MACD_signal | 0.496 | -0.0412 | +0.0151 | yes | +2 [-5.0, 6.0] |
| sentiment_change | 0.491 | -0.0461 | +0.0154 | yes | -2 [-6.25, 5.0] |
| MACD | 0.487 | -0.0497 | +0.0107 | yes | +1 [-5.0, 7.25] |
| sentiment_MA5 | 0.487 | -0.0501 | +0.0164 | yes | -3 [-8.0, 4.0] |

## bull_trap:blow-off->post-top (n = 25 paths; 171 positive / 31954 negative days; reference AUC 0.571 = ref_dlogPSMA20)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.682 | +0.1115 | +0.0902 | **NO** | -7 [-9.0, -2.0] |
| SMA20 | 0.612 | +0.0409 | +0.0776 | yes | -2 [-8.0, 0.0] |
| reported_PE | 0.553 | -0.0183 | -0.0028 | yes | -4 [-7.0, -2.0] |
| dividend_yield | 0.548 | -0.0230 | -0.0034 | yes | -4 [-6.0, -1.0] |
| implied_volatility | 0.545 | -0.0257 | +0.0268 | yes | +2 [-7.0, 6.0] |
| RSI14 | 0.534 | -0.0372 | +0.0000 | yes | -1 [-4.0, 2.0] |
| MACD_signal | 0.527 | -0.0435 | +0.0612 | yes | +2 [-2.0, 9.0] |
| trend_strength | 0.512 | -0.0592 | +0.0777 | yes | -1 [-7.0, 8.0] |
| analyst_fair_value | 0.509 | -0.0617 | +0.0239 | yes | +4 [-5.0, 7.0] |
| volume | 0.507 | -0.0641 | +0.0223 | yes | +0 [-4.0, 5.0] |
| news_sentiment | 0.501 | -0.0699 | +0.0224 | yes | +0 [-5.0, 5.0] |
| trend_regime | 0.493 | -0.0781 | +0.0222 | yes | -10 [-10.0, -5.0] |
| volume_ratio | 0.492 | -0.0785 | +0.0175 | yes | -5 [-8.0, 0.0] |
| days_since_eps_announcement | 0.492 | -0.0789 | +0.0202 | yes | -10 [-10.0, -10.0] |
| sentiment_MA5 | 0.491 | -0.0800 | +0.0525 | yes | -1 [-8.0, 5.0] |
| sentiment_change | 0.488 | -0.0832 | +0.0469 | yes | +0 [-5.0, 5.0] |
| MACD | 0.487 | -0.0838 | +0.0345 | yes | +3 [-4.0, 8.0] |

**Verdict (as registered):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value'), ('crash:deterioration->panic', 'MACD'), ('crash:panic->stabilisation', 'MACD'), ('crash:panic->stabilisation', 'MACD_signal'), ('crash:panic->stabilisation', 'SMA20'), ('crash:panic->stabilisation', 'SMA50'), ('bull_trap:mania->blow-off', 'SMA20'), ('bull_trap:mania->blow-off', 'SMA50'), ('bull_trap:blow-off->post-top', 'SMA50')].

**Verdict (non-price fields, ADDENDUM 1.3):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value')].

