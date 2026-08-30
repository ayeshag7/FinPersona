# Pre-registration, Phase 0 (v2 → v2.1): verification and freeze

Status: **written 29 August 2026 before any Phase-0 run**, on the working tree at commit `b61fe07` (plus the uncommitted
documentation restructure of 27 Aug). Governing document: `V2_1_IMPROVEMENT_PLAN.md` Section 4 (Phase 0) and Section 1
(protocol). Phase 0 contains **no design decision**: nothing that changes a path's distribution by design is touched;
every code change either makes an implementation match its own documentation or removes a silent override. No paid API
call is made. Nothing is committed. Team decisions needed: none (plan Section 15, row "0").

Everything below — seeds, horizons, estimators, statistics, tolerances and the verdict rules — is fixed here and is not
moved after the numbers are seen. If a rule turns out to be wrong it is said so in `PHASE_0_REPORT.md`, the replacement
is derived in a separately documented step, and the result is reported under both.

## 0. Provenance labels used in this phase

LIT / FIT / CAL / DESIGN as defined in the plan. Phase 0 introduces no FIT value. Two provisional test tolerances
(§6) are labelled **DESIGN-provisional** with the phase that replaces them by a derived value; they gate strict-xfail
tests only (a strict xfail keeps the suite green while the defect persists and alerts when it disappears), so they
cannot make any claim pass.

## 1. Seeds, horizons, estimators (fixed)

All seeds are new: none coincides with the reviewers' (0–29, 24 seeds, 40 seeds), the plan's dry run (7000+, 8000+) or
the 27-Aug re-runs (777, 778). Generator: `envs/synthetic_market.py` / `envs/v2/` **unmodified** for every
reproduction run (the "before" state); the analyst-field statistics are re-run once after the bug fix (§4.1) and
reported before/after on the same seeds.

| Block | Purpose | Seeds | Horizon |
|---|---|---|---|
| S200 | main T = 200 panel: flat, bull_trap, sustained_bull, crash at δ ∈ {0.55, 0.70, 0.85} (δ 0.70 where one δ is used) | 10000–10049 (50 per scenario) | 200 |
| S800 | persistence at T = 800 (flat, phase-free) | 11000–11049 (50) | 800 |
| S5000 | stationary sd and half-life of the engine inside the full generator (flat) | 12000–12009 (10) | 5000 |
| SMULTI | 3-asset crash δ 0.70, vol scale [1, 1, 0.5], ρ_common 0.3 | 13000–13049 (50) | 200 |
| SAR1 | pure Gaussian AR(1) simulations for the estimator-bias table, true half-life ∈ {60, 150, 580} d, T ∈ {200, 800, 2000, 5000} | `default_rng(14000)`, 200 paths per cell | as stated |
| SANALYST | analyst error statistics (the block needs no price path) | 15000–15099 (100) | 460-day timeline (burn-in 260 + 200) |
| SFLAT100 | `test_flat_x_unbiased` | 16000–16099 (100), flat | 200 |
| SIV30 | `test_iv_continuity` | 17000–17029 (30), crash δ 0.70 | 200 |
| SNF30 | `test_fundamentalist_share` | 17100–17129 (30), flat | 200 |
| SSB50 | sustained-bull first-attempt selection (reproduction and `test_sustained_bull_selection`) | 18000–18049 (50) | 200 |
| SPILOT | long calm-engine pilots (Gaussian innovations, no events, no jumps): five pilots | 9001–9005 | 200,000 steps each |
| SSTART | randomised start prices: P_1 ~ U(20, 500) per path, drawn from `numpy.random.default_rng(20000)` in path order, applied to the S200 seeds (the reviewer's design, review C §A.2–3) | — | 200 |
| Bootstrap | cluster bootstrap over paths (seeds), 2,000 resamples (200 for the classifier statistics), `default_rng(0)`, percentile 95 % interval | — | — |

Surrogate (where used): `HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6, random_state=0)`
with `GroupKFold(5)` grouped by path — the `gbt` model of `evaluation/leakage_audit._models()`, so that the numbers are
comparable with the published audit. Lags: 5, plus returns at 1/5/20 d, as in `add_lags_and_returns`.

Feature sets for the attacker comparison (review C §A.2–3):
- **level** = the audit's `PRICE_ONLY_KEYS` (price, SMA20, SMA50, trend_strength, trend_regime, RSI14, MACD, MACD_signal) + lags + returns;
- **level-free** = ret_1, ret_5, ret_20, log(P/SMA20), log(P/SMA50), RSI14, MACD/P, MACD_signal/P, trend_strength, trend_regime, each with 5 lags (no level);
- **full** = all 18 rendered numeric fields + lags + returns (the audit's full set).

Compute: 8 CPUs, Python 3.13.13, numpy 2.4.6, scipy 1.18.0, pandas 3.0.3, scikit-learn 1.9.0, statsmodels 0.14.6,
arch 8.0.0 (recorded in the report).

## 2. Findings to be recomputed (`tools/verify_v2_findings.py` → `generated/v2_1/findings_reproduction.md`)

Each row states the statistic, the design, the interval and the reviewer's value that will be printed beside mine.
"Rev." cites the source: A/B/C = the three reviews (`docs/env_v2/reviews/`), W = `V2_WEAKNESSES.md`, LOG = the
verification log, PLAN = plan §0.1.

| Item(s) | Statistic (mine) | Design | Interval | Reviewer value (source) |
|---|---|---|---|---|
| 1 | MCR at θ = 0.05 of the rule "cash → band-high if log(P/100) > 0.05, band-low if < −0.05, else unchanged" (ISFJ band 0.70–0.90, start 0.80), executed through `PortfolioV2` at 5 bp like every baseline, beside the mandate-conditional oracle, always-hold, constant-mix and the two constant band-edge policies; also the direct (no-execution) scoring of the same rule | S200 × {flat, crash δ 0.70, bull_trap, sustained_bull} | cluster bootstrap over seeds | rule 0.014 / 0.007 / 0.005 / 0.098 (flat / crash / bull / SB), oracle 0.003, always-hold 0.11–0.14 (C §A.2, 12 seeds); direct: 0.022 / 0.011 / 0.007 / 0.083, oracle 0.000, always-hold 0.100 (LOG §1) |
| 2, 11 | share of days with n_f > 0.99 and mean n_f, per scenario; deterministic pilot n̄ at `price_scale` 100 vs 1 (20,000 steps, seed 12345, the cached pilot's design) and in the five 200,000-step pilots | S200; SPILOT | cluster bootstrap | 0.983 / 0.987 / 0.991 flat / crash / bull (C §A.1, 10 seeds); n̄ 0.997–0.999; scale 1 → n̄ 0.83 (C; LOG §1: 0.9985 / 0.8268) |
| 3, 5, 43 | attacker R²(x) (calm / event / all), sign accuracy on resolvable steps, MAPE(V), for feature sets level / level-free / full, on (a) the anchored panel (P_1 = 100) and (b) the randomised-start panel (SSTART) | S200 × {flat, bull_trap, crash δ 0.70, sustained_bull} = 200 paths per panel | cluster bootstrap over paths of the OOS predictions | (b) price-only calm R² 0.217, sign 0.768, event R² 0.730, MAPE 15.3 %; full calm 0.779, sign 0.862, event 0.904, MAPE 10.1 % (C §A.3, 24 seeds); (a) level R² 0.84 / sign 0.945; level-free 0.40 / 0.71 (C §A.2); published 50-seed audit: full calm 0.898, price-only 0.787, MAPE 3.5 / 4.9 % (`leakage_audit_v2.md`) |
| 4 | flat: mean of the path-mean x, pooled median x, P(x < 0), mean x_1, share of resolvable steps (\|x\| ≥ 0.05) with x < 0; crash: share of resolvable steps with x < 0; flat with `jumps=False`: mean x, P(x < 0); analytic stationary mean −(0.010 × 0.04)/(μ n̄ φ) | S200 flat and crash δ 0.70; jumps-off on the same seeds | cluster bootstrap over seeds | −0.100 / −0.068 / 0.70 / −0.076; 74 %; crash 84 %; jumps off −0.018, 0.50 (C §A.4, 30 seeds); −0.077 (SE 0.019), 0.71, −0.087, jumps off +0.009 / 0.46; analytic −0.087 (LOG §1) |
| 5, 20 | L1 candidates on the anchored panel with the audit's `l1_algebraic` (k·P, k·P/PE, k·P·DY, k·analyst): median APE and p5/p10/p25; the extended candidate "mean of k·SMA50, k·P/PE, k·analyst" (per-candidate k as in the audit): median APE and share of steps within 1 / 2 / 5 % | S200 panel (a) | percentile bootstrap over paths of the median | k·P 0.1236, k·P/PE 0.1546, k·P·DY 0.1558, k·analyst 0.2235 (`leakage_audit_v2.md`, 150 paths); three-term mean 9.2 %, 27 % within 5 %, p5/p10 1–4 % (B row 5, 64 paths) |
| 6 | setup-first crash and bull_trap: P(calm \| day ≤ 50), P(non-calm \| day ≥ 170); day-only macro-phase classifier accuracy within scenario (HGB depth 3, GroupKFold 5) vs the majority share; the mixed-set accuracy of checklist item 15 on the same seeds | S200 crash δ 0.70 and bull_trap; mixed set as `checklist_paths` builds it, on the S200 seeds | Wilson 95 % for the shares; the classifier accuracy with a seed-cluster bootstrap (200 resamples) | 1.000 / 1.000; 80.4 % crash, 87.2 % bull vs majority 40 / 54 % (C §C.20, 40 seeds); mixed 64.8 % (`checklist_v2.md`) |
| 13 (coupling with 4) | flat: share of paths with excess kurtosis > 1.5 (checklist definition: `scipy.stats.kurtosis` of daily log returns over the 200 benchmark days) and median kurtosis, under {current jumps, mean-zero jumps (`jump_mean = 0`), no jumps}; mean x under each | S200 flat, same seeds | Wilson / bootstrap | 0.85 / 0.70 / 0.60 (LOG §2, 40 seeds); 0.70 / 0.55 / 0.45 on another definition (pass-3 review) |
| 16, 47 | event phases: script share = R² of Δx_t on the scripted drift d_t (the driver re-run in lock-step on the stored path, which reproduces d_t exactly) within panic, stabilisation and post-top; share of mania days at the drift cap g_max; FW pull at x = −0.30 (μ n̄ φ × 0.30) at the live φ and at the index φ, beside the scripted step size | S200 crash δ 0.70 and bull_trap | cluster bootstrap | cap share 38 %; pull 0.00034/day vs script ≈ 0.01/day (C §A.8; the 0.00034 corresponds to the index φ = 0.12) |
| 18, 42 | sustained_bull first attempts (`reject=False`, then `check_validity`): accepted / rejected counts, daily sd of log returns, ACF(1) of returns, sd of 20-day returns in each group; flat daily sd and ACF(1) on the same seeds; the rejection rate under rejection sampling | SSB50 | bootstrap over paths within group | 33 / 27; sd 0.0147 vs 0.0240; ACF1 −0.025 vs +0.024 (flat); 20-d sd 0.044 vs 0.080; daily sd 0.0148 vs 0.0181 (C §A.5, 30 seeds); 32 / 18, 0.0153 vs 0.0210, rejection 0.36 (LOG §1); published rate 39.8 % (`checklist_v2.md`) |
| 21, 68 | analyst error u: pooled sd over benchmark days and over the full 460-day timeline, median \|u\| on benchmark days; analytic 0.15 √5 = 0.335; **after the fix** the same on the same seeds | SANALYST; also S200 crash δ 0.70 (the reviewers' design) | cluster bootstrap | 0.335 / measured 0.333 (C §D.24); 0.338, median APE 0.21 (B row 6); 0.350 / 0.262 (PLAN, 30 crash × 460 d); 0.306 / 0.330 / 0.222 (LOG §1) |
| 25 | share of benchmark days whose IV stress flag differs between the full-path 0.9 quantile (as implemented: burn-in + benchmark, i.e. including the future) and a past-only expanding-window 0.9 quantile; share of flagged days (full-path rule) in crash paths that are panic days | S200 crash δ 0.70 | Wilson / bootstrap | 9 %; 75 % (C §A.7) |
| 35 | documentary from `fw_single_stock.REJECTED.json` and `fw_J_profile.csv` (J = 408; start-J absent; maxiter 150; 10 survivor tickers; diagonal proxy W; J-profile range) **plus** the pilot n̄ at every φ of the profile grid at `price_scale` 100 (20,000 steps, seed 12345) to show the regime in which the profile was computed | deterministic | none | n_f ≈ 1 throughout (B row 12, C §A.1) |
| 36, 62, 71 | (a) sample half-life −ln2/ln ACF(1) of x on calm windows: T = 200 (S200 flat: median, IQR, share ≥ 60 d, within-window sd of x), T = 800 (S800), T = 5000 (S5000); (b) SAR1 table: median sample half-life and share ≥ 60 d for true half-life {60, 150, 580} × T {200, 800, 2000, 5000}; (c) the engine's long pilots (SPILOT): ACF(1)-implied half-life, mean n_f, sd(x) with raw weights (`w_norm = 1`, as `pilot_stats` measures) and with the engine's unit-mean weights, at sd_e 0.016 and 0.017; the cached 20,000-step pilot (seed 12345): ACF(1) → half-life; the pull-rate half-life ln2/(μ n̄ φ) from the live parameters | as stated | percentile bootstrap for medians/shares; the pilots are deterministic | 26 d (30 flat) / 72 d (20 T = 800) / 55 % (PLAN); 35 / 65 / 60 % (LOG); 14 d calm windows (C §B.15); HL 150 at T = 800: 62 d [28–140], 54 %; T = 200: 21 d; T = 2000: 98; T = 5000: 127; HL 580 at T = 800: 84 d; HL 60: 41 d (B row 9); cached pilot 188.5 d; five 200k pilots 141–154 d, mean 147; 142 and 160 (LOG §1; pass-3 review); pull rate 150.0 d; sd(x) 0.162–0.169 (LOG) vs 0.131 / 0.140 (pass-3 review) vs 0.142 (`CALIBRATION_REPORT.md`) |
| 40 | checklist item 10 on 50 crash seeds × 3 δ: event-window MDD partial R² of δ (controlling D_V) and the spread δ 0.55 vs 0.85, with a seed-cluster bootstrap interval | S200 crash × {0.55, 0.70, 0.85} | cluster bootstrap | 0.38 / 18.0 pp (`checklist_v2.md`, 150 paths) |
| 41 | bull_trap with `g_max = 1.0` (the cap effectively removed; `reject=False`): topped share, share of runs with peak P/V > 3, median peak P/V; the same with the live cap | S200 bull_trap | Wilson / bootstrap | claim "without a cap every run reaches P/V > 3" (A5), never tested (B row 34) |
| 46 | mean change in log IV at deterioration → panic and panic → stabilisation (crash), calm → mania and blow-off → post-top (bull), calm day-to-day sd of log IV, z = mean change / calm sd | S200 crash δ 0.70 and bull_trap | cluster bootstrap | +0.62 / −0.64 / +0.15 / +0.33; sd 0.089; z ≈ 7 (C §A.6, 30 + 30 seeds); +0.606 / −0.619, sd 0.086, z 7.06 (LOG) |
| 48 | ISFJ oracle at θ = 0.05: number of target switches per run (median; share with ≥ 2), share of resolvable steps at a single band edge (max over the two edges), per scenario | S200 × 4 scenarios | bootstrap | medians 0 / 1 / 1 (flat / crash / bull), 77–91 % (C §B.15, 30 seeds); 0 / 0 / 1 / 2 and 0.23–0.27 (LOG §2); 0 / 1 / 1 / 2 and 0.25 / 0.45 / 0.30 / 0.55 (pass-3 review, 20 seeds) |
| 49 | bull_trap: un-topped share; blow-off start day in un-topped runs (min–max); in topped runs the share whose realised maximum of x over the run occurs at `top_day + 1` (the off-by-one) | S200 bull_trap | Wilson | 58 % un-topped; blow-off from day 153–170; top one step early (C §A.11–12) |
| 50 | sd of x on day 1 across seeds for engines `fw_single` (live), `fw_index`, `pruna`, beside the long-run sd of x of each engine (200,000-step pilot); ratio and the burn-in in half-lives | S200 flat (50 seeds per engine) | bootstrap | fw_index: x_1 sd ≈ 0.6 σ_stat, 0.45 half-lives (C §A.9) |
| 58 | 3-asset crash: mean pairwise correlation of x across assets (per seed, then across seeds), spread-resolvable share (max_i x_i − min_i x_i ≥ 0.05), IV / realised-21-day-vol ratio for asset 0 and asset 2 | SMULTI | cluster bootstrap | corr 0.46–0.65; 0.87; 1.28 vs 1.06 (C §G.41, 10 seeds) |
| 39 | pass / fail counts of every `checklist_v2*.csv` versus the footer of the matching `.md` | the seven generated files | none | five of six footers wrong: index 8/7 vs 7/6, omega 7/8 vs 6/7, panic3 9/6 vs 8/5, panic6 8/7 vs 7/6, pruna 7/8 vs 6/7 (W 39, LOG §5) |
| 44, 30, 61 | the n behind every published headline number (documentary table compiled from the generated files and the code): checklist items 4 and 9 (20 paths), hazard (60 seeds), audit (150 of 400 paths after `MAX_ROWS`), L5 (12 / 10 seeds), sensitivities (25 seeds), pilot (3 scenarios, 1 seed) | documentary | none | W 30, 44, 61; B row 1 |
| 71, 72 | every stale statement located (file:line) — half-lives (60–120, 90, 120, 150, 187/188, 72, 14), sustained-bull multiplier 0.25, jump rate 0.008 | grep | none | W 71, 72; A §3 |
| 66 | the state of the test suite before Phase 0 (`pytest tests/ -q --ignore=tests/test_market_environment.py`, slow audit file included, and the collection error of the ignored file) | run | none | 60 passed / 1 failed without the slow file (PLAN §0.3); 68 passed / 1 failed / 3 xfailed with it (LOG §8) |

Items 7, 8–10, 12, 14, 15, 17, 19, 22–24, 26–34, 37–38, 45, 51–57, 59–60, 63–65, 67, 69–70, 73–74 are **documentary**
(provenance, citations, code facts, statements): the script records the code fact or file reference that establishes
each where one exists (e.g. `hazard.json` values vs the module constants for 69; the `fw_single` fallback path for 70)
and the report lists them with the phase that closes them; no statistic is recomputed for them.

## 3. Verdict rules (fixed before the runs)

For each computational row the script prints my value with its n and interval, the reviewer's value with its n, and one
verdict:

- **R (reproduced):** the reviewer's point value lies inside my 95 % interval; or, when the reviewer's n is stated, the
  two estimates differ by less than 1.96 × √(SE_mine² + SE_mine² × n_mine / n_rev) (the reviewer's SE taken as mine
  scaled by the square root of the seed ratio); for deterministic quantities (pilots, code facts, footer counts): equal
  at the stated rounding.
- **S (reproduced in substance):** R fails but the qualitative finding holds in my data — the sign, the ordering or the
  pass/fail conclusion stated in the weakness item (e.g. "the rule is within 0.02 of the oracle in three scenarios and
  fails in the sustained bull"; "the T = 800 estimator cannot separate 150 from 580 d").
- **N (not reproduced):** neither.
- **D (documentary):** no statistic.

"Reproduced" in the report means R; S is reported as S with the numbers, never upgraded.

## 4. Bug fixes (implementation ≠ documentation) and the tests that lock them

Every fix below is checked against the "no distribution change" fixture of §7. A fix that would move any hidden path
(P, V, x, phase, n_f, σ, sentiment, volume, IV, EPS, dividends) is **not** applied in Phase 0 and is listed as deferred.

### 4.1 Analyst error (item 68) — `envs/v2/observables.py::analyst_block`
- Documented: u AR(1) with ρ = 0.95 per 5-day update, stationary sd 0.15 (`observables.py` docstring, `TABLE2_DEFINITIONS`, spec §6, slide 5).
- Implemented: innovation sd 0.15 √(1 − ρ²) **× √5**, giving stationary sd 0.15 √5 = 0.335.
- Fix: remove the √5. ρ and 0.15 are unchanged (whether 0.15 is right is Phase 5's question).
- Consequence (declared): only `analyst_fair_value` and `analyst_error_u` change; every other column is bit-identical (§7).
- Test `test_analyst_error_sd` (hard): 100 seeds (SANALYST), pooled sd of u over the 460-day timeline within ± 10 % of 0.15.
  Derivation of the tolerance: 92 updates per seed × 100 seeds = 9,200 AR(1) updates at ρ = 0.95 → effective n ≈
  9,200 × (1 − ρ)/(1 + ρ) ≈ 236 → relative SE of the sample sd ≈ 1/√(2 × 236) ≈ 4.6 %, so ± 10 % is ≈ 2.2 SE (size ≈ 3 %);
  the √5 defect (+ 124 %) is detected with power ≈ 1.

### 4.2 Sensitivity footers (item 39) — `docs/env_v2/generated/checklist_v2_sens_*.md`
- The `.md` footers were written by an earlier version of `to_markdown`; the CSV tables are the record. Fix: regenerate
  every sensitivity `.md` from its CSV with the current `to_markdown` (title and preamble preserved) and add
  `test_footer_counts_match_csv` (all seven files).

### 4.3 MCR normalisation labels (item 53) — `evaluation/metrics_v2.py`, `tools/report_v2.py`, `PILOT_NOTES.md`
- Code: for every lower-is-better metric (including `mcr_0.05`) the ceiling is `constant_mix` and the floor the worst of
  {always_buy, always_sell, random}. Documents: "ceiling = mandate-conditional oracle, floor = best trivial policy".
- Fix (labels only): the docstring of `floors_and_ceilings` states the convention exactly; `report_v2.py`'s text and
  `PILOT_NOTES.md` say "normalised against constant-mix"; a test asserts the docstring and the returned ceiling agree.
  The convention v2.1 adopts (and the regret decomposition) is Phase 7; the pre-registration's RG-type rule (ceiling =
  mandate oracle) is logged as amendment A9 (labelling discrepancy, unresolved until Phase 7). No number changes.

### 4.4 Day-1 gate input (item 54) — `tools/report_v2.py::salience_tables`
- Fix: the gate is computed on common-start cells only; the start-at-target ΔC_1 table is renamed
  `exploratory_deltaC1_start_at_target` and carries the reason (a level gate fed a difference); `test_gate_common_start_only`.
  Re-specification is Phase 7. The pilot report is regenerated from `results_v2_pilot/` so that the published tables
  carry the new labels; every per-run metric is expected to be unchanged (checked by diff).

### 4.5 Silent overrides (items 69, 70) — `envs/v2/generator.py`, `envs/v2/events.py`, `envs/v2/mispricing.py`
- `HAZARD_H0`, `HAZARD_B` (generator) and `G_MAX` (events) are set to the calibrated values 3e-4, 6.0, 0.012; the loader
  raises at import if `params/hazard.json` is missing or disagrees with them.
- `engine="fw_single"` raises unless `params/fw_single_stock.json` exists **and** carries `"accepted": true`; the
  fallback is the explicitly named engine `fw_fallback_hl150` (same parameters, φ = 0.4632, `price_scale` 100), which
  becomes the default engine name in `GenConfig`, `SyntheticMarketEnv`, `RunConfig`; `get_metadata()` records
  `engine_used` (the parameter set actually loaded). Consequence (declared): `Gen_Config_Hash` of every future run
  changes because the engine string changes; no path changes (§7). Tests: `test_hazard_loader_is_loud`,
  `test_engine_named_honestly`, `test_rejected_file_cannot_switch_engine`.
- `pilot_stats` (20,000 steps, seed 12345) keeps setting w̄ and n̄ (they determine φ and the innovation weight, hence
  every path); the plan's "re-run at 200,000 steps" is applied to the **reported** pilot statistics (half-life, sd) via a
  new `long_pilot_stats` that does not touch the normalisation cache. The φ and w̄ that a 200,000-step normalisation
  would give are computed and reported, and the change is **deferred to Phase 2** because it would move every path.

### 4.6 Half-life and stale numbers (items 71, 72)
- Every document states: pull-rate half-life 150.0 d (CAL); long-pilot ACF(1) half-life = the SPILOT value (reported with
  its range); sample half-life at T = 200 and T = 800 = the S200 / S800 medians (estimator-biased, stated); stationary
  sd(x) = the value established under §8 with the explanation; sustained-bull variance multiplier 1.0; jump rate 0.010;
  the pilot covered three scenarios. The 188 d figure is removed everywhere. Stale statements are corrected in place
  with a "[Phase 0 correction]" marker where the document is a signed record (`DECISION_LOG.md`), and rewritten where
  it is a description (spec, calibration report, docstrings). `test_docs_numbers.py` checks the canonical numbers
  against `generated/v2_1/phase0_numbers.json` and the absence of the stale phrases.

### 4.7 Item 73
- Runner trader band (0.4, 0.6) → (0.0, 1.0), the band-free convention of the metrics; `test_trader_band_free`.
- The common factor's t-mixture documented as "not t(5)" (generator docstring, spec).
- Crash V drift = 0 after deterioration documented as a stated choice pending Phase 4 (events.py, spec).
- The $1 holdings threshold of `v1_rule` named as a constant and documented.

### 4.8 Scenario and seed counts (items 44, 30)
- "four scenarios" → three wherever it appears (speaker script listed in the deck note; PILOT_NOTES already says three);
  the n-behind-the-number table (§2, row "44, 30, 61") goes to the report and the deck note.

## 5. Freeze (0.3)

`tests/test_v2_freeze.py` with the manifest `tests/v2_freeze_manifest.json`: SHA-256 of every file matching
`envs/v2/**/*.py`, `envs/synthetic_market.py`, `envs/v2/params/*.json`, `evaluation/{stylized_facts, leakage_audit,
observables_oracle, metrics_v2, baselines_v2, targets}.py`, hashed after normalising CRLF → LF (checkout-independent);
the manifest hash = SHA-256 of the sorted "path:hash" lines. `simulation/provenance.py::env_provenance` returns
`Env_Code_Hash` = the first 16 hex characters of the runtime manifest hash for a v2 environment (the v1 environment
keeps the single-file hash, so the E0 test is unchanged). The manifest is written once at the **end** of Phase 0, after
every code change, by `python -m tools.freeze_manifest --write`; any later regeneration is a logged decision.

## 6. Regression tests (0.4) and the known-defect registry

`tests/test_v2_1_stats.py` (seed blocks of §1):

| Test | Design | Criterion | Provenance of the tolerance | Status now (predicted) | Owner |
|---|---|---|---|---|---|
| `test_flat_x_unbiased` | SFLAT100, mean of path means x̄, SE = sd of path means / √100 | \|x̄\| ≤ 1.96 SE | size 5 %; power vs the −0.087 bias: SE ≈ 0.013 → z ≈ 6.7, power > 0.999 | fails (defect 4) → `xfail(strict=True)` | Phase 1 |
| `test_analyst_error_sd` | §4.1 | ± 10 % of 0.15 | §4.1 | passes after the fix | hard |
| `test_iv_continuity` | SIV30, z = mean Δlog IV at det→panic and panic→stab / calm day-to-day sd of log IV | z ≤ 3 | DESIGN-provisional: 3 calm-sd is the boundary a Gaussian day-to-day change reaches on 0.3 % of days; Phase 3 replaces it by the 95th percentile of the realised-variance change-point statistic | fails (z ≈ 7) → strict xfail | Phase 3 |
| `test_fundamentalist_share` | SNF30, share of days with n_f > 0.99 (pooled), mean chartist share | share < 0.50 (switching active on at least half the days, the majority boundary of "inert"); the mean chartist share is printed against SABCEMM's DCA-HPM 0.2285 (LOG §4.2, read 26 Aug 2026) with **no tolerance in Phase 0** — Phase 2's E2.1 supplies it | DESIGN-provisional (Phase 2) | fails (0.98) → strict xfail | Phase 2 |
| `test_half_life_consistency` | SPILOT: five 200,000-step calm pilots, Gaussian innovations sd 0.017, engine weight normalisation; statistic = mean over pilots of −ln2/ln ACF(1) of x; reference = ln2/(μ n̄ φ) from the live parameters (n̄ = the pilot's realised share) | \|mean − reference\| ≤ 8 d | Bartlett SE of ACF(1) for an AR(1) at ρ = 0.99538 over 200,000 steps = √((1 − ρ²)/n) = 2.15 × 10⁻⁴; delta method → 7.0 d per pilot, 3.1 d for the mean of five; 8 d ≈ 2.6 SE of the mean (size ≈ 1 %); the withdrawn 188-d figure would be rejected with power ≈ 1 | passes (hard test from Phase 0, as the plan states) | hard |
| `test_sustained_bull_selection` | SSB50 first attempts, accepted vs rejected daily sd | \|sd_acc − sd_rej\| / sd_rej ≤ 0.10 | DESIGN-provisional; Phase 4 replaces it by the KS-distance upper-limit bound | fails (0.015 vs 0.021–0.024) → strict xfail | Phase 4 |
| `tests/test_leakage_ci.py::test_v2_L2_surrogate_thresholds` | unchanged | unchanged | pre-registered L2 gate | strict xfail (items 5, 32) | Phase 6 (gate derived) after Phases 1 and 5 |

`tests/known_defects.py` lists every strict-xfail test of the v2 generator with the item numbers and the owning phase; a
meta-test asserts that the set of strict xfails collected in `tests/` equals the registry (v1 baseline xfails are listed
in a separate, permanent section); the registry is printed at the end of every pytest session (conftest hook). v2.1
acceptance: the v2 section is empty.

## 7. No-distribution-change check

Before any edit, `generated/v2_1/path_hashes_before.json` records, for seeds 0–9 × {flat, bull_trap, sustained_bull,
crash δ 0.55 / 0.70 / 0.85} (setup-first) and seeds 0–4 × {crash, bull_trap} event-first, seeds 0–4 × engines
{fw_index, pruna, ar1, fw_hl60} (flat) and seeds 0–4 of the 3-asset crash, T = 200: the SHA-256 of every `env.data`
column (exact bytes), separately for the analyst columns. After every Phase-0 code change the same tool
(`tools/path_hashes.py`) must reproduce every non-analyst hash exactly (`path_hashes_after.json`, compared by
`tests/test_v2_1_phase_0.py::test_phase0_paths_unchanged`). The analyst columns are expected to differ. The 50-seed
checklist is re-run on the frozen state and must be identical line for line to `checklist_v2.md` (it uses no analyst field).

## 8. The stationary sd(x) discrepancy (0.13–0.14 vs 0.165): hypothesis and prediction

The plan holds the third pass's 0.162–0.169 until reproduced. Hypothesis H (from reading `mispricing.py` before any
run): `pilot_stats` measures sd(x) with **raw** weights (`w_norm = 1.0`, weight ≈ n_f σ_f + n_c σ_c ≈ 0.76), whereas the
generator runs with unit-mean weights (raw / w̄ ≈ 1), so the pilot's sd understates the engine's by the factor w̄.
Prediction (analytic, AR(1) with ρ = 1 − μ n̄ φ = 0.99538): sd(x) = w × sd_e / √(1 − ρ²) = 10.4 × w × sd_e, i.e.
**0.167 (engine weights, sd_e 0.016) / 0.177 (sd_e 0.017)** and **0.127 / 0.135 (raw weights)**. If the five SPILOT
pilots give ≈ 0.16–0.18 with engine weights and ≈ 0.13–0.14 with raw weights, both published numbers are reproduced and
the discrepancy is a normalisation artefact; the documents then state the engine's value with this explanation and
the pilot's raw-weight value as what `pilot_stats` prints. If the prediction fails, the report says so and the
documents keep the reproduced 0.13–0.14 as the plan instructs. The full-generator value (S5000, with GARCH-t and jumps,
`jumps=True` and `jumps=False`) is reported beside both.

## 9. Reporting rules if a criterion is not met

- A finding marked N stays N; the report states which reviewer number could not be reproduced and what was found.
- A test predicted to pass that fails (e.g. `test_half_life_consistency`) is reported as failing; the tolerance is not
  moved; a corrected derivation, if any, is a separate documented step.
- If the "no distribution change" check fails for any fix, that fix is reverted and listed as deferred.
- If the fast suite is not green after 0.5, the failing tests are reported with their output; no test is deleted.

## 10. Explicitly not done in Phase 0 (deferred, with the owning phase)

Start-price mechanism (1; Phase 1, D13 provisional B); jump placement and E[x] (4, 13; Phases 1, 3); FW units and the
engine decision (2, 11; Phase 2); the 200,000-step re-normalisation of w̄ / n̄ (Phase 2); IV construction (25, 46;
Phase 3); the sustained-bull control (18, 42; Phase 4, D14); MCR convention and decomposition (52, 53; Phase 7); the
day-1 gate re-specification (54; Phase 7); the L2 gate derivation (5, 32; Phase 6); every parameter provenance item
(8–34; Phases 1–5); slides and script (74; Phase 10 — the immediate corrections note is Phase 0's `DECK_CORRECTIONS_NOW.md`).
