# E1.4 panel side: announcement windows vs other days (PREREG_PHASE_1.md section 5.1)

Set A (415 names with EDGAR filings), residuals of the full-sample GJR-GARCH-t fits (E3.1), 2009-01-01 .. 2024-12-31; window = the 10 trading days ending on a 10-Q/10-K filing date; jump day = |z| > 4. Intervals: 1000-resample bootstrap over stocks.

| statistic | value | 95 % CI |
|---|---|---|
| window_share_of_days | 0.1452 | [0.1435, 0.1469] |
| q_share_of_jumps_in_window | 0.4345 | [0.4118, 0.4564] |
| enrichment | 2.9921 | [2.8328, 3.1449] |
| jump_rate_in_window | 0.0134 | [0.0124, 0.0143] |
| jump_rate_outside | 0.0030 | [0.0028, 0.0031] |
| rate_ratio | 4.5225 | [4.1102, 4.9476] |
| excess_kurtosis_in | 16.1595 | [14.2057, 18.2189] |
| excess_kurtosis_out | 14.9823 | [8.3421, 24.0881] |
| r_jump_in_mean | -0.0135 | [-0.0174, -0.0096] |
| r_jump_in_sd | 0.1098 | [0.1030, 0.1173] |
| r_jump_in_neg_share | 0.5616 | [0.5432, 0.5787] |
| r_jump_out_mean | -0.0187 | [-0.0224, -0.0151] |
| r_jump_out_sd | 0.1211 | [0.1151, 0.1281] |
| r_jump_out_neg_share | 0.6075 | [0.5905, 0.6247] |

n = 1,670,790 stock-days, 242,603 in windows; 7,492 jump days, 3,255 inside windows.

Literature beside (not tolerances): ABD 2007 (REStat; S&P 500 futures 1990-2002; read by the third pass, LOG 4.2): jump variation 14.4 % of realised variance; 27.9 % of days with a significant jump (index level); Boudoukh, Feldman, Kogan & Richardson 2019 (RFS; read): identified news explains 49.6 % of overnight idiosyncratic volatility (firm level).

Caveats: filing dates, not 8-K release dates: the window is 10 trading days ending on the 10-Q/10-K filing; set A survivors only (REG-15): crash-related jumps of delisted names are absent; EDGAR coverage starts 2009, so 2000-2008 residuals are not split.
