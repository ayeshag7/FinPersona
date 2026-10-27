# Pre-registration — Phase 9, stage 1 of the open-weight headline (E9.4)

Written 24 Oct 2026, before any run of `docs/env_v2/generated/v2_1/e9_4/manifest_headline_open.json`. It registers
stage 1 for the six open-weight configurations the headline now runs first (DECISION_LOG P9-12, P9-13), and it is the
stage-1 pre-registration `GRID_EXPERIMENT_PLAN.md` lists as O5. Where it changes `PREREG_PHASE_9.md` 4.1, the change
is named in section 0 with its decision. Everything 4.1 fixes that section 0 does not name stands.

---

## 0. What this file changes in PREREG_PHASE_9.md 4.1

| Item | PREREG_PHASE_9.md 4.1 | Here | Decision |
|---|---|---|---|
| Roster | the 13 configurations of P9-2 | the six of `e9_roster.HEADLINE_OPEN` | P9-12, P9-13 |
| Seeds per cell | E9.2's count, Appendix A as written | **122**, the paired-correct count | P9-13 |
| Confirmatory test | R5 over the M models in each cell × metric, one family of 36 | **each model's own family of 36**; R5 exploratory | P9-14 |
| D11 common-start slice | in stage 1, after each model's headline cells | deferred to the later experiments | P9-14 |
| Concurrency | 15 workers per model | 64 in-flight calls per model served by our own vLLM | P9-11, approved in P9-14 |
| Where it runs | the providers' APIs | vLLM 0.29.0 on HiPerGator B200s | P9-12 |

**Unchanged:** the static and memory arms; ISFJ, INTJ and ENTJ; flat, bull_trap, crash (δ 0.70) and sustained_bull; the
default generator; T = 200; R = 1; `harness_version = placebo_version = "v2_1"`; dividends paid; start at the band
centre; seeds from 10001, the same for every model, persona and scenario; P9-5's configuration rule (each model's
default configuration, temperature 0.2 where accepted); `Env_Code_Hash` 1d689aaf82a33a2e.

## 1. The design

**Roster.** Each configuration is pinned by Hugging Face revision and served by vLLM 0.29.0 with
`--max-model-len 32768 --gpu-memory-utilization 0.90 --enable-prefix-caching`, tensor parallel 1, plus the flags below.

| Configuration | Lab | Size | Revision | Further vLLM flags | Its variance pilot |
|---|---|---|---|---|---|
| `vllm/google/gemma-4-31b-it` | Google | 30.7B dense | `842da37` | none | `manifest_vllm_gemma.json`, RTX PRO 6000, 18 Sep |
| `vllm/google/gemma-4-e4b-it` | Google | 8.0B dense | `ee0ef60` | none | `manifest_vllm_gemmae4b.json`, RTX PRO 6000, 18 Sep |
| `vllm/openai/gpt-oss-20b` | OpenAI | 20.9B MoE | `6cee5e8` | none | `manifest_vllm_gptoss.json`, job 42551139, RTX PRO 6000, 18 Sep |
| `vllm/meta/muse-glimmer-30b` | Meta | 29.8B dense | `a4e59da` | `--reasoning-parser muse_glimmer` | `manifest_vllm_glimmer.json`, job 47436265_0, B200, 24 Oct |
| `vllm/allenai/olmo-3.1-32b-instruct` | AI2 | 32.2B dense | `ac0587e` | none | `manifest_vllm_olmo31.json`, job 47436265_2, B200, 24 Oct |
| `vllm/mistralai/ministral-3-14b-instruct-2512` | Mistral | 13.9B dense | `3cea74c` | `--tokenizer-mode mistral --config-format mistral --load-format mistral` | `manifest_vllm_ministral14.json`, job 47436790_3, B200, 24 Oct |

Every configuration's static and memory prompts equal its pilot's, persona by persona, under the same `Env_Code_Hash`
(`tests/test_v2_1_phase_9.py::test_open_headline_manifest_is_its_sizing_and_its_pilots`).

**Cells.** 3 personas × (static, memory) × 4 scenarios × seeds 10001–10122 × R = 1: **2,928 runs per model and 17,568
in all**, each 200 simulated days with one decision a day.

**Manifest.** `e9_4/manifest_headline_open.json` (sha256 `736b5bc8ccf30987aa08191339111a464c771f6566a5e9c072ec7cac428d8613`),
built by `tools/phase9/e9_4_grid.py --stages manifest_open`; subdir `stage1_open`; ledgers
`e9_4/ledger_default_<slug>.jsonl`. Its fingerprint holds the prompt hash of every configuration × persona × arm, the
`Env_Code_Hash` and the LF sha256 of the eight harness sources, and the runner refuses to run if any of them moves.

## 2. The seed count (P9-13)

- **Plug-in:** the largest one-sided 90 % chi-square limit of band-MAS σ_d(R = 1) over the six pilots (48 pairs and
  36 df each; P8-16's rule): gpt-oss-20b's 0.1364.
- **Count:** S = ⌈(z_{1−α′/2} + z_{0.80})² σ² / Δ²⌉ with α′ = 0.05 / 36 and Δ = 0.05 band-MAS (D12):
  ⌈121.38⌉ = **122**. Appendix A as written, with its factor 2, gives 243 and is reported beside. P9-13 gives the
  reason for the paired count: σ_d is already the sd of the paired difference, so the factor counts it twice.
- **Per model at 122 seeds** (`e9_2/sizing_open.json`, sha256 `d24f92de4d381658de8c0188c98891563dd2975301d3022bc102356c8fe08020`,
  from `tools/phase9/e9_2_pilot.py --stages open`):

| Configuration | σ_d | 90 % limit | Power at Δ = 0.05 | Paired MDD, band-MAS | D at θ 0.05 | D at θ 0.0020 |
|---|---|---|---|---|---|---|
| Gemma 4 31B | 0.0482 | 0.0571 | > 0.999 | 0.0209 | 0.0163 | 0.0088 |
| Gemma 4 E4B | 0.0342 | 0.0405 | > 0.999 | 0.0148 | 0.0194 | 0.0116 |
| gpt-oss-20b | 0.1151 | 0.1364 | 0.803 | 0.0499 | 0.0166 | 0.0100 |
| Muse Glimmer 30B | 0.0855 | 0.1013 | 0.988 | 0.0370 | 0.0237 | 0.0115 |
| OLMo 3.1 32B | 0.0102 | 0.0121 | > 0.999 | 0.0044 | 0.0266 | 0.0159 |
| Ministral 3 14B | 0.0686 | 0.0813 | > 0.999 | 0.0297 | 0.0198 | 0.0107 |

D has no stipulated effect (P8-2); its MDD at the band-MAS-sized design is its achieved power, stated in D's units.

## 3. The confirmatory analysis (P9-14)

- **One family per model.** For model m, Q1|C_m is memory − static × 3 personas × 4 scenario cells × tier C's three
  metrics (band-MAS, D at θ 0.05, D at θ 0.0020), so **m = 36**. D's two θ are near-duplicates (|r| 0.992), which is
  stated beside the count.
- **The test** is Phase 8's registered single-model analysis, `tools/stats_v2.run_stats_v21`, on the model's own scored
  runs. It forms the seed-level pairs (`seed_level_pairs`), then the one-way path bootstrap that E2 reduces to with one
  model (`pigeonhole_ci`, 1,999 draws, seed 0) gives each cell's percentile interval and two-sided p. Cliff's δ is
  reported beside.
- **The decision** is BH within the model's family at q = 0.05 (`inference_params.decision_rule(1)`). P8-10's
  simulation held this procedure's FDR at 0.042 on one family of 36. A claim reads: for model m, re-injecting the
  mandate changes this metric for persona p in scenario c, in the direction of the estimate. **No claim about models in
  general is made from these tests.**
- **Before any claim,** for each model and cell: the parse-fallback share, the zero-trade share and the static arm's
  mean cash share (`GRID_EXPERIMENT_PLAN.md` 7, Cycle 2's precondition).
- **Completeness.** A model's family is read once `e9_4_grid --stages verify` passes for it: every planned run present,
  with the manifest's prompt hash, `Env_Code_Hash`, configuration, scenario, seed and start design. A run abandoned
  after the runner's three non-ok attempts is reported as missing. Nothing is imputed, and no model is substituted.

## 4. Predictions, stated from the E9.2 pilots

The pilots ran seeds 3001–3004, disjoint from the headline's. **Rule:** a direction is predicted for a model × persona
where its pilot's memory − static band-MAS difference over 16 pairs (4 scenarios × 4 seeds) has |t| ≥ 2 and
|mean| ≥ 0.005, a tenth of Δ. Otherwise no direction is predicted. Higher band-MAS is worse adherence.

| Configuration | ENTJ | INTJ | ISFJ |
|---|---|---|---|
| Gemma 4 31B | higher (0.074, t 3.4) | higher (0.038, t 3.6) | higher (0.018, t 5.2) |
| Gemma 4 E4B | none (−0.0004) | higher (0.022, t 4.9) | none (0.025, t 1.7) |
| gpt-oss-20b | none (0.032, t 0.7) | none (0.003, t 0.6) | higher (0.029, t 9.8) |
| Muse Glimmer 30B | none (−0.019, t −0.5) | higher (0.024, t 2.1) | higher (0.013, t 6.1) |
| OLMo 3.1 32B | lower (−0.011, t −4.8) | lower (−0.008, t −2.0) | higher (0.023, t 19.4) |
| Ministral 3 14B | lower (−0.125, t −4.5) | higher (0.028, t 2.8) | higher (0.018, t 6.5) |

- **P1, per model and persona:** each direction in the table.
- **P2, ISFJ across models:** re-injecting the mandate raises ISFJ's band-MAS in at least five of the six models. In
  the pilot it was positive in all six and t ≥ 2 in five: the conservative persona over-corrects toward all cash.
- **P3, size:** Gemma 4 E4B's mean contrast over the 12 cells is smaller in absolute value than Gemma 4 31B's. The pilot
  gave 0.016 against 0.043; P9-12 records the same pattern from Cycle 2, where the effect was weakest or reversed at
  4–9B.
- **How they are read:** each model × persona's estimate is pooled over its 4 scenarios × 122 seeds, and its sign is
  read against the prediction. The reading is descriptive and outside every BH family. A wrong prediction is reported
  as wrong.

## 5. Exploratory, with no claim

- **R5** (P9-4) in each cell × metric over the six models, with its power stated. P9-2 measured R5's power at M = 5–6
  as at most 0.55 at a between-model sd of half Flash's σ_d limit and at most 0.09 at the full limit, at 93 seeds, and
  seeds barely move it (P9-3).
- E1 at the better REML optimum (P8-17).
- Tier S (turnover, MDD, return), in its own families.
- How often each cell's sign agrees across the six models, and the persona-pooled contrasts.
- Reasoning tokens and seconds per run, per model.

## 6. Not in this stage

The D11 common-start slice and its salience shares (E3), Track A (E4), the causal package (E2), the generator sweep
(E5, stage 2), context length (E6), and the rest of `GRID_EXPERIMENT_PLAN.md` 3. Each gets its own pre-registration
and compute estimate before it runs.

## 7. How it runs

- **One SLURM array.** `tools/cluster/headline_b200.sbatch` runs on `hpg-b200` under fire-finai: six tasks, at most
  four at once, each with 1 B200, 6 cores and 44 GB. That fits Lingfei's caps of 4 GPUs, 24 cores and 180 GB across
  all of the project's jobs at once, for one week (P9-12). The longest models run first.
- **Each task** loads the pinned snapshot and serves it with its pilot's vLLM arguments. It then runs the twelve-call
  parse preflight, where a model that fails stops and is reported. Last, the runner makes 64 in-flight calls and
  checkpoints every run. A resubmission resumes the same manifest or refuses to start.
- **Estimate:** 110–130 B200 GPU-hours and about 2.5–3 days of wall-clock. Muse Glimmer, at about 54–67 h on one GPU,
  is the long pole.

## 8. After the first run

Nothing above changes after the first run of this manifest. A deviation is recorded as a numbered addendum with its
reason. The fingerprint refusal keeps cells, prompts and seeds from moving silently.
