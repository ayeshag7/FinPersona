# FinPersona: Financial Personality Simulation Engine
FinPersona is a framework for simulating diverse investor behaviors using LLMs. It utilizes a **"Prompt-as-Policy"** architecture to condition AI agents with specific MBTI profiles (e.g., ENTJ, INFP) and evaluates their trading performance in a historical market environment.

## Architecture

1.  **Data Layer (`market_data/`)**: Ingests historical stock data (AAPL, 2019-2021) via `yfinance` and computes technical indicators (SMA, RSI, MACD) using `vectorbt`.
2.  **Decision Layer (`agent/`)**: The cognitive core. Combines MBTI baselines with financial context and uses **Pydantic** to enforce structured JSON output (Action, Quantity, Rationale) from Google Gemini.
3.  **Execution Layer (`simulation/`)**: Manages the event loop, tracks portfolio state (Mark-to-Market), executes trades, and logs results.

## Setup

**Prerequisites:** Python 3.9+ and a Google Gemini API Key.

**Instructions**

1. Clone the repository
```
git clone https://github.com/yourusername/FinPersona.git
cd FinPersona
```

2. Install dependencies
```
pip install -e .[dev]
```

3. Configure API Key
Create a .env file in the root directory:
```
echo "GOOGLE_API_KEY=your_actual_key_here" > .env
```
