# Pre-registration addendum, Phase 5

Corrections and interpretations made **after** data were seen, each with a disclosure of exactly what had been
seen when it was written, following `PREREG_PHASE_4_ADDENDUM.md`. Results are reported under both the rule as
registered and the corrected rule wherever the two differ.

---

## 1. E5.7(c)'s price-derived reference set was too narrow: the technical fields are price-derived and belong on the reference side

### 1.1 Disclosure

Written after the **baseline** onset audit (`e5_7c/baseline/onset.{json,md}`, the 18 fields as handed over) had
been read, and before any arm's onset audit had been read. What had been seen: at three crash transitions and
one bull-trap transition, `SMA20`, `SMA50`, `MACD` and `MACD_signal` exceeded the registered reference
(the best of {\|r\|, \|ret_5\|, \|Δ log √(252·fc)\|, \|Δ RSI14\|, \|Δ log(P/SMA20)\|}) by more than the null's
95th percentile — e.g. \|Δ log SMA50\| at panic→stabilisation, AUC 0.755 against the reference's 0.655. The
same table also showed the two failures the audit exists to find: `analyst_fair_value` at crash
calm→deterioration (ΔAUC +0.034 vs null +0.001) and the three sentiment fields at bull-trap calm→mania
(+0.017 to +0.023 vs null ≈ +0.010).

### 1.2 Why the registered set was wrong

REV-11b's rule exists so that *"the premium's legitimate rise through returns is not scored as a leak"*: a
field may not detect a hidden transition better than the price path itself does. The moving averages and MACD
are deterministic functions of the price path (`technicals_block(P)`), so their detection power **is** the
price path's; scoring them against a five-member subset of the price-derived scores is a statement about the
subset, not about leakage. The registered set was chosen for the IV audit of Phase 3, where the reference was
"the same filter's forecast", and was carried over without asking which of the 18 fields are price-derived by
construction.

### 1.3 The corrected rule, registered before any arm's onset table is read

The price-derived reference is the **best AUC over the five registered scores and the scores of every
price-derived rendered field** (`SMA20`, `SMA50`, `MACD`, `MACD_signal`, `RSI14`, `trend_strength`,
`trend_regime`), and the rule *"ΔAUC_f ≤ null p95"* is applied to the **non-price fields**: `reported_PE`
(+ `reported_PE_nm`), `dividend_yield`, `days_since_eps_announcement`, `analyst_fair_value`,
`news_sentiment`, `sentiment_MA5`, `sentiment_change`, `volume`, `volume_ratio`, `implied_volatility`. The
technical fields' AUCs stay in every table for the record. The null is unchanged (500 per-path circular shifts).
The tool records both verdicts (`verdict` as registered, `verdict_nonprice` under this section) so nothing is
hidden by the correction.

### 1.4 Consequence for the baseline

Under the corrected rule the baseline fails on exactly the two channels Phase 5 exists to close — the v2
analyst field (V·e^u reads the deterioration's V decline) and the v2 sentiment (0.6·tanh(2x) reads the mania's
x). Under the rule as registered it fails on those and on four price-derived fields, which is reported as
registered and read as a defect of the reference set.

---

## 2. E5.6's rule: the run-up turnover ratio's CI excludes 1 from BELOW

### 2.1 Disclosure

Written after `e5_6/volume.json` had been read and before either volume arm's ablation or onset audit had
been read. What had been seen: the median run-up log ratio is −0.015 [−0.032, −0.001] (ratio 0.985
[0.969, 0.999]); the level-free loading β_ru is −0.012 [−0.020, −0.006] with sub-period signs +0.10 / −0.06 /
−0.08 / −0.06.

### 2.2 The interpretation, stated now

REG-10c's rule reads *"B if the FIT ratio's CI excludes 1 and B's onset AUC excess over price is inside the
null margin; else A"*, and its premise (GSY 2019, read) is that turnover is **elevated** in run-ups. A CI that
excludes 1 from below satisfies the clause's letter and contradicts its premise; the effect is 1.5 % of volume
and its level-free form changes sign across sub-periods, so what B would write into the generator is a
sign-unstable coefficient of no economic size. **The interpretation registered here:** clause 1 is read as
"the CI excludes 1 in the direction of the premise (a ratio above 1)". Under that reading B fails clause 1 and
**A is adopted** whatever the onset audit shows; under the letter of the clause B's adoption still depends on
its onset audit, and both verdicts are reported. B stays implemented and switchable with its FIT loading, and
its ablation and onset audit run regardless, so the cost of either reading is measured rather than argued.

---

## 3. E5.5 rule (i) is evaluated on the frequency each design lives at

### 3.1 Disclosure

Written after `e5_arms/stats.json`'s sentiment rows had been read. What had been seen: designs A, B-full and
B-half meet the daily 200-day-window references (ACF(1) 0.205 / 0.216 / 0.207 against 0.200 [0.154, 0.265];
corr(s, r) 0.017 / 0.004 / 0.011 against 0.006 [−0.028, 0.019]); design C's daily ACF(1) is 0.914 because the
field is held for five days by construction, and on the weekly statistics it gives ACF(1) 0.570 (inside the
AAII 40-week reference 0.537 [0.478, 0.581]) and corr 0.322 against 0.242 [0.142, 0.311] — **outside, by
0.011**.

### 3.2 What is registered

The pre-registration already says C is judged against the AAII 40-week references (section 8.3), so nothing
moves: **C does not meet rule (i)** on the weekly correlation, and is excluded from rule (ii). The size of the
miss and its mechanism are reported (the 40-week window-median loading b₀ = 0.298 per sd overshoots the
window-median correlation 0.24, because the ratio of medians is not the median of the ratio); the rule is not
relaxed to admit it.

---

## 4. E5.2 and E5.3: three estimator defects exposed by their own summary statistics

### 4.1 Disclosure

Written after `e5_2/eps.{json,md}` and `e5_3/dividends.{json,md}` had been read and before any arm that uses
them had been measured (the multiple / eps-dividend arm panels built from the first-pass files were discarded
and rebuilt). What had been seen:

- the seasonal residual relative to the level has plain sd **4,490** (excess kurtosis 12,658) against a robust
  sd of 0.41: a handful of quarters whose level L_q (the mean \|EPS\| of the four preceding quarters) is a few
  cents turn ordinary changes into ratios of thousands; the loss-size grid's top point is **541,538** for the
  same reason;
- the 8-K announcement-lag grid runs from **1 to 83 trading days**: a lag of one trading day cannot be a
  quarterly earnings release of that period (a matching artefact: an Item-2.02 8-K that is not the period's
  release), and 83 is the 120-calendar-day search cap;
- the pooled quarterly Lintner regression is **unidentified**: τ = 0.85 with a stock-bootstrap CI of
  [−0.06, 721] and c = 0.68 [0.00, 1.10], because quarterly EPS is too noisy a target base and 57.5 % of payer
  quarters carry an unchanged DPS;
- the payer share among names *reporting* a DPS concept is 1.000 (353/353), with 64 names of set A reporting
  neither concept.

### 4.2 What is corrected, each a stated DESIGN choice

1. **Level floor.** The residual and the loss size are computed on quarters whose level L_q is at least 10 % of
   the stock's median \|EPS\| over its history. The plain sd, robust sd and kurtosis are reported with and
   without the floor; the generator's s_EPS is the **robust** sd net of V (the plain sd is not a dispersion of
   the central distribution the Gaussian noise describes; the tails are the loss chain's).
   *Measured after the re-run:* the floor removes only **17** of 24,419 pairs and the plain sd stays at 4,491 —
   so the diagnosis in 4.1 ("levels of a few cents") was wrong about the largest values. Inspected: the two
   extreme pairs are **EDGAR scale errors** (TKR 2015-12-31 basic EPS −440,000; BBWI 2011-10-29 +320,000 — a
   quarterly EPS reported in raw dollars), and the next are genuine write-off quarters against a near-breakeven
   level (NOV 2019-Q2 −14.11 on a level of 0.07; CLF 2014-Q3 −38.49 on 0.36; NBR 2020-Q1 −56.73 on 0.53).
   0.45 % of pairs have \|residual\| > 10; without them the plain sd is 1.17. The robust sd (0.407 with or
   without the floor) is unaffected, the two scale errors fall outside the loss-size grid's P5–P95 truncation,
   and the floor is kept as stated. Nothing else changes.
2. **Grid truncation.** The loss-size and announcement-lag grids are 33-point quantile grids over the
   **P5–P95** of their distributions (the Phase-4 sampler's form, which truncated at P10–P90); the truncation
   points are recorded beside the grids, and the P10/P50/P90 quoted in the report are those of the untruncated
   distributions.
3. **Lintner, τ constrained.** The target payout τ is the FIT median annual payout (E5.3's own distribution,
   0.406 [0.373, 0.444]); the speed c is then the one-parameter OLS of ΔD_q on (τ·Ē_q − D_{q−1}) with Ē_q the
   trailing four-quarter mean EPS (floored at 0), stock-clustered SEs and a stock bootstrap. The unconstrained
   two-parameter fit stays in the file as the record of why.
4. **Payer share.** A name reporting neither DPS concept is a non-payer iff Yahoo's dividend column shows no
   cash dividend in 2009-06 → 2024-12 (the check is in `e5_3/dividends.json`); the payer share is then the share
   of set A that paid, not the share among reporters.

Nothing in the decision rules moves; these are estimator repairs of the kind the protocol's step 2 requires
to be documented rather than silently applied.

---

## 5. E5.1's KS check: the truncation convention decides the A-vs-B contest by itself

### 5.1 Disclosure

Written after `e5_arms/stats.json`'s multiple rows had been read and before either multiple arm's ablation had
been run (both are queued behind the baseline). What had been seen, per-path median rendered P/E over 1,600
paths against the EDGAR pooled stock-month cross-section, bootstrap 95 % upper limit of the KS distance:

| width | A vs data truncated to the width | B vs data truncated to the width | A vs untruncated data | B vs untruncated data |
|---|---|---|---|---|
| P10–P90 | **0.095 pass** | 0.152 fail | 0.112 fail | **0.082 pass** |
| P25–P75 | 0.121 fail | 0.340 fail | — | — |
| P5–P95 | **0.097 pass** | 0.110 fail | 0.091 pass | **0.076 pass** |

The sd of log per-path median P/E is 0.53 under A (P10–P90) and 0.76 under B against the pooled data's 1.10.

### 5.2 Why the registered convention is A's, not B's

The pre-registration (section 4.3) compares every design with "the EDGAR pooled stock-month P/E truncated to
the same width". The width is a parameter of **design A's fixed draw** (REG-10a: "a fixed k per seed from the
FIT range … at three widths"); design B's k_t is the fitted **pooled** process — a between-stock draw plus a
within-stock log-AR(1) whose dispersion is FIT (0.78) — and truncating its between-stock draw does not
truncate the process, so B's per-path medians spread beyond any band by construction and fail the truncated
check whatever the data say. Against the population B actually models, the untruncated cross-section, it
passes at both widths that matter; A, being truncated, fails there for the mirror-image reason.

### 5.3 What is registered, before the ablations are read

Each design is checked against **its own natural population**: A against the data truncated to its width, B
against the untruncated cross-section. Under that reading both A (P10–P90, P5–P95) and B (P10–P90, P5–P95)
qualify, and **the contest is decided by rule (ii) as written**: at the default width, B if the paired 95 % CI
of ΔR²_add(VAL)_A − ΔR²_add(VAL)_B (x, P-all) lies above zero, else A. A's failure at P25–P75 (0.121) stands as
a finding about that width: the within-path smearing of P/E by x and the EPS noise is too wide for a band that
narrow, and P25–P75 is recorded as **not KS-equivalent** for the Phase-9 sweep. Both KS conventions stay in the
report.

---

## 6. The permutation null margin is negative: the absolute-admissibility clause measures the cost of noise columns, not the zero of "no information"

### 6.1 Disclosure

Written after the baseline's permutation nulls (`e5_7a/baseline/ablation.json`, `null_margins`) had been read and
after every arm's ablation and onset audit was on disk, before `apply_e5.py` ran. What had been seen: over 20
across-path permutations of the group block on P-all, ΔR²_add(ANALYST) ranges from -0.0110 to -0.0057 (p95 estimate
-0.0057) and ΔR²_add(SENT) from -0.0039 to -0.0018 (p95 -0.0024). Every draw is **below zero**.

### 6.2 What the number means

A permuted block carries another path's field values — realistic marginals, no link to this path's x — and the
GBT spends splits on it, so its out-of-sample R² falls by 0.002 to 0.011. The null therefore sits at the noise
cost of extra columns, not at zero, and "ΔR²_add ≤ the null margin" (section 3's absolute clause; section 7.3's
first clause) can be satisfied by no rendered field: design C, which carries nothing by construction, is at
-0.0017 [-0.0046, +0.0014], above the margin. PP5 put the null "of order 10⁻⁴" because its synthetic check did not reproduce that
cost; the pre-registered scale was wrong in location, not in width (the 20 draws span 0.005).

### 6.3 What is done

Nothing in the decisions moves: the E5.4 rule is conjunctive and **every design-A arm fails its onset clause on
its own** (crash calm→deterioration, +0.017 to +0.021 against a null p95 of +0.001), so C is the provisional
default under the rule as registered whatever the first clause says; rule (ii) of E5.5 compares paired
increments between arms and does not use the absolute margin. The margin is reported as measured, the clause is
recorded as mis-specified, and it is **not** re-specified after the fact (a centred version — ΔR²_add minus
the null's median, or an interval test — is the obvious repair, and it is Phase 6's to register with its
derived margins). The `test_no_field_is_deterministic_in_x` bound (0.20, PROVISIONAL) is unaffected.
