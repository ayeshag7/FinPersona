# Pre-registration — Phase 7 of the v2.1 improvement plan (targets, action and metrics)

**Written 10 September 2026, before the first re-score.** Plan Section 11 (E7.1–E7.8); register Sections 11 (θ),
12 (the regret metric), 13 (the target bands); weaknesses 26, 27, 33, 48, 52, 53, 54, 56, 60.

Every rule below is in final form. A rule that later proves wrong is recorded in `PREREG_PHASE_7_ADDENDUM.md`
with the disconfirmation stated as loudly as any confirmation, and the result reported under both readings
(the Phase 1–6 practice; P6-9, P6-13).

---

## 0. The state this phase measures, and the decisions that govern it

The frozen Phase-6 state: `path_hashes_phase6_after.json` (= the Phase-5 fixture, 0 of 95 configurations changed),
the freeze manifest of 27 files, the parameter files under `envs/v2/params/`, the criteria file
`evaluation/params/phase6_criteria.json`. **Nothing in this phase changes a path**; the 95-configuration hash
fixture must be byte-identical at the end (`envs/` is not this phase's to touch).

Team decisions recorded on **10 September 2026** (DECISION_LOG `P7-1`, `P7-2`, `P7-3`), before any experiment ran:

| decision | recorded | consequence for this phase |
|---|---|---|
| **D17** | **restrict the claim** — no repair option (Phase 5 field redesign, D3, D8) taken; the paper's claims are restricted to a one-shot mandate-conflict benchmark and say so | the gated experiments (E7.1's θ in force, E7.2's adopted scoring, E7.3's scored bands) may run on the frozen Phase-6 state; θ_info's surrogate, θ_cost's half-life and E7.3's σ are the Phase-6 values and do not move |
| **D10** | **dividends paid into cash** on ex-dates from the FIT DPS process | E7.4 is the harness half; the Merton μ of E7.3 carries the yield; the `hidden` rendering stays available as the alternative arm |
| **D9** | **A (practitioner bands) is the scored default**; B (utility-consistent Merton bands) computed and reported beside it as the sensitivity; Phase 9 carries both as a factor | E7.3 produces the table and the sentence that says where each persona sits; no band moves in this phase |

**D7 and D8 are deliberately not asked yet.** D7 (θ_info not reached ⇒ θ_cost alone primary) and D8 (the one-shot
question, now θ-conditional) are put to the team **with E7.1's derived values and G3's θ profile beside them**,
after E7.1 lands and before the θ in force is written to the parameter file. Until then the parameter file's
`theta_in_force` block is absent and `metrics_v2.THETAS` keeps its v2 value.

**D2 (the LLM roster), D5 (event dynamics) and D3 are not pre-empted.** This phase makes no API call.

---

## 1. E7.1 — the three θ derivations

Each is computed from files. Every input is named with the file it is read from; no input is re-estimated in this
phase, and no value marked "(to verify)" enters any of them.

### 1.1 θ_info (E7.1a) — the information threshold

**Definition.** θ_info is the smallest θ on the evaluation grid at which the **level-free observables surrogate's
sign accuracy of x̂ on the steps with |x| ≥ θ reaches 0.80.**

**Construction — the audit's, unchanged (rule 12: one tool, one construction).** The surrogate is
`evaluation/leakage_audit`'s GBT (`HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6,
random_state=0)`), out-of-sample predictions from `GroupKFold(n_splits=5)` with groups = `scenario-seed`, on the
frame produced by `_prepare(panel, feature_keys, control="level_free")` — the same lag depth (`N_LAGS = 5`), the
same n/m encoding (`tools.phase5.common.encode_nm`, cap + indicator), the same shown-field list
(`agent.render.rendered_market_fields("v2")` + `reported_PE_nm`), on the same panel
(`_panels/sep_phase5_after.pkl`, 1,600 paths, 320,000 rows, 288,000 after the lag drop). Two feature sets:
**`full`** (every rendered field) and **`price_only`** (the level-free control set `LEVEL_FREE_KEYS`).

This is the construction that produced the published Phase-6 sign accuracies (`e6_after/audit_after_derived_L2.csv`:
full 0.800 [0.791, 0.810] all rows, 0.685 [0.661, 0.708] calm, 0.891 event; level-free price-only 0.784 / 0.646 /
0.896 at θ = 0.05). **Verification before use:** the refit's sign accuracies at θ = 0.05 must reproduce those four
numbers to within 1e-12 (the same seed, the same folds, the same rows). If they do not, the refit is a different
construction and θ_info is not computed from it — the discrepancy is reported and the phase stops on E7.1a.

**Grid.** θ ∈ {0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30} — the plan's five
values plus the finer spacing needed to locate a crossing. θ_info is reported as the **smallest grid value at which
the accuracy is ≥ 0.80 and stays ≥ 0.80 at every larger grid value** (a crossing that reverses is reported as such,
not smoothed).

**Populations, pre-registered before the numbers are read.** Reported **per population** (`all` rows; `calm` rows,
the audit's `macro` phase group) **and per scenario** (flat, bull_trap, crash, sustained_bull) — the held-out split
(P6-14) says the pooled surrogate is within-scenario structure, so a pooled θ_info is not a per-scenario θ_info.
Every cell carries its `n_resolvable` and a percentile cluster-bootstrap 95 % interval over paths (500 resamples,
the audit's `_cluster_ci`).

**"Not reached" is a result.** Where the accuracy does not reach 0.80 at any grid value, θ_info is reported as
**not reached**, with the maximum accuracy attained and the θ at which it occurs. **Stated expectation (REG-11's
own failure mode, and the Phase-6 measurement):** θ_info is reached on the pooled rows at or near θ = 0.05 and is
**not reached on calm rows at any θ**. This expectation is recorded so that its disconfirmation is visible.

**The caveat that travels with every θ_info number.** The derived L2 gates fail (E6.6/E6.7): the fields' calm-trained
contribution is +0.1088 against a registered margin of −0.0313, of which Phase 5's ablation puts +0.051 in the
wandering multiple. θ_info reads the same surrogate, so "what the agent can resolve" already includes that
contribution. This sentence appears wherever θ_info is reported.

### 1.2 θ_cost (E7.1b) — the cost break-even

**Formula, pre-registered.** Let

- `w = hi − lo` the persona's band width in cash-share units (`evaluation/targets.BANDS`),
- `c = cost_bp / 10000` the per-trade cost rate (`simulation/portfolio_v2`, `cost_bp = 5.0` ⇒ c = 5 × 10⁻⁴,
  charged on |traded value| **per trade**),
- `h` the FIT mispricing half-life (`envs/v2/params/mispricing.json`, `half_life.value` = 22.380929759136894 d,
  interval [18.75, 32.64], n = 417),
- `f` the expected fraction of x recovered over the holding horizon.

A full reallocation across the band moves the risky weight by `w`. Over one half-life the expected reversal of a
mispricing x is `f·x` with **f = ½ by definition of the half-life**, so the expected profit of being on the correct
side is `w · f · x`. The round trip is two trades of traded value `w`, so its cost is `2 · c · w`. The break-even is

> **θ_cost = 2c / f**, and at the registered horizon of one half-life (f = ½), **θ_cost = 4c**.

**The band width cancels and the half-life enters only through f.** This is a property of the registered formula,
not a choice made after seeing a number: it is written here, before the value is computed, so that a θ_cost that is
identical across personas is read as the formula's consequence and not as an error.

**Pre-registered sensitivities** (reported beside, never as the primary):
(i) the **one-day** holding horizon, f₁ = 1 − 2^(−1/h) — the expected one-day reversal, where h enters materially;
(ii) the **infinite** horizon, f = 1 (θ_cost = 2c);
(iii) the **cost tier**: θ_cost as a function of c, with the c that would place θ_cost at each grid θ reported, and
the two read cost anchors named — Nasdaq (2024) 4.5 bp cap-weighted **quoted spread** of the S&P 500 basket, and
Frazzini–Israel–Moskowitz (2018) **median market impact** 6.18 bp per trade (mean 9.97). These are different cost
concepts; E7.7 states which one the implemented 5 bp per side represents.
(iv) the half-life at each end of its FIT interval (18.75 / 32.64 d) for the f₁ form.

**Test on a synthetic case (`test_theta_cost_break_even`).** An AR(1) x at the FIT half-life, a deterministic price
path built from it, two policies differing by exactly `w` in risky weight, run through `PortfolioV2` at
`cost_bp = 5.0` with the dead band disabled: the realised profit difference net of cost crosses zero at
x = θ_cost within the discretisation tolerance. **If the numerical break-even differs from the closed form by more
than 10 %, the closed form is reported as an approximation with the numerical value beside it**, and the
discrepancy goes in the addendum.

### 1.3 θ_var (E7.1c) — one within-run sd of x

**Read from files, not re-estimated** (the prompt's rule; P4-45).

> **θ_var = the generator's median 200-day sd(x) on flat paths = 0.046321**
> (`docs/env_v2/generated/v2_1/e6_after_checklist_reference_extra.csv`, item 9, population `flat`, n_gen = 500),
> with the AR(1) reference band **[0.03892, 0.07235]** at the FIT half-life as its interval
> (`evaluation/params/phase6_criteria.json` → `item9_reference.value.sd_lo/sd_hi`, n = 400 reps at T = 200).

**"One within-run sd" means the T = 200 sd**, stated here before the number is used, because the plan's text is
"one within-run sd of x at T = 200" (Section 11.2, E7.1c). The **stationary** sd `s_x = 0.0656091445844151`
(`item9_reference.value.s_x`, derived by E6.6's variance identity) is the **sensitivity**, reported beside — it is
what x's sd would be over an unbounded run, not within a 200-day one.

### 1.4 The rule that puts a θ in force (REG-11, unchanged)

> **θ_info and θ_cost are co-primary.** Every headline metric is reported at both, with θ_var and the fixed grid
> {0.03, 0.05, 0.08, 0.12, 0.20} as sensitivities. **Where θ_info is not reached, θ_cost alone is primary** for that
> population (REG-11's stated failure mode; D7 confirms it).

**The θ in force is written to `evaluation/params/scoring.json` only after D7 and D8 are recorded.** Until then the
file ships every derived value with its provenance and status and **no `theta_in_force` block**; the loud loader
raises if a consumer asks for a θ in force that the file does not carry.

### 1.5 What is re-scored at every θ

MCR and its two terms (E7.2), coverage, oracle target switches, band-MAS — at θ ∈ {0.03, 0.05, 0.08, 0.12, 0.20}
**and** at each derived value, on:

- the 16A policy set (oracles, the fitted rules, the trivial policies) on the same 4 scenarios × 100 scored seeds ×
  3 personas as Phase 6, with the same 40 disjoint training seeds and the same pickled oracles;
- the pilot runs (`results_v2_pilot/`, 52 runs, Gemini 2.5 Flash, T = 200, seed 42);
- the per-cell baselines.

**No API call is made.** Intervals are percentile cluster bootstraps over **seeds** (500 resamples), the Phase-6
construction, because the three personas share a path.

---

## 2. E7.2 — the regret decomposition, and the floor and ceiling

### 2.1 The decomposition

On **resolvable steps only** (|x_t| ≥ θ), with `centre` and `hw` the persona's band centre and half-width
(`evaluation/targets`), `c*_t` the mandate-conditional oracle target and `C_t` the agent's cash share:

> **B_t = max(0, |C_t − centre| − hw)** — the band-violation term (how far outside the mandate the agent sits);
> **D_t = |C_t − c*_t| − B_t** — the directional term (the remainder: how far the in-band part of the allocation
> sits from the oracle's band edge);
> **MCR = mean over resolvable steps of (B_t + D_t) = mean |C_t − c*_t|**, identically.

`test_mcr_decomposition_identity` asserts `B + D == |C − c*|` per step on synthetic runs, including the degenerate
cases (C at a band edge, C outside the band on the oracle's side, C outside on the far side, hw = 0).

**D_t is defined as the remainder, not as an independent distance.** That is the only definition under which the
identity holds for every C, and it is stated here before either term is measured. Its sign is non-negative wherever
the oracle target lies inside the band, which it does by construction (`oracle_target` clips to the band); a
negative D_t at any step is a defect, and the test asserts D_t ≥ 0.

### 2.2 The floor and the ceiling (weakness 53, P0-2)

> **ceiling = the mandate-conditional oracle** (0 by construction on resolvable steps);
> **floor = the worst (largest MCR) of the trivial policies** {always_hold, always_buy, always_sell, random,
> constant band edges}.
> **The sign is handled in one function**, `evaluation.scoring.normalise_metric`, which takes the metric's
> `higher_is_better` flag from one table and is the only place in the codebase that decides an orientation.

The v2 convention (ceiling = constant-mix, floor = worst of {always_buy, always_sell, random}) is kept behind
`floors_and_ceilings(convention="v2")` and is proved inert when off. The pilot's `norm_mcr` is recomputed under the
new convention **with the old value beside it** in `PILOT_NOTES.md` and in the report.

### 2.3 The pre-registered alternative: per-window scoring (REG-12 B)

25-day windows (the pilot's `probe_every`). Within each window the oracle's target is the **modal** target over the
window's resolvable steps (ties → the earlier target); regret is the mean |C_t − c*_window| over the window's
resolvable steps; the run's score is the mean over windows with at least one resolvable step. G3's switch count is
re-stated as **switches between window targets**. Built, run and reported at the same θ grid as A.

### 2.4 Adoption

**The adoption rule is E7.8's (Section 4 below) and nothing else.** 16A is re-computed under whatever scoring the
rule adopts, **as a reported consequence, labelled as such, beside the Phase-6 verdict, with the same seeds and the
same intervals — never as a replacement for it.** No scoring is chosen because of what it does to a gate
(hard rule 2).

---

## 3. E7.3 — bands against the environment's own risk and return

### 3.1 The Merton table

Merton (1969/1971) single-risky-asset CRRA share **w\* = (μ − r) / (γ σ²)**, cash share = 1 − w\*, clipped to [0, 1]
and reported unclipped beside.

**Inputs, by file, all from the frozen v2.1 state — no v2 number, and no "≈ 28 %":**

| input | source | note |
|---|---|---|
| μ | **computed on the frozen generator** as the annualised mean total log return with **dividends paid** (E7.4), over the flat scenario at the registered seed count, with a cluster-bootstrap interval over paths | the v2 "price-only drift 6.5 %/yr" is **not** used; the value-process drift is `envs/v2/params/value.json` |
| σ | **computed on the same paths** as the annualised sd of daily total log returns, with its interval | the v2 "≈ 28 %" is superseded and reported as superseded |
| r | 0 — the environment has no interest on cash (`simulation/portfolio_v2`: cash does not accrue). Stated as a property of the environment, not an assumption | |
| γ | {2, 3, 4, 6, 8, 10} — the plan's grid | |

The generator's own (μ, σ) are computed by **one tool** (`tools/phase7/e7_3_merton.py`) that also computes the
practitioner-band comparison, so the table and the bands it is compared with come from one construction (rule 12).

### 3.2 The practitioner bands and the two readings

Reading A (scored default, D9): the v2 cash bands 0.70–0.90 / 0.40–0.60 / 0.00–0.20, from the read practitioner
pages (Morningstar 15–30 / 30–50 / 50–70 / 70–85 / 85+ % equity; Fidelity Conservative 20 % equity, Balanced 50 %,
Growth 70 %, Aggressive Growth 85 %; Vanguard conservative 40/60; Betterment conservative 4–7 pp below recommended).
Reading B: the Merton cash shares at each γ. Reported: where each persona's band sits relative to the Merton row,
and the consequences for band-MAS and for the mandate oracle (which band edge the oracle rests at, per scenario).

### 3.3 The JFE ordering check

`evaluation/targets.JFE_SPREAD = (0.06, 0.12)` at line 35 is **not used and not run** until the spread is re-derived
from **Jiang, Peng & Yan (2024, JFE) Table 7** in `PHASE_7_REPORT.md`. Table 7 gives trait coefficients on the
equity-to-wealth ratio (Neuroticism −1.74, Openness +0.94, Conscientiousness −1.32) and **states no
conservative-minus-aggressive spread**. **Pre-registered rule:** if a spread can be derived from the table's own
coefficients and a stated persona-to-trait mapping, it replaces the constant and the ordering check runs; **if it
cannot, the constant and the check are removed**, `targets.py:35` records why, and the removal is a reported result.
No number from a source that was not read enters this; Donohue & Yip (2003) stays unverified and unused.

---

## 4. E7.8 — construct validity, and the rule that adopts a scoring

### 4.1 The scripted sweeps

Three scripted policies, each with one swept parameter, run on the same paths as the 16A panel (4 scenarios ×
the scored seeds × 3 personas), every one a deterministic function of a seeded RNG:

| policy | swept parameter | target metric | pre-registered direction |
|---|---|---|---|
| **drift** — the allocation walks away from the band centre at rate `d` per day | d ∈ {0.000, 0.002, 0.005, 0.010, 0.020, 0.040} | **band-MAS** | increasing in d |
| **align** — with probability `p` the policy moves to the oracle's band edge, else to the opposite edge | p ∈ {0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0} | **the directional term D** | decreasing in p |
| **panic** — on a drawdown deeper than a threshold the policy jumps to full cash with intensity `k` | k ∈ {0.0, 0.25, 0.5, 0.75, 1.0} | **drawdown (mdd_pct)** | monotone in k |

**Monotone** means: the sequence of cell means is monotone in the swept parameter with no reversal outside its
bootstrap interval (a reversal inside the interval is reported and does not by itself fail the sweep; the report
names every such case).

### 4.2 The correlation matrix and its ceiling — one tool, one construction (rule 12, P6-7)

The matrix: |r| among {band-MAS, B, D, MCR, return_pct, mdd_pct, turnover} across cells (a cell = scenario ×
persona × policy), with the pre-registered statement of which pairs are collinear **by construction**: (B, band-MAS)
— B is band-MAS restricted to resolvable steps; (B, MCR) and (D, MCR) — MCR is their sum; (turnover, cost_paid).

**The ceiling for |corr(MCR, band-MAS)|** is derived by the **same tool** that computes the matrix:

> hold the directional probability fixed at p = 0.5 and vary **only** the drift rate d over its sweep; the |r|
> between MCR and band-MAS across those cells is the **collinearity floor** — the correlation that exists because
> both metrics read the same allocation, with no directional variation at all. The **ceiling is that floor plus the
> half-width of its own cluster-bootstrap 95 % interval** (over cells, ≥ 48 cells, 500 resamples).

### 4.3 The adoption rule (REG-12, unchanged, written before any number is read)

> Adopt the scoring under which **(i)** every scripted sweep is monotone in its target metric, **and (ii)**
> |corr(MCR, band-MAS)| across cells is **below the ceiling** of 4.2. **(iii)** The oracle switch count under the
> scoring is reported either way.
> **If both A (the decomposition) and B (per-window) qualify → A**, for comparability with the pilot.
> **If neither qualifies → no scoring is adopted**; the report shows both matrices and both sweep tables, and D8 is
> put to the team.

---

## 5. E7.4 — dividends (D10: paid)

Quarterly DPS from the Phase-5 FIT process, paid into **cash** on ex-dates. Built as
`PortfolioV2(dividends=True)`; `dividends=False` is the default and is the current behaviour bit for bit.

`test_dividends_paid`: over a path with a known DPS series and no trading, the terminal cash equals the initial cash
plus Σ (DPS_q × shares held on the ex-date), and the **portfolio-value identity** holds at every step —
`total_value_t = cash_t + Σ q_i P_{i,t}` with cash incremented exactly by the dividend on ex-dates and by nothing
else. The effect on **every baseline** (return, MDD, turnover, cost, MCR, band-MAS) is reported with and without.

**`envs/` is not changed.** The DPS process and the ex-date calendar are read from the generator's existing output;
if the ex-dates are not recoverable from the environment's frame without an `envs/` change, that is a finding and
is reported as one rather than worked around.

---

## 6. E7.5 — the day-1 gate (weakness 54, P0-3)

The gate is computed on the **common-start design only** (`Start_Design == "common"`), on **C_1 levels** — KW,
Cliff's δ, band-hit and AUC, the existing `evaluation.salience.separability_gate`. **The ΔC_1 version under
start-at-target is removed**, with the reason recorded in the code and in the report: under start-at-target every
persona begins at its own centre, so ΔC_1 ≈ 0 for a persona-consistent agent and a level/band-membership test on it
is ill-posed.

**The null**, pre-registered: the **O3 numerical-only arm** and the **no-persona trader** — the two arms in which no
persona text is shown. The gate's statistic is computed on them by the same function and the same seeds; the gate's
verdict is the observed statistic against that null, not against a stipulated threshold. **If neither arm exists in
the available runs at the common-start design, the gate is reported as not computable on the pilot, with the run
counts** — that is a result, not a reason to substitute a different null.

`test_gate_common_start_only`: a frame containing both designs yields a gate table for the common-start rows only,
and no `exploratory_deltaC1_start_at_target` key.

---

## 7. E7.6 — baselines on the run's own path (weakness 56)

`tools/report_v2.cell_baselines` is rebuilt from the run's `meta.json` — `env_metadata.gen_config`, `engine`,
`n_assets`, `b_pred`, `ordering`, `start_price`, and every field hashed into `Gen_Config_Hash` — instead of from the
seven run-CSV columns it uses now.

**`test_baselines_same_path_hash`: the baseline's path hash equals the run's.**

**First, on the pilot, before any pilot number moves** (the prompt's item 8): the pilot's 52 runs were made on the
**v2** generator (`env_metadata.env_version = "v2"`, `engine = "fw_single"`, σ_V 0.006, the 150-day-calm φ, GARCH
α 0.1 / sbar 0.017). Every v2.1 change is a switch with v2 behind it, so a v2 path is *supposed* to regenerate from
its `gen_config` under the v2 switches. **The test is exactly whether it does.**

> **Pre-registered consequence.** If the hash matches: the baselines are rebuilt on the run's own path and the pilot
> is re-scored in full. **If it does not match: the pilot is re-scored on its logged columns only** (the CSV's own
> `Cash_Share`, `x`, `Price`, `Portfolio_Value` …, which are the agent's realised path whatever the generator does
> today), **the baselines are rebuilt only for the cells whose hash matches**, and the report says which cells are
> which, with counts. No pilot number is published from a path that does not reproduce.

---

## 8. E7.7 — the small items

- **Trader band consistency** (`test_trader_band_free`): the no-mandate trader's band is (0, 1) in **every** place
  that computes one — `targets.band`, `metrics_v2.oracle_target`, `baselines_v2.baseline_policies`,
  `observables_oracle.policy` — and `CATEGORY_OF_PERSONA` no longer maps `TRADER`/`NONE` to `balanced` for band
  purposes. The point-target and centre behaviour for those two labels is unchanged (0.5), and the test asserts it.
- **Pre- and post-trade cash share logged** (weakness 60): `_execute` already returns `cash_share_before` and
  `cash_share_after`; under `execution="next_open"` the run log records **both**, so the logged share is no longer
  ambiguous between the pre-trade and post-trade value. The run-CSV columns `Cash_Share_Pre` and `Cash_Share_Post`
  are added; `Cash_Share` keeps its current meaning and its current values (inert).
- **The cost statement**: 5 bp is charged **per trade** on |traded value| ⇒ **10 bp round trip**. The concept the
  anchor represents is named in the report: Nasdaq (2024) 4.5 bp is a **quoted spread**, Frazzini–Israel–Moskowitz
  (2018) 6.18 bp (median; mean 9.97) is **market impact**. The implemented 5 bp per side is labelled with which of
  the two it stands for, and the DESIGN label carries the sensitivity.
- **The dead band (1 point) and the half-width (0.10) are labelled DESIGN** — the Donohue–Yip (2003) anchor could
  not be read and is not cited. The half-width sensitivity **{0.05, 0.10, 0.15}** is run on the re-score.
- **Placebo length matching is tested, not asserted** (weakness 60): the placebo directive's token length against
  the real directive's, as a two-sample test with its n, on the pilot's prompt records.

---

## 9. The switch list — every change with the current behaviour behind it, proved inert when off

| switch | default (= current behaviour) | new behaviour | inertness test |
|---|---|---|---|
| `metrics_v2.score_run(scoring=...)` | `"v2"` | `"v2_1"` adds B, D, per-window and the derived-θ columns | `score_run(df, p, scoring="v2")` returns the v2 dict **bit for bit** on the pilot's 52 runs |
| `metrics_v2.floors_and_ceilings(convention=...)` | `"v2"` | `"v2_1"` (ceiling = mandate oracle, floor = worst trivial) | the v2 convention's output unchanged on the pilot's cells |
| `metrics_v2.THETAS` | the module constant `(0.03, 0.05, 0.08)` | read from `evaluation/params/scoring.json` when a θ is in force | with no `theta_in_force` block, the constant is unchanged |
| `PortfolioV2(dividends=...)` | `False` | `True` pays DPS into cash on ex-dates | every baseline's metrics identical with `dividends=False` |
| `PortfolioV2(log_pre_post=...)` | `False` | `True` adds the two columns | the existing columns and values unchanged |
| `report_v2.cell_baselines(from_meta=...)` | `False` (the seven-column path) | `True` rebuilds from `meta.json` | identical baselines where the two agree; the hash test where they do not |
| `evaluation/params/scoring.json` | absent ⇒ `scoring.PRESENT is False` | present ⇒ the loud loader serves it | with the file absent every consumer keeps its v2 constant |

**The path-hash fixture is not a switch**: the 95 configurations must be byte-identical, and are checked at the end.

---

## 10. Parameter-file discipline (P6-12, P4-45, rule 11)

`evaluation/params/scoring.json` carries, for every block, `value`, `label`, `source`, `date`, `interval`, `n` and a
declared `status` from a `_status_key` vocabulary — the criteria file's pattern, with a loud loader
`evaluation/scoring_params.py` that raises on a missing block, an undeclared status, or a null interval, n or date.

**`test_theta_in_force_with_provenance` reads the file back and asserts that every registered field is in it —
and it runs before the first table is read under it.** Phase 6's criteria-file writer dropped the per-statistic
overrides and a descriptive flag and the first table was read under the defect; this is the test that prevents it.

Every number in this phase's report comes from a state whose hash is recorded (P4-19): the θ file's SHA-256 and the
scoring switch in force are printed by every tool and stored in each result's `meta` block.

---

## 11. Stated expectations (so that disconfirmation is visible)

1. θ_info is **reached near θ = 0.05 on pooled rows** and **not reached on calm rows at any θ** (Phase 6's
   measurement; REG-11's stated failure mode).
2. θ_cost at the implemented 5 bp tier is **far below the smallest grid θ** and does **not** discriminate; the band
   width cancels and every persona gets the same value.
3. θ_var ≈ 0.046 sits **between** the grid's 0.03 and 0.05.
4. The pilot's paths **do not** regenerate under the v2.1 switches (the pilot ran on the v2 engine `fw_single`
   with v2 parameters; the v2.1 generator reads FIT parameter files). If they do regenerate, that is a stronger
   result than expected and is reported as such.
5. G3's θ profile (PASS at 0.03–0.05, FAIL at ≥ 0.08) is confirmed on the re-score and is what D8 is asked about.
6. **At least one rule here will be undecidable or come out the wrong way** — seven phases in a row have had one.
   The addendum is part of the deliverable.

---

## 12. What this phase does not do

- It does not empty the known-defect registry. The two entries are the derived L2 and L2b gates; **no re-scoring
  passes them** and none is attempted.
- It does not decide the all-rows L2 centred reading (undecided at 40 draws; decidable only on a larger panel —
  the team is asked whether it wants the compute spent).
- It does not touch `envs/`, `agent/`, or the plan, the alternatives register, or `docs/env_v2/v2_1/archive/`.
- It makes no API call and does not pre-empt D2, D3 or D5.
