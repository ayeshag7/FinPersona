# Section 9 validation checklist, standard checklist panel (Phase 2 after)

Generator v2.1 after Phase 2; 200 seeds per scenario (crash: per delta), T = 200, seeds from 40000 (SCL, the standard checklist panel of PREREG_PHASE_1.md section 2, so the row is like-for-like with `e1_6_checklist_after`). Items 14 and 16 come from the leakage audit; 18 and 19 are unit tests.

| # | Property | Statistic | Pass criterion | Result | n |
|---|---|---|---|---|---|
| 1 | No linear autocorrelation of returns in calm phases (Cont 1) | LB Q(10) p>0.05 in 87%; median |ACF(1)| = 0.064 | >= 80% of seeds p>0.05; |ACF(1)| < 0.15 | PASS | 400 |
| 2 | Heavy tails (Cont 2, 7) | excess kurtosis > 1.5 in 62% (median 2.07); JB rejects in 84%; Hill median 3.69 | kurtosis > 1.5 in >= 80%; JB rejects; Hill 2.5-5 | FAIL | 1820 |
| 3 | Volatility clustering (Cont 6) | LB|r| p<0.01 in 52%; LB r^2 in 47%; ARCH-LM(5) rejects in 38%; median ACF|r|(1) = 0.120 | p < 0.01 in >= 80%; ACF|r|(1) 0.1-0.4 | FAIL | 1820 |
| 4 | Decay of ACF|r| (Cont 8) | median ACF|r| at lags 1: 0.076, 5: 0.065, 10: 0.059, 20: 0.055, 50: -0.013 | descriptive (T = 800 paths); not a pass criterion | n/a | 20 |
| 5 | GARCH persistence recoverable | median alpha+beta = 0.959 | median alpha + beta in [0.90, 0.995] | PASS | 1820 |
| 6 | Leverage effect (Cont 9) | corr(r_t,|r_t+1|) < 0 in 57% (median -0.013); GJR gamma median 0.054 | negative in >= 70%; gamma > 0 | FAIL | 1820 |
| 7 | Volume-volatility (Cont 10) | median Spearman corr(volume,|r|) = 0.416; median AC(1) log volume = 0.752; Shapiro p > 0.01 in 48% of seeds (median p = 0.008) | corr 0.2-0.5; AC(1) 0.5-0.8; log-normality not rejected (p > 0.01 in >= 50% of seeds) | FAIL | 1820 |
| 8 | Gain/loss asymmetry in crash (Cont 3) | median skew = 0.077; worst day larger than best in 48% | skew < 0; worst > best in >= 70% of crash seeds | FAIL | 600 |
| 9 | Mispricing persistence (FW regime) | 200-day calm windows: median ACF(1) of x = 0.8832, half-life = 6 d, sd(x) = 0.029; T=800 phase-free: ACF(1) = 0.9084, half-life = 7 d, sd(x) = 0.032 (criterion applied here) | ACF(1) >= 0.98; half-life >= 60 d; sd 0.08-0.20 | FAIL | 20 |
| 10 | Delta matters | event-window MDD: partial R2 of delta (controlling D_V) = 0.30, spread between delta 0.55 and 0.85 = 11.6 pp, means 0.55: -47.0%, 0.7: -40.2%, 0.85: -35.4%; whole-path MDD (reported): partial R2 0.25, spread 10.7 pp, means 0.55: -50.9%, 0.7: -44.6%, 0.85: -40.2% | partial R2 > 0.7; spread >= 20 pp between delta 0.55 and 0.85 (event-window MDD, amendment A7) | FAIL | 600 |
| 11 | Bubble shape and populations | mean 2nd difference of log P over mania > 0 in 47% (median -2.46e-05); topped share = 8%; median peak P/V in topped seeds = 1.42 | convex; 40-60% topped; peak P/V 1.6-2.5 in topped seeds | FAIL | 200 |
| 12 | Sentiment dynamics | median ACF(1) = 0.840; median corr(s_t, r_t) = 0.367; median calm corr(s_t-1, r_t) = -0.055 (configured b_pred = 0.0008) | ACF(1) 0.7-0.9; corr 0.25-0.55; lagged corr equals configured b_pred within CI | PASS | 1820 |
| 13 | IV realism | mean IV calm 42.9%, panic 87.5%; median corr(IV, next-20d RV) = 0.43; IV-RV calm +16.6 pts, panic +45.1 pts; sd of calm IV across seeds 23.57 | calm 25-35%, panic 60-100%; corr 0.4-0.8; IV-RV +3..+8 calm, +10..+25 panic; non-degenerate across seeds | FAIL | 1820 |
| 14 | Value leak | see evaluation.leakage_audit (L1-L3) | calm R2 <= 0.30; event R2 < 0.90 & MAPE >= 10%; no inversion | n/a | 0 |
| 15 | Phase/time separability | macro-phase accuracy from day alone = 59.1% (mixed set, 1820 paths; within-scenario mean 73.9%); |corr(day, phase id)| = 0.20 | < 80% on the mixed set; < 0.9 | PASS | 1820 |
| 16 | Composite phase clock | see evaluation.leakage_audit (L2b) | selectivity <= 10 pp | n/a | 0 |
| 17 | Conditioning | flat: rejection rate 0.0%; bull_trap: rejection rate 94.5%; crash: rejection rate 3.7%; sustained_bull: rejection rate 31.0%; mixed: rejection rate 84.7%; flat_T800: rejection rate 0.0%; bull-trap topped share 8% | rejection < 5% per scenario; joint conditioning published | FAIL | 1820 |
| 18 | Start design applied | unit test (tests/) | C_0 as configured | n/a | 0 |
| 19 | Action-space reachability | unit test (tests/) | any allocation reachable; SELL feasible at t=1 | n/a | 0 |
| 20 | Magnitudes | median crash MDD = -44.9%; median calm daily sigma (flat) = 1.77%; median worst panic day = -7.2% | crash MDD -20..-65%; calm sigma 1.4-2.2%/day; worst day -6..-15% in panic | PASS | 800 |

**Pass 5 / fail 10 / not applicable 5.**

Reference values (plan Section 9): S&P 500 daily excess kurtosis ~7-10; |r| ACF(1) ~0.2; TwinMarket SSE-50 kurtosis 7.26, leverage 0.14, GARCH alpha+beta 0.95; Hashimoto 18 JPX stocks kurtosis 7.85 +/- 1.07, |r| ACF(1) 0.19, |r|-volume correlation 0.46.
