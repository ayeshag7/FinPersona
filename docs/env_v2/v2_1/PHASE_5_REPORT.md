# Phase 5 report — observables: the fields the agent actually reads (v2.1)

Executed under `PREREG_PHASE_5.md`. Nothing is committed; everything is in the working tree on `main`. Section 9
of `V2_1_IMPROVEMENT_PLAN.md`; REG-10a–d, REG-15. Weakness items owned: 3, 20, 21, 22, 23, 24, 34, 45.

**This report is written as results land, not assembled at the end** (the Phase-4 lesson). Sections marked
*(pending)* are being executed; every number below is backed by a file under `docs/env_v2/generated/v2_1/e5_*`,
and the report's parameter table (section 4) is checked against `envs/v2/params/observables.json` by
`tests/test_v2_1_phase_5.py::test_phase5_report_parameter_table_matches_observables_json`.

---

## 0. Current state, and how to read this report

| item | status |
|---|---|
| Pre-registration | `PREREG_PHASE_5.md`, written before any run; two corrections made before the outputs they concern were read (section 2); six post-hoc readings in `PREREG_PHASE_5_ADDENDUM.md`, each with its disclosure |
| Team decisions | **D10 put to the team, undecided: both dividend variants carried** (the yield's rendering now has a measured cost, section 3.4). **D15 the team's**: the rule selects sentiment A (section 4.1). The analyst field's C-vs-B is Phase 9's (section 5). |
| Data fits | E5.1 (multiple), E5.2 (EPS, losses, 8-K lags), E5.3 (dividends), E5.5 (sentiment), E5.6 (volume) **done**; E5.4 has no free data (LIT anchor; stated) |
| Implementation | every block a switch with the v2 construction behind it; **proved inert when off** (section 3.9); `envs/v2/params/observables.json` **written** by `apply_e5.py` from `e5_decide.py`'s decisions file; the loader raises on a missing entry, a null interval, a missing date or n, an undeclared status |
| Decisions | multiple **B** (ADOPTED), EPS/dividends v21 (ADOPTED), analyst **C** (PROVISIONAL, Phase 9), sentiment **A** (PROVISIONAL, D15), volume **A** (ADOPTED) — section 4.1, every one by its registered rule on data |
| Audits | E5.7(a) baseline and 20 arms, onset audits on 14 arms, the permutation null (negative: addendum §6) **done**; **final state done** (section 4.3): **L2b +1.8 pp PASS** (was +10.4 FAIL), L2 absolute PASS, onset PASS (non-price rule), final ablation full-field R²(x) 0.805 → 0.432 over a level-free 0.406, calm-trained 0.49 → 0.40, L5 ordering intact |
| Tests | the whole tree run after the file settled (P4-38): **159 passed, 1 skipped, 4 xfailed** (the registered Phase-6 / v1 defects); one fixture defect found and fixed on the way (P5-18) |
| Compute | laptop only; the lab box came back (128 cores) but its tunnel cannot take the data (section 7) |

---

## 1. Literature review and the citation table

| Statistic | Source | Status | Used for |
|---|---|---|---|
| The Daily News Sentiment Index is *"a trailing weighted average of the raw data, with weights that decline geometrically … a depreciation rate of 5%"* | Buckman, Shapiro, Sudhof & Wilson, FRBSF Economic Letter 2020-08, https://www.frbsf.org/research-and-insights/publications/economic-letter/2020/04/news-sentiment-time-of-covid-19/ (read 6 Sep 2026) | **read** | E5.5's deconvolution kernel, λ = 0.95 (LIT) |
| The index page: geometric weighting confirmed; no window stated | https://www.frbsf.org/research-and-insights/data-and-indicators/daily-news-sentiment-index/ (read 6 Sep 2026) | **read** | the same |
| Absolute target-price error ≈ 45 % of price at 12 months; 44.7 % | Bradshaw, Brown & Huang (2013, RAST); Bilinski, Lyssimachou & Walker (2013, TAR) | read in the plan's verification pass (LOG §4.3); carried, not re-read here | E5.4's LIT anchor, sd = 0.45·√(π/2) = 0.564 under the pre-registered mapping |
| 8.1 bp next-day return per sd of pessimism; 6.8 bp reversal over days 2–5 (DJIA, daily) | Tetlock (2007, JF) | read (LOG §4.3) | `b_pred` stays LIT; the SF Fed reverse regression is its cross-check (section 3.6) |
| Turnover elevated in all run-ups, crash or not | Greenwood, Shleifer & You (2019, JFE) | read (LOG §4.3) | E5.6 design B's premise — **not reproduced on this panel** (section 3.7) |
| Weekly turnover-index AC(1) 0.91 (VW) / 0.87 (EW), market level | Lo & Wang (2000, RFS) | read (LOG §4.3) | sanity range only |
| Model 1 = the seasonal random walk | Foster (1977, AR) | read (LOG §4.3) | E5.2's residual definition |
| SEC 10-Q deadlines 40 / 45 days | SEC Form 10-Q general instructions | **LIT, not re-read at source in this phase** | E5.2's sanity bound on the filing lag only |
| Lintner (1956); Kothari (2001); Karpoff (1987) 0.2–0.5 | — | **not readable / not read** | **nothing** — no number from them appears in any table, tolerance or parameter file |

---

## 2. Pre-registration, verification of the inherited numbers, and corrections

`PREREG_PHASE_5.md` was written before any run. `tools/phase5/prereg_power.py` then (i) read every inherited
number back from the file it cites, (ii) regenerated eight paths of the stored post-D14 panel with the current
generator and found them **bit-identical on every column**, and (iii) simulated every registered threshold's
decidability at its stated n (`e5_0/power.{json,md}`):

| row | rule | verdict |
|---|---|---|
| PP1 | E5.1's KS check (bootstrap upper limit of D < 0.10; 1,600 per-path medians vs ≈ 50,000 stock-months) | DECIDABLE — null floor p95 0.034; pass rate 1.00 under D = 0, 0.00 under a true D = 0.10 |
| PP2 | E5.7c's onset rule (ΔAUC ≤ circular-shift null p95 at 200 seeds) | DECIDABLE — simulated null p95 +0.017 (sd 0.011); an AUC excess of 0.028 is detected with 80 % power; E3.5's measured +0.032 sits inside the simulated scale, so the null is not degenerate |
| PP3 | `test_eps_lag_distribution`'s median rule | DECIDABLE iff the FIT lag grid is skewed by more than ≈ 0.5 d |
| PP4 | E5.5 rule (i): generator window-median CI vs the data's | DECIDABLE for gaps above ≈ 0.03; the data side (57 windows) limits resolution |
| PP5 | E5.4's admissibility against the permutation null of ΔR²_add | the real estimator on a synthetic SEP-sized panel gives a null of **10⁻⁵–10⁻⁴** (five draws, max +0.00007) against an expected analyst effect ≥ 0.014 — DECIDABLE; the measured 20-draw null on the real panel supersedes it |
| PP6 | L2b accuracy differences; the n/m share | DECIDABLE at 2 pp |

**Two corrections made before the outputs they concern were read**, each recorded in the pre-registration
itself:

1. Design B's net within-stock variance subtracts the trailing-sum noise s_EPS²/4, not 2·s_EPS² (the variance of
   a seasonal *difference*, which does not enter the level of log P/E). Corrected before E5.1 or E5.2 output was
   read.
2. The inherited-number table cited gbt's −0.394 as the "best" cross-phase-trained level-free calm R²; the file's
   best is ridge's −0.249. Caught by the verify stage; the file's value stands. No threshold depends on it.

**One data fact established before the pre-registration was finished changed a fit's design**: the SF Fed index
is smoothed at source (AC(1) 0.9967; sd(Δs)/sd(s) = 0.081 ≈ √(2(1−λ))), and the Economic Letter states the kernel.
The "AR(1) of daily sentiment" is therefore fitted on the deconvolved series, and design A's parameters are the
**200-trading-day window** fits, like-for-like with the benchmark path (P4-1's one-estimator-both-sides rule).

**Six readings made after data were seen**, each in `PREREG_PHASE_5_ADDENDUM.md` with a disclosure of exactly
what had been seen when it was written, and each reported under both the rule as registered and the reading:

| § | what | consequence |
|---|---|---|
| 1 | the onset audit's price-derived reference set was too narrow: the technicals are functions of the price path and belong on the reference side; the rule applies to the non-price fields | the baseline fails on exactly the v2 analyst and v2 sentiment fields; both verdicts are in every onset file; `test_onset_audit_bound` asserts the non-price verdict and that every registered-rule failure is a price-derived field |
| 2 | E5.6's clause 1 is read in the premise's direction (the run-up ratio's CI excludes 1 from *below*) | A adopted; the letter's verdict (B) recorded beside it (section 4.1, item 4 of section 5) |
| 3 | E5.5 rule (i) is evaluated at the frequency each design lives at (C on the AAII weekly references) | C fails by 0.011 and is excluded from rule (ii) |
| 4 | E5.2/E5.3 estimator repairs: the level floor, the P5–P95 grid truncation, the τ-constrained Lintner, the Yahoo-checked payer share; two EDGAR scale errors (TKR, BBWI) identified | the robust sd is the generator's s_EPS; the plain sd's 4,491 is explained and reported |
| 5 | E5.1's KS check: each design against its natural population (A truncated, B untruncated) | both qualify at P10–P90; the contest goes to rule (ii) as written |
| 6 | the permutation null margin is negative (permuted columns cost the GBT out-of-sample fit); the absolute-admissibility clause is disclosed as mis-specified, not repaired | no decision depends on it (section 4.1); PP5's synthetic scale was wrong in location |

**Tool defects found and repaired before any number from them was read** (each in the decision log): the
arm-ablation table builder required a FULL fit the arm runs no longer make (empty tables for four arms;
recomputed from their stored fits, P5-12); E5.1 first read a fitted `s_x` (0.025) where the rule wants the
engine's stationary sd(x) (0.0656, from `mispricing.json` and `volatility.json`); E5.2's merge crashed on a
column suffix; `e5_arms.py` overwrote its registry per block (merged); the baseline ablation's final save
dropped its `base_hash` (re-stamped before the arms reused it). The stored `path_hashes_phase4_after.json`
fixture predates D14 and the centred depth draw; the inertness proof compares against a HEAD worktree
(`path_hashes_phase5_before.json`, P5-2). **Found by the whole-tree run (P4-38):** the CI leakage fixture fed the
raw panel to the audit, so the NaN of an undefined P/E made the `k·P/reported_PE` candidate's APE NaN on 6 % of
days, which `nanmean(ape > floor)` counts as *inside* the floor — L1 "failed" on a candidate with median APE
0.64; the fixture now applies the registered audit-side encoding (cap + indicator, section 10d of the
pre-registration), as the after-state audit does. The audit machinery itself is unchanged.

---

## 3. Experiments and results

### 3.1 E5.0 — the inherited numbers and the stored baseline panel

All 29 inherited figures reproduce from their files except the one citation slip above (`e5_0/power.md`). The
post-D14 panel `_panels/sep_phase4_after.pkl` (1,600 paths, 320,000 rows) is the current generator's output
bit for bit, so it is a valid baseline for E5.7(a) — the state measured is the state deployed (P4-19).

### 3.2 E5.1 — the multiple (`e5_1/multiple.{json,md}`)

Phase 1's monthly trailing-P/E panel reused unchanged: set A, 411 stocks with a P/E, **61,843 stock-months with
EPS_ttm > 0 of 67,217 with a known trailing EPS** (2009-06 → 2024-12), stock-bootstrap CIs.

| quantile | trailing P/E | 95 % CI |
|---|---|---|
| P5 | 3.86 | [3.12, 4.63] |
| **P10** | **5.77** | [5.19, 6.34] |
| P25 | 9.23 | [8.68, 9.83] |
| P50 | 15.12 | [14.34, 16.06] |
| P75 | 24.42 | [23.10, 25.85] |
| **P90** | **39.98** | [36.87, 43.73] |
| P95 | 58.51 | [53.09, 65.81] |
| **P99 (the cap)** | **191.5** | [154.8, 244.7] |

v2 drew k from U(14, 22): a range that covers roughly the P45–P70 of the real cross-section. The by-year table
(P50 from 9.5 in 2010–11 to 20.9 in 2024) is the time variation Shiller's series describes, at the stock level.

- **n/m share** (EPS_ttm ≤ 0 among months with a known trailing EPS): **0.080** (se 0.001, n = 67,217). Phase 1's
  19.5 % on "the same set" counted every NaN month of the panel matrix, including months before a stock's EDGAR
  coverage begins; the two are different denominators, not a disagreement.
- **Quarterly persistence of log P/E**: median ρ_q = **0.8076 [0.7814, 0.8269]** over 367 stocks (≥ 20 quarters);
  daily equivalent ρ_d = 0.99661 (half-life ≈ 204 trading days).
- **Dispersion of log P/E**: pooled sd 1.096; between-stock sd 0.804; **within-stock sd 0.791**. The engine's
  stationary sd(x) is 0.0656 (analytic: ρ = 2^(−1/22.38), innovation variance sbar² + λσ_J²; E3.8's 200-path
  realised 0.069), so essentially all of the within-stock P/E variation the data show is the multiple's own,
  not mispricing — which is what makes design B's k_t wander by a factor e^0.78 (one sd) and is the mechanism
  by which P/E stops identifying V.
- Damodaran industry current P/E (Jan 2026; cross-check only): median 35.0, IQR [21.2, 70.4], 95 industries.

**The KS check on the arms** (`e5_arms/stats.json`; per-path median rendered P/E over 1,600 paths against the
EDGAR pooled stock-month cross-section; bootstrap 95 % upper limit of D, rule < 0.10):

| width | A vs data truncated to the width | B vs data truncated to the width | A vs untruncated data | B vs untruncated data |
|---|---|---|---|---|
| **P10–P90 (default)** | **0.095 pass** | 0.152 fail | 0.112 fail | **0.082 pass** |
| P25–P75 | 0.121 fail | 0.340 fail | — | — |
| P5–P95 | **0.097 pass** | 0.110 fail | 0.091 pass | **0.076 pass** |

The registered convention (data truncated to the width) is design A's: B's k_t is the fitted pooled process
and no truncation of its between-stock draw truncates it, so B fails that check by construction and passes
against the population it models. `PREREG_PHASE_5_ADDENDUM.md` §5 registers, before the multiple arms'
ablations were read, that each design is checked against its own natural population — both then qualify at
P10–P90 and the contest goes to rule (ii). P25–P75 is **not KS-equivalent** for A (the within-path smearing by
x and the EPS noise is wider than the band) and is recorded as such for Phase 9. The v2 draw U(14, 22) fails
the same check at D = 0.319 (`epsdiv` arms).

### 3.3 E5.2 — EPS, losses and the announcement lags (`e5_2/eps.{json,md}`)

Set A, 411 stocks, 27,515 EDGAR quarters (basic EPS; Phase 1's dedup rule; Q4 derived from FY where needed).
The 8-K Item 2.02 dates were fetched for 415 of 417 names (`CCEP`, `CCU` carry no CIK in the E1.0 panel;
`tools/phase5/fetch_8k.py`, 27,242 earnings-release filings). Stock-bootstrap CIs (1,000).

| quantity | value | n |
|---|---|---|
| seasonal residual (E_q − E_{q−4})/L_q, robust sd | **0.407 [0.377, 0.441]**; P10/P50/P90 −0.78 / +0.09 / +1.08 | 24,402 pairs / 410 stocks |
| the same, plain sd | 4,491 (excess kurtosis 12,649) — two EDGAR scale errors and a handful of write-off quarters; `PREREG_PHASE_5_ADDENDUM.md` §4 | |
| log seasonal change, positive pairs, robust sd | 0.334 [0.314, 0.358] (plain 0.858) | 20,566 |
| V's own annual sd in force | 0.231 (σ_V 0.01457 × √252) | |
| **s_EPS, the generator's noise net of V** | **0.171 [0.150, 0.193]** (from the plain sd it would be 0.584) — v2 used 0.10 | |
| P(loss quarter) | **0.098 [0.086, 0.110]**; P(loss \| loss) **0.425 [0.382, 0.463]**; P(loss \| profit) 0.062 [0.055, 0.068] | 26,389 quarters |
| loss size −E_q/L_q | P10/P50/P90 0.08 / 0.68 / 3.5; grid over P5–P95 = [0.045, 5.94] | 2,344 loss quarters |
| **n/m frequency** (EPS_ttm ≤ 0 over four consecutive quarters) | **0.085 [0.072, 0.099]** (E5.1's monthly count: 0.080) | 24,419 stock-quarters |
| announcement lag, 8-K 2.02 | **P10/P50/P90 = 17 / 28 / 38 calendar days = 12 / 19 / 26 trading days**; grid over P5–P95 = [10, 30] td — v2 drew U(25, 35) | 27,242 filings / 411 stocks |
| filing lag, 10-Q/10-K (beside) | 25 / 35 / 54 calendar days; the release precedes the filing by a median of 7 days (SEC 10-Q deadline 40/45 d) | 25,311 |

Three estimator corrections were made after these files were first read and are disclosed in the addendum
(§4): a level floor (which turned out to remove only 17 pairs — the extremes are scale errors and genuine
write-offs, and the registered robust statistic is unaffected), P5–P95 truncation of the two grids (the
untruncated lag grid ran from 1 to 83 trading days, both ends matching artefacts), and — for E5.3 — a
τ-constrained Lintner fit. The design (§5.2 of the pre-registration) is unchanged: a two-state loss chain
independent of x and of the phase label, Gaussian log-noise at s_EPS in profit quarters, "n/m" when the trailing
EPS is ≤ 0, the P/E capped at the FIT P99 (191.5), lags by inverse CDF from the 8-K grid.

**The rendered n/m frequency** on the eps/dividend arm (1,600 paths): **6.2 %** of days against the data's
8.5 % [7.2, 9.9] of stock-quarters. The gap is the P5–P95 truncation of the loss-size grid: a loss of ≥ 5.9× the
level (the top 5 % of losses, 0.5 % of quarters) makes the trailing sum negative for four quarters, ≈ 2 pp of
days — a stated cost of keeping the two EDGAR scale errors out of the generator. Reported, no gate.

**The residual clock, resolved** (`e5_2/clock/clock.{json,md}`; E4.7's `eps_clock` unchanged, 200 flat seeds,
the quarter grid randomised per seed, the registered split plus five more):

| lags | full window, registered split | interior days 64–137, registered split | full-window excess, 6 splits | interior excess, 6 splits |
|---|---|---|---|---|
| v2 U(25, 35) | 0.384 vs null 0.364 (+2.0 pp) | 0.4285 vs 0.4296 (−0.1 pp) | **+0.78 ± 1.23 pp** | **−1.56 ± 1.18 pp** |
| FIT 8-K grid | 0.397 vs 0.364 (+3.3 pp) | 0.4445 vs 0.4299 (+1.5 pp) | **+1.47 ± 1.63 pp** | **+0.09 ± 1.12 pp** |

The interior residual is at chance under both lag designs; the full-window excess is within one split-sd of
zero. P4-29's 3.3 pp at n = 150 was the window's edges (the first days of a path can only be reached from an
announcement in the burn-in, which fixes those days' quarter position across seeds) plus the sampling
variability of a single split — not a property of the field's construction, and nothing E5.2 needs to redesign.

### 3.4 E5.3 — dividends (`e5_3/dividends.{json,md}`; D10 undecided, both renderings carried)

| quantity | value | n |
|---|---|---|
| payer share of set A | **0.887** (370/417): 353 names report a DPS concept and pay; of the 64 with neither concept, 17 paid a cash dividend per Yahoo's dividend column and 47 (AMZN, GOOGL-style non-payers) never did | 417 |
| payout, annual DPS / annual EPS (EPS > 0) | median **0.406 [0.373, 0.444]**, IQR 0.25–0.64, P90 1.11 — v2 used 0.35 | 10,666 stock-years / 281 stocks |
| Lintner speed c, τ constrained to 0.406 | **0.697 [0.005, 1.075]** per quarter (clustered se 0.233); DPS unchanged quarter-to-quarter in 57.5 % of payer quarters | 15,161 quarters |
| the unconstrained two-parameter fit | UNIDENTIFIED: τ = 0.85 with CI [−0.06, 721] — the record of why the constrained form is used | |
| cuts ≥ 20 % within four quarters of a fast-crash peak | **0.177 [0.122, 0.239]** against an unconditional four-quarter cut rate of **0.073** — cuts are 2.4× more frequent in crashes | 186 episodes / 137 stocks |

The generator's DPS_q = (1 − c)·DPS_{q−1} + c·τ·max(EPS_q, 0) with c = 0.697 and τ = 0.406, and a per-seed
payer draw at 0.887. Its crash cut rate is an outcome (V falls by D_V in a crash, EPS follows, the chain cuts)
and is reported on the final state. Survivor caveat (REG-15): names that cut to zero and delisted are absent,
so the cut rates are understated.

**The D10 arms** (`e5_arms/epsdiv_v21_{shown,hidden}/ablation.md`; the FIT EPS and dividend chains under the
v2 multiple, so the contrast isolates the rendering of the yield): ΔR²_add(VAL) on all rows **+0.090
[+0.075, +0.105] with the yield shown vs +0.052 [+0.040, +0.063] hidden**, paired difference **+0.038
[+0.029, +0.048]**. The yield is 4·DPS/P with DPS a Lintner smoothing of τ·EPS ∝ V/k: a valuation ratio like
P/E, carrying e^{−x}/k with the smoothing's lag, so rendering it has a measured cost of 0.04 of R²(x) under a
constant k. Under the adopted wandering multiple the same ratio is smeared by k_t; the final ablation
(section 4) measures the valuation group as deployed. 12.8 % of the shown arm's days render a zero yield (the
11.3 % non-payers of the draw and quarters whose Lintner target is zero after losses). Onset
(`e5_7c/epsdiv_v21_shown/onset.json`): `reported_PE`, `dividend_yield` and `days_since_eps_announcement` pass
the non-price rule at every transition (crash deterioration→panic AUC 0.64 / 0.63 against the reference 0.74 —
they see the panic through P, after the price does). D10 stays the team's; the cost is now a number.

### 3.5 E5.4 — the analyst estimate *(onset arms landed; ablation arms pending)*

The phase states plainly, before the arms: **no free data can fit the analyst error sd.** The anchor is LIT
(45 % absolute target-price error), the mapping to a log-sd (0.564) is pre-registered, the horizon mismatch is
stated, and the expectation written into the pre-registration is that no LIT sd will be admissible against a
permutation null of order 10⁻⁴ (PP5 confirms the null's scale).

**The onset audit on the analyst arms** (`e5_7c/analyst_A_sd0.564`, `e5_7c/analyst_C`; 200 crash + 200
bull-trap seeds, 500 circular-shift null draws per field; the non-price rule of the addendum §1.3, the
registered verdict beside it). The transition that matters is the crash's calm→deterioration, where V starts
to fall before the price does and a field built on V reads it:

| arm | `analyst_fair_value` AUC at calm→deterioration | reference (best price-derived score) | ΔAUC | null p95 | non-price verdict | verdict as registered |
|---|---|---|---|---|---|---|
| v2 baseline (V·e^u, sd 0.15) | 0.613 | 0.579 (ΔRSI) | **+0.034** | +0.001 | FAIL | FAIL |
| A, sd 0.300 | 0.600 | 0.579 | **+0.021** | +0.001 | FAIL | FAIL |
| A, sd 0.450 | 0.597 | 0.579 | **+0.018** | +0.001 | FAIL | FAIL |
| A, sd 0.564 (LIT anchor) | 0.597 | 0.579 | **+0.017** | +0.001 | FAIL | FAIL |
| A, sd 0.600 | 0.597 | 0.579 | **+0.018** | +0.002 | FAIL | FAIL |
| C (SMA250(P)·e^u, sd 0.564) | 0.448 | 0.579 | −0.131 | +0.018 | **PASS at all six transitions** | FAIL at one: blow-off→post-top |

Doubling to quadrupling the v2 noise halves the excess and leaves it flat at +0.017 to +0.021 across the whole
Phase-9 bracket — seventeen null widths above the line, and not monotone in the noise: **no LIT sd is
admissible**, as the pre-registration expected, because the leak is V's decline itself, not the noise around
it. The proxy C carries no V at all and detects nothing anywhere (its largest ΔAUC against the extended
reference is −0.037). Its one failure under the rule *as registered* is the bull-trap blow-off→post-top
transition (n = 26 topped paths), where the SMA250-based field scores 0.627 against the registered five-score
reference of 0.583 (+0.044 vs a null p95 of +0.032) and against the extended reference of 0.664 it is −0.037:
a 250-day moving average of the price detecting a top *less well than SMA50 does* is the addendum §1's point
restated, not a leak. The ablation arms (3.8(d)): the ANALYST group adds +0.001 to +0.002 of R²(x) on all rows
at every sd, CIs including zero, and C −0.002 [−0.005, +0.001]; the admissibility rule (both clauses) is applied
in section 4 against the permutation-null margin.

### 3.6 E5.5 — sentiment (`e5_5/sentiment.{json,md}`)

**(a) Deconvolution.** raw_t = (s_t − 0.95·s_{t−1})/0.05 over 17,017 calendar days (18 one-day gaps treated
as consecutive). The deconvolved series has sd 0.338, **AC(1) 0.349 [0.286, 0.407]**, AC(2) 0.299, and a
plateau near 0.30 out to lag 21 — a slow component plus a large day-level noise, not an AR(1): the AR(1)+noise
reading (ρ = AC2/AC1 = 0.855, noise share 0.59) is reported for the record but fits the plateau badly, and the
window fits below are what the generator uses.

**(b) Loadings on the standardised FF market return** (11,589 trading days, NW(10)): AR form ρ 0.403
(se 0.015), **b₀ = +0.011 (se 0.007) per sd of raw, b₁ = +0.084 per sd**, residual sd 0.91; R² 0.17;
**corr(raw, mkt) = +0.006**. Economics-news sentiment barely moves with the market's same-day return at the
market level and responds mostly the day after. The sub-periods agree in sign (b₁ +0.07 to +0.18).

**200-trading-day window fits — design A's parameters, like-for-like with the benchmark path** (57 windows):
**ρ = 0.211 [0.155, 0.256]** (P10–P90 0.05–0.44), b₀ = +0.011 [−0.012, +0.029], **b₁ = +0.111 [0.062, 0.132]**,
residual sd 0.972 per sd of raw. The window fit demeans the slow component the full-sample ρ (0.40) keeps.

**(c) The reverse regression (Tetlock's direction).** Next-day market return **−0.64 bp per sd of raw sentiment
(se 1.15)**; days 2–5 cumulative −2.12 bp (se 3.53). The SF Fed index does **not** reproduce Tetlock's 8.1 bp
(a WSJ-column pessimism factor on the DJIA, 1984–99). `b_pred` stays the LIT value in every design, as
registered; the phase reports that the free daily source gives 0 ± 2.3 bp for it, and the `b_pred = 0`
control arm already exists for Phase 9.

**(d) The valuation link (design B).** Monthly raw sentiment on the log-CAPE deviation from its trailing
120-month mean, 560 months, NW(12): **+0.95 sd of raw per unit log-deviation [0.48, 1.42]** (full-sample-mean
deviation: +0.48). Transferred to a single stock's x this is 0.95 sd per unit x, against v2's 0.6·tanh(2x) ≈ 3.4
sd per unit x — the FIT link is about 3.6× weaker than the stipulated one, and it is positive (pro-cyclical).

**(e) AAII (design C).** 2,010 weeks: ρ_w 0.694 (se 0.017), loading on the standardised weekly return b₀ +0.188
(se 0.017), b₁ +0.114, residual sd 0.66; 40-week window fits (50 windows): ρ_w 0.534 [0.493, 0.578],
b₀ +0.298, b₁ +0.199, residual sd 0.76.

**Rule (i) references.** 200-day windows of the deconvolved series: ACF(1) median **0.200 [0.152, 0.258]**
(P10–P90 0.05–0.43); corr(s, r) median **+0.006 [−0.028, +0.019]**. AAII 40-week windows: ACF(1) 0.536
[0.478, 0.572], corr +0.241 [0.152, 0.311]. The checklist's item-12 bands (ACF(1) 0.7–0.9, corr 0.25–0.55)
were stipulated (weakness 31) and are far from the daily data; Phase 6 re-derives them.

**Rule (i) on the arms** (`e5_arms/stats.json`; 1,600 paths per arm, path-cluster CIs of the median):

| design | daily ACF(1) | daily corr(s, r) | meets (i) | weekly ACF(1) | weekly corr | meets (i), weekly |
|---|---|---|---|---|---|---|
| A | 0.205 [0.201, 0.209] | +0.017 [+0.013, +0.021] | **yes** | — | — | — |
| B full | 0.216 [0.211, 0.221] | +0.004 [−0.001, +0.009] | **yes** | — | — | — |
| B half | 0.207 [0.202, 0.212] | +0.011 [+0.006, +0.015] | **yes** | — | — | — |
| C (weekly field) | 0.914 (held 5 days) | +0.025 | n/a | 0.570 | **+0.322** vs 0.242 [0.142, 0.311] | **no** (by 0.011) |
| v2, `b_pred = 0` | 0.838 | +0.380 | no | 0.440 | +0.673 | no |

A and both B variants reproduce the data's window statistics; C misses the AAII weekly correlation by 0.011
(the 40-week window-median loading overshoots the window-median correlation — the ratio of medians is not the
median of the ratio; `PREREG_PHASE_5_ADDENDUM.md` §3) and is excluded from rule (ii). v2's construction sits
where its own stipulated item-12 bands put it, nowhere near the daily data.

**The onset audit on the sentiment arms** (`e5_7c/sentiment_{A,B_full}/onset.json`; the non-price rule of the
addendum, §1.3). At the bull-trap mania onset the v2 sentiment fields were the baseline's failure (AUC 0.518–0.525
against a reference of 0.501, ΔAUC +0.017 to +0.023 vs a null of ≈ +0.010); under design **A** they sit at
**0.494–0.496 (ΔAUC −0.007 to −0.008 vs +0.007)** and under **B-full** at 0.497–0.498 (−0.006 vs +0.007) — no
detection at all, as a returns-only construction must give. At the crash transitions they detect nothing either
(deterioration→panic: AUC 0.50 against a reference of 0.74). The only non-price failure left in either arm is
the v2 analyst field that both arms still carry (crash calm→deterioration, +0.035), which is E5.4's.

**The ablation on the sentiment arms, and rule (ii)** (`e5_arms/sentiment_*/ablation.md`; the arms are
re-simulated, so each refits its own level-free base and the pairing is by seed). ΔR²_add(SENT) on all rows:
v2 **+0.062**; **A −0.001 [−0.001, −0.000]** — a returns-only field adds nothing a return-lag base does not
already hold; **B-half +0.021 [+0.017, +0.024]**; **B-full +0.081 [+0.073, +0.088]** — the valuation link *is*
x, lagged, and the GBT reads it straight back (the FIT c_val of 0.95 per sd per unit log-deviation puts more x
into the field on all rows than v2's 0.6·tanh(2x) did); C −0.001 [−0.002, +0.000], excluded by rule (i).
Rule (ii): among the designs meeting (i) whose onset passes, the lowest ΔR²_add is **A**; B's link is retained
only if its paired increment over A includes zero, and neither does (B-half **+0.021 [+0.018, +0.024]**, B-full
+0.082 [+0.074, +0.089]), so both B variants are the labelled sensitivities and **A is the rule's selection**.
Calm-trained co-statistic: A +0.003 [−0.001, +0.006], B-half +0.006, B-full +0.021. The phase records the
selection; **D15 is the team's** (section 5).

### 3.7 E5.6 — volume (`e5_6/volume.{json,md}`)

Set A, 417 stocks, 2000–2024, log volume detrended by its trailing 252-day mean (DESIGN, stated: no shares
outstanding in the panel), stock-bootstrap CIs:

| parameter | design A | design B |
|---|---|---|
| ρ_v | **0.526 [0.522, 0.529]** (IQR 0.50–0.56) | 0.523 |
| β on \|r\|/σ (per sd of z) | **0.203 [0.198, 0.206]** | 0.203 |
| residual sd | **0.347 [0.339, 0.351]** | 0.347 |
| β_ru on max(ret_252, 0) | — | **−0.012 [−0.020, −0.006]** (sub-periods: +0.10, −0.06, −0.08, −0.06) |

v2 stipulated ρ 0.65, +0.25 \|r\|, **+1.2 \|x\|** (no read source — dominated), noise 0.30.

**The run-up turnover ratio** (E4.1's 3,202 run-ups, every index re-checked against the stored `runup` value, 0
mismatches; 3,019 with a usable window): median log ratio **−0.015 [−0.032, −0.001]**, i.e. volume during a
run-up is **1.5 % lower** than in the year before it, ratio 0.985 [0.969, 0.999]. The CI excludes 1 — in the
direction opposite to the register's premise (GSY's "elevated turnover in run-ups"), and the level-free loading
changes sign across sub-periods. Section 4 records how the pre-registered rule is applied to a result that
satisfies its first clause in letter and contradicts it in substance.

**The onset audit on the volume arms** (`e5_7c/volume_{A,B}/onset.json`, same seeds and null as the baseline).
Both designs pass the non-price rule at every transition; the two failures each arm still shows are the v2
analyst and v2 sentiment fields it carries unchanged. The largest excess of `volume` or `volume_ratio` over the
extended reference is −0.017 (B, bull-trap calm→mania, null p95 +0.011); at the crash's deterioration→panic
both designs' `volume_ratio` reach 0.61 against a reference of 0.74 — they see the panic through \|r\| after the
price does, as an \|r\|-loaded field should. Under design **A** the run-up ratio is 0.985 by construction of
the loadings (no \|x\| term); B's β_ru of −0.012 changes nothing the audit can see. So REG-10c's second clause
(B's onset excess inside the null margin) is met by both, and the contest rests entirely on the first clause,
which the addendum §2 reads in the direction of the premise: **A**.

### 3.8 E5.7 — the audits *(arms and final pending)*

**(a) The per-field-group ablation, baseline** (`e5_7a/baseline/ablation.{json,md}`; the stored post-D14
panel, 1,600 paths / 288,000 modelled rows; the audit's `gbt`, 5-fold GroupKFold by path; 500-resample paired
cluster bootstrap; 8,480 s). This is the first per-field-group attribution in the programme.

| group | ΔR²(x) add-one, all rows | drop-one | ΔR²(x) add-one, calm-trained | drop-one | ΔR²(log V) add-one, all | L2b accuracy add-one |
|---|---|---|---|---|---|---|
| LEVELS (price, SMAs, MACD) | +0.007 [−0.005, +0.018] | +0.052 | +0.018 [+0.006, +0.032] | +0.062 | +0.053 | +0.2 pp |
| VAL (P/E, DY, days-since) | **+0.133 [+0.114, +0.155]** | +0.034 | +0.021 [+0.012, +0.031] | +0.006 | **+0.114** | **+3.1 pp** |
| ANALYST | +0.002 [−0.001, +0.006] | +0.055 | +0.020 [+0.006, +0.033] | +0.062 | +0.064 | +0.7 pp |
| SENT | +0.062 [+0.055, +0.068] | +0.007 | +0.027 [+0.021, +0.033] | +0.013 | +0.003 | +1.2 pp |
| **VOL** | **+0.220 [+0.204, +0.236]** | **+0.085** | **+0.052 [+0.041, +0.062]** | +0.023 | +0.013 | **+6.6 pp** |
| IV | +0.002 [+0.000, +0.005] | +0.008 | +0.016 [+0.008, +0.022] | +0.006 | +0.003 | +0.1 pp |
| BASE → FULL | 0.414 → 0.805 | | **0.3213** → 0.491 | | 0.381 → 0.595 | 0.657 → 0.763 |

Three things this table settles:

1. **The volume field is the largest single carrier of the hidden state** — of x on all rows (+0.22, twice
   the next group), of the calm-trained channel (+0.05) and of the macro-phase clock (+6.6 pp of the 10.7 pp
   full-minus-base gap). Its v2 construction loads `1.2·|x_{t−j}|`, a term with no read source (weakness 24)
   that E5.6 drops. Nobody had ranked it: the reviews named P/E, sentiment and the analyst field.
2. **The valuation group is second** on x (+0.13) and first on V (+0.11 — P/E and the dividend yield are
   V/k through the EPS updates) and on the clock after volume. The analyst field, the reviews' prime suspect,
   adds almost nothing *given the other fields* (+0.002 on all rows) and +0.055 when dropped from the full
   set — its information is largely redundant with the valuation group's; in the calm population it adds
   +0.020 on its own.
3. **The calm-trained level-free base is 0.3213** — the number E4.21 reported for the same quantity, from the
   same code path, which is the consistency check that the ablation measures what the brief measured. The
   fields add +0.17 on calm rows on top of it; the level-free residual ≈ 0.118 itself is not the fields' and
   is attributed by the `b_pred = 0` arm (below).

**(b) The L1 extended candidate set, baseline** (`e5_7b/baseline/l1ext.md`; the stored post-D14 panel, 1,600
paths, in-sample, the attacker's most favourable case). No candidate beats price itself: `k·P` has median APE
**0.0644** and a within-5 % share of **0.416 [0.406, 0.426]**; the best least-squares combination in logs of up
to three candidates (`price + P·DY + F`) reaches 0.0659 / 0.396, and every pairwise geometric mean and the
median-of-valuation-candidates sit at or above price. Under mechanism C's per-seed render scale, a cross-path
level formula cannot recover V from *any* combination of the rendered levels — Phase 1's single-field finding
holds for the extended set. The inversion share the E5.1 rule compares across arms is therefore the within-5 %
share of the best candidate, which at baseline is price's own 0.416 (= the share of days with \|x\| < 0.05).

**On every arm** (`e5_7b/<arm>/l1ext.json`, 21 panels) the best candidate is again `k·P` itself: median APE
0.0644 and inversion share 0.4163 [0.4057, 0.4263] on every post-hoc arm (identical hidden paths), and
0.4236–0.4263 on the re-simulated sentiment arms (their price paths differ; all inside one CI). No extended
formula beats price under any design, so E5.1's inversion-share clause cannot move the A-vs-B contest either
way: the share is the same number on both arms.

**(c) The onset-detection audit, baseline** (`e5_7c/baseline/onset.{json,md}`; 200 crash + 200 bull-trap
seeds, 500 circular-shift null draws, 2,354 s). Under the rule **as registered** eleven (field, transition)
pairs fail — and seven of them are `SMA20`, `SMA50`, `MACD` and `MACD_signal`, which are deterministic
functions of the price path and cannot leak: the registered five-score reference set was too narrow, and the
correction (the technicals join the reference side; the rule applies to the non-price fields) is registered
in `PREREG_PHASE_5_ADDENDUM.md` §1 with the disclosure of what had been seen. Under the corrected rule the
baseline fails on exactly the two channels this phase exists to close:

| transition | field | AUC | reference | ΔAUC | null p95 |
|---|---|---|---|---|---|
| crash calm→deterioration | `analyst_fair_value` (v2: V·e^u) | 0.613 | 0.579 (ΔRSI) | **+0.034** | +0.001 |
| bull-trap calm→mania | `sentiment_change` / `news_sentiment` / `sentiment_MA5` (v2: 0.6·tanh(2x)) | 0.525 / 0.521 / 0.518 | 0.501 | **+0.023 / +0.020 / +0.017** | +0.010 |

Every other non-price field passes at every transition (IV's largest excess is −0.04, volume's −0.04; the
E3.5 result for IV reproduces in kind). The bull-trap blow-off→post-top transition has only 26 topped paths
with a post-top window and is reported, not decided.

**E5.2's residual clock, first half** (`e5_2/clock/`; E4.7's `eps_clock` unchanged, 200 flat seeds, the v2
lags with the randomised quarter grid): full window **0.384 vs null 0.364** (+2.0 pp; P4-29 had +3.3 pp at
n = 150) — and on the **interior days 64–137 it is 0.4285 vs null 0.4296**, no clock. The residual is an edge
effect of the 200-day window, not a property of the field; the FIT-lag arm is measured in section 3.3.

**(d) The arms** (`e5_arms/<arm>/ablation.{json,md}`, `e5_7c/<arm>/onset.json`). Every post-hoc arm (multiple,
EPS/dividend, analyst, volume) is rendered from the **same 1,600 hidden paths** as the baseline, so its level-free
BASE fit is the baseline's (the feature-matrix hash is checked before reuse) and the paired intervals — within an
arm and between two arms — are exact; the sentiment arms change the price path through `b_pred` and are paired by
seed only. The table is generated from the files by `tools/phase5/e5_arms_table.py`; a contest's paired
difference is drawn by `tools/phase5/e5_decide.py` on the ablation tool's own resample indices.

<!-- arms-table -->
| arm | group | ΔR²_add(x) all rows [paired CI] | ΔR²_add(x) calm-trained | ΔR²_add(log V) all | onset, the arm's fields (non-price rule) | worst excess (transition; null p95) |
|---|---|---|---|---|---|---|
| v2 baseline | VAL | +0.1328 [+0.1136, +0.1551] | +0.0209 [+0.0117, +0.0311] | +0.1143 [+0.0967, +0.1292] | see 3.8(c) | |
| v2 baseline | ANALYST | +0.0024 [-0.0008, +0.0058] | +0.0196 [+0.0064, +0.0326] | +0.0638 [+0.0479, +0.0785] | see 3.8(c) | |
| v2 baseline | SENT | +0.0616 [+0.0547, +0.0675] | +0.0269 [+0.0208, +0.0331] | +0.0033 [+0.0021, +0.0045] | see 3.8(c) | |
| v2 baseline | VOL | +0.2203 [+0.2040, +0.2360] | +0.0515 [+0.0413, +0.0622] | +0.0133 [+0.0092, +0.0172] | see 3.8(c) | |
| `sentiment_A` | SENT | -0.0007 [-0.0012, -0.0002] | +0.0029 [-0.0005, +0.0064] | +0.0001 [-0.0006, +0.0009] | PASS | -0.007 (bull_trap:calm->mania; +0.007) |
| `sentiment_B_full` | SENT | +0.0813 [+0.0731, +0.0883] | +0.0212 [+0.0151, +0.0274] | +0.0027 [+0.0017, +0.0036] | PASS | -0.005 (bull_trap:calm->mania; +0.007) |
| `sentiment_B_half` | SENT | +0.0205 [+0.0168, +0.0236] | +0.0056 [+0.0010, +0.0109] | +0.0004 [-0.0003, +0.0011] | PASS | -0.006 (bull_trap:calm->mania; +0.007) |
| `sentiment_C` | SENT | -0.0009 [-0.0021, +0.0003] | +0.0073 [+0.0006, +0.0146] | +0.0000 [-0.0014, +0.0014] | PASS | -0.003 (bull_trap:calm->mania; +0.002) |
| `sentiment_v2_bpred0` | SENT | +0.0595 [+0.0529, +0.0656] | +0.0215 [+0.0159, +0.0273] | +0.0031 [+0.0020, +0.0042] | not run (no rule needs it) |  |
| `analyst_A_sd0.300` | ANALYST | +0.0013 [-0.0024, +0.0048] | +0.0187 [+0.0056, +0.0303] | +0.0439 [+0.0305, +0.0569] | FAIL crash:calm->deterioration:analyst_fair_value | +0.021 (crash:calm->deterioration; +0.001) |
| `analyst_A_sd0.450` | ANALYST | +0.0018 [-0.0017, +0.0051] | +0.0175 [+0.0056, +0.0293] | +0.0318 [+0.0200, +0.0429] | FAIL crash:calm->deterioration:analyst_fair_value | +0.018 (crash:calm->deterioration; +0.001) |
| `analyst_A_sd0.564` | ANALYST | +0.0020 [-0.0015, +0.0053] | +0.0142 [+0.0012, +0.0268] | +0.0261 [+0.0155, +0.0363] | FAIL crash:calm->deterioration:analyst_fair_value | +0.017 (crash:calm->deterioration; +0.001) |
| `analyst_A_sd0.600` | ANALYST | +0.0017 [-0.0016, +0.0050] | +0.0126 [+0.0006, +0.0249] | +0.0257 [+0.0148, +0.0355] | FAIL crash:calm->deterioration:analyst_fair_value | +0.018 (crash:calm->deterioration; +0.002) |
| `analyst_C` | ANALYST | -0.0017 [-0.0046, +0.0014] | +0.0145 [+0.0031, +0.0244] | +0.0086 [+0.0016, +0.0157] | PASS | -0.037 (bull_trap:blow-off->post-top; +0.032) |
| `volume_A` | VOL | +0.0042 [+0.0026, +0.0059] | +0.0065 [+0.0035, +0.0092] | +0.0061 [+0.0043, +0.0082] | PASS | -0.017 (bull_trap:calm->mania; +0.010) |
| `volume_B` | VOL | +0.0036 [+0.0021, +0.0051] | +0.0070 [+0.0039, +0.0098] | +0.0051 [+0.0034, +0.0069] | PASS | -0.017 (bull_trap:calm->mania; +0.011) |
| `multiple_A_P10-P90` | VAL | +0.0254 [+0.0134, +0.0367] | +0.0202 [+0.0100, +0.0309] | +0.0178 [+0.0078, +0.0268] | PASS | -0.003 (bull_trap:calm->mania; +0.002) |
| `multiple_B_P10-P90` | VAL | +0.0114 [+0.0027, +0.0204] | +0.0388 [+0.0272, +0.0508] | +0.0051 [-0.0012, +0.0121] | PASS | -0.003 (bull_trap:calm->mania; +0.002) |
| `multiple_A_P25-P75` | VAL | +0.0689 [+0.0522, +0.0883] | +0.0204 [+0.0107, +0.0314] | +0.0552 [+0.0402, +0.0669] | not run (no rule needs it) |  |
| `multiple_B_P25-P75` | VAL | +0.0142 [+0.0049, +0.0236] | +0.0346 [+0.0224, +0.0472] | +0.0103 [+0.0029, +0.0177] | not run (no rule needs it) |  |
| `multiple_A_P5-P95` | VAL | +0.0117 [+0.0014, +0.0213] | +0.0225 [+0.0122, +0.0338] | +0.0101 [+0.0019, +0.0172] | not run (no rule needs it) |  |
| `multiple_B_P5-P95` | VAL | +0.0112 [+0.0026, +0.0198] | +0.0410 [+0.0306, +0.0519] | +0.0044 [-0.0023, +0.0107] | not run (no rule needs it) |  |
| `epsdiv_v21_shown` | VAL | +0.0897 [+0.0747, +0.1045] | +0.0357 [+0.0217, +0.0516] | +0.0980 [+0.0813, +0.1137] | PASS | +0.001 (bull_trap:calm->mania; +0.002) |
| `epsdiv_v21_hidden` | VAL | +0.0515 [+0.0399, +0.0628] | +0.0231 [+0.0120, +0.0359] | +0.0750 [+0.0598, +0.0888] | not run (no rule needs it) |  |
<!-- /arms-table -->

**E5.1 is decided by the rule as registered** (§4.3, the KS convention of the addendum §5): both designs qualify
(A 0.095 against the data truncated to P10–P90, B 0.082 against the untruncated cross-section, both < 0.10);
ΔR²_add(VAL) on all rows is **A +0.025 [+0.013, +0.037]** and **B +0.011 [+0.003, +0.020]**, and the paired
difference A − B = **+0.014 [+0.001, +0.026]** lies above zero → **B**, the FIT wandering multiple. Either design
removes most of the v2 P/E channel (+0.133 → +0.025 / +0.011): v2's k was a constant in [14, 22], so P/E read
x through k·P/V with only the EPS noise in the way, whereas the FIT within-stock wander of log k (sd 0.78 net
of x and the EPS noise) is twelve times the engine's sd(x) and buries it. The calm-trained co-statistic runs
the other way (A +0.020, B +0.039 — the wandering k is itself a slow level-free signal a calm-trained reader can
use); the register made P-all primary and the co-statistic is reported, not weighed. The inversion share is
0.4163 on both arms (price itself is the best candidate on every panel, 3.8(b)), so the second clause cannot
move the contest. The widths are measured on B and recorded for Phase 9 in section 4.

**E5.6 is decided** (§9.3 under the addendum §2's reading): the volume channel **collapses from +0.220 to
+0.004** under either design — the `1.2·|x|` loading *was* the channel — and the two designs differ by
+0.0006 [+0.0002, +0.0011] (paired A − B). Clause 1 is met by the letter (the run-up log-ratio CI
[−0.032, −0.001] excludes zero) and failed in the premise's direction (the ratio is *below* 1); clause 2 is met
(B's `volume` and `volume_ratio` pass the onset rule at every transition, worst excess −0.017). The letter gives
**B**, the registered reading gives **A**, and A is adopted; B's β_ru = −0.012 stays in the file as the
switchable, labelled sensitivity. Both verdicts are in `e5_arms/decisions.md`.

**E5.4** has every arm's ablation and all but one onset audit (sd 0.450 is queued): the ANALYST group adds
+0.001 to +0.002 on all rows at every sd (the CIs include zero) and every measured A sd **fails the onset rule**
at the crash's calm→deterioration (+0.017 to +0.021 against a null p95 of +0.001 — the excess is not monotone in
the noise, because the leak is V's decline, not the noise around it); C adds −0.002 [−0.005, +0.001] and passes
everywhere. The rule is applied in section 4 once the permutation null margin and the last onset audit land.

**The `b_pred = 0` arm** (`e5_arms/sentiment_v2_bpred0/ablation.md`; v2 sentiment with the feedback into the
price switched off, re-simulated) answers the question 3.8(a) left open — how much of the calm level-free
residual is the sentiment feedback's. The calm-trained level-free base falls from **0.3213 [0.291, 0.350] to
0.2895 [0.259, 0.319]** (−0.032, CIs overlapping) and the all-rows base from 0.4137 to 0.4054 (−0.008). Of the
≈ 0.118 that E4.21 left to "fields and sentiment feedback" after E3.8's process stack, the feedback is worth
about **0.03** — a quarter — with the interval wide enough that the number is a scale, not a share; the rest is
the process stack's own calm signature (E3.8) and is not the observables'. The v2 sentiment fields' own add-one
on this arm is +0.060 [+0.053, +0.066], the same as with the feedback on (+0.062): the fields carry x through
their construction, not through the price loop.

**E5.5 and the EPS/dividend arms** are in the table above and decided in sections 3.4 and 3.6.

### 3.9 The switches, and the proof that they are inert when off

Every block of `envs/v2/observables.py` takes an optional `params` section; with `params=None` or a section at
design `"v2"` the committed code runs verbatim. Proved two ways:

- **function level**: `announcement_schedule`, `earnings_block`, `analyst_block`, `volume_block` and
  `SentimentState` reproduce the committed HEAD functions **exactly on 50 of 50 random inputs** each
  (`tests/test_v2_1_phase_5.py::test_observables_switches_preserve_v2`);
- **path level**: the 95-configuration path-hash fixture run on the patched code with no `observables.json`
  present against the same fixture run in a **HEAD worktree**: **0 non-analyst column changes**
  (`path_hashes_phase5_before.json` vs `path_hashes_phase5_v2check.json`).

The first comparison, against `path_hashes_phase4_after.json`, showed 722 changed columns — all in the 10
sustained-bull configurations (D14 changed every sustained-bull path) and the 20 crash configurations at
δ ≠ 0.70 (the centred depth draw is bit-identical only at 0.70). That fixture (5 Sep 17:13) predates the final
`events.json` (6 Sep 03:08): **a stale reference, not a non-inert switch**, and it is the reason the HEAD
worktree comparison exists (P5-2).

---

## 4. Decisions taken and the parameter file

Every contest was decided by `tools/phase5/e5_decide.py` from the files on disk after the last arm and the
permutation nulls landed (`e5_arms/decisions.{json,md}` — the paired cross-arm intervals are drawn on the
ablation tool's own resample indices), and `tools/phase5/apply_e5.py` wrote `envs/v2/params/observables.json`
from that file through the same `e5_params.sections()` that built the arms, so the deployed numbers cannot
differ from the ones measured. Everything in section 4.3 onward was measured **after** the file settled (P4-45).

### 4.1 The contests

| block | rule | verdict | status in the file |
|---|---|---|---|
| multiple (E5.1) | §4.3 with the addendum §5 KS convention: B iff the paired ΔR²_add(VAL) A − B lies above zero | A − B = **+0.0139 [+0.0014, +0.0256]** → **B** at P10–P90 (A +0.025, B +0.011; v2 +0.133) | ADOPTED |
| EPS, losses, lags (E5.2) | no contest: FIT, with the addendum §4 estimator repairs | v21 | ADOPTED |
| dividends (E5.3) | no contest for the process; the rendering is D10's | v21, `field = "shown"`, both carried; the yield's rendering costs +0.0382 [+0.0292, +0.0480] under a constant k | ADOPTED (process); D10 undecided |
| analyst (E5.4) | §7.3: A at σ admissible iff ΔR²_add ≤ the ANALYST null margin **and** its onset passes | no A arm passes the onset clause (+0.017 to +0.021 vs +0.001 at every sd) → **C**, the SMA250 proxy, provisional; C's ΔR²_add -0.0017 [-0.0046, +0.0014] | PROVISIONAL (Phase 9: C vs B) |
| sentiment (E5.5) | §8.3: (i) the item-12 references, then (ii) the lowest ΔR²_add passing onset; B's link kept only if its increment over A includes zero | (i) A, B-full, B-half; (ii) **A** (−0.001); B-half +0.021 [+0.018, +0.024] and B-full +0.082 [+0.074, +0.089] over A exclude zero → labelled sensitivities | PROVISIONAL (D15) |
| volume (E5.6) | §9.3 under the addendum §2 reading | letter **B**, reading **A** → A adopted (A +0.004, B +0.004; v2 +0.220) | ADOPTED |

**The permutation null margin is negative** (ANALYST p95 -0.0057, 20 draws from -0.0110 to -0.0057; SENT -0.0024).
A permuted block costs the GBT out-of-sample fit, so the null sits at the noise cost of extra columns and no
field — not even C, which carries nothing — can be "inside" it. The clause is disclosed as mis-specified in the
addendum §6 and is not re-specified after the fact; no decision depends on it (E5.4's rule is conjunctive and
the onset clause fails on its own; E5.5's rule (ii) uses paired increments). PP5's synthetic check had put this
null at 10⁻⁴ — wrong in location, not in width.

**Widths on the adopted design B, recorded for Phase 9:** P25-P75: ΔR²_add(VAL) +0.0142 [+0.0049, +0.0236]; KS vs the truncated data 0.340 (fail); P5-P95: ΔR²_add(VAL) +0.0112 [+0.0026, +0.0198]; KS vs the truncated data 0.110 (fail), vs the untruncated 0.076 (pass). The default stays P10–P90; P25–P75 is not
KS-equivalent under either convention.

### 4.2 The parameter file

`envs/v2/params/observables.json`, read by `envs/v2/observables_params.py` (raises on a missing entry, a null
interval, a missing date or n, and an undeclared status). The table is generated from the file by
`tools/phase5/e5_param_table.py`; `tests/test_v2_1_phase_5.py::test_phase5_report_parameter_table_matches_observables_json`
reads the status column back against the file.

<!-- param-table -->
| entry | status | design and values in force | n | interval | label (the file's, abridged) |
|---|---|---|---|---|---|
| `multiple` | **ADOPTED** | design: B; width: P10-P90; grid_A: 3 widths x 33 pts; grid_B_log_between: 3 widths x 33 pts; rho_q: 0.8076; rho_d: 0.9966; s_w: 0.7833; s_w_net_variance: 0.6135; sd_within_gross: 0.7906; sd_x_engine: 0.0656; s_eps_used: 0.1707 | stocks 411; stock_months_positive 61843; stocks_ar1 367 | p10_p90_pooled [5.7676, 39.9813]; p10_ci [5.1903, 6.3413]; p90_ci [36.8731, 43.7291]; rho_q_ci [0.7814, 0.8269] | ADOPTED by PREREG section 4.3 on data: design B at width P10-P90 -- FIT (EDGAR trailing P/E cross-section, set A). KS under ADDENDUM section 5's convention: A passes (0.095 vs 0.10 truncated), B passes (0.082 untruncated); paired dR2_add(VAL) A - B = +0.0139 [+0.0014, +0.0256] (x, P-all, 1,600 paths); the inversion share is 0.4163 on both arms (price itself is the best candidate on every panel), so the second clau... |
| `eps` | **ADOPTED** | design: v21; s_eps: 0.1707; p_loss: 0.0975; p_loss_given_loss: 0.4251; p_loss_given_profit: 0.0616; loss_size_grid: 33 pts; pe_cap: 191.5497; lag_grid_td: 33 pts; lag_p10_p50_p90_td: [12, 19, 26]; nm_share_data: 0.0848 | quarters 27515; stocks 411; seasonal_pairs 20566; loss_quarters 26389; announcement_filings 27242; announcement_stocks 411 | s_eps [0.1497, 0.1928]; p_loss [0.0856, 0.1097]; nm_share_data [0.0719, 0.0987]; lag_p50_td [19, 19]; pe_cap_p99 [154.7454, 244.6775] | ADOPTED: FIT on EDGAR basic EPS (set A) and 8-K Item 2.02 announcement dates, with the level floor and the P5-P95 grid truncation of ADDENDUM section 4; no contest was registered (the v2 construction had no fitted alternative and is retrievable under design 'v2'); the residual clock is resolved as an edge effect (e5_2/clock) |
| `dividend` | **ADOPTED** | design: v21; field: shown; c_speed: 0.6972; tau: 0.4063; payer_share: 0.8873; payout_median_data: 0.4063 | stocks_set_A 417; stocks_reporting_dps 353; payers_set_A 370; lintner_quarters 15738; payout_stock_years 10666; crash_episodes 186 | c_speed [0.0052, 1.0751]; tau [0.251, 0.6386]; payout_median [0.3731, 0.4444] | ADOPTED for the process: FIT Lintner at quarterly frequency with tau constrained to the FIT median payout (ADDENDUM section 4.2.3) and the payer share from EDGAR + Yahoo (4.2.4); the FIELD's rendering is D10's, undecided -- both variants carried, default 'shown' = the v2 rendering |
| `analyst` | **PROVISIONAL** | design: C; sd: 0.564; rho: 0.95; update_days: 5; field: shown; lit_anchor_sd: 0.564; bracket_phase9: 3 pts | note no free target-price data: the sd is LIT and the phase states plainly that no free data can fit it; arms_measured 5; paths_per_arm 1600 | lit_bracket_phase9 [0.3, 0.6]; anchor_mapping E|u| = sd sqrt(2/pi), 45 % -> 0.564 if a mean absolute log error; persistence DESIGN, rho 0.95 per 5-day update (no free data) | PROVISIONAL by PREREG section 7.3: no design-A sd is admissible -- every A arm fails the onset rule at the crash's calm->deterioration (V's decline is the leak, not the noise: excess sd 0.3: +0.021 vs null p95 +0.001; sd 0.45: +0.018 vs null p95 +0.001; sd 0.5639913617919751: +0.017 vs null p95 +0.001; sd 0.6: +0.018 vs null p95 +0.002) -- so design C (SMA250(P) e^u, LIT sd 0.564, DESIGN rho 0.95 per 5-day update)... |
| `sentiment` | **PROVISIONAL** | design: A; rho: 0.2113; b0: 0.0113; b1: 0.111; sd_e: 0.9718; s_raw: 0.3971; c_val: 0.9499; c_val_full: 0.9499; link_size: full; rho_w: 0.5339; b0_w: 0.298; b1_w: 0.1994; sd_e_w: 0.7593; update_days: 5; full_sample_fit: 4 widths x 1 pts | sf_fed_calendar_days 17017; trading_days_aligned 11589; windows_200d 57; aaii_weeks 2010; cape_months 560 | rho_window [0.1552, 0.2561]; b1_window [0.0616, 0.1316]; c_val_full_per_sd_per_unit_logdev [0.4817, 1.4181]; rho_w_aaii [0.4933, 0.5783] | PROVISIONAL pending D15 (the team's default): PREREG section 8.3's rule selects design A -- rule (i) met by A, B-full, B-half (C fails the AAII weekly correlation by 0.011, ADDENDUM section 3); rule (ii) ordering by dR2_add(SENT) x, P-all: A -0.0007, B-half +0.0205, B-full +0.0813. FIT on the SF Fed daily index deconvolved at lambda = 0.95, 200-day window medians; the pairing of the sentiment arms is by seed only ... |
| `volume` | **ADOPTED** | design: A; rho_v: 0.5259; beta_absr: 0.2027; sd_e: 0.3469; beta_ru: -0.0123 | stocks 417; runup_episodes 3019; runup_stocks 394 | rho_v [0.5224, 0.5286]; beta_absr [0.1983, 0.206]; sd_e [0.3389, 0.3509]; runup_log_ratio [-0.032, -0.0015]; beta_ru [-0.0202, -0.0056] | ADOPTED by PREREG section 9.3 under ADDENDUM section 2's reading: design A -- FIT (set A daily volume: rho_v, the |r|/sigma loading and the residual sd); the run-up log-ratio CI [-0.0320, -0.0015] excludes zero BELOW (ratio 0.985, n = 3019 run-ups), against the premise, so clause 1 fails in substance; under the clause's letter the verdict would be B (B's onset audit passes; its beta_ru is sign-unstable across sub-... |
| `audit_bounds` | **PROVISIONAL** | no_field_deterministic_R2: 0.2; onset_rule: dAUC <= circular-shift null p95 (measured); l2b_margin_phase6_owned: 0.1 | paths 1600 | none: a provisional reference bound, owned by Phase 6 | PROVISIONAL bound for test_no_field_is_deterministic_in_x: 0.20 is evaluation/leakage_audit.L2_SELECTIVITY_R2, amendment A8's reference value (the plan's own number, not a new stipulation), applied per field group to the add-one R2(x) on all rows; Phase 6 derives the margin that replaces it. The onset rule's threshold is the measured null, not a number. |
<!-- /param-table -->

### 4.3 The final state *(every number measured after the file settled, P4-45)*

**The hand-over panel** (`_panels/sep_phase5_after.pkl`: 1,600 paths, T = 200, 320,000 rows, the fast renderer
verified bit-for-bit against `panel_from_env` on its verification manifest) and **the SEP audit on it**
(`e5_after/audit_after_levelfree.{md,pkl}`, `run_audit` unchanged, "n/m" encoded as the cap plus the
`reported_PE_nm` indicator, level-free control):

| gate | Phase 4 post-D14 (E4.21) | **Phase 5** | rule |
|---|---|---|---|
| **L2b phase-clock selectivity** (full − price-only macro-class accuracy, 288,000 rows) | +10.4 pp **FAIL** | **+1.8 pp** (67.6 % − 65.8 %; day-only 50.8 %, majority 41.4 %) **PASS** | ≤ 10 pp (Phase 6 re-derives the margin) |
| L2 absolute (pre-registered A6 gate; a registered known defect since Phase 0) | FAIL | calm best R²(x) −0.61, event 0.45, MAPE(V) 0.128; max selectivity R²(x) +0.028, MAPE(V) gain 1.7 %, shuffled-V R² 0.001 → **PASS** | absolute thresholds as registered |
| L1 algebraic inversion | pass | pass (price itself is the best inverter, 3.8(b)) | A6 |
| onset detection (`e5_7c/final/onset.json`, 200 + 200 seeds, 500 shifts) | v2 analyst and v2 sentiment fail | **PASS under the non-price rule at all six transitions**; the registered rule's failures are the technicals and `analyst_fair_value` at blow-off→post-top (n = 23, against the narrow reference only; +0.010) | addendum §1.3 |

**The calm-trained level-free channel** (`e5_after/calm_trained_phase5.{json,md}`; the e3_9 estimator on the
Phase-3, post-D14 Phase-4 and Phase-5 panels in one process, 500 resamples):

| state | level-free R²(x) | full-field R²(x) | the fields' calm contribution |
|---|---|---|---|
| Phase 3 | +0.3493 [+0.3218, +0.3743] | +0.5501 [+0.5180, +0.5791] | 0.201 |
| Phase 4 post-D14 | +0.3213 [+0.2935, +0.3478] | +0.4905 [+0.4607, +0.5203] | 0.169 |
| **Phase 5** | **+0.2912 [+0.2637, +0.3179]** | **+0.3950 [+0.3609, +0.4284]** | **0.104** |

The level-free figure moves 0.3213 → 0.2912 with overlapping intervals — the `b_pred = 0` arm (3.8(d)) says
0.03 of it is the feedback's, and the new sentiment has no x term — and the full-field figure falls
0.4905 → 0.3950 with intervals that do not overlap: what the observables carried into a calm-trained reader
is down by 0.065 and what remains (0.104) is the process stack's calm signature plus the valuation ratios
(4.1). The checklist (`e5_after_checklist.{md,csv}`, 1,013 s), the path-hash fixture
(`path_hashes_phase5_after.json`: 2,635 non-analyst column changes against the HEAD worktree — every
observable block changed, as deployed) and the freeze manifest (`tests/v2_freeze_manifest.json`, 27 files)
are written. **L5 and the discrimination table** (`e5_l5/l5_phase5_after.{csv,md}` — the n/m-aware oracle subclass, the frozen
`ObservablesOracle` otherwise unchanged, 40 training + 50 scored seeds, three personas × four scenarios;
`e5_l5/discrimination.{json,md}` by `tools/phase5/e5_discrimination.py`, beside the Phase-4, -3 and -2 rows; no
pass/fail — G1 is Phase 6's):

| scenario | coverage P4 → P5 | mandate oracle | best L5 | best trivial | gap oracle→L5 P4 → P5 [CI] | gap L5→trivial P5 [CI] |
|---|---|---|---|---|---|---|
| flat | 0.378 → **0.362** | 0.0029 | 0.0627 (level_free) | 0.1006 | 0.0534 → 0.0598 [0.0543, 0.0656] | 0.0379 [0.0321, 0.0434] |
| crash | 0.553 → **0.543** | 0.0023 | 0.0427 (level_free) | 0.1003 | 0.0356 → 0.0405 [0.0369, 0.0439] | 0.0576 [0.0542, 0.0611] |
| bull_trap | 0.646 → **0.636** | 0.0033 | 0.0413 (level_free) | 0.1008 | 0.0287 → 0.0380 [0.0325, 0.0434] | 0.0595 [0.0540, 0.0650] |
| sustained_bull | 0.044 → **0.354** | 0.0029 | 0.0631 (full) | 0.1009 | 0.0676 → 0.0602 [0.0530, 0.0675] | 0.0378 [0.0305, 0.0450] |

The ordering oracle < L5 < trivial holds in every scenario with both gaps' intervals above zero; the best L5
policy is `level_free` in three scenarios and `full` in sustained-bull; the oracle→L5 gap widens by 0.005–0.009
in flat, crash and bull-trap — the redesigned fields give the L5 reader less — and narrows in sustained-bull,
whose coverage moves from 0.044 to 0.354 (the Phase-4 csv on disk, `e4_16/l5_phase4_after.csv`, is the
**pre-D14** hand-over; post-D14 coverage was 0.374, E4.21). No run has an undefined MCR.

**The final per-field-group ablation** (`e5_7a/final/ablation.{json,md}`; the after panel, the same estimator,
feature-set construction, 5-fold GroupKFold by path and paired 500-resample cluster bootstrap as the baseline;
70 fits, 6,881 s), beside the v2 baseline of 3.8(a):

| group | ΔR²_add(x) all rows, v2 → **Phase 5** [CI] | ΔR²_drop(x) all | ΔR²_add(x) calm-trained | ΔR²_add(log V) all | Δacc macro clock, Phase 5 [CI] |
|---|---|---|---|---|---|
| VOL | +0.2203 → **+0.0042 [+0.0025, +0.0059]** | +0.0846 → +0.0023 [-0.0004, +0.0047] | +0.0515 → **+0.0058 [+0.0022, +0.0087]** | +0.0133 → +0.0053 [+0.0034, +0.0073] | +0.0148 [+0.0125, +0.0172] |
| VAL | +0.1328 → **+0.0090 [+0.0011, +0.0167]** | +0.0344 → +0.0099 [+0.0010, +0.0177] | +0.0209 → **+0.0509 [+0.0353, +0.0677]** | +0.1143 → +0.0064 [-0.0013, +0.0140] | +0.0037 [+0.0003, +0.0068] |
| SENT | +0.0616 → **-0.0007 [-0.0012, -0.0002]** | +0.0070 → -0.0011 [-0.0029, +0.0004] | +0.0269 → **+0.0029 [-0.0005, +0.0064]** | +0.0033 → +0.0001 [-0.0006, +0.0009] | -0.0008 [-0.0016, -0.0000] |
| ANALYST | +0.0024 → **-0.0011 [-0.0039, +0.0021]** | +0.0550 → +0.0053 [-0.0005, +0.0106] | +0.0196 → **+0.0100 [-0.0035, +0.0223]** | +0.0638 → +0.0084 [+0.0017, +0.0147] | +0.0002 [-0.0015, +0.0020] |
| LEVELS | +0.0067 → **+0.0055 [-0.0060, +0.0163]** | +0.0517 → +0.0103 [-0.0020, +0.0218] | +0.0179 → **+0.0225 [+0.0085, +0.0373]** | +0.0531 → +0.0502 [+0.0357, +0.0652] | +0.0020 [-0.0011, +0.0051] |
| IV | +0.0023 → **+0.0029 [+0.0008, +0.0053]** | +0.0078 → +0.0043 [+0.0008, +0.0080] | +0.0159 → **+0.0188 [+0.0111, +0.0260]** | +0.0030 → +0.0027 [-0.0003, +0.0054] | +0.0013 [-0.0007, +0.0036] |

The level-free base is +0.4137 [+0.3988, +0.4287] → +0.4059 [+0.3909, +0.4213] on all rows and
+0.3213 [+0.2910, +0.3498] → +0.2912 [+0.2619, +0.3201] calm-trained (the same code path as the
E4.21 / calm-trained figures above), and **the full feature set falls from +0.805 to
+0.432** on all rows: the eighteen fields together now add **+0.026** of R²(x) over
a level-free reader where they added +0.39. No group is above the PROVISIONAL bound of 0.20
(`test_no_field_is_deterministic_in_x`; the worst is VAL at +0.009). The largest remaining carriers are the two
ratios of price to a slowly-moving quantity — VAL (P/E and the yield) at +0.009 on all rows and **+0.051 calm-trained**
(the wandering multiple is itself a slow signal a calm-trained reader uses, the co-statistic 4.1 flagged) — and
VOL at +0.004 through its FIT \|r\|/σ loading. The macro-phase clock: base 0.658 → full
0.688 (+3.0 pp, against +10.7 pp on the baseline), VOL the
largest single contributor at +1.5 pp (was +6.6) — volume answers volatility
and the phases are volatility-laden, which is what the FIT loading says it should do — VAL +0.4 pp (was +3.1),
SENT -0.1 pp (was +1.2). The audit's own L2b figure on the same panel is +1.8 pp (4.3, first table).


---

## 5. Decisions the team must take

1. **D10 — the dividend rendering.** Undecided at the phase's start; both variants are carried and audited,
   the default is `shown` (v2's rendering). The measured cost of rendering the yield under the v2 multiple is
   **+0.038 [+0.029, +0.048]** of R²(x) on all rows (section 3.4); the final ablation gives the valuation
   group's figure under the deployed multiple. Paying dividends into the agent's cash is a `simulation/`
   change (weakness 33) outside this phase — the harness half of D10, Phase 7/8's.
2. **D15 — the sentiment default.** The rule selects **A** (returns only; ΔR²_add −0.001, passes onset);
   **B-half** (+0.021) and **B-full** (+0.081) are the labelled sensitivities, switchable with their FIT link;
   **C** fails rule (i) by 0.011 on the AAII weekly correlation and is not relaxed (addendum §3). The file
   carries A as PROVISIONAL pending D15; the table is in section 4 and `e5_arms/decisions.md`.
3. **The analyst field: C (the SMA250 price proxy, the deployed PROVISIONAL default) vs B (drop it)** — Phase 9's
   per the register, noted here because the default is in force. Design A is not admissible at any sd measured
   (section 3.5). C's calm-trained co-statistic is +0.015 [+0.003, +0.024]: a price-derived field a
   calm-trained reader can use, the same kind of information as the technicals carry.
4. **Two places where a rule's letter and its registered reading differ**, adopted as the reading says, for the
   team to confirm or overturn: (a) **E5.6** — the letter gives B, the addendum §2 reading gives **A**; the
   difference between them is 0.0006 of R²(x) and a sign-unstable coefficient; (b) **E5.1** — the registered
   primary statistic (P-all) gives **B**; the calm-trained co-statistic runs the other way (A +0.020 vs
   B +0.039 [+0.027, +0.051]). Both alternatives stay switchable with their FIT parameters.
5. **`b_pred`.** The free SF Fed source does not reproduce Tetlock's 8.1 bp (−0.64 ± 1.15 bp, section 3.6); the
   LIT value stays in force. Keep it LIT, or fund a source that can fit it.

---

## 6. Files written or changed

`PHASE_5_CHANGED_FILES.md`.

---

## 7. What was not done, and who owns it

| item | state | owner |
|---|---|---|
| **The harness half of D10** — dividends paid into the agent's cash (weakness 33) | not done: a `simulation/` change outside this phase's remit; the generator half (the FIT DPS process, both renderings) is done and audited | Phase 7/8 (the harness) |
| **D15** — the sentiment default | the rule's selection and the full table are in section 4; the decision is the team's | team |
| **The analyst field: C vs B** (keep the price-proxy field or drop it) | C is carried PROVISIONAL with its audits done; the condition that decides it ("its inclusion changes no arm contrast beyond the equivalence margin") is an LLM-grid statement; B is the fallback | Phase 9 |
| **The analyst bracket {0.30, 0.45, 0.60}** the plan reserved for Phase 9 | measured here: every design-A sd fails the onset rule, so a Phase-9 sweep of A is moot unless the onset rule itself is changed | Phase 9 (recorded, not needed) |
| **The multiple's widths** P25–P75 and P5–P95 | measured on the adopted design and recorded as the Phase-9 sensitivity settings; P25–P75 is **not KS-equivalent** (0.121 > 0.10) | Phase 9 |
| **The n/m frequency** — the generator renders 6.2 % against the panel's 8.5 % | reported; the shortfall is the P5–P95 truncation of the loss-size grid (the tail losses that keep trailing EPS negative for several quarters); no gate exists for it | Phase 6 (a checklist band, if wanted) |
| **`b_pred`** — the free SF Fed source does not reproduce Tetlock's 8.1 bp (−0.64 ± 1.15 bp) | the LIT value stays in force unchanged; the non-reproduction is reported | team (a paid source, or keep LIT) |
| **The L2b selectivity gate and the surrogate thresholds** | Phase 6's; the values on the final state are reported beside them | Phase 6 |
| **The PROVISIONAL bound 0.20** of `test_no_field_is_deterministic_in_x` | amendment A8's reference value, labelled PROVISIONAL in `observables.json`; Phase 6 derives the margin that replaces it | Phase 6 |
| **Survivor bias** (REG-15) | set A is survivor-only: the P/E tails, the n/m share and the loss frequencies are understated relative to the full universe; no free delisted universe exists | open (recorded in the file's `survivor_vs_literature_gap` entries) |
| **Design C for sentiment** (survey frequency) | fails rule (i) by 0.011 on the AAII weekly correlation because the window-median loading overshoots the window-median correlation; not relaxed; a median-of-ratio fit would be the repair if the team wants a survey-frequency field | team (if wanted) |
| **Compute** | everything ran on the laptop. The lab box came back on 7 Sep (128 cores, 32 GiB cgroup; environment built at the laptop's library pins, `docs/COMPUTE_GPU_ACCESS.md`) but its tunnel delivers ≈ 3 KB/s upstream and resets bulk transfers, so the panel could not be pushed to it; the user skipped it for this phase with the local runs already near their end. The cross-machine reproduction check (a stored laptop fit reproduced exactly) is therefore still to be done before any fitted number from it can be reported | Phase 6 (a pull path for data: Kaggle dataset or a share Fan controls) |

