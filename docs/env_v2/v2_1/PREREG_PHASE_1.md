# Pre-registration, Phase 1 (v2 → v2.1): value and price structure

Status: **written 29 August 2026 before any Phase-1 run**, on the working tree at commit `b679941` (Phase 0 frozen state,
`tests/v2_freeze_manifest.json` label "Phase 0 freeze", manifest hash `92ddcf52…`; E1.0 panel at `datasets/`). Governing
documents: `V2_1_IMPROVEMENT_PLAN.md` Section 5 (Phase 1), Section 1 (protocol), Section 3, 16, 16A, 17, Appendices A–B;
`V2_1_ALTERNATIVES_REGISTER.md` REG-1, 2, 3, 5, 15, 17; `PHASE_1_EXECUTION_PROMPT.md`. Decisions in force: **D1 = C
(hybrid)**, **D13 = provisional B**, **D16 = full programme**. WRDS access is **not confirmed** (blank in the brief), so
REG-15's option B is not available and every fit below runs on the free panel with its survivor-vs-literature gap
published; the fitting code takes the panel root as a parameter (`tools/phase1/panel.py::PanelSpec`) so that a
CRSP/Compustat re-run is a data-path change. No paid API call. Nothing is committed.

Everything below — the panel exclusion rule, the analysis sets, seed blocks, horizons, estimators, statistics,
bootstrap counts, pass/decision rules and what is reported when a rule is not met — is fixed here and is not moved
after any number is seen. If a rule turns out to be wrong, `PHASE_1_REPORT.md` says so, the replacement is derived in
a separately documented step, and the result is reported under both.

## 0. Provenance labels and the citation rule

LIT / FIT / CAL / DESIGN as the plan defines them. Every number that enters `envs/v2/params/value.json`, a test
tolerance or a document in this phase is FIT on the panel described in §1, or DESIGN with the alternatives and the
discriminating experiment stated, or CAL carried over from v2 with that label (jump total rate 0.010/day, jump size
sd 0.03 — both re-fitted in Phase 3). Literature statistics are **quoted beside** the fitted values, never used as a
tolerance. Citation statuses in the report come from `reviews/V2_1_PLAN_VERIFICATION_LOG.md` §4 ("read by the third
pass, 26 Aug 2026"); Phase 1 re-reads nothing and marks each row accordingly; a statistic marked "(to verify)" or
NOT-RETRIEVABLE may not appear in a parameter file, a tolerance or a slide.

## 1. The panel: exclusion rule and analysis sets (E1.0 report Q7; set here before any statistic is computed)

Inputs: `datasets/_manifests/ticker_reuse_screen.csv` (five flags), `datasets/_manifests/survivorship_accounting.csv`,
`datasets/01_prices/daily/*.parquet`, `datasets/03_fundamentals/by_ticker/*.parquet`, `datasets/02_constituents/`.

**Exclusion rule (fixed):**
1. Exclude every ticker with `n_flags > 0` in the reuse screen (86 of 673). Reason: each flag is evidence that the series
   is not the constituent (E1.0 §1.3); the start-date flag was validated by two independent methods on `UK` and `GP`
   (E1.0 §9.4). No per-name adjudication is done (it would be a judgement call made after seeing the data).
2. Duplicate spellings (`BF.B`/`BF-B`, `BRK.B`/`BRK-B`; checked identical to the last decimal on 6,539 rows): keep the
   Yahoo symbol with `-`, drop the `.` file.
3. Window: 2000-01-03 → 2024-12-31 (plan E1.0). Rows outside the window are dropped before any statistic.
4. Returns: daily log returns of `Adj Close` (split- and dividend-adjusted; `Close` would carry split discontinuities).
   No winsorising, no filling (E1.0: nothing is cleaned; the reuse rule removes the series that carried the 21× days).
   Prices for the start-price range (E1.1) use unadjusted `Close` (what a trader sees).

**Analysis sets (fixed):**
- **Set A — the large-cap analysis set (primary):** flag-free, full-history names (`full_history = True`: first row ≤
  2000-01-04 and last row ≥ 2024-12-31) after rule 2: **417 names** (419 − 2 duplicates). Every fit below runs on A.
- **Set B — shorter series:** flag-free, not full-history, ≥ 1,000 trading days inside the window: **158 names**. The plan
  says "a random sample of the shorter ones"; since the set is small enough to use whole, no sample size is chosen —
  B is all 158. Used for the E3.1 sensitivity (A ∪ B) and the survivorship description; not for VR(500).
- **EDGAR sub-set:** A ∩ names with an EDGAR file (417 of 417 by file count; the usable count after §4.2's dedup is
  reported). GICS sector from `wikipedia_current_20250611.csv` (335 of A have one; the rest use the market median, §4.2).
- Delisted coverage inside A: the 12 full-history names that left the index are in A iff flag-free (count reported).
  A contains no bankruptcies — the survivor caveat of REG-15 applies to every tail statistic and is printed beside it.
- Sub-periods (plan E1.2): 2000–07, 2008–12, 2013–19, 2020–24.

**Hybrid (D1 = C):** `PanelSpec(root="datasets", price_dir="01_prices/daily", fundamentals_dir="03_fundamentals/by_ticker",
price_col="Adj Close", …)` — a CRSP/Compustat re-run replaces the spec, not the code. Recorded in every output JSON.

## 2. Seeds, panels, bootstrap counts (fixed; all fresh, none in Phase 0's 9001–20000 or the reviewers' 0–49/777/778)

| Block | Purpose | Seeds | Horizon |
|---|---|---|---|
| **SEP** — standard evaluation panel (every before/after audit row) | `audit_panel` composition (the published audit's): per seed setup-first flat, bull_trap, sustained_bull, crash δ 0.55/0.70/0.85 (seed s) and event-first bull_trap and crash δ 0.70 (seed 1000 + s) | 30000–30199 (event-first 31000–31199); 200 seeds → 1,600 paths, 320,000 rows | 200 |
| **SCL** — standard checklist panel | `checklist_paths` composition at 200 seeds with a seed offset (new argument `seed0`, default 0): flat/bull/SB/crash×3 at 40000–40199, mixed set at 41000+/42000+/43000+, flat T = 800 at 40000–40019 | as stated | 200 / 800 |
| **S11** — E1.1 attacker test | 4 scenarios (flat, bull_trap, crash δ 0.70, sustained_bull) × mechanisms {fixed (v2), A, B, C} | 50000–50499 (500 per scenario) | 200 |
| **S13** — E1.3 sweep | 4 scenarios × 40 grid points; item 9 on flat T = 800 | 60000–60199 (200); T = 800 at 60000–60049 (50); μ_V nuisance 60000–60049 (50) | 200 / 800 |
| **S14** — E1.4 generator side | flat, per jump variant | 70000–70199 (200) | 200 |
| **S15** — E1.5 burn-in | flat, per engine and burn-in option; reference T = 5,000 | 80000–80499 (500) | see §6 |
| **S12R** — E1.2 recovery study | synthetic panels from the vectorised calm simulator | `default_rng(90000 + cell × 1000 + replication)` | 6,300 d × 100 stocks |
| **L5** | observables oracle: training / evaluation seeds | 500–539 (40) / 0–49 (50) — a superset of the published 500–511 / 0–9 | 200 |
| **Start-price range** | 40 random panel dates | `default_rng(20260829)` | — |
| Bootstrap | percentile bootstrap, `default_rng(0)`, 95 % | **500** resamples for every surrogate/attacker statistic (cluster over paths), **1,000** for closed-form statistics (VR fits, KS distances, means, medians, GARCH medians over stocks), **200** for classifier accuracies | — |

These are the counts that **will** be run (Phase 0's lesson). Compute basis, measured 29 Aug on this machine: generator
≈ 30 ms per 460-day path incl. observables; `panel_from_env` ≈ 1 ms/row; GBT 5-fold ≈ 19 s per 58k rows × 111
features (≈ 2 min at 320k rows); MLP ≈ 52 s per 58k rows (≈ 5 min at 320k); `arch` GJR-t fit ≈ 0.07 s. So: E1.6 at 200
seeds without `MAX_ROWS` ≈ 1 h per audit run; E1.1 ≈ 15 min per mechanism; E1.3 ≈ 1 min per grid point; E3.1 ≈ 5 min.

Surrogate (where used): `HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6, random_state=0)`,
`GroupKFold(5)` by path (the audit's `gbt`); E1.6's L2 also runs the audit's `ridge` and `mlp`. Lags 5; returns 1/5/20 d.

Feature sets (Phase 0's definitions, `tools/verify_v2_findings.py::_feature_sets`): **level** = the audit's
`PRICE_ONLY_KEYS` (price, SMA20, SMA50, trend_strength, trend_regime, RSI14, MACD, MACD_signal) + lags + returns (51);
**level-free** = ret_1, ret_5, ret_20, log(P/SMA20), log(P/SMA50), RSI14, MACD/P, MACD_signal/P, trend_strength,
trend_regime, each with 5 lags (45, no level); **full** = all 18 rendered numeric fields + lags + returns (111).

## 3. E3.1 — per-stock GJR-GARCH-t fits (run first; Phase 3 confirms and documents)

- Model: `arch_model(100·r, mean="Constant", vol="GARCH", p=1, o=1, q=1, dist="t")`, per stock, on set A (and A ∪ B as
  the sensitivity), full sample 2000–2024 and the four sub-periods (a sub-period fit needs ≥ 500 returns; convergence
  flag stored). Standardised residuals z_t = (r_t − μ̂)/σ̂_t stored (`generated/v2_1/e3_1/residuals.parquet`, float32) for
  E1.4 and Phase 3.
- Reported: cross-sectional median and IQR of α, γ, β, ν, persistence α + γ/2 + β, unconditional daily sd, with a
  1,000-resample bootstrap over stocks on each median; non-converged share; per sub-period. The literature values the
  plan lists (Engle 2001 α 0.077 / β 0.905 on a portfolio; the plan's sanity range persistence 0.95–0.99, ν 4–8 — read by
  the third pass) are printed beside them, not used. Survivor caveat printed (set A has no delistings by construction).
- Nothing is adopted into the generator here (Phase 3's E3.1 adopts the median); the fits are inputs to E1.4 and E2.3.

## 4. E1.2 — the value–mispricing decomposition (three estimators + REG-5's recovery study)

Model: log P_t = log V_t + x_t; log V a random walk with drift and daily variance σ_V²; x an AR(1) with coefficient
ρ = 2^{−1/h} and stationary sd s_x. The three estimators, exactly as they will be run:

### 4.1 Estimator A — variance ratios (Lo & MacKinlay 1988, overlapping estimator with the small-sample correction)
- Moments: Var(r_1) (daily variance) and VR(k) = Var(r_k)/(k Var(r_1)) for k ∈ {5, 10, 20, 60, 120, 250, 500}, per stock;
  pooled curve = cross-sectional **mean** over set A. Var(r_1) is included because VR ratios alone identify only s_x/σ_V
  and ρ (not the scale). Model curve: Var(r_1) = σ_V² + 2 s_x²(1 − ρ); VR(k) = [k σ_V² + 2 s_x²(1 − ρ^k)] / [k Var(r_1)].
- Fit: minimum distance in (log σ_V, log s_x, log h) with weights 1/Var_boot of each pooled moment (Nelder–Mead from a 3 × 3 × 4
  log grid, best of the starts). Intervals: (i) primary — cluster bootstrap over stocks (1,000); (ii) secondary — joint
  stock × moving-block (250-day) bootstrap over time (500) reported beside, because VR(500) straddles blocks (LOG §7:
  ≈ 8 non-overlapping 750-day windows per stock; the CI is expected to be wide — reported, not assumed).
- Per sub-period fits with the same procedure (k ≤ 250 for the 5-year sub-periods, stated).

### 4.2 Estimator B — log(P/V̂) AR(1) with Andrews' (1993) median-unbiased correction
- V̂ from EDGAR: quarterly EPS (`EarningsPerShareBasic`; `EarningsPerShareDiluted` as a sensitivity), **deduplicated on
  (concept, start, end) keeping the earliest `filed`** (the brief's rule: 10-K, 10-K/A and later comparatives repeat a
  fact); quarterly rows are those with 80 ≤ end − start ≤ 100 days; Q4 = FY − (Q1 + Q2 + Q3) where the three quarters
  and the FY row exist (EPS is not exactly additive across share-count changes; flagged and reported). Trailing-4Q EPS
  known as of the filing date. Monthly (month-end) log P/E of the stock from `Adj Close` × trailing EPS; V̂ = EPS_ttm ×
  k_med where k_med = the **sector-median** trailing P/E that month over the names in set A with that GICS sector (sector
  known for 335 of A; a sector needs ≥ 5 names that month) and the **market median** otherwise; log(P/V̂) = log P/E −
  log k_med. Months with EPS_ttm ≤ 0 are undefined and dropped (share reported). Sample: 2009-06 → 2024-12; a stock needs
  ≥ 60 valid months. Both the sector-median and the market-median versions are reported.
- Per stock: OLS AR(1) with intercept → ρ̂; Andrews' exactly median-unbiased ρ from the simulated median function
  m_T(ρ) of the OLS estimator (Gaussian AR(1), 20,000 replications per (T, ρ) on a ρ grid 0.50–0.995, T = the stock's
  own length, linear interpolation, inverted); h_B = −ln 2 / ln ρ_MU (monthly → days × 21). s_x = the per-stock sd of
  log(P/V̂); σ_V from the variance of Δlog V̂ (monthly, /21 for daily) — **overstated** by the measurement noise in V̂
  (stated). Reported: cross-sectional median and IQR of h, s_x, σ_V; bootstrap over stocks (1,000).

### 4.3 Estimator C — simulation-based (the light form of E2.3; Phase 2 owns the full SMM)
- Simulator: `tools/phase1/calm_sim.py`, a vectorised (over paths) re-implementation of the calm generator: the FW
  recursion of `mispricing.py` (`fw_fallback` form with φ set by the pull-rate half-life h at the pilot n̄), the GJR-GARCH-t
  of `garch.py` (α 0.10, γ 0.10, β 0.83, ν 5, `sbar` free), V a random walk with t(5) shocks and σ_V free, no events,
  jumps as adopted in E1.4. **Equivalence check, pre-registered:** on 100 paths × 5,000 days the simulator's sd(x),
  ACF(1) of x and return kurtosis must lie inside the 95 % bootstrap interval of the same statistics from `envs.v2`
  (100 flat paths, T = 5,000, jumps off); otherwise C is reported as not run.
- Moments (9): Var(r_1); VR(20, 60, 120, 250, 500); ACF of log(P/SMA250) at lags 20, 60, 120. Targets pooled over set A;
  weight matrix **diagonal** 1/Var_boot (the full block-bootstrap W is E2.3's). Simulated moments: 20 paths × 5,000 days,
  common random numbers. Parameters (σ_V, sbar → s_x, h); Nelder–Mead from 4 starts; J reported. Interval: bootstrap of
  the data moments (200 resamples over stocks, refit each).

### 4.4 The recovery study (REG-5, decides which estimators are usable)
- Synthetic panels: 100 stocks × 6,300 days from `calm_sim` with known h ∈ {30, 60, 120, 150, 250, 500} d × σ_V ∈
  {0.006, 0.012}, sbar 0.017 (s_x ≈ 0.175, the engine's value, PHASE_0_REPORT §3.4); V̂ = V × exp(m) sampled quarterly with
  m an AR(1) measurement error whose sd is FIT as the cross-sectional median of the per-stock sd of log(EPS_ttm,q /
  EPS_ttm,q−4) on the EDGAR sub-set and whose persistence is bracketed {0 (white), 0.9 per quarter (persistent)} — the
  bracket is DESIGN (no free data identify it) and both are reported.
- Replications per cell: **200 for A and B, 50 for C** (C costs ≈ 5 s per fit; 12 cells × 50 = 50 min; 200 would be
  3.3 h — the reduced count gives C's RMSE to ± 10 % instead of ± 5 %, stated).
- Usability rule (REG-5): an estimator is usable at a given h if its median recovery error |ĥ − h|/h < 0.20 **and** its
  95 % interval covers the truth in ≥ 90 % of replications (A, B: the stock-cluster bootstrap interval per replication,
  200 resamples; C: coverage is not measured in the study — its usability rests on the error criterion alone, stated).
- Usability is evaluated at the h nearest to each estimator's own data point estimate (interpolating between grid
  points is not done; the nearest grid cell is used).

### 4.5 Decision rules (fixed)
- **h and s_x (REG-5):** among the usable estimators, adopt the one with the smallest RMSE (at the nearest cell) whose
  data 95 % interval contains the other usable estimators' point estimates; if the usable estimators' intervals are
  disjoint, adopt none — report all three and hand the union of the intervals to Phase 2's persistence sweep (E2.6).
  What Phase 1 "adopts" for h and s_x is a **FIT target recorded in `params/value.json`** with its interval; the engine's
  φ and sbar that put it in force are Phase 2's (`params/mispricing.json`, E2.2/E2.6, `test_persistence_in_force`).
- **σ_V (plan E1.2 / REG-2):** if the σ_V 95 % intervals of the usable estimators overlap, adopt the pooled FIT (inverse-
  variance-weighted mean of the usable estimators' point estimates, interval from the union) into the generator
  (`params/value.json`, `GenConfig.sigma_V`, `test_sigma_V_in_force`); if they do not overlap, adopt neither — report both
  with the E1.3 consequence tables and refer to the team (D3).
- If only one estimator is usable, it is adopted alone (its own interval); if none is usable, D3 with all three reported.
- **μ_V (plan 5.3):** FIT = the mean monthly log change of Shiller's nominal S&P price (`shiller_monthly.csv`, column `P`,
  1871.01 → 2024.12 and 2000.01 → 2024.12 both reported) converted to per-trading-day (/21); adopted value = the 2000–2024
  window (the panel's window; the long-run value beside it); insensitivity shown in E1.3's μ_V nuisance sweep {0,
  0.00025, 0.0005}/day. DMS 9.7 % nominal US 1900–2024 (read by the third pass) is quoted beside, not used.
- **df_V (plan 5.3):** standardised quarterly EPS changes on the EDGAR sub-set: d_q = (EPS_q − EPS_q−4) / s_i with s_i the
  stock's own sd of the seasonal change; pooled z. Two-sample bootstrap KS distance (1,000) between the pooled z and (i)
  N(0, 1), (ii) t(5)/√(5/3): FIT Gaussian if only (i)'s upper limit < 0.10, FIT t5 if only (ii)'s, else **DESIGN** with
  both variants carried in the checklist (E1.3 runs both anyway). Pooled excess kurtosis reported with its interval.

## 5. E1.4 — where jumps belong

### 5.1 Panel side
- Residuals: E3.1's z_t on set A, 2009-01 → 2024-12 (EDGAR coverage; stated).
- Announcement window (no 8-K Item 2.02 dates exist in the panel; E1.0 §3): the **10 trading days ending on a 10-Q or
  10-K filing date inclusive** (unique `filed` dates per stock, forms 10-Q and 10-K only; the release precedes the filing
  by 0–14 calendar days, plan §3). "Other days" = all remaining days. Window share of days reported (≈ 16 % expected:
  4 × 10 / 252).
- Statistics, each with a 1,000-resample bootstrap over stocks: share of |z| > 4 days that fall inside windows (q);
  the enrichment ratio q / (window share of days); the |z| > 4 rate inside and outside windows; excess kurtosis of z
  inside vs outside; the size (mean, sd, negative share) of r on |z| > 4 days inside vs outside.
- Literature beside: ABD 2007 (14.4 % jump share of index-futures variance; 27.9 % of days with a significant jump —
  index level, read by the third pass); Boudoukh et al. 2019 (49.6 % of overnight idiosyncratic volatility explained by
  identified news; firm level, read). Neither is a tolerance.

### 5.2 Generator variants (`GenConfig.jump_placement`), all with total expected jump count held at v2's CAL rate
0.010/day and size sd 0.03 (CAL; Phase 3 re-fits both), so that only the **placement** differs:
- **current** (dominated; recorded): x jumps, rate 0.010, N(−0.04, 0.03).
- **B — `x_zero`:** x jumps, rate 0.010, N(0, 0.03).
- **A — `V_announce`:** at each EPS announcement day a jump J ~ N(0, 0.03) in log V with probability p_ann = q · 0.010 · 63
  (q from §5.1, so that the expected announcement-jump count equals the panel's window share of jump days), plus a
  residual Poisson component in log V at rate λ_res = (1 − q) · 0.010 with N(0, 0.03) sizes. The announced EPS_q of that
  quarter is computed from V after the jump (the EPS field carries the jump, as in reality — Phase 5 audits that channel).
- **C — `both`:** the announcement component of A in V, the residual component in **x** (mean zero).
- Implementation detail declared: announcement days move into the generator (new RNG component `announce`, appended to
  `rng.COMPONENTS`) so that the jump and the EPS field share them; `earnings_block` takes the days and the jump sizes as
  arguments. The `eps` stream's draw order therefore changes (EPS noise values differ from v2 at the same seed) — every
  path changes in Phase 1 anyway (§9).

### 5.3 Generator side and the rule
- 200 flat paths (S14) per variant at the adopted σ_V (or v2's 0.006 if D3 is pending — stated in the report): GJR-t
  residuals by the same `arch` fit per path; window = the 10 trading days ending on each announcement day inclusive.
- Statistics: the two-sample KS distance between the panel's and the generator's residual distributions, separately for
  window days and other days, each with a 1,000-resample bootstrap over stocks (panel) and paths (generator) → 95 % upper
  limit; the kurtosis split; q under each variant.
- **Rule (REG-3):** adopt the variant with both upper limits < 0.10; if more than one, the one with the smaller window-day
  distance; **if none passes, report all distances and kurtosis shares and carry C (the most flexible) forward with the
  shortfall stated.** In every case the adopted variant must satisfy the **E[x] equivalence rule**: on 200 flat paths the
  95 % cluster-bootstrap interval of the mean of x (mean over paths of the path mean) lies inside [−0.02, +0.02] (the
  plan's DESIGN margin, below the smallest θ candidate 0.03); a variant that fails it is out regardless of the KS rule.
- Consequence reported, not gated: the flat-path share with excess kurtosis > 1.5 under each variant (checklist item 2 is
  re-scored in Phase 3 after E3.2's size re-fit).
- Power (register): KS sd ≈ 0.02 at these sizes → equivalence at 0.10 has ≈ 0.8 power against a true 0.05; the E[x] SE at
  200 seeds ≈ 0.009 (the −0.087 bias is rejected with power ≈ 1).

## 6. E1.5 — burn-in (REG-17)

- State variables: (x, GARCH conditional variance σ², n_f) on day 1. Reference distribution: the same three variables on
  benchmark day 5,000 of 500 flat paths (S15, T = 5,000, burn-in 260, jumps as adopted) per engine.
- Engines (the sensitivity set): `fw_fallback_hl150` (default), `fw_hl60`, `fw_index`, `pruna`, `ar1`. Slowest state
  variable per engine = x; pull-rate / pilot half-lives 150 / 60 / 628 / 622 / 150 d (PHASE_0 block R19) → "5 half-lives"
  = 750 / 300 / 3,140 / 3,110 / 750 days.
- Options: **(i) current** burn-in 260 d; **(ii) A — long burn-in** ≥ 5 half-lives (the values above, rounded up to the
  next 10 days); **(iii) B — stored state:** the day-1 state drawn per seed from a stored 500-draw sample of the reference
  distribution (`envs/v2/params/burn_in_states_<engine>.npz`, hashed in the freeze), followed by a 60-day burn-in so that
  the trailing windows (SMA50, EPS quarters, volume) are warm (60 d is the longest rendered window; stated).
- Statistic: per engine, per variable, the two-sample KS distance between the 500 day-1 values and the 500 reference
  values; 1,000-resample bootstrap (paths) → 95 % upper limit. **Rule:** an option passes for an engine if every
  variable's upper limit is < 0.10. Adopt, per REG-17: if both A and B pass, A for the default engine (no artefact) and B
  for the slow sensitivities (`fw_index`, `pruna`); if only one passes, that one; if neither passes for some engine, report
  the distances and keep the current burn-in for it with the shortfall stated. Power: at 500 vs 500 the KS sd ≈ 0.03;
  equivalence at 0.10 has ≈ 0.8 power against a true 0.05 (the plain-KS critical value 0.086 is not the criterion).
- The GARCH variance and n_f are reported per engine even where x decides. The adopted burn-in is written to
  `params/value.json` and `GenConfig.burn_in`; `test_burn_in_stationary` re-runs the statistic at 500 seeds.

## 7. E1.1 — the start-price answer key (REG-1; D13 provisional B)

- Switch `GenConfig.start_price_mode` ∈ {`fixed` (v2: V_1 = P_1 = 100), `randomise` (A: V_1 ~ LogU(P_lo, P_hi) from the new
  RNG component `start_price`, P_1 = V_1 e^{x_1}), `normalise` (B: P_1 ≡ 100, V_1 = 100 e^{−x_1}), `both` (C: B for the
  hidden path plus k_render ~ LogU(P_lo/100, P_hi/100) applied at render time to price, SMA20, SMA50, MACD, MACD_signal
  and analyst_fair_value; P/E, yield, volume, RSI, trend fields are ratios or shares and are unchanged)}. Default = B (D13).
  REG-1's definition of C (rendered day-1 price = 100 k_render) is implemented; the plan's E1.1 sentence "rendered price =
  100 on day 1 and a random scale" is read as REG-1 states it (a rendered scale cannot also leave day 1 at 100).
- (P_lo, P_hi) **FIT** = the P5 and P95 of unadjusted `Close` over set A on 40 random trading dates in the window
  (`default_rng(20260829)`), pooled (≈ 16,700 observations); bootstrap over dates (1,000) for the interval; written to
  `params/value.json` with the date list.
- **Attacker test** (S11, 500 seeds × 4 scenarios per mechanism; the `fixed` mechanism is the frozen v2 generator): the
  GBT with the level (51), level-free (45) and full (111) sets, fit on the pooled 4-scenario panel with GroupKFold(5) by
  path, evaluated per scenario on all days and on calm days. Statistic: Δ = R²_level − R²_level-free per scenario;
  500-resample cluster bootstrap over paths → 95 % CI. **Rule:** a mechanism passes if the CI's lower limit ≤ 0 in every
  scenario (the level attacker is not detectably better than the level-free one). Power: half-width ≈ 0.02 at 500 seeds
  (REG-1's estimate from the audits' path-level variance; the achieved half-width is reported), so a residual level leak
  of 0.05 is detected with > 0.8 power.
- **Rule-100 test** (ISFJ, θ 0.05, PortfolioV2 at 5 bp, 500 seeds per scenario): MCR of "cash → band-high if log(P_rendered/
  100) > 0.05, band-low if < −0.05, else unchanged" beside the mandate-conditional oracle, always-hold, constant-mix and
  the two constant band-edge policies, with 500-resample bootstrap intervals. **Rule:** the rule's point MCR lies inside
  the union of the 95 % intervals of the two constant-edge policies in every scenario (it is no better than a constant
  policy). Under `fixed` the Phase-0 finding (rule ≈ oracle in three scenarios) is expected to reproduce.
- **Reported without a gate:** the Kalman bound (identical under A/B/C); the L1 candidates k·analyst and EPS × k (median
  APE, p5/p10/p25) under each mechanism — the field channel that still reveals V_1 (Phase 5's).
- D13: B is set as the default for Phases 1–6 by the team's decision; A and C stay behind the switch for REG-1's LLM
  test in Phase 9. If B fails the attacker rule, that is reported as a failure and the team is asked (B cannot be
  replaced by preference).

## 8. E1.3 — the σ_V × s_x sweep with the analytic bound

- Grid: σ_V ∈ {0.004, 0.006, 0.010, 0.015, 0.020}/day × df_V ∈ {Gaussian (`df_V = None`, new), t5} × s_x ∈ {0.10, 0.13,
  0.165, 0.20} = 40 points, at the current mispricing engine (`fw_fallback_hl150`), with jumps and burn-in as adopted in
  §5–6 and the start price under B; s_x is set through the GARCH scale sbar = 0.017 × s_x / 0.1752 (the engine's stationary
  sd(x) is linear in sd_e: PHASE_0_REPORT §3.4, confirmed to three decimals); the realised sd(x) at T = 5,000 is
  reported at each s_x so the mapping is checked, not assumed. 200 seeds × 4 scenarios (S13) per point.
- Statistics per point: (i) level-free price-only GBT R²(x) on calm days and on all days, with 500-resample cluster CI;
  (ii) the analytic Kalman bound (Appendix B; `tools/phase1/kalman_bound.py`: state (x_t, x_{t−1}), observation r_t = x_t
  − x_{t−1} + σ_V z_t, steady-state and finite-window from the stationary prior — averaged over a 200-day window, at day
  200, and at steady state) at the grid's (σ_V, s_x, h = 150); **verification before use:** the tool must reproduce LOG
  §3's table (0.137 / 0.235 / 0.396 at σ_V 0.006, s_x 0.13) to three decimals; (iii) L4 coverage at θ ∈ {0.03, 0.05, 0.08}
  per scenario; (iv) checklist items 9 (on 50 flat T = 800 paths) and 20; (v) MAPE of V from a long price average, V̂_t =
  exp(mean of log P over the trailing 250 days), over benchmark days, with its CI.
- μ_V nuisance: {0, 0.00025, 0.0005}/day at the adopted (σ_V, s_x), 50 seeds (S13), same statistics.
- No value is adopted from this sweep (the adopted σ_V is E1.2's); the sweep makes the consequences visible. The
  surrogate must lie at or below the bound within its CI "plus the nonlinear allowance measured on a Gaussian control
  run" (Appendix B): the allowance = the surrogate-minus-bound gap on the Gaussian df_V row at the same (σ_V, s_x),
  reported per point; a t5 surrogate above bound + allowance + CI is flagged as a leak through a non-price channel.

## 9. E1.6 — the level-free leakage audits (no gate; the v2 gates reported for the record)

- `evaluation/leakage_audit.py` gains a **level-free control** (`control="level_free"`, the default from Phase 1): keys
  ret_1/5/20, log(P/SMA20), log(P/SMA50), RSI14, MACD/P, MACD_signal/P, trend_strength, trend_regime (derived columns;
  for v1 panels the SMA60/SMA200 ratios). The former control stays available as `control="level"` for the record.
  `MAX_ROWS` subsampling is switched off for the published run (`max_rows=None`). L1 gains the APE percentiles
  (p5/p10/p25/p50) and the share within 1/2/5 % per candidate; L2 rows carry 500-resample cluster-bootstrap intervals over
  paths on R², sign accuracy and MAPE(V); the Kalman bound at the adopted parameters is printed beside every price-only R².
- Runs (all on SEP): **after** = the Phase-1 state with the level-free control (the published audit) and with the level
  control (for the record); **before** = the frozen v2 generator (paths generated before any code change and stored)
  with both controls. Same seeds, same rows, same estimators — like for like.
- L5 (`tools/l5_report.py`): 40 training / 50 evaluation seeds, three personas, full vs level-free price-only variants,
  before and after. Scenario discrimination as in the audit. Checklist (SCL) before and after at 200 seeds.
- Outputs restate items 3, 5, 43 with intervals; the pre-registered v2 gates (L1 A6 rule, L2 absolute, L2b 10 pp) are
  printed as pass/fail for the record — no gate is applied (Phase 6 derives the gates); the registered strict xfails
  for the L2 and L1 CI tests are **not** touched (they belong to Phase 6).

## 10. Parameter file, tests, freeze

- `envs/v2/params/value.json`: sigma_V (FIT or D3-pending with v2's 0.006 kept and labelled), mu_V (FIT), df_V (FIT or
  DESIGN), s_x_fit and h_fit (FIT targets for Phase 2, with intervals and estimator), start_price_mode (DESIGN, D13),
  start_price_range (FIT, with dates), jump_placement and its (p_ann, λ_res, size sd, total rate) with labels, burn_in
  (per engine), each with {label, source, date, interval, n, survivor_vs_literature_gap}. `GenConfig` defaults read the
  file through a loud loader (as `hazard.json`); a missing or disagreeing file raises.
- Tests (`tests/test_v2_1_phase_1.py`): `test_sigma_V_in_force`, `test_value_params_loader_is_loud`,
  `test_start_price_carries_no_information` (asserts the stored 500-seed E1.1 result for the mechanism in force **and**
  re-runs the attacker at 100 seeds × 4 scenarios live, CI lower limit ≤ 0 in every scenario — the live half-width is
  ≈ 0.05, so it is a guard, not the evidence; stated in the docstring), `test_burn_in_stationary` (500 seeds per engine,
  KS upper limit < 0.10), `test_kalman_bound_tabulated` (regenerated from `value.json`, equals the stored table),
  `test_level_free_price_only_keys` (no level in the control set), `test_render_scale_invariance` (under C every ratio
  field and every return is invariant to k_render), `test_jump_placement_variants` (each variant produces the declared
  jump count and E[jump] = 0 where declared), `test_flat_x_unbiased` flipped to **hard** and `test_flat_x_equivalence`
  (95 % CI of mean x inside ± 0.02 at 100 seeds) added; registry entry for defects 4/13 removed.
- Suite consequences declared: `test_v2_generator::test_price_decomposition_and_start` asserts V_1 = 100 → becomes P_1 =
  100 under B; `test_docs_numbers` reads jump_mean/burn_in from `phase0_numbers.json` → the Phase-1 numbers file
  (`phase1_numbers.json`) takes over for the values Phase 1 changed; `rendered_prompt_v2_*.txt` and `table2_v2_from_code.*`
  are regenerated (the rendered sample changes because every path changes).
- Freeze: `python -m tools.freeze_manifest --write --label "Phase 1 freeze"` at the end (logged as a decision); the
  Phase-0 path-hash fixture is left as is (it records Phase 0); a Phase-1 fixture `path_hashes_phase1_{before,after}.json`
  documents that **every** hidden and rendered column changes (declared consequence of B, the jump placement, the
  burn-in and the `eps` stream reorder), and `tools/path_hashes.compare` is not asserted on it.
- Execution-order rule: the checklist (SCL), the audits (SEP), L5 and Table 2 are re-run on the handed-over state.

## 11. Order of execution

E3.1 → E1.2 (A, B, C, recovery) → E1.4 → E1.5 → write `value.json` → E1.1 → E1.3 → E1.6 (after) → tests, freeze, docs.
The **before** panels (SEP, SCL, S11 `fixed`, L5-before, S15 current burn-in) are generated from the frozen code before
any code change and stored in the scratchpad; their statistics are computed with the same tools as the after panels.

## 12. What is reported if a rule is not met

- E1.2: estimators disagree → all three with intervals, the recovery table, the union interval to Phase 2, and D3 with
  E1.3's consequence tables (REG-2). No estimator usable → the same, with the usability table.
- E1.4: no variant passes the KS rule → C carried forward with the shortfall; the adopted variant fails the E[x] rule →
  none is adopted, the team is asked with the table (this cannot be met by re-tuning here).
- E1.5: neither option passes for an engine → the current burn-in kept for that engine with the KS table published.
- E1.1: B fails the attacker or rule-100 test → reported as a failure; the team is asked (D13); A/C results beside.
- E1.3, E1.6: descriptive; failures of the v2 gates are printed as failures.
- Any test predicted to pass that fails is reported with its output; no tolerance is moved; no test is deleted.

## 13. Not done in Phase 1 (owner)

The full SMM with the block-bootstrap weight matrix and the engine decision (Phase 2, E2.3–E2.4); the jump size and
rate re-fit and Lee–Mykland detection (Phase 3, E3.2); the IV construction (Phase 3); the field redesign and the
analyst/EPS channel (Phase 5); the gate derivation (Phase 6); REG-1's LLM test (Phase 9); the 200,000-step
re-normalisation of w̄/n̄ (Phase 2, P0-8). WRDS re-fit: when access arrives, `PanelSpec` is pointed at the new files and
E3.1/E1.2/E1.4 re-run unchanged (D1 = C).
