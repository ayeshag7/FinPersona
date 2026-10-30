# Pre-registration — Phase 9, stage 2, E5: the generator sweep (robustness to market parameters)

**DRAFT, 30 Oct 2026 — not yet registered.** It becomes the registration when the team approves it, and no run of
`docs/env_v2/generated/v2_1/e9_4/manifest_sensitivity_open.json` may start before then. Nothing of this experiment
has run. Where it changes `PREREG_PHASE_9.md` 4.1 and the plan's 13.3, the change is named in section 0.

---

## 0. What this file changes in PREREG_PHASE_9.md 4.1 and plan 13.3

| Item | As registered | Here | Decision |
|---|---|---|---|
| Which parameters | the plan's six, named by reviewers | the **data-driven six** | **P9-6** (they share only 3 with the plan's, where the rule asks for 5) |
| Levels | two per parameter | unchanged: two per parameter, **12 non-default levels** | E9.1 |
| The default level | run as a 13th level | **read from the 122 stage-1 seeds already on disk** | **P9-21** |
| Roster | the 13 API configurations | the six of `e9_roster.CORE_OPEN` | `HEADLINE_MODEL_SELECTION.md` 4.3 |
| Seeds per level | Appendix A on the API sizing | **60**, the first 60 of the headline's | plan 3; section 2 |
| Sign criterion | plan 13.3's sentence as written | the **significant-only** reading is the headline, the plain reading reported beside | team decision, **P9-23**, backfilling `history/SYNTHETIC_ENVIRONMENT_HISTORY.md` 16.3 — see §0a |
| Concurrency | 15 workers per model | per-server, under a 256 ceiling | P9-20 |

**Unchanged:** the three personas, the two arms and the four scenarios; T = 200; R = 1; `harness_version =
placebo_version = "v2_1"`; dividends paid; start at the band centre; temperature 0.2; the generator **code** at
`Env_Code_Hash` **1d689aaf82a33a2e** — only its parameters move.

### 0a. The sign criterion's provenance — unresolved, and E5 does not start until it is

DECISION_LOG **P9-9** (12 Sep) left the three criteria "exactly as registered", and `PHASE_9_REPORT.md` 5 lists the
reading as a decision **for the team**. The team then took it: `history/SYNTHETIC_ENVIRONMENT_HISTORY.md` 16.3 records
that "the sign criterion uses the significant-only reading as its headline … the plain reading is reported beside it
because it is the plan's sentence." That decision had no DECISION_LOG row until **P9-23** (30 Oct) recorded it, with its
measured rates and the alternative rejected. Both readings were constructed in `PREREG_PHASE_9_ADDENDUM.md` 9
**before** the stage produced a number, so neither was written after seeing which read better. An earlier draft of this file cited `PHASE_9_REPORT.md` 16.3; that section does not exist.

## 1. The question

Every conclusion the benchmark draws is drawn inside one synthetic market. E5 asks whether those conclusions survive
when the market's own fitted parameters are moved to the ends of their confidence intervals. It is the experiment
Phase 9 exists for, and the robustness table (E9.5) is its output.

## 2. The design

**The six parameters** are E9.1's data-driven six, ranked by the standardised effect of each parameter's larger level
on the level-free oracle's regret and on the scripted policies' band-MAS, with a 1,000-resample seed bootstrap for
top-six stability (`e9_1/ranking.json`): **the GARCH set, `sbar`, `mu_V`, the half-life, `sigma_V`, the jump rate**.
Three reviewer-named parameters fell out, each moving the scripted policies by at most 0.002: the P/E dispersion, the
analyst sd and the sentiment loading.

**The twelve levels**, taken from `tools/phase9/e9_1_ranking.level_configs()` — the same code that produced the
ranking, so the levels the sweep runs are the levels the ranking ranked:

| Level | Generator override |
|---|---|
| `garch_set__low` / `__high` | α 0.0190 / 0.0417, γ 0.0434 / 0.0764, β 0.9457 / 0.9157, ν 4.291 / 5.742 |
| `sbar__low` / `__high` | sbar 0.013425 / 0.016776 |
| `mu_V__low` / `__high` | mu_V −5.13 × 10⁻⁵ / +4.787 × 10⁻⁴ |
| `half_life__low` / `__high` | engine `ar1_fit_hl18.7499` / `ar1_fit_hl32.6393`, with sbar re-matched to 0.016360 / 0.012705 |
| `sigma_V__low` / `__high` | sigma_V 0.012750 / 0.015269 |
| `jump_rate__low` / `__high` | jump rate 4.607 × 10⁻⁴ / 8.165 × 10⁻⁴ per day |

The half-life levels carry a matched `sbar` so that the stationary sd of the mispricing is held while its persistence
moves; the registered construction lands within +5.3 % and +0.8 % of its target and is applied once, not iterated.

**Roster** — `e9_roster.CORE_OPEN`: Gemma 4 E4B, gpt-oss-20b, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B, Phi-4.

**Cells.** 12 levels × 3 personas × (static, memory) × 4 scenarios × seeds 10001–10060 × R = 1 =
**17,280 runs per model, 103,680 in all**. Each level is its own `setting` (`sens_<level>`), which
`e9_runner.cfg_for` makes a path and run-key component, and the level's override rides on the cell as `env_config`,
which `cfg_for` passes to `SyntheticMarketEnv`.

**How often each level actually changes the market, measured before any run.** Regenerating all twelve levels and
the default over the sweep's own 240 (scenario, seed) paths and hashing each price series:

| Level | Paths changed, of 240 |
|---|---|
| `garch_set`, `sbar`, `mu_V`, `half_life`, `sigma_V` (ten levels) | **240 / 240 = 100 %** |
| `jump_rate__high` | **61 / 240 = 25.4 %** (flat 16, bull_trap 13, crash 16, sustained_bull 16) |
| `jump_rate__low` | **41 / 240 = 17.1 %** (flat 10, bull_trap 10, crash 10, sustained_bull 11) |

Jumps are rare by construction — the fitted rate is 5.825 x 10⁻⁴ a day, so over 200 days plus a 750-day burn-in most
paths draw no jump at either level and the shared uniform stream reproduces the default's path exactly. `Gen_Config_Hash`
still differs on those runs, because the rate is part of the hashed configuration, so no hash check can see it.

**What follows from that, registered here rather than discovered afterwards.** The two `jump_rate` levels are run as
the design registers them — a parameter set fixed by P9-6 is not re-chosen after seeing a measurement — but their
**primary verdict is read on the paths the level actually changed** (61 and 41 of 240), with the full 240 reported
beside it as the sensitivity, and the share above printed in the robustness table's `jump_rate` rows so the verdict
carries its real n. On the unchanged paths the level-versus-default contrast is decoding noise at temperature 0.2
and would otherwise pull those rows toward *robust* by construction, which is P1. Roughly 30 of E5's 225 GPU-hours
re-measure the default market; that is the price of leaving a registered parameter set alone, and it is stated here.

**The default level is not run.** P9-21: it is read from the headline's 122 seeds, already verified at the same
`Env_Code_Hash`, which adds data (122 pairs against 60) and removes about 19 GPU-hours of runs. Every level is
compared with the default on **common random seeds** — the sweep's 60 are the first 60 of the headline's — and
not on identical market paths: changing a generator parameter changes the path, which is the point of a sweep.
`pigeonhole_ci` clusters on `Scenario_Cell|Seed`, so the cluster is the seed.

**The check that the levels took effect.** `Env_Code_Hash` cannot see a parameter change — the code is identical and
only the values passed to it differ — so a level whose `env_config` never reached the generator would verify clean
and silently be the default under another name. `e9_4_grid --stages verify` therefore also requires that, on any one
(configuration, scenario, seed), the twelve settings map to **twelve distinct `Gen_Config_Hash` values**, and that a
setting produces one hash throughout. A collision fails verification and the level is re-run, never reported.

**Manifest.** `e9_4/manifest_sensitivity_open.json`, sha256
`11d50d6698239927d50cf5598183df5fdc94697bfb2b7a0499f489242d767b6c`, subdir `stage2_sens`.

**Cost.** 225.2 B200 GPU-hours — three quarters of stage 2's total, and the long pole of the week.


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

## 3. The analysis: the robustness table (E9.5)

One row per **conclusion** × **generator parameter**. A conclusion is a stage-1 cell whose memory − static contrast
was significant under BH within its model's family of 36. Columns, as plan 13.3 fixes them and P9-9 measured them:

1. **The sign at each level**, under both readings:
   - *significant-only* (**the headline**): a conclusion is level-dependent only if the contrast is significant at
     some level with the opposite sign. Measured false-flag rate at most 0.008.
   - *plain* (the plan's sentence as written): level-dependent if the sign differs at any level, significant or not.
     Reported beside, because it is what the plan says — and because it falsely declares a conclusion
     level-dependent up to 0.241 of the time when the effect is identical at every level, and about 0.60 when there
     is no effect at all.
2. **R5's p-value at each level** — the two-way random-effects variance referred to t(M − 1) — with BH within the
   stage-1 family the conclusion came from. Its power at M = 6 is at most 0.55 at a between-model sd of half the
   plug-in and at most 0.09 at the full limit, and that is printed in the table rather than left for the reader.
3. **The level × arm interaction's 90 % interval** on t(M − 1), against the registered equivalence margin of
   **0.025**, half the minimum effect. Its power is 0.993–1.000 when there is no level × arm × model term and
   0.086–0.668 when there is one at half the measured spread; false equivalence at the margin is at most 0.095.
4. **A verdict** — robust / level-dependent / not equivalent — with **each criterion reported separately**. No
   criterion is collapsed into another, and criterion (ii), which holds 0.03–0.05 of the time at M = 6 against
   0.58–0.63 at M = 14, is reported with that rate beside it.

**How the function is called.** `run_stats_v21` iterates `tools/stats_v2.question_families()`, a **fixed** dict, and
`seed_level_pairs` groups on (Model, Persona, Scenario_Cell, Seed, Arm) **ignoring `Setting`**. It is therefore called
**once per model and once per level**, on a frame holding only that level's rows beside the stage-1 default's. A single
call over all twelve `sens_*` settings would average the levels into one number silently, with no error, and would run
BH over 12 x 36 rows in one family. The decision rule must read `bh_within`.

**Before any claim:** the parse-fallback, zero-trade and static-arm cash share per model × level × cell, and the
share of cells where MCR is undefined (the 75th-percentile GJR set left 4.25 % of path × persona cells with no
resolvable day at θ 0.05, handled pairwise-complete as registered in addendum 4).

**Completeness** as in E2, plus the `Gen_Config_Hash` requirement above.

## 4. Predictions, stated in advance

**P1 — most conclusions are robust.** At least two thirds of the conclusion × parameter rows return *robust* under
the significant-only reading. Rationale: E9.1 measured every one of the six at a standardised effect of 0.096 or
less on outcomes that contain no LLM, and the levels are confidence-interval endpoints, not regime changes.

**P2 — the GARCH set moves the most rows.** Of the six, it produces the largest number of level-dependent verdicts.
Rationale: it ranks first on both E9.1 criteria (0.096 on the oracle, 0.086 on the scripted policies) with a top-six
bootstrap share of 1.000, and it is the level that leaves cells unresolvable.

**P3 — the plain reading inflates level-dependence.** It returns more level-dependent verdicts than the
significant-only reading, on at least three of the six parameters. This is a prediction about the *criterion*, not
about the environment, and it is why P9-9 put the two readings side by side.

**P4 — ISFJ's worsening under memory is robust everywhere.** The conclusion "memory raises ISFJ band-MAS" holds its
sign at all 12 levels in at least five of the six models. Rationale: on stage 1's 122 seeds it holds in all nine
open-weight models measured, with |t| from 5.0 to 108.6 — the largest and most consistent effect the headline found.

**How they are read.** Descriptive, outside every BH family. A wrong prediction is reported as wrong.

## 5. Exploratory, with no claim

The level × model interaction; whether a parameter's effect on LLM behaviour agrees in rank with its E9.1 effect on
the oracle and the scripted policies (a parameter that ranks low there and moves LLM behaviour here is evidence
about the models, which the pre-registration states in advance); tier S; seconds and tokens per run per level.

## 6. Not in this experiment

E2's placebo arms, E3's slice and shares, E4's Track A, E6's context length, E7, E8 and the mechanistic appendix.
The three reviewer-named parameters that E9.1's rule excluded are not swept. The `half_life_unmatched` levels belong
to the E9.1 ranking, which ran without any LLM and is already done; they are not run here.

## 7. How it runs

As E2 to E4: one SLURM array on `hpg-b200` under fire-finai, at most four tasks at once, 1 B200 / 6 cores / 44 GB
each, pinned revisions, the twelve-call parse preflight, checkpointed runs, P9-20's per-server concurrency.

**Because this is three quarters of the week's GPU-hours**, each task's first two blocks run at two concurrency
settings and the rest at whichever was faster, measured from the task's own ledger. Those blocks are real E5 runs, so
the measurement costs nothing; the concurrency used is logged per row, and it changes when calls are served, not the
cells, prompts, seeds or decoding settings.

The manifest's sha256 and this file's are recorded in `DECISION_LOG.md` before the first call, with the cluster
state checked at submission.

## 8. Deviations

Nothing above changes after the first run of this manifest. A deviation is recorded as a numbered addendum to this
file with its reason and with what had already been seen when it was made.
