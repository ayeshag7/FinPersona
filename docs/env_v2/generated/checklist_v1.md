# Section 9 validation checklist (v1)

Generator v1; 50 seeds per scenario (crash: per delta), T = 200. Items 14 and 16 are filled by `python -m evaluation.leakage_audit`; 18 and 19 are unit tests.

| # | Property | Statistic | Pass criterion | Result | n |
|---|---|---|---|---|---|
| 1 | No linear autocorrelation of returns in calm phases (Cont 1) | LB Q(10) p>0.05 in 72%; median |ACF(1)| = 0.161 | >= 80% of seeds p>0.05; |ACF(1)| < 0.15 | FAIL | 100 |
| 2 | Heavy tails (Cont 2, 7) | excess kurtosis > 1.5 in 4% (median 0.22); JB rejects in 28%; Hill median 5.72 | kurtosis > 1.5 in >= 80%; JB rejects; Hill 2.5-5 | FAIL | 270 |
| 3 | Volatility clustering (Cont 6) | LB|r| p<0.01 in 39%; LB r^2 in 41%; ARCH-LM(5) rejects in 34%; median ACF|r|(1) = 0.137 | p < 0.01 in >= 80%; ACF|r|(1) 0.1-0.4 | FAIL | 270 |
| 4 | Decay of ACF|r| (Cont 8) | median ACF|r| at lags 1: 0.008, 5: 0.002, 10: -0.002, 20: -0.009, 50: -0.009 | descriptive (T = 800 paths); not a pass criterion | n/a | 20 |
| 5 | GARCH persistence recoverable | median alpha+beta = 0.966 | median alpha + beta in [0.90, 0.995] | PASS | 270 |
| 6 | Leverage effect (Cont 9) | corr(r_t,|r_t+1|) < 0 in 55% (median -0.006); GJR gamma median 0.032 | negative in >= 70%; gamma > 0 | FAIL | 270 |
| 7 | Volume-volatility (Cont 10) | median Spearman corr(volume,|r|) = 0.052; median AC(1) log volume = 0.925; median Shapiro p = 0.000 | corr 0.2-0.5; AC(1) 0.5-0.8; log-normality not rejected | FAIL | 270 |
| 8 | Gain/loss asymmetry in crash (Cont 3) | median skew = 0.011; worst day larger than best in 55% | skew < 0; worst > best in >= 70% of crash seeds | FAIL | 150 |
| 9 | Mispricing persistence (FW regime) | median ACF(1) of x in calm = -0.0092; median half-life = inf d; median sd(x) = 0.007 | ACF(1) >= 0.98; half-life >= 60 d; sd 0.08-0.20 | FAIL | 100 |
| 10 | Delta matters | partial R2 of delta (controlling D_V) = 0.03; MDD spread between delta 0.85 and 0.95 = 0.5 pp; means 0.85: -48.2%, 0.92: -47.8%, 0.95: -47.7% | partial R2 > 0.7; spread >= 20 pp between delta 0.55 and 0.85 | FAIL | 150 |
| 11 | Bubble shape and populations | mean 2nd difference of log P over mania > 0 in 16% (median -9.86e-05); topped share = n/a (v1 has no hazard top); median peak P/V (all seeds) = 2.15 | convex; 40-60% topped; peak P/V 1.6-2.5 in topped seeds | FAIL | 50 |
| 12 | Sentiment dynamics | median ACF(1) = 0.606; median corr(s_t, r_t) = 0.075; median calm corr(s_t-1, r_t) = -0.006 (configured b_pred = 0.0) | ACF(1) 0.7-0.9; corr 0.25-0.55; lagged corr equals configured b_pred within CI | FAIL | 270 |
| 13 | IV realism | mean IV calm 12.5%, panic 33.8%; median corr(IV, next-20d RV) = 0.39; IV-RV calm -18.5 pts, panic -22.9 pts; sd of calm IV across seeds 1.48 | calm 25-35%, panic 60-100%; corr 0.4-0.8; IV-RV +3..+8 calm, +10..+25 panic; non-degenerate across seeds | FAIL | 270 |
| 14 | Value leak | see evaluation.leakage_audit (L1-L3) | calm R2 <= 0.30; event R2 < 0.90 & MAPE >= 10%; no inversion | n/a | 0 |
| 15 | Phase/time separability | macro-phase accuracy from day alone = 63.6% (mixed set, 270 paths; within-scenario mean 100.0%); |corr(day, phase id)| = 0.29 | < 80% on the mixed set; < 0.9 | PASS | 270 |
| 16 | Composite phase clock | see evaluation.leakage_audit (L2b) | selectivity <= 10 pp | n/a | 0 |
| 17 | Conditioning | flat: rejection rate 0.0%; bull_trap: rejection rate 0.0%; crash: rejection rate 0.0%; flat_T800: rejection rate 0.0%; bull-trap topped share n/a | rejection < 5% per scenario; joint conditioning published | PASS | 270 |
| 18 | Start design applied | unit test (tests/) | C_0 as configured | n/a | 0 |
| 19 | Action-space reachability | unit test (tests/) | any allocation reachable; SELL feasible at t=1 | n/a | 0 |
| 20 | Magnitudes | median crash MDD = -46.8%; median calm daily sigma (flat) = 2.08%; median worst panic day = -8.7% | crash MDD -20..-65%; calm sigma 1.4-2.2%/day; worst day -6..-15% in panic | PASS | 200 |

**Pass 3 / fail 10 / not applicable 7.**

Reference values (plan Section 9): S&P 500 daily excess kurtosis ~7-10; |r| ACF(1) ~0.2; TwinMarket SSE-50 kurtosis 7.26, leverage 0.14, GARCH alpha+beta 0.95; Hashimoto 18 JPX stocks kurtosis 7.85 +/- 1.07, |r| ACF(1) 0.19, |r|-volume correlation 0.46.
