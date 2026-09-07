# E5.7(c) onset-detection audit -- final (Phase 5 hand-over)

200 crash + 200 bull-trap seeds, schedule pinned v21, overrides {}; 500 circular-shift null draws. Rule: dAUC (field - best price-derived reference) <= null p95.

## crash:calm->deterioration (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.578 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| RSI14 | 0.578 | +0.0000 | +0.0000 | yes | +1 [-4.0, 5.0] |
| volume_ratio | 0.537 | -0.0406 | +0.0074 | yes | +4 [-1.0, 8.0] |
| implied_volatility | 0.535 | -0.0432 | +0.0069 | yes | +2 [-0.25, 6.0] |
| volume | 0.509 | -0.0692 | +0.0100 | yes | +2 [-3.0, 6.0] |
| trend_regime | 0.502 | -0.0760 | +0.0066 | yes | -7 [-10.0, 1.0] |
| days_since_eps_announcement | 0.500 | -0.0779 | +0.0057 | yes | -10 [-10.0, -1.75] |
| reported_PE | 0.499 | -0.0786 | +0.0040 | yes | +4 [1.0, 7.0] |
| sentiment_change | 0.497 | -0.0813 | +0.0119 | yes | +0 [-6.0, 5.0] |
| news_sentiment | 0.497 | -0.0813 | +0.0125 | yes | +0 [-5.0, 5.0] |
| dividend_yield | 0.496 | -0.0825 | +0.0055 | yes | +4 [1.0, 8.0] |
| MACD | 0.493 | -0.0852 | +0.0047 | yes | +7 [4.0, 9.0] |
| sentiment_MA5 | 0.490 | -0.0885 | +0.0134 | yes | -1 [-6.0, 5.0] |
| analyst_fair_value | 0.446 | -0.1316 | +0.0180 | yes | -1 [-5.0, 5.25] |
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
| trend_strength | 0.631 | -0.1030 | +0.0172 | yes | +5 [1.0, 9.0] |
| reported_PE | 0.623 | -0.1108 | +0.0032 | yes | +5 [1.0, 8.0] |
| dividend_yield | 0.622 | -0.1116 | +0.0027 | yes | +4 [0.0, 7.0] |
| volume_ratio | 0.606 | -0.1274 | +0.0075 | yes | +3 [-1.0, 6.0] |
| SMA50 | 0.594 | -0.1399 | +0.0264 | yes | +7 [3.0, 10.0] |
| implied_volatility | 0.575 | -0.1587 | +0.0095 | yes | +2 [-2.0, 5.25] |
| volume | 0.541 | -0.1928 | +0.0120 | yes | +3 [-2.0, 7.0] |
| RSI14 | 0.530 | -0.2037 | +0.0000 | yes | +3 [-2.0, 6.0] |
| trend_regime | 0.513 | -0.2211 | +0.0109 | yes | -7 [-10.0, -2.0] |
| sentiment_change | 0.506 | -0.2276 | +0.0152 | yes | +0 [-5.0, 5.0] |
| news_sentiment | 0.505 | -0.2284 | +0.0157 | yes | +0 [-5.0, 6.0] |
| days_since_eps_announcement | 0.503 | -0.2312 | +0.0105 | yes | -10 [-10.0, -4.0] |
| sentiment_MA5 | 0.500 | -0.2339 | +0.0173 | yes | -1 [-5.25, 5.0] |
| analyst_fair_value | 0.486 | -0.2481 | +0.0209 | yes | +0 [-6.0, 4.0] |

## crash:panic->stabilisation (n = 200 paths; 1400 positive / 30467 negative days; reference AUC 0.659 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.758 | +0.0988 | +0.0008 | **NO** | -0 [-6.0, 5.0] |
| SMA20 | 0.711 | +0.0518 | -0.0002 | **NO** | -3 [-7.0, 2.0] |
| MACD | 0.709 | +0.0499 | -0.0077 | **NO** | -4 [-7.0, -1.0] |
| MACD_signal | 0.704 | +0.0453 | -0.0043 | **NO** | -4 [-7.0, 0.0] |
| dividend_yield | 0.622 | -0.0371 | -0.0043 | yes | -3 [-7.0, 0.0] |
| reported_PE | 0.620 | -0.0386 | -0.0039 | yes | -4 [-7.0, 0.0] |
| trend_strength | 0.614 | -0.0449 | +0.0079 | yes | -1 [-6.0, 5.25] |
| analyst_fair_value | 0.607 | -0.0524 | +0.0049 | yes | +0 [-5.0, 5.0] |
| volume | 0.521 | -0.1376 | +0.0093 | yes | -2 [-6.25, 3.0] |
| sentiment_change | 0.508 | -0.1504 | +0.0116 | yes | -1 [-6.0, 5.0] |
| news_sentiment | 0.508 | -0.1510 | +0.0121 | yes | -1 [-6.0, 6.0] |
| sentiment_MA5 | 0.505 | -0.1540 | +0.0125 | yes | -1 [-6.0, 4.0] |
| days_since_eps_announcement | 0.502 | -0.1566 | +0.0060 | yes | -10 [-10.0, -4.75] |
| implied_volatility | 0.499 | -0.1598 | +0.0118 | yes | -3 [-7.0, 2.0] |
| trend_regime | 0.492 | -0.1669 | +0.0076 | yes | -10 [-10.0, -6.75] |
| volume_ratio | 0.484 | -0.1752 | +0.0128 | yes | -3 [-8.0, 1.0] |
| RSI14 | 0.440 | -0.2188 | +0.0000 | yes | -3 [-7.0, 0.0] |

## bull_trap:calm->mania (n = 200 paths; 1400 positive / 31992 negative days; reference AUC 0.499 = ref_dRSI)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| trend_regime | 0.503 | +0.0032 | +0.0011 | **NO** | -7 [-10.0, -1.0] |
| implied_volatility | 0.502 | +0.0030 | +0.0069 | yes | +0 [-6.0, 5.0] |
| days_since_eps_announcement | 0.501 | +0.0020 | +0.0021 | yes | -10 [-10.0, -3.0] |
| RSI14 | 0.499 | +0.0000 | +0.0000 | yes | +0 [-4.25, 5.0] |
| news_sentiment | 0.496 | -0.0034 | +0.0074 | yes | +0 [-5.0, 5.0] |
| sentiment_change | 0.496 | -0.0034 | +0.0077 | yes | +0 [-5.25, 4.0] |
| sentiment_MA5 | 0.494 | -0.0051 | +0.0072 | yes | -1 [-6.0, 4.0] |
| MACD | 0.486 | -0.0133 | +0.0075 | yes | +0 [-5.0, 4.0] |
| dividend_yield | 0.486 | -0.0139 | +0.0025 | yes | +2 [-5.0, 6.0] |
| volume_ratio | 0.481 | -0.0181 | +0.0115 | yes | +1 [-5.0, 5.0] |
| reported_PE | 0.481 | -0.0189 | +0.0026 | yes | +1 [-5.0, 5.0] |
| volume | 0.479 | -0.0208 | +0.0100 | yes | -1 [-6.0, 4.0] |
| trend_strength | 0.474 | -0.0259 | +0.0194 | yes | +0 [-6.25, 6.0] |
| MACD_signal | 0.473 | -0.0267 | +0.0156 | yes | +0 [-6.0, 5.25] |
| analyst_fair_value | 0.438 | -0.0610 | +0.0156 | yes | +0 [-6.0, 5.0] |
| SMA20 | 0.438 | -0.0619 | +0.0235 | yes | +0 [-6.0, 6.0] |
| SMA50 | 0.397 | -0.1024 | +0.0283 | yes | +0 [-6.0, 6.0] |

## bull_trap:mania->blow-off (n = 200 paths; 1400 positive / 31992 negative days; reference AUC 0.535 = ref_abs_ret5)

| field | AUC | dAUC vs reference | null p95 | pass | timing error median [IQR] |
|---|---|---|---|---|---|
| SMA50 | 0.578 | +0.0421 | +0.0168 | **NO** | +3 [-5.0, 8.0] |
| SMA20 | 0.577 | +0.0419 | +0.0151 | **NO** | +1 [-6.0, 7.0] |
| dividend_yield | 0.532 | -0.0038 | +0.0028 | yes | +2 [-4.0, 7.0] |
| reported_PE | 0.524 | -0.0110 | +0.0022 | yes | +1 [-5.0, 7.0] |
| analyst_fair_value | 0.517 | -0.0186 | +0.0106 | yes | +0 [-6.0, 5.0] |
| volume_ratio | 0.513 | -0.0222 | +0.0089 | yes | +1 [-5.0, 6.0] |
| trend_strength | 0.513 | -0.0229 | +0.0160 | yes | -1 [-7.0, 6.0] |
| RSI14 | 0.510 | -0.0251 | +0.0000 | yes | +1 [-5.0, 5.0] |
| volume | 0.510 | -0.0254 | +0.0096 | yes | -1 [-6.0, 5.0] |
| implied_volatility | 0.501 | -0.0340 | +0.0097 | yes | +1 [-4.0, 5.25] |
| days_since_eps_announcement | 0.501 | -0.0343 | +0.0029 | yes | -10 [-10.0, -3.75] |
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
| analyst_fair_value | 0.623 | +0.0455 | +0.0353 | **NO** | -1 [-5.5, 6.0] |
| SMA20 | 0.598 | +0.0205 | +0.0835 | yes | -2 [-7.0, 0.0] |
| implied_volatility | 0.551 | -0.0268 | +0.0231 | yes | +2 [-7.5, 5.5] |
| MACD_signal | 0.548 | -0.0295 | +0.0586 | yes | +1 [-5.5, 8.5] |
| reported_PE | 0.545 | -0.0324 | +0.0073 | yes | -4 [-5.0, 3.0] |
| RSI14 | 0.536 | -0.0412 | +0.0000 | yes | -2 [-5.5, 1.0] |
| trend_strength | 0.525 | -0.0524 | +0.0796 | yes | -1 [-5.5, 8.0] |
| dividend_yield | 0.524 | -0.0531 | +0.0065 | yes | -3 [-5.0, 3.0] |
| sentiment_change | 0.513 | -0.0647 | +0.0356 | yes | +1 [-3.5, 5.0] |
| news_sentiment | 0.509 | -0.0682 | +0.0334 | yes | +1 [-1.5, 5.0] |
| MACD | 0.499 | -0.0781 | +0.0343 | yes | +3 [-3.5, 8.0] |
| days_since_eps_announcement | 0.495 | -0.0821 | +0.0223 | yes | -10 [-10.0, -8.0] |
| trend_regime | 0.494 | -0.0835 | +0.0197 | yes | -10 [-10.0, -4.5] |
| volume | 0.492 | -0.0855 | +0.0281 | yes | -3 [-6.5, 1.0] |
| sentiment_MA5 | 0.488 | -0.0890 | +0.0375 | yes | -2 [-5.5, 2.0] |
| volume_ratio | 0.459 | -0.1185 | +0.0299 | yes | -5 [-8.5, 0.5] |

**Verdict (as registered):** FAILURES: [('crash:deterioration->panic', 'MACD'), ('crash:panic->stabilisation', 'MACD'), ('crash:panic->stabilisation', 'MACD_signal'), ('crash:panic->stabilisation', 'SMA20'), ('crash:panic->stabilisation', 'SMA50'), ('bull_trap:calm->mania', 'trend_regime'), ('bull_trap:mania->blow-off', 'SMA20'), ('bull_trap:mania->blow-off', 'SMA50'), ('bull_trap:blow-off->post-top', 'analyst_fair_value')].

**Verdict (non-price fields, ADDENDUM 1.3):** every non-price field passes at every transition.

