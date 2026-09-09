# Calibration report — the E6 appendix (v2.1 Phase 6): the yardsticks, derived not stated

*Rewritten by v2.1 Phase 6 (plan Section 10.5). The 22 August 2026 E6 draft — the v2 parameters in force, the 50-seed
checklist under the v2 criteria, the hazard grid, the subsampled audit, the 25-seed sensitivities — is archived verbatim
at `spec/archive/CALIBRATION_REPORT_v2_E6_draft_22Aug2026.md`; its numbers are the "pre-amendment / v2" column of the
tuned-parameter ledger (`v2_1/PHASE_6_REPORT.md` section 3.10) and are not restated here. Every table below is generated
from the file it names by `tools/phase6/e6_report_tables.py` and read back by `tests/test_v2_1_phase_6.py`.*

**What this appendix is.** Phases 1–5 made every generator parameter FIT or tested on data. This appendix does the same
for the *criteria*: an empirical reference distribution from real 200-day windows for every checklist statistic, a
criterion form whose size and power were measured on known-answer panels before it was applied, a seed count from a
power analysis, and leakage gates derived from an analytic bound and from nulls simulated with the real estimator on the
real panel. The rules are registered in `v2_1/PREREG_PHASE_6.md`; nothing here was moved after a result was seen.

---

## 1. The reference distributions (E6.1; `generated/v2_1/e6_1/`)

Every non-overlapping 200-day window of every name in analysis set A, every statistic computed by the audit's own
functions (`evaluation/reference_stats.py`, the estimator the checklist applies to the generator). **Survivorship
(REG-15):** set A is survivor-biased by construction (a complete 2000–2024 history in a `yfinance` panel); tails,
drawdowns and loss frequencies are understated, most for items 2, 8 and 20 and least for items 1, 3, 5, 6, 7. The IV
block pairs the VIX with the Fama–French value-weighted market (no survivorship), the S&P 500 (FRED, ten years) and a
set-A proxy, and the five CBOE single-stock VIX indices with their stocks (five surviving mega-caps, a selected sample).

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

## 2. The known answers (E6.9; `generated/v2_1/e6_9/`)

Each statistic applied to a synthetic process whose value is known in closed form: convergence at a long horizon proves
the code; the T = 200 row measures the bias the benchmark horizon imposes. The Hill index at the audit's 5 % depth misses a
Student-t index by ≈ 20 % while the Pareto control is exact; the sample kurtosis of a Student-t(5) has no usable
finite-sample distribution; the sample ACF(1) of an AR(1) at the engine's FIT half-life reads 0.947 for 0.9695. Against the
generator's own fitted GJR shape, ARCH-LM(5) rejects at 1 % in 23 % of 200-day windows and LB\|r\| in 28 %. These are
properties of the rulers, and they fall on both sides of a like-for-like criterion — which is why the criteria below
compare the generator's windows with the real windows measured the same way rather than with absolute bands.

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

## 3. The criteria (E6.2; `generated/v2_1/e6_2/`; `evaluation/params/phase6_criteria.json`)

- **A (v2):** the numeric bands of `evaluation/stylized_facts.py`, unchanged, reported for continuity.
- **B (KS-equivalence):** the bootstrap 95 % upper limit of the two-sample KS distance between the generator's cross-seed
  distribution and the reference is **< 0.10**. "The KS test did not reject" is not a criterion.
- **C (band share):** the generator's share inside the reference P10–P90 is **≥ 0.80 − 1.96 √(0.8·0.2/n_gen)**.

Their measured size and power on known-answer panels (the generator sample replaced by a draw from the reference, and by
the reference shifted to a true KS distance of 0.05 and 0.10): **B has no size at n_gen = 200** and full size and power at
800; **C has size at every n but no power against a D = 0.10 shift on most statistics**. B decides, at n ≥ its size
threshold (`criterion_B.n_min_size` in the criteria file); C is the band report. The items without a real-window
counterpart (9, 11, 12, 13, 15, 17) are handled in `PREREG_PHASE_6.md` 5.4 (item 9 as fidelity to the FIT process
measured with the same 200-day ruler; item 12's lagged relation and item 13's non-degeneracy implemented for the first
time, weakness 64).

<!-- table:e6_2 -->
| item | statistic | pop | n_gen / n_ref | gen P50 | ref P50 | B: D (upper) | B | C: share (thr) | C | A (v2) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `lb_p_r` | all | 1600 / 12927 | 0.322 | 0.392 | 0.076 (0.098) | PASS | 0.756 (0.780) | FAIL | PASS |
| 1 | `abs_acf1_r` | all | 1600 / 12927 | 0.0561 | 0.0585 | 0.031 (0.058) | PASS | 0.807 (0.780) | PASS | PASS |
| 2 | `kurtosis` | all | 1600 / 12927 | 1.73 | 2.17 | 0.101 (0.128) | FAIL | 0.811 (0.780) | PASS | FAIL |
| 2 | `hill` | all | 1600 / 12927 | 3.84 | 3.56 | 0.101 (0.126) | FAIL | 0.821 (0.780) | PASS | FAIL |
| 2 | `jb_p` | all | 1600 / 12927 | 8.3e-07 | 8.24e-11 | 0.111 (0.136) | FAIL | 0.800 (0.780) | PASS | FAIL |
| 3 | `lb_p_absr` | all | 1600 / 12927 | 0.0302 | 0.182 | 0.224 (0.246) | FAIL | 0.621 (0.780) | FAIL | FAIL |
| 3 | `lb_p_r2` | all | 1600 / 12927 | 0.116 | 0.447 | 0.167 (0.194) | FAIL | 0.734 (0.780) | FAIL | FAIL |
| 3 | `arch_lm_p` | all | 1600 / 12927 | 0.223 | 0.395 | 0.095 (0.121) | FAIL | 0.793 (0.780) | PASS | FAIL |
| 3 | `acf1_absr` | all | 1600 / 12927 | 0.0914 | 0.0873 | 0.094 (0.117) | FAIL | 0.698 (0.780) | FAIL | FAIL |
| 4 | `acf1_absr` | all | 1600 / 12927 | 0.0914 | 0.0873 | 0.094 (0.116) | FAIL | 0.698 (0.780) | FAIL | n/a |
| 4 | `acf5_absr` | all | 1600 / 12927 | 0.0768 | 0.0427 | 0.165 (0.190) | FAIL | 0.672 (0.780) | FAIL | n/a |
| 4 | `acf10_absr` | all | 1600 / 12927 | 0.0612 | 0.0291 | 0.163 (0.188) | FAIL | 0.691 (0.780) | FAIL | n/a |
| 4 | `acf20_absr` | all | 1600 / 12927 | 0.0386 | 0.00948 | 0.178 (0.202) | FAIL | 0.703 (0.780) | FAIL | n/a |
| 4 | `acf50_absr` | all | 1600 / 12927 | -0.0146 | -0.00898 | 0.051 (0.076) | PASS | 0.771 (0.780) | FAIL | n/a |
| 5 | `garch_persistence` | all | 1600 / 12927 | 0.975 | 0.93 | 0.222 (0.245) | FAIL | 0.768 (0.780) | FAIL | PASS |
| 5 | `garch_alpha` | all | 1600 / 12927 | 0.0647 | 0.0579 | 0.084 (0.098) | PASS | 0.958 (0.780) | PASS | PASS |
| 5 | `garch_beta` | all | 1600 / 12927 | 0.883 | 0.825 | 0.196 (0.218) | FAIL | 0.852 (0.780) | PASS | PASS |
| 6 | `leverage_corr` | all | 1600 / 12927 | -0.0224 | -0.0381 | 0.080 (0.102) | FAIL | 0.805 (0.780) | PASS | FAIL |
| 6 | `gjr_gamma` | all | 1600 / 12927 | 0.0591 | 0.0598 | 0.092 (0.111) | FAIL | 0.888 (0.780) | PASS | FAIL |
| 7 | `volume_absr_spearman` | all | 1600 / 12927 | 0.325 | 0.326 | 0.052 (0.072) | PASS | 0.885 (0.780) | PASS | PASS |
| 7 | `logvolume_acf1` | all | 1600 / 12927 | 0.554 | 0.508 | 0.254 (0.273) | FAIL | 0.871 (0.780) | PASS | PASS |
| 7 | `logvolume_shapiro_p` | all | 1600 / 12927 | 0.203 | 0.0037 | 0.375 (0.397) | FAIL | 0.663 (0.780) | FAIL | PASS |
| 8 | `skew` | crash | 800 / 6275 | 0.0401 | -0.135 | 0.142 (0.175) | FAIL | 0.866 (0.772) | PASS | FAIL |
| 8 | `worst_over_best` | crash | 800 / 6275 | 1 | 1.11 | 0.129 (0.160) | FAIL | 0.858 (0.772) | PASS | FAIL |
| 20 | `mdd` | crash | 800 / 6275 | -0.512 | -0.307 | 0.623 (0.643) | FAIL | 0.613 (0.772) | FAIL | PASS |
| 20 | `worst_day` | crash | 800 / 6275 | -0.137 | -0.0944 | 0.407 (0.429) | FAIL | 0.825 (0.772) | PASS | PASS |
| 20 | `daily_sigma` | flat | 200 / 12927 | 0.0199 | 0.0175 | 0.436 (0.451) | FAIL | 0.990 (0.745) | PASS | PASS |

Size and power (pass rates of B / C at true D = 0, 0.05, 0.10):

| item | statistic | n = 200: D0 / D.05 / D.10 | n = 500: D0 / D.05 / D.10 | n = 800: D0 / D.05 / D.10 |
|---|---|---|---|---|
| 1 | `lb_p_r` | 0.02 0.99 / 0.05 1.00 / 0.00 1.00 | 0.92 0.95 / 0.94 0.98 / 0.00 1.00 | 1.00 0.97 / 1.00 0.98 / 0.00 1.00 |
| 1 | `abs_acf1_r` | 0.06 0.99 / 0.00 1.00 / 0.00 1.00 | 0.96 0.99 / 0.52 1.00 / 0.00 1.00 | 1.00 0.97 / 0.77 1.00 / 0.00 1.00 |
| 2 | `kurtosis` | 0.05 0.96 / 0.00 1.00 / 0.00 1.00 | 0.94 0.95 / 0.54 1.00 / 0.02 1.00 | 1.00 0.99 / 0.79 1.00 / 0.00 1.00 |
| 2 | `hill` | 0.01 0.97 / 0.00 1.00 / 0.00 1.00 | 0.94 0.98 / 0.34 1.00 / 0.00 1.00 | 1.00 0.98 / 0.58 1.00 / 0.00 1.00 |
| 2 | `jb_p` | 0.08 0.97 / 0.00 1.00 / 0.00 1.00 | 0.94 0.99 / 0.00 1.00 / 0.00 1.00 | 1.00 0.97 / 0.00 1.00 / 0.00 1.00 |
| 3 | `lb_p_absr` | 0.06 0.97 / 0.05 0.99 / 0.00 1.00 | 0.96 0.98 / 0.93 0.99 / 0.00 1.00 | 1.00 1.00 / 1.00 0.99 / 0.00 1.00 |
| 3 | `lb_p_r2` | 0.04 0.98 / 0.02 1.00 / 0.00 1.00 | 0.93 0.99 / 0.95 0.99 / 0.00 1.00 | 1.00 0.99 / 1.00 0.97 / 0.00 1.00 |
| 3 | `arch_lm_p` | 0.07 0.96 / 0.07 0.98 / 0.00 1.00 | 0.97 0.97 / 0.96 0.98 / 0.00 1.00 | 0.99 0.97 / 1.00 0.96 / 0.00 1.00 |
| 3 | `acf1_absr` | 0.03 0.99 / 0.02 1.00 / 0.00 0.99 | 0.94 0.99 / 0.37 1.00 / 0.00 1.00 | 1.00 0.98 / 0.60 0.99 / 0.00 0.99 |
| 4 | `acf1_absr` | 0.04 0.97 / 0.02 0.99 / 0.00 1.00 | 0.98 0.96 / 0.29 1.00 / 0.00 1.00 | 1.00 0.97 / 0.64 1.00 / 0.00 1.00 |
| 4 | `acf5_absr` | 0.05 0.99 / 0.01 0.99 / 0.00 1.00 | 0.93 0.98 / 0.33 1.00 / 0.01 1.00 | 0.98 0.96 / 0.60 0.98 / 0.00 1.00 |
| 4 | `acf10_absr` | 0.06 0.93 / 0.01 0.97 / 0.00 0.98 | 0.94 0.95 / 0.34 0.98 / 0.00 0.99 | 1.00 0.97 / 0.75 0.99 / 0.00 0.99 |
| 4 | `acf20_absr` | 0.05 0.98 / 0.01 1.00 / 0.00 0.99 | 0.96 0.97 / 0.34 0.98 / 0.01 1.00 | 1.00 0.98 / 0.62 1.00 / 0.00 0.97 |
| 4 | `acf50_absr` | 0.06 0.96 / 0.00 0.98 / 0.00 0.98 | 0.98 0.99 / 0.40 0.97 / 0.00 0.99 | 1.00 0.99 / 0.66 0.98 / 0.00 0.97 |
| 5 | `garch_persistence` | 0.03 0.98 / 0.00 1.00 / 0.00 0.95 | 0.91 0.97 / 0.68 0.95 / 0.05 0.90 | 1.00 0.99 / 0.89 0.99 / 0.05 0.93 |
| 5 | `garch_alpha` | 0.02 1.00 / 0.00 1.00 / 0.00 1.00 | 0.91 1.00 / 0.00 1.00 / 0.00 1.00 | 1.00 1.00 / 0.00 1.00 / 0.00 1.00 |
| 5 | `garch_beta` | 0.05 0.98 / 0.04 0.97 / 0.00 0.98 | 0.93 0.98 / 0.93 0.98 / 0.00 0.99 | 1.00 0.98 / 1.00 0.96 / 0.00 1.00 |
| 6 | `leverage_corr` | 0.03 1.00 / 0.01 0.97 / 0.00 0.92 | 0.94 0.97 / 0.33 0.96 / 0.01 0.80 | 0.99 0.99 / 0.66 0.93 / 0.00 0.67 |
| 6 | `gjr_gamma` | 0.08 0.97 / 0.02 0.98 / 0.00 0.98 | 0.96 1.00 / 0.67 0.95 / 0.02 0.99 | 1.00 0.98 / 0.97 0.97 / 0.06 0.96 |
| 7 | `volume_absr_spearman` | 0.03 0.99 / 0.00 0.98 / 0.00 0.93 | 0.94 0.98 / 0.34 0.97 / 0.02 0.89 | 1.00 0.98 / 0.57 0.98 / 0.00 0.84 |
| 7 | `logvolume_acf1` | 0.06 0.97 / 0.00 0.93 / 0.00 0.95 | 0.97 0.98 / 0.27 0.99 / 0.00 0.89 | 1.00 0.97 / 0.61 0.94 / 0.00 0.83 |
| 7 | `logvolume_shapiro_p` | 0.04 0.97 / 0.03 0.93 / 0.00 1.00 | 0.94 1.00 / 0.93 0.99 / 0.00 1.00 | 1.00 0.99 / 1.00 1.00 / 0.00 1.00 |
| 8 | `skew` | 0.03 0.98 / 0.02 0.97 / 0.00 0.91 | 0.93 1.00 / 0.43 0.94 / 0.01 0.73 | 0.99 0.97 / 0.62 0.96 / 0.00 0.54 |
| 8 | `worst_over_best` | 0.02 0.99 / 0.04 1.00 / 0.00 1.00 | 0.92 0.99 / 0.44 1.00 / 0.00 1.00 | 1.00 0.98 / 0.78 1.00 / 0.00 1.00 |
| 20 | `mdd` | 0.06 0.98 / 0.00 0.61 / 0.00 0.24 | 0.92 0.94 / 0.58 0.37 / 0.02 0.02 | 1.00 0.98 / 0.89 0.18 / 0.02 0.00 |
| 20 | `worst_day` | 0.04 0.97 / 0.01 0.86 / 0.00 0.30 | 0.95 0.97 / 0.41 0.53 / 0.01 0.02 | 1.00 0.97 / 0.73 0.54 / 0.00 0.00 |
| 20 | `daily_sigma` | 0.05 0.97 / 0.02 1.00 / 0.00 1.00 | 0.96 0.96 / 0.56 1.00 / 0.00 1.00 | 1.00 0.99 / 0.70 1.00 / 0.00 1.00 |
<!-- /table:e6_2 -->

## 4. The seed policy (E6.3; `generated/v2_1/e6_3/`)

Appendix A's rules applied to the cross-seed variance of every per-seed statistic on the stored 1,600-path panel, and the
decidability of each verdict at the planned n. **The final checklist runs at 500 seeds per scenario** (2,000 pooled;
T = 200; T ∈ {800, 2000} at 100 flat seeds for items 4 and 9, descriptive only); the audits at 1,600 paths without
subsampling; 16A at 100 scored seeds per scenario on training-disjoint seeds.

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

## 5. The gates

### 5.1 L1 — the noise floor derived from the x process (E6.5; `generated/v2_1/e6_5/`)

A candidate carrying nothing about x beyond the price path is V̂ = P e^{−x̂}; its within-τ share is bounded by
2Φ(τ/(s_x√(1−B))) − 1 with s_x from the volatility identity and B the Appendix-B bound. The rule replaces the hard-coded
1 % floor (weakness 32), which stays behind the `gates="v2"` switch.

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

### 5.2 L2 — the analytic bound, the sweep check, the calm-channel ladder (E6.6; `generated/v2_1/e6_6/`)

The steady-state Kalman bound (Appendix B, `tools/phase1/kalman_bound.py`, verified against LOG §3) at the parameters in
force — σ_V and h from the parameter files, **s_x derived from sbar, λ and σ_J** (no file stores a stationary sd(x)) —
checked against the surrogate at every point of Phase 1's sweep, and the nonlinear allowance measured on the ladder from
the exact Gaussian process to the generator's own calm rows. The rule that reads it (G4's second clause) is
`PREREG_PHASE_6.md` 7.3.

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

### 5.3 L2 and L2b — the target-permutation nulls and the derived margins (E6.6, E6.7; `generated/v2_1/e6_6/null/`)

Each path's target (x for L2, the macro-label vector for L2b) swapped whole with another path's, both feature sets
refitted with the audit's estimator at the panel's n; the margin is the null's 95th percentile plus the paired sampling
half-width (the centred margin is the registered sensitivity). The margins are written to the criteria file's `gates`
block by `tools/phase6/e6_criteria_extra.py --stages gates` and read back by `test_l2_gate_derived`.

<!-- table:e6_null -->
| statistic | pop | BASE | FULL | measured selectivity [paired CI] | half-width | null median | null p95 (draws) | margin | verdict |
|---|---|---|---|---|---|---|---|---|---|
| L2 R²(x) | all | +0.4059 | +0.4322 | +0.0263 [+0.0106, +0.0402] | 0.0148 | -0.0481 | -0.0362 (40) | -0.0214 | FAIL |
| L2 R²(x) | calm | +0.2912 | +0.4000 | +0.1088 [+0.0849, +0.1307] | 0.0229 | -0.0692 | -0.0542 (20) | -0.0313 | FAIL |
| L2b accuracy | all | +0.6582 | +0.6877 | +0.0295 [+0.0237, +0.0352] | 0.0057 | -0.0129 | -0.0081 (20) | -0.0023 | FAIL |
<!-- /table:e6_null -->

### 5.4 L2c — the onset audit

The addendum §1.3 rule on 200 crash + 200 bull-trap seeds with 500 circular shifts; the Phase-5 final state's run
(`generated/v2_1/e5_7c/final/onset.json`: PASS at all six transitions under the non-price rule; nine (transition, field)
failures under the rule as registered, all but one a price-derived technical) is the frozen generator's L2c, the path-hash
fixture proving the state unchanged.

## 6. The checklist on the frozen generator at the registered n (`generated/v2_1/e6_after_checklist*`)

<!-- table:e6_after -->
| item | property | population | n | A (v2) | B | C |
|---|---|---|---|---|---|---|
| 1 | No linear autocorrelation of returns | all | 3000 | PASS | FAIL | FAIL |
| 2 | Heavy tails | all | 3000 | FAIL | FAIL | PASS |
| 3 | Volatility clustering | all | 3000 | FAIL | FAIL | FAIL |
| 4 | Decay of ACF|r| (descriptive) | all | 3000 | n/a | PASS | PASS |
| 5 | GARCH persistence | all | 3000 | PASS | FAIL | FAIL |
| 6 | Leverage effect | all | 3000 | FAIL | FAIL | FAIL |
| 7 | Volume-volatility | all | 3000 | PASS | FAIL | FAIL |
| 8 | Gain/loss asymmetry in crash | crash | 1500 | FAIL | FAIL | PASS |
| 20 | Magnitudes | crash/flat | 500 | PASS | FAIL | FAIL |

| item | statistic | pop | n_gen / n_ref | gen P50 | ref P50 | B: D (upper) | B | C: share (thr) | C |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `lb_p_r` | all | 3000 / 12927 | 0.294 | 0.392 | 0.100 (0.119) | FAIL | 0.753 (0.786) | FAIL |
| 1 | `abs_acf1_r` | all | 3000 / 12927 | 0.059 | 0.0585 | 0.029 (0.042) | PASS | 0.818 (0.786) | PASS |
| 2 | `kurtosis` | all | 3000 / 12927 | 1.72 | 2.17 | 0.126 (0.142) | FAIL | 0.809 (0.786) | PASS |
| 2 | `hill` | all | 3000 / 12927 | 3.86 | 3.56 | 0.120 (0.137) | FAIL | 0.828 (0.786) | PASS |
| 2 | `jb_p` | all | 3000 / 12927 | 7.6e-07 | 8.24e-11 | 0.133 (0.149) | FAIL | 0.802 (0.786) | PASS |
| 3 | `lb_p_absr` | all | 3000 / 12927 | 0.0171 | 0.182 | 0.242 (0.260) | FAIL | 0.595 (0.786) | FAIL |
| 3 | `lb_p_r2` | all | 3000 / 12927 | 0.0851 | 0.447 | 0.189 (0.207) | FAIL | 0.717 (0.786) | FAIL |
| 3 | `arch_lm_p` | all | 3000 / 12927 | 0.182 | 0.395 | 0.124 (0.141) | FAIL | 0.803 (0.786) | PASS |
| 3 | `acf1_absr` | all | 3000 / 12927 | 0.1 | 0.0873 | 0.119 (0.138) | FAIL | 0.662 (0.786) | FAIL |
| 4 | `acf1_absr` | all | 3000 / 12927 | 0.1 | 0.0873 | 0.119 (0.137) | FAIL | 0.662 (0.786) | FAIL |
| 4 | `acf5_absr` | all | 3000 / 12927 | 0.0797 | 0.0427 | 0.188 (0.205) | FAIL | 0.672 (0.786) | FAIL |
| 4 | `acf10_absr` | all | 3000 / 12927 | 0.066 | 0.0291 | 0.178 (0.197) | FAIL | 0.666 (0.786) | FAIL |
| 4 | `acf20_absr` | all | 3000 / 12927 | 0.0437 | 0.00948 | 0.189 (0.206) | FAIL | 0.676 (0.786) | FAIL |
| 4 | `acf50_absr` | all | 3000 / 12927 | -0.0124 | -0.00898 | 0.025 (0.046) | PASS | 0.781 (0.786) | FAIL |
| 5 | `garch_persistence` | all | 3000 / 12927 | 0.981 | 0.93 | 0.267 (0.283) | FAIL | 0.723 (0.786) | FAIL |
| 5 | `garch_alpha` | all | 3000 / 12927 | 0.0623 | 0.0579 | 0.121 (0.132) | FAIL | 0.975 (0.786) | PASS |
| 5 | `garch_beta` | all | 3000 / 12927 | 0.891 | 0.825 | 0.258 (0.274) | FAIL | 0.838 (0.786) | PASS |
| 6 | `leverage_corr` | all | 3000 / 12927 | -0.0155 | -0.0381 | 0.114 (0.133) | FAIL | 0.781 (0.786) | FAIL |
| 6 | `gjr_gamma` | all | 3000 / 12927 | 0.046 | 0.0598 | 0.140 (0.153) | FAIL | 0.912 (0.786) | PASS |
| 7 | `volume_absr_spearman` | all | 3000 / 12927 | 0.326 | 0.326 | 0.050 (0.063) | PASS | 0.876 (0.786) | PASS |
| 7 | `logvolume_acf1` | all | 3000 / 12927 | 0.547 | 0.508 | 0.222 (0.238) | FAIL | 0.911 (0.786) | PASS |
| 7 | `logvolume_shapiro_p` | all | 3000 / 12927 | 0.224 | 0.0037 | 0.402 (0.419) | FAIL | 0.616 (0.786) | FAIL |
| 8 | `skew` | crash | 1500 / 6275 | -0.0266 | -0.135 | 0.137 (0.160) | FAIL | 0.880 (0.780) | PASS |
| 8 | `worst_over_best` | crash | 1500 / 6275 | 1.02 | 1.11 | 0.142 (0.165) | FAIL | 0.879 (0.780) | PASS |
| 20 | `mdd` | crash | 1500 / 6275 | -0.516 | -0.307 | 0.631 (0.649) | FAIL | 0.596 (0.780) | FAIL |
| 20 | `worst_day` | crash | 1500 / 6275 | -0.138 | -0.0944 | 0.380 (0.398) | FAIL | 0.849 (0.780) | PASS |
| 20 | `daily_sigma` | flat | 500 / 12927 | 0.0202 | 0.0175 | 0.422 (0.436) | FAIL | 0.976 (0.765) | PASS |

| item | statistic | pop | value | reference | criterion | result | n |
|---|---|---|---|---|---|---|---|
| 12 | slope of r_t on z(s_{t-1}) | r_{t-1}, calm rows | all | 0.00055313 [0.00046254300506362415, 0.000633907770729876] | 0.0008 | CI contains the configured b_pred (E6.8) | FAIL | 3000 |
| 13 | sd across seeds of the calm IV mean | all | 6.8059 [6.40094201867731, 7.231648870429242] | 0.0 | non-degenerate: CI excludes 0 (E6.8) | PASS | 2500 |
| 9 | median 200-day ACF(1) of x, flat paths | flat | 0.94502  | [0.9060659079627575, 0.9684235368359597] | inside E6.9's AR(1) reference [P10, P90] at the FIT half-life | PASS | 500 |
| 9 | median 200-day sd(x), flat paths | flat | 0.046321  | [0.03891957285254531, 0.07235255190542306] | inside the AR(1) reference [P10, P90] scaled to s_x | PASS | 500 |

Long horizons (descriptive, 100 flat seeds): T = 800: ACF(1) of x 0.9642, half-life 19.0 d, sd(x) 0.0568; T = 2000: ACF(1) of x 0.9673, half-life 20.8 d, sd(x) 0.0647.
<!-- /table:e6_after -->

## 7. The audits on the frozen generator under the derived gates (`generated/v2_1/e6_after/`)

`audit_after_derived.md` (1,600 paths, 320,000 steps, no subsampling — `test_no_subsampling_in_published_audit`;
`run_audit(..., control="level_free", gates="derived")`; 11.3 h on the laptop):

| gate | statistic | measured | margin as registered | verdict | centred margin | centred reading |
|---|---|---|---|---|---|---|
| L1 (E6.5) | within-5 % share of price itself | 0.426 | ≤ 0.617 | **PASS** | — | — |
| L2 all rows (E6.6) | FULL − BASE R²(x) | +0.0263 [+0.0106, +0.0402] | −0.0214 (null p95 −0.0362 + hw 0.0148; 40 draws) | **FAIL** | +0.0267 | undecided (0.0004 on a half-width of 0.0148) |
| L2 calm-trained (E6.6) | FULL − BASE R²(x), calm rows | +0.1088 [+0.0849, +0.1307] | −0.0313 (20 draws) | **FAIL** | +0.0379 | **FAIL** |
| L2b (E6.7) | FULL − BASE macro-class accuracy | +0.0295 [+0.0237, +0.0352]; the audit's own +0.0181 | −0.0023 (20 draws) | **FAIL** | +0.0105 | **FAIL** |

Items 14 and 16 of the Section-9 checklist read FAIL under `gates="derived"` and PASS under `gates="v2"` (the
pre-Phase-6 dictionary, unchanged). MAPE(V) (GBT, held-out seeds): full 10.4 % [10.0, 10.9] calm / 12.8 % [12.3, 13.4]
event / 15.9 % [15.2, 16.8] resolution / 12.6 % [12.3, 13.0] all; level-free 11.1 / 13.3 / 18.2 / 13.6 %.
**Held-out-scenario split** (`holdout.md`, weakness 67, no gate): R²(x) is negative on every held-out scenario for both
feature sets (GBT, all rows: bull-trap −1.27, crash −0.68, flat −0.23, sustained-bull −3.14 full; −1.31 / −0.82 / −0.25 /
−2.30 level-free) except bull-trap's calm rows (+0.29 [+0.17, +0.38] full, +0.18 [+0.07, +0.25] level-free): the
seed-split R² is within-scenario structure. Report section 3.8c.

## 8. 16A (`generated/v2_1/e6_16a/16A.md`)

**Not met** (100 scored seeds × 4 scenarios × 3 personas, oracles trained on 240 paths; θ = 0.05 the checkpoint,
{0.03, 0.08, 0.12, 0.20} sensitivities): **G1 FAIL** (0 of 4 scenarios with the true-V, observables and best-trivial
MCRs apart — a constant band edge is the true-V oracle's resting place in a directional scenario), **G2 FAIL** (0 of 4:
log(P/SMA50) at ±3 % tracks sign(x) as well as the field-bearing oracle at the FIT 22-day half-life), **G3 PASS**
(2–6 oracle switches per 200-day run; the plan expected a fail at a 150-day half-life), **G4a FAIL** (0 of 4), **G4b
FAIL** (0.2912 [0.264, 0.318] against the 0.2267 ceiling; the ladder puts +0.069 of it in the events' pre-event calm).
D17 is laid out in the report (section 5) with the failure located per gate; no option is chosen.

## 9. The tuned-parameter ledger

`v2_1/PHASE_6_REPORT.md` section 3.10: every item whose threshold moved in v2 (7, 9, 10, 11, 13, 17, 20; amendments A1,
A2, A6, A7, A8), the parameters tuned against it, and the pre-amendment results beside the amended ones.
