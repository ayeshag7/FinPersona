# Pre-registration — Phase 9, stage 2, E7: the OCEAN vocabulary gradient (persona text against directive, across two vocabularies)

**REGISTERED 4 Nov 2026**, drafted 3 Nov and approved by the team on 4 Nov as drafted, with both judgment calls it
flagged taken as recommended (the six models of `e9_roster.CAUSAL_OPEN` rather than the rule's three; the vocabulary
contrast within arm as the confirmatory family), before any run of
`docs/env_v2/generated/v2_1/e9_4/manifest_ocean_open.json` existed (`DECISION_LOG.md` P9-35). Nothing of this
experiment has run. Where it changes `PREREG_PHASE_9.md` 4.1 or the E7 row of `GRID_EXPERIMENT_PLAN.md` 3, the change is named in
section 0; everything 4.1 fixes that section 0 does not name stands.

---

## 0. What this file changes in PREREG_PHASE_9.md 4.1 and in the plan's E7 row

| Item | As registered / planned | Here | Why |
|---|---|---|---|
| Personas | ISFJ, INTJ, ENTJ | the OCEAN pair **O1_conservative, O2_aggressive**, with E3's ISFJ and ENTJ rows as the MBTI side of the gradient; INTJ has no OCEAN counterpart and is in no E7 frame | the plan's E7 row; section 1 |
| Arms | the plan's row: static, memory | **static, memory, swapped**, every cell at `start_design = "common"` | the plan's row identifies no share: `evaluation/salience.identification_check` needs a common start, a no-persona reference and a run whose directive differs from its persona (section 2) |
| Start | the band centre | **common, 0.5** | the same |
| Reference level | — | **E3's NONE trader runs, not re-run** | same six models, seeds, paths, prompt hash and `Env_Code_Hash`, verified 2,400 / 2,400 per model |
| Roster | the plan's 3; the selection's rule gives Gemma 4 E4B, Ministral 3 14B, Llama 3.1 8B | **the six of `e9_roster.CAUSAL_OPEN`** | the MBTI side and the reference exist on exactly these six; the plan's own rule is to buy models, not seeds; the three cost 7.4 GPU-hours, the six 23.5 |
| Runs per model | ~480 (the selection's costing: 2 personas × 2 arms × 2 scenarios × 60) | **1,440** = 2 × 3 × 4 × 60 | pairs cell for cell with E3 on all four scenarios |
| Seeds per cell | Appendix A on the API sizing | **60**, the first 60 of the headline's, as every stage-2 experiment | plan 3 |
| The harness | `agent/v2_prompts.py` as the four stage-2 manifests ran it | **`MANDATE_COUNTERPART` added**: an OCEAN persona's mandate is its MBTI counterpart's at every wording level | section 2, "the harness change" — a declared change with its evidence |
| O3 numerical-only | plan 4.5 / 4.6 name it as a reference and a validation arm | **not run** | P8-14: it cannot be constructed on v2 and its text contradicts the bands; E4 shows the stated-target arm sits on band-MAS's floor (73.0 % exact zeros, 17 of 18 cells below 0.001), where a surrogate has nothing to decompose |
| Confirmatory test | R5 over the roster | **each model its own family**; R5 exploratory | P9-14, carried |
| Concurrency | 15 workers per model | per-server, under a 256 ceiling | P9-20 |

**Unchanged:** T = 200; R = 1; `harness_version = placebo_version = "v2_1"`; dividends paid; the `rewritten` wording;
Track B (no band is stated in any prompt); the default generator at `Env_Code_Hash` **1d689aaf82a33a2e**;
temperature 0.2.

## 1. The question

E3 decomposes what the agent does into the **persona text**, the **mandate directive** and the **start**, on one
vocabulary: the MBTI narrative. E7 asks whether that decomposition, and the memory − static effect the benchmark
rests on, depend on the vocabulary the persona is written in. The OCEAN pair states the same two risk categories as a
Big Five trait profile — five numeric scores with IPIP-anchor behavioural descriptions (Big5-Scaler, Cho & Cheong,
2025; Goldberg, 1999) — in place of the MBTI narrative, **with the mandate held byte-identical**, so that a difference
between the two sides of the gradient attributes to the persona text and nothing else.

v1's rebuttal (Section 4.5) claimed framework independence on the v1 point targets at a 100 %-cash start, on three API
models at five seeds, and under the v1 gate the OCEAN pair separated no better than the MBTI three
(`E0_SEPARABILITY_GATE_V1.md` 5: pooled O1-vs-O2 AUC 0.624 at n = 180, ordering met in 2 of 3 models in the static
arm, band-hit 0.133). None of that transfers to bands, a common start and identified shares. E7 is the v2.1 question.

**Three findings, checked on the code before this design was written.**

- **The OCEAN mandates were not content-identical to the MBTI ones under v2.1**, contrary to `agent/ocean_prompts.py`'s
  docstring. v2.1's default wording is `rewritten`, which gives ISFJ the single-asset clause *"Keep a large cash
  cushion instead of insurance products"*; O1 fell through to v1's *"Buy insurance (puts/hedges)"*, an instrument this
  environment does not have, and the `paraphrase`, `abbreviated` and `no_action_clauses` levels fell through the
  same way. O2 and ENTJ were identical. Section 2 records the fix.
- **v2 never reads the OCEAN module's `cideal`.** Scoring takes O1's band from `evaluation/targets.py` (0.70–0.90) and
  the OCEAN system prompt states no number, so the 1.0 is a stale v1 field, not a scoring defect.
- **The plan's one-line E7 identifies no share.** Static and memory on O1/O2 at the default start fail clauses (ii)
  and (iii) of the identification check exactly as the headline does (E3 section 1); the common-start design with a
  no-persona reference is the only one on which the shares are reported, and E7 uses it.

## 2. The design

**Roster** — `e9_roster.CAUSAL_OPEN`: Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B, Phi-4, Gemma 4 31B.
The selection's rule assigned E7 three of these (`HEADLINE_MODEL_SELECTION.md` 4.3: Gemma 4 E4B, Ministral 3 14B,
Llama 3.1 8B, by coverage of the core among the members meeting R_persona, which all nine meet). The six are the
three plus the other three E3 ran, because the MBTI side and the reference level exist on them and on no other model.

**Cells**, every one at `start_design = "common"`, setting `common_start`, subdir `stage2_ocean`:

- **O1_conservative, O2_aggressive** × (`static`, `memory`, `swapped`) × flat, bull_trap, crash (δ 0.70),
  sustained_bull × seeds 10001–10060 × R = 1 = **1,440 runs per model, 8,640 in all.**

**Reused from E3's slice, on the same six models, seeds and paths**, verified 2,400 / 2,400 per model
(`verify_slice_open.json`):

| E3 rows an E7 frame uses | per model |
|---|---|
| ISFJ, ENTJ × (static, memory, swapped) × 4 scenarios × 60 seeds — the MBTI side of the gradient | 1,440 |
| NONE × trader × 4 scenarios × 60 seeds — the reference level | 240 |

**The `swapped` arm** gives O1 the O2 mandate and O2 the O1 mandate, persona text unchanged, as it gives ISFJ the
ENTJ mandate. After the counterpart map the O2 mandate *is* the ENTJ mandate, so O1-swapped and ISFJ-swapped inject
the same bytes.

**Why common start, shown rather than asserted.** On run-level synthetic frames of this design,
`identification_check` returns identified for the OCEAN pair with the NONE reference (persona rank 2, directive
rank 2, start rank 0, persona-to-directive canonical correlation 0.47) and **not identified** for the pair without it
(clause iv). A pooled frame of both pairs with the reference is identified either way, but with the directive
labelled per persona (mandate:ISFJ beside mandate:O1_conservative, one text under two labels) its persona-to-directive
canonical correlation is 0.82 against 0.37 with the directive relabelled by risk category. The two per-vocabulary
frames are therefore the registered read and the pooled, relabelled frame a check (`tests/test_v2_1_e7.py`).

**The harness change, declared.** `agent/v2_prompts.MANDATE_COUNTERPART` resolves O1 to ISFJ's and O2 to ENTJ's
mandate before any wording level is applied; the system prompt — the trait text — is untouched. What this does and
does not move, measured:

- every mandate block is byte-equal across each pair at all eight wording levels and all four block kinds, and the
  swapped blocks are byte-equal (`test_ocean_mandate_is_its_counterparts_at_every_wording_level`);
- **0 of the 540 prompt hashes** stored across the nine manifests on disk moved; `Env_Code_Hash` is unchanged
  (`test_no_mbti_prompt_hash_moved`); the Phase-8 golden check's diff is the same 40 mixed-model floating-point lines
  before and after, with 0 prompt lines;
- `agent/v2_prompts.py` is one of the eight sources the manifest fingerprint hashes, so every manifest's
  `sources_sha256_lf` for that file now differs from the working tree — as the five stage-1 manifests' already did for
  `tools/phase9/e9_roster.py`. Their runs are complete and still verify; nothing of theirs is resumed; and E7's own
  manifest carries the new hash. The cluster clone must be at the commit carrying the map before this manifest is
  run, or the fingerprint refuses it.

**Manifest.** `e9_4/manifest_ocean_open.json`, sha256
`03d13524cabc03b3f42c586710ecc2954b8d38260865a4fc821aab232f94022b`, subdir `stage2_ocean`, 36 prompt-hash keys (six
configurations × two personas × three arms), `Env_Code_Hash` 1d689aaf82a33a2e. The O1 memory block it injects equals
ISFJ's memory block byte for byte; the O1 prompt hash differs from ISFJ's because the system prompt does
(`test_e7_manifest_on_disk_is_its_cells_and_roster`).

**Cost**, 1,440 runs × each model's measured GPU-hours per run (`e9_4/selection/cost.csv`, n = 2,928 runs per model):

| model | GPU-h | model | GPU-h |
|---|---|---|---|
| Gemma 4 31B | 8.11 | Phi-4 | 2.75 |
| OLMo 3.1 32B | 5.28 | Llama 3.1 8B | 2.60 |
| Ministral 3 14B | 3.47 | Gemma 4 E4B | 1.31 |

**23.5 B200 GPU-hours projected**; E5 ran at 0.74–0.80 of its projection (`STAGE2_OPERATIONS.md` 3), which would
put E7 at 17–19. Floor on four GPUs 5.9 h; every model sharded in two, 6.1 h at 96.6 % (section 7).

## 2a. Power at S = 60, and the model it does not cover

`HEADLINE_MODEL_SELECTION.md` 3.5 gives the seeds each model needs for band-MAS at Δ = 0.05, α′ = 0.05/36 and power
0.80, from its own largest-cell σ_d at 122 pairs per cell, with the band-MAS MDD this design achieves:

| model | S needed | MDD at S = 60 |
|---|---|---|
| OLMo 3.1 32B | 2 | 0.007 |
| Phi-4 | 42 | 0.038 |
| Llama 3.1 8B | 46 | 0.040 |
| Gemma 4 31B | 52 | 0.042 |
| Gemma 4 E4B | 66 | 0.048 |
| **Ministral 3 14B** | **246** | **0.093** |

Five of the six are covered at S = 60 or close to it. At 60 seeds the smallest difference this design can detect for
Ministral is 0.093, roughly twice the registered Δ, so a null in its cells is **uninformative about effects between
0.05 and 0.09** and is reported as such. P2, an equivalence prediction, excludes an underpowered model's cells from
its count for exactly this reason and reports them beside. Registered in advance, not discovered afterwards.

## 3. The confirmatory analysis

- **One family per model**: the **vocabulary contrast within arm**, OCEAN − MBTI for `static`, `memory` and
  `swapped`, × the two persona pairs × 4 scenario cells × tier C's three metrics (band-MAS, D at θ 0.05, D at
  θ 0.002) = **m = 72**, decided by BH within the family at q = 0.05, through `tools/stats_v2.run_stats_v21`
  (seed-level pairs, `pigeonhole_ci` at 1,999 draws, seed 0, one-way by path with a single model). Cliff's δ beside.
- **The pairing is by seed and path**: an O1 run and its ISFJ twin share the scenario, seed, arm and generator
  configuration, so `seed_level_pairs` pairs them exactly as E4 pairs the two tracks.
- **Construction.** E3's ISFJ and ENTJ rows are filtered to seeds 10001–10060 and relabelled `static_M` / `memory_M`
  / `swapped_M` under the persona labels `conservative` and `aggressive`; E7's rows keep `static` / `memory` /
  `swapped` under the same two labels. The relabelling is mechanical and in `tools/phase9/e9_5_e7_analyse.py`, and the
  contrast `static − static_M` reads "replace the MBTI narrative with the OCEAN trait profile, mandate held fixed".
  It is also what stops `seed_level_pairs` — which groups on (Model, Persona, Scenario_Cell, Seed, Arm) and ignores
  both `Manifest` and `Setting`, and both sides carry the setting `common_start` — from averaging O1's static runs
  with ISFJ's into one mean with no error. A pairing check runs first, per model: every (persona, cell, seed) key
  carries all six arms and no (key, arm) comes from two manifests, or the model is refused.
- **The decision** is BH within the model's family. A claim reads: *for model m, replacing the MBTI narrative with
  the OCEAN trait profile, the mandate held byte-identical, changes this metric for this persona in scenario c under
  this arm, in the direction of the estimate.* No claim about models in general is made from these tests.
- **The second registered read: the vocabulary × arm interaction**, (memory − static)_OCEAN − (memory − static)_MBTI
  on the same seed and path, per model × persona × scenario cell on band-MAS (the other two tier-C metrics beside).
  Its **90 % one-way path-bootstrap interval** is read against E5's registered equivalence margin of **0.025**, half
  of Δ — the two-one-sided-tests reading E5 registered for its level × arm interaction. A cell is **admitted** only
  when at least one vocabulary's mandate effect reaches **0.01**, E2's registered floor: two arms pinned at the
  metric's floor must differ by 0 and must not be read as "equivalent" by arithmetic (E4's P2 lesson).
- **The salience shares** are computed by `evaluation/salience.py` `salience_by_window(identification="v2_1")` on
  two frames per model, each run through `identification_check` first and each identified on its own: the **OCEAN
  frame** (O1, O2 under the three arms, plus E3's NONE trader) and the **MBTI pair frame** (ISFJ, ENTJ under the same
  three arms, plus the same trader). The seed-cluster bootstrap at **200 refits per window** with the P8-18 fold fix.
  The pooled frame with the directive relabelled by category is reported as a check. `identified_as_registered` is
  false on clause (i) at common start, the known addendum-10 artefact, and every share row carries that flag. Shares
  are **never** pooled with any start-at-target run. The MBTI pair frame is E7's construction — E3's registered frame
  holds INTJ — so its numbers are E7's and are not quoted as E3's.
- **The day-1 gate's persona side** is `evaluation/salience.py` `separability_gate` on each pair's day-1 cash share
  (the two persona labels, every persona arm, as `tools/report_v2.gate_tables` populates it; the static arm alone
  beside). Its **null is NOT COMPUTABLE** under NONE alone (P8-14), is reported as such, and no pass/fail is claimed.
- **How the function is called, and the trap checked before it could bite.** `run_stats_v21` iterates
  `question_families()`, a fixed shared dict. On the raw OCEAN frame it fires Q1's `memory − static` and Q2's
  `swapped − memory`: two families, `by_across`, and no registered contrast. On the frame worded above it fires the
  same two **within the OCEAN rows** and reports them under `bh_within` — E4's failure, the registered rule on the
  wrong question. The family is therefore passed explicitly through `run_stats_v21(families=...)`, as E3 and E4 pass
  theirs, and `test_e7_registered_family_is_absent_from_the_shared_dict` states both facts. The decision rule must
  read `bh_within`; a frame yielding more than one tier-C family is re-framed, never reported under a rule it did not
  use.
- **Before any claim**, per model and cell: the parse-fallback share, the zero-trade share, the static arm's mean cash
  share, the identification verdict of each frame, and the test that the three mandate blocks are byte-identical
  across the pair.
- **Completeness.** A model's family is read once `e9_4_grid --stages verify --only ocean_open` passes for it, and
  only against E3 rows that already verified. A run abandoned after three non-ok attempts is reported missing.
  Nothing is imputed and no model is substituted.

## 4. Predictions, stated in advance

E3's common-start slice gives the MBTI side already, pooled over the four scenarios on 240 pairs per entry
(`e9_4/per_run.csv`, manifest `e9_4_stage2_slice`), band-MAS:

| | ISFJ static | ISFJ memory − static | ENTJ static | ENTJ memory − static |
|---|---|---|---|---|
| OLMo 3.1 32B | 0.075 | +0.021 | 0.012 | −0.012 |
| Gemma 4 31B | 0.027 | +0.016 | 0.200 | +0.078 |
| Gemma 4 E4B | 0.130 | −0.031 | 0.000 | −0.000 |
| Llama 3.1 8B | 0.033 | +0.041 | 0.439 | −0.244 |
| Phi-4 | 0.068 | +0.023 | 0.386 | −0.345 |
| Ministral 3 14B | 0.077 | +0.015 | 0.136 | −0.119 |

ISFJ's pooled memory effect reaches +0.01 in **5 of 6** models; 20 of its 24 cells reach it. ENTJ's reaches 0.01 in
magnitude in **17 of 24** cells; Gemma 4 E4B's four ENTJ static cells sit below band-MAS's floor of 0.001 (4 of 48).
Every prediction below carries a floor or admission guard, so that a cell that cannot move cannot count as support.

**P1 — the persona share dominates, and is vocabulary-invariant.** On the OCEAN frame, S_persona > S_directive in at
least **five of the six** models; and |S_persona(OCEAN) − S_persona(MBTI pair)|, each the mean over readable windows,
is at most **0.15** in at least **four of the six**. A window whose surrogate out-of-fold R² is below **0.5** — the
v1 gate's own surrogate criterion — is unreadable, a frame with more than half its windows unreadable makes the model
unreadable, and an unreadable model counts toward neither bar. Rationale: Phase 8's known-answer recovery on this
design gave S_persona 0.979; the OCEAN-labelled known answer in `test_e7_known_answer_shares_on_an_ocean_frame`
recovers it too. "The interval on S_directive covers 0" is not claimed (P8-18).

**P2 — the static arm is vocabulary-equivalent within Δ.** The 90 % interval of the static-arm OCEAN − MBTI band-MAS
contrast lies inside ±0.05 in at least **two thirds** of the counted cells over the 48 model × persona × scenario
cells. A cell with both static arms below the 0.001 floor is degenerate; an underpowered model's cells (MDD at S = 60
above Δ: Ministral) cannot pass and are reported, not counted. Rationale: both texts name the same risk category and
the same decision style; what differs is the vocabulary that names it.

**P3 — the memory effect replicates with magnitude.** O1's band-MAS memory − static, pooled over the four scenarios,
is at least **+0.01** in at least **five of the six** models, as ISFJ's is above (its exception, Gemma 4 E4B, falls
under memory at common start); and O2's and ENTJ's memory − static agree in sign in at least **two thirds** of the
aggressive cells where both reach 0.01. Rationale: stage 1 found ISFJ worsening under memory in all nine open-weight
models and E3 found it in 5 of 6 at common start; the magnitude floor is what keeps a sign at 10⁻⁴ from passing.

**P4 — framework independence.** The 90 % interval of the vocabulary × arm interaction on band-MAS lies inside
±0.025 in at least **two thirds** of the admitted cells. At least 37 of the 48 cells are admitted by the MBTI side
alone (20 ISFJ + 17 ENTJ cells at or above 0.01). This is the prediction that would most change the paper if it
failed: a memory effect that depends on the vocabulary the persona is written in is a property of the prompt, not of
the mandate.

**P5 — the day-1 gate's persona side tracks across vocabularies.** |AUC(O1 vs O2) − AUC(ISFJ vs ENTJ)| on the day-1
cash share at common start is at most **0.10** in at least **four of the six** models. No pass or fail of the gate is
claimed; its null is not computable here. Rationale: on v1's data the OCEAN pair's pooled AUC (0.624) and the MBTI
triple's (0.527) were both near chance under a 100 %-cash start, which says nothing about a common start; this
prediction is the first measurement.

**How they are read.** Descriptive, outside every BH family, through `tools/phase9/e9_5_predictions.py` with its four
verdicts; P1 and P5 are `unevaluated` until the per-step job has run. A wrong prediction is reported as wrong.

## 5. Exploratory, with no claim

The within-OCEAN family {memory, swapped} − static (m = 48, E3's registered family on the new vocabulary), reported
with intervals beside E3's MBTI family; the pooled-frame shares; R5 over the six with its power stated; tier S in its
own families; the shares by window across the run; seconds and tokens per run.

## 6. Not in this experiment

O3 and any numbers-only persona (section 0); the `numeric_only` wording; Track A on the OCEAN pair; INTJ and any
balanced OCEAN profile; E2's placebo arms; E5's generator sweep; E6; E8; the mechanistic appendix. No share is
reported from any other design, and nothing here is pooled with a start-at-target run.

## 7. How it runs

As E2–E5: one SLURM array on `hpg-b200` under fire-finai, `STAGE=ocean`, `--array=0-11%4` (every model in two
shards, P9-22), 1 B200 / 6 cores / 44 GB per task, pinned revisions, the twelve-call parse preflight, checkpointed
runs, P9-20's per-server concurrency. The cluster clone is first brought to the commit carrying
`MANDATE_COUNTERPART`. After the array: `pack_stage.sbatch` with `STAGE=ocean`, `e9_4_grid --stages verify,score
--only ocean_open`, the Hugging Face push, then `tools/phase9/e9_5_e7_salience.py` on the cluster against
`stage2_ocean` and `stage2_slice` (its `salience_summary.json` is pulled with `per_run.csv`), and
`tools/phase9/e9_5_e7_analyse.py`. The manifest's sha256 and this file's are recorded in `DECISION_LOG.md` before
the first call.

## 8. Deviations

Nothing above changes after the first run of this manifest. A deviation is recorded as a numbered addendum to this
file with its reason and with what had already been seen when it was made.
