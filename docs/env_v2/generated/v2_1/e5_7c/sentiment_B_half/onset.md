# E5.7(c) onset-detection audit -- sentiment_B_half

200 crash + 200 bull-trap seeds, schedule pinned v21, overrides {"multiple": {"design": "v2"}, "eps": {"design": "v2"}, "dividend": {"design": "v2"}, "analyst": {"design": "v2"}, "sentiment": {"design": "B", "rho": 0.21127624401947614, "b0": 0.011336005215507806, "b1": 0.11097693054019067, "sd_e": 0.971818924981291, "s_raw": 0.3970515881879271, "c_val": 0.47496604504765394, "c_val_full": 0.9499320900953079, "link_size": "half", "rho_w": 0.5339356961700638, "b0_w": 0.2980105377069622, "b1_w": 0.19940872764652662, "sd_e_w": 0.7593161575955316, "update_days": 5, "full_sample_fit": {"rho": 0.4026031062150719, "b0_per_sd_raw": 0.011751427478029973, "b1_per_sd_raw": 0.08442584293369898, "sd_resid_per_sd_raw": 0.9103032882304359}}, "volume": {"design": "v2"}}; 500 circular-shift null draws. Rule: dAUC (field - best price-derived reference) <= null p95.

## crash:calm->deterioration (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.578 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.613 | +0.0348 | +0.0010 | **NO** | +2 [-3.0, 5.0] |
| RSI14 | 0.578 | +0.0000 | +0.0000 | yes | +1 [-4.0, 5.0] |
| volume_ratio | 0.545 | -0.0331 | +0.0053 | yes | +5 [0.0, 8.0] |
| implied_volatility | 0.535 | -0.0434 | +0.0068 | yes | +2 [-0.25, 6.0] |
| trend_regime | 0.502 | -0.0763 | +0.0066 | yes | -7 [-10.0, 1.0] |
| reported_PE | 0.501 | -0.0770 | +0.0009 | yes | +5 [2.0, 8.0] |
| dividend_yield | 0.501 | -0.0773 | +0.0006 | yes | +4 [1.0, 8.0] |
| days_since_eps_announcement | 0.499 | -0.0788 | +0.0067 | yes | -10 [-10.0, -5.0] |
| news_sentiment | 0.497 | -0.0815 | +0.0124 | yes | +0 [-5.0, 5.25] |
| sentiment_change | 0.496 | -0.0818 | +0.0120 | yes | +0 [-6.0, 5.25] |
| MACD | 0.493 | -0.0855 | +0.0047 | yes | +7 [4.0, 9.0] |
| sentiment_MA5 | 0.490 | -0.0885 | +0.0126 | yes | -1 [-6.0, 5.0] |
| volume | 0.485 | -0.0935 | +0.0099 | yes | +3 [-1.25, 7.0] |
| SMA20 | 0.438 | -0.1403 | +0.0173 | yes | +9 [4.0, 10.0] |
| MACD_signal | 0.432 | -0.1464 | +0.0134 | yes | +8 [6.0, 10.0] |
| SMA50 | 0.423 | -0.1550 | +0.0269 | yes | +8 [-1.0, 10.0] |
| trend_strength | 0.421 | -0.1574 | +0.0221 | yes | +7 [-0.25, 10.0] |

## crash:deterioration->panic (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.734 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| MACD | 0.741 | +0.0074 | +0.0001 | **NO** | +5 [2.0, 8.0] |
| SMA20 | 0.739 | +0.0050 | +0.0062 | yes | +7 [3.0, 9.0] |
| MACD_signal | 0.734 | +0.0006 | +0.0067 | yes | +5 [2.0, 8.25] |
| volume_ratio | 0.658 | -0.0754 | +0.0043 | yes | +5 [2.0, 8.0] |
| analyst_fair_value | 0.646 | -0.0880 | +0.0054 | yes | +0 [-4.0, 3.0] |
| reported_PE | 0.632 | -0.1018 | -0.0003 | yes | +5 [3.0, 8.0] |
| dividend_yield | 0.631 | -0.1028 | -0.0004 | yes | +5 [2.75, 8.0] |
| trend_strength | 0.631 | -0.1031 | +0.0173 | yes | +5 [1.0, 9.0] |
| SMA50 | 0.594 | -0.1394 | +0.0266 | yes | +7 [3.0, 10.0] |
| implied_volatility | 0.575 | -0.1586 | +0.0095 | yes | +2 [-2.0, 5.25] |
| volume | 0.549 | -0.1848 | +0.0103 | yes | +4 [1.0, 8.0] |
| RSI14 | 0.530 | -0.2037 | +0.0000 | yes | +3 [-2.0, 6.0] |
| trend_regime | 0.513 | -0.2211 | +0.0107 | yes | -7 [-10.0, -2.0] |
| sentiment_change | 0.506 | -0.2273 | +0.0156 | yes | +0 [-5.0, 6.0] |
| news_sentiment | 0.506 | -0.2281 | +0.0154 | yes | -1 [-5.0, 6.0] |
| days_since_eps_announcement | 0.501 | -0.2329 | +0.0110 | yes | -10 [-10.0, -4.0] |
| sentiment_MA5 | 0.500 | -0.2340 | +0.0177 | yes | -1 [-5.0, 5.0] |

## crash:panic->stabilisation (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.659 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.758 | +0.0991 | +0.0007 | **NO** | -1 [-6.0, 5.0] |
| SMA20 | 0.711 | +0.0520 | -0.0007 | **NO** | -3 [-7.0, 2.0] |
| MACD | 0.709 | +0.0498 | -0.0076 | **NO** | -4 [-7.0, -1.0] |
| MACD_signal | 0.704 | +0.0453 | -0.0043 | **NO** | -4 [-7.0, 0.0] |
| dividend_yield | 0.631 | -0.0277 | -0.0081 | yes | -4 [-7.0, -1.0] |
| reported_PE | 0.631 | -0.0284 | -0.0074 | yes | -4 [-7.0, -0.75] |
| trend_strength | 0.614 | -0.0449 | +0.0082 | yes | -1 [-6.0, 5.25] |
| volume | 0.598 | -0.0610 | +0.0025 | yes | -3 [-7.0, 0.0] |
| volume_ratio | 0.550 | -0.1084 | +0.0089 | yes | -4 [-8.0, 0.0] |
| analyst_fair_value | 0.513 | -0.1457 | +0.0088 | yes | +0 [-5.0, 5.0] |
| sentiment_change | 0.508 | -0.1514 | +0.0114 | yes | -1 [-6.0, 5.0] |
| news_sentiment | 0.507 | -0.1521 | +0.0122 | yes | -1 [-6.0, 5.0] |
| sentiment_MA5 | 0.504 | -0.1553 | +0.0127 | yes | -2 [-7.0, 4.0] |
| days_since_eps_announcement | 0.502 | -0.1573 | +0.0066 | yes | -10 [-10.0, -3.0] |
| implied_volatility | 0.499 | -0.1596 | +0.0119 | yes | -3 [-7.0, 2.0] |
| trend_regime | 0.492 | -0.1669 | +0.0075 | yes | -10 [-10.0, -6.75] |
| RSI14 | 0.440 | -0.2192 | +0.0000 | yes | -3 [-7.0, 0.0] |

## bull_trap:calm->mania (n = 200 paths; 1400 positive / 31973 negative days; reference AUC 0.500 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| analyst_fair_value | 0.505 | +0.0054 | +0.0054 | yes | +0 [-5.0, 4.25] |
| trend_regime | 0.503 | +0.0035 | +0.0011 | **NO** | -7 [-10.0, -1.0] |
| implied_volatility | 0.502 | +0.0030 | +0.0065 | yes | +0 [-6.0, 5.0] |
| RSI14 | 0.500 | +0.0000 | +0.0000 | yes | +0 [-5.0, 5.0] |
| days_since_eps_announcement | 0.498 | -0.0018 | +0.0022 | yes | -10 [-10.0, -7.0] |
| sentiment_change | 0.497 | -0.0029 | +0.0074 | yes | +0 [-5.0, 4.0] |
| news_sentiment | 0.497 | -0.0030 | +0.0071 | yes | +0 [-5.0, 5.0] |
| sentiment_MA5 | 0.495 | -0.0040 | +0.0074 | yes | -1 [-6.0, 5.0] |
| MACD | 0.486 | -0.0131 | +0.0075 | yes | +0 [-5.0, 4.0] |
| reported_PE | 0.482 | -0.0174 | +0.0008 | yes | +0 [-4.0, 5.0] |
| dividend_yield | 0.478 | -0.0218 | +0.0011 | yes | +1 [-4.0, 5.0] |
| volume | 0.474 | -0.0256 | +0.0082 | yes | -1 [-6.0, 5.0] |
| trend_strength | 0.474 | -0.0258 | +0.0195 | yes | +0 [-6.25, 6.0] |
| MACD_signal | 0.473 | -0.0266 | +0.0158 | yes | +0 [-6.0, 5.0] |
| volume_ratio | 0.465 | -0.0349 | +0.0104 | yes | +1 [-4.0, 6.0] |
| SMA20 | 0.437 | -0.0623 | +0.0238 | yes | -0 [-6.0, 6.0] |
| SMA50 | 0.397 | -0.1026 | +0.0278 | yes | +0 [-6.0, 6.0] |

## bull_trap:mania->blow-off (n = 200 paths; 1400 positive / 31973 negative days; reference AUC 0.536 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.578 | +0.0420 | +0.0165 | **NO** | +4 [-5.0, 9.0] |
| SMA20 | 0.577 | +0.0417 | +0.0155 | **NO** | +1 [-6.0, 7.0] |
| volume_ratio | 0.529 | -0.0067 | +0.0073 | yes | +2 [-4.0, 7.0] |
| dividend_yield | 0.523 | -0.0125 | -0.0000 | yes | +1 [-5.0, 7.0] |
| reported_PE | 0.523 | -0.0126 | +0.0002 | yes | +1 [-5.0, 6.0] |
| trend_strength | 0.513 | -0.0226 | +0.0159 | yes | -1 [-7.0, 6.0] |
| analyst_fair_value | 0.511 | -0.0250 | +0.0070 | yes | +0 [-6.0, 6.0] |
| RSI14 | 0.510 | -0.0251 | +0.0000 | yes | +1 [-5.0, 5.0] |
| volume | 0.510 | -0.0255 | +0.0082 | yes | -1 [-6.0, 5.0] |
| implied_volatility | 0.502 | -0.0339 | +0.0098 | yes | +1 [-4.0, 5.25] |
| days_since_eps_announcement | 0.501 | -0.0350 | +0.0033 | yes | -10 [-10.0, -5.0] |
| news_sentiment | 0.499 | -0.0364 | +0.0098 | yes | +0 [-6.0, 6.0] |
| trend_regime | 0.499 | -0.0368 | +0.0051 | yes | -10 [-10.0, -3.75] |
| sentiment_MA5 | 0.495 | -0.0401 | +0.0084 | yes | -1 [-6.0, 4.0] |
| sentiment_change | 0.495 | -0.0401 | +0.0102 | yes | +0 [-5.0, 5.0] |
| MACD_signal | 0.494 | -0.0419 | +0.0143 | yes | +2 [-5.0, 6.0] |
| MACD | 0.488 | -0.0478 | +0.0103 | yes | +1 [-5.0, 8.0] |

## bull_trap:blow-off->post-top (n = 24 paths; 164 positive / 31973 negative days; reference AUC 0.586 = ref_dlogPSMA20)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.642 | +0.0562 | +0.0768 | yes | -8 [-10.0, -3.5] |
| SMA20 | 0.610 | +0.0248 | +0.0811 | yes | -2 [-6.5, 0.0] |
| MACD_signal | 0.563 | -0.0222 | +0.0580 | yes | +1 [-5.25, 8.25] |
| reported_PE | 0.562 | -0.0241 | -0.0028 | yes | -4 [-7.25, -2.0] |
| dividend_yield | 0.559 | -0.0264 | -0.0017 | yes | -4 [-7.25, -1.75] |
| implied_volatility | 0.555 | -0.0307 | +0.0236 | yes | +2 [-8.25, 5.25] |
| trend_strength | 0.544 | -0.0412 | +0.0780 | yes | +4 [-3.25, 10.0] |
| RSI14 | 0.539 | -0.0464 | +0.0000 | yes | -2 [-5.25, 1.0] |
| MACD | 0.518 | -0.0679 | +0.0351 | yes | +3 [-3.25, 8.0] |
| analyst_fair_value | 0.515 | -0.0709 | +0.0225 | yes | +4 [-5.0, 7.0] |
| volume | 0.513 | -0.0730 | +0.0217 | yes | -2 [-6.25, 2.25] |
| sentiment_change | 0.506 | -0.0800 | +0.0342 | yes | -0 [-5.0, 4.25] |
| news_sentiment | 0.500 | -0.0853 | +0.0308 | yes | +0 [-5.0, 5.25] |
| trend_regime | 0.497 | -0.0891 | +0.0206 | yes | -10 [-10.0, -3.5] |
| volume_ratio | 0.493 | -0.0923 | +0.0180 | yes | -5 [-8.25, 0.25] |
| days_since_eps_announcement | 0.492 | -0.0936 | +0.0168 | yes | -10 [-10.0, -9.5] |
| sentiment_MA5 | 0.486 | -0.0995 | +0.0387 | yes | -2 [-6.25, 1.5] |

**Verdict (as registered):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value'), ('crash:deterioration->panic', 'MACD'), ('crash:panic->stabilisation', 'MACD'), ('crash:panic->stabilisation', 'MACD_signal'), ('crash:panic->stabilisation', 'SMA20'), ('crash:panic->stabilisation', 'SMA50'), ('bull_trap:calm->mania', 'trend_regime'), ('bull_trap:mania->blow-off', 'SMA20'), ('bull_trap:mania->blow-off', 'SMA50')].

**Verdict (non-price fields, ADDENDUM 1.3):** FAILURES: [('crash:calm->deterioration', 'analyst_fair_value')].

