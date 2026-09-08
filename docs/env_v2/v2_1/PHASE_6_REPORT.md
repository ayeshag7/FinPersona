# Phase 6 report — audits and checklist methodology: the gates, derived not stated (v2.1)

*Written as results land (execution prompt, "Documentation"); every number cites the file it comes from; the tables
marked `<!-- table:... -->` are generated from those files by `tools/phase6/e6_report_tables.py` and read back by
`tests/test_v2_1_phase_6.py::test_phase6_report_tables_match_files`. Sections follow the protocol's six headings.*

**Status: IN PROGRESS (9 September 2026).** Pre-registration written (`PREREG_PHASE_6.md`, three cells pending on
the nulls and one on the n = 500 size row); the diagnostic experiments done on the laptop; the lab box being
brought up as the reference machine for the sklearn stages (section 0); no gated run yet.

---

## 0. Current state, and how to read this report

| item | status |
|---|---|
| Pre-registration | `PREREG_PHASE_6.md`, written before any gated run, after the diagnostic runs it discloses in its section 2; the criteria in final form; three cells to be filled from files (the n = 500 size row, the L2 and L2b null locations) |
| Team decisions | **D2 undecided** (L3 built, not run); **D10 undecided** (audits on `shown`); **D15 not taken** (A deployed); θ = 0.05 for 16A with the plan's sensitivity set; D17 to be laid out after 16A |
| E6.9 known answers | **done** — 30 cases; 18 pass / 3 fail / 9 reported; the three failures are estimator properties (Hill at a 5 % depth, the sample kurtosis of a heavy tail, the JB size at 400 reps — the 2,000-rep re-check passes); item 3's rules have 23–28 % power against the generator's own shape at T = 200 |
| E6.1 reference | **done** — 12,927 windows of 417 names (31 each, four sub-periods), 0 errors; IV block 166 windows (VIX vs the FF market, the S&P 500, a set-A proxy; five single-stock IV indices) |
| E6.3 pilot | **done** on the stored 1,600-path panel; Appendix A's per-item n and the verdict decidability at 200 |
| E6.2 criteria | **done** on the stored panel: A/B/C per item and population, the size and power of B and C on known-answer panels (B has no size at n = 200; C no power against D = 0.10), the concordance table; `evaluation/params/phase6_criteria.json` written with a loud loader |
| E6.5 floor | **done** — the derived 5 % ceiling 0.606 + 0.011 = 0.617; price itself 0.426; the best of 27 extended candidates 0.399; expected PASS |
| E6.6 bound / sweep / ladder | **done** — bound 0.177 / 0.200 at the adopted parameters; 40 of 40 sweep points valid; the ladder attributes the calm channel: process stack 0.20, feedback +0.001, events' pre-event calm +0.069 |
| E6.6 / E6.7 nulls | **running** — 9 of 80 L2 fits done on the laptop before the laptop runs were stopped; resumed on the box once its reference rows reproduce |
| The switches | **written** — `run_audit(gates=, holdout_scenario=)`, `run_checklist_reference`, `evaluation/reference_stats.py`, `evaluation/criteria.py`; inertness test in `tests/test_v2_1_phase_6.py` |
| Final checklist (500 seeds), final audit (derived gates), held-out split, L3, 16A | **not run** |
| Compute | laptop for everything so far; the box (128 cores) reached by the per-file `raw.githubusercontent.com` route through Fan's proxy after the tarball and `git clone` routes failed on the proxy's cuts (`docs/COMPUTE_GPU_ACCESS.md`) |

---

## 1. Literature review and the citation table

*(to be completed with the report: Cont 2001; Ratliff-Crain et al. 2025; Hashimoto et al. 2025 Table 3 and TwinMarket
2025 Table 4 as the reference-table precedents; Vyetrenko et al. 2020; Hewitt & Liang 2019 for selectivity; Gururangan
et al. 2018; Kaufman et al. 2012; Harvey 1989 for the steady-state Kalman filter behind Appendix B. Every statistic
carries "(read at source)" or "(to verify)"; a "(to verify)" statistic appears in no parameter file, tolerance or slide.)*

---

## 2. Pre-registration, verification of the inherited numbers, and corrections

`tools/phase6/prereg_verify.py` → `e6_0/verify.md`: **59 rows, 0 mismatches**. Two accessor errors were the tool's
(the "+0.026 the fields add" is FULL − BASE, not the sum of per-group add-ones, 0.0198; the onset verdict's key is
`all_pass`); the record was right both times.

Corrections made to this phase's own instruments before their numbers were used, each disclosed in the tool's notes:
E6.9's `mdd_deterministic` case needed a floating-point floor (a deterministic statistic has an MCSE at machine
precision, so a pure z-test can never pass an exact answer); its `garch_persistence_block_in_force` case was first
given the target α + β, then α + γ/2 + β, and is finally *reported* (a symmetric QMLE on a GJR process has no exact
closed form); E6.3's decidability rule was made two-fold (Appendix A's design n, and whether the verdict on this
state is decidable at the planned n — an item observed at 0.95 against p0 = 0.80 is decidable at any n whatever the
5-pp design formula says); E6.1's per-ticker cache was added for resumability (rule 14).

---

## 3. Experiments and results

### 3.1 E6.9 — known-answer tests (`e6_9/known_answers.{json,md}`)

<!-- table:e6_9 -->
| case | statistic | target | T = 200 median [P10, P90] | long-T mean | verdict |
|---|---|---|---|---|---|
| `acf_ar1_phi0.6_lag1` | acf(r, 1) | 0.6000 | 0.5890 [0.5119, 0.6561] | 0.6003 | pass |
| `acf_ar1_phi0.9_lag5` | acf(r, 5) | 0.5905 | 0.5223 [0.3459, 0.6698] | 0.5905 | pass |
| `acf_ar1_engine_persistence_lag1` | acf(x, 1) on the engine's persistence | 0.9695 | 0.9468 [0.9061, 0.9684] | 0.9694 | pass |
| `half_life_ar1_engine` | half-life from ACF(1) | 22.3809 | 12.6905 [7.0268, 21.6032] | 22.3528 | pass |
| `sd_ar1_engine` | sd(x) | 4.0804 | 3.3476 [2.4205, 4.4998] | 4.0799 | pass |
| `acf_logvolume_ar1` | acf(log volume, 1) | 0.6500 | 0.6390 [0.5613, 0.7008] | 0.6503 | pass |
| `kurtosis_t5` | scipy kurtosis (excess) | 6.0000 | 1.7717 [0.5778, 6.0027] | 5.0708 | fail |
| `kurtosis_normal` | scipy kurtosis (excess) | 0.0000 | -0.0495 [-0.4213, 0.4766] | -0.0019 | pass |
| `skew_normal` | scipy skew | 0.0000 | -0.0003 [-0.2373, 0.2350] | -0.0004 | pass |
| `hill_pareto_alpha3` | hill_index(r, 0.05) | 3.0000 | 3.1720 [2.1694, 4.8271] | 3.0009 | pass |
| `hill_t4` | hill_index(r, 0.05) | 4.0000 | 3.2125 [2.2671, 5.0368] | 3.1973 | fail |
| `garch_persistence` | garch_fit -> alpha + beta | 0.9800 | 0.9627 [0.7021, 0.9956] | 0.9795 | pass |
| `garch_alpha` | garch_fit -> alpha | 0.0800 | 0.0650 [0.0000, 0.1488] | 0.0797 | pass |
| `gjr_gamma` | garch_fit(o=1) -> gamma | 0.1000 | 0.0981 [-0.0000, 0.2162] | 0.1001 | pass |
| `leverage_corr_symmetric` | corr(r_t, |r_t+1|) | 0.0000 | -0.0047 [-0.1055, 0.1115] | -0.0004 | pass |
| `leverage_corr_gjr` | corr(r_t, |r_t+1|) | — | -0.0403 [-0.1356, 0.0770] | -0.0439 | reported |
| `mdd_deterministic` | mdd(price) | -0.4000 | -0.4000 [-0.4000, -0.4000] | -0.4000 | pass |
| `ljung_box_size_iid` | ljung_box_p(r, 10) > 0.05 | nominal 0.050 | rejection 0.0625 [0.043, 0.091] | 0.0575 | pass |
| `ljung_box_power_ar1_015` | ljung_box_p(r, 10) < 0.05 | nominal — | rejection 0.2725 [0.231, 0.318] | 1.0000 | reported |
| `arch_lm_size_iid` | arch_lm_p(r, 5) < 0.01 | nominal 0.010 | rejection 0.0125 [0.005, 0.029] | 0.0075 | pass |
| `arch_lm_power_garch` | arch_lm_p(r, 5) < 0.01 | nominal — | rejection 0.3400 [0.295, 0.388] | 1.0000 | reported |
| `lb_abs_r_power_garch` | ljung_box_p(|r|, 10) < 0.01 | nominal — | rejection 0.4000 [0.353, 0.449] | 1.0000 | reported |
| `shapiro_size_normal` | shapiro(log v) < 0.01 | nominal 0.010 | rejection 0.0150 [0.007, 0.032] | 0.0075 | pass |
| `jarque_bera_size_normal` | jarque_bera(r) < 0.05 | nominal 0.050 | rejection 0.0425 [0.027, 0.067] | 0.0725 | fail |
| `jarque_bera_power_t5` | jarque_bera(r) < 0.05 | nominal — | rejection 0.8525 [0.814, 0.884] | 1.0000 | reported |
| `arch_lm_power_block_in_force` | arch_lm_p(r, 5) < 0.01 | nominal — | rejection 0.2325 [0.194, 0.276] | 1.0000 | reported |
| `lb_abs_r_power_block_in_force` | ljung_box_p(|r|, 10) < 0.01 | nominal — | rejection 0.2750 [0.234, 0.321] | 1.0000 | reported |
| `acf1_absr_block_in_force` | acf(|r|, 1) | — | 0.0570 [-0.0308, 0.1861] | 0.1585 | reported |
| `jarque_bera_size_normal_recheck` | jarque_bera(r) < 0.05 | nominal 0.050 | rejection 0.0495 [0.041, 0.060] | 0.0570 | pass |
| `garch_persistence_block_in_force` | garch_fit -> alpha + beta | 0.9880 | 0.9662 [0.7239, 0.9986] | 0.9872 | reported |

30 cases: 18 pass / 3 fail / 9 reported (no closed form); 400 reps (GARCH 200), root seed 20260908.
<!-- /table:e6_9 -->

Reading. The estimators are correct where a closed form exists (the Pareto Hill, AR(1) ACFs, GARCH and GJR
coefficients at the long horizon, deterministic MDD, the nominal sizes of LB, ARCH-LM, Shapiro and JB). Three
findings decide how the criteria must be written: the sample ACF(1) at the engine's FIT half-life reads 0.947
[0.906, 0.968] on 200 days for a true 0.9695 (the implied half-life 12.7 d for 22.4 d); the sample kurtosis of a
Student-t(5) has a T = 200 median of 1.77 for a true 6.0 and no usable distribution even at T = 20,000; the Hill
index at the audit's 5 % depth reads 3.19 for a true 4.0 while the Pareto control is exact. And the power rows:
against the generator's own fitted GJR shape, ARCH-LM(5) rejects at 1 % in 23 % of 200-day windows and LB\|r\| in
28 %, with a median ACF\|r\|(1) of 0.057 — item 3's "≥ 80 % of seeds" and "0.10–0.40" ask for what the true process
cannot show at T = 200.

### 3.2 E6.1 — the reference distributions (`e6_1/reference.{json,md}`, `e6_1/iv_reference.md`)

<!-- table:e6_1 -->
12,927 windows of 417 names (T = 200); sub-periods 2000-07 4,170, 2008-12 2,502, 2013-19 3,753, 2020-24 2,502; 0 errors.

| statistic | n | P10 | P50 | P90 | P50 2000-07 | P50 2008-12 | P50 2013-19 | P50 2020-24 |
|---|---|---|---|---|---|---|---|---|
| `lb_p_r` | 12,927 | 0.02367 | 0.3923 | 0.8666 | 0.3789 | 0.309 | 0.4445 | 0.4229 |
| `abs_acf1_r` | 12,927 | 0.01105 | 0.05852 | 0.1511 | 0.06225 | 0.06609 | 0.05204 | 0.05702 |
| `kurtosis` | 12,927 | 0.4665 | 2.173 | 10.74 | 1.951 | 1.811 | 2.581 | 2.72 |
| `hill` | 12,927 | 2.308 | 3.556 | 5.572 | 3.654 | 3.777 | 3.393 | 3.406 |
| `jb_p` | 12,927 | 1.015e-223 | 8.24e-11 | 0.1905 | 7.522e-09 | 1.533e-07 | 8.596e-15 | 1.072e-15 |
| `lb_p_absr` | 12,927 | 3.697e-07 | 0.1823 | 0.8354 | 0.2018 | 0.04372 | 0.2303 | 0.2396 |
| `arch_lm_p` | 12,927 | 0.0001547 | 0.395 | 0.9824 | 0.3987 | 0.1897 | 0.5495 | 0.402 |
| `acf1_absr` | 12,927 | -0.02559 | 0.08726 | 0.2321 | 0.08884 | 0.07672 | 0.091 | 0.08791 |
| `garch_persistence` | 12,927 | 0.2893 | 0.9298 | 1 | 0.9162 | 0.9693 | 0.9031 | 0.9124 |
| `garch_alpha` | 12,927 | 0 | 0.05795 | 0.2699 | 0.06078 | 0.03896 | 0.05864 | 0.07277 |
| `gjr_gamma` | 12,927 | -0.1008 | 0.05979 | 0.3353 | 0.05609 | 0.06438 | 0.06201 | 0.05612 |
| `leverage_corr` | 12,927 | -0.1472 | -0.03808 | 0.06983 | -0.02524 | -0.05442 | -0.04112 | -0.03681 |
| `volume_absr_spearman` | 12,927 | 0.1869 | 0.3256 | 0.4596 | 0.3028 | 0.3411 | 0.3372 | 0.3302 |
| `logvolume_acf1` | 12,927 | 0.3728 | 0.5084 | 0.642 | 0.4756 | 0.5441 | 0.5102 | 0.5207 |
| `logvolume_shapiro_p` | 12,927 | 2.227e-07 | 0.003695 | 0.4219 | 0.008697 | 0.005251 | 0.002594 | 0.0009817 |
| `skew` | 12,927 | -1.044 | -0.06929 | 0.7473 | 0.05444 | -0.02749 | -0.2076 | -0.1563 |
| `worst_over_best` | 12,927 | 0.5711 | 1.031 | 1.851 | 0.975 | 1.011 | 1.081 | 1.07 |
| `mdd` | 12,927 | -0.4363 | -0.1955 | -0.09651 | -0.2001 | -0.236 | -0.1545 | -0.2263 |
| `daily_sigma` | 12,927 | 0.01076 | 0.01747 | 0.03411 | 0.01898 | 0.02131 | 0.014 | 0.01957 |
| `worst_day` | 12,927 | -0.1555 | -0.06516 | -0.03464 | -0.06766 | -0.07689 | -0.05358 | -0.07392 |

IV block (`e6_1/iv_reference.md`):

| pair | n | IV mean P10 / P50 / P90 | corr(IV, next-20d RV) P50 | IV − RV20 P50 |
|---|---|---|---|---|
| index:VIX vs FF value-weighted US market (1990-) | 33 | 13.1 / 18.6 / 25.4 | 0.44 | +3.13 |
| index:VIX vs S&P 500 (FRED, 2016-) | 12 | 12.9 / 17.5 / 25.3 | 0.41 | +3.53 |
| index:VIX vs set-A equal-weight proxy (2000-2024) | 31 | 13.0 / 18.6 / 25.4 | 0.47 | +3.17 |
| single:VXAPL vs AAPL | 18 | 24.0 / 29.3 / 37.0 | 0.50 | +4.50 |
| single:VXAZN vs AMZN | 18 | 28.5 / 33.0 / 39.9 | 0.68 | +4.92 |
| single:VXGOG vs GOOG | 18 | 22.4 / 26.8 / 33.5 | 0.59 | +3.19 |
| single:VXGS vs GS | 18 | 23.7 / 27.9 / 38.3 | 0.33 | +4.95 |
| single:VXIBM vs IBM | 18 | 19.7 / 23.3 / 28.8 | 0.54 | +3.51 |
| single:pooled | 90 | 21.6 / 28.4 / 37.6 | 0.55 | +4.14 |
<!-- /table:e6_1 -->

Survivorship (REG-15): set A is survivor-biased by construction; tails, drawdowns and loss frequencies understated;
per-item reading in `PREREG_PHASE_6.md` section 3.

### 3.3 E6.3 — the power analysis (`e6_3/power_v2.md`)

<!-- table:e6_3 -->
Pilot `docs/env_v2/generated/v2_1/_panels/sep_phase5_after.pkl` (1600 paths: bull_trap 400, crash 800, flat 200, sustained_bull 200); planned n = 200.

| criterion | item | kind | pilot n | observed | n required | decidable at planned n |
|---|---|---|---|---|---|---|
| `item1_lb_p_share` | 1 | share | 1000 | share 0.951 | 419 | yes |
| `item1_abs_acf1` | 1 | band | 1000 | median 0.06204 | 9 | yes |
| `item2_kurt_share` | 2 | share | 1600 | share 0.560 | 21 | yes |
| `item2_hill` | 2 | band | 1600 | median 3.844 | 54 | yes |
| `item3_lb_absr_share` | 3 | share | 1600 | share 0.463 | 11 | yes |
| `item3_acf1_absr` | 3 | band | 1600 | median 0.09141 | 25 | no |
| `item5_persistence` | 5 | band | 1600 | median 0.9747 | 754 | no |
| `item6_lev_share` | 6 | share | 1600 | share 0.610 | 168 | yes |
| `item6_gamma` | 6 | band | 1600 | median 0.05911 | 85 | yes |
| `item7_spearman` | 7 | band | 1600 | median 0.3251 | 13 | yes |
| `item7_logvol_ac1` | 7 | band | 1600 | median 0.5539 | 9 | yes |
| `item7_shapiro_share` | 7 | share | 1600 | share 0.752 | 617 | yes |
| `item8_skew` | 8 | band | 800 | median 0.04011 | 2028 | no |
| `item8_worst_share` | 8 | share | 800 | share 0.501 | 35 | yes |
| `item9_acf1_x` | 9 | band | 1000 | median 0.9203 | 8 | yes |
| `item9_sd_x` | 9 | band | 1000 | median 0.03854 | 5 | yes |
| `item12_sent_acf1` | 12 | band | 1600 | median 0.2034 | 18 | yes |
| `item12_sent_corr` | 12 | band | 1600 | median 0.01736 | 9 | yes |
| `item13_iv_calm` | 13 | band | 1249 | median 32.36 | 88 | yes |
| `item13_iv_rv_corr` | 13 | band | 1600 | median 0.2295 | 99 | yes |
| `item20_mdd` | 20 | band | 800 | median -0.5122 | 7 | yes |
| `item20_calm_sigma` | 20 | band | 200 | median 0.01988 | 39 | yes |
| `item20_worst_panic` | 20 | band | 800 | median -0.1245 | 84 | yes |
<!-- /table:e6_3 -->

### 3.4 E6.2 — the criteria, their size and power, the concordance (`e6_2/criteria.md`)

<!-- table:e6_2 -->
| item | statistic | pop | n_gen / n_ref | gen P50 | ref P50 | B: D (upper) | B | C: share (thr) | C | A (v2) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `lb_p_r` | all | 1600 / 12927 | 0.322 | 0.392 | 0.076 (0.098) | PASS | 0.756 (0.780) | FAIL | PASS |
| 1 | `abs_acf1_r` | all | 1600 / 12927 | 0.0561 | 0.0585 | 0.031 (0.055) | PASS | 0.807 (0.780) | PASS | PASS |
| 2 | `kurtosis` | all | 1600 / 12927 | 1.73 | 2.17 | 0.101 (0.127) | FAIL | 0.811 (0.780) | PASS | FAIL |
| 2 | `hill` | all | 1600 / 12927 | 3.84 | 3.56 | 0.101 (0.126) | FAIL | 0.821 (0.780) | PASS | FAIL |
| 2 | `jb_p` | all | 1600 / 12927 | 8.3e-07 | 8.24e-11 | 0.111 (0.134) | FAIL | 0.800 (0.780) | PASS | FAIL |
| 3 | `lb_p_absr` | all | 1600 / 12927 | 0.0302 | 0.182 | 0.224 (0.248) | FAIL | 0.621 (0.780) | FAIL | FAIL |
| 3 | `lb_p_r2` | all | 1600 / 12927 | 0.116 | 0.447 | 0.167 (0.193) | FAIL | 0.734 (0.780) | FAIL | FAIL |
| 3 | `arch_lm_p` | all | 1600 / 12927 | 0.223 | 0.395 | 0.095 (0.118) | FAIL | 0.793 (0.780) | PASS | FAIL |
| 3 | `acf1_absr` | all | 1600 / 12927 | 0.0914 | 0.0873 | 0.094 (0.116) | FAIL | 0.698 (0.780) | FAIL | FAIL |
| 4 | `acf1_absr` | all | 1600 / 12927 | 0.0914 | 0.0873 | 0.094 (0.116) | FAIL | 0.698 (0.780) | FAIL | n/a |
| 4 | `acf5_absr` | all | 1600 / 12927 | 0.0768 | 0.0427 | 0.165 (0.188) | FAIL | 0.672 (0.780) | FAIL | n/a |
| 4 | `acf10_absr` | all | 1600 / 12927 | 0.0612 | 0.0291 | 0.163 (0.187) | FAIL | 0.691 (0.780) | FAIL | n/a |
| 4 | `acf20_absr` | all | 1600 / 12927 | 0.0386 | 0.00948 | 0.178 (0.201) | FAIL | 0.703 (0.780) | FAIL | n/a |
| 4 | `acf50_absr` | all | 1600 / 12927 | -0.0146 | -0.00898 | 0.051 (0.076) | PASS | 0.771 (0.780) | FAIL | n/a |
| 5 | `garch_persistence` | all | 1600 / 12927 | 0.975 | 0.93 | 0.222 (0.246) | FAIL | 0.768 (0.780) | FAIL | PASS |
| 5 | `garch_alpha` | all | 1600 / 12927 | 0.0647 | 0.0579 | 0.084 (0.097) | PASS | 0.958 (0.780) | PASS | PASS |
| 5 | `garch_beta` | all | 1600 / 12927 | 0.883 | 0.825 | 0.196 (0.218) | FAIL | 0.852 (0.780) | PASS | PASS |
| 6 | `leverage_corr` | all | 1600 / 12927 | -0.0224 | -0.0381 | 0.080 (0.104) | FAIL | 0.805 (0.780) | PASS | FAIL |
| 6 | `gjr_gamma` | all | 1600 / 12927 | 0.0591 | 0.0598 | 0.092 (0.113) | FAIL | 0.888 (0.780) | PASS | FAIL |
| 7 | `volume_absr_spearman` | all | 1600 / 12927 | 0.325 | 0.326 | 0.052 (0.073) | PASS | 0.885 (0.780) | PASS | PASS |
| 7 | `logvolume_acf1` | all | 1600 / 12927 | 0.554 | 0.508 | 0.254 (0.274) | FAIL | 0.871 (0.780) | PASS | PASS |
| 7 | `logvolume_shapiro_p` | all | 1600 / 12927 | 0.203 | 0.0037 | 0.375 (0.399) | FAIL | 0.663 (0.780) | FAIL | PASS |
| 8 | `skew` | crash | 800 / 6275 | 0.0401 | -0.135 | 0.142 (0.176) | FAIL | 0.866 (0.772) | PASS | FAIL |
| 8 | `worst_over_best` | crash | 800 / 6275 | 1 | 1.11 | 0.129 (0.163) | FAIL | 0.858 (0.772) | PASS | FAIL |
| 20 | `mdd` | crash | 800 / 6275 | -0.512 | -0.307 | 0.623 (0.643) | FAIL | 0.613 (0.772) | FAIL | PASS |
| 20 | `worst_day` | crash | 800 / 6275 | -0.137 | -0.0944 | 0.407 (0.430) | FAIL | 0.825 (0.772) | PASS | PASS |
| 20 | `daily_sigma` | flat | 200 / 12927 | 0.0199 | 0.0175 | 0.436 (0.449) | FAIL | 0.990 (0.745) | PASS | PASS |

Size and power (pass rates of B / C at true D = 0, 0.05, 0.10):

| item | statistic | n = 200: D0 / D.05 / D.10 | n = 800: D0 / D.05 / D.10 |
|---|---|---|---|
| 1 | `lb_p_r` | 0.02 0.99 / 0.05 1.00 / 0.00 1.00 | 1.00 0.97 / 1.00 0.99 / 0.00 1.00 |
| 1 | `abs_acf1_r` | 0.03 0.96 / 0.02 1.00 / 0.00 1.00 | 1.00 0.97 / 0.80 1.00 / 0.00 1.00 |
| 2 | `kurtosis` | 0.08 1.00 / 0.03 1.00 / 0.00 1.00 | 0.99 0.96 / 0.88 1.00 / 0.01 1.00 |
| 2 | `hill` | 0.04 0.98 / 0.02 1.00 / 0.00 1.00 | 1.00 0.96 / 0.70 1.00 / 0.00 1.00 |
| 2 | `jb_p` | 0.07 0.96 / 0.00 1.00 / 0.00 1.00 | 1.00 0.93 / 0.00 1.00 / 0.00 1.00 |
| 3 | `lb_p_absr` | 0.07 0.96 / 0.05 0.97 / 0.00 1.00 | 0.99 0.98 / 1.00 1.00 / 0.00 1.00 |
| 3 | `lb_p_r2` | 0.06 0.97 / 0.06 0.97 / 0.00 1.00 | 1.00 0.99 / 1.00 0.96 / 0.00 1.00 |
| 3 | `arch_lm_p` | 0.02 0.98 / 0.08 1.00 / 0.00 1.00 | 1.00 0.99 / 1.00 0.96 / 0.00 1.00 |
| 3 | `acf1_absr` | 0.00 0.96 / 0.02 1.00 / 0.00 1.00 | 0.99 0.98 / 0.63 1.00 / 0.00 1.00 |
| 4 | `acf1_absr` | 0.03 0.94 / 0.03 0.99 / 0.00 1.00 | 1.00 0.98 / 0.73 1.00 / 0.00 1.00 |
| 4 | `acf5_absr` | 0.03 0.97 / 0.02 1.00 / 0.00 0.99 | 1.00 1.00 / 0.72 0.99 / 0.00 1.00 |
| 4 | `acf10_absr` | 0.07 0.96 / 0.03 0.96 / 0.00 0.98 | 1.00 0.97 / 0.68 0.99 / 0.00 0.98 |
| 4 | `acf20_absr` | 0.01 0.99 / 0.01 0.99 / 0.00 0.98 | 1.00 0.97 / 0.66 1.00 / 0.00 0.98 |
| 4 | `acf50_absr` | 0.05 0.97 / 0.03 0.97 / 0.00 0.96 | 1.00 0.98 / 0.58 0.99 / 0.01 0.96 |
| 5 | `garch_persistence` | 0.02 0.99 / 0.00 0.98 / 0.00 0.92 | 1.00 0.98 / 0.93 0.96 / 0.05 0.90 |
| 5 | `garch_alpha` | 0.08 1.00 / 0.00 1.00 / 0.00 1.00 | 0.98 1.00 / 0.00 1.00 / 0.00 1.00 |
| 5 | `garch_beta` | 0.04 0.98 / 0.02 0.97 / 0.00 0.96 | 1.00 0.98 / 0.98 0.98 / 0.00 0.99 |
| 6 | `leverage_corr` | 0.03 0.96 / 0.00 0.97 / 0.00 0.81 | 1.00 0.97 / 0.65 0.97 / 0.00 0.78 |
| 6 | `gjr_gamma` | 0.06 0.98 / 0.02 0.98 / 0.00 0.99 | 1.00 0.98 / 0.93 0.96 / 0.03 1.00 |
| 7 | `volume_absr_spearman` | 0.02 1.00 / 0.02 1.00 / 0.00 0.90 | 1.00 0.98 / 0.71 0.95 / 0.00 0.86 |
| 7 | `logvolume_acf1` | 0.03 0.97 / 0.00 0.96 / 0.00 0.94 | 1.00 1.00 / 0.68 0.97 / 0.01 0.82 |
| 7 | `logvolume_shapiro_p` | 0.03 0.98 / 0.05 1.00 / 0.00 1.00 | 1.00 0.98 / 1.00 0.98 / 0.00 1.00 |
| 8 | `skew` | 0.02 0.99 / 0.00 0.93 / 0.00 0.87 | 1.00 0.99 / 0.66 0.90 / 0.00 0.55 |
| 8 | `worst_over_best` | 0.08 1.00 / 0.02 0.99 / 0.00 1.00 | 1.00 0.99 / 0.65 1.00 / 0.01 1.00 |
| 20 | `mdd` | 0.03 0.98 / 0.01 0.71 / 0.00 0.22 | 1.00 1.00 / 0.81 0.13 / 0.01 0.00 |
| 20 | `worst_day` | 0.05 0.99 / 0.00 0.76 / 0.00 0.41 | 1.00 0.99 / 0.61 0.38 / 0.00 0.00 |
| 20 | `daily_sigma` | 0.07 1.00 / 0.01 1.00 / 0.00 1.00 | 1.00 0.98 / 0.74 1.00 / 0.00 1.00 |
<!-- /table:e6_2 -->

The finding that sets the seed policy: **B has no size at n_gen = 200** (a sample drawn from the reference passes
2–8 % of the time) and full size and power at 800; **C has size at every n but no power against a D = 0.10 shift**
on most statistics. B decides, at n ≥ its size threshold; C is the band report.

### 3.5 E6.5 — the L1 floor (`e6_5/floor.md`)

<!-- table:e6_5 -->
s_x = 0.0656; B (day 200) = 0.2005; ceiling at 5 % = 0.6060; half-width 0.0107; **margin 0.6167**; trivial line (generator) 0.426 [0.416, 0.437].

| candidate | within-5 % | passes the derived ceiling |
|---|---|---|
| k * P (price itself) (e5_after L1) | 0.426 | PASS |
| k * P * dividend_yield (e5_after L1) | 0.036 | PASS |
| k * P / reported_PE (e5_after L1) | 0.036 | PASS |
| k * analyst_fair_value (e5_after L1) | 0.030 | PASS |
| k*price (e5_7b/final l1ext) | 0.426 | PASS |
| k*P/PE (e5_7b/final l1ext) | 0.033 | PASS |
| k*P*DY (e5_7b/final l1ext) | 0.036 | PASS |
| k*F (e5_7b/final l1ext) | 0.030 | PASS |
| k*sqrt(price*P/PE) (e5_7b/final l1ext) | 0.072 | PASS |
| k*sqrt(price*P*DY) (e5_7b/final l1ext) | 0.074 | PASS |
| k*sqrt(price*F) (e5_7b/final l1ext) | 0.065 | PASS |
| lsq(price) (e5_7b/final l1ext) | 0.397 | PASS |
| lsq(P/PE) (e5_7b/final l1ext) | 0.206 | PASS |
| lsq(P*DY) (e5_7b/final l1ext) | 0.189 | PASS |
| lsq(F) (e5_7b/final l1ext) | 0.216 | PASS |
| lsq(price+P/PE) (e5_7b/final l1ext) | 0.376 | PASS |
| lsq(price+P*DY) (e5_7b/final l1ext) | 0.343 | PASS |
| lsq(price+F) (e5_7b/final l1ext) | 0.399 | PASS |
| lsq(P/PE+P*DY) (e5_7b/final l1ext) | 0.175 | PASS |
| lsq(P/PE+F) (e5_7b/final l1ext) | 0.201 | PASS |
| lsq(P*DY+F) (e5_7b/final l1ext) | 0.187 | PASS |
| lsq(price+P/PE+P*DY) (e5_7b/final l1ext) | 0.323 | PASS |
| lsq(price+P/PE+F) (e5_7b/final l1ext) | 0.377 | PASS |
| lsq(price+P*DY+F) (e5_7b/final l1ext) | 0.345 | PASS |
| lsq(P/PE+P*DY+F) (e5_7b/final l1ext) | 0.175 | PASS |
| median(valuation candidates) (e5_7b/final l1ext) | 0.043 | PASS |
| best = k*price (e5_7b/final l1ext (best)) | 0.426 | PASS |
<!-- /table:e6_5 -->

### 3.6 E6.6 — the bound, the sweep check and the ladder (`e6_6/bound.md`)

<!-- table:e6_6 -->
Adopted: σ_V = 0.014573, h = 22.38 d, s_x = 0.0656 (identity with the jumps); bound window average **0.1773**, day 200 **0.2005**, steady 0.2006. Sweep: 40 points, CI lower end above the window-average bound at 0, above the day-200 bound at 0.

| rung | arm | n | level-free R²(x) [CI] | bound (window) | increment |
|---|---|---|---|---|---|
| 1 | E3.8: exact (the bound's model) | 200 | 0.1453 [0.1076, 0.1759] | 0.1633 | — |
| 2 | E3.8: + GJR-t innovation (block in force) | 200 | 0.1454 [0.0962, 0.1838] | 0.1633 | +0.0001 |
| 3 | E3.8: + jumps (FIT lambda, sigma_J) | 200 | 0.1918 [0.1047, 0.2882] | 0.1773 | +0.0465 |
| 4 | E3.8: + GJR-t + jumps (the Phase-3 x innovation) | 200 | 0.2025 [0.1409, 0.2625] | 0.1773 | +0.0107 |
| 5 | generator flat, feedback OFF (b_pred = b_rev = 0) | 200 | 0.2204 [0.1599, 0.2801] | 0.1714 | +0.0179 |
| 6 | generator flat, as deployed (feedback ON) | 200 | 0.2217 [0.1611, 0.2813] | 0.1716 | +0.0014 |
| 7 | generator, every calm row of the SEP panel (flat + pre-event calm) | 1600 | 0.2912 [0.2637, 0.3179] | 0.1695 | +0.0694 |
<!-- /table:e6_6 -->

### 3.7 E6.6 / E6.7 — the nulls and the derived gates *(pending)*

### 3.8 E6.4, E6.8, the final checklist, the final audit, the held-out split *(pending)*

### 3.9 The switches, and the proof that they are inert when off

`run_audit(gates="v2", holdout_scenario=False)` is the pre-Phase-6 call and returns the pre-Phase-6 dictionary;
`gates="derived"` and `holdout_scenario=True` add keys (`derived`, `L2_holdout`) and change no existing value
(`test_audit_switches_inert`). `run_checklist` is untouched; `run_checklist_reference` is a separate entry point.
The estimator behind the reference criteria (`evaluation/reference_stats.window_stats`) reproduces E6.1's stored
rows to 1e-9 (`test_reference_stats_is_the_reference_estimator`).

---

## 4. Decisions taken and the parameter file *(in progress — DECISION_LOG P6-*)*

## 5. Decisions the team must take *(D2, D10, D15 open; D17 after 16A)*

## 6. Files written or changed *(`PHASE_6_CHANGED_FILES.md`, verified against disk at the end)*

## 7. What was not done, and who owns it
