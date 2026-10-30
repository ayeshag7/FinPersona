# Pre-registration — Phase 9, stage 2, E2: the causal package (mandate reminder ablation)

**DRAFT, 30 Oct 2026 — not yet registered.** It becomes the registration when the team approves it, and no run of
`docs/env_v2/generated/v2_1/e9_4/manifest_causal_open.json` may start before then. Nothing of this experiment has run.
Where it changes `PREREG_PHASE_9.md` 4.1, the change is named in section 0 with its decision; everything 4.1 fixes that
section 0 does not name stands.

---

## 0. What this file changes in PREREG_PHASE_9.md 4.1

| Item | PREREG_PHASE_9.md 4.1 | Here | Decision |
|---|---|---|---|
| Experiment | the headline's two arms | `GRID_EXPERIMENT_PLAN.md` 3's **E2**, three further arms | plan 3 |
| Roster | the 13 API configurations | the six of `e9_roster.CAUSAL_OPEN` | `HEADLINE_MODEL_SELECTION.md` 4.3 |
| Seeds per cell | Appendix A on the API sizing | **60**, the plan's own count, being the first 60 of the headline's | plan 3; section 2 |
| Confirmatory test | R5 over the roster | **each model its own family**; R5 exploratory | P9-14, carried |
| Concurrency | 15 workers per model | per-server, the task's own `--workers` under a 256 ceiling | P9-20 |
| Where it runs | the providers' APIs | vLLM 0.29.0 on HiPerGator B200s | P9-12, carried |

**Unchanged:** the three personas; T = 200; R = 1; `harness_version = placebo_version = "v2_1"`; dividends paid;
start at the band centre; the default generator at `Env_Code_Hash` **1d689aaf82a33a2e**; temperature 0.2.

## 1. The question

The headline measures memory − static. That contrast confounds three things the injected block changes at once:
**what it says** (the mandate's content), **how it says it** (imperative force, delimiters, length) and **where it
sits** (the recency position). E2 separates them with three arms that each hold two of the three fixed:

| Arm | Injects | Holds fixed | Isolates |
|---|---|---|---|
| `placebo_declarative` | irrelevant text, length-matched, declarative | position, length | text at the recency position, with neither content nor force |
| `placebo_directive` | irrelevant text, **imperative-, delimiter- and length-matched** per persona (E8.1(e)) | position, length, force | **imperative force without the mandate's content** |
| `wrapper_only` | the "ACTIVE MEMORY REFRESH … strictly adhere to your core mandate" framing with **no mandate** | position, the framing | the meta-instruction alone |

Cycle 2 made this the condition on which the paper's framing turns: if `placebo_directive` reproduces most of the
memory effect, the result is "any imperative at the recency position shifts a stateless agent, and content only
modulates the magnitude"; if it does not, the result is content attribution.

## 2. The design

**Roster** — `e9_roster.CAUSAL_OPEN`, the selection's core with gpt-oss-20b pruned (R_effect: its pooled band-MAS CI
includes 0, its cells cancelling) and **Gemma 4 31B** as the rule's top-up:

Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B, Phi-4, Gemma 4 31B.

**Cells.** 3 personas × 3 arms × 2 scenarios (flat, crash at δ 0.70) × seeds 10001–10060 × R = 1 =
**1,080 runs per model, 6,480 in all**.

**Why flat and crash only.** `GRID_EXPERIMENT_PLAN.md` 3 sizes E2 at these two: flat is where the headline's effect is
cleanest and crash is where Cycle 2's panic-selling question lives. bull_trap and sustained_bull are not run and no
claim is made about them.

**Why static and memory are not in the manifest.** They already exist, verified, on these exact seeds and market
paths at the same `Env_Code_Hash` — the first 60 of the headline's 122. Re-running them would spend about 12 GPU-hours
to reproduce rows already on disk. Every contrast below is formed against those stored rows.

**Manifest.** `e9_4/manifest_causal_open.json`, sha256
`e44d9c96f4e45f24556832ae42d6acc9ab701fa32ccd321cac5952b4c0b64cdd`, built by
`tools/phase9/e9_4_grid.py --stages manifest_stage2`; subdir `stage2_causal`. Its fingerprint holds the prompt hash of
every configuration × persona × arm, the `Env_Code_Hash` and the LF sha256 of the eight harness sources; the runner
refuses to start if any of them has moved.

**Cost.** 17.6 B200 GPU-hours at the headline's measured per-run cost (`e9_4/selection/cost.csv`).


## 2a. Power at S = 60, and the two models it does not cover

`HEADLINE_MODEL_SELECTION.md` 3.5 gives the seeds each model needs for band-MAS at Δ = 0.05, α′ = 0.05/36 and power
0.80, from its own largest-cell σ_d at 122 pairs per cell, with the band-MAS MDD this design actually achieves:

| model | S needed | MDD at S = 60 | in this experiment |
|---|---|---|---|
| OLMo 3.1 32B | 2 | 0.007 | yes |
| Phi-4 | 42 | 0.038 | yes |
| Llama 3.1 8B | 46 | 0.040 | yes |
| Gemma 4 31B | 52 | 0.042 | E2, E3 only |
| Gemma 4 E4B | 66 | 0.048 | yes |
| **gpt-oss-20b** | **224** | **0.088** | E4, E5 only |
| **Ministral 3 14B** | **246** | **0.093** | yes |

**Four of the six are covered at S = 60 or close to it. Two are not.** At 60 seeds the smallest difference this
design can detect for gpt-oss-20b is 0.088 and for Ministral 0.093, roughly **twice** the registered Δ of 0.05. A
null result in those two models' cells is therefore **uninformative about effects between 0.05 and 0.09**, and is
reported as such rather than as evidence of no effect. S = 60 is the plan's own count and the count Lingfei's
300 GPU-hours were quoted at; raising it to cover those two would multiply this experiment's cost by about four.
This is registered in advance, not discovered afterwards.

## 3. The confirmatory analysis

- **One family per model.** For model m, the family is {`placebo_declarative`, `placebo_directive`, `wrapper_only`}
  − `static`, × 3 personas × 2 scenarios × tier C's three metrics (band-MAS, D at θ 0.05, D at θ 0.002): **m = 54**.
  D's two θ are near-duplicates — |r| **0.894** over the 26,244 stage-1 runs these families are computed on;
  the 0.992 of `PHASE_8_REPORT.md` 365 is over 600 scripted-policy cell means, a different population, and the
  weaker figure is the one that applies here.
- **The test** is Phase 8's registered single-model analysis, `tools/stats_v2.run_stats_v21`: seed-level pairs, then
  the one-way path bootstrap `pigeonhole_ci` (1,999 draws, seed 0) for each cell's percentile interval and two-sided p.
  Cliff's δ beside.
- **The decision** is BH within the model's family at q = 0.05. A claim reads: *for model m, injecting this block
  changes this metric for persona p in scenario c, in the direction of the estimate.* **No claim about models in
  general is made from these tests.**
- **The absorption ratio**, the quantity the question turns on, is reported per model × persona × scenario:

  A = **sign-aligned**: ((placebo_directive − static) · s) / |memory − static|, where s = sign(memory − static)
  on band-MAS, so A is the share of the mandate's effect reproduced **in the mandate's own direction**.

  It is computed only on cells meeting **both** registered guards: the denominator's seed-cluster bootstrap CI
  excludes 0, **and** |memory − static| ≥ 0.01 (a fifth of Δ). Measured on stage 1's first 60 seeds over exactly
  these 36 cells, 34 denominators have a CI excluding 0 but **14 of those are negative** (memory *improves*
  band-MAS: Phi-4 ENTJ flat −0.375, Llama 3.1 8B ENTJ flat −0.220) and **two are ≈ 1.5 × 10⁻⁴** (Gemma 4 E4B ENTJ),
  so an unsigned ratio would mix opposite effects and a sign-only guard would admit |A| ≈ 77. The floor and the
  alignment are registered here, before E2 runs; the count of cells each guard excludes is reported.

  There is **no implementation of A in the repository**; it is written for this experiment, and its unit test
  reproduces a planted ratio on synthetic pairs before it touches a run. The same statistic is reported for
  `placebo_declarative` and `wrapper_only`.
- **How the function is called.** `run_stats_v21` iterates `tools/stats_v2.question_families()`, a **fixed** dict, and
  `seed_level_pairs` groups on (Model, Persona, Scenario_Cell, Seed, Arm) **ignoring `Setting`**. It is therefore
  called **once per model and once per setting**, on a frame holding only the rows of that comparison. A frame mixing
  settings would be averaged silently, with no error. The decision rule must read `bh_within`
  (`inference_params.decision_rule(1)`); if a frame yields more than one tier-C family the rule flips to `by_across`,
  and the run is re-framed rather than reported under a rule it did not use.
- **Before any claim,** per model and cell: the parse-fallback share, the **refusal rate**, the zero-trade share and the
  static arm's mean cash share (`GRID_EXPERIMENT_PLAN.md` 7, Cycle 2's precondition).
- **Completeness.** A model's family is read once `e9_4_grid --stages verify` passes for it: every planned run present
  with the manifest's prompt hash, `Env_Code_Hash`, configuration, scenario, seed and start design. A run abandoned
  after three non-ok attempts is reported missing. Nothing is imputed and no model is substituted.

## 4. Predictions, stated in advance

**P1 — the directive placebo absorbs less than 30 % of the mandate effect.** Median A over the model × persona ×
scenario cells where it is defined is below 0.30. *This is Cycle 2's own registered tripwire* (area-chair report,
GO condition 4). If A ≥ 0.30 the honest reading is imperative force, not content, and the paper says so.

**P2 — the declarative placebo absorbs least, the wrapper sits between.** A(declarative) ≤ A(wrapper_only) ≤
A(directive) on the median over defined cells. Rationale: each arm adds one more of the three ingredients.

**P3 — ISFJ moves under every arm.** The conservative persona's band-MAS rises (adherence worsens) under
`placebo_directive` in at least four of the six models. Rationale: on stage 1's 122 seeds, memory raises ISFJ's
band-MAS in **all nine** open-weight models measured (|t| 5.00 to 108.62), so ISFJ is the persona most sensitive to
anything injected at the recency position — the test is whether irrelevant imperative text does it too.

**P4 — Gemma 4 31B keeps its ENTJ sign.** Its ENTJ band-MAS rises under `placebo_directive` as it does under memory
(stage 1: +0.0800, t +19.1 — the only one of the nine whose ENTJ worsens). It is the rule's top-up precisely
because it carries that sign.

**How they are read.** Each is descriptive and outside every BH family. A wrong prediction is reported as wrong.

## 5. Exploratory, with no claim

R5 over the six with its power stated (P9-2: at most 0.55 at M = 6); tier S (turnover, MDD, return) in its own
families; the agreement of each cell's sign across models; the placebo's realised word and imperative counts per
persona against the matched target (E8.1(e)); seconds and tokens per run.

## 6. Not in this experiment

E3's common-start slice and its salience shares, E4's Track A, E5's generator sweep, E6's context length, E7, E8 and
the mechanistic appendix. Each has its own pre-registration. bull_trap and sustained_bull are not run here.

## 7. How it runs

One SLURM array on `hpg-b200` under fire-finai, at most four tasks at once, each 1 B200, 6 cores, 44 GB — within
Lingfei's caps of 4 GPUs, 24 cores and 180 GB (P9-12; our request is 4 x 44 = 176) across all the project's jobs. Each task loads its pinned Hugging Face
revision, serves it with its stage-1 vLLM arguments, runs the twelve-call parse preflight, then makes its calls at the
task's `--workers` under P9-20's per-server ceiling. Every run is checkpointed; a resubmission resumes the same
manifest or refuses to start.

**Before the first call:** the manifest's sha256 and this file's are recorded in `DECISION_LOG.md`, as P9-16 and P9-19
recorded stage 1's, with the cluster state checked at submission.

## 8. Deviations

Nothing above changes after the first run of this manifest. A deviation is recorded as a numbered addendum to this
file with its reason and with what had already been seen when it was made.
