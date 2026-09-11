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
*(rewritten in v2.1 Phase 7, E7.4 and E7.7; DECISION_LOG P7-2, P7-10, P7-11)*

`cash`, `holdings_value`, **`cash_share`** (rendered), per-asset weights under N > 1. Initial allocation is a
factor [D]: primary = each persona starts at its own band centre (ISFJ 0.80, INTJ 0.50, ENTJ 0.10 cash);
secondary = common 0.5; bridge cell = 1.0 (v1). Baselines use the cell's start.

**Dividends [D10 = pay].** `PortfolioV2(dividends=True)` credits cash with (shares held x DPS per share) on each
ex-date; the accumulated total is `Dividends_Paid` in the log. `dividends=False` is the default and reproduces the
v2 accounting bit for bit (`pay_dividend` is then a no-op returning 0.0).

* **The ex-date is the quarterly EPS/DPS announcement day** — the day on which the generator's
  `days_since_eps_announcement` is 0 — and the amount is that day's `dps_quarterly`. This is the only ex-date
  recoverable from the environment's own frame; the generator has no separate ex-date concept and `envs/` is
  frozen. A 200-day path carries three, ~63 trading days apart, so the realised cash flow is the `4 x DPS / P`
  that the rendered `dividend_yield` field states.
* **The dividend goes to the holder of record**: it is paid at the start of the ex-date, before that day's
  settlement and trade, on the holdings carried in.
* **The price path is NOT ex-dividend adjusted.** The generator's price is a price-return series and is frozen, so
  a paying holder is a *total-return* holder on a price-return path: paying the dividend adds the yield to the
  total return rather than redistributing it out of the price. Every number computed with `dividends=True` carries
  this sentence. Measured on 500 flat seeds: realised annual yield 3.42 %, payer share 0.908 — the FIT payer share
  is a per-seed draw, so about 9 % of paths receive nothing at all with the switch on.

**Band-free arms.** The band that belongs to a portfolio state comes from `evaluation/targets.band()`, which is the
single definition: the arms with no mandate stated (`NONE`, `TRADER`) are band-free, (0, 1), with centre 0.5 and
therefore a half-width of 0.5, so such an arm can never violate its band. The mandated personas' bands are
unchanged.

### 2.3 Action [D]
*(rewritten in v2.1 Phase 7, E7.7; weakness 60)*

`TargetAllocation{target_cash_share in [0,1] (N=1) | target_weights (N>1), rationale}`; the trade is the delta
between target and current cash share; derived labels for RG: BUY if equity share rises > 1 pt, SELL if falls
> 1 pt, HOLD otherwise (no trade; allocation drifts with price). Execution same-day close [D: next-open
sensitivity]; **cost 5 bp x |traded value| PER TRADE, i.e. 10 bp round trip** [D: {0,5,20} bp; shown vs hidden,
default hidden]; fractional shares; long-only; no leverage. The v1 `TradeDecision` interface is kept behind
`action_interface="v1"` for the bridge cell (A1 x A2 factorial).

**The cost tier's concept.** 5 bp per trade is a **DESIGN** choice, not a value taken from either read anchor, and
the two anchors are different cost concepts: Nasdaq (2024) 4.5 bp is the cap-weighted **quoted spread** of the
S&P 500 basket (a half-spread of ~2.25 bp per side); Frazzini, Israel & Moskowitz (2018) 6.18 bp is the median
**market impact** per trade (mean 9.97). The implemented tier sits between them and is labelled as such in
`evaluation/params/scoring.json` (`cost_tier`). The **dead band** (1 point, inside which no trade happens at all)
is DESIGN as well; it is why the mandate-conditional oracle's own realised MCR is 0.0028 rather than 0.

**Pre- and post-trade cash share (weakness 60).** The trade record and the run log now carry **both**:
`Cash_Share_Pre` is the share before anything executes on that day, `Cash_Share_Post` the share after everything
has. `Cash_Share` keeps its existing meaning and its existing values. Under `execution="next_open"` the record
returned by `retarget` no longer calls the pre-trade share `cash_share_after`: it returns the pre-trade value under
both names with `pending: True` beside it, and `settle_pending` returns the real before/after when the deferred
trade executes.

**The scoring the action is judged by** is `evaluation/params/scoring.json`, read through the loud loader
`evaluation/scoring_params.py`: the θ in force (co-primary θ_info 0.05 and θ_cost 0.0020), the regret decomposition
MCR = B + D, the floor and ceiling convention, the half-width and its sensitivity, and the per-window alternative.
`metrics_v2.score_run(scoring="v2")` and `floors_and_ceilings(convention="v2")` keep the v2 behaviour unchanged.

### 2.4 Arms (E3; config-driven registry)
*(rewritten in v2.1 Phase 8, E8.1 and E8.2; PREREG_PHASE_8.md 1-2; DECISION_LOG P8-*)*

The registry is `experiments/arms_v2.ARMS`; an arm is a configuration, not a class. **Stateless:** static /
declarative placebo / directive placebo / wrapper-only / mandate (memory); swapped mandate; the no-mandate
no-persona trader (`trader`, `trader_maximise`; starts at 0.5); Path B (`path_b_static`, `path_b_memory`: the
mandate in the system prompt at t = 0). **Stateful** (the mandate in the system prompt at t = 0 in every one;
`static` = no per-step block, `memory` = the block re-injected into the current turn): rolling 5
(`stateful_r5_*`), rolling 20 (`stateful_*`), **rolling 50 (`stateful_w50_*`, added in Phase 8)**, full
(`stateful_full_*`, a 60,000-token history budget), summary (`stateful_summary_*`: a running summary every 10 steps
plus 5 raw turns; its matched control is rolling 5). Forked restatement probe (off-transcript); mandate wording
parameters; decode replicates ≥ 3 per cell; Track A (band stated in the prompt) vs Track B (persona text only).

**The context-length factor.** `experiments/arms_v2.CONTEXT_LEVELS` = {5, 20, 50, full} is a pre-registered factor
of the decay thesis. The full level is not unbounded: the 60,000-token budget holds **80 retained turns under v2**
(chars/4) and **77 under v2_1** (o200k), measured from the pilot's per-turn growth
(`docs/env_v2/generated/v2_1/e8_2/context_cost.json`, which also prices every level per run and per 90-run Tier-A
block).

**Two switches with the published behaviour behind them.** `RunConfig.harness_version`: `"v2"` (default, every
published stateful run) or `"v2_1"` — E8.1's corrections: (a) the mandate offset measured to the nearest copy the
model can attend to; (b) retained history turns rendered without the injected block, so the static and memory
histories are byte-identical under the same replies; (c) a parse fallback stored as `no valid answer`, never as the
fabricated decision; (d) the provider's token count when available, a tokenizer (`o200k_base`) otherwise, `chars/4`
only as a labelled last resort. `RunConfig.placebo_version`: `"v2"` (default) or `"v2_1"`, the per-persona matched
directive placebo. The v2 placebo matches the real block's imperative-clause count for ISFJ only (ENTJ 8 vs 7, INTJ
6 vs 7); the v2_1 placebo matches all three with words within 10 %
(`docs/env_v2/generated/v2_1/e8_1/placebo_matching.json`; `agent/prompt_matching.py`). Harness constants and their
provenance: `agent/params/harness.json`, read by `agent/harness_params.py`.

### 2.5 Log schema additions
`x_t = log(P/V)` (referee), `phase`, `macro_phase`, `resolvable_theta{0.03,0.05,0.08}`, `target_cash_share`,
`derived_action`, `traded_value`, `cost_paid`, `cash_share`, `start_design`, `action_interface`, `arm`,
`track`, `decode_replicate`, `parse_status`, `context_tokens`, `mandate_token_offset` (stateful arm),
plus the provenance columns above.

**Added in v2.1 Phase 7:** `Cash_Share_Pre`, `Cash_Share_Post` (section 2.3, weakness 60) and `Dividends_Paid`
(the running total credited to cash, section 2.2). `Cash_Share` is unchanged in meaning and in value.

**Added in v2.1 Phase 8 — stateful arms under `harness_version="v2_1"` only; a v2 log is unchanged in its columns
and values** (`tests/test_v2_1_phase_8.py::test_phase8_switches_inert`):

| column | meaning |
|---|---|
| `Harness_Version` | `v2_1` (absent from a v2 log) |
| `Mandate_Offset_Tokens` | **under v2_1: the offset of the nearest mandate copy** (primary covariate of the decay thesis); under v2: chars/4 from the system copy |
| `Mandate_Offset_System` | the offset of the system-prompt copy (secondary covariate) |
| `Mandate_Offset_Injected` | the offset of the block injected into the current turn; empty when the arm injects none |
| `Mandate_Copies_In_Context` | mandate copies in the context sent (v2_1: 1 static, 2 memory; v2 at a full window: window + 2) |
| `Context_Tokens` | the provider's input-token count when the call returns it, else the tokenizer count |
| `Context_Tokens_Tokenizer` | the `o200k_base` count of the same context, so every row can be put in one unit |
| `Token_Count_Method` | `provider`, `tokenizer:o200k_base` or `chars4` |
| `Offset_Count_Method` | `tokenizer:o200k_base*provider_scale`, `tokenizer:o200k_base` or `chars4` |
| `Token_Scale` | provider count / tokenizer count of the context (empty when no provider count) |
| `History_Fallback_Turns` | parse fallbacks stored in the history as `no valid answer` |

`meta.json`'s `run_config` gains `harness_version` and `placebo_version`. **How to read a v2 (pilot) log:** its
`Context_Tokens` is the provider's count and its `Mandate_Offset_Tokens` is chars/4 from the system copy through 20
replayed copies — two units in one log; on the pilot's day 200 the offset reads 15,261–16,546 where the nearest copy
is 409 (chars/4) away (`docs/env_v2/generated/v2_1/e8_1/pilot_offsets.json`). The per-call billed usage of the
variance pilot is written beside each run as `<run_id>.usage.json` by `tools/phase8/e8_5_variance_pilot.py`; it is
not part of the runner's schema.
