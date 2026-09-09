# Phase 6 report — audits and checklist methodology: the gates, derived not stated (v2.1)

*Written as results land (execution prompt, "Documentation"); every number cites the file it comes from; the tables
marked `<!-- table:... -->` are generated from those files by `tools/phase6/e6_report_tables.py` and read back by
`tests/test_v2_1_phase_6.py::test_phase6_report_tables_match_files`. Sections follow the protocol's six headings.*

**Status: COMPLETE, STOPPED FOR THE TEAM (9 September 2026).** Every experiment of the execution prompt ran on the
laptop (the box's reproduction check is still waiting for the tunnel, section 0); the pre-registration's three cells
are filled from files; two addendum sections (the L2 null's location; the criteria file's `items` defect); the gated
runs done — **16A is not met** (G1, G2, G4a, G4b FAIL; G3 PASS), the derived L2 and L2b gates **FAIL as registered**,
the 500-seed checklist fails every judged item under criterion B and passes two under C. Under the plan's Section 16
the programme stops here and the team takes **D17** (section 5), with D2, D10 and D15 still open. L3 is built and not
run (D2).

---

## 0. Current state, and how to read this report

| item | status |
|---|---|
| Pre-registration | `PREREG_PHASE_6.md`, written before any gated run, after the diagnostic runs it discloses in its section 2; the criteria in final form; its three cells (the n = 500 size row, the L2 and L2b null locations) filled from files with the date of the fill; `PREREG_PHASE_6_ADDENDUM.md` sections 1 (the L2 null's location) and 2 (the criteria file's `items` defect) |
| Team decisions | **D2 undecided** (L3 built, not run); **D10 undecided** (audits on `shown`); **D15 not taken** (A deployed); θ = 0.05 for 16A with the plan's sensitivity set; **D17 triggered** and laid out in section 5 |
| E6.9 known answers | **done** — 30 cases; 18 pass / 3 fail / 9 reported; the three failures are estimator properties (Hill at a 5 % depth, the sample kurtosis of a heavy tail, the JB size at 400 reps — the 2,000-rep re-check passes); item 3's rules have 23–28 % power against the generator's own shape at T = 200 |
| E6.1 reference | **done** — 12,927 windows of 417 names (31 each, four sub-periods), 0 errors; IV block 166 windows (VIX vs the FF market, the S&P 500, a set-A proxy; five single-stock IV indices) |
| E6.3 pilot | **done** on the stored 1,600-path panel; Appendix A's per-item n and the verdict decidability at 200 |
| E6.2 criteria | **done** on the stored panel: A/B/C per item and population, the size and power of B and C on known-answer panels (B has no size at n = 200; C no power against D = 0.10), the concordance table; `evaluation/params/phase6_criteria.json` written with a loud loader |
| E6.5 floor | **done** — the derived 5 % ceiling 0.606 + 0.011 = 0.617; price itself 0.426; the best of 27 extended candidates 0.399; expected PASS |
| E6.6 bound / sweep / ladder | **done** — bound 0.177 / 0.200 at the adopted parameters; 40 of 40 sweep points valid; the ladder attributes the calm channel: process stack 0.20, feedback +0.001, events' pre-event calm +0.069 |
| E6.6 L2 null | **done** (laptop, 80 fits) — the null sits **entirely below zero** (median −0.047 all rows, −0.069 calm-trained; p95 −0.034 / −0.054): the registered margin (p95 + half-width) is negative, **FAIL / FAIL as registered**; the registered centred sensitivity gives all rows PASS by 0.001 (within a half-width — undecided at 20 draws, raised to 40) and calm-trained **FAIL** (0.109 vs 0.038). `PREREG_PHASE_6_ADDENDUM.md` section 1 |
| E6.7 L2b null | **done** (laptop, 42 fits) — the same location: null median −0.013, p95 −0.008; the registered margin −0.002 and the centred +0.011 are both below the measured +0.030 (the gate's construction) / +0.018 (the audit's): **FAIL / FAIL** (addendum 1.5) |
| The switches | **written** — `run_audit(gates=, holdout_scenario=)`, `run_checklist_reference`, `evaluation/reference_stats.py`, `evaluation/criteria.py`; inertness test in `tests/test_v2_1_phase_6.py`; the registry's two entries re-expressed as the derived gates (strict xfails that XPASS when a gate passes) |
| 16A | **done** (laptop, 100 scored seeds × 4 scenarios × 3 personas): **not met** — G1, G2, G4a, G4b FAIL, G3 PASS (section 3.8b); D17 laid out in section 5 |
| Final checklist (500 seeds) | **done** under A, B and C (section 3.8): A 5 pass / 10 fail; B decisive at n = 500 and failing every judged item; C passes items 2 and 8; item 9 re-stated PASSES; item 12's realised slope 0.00055 [0.00046, 0.00063] against the configured 0.0008 FAILS; item 13's non-degeneracy PASSES |
| Final audit (derived gates), held-out split | **done** (laptop, 11.3 h at three workers; section 3.8c): L1 PASS (0.426 vs the 0.617 ceiling); L2 all rows FAIL as registered / centred undecided, calm-trained FAIL / FAIL, L2b FAIL / FAIL — items 14 and 16 FAIL under `gates="derived"`; the held-out-scenario split: R²(x) negative on every held-out scenario but bull-trap's calm rows — the seed-split R² is within-scenario structure; path hashes: 0 of 95 configurations changed vs Phase 5; freeze re-written |
| L3 | **built, not run** (D2): 200 probes from day 22 on; the entitled reader (level-free GBT) at sign accuracy 0.780 [0.718, 0.832], ceiling 0.837, permutation null p95 0.57 (`e6_l3/l3.json`) |
| Compute | **laptop for every number in this report.** The box (128 cores; `docs/COMPUTE_GPU_ACCESS.md`): the repo made public on 8 Sep, so no credential is needed; `git clone` and the tarball fail on the proxy's mid-stream cuts; the per-file `raw.githubusercontent.com` route fetched 81 of 267 files before the proxy stopped answering at 03:01 (box time) and the ssh tunnel followed at ≈ 03:30 (from ≈ 04:00 `kex_exchange_identification: Connection reset by peer`, the 5 Sep signature of a reset container); the proxy returned at 16:39, the downloaders were relaunched at 16:44 and by 16:50 **all 267 files were on the box with the committed sizes (0 bad)**; stage 2 (17:33) found a corrupt hybrid file (curl's resume appended a newer version's tail onto an older copy of the same size) and byte-hash differences with no magnitude; **stage 3 (22:28–22:30 box time, commit `74819bd`; `e6_0/box_stage3.log`) passed the reproduction check**: the numeric cross-machine check reports SAME GENERATOR (0 of 245 columns above 1e-9; worst 2.3 × 10⁻¹³), `test_smm_reference_row` passes, and `BASE\|x\|all` refitted on the regenerated panel is **0.4058695137596712, identical to the laptop's** — the panel builds in 7 s at 24 workers. The check landed after this phase's last audit had run, so **every number in this report is still the laptop's**; from Phase 7 on the box is a reference machine for sklearn stages (P6-15) |

---

## 1. Literature review and the citation table

This phase takes **methods** from the literature and **no numbers**: every criterion, margin and seed count is FIT from
E6.1's windows, derived from a bound or a null, or measured on a known-answer panel. The precedents' published
statistics (the kurtosis and ACF values in `REFERENCE_NOTE` of `evaluation/stylized_facts.py`) appear in no criterion, tolerance
or parameter file of this phase.

| Statistic or method | Source | Status | Used for |
|---|---|---|---|
| The list of stylized facts the checklist items are named after (absence of linear autocorrelation, heavy tails, gain/loss asymmetry, volatility clustering, slow decay of \|r\| autocorrelation, leverage, volume–volatility correlation) | Cont (2001, Quantitative Finance) | read in the plan's verification pass (LOG); carried, not re-read here | the item names and the statistic set of E6.1; **no numeric value** |
| Reference tables of the same facts on real single stocks; the revisit of Cont's list | Ratliff-Crain et al. (2025); Hashimoto et al. (2025, Table 3); TwinMarket (2025, Table 4) | **not re-read at source in this phase** | the *form* of a reference table (P10/P50/P90 per statistic); **their numbers are not used** — E6.1's reference is this panel's own 12,927 windows |
| Distribution overlays for generator validation | Vyetrenko et al. (2020) | not re-read | the two-sample form of criterion B (a distance between distributions rather than a point band) |
| Selectivity = full-model minus control-model performance as the measure of what a field set carries | Hewitt & Liang (2019) | read (the plan's 10.1) | E6.6/E6.7's statistic (FULL − BASE); the null is this phase's own |
| Partial-input baselines (a model given only part of the input) | Gururangan et al. (2018) | read (the plan's 10.1) | the level-free control as the partial input; the L3 probe's shuffled arm |
| Leakage defined as information available at test time that would not be available in deployment | Kaufman et al. (2012) | read (the plan's 10.1) | the framing of L1–L3; no number |
| Probe design with Wilson intervals for an LLM's answers | KTD-Fin (as cited by the plan) | not re-read | the L3 probe's interval form (`tools/phase6/e6_l3_probe.py`); no number |
| The steady-state Kalman filter for a random-walk-plus-AR(1) signal | Harvey (1989) | read in LOG §3 (Appendix B, reproduced independently on 27 Aug 2026 to three decimals; `kalman_bound_verification.json` passed) | the analytic bound of E6.6, evaluated at the parameters in force |
| Appendix A's power formulas (the share-type n; the median rule with the √(π/2) factor; the equivalence form of the KS criterion) | the plan's Appendix A (LOG §3) | read | E6.3; the measured size/power of B and C replaces the appendix's asserted "a true D ≤ 0.05 passes with ≈ 80 % power" with the table in `e6_2/criteria.md`: at n_gen = 500 B passes a true D = 0.05 in **0–96 % of simulations, median 43 %** (at 800: 0–100 %, median 73 %); two statistics (`jb_p`, `garch_alpha`) pile at a mass point and never pass a shift — so B is an equivalence test with power against D = 0.10 (≥ 95 % everywhere at 500) and only partial power against D = 0.05, not the uniform 80 % the appendix assumed |
| Survivorship: the full-universe values of crash depth, tails and volatility that a survivor panel understates | REG-15's reading of Mishkin & White (2002), GSY (2019), ABD (2007) | read in the plan; not re-read | stated per item beside the reference (section 3.2); **no number enters a criterion** |

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

### 3.7 E6.6 / E6.7 — the nulls and the derived gates (`e6_6/null/null.{json,md}`)

<!-- table:e6_null -->
| statistic | pop | BASE | FULL | measured selectivity [paired CI] | half-width | null median | null p95 (draws) | margin | verdict |
|---|---|---|---|---|---|---|---|---|---|
| L2 R²(x) | all | +0.4059 | +0.4322 | +0.0263 [+0.0106, +0.0402] | 0.0148 | -0.0481 | -0.0362 (40) | -0.0214 | FAIL |
| L2 R²(x) | calm | +0.2912 | +0.4000 | +0.1088 [+0.0849, +0.1307] | 0.0229 | -0.0692 | -0.0542 (20) | -0.0313 | FAIL |
| L2b accuracy | all | +0.6582 | +0.6877 | +0.0295 [+0.0237, +0.0352] | 0.0057 | -0.0129 | -0.0081 (20) | -0.0023 | FAIL |
<!-- /table:e6_null -->

**The L2 null's location decides the reading, and it was reported before the reading was written**
(`PREREG_PHASE_6_ADDENDUM.md` section 1). Under a target permutation the FULL set (141 columns) fits a random target at
R² ≈ −0.047 (all rows) / −0.069 (calm) and the level-free BASE (45 columns) at ≈ −0.004: every one of the 40 draws of
the difference is negative, because the difference of two out-of-sample R² values from feature sets of different size is
centred at the overfitting-penalty difference, not at zero — P5-16's column-permutation finding in another form. The
plan's letter (margin = p95 + half-width) therefore gives **negative margins** (−0.020 / −0.031) that no field can pass:
**FAIL / FAIL as registered**, written to the criteria file as such. The registered centred sensitivity (p95 − median +
half-width) gave **+0.0275** on all rows at 20 draws — the measured +0.0263 passing by 0.0012, inside one half-width
(0.0148), so *undecided*; the addendum raised the draw count to 40 (same seed stream, the first 20 unchanged): p95
−0.0362, centred margin **+0.0267** against **+0.0263** — a gap of 0.0004 on a half-width of 0.0148, which doubling the
draws did not move. The all-rows centred reading is therefore **undecided at this panel's n** (the file records
`pass_centred: true` by the letter; the report does not call it a pass). Calm-trained the centred margin is **+0.0379**,
which the measured **+0.1088** exceeds by five half-widths: **FAIL**. That failure is the fields' calm-trained
contribution Phase 5 measured (0.104: VAL +0.051 with the wandering multiple as a slow signal, LEVELS +0.023, IV +0.019):
information about x that a calm-day reader takes from the fields and cannot take from the price path. It is D17's
(section 5).

**L2b** (E6.7, addendum 1.5): the label-permutation null has the same location — FULL (141 columns) reaches ≈ 0.40–0.41
on a permuted macro label and BASE ≈ 0.41–0.42, both at the majority class 0.414 — so the registered margin is
**−0.0023** and the centred **+0.0105**, against a measured **+0.0295** [+0.0237, +0.0352] in the gate's construction
and **+0.0181** in the audit's own: **FAIL under both margins in both constructions**. Phase 5's "PASS at +1.8 pp" was
against the 10 pp margin frozen after the result was known; the derived margin is a tenth of that.

**MAPE(V)** (`e6_after/audit_after_derived.md`, GBT, held-out seeds; no absolute threshold): the full set 10.4 %
[10.0, 10.9] calm, 12.8 % [12.3, 13.4] event, 15.9 % [15.2, 16.8] resolution, 12.6 % [12.3, 13.0] all rows; the
level-free control 11.1 % [10.6, 11.5] / 13.3 % [12.7, 13.9] / 18.2 % [17.3, 19.2] / 13.6 % [13.2, 14.0]. The fields
gain 0.5–2.3 pp of MAPE(V), most in resolution.

### 3.8 The final checklist at 500 seeds under A, B and C; E6.4 and E6.8 (`e6_after_checklist*`)

The registered run (PREREG 5.3): the SCL design at **500 seeds per scenario** (seeds 40000+; 3,000 T = 200 paths pooled,
1,500 of them crash across the three δ), T = 200, the v2 checklist (`run_checklist`, unchanged) and the reference
criteria (`run_checklist_reference`) on the same paths; T ∈ {800, 2000} at 100 flat seeds for items 4 and 9, descriptive.
2,327 s on the laptop. The B/C evaluation was re-run from the cached per-path statistics after the criteria file's
`items` block was corrected to the registered per-statistic populations (addendum section 2); nothing else moved.

**Under A (v2):** 5 pass / 10 fail / 5 n.a. — items 1, 5, 7, 15, 20 pass; 2, 3, 6, 8, 9, 10, 11, 12, 13, 17 fail
(`e6_after_checklist.md`). **Under B:** every judged item fails — the generator's cross-seed distributions are not
KS-equivalent to the real windows within D0 = 0.10 on any item, and at n_gen = 3,000 the bootstrap upper limit sits
only ≈ 0.017 above D, so the verdict is the distance itself: D is 0.03–0.05 on `abs_acf1_r`, `volume_absr_spearman`
and `acf50_absr` (they pass alone), 0.10–0.14 on the tail, ARCH-LM, leverage and GJR statistics, 0.19–0.27 on the
persistence and the LB\|r\| statistics, and 0.38–0.63 on `logvolume_shapiro_p`, `worst_day`, `daily_sigma` and `mdd`.
**Under C:** items 2 and 8 pass; 1 (LB p on r, share 0.753 against 0.786), 3, 5, 6 (leverage 0.781 against 0.786), 7
(the log-volume normality: the generator's median Shapiro p is 0.224 where real windows' is 0.004 — the generator's
volume is *more* log-normal than real volume) and 20 (MDD: the crash scenario's median −0.52 against the crash windows'
−0.31; calm σ on flat 0.020 against every window's 0.017) fail.

**E6.4 — per scenario, and the regime-switching contribution.** The pooled failures on the clustering items are the
crash scenario's: LB\|r\| p < 0.01 inside the band in **0.83 / 0.81 / 0.83** of flat / bull-trap / sustained-bull paths
and **0.37** of crash paths (pooled 0.60, threshold 0.786); the leverage correlation 0.81 / 0.78 / 0.84 against 0.75
in crash. ACF\|r\|(1) fails in every scenario (0.61–0.73): the generator's distribution is wider than the real
windows' at the same median (0.100 vs 0.087). The regime-switching contribution is the pooled-minus-flat share:
≈ −0.23 on LB\|r\| and −0.03 on leverage.

**E6.8 — the never-implemented criteria.** Item 12: the within-phase partial slope of r_t on the standardised s_{t−1}
is **0.00055 [0.00046, 0.00063]** against the configured b_pred = 0.0008 — **FAIL**: the realised next-day loading is
≈ 70 % of the configured one (the reversal `b_rev` = 0.0006 over days 2–5 and the sentiment's own autocorrelation
absorb part of it in a partial slope); a fidelity question for the sentiment block (D15), reported. Item 13:
non-degenerate across seeds — the calm IV mean's cross-seed sd 6.8 [6.4, 7.2] — **PASS**.

**Item 9 re-stated** (P6-6): the flat paths' median 200-day ACF(1) of x **0.945** inside [0.906, 0.968] and the
median 200-day sd(x) **0.0463** inside [0.039, 0.072] — **PASS** on both: the generator's x is the FIT process measured
with the FIT process' own ruler. The v2 band (≥ 0.98, ≥ 60 d, 0.08–0.20) fails under A as E6.9 said it would. The
descriptive long horizons: T = 800 ACF(1) 0.964, half-life 19.0 d, sd 0.057; T = 2000 0.967, 20.8 d, 0.065 — the
estimator bias closing toward the FIT 22.4 d as T grows.

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

### 3.8b 16A — the checkpoint (`e6_16a/16A.{json,md}`)

<!-- table:e6_16a -->
100 scored seeds per scenario, 40 training seeds; best simple rule `p_sma50` (scale 0.03, direction +1).

**θ = 0.03** (sensitivity)

| scenario | oracle | L5 level-free observables | L5 level-free price-only | best rule | best trivial |
|---|---|---|---|---|---|
| flat | 0.0220 [0.0192, 0.0255] | 0.0781 [0.0705, 0.0859] | 0.0768 [0.0701, 0.0840] | 0.0623 [0.0564, 0.0690] | band_hi: 0.0885 [0.0779, 0.0989] |
| bull_trap | 0.0116 [0.0102, 0.0129] | 0.0459 [0.0400, 0.0524] | 0.0483 [0.0426, 0.0546] | 0.0432 [0.0381, 0.0483] | band_hi: 0.0353 [0.0301, 0.0409] |
| crash | 0.0140 [0.0124, 0.0157] | 0.0564 [0.0513, 0.0616] | 0.0536 [0.0493, 0.0581] | 0.0562 [0.0514, 0.0607] | band_lo: 0.0692 [0.0621, 0.0767] |
| sustained_bull | 0.0225 [0.0194, 0.0252] | 0.0779 [0.0687, 0.0870] | 0.0788 [0.0707, 0.0874] | 0.0624 [0.0546, 0.0710] | band_hi: 0.0872 [0.0774, 0.0973] |

| gate | per scenario | verdict |
|---|---|---|
| G1 | {'flat': False, 'bull_trap': False, 'crash': True, 'sustained_bull': False} | FAIL |
| G2 (0 of 4) | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G3 | flat: median 3, share≥2 0.88, bull_trap: median 2, share≥2 0.77, crash: median 6, share≥2 0.92, sustained_bull: median 3, share≥2 0.89 | PASS |
| G4a | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |

**θ = 0.05** — the checkpoint

| scenario | oracle | L5 level-free observables | L5 level-free price-only | best rule | best trivial |
|---|---|---|---|---|---|
| flat | 0.0027 [0.0026, 0.0028] | 0.0770 [0.0669, 0.0856] | 0.0745 [0.0660, 0.0842] | 0.0541 [0.0458, 0.0622] | band_hi: 0.0874 [0.0751, 0.0997] |
| bull_trap | 0.0033 [0.0033, 0.0034] | 0.0383 [0.0326, 0.0448] | 0.0405 [0.0342, 0.0476] | 0.0378 [0.0325, 0.0428] | band_hi: 0.0262 [0.0214, 0.0312] |
| crash | 0.0022 [0.0022, 0.0023] | 0.0466 [0.0409, 0.0518] | 0.0437 [0.0395, 0.0482] | 0.0481 [0.0430, 0.0533] | band_lo: 0.0581 [0.0506, 0.0660] |
| sustained_bull | 0.0028 [0.0027, 0.0029] | 0.0769 [0.0669, 0.0869] | 0.0771 [0.0668, 0.0878] | 0.0570 [0.0480, 0.0665] | band_hi: 0.0877 [0.0749, 0.1006] |

| gate | per scenario | verdict |
|---|---|---|
| G1 | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G2 (0 of 4) | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G3 | flat: median 2, share≥2 0.76, bull_trap: median 2, share≥2 0.61, crash: median 4, share≥2 0.90, sustained_bull: median 2, share≥2 0.77 | PASS |
| G4a | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |

**θ = 0.08** (sensitivity)

| scenario | oracle | L5 level-free observables | L5 level-free price-only | best rule | best trivial |
|---|---|---|---|---|---|
| flat | 0.0029 [0.0028, 0.0030] | 0.0750 [0.0629, 0.0889] | 0.0706 [0.0577, 0.0841] | 0.0428 [0.0322, 0.0531] | band_hi: 0.0995 [0.0816, 0.1160] |
| bull_trap | 0.0035 [0.0034, 0.0035] | 0.0286 [0.0226, 0.0345] | 0.0303 [0.0238, 0.0370] | 0.0316 [0.0263, 0.0370] | band_hi: 0.0169 [0.0130, 0.0217] |
| crash | 0.0022 [0.0022, 0.0023] | 0.0329 [0.0284, 0.0384] | 0.0293 [0.0247, 0.0344] | 0.0363 [0.0316, 0.0423] | band_lo: 0.0398 [0.0323, 0.0470] |
| sustained_bull | 0.0030 [0.0028, 0.0032] | 0.0783 [0.0636, 0.0928] | 0.0781 [0.0640, 0.0932] | 0.0516 [0.0406, 0.0654] | band_hi: 0.0976 [0.0805, 0.1130] |

| gate | per scenario | verdict |
|---|---|---|
| G1 | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G2 (0 of 4) | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G3 | flat: median 1, share≥2 0.37, bull_trap: median 1, share≥2 0.47, crash: median 3, share≥2 0.73, sustained_bull: median 1, share≥2 0.38 | FAIL |
| G4a | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |

**θ = 0.12** (sensitivity)

| scenario | oracle | L5 level-free observables | L5 level-free price-only | best rule | best trivial |
|---|---|---|---|---|---|
| flat | 0.0028 [0.0025, 0.0031] | 0.0641 [0.0446, 0.0834] | 0.0514 [0.0362, 0.0670] | 0.0237 [0.0126, 0.0356] | band_lo: 0.0958 [0.0720, 0.1190] |
| bull_trap | 0.0035 [0.0035, 0.0036] | 0.0214 [0.0160, 0.0273] | 0.0243 [0.0178, 0.0322] | 0.0270 [0.0222, 0.0336] | band_hi: 0.0112 [0.0076, 0.0150] |
| crash | 0.0020 [0.0020, 0.0021] | 0.0187 [0.0139, 0.0236] | 0.0159 [0.0116, 0.0198] | 0.0234 [0.0185, 0.0282] | band_lo: 0.0237 [0.0171, 0.0299] |
| sustained_bull | 0.0031 [0.0028, 0.0034] | 0.0774 [0.0578, 0.0999] | 0.0774 [0.0581, 0.0982] | 0.0454 [0.0270, 0.0625] | band_lo: 0.0940 [0.0701, 0.1154] |

| gate | per scenario | verdict |
|---|---|---|
| G1 | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G2 (0 of 4) | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G3 | flat: median 1, share≥2 0.12, bull_trap: median 1, share≥2 0.22, crash: median 2, share≥2 0.56, sustained_bull: median 1, share≥2 0.17 | FAIL |
| G4a | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |

**θ = 0.2** (sensitivity)

| scenario | oracle | L5 level-free observables | L5 level-free price-only | best rule | best trivial |
|---|---|---|---|---|---|
| flat | 0.0025 [0.0019, 0.0030] | 0.0412 [0.0105, 0.0814] | 0.0119 [0.0025, 0.0280] | 0.0049 [0.0025, 0.0082] | band_lo: 0.0165 [0.0020, 0.0448] |
| bull_trap | 0.0035 [0.0035, 0.0036] | 0.0156 [0.0113, 0.0208] | 0.0184 [0.0119, 0.0255] | 0.0242 [0.0187, 0.0302] | band_hi: 0.0061 [0.0041, 0.0089] |
| crash | 0.0018 [0.0017, 0.0019] | 0.0055 [0.0037, 0.0080] | 0.0041 [0.0027, 0.0058] | 0.0086 [0.0056, 0.0120] | band_lo: 0.0107 [0.0056, 0.0167] |
| sustained_bull | 0.0024 [0.0017, 0.0030] | 0.0604 [0.0276, 0.0980] | 0.0459 [0.0184, 0.0749] | 0.0157 [0.0029, 0.0362] | band_lo: 0.0275 [0.0022, 0.0638] |

| gate | per scenario | verdict |
|---|---|---|
| G1 | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G2 (0 of 4) | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |
| G3 | flat: median 0, share≥2 0.00, bull_trap: median 1, share≥2 0.06, crash: median 1, share≥2 0.14, sustained_bull: median 0, share≥2 0.01 | FAIL |
| G4a | {'flat': False, 'bull_trap': False, 'crash': False, 'sustained_bull': False} | FAIL |

G4b: surrogate 0.2912 [0.2637, 0.3179] vs ceiling 0.2267 (bound 0.1695 + allowance 0.0572) → FAIL
<!-- /table:e6_16a -->

Computed exactly as 16A is written (PREREG 12): 100 scored seeds per scenario, 40 training seeds (disjoint) for the two
level-free oracles (`Oracle16A`: the frozen `ObservablesOracle` with the n/m encoding, a 20-day history, and the field
sets 16A names) and for the pre-registered rule family's scales; three personas; θ = 0.05 the checkpoint with the plan's
sensitivity set; MCR with 500-resample cluster-bootstrap intervals over seeds (`e6_16a/runs.csv`, every run).

**Reading, under the criterion as written.**

- **G1 FAILS in every scenario at θ = 0.05.** The oracle < observables ordering holds everywhere with intervals apart,
  but the second inequality does not: the best *trivial* policy is a **constant band edge**, and it matches or beats the
  level-free observables oracle — bull-trap: band-high 0.0262 [0.0214, 0.0312] *below* the oracle's 0.0383 [0.0326,
  0.0448]; crash: band-low 0.0581 vs 0.0466 with overlapping intervals; flat and sustained-bull: band-high 0.087 vs
  0.077, overlapping. In a directional scenario the true-V oracle's target sits at one band edge most of the time, so a
  policy that sits there constantly is hard to beat on MCR. Phase 5's discrimination table (P5-19) had the ordering
  with both gaps' intervals above zero because its trivial set was always-hold and constant-mix; 16A's list adds the
  band edges, and they decide it.
- **G2 FAILS (0 of 4).** The best two-line rule — cash to band-high when log(P/SMA50) > 0.03, band-low when < −0.03,
  the scale and direction fitted on the training seeds — is *not* above the observables oracle: it is below it in flat
  (0.054 vs 0.077) and sustained-bull (0.057 vs 0.077) and level in the event scenarios. Item 1's finding ("a two-line
  rule reaches oracle level") reproduces at the FIT persistence: with a 22-day half-life, the price's position against
  its 50-day average is a serviceable proxy for the sign of x.
- **G3 PASSES at θ = 0.05** — medians of 2 / 2 / 4 / 2 oracle target switches per run (flat / bull-trap / crash /
  sustained-bull) with shares ≥ 2 of 0.76 / 0.61 / 0.90 / 0.77. The plan's note that G3 "will fail unless D8 changes
  the horizon" was written at a 150-day half-life; at the FIT 22.4 d the oracle changes its mind several times in 200
  days. **The expectation registered in PREREG 12 is disconfirmed.** G3 fails at θ ≥ 0.08 (fewer crossings of a wider
  band), which is the θ sensitivity the checkpoint asked for.
- **G4a FAILS in every scenario.** The level-free observables oracle does not beat the level-free price-only oracle:
  0.0770 vs 0.0745 (flat), 0.0383 vs 0.0405, 0.0466 vs 0.0437, 0.0769 vs 0.0771 — every pair overlapping, two of four
  the wrong way. The fields *do* improve x̂ on the training pool (calm OOS R² 0.10 vs −0.08, sign accuracy 0.85 vs
  0.78; `e6_16a/run.log`); the improvement does not reach the mandate metric. This is the policy-level statement of
  Phase 5's +0.026 of R²(x): what the fields carry beyond the price path is real but small, and MCR does not see it.
- **G4b FAILS** (section 3.6; the ladder attributes the excess to the events' pre-event calm).

**Caveats stated with the result, not against it.** (i) The oracles are GBTs on 240 training paths (40 seeds × 6
designs), the count Phase 5 used; a larger training pool is a D17 option, not a re-run of this checkpoint. (ii) The
rule family's scales were fitted on the same 40 seeds. (iii) The three personas share each path, so the intervals are
cluster-bootstrapped over seeds. (iv) Every number is the laptop's; the box did not run.

**The checkpoint's verdict:** 16A is **not met** — G1, G2, G4a and G4b fail; G3 passes. Under Section 16 the plan stops
after Phase 6 and the team takes D17 (section 5).

### 3.8c The final audit under the derived gates and the held-out-scenario split (`e6_after/`)

**The run.** `run_audit(panel, shown, max_rows=None, control="level_free", gates="derived")` on the stored Phase-5
after-state panel (`sep_phase5_after.pkl`: 1,600 paths, 320,000 steps, no subsampling —
`test_no_subsampling_in_published_audit`), the three surrogate families (ridge, GBT, MLP) on held-out seeds with the
500-resample cluster bootstrap; 40,755 s (11.3 h) at three workers on the laptop, the null draws sharing the machine.
The held-out-scenario split (`holdout_scenario=True`'s table, run as its own stage) 192 s. Outputs:
`audit_after_derived.{md,pkl}`, `_L1/_L2/_L4/_checklist_rows.csv`, `holdout.{md,csv}`.

**L1 under the derived ceiling (E6.5): PASS.** Price itself has 42.6 % of steps within 5 % of V against the ceiling
0.617; every field candidate 3.0–3.6 % (`k·P·dividend_yield` 0.036, `k·P/reported_PE` 0.036, `k·analyst_fair_value`
0.030). The v2 literal (median APE 6.3 %, 91 % of steps above the 1 % floor) is reported in the statistic column and
gates nothing.

**L2 — the v2 literal, reported.** Calm best R²(x) −0.614 (ridge; GBT −0.716, MLP −1.187), calm sign accuracy 0.654;
event best R²(x) 0.454 (GBT), sign 0.891; the literal's thresholds (R² ≤ 0.30, sign ≤ 0.70; event R² < 0.90) are met
and decide nothing. The audit's own selectivity (best full minus best level-free, the audit's held-out-seed split):
+0.015 all rows (0.421 − 0.406), +0.021 event, +0.078 resolution, −0.254 calm (both negative there; the audit's calm
population is the SEP panel's calm rows scored by a model trained on every row, not the calm-trained model of the gate).

**L2 and L2b under the derived gates (E6.6, E6.7; the criteria file's `gates` block re-attached to the audit):**

| gate | measured | null median / p95 (draws) | margin as registered | verdict | centred margin | centred reading |
|---|---|---|---|---|---|---|
| L2 all rows | +0.0263 [+0.0106, +0.0402] | −0.0481 / −0.0362 (40) | −0.0214 | **FAIL** | +0.0267 | undecided (0.0004 on a half-width of 0.0148) |
| L2 calm-trained | +0.1088 [+0.0849, +0.1307] | −0.0692 / −0.0542 (20) | −0.0313 | **FAIL** | +0.0379 | **FAIL** |
| L2b | +0.0295 (gate's construction); +0.0181 (the audit's) | −0.0129 / −0.0081 (20) | −0.0023 | **FAIL** | +0.0105 | **FAIL** (both constructions) |

Items 14 and 16 of the Section-9 checklist therefore read **FAIL** under `gates="derived"`
(`audit_after_derived_checklist_rows.csv`); under `gates="v2"` the same panel reads 14 PASS (L1 + the L2 literal) and
16 PASS (+1.8 pp against 10 pp) — the pre-Phase-6 dictionary, unchanged (`test_audit_switches_inert`).

**L2b's own figures:** full 67.6 %, level-free 65.8 %, day-only 50.8 %, majority class 41.4 % — Phase 5's numbers
reproduced on the stored panel. **Scenario discrimination (D5):** accuracy price-only 53.8 %, price + IV 53.7 %,
full 49.5 % against a 37.7 % majority; recall of sustained-bull days 20–21 % in every set — reported, no threshold.
**L4 resolvability:** unchanged from Phase 5 (calm rows' median |x| 0.037, coverage at θ = 0.05 0.37; panic 0.75,
blow-off 0.99).

**The held-out-scenario split (weakness 67; `holdout.md`): the surrogate does not transfer across scenarios.**
Train on three scenarios, score the fourth (level-free and full sets; ridge and GBT; 400 / 800 / 200 / 200 held-out
paths):

| held out | full GBT, all rows | level-free GBT, all rows | full GBT, calm rows | level-free GBT, calm rows |
|---|---|---|---|---|
| bull-trap | −1.27 [−1.42, −1.15] | −1.31 [−1.47, −1.19] | **+0.29** [+0.17, +0.38] | +0.18 [+0.07, +0.25] |
| crash | −0.68 [−0.76, −0.61] | −0.82 [−0.89, −0.76] | −0.29 [−0.48, −0.15] | −0.86 [−1.07, −0.71] |
| flat | −0.23 [−0.38, −0.10] | −0.25 [−0.40, −0.13] | (= all) | (= all) |
| sustained-bull | −3.14 [−3.95, −2.50] | −2.30 [−2.78, −1.88] | (= all) | (= all) |

R²(x) is negative on every held-out scenario except bull-trap's calm rows. The pooled 0.42 of the seed-split audit is
therefore **within-scenario structure**: each scenario's x has its own location (sustained-bull's positive drift,
crash's negative run), a model that never saw that scenario predicts around the wrong mean, and R² against the
held-out scenario's own variance goes below zero — most for sustained-bull (−2.3 to −3.1), whose x distribution the
other three do not contain. The fields help the transfer under GBT on four of the five distinct comparisons (crash
calm −0.29 vs −0.86 the largest) and hurt it on sustained-bull; under ridge they help on bull-trap only. There is no
registered threshold on this table (PREREG 7.4 names it a report); it says that the audit's R²(x) is a statement
about a reader who has seen every scenario, and that the per-scenario reporting E6.4 asks for is not optional for L2
either.

**Path hashes and the freeze.** 95 configurations hashed (`path_hashes_phase6_after.json`) against the Phase-5 fixture:
**0 changed** — this phase altered no path (`path_hashes_phase6_compare.json`); the freeze manifest re-written with
the label "v2.1 Phase 6 freeze" and checked by `tests/test_v2_freeze.py`.

### 3.9 The switches, and the proof that they are inert when off

`run_audit(gates="v2", holdout_scenario=False)` is the pre-Phase-6 call and returns the pre-Phase-6 dictionary;
`gates="derived"` and `holdout_scenario=True` add keys (`derived`, `L2_holdout`) and change no existing value
(`test_audit_switches_inert`). `run_checklist` is untouched; `run_checklist_reference` is a separate entry point.
The estimator behind the reference criteria (`window_stats` in `evaluation/reference_stats.py`) reproduces E6.1's stored
rows to 1e-9 (`test_reference_stats_is_the_reference_estimator`).

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

---

## 4. Decisions taken and the parameter file

The decisions are `DECISION_LOG.md` P6-1 to P6-14, each with its evidence, the alternative rejected and the file.
In one line each:

- **P6-1** the box is a reference machine only after two reference rows reproduce; the code reaches it by the
  per-file public-repo route with no credential on it.
- **P6-2** the known-answer tests run first; three failures recorded as estimator properties (Hill at 5 %, the sample
  kurtosis of a heavy tail, the JB size at 400 reps), not repaired by re-tuning.
- **P6-3** B is decisive and only at n ≥ its measured size threshold; C is the band report; 500 seeds per scenario.
- **P6-4** G4b read as the window-average bound at the derived s_x + the nonlinear allowance; expected FAIL.
- **P6-5** the L1 rule derived from the x process (ceiling 0.617); the 1 % floor behind `gates="v2"`.
- **P6-6** item 9 judged as fidelity to the FIT process with the same 200-day ruler; the v2 band reported as A.
- **P6-7** the gate statistic and its null computed by one tool with one construction; the centred margin registered
  as the sensitivity before any draw was read.
- **P6-8** every change to the audit machinery a switch that is inert when off; one estimator for the reference and
  the generator.
- **P6-9** the L2 null below zero: FAIL as registered, the centred sensitivity beside, the rule not re-specified.
- **P6-10** B's n_min = 500 from its measured size; the earlier fill (800) recorded.
- **P6-11** 16A computed as written and not met (G1, G2, G4a, G4b FAIL; G3 PASS); D17 laid out, nothing chosen.
- **P6-12** the criteria file's `items` block corrected to the registered overrides after the first table was read;
  the verdicts re-evaluated from cache; a test asserts the file.
- **P6-13** L2b FAIL under both margins in both constructions; the all-rows L2 centred reading recorded as undecided,
  not as the file's boolean; the registry keeps both entries.
- **P6-14** the held-out-scenario split reported as a finding (no transfer across scenarios), no gate.

**The parameter file — `evaluation/params/phase6_criteria.json`** (loud loader `evaluation/criteria.py`; every block
carries `label`, `source`, `date`, `interval`, `n` and a status from `_status_key` — FIT, DERIVED, MEASURED — and the
loader raises on a missing field, an undeclared status or an empty reference):

| block | what it holds | status | source |
|---|---|---|---|
| `reference` | P10 / P50 / P90 of every E6.1 statistic, all windows and by sub-period, each with its n (12,927 windows, 417 names) | FIT | `e6_1/reference.json` |
| `criterion_B` | D0 = 0.10, the bootstrap form, `n_min_size` = 500 and the size table by n | FIT / DERIVED | `e6_2/criteria.json` |
| `criterion_C` | p0 = 0.80 and the one-sided band 0.80 − 1.96√(0.8·0.2/n) | FIT | PREREG 5.2 |
| `crash_window_rule` | the crash-window population: 200-day MDD ≤ −0.20 | FIT | PREREG 5.1 |
| `items` | item → statistics, population, reference, the per-statistic overrides (item 20's σ on the flat paths against every window), item 4 descriptive | — | `ITEMS` in `tools/phase6/e6_2_criteria.py` |
| `item9_reference` | ACF(1) [0.906, 0.968] and sd(x) [0.039, 0.072] at T = 200 from the AR(1) known answer at the FIT half-life, scaled to s_x | DERIVED | `e6_9/known_answers.json`, `e6_6/bound.json` |
| `gates.l1_floor` | the within-5 % ceiling 0.617 (0.606 + 0.011) | DERIVED | `e6_5/floor.json` |
| `gates.l2_all`, `gates.l2_calm`, `gates.l2b` | measured selectivity with its paired CI, the null's median / p95 / draws, the margin as registered, `pass`, the centred margin, `pass_centred`, BASE and FULL | DERIVED | `e6_6/null/null.json` |

Consumers: `run_checklist_reference` (B, C, the populations), `leakage_audit.derived_verdicts` (the gates),
`_derived_audit_bounds` in `envs/v2/observables_params.py` (the only `envs/` edit: `AUDIT_BOUNDS`' two Phase-6-owned
entries are replaced when the file holds the gates — `no_field_deterministic_R2` by the centred L2 all-rows margin
+0.0267 (a field group's add-one over the level-free control is the FULL − BASE construction; the registered
uncentred margin −0.0214 is carried beside as `…_registered_uncentred`, since a negative bound on an add-one is
meaningless), `l2b_margin_phase6_owned` by the registered L2b margin −0.0023 — and `status` reads DERIVED; without
the file the PROVISIONAL 0.2 / 0.1 stand and the status says so).

## 5. Decisions the team must take

**D2** (the L3 roster and ≈ $12), **D10** (the yield's rendering), **D15** (the sentiment default) — open since Phase 5
and this phase's first message; the audits ran on the deployed defaults (`shown`, A).

**D17 — triggered.** 16A is not met (section 3.8b): G1, G2, G4a and G4b fail; G3 passes. The ladder, the null and the
checkpoint's own table say *where* each failure sits, which is what makes the options concrete. None is chosen here.

| gate | as registered | where the failure sits | admissible responses (the plan's, 16A; none chosen here) |
|---|---|---|---|
| **G1** oracle < observables oracle < best trivial, intervals apart, every scenario | **FAIL** (0 of 4 at θ = 0.05; crash alone at θ = 0.03) | the constant band edges: in a directional scenario the true-V oracle sits at one edge most of the time, so a constant edge is within the observables oracle's interval (crash, flat, sustained-bull) or below it (bull-trap, 0.026 vs 0.038). The oracle → observables gap holds everywhere. | (i) the plan's trivial set read as it was in Phase 5's discrimination table (always-hold, constant-mix, random) — then G1 holds, but that is a change of criterion after the result and is not made here; (ii) a mandate design in which the band edges are not the oracle's resting places (REG-13, D9: utility-consistent bands), a Phase-7 question; (iii) restrict the claim: the benchmark measures conformity, not the value of the information. |
| **G2** best simple level-free rule above the observables oracle, ≥ 3 of 4 | **FAIL** (0 of 4) | log(P/SMA50) at ±3 % tracks sign(x) as well as the field-bearing GBT at a 22-day half-life; the rule beats the oracle in flat and sustained-bull | (i) the oracles trained on more than 240 paths (a D17 re-run of the checkpoint at a larger training pool, stated as such); (ii) D3 / D5: a longer FIT persistence is not admissible (tuning-to-pass), but a value process whose σ_V is Vuolteenaho-type makes x harder to read from P/SMA (Appendix B: the bound falls to ≈ 0.08); (iii) restrict the claim to a one-shot mandate-conflict benchmark, where the rule's edge is irrelevant. |
| **G4a** level-free observables oracle beats the level-free price-only oracle, every scenario | **FAIL** (0 of 4; two pairs the wrong way) | the fields raise calm OOS R²(x) from −0.08 to 0.10 and sign accuracy from 0.78 to 0.85 on the training pool, and the policy does not gain: what the fields carry is small (Phase 5: +0.026 of R²) and MCR does not see it | (i) Phase 5's field redesign re-opened in the *other* direction — fields that carry legitimate, non-leaking information the price path lacks (the plan's D3/Phase-5 route); (ii) accept: the benchmark's observables are cosmetic to a level-free reader, and the paper's claim is about mandate conformity under a rendered environment, not about information in the fields. |
| **G4(b)** the level-free price-only surrogate ≤ the Appendix-B bound + the nonlinear allowance | **FAIL** — 0.2912 [0.264, 0.318] against a ceiling of 0.2267 (0.1695 + 0.0572); no reading of the bound or the allowance passes (PREREG 7.3) | the ladder (`e6_6/bound.md`): the process stack 0.203, the generator's flat scenario 0.222 (inside the allowance), the feedback +0.001, **the events' pre-event calm +0.069** — a leak through the price path's own calm signature, Phase 4's territory | (i) **D5 / Phase 4 re-opened**: the pre-event calm of crash and bull-trap paths is distinguishable from flat calm to a level-free reader (the schedule's conditioning, the rejection sampling, or the calm-phase parameters of the event scenarios); the SEP audit of Phase 4 reported it could not narrow this, and the ladder now bounds it at 0.07 of R²(x). (ii) **D3**: a Vuolteenaho-type σ_V lowers the bound itself (Appendix B: ≈ 0.08 at 0.02/day) and would move the ceiling *down*, so it does not help this clause. (iii) Restrict the paper's claim: the price-only reader is entitled to ≈ 0.22 on flat paths and reads ≈ 0.29 on event paths' calm; state the calm channel as the engine's plus the events', with the bound beside. |
| **L2 calm-trained selectivity** (E6.6's derived gate) | **FAIL** — +0.109 [+0.085, +0.131] against −0.031 as registered and +0.038 centred | the per-field-group ablation of Phase 5 (`e5_7a/final`): VAL +0.051 (the wandering multiple — a FIT log-AR(1) at ρ_d 0.9966 — is a slow signal a calm reader uses), LEVELS +0.023, IV +0.019, ANALYST +0.010 | (i) **Phase 5's field redesign re-opened for the multiple**: the P10–P90 width (P5-10) or a shorter within-stock persistence, each a FIT choice with a measured cost; (ii) hide the P/E and yield (D10's `hidden` arm carries the yield's half: −0.038 of R²(x) under a constant multiple, P5-14); (iii) accept and state: a calm-day reader with the fields reaches R²(x) ≈ 0.40 against ≈ 0.29 without them, and the benchmark's claim is made conditional on it. |
| **L2 all-rows selectivity** | **FAIL as registered** (a negative margin); **undecided** under the centred sensitivity at 40 draws (+0.0263 vs +0.0267, a gap of 0.0004 on a half-width of 0.0148 that 20 more draws did not move) | the fields add +0.026 of R²(x) over the level-free control on all rows (Phase 5's 93 % reduction from +0.39) | reported; not resolvable by more draws at this panel's n (P6-13) |
| **L2b** (E6.7's derived gate) | **FAIL** — +0.0295 [+0.0237, +0.0352] (gate's construction) and +0.0181 (the audit's) against −0.0023 as registered and +0.0105 centred | the fields' macro-phase selectivity is small (Phase 5 cut it from +10.4 pp to +1.8 pp) and above a margin that is a tenth of the frozen 10 pp | (i) the same field decisions as the calm-trained row (the multiple and the yield are the slow signals a phase clock reads); (ii) accept and state: the fields tell a reader the macro phase ≈ 2–3 pp better than the price path does |

The plan's own note on **G3** (16A: "G3 will fail unless D8 changes the horizon or the scoring") was written at a
half-life of 150 d; at the FIT 22.4 d the 100-seed run counts medians of 2–6 oracle switches per 200-day run and
**G3 passes** at θ = 0.05 (section 3.8b). The expectation in `PREREG_PHASE_6.md` section 12 is recorded as
disconfirmed — a measurement, not a criterion moved.

## 6. Files written or changed

`PHASE_6_CHANGED_FILES.md`, generated from git (`0b2c48c..HEAD`) and the working tree by
`tools/phase6/e6_changed_files.py` and verified against disk by its `--check` (111 paths; 0 deleted; 0 empty on disk
— an empty generated file is not a result, P5-12). In outline: `envs/` one file (`observables_params.py`'s
`AUDIT_BOUNDS` entries that name Phase 6); `evaluation/` two added (`criteria.py`, `reference_stats.py`), two
modified (`leakage_audit.py` — the switches; `stylized_facts.py` — `run_checklist_reference` appended,
`run_checklist` untouched) and the parameter file `params/phase6_criteria.json`; `tools/phase6/` the phase's
tools (E6.9, E6.1, E6.3, E6.2, E6.5, E6.6 bound and null, the criteria blocks, 16A, L3, the after-state chain, the
report tables, the cite check, the changed-files generator, the box bootstrap); `tests/` `test_v2_1_phase_6.py`
(11 tests), the registry re-expressed (`known_defects.py`, `test_leakage_ci.py`), the re-frozen manifest; `docs/`
the pre-registration and its addendum, this report, the E6 appendix (`spec/CALIBRATION_REPORT.md`, the v2 draft
archived), the spec's section 7, the decision log's P6 rows, and the generated results under
`generated/v2_1/e6_*` and `e6_after*`.

## 7. What was not done, and who owns it

| item | state | owner |
|---|---|---|
| **L3** (the LLM probe) | built and dry-run, **not run**: 200 probes from day 22 on, the entitled reader's surrogate 0.780 [0.718, 0.832], ceiling 0.837, permutation null p95 0.57 (`e6_l3/l3.json`); the roster and ≈ $12 are D2's | the team (D2); `tools/phase6/e6_l3_probe.py --models …` runs it |
| **The box** | every number here is the laptop's; the reproduction check **passed** after the phase's last audit (stage 3: SAME GENERATOR at 1e-9, both reference rows exact; `e6_0/box_stage3.log`, P6-15) — the box is a reference machine for sklearn stages from Phase 7 on, when the tunnel answers | Phase 7 (use it); Fan (the tunnel) |
| **The known-defect registry** | not emptied: both entries re-expressed as the derived gates and standing (strict xfails that XPASS when a gate passes) | Phase 7 / D17 |
| **The all-rows L2 centred reading** | undecided at 40 draws (0.0004 on a half-width of 0.0148); more draws cannot resolve it; a larger panel could | Phase 7, if the team wants it decided |
| **Item 3** (volatility clustering) | mis-specified for T = 200 — E6.9 measures 23–28 % power of its rules against the generator's own GJR shape; judged under B/C and reported, not re-specified | the team's reading of the checklist (D17) |
| **Item 12** (sentiment's next-day loading) | the realised partial slope 0.00055 [0.00046, 0.00063] against the configured 0.0008 — FAIL, a fidelity question for the sentiment block | D15's owner |
| **Item 7** (log-volume normality) | the generator is *more* log-normal than real volume (median Shapiro p 0.224 vs 0.004): a mis-specified criterion in both forms, reported | Phase 7 (the volume block's reference) |
| **16A's oracles** | trained on 240 paths, the count Phase 5 used; a larger training pool is a D17 option, stated as a re-run of the checkpoint, not a repair | D17 |
| **The L2 per-scenario reading inside the audit** | the held-out table is the audit's per-scenario statement; `l2_surrogate` itself still reports by phase group pooled over scenarios | Phase 7 |
| **The E6.1 IV reference** | VIX against an S&P / FF-market / set-A proxy plus five single-stock IV indices (166 windows); no single-stock IV panel matched to the 417 names exists in `datasets/` | reported as the reference's limit (section 3.2) |
