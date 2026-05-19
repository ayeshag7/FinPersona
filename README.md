# <img width="80" alt="FinPersona Logo" src="https://github.com/user-attachments/assets/5e09882c-f303-4fff-a112-438520448771" /> FinPersona: Financial Personality Simulation Engine

FinPersona is a research framework for benchmarking LLM-based trading agents conditioned on MBTI personality profiles. It uses a **"Prompt-as-Policy"** architecture to evaluate whether AI agents exhibit personality-consistent trading behavior across multiple market scenarios, models, and agent types.

## Research Questions

1. **Drift Test (Pillar I):** Do agents stay true to their personality mandate, or drift toward neutrality? Measured via Mean Absolute Deviation (MAS) from target cash allocation.
2. **Stereotype Test (Pillar II):** Do agents exhibit stereotype-consistent behavior (activity levels, risk tolerance)? Measured via trade count and max drawdown.
3. **Rationality Test (Pillar III):** Do agents trade rationally relative to hidden fundamental value? Measured via Rationality Score.

## Architecture

### 1. Market Environment (`envs/`)
Generates synthetic financial data with three scenario types:
- **`flat`** — Regime-based GARCH-like volatility clustering; low signal-to-noise baseline.
- **`bull_trap`** — Multi-phase bubble: legitimate rise → mania → blow-off top.
- **`crash`** — Panic selling: fundamental deterioration → oversold panic → stabilization.

Each scenario exposes per-step observables (price, SMA20/SMA60, RSI14, P/E, implied volatility, volume ratio, news sentiment) and a hidden `Fundamental_Value` used for rationality scoring.

### 2. Agent Layer (`agent/`)
Two agent types built on a shared `BaseAgent` interface:

- **`StaticAgent`** — Baseline agent. MBTI persona is injected once at initialization and remains unchanged across all decisions.
- **`ActiveMemoryAgent`** — Extends `StaticAgent` with **Periodic Mandate Retrieval**: the core personality mandate is re-injected at every decision step to counteract attention decay in long contexts.

Structured output (action, quantity, rationale) is enforced via **Pydantic** schemas. Supported LLM backends via LangChain:

| Provider  | Models |
|-----------|--------|
| Google    | `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash` |
| Anthropic | `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5` |
| OpenAI    | `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, `gpt-4.1-mini` |
| DeepSeek  | `deepseek-chat` |

MBTI profiles are defined in `agent/personas/mbti_profiles.json` and cover all 16 personality types plus `EXPERT` and `NONE` (control) baselines.

### 3. Simulation & Execution (`simulation/`)
- **`runner.py`** — Main orchestrator. Connects environment to agent, manages the 100-day trading loop, and logs portfolio state + market observables daily to CSV.
- **`portfolio_tracker.py`** — Accounting module tracking cash, share holdings, mark-to-market value, and a full transaction log.

### 4. Benchmarking (`run_experiments.py`)
Full experimental matrix with concurrent execution (up to 10 parallel workers):
- **Personas:** 3 primary (ENTJ, ISFJ, INTJ); expandable to all 16 MBTI types
- **Scenarios:** `flat`, `bull_trap`, `crash` (+ crash sensitivity variants at discount 0.85/0.92/0.95)
- **Agent types:** `static`, `memory`
- **Seeds:** 5 (42, 123, 456, 789, 999)
- **Checkpointing:** Completed runs are tracked so experiments are resumable.

### 5. Analysis (`analysis/`, `figure_and_targeted_runs/`)
- **`numerical_analysis.py`** — Computes financial metrics (Return %, Max Drawdown), rationality score, stereotype metrics (trade count), drift (MAS Deviation from `cideal`), and bubble participation (Avg Buy P/E).
- Visualization scripts for per-persona figures, per-model bar charts, and temporal decay plots.

### 6. Annotation App (`annotation_app/`)
Interactive **Streamlit** app for human evaluation of agent rationale quality. Supports pairwise comparison of agent decisions for inter-rater reliability analysis.

## Setup

**Prerequisites:** Python 3.9+ and API keys for the model providers you intend to use.

1. Clone the repository:
```bash
git clone https://github.com/ayeshag7/FinPersona.git
cd FinPersona
```

2. Install dependencies:
```bash
pip install -e .[dev]
```

3. Create a `.env` file in the root directory with your API keys:
```bash
GOOGLE_API_KEY=your_google_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
```
Only include keys for the providers you plan to use.

## Usage

**Single backtest run** (ENTJ persona, 50 days):
```bash
python run_backtest.py
```

**Full benchmark suite** (all models × personas × scenarios × seeds):
```bash
python run_experiments.py
```

**Model-specific targeted runs** (e.g., Claude):
```bash
python figure_and_targeted_runs/run_claude_targeted.py
```

**Temperature calibration study:**
```bash
python run_t_calibration.py
```

**Human annotation app:**
```bash
streamlit run annotation_app/annotation_app.py
```

## Results Structure

```
results/
└── {model}/
    └── {scenario}/
        └── seed{seed}/
            └── {mbti_type}_{agent_type}_{scenario}_seed{seed}.csv
```

Aggregated metrics are written to `results/master_summary_YYYYMMDD_HHMMSS.csv`.

## Key Metrics

| Metric | Description |
|--------|-------------|
| `Return_Pct` | Final portfolio return relative to initial capital |
| `Max_Drawdown_Pct` | Largest peak-to-trough decline |
| `Trade_Count` | Total number of non-HOLD decisions |
| `Rationality_Score` | % of decisions aligned with hidden fundamental value |
| `MAS_Deviation` | Mean Absolute Deviation from target cash allocation (`cideal`) |
| `Avg_Buy_PE` | Average P/E ratio at buy decisions (bubble participation proxy) |
| `Cideal` | Personality-specific target cash allocation (ISFJ: 1.0, INTJ: 0.5, ENTJ: 0.2) |
