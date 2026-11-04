# Pre-registration — Phase 9, stage 2, the E6 sizing pilot: the stateful arms' noise and cost at the four context levels

**REGISTERED 4 Nov 2026**, drafted and approved by the team the same day as drafted, with the four judgment calls of
section 9 taken as recommended (8 seeds per cell; one served length of 65,536; seeds disjoint from E6's; the ρ
discrepancy carried beside the committed table rather than the selection regenerated), before any run of
`docs/env_v2/generated/v2_1/e9_4/manifest_context_pilot.json` existed (`DECISION_LOG.md` P9-37). Nothing of this
pilot has run. Where it changes `PREREG_PHASE_9.md` 2 or 4.1, the E6 row of `GRID_EXPERIMENT_PLAN.md` 3, or the E6 assignment of
`HEADLINE_MODEL_SELECTION.md` 4.3, the change is named in section 0; everything those fix that section 0 does not
name stands.

This is a **sizing pilot**, not E6. It measures the two things E6's own pre-registration cannot be written without,
the paired noise of the stateful arms and the GPU-hours a stateful run costs at each level, and it makes no claim
about the decay thesis. E6's pre-registration follows it and takes its decisions from the files this pilot writes
(section 3e).

---

## 0. What this file changes, and where it sits

| Item | As registered / planned | Here | Why |
|---|---|---|---|
| The gate | `GRID_EXPERIMENT_PLAN.md` 2: "a stateful sizing pilot" blocks E6, "the stateful arms' sigma_d was never measured, so that stage has no seed count"; 4 M3 "a pilot run, not code" | **this pilot**, with the code it needed (section 1, the three findings) | the gate was named and never built |
| Arms | the plan's E6 row: "six stateful arms" | **eight**: the factor's four levels × {static, memory}, `experiments/arms_v2.CONTEXT_LEVELS` | P8-7 added the 50 level after the row was written; the summary arms are not levels of the factor (`PREREG_PHASE_8.md` 2) |
| Roster | the selection's E6 assignment: **Llama 3.1 8B only**, three places open "if config files at the pinned revisions show windows that hold their full-level needs" | **Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B** — the plan's four, by the selection's own rule, the three windows now read (section 1) | a file read the selection said was a file read, done |
| Pilot shape | `PREREG_PHASE_9.md` 2's rule for the stage-1 pilots (12 cells × 2 arms, S_p from {4, 8, 12, 16, 24, 32} by expected total runs) | **the same rule on E6's counts**: 12 cells × 8 arms, S_p = **8**, 768 runs per model, 3,072 in all | section 2 |
| Seeds | stage-1 pilots 3001 upward; the grid 10001 upward | **5001–5008**, disjoint from E8.5's 2001–2008, E9.2's 3001–3016 and the grid's 10001–10122 | a pilot run can never be folded into E6's confirmatory set by accident (J3) |
| Served length | 32,768 in stages 1 and 2 | **65,536 on every model** | the 50 and full levels do not fit 32,768; 65,536 is the smallest roster window (OLMo's), so a reply is cut at the same point on every model (J2) |
| Concurrency | per server under a 256 ceiling; stage 2's operating point 192 | **per (model, level)**, one B200's KV cache over the context plus a typical largest reply, capped at 192: `context_pilot/workers.csv` | a level's calls are up to 35 times stage 1's prompts; above the KV bound vLLM preempts and recomputes |
| Array | one task per model, or per shard | **one task per (model, level)**, 16 tasks, `e9_runner run --arms` | the concurrency row |
| The fingerprint | `e9_runner.fingerprint` **skipped stateful cells** | hashes them, built as the runner builds the agent | section 1, finding 1 |

**Unchanged:** T = 200; R = 1; `harness_version = placebo_version = "v2_1"`; dividends paid; the `rewritten`
wording; Track B; `start_design = "target"` (the headline's start: this is not a salience design); the default
generator at `Env_Code_Hash` **1d689aaf82a33a2e**; temperature 0.2; the mandate in the system prompt of every
stateful arm (Path B, `StatefulV2Agent`); the 60,000-token budget of the full level (DESIGN, P8-7).

## 1. The question

**What E6 will ask, so that this pilot measures the right nuisance parameters.** The decay thesis says the mandate's
hold on behaviour weakens with the context between it and the generation point. In the stateful arms the mandate sits
in the system prompt; in the memory arm a second copy is re-injected into the current turn, so the nearest copy is a
constant 436 tokens away, while in the static arm the nearest copy is the system one and the distance grows with the
window (P8-4). E6's contrasts are therefore, per model and paired on (persona, scenario, seed):

- **memory − static at each level** — the re-injection effect, as the headline reads it, at windows 5, 20, 50 and full;
- **the level contrasts against the shortest window**: effect(L) − effect(5), the interaction the thesis predicts
  grows with L; and static(L) − static(5), the thesis's direct reading. Under P8-11 a temporal claim is made across
  paths with the sign-flip null, never within a run.

E6's seed count depends on the paired noise of those three quantities, and its cost on the GPU-hours of a stateful
run at each level. **Neither has ever been measured on an open-weight model.** The only stateful runs in the record
are three Gemini 2.5 Flash runs under the v2 harness (`results_v2_pilot/stateful/`, flat, seed 42, rolling 20) and
E8.5's eight context-smoke runs on Flash (`e9_0/smoke/smoke_context_thinking0_gemini-2.5-flash.json`), which timed
the levels and measured nothing paired. Stage 1's GPU-hours do not price a stateful run: its per-call context is 3.1
to 27.8 times the stateless input (`e8_2/context_cost.json`, v2_1 rows).

**Three findings, checked on the code before this design was written.**

1. **The manifest fingerprint skipped stateful cells.** `e9_runner.fingerprint` returned no prompt hash for a cell
   whose `context_mode` was not `stateless`, so a manifest of stateful arms would have carried no prompt hash at all
   and `stage_verify` would have checked nothing about its prompts. It now builds the agent exactly as
   `simulation/runner_v2.run_simulation_v2` does and hashes it; every prompt hash every manifest on disk stores
   recomputes unchanged (`tests/test_v2_1_e6_pilot.py`, `tests/test_v2_1_e7.py::test_no_mbti_prompt_hash_moved`),
   since none had a stateful cell. `e9_runner.py` is not one of the eight hashed sources, so no manifest's source
   hash moves.
2. **The committed context table and the selection document disagree.** `selection/context_e6.csv` carries no KV-cache
   size for any model — it was written on a machine without the stage-1 server logs — which is why `R_context` never
   left "conditional" there; and its ρ (each model's own tokens per o200k token) is 0.88–0.93 where section 3.7's
   table has 1.01–1.06, so the document's full-level needs are about 13 % larger (OLMo: 64.5k against 57.0k). The
   KV sizes are taken from the document's table and labelled so (`KV_TOKENS_DOC`); the document's full-level needs
   are checked beside the CSV's (`fits_window_doc_3_7`), and the pilot logs the context the model actually saw
   (`Context_Tokens`, the provider's count), which settles ρ. Regenerating the selection needs the 7.5 GB of stage-1
   CSVs and is not done here (J4).
3. **The three unread windows, read** from `config.json` at the pinned revisions on the Hub on 4 Nov 2026
   (`context_pilot/windows.json`, each with its field and revision): **Gemma 4 E4B 131,072** (sliding window 512 on
   the local layers), **OLMo 3.1 32B 65,536** (YaRN factor 8 over 8,192; sliding window 4,096 on three layers in
   four), **Ministral 3 14B 262,144** (YaRN factor 16 over 16,384); Gemma 4 31B 262,144 beside. Each holds its full
   level under both ρ bases. By the selection's rule (`EXPERIMENT_REQ["E6"]` = R_effect and R_context over the core)
   E6's roster is exactly the plan's four: Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B. gpt-oss-20b
   fails R_effect, Phi-4's 16,384 fails the 50 and full levels, and Gemma 4 31B meets both requirements but is not
   a core member (section 6).

## 2. The design

| | |
|---|---|
| Manifest | `e9_4/manifest_context_pilot.json`, name `e9_4_context_pilot`, kind `pilot`, subdir `pilot_context`, setting `default`; sha256 recorded in `DECISION_LOG.md` at registration |
| Cells | the headline's 12: {ISFJ, INTJ, ENTJ} × {flat, bull_trap, crash δ 0.70, sustained_bull} |
| Arms | level 5: `stateful_r5_static`, `stateful_r5_memory`; 20: `stateful_static`, `stateful_memory`; 50: `stateful_w50_static`, `stateful_w50_memory`; full: `stateful_full_static`, `stateful_full_memory` |
| Seeds | 8 per cell, 5001–5008, the same for every model, arm and cell; R = 1 |
| Runs | 8 arms × 12 cells × 8 seeds = **768 per model, 3,072 in all** |
| Roster | `context_pilot/windows.json` → `e6_roster`: the four of section 1 |
| Serving | vLLM 0.29.0, the pinned revisions, `--max-model-len 65536`, `--gpu-memory-utilization 0.90`, `--max-num-seqs` = the task's workers, prefix caching on |
| Concurrency | `workers.csv`, column `workers_typical`: E4B 192 / 189 / 82 / 46; OLMo 77 / 27 / 11 / 7; Ministral 148 / 51 / 22 / 14; Llama 3.1 8B 192 / 81 / 36 / 20 at levels 5 / 20 / 50 / full |
| Array | 16 tasks, `model@level`, longest per run first, `--array=0-15%4` |
| Preflight | `tools.cluster.preflight_vllm` as every stage: two decisions per (persona, arm) with the stateful system prompt; 48 calls |

**The shape rule** (`e9_4_context_pilot --stages shape`, `context_pilot/shape.json`), `PREREG_PHASE_9.md` 2's as
written with E6's counts: expected runs per model = the pilot's 96 S_p + f²(df_d) × G_ref, where f² is the one-sided
90 % chi-square limit's inflation at df_d = 12 S_p − 12 (per level, never pooled across levels) and G_ref is E6's
5,760 runs per model at stage 2's quoted S = 60 divided by the inflation E8.5's sizing carried, f²(84) = 1.268.

| S_p | runs | df_d per level | f | expected total |
|---|---|---|---|---|
| 4 | 384 | 36 | 1.185 | 6,918 |
| **8** | **768** | **84** | **1.112** | **6,528** |
| 12 | 1,152 | 132 | 1.087 | 6,655 |
| 16 | 1,536 | 180 | 1.074 | 6,901 |
| 24 | 2,304 | 276 | 1.058 | 7,519 |
| 32 | 3,072 | 372 | 1.050 | 8,202 |

The cost-weighted optimum is the same S_p: the pilot and E6 run the levels in the same proportions, so every level's
cost multiplies both terms alike.

**Cost, a PROJECTION** (`--stages project`, `context_pilot/projection.json`): Phase 8's measured input tokens per
run per level (v2_1 harness, n = 3 Flash runs: 1.20 M / 3.52 M / 7.60 M / 10.63 M at 5 / 20 / 50 / full, against
0.38 M stateless) over stage 1's measured input tokens per GPU-second per model (`selection/cost.csv`, n = 2,928 runs
each, at 1.8k-token prompts). Stage 1's rate blends prefill and decode at short prompts; at 60k the prefill share is
larger and the prefix cache helps the full level until its budget binds and the rolling levels not at all, so the
true figure can sit on either side. **The projection is what prediction P1 tests**, and E6's cost will be quoted from
the pilot's measurement, not from this table.

| model | GPU-h per run at 5 / 20 / 50 / full | pilot GPU-h | E6 at S = 60, GPU-h |
|---|---|---|---|
| Gemma 4 E4B | 0.0030 / 0.0087 / 0.0189 / 0.0264 | 10.9 | 82 |
| OLMo 3.1 32B | 0.0125 / 0.0366 / 0.0791 / 0.1108 | 45.9 | 344 |
| Ministral 3 14B | 0.0079 / 0.0231 / 0.0500 / 0.0699 | 29.0 | 217 |
| Llama 3.1 8B | 0.0060 / 0.0178 / 0.0384 / 0.0537 | 22.3 | 167 |
| **total** | | **108.0** | **810** |

**Wall-clock.** The four GPUs' floor is 27 h at the projection. OLMo's full-level task is the longest: 192 runs at 7
in flight, each run 200 calls on a 55k-token context. The `--time` limit of four days holds it either way.

**The pilot's harness.** Every run under the v2_1 stateful corrections (P8-4): the nearest-copy offset as the
primary covariate, the system-copy offset beside, retained turns without the injected block, a fallback stored as
`no valid answer`, provider token counts with the method logged. No `max_tokens` is sent on the vLLM route, as in
stages 1 and 2; a reply is bounded by the served length alone (section 6).

## 3. What is measured, and the rule that turns it into E6

**(a) Noise** (`--stages analyse`, `context_pilot/sigma.csv`, `contrasts.csv`). Per model and level, for band-MAS and
every tier-C metric: σ_d(R = 1) of memory − static paired on (persona, scenario, seed), centred per cell, on
df_d = 96 − 12 = 84, with its one-sided 90 % chi-square limit (`e9_2_pilot.sigma_r1`, the closed form at R′ = R,
P8-15). Per model and level L ∈ {20, 50, full}, for band-MAS: the same for effect(L) − effect(5), static(L) − static(5)
and memory(L) − memory(5), paired on the same triple.

**(b) E6's seed count** (`sizing.json`), `PREREG_PHASE_9.md` 2's rule applied quantity by quantity: the plug-in is the
**maximum limit over the roster** (P8-16's rule on measured models); the seeds follow Appendix A at
α′ = 0.05 / 36 — stage 1's convention and E6's candidate family of three level contrasts × twelve cells, which E6's
registration fixes for itself — with the paired-correct count beside; per model, its own count and the MDD at
S ∈ {5, 20, 30, 40, 60}; and the flag the plan's 13.1 asks for, whether the contrast is estimable at 5 seeds
(MDD at S = 5 ≤ Δ = 0.05 at the plug-in). Each of the ten quantities (four within-level effects, three interaction
contrasts, three static contrasts) is its own row. **A roster model with no rows is named, never dropped.**

**(c) Cost** (`cost.csv`): per model and level, the busy GPU time of that level's runs as the union of the attempts'
ledger intervals (the selection's `cost.csv` construction), per completed run, the mean concurrency reached, tokens
per run, and E6's GPU-hours at every candidate seed count, summed over the roster.

**(d) Gates** (`gates.csv`), per (model, level), the selection's two on the pilot's own runs and three the pilot adds:
G2, the largest cell's parse-fallback share ≤ 0.01; G3, the share of zero-trade runs ≤ 0.5; the largest
`Context_Tokens` of any run below the served length (headroom > 0); the share of runs with a reply of ≥ 8,192 tokens
(the runaway bar: the cap the roster already applies on the OpenRouter route); `Mandate_Copies_In_Context` ≤ 2 and the
token-count method `provider` on every row (P8-4's corrections, in force on a real server for the first time).

**(e) What E6's registration then decides, from these files and not here:** its seed count, one for the roster or
one per model; whether a (model, level) that fails a gate is dropped or carried as uninterpretable; whether a
`max_tokens` cap is sent on the vLLM route for E6 (a change to `e9_roster.make_client` the pilot's runaway share
either motivates or does not); whether E6 runs on the grid's seeds 10001 upward, where the stateless static and
memory runs of E1 and E3 already exist as a free "level 0" on the same paths; the confirmatory family and its count.
None of those is a pilot decision.

## 4. Predictions, stated in advance

Two, both about the pilot's own measurements and neither about the thesis. Each is `unevaluated` when its inputs are
missing, never passed by default.

- **P1, the projection.** For every one of the 16 (model, level) pairs, the measured GPU-hours per run lies within a
  factor 2 of section 2's projection. **Holds** if the worst pair's factor is ≤ 2. A failure means E6 cannot be
  priced from stage-1 rates and Phase 8's token counts, and its cost table must come from this pilot alone — which it
  does in any case (section 2); P1 records whether the method was any good.
- **P2, the noise regime.** For every roster model, σ_d of memory − static at level 5 (96 pairs, df 84) lies within
  a factor 2 of the model's stateless σ_d, the RMS over its twelve stage-1 cells at 122 pairs each
  (`selection/noise_seeds.csv`, `sigma_rms_bm`). **Holds** if the worst model's factor is ≤ 2. A failure means the
  stateful arms are a different noise regime from the stateless ones, and E6's registration may not borrow stage 1's
  noise for anything.

Neither can pass trivially: P1 fails on any pair, P2 on any model, and the bars are a factor of two, not a sign.

## 5. Exploratory, with no claim

The per-level effect means (`sigma.csv`, column `mean`) and the signs of the level contrasts (`contrasts.csv`) are
reported as descriptives, with their n. They are what E6 is designed to test and no reading of them here is a
result: at 8 seeds a single cell's MDD at α′ is above 0.1 band-MAS on every model whose stateless noise is known.
The logged offsets (`Mandate_Offset_Tokens`, both copies) are summarised per level for E6's covariate design.

## 6. Not in this pilot

- **The summary arms** (`stateful_summary_*`): not a level of the factor; their matched control is the 5 level
  itself (P8-7, R2-3).
- **Gemma 4 31B**: meets R_effect and, with its window read, R_context, but it is not a core member and the rule's E6
  places go to core members; its KV cache holds 2 runs at the full level (116,137 tokens), so a full-level cell would
  run 96 runs two at a time.
- **Phi-4** (16,384-token window) and **gpt-oss-20b** (fails R_effect), by the rule.
- **A stateless reference arm**: it exists on seeds 10001 upward and not on 5001–5008; the pilot sizes, it does not
  compare (section 3e).
- **Decode replicates**: R = 1, as every grid stage.
- **A `max_tokens` cap**: measured first, decided at E6's registration.
- **INTJ dropped, or two scenarios instead of four**: the stage-1 noise rule reads the largest cell's σ_d, and stage
  1's largest cells were ENTJ's in flat, crash and sustained_bull depending on the model; a pilot that leaves cells
  out can miss the one that sizes E6.

## 7. How it runs

1. Done 4 Nov: approval; the DRAFT line replaced; the registration row P9-37 in `DECISION_LOG.md` with this file's
   sha256 and the manifest's (`05d54102…`, recomputed at registration).
2. `git pull` in `repo_s2` to the registered commit (the manifest's fingerprint refuses an older tree).
3. `sbatch --export=ALL,STAGE=e6pilot --array=0-15%4 tools/cluster/stage2_b200.sbatch`; the preflight runs inside
   each task. **Only with `%4`**: 16 tasks without it would take 16 GPUs.
4. `sbatch --export=ALL,STAGE=e6pilot --dependency=afterany:<array id> tools/cluster/pack_stage.sbatch`.
5. On the cluster: `python -u -m tools.phase9.e9_4_grid --stages verify,score --only context_pilot` (writes
   `verify_context_pilot.json`, `per_run_context_pilot.csv`), then
   `python -u -m tools.phase9.e9_4_context_pilot --stages summarise --server-logs '<logs>/vllm_srv_<array id>_*.log'`
   (writes `context_pilot/per_run_context.csv`, `servers.json`), then the Hugging Face push.
6. On the laptop, with those files pulled: `python -u -m tools.phase9.e9_4_context_pilot --stages analyse`.
7. New files under `docs/env_v2/generated/v2_1/` are invisible to `git status` (`.gitignore:69`) and need
   `git add -f`, then `git show --stat`.
8. E6's pre-registration, written from `context_pilot/{sizing.json, cost.csv, gates.csv, summary.json}`.

## 8. Deviations

None. A deviation is numbered here before the array that carries it is submitted.

## 9. Judgment calls for the team

- **J1, S_p = 8 by the rule, or 4.** Four seeds per cell halves the pilot (384 runs per model, ≈ 54 GPU-h projected)
  at a limit factor of 1.185 against 1.112, which makes E6 about 14 % larger if it is sized at the limit; the rule
  as E9.2 ran it says 8. **Recommended: 8.**
- **J2, one served length or each model's native.** At 65,536 a Llama 3.1 8B runaway (30,923 tokens in stage 1) is
  cut where OLMo's would be; at 131,072 it runs its course and costs a window. One length makes the models comparable
  and bounds the cost; it also means the truncation point is a design parameter of E6. **Recommended: 65,536.**
- **J3, disjoint seeds or an internal pilot.** On 10001–10008 the pilot's runs would be E6's first eight seeds and
  the stateless reference would exist on the same paths, saving 8 / S of E6; the variance-only use of an internal
  pilot is defensible. The stage-1 convention is disjoint seeds, and this draft keeps it. **Recommended: disjoint.**
- **J4, the ρ discrepancy.** This draft reads the committed CSV and carries the document's larger needs beside it;
  the alternative is to regenerate the selection on the cluster first. **Recommended: proceed; the pilot's logged
  `Context_Tokens` settles it, and the served length holds under both.**
