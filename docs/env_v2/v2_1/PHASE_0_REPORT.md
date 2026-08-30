# Phase 0 report (v2 → v2.1): verification and freeze

Date: 29 August 2026. Working tree at commit `b61fe07` plus the 27-Aug documentation restructure; nothing committed, no
branch, no paid API call. Governing documents: `V2_1_IMPROVEMENT_PLAN.md` Section 4 and `PREREG_PHASE_0.md` (written before
any run, not moved afterwards). Phase 0 contains **no design decision**: every code change makes an implementation match its
own documentation or removes a silent override; every hidden and rendered path column except the analyst field is
bit-identical before and after (`generated/v2_1/path_hashes_{before,after}.json`, 95 configurations, 0 non-analyst changes).

**Status: Phase 0 complete; stopping for review. Phase 1 not started.** Team decisions needed for Phase 0: none. Still
blank and needed later: D1 and D13 (Phase 1), D16 (which programme first), D10 (before Phase 5), D2 (Phases 6, 8, 9).

---

## 1. Literature review

The plan says "none needed; this phase is about the repository's own claims", and that holds: no parameter, threshold or
range was set from a source in Phase 0. Three external statements are *quoted* (never used as a tolerance) and one internal
document was read; their status per the plan's rule:

| Statistic / statement | Where used | Status | Source, date |
|---|---|---|---|
| SABCEMM DCA-HPM average chartist share 0.2285 (simulated, 200 runs × 7,000 steps) | printed beside the engine's chartist share in `test_fundamentalist_share` and in the findings table; **no tolerance** (Phase 2's E2.1 supplies it) | read-and-correct by the third pass, 26 Aug 2026 (LOG §4.2: the plan's "0.17 / 10" was the DCA-WHP row); not re-read in Phase 0 | arXiv:1812.02726, Table 1 |
| Franke & Westerhoff 2012: p_t is the log price, so the misalignment term takes natural-log deviations (`price_scale = 1`) | the deck note's statement that the switching is inert at scale 100; no code change (Phase 2) | read-and-correct by the third pass, 26 Aug 2026 (LOG §4.4) | JEDC 36:1193–1211, Bamberg PDF (`.../Westerhoff/Publications/2011/JEDC_RF_FW_Fin.pdf`) |
| Absolute target-price error ≈ 45 % (Bradshaw, Brown & Huang 2013; Bilinski et al. 2013) | quoted in the observables docstring as the read anchor Phase 5 will use; **not** adopted in Phase 0 (the documented 0.15 is kept, labelled DESIGN) | read-and-correct by the third pass (LOG §4.3) | RAST 2013; TAR 2013 |
| Execution-order rule "Anything that changes the environment or the prompts after step 0 restarts from step 0: re-freeze, re-audit, new hashes" and the smoke gate ("100 percent of calls parsed; every run has all rows; provenance columns filled; rendered prompt matches the published sample") | rule 0.6 (adopted; DECISION_LOG P0-11) | read in Phase 0 from the docx (paragraphs 14 and 59 of the extracted text), 29 Aug 2026 | `docs/planning/FinPersona-Bench_Experiment_Execution_Order_Aug2026.docx` |

The provisional tolerances of the strict-xfail tests (z ≤ 3 for IV continuity; < 50 % saturated days for the fundamentalist
share; ± 10 % daily-sd difference for the sustained-bull selection) are labelled **DESIGN-provisional** with the phase that
replaces each by a derived value (PREREG §6); they gate only tests that are expected to fail, so they cannot make a claim pass.

## 2. Pre-registration

`PREREG_PHASE_0.md` fixed, before any run: the seed blocks (all fresh: 9001–9005, 10000–10049, 11000–11049, 12000–12009,
13000–13049, 15000–15099, 16000–16099, 17000–17129, 18000–18049; start prices from `default_rng(20000)`), the horizons, the
surrogate and its settings, the statistic and interval for every recomputed finding with the reviewers' value beside it, the
verdict rules R / S / N / D, the bug fixes with their test tolerances and derivations, the freeze contents, the regression tests
and the registry, the no-distribution-change fixture, the sd(x) hypothesis with its numerical prediction, and the deferred list.

Deviations from the pre-registration, all disclosed here:

1. **Bootstrap resamples.** The pre-registration says 2,000 resamples (200 for classifier statistics). The sklearn-based
   statistics used 500 (attacker R², L1 medians), the pure AR(1) and item-10 statistics 1,000, the within-scenario classifier
   60 (each resample refits a 5-fold cross-validated classifier). The intervals are correspondingly rougher (Monte-Carlo error
   of a percentile bound ≈ 0.01 in R² units at 500 resamples; ≈ 0.01 in accuracy at 60). No verdict depends on this precision.
2. **The path-hash fixture was rebuilt.** The first `path_hashes_before.json` hashed the two string columns (`phase`,
   `macro_phase`) through `numpy.tobytes()` on an object array, i.e. pointer values, which are not reproducible (pandas 3.0's
   `str` dtype is not `object`). The tool was fixed (string columns are hashed by their values) and the "before" fixture was
   rebuilt from the pre-fix code exported read-only with `git archive HEAD` (HEAD's `envs/`, `evaluation/`, `simulation/`
   equal the pre-Phase-0 code: the only uncommitted files were documentation). The numeric columns of the first fixture were
   already valid and identical.
3. **The plan's premise about the legacy test was wrong.** Plan §0.3 says `test_bull_trap_generation`'s plateau assertion "was
   true of v1's plateau". It was not: on the frozen v1 at the test's own seed and horizon V moves 100.60 → 96.32 and P_50 =
   125.93 (< 140). The test (March 2026) predates the frozen v1. The v1 facts are asserted positively in
   `test_provenance_and_freeze.py::test_v1_bull_trap_value_plateau_frozen` (E0 record); the v2 test is rewritten to the v2 contract.
4. **One reviewer value re-attributed.** Review C's "FW pull at x = −0.3 is 0.00034/day" corresponds to the index φ = 0.12;
   at the live φ = 0.463 the pull is 0.00139/day. Both are printed; the substance (scripted step ≈ 0.0075/day ≫ pull) holds.

5. **One CI test failed on the frozen state and was registered, not fixed.** After the analyst fix, amendment A6's L1 rule is
   marginal (§3.3): `test_leakage_ci.py::test_v2_L1_no_algebraic_inversion` fails deterministically at the 8 CI seeds (the
   k·analyst candidate is inside the 1 % floor on 6.4 % of steps vs price's 3.6 %) while the 50-seed audit passes by 0.26 pp.
   PREREG §9's rule ("report the failing test with its output; no test is deleted") is applied by making it a strict xfail
   with a registry entry (items 5, 21, 32; Phase 6 after Phase 5) — the pre-registration did not foresee this entry.

Nothing else moved. Where a reviewer's value was not reproduced, the row is N and stays N (§3.2).

## 3. Runs

All results are in `generated/v2_1/`: `findings_reproduction.md` (149 rows), `findings/*.json` (numbers, seeds, intervals),
`phase0_numbers.json` (the canonical numbers the documents and `tests/test_docs_numbers.py` use), `path_hashes_{before,after}.json`.
Compute: `tools/verify_v2_findings.py` 652 s on 8 CPUs (Python 3.13.13, numpy 2.4.6, scipy 1.18.0, pandas 3.0.3,
scikit-learn 1.9.0, statsmodels 0.14.6, arch 8.0.0); the analyst after-run 6 min; checklist re-run 4 min; leakage audit re-run
9 min; L5 re-run 12 min; the full test suite 9 min 05 s (final run).

### 3.1 Findings reproduction (unmodified v2.0 generator, fresh seeds)

Verdicts over 149 rows: **R 97, S 5, N 16, D 31**. Every headline finding holds. The table below gives one line per
weakness item (full rows, intervals and sources in the findings file).

| Item | Finding | Phase 0 (n; 95 % interval) | Reviewer | Verdict |
|---|---|---|---|---|
| 1 | "compare price with 100" rule ≈ oracle | MCR (ISFJ, θ 0.05, PortfolioV2, 5 bp) 0.018 [0.011, 0.027] flat / 0.009 [0.007, 0.013] crash / 0.010 [0.007, 0.013] bull / 0.110 [0.089, 0.129] sustained bull; oracle 0.003 / 0.003 / 0.004 / 0.002; always-hold 0.106 / 0.132 / 0.140 / 0.101; constant band edges 0.04–0.17; random 0.33–0.35 (50 seeds) | 0.014 / 0.007 / 0.005 / 0.098; 0.003; 0.11–0.14 (C, 12 seeds) | R (all four) + S |
| 2, 11 | FW switching inert | n_f > 0.99 on 0.985 [0.978, 0.990] of flat days (0.990 crash, 0.991 bull); mean n_f 0.998; pilot n̄ 0.999 at scale 100, 0.827 at scale 1 (chartist share 0.173) | 0.983 / 0.987 / 0.991; 0.83 (C, LOG) | R |
| 3, 5, 43 | fields leak once the anchor is removed; level-free reader weak | anchored panel (200 paths): level R²(x) 0.849 [0.824, 0.871], sign 0.948; level-free 0.493 [0.431, 0.549], sign 0.736 [0.701, 0.774]; full calm R² 0.814, MAPE(V) 0.042 calm / 0.063 event. Randomised start U(20, 500): level calm R² 0.054 [−0.135, 0.179], event 0.634; full calm 0.653 [0.570, 0.722], sign 0.851, event 0.904, MAPE 0.077; selectivity (full − level, calm) **+0.09 anchored vs +0.60 randomised** | C: level 0.84 / 0.945, level-free 0.40 / 0.71; randomised price-only 0.217 / full 0.779, MAPE 15.3 / 10.1 %; published audit full calm 0.898, price-only 0.787, MAPE 3.5 / 4.9 % | R on 12 rows; N on 4 (my MAPEs lower than C's, my anchored full R² 0.81 vs the audit's 0.90 — different panel composition and one GBT instead of best-of-three); S on both substance rows |
| 4 | flat control biased cheap | mean x −0.068 [−0.107, −0.029]; median −0.058; P(x < 0) 0.632 [0.522, 0.739]; day-1 −0.068; undervalued resolvable steps 0.666 flat, 0.839 crash; jumps off +0.009 [−0.026, 0.044], P(x < 0) 0.466; analytic stationary mean −0.087 | −0.100 / −0.068 / 0.70 / −0.076; 0.74; 0.84; jumps off −0.018 (C, 30 seeds); −0.077 (LOG) | R (all) |
| 5, 20 | L1 candidates; the "≥ 12 % off" headline | median APE: k·P 0.094, k·P/PE 0.131, k·P·DY 0.130, k·analyst 0.240, k·SMA50 0.093, three-term mean 0.107 (p5/p10 1–4 %; 24 % of steps within 5 %) | audit 0.124 / 0.155 / 0.156 / 0.224; B: three-term 9.2 %, 27 % within 5 % | k·analyst R; the others N (my panel is 25 % sustained-bull paths with tiny \|x\|, so every median is lower); substance "three-term beats price" N before the fix (0.107 vs 0.094) and holds after it (0.071 vs 0.094) |
| 6 | calendar is a phase clock in the LLM population | P(calm \| day ≤ 50) = 1.000, P(event \| day ≥ 170) = 1.000 (crash and bull, 2,500 / 1,550 path-days); day-only accuracy 0.828 [0.792, 0.848] crash (majority 0.40), 0.809 [0.781, 0.846] bull (majority 0.49); mixed set 0.535 | 1.000 / 1.000; 0.804 / 0.872; mixed 0.648 (checklist) | R on 5 rows; N on the bull accuracy (0.81 vs 0.87) and the mixed set (0.54 vs 0.65: the mixed-set statistic is seed-unstable) |
| 13 | jumps ↔ kurtosis coupling | flat paths with excess kurtosis > 1.5: 0.78 [0.65, 0.87] current jumps / 0.70 mean-zero / 0.68 no jumps; mean x −0.068 / +0.012 / +0.009 | 0.85 / 0.70 / 0.60 (LOG, 40 seeds); 0.70 / 0.55 / 0.45 (pass-3) | R (all three) — the drop is smaller on these seeds (0.10) than the LOG's 0.25 |
| 16, 47 | script share; mania cap | R² of Δx on the scripted drift: panic 0.063 [0.052, 0.073], stabilisation 0.028, post-top 0.207 [0.132, 0.330], mania 0.009 — the daily changes are GARCH noise, the script sets the level path; mania days at the cap 0.372 [0.325, 0.416]; FW pull at x = −0.30: 0.00139/day (live φ) vs a median scripted panic step of 0.0075/day | cap 38 %; pull 0.00034 (index φ) (C) | R; the script share is new (D) |
| 18, 42 | sustained-bull selection | first attempts 34 accepted / 16 rejected; daily sd 0.0146 [0.014, 0.015] vs 0.0235 [0.020, 0.028] (flat 0.0162); ACF1 −0.031 vs +0.025 (flat +0.007); 20-day sd 0.041 vs 0.070 (flat 0.069); rejection rate under sampling 0.405 [0.306, 0.512] | 33 / 27; 0.0147 vs 0.0240; −0.025 vs +0.024; 0.044 vs 0.080; 39.8 % | R (all) + S |
| 21, 68 | analyst error | pooled sd(u) 0.352 [0.323, 0.377] on benchmark days, 0.335 on the full timeline; median \|u\| 0.247; median \|F/V − 1\| 0.245 [0.228, 0.261] (100 / 200 seeds) | 0.333 / 0.335 analytic; 0.222; 0.224 | R (all) |
| 25 | IV threshold look-ahead | 0.085 [0.064, 0.106] of benchmark days flagged differently by a past-only threshold; 0.659 [0.586, 0.736] of flagged days are panic days | 9 %; 75 % | R |
| 35 | SMM "not identified" | J = 408.2; start-J not recorded; 10 survivor tickers; diagonal proxy W; J-profile 2.89–3.16; pilot n̄ ≥ 0.9954 at every φ of the profile grid (scale 100) | "computed where chartists never act" | R (the regime claim) + D |
| 36, 62, 71 | half-life estimator; the 150 / 188 / 72 / 14 d numbers | sample half-life 20.1 d [16.1, 24.2] at T = 200 (IQR 14–29; 0 % clear 60 d), 61.9 d [55.3, 80.7] at T = 800 (52 % clear 60 d), 174 d at T = 5000; pure AR(1) with true 150 d: 20 / 59 / 96 / 124 d at T = 200 / 800 / 2000 / 5000 (share ≥ 60 d 0.01 / 0.49 / 0.93 / 0.99); true 580 d at T = 800: 84 d; true 60 d: 40 d; pull-rate half-life 150.0 d; cached 20k pilot 188.5 d; five 200k pilots **146.6 d [141.5, 155.4]** | 26 / 72 d; B: 62 / 21 / 98 / 127 / 84 / 41 d, 54 %; 188.5; 147 (141–154) | R (all 13 rows) |
| 71 (sd) | stationary sd(x): 0.13–0.14 vs 0.165 | engine weights: **0.165** (sd_e 0.016) / **0.175** (sd_e 0.017); raw weights (what `pilot_stats` prints): 0.126 / 0.134; ratio 0.762 = w̄ 0.761; full generator T = 5000: 0.196 (jumps on; range 0.13–0.40 over seeds), 0.186 (jumps off) | 0.162–0.169 (LOG) vs 0.131 / 0.140 (pass-3) vs 0.142 (calibration report) | **R for both** — PREREG §8's hypothesis confirmed to three decimals: the two published numbers measure the same engine under different weight normalisations |
| 40 | item 10 fails | event-window partial R² 0.373 [0.295, 0.493]; spread 17.3 pp [15.8, 18.8] | 0.38 / 18.0 | R |
| 41 | "without a cap every run reaches P/V > 3" | with g_max = 1.0: 0.18 [0.10, 0.31] of runs reach P/V > 3 (topped share 0.86, median peak 2.32); live cap: 0.00, topped 0.62, median 1.92 | claim: 100 % (A5, never tested) | **N** — the claim in amendment A5 is false: without the cap the hazard tops the bubble earlier; the cap was not needed for the reason stated |
| 46 | IV phase step | Δlog IV +0.618 [0.591, 0.646] at deterioration → panic (z = 7.7), −0.591 at panic → stabilisation (z = −7.4), +0.172 at calm → event (z = 2.2), +0.324 at blow-off → post-top (z = 4.1); calm day-to-day sd 0.080 [0.073, 0.086] | +0.62 / −0.64 / +0.15 / +0.33; 0.089; z ≈ 7 | R on 5, N on panic → stabilisation (−0.59 vs −0.64; same substance) |
| 48 | one-shot side call | oracle switches per run: median 0.5 / 1 / 1 / 2 (flat / crash / bull / SB); runs with ≥ 2: 0.28 / 0.26 / 0.42 / 0.52; resolvable steps at one band edge 0.945 / 0.864 / 0.763 / 0.810 | 0 / 1 / 1 / 2; 0.25 / 0.45 / 0.30 / 0.55; 77–91 % | R on 7, N on the flat edge share (0.95 vs 0.84; substance stronger) |
| 49 | blow-off label; top day | un-topped 0.38 [0.26, 0.52]; blow-off label starts on day 154–171 in un-topped runs; realised maximum of x on top_day + 1 in 0.58 [0.41, 0.74] of topped runs (max x − x_top = +0.019 ≈ g) | 58 % un-topped; 153–170; off by one | N on the un-topped share (0.38 vs 0.58: 62 % topped on these seeds vs 44–47 % in the calibration — a ± 14 pp statistic at 50 seeds), S on the off-by-one |
| 50 | burn-in | sd(x_1) / long-run sd: 0.83 live (burn-in 1.7 half-lives), **0.61 [0.52, 0.69] `fw_index`** (0.41 half-lives; pilot half-life 628 d), 0.61 pruna | ≈ 0.6 (C) | R |
| 58 | multi-asset | pairwise corr of x 0.546 [0.456, 0.632]; spread-resolvable share 0.866 [0.842, 0.889]; IV / realised vol 1.33 asset 0, **1.41 asset 2** | 0.46–0.65; 0.87; 1.28 vs 1.06 | R, R, R / **N**: the inconsistency exists (asset 2's IV uses the unscaled σ_V) but its sign is the opposite of the reviewer's numbers — asset 2's IV premium is *higher*, not lower |
| 39 | footers | CSV vs `.md`: default 8/7 = 8/7; fw_index 8/7 vs 7/6; pruna 7/8 vs 6/7; hl60 7/8 = 7/8; omega 7/8 vs 6/7; panic3 9/6 vs 8/5; panic6 8/7 vs 7/6 | five of six wrong | R |
| 30, 44, 61 | the n behind the published numbers | items 4 and 9: 20 paths; hazard 60 seeds; audit 150 of 400 paths (30,000 rows; L2 rows 27,000); L5 12 / 10 seeds; sensitivities 25 seeds; pilot 3 scenarios, 1 seed | — | D (table in the findings file and the deck note) |
| 71, 72 | stale statements | 21 located (file:line in the findings file): half-life 60–120 / 90 / 120 / 72 d, sustained-bull 0.25 (spec, calibration report), jump rate 0.008 (decision log, variant table), "four scenarios" (script), 188 d (pilot cache) | — | D; every one corrected or annotated (§6) |
| 66 | test suite before Phase 0 | `pytest tests/ --ignore=tests/test_market_environment.py`: 1 failed (`test_bull_trap_generation`), 68 passed, 3 xfailed in 10 min 07 s; the ignored file cannot collect (`vectorbt` absent) | 68 / 1 / 3 (LOG §8) | R |

### 3.2 Rows not reproduced (N), each with its reason

Sixteen rows are N under the pre-registered rule R (reviewer value outside my interval and outside the two-sample allowance).
None reverses a finding; each is listed with what was found:

- **Panel-composition differences (7 rows).** My anchored panel is 50 seeds × {flat, bull_trap, crash δ 0.70, sustained_bull}
  with one GBT; the published audit's 150 paths mix three crash deltas and event-first paths and take the best of three models;
  review C's randomised-start run used 24 seeds. My full-set calm R² is 0.81 (audit 0.90), my MAPE(V) 4.2 / 6.3 % (audit 3.5 /
  4.9 %), my randomised-start MAPEs 11.2 / 7.7 % (C: 15.3 / 10.1 %); my L1 medians are lower than the audit's for every candidate
  because a quarter of my paths are sustained-bull paths with median \|x\| 0.014. The substance rows (selectivity +0.09 vs +0.60;
  level-free ≪ level) are S.
- **The three-term L1 candidate (1 row).** Before the fix it did *not* beat price on my panel (0.107 vs 0.094); after the fix it
  does (0.071). Review B's 9.2 % came from 64 paths.
- **Seed-set differences in 50-seed shares (5 rows).** Un-topped share 0.38 vs 0.58; bull day-only accuracy 0.81 vs 0.87;
  mixed-set accuracy 0.54 vs 0.65; flat single-edge share 0.95 vs 0.84; panic → stabilisation IV step −0.59 vs −0.64. All have
  the same sign and conclusion; the mixed-set item-15 statistic in particular moves by 11 pp between seed sets, which Phase 4's
  permutation null will replace.
- **Two claims that are false as stated (2 rows).** Amendment A5's "without a cap every run reaches P/V > 3" (18 % do) and the
  reviewer's asset-2 IV/RV ratio 1.06 (it is 1.41; the inconsistency exists but with the opposite sign).
- **The reviewer's index-φ pull (1 row, re-attributed, §2).**

### 3.3 Before / after the analyst fix (same seeds; only the analyst field changed)

| Statistic | Before | After | Documented |
|---|---|---|---|
| pooled sd(u), benchmark days (100 seeds) | 0.352 [0.323, 0.377] | **0.158** | 0.15 |
| pooled sd(u), full 460-day timeline | 0.335 | 0.156 | 0.15 |
| median \|u\| | 0.247 | 0.111 | — |
| median \|F/V − 1\| (200 paths; the deck's "22 %") | 0.245 | **0.112** | — |
| L1 median APE, k·analyst | 0.240 | 0.110 | — |
| L1 median APE, mean(k·SMA50, k·P/PE, k·analyst) | 0.107 | 0.071 | — |
| anchored full-set calm R²(x) / MAPE(V) | 0.814 / 0.042 | 0.841 / 0.039 | — |
| randomised-start full-set calm R²(x) / MAPE(V) | 0.653 / 0.077 | 0.676 / 0.071 | — |
| selectivity full − level, calm R² (anchored / randomised) | +0.093 / +0.599 | +0.120 / +0.623 | — |

The corrected analyst field is *more* informative, not less: a fair-value estimate with a 15 % error is a better estimate of V
than one with a 33 % error. One consequence: amendment A6's L1 rule ("a candidate reproduces V iff it lands inside the 1 % floor
on more steps than price itself + 1 pp") becomes marginal — the k·analyst candidate is inside the floor on 4.8 % of steps vs
price's 4.1 % (50 seeds: PASS by 0.26 pp) and on 6.4 % vs 3.6 % at the 8 CI seeds (FAIL). The rule is not moved; the CI test is
registered (P0-14) for Phase 6's re-derivation of the L1 pass rule from the x noise floor (E6.5). Published audits re-run on the frozen state (§5): 50-seed leakage audit (150 of 400 paths, 30,000 rows): L1 — k·analyst median APE 0.101 (before 0.224), price 0.124, so the analyst candidate now beats price itself and the sentence "no formula beats price" is withdrawn (A6 still passes); L2 absolute gate still FAILS — calm best R²(x) 0.918 (before 0.898), sign 0.974, event 0.966, MAPE(V) 4.5% (before 4.9 %); exploratory selectivity +0.131 R² (before +0.111), MAPE gain +3.2%; shuffled-V -0.061; L2b full 85.2% vs price-only 78.3%, selectivity +6.9 pp (before +6.6) PASS; scenario discrimination recall of sustained-bull days 82.5% / 82.1% / 85.1% (price / price+IV / full); L4 unchanged (x unchanged). L5 (12 / 10 seeds): full-set gap 0.018–0.019 bull/crash, 0.031–0.032 flat, 0.085–0.086 sustained bull (before 0.019 / 0.041–0.042 / 0.071–0.072); price-only unchanged. Every published audit file is regenerated on the frozen state (`generated/leakage_audit_v2.*`, `generated/l5_observables_oracle.*`).

### 3.4 The stationary sd(x) discrepancy, resolved

`pilot_stats` simulates the engine with **raw** innovation weights (n_f σ_f + n_c σ_c ≈ 0.76; `w_norm = 1`), whereas the generator
divides the weight by its pilot mean w̄ = 0.761 so that it has unit mean. The pre-registered prediction (PREREG §8) was sd(x) =
w × sd_e / √(1 − ρ²) with ρ = 1 − μ n̄ φ = 0.99538: 0.167 / 0.177 (engine, sd_e 0.016 / 0.017) and 0.127 / 0.135 (raw). Measured on
five 200,000-step pilots: 0.165 / 0.175 and 0.126 / 0.134; ratio 0.762. So the third pass's 0.162–0.169 (engine) and the pass-3
reviewer's 0.131 / 0.140 and the calibration report's 0.142 (raw pilot) are all right; the documents now state the engine's value
with this explanation. The full generator (GARCH-t + jumps) at T = 5000 gives a heavier-tailed 0.19 (0.13–0.40 across ten seeds).
Consequence for Phase 1: the plan's Appendix B bound should be read at s_x ≈ 0.175 (its "0.165" row: 0.15 / 0.26 / 0.48), not 0.13.

### 3.5 What a 200,000-step normalisation would change (deferred, PREREG §4.5)

n̄ 0.99765 → 0.99734, w̄ 0.76113 → 0.76154, φ 0.46319 → 0.46333 (+0.03 %). Small, but it moves every path; the change is
Phase 2's (which re-derives φ). Phase 0 applies the long pilot only to the *reported* statistics (`long_pilot_stats`).

## 4. Decisions with evidence

Thirteen entries P0-1 … P0-13 in `decisions/DECISION_LOG.md` (Phase 0 section), amendment A9 in
`preregistration/PREREGISTRATION_AMENDMENTS.md`. None is a design decision. In brief:

| # | Decision | Label |
|---|---|---|
| P0-1 | Analyst error: the documented AR(1) (ρ 0.95 per weekly update, sd 0.15) is authoritative; the √5 removed | DESIGN (the 0.15; Phase 5 decides its value) |
| P0-2 | MCR normalisation: labels made exact (constant-mix ceiling, worst-trivial floor); pilot `norm_mcr` annotated; convention → Phase 7 | A9 |
| P0-3 | Day-1 gate: common-start cells only; ΔC_1 table exploratory; re-specification → Phase 7 | A9 |
| P0-4 | Hazard: module constants = calibrated values; loud loader | CAL (unchanged) |
| P0-5 | Engine named `fw_fallback_hl150`; `fw_single` requires an accepted estimate; `engine_used` in metadata; `Gen_Config_Hash` changes for every future run (the engine string changed), no path changes | CAL (unchanged) |
| P0-6 | Half-life statements unified (150.0 d pull rate; 147 d long pilot; 20 d / 62–72 d sample; 188 d withdrawn) | — |
| P0-7 | sd(x): engine 0.165 / 0.175; raw pilot 0.126 / 0.134; explanation recorded | — |
| P0-8 | 200,000-step re-normalisation deferred to Phase 2 | — |
| P0-9 | Item 73: trader band (0, 1); t-mixture, crash μ_V = 0, $1 threshold documented | DESIGN (documented) |
| P0-10 | Footers regenerated from CSVs | — |
| P0-11 | Freeze manifest and its regeneration rule; execution-order step-0 rule adopted; smoke gate kept for Phases 8/9 | — |
| P0-12 | Legacy tests: skip / rewrite; the v1 plateau never held | — |
| P0-13 | Known-defect registry; acceptance = empty | — |

Deferred because it would change a path's distribution, or because it is a later phase's design decision: everything in PREREG §10
(start price → Phase 1 under provisional B; jump placement → Phases 1/3; FW units and engine → Phase 2; the 200k normalisation →
Phase 2; IV → Phase 3; the control → Phase 4; MCR convention and the gate → Phase 7; L2 gate → Phase 6; every parameter
provenance → Phases 1–5; slides and script → Phase 10).

## 5. Regression tests

`tests/test_v2_1_stats.py` (seed blocks and derivations in PREREG §6), `tests/test_v2_1_phase_0.py`, `tests/test_docs_numbers.py`,
`tests/test_v2_freeze.py`, `tests/known_defects.py`, `tests/conftest.py` (prints the registry at the end of every session).

| Test | Criterion (tolerance provenance) | Outcome |
|---|---|---|
| `test_flat_x_unbiased` | \|x̄\| ≤ 1.96 SE, 100 flat seeds (size 5 %; power vs −0.087 ≈ 1) | **xfailed (strict)** — defect 4, Phase 1 |
| `test_analyst_error_sd` | pooled sd(u) within ± 10 % of 0.15 at 100 seeds (≈ 2.2 SE; the √5 defect detected with power ≈ 1) | **passes** (0.158 → +5.3 %) |
| `test_iv_continuity` | z ≤ 3 at the panic transitions (DESIGN-provisional → Phase 3) | **xfailed (strict)** — z ≈ 7.7 / −7.4; defect 46, Phase 3 |
| `test_fundamentalist_share` | share of days with n_f > 0.99 < 0.50 (majority boundary; the SABCEMM 0.2285 printed with no tolerance → Phase 2) | **xfailed (strict)** — 0.985; defects 2, 11, Phase 2 |
| `test_half_life_consistency` | five 200,000-step pilots, \|mean ACF(1) half-life − pull-rate half-life\| ≤ 8 d (Bartlett SE 7.0 d per pilot, 3.1 d for the mean; size ≈ 1 %) | **passes**: 146.6 d vs 150.0 d (hard test, as the plan states) |
| `test_sustained_bull_selection` | accepted vs rejected daily sd within 10 % (DESIGN-provisional → Phase 4) | **xfailed (strict)** — 38 % quieter; defects 18, 42, Phase 4 |
| `test_leakage_ci.py::test_v2_L2_surrogate_thresholds` | unchanged | **xfailed (strict)** — items 5, 32; Phase 6 |
| `test_leakage_ci.py::test_v2_L1_no_algebraic_inversion` | unchanged (A6 rule) | **xfailed (strict), new in Phase 0** — the analyst fix made the A6 rule marginal (fails at the 8 CI seeds, passes by 0.26 pp at 50); items 5, 21, 32; Phase 6 after Phase 5 (P0-14) |
| `test_v2_1_phase_0.py` (11 tests) | footers = CSV; MCR label = code; gate common-start only; hazard loader loud; engine named honestly and a renamed REJECTED file cannot switch it; trader band-free; $1 threshold named; no √5 in the analyst block; registry = strict xfails; paths unchanged | **all pass** |
| `test_docs_numbers.py` (11 tests) | code constants and documents vs `phase0_numbers.json`; no stale phrase in the descriptive documents; stale decision-log lines annotated; sensitivity counts | **all pass** |
| `test_v2_freeze.py` (4 tests) | manifest covers every generator file and matches; `Env_Code_Hash` = manifest hash; sensitive to any module and line-ending independent | **4 pass** (after the manifest was written) |

Known-defect registry (v2 section, printed at the end of every session): defects 4/13 → Phase 1; 2/11 → Phase 2; 46/25 → Phase 3;
18/42 → Phase 4; L2 gate 5/32 → Phase 6; L1 rule (A6) 5/21/32 → Phase 6 after Phase 5. v1 baseline xfails (2) are permanent.

**Suite state.** Before Phase 0: 1 failed, 68 passed, 3 xfailed (10 min, slow audit file included; `test_market_environment.py`
could not collect). After Phase 0, fast suite (`--ignore=tests/test_leakage_ci.py`): 81 passed, 3 skipped (the freeze tests before
the manifest existed), 4 xfailed, 0 failed (3 min 43 s). Full suite on the frozen state: `python -m pytest tests/ -q` (every file, the slow audit file included): **103 passed, 1 skipped (`test_market_environment.py`, `vectorbt` absent), 8 xfailed (the six registered v2 defects and the two permanent v1 records), 0 failed, in 9 min 05 s**, with the known-defect registry printed at the end. An earlier full run on the same frozen state had failed `test_v2_L1_no_algebraic_inversion` (§2, deviation 5); that test is now the sixth registry entry.

The MixedLM `ConvergenceWarning` from `test_review_additions.py::test_windowed_stats_and_sign_flip` is still emitted (Phase 8 must
not silence it without explanation).

**Freeze.** `tests/v2_freeze_manifest.json`, label "Phase 0 freeze", 17 files, manifest hash `92ddcf527be61986e180c78d3ec69270cfaeea779b240f0fb9b709c9d094edc2` (`Env_Code_Hash` = `92ddcf527be61986`). `Env_Code_Hash` for every v2 run is now the
first 16 hex characters of that manifest hash (`simulation/provenance.py::env_provenance`); a change to any file in
`envs/v2/**/*.py`, `envs/synthetic_market.py`, `envs/v2/params/*.json` or the six evaluation modules changes it. Rule adopted
(execution-order step 0): any environment or prompt change after a freeze restarts from step 0 — re-freeze (`python -m
tools.freeze_manifest --write`, logged in the decision log), re-audit, new hashes; the main grid runs only on the freeze of Phase 10.

**No-distribution-change check.** `python -m tools.path_hashes --compare`: 95 configurations, 0 non-analyst column changes,
190 analyst-column changes (both analyst columns of every configuration — the declared fix). The 50-seed checklist re-run on the
frozen state reproduces the published `checklist_v2.md` line for line except item 15's within-scenario mean (73.6 % → 73.7 %,
the classifier's own RNG); the re-run is now the published file.

## 6. Documentation

Corrected (all numbers of §3 written into them; `tests/test_docs_numbers.py` guards them):
- `spec/E1_V2_GENERATOR_SPEC.md`: engine name and half-life numbers (§2); sustained-bull multiplier 1.0 (§4); analyst fix (§6);
  8 / 7 / 5 and the n per item, item 9's 72 d as estimator-biased, item 14 after the re-run (§7).
- `spec/CALIBRATION_REPORT.md`: engine, pilot and long-pilot numbers (§1); multiplier (§1); the n note (§2); audit tables after the
  re-run (§4); sensitivity counts (§5); L5 after the re-run with the corrected reading (§7).
- `decisions/DECISION_LOG.md`: five stale statements annotated in place with "[Phase 0 correction …]" (the signed record is not
  rewritten); the Phase 0 section (P0-1 … P0-13).
- `preregistration/PREREGISTRATION_AMENDMENTS.md`: A9.
- `status/E1_E4_STATUS.md` (5 n-a; A8 note; Phase 0 status), `status/PILOT_NOTES.md` (normalisation label; exploratory ΔC_1 table;
  three scenarios; the defective analyst field), `generated/README.md` (footers; v2.1 group; pilot files), `README.md` (status;
  regeneration commands).
- `envs/v2/mispricing.py`, `envs/v2/observables.py`, `envs/v2/generator.py`, `envs/v2/events.py`, `evaluation/metrics_v2.py`,
  `evaluation/leakage_audit.py`, `tools/report_v2.py`: docstrings and printed interpretations corrected (the L2 "hidden from the
  fields, not from price dynamics" sentence withdrawn).
- `DECK_CORRECTIONS_NOW.md`: the one-page note (0.2b) — slide by slide, what is on the slide and what is true.
- Regenerated machine-written files: `generated/table2_v2_from_code.*` and `rendered_prompt_v2_*.txt` (analyst value and hashes),
  `generated/checklist_v2.{md,csv}` (re-run), the six `checklist_v2_sens_*.md` footers, `generated/leakage_audit_v2.*`,
  `generated/l5_observables_oracle.*`, `generated/pilot_report.md` and `pilot_report_exploratory_deltaC1_start_at_target.csv`
  (the stale `pilot_report_gate_start_at_target_deltaC1.csv` removed).

Not touched, by rule: `envs/v1/`, `docs/planning/`, `docs/env_v2/v2_1/archive/`, the deck and the speaker script (Phase 10;
the deck note is the interim correction).

## 7. What could block the next phase

- Phase 1 needs D1 (data substitutes vs WRDS) and D13 (provisional start-price mechanism B) approved, and D16 (full programme
  vs minimal path) chosen; none is taken. E1.0 also needs a historical-constituent source (the Wikipedia table is gone).
- The sd(x) result (0.175, not 0.13) changes the s_x row Phase 1's Kalman tabulation should treat as the reference.
- The Phase-0 finding on amendment A5 (the cap was not needed for the stated reason) and the multi-asset IV sign are new inputs
  for Phases 4 and 9.

## 8. Files written or changed in Phase 0

Nothing was committed, stashed or pushed; no branch was created; `envs/v1/`, `docs/planning/` and `docs/env_v2/v2_1/archive/`
were not touched. The `.gitignore` modification in the working tree predates Phase 0 (the 27-Aug restructure) and was left as it
is; by its rules everything under `docs/env_v2/v2_1/` (this report, the pre-registration, the deck note) is local-only and does
not appear in `git status`.

**New — Phase 0 deliverables (documents):** `docs/env_v2/v2_1/PREREG_PHASE_0.md`, `docs/env_v2/v2_1/PHASE_0_REPORT.md`,
`docs/env_v2/v2_1/DECK_CORRECTIONS_NOW.md`.

**New — generated results:** `docs/env_v2/generated/v2_1/findings_reproduction.md`, `docs/env_v2/generated/v2_1/findings/*.json`
(23 blocks before the fix, 3 after), `docs/env_v2/generated/v2_1/phase0_numbers.json`, `docs/env_v2/generated/v2_1/path_hashes_before.json`,
`docs/env_v2/generated/v2_1/path_hashes_after.json`, `docs/env_v2/generated/pilot_report_exploratory_deltaC1_start_at_target.csv`.

**New — tools:** `tools/verify_v2_findings.py`, `tools/path_hashes.py`, `tools/freeze_manifest.py`, `tools/regen_checklist_md.py`.

**New — tests:** `tests/known_defects.py`, `tests/conftest.py`, `tests/test_v2_1_stats.py`, `tests/test_v2_1_phase_0.py`,
`tests/test_docs_numbers.py`, `tests/test_v2_freeze.py`, `tests/v2_freeze_manifest.json`.

**Changed — code:** `envs/v2/observables.py` (analyst √5 removed; docstring), `envs/v2/mispricing.py` (`ENGINE_DEFAULT`,
`load_params` without silent fallback, `long_pilot_stats`, docstrings), `envs/v2/generator.py` (hazard constants + loud loader,
engine default, t-mixture docstring), `envs/v2/events.py` (`G_MAX` = 0.012; crash μ_V note), `envs/synthetic_market.py` (engine
default, `engine_used`, Table 2 texts), `evaluation/metrics_v2.py` (`V1_RULE_HOLDINGS_THRESHOLD`; `floors_and_ceilings` docstring),
`evaluation/leakage_audit.py` (printed L2 interpretation), `simulation/provenance.py` (freeze manifest; `Env_Code_Hash` for v2),
`simulation/runner_v2.py` (engine default; trader band (0, 1)), `tools/report_v2.py` (gate on common-start only; exploratory ΔC_1
table; normalisation text), `tools/calibrate_hazard.py` (default `g_max`), `tests/test_env_logic.py` (rewritten to the v2
contract), `tests/test_market_environment.py` (`importorskip("vectorbt")`), `tests/test_provenance_and_freeze.py` (v1 bull-trap
record), `tests/test_v2_generator.py` (engine-name assertion).

**Changed — documents:** `docs/env_v2/README.md`, `docs/env_v2/spec/E1_V2_GENERATOR_SPEC.md`, `docs/env_v2/spec/CALIBRATION_REPORT.md`,
`docs/env_v2/decisions/DECISION_LOG.md` (five in-place annotations + the Phase 0 section), `docs/env_v2/preregistration/PREREGISTRATION_AMENDMENTS.md`
(A9), `docs/env_v2/status/E1_E4_STATUS.md`, `docs/env_v2/status/PILOT_NOTES.md`, `docs/env_v2/generated/README.md`.

**Regenerated machine-written files (on the frozen state):** `docs/env_v2/generated/checklist_v2.{md,csv}`, the six
`checklist_v2_sens_*.md` (footers), `leakage_audit_v2.{md,pkl}` + `leakage_audit_v2_{L1,L2,checklist_rows}.csv` (`_L4.csv` unchanged),
`l5_observables_oracle.{md,csv}`, `table2_v2_from_code.{md,json,tex}`, `rendered_prompt_v2_{static,memory}.txt`, `pilot_report.md`.

**Deleted:** `docs/env_v2/generated/pilot_report_gate_start_at_target_deltaC1.csv` (replaced by the exploratory file above).

Scratch-only (not in the repository): the fixes patch script, the `git archive HEAD` tree used to rebuild the before-hash fixture,
the run logs, the dry-run outputs.
