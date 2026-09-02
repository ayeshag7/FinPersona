# E2.6 checklist, sd_h30

engine ar1_hl30, sbar 0.00810, 100 seeds per scenario, T = 200, seeds from 130000.

| # | Property | Statistic | Pass criterion | Result | n |
|---|---|---|---|---|---|
| 1 | No linear autocorrelation of returns in calm phases (Cont 1) | LB Q(10) p>0.05 in 86%; median |ACF(1)| = 0.080 | >= 80% of seeds p>0.05; |ACF(1)| < 0.15 | PASS | 200 |
| 2 | Heavy tails (Cont 2, 7) | excess kurtosis > 1.5 in 64% (median 2.14); JB rejects in 85%; Hill median 3.60 | kurtosis > 1.5 in >= 80%; JB rejects; Hill 2.5-5 | FAIL | 920 |
| 3 | Volatility clustering (Cont 6) | LB|r| p<0.01 in 53%; LB r^2 in 47%; ARCH-LM(5) rejects in 37%; median ACF|r|(1) = 0.128 | p < 0.01 in >= 80%; ACF|r|(1) 0.1-0.4 | FAIL | 920 |
| 4 | Decay of ACF|r| (Cont 8) | median ACF|r| at lags 1: 0.120, 5: 0.071, 10: 0.045, 20: 0.031, 50: 0.003 | descriptive (T = 800 paths); not a pass criterion | n/a | 20 |
| 5 | GARCH persistence recoverable | median alpha+beta = 0.957 | median alpha + beta in [0.90, 0.995] | PASS | 920 |
| 6 | Leverage effect (Cont 9) | corr(r_t,|r_t+1|) < 0 in 63% (median -0.034); GJR gamma median 0.062 | negative in >= 70%; gamma > 0 | FAIL | 920 |
| 7 | Volume-volatility (Cont 10) | median Spearman corr(volume,|r|) = 0.266; median AC(1) log volume = 0.764; Shapiro p > 0.01 in 61% of seeds (median p = 0.050) | corr 0.2-0.5; AC(1) 0.5-0.8; log-normality not rejected (p > 0.01 in >= 50% of seeds) | PASS | 920 |
| 8 | Gain/loss asymmetry in crash (Cont 3) | median skew = -0.176; worst day larger than best in 66% | skew < 0; worst > best in >= 70% of crash seeds | FAIL | 300 |
| 9 | Mispricing persistence (FW regime) | 200-day calm windows: median ACF(1) of x = 0.9383, half-life = 11 d, sd(x) = 0.023; T=800 phase-free: ACF(1) = 0.9694, half-life = 22 d, sd(x) = 0.034 (criterion applied here) | ACF(1) >= 0.98; half-life >= 60 d; sd 0.08-0.20 | FAIL | 20 |
| 10 | Delta matters | event-window MDD: partial R2 of delta (controlling D_V) = 0.75, spread between delta 0.55 and 0.85 = 19.0 pp, means 0.55: -52.7%, 0.7: -42.5%, 0.85: -33.7%; whole-path MDD (reported): partial R2 0.70, spread 18.0 pp, means 0.55: -55.1%, 0.7: -45.4%, 0.85: -37.1% | partial R2 > 0.7; spread >= 20 pp between delta 0.55 and 0.85 (event-window MDD, amendment A7) | FAIL | 300 |
| 11 | Bubble shape and populations | mean 2nd difference of log P over mania > 0 in 57% (median 2.35e-05); topped share = 10%; median peak P/V in topped seeds = 1.58 | convex; 40-60% topped; peak P/V 1.6-2.5 in topped seeds | FAIL | 100 |
| 12 | Sentiment dynamics | median ACF(1) = 0.886; median corr(s_t, r_t) = 0.346; median calm corr(s_t-1, r_t) = 0.010 (configured b_pred = 0.0008) | ACF(1) 0.7-0.9; corr 0.25-0.55; lagged corr equals configured b_pred within CI | PASS | 920 |
| 13 | IV realism | mean IV calm 20.8%, panic 41.1%; median corr(IV, next-20d RV) = 0.38; IV-RV calm +7.8 pts, panic +19.5 pts; sd of calm IV across seeds 10.06 | calm 25-35%, panic 60-100%; corr 0.4-0.8; IV-RV +3..+8 calm, +10..+25 panic; non-degenerate across seeds | FAIL | 920 |
| 14 | Value leak | see evaluation.leakage_audit (L1-L3) | calm R2 <= 0.30; event R2 < 0.90 & MAPE >= 10%; no inversion | n/a | 0 |
| 15 | Phase/time separability | macro-phase accuracy from day alone = 61.5% (mixed set, 920 paths; within-scenario mean 74.2%); |corr(day, phase id)| = 0.09 | < 80% on the mixed set; < 0.9 | PASS | 920 |
| 16 | Composite phase clock | see evaluation.leakage_audit (L2b) | selectivity <= 10 pp | n/a | 0 |
| 17 | Conditioning | flat: rejection rate 0.0%; bull_trap: rejection rate 7.4%; crash: rejection rate 0.3%; sustained_bull: rejection rate 8.3%; mixed: rejection rate 1.3%; flat_T800: rejection rate 0.0%; bull-trap topped share 10% | rejection < 5% per scenario; joint conditioning published | FAIL | 920 |
| 18 | Start design applied | unit test (tests/) | C_0 as configured | n/a | 0 |
| 19 | Action-space reachability | unit test (tests/) | any allocation reachable; SELL feasible at t=1 | n/a | 0 |
| 20 | Magnitudes | median crash MDD = -45.9%; median calm daily sigma (flat) = 0.89%; median worst panic day = -4.3% | crash MDD -20..-65%; calm sigma 1.4-2.2%/day; worst day -6..-15% in panic | FAIL | 400 |

**Pass 5 / fail 10 / not applicable 5.**

Reference values (plan Section 9): S&P 500 daily excess kurtosis ~7-10; |r| ACF(1) ~0.2; TwinMarket SSE-50 kurtosis 7.26, leverage 0.14, GARCH alpha+beta 0.95; Hashimoto 18 JPX stocks kurtosis 7.85 +/- 1.07, |r| ACF(1) 0.19, |r|-volume correlation 0.46.
