# Pre-registration: Phase 5 (observables — the fields the agent actually reads)

**Written before any Phase-5 run.** Plan Section 9; protocol Section 1; power formulas Appendix A.
Register entries in force: REG-10a (the multiple), REG-10b (sentiment), REG-10c (volume), REG-10d (the
analyst estimate), REG-15 (data). Weakness items owned: 3, 20, 21, 22, 23, 24, 34 (observable constants), 45.

Nothing below is moved after data are seen. If a criterion turns out to be wrong it is corrected in a separate
documented step *before* the re-run, with a disclosure of what had already been seen, and the result is
reported under both the old and the new rule (`PREREG_PHASE_4_ADDENDUM.md` is the template; its section 6 is
the template for a departure the team authorises).

Four method rules Phase 4 learned the expensive way are binding here and are restated where they bite:
**pin the configuration a tool measures** (P4-19), **verify every cited file exists before the citation is
written** (P4-37), **run the whole test tree** (P4-38), **measure after the parameter file settles** (P4-45).

---

## 0. Team decisions in force at the time of writing

| Decision | Status | What Phase 5 does |
|---|---|---|
| **D1** data | C, hybrid | Fit on the free panel (set A, EDGAR, SF Fed, AAII, Shiller, Damodaran); publish the survivor gap where it can be quantified; every fit re-runnable on WRDS/IBES by a data-path change (`tools/phase1/panel.PanelSpec`). |
| **D10** dividends | **UNDECIDED** (put to the team in this phase's first message, 6 Sep 2026) | The plan's instruction applies: **both variants are carried**. The DPS process is FIT either way; the field is rendered (`dividend_field="shown"`, the v2 behaviour) or omitted (`"hidden"`) behind a switch, and the audits run under both. Paying dividends into the agent's cash is a `simulation/` change outside this phase's remit and is recorded as the harness half of D10. |
| **D13** start price | mechanism C (`start_price_mode="both"`) | In force, unchanged. The per-seed render scale is what defeated the cross-path analyst inversion (Phase 1); the *within-path* channel is this phase's. |
| **D14** control | **A** (team, 6 Sep 2026; P4-43) | In force. Every audit here runs on the post-D14 generator. |
| **D6** calendar | "Day-N" | In force; the eps quarter grid is randomised per seed (P4-29). |
| **D15** sentiment default | not taken | Taken by the team **after** E5.5 on its results. This phase records the design its rule selects and does not pre-empt D15. |
| **D5**, **κ = 0** | open, blocked (P4-42, P4-44) | Not touched. |

---

## 1. Inherited numbers verified before use

Following `PHASE_4_REPORT.md` section 0 and P4-37: no Phase-5 statement builds on an inherited figure until the
figure has been checked against the generated file it cites. `tools/phase5/prereg_power.py` performs the check
mechanically (every file below must exist and carry the value) before the first experiment.

| Inherited figure | Cited value | File it must come from |
|---|---|---|
| L2b macro-class accuracy, post-D14: full / price-only / day-only / majority; selectivity | 0.760160 / 0.656635 / 0.509229 / 0.414490; **0.1035 (FAIL vs 10 pp)** | `e4_21/audit_after_levelfree.pkl` `L2b` |
| Best full-field R²(x) post-D14: all / calm / event / resolution | 0.8046 / 0.2326 / 0.8541 / 0.7442 | `e4_21/audit_after_levelfree_L2.csv` (gbt rows) |
| Best level-free R²(x) post-D14: all / calm | 0.4458 / **−0.249** (cross-phase-trained; best = ridge) | same file (`price_only` rows) — *the first draft of this row cited gbt's −0.394 as "best"; `prereg_power.py`'s verify stage caught it (the best cross-phase-trained level-free calm cell is ridge's −0.249) and the file's value stands* |
| Calm-TRAINED level-free R²(x), post-D14 | **+0.3213 [0.2935, 0.3478]** | `e4_21/calm_trained_phase4.json` |
| Calm-trained full-field R²(x), post-D14 | +0.4905 [0.4607, 0.5203] | same |
| Process + GJR + jump stack (E3.8) | 0.203 [0.141, 0.262] | `e3_8/decomposition.json` |
| The 18 shown fields | as listed in the execution prompt | `e4_21/audit_after_levelfree.pkl` `shown_fields` |
| `days_since_eps_announcement` clock: fixed grid / randomised | 0.8728 / **0.3958** vs null p95 0.3627 / 0.3625 (n = 150) | `e4_7/calendar.json` `eps_quarter_clock` |
| Analyst field L1 inversion under mechanism C | median APE 0.6786 (`k * analyst_fair_value`) | `e4_21/audit_after_levelfree_L1.csv` |
| IV onset audit (REG-6 form) | ΔAUC −0.107 vs null p95 +0.032 | `e3_5/audit.json` |
| Engine stationary sd(x) and half-life (needed by E5.1's net-of-x correction) | sd(x) 0.068; h 22.4 d | `envs/v2/params/mispricing.json` (in force) |
| σ_V in force (needed by E5.2's net-of-V correction) | 0.01457/day | `envs/v2/params/value.json` |
| Discrimination table, post-D14 (coverage flat / crash / bull / SB) | 0.378 / 0.553 / 0.646 / 0.374 | `e4_21/discrimination.json` |

**Rule:** a figure that does not reproduce from its file is reported as a discrepancy and the file's value is
used.

---

## 2. Data — what was checked before any fit, and what it constrains

All fits use the E1.0 panel under Phase 1's exclusion rule (`tools/phase1/panel.py`: set A = 417 flag-free
names with full 2000–2024 histories). REG-15 applies: set A is survivor-only, and each fit states whether
survivorship plausibly biases it and in which direction.

Facts established **before this document was finished**, by inspecting the files (not by fitting anything):

1. **The SF Fed Daily News Sentiment Index is smoothed at source.** The series (17,018 calendar days,
   1980-01-01 → 2026-08-23, seven days a week) has AC(1) = 0.9967 and sd(Δs)/sd(s) = 0.081, which is the
   signature √(2(1−λ)) of an exponentially weighted trailing average with λ ≈ 0.9967 of a *persistent*
   underlying series. The FRBSF Economic Letter 2020-08 (Buckman, Shapiro, Sudhof & Wilson; read at
   https://www.frbsf.org/research-and-insights/publications/economic-letter/2020/04/news-sentiment-time-of-covid-19/
   on 6 Sep 2026) states the construction: *"a smoothed daily index as a trailing weighted average of the raw
   data, with weights that decline geometrically … We assume a depreciation rate of 5%"*. The index page
   confirms the geometric weighting but states no window. **Consequence, registered now:** the plan's "AR(1) of
   daily sentiment (FIT)" cannot be read off the published series. E5.5 deconvolves it under the stated kernel
   (§8) and fits on the recovered day-level series; the depreciation rate 0.05 is a **LIT** input read at
   source. The observed AC(1) of 0.9967 is far above 0.95, so the underlying day-level series is itself
   persistent — the deconvolution is well-posed rather than degenerate.
2. **EDGAR's submissions endpoint serves 8-K Item 2.02 dates from this machine** (probed on one CIK: 45
   earnings-release 8-Ks with report dates). E5.2's announcement-lag distribution is therefore fitted on
   release dates, as the plan names, with the 10-Q/10-K filing lag already in the panel published beside it.
   If the fetch fails for part of the universe, the achieved coverage is stated and the filing lag is the
   fallback for the uncovered names, with the plan's "up to two weeks" caveat.
3. **EDGAR quarterly EPS and DPS coverage in set A.** On the first 120 names: 118 carry quarterly basic EPS,
   98 carry a DPS concept (declared or cash-paid); 8.3 % of quarters have negative basic EPS (n = 18,468
   quarters). Phase 1 measured 19.5 % of stock-months with EPS_ttm ≤ 0 on the same set. The share of
   non-payers is a fitted quantity of E5.3, not an assumption.
4. **The Shiller file carries CAPE monthly to 2026.08** (E5.5 design B); **AAII is weekly, 1987-07 → 2026-08,
   unsmoothed** (the `Mov Avg` column is a separate 8-week average and is not used).
5. **Damodaran `pedata.xls` and `divfund.xls` (Jan 2026 update)** are industry-level cross-checks only; no
   parameter is taken from them.

---

## 3. The common estimator: the per-field-group ablation (E5.7a)

Every design contest in this phase is decided by the same statistic, defined once here and computed by one
tool (`tools/phase5/e5_7a_ablation.py`) on stored panels, so that no two arms can differ in estimator.

**Panel.** The standard evaluation panel (SEP) design of Phases 1–4: `envs.synthetic_market.audit_panel(200,
200, seed0=30000)` — per seed s ∈ [30000, 30199]: flat s; bull-trap s; bull-trap event-first 1000+s;
sustained-bull s; crash s at δ ∈ {0.55, 0.70, 0.85}; crash event-first 1000+s. **1,600 paths, 320,000 rows,
288,000 modelled rows** after the audit's 5 lags. The baseline is the stored post-D14 panel
`_panels/sep_phase4_after.pkl`, whose paths are re-verified against the current generator on 8 seeds before
use (P4-19: the state measured must be the state deployed).

**Feature construction.** `evaluation.leakage_audit._prepare(panel, shown, "level_free")` **unchanged**
(the frozen audit's lags, returns and level-free derivations). The BASE set is the audit's level-free control
(`LEVEL_FREE_KEYS` + lags: returns 1/5/20, log P/SMA20, log P/SMA50, RSI14, MACD/P, MACD_signal/P, trend
fields). The field groups, each added as its rendered fields plus their 5 lags:

| group | rendered fields |
|---|---|
| LEVELS | `price`, `SMA20`, `SMA50`, `MACD`, `MACD_signal` (the price-denominated levels, rendered under mechanism C's per-seed scale) |
| VAL | `reported_PE`, `dividend_yield`, `days_since_eps_announcement` (+ the `reported_PE_nm` indicator once E5.2 introduces "n/m") |
| ANALYST | `analyst_fair_value` |
| SENT | `news_sentiment`, `sentiment_MA5`, `sentiment_change` |
| VOL | `volume`, `volume_ratio` |
| IV | `implied_volatility` |

FULL = BASE ∪ all groups. (The audit's own "full" set is the 18 fields + lags without the derived level-free
columns; it is reported beside FULL for continuity, but FULL is the ablation's reference.)

**Statistics.** For target y ∈ {x, log V}:
- add-one: ΔR²_add(G) = R²(BASE ∪ G) − R²(BASE);
- drop-one: ΔR²_drop(G) = R²(FULL) − R²(FULL \ G);
- for the macro-phase clock (L2b): the same two differences in classification accuracy.

**Estimator.** `HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6, random_state=0)`
— the audit's `gbt`, which is the best of its three models in every full-field x cell of the post-D14 audit
(calm 0.233 vs mlp −0.227 / ridge −0.701; event 0.854; resolution 0.744; all 0.805) and in every log V cell.
Ridge and MLP are not run in the ablation (compute; their inferiority on this panel is on file). 5-fold
`GroupKFold` by path, OOS predictions, R² over the scored population. The L2b classifier is the audit's
`HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_depth=4)`.

**Populations.** (P-all) fitted and scored on all rows; (P-calm) fitted **and** scored on calm rows only — the
`tools/phase3/e3_9_calm_trained.calm_trained` construction, which is the brief's quantity (P4-36).

**Intervals.** 500-resample percentile cluster bootstrap over paths from per-path sufficient statistics (the
audit's `_cluster_ci`), with the **same resample indices applied to both arms of every difference**, so the
CI of a difference is a paired CI.

**Primary decision statistic.** ΔR²_add(G) for target **x** on **P-all**. Co-reported everywhere: P-calm, the
log V target (and MAPE(V)), drop-one, and the L2b accuracy differences.

**Two kinds of "null margin", each used where the register's wording calls for it:**
- *Absolute admissibility of a field* ("its selectivity is inside the null margin"): the **permutation null
  margin** of group G = the 95th percentile of ΔR²_add(G) when G's columns are permuted **across paths**
  (each path receives another path's whole G block, so within-path structure survives and only the link to
  that path's x is broken), over **N_PERM = 20** permutations on P-all. With 20 draws the 95th percentile is
  the 19th order statistic; its resolution is stated with the number. Computed for the groups whose rule needs
  it (ANALYST for E5.4; SENT for E5.5; VOL for E5.6's onset margin is a different null, §10c).
- *Comparison between two designs* ("lower by more than the null margin"): the paired cluster-bootstrap 95 %
  CI of the difference in ΔR²_add between the two arms **excludes zero**. Both arms are rendered from the same
  hidden paths wherever the design is post-hoc (E5.1, E5.2, E5.3, E5.4, E5.6 — the multiple, EPS, DPS,
  analyst and volume blocks are computed from the stored V, P and r), so the pairing is exact; sentiment arms
  (E5.5) change the price path through `b_pred` and are paired by seed only, which the report states.

**Sample size.** 1,600 paths is the plan's 200 seeds. From the post-D14 audit the cluster-bootstrap half-width
of an all-rows R²(x) is ≈ 0.011 and of a calm R² ≈ 0.06; paired differences are tighter. The effects at stake
are ≥ 0.02 (§7's analytic expectation for the analyst field at the LIT sd) against a permutation null whose
scale is measured in the baseline before any design is run; `prereg_power.py` records whether 0.02 is
separable from that null at this n (PP5) **before** E5.4 is decided.

**Baseline first.** The ablation is run on the current fields (the post-D14 state) before any generator
change, and that table is the reference every later arm is differenced against.

**The level-free residual (≈ 0.118).** The calm-trained level-free channel carries no field at all; the fields
can reach it only through the sentiment feedback `b_pred` (s → next-day return). Registered experiment: the
calm-trained level-free R²(x) (the `e3_9` estimator, unchanged) on a re-simulated SEP panel with
`b_pred = 0`, against the baseline. The difference, with its CI, is the feedback's share of the residual;
whatever remains is the event block's and the process's, and is handed on with that label.

---

## 4. E5.1 — the multiple (REG-10a)

### 4.1 Fits (EDGAR EPS × Yahoo prices, set A)

The monthly trailing P/E panel of Phase 1 (`tools/phase1.e1_2_pv.monthly_pe_panel`: trailing-4Q basic EPS as
known at each month-end from filings, consecutive quarters within 400 days, Q4 derived from FY where needed;
2009-06 → 2024-12) is **reused unchanged**.

| quantity | definition | reported |
|---|---|---|
| cross-section | pooled stock-months with EPS_ttm > 0 | P5 / P10 / P25 / P50 / P75 / P90 / P95, pooled and **by year**; n stock-months, n stocks; 1,000-resample stock bootstrap on each pooled quantile |
| n/m share | stock-months with EPS_ttm ≤ 0 | share pooled and by year (E5.2's target statistic) |
| quarterly persistence | per stock, log P/E at quarter-end months (Mar/Jun/Sep/Dec), OLS AR(1) with intercept, ≥ 20 quarters | median ρ_q with stock bootstrap; Andrews median-unbiased ρ from Phase 1's table beside it |
| dispersion decomposition | var(log P/E pooled) = between-stock (variance of stock means) + within-stock (variance of stock-demeaned values) | both, with CIs |
| P99 | pooled P99 of trailing P/E (the cap, E5.2) | value |
| cross-check | Damodaran `pedata.xls` industry current P/E (Jan 2026) | median and IQR across industries, reported only |

### 4.2 Designs (all implemented behind `multiple_design`)

- **A** — fixed k per seed, drawn by inverse CDF from a 33-point empirical quantile grid of the pooled
  cross-section truncated to the width (the Phase-4 sampler, `schedule._draw`'s grid form). Widths: **P10–P90
  (default, the plan's E5.1 text)**, P25–P75, P5–P95.
- **B** — k_t = exp(μ_k + z_t) per seed: μ_k from the between-stock grid (stock-mean log P/E, truncated to the
  width's quantiles of the between-stock distribution); z_t a daily log-AR(1) with ρ_d = ρ_q^{1/63} and
  stationary sd s_w = √(max(var_within − var(x)_engine − s_EPS²/4, 0)), i.e. the within-stock dispersion **net
  of the mispricing the engine already puts into P/E and net of the EPS noise E5.2 fits** (both would
  otherwise be double-counted; log P/E = x + log k − log(noise in the trailing sum), and the trailing sum of
  four independent multiplicative noises has variance ≈ s_EPS²/4). If the net variance is ≤ 0 the design is
  reported as degenerate and A stands. *[Correction made 6 Sep 2026 before any E5.1 or E5.2 output was read: the
  first draft subtracted 2·s_EPS², the variance of a seasonal difference of the quarterly noise, which is not the
  quantity that enters the level of log P/E.]*
- **C** — k tied to rendered characteristics: **dominated** (no characteristic is rendered; the observation
  contract is unchanged). Recorded, not run.

The v2 `U(14, 22)` stays retrievable as `multiple_design="v2"`.

### 4.3 Checks and decision rule

**KS check (per design and width).** Statistic: two-sample KS between the per-path median rendered P/E over
days with a numeric P/E (one number per path, n = 1,600) and the EDGAR pooled stock-month P/E truncated to the
same width. Rule: bootstrap 95 % upper limit of D < 0.10 (protocol §1(a)). PP1 records the null floor at these
n (≈ 0.034 at 1,600 vs ≈ 50,000), so the bound is decidable. A design that fails the check is a broken sampler,
not a losing arm: it is fixed and re-run, and the report says so.

**Decision (at the default width P10–P90).** Among {A, B} passing the KS check: **B if the paired 95 % CI of
ΔR²_add(VAL)_A − ΔR²_add(VAL)_B (x, P-all) lies above zero, else A** (simpler). The L1 extended inversion
share (§10b) of the P/E candidate is reported for both and must not move the other way by more than its own
paired CI; if it does, the contest is reported as **undecided** and A stands as the simpler design.

**Widths.** P25–P75 and P5–P95 are measured on the adopted design (ΔR²_add(VAL), KS, inversion share) and
recorded as the Phase-9 sensitivity settings; they do not change the adoption.

**Reported if the rule is not met.** Both arms' tables with CIs; the verdict; A retained as the simpler design
with the reason.

---

## 5. E5.2 — EPS and the announcement lags

### 5.1 Fits (set A, EDGAR basic EPS, quarterly rows of 80–100 days; Phase 1's dedup rule)

| quantity | definition | use |
|---|---|---|
| seasonal-RW residual, relative to level | ε_q = (E_q − E_{q−4}) / L_q, L_q = mean of \|E\| over the four preceding quarters (a level that is defined for negative quarters; the choice is DESIGN and stated) | sd, robust sd (1.4826·MAD), P10/P50/P90, excess kurtosis; stock-bootstrap CIs |
| log seasonal change, positive pairs | log(E_q / E_{q−4}) for E_q, E_{q−4} > 0 | sd, robust sd — the quantity the generator's multiplicative noise must match **net of V**: s_EPS = √(max((s_log² − 252·σ_V²)/2, 0)) with σ_V from `value.json` (the generator's own annual V change enters E_q/E_{q−4} once; the noise enters twice) |
| loss quarters | share of quarters with E_q < 0; P(E_q < 0 \| E_{q−1} < 0) and P(E_q < 0 \| E_{q−1} ≥ 0); loss size −E_q / L_q (33-point grid) | the two-state loss chain and its size distribution |
| n/m frequency | share of stock-quarters with EPS_ttm ≤ 0 (and the stock-month share from E5.1) | the target statistic the generator's rendered field is compared with |
| announcement lag | 8-K Item 2.02 report date − fiscal period end, matched to the nearest preceding quarter-end in the EPS table within [0, 120] d, first 8-K per period | P10/P50/P90, 33-point grid; n filings, n stocks, coverage of set A |
| filing lag (beside) | 10-Q/10-K `filed` − period end (already in the panel) | P10/P50/P90; the SEC deadlines 40/45 d (10-Q) as the LIT sanity bound |

### 5.2 Design (behind `eps_design`)

Quarterly EPS_q = (V_q / 4k_q) · exp(s_EPS·η_q) in a normal quarter; in a loss quarter EPS_q = −(V_q / 4k_q)
· λ_q with λ_q drawn from the loss-size grid; the loss state follows the fitted two-state chain, **independent
of x and of the phase label** (DESIGN, stated: a label-tied loss rate would be the phase clock the module
forbids, and a V-tied one is a hidden-state channel the audit would have to price). Trailing-4Q EPS is the
sum of the last four announced quarters; **P/E is rendered "n/m" when trailing EPS ≤ 0** (the observation
value is the string `"n/m"`, exactly as data vendors show it) and **capped at the FIT P99** otherwise.
Announcement lags are drawn by inverse CDF from the 8-K lag grid (replacing `U(25, 35)`), from the `announce`
stream as now, so the V announcement jump of jump placement `V_announce`/`both` still shares the date.
The v2 behaviour is `eps_design="v2"` and is proved inert-when-off (§12).

**The n/m indicator in the audits.** The frozen audit keeps only numeric observation values, so an "n/m" day
would otherwise be dropped. Every Phase-5 audit tool post-processes its panel: `reported_PE` ← the P99 cap on
n/m days and `reported_PE_nm` ← 1 on those days, and the indicator is passed to `run_audit` as a shown field —
the attacker sees "n/m" and may encode it; the audit must too.

### 5.3 Checks

- Realised n/m share of rendered days on the SEP panel, with a path-cluster CI, against the EDGAR stock-month
  share with its CI — **reported, no gate** (the loss chain is FIT; the trailing sum is an outcome).
- Realised seasonal-change sd of the generator's quarterly EPS (positive pairs) against s_log's CI — the
  net-of-V arithmetic is verified by measurement, not assumed.
- **The residual clock (P4-29).** `tools/phase4/e4_7_calendar.eps_clock` re-run **unchanged** on 200 flat paths
  (seeds 326000+, the E4.7 block) under the new lag distribution; and, to test the one mechanism this phase can
  name, the same statistic restricted to interior days 64–137 (excluding the window's edges) — if the residual
  vanishes on interior days the edge is the mechanism; if not, it is reported as unexplained. Rule: none; the
  residual is reported with its null.

---

## 6. E5.3 — dividends (blocked on D10; both variants carried)

### 6.1 Fits (set A, EDGAR `CommonStockDividendsPerShareDeclared`, fallback `…CashPaid`, quarterly rows)

| quantity | definition | reported |
|---|---|---|
| payer share | stocks with any positive quarterly DPS in the window; and the share of stock-years with DPS = 0 | shares with CIs |
| payout | annual DPS / annual EPS per stock-year with EPS > 0 | median, IQR, stock bootstrap |
| stickiness (Lintner at quarterly frequency) | ΔD_q = a + c·(τ·E_q⁺ − D_{q−1}) + e, pooled OLS with stock-clustered SEs, E_q⁺ = max(E_q, 0); and the share of quarters with D_q = D_{q−1} | c (speed), τ (target payout), share unchanged |
| crash behaviour | on `e4_1/dd30.csv` fast-crash episodes with DPS coverage: P(DPS cut ≥ 20 % within four quarters of the peak) vs the unconditional cut rate | both with CIs, n episodes / stocks |

The aggregate-annual speed of adjustment ≈ 0.3 (secondary sources, plan §9.1) is a **sanity range only**;
Lintner (1956) was not readable and no number from it is used.

### 6.2 Design (behind `dividend_design`)

DPS_q = (1 − c)·DPS_{q−1} + c·τ·EPS_q⁺ with the FIT c and τ; a per-seed payer/non-payer draw at the FIT payer
share (a non-payer renders yield 0.00); `dividend_yield = 4·DPS/P·100`. The crash cut rate is an **outcome**
of the fitted chain and is reported against the panel's. **D10 variants:** `dividend_field="shown"` (default =
v2 rendering) / `"hidden"` (the key is absent from the observation, like `day_index_mode="none"`); both are
audited (§10a) and the phase does not choose.

---

## 7. E5.4 — the analyst estimate (REG-10d)

### 7.1 Literature and the sd mapping

The read anchor (plan §9.1, LOG §4.3): absolute target-price error ≈ 45 % of price at 12 months (Bradshaw,
Brown & Huang 2013; Bilinski, Lyssimachou & Walker 2013: 44.7 %). Pre-registered mapping: for Gaussian log
error, E\|u\| = sd·√(2/π), so **sd = 0.45 · √(π/2) = 0.564** if the 45 % is a mean absolute log error. The
horizon mismatch is stated: the field is a fair-value estimate, not a 12-month target. Persistence stays
DESIGN (ρ = 0.95 per 5-day update; no free data). The Phase-9 bracket is {0.30, 0.45, 0.60}; the v2 value 0.15
is below every read value. **The report states plainly that no free data can fit this sd.**

An analytic expectation, stated before the run so it can be wrong: log(F/P) = u − x is level-free and directly
readable, so a single-day reader's R² for x is ≈ var(x)/(var(x)+var(u)) = 0.0046/(0.0046+0.0225) ≈ 0.17 at
sd 0.15 and ≈ 0.014 at sd 0.564; with lags and u's persistence the GBT does somewhat better. The expectation is
therefore that **no LIT sd is admissible** against a permutation null of order 10⁻³, and the phase is
prepared for it.

### 7.2 Options (behind `analyst_design`)

- **A** — F_t = V_t·e^{u_t}, u AR(1) as now, stationary sd ∈ {0.30, 0.45, **0.564**, 0.60} (four re-rendered
  arms; the anchor and the bracket). `analyst_design="v2"` retrieves sd 0.15.
- **B** — drop the field (`analyst_field="hidden"`).
- **C** — a lagged smoothed price proxy: F_t = SMA250_t · e^{u_t} with u the LIT-sd (0.564) AR(1) noise, so the
  field keeps an analyst estimate's dispersion but is a function of the price path and its own stream only —
  level-free and x-free by construction. (The register's alternative, k × trailing EPS, re-opens E5.1's V
  channel and is not run.)

### 7.3 Decision rule

- A at sd σ is **admissible** iff ΔR²_add(ANALYST at σ) ≤ the permutation null margin of the ANALYST group
  (x, P-all), **and** its onset ΔAUC passes §10c.
- If any A arm is admissible, adopt A at the admissible sd **closest to the anchor 0.564**.
- Otherwise C is implemented and carried as the **provisional default**, exactly as D13's provisional B was: C's
  own selectivity is measured (expected ≈ 0; the test in §11 asserts it), and **C vs B is Phase 9's** (its
  condition — "its inclusion changes no arm contrast beyond the equivalence margin" — is an LLM-grid statement
  no generator audit can evaluate). B is the fallback if Phase 9 rejects C. The provisional status is written
  into `observables.json` with its owner.
- L5: the observables-oracle MCR with and without the field is reported on the **final** state (§10d), not per
  arm (compute: ≈ 1 h per L5 run; the L2 statistic carries the CI and the null, L5 corroborates).

---

## 8. E5.5 — sentiment (REG-10b; REV-2b: the valuation loading is not zeroed by fiat)

### 8.1 Fits

**(a) Deconvolution (SF Fed, calendar-daily).** raw_t = (s_t − λ·s_{t−1}) / (1 − λ), λ = 0.95 (LIT, §2.1).
Reported: sd(raw), AC(1), AC(2), the AR(1)-plus-measurement-noise-corrected persistence ρ̂ = AC(2)/AC(1)
(exact for AR(1) + white noise), all with 250-day moving-block bootstrap CIs; and the same statistics on the
published smoothed series for the record. The **kernel assumption is stated as LIT+DESIGN**: geometric weights
are documented, the rate 0.05 is read at source, the recursion form is assumed exact.

**(b) Return loadings (market level, daily).** Market return = F-F `Mkt-RF + RF` (decimal), standardised by
its trailing 252-day sd. raw sentiment aligned to trading days by averaging over the calendar days since the
previous trading day. Fitted in the generator's own form: raw_t = c + ρ·raw_{t−1} + b₀·z_t + b₁·z_{t−1} + e_t,
OLS with Newey–West(10) SEs, full sample 1980–2026 and the four sub-periods of `PanelSpec`; loadings are
reported **per sd of standardised return and per sd of raw sentiment** (the units the generator uses).
Cross-check: the distributed-lag form with lags 1–5.

**(c) The reverse regression (Tetlock's direction).** Mkt_{t+1} = a + γ·std(raw_t) + Σ_{h=1..5} φ_h Mkt_{t+1−h}
+ e; γ in bp per sd, NW SEs, against Tetlock's read 8.1 bp next-day and 6.8 bp reversal over days 2–5. `b_pred`
stays the LIT value in every design; γ is its cross-check and is reported.

**(d) The valuation link (design B; monthly, market level).** Monthly mean raw sentiment on the log-CAPE
deviation from its trailing 120-month mean (DESIGN; the full-sample-mean alternative reported), NW(12) SEs,
1980-01 → 2026-08 (Shiller CAPE). "Full Baker–Wurgler-sized" = that coefficient; "half" = half of it. The
transfer of a market-level coefficient on log-CAPE deviation to a single stock's x = log(P/V) is **DESIGN** and
is stated as such.

**(e) AAII (design C; weekly).** y_w = Bullish − Bearish; AR(1) with intercept; loading on the standardised
weekly S&P log return (AAII's `Close`) contemporaneous and lag 1; NW(4) SEs; 1987-07 → 2026-08.

**Like-for-like references for rule (i).** The checklist's item-12 statistics are 200-day-window quantities
(ACF(1) of s; corr(s_t, r_t)). The FIT references are therefore the **same statistics computed on the
deconvolved SF Fed series in rolling 200-trading-day windows** (median across windows, block-bootstrap CI),
not the full-sample parameters — one estimator on both sides (P4-1's lesson).

### 8.2 Designs (behind `sentiment_design`; `b_pred` feedback kept in all three)

Raw process standardised to unit stationary sd, then the field is s_t = tanh(S_RAW·raw_t) with S_RAW a
**DESIGN** rendering constant set so that sd(s) matches `SENT_SD_REF` = 0.35 (the constant the `b_pred`
standardisation already uses); the jitter lag applies as now.
- **A** — returns-only: raw_t = ρ·raw_{t−1} + b₀·z_t + b₁·z_{t−1} + σ_e·ε_t (all FIT from (b)); level-free and
  x-free by construction.
- **B** — A plus a slow valuation link: + c_val·x_{t−j} in standardised units (c_val from (d), transfer DESIGN);
  run at "full" and "half".
- **C** — survey-style: the field updates every 5 trading days with ρ_w and the weekly-return loading from (e),
  held constant between updates.
- `sentiment_design="v2"` retrieves the current 0.6·tanh(2x) construction.

### 8.3 Decision rule

(i) A design **meets the item-12 references** iff the generator's median 200-day ACF(1) of s and median
corr(s_t, r_t) each have a 95 % path-cluster CI overlapping the data's window-median CI (the SF Fed reference
for A and B; the AAII weekly reference, on 40-week windows, for C).
(ii) Among designs meeting (i): adopt the one with the lowest ΔR²_add(SENT) (x, P-all) whose onset ΔAUC
passes §10c. **B's valuation link is retained only if the paired 95 % CI of ΔR²_add(SENT)_B − ΔR²_add(SENT)_A
includes zero** (its increment is inside the null margin); otherwise B is reported as the labelled sensitivity
("full"/"half") and is not the default. If no design meets (i), the one closest to the references (by the
sum of standardised distances) is carried as **INCUMBENT-BY-DEFAULT** with the shortfall stated, and D15 is
put to the team with the table. **D15 is the team's** after this table exists.

---

## 9. E5.6 — volume (REG-10c)

### 9.1 Fits (set A, daily, 2000–2024)

Per stock: lv_t = log Volume_t − trailing-252-day mean of log Volume (DESIGN detrending, stated — the panel has
no shares outstanding, so turnover is not available and the level is removed by a trailing mean). Then
lv_t = ρ_v·lv_{t−1} + β·(\|r_t\|/σ̂_t − E\|z\|) + σ_e·ε_t with σ̂ the trailing-252-day return sd, OLS per stock;
medians of ρ_v, β, σ_e with stock bootstrap; sub-periods. Cross-check: Lo & Wang's weekly turnover AC(1)
0.91/0.87 (read; market level, weekly — a sanity range, not the value).

Run-up turnover ratio (GSY-style): on `e4_1/runup4.csv` episodes, the mean of lv over [start, top] minus its
mean over the 252 days before `start` (a log ratio); median with episode/stock bootstrap; n. Also the same
ratio as a function of the trailing 252-day log return in the whole panel (the level-free form design B
needs): β_ru from lv_t on max(ret_252,t, 0) alongside the AR and \|r\| terms.

### 9.2 Designs (behind `volume_design`)

- **A** — lv_t = ρ_v·lv_{t−1} + β·(\|r_t\|/σ − E\|z\|) + σ_e·ε_t, σ the trailing-252-day sd of the generator's
  own observed returns (level-free; no phase input).
- **B** — A + β_ru·max(ret_252,t, 0) (the run-up elevation, driven by the observed trailing return, not by
  the label).
- The v2 `1.2·\|x_{t−j}\|` loading is recorded as **dominated** (no read source links volume to mispricing)
  and retrievable as `volume_design="v2"`.

### 9.3 Decision rule

**B iff the run-up log-ratio's 95 % CI excludes zero (the ratio's CI excludes 1) AND B's onset ΔAUC over the
price-derived reference is ≤ the null p95 at every transition (§10c); else A.** Checklist item 7 is re-derived
by Phase 6; here its statistics are reported for both designs beside the panel's own values.

---

## 10. E5.7 — the audits

### 10a. Per-field-group ablation (§3), run at three moments

1. **Baseline** on the stored post-D14 panel, before any change.
2. **Per arm** for every design contest (§4–§9), on re-rendered or re-simulated SEP panels.
3. **Final** on the handed-over state, after `observables.json` settles (P4-45), beside the D10 and analyst
   variants.

Outputs per run: the add-one / drop-one tables for x, log V (with MAPE) and the L2b accuracy, P-all and
P-calm, with paired CIs; the permutation null margins where computed; `e5_7a/<state>/ablation.{json,md}`.

### 10b. The L1 extended candidate set

On the same panels, in-sample (the attacker's most favourable case), with the free scalar k fitted as the
audit does: (1) the audit's single-field candidates; (2) pairwise geometric means of the valuation
candidates (P/PE, P·DY, F) with price; (3) the least-squares best linear combination in logs of up to three
candidates; (4) the median of the three valuation candidates. Statistics: median APE, within-1/2/5 % shares,
share above the 1 % floor; the **inversion share** = the within-5 % share of the best candidate, with a
path-cluster CI. No gate (Phase 6's method derives the gate); E5.1 uses the paired change.

### 10c. The onset-detection audit (REV-11b), with a label-permutation null

200 crash seeds (δ 0.70, seeds 410000+) and 200 bull-trap seeds (411000+), `schedule_mode` pinned to the
deployed value. Transitions: crash calm→deterioration, deterioration→panic, panic→stabilisation; bull-trap
calm→mania, mania→blow-off, blow-off→post-top. Labels: 1 on days τ−3 … τ+3 of the transition ("within ±3
days"); 0 on days at least 10 days from every transition; other days excluded. Per field, the day score is
\|Δ field\| for bounded/signed fields and \|Δ log field\| for positive level fields (n/m days excluded for
P/E). The **price-derived reference** is the best AUC over the fixed set {\|r_t\|, \|ret_5\|, \|Δ log √(252·fc_t)\|
with fc the IV filter's own past-only forecast on observed returns, \|Δ RSI14\|, \|Δ log(P/SMA20)\|}.
Statistic: ΔAUC_f = AUC_f − AUC_ref, pooled day-level. **Null:** 500 per-path circular shifts of the label
vector (a seed-label permutation is degenerate when paths share a day axis, P4-29; a per-path shift preserves
the label structure and destroys alignment — the E3.5 construction, whose p95 was +0.032 for IV). PP2 simulates
this null's scale at the intended n before the tool is trusted. **Rule:** for every field and transition,
ΔAUC_f ≤ the null's 95th percentile. Timing error: per path, the day of the field's maximum score within
[τ−10, τ+10] minus τ (median and IQR). A field failing the rule is redesigned or dropped, and dropping is
reported.

### 10d. The v2 gates, for the record (on the final state)

The SEP audit (L1/L2/L2b/L4 via `evaluation.leakage_audit.run_audit`, level-free control, no subsampling, the
n/m indicator passed as a shown field), the calm-trained comparison (`e3_9` estimator unchanged, Phases 3, 4
and 5 in one process), the checklist at 200 seeds (SCL, seeds 40000+), the path hashes, and the discrimination
table (L5 at 40/50 seeds through an oracle subclass that encodes "n/m" exactly as the audit does, the frozen
`ObservablesOracle` otherwise unchanged). The two Phase-6 gates (`test_v2_L2_surrogate_thresholds`,
`test_v2_L2b_phase_clock_selectivity`) stay registered as Phase 6's; their values are reported.

---

## 11. Tests (plan §9.4) and their tolerances

| test | asserts | tolerance provenance |
|---|---|---|
| `test_observable_params_provenance` | `params/observables.json` exists, every entry carries label / source / date / interval / n and a declared status; the loader raises on a missing entry, a null interval and an undeclared status; the constants in force equal the file | structural |
| `test_no_field_is_deterministic_in_x` | the stored final ablation: every group's ΔR²_add(x, P-all) ≤ the **PROVISIONAL** bound written in `observables.json` (0.20 = `leakage_audit.L2_SELECTIVITY_R2`, amendment A8's reference value, to be replaced by Phase 6's derived margin — labelled as such); live guard on an 8-seed panel that no single field alone reaches R²(x) ≥ 0.90 | the bound is the plan's own reference number, not a new stipulation; Phase 6 owns the derived one |
| `test_onset_audit_bound` | the stored `e5_7c` result: no (field, transition) exceeds the null p95; live guard that the audit computes | the null is measured |
| `test_sentiment_level_free` | `SentimentState` output is bit-identical when P and V are both scaled by a constant (any design) and when P alone is scaled (designs A and C) | exact |
| `test_eps_lag_distribution` | the announcement lags the generator draws (500 seeds) lie inside the FIT grid's range and their median is nearer the panel's P50 than the grid midpoint (the Phase-4 sampler test) | grid from the file |
| `test_observables_switches_preserve_v2` | with every observable switch at its v2 setting, `earnings_block`, `analyst_block`, `volume_block`, `SentimentState` reproduce the committed HEAD functions exactly on 50 random inputs, and the path-hash fixture reproduces `path_hashes_phase4_after.json` | exact (the freeze rule) |
| `test_phase5_report_parameter_table_matches_observables_json` | the report's parameter table equals the file's statuses (the P4-47 pattern, verified by negative control) | exact |

---

## 12. Compute and the offload rule

- **Local (reference machine):** every scikit-learn fit — the ablation, its permutation nulls, the SEP audit,
  the calm-trained comparison, L5, the onset AUCs. Independent jobs overlap at 2 threads each, at most three
  at once (P4's measured guidance); nothing else heavy runs beside the SEP audit.
- **Local, minutes:** the data fits of §4–§9 (EDGAR, SF Fed, AAII, Shiller, the volume panel); the 8-K fetch
  (≈ 800 requests at ≤ 3/s).
- **Kaggle (estimator-free simulation only):** re-simulated SEP panels for the sentiment arms and `b_pred = 0`
  if local generation would serialise behind the fits; the reference-row guard runs on the first kernel and a
  Kaggle-built panel is compared bit-for-bit with a locally built one on 8 seeds before use. `datasets/` never
  leaves this machine.
- **The lab GPU box is not used.**
- **Reduced designs, fixed now:** the ablation runs GBT only (§3); the permutation null uses 20 draws
  (§3); L5 runs on the final state only (§7.3). Each is stated in the report with its cost in resolution. No
  pre-registered seed count is cut.

---

## 13. What is reported if a rule is not met

The achieved value with its n and CI, the constraint that binds, and the verdict **not met** or **undecided**
— never a moved threshold. Every contest above has its "not met" branch written in its own section. Five
phases in a row have had at least one undecidable criterion; the one this phase expects (§7.1) is written
down before the run. `tools/phase5/prereg_power.py` checks each rule's decidability at its stated n and its
output is `e5_0/power.{json,md}`.

---

## 14. Order of work (measure after the parameter file settles)

1. `prereg_power.py` (inherited-number verification, PP1–PP6).
2. Baseline ablation on the stored post-D14 panel; the `b_pred = 0` arm; the baseline onset audit.
3. Data fits E5.1–E5.6 (parallel; minutes).
4. Implementation: every design a switch with the v2 behaviour behind it; the inert-when-off proof.
5. Arms and decisions in the register's order; `apply_e5.py` writes `observables.json` only after every
   contest is decided.
6. **Then, and only then:** the final ablation, onset audit, SEP audit, calm-trained comparison, checklist, L5
   and discrimination, path hashes, freeze — the two long audits in parallel with each other and with nothing
   else.
7. Whole test tree, staged; cite-check of the report; `PHASE_5_CHANGED_FILES.md` verified against disk.
