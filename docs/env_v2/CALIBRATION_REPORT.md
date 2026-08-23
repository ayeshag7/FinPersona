# Calibration report (E6 draft, assembled 22 Aug 2026)

Everything below is regenerated from code (`docs/env_v2/generated/`); reference ranges are the plan's Section 9 notes.
Open issues and amendments: `DECISION_LOG.md` (addendum), `PREREGISTRATION_AMENDMENTS.md`.

## 1. Generator parameters in force
- Fundamental: mu_V 0.00025/day, sigma_V 0.006/day, t(5); sustained-bull mu ~ U(0.0015, 0.0025); crash D_V ~ U(0.10, 0.30).
- Mispricing engine `fw_single_stock_fallback`: phi 0.463, chi 1.5, sigma_f 0.758, sigma_c 2.087, alpha_0 -0.327, alpha_n 1.79, alpha_p 18.43, beta 1.0, mu 0.01, price_scale 100.0; pilot n_bar 0.998, w_bar 0.761, stationary sd(x) 0.142, ACF(1) 0.9963. Source: DESIGN CHOICE (no SMM estimate available): FW 2012 functional form with phi set for a ~150-day calm half-life at the realised fundamentalist share n_bar=0.998; see DECISION_LOG.md row 2
- GJR-GARCH-t: alpha 0.1, gamma 0.1, beta 0.83 (persistence 0.980), sbar 0.017, df 5.0, panic multiplier 5.0, scale_mode variance; phase multipliers {'calm': 1.0, 'deterioration': 1.5, 'panic': 4.0, 'stabilisation': 1.5, 'mania': 1.5, 'blow-off': 2.0, 'post-top': 3.0, 'sustained-bull': 0.25}.
- Jumps: on, rate 0.01/day, N(-0.04, 0.03). Sentiment b_pred 0.0008, reversal 0.0006.
- Bubble: g0 0.002, kappa ~ U(0.02, 0.04), g_max 0.012, hazard h0 0.0003, b 6.0 (60-seed calibration: topped 0.47, topped peak P/V median 2.12).
- Burn-in 260 d; rejection up to 50 attempts.

## 2. Section 9 checklist (50 seeds per scenario, crash per delta, T = 200; final calibration incl. sustained-bull variance x1.0; item 10 on the event window, A7)
| item | property | statistic | criterion | result | n_seeds |
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

## 3. Hazard calibration grid (best five; `hazard_calibration.csv`)
| h0 | b | g_max | topped_share | peak_pv_topped_median | peak_pv_topped_q10 | peak_pv_topped_q90 | peak_pv_untopped_median | top_day_in_mania_median | mean_attempts | score |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | 6.000 | 0.012 | 0.467 | 2.125 | 1.671 | 2.523 | 1.823 | 105.500 | 1.050 | 0.164 |
| 0.000 | 8.000 | 0.012 | 0.583 | 2.189 | 1.800 | 2.513 | 1.789 | 106.000 | 1.050 | 0.381 |
| 0.001 | 4.000 | 0.015 | 0.550 | 2.406 | 1.776 | 2.866 | 2.064 | 105.000 | 1.067 | 0.385 |
| 0.000 | 6.000 | 0.015 | 0.600 | 2.407 | 1.734 | 2.799 | 2.024 | 103.000 | 1.033 | 0.502 |
| 0.000 | 8.000 | 0.010 | 0.383 | 2.084 | 1.751 | 2.493 | 1.846 | 102.000 | 1.067 | 0.571 |

## 4. Section 5 audit (50 seeds, 27,000 steps after path subsampling; `leakage_audit_v2.md`)
### L1 algebraic inversion (A6 rule) -- PASS
| candidate | fitted_k | median_APE | max_APE | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|
| k * P (price itself) | 1.0506 | 0.1236 | 2.3639 | 0.9592 | 0.6872 | True |
| k * P / reported_PE | 17.5239 | 0.1546 | 0.7136 | 0.9717 | 0.6872 | True |
| k * P * dividend_yield | 0.5019 | 0.1558 | 0.7224 | 0.9706 | 0.6872 | True |
| k * analyst_fair_value | 0.9839 | 0.2235 | 1.5688 | 0.9762 | 0.6872 | True |
### L2 surrogate, best models (held-out seeds) -- pre-registered absolute thresholds are the gate: FAIL (calm R2(x) 0.90, event 0.96, MAPE(V) 4.9%); exploratory selectivity of non-price fields +0.11 R2 / +2.9 pp; shuffled-V -0.06
| target | phase_group | n | R2 | sign_acc_resolvable | MAPE_V | R2_price_only | selectivity_R2 | R2_shuffledV |
|---|---|---|---|---|---|---|---|---|
| x | calm | 11700 | 0.898 | 0.969 | nan | 0.787 | 0.111 | -0.279 |
| x | event | 9239 | 0.961 | 0.977 | nan | 0.926 | 0.034 | -0.254 |
| x | resolution | 6061 | 0.942 | 0.986 | nan | 0.872 | 0.070 | -0.227 |
| x | all | 27000 | 0.947 | 0.976 | nan | 0.892 | 0.055 | -0.248 |
| logV | calm | 11700 | 0.805 | nan | 0.035 | 0.634 | 0.171 | -0.175 |
| logV | event | 9239 | 0.690 | nan | 0.049 | 0.425 | 0.266 | -0.258 |
| logV | resolution | 6061 | 0.711 | nan | 0.051 | 0.353 | 0.358 | -0.215 |
| logV | all | 27000 | 0.832 | nan | 0.044 | 0.670 | 0.162 | -0.198 |
### L2b composite phase clock -- PASS: full 84.9% vs price-only 78.3% (day-only 54.6%, majority 43.3%), selectivity +6.6 pp (margin 10 pp)
### Scenario discrimination (review R1-D5; reported, no threshold): sustained-bull vs mania vs calm days, n = 13,320 (majority 46%): accuracy price-only 75.3%, price+IV 78.0%, full 78.0%; recall of sustained-bull days 82-84% under every feature set -- the control is identifiable from PRICE DYNAMICS (a trend without mispricing), not from IV specifically (price+IV adds 2.7 pp over price-only).
### L4 resolvability
| scenario | phase | n_steps | median_abs_x | coverage_theta_0.03 | coverage_theta_0.05 | coverage_theta_0.08 |
|---|---|---|---|---|---|---|
| flat | calm | 4000 | 0.115 | 0.828 | 0.717 | 0.596 |
| bull_trap | calm | 1720 | 0.149 | 0.913 | 0.848 | 0.763 |
| bull_trap | mania | 2826 | 0.135 | 0.905 | 0.815 | 0.686 |
| bull_trap | blow-off | 1395 | 0.582 | 0.993 | 0.986 | 0.981 |
| bull_trap | post-top | 1459 | 0.288 | 0.951 | 0.926 | 0.867 |
| crash | calm | 5316 | 0.137 | 0.902 | 0.824 | 0.726 |
| crash | deterioration | 2038 | 0.128 | 0.877 | 0.797 | 0.678 |
| crash | panic | 3244 | 0.259 | 0.962 | 0.936 | 0.887 |
| crash | stabilisation | 4602 | 0.170 | 0.880 | 0.810 | 0.731 |
| sustained_bull | sustained-bull | 3400 | 0.014 | 0.185 | 0.057 | 0.005 |
| flat | ALL | 4000 | 0.115 | 0.828 | 0.717 | 0.596 |
| bull_trap | ALL | 7400 | 0.206 | 0.932 | 0.877 | 0.795 |
| crash | ALL | 15200 | 0.166 | 0.905 | 0.840 | 0.755 |
| sustained_bull | ALL | 3400 | 0.014 | 0.185 | 0.057 | 0.005 |

## 5. Generator sensitivities (25 seeds per scenario; checklist pass/fail counts; `generated/checklist_v2_sens_*.md`)
| Sensitivity | Pass / fail | Note |
|---|---|---|
| default (50 seeds) | 8 / 7 | `checklist_v2.md` |
| `fw_index` (FW 2012 index parameters, half-life ~580 d) | 7 / 6 | the plan's index-parameter sensitivity |
| `pruna` (Pruna et al. 2016) | 6 / 7 | |
| `fw_hl60` (60-day stationary half-life) | 7 / 8 | short-persistence bracket |
| `scale_mode = omega` (plan-literal omega multipliers) | 6 / 7 | cannot reach the panic targets (A3) |
| panic multiplier 3 | 8 / 5 | sensitivity range 3-6 |
| panic multiplier 6 | 7 / 6 | |
Items 9 and 11 are calibration targets (phi; hazard/cap) and pass by construction; the sustained-bull control runs at
variance multiplier 1.0 (review R1-D5) and its rejection rate (~37%) is published.

## 6. Sensitivities still to run (E6)
cost tier and visibility, ISFJ target, delta set, k range, start design, action interface, field order, horizon
disclosure (harness factors exist; LLM runs pending); FW index parameters and `scale_mode='omega'` as generator
sensitivities (flags exist). Single-stock SMM attempted on real data and rejected (J = 408; DECISION_LOG row 2 note). J-profile over phi (`fw_J_profile.csv`, other parameters at the index set, scale-free diagonal weights): J ranges 2.9-3.2 over phi in [0.03, 2.0] -- the nine FW return-moments are flat in the mispricing persistence, i.e. not identified.

## 7. L5 observables oracle (`generated/l5_observables_oracle.md`)
GBT on the rendered fields (+5 lags), training seeds 500-511, evaluated on seeds 0-9: per-phase OOS R2 of x_hat = 0.94 /
0.96 / 0.91 (calm / event / resolution) for the full field set and 0.90 / 0.91 / 0.80 for price-and-technicals only.
The withheld-information gap (MCR of the L5 policy minus MCR of the true-V mandate-conditional oracle, theta 0.05) is
0.02-0.03 in bull-trap and crash, 0.04 in flat and 0.07-0.08 in sustained bull (all personas), and price-only is within
0.01 of the full set. Reading: a policy fitted on what the agent SEES can nearly replicate the V-oracle -- the environment
withholds little of the DIRECTION of mispricing (the level of V is recoverable to ~4% MAPE); this is the same structural
fact as the L2 absolute failure and is disclosed as such. The plan's "information the environment deliberately withholds"
is therefore small by construction under the smooth-V / persistent-x design; it is what makes the fundamentalist mandate
playable (plan Section 5, first paragraph).
