# Pre-registration addendum — Phase 9

Every rule in `PREREG_PHASE_9.md` that proved wrong, and every check added after a result was read, is recorded here
with the disconfirmation stated as loudly as a confirmation. An item says what was registered, what was measured,
what is added, and when it was added relative to the numbers it could have been tuned to.

## 1. E9.3 `refdist`: the registered rule recommends no reference distribution at any roster size, and a fifth candidate is registered here, after R1–R4 were read and before it is simulated

**Registered (3.1).**

- **The rule:** a candidate holds size at M if its size's Wilson lower limit is ≤ α at both α = 0.05 and
  α′ = 0.05 / 36, in every condition at that M.
- **The recommendation:** the size-holding candidate with the highest power at α′ at τ = ½ × Flash's σ_d limit,
  S = 93, the model-specific reading and equal heterogeneity. If none holds, none is recommended and the table goes
  to the team.

**The bridge to Phase 8 passed** (`e9_3/bridge.json`). R3's size at M = 6, S = 19, τ = √2 × 0.03, on 2,000 datasets:

| reading | here [Wilson 95 %] | Phase 8's E2 row [Wilson 95 %] |
|---|---|---|
| shared | 0.098 [0.086, 0.112] | 0.090 [0.058, 0.138] |
| model-specific | 0.117 [0.104, 0.132] | 0.135 [0.094, 0.189] |

**Measured.** `e9_3/refdist.{csv,json}` has 864 conditions × 10,000 datasets; `e9_3/refdist_boot.{csv,json}` has
64 conditions × 1,000 datasets, B = 1,999. **Recommended: none, at every M from 2 to 14.** Every candidate fails
somewhere:

- **R1, normal.** Fails everywhere. At α = 0.05 its size reaches 0.76 (shared reading, τ = 0, M = 14).
- **R2, t on M − 1 df on the per-model means.**
  - Holds in the model-specific reading when τ > 0.
  - Fails in the shared reading when the per-model effect is small. At τ = 0 its size rises from 0.13 at M = 2 to
    0.74 at M = 14: the shared path × arm and persona × path × arm terms move every model's mean together, and the
    spread of the M means cannot see them.
  - Fails in the model-specific reading at τ = 0 from M = 8 (0.079–0.105), for the same reason through the shared
    path × arm term.
- **R3, the two-way cluster bootstrap (E2).**
  - At τ = √2 × 0.03, its size is 0.065–0.249 at α and **0.008–0.170 at α′**, against 0.00139.
  - At τ = 0 it is conservative.
  - This is P8-17's finding at the sizes and roster candidates of this phase.
- **R4, two-way random-effects ANOVA with Satterthwaite df.**
  - Holds at α = 0.05 from M = 4.
  - At α′ it over-rejects when τ > 0 at small M. The largest Wilson lower limit over conditions is 0.075 at M = 2,
    0.025 at M = 3, 0.011 at M = 4 and 0.0055 at M = 5.
  - It stays marginally above α′ in some conditions up to M = 14 (lower limits 0.0012–0.0019). The Satterthwaite df
    is dominated by the path mean square and overstates the model-level df that governs a contrast when τ > 0.

**Reading, as registered.** No validated reference distribution holds size at α′ in every condition the grid could
be in. The table goes to the team (section 5 of the report).

**Added here — R5, before it is simulated.** R5 refers R4's variance to t with the model-level df:

Var(d̄) = max(MS_M + MS_S − MS_E, MS_E) / (M S),   with d̄ / √Var against t(M − 1).

- **Why this form:** its variance carries the shared path term that R2 lacks, and its df is the number of
  model-level draws that governs the contrast when the arm effect varies by model. R4's Satterthwaite df does not.
- **It was chosen after R1–R4's rates were read.** It is therefore judged only on **fresh datasets**: stage
  `refdist_fresh`, stream [9, 3, 5, key], sharing no draw with `refdist`'s [9, 3, 1, key]. The 864 conditions are the
  same, with 10,000 datasets each.
- **R1, R2 and R4 are re-run on the same fresh datasets**, so their rates are replicated on independent data. R3 is
  not re-run.

**The outcome is reported twice:**

- the registered rule on {R1, R2, R4} and R3's subset;
- the same rule with R5 added, labelled as this addendum's.

**What R5 is expected to cost.** In the model-specific reading at τ > 0 its power should be close to R2's, since both
refer to t(M − 1) and the path term is small. At τ = 0 it is conservative, because the t(M − 1) reference is wider
than the model count needs. If R5 also fails somewhere, the failure is located by condition
(`conditions_breaking` in the file) and reported. No threshold, df rule or further candidate is added after that read.

**Precedent, and how this differs.** P8-17's t reference was computed on the same cached estimates as the rates that
suggested it, and was not adopted. Here the candidate is registered first and tested on independent data.

### 1b. The outcome on fresh datasets (`e9_3/refdist_fresh.{csv,json}`, stream [9, 3, 5])

**R1, R2 and R4 replicate.** Their sizes at α on the fresh datasets are within 0.022 (R1), 0.016 (R2) and 0.017 (R4)
of the registered run in every condition. The registered rule again recommends none, at every M.

**R5.**

- **At α = 0.05 its size is at most 0.055** in every condition.
- **At α′ its Wilson lower limit exceeds α′ in exactly one condition at each of M = 6, 8, 10 and 12, and in none at
  M = 2, 3, 4, 5 and 14.** The breaking conditions are:
  - M 6: S 47, τ = √2 × 0.03, model-specific, equal heterogeneity;
  - M 8: S 47, τ = limit, model-specific, equal;
  - M 10: S 19, τ = √2 × 0.03, model-specific, equal;
  - M 12: S 93, τ = √2 × 0.03, shared, heterogeneous.
- Their lower limits are 0.0014–0.0015, against α′ = 0.00139.

**The rule applied with R5, as this addendum wrote it: R5 is recommended at M ∈ {2, 3, 4, 5, 14} and no candidate at
M ∈ {6, 8, 10, 12}.** R5's power at α′ at M ≤ 3 is ≤ 0.045 in every condition. A recommendation there is a size
statement, not a usable test.

## 3. The recommendation rule's own false-failure rate — a check registered here, after 1b was read and before it is computed

**Why it is needed.** The rule demands the Wilson lower limit be ≤ the nominal level in **every** null condition at
an M: 48 conditions per M for the analytic candidates, and 8 for R3. For a test whose true rejection rate is exactly
nominal, each Wilson 95 % lower limit exceeds the nominal level with probability of roughly 2.5 %. With 48 chances
per M, a perfectly sized test would then break the rule about once per M, which is 1b's pattern for R5. **If so, the
rule cannot be met by construction** in the way Phase 8's "the directive interval covers 0" could not.

**The check** (`tools/phase9/e9_3_simulate.py --stages rule_check`, exact binomial arithmetic, no simulation):

- for n = 10,000 (and n = 1,000 for R3), and a true rate equal to α and to α′, the probability that the Wilson lower
  limit exceeds the nominal level;
- the expected number of breaking conditions per M, and the probability of at least one, over the rule's condition
  count at both α levels (the conditions treated as independent);
- the same probability at true rates 1.1 × and 1.25 × nominal, so that the rule's power to catch a real excess is
  shown beside its false-failure rate.

**What it decides: nothing is re-read or re-adopted from it.**

- The registered rule's outcome (none) and 1b's outcome stand as reported.
- If the check shows the rule fails an exactly-sized test with probability above one half at 48 conditions, the rule
  is reported as **unmeetable by construction at this design's condition count**. The choice of reference
  distribution goes to the team with every candidate's located breaches and the check beside them.
- No replacement rule is adopted here.

**Result** (`e9_3/rule_check.{json,csv}`). The count threshold is the number of rejections at which the Wilson 95 %
lower limit exceeds the nominal level.

| candidates, datasets, null conditions per M | α | count threshold | P(one condition breaks), exact size | expected breaks per M | P(≥ 1 break per M) at 1 × / 1.1 × / 1.25 × nominal |
|---|---|---|---|---|---|
| analytic, 10,000, 48 | 0.05 | 543 | 0.027 | 1.28 | 0.73 / 1.00 / 1.00 |
| analytic, 10,000, 48 | 0.05 / 36 | 22 | 0.027 | 1.28 | 0.73 / 0.95 / 1.00 |
| R3, 1,000, 8 | 0.05 | 64 | 0.028 | 0.23 | 0.21 / 0.64 / 0.99 |
| R3, 1,000, 8 | 0.05 / 36 | 4 | 0.052 | 0.42 | 0.35 / 0.44 / 0.56 |

**An exactly sized analytic test breaks the rule at a given M with probability 0.93** (either α, 48 conditions).
**The recommendation rule of 3.1 is unmeetable by construction at this design's condition count.** Taken alone it
could never have recommended a correctly sized test.

R5's record in 1b is what an exactly sized test produces: one break at each of M = 6, 8, 10 and 12, and none at
M = 2–5 and 14. Every break is a lower limit within 0.0001 of α′.

The other candidates' breaks are not of that kind:

- R1: 48 of 48 at every M;
- R2: 12–32 per M;
- R4: 36 at M = 2 falling to 4 at M = 12–14;
- R3: its α′ rates of 0.008–0.170 against 0.00139 far exceed the 1.25 × column.

**As registered, the rule's outcome is "none"; this finding travels with it,** and the choice goes to the team with
the located breaks.

## 4. E9.1: one generator level makes MCR at θ = 0.05 undefined on 4.25 % of path × persona cells, and the tool handled it two different ways

**Registered (1.4).** E(ℓ, k, c) = |mean of the paired seed differences| ÷ the sd over seeds at the default; E(ℓ, k) is
the mean over the 12 cells; **E(j, k) is the maximum over j's non-default levels.** Nothing said what happens when an
outcome is undefined at a level.

**Measured.** In `panel_garch_set__high` (the P75 GJR-GARCH set), MCR at θ = 0.05 is NaN in 1,020 of 24,000 rows: all
20 policies of **51 path × persona cells** (17 seeds — 8 flat, 9 sustained_bull — × 3 personas), 4.25 % of the panel.
No other level, and not the default panel, has a NaN anywhere.

**Why.** The P75 set lowers x's dispersion, so some paths never reach the resolvability threshold and MCR at θ = 0.05
has nothing to average. On flat seed 21, |x| peaks at 0.0433 with **0 resolvable days** at θ = 0.05, where the same
path at the default has 20; sd(x) is 0.0143 against 0.0211. MCR at θ = 0.0020 (192 resolvable days) and band-MAS,
which averages over every day, are unaffected.

**The defect this exposed, in the tool and not in the environment.** The point estimate took Python's `max()`, which
returns the other level when one is NaN, and the bootstrap took `np.max`, which propagates it.

- The point estimate of `garch_set`'s oracle effect at θ = 0.05 silently rested on its **low level alone**.
- Its bootstrap top-six share came out as **0.000** although it ranked first on both outcomes — an artefact, not a
  finding.

**The handling, registered here before the statistic is recomputed** (the panels are unchanged; only the `rank` stage
re-runs):

1. **Pairwise-complete seeds.** In each cell, the paired difference and the default sd use the seeds where **both**
   the default and the level are defined. The seeds used are recorded per level, outcome and cell.
2. **A cell is used** if at least **50 of the 100** seeds are defined. A cell below that is dropped, and the drop is
   recorded.
3. **A level's outcome is NOT DEFINED** if more than **2 of its 12** cells are dropped. It is then excluded from the
   maximum over levels, loudly, and the exclusion is stored beside the parameter's effect.
4. **If every level of a parameter is undefined for an outcome**, the parameter is not rankable on that outcome. It is
   reported as such and ranked last on it, with the reason stored.
5. **One function computes the point estimate and every bootstrap draw**, so the two can no longer disagree.
6. **The maximum over levels ignores undefined levels explicitly**, never implicitly.

The thresholds in (2) and (3) are **DESIGN**: no data sets them. They are fixed here, before the recomputation, and
the counts they act on are reported whatever they are, so a reader can see how close any level came to them.

**Reported beside the ranking, as a result in its own right:** each level's share of path × persona cells with at
least one resolvable day at each co-primary θ, and its sd(x) and sd(r). A parameter that removes resolvable days has
changed what the benchmark can score, which is a finding about the environment, not a nuisance.

**What this cannot do.** It cannot recover the 51 cells. `garch_set`'s oracle effect at θ = 0.05 is measured on the
cells that remain, and its n travels with it.

**Result of the recomputation** (`e9_1/ranking.json`, the panels unchanged; only the `rank` stage re-ran):

- **No level is NOT DEFINED.** Every cell of `garch_set__high` keeps at least **91** of its 100 seeds (median 96),
  well above the floor of 50, so all 12 cells are used and the level enters the maximum as the rule intends.
- **The level's coverage is reported as its own result:** 0.958 of its path × persona cells have a resolvable day at
  θ = 0.05, against 1.000 everywhere else, with sd(x) 0.0740.
- **The correction moves `garch_set`'s numbers, not the decision.** Its oracle effect goes from 0.066 to **0.096**
  (its θ = 0.05 effect, 0.1139, is now in the maximum) and its bootstrap top-six share from 0.000 to **1.000**.
- **The six the rule selects are unchanged**, and so is the five-of-six verdict: three shared, so the data-driven six
  run (P9-6).

The fix is locked by `tests/test_v2_1_phase_9.py::test_effects_from_pairwise_complete_and_undefined`.

## 5. Two pilots are stopped on a clock, not on their numbers: a wall-clock truncation rule (TEAM, 12 Sep 2026)

**Registered (PREREG_PHASE_9.md 2).** Every piloted model runs 16 seeds per cell, 384 runs, df_d 180, and its
band-MAS σ_d(1) carries the chi-square one-sided 90 % limit at that df. The plug-in is the maximum over the roster.

**What happened.** Gemini 2.5 Pro and GPT-5 nano spend the most reasoning tokens per call of the roster (≈ 1,605 and
≈ 2,012), so a run takes ≈ 3,000 s against ≈ 1,700–1,825 s for the GPT-5 pair. At the cap of 15 in-flight calls per
model, their measured effective concurrency is 13.7 and 11.5, and their pilots had ≈ 9 h and ≈ 11 h left where the
rest of the roster was finishing.

**The rule the team took, and it references the clock only:** *the pilots of Gemini 2.5 Pro and GPT-5 nano stop two
hours from 12 Sep 2026 06:30 UTC, at whatever pairs they have reached.* Nothing in the rule refers to a measured
σ_d, a limit or a rank.

**Disclosure, because it matters for the limit's coverage.** An interim σ_d table had already been computed from the
runs on disk and read (section "interim" of `e9_2/sigma.csv`, written before this rule) while answering whether the
heavy models needed full pilots. **Stopping a measurement because of what its estimate shows would break the 90 %
coverage of its limit**, so the rule was fixed on the clock instead. What the interim table showed is recorded here
for the reader to judge:

- Gemini 2.5 Pro's interim band-MAS σ_d is 0.0564 (5th of 13) and GPT-5 nano's 0.0150 (13th of 13);
- the interim maximum is Claude Fable 5.1's 0.1082, on 29 pairs;
- neither truncated model is near the maximum, and nano's σ_d would have to rise about 6.5× to bind it.

**What truncation costs, and what it cannot cost.**

- The chi-square limit is a valid one-sided 90 % bound at any df, so a shorter pilot **widens** the limit; it never
  under-protects the design.
- At 12 seeds per cell the limit is 1.087 × the point estimate against 1.074 at 16, so stage 1 would take ≈ 2 % more
  seeds **if that model set the maximum**. Neither does on the interim table.
- Each truncated model's pairs, df and limit are reported beside every other model's, and its row says it was
  truncated.

**How the stop is made.** A timer stops those two runner processes and nothing else
(`e9_2/truncation_stop.log` records when it fired and which processes it stopped). Runs in flight at that moment
write no ledger row and use no attempt from the three the contamination rule allows, so a truncated pilot is
short, never contaminated.

**The sizing tool refuses to treat a truncated pilot as a finished one.** `tools/phase9/e9_2_pilot.py` now compares
each model's completed runs with its planned cells and marks the pilots that are short; only the two models named
here are allowed to be short, and `e9_2/sizing.json` records every model's runs done against runs planned.

## 6. The roster is re-routed through OpenRouter and re-composed to fit one $300 budget (TEAM, 12 Sep 2026; P9-8)

**Registered (PREREG_PHASE_9.md 0, 2, 4.1).** The roster was 13 configurations, each called on its provider's own
first-party API, with each model's σ_d measured by a pilot in exactly the configuration the grid runs (P9-5).

**What changed, and why.** The phase has no Anthropic credit and one pot of **$300 of OpenRouter credit**. At measured
token use, Sonnet 5's pilot alone costs $496 and Opus 5's $1,293. **Cost, not wall-clock, is now the binding
constraint** — the reverse of P9-1.

**The roster (P9-8):** the nine Google and OpenAI configurations unchanged on their own APIs; **Claude Haiku 4.5 only**,
routed `openrouter/anthropic/claude-haiku-4.5`; and four open-weight models added through OpenRouter — DeepSeek V4
Flash, Qwen3.7 Flash, GLM 4.7 Flash, Qwen3 235B. M = 14.

**The pinning rule, fixed here before any run.** OpenRouter load-balances across upstream providers, and a probe on
12 Sep 2026 was served by four different ones in five calls (Anthropic, GMICloud, Alibaba, Cloudflare, Google).
Upstreams differ in version, quantisation and sampling, so an unpinned route would put backend variation inside σ_d —
the very quantity this phase measures.

- **Every OpenRouter configuration is pinned to exactly one upstream**, with `provider: {order: [<one>],
  allow_fallbacks: false}`, so a request that cannot be served by that upstream **fails** rather than being silently
  re-routed.
- **The upstream is chosen by a stated rule, not by which server answered first:** among the endpoints serving the
  model, the one with the **lowest price per run** at our measured token profile; ties go to the **larger context
  window**. The chosen upstream, its price and its context window are recorded per configuration in
  `tools/phase9/e9_roster.py` and in every run's `Provider_Options` column.

  *Corrected on 12 Sep 2026, before any run on these configurations.* The first version of this rule ranked upstreams
  by median throughput with latency as the tie-break. **OpenRouter's endpoint API returns no throughput or latency
  statistics for any of these four models** — every `p50_throughput` and `p50_latency` field came back empty — so that
  rule could never have been applied, and applying it "as far as possible" would have meant pinning by price while
  the document claimed otherwise. Price and context window are the fields the data actually carries. Throughput is
  therefore measured by our own smokes instead, and is reported per configuration; it does not select the upstream.
- **How the pin is enforced, measured rather than assumed** (12 Sep 2026, before any run):
  - **The request fails closed.** `anthropic/claude-haiku-4.5` pinned to an upstream that does not serve it returns
    **HTTP 404** with `allow_fallbacks: false`. The same request with `allow_fallbacks: true` was served by **Azure** —
    the backend drift the pin exists to prevent. So the pin is enforced at request time, by the provider, and a run
    that completes was served by the pinned upstream.
  - **The serving upstream does NOT reach the callback.** A run's `response_metadata` carries `token_usage`,
    `model_provider` (LangChain's client class, not the backend), `model_name` (the model asked for),
    `system_fingerprint`, `id`, `service_tier`, `finish_reason` and `logprobs`. There is **no `provider` field**, so a
    per-call check inside the runner cannot be written from it. An earlier version of this section claimed every run
    records its upstream and that the runner discards a mismatched run; **neither was true as built**, and the dead
    check has been removed rather than left to look like a guard.
  - **The audit is out-of-band, by generation id.** Every call's response `id` is recorded, and a sample is resolved
    through OpenRouter's generation endpoint, which returns `provider_name`, the **exact snapshot served** (e.g.
    `anthropic/claude-4.5-haiku-20251001`) and the true cost. A sampled id whose `provider_name` is not the pinned
    upstream fails the configuration, and its runs are discarded.
  - **Cost is measured, not estimated.** OpenRouter returns `cost` and `cost_details.upstream_inference_cost` per
    call, so this phase's OpenRouter spend is recorded from the provider's own accounting rather than inferred from a
    price table.

**Haiku's route change is a configuration change, and its earlier runs are not pooled.** The 252 Haiku runs already
made on Anthropic's own API (124 pairs) used a different client and request schema. **They are not pooled with
OpenRouter runs.** Haiku is re-piloted on the route the grid will use, and the direct-API runs are reported beside it
as a **route sensitivity** — two measurements of one model on two routes, which is information the phase gets for
free, not a pooling decision made to save money. The same applies to Sonnet 5's and Opus 5's part-finished pilots:
reported, never used to size anything.

**What this cannot do.** It cannot restore the frontier tier. No claim of this phase covers Sonnet-, Opus- or
GPT-5-pro-class Anthropic behaviour, and the report says so wherever the roster is described.

**Still open, and not decided here:** whether Haiku and the open-weight models can afford the sweep's cells at all.
At the plan's Tier A shape (1,170 runs per model) Haiku costs $650 — more than twice what remains of the budget after
the pilots. The sweep's shape is fixed only after E9.3's criteria stage sizes it, and it is then costed against the
remaining credit before a single grid run starts.

## 7. OpenRouter runs send an explicit `max_tokens`, because sending none makes some upstreams reject every call

**Registered (P9-5).** Every model runs its provider's default configuration. The harness has never set `max_tokens`:
on the first-party APIs an absent cap means the provider's own default, which is what "provider default" meant.

**Measured (12 Sep 2026, the OpenRouter smokes).** Through OpenRouter an absent `max_tokens` does not mean "the
provider's default" — the router fills in the model's **full context window**, and the upstream then sees a request for
more tokens than the context can hold:

> Requested token count exceeds the model's maximum context length of 131072 tokens. You requested a total of 131082
> tokens: 10 tokens from the input messages and 131072 …

**Qwen3 235B failed all 400 calls of its smoke this way** (two runs, every day a fallback, both discarded by the
contamination rule — no data entered). Controlled variants isolate the cause: pinned to GMICloud the model answers
normally **with** a cap and **with** the harness temperature, and fails **only** when `max_tokens` is absent; DeepInfra,
Novita and the unpinned route behave the same. It is not the upstream, the pin or the temperature — it is the missing
cap. Claude Haiku 4.5 and DeepSeek V4 Flash survived it because their upstreams resolve an absent cap differently.

**The change, registered before any run uses it:** every **OpenRouter** configuration sends `max_tokens = 8192`. The
first-party Google, OpenAI and Anthropic configurations are **unchanged** — they keep sending none, so no run already
on disk is affected and no earlier measurement moves.

**Why 8,192, from data rather than stipulation.** Across every run on disk (3,600+ runs, 14 models) the **largest mean
output per call of any run is 3,097 tokens** (GPT-5 nano, 72 % of it reasoning); Gemini 2.5 Pro's worst is 1,791, and
every non-reasoning model stays under 220. 8,192 is **2.6× the worst case ever observed** and far below every roster
model's context window (the smallest is GLM 4.7 Flash's 131,072). A cap that truncated a reply would show as a parse
fallback, and the fallback share is reported per configuration, so truncation cannot pass silently.

**What this costs.** Nothing in price — `max_tokens` is a ceiling, not a reservation, and billing is on tokens
produced. It is recorded in every run's `Provider_Options` column, so a reader can see which runs carried a cap.

## 2. E9.1 `calibrate`: e2_6's matched-sd(x) construction lands within +5.3 % and +0.8 % of its target, not on it

**Registered (1.3).** Matched sd(x) for the half-life levels by `tools.phase2.e2_6_sweep.calibrate`:

- measure the stationary sd(x) at σ̄ in force;
- scale σ̄ by (target ÷ measured), on the premise that sd(x) is linear in the innovation scale;
- report the confirmation pass.

No tolerance was registered.

**Measured** (`e9_1/calibration.json`, 20 flat paths of T = 5,000 per pass; target 0.05839, the default engine's
stationary sd(x) on seeds 133900–133919):

| half-life | sd(x) at σ̄ in force | σ̄ matched | sd(x) after matching | off the target |
|---|---|---|---|---|
| 18.75 d | 0.05385 | 0.01636 | 0.06146 | **+5.3 %** |
| 32.64 d | 0.06934 | 0.01270 | 0.05885 | +0.8 % |

**The low level misses by more than the high one.** The scaling pass and the confirmation pass use different seed
blocks (132000 and 133000), as e2_6 does. So the miss mixes seed noise with any departure from linearity (the GJR
feedback makes x's innovation scale path-dependent). This measurement cannot separate the two.

**What is done.** The construction is applied as registered, once. It is not iterated, because an iteration would
be a second construction chosen after the first one's miss was seen.

- Each level's sd(x) and sd(r) on the panel are reported beside its effect (`e9_1/effects.csv`).
- The unmatched levels run as the registered sensitivity.
- **The half-life's rank is read with this beside it.** A +5.3 % larger sd(x) at the low level adds dispersion to
  what the ranking attributes to persistence.

## 8. The first OpenRouter smoke ran without the cap registered in 7 and is discarded; GLM 4.7 Flash is stopped mid-flight, and a stopping rule for an unfinished smoke is registered here

**What happened, in order.**

| UTC, 12 Sep 2026 | event |
|---|---|
| 08:00:49 | the OpenRouter smoke starts: five configurations, two cells each, **all ten runs concurrent** (`stage_smoke` submits every job at once) |
| 08:11–08:20 | Claude Haiku 4.5 and DeepSeek V4 Flash complete, 200/200 calls parsed, routing audited |
| 08:26 | Qwen3 235B fails all 400 calls — OpenRouter reads an absent `max_tokens` as the model's full context window |
| ~08:40 | **item 7 registers `OPENROUTER_MAX_TOKENS = 8192`** — while the smoke process is still running, so that process keeps the old code |
| 09:30 | Qwen3.7 Flash completes (89 min per run, the slowest completion) |
| 10:53 | GLM 4.7 Flash has still not completed after **173 min**; the process is stopped |

**The consequence, stated plainly.** Every row of the first smoke carries `max_tokens_client: null`. Those runs
confirm routing, parsing and the token profile of an **uncapped** client. They do **not** confirm the configuration
this phase registered. They size nothing and gate nothing; the smoke is re-run under the cap.

**The uncapped measurements, reported and kept** (two runs per configuration, 200 calls each, provider-reported cost):

| configuration | $/run | s/run | output tok/run | parsed | routing audit |
|---|---|---|---|---|---|
| `anthropic/claude-haiku-4.5` → Anthropic | 0.574 | 632 | 34,449 | 200/200 | MATCH `anthropic/claude-4.5-haiku-20251001` |
| `deepseek/deepseek-v4-flash` → Baidu | 0.030 | 1,062 | 110,652 | 200/200 | MATCH `deepseek/deepseek-v4-flash-20260423` |
| `qwen/qwen3.7-flash` → Alibaba | 0.065 | 4,973 | 413,557 | 200/200 | MATCH `qwen/qwen3.7-flash-20260727` |
| `qwen/qwen3-235b-a22b-2507` → GMICloud | — | — | — | 0/400 | contaminated, no call completed |
| `z-ai/glm-4.7-flash` → Cloudflare | — | — | — | — | **discarded, stopped in flight** |

Outputs and ledgers archived under `results_v2/phase9/smoke/_uncapped_20260912/`.

**GLM's discarded run.** Both GLM runs are discarded with no ledger row: the runner writes a row when a run ends, and
neither ended. The route was live — a single call pinned to Cloudflare, `max_tokens` 8,192, answered in **4.3 s**
(`gen-1789210501-kHdwsZ5E0YxP3nBb3geY`) — so the configuration is re-smoked rather than dropped on this evidence.

**Spend.** $1.34 is ledgered across the runs above; OpenRouter reports $1.90 used. The **$0.56 difference is not
attributable to any ledger row** — it is the discarded GLM calls and the failed 235B calls, which no completed run
recorded. It is reported as spend, not as data. $298.10 of the $300 remains.

**Registered now, before the re-smoke is read (nothing of it is on disk yet).** A smoke that does not finish must not
be waited on indefinitely, and the wait must not be chosen after seeing which configuration is slow:

> **A configuration's smoke FAILS if it has not completed 30 minutes after the last other configuration in the same
> smoke completes.** Its runs are discarded, its spend is reported, and the configuration is dropped from the roster
> for this phase. No second wait is granted.

This rule can be met or failed by any configuration, and it is failed by a configuration that is merely too slow —
which for this phase is the same problem as one that does not answer, because a roster member has to finish a pilot.

## 9. E9.3 `criteria`: the constructions PREREG 3.2 left to the implementation, registered here before the stage is written to disk

3.2 fixed the three questions and left L, S and M to the design. Writing the stage forces choices 3.2 does not
name. They are registered here, **before the stage has produced a single number** (no `e9_3/criteria.*` exists), and
each is stated so that it can be read against the plan's own words (13.3).

**9.1 The data-generating process across levels.** The default level and each of L non-default levels carry their own
(M × S) matrix of seed-level memory − static differences, built by `draw_arm_terms` / `D_from_terms` — the same
construction 3.1 registered — with three additions:

| term | drawn | why |
|---|---|---|
| model × arm, sd τ = `band_mas_R1_limit` | **once, shared by every level** | the same model is run at every level, and its arm tendency travels with it |
| path × arm, persona × path × arm, replicate | **afresh at every level** | a generator parameter changes the path a seed produces, so a seed's path is not the same object across levels |
| level × arm × model, sd τ_LAM | independently at **every** level, the default included | the quantity 3.2 names; independent draws, no sum-to-zero constraint |

**τ, the model × arm sd, is held at the measured limit** (0.03798) rather than swept. It cancels from the
interaction (it is shared across levels) and a smaller τ only makes the per-level test easier, so the registered
value is the conservative one for criterion (ii). This is a choice, and it is the reason it is a choice.

**9.2 Criterion (i), the sign criterion.** Plan 13.3 says "the sign of the arm contrast is unchanged". Read plainly:
a conclusion is **level-dependent** when the point estimate ĝ_ℓ at any non-default level carries the opposite sign to
ĝ₀ at the default level. That is the headline rate. A second reading — a level flips the sign only if its own R5 test
is significant at α — is reported beside it, because the plain reading lets a level with no resolvable effect at all
overturn a conclusion. **The headline is the plain reading**, because it is the plan's sentence; the second is
reported so the difference between them is visible, not so the better number can be chosen afterwards.

**9.3 Criterion (ii), the model-level test at every level.** R5 (P9-4) at each level; the L + 1 p-values of one
conclusion are one family under BH; the criterion **holds** when every level's q stays below the level. Reported at
α = 0.05 and at α′ = 0.05/36 (E8.5's family count, re-read at the design's count when section 4 is fixed).

**9.4 Criterion (iii), the equivalence interval.** The level × arm interaction at level ℓ is estimated **per model and
then differenced** — dₘ = r̄_{ℓm} − r̄_{0m}, estimate mean_m(dₘ), se = sd(dₘ)/√M, 90 % interval on t(M − 1). This is
the estimator that respects the shared model term; differencing the two grand means and treating them as independent
would not. Equivalence is **declared only when every non-default level's interval lies inside ± 0.025**
(= half of `inference_params` `min_effect.band_mas` = 0.05, read not typed).

**9.5 The shapes swept, and the simulation's size.** M ∈ {6, 10, 14}, S ∈ {19, 47, 93}, L ∈ {1, 2, 6, 12} (P9-6's six
parameters at two non-default levels each is L = 12), τ_LAM ∈ {0, ½τ}, β ∈ {0, ½Δ, Δ}, true interaction ∈ {0, 0.025}
— **432 conditions × 2,000 datasets**, stream [9, 3, 6, key]. 2,000 is smaller than 3.1's 10,000: a condition here
carries L + 1 matrices rather than one. At a rate near 0.05 the Wilson half-width is ≈ 0.010, which is the precision
this stage's readings are reported to.

**9.6 What the stage may conclude.** Any criterion whose rate shows it cannot be met at a shape the design can afford
is reported **here, before the grid**, exactly as 3.2 requires — and, as in item 3, a criterion found unmeetable is
reported as loudly as one that holds.

## 10. The OpenRouter pilots are truncated on a clock, and three configurations are not piloted at all (TEAM, 12 Sep 2026)

**Registered before the first OpenRouter pilot run is launched** (no `pilot` run exists for any OpenRouter
configuration; the ledger `e9_2/ledger_*openrouter*` files do not exist).

**The constraint.** The team requires Phase 9 finished within hours of 11:15 UTC, 12 Sep 2026. The binding constraint
is **wall-clock, not money**: a run is 200 sequential calls, and P9-1 caps a model at 15 concurrent calls. The smoke
measured, per run:

| configuration | s/run (capped smoke) | 192-run pilot at 15 concurrent | $/run |
|---|---|---|---|
| `openrouter/anthropic/claude-haiku-4.5` | 652 | 2.3 h | 0.574 |
| `openrouter/deepseek/deepseek-v4-flash` | ~1,060 | 3.8 h | 0.030 |
| `openrouter/qwen/qwen3.7-flash` | ~4,970 | **17.7 h** | 0.065 |
| `openrouter/z-ai/glm-4.7-flash` | not completed | — | — |
| `openrouter/qwen/qwen3-235b-a22b-2507` | not completed | — | — |

**What is registered.**

1. **The pilot's seeds are truncated, not its cells.** Section 2 fixed 16 seeds per cell (192 pairs). The OpenRouter
   configurations run the **same 12 persona × scenario cells and the same seed block, from its start**:
   * Claude Haiku 4.5 — seeds **3001–3008**, 8 per cell, 96 pairs, 192 runs;
   * DeepSeek V4 Flash — seeds **3001–3004**, 4 per cell, 48 pairs, 96 runs.
   Truncating the seed list from its start keeps every cell balanced, so σ_d(R = 1) is estimated on the registered
   estimator with fewer df — 96 − 12 = 84 and 48 − 12 = 36 — and its chi-square 90 % limit inflates accordingly. **The
   limit is not comparable to a 180-df limit, and the sizing must report the df beside it.**
2. **Qwen3.7 Flash, GLM 4.7 Flash and Qwen3 235B are not piloted.** They are dropped from the roster **for sizing**;
   their smokes are reported. Qwen3.7 Flash is dropped on the measured 17.7 h, which the clock cannot hold; GLM and
   235B by item 8's stopping rule if their capped smokes do not complete.
3. **The direction of the error is stated in advance.** A pilot with fewer seeds gives a **wider** upper limit for
   σ_d, so any seed count it sizes is **conservative** — larger, not smaller. Truncation cannot make the grid look
   cheaper than it is.
4. **What this costs the phase's question.** E9.2 asks which roster member's σ_d drives the plug-in (P8-16, the
   maximum over the roster). With three configurations unpiloted, the maximum is taken over **11 of 14**, and the
   report must say so wherever the plug-in appears. A model that is not piloted cannot drive the plug-in, so the
   plug-in reported here is a **lower bound** on the one a full roster would give.

### 10a. Correction to item 10, made the same hour, before any run it governs

Item 10's table was written from the **uncapped** smoke of item 8, and it records Qwen3 235B and GLM 4.7 Flash as
"not completed". By the time it was written that was already stale for one of them:

- **Qwen3 235B's capped smoke COMPLETED and PASSED at 11:12 UTC** — 2 runs × 200/200 calls parsed, **803 s and 836 s**
  per run, 19 k output tokens per run — which is *faster* than DeepSeek V4 Flash. The fix registered in item 7 is
  what changed it: uncapped it failed all 400 calls, capped it fails none.
- Item 8's stopping rule therefore **does not** apply to it, and item 10's clause 2 does not either.

**Registered, before its first pilot run:** Qwen3 235B **is piloted**, at seeds 3001–3004, 4 per cell, 48 pairs,
96 runs — the same truncation DeepSeek V4 Flash takes. The team's window was extended to 6–7 hours at 11:17 UTC,
which is what makes a third pilot fit; the extension is recorded because it, not a result, is the reason.

**Unchanged:** Qwen3.7 Flash stays unpiloted. At 4,973 s per run even a half-size pilot is 5.5 h at the cap and would
take slots from the configurations that can finish. GLM 4.7 Flash remains governed by item 8's rule.

With this correction the plug-in maximum is taken over **12 of 14** configurations, not 11.

## 11. Item 8's stopping rule is applied: Qwen3.7 Flash and GLM 4.7 Flash fail their smoke and leave the roster

**The rule, as registered in item 8 before the re-smoke was launched:** a configuration's smoke fails if it has not
completed 30 minutes after the last other configuration in the same smoke completes.

**The arithmetic, done by the clock and not by choice:**

| event | UTC |
|---|---|
| capped smoke started (10 runs, all five configurations at once) | 11:58:24 → *10:58:24* |
| Claude Haiku 4.5 completed both runs (647 s, 656 s) | 11:09 |
| Qwen3 235B completed both runs (803 s, 836 s) | 11:12 |
| DeepSeek V4 Flash completed both runs (1,017 s, 1,227 s) — **the last other configuration** | 11:19:07 |
| **deadline = 11:19:07 + 30 min** | **11:49:07** |
| state at the deadline: Qwen3.7 Flash **0 of 2**, GLM 4.7 Flash **0 of 2**, 51 minutes elapsed | 11:49:07 |
| process stopped | 11:50:54 |

**Both configurations FAIL.** They are dropped from the roster for this phase: not piloted, and unable to reach the
plug-in. `tools/phase9/e9_2_pilot.py` carries them as `NOT_PILOTED`, so `sizing.json` reports the plug-in maximum as
taken over **12 of 14** configurations rather than silently over "the roster".

**This was not a surprise to the rule, which is the point.** Qwen3.7 Flash's uncapped smoke had already measured
4,973 s per run, so 30 minutes was never going to be enough; GLM 4.7 Flash's uncapped attempt ran 173 minutes without
finishing a single run. The rule was registered before either was re-run, it could have been met — the three
configurations that passed met it with 30–37 minutes to spare — and it was applied without modification.

**Spend.** Their discarded runs carry no ledger row, because the runner writes a row when a run ends and none ended.
Across the whole phase, OpenRouter reports **$28.86** used against **$22.81** ledgered to completed runs: the
**$6.06 difference** is the discarded GLM and Qwen3.7 calls plus the uncapped 235B failures. It is reported as spend,
not as data. **$271.14 of the $300 remains.**

### 11a. Correction to item 11's spend attribution, made when the later data contradicted it

Item 11 states that the **$6.06** difference between OpenRouter's reported usage and the cost ledgered against
completed runs "is the discarded GLM and Qwen3.7 calls plus the uncapped 235B failures". **That attribution is
wrong, and the evidence against it is arithmetic.**

| moment | ledgered across runs | OpenRouter `total_usage` | difference |
|---|---|---|---|
| 11:50 UTC, when item 11 was written | $22.81 | $28.86 | $6.06 |
| 14:15 UTC, every pilot finished | $111.84 | $115.27 | **$3.43** |

**The difference shrank by $2.63 while spending continued.** Discarded spend cannot shrink, so the gap is not the
discarded runs alone: the sum of the **per-call** costs the provider returns drifts from the **account debit**
(rounding per call, and any discount applied at the account level). Between those two moments the ledgered total
grew $89.03 against a debit of $86.41 — the per-call sums ran *ahead* of the debit.

**What is therefore true, stated as narrowly as the measurement allows:**

- the account was debited **$115.27**, and **$184.73 of the $300 remains** — both read from the provider;
- **$111.84** is the sum of provider-reported per-call costs over every ledgered run;
- the **$3.43** difference contains the discarded runs' spend **and** the per-call/account drift, **and this phase
  cannot separate them**. The discarded runs are reported as discarded (items 8 and 11); no dollar figure is
  attributed to them, because none was measured.

Item 11's table and its stopping-rule finding are unaffected. Only the sentence attributing the difference is
withdrawn, and it is withdrawn here rather than edited away.
