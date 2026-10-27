# Pre-registration — Phase 9, stage 1 of the open-weight headline, second batch (E9.4)

Written 26 Oct 2026, before any run of `docs/env_v2/generated/v2_1/e9_4/manifest_headline_open_b2.json` and before any
of the first batch's six models is scored. It registers the second stage-1 batch (DECISION_LOG P9-17, P9-18): three
open-weight configurations that comparable published studies run. Everything `PREREG_PHASE_9_STAGE1_OPEN.md` fixes
stands for this batch unless section 0 names it.

---

## 0. What this file changes in PREREG_PHASE_9_STAGE1_OPEN.md

| Item | PREREG_PHASE_9_STAGE1_OPEN.md | Here | Decision |
|---|---|---|---|
| Roster | the six of `e9_roster.HEADLINE_OPEN` | the three of `e9_roster.HEADLINE_OPEN_B2` | P9-17 |
| Seeds per cell | 122, the paired count at the six's plug-in | **122**, the six's count; this batch's own paired count is 19 | P9-18 |
| Context length | `--max-model-len 32768` | Phi-4 at 16,384 tokens, its trained context | P9-17 |
| Model files | each from its Hugging Face revision | Llama 3.1 from NousResearch's open copy with Meta's `tokenizer_config.json`, checked file by file against Meta's revision | P9-17 |
| Where it runs | `$BASE/repo` | `$BASE/repo_b2`, a copy whose roster is this batch's | P9-17 |

**Unchanged:** the cells — ISFJ, INTJ and ENTJ; the static and memory arms; flat, bull_trap, crash (δ 0.70) and
sustained_bull; seeds 10001–10122; R = 1 — so the same 2,928 runs per model as the six; T = 200;
`harness_version = placebo_version = "v2_1"`; the default generator; P9-5's configuration rule (each model's default
configuration, temperature 0.2); `Env_Code_Hash` 1d689aaf82a33a2e; vLLM 0.29.0 on B200s at tensor parallel 1 with
`--gpu-memory-utilization 0.90 --enable-prefix-caching`; 64 in-flight calls (P9-11); and the analysis of section 3.

## 1. The design

**Roster.** Each configuration is pinned by Hugging Face revision and served by vLLM 0.29.0 with the shared flags above.

| Configuration | Lab | Size | Revision | Files | Further vLLM flags | Its variance pilot |
|---|---|---|---|---|---|---|
| `vllm/meta-llama/llama-3.1-8b-instruct` | Meta | 8.0B dense | `0e9e39f` | NousResearch copy `d10aef7`, Meta's `tokenizer_config.json` | none | `manifest_vllm_llama8.json`, job 47791909_0, B200, 26 Oct |
| `vllm/meta-llama/llama-3.1-70b-instruct` | Meta | 70.6B dense | `1605565` | NousResearch copy `d50656e`, Meta's `tokenizer_config.json` | none | `manifest_vllm_llama70.json`, job 47791909_1, B200, 26 Oct |
| `vllm/microsoft/phi-4` | Microsoft | 14.7B dense | `2db69c1` | its own | `--max-model-len 16384` in place of 32768 | `manifest_vllm_phi4.json`, job 47791909_2, B200, 26 Oct |

**Llama's files.** Llama 3.1 is gated, and no token is kept on the cluster account. The NousResearch copies equal Meta's
pinned revisions on every weight shard (4 and 30, by LFS sha256), the model and generation configs, the tokenizer and
the weight index (`e9_2/llama_meta_files.json`, read with an approved account on 26 Oct 2026). Only
`tokenizer_config.json` differs, and Meta's own is used (sha256 `177c7b61e616fecb84c17ce0591acb92c6c4d60e9ac5ababfb940ff23bbcd424`,
the same file for both sizes). `tools/cluster/assemble_llama.py` builds each served directory and refuses it unless every
file equals Meta's. Meta's chat template begins every system message with "Cutting Knowledge Date: December 2023" and
"Today Date: 26 Jul 2024". It is served as shipped, as P9-5's default configuration requires. The environment's dates
are Day-1 to Day-200, so nothing the model observes conflicts with that line.

**Phi-4's context.** Its 16,384 tokens are below the registered 32,768. The longest prompt in 400 sampled Gemma 4 31B
headline runs was 1,989 tokens, so no call comes near either limit.

Every configuration's static and memory prompts equal its pilot's, persona by persona, under the same `Env_Code_Hash`
(`tests/test_v2_1_phase_9.py::test_open_headline_b2_manifest_is_the_six_cells_and_its_pilots`).

**Cells.** The six's: 2,928 runs per model and 8,784 in all, each 200 simulated days with one decision a day.

**Manifest.** `e9_4/manifest_headline_open_b2.json` (sha256 `4780cb4eed79a4cf21d76c498b066ed1219459b12b3b72b311ca25f63ee1b82b`),
built by `tools/phase9/e9_4_grid.py --stages manifest_open_b2`, which refuses unless its cells equal the six's manifest;
subdir `stage1_open`; ledgers `e9_4/ledger_default_<slug>.jsonl`. Its fingerprint holds the prompt hash of every
configuration × persona × arm, the `Env_Code_Hash` and the LF sha256 of the eight harness sources, and the runner refuses
to run if any of them moves.

## 2. The seed count (P9-18)

- **This batch's own sizing** (`e9_2/sizing_open_b2.json`, sha256 `37b187e3319dd9ba120c4a39fce8d3fe9d80e3d9a7e697a40d5bc93489359c6c`,
  from `tools/phase9/e9_2_pilot.py --stages open_b2`): the rule of `PREREG_PHASE_9_STAGE1_OPEN.md` 2 over the three pilots
  (48 pairs and 36 df each) takes Llama 3.1 8B's 0.0538 as the plug-in and gives a paired count of **19**, with Appendix A
  as written giving 38.
- **The batch runs 122**, the six's count (P9-18, the user's decision of 26 Oct), so every comparison between these
  three and the six rests on the same 122 market paths in each cell. The count is set by comparability, not by this
  batch's power, and the extra seeds only raise that power.
- **Per model at 122 seeds**, by the same functions as the six's table:

| Configuration | σ_d | 90 % limit | Power at Δ = 0.05 | Paired MDD, band-MAS | D at θ 0.05 | D at θ 0.0020 |
|---|---|---|---|---|---|---|
| Llama 3.1 8B | 0.0454 | 0.0538 | > 0.999 | 0.0197 | 0.0267 | 0.0151 |
| Llama 3.1 70B | 0.0356 | 0.0422 | > 0.999 | 0.0154 | 0.0387 | 0.0227 |
| Phi-4 | 0.0226 | 0.0267 | > 0.999 | 0.0098 | 0.0351 | 0.0203 |

## 3. The confirmatory analysis

As `PREREG_PHASE_9_STAGE1_OPEN.md` 3, for each of the three models:

- **The family** is the model's own 36: memory − static × 3 personas × 4 scenario cells × tier C's three metrics
  (band-MAS, D at θ 0.05, D at θ 0.0020).
- **The test** is Phase 8's single-model analysis, `run_stats_v21`.
- **The decision** is BH within the family at q = 0.05.
- **Before any claim,** the parse-fallback share, the zero-trade share and the static arm's mean cash share are
  reported for each model and cell.
- **Completeness** is read from `e9_4_grid --stages verify`. Nothing is imputed, and no model is substituted.

No claim about models in general is made from these tests.

## 4. Predictions, stated from the pilots

The pilots ran seeds 3001–3004, disjoint from the headline's. The rule is `PREREG_PHASE_9_STAGE1_OPEN.md` 4's: a
direction is predicted for a model × persona where the pilot's memory − static band-MAS difference over its 16 pairs has
|t| ≥ 2 and |mean| ≥ 0.005. It is computed by `e9_2_pilot.pilot_predictions`, which reproduces the six's registered
table from their pilots (`test_pilot_predictions_reproduce_the_six_table`). Higher band-MAS is worse adherence.

| Configuration | ENTJ | INTJ | ISFJ |
|---|---|---|---|
| Llama 3.1 8B | lower (−0.254, t −10.7) | lower (−0.033, t −4.2) | higher (0.045, t 12.5) |
| Llama 3.1 70B | lower (−0.313, t −14.0) | none (0.003, t 0.3) | higher (0.020, t 4.1) |
| Phi-4 | lower (−0.327, t −19.0) | higher (0.044, t 10.2) | higher (0.021, t 6.9) |

- **P1b, per model and persona:** each direction in the table.
- **P3b, size within Llama:** Llama 3.1 8B's mean contrast over the 12 cells is smaller in absolute value than
  Llama 3.1 70B's. The pilot gave 0.080 against 0.097, both negative and driven by ENTJ. The six's P3 uses the same
  measure, and it reproduces that P3's 0.016 against 0.043.
- **How they are read:** as `PREREG_PHASE_9_STAGE1_OPEN.md` 4 reads them. Each estimate is pooled over the 4 scenarios
  × 122 seeds, and its sign is read against the prediction. The reading is descriptive and outside every BH family. A
  wrong prediction is reported as wrong.

## 5. Exploratory, with no claim

- Everything in `PREREG_PHASE_9_STAGE1_OPEN.md` 5, for these three models.
- Over all nine models: R5 in each cell × metric, with its power stated. M = 9 was not simulated; P9-2's table gives
  0.92 at M = 8 and 0.99 at M = 10 at half Flash's σ_d limit, and 0.24 and 0.43 at the full limit.
- Over all nine models: how often each cell's sign agrees, and in how many re-injecting the mandate raises ISFJ's
  band-MAS (the six's P2, counted over nine).

## 6. Not in this stage

As `PREREG_PHASE_9_STAGE1_OPEN.md` 6.

## 7. How it runs

- **One SLURM array.** `tools/cluster/headline_b2_b200.sbatch` runs on `hpg-b200` under fire-finai: three tasks, at
  most three at once, each with 1 B200, 6 cores and 44 GB. They run beside the first batch's last task, which makes
  4 GPUs, 24 cores and 176 GB across all of the project's jobs, within Lingfei's caps (this batch agreed 26 Oct).
- **Separate code.** It runs from `$BASE/repo_b2`, so the first batch's task keeps the harness its manifest
  fingerprints and can still resume.
- **Each task:**
  1. re-assembles and re-checks the Llama files (any mismatch stops the task);
  2. serves the model with its pilot's vLLM arguments;
  3. runs the twelve-call parse preflight;
  4. runs the runner at 64 in-flight calls, which checkpoints every run.
  
  A resubmission resumes the same manifest or refuses to start.
- **Estimate**, from each pilot's seconds per run and the first batch's pilot-to-headline ratios (1.12–1.25):
  - Llama 3.1 70B about 22–25 B200 GPU-hours;
  - Llama 3.1 8B and Phi-4 about 5–6 each;
  - about 33–37 in all, and about one day of wall-clock, with the 70B the long pole.

## 8. After the first run

Nothing above changes after the first run of this manifest. A deviation is recorded as a numbered addendum with its
reason. The fingerprint refusal keeps cells, prompts and seeds from moving silently.
