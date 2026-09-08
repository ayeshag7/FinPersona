# Prompt: execute Phase 6 of the v2.1 improvement plan (audits and checklist methodology — the gates, derived not stated)

## What this project is

**FinPersona-Bench** asks a question about LLM agents, not about markets: *when an LLM is given a persona with an
investment mandate — a risk band, a target allocation — does it keep to that mandate as market conditions change, or does
it drift?* An agent is run day by day through a multi-day market, sees a rendered snapshot (price, technicals, sentiment,
implied volatility, an analyst estimate, EPS and dividend fields), and allocates between cash and a risky asset. The
score is **mandate-conformity**, not profit: how far the agent's allocation sits outside the persona's band.

For that score to mean anything, the market must satisfy one hard requirement: **the agent must not be able to deduce the
hidden state from what it is shown.** The generator carries a hidden fundamental value `V` and a mispricing `x`, with
price `P = V·e^x`. If `x` can be reconstructed from the visible fields, a model that appears to "follow its mandate well"
may simply be reading the answer key.

**Phase 6 is the phase that owns the yardsticks.** Phases 1–5 rebuilt the generator so that every parameter is fitted or
tested on data. You do the same for the *criteria*: every checklist threshold gets an empirical reference distribution from
real 200-day windows, every leakage gate is derived from a null and a bound rather than chosen, every audit statistic gets a
known-answer test, and the seed counts come from a power analysis rather than habit. At the end you compute the plan's
go/no-go checkpoint (16A) on the frozen generator — the first time the whole programme is asked "is there a benchmark
here?" — and stop for the team.

**The governing rule of the whole programme: every generator parameter is fitted or tested on data, never stipulated.**
In your phase that reads: **no criterion is stated; every criterion is FIT from E6.1 and written down before the runs, and
none is moved after.** A statistic marked "(to verify)" may not appear in a parameter file, a test tolerance, or a slide.

---

## The document landscape

**The single working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`.** Its shape:

| Section | What it is |
|---|---|
| 0 | What was verified before the plan was written |
| **1** | **The protocol every phase follows** — pre-register, fit or test everything, report failures as failures; the power-analysis rules |
| 2 | Weakness-to-phase map (which of the 74 review findings each phase closes) |
| 3 | Data sources, their substitutes and their biases |
| 4–14 | **Phases 0–10**, one section each. 0 verification/freeze · 1 value and price structure · 2 mispricing engine · 3 volatility · 4 events, schedule and controls · 5 observables · **6 audits and checklist methodology (yours, Section 10)** · 7 targets, action and metrics · 8 harness and statistics · 9 LLM sensitivity · 10 documentation |
| 15 | Cross-phase compute, cost and effort |
| **16 / 16A** | **Order, dependencies, and the go/no-go checkpoint — written in advance, not to be moved. 16A is computed at the end of your phase.** |
| 17 | Decisions only the team can make |
| **A / B / C** | **Power-analysis formulas (yours: E6.3) · the analytic level-free bound for x (yours: E6.6) · numbers to be recomputed** |

Around it:

- `V2_1_ALTERNATIVES_REGISTER.md` — for each contested design choice, the alternatives and **the experiment that would
  decide between them**. **Section 14, "Checklist criteria, and the seed/horizon policy", is yours** (the plan calls it
  REG-14): A the v2 numeric thresholds, B KS-equivalence (bootstrap 95 % upper limit of the two-sample KS distance below
  0.10), C the P10–P90 band with a share criterion; T = 200 as the criterion, longer horizons reported separately.
  REG-15 (data and survivorship) applies to every reference distribution you build. REG-11 (θ) is Phase 7's but 16A is
  computed "at the co-primary θ values" — see the decisions section.
- `spec/E1_V2_GENERATOR_SPEC.md` (v2.1 as built; every section rewritten by its phase), `spec/IO_CONTRACT.md`, and
  **`spec/CALIBRATION_REPORT.md` — which the plan says you rewrite as the E6 appendix.**
- `reviews/V2_WEAKNESSES.md` — the 74 findings. Yours: **5, 7 (the tuned-parameter ledger), 30, 31, 32, 37, 40, 61, 63,
  64, 67**.
- `decisions/DECISION_LOG.md` — **the P5-* entries are the freshest precedent.** Read P5-9 (the first per-field-group
  attribution), P5-12 (a tool regression caught before a number was read), **P5-16 (a pre-registered null found to be
  mis-specified after the fact — the most instructive entry for a phase that derives nulls)**, P5-18 (a CI fixture that
  had silently diverged from the audit's own convention) and P5-19 (the final state).
- `generated/v2_1/` — every machine-written result. Yours will be `e6_*`.
- `tests/known_defects.py` — the registry. **Its only two entries are yours** (below).

---

## Context for this phase: what the evidence says, measured on the deployed state

Phase 5 closed by measuring the Phase-5 hand-over with the audits you now own. **These are measured values, not estimates**
(`e5_after/`, `e5_7a/final/`, `e5_7c/final/`, `e5_l5/`; every one measured after `observables.json` settled):

**1. The two gates in the known-defect registry now pass on the 1,600-path panel — under the v2 thresholds you are about
to replace.**

| gate (level-free control, 1,600 paths × T = 200) | Phase 4 post-D14 | **Phase 5** | v2 rule |
|---|---|---|---|
| L2b phase-clock selectivity (full − price-only macro-class accuracy) | +10.4 pp **FAIL** | **+1.8 pp** (67.6 % − 65.8 %; day-only 50.8 %; majority 41.4 %) **PASS** | ≤ 10 pp — a margin *chosen*, and frozen after the result was known (weakness 32) |
| L2 absolute | FAIL | calm best R²(x) −0.61, event 0.45, MAPE(V) 0.128; max selectivity R²(x) +0.028; MAPE(V) gain 1.7 %; shuffled-V R² 0.001 → **PASS** | absolute thresholds "inconsistent with the design" (weakness 32) |

**Read this the right way.** The pass is under thresholds the reviews rejected as arbitrary. Your job is not to celebrate
it but to replace both rules with derived ones (E6.6, E6.7) and report the Phase-5 state under the derived rules — which
may pass by more, or fail. The CI-sized versions (`tests/test_leakage_ci.py`, 8 seeds) **still strict-xfail** on this state;
the registry entries stay until you derive the gates and re-express those tests at a power-analysed n.

**2. The fields now carry almost nothing about x that price does not.** Final per-field-group ablation
(`e5_7a/final/ablation.md`; GBT, 5-fold GroupKFold by path, paired 500-resample cluster bootstrap):

| | v2 baseline (Phase-4 hand-over) | **Phase 5** |
|---|---|---|
| level-free base R²(x), all rows | +0.414 | +0.406 [0.391, 0.421] |
| **full feature set** | **+0.805** | **+0.432 [0.410, 0.453]** |
| all eighteen fields' add-one, summed | ≈ +0.39 | **+0.026** |
| largest group, all rows | VOL +0.220 | VAL +0.009 [+0.001, +0.017] |
| largest group, calm-trained | VOL +0.052 | **VAL +0.051 [+0.035, +0.068]** |
| macro clock, full − base | +10.7 pp | +3.0 pp (VOL +1.5, VAL +0.4) |

The calm-trained VAL figure is the one open thread: the wandering multiple (a FIT log-AR(1) at ρ_d 0.9966) is itself a
slow signal a calm-trained reader uses. It is inside the PROVISIONAL bound (0.20) by a factor of four; whether it is inside
a *derived* margin is your E6.6.

**3. The calm-trained level-free channel** (`e5_after/calm_trained_phase5.md`, the e3_9 estimator, 500 resamples):

| state | level-free R²(x) | full-field R²(x) |
|---|---|---|
| Phase 3 | +0.3493 [0.3218, 0.3743] | +0.5501 |
| Phase 4 post-D14 | +0.3213 [0.2935, 0.3478] | +0.4905 |
| **Phase 5** | **+0.2912 [0.2637, 0.3179]** | **+0.3950 [0.3609, 0.4284]** |

The level-free figure moved with overlapping intervals; the full-field figure moved with non-overlapping ones. What is left
in the level-free number is the process stack's (E3.8: 0.203) plus ≈ 0.03 of sentiment feedback (P5-15) — **it is the
engine's, and your E6.6 bound (Appendix B: 0.40 at steady state, 0.14–0.26 within 200 days under the v2 parameters) is the
instrument that says whether 0.29 is what a price-only reader is *entitled* to.** G4's second clause is exactly that test.

**4. L1 on the final state** (`e5_after/audit_after_levelfree.md`): price itself is the best inverter (median APE 0.063,
within-5 % 0.426); `k·P/PE`, `k·P·DY` and `k·F` sit at median APE 0.62–0.70 with within-5 % shares of 0.03–0.04. The
Phase-5 L1-extended run (`e5_7b/`) found the same on all 21 panels. **The 1 % floor is still hard-coded** (weakness 32);
E6.5 derives it from the x process.

**5. Onset detection** (`e5_7c/final/onset.json`; 200 crash + 200 bull-trap seeds, 500 circular shifts): PASS at all six
transitions **under the non-price rule** of `PREREG_PHASE_5_ADDENDUM.md` §1.3 — the technicals are price-derived and sit on
the reference side. That rule is the version to carry into **L2c** (E6.7); the registered five-score reference was too
narrow and fails on SMA/MACD at every state.

**6. A null that was wrong in location, not width.** Phase 5's absolute-admissibility clause compared a field group's
ΔR²_add with the 95th percentile of an across-path *column* permutation. The measured null was **negative** (ANALYST p95
−0.0057, SENT −0.0024, 20 draws): permuted columns cost the GBT out-of-sample fit, so no field — not even one carrying
nothing — could be "inside" it. The pre-registration's power check had simulated that null on a synthetic panel and put it
at 10⁻⁴. **Your E6.6 null is a different one (targets permuted across paths), but the lesson transfers whole: simulate every
null with the real estimator on the real panel at the real n, and read its location before you write the rule.**

**7. L5 and the discrimination table** (`e5_l5/discrimination.md`): oracle < L5 < trivial in every scenario with both gaps'
intervals above zero (G1's shape); the oracle→L5 gap widened 0.005–0.009 in flat, crash and bull-trap; sustained-bull
coverage 0.354 (0.044 pre-D14). **G3 is known to fail at the FIT persistence** — the plan says so (16A: medians 0 / 0–1 /
1 / 2 switches) and forbids the obvious fix. Expect D17.

**8. Three PROVISIONAL entries name you as owner** in `envs/v2/params/observables.json`'s `audit_bounds`:
`no_field_deterministic_R2 = 0.20` (amendment A8's reference value; `test_no_field_is_deterministic_in_x` reads it),
`onset_rule` (the measured circular-shift p95) and `l2b_margin_phase6_owned = 0.1`. Replace them with derived values under
a declared status term (the loader raises on an undeclared one), or move them to a Phase-6 gates file and point
`observables_params.AUDIT_BOUNDS` at it — either is a documented `envs/v2` change, allowed because the entry names you.

**9. Two smaller residues, reported not gated:** the generator renders "n/m" on 6.2 % of days against the panel's 8.5 %
(the P5–P95 truncation of the loss-size grid); `days_since_eps_announcement` keeps a 3.3 pp clock residual after quarter
randomisation, resolved as edge + split noise (P5-8). A checklist band for the first is yours if you want one.

---

## Read first, in this order

1. **Section 10 of the plan** — your phase, in full; then **16A** and **Appendices A and B**, which are your instruments.
2. **`PHASE_5_REPORT.md` section 0** (the state table), **section 4.3** (the final state — every number above with its file)
   and **section 2** (the six post-hoc readings and the tool defects — the addendum pattern you will need).
3. **`PREREG_PHASE_5_ADDENDUM.md` §1 and §6** — the onset reference-set correction (your L2c inherits it) and the negative
   null (why you simulate nulls on the real panel).
4. **`V2_1_ALTERNATIVES_REGISTER.md` Section 14** — your criterion contest, with the experiment already written.
5. **`evaluation/leakage_audit.py` and `evaluation/stylized_facts.py`** — what you are changing. **They are under the freeze
   manifest and every earlier phase was forbidden to touch them; you are the phase that may.** Every change is a switch
   with the current behaviour behind it, proved inert when off (Phase 5's `obs_mode="v2"` is the pattern: 50/50 random
   inputs bit-identical, and the 95-configuration path-hash fixture unchanged).
6. **`tools/phase5/`** — reuse before you write: `e5_7a_ablation.py` (per-field-group GBT with paired cluster bootstrap
   and across-path permutation nulls; `--reuse-base` shares BASE fits by feature-matrix hash), `e5_7c_onset.py` (the L2c
   candidate, both verdicts), `e5_panels.py` (the fast renderer, 1,600 paths in 172 s, verified bit-for-bit against
   `panel_from_env`), `e5_after_state.py` (panel → audit → calm-trained → checklist → hashes → freeze, each stage its own
   files), `e5_l5.py` (the n/m-aware oracle), `e5_discrimination.py`, `common.encode_nm` (the audit-side convention for an
   undefined P/E: cap + `reported_PE_nm` indicator — **every consumer of a panel must apply it**, P5-18),
   `e5_param_table.py` / `e5_arms_table.py` (report tables generated from files into marked blocks), `e5_cite_check.py`
   (P4-37's guard: every cited path exists).

---

## Decisions: what the team must take BEFORE you start, and what you must not pre-empt

- **D2 — the LLM roster and budget tier for the L3 probe.** E6.6's L3 is 200 probes × ≥ 5 models × 2 arms (normal,
  shuffled-V) ≈ 2,000 short calls ≈ **$12** at the plan's roster (Gemini 2.5 Flash, GPT-5 mini, Claude Sonnet 5, Haiku 4.5,
  Opus 5). **Put the roster and the $12 to the team with your pre-registration** (the plan proposes it "for approval with
  the phase's pre-registration"). Do not spend before it is approved; build the probe so it runs when it is.
- **D10 and D15 are still open**, and they change the state you audit: the yield's rendering (`dividend.field`) and the
  sentiment default (A deployed; B-half/B-full switchable). **Ask for both in your first message.** If they are undecided
  when the audits must run, audit the deployed defaults, say so in the report, and make the arm re-run cheap (the
  after-state chain is one command per state).
- **θ for 16A.** The checkpoint is "computed at the co-primary θ values", and θ's derivation (E7.1, REG-11) is Phase 7's.
  **Do not derive θ.** Compute 16A at the current θ = 0.05 and at the plan's re-scoring set {0.03, 0.05, 0.08, 0.12, 0.20},
  label the 0.05 row the checkpoint and the rest sensitivities, and state the order dependency in the report; if the team
  wants θ_info/θ_cost first, that is their call (D7), not yours.
- **D17 will be triggered by G3.** The plan records that the FIT persistence gives at most one oracle decision per 200-day
  run and that a shorter half-life is forbidden as tuning-to-pass. Your job is to *measure* G3 exactly as written and to
  lay out D17's admissible options with their consequences (a longer horizon reported as a factor; per-window scoring;
  restricting the paper's claim). Do not pick one.
- **Do not touch** D5 (event dynamics, unresolvable on its rule) or κ = 0 (blocked at 96.3 % rejection, P4-44).

---

## What Phase 5 hands you (do not redo this work)

- **Every observable is FIT, LIT-with-sensitivity or a stated DESIGN**, in `envs/v2/params/observables.json` with a loud
  loader (`envs/v2/observables_params.py`: raises on a missing entry, a null interval, a missing date or n, an undeclared
  status). Multiple B (wandering k), EPS/lags/dividends v21 (both dividend renderings carried), analyst C (price proxy,
  PROVISIONAL), sentiment A (returns only, PROVISIONAL), volume A (no |x| term). `obs_mode="v2"` retrieves v2 bit for bit.
- **The panel of the hand-over state**: `_panels/sep_phase5_after.pkl` (1,600 paths, 320,000 rows; git-ignored,
  regenerable in 3 minutes) and its audits under `e5_after/`; `path_hashes_phase5_after.json` is the current hash fixture
  (**`path_hashes_phase4_after.json` is stale** — it predates D14 and the centred depth draw, P5-2).
- **The freeze manifest** re-frozen (27 files); the whole test tree at 159 passed / 1 skipped / 4 strict xfails (the two
  registry entries and the two permanent v1 rows).
- **Tools** listed above, and the measured costs below.
- **The n/m convention**: an undefined P/E is NaN in the frame, the string `"n/m"` in the observation, and cap + indicator
  on the audit side. `tests/test_leakage_ci.py`'s fixture applies it; if you add a consumer, so must it.

---

## What to do now: Phase 6, Section 10 of the plan

Nine experiments and the checkpoint. In the plan's numbering:

- **E6.1 Empirical reference distributions.** Every non-overlapping 200-day window of every name in set A (≈ 3,000
  windows; sub-periods), every checklist statistic (LB p on r and |r|, ACF(1) of r and |r|, kurtosis, Hill, ARCH-LM, GJR γ,
  leverage correlation, volume–|r| Spearman, log-volume AC(1) and Shapiro p, skew, worst/best-day ratio, MDD, daily σ; the
  VIX/RV relations at index level and the five single-stock IV histories for the IV items). Publish P10/P50/P90 per
  statistic and sub-period. **Survivorship stated per item** (REG-15: tails, drawdowns and loss frequencies understated).
- **E6.2 Re-derived criteria.** For each item the old criterion and the new one, in REG-14's form (B: KS-equivalence with
  the bootstrap upper limit below D0 = 0.10; C: the P10–P90 band with a share criterion; "the KS test did not reject" is
  **not** a criterion). Results under both. **The tuned-parameter ledger** (weakness 7): every item whose threshold moved in
  v2 (9, 10, 11, 13, 17, 20; amendments A1, A2, A6, A7) with the parameters tuned against it (α, γ, β, σ̄, jump rate, panic
  multiplier, φ, hazard) and the pre-amendment results beside the amended ones.
- **E6.3 Power analysis per item** (Appendix A): the seed count from a 50-seed pilot's cross-seed variance; the table
  item → n → achieved power; the final checklist at the maximum required n (expect 200–500 seeds per scenario; T = 200 as
  the criterion, T ∈ {800, 2000} reported separately for the persistence and ACF-decay items, **never as the pass
  criterion for a T = 200 property**).
- **E6.4 Per-scenario and calm-only reporting** of items 2, 3, 5, 6, 12, with the regime-switching contribution quantified.
- **E6.5 The L1 extended candidate set** with the pass rule **derived from the noise floor implied by the x process**, not
  1 %. Phase 5's `e5_7b_l1ext.py` has the candidate list running; the floor derivation is the new part.
- **E6.6 The L2 gate.** The analytic bound (Appendix B) from the adopted (σ_V, s_x, h), checked against the surrogate at
  every point of Phase 1's sweep; the gate = selectivity of the non-price fields over the level-free control ≤ the 95th
  percentile of a **target-permutation** null plus the sampling half-width; MAPE(V) with intervals; the held-out-scenario
  split (weakness 67); **the L3 LLM probe** (200 probes stratified by scenario × phase × seed, ≥ 5 models, shuffled-V
  baseline, Wilson CIs) — after D2.
- **E6.7 The L2b gate**: the 10 pp margin replaced by the same null-derived margin; **L2c = the onset audit**, with the
  addendum §1.3 reference set; both with intervals.
- **E6.8 The never-implemented criteria** (weakness 64): item 12's lagged correlation = configured `b_pred` (within-phase
  partial correlation with a CI — note Phase 5 found the free sentiment source does *not* reproduce Tetlock's 8.1 bp, so
  the configured value is LIT and the criterion tests the generator's fidelity to it, not the world's); item 13's
  non-degeneracy across seeds.
- **E6.9 Known-answer tests** for every audit statistic (synthetic AR/GARCH series with known properties). **Write these
  first**: they are what tells you a criterion's size and power before you apply it (REG-14's experiment (i)).
- **16A** on the frozen generator: G1–G4 at ≥ 100 seeds per scenario with cluster-bootstrap intervals; the level-free
  observables oracle (current-day fields plus a 20-day history, trained on disjoint seeds), the best simple level-free rule
  from the pre-registered family, the trivial policies. Report every G under the criterion as written.

**E6.6 and E6.7 are the deliverables that matter most.** They are the gates the whole programme has been promising to
derive since Phase 0, and the registry cannot be emptied without them.

---

## Hard rules (from the plan; not optional)

1. **Pre-register before you run.** `PREREG_PHASE_6.md` exists before the first generator run, with every criterion in its
   final form, the null of every gate **simulated with the real estimator on the real panel at the intended n** and its
   location reported, and the seed count per item from E6.3's rule. If a criterion later proves wrong, that goes in an
   addendum with the disconfirmation stated as loudly as any confirmation, and results are reported under both.
2. **Criteria are FIT from E6.1 and none is moved after** (10.3). A failing item is reported as failing under both criteria
   with the reason.
3. **Every change to the audit machinery is a switch with the current behaviour behind it, proved inert when off.**
   `evaluation/` is under the freeze manifest.
4. **Report failures as failures, with evidence. Numbers carry their `n`.** Never substitute a dataset, a source or a
   result silently. **No subsampling in a published audit** (`test_no_subsampling_in_published_audit`).
5. **`datasets/` is git-ignored and must never be uploaded anywhere.** Ship derived statistics (the reference tables are
   derived statistics).
6. **Do not modify `envs/`, `agent/` or `simulation/` unless the task is explicitly about them.** `evaluation/` *is* yours;
   the `audit_bounds` entry of `observables.json` names you; nothing else in `envs/` does.
7. **Work stays on `main`. Do not create branches. Commit only when asked**, one-line message, no body, no trailers.

### Method rules Phases 4 and 5 learned the expensive way

8. **Pin the configuration a tool measures** (P4-19), and **measure after the parameter file settles** (P4-45): every
   number in your report comes from a state whose hash you recorded.
9. **Verify every file you cite exists** before the citation is written (P4-37). `tools/phase5/e5_cite_check.py` is the
   pattern; run it on your documents.
10. **Run the WHOLE test tree** (P4-38). Phase 5's run found a fixture that had silently diverged from the audit's own
    convention (P5-18) — the older tests are what break.
11. **Simulate every null on the real thing** (P5-16). A synthetic proxy put a null at 10⁻⁴ that measured −0.006 on the
    panel. Report the null's location and width before the rule that uses it is final.
12. **A tool's "done" check tests emptiness, not presence** (P5-12). A JSON with `"tables": {}` is not a result.
13. **Generate every report table from its file** into a marked block, and add the test that reads it back
    (`test_phase5_report_parameter_table_matches_observables_json` is the pattern). Phase 4's report went stale twice;
    Phase 5's never did.
14. **Make every long chain resumable and staged.** The Phase-5 after-state chain survived a laptop sleep of nine hours and
    an editor crash because each stage wrote its own files and the ablation resumed from stored fits. Anything over ten
    minutes runs in the background with `python -u`, writes as it goes, and blocks on a file, not a poll.

---

## Documentation: keep it current as you go, not at the end

- **`PHASE_6_REPORT.md` is written as results land**, under the protocol's six headings, with section 0 as the state table.
- **Every decision gets a DECISION_LOG entry (`P6-*`)** with the alternative rejected and the evidence file. Entries where
  the phase decides against itself are the valuable ones.
- **The criteria file** (the reference percentiles, their n, the derived gates and margins, the null percentiles) carries
  provenance and a loud loader like `observables.json`'s, and `test_checklist_criteria_from_reference` /
  `test_l2_gate_derived` read it back.
- **`CALIBRATION_REPORT.md` is rewritten as the E6 appendix**; the plan's Table 2 and the spec's audit sections are updated
  in the same pass; `PHASE_6_CHANGED_FILES.md` is verified against disk.
- **The known-defect registry** ends the phase either empty or with entries whose reason names a derived gate and the
  phase that must pass it — `test_known_defect_registry_matches_strict_xfails` enforces the pairing.

---

## Compute: where to run what

**The rule that governs all of them: go faster by running independent stages in parallel, never by cutting a
pre-registered sample size.** If compute forces a reduction, fix the reduced design *before* the run, state the achieved
count and its power cost, and mark the verdict undecided if the smaller sample cannot decide it.

### Measured costs from Phase 5 (the laptop: i5-1135G7, 4 physical / 8 logical cores, 15.7 GB)

| stage | measured |
|---|---|
| 1,600-path SEP panel with the fast renderer (verified bit-for-bit) | **172 s** |
| SEP level-free audit on it (`run_audit`, ridge + GBT + MLP) | ≈ 70–80 min |
| per-field-group ablation, 70 GBT fits at 3 workers × 2 threads | **6,881 s** (≈ 100 s per fit; the FULL-set fits 220–450 s) |
| one post-hoc arm with BASE fits reused by hash | ≈ 10 min |
| permutation nulls, 40 fits | ≈ 25 min |
| onset audit, 200 + 200 seeds, 500 circular shifts, 3 workers | **1,094 s** |
| checklist (SCL panel) | 1,013 s |
| calm-trained comparison on three stored panels | ≈ 25 min |
| L5 at 40 / 50 seeds + the discrimination table | ≈ 76 min + 1 min |
| the whole test tree in one go | **33 min** (+ 1 min for the Phase-5 file) |

The 2-thread rule for sklearn stands (`leakage_audit` caps native pools at 2; 8 threads is slower than 4). The win is
overlapping independent jobs. Two Windows traps: `ProcessPoolExecutor` cannot spawn from a heredoc (write a module file);
this harness's Bash chokes on long heredocs containing quotes — write scratch scripts to a file and run them by path. **The
laptop sleeps on battery**: a nine-hour pause cost Phase 5 nothing because every chain was resumable (rule 14), but plan
wall-clock as if it will happen.

### 1. The laptop — the reference environment

**Every reported surrogate, audit or L5 number comes from here** unless the box below has passed the reproduction check.
Your biggest single item — the audits at 200 seeds with all paths and the MLP — is the plan's 3–4 hours; the checklist at
500 seeds ≈ 20 minutes; the reference statistics are minutes.

### 2. Kaggle — the proven offload

**Read `docs/COMPUTE_KAGGLE_GUIDE.md` first.** CLI 2.2.4, account `ayeshaiq`, five concurrent 4-vCPU / 30 GB sessions; the
cross-machine reference row proven to 6.4 × 10⁻¹⁶. **Send there:** E6.1's window statistics (3,000 windows × every
statistic, embarrassingly parallel), the per-window GJR fits, the known-answer panels of E6.9, the 50-seed pilots of E6.3.
**Not there** (unless the box passes the check below): anything whose number you will report from a scikit-learn fit.
`datasets/` never leaves the laptop; the derived tables do.

### 3. The lab GPU box — AVAILABLE since 7 September, with a proxy since 8 September

**Read `docs/COMPUTE_GPU_ACCESS.md`** (local file; it carries the whole thread and the tests). The short version:

- `ssh -i ~/.ssh/gpu_access_id_ed25519 -p 24761 root@115.236.153.177` (DDNS `109130cy78xp1.vicp.fun`), host
  `zhangf-6dffcfb96-nvf7l`: **128 cores**, 2 × RTX 4090 (idle; nothing here has a GPU path), **cgroup memory limit 32 GiB**
  (`free` says 1 TB and lies), `/nfs1` shared with the 1-GPU box (66 TB free).
- **Our environment is built and verified**: `/nfs1/ayesha/venv/bin/python` = Python 3.13.15 with numpy 2.4.6 / pandas
  3.0.3 / scipy 1.18.0 / scikit-learn 1.9.0 (the laptop's pins), joblib, threadpoolctl, pytest; `tmux` installed. The
  system Python 3.8 has no numpy — do not use it.
- **Fan's messages, in order** (7–8 September):
  > "Ok please try it again. 1gpu and 2gpu share the same nfs. You can find your previous code in nfs."
  > (Ayesha reported the key accepted, the environment rebuilt on /nfs1, and that from inside the container huggingface.co
  > resolves to Facebook/Meta addresses — DNS intercepted — with github.com and hf-mirror.com timing out while
  > modelscope.cn and mirrors.aliyun.com work; asked for an http/https proxy or the lab's egress route.)
  > "Because websites like Hugging Face and Google are blocked in China … we need to use a VPN to access them … the VPN plan
  > I currently have probably won't be sufficient, so I may need to pay extra to increase the data allowance." … "I bought it
  > for you. I'll set it up." … "One annoying thing about GPUs at Chinese universities is that the machines often get reset,
  > so I have to spend time setting up access between the internal and external networks so that you guys can log in …
  > Luckily, it's working again now."
  > **8 Sep, 3:57 PM:** "There is a Mihomo/Clash proxy running inside the container. Please set:
  > `export http_proxy=http://127.0.0.1:7890/` `export https_proxy=http://127.0.0.1:7890/` `export HTTP_PROXY="$http_proxy"`
  > `export HTTPS_PROXY="$https_proxy"` `export NO_PROXY=localhost,127.0.0.1` — Alternatively, for SOCKS5 with proxy-side DNS
  > resolution: `export ALL_PROXY=socks5h://127.0.0.1:7891` `export all_proxy="$ALL_PROXY"`"
- **Tested from the laptop on 8 September after that message:** the container was not reset (up 32 days; our venv intact);
  `mihomo` listens on 7890/7891; **through the proxy github.com, huggingface.co, www.kaggle.com and pypi.org all answer 200**
  and a GitHub release asset downloads at **2.77 MB/s**; without the proxy github.com still times out. **The tunnel from the
  laptop into the box is unchanged: ≈ 3 KB/s upstream and it resets bulk transfers** — a 74 MB panel cannot be pushed, and on
  8 September even a 1.5 MB code tarball in verified 64 KB chunks with retries did not get through (2 of 24 chunks arrived in two hours; the rest
  hung or reset), so the reproduction check below has **not** been run yet: the code is not on the box.
- **Therefore the data path is: the box pulls.** Publish code and panels where it can fetch them through the proxy — the
  private Kaggle dataset route is the one already proven from the laptop side (`python -m kaggle datasets version`), and on
  the box `pip install kaggle` in the venv with `KAGGLE_USERNAME`/`KAGGLE_KEY` in the environment of the *one pulling
  process only* (never on disk; root — Fan — can read a process environment while it runs; **ask the user before each use of
  the token there**). Export the proxy variables in every shell that fetches.
- **Before any fitted number from it is reported: reproduce a stored laptop fit exactly.** Two reference rows exist:
  `tests/test_v2_1_phase_2.py::test_smm_reference_row` (the standard Kaggle met) and, for the audit's estimators, a BASE
  row of `e5_7a/final/ablation.json` (re-fit it with `tools/phase5/e5_7a_ablation.py --stages add --groups VAL` on
  `sep_phase5_after.pkl` and compare `fits["BASE|x|all"]["R2"]` to the stored value; the GBT is deterministic at
  `OMP_NUM_THREADS=2`, so agreement should be exact or at floating-point level). If both agree, **the box is a reference
  machine for every sklearn stage in this phase**, and 128 cores turn the 3–4-hour audits into minutes — the single largest
  win available to you; run under `tmux` at ≤ 24 workers (memory: each worker holds the prepared frame). If either
  disagrees, record the non-reproduction in the report and keep every fitted number on the laptop, as Phase 5 did.
- **Never upload `datasets/`.** Never store credentials on the box. Re-check `nproc` and the cgroup limit at the start of
  every session — the machines get reset.

---

## Inherited open items

- **The two registry entries** — `test_v2_L2_surrogate_thresholds` and `test_v2_L2b_phase_clock_selectivity` — are yours to
  derive gates for and to re-express at a power-analysed n; the v2.1 acceptance criterion is an empty registry.
- **The three PROVISIONAL `audit_bounds`** in `observables.json` (0.20; the onset rule; the 10 pp margin).
- **The calm-trained VAL +0.051** (the wandering multiple as a slow signal) and the level-free 0.29 that is the engine's:
  Appendix B decides whether either is a leak.
- **The negative column-permutation null** (P5-16): a centred or interval version is the repair if a column-permutation
  margin is ever wanted again; your E6.6 null is a target permutation and must be located before use.
- **Three registered Phase-4 criteria that were unmeetable** (E4.6's coverage threshold, E4.5's KS bound at n_rej ≈ 81 vs
  the ≈ 400 needed, REG-18's topped share) — REG-14's concordance table is where "structural vs mis-specified criterion"
  is answered item by item.
- **G3** will fail at the FIT persistence; **D17** follows; the half-life is not a knob.
- **D10, D15, analyst C-vs-B (Phase 9), `b_pred` LIT-only** — open, the team's.
- **The generator cannot produce a panel-median crash** (P4-41: a stipulated `D_V` plus Phase 3's frozen panic
  volatility) — your MDD and severity items (10, 20) will meet this; report it as the structural cause it is.

---

## My recommendation for how to begin, and why

1. **First message: D2 (the roster and the $12), D10 and D15 — then start E6.9 and E6.1 while you wait.** The known-answer
   tests and the reference distributions depend on no decision, and everything else depends on them.
2. **Locate every null before you write a rule.** Simulate the target-permutation null of E6.6/E6.7 with the real
   estimator on `sep_phase5_after.pkl` at the intended n, read its location, and write the margin from what you see.
   Phase 5 pre-registered a rule around a null it had simulated on a proxy, and the real one was on the other side of zero.
3. **Try the box's reproduction check on day one, in the background.** If the two reference rows agree, your whole audit
   budget changes; if not, you have lost an hour and know where you stand. Ask for the token before the pull.
4. **Do E6.5's floor derivation and E6.6's bound before the surrogates run** — they are analytic, and they are what makes
   the surrogate numbers interpretable rather than merely reported.
5. **Run the 200-seed audits once, on the settled state, after D10/D15 are answered** (rule 8). Phase 4 ran a 77-minute audit
   and then adopted a change that invalidated it.
6. **Compute 16A last, exactly as written, and do not soften G3.** The plan's authors knew it would fail and wrote D17 for
   it; the value of the checkpoint is in the measurement, not the verdict.
7. **Expect at least one pre-registered criterion to be undecidable.** Six phases in a row have had one; the addendum is
   part of the deliverable, not a failure of it.

---

## Deliverable of this request

`PREREG_PHASE_6.md` (before any generator run; criteria in final form, every null simulated on the real panel with its
location reported, the seed count per item), the code and results under `tools/phase6/` and
`docs/env_v2/generated/v2_1/e6_*/`, the criteria/gates parameter file with provenance and a loud loader, the tests of
Section 10.4 (`test_checklist_criteria_from_reference`, `test_footer_counts`, `test_audit_known_answers`,
`test_no_subsampling_in_published_audit`, `test_l2_gate_derived`) plus a report-table consistency test, the tuned-parameter
ledger, the reference tables with P10/P50/P90 per statistic and sub-period, the checklist at the final n under both
criteria, the leakage tables with percentiles and intervals, the L3 results (after D2), the 16A table with G1–G4 under the
criterion as written and D17's options laid out if any fails, the known-defect registry emptied or re-expressed, a
refreshed freeze manifest and path hashes, `CALIBRATION_REPORT.md` rewritten as the E6 appendix, DECISION_LOG entries
`P6-*`, `PHASE_6_CHANGED_FILES.md`, and **`PHASE_6_REPORT.md`**.

Then stop for review — the team takes 16A and D17 before Phase 7 begins.
