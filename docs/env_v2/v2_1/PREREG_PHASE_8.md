# Pre-registration — Phase 8 of the v2.1 improvement plan (harness and statistics)

**Written 10 September 2026, before any correction is measured and before any paid call.** Plan Section 12
(E8.1–E8.5), Section 17 (D2, D11, D12), Appendix A; register Section 16 (the LLM sensitivity grid, which is sized
from E8.5); weaknesses 28, 34 (the harness constants), 55, 57, 59, 60 (placebo matching), 67 (salience bootstrap
intervals, random slopes).

Every rule below is in final form. A rule that later proves wrong is recorded in `PREREG_PHASE_8_ADDENDUM.md` with
the disconfirmation stated as loudly as any confirmation, and the result reported under both readings.

**What was looked at before this was written, so that nothing below is mistaken for a blind rule.** The code of
every module this phase changes; the pilot's logged stateful columns (the day-1/20/21/200 values of
`Context_Tokens`, `Mandate_Offset_Tokens`, `Context_Turns` and the parse statuses of the three `stateful_memory`
runs); the pilot's paired memory − static differences at θ = 0.05, half-width 0.10 (n = 9 pairs, used for D12's
question and quoted in P8-1); the rendered prompt sizes of the current harness (o200k tokens); the size of the
format instructions (1,636 characters, 435 o200k tokens); and the rendered texts of the three mandates and the
directive placebo, which are constants in `agent/v2_prompts.py` and `agent/personas/mbti_profiles.json`. **No
corrected covariate, no simulated size or power, no placebo count, no salience share and no variance component has
been computed.**

---

## 0. The state this phase measures, and the decisions that govern it

The frozen Phase-7 state: the freeze manifest of 30 files (`tests/v2_freeze_manifest.json`), the 95-configuration
path-hash fixture unchanged since Phase 5 (`path_hashes_phase7_after.json`), the scoring file
`evaluation/params/scoring.json` read through `evaluation/scoring_params.py` (θ co-primary: θ_info = 0.05,
θ_cost = 0.0020; scoring A, MCR = B + D). **This phase changes no path and no scoring**: `envs/`,
`evaluation/scoring.py`, `evaluation/scoring_params.py`, `evaluation/metrics_v2.py`, `evaluation/targets.py` and
`evaluation/params/scoring.json` are read, never edited. The test-tree baseline is Phase 7's second run: 191 passed,
1 skipped, 4 strict xfails, 0 failed (`e7_tests_full2.log`).

Team decisions recorded on **10 September 2026** (DECISION_LOG P8-1 … P8-3), before any experiment ran:

| decision | recorded | consequence |
|---|---|---|
| **D12** | **Δ = 0.05 band-MAS**, sized on the 90 % upper confidence limit of σ_d, at seed-level pairing, at the Bonferroni α within the contrast's question family; Appendix A as written with the paired-correct n beside; achieved power reported if the design falls short; Cliff's δ reported, sizes nothing | section 5.5 |
| **D on its own** | **no stipulated Δ_D**; the minimum detectable D difference at the band-MAS-sized design is reported, at both co-primary θ, with B and D's variance components separate | section 5.5 |
| **D2 (Phase 8's spend)** | **E8.5 on Gemini 2.5 Flash (576 runs) + a GPT-5 mini variance-transfer check (144 runs) + Phase 6's L3 probe as registered**, ≈ $139 at the plan's per-run prices, one approval, behind the cost gate of section 5.3 | sections 5.1–5.3, 5.7 |

**D11 is not asked yet**: it is answered by E8.4's identification table (section 4), and put to the team with the
collinearity shown. **D3, D5, D15 and everything Phase 9 decides are not pre-empted.** D17 = restrict the claim
(P7-1) governs what the power analysis sizes: the arm contrasts of a one-shot mandate-conflict benchmark.

---

## 1. E8.1 — the stateful arm corrections

### 1.1 The switch

`StatefulV2Agent(..., harness="v2")` is the default and is the code that produced the pilot's three stateful runs;
`harness="v2_1"` applies 1.2–1.5. `RunConfig.harness_version` (default `"v2"`) passes it through the runner. Under
`"v2"` the messages sent, the retained history and the logged dictionary are identical, bit for bit, to the
pre-Phase-8 code — proved against a golden record captured from the unmodified code **before** the first edit
(section 7).

### 1.2 The mandate-offset covariate (weakness 57, E8.1(a))

The generation point is the end of the last message sent. A **copy** of the mandate is a span of the context that
the model can attend to and that carries the persona's mandate text:

* the **system copy** — `CORE MANDATE.\n<mandate text>` in the system prompt (every stateful arm, Path B);
* the **injected copy** — the rendered mandate block in the **current** human turn (memory arms only);
* under `"v2"` only, the copies replayed inside retained history turns (removed by 1.3 under `"v2_1"`).

Logged under `"v2_1"`, each in tokens from the end of the copy to the generation point:

| column | definition |
|---|---|
| `Mandate_Offset_System` | offset of the system copy |
| `Mandate_Offset_Injected` | offset of the injected copy in the current turn; empty when the arm injects nothing |
| **`Mandate_Offset_Tokens`** | **primary: the offset of the nearest copy** = min of the two above over the copies present |
| `Mandate_Copies_In_Context` | the number of mandate copies in the context sent |
| `Offset_Count_Method` | how the offsets were counted (1.5) |

`Mandate_Offset_Tokens` keeps its column name and changes its meaning only under `"v2_1"`, which is why the
harness version is a logged column. **The primary covariate of the decay thesis is the nearest copy**, because a
covariate that measures distance to a copy the model does not need is not a covariate of forgetting. The system-copy
offset is the secondary covariate, reported beside every use of the primary.

### 1.3 Token-budget parity (weakness 57, E8.1(b))

Under `"v2_1"` a retained history turn stores the human message **rendered with an empty mandate block** — the
block is rendered into the current turn only — and the model's own reply as returned.

**Parity criterion (exact, no tolerance).** With an identical deterministic fake LLM, for every context mode
(`rolling` at each window, `full`, `summary`) and at every step: the retained history of `stateful_*_memory` is
**byte-identical** to that of `stateful_*_static`, and the two contexts sent differ only in the current human turn,
by exactly the characters of the rendered mandate block. `test_context_budget_parity` asserts this; the same test
asserts that under `"v2"` the difference grows with the number of retained turns (the defect, documented).
`test_stateful_no_duplicate_mandate` asserts `Mandate_Copies_In_Context` ≤ 2 under `"v2_1"` at a full window (the
system copy and the injected copy) and that it was `window + 2` under `"v2"`.

### 1.4 Parse fallbacks (weakness 57, E8.1(c))

Under `"v2_1"` a fallback stores the human turn (without the block) and the reply text **`no valid answer`**, never
the fabricated decision. `test_fallback_not_in_history` forces a fallback with a fake LLM that returns unparseable
text and asserts that no retained turn contains the fabricated `TargetAllocation` JSON. The defect is latent (0
fallbacks in the pilot's three runs), so this test is the only thing that keeps it fixed.

### 1.5 Token counting (weakness 34, E8.1(d))

A hierarchy, applied per quantity and labelled per row:

1. **`Context_Tokens`**: the provider's `usage_metadata.input_tokens` when the call returns it; else the tokenizer
   count; else `chars/4`. Label in `Token_Count_Method` ∈ {`provider`, `tokenizer:o200k_base`, `chars4`}.
2. **Offsets**: the provider reports no span positions, so offsets are counted with the tokenizer
   (`tiktoken` `o200k_base`) on the exact text after the copy, and — when the provider count of the whole context
   is available — **scaled into provider units** by `provider_total / tokenizer_total` of the same context. Label in
   `Offset_Count_Method` ∈ {`tokenizer:o200k_base*provider_scale`, `tokenizer:o200k_base`, `chars4`}. `chars/4` is a
   last resort, used only if the tokenizer cannot be loaded, and labelled.
3. `Context_Tokens_Tokenizer` is logged beside `Context_Tokens` so that any grid can re-express every row in one
   unit. **A covariate computed three ways across a grid is not one covariate**: the analysis of the decay thesis
   uses the provider-scaled offset where every row has it and reports the share of rows that do not.
4. Under `"v2_1"` the `full` mode's budget is counted with the tokenizer, not `chars/4`.

For Gemini the o200k tokenizer is a proxy whose unit the provider scale corrects; the ratio is logged per row
(`Token_Scale`), so its stability is itself a reported number.

### 1.6 Placebo matching, tested on the rendered texts (weakness 60, E8.1(e))

For each persona P ∈ {ISFJ, INTJ, ENTJ} at the grid's wording (`rewritten`), the **real block** is
`mandate_block("mandate", P)` and the **placebo block** is `mandate_block("placebo_directive", P)`, both as rendered.

**Word rule.** Words are the matches of `[A-Za-z][A-Za-z'\-]*` over the whole rendered block (wrapper and delimiter
lines included, identically for both). Criterion: |words(placebo) − words(real)| / words(real) ≤ 0.10.

**Clause rule.** Delete the delimiter line `*** ACTIVE MEMORY REFRESH ***`; replace `—` by `. `; split on
whitespace that follows `.`, `!`, `?` or `:`, and on newlines; strip; drop empty segments; for a segment that starts
with `If ` and contains a comma, the clause is the text after the first comma (the conditional's main clause).

**Imperative labels — a registered human annotation**, because no part-of-speech tagger is installed (no `nltk`, no
`spaCy`) and a closed-class heuristic mislabels declaratives such as "Standard disclosures apply". The test
segments the rendered text with the clause rule and asserts that the clause list **equals** the annotated list
(so any change to a text fails loudly), then counts the annotated imperatives:

| block | clauses (I = imperative, N = not) | imperatives |
|---|---|---|
| wrapper (mandate) | "Strictly adhere to your core mandate" I · … · "Evaluate this trade ONLY through the lens of this mandate" I | 2 |
| ENTJ text | "REMINDER" N · "You are a MOMENTUM COMMANDER" N · "Your goal is GROWTH" N · "Be decisive" I · "BUY" I · "SELL" I · "Do not hesitate" I · "Ignore small losses" I · "CHASE THE BIG WINS" I | 6 → block **8** |
| ISFJ text | "REMINDER" N · "You are a GUARDIAN INVESTOR" N · "Your goal is SECURITY" N · "Protect the principal" I · "Avoid volatility" I · "Keep a large cash cushion instead of insurance products" I · "Do not take unnecessary risks" I · "SLEEP WELL AT NIGHT" I | 5 → block **7** |
| INTJ text | "REMINDER" N · "You are a SYSTEM ARCHITECT" N · "Your goal is ALPHA" N · "Trust the model" I · "Ignore the news cycle" I · "Plan the exit before the entry" I · "The market is a puzzle" N · "SOLVE IT" I | 4 → block **6** |
| wrapper (placebo) | "Strictly adhere to your core procedure" I · … · "Write this decision ONLY in the manner of this procedure" I | 2 |
| placebo text | "REMINDER" N · "You are a DILIGENT RECORD-KEEPER" N · "Your goal is CLARITY" N · "Write your rationale in full sentences" I · "State the date first" I · "Use plain language" I · "Do not use abbreviations" I · "KEEP IT CLEAR" I | 5 → block **7** |

Criterion: imperatives(placebo block) = imperatives(real block). **On this annotation the v2 placebo matches ISFJ
only (7 = 7) and misses ENTJ (7 vs 8) and INTJ (7 vs 6); the word criterion is at risk for INTJ, whose block is the
shortest (290 characters against the placebo's 317).** That is stated here because the texts were read; the test is
what records it.

**The matched placebo, behind `placebo_version="v2_1"`** (default `"v2"`, the pilot's text). Construction, fixed
now and applied once: start from the v2 placebo text; while the placebo block has more imperatives than the persona's
real block, remove clauses in the order "Use plain language.", "State the date first."; while it has fewer, append
clauses in the order "Check your spelling.", "Number your points.", "Avoid jargon." Every added clause is about the
form of the written rationale and says nothing about allocation. The word criterion is then **tested on the result
and reported whatever it says**; no further editing is done to make it pass. `test_placebo_matching` asserts the
annotation, the v2 outcome as measured (the defect documented) and the v2_1 outcome.

Phase 7's measurement (`e7_7/placebo_length.json`: ratio 1.005 chars, 0.964 words, 0.981 tokens; n = 9 and 11) is the
starting point; the per-persona rule above replaces a pooled mean that hid the per-persona mismatch.

### 1.7 Before/after on the pilot's logged context

The pilot cannot be re-run (P7-8). What its logs determine exactly, per stateful run at days 1, 2, 20, 21 and 200:

* the v2 offset as logged (`chars/4` from the system copy's end);
* the v2_1 **system-copy** offset in the same unit = logged offset − `Context_Turns` × len(block) / 4 (the replayed
  copies removed; exact arithmetic on logged columns and the block text in `meta.json`);
* the v2_1 **nearest-copy** offset = the count of `"\n\n" + format_instructions` after the injected block, in
  `chars/4` (for comparability with the logged unit) and in o200k tokens;
* the retained mandate copies, v2 (`Context_Turns` + 2) against v2_1 (2);
* the context tokens as logged against the logged value minus the replayed blocks' tokens.

Reported as the phase's first number. Expectation stated in section 8.

---

## 2. E8.2 — context length as a factor (weakness 28)

**Levels, pre-registered as a factor of the decay thesis:** rolling window ∈ {5, 20, 50} and `full`.

| level | arms | exists |
|---|---|---|
| 5 | `stateful_r5_static`, `stateful_r5_memory` | yes (also the summary arm's matched control) |
| 20 | `stateful_static`, `stateful_memory` | yes |
| **50** | **`stateful_w50_static`, `stateful_w50_memory`** | **added in this phase** |
| full | `stateful_full_static`, `stateful_full_memory` (budget 60,000 tokens) | yes |

The summary arm keeps `summary_every` = 10 and `summary_raw_turns` = 5 against its rolling-5 control. The window
default (20), the budget (60,000), the cadence (10) and the raw-turn count (5) are **DESIGN** in the harness
parameter file, each with this factor or its matched control as its sensitivity.

**Cost of the {50, full} levels, for Phase 9's grid**, computed from the pilot's **measured** growth, not an
estimate: the tokens added per retained turn = (`Context_Tokens` on day 21 − day 1) / 20, averaged over the three
stateful runs, in the provider's unit; under `"v2_1"` less the replayed block's tokens (1.3). Per run: input tokens
= Σ_t (day-1 context + min(t − 1, W) × per-turn tokens) for a window W; for `full`, the retained turns are capped by
the budget. Output tokens per call from E8.5's measured usage. Prices: Gemini 2.5 Flash $0.30 / $2.50 per M
input/output, GPT-5 mini $0.25 / $2.00 (plan 0.4, read 26–27 Aug 2026; not re-read in this phase; no caching
discount applied). Stated per run and for a Tier-A-shaped cell block (3 personas × 2 arms × 3 scenarios × 5 seeds ×
1 replicate) per level, in calls and dollars.

---

## 3. E8.3 — the statistics (weakness 59, 67)

### 3.1 Unit of analysis

A **run** is (model, persona, arm, scenario cell, seed, replicate). A **path** is (scenario cell, seed): the
environment does not depend on the persona or the arm, so a path is shared by every persona, arm and model and is
**crossed** with all three. A **pair** for an arm contrast is (model, persona, path): the replicate-mean of the arm
minus the replicate-mean of its reference. Replicates are exchangeable, so they are averaged before pairing, never
paired by index.

### 3.2 The mixed model, written out

For metric y, with arms coded against the contrast's reference:

y(m, p, a, c, s, r) = β₀ + β_a + β_p + β_c + β_{a×p} + β_{a×c} + β_{p×c} + β_{a×p×c}
 + u_m + v_{m,a} + w_{c,s} + x_{c,s,a} + ε

| term | distribution | meaning |
|---|---|---|
| u_m | N(0, σ²_M) | model intercept |
| v_{m,a} | N(0, σ²_{M×A}) | **model × arm: the random slope for arm by model**, in the interaction-variance parameterisation (one variance shared across arm levels, independent of u_m) |
| w_{c,s} | N(0, σ²_P) | path intercept, crossed with model, persona and arm |
| x_{c,s,a} | N(0, σ²_{P×A}) | path × arm (the seed-specific arm effect); included only where a cell has ≥ 2 replicates, otherwise absorbed into ε |
| ε | N(0, σ²_ε) | replicate (decode) noise |

statsmodels 0.14.6:

```python
smf.mixedlm("y ~ C(Arm, Treatment(ref)) * C(Persona) * C(Scenario)", d, groups=np.ones(len(d)),
            re_formula="0", vc_formula={"model": "0 + C(Model)", "model_arm": "0 + C(Model):C(Arm)",
                                        "path": "0 + C(Path)", "path_arm": "0 + C(Path):C(Arm)"})
.fit(reml=True)
```

**Limitation stated now:** statsmodels' variance-component path estimates no intercept–slope correlation; Barr et
al.'s maximal structure would. The simulation (3.8) plants a correlation and measures what its omission does to size.
Every fit reports the variance components (`vcomp`, the residual `scale`), the number of components at the zero
boundary, and the convergence flag; a non-converged fit is reported as such, never replaced silently.

### 3.3 Intervals

Every contrast interval is a **two-way cluster bootstrap by model and path** ("pigeonhole"): in each of B = 1,999
resamples, draw the models with replacement and, independently, the paths with replacement within each scenario
cell; weight every pair by (its model's draw count × its path's draw count); the statistic is the weighted mean
paired difference (and, reported beside, the weighted Cliff's δ); the interval is percentile. With one model the
model dimension is degenerate and the bootstrap is one-way by path, and it says so.

### 3.4 The family, and its size

**Metric tiers, set with Phase 7's correlation matrix open** (`e7_8/matrix.json`, scoring A, half-width 0.10):
|r|(B, band-MAS) = 0.996, |r|(MCR, band-MAS) = 0.976, |r|(MCR, B) = 0.978, |r|(D, band-MAS) = 0.069,
|r|(D, MCR) = 0.267.

| tier | metrics | tested? | why |
|---|---|---|---|
| **C, confirmatory** | band-MAS; D at θ_info = 0.05; D at θ_cost = 0.0020 | yes | band-MAS is D12's unit; D is the term nearly orthogonal to band adherence; θ is co-primary (P7-4), so D enters at both |
| **S, secondary** | turnover; MDD %; return % | yes, as their own families | behaviour and outcome, not mandate adherence |
| descriptive | MCR and B at both θ; point-MAS; RG; the per-window variants | intervals only | B is band-MAS on resolvable steps (r 0.996) and MCR = B + D (r 0.976 with band-MAS): testing them beside band-MAS is testing one quantity two or three times. point-MAS and RG are not in Phase 7's matrix, so their redundancy is unmeasured and they are not given a test they may duplicate |

**Question families (contrasts within persona × scenario cell):**

| family | question | contrasts (arm − reference) |
|---|---|---|
| Q1 | does re-injecting the mandate change adherence? | memory − static; path_b_memory − path_b_static |
| Q2 | is it the mandate's content? | memory − placebo_directive; swapped − memory |
| Q3 | does the form alone move it? | placebo_directive − static; placebo_declarative − static; wrapper_only − static |
| Q4 | does placement in the system prompt? | path_b_static − static |
| Q5 | does context length change it? | per window level L: stateful_L_memory − stateful_L_static; stateful_L_memory − memory |

A family F = (question, tier). **Its size is computed from the grid actually run, never typed**:
m(F) = (contrasts of the question present in the grid) × (personas) × (scenario cells) × (metrics of the tier).
`tools/stats_v2.family_table(per_run)` returns every family with its m and the total; `test_bh_family_size_logged`
asserts that the count is written beside every q-value. The reviewer's "≈ 840" is re-derived by the same function on
the v2 construction (7 metrics × every non-reference arm × personas × scenario cells) and reported, with the grid it
assumes stated.

### 3.5 Multiplicity

BH at q = 0.05 **within each family**; **Benjamini–Yekutieli across all confirmatory families** as the conservative
report (and, separately, across all secondary families). Both q-values are in every table with m(F) and the total.

### 3.6 The temporal null (the circular shift replaced)

The v2 null shifts eight 25-day window means per run, so a run has at most eight distinct rotations. Candidates:

* **N0** (v2): circular shift of window means;
* **N1**: permutation of the eight window means (8! orderings);
* **N2**: day-level block permutation — blocks of 25 days with a random circular offset in [0, 24], blocks permuted
  (8! × 25 arrangements per run);
* **N3 (kept)**: the paired sign-flip of the trend difference (stateful − stateless on the same model, persona and
  path), with the sign flipped at the **path** level (all replicates of a path share one sign).

A null is used for a real contrast only if it holds size in 3.8 at the persistence the pilot's own series show.

### 3.7 What is kept

`paired_sign_flip`, `cliffs_delta`, `hedges_g`, `bh_adjust` and the v2 functions stay; the re-specification is new
functions beside them (section 7).

### 3.8 Validation on simulated data with known answers — before any real contrast

**(a) The mixed model and the intervals.** Data-generating process: 2 arms (static, memory), 3 personas, 2 scenario
cells, models M ∈ {3, 6}, paths S ∈ {5, 10} per cell, replicates R = 1 (plus one condition at M = 6, S = 5, R = 3).
The path effect w is **real**: the per-(scenario, seed, persona) band-MAS of the level-free observables oracle in
`e7_rescore/cells.parquet` at θ = 0.05 and half-width 0.10, centred within scenario × persona and resampled by seed.
Planted: σ_M = 0.05, σ_{M×A} ∈ {0, 0.03}, σ_ε = 0.03 (DESIGN values for the simulation, on the pilot's σ_d scale; a
registered second pass repeats the size check at E8.5's measured components), intercept–slope correlation 0 and 0.5
in the σ_{M×A} = 0.03 conditions, arm effect β ∈ {0 (size), 0.05 (power)}. 300 datasets per condition.

Estimators: **E0** the v2 `mixed_effects` (seeds nested in models, intercepts only); **E1** section 3.2; **E2** the
two-way cluster bootstrap (3.3); **E3** the v2 run-level `bootstrap_ci`. Reported per condition: rejection rate of
β = 0 at α = 0.05 with its Wilson 95 % interval (size at β = 0, power at β = 0.05), interval coverage of the planted
β, the median estimated variance components against the planted, and the share of fits at the zero boundary.

**Adoption rule.** An estimator is used for real contrasts only if the Wilson interval of its simulated size at the
condition nearest the real design contains 0.05 or lies below it. If none does, the contrast is reported with the
estimator that comes closest, labelled with its simulated size — not presented as holding size.

`test_mixed_model_crossed`: on a large simulated design (M = 12, S = 20) E1 recovers each planted component inside
the 5th–95th percentile band of E1's estimates across that condition's simulation (read from `e8_3/`, derived, not
typed), and E0 has no model × arm component by construction.

**(b) Multiplicity.** Test statistics z ~ N(μ, Σ) per contrast cell with Σ over tier C from the correlations measured
on `e7_rescore/cells.parquet` at half-width 0.10 with the construction of `e7_8/matrix.json` (band-MAS, D at 0.05,
D at 0.0020); families of the sizes 3.4 gives for the E8.5 grid and for the reviewer's grid; non-null share
π₁ ∈ {0, 0.1, 0.3} at a shift of 3; 5,000 replications. Reported: FDR and power for (i) the v2 procedure (BH across
metrics within a contrast), (ii) BH within family, (iii) BY across. Adopted if (ii)'s FDR ≤ 0.05 + its Monte-Carlo
half-width.

**(c) The temporal null.** Per-run daily series: AR(1) with no trend at φ ∈ {0.90, 0.97, 0.99} and φ_pilot = the
median lag-1 autocorrelation of daily `Cash_Share` over the pilot's 36 main T = 200 runs; n_runs ∈ {3, 36};
N0–N3 at 999 draws; 1,000 replications; size with Wilson intervals. Same adoption rule, at φ_pilot.

---

## 4. E8.4 — salience shares (weakness 55, 67)

**Identification condition.** Build the surrogate's block design on the runs to be analysed — P (persona one-hot), D
(directive one-hot, as `evaluation/salience._design` builds it) and S (the start cash share) — each column-centred.
The shares are **identified** only if (i) every block has rank ≥ 1, (ii)
rank([P, D, S]) = rank(P) + rank(D) + rank(S) (no block in the span of the others), (iii) `Start_Design` is `common`
for every run, and (iv) the reference levels are present: at least one run with no persona text (`NONE`, `TRADER`,
`O3_conservative`, `O3_aggressive`) and at least one in which the directive's persona differs from the run's
persona or no directive is shown. Under start-at-target S = centre(P), so (ii) fails by construction; that rank
deficit, the R² of each block regressed on the others, and the canonical correlations are **shown** in the report as
a table, not described.

`salience_by_window(..., identification="v2")` is the default and unchanged; `identification="v2_1"` evaluates the
condition and returns `NOT IDENTIFIED` rows with the failing clause instead of shares; when identified it adds a
**cluster bootstrap by seed** (B = 200 refits) percentile interval to every share. `test_salience_common_start_only`
asserts both.

**Known-answer check.** Synthetic runs with c* = persona effect + market effect + noise and **no directive effect**:
(a) start-at-target, arms static and memory (the pilot's design); (b) common start with static, memory, swapped, and
the NONE and O3 references. Reported: the condition's verdict for each; the shares over 10 surrogate seeds (their
spread under (a) is the non-identification made visible); under (b) whether S_directive's bootstrap interval covers
0 and S_persona's excludes it.

**D11 is then asked with the table**: common-start only, with the reference levels in the main grid, or the measure
dropped from the headline set and kept exploratory. The pilot's nine common-start runs (static only, MBTI personas
only) are expected to fail (iv).

---

## 5. E8.5 — the variance pilot and the power analysis that sizes the main grid

### 5.1 Design (fixed; the design does not move after the first batch)

| factor | levels |
|---|---|
| model | `gemini-2.5-flash` |
| persona | ISFJ, INTJ, ENTJ |
| arm | static, memory |
| scenario | flat, bull_trap, crash (δ = 0.70), sustained_bull |
| seed | **2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008** |
| decode replicate | 0, 1, 2 |

= 576 runs, T = 200, 115,200 decision calls. Every other setting is the harness default of `experiments/arms_v2.py`
`FACTOR_DEFAULTS` (track B, wording `rewritten`, start at target, target interface, cost 5 bp hidden, same-day
execution, horizon undisclosed, canonical field order, setup-first ordering, temperature 0.2, no probe), engine
`ar1_fit` (the generator default), **dividends paid** (D10 = pay, P7-2; the main grid pays them, so the pilot that
sizes it does), stateless harness. Scored with `metrics_v2.score_run(scoring="v2_1")` at the θ in force.

**Transfer check** (P8-3): `gpt-5-mini`, bull_trap only, the same personas, arms, seeds and replicates = 144 runs,
28,800 calls. If the provider rejects temperature 0.2, the check runs at the only temperature it accepts, the value
is logged in `Temperature`, and the transfer ratio is reported as a transfer of **model and temperature together** —
not as a model transfer.

### 5.2 Execution: resumable per run, checkpointed, contamination-safe

`tools/phase8/e8_5_variance_pilot.py`, stages `dry-run` → `smoke` → `run` → `transfer` → `analyse`, each its own
files under `docs/env_v2/generated/v2_1/e8_5/`. A run is checkpointed only after its CSV, `meta.json` and a usage
record (billed input and output tokens per call, from `UsageMetadataCallbackHandler`) are written. On resume the tool
re-computes `Prompt_Hash` for every (persona, arm) and `Env_Code_Hash`, and **refuses to resume** if either differs
from the launch manifest. The LLM client retries transient provider errors with backoff before the agent's own three
attempts. **Contamination rule:** a run containing a fallback whose recorded error is not a parse error
(`OutputParserException`, `ValidationError`, `JSONDecodeError`) is discarded, logged in the manifest with the error
class, and re-run (at most twice); parse fallbacks are the model's behaviour, are kept, and their share is reported.

### 5.3 Price and the cost gate

At the plan's per-run prices: Flash 576 × $0.18 ≈ $104, GPT-5 mini 144 × $0.15 ≈ $22, L3 ≈ $12; ≈ $139. The measured
prompt is ≈ 1,750 o200k tokens per stateless call (≈ 0.35 M input per run). The plan's price assumes 120 output
tokens per call; **thinking tokens bill at the output rate and have not been measured.** Gate: the first two design
runs on Flash (ISFJ static and memory, bull_trap, seed 2001, replicate 0) and the same two cells on GPT-5 mini run
first; their billed usage × the prices gives the projected total for all 720 runs. **If it exceeds $174 (125 % of
the approval), the batch stops and the team is asked**; thinking settings are not changed to fit the price (that
would change the model the pilot measures).

### 5.4 Variance components and ICCs

Metrics: band-MAS; B, D and MCR at θ = 0.05 and at θ = 0.0020; turnover. For each:

1. REML fit of y ~ C(Arm) * C(Persona) * C(Scenario) with vc {path, path × arm}, residual = replicate: σ²_P,
   σ²_{P×A}, σ²_ε, and ICC_path = σ²_P / (σ²_P + σ²_{P×A} + σ²_ε), ICC_{path×arm} likewise.
2. Model-free, the plug-in quantities: d(p, c, s) = replicate-mean(memory) − replicate-mean(static);
   σ_d(3) = the residual sd of d after persona × scenario means (df = 96 − 12 = 84); σ²_rep = the pooled
   within-(persona, arm, scenario, seed) replicate variance (df = 576 − 192 = 384);
   σ²_int = max(0, σ²_d(3) − 2σ²_rep / 3); the projection σ²_d(R′) = σ²_int + 2σ²_rep / R′ for R′ ∈ {1, 2, 3}.
3. **B and D are reported in separate rows**, never only through MCR.

### 5.5 The power rule (D12, P8-1, P8-2)

* **Plug-in:** σ_UCL(R′) = the one-sided 90 % upper limit of σ_d(R′), percentile cluster bootstrap over paths
  (resampling the 32 paths within scenario, 2,000 resamples); the χ² limit of σ_d(3) on 84 df beside. Sensitivity at
  the 80 % and 95 % limits.
* **α:** α′ = 0.05 / m(Q1, C) for the grid being sized (for the E8.5 cell structure: 1 contrast × 3 personas × 4
  scenario cells × 3 tier-C metrics = 36); the nominal α = 0.05 row beside.
* **Seeds per persona × scenario cell:** n = ⌈2 (z_{1−α′/2} + z_{0.80})² σ²_UCL(R′) / Δ²⌉ with Δ = 0.05 on
  band-MAS (Appendix A as written); the paired-correct n = ⌈(z_{1−α′/2} + z_{0.80})² σ²_UCL(R′) / Δ²⌉ beside,
  flagged as an amendment. Runs per contrast cell = 2 × n × R′.
* **The minimum detectable difference** MDD = √2 (z_{1−α′/2} + z_{0.80}) σ_UCL(R′) / √n for band-MAS, B, D (both θ),
  MCR (both θ) and turnover, at: E8.5's own design (n = 8, R′ = 3); Phase 9's Tier A (n = 5, R′ = 1); and the
  band-MAS-sized design. **D's row at the band-MAS-sized design is P8-2's "achieved power"**, stated in D's units.
* **Replicates against seeds:** at equal cost per run the variance of the mean contrast per unit cost is
  σ²_int·R′ + 2σ²_rep, which is minimised at R′ = 1 whenever σ²_int > 0; the table reports it rather than asserting it.
* **Models:** the between-model sd is not estimable from one model (and one df from two). The model count is set by
  the roster (D2); model-level power is tabulated for M ∈ {2, 3, 5, 8} at a between-model sd of {0.5, 1, 2} × σ_UCL,
  labelled DESIGN.
* **If the affordable design falls short, the achieved power is reported and Δ does not move.**
* **The register's stateful-inclusion rule** (REG-16 (ii)) needs the stateful contrasts' σ_d; E8.5 is stateless, so
  it is reported as not measured here.

### 5.6 The transfer check

σ_d(bull_trap) for each model (24 seed-level pairs, df 21), the ratio r = σ_GPT-5-mini / σ_Flash with a 90 %
cluster-bootstrap interval over paths. The main grid's plug-in is σ_UCL(Flash, pooled) × max(1, r̂); the plug-in at
r's upper limit is reported beside.

### 5.7 L3

Phase 6's probe runs exactly as registered in `PREREG_PHASE_6.md` section 9 (roster, 200 probes, two arms, the
entitled-reader rule). It is Phase 6's result, reported in Phase 8's report under its own heading.

---

## 6. Parameter files (P6-12, P4-45)

* **`agent/params/harness.json`** with the loud loader **`agent/harness_params.py`**: the context window default and
  the factor levels, the token budget, the summary cadence, the summary raw-turn count, the summary word cap and its
  1,200-character truncation, the 160-character step truncation inside the summariser prompt, the token-count
  hierarchy, the offset definition, the history rule, the fallback text, the placebo matching outcome, the decode
  temperature and the parse-retry count — each with `value`, `status`, `label`, `source`, `date`, `interval`, `n`
  and a declared `_status_key`. Written by `tools/phase8/e8_write_params.py` from result files; read back before any
  table under it.
* **`experiments/params/inference.json`** with **`experiments/inference_params.py`**: D12, the plug-in rule, the
  pairing unit, the α rule, the power, the family definition, the multiplicity procedure, the adopted temporal null,
  the bootstrap specification, the mixed-model formula, E8.5's design, the transfer rule and the cost gate.

Status vocabulary: DERIVED, MEASURED, REGISTERED, DESIGN, TEAM (a decision recorded in DECISION_LOG), READ.

---

## 7. The switch list — every change with the current behaviour behind it, proved inert when off

| switch | default (= current behaviour) | new behaviour | inertness test |
|---|---|---|---|
| `StatefulV2Agent(harness=)` / `RunConfig.harness_version` | `"v2"` | 1.2–1.5 | messages, history and `context_log()` identical to a golden record captured from the unmodified code, for rolling/full/summary × static/memory × a forced fallback |
| `v2_prompts.mandate_block(..., placebo_version=)` / `RunConfig.placebo_version` | `"v2"` | the per-persona matched placebo | every block and `Prompt_Hash` of every existing arm identical to the golden record |
| `experiments/arms_v2.ARMS` | the existing 18 arms | + `stateful_w50_static`, `stateful_w50_memory` | `build_config` of every pre-existing arm identical to the golden record |
| `tools/stats_v2` | `run_stats`, `mixed_effects`, `bootstrap_ci`, `windowed_trend_vs_null(null="circular")` unchanged | new functions beside them | `run_stats` on the existing synthetic table identical to the golden record |
| `evaluation/salience.salience_by_window(identification=)` | `"v2"` | the identification check and the bootstrap | the v2 output identical on a fixed synthetic frame |
| `agent/params/harness.json` | absent ⇒ the constructor defaults | the loader serves the same values | the values equal the constructor defaults |

The golden record is written **before the first edit** by `tools/phase8/e8_0_golden.py` into `tests/phase8_golden.json`.
**The path-hash fixture is not a switch**: the 95 configurations must be byte-identical at the end
(`tools/path_hashes.py --compare`).

---

## 8. Stated expectations (so that disconfirmation is visible)

1. **The memory arm's nearest-copy offset is the format instructions plus a separator: ≈ 410 in `chars/4`, ≈ 435
   o200k tokens, constant from day 1 to day 200** — against 15,261 / 15,909 / 16,546 logged at day 200. The error is
   ≈ 35×, not the "≈ 77 tokens away" of the execution prompt, which is the block's own size, not the distance.
2. The system-copy offset under v2_1 is below the logged value by the replayed blocks (≈ 20 × 311 characters at a full
   window, ≈ 1,555 in `chars/4`, ≈ 10 %).
3. Placebo: the imperative criterion holds for ISFJ only under v2; the word criterion may fail for INTJ; the matched
   v2_1 placebo meets the imperative criterion by construction and the word criterion is an open measurement.
4. At a 60,000-token budget the `full` level retains ≈ 65 turns, so the {50, full} levels nearly coincide; this is a
   DESIGN finding for the team, not something this phase changes.
5. E0 (the v2 model) over-rejects when σ_{M×A} > 0; E1's model components sit at the zero boundary often at M = 3;
   E3 (the run bootstrap) under-covers; E2 is closest to nominal.
6. N0–N2 over-reject at the pilot's persistence; only N3, the path-level sign-flip, holds size.
7. Under start-at-target the rank deficit is ≥ 1; the pilot's common-start runs fail condition (iv).
8. E8.5: σ_d(D) < σ_d(band-MAS); R′ = 1 is the efficient replicate count; at Δ = 0.05 with the 90 % limit and the
   Bonferroni α the band-MAS-sized design needs more seeds per cell than Tier A's 5.
9. **At least one rule here will be undecidable or come out the wrong way.** Eight phases in a row have had one.

---

## 9. What this phase does not do

- It does not touch `envs/`, `evaluation/scoring.py`, `scoring_params.py`, `metrics_v2.py`, `targets.py` or
  `params/scoring.json`; a scoring finding goes to the report and the team.
- It does not touch the known-defect registry's two entries.
- It runs no stateful LLM call: E8.1 is verified with a deterministic fake LLM and on the pilot's logs; the corrected
  covariate on real runs arrives with the main grid.
- It does not edit the plan, `V2_1_ALTERNATIVES_REGISTER.md` or `docs/env_v2/v2_1/archive/`; amendments are recorded
  in the report.
- It does not pre-empt D3, D5, D15, D11 (until E8.4's table) or Phase 9's tier and roster.
