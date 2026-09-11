# Phase 8 report — harness and statistics: the stateful arm made honest, context length a factor, the model re-specified, the grid sized (v2.1)

*Written as results land (execution prompt, "Documentation"); every number cites the file it comes from; the tables
marked `<!-- table:... -->` are generated from those files by `tools/phase8/e8_report_tables.py` and read back by
`tests/test_v2_1_phase_8.py::test_phase8_report_tables_match_files`. Sections follow the protocol's six headings.
A section still marked **pending** has no number in it yet, by design.*

**Status: COMPLETE — stopped for review (11 September 2026). Nothing is committed.**

---

## 0. Current state, and how to read this report

| item | status |
|---|---|
| Pre-registration | `PREREG_PHASE_8.md`, written before any correction was measured and before any paid call; `PREREG_PHASE_8_ADDENDUM.md` records every disconfirmation as it lands |
| Team decisions | **D12** = Δ 0.05 band-MAS, sized on σ_d's 90 % upper limit at seed-level pairing and the Bonferroni α within family (P8-1); **D alone** = achieved power reported, no stipulated Δ_D (P8-2); **D2** for Phase 8 = E8.5 on Flash + a GPT-5 mini transfer check + L3, ≈ $139 behind a cost gate (P8-3). **D11** is asked with E8.4's table (section 5) |
| E8.1 stateful corrections | **done** — behind `harness_version="v2_1"`, v2 the default (P8-4). On the pilot's logs the covariate was **37.3–40.5× too large** (section 3.1) |
| E8.1(e) placebo | **done** — the v2 placebo matches ISFJ only; the matched v2_1 placebo matches all three (P8-5) |
| E8.2 context length | **done** — {5, 20, 50, full} registered, the 50 level added, `full` measured as an ~80-turn window, every level priced (P8-7) |
| E8.3 statistics | **done** — the v2 model rejects a true null in 36–58 % once the arm effect varies by model; the crossed model and the two-way bootstrap hold size at 6 models, **not at 3**; BY across families is the decision rule on a multi-family grid; only the path-level sign-flip holds size as a temporal null (P8-9 – P8-11; section 3.4). The unregistered Gaussian-path sensitivity **done**: the verdicts do not move. **Addendum 17:** lbfgs stops at local optima in 15–20 % of E1's fits. With E8.5's measured components, E1-amended is not adopted by its rule, and at six models with a model × arm sd of 0.03 **neither E1 nor E2 holds size** at the sized seeds. The crossed model is descriptive, fitted at the better optimum (P8-17) |
| E8.4 salience | **not identified on any pilot design** (R² of start on persona 1.000); the registered condition was itself unsatisfiable (addendum 10); the known answer is recovered stably at common start with a no-persona reference and arbitrarily split under start-at-target; **D11 taken: a common-start slice with NONE** (P8-13, P8-14). The seed-cluster bootstrap **leaked** each seed's copies across cross-validation folds. This was found on the known answer and fixed. In the re-run every interval contains its point estimate: S_persona 0.979 [0.974, 0.984], S_directive's upper limit 9.4 × 10⁻⁵ (window 1). "The directive interval covers 0" fails by construction (addendum 18; P8-18) |
| E8.5 variance pilot | the first smoke **stopped by the registered gate** at ≈ $594 (Flash thinks 1,540 tokens per call); the team took thinking off (P8-8); the amended gate **passed** at $153.04; **both batches are complete** (720 runs, 0 non-ok; $144.66 of $151). **The power analysis's known-answer validation found the registered 90 % limit covering only 60–67 %**; the grid is sized on a closed-form limit that covers 0.915–0.945, with the registered limit beside (P8-15; addenda 13, 16). **Flash alone needs 19 seeds per cell. GPT-5 mini's σ_d is 2.21× Flash's, so the registered rule asks for 93** (P8-16), and the grid's affordability goes to the team. E1 as registered does not pair within persona × path; E1-amended, which does, was not adopted by its rule, so the crossed model is descriptive (P8-17) |
| L3 (Phase 6's probe) | **done** — all five models at chance and PASS, because every one answers by comparing price with the analyst estimate (93–99 % of answers); three run defects fixed before any answer was used (P8-12) |
| A latent runner defect | **found by the smoke and fixed** (P8-6, section 3.9) |
| The switches | golden record of the unmodified code; **0 differences** at every default (section 3.8) |
| Path hashes, freeze | **done** — 0 of 95 configurations changed; the freeze manifest unchanged, 30 files (section 3.11) |
| Whole test tree | **219 passed, 1 skipped, 4 xfailed, 0 failed**: Phase 7's 191 / 1 / 4 plus this phase's 28 tests; no older test changed (section 3.10) |
| Compute | the laptop (8 cores) for every offline number; the box and Kaggle not used (section 6) |

---

## 1. Literature review and the citation table

**No number from any source below enters a parameter file, a test tolerance or a decision rule in this phase.**
The statistical methods are validated by simulation on data with known answers (section 3.4), which is what the hard
rules require whether or not a source was read; the sources are named for what each method is, not for a value.

| source | what it is cited for | status | where it enters |
|---|---|---|---|
| Liu et al. (2024, TACL), "Lost in the middle" | position effects as a function of context length — the motivation for the context-length factor | **not re-read in this phase** | E8.2's factor exists as a factor; no level or threshold is taken from it |
| "When Attention Closes" (note cited in the DECISION_LOG, E5) | the forced-closure regime the rolling window mimics | **not re-read in this phase** | none |
| Barr, Levy, Scheepers & Tily (2013) | maximal random-effects structures (random slopes where the design has them) | **not re-read in this phase** | the *specification* of E1 includes model × arm; its size is measured by simulation, not assumed from the paper |
| Bates, Kliegl, Vasishth & Baayen (2015) | parsimonious mixed models (boundary estimates, over-parameterisation) | **not re-read in this phase** | E1's boundary shares are measured and reported |
| Cameron, Gelbach & Miller (2008) | cluster bootstrap with few clusters | **not re-read in this phase** | E2's size is measured at M ∈ {3, 6}; no cluster-count threshold is taken from it |
| Benjamini & Hochberg (1995) | the step-up FDR procedure | **not re-read in this phase** | implemented and its FDR simulated (section 3.4) |
| Benjamini & Yekutieli (2001) | FDR under arbitrary dependence (the Σ 1/i correction) | **not re-read in this phase** | implemented and simulated |
| Gelman & Hill (2007) | crossed random effects | **not re-read in this phase** | E1's formula; recovery measured by simulation |
| `langchain_openai` 1.6.0, `BaseChatOpenAI.validate_temperature` (source code) | gpt-5 models: any temperature other than 1 is removed silently | **read, correct** | E8.5's transfer runs at 1.0, logged so (addendum 6) |
| `langchain_google_genai` 4.3.5, the usage-metadata block (source code) | `output_tokens` = candidates + thoughts | **read, correct** | E8.5's cost gate prices output including thinking tokens |
| Provider price pages (plan 0.4, read 26–27 Aug 2026) | $ per M input / output tokens | **carried from the plan, not re-read** | prices only; every token count is measured here |

---

## 2. Pre-registration, verification of the inherited numbers, and corrections

The pre-registration was written before any correction was measured and before any paid call; what had been looked
at before it was written is listed at its head. Verified before use:

1. **The golden record predates every edit.** `tests/phase8_golden.json` was written from the unmodified modules
   (their LF sha256 is stored in it); a first capture showed the salience surrogate differing from itself at the
   last bit (the forest's two-thread float sums), so the capture runs under joblib's sequential backend and was
   rewritten before any edit — two consecutive checks, 0 differences.
2. **The path policy of the simulation is the observables oracle.** `L5_full_level_free`'s flat MCR at θ 0.05 is
   0.0770, the published figure (`e8_3/paths.json`).
3. **Tier C's correlation reproduces E7.8.** |r|(band-MAS, D at 0.05) = 0.069 with E7.8's own `_cell_frame`; the
   tool refuses to run otherwise (a first run with a different construction is disclosed, addendum 4).
4. **The parameter files are read back through their loud loaders** before any table under them.

**Corrections to inherited numbers, made here:**

- The execution prompt's "the nearest copy … is about **77 tokens** away": 77 is the mandate block's own size; the
  distance is **409 (chars/4) / 436 (o200k)** (section 3.1).
- Phase 7's placebo matching, "ratio 0.964 (words)": a pooled mean that hid a per-persona imperative mismatch in two
  of three personas (section 3.2).
- The plan's E8.5 price, "≈ $105 on Flash": measured in section 3.6.

### Amendments to the plan, recorded here rather than by editing it

The plan, `V2_1_ALTERNATIVES_REGISTER.md` and `docs/env_v2/v2_1/archive/` are untouched.

| plan text | amendment |
|---|---|
| Appendix A: n_pairs = 2(z₀.₉₇₅ + z₀.₈₀)² σ_d² / Δ² for arm contrasts "paired by seed and replicate" | The factor 2 belongs to a two-sample design; with σ_d the sd of the paired difference the paired n is half. **Used as written** (the conservative reading), the paired-correct n reported beside it everywhere (P8-1) |
| Appendix A: "paired by seed and replicate" | Replicates are exchangeable, so pairing replicate k of one arm with replicate k of the other adds noise; the pair is the **seed** with replicates averaged (P8-1) |
| 12.2 E8.1(e): "word count within 10 %, same number of imperative clauses" | Tested **per persona** with a registered clause annotation; the v2 placebo fails the imperative clause for ENTJ and INTJ, and the fix is a switch, not an edit (P8-5) |
| 12.2 E8.5 / 12.6: "≈ $105 (Flash)" or "≈ $86 (GPT-5 mini)"; 0.4: "≈ $0.18 per stateless Flash run" | **Measured $0.934 per Flash run and $0.307 per GPT-5 mini run** (n = 2 each): Flash thinks 1,540 tokens per call, billed as output; the plan assumed 120 output tokens per call. The registered E8.5 costs ≈ $594; the cost gate stopped it (addendum 8) |
| 13.2 Tier A: "Gemini 2.5 Flash ≈ $210" | ≈ $1,090 at the measured Flash price with default thinking |

---

## 3. Experiments and results

### 3.1 E8.1(a)–(d) — the stateful arm, before and after, on the pilot's own logs

<!-- table:e8_pilot_offsets -->
From the pilot's three `stateful_memory` logs (`results_v2_pilot/stateful/`, flat, seed 42, rolling 20). The format instructions after the injected block: 1,636 characters, 436 o200k tokens with the separator.

| persona | day | turns | v2 offset as logged (chars/4, system copy) | v2_1 system-copy offset (chars/4) | v2_1 nearest copy (chars/4 / o200k) | logged ÷ nearest | copies v2 → v2_1 | Context_Tokens logged (provider) | chars/4 of the same context | v2_1 context, est. |
|---|---|---|---|---|---|---|---|---|---|---|
| ENTJ | 1 | 0 | 637 | 637 | 409 / 436 | 1.6 | 2 → 2 | 1,929 | 2,082 | 1,929 |
| ENTJ | 20 | 19 | 14,567 | 13,090 | 409 / 436 | 35.6 | 21 → 2 | 19,561 | 16,012 | 17,756 |
| ENTJ | 21 | 20 | 15,300 | 13,745 | 409 / 436 | 37.4 | 22 → 2 | 20,484 | 16,745 | 18,582 |
| ENTJ | 200 | 20 | 15,261 | 13,706 | 409 / 436 | 37.3 | 22 → 2 | 20,454 | 16,706 | 18,550 |
| INTJ | 1 | 0 | 631 | 631 | 409 / 436 | 1.5 | 2 → 2 | 1,788 | 1,912 | 1,788 |
| INTJ | 20 | 19 | 14,738 | 13,360 | 409 / 436 | 36.0 | 21 → 2 | 19,228 | 16,019 | 17,575 |
| INTJ | 21 | 20 | 15,482 | 14,032 | 409 / 436 | 37.9 | 22 → 2 | 20,144 | 16,763 | 18,402 |
| INTJ | 200 | 20 | 15,909 | 14,459 | 409 / 436 | 38.9 | 22 → 2 | 20,512 | 17,190 | 18,782 |
| ISFJ | 1 | 0 | 644 | 644 | 409 / 436 | 1.6 | 2 → 2 | 2,016 | 2,211 | 2,016 |
| ISFJ | 20 | 19 | 14,882 | 13,272 | 409 / 436 | 36.4 | 21 → 2 | 19,632 | 16,449 | 17,710 |
| ISFJ | 21 | 20 | 15,627 | 13,932 | 409 / 436 | 38.2 | 22 → 2 | 20,563 | 17,194 | 18,536 |
| ISFJ | 200 | 20 | 16,546 | 14,851 | 409 / 436 | 40.5 | 22 → 2 | 21,332 | 18,113 | 19,336 |

Day 200, n = 3 runs: logged 15,261–16,546 against a nearest copy 409 (chars/4) / 436 (o200k) away — **37.3–40.5× too large**; the replayed blocks were **9.0%** of the context's characters.
<!-- /table:e8_pilot_offsets -->

**Reading.** The decay thesis's covariate was measuring the distance to a copy the model did not need. The memory
arm puts the mandate block into every turn, so the nearest copy sat 409 characters/4 from the generation point on
day 1 and on day 200 alike; the logged column counted from the system prompt's copy, through twenty replayed copies,
and grew to 15,261–16,546. Twenty-two copies were in the context at a full window. And the pilot's two context
columns were in two units: `Context_Tokens` the provider's count, `Mandate_Offset_Tokens` chars/4 — on ENTJ's day
200 the same context is 20,454 provider tokens and 16,706 chars/4.

**The corrections, each tested with both arms built in the test** (the pilot never ran `stateful_static`):

| defect | v2 (measured with a deterministic fake LLM) | v2_1 | test |
|---|---|---|---|
| (a) offset to the system copy only | the offset grows with every replayed copy | nearest copy logged as primary (436 o200k, constant), system copy beside, copy count logged: 2 in memory, 1 in static | `test_stateful_no_duplicate_mandate` |
| (b) the block replayed in history | memory − static context = one block per retained turn (rolling, summary), and in `full` the chars/4 budget drops *more* memory turns, so memory's context is ~749 characters *shorter* than static's — mismatched in both directions | histories byte-identical, contexts differ by exactly the 311-character block, every mode | `test_context_budget_parity` |
| (c) fallback stored as the model's turn | the fabricated `TargetAllocation` JSON ("Error after 3 attempts …") is the prior turn | `no valid answer` | `test_fallback_not_in_history` |
| (d) chars/4 throughout | the offset in chars/4 beside a provider context count | provider → o200k → labelled chars/4; offsets scaled into provider units; method and scale logged | `test_token_count_method_logged` |

### 3.2 E8.1(e) — the placebo, per persona, on the rendered texts

<!-- table:e8_placebo -->
| persona | placebo version | words real / placebo (rel. diff) | within 10 % | imperatives real / placebo | equal | both |
|---|---|---|---|---|---|---|
| ISFJ | v2 | 52 / 49 (0.058) | yes | 7 / 7 | yes | **PASS** |
| ISFJ | v2_1 | 52 / 49 (0.058) | yes | 7 / 7 | yes | **PASS** |
| INTJ | v2 | 49 / 49 (0.000) | yes | 6 / 7 | **no** | **FAIL** |
| INTJ | v2_1 | 49 / 46 (0.061) | yes | 6 / 6 | yes | **PASS** |
| ENTJ | v2 | 52 / 49 (0.058) | yes | 8 / 7 | **no** | **FAIL** |
| ENTJ | v2_1 | 52 / 52 (0.000) | yes | 8 / 8 | yes | **PASS** |

v2 placebo: **1 of 3** personas matched; matched v2_1 placebo: **3 of 3**.
<!-- /table:e8_placebo -->

**Reading.** The directive placebo was length-matched to every mandate (words within 6 %) but imperative-matched to
ISFJ's only: ENTJ's block carries eight imperatives, INTJ's six, the placebo seven. So in the pilot's `placebo_directive`
arm, a difference from `memory` for ENTJ or INTJ could partly be one imperative clause. The matched v2_1 placebo adds
or removes one whole record-keeping clause in a registered order and meets both criteria for all three. The
pre-registered expectation that INTJ's word count was at risk was wrong (49 = 49; addendum 1).

### 3.3 E8.2 — context length as a factor, and what its levels cost

<!-- table:e8_context_cost -->
Measured growth, n = 3 pilot stateful runs: day-1 context 1,911 provider tokens; 924.3 per retained turn (v2), 826.7 (v2_1). The 60,000-token budget holds 80 turns (v2) / 77 (v2_1). Output tokens per call: gemini-2.5-flash 106 (e8_5/smoke.json, billed usage, thinking off); gpt-5-mini 534 (e8_5/smoke.json, billed usage, provider-default thinking). Prices per M input/output: gemini-2.5-flash $0.30 / $2.50; gpt-5-mini $0.25 / $2.00 (plan 0.4; no caching).

| harness | level | calls / run | input tokens / run | turns at plateau | Flash $ / run | Flash $ / 90 runs | × stateless | GPT-5 mini $ / run | GPT-5 mini $ / 90 runs |
|---|---|---|---|---|---|---|---|---|---|
| v2 | stateless | 200 | 382,200 | 0 | 0.168 | 15.08 | 1.0 | 0.309 | 27.83 |
| v2 | rolling 5 | 200 | 1,292,636 | 5 | 0.441 | 39.66 | 2.6 | 0.537 | 48.32 |
| v2 | rolling 20 | 200 | 3,885,297 | 20 | 1.219 | 109.67 | 7.3 | 1.185 | 106.65 |
| v2 | rolling 50 | 200 | 8,446,718 | 50 | 2.587 | 232.82 | 15.4 | 2.325 | 209.29 |
| v2 | full (60k) | 200 | 12,176,268 | 80 | 3.706 | 333.52 | 22.1 | 3.258 | 293.20 |
| v2 | summary (5 raw) | 220 | 1,363,682 | 5 | 0.467 | 42.06 | 2.8 | 0.576 | 51.84 |
| v2_1 | stateless | 200 | 382,200 | 0 | 0.168 | 15.08 | 1.0 | 0.309 | 27.83 |
| v2_1 | rolling 5 | 200 | 1,196,489 | 5 | 0.412 | 37.07 | 2.5 | 0.513 | 46.16 |
| v2_1 | rolling 20 | 200 | 3,515,354 | 20 | 1.108 | 99.68 | 6.6 | 1.093 | 98.33 |
| v2_1 | rolling 50 | 200 | 7,595,067 | 50 | 2.331 | 209.83 | 13.9 | 2.112 | 190.12 |
| v2_1 | full (60k) | 200 | 10,630,671 | 77 | 3.242 | 291.79 | 19.3 | 2.871 | 258.42 |
| v2_1 | summary (5 raw) | 220 | 1,267,536 | 5 | 0.438 | 39.46 | 2.6 | 0.552 | 49.68 |
<!-- /table:e8_context_cost -->

**Reading.** `full` is not a full transcript: at the 60,000-token budget it retains ~80 turns, so the factor's top
two levels are a 50-turn and an ~80-turn window. The pre-registered "≈ 65 turns" was wrong (addendum 2). The cost
column is at the plan's 120 output tokens per call until the smoke's measured output replaces it; section 3.6.

### 3.4 E8.3 — the statistics, validated on simulated data before any real contrast

#### (a) The mixed model and the intervals — size and power

**Reading.** The v2 statistics would have produced false findings as a matter of routine. Once the arm effect varies by
model — a model × arm sd of 0.03, which is what "random slopes for arm by model" were pre-registered to absorb — the v2
nested, intercept-only model rejects a true null in **36–58 %** of datasets, at every design size simulated. The crossed
model (E1) and the two-way cluster bootstrap (E2) hold size at six models and **not at three** (E1 0.077–0.100; E2 up to
0.123 with ten paths); the v2 run-level bootstrap gets *worse* as paths are added (0.133–0.207), because more paths make
its too-narrow interval narrower. Without model × arm variance all three new estimators are conservative. **For the
main grid this is a statement about its roster before it is one about its seeds:** at two or three models no interval
estimator in this set holds size, and every interval must carry the simulated size of the one used (P8-9; addendum 11).
The recovery table shows that E1 finds each planted component inside its own 5th–95th percentile band on a large
design; the unregistered Gaussian-path sensitivity (addendum 3) tests the path dimension the registered path effect
could not.

<!-- table:e8_mixed -->
Rejection rate of β = 0 at α = 0.05 with its Wilson 95 % interval: **size** in the β = 0 rows (bold = the interval lies above 0.05, size does not hold), **power** in the β = 0.05 rows. The tested cell is ENTJ × bull_trap (E1, E2, E3) and ENTJ pooled over scenarios (E0, as implemented). Path effect: the real band-MAS of the observables oracle (sd 0.0003–0.0005; addendum 3).

| M | S | R | σ model×arm | ρ | β | n | E0 v2 nested | E1 crossed | E2 two-way bootstrap | E3 run bootstrap | E2 coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 5 | 1 | 0.00 | 0.0 | 0.00 | 300 | **0.077 [0.052, 0.112]** | 0.023 [0.011, 0.047] | 0.017 [0.007, 0.038] | 0.013 [0.005, 0.034] | 0.983 |
| 3 | 5 | 1 | 0.03 | 0.0 | 0.00 | 300 | **0.360 [0.308, 0.416]** | **0.077 [0.052, 0.112]** | 0.063 [0.041, 0.097] | **0.077 [0.052, 0.112]** | 0.937 |
| 3 | 5 | 1 | 0.03 | 0.5 | 0.00 | 300 | **0.383 [0.330, 0.439]** | **0.100 [0.071, 0.139]** | **0.087 [0.060, 0.124]** | 0.073 [0.049, 0.109] | 0.913 |
| 3 | 10 | 1 | 0.00 | 0.0 | 0.00 | 300 | 0.047 [0.028, 0.077] | 0.017 [0.007, 0.038] | 0.000 [0.000, 0.013] | 0.007 [0.002, 0.024] | 1.000 |
| 3 | 10 | 1 | 0.03 | 0.0 | 0.00 | 300 | **0.523 [0.467, 0.579]** | **0.093 [0.065, 0.132]** | **0.107 [0.077, 0.147]** | **0.177 [0.138, 0.224]** | 0.893 |
| 3 | 10 | 1 | 0.03 | 0.5 | 0.00 | 300 | **0.520 [0.464, 0.576]** | **0.090 [0.063, 0.128]** | **0.123 [0.091, 0.165]** | **0.187 [0.147, 0.235]** | 0.877 |
| 6 | 5 | 1 | 0.00 | 0.0 | 0.00 | 300 | 0.040 [0.023, 0.069] | 0.027 [0.014, 0.052] | 0.003 [0.001, 0.019] | 0.003 [0.001, 0.019] | 0.997 |
| 6 | 5 | 1 | 0.03 | 0.0 | 0.00 | 300 | **0.373 [0.321, 0.429]** | 0.053 [0.033, 0.085] | 0.023 [0.011, 0.047] | 0.040 [0.023, 0.069] | 0.977 |
| 6 | 5 | 1 | 0.03 | 0.5 | 0.00 | 300 | **0.410 [0.356, 0.466]** | 0.073 [0.049, 0.109] | 0.057 [0.036, 0.089] | 0.053 [0.033, 0.085] | 0.943 |
| 6 | 5 | 3 | 0.03 | 0.0 | 0.00 | 300 | **0.580 [0.523, 0.634]** | 0.027 [0.014, 0.052] | **0.077 [0.052, 0.112]** | **0.207 [0.165, 0.256]** | 0.923 |
| 6 | 10 | 1 | 0.00 | 0.0 | 0.00 | 300 | 0.043 [0.025, 0.073] | 0.013 [0.005, 0.034] | 0.003 [0.001, 0.019] | 0.003 [0.001, 0.019] | 0.997 |
| 6 | 10 | 1 | 0.03 | 0.0 | 0.00 | 300 | **0.517 [0.460, 0.573]** | 0.057 [0.036, 0.089] | 0.053 [0.033, 0.085] | **0.140 [0.105, 0.184]** | 0.947 |
| 6 | 10 | 1 | 0.03 | 0.5 | 0.00 | 300 | **0.513 [0.457, 0.569]** | 0.070 [0.046, 0.105] | 0.073 [0.049, 0.109] | **0.133 [0.099, 0.176]** | 0.927 |
| 3 | 5 | 1 | 0.00 | 0.0 | 0.05 | 300 | 1.000 [0.987, 1.000] | 0.920 [0.884, 0.946] | 0.950 [0.919, 0.969] | 0.820 [0.773, 0.859] | 0.980 |
| 3 | 5 | 1 | 0.03 | 0.0 | 0.05 | 300 | 0.960 [0.931, 0.977] | 0.627 [0.571, 0.679] | 0.690 [0.636, 0.740] | 0.653 [0.598, 0.705] | 0.910 |
| 3 | 5 | 1 | 0.03 | 0.5 | 0.05 | 300 | 0.977 [0.953, 0.989] | 0.623 [0.567, 0.676] | 0.683 [0.629, 0.733] | 0.620 [0.564, 0.673] | 0.877 |
| 3 | 10 | 1 | 0.00 | 0.0 | 0.05 | 300 | 1.000 [0.987, 1.000] | 0.970 [0.944, 0.984] | 1.000 [0.987, 1.000] | 0.993 [0.976, 0.998] | 0.993 |
| 3 | 10 | 1 | 0.03 | 0.0 | 0.05 | 300 | 0.987 [0.966, 0.995] | 0.733 [0.681, 0.780] | 0.797 [0.748, 0.838] | 0.867 [0.824, 0.901] | 0.873 |
| 3 | 10 | 1 | 0.03 | 0.5 | 0.05 | 300 | 0.980 [0.957, 0.991] | 0.693 [0.639, 0.743] | 0.787 [0.737, 0.829] | 0.817 [0.769, 0.856] | 0.897 |
| 6 | 5 | 1 | 0.00 | 0.0 | 0.05 | 300 | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 0.983 [0.962, 0.993] | 0.990 |
| 6 | 5 | 1 | 0.03 | 0.0 | 0.05 | 300 | 0.997 [0.981, 0.999] | 0.880 [0.838, 0.912] | 0.863 [0.820, 0.898] | 0.897 [0.857, 0.926] | 0.950 |
| 6 | 5 | 1 | 0.03 | 0.5 | 0.05 | 300 | 1.000 [0.987, 1.000] | 0.860 [0.816, 0.895] | 0.907 [0.868, 0.935] | 0.817 [0.769, 0.856] | 0.943 |
| 6 | 5 | 3 | 0.03 | 0.0 | 0.05 | 300 | 1.000 [0.987, 1.000] | 0.857 [0.812, 0.892] | 0.970 [0.944, 0.984] | 0.990 [0.971, 0.997] | 0.940 |
| 6 | 10 | 1 | 0.00 | 0.0 | 0.05 | 300 | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 0.997 |
| 6 | 10 | 1 | 0.03 | 0.0 | 0.05 | 300 | 1.000 [0.987, 1.000] | 0.937 [0.903, 0.959] | 0.957 [0.927, 0.975] | 0.987 [0.966, 0.995] | 0.937 |
| 6 | 10 | 1 | 0.03 | 0.5 | 0.05 | 300 | 0.997 [0.981, 0.999] | 0.887 [0.846, 0.918] | 0.947 [0.915, 0.967] | 0.957 [0.927, 0.975] | 0.933 |

E1's variance components (median over datasets) and the share of fits with the model × arm component at the zero boundary:

| M | S | R | σ model×arm planted | β | model (planted 0.0025) | model×arm | path | model×arm at boundary | fit failures |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 5 | 1 | 0.00 (ρ 0.0) | 0.00 | 0.00140 | 0.00002 | 0.000025 | 0.02 | 0 |
| 3 | 5 | 1 | 0.03 (ρ 0.0) | 0.00 | 0.00138 | 0.00041 | 0.000009 | 0.00 | 0 |
| 3 | 5 | 1 | 0.03 (ρ 0.5) | 0.00 | 0.00166 | 0.00037 | 0.000010 | 0.01 | 0 |
| 3 | 10 | 1 | 0.00 (ρ 0.0) | 0.00 | 0.00119 | 0.00002 | 0.000012 | 0.03 | 0 |
| 3 | 10 | 1 | 0.03 (ρ 0.0) | 0.00 | 0.00132 | 0.00045 | 0.000006 | 0.00 | 0 |
| 3 | 10 | 1 | 0.03 (ρ 0.5) | 0.00 | 0.00152 | 0.00050 | 0.000006 | 0.00 | 0 |
| 6 | 5 | 1 | 0.00 (ρ 0.0) | 0.00 | 0.00171 | 0.00005 | 0.000021 | 0.03 | 0 |
| 6 | 5 | 1 | 0.03 (ρ 0.0) | 0.00 | 0.00179 | 0.00047 | 0.000005 | 0.00 | 0 |
| 6 | 5 | 1 | 0.03 (ρ 0.5) | 0.00 | 0.00245 | 0.00053 | 0.000006 | 0.00 | 0 |
| 6 | 5 | 3 | 0.03 (ρ 0.0) | 0.00 | 0.00140 | 0.00060 | 0.000067 | 0.00 | 0 |
| 6 | 10 | 1 | 0.00 (ρ 0.0) | 0.00 | 0.00160 | 0.00001 | 0.000014 | 0.02 | 0 |
| 6 | 10 | 1 | 0.03 (ρ 0.0) | 0.00 | 0.00169 | 0.00045 | 0.000004 | 0.00 | 0 |
| 6 | 10 | 1 | 0.03 (ρ 0.5) | 0.00 | 0.00194 | 0.00051 | 0.000004 | 0.00 | 0 |
| 3 | 5 | 1 | 0.00 (ρ 0.0) | 0.05 | 0.00127 | 0.00003 | 0.000023 | 0.02 | 0 |
| 3 | 5 | 1 | 0.03 (ρ 0.0) | 0.05 | 0.00137 | 0.00042 | 0.000011 | 0.01 | 0 |
| 3 | 5 | 1 | 0.03 (ρ 0.5) | 0.05 | 0.00186 | 0.00035 | 0.000007 | 0.01 | 0 |
| 3 | 10 | 1 | 0.00 (ρ 0.0) | 0.05 | 0.00127 | 0.00002 | 0.000013 | 0.03 | 0 |
| 3 | 10 | 1 | 0.03 (ρ 0.0) | 0.05 | 0.00146 | 0.00045 | 0.000006 | 0.00 | 0 |
| 3 | 10 | 1 | 0.03 (ρ 0.5) | 0.05 | 0.00163 | 0.00050 | 0.000006 | 0.00 | 0 |
| 6 | 5 | 1 | 0.00 (ρ 0.0) | 0.05 | 0.00185 | 0.00006 | 0.000019 | 0.02 | 0 |
| 6 | 5 | 1 | 0.03 (ρ 0.0) | 0.05 | 0.00178 | 0.00046 | 0.000005 | 0.00 | 0 |
| 6 | 5 | 1 | 0.03 (ρ 0.5) | 0.05 | 0.00246 | 0.00053 | 0.000005 | 0.00 | 0 |
| 6 | 5 | 3 | 0.03 (ρ 0.0) | 0.05 | 0.00148 | 0.00065 | 0.000075 | 0.00 | 0 |
| 6 | 10 | 1 | 0.00 (ρ 0.0) | 0.05 | 0.00158 | 0.00001 | 0.000014 | 0.03 | 0 |
| 6 | 10 | 1 | 0.03 (ρ 0.0) | 0.05 | 0.00161 | 0.00045 | 0.000003 | 0.00 | 0 |
| 6 | 10 | 1 | 0.03 (ρ 0.5) | 0.05 | 0.00189 | 0.00048 | 0.000003 | 0.00 | 0 |
<!-- /table:e8_mixed -->

<!-- table:e8_recovery -->
Design: M = 12, S = 20, all-Gaussian in E1's own parameterisation; 100 datasets. Power at β = 0.05: 0.970 [0.915, 0.990].

| component | planted variance | p05 | median | p95 | planted inside [p05, p95] |
|---|---|---|---|---|---|
| model | 0.00250 | 0.00073 | 0.00224 | 0.00530 | yes |
| model_arm | 0.00090 | 0.00039 | 0.00085 | 0.00161 | yes |
| path | 0.00160 | 0.00103 | 0.00153 | 0.00225 | yes |
| residual | 0.00090 | 0.00087 | 0.00090 | 0.00094 | yes |
<!-- /table:e8_recovery -->

<!-- table:e8_mixed_gpath -->
**Unregistered sensitivity** (addendum 3): a Gaussian path intercept, sd 0.04, S = 10.

| M | S | R | σ model×arm | ρ | β | n | E0 v2 nested | E1 crossed | E2 two-way bootstrap | E3 run bootstrap | E2 coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 10 | 1 | 0.00 | 0.0 | 0.00 | 300 | 0.003 [0.001, 0.019] | 0.043 [0.025, 0.073] | 0.017 [0.007, 0.038] | 0.000 [0.000, 0.013] | 0.983 |
| 3 | 10 | 1 | 0.03 | 0.0 | 0.00 | 300 | **0.373 [0.321, 0.429]** | **0.087 [0.060, 0.124]** | **0.087 [0.060, 0.124]** | **0.077 [0.052, 0.112]** | 0.913 |
| 6 | 10 | 1 | 0.00 | 0.0 | 0.00 | 300 | 0.010 [0.003, 0.029] | 0.020 [0.009, 0.043] | 0.000 [0.000, 0.013] | 0.000 [0.000, 0.013] | 1.000 |
| 6 | 10 | 1 | 0.03 | 0.0 | 0.00 | 300 | **0.363 [0.311, 0.419]** | 0.067 [0.044, 0.101] | 0.060 [0.038, 0.093] | **0.080 [0.054, 0.116]** | 0.940 |
| 3 | 10 | 1 | 0.00 | 0.0 | 0.05 | 300 | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 0.933 [0.899, 0.956] | 0.987 |
| 3 | 10 | 1 | 0.03 | 0.0 | 0.05 | 300 | 0.977 [0.953, 0.989] | 0.763 [0.712, 0.808] | 0.800 [0.751, 0.841] | 0.777 [0.726, 0.820] | 0.877 |
| 6 | 10 | 1 | 0.00 | 0.0 | 0.05 | 300 | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 1.000 [0.987, 1.000] | 1.000 |
| 6 | 10 | 1 | 0.03 | 0.0 | 0.05 | 300 | 0.997 [0.981, 0.999] | 0.953 [0.923, 0.972] | 0.943 [0.911, 0.964] | 0.967 [0.940, 0.982] | 0.950 |
<!-- /table:e8_mixed_gpath -->

**Reading of the unregistered sensitivity.** With a path effect that matters (sd 0.04), the verdicts do not move:
E1 and E2 hold size at six models (0.067, 0.060) and fail at three (0.087 each); E0 still rejects a true null in 36–37 %;
the run bootstrap fails at both (0.077, 0.080); E1 recovers the planted path component. Power at β = 0.05 and six models
is 0.95 (E1) and 0.94 (E2). The registered conditions' conclusion was not an artefact of their near-empty path effect.

**Two findings from after E8.5 qualify (a)** (addendum 17).

1. **lbfgs, the optimizer E1 uses, stops at a local optimum in 15–20 % of fits on these conditions.** At the better
   optimum:
   - at three models, E1 rejects a true null in **14 %** of datasets, not 9 %;
   - at six models, its power is 0.99, not 0.94.

   The verdict at three models is therefore stronger than the table shows, and the verdict at six is unchanged
   (`e8_3/mixed_optimizer.json`, 100 datasets per condition).
2. **No condition here planted a persona-specific path effect, and E8.5 found one** carrying 82 % of Flash's band-MAS
   variance. E1 as specified does not pair within persona × path. A simulation with E8.5's measured components
   compares E1 as registered with E1 fitted on seed-level differences (`e8_3/mixed_pp.json`).

<!-- table:e8_mixed_optimizer -->
Unregistered (addendum 17): E1 fitted by lbfgs and powell, the higher REML likelihood kept (E1-best); a local optimum is llf(powell) - llf(lbfgs) > 1. Fresh datasets from E8.3's process; model × arm sd 0.03.

| models | seeds | β | datasets | lbfgs stops short | largest gap | decisions that change | E1 as registered (lbfgs) [Wilson 95 %] | E1-best |
|---|---|---|---|---|---|---|---|---|
| 3 | 10 | 0.0 | 100 | 18 % | 3.9 | 5 | 0.090 [0.048, 0.162] | 0.140 [0.085, 0.221] |
| 3 | 10 | 0.05 | 100 | 20 % | 3.7 | 11 | 0.680 [0.583, 0.763] | 0.790 [0.700, 0.858] |
| 6 | 10 | 0.0 | 100 | 15 % | 18.4 | 0 | 0.070 [0.034, 0.137] | 0.070 [0.034, 0.137] |
| 6 | 10 | 0.05 | 100 | 19 % | 6.8 | 5 | 0.940 [0.875, 0.972] | 0.990 [0.946, 0.998] |
<!-- /table:e8_mixed_optimizer -->

<!-- table:e8_mixed_pp -->
Unregistered (addendum 17). Planted: E8.5's band-MAS components (path 9.3e-05, path_arm 2.1e-05, persona_path 0.0031, persona_path_arm 0.00041, replicate 0.00017); 19 seeds per scenario, R = 1, 2 scenarios, 3 personas, model intercept sd 0.05. Reject rates [Wilson 95 %] at α = 0.05; at α′ = 0.00139 beside. E1: as registered (lbfgs). E1-best: E1 at the better of lbfgs and Powell. E1-amended: E1 on seed-level differences. SE ÷ sd: the median model SE over the sd of the estimates (1 = calibrated).

| persona × path | models | model × arm sd | β | datasets | E1 | E1-best | E1-amended | E1 at α′ | E1-amended at α′ | E2 | SE ÷ sd: E1 / E1-best / E1-amended |
|---|---|---|---|---|---|---|---|---|---|---|---|
| shared | 3 | 0.0 | 0.0 | 200 | 0.005 [0.001, 0.028] | 0.005 [0.001, 0.028] | 0.055 [0.031, 0.096] | 0.000 | 0.000 | 0.025 [0.011, 0.057] | 1.48 / 1.41 / 1.06 |
| shared | 3 | 0.0 | 0.05 | 200 | 0.975 [0.943, 0.989] | 1.000 [0.981, 1.000] | 1.000 [0.981, 1.000] | 0.925 | 1.000 | 1.000 [0.981, 1.000] | 1.44 / 1.37 / 1.02 |
| shared | 3 | 0.03 | 0.0 | 200 | 0.110 [0.074, 0.161] | 0.115 [0.078, 0.167] | 0.140 [0.099, 0.195] | 0.035 | 0.040 | 0.200 [0.150, 0.261] | 0.92 / 0.91 / 0.90 |
| shared | 3 | 0.03 | 0.05 | 200 | 0.655 [0.587, 0.717] | 0.655 [0.587, 0.717] | 0.655 [0.587, 0.717] | 0.370 | 0.390 | 0.735 [0.670, 0.791] | 0.83 / 0.82 / 0.80 |
| shared | 6 | 0.0 | 0.0 | 200 | 0.065 [0.038, 0.108] | 0.085 [0.054, 0.132] | 0.065 [0.038, 0.108] | 0.000 | 0.000 | 0.080 [0.050, 0.126] | 0.94 / 0.91 / 0.94 |
| shared | 6 | 0.0 | 0.05 | 200 | 0.980 [0.950, 0.992] | 1.000 [0.981, 1.000] | 1.000 [0.981, 1.000] | 0.955 | 1.000 | 1.000 [0.981, 1.000] | 0.99 / 0.95 / 0.99 |
| shared | 6 | 0.03 | 0.0 | 200 | 0.085 [0.054, 0.132] | 0.085 [0.054, 0.132] | 0.080 [0.050, 0.126] | 0.015 | 0.010 | 0.090 [0.058, 0.138] | 0.97 / 0.96 / 0.98 |
| shared | 6 | 0.03 | 0.05 | 200 | 0.770 [0.707, 0.823] | 0.780 [0.718, 0.832] | 0.775 [0.712, 0.827] | 0.450 | 0.430 | 0.780 [0.718, 0.832] | 0.91 / 0.91 / 0.92 |
| model-specific | 3 | 0.0 | 0.0 | 200 | 0.000 [0.000, 0.019] | 0.000 [0.000, 0.019] | 0.060 [0.035, 0.102] | 0.000 | 0.000 | 0.000 [0.000, 0.019] | 2.40 / 2.28 / 1.01 |
| model-specific | 3 | 0.0 | 0.05 | 200 | 0.920 [0.874, 0.950] | 1.000 [0.981, 1.000] | 1.000 [0.981, 1.000] | 0.815 | 1.000 | 1.000 [0.981, 1.000] | 2.59 / 2.49 / 1.10 |
| model-specific | 3 | 0.03 | 0.0 | 200 | 0.100 [0.066, 0.149] | 0.100 [0.066, 0.149] | 0.145 [0.103, 0.200] | 0.035 | 0.065 | 0.200 [0.150, 0.261] | 1.00 / 0.97 / 0.91 |
| model-specific | 3 | 0.03 | 0.05 | 200 | 0.540 [0.471, 0.608] | 0.570 [0.501, 0.637] | 0.615 [0.546, 0.680] | 0.230 | 0.320 | 0.705 [0.638, 0.764] | 0.97 / 0.93 / 0.87 |
| model-specific | 6 | 0.0 | 0.0 | 200 | 0.000 [0.000, 0.019] | 0.000 [0.000, 0.019] | 0.055 [0.031, 0.096] | 0.000 | 0.005 | 0.005 [0.001, 0.028] | 2.22 / 2.09 / 0.95 |
| model-specific | 6 | 0.0 | 0.05 | 200 | 0.980 [0.950, 0.992] | 1.000 [0.981, 1.000] | 1.000 [0.981, 1.000] | 0.770 | 1.000 | 1.000 [0.981, 1.000] | 2.53 / 2.40 / 1.09 |
| model-specific | 6 | 0.03 | 0.0 | 200 | 0.095 [0.062, 0.144] | 0.095 [0.062, 0.144] | 0.135 [0.094, 0.189] | 0.005 | 0.010 | 0.135 [0.094, 0.189] | 1.06 / 1.01 / 0.94 |
| model-specific | 6 | 0.03 | 0.05 | 200 | 0.760 [0.696, 0.814] | 0.775 [0.712, 0.827] | 0.815 [0.755, 0.863] | 0.405 | 0.530 | 0.820 [0.761, 0.867] | 0.96 / 0.91 / 0.83 |

Adoption rule at six models (addendum 17): E1-amended's size holds in 3 of 4 settings; its power at α′ is not below E1's in 3 of 4. **E1-amended adopted: no.**
<!-- /table:e8_mixed_pp -->

**Reading.**

- **By its pre-registered rule, E1-amended is not adopted** (P8-17).
  - Its size fails in one of the four settings at six models: the model-specific reading with model × arm sd 0.03,
    0.135 [0.094, 0.189].
  - Its power at α′ falls below E1's in one: the shared reading with sd 0.03, 0.430 against 0.450, four datasets
    in 200.

  The rule's fallback applies: the crossed model is reported descriptively, and E2's intervals decide.
- **The seed count assumed pairing, and E1 does not pair.** Without model × arm variance, E1's SEs are 2.2–2.6× the
  spread of its estimates in the model-specific reading; E1-amended's are 0.94–1.10. E1-best also reaches power 1.00
  at α′ there, so E1's shortfall (0.77–0.96) is lbfgs stopping short, in 34–61 % of those fits.
- **When the arm effect varies by model, six models do not hold size at nineteen seeds.**
  - With a model × arm sd of 0.03, E1 rejects a true null in 8.5–9.5 % and E2 in 9–13.5 %.
  - E1-amended holds only in the shared reading, at the boundary: 0.080 [0.050, 0.126].
  - At ten seeds (P8-9) E1 and E2 held at six models. More seeds shrink the within-model noise and leave six
    model-level draws governing the contrast.
- **Post hoc, adopting nothing:** a t reference with M − 1 df on the same estimates restores size — E1 0.030–0.045,
  E1-amended 0.035–0.060 at six models with sd 0.03 — while power at α′ falls to 0.025–0.075
  (`e8_3/mixed_tref_posthoc.json`). **When the arm effect varies by model, the model count, not the seed count, bounds
  a confirmatory contrast.** Section 5.5's model-level DESIGN table says the same. The reference distribution is
  carried to Phase 9 (section 7).

#### (b) Multiplicity — the family, its size, and the procedure

<!-- table:e8_multiplicity -->
Tier C's correlation on 600 cells (E7.8 _cell_frame (means over seeds); |r|(band-MAS, D at 0.05) = 0.069, reproducing `e7_8/matrix.json`): |r|(band-MAS, D at 0.0020) = 0.066, **|r|(D at 0.05, D at 0.0020) = 0.992**. 5,000 replications, non-null shift 3.

| grid | tests | π₁ | procedure | FDR (MC half-width) | FWER | power | FDR ≤ 0.05 + MC |
|---|---|---|---|---|---|---|---|
| e8_5 {"Q1": 12} | 36 | 0.0 | v2 | 0.4308 (0.0137) | 0.431 | — | **no** |
| e8_5 {"Q1": 12} | 36 | 0.0 | bh_within | 0.0418 (0.0055) | 0.042 | — | yes |
| e8_5 {"Q1": 12} | 36 | 0.0 | by_across | 0.0118 (0.0030) | 0.012 | — | yes |
| e8_5 {"Q1": 12} | 36 | 0.1 | v2 | 0.2039 (0.0074) | 0.444 | 0.744 | **no** |
| e8_5 {"Q1": 12} | 36 | 0.1 | bh_within | 0.0412 (0.0039) | 0.098 | 0.524 | yes |
| e8_5 {"Q1": 12} | 36 | 0.1 | by_across | 0.0110 (0.0023) | 0.021 | 0.338 | yes |
| e8_5 {"Q1": 12} | 36 | 0.3 | v2 | 0.0820 (0.0031) | 0.438 | 0.764 | **no** |
| e8_5 {"Q1": 12} | 36 | 0.3 | bh_within | 0.0352 (0.0022) | 0.210 | 0.666 | yes |
| e8_5 {"Q1": 12} | 36 | 0.3 | by_across | 0.0084 (0.0012) | 0.044 | 0.448 | yes |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.0 | v2 | 0.9964 (0.0017) | 0.996 | — | **no** |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.0 | bh_within | 0.1578 (0.0101) | 0.158 | — | **no** |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.0 | by_across | 0.0066 (0.0022) | 0.007 | — | yes |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.1 | v2 | 0.2455 (0.0025) | 0.997 | 0.743 | **no** |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.1 | bh_within | 0.0564 (0.0018) | 0.552 | 0.512 | **no** |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.1 | by_across | 0.0070 (0.0009) | 0.054 | 0.232 | yes |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.3 | v2 | 0.0834 (0.0010) | 0.997 | 0.767 | **no** |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.3 | bh_within | 0.0365 (0.0007) | 0.884 | 0.671 | yes |
| reviewer {"Q1": 30, "Q2": 30, "Q3": 45, "Q4": 15} | 360 | 0.3 | by_across | 0.0053 (0.0004) | 0.164 | 0.371 | yes |
<!-- /table:e8_multiplicity -->

**Reading.** The v2 procedure — BH across seven metrics within each contrast — does not control anything a reader
would call a false-discovery rate: under the global null it produces at least one false claim in 43 % of E8.5-sized
grids and in essentially every reviewer-sized one. BH within each question family holds on a single-family grid and
**fails the registered adoption rule on a grid of four families** (FDR 0.158 at π₁ = 0), because it controls the rate
family by family, not over what the paper reports. BY across all confirmatory families holds in every row, at a power
cost (0.23–0.45 against 0.51–0.67). So, as the registered rule requires: **BY across families is the decision rule on
any grid with more than one confirmatory family**, BH within family is reported beside as the per-question view
(addendum 5). And the correlation matrix says something the family's count does not: the co-primary θ puts **two
copies of D** in tier C (|r| = 0.992).

#### (c) The temporal null

**Reading.** The circular shift was not the only problem with the v2 trend test, and replacing it with a block
permutation does not fix it. At the persistence the pilot's own cash-share series have (φ = 0.9214, the median over
36 runs), the circular shift rejects a trend-free null in 0.071 of replications, the window permutation in 0.119 and
the registered day-block permutation in **0.120**; at φ = 0.99 all three pass a third of null series. Permuting pieces
of a persistent series manufactures trends, whatever the number of distinct values. Only the path-level sign-flip holds
size (0.043), and it cannot reject with fewer than six paths (exact floor 2 / 2ⁿ; size 0.000 at three). **A claim that
the mandate's effect decays with time is therefore made across paths with N3, or not made** (P8-11; addendum 12).

<!-- table:e8_null -->
AR(1) daily series, T = 200, no trend; 1,000 replications, 999 null draws each. φ_pilot = the median lag-1 autocorrelation of daily cash share over the pilot's 36 main runs = **0.9214** (P10 0.715, P90 0.988). One run under N0 has at most 8 rotations, so its smallest attainable p is 0.125.

| φ | runs (pairs for N3) | N0 circular shift (v2) | N1 window permutation | N2 day-block permutation | N3 path-level sign-flip |
|---|---|---|---|---|---|
| 0.9 | 3 | **0.087 [0.071, 0.106]** | **0.106 [0.088, 0.127]** | **0.111 [0.093, 0.132]** | 0.000 [0.000, 0.004] |
| 0.9 | 36 | 0.062 [0.049, 0.079] | **0.101 [0.084, 0.121]** | **0.109 [0.091, 0.130]** | 0.044 [0.033, 0.059] |
| 0.9214 (pilot) | 3 | **0.088 [0.072, 0.107]** | **0.105 [0.087, 0.126]** | **0.124 [0.105, 0.146]** | 0.000 [0.000, 0.004] |
| 0.9214 (pilot) | 36 | **0.071 [0.057, 0.089]** | **0.119 [0.100, 0.141]** | **0.120 [0.101, 0.142]** | 0.043 [0.032, 0.057] |
| 0.97 | 3 | **0.166 [0.144, 0.190]** | **0.233 [0.208, 0.260]** | **0.243 [0.217, 0.271]** | 0.000 [0.000, 0.004] |
| 0.97 | 36 | **0.135 [0.115, 0.158]** | **0.225 [0.200, 0.252]** | **0.229 [0.204, 0.256]** | 0.045 [0.034, 0.060] |
| 0.99 | 3 | **0.269 [0.242, 0.297]** | **0.365 [0.336, 0.395]** | **0.384 [0.354, 0.415]** | 0.000 [0.000, 0.004] |
| 0.99 | 36 | **0.237 [0.212, 0.264]** | **0.336 [0.307, 0.366]** | **0.365 [0.336, 0.395]** | 0.056 [0.043, 0.072] |
<!-- /table:e8_null -->

### 3.5 E8.4 — are the salience shares identified?

**Reading, on the pilot's own designs: no, and not by a margin.**

- **The main runs (start-at-target, 36 runs).** The start share is a function of the persona: the R² of the start block
  on the persona block is **1.000** and their canonical correlation **1.000**. A surrogate cannot tell a persona's text
  from the starting allocation that persona's band centre fixed, so any split of importance between the two is
  arbitrary. That is weakness 55, shown rather than described.
- **The nine common-start runs.** They vary the persona and nothing else: every directive is "none", and there is no
  no-persona or O3 reference. The directive share has nothing to estimate and the persona share has no null.

The registered condition could never have been met (addendum 10). Under the adopted reading the pilot's verdicts are
unchanged, because every pilot design fails for reasons that do not depend on clause (i). The known-answer designs
below show what a common start with the reference levels would buy. **D11 is put to the team with this table
(section 5).**

<!-- table:e8_identification -->
Clause (i) is read on the persona and directive blocks; as registered it also asked the start block to vary, which clause (iii) forbids, so no design passes as registered (addendum 10) — that verdict is the last column.

| design | runs | start designs | rank P / D / S / all | (i) P, D vary | (ii) | (iii) | (iv) | R² of S on P, D | max canonical corr P~S | P~D | **identified** | as registered |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot_main_all_arms | 36 | target | 2 / 4 / 1 / 6 | yes | **no** | **no** | **no** | 1.000 | 1.000 | 0.500 | **NO** | no |
| pilot_main_static_memory | 18 | target | 2 / 3 / 1 / 5 | yes | **no** | **no** | **no** | 1.000 | 1.000 | 0.707 | **NO** | no |
| pilot_common_start | 9 | common | 2 / 0 / 0 / 2 | **no** | yes | yes | **no** | — | — | — | **NO** | no |
| A_start_at_target | 48 | target | 2 / 3 / 1 / 5 | yes | **no** | **no** | **no** | 1.000 | 1.000 | 0.707 | **NO** | no |
| B_common_start_with_references | 96 | common | 5 / 3 / 0 / 8 | yes | yes | yes | yes | — | — | 0.577 | **yes** | no |
<!-- /table:e8_identification -->

<!-- table:e8_salience_shares -->
Known answer: c* depends on the persona and the market only (no directive effect). Shares over 10 surrogate seeds:

| design | window | S_persona mean (min–max) | S_start mean (min–max) | S_directive mean (min–max) | S_market mean | OOF R² |
|---|---|---|---|---|---|---|
| A_start_at_target | 1 | 0.697 (0.639–0.747) | 0.262 (0.212–0.320) | 0.000 (0.000–0.000) | 0.041 | 0.967 |
| A_start_at_target | 26 | 0.914 (0.903–0.923) | 0.051 (0.043–0.060) | 0.000 (0.000–0.000) | 0.035 | 0.971 |
| B_common_start_with_references | 1 | 0.979 (0.979–0.980) | 0.000 (0.000–0.000) | 0.000 (0.000–0.000) | 0.021 | 0.969 |
| B_common_start_with_references | 26 | 0.975 (0.974–0.975) | 0.000 (0.000–0.000) | 0.000 (0.000–0.000) | 0.025 | 0.970 |
<!-- /table:e8_salience_shares -->

**Reading of the known-answer designs.** In both synthetic designs the chosen allocation depends on the persona and the
market only, with no directive effect. Two things follow.

- **Start-at-target splits one persona effect arbitrarily.** The surrogate gives S_persona 0.697 and S_start 0.262 in
  the first window. The split moves by about 0.1 across ten surrogate seeds (persona 0.639–0.747, start
  0.212–0.320), and to 0.914 / 0.051 in the second window, which was generated identically. Two blocks carrying the
  same information take turns claiming it. **That is non-identification, visible.**
- **The common-start design with the NONE and O3 references recovers the known answer, stably.** S_persona is
  0.979 in every seed (range 0.979–0.980) and 0.975 in the second window, and S_directive is 0. The start share is
  not applicable, because a common start has no start variation to attribute.

So the measure is not broken; the pilot's designs could not identify it. **The main grid carries the cells that
can: a common-start slice with the NONE reference (D11; P8-13, P8-14).**

**The seed-cluster bootstrap leaked the first time it ran** (addendum 18). The table below is the re-run with the fix;
the leaky run's intervals are kept in `e8_4/bootstrap_leaky.json` and not used.

- **What went wrong.** On data where the directive share is 0, the directive interval [0.00019, 0.0029] excludes 0,
  and neither interval contains its own point estimate.
- **Why.** The copies of a resampled seed were relabelled into different cross-validation folds, so test rows had
  identical twins in the training rows.
- **The diagnostic.** The run's first 12 resamples were refitted with each seed's copies kept in one fold:

  | median share | copies in different folds (as run) | copies in one fold | point estimate |
  |---|---|---|---|
  | directive | 0.00094 | 0.000019 | — |
  | persona | 0.969 | 0.978 | 0.979 |
  | out-of-fold R² | 0.979 | 0.968 | 0.969 |

  The inflated R² is the leak.
- **The fix.** Each seed's copies now stay in one fold (`test_salience_bootstrap_copies_share_a_fold`; P8-18).
- **The re-run** (the registered 200 refits per window, 19,875 s). Every interval now contains its point estimate:
  - S_persona: 0.979 [0.974, 0.984] and 0.975 [0.970, 0.980];
  - S_directive: 3.2 × 10⁻⁶ [1.2 × 10⁻⁶, 9.4 × 10⁻⁵] and 1.1 × 10⁻⁵ [3.1 × 10⁻⁶, 1.9 × 10⁻⁴], an upper limit
    14–31× below the leaky run's.

  On data with no directive effect, the measure gives the directive block at most about 0.02 % of the importance and
  the persona block 97–98 %.
- **One registered check fails by construction, fix or no fix.** A share is a sum of importances clipped at 0, so
  "the directive interval covers 0" cannot pass.

<!-- table:e8_salience_bootstrap -->
Design B through `salience_by_window(identification="v2_1")`, 200 seed-cluster refits per window; cross-validation folds grouped by the original seed of each resampled copy (evaluation/salience._boot_frame; addendum 18).

| window | status | S_persona [95 %] | excludes 0 | S_directive [95 %] | covers 0 |
|---|---|---|---|---|---|
| 1 | IDENTIFIED | 0.979 [0.974, 0.984] | yes | 3.20e-06 [1.22e-06, 9.42e-05] | **no** |
| 26 | IDENTIFIED | 0.975 [0.970, 0.980] | yes | 1.11e-05 [3.07e-06, 1.93e-04] | **no** |

the shares are sums of max(permutation importance, 0), so a share cannot be negative and its lower percentile reaches 0 only if at least 2.5 % of refits give it exactly 0
<!-- /table:e8_salience_bootstrap -->

### 3.6 E8.5 — the variance pilot

#### The first smoke and its cost gate (Flash at the provider-default thinking)

<!-- table:e8_smoke_first -->
| run | status | seconds | calls | input tokens | output tokens (reasoning) | $ |
|---|---|---|---|---|---|---|
| `gemini-2.5-flash__ISFJ__static__bull_trap__seed2001__rep0` | failed | 2000 | 200 | 377,409 | 387,434 (367,673) | 1.082 |
| `gemini-2.5-flash__ISFJ__memory__bull_trap__seed2001__rep0` | failed | 1396 | 200 | 392,801 | 267,612 (248,462) | 0.787 |
| `gpt-5-mini__ISFJ__static__bull_trap__seed2001__rep0` | failed | 1454 | 200 | 360,775 | 121,942 (102,464) | 0.334 |
| `gpt-5-mini__ISFJ__memory__bull_trap__seed2001__rep0` | failed | 1143 | 200 | 374,663 | 93,418 (75,456) | 0.281 |

| design | model | $ per run (measured) | runs | projected $ | output tokens / call | reasoning / call | seconds / run |
|---|---|---|---|---|---|---|---|
| main | gemini-2.5-flash | 0.934 | 576 | 538.18 | 1638 | 1540 | 1698 |
| transfer | gpt-5-mini | 0.307 | 144 | 44.25 | 538 | 445 | 1298 |

Projected total with L3 ($12): **$594.43** against the approval $139 and the gate $174 → **STOP**.
<!-- /table:e8_smoke_first -->

**Reading.** The registered gate did its job: the design the plan priced at ≈ $105 costs ≈ $594, because Gemini 2.5
Flash spends 1,540 thinking tokens per call and bills them as output — 94 % of what it emits. The plan's figure
assumed 120 output tokens. GPT-5 mini reasons less (445 per call). Two runs per model is a small sample and the two
Flash runs differ by 37 %, but no plausible spread brings the total near the $174 gate. **No batch started; the
spend decision is the team's (section 5).** The same arithmetic moves Phase 9: Tier A is ≈ $1,090 at this price.

#### The amended configuration (P8-8): Flash with thinking off — the second smoke and its gate

**Reading.** With thinking off, Flash emits ≈ 106 tokens per call and bills **$0.168 per run** — the estimate made from
the first smoke's own non-thinking tokens, confirmed. A run takes ≈ 4 minutes instead of ≈ 28. The gate passes at
$153.04 against $189, and the first smoke's four runs, which had broken on the runner's meta write, are replaced by
four `ok` runs under the fixed runner. The batch was launched on this gate.

<!-- table:e8_smoke -->
| run | status | seconds | calls | input tokens | output tokens (reasoning) | $ |
|---|---|---|---|---|---|---|
| `gemini-2.5-flash__ISFJ__static__bull_trap__seed2001__rep0` | ok | 246 | 200 | 377,425 | 21,685 (0) | 0.167 |
| `gemini-2.5-flash__ISFJ__memory__bull_trap__seed2001__rep0` | ok | 241 | 200 | 392,787 | 20,654 (0) | 0.169 |
| `gpt-5-mini__ISFJ__static__bull_trap__seed2001__rep0` | ok | 1448 | 200 | 360,767 | 119,987 (100,800) | 0.330 |
| `gpt-5-mini__ISFJ__memory__bull_trap__seed2001__rep0` | ok | 1231 | 200 | 374,665 | 93,727 (75,584) | 0.281 |

| design | model | $ per run (measured) | runs | projected $ | output tokens / call | reasoning / call | seconds / run |
|---|---|---|---|---|---|---|---|
| main | gemini-2.5-flash | 0.168 | 576 | 97.03 | 106 | 0 | 244 |
| transfer | gpt-5-mini | 0.306 | 144 | 44.01 | 534 | 441 | 1339 |

Projected total with L3 ($12): **$153.04** against the approval $151 and the gate $189 → **PASS**.
<!-- /table:e8_smoke -->

#### The power analysis on known answers, before any pilot number was read (addendum 13, 16)

<!-- table:e8_validate -->
3 personas × 2 arms × 4 scenarios × 8 seeds × 3 replicates per dataset; 200 datasets per setting; 2,000 bootstrap resamples. Nominal coverage of a one-sided limit: 0.90. Coverage with its Wilson 95 % interval.

| seed × arm sd | replicate sd | median estimate ÷ truth (R = 1) | percentile bootstrap (registered), R = 1 | R = 3 | closed-form limit, R = 1 | R = 3 | plug-in seeds below the truth's: bootstrap | closed form |
|---|---|---|---|---|---|---|---|---|
| 0.00 | 0.05 | 1.008 | 0.92 [0.87, 0.95] | 0.97 [0.94, 0.99] | 0.94 [0.90, 0.97] | 0.94 [0.90, 0.97] | 0.07 | 0.04 |
| 0.03 | 0.04 | 0.998 | **0.67 [0.60, 0.73]** | **0.64 [0.57, 0.70]** | 0.94 [0.89, 0.96] | 0.92 [0.87, 0.95] | 0.29 | 0.06 |
| 0.05 | 0.02 | 0.998 | **0.60 [0.53, 0.67]** | **0.59 [0.53, 0.66]** | 0.94 [0.90, 0.97] | 0.94 [0.89, 0.96] | 0.40 | 0.06 |

Bold: the interval lies entirely below the nominal 0.90, so the limit does not deliver its assurance.
<!-- /table:e8_validate -->

**Reading.** This check was not registered (addendum 13); it was added because the main grid's seed count rests on an
upper limit covering the true σ_d as often as it claims, and hard rule 2 asks for that to be shown on a known answer
before a real number is read. **The registered limit fails it.** The point estimates are unbiased, but whenever
seed × arm variance is present the percentile path bootstrap's "90 %" limit covers the truth only 60–67 % of the
time — resampling eight seeds per scenario understates how uncertain a standard deviation is — and a grid sized on
it would get fewer seeds than D12 needs in 29–40 % of cases. The closed-form limit (the modified large-sample bound
for the two mean squares σ_d is built from, equal to the registered χ² limit at the observed replicate count) covers
0.915–0.945 in every setting and sizes the grid too small in 4–6 % of cases, for a few more seeds per cell. **The main
grid is sized on the closed-form limit, and the registered bootstrap limit is reported beside every number** (P8-15;
addendum 16). Both decisions were fixed before any E8.5 number was read. The bootstrap itself now runs as array
arithmetic proven equal to the loop, ≈ 300× faster (`test_boot_plug_ins_fast_equals_loop`,
`test_transfer_ratios_fast_equals_loop`).

#### Variance components, the power table, and the transfer check

**Flash, the model the grid is sized on.** 576 runs with thinking off: the 574 batch runs plus the 2 smoke runs.
1 parse fallback, 0 provider fallbacks, $96.69.

- **B and D are not alike.** B's seed-level σ_d at R = 1 is 0.0490 at θ 0.05 and D's is 0.0232; at θ 0.0020 they
  are 0.0344 and 0.0115. D is the quieter term by a factor of 2–3. A design sized for band-MAS therefore detects
  smaller D differences: 0.033 at θ 0.05 and 0.016 at θ 0.0020 with 19 seeds. That is P8-2's achieved power, on
  Flash's variance.
- **Most of a pair's variance is the arm effect varying across seeds, not decoding noise.** For every metric, σ²_int
  is 65–83 % of Var(d) at R = 1. Replicates buy little: a contrast cell needs 38 runs at R = 1 (19 seeds), 68 at
  R = 2 and 96 at R = 3. **The grid runs R = 1.**
- **The registered ICCs mislead.** The registered REML puts 25–37 % of the variance in path (turnover 13 %) and
  about 0 in path × arm (turnover 0.25). It reports 0.0025 as "replicate" variance for band-MAS, 15× the pooled
  replicate variance. With persona × path in the model, that term carries 82 % of band-MAS's variance (addendum 17).
  The power table never used the REML fit; the mixed model the grid will be analysed with does (below).
- **Descriptive only.** Band-MAS's mean memory − static difference is +0.047 over the 96 pairs. E8.5 sizes the grid;
  it tests nothing.

**Sizing on Flash's variance alone gives 19 seeds per persona × scenario cell,** under both limits: σ_d(R = 1) 0.0348,
closed-form 90 % limit 0.0380, registered bootstrap limit 0.0372 (Appendix A as written, α′ = 0.05 / 36). The
paired-correct count is 10; the bootstrap's 80 % and 95 % limits give 17 and 20. At Tier A's 5 seeds, band-MAS's
MDD is 0.097, about twice Δ.

**The transfer check.** On bull_trap, with the same seeds, personas and arms (24 pairs each), GPT-5 mini's σ_d is
0.0651 against Flash's 0.0294: **ratio 2.21 [1.88, 2.99]**.

- **Every B, D and MCR metric agrees:** 2.08–2.69, with every 90 % lower limit ≥ 1.41. Only turnover goes the other
  way (0.80).
- **Temperature is not what differs.** The ratio transfers model and temperature together (1.0 against 0.2). But
  GPT-5 mini's replicate variance on bull_trap is only 1.35× Flash's (0.000123 against 0.000091), while its seed ×
  arm variance is 5.2× (0.00416 against 0.000804). GPT-5 mini's arm effect varies more from seed to seed.

**By the registered rule, the main grid's plug-in is 0.0380 × 2.21 = 0.0841, and the grid needs 93 seeds per persona
× scenario cell at R = 1.** Beside it: 47 paired-correct, 169 at the ratio's upper limit, 89 on the bootstrap limit.
At that design, D's MDD at its own ratio is 0.039 at θ 0.05 and 0.015 at θ 0.0020. **Whether 93 seeds are affordable,
and on which roster, is D2 for Phase 9** (section 5; P8-16).

The count also assumes an analysis that pairs within persona × path. On Flash's rows at R = 1, E1 as registered has
2.27× the paired SE as fitted by lbfgs, and 2.48× at the better REML optimum (`e8_5/e1_pairing_se.json`): about
5–6× the seeds for the same power. Addendum 17's simulation did not adopt
E1-amended (P8-17): the crossed model is descriptive, and E2's intervals decide. **Neither holds size at six models
when the arm effect varies by model (sd 0.03).** Beyond a point, seeds do not buy the contrast; models do.

Section 5.5's model-level DESIGN table puts numbers on this (t with M − 1 df at α′, 19 seeds per cell; the table
above):

| between-model sd | 2 models | 3 models | 5 models | 8 models |
|---|---|---|---|---|
| half the σ_d limit | 0.006 | 0.025 | 0.25 | 0.86 |
| equal to the σ_d limit | — | — | — | 0.22 |

(Addendum 19 records that the eight-model row had been NaN until the power calculation was fixed.)

<!-- table:e8_components -->
| model | metric | pairs | mean memory − static | σ_d(R=1) point [closed-form 90 % limit; bootstrap limit] | σ_d(R=3) | σ²_int | σ²_rep | share of Var(d) at R=1 from seed×arm | ICC path | ICC path×arm |
|---|---|---|---|---|---|---|---|---|---|---|
| gemini-2.5-flash | `band_mas` | 96 | 0.0468 | 0.0348 [0.0380; 0.0372] | 0.0313 | 0.000869 | 0.000170 | 0.719 | 0.300 | 0.000 |
| gemini-2.5-flash | `v21_mcr_B_0.05` | 96 | 0.0416 | 0.0490 [0.0538; 0.0556] | 0.0455 | 0.001908 | 0.000245 | 0.796 | 0.279 | 0.000 |
| gemini-2.5-flash | `v21_mcr_D_0.05` | 96 | 0.0021 | 0.0232 [0.0253; 0.0259] | 0.0207 | 0.000373 | 0.000082 | 0.695 | 0.275 | 0.000 |
| gemini-2.5-flash | `v21_mcr_0.05` | 96 | 0.0437 | 0.0620 [0.0682; 0.0725] | 0.0585 | 0.003204 | 0.000320 | 0.834 | 0.253 | 0.005 |
| gemini-2.5-flash | `v21_mcr_B_0.002` | 96 | 0.0466 | 0.0344 [0.0376; 0.0369] | 0.0309 | 0.000845 | 0.000169 | 0.714 | 0.304 | 0.000 |
| gemini-2.5-flash | `v21_mcr_D_0.002` | 96 | 0.0018 | 0.0115 [0.0125; 0.0119] | 0.0100 | 0.000086 | 0.000023 | 0.648 | 0.374 | 0.000 |
| gemini-2.5-flash | `v21_mcr_0.002` | 96 | 0.0483 | 0.0376 [0.0410; 0.0402] | 0.0338 | 0.001009 | 0.000201 | 0.715 | 0.282 | 0.000 |
| gemini-2.5-flash | `turnover` | 96 | -9.2996 | 9.5365 [10.4756; 10.2194] | 8.8856 | 72.957438 | 8.993839 | 0.802 | 0.127 | 0.255 |
| gpt-5-mini | `band_mas` | 24 | 0.0259 | 0.0664 [0.0830; 0.0788] | 0.0651 | 0.004160 | 0.000123 | 0.944 | 0.296 | 0.086 |
| gpt-5-mini | `v21_mcr_B_0.05` | 24 | 0.0102 | 0.0626 [0.0779; 0.0706] | 0.0606 | 0.003555 | 0.000180 | 0.908 | 0.261 | 0.090 |
| gpt-5-mini | `v21_mcr_D_0.05` | 24 | 0.0219 | 0.0271 [0.0336; 0.0303] | 0.0260 | 0.000642 | 0.000047 | 0.872 | 0.397 | 0.183 |
| gpt-5-mini | `v21_mcr_0.05` | 24 | 0.0321 | 0.0558 [0.0691; 0.0602] | 0.0532 | 0.002685 | 0.000213 | 0.863 | 0.243 | 0.003 |
| gpt-5-mini | `v21_mcr_B_0.002` | 24 | 0.0252 | 0.0651 [0.0814; 0.0758] | 0.0639 | 0.003995 | 0.000124 | 0.942 | 0.301 | 0.083 |
| gpt-5-mini | `v21_mcr_D_0.002` | 24 | 0.0148 | 0.0201 [0.0249; 0.0220] | 0.0193 | 0.000356 | 0.000023 | 0.885 | 0.631 | 0.083 |
| gpt-5-mini | `v21_mcr_0.002` | 24 | 0.0400 | 0.0599 [0.0747; 0.0678] | 0.0583 | 0.003302 | 0.000144 | 0.920 | 0.349 | 0.037 |
| gpt-5-mini | `turnover` | 24 | -3.4363 | 5.9971 [7.4585; 7.2239] | 5.7911 | 32.322724 | 1.821122 | 0.899 | 0.208 | 0.098 |
<!-- /table:e8_components -->

<!-- table:e8_power -->
D12: Δ = 0.05 band-MAS, power 0.8, α' = 0.05 / 36 = 0.00139; plug-in: PRIMARY: the closed-form one-sided 90 % limit (modified large-sample; known-answer coverage 0.915-0.945); BESIDE: the registered percentile path-bootstrap limit (coverage 0.60-0.67 when seed x arm variance is present) -- P8-15, addendum 16.

| replicates R | σ_d point | σ_d closed-form 90 % limit | **seeds / cell, App. A (Bonferroni)** | paired-correct (Bonferroni) | App. A (nominal α) | paired (nominal) | App. A at the point σ | bootstrap limit (registered): σ_d / seeds | bootstrap 80 % / 95 % limit: seeds | runs / contrast cell |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.0348 | 0.0380 | **19** | 10 | 10 | 5 | 16 | 0.0372 / 19 | 17 / 20 | 38 |
| 2 | 0.0322 | 0.0357 | **17** | 9 | 8 | 4 | 14 | 0.0344 / 16 | 15 / 17 | 68 |
| 3 | 0.0313 | 0.0349 | **16** | 8 | 8 | 4 | 13 | 0.0335 / 15 | 14 / 16 | 96 |

Minimum detectable difference (80 % power) in each metric's own units, at the closed-form limit (the registered bootstrap limit beside):

| metric | design | seeds / cell | R | σ_d closed-form limit | MDD App. A (Bonferroni) | paired (Bonferroni) | App. A (nominal) | App. A (Bonferroni) at the bootstrap limit |
|---|---|---|---|---|---|---|---|---|
| `band_mas` | E8.5 (8 seeds, 3 reps) | 8 | 3 | 0.0349 | 0.0704 | 0.0498 | 0.0488 | 0.0676 |
| `band_mas` | Tier A (5 seeds, 1 rep) | 5 | 1 | 0.0380 | 0.0970 | 0.0686 | 0.0673 | 0.0951 |
| `band_mas` | band-MAS-sized (R=1, App. A, Bonferroni) | 19 | 1 | 0.0380 | 0.0498 | 0.0352 | 0.0345 | 0.0488 |
| `v21_mcr_B_0.05` | E8.5 (8 seeds, 3 reps) | 8 | 3 | 0.0506 | 0.1022 | 0.0723 | 0.0709 | 0.1054 |
| `v21_mcr_B_0.05` | Tier A (5 seeds, 1 rep) | 5 | 1 | 0.0538 | 0.1374 | 0.0971 | 0.0953 | 0.1419 |
| `v21_mcr_B_0.05` | band-MAS-sized (R=1, App. A, Bonferroni) | 19 | 1 | 0.0538 | 0.0705 | 0.0498 | 0.0489 | 0.0728 |
| `v21_mcr_D_0.05` | E8.5 (8 seeds, 3 reps) | 8 | 3 | 0.0230 | 0.0464 | 0.0328 | 0.0322 | 0.0476 |
| `v21_mcr_D_0.05` | Tier A (5 seeds, 1 rep) | 5 | 1 | 0.0253 | 0.0645 | 0.0456 | 0.0448 | 0.0662 |
| `v21_mcr_D_0.05` | band-MAS-sized (R=1, App. A, Bonferroni) | 19 | 1 | 0.0253 | 0.0331 | 0.0234 | 0.0230 | 0.0340 |
| `v21_mcr_0.05` | E8.5 (8 seeds, 3 reps) | 8 | 3 | 0.0650 | 0.1313 | 0.0929 | 0.0911 | 0.1402 |
| `v21_mcr_0.05` | Tier A (5 seeds, 1 rep) | 5 | 1 | 0.0682 | 0.1743 | 0.1233 | 0.1209 | 0.1852 |
| `v21_mcr_0.05` | band-MAS-sized (R=1, App. A, Bonferroni) | 19 | 1 | 0.0682 | 0.0894 | 0.0632 | 0.0620 | 0.0950 |
| `v21_mcr_B_0.002` | E8.5 (8 seeds, 3 reps) | 8 | 3 | 0.0344 | 0.0695 | 0.0492 | 0.0482 | 0.0666 |
| `v21_mcr_B_0.002` | Tier A (5 seeds, 1 rep) | 5 | 1 | 0.0376 | 0.0960 | 0.0679 | 0.0666 | 0.0943 |
| `v21_mcr_B_0.002` | band-MAS-sized (R=1, App. A, Bonferroni) | 19 | 1 | 0.0376 | 0.0492 | 0.0348 | 0.0341 | 0.0484 |
| `v21_mcr_D_0.002` | E8.5 (8 seeds, 3 reps) | 8 | 3 | 0.0112 | 0.0226 | 0.0160 | 0.0157 | 0.0211 |
| `v21_mcr_D_0.002` | Tier A (5 seeds, 1 rep) | 5 | 1 | 0.0125 | 0.0319 | 0.0226 | 0.0221 | 0.0305 |
| `v21_mcr_D_0.002` | band-MAS-sized (R=1, App. A, Bonferroni) | 19 | 1 | 0.0125 | 0.0164 | 0.0116 | 0.0114 | 0.0157 |
| `v21_mcr_0.002` | E8.5 (8 seeds, 3 reps) | 8 | 3 | 0.0376 | 0.0759 | 0.0537 | 0.0527 | 0.0737 |
| `v21_mcr_0.002` | Tier A (5 seeds, 1 rep) | 5 | 1 | 0.0410 | 0.1048 | 0.0741 | 0.0727 | 0.1027 |
| `v21_mcr_0.002` | band-MAS-sized (R=1, App. A, Bonferroni) | 19 | 1 | 0.0410 | 0.0538 | 0.0380 | 0.0373 | 0.0527 |
| `turnover` | E8.5 (8 seeds, 3 reps) | 8 | 3 | 9.8848 | 19.9602 | 14.1140 | 13.8465 | 19.3585 |
| `turnover` | Tier A (5 seeds, 1 rep) | 5 | 1 | 10.4756 | 26.7571 | 18.9201 | 18.5616 | 26.1026 |
| `turnover` | band-MAS-sized (R=1, App. A, Bonferroni) | 19 | 1 | 10.4756 | 13.7261 | 9.7058 | 9.5219 | 13.3903 |

Model-level power (DESIGN: the between-model sd is not estimable from one model):

| models | τ / σ_d | seeds / cell | power (Bonferroni α, t with M − 1 df) |
|---|---|---|---|
| 2 | 0.5 | 19 | 0.006 |
| 2 | 1.0 | 19 | 0.003 |
| 2 | 2.0 | 19 | 0.002 |
| 3 | 0.5 | 19 | 0.025 |
| 3 | 1.0 | 19 | 0.008 |
| 3 | 2.0 | 19 | 0.003 |
| 5 | 0.5 | 19 | 0.247 |
| 5 | 1.0 | 19 | 0.044 |
| 5 | 2.0 | 19 | 0.009 |
| 8 | 0.5 | 19 | 0.863 |
| 8 | 1.0 | 19 | 0.222 |
| 8 | 2.0 | 19 | 0.028 |
<!-- /table:e8_power -->

<!-- table:e8_transfer -->
| metric | σ_d Flash (bull_trap) | σ_d GPT-5 mini (bull_trap) | ratio [90 %] | main-grid σ_d limit (Flash's limit × max(1, ratio)) | MDD at the main grid's seeds (App. A, Bonferroni) |
|---|---|---|---|---|---|
| `band_mas` | 0.0294 | 0.0651 | 2.214 [1.878, 2.993] | 0.0841 | 0.0498 |
| `v21_mcr_B_0.05` | 0.0239 | 0.0606 | 2.536 [1.892, 3.386] | 0.1364 | 0.0808 |
| `v21_mcr_D_0.05` | 0.0101 | 0.0260 | 2.579 [1.888, 2.990] | 0.0652 | 0.0386 |
| `v21_mcr_0.05` | 0.0197 | 0.0532 | 2.693 [1.929, 3.760] | 0.1838 | 0.1088 |
| `v21_mcr_B_0.002` | 0.0290 | 0.0639 | 2.199 [1.789, 2.914] | 0.0826 | 0.0489 |
| `v21_mcr_D_0.002` | 0.0093 | 0.0193 | 2.079 [1.407, 2.696] | 0.0260 | 0.0154 |
| `v21_mcr_0.002` | 0.0248 | 0.0583 | 2.351 [1.805, 4.348] | 0.0965 | 0.0571 |
| `turnover` | 7.2879 | 5.7911 | 0.795 [0.483, 1.117] | 10.4756 | 6.2041 |

Main-grid plug-in σ_d (band-MAS, R = 1), closed-form limit: 0.0380 × max(1, 2.214) = **0.0841**; at the ratio's upper limit 0.1137; at the registered bootstrap limit 0.0825. GPT-5 mini runs at temperature 1.0 (the only value the provider accepts): the ratio is a transfer of model AND temperature.

Seeds per persona × scenario cell the main grid needs at that plug-in (R = 1, App. A, α' = 0.00139): **93** (paired-correct 47); at the ratio's upper limit 169; at the registered bootstrap limit 89.
<!-- /table:e8_transfer -->

### 3.7 L3 (Phase 6's probe, run under this phase's D2)

<!-- table:e8_l3 -->
200 probes; the entitled reader (level-free GBT) scores 0.780 [0.718, 0.832]; ceiling for a model 0.837; null p95 0.560. The rule "over-valued iff price > analyst fair-value estimate" scores 0.520 on the same probes.

| model | arm | temperature that ran | sign accuracy [Wilson 95 %] | fair / unparsed | errors | agreement with the analyst rule | verdict |
|---|---|---|---|---|---|---|---|
| gemini-2.5-flash | normal | 0.0 | 0.520 [0.451, 0.588] | 0.01 | 0 | 0.990 | PASS |
| gemini-2.5-flash | shuffled | 0.0 | 0.485 [0.417, 0.554] | 0.01 | 0 | 0.990 | PASS |
| gpt-5-mini | normal | 0.0 requested; langchain_openai drops it for gpt-5 models, so the provider default 1.0 ran | 0.520 [0.451, 0.588] | 0.01 | 0 | 0.990 | PASS |
| gpt-5-mini | shuffled | 0.0 requested; langchain_openai drops it for gpt-5 models, so the provider default 1.0 ran | 0.480 [0.412, 0.549] | 0.02 | 0 | 0.980 | PASS |
| claude-sonnet-5 | normal | none sent (provider default; the model rejects one, P8-12) | 0.505 [0.436, 0.574] | 0.04 | 0 | 0.965 | PASS |
| claude-sonnet-5 | shuffled | none sent (provider default; the model rejects one, P8-12) | 0.475 [0.407, 0.544] | 0.03 | 0 | 0.970 | PASS |
| claude-haiku-4-5-20251001 | normal | 0.0 | 0.520 [0.451, 0.588] | 0.00 | 0 | 0.930 | PASS |
| claude-haiku-4-5-20251001 | shuffled | 0.0 | 0.530 [0.461, 0.598] | 0.00 | 0 | 0.930 | PASS |
| claude-opus-5 | normal | none sent (provider default; the model rejects one, P8-12) | 0.515 [0.446, 0.583] | 0.03 | 0 | 0.970 | PASS |
| claude-opus-5 | shuffled | none sent (provider default; the model rejects one, P8-12) | 0.475 [0.407, 0.544] | 0.03 | 0 | 0.970 | PASS |

Pairwise agreement between models, normal arm: claude-haiku-4-5-20251001 / claude-opus-5 0.905; claude-haiku-4-5-20251001 / claude-sonnet-5 0.895; claude-haiku-4-5-20251001 / gemini-2.5-flash 0.920; claude-haiku-4-5-20251001 / gpt-5-mini 0.920; claude-opus-5 / claude-sonnet-5 0.985; claude-opus-5 / gemini-2.5-flash 0.980; claude-opus-5 / gpt-5-mini 0.980; claude-sonnet-5 / gemini-2.5-flash 0.975; claude-sonnet-5 / gpt-5-mini 0.975; gemini-2.5-flash / gpt-5-mini 1.000.
<!-- /table:e8_l3 -->

**Reading.** Every model passes L3's rule, and the table says why that is not reassurance in the way the rule
imagined. The probe asks whether the stock is over- or under-valued relative to its fundamental value; the models
answer by comparing the price with the one rendered field labelled a value, the analyst fair-value estimate. That
rule decides 93–99 % of every model's answers, it is at chance on this environment, and so every model is at
chance — the entitled reader, which uses the whole rendered observation, scores 0.780. Any two of the five models
agree on 90–100 % of probes, and two from different providers gave identical answers on all 200, because all of them
applied the same rule. **The models do not leak the hidden value; they do not
read the mispricing either.** That is a fact about the models and the analyst field, and it matters for the
benchmark's premise that an agent can act on information in the observation.

**Three defects of the run, fixed before any answer was used** (P8-12; addendum 14): Claude Sonnet 5 and Opus 5
reject any temperature, so all 800 of their first calls failed, and the probe marked those four arms PASS; they now
run with none sent and an errored arm is NOT COMPUTABLE. A first re-run returned thinking blocks that pushed 17 of
Sonnet 5's first 146 answers past the 500-character cut; it was stopped and discarded, and only a reply's text parts
are kept. **Three of five models ran at a temperature other than Phase 6's registered 0.0** (GPT-5 mini at 1.0 because
`langchain_openai` drops 0.0; Sonnet 5 and Opus 5 with none sent); the table's temperature column records it.

### 3.8 The switches, and the proof that they are inert when off

| switch | default | proved inert by |
|---|---|---|
| `StatefulV2Agent(harness=)` / `RunConfig.harness_version` | `"v2"` | `test_phase8_switches_inert` — every message list the model received, every history, every `context_log()` for rolling 5 / 20, full, summary, with and without the block, and a forced fallback, identical to the golden record |
| `mandate_block(..., placebo_version=)` / `RunConfig.placebo_version` | `"v2"` | the same record: every block for 5 personas × 7 wordings × 5 kinds, and `Prompt_Hash` of every stateless arm; `test_placebo_version_switch_inert` |
| `experiments/arms_v2.ARMS` | the 18 existing arms | every existing arm's `build_config` identical; the two new arms and the two new `RunConfig` fields at their v2 default are the declared additions |
| `evaluation/salience.salience_by_window(identification=)` | `"v2"` | the golden record's salience block (sequential backend) |
| `tools/stats_v2` | the v2 functions unchanged | the golden record's `run_stats`, trend null and sign-flip on fixed frames; the re-specification (P8-9 – P8-11) is new functions beside them, equal to the estimators the simulation validated (`test_stats_v21_matches_simulation`) |
| `agent/params/harness.json` | the constructor defaults unchanged | `test_harness_params_match_code` |
| `simulation/runner_v2.py` meta write | — | `test_runner_meta_with_live_client`: identical JSON to the asdict construction for a run without a client |

### 3.9 A latent runner defect, found by the smoke

Every smoke run completed its 200 decisions, wrote a complete CSV (201 lines), and then failed:
`TypeError: cannot pickle '_thread.RLock' object` (GPT-5 mini) / `'_thread.lock'` (Gemini). The runner wrote
`meta.json` with `dataclasses.asdict(cfg)`, which deep-copies every field before the injected client is dropped, and a
live provider client holds a thread lock. The pilot never injected a client, so the line had never run with one; any
grid runner that injects a client — which is how per-run billed usage is captured — would have failed on every run.
Fixed field by field (P8-6).

### 3.10 The whole test tree

`python -m pytest -q -p no:cacheprovider tests/`, run once at the end (`docs/env_v2/generated/v2_1/e8_tests_full.log`):
**219 passed, 1 skipped, 4 xfailed; 0 failed, 0 errors.**

- **Against Phase 7** (191 passed, 1 skipped, 4 xfailed; `docs/env_v2/generated/v2_1/e7_tests_full2.log`): the 28
  extra passes are this phase's tests in `tests/test_v2_1_phase_8.py`. The skip count is unchanged, and so are the
  four xfails: the known-defect registry's two derived gates (L2, L2b) and the two permanent v1 baseline defects.
- **No older test was changed.** `tests/test_v2_1_phase_0.py`, `tests/test_v2_1_phase_7.py` and
  `tests/v2_freeze_manifest.json` were last written before this phase's pre-registration (10 Sep, 06:01–10:51), at
  the sizes Phase 7's changed-files list records.
- **It took 5 h 15 min** (Phase 7: 1 h), because it shared the laptop with E8.4's re-run and was paused by two
  sleeps (section 6).
- **One code file changed after the run started:** the report-table generator's number format (section 3.5).
  `test_phase8_report_tables_match_files` was re-run on its own afterwards and passes.

### 3.11 Path hashes and the freeze

**The freeze manifest is unchanged: 30 files under `V2_FREEZE_PATTERNS`, 0 differing from `tests/v2_freeze_manifest.json`.**
Phase 8 touched no file the patterns cover — `envs/`, the scoring layer, `metrics_v2.py` and `targets.py` were read and
never edited — so no re-freeze is needed and `Env_Code_Hash` on a logged row is the one Phase 7 left. The files this
phase did change (`agent/`, `experiments/`, `simulation/runner_v2.py`, `evaluation/salience.py`, `tools/stats_v2.py`)
are outside the patterns: they change what an agent sees or how a result is computed, never a generator path.

**The 95-configuration path-hash fixture is byte-identical to Phase 7's: 0 of 95 configurations changed**
(`changed_non_analyst: []`; 190 analyst columns unchanged), regenerated into `path_hashes_phase8_after.json` and
compared with `path_hashes_phase7_after.json` (`path_hashes_phase8_compare.txt`). This phase changes no generator path.

---

## 4. Decisions taken and the parameter files

**P8-1** (D12) · **P8-2** (D alone) · **P8-3** (D2 for Phase 8, with the cost gate) · **P8-4** (the stateful
corrections behind a switch) · **P8-5** (the matched placebo behind a switch) · **P8-6** (the runner's meta write) ·
**P8-7** (the context-length factor) · **P8-8** (D2 re-opened by the gate: Flash with thinking off) · **P8-9** (the crossed
model and the two-way bootstrap, with their simulated size) · **P8-10** (the families and BY across them) · **P8-11** (the
path-level sign-flip as the only temporal null) · **P8-12** (L3's run defects) · **P8-13** (D11: a common-start slice
with a reference level; salience shares reported only there) · **P8-14** (NONE as the only reference level) ·
**P8-15** (the closed-form limit sizes the grid) · **P8-16** (the grid's sizing by the registered rule: 93 seeds per
cell) · **P8-17** (E1-amended not adopted; the crossed model descriptive at the better optimum; the model-level
reference carried to Phase 9) · **P8-18** (the salience bootstrap's fold leak fixed and the bootstrap re-run).

`agent/params/harness.json`, written by `tools/phase8/e8_write_params.py` from the code and the `e8_1` / `e8_2`
files, read back through `agent/harness_params.py`. `experiments/params/inference.json`, written by `tools/phase8/e8_write_inference.py` from the `e8_3` and `e8_5`
files by the registered adoption rules, and read back through `experiments/inference_params.py`
(`test_inference_params_readable`). It carries the main grid's sizing (P8-16). Its mixed-model and cluster-bootstrap
blocks record addendum 17's outcome (P8-17).

---

## 5. Decisions the team must take

| decision | state | the evidence in front of it |
|---|---|---|
| **E8.5's spend** (D2 re-opened by the registered gate) | **taken, 10 Sep 2026 (P8-8): Flash with thinking off. Spent $144.66 of the $151 approved (gate $189), both smokes included; L3's spend was not metered by the probe** | the registered design at the measured price ≈ $594 (Flash $0.934 × 576, GPT-5 mini $0.307 × 144, L3 $12); with thinking off the batches billed $0.1646 per Flash run and $0.3292 per GPT-5 mini run (`e8_5/ledger_*.jsonl`) |
| **The main grid's seeds and roster** (D2 for Phase 9) | **open** | **By the registered rule the main grid needs 93 seeds per persona × scenario cell at R = 1** (P8-1, P8-15, PREREG 5.6; `e8_5/transfer.json`): Flash's closed-form limit 0.0380 × GPT-5 mini's transfer ratio 2.21 = 0.0841. For comparison: 47 paired-correct; 169 at the ratio's upper 90 % limit; 19 on Flash's variance alone. **One contrast in E8.5's cell structure** (12 persona × scenario cells × 2 arms × 93 seeds = 2,232 runs per model) costs ≈ $367 on Flash and ≈ $735 on GPT-5 mini, at the batches' billed cost per run. If the affordable design falls short, the achieved power is reported and Δ does not move (P8-1 (v)). Two cautions: the ratio is a transfer of model **and** temperature (1.0 against 0.2), and it rests on one scenario (24 pairs per model) |
| **The model count and the reference distribution for confirmatory contrasts** (D2 for Phase 9, with the seed count) | **open** | When the arm effect varies by model, seeds do not buy a contrast's power. At a model × arm sd of 0.03 with six models and nineteen seeds, no validated estimator holds size with a normal reference; with a t reference on 5 df, power at α′ is 0.025–0.075 (addendum 17; P8-17). One model cannot measure the between-model sd (E8.5), so the roster decision rests on section 5.5's model-level DESIGN table (`e8_5/power.json`) |
| **D11** (salience shares) | **taken, 10 Sep 2026 (P8-13, P8-14): the main grid carries a common-start slice with the no-persona NONE reference; the shares are reported only there. O3 is not wired (it cannot run in v2, and v1's text contradicts the v2 bands); the team confirmed NONE only after being told it leaves the day-1 gate's null NOT COMPUTABLE** | section 3.5: not identified on any pilot design (R² of start on persona 1.000); the known answer recovered stably at common start with a reference (S_persona 0.979), and identified with NONE alone; addendum 15 |

---

## 6. Files written or changed

`PHASE_8_CHANGED_FILES.md`, generated from git and the working tree by `tools/phase8/e8_changed_files.py`. **Phase 7 is
uncommitted**, so the list marks every path that is also in Phase 7's list.

**On compute.** Every offline number is the laptop's. The heavy stage of this phase is an API, and cores do not buy
API throughput. Most simulations took minutes at six or seven workers. The long runs were:

- E8.3's persona × path simulation: 5,089 s on 7 workers;
- E8.4's seed-cluster bootstrap: 16,225 s for the leaky run and 19,875 s for the fixed one;
- the whole test tree.

The laptop slept twice during the fixed bootstrap and the test tree (22:59–23:25 and 01:59–03:25, 10–11 Sep). The
processes were paused, not restarted, and every refit's seed is fixed. The box and Kaggle were not used.

**Spend.** E8.5 cost $144.66 of the $151 approved: Flash $96.69 and GPT-5 mini $47.97, both smokes included
(`e8_5/ledger_*.jsonl`). L3's spend was not metered by the probe.

---

## 7. What was not done, and who owns it

| item | state | owner |
|---|---|---|
| **The main grid's roster at two or three models** | no interval estimator validated here holds size below six models when the arm effect varies by model (E1 0.077–0.100, E2 up to 0.123); Tier A's two workhorses are below that line. Every interval such a grid reports must carry its simulated size (P8-9) | D2 / Phase 9 |
| **The common-start slice of D11** | the main grid carries common-start cells with the NONE reference (P8-13, P8-14); the salience shares are computed only there. ≈ 150 stateless runs per model at a Tier-A size | Phase 9 |
| **The day-1 gate's null** | **stays NOT COMPUTABLE** under NONE only: the gate needs two no-persona labels and both trader arms are NONE. O3 would supply them, but it cannot run in v2 and its two arms separate by construction; the gate's "no arm in which no persona text is shown" message also misreports this case (addendum 15) | Phase 7's gate design / Phase 9 |
| **A logged provider-options column** | `RunConfig` has no field for provider options, so a run's CSV cannot say whether its model thought; E8.5 records the budget in its manifest, usage records and directory. The main grid needs it per row (addendum 9) | Phase 9 |
| **Thinking on against thinking off** | P8-8 fixes the grid's Flash configuration at thinking off; the only thinking-on runs are the first smoke's two, which cannot size a sensitivity | the team, if the claim needs it; Phase 9 |
| **The stateful arms' σ_d** | E8.5 is stateless, so REG-16 (ii)'s stateful-inclusion rule has no variance to read; the corrected harness (`harness_version="v2_1"`) and its covariate reach real runs with the main grid | Phase 9 / D2 |
| **Within-run trend claims** | no within-run permutation null holds size at the pilot's persistence; a temporal claim is made with the path-level sign-flip across ≥ 6 paths or not made (P8-11) | Phase 9's pre-registration |
| **The pilot's stateful covariate** | recomputed exactly from the logs (section 3.1); not re-run — the pilot's engine no longer exists (P7-8) | closed |
| **Co-primary θ's duplicate D** | tier C carries D at both θ (\|r\| = 0.992); kept because P7-4 makes both co-primary, stated beside every count | the team, if it wants one θ for D |
| **`evaluation/criteria.py` and `params/phase6_criteria.json` outside the freeze patterns** | carried from Phase 7, still not fixed — not this phase's files | Phase 10 |
| **The known-defect registry** | untouched: its two entries are the derived L2 and L2b gates | D17's chosen option; carried |
| **The all-rows L2 centred reading; items 7 and 12** | carried unchanged | the team; D15's owner |
| **Phase 7 and Phase 8 in one working tree** | Phase 7 is uncommitted, so git cannot separate the two phases' changes; `PHASE_8_CHANGED_FILES.md` marks every path that is also in Phase 7's list | the user (commit points) |
| **The main grid's seed count against its budget** | The registered rule gives 93 seeds per persona × scenario cell at R = 1 (P8-16). One static–memory contrast over E8.5's 12 cells then costs ≈ $367 on Flash and ≈ $735 on GPT-5 mini. Whether the grid is cut, the roster changed or the achieved power reported is not this phase's decision | D2 / Phase 9 |
| **The transfer ratio rests on one scenario and one other model, at another temperature** | 24 pairs on bull_trap. The excess is seed × arm variance, not replicate noise, so temperature does not explain it. GPT-5 mini accepts only 1.0, so the two models could not run at one temperature, and no third model was measured | Phase 9's pilot, if the team wants the ratio pinned |
| **The mixed model's optimizer** | lbfgs stops at a local optimum in 15–20 % of E1's fits and changes 0–11 of 100 decisions (addendum 17). `tools/stats_v2.crossed_mixed_model` fits with lbfgs, and P8-9's rates were measured with it | closed: `crossed_mixed_model(optimizer="best")`, used by `run_stats_v21`; the default stays the validated lbfgs (P8-17) |
| **The reference distribution for model-level contrasts** | With the arm effect varying by model (sd 0.03, a DESIGN value), E1 and E2 over-reject at six models and nineteen seeds. Post hoc, a t reference with M − 1 df restores size at a power at α′ of 0.025–0.075 (addendum 17). Not adopted, because it was chosen after the rates were read | Phase 9's pre-registration |
| **E8.3's simulation seeds** | They come from per-process string hashes, so the caches are valid draws but not bit-reproducible (addendum 17). Not re-run | closed (disclosed) |
| **The registered REML ICCs** | The registered components model omits persona × path, so its "replicate" residual is 15× the replicate variance. Reported as registered, with the persona × path fit beside (addendum 17) | Phase 9's analysis plan |
| **"S_directive's interval covers 0"** | Fails by construction: a share is a sum of importances clipped at 0. Reported as registered (addendum 18) | the team, if a directive-null test is wanted |
| **L3's spend** | The probe records no tokens, so its cost is unknown | Phase 9's tooling |
