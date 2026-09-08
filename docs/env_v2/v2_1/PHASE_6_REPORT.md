# Phase 6 report — audits and checklist methodology: the gates, derived not stated (v2.1)

*Written as results land (execution prompt, "Documentation"); every number cites the file it comes from; the tables
marked `<!-- table:... -->` are generated from those files by `tools/phase6/e6_report_tables.py` and read back by
`tests/test_v2_1_phase_6.py::test_phase6_report_tables_match_files`. Sections follow the protocol's six headings.*

**Status: IN PROGRESS (9 September 2026).** Pre-registration written (`PREREG_PHASE_6.md`; two of its three cells
filled from files — the n = 500 size row and the L2 null; the L2b null pending); one addendum section (the L2 null's
location); the diagnostic experiments done; the gated runs (16A, the 500-seed checklist, the derived-gate audit) running
on the laptop while the lab box is unreachable (section 0).

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
| E6.6 L2 null | **done** (laptop, 80 fits) — the null sits **entirely below zero** (median −0.047 all rows, −0.069 calm-trained; p95 −0.034 / −0.054): the registered margin (p95 + half-width) is negative, **FAIL / FAIL as registered**; the registered centred sensitivity gives all rows PASS by 0.001 (within a half-width — undecided at 20 draws, raised to 40) and calm-trained **FAIL** (0.109 vs 0.038). `PREREG_PHASE_6_ADDENDUM.md` section 1 |
| E6.7 L2b null | **running** (laptop, 42 fits; the FULL classifier under permutation sits at the majority class, ≈ 0.40–0.41) |
| The switches | **written** — `run_audit(gates=, holdout_scenario=)`, `run_checklist_reference`, `evaluation/reference_stats.py`, `evaluation/criteria.py`; inertness test in `tests/test_v2_1_phase_6.py` (8 passed, 2 skipped pending files) |
| 16A | **running** (laptop, 100 scored seeds × 4 scenarios × 3 personas; oracles and rules fitted on 40 training seeds) |
| Final checklist (500 seeds), final audit (derived gates), held-out split | **queued** behind the nulls and 16A on the laptop |
| L3 | **built, not run** (D2): 200 probes from day 22 on; the entitled reader (level-free GBT) at sign accuracy 0.780 [0.718, 0.832], ceiling 0.837, permutation null p95 0.57 (`e6_l3/l3.json`) |
| Compute | laptop for everything so far. The box (128 cores; `docs/COMPUTE_GPU_ACCESS.md`): the repo made public on 8 Sep, so no credential is needed; `git clone` and the tarball fail on the proxy's mid-stream cuts; the per-file `raw.githubusercontent.com` route fetched 81 of 267 files (31 marked BAD after twenty retries each) before the proxy stopped answering at 03:01 (box time) and the ssh tunnel followed at ≈ 03:30; the downloaders resume by size when it returns; the reference-row check has not run there yet, so **no number in this report is the box's** |

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

### 3.2 E6.1 — the reference distributions (`e6_1/reference.json`, `e6_1/reference_percentiles.csv`, `e6_1/iv_reference.md`)

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

### 3.7 E6.6 / E6.7 — the nulls and the derived gates (`e6_6/null/null.{json,md}`; L2b *pending*)

<!-- table:e6_null -->
| statistic | pop | BASE | FULL | measured selectivity [paired CI] | half-width | null median | null p95 (draws) | margin | verdict |
|---|---|---|---|---|---|---|---|---|---|
| L2 R²(x) | all | +0.4059 | +0.4322 | +0.0263 [+0.0106, +0.0402] | 0.0148 | -0.0470 | -0.0343 (20) | -0.0195 | FAIL |
| L2 R²(x) | calm | +0.2912 | +0.4000 | +0.1088 [+0.0849, +0.1307] | 0.0229 | -0.0692 | -0.0542 (20) | -0.0313 | FAIL |
<!-- /table:e6_null -->

**The L2 null's location decides the reading, and it was reported before the reading was written**
(`PREREG_PHASE_6_ADDENDUM.md` section 1). Under a target permutation the FULL set (141 columns) fits a random target at
R² ≈ −0.047 (all rows) / −0.069 (calm) and the level-free BASE (45 columns) at ≈ −0.004: every one of the 40 draws of
the difference is negative, because the difference of two out-of-sample R² values from feature sets of different size is
centred at the overfitting-penalty difference, not at zero — P5-16's column-permutation finding in another form. The
plan's letter (margin = p95 + half-width) therefore gives **negative margins** (−0.020 / −0.031) that no field can pass:
**FAIL / FAIL as registered**, written to the criteria file as such. The registered centred sensitivity (p95 − median +
half-width) gives **+0.0275** on all rows — the measured +0.0263 passes by 0.0012, inside one half-width (0.0148), so
*undecided at 20 draws*; the addendum raises the draw count to 40 — and **+0.0379** calm-trained, which the measured
**+0.1088** exceeds by five half-widths: **FAIL**. That failure is the fields' calm-trained contribution Phase 5
measured (0.104: VAL +0.051 with the wandering multiple as a slow signal, LEVELS +0.023, IV +0.019): information about x
that a calm-day reader takes from the fields and cannot take from the price path. It is D17's (section 5).

**MAPE(V)**: the audit's intervals are reported in `e6_after/audit_after_derived.md` when the final audit lands; no
absolute threshold.

### 3.8 The final checklist at 500 seeds under A, B and C; E6.4 and E6.8 (`e6_after_checklist*`)

<!-- table:e6_after -->
*(pending: running)*
<!-- /table:e6_after -->

### 3.8b 16A — the checkpoint (`e6_16a/16A.{json,md}`)

<!-- table:e6_16a -->
*(pending: running at 100 scored seeds per scenario)*
<!-- /table:e6_16a -->

### 3.8c The final audit under the derived gates and the held-out-scenario split (`e6_after/`) *(pending)*

### 3.10 The tuned-parameter ledger (weakness 7)

The v2 claim "nothing re-tuned to pass" is replaced by the record. Sources: `docs/env_v2/preregistration/PREREGISTRATION_AMENDMENTS.md`
(A1–A9), `docs/env_v2/generated/e1_calibration_variants.md` (the calibration variants A–E, 25 seeds), `hazard_calibration.csv`
(the hazard grid searched to item 11), `checklist_v2_sens_*.md` (the sensitivities' footers).

| item | what moved, and when | parameters tuned against it | pre-amendment result | post-amendment result | Phase 6 reads it as |
|---|---|---|---|---|---|
| 7 (volume) | A1 (22 Aug): "log-normality not rejected" from a median Shapiro p > 0.05 to p > 0.01 in ≥ 50 % of seeds | none directly (the volume equation's \|r\| and \|x\| terms made the 5 % test reject) | median Shapiro p 0.006–0.03 → FAIL | PASS at the 1 %-majority form | the real windows reject log-normality in most cases (median p 0.0037); the generator over-satisfies it (C share 0.66 vs 0.78 required, the *other* way) — a mis-specified criterion in both forms; B/C decide |
| 9 (persistence) | A2 (22 Aug): the pass criterion moved from 200-day calm windows to the T = 800 phase-free paths | the half-life itself (60 vs 150 d variants: `checklist_v2_sens_hl60`) | 200-day ACF(1) far below 0.98 | PASS at T = 800 | E6.9: the 200-day estimator cannot reach 0.98 at any FIT half-life; re-stated as fidelity to the FIT process with the same ruler (P6-6); T = 800/2000 descriptive only |
| 10 (delta matters) | A7 (23 Aug): MDD over the event window instead of the whole path; thresholds unchanged | δ grid, D_V | partial R² 0.36–0.38, spread 16.5–18 pp → FAIL | 0.38 / 18.0 pp → still FAIL, published | the R² criterion is unattainable by construction (weakness 40); reported, not gated; the crash depth's structural floor is P4-41's |
| 11 (bubble) | the hazard (h0, b, g_max) grid-searched to "40–60 % topped, peak P/V 1.6–2.5" (`hazard_calibration.csv`, best score 0.16–0.38); A5 capped the mania drift at g_max | h0, b, g_max | uncapped: every run exceeds P/V 3 | topped 47–58 %, peak 2.1–2.4 → PASS | a calibration target, not a test (weakness 41); reported as such |
| 13 (IV) | bands 25–35 / 60–100 / corr 0.4–0.8 / gaps written to what the v2 IV block produced; A3 changed the phase multipliers from ω-only to whole-variance so panic IV could reach 60–100 | panic multiplier (×3, ×6 variants), IV horizon | calm 28–30 %, panic 50–56 %, corr 0.29–0.31 → FAIL | v2.1 E3.5 rebuilt IV as a past-only filter | the real reference (`e6_1/iv_reference.md`): single-stock IV 21.6 / 28.4 / 37.6, corr 0.55; the generator's corr 0.23 is structural (past-only filter) and reported so |
| 17 (conditioning) | rejection rate "< 5 %" while A4/A4b's anchoring drift and variance multiplier (0.25 → 1.0) set the sustained-bull rejection at 11–17 %; the tile said "calibration" | anchoring drift −0.15 x, variance multiplier | 40 % (v2 pilot) | 11–17 % at 25 seeds; D14 (control A) in Phase 4 | a property of the sampler, reported (P4-43) |
| 20 (magnitudes) | bands written to the panic targets (worst day −6..−15 %, σ 1.4–2.2 %); the σ̄, α/γ/β and jump-rate variants A–E were selected on the checklist subset | σ̄ (0.017), α/γ/β (0.10/0.10/0.83), panic multiplier (5), jump rate (0.008) — "final defaults = variant E" | variants A–D: 7–9 of 15 pass | E: 8 / 7 (50 seeds) | every one of these is FIT in v2.1 (Phases 2–4) and none is tuned to a checklist item; B/C judge the magnitudes against the crash windows (section 3.4) |
| 14 (L1) | A6 (22 Aug): "≥ 99 % of steps above the 1 % floor" to "median APE ≥ 1 % or not inside the floor more than price itself + 1 pp" | — | FAIL for any process through zero | PASS | the 1 % floor was stated; E6.5 derives the ceiling (0.617) |
| 14 (L2) | A8 (23 Aug, WITHDRAWN): selectivity margins 0.20 / 5 pp frozen after the E1 run with headroom | — | absolute: FAIL | selectivity: pass (withdrawn as a gate) | E6.6 derives the margin from the target-permutation null |
| 16 (L2b) | the 10 pp margin "frozen after the E1 calibration run" | — | +6.9 pp (v2, with the level) | +1.8 pp (Phase 5, level-free) | E6.7 derives the margin from the label-permutation null |

Sensitivity footers as stored (50 seeds, v2 criteria): default 8/7, `fw_index` 8/7, `hl60` 7/8, `omega_mode` 7/8, `panic3` 9/6, `panic6` 8/7, `pruna` 7/8 — the counts weakness 39 found mis-stated in five of six rows on the slides are these.

### 3.9 The switches, and the proof that they are inert when off

`run_audit(gates="v2", holdout_scenario=False)` is the pre-Phase-6 call and returns the pre-Phase-6 dictionary;
`gates="derived"` and `holdout_scenario=True` add keys (`derived`, `L2_holdout`) and change no existing value
(`test_audit_switches_inert`). `run_checklist` is untouched; `run_checklist_reference` is a separate entry point.
The estimator behind the reference criteria (`window_stats` in `evaluation/reference_stats.py`) reproduces E6.1's stored
rows to 1e-9 (`test_reference_stats_is_the_reference_estimator`).

---

## 4. Decisions taken and the parameter file *(in progress — DECISION_LOG P6-*)*

## 5. Decisions the team must take

**D2** (the L3 roster and ≈ $12), **D10** (the yield's rendering), **D15** (the sentiment default) — open since Phase 5
and this phase's first message; the audits ran on the deployed defaults (`shown`, A).

**D17 — triggered.** Two of the checkpoint's clauses fail under the criteria as written before any of this phase's runs,
and the ladder and the null say *where* the failure sits, which is what makes the options concrete. The full 16A table
(G1, G2, G3, G4a) follows in section 3.8 when the 100-seed run lands; the two failures already decided:

| gate | as registered | where the excess is | admissible responses (the plan's, 16A; none chosen here) |
|---|---|---|---|
| **G4(b)** the level-free price-only surrogate ≤ the Appendix-B bound + the nonlinear allowance | **FAIL** — 0.2912 [0.264, 0.318] against a ceiling of 0.2267 (0.1695 + 0.0572); no reading of the bound or the allowance passes (PREREG 7.3) | the ladder (`e6_6/bound.md`): the process stack 0.203, the generator's flat scenario 0.222 (inside the allowance), the feedback +0.001, **the events' pre-event calm +0.069** — a leak through the price path's own calm signature, Phase 4's territory | (i) **D5 / Phase 4 re-opened**: the pre-event calm of crash and bull-trap paths is distinguishable from flat calm to a level-free reader (the schedule's conditioning, the rejection sampling, or the calm-phase parameters of the event scenarios); the SEP audit of Phase 4 reported it could not narrow this, and the ladder now bounds it at 0.07 of R²(x). (ii) **D3**: a Vuolteenaho-type σ_V lowers the bound itself (Appendix B: ≈ 0.08 at 0.02/day) and would move the ceiling *down*, so it does not help this clause. (iii) Restrict the paper's claim: the price-only reader is entitled to ≈ 0.22 on flat paths and reads ≈ 0.29 on event paths' calm; state the calm channel as the engine's plus the events', with the bound beside. |
| **L2 calm-trained selectivity** (E6.6's derived gate) | **FAIL** — +0.109 [+0.085, +0.131] against −0.031 as registered and +0.038 centred | the per-field-group ablation of Phase 5 (`e5_7a/final`): VAL +0.051 (the wandering multiple — a FIT log-AR(1) at ρ_d 0.9966 — is a slow signal a calm reader uses), LEVELS +0.023, IV +0.019, ANALYST +0.010 | (i) **Phase 5's field redesign re-opened for the multiple**: the P10–P90 width (P5-10) or a shorter within-stock persistence, each a FIT choice with a measured cost; (ii) hide the P/E and yield (D10's `hidden` arm carries the yield's half: −0.038 of R²(x) under a constant multiple, P5-14); (iii) accept and state: a calm-day reader with the fields reaches R²(x) ≈ 0.40 against ≈ 0.29 without them, and the benchmark's claim is made conditional on it. |
| **L2 all-rows selectivity** | **FAIL as registered** (a negative margin); **undecided** under the centred sensitivity at 20 draws (+0.0263 vs +0.0275, inside a half-width); 40 draws pending | the fields add +0.026 of R²(x) over the level-free control on all rows (Phase 5's 93 % reduction from +0.39) | reported; the 40-draw reading follows |

The plan's own note on **G3** (16A: "G3 will fail unless D8 changes the horizon or the scoring") was written at a
half-life of 150 d; at the FIT 22.4 d the smoke run counts medians of 2–6 oracle switches per 200-day run. If the
100-seed run confirms it, G3 passes at the FIT persistence and the expectation in `PREREG_PHASE_6.md` section 12 is
recorded as disconfirmed — a measurement, not a criterion moved.

## 6. Files written or changed *(`PHASE_6_CHANGED_FILES.md`, verified against disk at the end)*

## 7. What was not done, and who owns it
