# Calibration report (E6 draft, assembled 22 Aug 2026)

Everything below is regenerated from code (`docs/env_v2/generated/`); reference ranges are the plan's Section 9 notes.
Open issues and amendments: `DECISION_LOG.md` (addendum), `PREREGISTRATION_AMENDMENTS.md`.

## 1. Generator parameters in force
- Fundamental: mu_V 0.00025/day, sigma_V 0.006/day, t(5); sustained-bull mu ~ U(0.0015, 0.0025); crash D_V ~ U(0.10, 0.30).
- Mispricing engine `fw_fallback_hl150` (named in v2.1 Phase 0; printed as `fw_single_stock_fallback` before): phi 0.4632, chi 1.5, sigma_f 0.758, sigma_c 2.087, alpha_0 -0.327, alpha_n 1.79, alpha_p 18.43, beta 1.0, mu 0.01, price_scale 100.0. Pull-rate half-life ln2/(mu n_bar phi) = 150.0 d (CAL). 20,000-step pilot (raw weights): n_bar 0.998, w_bar 0.761, sd(x) 0.142, ACF(1) 0.9963 (the implied 188 d was that short pilot's sampling error and is withdrawn). Five 200,000-step pilots (v2.1 Phase 0): ACF(1) half-life 147 d (141–155 d); stationary sd(x) 0.165 (sd_e 0.016) / 0.175 (sd_e 0.017) with the engine's unit-mean innovation weight, 0.126 / 0.134 with raw weights (ratio 0.76 = w_bar). Sample half-life ≈ 20 d on 200-day windows, 62–72 d on T = 800 paths (estimator-biased). Source: CAL (no accepted SMM estimate): FW 2012 functional form with phi set for a 150-day pull-rate half-life at the realised fundamentalist share n_bar = 0.998; see DECISION_LOG.md row 2
- GJR-GARCH-t: alpha 0.1, gamma 0.1, beta 0.83 (persistence 0.980), sbar 0.017, df 5.0, panic multiplier 5.0, scale_mode variance; phase multipliers {'calm': 1.0, 'deterioration': 1.5, 'panic': 4.0, 'stabilisation': 1.5, 'mania': 1.5, 'blow-off': 2.0, 'post-top': 3.0, 'sustained-bull': 1.0} (the 0.25 used during E1 was reverted after review R1-D5; this line printed 0.25 until v2.1 Phase 0).
- Jumps: on, rate 0.01/day, N(-0.04, 0.03). Sentiment b_pred 0.0008, reversal 0.0006.
- Bubble: g0 0.002, kappa ~ U(0.02, 0.04), g_max 0.012, hazard h0 0.0003, b 6.0 (60-seed calibration: topped 0.47, topped peak P/V median 2.12).
- Burn-in 260 d; rejection up to 50 attempts.

## 2. Section 9 checklist (50 seeds per scenario, crash per delta, T = 200; final calibration incl. sustained-bull variance x1.0; item 10 on the event window, A7)

n per item is the last column: 470 pooled paths for the pooled items; items 4 and 9 use the 20 T = 800 paths (not 50 seeds); items 14 and 16 come from the Section 5 audit (150 of 400 paths after `MAX_ROWS` subsampling); 8 pass / 7 fail / 5 n-a of 20 rows. Items 9 and 11 are calibration targets and pass by construction; item 9's 72 d is the estimator-biased sample half-life (v2.1 Phase 0).
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

## 4. Section 5 audit (50 seeds -> 400 paths, 150 kept after `MAX_ROWS` subsampling = 30,000 steps; `leakage_audit_v2.md`; re-run in v2.1 Phase 0 on the frozen state after the analyst fix)
### L1 algebraic inversion (A6 rule) -- PASS
| candidate | fitted_k | median_APE | max_APE | share_APE_above_floor | sign_acc_PE15_rule | pass |
|---|---|---|---|---|---|---|
| k * analyst_fair_value | 0.9930 | 0.1008 | 0.5219 | 0.9518 | 0.6872 | True |
| k * P (price itself) | 1.0506 | 0.1236 | 2.3639 | 0.9592 | 0.6872 | True |
| k * P / reported_PE | 17.5239 | 0.1546 | 0.7136 | 0.9717 | 0.6872 | True |
| k * P * dividend_yield | 0.5019 | 0.1558 | 0.7224 | 0.9706 | 0.6872 | True |
Before the analyst fix the k·analyst candidate had median APE 0.2235 (the field's own sd was 0.335 by the sqrt(5) defect); after it, 0.1008 — the analyst field now beats price itself (0.1236), so the earlier statement "no formula beats price itself" no longer holds (the A6 rule passes by 0.26 pp: the candidate is inside the 1 % floor on 4.8 % of steps vs price's 4.1 % + 1 pp; on the 8-seed CI panel it is 6.4 % vs 3.6 % and the rule FAILS — `tests/test_leakage_ci.py::test_v2_L1_no_algebraic_inversion` is a registered known defect, decision P0-14; the rule is re-derived in Phase 6). The three-term mean of k·SMA50, k·P/PE and k·analyst reaches a median APE of 0.071 on the Phase-0 panel (`generated/v2_1/findings_reproduction.md`, block R5).
### L2 surrogate, best models (held-out seeds) -- pre-registered absolute thresholds are the gate: FAIL (calm R2(x) 0.92, sign 0.97, event 0.97, MAPE(V) 4.5%); exploratory selectivity of non-price fields +0.13 R2 / +3.2%; shuffled-V -0.06
| target | phase_group | n | R2 | sign_acc_resolvable | MAPE_V | R2_price_only | selectivity_R2 | R2_shuffledV |
|---|---|---|---|---|---|---|---|---|
| x | calm | 11700 | 0.918 | 0.974 | nan | 0.787 | 0.131 | -0.295 |
| x | event | 9239 | 0.966 | 0.980 | nan | 0.926 | 0.040 | -0.263 |
| x | resolution | 6061 | 0.948 | 0.989 | nan | 0.872 | 0.076 | -0.196 |
| x | all | 27000 | 0.954 | 0.980 | nan | 0.892 | 0.062 | -0.247 |
| logV | calm | 11700 | 0.842 | nan | 0.032 | 0.634 | 0.208 | -0.168 |
| logV | event | 9239 | 0.746 | nan | 0.045 | 0.425 | 0.321 | -0.236 |
| logV | resolution | 6061 | 0.746 | nan | 0.048 | 0.353 | 0.393 | -0.232 |
| logV | all | 27000 | 0.860 | nan | 0.040 | 0.670 | 0.191 | -0.194 |
Interpretation (corrected in v2.1 Phase 0; before: "fails by construction, hidden from the fields, not from price dynamics"): the price-only strength is the fixed start price V_1 = P_1 = 100 acting as an answer key — a level-free reader reaches R2(x) 0.49 (sign 0.74) instead of 0.85 (0.95), and with the start price randomised the non-price fields add ≈ +0.6 R2 in calm (block R3 of the findings file; reviews C.2–C.3). Phase 1 removes the anchor and re-runs this audit with a level-free control; Phase 5 redesigns the fields; Phase 6 derives the gate.
### L2b composite phase clock -- PASS: full 85.2% vs price-only 78.3% (day-only 54.6%, majority 43.3%), selectivity +6.9 pp (margin 10 pp). A 4-class accuracy cannot see a change-point leak: log IV jumps ×1.85 on the first panic day (z = 7.7; weakness item 46).
### Scenario discrimination (review R1-D5; reported, no threshold): sustained-bull vs mania vs calm days, n = 13,320 (majority 46%): accuracy price-only 75.3%, price+IV 78.0%, full 78.8%; recall of sustained-bull days 82.5% / 82.1% / 85.1% -- the control is identifiable from PRICE DYNAMICS (a selected quiet sub-population with anchored x; weakness items 18, 42), not from IV specifically.
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
| `fw_index` (FW 2012 index parameters, half-life ≈ 610 d) | 8 / 7 | the plan's index-parameter sensitivity |
| `pruna` (Pruna et al. 2016) | 7 / 8 | |
| `fw_hl60` (60-day stationary half-life) | 7 / 8 | short-persistence bracket |
| `scale_mode = omega` (plan-literal omega multipliers) | 7 / 8 | cannot reach the panic targets (A3) |
| panic multiplier 3 | 9 / 6 | sensitivity range 3-6 |
| panic multiplier 6 | 8 / 7 | |
Counts are pass / fail of the 15 applicable rows, read from the CSVs (v2.1 Phase 0 corrected five footers that disagreed with their own tables: the counts above are the corrected ones; weakness item 39). At 25 seeds the margin items (2, 6, 7, 8, 13) flip between variants at random, so "stable across variants" is not a supported statement. Items 9 and 11 are calibration targets (phi; hazard/cap) and pass by construction; the sustained-bull control runs at
variance multiplier 1.0 (review R1-D5) and its rejection rate (39.8 % at 50 seeds) is published.

## 6. Sensitivities still to run (E6)
cost tier and visibility, ISFJ target, delta set, k range, start design, action interface, field order, horizon
disclosure (harness factors exist; LLM runs pending); FW index parameters and `scale_mode='omega'` as generator
sensitivities (flags exist). Single-stock SMM attempted on real data and rejected (J = 408; DECISION_LOG row 2 note). J-profile over phi (`fw_J_profile.csv`, other parameters at the index set, scale-free diagonal weights): J ranges 2.9-3.2 over phi in [0.03, 2.0] -- the nine FW return-moments are flat in the mispricing persistence, i.e. not identified.

## 7. L5 observables oracle (`generated/l5_observables_oracle.md`)
GBT on the rendered fields (+5 lags), training seeds 500-511, evaluated on seeds 0-9 (**10 evaluation seeds, no intervals** — weakness item 43; re-run in v2.1 Phase 0 after the analyst fix): per-phase OOS R2 of x_hat = 0.95 / 0.97 / 0.93 (calm / event / resolution) for the full field set and 0.90 / 0.91 / 0.80 for price-and-technicals only. The gap (MCR of the L5 policy minus MCR of the true-V mandate-conditional oracle, theta 0.05) is 0.018-0.019 in bull-trap and crash, 0.031-0.032 in flat and 0.085-0.086 in sustained bull for the full set (before the analyst fix: 0.019 / 0.019 / 0.041-0.042 / 0.071-0.072), and 0.026-0.027 / 0.037-0.038 / 0.078-0.080 for price-only (unchanged by the fix). **Reading (corrected in v2.1 Phase 0):** this policy is trained across seeds on fields that include the price LEVEL, and every run starts at V_1 = P_1 = 100, so it learns the start-price anchor (weakness items 1, 43): a level-free reader reaches sign accuracy 0.74 on resolvable steps instead of 0.95 (`generated/v2_1/findings_reproduction.md`, block R3), and a two-line rule that compares the price with 100 already reaches MCR 0.009-0.018 in flat, crash and bull-trap. The earlier sentence "the environment withholds the level of value, not the direction of mispricing" is withdrawn: the level of V is recoverable to ~4-5 % MAPE by a fitted model, and the direction is recoverable through the anchor. What a level-free reader can infer is Phase 1's question (E1.6, the Kalman bound of the plan's Appendix B), and the L5 oracle is re-specified level-free there.
