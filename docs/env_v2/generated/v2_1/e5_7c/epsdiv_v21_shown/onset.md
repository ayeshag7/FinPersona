# E5.7(c) onset-detection audit -- epsdiv_v21_shown

200 crash + 200 bull-trap seeds, schedule pinned v21, overrides {"multiple": {"design": "v2"}, "eps": {"design": "v21", "s_eps": 0.17073819394108877, "p_loss": 0.09746485277956725, "p_loss_given_loss": 0.4250576479631053, "p_loss_given_profit": 0.061630302265943585, "loss_size_grid": [0.04459691252144083, 0.06924042899809937, 0.08834701007474836, 0.12090353539405778, 0.14814814814814817, 0.18299969805338792, 0.2189441670641594, 0.2536090783944356, 0.2894608737982232, 0.33597189847189846, 0.37943875620216977, 0.42247386759581895, 0.460662701784197, 0.5106382978723404, 0.5682499580677626, 0.6286467290100027, 0.6825107171822501, 0.7275096940973719, 0.7895435593592276, 0.873439276914329, 0.9680803951626641, 1.0455879655109153, 1.163365919433676, 1.2922483766233765, 1.4439136588818116, 1.5810314685314684, 1.802555623663867, 2.0452455543999384, 2.2974373469003204, 2.7238253207014242, 3.354086395969176, 4.180362302311435, 5.892215568862275], "pe_cap": 191.54973157246968, "lag_grid_td": [10.0, 11.0, 12.0, 12.0, 13.0, 14.0, 14.0, 15.0, 16.0, 16.0, 17.0, 17.0, 17.0, 18.0, 18.0, 19.0, 19.0, 19.0, 20.0, 20.0, 21.0, 21.0, 21.0, 22.0, 23.0, 23.0, 23.0, 24.0, 25.0, 26.0, 26.0, 28.0, 30.0], "lag_p10_p50_p90_td": [12.0, 19.0, 26.0], "nm_share_data": 0.08477005610385356}, "dividend": {"design": "v21", "field": "shown", "c_speed": 0.6971535189961907, "tau": 0.40631648936170217, "payer_share": 0.8872901678657075, "payout_median_data": 0.40631648936170217}, "analyst": {"design": "v2"}, "sentiment": {"design": "v2"}, "volume": {"design": "v2"}}; 500 circular-shift null draws. Rule: dAUC (field - best price-derived reference) <= null p95.

## crash:calm->deterioration (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.579 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.613 | +0.0338 | +0.0008 | **NO** | +2 [-3.0, 5.0] |
| RSI14 | 0.579 | +0.0000 | +0.0000 | yes | +1 [-3.0, 5.0] |
| volume_ratio | 0.544 | -0.0352 | +0.0054 | yes | +5 [1.0, 8.0] |
| implied_volatility | 0.536 | -0.0434 | +0.0072 | yes | +2 [-1.0, 6.0] |
| sentiment_MA5 | 0.507 | -0.0723 | +0.0187 | yes | +2 [-4.0, 5.0] |
| reported_PE | 0.503 | -0.0762 | +0.0032 | yes | +5 [2.0, 8.0] |
| trend_regime | 0.500 | -0.0791 | +0.0076 | yes | -7 [-10.0, 1.0] |
| days_since_eps_announcement | 0.500 | -0.0794 | +0.0059 | yes | -10 [-10.0, -1.75] |
| dividend_yield | 0.500 | -0.0795 | +0.0046 | yes | +4 [1.0, 8.0] |
| news_sentiment | 0.495 | -0.0842 | +0.0197 | yes | +0 [-6.0, 2.0] |
| MACD | 0.493 | -0.0869 | +0.0049 | yes | +7 [4.0, 9.0] |
| volume | 0.485 | -0.0944 | +0.0100 | yes | +3 [-2.0, 7.0] |
| sentiment_change | 0.479 | -0.1007 | +0.0205 | yes | +0 [-6.0, 2.0] |
| SMA20 | 0.440 | -0.1395 | +0.0172 | yes | +9 [3.75, 10.0] |
| MACD_signal | 0.433 | -0.1463 | +0.0129 | yes | +8 [6.0, 10.0] |
| SMA50 | 0.424 | -0.1551 | +0.0268 | yes | +8 [-1.0, 10.0] |
| trend_strength | 0.424 | -0.1555 | +0.0214 | yes | +6 [-1.0, 10.0] |

## crash:deterioration->panic (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.734 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| MACD | 0.740 | +0.0065 | +0.0005 | **NO** | +5 [1.0, 8.0] |
| SMA20 | 0.739 | +0.0055 | +0.0061 | yes | +7 [3.0, 9.0] |
| MACD_signal | 0.733 | -0.0003 | +0.0067 | yes | +5 [2.0, 8.0] |
| volume_ratio | 0.661 | -0.0731 | +0.0044 | yes | +5 [1.75, 8.0] |
| analyst_fair_value | 0.645 | -0.0883 | +0.0058 | yes | +0 [-4.0, 3.0] |
| reported_PE | 0.636 | -0.0975 | +0.0013 | yes | +5 [1.0, 8.0] |
| dividend_yield | 0.628 | -0.1056 | +0.0025 | yes | +5 [1.0, 7.0] |
| trend_strength | 0.628 | -0.1056 | +0.0179 | yes | +5 [1.0, 9.0] |
| SMA50 | 0.597 | -0.1362 | +0.0271 | yes | +7 [3.0, 10.0] |
| implied_volatility | 0.576 | -0.1577 | +0.0089 | yes | +2 [-2.0, 6.0] |
| volume | 0.550 | -0.1835 | +0.0095 | yes | +4 [1.0, 8.0] |
| RSI14 | 0.528 | -0.2056 | +0.0000 | yes | +3 [-2.0, 6.0] |
| trend_regime | 0.511 | -0.2222 | +0.0111 | yes | -7 [-10.0, -2.0] |
| days_since_eps_announcement | 0.503 | -0.2310 | +0.0111 | yes | -10 [-10.0, -4.0] |
| sentiment_MA5 | 0.404 | -0.3296 | +0.0296 | yes | +1 [-5.0, 7.0] |
| sentiment_change | 0.354 | -0.3796 | +0.0267 | yes | +4 [-5.0, 8.0] |
| news_sentiment | 0.313 | -0.4206 | +0.0303 | yes | +3 [-5.0, 7.0] |

## crash:panic->stabilisation (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.655 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.755 | +0.0997 | +0.0015 | **NO** | -0 [-5.0, 4.25] |
| SMA20 | 0.706 | +0.0508 | +0.0005 | **NO** | -3 [-7.0, 2.0] |
| MACD | 0.705 | +0.0504 | -0.0075 | **NO** | -4 [-7.0, -1.0] |
| MACD_signal | 0.700 | +0.0454 | -0.0046 | **NO** | -4 [-7.0, 0.0] |
| reported_PE | 0.627 | -0.0273 | -0.0063 | yes | -3 [-6.5, 0.0] |
| dividend_yield | 0.620 | -0.0344 | -0.0049 | yes | -3 [-6.0, 0.0] |
| trend_strength | 0.609 | -0.0462 | +0.0083 | yes | -1 [-6.0, 5.25] |
| volume | 0.597 | -0.0578 | +0.0021 | yes | -3 [-7.0, 0.0] |
| volume_ratio | 0.550 | -0.1051 | +0.0094 | yes | -4 [-8.0, 0.0] |
| analyst_fair_value | 0.513 | -0.1417 | +0.0085 | yes | +0 [-5.0, 5.0] |
| days_since_eps_announcement | 0.502 | -0.1526 | +0.0064 | yes | -10 [-10.0, -4.75] |
| implied_volatility | 0.499 | -0.1556 | +0.0121 | yes | -3 [-6.25, 2.0] |
| trend_regime | 0.491 | -0.1641 | +0.0078 | yes | -10 [-10.0, -7.0] |
| sentiment_MA5 | 0.472 | -0.1833 | +0.0180 | yes | +1 [-4.0, 6.0] |
| sentiment_change | 0.462 | -0.1932 | +0.0160 | yes | -1 [-6.0, 5.0] |
| RSI14 | 0.441 | -0.2138 | +0.0000 | yes | -3 [-6.25, 0.25] |
| news_sentiment | 0.436 | -0.2188 | +0.0192 | yes | +0 [-5.0, 6.0] |

## bull_trap:calm->mania (n = 200 paths; 1400 positive / 31935 negative days; reference AUC 0.501 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| sentiment_change | 0.525 | +0.0234 | +0.0100 | **NO** | -1 [-6.0, 4.25] |
| news_sentiment | 0.521 | +0.0200 | +0.0103 | **NO** | +0 [-5.25, 5.0] |
| sentiment_MA5 | 0.518 | +0.0165 | +0.0094 | **NO** | +1 [-6.0, 5.0] |
| analyst_fair_value | 0.502 | +0.0012 | +0.0052 | yes | -0 [-5.0, 4.0] |
| days_since_eps_announcement | 0.502 | +0.0006 | +0.0018 | yes | -10 [-10.0, -3.0] |
| RSI14 | 0.501 | +0.0000 | +0.0000 | yes | +0 [-5.0, 4.25] |
| implied_volatility | 0.501 | -0.0003 | +0.0075 | yes | +0 [-6.0, 5.0] |
| trend_regime | 0.501 | -0.0004 | +0.0021 | yes | -7 [-10.0, 0.0] |
| dividend_yield | 0.491 | -0.0102 | +0.0033 | yes | +1 [-4.0, 6.0] |
| MACD | 0.486 | -0.0151 | +0.0080 | yes | +0 [-5.0, 4.0] |
| reported_PE | 0.484 | -0.0178 | +0.0017 | yes | +1 [-4.25, 5.0] |
| volume | 0.477 | -0.0244 | +0.0073 | yes | -1 [-6.0, 5.0] |
| trend_strength | 0.472 | -0.0293 | +0.0199 | yes | +0 [-6.25, 6.0] |
| MACD_signal | 0.472 | -0.0295 | +0.0151 | yes | +0 [-7.0, 6.0] |
| volume_ratio | 0.469 | -0.0323 | +0.0098 | yes | +1 [-4.0, 5.25] |
| SMA20 | 0.441 | -0.0608 | +0.0249 | yes | +0 [-7.0, 6.0] |
| SMA50 | 0.402 | -0.0989 | +0.0296 | yes | +0 [-6.0, 6.25] |

## bull_trap:mania->blow-off (n = 200 paths; 1400 positive / 31935 negative days; reference AUC 0.536 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.578 | +0.0422 | +0.0155 | **NO** | +3 [-5.0, 9.0] |
| SMA20 | 0.575 | +0.0391 | +0.0176 | **NO** | +1 [-6.0, 8.0] |
| volume_ratio | 0.529 | -0.0074 | +0.0077 | yes | +2 [-4.0, 7.0] |
| dividend_yield | 0.528 | -0.0085 | +0.0009 | yes | +2 [-5.0, 7.0] |
| reported_PE | 0.520 | -0.0167 | +0.0016 | yes | +2 [-4.0, 7.0] |
| analyst_fair_value | 0.511 | -0.0249 | +0.0075 | yes | +0 [-5.0, 6.0] |
| volume | 0.511 | -0.0255 | +0.0079 | yes | -1 [-5.25, 5.0] |
| trend_strength | 0.509 | -0.0268 | +0.0161 | yes | -1 [-7.0, 6.0] |
| RSI14 | 0.509 | -0.0271 | +0.0000 | yes | +1 [-4.0, 5.25] |
| days_since_eps_announcement | 0.501 | -0.0351 | +0.0029 | yes | -10 [-10.0, -3.75] |
| implied_volatility | 0.500 | -0.0365 | +0.0091 | yes | +1 [-4.0, 6.0] |
| trend_regime | 0.498 | -0.0385 | +0.0052 | yes | -10 [-10.0, -3.0] |
| MACD_signal | 0.491 | -0.0451 | +0.0149 | yes | +2 [-5.0, 6.0] |
| MACD | 0.485 | -0.0516 | +0.0112 | yes | +1 [-5.25, 7.25] |
| news_sentiment | 0.462 | -0.0739 | +0.0179 | yes | +0 [-6.0, 6.0] |
| sentiment_change | 0.459 | -0.0771 | +0.0181 | yes | +1 [-6.0, 6.0] |
| sentiment_MA5 | 0.457 | -0.0794 | +0.0181 | yes | -1 [-6.25, 6.0] |

## bull_trap:blow-off->post-top (n = 26 paths; 178 positive / 31935 negative days; reference AUC 0.583 = ref_dlogPSMA20)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.664 | +0.0809 | +0.0821 | yes | -8 [-9.75, -2.5] |
| SMA20 | 0.621 | +0.0380 | +0.0776 | yes | -2 [-7.5, 0.0] |
| dividend_yield | 0.572 | -0.0106 | +0.0080 | yes | -2 [-5.25, 3.0] |
| reported_PE | 0.566 | -0.0167 | -0.0057 | yes | -4 [-6.0, 3.0] |
| implied_volatility | 0.550 | -0.0333 | +0.0258 | yes | +2 [-7.75, 6.0] |
| MACD_signal | 0.541 | -0.0423 | +0.0586 | yes | +3 [-3.75, 9.0] |
| RSI14 | 0.539 | -0.0441 | +0.0000 | yes | -2 [-5.75, 2.0] |
| trend_strength | 0.528 | -0.0550 | +0.0814 | yes | -1 [-6.5, 8.0] |
| volume | 0.514 | -0.0686 | +0.0204 | yes | +0 [-4.75, 2.75] |
| analyst_fair_value | 0.512 | -0.0711 | +0.0230 | yes | +4 [-5.0, 7.0] |
| volume_ratio | 0.503 | -0.0798 | +0.0173 | yes | -4 [-8.0, 0.75] |
| MACD | 0.501 | -0.0816 | +0.0368 | yes | +4 [-3.0, 8.0] |
| days_since_eps_announcement | 0.501 | -0.0823 | +0.0203 | yes | -10 [-10.0, -2.75] |
| trend_regime | 0.495 | -0.0879 | +0.0193 | yes | -10 [-10.0, -4.5] |
| news_sentiment | 0.389 | -0.1943 | +0.0396 | yes | +2 [-4.0, 7.75] |
| sentiment_MA5 | 0.376 | -0.2070 | +0.0497 | yes | +4 [-2.5, 6.0] |
| sentiment_change | 0.368 | -0.2150 | +0.0355 | yes | +4 [-4.75, 7.75] |

**Verdict (as registered):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value'), ('crash:deterioration->panic', 'MACD'), ('crash:panic->stabilisation', 'MACD'), ('crash:panic->stabilisation', 'MACD_signal'), ('crash:panic->stabilisation', 'SMA20'), ('crash:panic->stabilisation', 'SMA50'), ('bull_trap:calm->mania', 'news_sentiment'), ('bull_trap:calm->mania', 'sentiment_MA5'), ('bull_trap:calm->mania', 'sentiment_change'), ('bull_trap:mania->blow-off', 'SMA20'), ('bull_trap:mania->blow-off', 'SMA50')].

**Verdict (non-price fields, ADDENDUM 1.3):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value'), ('bull_trap:calm->mania', 'news_sentiment'), ('bull_trap:calm->mania', 'sentiment_MA5'), ('bull_trap:calm->mania', 'sentiment_change')].

