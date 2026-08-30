# E1 calibration variants (checklist subset, 25 seeds per scenario, crash per delta)

Generated from the quick-iteration runs during E1 (scratchpad quick_items.py). Final defaults = variant E (df 5, alpha/gamma/beta 0.10/0.10/0.83, panic_mult 5, jump_rate 0.008, sbar 0.017). The full 50-seed run is in checklist_v2.md.

```
=== A_default  cfg={}  (28s)
 1 PASS  LB Q(10) p>0.05 in 90%; median |ACF(1)| = 0.058
 2 FAIL  excess kurtosis > 1.5 in 75% (median 2.53); JB rejects in 99%; Hill median 3.44
 3 FAIL  LB|r| p<0.01 in 50%; LB r^2 in 40%; ARCH-LM(5) rejects in 33%; median ACF|r|(1) = 0.108
 6 PASS  corr(r_t,|r_t+1|) < 0 in 73% (median -0.066); GJR gamma median 0.065
 7 FAIL  median Spearman corr(volume,|r|) = 0.338; median AC(1) log volume = 0.770; median Shapiro p = 0.030
 8 FAIL  median skew = -0.416; worst day larger than best in 68%
10 FAIL  partial R2 of delta (controlling D_V) = 0.36; MDD spread between delta 0.55 and 0.85 = 16.5 pp; means 0.55: -57.7%, 0.7: -48.2%, 0.85: -41.2%
11 PASS  mean 2nd difference of log P over mania > 0 in 72% (median 1.36e-04); topped share = 56%; median peak P/V in topped seeds = 2.36
12 PASS  median ACF(1) = 0.881; median corr(s_t, r_t) = 0.375; median calm corr(s_t-1, r_t) = -0.005 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 29.5%, panic 56.1%; median corr(IV, next-20d RV) = 0.31; IV-RV calm +7.2 pts, panic +21.8 pts; sd of calm IV across seeds 7.21
20 PASS  median crash MDD = -49.1%; median calm daily sigma (flat) = 1.46%; median worst panic day = -6.7%
rejection rates: {'flat': 0.0, 'bull_trap': 0.074, 'crash': 0.013, 'sustained_bull': 0.107}

=== B_garch  cfg={'garch': {'alpha': 0.08, 'gamma': 0.1, 'beta': 0.85}}  (28s)
 1 PASS  LB Q(10) p>0.05 in 88%; median |ACF(1)| = 0.063
 2 FAIL  excess kurtosis > 1.5 in 76% (median 2.61); JB rejects in 98%; Hill median 3.43
 3 FAIL  LB|r| p<0.01 in 51%; LB r^2 in 42%; ARCH-LM(5) rejects in 39%; median ACF|r|(1) = 0.136
 6 PASS  corr(r_t,|r_t+1|) < 0 in 71% (median -0.072); GJR gamma median 0.057
 7 FAIL  median Spearman corr(volume,|r|) = 0.330; median AC(1) log volume = 0.783; median Shapiro p = 0.020
 8 PASS  median skew = -0.387; worst day larger than best in 71%
10 FAIL  partial R2 of delta (controlling D_V) = 0.36; MDD spread between delta 0.55 and 0.85 = 17.0 pp; means 0.55: -57.2%, 0.7: -47.4%, 0.85: -40.2%
11 PASS  mean 2nd difference of log P over mania > 0 in 68% (median 1.20e-04); topped share = 56%; median peak P/V in topped seeds = 2.35
12 PASS  median ACF(1) = 0.883; median corr(s_t, r_t) = 0.374; median calm corr(s_t-1, r_t) = 0.001 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 28.1%, panic 49.8%; median corr(IV, next-20d RV) = 0.31; IV-RV calm +7.2 pts, panic +19.9 pts; sd of calm IV across seeds 7.67
20 FAIL  median crash MDD = -47.8%; median calm daily sigma (flat) = 1.35%; median worst panic day = -6.2%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.013, 'sustained_bull': 0.107}

=== C_garch_jumps  cfg={'garch': {'alpha': 0.08, 'gamma': 0.1, 'beta': 0.85}, 'jump_rate': 0.008}  (28s)
 1 PASS  LB Q(10) p>0.05 in 84%; median |ACF(1)| = 0.059
 2 PASS  excess kurtosis > 1.5 in 87% (median 3.12); JB rejects in 99%; Hill median 3.15
 3 FAIL  LB|r| p<0.01 in 45%; LB r^2 in 40%; ARCH-LM(5) rejects in 37%; median ACF|r|(1) = 0.123
 6 FAIL  corr(r_t,|r_t+1|) < 0 in 69% (median -0.055); GJR gamma median 0.034
 7 FAIL  median Spearman corr(volume,|r|) = 0.330; median AC(1) log volume = 0.782; median Shapiro p = 0.006
 8 PASS  median skew = -0.465; worst day larger than best in 71%
10 FAIL  partial R2 of delta (controlling D_V) = 0.32; MDD spread between delta 0.55 and 0.85 = 17.4 pp; means 0.55: -56.4%, 0.7: -46.6%, 0.85: -39.0%
11 PASS  mean 2nd difference of log P over mania > 0 in 68% (median 1.22e-04); topped share = 52%; median peak P/V in topped seeds = 2.35
12 PASS  median ACF(1) = 0.881; median corr(s_t, r_t) = 0.369; median calm corr(s_t-1, r_t) = 0.001 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 27.7%, panic 49.8%; median corr(IV, next-20d RV) = 0.29; IV-RV calm +6.7 pts, panic +19.3 pts; sd of calm IV across seeds 7.69
20 FAIL  median crash MDD = -48.2%; median calm daily sigma (flat) = 1.37%; median worst panic day = -6.5%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.0, 'sustained_bull': 0.167}

=== D_jumps  cfg={'jump_rate': 0.008}  (28s)
 1 PASS  LB Q(10) p>0.05 in 90%; median |ACF(1)| = 0.055
 2 PASS  excess kurtosis > 1.5 in 86% (median 2.99); JB rejects in 100%; Hill median 3.30
 3 FAIL  LB|r| p<0.01 in 42%; LB r^2 in 37%; ARCH-LM(5) rejects in 29%; median ACF|r|(1) = 0.095
 6 PASS  corr(r_t,|r_t+1|) < 0 in 71% (median -0.057); GJR gamma median 0.042
 7 FAIL  median Spearman corr(volume,|r|) = 0.338; median AC(1) log volume = 0.774; median Shapiro p = 0.009
 8 FAIL  median skew = -0.445; worst day larger than best in 67%
10 FAIL  partial R2 of delta (controlling D_V) = 0.32; MDD spread between delta 0.55 and 0.85 = 17.1 pp; means 0.55: -56.9%, 0.7: -47.2%, 0.85: -39.8%
11 PASS  mean 2nd difference of log P over mania > 0 in 68% (median 1.24e-04); topped share = 52%; median peak P/V in topped seeds = 2.31
12 PASS  median ACF(1) = 0.879; median corr(s_t, r_t) = 0.369; median calm corr(s_t-1, r_t) = -0.003 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 29.4%, panic 56.1%; median corr(IV, next-20d RV) = 0.30; IV-RV calm +6.7 pts, panic +20.9 pts; sd of calm IV across seeds 7.20
20 PASS  median crash MDD = -49.2%; median calm daily sigma (flat) = 1.51%; median worst panic day = -7.0%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.0, 'sustained_bull': 0.107}

=== E  cfg={'garch': {'alpha': 0.1, 'gamma': 0.1, 'beta': 0.83, 'df': 5, 'panic_mult': 5}, 'jump_rate': 0.008}  (22s)
 1 PASS  LB Q(10) p>0.05 in 88%; median |ACF(1)| = 0.073
 2 FAIL  excess kurtosis > 1.5 in 71% (median 2.61); JB rejects in 92%; Hill median 3.50
 3 FAIL  LB|r| p<0.01 in 60%; LB r^2 in 52%; ARCH-LM(5) rejects in 44%; median ACF|r|(1) = 0.160
 6 FAIL  corr(r_t,|r_t+1|) < 0 in 69% (median -0.054); GJR gamma median 0.043
 7 FAIL  median Spearman corr(volume,|r|) = 0.369; median AC(1) log volume = 0.798; median Shapiro p = 0.010
 8 FAIL  median skew = -0.354; worst day larger than best in 65%
10 FAIL  partial R2 of delta (controlling D_V) = 0.34; MDD spread between delta 0.55 and 0.85 = 16.4 pp; means 0.55: -57.6%, 0.7: -48.5%, 0.85: -41.2%
11 PASS  mean 2nd difference of log P over mania > 0 in 76% (median 1.45e-04); topped share = 48%; median peak P/V in topped seeds = 2.20
12 PASS  median ACF(1) = 0.873; median corr(s_t, r_t) = 0.358; median calm corr(s_t-1, r_t) = -0.006 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 29.0%, panic 62.0%; median corr(IV, next-20d RV) = 0.40; IV-RV calm +6.4 pts, panic +20.9 pts; sd of calm IV across seeds 14.57
20 PASS  median crash MDD = -48.5%; median calm daily sigma (flat) = 1.48%; median worst panic day = -7.4%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.013, 'sustained_bull': 0.167}

=== F  cfg={'garch': {'alpha': 0.1, 'gamma': 0.1, 'beta': 0.83, 'df': 4, 'panic_mult': 5}, 'jump_rate': 0.006}  (22s)
 1 PASS  LB Q(10) p>0.05 in 84%; median |ACF(1)| = 0.059
 2 PASS  excess kurtosis > 1.5 in 83% (median 3.18); JB rejects in 99%; Hill median 3.18
 3 FAIL  LB|r| p<0.01 in 55%; LB r^2 in 43%; ARCH-LM(5) rejects in 39%; median ACF|r|(1) = 0.133
 6 PASS  corr(r_t,|r_t+1|) < 0 in 71% (median -0.058); GJR gamma median 0.041
 7 FAIL  median Spearman corr(volume,|r|) = 0.332; median AC(1) log volume = 0.789; median Shapiro p = 0.006
 8 PASS  median skew = -0.469; worst day larger than best in 73%
10 FAIL  partial R2 of delta (controlling D_V) = 0.33; MDD spread between delta 0.55 and 0.85 = 17.8 pp; means 0.55: -57.1%, 0.7: -47.3%, 0.85: -39.3%
11 PASS  mean 2nd difference of log P over mania > 0 in 64% (median 1.16e-04); topped share = 52%; median peak P/V in topped seeds = 2.30
12 PASS  median ACF(1) = 0.883; median corr(s_t, r_t) = 0.368; median calm corr(s_t-1, r_t) = 0.004 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 27.5%, panic 53.6%; median corr(IV, next-20d RV) = 0.32; IV-RV calm +7.0 pts, panic +23.2 pts; sd of calm IV across seeds 7.53
20 FAIL  median crash MDD = -47.8%; median calm daily sigma (flat) = 1.32%; median worst panic day = -6.8%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.0, 'sustained_bull': 0.107}

=== G  cfg={'garch': {'alpha': 0.12, 'gamma': 0.12, 'beta': 0.8, 'df': 4, 'panic_mult': 5}, 'jump_rate': 0.008}  (22s)
 1 PASS  LB Q(10) p>0.05 in 82%; median |ACF(1)| = 0.059
 2 PASS  excess kurtosis > 1.5 in 88% (median 3.75); JB rejects in 99%; Hill median 3.07
 3 FAIL  LB|r| p<0.01 in 55%; LB r^2 in 43%; ARCH-LM(5) rejects in 41%; median ACF|r|(1) = 0.139
 6 PASS  corr(r_t,|r_t+1|) < 0 in 71% (median -0.055); GJR gamma median 0.038
 7 FAIL  median Spearman corr(volume,|r|) = 0.328; median AC(1) log volume = 0.788; median Shapiro p = 0.005
 8 PASS  median skew = -0.499; worst day larger than best in 75%
10 FAIL  partial R2 of delta (controlling D_V) = 0.32; MDD spread between delta 0.55 and 0.85 = 17.8 pp; means 0.55: -56.2%, 0.7: -46.2%, 0.85: -38.4%
11 PASS  mean 2nd difference of log P over mania > 0 in 64% (median 1.18e-04); topped share = 48%; median peak P/V in topped seeds = 2.23
12 PASS  median ACF(1) = 0.885; median corr(s_t, r_t) = 0.364; median calm corr(s_t-1, r_t) = 0.008 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 26.3%, panic 51.0%; median corr(IV, next-20d RV) = 0.30; IV-RV calm +6.6 pts, panic +22.3 pts; sd of calm IV across seeds 7.37
20 FAIL  median crash MDD = -47.1%; median calm daily sigma (flat) = 1.25%; median worst panic day = -6.4%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.0, 'sustained_bull': 0.167}

=== H  cfg={'garch': {'alpha': 0.1, 'gamma': 0.1, 'beta': 0.83, 'df': 5, 'panic_mult': 5}, 'jump_rate': 0.008, 'lam_panic': 0.25}  (22s)
 1 PASS  LB Q(10) p>0.05 in 88%; median |ACF(1)| = 0.073
 2 FAIL  excess kurtosis > 1.5 in 71% (median 2.68); JB rejects in 91%; Hill median 3.42
 3 FAIL  LB|r| p<0.01 in 59%; LB r^2 in 53%; ARCH-LM(5) rejects in 46%; median ACF|r|(1) = 0.157
 6 FAIL  corr(r_t,|r_t+1|) < 0 in 65% (median -0.050); GJR gamma median 0.048
 7 FAIL  median Spearman corr(volume,|r|) = 0.361; median AC(1) log volume = 0.800; median Shapiro p = 0.007
 8 FAIL  median skew = -0.356; worst day larger than best in 68%
10 FAIL  partial R2 of delta (controlling D_V) = 0.38; MDD spread between delta 0.55 and 0.85 = 17.1 pp; means 0.55: -57.0%, 0.7: -47.6%, 0.85: -39.9%
11 PASS  mean 2nd difference of log P over mania > 0 in 76% (median 1.45e-04); topped share = 48%; median peak P/V in topped seeds = 2.20
12 PASS  median ACF(1) = 0.872; median corr(s_t, r_t) = 0.360; median calm corr(s_t-1, r_t) = -0.020 (configured b_pred = 0.0008)
13 PASS  mean IV calm 28.9%, panic 62.0%; median corr(IV, next-20d RV) = 0.41; IV-RV calm +6.4 pts, panic +20.5 pts; sd of calm IV across seeds 14.57
20 PASS  median crash MDD = -49.6%; median calm daily sigma (flat) = 1.48%; median worst panic day = -7.5%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.0, 'sustained_bull': 0.167}

=== I  cfg={'garch': {'alpha': 0.1, 'gamma': 0.1, 'beta': 0.83, 'df': 5, 'panic_mult': 5}, 'jump_rate': 0.012}  (23s)
 1 PASS  LB Q(10) p>0.05 in 90%; median |ACF(1)| = 0.072
 2 FAIL  excess kurtosis > 1.5 in 79% (median 3.16); JB rejects in 95%; Hill median 3.30
 3 FAIL  LB|r| p<0.01 in 55%; LB r^2 in 45%; ARCH-LM(5) rejects in 35%; median ACF|r|(1) = 0.140
 6 PASS  corr(r_t,|r_t+1|) < 0 in 71% (median -0.050); GJR gamma median 0.021
 7 PASS  median Spearman corr(volume,|r|) = 0.370; median AC(1) log volume = 0.795; Shapiro p > 0.01 in 54% of seeds (median p = 0.016)
 8 FAIL  median skew = -0.398; worst day larger than best in 69%
10 FAIL  partial R2 of delta (controlling D_V) = 0.34; MDD spread between delta 0.55 and 0.85 = 15.9 pp; means 0.55: -57.3%, 0.7: -48.4%, 0.85: -41.3%
11 PASS  mean 2nd difference of log P over mania > 0 in 80% (median 1.43e-04); topped share = 44%; median peak P/V in topped seeds = 2.28
12 PASS  median ACF(1) = 0.874; median corr(s_t, r_t) = 0.359; median calm corr(s_t-1, r_t) = -0.005 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 29.0%, panic 62.0%; median corr(IV, next-20d RV) = 0.38; IV-RV calm +5.8 pts, panic +21.0 pts; sd of calm IV across seeds 14.56
20 PASS  median crash MDD = -49.1%; median calm daily sigma (flat) = 1.51%; median worst panic day = -7.5%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.013, 'sustained_bull': 0.194}

=== J  cfg={'garch': {'alpha': 0.1, 'gamma': 0.1, 'beta': 0.83, 'df': 5, 'panic_mult': 5}, 'jump_rate': 0.01, 'jump_sd': 0.04}  (23s)
 1 PASS  LB Q(10) p>0.05 in 90%; median |ACF(1)| = 0.076
 2 FAIL  excess kurtosis > 1.5 in 79% (median 3.31); JB rejects in 97%; Hill median 3.32
 3 FAIL  LB|r| p<0.01 in 53%; LB r^2 in 37%; ARCH-LM(5) rejects in 35%; median ACF|r|(1) = 0.148
 6 PASS  corr(r_t,|r_t+1|) < 0 in 70% (median -0.049); GJR gamma median 0.024
 7 PASS  median Spearman corr(volume,|r|) = 0.371; median AC(1) log volume = 0.799; Shapiro p > 0.01 in 52% of seeds (median p = 0.014)
 8 PASS  median skew = -0.455; worst day larger than best in 75%
10 FAIL  partial R2 of delta (controlling D_V) = 0.33; MDD spread between delta 0.55 and 0.85 = 16.2 pp; means 0.55: -57.4%, 0.7: -48.4%, 0.85: -41.3%
11 PASS  mean 2nd difference of log P over mania > 0 in 80% (median 1.52e-04); topped share = 48%; median peak P/V in topped seeds = 2.21
12 PASS  median ACF(1) = 0.874; median corr(s_t, r_t) = 0.357; median calm corr(s_t-1, r_t) = -0.020 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 29.0%, panic 62.0%; median corr(IV, next-20d RV) = 0.39; IV-RV calm +5.4 pts, panic +20.8 pts; sd of calm IV across seeds 14.52
20 PASS  median crash MDD = -48.5%; median calm daily sigma (flat) = 1.54%; median worst panic day = -7.6%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.013, 'sustained_bull': 0.286}

=== K  cfg={'garch': {'alpha': 0.1, 'gamma': 0.1, 'beta': 0.83, 'df': 4, 'panic_mult': 6}, 'jump_rate': 0.006}  (23s)
 1 PASS  LB Q(10) p>0.05 in 84%; median |ACF(1)| = 0.059
 2 PASS  excess kurtosis > 1.5 in 82% (median 3.42); JB rejects in 99%; Hill median 3.16
 3 FAIL  LB|r| p<0.01 in 57%; LB r^2 in 45%; ARCH-LM(5) rejects in 42%; median ACF|r|(1) = 0.133
 6 PASS  corr(r_t,|r_t+1|) < 0 in 72% (median -0.063); GJR gamma median 0.051
 7 FAIL  median Spearman corr(volume,|r|) = 0.341; median AC(1) log volume = 0.794; Shapiro p > 0.01 in 47% of seeds (median p = 0.005)
 8 PASS  median skew = -0.462; worst day larger than best in 72%
10 FAIL  partial R2 of delta (controlling D_V) = 0.32; MDD spread between delta 0.55 and 0.85 = 17.5 pp; means 0.55: -57.4%, 0.7: -47.7%, 0.85: -39.8%
11 PASS  mean 2nd difference of log P over mania > 0 in 64% (median 1.16e-04); topped share = 52%; median peak P/V in topped seeds = 2.30
12 PASS  median ACF(1) = 0.882; median corr(s_t, r_t) = 0.368; median calm corr(s_t-1, r_t) = 0.004 (configured b_pred = 0.0008)
13 FAIL  mean IV calm 27.5%, panic 59.2%; median corr(IV, next-20d RV) = 0.34; IV-RV calm +7.0 pts, panic +26.5 pts; sd of calm IV across seeds 7.52
20 FAIL  median crash MDD = -48.4%; median calm daily sigma (flat) = 1.32%; median worst panic day = -7.0%
rejection rates: {'flat': 0.0, 'bull_trap': 0.107, 'crash': 0.0, 'sustained_bull': 0.107}

```
