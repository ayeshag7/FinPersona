# FinPersona-Bench synthetic environment: improvement plan v2 → v2.1

Status: **draft for review, 26 August 2026. No code was changed, no paid API was called, nothing was committed.** Execution starts only after this plan is approved, one phase at a time, with a written report and a stop for review at the end of every phase.

Scope: every item in `docs/env_v2/reviews/V2_WEAKNESSES.md` (74 items, plus the "what a robust v3 would need" list), the three reviews in `docs/env_v2/reviews/`, and the hard rules in `docs/env_v2/v2_1/V2_IMPROVEMENT_PROMPT.md`. The result is the same environment in the same repository, called **v2.1**.

Conventions used below. T = 200 trading days for the benchmark unless stated. "Path" = one (scenario, seed, delta) run of the generator. "Level-free" = features that do not depend on the price level (returns, ratios to moving averages, RSI, MACD/P). Provenance labels for every number: **LIT** (a specific published statistic, cited), **FIT** (estimated on a stated dataset by a stated method, with an interval), **CAL** (a calibration target: tuned to meet a criterion, and labelled as such wherever it is reported), **DESIGN** (a choice that evidence cannot decide, presented with its alternatives and consequences, chosen by the team, never by the implementer's preference). Nothing may be adopted with the label PLAN, ARB or "conventional".

Note on file locations: while this plan was being written the `docs/` tree was reorganised. The research notes are now in `docs/planning/env_v2_research/` (not `docs/env_research/`), the earlier review rounds in `docs/reviews/cycle1/` and `docs/reviews/cycle2/`, and the plan document in `docs/planning/`. Paths below use the new layout.

---

## 0. What was verified before writing this plan

Everything in this section was recomputed on 26 August 2026 from the working tree at commit `b61fe07` (the first tool run of this session; nothing in the repository was modified). Seeds and sample sizes are stated with every number.

### 0.1 Review findings reproduced (30 seeds per scenario unless stated)

| Item | Finding | Reproduced value (n) | Reviewer's value |
|---|---|---|---|
| 4 | Flat "control" biased cheap by jumps | mean x = −0.100, median −0.068, P(x<0) = 0.70, day-1 mean −0.076 (30 seeds × 200 d); with `jumps=False`: mean −0.018, P(x<0) = 0.50 | −0.100 / −0.068 / 0.70 (C.4) |
| 2, 11 | FW switching inert at `price_scale = 100` | share of days with n_f > 0.99 = 0.981 (flat, 30 seeds); pilot n_bar 0.999 at the index set; **with `price_scale = 1` the index set gives n_bar = 0.827, i.e. a 17 % chartist share** (20,000-step pilot) | 0.983–0.991 (C.1); FW's published mean chartist share ≈ 0.17 |
| 68 | Analyst error implemented at sd ≈ 0.34, documented 0.15 | pooled sd(u) = 0.350, median \|u\| = 0.262 (30 crash paths × 460 d) | 0.335–0.338 (B.6, C.24) |
| 46 | IV is a one-day phase step at panic onset | mean jump in log IV at deterioration→panic = +0.594 (×1.81); calm day-to-day sd of log IV 0.084; z = 7.1 (30 crash seeds) | +0.62, z ≈ 7 (C.6) |
| 18, 42 | Sustained-bull rejection selects the quiet sub-population | first-attempt paths: 17 accepted (daily sd 0.0150) vs 13 rejected (0.0242); rejection rate 0.38 (30 seeds) | 33/27, 0.0147 vs 0.0240 (C.5); 39.8 % (checklist 17) |
| 36 | Half-life is an estimator artefact | sample half-life median 26 d at T = 200 (30 flat paths), 72 d at T = 800 (20 paths); only 55 % of T = 800 paths clear the 60-day floor | 14 d on calm windows, 72 d at T = 800, 54 % clear (B.9) |
| 1 | Fixed start price is an answer key | ISFJ regret (MCR at θ = 0.05, 12 seeds): "compare price with 100" rule 0.014 flat / 0.007 crash / 0.005 bull-trap / 0.098 sustained-bull vs true-value oracle 0.003 and always-hold 0.11–0.14 | 0.014 / 0.007 / 0.005 / 0.098 (C.2) |
| 71 | Half-life numbers inconsistent | fallback φ = 0.463 gives pilot ACF(1) 0.9963 → 188 d, not the 150 d it was set for; `fw_index` at either `price_scale` gives ≈ 610 d | 187 d (B.14) |

Conclusion: the headline findings hold. Two of them are stronger than the reviews said: the FW units question is close to settled (Section 5, Phase 2) and the "72-day realised half-life" clears its own floor on barely half the paths.

### 0.2 Units of the Franke–Westerhoff model (evidence gathered today)

Pruna, Polukarov & Jennings (2016, arXiv:1604.08824, text extracted from the PDF): "their core demand D^f_t is proportional to the gap (p^f_t − p_t), where p_t is the **log price** of the asset at time t, while p^f_t is the fundamental log value" and chartist demand is proportional to (p_t − p_{t−1}) "where p_t and p_{t−1} are the log prices". The FW 2012 noise levels (σ_f = 0.758, σ_c = 2.087) with μ = 0.01 give daily price changes of order 0.76–2 %, which is only consistent with natural-log units for p. Together with the reproduced chartist share (0.17 at `price_scale = 1` vs 0.001 at 100), the evidence says the misalignment term must be `alpha_p * x^2` with x in natural-log units, i.e. `price_scale = 1`. Phase 2 confirms this against the FW 2012 PDF itself (the Bamberg copy is reachable: `www.uni-bamberg.de/.../JEDC_RF_FW_Fin.pdf`) before anything is changed.

### 0.3 State of the test suite

`python -m pytest tests/` cannot collect: `tests/test_market_environment.py` imports `legacy_market_data`, which needs `vectorbt` (not installed). Excluding that file and the slow audit file, the suite gives **60 passed, 1 failed in 9 min 21 s**: `tests/test_env_logic.py::test_bull_trap_generation` asserts that the fundamental value stays flat (|V_1 − V_50| < 1) in a bull trap, which was true of v1's plateau and is false by design in v2 (V grows at μ_V; observed 100.0 → 106.2 over 50 days). These two are the "two legacy tests" of item 66; neither is a v2 defect. `tests/test_leakage_ci.py::test_v2_L2_surrogate_thresholds` is a **strict xfail**: a green CI currently requires the L2 leak to persist (item 66). The statistics tests emit MixedLM convergence warnings, which Phase 8's re-specification must not silence without explanation.

### 0.4 Data, compute and API facts that shape the plan

- **No CRSP, Compustat, OptionMetrics, I/B/E/S or RavenPack access** exists in this environment. This is the single biggest constraint on the "fit on data" rule. Free substitutes that were checked reachable today: Yahoo Finance via `yfinance 1.6.0` (one ticker-month downloaded in 8 s; raw HTTP is rate-limited with 429, the library handles it), Kenneth French data library, FRED (VIX history), Robert Shiller's monthly S&P data, CBOE index files, Damodaran's datasets. Not yet checked but public: SEC EDGAR XBRL company-facts API and Financial Statement Data Sets (quarterly EPS, dividends, book values for every US filer, 2009 onwards); the San Francisco Fed Daily News Sentiment Index; AAII weekly survey; Baker–Wurgler monthly index. Section 3 lists what each substitute can and cannot deliver and the survivorship bias it carries.
- Python 3.13; `arch 8.0` (GARCH fitting), `statsmodels 0.14.6`, `scikit-learn 1.9`, `scipy 1.18` installed; `lightgbm`, `numba`, `pandas_datareader` not installed. 8 CPUs.
- Generator cost: about 0.15–0.2 s per 200-day path including observables (after a 1 s warm-up for the FW pilot cache); a 200-seed checklist (about 1,900 paths) is a few minutes on 8 cores; the 50-seed leakage audit (sklearn surrogates) takes about 10–20 minutes.
- API keys present in `.env` (names only): OpenAI, Gemini/Google, Anthropic, HF. No DeepSeek or OpenRouter key, so the roster is Gemini, OpenAI and Anthropic models unless keys are added.
- Prompt sizes measured from the pilot: system prompt 5,583 characters (≈ 1,400 tokens), per-step human message ≈ 1,700 characters (≈ 450 tokens), output ≈ 120 tokens (JSON plus a 357-character rationale on average); the stateful rolling-20 arm averaged 19,700 context tokens per call (pilot log). Per 200-day run this gives ≈ 0.38 M input and 0.024 M output tokens (stateless) and ≈ 3.9 M input tokens (stateful).
- Prices used for the cost tables (checked 26 Aug 2026): Gemini 2.5 Flash $0.30 / $2.50 per M input/output tokens (Flash-Lite $0.10 / $0.40); GPT-5 mini $0.125 / $1.00 after OpenAI's July 2026 cuts; Claude Sonnet 5 $2 / $10, Haiku 4.5 $1 / $5, Opus 5 $5 / $25 (batch endpoints at 50 % where used). Per stateless run: Flash ≈ $0.17, GPT-5 mini ≈ $0.07, Haiku 4.5 ≈ $0.50, Sonnet 5 ≈ $1.00 (≈ $0.6 with system-prompt caching), Opus 5 ≈ $2.5. Per stateful run: Flash ≈ $1.2, GPT-5 mini ≈ $0.5, Sonnet 5 ≈ $8.

---

## 1. How every phase is run (the protocol)

Every phase follows the same six steps, in this order, and its report is organised under the same six headings.

1. **Literature review.** For each parameter or criterion in the phase: the sources, the specific statistic each source reports (with table/page), what it can and cannot justify (index vs single stock, monthly vs daily, US vs global), and the range the literature gives. Numbers recalled from memory are marked "(to verify)" until read from the source; the phase report only cites what was read.
2. **Pre-registration, written before any run** (`docs/env_v2/v2_1/PREREG_PHASE_k.md`): the data or seeds, horizons, estimators, the exact statistic, the pass/fail or decision rule, the power analysis that sets the sample size, and what will be reported if the rule is not met. Thresholds are not moved after data are seen. If a pre-registered criterion turns out to be wrong, that is stated, the empirical reference distribution is derived in a separate documented step, and results are reported under both the old and the new criterion.
3. **Runs.** Every result is saved under `docs/env_v2/generated/v2_1/` with the seed list, horizon, path count and the generator hash, so the phase report can be regenerated.
4. **Decision with evidence** (`DECISION_LOG.md`, one entry per decision): the alternatives, the evidence for each, why the others were rejected, the provenance label (LIT/FIT/CAL/DESIGN). Deviations from the v2 plan go to `PREREGISTRATION_AMENDMENTS.md`. Where evidence cannot decide, the entry says so and lists the options with consequences; the phase stops and asks.
5. **Regression tests** that lock the decision in (`tests/test_v2_1_phase_k.py`): statistical tests with pre-registered tolerances and the seed count that gives them power, plus the hash freeze.
6. **Documentation**: the phase report (`docs/env_v2/v2_1/PHASE_k_REPORT.md`), updates to the spec, calibration report, I/O contract, and the claims ledger (Phase 10) so that no document carries a number the generated files do not support.

Reporting rules that apply everywhere: every number carries its n (seeds, horizon, paths) and a 95 % interval where one can be computed (cluster bootstrap by path for pooled statistics); before/after comparisons use the same window, estimator and seed count; failures are reported as failures; every tuned parameter is labelled CAL where it appears.

Power-analysis rules (formulas in Appendix A): for a share-type criterion the seed count is set so that a true share 5 pp on the wrong side of the criterion is detected with 80 % power at α = 0.05 (about 420 paths for a criterion at 0.80); for a median or correlation criterion the seed count is set so that the bootstrap 95 % half-width is at most one fifth of the width of the acceptance band; for generator-vs-real comparisons the two-sample size is set so that a Kolmogorov–Smirnov equivalence bound of 0.10 has 80 % power. Seed counts that come out of these rules are stated in each phase; where a rule would need more compute than the phase budget, the phase says so and reports the achieved power instead of pretending.

Git: everything stays on `main`, in the working tree; no commit, amend, reset, stash or push unless asked in that message. At the end of each phase the report lists the changed files. Points at which a commit or tag would be natural are marked "(commit point, if you wish)". The frozen v1 code and the plan document are never modified.

---

## 2. Weakness-to-phase map

Every item of `V2_WEAKNESSES.md` is assigned to exactly one phase that closes it; items that several phases touch are listed under the closing phase with the contributing phases in brackets.

| Phase | Items closed |
|---|---|
| 0 Verification and freeze | 39, 44 (count of scenarios), 53, 54 (input bug; re-specification in 7), 65, 66, 68, 69, 70, 71, 72, 73 (crash V drift statement, trader band, t5 sum, $1 threshold), 74 (list only; corrected in 10) |
| 1 Value and price structure | 1, 3 (level-free audit; field redesign in 5), 4, 5 (restated after the level-free audit), 8, 9, 13 (where jumps belong; rate in 3), 43 (level-free L5), 50 |
| 2 Mispricing engine | 2, 10, 11, 35, 36, 38 (ar1 included), 62 |
| 3 Volatility | 12, 14, 25, 46, 47 (mania drift: 4), 73 (GARCH fit on regime paths) |
| 4 Events, schedule, controls | 6, 15, 16, 17, 18, 19, 41, 42, 47, 49, 51, 58 (shared event; per-asset start in 1) |
| 5 Observables | 3, 20, 21, 22, 23, 24, 34 (undocumented observable constants), 45 |
| 6 Audits and checklist methodology | 5, 7 (the tile: what was tuned), 30, 31, 32, 37, 40, 61, 63, 64, 67 (held-out scenario, L3 probe) |
| 7 Targets, action and metrics | 26, 27, 33, 48, 52, 53 (convention), 54, 56, 60 |
| 8 Harness and statistics | 28, 55, 57, 59, 60 (placebo matching), 67 (random slopes, bootstrap CIs) |
| 9 Sensitivity through the LLM harness | 8, 10, 12, 20, 21, 23 (LLM-grid sensitivities), 29 (multi-asset provenance sensitivities) |
| 10 Documentation, slides, script | 7, 44, 45, 63, 74 |

Items 34 and 73 are split by module: the constants that belong to the generator are documented in the phase that owns the module; harness constants in Phase 8.

---

## 3. Data sources, their substitutes and their biases

The hard rules require every parameter to be fitted or tested on data. The datasets the reviews name are not available here, so the plan states what will be used instead, what it cannot deliver, and where that leaves a parameter literature-anchored with a sensitivity instead of fitted.

| Need | Ideal source (unavailable) | Substitute (checked / to check) | What it delivers | Known bias, and how it is handled |
|---|---|---|---|---|
| Daily prices and volume, ≥ 100 US large caps, 2000–2024 | CRSP | Yahoo Finance via `yfinance` (checked); Stooq as a second source for cross-checks | adjusted close, volume; enough for GARCH fits, variance ratios, volume models, drawdown/run-up episodes, real 200-day windows | survivorship: only currently listed tickers download. Mitigation: build the universe from the historical S&P 500 constituent list (Wikipedia's "changes" table, cross-checked with two other public lists) and download every ticker that still resolves; report the share of delisted names that could not be retrieved and, for the statistics that survivorship affects most (tails, drawdown depths, volatility level), report the result on the survivor sample beside the literature value for the full universe |
| Quarterly fundamentals (EPS, dividends, book value), report dates | Compustat | SEC EDGAR: XBRL company-facts API (one call per CIK) and the quarterly Financial Statement Data Sets (to check) | quarterly EPS (basic/diluted), DPS, filing dates (10-Q/10-K), 2009–2025, all filers | starts 2009; tag inconsistencies across filers (handled with the standard `us-gaap` tags and manual checks on a sample); announcement dates (8-K earnings releases) differ from filing dates by up to two weeks and are taken from 8-K Item 2.02 filings where needed |
| Index-level valuation history | Compustat/S&P | Shiller monthly data (checked reachable): S&P price, earnings, dividends, CAPE, 1871– | long-run P/E and payout distributions, index-level earnings volatility | index level only; used for time variation of multiples and drift anchors, not cross-sections |
| Cross-sectional P/E | Compustat | EDGAR EPS × yfinance prices (constructed); Damodaran's industry P/E files (checked reachable) as a cross-check | trailing P/E cross-section by year, P10–P90 | large-cap survivor universe; negative-earnings firms (P/E undefined) reported separately |
| Implied volatility, single stocks | OptionMetrics | CBOE VIX history (FRED, checked); CBOE single-stock VIX indices (VXAPL, VXAZN, VXGOG, VXGS, VXIBM; to check whether the historical files are still served); published single-stock VRP statistics (Carr & Wu 2009; Bakshi & Kapadia 2003; Goyal & Saretto 2009) | IV–RV relation at index level daily; single-stock IV levels for five names if available; otherwise literature only | the single-stock IV model will be literature-anchored (LIT) with a sensitivity, and the audit tests its information content rather than its level |
| Daily news sentiment | RavenPack, Tetlock's factor | San Francisco Fed Daily News Sentiment Index (public, daily, 1980–; to check); Tetlock 2007 statistics (verified in the fact-check: 8.1 bp next day, 6.8 bp reversal); Garcia 2013; AAII weekly (public); Baker–Wurgler monthly (public) | persistence of daily sentiment, contemporaneous and lagged return relations at the market level | market-level, not single-stock; the single-stock loading is bracketed by the market-level estimate (upper bound on persistence) and reported as LIT+sensitivity |
| Analyst target prices | I/B/E/S | none free | — | literature only (Brav & Lehavy 2003; Bradshaw, Brown & Huang 2013; Bilinski, Lyssimachou & Walker 2013; Da & Schaumburg 2011); the error sd is a LIT value with an LLM-grid sensitivity (Phase 9) |
| Crash and bubble episodes | — | Mishkin & White 2002 (NBER w8992), Barro & Ursúa 2017 (NBER w22743 "Stock-market crashes and depressions"), Greenwood, Shleifer & You 2019 (JFE 131; verified: 40 run-ups, 21 crashed, 20/53/80 %), Sornette's LPPLS literature; plus single-stock episodes constructed from the price panel | durations, depths, recovery shares, run-up sizes, crash probabilities, hazard shapes | index and industry episodes are few (tens); single-stock episodes from the survivor panel understate depth; both reported |

If the team can obtain WRDS access (CRSP/Compustat/OptionMetrics/IBES), Phases 1–5 re-run their fits on it with the same pre-registered code; the plan is written so that the substitute results are labelled and replaceable. **Decision needed from the team (D1, Section 12): proceed with the substitutes, or pause Phases 1–5 until WRDS access exists.**

---

## 4. Phase 0. Verification and freeze (no design changes)

**Goal.** Reproduce every finding in the three reviews from code, fix the outright bugs, remove silent overrides, freeze the generator with hashes, add the statistical regression tests that will guard the later phases (as documented failures where the defect is a design change reserved for a later phase), make the test suite clean, and correct the stale documents. Nothing that changes a path's distribution by design is touched here; the fixes below either correct an implementation against its own documentation or remove an inconsistency.

**Weaknesses addressed.** 39, 44, 53, 54 (input), 65, 66, 68, 69, 70, 71, 72, 73, and the reproduction of every other item.

**Literature.** None needed; this phase is about the repository's own claims.

**Work and experiments.**

0.1 *Reproduction script.* `tools/verify_v2_findings.py` recomputes every numbered finding that is computational (items 1–6, 13, 16, 18, 20, 21, 25, 35–38, 40–43, 46–51, 58, 62, 68) with 50 seeds per scenario at T = 200 (and the T = 800 items at 50 seeds), writes `docs/env_v2/generated/v2_1/findings_reproduction.md` with the value, n, 95 % interval and the reviewer's number, and marks each item reproduced / not reproduced / documentary. The 30-seed numbers in Section 0.1 are the dry run of this script. Compute: about 10 minutes.

0.2 *Bug fixes (implementation ≠ documentation).*
- Analyst error (68): `observables.py::analyst_block` applies ρ = 0.95 per 5-day update and multiplies the innovation by √5, giving stationary sd 0.15√5. The documented process is an AR(1) with ρ = 0.95 per weekly update and stationary sd 0.15; the √5 is removed. Whether 0.15 is the right sd is Phase 5's question; Phase 0 only makes the code match its documentation. Test: pooled sd(u) within 10 % of the documented value at 100 seeds.
- Sensitivity pass/fail counts (39): regenerate every `checklist_v2_sens_*.md` footer from its CSV; add a test that footer counts equal row counts.
- MCR normalisation labels (53): `metrics_v2.floors_and_ceilings` uses constant-mix as the ceiling for lower-is-better metrics while `report_v2.py` and PILOT_NOTES say the ceiling is the mandate oracle. Phase 0 makes the code and the documents say the same thing and adds a docstring test. Which convention v2.1 uses (and the regret decomposition) is Phase 7; until then the published pilot `norm_mcr` values are annotated in PILOT_NOTES as "normalised against constant-mix".
- Day-1 gate input (54): `report_v2.py` feeds ΔC_1 into a gate that tests level ordering and band membership. Phase 0 restricts the gate to common-start cells and labels the ΔC_1 table exploratory with the reason; the re-specification is Phase 7.
- Silent overrides (69, 70): `HAZARD_H0/B` and `G_MAX` module constants set equal to the calibrated values, and the loader raises if `hazard.json` is missing or disagrees; `engine="fw_single"` raises unless an accepted `fw_single_stock.json` exists, and the fallback becomes an explicitly named engine (`fw_fallback_hl150`) so that renaming a REJECTED file cannot switch engines. Provenance (`get_metadata`) records the engine actually used.
- Half-life statements (71) and stale numbers (72): every document states the same three numbers (pull-rate half-life 150 d, pilot ACF(1) half-life 188 d at 20,000 steps, sample half-life 26 d at T = 200 / 72 d at T = 800 with their n); the sustained-bull multiplier is 1.0 and the jump rate 0.010 everywhere; the pilot covered three scenarios (44).
- Item 73: the trader band (0.4, 0.6) in the runner is replaced by the band-free convention used by the metrics; the common factor's t-mixture is documented as "not t5"; the crash V drift after deterioration is documented as a stated choice pending Phase 4; the $1 holdings threshold is documented.
- Scenario count in the script (44) and every "50 seeds" claim that is not 50 seeds get the correct n (list compiled by the reproduction script for Phase 10).

0.3 *Freeze.* `tests/test_v2_freeze.py`: SHA-256 manifest of `envs/v2/**/*.py`, `envs/synthetic_market.py`, `envs/v2/params/*.json`, `evaluation/{stylized_facts,leakage_audit,observables_oracle,metrics_v2,baselines_v2,targets}.py`; `simulation/provenance.py::env_provenance` hashes the manifest, not just the facade file, so `Env_Code_Hash` changes when any generator module changes. The manifest is regenerated deliberately at each phase end (the regeneration is itself a logged decision). (Commit point, if you wish: "v2.0 frozen".)

0.4 *Statistical regression tests* (`tests/test_v2_1_stats.py`), each with the seed count from the power rule and a stated tolerance:
- `test_flat_x_unbiased`: 100 flat seeds × 200 d, |mean x| ≤ 2 SE (cluster by seed). Currently fails (item 4); marked `xfail(strict=True, reason="defect 4; fixed in Phase 1")` and flipped to a hard test in Phase 1.
- `test_analyst_error_sd`: passes after 0.2.
- `test_iv_continuity`: z of the log-IV change at the deterioration→panic and panic→stabilisation transitions ≤ 3 against the calm day-to-day sd (30 crash seeds). Fails now; strict xfail until Phase 3.
- `test_fundamentalist_share`: with the engine's own parameters, mean n_f within the FW-published range and share of days with n_f > 0.99 below 50 %. Fails now; strict xfail until Phase 2.
- `test_half_life_consistency`: the engine's pull-rate half-life and the long-simulation ACF(1) half-life agree within 25 % (200,000 steps). Fails now (150 vs 188 d); strict xfail until Phase 2 explains and fixes the difference.
- `test_sustained_bull_selection`: accepted and rejected first-attempt paths have the same daily sd within 10 %. Fails now; strict xfail until Phase 4.
- `test_leakage_ci`: the strict xfail on the pre-registered L2 gate stays as the documented defect, with a registry (`tests/known_defects.py`) of every strict-xfail test and the phase that must empty it; the v2.1 acceptance rule is that the registry is empty.

0.5 *Clean suite.* `tests/test_market_environment.py` gets `pytest.importorskip("vectorbt")`; `tests/test_env_logic.py::test_bull_trap_generation` is rewritten against the v2 contract (V grows at μ_V in a bull trap; the assertion that carries over is that the price leaves the value) and its v1 form is kept in the v1 freeze tests only. CI target: `pytest tests/ -q` green, with the known-defect registry printed.

0.6 *What the earlier review rounds require of the freeze* (from `docs/reviews/cycle1`, `cycle2` and `docs/planning/FinPersona-Bench_Experiment_Execution_Order_Aug2026.pdf`, extracted today): the execution order's step 0 rule — "any environment or prompt change after the freeze restarts from step 0: re-freeze, re-audit, new hashes" — is adopted as a rule of this plan: the main grid (execution-order step 3) runs only on the v2.1 freeze produced at the end of Phase 10, and every phase end re-runs the checklist and audits on the frozen state it hands over. The smoke gate of the execution order (100 % parsed, all rows present, provenance columns filled, rendered prompt equal to the published sample) is kept as the Phase 8/9 run gate.

**Decision rules.** None (no design decisions in this phase). Any fix that would change a path's distribution beyond the documented bug is deferred and listed.

**Tests.** 0.3–0.5 above; plus `test_docs_numbers.py`: a small table of numbers that appear in the documents (half-lives, multiplier, jump rate, seeds) checked against the generated files.

**Documentation.** `PHASE_0_REPORT.md` (findings reproduction, list of bug fixes with before/after values, the known-defect registry, the test run log); spec, calibration report, PILOT_NOTES corrected; DECISION_LOG entries for the analyst-error interpretation and the MCR labelling convention.

**Compute / cost.** About 30 minutes of generator time; no API calls.

**What could block it.** Only the failing fast-suite test if it turns out to be environmental (e.g. a version-specific sklearn/statsmodels change); it will be reported either way.

---

## 5. Phase 1. Value and price structure

**Goal.** Remove the start-price answer key; fit the value process (drift, volatility, tails) to data with sources; decide where jumps belong; set the burn-in from a stationarity test; re-run the leakage audits with a level-free price control and re-state, with intervals, what is and is not inferable.

**Weaknesses addressed.** 1, 3 (audit side), 4, 5 (re-statement), 8, 9, 13 (placement), 43 (level-free L5), 50; per-asset start prices from 58.

### 5.1 Literature to consult (source → statistic → use)

Value volatility and the fundamental/transitory split at the firm level:
- Vuolteenaho (2002), *J. Finance* 57, "What drives firm-level stock returns?": variance decomposition of firm-level returns into cash-flow news and expected-return news; the share of firm-level return variance that is cash-flow news (recalled as the larger share, with the two components positively correlated; to verify Table 3). Use: an upper bound on how "smooth" V can be for a single stock. This matters because the v2 rationale ("the majority of single-stock variance is idiosyncratic mispricing, CLMX 2001") conflates idiosyncratic-vs-market variance with fundamental-vs-transitory variance; CLMX say nothing about mispricing.
- Cohen, Polk & Vuolteenaho (2003), *J. Finance*, "The value spread": share of the cross-sectional variance of book-to-market explained by future profitability vs future returns (recalled 75–80 % profitability at 15 years; to verify). Use: same bound, different method.
- Campbell (1991), Campbell & Shiller (1988), Cochrane (2008 RFS "The dog that did not bark"): at the index level the decomposition goes the other way (discount-rate news dominates). Use: to state why index-level anchors cannot set a single-stock σ_V.
- Poterba & Summers (1988, JFE 22; NBER w2343): transitory component sd 15–25 % at index level; Fama & French (1988, JPE): 25–45 % of 3–5-year return variance predictable for portfolios, weaker after 1940; Summers (1986, JF): fads model; De Bondt & Thaler (1985, JF): 3-year reversal of about 25 % for losers vs winners. Use: the size of the transitory component and its horizon (these are the same evidence Phase 2 uses for persistence).
- Bartram & Grinblatt (2018, JFE, "Agnostic fundamental analysis works"): firm-level mispricing measured as the deviation of price from a peer-implied fair value; the average absolute mispricing and its decay over 1–36 months (to verify the numbers). Rhodes-Kropf, Robinson & Viswanathan (2005, JFE): decomposition of market-to-book into firm-specific error, time-series sector error and long-run value; the firm-specific error's dispersion and persistence (to verify). Lee, Myers & Swaminathan (1999, JF): P/V ratio mean reversion for the Dow 30. Frankel & Lee (1998, JAE): V/P predicts 36-month returns. Use: direct evidence on the size and persistence of firm-level mispricing, which with the total return variance pins σ_V.
- Drift: Dimson, Marsh & Staunton (UBS Global Investment Returns Yearbook 2025: 4.3 % equity premium over bills, long-run) and Shiller's data (price-only US return, 1871–, computable from the monthly file); Damodaran implied ERP (verified 4.33 %, Jan 2025). Use: μ_V as a LIT value with an insensitivity check.
- Tails of fundamental shocks: the distribution of quarterly EPS surprises and of announcement-day returns (Ball & Brown 1968; Foster 1977; the earnings-announcement return literature, e.g. Kothari's 2001 survey for magnitudes; to verify). Use: whether V shocks should be Student-t, and whether jumps are fundamental.

Start-price randomisation: no literature is needed for the principle (a nuisance parameter must carry no information); the range comes from the empirical distribution of US large-cap share prices (from the panel), reported as P5–P95.

Burn-in: standard MCMC/simulation practice (Gelman–Rubin-type convergence is overkill; a two-sample KS test between the day-1 state and the long-run state distribution is used).

### 5.2 Experiments (pre-registered in PREREG_PHASE_1.md before running)

E1.0 *Shared data panel* (used by Phases 1–6): (a) daily adjusted close and volume for every ticker in the historical S&P 500 constituent list that `yfinance` still serves, 2000-01-01 to 2024-12-31, target ≥ 300 names, of which the "large-cap analysis set" is the ≥ 100 names with the longest complete histories plus a random sample of the shorter ones; (b) EDGAR quarterly EPS, DPS and filing/announcement dates for the same names, 2009–2025; (c) FRED VIX daily; (d) SF Fed daily news sentiment; (e) Shiller monthly. Deliverable: `data/panel/` (git-ignored) plus `docs/env_v2/generated/v2_1/panel_manifest.md` (tickers, date ranges, survivorship accounting). Compute: an afternoon of rate-limited downloads; no API cost.

E1.1 *Start-price randomisation.* Implement `start_price ~ LogUniform(P_lo, P_hi)` per seed and per asset with (P_lo, P_hi) = the P5–P95 of large-cap closes sampled on 40 random dates from the panel (a FIT value, reported with its own interval); V_1 = start price still holds, so EPS, DPS and the analyst estimate scale with it; ratios (P/E, yield) are scale-free and are Phase 5's business. Tests: across 500 seeds, R² of x_1 on log P_1 < 0.01; the level-based attacker of review C (GBT on level features) drops to the level-free R² within its CI.

E1.2 *Value–mispricing decomposition on data* (joint with Phase 2). On the panel: variance ratios VR(k) of daily log prices for k ∈ {5, 10, 20, 60, 120, 250, 500} per stock, pooled with a block bootstrap (block 250 d) for intervals; the model log P = log V + x with V a random walk with drift (variance σ_V²) and x an AR(1) (sd s_x, half-life h) implies a closed-form VR(k); fit (σ_V, s_x, h) by minimum distance to the pooled VR curve; also per sub-period (2000–07, 2008–12, 2013–19, 2020–24). Second method: log(P/V̂) with V̂ = trailing-4Q EPS × the sector-median multiple (EDGAR), quarterly 2009–2025: AR(1) with the median-unbiased correction (Andrews 1993) gives h and s_x; σ_V from the variance of Δlog V̂. The two methods are reported side by side with intervals. Pre-registered decision rule: if the two methods' σ_V intervals overlap, adopt the pooled estimate (FIT); if they do not, adopt neither and present both with the consequences (Section 12, D3).

E1.3 *σ_V sweep through the audits.* σ_V ∈ {0.004, 0.006, 0.010, 0.015, 0.020}/day × df_V ∈ {Gaussian, t5} at the current mispricing engine (so the effect of σ_V alone is isolated), 200 seeds per scenario: L2 level-free price-only R²(x) (surrogate and the analytic Kalman bound, Appendix B), L4 coverage at θ ∈ {0.03, 0.05, 0.08}, checklist items 9 and 20, and the "MAPE of V from a long price average" statistic. This sweep is what makes the σ_V decision's consequences visible; the value adopted is the fitted one from E1.2, not the one that makes an audit pass.

E1.4 *Where jumps belong.* Data: on the panel, the distribution of standardised daily returns (residuals from the per-stock GJR-GARCH fit of Phase 3, run early here as E3.1) on earnings-announcement days vs other days: the share of |z| > 4 days that are announcement days, and the size distribution on each. Model variants: (a) jumps in V at announcement dates (quarterly, tied to the EPS process) plus a residual Poisson component in V; (b) jumps in x with zero mean; (c) current (negative-mean jumps in x). Pre-registered rule: E[x] in flat must be 0 within 2 SE at 200 seeds under whichever variant is adopted (this rules out (c) unless its mean is removed); between (a) and (b), adopt the one whose announcement-day/other-day kurtosis split is closer to the panel's (KS distance), and report both. Consequence to state: variant (a) makes the EPS field carry the jump (as in reality), which the Phase 5 leakage audit must then test.

E1.5 *Burn-in.* Draw the day-1 state from a stationarity test: 500 seeds, compare the day-1 distribution of (x, GARCH variance, n_f) with the distribution after 5,000 days (KS test with equivalence bound 0.10); rule: burn-in ≥ 5 half-lives of the slowest state variable for every engine in the sensitivity set (including `fw_index` at ≈ 600 d), or sample the initial state from a stored long-run distribution. Report the KS statistic per engine.

E1.6 *Level-free leakage audits.* Re-run L1, L2, L2b, L4, L5 and the scenario-discrimination audit with (i) randomised start prices, (ii) `PRICE_ONLY_KEYS` replaced by a level-free set (returns at 1/5/20 d, log P/SMA20, log P/SMA50, RSI, MACD/P, trend), (iii) no `MAX_ROWS` subsampling, (iv) 200 seeds, (v) cluster-bootstrap intervals over paths, (vi) percentiles (p5/p10/p25/p50) of APE for every L1 candidate. Outputs restate items 3, 5 and 43: what a level-free reader can infer about x and V, with intervals, and the selectivity of the non-price fields against the level-free control (which is what Phase 5 must reduce). No gate is applied yet (Phase 6 derives the gates); the pre-registered v2 gates are reported as pass/fail for the record.

### 5.3 Decision rules

- Start price: randomised (no alternative survives item 1); the range is FIT from the panel.
- σ_V, s_x, h: FIT from E1.2 if identified (rule above); otherwise D3.
- μ_V: LIT (price-only long-run return from Shiller/DMS); insensitivity shown over 0–0.0005/day on the audits (E1.3 adds μ_V as a nuisance sweep at 50 seeds).
- df_V: FIT if the EPS-surprise tails distinguish Gaussian from t (KS on standardised quarterly EPS changes); otherwise reported as DESIGN with both variants in the checklist.
- Jumps: E1.4 rule.
- Burn-in: E1.5 rule.

### 5.4 Tests locked in

`test_start_price_carries_no_information` (R² of x_1 on log P_1 < 0.01, 500 seeds); `test_flat_x_unbiased` flipped to hard; `test_burn_in_stationary` (KS < 0.10 for every engine); `test_level_free_price_only_keys` (the audit's control set contains no level); `test_sigma_V_in_force` (the generator's σ_V equals the value in `params/value.json`, which carries its provenance record).

### 5.5 Documentation

PHASE_1_REPORT (panel manifest; decomposition fits with intervals per method and period; σ_V sweep tables; jump placement evidence; burn-in KS table; level-free audit tables with percentiles and intervals; the corrected statements for items 3, 5, 43); spec section 1 rewritten; `params/value.json` with provenance; DECISION_LOG entries; amendments for every deviation from the v2 plan (start price, σ_V, jumps, burn-in).

### 5.6 Compute / cost

Panel download: hours (rate-limited), one-off. Fits: minutes. Sweeps: 10 settings × 200 seeds × 4 scenarios (+ crash deltas) ≈ 12,000 paths ≈ 40 minutes on 8 cores; level-free audits at 200 seeds ≈ 1–2 hours of sklearn time. No API cost.

### 5.7 What could block it

- Panel construction: if fewer than 100 names with full 2000–2024 histories can be downloaded, the fits run on what exists and the report says so; the historical-constituent retrieval rate is reported.
- Identification of the decomposition (E1.2) may fail on 25 years of data per stock (variance ratios at k = 500 have few non-overlapping windows even pooled); the pre-registered fallback is D3.
- The σ_V answer may be much larger than 0.006 (Vuolteenaho-type evidence points that way). That would change the character of the benchmark (a less smooth V makes x harder to infer from price, which strengthens the "hidden value" claim and weakens the "playable from price" claim). The report will show both faces through E1.3 and E1.6; the team decides (D3).

---

## 6. Phase 2. Mispricing engine

**Goal.** Resolve the FW units against the original paper; decide between a working FW and an honest AR(1)+GARCH on pre-registered evidence; estimate the persistence from firm-level data with a proper method; report a bias-corrected half-life at the horizons the benchmark uses; sweep persistence through the checklist (and, in Phase 9, the LLM harness).

**Weaknesses addressed.** 2, 10, 11, 35, 36, 38, 62.

### 6.1 Literature

- Franke & Westerhoff (2012, JEDC 36:1193–1211; Bamberg PDF reachable): the DCA-HPM equations, the units of p (log price), the estimated parameters (verified in the fact-check), the nine moments, the bootstrap J-test (p = 32.6 %), and the reported simulated moments; Franke & Westerhoff (2014/2016) on the MSM bootstrap procedure. Pruna, Polukarov & Jennings (2016, arXiv:1604.08824): log-price units confirmed (Section 0.2), FW+ parameters with a GBM fundamental (verified). Platt (2020, JEDC, "A comparison of economic agent-based model calibration methods") and Grazzini & Richiardi (2015) for SMM/MSM practice; the SABCEMM contest (arXiv:1812.02726) for the DCA-HPM's reported mean chartist share (≈ 0.17) and excess kurtosis (≈ 10).
- Persistence at the firm level: the sources in 5.1 (Bartram & Grinblatt 2018; Rhodes-Kropf et al. 2005; Lee, Myers & Swaminathan 1999; Frankel & Lee 1998; De Bondt & Thaler 1985/1987; Fama & French 1988; Poterba & Summers 1988; Balvers, Wu & Gilliland 2000 for the index-level half-life of 3–3.5 years by a panel method) — what each reports as a half-life or decay rate, and at what level (firm/industry/index).
- Estimator bias: Marriott & Pope (1954) and Kendall (1954) for the AR(1) bias; Andrews (1993, Econometrica) median-unbiased estimation; Lo & MacKinlay (1988) variance-ratio test and its heteroskedasticity-robust standard errors. Use: the bias-corrected half-life and the persistence-carrying moments.

### 6.2 Experiments

E2.1 *Units verified at source.* Transcribe FW 2012's price, demand and switching equations from the PDF; state the units of p and of the misalignment term; reproduce, at the index set, FW's reported simulated moments and the SABCEMM chartist share with `price_scale = 1` and with 100 (10 paths × 7,000 days each). Rule: the convention that reproduces the published moments within the paper's own bootstrap intervals is the correct one. Expected (Section 0.2): `price_scale = 1`. This is a bug fix once verified, logged as such (LIT).

E2.2 *Firm-level persistence estimate.* Two estimators on E1.0: (i) the variance-ratio decomposition of E1.2 (shared); (ii) log(P/V̂) AR(1) on EDGAR fundamentals at monthly frequency (prices monthly, V̂ updated quarterly), 2009–2025, ≥ 100 names, with Andrews' median-unbiased correction and a block bootstrap over stocks and time; report the cross-sectional median half-life, P25/P75, and per sub-period. Pre-registered: the adopted half-life is the median of (ii) if (i) and (ii) overlap, else D3.

E2.3 *SMM redone properly* (on the same panel). Moments: FW's nine (lag-1 return ACF, mean |r|, Hill 5 %, ACF |r| at 1/5/10/25/50/100) plus persistence-carrying moments: variance ratios at 20/60/120/250/500 d and the ACF of log(P/SMA250) at lags 20/60/120; empirical targets pooled over ≥ 100 stocks with a block-bootstrap weight matrix (stored to disk, not a diagonal proxy); simulated model = the calm engine with the Phase-3 GJR-GARCH-t innovation (fitted in E3.1, which is run before this step) and the E1.2 value process; common random numbers, 20 paths × 5,000 days per evaluation (vectorised over paths); optimiser: differential evolution (scipy) with ≥ 20 starts including chartist-active regions, followed by Nelder–Mead polish; acceptance: χ² at 5 % with df = moments − parameters, plus FW's bootstrap p-value; full-parameter J profiles at the optimum; three sub-periods; start-J and end-J recorded. Compute: 20 starts × ~400 evaluations × ~0.3 s ≈ 40 minutes per sub-period.

E2.4 *FW vs AR(1)+GARCH decision.* Pre-registered comparison: (a) SMM acceptance for each engine on the same moments; (b) held-out-period moment prediction (fit on 2000–2016, predict 2017–2024 moments; distance in bootstrap-sd units); (c) equivalence of the checklist and the level-free leakage statistics at matched persistence and variance (200 seeds; any item that differs by more than its CI is listed). Rule: FW stays the default only if it is accepted at (a) and beats AR(1)+GARCH at (b) by more than one bootstrap sd on the persistence-carrying moments; otherwise AR(1)+GARCH becomes the default, FW (with `price_scale = 1`) the sensitivity, and every document names the engine honestly. If FW is retained, the parameters are FIT (E2.3), not the index set.

E2.5 *Half-life reporting.* Simulation table: pure AR(1) with true half-life ∈ {30, 60, 120, 150, 250, 500, 600} d, T ∈ {200, 800, 2000, 5000}, 200 seeds each: the distribution of the naive ACF(1) half-life and of the median-unbiased estimate; the table becomes the lookup for the checklist item and the documents report (i) the analytic half-life from the pull rate, (ii) the median-unbiased estimate at T = 200 ("what the agent experiences": also sd of x within 200 days and the number of oracle target switches per run), (iii) at T = 5,000 (stationary). The 150 vs 188 d discrepancy is diagnosed (the chartist term and the weight normalisation shift the effective pull) and either the engine is corrected so the two agree or the documents state the measured value.

E2.6 *Persistence sweep.* Half-life ∈ {30, 60, 120, 250, 500} d at matched stationary sd of x (so persistence is isolated from variance) and, separately, at matched innovation variance: checklist at 200 seeds (all items), level-free audits at 100 seeds, hazard/topped share, rejection rates. The LLM sweep is Phase 9.

### 6.3 Decision rules

Stated in E2.1, E2.2, E2.4. The half-life is FIT (E2.2) with its interval; the engine is decided by E2.4; both bracketed by the E2.6 sensitivities; item 9's criterion is re-derived in Phase 6 from the panel, not stated.

### 6.4 Tests

`test_fw_units` (chartist share at the index set within the published range); `test_engine_named_honestly` (the metadata engine name equals the code path used; no silent fallback); `test_half_life_estimator_table` (the lookup table regenerates within tolerance at 50 seeds); `test_persistence_in_force` (pull rate matches `params/mispricing.json` with provenance); `test_fundamentalist_share` flipped to hard (if FW retained) or removed with a note (if AR(1)).

### 6.5 Documentation

PHASE_2_REPORT (units transcription; persistence estimates with intervals; SMM tables incl. weight matrix provenance, start/end J, profiles; the engine decision; the half-life table; the sweep); spec section 2 rewritten; `params/mispricing.json`; DECISION_LOG; amendment for the engine change; the `fw_single_stock.REJECTED.json` retained as history.

### 6.6 Compute / cost

SMM ≈ 2–3 hours total; sweeps ≈ 1 hour; no API cost.

### 6.7 What could block it

The FW 2012 PDF becoming unreachable (a copy is requested from the team's references folder if so); SMM non-identification even with persistence-carrying moments (then the AR(1) default follows from the rule, which is acceptable); the panel limitation of Section 3.

---

## 7. Phase 3. Volatility

**Goal.** GJR-GARCH-t parameters fitted per stock on a stated dataset; jump rate and size from data; phase variance multipliers from regime-conditional evidence; an implied-volatility construction that is not a phase step and has no look-ahead.

**Weaknesses addressed.** 12, 14, 25, 46, 73 (GARCH fit on regime paths), and the jump rate/size part of 13.

### 7.1 Literature

- GARCH on single stocks: Engle (2001, JEP; verified secondary: α 0.077, β 0.905 on a portfolio), Hansen & Lunde (2005, JAE; verified: leverage models beat GARCH(1,1) on IBM), Glosten, Jagannathan & Runkle (1993; monthly, so not a daily γ range — the fact-check's correction stands), Bollerslev (1986). The daily single-stock α/γ/β/ν distribution will be FIT; the literature provides the sanity range (persistence 0.95–0.99; ν 4–8), cited as such.
- Jumps: Lee & Mykland (2008, RFS) jump detection with local volatility; Andersen, Bollerslev & Diebold (2007, REStat) on jump contribution to variance (daily data version); Kou (2002) / Bates (1996) jump-diffusion parameterisations; the earnings-announcement return literature (Phase 1) for fundamental jumps. Use: rate per year, size distribution, sign asymmetry, and the announcement/non-announcement split.
- Regime-conditional variance: Ang & Timmermann (2012; verified: monthly σ 4.89 % vs 2.45 %, variance ratio ≈ 4.0), Ang & Bekaert (2002; verified: 7.04 % vs 3.77 %, ratio ≈ 3.5), Hamilton & Susmel (1994, J. Econometrics; SWARCH on weekly stock returns; the high-variance regime factor, to verify), Schwert (1989, JF; 1990) on volatility in recessions and crashes, Greenwood, Shleifer & You (2019; verified: volatility rises in run-ups that crash). Use: sanity ranges for the multipliers, which are FIT from single-stock event windows.
- Implied volatility and the variance risk premium: Carr & Wu (2009, RFS; individual-stock VRPs small), Bakshi & Kapadia (2003, RFS), Goyal & Saretto (2009, JFE; cross-section of log(IV/RV)), Bollerslev, Tauchen & Zhou (2009, RFS; index VRP), Bollerslev & Todorov (2011, JF); Christensen & Prabhala (1998, JFE) on IV vs subsequent RV regressions. Use: the IV = f(past RV, GARCH forecast) mapping, the premium size and its state dependence, and the noise around it.

### 7.2 Experiments

E3.1 *Per-stock GJR-GARCH-t fits* (`arch`): every name in the analysis set, full sample and four sub-periods; report cross-sectional median and IQR of α, γ, β, ν, persistence, unconditional daily sd; survivor bias stated (survivors have lower unconditional variance; reported beside the literature's full-universe values). Adopt the median (FIT); the P25 and P75 sets are sensitivities run through the checklist (Phase 6) and the LLM grid (Phase 9).

E3.2 *Jumps.* On the standardised residuals from E3.1: Lee–Mykland-type detection at a pre-registered threshold (|z| > 4 with the local-volatility correction), rate per year, mean and sd of jump sizes, negative share, and the announcement-day split (E1.4). Adopt the FIT rate and size distribution for whichever placement E1.4 chose.

E3.3 *Phase variance multipliers from event windows.* On the panel: single-stock drawdown episodes ≥ 30 % (peak-to-trough), run-ups ≥ 100 % over 2 years (GSY-style), and the market-wide crash windows (2008Q4, 2011Q3, 2018Q4, 2020Q1, 2022H1); for each episode, realised variance in windows defined relative to the trough/peak (pre-event calm; deterioration = the 40 days before the largest 20-day decline; panic = the 20 days around it; stabilisation = the 60 days after the trough; mania/blow-off/post-top analogously for run-ups) divided by the pre-event calm variance; medians with bootstrap CIs. Adopt the FIT multipliers; report the literature ratios beside them.

E3.4 *How the regime enters the variance.* The choice between scaling the whole conditional variance (v2, amendment A3) and scaling ω with a ramp is decided by the empirical rise time: from the event windows, the number of days from onset to peak realised variance (e.g. 2020: ≈ 10 trading days; 2008: ≈ 30) and the decay half-life after the peak; the mechanism (and ramp length, FIT) that reproduces the empirical rise and decay within their CIs is adopted. Both are kept as engine options.

E3.5 *Implied volatility without a step or look-ahead.* Construction: IV_t = √(252 · σ̂²_{t+1..t+21}) · (1 + π_t) · exp(ε_t), where σ̂² is the 21-day forecast of a GJR-GARCH filter run on the observed returns only (the same model class, so the filter is a past-only function of the price path; the hidden regime enters only through the returns it has already produced), π_t the premium as a function of the filter's variance level (FIT from the VIX–RV relation on FRED data and the single-stock VRP literature), and ε_t a noise term whose sd is FIT from the residual of the IV–RV regression. Pre-registered checks: (i) no field uses information from t+1 onwards (a code test); (ii) onset-detection audit (Phase 5/6): IV's change-point detectability at phase transitions is not higher than that of 21-day realised variance computed from the price path; (iii) checklist item 13 re-derived from the empirical IV–RV distribution (Phase 6). The `IV_PREMIUM_STRESS` decile trigger and the whole-path quantile are removed.

E3.6 *Item 73 (GARCH persistence on regime paths).* Item 5 of the checklist is computed on calm windows only and on the whole path, both reported.

### 7.3 Decision rules

All parameters in this phase are FIT with intervals; where the data cannot deliver (single-stock IV level), the value is LIT with a sensitivity and labelled. The variance mechanism is decided by E3.4's rise-time rule.

### 7.4 Tests

`test_garch_params_in_force` (equal to `params/volatility.json` with provenance); `test_iv_no_lookahead` (IV at day t is unchanged when the path after t is altered; 20 seeds); `test_iv_continuity` flipped to hard with the tolerance derived in E3.5 (z at transitions ≤ the 95th percentile of the realised-variance change-point statistic); `test_jump_process` (rate and mean size within the FIT intervals at 500 seeds).

### 7.5 Documentation

PHASE_3_REPORT (fit tables, event-window multipliers with CIs, rise-time analysis, IV construction and its audits); spec section 4; `params/volatility.json`; DECISION_LOG; amendments (A3 revisited with evidence).

### 7.6 Compute / cost

GARCH fits: minutes; event-window analysis: minutes; checklist re-runs at 200 seeds for the quartile sets: ≈ 30 minutes. No API cost.

### 7.7 What could block it

Single-stock IV data may be unavailable (then the IV level is LIT); survivorship in the drawdown episodes (depths understated; reported).

---

## 8. Phase 4. Events, schedule and controls

**Goal.** Crash and bubble durations, depths, discounts and hazard from historical episodes; the sustained-bull control on the same mispricing process as the flat market with published selection effects; the error-correction gains justified or replaced; orderings run in the grid; the calendar removed as a clock.

**Weaknesses addressed.** 6, 15, 16, 17, 18, 19, 41, 42, 47, 49, 51, 58 (shared event), 73 (crash V drift).

### 8.1 Literature

- Mishkin & White (2002, NBER w8992): the 15 US stock-market crashes (≥ 20 % declines) 1900–2000 with dates, peak-to-trough magnitudes and durations. Barro & Ursúa (2017, NBER w22743, "Stock-market crashes and depressions"): crash frequency and size distribution across 30 countries (crash = cumulative real decline ≥ 25 %); the probability and duration statistics. Pagan & Sossounov (2003, JAE; verified secondary: bull ≈ 25 months, bear ≈ 15 months) for the dating algorithm applied to the panel.
- Greenwood, Shleifer & You (2019, JFE; verified): 40 industry run-ups ≥ 100 %, 21 crashed within 2 years; crash probability 20 / 53 / 80 % after 50 / 100 / 150 % run-ups; the characteristics that predict crashes (volatility, issuance, acceleration; not turnover); the post-run-up return distribution. Use: hazard slope b (a logit of crash probability on log run-up), the topped share over a stated horizon, peak run-up sizes, and the sustained-bull ("did not crash") population's characteristics.
- Sornette's LPPLS: Johansen, Ledoit & Sornette (2000), Filimonov & Sornette (2013, Physica A) for the linearised calibration; Sornette, Demos et al. (2015) "Real-time prediction and post-mortem analysis of the Shanghai 2015 bubble"; Sornette & Cauwels (2015). Use: the super-exponential exponent m ∈ (0, 1), ω, and the hazard's shape, fitted on the panel's run-ups and on Nasdaq 1998–2000.
- Cash-flow vs discount-rate decomposition of crashes: Campbell, Giglio & Polk (2013, RFS, "Hard times"): the 2000–02 and 2007–09 declines decomposed into cash-flow and discount-rate news (to verify which dominated in each). Use: the split between the fundamental drop D_V and the panic discount delta, and the delta levels.
- Sustained bull: GSY's 19 non-crashing run-ups (returns and volatility), the panel's run-ups that did not reverse within 200 days.
- Deterioration and stabilisation shapes: the cumulative-decline shapes of 1987, 2000–02, 2008, 2020 from the Shiller/FRED series; single-stock episodes from the panel.

### 8.2 Experiments

E4.1 *Episode tables.* Index episodes (Mishkin–White, Barro–Ursúa, Shiller series) and single-stock episodes from the panel (Pagan–Sossounov dating on daily data; drawdowns ≥ 20 % and ≥ 30 %; run-ups ≥ 100 %/2 y): peak-to-trough duration, depth, front-loading (share of the decline in the first third), share recovered within 60/120/200 days, the pre-decline "deterioration" length (days from the last high to the first 10 % down), and for run-ups the LPPLS fit (m, ω, hazard) and the peak P/V̂ using the EDGAR value proxy. Every quantity with its empirical P10/P50/P90.

E4.2 *Sampling ranges from the tables.* Pre-registered rule: each schedule parameter (setup length, deterioration length, panic length, D_V, delta, delta_end, front-loading, mania kappa, post-top length and drop) is drawn from the empirical P10–P90 (FIT), truncated only where T = 200 forces it, with the truncation rate reported; where the panel and the index tables disagree, the report shows both and the team chooses (D4). The current uniform ranges are shown beside the empirical ones so that the change is visible.

E4.3 *Hazard.* b from a logit of GSY's crash indicator on the log run-up (their 20/53/80 % points give the slope directly; the fit on the panel's own run-ups is the cross-check); h0 from the horizon by setting the implied 200-day crash probability at the median run-up equal to the empirical value (FIT); the "40–60 % topped" band and the P/V 1.6–2.5 band are retired as targets; the topped share becomes an outcome that is reported. The calibration tool's arbitrary score and rejection penalty are removed. The uncapped mania run is included in the report (item 41).

E4.4 *Mania drift.* kappa and the mania length are drawn jointly from the LPPLS fits so that the drift cap is unnecessary (rule: the cap binds on < 5 % of mania days; convexity test on the pre-cap segment); if the fits do not support a super-exponential drift over 40–100 days, the report says so and offers a scripted-drift alternative with the shape FIT from the run-up table.

E4.5 *Sustained bull on the same process.* d_t = 0 (as the v2 plan said); the x-band rejection is removed; validity is defined on V only (V_T/V_1 ≥ the FIT threshold from the non-crashing run-up table) so that no path is selected on its mispricing; the realised x distribution is published; accepted-vs-rejected volatility, ACF and IV are published; the scenario-discrimination audit is re-run on demeaned, level-free returns with the rule that a classifier of sustained-bull vs flat days must be at chance (95th percentile of a label-permutation null) — if it is not, the remaining channel is named. The execution order's acceptance test for the control ("adherence moves, regret does not") is pre-registered here as a baseline-level check: on the control, the mandate-conditional oracle and constant-mix must have the same regret within its CI while band-MAS differs across the trivial policies; it is then re-run on the LLM cells in Phase 9.

E4.6 *Error-correction gains.* Three formulations, all implemented: (i) tracking gain λ (current), (ii) a shift of the perceived fundamental p* to the scripted target with a regime-specific pull φ_regime (FW-native: an event is a change in what fundamentalists believe, with the pull rate FIT from the panel's crash-window decay), (iii) an explicit drift with no feedback plus rejection. For each: the variance share of event-phase Δx explained by the script (R² of d_t on Δx), the rejection rate, checklist items 10 and 20, the level-free leakage statistics, at 200 seeds; λ swept over {0.02, 0.05, 0.10, 0.25} for (i). Pre-registered rule: adopt the formulation with the lowest script share that meets the empirical depth/duration ranges of E4.2 with rejection below the pre-registered rate (itself derived in Phase 6); if none does, report and ask (D5). The adopted gain, if any, is labelled CAL.

E4.7 *Orderings and the calendar.* (a) event-first and phase-free orderings enter the LLM grid as a factor (the harness already supports them); the mix and the setup range are set so that, within each scenario, the day-only phase classifier's accuracy is no higher than the majority class plus the margin derived from a label-permutation null at 200 seeds (Phase 6 derives the margin; here the schedule is designed to meet it); (b) the rendered day index: options are a calendar date from a random start date, no date, or "Day-N" as a disclosed-index arm; the pre-registered measurement is the same day-only classifier on what the agent can compute (for a stateless agent, nothing; for a stateful agent, the turn count); D6 asks the team which rendering is the default because it changes comparability with v1; (c) the quarter phase of `days_since_eps_announcement` randomised per seed; (d) `Schedule_Setup_Len` and the ordering logged (already).

E4.8 *Labels and small fixes.* Blow-off defined by a dynamic criterion (drift above a FIT threshold, or reported only for topped runs); top day recorded at the realised peak (off-by-one); crash V drift after deterioration stated and tested against the episode table's fundamental decline shape; the multi-asset shared event replaced by per-asset event draws with a common-factor loading FIT from the panel's cross-sectional correlation of drawdowns (the multi-asset provenance sensitivities themselves are Phase 9).

### 8.3 Decision rules

E4.2, E4.3, E4.5, E4.6 rules above; the calendar rendering is D6.

### 8.4 Tests

`test_schedule_ranges_from_params` (draws inside the FIT ranges); `test_sustained_bull_selection` flipped to hard; `test_no_x_selection_in_control` (accepted and rejected paths have the same x distribution within a KS bound); `test_hazard_params_provenance`; `test_script_share_reported` (the event-phase script share is computed and stored in metadata); `test_day_index_rendering_option` (the renderer honours the chosen option).

### 8.5 Documentation

PHASE_4_REPORT (episode tables with sources and P10/50/90; the sampling ranges before/after; hazard fit; mania drift fit; the control's published selection statistics; the gain comparison; the ordering/calendar audit); spec section 3; `params/events.json`; DECISION_LOG; amendments (A4, A5 revisited; the plan's x-band for the control retired).

### 8.6 Compute / cost

Episode analysis: minutes; three formulations × 4 λ × 200 seeds ≈ 15,000 paths ≈ 1 hour; ordering audits ≈ 30 minutes. No API cost (the orderings run in the LLM grid in Phase 9 / the main grid).

### 8.7 What could block it

Few index episodes (statistical tables will be thin; the panel supplies the mass); the LPPLS fits are notoriously unstable (the report will show the fit diagnostics and, if unstable, fall back to the scripted-drift alternative of E4.4); D4–D6 are team decisions.

---

## 9. Phase 5. Observables

**Goal.** Earnings, P/E multiple range, dividends, analyst error, sentiment, volume and technicals each anchored to a stated empirical source and designed so that no field is a deterministic function of the hidden state; audited for leakage with the level-free control and an onset-detection test.

**Weaknesses addressed.** 3, 20, 21, 22, 23, 24, 34 (observable constants), 45.

### 9.1 Literature

- Earnings: Foster (1977, Accounting Review) seasonal random-walk model of quarterly EPS; Ball & Brown (1968); Brown & Rozeff (1979); Kothari (2001, JAE survey) for surprise magnitudes; SEC 10-Q deadlines (40/45 days) and the announcement-lag distribution (EDGAR 8-K Item 2.02 dates). Use: EPS noise as the residual sd of the seasonal RW relative to the level (FIT on EDGAR), reporting lags (FIT), and the frequency of negative EPS (for the P/E cap: FIT P99).
- Multiples: the trailing P/E cross-section (EDGAR × prices; Damodaran industry files as cross-check) for the range; Shiller's series and the panel for the time variation of multiples (a slowly varying log-AR(1) for k_t, FIT). Use: replaces U(14, 22) by a FIT distribution and a time-varying multiple so that P/E never identifies V even asymptotically.
- Dividends: Lintner (1956, AER; speed of adjustment ≈ 0.3 per year, to verify), Brav, Graham, Harvey & Michaely (2005, JFE), Leary & Michaely (2011, RFS) for smoothing speeds; EDGAR payout distributions. Use: payout (FIT), quarterly stickiness converted from the annual speed (FIT), whether dividends are cut in crashes (FIT from 2008–09/2020 episodes).
- Analyst estimates: Brav & Lehavy (2003, JF; target prices, implied return ≈ 28 %, to verify), Bradshaw, Brown & Huang (2013, RAST; target-price accuracy, share met within 12 months and absolute errors, to verify), Bilinski, Lyssimachou & Walker (2013, TAR; international accuracy), Da & Schaumburg (2011, JFM), Gleason, Johnson & Li (2013, CAR) for valuation-model-based target errors. Use: the error sd and persistence as LIT values with a Phase-9 sensitivity (no free target-price data).
- Sentiment: Tetlock (2007, JF; verified 8.1 bp / 6.8 bp), Garcia (2013, JF; NYT columns 1905–2005, persistence and predictability concentrated in recessions), Boudoukh, Feldman, Kogan & Richardson (2019, RFS; news days and return variance), Baker & Wurgler (2006, 2007) for the level–valuation link at market level, Brown & Cliff (2004) for survey sentiment vs contemporaneous returns; the SF Fed Daily News Sentiment Index (Shapiro, Sudhof & Wilson 2020, J. Econometrics) as public daily data. Use: the AR(1) of daily sentiment (FIT), the contemporaneous and lagged return loadings (FIT at market level, LIT at firm level), and whether any direct valuation loading is supported (Baker–Wurgler: at market level, yes, slowly; at daily single-stock frequency, no direct evidence — so the default is a returns-only sentiment with the valuation link as a labelled sensitivity).
- Volume: Karpoff (1987, JFQA; volume–|Δp| correlations 0.2–0.5, to verify the table), Gallant, Rossi & Tauchen (1992, RFS), Lo & Wang (2000, RFS; turnover autocorrelation), Llorente, Michaely, Saar & Wang (2002, RFS); GSY (2019) on turnover in run-ups (elevated in all run-ups; not a crash predictor). Use: log-volume AR(1) and the |r| elasticity FIT on the panel; the |x| loading is supported only through the run-up turnover ratio (FIT from GSY-style run-ups in the panel), otherwise zero.
- Technicals: Wilder (1978), Appel (MACD), Brock, Lakonishok & LeBaron (1992); already reference-tested; unchanged.

### 9.2 Experiments

E5.1 *Multiple.* FIT the trailing P/E cross-section (P10–P90 by year) and the quarterly AR(1) of log P/E at the stock level (EDGAR × prices); implement k_t as a log-AR(1) per seed with the FIT dispersion and persistence; sweep the width (P25–P75, P10–P90, P5–P95) through the level-free L2 (the Phase-9 LLM sweep uses the same levels).

E5.2 *EPS and lags.* FIT the seasonal-RW residual sd and the lag distribution; implement announcement dates from the FIT distribution; the quarter phase randomised (Phase 4); negative EPS handled as in the data (P/E undefined → rendered as "n/m", with the frequency reported; the cap becomes the FIT P99 or the field is n/m).

E5.3 *Dividends.* FIT payout and stickiness; dividend behaviour in crash episodes; the field is kept only if dividends are paid into cash (Phase 7).

E5.4 *Analyst estimate.* LIT sd and persistence from the target-price literature, with the update frequency (quarterly revisions with earnings, weekly consensus drift); the sd is bracketed {0.15, 0.30, 0.45} and swept through the level-free L2/L5 here and the LLM grid in Phase 9; the report states plainly that no free data can fit it.

E5.5 *Sentiment.* FIT the AR(1) and the return loadings on the SF Fed index vs S&P returns (daily) and cross-check against Tetlock's published numbers; implement s_t as an AR(1) driven by contemporaneous and lagged returns (level-free by construction) with the b_pred feedback as before; the direct x loading is set to zero in the default and kept as a labelled sensitivity (Baker–Wurgler-style slow valuation link), with its L2 selectivity reported.

E5.6 *Volume.* FIT ρ_v, the |r| elasticity and the noise sd on the panel; the |x| loading replaced by a run-up turnover ratio FIT (or zero); the onset-detection audit decides whether any residual clock remains.

E5.7 *Audits.* (a) Level-free L2 with a per-field-group ablation (which field group adds how much R² for x and for V, with cluster-bootstrap CIs, 200 seeds); (b) the L1 extended candidate set (Phase 6's method) on the new fields; (c) the onset-detection audit: predict "a phase transition occurred within ±3 days" from each field's own changes vs from realised variance and returns; report AUC and timing error per field with a label-permutation null; rule: no field exceeds the price-derived AUC by more than the null's 95th percentile; (d) the earlier v2 gates reported for the record.

### 9.3 Decision rules

Every constant in `observables.py` ends this phase with a provenance label; FIT where the panel/EDGAR/SF Fed deliver, LIT+sensitivity where they do not (analyst sd), DESIGN only for the rendering of undefined values. Any field that fails the onset rule or adds more x-R² than the Phase-6-derived margin is redesigned or dropped; dropping is reported, not hidden.

### 9.4 Tests

`test_observable_params_provenance` (every constant is read from `params/observables.json` with a source field); `test_no_field_is_deterministic_in_x` (partial R² of each field on x given the price path below a stated bound at 200 seeds); `test_onset_audit_bound`; `test_sentiment_level_free` (s_t unchanged under a shift of the price level); `test_eps_lag_distribution`.

### 9.5 Documentation

PHASE_5_REPORT; spec section 6; Table 2 regenerated; `params/observables.json`; DECISION_LOG; amendments.

### 9.6 Compute / cost

EDGAR retrieval: hours (one-off, part of E1.0); fits: minutes; audits at 200 seeds ≈ 2 hours. No API cost.

### 9.7 What could block it

EDGAR tag heterogeneity (mitigated with standard tags and a manual sample); the SF Fed index availability (fallback: Garcia's published moments and Tetlock's, LIT); the analyst field remains LIT by necessity.

---

## 10. Phase 6. Audits and checklist methodology

**Goal.** Every checklist statistic given an empirical reference distribution from real 200-day windows of large-cap stocks; a per-item power analysis; seeds and horizons set accordingly; an extended L1 candidate set; L2/L2b gates derived, not stated; leakage reported with percentiles and intervals; the tuned-parameter ledger.

**Weaknesses addressed.** 5, 7 (ledger), 30, 31, 32, 37, 40, 61, 63, 64, 67 (held-out scenario, L3).

### 10.1 Literature

Cont (2001, verified list) for the facts; the Ratliff-Crain et al. (2025) revisit; Hashimoto et al. (2025, Table 3) and TwinMarket (2025, Table 4) as the precedents for reference tables; Vyetrenko et al. (2020) for distribution overlays; for the leakage methodology: Hewitt & Liang (2019) selectivity, Gururangan et al. (2018) partial-input baselines, Kaufman et al. (2012) leakage definition, KTD-Fin's probe design with Wilson CIs; for the analytic bound: the steady-state Kalman filter for a random-walk-plus-AR(1) signal (Harvey 1989; Appendix B).

### 10.2 Experiments

E6.1 *Empirical reference distributions.* From E1.0: every non-overlapping 200-day window of every name in the analysis set (≈ 30 per name × ≥ 100 names ≈ 3,000 windows; sub-periods reported): every checklist statistic (LB p-values on r and |r|, ACF(1) of r and |r|, kurtosis, Hill, ARCH-LM, GJR γ, leverage correlation, volume–|r| Spearman, log-volume AC(1) and Shapiro p, skew, worst/best day ratio, MDD, daily σ, and — for IV items — the VIX/RV relations at index level and the single-stock IV where available). Publish the P10/P50/P90 per statistic and per sub-period. Survivorship stated.

E6.2 *Re-derived criteria.* For each item: the old (v2 plan) criterion and a new one of the form "the generator's cross-seed distribution of the statistic is not distinguishable from the real-window distribution beyond an equivalence bound" (two-sample KS with bound 0.10, or the P10–P90 band with a share criterion), written in PREREG_PHASE_6 before the generator is re-run; results reported under both criteria; every item whose threshold was moved in v2 (9, 10, 11, 13, 17, 20; amendments A1, A2, A6, A7) listed in the **tuned-parameter ledger** together with the parameters tuned against it (α, γ, β, σ̄, jump rate, panic multiplier, φ, hazard) and the pre-amendment results beside the amended ones (item 7).

E6.3 *Power analysis per item* (Appendix A): the seed count per item from the rule in Section 1, using the cross-seed variance from a 50-seed pilot; a table of item → n → achieved power; the final checklist run at the maximum required n (expected 200–500 seeds per scenario; T = 200 for "what the agent experiences", with T ∈ {800, 2000} reported separately for the persistence and ACF-decay items, never as the pass criterion for a T = 200 property).

E6.4 *Per-scenario and calm-only reporting.* Items 2, 3, 5, 6, 12 reported on flat paths and calm windows separately from the pooled set (items 37, 50), with the regime-switching contribution quantified.

E6.5 *L1 extended candidate set.* Candidates: k·P, k·P/PE, k·P·DY, k·F, k·SMA50, k·SMA50/PE, trailing-EPS × k with per-path k, EPS-step tracking, averages of two and three candidates, the analyst estimate rescaled per path, and a small template search (products/ratios of up to three shown fields with one free scale); for each: the APE distribution (p5/p10/p25/p50) and the share of steps within 1/2/5 %; the pass rule derived from the noise floor implied by the x process (the share of steps that any level-free estimate could hit given sd(x)), not a hard-coded 1 %.

E6.6 *L2 gate derivation.* The analytic level-free price-only bound on R²(x) from the adopted (σ_V, s_x, h) (Appendix B), checked against the surrogate; the gate = selectivity of the non-price fields over the level-free control ≤ the 95th percentile of a label-permutation null (paths' targets permuted across seeds) plus the sampling half-width; MAPE(V) reported with intervals; the held-out-scenario split implemented (item 67); the L3 LLM probe implemented (200 probes stratified by scenario × phase × seed, ≥ 5 models, shuffled-V baseline, Wilson CIs; cost in Section 10.6).

E6.7 *L2b gate derivation.* The 10 pp margin replaced by the same null-derived margin; the onset-detection audit added as L2c; both reported with intervals.

E6.8 *Never-implemented criteria (item 64)* implemented: item 12's lagged-correlation = configured b_pred (within-phase partial correlation with a CI), item 13's non-degeneracy across seeds.

E6.9 *Known-answer tests for every audit statistic* (synthetic AR/GARCH series with known properties).

### 10.3 Decision rules

Criteria are FIT from E6.1 and written down before the runs; no criterion is moved after; a failing item is reported as failing under both criteria with the reason.

### 10.4 Tests

`test_checklist_criteria_from_reference` (the criteria file carries the reference percentiles and their n); `test_footer_counts`; `test_audit_known_answers`; `test_no_subsampling_in_published_audit`; `test_l2_gate_derived` (the gate's margin equals the stored null percentile).

### 10.5 Documentation

PHASE_6_REPORT (reference tables, criteria before/after, power table, checklist at the final n under both criteria, tuned-parameter ledger, leakage tables with percentiles and CIs, L3 results); CALIBRATION_REPORT rewritten as the E6 appendix; DECISION_LOG.

### 10.6 Compute / cost

Reference statistics: minutes; checklist at up to 500 seeds ≈ 20 minutes; audits at 200 seeds with all paths ≈ 3–4 hours (sklearn; the MLP is the slow part and is kept because it was pre-registered). **L3 probe API cost:** 200 probes × 5 models × 2 arms (normal, shuffled-V) = 2,000 short calls; at ≈ 2k input / 150 output tokens: Flash ≈ $1.5, GPT-5 mini ≈ $1, Sonnet 5 ≈ $5, Haiku ≈ $2.5, Opus 5 ≈ $12 — about **$25 total**; proposed for approval with the phase's pre-registration.

### 10.7 What could block it

Compute for the MLP surrogate at 200 seeds (mitigated by threadpool limits already in place); survivorship in the reference distributions (tails and drawdowns understated — reported, with the literature's full-universe values beside).

---

## 11. Phase 7. Targets, action and metrics

**Goal.** Resolvability threshold derived; regret decomposed into band adherence and directional agreement with correct floor and ceiling; bands checked against the environment's own risk and return; dividends paid or the field removed; the day-1 gate re-specified; baselines rebuilt on each cell's actual path.

**Weaknesses addressed.** 26, 27, 33, 48, 52, 53, 54, 56, 60.

### 11.1 Literature

- Resolvability: no finance paper defines a "resolvable mispricing" threshold; the derivation uses (a) the information available to the agent (the level-free surrogate's error in x, Phase 5/6), (b) the cost break-even (round-trip cost vs expected reversal profit over the half-life), (c) the within-run variability of x (Phase 2's T = 200 sd). Rebalancing-band literature for (b) and item 27: Donohue & Yip (2003, JPM) and Sun et al. (2006) on optimal rebalancing bands as a function of costs (to verify the 2–5-point bands at 5 bp).
- Bands and risk: Merton (1969/1971) with the environment's own (μ, σ) — the environment's price-only drift 6.5 %/yr, no dividend, annual σ ≈ 28 % (to be recomputed after Phases 1–3); the practitioner conventions already sourced (Morningstar, Vanguard, Fidelity, Betterment; verified); the JFE spread (Jiang, Peng & Yan 2024; verified) as the ordering check; Fieberg et al. (2025) for the LLM/robo gaps.
- Costs: Nasdaq (2024) 4.5 bp for the S&P 500 (verified), Frazzini, Israel & Moskowitz (median ≈ 6 bp); per-trade vs round-trip stated.

### 11.2 Experiments

E7.1 *θ derivation.* Three candidate derivations computed and reported: (a) θ_info = the |x| at which the level-free observables surrogate reaches sign accuracy 0.80 (so "resolvable" means resolvable from what the agent sees); (b) θ_cost = the mispricing at which the expected profit from a full reallocation over one half-life exceeds the round-trip cost at the adopted cost tier; (c) θ_var = one within-run sd of x at T = 200. All headline metrics (MCR and its decomposition, coverage, oracle switches, band-MAS) re-scored at θ ∈ {0.03, 0.05, 0.08, 0.12, 0.20} and at the three derived values on the pilot runs and on the baselines (no new API calls). Pre-registered rule: the default θ is θ_info (it is the only derivation that ties correctness to information), with (b) and (c) reported as sensitivities — unless θ_info falls outside [θ_cost, 0.20], in which case the team decides (D7).

E7.2 *Regret decomposition.* MCR is split into a band-violation term B_t = max(0, |C_t − centre| − hw) and a within-band directional term D_t = distance between C_t and the oracle's band edge, on resolvable steps only; both reported with the number of oracle target switches per run and the share of resolvable steps at each band edge (item 48). Floors and ceilings per term: ceiling = mandate-conditional oracle (0 by construction), floor = the worst of the trivial policies, with the lower-is-better sign handled in one function and documented in one place; normalised values recomputed for the pilot and labelled. The "one-shot side call" nature of the current environment is measured (switches per run) and, after Phases 2–4, re-measured; if the median stays at ≤ 1 switch per run the report says the benchmark measures a one-shot call, and the options (shorter half-life, longer T, per-window scoring) go to the team (D8).

E7.3 *Bands vs the environment's own risk-return.* Recompute the Merton shares with the environment's (μ, σ) after Phases 1–3 (with dividends paid, E7.4) for γ ∈ {2, 3, 4, 6, 8, 10}; report where each persona's practitioner band sits relative to them; present the two readings (practitioner categories vs utility-consistent bands) with the consequences for band-MAS and for the mandate oracle; D9 asks the team which is the scored default (the other becomes a sensitivity). The JFE-spread comparison (`targets.py:35`) is implemented as the pre-registered ordering check.

E7.4 *Dividends.* Paid into cash on ex-dates from the DPS process (quarterly), so that the shown yield is real; the accounting change is tested (portfolio value identity) and the effect on the baselines reported. If the team prefers to remove the field, both the field and its leakage channel go (D10).

E7.5 *Day-1 gate.* Pre-registered on the common-start design only (C_1 levels; KW, Cliff's δ, band-hit, AUC as before), with the null distribution from the O3 numerical-only arm and the no-persona trader; under start-at-target the gate is not computed (the ΔC_1 version is removed, with the reason recorded).

E7.6 *Baselines per cell.* `report_v2.cell_baselines` rebuilt from the run's `meta.json` (`env_metadata.gen_config`, engine, n_assets, b_pred, ordering, start price, everything hashed in `Gen_Config_Hash`), with a test that the baseline's path hash equals the run's.

E7.7 *Small items.* Trader band consistency (0, 1) everywhere; next-open execution logs both pre- and post-trade cash share (item 60); cost stated as per trade (5 bp per side = 10 bp round trip) with the anchor's convention named; the dead band and half-width given their Donohue–Yip anchor or labelled DESIGN with a sensitivity {0.05, 0.10, 0.15} for the half-width on the pilot re-score.

E7.8 *Metric validity checks carried over from the first review cycle* (audit items V4 and the consolidated report's metric-correlation requirement): (a) construct monotonicity — scripted policies with a swept parameter (allocation drift rate for band-MAS; value-alignment probability for the directional term; panic intensity for drawdown) must move each metric monotonically, reported as a table; (b) the metric-correlation matrix across cells (|r| among band-MAS, the two regret terms, return, drawdown, turnover) reported with the pre-registered statement of which pairs are expected to be collinear; a metric that is collinear with cash share by construction (as v1's ISFJ MAS was, r = −1.000) is named as such.

### 11.3 Decision rules

E7.1 (θ), E7.2 (decomposition), E7.3 (D9), E7.4 (D10); everything else is a correctness fix.

### 11.4 Tests

`test_theta_in_force_with_provenance`; `test_mcr_decomposition_identity` (B + D reconstruct MCR on synthetic runs); `test_floor_ceiling_signs`; `test_gate_common_start_only`; `test_baselines_same_path_hash`; `test_dividends_paid`; `test_trader_band_free`.

### 11.5 Documentation

PHASE_7_REPORT; `evaluation/targets.py` docstrings with sources; IO_CONTRACT sections 2.2–2.3; PILOT report re-scored under the new definitions with the old beside; DECISION_LOG; amendments (θ, MCR, gate, dividends).

### 11.6 Compute / cost

Re-scoring the pilot and baselines: minutes. No API cost.

### 11.7 What could block it

D7–D10 are team decisions; the θ_info derivation depends on Phase 5's fields (so this phase runs after 5 and 6).

---

## 12. Phase 8. Harness and statistics

**Goal.** Stateful-arm covariates and token budgets corrected; context length as a swept factor; mixed-model specification, clustering and multiplicity fixed; salience shares identified or dropped; a power analysis for the main grid.

**Weaknesses addressed.** 28, 55, 57, 59, 60 (placebo matching), 67 (random slopes, bootstrap CIs), harness constants from 34.

### 12.1 Literature

Liu et al. (2024, TACL, "Lost in the middle") for position effects as a function of context length; the "When Attention Closes" note already cited in the decision log; for statistics: Barr et al. (2013) on maximal random-effects structures, Bates et al. (2015) on parsimonious mixed models, Cameron, Gelbach & Miller (2008) on cluster bootstrap with few clusters, Benjamini & Hochberg (1995) and Benjamini & Yekutieli (2001) for dependent families, Gelman & Hill (2007) for crossed random effects.

### 12.2 Experiments

E8.1 *Stateful arm corrections.* (a) The mandate-offset covariate computed to the nearest mandate copy the model can attend to (the system-prompt copy and, in the memory arm, the last injected copy), both logged; (b) retained history stores the model's own turns without the injected block (the block is re-rendered for the current turn only), so the context does not contain 20 mandate copies, and the two stateful arms have matched token budgets (logged, tested); (c) parse fallbacks are not stored as the model's own prior turn (stored as "no valid answer"); (d) the token estimate uses the provider's usage metadata when available and a tokenizer-based count otherwise (`chars/4` only as a last resort, labelled); (e) placebo length/imperative matching asserted by a test on the rendered texts (word count within 10 %, same number of imperative clauses).

E8.2 *Context length as a factor.* Rolling window ∈ {5, 20, 50, full} pre-registered as a factor of the decay thesis; the summary arm keeps its matched rolling-5 control; the cost of the {50, full} levels is stated in Phase 9's grid.

E8.3 *Statistics.* Mixed model re-specified as crossed random effects (model and seed crossed, via `vc_formula` with a single group in statsmodels), random slopes for arm by model (pre-registered), reported with the variance components; cluster bootstrap by model and seed for every contrast CI; multiplicity controlled over the full pre-registered family (the count of contrasts is stated; BH within each pre-registered question family and Benjamini–Yekutieli across families as the conservative report); the circular-shift null replaced by a block-permutation null with enough distinct values (or reported as exact with its 7 values); the paired sign-flip kept. Tested on simulated data with known effects (power and size).

E8.4 *Salience shares.* Identified only on the common-start design with the directive factor and persona factor both present and the O3/no-persona reference levels; bootstrap CIs implemented; under start-at-target the shares are not reported (the collinearity is shown in the report); if the common-start cells are not in the main grid, the measure is dropped from the headline set and kept as exploratory (D11).

E8.5 *Variance pilot and power analysis for the main grid.* A pre-registered variance pilot: 1 model (Gemini 2.5 Flash) × 3 personas × 2 arms (static, memory) × 4 scenarios × 8 seeds × 3 decode replicates = 576 stateless runs (≈ 115,000 calls). From it: the variance components of MCR, its two terms, band-MAS and turnover across seeds, replicates and cells; the intra-class correlations; the minimum detectable effect for the arm contrasts at the planned seed × replicate counts; the seed/replicate/model counts of the main grid set from the power rule (Appendix A) for a pre-registered minimum effect (a band-MAS difference of 0.05, i.e. half a band half-width, and a Cliff's δ of 0.33 — the latter is a DESIGN choice that the team should confirm, D12). Cost ≈ $100 at Flash prices; proposed for approval with the phase's pre-registration.

### 12.3 Decision rules

E8.4 (D11), E8.5 (D12); the rest are correctness fixes with tests.

### 12.4 Tests

`test_stateful_no_duplicate_mandate`; `test_context_budget_parity`; `test_fallback_not_in_history`; `test_placebo_matching`; `test_mixed_model_crossed` (recovers a known crossed structure on simulated data); `test_bh_family_size_logged`; `test_salience_common_start_only`.

### 12.5 Documentation

PHASE_8_REPORT (corrections, the statistics-track specification with the simulated size/power checks, the variance pilot results and the main-grid power table); IO_CONTRACT 2.4–2.5; DECISION_LOG.

### 12.6 Compute / cost

Simulation checks: minutes. **API: the variance pilot ≈ $100 (Flash)**, or ≈ $40 with GPT-5 mini; a second model doubles it.

### 12.7 What could block it

Provider usage metadata availability (fallback tokenizer counts); D11/D12.

---

## 13. Phase 9. Sensitivity through the LLM harness

**Goal.** The generator parameters that drive results swept through a small LLM grid to show which conclusions are robust; the grid and its cost proposed here for approval before any paid call.

**Weaknesses addressed.** 8, 10, 12, 20, 21, 23 (LLM-side), 29.

### 13.1 Parameters and levels

Six generator parameters that change what the agent sees (θ is a scoring parameter and is re-scored on the same runs at no cost):

| Parameter | Levels (low / default / high) | Source of the levels |
|---|---|---|
| σ_V (value volatility) | FIT P25 / FIT / FIT P75 from Phase 1 (or the E1.3 bracket if D3 was needed) | Phase 1 |
| Mispricing half-life | 60 / FIT / 250 d at matched sd(x) | Phase 2 |
| GJR-GARCH set | P25 set / median / P75 set | Phase 3 |
| P/E multiple dispersion | P25–P75 / P10–P90 / P5–P95 | Phase 5 |
| Analyst error sd | 0.15 / LIT default / 0.45 | Phase 5 |
| Sentiment valuation loading | 0 (default) / half / full Baker–Wurgler-sized | Phase 5 |

Plus two harness factors already built: ordering ∈ {setup-first, event-first} and the calendar rendering (D6), so that the "time vs phase" claim is identified in the population actually run. Multi-asset provenance sensitivities (ρ_common, vol scale; item 29) run only in the 3-asset extension cell, not here.

### 13.2 Grid and cost (for approval)

Tier A (minimum that answers the question): 13 generator settings (6 × 2 non-default + default) × 3 personas × 2 arms (static, memory) × 3 scenarios (flat, crash δ 0.70, bull-trap) × 5 seeds × 1 replicate = 1,170 runs (≈ 234,000 calls) per model. Gemini 2.5 Flash ≈ $200; GPT-5 mini ≈ $80.

Tier B (adds a mid-tier and a frontier model on the six highest-impact settings): Tier A on Flash + GPT-5 mini (≈ $280), plus Claude Sonnet 5 on default + 6 settings × ISFJ/ENTJ × 2 arms × 2 scenarios × 5 seeds = 280 runs ≈ $280–$330 (less with caching). Total ≈ $600.

Tier C (adds the ordering/calendar factor and sustained-bull, and 3 replicates on the default setting): Tier B + ≈ 1,000 Flash runs ≈ $170 + 300 GPT-5 mini runs ≈ $20. Total ≈ $800.

Stateful arms are not swept here (≈ 7× the cost per run); the context-length factor (E8.2) runs in the main grid on the default generator setting.

All runs at 10–15 concurrent requests, checkpointed, with provenance hashes; every cell's baselines rebuilt on its own path (Phase 7).

### 13.3 Pre-registered robustness criteria

A conclusion (e.g. "re-injection lowers ISFJ band-MAS"; "the swapped mandate moves the allocation to the injected content") is called robust if, across all generator levels, (i) the sign of the arm contrast is unchanged, (ii) the BH-corrected q stays below 0.05 in the crossed mixed model with the generator level as a fixed factor, and (iii) the effect size stays within the CI of the default-level effect. Any conclusion that fails (i) at some level is reported as level-dependent with the level named. Interactions between generator level and arm are reported with CIs regardless. The decision rules that the second review cycle pre-registered for the content thesis (the swapped-mandate direction; "directive placebo effect below 30 % of the mandate effect") are evaluated at every generator level in the same table, so that the grid answers whether they hold for reasons of the environment or of the models.

### 13.4 Tests and documentation

`test_grid_manifest_matches_runs` (every planned cell has a run file with the right hashes); PHASE_9_REPORT with per-parameter effect plots and the robustness table; DECISION_LOG.

### 13.5 What could block it

Budget approval; provider rate limits (checkpointing handles retries); the roster (only Gemini/OpenAI/Anthropic keys exist).

---

## 14. Phase 10. Documentation, slides and script

**Goal.** Every document, the deck (`docs/env_v2/slides/`) and the speaker script corrected to the verified numbers, with sample sizes and calibration labels on every slide.

**Weaknesses addressed.** 7, 44, 45, 63, 74.

**Work.**
- A **claims ledger** (`docs/env_v2/v2_1/CLAIMS_LEDGER.md`): every quantitative claim in the spec, calibration report, decision log, README, slides and script, mapped to the generated file and the cell it comes from, with n and interval; a test that regenerates the ledger's numbers from the files and fails on drift.
- Slides regenerated by `tools/build_slides.py` from the generated files only (no hand-typed numbers), with: the tuned-parameter ledger tile replacing "nothing re-tuned to pass"; the L2 result as FAIL/PASS under the pre-registered and the derived gates with MAPE(V) and intervals; the level-free inferability statement replacing "withholds the level of value"; like-for-like before/after rows (same window, estimator, n) for the half-life, phase-from-calendar (mixed-set and within-scenario for both v1 and v2.1), R² (full and level-free for both), drawdown spread (pp of MDD per pp of δ); the engine named as decided in Phase 2; the analyst error as implemented; the sensitivity counts from the CSVs; the pilot's scenario count; causal readings removed from the pilot slide; every parameter slide carrying its provenance label (LIT/FIT/CAL/DESIGN) and n.
- The speaker script (`SPEAKER_SCRIPT.md` → docx via `tools/script_to_docx.py`) rewritten line by line against the ledger; the "Where the numbers come from" paragraphs replaced by the phase reports' sources.
- README, E1 spec, calibration report, IO contract, PILOT_NOTES, E1_E4_STATUS brought to v2.1; the v2 documents kept as history with a banner.

**Tests.** `test_claims_ledger_current`; `test_slides_built_from_generated` (no numeric literal in `build_slides.py` outside the data loaders).

**Compute / cost.** Slide regeneration only; no API cost.

**What could block it.** Nothing external.

---

## 15. Cross-phase summary: experiments, compute and cost

| Phase | Local compute (approx.) | API cost | Team decisions needed |
|---|---|---|---|
| 0 | 0.5 h | none | none |
| 1 | data download (hours, one-off) + 3 h | none | D1 (data substitutes), D3 (if the decomposition is not identified) |
| 2 | 4 h | none | none, unless FW vs AR(1) is a tie (rule decides) |
| 3 | 1 h | none | none |
| 4 | 2 h | none | D4 (ranges), D5 (gain formulation, if no formulation meets the rule), D6 (calendar rendering) |
| 5 | data retrieval (hours) + 3 h | none | none (analyst sd is LIT by necessity) |
| 6 | 5 h | ≈ $25 (L3 probe) | none |
| 7 | 0.5 h | none | D7 (θ, if the rule's condition fails), D8 (one-shot call), D9 (bands), D10 (dividends) |
| 8 | 1 h | ≈ $100 (variance pilot) | D11 (salience), D12 (minimum effect) |
| 9 | grid orchestration | $200 / $600 / $800 by tier | tier and roster |
| 10 | 1 h | none | none |

Total API spend proposed: about $325 before Phase 9, plus the Phase 9 tier. The main grid (execution-order step 3) is outside this plan's scope; its size is set by the Phase 8 power analysis. For orientation: none of the earlier planning or review documents fixes a model roster, seed count, replicate count or budget for the new grid (checked today across the cycle-1 audit, the consolidated report, the cycle-2 verification report, the position update, the novelty note, the execution order and the resubmission plan); the only prior cost figures are the cycle-1 audit's order-of-magnitude table (memoryless full grid of 1,620 runs ≈ $1.0–2.5k; full-transcript sub-grid $4–12k before caching), which this plan's per-run prices supersede. The earlier rounds did ask for open-weight models (Llama-3.3-70B, Qwen2.5-72B, Gemma-3-27B) as mechanistic anchors; the v2 harness supports them through OpenRouter or a vLLM endpoint, for which no key or endpoint is configured (D2).

---

## 16. Order, dependencies and gates

0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10, with two cross-links: the per-stock GARCH fit (E3.1) is run inside Phase 1/2's data step because the SMM and the jump analysis need it (Phase 3 then confirms and documents it); Phase 7's θ derivation needs Phase 5's fields and Phase 6's surrogate. Each phase ends with its report and stops. A phase is re-opened if a later phase's evidence contradicts its decision (e.g. Phase 5's field redesign changing the level-free inferability that Phase 1 stated); the re-opening is a logged decision.

v2.1 acceptance (the exit criterion of the whole plan): every item of `V2_WEAKNESSES.md` is closed as fixed, or documented as a labelled design choice with a sensitivity, or reported as a failure with its reason; the known-defect registry is empty; every number in every document is in the claims ledger; the checklist and audits are published at the pre-registered seed counts with intervals; the Phase 9 robustness table exists.

---

## 17. Decisions that only the team can make (asked now so that the phases do not stall)

- **D1.** Proceed on the free substitutes (yfinance survivor panel, EDGAR, SF Fed, Shiller, FRED) with the biases stated, or pause Phases 1–5 until CRSP/Compustat/OptionMetrics access exists.
- **D2.** The LLM roster and the budget tier for Phases 6, 8 and 9 (Gemini 2.5 Flash and GPT-5 mini as the workhorses; Claude Sonnet 5 as the frontier model — or Opus 5 at 2.5× the cost).
- **D3.** If the firm-level value/mispricing decomposition is not identified from the panel: choose between (a) the Vuolteenaho-implied larger σ_V (V not smooth; x harder to infer from price), (b) the v2 value with the "smooth fundamental" rationale withdrawn, or (c) two environments run as a factor. The report will show the audit and checklist consequences of each.
- **D4.** Where the index episode tables and the single-stock panel disagree on event ranges, which population the benchmark's crashes and bubbles represent.
- **D5.** If no event formulation meets the script-share/rejection rule.
- **D6.** Calendar rendering default: random calendar dates, no date, or "Day-N" kept as an arm (affects comparability with v1).
- **D7–D10.** θ (if the information-based derivation falls outside the bracket), the one-shot-call issue (shorter half-life, longer horizon, or per-window scoring), practitioner vs utility-consistent bands, dividends paid vs field removed.
- **D11–D12.** Salience shares (common-start only, or dropped) and the minimum effect size for the main-grid power analysis.
- **Commit points.** Whether to tag "v2.0 frozen" after Phase 0 and to commit at each phase end.

---

## Appendix A. Power-analysis formulas used in the pre-registrations

- Share-type criterion (share ≥ p0 of paths): with a true share p1, one-sided α = 0.05, power 0.80: n = (z_{0.95}√(p0 q0) + z_{0.80}√(p1 q1))² / (p1 − p0)². For p0 = 0.80 and p1 = 0.75: n ≈ 420 paths; for p1 = 0.70: ≈ 110.
- Median/correlation criterion with an acceptance band of width w: the cross-seed sd s of the statistic is taken from a 50-seed pilot; n such that 1.96 · 1.25 · s/√n ≤ w/5 (the 1.25 is the median's efficiency factor for near-normal statistics; bootstrap otherwise).
- Generator-vs-real equivalence (two-sample KS with bound D0 = 0.10): with n_real ≈ 3,000 windows, n_gen ≥ 350 gives 80 % power to detect a true distance of 0.10 + 0.05 at α = 0.05 (KS critical value c(α)√((n1 + n2)/(n1 n2))).
- LLM arm contrasts (paired by seed and replicate): n_pairs = 2(z_{0.975} + z_{0.80})² σ_d² / Δ², with σ_d the sd of the paired difference from the variance pilot and Δ the pre-registered minimum effect (D12); the model-level version replaces n_pairs by the number of models and σ_d by the between-model sd of the per-model effect.
- Every pre-registration states which of these it used and the pilot variance it plugged in.

## Appendix B. The analytic level-free price-only bound for x

Under log P_t = log V_t + x_t with log V a random walk (variance σ_V² per day, drift μ) and x an AR(1) with coefficient ρ = 2^{−1/h} and innovation variance s_x²(1 − ρ²), the return r_t = μ + Δlog V_t + Δx_t is a stationary ARMA(1,1) process whose parameters are known functions of (σ_V, s_x, ρ). The steady-state Kalman filter for this state-space model gives the minimum-MSE estimate of x_t from the return history (and, without the level, nothing else), hence the maximal R²(x) any level-free reader of the price path can reach; its value is computed numerically for the adopted parameters and its sensitivity to (σ_V, s_x, h) tabulated. The surrogate's level-free R² must lie at or below this bound (within its CI); a surrogate above the bound indicates a leak through a non-price field or a level artefact. Under the v2 parameters (σ_V = 0.006, s_x ≈ 0.13, h ≈ 150–190 d) the bound is high because V is smooth; under a Vuolteenaho-type σ_V it falls sharply — which is the design consequence D3 puts to the team.

## Appendix C. Numbers in the current documents that will be recomputed (for Phase 10's ledger)

Half-lives (60–120, 90, 120, 150, 187/188, 72, 14/26 d); the sustained-bull multiplier (0.25 vs 1.0); the jump rate (0.008 vs 0.010); the analyst sd (0.15 vs 0.35); the sensitivity pass/fail counts (five of six rows); "50 seeds" claims that are 20, 25, 150-of-400 or 12+10; the phase-from-calendar "100 % → 65 %" row; the "R² 0.90 → 0.83" row; the "±12 % off" L1 headline; the "within 0.02–0.08 of the oracle" L5 number (10 evaluation seeds); the pilot's "four scenarios"; every "plan anchor" attribution the fact-check flagged as approximate.
