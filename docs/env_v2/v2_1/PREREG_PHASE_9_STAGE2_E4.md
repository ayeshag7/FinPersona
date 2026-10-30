# Pre-registration — Phase 9, stage 2, E4: Track A (stated vs unstated target)

**DRAFT, 30 Oct 2026 — not yet registered.** It becomes the registration when the team approves it, and no run of
`docs/env_v2/generated/v2_1/e9_4/manifest_track_a_open.json` may start before then. Nothing of this experiment has
run. Where it changes `PREREG_PHASE_9.md` 4.1, the change is named in section 0.

---

## 0. What this file changes in PREREG_PHASE_9.md 4.1

| Item | PREREG_PHASE_9.md 4.1 | Here | Decision |
|---|---|---|---|
| Track | B throughout (the target is not stated) | the headline cells at **track = A** | plan 3 (E4); the pre-grid build `40fe8be` |
| Roster | the 13 API configurations | the six of `e9_roster.CORE_OPEN` | `HEADLINE_MODEL_SELECTION.md` 4.3 |
| Seeds per cell | Appendix A on the API sizing | **60**, the first 60 of the headline's | plan 3 |
| Confirmatory test | R5 over the roster | each model its own family; R5 exploratory | P9-14, carried |
| Concurrency | 15 workers per model | per-server, under a 256 ceiling | P9-20 |

**Unchanged:** the three personas, the two arms and the four scenarios; T = 200; R = 1; `harness_version =
placebo_version = "v2_1"`; dividends paid; start at the band centre; the default generator at `Env_Code_Hash`
**1d689aaf82a33a2e**; temperature 0.2.

## 1. The question

The benchmark scores how far the agent's cash share sits from its mandate's band — but under Track B **the band is
never stated in the prompt**. The agent is given a persona and a strategy in words, and graded against a number it
was not told. Cycle 1 found that the v1 metric was "distance to an uncommunicated target", and Cycle 2's area chair
named the repair: run a **communicated-target track** beside the revealed-preference one, so that the contrast
between them becomes a designed axis rather than a confound.

Track A appends `track_a_statement(persona)` to the system prompt: the persona's cash band, stated. Everything else
is the headline cell. E4 therefore asks: **when the agent is told the number it is graded on, does it hit it — and
does re-injection still matter once it knows?**

This is the one axis the comparable corpus does not own.

## 2. The design

**Roster** — `e9_roster.CORE_OPEN`, the selection's core: Gemma 4 E4B, gpt-oss-20b, OLMo 3.1 32B, Ministral 3 14B,
Llama 3.1 8B, Phi-4. (Unlike E2 and E3, nothing is pruned: R_effect is not required to ask whether stating the target
changes behaviour.)

**Cells.** The headline grid cell for cell — 3 personas × (static, memory) × 4 scenarios × seeds 10001–10060 ×
R = 1 = **1,440 runs per model, 8,640 in all** — each carrying `factors: {"track": "A"}` and the setting `track_a`,
which is a path and run-key component so a Track-A run can never collide with its Track-B twin.

**The Track-B side is the headline's stored runs** on the same seeds, paths and `Env_Code_Hash`. Nothing is re-run.

**A note on the prompt hash.** Track A is the first grid factor that changes the rendered prompt, which is why the
fingerprint is keyed by prompt-affecting factors (`e9_runner.prompt_key`, fixed in `7886b74`). The manifest therefore
stores the Track-A hash, and `--stages verify` compares every run against it. Measured: `7f7a69e0550e85e5` at A
against `2cf22a92f78cb5d0` at B.

**Manifest.** `e9_4/manifest_track_a_open.json`, sha256
`c2c33af1c7784e27b384212572513a89ff635ffd95a9bd3a012cab63869062fa`, subdir `stage2_track_a`.

**Cost.** 18.8 B200 GPU-hours.


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

- **One family per model**: (track A − track B) × 3 personas × 4 scenarios × tier C's three metrics, within arm,
  **m = 36** per arm and **72** in all for the model. The two arms are reported as two questions in one family, and
  the family size is written beside every q-value.
- **The pairing is by seed and path**: a Track-A run and its Track-B twin share the scenario, seed, persona, arm and
  generator configuration, so `seed_level_pairs` pairs them exactly as it pairs memory with static. The test is
  `tools/stats_v2.run_stats_v21`'s one-way path bootstrap, 1,999 draws, seed 0.
- **Construction.** The Track-B rows are the headline's, filtered to seeds 10001–10060 and relabelled `static_B` /
  `memory_B`; the Track-A rows keep `static` / `memory`. The relabelling is mechanical and is recorded in the
  analysis script, so the contrast `static − static_B` is "stating the target, arm held fixed".
- **The decision** is BH within the model's family at q = 0.05. A claim reads: *for model m, stating the band changes
  this metric for persona p in scenario c under this arm, in the direction of the estimate.*
- **How the function is called.** `run_stats_v21` iterates `tools/stats_v2.question_families()`, a **fixed** dict, and
  `seed_level_pairs` groups on (Model, Persona, Scenario_Cell, Seed, Arm) **ignoring `Setting`**. It is therefore
  called **once per model and once per setting**, on a frame holding only the rows of that comparison. A frame mixing
  settings would be averaged silently, with no error. The decision rule must read `bh_within`
  (`inference_params.decision_rule(1)`); if a frame yields more than one tier-C family the rule flips to `by_across`,
  and the run is re-framed rather than reported under a rule it did not use.
- **Before any claim:** parse-fallback, zero-trade and static-arm mean cash share per cell, as always.
- **Completeness** as in E2.

## 4. Predictions, stated in advance

Stage 1's static-arm band-MAS on 122 seeds gives each cell's **headroom** — how far the agent sits from its band when
not told. Pooled over scenarios:

| | ENTJ | INTJ | ISFJ |
|---|---|---|---|
| Gemma 4 E4B | 0.000 | 0.383 | 0.082 |
| gpt-oss-20b | 0.346 | 0.261 | 0.061 |
| OLMo 3.1 32B | 0.011 | 0.113 | 0.074 |
| Ministral 3 14B | 0.117 | 0.338 | 0.079 |
| Llama 3.1 8B | 0.432 | 0.165 | 0.029 |
| Phi-4 | 0.372 | 0.135 | 0.067 |

**P1 — stating the target reduces band-MAS.** The Track A − Track B contrast on band-MAS is negative in at least
two thirds of the 72 model × persona × scenario × arm cells, and significant in that direction in at least half.
Rationale: v1's O3 ablation, which stated the target in words, pegged MAS at 0.000 for the conservative archetype in
both arms on all three models tested.

**P2 — the reduction tracks the headroom.** Across the 18 model × persona cells, the Spearman correlation between
static-arm band-MAS (above) and the size of the Track-A reduction is at least +0.5. Cells with headroom below 0.05
(Gemma 4 E4B ENTJ 0.000, OLMo ENTJ 0.011, Llama 3.1 8B ISFJ 0.029) cannot improve much and are predicted to move by
less than 0.02.

**P3 — the memory effect shrinks under Track A.** For each model, the mean |memory − static| on band-MAS is smaller
at Track A than at Track B. Rationale: if the band is in the system prompt on every call, re-injecting the mandate
adds less that the agent did not already have.

**P4 — ISFJ's worsening under memory survives in at least three models.** Stage 1 found it in all nine measured;
stating the target is predicted to reduce but not reverse it.

**How they are read.** Descriptive, outside every BH family. A wrong prediction is reported as wrong. P3 in
particular is the one that would most change the paper if it failed: a memory effect that is *unchanged* when the
target is stated is evidence the effect is not about knowing the target at all.

## 5. Exploratory, with no claim

R5 over the six with its power stated; tier S in its own families; the share of Track-A runs whose mean cash share
falls inside the stated band; the restatement probe where it is logged; seconds and tokens per run.

## 6. Not in this experiment

E2's placebo arms, E3's slice and shares, E5's generator sweep, E6, E7, E8 and the mechanistic appendix. No claim is
made about Track A on bull_trap or sustained_bull beyond the registered cells, and none about any model outside the
core.

## 7. How it runs

As E2 and E3: one SLURM array on `hpg-b200` under fire-finai, at most four tasks at once, 1 B200 / 6 cores / 44 GB
each, pinned revisions, the twelve-call parse preflight, checkpointed runs, P9-20's per-server concurrency. The
manifest's sha256 and this file's are recorded in `DECISION_LOG.md` before the first call.

## 8. Deviations

Nothing above changes after the first run of this manifest. A deviation is recorded as a numbered addendum to this
file with its reason and with what had already been seen when it was made.
