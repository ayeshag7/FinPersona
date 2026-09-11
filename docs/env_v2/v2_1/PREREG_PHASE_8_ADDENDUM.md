# Pre-registration addendum — Phase 8

*Every rule of `PREREG_PHASE_8.md` that proved wrong, undecidable or incomplete once data were read, and every
contingency that triggered, stated as loudly as a confirmation. Nothing registered is re-specified silently: each
item gives the rule as registered, what was measured, the reading the phase uses, and the file.*

---

## 1. Expectation 3 (placebo): the word criterion was NOT at risk for INTJ

**Registered (1.6, section 8 item 3):** "the word criterion is at risk for INTJ, whose block is the shortest (290
characters against the placebo's 317)."

**Measured:** INTJ's mandate block has **49 words, the same as the v2 placebo's 49** (relative difference 0.000). The
character count misled: INTJ's text uses more, shorter words. The word criterion holds for all three personas under
v2 (ISFJ 52 / 49, 0.058; ENTJ 52 / 49, 0.058). The imperative criterion behaved exactly as annotated: v2 matches ISFJ
only (7 = 7), misses ENTJ (8 vs 7) and INTJ (6 vs 7). The matched v2_1 placebo meets both criteria for all three
(INTJ 49 / 46, 0.061; ENTJ 52 / 52).

**Reading:** the expectation is disconfirmed; no rule changes. File: `docs/env_v2/generated/v2_1/e8_1/placebo_matching.json`.

## 2. Expectation 4 (context levels): the full level holds ~80 turns, not ~65

**Registered (section 8 item 4):** "At a 60,000-token budget the `full` level retains ≈ 65 turns, so the {50, full}
levels nearly coincide."

**Measured:** the budget counts the *history's* tokens in the harness's own unit, not the provider's context count
the expectation used. Under v2 (chars/4) it holds **80** retained turns; under v2_1 (o200k, on an actually rendered
turn) **77**. So `full` is an ~80-turn window: distinct from 50, and the v2_1 switch barely moves it.

**Two errors of this phase's own tool, corrected before any table was used and disclosed here:** the first draft of
`tools/phase8/e8_2_context_cost.py` (a) priced the summary text at a quarter of its tokens, and (b) converted
characters to o200k tokens at the rate of the English system prompt, giving 120 turns under v2_1; a retained turn is
mostly numbers and JSON (the rendered human turn is 3.2 characters per token) and the corrected count is 77.

File: `docs/env_v2/generated/v2_1/e8_2/context_cost.json`.

## 3. The registered real path effect is almost empty — an unregistered sensitivity added

**Registered (3.8(a)):** the path effect of the size/power simulation is "the per-(scenario, seed, persona) band-MAS
of the level-free observables oracle in `e7_rescore/cells.parquet` at θ = 0.05 and half-width 0.10, centred within
scenario × persona".

**Measured (stage `paths`, before any size was read):** the label check passed (`L5_full_level_free`, flat MCR 0.0770,
the published observables oracle), but the oracle almost never leaves its band, so the centred band-MAS has an sd of
**0.0003–0.0005** across seeds within scenario × persona — about **100 times below** the planted replicate sd (0.03).
The registered conditions are therefore a valid test of the model and model × arm structure but **barely exercise path
clustering**.

**Reading:** the registered conditions run and are reported as registered. An **unregistered sensitivity**
(`--stages mixed_gpath`) adds conditions with a Gaussian path intercept at sd 0.04 — the recovery design's value,
fixed before the sensitivity was run — so that the two-way bootstrap's path dimension is tested at a scale that
matters. It adds conditions; it replaces none. File: `docs/env_v2/generated/v2_1/e8_3/paths.json`, `mixed_gpath.json`.

**Result of the sensitivity (300 datasets per condition, 10 paths):** the conclusions of the registered conditions
stand. With a model × arm sd of 0.03 the crossed model and the two-way bootstrap hold size at six models (0.067,
0.060) and fail at three (0.087 each); the v2 model rejects a true null in 36–37 %; the run bootstrap fails at both
sizes (0.077, 0.080). The crossed model recovers the planted path component (median ≈ 0.002 against 0.0016).

## 4. The multiplicity simulation's first correlation used the wrong construction

**Registered (3.8(b)):** tier C's correlation "measured on `e7_rescore/cells.parquet` at half-width 0.10 with the
construction of `e7_8/matrix.json`".

**What happened:** the first run correlated the 60,000 seed-level rows and read |r|(band-MAS, D at 0.05) = **0.033**
against E7.8's **0.069** — a different statistic under the same name (P6-7, rule 13). The tool now imports E7.8's
own `_cell_frame` (a cell = scenario × persona × policy, the mean over seeds, 600 cells) and **refuses to run unless
the band-MAS–D pair reproduces `e7_8/matrix.json` to 1e-12**; it does. The superseded run's verdicts were the same in
every row (the correlations enter only through the metric blocks), and it is replaced, not averaged.

**And a fact the corrected matrix adds:** |r|(D at θ_info 0.05, D at θ_cost 0.0020) = **0.992**. Tier C, registered
as three tests per contrast cell, carries **two near-duplicates of D** — the co-primary θ of P7-4 costs a test
without adding an independent quantity. The family is kept as registered (co-primary means both are reported) and
the duplication is stated beside every count.

File: `docs/env_v2/generated/v2_1/e8_3/multiplicity.json`.

## 5. BH within family does NOT control the false-discovery rate across a multi-family grid — BY across becomes the decision rule

**Registered (3.5, 3.8(b)):** "BH at q = 0.05 within each family; Benjamini–Yekutieli across all confirmatory
families as the conservative report", with (ii) BH within "adopted if its FDR ≤ 0.05 + its Monte-Carlo half-width".

**Measured (5,000 replications; tier C's measured correlation; shift 3):**

| grid | π₁ | v2 (BH across metrics in a cell) | BH within family | BY across |
|---|---|---|---|---|
| E8.5 (one family, 36 tests) | 0 | 0.431 | **0.042** | 0.012 |
| E8.5 | 0.1 | 0.204 | 0.041 | 0.011 |
| reviewer-sized (four families, 360 tests) | 0 | 0.996 | **0.158** | 0.007 |
| reviewer-sized | 0.1 | 0.246 | **0.056** (MC half-width 0.002) | 0.007 |
| reviewer-sized | 0.3 | 0.083 | 0.037 | 0.005 |

BH within family controls the FDR *within each family* by construction, but the rule registered the overall FDR,
and on a grid of more than one family it **fails the adoption rule** at π₁ = 0 and 0.1. BY across holds in every
row (power 0.23–0.45 against 0.51–0.67 for BH within).

**Reading, as registered rules require:** on a grid with one confirmatory family (E8.5) BH within family is adopted.
On a grid with more than one, **BY across all confirmatory families is the decision rule**, and BH within family is
reported beside it as the per-question description, never as the basis of a claim. The v2 procedure is withdrawn.

## 6. The GPT-5 mini temperature contingency triggered

**Registered (5.1):** "If the provider rejects temperature 0.2, the check runs at the only temperature it accepts,
the value is logged, and the transfer ratio is reported as a transfer of model and temperature together."

**Found:** the provider is never given the chance to reject it — `langchain_openai`'s
`BaseChatOpenAI.validate_temperature` **silently removes** any temperature other than 1 for gpt-5 models, so a run
configured at 0.2 would have run at 1.0 and logged 0.2. The variance-pilot runner configures and logs GPT-5 mini at
**1.0**, and `tests/test_v2_1_phase_8.py::test_e8_5_llm_matches_factory` asserts the silent drop so that it cannot
return unnoticed. The same drop applies to Phase 6's L3 probe, which calls `make_llm(..., temperature=0.0)` for
`gpt-5-mini`; the probe's GPT-5 mini answers are at temperature 1.0 and are reported so.

## 8. The cost gate triggered: the registered design costs ≈ $594, not ≈ $139 — the batch did not start

**Registered (5.3):** "If [the projected total] exceeds $174 (125 % of the approval), the batch stops and the team is
asked; thinking settings are not changed to fit the price."

**Measured (the smoke: ISFJ static and memory, bull_trap, seed 2001, replicate 0, on each model; n = 2 runs per
model):** every run completed 200 of 200 calls; Gemini 2.5 Flash billed **$1.082 and $0.787** (mean **$0.934 per
run**) with **1,540 thinking tokens per call — 94 % of its output**; GPT-5 mini billed $0.334 and $0.281 (mean
$0.307). The plan's per-run prices ($0.18, $0.15) assumed 120 output tokens per call. **Projected total: $594.43**
(Flash 576 × $0.934 = $538.18; GPT-5 mini 144 × $0.307 = $44.25; L3 $12) against the $174 gate. **STOP, as
registered.** The two Flash runs differ by 37 %, so the projection is uncertain at that order; it is not uncertain
enough to reach the gate.

**Also found by the smoke, and not a model problem:** all four runs then failed on the runner's `meta.json` write
(P8-6), so the gate stage — which priced only `ok` runs — first recorded a NaN projection; it now prices every run
that completed its calls (their billed usage is what they cost) and still requires every smoke run to be `ok` to
pass. $2.48 was spent. The four runs' CSVs are complete; whether they enter E8.5 depends on the team's answer.

**Consequence beyond this phase:** at the measured Flash price, Phase 9's Tier A (1,170 runs) is ≈ $1,090, not the
plan's $210; the context-length levels cost $0.93 (stateless) to $4.01 (`full`) per Flash run
(`e8_2/context_cost.md`). Files: `docs/env_v2/generated/v2_1/e8_5/smoke.json`, `e8_5/ledger.jsonl`.

## 9. The design amendment the team took after the gate — registered before any batch

**The team's answer (10 Sep 2026, DECISION_LOG P8-8):** Gemini 2.5 Flash with thinking off, for E8.5 and the main
grid. Registered now, before the first batch run, and nothing else in section 5 moves:

| item | registered in 5.1–5.3 | amended |
|---|---|---|
| Flash's configuration | the provider default (thinking on; never set by `agent/llm_factory.make_llm`) | **`thinking_budget=0`** |
| GPT-5 mini (transfer) | provider default, temperature 1.0 | unchanged |
| approval / gate | $139 / $174 | **$151 / $189** (125 %, the registered rule) |
| smoke | ISFJ static and memory, bull_trap, seed 2001, replicate 0, each model | the same four runs **again**, under the amended configuration and the fixed runner — every smoke run must be `ok` to pass |
| where runs are written | `results_v2/phase8_e8_5/<model>/` | `results_v2/phase8_e8_5/<config tag>/<model>/` (`thinking0` for Flash, `default` for GPT-5 mini); the first smoke's failed files stay where they are, as the record |
| the ledger | every attempt | every attempt carries its `config_tag`; the gate and the retry counter read only the current configuration's rows |
| the first smoke's thinking-on Flash runs (n = 2) | — | **reported as a sensitivity of the configuration, never pooled** with the design's runs |

The launch manifest written under the first configuration is kept as `e8_5/manifest_thinking_default.json`; the
first gate's file as `e8_5/smoke_thinking_default.json`.

**The amended smoke passed its gate** (`e8_5/smoke.json`): all four runs `ok` under the fixed runner; Flash with
thinking off billed **$0.167 and $0.169** (0 thinking tokens, ≈ 106 output tokens per call, ≈ 4 minutes per run —
the ≈ $0.17 estimate confirmed); GPT-5 mini $0.281 and $0.330. **Projected total $153.04 against the $189 gate —
PASS** ($2 above the $151 approval and inside the registered 125 %). Spent on both smokes: $3.43.

**A gap this leaves, recorded rather than closed here:** `RunConfig` has no field for provider options, so a run's
CSV cannot say whether its model thought. E8.5 records the budget in its manifest, its usage records and its
directory; the main grid needs a logged column, and that is carried to Phase 9 (report section 7).

## 10. E8.4's identification condition, as registered, can never be met

**Registered (section 4):** identified only if "(i) every block has rank ≥ 1, (ii) rank([P, D, S]) = rank P + rank D +
rank S, (iii) `Start_Design` is `common` for every run, and (iv) the reference levels are present".

**Found when the check was first run on the pilot's designs, before any share was computed:** under a common start
every run begins at the same cash share, so the start block S is constant and its rank is 0. Clause (iii) *requires*
that, and clause (i) *forbids* it. **No design can pass the condition as registered**: the salience measure could never
be reported, whatever the grid contained. The rule is wrong, not the data.

**The reading adopted, and why it is the rule's evident intent:** clause (i) applies to the persona and directive
blocks, whose shares are what E8.4 is about; at a common start the start block is constant by design and its share is
**not applicable** (reported as such, never as 0). Section 4's own sentence — "under start-at-target S = centre(P), so
(ii) fails by construction" — only makes sense if the start block was meant to be *removed* by the common start, not
required to vary within it.

**Reported under both readings, every time:** `identification_check` returns `identified` (adopted) and
`identified_as_registered` with its failing clauses; `salience_by_window(identification="v2_1")` carries the registered
verdict on every row; the report's table shows both columns. On the pilot: the main runs fail (ii), (iii) and (iv)
under both readings (R² of the start block on the persona block **1.000**, canonical correlation **1.000**); the nine
common-start runs fail (i) and (iv) under both.

## 11. E8.3(a): no interval estimator holds size at three models when the arm effect varies by model

**Registered (3.8(a)):** "An estimator is used for real contrasts only if the Wilson interval of its simulated size at
the condition nearest the real design contains 0.05 or lies below it. If none does, the contrast is reported with the
estimator that comes closest, labelled with its simulated size." Expectation 5: E0 over-rejects, E1's model components
sit at the boundary often at M = 3, E3 under-covers, E2 is closest to nominal.

**Measured (300 datasets per condition):** with a model × arm sd of 0.03, **E0 (the v2 model) rejects a true null in
36–58 %** of datasets at every size; **E1 holds at 6 models (0.053–0.073) and not at 3 (0.077–0.100); E2 holds at 6
(0.023–0.073) and not at 3 with 10 paths (0.107–0.123)**; E3 fails wherever paths are many (0.133–0.207). With no
model × arm variance, E1–E3 are conservative (≤ 0.027) and E0 is at or over nominal. **E1's model × arm component sits
at the zero boundary in 0–3 % of fits, not "often"** — that part of expectation 5 is disconfirmed; the rest holds.

**Reading, as registered:** on a grid of six or more models E1 and E2 are adopted; **on a grid of two or three models —
Phase 9's Tier A has two — no estimator holds size**, and every interval is reported with the closest estimator's
simulated size beside it (E2 at 5 paths 0.063–0.087, at 10 paths 0.107–0.123). File: `e8_3/mixed.json`.

## 12. E8.3(c): the registered replacement null does not hold size either — only the path-level sign-flip does

**Registered (3.6, 3.8(c)):** the circular shift "replaced by a block-permutation null with enough distinct values, or
reported as exact with its eight"; a null is used only if it holds size at the pilot's persistence.

**Measured at φ_pilot = 0.9214** (the median lag-1 autocorrelation of daily cash share over the pilot's 36 main runs;
1,000 replications): N0 circular shift **0.071** (36 runs) / **0.088** (3); N1 window permutation 0.119 / 0.105; **N2
day-block permutation — the registered replacement — 0.120 / 0.124**; N3 path-level sign-flip **0.043 / 0.000**.
Expectation 6 is confirmed: every within-run permutation null over-rejects at the persistence the series have, and
"more distinct values" does not help — the defect is not the number of values but that permuting 25-day blocks of a
persistent series manufactures trends. N3 holds size and **cannot reject with fewer than six paths** (its exact floor is
2 / 2ⁿ).

**Reading:** no within-run trend statistic has a valid null in this phase; **a temporal claim rests on N3 across paths
or is not made.** File: `e8_3/null.json`.

## 13. An unregistered check added before E8.5's data are read: the power analysis on data with a known answer

**What was registered:** section 3.8 simulated E8.3's estimators; section 5.4's plug-in quantities (σ²_int, σ²_rep,
σ_d(R′)) and section 5.5's one-sided 90 % path-bootstrap upper limit were **not** given a known-answer check, although
hard rule 2 applies to them as much as to the mixed model — the main grid's seed count rests on that limit covering
the true σ_d as often as it says.

**What is added, written before any pilot run has been scored:** `tools/phase8/e8_5_validate.py` simulates E8.5's own
shape (3 personas × 2 arms × 4 scenarios × 8 seeds × 3 replicates) with a planted seed × arm variance and replicate
variance at three settings — mixed (0.03, 0.04), replicate-only (0, 0.05), seed-dominated (0.05, 0.02) — 200 datasets
each, and measures the plug-ins' bias against the truth σ_d(R′) = √(s²_int + 2 s²_rep / R′) and the coverage of the
"90 %" limit (nominal 0.90). **It adds evidence and replaces no rule**: if the limit under-covers, the measured coverage
is reported beside the power table and the rule is not re-tuned after the pilot's numbers are seen.

File: `docs/env_v2/generated/v2_1/e8_5/validate.{json,csv}` (results appended here when they land).

**How it is run, and one change made before any of its numbers were read:**

- **The first run was too slow to finish.** Written with the analysis's pandas bootstrap, it took ≈ 49 s per dataset
  and stood at 250 of 600 after 3.3 h. It was stopped there and **none of its output is used**.
- **The bootstrap is now array arithmetic.** The design is complete and balanced, so every run is one array
  (persona × arm × scenario × seed × replicate). The array form draws the seeds with the same generator calls, in
  the same order, and computes the same statistics over all resamples at once
  (`tools/phase8/e8_5_analyse.boot_plug_ins_fast`). It is **proven equal to the loop to 1e-12**
  (`tests/test_v2_1_phase_8.py::test_boot_plug_ins_fast_equals_loop`, rule 18) and falls back to the loop exactly
  on an incomplete design. It is ≈ 300× faster: 0.86 s for 2,000 resamples against ≈ 267 s. The real analysis
  uses the same function.
- **The validation now draws 2,000 resamples per dataset, not 500.** That is the count the real analysis uses
  (`N_BOOT`), so the coverage measured is the coverage of the limit actually plugged in.

## 14. L3 (Phase 6's probe, run under this phase's D2): two models rejected the registered temperature, and the tool read their rejections as passes

**Registered (`PREREG_PHASE_6.md` section 9):** 200 probes, two arms, ≥ 5 models, each called through
`agent.llm_factory.make_llm(model, temperature=0.0)`; a model passes if its normal-arm sign accuracy ≤ the level-free
surrogate's + the Wilson half-width, and its shuffled arm sits inside the null.

**What happened on the first run:**

1. **Claude Sonnet 5 and Claude Opus 5 answered nothing.** Every one of their 800 calls returned HTTP 400
   "`temperature` is deprecated for this model". Those calls were rejected, not answered.
2. **The probe's table marked all four of those arms PASS.** An accuracy of 0 from 200 errors is "below the
   ceiling" and "inside the null". **That is a false pass: a defect in the Phase-6 tool's verdict**, which never
   asked whether there was an answer to judge.
3. **GPT-5 mini's registered temperature 0.0 was never sent either.** `langchain_openai` drops it silently (item
   6), so GPT-5 mini ran at the provider default.

**What is done, and why:**

- **Verdict fixed in `tools/phase6/e6_l3_probe.py`.** An arm with any provider error is now **NOT COMPUTABLE**,
  and every model's actual temperature is recorded in `l3.json`.
- **The two Claude 5 models are re-run with no temperature sent** (the provider default), through a
  `--no-temperature` option that names them. This is the same situation GPT-5 mini was already in, made explicit
  rather than silent. It completes the registered roster instead of leaving two models blank.
- **The rejected answer files are kept as the record** (`answers_claude-*.temperature_rejected.csv`).

**Reported as a deviation from Phase 6's registered temperature for three of the five models.**

**What the valid answers are made of** (`tools/phase8/e8_l3_rule.py`):

- **Gemini Flash and GPT-5 mini gave identical answers on all 200 probes.** Both follow the rule "over-valued iff
  the rendered price exceeds the rendered analyst fair-value estimate" in 99 % of probes, and Haiku 4.5 in 93 %.
  They follow it in the shuffled arm too, applied to the fields they were shown.
- **That rule's own sign accuracy against sign(x) is 0.520**, which is every model's accuracy.
- **So the models do not infer the mispricing from the fields; they take the one field labelled a value as the
  answer**, and on this environment that field is at chance.
- **This is a finding about the models and the analyst field, not a leak.** It passes L3's rule for the wrong
  reason, and the report says so.

**A second defect, found in the first re-run and fixed before any of its answers were used:**

- **What went wrong.** With no temperature sent, Claude Sonnet 5 thinks by default and returns a thinking block,
  carrying a long signature, before its one-word answer. The probe joined every part of the reply into `raw`, then
  cut `raw` at 500 characters.
- **How many rows it hit.** Of the first 146 Sonnet 5 answers, 40 carried the block and 17 were cut before the
  answer, so the answer was gone. Almost all 20 unparsed rows are this defect; the rest are genuine "FAIR" answers.
  An unparsed row scores as wrong, which would have biased Sonnet 5 — and Opus 5, which also thinks — toward chance
  for a reason unrelated to the models.
- **What was done.** The re-run was stopped and its file set aside unused
  (`answers_claude-sonnet-5_normal.thinking_truncated.csv`). The probe now keeps only the text parts of a reply
  before truncating, and both Claude 5 models run again from the start.
- **The configuration recorded for them.** The provider default, with no temperature sent and adaptive thinking on.

**The outcome of the final run** (`e6_l3/l3.json`; all five models, 200 probes each, 0 provider errors):

| model | temperature that actually ran | sign accuracy, normal | shuffled | verdict |
|---|---|---|---|---|
| Gemini 2.5 Flash | 0.0 (provider-default thinking) | 0.520 | 0.485 | PASS |
| GPT-5 mini | provider default 1.0 (0.0 dropped silently) | 0.520 | 0.480 | PASS |
| Claude Sonnet 5 | none sent (provider default) | 0.505 | 0.475 | PASS |
| Claude Haiku 4.5 | 0.0 | 0.520 | 0.530 | PASS |
| Claude Opus 5 | none sent (provider default) | 0.515 | 0.475 | PASS |

The entitled reader scores 0.780 [0.718, 0.832] (ceiling 0.837) and the null's p95 is 0.560. **Every model is at
chance and passes, for the reason stated above: it reads the analyst field, not the mispricing.** With the Claude 5
answers in, the rule "over-valued iff price > analyst estimate" decides 0.97 of Opus 5's answers and 0.965–0.97 of
Sonnet 5's, beside Flash and GPT-5 mini at 0.98–0.99 and Haiku 4.5 at 0.93; any two models agree on 0.895–1.000 of
probes (`e6_l3/rule_analysis.json`). Every unparsed
Claude 5 answer is a genuine "FAIR" (6–7 per arm). One Opus 5 answer carried reasoning prose before its word and
kept the word inside the cut.

## 15. D11's O3 reference level cannot run in the v2 harness, and D11 does not need it

**What D11 (P8-13) named:** a common-start slice "with the no-persona (NONE) and O3 numerical-only reference levels".
Phase 7's day-1 gate null (P7-7) names the same two.

**Found when the decision was checked for feasibility, before any grid was built:**

- **O3 cannot be constructed.** `agent/v2_prompts.system_prompt` sends every persona other than NONE/TRADER to the
  MBTI persona builder, so `V2Agent(persona="O3_conservative")` and the runner both raise
  `ValueError: Unknown MBTI type: O3_conservative`. The O3 band, centre and common start are defined; only the
  prompt is missing. **An arm Phase 7's gate null names has never been runnable in v2.** NONE runs.
- **The only existing O3 text contradicts the v2 bands.** `agent/ocean_prompts.py` (v1's numerical-only ablation)
  tells O3_conservative its target is 100 % cash and O3_aggressive 20 %; the v2 bands are 0.70–0.90 and
  0.00–0.20. `evaluation/separability_gate.py` records the mismatch. Porting that text verbatim would score a run
  as out of mandate for doing what its prompt says.
- **D11 is identified without O3.** On the known-answer common-start design (`frame("B_common_start_with_references")`
  in `tools/phase8/e8_4_salience.py`), `identification_check` passes with NONE as the only reference (80 runs;
  ranks P 3 / D 3 / S 0 / all 6), passes with O3 only, and fails clause (iv) with no reference at all.

**Reading:** D11's substance — a common-start slice with a no-persona reference — is implementable now with NONE.
Whether O3 is added, and with which wording, is a separate design choice put to the team, not taken here.

**A consequence checked after the team first chose "NONE only", and a correction of what the D11 question said:**

- **What the question said.** Putting D11 to the team, this phase said the reference cells would make the day-1 gate's
  null computable.
- **What the code does.** Phase 7's gate (`tools/report_v2.gate_tables`) computes its null only when the no-persona
  arms carry **at least two distinct persona labels**. Both no-persona trader arms (`trader`, `trader_maximise`) are
  labelled NONE.
- **The test.** On a synthetic common-start day 1 with ISFJ, INTJ, ENTJ and both trader arms, the null is returned
  **NOT COMPUTABLE**.
- **So the claim holds only with O3.** O3_conservative and O3_aggressive are two labels, so O3 would make the null
  computable. Its two arms are told different numeric targets, though, so they would separate by construction;
  whether that is the null P7-7 intended is Phase 7's design, not settled here.
- **The gate's message misleads on this case.** It says "the common-start runs carry no arm in which no persona text
  is shown", although they do carry such arms; the condition that actually failed is the single label. Recorded,
  not changed (Phase 7's code).

The team was told this and asked to confirm or change the O3 choice with it in front of them.

## 16. The registered 90 % upper limit covers the truth only 60–67 % of the time

**Registered (5.5; P8-1):** the plug-in is "the one-sided 90 % upper limit of σ_d(R′), percentile cluster bootstrap
over paths (resampling the 32 paths within scenario, 2,000 resamples); the χ² limit of σ_d(3) on 84 df beside".
The team chose a 90 % limit so that the main grid's seed count holds with 90 % assurance.

**Measured on known answers** (item 13; 200 datasets per setting in E8.5's own shape; 2,000 resamples; **before any
E8.5 number was read**):

- **The point estimates are unbiased.** Median estimate ÷ truth is 0.998–1.008.
- **With replicate noise only** (seed × arm sd 0), the limit covers **0.92** (R′ = 1) and **0.97** (R′ = 3) —
  conservative, because σ²_int is truncated at 0 in half the datasets.
- **With seed × arm variance present, it fails badly:**
  - mixed (0.03 / 0.04): **0.67** [0.60, 0.73] at R′ = 1 and **0.64** at R′ = 3;
  - seed-dominated (0.05 / 0.02): **0.60** [0.53, 0.67] and **0.60**.
- **The consequence:** sized on this limit, the grid gets fewer seeds than D12 needs in **29 %** and **40 %** of
  datasets in those two settings. Resampling eight seeds per scenario understates the uncertainty of a standard
  deviation.

**The rule, as registered, does not deliver the assurance P8-1 chose.** It is not re-tuned, and it is not dropped:
the power table reports it with its measured coverage beside it.

**Added beside it, before any pilot number was read:** a closed-form upper limit that does not resample, the
modified large-sample bound for the non-negative combination σ_d(R′)² = E[MS_d] + (2/R′ − 2/R) E[MS_rep] of two
independent mean squares (`tools/phase8/e8_5_analyse.mls_ucl_sigma_d`). At R′ = R it equals the registered χ² limit
exactly (`test_mls_limit_reduces_to_chi_square`). Its source, Graybill & Wang (1980), was not re-read, so its
coverage is measured on the same known-answer datasets rather than taken from the paper; the result is appended
below. **The power table is reported under both limits.**

**The closed-form limit's measured coverage** (same 600 datasets; nominal 0.90; `e8_5/validate.csv`):

| seed × arm sd / replicate sd | bootstrap, R′ = 1 | closed form, R′ = 1 | bootstrap, R′ = 3 | closed form, R′ = 3 | grid sized too small: bootstrap / closed form |
|---|---|---|---|---|---|
| 0 / 0.05 | 0.920 | **0.945** [0.904, 0.969] | 0.970 | **0.940** | 7 % / 4 % |
| 0.03 / 0.04 | 0.670 | **0.935** [0.892, 0.962] | 0.640 | **0.915** | 29 % / 6 % |
| 0.05 / 0.02 | 0.600 | **0.940** [0.898, 0.965] | 0.595 | **0.935** | 40 % / 6 % |

**The closed-form limit delivers the 90 % assurance in every setting**, slightly conservatively. It costs a few seeds:
the median plug-in size is 61 against the truth's 54 in the mixed setting, and 52 against 44 in the seed-dominated
one. **The main grid is sized on it, and the registered bootstrap limit is reported beside every number** (DECISION_LOG
P8-15). Both were fixed before any E8.5 number was read.

## 7. The execution prompt's "≈ 77 tokens away" was the block's size, not the distance

Stated in the pre-registration before measurement (section 8 item 1) and now measured: the nearest copy is the
format instructions plus a separator away — **409 in chars/4, 436 o200k tokens** — against the logged 15,261–16,546,
a factor of **37.3–40.5** (expectation: ≈ 35). File: `docs/env_v2/generated/v2_1/e8_1/pilot_offsets.json`.

## 17. E8.5's variance sits in persona × path, which neither the registered components model nor E1 carries — an unregistered check, registered here before it runs

**Registered:** 5.4 (1), REML with variance components {path, path × arm} and the residual read as the replicate
variance; 3.2 (E1, P8-9), the crossed model with model, model × arm, path, and path × arm when R ≥ 2.

**Measured on Flash's 576 runs (band-MAS), after the batch was scored:**

- **The registered REML's residual is not the replicate variance.** It is 0.00251, against the pooled within-cell
  replicate variance of 0.000170 (df 384) — 15 times larger. Its path × arm component sits at the boundary (5.0 × 10⁻⁹)
  while the model-free σ²_int is 0.000869. The registered ICCs therefore count persona-specific variance as noise.
- **With persona × path and persona × path × arm added** (unregistered, `e8_5/components_reml_persona_path.json`,
  written by `e8_5_analyse --stages reml_pp`, which reproduced the first computation to 0.0 in every component;
  lbfgs and Powell agree within 0.02 log-likelihood units, so the planted components are not a local optimum):
  path 9.3 × 10⁻⁵, path × arm 2.1 × 10⁻⁵, **persona × path 0.00311 (ICC 0.82)**, persona × path × arm 0.000414 (0.11),
  replicate 0.000170 (0.045). The implied σ_d(R = 1) is 0.03476, equal to the plug-in. D at both θ shows the same
  pattern (persona × path 0.75–0.83); turnover's variance sits in persona × path × arm (0.54).
- **What it does to E1, on Flash's own rows** (sum-to-zero coding, the average memory − static over the 12 persona ×
  scenario cells):
  - at R = 1 (replicate 0, 192 runs), E1's arm SE is **0.00723** against the model-free paired SE **0.00318** — ratio
    **2.27**, about **5×** the seeds for the same power; with a persona × path intercept, 0.00318 (ratio 1.00);
  - at R = 3, 0.00417 against 0.00320 (1.30); with both persona terms, 0.00333 (1.04).

  These were first computed inline, with lbfgs. They are now a stage, `e8_5_analyse --stages e1_pairing`
  (`e8_5/e1_pairing_se.json`), which reproduces every one of them and adds the better REML optimum beside. At R = 1,
  lbfgs had stopped at a local optimum for E1 itself (log-likelihood 150.2 against 186.1): **at the better optimum
  E1's SE is 0.0079, 2.48× the paired SE, about 6× the seeds.** The persona × path fits and the R = 3 fits are the
  same at both optima.

  **P8-15's seed count assumes the paired SE.** A grid analysed with E1 as registered would not have the power it was
  sized for.
- **E8.3 never planted this structure.** Its real path effect is per (scenario, seed, persona) but has an sd of
  0.0003–0.0005 (item 3); its Gaussian sensitivity is shared by personas.

**What is added** (`tools/phase8/e8_3_simulate.py --stages mixed_pp`). Data are generated with the five components
read from `components_reml_persona_path.json` (band-MAS), under two readings that one model cannot tell apart:

- **shared** — persona × path and persona × path × arm belong to the environment and are the same for every model;
- **model-specific** — both are drawn per model.

Everything else is E8.3's: model intercept sd 0.05, model × arm sd ∈ {0, 0.03} in E1's own parameterisation, 2
scenarios, 3 personas, M ∈ {3, 6}. The seed count is **the band-MAS-sized S read from `e8_5/power.json`** (19), with
R = 1 and β ∈ {0, 0.05}: 16 conditions × 200 datasets.

The estimators:

- **E1 as registered.**
- **E1-amended:** E1 fitted on the seed-level differences d = replicate-mean(memory) − replicate-mean(static) per
  (model, persona, path) — P8-1's pairing, the one the plug-ins use. Its fixed effects are persona × scenario, so the
  intercept is the reference cell's memory − static effect, E1's estimand. Its variance components are model
  (≡ model × arm), path (≡ path × arm) and persona × path (≡ persona × path × arm). Every persona × path intercept
  cancels in the difference, whether it is shared across models or not.

  **Changed before any rate was read.** The first form written here added persona × path, persona × path × arm and
  model × persona × path to E1 on the runs. A one-dataset smoke test at M = 6 (19 seeds, model × arm sd 0.03, β = 0,
  one dataset per reading) timed it at **425 s and 516 s per fit**, on a laptop shared with another job, and the
  shared-reading fit **did not converge**. That smoke test's output was not kept, and timings on a shared laptop are
  not reproducible. 3,200 such fits would take on the order of ten hours or more. The
  difference form estimates the same contrast with the same pairing and has about 700 rows and 160 random-effect
  levels at M = 6. No simulated rate existed when the change was made.

  **The optimizer, also changed before any rate was read.** On one model-specific dataset (M = 6, model × arm sd 0),
  E1-amended fitted by lbfgs — the optimizer E1 and `tools/stats_v2.crossed_mixed_model` use — **reported convergence
  at a local optimum**: REML log-likelihood 1300.6, a model component of 0.00069 where none was planted, SE 0.0114.
  Powell and Nelder–Mead reached **1309.9**, with the model component 0 and SE 0.0037. A moment estimate on the
  reference cell agrees with them (model 0.00003; residual 0.00131 against the planted 0.00117). The example is kept
  as `e8_3/optimizer_example.json` (`--stages optimizer_example`), which reproduces every number here.

  Every mixed fit in this stage therefore runs lbfgs and Powell and keeps the higher restricted likelihood, recording
  the winner and the gap. The registered E1 is reported both as registered (lbfgs) and at the better optimum
  (**E1-best**). The rule compares E1-amended with E1 as registered.

  E8.3's E1 rates were measured with lbfgs alone. How often that optimizer stops short on E8.3's own conditions is
  measured by `--stages mixed_optimizer`: 100 fresh datasets each at M ∈ {3, 6}, 10 seeds, model × arm sd 0.03,
  β ∈ {0, 0.05}. It reports the share of fits where Powell's log-likelihood exceeds lbfgs's by more than 1, and the
  number of reject decisions that change. P8-9's rates are not re-run.

**Result: the optimizer on E8.3's own conditions** (`e8_3/mixed_optimizer.json`; 100 fresh datasets per condition;
10 seeds; model × arm sd 0.03):

| models | β | lbfgs stops short (gap > 1) | largest gap | decisions that change | E1 as registered (lbfgs), reject [Wilson 95 %] | E1-best |
|---|---|---|---|---|---|---|
| 3 | 0 | 18 % | 3.9 | 5 | 0.09 [0.048, 0.162] | **0.14 [0.085, 0.221]** |
| 3 | 0.05 | 20 % | 3.7 | 11 | 0.68 [0.583, 0.763] | 0.79 [0.700, 0.858] |
| 6 | 0 | 15 % | 18.4 | 0 | 0.07 [0.034, 0.137] | 0.07 [0.034, 0.137] |
| 6 | 0.05 | 19 % | 6.8 | 5 | 0.94 [0.875, 0.972] | 0.99 [0.946, 0.998] |

**lbfgs stops at a local optimum in 15–20 % of E1's fits.** When it does, it inflates a variance component, which
makes E1 conservative:

- **At three models,** the better optimum rejects a true null in **14 %** of datasets (its Wilson interval lies
  wholly above 0.05), against 9 % as measured with lbfgs. P8-9's verdict (E1 does not hold size at three models)
  stands, and is **stronger** than its registered numbers show.
- **At six models,** size is unchanged in these 100 datasets, and power is higher (0.99 against 0.94).

P8-9's rates are not re-run. How `crossed_mixed_model` is fitted is settled together with this item's rule, when
`mixed_pp` lands.

**Result: `mixed_pp`** (`e8_3/mixed_pp.json`; 200 datasets per condition; 19 seeds; the full table is rendered in the
report, section 3.4). At six models, the rule's conditions, true-null rejection [Wilson 95 %]:

| persona × path | model × arm sd | E1 | E1-best | E1-amended | E2 |
|---|---|---|---|---|---|
| shared | 0 | 0.065 [0.038, 0.108] | 0.085 [0.054, 0.132] | 0.065 [0.038, 0.108] | 0.080 [0.050, 0.126] |
| shared | 0.03 | 0.085 [0.054, 0.132] | 0.085 [0.054, 0.132] | 0.080 [0.050, 0.126] | 0.090 [0.058, 0.138] |
| model-specific | 0 | 0.000 [0.000, 0.019] | 0.000 [0.000, 0.019] | 0.055 [0.031, 0.096] | 0.005 [0.001, 0.028] |
| model-specific | 0.03 | 0.095 [0.062, 0.144] | 0.095 [0.062, 0.144] | **0.135 [0.094, 0.189]** | 0.135 [0.094, 0.189] |

Power at β = 0.05 and α′ = 0.05 / 36:

| persona × path | model × arm sd | E1 | E1-best | E1-amended |
|---|---|---|---|---|
| shared | 0 | 0.955 | 1.000 | 1.000 |
| shared | 0.03 | 0.450 | 0.450 | **0.430** |
| model-specific | 0 | 0.770 | 1.000 | 1.000 |
| model-specific | 0.03 | 0.405 | 0.445 | 0.530 |

**The rule, applied as registered: E1-amended is not adopted.**

- (a) fails in one of four settings: model-specific reading, model × arm sd 0.03, size 0.135 (Wilson lower limit 0.094).
- (b) fails in one: shared reading, sd 0.03, power 0.430 against E1's 0.450 — four datasets in 200.

**The fallback therefore applies:** no mixed-model p-value decides a claim; E1 is reported descriptively; E2's
intervals decide.

**What the table shows beyond the rule:**

- **Without model × arm variance, E1 does not pair, and E1-amended does.**
  - Median SE ÷ sd of the estimates: E1 **2.22–2.59** in the model-specific reading (1.44–1.48 in the shared one at
    three models); E1-amended **0.94–1.10** everywhere.
  - E1-best also reaches power 1.00 at α′ there, so E1's own shortfall (0.77–0.96) is the optimizer: lbfgs stops
    short in **34–61 %** of those fits, at a zero-variance boundary.
- **With a model × arm sd of 0.03 at nineteen seeds, E1 and E2 do not hold size at six models.**
  - E1: 0.085–0.095 (Wilson lower limits 0.054–0.062). E2: 0.090–0.135 (0.058–0.094).
  - E1-amended holds only in the shared reading, at the boundary: 0.080 [0.050, 0.126].
  - At three models E2 rejects a true null in 20 %.
  - At ten seeds (P8-9) E1 and E2 held at six models. More seeds shrink the within-model noise and leave six
    model-level draws governing the contrast.

**Post hoc — computed after the rates above were read; adopts nothing** (`--stages mixed_tref`,
`e8_3/mixed_tref_posthoc.json`; the cached estimates and SEs, no refit). The same estimates were referred to a
t distribution with M − 1 df instead of the normal:

- **Size holds for every mixed estimator** at six models with model × arm sd 0.03: E1 0.030–0.045, E1-amended
  0.035–0.060, Wilson lower limits ≤ 0.035. On `mixed_optimizer`'s ten-seed datasets it is 0.000–0.020.
- **Power at α′ collapses** to 0.025–0.075 in those settings, from 0.405–0.530 with the normal reference. Without
  model × arm variance, E1-amended keeps 0.735–1.000 against E1's 0.135–0.625.

**When the arm effect varies by model, the number of models, not the number of seeds, bounds a confirmatory
contrast.** Section 5.5's model-level DESIGN table (`e8_5/power.json`), which already uses t with M − 1 df, says the
same. The reference distribution for model-level contrasts is carried to Phase 9's pre-registration (P8-17).

**How `crossed_mixed_model` is fitted.** `optimizer="best"` (lbfgs and Powell, the higher REML likelihood kept) is
added, and it equals E1-best (`test_crossed_mixed_model_best_optimizer`). The default stays lbfgs, the estimator P8-9
validated. `run_stats_v21` fits at the better optimum and labels the crossed model descriptive. An estimate that is
not the REML maximum is a numerical failure, and E1's measured size at three models was flattered by it.
- **E2** (P8-9) beside.

Reported: size at α = 0.05, power at α = 0.05 and at α′ = 0.05 / 36, Wilson intervals, and the median model SE
against the sd of the estimates (SE calibration).

**The rule, fixed now:** E1-amended replaces the registered E1 in `tools/stats_v2.crossed_mixed_model` for the main
grid iff, at M = 6, in both readings and both model × arm settings:

- (a) its size holds (Wilson lower limit ≤ 0.05), and
- (b) its power at α′ is not below the registered E1's.

If (a) fails, no mixed-model p-value decides a claim. E1 is then reported descriptively, and E2's intervals, which
are the contrast intervals under P8-9 either way, decide. At M = 3 the outcome is reported only: P8-9 already marks E1
and E2 invalid there when the arm effect varies by model. The registered REML components stay in the components
table, with this finding beside them. The power table does not change, because it never used the REML fit.

**A reproducibility defect in E8.3's simulation, disclosed here.** `_mixed_task` and `_gpath_task` seed each dataset
with `abs(hash(cond_key(c)))`. Python salts string hashes per process, so a dataset depends on which pool worker drew
it. The datasets are valid Monte-Carlo draws from the registered process, and every rate is as reported, but the
caches are not bit-reproducible. They are not re-run. The new stage seeds with `zlib.crc32`.

## 18. E8.4's seed-cluster bootstrap leaked copies of a seed across cross-validation folds — found on the known answer, fixed, re-run

**Registered (section 4, known-answer check):** under design (b), whether S_directive's bootstrap interval covers 0
and S_persona's excludes it, from a cluster bootstrap by seed with B = 200 refits.

**Result as run** (200 refits per window, 16,225 s):

| window | S_persona [95 %] | S_directive [95 %] |
|---|---|---|
| 1 | 0.979 [0.962, 0.978] | 3.2 × 10⁻⁶ [0.00019, 0.0029] |
| 26 | 0.975 [0.959, 0.974] | 1.1 × 10⁻⁵ [0.00017, 0.0027] |

Persona excludes 0. **Directive does not cover 0, although its true value is 0, and neither interval contains its own
point estimate.**

**Cause.** `_boot_refit` relabelled each copy of a drawn seed `s#j`, and `surrogate_shares` builds its GroupKFold
folds on `Seed`. The copies therefore landed in different folds, and a fold's test rows had identical twins in its
training rows. The docstring said relabelling "keeps them apart"; it did the reverse.

**Diagnostic** (unregistered; the reported run's first 12 resamples of window 1, each refitted both ways;
`e8_4/bootstrap_leak_diagnostic.csv`, written by `e8_4_salience --stages leak_diagnostic`, which reproduces the first
computation to 2.2 × 10⁻¹⁶ in every share and R²):

| refit | S_directive, median (range) | S_persona | OOF R² |
|---|---|---|---|
| copies relabelled (as run) | 0.00094 (0.00017–0.0029) | 0.969 (0.962–0.978) | 0.979 (0.973–0.987) |
| copies in one fold | 0.000019 (0.000001–0.000099) | 0.978 (0.974–0.982) | 0.968 (0.964–0.970) |
| the point fit | 3.2 × 10⁻⁶ | 0.979 | 0.969 |

**The inflated R² is the leak's signature.**

**Fix.** Copies keep distinct run labels and share a `Boot_Group`, the original seed, which
`surrogate_shares(groups_col=)` uses for the folds. The default is `Seed`, so v2 and every point estimate are
unchanged. Guarded by `test_salience_bootstrap_copies_share_a_fold`. The bootstrap is re-run as registered (200
refits). The leaky run's intervals are kept in `e8_4/bootstrap_leaky.json` and not used.

**Still unsatisfiable after the fix: "S_directive's interval covers 0".** Every share is a sum of max(permutation
importance, 0). A share is exactly 0 only if every one of its columns scores ≤ 0 in every fold. In the diagnostic's
12 grouped refits the directive share is 1 × 10⁻⁶ – 1 × 10⁻⁴ and never 0. The check is reported as registered and
**fails by construction**, as clause (i) did (item 10). No threshold is introduced after the fact; the interval is
reported as it is.

**Result of the re-run** (`e8_4/bootstrap.json`; 200 refits per window; 19,875 s). The laptop slept twice during the
run. The processes were paused, not restarted, and every refit's seed is fixed, so the result is unaffected. After
the first sleep the workers' warning lines stopped reaching the log; the parent wrote the result files.

| window | S_persona [95 %] | S_directive [95 %] |
|---|---|---|
| 1 | 0.979 [0.974, 0.984] | 3.2 × 10⁻⁶ [1.2 × 10⁻⁶, 9.4 × 10⁻⁵] |
| 26 | 0.975 [0.970, 0.980] | 1.1 × 10⁻⁵ [3.1 × 10⁻⁶, 1.9 × 10⁻⁴] |

- **Every interval now contains its point estimate.** The directive share's upper limit falls 14–31× from the leaky
  run (0.0029 and 0.0027).
- **The persona interval excludes 0:** the registered check passes.
- **The directive interval does not cover 0:** the registered check fails, by construction. Its lower limits,
  1.2 × 10⁻⁶ and 3.1 × 10⁻⁶, are sums of importances clipped at 0.
- **On data with no directive effect,** the measure attributes at most about 0.02 % of importance to the directive
  block and 97–98 % to the persona block.

## 19. Close-out audit of the stored results: four analyses moved into the repository, one reported NaN fixed

Asked whether every result was documented and stored, the phase checked in both directions: every generated file is
cited somewhere (90 of 90), and every cited number comes from a file written by code in the repository. The second
direction did not hold everywhere.

**Four analyses had been run from outside the repository** (a temporary scratch folder, or inline). They are now
stages, and each reproduces what the documents say:

| stage | file | reproduction |
|---|---|---|
| `e8_5_analyse --stages reml_pp` | `e8_5/components_reml_persona_path.json` | identical to 0.0 in every component `mixed_pp` planted; lbfgs and Powell agree within 0.02 log-likelihood units |
| `e8_5_analyse --stages e1_pairing` | `e8_5/e1_pairing_se.json` | every documented SE reproduced; **at R = 1 the registered E1's lbfgs fit was itself at a local optimum: at the better optimum its SE is 2.48× the paired SE, not 2.27×** (item 17) |
| `e8_3_simulate --stages optimizer_example` | `e8_3/optimizer_example.json` | every documented number reproduced |
| `e8_4_salience --stages leak_diagnostic` | `e8_4/bootstrap_leak_diagnostic.csv` | reproduced to 2.2 × 10⁻¹⁶ in every share and R² over all 24 refits (the difference is thread-order noise in the last bit) |

**The model-level DESIGN table in `e8_5/power.json` carried a NaN.** SciPy's noncentral-t CDF fails at 7 df and a
noncentrality of 6.8 (eight models, between-model sd half the limit), and the report rendered it as "nan".

- **The fix.** Power is now computed for every row by integrating the normal tail over the chi-square scale
  (`power_t_two_sided`). It matches SciPy to 3 × 10⁻⁷ relative on every row where SciPy is finite, and matches a
  seeded Monte Carlo at the failing point (`test_power_t_two_sided_matches_nct`). The missing row is **0.863**.
- **A mistake in the fix, caught before use.** A first version of the integral returned 0 for the two-model rows,
  whose probability mass sits at chi-square values below 6 × 10⁻⁵. The comparison against the stored values caught
  it, and it was fixed with geometric integration segments before any document used it.
- **Everything else in `power.json` and `power.csv` is unchanged.**

**Where the results live.** The raw E8.5 runs are under `results_v2/phase8_e8_5/`: the 720 design runs, plus the first
smoke's four runs set aside as `.failed.<time>` with their empty `meta.json` (P8-6). `.gitignore` excludes that folder,
so those runs exist on this laptop only. The scored table, the ledgers and every analysis file are under
`docs/env_v2/generated/v2_1/e8_5/`, which git tracks.
