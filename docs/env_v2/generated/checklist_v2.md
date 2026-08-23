# Section 9 validation checklist (v2)

Generator v2; 50 seeds per scenario (crash: per delta), T = 200; config overrides {}; engine default. Items 14 and 16 are filled by `python -m evaluation.leakage_audit`; 18 and 19 are unit tests.

| # | Property | Statistic | Pass criterion | Result | n |
|---|---|---|---|---|---|
| 1 | No linear autocorrelation of returns in calm phases (Cont 1) | LB Q(10) p>0.05 in 88%; median |ACF(1)| = 0.080 | >= 80% of seeds p>0.05; |ACF(1)| < 0.15 | PASS | 100 |
| 2 | Heavy tails (Cont 2, 7) | excess kurtosis > 1.5 in 79% (median 2.96); JB rejects in 94%; Hill median 3.36 | kurtosis > 1.5 in >= 80%; JB rejects; Hill 2.5-5 | FAIL | 470 |
| 3 | Volatility clustering (Cont 6) | LB|r| p<0.01 in 61%; LB r^2 in 49%; ARCH-LM(5) rejects in 42%; median ACF|r|(1) = 0.151 | p < 0.01 in >= 80%; ACF|r|(1) 0.1-0.4 | FAIL | 470 |
| 4 | Decay of ACF|r| (Cont 8) | median ACF|r| at lags 1: 0.229, 5: 0.177, 10: 0.154, 20: 0.083, 50: 0.017 | descriptive (T = 800 paths); not a pass criterion | n/a | 20 |
| 5 | GARCH persistence recoverable | median alpha+beta = 0.964 | median alpha + beta in [0.90, 0.995] | PASS | 470 |
| 6 | Leverage effect (Cont 9) | corr(r_t,|r_t+1|) < 0 in 68% (median -0.045); GJR gamma median 0.047 | negative in >= 70%; gamma > 0 | FAIL | 470 |
| 7 | Volume-volatility (Cont 10) | median Spearman corr(volume,|r|) = 0.372; median AC(1) log volume = 0.806; Shapiro p > 0.01 in 48% of seeds (median p = 0.007) | corr 0.2-0.5; AC(1) 0.5-0.8; log-normality not rejected (p > 0.01 in >= 50% of seeds) | FAIL | 470 |
| 8 | Gain/loss asymmetry in crash (Cont 3) | median skew = -0.392; worst day larger than best in 70% | skew < 0; worst > best in >= 70% of crash seeds | PASS | 150 |
| 9 | Mispricing persistence (FW regime) | 200-day calm windows: median ACF(1) of x = 0.9507, half-life = 14 d, sd(x) = 0.053; T=800 phase-free: ACF(1) = 0.9905, half-life = 72 d, sd(x) = 0.128 (criterion applied here) | ACF(1) >= 0.98; half-life >= 60 d; sd 0.08-0.20 | PASS | 20 |
| 10 | Delta matters | event-window MDD: partial R2 of delta (controlling D_V) = 0.38, spread between delta 0.55 and 0.85 = 18.0 pp, means 0.55: -53.0%, 0.7: -42.6%, 0.85: -35.0%; whole-path MDD (reported): partial R2 0.35, spread 16.5 pp, means 0.55: -56.8%, 0.7: -47.3%, 0.85: -40.3% | partial R2 > 0.7; spread >= 20 pp between delta 0.55 and 0.85 (event-window MDD, amendment A7) | FAIL | 150 |
| 11 | Bubble shape and populations | mean 2nd difference of log P over mania > 0 in 66% (median 9.59e-05); topped share = 44%; median peak P/V in topped seeds = 2.21 | convex; 40-60% topped; peak P/V 1.6-2.5 in topped seeds | PASS | 50 |
| 12 | Sentiment dynamics | median ACF(1) = 0.873; median corr(s_t, r_t) = 0.365; median calm corr(s_t-1, r_t) = -0.010 (configured b_pred = 0.0008) | ACF(1) 0.7-0.9; corr 0.25-0.55; lagged corr equals configured b_pred within CI | PASS | 470 |
| 13 | IV realism | mean IV calm 28.6%, panic 59.4%; median corr(IV, next-20d RV) = 0.39; IV-RV calm +6.7 pts, panic +21.6 pts; sd of calm IV across seeds 14.82 | calm 25-35%, panic 60-100%; corr 0.4-0.8; IV-RV +3..+8 calm, +10..+25 panic; non-degenerate across seeds | FAIL | 470 |
| 14 | Value leak | see evaluation.leakage_audit (L1-L3) | calm R2 <= 0.30; event R2 < 0.90 & MAPE >= 10%; no inversion | n/a | 0 |
| 15 | Phase/time separability | macro-phase accuracy from day alone = 64.8% (mixed set, 470 paths; within-scenario mean 73.6%); |corr(day, phase id)| = 0.03 | < 80% on the mixed set; < 0.9 | PASS | 470 |
| 16 | Composite phase clock | see evaluation.leakage_audit (L2b) | selectivity <= 10 pp | n/a | 0 |
| 17 | Conditioning | flat: rejection rate 0.0%; bull_trap: rejection rate 5.7%; crash: rejection rate 1.3%; sustained_bull: rejection rate 39.8%; mixed: rejection rate 1.3%; flat_T800: rejection rate 0.0%; bull-trap topped share 44% | rejection < 5% per scenario; joint conditioning published | FAIL | 470 |
| 18 | Start design applied | unit test (tests/) | C_0 as configured | n/a | 0 |
| 19 | Action-space reachability | unit test (tests/) | any allocation reachable; SELL feasible at t=1 | n/a | 0 |
| 20 | Magnitudes | median crash MDD = -48.0%; median calm daily sigma (flat) = 1.53%; median worst panic day = -7.9% | crash MDD -20..-65%; calm sigma 1.4-2.2%/day; worst day -6..-15% in panic | PASS | 200 |

**Pass 8 / fail 7 / not applicable 5.**

Reference values (plan Section 9): S&P 500 daily excess kurtosis ~7-10; |r| ACF(1) ~0.2; TwinMarket SSE-50 kurtosis 7.26, leverage 0.14, GARCH alpha+beta 0.95; Hashimoto 18 JPX stocks kurtosis 7.85 +/- 1.07, |r| ACF(1) 0.19, |r|-volume correlation 0.46.
