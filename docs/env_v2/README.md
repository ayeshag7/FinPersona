# docs/env_v2 — the synthetic market environment, v2 and the v2.1 programme

Everything about the rebuilt environment lives here. The v2 design plan it implements is `docs/planning/FinPersona-Bench_Synthetic_Environment_v2_Plan_Aug2026.docx` (research notes in `docs/planning/env_v2_research/`). Code: generator `envs/v2/` with its fitted parameter files `envs/v2/params/*.json` (facade `envs/synthetic_market.py`, frozen v1 in `envs/v1/`), harness `agent/` + `simulation/` + `experiments/arms_v2.py`, evaluation `evaluation/`, one tool package per phase (`tools/phase1/` … `tools/phase9/`), cluster tooling `tools/cluster/`, tests `tests/`.

**Everything under `docs/` is tracked and pushed.** The git-ignore entries that name paths in here (`generated/v2_1/`, the compute guides, the model-cost files) stop *new* files appearing; the 1,535 files already tracked stay tracked. The only documentation that lives on disk alone is what `.gitignore` has always excluded: the downloaded reference papers and the third-party `datasets/` panel.

## Layout

| Folder | What is in it |
|---|---|
| `spec/` | v2 as built and as each phase rewrote it: `E1_V2_GENERATOR_SPEC.md` (blocks, parameters, calibration choices, deviations, validation table — the volatility, observables and validation sections carry the v2.1 rewrites inline), `IO_CONTRACT.md` (observation, portfolio, action, logging), `CALIBRATION_REPORT.md` (parameters in force, checklist, hazard grid, audit tables) |
| `preregistration/` | `PREREGISTRATION.md` (thresholds, feature sets, gates written before the v2 runs) and `PREREGISTRATION_AMENDMENTS.md` (every change after, with what was seen before it) |
| `decisions/` | `DECISIONS_13_1.md` (the eleven v2 plan decisions, signed) and `DECISION_LOG.md` — the single running record: the v2 addendum and review round, then one section per v2.1 phase, P0-1 … P9-19, each row giving the decision, its evidence, the alternative rejected and the file |
| `v1_baseline/` | The old environment frozen for comparison: `E0_SUMMARY.md` (freeze, Table 2, day-1 gate, re-scoring, v1 checklist and audit) and `E0_V1_GENERATOR_SPEC.md` |
| `status/` | `E1_E4_STATUS.md` and `PILOT_NOTES.md` — **dated snapshots of 23 Aug 2026**, kept as history with superseding notes inline. They describe v2 as it stood before the v2.1 programme, not the environment in force |
| `generated/` | Machine-written results, never hand-edited: the v1 and v2 checklists, leakage audits, sensitivities, calibration grids, Table 2, rendered prompts (see `generated/README.md`), and `generated/v2_1/` — 1,295 files of phase outputs, `e1_0` … `e9_4`, which the phase reports cite cell by cell |
| `reviews/` | The three independent reviews of v2 (`review_A_parameter_provenance.md`, `review_B_claims_vs_evidence.md`, `review_C_methodology_robustness.md`) and the consolidated list `V2_WEAKNESSES.md` (74 items). Every item is answered by a v2.1 phase or recorded as a residual |
| `v2_1/` | The improvement programme. `V2_1_IMPROVEMENT_PLAN.md` / `.docx` / `.pdf` is the governing document and `V2_1_ALTERNATIVES_REGISTER.md` the 18 open choices with the experiment that decides each; `PREREG_PHASE_k.md` (+ addenda), `PHASE_k_REPORT.md` and `PHASE_k_CHANGED_FILES.md` for k = 0 … 9; `E1_0_DATA_REPORT.md` (the shared data panel); `PREREG_PHASE_9_STAGE1_OPEN.md` and `..._B2.md` (the open-weight headline, both batches); `GRID_EXPERIMENT_PLAN.md` (the grid stages with their cell arithmetic); the execution prompts given to the agents; `reviews/` (the plan review, the verification log, the closing note, the review of Phase 0); `archive/` (the superseded first draft, for the audit trail only) |
| `history/` | **`SYNTHETIC_ENVIRONMENT_HISTORY.pdf` / `.docx` / `.md`**: the whole history of the environment in one document, v1 through v2 to the ten phases of v2.1, with what each version was, what was found wrong with it, what changed, the evidence behind every change and which positions are held by design rather than by a fit. 63 pages, 33 figures, every number carrying its sample size. Built by `tools/history_figures.py` (figures, from the generated result files) and `tools/history_docx.py` (document and PDF). The figure PNGs are not tracked: the blanket `figures/` rule in `.gitignore` excludes them, and the docx and PDF embed them |
| `slides/` | The v2 deck (`FinPersona_env_v2_slides.pdf`) and the speaker script (`SPEAKER_SCRIPT.md`, `.docx`, `.pdf`). **Both predate the v2.1 programme and several of their numbers are contradicted by it**; read `reviews/V2_WEAKNESSES.md` part 6 and `v2_1/DECK_CORRECTIONS_NOW.md` before presenting. Regenerating them from the generated files is Phase 10's work and has not been done; `tools/build_slides.py` and `tools/script_to_docx.py` are not in this checkout |

## Reading order

For the whole story in one place, read `history/SYNTHETIC_ENVIRONMENT_HISTORY.pdf`: it covers v1, v2 and every v2.1 phase and ends with the environment as it stands. The phase reports remain the primary sources it cites. Otherwise:

1. What was wrong with v1 and what v2 changed: `v1_baseline/E0_SUMMARY.md`, then `spec/E1_V2_GENERATOR_SPEC.md`.
2. What was found wrong with v2: `reviews/V2_WEAKNESSES.md` (start with Part 1), then the three reviews.
3. The programme that answered them: `v2_1/V2_1_IMPROVEMENT_PLAN.md` (the governing rule, the phase map, the team decisions D1–D17) with `v2_1/V2_1_ALTERNATIVES_REGISTER.md`.
4. What each phase did: `v2_1/PHASE_k_REPORT.md` with its `PREREG_PHASE_k.md` and addendum, k = 0 … 9. Every decision is in `decisions/DECISION_LOG.md` under its phase.
5. The environment in force: `history/SYNTHETIC_ENVIRONMENT_HISTORY.md` section 17, and the parameter files themselves.
6. What runs on it next: `v2_1/GRID_EXPERIMENT_PLAN.md` and `v2_1/PREREG_PHASE_9_STAGE1_OPEN.md`.

## Status (29 October 2026)

**The environment is complete and frozen.** `Env_Code_Hash` is **1d689aaf82a33a2e**, the first 16 characters of the manifest hash over 30 files (`tests/v2_freeze_manifest.json`, written 17 Sep 2026), and every run row carries it. Phases 7, 8 and 9 and the pre-grid build each moved **0 of 95** path configurations. Every parameter in force carries a provenance label (LIT / FIT / CAL / DESIGN / DERIVED), its interval and its n; the table is `history/SYNTHETIC_ENVIRONMENT_HISTORY.md` section 17.1, and the loader fails loudly on a missing or malformed parameter file.

**The known-defect registry is empty.** `V2_DEFECTS = []` in `tests/known_defects.py` — the programme's acceptance criterion. Two derived leakage gates that the environment does not meet were moved on 16 Sep to permanent **v2.1 residuals**: the shown fields add about **+0.109** of calm-trained R² for the mispricing over a level-free reading of the price path, against a derived margin of +0.038, and the macro-phase clock adds **+0.030** of selectivity against +0.011. Both were closed by the team's Phase 7 decision to **restrict the benchmark's claim to a one-shot mandate-conflict benchmark** rather than by re-tuning the generator or re-specifying the gate, and each is owed one sentence in the paper's limitations.

**Checkpoint 16A was not met** (Phase 6, 9 Sep 2026): G1, G2, G4a and G4b fail 0 of 4 — a constant band edge matches or beats the level-free observables oracle — and G3 passes θ-conditionally (at θ up to 0.05, failing from 0.066). Phase 7 re-stated 16A on MCR, on its band-violation and directional components and per window, and no admissible scoring flips a gate. The team's answer is D17 above.

### The ten phases

Phases 0 to 9 ran from 29 August to 12 September 2026 under one rule — *every generator parameter is fitted or tested on data, never stipulated* — and the six-step protocol of the plan: a literature review with a citation table, a pre-registration written before any run and never edited afterwards, an addendum recording every disconfirmation, runs saved with their seeds and generator hash, decisions recorded with the alternatives rejected, and regression tests locking each decision in.

| Phase | What it settled |
|---|---|
| **0** Verification and freeze | 149 reproduction rows on fresh seeds (97 reproduced, 5 in substance, 16 not, 31 documentary); **every headline review finding held**; the analyst `sqrt(5)` bug fixed, the silent overrides removed, the generator frozen under a hash manifest, the known-defect registry created |
| **E1.0** The shared data panel | The free substitutes downloaded (`datasets/`, git-ignored, re-downloadable via `tools/e1_0_data/`): **set A = 417** flag-free US names with full 2000–2024 histories, set B = 155 shorter. Ticker reuse flagged 86 of 673 series; only 4.7 % of departed names survive both screens, so every tail statistic in the programme is survivor-based |
| **1** Value and price structure | The start-price answer key removed — mechanism **C** (a hidden start of 100 plus a per-seed render scale on \$7.47–240.02); the team's provisional mechanism B **failed both registered rules**. Mean-zero jumps in x; burn-in 260 → **750 days**; μ_V 0.000228/day FIT; estimator C adopted alone after a recovery study rejected the other two |
| **2** Mispricing engine | Franke–Westerhoff reproduced from its paper and the units settled at source (**price scale 1**, a literature bug fix). SMM on 17 moments over 417 stocks: **no engine accepted**, and no FW engine beat the AR(1) out of sample, so **AR(1) + GJR-GARCH-t** was adopted under the pre-registered asymmetric rule. The flat-bias defect closed on the new engine |
| **3** Volatility | The whole block FIT: GJR **α 0.027, γ 0.058, β 0.932**, diffusive ν **6.65**, `sbar` **0.01509** by an exact variance-accounting identity to the panel's 0.0218; jumps **0.000583/day at σ_J 0.230** (v2 had 0.010/day at 0.03); phase multipliers from 1,592 drawdowns and 3,125 run-ups, realised closed-loop. IV rebuilt as a past-only filter with a FIT premium — the one-day panic step fell from z ≈ 7.7 to **0.12**. The engine refit gives **half-life 22.38 d [18.75, 32.64]** |
| **4** Events, schedule, controls, calendar | Durations, depths, front-loading, recovery and the post-top leg drawn from fitted quantile grids over **642 fast crashes** and **3,201 run-ups**; the earnings-quarter grid randomised per seed (93 % of the clock's excess removed); the sustained-bull control replaced by **definition A**, which repaired that scenario's coverage (0.044 → 0.374). The hazard's adoption was **withdrawn** when it was shown to have been measured against a state that did not exist, and the topped-share and rise-time criteria were retired as horizon- and template-dominated |
| **5** Observables | Every field re-anchored: the P/E multiple on 411 stocks and 61,843 stock-months, EPS and losses on 27,515 quarters, announcement lags on 27,242 filings, dividends on 10,666 stock-years, sentiment on a deconvolved news index, volume on 417 stocks. **The eighteen shown fields add +0.026 of R² for the mispricing where they added +0.39 — a 93 % reduction** — and the macro-phase clock's selectivity fell from +10.4 points to +1.8 |
| **6** Audits, checklist methodology, **16A** | Every checklist threshold given an empirical reference from **12,927 real 200-day windows**; every leakage gate derived from a permutation null or a Kalman bound; 30 known-answer tests; the criteria's own size and power measured (criterion B has no size at 200 paths, so the final checklist runs at 500 seeds per scenario). **16A not met**; the programme stopped for the team |
| **7** Targets, action, metrics | θ derived three ways — **θ_info 0.05**, **θ_cost 0.0020**, θ_var 0.0463 — with the first two co-primary; MCR decomposed into **B + D** against a realised ceiling of 0.0028 and a floor from six trivial policies; the bands checked against the environment's own risk and return (a Merton reading would collapse the three personas into one band, so the practitioner bands stay scored and Merton is reported); dividends paid into cash; the day-1 gate re-specified to the common start |
| **8** Harness and statistics | The stateful arm's four defects corrected (the mandate-offset covariate was **37–40× too large**); context length made a factor; **the v2 nested mixed model rejects a true null 36–58 %** of the time once the arm effect varies by model, so the two-way cluster bootstrap decides and the crossed model is descriptive; BY across families, BH within one; only the path-level sign flip holds size as a temporal null; the paid variance pilot (720 runs, \$144.66) sized the grid |
| **9** Sensitivity through the LLM harness | The roster timed, smoked and piloted; the reference distribution for model-level contrasts simulated and **R5** chosen; the three robustness criteria simulated before the stage produced a number (two do not behave as the plan assumes); the parameter ranking computed, selecting the **data-driven six** (the GARCH set, `sbar`, μ_V, the half-life, σ_V, the jump rate). The grid was specified and sized; **E9.4 was not run in the phase itself** |
| **10** Documentation | **Not done.** The claims ledger (`v2_1/CLAIMS_LEDGER.md`) does not exist, the deck and speaker script have not been regenerated, and `status/` still carries its 23 Aug snapshots. The history document is the part of it that landed |

### The main grid: the open-weight headline, stage 1

Phase 9's API roster was set aside — stage 1 as first designed priced at \$126,000, the Anthropic credit ran out mid-pilot, and the remaining budget was \$184.73 of OpenRouter credit. **Stage 1 of the headline instead ran on open weights served by our own vLLM 0.29.0 on HiPerGator B200s** (DECISION_LOG P9-11 … P9-19), at 64 in-flight calls per model, each configuration pinned by Hugging Face revision.

- **Nine models × 2,928 runs each = 26,352 runs** of 200 simulated days: 3 personas × (static, memory) × 4 scenarios × **122 seeds** (10001–10122, the same paths for every model), R = 1, T = 200, `Env_Code_Hash` 1d689aaf82a33a2e.
- Batch 1, submitted 24 Oct as SLURM array 47506868: Gemma 4 31B, Gemma 4 E4B, gpt-oss-20b, Muse Glimmer 30B, OLMo 3.1 32B, Ministral 3 14B. Batch 2, submitted 26 Oct as array 47800184 on the same cells: Llama 3.1 8B, Llama 3.1 70B, Phi-4, chosen as the models the comparable published studies run.
- The seed count is the paired-correct count at the plug-in σ_d — gpt-oss-20b's band-MAS 90 % limit of 0.1364 — giving power of at least 0.803 at Δ = 0.05 for every model in batch 1 and above 0.999 for batch 2.
- **`e9_4 --stages verify` passes: 2,928 of 2,928 present for all nine, 0 missing, 0 mismatched.** Seven models pass all 19 validation checks; Gemma 4 31B (38 parse fallbacks in 585,600 decisions) and Muse Glimmer 30B (2) fail only the zero-fallbacks check and keep them as model behaviour.
- The per-run CSVs are **not in this working tree**: they live on the cluster and in the private Kaggle dataset `finpersona-open-headline-stage1` (81,194 files, 7.6 GB — see `docs/KAGGLE_DATASETS.md`). What is tracked here is the manifests, the nine ledgers (one JSON row per run), the verification and validation reports, the sizing and the cluster logs, under `generated/v2_1/e9_4/`.

**Not yet done: the runs are not scored.** `generated/v2_1/e9_4/per_run.csv` holds the four rows of the E0 dress rehearsal. The confirmatory analysis registered in `v2_1/PREREG_PHASE_9_STAGE1_OPEN.md` §3 — BH within each model's own family of 36 (3 personas × 4 scenarios × 3 tier-C metrics) through `tools/stats_v2.run_stats_v21`, with the parse-fallback, zero-trade and static-arm cash preconditions reported per cell before any claim, and the 18 registered per-model-and-persona predictions read against their signs — is the next step.

### What runs after it

`v2_1/GRID_EXPERIMENT_PLAN.md` holds the stages with their cell arithmetic. Its state table and backlog are written as of 17 Sep and are overtaken on two points: the E0 dress rehearsal has run, and the `fingerprint()` keying bug it describes is fixed (the probe is built from a real manifest cell, so Track A verifies).

| Stage | State |
|---|---|
| E1 headline | stage 1 done on nine open-weight configurations, **unscored**; the API roster is set aside |
| E2 causal package (declarative and directive placebos, wrapper-only) | not run; needs a manifest stage. It decides whether the headline is written as content attribution or as a negative control |
| E3 common-start slice | manifest built; **deferred out of stage 1** by P9-14 (4,880 runs per model at 122 seeds). It is the only design in which the salience shares are identified |
| E4 Track A (stated vs unstated target) | manifest built, keying fixed, 0 runs |
| E5 parameter sensitivity, the data-driven six | not run; needs a manifest stage with per-cell `env_config`. This is Phase 9's actual purpose, and the robustness table (E9.5) needs it together with E1 |
| E6 context length, the decay thesis | not run; the stateful arms have never been sized, so it needs a pilot first |
| E7 OCEAN vocabulary gradient | the O1/O2 personas are on the v2 harness; not run |
| E8 re-injection frequency k-sweep | small; a replication of Li et al. (COLM 2024), to be cited and not headlined |
| E9 mechanistic M2 / M3 | greenfield; see `MECH_INTERP_BRIEF.md` at the repo root. Gated on E2 |

## The grid runner branch

The finalised environment also lives on the branch `synthetic-env-grid`, cut from `main` by deleting everything the main grid does not need: no phase reports, no pre-registrations, no decision log, no analysis tools, no v1 generator, no old results, no data panel. What stays is the generator and its fitted parameters, the harness, the scoring layer, the grid tooling, the tests and a README of its own. It exists so that a long run happens against a small, reviewable surface, with no doubt about which code produced it. It is a branch of this repository and not a fork, and **the two branches are level**: the pre-grid freeze and the pre-grid build were both ported (`d01eda7`, `2151cb5`), so the freeze manifest reports the same `Env_Code_Hash` **1d689aaf82a33a2e** over the same 30 files on both, and the 95 path configurations reproduce the frozen reference with 0 changed. Nothing is developed there that is not also here.

```
git checkout synthetic-env-grid     # the runner branch
git checkout main                   # back to the full project
```

## Regenerating results

```
python -m tools.freeze_manifest --check                             # the v2.1 freeze (tests/v2_freeze_manifest.json)
python -m tools.path_hashes --out ph.json                           # the 95-configuration fixture
python -m pytest tests/ -q                                          # test_leakage_ci.py is slow; the registry prints at the end
python -m tools.gen_table2 --env v2                                 # generated/table2_v2_from_code.*
python -m evaluation.stylized_facts --env v2 --seeds 500 --T 200    # the checklist at the Phase-6 seed count
python -m evaluation.leakage_audit  --env v2 --seeds 50  --T 200    # generated/leakage_audit_v2.md
python -m tools.l5_report                                           # generated/l5_observables_oracle.*
python -m tools.verify_v2_findings                                  # generated/v2_1/findings_reproduction.md (Phase 0, ~11 min)
python -m tools.regen_checklist_md --check                          # checklist .md footers vs CSVs
python -m tools.history_figures && python -m tools.history_docx      # the history document and its 33 figures
```

The grid, against the frozen environment:

```
python -m tools.phase9.e9_4_grid --stages manifest_open             # or manifest, manifest_open_b2
python -u -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_headline_open.json
python -m tools.phase9.e9_4_grid --stages verify,score,status       # score needs results_v2/ present
python -m tools.stats_v2                                            # the registered contrasts
```

Each phase's own experiments are re-run from its tool package: `python -m tools.phase<k>.<experiment>`, named in that phase's report beside every number it produced.
