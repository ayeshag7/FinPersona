# Phase 9 report — sensitivity through the LLM harness: the roster timed and piloted, the reference distribution simulated, the parameter list computed, the grid staged (v2.1)

*Written as results land (execution prompt, "Documentation"). Every number cites the file it comes from. The tables
marked `<!-- table:... -->` will be generated from those files by `tools/phase9/e9_report_tables.py` and read back
by a test, as Phase 8's were. Sections follow the protocol's six headings. A section marked **pending** has no
number yet, by design.*

**Status: COMPLETE for what this phase covers — 12 September 2026. Nothing is committed.**

**What "complete" means here, stated so it cannot be read as more than it is.** E9.0–E9.3 and E9.5's specification
are done; every roster pilot finished and the grid is sized at **120 seeds** (§3.4). **The grid itself (E9.4) was not
run** — stage 1 as first designed was withdrawn as priced, and its shape is stage 2's to fix (§3.5, §7). **Two
decisions are open for the team** (§5): which reading of plan 13.3's sign criterion the robustness table uses, and
the roster size M. Both were left open deliberately rather than settled by me after seeing the rates (P9-9).

---

## 0. Current state

| item | status |
|---|---|
| Pre-registration | `PREREG_PHASE_9.md`, written before any simulated rate, ranking or paid batch. `PREREG_PHASE_9_ADDENDUM.md` records every disconfirmation as it lands (items **1, 1b, 2–11**, with 10a correcting 10 within the same hour) |
| Team decisions | **P9-1:** wall-clock binds, 10–15 calls per model — **its "cost is not a constraint" is superseded by P9-8**. **P9-2:** the roster was 13 configurations. **P9-3:** a staged grid, headline first. **P9-4:** the reference distribution is R5. **P9-5:** provider defaults, Flash's thinking off. **P9-6:** the sweep runs the **data-driven six**. **P9-7:** Fable 5.1 excluded on cost. **P9-8:** one budget of **$300 of OpenRouter credit and no Anthropic credit** — Sonnet 5 and Opus 5 dropped, Claude represented by Haiku 4.5 through OpenRouter, four open-weight models added; **roster = 14**. **P9-9:** the robustness criteria are simulated at the design's shape and **stand as registered, including the one shown to be unsafe**. **P9-10:** Qwen3.7 Flash and GLM 4.7 Flash fail the registered smoke stopping rule and leave the roster for sizing; **the plug-in is taken over 12 of 14** |
| E9.0 throughput and wall-clock | **done** for every roster model: two measured in batch (E8.5), 11 by smoke, and Flash's context levels by smoke (section 3.1) |
| E9.3 reference distribution | **done** (section 3.2). **The registered recommendation rule recommends none, and it is unmeetable by construction** (addendum 3). R5 was added after the read, judged on fresh data, and chosen by the team (P9-4) |
| E9.1 parameter list | **done** (section 3.3). It was not in Phase 7's files (finding 1). The reference rows reproduced exactly; 45 panels ran; by REG-16 (i)'s rule the **data-driven six** are swept (P9-6), and one level's handling is addendum 4 |
| E9.2 roster pilots | **six complete** at the registered 384 runs (Flash-Lite, Gemini 3.5 Flash, GPT-5 mini, GPT-5, GPT-5.4 mini, GPT-5.5); **two truncated on a clock** (addendum 5: Gemini 2.5 Pro 279 runs / 128 pairs, GPT-5 nano 281 / 128); **four stopped by the Anthropic credit failure** and then dropped or re-routed by P9-8 (Haiku 252 runs, Sonnet 158, Opus 110, Fable 93 — reported, sizing nothing). Flash is exempt: its prompts equal E8.5's. **The five OpenRouter configurations were smoked twice** — once uncapped and discarded (addendum 8), once under the registered cap — and **three are piloted to completion on truncated seed lists** (addendum 10, 10a): Haiku 4.5 **192/192** (96 pairs), DeepSeek V4 Flash and Qwen3 235B **96/96** (48 pairs each). **Every roster pilot is complete**; the plug-in σ_d is 0.0958 and stage 1's seed count is **120** (section 3.4) |
| E9.3 criteria for stage 2 | **done** (section 3.2b). Their missing constructions were registered in addendum 9 before the stage produced a number, then simulated on 432 conditions × 2,000 datasets. **Two of the plan's three criteria do not behave as 13.3 assumes** — the sign criterion falsely fires up to 0.241 of the time, and (ii) at α′ holds 0.03–0.05 of the time at M = 6 (P9-9) |
| E9.4 stage 1 | **not run in this phase** (section 3.5). E9.2 gives it **120 seeds** by Appendix A; its shape is stage 2's to fix, with section 5's two open decisions in front of it |
| E9.5 robustness table | **specified, not populated** (section 3.6): its columns and rules are fixed with 3.2, and its operating characteristics are measured, but the table needs a grid this phase does not run |
| The switch | `RunConfig.provider_options` → `Provider_Options`; Phase 8's golden record shows 0 differences; tested |
| Tests | the Phase 9 file: **19 passed, 1 skipped** (20 items), including four added today — the vectorised BH against `tools.stats_v2.bh_adjust`, the criteria DGP's known answers, the shared model term, and the uncapped-OpenRouter ledger filter. **The whole tree: 239 passed, 2 skipped, 4 xfailed, 0 failed** (section 3.8), run twice because the first run preceded the last documentation edits; both runs agree |

---

## 1. Literature review and the citation table

**No number from any source below enters a parameter file, a test tolerance or a decision rule in this phase.** Every
statistical method is validated by simulation on data with known answers (section 3.2).

| source | what it is cited for | status | where it enters |
|---|---|---|---|
| Satterthwaite (1946) | the approximate df of a linear combination of mean squares (R4) | **not re-read in this phase** | R4's df; its size is measured, not assumed |
| Graybill & Wang (1980) | the modified large-sample limit (P8-15) | **not re-read** (carried from Phase 8) | the pilots' limit at R′ = R reduces to the chi-square limit |
| Benjamini & Hochberg (1995); Benjamini & Yekutieli (2001) | the step-up procedures (P8-10) | **not re-read** (carried) | stage 1's single confirmatory family uses BH within family |
| `langchain_anthropic` 1.6.1, `ChatAnthropic.thinking` docstring (source code) | Claude Sonnet 5 and Opus 5 run adaptive thinking by default; `{"type": "disabled"}` exists | **read, correct** | P9-5 keeps the default; the reasoning tokens are logged |
| `langchain_core` 1.6.0, `ChatGeneration` text extraction (source code) | only `type: text` blocks reach the output parser | **read, correct** | Claude replies with thinking blocks parse (smokes: every run `ok`) |
| `langchain_openai` 1.6.0, `validate_temperature` (source code) | gpt-5 models keep only temperature 1 unless the reasoning effort is "none" | **read, correct** | P9-5: gpt-5 models at 1.0 |
| Provider model lists (API, 11 Sep 2026) | which model ids the account's keys can call | **read** (`models.list` of each provider) | the candidates (`tools/phase9/e9_roster.py`) |

---

## 2. Pre-registration, verification of the inherited numbers, and corrections

**Found before any rule was written** (PREREG section 0):

1. **REG-16 (i)'s ranking was never computed.** E7.8 swept the scripted policies' own parameters on the frozen
   generator. No Phase 1–8 file carries a generator parameter's effect on the level-free oracle's regret or on the
   scripted policies' band-MAS. E9.1 computes it.
2. **Plan 13.1's level table predates the fits.**
   - Half-life: in force 22.38 d, CI95 [18.75, 32.64], where the plan writes 60 / FIT / 250.
   - Analyst error sd: in force 0.564, where the plan writes 0.15 / LIT / 0.45.
   - Sentiment loading: in force 0.
   - σ_V: only a bootstrap CI95 exists (`e9_1/candidates.json`).
3. **Phase 7's scripted policies are keyed on Python's salted string hash** (`tools/phase7/e7_panel.scripted_policies`),
   so E7.8's trajectories are not reproducible across processes. E9.1 uses a `zlib.crc32` key.
4. **REG-1's "60 + 60 runs"** does not match its own factor list, which gives 240 (`tools/phase9/e9_designs.py`).
5. **The execution prompt's throughput table is not reproduced by a repository tool.** It gives Flash 133 runs/h at
   effective concurrency 14.7 and GPT-5 mini 29/h at 12.8. On the same ledgers the tool gives Flash 129.0 at 14.29
   and GPT-5 mini 27.3 at 11.84 (`e9_0/throughput.csv`).

### Amendments to the plan, recorded here rather than by editing it

| plan text | amendment |
|---|---|
| 13.1: the six parameters' levels | Re-derived from the parameter files in force by PREREG 1.2; the plan's 60 / 250 d and 0.15 / 0.45 predate the fits |
| 13.2: Tiers A / B / C as budget tiers | Replaced by P9-1 (cost not a constraint) and P9-3 (a staged grid priced in hours) |
| 13.3 (ii): "BH-corrected q in the crossed mixed model" | The crossed model is descriptive (P8-17). The model-level test is R5 (P9-4), and its p-value enters BH within stage 1's single confirmatory family |
| 13.3 (i): "the sign of the arm contrast is unchanged" across all levels | **Measured, not amended.** At the design's shape the sentence as written calls a conclusion level-dependent up to **0.241** of the time when the arm effect is *identical* at every level, and ≈ 0.60 when there is no effect at all. A significant-only reading of the same rule reaches 0.008. The rule is **left as the plan writes it** (registered before the rates were read, addendum 9.2; P9-9) and the choice between the readings is section 5's, for the team. The plan's sentence is not silently reinterpreted |
| 13.3 (ii) at α′, and (iii) with a level × arm × model term | **Both turn on the roster size, and the plan does not say what M is.** (ii) holds at every level 0.03–0.05 of the time at M = 6 against 0.58–0.63 at M = 14; (iii)'s equivalence power is 0.09–0.11 at M = 6 against 0.55–0.67 at M = 14. Seeds move either by ≈ 0.05. Reported before the grid, as 3.2 requires |
| 15: "≈ 9 h wall-clock per model per tier" | Measured: stage 1's headline cells take 0.4–5.6 days per model at 15 streams by smoke rate (`e9_0/wallclock.csv`) |
| 13.2's tiers, and this report's own stage-1 design | **Withdrawn as priced.** Stage 1 as first designed — Phase 8's confirmatory sizing (93–153 seeds), 12 models, and the D11 slice at the headline's seed count — came to **$126,000**, against the plan's own Phase 9 of ≈ $210 for Tier A. Phase 8 sized "the main grid" for a confirmatory arm contrast; Section 15 puts the main grid outside this plan. **This phase's questions are sign stability, a level × arm interaction interval and an equivalence margin — within-design comparisons on shared seeds**, not a fresh confirmatory test of the memory − static effect. The sweep is therefore sized by E9.3's criteria stage, at sensitivity precision, and costed against the remaining credit before any grid run |
| 13.2: "all runs at 10–15 concurrent requests" and P9-1's cost framing | **Cost is now the binding constraint** (P9-8): one $300 OpenRouter budget, no Anthropic credit. Wall-clock ceased to bind once the roster's expensive models were dropped |

---

## 3. Experiments and results

### 3.1 E9.0 — throughput, wall-clock, and the smokes

<!-- table:e9_throughput -->
Every roster configuration, from the ledgers. A configuration timed by smoke has n = 2 runs at low concurrency, so its seconds per run are a lower bound on a batch's. Measured batch ÷ smoke: gemini-2.5-flash 1.64; gpt-5-mini 1.17.

| model · configuration | timed by | s / run | s / call | reasoning tokens / call | runs per stream-hour | LLM errors / fallbacks |
|---|---|---|---|---|---|---|
| gemini-2.5-flash-lite · default | smoke (n = 2) | 227 | 1.14 | 0 | 15.84 | 0 / 0 |
| gpt-5.4-mini · default | smoke (n = 2) | 289 | 1.44 | 0 | 12.47 | 0 / 0 |
| gemini-2.5-flash · thinking0 | batch (n = 574) | 399 | 1.99 | 0 | 9.03 | 0 / 1 |
| claude-haiku-4-5-20251001 · default | smoke (n = 2) | 592 | 2.96 | 0 | 6.08 | 0 / 0 |
| openrouter/anthropic/claude-haiku-4.5 · default | smoke (n = 2) | 651 | 3.26 | 0 | 5.53 | 0 / 0 |
| openrouter/qwen/qwen3-235b-a22b-2507 · default | smoke (n = 2) | 820 | 4.10 | 0 | 4.39 | 0 / 0 |
| claude-sonnet-5 · default | smoke (n = 2) | 1013 | 5.06 | 172 | 3.55 | 0 / 0 |
| gpt-5.5 · default | smoke (n = 2) | 1043 | 5.20 | 169 | 3.45 | 0 / 0 |
| openrouter/deepseek/deepseek-v4-flash · default | smoke (n = 2) | 1122 | 5.61 | 465 | 3.21 | 0 / 0 |
| gemini-3.5-flash · default | smoke (n = 2) | 1246 | 6.23 | 1017 | 2.89 | 0 / 0 |
| claude-opus-5 · default | smoke (n = 2) | 1379 | 6.90 | 192 | 2.61 | 1 / 0 |
| gpt-5-mini · default | batch (n = 142) | 1560 | 7.80 | 510 | 2.31 | 0 / 0 |
| claude-fable-5-1 · default | smoke (n = 2) | 1805 | 9.02 | 242 | 1.99 | 0 / 0 |
| gpt-5 · default | smoke (n = 2) | 2570 | 12.85 | 798 | 1.40 | 0 / 0 |
| gpt-5-nano · default | smoke (n = 2) | 3097 | 15.37 | 2012 | 1.16 | 0 / 0 |
| gemini-2.5-pro · default | smoke (n = 2) | 3240 | 16.20 | 1605 | 1.11 | 0 / 0 |
<!-- /table:e9_throughput -->

<!-- table:e9_wallclock -->
Days per model at 15 concurrent calls. Every model runs at once, so a roster's wall-clock is its slowest member's. A smoke-timed rate carries, in brackets, the same design at that rate scaled by the largest measured batch ÷ smoke ratio.

| model · configuration (rate) | headline_12cells @ 47 seeds (1,128 runs) | headline_12cells @ 93 seeds (2,232 runs) | tierA_shape @ 47 seeds (10,998 runs) | tierA_shape @ 93 seeds (21,762 runs) |
|---|---|---|---|---|
| claude-fable-5-1 · default (smoke) | 1.6 (2.6) | 3.1 (5.1) | 15.3 (25.1) | 30.3 (49.6) |
| claude-haiku-4-5-20251001 · default (smoke) | 0.5 (0.8) | 1.0 (1.7) | 5.0 (8.2) | 9.9 (16.3) |
| claude-opus-5 · default (smoke) | 1.2 (2.0) | 2.4 (3.9) | 11.7 (19.1) | 23.2 (37.9) |
| claude-sonnet-5 · default (smoke) | 0.9 (1.4) | 1.7 (2.9) | 8.6 (14.1) | 17.0 (27.8) |
| gemini-2.5-flash · thinking0 (batch) | 0.3 | 0.7 | 3.4 | 6.7 |
| gemini-2.5-flash-lite · default (smoke) | 0.2 (0.3) | 0.4 (0.6) | 1.9 (3.2) | 3.8 (6.2) |
| gemini-2.5-pro · default (smoke) | 2.8 (4.6) | 5.6 (9.1) | 27.5 (45.0) | 54.4 (89.0) |
| gemini-3.5-flash · default (smoke) | 1.1 (1.8) | 2.1 (3.5) | 10.6 (17.3) | 20.9 (34.2) |
| gpt-5 · default (smoke) | 2.2 (3.7) | 4.4 (7.2) | 21.8 (35.7) | 43.2 (70.6) |
| gpt-5-mini · default (batch) | 1.4 | 2.7 | 13.2 | 26.2 |
| gpt-5-nano · default (smoke) | 2.7 (4.4) | 5.3 (8.7) | 26.3 (43.0) | 52.0 (85.1) |
| gpt-5.4-mini · default (smoke) | 0.3 (0.4) | 0.5 (0.8) | 2.5 (4.0) | 4.8 (7.9) |
| gpt-5.5 · default (smoke) | 0.9 (1.5) | 1.8 (2.9) | 8.8 (14.5) | 17.5 (28.6) |
| openrouter/anthropic/claude-haiku-4.5 · default (smoke) | 0.6 (0.9) | 1.1 (1.8) | 5.5 (9.0) | 10.9 (17.9) |
| openrouter/deepseek/deepseek-v4-flash · default (smoke) | 1.0 (1.6) | 1.9 (3.2) | 9.5 (15.6) | 18.8 (30.8) |
| openrouter/qwen/qwen3-235b-a22b-2507 · default (smoke) | 0.7 (1.2) | 1.4 (2.3) | 7.0 (11.4) | 13.8 (22.5) |
<!-- /table:e9_wallclock -->

**Reading.**

- **The roster's clock is set by its three slowest members,** GPT-5 nano, Gemini 2.5 Pro and GPT-5. Their default
  configurations spend up to 494,208 reasoning tokens in a 200-call run.
- **Two runs per model is a small sample.** The measured batch ÷ smoke ratio is 1.64 for Flash and 1.17 for GPT-5
  mini, so every smoke-timed wall-clock is shown with and without the larger ratio.
- **The context-length levels on Flash take 1.04–1.96× a stateless smoke run** (`e9_0/smoke/smoke_context_*.json`).
- **Every first-party smoke** parsed at least 198 of 200 calls first time and wrote the provider-options column on
  every row. **The OpenRouter smokes did not all pass.** The two tables above carry the three that did, timed under
  the registered cap; the two that failed appear in neither, because their only completed runs were **uncapped** and
  those rows are filtered out of every timing (addendum 8,
  `tools/phase9/e9_wallclock._is_uncapped_openrouter`, 8 rows dropped).
  Their measured times are reported below instead, where their provenance can be stated.

**The five OpenRouter configurations, smoked twice** (uncapped, then under the registered `max_tokens` of addendum 7;
only the second tests the configuration this phase registered):

| configuration → pinned upstream | uncapped | capped | s / run (capped) | $ / run | verdict |
|---|---|---|---|---|---|
| `anthropic/claude-haiku-4.5` → Anthropic | 200/200 both runs | 200/200 both runs | 647, 656 | 0.574 | **passes**, piloted |
| `qwen/qwen3-235b-a22b-2507` → GMICloud | **0/400 calls** | 200/200 both runs | 803, 836 | ~0.023 | **passes once capped**, piloted (10a) |
| `deepseek/deepseek-v4-flash` → Baidu | 200/200 both runs | 200/200 both runs | 1,017, 1,227 | 0.029 | **passes**, piloted |
| `qwen/qwen3.7-flash` → Alibaba | 200/200 both runs, **4,973 s / run** | 0 of 2 runs at the deadline | — | — | **FAILS** the stopping rule (P9-10) |
| `z-ai/glm-4.7-flash` → Cloudflare | ran 173 min, never finished | 0 of 2 runs at the deadline | — | — | **FAILS** the stopping rule (P9-10) |

- **The routing was audited, not assumed.** Three generation ids per configuration were resolved through OpenRouter's
  generation endpoint: every one was served by the pinned upstream, on the expected snapshot
  (`anthropic/claude-4.5-haiku-20251001`, `deepseek/deepseek-v4-flash-20260423`, `qwen/qwen3.7-flash-20260727`).
- **Qwen3 235B is the case for the cap.** Uncapped it failed every one of 400 calls, because OpenRouter reads an
  absent `max_tokens` as the model's full context window and the upstream rejects the request; capped it failed none
  and is *faster* than DeepSeek. The defect was in the request, not the model.
- **Two configurations were dropped by a rule written before they ran** (addendum 8, applied in 11; P9-10), not by a
  judgement made after seeing which was slow.

### 3.2 E9.3 — the reference distribution for model-level contrasts

<!-- table:e9_refdist -->
Null conditions per M: 48 for the analytic candidates (10,000 datasets each), 8 for R3. A candidate 'breaks' a condition when its size's Wilson lower limit exceeds the nominal level at α = 0.05 or α′ = 0.05 / 36. R1, R2 and R4 are the registered candidates; R5 was added after their rates were read (addendum 1) and is judged only on these fresh datasets.

| models | R1 breaks | R2 breaks | R4 breaks | R5 breaks | R3 | registered rule | rule with R5 |
|---|---|---|---|---|---|---|---|
| 3 | 48 | 21 | 36 | 0 | **fails** | **none** | R5 |
| 4 | 48 | 24 | 32 | 0 | not run | **none** | R5 |
| 5 | 48 | 24 | 26 | 0 | not run | **none** | R5 |
| 6 | 48 | 25 | 22 | 1 | **fails** | **none** | none |
| 8 | 48 | 31 | 12 | 1 | **fails** | **none** | none |
| 10 | 48 | 32 | 13 | 1 | not run | **none** | none |
| 12 | 48 | 32 | 4 | 1 | **fails** | **none** | none |
| 14 | 48 | 32 | 4 | 0 | not run | **none** | R5 |

**An exactly sized test breaks this rule at a given M with probability 0.93** (48 conditions, both α), so the rule is unmeetable by construction (addendum 3).
<!-- /table:e9_refdist -->

**Reading.**

- **As registered, no candidate holds size at any roster size, and the rule could not have recommended one.** An
  exactly sized test breaks it at a given M with probability 0.93 (addendum 3).
- **Phase 8's two-way bootstrap (R3 = E2)** reproduces Phase 8's measured size at Phase 8's condition
  (`e9_3/bridge.json`). At α′ its size is 0.008–0.170 once the arm effect varies by model.
- **R5**, added after R1–R4 were read (addendum 1), was judged on 864 conditions × 10,000 fresh datasets:
  - its size at α is ≤ 0.055;
  - at α′ its breaks are what an exactly sized test produces.
- **The team chose R5 (P9-4).**
- **Model-level power** depends on the between-model sd of the arm effect far more than on the seeds. At 93 seeds and
  M = 12, it is 1.00 at ½ Flash's σ_d limit and 0.61 at the limit (`e9_3/refdist_fresh.csv`).

### 3.2b E9.3 — the three robustness criteria at the design's shape (PREREG 3.2, addendum 9)

<!-- table:e9_criteria -->
432 conditions × 2,000 datasets. Equivalence margin ± 0.025 (half of `inference_params` `min_effect.band_mas`), 90 % interval. The slice shown is the design's own: L = 12 non-default levels, S = 93 seeds. τ_LAM is the level × arm × model sd; ½τ is half the measured band-MAS σ_d limit. (i) and (iii) are read at a TRUE interaction of 0 — every rate below is a FALSE finding except the two marked power.

| models M | (i) false level-dependent, plain, β = ½Δ | (i) same, significant-only | (ii) holds at every level, α | (ii) at α′ | (iii) equivalence power, τ_LAM 0 | (iii) power at ½τ | (iii) false equivalence at the margin |
|---|---|---|---|---|---|---|---|
| 6 | 0.220 | 0.003 | 0.469 | 0.030 | 1.000 | 0.000 | 0.000 |
| 10 | 0.106 | 0.002 | 0.829 | 0.189 | 1.000 | 0.073 | 0.000 |
| 14 | 0.059 | 0.001 | 0.951 | 0.490 | 1.000 | 0.424 | 0.000 |

**The sign criterion as the plan writes it reaches 0.241 when the effect is the same at every level**; read as significant-only it reaches 0.008. Equivalence power at a true interaction of 0 spans 0.000–1.000 across all conditions, with 15 shapes at essentially zero; false equivalence at the margin stays at or below 0.095.
<!-- /table:e9_criteria -->

**Reading. Two of the plan's three criteria do not behave as 13.3 assumes, and both are reported here, before the
grid, as 3.2 requires.**

- **(i) The sign criterion, read as the plan writes it, is not safe at the design's shape.** With the arm effect
  **identical at every level**, it declares a conclusion "level-dependent" up to **0.241** of the time (L = 12,
  τ_LAM = ½τ, M = 6). It is a question of what the effect is: at β = Δ the rate is ≤ 0.013, at β = ½Δ it is 0.241.
  Read as significant-only — a level flips a sign only if its own R5 test resolves — the same rate is ≤ 0.008.
  **At β = 0 the plain rate is ≈ 0.60 by construction** (the sign of noise is a coin), so the criterion says nothing
  about a conclusion that does not exist at the default level.
- **(ii) Requiring every level to clear α′ is close to unmeetable at a small roster.** At β = Δ it holds 0.035–0.050
  of the time at M = 6 and 0.58–0.63 at M = 14. **M decides it, not seeds:** S from 19 to 93 moves it by ≈ 0.05,
  M from 6 to 14 by ≈ 0.55. At α the same criterion holds 0.57–0.61 (M = 6) and 0.97–0.98 (M = 14).
- **(iii) Equivalence is sound only when the level × arm × model term is absent.** Power at a true interaction of 0
  is 0.993–1.000 at τ_LAM = 0 but 0.086–0.668 at ½τ, and at M = 6 with ½τ the interval is 0.83–0.90 of the margin
  wide before any data, so 15 shapes have essentially zero power. False equivalence at a true interaction of exactly
  0.025 stays ≤ 0.095 throughout.
- **Nothing was re-registered after these were read.** The plain reading stays the headline because it is the plan's
  sentence (addendum 9.2); the significant-only reading is reported beside it. What the numbers change is a **team
  decision**, recorded in section 5, not a rule rewritten to fit them.

### 3.3 E9.1 — the parameter list

<!-- table:e9_ranking -->
21 ranked candidates, each at two levels against the default: 100 seeds × 4 scenarios × 3 personas per panel. E is the cell-mean standardised effect, the maximum over a parameter's levels; the oracle effect averages the two co-primary θ. The share is the fraction of 1,000 seed-bootstrap resamples in which the candidate is in the top six.

| candidate | in the plan's six | E oracle | E scripted | rank oracle | rank scripted | rank sum | top-six share |
|---|---|---|---|---|---|---|---|
| **garch_set** | yes | 0.096 | 0.086 | 1 | 1 | 2 | 1.000 |
| **sbar** | no | 0.050 | 0.055 | 3 | 3 | 6 | 0.999 |
| **mu_V** | no | 0.046 | 0.041 | 4 | 5 | 9 | 0.934 |
| **half_life** | yes | 0.032 | 0.054 | 8 | 4 | 12 | 0.999 |
| **jump_rate** | no | 0.037 | 0.016 | 6 | 6 | 12 | 0.638 |
| **sigma_V** | yes | 0.026 | 0.056 | 10 | 2 | 12 | 0.992 |
| jump_sd | no | 0.025 | 0.009 | 11 | 7 | 18 | 0.323 |
| pe_dispersion | yes | 0.033 | 0.000 | 7 | 12 | 19 | 0.068 |
| div_c_speed | no | 0.056 | 0.000 | 2 | 17 | 19 | 0.004 |
| blowoff_g | no | 0.008 | 0.004 | 12 | 8 | 20 | 0.024 |
| analyst_sd | yes | 0.027 | 0.000 | 9 | 13 | 22 | 0.011 |
| sentiment_loading | yes | 0.006 | 0.002 | 14 | 9 | 23 | 0.008 |
| div_tau | no | 0.039 | 0.000 | 5 | 18 | 23 | 0.000 |
| sent_rho | no | 0.006 | 0.001 | 16 | 10 | 26 | 0.000 |
| sent_b1 | no | 0.005 | 0.000 | 17 | 11 | 28 | 0.000 |
| s_eps | no | 0.006 | 0.000 | 15 | 14 | 29 | 0.000 |
| vol_sd_e | no | 0.008 | 0.000 | 13 | 21 | 34 | 0.000 |
| pe_cap | no | 0.005 | 0.000 | 18 | 16 | 34 | 0.000 |
| p_loss | no | 0.000 | 0.000 | 21 | 15 | 36 | 0.000 |
| vol_rho_v | no | 0.001 | 0.000 | 20 | 19 | 39 | 0.000 |
| vol_beta_absr | no | 0.001 | 0.000 | 19 | 20 | 39 | 0.000 |

**The data-driven six:** garch_set, sbar, mu_V, half_life, sigma_V, jump_rate. They share 3 parameters with the plan's six (garch_set, half_life, sigma_V), where the rule asks for five, so **data-driven six** run (P9-6).

**garch_set__high** leaves only 0.958 of its path × persona cells with a day resolvable at θ = 0.05 (sd(x) 0.0740), so MCR there is undefined on the rest (addendum 4).
<!-- /table:e9_ranking -->

**Reference rows, passed before any level panel was read** (`e9_1/reference.json`):

- the default panel's level-free observables oracle, flat MCR at θ 0.05 = 0.07701 (published 0.0770);
- 2,400 rows against `e6_16a/runs.csv`, worst |difference| 3.6 × 10⁻¹⁶.

**Reading.**

- **The ranking was not in Phase 7's files and is computed here**: 21 candidates × 2 levels, plus the default,
  each a panel of 100 seeds × 4 scenarios × 3 personas with the pickled Phase-6 oracles and E7.8's scripted families
  (P9-6).
- **By REG-16 (i)'s rule the data-driven six run,** because they share only three parameters with the plan's six —
  `garch_set`, `half_life`, `sigma_V` — where the rule asks for five. The list is `garch_set`, `sbar`, `mu_V`,
  `half_life`, `sigma_V`, `jump_rate`.
- **The sixth place is not sharp.** The seed bootstrap puts `jump_rate` in the top six in 0.638 of resamples against
  `jump_sd`'s 0.323; the first five are at 0.934–1.000.
- **Three parameters the reviews name fall out**: `pe_dispersion`, `analyst_sd` and `sentiment_loading` (weaknesses
  20, 21, 23). Each moves the scripted policies by 0.000–0.002.
- **What that does and does not mean.** These outcomes contain no LLM. PREREG 1.4 registered the expectation in
  advance: the analyst sd cannot move a scripted policy, because no scripted policy reads the analyst field, yet
  every model in Phase 6's L3 probe answered by comparing price with the analyst estimate (P8-12). A parameter that
  ranks low here and moves LLM behaviour in the grid is evidence about the models, not about the environment.
- **`div_c_speed` is the clearest split**: second on the oracle (0.056) and seventeenth on the scripted policies
  (0.000), so its rank sum keeps it out.
- **One level changed what the yardstick can score.** Under the P75 GJR-GARCH set, 4.25 % of path × persona cells
  have no day resolvable at θ = 0.05, so MCR there is undefined (addendum 4). Its handling was registered before the
  statistic was recomputed, and the correction raised `garch_set`'s oracle effect from 0.066 to 0.096 and its
  bootstrap share from 0.000 to 1.000, without changing which six parameters the rule selects.

Calibration of the half-life levels: addendum 2. The unmatched levels run beside as the registered sensitivity.

### 3.4 E9.2 — roster pilots — **complete**

The shape by PREREG 2's rule is 16 seeds per cell at R = 1: 384 runs per model, df_d 180 (`e9_2/shape.json`). The
three OpenRouter configurations ran **truncated seed lists registered before they started** (addendum 10, 10a):
Haiku 4.5 seeds 3001–3008 (96 pairs), DeepSeek V4 Flash and Qwen3 235B seeds 3001–3004 (48 pairs each).

<!-- table:e9_sizing -->
Band-MAS σ_d at R = 1 per roster configuration, with its one-sided 90 % chi-square limit. The plug-in is the **maximum** of that limit over the roster (P8-16); stage 1's seeds follow Appendix A at the Bonferroni α′ = 0.001389 for Δ = 0.05. A pilot truncated by the clock (addendum 5) or by a registered seed list (addendum 10) carries fewer df, which **widens** its limit.

| configuration | σ_d (R = 1) | 90 % limit | df_d | pairs | source |
|---|---|---|---|---|---|
| `gpt-5-nano|default` | 0.0154 | 0.0168 | 120 | 128 | e9_2 pilot (R = 1) |
| `gemini-2.5-flash|thinking0` | 0.0348 | 0.0380 | 84 | 96 | E8.5 closed form at R' = 1 (P8-15) |
| `gpt-5|default` | 0.0381 | 0.0409 | 180 | 192 | e9_2 pilot (R = 1) |
| `gemini-2.5-flash-lite|default` | 0.0415 | 0.0446 | 180 | 192 | e9_2 pilot (R = 1) |
| `openrouter/qwen/qwen3-235b-a22b-2507|default` | 0.0445 | 0.0528 | 36 | 48 | e9_2 pilot (R = 1) |
| `gpt-5.5|default` | 0.0533 | 0.0572 | 180 | 192 | e9_2 pilot (R = 1) |
| `gemini-3.5-flash|default` | 0.0547 | 0.0588 | 180 | 192 | e9_2 pilot (R = 1) |
| `gemini-2.5-pro|default` | 0.0540 | 0.0590 | 120 | 128 | e9_2 pilot (R = 1) |
| `openrouter/anthropic/claude-haiku-4.5|default` | 0.0556 | 0.0618 | 84 | 96 | e9_2 pilot (R = 1) |
| `gpt-5-mini|default` | 0.0595 | 0.0639 | 180 | 192 | e9_2 pilot (R = 1) |
| `gpt-5.4-mini|default` | 0.0670 | 0.0720 | 180 | 192 | e9_2 pilot (R = 1) |
| `openrouter/deepseek/deepseek-v4-flash|default` **← plug-in** | 0.0809 | 0.0958 | 36 | 48 | e9_2 pilot (R = 1) |

**Plug-in σ_d = 0.0958**, from `openrouter/deepseek/deepseek-v4-flash|default`, taken over **12 of 14** configurations (`openrouter/qwen/qwen3.7-flash|default`, `openrouter/z-ai/glm-4.7-flash|default` not piloted, P9-10). **Stage 1 seeds by Appendix A: 120** (60 by the paired-correct count). Every roster pilot is complete (`complete`: True); the four configurations dropped by P9-7 and P9-8 are reported as `dropped_and_unfinished` and size nothing.
<!-- /table:e9_sizing -->

**Reading.**

- **Every roster pilot finished** (`e9_2/sizing.json`, `complete`: true): six first-party models at the registered
  384 runs, two truncated on the clock (addendum 5), and the three OpenRouter configurations at their registered
  truncated seed lists — **192/192, 96/96, 96/96**, with one contaminated Haiku run discarded and re-run to `ok`.
- **The plug-in is set by the least-piloted model.** DeepSeek V4 Flash's limit, 0.0958 on 36 df, is the maximum, so
  it sizes the grid for everyone at **120 seeds**. Its σ_d (0.0809) is the largest measured, but its *limit* is
  widened further by having only 48 pairs. **This is the direction addendum 10 registered in advance:** fewer seeds
  ⇒ a wider limit ⇒ a larger, more conservative grid. Truncation cannot make the grid look cheaper than it is.
- **The plug-in is over 12 of 14 configurations**, because Qwen3.7 Flash and GLM 4.7 Flash were never piloted
  (P9-10). A configuration that is not piloted cannot drive a maximum, so **120 seeds is a lower bound** on what a
  full roster would have given.
- **The two Claude routes agree once compared like for like — and the naïve comparison would have been wrong.**
  The direct-API pilot's σ_d is 0.0215 with mean_d −0.0032; the OpenRouter route's is 0.0556 with mean_d −0.0959.
  That looks like a large route effect. It is not: **the direct pilot covers 8 of 12 persona × scenario cells**
  (the credit failure stopped it before ENTJ ever ran) while the OpenRouter pilot covers **12 of 12**. On the
  **64 (persona, scenario, seed) cells the two share**, they agree to within a thousandth —
  **mean_d −0.0013 vs −0.0002, sd 0.0219 vs 0.0224**. The gap was a coverage artefact of a missing persona, not the
  route, and the truncated direct pilot would have **understated** σ_d.
- **That is why addendum 10 truncated the seed list from its start rather than stopping mid-manifest**: a balanced
  cell grid loses df but stays unbiased, while an interrupted run loses whole personas. The evidence for the
  distinction arrived after the rule, which is the right order.
- **Provider errors, measured rather than summarised**: 36 HTTP 403s across **76,808 pilot calls (0.047 %)**, every
  one on the Anthropic upstream — DeepSeek and Qwen3 235B saw none. 20 of 192 Haiku runs saw at least one and the
  agent's own attempts absorbed all but three calls in a single run, which the contamination rule discarded whole
  and which was then re-run successfully.

**Two interruptions, both reported rather than smoothed over.**

- **The Anthropic account ran out of credit mid-pilot** (11 Sep, 19:24 UTC). Every subsequent Claude call returned
  HTTP 400 "Your credit balance is too low", so 294 runs failed whole and were discarded by the contamination rule —
  no partial run entered the data. Each had used one of its three attempts when the four processes were stopped.
- **Two pilots were truncated on a clock** (addendum 5), not on their numbers.

**The OpenRouter smokes** (section 3.1 carries the timings): Haiku 4.5 through OpenRouter, pinned to the Anthropic
upstream, parsed 200 of 200 calls in both runs and its token counts sit **within 2 tokens** of the direct-API runs —
evidence that the pinned route serves the same model, though the two routes are still not pooled (addendum 6).
DeepSeek V4 Flash parsed 200 of 200 at **$0.03 per run** measured from the provider's own accounting. **Qwen3 235B
failed all 400 of its smoke calls** on the missing-`max_tokens` defect of addendum 7.

**Both OpenRouter smokes are reported, because the first one does not test the configuration this phase registered.**
The smoke that ran from 08:00 UTC was launched before addendum 7 existed and carries `max_tokens_client: null` on
every row; the cap was registered while it was still running. It is archived, reported and sizes nothing
(addendum 8). Its GLM 4.7 Flash runs never finished — 173 minutes against 89 for the slowest configuration that did —
and were discarded when the process was stopped; a single pinned probe answered in 4.3 s, so the route was live.
$0.56 of spend belongs to those discarded calls and is reported as spend, not as data.

**Under the registered cap, the defect is gone.** Qwen3 235B parsed **200 of 200 in both runs at 803 s and 836 s** —
faster than DeepSeek V4 Flash — which is what promoted it from "dropped" to "piloted" (addendum 10a). Haiku 4.5
repeated at 647 s and 656 s. **Qwen3.7 Flash is the one the clock defeats:** 4,973 s per run, which is 17.7 h for a
192-run pilot at the team's cap of 15 concurrent calls, so it is not piloted (addendum 10).

### 3.5 E9.4 stage 1 — **not run in this phase**

**No grid run was made.** Stage 1 as first designed was withdrawn as priced (section 2's amendment table: $126,000
against the plan's own ≈ $210 for Tier A), and what replaced it is sized by E9.3's criteria stage against the
remaining credit. The pilots that size it were still running when this phase's budget and clock were fixed, so the
sweep's shape — its L, S and M — is stage 2's to fix (PREREG 4.2), with section 5's two open decisions in front of
it. **The manifest machinery is built and exercised**: three truncated pilot manifests were fingerprinted and run
through `tools/phase9/e9_runner.py` (addendum 10), which is the same path a grid manifest takes.

### 3.6 E9.5 — the robustness table — **specified, not populated**

**Fixed with 3.2 (addendum 9), so the table's rules are settled before any grid data exists.** One row per
conclusion × generator parameter, with:

| column | what it holds | rule |
|---|---|---|
| sign at each level | the sign of ĝ_ℓ, the arm contrast at level ℓ | (i) a conclusion is **level-dependent** when any non-default level's sign differs from the default level's; the level is named. The plain and significant-only readings are both reported (addendum 9.2) |
| q at each level | R5's p-value (P9-4), BH within stage 1's single confirmatory family | (ii) the criterion holds when every level's q stays below the level; reported at α and α′ |
| interaction and its 90 % interval | mean over models of r̄_{ℓm} − r̄_{0m}, se = sd/√M on t(M − 1) | (iii) **equivalence is declared only when every non-default level's interval lies inside ± 0.025** (half of `min_effect.band_mas`) |
| verdict | robust / level-dependent / not equivalent | all three criteria, each reported separately rather than collapsed into one word |

**Its operating characteristics are measured** (section 3.2b): what each column does when the answer is known. Two
of the three do not behave as plan 13.3 assumes, and that is reported before the grid rather than discovered in it.

**Why it is not populated.** The table is a reading of stage 1's runs, and stage 1 was not run (3.5). Populating it
needs the grid, the roster size M the team chooses, and the reading of criterion (i) the team chooses — the two
decisions in section 5. **Nothing in the table was tuned to data that does not yet exist.**

### 3.7 The switch, and the proof that it is inert when off

`RunConfig.provider_options` defaults to None.

- **Off:** the log's columns and values are unchanged (`test_provider_options_column_inert`), and Phase 8's golden
  record shows 0 differences with the field declared as a Phase 9 addition.
- **On:** every row carries the JSON record, and `meta.json` carries the field.

### 3.8 The whole test tree

`python -m pytest -q -p no:cacheprovider tests/`, on the finished state
(`docs/env_v2/generated/v2_1/e9_tests_full_final.log`): **239 passed, 2 skipped, 4 xfailed; 0 failed, 0 errors**, in
**26 min 22 s**.

**It was run twice, and both runs are reported.** The first (`e9_tests_full.log`, 26 min 28 s) started at 14:20 UTC,
*before* the last documentation edits landed — §3.4's reading, §6, and a citation fix. A tree run that precedes the
state it certifies is not evidence for that state, so it was re-run on the finished files. **The two runs agree
exactly** (239 / 2 / 4 both times), which is the useful part: the edits changed no test's outcome.

**Against Phase 8** (219 passed, 1 skipped, 4 xfailed; `e8_tests_full.log`), the 20 extra passes reconcile exactly:

| source | passes | skips |
|---|---|---|
| this phase's `tests/test_v2_1_phase_9.py` (20 items) | 19 | 1 |
| `tests/test_v2_1_phase_8.py`'s **29th test**, which Phase 8's own tree log predates | 1 | — |
| Phase 8's total | 219 | 1 |
| **this run** | **239** | **2** |

- **The 29th test is Phase 8's, not this phase's.** Phase 8's report states "the 28 extra passes are this phase's
  tests"; the file collects **29** items today, was committed at 11 Sep 12:30 while `e8_tests_full.log` was written
  at **11 Sep 03:46**, and is unmodified against `HEAD`. Its tree log simply predates its last test.
- **No older test was changed.** `git status` reports no modification to any tracked test file; the only new one is
  `tests/test_v2_1_phase_9.py`, still untracked.
- **The two skips**: this phase's `test_grid_manifest_matches_runs` ("stage 1's manifests are not written yet" —
  by design, E9.4 is not run), and one collection-level skip that Phase 8's run also carried. 244 items are
  collected and the collection-level skip has no progress character, which is why 244 collected and 245 outcomes
  are the same thing counted two ways.
- **The four xfails are unchanged**: the known-defect registry's two derived gates (L2, L2b) and the two permanent
  v1 baseline defects.
- **26 minutes against Phase 8's 5 h 15 min** on the same laptop — Phase 8's run shared the machine with a paid
  batch; this one did not.

### 3.9 Path hashes and the freeze — **0 of 95 changed**

`tools/path_hashes.py` rebuilt all 95 configurations and compared them with Phase 8's reference:
**`changed_non_analyst`: none, `changed_analyst`: 0, `unchanged_analyst`: 190**
(`path_hashes_phase9_after.json`, `path_hashes_phase9_compare.txt`, against `path_hashes_phase8_after.json`).

**The generator is untouched by this phase**, which is what lets E9.1's parameter sweep and E9.2's pilots be read as
measurements of the models rather than of a moving environment. `envs/`, `evaluation/` and `agent/` carry no Phase 9
edit; the only harness change is `RunConfig.provider_options`, proved inert when off (3.7).

---

## 4. Decisions taken and the parameter files

**P9-1** (the team's constraints, its "cost is not a constraint" clause superseded by P9-8) · **P9-2** (the roster) ·
**P9-3** (the staged design) · **P9-4** (R5) · **P9-5** (configurations) · **P9-6** (the sweep runs the data-driven
six) · **P9-7** (Fable 5.1 excluded on cost) · **P9-8** (one $300 OpenRouter budget; the roster re-cut to 14) ·
**P9-9** (the robustness criteria simulated at the design's shape and left exactly as registered, including the
criterion the measurement shows is unsafe) · **P9-10** (Qwen3.7 Flash and GLM 4.7 Flash fail the registered smoke
stopping rule and leave the roster for sizing).

**No parameter file was written or changed by this phase.** `envs/`, `evaluation/` and `agent/` carry no Phase 9
edit and the path hashes are unchanged (3.9). The one harness change, `RunConfig.provider_options`, records how a
client was configured; it is inert when off (3.7) and it is not a generator parameter. What this phase produced
**sizes a design and ranks a parameter list** — it tunes nothing in the environment, which is what lets E9.1's
ranking be read as a property of the generator rather than of a moving target.

---

## 5. Decisions the team must take

| decision | state | the evidence in front of it |
|---|---|---|
| Stage 1's D11 common-start slice, priced | **to be put to the team** | PREREG 4.1 queues the slice after each model's headline cells. At 93 seeds the slice is 3,720 runs per model against the headline's 2,232, so stage 1's wall-clock per model is ≈ 2.7× the headline's (`tools/phase9/e9_2_pilot.stage1_runs_per_model`) |
| Stage 2's context-length factor, stateful arms, REG-1 and REG-9 | open, fixed with stage 2 | the context-level smoke (`e9_0/smoke/smoke_context_*.json`). REG-1's fixed-magnitude rendering and REG-9's phase-restatement side call are not built |
| **Which reading of the sign criterion the robustness table uses** | **to be put to the team** | Plan 13.3's own sentence — the plain reading — falsely calls a conclusion level-dependent up to **0.241** of the time when the effect is the same at every level, and ≈ 0.60 when there is no effect at all; the significant-only reading of the same rule reaches 0.008 (section 3.2b, `e9_3/criteria.json`). The plain reading was registered as the headline **before** these rates were seen (addendum 9.2) and has not been changed after them (P9-9). Changing it now is the team's call to make, in the open |
| **The roster size M the grid runs** | **to be put to the team** | Criteria (ii) and (iii) both turn on M, not on seeds. (ii) holds at every level 0.035–0.050 of the time at M = 6 against 0.58–0.63 at M = 14; (iii)'s equivalence power with a level × arm × model term at ½τ is 0.086–0.109 at M = 6 against 0.551–0.668 at M = 14; S from 19 to 93 moves either by ≈ 0.05. This is the same finding as P8-17 — the model count bounds the contrast — now measured on the robustness criteria themselves |

---

## 6. Files written or changed, compute, and the wall-clock spent

**Files:** `PHASE_9_CHANGED_FILES.md`, regenerated by `tools/phase9/e9_changed_files.py` at the end of the phase.
No parameter file and nothing under `envs/`, `evaluation/` or `agent/` was changed (section 4); path hashes are
unchanged (3.9).

**Compute.** One 8-core laptop. Offline stages ran at 4 workers, paid batches at 13 concurrent calls per model
(15 minus the 2 the live smoke held registered) and 10 for Qwen3 235B. **Offline compute starves paid batches on
this machine**, which is why the criteria sweep was sized to finish before the pilots' first batch landed.

| stage | wall-clock, 12 Sep 2026 UTC | note |
|---|---|---|
| OpenRouter smoke, **uncapped** | 08:00:49 → 10:53 (2 h 52 min) | **discarded** (addendum 8); GLM ran 173 min without finishing a run |
| OpenRouter smoke, capped | 10:58:24 → 11:50:54 (52 min) | 6 of 10 runs completed; the other 4 failed the stopping rule (P9-10) |
| E9.3 `criteria` | ~7 min at 4 workers | 432 conditions × 2,000 datasets |
| **The three pilots** | **11:15:50 → 14:10:14 (2 h 54 min)** | 384 runs, 76,808 calls, one contaminated run re-run |
| Path hashes (95 configurations) | ~1 min | 0 changed |
| `score` (3,861 runs) + `analyse` | ~3 min | 0.04 s per run |
| The whole test tree | section 3.8 | run once, at the end |

**Spend, read from the provider and not from a price table.**

| item | amount |
|---|---|
| account debited | **$115.27** |
| summed provider-reported per-call cost over every ledgered run | $111.84 |
| — Claude Haiku 4.5 via OpenRouter (192 pilot + 4 smoke runs) | $106.68 |
| — DeepSeek V4 Flash (96 + 2) | $2.86 |
| — Qwen3 235B (96 + 2) | $2.30 |
| **remaining of the $300** | **$184.73** |

The $3.43 between the debit and the per-call sum contains the discarded runs' spend **and** a drift between per-call
reported costs and the account debit; **this phase cannot separate them**, and no dollar figure is attributed to the
discarded runs (addendum 11a, which withdraws an earlier attribution that the later data contradicted).

## 7. What was not done, and who owns it

| not done | why | owner |
|---|---|---|
| **The grid itself — E9.4 stage 1 and stage 2** | stage 1 as first designed was withdrawn as priced ($126,000 against the plan's ≈ $210 for Tier A, section 2); what replaces it is sized by E9.3's criteria against the remaining credit, and its shape needs section 5's two decisions | the team, at stage 2's fixing (PREREG 4.2) |
| **The robustness table populated (E9.5)** | its columns and rules are fixed and its operating characteristics measured (3.2b, 3.6), but it is a reading of grid runs that were not made | follows the grid |
| **Qwen3.7 Flash and GLM 4.7 Flash piloted** | both failed the smoke stopping rule registered before they ran (addendum 8, applied in 11; P9-10). Qwen3.7 Flash is 4,973 s per run — 17.7 h for a pilot at the team's cap | a later phase, if the roster wants a second open-weight family |
| **Claude Sonnet 5, Opus 5 and Fable 5.1 piloted to completion** | the Anthropic account ran out of credit mid-pilot and the phase has one $300 OpenRouter budget (P9-7, P9-8). Their partial runs are reported and size nothing | the team, if Anthropic credit returns |
| **The direct-API Haiku runs pooled with the OpenRouter route's** | they are a different route; addendum 6 registered that they are not pooled. The token counts agree within 2 tokens, so they are reported as a route sensitivity | — |
| **`upstreams_served_by` wired into the runner** | the serving upstream never reaches the LangChain callback. The pin is enforced in the request by `allow_fallbacks: false` (which fails closed, measured) and audited out of band through the generation endpoint | a later phase, if per-run auditing is wanted |
| **The context-length factor, the stateful arms' σ_d, REG-1 and REG-9** | not in stage 1 (PREREG 4.1). REG-1's fixed-magnitude rendering and REG-9's phase-restatement side call are not built | stage 2 |
| **α′ re-read at the design's own family count** | it stays at E8.5's 36 until section 4's design is fixed; the cached p-values allow it to be re-read without re-simulating | stage 2 |
