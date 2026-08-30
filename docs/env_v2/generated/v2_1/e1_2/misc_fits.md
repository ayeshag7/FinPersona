# Phase 1 FIT values without simulation (PREREG_PHASE_1.md sections 4.5, 7)

## mu_V (Shiller nominal S&P price, price-only)

- Adopted (2000-01..2024-12): 0.000228/day [-0.000051, 0.000479] (block bootstrap over months, block 12), i.e. 5.7 %/yr; n = 300 months.
- Long run (1871-02..2024-12): 0.000186/day [0.000071, 0.000294], 4.7 %/yr; n = 1847.
- v2 value 0.00025/day (6.5 %/yr, stipulated). Literature beside: DMS 2025 (read by the third pass, LOG 4.1): US 1900-2024 nominal equity return 9.7 %/yr (total return, incl. dividends); v2 used mu_V = 0.00025/day (6.5 %/yr, 'plan').

## df_V (tails of standardised seasonal quarterly EPS changes, EDGAR sub-set)

- n = 25859 changes over 409 stocks; excess kurtosis 8.34 [7.64, 9.19].
- KS distance to N(0,1): 0.193 (bootstrap 95 % upper limit 0.201); to t5: 0.173 (upper 0.181).
- Rule: FIT gaussian if only the normal upper limit < 0.10; FIT t5 if only the t5 upper limit < 0.10; else DESIGN. **Verdict: DESIGN (both variants carried).**

## V_hat measurement noise (for the recovery study)

- median over 406 stocks of sd(log EPS_ttm,q / EPS_ttm,q-4) = 0.569 (IQR 0.342-0.860).

## Start-price range (E1.1 mechanisms A and C)

- P5 = 7.47 [6.27, 9.03], P95 = 240.02 [196.78, 290.39] of unadjusted Close over set A on 40 random dates (seed 20260829), 16680 observations; median 43.99. FIT.
