# Prompt: execute Phase 2 of the v2.1 improvement plan (the mispricing engine and its persistence)

## What this project is

**FinPersona-Bench** asks a question about LLM agents, not about markets: *when an LLM is given a persona with an
investment mandate — a risk band, a target allocation — does it keep to that mandate as market conditions change, or does
it drift?* An agent is run day by day through a multi-day market, sees a rendered snapshot (price, technicals, sentiment,
implied volatility, an analyst estimate, EPS and dividend fields), and allocates between cash and a risky asset. The
score is **mandate-conformity**, not profit: how far the agent's allocation sits outside the persona's band.

For that score to mean anything, the market the agent trades in must satisfy one hard requirement: **the agent must not
be able to deduce the hidden state from what it is shown.** The generator carries a hidden fundamental value `V` and a
mispricing `x`, with price `P = V·e^x`. If `x` can be reconstructed from the visible fields, then a model that appears to
"follow its mandate well" may simply be reading the answer key, and the benchmark measures information leakage rather
than persona adherence. This is why so much of the programme is spent on leakage audits and on making every generator
parameter defensible.

The synthetic environment was built (v1 → v2), then **three independent reviews found v2 not robust**: parameters were
stipulated rather than fitted, several claims were not supported by the evidence cited, and the leakage controls had a
hole — the start price was fixed at V₁ = P₁ = 100, which made the price level itself an answer key. 74 weaknesses were
catalogued. The response is the **v2.1 improvement programme**: ten phases, each of which re-derives one block of the
environment from data under a pre-registered protocol.

**The governing rule of the whole programme: every generator parameter is fitted or tested on data, never stipulated.**
A statistic marked "(to verify)" may not appear in a parameter file, a test tolerance, or a slide.

## The document landscape

**The single working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`** (`.docx`/`.pdf` beside it are the same
content; keep them in sync if you ever edit — you should not need to). Its shape:

| Section | What it is |
|---|---|
| 0 | What was verified before the plan was written |
| **1** | **The protocol every phase follows** — pre-register, fit or test everything, report failures as failures |
| 2 | Weakness-to-phase map (which of the 74 review findings each phase closes) |
| 3 | Data sources, their substitutes and their biases |
| 4–14 | **Phases 0–10**, one section each. Phase 0 verification/freeze · **1 value and price structure** · **2 mispricing engine (yours, Section 6)** · 3 volatility · 4 events and schedule · 5 observables · 6 audits and checklist methodology · 7 targets, action and metrics · 8 harness and statistics · 9 LLM sensitivity · 10 documentation |
| 15 | Cross-phase compute, cost and effort |
| **16 / 16A** | **Order, dependencies, and the go/no-go checkpoint** (written in advance, not to be moved) |
| 17 | Decisions only the team can make |
| A / B / C | Power-analysis formulas · the analytic level-free bound for x · numbers to be recomputed |

Around it:

- `V2_1_ALTERNATIVES_REGISTER.md` — for each contested design choice, the alternatives and **the experiment that would
  decide between them**. REG-4 (engine) and REG-5 (persistence estimators) are yours.
- `docs/env_v2/README.md` — the layout of everything, the reading order, and the regeneration commands.
- `spec/E1_V2_GENERATOR_SPEC.md` and `spec/IO_CONTRACT.md` — v2 as actually built: blocks, parameters, the observation
  contract.
- `reviews/review_{A,B,C}_*.md` and `reviews/V2_WEAKNESSES.md` — the three reviews and the 74 findings that started this.
- `preregistration/` — v2's original thresholds and every amendment to them.
- `decisions/DECISIONS_13_1.md` and `decisions/DECISION_LOG.md` — the signed decisions and the running log; **Phase
  entries P0-*, P1-* are the precedent for how yours should read.**
- `v1_baseline/`, `status/`, `slides/` — the frozen old environment, current status, and the deck the results feed.
- `generated/` — every machine-written result, `generated/v2_1/` being this programme's.

## Context for this phase

**Phase 0 (verification and freeze) is done and reviewed. E1.0 (the data panel) is downloaded. Phase 1 (value and price
structure) is done, committed as `d6e3b24`, and its report is written.** You are to execute **Phase 2**: decide what
generates the mispricing `x`, and how persistent it is.

This is the phase where the environment's central mechanism is put on trial. v2 uses a Franke–Westerhoff (FW)
fundamentalist/chartist engine whose parameters came from a published index set rather than from a fit to this panel;
Phase 1 produced direct evidence that its mispricing is **not** the AR(1) process that the standard estimators — and the
plan's own analytic bound — assume. E2.4 exists to decide whether that engine survives a fair comparison against an
honest AR(1)+GARCH and against a published FW variant. Its answer determines what "persistence" means in every later
phase, so it is worth getting right rather than getting quickly.

Do not work from anything in `docs/env_v2/v2_1/archive/`, and do not edit the plan or `V2_1_ALTERNATIVES_REGISTER.md`.

## Read first, in this order

1. `docs/env_v2/README.md` — layout, reading order, regeneration commands.
2. The plan: Section 1 (the protocol every phase follows), Section 3 (data and biases), **Section 6 (Phase 2, in full)**,
   Section 16 (order and dependencies), 16A (the go/no-go checkpoint — written in advance and not to be moved),
   Section 17 (team decisions), Appendices A–B.
3. `V2_1_ALTERNATIVES_REGISTER.md`: **REG-4** (engine alternatives), **REG-5** (persistence estimators — Phase 1 has
   already executed its recovery study; see below), REG-2 (value process), REG-15 (data/survivorship).
4. **What Phase 1 established — read all four, in this order:**
   - `docs/env_v2/v2_1/PHASE_1_REPORT.md` — the whole report. §4.2 (the three estimators and the recovery study) and
     §6.1 (the open σ_V decision) are the ones Phase 2 inherits directly; §4.6 and §6.6 carry a reproducibility warning
     you must act on.
   - `docs/env_v2/v2_1/PREREG_PHASE_1_ADDENDUM.md` — three pre-registered criteria proved undecidable or underpowered
     and were corrected in documented steps (§1–§5), and §6 records the post-review extensions. Read it as a worked
     example of what to do when a criterion of your own turns out to be untestable at its stated sample size.
   - `docs/env_v2/v2_1/PHASE_1_CHANGED_FILES.md` — every file Phase 1 wrote or changed, with what each is.
   - `docs/env_v2/decisions/DECISION_LOG.md`, Phase 1 section, entries **P1-1 … P1-15**.
5. Phase 0: `PHASE_0_REPORT.md`, `reviews/review_of_PHASE_0.md`, `generated/v2_1/findings_reproduction.md`,
   `tests/known_defects.py` (the registry now holds two entries, both owned by later phases — one of them is yours).
6. The data panel: `datasets/README.md` (three caveats), `docs/env_v2/v2_1/E1_0_DATA_REPORT.md` (§1.2–1.3 survivorship
   and ticker reuse, §9.3 the usable panel, §11 open questions), the per-folder READMEs, `datasets/_manifests/`.
7. The code: `envs/v2/*.py` (especially `mispricing.py`, `generator.py`, `value_params.py`), `envs/v2/params/*.json`
   (especially `value.json` — every Phase-1 parameter with its provenance), `envs/synthetic_market.py`,
   `evaluation/*.py`, `tools/phase1/` (Phase 1's tools — several are directly reusable, listed below), `tests/`,
   `tools/freeze_manifest.py` and `tests/v2_freeze_manifest.json`. `envs/v1/` is frozen and must not be modified.

## Decisions the team has taken

- **D1 (data): C, hybrid** — fit on the free panel, publish every fitted value with its survivor-vs-literature gap,
  keep the fitting code re-runnable on WRDS by a data-path change. WRDS access: `______` (not confirmed unless filled in).
- **D13 (start price): mechanism C** (`start_price_mode = "both"`: P₁ ≡ 100 internally plus a per-seed render scale on
  every price-denominated rendered field). Revised from the provisional B during Phase 1 after B failed E1.1's attacker
  and rule-100 tests; A vs C is still REG-1's Phase-9 LLM test. Applied and in force — see P1-13.
- **D16 (programme): full programme.** Phase 2 now, in its own session.
- **D3 (σ_V, h, s_x): answered by Phase 1's rules, application deferred to you.** Estimator C (SMM) was the only usable
  estimator: **σ_V = 0.01957 [0.01892, 0.02036], h = 4.82 d [4.17, 5.42], s_x = 0.129 [0.125, 0.135]**. `h_fit` and
  `s_x_fit` are already written to `value.json` as Phase-2 targets. **σ_V is recorded as `ADOPTED-NOT-YET-APPLIED`**
  with 0.006 still in force, because writing it changes every path and triggers the execution-order rule. The team's
  choice (PHASE_1_REPORT.md §6.1) is: `______` — **(a)** apply σ_V now and re-run E1.4/E1.5/E1.1 and the Phase-1
  after-state before starting, or **(b)** fold the change into E2.3's re-fit, where σ_V and the pull rate are jointly
  identified. If this blank is empty, assume **(b)** and say so in your report's §2.
- **D2 (LLM roster/budget) and D10 (dividends):** not taken; nothing in Phase 2 needs them.

If something you need is not decided here, do every part that does not depend on it, then stop and ask with the options
and the evidence laid out. Never fill a blank with your own preference.

## What Phase 1 hands you (do not redo this work)

- **The recovery study already answers E2.2's "which estimator" question.** All 32 cells (h ∈ {5, 10, 30, 60, 120, 150,
  250, 500} × σ_V ∈ {0.006, 0.012}; A and B at 200 replications, C at 50) are in
  `generated/v2_1/e1_2/recovery.md` with the per-cell caches in `e1_2/cache/`. Verdicts: **A** (variance ratios) is never
  usable — its point estimate degrades monotonically with h and its bootstrap interval covers the truth in 0–1 % of
  replications; **B** (log(P/V̂) AR(1)) returns ĥ ≈ 36–47 d whatever the truth, and the *same* on a panel with x ≡ 0, so
  it measures the EDGAR V̂ error rather than x; **C** (SMM) is usable for h ≤ 150 (median relative error 0.03–0.16) and
  unusable at h ≥ 250. `e1_2/recovery_diagnostics.json` has the supporting diagnostics.
- **A finding that bears directly on E2.4:** estimator A recovers h correctly on an *exact* random-walk + AR(1) panel
  (ĥ 30.4 and 147 for truths of 30 and 150) but not on the engine's own panels. The engine's mispricing is therefore not
  the AR(1) that A's mapping and the plan's Appendix-B Kalman bound assume. That is direct evidence for the comparison
  E2.4 exists to make, and it is why the σ_V question belongs inside the engine re-fit.
- **A caveat you must carry:** the recovery panels come from `tools/phase1/calm_sim.py`, which *is* estimator C's model,
  so the usability test favours C by construction, and C's J = 66.6 on set A says the model does not fit the real
  moments well. E2.3's proper SMM (block-bootstrap weight matrix, χ² acceptance, FW's bootstrap p) is the test that can
  actually reject it. Do not treat "C was adopted" as evidence that the calm engine is right.
- **Reusable tools** (`tools/phase1/`): `panel.py` (exclusion rule, analysis sets A = 417 / B = 155, loaders),
  `calm_sim.py` (vectorised calm simulator, equivalence-checked), `e1_2_recovery.py` (recovery machinery and the SMM
  fitter — E2.3 extends this), `e1_2_vr.py`, `e1_2_pv.py`, `e3_1_garch.py` (the GJR-GARCH-t fits E2.3 needs),
  `e1_3_sweep.py` (the sweep pattern E2.6 follows), `kalman_bound.py`, `before_state.py` (`FROZEN_CFG`, panel
  generation), `phase1_chain.py` (**resumable stage runner — use this, or copy it; it is what made a 20-hour chain
  survivable**), `phase1_numbers.py`, `merge_recovery_caches.py`.
- **Reference results** for E2.3's targets: `e1_2/vr_fit.json` (pooled variance-ratio curve with intervals),
  `e1_2/smm_data_moments.json` (the nine calm moments and 200 stock-bootstrap resamples, cached so the fit runs without
  the raw panel), `e3_1/summary.md` and `garch_fits.csv`.

## What to do now: Phase 2, Section 6 of the plan

1. **Pre-register before running anything** — `docs/env_v2/v2_1/PREREG_PHASE_2.md`: seeds, horizons, estimators, the
   exact statistic, the pass/fail or decision rule, the power analysis that sets each sample size, and what will be
   reported if a rule is not met. **Check each criterion is decidable at the sample size you state** — compute the
   statistic's spread under the null before you commit to the threshold. Phase 1 lost time to three criteria that could
   not be met by any result (`PREREG_PHASE_1_ADDENDUM.md` §1, §4); the fix is one simulation per criterion, in advance.
2. **E2.1** — reproduce FW's own model (their price equation, two Gaussian demand noises, no GARCH, no jumps, no drift)
   at the DCA-HPM set with `price_scale` ∈ {1, 100}, 200 runs × 7,000 steps, and compare the average chartist share and
   excess kurtosis with 0.23 / 7.8. The convention that reproduces them is confirmed; log it as a bug fix (LIT).
3. **E2.2** — the firm-level persistence estimate, using Phase 1's recovery verdicts rather than repeating them: report
   the cross-sectional median half-life with P25/P75 and per sub-period for each estimator, and apply REG-5's
   disagreement rule to the *current* estimator set. State plainly that only C survived usability and what that implies.
4. **E2.3** — the SMM done properly on the same panel: FW's nine moments plus the persistence-carrying moments,
   **block-bootstrap weight matrix stored to disk** (not the diagonal proxy Phase 1 used), the Phase-3 GJR-GARCH-t
   innovation from E3.1 and the E1.2 value process, common random numbers, differential evolution with ≥ 20 starts
   including chartist-active regions then Nelder–Mead polish, χ² acceptance at 5 % plus FW's bootstrap p, full-parameter
   J profiles at the optimum, three sub-periods, start-J and end-J recorded. **If the team chose (b), σ_V is a free
   parameter here and its fitted value — with its interval — is what gets written into `value.json`.**
5. **E2.4** — the engine decision (FW vs AR(1)+GARCH vs FW+ of Pruna et al. 2016) under the plan's asymmetric rule:
   acceptance at (a), held-out prediction at (b) by more than one bootstrap sd on the persistence-carrying moments,
   equivalence of the checklist and level-free leakage statistics at (c). Ties go to the simpler model. Whatever wins,
   every document must name the engine honestly.
6. **E2.5** — the half-life estimator lookup table (AR(1), true half-life ∈ {30, …, 600} d × T ∈ {200, 800, 2000,
   5000}, 200 seeds), reporting the analytic, the T = 200 "what the agent experiences" and the T = 5,000 values.
7. **E2.6** — the persistence sweep at matched stationary sd and, separately, matched innovation variance, with the
   oracle-switch counts at every level because they feed the 16A checkpoint.
8. **Tests, parameter file, freeze** — Section 6.4's tests; `params/mispricing.json` (and `value.json` if σ_V is
   applied) with label / source / date / interval / n on every entry; rewrite the freeze manifest and the path hashes on
   the state you hand over; update `tests/known_defects.py` (**the E[x] ≈ +0.012 entry is yours** — see below).
9. **`PHASE_2_REPORT.md`** under the same six headings Phase 1 used, then stop.

## Hard rules (from the plan; not optional)

**On assuming nothing.**

- **Every parameter is fitted or tested on data, never stipulated.** A statistic marked "(to verify)" may not appear in a
  parameter file, a test tolerance or a slide. If a value cannot be fitted from the free panel, label it DESIGN or CAL
  with the reason, and say what would settle it.
- **Verify inherited numbers rather than trusting them — including mine.** Phase 1 re-derived Phase 0's constants and
  found two of its own conclusions wrong. Before you build on any figure in the Phase-1 report, check it against the file
  it cites. If a number in a document and a number in `generated/` disagree, the generated file wins and the document is
  corrected.
- **Read sources at first hand.** A paper's number may be quoted beside a fitted value as an anchor, never used as a
  tolerance, and never cited from a secondary source. If you cannot read it at source, say so and do not quote it.
- **State the n and the interval on every number.** A point estimate with no n is not a result.

**On experimenting rather than deciding.**

- **When two approaches are defensible, run both and compare — do not choose by argument.** That is the register's whole
  purpose: REG-4 names three engines because the question is empirical. Phase 1 did this repeatedly and it paid every
  time: four start-price mechanisms run head to head (the provisional favourite failed and would otherwise have shipped);
  four jump placements; two burn-in options per engine across five engines; three estimators put through a recovery study
  that reversed the answer an 8-replication run had given. **Expect to spend most of Phase 2's compute on comparisons,
  not on a single fit.**
- **Include the incumbent as a candidate, and the simplest thing that could work.** E2.4's asymmetric rule exists so the
  fancy model must earn its place; ties go to the simpler model. Never run only the option you expect to win.
- **When a result surprises you, design the experiment that distinguishes the explanations.** Phase 1's estimator A
  looked broken until a diagnostic panel showed it recovers `h` correctly on an exact AR(1) — which relocated the problem
  from the estimator to the engine, and became direct evidence for your E2.4. A refuted hypothesis that is documented is
  a result; a hunch that is asserted is not.
- **Report both arms even when one wins decisively.** The losing configuration's numbers are what make the winner
  credible, and Phase 6 and the deck will need them.

**On documenting everything.**

- **Pre-register before running anything, and never move a threshold after seeing data.** If a criterion turns out to be
  wrong, say so, derive the corrected one in a *separate documented step before* the re-run, **disclose what you had
  already seen when you wrote the correction**, and report the result under both the old and the new rule.
  `PREREG_PHASE_1_ADDENDUM.md` is the template — including its disclosure paragraphs.
- **Every run writes a file.** A number that exists only in a terminal is not evidence. Results go to
  `docs/env_v2/generated/v2_1/e2_*/` as JSON (machine-readable, with the design block: seeds, n, counts) *and* Markdown
  (the table a human reads). The report cites the file; the file is regenerable by the command in its own docstring.
- **Every parameter entry carries label / source / date / interval / n / survivor-vs-literature gap** in the params
  JSON — the pattern `envs/v2/params/value.json` already follows.
- **Log every decision** in `DECISION_LOG.md` as P2-*, each with the alternative that was rejected and the evidence file
  that decided it — the P1-* entries are the precedent.
- **Record deviations, shortfalls and achieved counts, not intended ones.** If you run 8 replications where 50 were
  pre-registered, the report says 8, states what that costs in power, and marks the verdict undecided if it is.
- **Report failures as failures, with evidence, and withdraw your own conclusions when they turn out wrong.** Phase 1
  withdrew two mid-phase; that is the standard, not an embarrassment. Never substitute a dataset, a source or a result
  silently.
- **Write the report as you go, not at the end.** Each experiment's section gets written when its results land, while
  you still remember which caveats matter.

**On the environment and the repository.**

- **Execution order.** Anything that changes the environment after the state is frozen restarts from step 0: re-freeze,
  re-audit, new hashes. Budget for that *before* you change a generator parameter — it is why σ_V is still unapplied.
- **Reproducibility of any offloaded computation.** Phase 1 found that a model-fitting result computed on Kaggle did not
  reproduce locally (calm R² 0.41 vs 0.15 on identical code, seeds and panel) while a different audit on the same two
  machines reproduced to three decimals; thread count and early stopping were tested and ruled out, and the cause is
  still unknown (`PHASE_1_REPORT.md` §6.6, `generated/v2_1/e1_3/repro_point.md`, `determinism_check.md`). **Before using
  any number from a machine other than the one you report from, reproduce a known reference row on that machine, on the
  same kind of panel the result will use.** Simulation and optimisation offload safely; model fits do not.
- **Make every long run resumable and serial.** Cache per unit of work, skip what exists, and run one heavy job at a
  time — Phase 1 hung the laptop twice with two concurrent audits, and a crashed 3,000-job run resumed from cache
  instead of restarting. `tools/phase1/phase1_chain.py` is the working pattern.
- **Do not modify** `envs/v1/`, the plan, the alternatives register, or anything under `v2_1/archive/`. Do not commit
  unless asked; work stays on `main`; commit messages are one line with no trailer (`CLAUDE.md`).
- **`datasets/` is git-ignored** (third-party data, redistribution restricted) and re-downloadable via
  `tools/e1_0_data/`. **`docs/env_v2/generated/v2_1/_panels/*.pkl` is also git-ignored** — the intermediate panels are
  ~1.2 GB and regenerable with `python -m tools.phase1.before_state {sep,s11} --tag <tag>`.

## Compute: where to run what

Three machines are in play. **The rule that governs all of them: go faster by running independent stages in parallel,
never by cutting a pre-registered sample size.** If compute forces a reduction, fix the reduced design *before* the run,
state the achieved count and its power cost in the report, and mark the verdict undecided if the smaller sample cannot
decide it (Phase 1 did exactly this for estimator C — `PREREG_PHASE_1_ADDENDUM.md` §5 — and the later full-scale run
reversed the verdict, which is why the reduced run was labelled undecided rather than negative).

### 1. The laptop — the reference environment, and the memory constraint

8 cores, 15.7 GB RAM of which typically **~5 GB is free**. It is the machine every reported surrogate/audit number must
come from (see the reproducibility rule above), and it is easy to kill:

- **One heavy job at a time.** Two concurrent 320,000-row audits (~1.3 GB each and growing) hung the machine twice
  during Phase 1. Check free RAM before launching a second job; if it is under ~3 GB, queue instead.
- **Use 2–3 workers, not 8.** `--workers 3` with `OMP_NUM_THREADS=2` left the laptop usable and lost little throughput.
- **Queue rather than interleave.** `tools/phase1/phase1_chain.py` runs stages serially and skips any whose output
  exists; a small waiter script can start the next chain when a process exits. Both patterns are in `tools/phase1/`.
- Full-panel audits take ~1.5–3 h each here; a 40-point sweep ~1.4 h; L5 ~20 min.

### 2. Kaggle — the default offload, use it freely

Account `ayeshaiq`; CPU kernels, **4 vCPU / 30 GB / 12 h**, several concurrently (5 sessions), **no weekly CPU quota**
(the 30 h/week limit is GPU-only and irrelevant — the code is NumPy/SciPy/scikit-learn, no GPU path). Working setup:

- **Client**: `python -m kaggle` (pip package `kaggle`); token already at `~/.kaggle/access_token`.
- **Bundle**: private dataset `ayeshaiq/finpersona-phase1-bundle` — a staged copy of `envs/ evaluation/ agent/
  simulation/ tools/ tests/ pyproject.toml` plus the `docs/env_v2/generated/v2_1` inputs a kernel needs. Refresh with
  `python -m kaggle datasets version -p <stage> --dir-mode zip -m "…"`. Make a `finpersona-phase2-bundle` if you prefer.
  **`datasets/` must never be uploaded** — third-party data with redistribution restrictions. Where a fit needs panel
  statistics, cache the derived moments and ship those instead (`e1_2/smm_data_moments.json` is the precedent).
- **Kernel pattern**: `kernel.py` + `kernel-metadata.json` (`kernel_type: script`, `enable_internet: false`,
  `dataset_sources: [the bundle]`); the script copies the repo to `/tmp/repo` — locate it by walking `/kaggle/input`
  for `pyproject.toml`, since Kaggle may or may not extract the zip — runs the stage with `PYTHONPATH`, and copies
  outputs to `/kaggle/working/out`. Then `kernels push -p <dir>`, `kernels status`, `kernels output -p <dir>`.
- **What to send there**: **E2.3's SMM fits, E2.5's estimator table, E2.6's sweep cells, E2.1's FW reproduction** — all
  simulation and optimisation, which offload safely and are the phase's biggest costs. One kernel per independent slice
  (e.g. one per sub-period, one per persistence level) and merge the caches locally;
  `tools/phase1/merge_recovery_caches.py` shows the merge pattern.
- **What not to send there**: anything whose number you will report from a scikit-learn model fit (the leakage audits,
  L5, any surrogate R²) — unless you first reproduce a known reference row on Kaggle and it matches. See the
  reproducibility rule; this is not hypothetical, it cost Phase 1 a day of re-runs.
- Observed timings on Kaggle: full-panel audit ≈ 1.5 h, L5 ≈ 15 min, 40-point sweep ≈ 20 min, 300 SMM fits ≈ 7.7 h.

### 3. The lab GPU box — do not use until the team says access is confirmed

A shared lab machine reached over SSH. Status as of 31 Aug 2026: the original 48-CPU container is **gone** (its resources
were reallocated after a restart), and the replacement 2×4090 container at `109130cy78xp1.vicp.fun` port `24761`
(IP 115.236.153.177) is reachable but **rejects our key** — `Permission denied (publickey)` for both
`~/.ssh/gpu_access_id_ed25519` and the default key. The machine's owner has been asked to add
`ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN3yLTm/YZAkwXY7eGIBmvf0u6vyJFpyGWk/GH2mt7BA gpu-access`.

**Do not spend time probing it.** Use Kaggle. If the team tells you access is confirmed, then:

- Connect with `ssh -o ConnectTimeout=60 -i ~/.ssh/gpu_access_id_ed25519 -p 24761 root@<host>`; the connection is flaky,
  so retry a few times rather than concluding it is down. Work lives on the NFS at `/nfs1/zhangf/` (shared between the
  1-GPU and 2-GPU containers, survives reboots); internet access needs
  `export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890`.
- **Check `nproc` and the cgroup memory limit first** (`/sys/fs/cgroup/memory.max`; `free`/`nproc` can lie inside a
  container). It is a GPU box — our code gains nothing from the GPUs, so its only value is CPU cores; if it has few, it
  is not worth the setup.
- Run detached under `tmux` so an SSH drop cannot kill a job.
- **Before reporting any model-fitting number from it, pin the library versions to match the laptop** (Python 3.13,
  numpy 2.4.6, pandas 3.0.3, scipy 1.18.0, scikit-learn 1.9.0) **and reproduce a reference row** — e.g. an E1.3 grid
  point, whose local value is in `generated/v2_1/e1_3/repro_point.md`. If it does not match, that machine may run
  simulation and optimisation only.
- Never upload `datasets/`; it is a shared machine with other users' work on it.

## Inherited open items

- **The engine's residual E[x] ≈ +0.012 in flat markets is yours** (`tests/known_defects.py`, registered to Phase 2).
  Phase 1 removed the −4 %/day jump bias, and the confirmatory run showed the remainder is the calm engine's own: with
  jumps switched off entirely, E[x] = +0.0113 [+0.0027, +0.0199] over 1,000 flat paths
  (`generated/v2_1/e1_4/confirm_jumps_off.json`). The engine decision is the natural place to resolve it.
- **The Kalman bound (Appendix B)** assumes a random walk plus an AR(1) mispricing. Phase 1's E1.3 found the level-free
  surrogate does *not* exceed it at any of 40 grid points on the reference environment, so the bound is usable — but the
  recovery study found the engine's x is not an AR(1). If E2.4 changes the engine, re-check whether the bound's model
  still applies before Phase 6 builds a gate on it.
- **The L2b phase-clock gate** is registered to Phase 6, not to you (`known_defects.py`); leave it.

## My recommendation for how to begin, and why

**Start with (b) — do not re-run the Phase-1 cascade — and make E2.3 the first substantial run, not E2.1.**

1. **Take σ_V into E2.3 rather than applying it first.** Phase 1's own evidence is that the engine's mispricing is not
   the process any of the three estimators assumes, and σ_V and the pull rate are jointly identified by the same
   moments. Applying σ_V now would freeze one half of a joint estimate, cost a full re-run of E1.4/E1.5/E1.1 and the
   after-state, and then very likely require a second re-run once E2.3 moves it. Fit them together, once.
2. **Do E2.1 first anyway — it is an hour, and it gates how you read everything else.** It is a self-contained
   reproduction of FW's published numbers, and its outcome determines whether `price_scale` is 1 or 100 in every
   subsequent fit. Running it first costs almost nothing; running it late risks invalidating E2.3.
3. **Then E2.3, and treat it as the phase's centre of gravity.** Everything else (E2.2's reporting, E2.4's acceptance
   test, E2.6's sweep levels) consumes its output. Budget for it honestly: the plan estimates ~40 minutes per
   sub-period, but Phase 1's experience is that SMM fits are the single most expensive thing in this codebase — one
   3-parameter fit took 310 s locally, and the recovery study needed 7.7 hours on a 4-vCPU cloud kernel. Differential
   evolution with ≥ 20 starts over more parameters and a block-bootstrap weight matrix will be much larger than that.
   **Size it with a timing pilot before you launch the real fit**, and put it on Kaggle (it is optimisation, which
   offloads safely) rather than on the laptop.
4. **Copy Phase 1's chain discipline from the start.** `tools/phase1/phase1_chain.py` runs stages serially, skips any
   whose output exists, and survives a kill; per-cell caches meant a crashed 3,000-job run resumed instead of
   restarting. Phase 1 hung the laptop twice by running two 320,000-row audits at once — one heavy job at a time, and
   check free memory before launching a second.
5. **Write the pre-registration's power analysis as runnable code, not prose.** For each criterion, simulate the
   statistic's spread under the null at the sample size you intend, and keep the script. Three of Phase 1's criteria
   were undecidable as written; each cost a re-run that a five-minute simulation would have prevented.
6. **Be sceptical of E2.4 favouring FW.** The comparison is deliberately asymmetric and ties go to the simpler model.
   Phase 1's diagnostic — that the engine's x is not an AR(1) — cuts both ways: it is evidence the current engine has
   structure a simple model lacks, *and* a reason its parameters have never been identified on data. Let the
   pre-registered rule decide, and report the answer plainly whichever way it falls, including in the deck.

## Deliverable of this request

`PREREG_PHASE_2.md` (before any run), the code and results under `tools/phase2/` and
`docs/env_v2/generated/v2_1/e2_*/`, updated parameter files with provenance, the tests of Section 6.4, a refreshed
freeze manifest and path hashes, DECISION_LOG entries P2-*, and **`PHASE_2_REPORT.md`**. Then stop for review — do not
begin Phase 3.
