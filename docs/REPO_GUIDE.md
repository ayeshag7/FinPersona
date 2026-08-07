# FinPersona-Bench — Repository Guide

A map of the codebase: what each part does, how the pieces connect, how they map to the
paper, and where the rough edges are. For how to *run* things, see the top-level
[`README.md`](../README.md). This document is about *understanding* the repo.

---

## 1. The mental model

The repo is four layers plus a few supporting pieces. Data flows top to bottom:

```
  Core library        envs/ + agent/ + simulation/      the benchmark engine
        |
  Experiment runners  run_*.py (repo root)              define the run matrix, call the engine
        |
  Results data        results_*/                        per-step CSV logs, one row per trading day
        |
  Analysis            analysis_*/ + mini-experiments    read CSVs -> metrics, figures, tables
```

Supporting pieces: the persona classifier (`finpersona_classifier_model/`), the human
annotation app (`annotation_app/`), documentation (`docs/`), the paper and its
references, and legacy code kept for provenance.

### End-to-end data flow

1. `envs/synthetic_market.py` generates a scenario: per-step observables `O_t` (price,
   SMAs, RSI, P/E, sentiment, ...) and a hidden `Fundamental_Value` `V_t`.
2. An agent policy in `agent/` maps `(persona, O_t)` to an action `{action, quantity,
   rationale}` by calling an LLM (via LangChain), with the output constrained by a
   Pydantic schema.
3. `simulation/runner.py` drives the day loop and `portfolio_tracker.py` handles cash,
   shares, and mark-to-market accounting.
4. Each day is written as one CSV row to `results_*/<model>/<scenario>/...`.
5. Analysis scripts read those CSVs and compute the paper's metrics (MAS, CI, RG) plus
   figures.

The whole design rests on `V_t` being generated independently of price, so behavioral
drift is measured against a known ground truth rather than subjective consensus.

---

## 2. Layer 1 — Core library

| Path | Role | Tracked |
|---|---|---|
| `envs/synthetic_market.py` | Synthetic market engine. Generates `flat`, `bull_trap`, `crash` scenarios and decouples observable price from hidden `Fundamental_Value`. | yes |
| `agent/base.py` | `BaseAgent` interface shared by all policies. | yes |
| `agent/static_agent.py` | `StaticAgent`: persona injected once at init, never refreshed. | yes |
| `agent/memory_agent.py` | `ActiveMemoryAgent`: re-injects the core mandate at every decision step. | yes |
| `agent/freq_agent.py` | `InjectionFreqAgent`: parameterized re-injection cadence `k`, with a `Mandate_Injected` audit column. | yes |
| `agent/ocean_static_agent.py`, `agent/ocean_memory_agent.py` | OCEAN (Big Five) persona variants of the two main agents. | yes |
| `agent/prompts.py`, `agent/ocean_prompts.py` | Prompt construction (persona core + finance extension + mandate). | yes |
| `agent/schemas.py` | Pydantic output schema `{action, quantity, rationale}`. | yes |
| `agent/personas/mbti_profiles.json` | Persona definitions: 16 MBTI types + `EXPERT`/`NONE` + OCEAN archetypes. | yes |
| `agent/legacy_agent.py` | Legacy agent, superseded. Kept for provenance. | yes |
| `simulation/runner.py` | Main orchestrator: connects env + agent, runs the day loop, logs CSVs. | yes |
| `simulation/ocean_runner.py` | OCEAN-specific runner. | yes |
| `simulation/portfolio_tracker.py` | Cash/shares/value accounting and transaction log. | yes |
| `simulation/legacy_runner.py` | Legacy runner, superseded. | yes |
| `legacy_market_data/` | **Legacy** historical-data market environment (`config.py`, `data_loader.py`, `indicator_calculator.py`, `market_environment.py`). Superseded by `envs/synthetic_market.py`. | yes |

---

## 3. Layer 2 — Experiment runners (entry points)

All in `experiments/`. Each defines a run matrix and calls the core library. Run them
from the repo root so the CWD-relative output paths resolve; a bootstrap line at the top
of each script also puts the repo root on `sys.path`, so imports resolve from any CWD.

| Script | Experiment | Results land in |
|---|---|---|
| `experiments/run_backtest.py` | Single smoke run (one persona, short horizon). | ad hoc |
| `experiments/run_experiments.py` | Main benchmark matrix: models x personas x scenarios x agent types x seeds. Resumable via `checkpoint.txt`. | `results/` |
| `experiments/run_ocean_experiments.py` | OCEAN framework-independence replication. | `results_ocean/` |
| `experiments/run_injection_freq_claude.py` | Injection-frequency ablation (`k` sweep). | `results_may/injection_freq/` |
| `experiments/run_long_horizon.py` | Long-horizon run (T=800). | `results_long_horizon/` |
| `experiments/run_t_calibration.py` | T-threshold calibration sweep. | `analysis/t_calibration_outputs/`, `results/t_calibration/` |

---

## 4. Layer 3 — Results data

Per-step CSVs, one row per trading day. Directory pattern:
`results_*/<model>/<scenario>/[discount<d>/]seed<s>/<persona>_<agent>_<scenario>_seed<s>...csv`.

CSV columns: `Date, Model, Persona, Agent_Type, Scenario, Seed, Crash_Discount, Phase,
Price, Fundamental_Value, Portfolio_Value, Cash, Holdings_Qty, Action, Quantity_Percent,
Rationale, SMA20, SMA60, RSI14, MACD, Volume, Volume_Ratio, Implied_Volatility,
Reported_PE, Dividend_Yield, Trend_Strength, Trend_Regime, Sentiment, Sentiment_MA5,
Sentiment_Change`.

| Path | Contents | Tracked |
|---|---|---|
| `results_april/` | Original 14 API-model panel at T=200, plus `t_calibration/` and `initial_general_results/`. | **no (gitignored)** |
| `results_may/` | 9-model open-weight + API panel. Subdirs: `google/`, `meta-llama/`, `Qwen/`, `injection_freq/`, `long_horizon/`. | **no (gitignored)** |
| `results_ocean/` | OCEAN replication, 3 models x 3 scenarios. | **yes (242 files)** |
| `results_long_horizon/` | T=800 runs for `claude-sonnet-4-6`. | **yes (153 files)** |

Note the inconsistency: two results directories are committed and two are gitignored.
See Section 8.

---

## 5. Layer 4 — Analysis and self-contained experiments

| Path | Role | Tracked |
|---|---|---|
| `analysis_may/` | **Primary analysis suite.** `numerical_analysis.py` (MAS, drawdown/CI, rationality/RG, trade count, Wilcoxon), `effect_sizes.py`, `persona_classifier.py`, `make_hero_figure.py`, `drift_breakdown.py`, `injection_freq_analysis.py`. Figures/tables in `outputs/`. | scripts yes, `outputs/` no |
| `analysis_april/` | Earlier analysis (`numerical_analysis.py`, `summarize_t_calibration.py`) + `outputs/`, `outputs_frontier_final/`. Duplicated script names with `analysis_may/`. | **no (gitignored)** |
| `analysis_ocean/` | `analyze_ocean_results.py` for the OCEAN panel. | yes |
| `placebo_reinjection_control/` | Self-contained three-arm placebo control (static / placebo / memory): its own `placebo_agent.py`, `run_placebo_experiment.py`, `analyze_placebo_results.py`, and `placebo_results/`. | yes |
| `rationale_linguistic_analysis/` | Output-level analysis: DistilBERT persona-confidence trajectories + Lexical Conflict Rate (LCR) + case studies, on crash rationales. Results in `rationale_results/`. This is behavioral/linguistic analysis, not mechanistic interpretability. | yes |

---

## 6. Supporting pieces

| Path | Role | Tracked |
|---|---|---|
| `finpersona_classifier_model/model/` | DistilBERT (`distilbert-base-uncased`) fine-tuned for 3-class persona classification (ENTJ/ISFJ/INTJ) on Day 1-5 rationales. Val macro-F1 = 0.94. Used to score `P(intended persona)`. | **no (gitignored)** |
| `annotation_app/` | Streamlit app for human evaluation of rationale quality. Self-contained: own `README.md`, `requirements.txt`, guide, and sample CSVs. | yes |
| `docs/EXPERIMENTS_REPORT.md` | Extended evaluation report (9-model panel, linguistic-drift metric, injection-frequency Pareto). Contributor extension. | yes |
| `references/mech_interp/` | The eight mechanistic-interpretability papers (PDFs + 2 web reports) plus `references.bib`, for the revision's interpretability track. | yes |
| `paper_text.txt` | Extracted text of the submitted paper. | (untracked working file) |
| `COLM FinPersona Rebuttal May.docx` | First-cycle COLM rebuttal. | (untracked working file) |
| `pyproject.toml`, `.flake8` | Package config, linting. | yes |
| `env` | **API keys (secrets).** Gitignored and never committed. Keep it that way; consider renaming to `.env` for clarity. | no |

---

## 7. How the repo maps to the paper

| Paper concept | Where it lives |
|---|---|
| Personas (ENTJ/ISFJ/INTJ, OCEAN) | `agent/personas/mbti_profiles.json`, `agent/prompts.py` |
| Scenarios (flat / bull_trap / crash) | `envs/synthetic_market.py` |
| Static vs Active Memory architectures | `agent/static_agent.py`, `agent/memory_agent.py` |
| Placebo control (W1) | `placebo_reinjection_control/` |
| Injection-frequency ablation | `agent/freq_agent.py`, `run_injection_freq_claude.py` |
| MAS / CI / RG metrics | `analysis_may/numerical_analysis.py` |
| Persona classifier, LCR (behavioral validation) | `finpersona_classifier_model/`, `rationale_linguistic_analysis/` |
| OCEAN replication | `agent/ocean_*`, `run_ocean_experiments.py`, `results_ocean/`, `analysis_ocean/` |
| T-calibration, long-horizon (T=800) | `run_t_callibration.py`, `run_long_horizon.py`, `results_long_horizon/` |

---

## 8. Known rough edges (cleanup opportunities)

1. **Month-based naming.** `results_april`, `results_may`, `analysis_april`, `analysis_may`
   name work by *when* it was run, not *what* it is. This keeps accreting and is opaque to a
   newcomer. Semantic names (main benchmark, ocean, ablations) are clearer.
2. **Inconsistent git tracking of results/analysis.** `results_ocean` and
   `results_long_horizon` are committed (395 CSVs in git history), while `results_april`,
   `results_may`, and `analysis_april` are gitignored. Pick one policy.
3. **Duplicate script names.** `numerical_analysis.py` and `summarize_t_calibration.py`
   exist in both `analysis_april/` and `analysis_may/`. Unclear which is authoritative.
4. **Root clutter.** Six `run_*.py` scripts plus several self-contained mini-experiment
   directories sit at the top level alongside the core library.
5. **Legacy interleaved with active code.** `legacy_market_data/`, `agent/legacy_agent.py`,
   `simulation/legacy_runner.py` are mixed in with current modules.
6. **Secrets hygiene.** `env` holds live keys in plaintext. Not committed, but worth
   rotating as a precaution and renaming to `.env`.

---

## 9. Reorganization status and remaining target

**Applied so far:** the six entry-point scripts were moved from the repo root into
`experiments/` (and `run_t_callibration.py` was renamed to `run_t_calibration.py`). Each
now carries a one-line bootstrap that puts the repo root on `sys.path`, so they run from any
CWD. Docs were updated to the new paths.

**Not yet applied (needs coordination):** the rest of the target below. These moves are
held back because the repo has no editable install (nothing is on `sys.path` except via the
run-from-root convention), and `placebo_reinjection_control/`, `rationale_linguistic_analysis/`,
and the `analysis_*` scripts hardcode `results_april`/`analysis_may` and compute the repo
root as `Path(__file__).parent.parent`. Moving them safely means rewriting those anchors and
re-running the pipeline to verify, which needs API keys or a GPU. The clean enabler is to make
the package pip-installable (`pip install -e .`) so nested layouts resolve without the
run-from-root assumption; do that first, then apply the rest.

Target structure (the `experiments/` group is already in place):

```
finpersona/                 # installable package (core library)
  envs/synthetic_market.py
  agents/                   # was agent/  (drop the legacy_agent here)
    base.py static.py memory.py freq.py
    ocean_static.py ocean_memory.py
    prompts.py ocean_prompts.py schemas.py
    personas/mbti_profiles.json
  simulation/runner.py ocean_runner.py portfolio_tracker.py

experiments/                # was root run_*.py
  run_backtest.py run_main.py run_ocean.py
  run_injection_freq.py run_long_horizon.py run_t_calibration.py   # typo fixed

ablations/                  # self-contained mini-experiments
  placebo_reinjection/
  rationale_linguistic/     # relabel as "behavioral validation" in the paper

analysis/                   # unify analysis_*
  main/                     # was analysis_may (the primary suite)
  ocean/
  common/                   # shared numerical_analysis, t_calibration summaries

results/                    # unify results_* under one policy (see below)
  main_benchmark/           # merges april 14-model + may 9-model panels
  ocean/
  long_horizon/
  ablations/

models/finpersona_classifier/     # was finpersona_classifier_model/
tools/annotation_app/             # was annotation_app/
legacy/                           # quarantine legacy_market_data + legacy_*.py
docs/  paper/  references/
```

**What executing this requires (why it needs coordination, not a blind `mv`):**

- Update hardcoded paths in scripts. For example, `rationale_linguistic_analysis.py`
  defaults to `--results-dir results_april` and `--classifier-dir
  finpersona_classifier_model/model`; runners write to `results_april/` and `results_may/`
  by name.
- Update `pyproject.toml` `[tool.setuptools.packages.find]` if the package root changes.
- Decide a single results policy: either (a) gitignore all `results/` and publish the data
  as a release or external download, or (b) commit all of it. Mixing the two (current state)
  is the main inconsistency. Recommended: gitignore results, add a short data-availability
  note, and keep only small illustrative samples in git.
- Because `results_ocean/` and `results_long_horizon/` are currently committed, moving them
  is a history-affecting change that teammates will pull. Do it on a branch and announce it.

Suggested order: do it on a feature branch, move files with `git mv`, update the hardcoded
paths, run `pytest`, then open a PR so the team reviews the path changes before merge.
