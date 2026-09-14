# The FinPersona Synthetic Market Environment: Improvements from v1 through v2 to v2.1

*This document records every change made to the synthetic market environment on which the FinPersona benchmark runs: the original version (v1), the rebuilt version (v2), and the ten-phase improvement programme called v2.1 (Phases 0 to 9). It states what each version was, what was found wrong with it, what was changed, what evidence each change rests on, and which of its positions are held by design rather than by a fit. Every number is taken from the programme's result files and carries its sample size where the source gives one.*

## 1. Scope and conventions

**Purpose.** A single account, written for a reader who knows the benchmark exists but has not read the phase reports, of how the environment was improved and why. The focus is on the work and its evidence; the internal organisation of the project is not described.

**The benchmark.** A language model plays a portfolio manager for 200 simulated trading days in a synthetic stock market. Each day it is shown a screen of market fields (price, moving averages, volume, sentiment, implied volatility, a P/E ratio, an analyst estimate and others) together with its own portfolio, and it answers with a target cash share. It is given a persona (ISFJ conservative, INTJ balanced, ENTJ aggressive) whose mandate says how much cash it should hold, and the benchmark scores mandate conformity: how far the agent's cash share sits from where the mandate says it should be, given what the hidden market state actually was. The market is synthetic so that the correct answer (the hidden fundamental value) is known exactly, and so that the same market path can be replayed for every persona, every prompt variant and every model.

**The market model used from v2 onwards.** The price is P, the hidden fundamental value is V, and the mispricing is x = log(P / V). The agent never sees V or x. Scenarios are flat, crash (at a discount delta of 0.55, 0.70 or 0.85), bull trap (a bubble that tops) and sustained bull (a rise that does not top). A day is resolvable when the absolute mispricing is at least a threshold theta; on such days there is a correct direction in which to lean.

**Conventions.**

- Provenance labels on parameters: LIT (a published statistic, read at source), FIT (estimated on a stated dataset by a stated method, with an interval), CAL (tuned to meet a criterion and labelled as such), DESIGN (a choice that evidence cannot decide, made by the team and named with its alternatives), DERIVED (computed from a null distribution, a bound or a known-answer reference; formalised as a label in Phase 6).
- Status words used for parameters: ADOPTED, INCUMBENT (the v2 behaviour stays), "TESTED, REJECTED", "TESTED, NOT ADOPTED", PROVISIONAL, "IN FORCE, ADOPTION WITHDRAWN".
- Intervals in square brackets are 95 percent intervals unless stated otherwise; n is the sample size on which a number rests.
- "The panel" is the analysis set of 417 United States stocks with full daily histories over 2000 to 2024 on which every fit was made; set B is a secondary set of 155 shorter histories.
- Ranges are written "a to b".

**Figures.** Every figure is followed by an italic caption giving the quantity plotted, the data it was drawn from and the sample size. All 33 figures were drawn from the programme's result files; no number in a figure was typed in.

---

## 2. Summary

| Version | What it was | What was found wrong | What replaced it |
|---|---|---|---|
| v1 | Price equal to the hidden value plus dollar noise; three scenarios with fixed phase lengths (80, 60 and 60 days); a P/E field equal to a constant times price over value; volume, sentiment and implied volatility driven directly by the phase label; every persona started fully in cash; asymmetric BUY and SELL actions; no baseline policies | The P/E field inverted to the hidden value exactly; the flat market had no mispricing to resolve (0 percent of steps at theta 0.05); phase and day could be read off the fields; the universal cash start manufactured the conservative persona's apparent adherence; no model passed the day-1 persona gate (0 of 18); 11.5 percent of runs never traded | v2 |
| v2 | log P = log V + x with a Franke-Westerhoff style mispricing, GJR-GARCH-t volatility, scripted crash and bubble events with random timing, a probabilistic bubble top, 19 label-free observable fields, a target-cash-share action with a 5 bp cost, persona cash bands, a configurable set of prompt arms, a mandate-conditional regret metric and a pre-registered 20-item stylized-facts checklist | Three independent reviews found 74 weaknesses: the fixed start price of 100 was an answer key for the mispricing; the Franke-Westerhoff switching was inert because of a units error; the flat market was biased cheap by negative-mean jumps; the fields leaked the hidden state once the anchor was removed; the calendar remained a phase clock in the runs actually made; several statements exceeded their evidence; an analyst-error bug; wrong sensitivity counts; about 200 numbers with no provenance | v2.1 |
| v2.1 | The same environment, rebuilt block by block under one rule: every generator parameter is fitted or tested on data, never stipulated | The checkpoint the plan set for the environment (16A) was not met in Phase 6: an informed policy does not beat a constant band edge, and the team resolved this by restricting the paper's claim to a one-shot mandate-conflict benchmark (Phase 7) rather than by re-tuning the environment; the main LLM grid was then sized on the finished environment (Phases 8 and 9) | The environment in force: complete and frozen under a hash manifest, every parameter carrying its evidence and its label; the LLM grid that runs on it is specified and sized |

The programme's principal changes:

- **The price anchor was removed.** In v2 a two-line rule (sell if the price is above 105, buy if it is below 95) matched the true-value oracle. Under the v2.1 start-price mechanism the same rule sits with the constant band-edge policies (Phase 1).
- **The mispricing engine is the one the data support.** The Franke-Westerhoff form was reproduced from its paper (which exposed the units error), then estimated properly on 417 stocks together with two alternatives; none fitted, and an AR(1) with a fitted half-life of 22.4 days [18.75, 32.64] was adopted under a pre-registered rule (Phases 2 and 3). The v2 half-life was 150 days, set by hand.
- **Every volatility, event and observable constant is now FIT, DESIGN or LIT with a stated source and interval** (Phases 3 to 5): per-stock GJR-GARCH-t fits, a jump process fitted on 2.6 million stock-days, event durations and depths drawn from 1,789 drawdowns and 3,202 run-ups, a P/E multiple drawn from the regulatory-filing cross-section, a sentiment process fitted on a daily news-sentiment index, and a volume process fitted on 417 stocks.
- **The fields stopped carrying the hidden state.** The R-squared for the mispricing that all shown fields together add beyond a level-free reading of the price path fell from +0.39 with the fields as inherited at the Phase 4 hand-over to +0.026 after Phase 5, a 93 percent reduction; the macro-phase clock's selectivity fell from +10.4 percentage points at that hand-over to +1.8 (Phase 5; v2's own was +6.9).
- **The yardsticks were rebuilt from real data and derived nulls** (Phase 6): 12,927 real 200-day windows of 417 stocks give every checklist statistic a reference distribution; the leakage gates were derived from permutation nulls and a Kalman bound; known-answer tests were added for every audit statistic.
- **The scoring was derived rather than stated** (Phase 7): the resolvability threshold, the decomposition of regret into band violation and direction, the floor and ceiling, dividends paid into cash, the day-1 gate re-specified, baselines computed on each run's own path.
- **The statistics were validated on simulated data before any real contrast was tested** (Phases 8 and 9): the v2 mixed model rejected a true null 36 to 58 percent of the time when the arm effect varied by model; the replacements were sized by simulation, and the grid sized at 93 seeds per cell from a paid variance pilot and then at 120 seeds from the roster pilots.

One figure summarises the trajectory. Figure 1 shows the leakage audit at every hand-over: how well the hidden value can be rebuilt from the screen (L1), how predictable the mispricing is on calm days (L2), and how often a flat market has a correct answer at all (L4).

![Figure 1](figures/F02_leakage_by_version.png)

*Figure 1. (a) The median absolute percentage error of the best formula that rebuilds V from the shown fields, with the formula named under each bar: in v1 the P/E field inverted V to 0.2 percent; from Phase 2 onwards the price itself is the best inverter and it is off by 3.5 to 6.4 percent. (b) The R-squared of the best of three surrogates (ridge, gradient-boosted trees, MLP) predicting x on calm days from all shown fields and from price fields only; the v1 price-only surrogate sits at minus 41 and is clipped. (c) The share of flat-market calm days with an absolute mispricing above theta = 0.05. Calm rows: 7,200 (v1), 11,700 (v2), about 119,400 (Phases 1 to 6); flat calm steps: 6,000 (v1), 4,000 (v2), 40,000 (Phases 1 to 6). The v1 and v2 audits carry no intervals; the v2.1 audits carry seed-cluster bootstrap intervals.*

---

## 3. Version 1: the original environment

### 3.1 Design

v1 is the generator on which the first FinPersona experiments were run. Its design, as documented by the baseline measurements made before v2 was built and by the v2 plan's list of defects:

- **Price and value.** A hidden fundamental value with a price equal to value plus dollar noise; three scenarios (flat, bull trap, crash with a discount delta of 0.85, 0.92 or 0.95 that sets how far price fell relative to value; v2 moved to 0.55, 0.70 and 0.85) with fixed phase lengths of 80, 60 and 60 days, so that the calendar day identified the phase exactly.
- **The screen.** A P/E field computed as a constant multiple of price over value, so that a reader could invert it to the hidden value to the last decimal; implied volatility, volume and sentiment driven by the phase label rather than by the price path, so that each was a clock for the phase; sentiment independent and identically distributed within a phase, with a correlation of 0.08 to returns.
- **The action and the start.** Every persona began with 100 percent cash and 10,000 dollars; the action was BUY, SELL or HOLD with an asymmetry that made SELL a no-op on day 1 and made any allocation reachable only from above; the persona classifier was a DistilBERT model (validation macro-F1 0.94).
- **What was missing.** No baseline policies against which an agent's score could be normalised; no provenance columns beyond the run itself; a decoding temperature of 0.2 where the paper stated 0.0.

The paper's v1 panel covered 14 models, three personas and five seeds (210 pairs per metric), later 18 models (270 pairs); the baseline re-scoring covered 2,658 runs of 200 days across those 18 models, plus OCEAN-persona and long-horizon variants.

### 3.2 The baseline measurements on v1

Before v2 was built, the v1 generator and the v1 runs were re-scored under the v2 definitions.

| What was measured | v1 result | n |
|---|---|---|
| Stylized-facts checklist (20 items) | 3 pass, 10 fail, 7 not applicable | 50 seeds per scenario (270 paths pooled) |
| Flat returns: excess kurtosis, autocorrelation of absolute returns, corr(volume, absolute return) | 0.06, 0.01, minus 0.02 (real markets show fat tails, clustering and a positive correlation) | 20 seeds x 200 days |
| Crash return autocorrelation at lag 1 | minus 0.45 for every delta (the bid-ask-bounce signature of additive dollar noise around a level) | diagnostic run |
| Effect of delta on the crash drawdown | means minus 48.2, minus 47.8, minus 47.7 percent; spread 0.5 percentage points; partial R-squared 0.03 | 150 crash paths |
| Bull daily sigma against flat | 1.3 against 2.1 percent; corr(volume, absolute return) minus 0.21 | diagnostic |
| L1 inversion: k x P / PE reproduces V | fitted k 15.0000; median absolute percentage error 0.0016; maximum 0.0041; sign(P minus V) = sign(PE minus 15) on 85 percent of steps in the 30-seed audit (100 percent in the plan's own diagnostic) | 30 seeds, 30,000 steps |
| Flat steps with price within 1 percent of value | 96.9 percent | audit |
| Resolvable share at theta 0.05: flat / bull trap / crash | 0.000 (mean absolute x 0.003) / 0.579 / 0.820 | 21,000 / 1,000 / 3,400 steps |
| L2 surrogate: calm R-squared of x; event R-squared; MAPE of V | 0.903; 1.000; 0.7 percent | 7,200 / 14,400 rows |
| L2b phase clock: full fields / price only / day only / majority | 99.8 / 94.9 / 60.0 / 40.0 percent accuracy; selectivity +5.0 points | the L2 panel |
| Within-scenario day-only phase accuracy | 100.0 percent (mixed set 63.6) | 270 paths |
| Implied volatility, calm / panic; IV minus realised | 12.5 / 33.8 percent; minus 18.5 / minus 22.9 points (below realised volatility) | 270 paths |
| Day-1 cash share ISFJ / INTJ / ENTJ | means 0.919 / 0.915 / 0.839, medians 1.000 for all three | 2,658 runs |
| Day-1 separability gate | 0 of 18 models pass | 36 model and arm rows |
| Cliff's delta ISFJ against INTJ / INTJ against ENTJ / ISFJ against ENTJ | minus 0.010 / 0.109 / 0.098 | 2,658 |
| Band hit on day 1 (all / ISFJ / INTJ / ENTJ) | 8.7 percent (13.7 / 5.1 / 7.2); point hit 80.3 / 5.1 / 1.2 | 2,658 |
| Probability of SELL on day 1 | 0.0000 for every persona | 888 / 882 / 888 |
| Zero-trade runs | 306 of 2,658 (11.5 percent); ISFJ memory arm 36 to 47 percent | 2,658 |
| Parse-fallback rows | 4 rows in 4 runs | 2,658 x 200 |
| Seed reproducibility | 102 runs in 25 cells differ from the path their seed should give (127 distinct paths) | 2,658 |
| Bull-trap trivial envelope: buy on day 1 and hold / always HOLD / random | 99.7 / 79.8 / 66.9 against the two arms' 85.9 and 78.4 | 5 cells |
| RG normalisation | degenerate (share 1.000 in every scenario) | 540 / 1,578 / 540 runs |
| ISFJ memory-arm improvement over the static arm (the paper's bidirectional headline) | 16 of 18 models under the v1 point metric; 11 of 18 under the v2 band metric; 10 of 18 under the v2 point metric | 18 models, 1,329 pairs |
| ENTJ memory-arm worsening | 14 of 18 (v1) to 12 of 18 (band); crash 17 of 18 to 13 of 18 | 18 |
| Numerical-only persona separation (the O3 control) | Cliff's delta 0.833, AUC 0.917 pooled | 60 runs |

Interpretation: the flat scenario had nothing to resolve (0 percent of steps at theta 0.05, because the price sat within 1 percent of value on 97 percent of days); the P/E field was an answer key; the bull-trap result was inside the trivial envelope (buying on day 1 and holding beat both arms); the conservative persona's apparent adherence and its memory benefit were manufactured by the universal 100 percent cash start and a target of 1.0 that coincided with it; and no model's day-1 allocation identified its persona (Figure 2).

![Figure 2](figures/F03_v1_separability_gate.png)

*Figure 2. The day-1 separability gate on the v1 runs: for each of 18 models and both prompt arms, the macro one-versus-rest AUC of the day-1 cash share against the persona (0.5 is chance). 2,658 runs, 75 per point (54 for gemma-3-4b-it). No model and arm cell passes the gate, which requires the ordering, band, AUC and surrogate criteria together.*

### 3.3 The defect list that shaped v2

The v2 plan opened with a list of fifteen v1 defects drawn from an audit of the synthetic market and from the baseline measurements above. Those with a measured number are in the table: the P/E leak, the label-driven clocks, the absent stylized facts, the trivial delta effect, the mismatch between the paper's field table and the rendered prompt, the 97 percent of flat steps inside 1 percent of value, the universal cash start and the BUY/SELL asymmetry, and the bull-trap trivial envelope. Each maps to a v2 design decision in section 4.

---

## 4. Version 2: the rebuild

### 4.1 The plan and the build

v2 was designed in a written plan (with three research notes, a fact-check and a coherence report) and built in two stages: the generator and its calibration first, then the harness, arms and evaluation layer, followed by a pilot, a 27-slide deck with a speaker script, and an integrity review by two reviewer agents. Eleven design decisions from the plan were taken "as recommended" on the team's instruction to record each decision and its reasoning. The generator keeps the same public interface as v1 over new modules for the generator, the mispricing engine, the GARCH block, the events, the schedule and the observables.

### 4.2 The design, block by block

**Value and price.** log P = log V + x. V is a hidden random walk with drift mu_V = 0.00025 per day, daily standard deviation sigma_V = 0.006 and t-distributed shocks with 5 degrees of freedom; both constants were plan anchors without a data source. Both price and value started at 100 on day 1. Jumps (rate 0.010 per day, size drawn from a normal with mean minus 4 percent and standard deviation 3 percent) entered x, not V.

**The mispricing engine.** x followed a Franke and Westerhoff (2012) fundamentalist-versus-chartist recursion driven by a GJR-GARCH-t innovation. The plan called for the model's parameters to be re-estimated by the simulated method of moments on about ten single stocks; that attempt was rejected (J = 408.154 on nine moments), so a fallback engine shipped with phi = 0.4632, chosen so that the pull-rate half-life of the mispricing was 150 days, published as a design choice outside the 60 to 120 day window the decision had named. The engine ran with a price scale of 100, a units interpretation the specification flagged as "to be verified" and that Phase 2 later found to be wrong. A one-dimensional J-profile over phi (2.89 to 3.16 for phi between 0.03 and 2.0, with the fundamentalist share above 0.995 at every phi) was published alongside. Alternative engines (the paper's index parameters, a published single-stock variant, a plain AR(1), a 60-day half-life) were kept behind a switch as sensitivities. The burn-in was 260 days.

**Volatility.** A GJR-GARCH(1,1) with t innovations: alpha 0.10, gamma 0.10, beta 0.83, unconditional scale sbar 0.017, 5 degrees of freedom, all moved off the plan's anchors (0.05 / 0.08 / 0.89, sbar 1.6 percent) in a calibration ladder of eleven variants (A to K) judged on a subset of the checklist at 25 seeds; the shipped set was variant E. Phase-specific variance multipliers (deterioration 1.5, panic 5, stabilisation 1.5, mania 1.5, blow-off 2, post-top 3) scaled the whole conditional variance; none had a source.

**Events and schedule.** Scripted crash phases (setup, deterioration, panic, stabilisation) and bubble phases (setup, mania, blow-off, post-top) with randomised timing: a setup of 25 to 55 percent of the horizon, deterioration uniform on 15 to 40 days, panic uniform on 15 to 70 days, a fundamental decline D_V uniform on 10 to 30 percent, recovery uniform between delta and 1, a 30-day stabilisation ramp, fixed 50 percent front-loading. Error-correction gains of 0.10 (panic), 0.05 (stabilisation) and 0.10 (post-top) made the scripted target path binding. The bubble top was probabilistic: a hazard h(t) = h0 exp(b x) with h0 = 3e-4 and b = 6.0 and a mania drift capped at 0.012, grid-searched over 36 combinations at 60 seeds to give a "topped" share of 47 percent and a median peak price-to-value ratio of 2.125. A sustained-bull control scenario anchored x with a drift of minus 0.15 x. Rejection sampling redrew a whole schedule when a path failed a validity band. Orderings other than setup-first existed in code, but every LLM run used setup-first and rendered the day as "Day-N".

**Observables.** Nineteen fields, each "a function of the price path, the hidden value path, the GARCH state or its own noise, never of the phase label": date, price, SMA20, SMA50, trend strength, trend regime, RSI14, MACD, MACD signal, volume, volume ratio, news sentiment, sentiment 5-day average, sentiment change, implied volatility, reported P/E, dividend yield, analyst fair value, days since the earnings announcement (the disclosed-horizon arm renders the day as Day-N of T). The P/E used a hidden multiple k drawn uniformly on 14 to 22 per seed with quarterly EPS = V / (4k) times a 10 percent noise, announced 25 to 35 days after quarter end; dividends paid out 35 percent with a Lintner stickiness of 0.7; the analyst estimate was V times an AR(1) error with rho 0.95 per weekly update and a documented stationary standard deviation of 0.15 (implemented at 0.335 by a bug); sentiment had a mean of 0.6 tanh(2x) + 0.3 tanh(ret20 / 0.15), an AR coefficient of 0.85, a return loading of 0.25 and a Tetlock-sized predictive component (+8 basis points next day per standard deviation, 6 reversed over days 2 to 5); volume had an AR coefficient of 0.65, a loading of 0.25 on the absolute standardised return and 1.2 on absolute x; implied volatility was the square root of 252 times a 21-day GARCH variance forecast times (1 + a premium of 0.20, or 0.35 when the variance was in its path's top decile), with a floor of 12 percent, plus a sigma_V add-on and a weight factor inherited from the engine that Phase 3 later found and removed. The rendered prompt equalled the paper's field table by construction.

**Portfolio, action, start.** The action became a target cash share in [0, 1], traded as the difference from the current share, with a 1-point dead band, same-day-close execution, a 5 basis point cost per trade (hidden by default), fractional shares, long only. The initial allocation became an experimental factor: primary = each persona starts at its own band centre (0.80 / 0.50 / 0.10 cash), secondary = a common 0.5, bridge = 1.0 with the v1 interface.

**Targets and bands.** Conservative cash 0.70 to 0.90 (centre 0.80), balanced 0.40 to 0.60, aggressive 0.00 to 0.20, taken from practitioner allocation guidance (Morningstar, Fidelity, Vanguard, Betterment); band-MAS = the mean daily distance outside the band; the v1 target of 1.0 kept only as a labelled fully-liquid level in one track.

**Arms and agents.** One configurable stateless agent for every arm ("the arm is a configuration, not a class") with a registry of arms: static, memory (the mandate re-injected every step), a declarative placebo, a directive placebo (imperative-, delimiter- and length-matched), a wrapper-only arm, a swapped-mandate arm (ISFJ and ENTJ mandates exchanged), a trader arm (no persona, no mandate), variants with the mandate in the system prompt, and stateful arms with a rolling context of 5 or 20 turns, a full transcript up to 60,000 tokens, or a running summary; a forked restatement probe; temperature 0.2; parse failures retried three times, then marked as fallbacks and excluded from scoring.

**Logging and provenance.** Every row carried the hidden x, the phase, resolvability flags at theta 0.03 / 0.05 / 0.08, the target and derived action, the cost paid, the arm and track, and provenance columns: the environment version, a hash of the full generator configuration, a hash of the generator code (which, until Phase 0, covered only the facade module), prompt hashes, temperature and the code revision.

**Evaluation.** Point-MAS, band-MAS, RG with coverage on resolvable rows, and the mandate-conditional regret MCR = the mean absolute distance between the agent's cash share and the true-value oracle's target clipped into the persona's band, over resolvable steps. Twelve rule policies run on the same price path from the cell's start (always hold, always buy, always sell, random, buy on day 1 and hold, constant mix, momentum, mean reversion, the V oracle, the mandate-conditional oracle, the observables oracle and the no-mandate trader). A target-free mandate-salience decomposition by permutation importance. The 20-item checklist and the leakage audit (L1 algebraic inversion, L2 surrogate, L2b phase clock, L4 resolvability) were written to run on either generator. A statistics track held sign counts, Cliff's delta, a mixed model, bootstrap intervals and a BH correction across metrics.

### 4.3 Where the v2 numbers came from

Of roughly 200 numeric choices in v2, about a dozen traced to a published statistic. The rest were plan anchors (stated without a source), CAL values tuned against the checklist, or design choices. The plan's own approximate anchors that were never verified included a daily GJR gamma of about 0.1, a weekly sentiment AR(1) of 0.7 to 0.8, a monthly sentiment persistence above 0.9, a single-stock P/E interquartile range of 12 to 30 and published bull and bear cycle durations of 25 and 15 months. The hazard, the GARCH set, the jump rate, phi and several checklist bands were tuned to what the generator produced, and three amendments changed the statistic or criterion of items 7, 9 and L1 after a fail.

| Block | v2 value | How it was set |
|---|---|---|
| sigma_V, mu_V, value shock tail | 0.006 / day, 0.00025 / day, t5 | plan anchors, cited qualitatively |
| Engine, half-life, price scale | Franke-Westerhoff fallback, phi 0.4632, pull-rate half-life 150.0 d; price scale 100 | CAL after the SMM was rejected; units unverified |
| GJR-GARCH-t | 0.10 / 0.10 / 0.83, sbar 0.017, df 5 | CAL, variant E of eleven |
| Jumps | 0.010 / day, N(minus 0.04, 0.03) in x | CAL (raised from 0.004 to 0.008 to 0.010) |
| Phase multipliers | 1.5 / 5 / 1.5 / 1.5 / 2 / 3 | no source |
| Event ranges and gains | as in section 4.2 | design choices with loose anchors |
| Hazard | h0 3e-4, b 6.0, drift cap 0.012 | CAL: grid-searched to a 40 to 60 percent topped share and a peak P/V of 1.6 to 2.5, targets without a source |
| Sustained bull | drift minus 0.15 x, band [minus 0.10, 0.15], variance x 1.0 | amendments; 40 percent of draws rejected |
| P/E multiple, EPS noise, lag, payout, stickiness | U(14, 22), 0.10, U(25, 35) d, 0.35, 0.7 | uncited |
| Analyst error | sd 0.15, rho 0.95 | uncited; implemented at 0.335 |
| Sentiment, volume, IV constants | as in section 4.2 | uncited; the Tetlock size was LIT |
| theta, band half-width, dead band, cost, temperature | 0.05, 0.10, 0.01, 5 bp, 0.2 | stated |
| Bands | 0.70 to 0.90 / 0.40 to 0.60 / 0.00 to 0.20 | LIT (practitioner guidance) |

### 4.4 The decisions and amendments

The eleven design decisions, all taken as recommended: (1) the instrument, a leak-free, phase-controlled, baseline-normalised environment, is the apparatus in every case, and the causal arms decide the thesis; (2) the mispricing engine is the Franke-Westerhoff form re-estimated by SMM on single stocks, with a fallback half-life of 60 to 120 days if the SMM fails; (3) event durations are design choices with quoted anchors rather than a fitted Markov chain; (4) the initial allocation is a factor with start-at-own-centre primary; (5) the action is a target cash share with a 1-point dead band; (6) the ISFJ target is the 0.80 band centre; (7) the bubble top is hazard-based with topped and un-topped strata plus a sustained-bull control; (8) multi-asset capability is built but the main grid runs one asset; (9) a 5 bp cost, hidden by default; (10) sentiment is predictive at the Tetlock size; (11) the horizon is undisclosed, the field order canonical, execution at the same-day close.

Decisions on the open issues: checklist item 3 (volatility clustering) fails and is reported, no threshold moved; item 10 is restated on the event-window drawdown and still fails; the L2 gate was restated on the selectivity of non-price fields and withdrawn the same day after the integrity review, so the pre-registered absolute gate remains the gate and it fails; the sustained-bull rejection rate is published per run; the Franke-Westerhoff units are flagged for verification. The integrity review also reverted the sustained-bull variance multiplier to 1.0 (a volatility reduction is a scenario clock through implied volatility), relabelled items 9 and 11 as calibration targets rather than validations, reconciled the half-life numbers, re-ran the L2 audit at 50 seeds, re-specified the observables oracle to regress x with full and price-only variants, and added a rolling-5 control arm for the summary arm.

The pre-registration amendments, in order: item 7's log-normality criterion relaxed from a median Shapiro p above 0.05 to p above 0.01 in at least half the seeds; item 9 judged on 800-day phase-free paths because the 200-day estimator is biased; the multipliers scale the whole conditional variance; the sustained-bull anchoring and its variance multiplier; the mania drift cap; the L1 rule (a candidate reproduces V if its median error is below 1 percent or it lands inside the floor more often than the price itself plus one point); item 10 on the event window; the withdrawn L2 restatement; and, in Phase 0, a relabelling of the normalisation and the removal of the day-1 gate under start-at-target, with no number changed.

### 4.5 Validation as published

**The checklist** (50 seeds per scenario, crash per delta, T = 200): 8 pass, 7 fail, 5 not applicable (v1: 3 / 10 / 7; the deck's "7 not applicable" was a miscount). Items 4 and 9 used only 20 paths of 800 days; item 11 used 50 bull paths; most others pooled 470 paths.

*Table 4.1. The v2 checklist result by item.*

| Item | v2 result | Statistic |
|---|---|---|
| 1 No linear autocorrelation | pass | Ljung-Box p above 0.05 in 88 percent of seeds; median absolute ACF(1) 0.080 |
| 2 Heavy tails | fail (margin) | excess kurtosis above 1.5 in 79 percent (need 80); Hill index 3.36 |
| 3 Volatility clustering | fail | Ljung-Box on absolute returns rejects in 61 percent (need 80); ACF of absolute returns at lag 1 0.151 |
| 4 Decay of the ACF of absolute returns | not applicable | 0.229 / 0.177 / 0.154 / 0.083 / 0.017 at lags 1 / 5 / 10 / 20 / 50 (T = 800, n 20) |
| 5 GARCH persistence | pass | alpha + beta 0.964 |
| 6 Leverage effect | fail (margin) | negative correlation in 68 percent (need 70); gamma 0.047 |
| 7 Volume and volatility | fail (margin) | Spearman 0.372; volume AC(1) 0.806 (band 0.5 to 0.8); Shapiro p above 0.01 in 48 percent (need 50) |
| 8 Gain and loss asymmetry in a crash | pass | skew minus 0.392; worst day larger than best in 70 percent |
| 9 Mispricing persistence | pass | T = 800: ACF(1) 0.9905, half-life 72 d, sd(x) 0.128 (200-day windows: 0.9507 / 14 d / 0.053); a calibration target, n 20 |
| 10 Delta matters | fail | event-window drawdown: partial R-squared 0.38 (need 0.7), spread 18.0 points (need 20); means minus 53.0 / minus 42.6 / minus 35.0 percent |
| 11 Bubble shape | pass | convex in 66 percent; topped 44 percent; topped peak P/V 2.21; a calibration target |
| 12 Sentiment | pass | ACF(1) 0.873; corr(s, r) 0.365; the lagged-correlation clause was never implemented |
| 13 Implied volatility | fail (margin) | calm 28.6, panic 59.4 (need 60); corr(IV, RV) 0.39 (need 0.40) |
| 14 Value leak | fail on the L2 absolute gate; pass on L1 | see the audit below |
| 15 Phase and time separability | pass | day-only accuracy 64.8 percent on a mixed set of orderings; 73.7 within scenario |
| 16 Composite phase clock | pass | L2b selectivity +6.9 points (limit 10) |
| 17 Conditioning | fail | rejection rates: flat 0.0, crash 1.3, bull trap 5.7, sustained bull 39.8 percent |
| 18, 19 Start design and action reachability | unit tests pass | any allocation reachable in one step; SELL feasible on day 1 |
| 20 Magnitudes | pass | crash drawdown minus 48.0 percent; calm daily sigma 1.53 percent; worst panic day minus 7.9 percent |

**The leakage audit** (50 seeds, 150 of 400 paths kept after subsampling, 30,000 steps; re-run in Phase 0 after the analyst fix): L1 passed under the amended rule (best candidate k times the analyst estimate, median absolute error 0.101 after the fix, 0.224 before; price 0.124; k times P / PE 0.155); L2 failed the absolute gate (calm R-squared of x 0.918 by gradient-boosted trees, sign accuracy 0.974, against limits of 0.30 and 0.70; event R-squared 0.966; MAPE of V 4.5 percent against a limit of 10); the price-only calm R-squared was 0.787; L2b passed (full 85.2 percent, price only 78.3, day only 54.6, majority 43.3; selectivity +6.9 points); scenario discrimination recalled 82.5 to 85.1 percent of sustained-bull days; L4 coverage at theta 0.05 was 0.717 flat, 0.877 bull trap, 0.840 crash and 0.057 sustained bull.

**The observables oracle** (a gradient-boosted tree on the rendered fields with 5 lags; 12 training and 10 evaluation seeds, no intervals): out-of-sample R-squared of the estimated x 0.95 / 0.97 / 0.93 by phase group (price only 0.90 / 0.91 / 0.80); MCR gap to the true oracle 0.018 to 0.019 in bull trap and crash, 0.031 to 0.032 flat, 0.085 to 0.086 sustained bull (price only within 0.01 of the full set). The reading offered at the time, that the environment's claim is "leak-free fields and algebra, not an uninferable mispricing", was withdrawn in Phase 0 once the start-price anchor was understood.

**Generator sensitivities** (the default at 50 seeds, the variants at 25 seeds per scenario; 15 applicable rows): default 8 pass / 7 fail; the index engine 8 / 7; the published single-stock engine 7 / 8; the 60-day engine 7 / 8; omega-only scaling 7 / 8; panic x3 9 / 6; panic x6 8 / 7. Five of the six published footers carried different counts; Phase 0 regenerated them from the underlying tables. At 25 seeds the margin items flip at random between variants, so "stable across variants" was not a supported statement.

**The pilot** (Gemini 2.5 Flash, one seed, T = 200, three personas): 36 main runs (static, memory, directive-placebo and swapped arms across flat, bull trap and crash at delta 0.70), 9 common-start runs and 3 stateful runs; 48 runs and about 9,800 calls, 100 percent parsed, no fallbacks. Three scenarios, not the four the speaker script claimed. Mean cash share over the run (static / memory / placebo / swapped): ISFJ 0.70 / 0.97 / 0.66 / 0.29; INTJ 0.14 / 0.24 / 0.14 / 0.28; ENTJ 0.27 / 0.29 / 0.26 / 0.98. MCR as re-scored in Phase 7 (n 3 to 4 per cell): ISFJ static 0.2514, memory 0.2342, swapped 0.5949; INTJ 0.3925 / 0.3610 / 0.4771; ENTJ 0.2101 / 0.2414 / 0.9396. The published normalised MCR had been normalised against constant mix rather than the mandate oracle and was withdrawn; none of the 52 pilot paths can be regenerated because the engine they recorded no longer exists. The pilot models saw the defective analyst field.

**What v2 did not do.** No real LLM runs on the v2 harness beyond the pilot; the statistics track never ran on real data; the multi-asset per-asset audit and the sensitivities that need LLM runs were not made.

### 4.6 What the reviews found

Three independent review agents (parameter provenance; claims versus evidence; methodology and robustness) and the team lead's four concerns produced a list of 74 numbered weaknesses, each rated by severity, with the ones marked as verified re-run by the author. The seven that mattered most:

1. **The fixed start price was a hidden answer key** (verified). With price and value both starting at 100 and value drifting slowly, log(P / 100) is the mispricing to within about 0.08 for the whole run. A two-line rule (sell to the band's high edge if the price is above 105, buy to the low edge below 95) reached a regret of 0.005 (bull trap), 0.006 (crash) and 0.013 (flat) against the true-value oracle's 0.003 and always-hold's 0.10 to 0.14; it failed only in the sustained bull (0.098). Every "price history predicts mispricing by design" statement, the L2 audit, the observables oracle and three slides were explained by this anchor.
2. **The Franke-Westerhoff model was not what ran** (verified). With a price scale of 100 the switching saturates: the fundamentalist share exceeds 0.99 on 98 percent of days; the chartist parameters have no effect; the calm process is an AR(1) with a constant weight.
3. **With the anchor removed, the fields leaked.** With a randomised start price the price-only R-squared of the mispricing fell to 0.22 and the full field set gave 0.78; the channels were the P/E (a multiple as narrow as the mispricing itself), sentiment (whose mean is 0.6 tanh(2x)), volume (rising with absolute x) and the analyst estimate (V times an error).
4. **The flat control was biased cheap** (verified). Jumps with a mean of minus 4 percent enter x, so flat mispricing averaged about minus 0.07 to minus 0.10 with 63 to 70 percent of days undervalued; the oracle said "buy" on about three quarters of resolvable flat steps.
5. **The claim that the hidden value is withheld was contradicted by the audit**: V recovered to 3.5 to 4.9 percent MAPE, x with R-squared 0.90 to 0.96; a slide said "withholds the level of value".
6. **The calendar remained a phase clock in the runs actually made**: every LLM run used setup-first ordering and "Day-N"; in that population P(calm given day at most 50) = 1.00 and P(event given day at least 170) = 1.00; day-only phase accuracy 80 to 87 percent. The 65 percent on a slide came from a mixed set of orderings no run used.
7. **"Nothing re-tuned to pass" was not true**: three amendments changed criteria after fails; the GARCH set, the jump rate, phi and the hazard were tuned against the checklist; several bands were moved to what the generator produced.

The remaining items fell into: numbers with no adequate justification (covering every block of section 4.3); claims stronger than the evidence (the SMM "not identified" claim rested on one stalled optimiser run; the "150-day half-life, about 70 realised" statement was an estimator artefact, since a pure AR(1) with a true 150-day half-life reads 62 days at T = 800 and 21 at T = 200, so item 9 could not distinguish 150 from 580; real 200-day windows of ten United States stocks failed the clustering criterion more often than the generator; the sensitivity counts were wrong in five of six rows); design and methodology flaws (implied volatility jumped by a factor of 1.9 on the first panic day with a z of about 7 and used a whole-path quantile with look-ahead; the mispricing was near-constant within a run, so the oracle changed its mind zero or one times and 77 to 91 percent of resolvable steps sat at one band edge; the blow-off label was a calendar label in the 58 percent of bull runs that never topped; MCR tracked band-MAS almost one for one; its normalisation was mislabelled; the day-1 gate was ill-posed under start-at-target; the stateful arm's covariate ignored the re-injected block; the statistics nested seeds inside models although they are crossed); testing gaps (no power analysis anywhere; the continuous-integration leakage test was an expected failure, so a green build required the leak; the generator was not frozen by a hash); and bugs, silent overrides and stale numbers (the analyst error at 0.34 instead of 0.15; a parameter file silently overriding module constants; an engine silently falling back to another; the half-life stated seven different ways).

The review closed with what a robust environment would need, in order: randomise the start price and make the price control level-free; fix the Franke-Westerhoff units, the analyst bug, the jump placement and the sustained-bull control, and freeze the generator with hashes; replace each plan anchor with a fitted estimate from a stated dataset; rebuild the checklist thresholds from real 200-day windows with a power analysis; run event-first and phase-free orderings and stop rendering the absolute day; repair the metric layer and the mixed model; redo the SMM properly; run generator-parameter sensitivities through the LLM grid. That list became the v2.1 plan.

### 4.7 Contradictions between v2 documents

Where two v2 documents disagreed, both sides were recorded and later resolved. The mispricing half-life was stated as 60 to 120, 90, 120, 150, 187, 72 and 14 days in different places (resolved in Phase 0: pull rate 150.0 days; long-pilot ACF half-life 147 days over five 200,000-step pilots; sample medians of 20 days at T = 200 and 62 days at T = 800, all estimator-biased). The jump rate was 0.008 in the variant table and 0.010 in the code (0.010 shipped; the 0.010 configuration was never run in the variant table). The sustained-bull variance multiplier was 0.25 in two documents and 1.0 in the code. The analyst error was 0.15 documented and 0.335 implemented. The checklist's not-applicable count was 7 on the deck and 5 in the file. Item 15's mixed-set accuracy was 64.8 percent on 470 paths and 53.5 on 150 Phase 0 paths (seed-unstable). The topped share was 44, 47 and 62 percent in three runs of 50 to 60 seeds (a 50-seed share is plus or minus 14 points). The pilot scenario count was four in the speaker script and three in the notes. The Franke-Westerhoff units were "price scale 100, to verify" and, from the paper's equation (1), price scale 1.

---

## 5. The v2.1 programme: rule, protocol and plan

### 5.1 The governing rule

The v2.1 improvement plan covers every one of the 74 weaknesses and the review's list of what a robust environment would need. Its governing rule: **every generator parameter is fitted or tested on data, never stipulated.** Every number carries a provenance label (LIT, FIT, CAL, DESIGN; ESTIMATE only for effort numbers; DERIVED, formalised as a label in Phase 6); nothing may be adopted with the label "plan", "arbitrary" or "conventional"; and a statistic marked as unverified may not appear in a parameter file, a test tolerance or a slide. The team lead's version: every number must be justified by published finance literature, then fitted or tested on data or by experiment.

### 5.2 The protocol every phase followed

Six steps per phase: (1) a literature review with a citation table marking each source as read and correct, read and wrong, or not retrievable; (2) a pre-registration written before any run (data, seeds, horizons, estimators, the exact statistic, the decision rule, a power analysis), never edited afterwards, with an addendum recording every disconfirmation and every corrected rule together with what had already been seen when the correction was made; (3) runs saved with seeds, horizon, path count and the generator hash; (4) each decision recorded with the alternatives rejected, the evidence and the label, and a stop for the team where evidence cannot decide; (5) regression tests locking the decision in; (6) documentation and a claims ledger.

Reporting rules: every number carries its n and a 95 percent interval (cluster bootstrap by path); before-and-after comparisons use the same window, estimator and seed count; failures are reported as failures; every tuned parameter is labelled CAL. Power rules: share criteria are sized for 80 percent power at 5 percentage points on the wrong side (about 420 paths at a base rate of 0.80); median and correlation criteria need a bootstrap half-width of at most one fifth of the band; generator-versus-real equivalence means a bootstrap 95 percent upper limit of the two-sample Kolmogorov-Smirnov distance below 0.10.

Two working rules matter for reading the phases. The **execution-order rule**: anything that changes the environment or the prompts restarts from step 0, which means re-freezing the generator's hash manifest, regenerating a fixture of 95 path configurations, and re-running the checklist and the leakage audits on the handed-over state. The **known-defect registry**: every expected test failure is listed with the weaknesses it stands for and the phase that owns it; the programme's acceptance criterion is an empty registry.

Every generator change from Phase 1 onwards is a **switch with the v2 behaviour kept behind it**, proved inert when off by the fixture of 95 configurations (ten seeds of each scenario in setup-first order, five in event-first order, four sensitivity engines, a three-asset crash) whose hidden and rendered columns are hashed and compared.

### 5.3 What the plan reproduced before it was written

The plan's first section re-ran the review findings on fresh seeds before any phase started:

| Finding | First draft | Third pass (new seeds) |
|---|---|---|
| Flat biased cheap by jumps | mean x minus 0.100, median minus 0.068, P(x below 0) 0.70 (30 seeds); jumps off minus 0.018 / 0.50 | mean x minus 0.077 (SE 0.019, 50 seeds); analytic stationary mean minus 0.087 |
| Franke-Westerhoff switching inert | days with a fundamentalist share above 0.99: 0.981; price scale 1 gives a mean share of 0.827 | 0.975; 0.9985 (scale 100) / 0.8268 (scale 1) |
| Analyst error sd | pooled 0.350 (30 crash paths x 460 days) | 0.306 full / 0.330 on benchmark days; analytic 0.335 |
| IV step at panic onset | +0.594 log IV (x 1.81), calm sd 0.084, z 7.1 | +0.606 (x 1.83), z 7.06 |
| Sustained-bull selection | accepted daily sd 0.0150 against rejected 0.0242; rejection 0.38 | 32 / 18 of 50; 0.0153 against 0.0210; 0.36 |
| Half-life estimator artefact | median 26 d at T = 200, 72 at T = 800; 55 percent clear 60 d | 35; 65; 60 percent |
| Start-price answer key | rule MCR 0.014 / 0.007 / 0.005 / 0.098 against the oracle's 0.003 (12 seeds) | 0.022 / 0.011 / 0.007 / 0.083 (direct scoring) |
| Half-life inconsistency | phi 0.463 gives a pilot ACF(1) of 0.9963, hence 188 d | five 200,000-step pilots: 141 to 154 d (mean 147); 188 was one pilot's sampling error |

The plan also settled the Franke-Westerhoff units from the paper (equation (1) defines the return as 100 times the change in the log price, so the misalignment term takes natural-log deviations and the price scale should be 1), found that the test suite could not even be collected (a legacy test needed an uninstalled package), measured the generator's cost (0.17 seconds per 200-day path) and the prompt sizes (system prompt about 1,510 tokens, one human message about 560, a stateful rolling-20 call 19,500 to 20,000 tokens), and listed the free data substitutes for the commercial databases that the programme would fit on.

### 5.4 The phase map

| Phase | Goal in one sentence | Weaknesses closed |
|---|---|---|
| 0 Verification and freeze | reproduce every review finding from code with fresh seeds; fix outright bugs; remove silent overrides; freeze the generator with hashes; add statistical regression tests; clean the test suite; correct stale documents; no design change | the wrong counts, the mislabelled normalisation, the ill-posed gate's input, the missing freeze, the structural-only tests, the analyst bug, the silent overrides, the inconsistent statements |
| Data panel | download the free substitutes every fit will use | (data) |
| 1 Value and price structure | remove the start-price answer key; fit the value process; decide where jumps belong; set the burn-in by a stationarity test; level-free leakage audits | the answer key, the level-free audit, the flat bias, the value recovery, the unsourced value constants, the jump placement, the anchored oracle claim, the short burn-in |
| 2 Mispricing engine | resolve the Franke-Westerhoff units against the paper; decide between a working Franke-Westerhoff engine and an AR(1) with GARCH on pre-registered evidence; estimate persistence from firm-level data; tabulate the half-life estimator's bias | the inert switching, the hand-set half-life, the units, the identification claim, the estimator artefact, the "stable counts" claim, the horizon question |
| 3 Volatility | fit the GJR-GARCH-t shape per stock, the jump rate and size and the phase multipliers; build an implied-volatility construction that is neither a phase step nor a look-ahead | the tuned GARCH set, the tuned jumps, the unsourced multipliers, the unsourced IV constants, the IV phase step, the GARCH fit on regime paths |
| 4 Events, schedule, controls | crash and bubble durations, depths and hazard from historical episodes; the sustained-bull control; the error-correction gains; orderings; the calendar as a clock | the calendar clock, the unsourced event ranges and gains, the tuned hazard and its targets, the selected sustained-bull population, the capped mania, the calendar blow-off label, the redraw rule, the shared multi-asset event |
| 5 Observables | anchor each field to a stated source and design it so that no field is a deterministic function of the hidden state; level-free audits and an onset-detection test | the field leaks, the narrow multiple, the unsourced analyst, earnings, sentiment and volume constants, the undocumented constants, the paraphrased anchors |
| 6 Audits and checklist methodology | an empirical reference distribution from real 200-day windows for every statistic; per-item power; the L1 set extended; the L2 and L2b gates derived; the tuned-parameter ledger; the go / no-go checkpoint | the value-recovery claim, the tuned-to-pass record, the missing power analysis, the stated thresholds and margins, the mis-stated clustering claim, the unimplemented criteria |
| 16A go / no-go | four gates: information to act on (G1), not solved by a two-line rule (G2), judgement over time (G3), the level-free observables oracle beats the price-only oracle and the surrogate sits under the Kalman bound (G4) | the team decides if any gate fails |
| 7 Targets, action and metrics | derive theta; decompose regret into band adherence and direction with a correct floor and ceiling; check the bands against the environment's own risk and return; pay dividends; re-specify the day-1 gate; compute baselines on each cell's own path | the stated theta, the stated scoring constants, the index-based bands, the one-shot call, the collinear metric, the mislabelled normalisation, the ill-posed gate, the mismatched baselines, the pre-trade log |
| 8 Harness and statistics | correct the stateful arm's covariates and token budgets; make context length a factor; fix the mixed model, clustering and multiplicity; identify or drop the salience shares; size the main grid | the stipulated context budget, the unidentified shares, the stateful arm's defects, the invalid statistics, the untested placebo matching |
| 9 Sensitivity through the LLM harness | sweep the generator parameters that drive results through an LLM grid; time and pilot the roster; size and cost the grid before any paid call | the value, persistence, volatility, multiple, analyst, sentiment and multi-asset constants as they affect LLM behaviour |
| 10 Documentation | correct every document, the deck and the script to verified numbers with n and labels | the stale numbers and the overstated claims |

Order: Phase 0, then the data panel, then Phases 1 to 3, Phases 4 and 5, Phase 6 with the 16A checkpoint, Phase 7, Phase 9 (with Phase 8's power analysis; Phase 8's code work at any time after Phase 0), Phase 10. Cost estimate before Phase 9: about 120 dollars of API spend plus a Phase 9 tier of about 210, 775 or 1,000 dollars; analyst effort 72 to 107 person-days.

### 5.5 The team decisions the plan asked for

Seventeen decisions were reserved for the team: the data source (proceed on the free substitutes, publish each fitted value with its survivor-versus-literature gap, keep the code re-runnable on the commercial databases by a data-path change); the LLM roster and budget (re-framed in Phases 8 and 9); what to do if the firm-level value and mispricing decomposition is not identified (answered by Phase 1's estimator and applied in Phase 2); which population the crashes and bubbles represent (the single-stock panel); what to do if no event formulation meets its rule (formulation A, the incumbent through Phases 4 to 9, adopted by the team as a design choice on the comparison, section 17); the calendar rendering ("Day-N" kept, with three renderings behind a switch); theta if the two derived candidates disagree (co-primary, Phase 7); the one-shot-call issue (a theta-conditional pass, Phase 7); practitioner against utility-consistent bands (practitioner bands scored, the Merton reading reported); dividends paid or the field removed (paid); the salience shares (a common-start slice only); the minimum effect size (0.05 band-MAS); the start-price mechanism (a provisional normalisation, revised to the combined mechanism after Phase 1); what the sustained-bull control is for (the flat process); the sentiment valuation loading (the returns-only design selected by the rule in Phase 5 and adopted by the team, the valuation-link variants as sensitivities); the full programme against a minimal path (the full programme); and which option to take if 16A fails (restrict the claim).

---

## 6. Phase 0: verification and freeze

### 6.1 Goal

Reproduce every computational finding of the three reviews with fresh seeds and intervals; fix the bugs where the implementation contradicted its own documentation without changing any path's distribution by design; freeze the generator under a hash manifest; add statistical regression tests with a known-defect registry; write the deck-corrections note. Explicitly no design decision.

### 6.2 Work carried out

**Pre-registration.** Fresh seed blocks registered in advance, none overlapping the reviewers' seeds: a main 200-day panel of 50 seeds per scenario; 50 flat seeds at 800 days; 10 at 5,000 days; 50 three-asset crashes; pure AR(1) paths with true half-lives of 60, 150 and 580 days at four horizons, 200 paths per cell; 100 seeds for the analyst error; blocks for each new test; five 200,000-step calm-engine pilots; randomised start prices uniform on 20 to 500. Verdict rules fixed in advance: reproduced (the reviewer's point inside the 95 percent interval, or within 1.96 standard errors), reproduced in substance, not reproduced, documentary.

**Runs.** A single verification tool produced 149 reproduction rows and the canonical numbers that the documentation tests check every document against. Verdicts: reproduced 97, in substance 5, not reproduced 16, documentary 31. **Every headline finding held.** The sixteen rows not reproduced reversed none: seven came from panel composition (a quarter of the Phase 0 paths are sustained-bull paths with a median absolute x of 0.014), five from seed-set differences in 50-seed shares (the un-topped share 0.38 against 0.58; the mixed-set day-only accuracy 0.54 against 0.65), two were false claims found on the way, one was a re-attributed number, and one was the three-term L1 candidate before its fix (0.107 against 0.094).

Selected reproductions (95 percent intervals):

| Finding | Phase 0 measurement (n) | Reviewer | Verdict |
|---|---|---|---|
| The "compare with 100" rule | MCR 0.018 [0.011, 0.027] flat, 0.009 [0.007, 0.013] crash, 0.010 [0.007, 0.013] bull trap, 0.110 [0.089, 0.129] sustained bull; oracle 0.002 to 0.004; always-hold 0.10 to 0.14 (50 seeds) | 0.014 / 0.007 / 0.005 / 0.098 | reproduced |
| Franke-Westerhoff switching inert | fundamentalist share above 0.99 on 0.985 [0.978, 0.990] of flat days; at price scale 1 the index set gives 0.827 | 0.983; 0.83 | reproduced |
| Fields leak without the anchor | anchored: level R-squared 0.849, level-free 0.493 [0.431, 0.549]; randomised start: level calm 0.054 [minus 0.135, 0.179], full 0.653 [0.570, 0.722]; selectivity +0.09 anchored against +0.60 randomised (200 paths) | 0.84 / 0.40; 0.217 / 0.779 | reproduced on 12 rows, not on 4 (panel composition) |
| Flat control biased cheap | mean x minus 0.068 [minus 0.107, minus 0.029]; P(x below 0) 0.632; jumps off +0.009 (50 seeds) | minus 0.100; 0.70; minus 0.018 | reproduced |
| Calendar clock | P(calm given day at most 50) = 1.000, P(event given day at least 170) = 1.000 (2,500 / 1,550 path-days); day-only accuracy 0.828 crash, 0.809 bull trap | 1.000; 0.804 / 0.872 | reproduced on five rows; not on the bull-trap accuracy (0.809 against 0.872) and the mixed-set day-only accuracy (0.54 against 0.65) |
| Analyst error | pooled sd 0.352 [0.323, 0.377] on benchmark days (100 seeds) | 0.333 to 0.335 | reproduced |
| IV phase step | +0.618 [0.591, 0.646] log IV at the deterioration-to-panic transition (z 7.7); calm day-to-day sd 0.080 | +0.62; z about 7 | reproduced |
| Half-life estimator | pure AR(1) with a true 150 d: medians 20 / 59 / 96 / 124 d at T = 200 / 800 / 2,000 / 5,000; five 200,000-step pilots 146.6 d [141.5, 155.4] | 26 / 72; 147 | reproduced |
| One-shot side call | median oracle switches 0.5 / 1 / 1 / 2 per run; steps at one band edge 0.945 / 0.864 / 0.763 / 0.810 | 0 / 1 / 1 / 2; 77 to 91 percent | reproduced on seven rows; not on the flat edge share (0.945 against 0.84, the substance stronger) |
| Sustained-bull selection | accepted daily sd 0.0146 against rejected 0.0235; rejection rate 0.405 [0.306, 0.512] | 0.0147 / 0.0240; 39.8 percent | reproduced |
| "Without a cap every run reaches P/V above 3" | with the cap removed only 0.18 [0.10, 0.31] of bull-trap runs reach P/V 3 | claim: 100 percent | not reproduced: the claim was false |
| Sensitivity footers | five of six differ from their underlying tables | | reproduced |

**Bug fixes** (the implementation made to match the documentation; no path changed except the two analyst columns): the analyst innovation scaled by the square root of 5 was removed (sd on benchmark days 0.352 to 0.158 and over the full 460-day timeline 0.335 to 0.156, measured on 100 seeds; 0.15 documented); the six sensitivity footers were regenerated from their tables; the MCR normalisation labels were made exact (the code normalised against constant mix, not the mandate oracle; the convention went to Phase 7); the day-1 gate was computed on common-start cells only; the hazard module constants were set equal to the calibrated file (they had been 0.0015 / 6.0 / 0.02, silently overridden by 3e-4 / 6.0 / 0.012) behind a loader that fails loudly; the single-stock engine was made to fail unless an accepted estimate exists, the fallback was named for what it is and recorded in every run's metadata; the half-life and other stale statements were unified (21 stale statements located); the runner's trader band was made band-free; the multi-asset t-mixture documented as not t5; the one-dollar holdings threshold named.

**Freeze.** A manifest of SHA-256 hashes over every generator module, the generator's parameter files and six evaluation modules; the generator-code hash in every run row became the first 16 hexadecimal characters of the manifest hash. Written once at the end of the phase: 17 files. The **no-distribution-change check**: 95 configurations, 0 non-analyst column changes, 190 analyst-column changes (the declared fix). The 50-seed checklist re-run reproduced the published table line for line except item 15's within-scenario mean (73.6 to 73.7 percent, the classifier's own random state).

**Before and after the analyst fix** (same seeds): pooled sd 0.352 to 0.158; the median absolute error of k times the analyst estimate 0.240 to 0.110; the three-term mean of k SMA50, k P/PE and k analyst 0.107 to 0.071; the anchored full-set calm R-squared 0.814 to 0.841. **The corrected field is more informative, not less**: a 15 percent error estimates V better than a 33 percent one, which made the amended L1 rule marginal (the 50-seed audit passed by 0.26 points; the 8-seed continuous-integration panel failed) and withdrew the sentence "no formula beats price". This was registered as a known defect rather than the floor being moved.

### 6.3 Decisions

The documented analyst process is authoritative (labelled DESIGN, its value left to Phase 5). Labels and the day-1 gate input were corrected without changing a number. The hazard constants equal the file, with a loud loader. The engine is named for what it is, and the engine used is recorded. The half-life statements were unified and the 188-day figure withdrawn (one 20,000-step pilot's sampling error). The two published values of the stationary sd of x (0.165 / 0.175 with engine weights, 0.126 / 0.134 raw) were both right under different weight normalisations (ratio 0.762, equal to the mean weight 0.761); consequence: the plan's Kalman bound should be read at a stationary sd near 0.175. The 200,000-step re-normalisation was deferred (it would move every path). The correct sensitivity counts were recorded. The freeze manifest is rewritten only at a phase end by one tool. Two legacy tests were repaired, and the finding recorded that the v1 plateau assertion never held on the frozen v1. The known-defect registry was created. The marginal L1 failure was registered, not fixed.

### 6.4 Results that contradicted expectations

The claim behind the mania-drift cap was false (above). The multi-asset implied-volatility inconsistency had the opposite sign from the reviewer's (asset 2's implied volatility over realised volatility 1.41, not 1.06). The legacy v1 bull-trap test never held on the frozen v1 (V moves from 100.60 to 96.32 at its own seed). A new documentary finding: within event phases the scripted drift explains only a small share of daily changes (R-squared of the daily change in x on the scripted drift: panic 0.063 [0.052, 0.073], stabilisation 0.028, post-top 0.207, mania 0.009); the script sets the level path and the GARCH noise sets the daily moves. Five pre-registration deviations were disclosed (fewer bootstrap resamples than registered for the slow statistics; the path-hash fixture rebuilt after it was found to hash object pointers; the plan's premise about the legacy test; a re-attributed pull rate; the L1 expected failure).

### 6.5 Tests

New statistical regression tests, three with tolerances derived from measured standard errors (the flat bias, the analyst error sd, the half-life consistency) and three with provisional design tolerances (the implied-volatility continuity, the fundamentalist share, the sustained-bull selection), eleven phase tests, eleven documentation-number tests and four freeze tests. Six registered v2 defects as expected failures (the flat bias, the IV step, the fundamentalist share, the sustained-bull selection and the two leakage gates), each owned by a later phase. The suite before Phase 0: 1 failed, 68 passed, 3 expected failures, with one file uncollectable. After: 103 passed, 1 skipped, 8 expected failures, 0 failed. No paid API call.

---

## 7. The shared data panel

The free substitutes every later fit uses. Nothing in the generator was touched and no parameter was fitted.

| Need | Outcome |
|---|---|
| Daily prices and volume | Yahoo Finance, 2000 to 2026: 673 of 1,094 universe names returned data (61.5 percent), 428 with full 2000 to 2024 histories |
| Historical index constituents | a 1,094-name universe from two point-in-time constituent lists and an encyclopaedia revision; agreement between the two lists 0.88 to 0.996 (Jaccard) across six dates |
| Quarterly EPS and DPS with filing dates | the regulator's XBRL company facts: 819 of 1,094 filers, 799,946 fact rows, 2005 to 2026; the filing date is not the announcement date |
| Long-run valuation | Shiller's monthly series, 1,868 rows from 1871 to 2026 (a first parse produced 1,712 spurious duplicates from the fractional-year date, fixed) |
| Implied volatility | 25 exchange-published index histories including all five single-stock volatility indices (Apple, Amazon, Google, Goldman Sachs, IBM; 3,929 rows each, 2011 to 2026); the market index from 1990; a central-bank mirror is a copy, not a second source |
| Sentiment | a daily news-sentiment index (17,018 rows, 1980 to 2026); a weekly investor survey (2,041 rows, downloaded by hand because scripted access is forbidden); a monthly investor-sentiment index (702 non-null rows to 2023) |
| Factors, industry P/E, payout, risk-free rate | the Fama-French daily and monthly factors and industries; Damodaran's January tables; the central bank's rate series |
| A second price source | an exchange's public historical endpoint: 640 of 673 tickers, 2016 to 2025 |

**Survivorship.** Of 752 names still in the index at the end of 2024, 589 were retrieved and 416 had full histories; of 342 names that left the index, 84 were retrieved and 12 had full histories. **Ticker reuse**, the defect the plan did not anticipate: the price source serves whichever company holds a symbol today, so 86 of 673 series (12.8 percent) were flagged, 64 of them by a start-date test (the series begins more than 180 days after the index exit, in one case by 9,086 days); of the 342 departed names only 16 (4.7 percent) survive both screens. The second price source independently found the two reuse cases with a return correlation below 0.90. Source agreement over 1,424,865 day-pairs: median per-ticker return correlation 1.000000. Quality: no duplicate dates, no calendar gaps above 7 days, no non-positive closes; 400 day-observations with absolute returns above 50 percent left as they are. A first pass had called two of the sources independent when one mirrors the other, and had put delisted coverage at 24.6 percent; both were corrected.

Phase 1 then fixed the **exclusion rule** before any statistic: drop every flagged series and the two duplicate spellings; window 2000 to 2024; log returns of the adjusted close, nothing winsorised or filled. **Set A** = 417 flag-free full-history names (the primary panel for every fit that follows); **set B** = 155 flag-free names with at least 1,000 days but not a full history (the pre-registration counted 158; both recorded). Every tail statistic in the programme is survivor-based; the Phase 1, 3 and 6 reports say so beside each number, and the caveat applies equally to the Phase 4 episode tables.

---

## 8. Phase 1: value and price structure

### 8.1 Goal

Fit the value process (sigma_V, mu_V, the tail of its shocks) and the mispricing's persistence and amplitude from data with three estimators and a simulation-recovery study; decide where jumps belong; set the burn-in by a stationarity test; test the start-price mechanisms against a level-feature versus level-free attacker; sweep sigma_V against the mispricing's amplitude against the analytic Kalman bound; run level-free leakage audits before and after on one standard panel. The phase also fitted the per-stock GJR-GARCH model because Phase 2 needed it.

Two panels were fixed here and used by every later phase: the **standard evaluation panel** (1,600 paths of 200 days, six path types per seed in setup-first order and two in event-first order (1,200 and 400 paths); 320,000 rows, 288,000 after the first days are dropped for lags; no subsampling) and the **standard checklist panel** (200 seeds per scenario). The surrogate for every audit is a gradient-boosted tree (200 iterations, learning rate 0.08, depth 6) scored out of sample by five-fold cross-validation grouped by path, with ridge and MLP alternatives and the best per cell reported. Three feature sets: **level** (price, the moving averages, the technicals and their lags, 51 features), **level-free** (returns at 1, 5 and 20 days, log price over the two moving averages, RSI, MACD over price, the trend fields and their lags, 45 features, no level), **full** (all 18 rendered numeric fields with lags, 111 features).

### 8.2 Work carried out

**Per-stock GJR-GARCH(1,1)-t fits** on set A, full sample, 417 of 417 converged: alpha 0.027 [0.025, 0.030], gamma 0.058 [0.055, 0.061], beta 0.932 [0.928, 0.935], tail degrees of freedom 4.86 [4.73, 5.02], persistence 0.991, unconditional daily standard deviation 0.0218 [0.0210, 0.0225] (1,000-resample stock bootstrap). Set B (155 shorter, partly delisted names) is fatter-tailed and more volatile (degrees of freedom 4.33, sd 0.0243), which is the direction of the survivor gap. Engle's (2001) portfolio values (alpha 0.077, beta 0.905) were recorded beside as not comparable.

**Three estimators of sigma_V, s_x and the half-life h**, for the model log P = log V + x with V a random walk and x an AR(1):

- **A, Lo and MacKinlay variance ratios** pooled over 417 stocks at horizons of 5 to 500 days: sigma_V = 0.0205 per day [0.0197, 0.0213], s_x = 0.024 [0.022, 0.026], h = 5 days [4, 6]; the random walk carries 0.74 of daily variance; a one-component model is rejected (J = 80 on 8 moments). An exploratory two-component fit strongly prefers a second transitory component near 40 days, and under every fit sigma_V is 2.7 to 3.4 times the v2 value of 0.006.
- **B, the AR(1) of log(P over a filings-based value proxy)** with the Andrews median-unbiased correction, monthly 2009 to 2024, 367 stocks: h = 256 days [223, 277], s_x = 0.39 [0.36, 0.44].
- **C, a simulated method of moments** on persistence-carrying moments: sigma_V = 0.01957 [0.01892, 0.02036], h = 4.82 days [4.17, 5.42], J = 66.6 on 9 moments (misspecified); s_x was published as 0.129 [0.125, 0.135] and **corrected in Phase 2 to 0.0250** (the estimation code had returned the calm engine's sd at the reference 150-day half-life whatever h it fitted).

A and B disagreed by a factor of 50 in h. The pre-registered **recovery study** (synthetic panels of 100 stocks over 6,300 days with known h in {5, 10, 30, 60, 120, 150, 250, 500} days and sigma_V in {0.006, 0.012}; 200 replications for A and B, 50 for C; the h = 5 and 10 cells added after review because A and C located the data below the original grid) decided which estimator to believe: A's intervals cover the truth in 0 to 1 percent of replications (its mapping assumes an AR(1) the engine's x is not); B returns 36 to 47 days whatever the truth, including on a panel with x identically zero (at the panel's noise level it measures the value proxy's error, not x); C is usable (median relative error 0.03 to 0.16) for h up to 150 days and unusable at 250 days and above. **C was adopted alone**, with the stated qualification that the recovery panels come from C's own model. The application of sigma_V was deferred to Phase 2 (applying it would have restarted the whole cascade), so the fitted 0.01957 was recorded as adopted but not applied while 0.006 stayed in force at the hand-over.

![Figure 3](figures/F04_phase1_estimators.png)

*Figure 3. (a) The mispricing half-life from the three panel estimators (A and B in grey, judged unusable by the recovery study; C in blue), followed by the two engine refits of Phases 2 and 3. (b) The stationary sd of the mispricing by estimator; the orange diamond is C's value as corrected in Phase 2 (0.025). 417 stocks for estimators A and C, 367 for B; 30 bootstrap refits for the engine intervals.*

![Figure 4](figures/F05_variance_ratio_curve.png)

*Figure 4. The pooled variance ratio of returns over horizons of 5 to 500 trading days for 417 stocks (with the per-stock interquartile band) and the fitted value-plus-AR(1)-mispricing model (h = 4.9 days). A random walk would sit at 1; the decline is the mean reversion the mispricing produces.*

**Other fitted values.** mu_V from the nominal price index over 2000 to 2024: 0.000228 per day [minus 0.000051, 0.000479] (5.7 percent a year; n = 300 months); v2 had 0.00025. The tail of the value shocks: standardised seasonal EPS changes over 409 stocks (n = 25,859) have an excess kurtosis of 8.3, and neither a normal nor a t5 is equivalent to them by the Kolmogorov-Smirnov rule (upper limits 0.201 and 0.181), so the degrees of freedom remain a DESIGN choice at t5. The start-price range for the randomised mechanisms: the 5th to 95th percentile of unadjusted closes over set A on 40 random dates, 7.47 [6.27, 9.03] to 240.02 [196.78, 290.39] dollars (n = 16,680).

**Where jumps belong.** On the panel, jump days (a standardised residual above 4 in absolute value; 7,492 of 1,670,790 stock-days) cluster in 10-day windows ending on a quarterly or annual filing date: the windows are 14.5 percent of days and hold 43.5 percent [41.2, 45.6] of jump days (rate ratio 4.5). Four generator placements were run at 200 flat seeds with the total rate and size fixed: the current negative-mean jumps in x; mean-zero jumps in x; jumps in log V on announcement days; both. All four passed the Kolmogorov-Smirnov rule against the panel's window split; the generator put only 19 to 28 percent of its large moves in windows against the panel's 43. The mean of x over 200 flat paths was minus 0.069 [minus 0.088, minus 0.048] under the current placement and +0.010 under mean-zero jumps; the rule selected mean-zero jumps in x, which are in force. A confirmatory equivalence test at 1,000 seeds gave E[x] = +0.0126 [+0.0038, +0.0214], failing the plus or minus 0.02 margin by its upper limit; with jumps off entirely the same seeds gave +0.0113, so the residual was the calm engine's own (its sentiment and trend feedback), not the jumps'; it was registered as a Phase 2 defect and closed there. Derived: the announcement share q = 0.4345 [0.412, 0.456].

**The burn-in.** State variables (x, the GARCH variance, the fundamentalist share) on day 1 against their day-5,000 distribution, per engine, 2,000 paths per engine and option (the pre-registered 500-path run was uninformative because at 500 against 500 the Kolmogorov-Smirnov upper limit under identical distributions is about 0.12, above the 0.10 rule; disclosed in the addendum). The v2 burn-in of 260 days is adequate for the 150-day and 60-day engines (distances on x of 0.047 and 0.046) and inadequate for the 620-day engines (0.172 and 0.170). Adopted: 750 days (five half-lives) for the default engine; a stored day-5,000 state plus 60 days for the four sensitivity engines.

**The start-price mechanisms.** Four mechanisms behind one switch: fixed (v2: V1 = P1 = 100); A, randomise (V1 log-uniform on 7.47 to 240.02, P1 = V1 exp(x1)); B, normalise (P1 = 100, V1 = 100 exp(minus x1), the team's provisional choice); C, both (B plus a per-seed render scale applied at render time to every price-denominated field, so that ratios and shares are unchanged). 500 seeds per scenario per mechanism. The attacker rule: the R-squared advantage of the level feature set over the level-free set must have a confidence interval touching zero in every scenario. The rule-100 test: the two-line rule's regret must sit inside the range of the two constant band-edge policies.

| Mechanism | Advantage of level over level-free: flat / crash / bull trap | Attacker | Rule-100 regret flat / crash / bull trap / sustained bull | Rule-100 |
|---|---|---|---|---|
| Fixed (v2) | +0.64 [+0.58, +0.70] / +0.57 / +0.33 | fail | 0.015 / 0.011 / 0.009 / 0.083 (oracle 0.002 to 0.004) | fail |
| A randomise | +0.02 [minus 0.02, +0.06] / minus 0.01 / +0.00 | pass | 0.097 / 0.061 / 0.115 / 0.105 | pass |
| B normalise | +0.08 [+0.01, +0.14] / +0.21 / +0.12 | fail | 0.072 / 0.045 / 0.046 / 0.084, below both band edges everywhere | fail |
| C both | minus 0.03 / minus 0.06 / minus 0.03 | pass | 0.096 / 0.062 / 0.113 / 0.104 | pass |

**The team's provisional mechanism B failed both rules**, because with P1 fixed at 100 the level encodes the cumulative return since day 1: log(P_t / 100) is approximately x_t minus x_1, so the level predicts x with an R-squared near 0.1 at day 50 and 0.3 at day 200 for a 150-day half-life. The team revised its decision to **mechanism C**; C keeps the hidden paths identical to B's, so the day-1 states, the burn-in and the checklist carried over. A consequence for Phase 5: k times the analyst estimate inverts V with a median error of 0.10 under fixed, A or B, but 0.70 under C (the per-seed scale defeats a single fitted k).

![Figure 5](figures/F27_start_price_mechanisms.png)

*Figure 5. The four start-price mechanisms. (a) The attacker test: the R-squared advantage of the price level over level-free features, per scenario, with 95 percent intervals; the level may add nothing. (b) The rule-100 test: the two-line rule's regret against the range of the two constant band-edge policies and the true-value oracle. 500 seeds per scenario per mechanism (2,000 paths each); 500-resample cluster bootstrap. Mechanism B was the team's provisional choice and failed both tests; C is in force.*

**The sigma_V by s_x sweep against the Kalman bound.** 40 grid points (sigma_V in {0.004, 0.006, 0.010, 0.015, 0.020}, Gaussian or t5 value shocks, s_x in {0.10, 0.13, 0.165, 0.20}) at 200 seeds per scenario, a level-free surrogate for x, and the analytic bound (which reproduces the plan's 0.137 / 0.235 / 0.396 at sigma_V 0.006 and s_x 0.13). **No point has a 95 percent interval entirely above the bound** (gaps minus 0.175 to +0.042). A first run on a remote kernel gave calm R-squared of 0.11 to 0.44 with gaps up to +0.34 over the bound and was not reproducible on the reference machine (0.407 against 0.153 on a panel proven identical); the cause was never identified, so every surrogate number was regenerated locally and the remote table kept as a record only; the report's first finding of a non-price channel at every grid point was withdrawn. Two further readings: the checklist's own calm-sigma item prefers a sigma_V between 0.010 and 0.015 (0.006 fails low, 0.020 fails high); coverage at theta 0.05 is a property of s_x alone (0.62 at 0.10 to 0.80 at 0.20).

![Figure 6](figures/F06_phase1_sweep_bound.png)

*Figure 6. The calm level-free R-squared of the mispricing across the 40-point sweep, for Gaussian and t5 value shocks, beside the analytic Kalman bound at the same points; the same colour scale in every panel, so that a measured cell darker than the bound's cell would mean a surrogate above the bound, which does not occur. 200 seeds per scenario per point.*

**The audits before and after.** Before = frozen v2 (V1 = P1 = 100, negative-mean jumps, 260-day burn-in); after = mechanism C, mean-zero jumps, 750-day burn-in, sigma_V still 0.006. Calm R-squared of x: before 0.811 [0.772, 0.840] with the level control and 0.383 [0.278, 0.473] level-free, so the fixed start price was worth +0.43 of R-squared; after 0.161 and 0.086 [0.043, 0.122], so about five sixths of the level channel was gone. The full field set's calm R-squared fell from 0.928 to 0.823, its MAPE of V rose from 4.1 to 12.5 percent. L1's best candidate went from k times the analyst estimate (median error 0.10) to the price itself (0.126). The L2b macro-phase clock passed the 10-point margin only with the v2 level control (+8.6 points) and failed level-free before (+16.4) and after (+11.7): the v2 control had passed because the price level carried the phase, registered for Phase 6. The observables oracle's MCR rose from 0.041 to 0.051 and the price-only level control from 0.042 to 0.068. The checklist went from 7 pass / 8 fail / 5 not applicable (before) to 5 / 10 / 5 (after): the leverage item turned to pass; the volume log-normality and calm-sigma items turned to fail at the edge; the topped share moved from 52 to 62 percent against a 40 to 60 band.

### 8.3 Parameters at the hand-over

| Entry | v2 | In force after Phase 1 | Label | Evidence |
|---|---|---|---|---|
| sigma_V | 0.006 | 0.006 kept; 0.01957 [0.01892, 0.02036] recorded as adopted, not applied | deferred to Phase 2 | estimator C; A gives 0.0205 by another route |
| mu_V | 0.00025 | 0.000228 / day | FIT | nominal index 2000 to 2024, n = 300 months |
| Value shock tail | t5 | t5 | DESIGN | EPS tails, n = 25,859 |
| Start-price mechanism | fixed | C (both) | DESIGN (team decision revised) | 2,000 paths |
| Start-price range | none | [7.47, 240.02] | FIT | n = 16,680 |
| Jump placement | negative mean in x | mean zero in x | FIT / DESIGN | 1,000 seeds |
| Announcement share and derived rates | none | 0.4345, 0.2737, 0.005655 | FIT | 7,492 jump days |
| Burn-in | 260 d | 750 d default; stored state + 60 d for the sensitivity engines | FIT / DESIGN | 2,000 paths per engine |

Freeze: 19 files. Path hashes: every hidden and rendered column changed after (by design). Tests: nine new phase tests, including a stored 500-seed start-price result with a 100-seed live guard and a stored 2,000-path burn-in result with a 500-seed live guard; the flat-bias test promoted to a hard test; the marginal L1 failure disappeared under the new state and its registry entry was removed. Compute: the local 8-core machine plus four remote CPU kernels; no paid API call.

### 8.4 Results that contradicted expectations

The provisional mechanism B failed both rules. Two pre-registered equivalence criteria were guaranteed failures at their registered sample sizes (the equivalence test at 200 seeds; the Kolmogorov-Smirnov bound at 500 paths) and were corrected with disclosure. The first recovery-study scope (8 replications) could not decide C; the full study reversed the first reading. Estimator B measures the proxy's error; estimator A's intervals are far too narrow. The flat residual is the engine's, not the jumps'. Remote surrogate numbers were not reproducible on the reference machine, and the first diagnosis (thread count, early stopping) was refuted.

---

## 9. Phase 2: the mispricing engine

### 9.1 Goal

Decide what generates x and how persistent it is: reproduce the Franke and Westerhoff model from its paper to settle the units; run the simulated method of moments properly, with persistence-carrying moments and a block-bootstrap weight matrix on 417 stocks; apply the disagreement rule between estimators; decide the engine among the incumbent Franke-Westerhoff form, an AR(1) with GJR-GARCH-t innovations and a published Franke-Westerhoff variant by a pre-registered asymmetric rule; tabulate the half-life estimator's bias; sweep persistence through the checklist and the audits.

### 9.2 Work carried out

**Literature read at first hand.** Franke and Westerhoff (2012): equations (1), (5) to (7), the parameter table, the joint moment coverage ratio of 10.1 percent, the empirical moments and the block-bootstrap appendix; the replication table of a later systematic comparison; Pruna and co-authors (2016). Two inputs were found wrong on the way: the plan's replication target (0.23 / 7.8) matched no row of the model it named (the row is 0.1674 / 10.033; the nearest row to the plan's figure, 0.2285 / 7.76, belongs to a different variant), and Phase 1's s_x (above).

**The Franke-Westerhoff model reproduced.** The paper's specification at its own parameters, 200 runs of 6,750 steps. At a price scale of 1 the joint moment coverage ratio was 10.0 percent [6.6, 14.9], containing the paper's 10.1; at a price scale of 100 it was 0.0 percent [0.0, 1.9] and the chartist share 0.0028 (switching saturated). **A price scale of 1 was confirmed as a literature bug fix.** The per-moment profile did not reproduce (thinner tails than the paper, higher coverage at long lags) and was reported as an unexplained discrepancy without re-tuning. The replication table's row itself (chartist share 0.1674, kurtosis 10.033) was not reproducible from the paper's equations (0.2987 and 1.781 measured).

**The simulated method of moments.** Seventeen moments pooled over set A's 417 names and 6,289 days: the paper's nine (the return autocorrelation, the inverse Hill index, the mean absolute return, the smoothed autocorrelation of absolute returns at lags 1, 5, 10, 25, 50 and 100) plus variance ratios at 20, 60, 120, 250 and 500 days and the autocorrelation of the log price over its 250-day average at lags 20, 60 and 120. The weight matrix came from a joint stock-and-block bootstrap (500 resamples; blocks of 250, 750 and 1,250 days by moment type) with a 10 percent ridge. Three engines: an AR(1) (three free parameters), the Franke-Westerhoff form driven by one GARCH innovation (seven) and the form with two demand noises and no GARCH (eight); differential evolution from at least 20 named starts, then a Nelder-Mead polish; 200 common-random-number paths of 5,000 days per evaluation. **No engine was accepted on either criterion** (the chi-square test or the paper's bootstrap p-value):

| Engine | Fitted | J | df | Chi-square 5 percent | Bootstrap p |
|---|---|---|---|---|---|
| AR(1) | sigma_V 0.01220, sbar 0.00870, h 7.50 d | 80.4 | 14 | 23.7 | 0.000 |
| Franke-Westerhoff, one innovation | sigma_V 0.01145, sbar 0.01082, phi 30.78, chi 0.221, alpha_0 minus 0.062, alpha_n 8.313, alpha_p 8.409 | 29.2 | 10 | 18.3 | 0.005 |
| Franke-Westerhoff, two noises | sigma_V 0.01171, sigma_f 0.874, sigma_c 0.596, phi 15.59, chi 2.879 | 110.3 | 9 | 16.9 | 0.000 |

The rejection is driven by the volatility block (the paper's nine moments missed by 2.1 to 7.3 bootstrap standard deviations), not by the persistence block (matched within 2.0). The best-fitting Franke-Westerhoff engine has an essentially inert switching mechanism reached from the opposite direction to v2's (a bistable herding lock, alpha_n = 8.31, chartist share 0.043, fundamentalist share above 0.99 on 95.7 percent of days) and, fitted freely on the 2000 to 2016 training window, turns itself into an AR(1) (chartist share 0.0004, 100 percent of days locked). Sub-period fits gave half-lives of 13.1, 8.9, 9.2, 7.5 and 5.2 days across windows; a first reading that two sub-periods were "not rejected" was withdrawn once the bootstrap yardstick was shown to move with the window length.

**The engine decision.** The pre-registered rule was asymmetric: a Franke-Westerhoff engine had to be accepted and to beat the AR(1) out of sample by more than one bootstrap standard deviation in order to displace it. Held out (fitted on 2000 to 2016, predicting 2017 to 2024): the mean absolute residual over the eight persistence moments was 1.512 [1.335, 1.689] for the AR(1), 1.510 and 1.488 for the two Franke-Westerhoff engines; neither beat the AR(1). **The AR(1) with a GJR-GARCH-t innovation was adopted; no threshold moved.** The inherited flat-bias defect closed on the new engine: E[x] = minus 0.00013 [minus 0.00087, +0.00064] with jumps and minus 0.00029 without (1,000 flat paths), because the AR(1) has no asymmetry where the Franke-Westerhoff misalignment term was even in x and the herding lock was not.

![Figure 7](figures/F07_phase2_engines.png)

*Figure 7. (a) The SMM distance J of each candidate engine to the 17 panel moments, with the chi-square critical value marked on each bar: none is accepted. (b) The held-out distance on the persistence moments with its Monte Carlo interval: no Franke-Westerhoff engine beats the AR(1). 417 stocks, 2000 to 2024; 20 common-random-number replicates at 417 paths x 2,012 days for the held-out window.*

**The half-life estimator table** (pure AR(1), 200 seeds per cell): the naive ACF(1) half-life at T = 200 reads 18 to 30 days whatever the truth between 30 and 600 days (the review's estimator artefact reproduced exactly); the median-unbiased estimator at T = 200 is censored at its grid top on 18 to 48 percent of paths; at T = 2,000 and 5,000 the correction works. Rule adopted: quote the analytic half-life from the AR coefficient; report the median-unbiased estimate only at T of at least 2,000; at T = 200 report the naive value as "what a 200-day window shows". At the fitted 7.5 days the naive T = 200 median is 6.59 days.

![Figure 8](figures/F29_half_life_estimator_bias.png)

*Figure 8. The bias of the naive half-life estimator on a pure Gaussian AR(1). (a) The median naive estimate against the true half-life for four window lengths, with interquartile bands; at T = 200 the estimate reads 18 to 30 days whatever the truth between 30 and 600 days. (b) The share of paths whose estimate clears 60 days, the v2 item-9 criterion. 200 seeds per cell; 7 true half-lives x 4 window lengths.*

**The persistence sweep** on AR(1) engines with h in {5, 7.5, 10, 15, 30, 60, 120, 250, 500} days, either at a matched stationary sd of x or at a matched innovation scale; 200 seeds per cell for the oracle-switch statistics, 100 for the checklist and 50 for the surrogate (matched-sd arm). At the fitted level the mandate oracle switches its target 2 to 3 times per 200-day run in flat, crash and bull trap (69 to 77 percent of runs with at least two switches), which **reversed the plan's expectation that a fitted persistence would give at most one decision per run**; sustained bull is the exception (median 1, share 0.40). The cost: coverage at theta 0.05 fell to 0.13 in flat and 0.03 in sustained bull; the bull-trap rejection rate rose to 0.94 because its validity band had been calibrated against the old x moves (Phase 4's problem). The checklist passed 4 to 8 of 20 across the sweep; the level-free calm surrogate at the fitted level read 0.350 [0.231, 0.459] against a Kalman bound of 0.245.

![Figure 9](figures/F28_persistence_sweep.png)

*Figure 9. The persistence sweep at a matched stationary sd of x: (a) the share of runs in which the mandate oracle switches its target at least twice, per scenario, against the half-life (Wilson 95 percent bands), with the fitted 7.5 days and the v2 150 days marked; (b) the share of days resolvable at theta 0.05. 200 seeds per scenario and level. The fitted half-life gives two to three decisions per run where the v2 value gave at most one.*

**Post-review checks.** The benchmark still discriminated: the oracle beat the best observables surrogate, which beat the best trivial policy, in every scenario with both gaps positive at 95 percent, though flat lost a third of its spread and sustained bull nearly half, and MCR was undefined on 4 percent of flat and 10 percent of sustained-bull runs (a Phase 7 question). The surrogate was shown to be unbiased: on the bound's own Gaussian model it measured 0.241 [0.214, 0.268] against an analytic 0.245, so the generator's higher 0.339 was a real channel (events, jumps, the GJR innovation and the sentiment feedback), worth about +0.10.

### 9.3 Parameters at the hand-over

| Entry | v2 | In force after Phase 2 | Label | Interval, n |
|---|---|---|---|---|
| Engine | Franke-Westerhoff fallback | AR(1) with a GJR-GARCH-t innovation | FIT decision | 417 stocks |
| Price scale | 100 | 1.0 (the legacy engines keep 100 behind their names so that the v2 numbers stay reproducible) | LIT bug fix | joint coverage 10.0 percent [6.6, 14.9] against 10.1 |
| Half-life h | 150 d (pull rate) | 7.498 d | FIT (17 moments) | [3.81, 23.61]; 30 refits |
| sigma_V | 0.006 | 0.01220 | FIT, conditional on the engine | [0.01066, 0.01419] |
| sbar | 0.017 | 0.00870 recorded, not applied (Phase 3 owns it) | FIT recorded | [0.00659, 0.01298] |
| GARCH shape | 0.10 / 0.10 / 0.83, df 5 | held at the per-stock medians inside the SMM; not yet applied (registered as a Phase 3 defect) | FIT | 417 |
| s_x target | none | 0.02498 (corrected from 0.1286) | FIT target | |

The leakage audit on the handed-over state: level-free calm R-squared 0.339 [0.208, 0.434] (Phase 1: 0.086), full-field calm 0.346 (Phase 1: 0.823), full-field all phases 0.731 (0.928), L2b selectivity +15.4 points (+11.7): **the fitted engine traded field leakage for price leakage**, which Phase 3's calm-trained re-reading later put in proportion. Checklist: item 20 turned to pass (calm sigma 1.77 percent) and item 6 turned to fail (a negative leverage correlation in 57 percent) as sigma_V doubled. Freeze: 21 files. Test suite: 121 passed, 1 skipped, 7 expected failures, 0 failed. Compute: local only; one full SMM cell 1.5 to 3 hours, the 15 pre-registered cells 25 to 35 hours serially; no paid API call.

### 9.4 Results that contradicted expectations

Three inputs were wrong and corrected (the plan's replication target, Phase 1's s_x, the report's first sub-period reading). No engine of any class fits the panel's 17 moments. The best Franke-Westerhoff engine is inert from the other direction and collapses to an AR(1) on the training window. The plan's expectation of a one-shot decision was reversed. The bull-trap rejection rate jumped from 0.06 to 0.94. The pre-registered simulation-noise rule (every persistence moment's simulation sd at most 0.30 of the bootstrap sd) had an empty acceptance set (it would need about 960 paths per evaluation) and was re-scoped in the addendum before the runs.

---

## 10. Phase 3: volatility

### 10.1 Goal

Fit the whole volatility block: confirm and adopt the GJR-GARCH-t shape, fit the jump rate and size, fit the phase variance multipliers, decide how the regime enters the variance, build an implied-volatility construction that is neither a phase marker nor a look-ahead, close the small inconsistencies, and decide, pre-registered, whether Phase 2's SMM is re-run on the new block.

### 10.2 Work carried out

**Three corrections in the addendum, each before the run it governed.** (1) The registered "pre-event calm" window for run-ups (120 days ending at the 504-day minimum) measured a post-crash trough, 2.74 times the stock's unconditional level, so every run-up multiplier came out below 1 (mania 0.46, blow-off 0.70, post-top 0.42); the reference was corrected to the stock's unconditional level and both variants published. (2) The pooled population of 30-percent drawdowns is dominated by slow multi-year declines (rise time 118 days [107, 131]) against a scripted crash that completes inside 110 trading days; a fast-crash subpopulation (peak to trough within 126 days) was registered as the adoption-governing secondary. (3) Both registered jump-adoption paths failed, and the adoption was corrected to the primary fit's triple with recovery-informed intervals.

**The GJR-GARCH-t shape confirmed and adopted**: alpha 0.027 [0.025, 0.030], gamma 0.058 [0.055, 0.061], beta 0.932 [0.928, 0.935]; the tail degrees of freedom set jointly with the jumps (below). Sensitivity sets for later phases were built on quantiles of (alpha, gamma, degrees of freedom, persistence) with beta derived, because the raw per-parameter 75th percentiles give a persistence of 1.028. Three "volatility scale" numbers were named: 0.0218 [0.0210, 0.0225], the panel's per-stock median unconditional daily return sd; 0.00870, Phase 2's fitted innovation scale under an objective the model fails; 0.017, v2's tuned calm scale. Adopted: the generator's free-running unconditional daily return sd is set equal to 0.0218 by the exact variance identity sbar squared = (s_A squared minus sigma_V squared)(1 + rho) / 2 minus lambda sigma_J squared, imposed as a constraint inside the engine refit.

![Figure 10](figures/F08_garch_fits_by_period.png)

*Figure 10. Per-stock GJR-GARCH-t fits on set A by period: the news coefficient alpha, the leverage term gamma, the memory beta, the tail degrees of freedom and the persistence, as box plots with quartiles and 1.5 IQR whiskers. 417 stocks (416 in two sub-periods). The full-sample medians are the parameters in force.*

**Jumps.** Detection on 2,622,096 set-A stock-days: at an absolute standardised residual above 4 the observed share is 0.00440 per day while each stock's own fitted t tail predicts 0.00366; the excess is negative at moderate thresholds and positive and growing from 3.5 upwards (+0.00074 [+0.00066, +0.00082] at 4). Announcement clustering: 0.0134 in filing windows against 0.0030 outside. A mixture fit on nine pooled moments gave degrees of freedom 6.65 [6.48, 6.83], lambda 0.00058 [0.00046, 0.00072] jumps per day and sigma_J 0.230 [0.223, 0.241], with J = 790 (the mixture as a whole decisively rejected, for two structural reasons: cross-sectional heterogeneity of the tail and an announcement elevation that a total-rate-preserving split cannot deliver). The recovery grid (6 cells x 5 replicates) recovered the degrees of freedom to plus or minus 2.4 percent but lambda only to plus or minus 59 percent and sigma_J to plus or minus 28 percent, failing the 0.20 usability rule; the registered fallback (degrees of freedom pinned at 4.86) collapsed to a corner (lambda about 3e-14). Three independent reads of lambda agreed (0.00058, 0.00074, 0.00074, about 0.15 jumps a year) and a size decomposition put sigma_J near 0.086. Adopted with widened intervals: degrees of freedom 6.650 (the diffusive tail net of jumps; the quasi-likelihood 4.86 is the total tail and is recorded beside), lambda 0.000583 [0.00046, 0.00082], sigma_J 0.230 [0.086, 0.241], the label "weakly identified" travelling with both. The v2 jumps (0.010 per day at a 3 percent size) were superseded: seventeen times the rate at an eighth of the size.

![Figure 11](figures/F30_jumps_and_iv_transitions.png)

*Figure 11. (a) Jump detection on the panel: the observed share of stock-days above each threshold on the absolute standardised residual against the share each stock's fitted t tail predicts (log scale), with the excess at 4 and its interval; 417 stocks, 2,622,096 stock-days, 1,000-resample stock bootstrap. (b) The implied-volatility construction at the three crash transitions: the mean z-score of the one-day change in log implied volatility under the v2 construction (50 crash seeds) and under the v2.1 construction (200 crash seeds), with the derived tolerances; the v2 construction jumped by z = 7.7 at the panic onset, the v2.1 construction reads z = 0.12.*

**Phase multipliers** from set A, 2000 to 2024: 1,789 drawdowns of at least 30 percent over 417 stocks (median depth minus 45 percent) and 3,202 run-ups over 398 stocks (3,125 over 394 with a usable calm reference). Windows: panic = the 20 days ending at the worst trailing-20-day return, deterioration = the 40 days before that, stabilisation = 60 days from the trough; mania = the 40 days ending 20 days before the run-up's peak-momentum day (the day within its last 126 days with the largest trailing 20-day return), blow-off = the 20 days ending on that day, post-top = 60 days after the top. Medians of the total-return variance ratio to the stock's unconditional level, with 1,000-resample stock-bootstrap intervals:

| Phase | Multiplier adopted | Interquartile range | As first registered (trough reference) | Episodes / stocks (n) |
|---|---|---|---|---|
| Deterioration | 1.37 [1.31, 1.44] | 0.80 to 2.67 | 1.16 | 1,592 / 412 |
| Panic | 7.45 [6.86, 8.13] | 3.17 to 17.38 | 5.43 | 1,592 / 412 |
| Stabilisation | 3.11 [2.96, 3.34] | 1.60 to 6.22 | 2.39 | 1,571 / 412 |
| Mania | 1.18 [1.12, 1.21] | 0.69 to 2.32 | 0.46 | 3,125 / 394 |
| Blow-off | 1.65 [1.58, 1.71] | 0.96 to 3.41 | 0.70 | 3,125 / 394 |
| Post-top | 1.16 [1.13, 1.20] | 0.77 to 1.88 | 0.42 | 3,122 / 394 |

v2 had 1.5 / 5 / 1.5 / 1.5 / 2 / 3 without a source. Also measured: the fast-crash subpopulation's rise time from onset to the realised-volatility peak, 30 days [29, 35] (n = 531 / 276), against the pooled 118 days; the decay half-life 9 days [9, 10]; market-wide windows (the fourth quarter of 2008 at 4.58 and the first quarter of 2020 at 9.20 times the pre-window level). Every depth and multiplier is survivor-understated.

**The closed loop and the mechanism.** Because sigma_V is not scaled by phase, reproducing a total-return ratio of 7.45 in panic takes a multiplier of 16.17 on the x innovation (a first-order mapping said 12.7; the GARCH feedback needs the rest); three closed-loop iterations at 60 seeds, verified at 200, gave x-innovation multipliers of 1.35 / 16.17 / 5.63 / 1.35 / 0.35 with realised ratios of 1.34 / 7.54 / 3.12 / 1.19 for deterioration, panic, stabilisation and mania, each inside its target interval. Two structural shortfalls were found and handed to Phase 4: **the blow-off multiplier had been dead code since v2** (its label was assigned after the fact by a relabelling step, so no multiplier ever reached the variance; the knob diverged to 9.3 while the realised ratio stayed near 1.1), and **post-top is drift-dominated** (the scripted reversal leg floors its realised ratio near 1.59 whatever the multiplier). Three ways for the regime to enter the variance were compared on 200 crash seeds (whole-variance scaling as in v2; an omega ramp; a two-regime switch): none brought the rise time inside either empirical interval (75.5, 103 and 80 days against 30 [29, 35]), because the onset falls inside a scripted deterioration whose remaining length plus the panic build-up is 50 to 90 days by the schedule template; the rise criterion is decided by Phase 4's event template, not by the variance mechanism. Whole-variance scaling stays as the documented shortfall. This stage ran on a remote kernel after the kernel reproduced the committed 51-moment reference vector to a worst relative difference of 6.4e-16.

![Figure 12](figures/F09_event_multipliers.png)

*Figure 12. The panel's variance multiplier per event phase (blue dot with its 95 percent interval) against what the generator realised after the closed loop (diamonds; green inside the interval, red outside). Blow-off (dead code) and post-top (drift-dominated) are the two red points; both went to Phase 4. The panel n per phase is under each label; 200 generator seeds per phase (199 for mania and blow-off; 20 bull-trap paths reached post-top).*

**Implied volatility.** Panel side: five single-stock volatility indices against the same past-only GJR filter, 17,570 pooled days 2011 to 2024; by leave-one-name-out cross-validation a constant premium won (log(1 + pi) = minus 0.0224, a premium of about minus 2 percent), and the residual is a strong AR(1) (rho 0.926, innovation sd 0.083). Generator side: implied volatility = the square root of 252 times a past-only GJR forecast on observed returns, times (1 + pi), times the exponential of an AR(1) noise from a new day-indexed random stream; the stress trigger, the whole-path quantile, the sigma_V add-on, a silent factor of 1.19 left over from the Franke-Westerhoff weight plumbing (found in verification) and the floor of 12 were all removed. Audits on 200 crash seeds: the mean z of the change in implied volatility at the panic onset is +0.12 (v2: about 7); the onset-detection AUC of the implied-volatility change is 0.576 against the filter's own 0.683 (a difference of minus 0.107 against a permutation null of +0.032); the rendered implied volatility adds nothing to scenario classification (53.7 percent with and without it). Tolerances of 2.70 / 2.28 / 1.88 were derived from the reference distribution and written into the parameter file; the continuity test became a hard, passing test.

**The engine refit** on the new block (the fitted shape, the fitted jumps, sbar eliminated by the identity, sigma_V and h free): sigma_V 0.01457 [0.01275, 0.01527], h 22.38 days [18.75, 32.64], sbar 0.01509 by the identity, J 119.3 on 15 (not accepted; no engine of this class is). Phase 2's 7.50 days lies outside the new interval and the new 22.38 lies inside Phase 2's [3.81, 23.61]; the block carries the half-life from 7.50 to 16.96 days and the identity constraint from 16.96 to 22.38. Realised sd of x 0.068 (handed over 0.042); the bull-trap rejection rate fell from 0.94 to 0.13.

**Post-review.** (a) The audit's published calm R-squared is cross-phase-trained (the model is fitted on all rows and masked by phase afterwards), which is why it read minus 0.58 after Phase 3; **calm-trained** (fitted and scored on calm rows only) the level-free channel is +0.349 [0.322, 0.374] (Phase 2: 0.421) and the full-field one +0.550, so the report's headline "the calm price channel is gone" was withdrawn: the channel narrowed modestly and sits about +0.19 above the Gaussian bound, of which about +0.15 is events and sentiment on calm rows. (b) A decomposition on calm-only worlds located the volatility channel: the exact Gaussian process reads 0.145 (bound 0.163), the GJR innovation adds nothing, the jump block adds +0.05. (c) The level anchoring was reported as double-counting the panel's crises (+30.5 percent realised return sd over the scenario mix), a finding Phase 4 later withdrew: the comparison had set a per-stock median against a pooled mean, and what survives of it is that the deployed deterioration phase is too loud. (d) The jump-size span costs about +0.018 of R-squared from the interval floor to the adopted point; the adopted 0.230 is the conservative end. Six checkable errors were corrected in place (a miscopied lambda interval, a self-contradictory compute header, run-up counts, the n of the post-top floor, a stale label, a stale registry number).

### 10.3 Parameters at the hand-over

| Entry | v2 or Phase 2 | In force after Phase 3 | Label | Interval, n |
|---|---|---|---|---|
| GJR alpha, gamma, beta | 0.10 / 0.10 / 0.83 | 0.027 / 0.058 / 0.932 | FIT | 417 stocks |
| Innovation degrees of freedom | 5 | 6.65 (diffusive, net of jumps) | FIT conditional on the jumps | [6.48, 6.83] |
| sbar | 0.017 | 0.01509 | FIT by the variance identity | [0.01342, 0.01678] |
| Jump rate lambda | 0.010 / day | 0.000583 / day, mean zero | FIT, weakly identified | [0.00046, 0.00082]; 2.6 million stock-days |
| Jump size sigma_J | 0.03 | 0.230 (log units) | FIT, weakly identified | [0.086, 0.241] |
| Phase multipliers (total-return targets) | 1.5 / 5 / 1.5 / 1.5 / 2 / 3 | 1.37 / 7.45 / 3.11 / 1.18 / 1.65 / 1.16; sustained bull 1.0 | FIT; sustained bull DESIGN | 1,592 / 3,125 episodes |
| x-innovation multipliers in force | | 1.35 / 16.17 / 5.63 / 1.35 / (blow-off = mania, inert) / 0.35 | closed-loop FIT with two documented shortfalls | 200 seeds |
| Variance mechanism | whole variance | whole variance | documented shortfall | |
| Implied volatility | 21-day forecast, premium 0.20, stress 0.35, floor 12 | past-only filter, premium minus 0.0224, AR(1) noise (0.926, 0.083), no floor, tolerances 2.70 / 2.28 / 1.88 | FIT (five single-stock indices) | 17,570 days |
| sigma_V | 0.01220 | 0.01457 | FIT conditional on the engine and the block | [0.01275, 0.01527] |
| Half-life h | 7.498 d | 22.38 d | FIT | [18.75, 32.64] |

Freeze: 23 files. Path hashes: 2,648 non-analyst hidden-column changes against Phase 2 (the whole environment moved, as it must). Test suite: 127 passed, 1 skipped, 5 expected failures, 0 failed; the registry after Phase 3 holds three entries, the sustained-bull selection (Phase 4) and the two Phase 6 leakage gates; the two permanent v1 baselines are expected failures kept outside the registry. Checklist: 5 of 20 pass, the same set as after Phase 2 (items 1, 5, 12, 15, 20), while rows moved (implied-volatility levels back in band: calm 32.1, panic 67.4 percent; the clustering share fell from 52 to 42 percent because the fitted alpha of 0.027 has less short-window power than the v2 value of 0.10; the topped share stayed at the 8 percent it had fallen to in Phase 2, from 62 percent after Phase 1, because the tuned hazard was stale under the new x dynamics, Phase 4's problem). Compute: local except the mechanism arms on a remote kernel; no paid API call.

---

## 11. Phase 4: events, schedule, controls and the calendar

### 11.1 Goal and the defects it inherited

Rebuild the event block from the data panel: the crash and bubble episode tables, the schedule ranges drawn from them, the bubble hazard, the mania drift, the sustained-bull control definition, the event-dynamics formulation, the orderings and the day-index rendering. The phase arrived with five measured defects: the schedule template owns the crash rise time (panel 30 days [29, 35] against at least 75.5 in the generator under any variance mechanism); the tuned hazard was stale (topped share 8 percent against the 40 to 60 target); the blow-off multiplier was dead code; post-top was drift-dominated (floor 1.59 against a target of 1.16); and the sustained-bull selection defect (rejection 32.9 percent, coverage 0.044, 10 percent of runs with no resolvable step) still sat in the registry. Team decisions in force: the single-stock panel as the primary population, "Day-N" kept, mechanism C for the start price, the sustained-bull control deliberately left open, the event-dynamics decision not taken. The pre-registration's own power tool raised the event-dynamics experiment from 200 to 500 seeds and fixed the label-permutation null to permute seed labels rather than day labels (a day-level null would have called almost any classifier a leak).

### 11.2 Work carried out

**The level.** The registered rule (adopt a fitted calm multiplier if 1.0 lies outside its interval) gave m_calm = 1.0102 [0.9791, 1.0561] over 1,592 episodes and failed, so the level as handed over stood. On the way the addendum found that Phase 3's "double-count" compared a per-stock median of rolling realised variance with a pooled mean: the ratio of mean to median realised variance across 417 stocks is 1.354, which is the 1.356 Phase 3 had read as a defect. With one estimator on both sides the panel's calm daily sd is 0.021672 [0.020860, 0.022439] against the generator's 0.022054 [0.021652, 0.022482] at 500 seeds per scenario: **no calm level defect**. The deterioration phase, however, reversed sign once the fitted lengths were deployed: 2.632 [2.382, 2.938] times its own calm level against the panel's 1.618 [1.506, 1.746], because a fitted deterioration length with a median of 8 days (v2: 27) compresses the same fundamental decline into a third of the days.

**The episode tables** (set A, 417 names, 2000 to 2024): 3,078 drawdowns of at least 20 percent and 1,789 of at least 30 percent; 642 fast 30-percent drawdowns (peak to trough within 126 days) over 313 stocks; 1,975 Pagan and Sossounov bear phases; 3,202 run-ups of at least 100 percent within 504 days over 398 stocks; 12 and 6 index-level episodes (too few to use). The fast-crash quantities the schedule draws from:

| Quantity | P10 | P50 | P90 | v2 drew |
|---|---|---|---|---|
| Deterioration length (days) | 3 | 8 [7, 9] | 25.9 | uniform 15 to 40 |
| Panic length (days) | 15 | 39 [35, 43] | 100.9 | uniform 15 to 70 |
| Depth (trough over peak minus 1) | minus 0.538 | minus 0.369 | minus 0.312 | delta fixed at 0.70 |
| Front-loading | 0.088 | 0.272 | 0.574 | fixed 0.50 |
| Recovery at 60 days | 0.236 | 0.569 | 1.037 | uniform between delta and 1 |

Also: the run-ups' topped share (a 40 percent drawdown within 200 days of the top) 0.110 [0.0966, 0.1245] (n = 3,201 / 398); a corrected bubble-side calm reference giving blow-off over mania 1.289 [1.215, 1.371] and post-top over mania 0.6225 [0.599, 0.648]; a log-periodic power-law fit on 3,125 run-ups with a median exponent of 0.926 and a stable share of only 0.329, which failed the registered trigger for a super-exponential mania.

**The schedule and the rise time.** "Drawn from the empirical P10 to P90" was implemented as inverse-CDF sampling from a 33-point quantile grid, not as a uniform (a uniform on [3, 25.9] has median 14.4 where the panel says 8). The registered criterion, that the generator's median onset-to-volatility-peak rise time overlap the panel's [29, 35] days, was **not met and not relaxed**: 70.0 [65, 74] under the v2 uniforms, 65.0 under the fitted interval with a uniform shape, 58.0 [52, 64] under the empirical shape (500 seeds each). What binds is the lag between the running price peak and the scripted event (correlation 0.684 with the rise), not the deterioration length: the peak falls a median of 38 days before the event, so the lever is the setup length. A setup sweep showed that the criterion can be met at a 13-day median setup (37.0 [34, 41]) with the day-only classifier still acceptable, but a 13-day setup leaves almost no pre-event baseline, so it was measured and not adopted.

![Figure 13](figures/F13_crash_depth_duration.png)

*Figure 13. Depth against peak-to-trough duration for 1,789 real drawdown episodes of at least 30 percent in 417 stocks, with the generator's crashes under the v2 schedule (n 364) and under the v2.1 empirical schedule (n 380); the box is the panel's P10 to P90 range on both quantities. The generator's crashes are deeper than the panel's median, and the depth floor near minus 0.46 was traced to the fundamental decline.*

**The hazard.** The slope b = 5.419 was fitted through the published crash probabilities of Greenwood, Shleifer and You after 50, 100 and 150 percent run-ups (20 / 53 / 80 percent) and h0 solved from a hazard-off pilot; of four mappings only "no horizon scaling" put the topped share inside the panel's band (0.108 [0.081, 0.135] against [0.0966, 0.1245]; 500 bull-trap seeds). It was adopted, then **its adoption was withdrawn**: it had been measured before the new event file existed, under the v2 post-top leg, and on the deployed state the topped share is 0.008 [0.002, 0.016]. A window-matched comparison showed why: only 0.9 percent of generated topped paths have 120 days left after the top (the median is 29), while the panel's 11 percent topped share is reached only with 150 to 201 post-top days available; on comparable windows the two agree (0.025 against 0.029 with 0 to 50 days). The criterion is horizon-dominated and not evaluable on a 200-day scenario. The 40 to 60 percent topped band and the P/V 1.6 to 2.5 band were retired as targets; the peak P/V is reported as an outcome (median 1.49).

**The mania drift.** The panel's run-ups decelerate: the ratio of the last third's log gain to the first third's is 0.665 over 2,937 run-ups and, with the end not selected on price, 0.342 [0.318, 0.368] over 3,186 run-ups. The fitted super-exponential parameter is therefore zero; it was reported and not applied, because a zero drift makes the bull-trap validity criterion reject 96.3 percent of draws. The v2 uniform on 0.02 to 0.04 stays, labelled TESTED, NOT ADOPTED.

**The sustained-bull control.** Four definitions at 500 seeds with rejection off: A (the same mispricing process as flat, no band on x, validity on V only), B (a band on V, mania driver off), C (the anchored x of v2) and D (rendered-matched). C rejects 35.8 percent of draws and its accepted paths are quieter with lower implied volatility (Kolmogorov-Smirnov distances 0.474 and 0.434 against 0.081 and 0.187 for A); A, B and D are indistinguishable. The registered equivalence bound was undecidable at these rejection counts (the null floor at 419 against 81 paths is about 0.20 against a bound of 0.10; roughly 4,000 seeds would be needed). No definition could be adopted on the audit's evidence under the pre-registration; the team chose **definition A**: the two selection weaknesses were closed and both registered expected failures were removed. Re-measured at 800 seeds: C rejection 0.330, distance on the daily sd 0.44 against its own null floor of 0.10; A rejection 0.150, distance 0.11 against a floor of 0.14.

**Event dynamics** (remote kernel; 1,000 crash and 1,000 bull seeds per formulation). The coverage of the panel's depth-by-duration box: formulation A (the v2 error-correction gain) 0.474 to 0.562 across gains 0.02 to 0.25; B (a shifted target) 0.521; C (scripted, no feedback) 0.462; D (an unscripted regime switch) 0.323. **No formulation reaches the registered 0.70, which stops the decision for the team.** The addendum then showed that the threshold was wrong by construction: a P10-to-P90 box on two quantities captures about 0.64 of its own population, and the panel's self-coverage is 0.643 [0.607, 0.679], so the rule asked the generator to beat the panel by 6 points; no corrected threshold was set. A re-test on the stored output refuted two of the report's own arguments about it (the noise-floor claim and the root-cause explanation) and showed that the "script share" statistic is not monotone in scriptedness (the fully scripted C scores below the unscripted D), so it cannot rank formulations. Formulation A at a panic gain of 0.10 stays as INCUMBENT, referred to the team.

![Figure 14](figures/F14_event_dynamics_stop.png)

*Figure 14. (a) The share of generated crashes inside the panel's depth-by-duration box for each event-dynamics formulation, against the panel's own coverage of 0.64 (the registered 0.70 was above it). (b) The median share of the event's move that the script writes directly. 1,000 crash seeds per formulation; 2,000-resample bootstrap clustered by seed.*

**The calendar.** Orderings (setup-first, event-first, phase-free) and renderings ("Day-N", none, a date) were tested against the rule that day-only phase accuracy must not exceed a seed-permutation null by more than one point (200 seeds, 200 permutations): the setup-first and event-first orderings and every rendering were acceptable (the phase-free ordering is uninformative by construction, its accuracy and its null both 1.0), "Day-N" the marginal one (+0.22 points on bull trap, inside the margin); the rendering stands and an ordering factor was added to the arm registry. The earnings-quarter clock: with v2's quarter grid fixed across seeds, the days-since-announcement field predicted which third of the quarter a day was in with accuracy 0.8728 against a null of 0.3627; randomising the grid per seed removed 93 percent of the excess (0.3958 against 0.3625); adopted. The 3.3-point residual was resolved by Phase 5 as an edge effect.

**Labels, the post-top leg, blow-off, the crash's value path, multi-asset.** The blow-off label was made real-time (a mania drift above a fitted threshold of 0.00984 [0.00590, 0.02080]; the label now reaches 100 percent of paths and the driver). The post-top leg became a decay with a half-life re-fitted at 1,500 seeds per arm under fitted post-top ranges: 40 days realises 0.6216 against the panel's 0.6225 [0.599, 0.648] (a first pass at 400 seeds would have adopted 10 days, caught before writing). The blow-off multiplier was calibrated in a closed loop from 1.345 to 2.0764, realising 1.3136 [1.2139, 1.4119] against the panel's 1.2895. The crash's value decline: on 106 fast-crash episodes with a falling filings-based value proxy, the median share of the total decline that falls before the price onset is 0.000, in the panic 0.024, and after the trough 0.891; v2 put all of it in deterioration, so the direction is REJECTED while the magnitude is not identified; the v2 shape ships flagged TESTED, REJECTED. The post-top drop and length shipped in Phase 4's own first file as v2 design values (uniform 0.30 to 0.50; 10 to 30 days) where the panel holds P10 / P50 / P90 of 0.061 / 0.169 / 0.414 and 8 / 60 / 187 days; both were replaced by fitted grids. Multi-asset: the common-factor loading was fitted at 0.236 (417 names), but a per-asset event mechanism moved the co-drawdown share by 0.0003, so it is implemented and NOT ADOPTED; the first numbers for this stage came from a console and the cited file had never been written, so they were re-run.

**The depth floor.** A centred depth draw (the fitted depth grid centred on the arm's delta) restored 73 percent of the delta effect that the fitted schedule had made structurally inert (spread 0.0000 to minus 0.0814 between delta 0.55 and 0.85). A closed loop on the depth saturates near minus 0.451 whatever the gain: **the generator cannot produce a panel-median crash** (minus 0.369), because the floor is the stipulated fundamental decline (uniform on 10 to 30 percent) plus the panic-phase mispricing excursion; a depth gain is NOT ADOPTED and the fundamental decline is named as the floor's cause.

**The audits.** The event redesign did not narrow the calm level-free channel (calm-trained +0.3493 to +0.3594, then +0.3213 [0.2935, 0.3478] after the control decision). The L2b clock's selectivity fell from 12.7 to 10.7 points before the control decision, from the wrong side (only the price-only baseline rose), and to 10.4 after it, when the field channel itself fell (full-field accuracy 0.783 to 0.760; the worst-group selectivity R-squared 0.688 to 0.482). The control decision repaired the sustained-bull scenario's usability: coverage at theta 0.05 from 0.044 to 0.374, runs with no resolvable step from 10 percent to 0. Two long audits had been run before the decision was adopted and had to be redone.

### 11.3 Parameters at the hand-over

| Entry | v2 | Deployed | Label | Data, n | Status |
|---|---|---|---|---|---|
| Deterioration, panic lengths | U(15, 40), U(15, 70) d | 33-point grids [3.0, 25.9] and [15.0, 100.9] d | FIT | 642 fast crashes / 313 stocks | ADOPTED |
| Front-loading, depth, recovery | 0.5; delta fixed; U(delta, 1) | grids [0.088, 0.574]; [minus 0.538, minus 0.312] centred on the arm's delta; [0.236, 1.037] | FIT (+ DESIGN centring) | same | ADOPTED |
| Post-top drop, length | U(0.30, 0.50); U(10, 30) d | grids [0.061, 0.414]; [8, 187] d | FIT | 3,201 run-ups / 398 | ADOPTED |
| Fundamental decline, mania drift, bull drift, setup fraction | U(0.10, 0.30); U(0.02, 0.04); U(0.0015, 0.0025); U(0.25, 0.55) | unchanged | DESIGN (mania drift: TESTED, NOT ADOPTED, fitted value 0 recorded) | | |
| Hazard | h0 3e-4, b 6.0 | h0 6.712e-4, b 5.419, drift cap 0.012 | FIT / CAL | 3 published points; 500 seeds | IN FORCE, ADOPTION WITHDRAWN |
| Blow-off label; multiplier | after the fact; dead | dynamic, threshold 0.00984; 2.0764 (realised 1.3136) | FIT; CAL | 3,202 run-ups; 1,200 seeds | ADOPTED |
| Post-top leg | linear | decay, half-life 40 d | CAL to the fitted 0.6225 | 1,500 seeds per arm | ADOPTED |
| Crash value drift | all in deterioration | unchanged | TESTED, REJECTED (direction) | 106 episodes / 96 stocks | |
| Sustained-bull control | C (anchored x) | A (no band on x) | DESIGN by team decision | 500 seeds per definition; 800 deployed | ADOPTED |
| Event dynamics | A, gain 0.10 | unchanged | INCUMBENT (referred to the team) | 2,000 seeds x 7 arms | |
| Calendar | "Day-N", fixed quarter grid | "Day-N"; quarter grid randomised per seed; three renderings and an ordering factor behind switches | DESIGN; randomisation MEASURED | 200 seeds | ADOPTED |
| Multi-asset | shared event | per-asset events off; loading 0.236 recorded | TESTED, NOT ADOPTED | 417 names; 60 seeds | |

The freeze manifest was rewritten five times in the phase, always 25 files. Checklist at 200 seeds: 5 pass / 10 fail / 5 not applicable. Tests: the plan's seven tests plus provenance, the blow-off label reaching the driver, post-top no longer drift-dominated, the realised top day, v2 bit-identity of the schedule, the grid sampler reproducing the panel's shape, three verification guards, the quarter-phase switch, and the status vocabulary enforced by the loader after two undeclared statuses were found; a report-table test checks the parameter table against the parameter file. The whole suite at close-out: 148 passed, 1 skipped, 4 expected failures, 0 failed across 22 files (nine of which had never been run before this phase, six of them failing when first run). Compute: a laptop, plus one remote kernel for the event-dynamics experiment (7 arms x 2,000 seeds in 385 seconds after the reference-row guard reproduced to a worst relative difference of 0.0); no LLM cost.

### 11.4 Results that contradicted expectations (21 recorded)

The registered level hypothesis was refuted and its corrected rule withdrawn unrun. The uniform sampler was a stipulated shape hiding in a fitted interval. The event-dynamics coverage threshold was unmeetable by any generator. The control's equivalence bound was undecidable. The topped-share criterion was horizon-dominated, and its adoption withdrawn. Three tools had measured a state that did not exist, and two adopted parameters were withdrawn. The 400-seed half-life search would have adopted noise. The first quarter-clock test was degenerate. A cited evidence file had never been written. Six failing tests were unseen because nine files had never been run. Three of the report's own recommendations were refuted by their own tests. The crash-depth floor sits outside the event block. Two audits were invalidated by a sequencing error. A pre-registration departure was disclosed: the team authorised acting on the recommendations, the control decision was taken, the event-dynamics decision was not.

---

## 12. Phase 5: observables, the fields the agent reads

### 12.1 Goal

Rebuild what the agent is shown so that the fields stop carrying the hidden state, with every constant fitted on data: the P/E multiple, sentiment, volume, the analyst estimate, plus earnings, losses, announcement lags and dividends. Inherited state: L2b selectivity +10.4 points FAIL; the full field set's calm R-squared 0.233; calm-trained level-free 0.3213 and full 0.4905. The measure of each design is the **add-one selectivity**: the R-squared for x that a field group adds to the level-free base when added, on all rows, with a paired cluster-bootstrap interval; the calm-trained co-statistic is reported beside it; the onset audit (does a non-price field announce a phase transition before the price path's own change scores do, against a 500-shift circular null) is the second gate, with the technical indicators moved to the reference side after the registered reference set proved too narrow (seven of its eleven failures were price functions).

### 12.2 Work carried out

**The multiple.** Trailing P/E across 411 set-A stocks and 61,843 stock-months (2009 to 2024): P10 5.77, P25 9.23, P50 15.12 [14.34, 16.06], P75 24.42, P90 39.98, P99 191.5. The v2 uniform on 14 to 22 covered roughly the 45th to 70th percentile and fails a Kolmogorov-Smirnov test against the cross-section at a distance of 0.319. Quarterly persistence of the log multiple within a stock: 0.8076 [0.7814, 0.8269] over 367 stocks (a daily 0.99661, half-life about 204 days). Two designs, A (a between-stock draw only) and B (a between-stock draw plus a within-stock daily AR(1)), both on the P10 to P90 width; B's add-one selectivity was lower (+0.0114 [+0.0027, +0.0204] against A's +0.0254; paired difference +0.0139 [+0.0014, +0.0256]) and **B was adopted**, though the calm-trained co-statistic pointed the other way (A +0.020, B +0.039) and is recorded.

**Earnings, losses, lags.** From 27,515 filed quarters: the seasonal EPS residual's robust sd is 0.407 (the plain sd is 4,491 because of two scale errors in filings and write-offs), and the log seasonal change's robust sd is 0.334; net of V's own annual sd (0.231) and of the doubling a difference of two draws carries, the EPS noise is **0.171 [0.150, 0.193]** (v2 used 0.10); P(loss quarter) 0.098 with P(loss given loss) 0.425 and P(loss given profit) 0.062 (26,389 quarters); loss sizes on a grid from P5 to P95; the P/E cap set at the P99 of 191.5; "n/m" rendered when trailing EPS is not positive (8.5 percent of stock-quarters in the data, 6.2 percent of rendered days). The announcement lag from 27,242 earnings-release filings: P10 / P50 / P90 = 12 / 19 / 26 trading days (v2: uniform 25 to 35), sampled from a P5 to P95 grid of [10, 30].

**Dividends.** 370 of 417 set-A names pay (0.887); the payout ratio of dividends to earnings has median 0.406 [0.373, 0.444] (v2: 0.35; 10,666 stock-years); the Lintner speed with the target constrained is 0.697 per quarter (dividends unchanged in 57.5 percent of payer quarters; an unconstrained fit is unidentified); cuts of at least 20 percent within four quarters of a fast-crash peak occur in 17.7 percent of episodes against 7.3 percent unconditionally. The process is FIT and ADOPTED; whether the yield is shown was left to the team with its cost measured: showing it adds +0.0382 [+0.0292, +0.0480] of R-squared for x over hiding it.

**The analyst estimate.** No free data can fit the error; the literature anchor is a 45 percent absolute target-price error (Bradshaw, Brown and Huang, 2013; Bilinski, Lyssimachou and Walker, 2013), hence an sd of 0.564. Every design that multiplies V by an error failed the onset audit at the crash's calm-to-deterioration transition whatever the noise (0.300 to 0.600: excess AUC +0.017 to +0.021 against a null of +0.001), because the leak is V's decline itself, not the noise. Design C, the 250-day price average times the error, passed at all six transitions under the non-price rule (and failed the narrow registered rule at one, on the 26 topped paths of that arm's audit). **C is the PROVISIONAL default; C against dropping the field is a Phase 9 question.**

**Sentiment.** The daily news-sentiment index is smoothed at source (a 5 percent geometric depreciation, stated in its publisher's note); deconvolved, the raw series has an AR(1) of 0.349 and a plateau near 0.30. Over 11,589 trading days the standardised market return explains it with a daily rho of 0.403 and a loading of +0.084 per sd; over 57 windows of 200 days, the benchmark's horizon, the medians are rho 0.211 [0.155, 0.256] and +0.111, the values deployed. Tetlock's 8.1 basis points next-day return was not reproduced by this free source (minus 0.64 plus or minus 1.15 bp), so the predictive size stays LIT at 0.0008. A valuation link exists in the monthly data (+0.95 sd per unit log-CAPE deviation, 560 months) and is pro-cyclical and about 3.6 times weaker than v2's 0.6 tanh(2x). Designs: A (returns only), B (A plus the valuation link at full or half strength), C (a weekly field). By the registered rule A's selectivity is minus 0.0007 [minus 0.0012, minus 0.0002] against B-half's +0.0205 and B-full's +0.0813; **A was selected, B carried as sensitivities, the default left to the team.** The v2 bands for item 12 (an autocorrelation of 0.7 to 0.9 and a return correlation of 0.25 to 0.55) had been stipulated; the data give 0.200 and +0.006 daily.

**Volume.** On 417 stocks with log volume detrended by a trailing 252-day mean: autocorrelation 0.526 [0.522, 0.529], loading 0.203 on the absolute standardised return, residual sd 0.347. v2 had 0.65, 0.25 and a loading of 1.2 on absolute x with no source. Greenwood, Shleifer and You's premise of elevated turnover in run-ups was not reproduced (ratio 0.985 [0.969, 0.999], below 1). Design A (no run-up term) adopted; the volume channel collapsed from +0.220 to +0.0042 [+0.0026, +0.0059].

**The audits.** A baseline ablation on the stored Phase 4 panel (288,000 rows; 70 design fits and 40 permutation-null fits) first attributed the hidden state to field groups: **volume, not the analyst field or the P/E, was the largest carrier** (add-one +0.220), then the valuation group (+0.133), sentiment (+0.062), with the analyst field (+0.002) and implied volatility (+0.002) near zero. The extended L1 set (22 candidates, least-squares combinations of up to three) found nothing that beats the price. The final ablation after every design landed:

| Group | Add-one R-squared for x, v2 baseline to Phase 5 | Calm-trained add-one, Phase 5 |
|---|---|---|
| Volume | +0.2203 to +0.0042 [+0.0025, +0.0059] | +0.0058 |
| Valuation (P/E, yield, days since announcement) | +0.1328 to +0.0090 [+0.0011, +0.0167] | +0.0509 [+0.0353, +0.0677] |
| Sentiment | +0.0616 to minus 0.0007 | +0.0029 |
| Analyst | +0.0024 to minus 0.0011 | +0.0100 |
| Levels (price, moving averages, MACD) | +0.0067 to +0.0055 | +0.0225 |
| Implied volatility | +0.0023 to +0.0029 | +0.0188 |
| Base to full, all rows | 0.414 to 0.805 (v2 fields) becomes 0.406 to 0.432 | 0.291 to 0.395 |

**The eighteen fields add +0.026 of R-squared where they added +0.39: a 93 percent reduction.** The macro-phase clock's selectivity fell from +10.4 points to +1.8 (67.6 against 65.8 percent; day only 50.8; majority 41.4), a PASS against the 10-point margin that Phase 6 then re-derived. The onset audit passed at all six transitions under the non-price rule. The calm-trained level-free channel moved from 0.3493 (Phase 3) to 0.3213 (Phase 4) to 0.2912 [0.2637, 0.3179] (Phase 5), and the full-field one from 0.5501 to 0.4905 to 0.3950; the fields' calm contribution fell from 0.201 to 0.169 to 0.104, with the valuation group (+0.051) the largest remainder. A permutation null for the add-one statistic was found to sit below zero (a larger feature set overfits a random target more), so the absolute-admissibility clause was disclosed as mis-specified rather than re-specified, a finding Phase 6 met again.

![Figure 15](figures/F15_observables_fits.png)

*Figure 15. What the data give (blue) against what v2 had assumed (orange) for the P/E cross-section (411 tickers, monthly 2009 to 2024), the dividend payout (10,666 stock-years), the volume process (417 stocks) and the announcement lag (27,242 filings).*

![Figure 16](figures/F31_field_group_ablation.png)

*Figure 16. The field-group ablation before and after the redesign: the R-squared for x that each field group adds to the level-free base, (a) on all rows and (b) calm-trained, with paired cluster-bootstrap intervals; 1,600 paths, 288,000 modelled rows. All shown fields together added +0.39 over the base as inherited and +0.026 after Phase 5.*

![Figure 17](figures/F16_onset_audit.png)

*Figure 17. The final onset audit: for each shown field and each phase transition, the field's AUC for detecting the transition over the next five days minus the best price-based reference; a negative value means the field announces nothing the price path did not; the dagger marks the cells that fail the registered null (technical indicators, which the addendum moved to the reference side, and the analyst field at the blow-off to post-top transition on 23 paths). 200 paths per transition (23 for the last); 500 circular shifts.*

![Figure 18](figures/F11_calm_trained_by_phase.png)

*Figure 18. The calm-trained surrogate for x at the Phase 3, 4 and 5 hand-overs: (a) R-squared on calm rows for the level-free feature set (price shape only) and for every shown field; (b) sign accuracy on resolvable steps. The gap between the two series is what the fields add; it closed from 0.20 to 0.10. the 1,200 paths of the 1,600-path panel that carry calm rows, about 119,400 calm rows, 500-resample cluster bootstrap.*

![Figure 19](figures/F12_discrimination_by_handover.png)

*Figure 19. Whether the benchmark still discriminates at each hand-over: the mandate-conditional regret of the true-value oracle, the two observables surrogates and two trivial policies, per scenario, after Phases 2 to 5. The oracle must beat the surrogates, which must beat the trivial policies; this held at every hand-over while the gaps moved. 150 cells per state and scenario (50 scored seeds x 3 personas).*

### 12.3 Parameters at the hand-over

| Entry | v2 (DESIGN) | In force after Phase 5 | Label | n | Status |
|---|---|---|---|---|---|
| Multiple | k uniform on 14 to 22 per seed | design B: a between-stock log grid (P/E 5.77 to 39.98) plus a within-stock daily AR(1) (0.99661) | FIT | 411 stocks, 61,843 stock-months | ADOPTED |
| EPS | noise 0.10; lag U(25, 35); cap 200; no losses | noise 0.1707; loss probabilities 0.097 / 0.425 / 0.062; a loss-size grid; cap 191.5; lag grid [10, 30] trading days; "n/m" for non-positive trailing EPS | FIT | 27,515 quarters; 27,242 filings | ADOPTED |
| Dividend | payout 0.35, stickiness 0.7, everyone pays | speed 0.697, target 0.406, payer share 0.887; field shown (hidden switchable) | FIT (process); rendering open | 417 names; 10,666 stock-years | ADOPTED (process) |
| Analyst | V times an error of sd 0.15 | design C: the 250-day price average times an error of sd 0.564 (LIT), rho 0.95 per weekly update (DESIGN) | LIT + DESIGN | 5 arms x 1,600 paths | PROVISIONAL |
| Sentiment | 0.6 tanh(2x) + 0.3 tanh(ret20 / 0.15); AR 0.85 | design A: rho 0.211, loading 0.111, residual 0.972; predictive size 0.0008 unchanged (LIT); B's valuation link 0.95 switchable | FIT | 17,017 days; 57 windows; 560 months | PROVISIONAL |
| Volume | AR 0.65; 0.25 on the absolute return; 1.2 on absolute x | design A: 0.526, 0.203, residual 0.347 | FIT | 417 stocks | ADOPTED |
| Audit bounds | | a 0.20 ceiling on any field group's add-one; the onset rule; an L2b margin owned by Phase 6 | PROVISIONAL | | Phase 6 |

Freeze: 27 files. Path hashes: 2,635 non-analyst column changes against the previous state (0 when every switch is off, proved against a clean copy of the previous state). Whole suite: 159 passed, 1 skipped, 4 expected failures. Checklist: 5 / 10 / 5. A continuous-integration fixture defect was found (the raw panel's "n/m" days counted inside the L1 floor) and fixed in the fixture rather than in the frozen evaluation code. Compute: a laptop only (the largest ablation 8,480 seconds); no LLM cost.

### 12.4 Results that contradicted expectations

Greenwood, Shleifer and You's run-up turnover premise did not reproduce. Tetlock's 8.1 basis points did not reproduce on the free source. The registered onset reference set failed on the technicals. The permutation null sits below zero. Every analyst design of the form V times an error fails the onset test regardless of the noise. The weekly sentiment design fails the first rule by 0.011. Two scale errors in filings and an unidentified unconstrained Lintner fit. The fitted valuation link puts more x into the sentiment field than the v2 tanh did. The rendered "n/m" share undershoots the data (6.2 against 8.5 percent). A stale path-hash fixture (722 columns) was explained as Phase 4's own control and centred-depth changes.

---

## 13. Phase 6: audits and checklist methodology, and the 16A checkpoint

### 13.1 Goal

Give every checklist threshold an empirical reference from real 200-day windows; derive every leakage gate from a null or a bound; give every audit statistic a known-answer test; derive seed counts from power; compute the plan's go / no-go checkpoint; stop for the team. No criterion is stated; every criterion is FIT from the reference distribution or DERIVED.

### 13.2 Work carried out

**Known-answer tests first** (30 cases, 400 replications at T = 200 and a long horizon): 18 pass, 3 fail, 9 reported. The failures are estimator properties, recorded rather than silenced: the Hill index at 5 percent depth reads 3.19 for a t(4) tail (exact for a Pareto tail); the sample excess kurtosis of a t(5) has median 1.77 at T = 200 for a true 6.0; the Jarque-Bera size at 400 replications read 0.0725 (0.057 at 2,000). Consequences for the v2 criteria: the 200-day sample ACF(1) at the fitted half-life reads 0.947 for a true 0.9695 (an implied half-life of 12.7 days for a true 22.4), so item 9's "at least 0.98 and 60 days" cannot be met by the process in force; against the generator's own GJR shape, the ARCH-LM(5) test rejects at 1 percent in only 23.3 percent of 200-day windows and the Ljung-Box test on absolute returns in 27.5 percent, so item 3's "at least 80 percent of seeds" asks for what the true process cannot show.

**The reference distributions.** 12,927 non-overlapping 200-day windows of the 417 set-A names (31 each), computed by the audit's own functions, with P10 / P50 / P90 per statistic overall and in four sub-periods. For example, the median absolute lag-1 return autocorrelation is 0.0585, the median excess kurtosis 2.17, the Ljung-Box p-value on absolute returns has median 0.18 (so real windows fail the clustering criterion most of the time), the leverage correlation median is minus 0.038, the volume-volatility Spearman correlation 0.326, the log-volume Shapiro p median 0.0037 (real volume is not log-normal), the crash-window drawdown median minus 0.31 (6,275 windows with a drawdown of at least 20 percent), the daily sigma median 0.0175. An implied-volatility block from 166 windows: single-stock implied volatility pooled over five names 21.6 / 28.4 / 37.6 percent with a correlation of 0.55 to the next 20 days' realised volatility.

**The power analysis** on the stored 1,600-path panel: 23 criteria, of which 20 are decidable at the planned 200 seeds and three are not (the absolute-return ACF band, whose pilot median sits just outside the band; GARCH persistence, which needs 754; skew, which needs 2,028).

**The criteria, their size and their power.** Three forms: A = the v2 rules; B = the bootstrap 95 percent upper limit of the two-sample Kolmogorov-Smirnov distance against the reference below 0.10; C = the share of generator paths inside the reference P10 to P90 at least 0.80 minus a binomial allowance. Simulated on the reference itself: **B has no size at 200 paths** (it passes a sample drawn from the reference only 2 to 8 percent of the time), size 0.94 at 500 and 1.00 at 800, and it rejects a true distance of 0.10 with at least 95 percent power everywhere at 500; **C has size at every n but no power against a 0.10 shift on most statistics**. So B decides at 500 seeds per scenario and C is the band report; the plan had asserted a power that B does not have.

**The final checklist at 500 seeds per scenario** (3,000 pooled paths, 1,500 crashes): under A (the v2 rules) 5 pass / 10 fail / 5 not applicable; under B every judged item fails (at n = 3,000 the upper limit sits about 0.017 above the distance, so the verdict is the distance itself: 0.03 to 0.05 on three statistics, 0.10 to 0.14 on the tails, ARCH, leverage and the GJR term, 0.19 to 0.27 on persistence and the absolute-return Ljung-Box statistic, 0.38 to 0.63 on volume log-normality, the worst day, daily sigma and the drawdown); under C items 2 and 8 pass and items 1, 3, 5, 6, 7 and 20 fail (the generator's volume is more log-normal than real volume; its crash drawdown of minus 0.52 is deeper than the real minus 0.31; its calm sigma 0.020 against 0.017). Two never-implemented v2 clauses were run: item 12's realised next-day sentiment loading is 0.00055 [0.00046, 0.00063] against the configured 0.0008 (FAIL, a fidelity question for the sentiment decision); item 13's cross-seed sd of calm implied volatility is 6.8 (PASS, non-degenerate). Item 9 was re-stated on the fitted process: the median 200-day ACF(1) of x on flat paths, 0.945, sits inside the AR(1) reference [0.906, 0.968] at the fitted half-life, and the sd inside its band (PASS).

![Figure 20](figures/F17_reference_distributions.png)

*Figure 20. For every checklist statistic, the generator's P10 to P90 range (blue, with its median) against the real panel's (grey), standardised per row by the panel's P10 to P90 width; the verdicts under criterion B (the Kolmogorov-Smirnov distance) and C (the share in band) at the right. Generator 3,000 paths (500 seeds per scenario); reference 12,927 windows.*

**The L1 ceiling derived.** A candidate carrying nothing about x beyond the price path has a within-5-percent share of at most 0.606, from the mispricing's sd (0.0656) and the Kalman bound at day 200 (0.2005); with a bootstrap half-width the rule is 0.617. The price itself sits at 0.426 [0.416, 0.437]; every field candidate at 0.03 to 0.07; all 27 candidates (the 22 extended ones, four audit candidates and the best-of row) PASS. The 1 percent hard-coded floor stays available only as the v2 rule.

**The bound and the ladder.** The Gaussian Kalman bound at the values in force (sigma_V 0.014573, h 22.38, s_x 0.0656) is 0.1773 window-averaged and 0.2005 at day 200. The ladder locates the excess (Figure 21): the exact Gaussian process 0.145, plus the GJR innovation 0.145, plus jumps 0.192, both 0.203 (the allowance +0.057); the generator's flat scenario with the sentiment feedback off 0.220 and on 0.222 (the feedback is worth +0.0014); every calm row of the standard panel 0.2912 [0.2637, 0.3179] (the events' pre-event calm adds +0.069). The G4b rule: the calm-trained level-free R-squared must have a lower limit at or below the bound at the population's s_x (0.1695) plus the allowance, 0.2267; measured 0.2912 with a lower limit of 0.2637, **FAIL**, and it fails under the readings not adopted too. The flat scenario alone passes; the excess is not the fields and not the feedback but the events' pre-event calm, Phase 4's territory.

![Figure 21](figures/F10_calm_channel_ladder.png)

*Figure 21. The calm level-free channel decomposed block by block: each rung's measured R-squared (blue, 95 percent interval) against the Gaussian Kalman bound at that rung's mispricing sd (orange tick). 200 paths per rung, 1,600 for the last.*

**The derived L2 and L2b gates.** One tool and one feature construction (the level-free control of 45 columns; the full set of 141 columns adding every rendered field); the null swaps each path's target series whole with another path's and refits both sets; the registered margin is the null's 95th percentile plus a half-width. **The null sits entirely below zero** (all 40 draws negative: the level-free base fits a random target at about minus 0.004 and the full set at minus 0.047, the overfitting penalty of the larger set), so the plan's letter gives a negative margin that no field could pass: FAIL as registered on all rows (+0.0263 measured against minus 0.0214), on calm rows (+0.1088 against minus 0.0313) and for the phase clock (+0.0295 against minus 0.0023). A centred reading registered as the sensitivity before any draw was read gives +0.0267 against +0.0263 on all rows (undecided, a gap of 0.0004 on a half-width of 0.0148), FAIL by three half-widths calm-trained (+0.1088 against +0.0379: the fields' calm contribution that Phase 5 measured), and FAIL for the clock under both margins (+0.0295 and +0.0181 against +0.0105). **Phase 5's L2b PASS at +1.8 points was against a 10-point margin frozen after the result was known; the derived margin is a tenth of that.** Nothing was re-specified; both entries stay in the known-defect registry as derived gates.

![Figure 22](figures/F32_derived_gates.png)

*Figure 22. (a) The target-permutation null for the derived L2 and L2b gates: the null draws (grey), the null's 95th percentile, the registered margin and the measured selectivity with its interval; every draw is negative because a larger feature set overfits a random target more. 40 draws (all rows), 20 (calm-trained and the clock) on 1,600 paths. (b) The derived L1 rule: the share of steps on which each candidate lands within 5 percent of V against the derived ceiling of 0.617; 1,600 paths, 320,000 steps.*

**The held-out split**: training on three scenarios and scoring the fourth gives a negative R-squared for x on every held-out scenario except the bull trap's calm rows (sustained bull minus 2.3 to minus 3.1); the pooled 0.42 is within-scenario structure, and the surrogate does not transfer across scenarios (a finding with no gate).

**The tuned-parameter ledger** records, for items 7, 9, 10, 11, 13, 17, 20, 14 (L1 and L2) and 16, what moved when, which parameters were tuned against it, and how Phase 6 reads it now: item 7's criterion is mis-specified in both forms (real volume rejects log-normality); item 9's 200-day estimator cannot reach 0.98 at any fitted half-life; item 10 is unattainable by construction; item 11 was a calibration target; item 13's implied-volatility correlation of 0.23 against a real 0.55 is structural to the past-only filter; item 17's rejection rate is a sampler property; item 20's magnitudes are now judged by B and C; L1's ceiling and the L2 and L2b margins are derived.

**16A, the go / no-go checkpoint** (100 scored seeds per scenario, 40 disjoint training seeds, three personas; the oracles are gradient-boosted trees on 240 training paths; MCR at theta 0.05 with a 500-resample cluster bootstrap over seeds):

| Scenario | True-value oracle | Level-free observables oracle | Level-free price-only oracle | Best simple rule (price against its 50-day average) | Best trivial policy |
|---|---|---|---|---|---|
| Flat | 0.0027 [0.0026, 0.0028] | 0.0770 [0.0669, 0.0856] | 0.0745 [0.0660, 0.0842] | 0.0541 [0.0458, 0.0622] | band high 0.0874 [0.0751, 0.0997] |
| Bull trap | 0.0033 | 0.0383 [0.0326, 0.0448] | 0.0405 | 0.0378 | band high 0.0262 [0.0214, 0.0312] |
| Crash | 0.0022 | 0.0466 [0.0409, 0.0518] | 0.0437 | 0.0481 | band low 0.0581 [0.0506, 0.0660] |
| Sustained bull | 0.0028 | 0.0769 [0.0669, 0.0869] | 0.0771 | 0.0570 | band high 0.0877 [0.0749, 0.1006] |

G1 (oracle below observables oracle below the best trivial policy, intervals apart, in every scenario): FAIL, 0 of 4, because a constant band edge matches or beats the observables oracle (it beats it outright in the bull trap). G2 (the best simple level-free rule above the observables oracle in at least 3 of 4): FAIL, 0 of 4, because the two-line rule is below the oracle in flat and sustained bull. G3 (the oracle's target switches at least twice per run in the event scenarios, in at least half the runs): **PASS** (medians 2 / 2 / 4 / 2, shares 0.76 / 0.61 / 0.90 / 0.77), disconfirming the plan's expectation, which had been written at a 150-day half-life. G4a (the observables oracle beats the price-only oracle): FAIL, 0 of 4 (the fields raise the training-pool calm R-squared from minus 0.08 to 0.10 without reaching the mandate metric). G4b: FAIL (above). Sensitivities at theta 0.03, 0.08, 0.12 and 0.20: G1, G2 and G4a fail at every theta except G1 in the crash at 0.03; G3 passes at 0.03 and fails from 0.08. **16A is not met; under the plan the programme stops for the team to decide.** The reading not adopted: with Phase 5's trivial set (always hold, constant mix, random) G1 would have held; the constant band edges added to the trivial set are what defeats it.

![Figure 23](figures/F18_checkpoint_16A.png)

*Figure 23. Checkpoint 16A restated on the Phase 7 panel: the mandate-conditional regret at theta 0.05 of every policy in each scenario; an informed policy must beat the best trivial one in every scenario (G1), and it does not. Up to 300 runs per policy and scenario (100 scored seeds x 3 personas).*

**The L3 probe** (an LLM asked "over-valued, under-valued or fairly valued?" on 200 rendered days, with a shuffled-V arm) was built here and run in Phase 8 (section 15).

### 13.3 Parameters set or derived

The reference P10 / P50 / P90 of every statistic with its n (FIT); criterion B (a distance of 0.10, 500 resamples, a minimum n of 500 derived from its measured size; DESIGN and DERIVED); criterion C (DESIGN); the crash-window rule (a real window contains a crash when its drawdown is at least 20 percent; 6,275 windows; DESIGN); the item 9 reference at the fitted half-life (DERIVED); the L1 ceiling 0.617 (DERIVED); the L2 all-rows, L2 calm-trained and L2b margins as registered and centred (DERIVED). The only edit inside the generator's parameter code replaces the two provisional audit bounds by the derived values when the criteria file is present. No generator parameter changed: 0 of 95 path configurations moved. Freeze: 27 files. Tests: eleven new tests (every reference row has n and ordered quantiles; footer counts; the known answers with the findings recorded rather than silenced; no subsampling in the published audit; the derived margin equals the stored 95th percentile plus the half-width; every report table regenerates from its file; the audit switches inert; the reference estimator reproduces the reference rows to 1e-9). The after-state suite showed 3 failed, 169 passed, 1 skipped, 4 expected failures; the three failures were two documentation-number tests and the footer-count test on the reference checklist, and the next phase's clean run (191 passed) is the evidence they were addressed. Compute: the final audit 11.3 hours at three workers; the null 80 fits of about 345 seconds each.

**The reference machine.** Phase 6 also established a 128-core laboratory machine as a reference: it reproduced 7 path configurations to a worst relative difference of 2.3e-13, the 51-moment SMM reference row to 1e-10 and a level-free gradient-boosted refit exactly (0.4058695137596712 on both machines), in 7 seconds for the 1,600-path panel against 172 on the laptop. A byte-level hash comparison is not usable across platforms (1,877 last-bit differences), so a numeric check at 1e-9 replaces it.

### 13.4 Results that contradicted expectations

The L2 target-permutation null sits entirely below zero. The L2b derived margin is a tenth of the frozen one. Three known-answer failures and 23 to 28 percent power for item 3's rules against the generator's own process. Criterion B has no size at 200 paths. The criteria file's items block had dropped the per-statistic overrides (found and rebuilt from cache). G3 passes where the plan expected a fail. G1 fails because of the constant band edges; G2 because a 3 percent price-over-average rule tracks the sign of x as well as the field-bearing oracle at a 22-day half-life; G4a fails although the fields raise the training-pool R-squared. The surrogate does not transfer across scenarios. Item 12's realised loading is 70 percent of the configured one. The reference machine's per-file transfer produced a corrupt hybrid file once (a resumed download joined a newer tail onto an older head), caught by the numeric check.

---

## 14. Phase 7: targets, action and metrics

### 14.1 Goal

Phase 7 owns the scoring: what counts as a correct action (the resolvability threshold theta), what the regret metric measures (band violation against directional agreement) with a floor and ceiling that mean what the documents say, whether the persona bands are consistent with the environment's own risk and return, whether the shown dividend is real money, whether the day-1 gate is well posed, and whether every cell's baselines are computed on the path the agent actually saw. No LLM call; everything is a re-scoring of stored runs, scripted policies, or a derivation on the frozen generator. Team decisions before any experiment: restrict the claim (the paper's claims are restricted to a one-shot mandate-conflict benchmark; no repair option is run; the gated experiments run on the frozen Phase 6 state), pay dividends, and score the practitioner bands; the theta decisions were held until the derived values were on the table.

Verification before anything was read: the theta refit reproduced the four published Phase 6 sign accuracies to 1e-12; the regenerated 12-million-row policy panel equals Phase 6's own MCR to a worst difference of 1e-16 over 51,450 comparisons (a first single-precision build at 3e-8 was rebuilt rather than the tolerance widened).

### 14.2 Work carried out

**Theta derived three ways.** theta_info = the smallest grid value at which the level-free surrogate's sign accuracy on resolvable steps reaches 0.80 and stays there: pooled over all rows **0.05** (accuracy 0.800 [0.791, 0.810], coverage 0.597, n = 171,916 resolvable rows); on calm rows alone 0.20 (0.880, coverage 0.009, n = 1,089); per scenario the values range from 0.01 (bull trap) to 0.25 (sustained bull, on 131 rows), reported with their n and stored in the parameter file as a record, with only the pooled values in force. The registered expectation that calm rows never reach 0.80 was wrong. theta_cost = the mispricing at which one full reallocation pays for its round-trip cost over one half-life: 2c / f = 4c = **0.0020** at a 5 bp cost, the same for every persona, checked numerically against the real portfolio simulator to 0.14 percent; at this theta coverage is 0.97, so the cost does not discriminate (a cost tier 25 times larger would put it at 0.05). theta_var = one within-run sd of x = 0.0463 [0.0389, 0.0724]. theta_info and theta_cost are **co-primary**; the calm 0.20 is reported and not primary.

![Figure 24](figures/F19_theta_tradeoff.png)

*Figure 24. (a) The level-free surrogate's sign accuracy on resolvable steps against theta, for every shown field and for the price fields only, with the derived thresholds marked; (b) the share of days that are resolvable at each theta. 1,600 paths, 288,000 rows; 500-resample cluster bootstrap.*

**The decomposition.** MCR = B + D by construction, where B_t = max(0, the distance of the agent's cash share from the band centre minus the half-width) is the band-violation term and D_t is the directional remainder (how far the in-band part of the allocation is from the oracle's edge); D is never negative because the oracle's target is clipped into the band. The ceiling is the mandate-conditional oracle run through the real simulator (realised 0.0028, not 0, because of the dead band and the drift between trades) and the floor the worst of six trivial policies (always hold, always buy, always sell, random, band low, band high); the sign lives in one function. Under the v2 convention the observables oracle had scored 1.067 (above 1); under v2.1 it scores 0.919.

**The bands against the environment's own risk and return** (500 seeds per scenario, dividends paid, a zero risk-free rate): flat-path annualised sigma 0.3468 [0.3381, 0.3556] (the v2 documents' "about 28 percent" is superseded), total-return mu 0.0874 [0.0618, 0.1151], price-only 0.0548. The Merton share w = (mu minus r) / (gamma sigma squared) for risk aversion gamma from 2 to 10 gives cash shares of 0.637 to 0.927: three values of gamma (3, 4, 6) land in the ISFJ band of 0.70 to 0.90 and none in the INTJ band of 0.40 to 0.60 or the ENTJ band of 0.00 to 0.20. A Merton reading would collapse the personas into one band; the practitioner bands stay the scored default and the Merton reading is reported. A spread constant the v2 code carried (0.06 to 0.12, attributed to a finance-journal table) was withdrawn: the cited table contains trait coefficients, not a spread.

**Dividends paid.** Ex-dates are recovered from the generator's own frame (three per 200-day path, about 63 days apart; the price path is not ex-dividend adjusted, because the generator is frozen). On 500 flat seeds the realised yield is 3.42 percent a year and the payer share 0.908. The effect on the ten baseline policies (100 seeds x 4 scenarios x 3 personas): returns rise by 0.9 to 2.6 points in proportion to how invested a policy is; always-sell gains exactly 0; the absolute change in MCR is at most 0.007. The switch defaults to off and is inert.

**The day-1 gate**, re-specified to the common-start design only, on day-1 levels (a persona-consistent agent that starts at its centre has a change of about zero, so the change table under start-at-target is removed rather than kept as exploratory); its null comes from arms with no persona text, so on the pilot's nine common-start runs it is NOT COMPUTABLE, and it stays so under Phase 8's decision that the only no-persona reference is the NONE arm.

**Baselines on the run's own path.** The baselines are rebuilt from each run's stored metadata (every hashed field). On the pilot's 52 runs: 0 of 52 environments are constructible under the recorded engine (the single-stock engine was rejected in Phase 2), 52 of 52 are constructible under the fallback but 0 of 52 reproduce (worst price difference median 37.5). So the pilot is re-scored on logged columns only and no baseline is rebuilt for it. The switch is tested on a fresh cell with a non-default sentiment predictive loading where only the metadata construction matches the run's hash.

**Further corrections.** The trader arm is band-free everywhere (one definition, four consumers); pre-trade and post-trade cash-share columns record both shares under next-open execution; the cost concept is named (5 bp per trade, 10 bp round trip, a DESIGN value between a 2.25 bp half-spread and a 6.18 bp market-impact median); the half-width 0.10 and the dead band 0.01 are labelled DESIGN, the half-width swept at 0.05, 0.10 and 0.15 on every re-score; the placebo's length was measured on the pilot's prompts (words 52.9 real against 51.0 placebo, n 11 and 9).

**Construct validity and the adoption rule.** Three scripted policy families with a known construct (drift walks away from the band centre; align moves to the oracle's edge with probability p; panic jumps to cash on a drawdown) were swept across their parameters at 100 seeds per value, 1,200 cells per swept value: every sweep is monotone with zero reversals under both candidate scorings (the decomposition A and a per-window alternative B). The correlation matrix across 600 cells says what the metrics measure: |r|(band-MAS, MCR) = 0.976, |r|(band-MAS, B) = 0.996, |r|(D, band-MAS) = 0.069, |r|(return, drawdown) = 0.454, |r|(B, MCR) = 0.978 by construction, everything else at most 0.27. A collinearity ceiling computed from a fourth family (align at p = 0.5 plus the drift displacement) is 0.9950 for A; the observed 0.9758 sits below it, so A qualifies (as does B); the tie-break adopts **A** for comparability with the pilot, and the adoption holds at all 9 theta x 3 half-width combinations. Stated plainly: MCR and band-MAS are near-duplicates (0.98), and D is the component that is not.

![Figure 25](figures/F33_merton_and_g3_profile.png)

*Figure 25. (a) The Merton cash share against risk aversion, with its interval, against the three persona bands: three values of gamma land in the conservative band and none in the balanced or aggressive bands; 500 flat seeds. (b) The mandate oracle's target switches per run against theta, per scenario, and (c) the share of resolvable days against theta; 100 seeds x 3 personas per scenario, 500-resample cluster bootstrap over seeds. The two vertical lines mark the co-primary thresholds.*

![Figure 26](figures/F20_metric_matrix_and_sweeps.png)

*Figure 26. (a) The absolute correlation between metrics across 600 policy cells; (b1) the align sweep lowers D monotonically; (b2) the drift sweep raises band-MAS monotonically. 600 cells; 1,200 cells and 100 seeds per swept value.*

**16A restated** on MCR, on B, on D and per window: G1, G2 and G4a fail 0 of 4 on every statistic; daily G3 reproduces Phase 6 exactly; per-window G3 fails at every theta (so the plan's own admissible alternative scoring removes the one passing gate). G3's theta profile: PASS at every theta up to 0.05, FAIL from 0.066 (a theta-conditional pass, recorded, with no horizon or scoring change). A half-width sensitivity across 27 theta-by-half-width slices and four statistics finds G2's ordering in nine of the 108 cells (eight on the band-violation term at a half-width of 0.05, one on per-window MCR), reported as a diagnostic and never as a pass.

**The pilot re-scored**: the re-score reproduces the published per-run file to 2e-16; the decomposition separates INTJ's failure (out of mandate: static MCR 0.3925 = B 0.3756 + D 0.0168, outside the band on 98.9 percent of resolvable steps) from ISFJ's memory arm (inside the band, wrongly directed: B 0.0764, D 0.1545); four prose figures in the pilot notes that disagreed with their own table were corrected (they had averaged the 30-day smoke runs in).

### 14.3 Settings at the hand-over

The theta grid {0.03, 0.05, 0.08, 0.12, 0.20} (REGISTERED); theta_info pooled 0.05 and calm 0.20 (DERIVED); theta_cost 0.0020 with a one-day-horizon sensitivity of 0.0328 and a cost-tier table (DERIVED); theta_var 0.0463 (DERIVED); the co-primary pair [0.002, 0.05] in force, with G3 recorded as theta-conditional; half-width 0.10 and dead band 0.01 (DESIGN); the cost tier of 5 bp per trade (DESIGN, interval [2.25, 9.97]); band convention A scored and the Merton reading reported (READ from four practitioner sources); the decomposition with its floor and ceiling (REGISTERED); the 25-day window alternative built and not adopted; the spread constant withdrawn; the trader band (0, 1); the dividend switch off by default; a scoring switch that adds the new keys. Freeze: 27 to 30 files (the scoring module, its loader and its parameter file). 0 of 95 path hashes changed. Tests: 19 new; one Phase 0 test asserting the contract that the gate re-specification replaced was updated, not weakened. Whole suite: 191 passed, 1 skipped, 4 expected failures, 0 failed. Compute: a laptop only; no spend.

### 14.4 Results that contradicted expectations

theta_info is reached on calm rows (0.20 on 1,089 rows). The ceiling's construction needed a policy family the sweep set lacked. The 16A runs file carried no per-day allocations, so trajectories were regenerated. The pilot's engine cannot be constructed at all. G3 fails at every theta under per-window scoring. The pilot notes' prose disagreed with their table. The v2.1 ceiling is 0.0028, not "0 by construction". The registered theta locator is silent when a larger grid point is unmeasurable; two readings differ on one cell and both are stored, because a silent edit had once flipped the published table.

---

## 15. Phase 8: harness and statistics

### 15.1 Goal

Phase 8 owns everything between the environment and a published contrast: what the stateful (memory-carrying) agent actually sees and how many tokens of it; how the covariate behind the "decay" thesis (that the mandate's influence fades with distance in the context) is computed; which statistical model contrasts are fitted with and whether it holds its false-positive rate; how multiplicity across hundreds of contrasts is controlled; whether the salience shares (how much of the agent's behaviour is attributable to the persona text, the directive and the starting allocation) are identified at all; and the one paid experiment, the variance pilot that measures the noise the main grid must be sized against. Every statistical choice was validated on simulated data with a known answer before it touched a real contrast. A golden record of the unmodified modules was captured first; every switch was later proved inert against it.

### 15.2 Work carried out

**The stateful arm's four defects**, each measured on the pilot's three stateful logs and corrected behind a harness-version switch: (a) the mandate-offset covariate pointed at the wrong copy of the mandate (it was counted from the system prompt's copy through every replayed copy, growing to 15,261 to 16,546 tokens at day 200, while the nearest copy, injected into the current turn, sits 409 characters-over-4 or 436 tokenizer tokens away, constant from day 1 to 200: a factor of 37 to 40); (b) the token budget was mismatched (history turns replayed 20 copies of the mandate block, 22 in all, 9.0 percent of the day-200 context; in the full mode the memory arm's context was about 749 characters shorter than static's); (c) parse fallbacks were stored as the model's own prior turn (fabricated JSON; latent, 0 occurrences in the pilot); (d) two token units in one log (the provider's count for the context, characters-over-4 for the offset). Under the corrected harness the static and memory histories are byte-identical and their contexts differ by exactly the 311-character block; the nearest copy is the primary offset with the system copy beside; fallbacks are stored as "no valid answer"; tokens are counted by the provider, else a tokenizer, else characters-over-4, with the method logged. The placebo, measured per persona: the v2 placebo's 7 imperatives matched ISFJ only (ENTJ has 8, INTJ 6); the corrected placebo removes or appends registered clauses until the imperatives are equal, the word count then tested (within 10 percent) and reported as found; both hold for 3 of 3 personas.

**Context length as a factor.** Levels {5, 20, 50, full}, with 50-turn arms added; the 60,000-token budget holds 80 turns (v2) or 77 (corrected), so "full" is an 80-turn window, not a full transcript (the registered "about 65 turns" was wrong). Priced per run at the then rates: stateless 0.168 dollars on Gemini 2.5 Flash, rolling 20 about 1.1, full about 3.2.

**The mixed model and the intervals.** Four estimators on simulated data (2 arms, 3 personas, 2 scenario cells, 3 or 6 models, 5 or 10 paths per cell; the path effect real, from the observables oracle's own band-MAS; 300 datasets per condition): the v2 nested model (seeds inside models, intercepts only); a crossed mixed model with variance components for model, model by arm, path and path by arm; a two-way cluster bootstrap over models and paths (1,999 resamples, percentile intervals); the v2 run-level bootstrap. With a model-by-arm sd of 0.03, **the v2 nested model rejects a true null in 36 to 58 percent of datasets**; the crossed model holds at 6 models (0.053 to 0.073) and not at 3; the two-way bootstrap holds at 6 and not at 3 with 10 paths; the run-level bootstrap fails where paths are many and gets worse as paths are added. Recovery on a large design (12 models, 20 paths): every planted component inside the crossed model's 5th to 95th percentile band; power 0.970. After the variance pilot the picture sharpened: the pilot put 82 percent of Flash's band-MAS variance in persona by path, which the crossed model does not pair within, so its arm standard error is 2.27 to 2.48 times the paired one; the optimiser stops at a local optimum in 15 to 20 percent of fits; an amended model on seed-level differences did not meet its pre-registered adoption rule. Fallback: the crossed model is reported descriptively at the better of two optimisers, **the two-way bootstrap's intervals decide**, and a t reference with M minus 1 degrees of freedom, which restores size at six models, was carried to Phase 9 as a candidate rather than adopted after the fact. The simulation's dataset seeds came from per-process string hashes and are not bit-reproducible (disclosed; the new stages use a deterministic hash).

![Figure 27](figures/F26_estimator_size_power.png)

*Figure 27. On simulated data with a known answer: (a) the false-positive rate of four contrast estimators when there is no arm effect, at a nominal 0.05 (the v2 nested mixed model, in grey, rejects a true null 36 to 58 percent of the time once the arm effect varies by model); (b) power at a true effect of 0.05. M models, S seeds per cell, sd = the planted between-model spread of the arm effect. 300 datasets per condition; Wilson 95 percent intervals.*

**Multiplicity.** The confirmatory tier (band-MAS and D at the two co-primary thetas) has correlations of 0.069, 0.066 and 0.992 (the two D tests are near-duplicates). Simulated over 5,000 replications: the v2 procedure's false-discovery rate under the global null is 0.431 on the pilot's family (36 tests) and 0.996 on a reviewer's four-family grid (360 tests); Benjamini-Hochberg within a family holds on one family (0.042) and fails on four (0.158); Benjamini-Yekutieli across families holds everywhere (at most 0.012) at a power cost. Rule: Benjamini-Yekutieli across families decides on any multi-family grid, Benjamini-Hochberg within a family is reported beside it, and the v2 procedure is withdrawn.

**The temporal null.** For a within-run trend claim, four nulls on AR(1) series with the pilot's own persistence (0.9214) and no trend: the v2 circular shift rejects 7.1 percent, a window permutation 11.9, the registered day-block permutation 12.0, a path-level sign flip 4.3. Only the sign flip holds; it needs at least six paths to reject at all.

![Figure 28](figures/F34_multiplicity_and_temporal_null.png)

*Figure 28. (a) The false-discovery rate of three multiplicity procedures on one family of 36 tests and on four families of 360 tests, with and without true effects; 5,000 replications per cell. (b) The false-positive rate of four temporal nulls for a within-run trend when no trend is present, at 36 runs, against the persistence of the daily cash-share series; 1,000 replications with 999 null draws each. Only the path-level sign flip holds its size.*

**Salience identification.** The registered identification condition was unsatisfiable as written (one clause requires a common start, another requires the start block to vary); under start-at-target the start share is a deterministic function of the persona (R-squared 1.000, canonical correlation 1.000), so the persona and start shares cannot be told apart: in a known-answer design the start-at-target surrogate splits one persona effect arbitrarily (a persona share of 0.697 and a start share of 0.262 in one window, 0.914 and 0.051 in another), while a common-start design with a no-persona reference recovers it stably (0.979 in the first window and 0.975 in the second). The team decided that shares are computed only on a common-start slice with a reference level, and the only reference that exists is the NONE arm (the v1 numerical persona cannot run in v2 and its text contradicts the bands), which the team confirmed knowing that it leaves the day-1 gate's null NOT COMPUTABLE. The seed-cluster bootstrap for the shares had leaked (relabelled copies of a resampled seed landed in different cross-validation folds), giving intervals that excluded their own point estimates; fixed and re-run at 200 refits per window: a persona share of 0.979 [0.974, 0.984].

**The variance pilot** (the only paid experiment before Phase 9). Design: Gemini 2.5 Flash; ISFJ, INTJ, ENTJ; static and memory arms; flat, bull trap, crash at delta 0.70, sustained bull; eight seeds; three decode replicates; T = 200: 576 runs, 115,200 calls; a transfer check on GPT-5 mini (bull trap only, 144 runs). A smoke and a cost gate first: at the provider's default the first smoke billed 1.082 and 0.787 dollars per Flash run (1,540 thinking tokens per call, 94 percent of its output), projecting 594 dollars against an approval of 139 and a gate of 174, so the batch was not started; the team took Flash with thinking off (0.167 per run, 106 output tokens per call, about 4 minutes per run instead of 28; the pilot and the grid therefore differ in configuration, and a provider-options column was added to every row in Phase 9). All four first-smoke runs also failed on a latent runner defect (a deep copy of a live client holding a thread lock, after all 200 decisions and a complete log), fixed. The known-answer validation of the sizing plug-in, done before any pilot number was read: the registered bootstrap upper limit covers the true sigma_d only 60 to 67 percent of the time whenever a seed-by-arm term is present, so the grid would have been sized too small in up to 40 percent of datasets; a closed-form limit covers 0.915 to 0.945 and sizes the grid.

Results: 720 runs, 0 failures, 1 parse fallback, 0 provider fallbacks; spend 144.66 dollars of the 151 approved (Flash 96.69, GPT-5 mini 47.97). Flash's band-MAS sigma_d (the sd of one seed's memory minus static difference) at one replicate is 0.0348, with a 90 percent closed-form limit of 0.0380; 65 to 83 percent of the variance is seed-by-arm interaction rather than decode noise, so replicates buy little and the grid runs one replicate. Sized on Flash alone: 19 seeds per persona and scenario cell at the Bonferroni alpha of 0.05 / 36 for a minimum effect of 0.05 band-MAS. The transfer: GPT-5 mini's sigma_d is 2.214 times Flash's [1.878, 2.993] on the bull trap, and the excess is seed-by-arm variance (5.2 times), not replicate noise (1.35 times), so temperature does not explain it. Plug-in 0.0380 x 2.214 = 0.0841 and **93 seeds per persona and scenario cell** (47 under the paired-correct formula; 169 at the ratio's upper limit). At the plan's Tier A of 5 seeds the minimum detectable difference on band-MAS is 0.097, twice the effect of interest. One contrast in this shape costs about 367 dollars on Flash and 735 on GPT-5 mini.

![Figure 29](figures/F21_variance_components.png)

*Figure 29. (a) sigma_d at one replicate per metric and model, with its one-sided 90 percent upper limit; (b) the share of that variance that is seed-by-arm interaction rather than decode noise. Flash 96 pairs (thinking off), GPT-5 mini 24 pairs (bull trap only, temperature 1).*

**The L3 probe**, run here on five models (200 probes, a normal and a shuffled-V arm): every model is at chance (sign accuracy 0.475 to 0.530) against the level-free surrogate's 0.780 [0.718, 0.832], because 93 to 99 percent of every model's answers follow the rule "over-valued if the price is above the analyst estimate", a rule whose own accuracy is 0.520; Flash and GPT-5 mini gave identical answers on all 200 probes. The first run had read two Claude models' rejection of the temperature parameter as a PASS (800 HTTP 400 errors), and GPT-5 mini had run at temperature 1.0 because its client drops any other value; the false PASS and a truncation of thinking blocks were fixed, and the temperature column records the values actually run.

### 15.3 Settings at the hand-over

The harness version (v2 default; the corrected version for the main grid); the offset definition (nearest copy primary, system copy beside); the injected block rendered empty in retained turns; the fallback history text; the token-count hierarchy; the context window 20 (DESIGN) with levels {5, 20, 50, full} as the factor; the 60,000-token budget (DESIGN, holds 77 to 80 turns); the summariser constants (DESIGN); the matched placebo; temperature 0.2 (the gpt-5 models run and log 1.0); three parse retries. Inference: the minimum effect 0.05 band-MAS with no stipulated D effect (achieved power reported); the sigma_d plug-in as a one-sided 90 percent closed-form limit; pairing by seed on replicate means; alpha 0.05 Bonferroni within the confirmatory family; power 0.8 with the plan's formula as written and the paired-correct count beside it; metric tiers C {band-MAS, D at 0.05, D at 0.002}, S {turnover, drawdown, return} and descriptive; Benjamini-Yekutieli across families; the sign-flip temporal null; the two-way cluster bootstrap deciding; the crossed mixed model descriptive; the variance-pilot design and the transfer rule; 93 seeds per cell; the cost gate. Freeze unchanged (30 files); 0 of 95 path hashes changed. Tests: 28 new in the tree run, a 29th added to the file after it. Whole suite: 219 passed, 1 skipped, 4 expected failures, 0 failed.

### 15.4 Results that contradicted expectations (19 recorded)

The cost gate triggered at 594 against 174 dollars. No interval estimator holds size at three models when the arm effect varies by model. The registered day-block null over-rejects. The registered bootstrap limit under-covers. The pilot's variance sits in persona by path, which neither the registered model nor the crossed model carries. The salience identification condition was unsatisfiable as registered, and its bootstrap leaked. The probe's tool read rejections as passes. GPT-5 mini's temperature contingency triggered silently (the client drops any value but 1). The execution prompt's "about 77 tokens away" was the block's own size, not the distance. The "full" window holds 80 turns, not 65.

---

## 16. Phase 9: sensitivity through the LLM harness

### 16.1 Goal and the constraints that changed under it

The plan's Phase 9 sweeps the generator parameters that drive results through a small LLM grid. What the phase did: it timed and smoked every candidate model, simulated the reference distribution for model-level contrasts and the three robustness criteria before any grid run, computed the parameter ranking that the plan asked for and that no earlier phase had produced, piloted every roster model to measure its own noise, sized the grid, and specified the grid and its robustness table for execution as the benchmark's main experiment on the finished environment. The constraints moved twice: the team first stated that cost was not a constraint and that wall-clock time bound at 10 to 15 concurrent calls per model; then, when the Anthropic account ran out of credit in the middle of the pilots, the phase was given one budget of 300 dollars of OpenRouter credit and no Anthropic credit at all, which dropped Claude Sonnet 5 and Opus 5, represented Claude by Haiku 4.5 through OpenRouter pinned to the Anthropic upstream, and added four open-weight models through the same key.

Found before any rule was written: the ranking the plan needed had never been computed; the plan's parameter levels predated the fits (half-life 60 / 250 days where 22.38 [18.75, 32.64] is in force; analyst sd 0.15 / 0.45 where 0.564 is); Phase 7's scripted policies were keyed on a salted string hash and were not reproducible across processes; the plan's "60 + 60 runs" for one experiment did not match its own factor list. Stage 1 of the grid as first designed (Phase 8's confirmatory sizing, 12 models, the common-start slice) priced at 126,000 dollars against the plan's own 210 for its first tier and was withdrawn; the phase's questions are within-design comparisons on shared seeds (sign stability, an interaction interval, an equivalence margin), sized by the criteria stage.

### 16.2 Work carried out

**Throughput and the smokes.** Every roster configuration was timed from the run ledgers (two in batch from the variance pilot, the rest by two-run smokes): seconds per 200-call run from 227 (Gemini 2.5 Flash-Lite) to 3,240 (Gemini 2.5 Pro), set by the reasoning tokens a default configuration spends (0 per call for Flash-Lite, GPT-5.4 mini and Haiku 4.5; up to 2,012 for GPT-5 nano, whose runs spend up to 494,208 reasoning tokens). At 15 concurrent calls the 12-cell headline at 93 seeds takes 0.4 to 5.6 days per model; the roster's clock is its three slowest members. Every model runs its provider's default except Flash with thinking off. The five OpenRouter configurations were smoked twice: the first smoke ran without a cap on the output tokens and is discarded (OpenRouter reads an absent cap as the model's full context window and one upstream rejected every one of Qwen3 235B's 400 calls); under the registered cap of 8,192 Haiku 4.5, Qwen3 235B and DeepSeek V4 Flash parsed 200 of 200 in both runs, while Qwen3.7 Flash (4,973 seconds per run uncapped, 17.7 hours for a pilot at the concurrency cap) and GLM 4.7 Flash (173 minutes without finishing a run) failed a stopping rule registered before the capped smoke was launched. Routing was audited by generation identifier: every sampled call was served by the pinned upstream on the expected snapshot; a pin with fallbacks disabled fails closed (HTTP 404), while with fallbacks allowed the same request was served by another upstream, the drift the pin exists to prevent; cost is read from the provider's own accounting.

![Figure 30](figures/F22_throughput_per_model.png)

*Figure 30. Mean minutes per 200-call run for every configuration piloted in Phase 9, measured on the pilot batches, with the number of runs and the reasoning tokens per call; provider defaults throughout (Gemini 2.5 Flash with thinking off was timed in Phase 8 and is not drawn).*

**The reference distribution for model-level contrasts.** Four registered candidates (a normal reference; a t reference; Phase 8's two-way bootstrap; a two-way random-effects variance with Satterthwaite degrees of freedom) were simulated on 48 null conditions per roster size at 10,000 datasets each (the bootstrap candidate on 8 conditions per roster size at 1,000 datasets of 1,999 resamples): **the registered recommendation rule recommends none** at any roster size, and it is unmeetable by construction (an exactly sized test breaks it with probability 0.93). A fifth candidate, R5 (the two-way random-effects variance referred to a t distribution with M minus 1 degrees of freedom), was registered after the four were read, judged only on fresh datasets (864 conditions x 10,000), holds size at alpha everywhere (at most 0.055) and breaks at the Bonferroni alpha only as an exactly sized test would; **the team chose R5.** Model-level power depends on the between-model sd of the arm effect far more than on the seeds: at 93 seeds it is 1.00 at half of Flash's sigma_d limit and 0.61 at the limit with 12 models (0.76 with 14).

**The three robustness criteria** of the plan, given their missing constructions in the addendum before the stage produced a number, then simulated on 432 conditions x 2,000 datasets at the design's shape (12 non-default levels, 93 seeds; equivalence margin 0.025, half of the minimum effect). Two of the three do not behave as the plan assumes: (i) the sign criterion as the plan writes it ("the sign of the arm contrast is unchanged across all levels") falsely declares a conclusion level-dependent up to 0.241 of the time when the effect is identical at every level (and about 0.60 when there is no effect at all, since the sign of noise is random), while a significant-only reading of the same sentence reaches at most 0.008; (ii) requiring every level to clear the Bonferroni alpha holds 0.03 to 0.05 of the time at 6 models against 0.58 to 0.63 at 14, and seeds barely move it; (iii) the equivalence interval has power 0.993 to 1.000 when there is no level-by-arm-by-model term and 0.086 to 0.668 when there is one at half the measured spread, with false equivalence at the margin at most 0.095. Nothing was re-registered after these were read; both readings are reported, and the team's choice between them is recorded in 16.3.

![Figure 31](figures/F25_reference_distribution_and_criteria.png)

*Figure 31. (a) and (b): the size at alpha and the power at the Bonferroni alpha of the candidate reference distributions for model-level contrasts against the roster size; 10,000 datasets per condition. (c) The three robustness criteria against the roster size at the design's shape; 2,000 datasets per condition.*

**The parameter list.** 21 candidate parameters, each at two levels against the default, on panels of 100 seeds x 4 scenarios x 3 personas with the stored Phase 6 oracles and Phase 7's scripted families; the reference rows reproduced first (the default panel's flat regret 0.07701 against the published 0.0770; 2,400 rows to 3.6e-16). Ranked by the cell-mean standardised effect on the level-free oracle's regret and on the scripted policies' band-MAS, with a 1,000-resample seed bootstrap for the stability of the top six:

| Candidate | In the plan's six | Effect on the oracle | Effect on the scripted policies | Rank sum | Top-six share |
|---|---|---|---|---|---|
| GARCH set | yes | 0.096 | 0.086 | 2 | 1.000 |
| sbar | no | 0.050 | 0.055 | 6 | 0.999 |
| mu_V | no | 0.046 | 0.041 | 9 | 0.934 |
| Half-life | yes | 0.032 | 0.054 | 12 | 0.999 |
| Jump rate | no | 0.037 | 0.016 | 12 | 0.638 |
| sigma_V | yes | 0.026 | 0.056 | 12 | 0.992 |
| Jump size | no | 0.025 | 0.009 | 18 | 0.323 |
| P/E dispersion | yes | 0.033 | 0.000 | 19 | 0.068 |
| Dividend speed | no | 0.056 | 0.000 | 19 | 0.004 |
| Analyst sd | yes | 0.027 | 0.000 | 22 | 0.011 |
| Sentiment loading | yes | 0.006 | 0.002 | 23 | 0.008 |

The data-driven six (the GARCH set, sbar, mu_V, the half-life, sigma_V, the jump rate) share only three parameters with the plan's six where the plan's rule asks for five, so **the data-driven six run**; the sixth place is not sharp (the jump rate at 0.638 against the jump size at 0.323). Three reviewer-named parameters fall out (the P/E dispersion, the analyst sd and the sentiment loading each move the scripted policies by at most 0.002); these outcomes contain no LLM, and a parameter that ranks low here and moves LLM behaviour in the grid would be evidence about the models, which the pre-registration stated in advance (every model in the L3 probe answered by reading the analyst field). One level (the 75th-percentile GJR set) leaves 4.25 percent of path and persona cells with no resolvable day at theta 0.05, so MCR is undefined there; the tool had handled the undefined cells in two different ways (the point estimate silently rested on the other level, the bootstrap propagated the missing value and gave a top-six share of 0.000 for the parameter ranked first); a pairwise-complete handling was registered before the statistic was recomputed, which moved the GARCH set's oracle effect from 0.066 to 0.096 and its share to 1.000 without changing the six. The half-life levels were run at a matched sd of x, which the registered construction lands within +5.3 and +0.8 percent of its target and which was applied once, not iterated.

![Figure 32](figures/F24_parameter_ranking.png)

*Figure 32. The standardised effect of each generator parameter, the larger of its two registered levels' effects against the default, on the level-free oracle's regret (blue) and on the scripted policies' band-MAS (orange), with 95 percent bootstrap intervals; the six swept are in colour, the rest greyed; the label gives each parameter's share of bootstrap resamples in the top six. 100 seeds per panel; 1,000 resamples.*

**The roster pilots.** The shape by the registered rule: 16 seeds per cell at one replicate, 384 runs per model (180 degrees of freedom for sigma_d). Six first-party models completed the 384 (Flash-Lite, Gemini 3.5 Flash, GPT-5 mini, GPT-5, GPT-5.4 mini, GPT-5.5); two were stopped on a clock registered as a wall-clock rule rather than on their numbers (Gemini 2.5 Pro 279 runs, GPT-5 nano 281; the addendum discloses that an interim sigma_d table had already been read and shows that neither was near the maximum); four Claude models were stopped by the credit failure (Haiku 252 runs, Sonnet 158, Opus 110, Fable 93; 294 runs failed whole with a "credit balance too low" error and were discarded by the contamination rule, none partially entering the data) and then dropped or re-routed; the three OpenRouter configurations were piloted to completion on truncated seed lists registered before they started (Haiku 4.5 192 of 192 runs, DeepSeek V4 Flash and Qwen3 235B 96 of 96), with one contaminated Haiku run discarded and re-run. Flash is exempt because its prompts equal the variance pilot's. The direct-API and OpenRouter Haiku pilots agree on the 64 cells they share (mean difference minus 0.0013 against minus 0.0002, sd 0.0219 against 0.0224), and a naive comparison of the two would have been wrong because the direct pilot covered only 8 of 12 persona and scenario cells; the two routes are not pooled. Provider errors: 36 HTTP 403 responses in 76,808 pilot calls (0.047 percent), all on the Anthropic upstream.

| Configuration | sigma_d (R = 1) | 90 percent limit | Pairs |
|---|---|---|---|
| gpt-5-nano | 0.0154 | 0.0168 | 128 |
| gemini-2.5-flash (thinking off; variance pilot) | 0.0348 | 0.0380 | 96 |
| gpt-5 | 0.0381 | 0.0409 | 192 |
| gemini-2.5-flash-lite | 0.0415 | 0.0446 | 192 |
| qwen3-235b-a22b-2507 (OpenRouter) | 0.0445 | 0.0528 | 48 |
| gpt-5.5 | 0.0533 | 0.0572 | 192 |
| gemini-3.5-flash | 0.0547 | 0.0588 | 192 |
| gemini-2.5-pro | 0.0540 | 0.0590 | 128 |
| claude-haiku-4.5 (OpenRouter) | 0.0556 | 0.0618 | 96 |
| gpt-5-mini | 0.0595 | 0.0639 | 192 |
| gpt-5.4-mini | 0.0670 | 0.0720 | 192 |
| deepseek-v4-flash (OpenRouter), the plug-in | 0.0809 | 0.0958 | 48 |

**The plug-in sigma_d is 0.0958**, from DeepSeek V4 Flash, the least-piloted model (its limit is widened by having only 48 pairs, the direction the truncation rule registered in advance: fewer seeds give a wider limit and a larger, more conservative grid), taken over 12 of 14 configurations; **stage 1's seed count by the plan's formula is 120** (60 by the paired-correct count), a lower bound on what the two unpiloted models might have given. Spend: 115.27 dollars debited (Haiku 106.68, DeepSeek 2.86, Qwen3 235B 2.30 by per-call accounting), 184.73 remaining of the 300; the 3.43 dollars between the debit and the per-call sum cannot be separated into discarded runs and accounting drift, so no figure is attributed to the discarded runs.

![Figure 33](figures/F23_sigma_d_and_pilot_completion.png)

*Figure 33. Per configuration: the band-MAS sigma_d at one replicate with its one-sided 90 percent limit (the plug-in is the maximum), and the runs completed against those planned for every pilot, including the four Claude pilots that stopped on the credit failure and size nothing. Pairs per configuration as labelled.*

**The grid and the robustness table.** No grid run was made; the manifest machinery was built and exercised on the three truncated pilot manifests, and a scoring stage for completed grid runs was added afterwards. The robustness table's columns and rules are fixed (one row per conclusion and generator parameter: the sign at each level under both readings; R5's p-value at each level with Benjamini-Hochberg within stage 1's family; the level-by-arm interaction's 90 percent interval on t(M minus 1); a verdict of robust, level-dependent or not equivalent, each criterion reported separately) and its operating characteristics measured, while the roster size and the reading of criterion (i) it uses are the team's decisions recorded in 16.3, and the grid run populates it.

**The switch and the tests.** A provider-options record on every run row (a Phase 8 gap): inert when off against the golden record. No parameter file and nothing in the generator, the evaluation layer or the agent changed; 0 of 95 path hashes moved. Whole suite: 239 passed, 2 skipped, 4 expected failures, 0 failed, run twice because the first run preceded the last documentation edits; both runs agree.

### 16.3 Decisions taken and the grid as specified

The team's decisions: the constraints (cost first not a constraint, then the binding one); the roster of 13, then 12 after Claude Fable 5.1 was excluded on cost (9.01 dollars per run, 57 percent of the Anthropic bill on its own), then 14 under the 300-dollar budget (a relay endpoint offered by a colleague was rejected because a call through it cannot be attributed to a named model on a first-party account); a staged grid, headline first; R5 as the reference distribution; provider defaults; the data-driven six; the criteria left as registered; two open-weight models dropped by the smoke rule.

Two choices were referred to the team by the phase and decided afterwards on the simulations. The sign criterion uses the significant-only reading as its headline: the plain reading of the plan's sentence declares a conclusion level-dependent up to 0.241 of the time when the effect is identical at every level, while the significant-only reading of the same sentence does so at most 0.008 of the time; the plain reading is reported beside it because it is the plan's sentence. The roster is the twelve piloted configurations, with fourteen if the two unpiloted models can be piloted: criteria (ii) and (iii) turn on the number of models and not on the seeds (criterion (ii) holds 0.03 to 0.05 of the time at 6 models and 0.58 to 0.63 at 14; model-level power at the sigma_d limit is 0.61 with 12 models and 0.76 with 14), so the grid runs on the largest roster the budget allows.

The grid runs in stages as the benchmark's main experiment on the complete and frozen environment: the headline contrasts first; then the common-start slice for the salience shares alone, the only design in which those shares are identified (3,720 runs per model at 93 seeds against the headline's 2,232); then stage 2's extensions, the context-length factor first because it carries the decay thesis, followed by the stateful arms, fixed-magnitude rendering and the phase-restatement side call. The robustness table is populated from the headline stage. Recorded for that run: Qwen3.7 Flash and GLM 4.7 Flash were dropped by the smoke rule; Sonnet 5, Opus 5 and Fable 5.1 have partial pilots that size nothing; the serving upstream is enforced at request time and audited out of band rather than recorded by the runner; and the Bonferroni alpha is re-read at the design's own family count before the first contrast is scored.

---

## 17. Current state of the environment

### 17.1 The generator in force

Every generator parameter in force after Phase 6 is unchanged by Phases 7 to 9 (0 of 95 path configurations moved in each). The table gives each block's value, its label and its evidence; every parameter is read from a parameter file by a loader that fails loudly if the file is missing or malformed.

| Block | Value in force | Label | Evidence |
|---|---|---|---|
| Value process | mu_V 0.000228 / day; sigma_V 0.01457 [0.01275, 0.01527]; t5 shocks | FIT; FIT conditional on the engine and the volatility block; DESIGN | the nominal index 2000 to 2024 (300 months); the constrained engine refit (30 refits, 417 stocks) |
| Start price | mechanism C: a hidden start of 100 with a per-seed render scale on 7.47 to 240.02 dollars | DESIGN (mechanism); FIT (range) | the attacker and rule-100 tests at 2,000 paths; the range from 16,680 closes |
| Jumps | mean zero in x; rate 0.000583 / day [0.00046, 0.00082]; size sd 0.230 [0.086, 0.241]; announcement share 0.4345 | FIT, weakly identified | 2.6 million stock-days for the rate and size; the announcement share from 7,492 jump days on 1.67 million stock-days |
| Burn-in | 750 days (default engine); a stored state plus 60 days (sensitivity engines) | FIT / DESIGN | 2,000 paths per engine |
| Engine | AR(1) with a GJR-GARCH-t innovation; half-life 22.38 days [18.75, 32.64]; price scale 1 | FIT decision; FIT; LIT | 17 moments on 417 stocks; the paper's equation (1) |
| Volatility | alpha 0.027, gamma 0.058, beta 0.932, degrees of freedom 6.65; sbar 0.01509 [0.01342, 0.01678] by the variance identity to an unconditional daily return sd of 0.0218 | FIT | 417 per-stock fits; the identity |
| Phase multipliers | targets 1.37 / 7.45 / 3.11 / 1.18 / 1.65 / 1.16 (deterioration, panic, stabilisation, mania, blow-off, post-top); x-innovation multipliers 1.35 / 16.17 / 5.63 / 1.35 / 2.076 / 0.35; sustained bull 1.0 | FIT; closed-loop CAL; DESIGN | 1,592 drawdowns, 3,125 run-ups |
| Implied volatility | a past-only GJR filter; premium minus 2.2 percent; AR(1) noise (0.926, 0.083); no floor | FIT | five single-stock volatility indices, 17,570 days |
| Event schedule | deterioration, panic, front-loading, depth (centred on the arm's delta), recovery, post-top drop and length from fitted quantile grids; the fundamental decline uniform on 10 to 30 percent; setup 25 to 55 percent of the horizon | FIT; DESIGN | 642 fast crashes; 3,201 run-ups |
| Bubble | hazard h0 6.712e-4, b 5.419, drift cap 0.012 (in force, adoption withdrawn); a real-time blow-off label at a drift of 0.00984; a post-top decay with a 40-day half-life; a mania drift uniform on 0.02 to 0.04 (the fitted value of 0 recorded beside it) | FIT / CAL; FIT; CAL; DESIGN | 500 to 1,500 seeds per arm |
| Sustained-bull control | definition A: the flat mispricing process, validity on V only | ADOPTED (team decision) | 500 seeds per definition; 800 deployed |
| Event dynamics | formulation A, panic gain 0.10 | DESIGN (team decision; 17.3) | 2,000 seeds x 7 arms; the best coverage of the panel's depth-by-duration box among four formulations |
| Calendar | "Day-N"; the earnings-quarter grid randomised per seed; setup-first with an ordering factor available | DESIGN; MEASURED | 200 seeds, 200 permutations |
| P/E multiple | a between-stock log grid (P/E 5.77 to 39.98) plus a within-stock daily AR(1) at 0.99661 | FIT | 411 stocks, 61,843 stock-months |
| Earnings | noise 0.1707; loss quarters 9.7 percent with persistence; cap 191.5; announcement lag 10 to 30 trading days; "n/m" for non-positive trailing EPS | FIT | 27,515 quarters; 27,242 filings |
| Dividends | Lintner speed 0.697, target payout 0.406, payer share 0.887; paid into cash on announcement days; field shown | FIT (process); team decision (paid) | 417 names; 10,666 stock-years |
| Analyst estimate | design C: the 250-day price average times an error of sd 0.564 (rho 0.95 per weekly update); field shown | LIT + DESIGN, ADOPTED (team decision; 17.3) | five arms x 1,600 paths |
| Sentiment | design A, returns only: rho 0.211, loading 0.111, residual 0.972; predictive size 0.0008 (LIT) | FIT, ADOPTED (team decision; 17.3); the B variants as sensitivities | the deconvolved news-sentiment index; 57 windows |
| Volume | design A: rho 0.526, loading 0.203 on the absolute return, residual 0.347 | FIT | 417 stocks |
| Audit criteria | the reference distribution of every checklist statistic (12,927 windows); criterion B (a Kolmogorov-Smirnov distance below 0.10 at 500 seeds per scenario) and C (the share in band); the L1 ceiling 0.617; the L2 and L2b margins as registered (negative) and centred | FIT; DESIGN / DERIVED | Phase 6 |

The generator is frozen under a hash manifest of 30 files, and every run row carries that hash.

### 17.2 The scoring and the harness in force

| Setting | Value in force | Label |
|---|---|---|
| Resolvability theta | co-primary 0.002 (cost) and 0.05 (information); the grid {0.03, 0.05, 0.08, 0.12, 0.20} as sensitivities | DERIVED; the grid and the pair in force REGISTERED |
| Regret | MCR = B + D on resolvable steps; ceiling the mandate-conditional oracle (0.0028 realised); floor the worst of six trivial policies | REGISTERED |
| G3 | theta-conditional: passes at theta up to 0.05, fails from 0.066 | team decision |
| Band half-width, dead band, cost | 0.10; 0.01; 5 bp per trade | DESIGN |
| Bands | 0.70 to 0.90 / 0.40 to 0.60 / 0.00 to 0.20 cash (scored); the Merton reading reported | READ |
| Dividends | paid into cash | team decision |
| Day-1 gate | common start only; its null NOT COMPUTABLE under the NONE reference alone | re-specified |
| Harness | the corrected version for the main grid: nearest-copy mandate offset, no replayed block, "no valid answer" fallback, the token hierarchy; the matched placebo | REGISTERED |
| Context length | 20 turns default, levels {5, 20, 50, full (77 turns under the corrected harness)} as a factor; a 60,000-token budget | DESIGN |
| Temperature | 0.2 (the gpt-5 models 1.0, logged) | DESIGN |
| Provider configuration | every model at its provider's default, Gemini 2.5 Flash with thinking off; OpenRouter routes pinned to one upstream with fallbacks disabled and an output cap of 8,192 tokens; the configuration logged per row | team decision |
| Minimum effect | 0.05 band-MAS; equivalence margin 0.025 | team decision |
| Sizing rule | one replicate; seeds per persona and scenario cell from the maximum one-sided 90 percent limit of sigma_d over the roster (93 on the Phase 8 transfer; 120 on the Phase 9 pilots) | MEASURED |
| Inference | R5 (a two-way random-effects variance on t(M minus 1)) for model-level contrasts; the two-way cluster bootstrap for arm contrasts; the crossed mixed model descriptive; Benjamini-Hochberg within one family, Benjamini-Yekutieli across families; the path-level sign flip for temporal claims | MEASURED; R5 by team decision |

### 17.3 Positions held by design, with their basis

Every parameter above is fitted, derived or a design choice carrying its evidence, and the generator is frozen: no parameter moved in Phases 7 to 9. Six positions are held by design rather than by a fit, because the data or the registered criterion could not decide them; the team adopted each of them on the evidence stated here. The parameter files keep the labels registered at the Phase 6 freeze, and the adoptions recorded here are the team's decisions on that frozen state.

- **Event dynamics.** The generator runs formulation A, the error-correction gain of v2, at a panic gain of 0.10. Four formulations were compared at 1,000 crash seeds each. A's coverage of the panel's depth-by-duration box, 0.47 to 0.56 across its gains, spans the best of the four (a shifted target 0.52, a fully scripted move 0.46, an unscripted regime switch 0.32), and the gap to the panel's own self-coverage of 0.64 is traced to the stipulated fundamental decline that floors the crash depth, not to the formulation. The registered threshold of 0.70 sat above what the panel achieves on itself and the script-share statistic does not rank formulations, so the comparison, not the rule, is the basis of the position. The team adopted formulation A as a design choice.
- **The mania drift.** The bull-trap scenario draws its mania drift uniformly from 0.02 to 0.04 (DESIGN). The panel's run-ups decelerate on average (the last third's log gain is 0.342 [0.318, 0.368] of the first third's, over 3,186 run-ups), so a fitted super-exponential drift is zero, and a zero drift cannot produce the scenario: 96.3 percent of draws fail the bull-trap validity criterion. A bull trap is a stress scenario, a run-up that tops, and not the average run-up; the team adopted the range as a scenario parameter, with the fitted value recorded beside it.
- **The analyst estimate.** Design C, the 250-day price average times an error of sd 0.564, is the field shown. It is the only construction that passes the onset audit at all six phase transitions, and it carries nothing about the mispricing (an add-one R-squared of minus 0.001 on all rows and +0.010 calm-trained). Whether the field is shown at all is a factor of the LLM grid rather than of the environment: the L3 probe found every model reading its answer off this field (93 to 99 percent of answers follow the rule "over-valued when the price is above the estimate"), so showing and hiding it measures the models. The team adopted design C, with the shown-or-hidden switch added to the grid's factor list.
- **Sentiment.** Design A, driven by returns only, is the default; the valuation-link variants B are sensitivities. A was selected by the registered rule (an add-one selectivity of minus 0.0007 against +0.0205 and +0.0813 for the two B variants). Its realised next-day return loading is 0.00055 [0.00046, 0.00063] against a configured 0.0008, the field's own persistence absorbing the rest; the configured value is a literature number that the free data source did not reproduce, so the realised loading is reported as the field's property rather than re-tuned to a target. The team adopted design A as the default, with the B variants carried as grid sensitivities.
- **The crash rise time and the topped share.** Both are reported as properties of the scenarios rather than as criteria. The generator's onset-to-volatility-peak rise time is 58 days [52, 64] against the panel's 30 [29, 35], and the lever is the setup length: a 13-day setup meets the panel's value (37 days [34, 41]) but leaves no pre-event baseline on a 200-day horizon, so the setup range stays. The topped share is horizon-dominated: only 0.9 percent of generated topped paths have 120 days after the top, and on comparable windows the generator and the panel agree (0.025 against 0.029 with 0 to 50 post-top days). The team retired both as generator criteria and keeps them as reported properties of the scenarios.
- **The two derived leakage margins.** The fields' calm-trained contribution to predicting the mispricing (+0.109 of R-squared against a derived margin of +0.038) and the phase clock's selectivity (+0.030 against +0.011) are registered as residuals and are covered by the decision, taken in Phase 7 before any experiment, to restrict the benchmark's claim to a one-shot mandate-conflict benchmark. The two v1 baselines stay in the registry as permanent references. The two residuals are to be stated in one sentence in the paper's limitations: the fields add about 0.10 of calm-day predictability beyond the price path, and the phase clock adds 0.03.

The LLM grid that runs on this environment is specified and sized (section 16), and the team's decisions on its analysis are recorded there: the significant-only reading of the sign criterion as the headline, the twelve piloted configurations as the roster (fourteen if the two unpiloted models can be piloted), the common-start slice as a stage after the headline for the salience shares alone, and the context-length factor as the first of stage 2's extensions. Its execution is the benchmark's main experiment, and the environment it runs on is fixed: the parameter files, the freeze manifest and every path hash are the ones recorded above.

---

## Appendix A. The parameter ledger across versions

Only parameters that changed value or label are listed; "same" means the value was carried over with its label re-derived.

| Parameter | v1 | v2 | v2.1 in force | Phase |
|---|---|---|---|---|
| Price model | value plus dollar noise | log P = log V + x | same | |
| Mispricing engine | none (noise) | Franke-Westerhoff fallback, phi 0.4632, half-life 150 d, price scale 100 | AR(1) with a GJR-GARCH-t innovation, half-life 22.38 d [18.75, 32.64], price scale 1 | 2, 3 |
| sigma_V | not applicable | 0.006 | 0.01457 [0.01275, 0.01527] | 1, 2, 3 |
| mu_V | | 0.00025 | 0.000228 [minus 0.000051, 0.000479] | 1 |
| Value shock tail | | t5 | t5 (DESIGN; tested against data) | 1 |
| Start price | 100 | 100 (an answer key) | mechanism C | 1 |
| Jumps | none | 0.010 / day, mean minus 4 percent, sd 3 percent, in x | 0.000583 / day, mean 0, sd 0.230, in x, with announcement clustering | 1, 3 |
| Burn-in | none | 260 d | 750 d | 1 |
| GJR-GARCH-t | none | 0.10 / 0.10 / 0.83, df 5, sbar 0.017 | 0.027 / 0.058 / 0.932, df 6.65, sbar 0.01509 | 3 |
| Phase multipliers | none (fixed phases) | 1.5 / 5 / 1.5 / 1.5 / 2 / 3 | 1.37 / 7.45 / 3.11 / 1.18 / 1.65 / 1.16 targets | 3 |
| Implied volatility | phase-driven | GARCH forecast, premium 0.20, stress 0.35, floor 12 | past-only filter, premium minus 2.2 percent, AR(1) noise, no floor | 3 |
| Crash phase lengths | fixed 80 / 60 / 60 | deterioration U(15, 40), panic U(15, 70) | fitted grids, medians 8 and 39 d | 4 |
| Crash depth | delta 0.85 / 0.92 / 0.95 on a fixed template | delta fixed per arm | a fitted depth grid centred on the arm's delta | 4 |
| Post-top | | a linear leg, drop U(0.30, 0.50), length U(10, 30) | a decay (40-day half-life), fitted drop and length grids | 4 |
| Hazard | none | 3e-4, 6.0, cap 0.012 (tuned) | 6.712e-4, 5.419, cap 0.012 (adoption withdrawn) | 4 |
| Blow-off multiplier | | 2.0 (dead code) | 2.076, real-time label | 4 |
| Sustained-bull control | none | anchored x, band, variance 1.0 | the flat process (A) | 4 |
| Calendar | fixed phases | "Day-N", fixed quarter grid | "Day-N", quarter grid randomised per seed | 4 |
| P/E multiple | a constant times P / V (an exact leak) | k uniform on 14 to 22 | a between-stock grid 5.77 to 39.98 with within-stock persistence | 5 |
| Earnings | | noise 0.10, lag 25 to 35 d, no losses | noise 0.171, lag 10 to 30 trading days, losses with persistence, cap 191.5 | 5 |
| Dividends | | payout 0.35, stickiness 0.7, not paid | speed 0.697, target 0.406, payer share 0.887, paid into cash | 5, 7 |
| Analyst estimate | | V times an error of sd 0.15 (0.335 implemented) | the 250-day price average times an error of sd 0.564 | 0, 5 |
| Sentiment | i.i.d. within phase | mean 0.6 tanh(2x) + 0.3 tanh(ret20 / 0.15), AR 0.85 | a returns-only AR(1): rho 0.211, loading 0.111 | 5 |
| Volume | phase-driven | AR 0.65, 0.25 on the absolute return, 1.2 on absolute x | AR 0.526, 0.203 on the absolute return, no x term | 5 |
| theta | none | 0.05 stated | 0.002 and 0.05 co-primary, derived | 7 |
| Regret metric | RG, point-MAS | MCR against a mislabelled floor and ceiling | MCR = B + D against the mandate oracle and the worst trivial policy | 7 |
| Start allocation | 100 percent cash | a factor (own centre primary) | same, with the day-1 gate on the common start only | 7 |
| Checklist criteria | v2 rules | v2 rules | the reference distribution of 12,927 real windows; B decides at 500 seeds | 6 |
| Leakage gates | a 1 percent floor; absolute R-squared limits; a 10-point clock margin | same | a derived L1 ceiling (0.617); permutation-null margins for L2 and L2b | 6 |
| Mixed model | none | nested, intercepts only | the crossed model descriptive; the two-way bootstrap and R5 decide | 8, 9 |
| Multiplicity | none | BH across seven metrics | BH within a family, BY across families | 8 |
| Grid size | about 5 seeds | Tier A, 5 seeds | 93 seeds per cell (Phase 8); 120 (Phase 9 pilots) | 8, 9 |

## Appendix B. List of figures

| Figure | Title | Data |
|---|---|---|
| 1 | The leakage audit by version | the L1, L2 and L4 audits, v1 to Phase 6 |
| 2 | The v1 day-1 separability gate per model and arm | 2,658 v1 runs, 18 models |
| 3 | The three estimators and the engine refits | 417 stocks; the Phase 2 and 3 refits |
| 4 | The variance-ratio curve | 417 stocks |
| 5 | The start-price mechanisms | 2,000 paths per mechanism |
| 6 | The sigma_V by s_x sweep against the Kalman bound | 40 points, 200 seeds per scenario |
| 7 | The candidate engines' fit and held-out check | 417 stocks, 2000 to 2024 |
| 8 | The bias of the naive half-life estimator | a pure AR(1), 200 seeds per cell |
| 9 | The persistence sweep | 200 seeds per scenario and level |
| 10 | The per-stock GJR-GARCH-t fits by period | 417 stocks |
| 11 | Jump detection and the implied-volatility transition step | 2,622,096 stock-days; 50 and 200 crash seeds |
| 12 | The phase multipliers, target and realised | 1,592 and 3,125 episodes; 200 seeds |
| 13 | Crash depth against duration, panel and generator | 1,789 episodes; 364 and 380 generator crashes |
| 14 | The event-dynamics formulations against the coverage rule | 1,000 seeds per formulation |
| 15 | The observable processes, data against the v2 assumptions | 411 tickers; 10,666 stock-years; 417 stocks; 27,242 filings |
| 16 | The field-group ablation before and after Phase 5 | 1,600 paths, 288,000 rows |
| 17 | The onset audit by field and transition | 200 paths per transition; 500 shifts |
| 18 | The calm-trained surrogate at three hand-overs | 1,200 paths with calm rows |
| 19 | Policy spread at four hand-overs | 150 cells per state and scenario |
| 20 | Generator against the real reference distributions | 3,000 paths; 12,927 windows |
| 21 | The calm channel ladder against the bound | 200 paths per rung |
| 22 | The derived L2 and L2b null margins and the L1 ceiling | 1,600 paths |
| 23 | Checkpoint 16A | 100 seeds x 3 personas per scenario |
| 24 | Sign accuracy and coverage against theta | 1,600 paths |
| 25 | The Merton reading of the bands and the G3 profile | 500 flat seeds; 100 seeds x 3 personas |
| 26 | The metric correlation matrix and the scripted sweeps | 600 cells |
| 27 | The estimators' size and power on simulated data | 300 datasets per condition |
| 28 | Multiplicity procedures and temporal nulls | 5,000 and 1,000 replications |
| 29 | The variance components of the paid pilot | 96 and 24 pairs |
| 30 | Run time per configuration | 93 to 384 runs per configuration |
| 31 | The reference distribution and the robustness criteria | 10,000 and 2,000 datasets per condition |
| 32 | The parameter ranking | 100 seeds per panel |
| 33 | sigma_d per configuration and pilot completion | 48 to 192 pairs per configuration |
