# Prompt: execute Phase 9 of the v2.1 improvement plan (sensitivity through the LLM harness — the generator parameters swept through a robust LLM grid, sized by Phase 8's power analysis, run as fast as the providers allow)

## What this project is

**FinPersona-Bench** asks a question about LLM agents, not about markets: *when an LLM is given a persona with an
investment mandate — a risk band, a target allocation — does it keep to that mandate as market conditions change, or does
it drift?* An agent is run day by day through a multi-day market, sees a rendered snapshot (price, technicals, sentiment,
implied volatility, an analyst estimate, EPS and dividend fields), and allocates between cash and a risky asset. The
score is **mandate-conformity**, not profit: how far the agent's allocation sits outside the persona's band.

Phases 1–5 rebuilt the generator so that every parameter is fitted or tested on data; Phase 6 did the same for the
yardsticks and computed the go/no-go checkpoint (16A, not met; the team took **D17 = restrict the claim**, P7-1);
Phase 7 settled the scoring; **Phase 8 made the harness honest and specified, validated and sized the inference.**
**Phase 9 is the first phase whose product is LLM behaviour at scale:** the generator parameters that drive results,
swept through an LLM grid, to show which conclusions survive the environment's own uncertainty.

**The governing rule of the whole programme: every generator parameter is fitted or tested on data, never stipulated.**
In your phase that reads: **the grid's size, its roster, its parameter list and its robustness criteria each follow a
pre-registered rule applied to measured inputs — Phase 8's variance components, its power table and its simulated
estimator sizes — and no conclusion is called robust unless its criterion was fixed before the runs were read.**

---

## Two constraints from the team that govern this phase, stated first

**1. Cost is not a constraint. Robustness is not to be compromised to save money.** Do not shrink seeds, models,
replicates, scenarios or reference cells to fit a budget; do not substitute a cheaper model for the one the design
needs; do not drop a validation because it costs API calls. Where Phase 8's rules say a design needs N, the design
gets N. Record this as a TEAM decision in `DECISION_LOG.md` (P9-1) with today's date — it replaces the budget-tier
framing of D2 and of the plan's Section 13.2.

**2. Wall-clock time is a constraint. Parallelise everything that can be parallelised and run everything faster —
but paid API concurrency is capped at 10–15 concurrent calls per model.** The providers are paid APIs; stay inside
10–15 in-flight requests for each model's batch (Phase 8 ran Flash at 16 workers and GPT-5 mini at 12 with **0 rate-limit
errors**, `e8_5/run_main.log`, `e8_5/run_transfer.log`). Speed therefore comes from:

- **running every model's batch at the same time** — the cap is per model, so a roster of M models is M × 10–15
  streams, and Phase 8 says the roster needs more models anyway (item 3 below);
- **never letting a model wait for another**: smoke tests, pilots and batches of different models overlap;
- **putting every offline stage on parallel hardware** (the lab box, Kaggle, or all laptop cores) while the API
  batches run, and building the analysis pipeline on simulated and pilot data *before* the batches land, so results
  are read the hour a batch finishes;
- **removing serial waits in the process**: the pre-registration, the tools, the tests and the report skeleton are
  written while the smokes run.

**When the two constraints collide** — a robust design that the capped concurrency cannot finish in the time
available — **do not quietly cut the design and do not raise the concurrency.** Put the wall-clock table (below) to the
team with the options located (more models in parallel, fewer generator settings at full robustness, a staged grid
whose first stage answers the headline question) and record what they choose.

**Do not use the providers' batch APIs.** They halve the price and multiply the latency (a lock-step runner submits
one simulated day per batch, 200 batches per run): they trade time for money, which is the opposite of this phase's
constraint.

---

## The document landscape

**The single working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`.** Its shape:

| Section | What it is |
|---|---|
| 0 | What was verified before the plan was written |
| **1** | **The protocol every phase follows** — pre-register, fit or test everything, report failures as failures; the power-analysis rules |
| 2 | Weakness-to-phase map |
| 3 | Data sources, their substitutes and their biases |
| 4–14 | **Phases 0–10**, one section each. **Section 13 is yours: Phase 9, sensitivity through the LLM harness** (13.1 parameters, 13.2 grid and cost, 13.3 robustness criteria, 13.4 tests, 13.5 blockers) |
| 15 | Cross-phase compute, cost and effort — your row: "≈ 9 h wall-clock per model per tier at 15 concurrent calls of ≈ 2 s", **written for 5 seeds; Phase 8 re-sized the grid (below)** |
| **16 / 16A** | Order and the go/no-go checkpoint; 16A not met, **D17 taken (restrict the claim, P7-1)** — size the grid for the restricted claim |
| 17 | Decisions only the team can make — **D2 (roster and budget) is re-framed by the team's constraints above**; do not pre-empt D3, D5, D15 |
| A / B / C | **Appendix A is the power rule**; Phase 8 applied it (P8-1, P8-15, P8-16) |

Around it:

- `V2_1_ALTERNATIVES_REGISTER.md` **entry 16 (the LLM sensitivity grid) is yours to apply, not to re-open**: (i) the
  parameter set by the pre-registered ranking rule — the six generator parameters with the largest standardised effect
  on the level-free observables-oracle regret and on the scripted policies' band-MAS (E7.8), run the plan's six if the
  two lists share at least five, the sixth of the data-driven list as a further cell; (ii) the stateful arms' inclusion
  on the two highest-ranked parameters only if the minimum effect is detectable at the design's seeds with ≥ 0.8
  power; (iii) the tier — now governed by the team's constraints above. **Entries REG-1 (the LLM magnitude test,
  ≈ 60 runs) and REG-9 (the phase-restatement probe, ≈ 90 runs) run in this phase** (plan 13.1).
- `reviews/V2_WEAKNESSES.md` — yours: **8, 10, 12, 20, 21, 23 (LLM side), 29** (plan Section 13). Read each before
  pre-registering; the report closes each as fixed, a labelled design choice with a sensitivity, or a failure.
- `decisions/DECISION_LOG.md` — **the P8-* entries are the freshest precedent**; read **P8-8** (a gate that stopped a
  spend and the configuration the team chose), **P8-15** (a registered limit that failed its known-answer check and
  what replaced it, decided before data), **P8-16** (the sizing), **P8-17** (a pre-registered adoption rule applied as
  written when the result was inconvenient), **P8-18** (a defect found on a known answer, fixed, re-run).
- `generated/v2_1/` — every machine-written result. Yours will be `e9_*`.
- `experiments/params/inference.json` (loud loader `experiments/inference_params.py`) — **every statistical choice
  your contrasts are made with is already a parameter with provenance.** Read it through the loader; do not retype a
  rule from the report.
- `tests/known_defects.py` — its two entries (the derived L2 / L2b gates) are not yours; carried.

---

## Context for this phase: what Phase 8 measured, and what it changes for you

Every number below is a measurement in `PHASE_8_REPORT.md` and the file it names.

**1. The grid is sized, and the size is not the plan's.** By the registered rule the main grid needs **93 seeds per
persona × scenario cell at R = 1** (Appendix A as written, Bonferroni α′ = 0.05 / 36; P8-16;
`e8_5/transfer.json`, `experiments/params/inference.json` block `main_grid_sizing`). The inputs: Gemini 2.5 Flash's
band-MAS σ_d(R = 1) 0.0348 with a closed-form 90 % upper limit 0.0380 (576 runs, 96 seed-level pairs); GPT-5 mini's
σ_d on the same bull-trap seeds **2.21× Flash's [1.88, 2.99]**. Flash alone would need 19; the paired-correct count is
47; at the ratio's upper limit 169. **Seeds, not replicates**: runs per contrast cell are 38 / 68 / 96 at R = 1 / 2 / 3
(σ²_int is 72 % of Var(d) at R = 1). The plan's Tier A (5 seeds) detects a band-MAS difference of 0.097 — twice D12's
Δ = 0.05. **Your pre-registration must say which contrasts the 93 applies to** (P8-16 sizes the arm contrast per
persona × scenario cell at the family's Bonferroni α′) and derive, by the same rule, what the robustness criteria of
plan 13.3 need — a sign test, a q-value in the crossed model and an equivalence interval at half of D12 are three
different power problems. **Do not carry 5 seeds forward because the plan wrote it.**

**2. The transfer check failed, so no model's variance may be assumed.** The excess of GPT-5 mini over Flash is
seed × arm variance (σ²_int 0.00416 against 0.000804 on bull-trap, 5.2×), **not** replicate noise (1.35×), so the
temperature difference (GPT-5 mini accepts only 1.0) does not explain it. A third model's σ_d is unknown. **Cost is
not a constraint, so measure every roster model's σ_d with a variance pilot before sizing on it** — the E8.5 runner
(`tools/phase8/e8_5_variance_pilot.py`: per-run checkpoint, ledger, cost gate, resumable) is the pattern, and the
pilots of different models run at the same time.

**3. The number of models, not the number of seeds, bounds a confirmatory contrast when the arm effect varies by
model** (P8-17; addendum 17). With E8.5's measured components planted and a model × arm sd of 0.03 (a DESIGN value —
one model cannot measure it), at six models and nineteen seeds **neither the crossed model (E1) nor the two-way
cluster bootstrap (E2) holds size** (8.5–13.5 % at α = 0.05). A t reference with M − 1 df restores size — post hoc,
not adopted — and then power at α′ is 0.025–0.075. The model-level DESIGN table (`e8_5/power.json`, t with M − 1 df at
α′, 19 seeds per cell) at a between-model sd half the σ_d limit: **0.006 at two models, 0.025 at three, 0.25 at five,
0.86 at eight**; at a between-model sd equal to the limit, 0.22 at eight. **The roster size is a statistical input,
and the reference distribution for model-level contrasts is yours to pre-register** (Phase 8 carried it to you). With
cost not binding, a larger roster also buys wall-clock, because concurrency is capped per model.

**4. The mixed model is descriptive; the contrast intervals are E2's; both carry their simulated size.** E1-amended
(E1 on seed-level differences, which pairs within persona × path) was **not adopted by its pre-registered rule**, so
by that rule's fallback no mixed-model p-value decides a claim (P8-17). `tools/stats_v2.crossed_mixed_model` fits at
the better of the lbfgs and Powell optima with `optimizer="best"` — **lbfgs stops at a local optimum in 15–20 % of
E1's fits and 34–61 % at a zero-variance boundary** — and `run_stats_v21` uses it. Flash's variance sits in
**persona × path** (ICC 0.82 for band-MAS; `e8_5/components_reml_persona_path.json`); E1 as registered does not pair
on it (its SE is 2.48× the paired SE at R = 1 at the better optimum; `e8_5/e1_pairing_se.json`). Plan 13.3 (ii) asks
for "the BH-corrected q in the crossed mixed model with the generator level as a fixed factor": **that criterion now
needs re-specifying against P8-17 in your pre-registration, with its size simulated on Phase 8's measured components
before a single grid run is read** (`tools/phase8/e8_3_simulate.py --stages mixed_pp` is the harness to extend).

**5. Multiplicity and the temporal null are settled rules.** On a grid with more than one confirmatory family,
**Benjamini–Yekutieli across families decides** and BH within family is reported beside (P8-10;
`inference_params.decision_rule`); families are counted from the tests computed (`family_table`). Tier C carries two
near-duplicate D tests (|r| 0.992 between θ 0.05 and 0.0020). **Temporal claims rest on the path-level sign-flip
only, which cannot reject with fewer than six paths** (P8-11).

**6. The harness the grid runs is `harness_version="v2_1"` and `placebo_version="v2_1"`** (P8-4, P8-5): the nearest-copy
mandate offset, matched stateful histories, fallbacks stored as "no valid answer", provider token counts with the
method logged, and the placebo matched per persona. The context-length factor is **{5, 20, 50, full}** (P8-7); per
200-day run the input grows from **0.38 M tokens (stateless) to 1.2 M (rolling 5), 3.5 M (20), 7.6 M (50) and
14.2 M (full)** (`e8_2/context_cost.json`) — longer contexts are also slower calls, so price and **time** the stateful
levels before including them.

**7. The model configurations are measured and some are forced.** Flash runs with **thinking off**
(`thinking_budget=0`, P8-8: with default thinking a run cost $0.934 and took ≈ 28 minutes; off, $0.165 and ≈ 4–6
minutes). `langchain_openai` **silently drops any temperature other than 1 for gpt-5 models** (addendum 6). **Claude
Sonnet 5 and Opus 5 reject any temperature** (HTTP 400; P8-12) and return thinking blocks — keep only a reply's text
parts. **`RunConfig` has no provider-options column**, so a run's CSV cannot say whether its model thought: add it
before the grid runs (carried from Phase 8, addendum 9). A variance pilot measures the configuration the grid runs;
change a configuration and the pilot is re-run.

**8. The models read the analyst field, not the mispricing.** Phase 6's L3 probe (P8-12): all five models (Flash,
GPT-5 mini, Sonnet 5, Haiku 4.5, Opus 5) are at chance on the over/under-valuation question, because 93–99 % of their
answers follow "over-valued iff price > the analyst fair-value estimate", a rule itself at chance in this environment.
**The analyst error sd is one of your six parameters (plan 13.1): expect it to move behaviour more than its place in
the table suggests, and pre-register what that would and would not mean.**

**9. The salience shares are identified only on the common-start slice with the NONE reference** (D11 = P8-13, P8-14),
with seed-cluster bootstrap intervals that keep every copy of a resampled seed in one fold (P8-18). The day-1 gate's
null stays **NOT COMPUTABLE** under NONE only. If the grid carries the slice, its cells are ≈ 150 stateless runs per
model at a Tier-A size — re-derive at your seed count.

**10. Measured throughput — the basis of every wall-clock number you write.** From the E8.5 ledgers
(`e8_5/ledger_thinking0_gemini-2.5-flash.jsonl`, `e8_5/ledger_default_gpt-5-mini.jsonl`), 200 calls per stateless run:

| model | workers | runs / h | effective concurrency | median s / run | $ / run |
|---|---|---|---|---|---|
| Gemini 2.5 Flash (thinking off) | 16 | 133 | 14.7 | 336 | 0.1646 |
| GPT-5 mini (temperature 1.0) | 12 | 29 | 12.8 | 1,590 | 0.3292 |

A run's 200 calls are sequential (each day depends on the last), so **one stream finishes ≈ 9 Flash runs or ≈ 2.3
GPT-5 mini runs per hour**; nothing but more concurrent streams makes a batch faster. Illustration only (your tool
computes the real table): one static–memory contrast over 12 persona × scenario cells at 93 seeds is 2,232 runs per
model — ≈ 17 h on Flash and ≈ 65 h on GPT-5 mini at 15 streams; the plan's Tier A shape at 93 seeds (13 settings ×
3 personas × 2 arms × 3 scenarios) is 21,762 runs per model — ≈ 6–7 days on Flash and ≈ 4 weeks on GPT-5 mini at 15
streams. **This is why the wall-clock table comes before the design is fixed.**

---

## Read first, in this order

1. **Section 13 of the plan**, then Section 17 (D2) and Appendix A.
2. **`PHASE_8_REPORT.md` sections 0, 3.4 (with the `mixed_pp` and `mixed_optimizer` tables), 3.5, 3.6, 5 and 7**, and
   `PREREG_PHASE_8_ADDENDUM.md` items **8, 9, 16, 17, 18, 19**.
3. **`DECISION_LOG.md` P8-8, P8-9, P8-10, P8-11, P8-15, P8-16, P8-17, P8-18.**
4. **`V2_1_ALTERNATIVES_REGISTER.md` entries 1, 9 and 16**, and weaknesses 8, 10, 12, 20, 21, 23, 29.
5. **The code you will build on**: `tools/phase8/e8_5_variance_pilot.py` (the resumable, checkpointed, ledgered, cost-gated
   runner), `tools/phase8/e8_5_analyse.py` (components, power, transfer), `tools/phase8/e8_3_simulate.py` (the
   estimator simulations), `tools/stats_v2.py` (`run_stats_v21`, `crossed_mixed_model(optimizer=)`, `pigeonhole_ci`,
   `path_sign_flip`), `experiments/arms_v2.py`, `simulation/runner_v2.py`, `experiments/inference_params.py`.
6. **`tools/phase8/`'s procedure tools** — `e8_report_tables.py`, `e8_cite_check.py`, `e8_changed_files.py`,
   `e8_write_params.py` / `e8_write_inference.py`. **Copy to `tools/phase9/` and adapt; do not invent a new discipline.**

---

## Decisions: what governs what you may start

**Start immediately, no decision needed:** the parameter ranking of REG-16 (i) on Phase 7's files; the wall-clock and
throughput tool; the grid manifest and `test_grid_manifest_matches_runs`; the provider-options column; the estimator
simulations for the robustness criteria on Phase 8's measured components; the analysis pipeline on simulated grids.

**Ask the team in your first message, with the tables in front of them:**

- **The roster** (D2, re-framed): which models, given that the model count bounds confirmatory contrasts (item 3) and
  multiplies throughput (item 10). Keys exist for Gemini, OpenAI and Anthropic (plan 0); Opus 5 and Sonnet 5 are
  priced and reachable; open-weight anchors need a key that does not exist. Show the model-level DESIGN table at the
  candidate roster sizes and the wall-clock of each.
- **The design against the clock**: the wall-clock table (every candidate design × roster, at 10 and at 15 concurrent
  calls per model, from the measured throughput, with a smoke-measured row for every model not yet timed) and the
  options where the robust design and the time available collide.
- **The reference distribution for model-level contrasts** is a pre-registration decision; present the simulated
  size and power of the candidates (normal, t with M − 1 df, the two-way bootstrap) on Phase 8's components at the
  candidate roster sizes **before** asking.

**Do not pre-empt** D3, D5, D15, or anything Phase 10 decides. **No paid batch before the roster, the design and the
pre-registration naming the seed list exist.** Smoke tests (a handful of runs per model to time it and check its
configuration) may run as soon as the roster candidates are named — they are what the wall-clock table needs.

---

## What Phase 8 hands you (do not redo this work)

- **The sizing and every input to it**: `e8_5/{per_run.csv, components.{csv,json}, power.{csv,json}, transfer.json,
  e1_pairing_se.json, components_reml_persona_path.json}`; the inference parameters with provenance
  (`experiments/params/inference.json`, including `main_grid_sizing`).
- **The validated statistics and their measured sizes**: `e8_3/{mixed, mixed_gpath, mixed_pp, mixed_optimizer,
  mixed_tref_posthoc, multiplicity, null}.json`; `tools/stats_v2.py`'s v2.1 functions.
- **The harness**, corrected and switched (`harness_version`, `placebo_version`), with `agent/params/harness.json`.
- **The runner pattern** for paid batches: `tools/phase8/e8_5_variance_pilot.py` — dry-run, smoke, gate, run, status;
  per-run CSV + meta + billed-usage record; a contamination rule; per-model ledgers keyed by configuration.
- **L3's answers** (`e6_l3/`), the salience identification and its fixed bootstrap (`e8_4/`).
- **The freeze and the tree**: path hashes 0 of 95 changed; **the whole test tree 219 passed, 1 skipped, 4 xfailed, 0
  failed** — the baseline your run is compared against (1 h alone on the laptop; 5 h 15 min when it shared the CPU
  with a 7-worker job and the laptop slept).

---

## What to do now: Phase 9, Section 13 of the plan

- **E9.1 The parameter list** (REG-16 (i)): compute the ranking from Phase 7's files by the pre-registered rule, apply
  the five-of-six test, and state the list before any run.
- **E9.2 Roster pilots**: a variance pilot per roster model not measured in Phase 8, in E8.5's shape or the smallest
  shape that gives each model's σ_d with a closed-form upper limit (P8-15's method), all models at once; each model's
  configuration logged per row. Re-derive the grid's plug-in from the measured σ_d of the models the grid actually
  runs, by P8-16's rule (the maximum over models, not a transfer ratio from one).
- **E9.3 The robustness criteria, validated before the grid**: plan 13.3's three criteria re-specified against P8-17 —
  the sign criterion, the model-level test with its pre-registered reference distribution, and the equivalence
  interval at half of D12 — each simulated for size and power on Phase 8's measured components at the grid's shape.
  **A criterion that cannot be met by construction is found here, on a known answer, not after the grid** (Phase 8
  found two: clause (i) of E8.4 and "the directive interval covers 0").
- **E9.4 The grid**: generator settings × personas × arms × scenarios × seeds × models as the pre-registration fixes,
  every model's batch in parallel at 10–15 concurrent calls, checkpointed per run, with provenance hashes, every cell's
  baselines rebuilt on its own path (Phase 7), and the common-start NONE slice if D11's cells are in the design.
  REG-1's magnitude test and REG-9's phase-restatement probe run beside it.
- **E9.5 The robustness table**: per conclusion and generator level, the sign, the model-level test, the equivalence
  interval, with BY across families deciding; interactions reported with intervals regardless; the content-thesis
  decision rules evaluated at every level (plan 13.3).

**E9.2 and E9.3 are the deliverables that decide whether E9.4 can make a robust claim at all; E9.4 is the one that
takes the wall-clock.** Order the work so that E9.2's pilots and E9.3's simulations run in parallel with each other
and with the tooling for E9.4.

---

## Speed: how to parallelise this phase

- **API batches**: one batch per model, all models concurrently, **10–15 in-flight calls each**; a smoke first for any
  model or configuration not yet timed; per-run checkpoints so an interruption costs only the runs in flight; a
  ledger per model and configuration; progress lines with an ETA in every batch log (Phase 8's E8.4 bootstrap printed
  nothing for five hours — do not repeat that).
- **Throughput is measured, not assumed**: the wall-clock tool reads the ledgers (runs per hour, effective
  concurrency, seconds per call) and is re-run after every smoke; latency varies by model, reasoning setting and
  context length.
- **Offline compute**: estimator simulations, bootstraps, refits and the test tree go where the cores are.
  - **The lab box** (128 cores, 32 GiB cgroup; verified as a reference machine at P6-15): code reaches it by pushing
    to the public repository and fetching changed files per file through the proxy — **pushing requires the user's
    explicit go-ahead each time**; re-run the numeric check each session; the tunnel drops for minutes to hours, so
    launch under `tmux` and poll. **API keys do not go to the box without the user's explicit permission.**
  - **Kaggle** (4-vCPU CPU kernels, several at once): simulation-only work without ceremony; anything that fits a
    model reproduces a reference row there first (a surrogate result once failed to reproduce, Phase 1).
  - **The laptop** (8 cores): long jobs in the background with `python -u`, staged and resumable; **the laptop sleeps
    when its battery runs down** — background jobs survive sleep but not a power-off, so keep it on power during
    batches and checkpoint everything.
- **Vectorise before you parallelise, and prove the vectorised form equals the loop** (rule 18); Phase 8's power
  validation went from 49 s to 0.86 s per dataset that way.
- **The test tree runs once, at the end**; if it must run sooner, run only the affected test files. `pytest-xdist` is
  not installed; installing it is a choice to validate against a serial run first (golden-record and file-reading tests
  must still pass in parallel).

---

## Hard rules (from the plan; not optional)

1. **Pre-register before you run.** `PREREG_PHASE_9.md` exists before the first paid batch, with: the parameter list and
   its ranking, the roster, the design and its seed list, the robustness criteria with their simulated size and power,
   the model-level reference distribution, the families and their counts, and the wall-clock plan. A rule that later
   proves wrong goes in `PREREG_PHASE_9_ADDENDUM.md`, stated as loudly as a confirmation.
2. **Every statistical method is validated on simulated data with a known answer before it touches a real contrast** —
   at the grid's shape and Phase 8's measured components. Size and power, both reported.
3. **No harness change alters the environment.** `envs/` is not yours; the 95-configuration path-hash fixture is
   byte-identical at the end; Phase 7's scoring files are read, never edited.
4. **Every change to the agent, the arms, the runner or the statistics is a switch with the current behaviour behind it,
   proved inert when off.**
5. **Report failures as failures, with evidence. Numbers carry their `n`.**
6. **`datasets/` is git-ignored and must never be uploaded anywhere** — not to the box, not to Kaggle.
7. **Work stays on `main`. Do not create branches. Commit only when asked**, one-line message, no body, no trailers.
   **Never push unless asked.**
8. **No paid batch before the roster, the design and the pre-registration exist.** A design that moved after the first
   batch is not the pre-registered design.
9. **Robustness is not traded for money** (team constraint 1). **Concurrency stays at 10–15 calls per model** (team
   constraint 2).

### Method rules Phases 4–8 learned the expensive way

10. **Pin the configuration a tool measures** (P4-19) and **measure after the parameter file settles** (P4-45).
11. **Verify every file you cite exists** (P4-37); run the cite check on every document.
12. **Run the WHOLE test tree** once at the end (P4-38); the older tests are what break — say whether you updated one to
    a replaced contract or weakened it (P7-16).
13. **Read a parameter file back through its loud loader before reading a result under it** (P6-12).
14. **A statistic and its null come from one tool with one construction** (P6-7).
15. **Generate every report table from its file** and test the read-back (`e8_report_tables.py --check`).
16. **Make every chain resumable and staged**; anything over ten minutes in the background, with progress output.
17. **A generated list that lists itself flips on every write** — exclude it.
18. **Do not vectorise a statistic without proving the vectorised form equals the loop.**
19. **Every number in a document comes from a file written by a repository tool** — no inline or scratch-folder
    analysis behind a published number (Phase 8 addendum 19 moved four such analyses into stages at close-out).
20. **A REML estimate is the higher of the lbfgs and Powell optima** (`crossed_mixed_model(optimizer="best")`); a
    "converged" lbfgs fit can be a local optimum (P8-17).
21. **A resampled cluster's copies stay in one cross-validation fold** (P8-18); relabelled copies leak.
22. **Check special-function results for NaN and for integrals that miss concentrated mass**: SciPy's noncentral-t CDF
    returned NaN in Phase 8's power table, and the first replacement returned 0 where the mass sat below 6 × 10⁻⁵
    (addendum 19). A table cell reading `nan` is a defect, not a result.
23. **A variance pilot measures the exact configuration the grid runs** — thinking budget, temperature, provider options —
    and the configuration is logged per row (P8-8, addendum 9).
24. **Provider quirks are facts to test, not to rediscover**: gpt-5 temperature dropped silently; Claude 5 rejects
    temperature and returns thinking blocks; Gemini's output tokens include thinking tokens; parse text parts only
    (P8-12, addendum 6).
25. **An estimator validated at one design is re-validated at another**: E1 and E2 held size at six models with ten
    seeds and failed with nineteen (P8-17). More seeds change what governs the uncertainty.

---

## Documentation: keep it current as you go, not at the end

- **`PHASE_9_REPORT.md` written as results land**, under the protocol's six headings, with the citation table, the
  robustness table, per-parameter effect plots generated from files, and **the wall-clock actually spent beside the
  plan's**.
- **Every decision gets a DECISION_LOG entry (`P9-*`)** with the alternative rejected and the evidence file — P9-1 is
  the team's two constraints.
- **The grid manifest** and `test_grid_manifest_matches_runs` (plan 13.4): every planned cell has a run file with the
  right hashes and configuration.
- **`IO_CONTRACT.md`** updated for the provider-options column and any new log field; **`PHASE_9_CHANGED_FILES.md`**
  generated from git and verified against disk.
- The plan's amendments recorded **in your report, not by editing the plan**.

---

## Inherited open items

- **D2** — re-framed by the team's constraints: the roster and the design against the clock (above).
- **The reference distribution for model-level contrasts** — carried from P8-17; yours to pre-register.
- **The stateful arms' σ_d** — E8.5 was stateless, so REG-16 (ii) has no measured input; measure it or state the power
  the design would have and leave the inclusion to the team.
- **The provider-options column** — carried from Phase 8 (addendum 9).
- **The day-1 gate's null** — NOT COMPUTABLE under NONE only (P8-14); O3 cannot run in v2.
- **Within-run trend claims** — only with the path-level sign-flip across ≥ 6 paths (P8-11).
- **Co-primary θ's duplicate D test** in tier C (|r| 0.992) — the team's, if it wants one θ for D.
- **The transfer ratio's single scenario and temperature** — superseded if every roster model gets its own pilot.
- **`evaluation/criteria.py` and `params/phase6_criteria.json` outside the freeze patterns** — Phase 10.
- **The two known-defect registry entries**, the all-rows L2 centred reading, items 7 and 12 — not yours, carried.
- **E8.5's raw runs live only on the laptop** (`results_v2/` is git-ignored); the scored tables are tracked.

---

## My recommendation for how to begin, and why

1. **First message: P9-1 recorded, then the roster question with the model-level DESIGN table and a first wall-clock
   table** — and in the same hour, start the parameter ranking, the wall-clock tool and the smoke tests of every
   candidate model not yet timed, because none of them waits for an answer.
2. **Build the robustness criteria's simulation before anything else statistical.** Phase 8's two most consequential
   findings (P8-15, P8-17) were an interval that did not cover and estimators that did not hold size at the design that
   mattered — both found only because the design was simulated first.
3. **Pilot every roster model at once.** The transfer check was off by a factor of two; the grid must be sized on the
   models it runs.
4. **Price the grid in hours, not dollars.** With cost free and concurrency capped, the design question is how many
   model-streams finish the robust design in the time the team has.
5. **Expect the wall-clock table to be uncomfortable**, and put it to the team rather than cutting the design; and
   **expect at least one pre-registered criterion to be unmeetable by construction** — find it on simulated data.

---

## Deliverable of this request

`PREREG_PHASE_9.md` (before the first paid batch), the tools under `tools/phase9/`, the parameter ranking, the roster
pilots with each model's σ_d and closed-form limit, the robustness criteria with their simulated size and power at the
grid's shape, the grid manifest and its test, the grid's runs with per-model ledgers and configurations, the robustness
table, `PHASE_9_REPORT.md` with the wall-clock spent, DECISION_LOG entries `P9-*`, `IO_CONTRACT.md` updated,
`PHASE_9_CHANGED_FILES.md`, path hashes unchanged (0 of 95), the whole test tree once at the end.

Then stop for review — Phase 10 corrects every document against the numbers this phase produces.
