# Section 9 validation checklist (v2)

Generator v2; 25 seeds per scenario (crash: per delta), T = 200; config overrides {'garch': {'panic_mult': 6.0}}; engine default. Items 14 and 16 are filled by `python -m evaluation.leakage_audit`; 18 and 19 are unit tests.

| # | Property | Statistic | Pass criterion | Result | n |
|---|---|---|---|---|---|
| 1 | No linear autocorrelation of returns in calm phases (Cont 1) | LB Q(10) p>0.05 in 90%; median |ACF(1)| = 0.080 | >= 80% of seeds p>0.05; |ACF(1)| < 0.15 | PASS | 50 |
| 2 | Heavy tails (Cont 2, 7) | excess kurtosis > 1.5 in 79% (median 3.29); JB rejects in 94%; Hill median 3.35 | kurtosis > 1.5 in >= 80%; JB rejects; Hill 2.5-5 | FAIL | 245 |
| 3 | Volatility clustering (Cont 6) | LB|r| p<0.01 in 64%; LB r^2 in 51%; ARCH-LM(5) rejects in 45%; median ACF|r|(1) = 0.168 | p < 0.01 in >= 80%; ACF|r|(1) 0.1-0.4 | FAIL | 245 |
| 4 | Decay of ACF|r| (Cont 8) | median ACF|r| at lags 1: 0.229, 5: 0.177, 10: 0.154, 20: 0.083, 50: 0.017 | descriptive (T = 800 paths); not a pass criterion | n/a | 20 |
| 5 | GARCH persistence recoverable | median alpha+beta = 0.970 | median alpha + beta in [0.90, 0.995] | PASS | 245 |
| 6 | Leverage effect (Cont 9) | corr(r_t,|r_t+1|) < 0 in 67% (median -0.043); GJR gamma median 0.035 | negative in >= 70%; gamma > 0 | FAIL | 245 |
| 7 | Volume-volatility (Cont 10) | median Spearman corr(volume,|r|) = 0.372; median AC(1) log volume = 0.815; Shapiro p > 0.01 in 47% of seeds (median p = 0.003) | corr 0.2-0.5; AC(1) 0.5-0.8; log-normality not rejected (p > 0.01 in >= 50% of seeds) | FAIL | 245 |
| 8 | Gain/loss asymmetry in crash (Cont 3) | median skew = -0.383; worst day larger than best in 69% | skew < 0; worst > best in >= 70% of crash seeds | FAIL | 75 |
| 9 | Mispricing persistence (FW regime) | 200-day calm windows: median ACF(1) of x = 0.9509, half-life = 14 d, sd(x) = 0.053; T=800 phase-free: ACF(1) = 0.9905, half-life = 72 d, sd(x) = 0.128 (criterion applied here) | ACF(1) >= 0.98; half-life >= 60 d; sd 0.08-0.20 | PASS | 20 |
| 10 | Delta matters | event-window MDD: partial R2 of delta (controlling D_V) = 0.31, spread between delta 0.55 and 0.85 = 17.3 pp, means 0.55: -53.9%, 0.7: -44.0%, 0.85: -36.6%; whole-path MDD (reported): partial R2 0.30, spread 16.0 pp, means 0.55: -57.6%, 0.7: -48.6%, 0.85: -41.6% | partial R2 > 0.7; spread >= 20 pp between delta 0.55 and 0.85 (event-window MDD, amendment A7) | FAIL | 75 |
| 11 | Bubble shape and populations | mean 2nd difference of log P over mania > 0 in 80% (median 1.49e-04); topped share = 48%; median peak P/V in topped seeds = 2.29 | convex; 40-60% topped; peak P/V 1.6-2.5 in topped seeds | PASS | 25 |
| 12 | Sentiment dynamics | median ACF(1) = 0.872; median corr(s_t, r_t) = 0.360; median calm corr(s_t-1, r_t) = -0.005 (configured b_pred = 0.0008) | ACF(1) 0.7-0.9; corr 0.25-0.55; lagged corr equals configured b_pred within CI | PASS | 245 |
| 13 | IV realism | mean IV calm 29.0%, panic 68.3%; median corr(IV, next-20d RV) = 0.43; IV-RV calm +6.6 pts, panic +24.1 pts; sd of calm IV across seeds 12.12 | calm 25-35%, panic 60-100%; corr 0.4-0.8; IV-RV +3..+8 calm, +10..+25 panic; non-degenerate across seeds | PASS | 245 |
| 14 | Value leak | see evaluation.leakage_audit (L1-L3) | calm R2 <= 0.30; event R2 < 0.90 & MAPE >= 10%; no inversion | n/a | 0 |
| 15 | Phase/time separability | macro-phase accuracy from day alone = 68.5% (mixed set, 245 paths; within-scenario mean 71.9%); |corr(day, phase id)| = 0.14 | < 80% on the mixed set; < 0.9 | PASS | 245 |
| 16 | Composite phase clock | see evaluation.leakage_audit (L2b) | selectivity <= 10 pp | n/a | 0 |
| 17 | Conditioning | flat: rejection rate 0.0%; bull_trap: rejection rate 3.8%; crash: rejection rate 1.3%; sustained_bull: rejection rate 19.4%; mixed: rejection rate 1.3%; flat_T800: rejection rate 0.0%; bull-trap topped share 48% | rejection < 5% per scenario; joint conditioning published | FAIL | 245 |
| 18 | Start design applied | unit test (tests/) | C_0 as configured | n/a | 0 |
| 19 | Action-space reachability | unit test (tests/) | any allocation reachable; SELL feasible at t=1 | n/a | 0 |
| 20 | Magnitudes | median crash MDD = -49.1%; median calm daily sigma (flat) = 1.49%; median worst panic day = -8.3% | crash MDD -20..-65%; calm sigma 1.4-2.2%/day; worst day -6..-15% in panic | PASS | 100 |

**Pass 7 / fail 6 / not applicable 7.**

Reference values (plan Section 9): S&P 500 daily excess kurtosis ~7-10; |r| ACF(1) ~0.2; TwinMarket SSE-50 kurtosis 7.26, leverage 0.14, GARCH alpha+beta 0.95; Hashimoto 18 JPX stocks kurtosis 7.85 +/- 1.07, |r| ACF(1) 0.19, |r|-volume correlation 0.46.
