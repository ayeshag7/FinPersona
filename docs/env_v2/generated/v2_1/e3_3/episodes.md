# E3.3 phase variance multipliers and rise/decay from panel event windows (PREREG_PHASE_3.md section 5)

set A (417), Adj Close ffilled, 2000-2024; windows per PREREG 5.1; medians over episodes with 1000-resample stock-bootstrap 95 % CIs (n = episodes/stocks). Multipliers are RV(window)/RV(pre-event calm) per episode - TOTAL-return variance ratios (the x-innovation mapping is PREREG 5.3). set A has no delistings (REG-15): depths and multipliers understate the full universe's crashes; the delisted tail is 4.7 % recoverable (E1.0).

| statistic | vs UNCONDITIONAL ref (ADDENDUM 1, adopted) | vs pre-event window (as first registered) |
|---|---|---|
| drawdown depth | -0.45 [-0.46, -0.44] (IQR -0.61--0.36; n=1789/417) | (same) |
| m_deterioration | 1.37 [1.31, 1.44] (IQR 0.80-2.67; n=1592/412) | 1.16 [1.13, 1.22] (IQR 0.77-1.99; n=1592/412) |
| m_panic | 7.45 [6.86, 8.13] (IQR 3.17-17.38; n=1592/412) | 5.43 [4.95, 5.89] (IQR 2.47-17.00; n=1592/412) |
| m_stabilisation | 3.11 [2.96, 3.34] (IQR 1.60-6.22; n=1571/412) | 2.39 [2.24, 2.54] (IQR 1.20-6.12; n=1571/412) |
| m_mania | 1.18 [1.12, 1.21] (IQR 0.69-2.32; n=3125/394) | 0.46 [0.44, 0.48] (IQR 0.24-0.93; n=3125/394) |
| m_blow-off | 1.65 [1.58, 1.71] (IQR 0.96-3.41; n=3125/394) | 0.70 [0.66, 0.73] (IQR 0.31-1.41; n=3125/394) |
| m_post-top | 1.16 [1.13, 1.20] (IQR 0.77-1.88; n=3122/394) | 0.42 [0.40, 0.45] (IQR 0.23-0.81; n=3122/394) |
| pre-event calm / unconditional (dd) | 1.01 [0.98, 1.06] (IQR 0.68-1.81; n=1592/412) | |
| pre-event calm / unconditional (ru) | 2.74 [2.57, 2.89] (IQR 1.35-6.10; n=3125/394) | |
| rise time (onset -> RV21 peak, d) | 118.0 [107.0, 131.0] (IQR 39.0-316.0; n=1585/412) | (reference-free) |
| decay half-life (d) | 11.0 [11.0, 12.0] (IQR 7.0-17.0; n=1786/417) | 11.0 [10.0, 11.0] (IQR 7.0-16.0; n=1583/412) |
| censored share (decay) | 0.001 | |
| stress spell (d) | 64.0 [56.0, 72.0] (IQR 23.0-190.0; n=1585/412) | |
| RV21 peak / calm | 8.25 [7.64, 8.94] (IQR 3.86-24.55; n=1585/412) | |

Fast-crash subpopulation (ADDENDUM 2: span <= 126 d; n = 642/313): rise 30.0 [29.0, 35.0] (IQR 23.0-64.5; n=531/276); decay 9.0 [9.0, 10.0] (IQR 7.0-13.0; n=531/276); stress spell 33.0 [27.0, 48.0] (IQR 22.0-112.0; n=531/276); depth -0.37 [-0.38, -0.36] (IQR -0.45--0.33; n=642/313).

Market-wide windows (per-stock RV ratio to own 120-d pre-window calm):

| window | m | peak-21d m |
|---|---|---|
| 2008Q4 | 4.58 [4.41, 4.76] (IQR 3.35-6.11; n=417/417) | 7.31 [7.02, 7.71] (IQR 5.32-10.40; n=417/417) |
| 2011Q3 | 3.52 [3.34, 3.62] (IQR 2.67-4.48; n=417/417) | 6.56 [6.30, 6.91] (IQR 4.98-8.65; n=417/417) |
| 2018Q4 | 2.26 [2.19, 2.39] (IQR 1.81-3.08; n=417/417) | 3.48 [3.27, 3.71] (IQR 2.60-4.72; n=417/417) |
| 2020Q1 | 9.20 [8.35, 9.97] (IQR 5.99-14.66; n=417/417) | 24.74 [22.32, 26.40] (IQR 15.12-39.95; n=417/417) |
| 2022H1 | 1.95 [1.85, 2.03] (IQR 1.52-2.47; n=417/417) | 3.69 [3.50, 3.81] (IQR 2.76-4.78; n=417/417) |

Literature beside (not tolerances): Ang & Timmermann 2012 (monthly S&P, read by the plan's pass): sigma 4.89 % vs 2.45 % -> variance ratio ~ 4.0; Ang & Bekaert 2002 (monthly): 7.04 % vs 3.77 %; Schwert 1989 (JF; index, monthly): recession/expansion volatility +76 % (1859-1986) to +227 % (1927-86); GSY 2019 (JFE; industry, monthly): 40 run-ups >= 100 %, 21 crashed; volatility rises in run-ups that crash; plan's two index examples (not a sample): onset->peak-RV 2020 ~ 10 trading days, 2008 ~ 30.
