# Pre-registration — Phase 9, stage 2, E3: the common-start slice (persona vs mandate attribution)

**DRAFT, 30 Oct 2026 — not yet registered.** It becomes the registration when the team approves it, and no run of
`docs/env_v2/generated/v2_1/e9_4/manifest_slice_open.json` may start before then. Nothing of this experiment has run.
Where it changes `PREREG_PHASE_9.md` 4.1, the change is named in section 0; everything 4.1 fixes that section 0 does
not name stands.

---

## 0. What this file changes in PREREG_PHASE_9.md 4.1

| Item | PREREG_PHASE_9.md 4.1 | Here | Decision |
|---|---|---|---|
| Where the slice sits | inside stage 1 | its own stage-2 experiment | **P9-14** (deferred out of stage 1) |
| Roster | the 13 API configurations | the six of `e9_roster.CAUSAL_OPEN` | `HEADLINE_MODEL_SELECTION.md` 4.3 |
| Seeds per cell | Appendix A on the API sizing | **60**, the first 60 of the headline's | plan 3; section 2 |
| Reference level | NONE **and** the O3 numerical-only persona | **NONE only** | P8-14 (O3 cannot run on v2 and its text contradicts the bands) |
| Concurrency | 15 workers per model | per-server, under a 256 ceiling | P9-20 |

**Unchanged:** the three personas and the four scenarios; T = 200; R = 1; `harness_version = placebo_version =
"v2_1"`; dividends paid; the default generator at `Env_Code_Hash` **1d689aaf82a33a2e**; temperature 0.2.

## 1. The question

How much of what the agent does is the **persona text**, how much the **mandate directive**, and how much the
**allocation it was started from**?

Phase 8 showed this is answerable only on one design. Under the headline's start-at-target the start block is a
deterministic function of the persona (R² 1.000, canonical correlation 1.000), so a surrogate splits one persona
effect arbitrarily — 0.697/0.262 in one window and 0.914/0.051 in an identically generated one. With a **common
start** and a **no-persona reference**, the same known-answer design recovers the planted share stably (S_persona
0.979 [0.974, 0.984], 200 refits per window). The shares are therefore reported **only** here, and nowhere else.

The same cells also bear on Phase 7's day-1 separability gate, **but they do not make its null computable**:
`tools/report_v2.py` `gate_tables` needs at least two distinct no-persona labels and this slice has one (`NONE`),
so the null returns NOT COMPUTABLE. **P8-14** recorded exactly this when it kept NONE alone — the D11 question's
claim that the reference cells make the gate computable was true only with O3, which cannot run on v2. The gate's
**persona side** (the three personas at a common start) is computable here and is reported; its null is not, and
no prediction is made about it.

## 2. The design

**Roster** — `e9_roster.CAUSAL_OPEN`: Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B, Phi-4, Gemma 4 31B.
gpt-oss-20b is pruned by R_effect as in E2, with Gemma 4 31B the rule's top-up.

**Cells**, every one at `start_design="common"`, setting `common_start`:

- 3 personas × 3 arms (`static`, `memory`, `swapped`) × 4 scenarios × seeds 10001–10060 = 2,160; plus
- the no-persona reference: `NONE` × `trader` × 4 scenarios × the same 60 seeds = 240.

**2,400 runs per model, 14,400 in all.**

**The `swapped` arm** gives ISFJ the ENTJ mandate and ENTJ the ISFJ mandate, persona text unchanged. It is what
separates "the agent follows the text it was given" from "the agent behaves as its persona label says".

**Why the headline's rows cannot serve.** They are start-at-target. The slice exists because that design does not
identify the shares; its cells are a different experiment on the same paths, and the `common_start` setting keeps
their run keys and output paths from colliding with the headline's.

**Manifest.** `e9_4/manifest_slice_open.json`, sha256
`3aae426f3f532494697be697e56123e62367da0e3d25a76bf97b5ebfa7ccc033`, subdir `stage2_slice`.

**Cost.** 39.2 B200 GPU-hours.


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

- **One family per model**, as in stage 1 and E2: {`memory`, `swapped`} − `static` × 3 personas × 4 scenarios ×
  tier C's three metrics = **m = 72**, decided by BH within the family at q = 0.05, through
  `tools/stats_v2.run_stats_v21` (seed-level pairs, `pigeonhole_ci` at 1,999 draws, seed 0). Cliff's δ beside.
- **The salience shares** are computed by `evaluation/salience.py` `salience_by_window(identification="v2_1")` on
  this slice only, with the **seed-cluster bootstrap at 200 refits per window** and the fold-leak fix of P8-18 (a
  resampled seed's copies must not land in different cross-validation folds). The NONE trader is the reference level.
  Shares are reported with their intervals and **never** pooled with any start-at-target run.
- **The day-1 gate's persona side** is computed by `tools/report_v2.py` `gate_tables`, which drives
  `evaluation/salience.py` `separability_gate(day1)` — **not** `evaluation/separability_gate.py`, which is a v1-only
  script with no `results_v2` path. Its **null is NOT COMPUTABLE** under NONE alone (P8-14), is reported as such, and
  carries no prediction. `identification_check` will flag `identified_as_registered = false` on clause (i), the known
  addendum-10 artefact at common start; every share row carries that flag.
- **How the function is called.** `run_stats_v21` iterates `tools/stats_v2.question_families()`, a **fixed** dict, and
  `seed_level_pairs` groups on (Model, Persona, Scenario_Cell, Seed, Arm) **ignoring `Setting`**. It is therefore
  called **once per model and once per setting**, on a frame holding only the rows of that comparison. A frame mixing
  settings would be averaged silently, with no error. The decision rule must read `bh_within`
  (`inference_params.decision_rule(1)`); if a frame yields more than one tier-C family the rule flips to `by_across`,
  and the run is re-framed rather than reported under a rule it did not use.
- **Before any claim:** the parse-fallback share, the refusal rate, the zero-trade share and the static arm's mean cash share per cell.
- **Completeness** as in E2: `--stages verify` must pass for a model before its family is read.

## 4. Predictions, stated in advance

**P1 — the persona share dominates the directive share.** S_persona > S_directive in at least five of the six models.
Rationale: Phase 8's known-answer recovery on this design gave S_persona 0.979 with S_directive's upper limit
9.4 × 10⁻⁵. The interval on S_directive is reported as measured; "it covers 0" is not claimed, because P8-18 recorded
that it fails by construction.

**P2 — the swapped mandate moves behaviour toward the text, not the label.** For ISFJ under `swapped` (given the ENTJ
mandate), the mean cash share falls relative to ISFJ under `static`; for ENTJ under `swapped` it rises. Significant
in the registered direction in at least four of the six models, for at least one scenario each. *This is Cycle 2's
registered P2 prediction* (area-chair report, GO condition 4: "swapped-mandate: cash shift follows injected text").

**P3 — ISFJ worsens under memory here too.** Common start does not remove the pattern stage 1 found at
start-at-target: ISFJ's band-MAS rises under `memory` in at least five of the six models. On stage 1's 122 seeds it
rose in all nine measured (|t| 5.00 to 108.62).

**P4 — the persona side of the day-1 gate separates poorly.** Macro one-versus-rest AUC of the day-1 cash share
against the persona is below 0.65 in at least four of the six models. Rationale: on v1 the full gate was failed by
**0 of 18** models, and nothing in v2.1 was tuned to make day-1 allocations separate. The gate's null is not
computed (above), so no pass/fail verdict is registered — only the AUC.

**How they are read.** Descriptive, outside every BH family. A wrong prediction is reported as wrong.

## 5. Exploratory, with no claim

R5 over the six with its power stated; tier S in its own families; the shares by window across the run; the
agreement of each cell's sign with the headline's start-at-target estimate on the same paths; seconds and tokens
per run.

## 6. Not in this experiment

E2's placebo arms, E4's Track A, E5's generator sweep, E6, E7, E8 and the mechanistic appendix. The O3 numerical-only
reference is not run (P8-14). No share is reported from any other design.

## 7. How it runs

As E2: one SLURM array on `hpg-b200` under fire-finai, at most four tasks at once, 1 B200 / 6 cores / 44 GB each,
pinned revisions, the twelve-call parse preflight, checkpointed runs, P9-20's per-server concurrency. The manifest's
sha256 and this file's are recorded in `DECISION_LOG.md` before the first call.

## 8. Deviations

Nothing above changes after the first run of this manifest. A deviation is recorded as a numbered addendum to this
file with its reason and with what had already been seen when it was made.
