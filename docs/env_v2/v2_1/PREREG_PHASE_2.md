# Pre-registration, Phase 2 (v2.1): the mispricing engine and its persistence

Status: **written 1 September 2026, before any Phase-2 experiment was run.** Working tree on `main` at commit
`d6e3b24` (the v2.1 Phase-1 state; `tests/v2_freeze_manifest.json` label "v2.1 Phase 1 freeze"), plus the untracked
`PHASE_2_EXECUTION_PROMPT.md`. Governing documents: `V2_1_IMPROVEMENT_PLAN.md` Section 6 (Phase 2) with Sections 1,
3, 16, 16A, 17 and Appendices A–B; `V2_1_ALTERNATIVES_REGISTER.md` REG-2, **REG-4**, **REG-5**, REG-15;
`PREREG_PHASE_1.md` and `PREREG_PHASE_1_ADDENDUM.md`; `PHASE_1_REPORT.md`.

**Team decisions in force.** D1 = C (hybrid: fit on the free panel, publish every fitted value with its
survivor-vs-literature gap, keep the code re-runnable on WRDS by a data-path change; WRDS **not** confirmed).
D13 = mechanism **C** (`start_price_mode = "both"`). D16 = full programme. **D3's application blank in the
execution prompt is empty, so the prompt's default applies: option (b)** — σ_V is *not* applied before Phase 2;
it enters E2.3 as a **free parameter**, jointly identified with the engine's pull rate, and the fitted value with
its interval is what gets written to `value.json`. Until E2.3 reports, the value in force stays v2's stipulated
0.006 and every pre-Phase-2 run below (E2.1, the power pilots) is unaffected by it.

Everything below — seeds, horizons, moment vectors, weight matrices, estimators, statistics, optimiser settings,
sample sizes, pass/decision rules and what is reported when a rule is not met — is fixed here and is **not moved
after any number is seen**. If a criterion turns out to be wrong, `PHASE_2_REPORT.md` says so, the replacement is
derived in a separately documented step in `PREREG_PHASE_2_ADDENDUM.md` **before** the re-run, with disclosure of
what had already been seen, and the result is reported under both.

---

## 0. Provenance labels, the citation rule, and what was already seen when this was written

LIT / FIT / CAL / DESIGN as the plan defines them. Every number that enters `envs/v2/params/mispricing.json`,
`value.json`, a test tolerance or a document in this phase is FIT on the panel of §2, or DESIGN with the
alternatives and the discriminating experiment named, or CAL carried from v2 with that label. Literature values
are quoted **beside** fitted values, never as tolerances.

**Sources read at first hand for this pre-registration (1 September 2026), with status:**

| Source | What was read | Status |
|---|---|---|
| Franke & Westerhoff 2012, JEDC 36:1193–1211 (PDF at the Bamberg URL of PLAN §0.2; 36 pp.) | eqs (1), (5)–(7), (DCA), (HPM); Table 1 DCA-HPM (φ 0.12, χ 1.50, α_o −0.327, α_n 1.79, α_p 18.43, σ_f 0.758, σ_c 2.087; μ = 0.01, β = 1 normalisations); Table 2 p = 32.6 %; **Table 4 DCA-HPM moment coverage ratios**; **Table A1 empirical moments with 95 % CIs**; Appendix A2 (block bootstrap 250/750 d, B = 5,000, W = Σ̂⁻¹); eq. (9) (the p-value construction) | **read-and-correct** — every value the repository attributes to FW 2012 is confirmed |
| SABCEMM (Trimborn, Otte, Cramer et al.), arXiv:1812.02726 | Table 1 (model contest, 200 runs × 7,000 steps) and Tables 6–12 (the parameter sets used) | **read-and-WRONG in the plan** — see §3.1; corrected here |
| Pruna, Polukarov & Jennings 2016, arXiv:1604.08824 | eqs (9)–(10) and Table 1 (φ 0.121, χ 1.555, σ_f 0.592, σ_c 1.917, α_0 −0.301, α_n 1.990, α_p 22.741, μ_p 0.01, σ_p 0.157) | **read-and-correct** for the parameters in `envs/v2/mispricing.py::PRUNA_2016`; the **units of σ_p are not resolvable from the paper** (it is called "percentage volatility" of a GBM in p^f while p^f enters the model as a log value), so σ_p is **not** used as a value or a tolerance anywhere in Phase 2 — the fundamental's volatility is fitted (§4) |

**Disclosure of what had been seen when this document was written** (the Phase-1 addendum's rule, applied in
advance rather than after the fact):

1. The **panel's pooled 17-moment vector** (§4.1) was computed while this document was being written, because the
   weight matrix is part of the design. Its values are printed in §4.1. No criterion below is a function of them.
2. A **pilot of FW's own model** at `price_scale = 1` was run to establish decidability: 12 independent pilots of
   20 runs × 6,750 steps (seeds 770001–770012) gave a joint moment-coverage ratio of **0.104**, a mean chartist
   share of **0.292** and a mean excess kurtosis of **1.79**. A single further 200-run pilot (seed 101) gave a
   joint MCR of 10.5 % and the per-moment coverage profile now quoted in §3.3. **These numbers already tell me
   that E2.1 will confirm FW's own joint MCR and will not reproduce SABCEMM's summary row.** The criteria in §3
   are therefore written with that knowledge and are stated as *reproduction checks against published values*,
   not as thresholds I could tune; the registered run uses fresh seeds (§2) and reports both conventions and both
   published targets whatever they show.
3. Nothing about E2.2–E2.6 has been run. The Phase-1 results this phase inherits (`e1_2/`, `e3_1/`) were read.

---

## 1. What is inherited, what is re-derived, and what is verified before use

**Inherited and not redone** (PHASE_1_REPORT.md §4.2, `e1_2/recovery.md`, 32 cells):

- Estimator **A** (variance ratios) is never usable: median relative error 0.11 → 20.0 as h grows, interval
  coverage 0.00–0.01. Estimator **B** (log(P/V̂) AR(1)) returns ĥ ≈ 36–47 d whatever the truth and the same on a
  panel with x ≡ 0. Estimator **C** (SMM) is usable for h ≤ 150 d (median relative error 0.03–0.16) and unusable
  at h ≥ 250 d. **E2.2 does not repeat the recovery study**; it applies REG-5's disagreement rule to this verdict.
- The diagnostic that A recovers h on an *exact* random-walk + AR(1) panel (ĥ 30.4 / 147 for truths 30 / 150) but
  not on the engine's panels — i.e. the engine's x is not an AR(1). This is E2.4's motivation, not its conclusion.
- E3.1's per-stock GJR-GARCH(1,1)-t medians (set A, full sample, n = 417): α 0.027, γ 0.058, β 0.932, ν 4.86.
  These are the **fixed** GARCH shape inside E2.3's simulator; only the unconditional scale `sbar` is free.
- μ_V = 0.0002281/day (FIT), df_V = 5 (DESIGN), the E1.4 jump placement and the E1.5 burn-in.

**Verified before use** (the "verify inherited numbers, including mine" rule). Every one of these checks is run
and its outcome reported in `PHASE_2_REPORT.md` §1, whether or not it agrees:

| # | Inherited claim | Where it is checked |
|---|---|---|
| V1 | `mispricing.py`'s FW parameter set equals FW 2012 Table 1 DCA-HPM | source read (§0); `tests/test_v2_1_phase_2.py::test_fw_index_params_match_source` |
| V2 | `mispricing.py`'s `PRUNA_2016` equals Pruna Table 1 | source read (§0); same test |
| V3 | The plan's SABCEMM target "0.23 / 7.8" | **already found wrong** — §3.1 |
| V4 | The engine's pull-rate half-life 150.0 d and long-pilot ACF(1) half-life 147 d (Phase 0, P0-6) | recomputed in E2.5 |
| V5 | The pilot constants n̄ = 0.99765, w̄ = 0.76113 that fix φ (P0-8: "Phase 2 re-derives φ anyway") | recomputed in E2.3/E2.5 |
| V6 | Phase 1's s_x_fit 0.129 and h_fit 4.82 d in `value.json` equal `e1_2/decision.json` | `tests/test_docs_numbers.py` extension |
| V7 | The engine's residual E[x] = +0.0113 [+0.0027, +0.0199] with jumps off (`e1_4/confirm_jumps_off.json`) | re-measured on the engine E2.4 adopts, at 1,000 flat paths |

---

## 2. Seeds, panels, sample sizes (fixed; all fresh — disjoint from Phase 0's 9001–20000 and Phase 1's 30000–90000)

| Block | Purpose | Seeds | Size |
|---|---|---|---|
| PW | Power pilots (§9) | 770001–770499 | as stated per block |
| FW1 | E2.1, FW's own model, both conventions | 100001–100199 | 200 runs × 7,000 steps (SABCEMM arm); 200 × 6,750 (FW arm) |
| SM | E2.3 SMM common random numbers | 110001 (+ 13·k for the k-th CRN replicate) | 20 paths × 5,000 d per evaluation (raised only by §9's rule) |
| SB | E2.3 bootstrap refits | 112001–112030 | 30 refits |
| MC | E2.3/E2.4 acceptance Monte Carlo | 113001–113200 | 200 replicates × (417 paths × T_period d) |
| HL | E2.5 half-life table | 120001–120200 | 200 seeds per (h, T) cell |
| SW | E2.6 persistence sweep | 130000–130199 (checklist, 4 scenarios), 131000–131099 (level-free audits) | 200 / 100 seeds |
| EQ | E2.4(c) equivalence panels | 140000–140199 | 200 seeds × 4 scenarios per engine |

**Panel (unchanged from Phase 1, D1 = C).** `tools/phase1/panel.py::PanelSpec` with the Phase-1 exclusion rule;
**set A = 417** flag-free full-history names, 2000-01-03 … 2024-12-31, daily log returns of `Adj Close`,
**6,289 trading days**. Survivorship (REG-15): set A has no delistings by construction, so every tail and
unconditional-variance statistic below understates the full universe; the gap is printed beside each value.

**E2.3 / E2.4 periods (fixed here).** `full` = 2000-01-03…2024-12-31; three sub-periods `p1` 2000–2008,
`p2` 2009–2016, `p3` 2017–2024; `train` = 2000-01-03…2016-12-31 and `test` = 2017-01-01…2024-12-31 for E2.4(b)
(the plan's "fit 2000–2016, predict 2017–2024"). These are **not** `panel.py`'s four Phase-1 sub-periods; E2.2
reports the Phase-1 four as well, so the two phases stay comparable.

---

## 3. E2.1 — FW's own model reproduced, and a correction to the plan's target

### 3.1 The correction (found at source **before** any Phase-2 run)

The plan (§6.1 and §6.2, marked "[changed: LOG §4.2]") states: *"SABCEMM contest (arXiv:1812.02726; read):
DCA-HPM average chartist share 0.23, excess kurtosis 7.8 (200 runs × 7,000 steps); the first draft's '0.17 / 10'
pair is the DCA-WHP row."* **This is wrong, and it inverts the first draft's correct reading.** SABCEMM's Table 1,
read at source on 1 September 2026 (200 runs × 7,000 time steps, parameters of their Tables 6–12):

| model | excess kurtosis | Hill estimator | average chartist share |
|---|---|---|---|
| DCA-W | 8.2023 | 3.173 | 0.2577 |
| DCA-WP | 7.7600 | 3.1314 | 0.2285 |
| **DCA-HPM** | **10.033** | **2.481** | **0.1674** |
| DCA-WHP | 8.01 | 3.1192 | 0.2227 |
| TPA-HPM | 8.614 | 2.5833 | 0.1503 |

The "0.17 / 10" pair **is** the DCA-HPM row; the plan's "0.23 / 7.8" is closest to the **DCA-WP** row
(0.2285 / 7.7600) and is not DCA-WHP either. The plan is not edited (the execution prompt forbids it); the
correction is logged as **P2-1** and the corrected values are what E2.1 compares against. Under the plan's own
rule a statistic that is read-and-wrong is corrected where it occurs and the corrected value is used.

### 3.2 The design

Simulate **FW's own model** — their price equation (5) with the two independent Gaussian demand noises (6)–(7),
the DCA switching, the HPM attractiveness index, a constant p\*, **no GARCH, no jumps, no drift** —
at the DCA-HPM parameters of FW Table 1, at `price_scale ∈ {1, 100}` (the multiplier on (p_t − p\*) inside the
misalignment term α_p (s·(p_t − p\*))², which is the only place the units convention bites).
Implementation: `tools/phase2/fw_pure.py` (equations transcribed in its docstring with FW's equation numbers).

Two arms, both at 200 runs (seeds 100001–100200), both conventions:

- **Arm A (primary; FW's own criterion).** T = 6,750 (FW's T′). Per run, FW's nine moments (returns in
  percentage points; ACF(|r|) smoothed by the centred three-lag average of FW's footnote 9; the Hill moment is
  γ̂ on the largest 5 % of |r|, i.e. FW's "1/Hill"). Statistics: the **moment coverage ratio** per moment and the
  **joint MCR** — the share of runs whose moments all lie inside FW's Table A1 95 % confidence intervals — with
  a Wilson interval. Published target: FW Table 4, DCA-HPM column, joint MCR **10.1 %** (their 5,000 replicates).
- **Arm B (secondary; SABCEMM's summary row).** T = 7,000, no burn-in, p\* = p_0 (SABCEMM Table 9), 200 runs.
  Statistics: mean chartist share and mean excess kurtosis of log returns over the 200 runs, each with a 95 %
  interval across runs. Published target: **0.1674 / 10.033** (§3.1). The Hill tail index 2.481 is reported beside.

Both arms are also run with a 500-step burn-in discarded, to show that SABCEMM's zero-burn-in convention is
immaterial (reported, no criterion).

### 3.3 The rule (fixed)

- **A convention is "confirmed" for the misalignment units iff its 95 % interval for the joint MCR (arm A)
  contains FW's published 10.1 %.** Decidability (§9, PA1): at 200 runs the half-width is ±4.2 pp, so an
  interval centred near 10 % contains 10.1 % and one centred near 0 % does not — the criterion separates the two
  conventions by construction.
- Arm B is reported as a **reproduction check with no pass/fail**, because the pilot already shows (disclosure
  §0.2) that FW's published equations as transcribed here give a chartist share of ≈ 0.29 and an excess kurtosis
  of ≈ 1.8 at 200 runs with half-widths of ±0.011 and ±0.038 — i.e. **SABCEMM's DCA-HPM row is not reproducible
  from FW's published equations at their published parameters**, whichever convention is used. Attaching a
  pass/fail to a target I already know fails would be theatre. What is registered instead is a **diagnostic**:
  the report states the discrepancy, quotes the one ambiguity in SABCEMM's own appendix that could explain a
  larger effective price impact (their eqs (5)–(6): `EDF = ½(ed_f + ed_c)` with `ed_f = 2 n_f d_f`, which is
  self-cancelling under one reading and doubles μ under another), and reports the single diagnostic run at
  `μ → 2μ` **as a diagnostic, not as a fit and not as a parameter**. No parameter of any engine is set from it.
- The per-moment coverage profile of arm A is **reported beside FW's Table 4 column** and is *not* a criterion:
  the pilot has already shown it diverges (invHill 23.5 % against FW's 79.5 %), and turning that into a criterion
  after seeing it would be moving a threshold onto data.
- Outcome: if `price_scale = 1` is confirmed and 100 is not, **the units are a bug fix (LIT)**, logged as such,
  and `price_scale = 1` is the convention for every E2.3 fit and for `tests/test_v2_1_stats.py::test_fundamentalist_share`
  (registry entry, items 2 and 11). If *neither* is confirmed, no bug fix is claimed, the incumbent's
  `price_scale = 100` stays in force pending E2.3/E2.4, and the report says the reproduction failed.

---

## 4. E2.3 — the SMM done properly

### 4.1 Moments and the data side (fixed)

**17 moments**, per stock (or per simulated path) and pooled as the cross-sectional mean:

- **FW's nine** (returns in percentage points, r = 100 Δlog P): `rAC1`, `invHill` (γ̂, 5 % tail), `vMean`,
  and the smoothed ACF(|r|) at lags 1, 5, 10, 25, 50, 100.
- **Eight persistence-carrying**: `VR(k)` at k = 20, 60, 120, 250, 500 (Lo–MacKinlay overlapping estimator with
  the small-sample correction — the *same* code E1.2 used, `tools/phase1/e1_2_vr.vr_moments`) and the ACF of
  log(P/SMA250) at lags 20, 60, 120.

Set-A pooled values, computed while writing this document (n = 417 stocks × 6,289 days; disclosure §0.1):

| rAC1 | invHill | vMean | vAC1 | vAC5 | vAC10 | vAC25 | vAC50 | vAC100 | VR20 | VR60 | VR120 | VR250 | VR500 | acf20 | acf60 | acf120 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| −0.0344 | 0.3699 | 1.499 | 0.2634 | 0.2314 | 0.2092 | 0.1633 | 0.1340 | 0.1014 | 0.8653 | 0.7846 | 0.7610 | 0.7239 | 0.6718 | 0.8478 | 0.5926 | 0.2629 |

FW 2012 Table A1 (S&P 500, 1980–2007) beside, as an anchor and never as a tolerance: −0.008 / 0.301 / 0.713 /
0.193 / 0.187 / 0.159 / 0.128 / 0.112 / 0.074. Single stocks are twice as volatile as the index and fatter-tailed,
as expected; the survivor gap (REG-15) is in the same direction for the tails.

### 4.2 The weight matrix (fixed; stored to disk, not a diagonal proxy)

**Joint stock × block bootstrap**, B = 500 resamples per period: stocks are resampled with replacement, and the
time blocks are **shared across the resampled stocks** so the market-factor cross-section survives (E1.2's joint
bootstrap convention). Blocks are re-chained in log-return space so no artificial jump appears at a join. Block
lengths follow FW Appendix A2 and extend it to the persistence moments:

| moment group | moments | block |
|---|---|---|
| short memory | rAC1, invHill, vMean, vAC1, vAC5 | 250 d |
| long memory | vAC10, vAC25, vAC50, vAC100 | 750 d |
| persistence | VR(20…500), acfSMA(20/60/120) | 1,250 d (longest horizon VR500) |

Σ̂ = the bootstrap covariance of the pooled 17-vector; **W = [(1 − s)Σ̂ + s·diag(Σ̂)]⁻¹ with s = 0.10** — a
fixed 10 % ridge toward the diagonal, registered *before* the condition number is known, so that a
near-singular Σ̂ cannot silently drive the fit. The condition number of the shrunk matrix is reported for every
period. Files: `e2_3/data_moments.json`, `data_boot_<period>.npy`, `weight_<period>.npy`.

### 4.3 The simulated model (fixed)

`tools/phase2/engines.py`, one scaffolding for the three REG-4 candidates: log P = log V + x, log V a random walk
with drift μ_V = 0.0002281 and standardised t₅ shocks of daily sd σ_V, **no events, no jumps**, and the
generator's sentiment feedback (b_pred 0.0008, b_rev 0.0006) kept on in **all three** engines so the comparison is
like for like. GARCH shape fixed at E3.1's medians; `sbar` free where the engine has a GARCH innovation.

| engine | x recursion | free parameters (order fixed) | p |
|---|---|---|---|
| `ar1` (REG-4 **B**, the simple one) | x_{t+1} = ρx_t + e_t, ρ = 2^{−1/h}, e GJR-GARCH-t | σ_V, sbar, h | 3 |
| `fw_v2` (REG-4 **A**, the incumbent form) | FW DCA-HPM driven by ONE GARCH innovation through the unit-mean weight (n_f σ_f + n_c σ_c)/w̄ | σ_V, sbar, φ, χ, α_0, α_n, α_p | 7 |
| `fw_plus` (REG-4 **C**, FW+) | FW's own TWO independent Gaussian demand noises (structural stochastic volatility, no GARCH), stochastic fundamental | σ_V, σ_f, σ_c, φ, χ, α_0, α_n, α_p | 8 |

`price_scale` in the two FW engines is the convention E2.1 confirms; if E2.1 confirms neither, both conventions
are fitted and both reported. **σ_V is free in every engine** (D3 = (b)). Search on the log scale for every
positive parameter, natural scale for α_0; bounds in `engines.py::BOUNDS`, fixed here.

Simulation per evaluation: **20 paths × 5,000 days, burn 500, common random numbers** (seed SM, identical across
θ). §9's PA2 measures the simulation noise of every pooled moment in units of the data bootstrap sd; **if any
persistence moment's ratio exceeds 0.30 the path count is raised (20 → 50 → 100) until it does not, before the
fit, and the achieved count is stated** (REG-4's own "to be verified in the SMM diagnostics"). This is the one
design quantity this pre-registration leaves to a measurement, and the rule that resolves it is fixed here.

### 4.4 The optimiser (fixed)

`scipy.optimize.differential_evolution` (`strategy='best1bin'`, `popsize` such that the population is ≥ 8·p,
`tol=0.01`, `mutation=(0.3, 1.0)`, `recombination=0.9`, `polish=False`, `updating='deferred'`, `workers=1`,
`seed` fixed) with an **initial population containing at least 20 named starts**, listed in
`tools/phase2/e2_3_smm.py::START_GRID` and including **chartist-active regions** (FW's own Table 1 set, Pruna's
Table 1 set, small α_p and small α_n where the switching is live) as well as fundamentalist-locked regions
(large α_p, the v2 fallback φ = 0.4632), σ_V at 0.006 / 0.012 / 0.0196 and sbar at 0.012 / 0.017 / 0.025; the
rest of the population is a Latin hypercube inside the bounds. **Nelder–Mead polish** from the DE optimum.
`maxiter` is set by the timing pilot of §9 to fit the compute budget and the achieved evaluation count is
reported; if the budget forces a smaller `maxiter` the reduced design is fixed *before* the run and the report
states the achieved count and marks the verdict undecided if the smaller search cannot decide it.

**Recorded for every fit**: start-J (J at the best named start), end-J, the achieved evaluation count, the
optimiser's convergence flag, θ̂, and **full-parameter J profiles** (each free parameter on an 11-point grid
spanning ±1 order of magnitude around θ̂ on its search scale, the others held at θ̂, CRN fixed).

### 4.5 Acceptance (fixed)

1. **χ² at 5 %.** J = d′W d with d = m_sim(θ̂) − m_data. Accept iff J ≤ χ²_{0.95}(q − p), q = 17, p as in §4.3
   (df = 14 / 10 / 9). The asymptotic χ² ignores simulation noise; the measured inflation (PA2) is reported
   beside, and the report states J, the critical value and the df explicitly.
2. **FW's bootstrap p-value** (FW 2012 eq. (9), reproduced at reduced counts): the **bootstrap** distribution
   {J[m_b]} over the B = 500 block-bootstrap moment vectors of the data gives J₀.₉₅; the **Monte Carlo**
   distribution {J[m_c(θ̂)]} over C = 200 model replicates simulated at the **data's own panel size**
   (417 paths × T_period days) gives the model's spread; **p = share of MC replicates with J ≤ J₀.₉₅**. Accept
   at the 5 % level iff p ≥ 0.05. FW used B = C = 5,000 and one series; ours are 500 and 200 over a 417-stock
   panel — the reduction is stated with its Monte-Carlo standard error (≈ 1.5 pp at p ≈ 0.1, C = 200).
3. **Both** criteria are reported for every engine and period. Acceptance at (a) in E2.4's rule means **the
   bootstrap p**, because it is the non-asymptotic one and it is FW's own; the χ² verdict is reported beside and
   any disagreement between them is stated rather than resolved silently.

### 4.6 Intervals, sub-periods, outputs

Parameter intervals: **30 bootstrap refits** (Nelder–Mead warm-started at θ̂) on 30 of the B moment resamples,
seeds SB — the count Phase 1 used, kept for comparability; the achieved count is stated. Refits are run for the
`full` period for all three engines; sub-period fits report point estimates with start/end J and no refit
interval (stated as a shortfall, with its consequence: sub-period differences are described, not tested).

Outputs: `e2_3/smm_<engine>_<period>.json` (design block, θ̂, J, df, χ², bootstrap p, profiles, start/end J,
seconds), `e2_3/smm.md` (the human table), `e2_3/profiles_<engine>.md`.

---

## 5. E2.2 — the firm-level persistence estimate and REG-5's disagreement rule

No new recovery study (§1). What E2.2 produces:

1. For each of the three estimators, the **cross-sectional median half-life with P25/P75 and per sub-period**:
   A from `e1_2/vr_fit.json` (already has the four Phase-1 sub-periods), B from `e1_2/pv_fit.json`, C from
   E2.3's `fw_v2`/`ar1` fits per period (C's h is the AR(1) half-life for `ar1` and the **pull-rate** half-life
   ln2/(μ n̄ φ) for the FW engines, both reported; they are not the same statistic and the report says so).
2. **REG-5's rule applied to the current estimator set**: an estimator is usable if the recovery study says so;
   *adopt the usable estimator with the smallest RMSE whose data interval contains the other usable estimators'
   point estimates; if the usable intervals are disjoint, adopt none and run E2.6 over the union of the
   intervals.* Since only C survived usability, **the rule adopts C**, and the report states plainly that the
   rule reduces to "adopt the only usable estimator" and carries Phase 1's two qualifications (the recovery
   panels come from C's own model; J = 66.6 on the real panel says the model does not fit it well) — E2.3's
   proper acceptance test is what can actually reject C's model, and its verdict is reported here.
3. **The union interval for E2.6.** Fixed rule: E2.6 sweeps half-lives over the union of (i) C's data interval
   from E2.3 for the adopted engine and (ii) the plan's own sweep levels {30, 60, 120, 250, 500} d, so that the
   sweep brackets both the fitted value and the levels the go/no-go checkpoint was written against, whatever
   E2.3 returns. If E2.3's interval falls outside {30…500}, the nearest decade below/above is added.

---

## 6. E2.4 — the engine decision

Three candidates (§4.3). The rule is the plan's, restated with no change:

- **(a) Acceptance.** Each engine is fitted by E2.3 on `full` and accepted or not by §4.5.
- **(b) Held-out prediction.** Each engine is fitted on `train` (2000–2016); its θ̂ is then used to simulate the
  `test` period (2017–2024) at the test panel's size and length; the distance is
  **D = mean over the eight persistence-carrying moments of |m_sim,j − m_test,j| / sd_boot,j**, sd_boot from the
  `test` block bootstrap. D is reported with a Monte-Carlo interval over 20 CRN replicates. "Beats by more than
  one bootstrap sd" is read as **D_FW ≤ D_AR1 − 1.0**; the same comparison on the full 17 moments is reported
  beside, and the per-moment table is published for both arms.
- **(c) Equivalence of the checklist and the level-free leakage statistics** at matched persistence and matched
  sd(x), 200 seeds per engine × 4 scenarios (seeds EQ) for the checklist and 100 seeds for the level-free audits.
  **Reported with intervals; no pass/fail is attached** — the plan's wording is "any item that differs by more
  than its CI is listed", which is a reporting rule, and Phase 1's experience (ADDENDUM §4) is that an
  equivalence bound at 100–200 paths is not meetable even under identical distributions. §9's PA6 measures the
  null spread of the level-free R² difference between two disjoint 100-seed panels of the *same* configuration
  and publishes it as the yardstick beside every listed difference.

**Decision rule (asymmetric by design; ties go to the simpler model).** `fw_v2` or `fw_plus` is adopted only if
it is accepted at (a) **and** D ≤ D_AR1 − 1.0 at (b); if both qualify, the smaller D wins. **Otherwise `ar1`
(AR(1)+GJR-GARCH-t) becomes the default**, the FW engines become the sensitivity, and every document — spec,
slides, `get_metadata()['engine_used']`, the report — names the engine honestly. If **no** engine is accepted at
(a), the rule still applies: `ar1` is the default by the tie rule, and the report says that none of the three
models fits the panel's moment vector, with J, df and p for each.

**Consequences that are fixed now, so they cannot be chosen later:**
- If `ar1` wins, `test_fundamentalist_share` is **removed with a note** (plan §6.4) and its registry entry is
  cleared; `mispricing.json` records the AR(1) half-life as FIT with its interval; the FW sets stay in the code
  as named sensitivities.
- If a FW engine wins, `test_fundamentalist_share` becomes **hard** at the fitted chartist share ± the fit's own
  interval, and the FW parameters are FIT (E2.3), never the index set.
- Either way the **Appendix-B Kalman bound is re-checked** against the adopted engine (the bound assumes an
  AR(1) x; Phase 1 found the incumbent's x is not one). The re-check is reported; if the bound no longer
  describes the adopted engine, that is handed to Phase 6 as an open item with the evidence, not patched here.
- The **E[x] known defect** (`tests/test_v2_1_phase_1.py::test_flat_x_equivalence`, registry, Phase 2) is
  re-measured on the adopted engine at 1,000 flat paths with jumps off and with jumps on, under the same ±0.02
  TOST the addendum registered. If it passes, the registry entry is removed; if it fails, it stays with the new
  number and the reason.

---

## 7. E2.5 — the half-life estimator lookup table

Pure AR(1) (no GARCH, no V, no events): true half-life h ∈ {30, 60, 120, 150, 250, 500, 600} d ×
T ∈ {200, 800, 2000, 5000}, **200 seeds** per cell (seeds HL). Per cell: the distribution of (i) the naive
ACF(1) half-life −ln2/ln ρ̂ and (ii) the **median-unbiased** estimate (Andrews 1993; the median function is
regenerated by simulation at each T, 20,000 replicates per ρ grid point, as `e1_2/andrews_median_table.npz` was),
reported as median with P25/P75 and a 95 % interval on the median. Decidability (§9, PA4): at 200 seeds the
95 % half-width of the median is 2–11 % of the median, well inside the ±20 % the recovery study used as its own
usability scale.

The documents then report, for whatever engine E2.4 adopts: (i) the **analytic** half-life from the pull rate
(FW engines) or from ρ (AR(1)); (ii) the median-unbiased estimate at **T = 200** — "what the agent experiences" —
together with the sd of x within 200 days and the **number of oracle target switches per run**; (iii) the value
at T = 5,000. The 200,000-step ACF(1) half-life of the engine in force (147 d, Phase 0) is recomputed and
reported beside. `test_half_life_estimator_table` regenerates the table at 50 seeds within the tolerance the
200-seed run establishes (the tolerance is set from the run's own cross-seed sd, stated in the test).

---

## 8. E2.6 — the persistence sweep

Half-life levels: **{30, 60, 120, 250, 500} d** plus any level required by §5.3's union rule, run twice:

- **matched stationary sd(x)** — `sbar` scaled so the realised sd(x) at T = 5,000 equals the value in force
  (the E1.3 convention, `sbar = 0.017 · s_x / 0.1752`, recomputed for the adopted engine), so persistence is
  isolated from variance; and
- **matched innovation variance** — `sbar` held fixed, so sd(x) moves with h.

Per level and matching: the **full checklist** at 200 seeds × 4 scenarios (seeds SW), the **level-free audits**
at 100 seeds, the hazard/topped share, the rejection rate, and — reported at **every** level because they feed
the 16A checkpoint — the **median number of oracle target switches per run** (ISFJ, θ = 0.05, `oracle_target`)
with its IQR and the **share of runs with ≥ 2 switches** with a Wilson interval. Decidability (§9, PA5): at 200
seeds a share has a 95 % half-width of ±0.058 and two levels are separated at 80 % power when they differ by
≥ 0.11, which is smaller than the 0.23 → 0.50 → 0.67 spread the plan records across 150 / 60 / 30 d.

No criterion is attached to the sweep: it is the sensitivity table Phases 6 and 9 consume, and G3 is decided in
Phase 6 on the frozen generator. **G3 may not be met by choosing a persistence shorter than the fitted value**
(plan 16A, edit 27 Aug); E2.6 reports what each level would give and says so explicitly.

---

## 9. Power and decidability (runnable: `tools/phase2/prereg_power.py`; results in `generated/v2_1/e2_0/power.json`)

| # | Criterion it protects | What was simulated | Result | Consequence |
|---|---|---|---|---|
| **PA1** | §3.3 joint-MCR rule | 12 pilots × 20 runs × 6,750 steps of FW's own model at `price_scale = 1` (seeds 770001–770012) | joint MCR 0.104; half-width at 200 runs **±4.2 pp**; chartist share 0.292 ± 0.011; excess kurtosis 1.789 ± 0.038 | 200 runs separate a convention near 10 % from one near 0 %; arm B is decidable and already known to fail (§3.3) |
| **PA2** | §4.3 path count, §4.5 χ² | sd of each pooled moment over 12 CRN seeds at 20 / 50 / 100 paths × 5,000 d, in units of the data bootstrap sd | filled by the run before any fit starts | path count raised until every persistence moment's ratio ≤ 0.30 |
| **PA3** | §6(b) "one bootstrap sd" | spread of D under correct specification (the model *is* the DGP), 40 CRN replicates | filled by the run before any fit starts | if sd(D) is not ≪ 1 the margin is undecidable and the report says so under both readings |
| **PA4** | §7 table | 10 × 200-seed cells at h ∈ {30, 150, 600} × T ∈ {200, 800, 5000} | 95 % half-width of the median = **2.3–11.4 %** of the median | 200 seeds suffice; the achieved half-width is printed in every cell |
| **PA5** | §8 switch shares | binomial half-widths and two-sample detectable differences at n = 100 / 200 | half-width **±0.058** at n = 200, p ≈ 0.23; two-sample MDE **0.11** | 200 seeds separate the plan's 0.23 / 0.50 / 0.67 levels |
| **PA6** | §6(c) equivalence yardstick | level-free L2 R² on two disjoint 100-seed panels of the **same** configuration | filled before E2.4(c) | any listed difference is read against this null spread |

PA2, PA3 and PA6 are run **before** the experiments they protect and their numbers are written into
`power.json` and quoted in the report; if PA2 or PA3 shows a design cannot decide its question, the corrected
design is fixed in `PREREG_PHASE_2_ADDENDUM.md` before the run, with disclosure.

---

## 10. Parameter file, tests, freeze

**`envs/v2/params/mispricing.json`** (new) with one entry per parameter carrying
`value / label / source / date / interval / n / survivor-vs-literature gap`, following `value.json`'s pattern:
`engine` (the adopted name), the engine's structural parameters with their FIT intervals, `price_scale`,
`half_life_pull` and `half_life_acf1` with the estimator and horizon that produced each, `s_x`, the GARCH shape
provenance (E3.1), and the moment/weight-matrix provenance of the fit. **`value.json`** is updated with the
fitted `sigma_V` (label FIT, E2.3, with its interval and n) — this is the D3 = (b) application, and it triggers
the execution-order rule: the state is re-frozen and the path hashes and audits are regenerated on the state
handed over.

**Tests** (`tests/test_v2_1_phase_2.py`, plus edits to the files named): `test_fw_units` (the confirmed
convention reproduces FW's joint MCR at 50 runs within the tolerance the 200-run run establishes),
`test_fw_index_params_match_source` (V1, V2), `test_engine_named_honestly` (`get_metadata()['engine_used']`
equals the code path; no silent fallback), `test_half_life_estimator_table` (regenerates within tolerance at 50
seeds), `test_persistence_in_force` (the pull rate in the running engine equals `params/mispricing.json`, with
provenance present), `test_fundamentalist_share` flipped hard or removed per §6, and `test_half_life_consistency`
(already hard from Phase 0) re-pointed at the adopted engine.

**Freeze**: `python -m tools.freeze_manifest --write` at the end of the phase, on the state handed over, label
"v2.1 Phase 2 freeze"; `path_hashes_phase2_{before,after}.json`; the checklist and the level-free audits
regenerated on that state (execution-order step-0 rule).

---

## 11. Order of execution and where each run happens

1. E2.1 (local, ~10 min) — it fixes `price_scale` for everything after it.
2. E2.3 data side (local only; `datasets/` never leaves this machine) → moments + weight matrices to disk.
3. PA2 / PA3 timing and noise pilots (local) → path count and `maxiter` fixed.
4. E2.3 fits and E2.4(b) held-out fits: **Kaggle** (pure NumPy/SciPy optimisation, which the reproducibility
   rule permits to offload) with a **reference-row check first** — one J evaluation at a fixed θ and CRN seed
   must agree with the local value to 10 significant figures before any Kaggle fit is used. Local runs in
   parallel as capacity allows, one heavy job at a time, 3 workers, `OMP_NUM_THREADS=2`.
5. E2.2 assembly (local, minutes) — needs E2.3.
6. E2.5 (Kaggle or local; embarrassingly parallel by cell).
7. E2.4(a)/(c) and E2.6 (local: they call the generator, the checklist and the sklearn surrogates, and every
   reported surrogate number must come from the reference environment — PHASE_1_REPORT §6.6).
8. Parameter files, tests, freeze, hashes, decision log, report.

`tools/phase2/phase2_chain.py` runs the stages serially and skips any whose output exists.

---

## 12. What is reported if a rule is not met

- E2.1: as §3.3 — the failed convention, the failed target, and no bug-fix claim.
- E2.3: an engine that is not accepted is reported as not accepted, with J, df, χ² critical value and bootstrap
  p; no moment is dropped and no weight matrix is changed to make a fit pass.
- E2.4: if the asymmetric rule leaves `ar1` the default, that is the answer and every document says
  "AR(1)+GJR-GARCH-t"; the FW arms' numbers are published beside so the winner is credible.
- E2.5/E2.6: achieved seed counts, not intended ones; a cell that did not run is listed as not run.
- Any criterion found undecidable is corrected in `PREREG_PHASE_2_ADDENDUM.md` in a separate documented step
  before the re-run, with disclosure of what had been seen, and results are reported under both rules.
- Compute shortfalls never shrink a pre-registered sample silently: the reduced design is fixed before the run,
  the achieved count is stated, and the verdict is marked **undecided** if the smaller sample cannot decide it.

## 13. Not done in Phase 2 (owner)

Jump size and rate re-fit and the GARCH re-fit as a Phase-3 deliverable (E3.2–E3.6); the L2/L2b gates and the
reference distributions (Phase 6); the estimator-environment reproducibility item (Phase 6); θ, bands and the
regret metric (Phase 7); the LLM persistence sweep (Phase 9); REG-1's A-vs-C start-price test (Phase 9).
