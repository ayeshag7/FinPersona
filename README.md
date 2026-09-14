# FinPersona synthetic market environment v2.1: the grid runner branch

This branch holds only what is needed to build, run, verify and score the main grid experiments (E9.4) of the
v2.1 programme: the finalised synthetic market environment, the LLM harness, the paid-call runner and the grid
tooling. It was cut from `main` at commit `470bc5c` on 14 September 2026.

Everything else lives on `main` and is deliberately absent here: the phase reports and pre-registrations, the
decision log, the analysis tools of Phases 0 to 9, the v1 environment, old results and the third-party data panel.
When you need the reasoning behind a number, read `main`; when you need to run the grid, stay here.

**The environment code on this branch is byte-identical to `main`.** Two checks prove it, and you should run both
before spending money (section 3).

## 1. What is in this branch

| path | what it is |
|---|---|
| `envs/synthetic_market.py`, `envs/v2/` | the synthetic market environment: the calibrated generator (GJR-GARCH-t volatility with jumps, an AR(1) mispricing process, scripted events and phases, the observables), and its fitted parameters in `envs/v2/params/*.json` |
| `agent/` | the LLM agent (`v2_agent.py` stateless, `stateful_agent.py` the memory arms), the prompts, the persona mandates (`personas/mbti_profiles.json`), the harness settings (`params/harness.json`) |
| `simulation/` | the day loop (`runner_v2.py`), the portfolio, dividends, and `provenance.py`, which stamps every run with the environment code hash |
| `experiments/arms_v2.py` | `build_config`: arms, factors and their defaults; `experiments/params/inference.json`: the statistical settings in force |
| `evaluation/` | scoring (`metrics_v2.score_run`), the mandate bands (`targets.py`), the scoring parameters (`params/scoring.json`) and the audit modules the environment exposes |
| `tools/phase9/e9_roster.py` | the model configurations (the roster) and how each client is built, including the OpenRouter pins |
| `tools/phase9/e9_runner.py` | the paid-call runner: fingerprinting, per-run checkpointing, the 15-call concurrency cap, the contamination rule, per-model ledgers |
| `tools/phase9/e9_4_grid.py` | the grid: `manifest`, `status`, `verify`, `score` |
| `tools/phase9/e9_launch.py` | starts one runner process per model for a manifest |
| `tools/phase9/e9_2_pilot.py` | the pilot scoring and sizing that produced `sizing.json` (kept so the seed count can be re-derived) |
| `tools/stats_v2.py` | the model-level statistics: the R5 reference distribution, BH within a family, BY across families, the two-way cluster bootstrap |
| `tools/path_hashes.py` | hashes 95 fixed environment configurations; with the reference file below it proves the environment is unchanged |
| `docs/env_v2/generated/v2_1/e9_2/sizing.json` | the pilot's result: the plug-in sigma_d and the seed count the grid uses (120) |
| `docs/env_v2/generated/v2_1/e8_5/` | the Phase 8 inputs that sizing read |
| `docs/env_v2/generated/v2_1/path_hashes_phase9_after.json` | the frozen path-hash reference |
| `tests/` | the environment, harness, freeze and grid tests (section 3) |

Files under `results_v2/` (the runs) are git-ignored.

### Why some paths and modules still say v2, phase 6 or phase 8

The finalised environment is the v2.1 one, and it lives under `envs/v2/`: v2.1 re-fitted every parameter inside the
v2 module tree rather than forking a new one, so the path name is the module's name, not an older version. The v1
generator is not on this branch at all. Three other names look like history and are not:

- **Superseded engines inside the frozen environment.** `envs/v2/mispricing.py` still implements the
  Franke-Westerhoff and Pruna mispricing engines, and four `params/burn_in_states_*.npz` files back them. The engine
  that runs is the fitted `ar1_fit`, named in `params/mispricing.json`; the others are inert switches kept as
  sensitivity arms. `params/fw_single_stock.REJECTED.json` is deliberate too: the loader refuses to start an engine
  from a rejected fit, and the file's presence is what that guard is tested against. All of this sits inside the 30
  files of the freeze manifest, so removing any of it would change `Env_Code_Hash` and break the equality with
  `main` that this branch exists to preserve.
- **`tools/phase8/`.** Three modules, imported directly by the grid tooling and its test: the metric names and seed
  counts the scorer uses, the runner's usage recorder, and the fake client the grid test runs against. They are
  dependencies of the grid, not leftover analysis.
- **`evaluation/params/phase6_criteria.json`, `tests/phase8_golden.json`, `tests/test_v2_1_phase_3.py`.** The
  criteria file is read by the audit modules the environment exposes and by `simulation/provenance.py`; the golden
  record is what `tools/phase8/e8_0_golden.py` compares the harness against, so that a harness edit cannot pass
  unnoticed; the test covers the volatility block.

The analysis tooling of Phases 0 to 9, the reports, the pre-registrations and the decision log are all absent, as is
every phase result file except the two sizing inputs the grid reads.

## 2. Setup

Python 3.11 or newer. The pilots ran on Python 3.13.13; `requirements.txt` pins the exact package versions they
ran on, and `pyproject.toml` carries the same packages as lower bounds.

```
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate on Linux or macOS
pip install -r requirements.txt   # exact versions
pip install -e .                  # optional; running from the repository root works without it
copy .env.example .env            # then fill in the keys (cp on Linux or macOS)
```

`.env` is read from the repository root. Only four keys are used (`.env.example` lists them). Never commit `.env`.

## 3. Verify before you spend money

Run these in order. Each one takes seconds to a minute and makes no paid call.

1. **Tests.** `python -m pytest -q`
   Expected: every test passes, with one or two skipped (the grid-manifest check skips until manifests exist; one
   environment test skips when an optional fixture is absent). At the cut this was 49 passed and 2 skipped; a
   checkout carrying the optional fixture gives 50 passed and 1 skipped. A failure, never a skip, is the signal.
   `tests/test_v2_freeze.py` proves the environment code hash equals the frozen manifest, which is the same file
   `main` carries; if it fails, the environment has been changed and every run's `Env_Code_Hash` will differ from
   the published one.

2. **Path hashes.** The 95 fixed configurations must reproduce the frozen reference bit for bit:
   ```
   python -m tools.path_hashes --out %TEMP%\ph.json
   python -m tools.path_hashes --compare docs/env_v2/generated/v2_1/path_hashes_phase9_after.json %TEMP%\ph.json
   ```
   Expected: `NON-ANALYST CHANGES: 0`. At the cut: 95 configurations, 0 changed.

3. **Clients.** `python -m tools.phase9.e9_runner check-clients`
   Builds every candidate client with the keys in `.env` and makes no call. Expected: exit 0, 18 candidates,
   0 errors. A configuration whose key is missing shows an error here rather than mid-grid.

4. **Optional, paid:** a smoke of one configuration, two runs of 200 calls each:
   `python -m tools.phase9.e9_runner smoke --configs "gemini-2.5-flash-lite|default"`

## 4. The grid as designed

The design is PREREG_PHASE_9.md section 4.1 on `main`, fixed by decisions P9-2, P9-3 and P9-5, and re-cut by
P9-8 and P9-10. In short:

- **Twelve configurations**, the roster members whose pilots completed. Nine first-party: Gemini 2.5 Flash
  (thinking off), Gemini 2.5 Flash-Lite, Gemini 2.5 Pro, Gemini 3.5 Flash, GPT-5, GPT-5 mini, GPT-5 nano,
  GPT-5.4 mini, GPT-5.5. Three through OpenRouter, each pinned to one upstream with fallbacks off: Claude Haiku 4.5
  (Anthropic), DeepSeek V4 Flash (Baidu), Qwen3 235B (GMICloud). Two roster members, Qwen3.7 Flash and GLM 4.7
  Flash, failed the registered smoke stopping rule and are named in each manifest as `configs_not_piloted`; they
  are not run.
- **Headline manifest**: 3 personas (ISFJ, INTJ, ENTJ) x 2 arms (static, memory) x 4 scenarios (flat, bull_trap,
  crash, sustained_bull) x 120 seeds (10001 to 10120), 200 simulated days per run. **2,880 runs per model.**
- **Slice manifest** (the D11 common-start slice, run after the headline per model): 3 personas x 3 arms (static,
  memory, swapped) plus the no-persona NONE trader, all at a common start, the same scenarios and seeds.
  **4,800 runs per model.**
- **Seeds**: 120 per cell, from `e9_2/sizing.json`. This is the plug-in sigma_d of 0.0958 (the largest 90 % upper
  limit over the piloted roster, DeepSeek V4 Flash, 36 df) put through Appendix A at alpha' = 0.05/36 for a minimum
  effect of 0.05 in band-MAS. Because it is a maximum over 12 of 14 configurations, 120 is a lower bound on what the
  full roster would have given.
- **Concurrency**: at most 15 in-flight calls per model (P9-1). The runner refuses more, across processes.

**The two decisions Phase 9 referred to the team have since been taken** (they were open at the cut; PHASE_9_REPORT.md
section 5 on `main` records why each was referred). The robustness table uses the **significant-only reading of the
sign criterion** as its headline, with the plain reading of the plan's sentence reported beside it: on the simulated
conditions the plain reading declares a conclusion level-dependent up to 0.241 of the time when the effect is
identical at every level, while the significant-only reading of the same sentence does so at most 0.008 of the time.
The roster is the **twelve piloted configurations**, rising to fourteen if Qwen3.7 Flash and GLM 4.7 Flash can be
piloted: criteria (ii) and (iii) turn on the number of models and not on the seeds, so the grid runs on the largest
roster the budget allows. Neither decision changes the manifests below, which are built from the twelve.

### Cost and wall-clock, from measured runs

Seconds per run are the Phase 9 pilot means (or the Phase 8 batch for Flash), from `e9_0/throughput.csv` on `main`.
Hours are at 15 concurrent calls per model; every model runs at once, so the roster's wall-clock is its slowest
member's. Dollars per run are provider-reported for the OpenRouter routes and read from a price table for Flash and
GPT-5 mini; **seven configurations have no measured price**, so the total below is a partial sum, not the bill.

| configuration | timed by | s per run | headline, hours | both manifests, hours | $ per run | $ both manifests |
|---|---|---|---|---|---|---|
| gemini-2.5-flash-lite | pilot, n = 384 | 293 | 15.6 | 41.7 | not measured | |
| gpt-5.4-mini | pilot, n = 384 | 322 | 17.2 | 45.8 | not measured | |
| gemini-2.5-flash (thinking off) | batch, n = 574 | 399 | 21.3 | 56.7 | 0.165 | 1,264 |
| claude-haiku-4.5 via OpenRouter | pilot, n = 192 | 635 | 33.9 | 90.3 | 0.553 | 4,245 |
| qwen3-235b via OpenRouter | pilot, n = 96 | 931 | 49.7 | 132.5 | 0.024 | 184 |
| gpt-5.5 | pilot, n = 384 | 990 | 52.8 | 140.8 | not measured | |
| gemini-3.5-flash | pilot, n = 384 | 1,095 | 58.4 | 155.7 | not measured | |
| deepseek-v4-flash via OpenRouter | pilot, n = 96 | 1,197 | 63.8 | 170.2 | 0.030 | 229 |
| gpt-5-mini | pilot, n = 384 | 2,135 | 113.8 | 303.6 | 0.329 | 2,530 |
| gpt-5 | pilot, n = 384 | 2,152 | 114.8 | 306.1 | not measured | |
| gemini-2.5-pro | pilot, n = 279 | 2,996 | 159.8 | 426.1 | not measured | |
| gpt-5-nano | pilot, n = 281 | 3,003 | 160.2 | 427.1 | not measured | |

Read this before running anything: the slowest two models need about 427 hours (18 days) for both manifests at the
cap, and the five priced configurations alone come to about $8,450. The whole grid is 92,160 runs of 200 calls.
This is the design as sized; it is not a recommendation to run it as is, and the open decisions above exist partly
because of these numbers.

## 5. Running

```
# 1. build the two manifests (reads e9_2/sizing.json; refuses if the sizing lacks a roster model without a registered reason)
python -m tools.phase9.e9_4_grid --stages manifest

# 2. run every model at once, one process per model, headline first, then the slice
python -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_headline.json --workers 15
python -m tools.phase9.e9_launch --manifest docs/env_v2/generated/v2_1/e9_4/manifest_slice.json --workers 15

# 3. watch, verify, score
python -m tools.phase9.e9_4_grid --stages status
python -m tools.phase9.e9_4_grid --stages verify
python -m tools.phase9.e9_4_grid --stages score
```

One model at a time, or to resume after an interruption (the runner skips completed runs):
```
python -m tools.phase9.e9_runner run --manifest docs/env_v2/generated/v2_1/e9_4/manifest_headline.json --config "gpt-5-mini|default" --workers 15
```

### What the runner guarantees

- **Fingerprint.** A manifest carries the hash of every prompt, the environment code hash and the harness sources.
  The runner refuses to run if the working tree no longer matches, so a design cannot move after its first batch.
- **Checkpointing.** Every completed run is recorded; re-running the same command resumes. Runs land under
  `results_v2/phase9/<subdir>/<setting>/<config_tag>/<model>/<scenario>/seed<seed>/<run_id>.{csv,meta.json,usage.json}`.
- **Contamination rule.** A run in which the provider caused a fallback (an error the agent's own three attempts
  did not absorb) is discarded whole, its files renamed with the status, and it is retried up to three attempts;
  after that it is counted as abandoned, never silently passed. The ledger `docs/env_v2/generated/v2_1/e9_4/ledger_<tag>_<model>.jsonl`
  records every attempt with its tokens, seconds, status and, on OpenRouter, the provider-reported cost and the
  generation ids that let the serving upstream be audited afterwards.
- **OpenRouter.** Each configuration names one upstream and is sent with `allow_fallbacks: false` (a wrong upstream
  fails with 404 instead of being re-routed) and `max_tokens` 8,192 (without a cap OpenRouter requests the model's
  full context window and some upstreams reject every call). First-party routes send neither.
- **Verify** checks every run on disk against its manifest: prompt hash, environment code hash, harness and placebo
  versions (`v2_1`), configuration tag, model, scenario, seed and start design. Missing runs are counted.
- **Score** writes `e9_4/per_run.csv`, one row per completed run with band-MAS and the other metrics, scored exactly
  as the pilots were (`evaluation.metrics_v2.score_run(scoring="v2_1")`); a run whose scoring fails is kept with
  its error in `score_error`.

### Known behaviour from the pilots

- The Anthropic upstream on OpenRouter returned HTTP 403 ("Request not allowed") on 36 of 76,808 pilot calls
  (0.047 %). Nearly all were absorbed by the agent's own retries; one run in 192 was contaminated and re-run.
  DeepSeek and Qwen3 235B saw none.
- The runner re-fingerprints every configuration at start; the first run of a large manifest lands some minutes
  after launch.
- Offline computation on the same machine starves the paid batches. Run analysis elsewhere while a grid is in
  flight.

## 6. Statistics on the scored runs

`tools/stats_v2.py` holds the registered machinery: `run_stats_v21(per_run, out_prefix)` computes the model-level
contrasts with the R5 reference distribution (a two-way random-effects variance referred to t with M minus 1
degrees of freedom), BH within the single confirmatory family, BY across families, and the two-way cluster
bootstrap beside it. The pre-registered robustness criteria for the parameter sweep and their measured operating
characteristics are in PHASE_9_REPORT.md sections 3.2b and 3.6 on `main`; they are not code on this branch.

## 7. Where to read more, on `main`

- `docs/env_v2/v2_1/PREREG_PHASE_9.md` (section 4.1, the grid) and `PREREG_PHASE_9_ADDENDUM.md` (items 6 to 11)
- `docs/env_v2/v2_1/PHASE_9_REPORT.md` (sections 3.1, 3.4, 5 and 7)
- `docs/env_v2/decisions/DECISION_LOG.md`, entries P9-1 to P9-10
- `docs/env_v2/spec/IO_CONTRACT.md` (the run log schema, including `Provider_Options` and the usage file)
