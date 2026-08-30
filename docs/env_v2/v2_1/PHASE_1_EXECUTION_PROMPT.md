# Prompt: execute Phase 1 of the v2.1 improvement plan (value and price structure)

## Context

FinPersona-Bench evaluates whether LLM trading agents keep to a persona's mandate over a multi-day synthetic market. The environment was rebuilt (v1 → v2), three independent reviews found v2 not robust, and a ten-phase improvement plan was written, verified and approved. **Phase 0 (verification and freeze) is done and reviewed; the shared data panel (step E1.0) is downloaded.** You are to execute **Phase 1**.

**The working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`** (same content as the `.docx`/`.pdf` beside it; changes are tagged `[changed: …]`, `[edit 27 Aug]`, `[resolved 29 Aug]`, `[edit 29 Aug]`). Do not work from anything in `docs/env_v2/v2_1/archive/`.

## Read first, in this order

1. `docs/env_v2/README.md` (layout, reading order, regeneration commands).
2. The plan: Section 1 (protocol every phase follows), Section 3 (data and biases), **Section 5 (Phase 1, in full)**, Section 16 (order and dependencies), 16A (go/no-go, written now and not moved), Section 17 (team decisions), Appendices A–B.
3. `docs/env_v2/v2_1/V2_1_ALTERNATIVES_REGISTER.md`: REG-1 (start price), REG-2 (value process), REG-3 (jumps), REG-5 (persistence estimators), REG-15 (data), REG-17 (burn-in).
4. What Phase 0 established: `docs/env_v2/v2_1/PHASE_0_REPORT.md`, `docs/env_v2/v2_1/reviews/review_of_PHASE_0.md` (accepted; read its "findings that change later phases" and "pointers"), `docs/env_v2/generated/v2_1/findings_reproduction.md`, `tests/known_defects.py`.
5. What the data panel is: `datasets/README.md` (entry point; read its three caveats), `docs/env_v2/v2_1/E1_0_DATA_REPORT.md` (§1.2–1.3 survivorship and ticker reuse, §9.3 the usable panel, §11 open questions), the per-folder `README.md` files and `datasets/_manifests/`.
6. The code: `envs/v2/*.py`, `envs/synthetic_market.py`, `envs/v2/params/*.json`, `evaluation/*.py`, `tools/*.py`, `tests/` (the freeze manifest `tests/v2_freeze_manifest.json` and `tools/freeze_manifest.py`), `tools/e1_0_data/`. `envs/v1/` is frozen and must not be modified.

## Decisions the team has taken

- D1 (data): **C, hybrid** — fit on the free panel now, publish every fitted value with its survivor-vs-literature gap, write the fitting code so that a CRSP/Compustat/OptionMetrics/IBES re-run is a data-path change; re-fit if WRDS access arrives. WRDS access: `______` (not confirmed unless filled in).
- D13 (start price): **provisional B** (P₁ ≡ 100, V₁ = 100·e^(−x₁)) for Phases 1–6; A/B/C decided by REG-1's LLM test in Phase 9.
- D16 (programme): **full programme**, Phase 1 first; Phases 2 and 3 follow in their own sessions.
- D2 (LLM roster/budget) and D10 (dividends): not yet taken; nothing in Phase 1 needs them.
- E1.0 panel location: `datasets/` at the repo root stands (the plan's `data/panel/` path is superseded; the plan is annotated).
- SEC User-Agent contact address: `______` (leave the project identifier as is if blank).

If something you need is not decided here, do every part that does not depend on it, then stop and ask with the options and the evidence laid out. Never fill a blank with your own preference.

## What to do now: Phase 1, Section 5 of the plan

Follow Section 5 exactly. In summary:

1. **Pre-register** `docs/env_v2/v2_1/PREREG_PHASE_1.md` before running anything: every experiment E1.1–E1.6 with its seeds, statistics, criteria and decision rules as written in the plan; the **actual** bootstrap and seed counts you will run (Phase 0's lesson: state the feasible number, not the ideal one); the **panel exclusion rule** for ticker reuse and truncated series (E1.0 report Q7: nothing was excluded; you set the rule here, from the manifests, before any statistic is computed) and the "large-cap analysis set"; and **one standard evaluation panel** (scenario mix, seeds, T) for every before/after comparison so that rows are like for like.
2. **E3.1 first**: the per-stock GJR-GARCH fits on the panel were not run in the data step; run them now (Section 16 puts them in the data step because E1.4 and Phase 2's SMM need them) and store the results under `docs/env_v2/generated/v2_1/` with intervals and the exclusion rule applied.
3. **E1.1** start-price mechanisms A/B/C behind one switch, the level-feature vs level-free attacker test at the pre-registered seed count, B set as the provisional default; report that the analyst field and EPS × k still reveal V₁ (Phase 5's channel).
4. **E1.2** the three-estimator decomposition (variance ratios; EDGAR-based V̂ with the median-unbiased AR(1); SMM with persistence-carrying moments) with the REG-5 simulation-recovery study deciding which estimators are usable; σ_V, s_x, h adopted by the pre-registered rules or referred to D3 with both consequences.
5. **E1.3** the σ_V × s_x sweep through the audits with the analytic Kalman bound (Appendix B; the engine's reference s_x is ≈ 0.175, resolved in Phase 0) tabulated beside the surrogate at every grid point.
6. **E1.4** where jumps belong (announcement-day vs other-day tails on the panel; variants a/b/c; the E[x] ≈ 0 equivalence rule).
7. **E1.5** burn-in by the stationarity test (REG-17).
8. **E1.6** the level-free leakage audits (randomised start, level-free price keys, no subsampling, 200 seeds, cluster-bootstrap intervals, APE percentiles), reported without gates.
9. Every fitted parameter enters `envs/v2/params/` with provenance (LIT / FIT / CAL / DESIGN, source, date, interval, survivor-vs-literature gap where REG-15 asks for one). Update the freeze manifest deliberately (the change is the phase's output, logged), re-run the checklist and audits on the state you hand over (execution-order rule), keep the test suite green with the known-defect registry current.
10. **`docs/env_v2/v2_1/PHASE_1_REPORT.md`** under the six protocol headings, DECISION_LOG entries, the decisions Phase 1 raises for the team (D3 if the estimators disagree; anything REG-15's rule triggers), and the list of every file you wrote or changed. Then **stop** and wait for review. Do not start Phase 2.

Known panel caveats to handle, not to discover again: Yahoo serves whichever company holds a ticker today (86 of 673 series flagged; 64 start after the constituent left the index); only 16 of the 342 names that left the index are genuinely recoverable, so crash-depth and tail statistics from this panel understate the full universe and must be reported next to the literature's full-universe values (REG-15); the FRED volatility files mirror CBOE and are not a second source; `04_shiller/datahub_*_crosscheck.csv` zero-fills its trailing months (use `shiller_monthly.csv` / `ie_data.xls`); EDGAR company-facts repeat a fact across 10-K, 10-K/A and later comparatives, so deduplicate on (concept, period end, first filing) before using EPS changes.

## Hard rules (from the plan; not optional)

1. **Do not assume anything.** Every parameter, threshold, range and design choice traces to a read source (URL, date, read-and-correct / read-and-wrong / not-retrievable) or to a stated experiment. "It was in the plan", "conventional", "reasonable" are not justifications.
2. **Do not make arbitrary suggestions.** Where evidence cannot settle a choice, present the alternatives with the discriminating experiment (the register's format) and stop.
3. **Research, experiment, test, then decide.** Pre-registration is written before results are seen and not moved afterwards; if a criterion turns out wrong, say so, derive the new one in a separate documented step, and report under both.
4. **Report failures as failures.** Every number with its n and an interval; comparisons like for like; every tuned parameter labelled CAL where it appears.
5. **Verify before you cite** the repository's own documents; Appendix C lists the stale numbers.
6. **Scale of evidence** from Appendix A's power rules. Generator runs are free; **no paid API call in Phase 1.**
7. **16A** is evaluated after Phase 6 exactly as written; G3 may not be passed by shortening the persistence below its fitted value.
8. **Git.** Stay on `main`, no branches. **Do not commit, amend, reset, stash or push under any circumstances unless the user asks in that message.** Leave changes in the working tree and list every file you wrote or changed. Do not modify `envs/v1/`, `docs/planning/`, `docs/env_v2/v2_1/archive/`, or the plan and register (annotations to the plan are the reviewer's job); do not re-download or alter `datasets/` (write derived tables to `docs/env_v2/generated/v2_1/`).
9. Temporary files in the scratchpad; deliverables under `docs/env_v2/v2_1/` (documents), `docs/env_v2/generated/v2_1/` (results), `tests/`, `envs/v2/params/`.
10. When blocked on something only the user can decide, do everything that does not depend on it first, then ask.

## Deliverable of this request

Phase 1 complete as above: `PREREG_PHASE_1.md`, the E3.1 fits, E1.1–E1.6 with their results and intervals under `generated/v2_1/`, parameter files with provenance, the re-run checklist and audits on the handed-over state, a green suite, `PHASE_1_REPORT.md`, and the list of changed files. Stop there.
