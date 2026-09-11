# Prompt: execute Phase 8 of the v2.1 improvement plan (harness and statistics — the stateful arm made honest, context length a factor, the model re-specified, the power analysis that sizes the main grid)

## What this project is

**FinPersona-Bench** asks a question about LLM agents, not about markets: *when an LLM is given a persona with an
investment mandate — a risk band, a target allocation — does it keep to that mandate as market conditions change, or does
it drift?* An agent is run day by day through a multi-day market, sees a rendered snapshot (price, technicals, sentiment,
implied volatility, an analyst estimate, EPS and dividend fields), and allocates between cash and a risky asset. The
score is **mandate-conformity**, not profit: how far the agent's allocation sits outside the persona's band.

Phases 1–5 rebuilt the generator so that every parameter is fitted or tested on data; Phase 6 did the same for the
yardsticks and computed the go/no-go checkpoint; Phase 7 owns the scoring — θ, the regret decomposition, the bands,
dividends, the day-1 gate, the baselines. **Phase 8 owns the harness and the inference.** Everything between the
environment and a published contrast: what the stateful agent actually sees, how many tokens of it, how the covariate
that the decay thesis rests on is computed, which model the contrasts are fitted with, how the multiplicity across
roughly eight hundred of them is controlled, whether the salience shares are identified at all — and, at the end, the
one paid experiment that sizes the main grid.

**The governing rule of the whole programme: every generator parameter is fitted or tested on data, never stipulated.**
In your phase that reads: **the harness constants — the window, the token budget, the summary cadence, the placebo's
length, the minimum detectable effect — are each either derived, swept as a factor, or labelled DESIGN with a
sensitivity; and every statistical choice is validated on simulated data with a known answer before it is applied to a
real contrast.** A statistic marked "(to verify)" may not appear in a parameter file, a test tolerance, or a slide.

---

## The document landscape

**The single working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`.** Its shape:

| Section | What it is |
|---|---|
| 0 | What was verified before the plan was written |
| **1** | **The protocol every phase follows** — pre-register, fit or test everything, report failures as failures; the power-analysis rules |
| 2 | Weakness-to-phase map (which of the 74 review findings each phase closes) |
| 3 | Data sources, their substitutes and their biases |
| 4–14 | **Phases 0–10**, one section each. **Section 12 is yours: Phase 8, harness and statistics** (E8.1–E8.5) |
| 15 | Cross-phase compute, cost and effort — **your row: 1 h of compute, ≈ $105 (Flash) or ≈ $86 (GPT-5 mini), 7–10 person-days, blocked on D11 and D12** |
| **16 / 16A** | **Order and the go/no-go checkpoint.** 16A was computed at the end of Phase 6 and **is not met**; the team took **D17 = restrict the claim** (P7-1), so the programme continues with the paper's claims restricted to a one-shot mandate-conflict benchmark. Section 16 also says **Phase 8 runs any time after Phase 0** and that **E8.5's variance pilot waits for the Phase-6 freeze, which exists** |
| 17 | Decisions only the team can make — **D11 (salience shares) and D12 (the minimum effect) are yours**; D2 (the roster and budget) gates your one paid experiment |
| A / B / C | **Appendix A is the power-analysis formulas your E8.5 must use** · the analytic level-free bound · numbers to be recomputed |

Around it:

- `V2_1_ALTERNATIVES_REGISTER.md` — **no entry is yours to decide**, but **entry 16 (the LLM sensitivity grid) names
  "ICC from the variance pilot" as one of its inputs**, so your E8.5 is what Phase 9's grid is sized from. Read it to
  see what your output has to support.
- `spec/IO_CONTRACT.md` **sections 2.4–2.5 are yours to rewrite** (the arms registry and the log schema); sections
  2.2–2.3 were rewritten by Phase 7 and are not yours.
- `reviews/V2_WEAKNESSES.md` — the 74 findings. Yours: **28** (window and budget stipulated, not swept), **34** (the
  harness constants found only in code), **55** (salience shares not identified under start-at-target; the promised
  bootstrap intervals never implemented), **57** (the stateful arm's three defects), **59** (the mixed model nests what
  is crossed, intercepts where slopes were registered, run-level bootstraps that ignore clustering, multiplicity across
  seven metrics instead of ~840 contrasts, a circular-shift null with seven distinct values), **60**'s remaining half
  (placebo matching asserted, not tested), **67**'s remaining pieces (salience bootstrap intervals; random slopes).
- `decisions/DECISION_LOG.md` — **the P7-* entries are the freshest precedent.** Read **P7-4/P7-5** (a decision put to
  the team *with the table in front of them*), **P7-9** (a rule adopted on its own evidence, with the number the rule
  does not capture reported beside it), **P7-16** (an older test updated to the contract that replaced it, not
  weakened), **P7-17** (a derivation confirmed by measuring the thing it is used for, with its own limit stated), and
  **P6-7** (a statistic and its null from one tool with one construction).
- `generated/v2_1/` — every machine-written result. Yours will be `e8_*`.
- `tests/known_defects.py` — the registry. **Its two entries are the derived L2 and L2b gates, failing, owned by D17.
  Nothing in your phase touches them.**

---

## Context for this phase: what Phase 7 measured, and what it changes for you

Every number below is a measurement on the frozen Phase-7 state (`PHASE_7_REPORT.md`; files under `e7_*`), or on the
pilot's own logs, which you can re-read.

**1. The scoring you will be doing inference on is settled and is not yours to revisit.** θ in force is **co-primary**:
θ_cost = **0.0020** and θ_info = **0.05** (`evaluation/params/scoring.json`, read through the loud loader
`evaluation/scoring_params.py`; D7, P7-4). MCR is decomposed as **MCR = B + D** on resolvable steps — B the band
violation, D the directional remainder — and **scoring A (the decomposition) is adopted** (P7-9, stable across all 27
θ × half-width combinations, P7-18). The entry point is `metrics_v2.score_run(..., scoring="v2_1")`, which adds
`v21_*` keys and changes no v2 key.

**2. The metric family you will correct multiplicity over is collinear, and Phase 7 measured by how much.** Across the
policy panel: **|r|(MCR, band-MAS) = 0.976** (0.981 on the 16A policy set alone), **|r|(B, band-MAS) = 0.996**, and
**|r|(D, band-MAS) = 0.069** with |r|(D, MCR) = 0.267 (`e7_8/matrix.{csv,json}`). **This is a fact about your family
definition, not a curiosity.** BH over a family containing MCR *and* band-MAS is close to BH over one test counted
twice; D is the term that carries what band adherence does not. `tools/stats_v2.py`'s `METRICS` list is still the v2
one — `["mcr_0.05", "band_mas", "point_mas_v2", "rg_theta_0.05", "return_pct", "mdd_pct", "turnover"]` — and carries
neither B nor D. **Which metrics form the pre-registered family, and how the family is partitioned for BH-within and
BY-across, is a decision you make in your pre-registration with these correlations in front of you.**

**3. The salience identification problem is the day-1 gate's problem, and Phase 7 hit it first.** E7.5 re-specified the
gate on the common-start design with the null taken from the arms in which **no persona text is shown** — the O3
numerical-only arm (`persona ∈ {O3_conservative, O3_aggressive}`) and the no-persona trader (`persona = "NONE"`, arms
`trader` / `trader_maximise`). **The pilot's nine common-start runs contain neither**, so the gate's null is reported
`NOT COMPUTABLE` (P7-7). **E8.4 needs exactly the same reference levels for exactly the same reason.** If the main
grid does not carry them at common start, your salience measure is not identified either, and that is D11's substance.

**4. Two of your inherited items are already half-closed by Phase 7.** Item 60's first half (next-open execution logged
the pre-trade share under the name `cash_share_after`) is **fixed**: `Cash_Share_Pre` and `Cash_Share_Post` are in the
log and the record carries `pending: True` (P7-11's sibling change). Item 34's trader-band clause is **fixed**:
`evaluation/targets.band()` is the single definition and returns (0, 1) for `NONE`/`TRADER` (P7-11). Item 67's
held-out-scenario split was done in Phase 6, and its JFE-spread clause was **removed** in Phase 7 because the source
does not contain the number (P7-6). **What is left of 34 is the list of constants; what is left of 60 is the placebo
test; what is left of 67 is the salience bootstrap and the random slopes — all three yours.**

**5. Phase 7 measured the placebo's length; it did not assert it.** From the pilot's own prompt records, placebo/real
ratio **1.005** (chars), **0.964** (words), **0.981** (approximate tokens), n = 9 and 11 (`e7_7/placebo_length.json`).
**The imperative-clause half of E8.1(e) was not done.** Your job is to turn a measurement into a test on the rendered
texts — word count within 10 %, same number of imperative clauses — and to note that n is small, so a non-significant
p is not evidence of matching; the ratio and its n are the statement.

**6. The stateful arm's defects, measured on the pilot's own three runs.** All three are `stateful_memory`, rolling
window 20, budget 60,000 (`results_v2_pilot/stateful/`):

| what the log says at day 200 | ENTJ | INTJ | ISFJ |
|---|---|---|---|
| `Context_Tokens` | 20,454 | 20,512 | 21,332 |
| `Mandate_Offset_Tokens` | **15,261** | **15,909** | **16,546** |
| `Context_Turns` | 20 | 20 | 20 |
| parse fallbacks in the run | 0 | 0 | 0 |

**The offsets are wrong by more than an order of magnitude and in the direction that flatters the decay thesis.** The
memory arm **re-injects the mandate into the current turn** (`agent/v2_agent.rendered_human_message` formats
`mandate_block=self.core_mandate` into `HUMAN_TEMPLATE_V2`), so the nearest copy the model can attend to is about
**77 tokens** away, not 15,000. `agent/stateful_agent.build_messages` computes the offset from
`self._mandate_end_char`, which is located by `self.full_system_prompt.find(m)` — **the system-prompt copy only**.
E8.1(a) asks for both, computed to the nearest copy and both logged.

The same construction causes E8.1(b): `self.history.append({"human": msgs[-1].content, ...})` stores the current human
turn **including its mandate block**, so a full rolling window replays **20 copies** of the mandate, plus the system
prompt's and the current turn's — **22 in all**. The mandate block is **311 characters ≈ 77 tokens**, so the retained
duplicates are ≈ **1,540 tokens, 7.5 % of the day-200 context**, present in the memory arm and absent in the static
one. That is the token-budget mismatch E8.1(b) is about, and **it has never been checkable on the pilot, because all
three stateful pilot runs are the memory arm and `stateful_static` was never run.**

E8.1(c): the fallback branch does `self.history.append({"human": ..., "ai": out.model_dump_json()})` — the fabricated
hold is stored as the model's own prior turn. **It has never fired in a real run** (0 fallbacks above), so this is a
latent defect, and your test is what makes it stay fixed.

E8.1(d): `_approx_tokens(text) = max(1, len(text) // 4)`. The provider's usage metadata is read *after* the call and
overwrites `last_context_tokens` only — **`last_mandate_offset` is always chars/4**, and the offset is the covariate
the decay thesis rests on.

**7. Nothing in the harness is swept.** `window = 20`, `token_budget = 60000`, `summary_every = 10`,
`summary_raw_turns = 5` are constructor defaults (item 28). The arms registry already carries the levels you need for
three of E8.2's four: `stateful_r5_*` (the matched rolling-5 control for the summary arm), `stateful_*` (rolling 20)
and `stateful_full_*`. **A window-50 level does not exist and you add it.**

**8. The statistics as implemented.** `tools/stats_v2.mixed_effects` fits
`smf.mixedlm(..., groups=d["Model"], re_formula="1", vc_formula={"seed": "0 + C(Seed)"})` — **seeds nested inside
models, random intercepts only**, exactly item 59. `bootstrap_ci` resamples runs, not clusters. `bh_adjust` is applied
"across the metric family within each contrast" (the module's own docstring), not across the family of contrasts; the
reviewer's count of the latter is **≈ 840**, which you re-derive rather than quote. `windowed_trend_vs_null(...,
null="circular")` shifts 25-day window means over a 200-day run — **eight windows, so at most eight distinct rotations**
— which is the "seven distinct values" of item 59. `paired_sign_flip` is the alternative already present and is kept.

---

## Read first, in this order

1. **Section 12 of the plan** — your phase, in full; then **Section 17 (D11, D12, and D2 which gates E8.5)**; then
   **Appendix A**, whose formulas E8.5 must plug the variance pilot into.
2. **`PHASE_7_REPORT.md` sections 0 (the state table), 3.11 and 3.11b (the correlation matrix, its ceiling, and the
   robustness of the adoption), 3.8 (the day-1 gate and its NOT COMPUTABLE null), 3.10 (the small items, including the
   placebo measurement) and 7 (what was carried and to whom).**
3. **`DECISION_LOG.md` P7-4, P7-5, P7-7, P7-9, P7-16, P7-17, P7-18**, and **P6-7** (one tool, one construction).
4. **The code you are changing**: `agent/stateful_agent.py` (all of it — it is 150 lines and every E8.1 defect is in
   it), `agent/v2_agent.py::rendered_human_message`, `experiments/arms_v2.py` (the registry), `tools/stats_v2.py`,
   `evaluation/salience.py`, `simulation/runner_v2.py` (the log schema).
5. **`tools/phase7/`** as the pattern for everything procedural: `tools/phase7/e7_report_tables.py` (report tables generated from
   their files and read back by a test), `tools/phase7/e7_cite_check.py`, `tools/phase7/e7_changed_files.py`, `tools/phase7/e7_write_scoring_params.py` (a
   parameter file written from result files and re-read through a loud loader before anything reads a table under it).
   **Copy them to `tools/phase8/` and adapt; do not invent a new discipline.**

---

## Decisions: what governs what you may start

**E8.1–E8.4 need no API call and no decision. Start them immediately.** They are correctness fixes, a factor
definition, a statistical re-specification validated on simulated data, and an identification analysis — every one of
them testable offline.

**E8.5 is the only gated experiment.** It spends money, so:

- **D2** (the roster and the budget tier) has been open since Phase 5 and is still open. E8.5 as the plan writes it is
  **1 model (Gemini 2.5 Flash) × 3 personas × 2 arms (static, memory) × 4 scenarios × 8 seeds × 3 decode replicates =
  576 stateless runs ≈ 115,000 calls ≈ $105**, or ≈ $86 on GPT-5 mini. **Put the design and the price to the team with
  your pre-registration, before the first paid call**, and note that **Phase 6's L3 probe (built, dry-run, not run;
  ≈ $12; `tools/phase6/e6_l3_probe.py`) shares D2** — if the team is approving a spend, approving both at once costs
  one decision instead of two.
- **D12** (the minimum detectable effect) must be recorded **before** the power table is read, not after. The plan
  states the candidates in the claim's own units: **a band-MAS difference of 0.05 — a quarter of a 20-point
  practitioner band, half a half-width — and a Cliff's δ of 0.33**, the latter explicitly labelled a DESIGN choice the
  team must confirm, with the plan's own warning that **"0.33 is conventional" is not a justification under the hard
  rules**. Ask for the effect size in the claim's units and record what you are told.
- **D11** (salience shares: common-start only, or dropped from the headline set) is answered by **your E8.4's
  identification analysis, not before it.** Do the analysis, then put it to the team with the collinearity shown.

**Ask for, in your first message:** **D12** with the two candidate effect sizes and what each implies for the grid's
size; **D2** with E8.5's design, its call count and its price, and the L3 probe beside it. **Do not ask D11 yet** —
it needs E8.4's table. **Do not pre-empt** D3, D5, D15, or anything Phase 9 decides.

---

## What Phase 7 hands you (do not redo this work)

- **The scoring, settled**: `evaluation/params/scoring.json` with twelve provenance-carrying blocks and its loud loader;
  `metrics_v2.score_run(scoring="v2_1")`; `evaluation/scoring.py` with the decomposition, the per-window alternative,
  and `normalise_metric` — **the one function in the codebase that decides a metric's orientation**. Use it; do not add
  a second place where a sign is decided.
- **The per-day policy panel** `e7_panel/` (12 M rows: 4 scenarios × 100 seeds × 3 personas × 50 policies × 200 days,
  verified identical to Phase 6's 16A at 1 × 10⁻¹⁶) and the re-scored cell frame `e7_rescore/cells.parquet`
  (1,620,000 rows at 9 θ × 3 half-widths). **Your simulated-data checks for E8.3 can use real cell distributions from
  this instead of invented ones**, which is a better test of the estimator than Gaussian noise.
- **The correlation matrix and its ceiling** (`e7_8/`), which is the evidence your family definition rests on.
- **The pilot, re-scored on its logged columns** (`e7_pilot/`, 52 runs) with the published per-run table reproduced at
  2.2 × 10⁻¹⁶ — the only LLM data in the repository until E8.5 runs.
- **The measured placebo lengths** (`e7_7/placebo_length.json`).
- **The freeze**: 30 files, manifest OK, and the 95-configuration path-hash fixture unchanged (0 of 95). **Your phase
  changes no path either; check it at the end the same way** (`tools/path_hashes.py --compare`).
- **The whole test tree green**: 191 passed, 1 skipped, 4 strict xfails, 0 failed, in 1:00:20. **That is the baseline
  your run is compared against**, and the one-hour cost is why you run it once at the end and not after every edit.

---

## What to do now: Phase 8, Section 12 of the plan

Five experiments, in the plan's numbering, with what Phase 7 adds to each:

- **E8.1 Stateful arm corrections.** (a) The mandate-offset covariate computed **to the nearest copy the model can
  attend to** — the system-prompt copy and, in the memory arm, the copy re-injected into the current turn — **both
  logged** as separate columns, so the decay thesis is tested against a covariate that means what it says. (b) The
  retained history stores the model's own turns **without** the injected block (the block is re-rendered for the
  current turn only), so the two stateful arms have matched token budgets — **logged and tested**, and note that the
  pilot cannot check this because it never ran `stateful_static`, so your test builds both arms itself. (c) Parse
  fallbacks are **not** stored as the model's own prior turn (store `"no valid answer"`); the defect is latent, so the
  test is the only thing that will keep it fixed. (d) The token estimate uses the **provider's usage metadata when
  available**, a tokenizer-based count otherwise, and `chars/4` **only as a last resort, labelled** — and the label
  reaches the log, because a covariate computed three different ways across a grid is not one covariate. (e) The
  placebo's length and imperative-clause count **asserted by a test on the rendered texts** (word count within 10 %,
  same number of imperative clauses), with Phase 7's measurement as the starting point.
- **E8.2 Context length as a factor.** Rolling window ∈ **{5, 20, 50, full}** pre-registered as a factor of the decay
  thesis — three levels exist in `experiments/arms_v2.ARMS`, **the 50 does not and you add it**. The summary arm keeps
  its matched rolling-5 control (`stateful_r5_*`, already there). State the cost of the {50, full} levels for Phase 9's
  grid, in calls and in dollars, using the pilot's measured context growth (20,454 tokens at day 200 on a window of 20)
  rather than an estimate.
- **E8.3 Statistics.** The mixed model re-specified as **crossed** random effects (model and seed crossed, via
  `vc_formula` with a single group in statsmodels), **random slopes for arm by model** as pre-registered, reported
  **with the variance components**; **cluster bootstrap by model and seed** for every contrast interval; multiplicity
  controlled over **the full pre-registered family with its count stated** — BH within each pre-registered question
  family, Benjamini–Yekutieli across families as the conservative report; the **circular-shift null replaced by a
  block-permutation null with enough distinct values**, or reported as exact with its eight; the paired sign-flip kept.
  **All of it tested on simulated data with known effects — size and power both**, and the family definition made with
  Phase 7's correlations in front of you (item 2 above).
- **E8.4 Salience shares.** Identified **only** on the common-start design with the directive factor and the persona
  factor both present **and the O3 / no-persona reference levels** — which is the same requirement that made Phase 7's
  day-1 gate NOT COMPUTABLE on the pilot. Bootstrap intervals implemented (item 67). Under start-at-target the shares
  are **not reported** and **the collinearity is shown in the report** rather than described. If the common-start cells
  are not in the main grid, the measure is **dropped from the headline set and kept as exploratory** — that is D11, and
  you ask it with the table.
- **E8.5 Variance pilot and the power analysis that sizes the main grid.** The pre-registered design above (576
  stateless runs). From it: **the variance components of MCR, its two terms B and D, band-MAS and turnover** across
  seeds, replicates and cells; the **intra-class correlations**; the **minimum detectable effect** for the arm
  contrasts at the planned seed × replicate counts; and the seed / replicate / model counts of the main grid set from
  **Appendix A's power rule** at the minimum effect D12 records. **Report the variance of B and D separately** — Phase 7
  showed they are nearly orthogonal, so a design powered for MCR is not automatically powered for D, and D is the term
  that carries what band adherence does not.

**E8.3 and E8.5 are the deliverables that matter most.** E8.3 decides whether any contrast the paper reports has a
defensible interval; E8.5 decides how big the grid that produces those contrasts has to be. **E8.1 is the one whose
defect is currently changing a published covariate by a factor of twenty**, so it is the one to fix first.

---

## Hard rules (from the plan; not optional)

1. **Pre-register before you run.** `PREREG_PHASE_8.md` exists before the first correction is measured and before any
   paid call, with: the mandate-offset definition (both copies, which is primary), the token-budget parity criterion,
   the context-length factor levels, the **exact model formula** for E8.3 with its random-effects structure written
   out, the **family definition and its size** for multiplicity, the null's construction, E8.4's identification
   condition, and E8.5's design, seed list, price and the minimum effect. If a rule later proves wrong, that goes in
   `PREREG_PHASE_8_ADDENDUM.md` with the disconfirmation stated as loudly as any confirmation.
2. **Every statistical method is validated on simulated data with a known answer before it touches a real contrast.**
   A crossed model that cannot recover a crossed structure you planted, or a multiplicity procedure whose false-positive
   rate you have not simulated, is not evidence. Size *and* power, both reported.
3. **No harness change is allowed to alter the environment.** `envs/` is not yours; the 95-configuration path-hash
   fixture must be byte-identical at the end. `evaluation/scoring.py`, `scoring_params.py`, `metrics_v2.py`,
   `targets.py` and `params/scoring.json` are **Phase 7's and under the freeze manifest** — you read them, you do not
   re-specify them. If you believe a Phase-7 scoring decision is wrong, that is a finding for the report and a decision
   for the team, not an edit.
4. **Every change to the agent, the arms or the statistics is a switch with the current behaviour behind it, proved
   inert when off** — the Phase-7 pattern: `score_run(scoring="v2")` returns the v2 dictionary bit for bit. The pilot's
   52 runs were produced by the current harness; a harness change that silently re-scores them is the defect this rule
   exists to prevent.
5. **Report failures as failures, with evidence. Numbers carry their `n`.** A salience measure that is not identified,
   a mixed model that will not converge on the real data, a power table that says the grid needs more models than the
   budget buys — each is a result, stated as such.
6. **`datasets/` is git-ignored and must never be uploaded anywhere.** Nothing in this phase needs it.
7. **Work stays on `main`. Do not create branches. Commit only when asked**, one-line message, no body, no trailers.
8. **No paid call before D2 and D12 are recorded**, and none before the pre-registration naming the seed list is
   written. A variance pilot whose design moved after the first batch is not a variance pilot.

### Method rules Phases 4–7 learned the expensive way

9. **Pin the configuration a tool measures** (P4-19) and **measure after the parameter file settles** (P4-45).
10. **Verify every file you cite exists** before the citation is written (P4-37); run the cite check on every document.
11. **Run the WHOLE test tree** (P4-38) — it takes an hour, so run it once at the end, and expect it to find one thing.
    Phase 7's run found exactly one failure and it was an older test encoding a contract Phase 7 had deliberately
    replaced (P7-16). **The older tests are what break, and updating one to the contract that replaced it is not the
    same as weakening it — say which you did.**
12. **Read a parameter file back before you read a result under it** (P6-12).
13. **A statistic and its null come from one tool with one construction** (P6-7, P5-16).
14. **A tool's "done" check tests emptiness, not presence** (P5-12).
15. **Generate every report table from its file** into a marked block and add the test that reads it back
    (`tools/phase7/e7_report_tables.py --check`; `test_phase7_report_tables_match_files`).
16. **Make every chain resumable and staged**, each stage its own files, anything over ten minutes in the background
    with `python -u`. **E8.5 is 576 runs against a rate-limited API: it must be resumable per run and it must
    checkpoint**, because a crash at run 500 that loses 500 runs of spend is a budget event, not an inconvenience.
17. **A generated list that lists itself flips on every write** — exclude it.
18. **Do not vectorise a statistic without proving the vectorised form equals the loop it replaces.** Phase 7's
    bootstrap went from minutes to one array operation and the equality was asserted on random inputs first
    (`test_oracle_target_series_matches_loop`, `test_regret_terms_batch_matches_scalar`).

---

## Documentation: keep it current as you go, not at the end

- **`PHASE_8_REPORT.md` is written as results land**, under the protocol's six headings: section 0 the state table,
  section 1 the citation table (Liu et al. 2024 TACL; Barr et al. 2013; Bates et al. 2015; Cameron, Gelbach & Miller
  2008; Benjamini & Hochberg 1995; Benjamini & Yekutieli 2001; Gelman & Hill 2007 — **each marked read / not re-read**,
  and **no number from a source that was not read**), then the corrections with before/after, the statistics
  specification **with its simulated size and power**, the variance-pilot results and the main-grid power table.
- **Every decision gets a DECISION_LOG entry (`P8-*`)** with the alternative rejected and the evidence file.
- **A harness parameter file** (`agent/params/harness.json` or the name you choose) carrying the constants item 34
  lists — the window, the budget, the summary cadence, the truncation, the token-estimate method — each with
  `value`, `status`, `label`, `source`, `date`, `interval`, `n`, a declared status vocabulary, and **a loud loader**;
  the Phase-7 pattern is `evaluation/scoring_params.py` and `tools/phase7/e7_write_scoring_params.py`.
- **`IO_CONTRACT.md` sections 2.4–2.5** rewritten (the arms registry, the context factor, the log schema's new
  columns); **`PILOT_NOTES.md`** annotated where a corrected covariate changes what its stateful paragraph means.
- **`PHASE_8_CHANGED_FILES.md`** generated from git and verified against disk.
- The plan's amendments recorded **in your report, not by editing the plan**.

---

## Compute: where to run what

**E8.1–E8.4 are minutes on the laptop.** Simulated-data checks for E8.3 are the largest offline stage and are still
minutes; if a size/power simulation needs many replicates, run it in the background with `python -u` and stage it.

**E8.5 is the only paid stage** and it is API-bound, not compute-bound: 576 runs × 200 days ≈ 115,000 calls, hours of
wall-clock against provider rate limits. **Checkpoint per run** — the pilot's `results_v2_pilot/*/checkpoint.txt` is
the existing pattern — and make the runner resumable so that an interrupted batch costs nothing to restart.

**The box** (`docs/COMPUTE_GPU_ACCESS.md`; 128 cores, 2 × RTX 4090, verified as a reference machine at P6-15) is
**not needed for this phase**: nothing here is a sklearn refit. Phase 7 probed it, found it up, and did not use it —
for the same reason you will not: the heavy stage is an API, and cores do not buy API throughput. Re-run the numeric
check only if you find a reason to send something there. **Kaggle is available and not needed.**

---

## Inherited open items

- **D2** — the roster and the budget. Blocks E8.5 and Phase 6's L3 probe. Ask once, for both.
- **D11, D12** — yours, as above.
- **D17 is taken** (restrict the claim, P7-1): the paper's claims are restricted to a one-shot mandate-conflict
  benchmark. **Your power analysis sizes a grid for that claim**, not for the information-value claim 16A tested and
  the programme dropped. Size the grid for the contrasts the restricted claim actually makes.
- **The two known-defect registry entries** (derived L2 / L2b gates, failing) — not yours, carried.
- **The all-rows L2 centred reading**, undecided at 40 draws — not yours; the team was asked in Phase 7 whether to
  spend the compute and has not answered.
- **Item 12** (sentiment's realised loading at 70 % of configured, D15's) and **item 7** (the generator's volume is
  more log-normal than real volume) — not yours, carried.
- **From Phase 7, and relevant to you**: per-scenario θ_info was computed from the *pooled* surrogate restricted to a
  scenario's rows rather than a held-out-scenario surrogate; the Merton table applies a GBM formula to a mean-reverting
  environment; `evaluation/criteria.py` and `params/phase6_criteria.json` sit outside the freeze patterns while Phase
  7's scoring layer sits inside. **None is yours to fix** — they are listed so you do not rediscover them as new.
- **Phase 9** is downstream of you and cannot be sized until E8.5 lands.

---

## My recommendation for how to begin, and why

1. **First message: D12 and D2**, with E8.5's design, its 115,000 calls and its price, and the L3 probe beside it —
   then start E8.1 while you wait, because none of E8.1–E8.4 depends on a decision.
2. **Fix E8.1(a) first and re-read the pilot's three stateful runs under the corrected covariate.** The offset is
   currently 15,261 where the attendable copy is ~77 tokens away. You will not be able to *re-run* the pilot (it is
   three runs on a generator that no longer exists — see P7-8), but you can recompute what the covariate *would* have
   been from the logged context, and the size of that correction is the first number your report should carry.
3. **Build E8.3's simulated-data harness before you touch `stats_v2.py`.** Plant a known crossed structure with known
   random slopes, confirm the current specification fails to recover it and the new one does, and only then re-specify.
   That ordering is what makes the re-specification evidence rather than preference.
4. **Define the multiplicity family with Phase 7's correlation matrix open.** A family containing MCR, B and band-MAS
   is three names for close to two independent things; D is the one that is nearly orthogonal. Say what the family is,
   count it, and justify the partition — the count is a number the report must carry.
5. **Do E8.4's identification analysis before asking D11.** Show the collinearity under start-at-target rather than
   asserting it, and show what the common-start design with the O3 and no-persona levels would buy.
6. **Expect the power table to be uncomfortable.** If the minimum effect D12 records implies more seeds or more models
   than the budget buys, that is the result — report the achieved power at the affordable design rather than adjusting
   the effect size until the design fits. The plan says this explicitly and Phase 6 and 7 both had a version of it.
7. **Expect at least one pre-registered rule to be undecidable or to come out the wrong way.** Eight phases in a row
   have had one; the addendum is part of the deliverable.

---

## Deliverable of this request

`PREREG_PHASE_8.md` (before any correction is measured and before any paid call; the offset definition, the parity
criterion, the factor levels, the model formula with its random-effects structure, the family and its size, the null's
construction, E8.4's identification condition, E8.5's design and price and minimum effect), the code under
`tools/phase8/` and the corrections in `agent/`, `experiments/`, `evaluation/salience.py` and `tools/stats_v2.py`, the
results under `docs/env_v2/generated/v2_1/e8_*/`, the harness parameter file with provenance and a loud loader, the
tests of Section 12.4 (`test_stateful_no_duplicate_mandate`, `test_context_budget_parity`,
`test_fallback_not_in_history`, `test_placebo_matching`, `test_mixed_model_crossed`, `test_bh_family_size_logged`,
`test_salience_common_start_only`) **plus the inertness test of every switch and a report-table consistency test**, the
before/after table of the stateful corrections on the pilot's logged context, the simulated size and power of the
re-specified statistics, the salience identification analysis with its bootstrap intervals, the variance components and
ICCs from E8.5 with **B and D reported separately**, the main-grid power table at the minimum effect D12 records, the
refreshed freeze manifest (path hashes unchanged, 0 of 95), `IO_CONTRACT.md` 2.4–2.5 updated, DECISION_LOG entries
`P8-*`, `PHASE_8_CHANGED_FILES.md`, and **`PHASE_8_REPORT.md`**.

Then stop for review — Phase 9's grid is sized from your power table and cannot start until it exists.
