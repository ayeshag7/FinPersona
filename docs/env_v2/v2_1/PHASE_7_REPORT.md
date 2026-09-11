# Phase 7 report — targets, action and metrics: θ derived, regret decomposed, bands checked (v2.1)

*Written as results land (execution prompt, "Documentation"); every number cites the file it comes from; the tables
marked `<!-- table:... -->` are generated from those files by `tools/phase7/e7_report_tables.py` and read back by
`tests/test_v2_1_phase_7.py::test_phase7_report_tables_match_files`. Sections follow the protocol's six headings.*

**Status: COMPLETE (10 September 2026).** Every experiment of the execution prompt ran, on the laptop. The team
recorded **D17 = restrict the claim**, **D10 = pay dividends**, **D9 = practitioner bands as the scored default**,
**D7 = co-primary as registered** and **D8 = the θ-conditional pass** (DECISION_LOG P7-1 … P7-5); the gated
experiments ran after D17, and the θ in force was written to the parameter file only after D7 and D8.

**The three results that matter.** (1) **θ_info = 0.05 on pooled rows** — the level-free observables surrogate's
sign accuracy crosses 0.80 exactly there — and **0.20 on calm rows**, where 0.9 % of calm steps survive; **θ_cost =
0.0020** for every persona, because the band width cancels, and the implemented cost tier would have to be 25×
higher to reach 0.05. (2) **The decomposition rescues nothing**: 16A's G1, G2 and G4a fail 0 of 4 on MCR, on B, on
D and under per-window scoring alike, so no scoring this phase could adopt flips a checkpoint. (3) **None of the
pilot's 52 paths regenerates** — the engine it ran on was rejected by Phase 2's SMM and no longer exists — so the
pilot is re-scored on its logged columns only and no pilot baseline is rebuilt.

---

## 0. Current state, and how to read this report

| item | status |
|---|---|
| Pre-registration | `PREREG_PHASE_7.md`, written before the first re-score, with the three θ formulas and their file inputs, the decomposition, E7.8's adoption rule and its ceiling's construction, the Merton inputs, the gate's null and the switch list. `PREREG_PHASE_7_ADDENDUM.md` carries **nine** items: θ_info reached on calm rows (expectation disconfirmed), the ceiling family the registered construction needed, two unregistered sensitivities, the `align` reference θ, `runs.csv` without allocations, E7.6's stronger-than-expected outcome, G3 under per-window scoring, the pilot note's prose, and the ceiling that is 0.0028 rather than 0 |
| Team decisions | **D17 = restrict the claim** (P7-1); **D10 = pay dividends** (P7-2); **D9 = A the scored default, B reported** (P7-3); **D7 = co-primary as registered** (P7-4); **D8 = the θ-conditional pass** (P7-5). D2 and D15 remain open and are not this phase's |
| E7.1a θ_info | **done** — the audit's own GBT refit to store per-row predictions, verified against the four published Phase-6 sign accuracies at **diff 0.0** before anything read it (`e7_1/verify.json`); 1,600 paths, 288,000 rows, 84 s |
| E7.1b θ_cost | **done** — 0.0020 = 4c for every persona; the band width cancels algebraically **and numerically** (spread 1.8 × 10⁻⁶ across w ∈ {0.10, 0.20, 0.40}; worst relative error 0.14 % against the real `PortfolioV2`). **Also tested as a policy rule** (section 3.2b, added after the first draft): acting at θ_cost gives the highest net return despite the most trades and the largest cost drag |
| E7.1c θ_var | **done** — 0.046321, read from the checklist file, inside the AR(1) reference band [0.0389, 0.0724] |
| E7.1 re-score | **done** — 1,620,000 cell-rows: 4 scenarios × 100 seeds × 3 personas × **50 policies** × 9 θ × 3 half-widths, under both scorings (`e7_rescore/cells.parquet`) |
| E7.2 decomposition | **done** — MCR = B + D identically (asserted per step, including every degenerate placement); the floor and ceiling re-specified with the sign in one function; the v2 convention kept behind its switch and proved inert |
| E7.3 bands | **done** — the environment's own σ is **34.7 %/yr**, not the v2 documents' "≈ 28 %"; the Merton cash shares at γ ∈ {2 … 10} are 0.64–0.93 and **no γ in the grid lands in the balanced or the aggressive band**; the JFE ordering check **removed**, its constant withdrawn |
| E7.4 dividends | **done** — paid on the generator's own announcement days (the only ex-dates recoverable without an `envs/` change); realised yield 3.42 %/yr, payer share 0.908; the price path is **not** ex-dividend adjusted and every dividend number carries that sentence |
| E7.5 day-1 gate | **done** — common-start only, on C₁ levels; the ΔC₁ table **removed**; the null named, and reported **NOT COMPUTABLE** on the pilot, which has no no-persona arm at common start |
| E7.6 baselines | **done** — 0 of 52 pilot environments are even constructible under the recorded engine; `cell_baselines(from_meta=True)` built and tested on a cell the seven run-CSV columns cannot express |
| E7.7 small items | **done** — the trader band-free everywhere, pre/post-trade shares logged, the cost concept named, the half-width and dead band labelled DESIGN with the {0.05, 0.10, 0.15} sensitivity run, the placebo length **measured** (ratio 0.96–1.01) rather than asserted |
| E7.8 validity | **done** — all three sweeps monotone under both scorings, 0 reversals; |r|(MCR, band-MAS) 0.9758 below its 0.9950 ceiling; **scoring A adopted** by REG-12's tie-break — and the absolute correlation of 0.98 reported as the collinearity it is. **The adoption re-checked at every θ and half-width** (section 3.11b): A in 27 of 27, worst margin +0.0024 |
| 16A re-stated | **done** — beside the Phase-6 verdict, never in place of it; G1, G2, G4a fail 0 of 4 under **every** statistic. **The half-width sensitivity applied to the gates** (section 3.12b): G1 and G4a fail in all 27 × 4 slices; G2's ordering appears in 9, all at half-width 0.05 and none on MCR — reported as a diagnostic, not a pass |
| The switches | **written and proved inert** — seven switches, each with the v2 behaviour behind it (section 3.14) |
| Path hashes | **unchanged** — this phase changes no path; the 95-configuration fixture is byte-identical to Phase 5's and Phase 6's (section 3.16) |
| The whole test tree | **run twice (rule 10).** First run (65 min): 190 passed, 1 skipped, 4 strict xfails, **1 failed** — a Phase-0 test asserting the day-1-gate contract Phase 7 deliberately replaced; updated to the replacing contract, not weakened (section 3.14b, P7-16). Confirmation run after that edit (60 min): **191 passed, 1 skipped, 4 strict xfails, 0 failed** |
| Compute | **the laptop for every number in this report.** The box answered at the start of the session (128 cores, 2 × RTX 4090 idle, sklearn 1.9.0 / numpy 2.4.6 matching), and was **not used**: see section 6 |

---

## 1. Literature review and the citation table

Every source below was read for this phase or carried forward from a phase that read it. **No number from a source
that was not read appears anywhere in this report, in `evaluation/params/scoring.json`, or in a test tolerance.**

| source | statistic used | status | where it enters |
|---|---|---|---|
| Merton (1969 RES; 1971 JET) | the single-risky-asset CRRA share w\* = (μ − r)/(γσ²) | **read, correct** | E7.3's table — the *formula* only; μ and σ are this environment's own, measured here |
| Nasdaq (2024), *US Equity Market Structure* | 4.5 bp cap-weighted **quoted spread** of the S&P 500 basket | **read, correct** | E7.7's cost statement, named as a *quoted spread* (a half-spread of ≈ 2.25 bp per side) — **not** the source of the implemented 5 bp |
| Frazzini, Israel & Moskowitz (2018 draft) | median **market impact** 6.18 bp per trade (mean 9.97) | **read, correct** | E7.7's cost statement, named as *market impact* — the other of the two anchors the implemented tier sits between |
| Jiang, Peng & Yan (2024, JFE) **Table 7** | trait coefficients on the equity-to-wealth ratio: Neuroticism −1.74, Openness +0.94, Conscientiousness −1.32 | **read — and it does not contain what the code claimed** | E7.3: the table states **no** conservative-minus-aggressive spread, so `targets.JFE_SPREAD = (0.06, 0.12)` is withdrawn and the ordering check removed (P7-6) |
| Fieberg, Hornuf, Meiler & Streich (2025, CESifo WP 11666) | LLM average equity share 67 % vs robo-advisers 59 % | **read, correct** | context for E7.3's band placement; no parameter takes a value from it |
| Morningstar / Fidelity / Vanguard / Betterment practitioner pages | equity bands 15–30 / 30–50 / 50–70 / 70–85 / 85+ %; Fidelity Conservative 20 %, Balanced 50 %, Growth 70 %, Aggressive Growth 85 %; Vanguard conservative 40/60; Betterment conservative 4–7 pp below recommended | **read, correct** | the source of reading A's cash bands, now recorded in `evaluation/targets.py`'s docstring |
| Sun, Fan, Chen, Schouwenaars & Albota (2006, JPM) | 40–60 bp costs and a 5 % tolerance band in their worked examples | **read, correct** | cited as *context* for the half-width, explicitly **not** as its source (different instrument, different cost tier) |
| Donohue & Yip (2003, JPM 29(4)) | rebalancing bands at a 5 bp cost tier | **not retrievable** (text inaccessible; unchanged since the plan) | **nothing.** The half-width and the dead band are labelled DESIGN with a sensitivity precisely because this could not be read; the "2–5-point bands" attribution is not used |

The two cost anchors are **different cost concepts**, and the implemented 5 bp per trade is neither of them: it is a
DESIGN choice that sits between a 2.25 bp half-spread and a 6.18 bp median market impact, labelled as such in
`evaluation/params/scoring.json` (`cost_tier`).

---

## 2. Pre-registration, verification of the inherited numbers, and corrections

**The pre-registration was written before the first re-score** and carries every rule in final form. Three things
were verified before anything downstream could read them:

1. **The θ_info surrogate is the audit's, not a lookalike.** The refit reproduces all four published Phase-6 sign
   accuracies — full 0.800484 / 0.684893 / 0.890616 / 0.763859 and the price-only control 0.784197 / 0.645903 /
   0.896250 / 0.734146 — at **|difference| = 0.0**, against a pre-registered tolerance of 1e-12. Had it not, the
   phase would have stopped at E7.1a (`e7_1/verify.json`).
2. **The regenerated panel is Phase 6's own.** `e7_panel/verify_vs_16a.json`: worst |difference| **9.98 × 10⁻¹⁷**
   over 51,450 MCR comparisons against `e6_16a/runs.csv`. The same holds at the level of the *published table*:
   at θ = 0.05 on flat paths this phase reads oracle 0.0027, observables oracle 0.0770, price-only oracle 0.0745,
   best rule 0.0541, band-high 0.0874, always-hold 0.1118 — every one identical to `e6_16a/16A.md` to four
   decimals, which is the whole panel-and-re-scoring chain checked against a number a human read.
3. **The parameter file is read back through its loud loader before the first table under it**, and
   `test_theta_in_force_with_provenance` asserts every registered field is in it (P6-12's lesson).

**Corrections to inherited numbers, made here:**

- `evaluation/targets.JFE_SPREAD` — **withdrawn**; not derivable from the source (P7-6).
- The environment's "annual σ ≈ 28 %" and "price-only drift 6.5 %/yr" — **superseded** by 0.3468 and 0.0548 on the
  frozen generator (E7.3).
- `evaluation/targets.band("TRADER" | "NONE")` returned the balanced band while four consumers hard-coded (0, 1) —
  **fixed**, one definition (P7-11).
- `PortfolioV2.retarget(execution="next_open")` returned the **pre**-trade share under the name
  `cash_share_after` — **fixed**; both keys now carry the pre-trade value with `pending: True` beside (weakness 60).
- `PILOT_NOTES.md`'s prose MCR figures for three cells disagree with the table they were written from —
  **corrected** (P7-14; addendum 7).

### Amendments to the plan, recorded here rather than by editing it

The plan, `V2_1_ALTERNATIVES_REGISTER.md` and everything under `docs/env_v2/v2_1/archive/` are **untouched**
(`git status` on all three is empty). The four amendments this phase makes to what the plan says are recorded
here, as the execution prompt requires:

| plan text | amendment |
|---|---|
| 11.2 E7.1: "θ_info = the \|x\| at which the level-free observables surrogate reaches sign accuracy 0.80 … (review C measured 0.71 on resolvable steps); if the surrogate never reaches 0.80, θ_info is reported as 'not reached'" | **θ_info is reached on both populations** — 0.05 pooled, 0.20 on calm rows. The failure mode the plan and REG-11 wrote for does not arise; what arises instead is a crossing at 0.9 % coverage on the calm population, which D7 answered by keeping the co-primary rule and reporting the calm value with its n (P7-4; addendum 1) |
| 11.2 E7.1: "θ_cost … depends on h and on the persona's band width" | **Neither dependence survives the algebra**: θ_cost = 2c/f, so the band width cancels exactly and the half-life enters only through f, which is ½ by definition at the registered horizon. Every persona gets 0.0020. Verified numerically as well as algebraically (addendum 8 of `PREREG_PHASE_7.md`'s expectations; `e7_1/theta_cost_var.json`) |
| 11.2 E7.2: "ceiling = mandate-conditional oracle (0 by construction)" | **The ceiling is 0.0028, not 0.** The oracle is executed through `PortfolioV2`, so a target inside the 1-point dead band is not traded and the realised share drifts with price between trades. "0 by construction" is true of the oracle's target series, not of the trajectory MCR reads (addendum 8) |
| 11.2 E7.3: "the environment's price-only drift 6.5 %/yr, annual σ ≈ 28 % (to be recomputed after Phases 1–3)" | **Recomputed: μ 0.0548 price-only / 0.0874 with dividends, σ 0.3468.** The Merton consequence is that no γ in the plan's grid falls in the balanced or the aggressive band (section 3.6) |
| 11.1: "`targets.py`'s JFE_SPREAD (0.06, 0.12) must be re-derived from Table 7 in the phase report before it is used as the ordering check" | **It cannot be re-derived and the check is removed**, not deferred: Table 7 has trait coefficients, not a spread (P7-6) |

---

## 3. Experiments and results

### 3.1 E7.1a — θ_info, per population and per scenario

The level-free observables surrogate is `evaluation/leakage_audit`'s GBT, out-of-sample from `GroupKFold(5)` by
path, on the 1,600-path panel — the audit's construction unchanged, refit only so that the per-row predictions can
be stored, which the published audit does not carry. θ_info is the smallest grid θ at which sign accuracy on
|x| ≥ θ reaches 0.80 and stays there.

**The caveat that travels with every value below:** the derived L2 gates fail (E6.6/E6.7 — calm-trained +0.1088
against a registered margin of −0.0313, of which Phase 5's ablation puts +0.051 in the wandering multiple). θ_info
reads that same surrogate, so "what the agent can resolve" already includes the fields' calm-trained contribution.

<!-- table:e7_theta_info -->
| scope | population | feature set | theta_info | sign accuracy there | coverage | n resolvable | max accuracy (at theta) | theta_info on the interval's lower end |
|---|---|---|---|---|---|---|---|---|
| pooled | all | full | **0.05** | 0.800 [0.791, 0.810] | 0.597 | 171,916 | 0.947 (at 0.30) | 0.06 |
| pooled | all | price_only | **0.06** | 0.802 [0.793, 0.811] | 0.539 | 155,158 | 0.950 (at 0.30) | 0.08 |
| pooled | calm | full | **0.20** | 0.880 [0.804, 0.943] | 0.009 | 1,089 | 1.000 (at 0.30) | 0.20 |
| pooled | calm | price_only | **0.20** | 0.875 [0.816, 0.932] | 0.009 | 1,089 | 1.000 (at 0.30) | 0.20 |
| bull_trap | all | full | **0.01** | 0.832 [0.818, 0.848] | 0.957 | 68,932 | 0.929 (at 0.30) | 0.01 |
| bull_trap | all | price_only | **0.01** | 0.846 [0.834, 0.857] | 0.957 | 68,932 | 0.936 (at 0.30) | 0.01 |
| bull_trap | calm | full | **0.15** | 0.850 [0.700, 0.979] | 0.021 | 246 | 0.938 (at 0.20) | 0.20 |
| bull_trap | calm | price_only | **0.15** | 0.858 [0.708, 0.971] | 0.021 | 246 | 0.938 (at 0.20) | 0.20 |
| crash | all | full | **0.05** | 0.801 [0.791, 0.811] | 0.611 | 87,956 | 0.990 (at 0.30) | 0.06 |
| crash | all | price_only | **0.08** | 0.811 [0.802, 0.820] | 0.451 | 64,880 | 0.984 (at 0.30) | 0.08 |
| crash | calm | full | **0.08** | 0.823 [0.784, 0.859] | 0.166 | 5,914 | 1.000 (at 0.20) | 0.10 |
| crash | calm | price_only | **0.12** | 0.816 [0.776, 0.853] | 0.052 | 1,870 | 1.000 (at 0.25) | 0.15 |
| flat | all | full | **0.20** | 0.905 [0.824, 0.970] | 0.010 | 347 | 1.000 (at 0.25) | 0.20 |
| flat | all | price_only | **0.15** | 0.813 [0.740, 0.878] | 0.029 | 1,055 | 1.000 (at 0.25) | 0.20 |
| flat | calm | full | **0.20** | 0.905 [0.824, 0.970] | 0.010 | 347 | 1.000 (at 0.25) | 0.20 |
| flat | calm | price_only | **0.15** | 0.813 [0.740, 0.878] | 0.029 | 1,055 | 1.000 (at 0.25) | 0.20 |
| sustained_bull | all | full | **0.25** | 0.901 [0.687, 1.000] | 0.004 | 131 | 1.000 (at 0.30) | 0.30 |
| sustained_bull | all | price_only | **0.25** | 0.924 [0.779, 1.000] | 0.004 | 131 | 1.000 (at 0.30) | 0.30 |
| sustained_bull | calm | full | **0.25** | 0.901 [0.687, 1.000] | 0.004 | 131 | 1.000 (at 0.30) | 0.30 |
| sustained_bull | calm | price_only | **0.25** | 0.924 [0.779, 1.000] | 0.004 | 131 | 1.000 (at 0.30) | 0.30 |

The pooled curve, both feature sets (the level-free observables surrogate and its level-free price-only control):

| theta | coverage | sign accuracy, all rows | sign accuracy, calm rows | n resolvable (all / calm) |
|---|---|---|---|---|
| 0.01 | 0.911 | 0.727 [0.718, 0.737] | 0.629 [0.613, 0.645] | 262,395 / 102,149 |
| 0.02 | 0.822 | 0.747 [0.737, 0.757] | 0.647 [0.630, 0.665] | 236,845 / 84,854 |
| 0.03 | 0.743 | 0.766 [0.756, 0.776] | 0.663 [0.644, 0.681] | 213,850 / 69,874 |
| 0.04 | 0.666 | 0.783 [0.773, 0.793] | 0.674 [0.654, 0.695] | 191,802 / 55,579 |
| 0.05 | 0.597 | 0.800 [0.791, 0.810] | 0.685 [0.664, 0.707] | 171,916 / 43,344 |
| 0.06 | 0.539 | 0.817 [0.808, 0.828] | 0.698 [0.675, 0.722] | 155,158 / 33,839 |
| 0.08 | 0.445 | 0.842 [0.833, 0.852] | 0.704 [0.675, 0.733] | 128,183 / 20,216 |
| 0.10 | 0.374 | 0.864 [0.854, 0.875] | 0.713 [0.679, 0.748] | 107,665 / 11,407 |
| 0.12 | 0.321 | 0.883 [0.873, 0.893] | 0.731 [0.692, 0.775] | 92,585 / 6,751 |
| 0.15 | 0.262 | 0.904 [0.894, 0.915] | 0.788 [0.738, 0.841] | 75,576 / 3,352 |
| 0.20 | 0.194 | 0.923 [0.912, 0.933] | 0.880 [0.804, 0.943] | 55,953 / 1,089 |
| 0.25 | 0.144 | 0.937 [0.926, 0.947] | 0.962 [0.897, 1.000] | 41,460 / 365 |
| 0.30 | 0.101 | 0.947 [0.936, 0.958] | 1.000 [1.000, 1.000] | 29,142 / 136 |
<!-- /table:e7_theta_info -->

**How to read the per-scenario rows.** The pooled rows are the usable ones. Several per-scenario cells locate
θ_info where almost nothing is left to measure — flat at 0.20 on **347** rows, sustained-bull at 0.25 on **131**,
bull-trap calm at 0.15 on **246** — and a threshold located on a few hundred rows is a number, not evidence. They
are published with their n so that they can be read as what they are; **only the pooled values enter the parameter
file.** One further caveat: these per-scenario accuracies are the *pooled* surrogate's predictions restricted to a
scenario's rows, not a surrogate trained without that scenario. The held-out-scenario split (P6-14) says those are
different things, and the second was not computed here (section 7).

Two readings of the registered locator exist where a larger grid point has no measurable accuracy; they differ on
**bull-trap calm only** (0.15 versus not reached, decided by two rows at θ = 0.30) and on no other cell. Both are
computed and stored; neither co-primary value moves. See `PREREG_PHASE_7_ADDENDUM.md` section 10.

**Reading.** On pooled rows the crossing is at **θ = 0.05**, exactly where Phase 6 measured 0.800 — the registered
expectation, confirmed. On calm rows it is at **θ = 0.20**, and the registered expectation ("not reached at any θ")
is **wrong**: it is reached, on 1,089 of 119,336 calm rows, with 0.9 % of calm steps scored. The two feature sets
are close everywhere — the level-free price-only control crosses at 0.06 pooled and 0.20 on calm rows — which is
G4a's failure seen from the θ side: the fields buy about one grid step of resolvability, not a different regime.

### 3.2 E7.1b / E7.1c — θ_cost and θ_var

<!-- table:e7_theta_cost -->
| quantity | value | source |
|---|---|---|
| cost rate c (5.0 bp per trade) | 0.000500 | `simulation/runner_v2.py` `RunConfig.cost_bp`; charged on \|traded value\| per trade by `simulation/portfolio_v2.py` |
| FIT half-life h | 22.3809 d [18.75, 32.64] | `envs/v2/params/mispricing.json` `half_life.value` (n = 417) |
| band width w (every persona) | 0.20 | `evaluation/targets.py` `BANDS` — **cancels** |
| f, one half-life (primary) | 0.5000 | by definition of the half-life |
| **theta_cost = 2c/f = 4c** | **0.002000** | the same for every persona |

| horizon | f | theta_cost |
|---|---|---|
| one half-life — **primary** | 0.5000 | **0.002000** |
| one day | 0.0305 | 0.032791 |
| one day at h = 18.75 | 0.0363 | 0.027553 |
| one day at h = 32.64 | 0.0210 | 0.047590 |
| infinite | 1.0000 | 0.001000 |

The closed form checked numerically against the real `PortfolioV2` at three band widths:

| band width | closed form at the discrete horizon | numeric break-even | relative error |
|---|---|---|---|
| 0.10 | 0.002024 | 0.002027 | 0.14% |
| 0.20 | 0.002024 | 0.002026 | 0.08% |
| 0.40 | 0.002024 | 0.002025 | 0.05% |

Spread of the numeric break-even across band widths **1.83e-06** — w cancels as a measurement, not only algebraically. Worst relative error **0.14%**, within the pre-registered 10 %.

What cost tier would put theta_cost on the grid:

| grid theta | bp per trade required | multiple of the implemented tier |
|---|---|---|
| 0.03 | 75 | 15× |
| 0.05 | 125 | 25× |
| 0.08 | 200 | 40× |
| 0.12 | 300 | 60× |
| 0.20 | 500 | 100× |

**theta_var = 0.046321** — the generator's median 200-day sd(x) on flat paths (n = 500 seeds), inside the AR(1) reference band [0.03892, 0.07235] at the FIT half-life. Sensitivity: the stationary s_x = 0.065609.
<!-- /table:e7_theta_cost -->

**Reading.** θ_cost is **0.0020 for every persona**, and that is a property of the registered formula, written
before the value was computed: the expected profit of a full reallocation is w·f·x and the round trip costs 2·c·w,
so w cancels and θ_cost = 2c/f. At the implemented 5 bp tier the cost does not bind — coverage at θ_cost is 0.97,
so nearly every step is "worth trading on". A tier **25× higher** (125 bp per trade) would be needed to put
θ_cost at 0.05. This is REG-11 option B producing a non-discriminating threshold, and it is reported as such
rather than replaced.

The horizon is where the half-life enters: at a **one-day** holding horizon f₁ = 1 − 2^(−1/h) = 0.0305 and
θ_cost = 0.0328, inside the plan's grid. That is a sensitivity, not the primary — the plan, the register and the
pre-registration all say "over one half-life".

### 3.2b E7.1b part 2 — θ_cost tested as a **policy rule**, not only as a per-decision break-even

**Why this was run.** The derivation in 3.2 charges the round trip **once**: it asks whether one full reallocation
pays for one round trip. A policy that *acts* at a low threshold pays that round trip again every time x crosses
back, and x crosses a low threshold far more often than a high one. Nothing in the phase as first written had
measured that, because **every θ-dependent policy in the panel acts at θ = 0.05** — the θ sweep changes the
yardstick, not the policy. So θ_cost, one of the two co-primary values in force, had never been tested as the thing
it is used for.

The experiment: the mandate-conditional oracle **acting** at each candidate θ, on the same paths, at the
implemented 5 bp tier and again at 0 bp. The oracle knows x exactly, which is precisely the case the derivation
assumes.

<!-- table:e7_theta_cost_policy -->
The mandate-conditional oracle **acting** at each candidate theta on 100 seeds x 4 scenarios x 3 personas, at 5.0 bp per trade and again at 0 bp. The oracle knows x exactly, which is the case theta_cost's derivation assumes. Cluster-bootstrap 95 % intervals over seeds.

| acting theta | label | net return % | gross return % (0 bp) | cost drag pp | trades per run | turnover |
|---|---|---|---|---|---|---|
| 0.002 | theta_cost | **14.075** [11.745, 16.801] | 14.229 | 0.154 | 30.0 | 2.84 |
| 0.03 | grid | **13.960** [11.445, 16.401] | 14.020 | 0.061 | 22.2 | 1.11 |
| 0.032791 | theta_cost_one_day | **14.019** [11.584, 16.775] | 14.077 | 0.058 | 21.8 | 1.07 |
| 0.046321 | theta_var | **14.029** [11.479, 16.596] | 14.075 | 0.045 | 19.7 | 0.85 |
| 0.05 | grid|theta_info_all | **13.968** [11.651, 16.698] | 14.011 | 0.043 | 19.1 | 0.81 |
| 0.065609 | theta_var_stationary | **13.870** [10.973, 16.474] | 13.904 | 0.034 | 16.5 | 0.64 |
| 0.08 | grid | **13.734** [11.113, 16.347] | 13.761 | 0.027 | 14.4 | 0.52 |
| 0.12 | grid | **13.378** [10.648, 15.911] | 13.396 | 0.019 | 10.3 | 0.34 |
| 0.2 | grid|theta_info_calm | **13.002** [10.717, 15.789] | 13.012 | 0.010 | 6.0 | 0.19 |

Derived theta_cost **0.0020**; best acting theta by net return **0.002**, by gross return 0.002. Cost drag at theta_cost 0.154 pp on 30 trades a run.
<!-- /table:e7_theta_cost_policy -->

**Reading. θ_cost survives the test.** Acting at θ = 0.0020 gives the **highest net return** (14.08 %), and it does
so while trading most often (30 trades a run against 6 at θ = 0.20) and paying the largest cost drag (0.154 pp).
The churn mechanism is real — the drag falls monotonically from 0.154 pp to 0.010 pp as the acting threshold rises
— but at 5 bp per trade it is an order of magnitude smaller than the return spread it buys, so it never overturns
the ranking. The closed form is therefore a per-decision break-even **and** the best acting threshold on this
environment, which is more than was established before.

**Two qualifications, both in the numbers above.** First, the net-return intervals overlap heavily across every θ
(θ_cost 14.08 [11.75, 16.80] against θ = 0.20's 13.00 [10.72, 15.79]), so **no pair of acting thresholds is
separated**; what is separated and monotone is the cost drag. Second, only ~30 trades a run occur at θ = 0.0020,
not hundreds, because the oracle trades only when its *target changes* and the 1-point dead band absorbs the rest —
the same dead band that makes the ceiling 0.0028 rather than 0.

### 3.3 E7.1 — every headline metric at every θ

Half-width 0.10 (the value in force); percentile cluster bootstrap over seeds, 500 resamples, the Phase-6
construction. MCR = B + D identically on resolvable steps.

<!-- table:e7_theta_table -->
| scenario | theta | label | policy | MCR | B (band violation) | D (directional) | band-MAS | MCR per window | oracle switches | coverage |
|---|---|---|---|---|---|---|---|---|---|---|
| flat | 0.002 | theta_cost | L5_full_level_free | 0.0833 [0.0775, 0.0890] | 0.0013 | 0.0820 | 0.0013 | 0.0813 | 12.25 | 0.968 |
| flat | 0.002 | theta_cost | L5_level_free | 0.0836 [0.0781, 0.0890] | 0.0011 | 0.0826 | 0.0011 | 0.0823 | 12.25 | 0.968 |
| flat | 0.002 | theta_cost | always_hold | 0.1073 [0.1054, 0.1093] | 0.0001 | 0.1072 | 0.0001 | 0.1068 | 12.25 | 0.968 |
| flat | 0.002 | theta_cost | band_hi | 0.0913 [0.0828, 0.0986] | 0.0018 | 0.0895 | 0.0018 | 0.0901 | 12.25 | 0.968 |
| flat | 0.002 | theta_cost | band_lo | 0.1121 [0.1041, 0.1197] | 0.0012 | 0.1109 | 0.0012 | 0.1131 | 12.22 | 0.968 |
| flat | 0.002 | theta_cost | mandate_conditional_oracle | 0.0451 [0.0415, 0.0492] | 0.0013 | 0.0439 | 0.0013 | 0.0409 | 12.25 | 0.968 |
| flat | 0.002 | theta_cost | rule_p_sma50 | 0.0740 [0.0690, 0.0792] | 0.0013 | 0.0727 | 0.0013 | 0.0781 | 12.23 | 0.968 |
| flat | 0.03 | grid | L5_full_level_free | 0.0781 [0.0701, 0.0868] | 0.0012 | 0.0769 | 0.0013 | 0.0797 | 3.37 | 0.546 |
| flat | 0.03 | grid | L5_level_free | 0.0768 [0.0698, 0.0838] | 0.0011 | 0.0758 | 0.0011 | 0.0804 | 3.37 | 0.546 |
| flat | 0.03 | grid | always_hold | 0.1097 [0.1073, 0.1122] | 0.0001 | 0.1095 | 0.0001 | 0.1087 | 3.37 | 0.546 |
| flat | 0.03 | grid | band_hi | 0.0885 [0.0773, 0.0987] | 0.0018 | 0.0867 | 0.0018 | 0.0921 | 3.37 | 0.546 |
| flat | 0.03 | grid | band_lo | 0.1150 [0.1040, 0.1251] | 0.0012 | 0.1138 | 0.0012 | 0.1115 | 3.07 | 0.546 |
| flat | 0.03 | grid | mandate_conditional_oracle | 0.0220 [0.0190, 0.0252] | 0.0013 | 0.0207 | 0.0013 | 0.0353 | 3.37 | 0.546 |
| flat | 0.03 | grid | rule_p_sma50 | 0.0623 [0.0551, 0.0688] | 0.0013 | 0.0610 | 0.0013 | 0.0686 | 3.27 | 0.546 |
| flat | 0.03279 | theta_cost_one_day | L5_full_level_free | 0.0780 [0.0704, 0.0873] | 0.0012 | 0.0768 | 0.0013 | 0.0803 | 3.25 | 0.511 |
| flat | 0.03279 | theta_cost_one_day | L5_level_free | 0.0764 [0.0693, 0.0828] | 0.0010 | 0.0753 | 0.0011 | 0.0795 | 3.25 | 0.511 |
| flat | 0.03279 | theta_cost_one_day | always_hold | 0.1098 [0.1067, 0.1128] | 0.0001 | 0.1096 | 0.0001 | 0.1090 | 3.25 | 0.511 |
| flat | 0.03279 | theta_cost_one_day | band_hi | 0.0881 [0.0771, 0.0991] | 0.0018 | 0.0863 | 0.0018 | 0.0924 | 3.25 | 0.511 |
| flat | 0.03279 | theta_cost_one_day | band_lo | 0.1154 [0.1042, 0.1267] | 0.0012 | 0.1142 | 0.0012 | 0.1112 | 2.94 | 0.511 |
| flat | 0.03279 | theta_cost_one_day | mandate_conditional_oracle | 0.0195 [0.0169, 0.0222] | 0.0013 | 0.0182 | 0.0013 | 0.0326 | 3.25 | 0.511 |
| flat | 0.03279 | theta_cost_one_day | rule_p_sma50 | 0.0613 [0.0549, 0.0684] | 0.0013 | 0.0601 | 0.0013 | 0.0675 | 3.14 | 0.511 |
| flat | 0.04632 | theta_var | L5_full_level_free | 0.0778 [0.0691, 0.0873] | 0.0012 | 0.0766 | 0.0013 | 0.0783 | 2.50 | 0.360 |
| flat | 0.04632 | theta_var | L5_level_free | 0.0752 [0.0674, 0.0839] | 0.0010 | 0.0742 | 0.0011 | 0.0776 | 2.50 | 0.360 |
| flat | 0.04632 | theta_var | always_hold | 0.1112 [0.1079, 0.1144] | 0.0002 | 0.1110 | 0.0001 | 0.1103 | 2.50 | 0.360 |
| flat | 0.04632 | theta_var | band_hi | 0.0879 [0.0746, 0.1007] | 0.0018 | 0.0861 | 0.0018 | 0.0923 | 2.50 | 0.360 |
| flat | 0.04632 | theta_var | band_lo | 0.1156 [0.1034, 0.1281] | 0.0012 | 0.1145 | 0.0012 | 0.1114 | 2.12 | 0.360 |
| flat | 0.04632 | theta_var | mandate_conditional_oracle | 0.0064 [0.0055, 0.0073] | 0.0012 | 0.0051 | 0.0013 | 0.0150 | 2.50 | 0.360 |
| flat | 0.04632 | theta_var | rule_p_sma50 | 0.0559 [0.0484, 0.0648] | 0.0012 | 0.0547 | 0.0013 | 0.0586 | 2.36 | 0.360 |
| flat | 0.05 | grid|theta_info_all | L5_full_level_free | 0.0770 [0.0668, 0.0876] | 0.0012 | 0.0758 | 0.0013 | 0.0787 | 2.37 | 0.328 |
| flat | 0.05 | grid|theta_info_all | L5_level_free | 0.0745 [0.0661, 0.0823] | 0.0010 | 0.0735 | 0.0011 | 0.0767 | 2.37 | 0.328 |
| flat | 0.05 | grid|theta_info_all | always_hold | 0.1118 [0.1083, 0.1153] | 0.0002 | 0.1116 | 0.0001 | 0.1106 | 2.37 | 0.328 |
| flat | 0.05 | grid|theta_info_all | band_hi | 0.0874 [0.0762, 0.0990] | 0.0018 | 0.0857 | 0.0018 | 0.0935 | 2.37 | 0.328 |
| flat | 0.05 | grid|theta_info_all | band_lo | 0.1162 [0.1035, 0.1296] | 0.0012 | 0.1150 | 0.0012 | 0.1103 | 2.00 | 0.328 |
| flat | 0.05 | grid|theta_info_all | mandate_conditional_oracle | 0.0027 [0.0026, 0.0028] | 0.0012 | 0.0015 | 0.0013 | 0.0060 | 2.37 | 0.328 |
| flat | 0.05 | grid|theta_info_all | rule_p_sma50 | 0.0541 [0.0461, 0.0626] | 0.0012 | 0.0529 | 0.0013 | 0.0566 | 2.23 | 0.328 |
| flat | 0.06561 | theta_var_stationary | L5_full_level_free | 0.0778 [0.0669, 0.0895] | 0.0012 | 0.0766 | 0.0013 | 0.0804 | 1.76 | 0.213 |
| flat | 0.06561 | theta_var_stationary | L5_level_free | 0.0756 [0.0645, 0.0858] | 0.0010 | 0.0747 | 0.0011 | 0.0793 | 1.76 | 0.213 |
| flat | 0.06561 | theta_var_stationary | always_hold | 0.1128 [0.1082, 0.1168] | 0.0002 | 0.1126 | 0.0001 | 0.1115 | 1.76 | 0.213 |
| flat | 0.06561 | theta_var_stationary | band_hi | 0.0935 [0.0792, 0.1080] | 0.0018 | 0.0916 | 0.0018 | 0.0959 | 1.76 | 0.213 |
| flat | 0.06561 | theta_var_stationary | band_lo | 0.1102 [0.0968, 0.1264] | 0.0012 | 0.1090 | 0.0012 | 0.1079 | 1.36 | 0.213 |
| flat | 0.06561 | theta_var_stationary | mandate_conditional_oracle | 0.0029 [0.0028, 0.0030] | 0.0012 | 0.0017 | 0.0013 | 0.0048 | 1.73 | 0.213 |
| flat | 0.06561 | theta_var_stationary | rule_p_sma50 | 0.0502 [0.0398, 0.0615] | 0.0012 | 0.0490 | 0.0013 | 0.0519 | 1.62 | 0.213 |
| flat | 0.08 | grid | L5_full_level_free | 0.0750 [0.0604, 0.0889] | 0.0012 | 0.0738 | 0.0013 | 0.0781 | 1.33 | 0.143 |
| flat | 0.08 | grid | L5_level_free | 0.0706 [0.0585, 0.0829] | 0.0010 | 0.0695 | 0.0011 | 0.0757 | 1.33 | 0.143 |
| flat | 0.08 | grid | always_hold | 0.1150 [0.1101, 0.1194] | 0.0003 | 0.1146 | 0.0001 | 0.1141 | 1.33 | 0.143 |
| flat | 0.08 | grid | band_hi | 0.0995 [0.0823, 0.1180] | 0.0018 | 0.0977 | 0.0018 | 0.1005 | 1.33 | 0.143 |
| flat | 0.08 | grid | band_lo | 0.1042 [0.0860, 0.1205] | 0.0012 | 0.1030 | 0.0012 | 0.1034 | 0.91 | 0.143 |
| flat | 0.08 | grid | mandate_conditional_oracle | 0.0029 [0.0028, 0.0030] | 0.0011 | 0.0018 | 0.0013 | 0.0042 | 1.27 | 0.143 |
| flat | 0.08 | grid | rule_p_sma50 | 0.0428 [0.0326, 0.0548] | 0.0012 | 0.0416 | 0.0013 | 0.0478 | 1.19 | 0.143 |
| flat | 0.12 | grid | L5_full_level_free | 0.0641 [0.0424, 0.0848] | 0.0011 | 0.0629 | 0.0013 | 0.0676 | 0.72 | 0.049 |
| flat | 0.12 | grid | L5_level_free | 0.0514 [0.0381, 0.0672] | 0.0009 | 0.0505 | 0.0011 | 0.0539 | 0.72 | 0.049 |
| flat | 0.12 | grid | always_hold | 0.1221 [0.1158, 0.1297] | 0.0007 | 0.1215 | 0.0001 | 0.1213 | 0.72 | 0.049 |
| flat | 0.12 | grid | band_hi | 0.1086 [0.0850, 0.1335] | 0.0017 | 0.1069 | 0.0018 | 0.1083 | 0.72 | 0.049 |
| flat | 0.12 | grid | band_lo | 0.0958 [0.0724, 0.1170] | 0.0012 | 0.0946 | 0.0012 | 0.0961 | 0.43 | 0.049 |
| flat | 0.12 | grid | mandate_conditional_oracle | 0.0028 [0.0026, 0.0031] | 0.0007 | 0.0021 | 0.0013 | 0.0030 | 0.68 | 0.049 |
| flat | 0.12 | grid | rule_p_sma50 | 0.0237 [0.0124, 0.0369] | 0.0009 | 0.0228 | 0.0013 | 0.0269 | 0.64 | 0.049 |
| flat | 0.2 | grid|theta_info_calm | L5_full_level_free | 0.0412 [0.0096, 0.0770] | 0.0010 | 0.0402 | 0.0013 | 0.0412 | 0.14 | 0.011 |
| flat | 0.2 | grid|theta_info_calm | L5_level_free | 0.0119 [0.0027, 0.0285] | 0.0006 | 0.0113 | 0.0011 | 0.0120 | 0.14 | 0.011 |
| flat | 0.2 | grid|theta_info_calm | always_hold | 0.1300 [0.1153, 0.1410] | 0.0001 | 0.1299 | 0.0001 | 0.1294 | 0.14 | 0.011 |
| flat | 0.2 | grid|theta_info_calm | band_hi | 0.1880 [0.1591, 0.2031] | 0.0028 | 0.1852 | 0.0018 | 0.1880 | 0.14 | 0.011 |
| flat | 0.2 | grid|theta_info_calm | band_lo | 0.0165 [0.0020, 0.0447] | 0.0006 | 0.0159 | 0.0012 | 0.0165 | 0.01 | 0.011 |
| flat | 0.2 | grid|theta_info_calm | mandate_conditional_oracle | 0.0025 [0.0019, 0.0031] | 0.0006 | 0.0019 | 0.0013 | 0.0025 | 0.10 | 0.011 |
| flat | 0.2 | grid|theta_info_calm | rule_p_sma50 | 0.0049 [0.0024, 0.0083] | 0.0007 | 0.0042 | 0.0013 | 0.0087 | 0.10 | 0.011 |
| bull_trap | 0.002 | theta_cost | L5_full_level_free | 0.0564 [0.0513, 0.0618] | 0.0011 | 0.0552 | 0.0011 | 0.0574 | 7.79 | 0.983 |
| bull_trap | 0.002 | theta_cost | L5_level_free | 0.0595 [0.0545, 0.0648] | 0.0010 | 0.0586 | 0.0010 | 0.0600 | 7.79 | 0.983 |
| bull_trap | 0.002 | theta_cost | always_hold | 0.1238 [0.1206, 0.1271] | 0.0019 | 0.1219 | 0.0019 | 0.1227 | 7.79 | 0.983 |
| bull_trap | 0.002 | theta_cost | band_hi | 0.0486 [0.0433, 0.0538] | 0.0015 | 0.0471 | 0.0015 | 0.0470 | 7.79 | 0.983 |
| bull_trap | 0.002 | theta_cost | band_lo | 0.1551 [0.1497, 0.1602] | 0.0013 | 0.1538 | 0.0013 | 0.1565 | 7.75 | 0.983 |
| bull_trap | 0.002 | theta_cost | mandate_conditional_oracle | 0.0279 [0.0251, 0.0310] | 0.0013 | 0.0267 | 0.0013 | 0.0277 | 7.79 | 0.983 |
| bull_trap | 0.002 | theta_cost | rule_p_sma50 | 0.0544 [0.0498, 0.0595] | 0.0012 | 0.0531 | 0.0012 | 0.0586 | 7.77 | 0.983 |
| bull_trap | 0.03 | grid | L5_full_level_free | 0.0459 [0.0403, 0.0523] | 0.0012 | 0.0447 | 0.0011 | 0.0559 | 2.55 | 0.756 |
| bull_trap | 0.03 | grid | L5_level_free | 0.0483 [0.0436, 0.0544] | 0.0010 | 0.0473 | 0.0010 | 0.0585 | 2.55 | 0.756 |
| bull_trap | 0.03 | grid | always_hold | 0.1299 [0.1258, 0.1340] | 0.0025 | 0.1274 | 0.0019 | 0.1244 | 2.55 | 0.756 |
| bull_trap | 0.03 | grid | band_hi | 0.0353 [0.0305, 0.0405] | 0.0014 | 0.0339 | 0.0015 | 0.0476 | 2.55 | 0.756 |
| bull_trap | 0.03 | grid | band_lo | 0.1685 [0.1631, 0.1742] | 0.0013 | 0.1672 | 0.0013 | 0.1562 | 2.28 | 0.756 |
| bull_trap | 0.03 | grid | mandate_conditional_oracle | 0.0116 [0.0101, 0.0130] | 0.0013 | 0.0103 | 0.0013 | 0.0225 | 2.55 | 0.756 |
| bull_trap | 0.03 | grid | rule_p_sma50 | 0.0432 [0.0380, 0.0481] | 0.0012 | 0.0420 | 0.0012 | 0.0511 | 2.45 | 0.756 |
| bull_trap | 0.03279 | theta_cost_one_day | L5_full_level_free | 0.0448 [0.0390, 0.0515] | 0.0012 | 0.0436 | 0.0011 | 0.0553 | 2.48 | 0.736 |
| bull_trap | 0.03279 | theta_cost_one_day | L5_level_free | 0.0471 [0.0410, 0.0533] | 0.0010 | 0.0461 | 0.0010 | 0.0578 | 2.48 | 0.736 |
| bull_trap | 0.03279 | theta_cost_one_day | always_hold | 0.1306 [0.1266, 0.1352] | 0.0026 | 0.1280 | 0.0019 | 0.1247 | 2.48 | 0.736 |
| bull_trap | 0.03279 | theta_cost_one_day | band_hi | 0.0340 [0.0290, 0.0403] | 0.0014 | 0.0326 | 0.0015 | 0.0474 | 2.48 | 0.736 |
| bull_trap | 0.03279 | theta_cost_one_day | band_lo | 0.1699 [0.1634, 0.1749] | 0.0013 | 0.1685 | 0.0013 | 0.1564 | 2.19 | 0.736 |
| bull_trap | 0.03279 | theta_cost_one_day | mandate_conditional_oracle | 0.0102 [0.0092, 0.0114] | 0.0013 | 0.0090 | 0.0013 | 0.0217 | 2.48 | 0.736 |
| bull_trap | 0.03279 | theta_cost_one_day | rule_p_sma50 | 0.0422 [0.0367, 0.0473] | 0.0012 | 0.0410 | 0.0012 | 0.0500 | 2.37 | 0.736 |
| bull_trap | 0.04632 | theta_var | L5_full_level_free | 0.0396 [0.0339, 0.0459] | 0.0012 | 0.0383 | 0.0011 | 0.0526 | 2.00 | 0.652 |
| bull_trap | 0.04632 | theta_var | L5_level_free | 0.0418 [0.0347, 0.0484] | 0.0011 | 0.0407 | 0.0010 | 0.0541 | 2.00 | 0.652 |
| bull_trap | 0.04632 | theta_var | always_hold | 0.1339 [0.1293, 0.1382] | 0.0029 | 0.1310 | 0.0019 | 0.1266 | 2.00 | 0.652 |
| bull_trap | 0.04632 | theta_var | band_hi | 0.0276 [0.0228, 0.0331] | 0.0014 | 0.0262 | 0.0015 | 0.0438 | 2.00 | 0.652 |
| bull_trap | 0.04632 | theta_var | band_lo | 0.1763 [0.1707, 0.1817] | 0.0013 | 0.1750 | 0.0013 | 0.1601 | 1.67 | 0.652 |
| bull_trap | 0.04632 | theta_var | mandate_conditional_oracle | 0.0044 [0.0040, 0.0047] | 0.0013 | 0.0031 | 0.0013 | 0.0103 | 2.00 | 0.652 |
| bull_trap | 0.04632 | theta_var | rule_p_sma50 | 0.0386 [0.0334, 0.0439] | 0.0012 | 0.0374 | 0.0012 | 0.0451 | 1.87 | 0.652 |
| bull_trap | 0.05 | grid|theta_info_all | L5_full_level_free | 0.0383 [0.0321, 0.0449] | 0.0012 | 0.0371 | 0.0011 | 0.0517 | 1.96 | 0.633 |
| bull_trap | 0.05 | grid|theta_info_all | L5_level_free | 0.0405 [0.0345, 0.0470] | 0.0011 | 0.0394 | 0.0010 | 0.0527 | 1.96 | 0.633 |
| bull_trap | 0.05 | grid|theta_info_all | always_hold | 0.1347 [0.1294, 0.1392] | 0.0030 | 0.1317 | 0.0019 | 0.1270 | 1.96 | 0.633 |
| bull_trap | 0.05 | grid|theta_info_all | band_hi | 0.0262 [0.0210, 0.0315] | 0.0014 | 0.0248 | 0.0015 | 0.0431 | 1.96 | 0.633 |
| bull_trap | 0.05 | grid|theta_info_all | band_lo | 0.1777 [0.1726, 0.1823] | 0.0013 | 0.1763 | 0.0013 | 0.1609 | 1.64 | 0.633 |
| bull_trap | 0.05 | grid|theta_info_all | mandate_conditional_oracle | 0.0033 [0.0033, 0.0034] | 0.0013 | 0.0021 | 0.0013 | 0.0060 | 1.96 | 0.633 |
| bull_trap | 0.05 | grid|theta_info_all | rule_p_sma50 | 0.0378 [0.0326, 0.0428] | 0.0012 | 0.0366 | 0.0012 | 0.0438 | 1.83 | 0.633 |
| bull_trap | 0.06561 | theta_var_stationary | L5_full_level_free | 0.0326 [0.0267, 0.0391] | 0.0012 | 0.0314 | 0.0011 | 0.0445 | 1.68 | 0.555 |
| bull_trap | 0.06561 | theta_var_stationary | L5_level_free | 0.0346 [0.0288, 0.0419] | 0.0011 | 0.0335 | 0.0010 | 0.0458 | 1.68 | 0.555 |
| bull_trap | 0.06561 | theta_var_stationary | always_hold | 0.1384 [0.1333, 0.1437] | 0.0033 | 0.1351 | 0.0019 | 0.1311 | 1.68 | 0.555 |
| bull_trap | 0.06561 | theta_var_stationary | band_hi | 0.0206 [0.0161, 0.0261] | 0.0013 | 0.0193 | 0.0015 | 0.0350 | 1.68 | 0.555 |
| bull_trap | 0.06561 | theta_var_stationary | band_lo | 0.1833 [0.1786, 0.1875] | 0.0014 | 0.1820 | 0.0013 | 0.1691 | 1.35 | 0.555 |
| bull_trap | 0.06561 | theta_var_stationary | mandate_conditional_oracle | 0.0035 [0.0034, 0.0035] | 0.0012 | 0.0022 | 0.0013 | 0.0051 | 1.64 | 0.555 |
| bull_trap | 0.06561 | theta_var_stationary | rule_p_sma50 | 0.0340 [0.0284, 0.0393] | 0.0012 | 0.0328 | 0.0012 | 0.0385 | 1.55 | 0.555 |
| bull_trap | 0.08 | grid | L5_full_level_free | 0.0286 [0.0229, 0.0356] | 0.0013 | 0.0273 | 0.0011 | 0.0394 | 1.61 | 0.501 |
| bull_trap | 0.08 | grid | L5_level_free | 0.0303 [0.0230, 0.0370] | 0.0012 | 0.0292 | 0.0010 | 0.0406 | 1.61 | 0.501 |
| bull_trap | 0.08 | grid | always_hold | 0.1413 [0.1359, 0.1473] | 0.0036 | 0.1377 | 0.0019 | 0.1344 | 1.61 | 0.501 |
| bull_trap | 0.08 | grid | band_hi | 0.0169 [0.0130, 0.0214] | 0.0013 | 0.0156 | 0.0015 | 0.0305 | 1.61 | 0.501 |
| bull_trap | 0.08 | grid | band_lo | 0.1870 [0.1820, 0.1910] | 0.0014 | 0.1856 | 0.0013 | 0.1735 | 1.27 | 0.501 |
| bull_trap | 0.08 | grid | mandate_conditional_oracle | 0.0035 [0.0034, 0.0035] | 0.0012 | 0.0022 | 0.0013 | 0.0049 | 1.53 | 0.501 |
| bull_trap | 0.08 | grid | rule_p_sma50 | 0.0316 [0.0265, 0.0371] | 0.0012 | 0.0304 | 0.0012 | 0.0369 | 1.48 | 0.501 |
| bull_trap | 0.12 | grid | L5_full_level_free | 0.0214 [0.0159, 0.0277] | 0.0013 | 0.0201 | 0.0011 | 0.0265 | 1.31 | 0.404 |
| bull_trap | 0.12 | grid | L5_level_free | 0.0243 [0.0176, 0.0319] | 0.0012 | 0.0231 | 0.0010 | 0.0287 | 1.31 | 0.404 |
| bull_trap | 0.12 | grid | always_hold | 0.1470 [0.1406, 0.1532] | 0.0044 | 0.1426 | 0.0019 | 0.1418 | 1.31 | 0.404 |
| bull_trap | 0.12 | grid | band_hi | 0.0112 [0.0077, 0.0152] | 0.0013 | 0.0099 | 0.0015 | 0.0173 | 1.31 | 0.404 |
| bull_trap | 0.12 | grid | band_lo | 0.1928 [0.1889, 0.1961] | 0.0014 | 0.1914 | 0.0013 | 0.1868 | 1.14 | 0.404 |
| bull_trap | 0.12 | grid | mandate_conditional_oracle | 0.0035 [0.0035, 0.0036] | 0.0012 | 0.0023 | 0.0013 | 0.0040 | 1.26 | 0.404 |
| bull_trap | 0.12 | grid | rule_p_sma50 | 0.0270 [0.0215, 0.0328] | 0.0012 | 0.0258 | 0.0012 | 0.0268 | 1.23 | 0.404 |
| bull_trap | 0.2 | grid|theta_info_calm | L5_full_level_free | 0.0156 [0.0110, 0.0209] | 0.0014 | 0.0142 | 0.0011 | 0.0167 | 1.07 | 0.289 |
| bull_trap | 0.2 | grid|theta_info_calm | L5_level_free | 0.0184 [0.0122, 0.0249] | 0.0013 | 0.0170 | 0.0010 | 0.0202 | 1.07 | 0.289 |
| bull_trap | 0.2 | grid|theta_info_calm | always_hold | 0.1544 [0.1483, 0.1611] | 0.0059 | 0.1485 | 0.0019 | 0.1513 | 1.07 | 0.289 |
| bull_trap | 0.2 | grid|theta_info_calm | band_hi | 0.0061 [0.0040, 0.0089] | 0.0013 | 0.0048 | 0.0015 | 0.0077 | 1.07 | 0.289 |
| bull_trap | 0.2 | grid|theta_info_calm | band_lo | 0.1977 [0.1948, 0.1999] | 0.0013 | 0.1964 | 0.0013 | 0.1963 | 1.03 | 0.289 |
| bull_trap | 0.2 | grid|theta_info_calm | mandate_conditional_oracle | 0.0035 [0.0035, 0.0036] | 0.0013 | 0.0022 | 0.0013 | 0.0043 | 1.06 | 0.289 |
| bull_trap | 0.2 | grid|theta_info_calm | rule_p_sma50 | 0.0242 [0.0186, 0.0298] | 0.0012 | 0.0230 | 0.0012 | 0.0231 | 1.06 | 0.289 |
| crash | 0.002 | theta_cost | L5_full_level_free | 0.0674 [0.0627, 0.0719] | 0.0010 | 0.0664 | 0.0010 | 0.0691 | 14.36 | 0.979 |
| crash | 0.002 | theta_cost | L5_level_free | 0.0652 [0.0611, 0.0692] | 0.0009 | 0.0643 | 0.0009 | 0.0655 | 14.36 | 0.979 |
| crash | 0.002 | theta_cost | always_hold | 0.1244 [0.1211, 0.1276] | 0.0025 | 0.1219 | 0.0025 | 0.1240 | 14.36 | 0.979 |
| crash | 0.002 | theta_cost | band_hi | 0.1236 [0.1172, 0.1298] | 0.0018 | 0.1218 | 0.0018 | 0.1255 | 14.36 | 0.979 |
| crash | 0.002 | theta_cost | band_lo | 0.0793 [0.0738, 0.0854] | 0.0010 | 0.0783 | 0.0010 | 0.0773 | 14.33 | 0.979 |
| crash | 0.002 | theta_cost | mandate_conditional_oracle | 0.0331 [0.0301, 0.0362] | 0.0012 | 0.0319 | 0.0012 | 0.0352 | 14.36 | 0.979 |
| crash | 0.002 | theta_cost | rule_p_sma50 | 0.0668 [0.0630, 0.0714] | 0.0012 | 0.0656 | 0.0012 | 0.0718 | 14.34 | 0.979 |
| crash | 0.03 | grid | L5_full_level_free | 0.0564 [0.0513, 0.0610] | 0.0010 | 0.0553 | 0.0010 | 0.0656 | 5.92 | 0.693 |
| crash | 0.03 | grid | L5_level_free | 0.0536 [0.0492, 0.0583] | 0.0009 | 0.0527 | 0.0009 | 0.0631 | 5.92 | 0.693 |
| crash | 0.03 | grid | always_hold | 0.1326 [0.1288, 0.1367] | 0.0032 | 0.1294 | 0.0025 | 0.1270 | 5.92 | 0.693 |
| crash | 0.03 | grid | band_hi | 0.1337 [0.1263, 0.1411] | 0.0017 | 0.1319 | 0.0018 | 0.1290 | 5.92 | 0.693 |
| crash | 0.03 | grid | band_lo | 0.0692 [0.0619, 0.0761] | 0.0010 | 0.0682 | 0.0010 | 0.0740 | 5.63 | 0.693 |
| crash | 0.03 | grid | mandate_conditional_oracle | 0.0140 [0.0125, 0.0156] | 0.0012 | 0.0128 | 0.0012 | 0.0285 | 5.92 | 0.693 |
| crash | 0.03 | grid | rule_p_sma50 | 0.0562 [0.0514, 0.0609] | 0.0012 | 0.0550 | 0.0012 | 0.0644 | 5.83 | 0.693 |
| crash | 0.03279 | theta_cost_one_day | L5_full_level_free | 0.0552 [0.0506, 0.0605] | 0.0010 | 0.0542 | 0.0010 | 0.0653 | 5.75 | 0.668 |
| crash | 0.03279 | theta_cost_one_day | L5_level_free | 0.0524 [0.0476, 0.0567] | 0.0009 | 0.0515 | 0.0009 | 0.0626 | 5.75 | 0.668 |
| crash | 0.03279 | theta_cost_one_day | always_hold | 0.1335 [0.1297, 0.1367] | 0.0033 | 0.1302 | 0.0025 | 0.1275 | 5.75 | 0.668 |
| crash | 0.03279 | theta_cost_one_day | band_hi | 0.1348 [0.1278, 0.1420] | 0.0017 | 0.1331 | 0.0018 | 0.1296 | 5.75 | 0.668 |
| crash | 0.03279 | theta_cost_one_day | band_lo | 0.0681 [0.0606, 0.0757] | 0.0010 | 0.0670 | 0.0010 | 0.0734 | 5.45 | 0.668 |
| crash | 0.03279 | theta_cost_one_day | mandate_conditional_oracle | 0.0122 [0.0108, 0.0137] | 0.0012 | 0.0111 | 0.0012 | 0.0276 | 5.75 | 0.668 |
| crash | 0.03279 | theta_cost_one_day | rule_p_sma50 | 0.0551 [0.0503, 0.0593] | 0.0012 | 0.0539 | 0.0012 | 0.0636 | 5.65 | 0.668 |
| crash | 0.04632 | theta_var | L5_full_level_free | 0.0482 [0.0433, 0.0534] | 0.0010 | 0.0472 | 0.0010 | 0.0628 | 4.52 | 0.555 |
| crash | 0.04632 | theta_var | L5_level_free | 0.0456 [0.0410, 0.0499] | 0.0010 | 0.0446 | 0.0009 | 0.0595 | 4.52 | 0.555 |
| crash | 0.04632 | theta_var | always_hold | 0.1385 [0.1339, 0.1425] | 0.0038 | 0.1348 | 0.0025 | 0.1301 | 4.52 | 0.555 |
| crash | 0.04632 | theta_var | band_hi | 0.1424 [0.1351, 0.1495] | 0.0017 | 0.1406 | 0.0018 | 0.1321 | 4.52 | 0.555 |
| crash | 0.04632 | theta_var | band_lo | 0.0604 [0.0524, 0.0679] | 0.0010 | 0.0594 | 0.0010 | 0.0709 | 4.14 | 0.555 |
| crash | 0.04632 | theta_var | mandate_conditional_oracle | 0.0039 [0.0035, 0.0044] | 0.0011 | 0.0029 | 0.0012 | 0.0167 | 4.52 | 0.555 |
| crash | 0.04632 | theta_var | rule_p_sma50 | 0.0496 [0.0443, 0.0546] | 0.0012 | 0.0484 | 0.0012 | 0.0585 | 4.39 | 0.555 |
| crash | 0.05 | grid|theta_info_all | L5_full_level_free | 0.0466 [0.0419, 0.0518] | 0.0010 | 0.0456 | 0.0010 | 0.0612 | 4.27 | 0.530 |
| crash | 0.05 | grid|theta_info_all | L5_level_free | 0.0437 [0.0389, 0.0487] | 0.0010 | 0.0427 | 0.0009 | 0.0567 | 4.27 | 0.530 |
| crash | 0.05 | grid|theta_info_all | always_hold | 0.1400 [0.1359, 0.1441] | 0.0039 | 0.1360 | 0.0025 | 0.1320 | 4.27 | 0.530 |
| crash | 0.05 | grid|theta_info_all | band_hi | 0.1447 [0.1365, 0.1524] | 0.0017 | 0.1430 | 0.0018 | 0.1355 | 4.27 | 0.530 |
| crash | 0.05 | grid|theta_info_all | band_lo | 0.0581 [0.0509, 0.0663] | 0.0010 | 0.0571 | 0.0010 | 0.0674 | 3.90 | 0.530 |
| crash | 0.05 | grid|theta_info_all | mandate_conditional_oracle | 0.0022 [0.0022, 0.0023] | 0.0011 | 0.0012 | 0.0012 | 0.0129 | 4.27 | 0.530 |
| crash | 0.05 | grid|theta_info_all | rule_p_sma50 | 0.0481 [0.0434, 0.0532] | 0.0012 | 0.0469 | 0.0012 | 0.0562 | 4.14 | 0.530 |
| crash | 0.06561 | theta_var_stationary | L5_full_level_free | 0.0388 [0.0336, 0.0441] | 0.0010 | 0.0378 | 0.0010 | 0.0549 | 3.48 | 0.431 |
| crash | 0.06561 | theta_var_stationary | L5_level_free | 0.0357 [0.0313, 0.0403] | 0.0010 | 0.0348 | 0.0009 | 0.0500 | 3.48 | 0.431 |
| crash | 0.06561 | theta_var_stationary | always_hold | 0.1459 [0.1411, 0.1504] | 0.0045 | 0.1414 | 0.0025 | 0.1372 | 3.48 | 0.431 |
| crash | 0.06561 | theta_var_stationary | band_hi | 0.1547 [0.1473, 0.1620] | 0.0017 | 0.1530 | 0.0018 | 0.1441 | 3.48 | 0.431 |
| crash | 0.06561 | theta_var_stationary | band_lo | 0.0480 [0.0408, 0.0557] | 0.0010 | 0.0470 | 0.0010 | 0.0589 | 3.03 | 0.431 |
| crash | 0.06561 | theta_var_stationary | mandate_conditional_oracle | 0.0023 [0.0022, 0.0023] | 0.0010 | 0.0013 | 0.0012 | 0.0110 | 3.45 | 0.431 |
| crash | 0.06561 | theta_var_stationary | rule_p_sma50 | 0.0415 [0.0368, 0.0467] | 0.0011 | 0.0404 | 0.0012 | 0.0506 | 3.33 | 0.431 |
| crash | 0.08 | grid | L5_full_level_free | 0.0329 [0.0280, 0.0381] | 0.0010 | 0.0319 | 0.0010 | 0.0483 | 2.87 | 0.361 |
| crash | 0.08 | grid | L5_level_free | 0.0293 [0.0246, 0.0339] | 0.0009 | 0.0284 | 0.0009 | 0.0443 | 2.87 | 0.361 |
| crash | 0.08 | grid | always_hold | 0.1508 [0.1460, 0.1555] | 0.0052 | 0.1456 | 0.0025 | 0.1414 | 2.87 | 0.361 |
| crash | 0.08 | grid | band_hi | 0.1628 [0.1552, 0.1700] | 0.0018 | 0.1611 | 0.0018 | 0.1504 | 2.87 | 0.361 |
| crash | 0.08 | grid | band_lo | 0.0398 [0.0332, 0.0472] | 0.0009 | 0.0389 | 0.0010 | 0.0526 | 2.32 | 0.361 |
| crash | 0.08 | grid | mandate_conditional_oracle | 0.0022 [0.0022, 0.0023] | 0.0010 | 0.0013 | 0.0012 | 0.0096 | 2.80 | 0.361 |
| crash | 0.08 | grid | rule_p_sma50 | 0.0363 [0.0314, 0.0415] | 0.0011 | 0.0352 | 0.0012 | 0.0470 | 2.68 | 0.361 |
| crash | 0.12 | grid | L5_full_level_free | 0.0187 [0.0143, 0.0240] | 0.0009 | 0.0178 | 0.0010 | 0.0304 | 1.93 | 0.236 |
| crash | 0.12 | grid | L5_level_free | 0.0159 [0.0117, 0.0198] | 0.0009 | 0.0150 | 0.0009 | 0.0282 | 1.93 | 0.236 |
| crash | 0.12 | grid | always_hold | 0.1633 [0.1583, 0.1682] | 0.0070 | 0.1563 | 0.0025 | 0.1547 | 1.93 | 0.236 |
| crash | 0.12 | grid | band_hi | 0.1789 [0.1725, 0.1846] | 0.0018 | 0.1771 | 0.0018 | 0.1661 | 1.93 | 0.236 |
| crash | 0.12 | grid | band_lo | 0.0237 [0.0185, 0.0304] | 0.0009 | 0.0228 | 0.0010 | 0.0368 | 1.27 | 0.236 |
| crash | 0.12 | grid | mandate_conditional_oracle | 0.0020 [0.0020, 0.0021] | 0.0009 | 0.0012 | 0.0012 | 0.0067 | 1.86 | 0.236 |
| crash | 0.12 | grid | rule_p_sma50 | 0.0234 [0.0181, 0.0287] | 0.0010 | 0.0224 | 0.0012 | 0.0318 | 1.75 | 0.236 |
| crash | 0.2 | grid|theta_info_calm | L5_full_level_free | 0.0055 [0.0036, 0.0079] | 0.0007 | 0.0048 | 0.0010 | 0.0091 | 1.09 | 0.108 |
| crash | 0.2 | grid|theta_info_calm | L5_level_free | 0.0041 [0.0027, 0.0059] | 0.0007 | 0.0034 | 0.0009 | 0.0067 | 1.09 | 0.108 |
| crash | 0.2 | grid|theta_info_calm | always_hold | 0.1782 [0.1731, 0.1844] | 0.0101 | 0.1682 | 0.0025 | 0.1746 | 1.09 | 0.108 |
| crash | 0.2 | grid|theta_info_calm | band_hi | 0.1919 [0.1860, 0.1969] | 0.0018 | 0.1900 | 0.0018 | 0.1891 | 1.09 | 0.108 |
| crash | 0.2 | grid|theta_info_calm | band_lo | 0.0107 [0.0055, 0.0167] | 0.0007 | 0.0100 | 0.0010 | 0.0137 | 0.24 | 0.108 |
| crash | 0.2 | grid|theta_info_calm | mandate_conditional_oracle | 0.0018 [0.0016, 0.0019] | 0.0007 | 0.0011 | 0.0012 | 0.0030 | 1.02 | 0.108 |
| crash | 0.2 | grid|theta_info_calm | rule_p_sma50 | 0.0086 [0.0057, 0.0126] | 0.0008 | 0.0078 | 0.0012 | 0.0133 | 0.90 | 0.108 |
| sustained_bull | 0.002 | theta_cost | L5_full_level_free | 0.0825 [0.0762, 0.0882] | 0.0011 | 0.0814 | 0.0011 | 0.0799 | 12.31 | 0.967 |
| sustained_bull | 0.002 | theta_cost | L5_level_free | 0.0840 [0.0779, 0.0900] | 0.0011 | 0.0829 | 0.0011 | 0.0826 | 12.31 | 0.967 |
| sustained_bull | 0.002 | theta_cost | always_hold | 0.1130 [0.1097, 0.1168] | 0.0024 | 0.1105 | 0.0024 | 0.1133 | 12.31 | 0.967 |
| sustained_bull | 0.002 | theta_cost | band_hi | 0.0889 [0.0813, 0.0957] | 0.0013 | 0.0876 | 0.0013 | 0.0863 | 12.31 | 0.967 |
| sustained_bull | 0.002 | theta_cost | band_lo | 0.1143 [0.1070, 0.1221] | 0.0014 | 0.1129 | 0.0014 | 0.1168 | 12.29 | 0.967 |
| sustained_bull | 0.002 | theta_cost | mandate_conditional_oracle | 0.0463 [0.0426, 0.0502] | 0.0011 | 0.0451 | 0.0011 | 0.0418 | 12.31 | 0.967 |
| sustained_bull | 0.002 | theta_cost | rule_p_sma50 | 0.0727 [0.0662, 0.0792] | 0.0012 | 0.0714 | 0.0012 | 0.0746 | 12.30 | 0.967 |
| sustained_bull | 0.03 | grid | L5_full_level_free | 0.0779 [0.0690, 0.0863] | 0.0011 | 0.0768 | 0.0011 | 0.0798 | 3.56 | 0.546 |
| sustained_bull | 0.03 | grid | L5_level_free | 0.0788 [0.0707, 0.0879] | 0.0011 | 0.0777 | 0.0011 | 0.0823 | 3.56 | 0.546 |
| sustained_bull | 0.03 | grid | always_hold | 0.1160 [0.1105, 0.1208] | 0.0027 | 0.1134 | 0.0024 | 0.1147 | 3.56 | 0.546 |
| sustained_bull | 0.03 | grid | band_hi | 0.0872 [0.0769, 0.0977] | 0.0013 | 0.0859 | 0.0013 | 0.0880 | 3.56 | 0.546 |
| sustained_bull | 0.03 | grid | band_lo | 0.1162 [0.1060, 0.1270] | 0.0014 | 0.1148 | 0.0014 | 0.1155 | 3.31 | 0.546 |
| sustained_bull | 0.03 | grid | mandate_conditional_oracle | 0.0225 [0.0194, 0.0253] | 0.0011 | 0.0213 | 0.0011 | 0.0349 | 3.56 | 0.546 |
| sustained_bull | 0.03 | grid | rule_p_sma50 | 0.0624 [0.0539, 0.0719] | 0.0012 | 0.0612 | 0.0012 | 0.0678 | 3.49 | 0.546 |
| sustained_bull | 0.03279 | theta_cost_one_day | L5_full_level_free | 0.0776 [0.0697, 0.0858] | 0.0011 | 0.0765 | 0.0011 | 0.0806 | 3.30 | 0.509 |
| sustained_bull | 0.03279 | theta_cost_one_day | L5_level_free | 0.0783 [0.0701, 0.0866] | 0.0011 | 0.0772 | 0.0011 | 0.0826 | 3.30 | 0.509 |
| sustained_bull | 0.03279 | theta_cost_one_day | always_hold | 0.1163 [0.1111, 0.1208] | 0.0027 | 0.1136 | 0.0024 | 0.1144 | 3.30 | 0.509 |
| sustained_bull | 0.03279 | theta_cost_one_day | band_hi | 0.0871 [0.0775, 0.0975] | 0.0013 | 0.0858 | 0.0013 | 0.0894 | 3.30 | 0.509 |
| sustained_bull | 0.03279 | theta_cost_one_day | band_lo | 0.1164 [0.1059, 0.1273] | 0.0014 | 0.1150 | 0.0014 | 0.1141 | 3.01 | 0.509 |
| sustained_bull | 0.03279 | theta_cost_one_day | mandate_conditional_oracle | 0.0198 [0.0172, 0.0227] | 0.0011 | 0.0187 | 0.0011 | 0.0310 | 3.30 | 0.509 |
| sustained_bull | 0.03279 | theta_cost_one_day | rule_p_sma50 | 0.0613 [0.0532, 0.0689] | 0.0012 | 0.0601 | 0.0012 | 0.0668 | 3.21 | 0.509 |
| sustained_bull | 0.04632 | theta_var | L5_full_level_free | 0.0775 [0.0680, 0.0876] | 0.0011 | 0.0764 | 0.0011 | 0.0802 | 2.49 | 0.360 |
| sustained_bull | 0.04632 | theta_var | L5_level_free | 0.0777 [0.0678, 0.0876] | 0.0011 | 0.0767 | 0.0011 | 0.0816 | 2.49 | 0.360 |
| sustained_bull | 0.04632 | theta_var | always_hold | 0.1172 [0.1118, 0.1231] | 0.0029 | 0.1143 | 0.0024 | 0.1158 | 2.49 | 0.360 |
| sustained_bull | 0.04632 | theta_var | band_hi | 0.0879 [0.0767, 0.1003] | 0.0013 | 0.0866 | 0.0013 | 0.0891 | 2.49 | 0.360 |
| sustained_bull | 0.04632 | theta_var | band_lo | 0.1157 [0.1026, 0.1273] | 0.0014 | 0.1142 | 0.0014 | 0.1146 | 2.11 | 0.360 |
| sustained_bull | 0.04632 | theta_var | mandate_conditional_oracle | 0.0062 [0.0054, 0.0071] | 0.0010 | 0.0052 | 0.0011 | 0.0149 | 2.49 | 0.360 |
| sustained_bull | 0.04632 | theta_var | rule_p_sma50 | 0.0587 [0.0503, 0.0691] | 0.0012 | 0.0575 | 0.0012 | 0.0627 | 2.37 | 0.360 |
| sustained_bull | 0.05 | grid|theta_info_all | L5_full_level_free | 0.0769 [0.0677, 0.0867] | 0.0011 | 0.0758 | 0.0011 | 0.0816 | 2.37 | 0.328 |
| sustained_bull | 0.05 | grid|theta_info_all | L5_level_free | 0.0771 [0.0671, 0.0877] | 0.0011 | 0.0761 | 0.0011 | 0.0817 | 2.37 | 0.328 |
| sustained_bull | 0.05 | grid|theta_info_all | always_hold | 0.1179 [0.1117, 0.1239] | 0.0030 | 0.1149 | 0.0024 | 0.1156 | 2.37 | 0.328 |
| sustained_bull | 0.05 | grid|theta_info_all | band_hi | 0.0877 [0.0755, 0.1012] | 0.0013 | 0.0863 | 0.0013 | 0.0901 | 2.37 | 0.328 |
| sustained_bull | 0.05 | grid|theta_info_all | band_lo | 0.1160 [0.1018, 0.1282] | 0.0014 | 0.1145 | 0.0014 | 0.1137 | 2.00 | 0.328 |
| sustained_bull | 0.05 | grid|theta_info_all | mandate_conditional_oracle | 0.0028 [0.0027, 0.0029] | 0.0010 | 0.0017 | 0.0011 | 0.0063 | 2.37 | 0.328 |
| sustained_bull | 0.05 | grid|theta_info_all | rule_p_sma50 | 0.0570 [0.0472, 0.0671] | 0.0012 | 0.0558 | 0.0012 | 0.0618 | 2.25 | 0.328 |
| sustained_bull | 0.06561 | theta_var_stationary | L5_full_level_free | 0.0791 [0.0665, 0.0925] | 0.0011 | 0.0780 | 0.0011 | 0.0817 | 1.81 | 0.215 |
| sustained_bull | 0.06561 | theta_var_stationary | L5_level_free | 0.0801 [0.0686, 0.0912] | 0.0011 | 0.0790 | 0.0011 | 0.0847 | 1.81 | 0.215 |
| sustained_bull | 0.06561 | theta_var_stationary | always_hold | 0.1170 [0.1103, 0.1250] | 0.0033 | 0.1137 | 0.0024 | 0.1158 | 1.81 | 0.215 |
| sustained_bull | 0.06561 | theta_var_stationary | band_hi | 0.0932 [0.0788, 0.1088] | 0.0013 | 0.0918 | 0.0013 | 0.0923 | 1.81 | 0.215 |
| sustained_bull | 0.06561 | theta_var_stationary | band_lo | 0.1104 [0.0958, 0.1237] | 0.0014 | 0.1091 | 0.0014 | 0.1116 | 1.42 | 0.215 |
| sustained_bull | 0.06561 | theta_var_stationary | mandate_conditional_oracle | 0.0029 [0.0028, 0.0031] | 0.0010 | 0.0020 | 0.0011 | 0.0049 | 1.79 | 0.215 |
| sustained_bull | 0.06561 | theta_var_stationary | rule_p_sma50 | 0.0552 [0.0432, 0.0675] | 0.0011 | 0.0541 | 0.0012 | 0.0575 | 1.66 | 0.215 |
| sustained_bull | 0.08 | grid | L5_full_level_free | 0.0783 [0.0623, 0.0918] | 0.0011 | 0.0772 | 0.0011 | 0.0824 | 1.38 | 0.145 |
| sustained_bull | 0.08 | grid | L5_level_free | 0.0781 [0.0635, 0.0925] | 0.0010 | 0.0770 | 0.0011 | 0.0838 | 1.38 | 0.145 |
| sustained_bull | 0.08 | grid | always_hold | 0.1162 [0.1075, 0.1259] | 0.0033 | 0.1129 | 0.0024 | 0.1151 | 1.38 | 0.145 |
| sustained_bull | 0.08 | grid | band_hi | 0.0976 [0.0800, 0.1156] | 0.0014 | 0.0963 | 0.0013 | 0.0967 | 1.38 | 0.145 |
| sustained_bull | 0.08 | grid | band_lo | 0.1060 [0.0888, 0.1241] | 0.0014 | 0.1046 | 0.0014 | 0.1072 | 0.99 | 0.145 |
| sustained_bull | 0.08 | grid | mandate_conditional_oracle | 0.0030 [0.0028, 0.0032] | 0.0009 | 0.0021 | 0.0011 | 0.0043 | 1.32 | 0.145 |
| sustained_bull | 0.08 | grid | rule_p_sma50 | 0.0516 [0.0392, 0.0654] | 0.0011 | 0.0505 | 0.0012 | 0.0582 | 1.22 | 0.145 |
| sustained_bull | 0.12 | grid | L5_full_level_free | 0.0774 [0.0570, 0.0971] | 0.0013 | 0.0761 | 0.0011 | 0.0840 | 0.80 | 0.049 |
| sustained_bull | 0.12 | grid | L5_level_free | 0.0774 [0.0591, 0.0975] | 0.0012 | 0.0762 | 0.0011 | 0.0844 | 0.80 | 0.049 |
| sustained_bull | 0.12 | grid | always_hold | 0.1192 [0.1061, 0.1317] | 0.0048 | 0.1145 | 0.0024 | 0.1190 | 0.80 | 0.049 |
| sustained_bull | 0.12 | grid | band_hi | 0.1103 [0.0880, 0.1327] | 0.0015 | 0.1088 | 0.0013 | 0.1090 | 0.80 | 0.049 |
| sustained_bull | 0.12 | grid | band_lo | 0.0940 [0.0726, 0.1180] | 0.0014 | 0.0926 | 0.0014 | 0.0954 | 0.48 | 0.049 |
| sustained_bull | 0.12 | grid | mandate_conditional_oracle | 0.0031 [0.0028, 0.0034] | 0.0007 | 0.0024 | 0.0011 | 0.0036 | 0.75 | 0.049 |
| sustained_bull | 0.12 | grid | rule_p_sma50 | 0.0454 [0.0290, 0.0643] | 0.0011 | 0.0443 | 0.0012 | 0.0477 | 0.70 | 0.049 |
| sustained_bull | 0.2 | grid|theta_info_calm | L5_full_level_free | 0.0604 [0.0274, 0.1022] | 0.0015 | 0.0589 | 0.0011 | 0.0691 | 0.15 | 0.010 |
| sustained_bull | 0.2 | grid|theta_info_calm | L5_level_free | 0.0459 [0.0215, 0.0763] | 0.0011 | 0.0448 | 0.0011 | 0.0510 | 0.15 | 0.010 |
| sustained_bull | 0.2 | grid|theta_info_calm | always_hold | 0.0952 [0.0775, 0.1118] | 0.0012 | 0.0940 | 0.0024 | 0.0925 | 0.15 | 0.010 |
| sustained_bull | 0.2 | grid|theta_info_calm | band_hi | 0.1763 [0.1367, 0.2018] | 0.0022 | 0.1741 | 0.0013 | 0.1803 | 0.15 | 0.010 |
| sustained_bull | 0.2 | grid|theta_info_calm | band_lo | 0.0275 [0.0022, 0.0667] | 0.0008 | 0.0267 | 0.0014 | 0.0234 | 0.02 | 0.010 |
| sustained_bull | 0.2 | grid|theta_info_calm | mandate_conditional_oracle | 0.0024 [0.0016, 0.0031] | 0.0008 | 0.0015 | 0.0011 | 0.0022 | 0.13 | 0.010 |
| sustained_bull | 0.2 | grid|theta_info_calm | rule_p_sma50 | 0.0157 [0.0025, 0.0380] | 0.0011 | 0.0146 | 0.0012 | 0.0192 | 0.12 | 0.010 |
<!-- /table:e7_theta_table -->

### 3.4 G3's θ profile — what D8 was asked about

| θ | 0.002 (θ_cost) | 0.030 | 0.033 | 0.046 (θ_var) | 0.050 (θ_info, all) | 0.066 (s_x) | 0.080 | 0.120 | 0.200 (θ_info, calm) |
|---|---|---|---|---|---|---|---|---|---|
| bull_trap (median / share ≥ 2) | 7 / 0.92 | 2 / 0.77 | 2 / 0.77 | 2 / 0.63 | 2 / 0.61 | 1 / 0.49 | 1 / 0.39 | 1 / 0.18 | 1 / 0.05 |
| crash | 14 / 0.99 | 6 / 0.92 | 5 / 0.94 | 4 / 0.91 | 4 / 0.90 | 3 / 0.79 | 3 / 0.72 | 2 / 0.54 | 1 / 0.13 |
| sustained_bull | 12 / 1.00 | 3 / 0.89 | 3 / 0.87 | 2 / 0.79 | 2 / 0.77 | 2 / 0.54 | 1 / 0.36 | 1 / 0.16 | 0 / 0.01 |
| **G3, daily** | PASS | PASS | PASS | PASS | **PASS** | FAIL | FAIL | FAIL | FAIL |
| **G3, per-window** | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| coverage (flat) | 0.968 | 0.546 | 0.511 | 0.360 | 0.328 | 0.213 | 0.143 | 0.049 | 0.011 |

The crossing is between θ = 0.05 and θ = 0.066. Under per-window scoring — 16A's own admissible response (ii) to a
G3 failure — G3 fails at **every** θ, so REG-12 option B does not rescue it; it removes the one gate that passes.
D8 records the θ-conditional pass (P7-5).

### 3.5 E7.2 — the decomposition, and the floor and ceiling

**B = max(0, |C − centre| − hw)** and **D = |C − c\*| − B**, on resolvable steps; MCR = mean(B + D) = mean|C − c\*|
identically. D is defined as the remainder — the only definition under which the identity holds for every C — and
because `oracle_target` clips c\* into the band, D ≥ 0 always. Both are asserted per step, including every
degenerate placement (C at an edge, outside on the oracle's side, outside on the far side, a zero half-width), by
`test_mcr_decomposition_identity`.

**The floor and the ceiling** (weakness 53, P0-2): ceiling = the mandate-conditional oracle, floor = the **worst**
of the trivial policies {always_hold, always_buy, always_sell, random, band_lo, band_hi}. The sign lives in one
function, `evaluation.scoring.normalise_metric`, which resolves a metric's orientation through
`scoring.orientation` — so `mcr`, `mcr_0.05` and `v21_mcr_0.05` all reach the same declared sign and an
unregistered metric **raises** rather than getting a default.

The size of the relabelling, on the panel at θ = 0.05 (`e7_rescore/normalisation.csv`): the level-free observables
oracle's normalised MCR moves from **1.067** under the v2 convention — *above 1*, because the v2 "ceiling" is
constant-mix and the oracle beats it — to **0.919** under v2.1. The v2.1 ceiling is **0.0028**, not the 0 the
pre-registration wrote: the oracle is executed through `PortfolioV2`, so a target inside the 1-point dead band is
not traded and the realised share drifts with price between trades (addendum 8).

**Per-window scoring (REG-12 B)** is built as the pre-registered alternative and reported at every θ; it is not
adopted (section 3.11).

### 3.6 E7.3 — the bands against the environment's own risk and return

500 seeds per scenario (seeds 40000…, disjoint from the 16A scored seeds), T = 200, 252 trading days, dividends
paid; cluster-bootstrap intervals over paths. **r = 0**: cash does not accrue in this environment — a property of
`simulation/portfolio_v2.py`, stated, not assumed.

<!-- table:e7_merton -->
| scenario | mu (total return) | sigma (total return) | mu (price only) | sigma (price only) | realised dividend yield | payer share |
|---|---|---|---|---|---|---|
| flat (primary) | 0.0874 [0.0618, 0.1151] | 0.3468 [0.3381, 0.3556] | 0.0548 | 0.3456 | 0.03421 | 0.908 |
| bull_trap | 0.5289 [0.5058, 0.5541] | 0.3834 [0.3727, 0.3968] | 0.5006 | 0.3826 | 0.03300 | 0.904 |
| crash | -0.3211 [-0.3503, -0.2931] | 0.6591 [0.6305, 0.6935] | -0.3580 | 0.6583 | 0.03209 | 0.906 |
| sustained_bull | 0.6209 [0.5973, 0.6406] | 0.3464 [0.3381, 0.3552] | 0.5902 | 0.3454 | 0.04002 | 0.904 |

| gamma | risky share w* | cash share 1 − w* | unclipped | 95 % interval |
|---|---|---|---|---|
| 2 | 0.363 | **0.637** | 0.637 | [0.497, 0.756] |
| 3 | 0.242 | **0.758** | 0.758 | [0.664, 0.837] |
| 4 | 0.182 | **0.818** | 0.818 | [0.748, 0.878] |
| 6 | 0.121 | **0.879** | 0.879 | [0.832, 0.919] |
| 8 | 0.091 | **0.909** | 0.909 | [0.874, 0.939] |
| 10 | 0.073 | **0.927** | 0.927 | [0.899, 0.951] |

| persona | category | practitioner cash band (reading A, scored) | gammas whose Merton cash share falls inside it | nearest gamma to the band centre | Merton cash there |
|---|---|---|---|---|---|
| ISFJ | conservative | 0.70–0.90 | [3, 4, 6] | 4 | 0.818 |
| INTJ | balanced | 0.40–0.60 | — | 2 | 0.637 |
| ENTJ | aggressive | 0.00–0.20 | — | 2 | 0.637 |
<!-- /table:e7_merton -->

**Reading, and it is a strong one.** The environment's own annual σ on flat paths is **0.347**, not the v2
documents' "≈ 28 %"; μ with dividends is 0.087 against 0.055 price-only. At those moments the Merton cash share is
**0.64 at γ = 2 and 0.93 at γ = 10** — every value in the plan's grid sits at or above the *conservative* band.
Three γ values (3, 4, 6) fall inside ISFJ's practitioner band; **no γ in the grid falls inside INTJ's balanced band
or ENTJ's aggressive band.**

So reading B (utility-consistent bands) does not merely shift the personas — under it the balanced and aggressive
mandates are not utility-consistent for any γ the plan considers, and the *personas' spread would collapse into
one band*. That is the "a Merton table that puts every persona in one band" outcome the execution prompt named as a
result to report as a failure, and it is reported as one. It is also why D9's default matters: **A remains the
scored default** (P7-3), B is the sensitivity, and the consequence for band-MAS under B would be that INTJ and ENTJ
are scored against a band no CRRA investor in the grid would hold.

**The JFE ordering check is removed**, not disabled: Table 7 gives trait coefficients, not a spread (P7-6).

### 3.7 E7.4 — dividends paid

D10 = pay. The ex-dates are recovered from the generator's own frame — `days_since_eps_announcement == 0` marks the
quarterly announcement and nothing else, and `dps_quarterly` on that day is the DPS just announced — because
`envs/` is frozen in this phase and no path may move. Three ex-dates in a 200-day path, ~63 days apart.

**The sentence that travels with every dividend number:** the generator's price path is **not** ex-dividend
adjusted, so a paying holder is a total-return holder on a price-return path. Paying the dividend adds the yield to
the total return rather than redistributing it out of the price. That is the honest consequence of paying under a
frozen generator, not a modelling claim.

Measured on 500 flat seeds (seeds 40000…, E7.3's population): realised annual dividend yield **3.42 %**, payer
share **0.908** — the FIT payer share is a per-seed draw, so about 9 % of paths receive nothing at all even with
the switch on. (On the 16A seed block, seeds 0–99 across all four scenarios, the same draw gives a payer share of
0.880; the two differ only because they are different seeds.)
`PortfolioV2(dividends=False)` is the default and every baseline's metrics are identical under it
(`test_dividends_switch_inert_on_baselines`); the effect when it is on:

<!-- table:e7_dividends -->
100 seeds x 4 scenarios x 3 personas, T = 200; 88.0% of paths are payers (a per-seed draw at the FIT payer share, so a non-payer path receives nothing even with the switch on). The price path is not ex-dividend adjusted.

| policy | return % off → on (Δ) | MDD % off → on (Δ) | MCR(0.05) off → on (Δ) | band-MAS off → on (Δ) | turnover off → on (Δ) |
|---|---|---|---|---|---|
| always_buy | 23.056 → 25.635 (+2.579) | -28.827 → -28.431 (+0.396) | 0.4824 → 0.4808 (-0.0017) | 0.3667 → 0.3652 (-0.0015) | 0.467 → 0.486 (+0.020) |
| always_hold | 12.312 → 13.509 (+1.197) | -16.214 → -15.926 (+0.288) | 0.1261 → 0.1258 (-0.0003) | 0.0017 → 0.0018 (+0.0000) | 0.000 → 0.000 (+0.000) |
| always_sell | -0.027 → -0.026 (+0.000) | 0.000 → 0.000 (+0.000) | 0.5176 → 0.5176 (+0.0000) | 0.4333 → 0.4333 (+0.0000) | 0.533 → 0.533 (+0.000) |
| buy_day1_hold | 23.056 → 25.300 (+2.244) | -28.827 → -28.275 (+0.551) | 0.4824 → 0.4753 (-0.0071) | 0.3667 → 0.3603 (-0.0064) | 0.467 → 0.467 (+0.000) |
| constant_mix | 12.013 → 13.324 (+1.311) | -16.199 → -15.993 (+0.206) | 0.1008 → 0.1008 (+0.0000) | 0.0000 → 0.0000 (+0.0000) | 0.303 → 0.307 (+0.004) |
| mandate_conditional_oracle | 13.968 → 15.299 (+1.331) | -15.946 → -15.730 (+0.215) | 0.0028 → 0.0030 (+0.0002) | 0.0012 → 0.0012 (+0.0000) | 0.808 → 0.814 (+0.006) |
| mean_reversion | 3.821 → 4.737 (+0.916) | -18.748 → -18.483 (+0.265) | 0.4008 → 0.4001 (-0.0007) | 0.3236 → 0.3228 (-0.0008) | 1.418 → 1.424 (+0.006) |
| momentum | 14.382 → 15.814 (+1.432) | -20.783 → -20.566 (+0.217) | 0.5401 → 0.5394 (-0.0007) | 0.3940 → 0.3936 (-0.0005) | 4.580 → 4.606 (+0.025) |
| random | 8.536 → 9.641 (+1.105) | -18.415 → -18.172 (+0.243) | 0.3729 → 0.3729 (-0.0000) | 0.2715 → 0.2715 (-0.0000) | 35.261 → 35.443 (+0.181) |
| v_oracle | 21.814 → 23.130 (+1.316) | -18.053 → -17.822 (+0.231) | 0.4053 → 0.4051 (-0.0002) | 0.3715 → 0.3709 (-0.0006) | 3.031 → 3.050 (+0.019) |
<!-- /table:e7_dividends -->

**Reading.** Paying the dividend adds 0.9–2.6 pp of 200-day return in proportion to how invested a policy is, and
`always_sell` — which holds no shares — gains **exactly 0.000**, which is the sanity check that the credit goes to
holdings and nothing else. The conformity metrics barely move: |ΔMCR| ≤ 0.007 and |Δband-MAS| ≤ 0.007 across every
policy. That is the right result and worth stating, because it says the D10 decision changes *the money*, not the
mandate-conformity scores the paper reports — the small residual comes from the cash inflow nudging the cash share
between trades.

### 3.8 E7.5 — the day-1 gate

Computed on the **common-start design only**, on C₁ levels (KW, Cliff's δ, band-hit, AUC). The ΔC₁ table under
start-at-target is **removed**, not demoted: under start-at-target every persona begins at its own band centre, so
ΔC₁ ≈ 0 for any persona-consistent agent and a level/band-membership test on it cannot separate personas whatever
the agent does — its verdict carries no information about the agent. Keeping it as "exploratory" invited it to be
read as weak evidence.

The null is the arms in which no persona text is shown (the O3 numerical-only arm and the no-persona trader). **The
pilot's 9 common-start runs carry no such arm**, so the gate's null is reported `NOT COMPUTABLE` with the run
counts and the personas and arms that *are* present — a result, not a substituted threshold.

### 3.9 E7.6 — the baselines on the run's own path

<!-- table:e7_repro -->
| question | answer |
|---|---|
| pilot runs | 52 |
| engines recorded | fw_single |
| environments CONSTRUCTIBLE under the recorded engine | **0 of 52** |
| paths that reproduce under the recorded engine | **0 of 52** |
| constructible under the documented CAL fallback engine | 52 of 52 |
| paths that reproduce under the fallback engine | 0 of 52 |
| worst abs difference against the logged price / V / x, fallback engine | median 37.50, minimum 37.50 |
| `Gen_Config_Hash` recomputed from the stored metadata matches | 52 of 52 |

The generator's own refusal, verbatim:

```
FileNotFoundError: engine 'fw_single' needs an accepted SMM estimate at <repo>\envs\v2\params\fw_single_stock.json; none exists (the attempt was rejected: fw_single_stock.REJECTED.json). Use engine 'ar1_fit' (the documented CAL fallback) explicitly.
```
<!-- /table:e7_repro -->

**Reading.** This is stronger than "the paths differ". The engine the pilot ran on **cannot be built**: Phase 2's
SMM rejected `fw_single` and the parameter file is now `fw_single_stock.REJECTED.json`. `Gen_Config_Hash`
recomputes correctly in 52 of 52, so the pilot's provenance record is intact — it is the generator that moved out
from under it.

Running the rebuild anyway, to report its outcome rather than assume it: `cell_baselines(from_meta=True)` raises
for **52 of 52** pilot cells with that same refusal (`e7_6/baselines_compare.{csv,md}`). The switch is therefore
correct and *untestable on this pilot*, which is why its test is on a freshly generated cell whose configuration
the seven run-CSV columns cannot express.

Consequence, exactly as pre-registered: **no pilot baseline is rebuilt on any path**, and the pilot is re-scored on
its logged columns only (section 3.13). `cell_baselines(from_meta=True)` is built and tested on a cell whose
configuration the seven run-CSV columns cannot express (a non-default `b_pred`), where the two constructions give
different paths and only the `meta.json` one matches the run's (`test_baselines_same_path_hash`).

### 3.10 E7.7 — the small items

| item | what was done |
|---|---|
| trader band consistency | `targets.band()` is the single definition and returns (0, 1) for `NONE`/`TRADER`; the four consumers that hard-coded it now agree; `band_mas` uses the persona's own half-width so a band-free arm scores 0; `centre()` unchanged at 0.5; the seven mandated personas untouched, so no prompt that quotes a band moved (P7-11) |
| pre/post-trade shares | `Cash_Share_Pre` and `Cash_Share_Post` added to the run log and to the baseline frames; under `execution="next_open"` the trade record no longer calls the pre-trade share "after" (weakness 60). `Cash_Share` keeps its meaning and its values |
| the cost, stated | **5 bp per trade** on \|traded value\| ⇒ **10 bp round trip**. The two read anchors are different concepts and neither is this number: Nasdaq's 4.5 bp is a *quoted spread* (≈ 2.25 bp per side); FIM's 6.18 bp is *median market impact* per trade. The implemented tier is DESIGN, sitting between them, and says so in the parameter file |
| half-width and dead band | both **DESIGN**, because Donohue & Yip could not be read; the half-width sensitivity {0.05, 0.10, 0.15} is run on the whole re-score (`e7_rescore/cells.parquet` carries all three) and on the pilot (`e7_pilot/pilot_rescore.md`) |
| placebo length | **measured, not asserted** (weakness 60); table below |

<!-- table:e7_placebo -->
From the pilot's own prompt records (`mandate_block_text`); n by arm: {'memory': 11, 'placebo_directive': 9, 'stateful_memory': 3, 'swapped': 9}.

| unit | real directive (mean ± sd, n) | placebo (mean ± sd, n) | ratio placebo/real | Mann–Whitney p |
|---|---|---|---|---|
| chars | 315.5 ± 20.6 (n = 11) | 317.0 ± 0.0 (n = 9) | 1.005 | 0.296 |
| words | 52.9 ± 1.9 (n = 11) | 51.0 ± 0.0 (n = 9) | 0.964 | 0.069 |
| tokens_approx | 68.3 ± 2.5 (n = 11) | 67.0 ± 0.0 (n = 9) | 0.981 | 0.077 |

weakness 60: the matching is TESTED, not asserted. n is small (one model, one seed), so a non-significant p is not evidence of matching -- the ratio and its n are the statement.
<!-- /table:e7_placebo -->

### 3.11 E7.8 — construct validity, the correlation matrix, and the rule that adopted a scoring

<!-- table:e7_sweeps -->
| scoring | family | swept parameter | target metric | registered direction | reversals | outside the interval | monotone |
|---|---|---|---|---|---|---|---|
| A_decomposition | align | [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0] | `mcr_D` | decreasing | 0 | 0 | **yes** |
| A_decomposition | drift | [0.0, 0.002, 0.005, 0.01, 0.02, 0.04] | `band_mas` | increasing | 0 | 0 | **yes** |
| A_decomposition | panic | [0.0, 0.25, 0.5, 0.75, 1.0] | `mdd_pct` | monotone | 0 | 0 | **yes** |
| B_per_window | align | [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0] | `mcr_window_D` | decreasing | 0 | 0 | **yes** |
| B_per_window | drift | [0.0, 0.002, 0.005, 0.01, 0.02, 0.04] | `band_mas` | increasing | 0 | 0 | **yes** |
| B_per_window | panic | [0.0, 0.25, 0.5, 0.75, 1.0] | `mdd_pct` | monotone | 0 | 0 | **yes** |

The cell means with their percentile cluster-bootstrap 95 % intervals over seeds (theta = 0.05, half-width 0.10):

| scoring | family | swept value | target metric | mean [95 % interval] | n cells | n seeds |
|---|---|---|---|---|---|---|
| A_decomposition | align | 0.000 | `mcr_D` | 0.1988 [0.1988, 0.1989] | 1200 | 100 |
| A_decomposition | align | 0.200 | `mcr_D` | 0.1596 [0.1591, 0.1602] | 1200 | 100 |
| A_decomposition | align | 0.400 | `mcr_D` | 0.1200 [0.1194, 0.1207] | 1200 | 100 |
| A_decomposition | align | 0.500 | `mcr_D` | 0.1005 [0.0997, 0.1012] | 1200 | 100 |
| A_decomposition | align | 0.600 | `mcr_D` | 0.0809 [0.0801, 0.0818] | 1200 | 100 |
| A_decomposition | align | 0.800 | `mcr_D` | 0.0416 [0.0409, 0.0421] | 1200 | 100 |
| A_decomposition | align | 1.000 | `mcr_D` | 0.0017 [0.0016, 0.0018] | 1200 | 100 |
| A_decomposition | drift | 0.000 | `band_mas` | 0.0000 [0.0000, 0.0000] | 1200 | 100 |
| A_decomposition | drift | 0.002 | `band_mas` | 0.0836 [0.0816, 0.0855] | 1200 | 100 |
| A_decomposition | drift | 0.005 | `band_mas` | 0.2343 [0.2264, 0.2421] | 1200 | 100 |
| A_decomposition | drift | 0.010 | `band_mas` | 0.3160 [0.3043, 0.3278] | 1200 | 100 |
| A_decomposition | drift | 0.020 | `band_mas` | 0.3570 [0.3419, 0.3713] | 1200 | 100 |
| A_decomposition | drift | 0.040 | `band_mas` | 0.3771 [0.3617, 0.3924] | 1200 | 100 |
| A_decomposition | panic | 0.000 | `mdd_pct` | -16.1985 [-16.9278, -15.5253] | 1200 | 100 |
| A_decomposition | panic | 0.250 | `mdd_pct` | -14.8441 [-15.4450, -14.2722] | 1200 | 100 |
| A_decomposition | panic | 0.500 | `mdd_pct` | -13.2751 [-13.7695, -12.7993] | 1200 | 100 |
| A_decomposition | panic | 0.750 | `mdd_pct` | -11.4369 [-11.7901, -11.0456] | 1200 | 100 |
| A_decomposition | panic | 1.000 | `mdd_pct` | -8.8913 [-9.0834, -8.6815] | 1200 | 100 |
| B_per_window | align | 0.000 | `mcr_window_D` | 0.1937 [0.1928, 0.1946] | 1200 | 100 |
| B_per_window | align | 0.200 | `mcr_window_D` | 0.1566 [0.1556, 0.1575] | 1200 | 100 |
| B_per_window | align | 0.400 | `mcr_window_D` | 0.1187 [0.1176, 0.1198] | 1200 | 100 |
| B_per_window | align | 0.500 | `mcr_window_D` | 0.1004 [0.0992, 0.1015] | 1200 | 100 |
| B_per_window | align | 0.600 | `mcr_window_D` | 0.0819 [0.0808, 0.0830] | 1200 | 100 |
| B_per_window | align | 0.800 | `mcr_window_D` | 0.0444 [0.0435, 0.0455] | 1200 | 100 |
| B_per_window | align | 1.000 | `mcr_window_D` | 0.0069 [0.0060, 0.0077] | 1200 | 100 |
| B_per_window | drift | 0.000 | `band_mas` | 0.0000 [0.0000, 0.0000] | 1200 | 100 |
| B_per_window | drift | 0.002 | `band_mas` | 0.0836 [0.0815, 0.0854] | 1200 | 100 |
| B_per_window | drift | 0.005 | `band_mas` | 0.2343 [0.2260, 0.2428] | 1200 | 100 |
| B_per_window | drift | 0.010 | `band_mas` | 0.3160 [0.3038, 0.3287] | 1200 | 100 |
| B_per_window | drift | 0.020 | `band_mas` | 0.3570 [0.3441, 0.3706] | 1200 | 100 |
| B_per_window | drift | 0.040 | `band_mas` | 0.3771 [0.3620, 0.3924] | 1200 | 100 |
| B_per_window | panic | 0.000 | `mdd_pct` | -16.1985 [-16.9485, -15.4952] | 1200 | 100 |
| B_per_window | panic | 0.250 | `mdd_pct` | -14.8441 [-15.4623, -14.2477] | 1200 | 100 |
| B_per_window | panic | 0.500 | `mdd_pct` | -13.2751 [-13.7760, -12.8000] | 1200 | 100 |
| B_per_window | panic | 0.750 | `mdd_pct` | -11.4369 [-11.7749, -11.0637] | 1200 | 100 |
| B_per_window | panic | 1.000 | `mdd_pct` | -8.8913 [-9.0772, -8.6995] | 1200 | 100 |
<!-- /table:e7_sweeps -->

<!-- table:e7_matrix -->
| scoring | pair | \|r\| across cells | collinear by construction |
|---|---|---|---|
| A_decomposition | band_mas — mcr_B | 0.996 | yes |
| A_decomposition | mcr_B — mcr | 0.978 | yes |
| A_decomposition | band_mas — mcr | 0.976 | no |
| A_decomposition | return_pct — mdd_pct | 0.454 | no |
| A_decomposition | mcr_D — mcr | 0.267 | yes |
| A_decomposition | mcr — turnover | 0.194 | no |
| A_decomposition | band_mas — turnover | 0.193 | no |
| A_decomposition | mcr_B — turnover | 0.179 | no |
| A_decomposition | mcr_D — turnover | 0.101 | no |
| A_decomposition | mdd_pct — turnover | 0.076 | no |
| A_decomposition | band_mas — mcr_D | 0.069 | no |
| A_decomposition | mcr_B — mcr_D | 0.063 | no |
| A_decomposition | mcr — mdd_pct | 0.061 | no |
| A_decomposition | mcr_B — mdd_pct | 0.059 | no |
| A_decomposition | band_mas — mdd_pct | 0.055 | no |
| A_decomposition | mcr_D — mdd_pct | 0.020 | no |
| A_decomposition | return_pct — turnover | 0.015 | no |
| A_decomposition | mcr_B — return_pct | 0.009 | no |
| A_decomposition | mcr — return_pct | 0.009 | no |
| A_decomposition | band_mas — return_pct | 0.006 | no |
| A_decomposition | mcr_D — return_pct | 0.001 | no |
| B_per_window | band_mas — mcr_window_B | 0.999 | yes |
| B_per_window | band_mas — mcr_window | 0.983 | no |
| B_per_window | mcr_window_B — mcr_window | 0.982 | yes |
| B_per_window | return_pct — mdd_pct | 0.454 | no |
| B_per_window | mcr_window_D — mcr_window | 0.242 | yes |
| B_per_window | mcr_window — turnover | 0.197 | no |
| B_per_window | band_mas — turnover | 0.193 | no |
| B_per_window | mcr_window_B — turnover | 0.184 | no |
| B_per_window | mcr_window_D — turnover | 0.097 | no |
| B_per_window | mdd_pct — turnover | 0.076 | no |
| B_per_window | band_mas — mcr_window_D | 0.063 | no |
| B_per_window | mcr_window — mdd_pct | 0.061 | no |
| B_per_window | mcr_window_B — mdd_pct | 0.057 | no |
| B_per_window | mcr_window_B — mcr_window_D | 0.055 | no |
| B_per_window | band_mas — mdd_pct | 0.055 | no |
| B_per_window | mcr_window_D — mdd_pct | 0.026 | no |
| B_per_window | return_pct — turnover | 0.015 | no |
| B_per_window | mcr_window_D — return_pct | 0.011 | no |
| B_per_window | mcr_window — return_pct | 0.009 | no |
| B_per_window | mcr_window_B — return_pct | 0.007 | no |
| B_per_window | band_mas — return_pct | 0.006 | no |

| scoring | collinearity floor | its 95 % interval | half-width | **ceiling** | observed \|r\|(MCR, band-MAS) | below the ceiling |
|---|---|---|---|---|---|---|
| A_decomposition | 0.9907 | [0.9858, 0.9944] | 0.0043 | **0.9950** | 0.9758 | **yes** |
| B_per_window | 0.9983 | [0.9975, 0.9991] | 0.0008 | **0.9991** | 0.9827 | **yes** |
<!-- /table:e7_matrix -->

<!-- table:e7_adopt -->
| scoring | every sweep monotone | failing sweeps | \|r\|(MCR, band-MAS) | ceiling | below ceiling | qualifies |
|---|---|---|---|---|---|---|
| A_decomposition | yes | — | 0.9758 | 0.9950 | yes | **yes** |
| B_per_window | yes | — | 0.9827 | 0.9991 | yes | **yes** |

**Adopted: A_decomposition** — both qualify; REG-12's tie-break adopts A, for comparability with the pilot
<!-- /table:e7_adopt -->

**Reading.** Every sweep is monotone under both scorings, with **zero** reversals — the metrics do move with the
constructs they are supposed to measure. Both scorings are below their ceiling, so REG-12's tie-break adopts **A,
the decomposition**, for comparability with the pilot.

**And the number the rule does not capture must be said plainly.** |r|(MCR, band-MAS) is **0.976**; it passes only
because the ceiling it is compared with is **0.995**, and the ceiling is that high because it is derived from a
family with no directional variation at all. On the 16A policy set alone — the population the paper's claims are
about — the correlation is **0.981** (addendum 2a), so this is not an artefact of the scripted sweeps. **On this
environment MCR and band-MAS are near-duplicates.** That is v1's ISFJ-MAS-versus-cash-share collinearity
(r = −1.000) in a milder form, and it is exactly what E7.8(b) asks to be named.

**And the matrix says what to do about it.** The decomposition separates the collinear part from the part that is
not: |r|(B, band-MAS) = **0.996** — B *is* band-MAS restricted to the resolvable steps, as pre-registered — while
|r|(**D**, band-MAS) = **0.069** and |r|(D, MCR) = **0.267**. The directional term is very nearly orthogonal to band
adherence. So the answer to "MCR duplicates band-MAS" is not to drop MCR but to report **D**: it is the component
that carries what band adherence does not, it is the term item 52 asked for, and on the pilot it is what
distinguishes INTJ's failure (out of mandate: B 0.376, D 0.017) from ISFJ's memory arm (in the band, wrongly
directed: B 0.076, D 0.155).

### 3.11b Is the adoption a property of the evidence, or of the θ it was read at?

PREREG 4.2–4.3 fixes the rule but **not the θ the matrix is computed at**; section 3.11 used 0.05, the Phase-6
checkpoint value, and that choice was never pre-registered. A verdict that hinged on it would be a verdict about an
arbitrary reporting choice, so the whole rule — every sweep's monotonicity *and* |corr(MCR, band-MAS)| against its
own ceiling — was re-evaluated at every θ in the re-score and every half-width in E7.7's sensitivity.

<!-- table:e7_adopt_robust -->
REG-12's rule re-applied at **every** theta in the re-score (9) and **every** half-width in E7.7's sensitivity (3) — 27 combinations in all.

| outcome | combinations |
|---|---|
| adopts **A** (the decomposition) | **27 of 27** |
| adopts B (per-window) | 0 |
| adopts neither | 0 |

**The verdict does not depend on the theta it is read at.** Worst margin for A across all 27 combinations (ceiling minus observed): **0.0024**.
<!-- /table:e7_adopt_robust -->

**Reading.** A is adopted in all 27 combinations, so the verdict is not an artefact of the unregistered θ. The
margin is thin, though — the worst is +0.0024 of correlation — which is the same fact as section 3.11's: the
observed correlation and its ceiling are both within a hundredth of 1, and the rule discriminates in that narrow
band rather than anywhere comfortable.

### 3.12 16A re-stated under the Phase-7 scorings — a consequence, beside the Phase-6 verdict

<!-- table:e7_16a -->
Phase 6's verdict, which stands: G1 FAIL, G2 FAIL, G3 PASS, G4a FAIL, G4b FAIL.

| statistic the gate is read on | G1 (4 of 4) | G2 (≥ 3 of 4) | G4a (4 of 4) |
|---|---|---|---|
| MCR — the Phase-6 statistic | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** |
| B, the band-violation term | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** |
| D, the directional term | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** |
| MCR per 25-day window (REG-12 B) | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** | 0 of 4 — **FAIL** |

| G3 reading | flat | bull_trap | crash | sustained_bull | verdict |
|---|---|---|---|---|---|
| daily | median 2, share 0.76 | median 2, share 0.61 | median 4, share 0.90 | median 2, share 0.77 | **PASS** |
| per_window | median 2, share 0.60 | median 1, share 0.39 | median 2, share 0.63 | median 2, share 0.57 | **FAIL** |
<!-- /table:e7_16a -->

**Reading.** This is the answer to the execution prompt's warning that "the temptation to make 16A pass by choosing
a scoring is exactly what rule 2 forbids": **there is nothing to be tempted by.** G1, G2 and G4a fail 0 of 4 on
MCR, on the band-violation term, on the directional term and under per-window scoring. The best trivial policy is a
constant band edge under every statistic but B on flat paths — which is G1's failure mechanism, unchanged by any
decomposition: in a directional scenario the true-V oracle *rests* at one edge, so a policy that sits there scores
like it.

The daily G3 reproduces Phase 6 exactly (medians 2 / 2 / 4 / 2; shares 0.76 / 0.61 / 0.90 / 0.77), which is a
cross-check on the whole regenerated panel.

### 3.12b The half-width sensitivity, applied where it bites: the gates

The half-width is **DESIGN** — no source for it could be read — so every verdict that depends on it has to be shown
at all three registered values, not only at the one in force. Section 3.13 shows it on the pilot; this shows it on
the gates, which is where a DESIGN parameter changing a verdict would matter most.

<!-- table:e7_half_width -->
G1, G2 and G4a on each of the four statistics, at every half-width in E7.7's DESIGN sensitivity ([0.05, 0.1, 0.15]) and every theta (9) — 27 slices x 4 statistics x 3 gates.

| gate that passes anywhere | half-width | theta |
|---|---|---|
| `mcr_B_G2` | 0.05 | 0.002 |
| `mcr_B_G2` | 0.05 | 0.03 |
| `mcr_B_G2` | 0.05 | 0.032791 |
| `mcr_B_G2` | 0.05 | 0.046321 |
| `mcr_B_G2` | 0.05 | 0.05 |
| `mcr_B_G2` | 0.05 | 0.065609 |
| `mcr_B_G2` | 0.05 | 0.08 |
| `mcr_B_G2` | 0.05 | 0.12 |
| `mcr_window_G2` | 0.05 | 0.002 |

| half-width | G3 (daily) passes at | observables oracle at theta 0.05: MCR = B + D |
|---|---|---|
| 0.05 | 0.002, 0.03, 0.032791, 0.046321, 0.05 | 0.0714 = 0.0426 + 0.0289 |
| 0.10 | 0.002, 0.03, 0.032791, 0.046321, 0.05 | 0.0597 = 0.0011 + 0.0586 |
| 0.15 | 0.002, 0.03, 0.032791, 0.046321, 0.05, 0.065609 | 0.1082 = 0.0000 + 0.1082 |
<!-- /table:e7_half_width -->

**Reading, and it needs stating carefully.** G1 and G4a fail in every one of the 27 × 4 slices. **G2's ordering
does appear in nine of them** — eight on the band-violation term B at a half-width of 0.05, one on per-window MCR
at the same half-width. That is *not* "G2 passes", and the report will not be read as saying so: G2 as registered
is about **MCR** at the deployed half-width, and on MCR it fails 0 of 4 everywhere. What the nine slices say is
something narrower and genuinely useful — **at a narrow band the fitted `log(P/SMA50)` rule sits outside the
mandate more often than the field-bearing oracle does.** The rule's advantage over the oracle at the deployed
half-width therefore lives in the *directional* term, not in band adherence. That is a diagnostic about where G2's
failure comes from, and it is exactly the kind of thing the decomposition was built to expose. It is reported here
and nowhere claimed as a checkpoint result (hard rule 2).

**One artefact, named so it is not mistaken for a finding.** G3 flips to PASS at θ = 0.0656 when the half-width is
0.15 (bull-trap median 1 → 2, share 0.49 → 0.52). Oracle switches count crossings of ±θ and cannot depend on the
band's width — except through the *first* target, which is the start allocation clipped into the band. A wider band
clips it less, which can add one switch on a borderline path. It moves a borderline median, not the phenomenon, and
G3's verdict at the deployed half-width is unchanged.

### 3.13 The pilot re-scored, with the published figures beside

<!-- table:e7_pilot -->
The re-score reproduces `generated/pilot_report_per_run.csv` run by run: 52 of 52 runs matched, worst absolute difference in `mcr_0.05` **2.220e-16** — the decomposition is a decomposition of exactly the statistic that was published.

| persona | arm | n (published / T200) | MCR as published | MCR in the note | MCR now (T200) | B | D | MCR per window | oracle switches | share outside band | norm_MCR in the note (v2-era) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ENTJ | memory | 4 / 3 | 0.2414 | 0.26 | 0.3218 | 0.2403 | 0.0816 | 0.3145 | 0.3 | 0.305 | 0.81 |
| ENTJ | placebo_directive | 3 / 3 | 0.2695 | — | 0.2695 | 0.1986 | 0.0709 | 0.2643 | 0.3 | 0.324 | — |
| ENTJ | stateful_memory | 1 / 1 | 0.3167 | — | 0.3167 | 0.2533 | 0.0633 | 0.3050 | 0.0 | 0.317 | — |
| ENTJ | static | 4 / 3 | 0.2101 | 0.25 | 0.2743 | 0.2049 | 0.0694 | 0.2698 | 0.3 | 0.333 | 0.82 |
| ENTJ | swapped | 3 / 3 | 0.9396 | 0.94 | 0.9396 | 0.7792 | 0.1603 | 0.9385 | 0.3 | 0.998 | 0.02 |
| INTJ | memory | 3 / 3 | 0.3610 | 0.36 | 0.3610 | 0.3266 | 0.0344 | 0.3607 | 0.3 | 0.937 | 0.44 |
| INTJ | placebo_directive | 3 / 3 | 0.3937 | — | 0.3937 | 0.3766 | 0.0171 | 0.3989 | 0.3 | 0.986 | — |
| INTJ | stateful_memory | 1 / 1 | 0.3206 | — | 0.3206 | 0.2944 | 0.0262 | 0.3257 | 0.0 | 0.800 | — |
| INTJ | static | 3 / 3 | 0.3925 | 0.39 | 0.3925 | 0.3756 | 0.0168 | 0.3979 | 0.3 | 0.989 | 0.38 |
| INTJ | swapped | 3 / 3 | 0.4771 | 0.48 | 0.4771 | 0.3993 | 0.0779 | 0.4789 | 0.3 | 0.998 | 0.19 |
| ISFJ | memory | 4 / 3 | 0.2342 | 0.23 | 0.2310 | 0.0764 | 0.1545 | 0.2288 | 0.3 | 0.841 | 0.79 |
| ISFJ | placebo_directive | 3 / 3 | 0.2338 | — | 0.2338 | 0.1827 | 0.0512 | 0.2316 | 0.3 | 0.884 | — |
| ISFJ | stateful_memory | 1 / 1 | 0.2159 | — | 0.2159 | 0.0462 | 0.1697 | 0.2203 | 0.0 | 0.606 | — |
| ISFJ | static | 4 / 3 | 0.2514 | 0.23 | 0.2141 | 0.1586 | 0.0555 | 0.2098 | 0.3 | 0.874 | 0.79 |
| ISFJ | swapped | 3 / 3 | 0.5949 | 0.60 | 0.5949 | 0.5155 | 0.0794 | 0.6031 | 0.3 | 1.000 | 0.23 |

The prose figures in `PILOT_NOTES.md` against the table they were written from:

| persona | arm | MCR in the prose | MCR in the table | agrees to 2 dp | norm in the prose | norm in the table | agrees to 2 dp |
|---|---|---|---|---|---|---|---|
| ISFJ | static | 0.23 | 0.2514 | **no** | 0.79 | 0.7501 | **no** |
| ISFJ | memory | 0.23 | 0.2342 | yes | 0.79 | 0.7799 | **no** |
| ISFJ | swapped | 0.60 | 0.5949 | **no** | 0.23 | 0.2293 | yes |
| ENTJ | static | 0.25 | 0.2101 | **no** | 0.82 | 0.8708 | **no** |
| ENTJ | memory | 0.26 | 0.2414 | **no** | 0.81 | 0.8366 | **no** |
| ENTJ | swapped | 0.94 | 0.9396 | yes | 0.02 | 0.0241 | yes |
| INTJ | static | 0.39 | 0.3925 | yes | 0.38 | 0.3756 | yes |
| INTJ | memory | 0.36 | 0.3610 | yes | 0.44 | 0.4440 | yes |
| INTJ | swapped | 0.48 | 0.4771 | yes | 0.19 | 0.1953 | **no** |
<!-- /table:e7_pilot -->

**Reading.** The decomposition earns its place here. INTJ's regret is **96 % band violation** (static: MCR 0.3925 =
B 0.3756 + D 0.0168) and it sits outside its band on 98.9 % of resolvable steps — INTJ under-holds cash and is
simply out of mandate, not wrongly directed. ISFJ's memory arm is the opposite: B 0.0764, D 0.1545 — inside the
band, on the wrong side of the oracle. Under MCR alone those two look similar (0.36 vs 0.23); under the
decomposition they are different failures. The swapped arm sits at the extreme on both terms (ENTJ: B 0.7792,
outside the band on 99.8 % of steps).

**No normalised value is recomputed**, because a normalised value needs baselines on the cell's own path and no
pilot path reproduces. The published `norm_mcr` figures are v2-era numbers, kept for the record and not carried
forward.

### 3.14 The switches, and the proof that they are inert when off

| switch | default | proved inert by |
|---|---|---|
| `metrics_v2.score_run(scoring=)` | `"v2"` | `test_score_run_v2_inert` — the v2 dict key-for-key and value-for-value; `"v2_1"` only *adds* `v21_*` keys and changes no v2 key |
| `metrics_v2.floors_and_ceilings(convention=)` | `"v2"` | `test_floors_and_ceilings_v2_inert` — identical dict; the v2 MCR ceiling is still constant-mix |
| `metrics_v2.THETAS` | the module constant | unchanged at (0.03, 0.05, 0.08); only `thetas_in_force()` reads the file, and `test_scoring_params_absent_keeps_v2_thetas` covers the file-absent path |
| `PortfolioV2(dividends=)` | `False` | `test_dividends_switch_inert_on_baselines` — every baseline's every finite metric identical; `pay_dividend` is a no-op returning 0.0 |
| `PortfolioV2` next-open record | — | `test_portfolio_next_open_logs_pre_and_post` — no computed value changes; one mislabelled key becomes two labelled ones |
| `report_v2.cell_baselines(from_meta=)` | `False` | `test_baselines_same_path_hash` — the two constructions agree except where the run-CSV columns cannot express the configuration, which is the point |
| `evaluation/params/scoring.json` | absent ⇒ `PRESENT is False` | `test_scoring_params_absent_keeps_v2_thetas` — every consumer keeps its v2 constant |

### 3.14b The whole test tree, and the one older test the new state broke

Rule 10 says run the whole tree, and the reason is that the older tests are what break. This one did.

**First full run (65 min, `e7_tests_full.log`): 190 passed, 1 skipped, 4 strict xfails, and 1 failed.** The single
failure was **`tests/test_v2_1_phase_0.py::test_gate_common_start_only`** — a Phase-0 test of the same name as this
phase's, asserting the contract Phase 0 wrote and Phase 7 deliberately replaced: that
`exploratory_deltaC1_start_at_target` is present with a `note` column. E7.5 removed that table (P7-7), so the
assertion could not hold.

Phase 0's own comment said the table was kept "with the reason; Phase 7 (E7.5) re-specifies it". Phase 7
re-specified it by removing it, so the test was updated to the replacing contract rather than weakened
(P7-16): item 54's substance — **no gate verdict is ever produced from start-at-target rows** — is still asserted;
the two clauses that named the withdrawn table now assert its absence *and* that the removal announces itself in
`gate_removed_note`; and the gate's null is asserted to report `NOT COMPUTABLE` where no no-persona arm exists, so
the change cannot become silent later. `tests/test_eval_v2.py::test_report_end_to_end` asserts only
`"gate_common_start" in st` and was unaffected.

**Confirmation run after that edit (`e7_tests_full2.log`, 1:00:20): 191 passed, 1 skipped, 4 strict xfails, 0
failed.** The four strict xfails are the known-defect registry's two derived-gate entries
(`test_v2_L2_surrogate_thresholds`, `test_v2_L2b_phase_clock_selectivity`) and the two permanent v1 baseline
defects; none is this phase's to clear, and none XPASSed — the registry is neither emptied nor quietly broken. The
skip is the L3 probe, which waits on D2.

The slowest calls, for whoever runs this next: `test_leakage_ci.py::test_v2_L1_no_algebraic_inversion` 1,128 s
(setup), `test_v2_1_phase_1.py::test_start_price_carries_no_information` 877 s,
`test_v2_1_phase_6.py::test_audit_switches_inert` 564 s.

### 3.15 The tuned-parameter ledger (weakness 7), Phase 7's rows

| parameter | value | label | what moved, when, against what |
|---|---|---|---|
| θ (co-primary) | θ_info 0.05, θ_cost 0.0020 | **DERIVED** | never tuned. Derived once from the audit's surrogate and from the cost/half-life identity; written to the parameter file only after D7 and D8 |
| θ_var | 0.046321 | **DERIVED** | read from `e6_after_checklist_reference_extra.csv`; not re-estimated here |
| half-width | 0.10 | **DESIGN** | unchanged since v2; never fitted (Donohue & Yip not retrievable); the {0.05, 0.10, 0.15} sensitivity is run on every re-score |
| dead band | 0.01 | **DESIGN** | unchanged since v2; not varied in this phase; it is why the v2.1 ceiling is 0.0028 rather than 0 |
| cost tier | 5.0 bp per trade | **DESIGN** | unchanged since v2; now labelled as sitting between a 2.25 bp half-spread and a 6.18 bp market-impact median, neither of which it is |
| bands | 0.70–0.90 / 0.40–0.60 / 0.00–0.20 | **READ** (practitioner) | unchanged; the sources are now in the code's docstring, and the utility-consistent alternative is computed and reported, not scored |
| `JFE_SPREAD` | withdrawn | — | removed this phase; the source does not contain it |
| window (per-window scoring) | 25 days | **REGISTERED** | built as REG-12's alternative; **not adopted** |

### 3.16 Path hashes and the freeze

This phase changes no generator path. The 95-configuration fixture is regenerated and compared with the Phase-6
fixture (`path_hashes_phase7_after.json`, `path_hashes_phase7_compare.json`): **0 of 95 configurations changed**.
The freeze manifest is re-written to cover the files this phase added (`evaluation/scoring.py`,
`evaluation/scoring_params.py`, `evaluation/params/scoring.json`, `simulation/dividends.py`).

---

## 4. Decisions taken and the parameter file

`evaluation/params/scoring.json`, written by `tools/phase7/e7_write_scoring_params.py` from the result files and
read back through the loud loader `evaluation/scoring_params.py`. Twelve blocks, each with `value`, `status`,
`label`, `source`, `date`, `interval` and `n`; `theta_in_force` written **only after** D7 and D8 were recorded.

Decisions: **P7-1** (D17 = restrict the claim) · **P7-2** (D10 = pay dividends) · **P7-3** (D9 = A the scored
default) · **P7-4** (D7 = co-primary as registered) · **P7-5** (D8 = the θ-conditional pass) · **P7-6** (the JFE
spread withdrawn) · **P7-7** (the day-1 gate) · **P7-8** (the pilot on logged columns only) · **P7-9** (scoring A
adopted, and its collinearity) · **P7-10** (dividends on the announcement day; no ex-dividend price adjustment) ·
**P7-11** (the trader band-free) · **P7-12** (16A re-stated, nothing flips) · **P7-13** (the panel regenerated and
verified) · **P7-14** (`PILOT_NOTES.md` corrected against its own table).

---

## 5. Decisions the team must take

**None is blocking this phase**, which is complete. What is carried:

| decision | state |
|---|---|
| **D2** (the LLM roster and budget) | open since Phase 5; this phase made no API call and does not need it. Phase 8's E8.5 variance pilot and Phase 6's L3 probe both wait on it |
| **D15** (sentiment's valuation loading) | open; not this phase's. The realised next-day slope 0.00055 [0.00046, 0.00063] against the configured 0.0008 still stands |
| **The all-rows L2 centred reading** | still undecided at 40 draws (a 0.0004 gap on a 0.0148 half-width). Deciding it needs a larger panel; **the team is asked whether to spend that compute**, since nothing in this phase or Phase 9 depends on it |
| **Reading B for the bands** | E7.3 shows that no γ in the plan's grid lands in the balanced or the aggressive band. D9's default (A) stands, but the team should know that the utility-consistent alternative would collapse the personas into one band — Phase 9 carries both as a factor and will measure the interaction |

---

## 6. Files written or changed

`PHASE_7_CHANGED_FILES.md`, generated from git (`22d572d..HEAD`) and the working tree by
`tools/phase7/e7_changed_files.py` and verified against disk by its `--check`.

**On compute.** The box was probed at the start of the session and answered — `zhangf-6dffcfb96-nvf7l`, 128 cores,
two idle RTX 4090s, `sklearn 1.9.0 / numpy 2.4.6` matching the laptop — and **was not used**, for two reasons that
are worth recording rather than leaving implicit:

1. **The GPU cannot legitimately accelerate this phase's one heavy stage.** θ_info's surrogate must be the *audit's*
   `HistGradientBoostingRegressor`; substituting a GPU tree library would change the estimator and make θ_info
   incomparable with the Phase-6 sign accuracies it is verified against (rule 12: one tool, one construction). What
   the box offers is cores, not a different estimator.
2. **It was not needed.** The stage the execution prompt budgeted at ≈ 100 s × 5 folds × 2 feature sets took
   **84 s** on the laptop at four workers, and the largest stage in the phase — the 12 M-row policy panel — took 13 min (774 s at five workers).
   Getting new Phase-7 code onto the box needs a push to the public repo through the per-file `raw.githubusercontent`
   route (P6-1), which is not done without being asked.

Nothing in this phase touched `datasets/`.

---

## 7. What was not done, and who owns it

| item | state | owner |
|---|---|---|
| **The known-defect registry** | **not emptied, and not touched.** Both entries are the derived L2 and L2b gates; no re-scoring can pass them and none was attempted. They are statements about the surrogate's R²(x) against a permutation null, not about a scoring | D17's chosen option, if one is ever taken; carried |
| **The all-rows L2 centred reading** | undecided at 40 draws; needs a larger panel | the team (section 5) |
| **Reading B scored** | computed and reported; **not scored**. D9 keeps A as the default and Phase 9 carries both as a factor | Phase 9 |
| **The day-1 gate's null** | the machinery is built and tested; the pilot has no no-persona arm at common start, so the null is `NOT COMPUTABLE` there | Phase 9's grid, which includes those arms |
| **The pilot's normalised values** | not recomputed and not recoverable: no pilot path regenerates | closed — the pilot is a pipeline check, and Phase 9's runs will carry reproducible paths |
| **A longer horizon as a factor** | 16A's admissible response (i) to G3; not run here (it needs new LLM runs and a Phase-2/6 re-run) | Phase 9, if the team wants it |
| **θ_info per scenario from a held-out-scenario surrogate** | **not computed.** The per-scenario values in 3.1 are the *pooled* surrogate's predictions restricted to a scenario's rows; P6-14 says a surrogate that never saw a scenario is a different thing. Only the pooled values enter the parameter file, and section 3.1 says so | Phase 9, if it quotes a per-scenario θ |
| **Merton's own assumption** | the formula assumes geometric Brownian motion; this environment mean-reverts (an AR(1) mispricing at a 22.4-day half-life) and has fat tails, so w\* = (μ − r)/(γσ²) is the plan's specified estimator applied outside its model. Stated as a limitation; a mean-reversion-aware optimum was not computed | D3 / Phase 9 |
| **`evaluation/criteria.py` and `params/phase6_criteria.json` outside the freeze patterns** | Phase 6 added them without extending `V2_FREEZE_PATTERNS`; Phase 7 extended the patterns for its own scoring layer but did not retro-fit Phase 6's. The inconsistency is recorded, not fixed | Phase 8 or 10 |
| **Item 7** (log-volume normality) and **item 12** (sentiment's loading) | carried, unchanged | D15's owner; the checklist's reading |
