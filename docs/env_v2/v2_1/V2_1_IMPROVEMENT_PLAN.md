# FinPersona-Bench synthetic environment: improvement plan v2 → v2.1

Status: **corrected draft for review. First draft 26 August 2026; corrected the same day by an independent third pass (changes marked [changed: reason]); reviewer edits applied 27 August 2026 (marked [edit 27 Aug]). No code was changed, no paid API was called, nothing was committed.** Execution starts only after this plan is approved, one phase at a time, with a written report and a stop for review at the end of every phase. The evidence for every [changed] tag is in `reviews/V2_1_PLAN_VERIFICATION_LOG.md` (cited as LOG §n); the alternatives for every unsettled choice are in `V2_1_ALTERNATIVES_REGISTER.md` (cited as REG-n); the plan review that prompted several changes is `reviews/review_of_V2_1_IMPROVEMENT_PLAN.md` (REV-n); the review of the third pass is `reviews/review_of_pass3_verification.md`. The first draft is kept in `archive/` for the audit trail only.

Scope: every item in `docs/env_v2/reviews/V2_WEAKNESSES.md` (74 items, plus the "what a robust v3 would need" list), the three reviews in `docs/env_v2/reviews/`, and the hard rules in `docs/env_v2/v2_1/V2_IMPROVEMENT_PROMPT.md`. The result is the same environment in the same repository, called **v2.1**.

Conventions used below. T = 200 trading days for the benchmark unless stated. "Path" = one (scenario, seed, delta) run of the generator. "Level-free" = features that do not depend on the price level (returns, ratios to moving averages, RSI, MACD/P). Provenance labels for every number: **LIT** (a specific published statistic, cited), **FIT** (estimated on a stated dataset by a stated method, with an interval), **CAL** (a calibration target: tuned to meet a criterion, and labelled as such wherever it is reported), **DESIGN** (a choice that evidence cannot decide, presented with its alternatives and consequences, chosen by the team, never by the implementer's preference). Nothing may be adopted with the label PLAN, ARB or "conventional". **[changed: a fifth label, ESTIMATE, is used only for the analyst-effort numbers in Section 15, which no source or experiment can supply; nothing else may carry it.]**

Note on file locations **[edit 27 Aug: `docs/env_v2/` was restructured on 27 Aug 2026]**: the v2 specification is in `docs/env_v2/spec/`, pre-registration in `preregistration/`, decisions in `decisions/`, the v1 baseline in `v1_baseline/`, status notes in `status/`, results in `generated/`; the three v2 reviews and `V2_WEAKNESSES.md` are in `docs/env_v2/reviews/`; this plan, the alternatives register and the prompts are in `docs/env_v2/v2_1/`, with the plan review, the verification log and the closing note in `docs/env_v2/v2_1/reviews/`. Phase pre-registrations and reports go to `docs/env_v2/v2_1/`, their outputs to `generated/v2_1/`. The research notes are in `docs/planning/env_v2_research/`, the earlier review rounds in `docs/reviews/cycle1/` and `docs/reviews/cycle2/`, the v2 design plan in `docs/planning/`.

**Reviewer edits of 27 Aug 2026** (from `reviews/review_of_pass3_verification.md`): (1) the stationary sd(x) ≈ 0.165 reported by the third pass was not reproduced on 27 Aug (two 200,000-step pilots gave 0.131 and 0.140; the calibration report's pilot 0.142) and was held — **[resolved 29 Aug, Phase 0, PHASE_0_REPORT §3.4]**: both numbers are right; `pilot_stats` simulates with raw innovation weights (w̄ ≈ 0.76, sd(x) 0.126–0.134) while the generator divides the weight by w̄, so the engine's stationary sd(x) is 0.165 (sd_e 0.016) / 0.175 (0.017), confirmed to three decimals by the pre-registered prediction and by an independent re-run; Appendix B's reference row is therefore s_x ≈ 0.175; (2) Claude Sonnet 5 and Opus 5 use a tokenizer that produces about 30 % more tokens for the same text (provider pricing page, read 27 Aug 2026), so their cost lines carry a 1.3× factor (Haiku 4.5, Gemini and GPT-5 mini are unaffected); (3) go/no-go G3 may not be passed by shortening the persistence below its fitted value; (4) Phases 1–6 run under the provisional start-price mechanism B (normalise the price), chosen by exclusion, until REG-1's LLM test in Phase 9, and the team is asked to approve that explicitly (D13); (5) the `.gitignore` line that hid `docs/env_v2/reviews/` is superseded by the restructure (`reviews/`, `v2_1/` and `slides/` are deliberately local).

---

## 0. What was verified before writing this plan

Everything in this section was recomputed on 26 August 2026 from the working tree at commit `b61fe07`; nothing in the repository was modified. Seeds and sample sizes are stated with every number. **[changed: a third-pass column with fresh seeds (7000+, 8000+) is added to every row; LOG §1.]**

### 0.1 Review findings reproduced (30 seeds per scenario unless stated)

| Item | Finding | First-draft value (n) | Third-pass value (n, new seeds) | Reviewer's value |
|---|---|---|---|---|
| 4 | Flat "control" biased cheap by jumps | mean x = −0.100, median −0.068, P(x<0) = 0.70, day-1 mean −0.076 (30 seeds × 200 d); with `jumps=False`: mean −0.018, P(x<0) = 0.50 | mean x −0.077 (SE 0.019, 50 seeds), median −0.074, P(x<0) 0.71, day-1 −0.087; jumps off +0.009 / 0.46 (30 seeds); analytic stationary mean −0.087 | −0.100 / −0.068 / 0.70 (C.4) |
| 2, 11 | FW switching inert at `price_scale = 100` | share of days with n_f > 0.99 = 0.981 (flat, 30 seeds); pilot n_bar 0.999 at the index set; **with `price_scale = 1` the index set gives n_bar = 0.827, i.e. a 17 % chartist share** (20,000-step pilot) | 0.975 (30 seeds); n̄ = 0.9985 (scale 100) / 0.8268 (scale 1) | 0.983–0.991 (C.1); **[changed: the published comparison is SABCEMM's DCA-HPM average chartist share 0.23 (kurtosis 7.8); the "≈ 0.17 / ≈ 10" pair is the DCA-WHP row; FW 2012 states no share; LOG §4.2]** |
| 68 | Analyst error implemented at sd ≈ 0.34, documented 0.15 | pooled sd(u) = 0.350, median \|u\| = 0.262 (30 crash paths × 460 d) | 0.306 (full 460 d incl. warm-up) / 0.330 (benchmark days); median \|u\| 0.222; analytic 0.15√5 = 0.335 | 0.335–0.338 (B.6, C.24) |
| 46 | IV is a one-day phase step at panic onset | mean jump in log IV at deterioration→panic = +0.594 (×1.81); calm day-to-day sd of log IV 0.084; z = 7.1 (30 crash seeds) | +0.606 (×1.83); −0.619 at panic→stabilisation; sd 0.086; z 7.06 (30 seeds) | +0.62, z ≈ 7 (C.6) |
| 18, 42 | Sustained-bull rejection selects the quiet sub-population | first-attempt paths: 17 accepted (daily sd 0.0150) vs 13 rejected (0.0242); rejection rate 0.38 (30 seeds) | 32/18 of 50; 0.0153 vs 0.0210; 0.36; mean attempts 1.6 | 33/27, 0.0147 vs 0.0240 (C.5); 39.8 % (checklist 17) |
| 36 | Half-life is an estimator artefact | sample half-life median 26 d at T = 200 (30 flat paths), 72 d at T = 800 (20 paths); only 55 % of T = 800 paths clear the 60-day floor | 35 d (30); 65 d (20); 60 % | 14 d on calm windows, 72 d at T = 800, 54 % clear (B.9) |
| 1 | Fixed start price is an answer key | ISFJ regret (MCR at θ = 0.05, 12 seeds): "compare price with 100" rule 0.014 flat / 0.007 crash / 0.005 bull-trap / 0.098 sustained-bull vs true-value oracle 0.003 and always-hold 0.11–0.14 | 0.022 / 0.011 / 0.007 / 0.083 vs oracle 0.000 (direct scoring), always-hold 0.100 | 0.014 / 0.007 / 0.005 / 0.098 (C.2) |
| 71 | Half-life numbers inconsistent | fallback φ = 0.463 gives pilot ACF(1) 0.9963 → 188 d, not the 150 d it was set for; `fw_index` at either `price_scale` gives ≈ 610 d | φ = 0.4632; same cached pilot → 188.5 d; **five 200,000-step pilots → 141–154 d (mean 147 d) against the pull-rate 150.0 d** (two further independent pilots on 27 Aug: 142 d and 160 d, confirmed); stationary sd(x) reported as 0.162–0.169 by the third pass, not reproduced on 27 Aug (0.131 / 0.140 raw-weight pilots) — **[resolved 29 Aug, Phase 0]**: engine 0.165 / 0.175 (sd_e 0.016 / 0.017), raw-weight pilot 0.126 / 0.134; ratio = w̄ 0.761 | 187 d (B.14) |

Conclusion: the headline findings hold on fresh seeds. **[changed: the "150 vs 188 d" discrepancy is sampling error of the single 20,000-step pilot cached in `mispricing.py` (SE of ACF(1) ≈ 0.0007 vs a gap of 0.0010), not an engine property; at 200,000 steps the ACF(1) half-life and the pull-rate half-life agree within 2 %. This changes Phase 0's test 0.4 and Phase 2's E2.5 (LOG §1, §7).]** The FW units question is settled at source (0.2) and the "72-day realised half-life" clears its own floor on barely half the paths.

### 0.2 Units of the Franke–Westerhoff model (evidence gathered today)

**[changed: read from the paper itself, LOG §4.4; the first draft's URL returns 404.]** FW 2012 (JEDC 36:1193–1211; PDF served at `https://www.uni-bamberg.de/fileadmin/uni/fakultaeten/sowi_lehrstuehle/vwl_wirtschaftspolitik/Team/Westerhoff/Publications/2011/JEDC_RF_FW_Fin.pdf`, 26 Aug 2026): eq. (1) "with respect to the log prices p_t … r_t := 100 (p_t − p_{t−1})"; eq. (5) "letting p_t be the (log) price … p_t = p_{t−1} + μ (n^f d^f + n^c d^c)"; eq. (6)–(7) d^f = φ (p* − p_t) + ε^f, ε^f ~ N(0, σ_f²), d^c = χ (p_t − p_{t−1}) + ε^c; the misalignment term is "the squared deviations of p_t from p*". DCA-HPM: φ 0.12, χ 1.50, α_0 −0.327, α_n 1.79, α_p 18.43, σ_f 0.758, σ_c 2.087, μ = 0.01, β = 1 (as in `mispricing.py`); joint bootstrap p-value 32.6 %. With p in natural-log units the noise contribution to a daily return is μ σ_f = 0.76 %, the right order for the S&P 500; in "log × 100" units it would be 0.0076 percentage points. The misalignment term therefore takes natural-log deviations: `price_scale = 1`. Pruna, Polukarov & Jennings (2016, arXiv:1604.08824) say the same in words ("p_t is the log price … p^f_t is the fundamental log value"). Phase 2's E2.1 becomes a reproduction check of the *pure* FW model (their noise, their equations), not an open question.

### 0.3 State of the test suite

`python -m pytest tests/` cannot collect: `tests/test_market_environment.py` imports `legacy_market_data`, which needs `vectorbt` (not installed). Excluding that file and the slow audit file, the suite gives **60 passed, 1 failed in 9 min 21 s**: `tests/test_env_logic.py::test_bull_trap_generation` asserts that the fundamental value stays flat (|V_1 − V_50| < 1) in a bull trap, which was true of v1's plateau and is false by design in v2 (V grows at μ_V; observed 100.0 → 106.2 over 50 days). These two are the "two legacy tests" of item 66; neither is a v2 defect. `tests/test_leakage_ci.py::test_v2_L2_surrogate_thresholds` is a **strict xfail**: a green CI currently requires the L2 leak to persist (item 66). The statistics tests emit MixedLM convergence warnings, which Phase 8's re-specification must not silence without explanation. **[changed: LOG §8.1 — with the slow audit file included the suite gives 1 failed (`test_bull_trap_generation`), 68 passed, 3 xfailed in 24 min 19 s; the "60 passed, 1 failed in 9 min 21 s" excluded that file and is consistent.]**

### 0.4 Data, compute and API facts that shape the plan

**[changed: every item re-checked on the network on 26 Aug 2026; LOG §5.]**
- **No CRSP, Compustat, OptionMetrics, I/B/E/S or RavenPack access** exists in this environment (WRDS is institutional-subscription only). This is the single biggest constraint on the "fit on data" rule. Free substitutes checked: `yfinance` (1.6.0 installed; 1.7.0 released 26 Aug), Kenneth French library, Damodaran datasets (last update 9 Jan 2026; `pedata.xls` served), **SEC EDGAR company-facts** (quarterly `EarningsPerShareBasic` and `CommonStockDividendsPerShareDeclared` with filing dates, 2009–2026, confirmed on Apple) and Financial Statement Data Sets (2009q1–2026q2), **SF Fed Daily News Sentiment Index** (daily since 1980, xlsx, updated 24 Aug 2026), **CBOE single-stock VIX files** (VXAPL, VXAZN, VXGOG, VXGS, VXIBM daily CSVs, 2011-01-07 → 2026-08-25 — better than the first draft expected), AAII (weekly since 1987, readable without login), Baker–Wurgler (monthly, ends Dec 2023), Shiller (the current file, to 2026.08, is at shillerdata.com; the Yale copy ends 2023.09). **Not usable as planned:** FRED was unreachable from this machine (the no-key CSV download is unverified); Stooq serves a JavaScript challenge to scripts; **the Wikipedia S&P 500 "Selected changes" table no longer exists on the article**, so the historical-constituent universe needs another public source, to be identified and logged before E1.0. Section 3 lists what each substitute can and cannot deliver and the survivorship bias it carries.
- Python 3.13.13; `arch 8.0.0`, `statsmodels 0.14.6`, `scikit-learn 1.9.0`, `scipy 1.18.0`, `numpy 2.4.6`, `pandas 3.0.3`; `lightgbm`, `numba`, `pandas_datareader`, `vectorbt` absent; `ta` present; 8 CPUs.
- Generator cost: 0.17 s per 200-day path including observables (measured; LOG §1); a 200-seed checklist (about 1,900 paths) is a few minutes on 8 cores; the 50-seed leakage audit (sklearn surrogates) takes about 10–20 minutes.
- API keys present in `.env` (names only): Anthropic, Gemini/Google, OpenAI, HF. No DeepSeek or OpenRouter key, so the roster is Gemini, OpenAI and Anthropic models unless keys are added (D2).
- Prompt sizes **measured on 26 Aug**: ISFJ track-B system prompt 6,041 characters (≈ 1,510 tokens at chars/4), one human message 2,234 characters (≈ 560 tokens); pilot output ≈ 120 tokens; the stateful rolling-20 arm averaged 19,500–20,000 context tokens per call (three pilot CSVs). Per 200-day run: ≈ 0.41 M input and 0.024 M output tokens (stateless), ≈ 3.9 M input (stateful).
- Prices read on the provider pages on 26 Aug 2026 and re-read on 27 Aug: Gemini 2.5 Flash $0.30 / $2.50 per M input/output tokens (Flash-Lite $0.10 / $0.40); **GPT-5 mini $0.25 / $2.00 (cached input $0.025) — the first draft's "$0.125 / $1.00 after July 2026 cuts" was wrong; no such cut is documented**; Claude Sonnet 5 $2 / $10 (the scheduled 1 Sept rise is cancelled), Haiku 4.5 $1 / $5, Opus 5 $5 / $25; batch 50 % at all three providers (usable only if the harness advances all runs in lock-step and batches each day's calls); Anthropic cache reads 0.1×. Per stateless run: Flash ≈ $0.18, GPT-5 mini ≈ $0.15, Haiku 4.5 ≈ $0.53. **[edit 27 Aug]** Claude 4.7 and later models (Sonnet 5, Opus 5; not Haiku 4.5) use a tokenizer that produces about 30 % more tokens for the same text (Anthropic pricing page, read 27 Aug 2026), so the chars/4 estimate is scaled by 1.3 for them: Sonnet 5 ≈ $1.4 per stateless run (≈ $0.7 with cached system prompt), Opus 5 ≈ $3.5. Per stateful run: Flash ≈ $1.24, GPT-5 mini ≈ $1.03, Sonnet 5 ≈ $10.5. OpenRouter serves Llama-3.3-70B ($0.10 / $0.32), Qwen2.5-72B ($0.36 / $0.40), Gemma-3-27B ($0.08 / $0.16) if a key is added (D2).

---

## 1. How every phase is run (the protocol)

Every phase follows the same six steps, in this order, and its report is organised under the same six headings.

1. **Literature review.** For each parameter or criterion in the phase: the sources, the specific statistic each source reports (with table/page), what it can and cannot justify (index vs single stock, monthly vs daily, US vs global), and the range the literature gives. Numbers recalled from memory are marked "(to verify)" until read from the source; the phase report only cites what was read. **[changed: REV-4 adopted and made enforceable]** Every phase report carries a citation table with one of three statuses per statistic — read-and-correct / read-and-wrong (with the correction) / not-retrievable — and the URL and date; a statistic marked "(to verify)" may not appear in a parameter file, a test tolerance or a slide. The verification log's §4 is the starting table; citations it marks WRONG are corrected in this plan where they occur.
2. **Pre-registration, written before any run** (`docs/env_v2/v2_1/PREREG_PHASE_k.md`): the data or seeds, horizons, estimators, the exact statistic, the pass/fail or decision rule, the power analysis that sets the sample size, and what will be reported if the rule is not met. Thresholds are not moved after data are seen. If a pre-registered criterion turns out to be wrong, that is stated, the empirical reference distribution is derived in a separate documented step, and results are reported under both the old and the new criterion. **[changed: LOG §3, §7]** (a) every "equivalence" criterion is stated as a TOST-type bound on the *upper confidence limit* of the distance (bootstrap), never as "the test did not reject"; (b) every share-type or mean-type pass rule states both the detection power against the pre-registered alternative and the equivalence margin it accepts; (c) every rule states what happens if its condition is never met (e.g. "θ_info = ∞ → D7").
3. **Runs.** Every result is saved under `docs/env_v2/generated/v2_1/` with the seed list, horizon, path count and the generator hash, so the phase report can be regenerated.
4. **Decision with evidence** (`DECISION_LOG.md`, one entry per decision): the alternatives, the evidence for each, why the others were rejected, the provenance label (LIT/FIT/CAL/DESIGN). Deviations from the v2 plan go to `PREREGISTRATION_AMENDMENTS.md`. Where evidence cannot decide, the entry says so and lists the options with consequences; the phase stops and asks.
5. **Regression tests** that lock the decision in (`tests/test_v2_1_phase_k.py`): statistical tests with pre-registered tolerances and the seed count that gives them power, plus the hash freeze.
6. **Documentation**: the phase report (`docs/env_v2/v2_1/PHASE_k_REPORT.md`), updates to the spec, calibration report, I/O contract, and the claims ledger (Phase 10) so that no document carries a number the generated files do not support.

Reporting rules that apply everywhere: every number carries its n (seeds, horizon, paths) and a 95 % interval where one can be computed (cluster bootstrap by path for pooled statistics); before/after comparisons use the same window, estimator and seed count; failures are reported as failures; every tuned parameter is labelled CAL where it appears.

Power-analysis rules (formulas in Appendix A): for a share-type criterion the seed count is set so that a true share 5 pp on the wrong side of the criterion is detected with 80 % power at α = 0.05 (about 420 paths for a criterion at 0.80); for a median or correlation criterion the seed count is set so that the bootstrap 95 % half-width is at most one fifth of the width of the acceptance band; for generator-vs-real comparisons the criterion is an equivalence bound on the bootstrap upper confidence limit of the two-sample Kolmogorov–Smirnov distance (D0 = 0.10), with the seed count set so that a true distance of 0.05 passes with 80 % power **[changed: LOG §3 — a plain KS test at these sample sizes rejects D = 0.10 with 97 % power, so non-rejection cannot serve as equivalence; the bootstrap is also the default for median/correlation criteria]**. Seed counts that come out of these rules are stated in each phase; where a rule would need more compute than the phase budget, the phase says so and reports the achieved power instead of pretending.

Git: everything stays on `main`, in the working tree; no commit, amend, reset, stash or push unless asked in that message. At the end of each phase the report lists the changed files. Points at which a commit or tag would be natural are marked "(commit point, if you wish)". The frozen v1 code and the plan document are never modified.

---

## 2. Weakness-to-phase map

Every item of `V2_WEAKNESSES.md` is assigned to exactly one phase that closes it; items that several phases touch are listed under the closing phase with the contributing phases in brackets. **[changed: LOG §2]** Item 13 (where jumps belong *and* their size) closes in **Phase 3** (Phase 1 decides the placement, Phase 3 re-fits the size distribution, because removing the negative jump mean lowers the flat-path kurtosis share from 0.85 to 0.60–0.70 and re-opens checklist item 2); item 47 closes in **Phase 4** (Phase 3 only supplies the variance multiplier); item 60 is split — next-open logging in Phase 7, placebo matching in Phase 8; item 1 is closed by Phase 1 **for the price channel only** and re-tested for the field channels in Phase 5 (REV-1).

| Phase | Items closed |
|---|---|
| 0 Verification and freeze | 39, 44 (count of scenarios), 53 (label), 54 (input bug; re-specification in 7), 65, 66, 68, 69, 70, 71, 72, 73 (crash V drift statement, trader band, t5 sum, $1 threshold), 74 (list only; corrected in 10) |
| 1 Value and price structure | 1 (price channel; field channels re-tested in 5), 3 (level-free audit; field redesign in 5), 4, 5 (restated after the level-free audit), 8, 9, 13 (placement only), 43 (level-free L5), 50 |
| 2 Mispricing engine | 2, 10, 11, 35, 36, 38 (ar1 included), 62 |
| 3 Volatility | 12, 13 (size/rate), 14, 25, 46, 73 (GARCH fit on regime paths) |
| 4 Events, schedule, controls | 6, 15, 16, 17, 18, 19, 41, 42, 47, 49, 51, 58 (shared event; per-asset start in 1) |
| 5 Observables | 3, 20, 21, 22, 23, 24, 34 (undocumented observable constants), 45 |
| 6 Audits and checklist methodology | 5, 7 (the tile: what was tuned), 30, 31, 32, 37, 40, 61, 63, 64, 67 (held-out scenario, L3 probe) |
| 7 Targets, action and metrics | 26, 27, 33, 48, 52, 53 (convention), 54 (re-specification), 56, 60 (next-open logging) |
| 8 Harness and statistics | 28, 55, 57, 59, 60 (placebo matching), 67 (random slopes, bootstrap CIs), harness constants of 34 |
| 9 Sensitivity through the LLM harness | 8, 10, 12, 20, 21, 23 (LLM-grid sensitivities), 29 (multi-asset provenance sensitivities) |
| 10 Documentation, slides, script | 7, 44, 45, 63, 74 |

Items 34 and 73 are split by module: the constants that belong to the generator are documented in the phase that owns the module; harness constants in Phase 8.

---

## 3. Data sources, their substitutes and their biases

The hard rules require every parameter to be fitted or tested on data. The datasets the reviews name are not available here, so the plan states what will be used instead, what it cannot deliver, and where that leaves a parameter literature-anchored with a sensitivity instead of fitted.

| Need | Ideal source (unavailable) | Substitute (checked / to check) | What it delivers | Known bias, and how it is handled |
|---|---|---|---|---|
| Daily prices and volume, ≥ 100 US large caps, 2000–2024 | CRSP | Yahoo Finance via `yfinance` (checked); **[changed: LOG §5]** a second source for cross-checks is still to be identified (Stooq serves a JavaScript challenge to scripts and cannot be used) | adjusted close, volume; enough for GARCH fits, variance ratios, volume models, drawdown/run-up episodes, real 200-day windows | survivorship: only currently listed tickers download. Mitigation: build the universe from the historical S&P 500 constituent list (**[changed]** the Wikipedia "Selected changes" table no longer exists; another public constituent-history source must be identified and logged before E1.0 — candidates: the SEC's ticker/CIK lists for coverage, the Financial Statement Data Sets' filer universe for delisting dates) and download every ticker that still resolves; report the share of delisted names that could not be retrieved and, for the statistics that survivorship affects most (tails, drawdown depths, volatility level), report the result on the survivor sample beside the literature value for the full universe |
| Quarterly fundamentals (EPS, dividends, book value), report dates | Compustat | SEC EDGAR: XBRL company-facts API (one call per CIK) and the quarterly Financial Statement Data Sets (to check) | quarterly EPS (basic/diluted), DPS, filing dates (10-Q/10-K), 2009–2025, all filers | starts 2009; tag inconsistencies across filers (handled with the standard `us-gaap` tags and manual checks on a sample); announcement dates (8-K earnings releases) differ from filing dates by up to two weeks and are taken from 8-K Item 2.02 filings where needed |
| Index-level valuation history | Compustat/S&P | Shiller monthly data (checked reachable; **[changed]** the current file, to 2026.08, is at shillerdata.com — the Yale copy ends 2023.09): S&P price, earnings, dividends, CAPE, 1871– | long-run P/E and payout distributions, index-level earnings volatility | index level only; used for time variation of multiples and drift anchors, not cross-sections |
| Cross-sectional P/E | Compustat | EDGAR EPS × yfinance prices (constructed); Damodaran's industry P/E files (checked reachable) as a cross-check | trailing P/E cross-section by year, P10–P90 | large-cap survivor universe; negative-earnings firms (P/E undefined) reported separately |
| Implied volatility, single stocks | OptionMetrics | **[changed: LOG §5]** CBOE's own VIX file (FRED was unreachable from this machine on 26 Aug; the no-key CSV is unverified); CBOE single-stock VIX indices (VXAPL, VXAZN, VXGOG, VXGS, VXIBM — **checked: daily CSVs served, 2011-01-07 → 2026-08-25**); published single-stock VRP statistics (Carr & Wu 2009; Goyal & Saretto 2009 — Bakshi & Kapadia 2003 RFS is index-only and is dropped for the single-stock claim) | IV–RV relation at index level daily; single-stock IV levels for five mega-caps, 15 years, daily | the single-stock IV model is FIT on the five names (with the caveat that they are mega-caps) with the literature values beside it; the audit tests its information content rather than its level |
| Daily news sentiment | RavenPack, Tetlock's factor | San Francisco Fed Daily News Sentiment Index (**[changed]** checked: daily since 1980, xlsx, updated 24 Aug 2026; Shapiro, Sudhof & Wilson 2022, J. Econometrics 228); Tetlock 2007 statistics (verified in the fact-check: 8.1 bp next day, 6.8 bp reversal); Garcia 2013; AAII weekly (public); Baker–Wurgler monthly (public) | persistence of daily sentiment, contemporaneous and lagged return relations at the market level | market-level, not single-stock; the single-stock loading is bracketed by the market-level estimate (upper bound on persistence) and reported as LIT+sensitivity |
| Analyst target prices | I/B/E/S | none free | — | literature only (Brav & Lehavy 2003; Bradshaw, Brown & Huang 2013; Bilinski, Lyssimachou & Walker 2013; Da & Schaumburg 2011); the error sd is a LIT value with an LLM-grid sensitivity (Phase 9) |
| Crash and bubble episodes | — | Mishkin & White 2002 (NBER w8992), Barro & Ursúa (**[changed: LOG §4.2]** NBER w14760, 2009; journal version *Research in Economics* 71(3), 2017 — w22743 is a different paper), Greenwood, Shleifer & You 2019 (JFE 131; verified: 40 run-ups, 21 crashed, 20/53/80 %), Sornette's LPPLS literature (Pagan & Sossounov's 25/15-month durations were not read from the paper and may not be quoted until they are); plus single-stock episodes constructed from the price panel | durations, depths, recovery shares, run-up sizes, crash probabilities, hazard shapes | index and industry episodes are few (tens); single-stock episodes from the survivor panel understate depth; both reported |

If the team can obtain WRDS access (CRSP/Compustat/OptionMetrics/IBES), Phases 1–5 re-run their fits on it with the same pre-registered code; the plan is written so that the substitute results are labelled and replaceable. **Decision needed from the team (D1, Section 17): proceed with the substitutes, or pause Phases 1–5 until WRDS access exists.** REG-15 gives the survivorship rule that decides between the two and the hybrid.

**[changed: REV-6 adopted]** Survivorship: names that delisted before `yfinance`'s coverage are exactly the crashes, tails and drawdowns Phases 3, 4 and 6 need. The reference distributions for checklist items 2, 3, 8 and 20 and the crash-episode tables are therefore biased toward calmer stocks; every slide that shows them says so, and D1 (WRDS access through the institution) is a real option. Where the bias can be quantified it is: the share of the historical constituent list that cannot be retrieved, and the difference between survivor and literature full-universe values for the tail and drawdown statistics.

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
- Half-life statements (71) and stale numbers (72): **[changed: LOG §1 item 71]** every document states the same numbers: pull-rate half-life 150 d; long-pilot ACF(1) half-life 147 d (five × 200,000 steps, range 141–154); sample half-life at T = 200 ≈ 26–35 d and at T = 800 ≈ 62–72 d (estimator-biased); stationary sd(x) of the engine 0.165 / 0.175 (sd_e 0.016 / 0.017; raw-weight pilot 0.126 / 0.134 — the two published numbers measure the same engine under different weight normalisations; [resolved 29 Aug, Phase 0 §3.4]) vs 0.128 (T = 800 sample). The 188 d figure is replaced everywhere, and `pilot_stats` is re-run at 200,000 steps (a logged change of a cached constant, not a design change); the sustained-bull multiplier is 1.0 and the jump rate 0.010 everywhere; the pilot covered three scenarios (44).
- Item 73: the trader band (0.4, 0.6) in the runner is replaced by the band-free convention used by the metrics; the common factor's t-mixture is documented as "not t5"; the crash V drift after deterioration is documented as a stated choice pending Phase 4; the $1 holdings threshold is documented.
- Scenario count in the script (44) and every "50 seeds" claim that is not 50 seeds get the correct n (list compiled by the reproduction script for Phase 10).

0.2b *Corrections to the current deck, immediately.* **[changed: REV-10 adopted]** Phase 0 produces a one-page `docs/env_v2/v2_1/DECK_CORRECTIONS_NOW.md` listing the sensitivity counts (fw_index 8/7, omega 7/8, panic×3 9/6, panic×6 8/7, Pruna 7/8 — verified against the CSVs), the "nothing re-tuned" tile, the analyst sd, the pilot's scenario count and the half-life numbers, so that nobody presents the wrong figures before Phase 10.

0.3 *Freeze.* `tests/test_v2_freeze.py`: SHA-256 manifest of `envs/v2/**/*.py`, `envs/synthetic_market.py`, `envs/v2/params/*.json`, `evaluation/{stylized_facts,leakage_audit,observables_oracle,metrics_v2,baselines_v2,targets}.py`; `simulation/provenance.py::env_provenance` hashes the manifest, not just the facade file, so `Env_Code_Hash` changes when any generator module changes. The manifest is regenerated deliberately at each phase end (the regeneration is itself a logged decision). (Commit point, if you wish: "v2.0 frozen".)

0.4 *Statistical regression tests* (`tests/test_v2_1_stats.py`), each with the seed count from the power rule and a stated tolerance:
- `test_flat_x_unbiased`: 100 flat seeds × 200 d, |mean x| ≤ 2 SE (cluster by seed). Currently fails (item 4); marked `xfail(strict=True, reason="defect 4; fixed in Phase 1")` and flipped to a hard test in Phase 1.
- `test_analyst_error_sd`: passes after 0.2.
- `test_iv_continuity`: z of the log-IV change at the deterioration→panic and panic→stabilisation transitions ≤ 3 against the calm day-to-day sd (30 crash seeds). Fails now; strict xfail until Phase 3.
- `test_fundamentalist_share`: with the engine's own parameters, mean n_f within the FW-published range and share of days with n_f > 0.99 below 50 %. Fails now; strict xfail until Phase 2.
- `test_half_life_consistency`: the engine's pull-rate half-life and the long-simulation ACF(1) half-life agree at 200,000 steps. **[changed: LOG §1]** A **hard test from Phase 0** (it passes: 147 vs 150 d), not a strict xfail; its tolerance is set from the ACF(1) sampling SE at 200,000 steps (≈ 0.0002 → ± 8 d) rather than 25 %.
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
**[changed: every recalled number replaced by the value read at source, LOG §4.1; unverifiable ones marked]**
- Vuolteenaho (2002), *J. Finance* 57, "What drives firm-level stock returns?" (read, NBER w8240 version): firm level, annual panel VAR, 1954–96; for market-adjusted returns the cash-flow-news variance is 0.080 vs expected-return-news 0.016 (ER-news share ≈ 0.25, s.e. 0.10), correlation of the two 0.41; the ordering reverses for the equal-weighted portfolio. Use: an upper bound on how "smooth" V can be for a single stock — but note the annual frequency; the daily σ_V must be FIT (E1.2), this only bounds it. This matters because the v2 rationale ("the majority of single-stock variance is idiosyncratic mispricing, CLMX 2001") conflates idiosyncratic-vs-market variance with fundamental-vs-transitory variance; CLMX (read: firm-level share of a typical stock's variance 0.72) say nothing about mispricing.
- Cohen, Polk & Vuolteenaho (2003), *J. Finance*, "The value spread" (read): 75–80 % of the cross-sectional B/M variance is profitability (≈ 55 %) plus the 15-year persistence of B/M (≈ 25 %); expected returns 20–25 %. Use: same bound, different method.
- Campbell (1991), Campbell & Shiller (1988), Cochrane (2008 RFS "The dog that did not bark"; read: long-run return coefficient 1.09 vs dividend growth 0.09, CRSP VW annual): at the index level the decomposition goes the other way (discount-rate news dominates). Use: to state why index-level anchors cannot set a single-stock σ_V.
- Poterba & Summers (1988, JFE 22; read): transitory component sd 15–25 % at index level, more than half of monthly return variance; Fama & French (1988, JPE; read): ≈ 25 % of 3–5-year return variance predictable for large-firm portfolios and ≈ 40 % for small-firm portfolios (the first draft's "25–45 %" is corrected; the post-1940 clause was not read and is not used); Summers (1986, JF; read): fads model, α = 0.98 monthly, half-life ≈ 3 years; De Bondt & Thaler (1985, JF; read): loser-minus-winner 24.6 % at 36 months. Use: the size of the transitory component and its horizon (these are the same evidence Phase 2 uses for persistence).
- Bartram & Grinblatt (2018, JFE, "Agnostic fundamental analysis works"; read): **[changed: attribution corrected]** reports the *alpha* of a convergence trade (up to 10 %/yr, decaying to zero over 34 months), not an average absolute mispricing level; use: the horizon of signal decay only. Rhodes-Kropf, Robinson & Viswanathan (2005, JFE; read): **[changed]** reports group *means* of the firm-specific error, not its dispersion or persistence; not usable for h. Lee, Myers & Swaminathan (1999, JF) and Frankel & Lee (1998, JAE): existence confirmed, the reversion speed and the 36-month spread were not retrievable; they support the *form* (cointegration of P and V) only.
- Drift: Dimson, Marsh & Staunton (UBS Yearbook 2025; read) — **[changed]** the 4.3 % is the world premium vs bills since 2000, not long-run; the US 1900–2024 nominal equity return is 9.7 % vs bills 3.4 %; Shiller's monthly file gives the price-only US return directly (FIT); Damodaran implied ERP 4.33 % (Jan 2025) confirmed. Use: μ_V as a FIT value from Shiller with an insensitivity check.
- Tails of fundamental shocks: the distribution of quarterly EPS surprises and of announcement-day returns (Ball & Brown 1968; Foster 1977; the earnings-announcement return literature, e.g. Kothari's 2001 survey for magnitudes; to verify). Use: whether V shocks should be Student-t, and whether jumps are fundamental.

Start-price randomisation: no literature is needed for the principle (a nuisance parameter must carry no information). **[changed: REV-1, REV-11a]** The principle is unchanged; the mechanism is not settled — see E1.1 and REG-1. Where a range is needed (mechanisms A and C) it comes from the empirical distribution of US large-cap share prices (from the panel), reported as P5–P95.

Burn-in: standard simulation practice; the test is an equivalence bound on the KS distance between the day-1 state and the long-run state distribution (E1.5).

### 5.2 Experiments (pre-registered in PREREG_PHASE_1.md before running)

E1.0 *Shared data panel* (used by Phases 1–6): (a) daily adjusted close and volume for every ticker in the historical S&P 500 constituent list that `yfinance` still serves, 2000-01-01 to 2024-12-31, target ≥ 300 names, of which the "large-cap analysis set" is the ≥ 100 names with the longest complete histories plus a random sample of the shorter ones; (b) EDGAR quarterly EPS, DPS and filing/announcement dates for the same names, 2009–2025; (c) CBOE's VIX file (FRED if it becomes reachable) **[changed]** plus the five CBOE single-stock VIX histories; (d) SF Fed daily news sentiment (confirmed); (e) Shiller monthly (shillerdata.com). The constituent-history source is identified and logged first (Section 3). Deliverable: `data/panel/` (git-ignored) plus `docs/env_v2/generated/v2_1/panel_manifest.md` (tickers, date ranges, survivorship accounting). Compute: an afternoon of rate-limited downloads; no API cost. **[edit 29 Aug: E1.0 done. The panel is at `datasets/` (git-ignored; eight need folders, each with a generated `README.md`, plus `_manifests/` holding the survivorship accounting, ticker-reuse screen, source agreement and quality checks; fetch code in `tools/e1_0_data/`); the report is `v2_1/E1_0_DATA_REPORT.md`. 1,094-name universe from three constituent sources; 673 retrieved, 428 full 2000–2024, 587 flag-free; of the 342 names that left the index only 16 are genuinely recoverable (4.7 %), because Yahoo serves whichever company holds the ticker today (86 of 673 series are a different company). All five CBOE single-stock VIX files, Nasdaq's public API as the second price source, AAII by manual download. The per-stock GARCH fits (E3.1) were not run in the data step and are still to do at the start of Phase 1.]**

E1.1 *Start-price answer key.* **[changed: REV-1 and REV-11a adopted; the first draft's test replaced, LOG §2]** Three mechanisms are implemented behind one switch and pre-registered together (REG-1): (A) randomise the level — V_1 ~ LogUniform(P_lo, P_hi) with (P_lo, P_hi) FIT as the P5–P95 of large-cap closes on 40 random panel dates, P_1 = V_1 e^{x_1}; (B) normalise the price — P_1 ≡ 100, V_1 = 100 e^{−x_1}; (C) both — rendered price = 100 on day 1 *and* a random rendered scale k_render applied to all price-denominated fields (price, SMAs, analyst estimate, EPS, DPS) so that the LLM sees both a level-free day-1 anchor and a random magnitude. Under every option the day-1 price carries no information about x_1 (the Kalman bound of Appendix B is identical for A, B and C); they differ in (i) the LLM-side magnitude nuisance (a "$18 stock" vs a "$420 stock"), (ii) what a stateful reader sees on day 1, (iii) comparability with v1/v2 runs. **Test (replaces "R² of x_1 on log P_1 < 0.01", which is failed by design under A for any plausible range — R² = var(x_1)/(var(x_1)+var(log V_1)) ≈ 0.02 at LogUniform(20, 500) — and met trivially under B):** at 500 seeds the level-feature attacker of review C (GBT on price, SMA20, SMA50 and their lags) reaches an R²(x) no higher than the level-free attacker's within its cluster-bootstrap CI, in every scenario; and the "compare price with 100" rule's MCR is within the CI of the constant-edge policies. The discriminating LLM experiment for A vs B vs C is REG-1 (≈ 60 Flash runs ≈ $11), run in Phase 9; until then Phases 1–6 use B as the provisional mechanism (D13, [edit 27 Aug]). Phase 1 reports that the analyst field and EPS × k still reveal V_1 under every option; that channel is Phase 5's.

E1.2 *Value–mispricing decomposition on data* (joint with Phase 2). On the panel: variance ratios VR(k) of daily log prices for k ∈ {5, 10, 20, 60, 120, 250, 500} per stock, pooled with a block bootstrap (block 250 d) for intervals; the model log P = log V + x with V a random walk with drift (variance σ_V²) and x an AR(1) (sd s_x, half-life h) implies a closed-form VR(k); fit (σ_V, s_x, h) by minimum distance to the pooled VR curve; also per sub-period (2000–07, 2008–12, 2013–19, 2020–24). Second method: log(P/V̂) with V̂ = trailing-4Q EPS × the sector-median multiple (EDGAR), quarterly 2009–2025: AR(1) with the median-unbiased correction (Andrews 1993) gives h and s_x; σ_V from the variance of Δlog V̂. The two methods are reported side by side with intervals. **[changed: REG-5]** A third estimator (SMM with persistence-carrying moments, E2.3) is added to the comparison; the rule for disagreement among the three is REG-5's (a simulation-recovery study on synthetic panels with known h decides which estimators are usable; the usable estimator with the smallest RMSE whose data interval contains the others' point estimates is adopted; if the usable estimators' intervals are disjoint, none is adopted and the persistence sweep E2.6 runs over the union of their intervals). Pre-registered decision rule for σ_V: if the estimators' σ_V intervals overlap, adopt the pooled estimate (FIT); if they do not, adopt neither and present both with the consequences (Section 17, D3). **[changed: LOG §7]** Caveat: VR(500) has ≈ 8 non-overlapping windows per stock in 25 years, so the pooled block-bootstrap CI will be wide.

E1.3 *σ_V sweep through the audits.* σ_V ∈ {0.004, 0.006, 0.010, 0.015, 0.020}/day × df_V ∈ {Gaussian, t5} at the current mispricing engine (so the effect of σ_V alone is isolated), 200 seeds per scenario: L2 level-free price-only R²(x) (surrogate and the analytic Kalman bound, Appendix B), L4 coverage at θ ∈ {0.03, 0.05, 0.08}, checklist items 9 and 20, and the "MAPE of V from a long price average" statistic. This sweep is what makes the σ_V decision's consequences visible; the value adopted is the fitted one from E1.2, not the one that makes an audit pass. **[changed: LOG §3]** s_x is swept jointly ({0.10, 0.13, 0.165, 0.20}) because the Kalman bound depends on s_x/σ_V, and the analytic bound is tabulated beside the surrogate at every grid point.

E1.4 *Where jumps belong.* Data: on the panel, the distribution of standardised daily returns (residuals from the per-stock GJR-GARCH fit of Phase 3, run early here as E3.1) on earnings-announcement days vs other days: the share of |z| > 4 days that are announcement days, and the size distribution on each. Model variants: (a) jumps in V at announcement dates (quarterly, tied to the EPS process) plus a residual Poisson component in V; (b) jumps in x with zero mean; (c) current (negative-mean jumps in x). Pre-registered rule: E[x] in flat must be 0 within 2 SE at 200 seeds under whichever variant is adopted (this rules out (c) unless its mean is removed) **[changed: LOG §2]** with an equivalence margin (|E[x]| ≤ 0.02, i.e. below the smallest θ candidate 0.03 — the margin is DESIGN and labelled); between (a) and (b), adopt the one whose announcement-day/other-day kurtosis split is closer to the panel's (bootstrap upper limit of the KS distance below 0.10), and report both (REG-3). Consequence to state: variant (a) makes the EPS field carry the jump (as in reality), which the Phase 5 leakage audit must then test. **[changed]** Removing the negative jump mean lowers the flat-path share with excess kurtosis > 1.5 from 0.85 to 0.70 (mean-zero x-jumps) or 0.60 (no jumps) at 40 seeds (the 27-Aug re-run gives 0.70 → 0.55 → 0.45 on another kurtosis definition; the drop is the same), so the jump size distribution is re-fitted in E3.2 before checklist item 2 is re-scored.

E1.5 *Burn-in.* Draw the day-1 state from a stationarity test: 500 seeds, compare the day-1 distribution of (x, GARCH variance, n_f) with the distribution after 5,000 days (**[changed: LOG §7]** the criterion is "the bootstrap 95 % upper limit of the two-sample KS distance is below 0.10", not "KS < 0.10" — the critical value at these sizes is 0.086; REG-17 gives the long-burn-in vs stored-state alternatives); rule: burn-in ≥ 5 half-lives of the slowest state variable for every engine in the sensitivity set (including `fw_index` at ≈ 600 d), or sample the initial state from a stored long-run distribution. Report the KS statistic per engine.

E1.6 *Level-free leakage audits.* Re-run L1, L2, L2b, L4, L5 and the scenario-discrimination audit with (i) randomised start prices, (ii) `PRICE_ONLY_KEYS` replaced by a level-free set (returns at 1/5/20 d, log P/SMA20, log P/SMA50, RSI, MACD/P, trend), (iii) no `MAX_ROWS` subsampling, (iv) 200 seeds, (v) cluster-bootstrap intervals over paths, (vi) percentiles (p5/p10/p25/p50) of APE for every L1 candidate. Outputs restate items 3, 5 and 43: what a level-free reader can infer about x and V, with intervals, and the selectivity of the non-price fields against the level-free control (which is what Phase 5 must reduce). No gate is applied yet (Phase 6 derives the gates); the pre-registered v2 gates are reported as pass/fail for the record. **[changed]** The analytic bound (Appendix B) is printed beside every price-only R² with the note that under the v2 parameters it is 0.14–0.26 within a 200-day window and 0.40 at steady state (LOG §3).

### 5.3 Decision rules

- Start price: the principle (no information in the level) is settled; the mechanism A/B/C is decided by REG-1's experiment — **[changed: this was "randomised (no alternative survives)"; the mechanism is D13]**; the range (A, C) is FIT.
- σ_V, s_x, h: FIT from E1.2 (three estimators, REG-5 rule); otherwise D3 (REG-2 gives the three environments' consequences).
- μ_V: FIT from Shiller's price-only return (the DMS 4.3 % is not a long-run number and is dropped); insensitivity shown over 0–0.0005/day on the audits (E1.3 adds μ_V as a nuisance sweep at 50 seeds).
- df_V: FIT if the EPS-surprise tails distinguish Gaussian from t (KS on standardised quarterly EPS changes); otherwise reported as DESIGN with both variants in the checklist.
- Jumps: E1.4 rule.
- Burn-in: E1.5 rule.

### 5.4 Tests locked in

`test_start_price_carries_no_information` (**[changed]** the attacker-based test of E1.1, 500 seeds); `test_flat_x_unbiased` flipped to hard; `test_burn_in_stationary` (KS-distance upper limit < 0.10 for every engine); `test_kalman_bound_tabulated` (the bound is regenerated from `params/value.json`); `test_level_free_price_only_keys` (the audit's control set contains no level); `test_sigma_V_in_force` (the generator's σ_V equals the value in `params/value.json`, which carries its provenance record).

### 5.5 Documentation

PHASE_1_REPORT (panel manifest; decomposition fits with intervals per method and period; σ_V sweep tables; jump placement evidence; burn-in KS table; level-free audit tables with percentiles and intervals; the corrected statements for items 3, 5, 43); spec section 1 rewritten; `params/value.json` with provenance; DECISION_LOG entries; amendments for every deviation from the v2 plan (start price, σ_V, jumps, burn-in).

### 5.6 Compute / cost

Panel download: hours (rate-limited), one-off. Fits: minutes. Sweeps: 10 settings × 200 seeds × 4 scenarios (+ crash deltas) ≈ 12,000 paths ≈ 40 minutes on 8 cores; level-free audits at 200 seeds ≈ 1–2 hours of sklearn time. No API cost.

### 5.7 What could block it

- Panel construction: if fewer than 100 names with full 2000–2024 histories can be downloaded, the fits run on what exists and the report says so; the historical-constituent retrieval rate is reported.
- Identification of the decomposition (E1.2) may fail on 25 years of data per stock (variance ratios at k = 500 have few non-overlapping windows even pooled); the pre-registered fallback is D3.
- The σ_V answer may be much larger than 0.006 (Vuolteenaho-type evidence points that way). That would change the character of the benchmark (a less smooth V makes x harder to infer from price, which strengthens the "hidden value" claim and weakens the "playable from price" claim); **[changed]** with numbers: the level-free price-only bound falls from 0.40 (σ_V 0.006) to 0.23 (0.010) to 0.08 (0.020). The report will show both faces through E1.3 and E1.6; the team decides (D3).
- The constituent-history source (Section 3) must be resolved before E1.0.

---

## 6. Phase 2. Mispricing engine

**Goal.** Resolve the FW units against the original paper; decide between a working FW and an honest AR(1)+GARCH on pre-registered evidence; estimate the persistence from firm-level data with a proper method; report a bias-corrected half-life at the horizons the benchmark uses; sweep persistence through the checklist (and, in Phase 9, the LLM harness).

**Weaknesses addressed.** 2, 10, 11, 35, 36, 38, 62.

### 6.1 Literature

- Franke & Westerhoff (2012, JEDC 36:1193–1211): **[changed: read; URL corrected (Section 0.2); LOG §4.2]** equations, units, DCA-HPM parameters, the nine moments and p = 32.6 % confirmed; the paper states no mean chartist share. SABCEMM contest (arXiv:1812.02726; read): DCA-HPM average chartist share 0.23, excess kurtosis 7.8 (200 runs × 7,000 steps); the first draft's "0.17 / 10" pair is the DCA-WHP row. Pruna, Polukarov & Jennings (2016, arXiv:1604.08824; read): FW+ with a GBM fundamental, Table 1 parameters as in `mispricing.py`. Platt (2020, JEDC) and Grazzini & Richiardi (2015, JEDC): existence confirmed. Franke & Westerhoff (2014/2016) on the MSM bootstrap procedure.
- Persistence at the firm level: the corrected sources of 5.1 (Bartram & Grinblatt and Rhodes-Kropf et al. cannot supply h; Balvers, Wu & Gilliland 2000 (read) give a 3–3.5-year half-life at the index level by a panel method; Lee–Myers–Swaminathan and Frankel–Lee support the cointegration form only) — what each reports as a half-life or decay rate, and at what level (firm/industry/index).
- Estimator bias: Marriott & Pope (1954) and Kendall (1954) confirmed to exist (the leading-term formula attributed to them could not be read at source and is not quoted); Andrews (1993, Econometrica) median-unbiased estimation, confirmed; Lo & MacKinlay (1988) variance-ratio test with heteroskedasticity-robust standard errors, confirmed (note the 1990 RFS erratum). Use: the bias-corrected half-life and the persistence-carrying moments.

### 6.2 Experiments

E2.1 *Units verified at source.* **[changed]** Done (Section 0.2). What remains is the reproduction: simulate FW's **own** model (their price equation, their two Gaussian demand noises, no GARCH, no jumps, no drift) at the DCA-HPM set with `price_scale` ∈ {1, 100}, 200 runs × 7,000 steps as in SABCEMM, and compare the average chartist share and excess kurtosis with 0.23 / 7.8; the convention that reproduces them is confirmed. Simulating the v2 hybrid instead would fail both conventions and make the rule unmeetable (LOG §7). This is a bug fix once confirmed, logged as such (LIT).

E2.2 *Firm-level persistence estimate.* **[changed: REG-5]** Three estimators on E1.0: (i) the variance-ratio decomposition of E1.2 (shared); (ii) log(P/V̂) AR(1) on EDGAR fundamentals at monthly frequency (prices monthly, V̂ updated quarterly), 2009–2025, ≥ 100 names, with Andrews' median-unbiased correction and a block bootstrap over stocks and time; (iii) the SMM persistence-carrying moments of E2.3. Report the cross-sectional median half-life, P25/P75, and per sub-period for each. Pre-registered disagreement rule: REG-5's (usability from a simulation-recovery study; adopt the usable estimator with the smallest RMSE whose data interval contains the others' point estimates; if the usable intervals are disjoint, adopt none and run E2.6 over the union of the intervals so that Phases 6 and 9 show whether anything depends on the choice).

E2.3 *SMM redone properly* (on the same panel). Moments: FW's nine (lag-1 return ACF, mean |r|, Hill 5 %, ACF |r| at 1/5/10/25/50/100) plus persistence-carrying moments: variance ratios at 20/60/120/250/500 d and the ACF of log(P/SMA250) at lags 20/60/120; empirical targets pooled over ≥ 100 stocks with a block-bootstrap weight matrix (stored to disk, not a diagonal proxy); simulated model = the calm engine with the Phase-3 GJR-GARCH-t innovation (fitted in E3.1, which is run before this step) and the E1.2 value process; common random numbers, 20 paths × 5,000 days per evaluation (vectorised over paths); optimiser: differential evolution (scipy) with ≥ 20 starts including chartist-active regions, followed by Nelder–Mead polish; acceptance: χ² at 5 % with df = moments − parameters, plus FW's bootstrap p-value; full-parameter J profiles at the optimum; three sub-periods; start-J and end-J recorded. Compute: 20 starts × ~400 evaluations × ~0.3 s ≈ 40 minutes per sub-period.

E2.4 *Engine decision: FW vs AR(1)+GARCH vs a published FW variant.* **[changed: REG-4]** A third candidate is added — the published FW variant with a stochastic fundamental (FW+ of Pruna et al. 2016; read), whose structure matches v2's (V a GBM) — so that "a working FW" is compared against both an honest AR(1)+GARCH and a published model with the same decomposition. Pre-registered comparison: (a) SMM acceptance for each engine on the same moments (χ² at 5 % with df = moments − parameters, plus FW's bootstrap p); (b) held-out-period moment prediction (fit on 2000–2016, predict 2017–2024 moments; distance in bootstrap-sd units); (c) equivalence of the checklist and the level-free leakage statistics at matched persistence and variance (200 seeds; any item that differs by more than its CI is listed). Rule (asymmetric on purpose; ties go to the simpler model): FW or FW+ is adopted only if it is accepted at (a) *and* beats AR(1)+GARCH at (b) by more than one bootstrap sd on the persistence-carrying moments; if both qualify, the one with the smaller held-out distance; otherwise AR(1)+GARCH becomes the default, FW (with `price_scale = 1`) the sensitivity, and every document names the engine honestly. If FW is retained, the parameters are FIT (E2.3), not the index set.

E2.5 *Half-life reporting.* Simulation table: pure AR(1) with true half-life ∈ {30, 60, 120, 150, 250, 500, 600} d, T ∈ {200, 800, 2000, 5000}, 200 seeds each: the distribution of the naive ACF(1) half-life and of the median-unbiased estimate; the table becomes the lookup for the checklist item and the documents report (i) the analytic half-life from the pull rate, (ii) the median-unbiased estimate at T = 200 ("what the agent experiences": also sd of x within 200 days and the number of oracle target switches per run), (iii) at T = 5,000 (stationary). **[changed: LOG §1]** The "150 vs 188 d" diagnosis is withdrawn: the discrepancy was pilot sampling error; the documents report the pull-rate half-life and the 200,000-step ACF(1) half-life (147 d, range 141–154 over five pilots; 142 and 160 d in two further pilots) together with the T = 200 / T = 800 / T = 5,000 estimator table.

E2.6 *Persistence sweep.* Half-life ∈ {30, 60, 120, 250, 500} d at matched stationary sd of x (so persistence is isolated from variance) and, separately, at matched innovation variance: checklist at 200 seeds (all items), level-free audits at 100 seeds, hazard/topped share, rejection rates. **[changed]** The oracle-switch count per run is reported at every level because it feeds the go/no-go checkpoint (Section 16A): at the live half-life the medians are 0 (flat) / 0–1 (crash) / 1 (bull trap) / 2 (sustained bull) and the share of event-scenario runs with ≥ 2 switches is 0.23–0.45; at 60 d 0.37–0.50; at 30 d 0.50–0.67 with coverage falling from 0.81 to 0.42 in flat (LOG §2; 27-Aug re-run). The LLM sweep is Phase 9.

### 6.3 Decision rules

Stated in E2.1, E2.2, E2.4. The half-life is FIT (E2.2) with its interval; the engine is decided by E2.4; both bracketed by the E2.6 sensitivities; item 9's criterion is re-derived in Phase 6 from the panel, not stated.

### 6.4 Tests

`test_fw_units` (chartist share at the index set within the published range, 0.23 for DCA-HPM); `test_engine_named_honestly` (the metadata engine name equals the code path used; no silent fallback); `test_half_life_estimator_table` (the lookup table regenerates within tolerance at 50 seeds); `test_persistence_in_force` (pull rate matches `params/mispricing.json` with provenance); `test_fundamentalist_share` flipped to hard (if FW retained) or removed with a note (if AR(1)); `test_half_life_consistency` is already hard from Phase 0.

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

**[changed: LOG §4.2]**
- GARCH on single stocks: Engle (2001, JEP; read: α 0.077, β 0.905 on a 50/30/20 Nasdaq/Dow/bond portfolio, daily 1990–2000 — portfolio level, not "index"), Hansen & Lunde (2005, JAE; read: leverage models beat GARCH(1,1) on IBM daily), Glosten, Jagannathan & Runkle (1993; monthly, confirmed — not a daily γ range), Bollerslev (1986). The daily single-stock α/γ/β/ν distribution will be FIT; the literature provides the sanity range (persistence 0.95–0.99; ν 4–8), cited as such.
- Jumps: Lee & Mykland (2008, RFS; read: rejection at β* = 4.6 at 1 %, intraday) jump detection with local volatility; Andersen, Bollerslev & Diebold (2007, REStat; read: jump variation is 14.4 % of realised variance for S&P 500 futures 1990–2002, 27.9 % of days with a significant jump — index futures); Kou (2002) / Bates (1996) jump-diffusion parameterisations (existence confirmed); the earnings-announcement return literature (Phase 1) for fundamental jumps. Use: rate per year, size distribution, sign asymmetry, and the announcement/non-announcement split.
- Regime-conditional variance: Ang & Timmermann (2012; read: monthly S&P σ 4.89 % vs 2.45 %, variance ratio ≈ 4.0), Ang & Bekaert (2002; read: 7.04 % vs 3.77 %) — both index, monthly, usable as sanity ratios only; **Hamilton & Susmel (1994): the variance factors could not be read (paywalled) and may not be quoted**; Schwert (1989, JF; read: recession/expansion volatility +76 % (1859–1986) to +227 % (1927–86), index, monthly); Greenwood, Shleifer & You (2019; read: volatility rises in run-ups that crash; industry level, monthly). Use: sanity ranges for the multipliers, which are FIT from single-stock event windows.
- Implied volatility and the variance risk premium: Carr & Wu (2009, RFS; read: individual-stock log VRPs negative for 21 of 35 names, mean VRPs mostly insignificant), Goyal & Saretto (2009, JFE; read: the sort is on log(RV/IV), not log(IV/RV)), Bollerslev, Tauchen & Zhou (2009, RFS) and Bollerslev & Todorov (2011, JF) on the index VRP; Christensen & Prabhala (1998, JFE; read: log RV on log IV slope 0.76, R² 39 %, S&P 100 monthly). **Bakshi & Kapadia (2003) RFS is index-only and is dropped for the single-stock claim.** Use: the IV = f(past RV, GARCH forecast) mapping, the premium size and its state dependence, and the noise around it — now FIT on the five CBOE single-stock VIX histories (Section 3).

### 7.2 Experiments

E3.1 *Per-stock GJR-GARCH-t fits* (`arch`): every name in the analysis set, full sample and four sub-periods; report cross-sectional median and IQR of α, γ, β, ν, persistence, unconditional daily sd; survivor bias stated (survivors have lower unconditional variance; reported beside the literature's full-universe values). Adopt the median (FIT); the P25 and P75 sets are sensitivities run through the checklist (Phase 6) and the LLM grid (Phase 9).

E3.2 *Jumps.* On the standardised residuals from E3.1: Lee–Mykland-type detection at a pre-registered threshold (|z| > 4 with the local-volatility correction), rate per year, mean and sd of jump sizes, negative share, and the announcement-day split (E1.4). Adopt the FIT rate and size distribution for whichever placement E1.4 chose.

E3.3 *Phase variance multipliers from event windows.* On the panel: single-stock drawdown episodes ≥ 30 % (peak-to-trough), run-ups ≥ 100 % over 2 years (GSY-style), and the market-wide crash windows (2008Q4, 2011Q3, 2018Q4, 2020Q1, 2022H1); for each episode, realised variance in windows defined relative to the trough/peak (pre-event calm; deterioration = the 40 days before the largest 20-day decline; panic = the 20 days around it; stabilisation = the 60 days after the trough; mania/blow-off/post-top analogously for run-ups) divided by the pre-event calm variance; medians with bootstrap CIs. Adopt the FIT multipliers; report the literature ratios beside them.

E3.4 *How the regime enters the variance.* **[changed: REG-6]** Three mechanisms — scaling the whole conditional variance (v2, amendment A3), scaling ω with a FIT ramp, and a fitted two-regime switching-variance model (regime variances and transition probabilities FIT on the panel's event windows, the scripted phases setting only the regime probabilities) — decided by the empirical rise and decay time: from the panel's single-stock episodes (n stated; the two index examples, 2020 ≈ 10 trading days and 2008 ≈ 30, are not a sample), the number of days from onset (first 10 % decline) to peak 21-day realised variance and the post-peak decay half-life, with bootstrap CIs; the mechanism (and ramp length, FIT) whose rise time and decay half-life both fall inside the empirical 95 % CI is adopted; if two do, the one with fewer free parameters; if none does, all three are reported against the CI and the whole-variance scaling is kept as the documented shortfall. All are kept as engine options.

E3.5 *Implied volatility without a step or look-ahead.* Construction: IV_t = √(252 · σ̂²_{t+1..t+21}) · (1 + π_t) · exp(ε_t), where σ̂² is the 21-day forecast of a GJR-GARCH filter run on the observed returns only (the same model class, so the filter is a past-only function of the price path; the hidden regime enters only through the returns it has already produced), π_t the premium as a function of the filter's variance level (FIT from the VIX–RV relation on FRED data and the single-stock VRP literature), and ε_t a noise term whose sd is FIT from the residual of the IV–RV regression. Pre-registered checks: (i) no field uses information from t+1 onwards (a code test); (ii) onset-detection audit (Phase 5/6): **[changed: REV-11b adopted]** IV's change-point detectability at phase transitions is compared against the *same filter's* 21-day realised-variance forecast, so that the premium's legitimate rise through returns is not counted as a leak; (iii) checklist item 13 re-derived from the empirical IV–RV distribution (Phase 6). **[changed: LOG §5]** The single-stock IV level and the premium π_t are FIT on the five CBOE histories (VXAPL…VXIBM, 2011–2026) against the names' realised variance, with the literature values beside them; the sensitivity remains. The `IV_PREMIUM_STRESS` decile trigger and the whole-path quantile are removed.

E3.6 *Item 73 (GARCH persistence on regime paths).* Item 5 of the checklist is computed on calm windows only and on the whole path, both reported.

### 7.3 Decision rules

All parameters in this phase are FIT with intervals; the single-stock IV level is FIT on five names (mega-caps, stated) with the literature beside it. The variance mechanism is decided by E3.4's rise-time rule.

### 7.4 Tests

`test_garch_params_in_force` (equal to `params/volatility.json` with provenance); `test_iv_no_lookahead` (IV at day t is unchanged when the path after t is altered; 20 seeds); `test_iv_continuity` flipped to hard with the tolerance derived in E3.5 (z at transitions ≤ the 95th percentile of the realised-variance change-point statistic); `test_jump_process` (rate and mean size within the FIT intervals at 500 seeds).

### 7.5 Documentation

PHASE_3_REPORT (fit tables, event-window multipliers with CIs, rise-time analysis, IV construction and its audits); spec section 4; `params/volatility.json`; DECISION_LOG; amendments (A3 revisited with evidence).

### 7.6 Compute / cost

GARCH fits: minutes; event-window analysis: minutes; checklist re-runs at 200 seeds for the quartile sets: ≈ 30 minutes. No API cost.

### 7.7 What could block it

Survivorship in the drawdown episodes (depths understated; reported); the five CBOE names are mega-caps (stated).

---

## 8. Phase 4. Events, schedule and controls

**Goal.** Crash and bubble durations, depths, discounts and hazard from historical episodes; the sustained-bull control on the same mispricing process as the flat market with published selection effects; the error-correction gains justified or replaced; orderings run in the grid; the calendar removed as a clock.

**Weaknesses addressed.** 6, 15, 16, 17, 18, 19, 41, 42, 47, 49, 51, 58 (shared event), 73 (crash V drift).

### 8.1 Literature

**[changed: LOG §4.2]**
- Mishkin & White (2002, NBER w8992; read): the 15 US stock-market crashes (≥ 20 % declines) of the twentieth century with dates and peak-to-trough magnitudes. **Barro & Ursúa: NBER w14760 (2009) / *Research in Economics* 71(3), 2017** (30 countries to 2006, 232 crashes defined as multi-year real returns ≤ −25 %; country index, annual) — w22743 is a different paper. Pagan & Sossounov (2003, JAE; existence confirmed) for the dating algorithm applied to the panel — **their 25/15-month durations were not read from the paper and are not quoted**.
- Greenwood, Shleifer & You (2019, JFE; read): 40 industry run-ups ≥ 100 % since 1928, 21 crashed (≥ 40 % drawdown) within 2 years; crash probability 20 / 53 / 80 % after 50 / 100 / 150 % net-of-market run-ups; volatility, issuance, acceleration and new-vs-old-firm performance predict crashes, turnover is high in run-ups that crash *and* in those that do not. **Industry** level, monthly. Use: hazard slope b (a logit of crash probability on log run-up), the topped share over a stated horizon, peak run-up sizes, and the sustained-bull ("did not crash") population's characteristics — the transfer to a single stock is under a stated assumption (E4.3).
- Sornette's LPPLS: Johansen, Ledoit & Sornette (2000), Filimonov & Sornette (2013, Physica A) for the linearised calibration; Sornette, Demos et al. (2015) "Real-time prediction and post-mortem analysis of the Shanghai 2015 bubble"; Sornette & Cauwels (2015). Use: the super-exponential exponent m ∈ (0, 1), ω, and the hazard's shape, fitted on the panel's run-ups and on Nasdaq 1998–2000.
- Cash-flow vs discount-rate decomposition of crashes: Campbell, Giglio & Polk (2013, *Review of Asset Pricing Studies* 3(1), "Hard times"; read): the 2000–02 decline was discount-rate driven, 2007–09 cash-flow driven (index, quarterly VAR). Use: the split between the fundamental drop D_V and the panic discount delta, and the delta levels.
- Sustained bull: GSY's 19 non-crashing run-ups (returns and volatility), the panel's run-ups that did not reverse within 200 days.
- Deterioration and stabilisation shapes: the cumulative-decline shapes of 1987, 2000–02, 2008, 2020 from the Shiller/FRED series; single-stock episodes from the panel.

### 8.2 Experiments

E4.1 *Episode tables.* Index episodes (Mishkin–White, Barro–Ursúa, Shiller series) and single-stock episodes from the panel (Pagan–Sossounov dating on daily data; drawdowns ≥ 20 % and ≥ 30 %; run-ups ≥ 100 %/2 y): peak-to-trough duration, depth, front-loading (share of the decline in the first third), share recovered within 60/120/200 days, the pre-decline "deterioration" length (days from the last high to the first 10 % down), and for run-ups the LPPLS fit (m, ω, hazard) and the peak P/V̂ using the EDGAR value proxy. Every quantity with its empirical P10/P50/P90.

E4.2 *Sampling ranges from the tables.* Pre-registered rule: each schedule parameter (setup length, deterioration length, panic length, D_V, delta, delta_end, front-loading, mania kappa, post-top length and drop) is drawn from the empirical P10–P90 (FIT), truncated only where T = 200 forces it, with the truncation rate reported; where the panel and the index tables disagree, the report shows both and the team chooses (D4). The current uniform ranges are shown beside the empirical ones so that the change is visible.

E4.3 *Hazard.* b from a logit of GSY's crash indicator on the log run-up (their 20/53/80 % points give the slope directly; the fit on the panel's own run-ups is the cross-check); h0 from the horizon (FIT); the "40–60 % topped" band and the P/V 1.6–2.5 band are retired as targets; the topped share becomes an outcome that is reported. **[changed: REV-11c adopted; REG-18]** The horizon assumption is written down: GSY's probabilities are two-year crash probabilities conditional on a two-year industry run-up; the daily hazard over a 40–150-day mania is obtained by (i) fitting b from the three GSY points, (ii) setting h0 so that the cumulative hazard over the median mania length equals the GSY probability at the median peak run-up scaled by the ratio of the mania length to GSY's two-year window — the scaling is an assumption (DESIGN) and is bracketed {0.5×, 1×, 2×} in the sensitivity table; REG-18 gives the alternative of fitting h0 and b directly on the panel's own run-ups, decided by which mapping's topped share falls inside the panel's CI. The calibration tool's arbitrary score and rejection penalty are removed. The uncapped mania run is included in the report (item 41).

E4.4 *Mania drift.* kappa and the mania length are drawn jointly from the LPPLS fits so that the drift cap is unnecessary (rule: the cap binds on < 5 % of mania days; convexity test on the pre-cap segment); if the fits do not support a super-exponential drift over 40–100 days, the report says so and offers a scripted-drift alternative with the shape FIT from the run-up table.

E4.5 *The sustained-bull control.* **[changed: REV-2a adopted; LOG §7; REG-7 — not decided here]** With d_t = 0 and no x-band (the first draft's proposal, and the v2 design plan's literal text), only 8 % of unanchored draws stay inside [−0.10, 0.15] (50 seeds; 94 % pass the V criterion; 7 % in the 27-Aug re-run), the path-mean x has p10/p50/p90 = −0.34/−0.11/+0.07, and the control becomes "flat market plus rising value" rather than "rising value without mispricing". Four definitions of the control are implemented and compared under one pre-registration (REG-7): (A) the same mispricing process as flat with no band (validity on V only: V_T/V_1 ≥ the FIT threshold from the non-crashing run-up table); (B) a band on V only with the mania driver switched off; (C) the anchored x of v2 (d_t = −0.15 x; dominated on the audit evidence but recorded); (D) a control defined on the rendered fields by matching the flat scenario's x distribution with a rising V, with the explicit statement that mispricing is present and the oracle acts on it. For every definition: the realised x distribution; accepted-vs-rejected volatility, ACF and IV (KS-distance upper limit < 0.10); the scenario-discrimination audit on demeaned, level-free returns with the rule that a classifier of sustained-bull vs flat days must be at chance (95th percentile of a label-permutation null, computed **here** because it needs only the generator — removing the dependency on Phase 6); and the execution order's acceptance test at baseline level ("adherence moves, regret does not": on the control the mandate-conditional oracle and constant-mix have the same regret within the CI while band-MAS differs across the trivial policies — this presupposes no resolvable mispricing and is only meetable by C; under A/B/D it is replaced by "the oracle's regret gap over constant-mix in the control equals its gap in flat within the CI"). The definition adopted is the one meeting the audits that serves the purpose the team states in D14 ("no mispricing" ⇒ only C serves it and its clock is published as a limitation; "rising value with the same mispricing" ⇒ A/B/D). The baseline-level test is re-run on the LLM cells in Phase 9.

E4.6 *Event dynamics.* **[changed: REG-8]** Four formulations, all implemented: (i) tracking gain λ (current), (ii) a shift of the perceived fundamental p* to the scripted target with a regime-specific pull φ_regime (FW-native: an event is a change in what fundamentalists believe, with the pull rate FIT from the panel's crash-window decay), (iii) an explicit drift with no feedback plus rejection, (iv) an unscripted regime-switching model without error correction (the event is a change in the fundamentalists' perceived p*, in the regime variance and in the drift of V, with no target path; depth and duration are outcomes — Campbell–Giglio–Polk's cash-flow vs discount-rate evidence supports giving events both a V and an x component). For each: the variance share of event-phase Δx explained by the script (R² of d_t on Δx; 0 for (iv) by construction), the share of paths whose peak-to-trough depth and duration fall inside the episode tables' P10–P90 (E4.1), the rejection rate, checklist items 10 and 20, the level-free leakage statistics, at 200 crash and 200 bull seeds; λ swept over {0.02, 0.05, 0.10, 0.25} for (i). Pre-registered rule: adopt the formulation with the lowest script share among those whose depth/duration coverage is ≥ 0.70 (the share of real episodes inside their own P10–P90 is 0.80 by construction; the 0.70 margin is DESIGN and labelled) and whose rejection rate is below the ceiling **pre-registered here from the episode tables** (not in Phase 6); if none qualifies, report and ask (D5). The adopted gain, if any, is labelled CAL.

E4.7 *Orderings and the calendar.* (a) event-first and phase-free orderings enter the LLM grid as a factor (**[changed: LOG §5]** `simulation/runner_v2.py` supports `ordering`, `experiments/arms_v2.py` has no ordering factor — it is added to the arm grid in this phase, tested); the mix and the setup range are set so that, within each scenario, the day-only phase classifier's accuracy is no higher than the majority class plus the margin derived from a label-permutation null at 200 seeds (**[changed]** the null is computed here, not in Phase 6; the rendering options and the ordering mix are REG-9, with an LLM-side phase-restatement probe of ≈ 90 Flash runs ≈ $16 in Phase 9); (b) the rendered day index: options are a calendar date from a random start date, no date, or "Day-N" as a disclosed-index arm; the pre-registered measurement is the same day-only classifier on what the agent can compute (for a stateless agent, nothing; for a stateful agent, the turn count); D6 asks the team which rendering is the default because it changes comparability with v1; (c) the quarter phase of `days_since_eps_announcement` randomised per seed; (d) `Schedule_Setup_Len` and the ordering logged (already).

E4.8 *Labels and small fixes.* Blow-off defined by a dynamic criterion (drift above a FIT threshold, or reported only for topped runs); top day recorded at the realised peak (off-by-one); crash V drift after deterioration stated and tested against the episode table's fundamental decline shape; the multi-asset shared event replaced by per-asset event draws with a common-factor loading FIT from the panel's cross-sectional correlation of drawdowns (the multi-asset provenance sensitivities themselves are Phase 9).

### 8.3 Decision rules

E4.2, E4.3, E4.6 rules above; the control is D14 (REG-7); the calendar rendering is D6 (REG-9).

### 8.4 Tests

`test_schedule_ranges_from_params` (draws inside the FIT ranges); `test_sustained_bull_selection` flipped to hard; `test_no_x_selection_in_control` (accepted and rejected paths have the same x distribution within a KS bound); `test_hazard_params_provenance`; `test_script_share_reported` (the event-phase script share is computed and stored in metadata); `test_day_index_rendering_option` (the renderer honours the chosen option); `test_arm_grid_has_ordering_factor`.

### 8.5 Documentation

PHASE_4_REPORT (episode tables with sources and P10/50/90; the sampling ranges before/after; hazard fit; mania drift fit; the control's published selection statistics; the gain comparison; the ordering/calendar audit); spec section 3; `params/events.json`; DECISION_LOG; amendments (A4, A5 revisited; the plan's x-band for the control retired).

### 8.6 Compute / cost

Episode analysis: minutes; four formulations (× 4 λ for the first) × 200 seeds ≈ 20,000 paths ≈ 1.5 hours; four control definitions × 200 seeds ≈ 30 minutes; ordering audits ≈ 30 minutes. No API cost (the orderings run in the LLM grid in Phase 9 / the main grid).

### 8.7 What could block it

Few index episodes (statistical tables will be thin; the panel supplies the mass); the LPPLS fits are notoriously unstable (the report will show the fit diagnostics and, if unstable, fall back to the scripted-drift alternative of E4.4); D4–D6 and D14 are team decisions.

---

## 9. Phase 5. Observables

**Goal.** Earnings, P/E multiple range, dividends, analyst error, sentiment, volume and technicals each anchored to a stated empirical source and designed so that no field is a deterministic function of the hidden state; audited for leakage with the level-free control and an onset-detection test.

**Weaknesses addressed.** 3, 20, 21, 22, 23, 24, 34 (observable constants), 45.

### 9.1 Literature

**[changed: every recalled number is replaced by the value read at source, LOG §4.3; the phase report may only carry read values]**
- Earnings: Foster (1977, Accounting Review; read — Model 1 is the seasonal random walk, Model 5 E(Q_t) = Q_{t−4} + φ(Q_{t−1} − Q_{t−5}) + δ is the usual "Foster model"; 69 firms, quarterly, 1946–74); Ball & Brown (1968) and Brown & Rozeff (1979) confirmed; **Kothari (2001) could not be read — no surprise magnitude is taken from it**; SEC 10-Q deadlines (40/45 days) and the announcement-lag distribution (EDGAR 8-K Item 2.02 dates). Use: EPS noise as the residual sd of the seasonal RW relative to the level (FIT on EDGAR), reporting lags (FIT), and the frequency of negative EPS (for the P/E cap: FIT P99).
- Multiples: the trailing P/E cross-section (EDGAR × prices; Damodaran industry files as cross-check) for the range; Shiller's series and the panel for the time variation of multiples (a slowly varying log-AR(1) for k_t, FIT). Use: replaces U(14, 22) by a FIT distribution and a time-varying multiple so that P/E never identifies V even asymptotically.
- Dividends: Lintner (1956, AER) not readable at source; secondary sources (Lambrecht & Myers; Fama & Babiak 1968) give a speed of adjustment ≈ 0.3 on **aggregate annual** data — usable only as a sanity range; Brav, Graham, Harvey & Michaely (2005, JFE) is a survey with no speed estimate; Leary & Michaely (2011, RFS) full text not read. Payout and quarterly stickiness are FIT on EDGAR DPS; whether dividends are cut in crashes is FIT from the 2008–09/2020 episodes.
- Analyst estimates: Brav & Lehavy (2003, JF; read: targets 28 % above price on average, Table VI; 900 firms, weekly consensus 1997–99), Bradshaw, Brown & Huang (2013, RAST; read: **absolute target-price errors average 45 %**, 38 % of targets met at 12 months, 64 % at some point, 2000–09), Bilinski, Lyssimachou & Walker (2013, TAR; read: mean absolute error 44.7 %, 59.1 % reached), Da & Schaumburg (2011, JFM), Gleason, Johnson & Li (2013, CAR) confirmed. So the error anchor is LIT: absolute error ≈ 45 % of price at a 12-month horizon (converted to a log-sd in REG-10d, with the horizon mismatch stated: the field is a *fair-value* estimate, not a 12-month target); the v2 value 0.15 is below every read value. Use: the error sd and persistence as LIT values with a Phase-9 sensitivity (no free target-price data).
- Sentiment: Tetlock (2007, JF; read: 8.1 bp next-day DJIA return per one-sd pessimism, 6.8 bp reversal over days 2–5 — **index level, daily**), Garcia (2013, JF; read: NYT 1905–2005, index), Boudoukh, Feldman, Kogan & Richardson (2019, RFS; read: news explains 49.6 % of overnight idiosyncratic volatility, firm level), Baker & Wurgler (2006, 2007; read: **monthly, market level**), Brown & Cliff (2004; existence only); the SF Fed Daily News Sentiment Index (Shapiro, Sudhof & Wilson **2022**, J. Econometrics 228; confirmed available). Use: the AR(1) of daily sentiment (FIT), the contemporaneous and lagged return loadings (FIT at market level, LIT at firm level), and whether any direct valuation loading is supported (Baker–Wurgler: at market level, yes, slowly; at daily single-stock frequency, no direct evidence) — **[changed: REV-2b adopted]** the valuation loading is not set to zero by fiat; the three designs and the audit that decides are E5.5 / REG-10b, and the default is recorded as D15 after the results.
- Volume: **Karpoff (1987, JFQA): the 0.2–0.5 range could not be read and is not used**; Gallant, Rossi & Tauchen (1992, RFS) and Llorente, Michaely, Saar & Wang (2002, RFS) confirmed; Lo & Wang (2000, RFS; read: weekly turnover-index AC(1) 0.91 (VW) / 0.87 (EW), **market level, weekly** — a sanity range, not the value); GSY (2019; read) on turnover in run-ups (elevated in all run-ups; not a crash predictor). Use: log-volume AR(1) and the |r| elasticity FIT on the panel; the |x| loading is supported only through the run-up turnover ratio (FIT from GSY-style run-ups in the panel), otherwise zero (REG-10c).
- Technicals: Wilder (1978), Appel (MACD), Brock, Lakonishok & LeBaron (1992); already reference-tested; unchanged.

### 9.2 Experiments

E5.1 *Multiple.* **[changed: REG-10a]** FIT the trailing P/E cross-section (P10–P90 by year) and the quarterly AR(1) of log P/E at the stock level (EDGAR × prices). Three designs are pre-registered: (A) a fixed k per seed from the FIT range; (B) k_t as a log-AR(1) per seed with the FIT dispersion and quarterly persistence; (C) k tied to a fitted cross-section on observable characteristics (dominated unless the observation contract changes; recorded). Decided by E5.7(a)'s per-field-group selectivity over the level-free control and the L1 extended inversion share at 200 seeds, at three widths (P25–P75, P10–P90, P5–P95): adopt the design with the lowest selectivity among those whose cross-seed P/E distribution is KS-equivalent (upper limit < 0.10) to the EDGAR cross-section; B if its selectivity is lower than A's by more than the null margin, else A. The Phase-9 LLM sweep uses the same widths.

E5.2 *EPS and lags.* FIT the seasonal-RW residual sd and the lag distribution; implement announcement dates from the FIT distribution; the quarter phase randomised (Phase 4); negative EPS handled as in the data (P/E undefined → rendered as "n/m", with the frequency reported; the cap becomes the FIT P99 or the field is n/m).

E5.3 *Dividends.* FIT payout and stickiness; dividend behaviour in crash episodes. **[changed: ordering, LOG §7]** D10 (pay dividends into cash vs remove the field) is put to the team **before** Phase 5 starts, since this step depends on it; if undecided, both variants are carried.

E5.4 *Analyst estimate.* **[changed: REG-10d]** Three options are pre-registered: (A) keep F_t = V_t e^{u_t} with a LIT sd — the read anchor is an absolute target-price error ≈ 45 % of price at a 12-month horizon (Bradshaw et al. 2013; Bilinski et al. 2013), converted to a log-error sd by the pre-registered mapping E|u| = sd·√(2/π) (≈ 0.56 if the 45 % is a mean absolute log error, or the direct FIT on the papers' error distributions where their tables give them), with the horizon mismatch stated; the bracket becomes {0.30, 0.45, 0.60} (the v2 0.15 is below every read value) and persistence stays DESIGN (no free data); (B) drop the field; (C) a lagged smoothed price proxy (an analyst who extrapolates; level-free by construction). Decided by the L2/L5 selectivity of the field at each sd level (A) vs (C) at 200 seeds, and by the Phase-9 grid (whether any arm contrast is level-dependent): A at a given sd is admissible if its selectivity is inside the null margin; C if its inclusion changes no arm contrast beyond the equivalence margin; B if neither holds. The report states plainly that no free data can fit the error sd.

E5.5 *Sentiment.* **[changed: REV-2b adopted; REG-10b]** FIT the AR(1) and the return loadings on the SF Fed index vs S&P returns (daily) and cross-check against Tetlock's published numbers. Three designs are pre-registered: (A) returns-only AR(1) (contemporaneous and lagged returns; level-free by construction), (B) returns plus a slow valuation link whose size is FIT as the regression coefficient of the SF Fed index on the Shiller CAPE log-deviation (monthly, market level, with its CI; "full Baker–Wurgler-sized" is defined as that coefficient, "half" as half of it; the transfer of a market-level coefficient to a single stock's log(P/V) is stated as DESIGN), (C) survey-style AR(1) with the weekly persistence and return loading FIT on AAII. The b_pred feedback is kept in all three. Decided by (i) the item-12 statistics against the FIT values with CIs and (ii) the L2 selectivity for x and V and the onset AUC: adopt the design meeting (i) with the lowest (ii); B's valuation link is retained only if its selectivity increment is inside the null margin, otherwise reported as the labelled sensitivity. The team's D15 records the default after the results.

E5.6 *Volume.* **[changed: REG-10c]** FIT ρ_v, the |r| elasticity and the noise sd on the panel; two designs: (A) |r| only; (B) |r| plus a run-up turnover ratio FIT from the panel's GSY-style run-ups. Adopt B if the FIT ratio's CI excludes 1 and B's onset AUC excess over price is inside the null margin; else A. The v2 |x| loading is dominated (no read evidence links volume to mispricing) and is recorded.

E5.7 *Audits.* (a) Level-free L2 with a per-field-group ablation (which field group adds how much R² for x and for V, with cluster-bootstrap CIs, 200 seeds); (b) the L1 extended candidate set (Phase 6's method) on the new fields; (c) the onset-detection audit: predict "a phase transition occurred within ±3 days" from each field's own changes vs from realised variance and returns; report AUC and timing error per field with a label-permutation null; rule: no field exceeds the price-derived AUC by more than the null's 95th percentile; (d) the earlier v2 gates reported for the record.

### 9.3 Decision rules

Every constant in `observables.py` ends this phase with a provenance label; FIT where the panel/EDGAR/SF Fed deliver, LIT+sensitivity where they do not (analyst sd), DESIGN only for the rendering of undefined values and the market-to-stock transfer of the sentiment valuation coefficient. Any field that fails the onset rule or adds more x-R² than the Phase-6-derived margin is redesigned or dropped; dropping is reported, not hidden. D10 is taken before the phase; D15 after E5.5.

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

E6.2 *Re-derived criteria.* For each item: the old (v2 plan) criterion and a new one of the form "the generator's cross-seed distribution of the statistic is equivalent to the real-window distribution" — **[changed: LOG §3]** stated as "the bootstrap 95 % upper limit of the two-sample KS distance is below D0 = 0.10", or the P10–P90 band with a share criterion; "the KS test did not reject" is not a criterion (at n_real ≈ 3,000 and n_gen ≥ 350 it rejects D = 0.10 with 97 % power); the alternatives for the criterion form and the seed/horizon policy are REG-14 — written in PREREG_PHASE_6 before the generator is re-run; results reported under both criteria; every item whose threshold was moved in v2 (9, 10, 11, 13, 17, 20; amendments A1, A2, A6, A7) listed in the **tuned-parameter ledger** together with the parameters tuned against it (α, γ, β, σ̄, jump rate, panic multiplier, φ, hazard) and the pre-amendment results beside the amended ones (item 7).

E6.3 *Power analysis per item* (Appendix A): the seed count per item from the rule in Section 1, using the cross-seed variance from a 50-seed pilot; a table of item → n → achieved power; the final checklist run at the maximum required n (expected 200–500 seeds per scenario; T = 200 for "what the agent experiences", with T ∈ {800, 2000} reported separately for the persistence and ACF-decay items, never as the pass criterion for a T = 200 property).

E6.4 *Per-scenario and calm-only reporting.* Items 2, 3, 5, 6, 12 reported on flat paths and calm windows separately from the pooled set (items 37, 50), with the regime-switching contribution quantified.

E6.5 *L1 extended candidate set.* Candidates: k·P, k·P/PE, k·P·DY, k·F, k·SMA50, k·SMA50/PE, trailing-EPS × k with per-path k, EPS-step tracking, averages of two and three candidates, the analyst estimate rescaled per path, and a small template search (products/ratios of up to three shown fields with one free scale); for each: the APE distribution (p5/p10/p25/p50) and the share of steps within 1/2/5 %; the pass rule derived from the noise floor implied by the x process (the share of steps that any level-free estimate could hit given sd(x)), not a hard-coded 1 %.

E6.6 *L2 gate derivation.* The analytic level-free price-only bound on R²(x) from the adopted (σ_V, s_x, h) (Appendix B), checked against the surrogate at every (σ_V, s_x, h) of Phase 1's sweep (**[changed]** under the v2 parameters the bound is 0.40 at steady state and 0.14–0.26 within 200 days, matching reviewer C's level-free R² of 0.40; LOG §3); the gate = selectivity of the non-price fields over the level-free control ≤ the 95th percentile of a label-permutation null (paths' targets permuted across seeds) plus the sampling half-width; MAPE(V) reported with intervals; the held-out-scenario split implemented (item 67); the L3 LLM probe implemented (200 probes stratified by scenario × phase × seed, ≥ 5 models, shuffled-V baseline, Wilson CIs; cost in Section 10.6).

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

Reference statistics: minutes; checklist at up to 500 seeds ≈ 20 minutes; audits at 200 seeds with all paths ≈ 3–4 hours (sklearn; the MLP is the slow part and is kept because it was pre-registered). **L3 probe API cost:** **[changed: LOG §6]** 200 probes × 5 models × 2 arms (normal, shuffled-V) = 2,000 short calls in total, 400 per model; at ≈ 2k input / 150 output tokens and today's prices with the 1.3× tokenizer factor on the Claude 5 models [edit 27 Aug]: Flash ≈ $0.4, GPT-5 mini ≈ $0.3, Sonnet 5 ≈ $2.9, Haiku 4.5 ≈ $1.1, Opus 5 ≈ $7.2 — about **$12 total** (the first draft's $25 matched neither reading of its own line); proposed for approval with the phase's pre-registration.

### 10.7 What could block it

Compute for the MLP surrogate at 200 seeds (mitigated by threadpool limits already in place); survivorship in the reference distributions (tails and drawdowns understated — reported, with the literature's full-universe values beside).

---

## 11. Phase 7. Targets, action and metrics

**Goal.** Resolvability threshold derived; regret decomposed into band adherence and directional agreement with correct floor and ceiling; bands checked against the environment's own risk and return; dividends paid or the field removed; the day-1 gate re-specified; baselines rebuilt on each cell's actual path.

**Weaknesses addressed.** 26, 27, 33, 48, 52, 53, 54, 56, 60.

### 11.1 Literature

**[changed: LOG §4.3]**
- Resolvability: no finance paper defines a "resolvable mispricing" threshold; the derivation uses (a) the information available to the agent (the level-free surrogate's error in x, Phase 5/6), (b) the cost break-even (round-trip cost vs expected reversal profit over the half-life), (c) the within-run variability of x (Phase 2's T = 200 sd). Rebalancing-band literature for (b) and item 27: Donohue & Yip (2003, JPM 29(4)) exists but its text is inaccessible — **the "2–5-point bands at 5 bp" attribution is unverified and is not used**; Sun et al. (2006, JPM; read) use 40–60 bp costs and a 5 % tolerance band in their examples.
- Bands and risk: Merton (1969/1971; confirmed) with the environment's own (μ, σ) — the environment's price-only drift 6.5 %/yr, no dividend, annual σ ≈ 28 % (to be recomputed after Phases 1–3); the practitioner pages (read): Morningstar equity bands 15–30 / 30–50 / 50–70 / 70–85 / 85+ %; Fidelity Conservative 20 % equity (80 % bonds + short-term), Balanced 50 %, Growth 70 %, Aggressive Growth 85 %; Vanguard conservative 40/60 (30/70 in retirement); Betterment conservative = 4–7 pp below the recommended stock share. Jiang, Peng & Yan (2024, JFE; read): Table 7 gives trait coefficients on the equity-to-wealth ratio (Neuroticism −1.74, Openness +0.94, Conscientiousness −1.32), **no stated conservative-minus-aggressive spread** — `targets.py`'s JFE_SPREAD (0.06, 0.12) must be re-derived from Table 7 in the phase report before it is used as the ordering check. Fieberg, Hornuf, Meiler & Streich (2025, CESifo WP 11666; read): LLM average equity share 67 % vs robo-advisors 59 %.
- Costs: Nasdaq (2024; read): 4.5 bp is the cap-weighted **quoted spread** of the S&P 500 basket; Frazzini, Israel & Moskowitz (2018 draft; read): **median market impact 6.18 bp** per trade (mean 9.97) — different cost concepts; the phase states which one the 5 bp per side represents, and per-trade vs round-trip.

### 11.2 Experiments

E7.1 *θ derivation.* Three candidate derivations computed and reported: (a) θ_info = the |x| at which the level-free observables surrogate reaches sign accuracy 0.80 (so "resolvable" means resolvable from what the agent sees); (b) θ_cost = the mispricing at which the expected profit from a full reallocation over one half-life exceeds the round-trip cost at the adopted cost tier; (c) θ_var = one within-run sd of x at T = 200. All headline metrics (MCR and its decomposition, coverage, oracle switches, band-MAS) re-scored at θ ∈ {0.03, 0.05, 0.08, 0.12, 0.20} and at the three derived values on the pilot runs and on the baselines (no new API calls). Pre-registered rule: **[changed: REV-7 adopted; LOG §7; REG-11]** θ_info and θ_cost are **co-primary** — every headline metric is reported at both, with θ_var and the fixed grid as sensitivities. The rule states its own failure modes: if the level-free surrogate never reaches sign accuracy 0.80 (review C measured 0.71 on resolvable steps), θ_info is reported as "not reached" and θ_cost alone is primary until Phase 9 shows whether any conclusion depends on the choice (D7); if a Phase-9 conclusion flips between θ_info and θ_cost, D7 is put to the team with the table.

E7.2 *Regret decomposition.* MCR is split into a band-violation term B_t = max(0, |C_t − centre| − hw) and a within-band directional term D_t = distance between C_t and the oracle's band edge, on resolvable steps only; both reported with the number of oracle target switches per run and the share of resolvable steps at each band edge (item 48). Floors and ceilings per term: ceiling = mandate-conditional oracle (0 by construction), floor = the worst of the trivial policies, with the lower-is-better sign handled in one function and documented in one place; normalised values recomputed for the pilot and labelled. The "one-shot side call" nature of the current environment is measured (switches per run; the counts are already known, Section 16A) and, after Phases 2–4, re-measured; if the median stays at ≤ 1 switch per run the report says the benchmark measures a one-shot call, and the options go to the team (D8; a shorter half-life is admissible only if it lies inside the FIT interval — [edit 27 Aug]). **[changed: REG-12]** Per-window scoring and the alternative ceiling/floor conventions are pre-registered as alternatives, with E7.8's construct-validity table as the discriminator (adopt the scoring under which every scripted sweep is monotone in its target metric and |corr(MCR, band-MAS)| across cells is below the pre-registered ceiling; if both the decomposition and per-window scoring qualify, the decomposition, for comparability with the pilot).

E7.3 *Bands vs the environment's own risk-return.* Recompute the Merton shares with the environment's (μ, σ) after Phases 1–3 (with dividends paid, E7.4) for γ ∈ {2, 3, 4, 6, 8, 10}; report where each persona's practitioner band sits relative to them; present the two readings (practitioner categories vs utility-consistent bands) with the consequences for band-MAS and for the mandate oracle; D9 asks the team which is the scored default (the other becomes a sensitivity; REG-13 gives the experiment, including both as a Phase-9 factor). The JFE-spread comparison (`targets.py:35`) is implemented as the pre-registered ordering check only after the spread is re-derived from Jiang–Peng–Yan Table 7.

E7.4 *Dividends.* Paid into cash on ex-dates from the DPS process (quarterly), so that the shown yield is real; the accounting change is tested (portfolio value identity) and the effect on the baselines reported. If the team prefers to remove the field, both the field and its leakage channel go (D10 — **[changed]** taken before Phase 5, Section 9).

E7.5 *Day-1 gate.* Pre-registered on the common-start design only (C_1 levels; KW, Cliff's δ, band-hit, AUC as before), with the null distribution from the O3 numerical-only arm and the no-persona trader; under start-at-target the gate is not computed (the ΔC_1 version is removed, with the reason recorded).

E7.6 *Baselines per cell.* `report_v2.cell_baselines` rebuilt from the run's `meta.json` (`env_metadata.gen_config`, engine, n_assets, b_pred, ordering, start price, everything hashed in `Gen_Config_Hash`), with a test that the baseline's path hash equals the run's.

E7.7 *Small items.* Trader band consistency (0, 1) everywhere; next-open execution logs both pre- and post-trade cash share (item 60); cost stated as per trade (5 bp per side = 10 bp round trip) with the anchor's convention named (quoted spread vs market impact); the dead band and half-width labelled DESIGN (the Donohue–Yip anchor could not be read) with a sensitivity {0.05, 0.10, 0.15} for the half-width on the pilot re-score.

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

E8.5 *Variance pilot and power analysis for the main grid.* A pre-registered variance pilot: 1 model (Gemini 2.5 Flash) × 3 personas × 2 arms (static, memory) × 4 scenarios × 8 seeds × 3 decode replicates = 576 stateless runs (≈ 115,000 calls). From it: the variance components of MCR, its two terms, band-MAS and turnover across seeds, replicates and cells; the intra-class correlations; the minimum detectable effect for the arm contrasts at the planned seed × replicate counts; the seed/replicate/model counts of the main grid set from the power rule (Appendix A) for a pre-registered minimum effect (a band-MAS difference of 0.05, i.e. half a band half-width, and a Cliff's δ of 0.33 — the latter is a DESIGN choice that the team should confirm, D12; **[changed: LOG §10]** "0.33 is conventional" is not a justification under the hard rules; the team states the minimum effect in the claim's own units — the practitioner bands are 20 pp wide, so 0.05 band-MAS is a quarter of a band). Cost **[changed: LOG §6]** ≈ $105 on Flash or ≈ $86 on GPT-5 mini; proposed for approval with the phase's pre-registration.

### 12.3 Decision rules

E8.4 (D11), E8.5 (D12); the rest are correctness fixes with tests.

### 12.4 Tests

`test_stateful_no_duplicate_mandate`; `test_context_budget_parity`; `test_fallback_not_in_history`; `test_placebo_matching`; `test_mixed_model_crossed` (recovers a known crossed structure on simulated data); `test_bh_family_size_logged`; `test_salience_common_start_only`.

### 12.5 Documentation

PHASE_8_REPORT (corrections, the statistics-track specification with the simulated size/power checks, the variance pilot results and the main-grid power table); IO_CONTRACT 2.4–2.5; DECISION_LOG.

### 12.6 Compute / cost

Simulation checks: minutes. **API: the variance pilot ≈ $105 (Flash)**, or ≈ $86 with GPT-5 mini **[changed: LOG §6]**; a second model doubles it.

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
| Sentiment valuation loading | 0 / half / full ("full" = the FIT market-level coefficient of Section 9; **[changed]**) | Phase 5 |

Plus two harness factors: ordering ∈ {setup-first, event-first} (**[changed]** added to the arm grid in Phase 4) and the calendar rendering (D6), so that the "time vs phase" claim is identified in the population actually run. Multi-asset provenance sensitivities (ρ_common, vol scale; item 29) run only in the 3-asset extension cell, not here. **[changed: REG-16]** The choice of the six parameters, the tiers, the roster and the inclusion of the stateful arms are made decidable: the pre-registered rule is "the six generator parameters with the largest standardised effect on the level-free observables-oracle regret and on band-MAS of the scripted policies (E7.8), ties broken toward the ones the reviews name" — if that list shares at least five parameters with the table above, the table is run and the sixth of the data-driven list is reported as Tier C; the stateful arms enter Tier B on the two highest-ranked parameters only if the variance pilot's ICC shows the stateful contrast is estimable at 5 seeds. REG-1's LLM magnitude test (≈ 60 runs) and REG-9's phase-restatement probe (≈ 90 runs) run in this phase.

### 13.2 Grid and cost (for approval)

**[changed: LOG §6, today's prices and measured prompt sizes; Claude 5 lines ×1.3 for the tokenizer, edit 27 Aug]** Tier A (minimum that answers the question): 13 generator settings (6 × 2 non-default + default) × 3 personas × 2 arms (static, memory) × 3 scenarios (flat, crash δ 0.70, bull-trap) × 5 seeds × 1 replicate = 1,170 runs (≈ 234,000 calls) per model. Gemini 2.5 Flash ≈ $210; GPT-5 mini ≈ $175.

Tier B (adds a frontier model on the six highest-impact settings): Tier A on Flash + GPT-5 mini (≈ $385), plus Claude Sonnet 5 on default + 6 settings × ISFJ/ENTJ × 2 arms × 2 scenarios × 5 seeds = 280 runs ≈ $390 (≈ $200 with cached system prompts). Total ≈ $775.

Tier C (adds the ordering/calendar factor and sustained-bull, and 3 replicates on the default setting): Tier B + ≈ 1,000 Flash runs ≈ $180 + 300 GPT-5 mini runs ≈ $45. Total ≈ $1,000. Batch pricing (−50 %) is available at all three providers only with a lock-step runner (a harness change to be costed in Phase 8 if the team wants it).

Stateful arms are not swept here (≈ 7× the cost per run); the context-length factor (E8.2) runs in the main grid on the default generator setting.

All runs at 10–15 concurrent requests, checkpointed, with provenance hashes; every cell's baselines rebuilt on its own path (Phase 7).

### 13.3 Pre-registered robustness criteria

A conclusion (e.g. "re-injection lowers ISFJ band-MAS"; "the swapped mandate moves the allocation to the injected content") is called robust if, across all generator levels, (i) the sign of the arm contrast is unchanged, (ii) the BH-corrected q stays below 0.05 in the crossed mixed model with the generator level as a fixed factor, and (iii) **[changed: LOG §7 — "within the CI of the default-level effect" is met trivially at 5 seeds]** the generator-level × arm interaction's 90 % CI lies inside ± a pre-registered equivalence margin equal to half the minimum effect of D12. Any conclusion that fails (i) at some level is reported as level-dependent with the level named. Interactions between generator level and arm are reported with CIs regardless. The decision rules that the second review cycle pre-registered for the content thesis (the swapped-mandate direction; "directive placebo effect below 30 % of the mandate effect") are evaluated at every generator level in the same table, so that the grid answers whether they hold for reasons of the environment or of the models.

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

The immediate deck-corrections note is produced in Phase 0 (0.2b) and the claims ledger absorbs it.

**Tests.** `test_claims_ledger_current`; `test_slides_built_from_generated` (no numeric literal in `build_slides.py` outside the data loaders).

**Compute / cost.** Slide regeneration only; no API cost.

**What could block it.** Nothing external.

---

## 15. Cross-phase summary: experiments, compute, cost and effort

**[changed: REV-8 adopted — an analyst-effort column is added. These numbers carry the label ESTIMATE: they are the third pass's judgement from the task counts (12 pre-registrations, the number of fits, code modules and reports per phase) and unit times of 0.5–1 day per pre-registration, 1–2 days per fitted module, 2 days per phase report; no source or experiment can supply them and they must not be quoted as evidence.]**

| Phase | Local compute (approx.) | API cost (today's prices) | Analyst effort (ESTIMATE, person-days) | Team decisions needed |
|---|---|---|---|---|
| 0 | 0.5 h | none | 4–6 | none |
| 1 | data download (hours, one-off) + 3 h | none | 8–12 | D1 (data substitutes), D13 (start-price mechanism, provisional B), D3 (if the decomposition is not identified) |
| 2 | 4 h | none | 8–12 | none, unless E2.4 ties (rule decides) |
| 3 | 1 h | none | 5–8 | none |
| 4 | 2 h | none | 10–14 | D4 (ranges), D5 (event formulation, if none meets the rule), D6 (calendar rendering), D14 (the control's purpose) |
| 5 | data retrieval (hours) + 3 h | none | 8–12 | D10 (before the phase), D15 (sentiment loading, after E5.5) |
| 6 | 5 h | ≈ $12 (L3 probe) | 8–12 | none |
| 16A go/no-go | 1 h | none | 1 | D17 (if the criterion fails) |
| 7 | 0.5 h | none | 5–7 | D7 (θ), D8 (one-shot call), D9 (bands) |
| 8 | 1 h | ≈ $105 (Flash) / ≈ $86 (GPT-5 mini) | 7–10 | D11 (salience), D12 (minimum effect) |
| 9 | orchestration; ≈ 9 h wall-clock per model per tier at 15 concurrent calls of ≈ 2 s | ≈ $210 / $775 / $1,000 by tier (Claude 5 lines ×1.3, [edit 27 Aug]) | 3–5 + run time | tier and roster (D2) |
| 10 | 1 h | none | 5–8 | none |
| **Total** | | **≈ $120 before Phase 9 + the tier** | **≈ 72–107 person-days serial; ≈ 60–65 working days on the critical path with the parallelism of Section 16** | |

**[changed: REV-9 adopted]** *Minimal path.* Phase 0 → E1.1 + E1.6 → E2.1 → E5.7 → E7.2 → Phase 10 closes the seven headline items (1–7 of `V2_WEAKNESSES.md`) and produces a defensible v2.0.1 in ≈ 15–20 person-days (ESTIMATE) with no API cost beyond Phase 0. It does **not** fit any parameter to data, so every LIT/DESIGN label stays and the paper's claims are limited to what the level-free audits show. Which programme runs first is D16; this plan does not recommend one because the choice depends on the team's deadline, which is not evidence available here.

Total API spend proposed before Phase 9: ≈ $120 (the first draft's $325 over-counted the L3 line; LOG §6), plus the Phase 9 tier. The main grid (execution-order step 3) is outside this plan's scope; its size is set by the Phase 8 power analysis. For orientation: none of the earlier planning or review documents fixes a model roster, seed count, replicate count or budget for the new grid (checked today across the cycle-1 audit, the consolidated report, the cycle-2 verification report, the position update, the novelty note, the execution order and the resubmission plan); the only prior cost figures are the cycle-1 audit's order-of-magnitude table (memoryless full grid of 1,620 runs ≈ $1.0–2.5k; full-transcript sub-grid $4–12k before caching), which this plan's per-run prices supersede. The earlier rounds did ask for open-weight models (Llama-3.3-70B, Qwen2.5-72B, Gemma-3-27B) as mechanistic anchors; the v2 harness supports them through OpenRouter or a vLLM endpoint, for which no key or endpoint is configured (D2).

---

## 16. Order, dependencies and gates

**[changed: REV-8 adopted; dependencies traced in LOG §7]**

```
Phase 0 (freeze, bugs, deck-corrections note)
   │
   ├──────────────► Phase 8 (harness fixes, statistics re-spec)  ── needs only the pilot logs; runs any time after 0
   │                     └── E8.5 variance pilot (API) after the v2.1 freeze of Phase 6 (execution-order rule)
   │
   ▼
E1.0 shared panel  ──┬──► Phase 1 (E1.1 start price ‖ E1.2–E1.6)
   (+ E3.1 GARCH     ├──► Phase 2 (E2.1 pure-FW check ‖ E2.2/E2.3 need E1.2 and E3.1)
    fits run here)   └──► Phase 3 (E3.2–E3.6; E3.2 needs E1.4's placement)
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
        Phase 4 (events, control,        Phase 5 (observables; needs D10;
          gains, calendar; own nulls)      needs Phase 1's level-free audit)
              │                               │
              └───────────────┬───────────────┘
                              ▼
                        Phase 6 (reference distributions, criteria, gates, L3)
                              ▼
                     ▶ 16A GO / NO-GO CHECKPOINT ◀
                              ▼
                        Phase 7 (θ, regret, bands, gate, baselines)
                              ▼
                        Phase 9 (LLM sensitivity grid)   ◄── Phase 8's power analysis
                              ▼
                        Phase 10 (ledger, deck, script)
```

Rules: Phases 1, 2, 3 run in parallel on the shared panel with the two stated cross-links (the per-stock GARCH fit E3.1 is run inside the data step because the SMM and the jump analysis need it; Phase 3 then confirms and documents it); Phases 4 and 5 run in parallel after 3; Phase 7's θ derivation needs Phase 5's fields and Phase 6's surrogate; Phase 8's code work is independent of 1–7 and its pilot waits for the Phase 6 freeze; every phase re-runs the checklist and audits on the frozen state it hands over (execution-order step-0 rule). Each phase ends with its report and stops. A phase is re-opened if a later phase's evidence contradicts its decision (e.g. Phase 5's field redesign changing the level-free inferability that Phase 1 stated); the re-opening is a logged decision.

v2.1 acceptance (the exit criterion of the whole plan): every item of `V2_WEAKNESSES.md` is closed as fixed, or documented as a labelled design choice with a sensitivity, or reported as a failure with its reason; the known-defect registry is empty; every number in every document is in the claims ledger; the checklist and audits are published at the pre-registered seed counts with intervals; the Phase 9 robustness table exists; the go/no-go criterion of 16A is met, or the team has taken D17.

### 16A. Go/no-go checkpoint after Phase 6 **[changed: REV-3 adopted; thresholds derived, not chosen]**

Written now, before Phase 1 starts; not moved afterwards. Computed on the Phase-6 frozen generator at the co-primary θ values, with ≥ 100 seeds per scenario and cluster-bootstrap 95 % intervals over paths; the policies are the mandate-conditional (true-V) oracle, the **level-free** observables oracle (current-day fields plus a 20-day history, trained on disjoint seeds, no level features), the best simple level-free rule from a pre-registered family (price vs SMA50 thresholds, RSI thresholds, analyst-vs-price thresholds, each with its scale fitted on the training seeds), and the trivial policies (always-hold at centre, constant band edges, random).

- **G1 (there is information to act on).** In every scenario, MCR(true-V oracle) < MCR(observables oracle) < MCR(best trivial policy), with non-overlapping 95 % intervals between adjacent pairs. *Derivation:* this is the ordering the L5 audit already presupposes; the interval rule is the plan's own reporting standard, not a chosen margin.
- **G2 (it is not solved by a two-line rule).** The best simple rule's MCR is above the observables oracle's, with non-overlapping intervals, in at least three of four scenarios. *Derivation:* item 1's finding is that a two-line rule reached oracle level in three of four scenarios; G2 is that finding's negation on the same scenario count.
- **G3 (judgement over time, not a one-shot call).** The median number of oracle target switches per run is ≥ 2 in the three event scenarios and the share of runs with ≥ 2 switches is ≥ 0.5. *Derivation:* item 48 and review C.15 define the one-shot call as "zero or one target change per run"; ≥ 2 is the smallest count that is not a one-shot call. Known today (LOG §2; 27-Aug re-run): the live engine gives medians 0 / 0–1 / 1 / 2 (flat / crash / bull trap / sustained bull) and event-scenario shares of 0.23–0.45, the 60-day engine 0.37–0.50, the 30-day engine 0.50–0.67 with coverage falling to 0.42 in flat — so G3 will fail unless D8 changes the horizon or the scoring. **[edit 27 Aug] G3 may not be met by choosing a persistence shorter than the fitted value: the persistence literature read in Phases 1–2 (Summers 1986, Poterba–Summers 1988, Balvers et al. 2000) points to half-lives of months to years, so a FIT persistence will give at most one decision per 200-day run, and a persistence shortened to pass G3 would be the tuning-to-pass the hard rules forbid. If G3 fails at the FIT persistence, the admissible responses under D17 are a longer horizon reported as a factor, per-window scoring, or restricting the paper's claim to a one-shot mandate-conflict benchmark — not a shorter half-life.**
- **G4 (the price-only reader is not the whole story).** The level-free observables oracle beats the level-free price-only oracle with non-overlapping intervals in every scenario, *and* the price-only surrogate's R²(x) lies at or below the Appendix B bound within its CI. *Derivation:* the first clause is the paper's "observables matter" claim stated as a test; the second is the leak test.

If any of G1–G4 fails, the plan stops after Phase 6 and the team takes D17: for G1/G2/G4 the options are Phase 5's field redesign or D3's environment choice; for G3 the options are D8's (a longer horizon with T reported as a factor, or per-window scoring; a shorter half-life is admissible only if it is itself inside the FIT interval — [edit 27 Aug]), each of which re-runs Phases 2 and 6 for the chosen option; if none is taken, the paper's claims are restricted to a one-shot mandate-conflict benchmark and say so. Results are reported under the pre-registered criterion in every case.

---

## 17. Decisions that only the team can make (asked now so that the phases do not stall)

- **D1.** Proceed on the free substitutes (yfinance survivor panel, EDGAR, SF Fed, Shiller, FRED) with the biases stated, or pause Phases 1–5 until CRSP/Compustat/OptionMetrics access exists.
- **D2.** The LLM roster and the budget tier for Phases 6, 8 and 9 (Gemini 2.5 Flash and GPT-5 mini as the workhorses; Claude Sonnet 5 as the frontier model — or Opus 5 at 2.5× the cost).
- **D3.** If the firm-level value/mispricing decomposition is not identified from the panel: choose between (a) the Vuolteenaho-implied larger σ_V (V not smooth; x harder to infer from price), (b) the v2 value with the "smooth fundamental" rationale withdrawn, or (c) two environments run as a factor. The report will show the audit and checklist consequences of each.
- **D4.** Where the index episode tables and the single-stock panel disagree on event ranges, which population the benchmark's crashes and bubbles represent.
- **D5.** If no event formulation meets the script-share/rejection rule.
- **D6.** Calendar rendering default: random calendar dates, no date, or "Day-N" kept as an arm (affects comparability with v1).
- **D7–D10.** θ (if a Phase-9 conclusion flips between θ_info and θ_cost, or θ_info is not reached), the one-shot-call issue (longer horizon, per-window scoring, or restricting the claim; a shorter half-life only inside the FIT interval), practitioner vs utility-consistent bands (REG-13), dividends paid vs field removed (D10 must be taken **before** Phase 5).
- **D11–D12.** Salience shares (common-start only, or dropped) and the minimum effect size for the main-grid power analysis (stated in the claim's own units; "conventional" is not a justification).
- **D13.** **[changed]** Start-price mechanism: randomise the level / normalise the price / both (REG-1). **[edit 27 Aug]** REG-1's discriminating LLM test runs in Phase 9, so Phases 1–6 must run under a provisional mechanism; the register names B (normalise the price) by exclusion, because it is the only option under which an LLM-side magnitude effect cannot exist. The generator-side audits are identical under A, B and C, so nothing in Phases 1–6 is re-run if the Phase-9 test later prefers A or C; only the rendering changes. The team is asked to approve the provisional B now rather than discover it later.
- **D14.** **[changed]** What the sustained-bull control is for, and hence which definition (REG-7).
- **D15.** **[changed]** Sentiment's valuation loading default, after REG-10b's audit.
- **D16.** **[changed]** Full programme vs the minimal path first (Section 15).
- **D17.** **[changed]** If the 16A criterion fails: which of the D8/D3/Phase-5 options to run.
- Where the plan review offered answers (D6 no date, D9 practitioner bands, D10 pay dividends, D11 common-start only, D12 0.33): recorded as one reviewer's opinion; not adopted here, because each is a preference and the register's experiments decide them.
- **Commit points.** Whether to tag "v2.0 frozen" after Phase 0 and to commit at each phase end.

---

## Appendix A. Power-analysis formulas used in the pre-registrations

- Share-type criterion (share ≥ p0 of paths): with a true share p1, one-sided α = 0.05, power 0.80: n = (z_{0.95}√(p0 q0) + z_{0.80}√(p1 q1))² / (p1 − p0)². For p0 = 0.80 and p1 = 0.75: n ≈ 420 paths; for p1 = 0.70: ≈ 110.
- Median/correlation criterion with an acceptance band of width w: the cross-seed sd s of the statistic is taken from a 50-seed pilot; n such that 1.96 · 1.25 · s/√n ≤ w/5 (the 1.25 = √(π/2) is the median's efficiency factor for near-normal statistics). **[changed]** The bootstrap is the default; this normal approximation is the exception.
- Generator-vs-real equivalence: **[changed: LOG §3]** stated as an equivalence test. With n_real ≈ 3,000 and n_gen ≥ 350 the two-sample KS test rejects equality at a true D = 0.10 with 97 % power (simulated), so non-rejection is not evidence of equivalence. The criterion is: the bootstrap 95 % upper limit of the KS distance < D0 = 0.10. Power for equivalence: with n_gen = 500 the KS distance's sampling sd is ≈ 0.02–0.03, so a true D ≤ 0.05 passes with ≈ 80 % power; a true D ≥ 0.10 fails.
- LLM arm contrasts (paired by seed and replicate): n_pairs = 2(z_{0.975} + z_{0.80})² σ_d² / Δ², with σ_d the sd of the paired difference from the variance pilot and Δ the pre-registered minimum effect (D12); the model-level version replaces n_pairs by the number of models and σ_d by the between-model sd of the per-model effect.
- Every pre-registration states which of these it used and the pilot variance it plugged in.

## Appendix B. The analytic level-free price-only bound for x

Under log P_t = log V_t + x_t with log V a random walk (variance σ_V² per day, drift μ) and x an AR(1) with coefficient ρ = 2^{−1/h} and innovation variance s_x²(1 − ρ²), the return r_t = μ + Δlog V_t + Δx_t is a stationary ARMA(1,1) process whose parameters are known functions of (σ_V, s_x, ρ). The steady-state Kalman filter for this state-space model gives the minimum-MSE estimate of x_t from the return history (and, without the level, nothing else), hence the maximal R²(x) any level-free reader of the price path can reach; its value is computed numerically for the adopted parameters and its sensitivity to (σ_V, s_x, h) tabulated. The surrogate's level-free R² must lie at or below this bound (within its CI); a surrogate above the bound indicates a leak through a non-price field or a level artefact. **[changed: computed, LOG §3; reproduced independently on 27 Aug to three decimals]** Results at h = 150 d: σ_V = 0.006, s_x = 0.13 → R² 0.14 averaged over a 200-day window from the stationary prior, 0.24 on day 200, **0.40 at steady state**; with s_x = 0.165 (the engine's stationary sd at sd_e 0.016; [resolved 29 Aug, Phase 0]: the reference row for Phase 1 is s_x ≈ 0.175 at the live sd_e 0.017, i.e. this row or slightly above, not the 0.13 row) 0.15 / 0.26 / 0.48; σ_V = 0.010 → 0.10 / 0.16 / 0.23; σ_V = 0.020 → 0.04 / 0.07 / 0.08. With the anchor (V_1 known) the bound is instead 1 − σ_V² t/s_x² ≈ 0.998 on day 1 and 0.57 on day 200 — which is what the published price-only R² of 0.79–0.90 reflected. **The first draft's sentence "under the v2 parameters the bound is high because V is smooth" is withdrawn**: the level-free bound is modest (0.40) and it matches reviewer C's level-free GBT (0.40); what was high was the anchored bound. A Vuolteenaho-type σ_V lowers it further (to ≈ 0.08 at 0.02/day), which is D3's consequence with numbers. Caveats: linear-Gaussian bound; calm windows only; a nonlinear filter on t/GARCH/jump innovations can exceed it slightly, so the surrogate is compared with the bound "within its CI plus the nonlinear allowance measured on a Gaussian control run".

## Appendix C. Numbers in the current documents that will be recomputed (for Phase 10's ledger)

Half-lives (60–120, 90, 120, 150, 187/188, 72, 14/26 d); the sustained-bull multiplier (0.25 vs 1.0); the jump rate (0.008 vs 0.010); the analyst sd (0.15 vs 0.35); the sensitivity pass/fail counts (five of six rows); "50 seeds" claims that are 20, 25, 150-of-400 or 12+10; the phase-from-calendar "100 % → 65 %" row; the "R² 0.90 → 0.83" row; the "±12 % off" L1 headline; the "within 0.02–0.08 of the oracle" L5 number (10 evaluation seeds); the pilot's "four scenarios"; every "plan anchor" attribution the fact-check flagged as approximate; **[changed]** the pilot half-life 187/188 d (→ 147 d at 200,000 steps), the stationary sd 0.128/0.13 (→ engine 0.165 / 0.175, raw-weight pilot 0.126 / 0.134; resolved in Phase 0), the analyst sd "0.35" (→ 0.33 on benchmark days / 0.335 analytic), the GPT-5 mini price, the L3 cost, the SABCEMM chartist share (0.23, not 0.17), the Barro–Ursúa citation, the FW PDF URL.
