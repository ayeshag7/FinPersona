# Prompt: execute Phase 5 of the v2.1 improvement plan (observables — the fields the agent actually reads)

## What this project is

**FinPersona-Bench** asks a question about LLM agents, not about markets: *when an LLM is given a persona with an
investment mandate — a risk band, a target allocation — does it keep to that mandate as market conditions change, or does
it drift?* An agent is run day by day through a multi-day market, sees a rendered snapshot (price, technicals, sentiment,
implied volatility, an analyst estimate, EPS and dividend fields), and allocates between cash and a risky asset. The
score is **mandate-conformity**, not profit: how far the agent's allocation sits outside the persona's band.

For that score to mean anything, the market must satisfy one hard requirement: **the agent must not be able to deduce the
hidden state from what it is shown.** The generator carries a hidden fundamental value `V` and a mispricing `x`, with
price `P = V·e^x`. If `x` can be reconstructed from the visible fields, a model that appears to "follow its mandate well"
may simply be reading the answer key, and the benchmark measures information leakage rather than persona adherence.

**Phase 5 is the phase that owns the fields themselves.** Every earlier phase built the process behind the price; you
build what the agent is shown. That makes this the phase with the most direct grip on the leakage problem — and the
phases before you have narrowed down, empirically, exactly which channel is left.

**The governing rule of the whole programme: every generator parameter is fitted or tested on data, never stipulated.**
A statistic marked "(to verify)" may not appear in a parameter file, a test tolerance, or a slide.

---

## The document landscape

**The single working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`.** Its shape:

| Section | What it is |
|---|---|
| 0 | What was verified before the plan was written |
| **1** | **The protocol every phase follows** — pre-register, fit or test everything, report failures as failures |
| 2 | Weakness-to-phase map (which of the 74 review findings each phase closes) |
| 3 | Data sources, their substitutes and their biases |
| 4–14 | **Phases 0–10**, one section each. 0 verification/freeze · 1 value and price structure · 2 mispricing engine · 3 volatility · 4 events, schedule and controls · **5 observables (yours, Section 9)** · 6 audits and checklist methodology · 7 targets, action and metrics · 8 harness and statistics · 9 LLM sensitivity · 10 documentation |
| 15 | Cross-phase compute, cost and effort |
| **16 / 16A** | **Order, dependencies, and the go/no-go checkpoint** (written in advance, not to be moved) |
| 17 | Decisions only the team can make |
| A / B / C | Power-analysis formulas · the analytic level-free bound for x · numbers to be recomputed |

Around it:

- `V2_1_ALTERNATIVES_REGISTER.md` — for each contested design choice, the alternatives and **the experiment that would
  decide between them**. **Its whole Section 10, "Observables that currently read the hidden state", is yours**:
  10a the P/E multiple · 10b sentiment · 10c volume · 10d the analyst estimate. (The plan calls these REG-10a–d; the
  register numbers them as sections, so search the heading, not the label.) REG-15 (data and survivorship) applies to
  every fit you make.
- `spec/E1_V2_GENERATOR_SPEC.md` and `spec/IO_CONTRACT.md` — v2 as built. **Section 6 (observables) is the one you
  rewrite**; Sections 3 and 4 show the expected form after Phases 3 and 4 rewrote them.
- `reviews/V2_WEAKNESSES.md` — the 74 findings. Yours: **3, 20, 21, 22, 23, 24, 34, 45**.
- `decisions/DECISION_LOG.md` — **the P4-* entries are the freshest precedent** and the most instructive: they include
  four decisions the phase took against itself (P4-34, P4-42, P4-44) and four method defects the phase found in its own
  conduct (P4-19, P4-37, P4-38, P4-45).
- `generated/v2_1/` — every machine-written result. Yours will be `e5_*`.

---

## Context for this phase: what the evidence says the fields are doing

Phase 4 closed by measuring the thing Phase 5 exists to fix. **These are measured values on the deployed state, not
estimates**, and they are the reason this phase matters:

**1. The calm channel is the fields', and Phase 4 proved it is not the events'.** The brief given to Phase 4 asked
whether redesigning the event block would narrow the calm level-free channel. It did not (`e4_21/calm_trained_phase4.md`):

| calm-trained level-free R²(x) | value |
|---|---|
| Phase 3 hand-over | +0.3493 [0.3218, 0.3743] |
| Phase 4 hand-over | **+0.3213 [0.2935, 0.3478]** |

CIs overlap — no detected change. E3.8's decomposition attributes **0.203** of that to the process + GJR + jump stack,
which leaves **≈ 0.118 for the events and the sentiment feedback**, and Phase 4 showed the *event* half cannot be moved
by rescheduling. **The residue is the fields and the sentiment feedback, and that is your remit.**

**2. The non-price fields still read the macro phase, and the margin is nearly exhausted.** Post-D14
(`e4_21/audit_after_levelfree.pkl`):

| L2b macro-class | value |
|---|---|
| accuracy, full fields | 0.760160 |
| accuracy, price only | 0.656635 |
| accuracy, day only | 0.509229 |
| majority class | 0.414490 |
| **selectivity (full − price)** | **0.1035 against a 10 pp margin — FAIL** |

It has come down from +15.4 pp (Phase 2) to +10.4 pp, but **read how it came down before you plan anything.** Phase 4's
event redesign narrowed it 1.94 pp *without touching the field channel at all* — full-field accuracy was unchanged and
the whole narrowing was the price-only baseline **rising** (P4-34). Only adopting control definition A moved it the right
way (−2.25 pp on full-field accuracy, P4-45). **A narrowing that comes from the subtrahend is not progress**, and this
is the single easiest way for your phase to fool itself.

**3. Best full-field R²(x) by phase group, post-D14** — the surface you are trying to lower:

| group | best full-field R²(x) |
|---|---|
| all | +0.8046 [0.7934, 0.8147] |
| calm | +0.2326 [0.1719, 0.2879] |
| event | +0.8541 [0.8443, 0.8641] |
| resolution | +0.7442 [0.7155, 0.7693] |

**4. The eighteen fields you inherit** (`e4_21` `shown_fields`): `price`, `SMA20`, `SMA50`, `RSI14`, `MACD`,
`MACD_signal`, `trend_regime`, `trend_strength`, `volume`, `volume_ratio`, `news_sentiment`, `sentiment_MA5`,
`sentiment_change`, `implied_volatility`, `analyst_fair_value`, `reported_PE`, `dividend_yield`,
`days_since_eps_announcement`.

**5. Two of them are known channels before you start.** Phase 1 reported that **the analyst field and EPS × k still
reveal `V_1` under every start-price mechanism** — explicitly deferred to you. And Phase 3's IV rebuild left the
onset-detection question (REV-11b) as a Phase 5/6 audit: IV's change-point detectability must be compared against *the
same filter's* realised-variance forecast, so the premium's legitimate rise through returns is not scored as a leak.

**6. `days_since_eps_announcement` is half-fixed and the residue is yours.** Phase 4 measured that with v2's fixed
quarter grid a lookup predicts which third of the quarter a day falls in with accuracy **0.873** against a null of 0.363.
Randomising the grid per seed drops it to **0.396** — 93 % of the excess removed, **3.3 pp residual reported, not
explained away** (P4-29). E5.2 owns whatever is left.

---

## Read first, in this order

1. **Section 9 of the plan** — your phase, in full. Note that its literature subsection has already been through the
   "replace every recalled number with the value read at source" pass, and records which sources **could not be read**
   (Kothari 2001, Lintner 1956, Karpoff's 0.2–0.5 range). Those may not reappear as numbers.
2. **`PHASE_4_REPORT.md` section 0** — the reading guide. That report was written in four passes and later passes
   overturn earlier ones; section 0 tells you which numbers are current and which carry state markers.
3. **`PHASE_4_REPORT.md` sections 8, 9.11 and 9.12** — the three method-defect write-ups. They are the most useful thing
   Phase 4 produced for you, and section "The three method defects this phase found in itself" in section 0 summarises
   them in one place.
4. **`PREREG_PHASE_4.md` and its addendum, section 6** — the addendum's disclosure of a pre-registration departure is
   the template for how to handle it if the team authorises you to take a decision the plan reserves for them.
5. **`V2_1_ALTERNATIVES_REGISTER.md`, Section 10 (10a–10d)** — your four pre-registered design contests, with the alternatives and the deciding experiment already written for each.
6. **`envs/v2/observables.py`** — what you are rewriting. It is **under the freeze manifest**, so any change must be
   proved inert when switched off (Phase 4's `q_phase` switch shows the pattern: reproduce the committed function
   exactly on 50 of 50 random inputs at the off setting).

---

## Decisions: one the team must take BEFORE you start

**D10 — pay dividends into cash, or remove the dividend field.** The plan is explicit that this is taken **before**
Phase 5 begins, because E5.3 depends on it (`LOG §7`). **Put it to the team in your first message.** If it is
undecided when you need to proceed, the plan's instruction is to **carry both variants** — not to pick one.

**D15 — the sentiment default — is taken AFTER E5.5**, on your results. Do not pre-empt it.

Two further decisions are open from Phase 4 and touch your work only indirectly; do not try to settle them:

- **D5 (event dynamics)** is unresolvable on its registered rule — Phase 4 showed the ranking metric is not monotone in
  scriptedness and the coverage criterion is blocked by a depth floor outside the event block (P4-41, P4-42).
- **κ = 0** is blocked at 96.3 % rejection until the stipulated bull-trap criterion `x.max() >= 0.30` is re-expressed
  jointly (P4-44).

---

## What Phase 4 hands you (do not redo this work)

- **The event block is fitted and deployed.** `envs/v2/params/events.json`, loader `envs/v2/events_params.py`. Schedule
  ranges are FIT from the panel's fast-crash family and sampled by inverse CDF; the blow-off multiplier is calibrated
  (2.0764 → realised 1.3136 against the panel's 1.2895); the post-top leg is an exponential decay at half-life 40.
- **The sustained-bull control is definition A** (D14, P4-43). This closed weakness items **18 and 42** and, unexpectedly,
  raised sustained-bull coverage from **0.044 to 0.374** with runs-with-no-scoreable-step falling from 10 % to 0 %
  (P4-46). The known-defect registry now carries **only the two Phase-6 leakage gates**.
- **`crash_discount` is a live arm factor again** (`depth_mode="centred"`, P4-40).
- **A structural finding that is not yours to fix but constrains what you can claim**: the generator cannot produce a
  panel-median crash. Realised depth floors near −0.46 against the panel's −0.3693; it is not selection (rejection is
  0.000 at every setting) but `D_V` — a **stipulated** uniform labelled DESIGN — plus Phase 3's frozen panic volatility
  (P4-41).
- **Every generator change is a switch with v2 behind it**, proved by hash. `schedule_mode="v2"` reproduces v2 bit for
  bit.
- **Tools you should reuse rather than rewrite**: `tools/phase4/e4_17_sep_audit.py` (builds its own panel under its own
  name), `e4_18_calm_trained.py` (imports Phase 3's estimator unchanged so the comparison cannot drift),
  `e4_9_deployed.py` (re-measures a whole block on the deployed state), `e4_16_discrimination.py` (takes an explicit
  `--out`).

---

## What to do now: Phase 5, Section 9 of the plan

Six fits and one audit block. In the plan's numbering:

- **E5.1 Multiple** — FIT the trailing P/E cross-section and the quarterly AR(1) of log P/E. Three designs (fixed k per
  seed / log-AR(1) k_t / k tied to characteristics), decided by E5.7(a)'s per-field-group selectivity and the L1
  extended inversion share, at three widths. **This replaces `U(14, 22)`, one of the most-cited stipulations in the
  reviews.**
- **E5.2 EPS and lags** — FIT the seasonal-RW residual sd and the announcement-lag distribution; negative EPS handled as
  in the data (P/E → "n/m").
- **E5.3 Dividends** — FIT payout and stickiness, and dividend behaviour in crash episodes. **Blocked on D10.**
- **E5.4 Analyst estimate** — three options (LIT sd / drop the field / a lagged smoothed price proxy). The read anchor is
  an absolute target-price error **≈ 45 % of price at 12 months**; the v2 value **0.15 is below every read value**. The
  report must state plainly that no free data can fit this sd.
- **E5.5 Sentiment** — FIT the AR(1) and return loadings on the SF Fed index; three designs, differing in whether a slow
  valuation link is carried. **REV-2b is explicit that the valuation loading is not to be set to zero by fiat.**
- **E5.6 Volume** — FIT ρ_v, the |r| elasticity and the noise sd; the v2 `|x|` loading is unsupported by any read source
  and is to be recorded as dominated.
- **E5.7 Audits** — (a) level-free L2 with a **per-field-group ablation** (which group adds how much R² for x and for V,
  with cluster-bootstrap CIs); (b) the L1 extended candidate set on the new fields; (c) the **onset-detection audit**
  with a label-permutation null; (d) the earlier v2 gates reported for the record.

**E5.7(a) is the deliverable that matters most.** It is the first per-field-group attribution in the programme, and it is
what tells the team *which* field is carrying the residual ≈ 0.118. Write it early, run it on the current fields before
you change anything, and you will have a baseline that makes every later design choice measurable rather than arguable.

---

## Hard rules (from the plan; not optional)

1. **Pre-register before you run.** `PREREG_PHASE_5.md` exists before the first experiment, with the decision rule for
   every contest and the null simulated at the intended sample size. If a criterion later proves unmeetable, that goes
   in an addendum with the disconfirmation stated as loudly as any confirmation.
2. **Every constant ends the phase with a provenance label** — FIT where the panel/EDGAR/SF Fed deliver, LIT+sensitivity
   where they do not (the analyst sd), DESIGN only for the rendering of undefined values and the market-to-stock
   transfer of the sentiment coefficient. **No entry ships with a null interval.**
3. **Every change is a switch with the current behaviour behind it, proved inert when off.** `observables.py` is under
   the freeze manifest.
4. **Report failures as failures, with evidence. Numbers carry their `n`.** Never substitute a dataset, a source or a
   result silently.
5. **`datasets/` is git-ignored and must never be uploaded anywhere** — third-party data, several sources forbid
   redistribution. Ship derived statistics instead.
6. **Do not modify `envs/`, `evaluation/`, `agent/` or `simulation/` unless the task is explicitly about them.**
   `observables.py` *is* explicitly yours; the leakage audit machinery is not.
7. **Work stays on `main`. Do not create branches. Commit only when asked**, one-line message, no body, no trailers.

### Four method rules Phase 4 learned the expensive way

Each of these cost Phase 4 real rework. They are cheap to follow and they are why its numbers can be trusted now.

8. **A tool that measures the generator must PIN the configuration it measures** (P4-19). Three Phase-4 results were
   measured before the parameter file they described existed, and no test could catch it because deployed and recorded
   were consistent — the recorded values had just been measured elsewhere.
9. **Verify every file you cite exists, before the citation is written** (P4-37). A cited evidence file had never been
   written; its stdout-sourced numbers proved unreproducible. A ten-line script checks the whole report.
10. **Run the WHOLE test tree, not the suites you remember writing** (P4-38). Nine of twenty-two files had never been
    run; six tests were failing, four since the main pass. Your own suite tests your own changes — what breaks is the
    older tests encoding the behaviour you replaced.
11. **Measure AFTER the parameter file settles** (P4-45). Phase 4 ran a 77-minute audit and a 40-minute comparison and
    then adopted a change that invalidated both. Sequence adoptions first, measurement second.

---

## Documentation: keep it current as you go, not at the end

This is not administrative advice. Phase 4's report went stale **twice** on its own parameter table — it read
`control | INCUMBENT | C — D14 open` while definition A was deployed — and both times the cause was that regenerating it
was an *intention* rather than a *check*.

- **`PHASE_5_REPORT.md` is written as you go**, not assembled at the end. Phase 4's report needed a reading guide
  (section 0) because it was written in four passes and later passes overturn earlier ones. If you update it as results
  land, you will not need one.
- **Every result gets a DECISION_LOG entry (`P5-*`) with the alternative rejected and the evidence file that decided
  it.** Entries that record the phase deciding *against itself* are the most valuable ones in the log.
- **Anything superseded is corrected in place with the original recorded**, not deleted. Where a number describes an
  earlier state, put a **state marker** on it naming the section that supersedes it.
- **Regenerate the parameter table from `params/observables.json`, and add a test that asserts they match** — Phase 4's
  `test_phase4_report_parameter_table_matches_events_json` is the pattern, and it was verified by negative control
  (re-injecting the staleness makes it fail). Do the same for the status vocabulary: `events_params.load` raises on a
  status its own `_status_key` does not declare, because that vocabulary had already drifted on 2 of 10 entries with
  nothing checking it.
- **Keep `PHASE_5_CHANGED_FILES.md` current** and verify its file listing against disk before you call it done.
- **Update the plan's Table 2 and `spec/` section 6 in the same pass**, not later.

---

## Compute: where to run what

**The rule that governs all of them: go faster by running independent stages in parallel, never by cutting a
pre-registered sample size.** If compute forces a reduction, fix the reduced design *before* the run, state the achieved
count and its power cost, and mark the verdict undecided if the smaller sample cannot decide it.

### Scope and parallelise — measured guidance, not exhortation

Phase 4 has hard numbers on this and they are worth reading before you plan a run:

- **Independent jobs must overlap.** Phase 4 ran a 77-minute audit, then a 40-minute comparison, then an hour of L5 —
  serially, for no reason. Running the last two together took the remaining wall-clock from ~1h40m to ~50 minutes.
- **But do not oversubscribe.** `evaluation/leakage_audit.py` caps native thread pools at 2 and says why: these
  estimators "collapse under oversubscription when other sklearn jobs run concurrently (100× slowdowns observed)".
  Measured on this laptop, one GBT fit on 60 000 rows takes **10.4 s at 2 threads, 7.7 s at 4, and 8.4 s at 8** — so
  raising the cap buys ~1.3×, not 2×, and 8 threads is *worse* than 4. The win is in overlapping independent jobs at
  2 threads each, not in giving one job more threads.
- **Stage long test runs.** The full tree took **45:29** in one session against **16:32** run in three stages on the
  same machine. Staging also banks partial results — a laptop battery killed two long Phase-4 runs, and the staged ones
  lost nothing.
- **Scope the audits honestly.** `tests/test_leakage_ci.py` is already scoped small (`N_SEEDS_CI = 8`) and its two
  module-scoped fixtures are 874 s of its 901 s — all eleven assertions together cost ~18 s. There is nothing to save
  by trimming it; the cost is one fixed audit per generator version.
- **A foreground command in this harness times out at 10 minutes.** Run anything longer in the background and block on
  a condition (`until [ -f <output> ]; do sleep 30; done`) rather than polling.

Two Windows traps: `ProcessPoolExecutor` cannot spawn from a `python - <<EOF` heredoc (write a real module file), and a
buffered background run can look dead — use `python -u`.

### 1. The laptop — the reference environment

An i5-1135G7: **4 physical cores, 8 logical**, 15.7 GB RAM. **Every reported surrogate or audit number must come from
here.** Measured Phase-4 costs, as your budget guide: the SEP level-free audit at 1600 paths **≈ 71 min** (plus ~26 min
to build the panel) · the calm-trained surrogate on two stored panels **≈ 49 min** · L5 at 40/50 seeds **≈ 55 min** ·
the discrimination table **< 1 min** given the L5 csv · 800 generated 200-day paths ≈ 4 min · the full test tree
**≈ 45 min** in one go, **≈ 17 min** staged.

### 2. Kaggle — the default offload, and a proven one

**Read `docs/COMPUTE_KAGGLE_GUIDE.md` first.** It carries the working connection details, the three non-negotiable
rules, the bundle-refresh and kernel-push recipe, rough timings, and the reproducibility caveat learned the hard way.

The short version: client **Kaggle CLI 2.2.4**, account **`ayeshaiq`**. Version the existing bundle rather than building
a new one. The cross-machine guard is proven — Phase 3's reference row agreed to a worst relative difference of
**6.4 × 10⁻¹⁶**, and Phase 4 re-ran it at **0.0** under numpy 2.0.2 / scipy 1.16.3. Run it once on your first kernel
(ten minutes), then offload freely.

**What to send there**: EDGAR-scale retrieval and parsing, the P/E cross-section fits, the seasonal-RW residual fits,
any per-episode or per-stock loop, and the sentiment/volume regressions — all embarrassingly parallel.
**What NOT to send**: anything whose number you will report from a scikit-learn model fit — the leakage audits, L5, the
per-field-group ablation, any surrogate R². Those stay on the laptop by the reproducibility guard.

**`datasets/` must never be uploaded.** Cache the derived statistics and ship those.

### 3. The lab GPU box — DO NOT USE

**`docs/COMPUTE_GPU_ACCESS.md`** has the connection details, and they **do not currently work** — the 2×4090 container
is reachable but rejects our key. **Do not spend any time probing it, and do not plan any stage around it.** If and only
if the team tells you access is confirmed, read that file, then check `nproc` and the cgroup memory limit first, run
under `tmux`, pin library versions, and reproduce a reference row before reporting any model-fitting number from it.
Nothing in Phase 5 needs a GPU.

---

## Inherited open items

- **The two Phase-6 leakage gates are the only entries left in the known-defect registry** — `test_v2_L2_surrogate_thresholds`
  and `test_v2_L2b_phase_clock_selectivity`. Phase 6 derives the gates; **your fields are what move them.**
- **The residual ≈ 0.118 of calm-trained level-free R²(x)** attributable to fields and sentiment feedback. No phase
  before you could move it; every phase after you inherits whatever you leave.
- **The analyst field and EPS × k reveal `V_1`** (Phase 1's finding, deferred to you).
- **IV's onset detectability** must be audited against the same filter's RV forecast, not against nothing (REV-11b).
- **Three registered criteria are unmeetable and need re-registering** — E4.6's coverage threshold, E4.5's KS
  equivalence bound (**costed: needs n_rej ≈ 400 against the 81 achieved**), and REG-18's topped share. Phase 4 found
  they share no single root; do not assume yours are safe because they are new.
- **The 3.3 pp residual clock** in `days_since_eps_announcement` after quarter randomisation.

---

## My recommendation for how to begin, and why

1. **Put D10 to the team in your first message, then start E5.7(a) while you wait.** D10 blocks E5.3 and nothing else;
   the ablation baseline depends on no decision at all.
2. **Measure the per-field-group ablation on the CURRENT fields before you change one line.** It is the only way you
   will be able to say what your redesign did, and it converts every later argument into a measurement. Phase 4's
   hardest-won lesson is that the phase which changes the environment is the phase that must measure what the change
   did — and that measuring it *afterwards only* leaves you unable to attribute anything.
3. **Do E5.1 and E5.4 early: they are the two fields with the strongest prior evidence of leakage.** `reported_PE` is a
   deterministic function of `V` through a stipulated `U(14, 22)`, and the analyst field is `V` plus noise whose sd is
   set below every value in the literature. Between them they are the most likely home of the residual.
4. **Expect the analyst sd to be irreducibly LIT, and say so early.** The plan already concedes no free data can fit it.
   Do not spend the phase looking for a source that section 9.1 has already recorded as unreadable.
5. **Write the onset-detection audit before you need it.** It has a label-permutation null, and Phase 4 twice built a
   null that was degenerate by construction — once permuting seeds when every path shared the day axis, once refitting
   nothing. Simulate your null at the intended n, as runnable code, before you commit to a threshold.
6. **Re-run the level-free audit and the discrimination table at the end, after the parameter file settles.** Budget
   ~2 hours and run them in parallel with each other, not with anything else.
7. **Expect at least one pre-registered criterion to be undecidable, and plan the addendum for it.** Five phases in a
   row have had one; Phase 3 had three and Phase 4 had three.

---

## Deliverable of this request

`PREREG_PHASE_5.md` (before any run), the code and results under `tools/phase5/` and
`docs/env_v2/generated/v2_1/e5_*/`, `envs/v2/params/observables.json` with provenance and a loud loader that raises on a
missing entry, a null interval **or an undeclared status term**, the tests of Section 9.4
(`test_observable_params_provenance`, `test_no_field_is_deterministic_in_x`, `test_onset_audit_bound`,
`test_sentiment_level_free`, `test_eps_lag_distribution`) plus a report-table consistency test, a refreshed freeze
manifest and path hashes with the checklist and level-free audit regenerated on the handed-over state, the re-run
per-field-group ablation and discrimination tables, DECISION_LOG entries `P5-*`, `PHASE_5_CHANGED_FILES.md`, the
regenerated Table 2 and `spec/` section 6, and **`PHASE_5_REPORT.md`**.

Then stop for review — do not begin Phase 6.
