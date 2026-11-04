# Pre-registration — Phase 9, stage 2, E8: the re-injection cadence (how much of the memory effect a sparse injection keeps)

**REGISTERED 4 Nov 2026**, drafted and approved by the team the same day as drafted, with the four judgment calls of
section 9 taken as recommended (a deterministic cadence with a seed phase; the six models of `e9_roster.CAUSAL_OPEN`;
the levels {2, 5, 10, 20}; two clones on the cluster), before any run of
`docs/env_v2/generated/v2_1/e9_4/manifest_cadence_open.json` existed (`DECISION_LOG.md` P9-39). Nothing of this
experiment has run. Where it changes `PREREG_PHASE_9.md` 4.1 or the E8 row of `GRID_EXPERIMENT_PLAN.md` 3, the change is named in
section 0; everything 4.1 fixes that section 0 does not name stands.

The plan's instruction for E8 is kept as written: **a replication, not a contribution** — Li et al. (COLM 2024) swept
injection probability with a capability-cost axis, so this is run small, cited, and not headlined (`GRID_EXPERIMENT_PLAN.md`
3). It is an appendix of the stage-2 package, on the package's roster, and its one novelty is stated in section 1: in
a stateless harness the cadence can only act through the portfolio state, which makes the retention it measures a
different quantity from Li et al.'s.

---

## 0. What this file changes in PREREG_PHASE_9.md 4.1 and in the plan's E8 row

| Item | As registered / planned | Here | Why |
|---|---|---|---|
| Arms | the plan's row: "freq arms" | **`memory_k2`, `memory_k5`, `memory_k10`, `memory_k20`**: the mandate block injected every k-th day, phase seed mod k (`experiments/arms_v2.CADENCE_LEVELS`); **k = 1 is the headline's `memory` arm and never is its `static` arm, not re-run** | no frequency arm existed in the harness (section 1); the two endpoints exist on these seeds and paths for every model |
| The factor | — | `RunConfig.mandate_every` (default 1, the behaviour of every published run), the agent rendering the block on day t iff (t − 1 − phase) % k = 0, `Mandate_Injected` logged per day and the injection count in `meta.json`; a stateful arm refuses it | section 1; a stateless factor by construction |
| Levels | — | **k ∈ {2, 5, 10, 20}**: 100, 40, 20 and 10 injected days of 200, between the endpoints' 200 and 0 | four interior points on a log-spaced grid; every k divides T, so each run carries exactly T / k injections at any phase (J3) |
| Roster | the plan's 3; the selection's rule gives Gemma 4 E4B, Ministral 3 14B, Llama 3.1 8B | **the six of `e9_roster.CAUSAL_OPEN`** | the stage-2 package (E2, E3, E7) reads on these six and the endpoints exist on all of them; the rule's three cost 14.8 GPU-hours, the six 47.0 (J2) |
| Runs per model | "small" | **2,880** = 3 personas × 4 cadences × 4 scenarios × 60 seeds | the stage-2 shape on the headline's cells |
| Seeds | — | **10001–10060**, the first 60 of the headline's, as every stage-2 experiment | the endpoints are on these seeds |
| Setting | — | `cadence`, subdir `stage2_cadence` | a run-key and path component: no E8 run can collide with its headline twin |
| The harness | the eight hashed sources as E7 and the E6 pilot registered them | **three moved**: `agent/v2_agent.py`, `simulation/runner_v2.py`, `experiments/arms_v2.py` | the factor; no prompt hash of any manifest moved (`tests/test_v2_1_e8.py`); the consequence for the two earlier registrations is in section 7 (J4) |
| Confirmatory test | R5 over the roster | **each model its own family**; R5 exploratory | P9-14, carried |
| Concurrency | 15 workers per model | per-server, under a 256 ceiling, stage 2's operating point | P9-20 |

**Unchanged:** T = 200; R = 1; `harness_version = placebo_version = "v2_1"`; dividends paid; the `rewritten`
wording; Track B; `start_design = "target"`; the default generator at `Env_Code_Hash` **1d689aaf82a33a2e**;
temperature 0.2; the mandate block byte-identical to the memory arm's on every injected day.

## 1. The question

The headline contrasts the memory arm, which re-injects the core mandate into every day's prompt, with the static arm,
which never does. E8 asks how much of that effect survives as the injections thin out: one day in two, in five, in
ten, in twenty. The quantity is the **retention** r(k) = d(k) / d(1), where d(k) is the paired band-MAS difference
between the cadence arm at k and the static arm, and d(1) the memory arm's, per model and cell.

**What makes the stateless harness a different experiment from Li et al.'s.** Every arm here is stateless: the model
sees one day's prompt and nothing of yesterday's. On a non-injected day the cadence arm's prompt is **byte for byte
the static arm's** (`test_cadence_renders_the_memory_prompt_on_injected_days_and_the_static_prompt_otherwise`). The
only thing that carries from an injected day to the next is the **portfolio state** the prompt shows: the cash share
the injected decision left behind. So if the model simply re-decides from scratch each day, the cadence arm behaves as
the memory arm on injected days and as the static arm on the others, and the retention is **exactly the injected
share, r(k) = 1 / k**. Anything above 1 / k is carry-over: an allocation set under the mandate that the mandate-free
days keep. Li et al.'s sweep ran with a dialogue history in which earlier injections stay visible; theirs measures
attention across turns, this measures persistence through state. The design axis is replicated, the mechanism is not,
and section 4 reads the difference directly (P3).

**Three findings, checked on the code before this design was written.**

1. **No frequency arm existed.** `experiments/arms_v2.ARMS` held every-day (`memory`) and never (`static`) and nothing
   between; the plan's "freq arms" were a row in a table. The factor is added as section 0 states, with the phase
   taken from the seed so that no cadence sits on the scripted event in every run, and the per-day rendering tested
   against the two existing arms' prompts.
2. **The factor touches three of the eight sources the manifest fingerprint hashes.** Every manifest's stored source
   hashes for those three now differ from the tree, as `agent/v2_prompts.py`'s did after E7's counterpart map. Every
   stored **prompt** hash of every manifest recomputes unchanged, and so does `Env_Code_Hash`. For the completed
   stage-1 and stage-2 manifests this changes nothing (their runs verify on prompt and environment hashes, and nothing
   of theirs is resumed). For the two registered and **unrun** manifests, E7's and the E6 pilot's, it means the runner
   refuses them on a tree that carries this change — by design, that refusal is what the fingerprint is for — so they
   run from a clone pinned at their own commit and E8 from a second clone at its own (section 7, J4).
3. **The endpoints are free and exact.** The headline's static and memory runs exist for all six models on seeds
   10001–10060 at the default setting, verified, with the memory arm's prompt hash equal to every cadence arm's
   (one prompt family: the block is present or absent, never different). E8 is scored against those rows as E2 is
   against the same ones.

## 2. The design

| | |
|---|---|
| Manifest | `e9_4/manifest_cadence_open.json`, name `e9_4_stage2_cadence`, subdir `stage2_cadence`, setting `cadence`; sha256 recorded in `DECISION_LOG.md` at registration |
| Cells | the headline's 12: {ISFJ, INTJ, ENTJ} × {flat, bull_trap, crash δ 0.70, sustained_bull} |
| Arms | `memory_k2`, `memory_k5`, `memory_k10`, `memory_k20`; endpoints `memory` (k = 1) and `static` (never) from the headline |
| Phase | seed mod k; injected days t (1-based) with (t − 1 − phase) % k = 0; exactly T / k per run |
| Seeds | 10001–10060; R = 1 |
| Runs | 4 × 12 × 60 = **2,880 per model, 17,280 in all** |
| Roster | `e9_roster.CAUSAL_OPEN`: Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B, Phi-4, Gemma 4 31B |
| Serving | as stage 2: vLLM 0.29.0, the pinned revisions, `--max-model-len 32768`, 192 in flight per server (80 for Gemma 4 31B) |
| Array | 12 tasks, every model in two shards, `--array=0-11%4`, from the E8 clone (section 7) |

**Cost**, 2,880 runs × each model's measured GPU-hours per run (`e9_4/selection/cost.csv`, n = 2,928 runs per model):

| model | GPU-h | model | GPU-h |
|---|---|---|---|
| Gemma 4 31B | 16.2 | Phi-4 | 5.5 |
| OLMo 3.1 32B | 10.6 | Llama 3.1 8B | 5.2 |
| Ministral 3 14B | 6.9 | Gemma 4 E4B | 2.6 |

**47.0 B200 GPU-hours projected**; E5 ran at 0.74–0.80 of its projection (`STAGE2_OPERATIONS.md` 3), which would put
E8 at 35–38. Floor on four GPUs 11.8 h; unsharded 16.2 h (72.5 %), Gemma 4 31B alone being 16.2; every model in two,
12.2 h at 96.6 %. The rule's three cost 14.8; the core's five effect-carrying models 30.8.

**What is logged that was not before.** Per day, `Mandate_Injected`; per run, `n_mandate_injections` and
`mandate_phase` in `meta.json`. Both are absent from a run without the factor, so no published run's columns change.

## 2a. Power at S = 60

E8's contrasts are paired on the same seeds and models as the headline's, so stage 1's noise applies: at S = 60 the
band-MAS MDD at α′ is 0.028–0.048 for the five models below the noisiest (`HEADLINE_MODEL_SELECTION.md` 3.5,
`noise_seeds.csv`, 122 pairs per cell) and 0.093 for Ministral 3 14B. A cadence contrast at k = 20 that keeps a
fifth of a 0.05 every-day effect is 0.01 and is not detectable in any model at S = 60; the per-cell confirmatory
family therefore reads the larger cadences, and the retention of section 3 is the pooled, bootstrapped reading where
the small ones live. The admission floor of 0.01 on the every-day effect (E2's) is what keeps a ratio from being
computed on noise.

## 3. The confirmatory analysis

**(a) The family**, per model: the four cadence arms against static, per persona × scenario cell × tier-C metric,
**4 × 12 × 3 = 144 tests, one BH family under `bh_within`**, passed explicitly to `run_stats_v21(families=...)` —
`question_families()` holds `memory − static` and nothing about a cadence arm (`test_e8_family_is_absent_from_the_shared_dict`).
A claim is a test at q ≤ 0.05 within the family. The two-way cluster bootstrap and the decision rule are the stage's.

**(b) Retention**, per model and metric: per cell, d(1) and d(k) as means over seeds of the paired differences;
a cell is **admitted** when |d(1)| ≥ 0.01; r(k) = d(k) / d(1) on admitted cells; pooled per model as the ratio of
signed sums over admitted cells, Σ d_c(k) sign d_c(1) / Σ |d_c(1)|, with a 95 % seed-cluster bootstrap interval
(999 draws, seeds resampled jointly across cells, admission fixed at the point estimate). A model is **readable** for
section 4 when at least 3 of its 12 cells are admitted (DESIGN). The injected share 1 / k is written beside every
estimate.

**(c) The per-step reading** (`tools/phase9/e9_5_e8_steps.py`, on the cluster): per run, the band distance of the
cash share, max(lo − c, c − hi, 0), averaged over injected days, non-injected days and the day after an injection;
per headline static and memory run on the same seeds, over every day; aggregated per (model, persona, cell, arm) with
the static arm's distance joined onto each cadence row.

**(d) Preconditions**, per model: the parse-fallback share of every cell ≤ 0.01 (G2), zero-trade share ≤ 0.5 (G3),
no scoring error; the pairing check that every (persona, cell, seed) key carries all six arms and that no (key, arm)
comes from two manifests (the frame takes the headline rows at the default setting only, because E3's common-start
and E4's Track-A `static` rows share their keys).

## 4. Predictions, stated in advance

Each is evaluated by `tools/phase9/e9_5_e8_analyse.py` on the retention table; a model enters only when readable;
with no readable model P1–P3 are `degenerate`, never held; P4 is `unevaluated` without the per-step file.

- **P1, the dose-response is monotone.** The pooled band-MAS retention at k = 2 exceeds that at k = 20 in at least
  two thirds of the readable models. It fails if thinning the injections does not thin the effect.
- **P2, a sparse cadence keeps most of the effect.** r(5) ≥ 0.5 — one injection in five keeps half the every-day
  effect — in at least half of the readable models. The 0.5 is a DESIGN bar. It fails if the effect needs the block
  on most days.
- **P3, carry-over through the portfolio state.** r(k) > 1 / k at k = 5, 10 and 20 in at least two thirds of the
  readable models. r(k) = 1 / k is exactly what a stateless agent with no carry-over gives (section 1), so this is
  the test of whether an allocation set under the mandate persists on the days the mandate is absent. It fails if the
  model re-decides from scratch each day.
- **P4, the per-step ordering.** On non-injected days the cadence arm's band distance lies between the static arm's
  and its own injected days', in the direction of the every-day effect, in at least two thirds of the admitted
  (model, cell, k) triples. It fails if non-injected days revert fully to the static arm or overshoot it.

None can pass trivially: P1 needs a direction, P2 a magnitude, P3 a strict inequality against an exact stateless
null, P4 an ordering of three measured quantities. A wrong prediction is reported as wrong.

## 5. Exploratory, with no claim

The cadence arms against the memory arm (how far each sits from the every-day effect, the other end of the same
ratio), the retention on the two D metrics, the day-after-injection distance, and the per-model R5 reading over the
roster: all reported with intervals and n, none a claim.

## 6. Not in this experiment

- **A stochastic cadence** (Bernoulli 1 / k per day, Li et al.'s form): a deterministic cadence with a seed-dependent
  phase gives the exact count T / k in every run and the same spread of injected days across seeds (J1).
- **Stateful cadence arms**: the retained history would carry the injected days and the quantity would be Li et
  al.'s; the stateful arms are unsized until the E6 pilot reports, and the runner refuses the factor on them.
- **gpt-oss-20b**: fails R_effect; **Muse Glimmer 30B, Llama 3.1 70B**: outside the core.
- **A `max_tokens` cap**, the OCEAN pair, Track A: as every stage-2 experiment.
- **Any headline claim**: the plan's instruction, kept.

## 7. How it runs

1. Done 4 Nov: approval; the DRAFT line replaced; the registration row P9-39 in `DECISION_LOG.md` with this file's
   sha256 and the manifest's (`6114d0ec…`, recomputed at registration).
2. **Two clones.** `repo_s2` stays at **b5baebb** until E7's and the E6 pilot's arrays have finished: a tree carrying
   this file's harness change refuses their manifests (section 1, finding 2). E8 runs from `repo_s3`, a clone at the
   registered E8 commit, passed to the batch script as `REPO=$BASE/repo_s3`.
3. `sbatch --export=ALL,STAGE=cadence,REPO=$BASE/repo_s3 --array=0-11%4 tools/cluster/stage2_b200.sbatch`, chained
   with `--dependency=afterany:` on whichever of E7's and the E6 pilot's arrays is last, so only one array holds the
   four GPUs; the preflight runs inside each task.
4. `sbatch --export=ALL,STAGE=cadence,REPO=$BASE/repo_s3 --dependency=afterany:<array id> tools/cluster/pack_stage.sbatch`.
5. On the cluster, from `repo_s3`: `e9_4_grid --stages verify,score --only cadence_open` (the verify stage checks each
   run's `mandate_every` and its injection count against T / k), then
   `python -u -m tools.phase9.e9_5_e8_steps --results results_v2/phase9 --headline-results <stage-1 record>/results_v2/phase9`,
   then the Hugging Face push.
6. On the laptop, with `per_run.csv` and `stats_e8_cadence/steps_summary.csv` pulled: `python -u -m tools.phase9.e9_5_e8_analyse`.
7. New files under `docs/env_v2/generated/v2_1/` need `git add -f`, then `git show --stat`.

## 8. Deviations

None. A deviation is numbered here before the array that carries it is submitted.

## 9. Judgment calls for the team

- **J1, deterministic cadence with a seed phase, or Bernoulli(1 / k).** Li et al. swept a probability. A deterministic
  cadence gives every run exactly T / k injections and the phase spreads the injected days across seeds; a Bernoulli
  cadence varies the count run by run and adds that variance to every contrast. **Recommended: deterministic.**
- **J2, the roster: the six, the rule's three, or the core's five.** The plan says 3 and "small"; the selection's rule
  gives E4B, Ministral and Llama 3.1 8B at 14.8 GPU-hours. The six keep the stage-2 package on one roster at 47.0, the
  five (every core member with an effect) sit between at 30.8. **Recommended: the six**, for the one-roster reading
  of E2, E3, E7 and E8 together; the cost sits well inside the E6 pilot's.
- **J3, the levels.** {2, 5, 10, 20} spans a factor of ten between the endpoints on a log grid, every level divides
  T. {2, 4, 8, 16} and three levels were considered; nothing in the record favours one grid over another.
  **Recommended: {2, 5, 10, 20}.**
- **J4, two clones or a sequenced pull.** The alternative to a second clone is to pull this commit into `repo_s2`
  only after every E7 and E6-pilot task has started, which a queued array under `%4` makes a timing exercise. A second
  clone costs a directory. **Recommended: two clones.**
