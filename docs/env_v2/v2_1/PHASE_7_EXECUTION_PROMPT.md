# Prompt: execute Phase 7 of the v2.1 improvement plan (targets, action and metrics — θ derived, regret decomposed, bands checked, baselines on the run's own path)

## What this project is

**FinPersona-Bench** asks a question about LLM agents, not about markets: *when an LLM is given a persona with an
investment mandate — a risk band, a target allocation — does it keep to that mandate as market conditions change, or does
it drift?* An agent is run day by day through a multi-day market, sees a rendered snapshot (price, technicals, sentiment,
implied volatility, an analyst estimate, EPS and dividend fields), and allocates between cash and a risky asset. The
score is **mandate-conformity**, not profit: how far the agent's allocation sits outside the persona's band.

Phases 1–5 rebuilt the generator so that every parameter is fitted or tested on data; Phase 6 did the same for the
yardsticks and computed the plan's go/no-go checkpoint. **Phase 7 owns the scoring**: what a "correct" action is (the
resolvability threshold θ), what the regret metric measures (band violation vs directional agreement, with a floor and a
ceiling that mean what the documents say), whether the persona bands are consistent with the environment's own risk and
return, whether the shown dividend is real money, whether the day-1 gate is well-posed, and whether every cell's
baselines are computed on the path the agent actually saw. Nothing in this phase calls an LLM: every experiment is a
re-scoring of stored runs and a set of scripted policies, and every one of its numbers is a derivation or a measurement
on the frozen v2.1 generator.

**The governing rule of the whole programme: every generator parameter is fitted or tested on data, never stipulated.**
In your phase that reads: **θ, the half-width, the cost tier and the bands are each either derived from the environment
and the agent's information, cited to a source that was actually read, or labelled DESIGN with a sensitivity — never
"the current 0.05".** A statistic marked "(to verify)" may not appear in a parameter file, a test tolerance, or a slide.

---

## The document landscape

**The single working document is `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`.** Its shape:

| Section | What it is |
|---|---|
| 0 | What was verified before the plan was written |
| **1** | **The protocol every phase follows** — pre-register, fit or test everything, report failures as failures; the power-analysis rules |
| 2 | Weakness-to-phase map (which of the 74 review findings each phase closes) |
| 3 | Data sources, their substitutes and their biases |
| 4–14 | **Phases 0–10**, one section each. **Section 11 is yours: Phase 7, targets, action and metrics** (E7.1–E7.8) |
| 15 | Cross-phase compute, cost and effort |
| **16 / 16A** | **Order, dependencies, and the go/no-go checkpoint.** 16A was computed at the end of Phase 6 and **is not met**; the plan says the programme stops there and the team takes D17. See the decisions section below — it governs what you may start. |
| 17 | Decisions only the team can make (D7, D8, D9, D10 and D17 are yours to carry) |
| A / B / C | Power-analysis formulas · the analytic level-free bound (Phase 6 used it; your θ_info reads its output) · numbers to be recomputed |

Around it:

- `V2_1_ALTERNATIVES_REGISTER.md` — **Sections 11 (θ), 12 (the regret metric) and 13 (the target bands) are yours**
  (REG-11, REG-12, REG-13). Each names the options, **the experiment already written to decide between them**, and the
  rule. REG-11: θ_info and θ_cost co-primary, θ_var and the fixed grid as sensitivities. REG-12: the decomposition A vs
  per-window scoring B vs the labelling conventions C, decided by E7.8's construct-validity table. REG-13: practitioner
  bands A vs utility-consistent bands B vs both as a Phase-9 factor C.
- `spec/E1_V2_GENERATOR_SPEC.md` (v2.1 as built), **`spec/IO_CONTRACT.md` sections 2.2–2.3 (portfolio state, action —
  yours to rewrite)**, `spec/CALIBRATION_REPORT.md` (the E6 appendix; you do not touch it).
- `reviews/V2_WEAKNESSES.md` — the 74 findings. Yours: **26** (θ stated, not derived), **27** (half-width, dead band,
  cost, temperature stated), **33** (bands from index inputs while the environment is a single stock at ≈ 28 % σ),
  **48** (the one-shot call), **52** (MCR is band adherence with one bit of direction), **53** (MCR normalisation
  mislabelled), **54** (the day-1 gate ill-posed under start-at-target), **56** (baselines rebuilt without the cell's
  config), **60** (next-open logs the pre-trade share; placebo length asserted not tested).
- `decisions/DECISION_LOG.md` — **the P6-* entries are the freshest precedent.** Read P6-7 (one tool, one construction
  for a statistic and its null), P6-9 and P6-13 (a rule that came out negative, reported as written with the
  sensitivity beside — never re-specified), **P6-11 (16A computed as written and not met)**, P6-12 (a parameter-file
  writer that dropped fields nobody read back), P6-14 (the held-out split: a surrogate's R² does not transfer across
  scenarios). Also P0-2 and P0-3: the two Phase-0 label fixes that this phase turns into real re-specifications.
- `generated/v2_1/` — every machine-written result. Yours will be `e7_*`.
- `tests/known_defects.py` — the registry. **Its two entries are the derived L2 and L2b gates, failing, with
  "Phase 7 / D17" as the owner.** They are not yours to pass by re-scoring; see the inherited items.

---

## Context for this phase: what Phase 6 measured, and what it changes for you

Every number below is a measurement on the frozen Phase-6 state (`PHASE_6_REPORT.md` sections 3.6–3.8c; files under
`e6_*`, `e6_after/`, `e6_16a/`), the state you re-score.

**1. 16A is not met.** At θ = 0.05 with 100 scored seeds per scenario, 40 disjoint training seeds and cluster-bootstrap
intervals over seeds (`e6_16a/16A.md`, `runs.csv`):

| gate | verdict | what the failure is |
|---|---|---|
| G1 (oracle < observables oracle < best trivial, every scenario) | **FAIL** 0 of 4 | the best trivial policy is a **constant band edge**; in a directional scenario the true-V oracle rests at one edge most of the time, so the edge matches or beats the observables oracle (bull-trap: band-high 0.0262 [0.0214, 0.0312] vs 0.0383 [0.0326, 0.0448]) |
| G2 (best simple rule above the observables oracle, ≥ 3 of 4) | **FAIL** 0 of 4 | `log(P/SMA50)` at ±0.03 tracks sign(x) as well as the field-bearing oracle at the FIT 22-day half-life |
| G3 (median oracle switches ≥ 2, share ≥ 0.5) | **PASS** at θ = 0.05: medians 2 / 2 / 4 / 2, shares 0.76 / 0.61 / 0.90 / 0.77; **FAIL at θ ≥ 0.08** | the plan's expectation of failure (written at a 150-day half-life) is disconfirmed at the FIT 22.4 d — **the one-shot question is a θ question now, which is yours (E7.1, E7.2)** |
| G4a (observables oracle beats the price-only oracle) | **FAIL** 0 of 4 | the fields raise the oracle's training-pool calm R²(x) from −0.08 to 0.10 and sign accuracy from 0.78 to 0.85, and MCR does not see it |
| G4b (price-only surrogate ≤ the Appendix-B bound + allowance) | **FAIL** 0.2912 [0.264, 0.318] vs 0.2267 | the ladder puts +0.069 of it in the events' pre-event calm (Phase 4's territory, D5) |

**Read this the right way.** The gates were computed with the v2 scoring — θ = 0.05, MCR as `metrics_v2.mcr_theta`, the
v2 bands, the constant band edges as trivial policies. Three of the four failures are statements *about the scoring*
as much as about the generator: G1 fails because the trivial set includes the resting place of the oracle; G2 and G4a
fail because MCR is insensitive to what the fields add. **Your E7.2 and E7.8 are where that is decided** — and the
temptation to make 16A pass by choosing a scoring is exactly what rule 2 below forbids. The register's rule (REG-12)
is what adopts a scoring: monotone scripted sweeps and a correlation ceiling derived from them, not the checkpoint's
verdict.

**2. The information the agent has, measured** (`e6_after/audit_after_derived.md`; 1,600 paths, GBT, held-out
seeds). Sign accuracy of x̂ on resolvable steps at θ = 0.05: full feature set **0.800 [0.791, 0.810]** on all rows,
0.685 [0.661, 0.708] on calm rows, 0.891 on event rows; the level-free price-only control 0.784 / 0.646 / 0.896.
**θ_info (E7.1a: the |x| at which the level-free observables surrogate reaches sign accuracy 0.80) is reached on the
pooled rows at about θ = 0.05 and is not reached on calm rows at any θ you will find** — the register's own failure
mode ("θ_info is reported as not reached and θ_cost alone is primary") is live for the calm population. Report θ_info
per population and per scenario (the held-out split, P6-14, says the pooled surrogate is within-scenario structure).

**3. Coverage by θ** (`audit_after_derived_L4.csv`; the share of steps with |x| ≥ θ): calm rows 0.587 / 0.366 / 0.172
at θ = 0.03 / 0.05 / 0.08; panic 0.849 / 0.754 / 0.625; blow-off 0.996 / 0.992 / 0.983; the median |x| on calm rows is
0.037. **Every θ you derive changes which steps are scored**; report coverage beside every headline.

**4. The x process in force** (E6.6, `e6_6/bound.json`): FIT half-life **22.4 d** (`envs/v2/params/mispricing.json`),
the stationary s_x **0.0656** derived by the variance identity, the median 200-day sd(x) on flat paths **0.0463
[0.039, 0.072]** (`phase6_criteria.json` `item9_reference`). **θ_var (E7.1c) is read from these files, not
re-estimated**; the T = 200 sd is the 0.046, the stationary sd is the 0.066, and which one "one within-run sd" means is
stated in the pre-registration before the number is used.

**5. The cost tier as implemented** (`simulation/portfolio_v2.py`): `cost_bp = 5.0` charged on |traded value| **per
trade**, a dead band of 1 point inside which no trade is made, `execution="next_open"` deferring the retarget. The plan's
anchor is a round trip (weakness 27); the cost concept (quoted spread 4.5 bp, Nasdaq 2024; median market impact 6.18
bp, Frazzini–Israel–Moskowitz 2018 — both read) is to be named in E7.7. θ_cost (E7.1b) is the break-even of a full
reallocation over one half-life against the round-trip cost at this tier; its inputs are the FIT half-life, the
persona's band width and the cost — every one a file value.

**6. The regret metric as implemented** (`evaluation/metrics_v2.py`): `mcr_theta` = mean |C_t − c*_t| over resolvable
steps with `oracle_target` a V-oracle that moves to a band edge when |x| > θ and holds otherwise; `floors_and_ceilings`
normalises every lower-is-better metric, MCR included, **against constant-mix as the ceiling and the worst of
{always-buy, always-sell, random} as the floor** — P0-2 relabelled it, the published `norm_mcr` values are annotated
"against constant-mix" in `status/PILOT_NOTES.md`, and **E7.2 re-specifies it** (ceiling = mandate oracle, floor = worst
trivial policy, the sign handled in one function). `THETAS = (0.03, 0.05, 0.08)` is hard-coded there; the θ in force
must come from a parameter file with provenance (`test_theta_in_force_with_provenance`).

**7. The day-1 gate** (`tools/report_v2.py`, P0-3): restricted to common-start cells; the start-at-target ΔC_1 table is
`exploratory_deltaC1_start_at_target`. E7.5 re-specifies it on the common-start design only, with the null from the O3
numerical-only arm and the no-persona trader.

**8. Baselines per cell** (`tools/report_v2.cell_baselines`, weakness 56): rebuilt from the run's metadata without
n_assets, engine, b_pred or env_config. **The pilot's runs (`status/PILOT_NOTES.md`: 36 + 9 + 3 runs, Gemini 2.5 Flash,
T = 200, seed 42, 23 Aug) were made on the v2 generator.** Every v2.1 change is a switch with v2 behind it, so a v2 path
is *supposed* to be reproducible from its `meta.json` — E7.6's first test is exactly whether it is (regenerate the
pilot's path from `env_metadata.gen_config` under the v2 switches, compare the path hash). If it is not, the pilot is
re-scored on its logged columns only, the baselines are rebuilt only where the hash matches, and the report says which.

**9. The bands and the JFE spread** (`evaluation/targets.py`): cash bands 0.70–0.90 / 0.40–0.60 / 0.00–0.20, centres,
`JFE_SPREAD = (0.06, 0.12)` at line 35 — the plan records that Jiang–Peng–Yan (2024) Table 7 states no
conservative-minus-aggressive spread, so **the ordering check may not run until the spread is re-derived from the table
in your report** (E7.3). The environment's own (μ, σ) for the Merton table are Phases 1–3's FIT values
(`envs/v2/params/*.json`), with dividends paid (E7.4) — the annual σ of the v2.1 generator is a number you compute from
the frozen state and cite, not the v2 "≈ 28 %".

**10. The derived leakage gates fail** (E6.6/E6.7): L2 all-rows +0.0263 against a registered margin of −0.0214
(centred reading undecided), calm-trained +0.1088 against −0.0313, L2b +0.0295 against −0.0023. **These are not
scoring questions and nothing you do changes them**; they are D17's. They matter to you in one way: θ_info reads the
same surrogate, so "what the agent can resolve" already includes the fields' calm-trained contribution (VAL +0.051,
the wandering multiple). Say so where θ_info is reported.

**11. The dividend field.** Phase 5 built the FIT DPS process with both renderings (`shown` / `hidden`) and D10 is
still open; the harness half — dividends **paid into cash on ex-dates** — was explicitly left to this phase
(`PHASE_5_REPORT.md` section 7). Until it is done, the shown yield is not real money and the Merton table's μ is wrong
by the yield.

---

## Read first, in this order

1. **Section 11 of the plan** — your phase, in full; then **16A and Section 17 (D7–D10, D17)**; then Appendix B (θ_info's
   surrogate is the one it bounds).
2. **`PHASE_6_REPORT.md` section 0** (the state table), **3.8b** (16A with its reading), **3.8c** (the audit's sign
   accuracies, coverage and the held-out split), **section 5** (D17 laid out per gate — read what each option would do
   to *your* inputs) and **section 7** (what was handed to you).
3. **`V2_1_ALTERNATIVES_REGISTER.md` Sections 11–13** — your three contests, with the experiments already written.
4. **`DECISION_LOG.md` P0-2, P0-3, P6-11, P6-14.**
5. **`evaluation/metrics_v2.py`, `evaluation/targets.py`, `tools/report_v2.py`, `simulation/portfolio_v2.py`,
   `evaluation/observables_oracle.py`** — what you are changing. `metrics_v2.py` and `targets.py` are under the freeze
   manifest; you are the phase that may touch them. **Every change is a switch with the current behaviour behind it,
   proved inert when off** — `score_run(..., scoring="v2")` returns the v2 dictionary bit for bit, and the 95-configuration
   path-hash fixture is unchanged (you change no path).
6. **`tools/phase6/e6_16a.py`** — reuse it whole: `Oracle16A` (the level-free observables and price-only oracles with a
   20-day history, pickled under `e6_16a/`), `rule_policy` / `fit_rules` (the pre-registered rule family), the trivial
   policies, `evaluate` (MCR with cluster-bootstrap intervals over seeds, the switch counts by θ), `runs.csv` (every
   run's per-day allocations — **re-score these under every scoring you propose before you write a line of new
   simulation**). `tools/phase6/e6_after_state.py` is the after-state chain pattern; `e6_report_tables.py` /
   `e6_cite_check.py` / `e6_changed_files.py` are the report discipline (copy them to `tools/phase7/`).

---

## Decisions: what governs what you may start

**D17 first.** The plan is explicit: if any of G1–G4 fails, the programme stops after Phase 6 and the team takes D17 —
Phase 5's field redesign, D3's environment choice, or D8's scoring options, "each of which re-runs Phases 2 and 6 for
the chosen option"; if none is taken, the paper's claims are restricted to a one-shot mandate-conflict benchmark.
**You do not begin the gated experiments (E7.1's θ values in force, E7.2's adopted scoring, E7.3's scored bands) until
D17 is recorded in `DECISION_LOG.md`** — a re-opened Phase 5 or D3 changes the state you would derive θ from. What you
*may* start regardless, because it is a correctness fix or a derivation whose inputs D17 cannot change:

- E7.4 (dividends paid; a `simulation/` change, tested by the portfolio identity),
- E7.5 (the day-1 gate on the common-start design),
- E7.6 (baselines on the run's own path; the reproducibility test of the pilot's paths),
- E7.7 (band consistency, pre/post-trade logging, the cost statement, the DESIGN labels),
- E7.8's scripted-policy machinery and the construct-validity table on the Phase-6 state (it is the *discriminator*
  for REG-12; running it before D17 costs nothing and tells the team which scorings are even admissible),
- the pre-registration, with every rule in final form and every derivation's inputs named by file.

**Ask for, in your first message:** D17 (with the report's section 5 table in front of the team), **D10** (the harness
half is yours either way: pay dividends into cash, or remove the field and its leakage channel), **D9** (practitioner
vs utility-consistent bands: the register's rule makes A the default unless Phase 9's interaction exceeds the
equivalence margin, so what you need now is approval of the *default*, not the choice), **D8** (the one-shot question is
now θ-conditional — put G3's θ profile to the team with E7.1's derived values beside it), and **D7** (θ_info not reached
on calm rows: confirm that θ_cost alone is primary there, per REG-11's stated failure mode). Do not pre-empt D2 (the
LLM roster) — this phase makes no API call — or D5 (event dynamics) or D3.

---

## What Phase 6 hands you (do not redo this work)

- **The frozen v2.1 state** with its hashes (`path_hashes_phase6_after.json` = the Phase-5 fixture, 0 of 95
  configurations changed; the freeze manifest re-written, 27 files; the whole test tree at 172 passed / 1 skipped / 4
  strict xfails).
- **The criteria file** `evaluation/params/phase6_criteria.json` with its loud loader `evaluation/criteria.py` — the
  reference percentiles with their n, the derived gates, `item9_reference` (the 200-day sd(x) band), and the pattern
  for your θ file: every block with `label`, `source`, `date`, `interval`, `n` and a declared status.
- **The panel of the hand-over state** `_panels/sep_phase5_after.pkl` (1,600 paths; git-ignored, regenerable in
  3 minutes) and its derived-gate audit under `e6_after/` — the sign accuracies, R²(x) and coverage per phase group
  and per feature set, with intervals, and the held-out-scenario split.
- **16A's machinery and every run** under `e6_16a/` (above), the checklist at 500 seeds under A/B/C
  (`e6_after_checklist*`), the known-answer tests (`e6_9/`), the reference distributions (`e6_1/`).
- **The n/m convention** (an undefined P/E is NaN in the frame, `"n/m"` in the observation, cap + indicator on the
  audit side; `tools/phase5/common.encode_nm`) — every consumer of a panel applies it, including your scripted policies.
- **The tuned-parameter ledger** (`PHASE_6_REPORT.md` 3.10): the record of what v2 tuned to pass — your θ, half-width
  and cost entries go in the same form (what moved, when, against what).
- **The box, verified** (P6-15; `e6_0/box_stage3.log`): the code is on it at commit `74819bd`, the numeric
  cross-machine check reports SAME GENERATOR (0 of 245 columns above 1e-9), `test_smm_reference_row` passes and
  `BASE|x|all` refits to the laptop's value exactly; the 1,600-path panel builds in 7 s at 24 workers. It is a
  reference machine for sklearn stages. This phase needs none; see the compute section.

---

## What to do now: Phase 7, Section 11 of the plan

Eight experiments. In the plan's numbering, with what Phase 6 adds to each:

- **E7.1 θ derivation.** Three candidates, each computed from files and reported with its inputs: (a) **θ_info** — the
  |x| at which the level-free observables surrogate's sign accuracy on steps with |x| ≥ θ reaches 0.80, computed on the
  stored audit's held-out predictions (`e6_after/audit_after_derived.pkl` carries the per-row x̂ if you store it; else
  refit the audit's GBT once, 5-fold GroupKFold by path, and store the predictions) **per population (all, calm) and per
  scenario**; "not reached" is a result. (b) **θ_cost** — the break-even mispricing: a full reallocation across the
  persona's band width, expected reversal over one FIT half-life (22.4 d; the expected fraction of x recovered in one
  half-life is ½ by definition), against the round-trip cost at the implemented tier (2 × 5 bp), per persona; state the
  formula in the pre-registration and test it on a synthetic case. (c) **θ_var** — one within-run sd of x at T = 200,
  read from `item9_reference`. Then **every headline metric** (MCR and its two terms, coverage, oracle switches,
  band-MAS) re-scored at θ ∈ {0.03, 0.05, 0.08, 0.12, 0.20} and at the three derived values on `e6_16a/runs.csv` (the
  oracles, rules and trivial policies), on the pilot runs and on the baselines — no API. **Rule as registered (REG-11):
  θ_info and θ_cost co-primary; where θ_info is not reached, θ_cost alone.** The θ in force goes to a parameter file
  with provenance; `metrics_v2.THETAS` reads it.
- **E7.2 Regret decomposition.** MCR = B_t (band violation, max(0, |C_t − centre| − hw)) + D_t (within-band distance to
  the oracle's band edge) on resolvable steps; `test_mcr_decomposition_identity` on synthetic runs; the oracle switch
  count and the share of resolvable steps at each band edge (item 48) beside every number; **ceiling = the
  mandate-conditional oracle (0 by construction), floor = the worst trivial policy**, the sign in one function, the
  pilot's `norm_mcr` recomputed and the old kept beside. **Per-window scoring (REG-12 B) is built as the pre-registered
  alternative** — the oracle's target per 25-day window, regret per window then averaged — and G3's switch count is
  re-stated per window. The adoption rule is E7.8's, written before either scoring's numbers are read.
- **E7.3 Bands vs the environment's own risk-return.** The Merton shares with the v2.1 generator's (μ, σ) — computed
  on the frozen state with dividends paid, with intervals from the Phase 1–3 fits — for γ ∈ {2, 3, 4, 6, 8, 10}; where
  each persona's practitioner band sits; the two readings (A practitioner, B utility-consistent) with the consequences
  for band-MAS and the mandate oracle; **the JFE ordering check only after `JFE_SPREAD` is re-derived from
  Jiang–Peng–Yan Table 7 in the report**, and if the table does not give one, the check is removed with the reason and
  `targets.py:35` says so.
- **E7.4 Dividends.** Paid into cash on ex-dates from the DPS process (quarterly), `test_dividends_paid` and the
  portfolio-value identity; the effect on every baseline reported. If D10 removes the field, both the field and its
  leakage channel go (the `hidden` rendering exists; the DPS process stays in the generator).
- **E7.5 Day-1 gate.** On the common-start design only (C_1 levels; KW, Cliff's δ, band-hit, AUC), the null from the
  O3 numerical-only arm and the no-persona trader; the ΔC_1 version removed with the reason; `test_gate_common_start_only`.
- **E7.6 Baselines per cell.** `cell_baselines` rebuilt from the run's `meta.json` — engine, n_assets, b_pred,
  ordering, start price, every field of `Gen_Config_Hash` — and **`test_baselines_same_path_hash`**: the baseline's path
  hash equals the run's. First run it on the pilot (item 8 above) and report which cells reproduce.
- **E7.7 Small items.** Trader band consistency (0, 1) everywhere (`test_trader_band_free`); next-open execution logs
  pre- and post-trade cash share (item 60); the cost stated as per trade with the anchor's concept named; the dead band
  and half-width labelled DESIGN with the half-width sensitivity {0.05, 0.10, 0.15} on the re-score; placebo length
  matching tested, not asserted.
- **E7.8 Metric validity.** (a) Scripted policies with a swept parameter — allocation drift rate → band-MAS;
  value-alignment probability → the directional term; panic intensity → drawdown — each metric monotone in its sweep,
  as a table with intervals; (b) the metric-correlation matrix across cells (|r| among band-MAS, B, D, return, drawdown,
  turnover) with the pre-registered statement of which pairs are collinear by construction; **(c) the REG-12 rule
  applied**: adopt the scoring under which every sweep is monotone and |corr(MCR, band-MAS)| across cells is below the
  ceiling derived from the sweeps (the collinearity floor when only the drift rate varies, plus the bootstrap
  half-width); if A and B both qualify, A; if neither, the matrices and D8.

**E7.1 and E7.2 are the deliverables that matter most.** θ defines "correct"; the decomposition is what makes G1, G2
and G4a's failures interpretable — *and it is the one place in the programme where a scoring choice could be made to
flip a checkpoint.* The register's rule, not the checkpoint, adopts a scoring; 16A is re-computed under the adopted
scoring **as a reported consequence, labelled as such, beside the Phase-6 verdict — never as a replacement for it.**

---

## Hard rules (from the plan; not optional)

1. **Pre-register before you run.** `PREREG_PHASE_7.md` exists before the first re-score, with θ's three formulas and
   their file inputs, the decomposition, the adoption rule of E7.8 with its ceiling's construction, the Merton inputs
   by file, the gate's null, and the switch list. If a rule later proves wrong, that goes in an addendum with the
   disconfirmation stated as loudly as any confirmation, and results are reported under both.
2. **No scoring is chosen to pass 16A.** The re-computation of G1–G4 under an adopted scoring is a consequence, reported
   beside the Phase-6 verdict with the same seeds and intervals; the adoption rule is REG-12's and is written before any
   G is read under it. A shorter half-life is not a knob (16A, edit 27 Aug); neither is θ.
3. **Every change to the scoring, the portfolio or the report machinery is a switch with the current behaviour behind
   it, proved inert when off.** `evaluation/metrics_v2.py` and `targets.py` are under the freeze manifest; so is
   whatever you add. `score_run(scoring="v2")`, `floors_and_ceilings(convention="v2")`, `PortfolioV2(dividends=False)`.
4. **Report failures as failures, with evidence. Numbers carry their `n`.** A θ_info that is not reached, a Merton
   table that puts every persona in one band, a pilot path that does not reproduce — each is a result, stated as such.
5. **`datasets/` is git-ignored and must never be uploaded anywhere.** Nothing in this phase needs it.
6. **`envs/` is not yours** (no path changes; the 95-configuration hash fixture stays byte-identical). **`simulation/`
   is yours for E7.4 and E7.7 only**, `evaluation/` for the scoring, `tools/report_v2.py` for the gate and the
   baselines; `agent/` not at all.
7. **Work stays on `main`. Do not create branches. Commit only when asked**, one-line message, no body, no trailers.

### Method rules Phases 4–6 learned the expensive way

8. **Pin the configuration a tool measures** (P4-19) and **measure after the parameter file settles** (P4-45): every
   number in your report comes from a state whose hash you recorded — for you, the θ file and the scoring switch.
9. **Verify every file you cite exists** before the citation is written (P4-37); run the cite check on every document.
10. **Run the WHOLE test tree** (P4-38). Phase 6's run found two v2 docs tests and one of its own that the new state
    broke — the older tests are what break.
11. **Read a parameter file back before you read a result under it** (P6-12). Phase 6's criteria-file writer dropped
    the per-statistic overrides and a descriptive flag; the first table was read under the defect. Your θ file and
    your scoring switches get a test that asserts every registered field is *in the file*, run before the first re-score.
12. **A statistic and its null (or its ceiling) come from one tool with one construction** (P6-7, P5-16). E7.8's
    correlation ceiling is derived by the same code that computes the matrix it bounds.
13. **A tool's "done" check tests emptiness, not presence** (P5-12).
14. **Generate every report table from its file** into a marked block and add the test that reads it back
    (`tools/phase6/e6_report_tables.py --check` is the pattern; `test_phase6_report_tables_match_files` the test).
15. **Make every chain resumable and staged**, each stage its own files, anything over ten minutes in the background
    with `python -u`. Nothing here should take ten minutes; if something does, that is a finding about the tool.
16. **A generated list that lists itself flips on every write** — exclude it (Phase 6's changed-files generator).

---

## Documentation: keep it current as you go, not at the end

- **`PHASE_7_REPORT.md` is written as results land**, under the protocol's six headings, section 0 the state table,
  section 1 the citation table (Merton 1969/1971; Sun et al. 2006; Nasdaq 2024; Frazzini–Israel–Moskowitz 2018;
  Jiang–Peng–Yan 2024 Table 7; Fieberg et al. 2025; the practitioner pages — each marked read / not re-read, and **no
  number from a source that was not read**: Donohue–Yip stays unverified and unused).
- **Every decision gets a DECISION_LOG entry (`P7-*`)** with the alternative rejected and the evidence file.
- **The θ file** (`evaluation/params/scoring.json` or the name you choose): θ_info per population and scenario with
  "not reached" where it is, θ_cost per persona with the formula's inputs, θ_var with its source, the θ in force and the
  rule that put it there, the half-width and dead band as DESIGN with their sensitivities, the cost tier with its
  concept, the band convention in force (A) with B beside — each with provenance and status; a loud loader;
  `test_theta_in_force_with_provenance` reads it.
- **`IO_CONTRACT.md` 2.2–2.3** rewritten (dividends in the portfolio state; pre/post-trade shares in the log; the
  scoring's fields); **`PILOT_NOTES.md`** re-scored under the new definitions with the old beside; **`targets.py`
  docstrings** with sources; the plan's amendments (θ, MCR, gate, dividends) recorded in your report, not by editing
  the plan.
- **`PHASE_7_CHANGED_FILES.md`** generated from git and verified against disk.
- **The known-defect registry** is not yours to empty; if D17 re-opens Phase 5 and the gates pass on the new state,
  the XPASS removes the entry then.

---

## Compute: where to run what

**Everything in this phase is a re-scoring or a scripted policy: minutes on the laptop, no API cost** (the plan's
11.6). The only stage that could exceed ten minutes is a refit of the audit's GBT to store per-row predictions for
θ_info (≈ 100 s per fit × 5 folds × 2 feature sets on the laptop); run it once, store the predictions under `e7_1/`,
and everything downstream reads the file.

**The laptop is the reference environment; the box is a verified second one** (`docs/COMPUTE_GPU_ACCESS.md`,
`tools/phase6/box_bootstrap.sh`, `box_numeric_check.py`; P6-15): at the end of Phase 6 the numeric cross-machine check
passed at 1e-9 relative and both reference rows reproduced exactly, so a sklearn number computed there may be reported
with the state's commit recorded. Re-run the numeric check at the start of every session (the machines get reset); the
tunnel drops for hours at a time, every ssh call needs `-o ConnectTimeout=150` and an outer `timeout ≥ 400`, nothing
sleeps inside a session, and a changed file is deleted before it is fetched (never resumed across versions). If this
phase refits the audit's GBT for θ_info's per-row predictions, that is the one stage worth sending there (minutes at
24 workers). Never upload `datasets/`; never store a credential there.

**Kaggle** (`docs/COMPUTE_KAGGLE_GUIDE.md`) is available and not needed.

---

## Inherited open items

- **D17** — the programme's stop. Phase 7's gated experiments wait for it; its options each change your inputs
  (a re-opened Phase 5 changes θ_info; D3 changes σ_V and hence θ_cost's half-life and the Merton σ; D8's scoring
  options are E7.2/E7.8's own alternatives).
- **The two registry entries** (derived L2 / L2b gates, failing) — owner D17 / Phase 7 in the sense that this phase
  carries them, not that re-scoring can pass them.
- **The all-rows L2 centred reading** undecided at 40 draws (0.0004 on a half-width of 0.0148) — decidable only on a
  larger panel; ask the team whether they want it decided before spending the compute.
- **Item 12** (the sentiment loading realised at 70 % of configured; D15's owner) and **item 7** (the generator's volume
  is more log-normal than real volume) — not yours, carried.
- **D10's harness half** (dividends paid) — yours, E7.4.
- **G3's θ profile** (PASS at 0.03–0.05, FAIL at ≥ 0.08) — becomes part of E7.1's report and D8's table.
- **The pilot's paths under the v2.1 switches** — reproducible or not is E7.6's first finding.
- **Phase 8** (harness and statistics) is independent of you and its E8.5 variance pilot was waiting for the Phase-6
  freeze, which exists now; it can run in parallel with this phase on D2's roster.

---

## My recommendation for how to begin, and why

1. **First message: D17 with the report's section 5 table, then D10, D9, D8, D7** — and start E7.4–E7.8's machinery
   while you wait; none of it depends on a decision.
2. **Re-score `e6_16a/runs.csv` under the decomposition and under per-window scoring before touching the pilot.** The
   16A runs are 1,200 policies × 200 days with the true x beside; they answer in minutes what the adopted scoring does
   to G1, G2 and G4a, and E7.8's discriminator runs on the same frame.
3. **Derive θ_cost and θ_var from files first** (they are arithmetic on FIT values), then θ_info from the stored audit
   — and write all three into the pre-registration with their inputs before you read what any of them does to a
   headline metric.
4. **Expect θ_info "not reached" on calm rows and reached near 0.05 on pooled rows.** That is REG-11's stated failure
   mode, not a surprise; report it per scenario, because the held-out split says the pooled surrogate is within-scenario.
5. **Run E7.6's reproducibility test on the pilot on day one.** If the pilot's v2 paths do not regenerate under the
   switches, the pilot is a logged-columns re-score only, and the report must say so before any pilot number moves.
6. **Compute the Merton table with intervals and put it beside the practitioner bands without adopting either.** D9's
   default is A by the register's rule; your job is the table, and the sentence that says where each persona sits.
7. **Expect at least one pre-registered rule to be undecidable or to come out the wrong way.** Seven phases in a row
   have had one; the addendum is part of the deliverable.

---

## Deliverable of this request

`PREREG_PHASE_7.md` (before any re-score; the three θ formulas with their file inputs, the decomposition, E7.8's
adoption rule with its ceiling's construction, the Merton inputs, the gate's null, the switch list), the code under
`tools/phase7/` and the results under `docs/env_v2/generated/v2_1/e7_*/`, the θ / scoring parameter file with
provenance and a loud loader, the tests of Section 11.4 (`test_theta_in_force_with_provenance`,
`test_mcr_decomposition_identity`, `test_floor_ceiling_signs`, `test_gate_common_start_only`,
`test_baselines_same_path_hash`, `test_dividends_paid`, `test_trader_band_free`) plus the inertness test of every
switch and a report-table consistency test, the θ table (three derivations per population and scenario, every headline
metric at the grid and the derived values), the construct-validity table and the correlation matrix with the adopted
scoring and the rule that adopted it, the Merton table beside the practitioner bands, the pilot re-scored with the old
beside, the baselines rebuilt with the hash test, 16A re-stated under the adopted scoring beside the Phase-6 verdict,
the refreshed freeze manifest (path hashes unchanged), `IO_CONTRACT.md` 2.2–2.3 and `PILOT_NOTES.md` updated,
DECISION_LOG entries `P7-*`, `PHASE_7_CHANGED_FILES.md`, and **`PHASE_7_REPORT.md`**.

Then stop for review — Phase 9's grid and Phase 8's power analysis take θ and the scoring from this phase.
