# <img width="80" alt="FinPersona Logo" src="https://github.com/user-attachments/assets/5e09882c-f303-4fff-a112-438520448771" /> FinPersona-Bench: A Benchmark for Longitudinal Psychometric Stability of Autonomous Financial Agents

FinPersona-Bench measures what happens to an LLM's **behavioural mandate** when it has to act. A language model
plays a portfolio manager for 200 simulated trading days in a synthetic market that decouples observable price from
a hidden fundamental value, so the correct answer is known exactly and the same market path can be replayed for
every persona, prompt arm and model. The model is given a persona whose mandate says how much cash it should hold,
and the benchmark scores **mandate conformity**: how far its allocation sits from where the mandate says it should
be, given what the hidden market state actually was.

---

## Status

| | |
|---|---|
| **Environment** | v2.1, complete and **frozen**. `Env_Code_Hash` `1d689aaf82a33a2e` over 30 files; every parameter fitted, derived or a named design choice, each with its label, interval and n |
| **Main experiment** | Stage 1 of the open-weight headline has run: **nine models × 2,928 runs = 26,352 runs**, all verified against their manifest with 0 missing and 0 mismatched. **Not yet scored** |
| **Next** | Score stage 1 under its pre-registration, then the causal package, the common-start slice, Track A and the generator sensitivity sweep |
| **Paper** | The submitted COLM draft describes the v1 pipeline. Three review cycles found its instrument did not measure what it claimed; the environment was rebuilt in response, and the benchmark's claim is now restricted to a one-shot mandate-conflict benchmark |

Full status, with the evidence behind each line: **[`docs/env_v2/README.md`](docs/env_v2/README.md)**.

## The environment

The synthetic market, harness and evaluation layer were rebuilt in two stages. **v2** (Aug 2026) replaced v1's
"price = value + noise" with `log P = log V + x`, a mispricing engine, GARCH volatility, scripted events with random
timing, 19 label-free observable fields and a target-cash-share action. Three independent reviews then found 74
weaknesses in it — a fixed start price that acted as an answer key, an inert switching mechanism, a flat control
biased cheap, and roughly 200 numbers with no provenance.

**v2.1** is the ten-phase programme that answered them, under one rule: *every generator parameter is fitted or
tested on data, never stipulated.* Every fit is on a panel of **417 US stocks over 2000–2024**; every phase wrote a
pre-registration before any run, recorded each disconfirmation in an addendum, and locked its decisions in with
regression tests. The result is an environment where the shown fields add **+0.026** of R² for the hidden mispricing
where they once added +0.39, every checklist threshold comes from **12,927 real 200-day windows**, and the two
leakage gates it still does not meet are recorded as permanent residuals rather than quietly re-specified.

The v1 generator used for every published result is frozen at tag `v1-env-freeze` (`envs/v1/`).

### Why a parameter has the value it has

Every change from v1 through v2 to the ten phases of v2.1, with the evidence behind each one and what remains a
design choice, is written up in **[`docs/env_v2/history/SYNTHETIC_ENVIRONMENT_HISTORY.pdf`](docs/env_v2/history/)**
(63 pages, 33 figures; the `.docx` and the source `.md` sit beside it). Its figures are drawn from the programme's
own result files by `tools/history_figures.py`; `tools/history_docx.py` builds the document.

## Branches

| Branch | What it holds | Who needs it |
|---|---|---|
| `main` | everything: the v1 and v2 environments, the harness, every phase report, pre-registration and decision, the analysis tools, the results and the history document | anyone working on the benchmark |
| `synthetic-env-grid` | only the finalised v2.1 environment and what is needed to run and score the main LLM grid: the generator and its fitted parameters, the agent harness, the scoring layer, the grid tooling, the tests and a README | anyone running the grid, or reading the environment without the history around it |

**Why the second branch exists.** The machine that runs the grid needs none of the programme's history: no phase
reports, no analysis tools, no v1 generator, no old results, no third-party data panel. Cutting those away leaves a
small surface that is quick to review before a long run starts, and it removes any doubt about which code produced
it. The branch is not a fork: it is a branch of this repository, cut from `main` by deleting files, and the
environment code is byte-identical. Two checks prove it, and the branch's own README explains how to run them: the
freeze manifest gives the same environment code hash on both branches (`1d689aaf82a33a2e` over the same 30 files),
and the 95 fixed path configurations reproduce the frozen reference with 0 changed. The two branches are level —
the pre-grid freeze and the pre-grid build were both ported — and nothing is developed on the branch that is not
also on `main`.

```
git checkout synthetic-env-grid     # the runner branch
git checkout main                   # back to the full project
```

---

## Architecture

### 1. Generator (`envs/`)

`envs/v2/` behind the `envs/synthetic_market.py` facade. `log P = log V + x`, with `V` a hidden random walk and `x`
the mispricing the agent never sees. Four scenarios: **flat**, **crash** (at a discount δ of 0.55 / 0.70 / 0.85),
**bull_trap** (a bubble with a hazard-driven top) and **sustained_bull** (a rise that does not top). A day is
*resolvable* when `|x| >= theta`; on such days there is a correct direction to lean.

The numbers live in `envs/v2/params/*.json` — value, mispricing, volatility, events, hazard, observables — and each
entry carries its provenance label (**LIT / FIT / CAL / DESIGN / DERIVED**), its interval, its n and its status. The
loaders fail loudly on a missing entry or an undeclared status. Every v2.1 change is a switch with the v2 behaviour
behind it, proved inert when off against a fixture of 95 path configurations.

Nineteen rendered fields: the day index, price, SMA20/50, trend strength and regime, RSI14, MACD and signal, volume
and volume ratio, news sentiment with its 5-day average and change, implied volatility, reported P/E, dividend
yield, analyst fair value, and days since the earnings announcement.

### 2. Harness (`agent/`, `simulation/`, `experiments/`)

One configurable stateless agent — *the arm is a configuration, not a class* — plus stateful variants that carry a
rolling window, a full transcript or a running summary. The action is a **target cash share** in [0, 1] with a
1-point dead band and a 5 bp cost, enforced by a Pydantic schema.

`experiments/arms_v2.py` holds the registry of **20 arms**. The ones that carry the argument:

| Arm | What it injects each step |
|---|---|
| `static` | nothing (persona only) |
| `memory` | the mandate, at the recency position |
| `placebo_declarative` | semantically irrelevant text, length-matched |
| `placebo_directive` | imperative-, delimiter- and length-matched to the mandate |
| `wrapper_only` | the "ACTIVE MEMORY REFRESH" framing with no mandate content |
| `swapped` | another persona's mandate |
| `trader` | no persona, no mandate, band-free |

Personas: **ISFJ** conservative (cash band 0.70–0.90), **INTJ** balanced (0.40–0.60), **ENTJ** aggressive
(0.00–0.20), **NONE**, plus the OCEAN vocabulary pair. `agent/llm_factory.py` routes any model name prefixed
`vllm/` to a local OpenAI-compatible server, so open weights need no adapter.

Every row carries its provenance: `Env_Code_Hash`, the prompt and system-prompt hashes, the temperature, the
provider configuration and the parse status.

### 3. Scoring (`evaluation/`)

Derived, not stated. The resolvability threshold **θ** is co-primary at 0.002 (the cost at which one reallocation
pays for itself) and 0.05 (where a level-free surrogate's sign accuracy reaches 0.80). Mandate-conditional regret
decomposes as **MCR = B + D** — band violation plus direction — against a ceiling from the mandate oracle run
through the real simulator and a floor from the worst of six trivial policies. Twelve rule policies run on each
cell's own path. The 20-item stylized-facts checklist and the L1 / L2 / L2b / L4 leakage audits are judged against
the real reference distribution and derived null margins.

### 4. Tools and tests (`tools/`, `tests/`)

One tool package per improvement phase (`tools/phase1/` … `tools/phase9/`), so every number in a phase report is
re-runnable. `tools/phase9/` is the grid: roster, sizing, manifests, launcher, verification and scoring.
`tools/cluster/` holds the SLURM and vLLM tooling. 268 tests, with a **known-defect registry** whose strict xfails
fail loudly if a recorded defect ever disappears.

---

## Experiments

### The main grid — open-weight headline, stage 1

Stage 1 ran on open weights served by our own vLLM 0.29.0 on HiPerGator B200s, each configuration pinned by Hugging
Face revision:

| Batch | Models |
|---|---|
| 1 (24 Oct 2026) | Gemma 4 31B, Gemma 4 E4B, gpt-oss-20b, Muse Glimmer 30B, OLMo 3.1 32B, Ministral 3 14B |
| 2 (26 Oct 2026) | Llama 3.1 8B, Llama 3.1 70B, Phi-4 — the models the comparable published studies run |

**Design:** 3 personas × (static, memory) × 4 scenarios × **122 seeds** (the same market paths for every model) ×
1 replicate, T = 200 — **2,928 runs per model, 26,352 in all**. The seed count is the paired-correct count at the
roster's plug-in σ_d, giving at least 0.80 power at a band-MAS difference of 0.05 for every model.

All nine verify against their manifest with **0 missing and 0 mismatched**; seven pass all 19 validation checks,
and two keep a handful of parse fallbacks as model behaviour. The runs are **not yet scored** — the confirmatory
analysis is registered in
[`PREREG_PHASE_9_STAGE1_OPEN.md`](docs/env_v2/v2_1/PREREG_PHASE_9_STAGE1_OPEN.md), one family of 36 per model under
Benjamini–Hochberg, with reliability preconditions reported per cell before any claim.

### What runs next

The causal package (declarative and directive placebos, wrapper-only), the common-start slice that identifies the
salience shares, Track A (stated versus unstated target), the generator sensitivity sweep over the data-driven six
parameters, the context-length factor, the OCEAN vocabulary gradient and the mechanistic appendix. Scale, cell
arithmetic and dependencies: [`GRID_EXPERIMENT_PLAN.md`](docs/env_v2/v2_1/GRID_EXPERIMENT_PLAN.md).

### The v1 panels (the submitted paper)

Frozen, kept for provenance, and read with the Cycle 2 findings beside them.

| Panel | Design |
|---|---|
| Main (`results_may/`) | 9 models (4B–frontier, open-weight via vLLM and API) × 3 personas × 3 scenarios × 2 agent types × 5 seeds, T = 200 |
| OCEAN (`results_ocean/`) | 3 API models × 4 Big-Five archetypes × 3 scenarios |
| Placebo re-injection (`placebo_reinjection_control/`) | static / placebo / memory, one model, flat, 3 personas × 5 seeds |
| Injection frequency (`results_may/injection_freq/`) | k ∈ {1, 5, 25, 100, ∞}, one model, 3 personas × 3 seeds |
| Long horizon (`results_long_horizon/`) | T = 800, flat, 3 seeds |
| Rationale linguistics (`rationale_linguistic_analysis/`) | classifier confidence trajectories and Lexical Conflict Rate on crash rationales |

---

## Setup

**Prerequisites:** Python 3.9+, and API keys or a local vLLM server for the models you intend to run.

```bash
git clone https://github.com/ayeshag7/FinPersona.git
cd FinPersona
pip install -e .[dev]
```

`pyproject.toml` predates the v2.1 work and does not declare everything the analysis layer imports; install
`scipy`, `scikit-learn`, `statsmodels`, `arch`, `matplotlib` and `python-docx` alongside it.

Create a `.env` in the repo root with only the providers you plan to use:

```bash
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
```

For open weights, stand up vLLM and point the harness at it — no adapter needed:

```bash
export VLLM_BASE_URL=http://localhost:8000/v1
export VLLM_API_KEY=EMPTY
```

## Usage

Run everything from the repo root.

**Verify you have the environment the documents describe** (do this first):

```bash
python -m tools.freeze_manifest --check     # expects Env_Code_Hash 1d689aaf82a33a2e over 30 files
python -m pytest tests/ -q                  # test_leakage_ci.py is slow
```

**A v2.1 grid cell:**

```bash
python -m experiments.arms_v2 \
    --models vllm/meta-llama/Llama-3.1-8B-Instruct \
    --personas ISFJ INTJ ENTJ --arms static memory \
    --scenarios flat bull_trap crash sustained_bull \
    --seeds 42 123 456 --reps 1
```

**A registered grid stage**, which refuses to start if any prompt hash or the environment hash has moved:

```bash
python -m tools.phase9.e9_4_grid --stages manifest_open
python -u -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_headline_open.json
python -m tools.phase9.e9_4_grid --stages verify,score,status
python -m tools.stats_v2
```

**The v1 pipeline** (frozen; for reproducing the submitted paper):

```bash
python experiments/run_experiments.py       # the main v1 matrix, resumable via checkpoint.txt
python experiments/run_ocean_experiments.py
streamlit run annotation_app/annotation_app.py
```

## Documentation

| Where | What |
|---|---|
| [`docs/REPO_GUIDE.md`](docs/REPO_GUIDE.md) | Map of the codebase: what each part does and how the pieces connect |
| [`docs/env_v2/README.md`](docs/env_v2/README.md) | The environment: index, reading order, current status, what runs next |
| [`docs/env_v2/history/`](docs/env_v2/history/) | The whole history in one document — why every parameter has its value |
| [`docs/env_v2/v2_1/`](docs/env_v2/v2_1/) | The improvement plan, and each phase's pre-registration and report |
| [`docs/env_v2/decisions/DECISION_LOG.md`](docs/env_v2/decisions/DECISION_LOG.md) | Every decision, its evidence and the alternative rejected |
| [`docs/reviews/`](docs/reviews/) | The two review cycles, including the conditions the paper must meet |
| [`MECH_INTERP_BRIEF.md`](MECH_INTERP_BRIEF.md) | Constraints on the mechanistic track that the code does not reveal |
