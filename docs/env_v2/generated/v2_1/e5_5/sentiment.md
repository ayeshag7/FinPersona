# E5.5 sentiment fits (PREREG_PHASE_5.md section 8.1)

SF Fed daily index, 17017 calendar days; published AC(1) 0.9967 (AC(21) 0.907, AC(252) 0.451). Deconvolved with lam = 0.95 (FRBSF Economic Letter 2020-08 (read 6 Sep 2026): 'depreciation rate of 5%'; 18 calendar gaps treated as consecutive): raw sd 0.338, AC(1) 0.3491 [0.2859454198179096, 0.40745851756667073], AC(2) 0.2985, AC(5) 0.2752, AC(21) 0.3017; **AR(1)+noise persistence rho = 0.8550 [0.7899056692428666, 0.8919627117636039]**, measurement-noise variance share 0.592 [0.5279303611286561, 0.6588578380736515].

Loadings on the standardised FF market return, AR form (n = 11589 trading days): rho 0.4026 (se 0.0152); b0 +0.0118 (se 0.0074) and b1 +0.0844 per sd of raw; residual sd 0.9103 sd; R2 0.172; corr(raw, mkt) +0.0059.

| sub-period | n | rho | b0 / sd | b1 / sd | resid sd / sd |
|---|---|---|---|---|---|
| 1980-99 | 4927 | 0.2498 | -0.0108 | +0.0688 | 0.9659 |
| 2000-07 | 2010 | 0.4624 | +0.0231 | +0.0910 | 0.8814 |
| 2008-12 | 1259 | 0.3613 | +0.0398 | +0.1803 | 0.9096 |
| 2013-19 | 1762 | 0.4480 | +0.0238 | +0.1030 | 0.8882 |
| 2020-26 | 1631 | 0.5266 | +0.0463 | +0.0733 | 0.8442 |

**200-trading-day WINDOW fits (like-for-like with the benchmark path; design A's parameters), n = 57 windows:** rho 0.2113 [0.1552108466290126, 0.2561215461691362] (P10-P90 0.050-0.436); b0 +0.0113 [-0.011789732498187896, 0.02854804011269813]; b1 +0.1110 [0.06163547920094077, 0.1315614145124275]; residual sd 0.9718 per sd of raw.
AAII 40-week window fits (design C's parameters), n = 50: rho_w 0.5339 [0.49333983895101713, 0.5782644053319608]; b0 +0.2980; b1 +0.1994; residual sd 0.7593 per sd.

Reverse (Tetlock's direction): next-day market return -0.64 bp per sd of raw sentiment (se 1.15, n = 11585); days 2-5 cumulative -2.12 bp (se 3.53). Tetlock 2007 (read): +8.1 bp next day, 6.8 bp reversed over days 2-5 (DJIA). b_pred stays LIT 0.0008 / 0.0006.

Valuation link (design B; monthly, raw on log-CAPE deviation from the trailing 120-month mean, n = 560 months): coefficient +0.2867 (se 0.0721) raw units per unit log-deviation = +0.9499 sd per unit [0.4817299549821392, 1.4181342252084765]; full-sample-mean deviation: +0.4821 sd per unit. DESIGN: a market-level coefficient on the log-CAPE deviation applied to a single stock's x = log(P/V).

AAII weekly (design C; n = 2010 weeks): rho_w 0.6939 (se 0.0169); loading on the standardised weekly return b0 +0.1878 per sd (se 0.0165), b1 +0.1139; residual sd 0.6604 sd; corr(spread, weekly return) +0.187.

Rule (i) references (200-trading-day windows, n = 57): ACF(1) median 0.2004 [0.15394875895264717, 0.2651782737128503] (P10-P90 0.047-0.430); corr(s, r) median +0.0058 [-0.02791579824513875, 0.01927226922835262]. AAII 40-week windows: ACF(1) 0.536 [0.4776465018344975, 0.5809316810316825], corr +0.241 [0.14187436792326386, 0.31097475522462026].

