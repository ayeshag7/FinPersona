# FinPersona-Bench — Repository Guide

A map of the codebase: what each part does, how the pieces connect, how they map to the
paper, and where the rough edges are. For how to *run* things, see the top-level
[`README.md`](../README.md); for the environment's design, evidence and current status, see
[`env_v2/README.md`](env_v2/README.md). This document is about *understanding* the repo.

---

## 1. The mental model

**The repo holds two generations of the benchmark, side by side.**

- **v1** is the pipeline that produced the submitted COLM paper: `envs/v1/`, the four agent
  classes, `simulation/runner.py`, the `results_*` directories and the `analysis_*` scripts.
  It is frozen. Three review cycles found its instrument did not measure what the paper said
  it did, so it is kept for provenance and for the baselines the v2.1 work re-scores against.
- **v2.1** is the rebuilt environment and everything around it: `envs/v2/` with fitted
  parameter files, a single configurable agent with a registry of 20 arms, a derived scoring
  layer in `evaluation/`, one tool package per improvement phase in `tools/phase1/` …
  `tools/phase9/`, and the grid tooling that runs the main experiment. It is **frozen under a
  hash manifest** and is what the revision runs on.

Data flows top to bottom in both generations:

```
  Generator           envs/v2/ (or envs/v1/)        hidden V, mispricing x, 19 rendered fields
        |
  Harness             agent/v2_agent.py + simulation/runner_v2.py + experiments/arms_v2.py
        |
  Run data            results_v2/<...>/            one CSV row per trading day, + meta + usage
        |
  Scoring             evaluation/                   band-MAS, MCR = B + D, baselines, audits
        |
  Statistics          tools/stats_v2.py             paired contrasts, bootstrap, BH / BY
```

The whole design rests on the hidden fundamental value `V` being generated independently of
price, so behavioural drift is measured against a known ground truth rather than a subjective
consensus. In v2 onwards the decomposition is `log P = log V + x`; the agent never sees `V`
or `x`, and a day is *resolvable* when `|x| >= theta`.

### What is frozen, and why it matters

`tests/v2_freeze_manifest.json` holds SHA-256 hashes over **30 files** — the generator, its
parameter files and the evaluation modules that score it. The first 16 characters of the
manifest hash are the `Env_Code_Hash` that **every run row carries**: `1d689aaf82a33a2e`.
`tools/path_hashes.py` hashes 95 fixed path configurations; a change that is meant to be inert
must move 0 of them. If your checkout reports another hash, you are not running the
environment the revision describes.

```
python -m tools.freeze_manifest --check
python -m tools.path_hashes --out ph.json
```

---

## 2. The v2.1 stack

### 2.1 Generator — `envs/`

| Path | Role |
|---|---|
| `envs/synthetic_market.py` | Facade with the v1 public API plus the v2 extras; Table 2 definitions and audit helpers. Routes to v1 or v2 |
| `envs/v2/generator.py` | The day loop: value, mispricing, volatility, events, observables |
| `envs/v2/rng.py` | Named, independent RNG streams (append-only registry); the global numpy RNG is never touched |
| `envs/v2/mispricing.py` | The engine: AR(1) with a GJR-GARCH-t innovation (the Franke–Westerhoff forms stay behind their names as sensitivities) |
| `envs/v2/garch.py`, `volatility_params.py` | Fitted GJR-GARCH-t block and the phase variance multipliers |
| `envs/v2/events.py`, `schedule.py`, `events_params.py` | Scripted crash and bubble phases, the hazard, the fitted duration and depth grids, the orderings |
| `envs/v2/observables.py`, `observables_params.py` | The 19 rendered fields: P/E and its hidden multiple, EPS and losses, dividends, the analyst estimate, sentiment, volume, implied volatility, the technicals |
| `envs/v2/params/*.json` | **Where the numbers live**: `value`, `mispricing`, `volatility`, `events`, `hazard`, `observables`, plus the stored burn-in states. Each entry carries its value, its provenance label (LIT / FIT / CAL / DESIGN / DERIVED), its interval, its n and its status; the loaders raise loudly on a missing entry, a null interval or an undeclared status |
| `envs/v1/` | The v1 generator and portfolio tracker, frozen at tag `v1-env-freeze` |

Every v2.1 change is a **switch with the v2 behaviour behind it** (`obs_mode="v2"`,
`iv_mode="v2"`, per-block `design` keys), proved inert when off against the 95-configuration
fixture.

### 2.2 Harness — `agent/`, `simulation/`, `experiments/`

| Path | Role |
|---|---|
| `agent/v2_agent.py`, `agent/v2_prompts.py`, `agent/render.py` | One configurable stateless agent — *the arm is a configuration, not a class* — and the prompt construction |
| `agent/stateful_agent.py` | The memory-carrying arms: rolling window (5 / 20 / 50), full transcript, running summary |
| `agent/llm_factory.py` | Provider routing. A model name prefixed `vllm/` goes to an OpenAI-compatible local server; no adapter to write |
| `agent/personas/mbti_profiles.json` | 16 MBTI types + `EXPERT` / `NONE` + the OCEAN archetypes |
| `agent/params/harness.json`, `harness_params.py` | Harness version, the mandate-offset definition, the token-count hierarchy, the matched placebo, the context budget |
| `agent/schemas.py` | `TargetAllocation` — the v2 action is a **float** target cash share, not an enum |
| `simulation/runner_v2.py` | The day loop: per-row referee fields, factors, provenance hashes, parse status |
| `simulation/portfolio_v2.py`, `dividends.py` | Target-share accounting, dead band, 5 bp cost, dividends paid into cash |
| `simulation/provenance.py` | `Env_Code_Hash`, prompt and system-prompt hashes, temperature, revision — on every row |
| `experiments/arms_v2.py` | **The arm registry (20 arms)** and the grid CLI: `static`, `memory`, `placebo_declarative`, `placebo_directive`, `wrapper_only`, `swapped`, `trader`, `trader_maximise`, the two `path_b_*` arms and ten stateful variants. Also the factor defaults (wording, track, start design, cost visibility, horizon disclosure, field order, ordering) |
| `experiments/params/inference.json`, `inference_params.py` | The registered inference settings: minimum effect, α, the sizing rule, the metric tiers |

### 2.3 Scoring and audits — `evaluation/`

| Path | Role |
|---|---|
| `evaluation/scoring.py`, `scoring_params.py`, `params/scoring.json` | The scoring in force: θ co-primary at 0.002 and 0.05, MCR decomposed into band violation **B** and direction **D**, the ceiling (the mandate oracle through the real simulator, 0.0028 realised) and the floor (the worst of six trivial policies) |
| `evaluation/metrics_v2.py` | point / band / relative MAS, RG, MCR, return, max drawdown, turnover, cost, fallback and zero-trade accounting |
| `evaluation/targets.py` | The persona cash bands: 0.70–0.90 / 0.40–0.60 / 0.00–0.20 |
| `evaluation/baselines_v2.py` | Twelve rule policies run on the cell's own path, from its own start |
| `evaluation/observables_oracle.py` | The level-free and price-only surrogates for `x` |
| `evaluation/stylized_facts.py` | The 20-item checklist, judged against the real reference distribution |
| `evaluation/reference_stats.py`, `criteria.py`, `params/phase6_criteria.json` | The reference distribution of every statistic over **12,927 real 200-day windows**, and the derived criteria and leakage gates |
| `evaluation/leakage_audit.py` | L1 (algebraic inversion), L2 (surrogate), L2b (phase clock), L4 (resolvability), with the derived margins |
| `evaluation/salience.py`, `separability_gate.py` | The salience shares (identified only on a common-start slice) and the day-1 persona gate |
| `evaluation/rescore_v1.py` | The v1 runs re-scored under the v2 definitions |

### 2.4 Tools — `tools/`

One package per improvement phase, named for the experiment it runs, so every number in a
phase report is re-runnable as `python -m tools.phase<k>.<experiment>`:

| Path | Role |
|---|---|
| `tools/e1_0_data/` | The shared data panel: fetch, screen for ticker reuse, cross-check two price sources, write per-folder READMEs and manifests. Output is `datasets/`, git-ignored |
| `tools/phase1/` … `tools/phase8/` | The per-phase experiments, their `apply_*.py` writers (which are what edit the parameter files) and their `*_report_tables.py` (which generate the report tables the tests read back) |
| `tools/phase9/` | The grid: `e9_roster.py` (configurations pinned by revision), `e9_2_pilot.py` (sizing), `e9_4_grid.py` (manifest / verify / score / status), `e9_launch.py` and `e9_runner.py` (execution, fingerprinting, checkpointing) |
| `tools/cluster/` | SLURM and vLLM: `preflight_vllm.py`, `validate_pilot.py`, `validate_headline.py`, `assemble_llama.py`. Local only, not pushed |
| `tools/freeze_manifest.py`, `path_hashes.py` | The freeze and the inertness fixture |
| `tools/stats_v2.py` | The statistics track: paired contrasts, the two-way cluster bootstrap, the crossed mixed model (descriptive), BH within a family and BY across |
| `tools/report_v2.py`, `gen_table2.py`, `l5_report.py`, `regen_checklist_md.py` | Reporting and the generated tables |
| `tools/history_figures.py`, `history_docx.py` | The 63-page history document and its 33 figures, drawn from the result files |
| `tools/hf_backup.py` | Off-site backup of everything GitHub does not hold, with a credential and cluster-identifier scan that must pass before anything leaves |

### 2.5 Tests — `tests/`

268 tests. One file per phase (`test_v2_1_phase_0.py` … `_9.py`) plus the generator, harness,
evaluation, action-space, freeze, provenance and documentation-number suites.

- `tests/known_defects.py` is the **known-defect registry**. `V2_DEFECTS` is empty — the
  programme's acceptance criterion. `V2_1_RESIDUALS` holds the two derived leakage gates the
  environment does not meet and that no phase will fix, because the team closed them by
  restricting the claim; `V1_BASELINE_XFAILS` holds the permanent v1 baselines. Each is a
  *strict* xfail, so it fails loudly the moment the defect disappears.
- `tests/test_docs_numbers.py` checks documents against the canonical generated numbers.
- `tests/test_leakage_ci.py` is slow (most of the suite's wall clock). The registry and its
  observed outcomes print at the end of every session.

---

## 3. The v1 stack (the paper's provenance)

Kept, not developed. Do not add to it.

| Path | Role |
|---|---|
| `agent/static_agent.py`, `memory_agent.py`, `freq_agent.py`, `ocean_*_agent.py`, `prompts.py`, `legacy_agent.py` | The four v1 agent classes and their prompts |
| `simulation/runner.py`, `ocean_runner.py`, `portfolio_tracker.py`, `legacy_runner.py` | The v1 day loop and accounting |
| `experiments/run_experiments.py`, `run_ocean_experiments.py`, `run_injection_freq_claude.py`, `run_long_horizon.py`, `run_t_calibration.py`, `run_backtest.py` | The v1 run matrices. Run from the repo root |
| `analysis_may/`, `analysis_ocean/` | The v1 analysis suites (MAS, CI, RG, effect sizes, the persona classifier, the hero figure) |
| `placebo_reinjection_control/`, `rationale_linguistic_analysis/` | Self-contained v1 mini-experiments |
| `legacy_market_data/` | The pre-synthetic historical-data environment |
| `annotation_app/` | Streamlit app for human evaluation of rationale quality |

**Two v1 results are carried with a warning.** Cycle 2 found the persona classifier was
trained on days 1–5 rationales from *both* arms with no `Agent_Type` filter, so it detects
mandate vocabulary rather than persona expression; every classifier-derived number is
quarantined. And `MAS_ISFJ` is identically `1 − mean cash`, so validating a cash-predicting
quantity against it is circular.

---

## 4. Where run data lives

| Path | Contents | In git? |
|---|---|---|
| `results_v2/` | The v2.1 run data: one CSV per run plus meta and usage files. **Not in this working tree** — stage 1 of the headline lives on the cluster and in the private Kaggle dataset `finpersona-open-headline-stage1` (81,194 files, 7.6 GB; see [`KAGGLE_DATASETS.md`](KAGGLE_DATASETS.md)) | no |
| `docs/env_v2/generated/v2_1/` | What *is* kept: manifests, per-run ledgers (one JSON row per run), verification and validation reports, sizing, cluster logs, and every phase's derived tables | yes (1,295 files; new files are now git-ignored) |
| `results_ocean/`, `results_long_horizon/` | v1 OCEAN and T=800 runs | yes |
| `results_april/`, `results_may/`, `analysis_april/` | v1 main panels | no (git-ignored) |
| `datasets/` | The third-party data panel. Several sources forbid redistribution; re-download with `tools/e1_0_data/` | no |

---

## 5. How the repo maps to the paper

| Concept | Where it lives |
|---|---|
| Personas and their cash bands | `agent/personas/mbti_profiles.json`, `evaluation/targets.py` |
| Scenarios (flat / bull_trap / crash / sustained_bull) | `envs/v2/events.py`, `schedule.py` |
| Static vs memory, and the causal arms that separate content from imperative force from position | `experiments/arms_v2.py` (`static`, `memory`, `placebo_declarative`, `placebo_directive`, `wrapper_only`, `swapped`) |
| The scoring (band-MAS, MCR = B + D, θ) | `evaluation/scoring.py` + `params/scoring.json` |
| The main experiment (the open-weight headline) | `tools/phase9/`, registered in `env_v2/v2_1/PREREG_PHASE_9_STAGE1_OPEN.md` and `..._B2.md` |
| Why each parameter has its value | `env_v2/history/SYNTHETIC_ENVIRONMENT_HISTORY.pdf`, with the phase reports as primary sources |
| What the benchmark may and may not claim | `reviews/cycle2/reviewer_C_areachair.md` (the GO conditions) and the two v2.1 residuals in `tests/known_defects.py` |
| The mechanistic track | `MECH_INTERP_BRIEF.md` at the repo root |

---

## 6. Rough edges

1. **`pyproject.toml` is v1-era.** Its dependency list predates the v2.1 work: `scipy`,
   `scikit-learn`, `statsmodels`, `arch`, `matplotlib`, `python-docx` and `requests` are all
   imported by code in `evaluation/` and `tools/` and none is declared. There is still no
   editable install, so everything runs from the repo root.
2. **Month-based naming survives in the v1 layer.** `results_april`, `results_may`,
   `analysis_may` name work by when it was run. They are frozen, so the cost is only to a
   newcomer reading them.
3. **Inconsistent git tracking of v1 results.** `results_ocean` and `results_long_horizon`
   are committed; `results_april`, `results_may` and `analysis_april` are ignored.
4. **Duplicate script names** in `analysis_april/` and `analysis_may/`
   (`numerical_analysis.py`, `summarize_t_calibration.py`); `analysis_may/` is the
   authoritative one.
5. **Phase 10 has not run.** The claims ledger does not exist, the v2 deck and speaker script
   still carry pre-v2.1 numbers, and `docs/env_v2/status/` holds 23 Aug 2026 snapshots. Those
   documents are marked where they are stale rather than silently corrected.
6. **`docs/env_v2/generated/v2_1/` is git-ignored from 28 Oct 2026** while its 1,295 existing
   files stay tracked, so new phase outputs will not appear in `git status`. That is
   deliberate — the directory was growing without bound — but it is a trap if you expect a
   generated file to be picked up.
7. **Running the test suite without `results_v2/` overwrites a tracked results file.**
   `tests/test_v2_1_phase_9.py::test_grid_manifest_matches_runs` calls `stage_verify()`, which
   rewrites `docs/env_v2/generated/v2_1/e9_4/verify.json` in place. On a machine where the run
   data is absent — which is every machine but the cluster — it replaces the real counts with
   zeros and still *passes*, because nothing on disk can mismatch. Check `git status` after a
   full run and restore the file if it moved.
8. **Secrets hygiene.** `env` / `.env` hold live keys in plaintext. Never committed;
   `tools/hf_backup.py` refuses to upload anything whose scan finds a key shape or a cluster
   identifier.

---

## 7. Working rules that are not discoverable from the code

- **The execution-order rule.** Anything that changes the environment or the prompts restarts
  from step 0: re-freeze the hash manifest, regenerate the 95-configuration fixture, re-run
  the checklist and the leakage audits on the handed-over state.
- **Provenance labels are mandatory.** LIT (a published statistic, read at source), FIT
  (estimated on a stated dataset by a stated method, with an interval), CAL (tuned to meet a
  criterion, and labelled as such), DESIGN (a choice evidence cannot decide, named with its
  alternatives), DERIVED (computed from a null, a bound or a known answer). A statistic marked
  "to verify" may not appear in a parameter file, a test tolerance or a slide.
- **Pre-register before you look.** Every phase wrote its pre-registration before any run and
  never edited it; corrections go in an addendum that records what had already been seen.
- **Numbers carry their n**, and failures are reported as failures. Several phases withdrew
  their own conclusions; the withdrawals are in the reports and the decision log.
- `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`, `V2_1_ALTERNATIVES_REGISTER.md` and anything
  under `v2_1/archive/` are not edited without being asked.
