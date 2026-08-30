# FinPersona-Bench I/O contract (E0 deliverable)

Status: **v1 section is a description of the frozen code at tag `v1-env-freeze`** (generated/verified by
`tools/gen_table2.py` and `tests/test_render_prompt_frozen.py`). **The v2 section is the contract as built in E1/E2** (plan Sections 2.1 blocks 8-10, 3, 7, 8); items marked [D] were Section 13.1 decisions, all signed as recommended on 22 Aug 2026 (`DECISION_LOG.md`).

---

## 1. v1 contract (as run for every v1 result)

### 1.1 Environment -> agent (observation)
`SyntheticMarketEnv.get_observation()` returns 16 keys (`date`, `price`, `SMA20`, `SMA60`, `RSI14`, `MACD`, `volume`,
`volume_ratio`, `news_sentiment`, `sentiment_MA5`, `sentiment_change`, `implied_volatility`, `reported_PE`,
`dividend_yield`, `trend_strength`, `trend_regime`). Rounding per key is in
`docs/env_v2/generated/table2_v1_from_code.md`. **Only 10 reach the prompt**: `date`, `price`, `SMA20`, `SMA60`
(rendered as "SMA20/60"; the series is the 50-day average), `trend_regime`, `RSI14`, `reported_PE`,
`implied_volatility`, `volume_ratio`, `news_sentiment`. `volume`, `sentiment_MA5`, `sentiment_change`,
`dividend_yield`, `trend_strength`, `MACD` are computed and logged but never shown. The horizon T is never disclosed.

### 1.2 Portfolio state -> agent
`PortfolioTracker.get_state()` -> `{"cash": float, "holdings_value": float}`; both rendered ("Cash: $x.xx",
"Holdings Value: $x.xx"). Initial state for every run, persona and arm: cash = 10,000.0, holdings = 0 (100% cash).

### 1.3 Prompt assembly (LangChain `ChatPromptTemplate`)
- system: `get_financial_persona(mbti)` = verbatim MBTI baseline text (`agent/prompts.py`) + `financial_extension`
  from `agent/personas/mbti_profiles.json`. The static arm never contains the core mandate.
- human (static): `agent/render.py::HUMAN_TEMPLATE_STATIC` with `render_static_input(...)`.
- human (memory): `HUMAN_TEMPLATE_MEMORY` with `render_memory_input(...)` followed by the
  `*** ACTIVE MEMORY REFRESH ***` block containing the persona's `core_mandate`.
- `{format_instructions}` = `PydanticOutputParser(TradeDecision).get_format_instructions()`.
- Verbatim samples: `docs/env_v2/generated/rendered_prompt_v1_{static,memory}.txt`.
- Temperature 0.2 for every provider (paper says 0.0; code is authoritative). Three parse attempts; after three
  failures a synthetic `HOLD` with rationale `"Error after 3 attempts: ..."` is returned **and logged as a decision**
  (evaluation must exclude these rows; the re-scoring does).

### 1.4 Agent -> environment (action)
`TradeDecision{action in {BUY,SELL,HOLD}, quantity in [0,1], rationale: str}` with the v1 asymmetric semantics:
BUY spends `cash * quantity`; SELL sells `holdings_qty * quantity`; HOLD does nothing. Execution at the same-day
close `price` on which the observation was rendered; fractional shares; zero cost; no short selling, no leverage.
Consequences (plan diagnosis 12-13): SELL is a no-op on day 1; repeated fractional BUYs approach full investment
geometrically; any cash share is reachable only from above.

### 1.5 Step order in `simulation/runner.py`
observe(t) -> decide -> execute at P_t -> log row(t) (with post-trade portfolio) -> `env.step()`.
`Fundamental_Value` logged per row is the referee's hidden truth for that step.

### 1.6 Per-row log schema (CSV, one row per day)
`Date, Model, MBTI, Agent_Type, Scenario, Seed, Crash_Discount, Phase, Price, Fundamental_Value, Portfolio_Value,
Cash, Holdings_Qty, Action, Quantity_Percent, Rationale, SMA20, SMA60, RSI14, MACD, Volume, Volume_Ratio,
Implied_Volatility, Reported_PE, Dividend_Yield, Trend_Strength, Trend_Regime, Sentiment, Sentiment_MA5,
Sentiment_Change` **plus, from E0 onward**: `Env_Version, Gen_Config_Hash, Env_Code_Hash, Prompt_Hash,
System_Prompt_Hash, Temperature, Git_Commit` (`simulation/provenance.py`).

---

## 2. v2 target contract

### 2.1 Observation (rendered == Table 2, generated from code: `generated/table2_v2_from_code.md`)
`SyntheticMarketEnv.get_observation()` returns exactly the 19 canonical fields, all rendered by `agent/render.py::
render_v2_input` (the contract: no exposed-but-unshown fields): `date`, `price`, `SMA20`, `SMA50`, `trend_strength`,
`trend_regime`, `RSI14` (Wilder), `MACD`, `MACD_signal`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`,
`sentiment_change`, `implied_volatility`, `reported_PE` (trailing-4Q, hidden multiple k), `dividend_yield`,
`analyst_fair_value`, `days_since_eps_announcement`; plus `days_remaining` and "Day-N of T" in the disclosed-horizon
arm, and an `assets` list (same fields per asset) when N > 1. Field order is canonical by default and permuted per
seed in the randomised-order arm. Phase labels, x, V, GARCH state, the hidden multiple and the analyst error are
NEVER exposed (`tests/test_v2_generator.py::test_observation_hygiene`). Rounding per field is in
`TABLE2_OBS_ROUNDING`.

### 2.2 Portfolio state
`cash`, `holdings_value`, **`cash_share`** (rendered), per-asset weights under N > 1. Initial allocation is a
factor [D]: primary = each persona starts at its own band centre (ISFJ 0.80, INTJ 0.50, ENTJ 0.10 cash);
secondary = common 0.5; bridge cell = 1.0 (v1). Baselines use the cell's start.

### 2.3 Action [D]
`TargetAllocation{target_cash_share in [0,1] (N=1) | target_weights (N>1), rationale}`; the trade is the delta
between target and current cash share; derived labels for RG: BUY if equity share rises > 1 pt, SELL if falls
> 1 pt, HOLD otherwise (no trade; allocation drifts with price). Execution same-day close [D: next-open
sensitivity]; cost 5 bp x |traded value| per trade [D: {0,5,20} bp; shown vs hidden, default hidden]; fractional
shares; long-only; no leverage. The v1 `TradeDecision` interface is kept behind `action_interface="v1"` for the
bridge cell (A1 x A2 factorial).

### 2.4 Arms (E3; config-driven registry)
static / declarative placebo / directive placebo / wrapper-only / mandate (memory); swapped mandate; no-mandate
no-persona trader (starts at 0.5); forked restatement probe (off-transcript); mandate wording parameters;
decode replicates >= 3 per cell; Track A (band stated in prompt) vs Track B (persona text only).

### 2.5 Log schema additions
`x_t = log(P/V)` (referee), `phase`, `macro_phase`, `resolvable_theta{0.03,0.05,0.08}`, `target_cash_share`,
`derived_action`, `traded_value`, `cost_paid`, `cash_share`, `start_design`, `action_interface`, `arm`,
`track`, `decode_replicate`, `parse_status`, `context_tokens`, `mandate_token_offset` (stateful arm),
plus the provenance columns above.
