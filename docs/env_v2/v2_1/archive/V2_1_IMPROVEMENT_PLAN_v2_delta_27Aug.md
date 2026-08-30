# FinPersona-Bench synthetic environment: improvement plan v2 → v2.1 — corrected plan (v2 of the plan)

Status: **corrected draft for review, 26 August 2026 (third, independent pass); reviewer edits applied 27 August 2026 (marked [edit 27 Aug]).** No code was changed, no paid API was called, nothing was committed. This document keeps the structure and numbering of `V2_1_IMPROVEMENT_PLAN.md`; every change is marked **[changed: reason]** so the diff is auditable. The evidence for each change is in `reviews/V2_1_PLAN_VERIFICATION_LOG.md` (cited as LOG §n); the alternatives for every unsettled choice are in `V2_1_ALTERNATIVES_REGISTER.md` (cited as REG-n). Points of the plan review (`reviews/review_of_V2_1_IMPROVEMENT_PLAN.md`, cited as REV-n) are adopted where marked; where this pass disagrees with the review it says so with the evidence (Section 17 and LOG §10).

Scope, conventions and provenance labels (LIT / FIT / CAL / DESIGN) are unchanged from the original. **[changed: one addition — a fifth label, ESTIMATE, for the analyst-effort numbers in Section 15, which no source or experiment can supply and which are this pass's judgement; nothing else may carry it.]**

Note on file locations **[edit 27 Aug: `docs/env_v2/` was restructured on 27 Aug 2026]**: the v2 specification is in `docs/env_v2/spec/`, pre-registration in `preregistration/`, decisions in `decisions/`, the v1 baseline in `v1_baseline/`, status notes in `status/`, results in `generated/`; the three v2 reviews and `V2_WEAKNESSES.md` are in `docs/env_v2/reviews/`; this plan, the alternatives register and the prompts are in `docs/env_v2/v2_1/`, with the plan review, the verification log and the closing note in `docs/env_v2/v2_1/reviews/`. Phase pre-registrations and reports go to `docs/env_v2/v2_1/`, their outputs to `generated/v2_1/`. **[changed: the FW 2012 PDF URL is corrected in 0.2 and 6.1 — the plan's URL returns 404; LOG §5.]**

**Reviewer edits of 27 Aug 2026** (from `reviews/review_of_pass3_verification.md`, each marked [edit 27 Aug] where it applies): (1) the stationary sd(x) ≈ 0.165 of the third pass is not reproduced (two independent 200,000-step pilots give 0.131 and 0.140; the calibration report's pilot gives 0.142) and is held pending the script that produced it; (2) Claude Sonnet 5 and Opus 5 use a tokenizer that produces about 30 % more tokens for the same text (provider pricing page, 27 Aug 2026), so their cost lines carry a 1.3× factor; Haiku 4.5, Gemini and GPT-5 mini are unaffected; (3) go/no-go G3 may not be passed by shortening the persistence below its fitted value; (4) Phases 1–6 run under the provisional start-price mechanism B (normalise the price), chosen by exclusion, until REG-1's LLM test in Phase 9 — the team is asked to approve that explicitly (D13); (5) the `.gitignore` line that hid `docs/env_v2/reviews/` from `git status` is superseded by the restructure (reviews/, v2_1/ and slides/ are deliberately local).

---

## 0. What was verified before writing this plan

Everything in this section was recomputed on 26 August 2026 from the working tree at commit `b61fe07`. **[changed: a third-pass column with fresh seeds (7000+, 8000+) is added to every row; LOG §1.]**

### 0.1 Review findings reproduced

| Item | Finding | Plan's value (n) | Third-pass value (n, new seeds) | Reviewer's value |
|---|---|---|---|---|
| 4 | Flat "control" biased cheap by jumps | mean x −0.100, median −0.068, P(x<0) 0.70, day-1 −0.076 (30 × 200 d); jumps off −0.018, 0.50 | mean x −0.077 (SE 0.019, 50 seeds), median −0.074, P(x<0) 0.71, day-1 −0.087; jumps off +0.009 / 0.46 (30 seeds); analytic stationary mean −0.087 | −0.100 / −0.068 / 0.70 (C.4) |
| 2, 11 | FW switching inert at `price_scale = 100` | n_f > 0.99 on 0.981 of days; index set at scale 1: n̄ = 0.827 | 0.975 (30 seeds); n̄ = 0.9985 (scale 100) / 0.8268 (scale 1) | 0.983–0.991 (C.1); **[changed: the published comparison is SABCEMM's DCA-HPM average chartist share 0.23 (kurtosis 7.8); the "≈ 0.17 / ≈ 10" pair is the DCA-WHP row; FW 2012 states no share; LOG §4.2]** |
| 68 | Analyst error implemented at sd ≈ 0.34, documented 0.15 | sd(u) 0.350, median \|u\| 0.262 (30 × 460 d) | 0.306 (full 460 d incl. warm-up) / 0.330 (benchmark days); median \|u\| 0.222; analytic 0.15√5 = 0.335 | 0.335–0.338 (B.6, C.24) |
| 46 | IV is a one-day phase step | +0.594 (×1.81); calm sd 0.084; z 7.1 | +0.606 (×1.83); −0.619 at panic→stabilisation; sd 0.086; z 7.06 (30 seeds) | +0.62, z ≈ 7 (C.6) |
| 18, 42 | Sustained-bull rejection selects the quiet sub-population | 17/13 accepted/rejected; sd 0.0150 vs 0.0242; rate 0.38 | 32/18 of 50; 0.0153 vs 0.0210; 0.36; mean attempts 1.6 | 33/27, 0.0147 vs 0.0240 (C.5); 39.8 % (checklist 17) |
| 36 | Half-life is an estimator artefact | 26 d at T = 200 (30); 72 d at T = 800 (20); 55 % clear 60 d | 35 d (30); 65 d (20); 60 % | 14 d / 72 d / 54 % (B.9) |
| 1 | Fixed start price is an answer key | "compare with 100" rule: 0.014 / 0.007 / 0.005 / 0.098 vs oracle 0.003, always-hold 0.11–0.14 (12 seeds) | 0.022 / 0.011 / 0.007 / 0.083 vs oracle 0.000 (direct scoring), always-hold 0.100 | 0.014 / 0.007 / 0.005 / 0.098 (C.2) |
| 71 | Half-life numbers inconsistent | φ = 0.463; pilot ACF(1) 0.9963 → 188 d; `fw_index` ≈ 610 d | φ = 0.4632; same cached pilot → 188.5 d; **five 200,000-step pilots → 141–154 d (mean 147 d) against the pull-rate 150.0 d** (two further independent pilots on 27 Aug: 142 d and 160 d, confirmed); stationary sd(x) reported as 0.162–0.169 by the third pass, **not reproduced** [edit 27 Aug]: 0.131 and 0.140 in the two 27-Aug pilots, 0.142 in the calibration report — held pending the third pass's script | 187 d (B.14) |

Conclusion: the headline findings hold on fresh seeds. **[changed: the "150 vs 188 d" discrepancy is sampling error of the single 20,000-step pilot cached in `mispricing.py` (SE of ACF(1) ≈ 0.0007 vs a gap of 0.0010), not an engine property; at 200,000 steps the ACF(1) half-life and the pull-rate half-life agree within 2 %. This changes Phase 0's test 0.4 and Phase 2's E2.5 (LOG §1, §7).]** The FW units question is settled at source (0.2) and the "72-day realised half-life" clears its own floor on barely half the paths.

### 0.2 Units of the Franke–Westerhoff model

**[changed: read from the paper itself, LOG §4.4.]** FW 2012 (JEDC 36:1193–1211; PDF served at `https://www.uni-bamberg.de/fileadmin/uni/fakultaeten/sowi_lehrstuehle/vwl_wirtschaftspolitik/Team/Westerhoff/Publications/2011/JEDC_RF_FW_Fin.pdf`, 26 Aug 2026; the plan's URL is 404): eq. (1) "with respect to the log prices p_t … r_t := 100 (p_t − p_{t−1})"; eq. (5) "letting p_t be the (log) price … p_t = p_{t−1} + μ (n^f d^f + n^c d^c)"; eq. (6)–(7) d^f = φ (p* − p_t) + ε^f, ε^f ~ N(0, σ_f²), d^c = χ (p_t − p_{t−1}) + ε^c; the misalignment term is "the squared deviations of p_t from p*". DCA-HPM: φ 0.12, χ 1.50, α_0 −0.327, α_n 1.79, α_p 18.43, σ_f 0.758, σ_c 2.087, μ = 0.01, β = 1 (as in `mispricing.py`); joint bootstrap p-value 32.6 %. With p in natural-log units the noise contribution to a daily return is μ σ_f = 0.76 %, the right order for the S&P 500; in "log × 100" units it would be 0.0076 percentage points. The misalignment term therefore takes natural-log deviations: `price_scale = 1`. Pruna et al. (2016) say the same in words (LOG §4.2). Phase 2's E2.1 becomes a reproduction check of the *pure* FW model (their noise, their equations), not an open question.

### 0.3 State of the test suite

Unchanged in substance (the `vectorbt` import, the v1-contract bull-trap assertion at `tests/test_env_logic.py:29`, the strict xfail at `tests/test_leakage_ci.py:100` — all confirmed by reading). **[changed: LOG §8.1 — with the slow audit file included the suite gives 1 failed (`test_bull_trap_generation`), 68 passed, 3 xfailed in 24 min 19 s; the plan's "60 passed, 1 failed in 9 min 21 s" excluded that file and is consistent.]**

### 0.4 Data, compute and API facts that shape the plan

**[changed: every item re-checked on the network on 26 Aug 2026; LOG §5.]**
- No CRSP/Compustat/OptionMetrics/IBES access (WRDS is institutional-subscription only). Free substitutes checked today: `yfinance` (1.6.0 installed; 1.7.0 released today), Kenneth French library, Damodaran datasets (last update 9 Jan 2026; `pedata.xls` served), **SEC EDGAR company-facts** (quarterly `EarningsPerShareBasic` and `CommonStockDividendsPerShareDeclared` with filing dates, 2009–2026, confirmed on Apple) and Financial Statement Data Sets (2009q1–2026q2), **SF Fed Daily News Sentiment Index** (daily since 1980, xlsx, updated 24 Aug 2026), **CBOE single-stock VIX files** (VXAPL, VXAZN, VXGOG, VXGS, VXIBM daily CSVs, 2011-01-07 → 2026-08-25 — better than the plan expected), AAII (weekly since 1987, readable without login), Baker–Wurgler (monthly, ends Dec 2023), Shiller (the current file, to 2026.08, is at shillerdata.com; the Yale copy ends 2023.09). **Not usable as planned:** FRED was unreachable from this machine (the no-key CSV download is unverified); Stooq serves a JavaScript challenge to scripts; **the Wikipedia S&P 500 "Selected changes" table no longer exists on the article**, so the historical-constituent universe needs another public source, to be identified and logged before E1.0.
- Python 3.13.13; `arch 8.0.0`, `statsmodels 0.14.6`, `scikit-learn 1.9.0`, `scipy 1.18.0`, `numpy 2.4.6`, `pandas 3.0.3`; `lightgbm`, `numba`, `pandas_datareader`, `vectorbt` absent; `ta` present; 8 CPUs.
- Generator cost: 0.17 s per 200-day path including observables (measured; LOG §1).
- API keys present (names only): Anthropic, Gemini/Google, OpenAI, HF; no DeepSeek or OpenRouter key.
- Prompt sizes **measured today**: ISFJ track-B system prompt 6,041 characters (≈ 1,510 tokens at chars/4), one human message 2,234 characters (≈ 560 tokens); pilot output ≈ 120 tokens; the stateful rolling-20 arm averaged 19,500–20,000 context tokens per call (three pilot CSVs). Per 200-day run: ≈ 0.41 M input and 0.024 M output tokens (stateless), ≈ 3.9 M input (stateful).
- Prices read on the provider pages today: Gemini 2.5 Flash $0.30 / $2.50 (Flash-Lite $0.10 / $0.40); **GPT-5 mini $0.25 / $2.00 (cached input $0.025) — the plan's "$0.125 / $1.00 after July 2026 cuts" is wrong; no such cut is documented**; Claude Sonnet 5 $2 / $10 (the scheduled 1 Sept rise is cancelled), Haiku 4.5 $1 / $5, Opus 5 $5 / $25; batch 50 % at all three providers (usable only if the harness advances all runs in lock-step and batches each day's calls); Anthropic cache reads 0.1×. Per stateless run: Flash ≈ $0.18, GPT-5 mini ≈ $0.15, Haiku 4.5 ≈ $0.53. **[edit 27 Aug]** Claude 4.7 and later models (Sonnet 5, Opus 5; not Haiku 4.5) use a tokenizer that produces about 30 % more tokens for the same text (Anthropic pricing page, read 27 Aug 2026), so the chars/4 estimate is scaled by 1.3 for them: Sonnet 5 ≈ $1.4 per stateless run (≈ $0.7 with cached system prompt), Opus 5 ≈ $3.5. Per stateful run: Flash ≈ $1.24, GPT-5 mini ≈ $1.03, Sonnet 5 ≈ $10.5. OpenRouter serves Llama-3.3-70B ($0.10 / $0.32), Qwen2.5-72B ($0.36 / $0.40), Gemma-3-27B ($0.08 / $0.16) if a key is added (D2).

---

## 1. How every phase is run (the protocol)

Steps 1–6 unchanged, with these additions:

1. Literature review — **[changed: REV-4 adopted and made enforceable]** every phase report carries a citation table with one of three statuses per statistic — read-and-correct / read-and-wrong (with the correction) / not-retrievable — and the URL and date; a statistic marked "(to verify)" may not appear in a parameter file, a test tolerance or a slide. The verification log's §4 is the starting table; citations it marks WRONG are corrected in this plan where they occur.
2. Pre-registration — unchanged, plus **[changed: LOG §3, §7]** (a) every "equivalence" criterion is stated as a TOST-type bound on the *upper confidence limit* of the distance (bootstrap), never as "the test did not reject"; (b) every share-type or mean-type pass rule states both the detection power against the pre-registered alternative and the equivalence margin it accepts; (c) every rule states what happens if its condition is never met (e.g. "θ_info = ∞ → D7").
3–6. Unchanged.

Reporting rules: unchanged. Power-analysis rules: unchanged except **[changed: LOG §3]** the KS rule is restated (Appendix A) and the bootstrap is the default for median/correlation criteria.

Git: unchanged.

---

## 2. Weakness-to-phase map

Unchanged except: **[changed: LOG §2]** item 13 (where jumps belong *and* their size) closes in **Phase 3** (Phase 1 decides the placement, Phase 3 re-fits the size distribution, because removing the negative jump mean lowers the flat-path kurtosis share from 0.85 to 0.60–0.70 and re-opens checklist item 2); item 47 closes in **Phase 4** (Phase 3 only supplies the variance multiplier); item 60 is split — next-open logging in Phase 7, placebo matching in Phase 8; item 1 is closed by Phase 1 **for the price channel only** and re-tested for the field channels in Phase 5 (REV-1, last sentence).

| Phase | Items closed |
|---|---|
| 0 | 39, 44 (count), 53 (label), 54 (input), 65, 66, 68, 69, 70, 71, 72, 73 (statements), 74 (list) |
| 1 | 1 (price channel; field channels re-tested in 5), 3 (audit side), 4, 5 (restatement), 8, 9, 13 (placement only), 43, 50 |
| 2 | 2, 10, 11, 35, 36, 38, 62 |
| 3 | 12, 13 (size/rate), 14, 25, 46, 73 (GARCH fit on regime paths) |
| 4 | 6, 15, 16, 17, 18, 19, 41, 42, 47, 49, 51, 58 (shared event) |
| 5 | 3, 20, 21, 22, 23, 24, 34 (observable constants), 45 |
| 6 | 5, 7 (ledger), 30, 31, 32, 37, 40, 61, 63, 64, 67 (held-out scenario, L3) |
| 7 | 26, 27, 33, 48, 52, 53 (convention), 54 (re-specification), 56, 60 (next-open logging) |
| 8 | 28, 55, 57, 59, 60 (placebo matching), 67 (random slopes, CIs), harness constants of 34 |
| 9 | 8, 10, 12, 20, 21, 23 (LLM-grid sensitivities), 29 |
| 10 | 7, 44, 45, 63, 74 |

---

## 3. Data sources, their substitutes and their biases

Table unchanged except these corrections **[changed: LOG §5]**:
- Daily prices: the universe source must be replaced (the Wikipedia changes table is gone); Stooq cannot be scripted; a second source is still required for cross-checks (candidates to be checked and logged in E1.0: the SEC's own ticker/CIK lists for coverage, the Financial Statement Data Sets' filer universe for delisting dates).
- Index valuation: Shiller's current file is at shillerdata.com.
- Implied volatility: the five CBOE single-stock VIX histories **are** available (15 years, daily), so the single-stock IV model can be FIT on five names (with the caveat that they are mega-caps) rather than LIT-only; FRED/VIX is unverified from this machine and must be re-checked or replaced by CBOE's own VIX file.
- News sentiment: SF Fed daily index confirmed.
- Crash episodes: Barro & Ursúa is NBER w14760 (2009) / Research in Economics 2017, not w22743 (a different paper); Pagan & Sossounov's 25/15-month durations were not read from the paper and may not be quoted until they are.

**[changed: REV-6 adopted]** Survivorship: names that delisted before `yfinance`'s coverage are exactly the crashes, tails and drawdowns Phases 3, 4 and 6 need. The reference distributions for checklist items 2, 3, 8 and 20 and the crash-episode tables are therefore biased toward calmer stocks; every slide that shows them says so, and D1 (WRDS access through the institution) is a real option (REG-15 gives the hybrid and the survivorship rule). Where the bias can be quantified it is: the share of the historical constituent list that cannot be retrieved, and the difference between survivor and literature full-universe values for the tail and drawdown statistics.

---

## 4. Phase 0. Verification and freeze (no design changes)

Goal, weaknesses, literature: unchanged.

0.1 Reproduction script: unchanged (the third-pass numbers of 0.1 are a second dry run; the script reports both).

0.2 Bug fixes: unchanged except **[changed: LOG §1 item 71]** the half-life statement becomes: pull-rate half-life 150 d; long-pilot ACF(1) half-life 147 d (five × 200,000 steps, range 141–154); sample half-life at T = 200 ≈ 26–35 d and at T = 800 ≈ 62–72 d (estimator-biased); stationary sd(x) ≈ 0.13–0.14 (200,000-step Gaussian pilots; the third pass's 0.165 is not reproduced and is not quoted until it is — [edit 27 Aug]) vs 0.128 (T = 800 sample). The 188 d figure is replaced everywhere, and `pilot_stats` is re-run at 200,000 steps (a logged change of a cached constant, not a design change).

**[changed: REV-10 adopted]** 0.2b *Corrections to the current deck, immediately.* Phase 0 produces a one-page `docs/env_v2/v2_1/DECK_CORRECTIONS_NOW.md` listing the sensitivity counts (fw_index 8/7, omega 7/8, panic×3 9/6, panic×6 8/7, Pruna 7/8 — verified against the CSVs), the "nothing re-tuned" tile, the analyst sd, the pilot's scenario count and the half-life numbers, so that nobody presents the wrong figures before Phase 10.

0.3 Freeze: unchanged.

0.4 Statistical regression tests: unchanged except **[changed: LOG §1]** `test_half_life_consistency` is a **hard test from Phase 0** (it passes at 200,000 steps: 147 vs 150 d, within the 25 % tolerance), not a strict xfail; its tolerance is set from the ACF(1) sampling SE at 200,000 steps (≈ 0.0002 → ± 8 d) rather than 25 %.

0.5 Clean suite, 0.6 earlier-round requirements: unchanged.

Decision rules, tests, documentation, compute: unchanged. **What could block it**: unchanged.

---

## 5. Phase 1. Value and price structure

Goal and weaknesses: unchanged, with item 1 closed for the price channel only (Section 2).

### 5.1 Literature to consult

**[changed: every recalled number replaced by the value read at source, LOG §4.1; unverifiable ones marked]**
- Vuolteenaho (2002): firm level, annual; cash-flow-news variance 0.080 vs expected-return-news variance 0.016 for market-adjusted returns (ER-news share ≈ 0.25, s.e. 0.10), correlation 0.41; the ordering reverses for the equal-weighted portfolio. Use: an upper bound on how smooth V can be for a single stock — but note the annual frequency; the daily σ_V must be FIT (E1.2), this only bounds it.
- Cohen, Polk & Vuolteenaho (2003): 75–80 % of the cross-sectional B/M variance is profitability (≈ 55 %) plus 15-year persistence of B/M (≈ 25 %); expected returns 20–25 %. Same use.
- Campbell (1991), Campbell & Shiller (1988), Cochrane (2008; read: long-run return coefficient 1.09 vs dividend growth 0.09, CRSP VW annual): index-level decomposition goes the other way. Use unchanged.
- Poterba & Summers (1988; read: transitory sd 15–25 %, > half of monthly return variance, index, monthly), Fama & French (1988; read: ≈ 25 % for large-firm and ≈ 40 % for small-firm portfolios at 3–5 years — the plan's "25–45 %" is corrected; the post-1940 clause is unverified and not used), Summers (1986; read: α = 0.98 monthly, half-life ≈ 3 years), De Bondt & Thaler (1985; read: 24.6 % loser-minus-winner at 36 months).
- Bartram & Grinblatt (2018): **[changed: attribution corrected]** the paper reports the alpha of a convergence trade (up to 10 %/yr, decaying to zero over 34 months), not an average absolute mispricing; use: the horizon of signal decay only. Rhodes-Kropf, Robinson & Viswanathan (2005): **[changed]** reports means of the firm-specific error by group, not its dispersion or persistence; not usable for h. Lee, Myers & Swaminathan (1999) and Frankel & Lee (1998): existence confirmed, the reversion speed and the 36-month spread were not retrievable; they support the *form* (cointegration of P and V) only.
- Drift: Dimson, Marsh & Staunton 2025 — **[changed]** the 4.3 % is the world premium vs bills since 2000, not long-run; the US 1900–2024 nominal equity return is 9.7 % vs bills 3.4 %; Shiller's monthly file gives the price-only US return directly (FIT). Damodaran implied ERP 4.33 % (Jan 2025) confirmed. CLMX (2001; read: firm-level share of a typical stock's variance 0.72) says nothing about mispricing — the v2 rationale's error stands.
- Tails of fundamental shocks: unchanged (read in Phase 5's table).

Start-price randomisation: **[changed: REV-1, REV-11a]** the principle is unchanged; the mechanism is not settled — see 5.2 E1.1 and REG-1.

Burn-in: unchanged in principle; the test is an equivalence bound (5.2 E1.5).

### 5.2 Experiments

E1.0 Shared data panel: unchanged except the constituent-history source (Section 3) and: the five CBOE single-stock VIX histories and the SF Fed index are added to the panel; FRED is replaced by CBOE's VIX file if still unreachable.

E1.1 *Start-price answer key.* **[changed: REV-1 and REV-11a adopted; the plan's test replaced, LOG §2]** Three mechanisms are implemented behind one switch and pre-registered together (REG-1): (A) randomise the level — V_1 ~ LogUniform(P_lo, P_hi) with (P_lo, P_hi) FIT as the P5–P95 of large-cap closes on 40 random panel dates, P_1 = V_1 e^{x_1}; (B) normalise the price — P_1 ≡ 100, V_1 = 100 e^{−x_1}; (C) both — rendered price = 100 on day 1 *and* a random rendered scale k_render applied to all price-denominated fields (price, SMAs, analyst estimate, EPS, DPS) so that the LLM sees both a level-free day-1 anchor and a random magnitude. Under every option the day-1 price carries no information about x_1 (the Kalman bound of Appendix B is identical for A, B and C); they differ in (i) the LLM-side magnitude nuisance (a "$18 stock" vs a "$420 stock"), (ii) what a stateful reader sees on day 1, (iii) comparability with v1/v2 runs. **Test (replaces R² < 0.01, which is failed by design under A for any plausible range and met trivially under B):** at 500 seeds the level-feature attacker of review C (GBT on price, SMA20, SMA50 and their lags) reaches an R²(x) no higher than the level-free attacker's within its cluster-bootstrap CI, in every scenario; and the "compare price with 100" rule's MCR is within the CI of the constant-edge policies. The discriminating LLM experiment for A vs B vs C is REG-1 (≈ 60 Flash runs ≈ $11). Phase 1 reports that the analyst field and EPS × k still reveal V_1 under every option; that channel is Phase 5's.

E1.2 *Value–mispricing decomposition on data*: unchanged, with **[changed: LOG §7]** the stated caveat that VR(500) has ≈ 8 non-overlapping windows per stock in 25 years, so the pooled block-bootstrap CI will be wide, and the pre-registered rule "adopt the pooled FIT if the two methods' σ_V intervals overlap, else D3" stands. **[changed: REG-5]** A third estimator (SMM with persistence-carrying moments, E2.3) is added to the comparison, and the rule for disagreement among the three is REG-5's.

E1.3 *σ_V sweep*: unchanged, plus **[changed: LOG §3]** s_x is swept jointly ({0.10, 0.13, 0.165, 0.20}) because the Kalman bound depends on s_x/σ_V, and the analytic bound is tabulated beside the surrogate at every grid point.

E1.4 *Where jumps belong*: unchanged in design; **[changed: LOG §2]** the pre-registered rule "E[x] in flat within 2 SE of 0 at 200 seeds" is completed with an equivalence margin (|E[x]| ≤ 0.02, i.e. below the smallest θ candidate 0.03 — the margin is DESIGN and labelled) and with the statement that removing the negative jump mean lowers the flat-path share with excess kurtosis > 1.5 from 0.85 to 0.70 (mean-zero x-jumps) or 0.60 (no jumps) at 40 seeds, so the jump size distribution is re-fitted in E3.2 before checklist item 2 is re-scored. Alternatives and the discriminating analysis: REG-3.

E1.5 *Burn-in*: **[changed: LOG §7]** the criterion is "the bootstrap 95 % upper limit of the two-sample KS distance between the day-1 state and the 5,000-day state is below 0.10" (500 seeds each), not "KS < 0.10" (the critical value at these sizes is 0.086).

E1.6 *Level-free leakage audits*: unchanged, plus the analytic bound (Appendix B) printed beside every price-only R² with the note that under the v2 parameters it is 0.14–0.26 within a 200-day window and 0.40 at steady state (LOG §3).

### 5.3 Decision rules

- Start price: mechanism A/B/C by REG-1's experiment; the range (A, C) is FIT. **[changed: this was "randomised (no alternative survives)" — the principle survives, the mechanism is D13.]**
- σ_V, s_x, h: FIT from E1.2 (three estimators, REG-5 rule); otherwise D3 (REG-2 gives the three environments' consequences).
- μ_V: LIT from Shiller's price-only return (FIT on the file) — the DMS 4.3 % is not a long-run number and is dropped.
- df_V, jumps, burn-in: unchanged (with the E1.4/E1.5 corrections).

### 5.4 Tests locked in

**[changed]** `test_start_price_carries_no_information` becomes the attacker-based test above; the rest unchanged; plus `test_kalman_bound_tabulated` (the bound is regenerated from `params/value.json`).

### 5.5 Documentation, 5.6 Compute, 5.7 Blockers: unchanged, plus the constituent-source problem (Section 3) as a blocker to resolve before E1.0, and the note that a large fitted σ_V lowers the price-only bound *further* (0.08 at σ_V = 0.02) — which is the D3 consequence, now with numbers.

---

## 6. Phase 2. Mispricing engine

Goal and weaknesses: unchanged.

### 6.1 Literature

- Franke & Westerhoff (2012): **[changed: read; URL corrected; LOG §4.2]** equations, units, DCA-HPM parameters, the nine moments and p = 32.6 % confirmed; the paper states no mean chartist share. SABCEMM (arXiv:1812.02726; read): DCA-HPM average chartist share 0.23, excess kurtosis 7.8 (200 runs × 7,000 steps); the 0.17 / 10 pair is DCA-WHP. Pruna et al. (2016; read): FW+ with a GBM fundamental, Table 1 parameters as in `mispricing.py`. Platt (2020), Grazzini & Richiardi (2015): existence confirmed.
- Persistence at the firm level: the corrected sources of 5.1 (Bartram–Grinblatt and RKRV cannot supply h; Balvers–Wu–Gilliland's 3–3.5-year half-life is index-level, annual, panel).
- Estimator bias: Marriott & Pope (1954) and Kendall (1954) confirmed to exist; the leading-term formula attributed to them could not be read at source and is not quoted; Andrews (1993) confirmed; Lo & MacKinlay (1988) confirmed (note the 1990 erratum).

### 6.2 Experiments

E2.1 *Units verified at source*: **[changed]** done (0.2). What remains is the reproduction: simulate FW's **own** model (their price equation, their two Gaussian demand noises, no GARCH, no jumps, no drift) at the DCA-HPM set with `price_scale` ∈ {1, 100}, 200 runs × 7,000 steps as in SABCEMM, and compare the average chartist share and excess kurtosis with 0.23 / 7.8; the convention that reproduces them is confirmed. Simulating the v2 hybrid instead would fail both conventions and make the rule unmeetable (LOG §7).

E2.2 *Firm-level persistence*: unchanged in method; **[changed: REG-5]** three estimators (variance ratios; P/V̂ AR(1) with Andrews' correction; SMM persistence moments) with the pre-registered disagreement rule.

E2.3 *SMM redone properly*: unchanged.

E2.4 *FW vs AR(1)+GARCH decision*: **[changed: REG-4]** a third candidate is added — the published FW variant with a stochastic fundamental (FW+ of Pruna et al. 2016; read) — so that "a working FW" is compared against both an honest AR(1)+GARCH and a published model whose structure matches v2's (V a GBM). The rule is unchanged in form (acceptance + held-out moment prediction + checklist/leakage equivalence) and is stated to be asymmetric on purpose (FW must both be accepted and beat AR(1)+GARCH by one bootstrap sd; ties go to the simpler model).

E2.5 *Half-life reporting*: unchanged except **[changed: LOG §1]** the "150 vs 188 d" diagnosis is withdrawn: the discrepancy is pilot sampling error; the documents report the pull-rate half-life and the 200,000-step ACF(1) half-life (147 d, range 141–154 over five pilots) together with the T = 200 / T = 800 / T = 5,000 estimator table.

E2.6 *Persistence sweep*: unchanged, plus the oracle-switch count per run (LOG §2: median 0/0/1/2 switches at the live half-life, 1/1/1.5/2 at 60 d, 2/1.5/2/2 at 30 d; coverage 0.81 → 0.42 in flat) reported at every level because it feeds the go/no-go checkpoint (Section 16A).

### 6.3–6.7: unchanged, with `test_half_life_consistency` already hard from Phase 0.

---

## 7. Phase 3. Volatility

Goal and weaknesses: unchanged (plus the jump size/rate of item 13).

### 7.1 Literature

**[changed: LOG §4.2]** Engle (2001): α 0.077, β 0.905 on a 50/30/20 Nasdaq/Dow/bond portfolio, daily 1990–2000 (portfolio, not "index"). Hansen & Lunde (2005): confirmed on IBM daily. GJR (1993): monthly, confirmed. Lee & Mykland (2008): confirmed (β* = 4.6 at 1 %). Andersen, Bollerslev & Diebold (2007): jump variation is 14.4 % of realised variance for S&P 500 futures (1990–2002), 27.9 % of days with a significant jump — index futures, intraday-based. Ang & Timmermann (2012): 4.89 % vs 2.45 % monthly (variance ratio ≈ 4.0) confirmed; Ang & Bekaert (2002): 7.04 % vs 3.77 % confirmed (both index, monthly). **Hamilton & Susmel (1994): the variance factors could not be read (paywalled) and may not be quoted.** Schwert (1989): recession/expansion volatility +76 % (1859–1986) to +227 % (1927–86), index, monthly. GSY (2019): confirmed (industry level, monthly). Carr & Wu (2009): individual-stock log VRPs negative for 21 of 35 names, mean VRPs mostly insignificant. **Bakshi & Kapadia (2003) RFS is index-only** — dropped for the single-stock claim. **Goyal & Saretto (2009) sort on log(RV/IV)**, not log(IV/RV) — corrected. Christensen & Prabhala (1998): log RV on log IV slope 0.76, R² 39 % (S&P 100, monthly). Bollerslev–Tauchen–Zhou (2009), Bollerslev–Todorov (2011), Kou (2002), Bates (1996), Bollerslev (1986): existence confirmed.

### 7.2 Experiments

E3.1 GARCH fits, E3.2 jumps, E3.3 event-window multipliers: unchanged (E3.2 also delivers the size distribution needed by E1.4's placement; Section 2).

E3.4 *How the regime enters the variance*: **[changed: REG-6]** three mechanisms (whole-variance scaling; ω-scaling with a ramp; a fitted two-regime switching-variance model) decided by the empirical rise/decay-time rule, with the sample size of single-stock episodes stated and a CI on the rise time; the rule's fallback (no mechanism inside the CI) is written.

E3.5 *Implied volatility*: unchanged, plus **[changed: REV-11b adopted]** the onset audit compares IV against the *same filter's* 21-day realised-variance forecast, so that the premium's legitimate rise through returns is not counted as a leak; and **[changed: LOG §5]** the single-stock IV level is FIT on the five CBOE histories (VXAPL…VXIBM, 2011–2026) against the names' realised variance, with the literature values beside it; the sensitivity remains.

E3.6: unchanged.

### 7.3–7.7: unchanged, with the IV level now FIT-on-five-names rather than LIT-only.

---

## 8. Phase 4. Events, schedule and controls

Goal and weaknesses: unchanged (item 47 closes here).

### 8.1 Literature

**[changed: LOG §4.2]** Mishkin & White (2002): 15 twentieth-century crashes, 20 % definition, confirmed. **Barro & Ursúa: NBER w14760 (2009) / Research in Economics 71(3) 2017**, 30 countries, 232 crashes at ≤ −25 % multi-year real returns; w22743 is a different paper. **Pagan & Sossounov (2003): durations not read; not quoted.** GSY (2019): confirmed — note the unit is an *industry* run-up (net of market, monthly), so the hazard slope transfers to a single stock only under a stated assumption. LPPLS papers: all four exist (Filimonov–Sornette 2013 is the linearised fit). Campbell, Giglio & Polk (2013): *Review of Asset Pricing Studies*, not RFS; 2000–02 discount-rate driven, 2007–09 cash-flow driven (index, quarterly) — confirmed.

### 8.2 Experiments

E4.1 Episode tables, E4.2 Sampling ranges: unchanged (with the citations corrected).

E4.3 *Hazard*: unchanged, plus **[changed: REV-11c adopted]** the horizon assumption written down: GSY's probabilities are two-year crash probabilities conditional on a two-year industry run-up; the daily hazard over a 40–150-day mania is obtained by (i) fitting b from the three GSY points, (ii) setting h0 so that the cumulative hazard over the median mania length equals the GSY probability at the median peak run-up scaled by the ratio of the mania length to GSY's two-year window — the scaling is an assumption (DESIGN) and is bracketed {0.5×, 1×, 2×} in the sensitivity table.

E4.4 *Mania drift*: unchanged.

E4.5 *Sustained bull*: **[changed: REV-2a adopted; LOG §7; REG-7]** not decided here. With d_t = 0 and no x-band, only 8 % of unanchored draws stay inside [−0.10, 0.15] (50 seeds; 94 % pass the V criterion), the path-mean x has p10/p50/p90 = −0.34/−0.11/+0.07, and the control becomes "flat market plus rising value" rather than "rising value without mispricing". Four definitions of the control are implemented (same process/no band; band on V only; anchored x as in v2; a control defined on the *rendered* fields by matching the flat scenario's x distribution with a rising V) and the pre-registered comparison of REG-7 decides; the team's D14 states which purpose the control serves. The measurements the plan listed (realised x distribution, accepted-vs-rejected statistics, the scenario-discrimination audit at chance) are made for every definition. The label-permutation null for the audit is computed **here** (it needs only the generator), removing the dependency on Phase 6.

E4.6 *Error-correction gains*: **[changed: REG-8]** a fourth formulation is added — an unscripted regime-switching model without error correction (the event is a change in the fundamentalists' perceived p* and in the regime variance, with no target path) — and the pre-registered rejection rate is set **here** from the episode tables (E4.2), not in Phase 6.

E4.7 *Orderings and the calendar*: **[changed: LOG §5]** `experiments/arms_v2.py` has no ordering factor; the runner has. The factor is added to the arm grid in this phase (a harness change, tested). The calendar rendering options and the ordering mix are REG-9; D6 remains the team's.

E4.8: unchanged.

### 8.3 Decision rules: E4.2, E4.3, E4.6 rules; the control is D14 (REG-7); the calendar is D6 (REG-9).

### 8.4–8.7: unchanged, plus `test_arm_grid_has_ordering_factor`.

---

## 9. Phase 5. Observables

Goal and weaknesses: unchanged.

### 9.1 Literature

**[changed: every recalled number is replaced by the value read at source, LOG §4.3; the phase report may only carry read values]**
- Earnings: Foster (1977; read) — Model 1 is the seasonal random walk, Model 5 E(Q_t) = Q_{t−4} + φ(Q_{t−1} − Q_{t−5}) + δ is the usual "Foster model"; 69 firms, quarterly, 1946–74. Ball & Brown (1968) and Brown & Rozeff (1979) confirmed; **Kothari (2001) could not be read — no surprise magnitude is taken from it.** EPS noise, announcement lags and the negative-EPS frequency are FIT on EDGAR.
- Multiples: FIT on EDGAR × prices; Damodaran's `pedata.xls` (served) as the cross-check.
- Dividends: Lintner (1956) not readable at source; secondary (Lambrecht & Myers; Fama & Babiak) give a speed of adjustment ≈ 0.3 on **aggregate annual** data — usable only as a sanity range; Brav et al. (2005) is a survey with no SOA estimate; Leary & Michaely (2011) full text not read. Payout and quarterly stickiness are FIT on EDGAR DPS.
- Analyst estimates: Brav & Lehavy (2003; read): targets 28 % above price on average (Table VI; 900 firms, weekly consensus 1997–99); Bradshaw, Brown & Huang (2013; read): **absolute target-price errors average 45 %**, 38 % of targets met at 12 months, 64 % at some point (2000–09); Bilinski et al. (2013; read): mean absolute error 44.7 %, 59.1 % reached. So the error anchor is LIT: absolute error ≈ 45 % of price at a 12-month horizon (converted to a log-sd in REG-10d, with the horizon mismatch stated: the field is a *fair-value* estimate, not a 12-month target). Da & Schaumburg (2011), Gleason et al. (2013): existence confirmed.
- Sentiment: Tetlock (2007; read): 8.1 bp next-day DJIA return per one-sd pessimism, 6.8 bp reversal over days 2–5 — **index level, daily**; Garcia (2013; read): NYT 1905–2005, index; Boudoukh et al. (2019; read): news explains 49.6 % of overnight idiosyncratic volatility, firm level; Baker & Wurgler (2007; read): **monthly, market level**; Brown & Cliff (2004): existence only; Shapiro, Sudhof & Wilson (**2022**, J. Econometrics 228): SF Fed daily index confirmed available for the FIT.
- Volume: **Karpoff (1987): the 0.2–0.5 range could not be read and is not used**; Lo & Wang (2000; read): weekly turnover-index AC(1) 0.91 (VW) / 0.87 (EW), **market level, weekly**; Gallant–Rossi–Tauchen (1992), Llorente et al. (2002): existence confirmed; GSY (2019; read): turnover high in run-ups that crash *and* those that do not. The |r| elasticity, the log-volume AR(1) and the noise are FIT on the panel.
- Technicals: unchanged (Appel needs a specific edition; BLL 1992 and Wilder 1978 confirmed).

### 9.2 Experiments

E5.1 *Multiple*: **[changed: REG-10a]** three designs (fixed draw with a FIT-wide range; time-varying log-AR(1) with FIT dispersion and persistence; a multiple tied to a fitted cross-section of P/E on observable characteristics) and the pre-registered leakage/onset comparison that decides.

E5.2 EPS and lags, E5.3 Dividends: unchanged, except **[changed: ordering, LOG §7]** D10 (pay dividends vs remove the field) is put to the team **before** Phase 5 starts, since E5.3 depends on it; if undecided, both variants are carried.

E5.4 *Analyst estimate*: REG-10d.

E5.5 *Sentiment*: **[changed: REV-2b adopted; REG-10b]** the valuation loading is not set to zero by fiat; three designs (returns-only; returns plus a slow valuation link with a FIT market-level size, defined as the regression coefficient of the SF Fed index on the Shiller CAPE log-deviation, monthly, with its CI; survey-style AR(1) with a return loading FIT on AAII) are pre-registered with the discriminating audit; the team's D15 records the default after the results.

E5.6 *Volume*: REG-10c (|r| only vs |r| plus a run-up turnover ratio FIT from the panel's GSY-style run-ups).

E5.7 *Audits*: unchanged.

### 9.3–9.7: unchanged, with D10 and D15 added.

---

## 10. Phase 6. Audits and checklist methodology

Goal, weaknesses, literature: unchanged (Cont 2001 and the leakage-methodology sources per LOG §4.3).

### 10.2 Experiments

E6.1 Reference distributions: unchanged, plus the single-stock IV reference from the five CBOE histories.

E6.2 *Re-derived criteria*: **[changed: LOG §3]** the equivalence form is "the bootstrap 95 % upper limit of the two-sample KS distance between the generator's cross-seed distribution and the real-window distribution is below D0 = 0.10", or the P10–P90 band with a share criterion; "the KS test did not reject" is not a criterion (at n_real ≈ 3,000 and n_gen ≥ 350 it rejects D = 0.10 with 97 % power). The alternatives for the criterion form and for the seed/horizon policy are REG-14.

E6.3 Power analysis, E6.4 per-scenario reporting, E6.5 L1 extended set: unchanged.

E6.6 *L2 gate derivation*: unchanged, plus the numbers now known (Appendix B): the analytic bound under the v2 parameters is 0.40 (steady state) and 0.14–0.26 within 200 days, matching reviewer C's level-free R² of 0.40; the surrogate is checked against it at every (σ_V, s_x, h) of Phase 1's sweep. L3 probe cost: **[changed: LOG §6]** 200 probes × 5 models × 2 arms = 2,000 calls total, 400 per model, ≈ $12 at today's prices with the 1.3× tokenizer factor on the Claude 5 models [edit 27 Aug] (Flash $0.4, GPT-5 mini $0.3, Sonnet 5 $2.9, Haiku 4.5 $1.1, Opus 5 $7.2); the plan's $25 matched neither reading of its own line.

E6.7–E6.9: unchanged.

### 10.3–10.7: unchanged, with the ≈ $12 figure.

---

## 11. Phase 7. Targets, action and metrics

Goal and weaknesses: unchanged.

### 11.1 Literature

**[changed: LOG §4.3]** Donohue & Yip (2003): exists (JPM 29(4):49–63) but the text is inaccessible — **the "2–5-point bands at 5 bp" attribution is unverified and is not used**; Sun et al. (2006; read) use 40–60 bp costs and a 5 % tolerance band in their examples. Merton (1969/1971): confirmed. Practitioner pages (read): Morningstar equity bands 15–30 / 30–50 / 50–70 / 70–85 / 85+ %; Fidelity Conservative 20 % equity (80 % bonds + short-term), Balanced 50 %, Growth 70 %, Aggressive Growth 85 %; Vanguard conservative 40/60 (30/70 in retirement); Betterment conservative = 4–7 pp below the recommended stock share. Jiang, Peng & Yan (2024; read): Table 7 gives trait coefficients on the equity-to-wealth ratio (Neuroticism −1.74, Openness +0.94, Conscientiousness −1.32), **no stated conservative-minus-aggressive spread** — `targets.py`'s JFE_SPREAD (0.06, 0.12) must be re-derived from Table 7 in the phase report before it is used. Fieberg, Hornuf, Meiler & Streich (2025, CESifo WP 11666; read): LLM average equity share 67 % vs robo-advisors 59 %. Costs: Nasdaq (2024; read): 4.5 bp is the cap-weighted **quoted spread** of the S&P 500 basket; Frazzini, Israel & Moskowitz (2018 draft; read): **median market impact 6.18 bp** per trade (mean 9.97) — the two are different cost concepts and the phase states which one the 5 bp per side represents.

### 11.2 Experiments

E7.1 *θ derivation*: **[changed: REV-7 adopted; LOG §7; REG-11]** θ_info and θ_cost are **co-primary**: every headline metric is reported at both, with θ_var and the fixed grid {0.03, 0.05, 0.08, 0.12, 0.20} as sensitivities. The rule states its own failure modes: if the level-free surrogate never reaches sign accuracy 0.80 (review C measured 0.71 on resolvable steps), θ_info is reported as "not reached" and θ_cost alone is primary until Phase 9 shows whether any conclusion depends on the choice (D7).

E7.2 *Regret decomposition*: unchanged in content; **[changed: REG-12]** the per-window scoring and the alternative ceiling/floor conventions are pre-registered as alternatives with the construct-validity experiment (E7.8) as the discriminator; the switch counts are already known (LOG §2) and go into Section 16A.

E7.3 *Bands*: unchanged; the practitioner-vs-utility-consistent choice is D9 with REG-13's experiment (both as a factor is the third option).

E7.4 Dividends: D10 is taken before Phase 5 (Section 9).

E7.5–E7.8: unchanged.

### 11.3–11.7: unchanged.

---

## 12. Phase 8. Harness and statistics

Goal, weaknesses, literature (statuses per LOG §4.3): unchanged.

E8.1–E8.4: unchanged. E8.5 *Variance pilot*: unchanged in design; **[changed: LOG §6]** cost ≈ $105 on Flash or ≈ $86 on GPT-5 mini (not $40); D12 stays open (LOG §10: "0.33 is conventional" is not a justification under the hard rules; the team states the minimum effect in the claim's own units — the practitioner bands are 20 pp wide, so 0.05 band-MAS is a quarter of a band — and it is labelled DESIGN).

### 12.3–12.7: unchanged with the corrected cost.

---

## 13. Phase 9. Sensitivity through the LLM harness

### 13.1 Parameters and levels

Unchanged in the six parameters, with **[changed: REG-16]** the choice of the six, the tiers, the roster and the inclusion of the stateful arms made decidable by the variance pilot: the six parameters are confirmed (or replaced) by the rank of their checklist/audit effect sizes from Phases 1–6 — the pre-registered rule is "the six generator parameters with the largest standardised effect on the level-free observables-oracle regret and on band-MAS of the scripted policies (E7.8), ties broken toward the ones the reviews name" — and the stateful arms enter Tier B on the two highest-ranked parameters only if the variance pilot's ICC shows the stateful contrast is estimable at 5 seeds. "Full Baker–Wurgler-sized" is defined (Section 9: the FIT market-level coefficient).

### 13.2 Grid and cost

**[changed: LOG §6, today's prices and measured prompt sizes]** Tier A: 1,170 runs per model — Gemini 2.5 Flash ≈ $210; GPT-5 mini ≈ $175. Tier B: Tier A on both (≈ $385) + Claude Sonnet 5 on 280 runs ≈ $390 with the 1.3× tokenizer factor [edit 27 Aug] (≈ $200 with cached system prompts) → ≈ $775. Tier C: + ≈ 1,000 Flash runs ≈ $180 + 300 GPT-5 mini runs ≈ $45 → ≈ $1,000. Batch pricing (−50 %) is available at all three providers only with a lock-step runner (a harness change to be costed in Phase 8 if the team wants it). The ordering factor is present in the arm grid from Phase 4.

### 13.3 Pre-registered robustness criteria

**[changed: LOG §7]** Criterion (iii) ("the effect size stays within the CI of the default-level effect") is replaced: the generator-level × arm interaction is tested with a pre-registered equivalence margin equal to half the minimum effect of D12; a conclusion is robust if (i) the sign is unchanged at every level, (ii) the BH-corrected q < 0.05 in the crossed model, and (iii′) the interaction's 90 % CI lies inside ± the margin. Otherwise unchanged.

### 13.4–13.5: unchanged.

---

## 14. Phase 10. Documentation, slides and script

Unchanged, except that the immediate deck-corrections note is produced in Phase 0 (0.2b) and the claims ledger absorbs it.

---

## 15. Cross-phase summary: experiments, compute, cost and effort

**[changed: REV-8 adopted — an analyst-effort column is added. These numbers carry the label ESTIMATE: they are this pass's judgement from the task counts (12 pre-registrations, the number of fits, code modules and reports per phase) and unit times of 0.5–1 day per pre-registration, 1–2 days per fitted module, 2 days per phase report; no source or experiment can supply them and they must not be quoted as evidence.]**

| Phase | Local compute | API cost (today's prices) | Analyst effort (ESTIMATE, person-days) | Team decisions needed |
|---|---|---|---|---|
| 0 | 0.5 h | none | 4–6 | none |
| 1 | panel download (hours) + 3 h | none | 8–12 | D1, D13 (start-price mechanism), D3 if needed |
| 2 | 4 h | none | 8–12 | none unless E2.4 ties |
| 3 | 1 h | none | 5–8 | none |
| 4 | 2 h | none | 10–14 | D4, D5, D6, D14 (control) |
| 5 | data retrieval (hours) + 3 h | none | 8–12 | D10 (before the phase), D15 (sentiment loading) |
| 6 | 5 h | ≈ $12 (L3) | 8–12 | none |
| 16A go/no-go | 1 h | none | 1 | D17 (if the criterion fails: D8 options) |
| 7 | 0.5 h | none | 5–7 | D7, D8, D9 |
| 8 | 1 h | ≈ $105 (Flash) / ≈ $86 (GPT-5 mini) | 7–10 | D11, D12 |
| 9 | orchestration; ≈ 9 h wall-clock per model per tier at 15 concurrent calls of ≈ 2 s | ≈ $210 / $775 / $1,000 by tier (Claude 5 lines ×1.3, [edit 27 Aug]) | 3–5 + run time | tier and roster (D2) |
| 10 | 1 h | none | 5–8 | none |
| **Total** | | **≈ $120 before Phase 9 + the tier** | **≈ 72–107 person-days serial; ≈ 60–65 working days on the critical path with the parallelism of Section 16** | |

**[changed: REV-9 adopted]** *Minimal path.* Phase 0 → E1.1 + E1.6 → E2.1 → E5.7 → E7.2 → Phase 10 closes the seven headline items (1–7) and produces a defensible v2.0.1 in ≈ 15–20 person-days (ESTIMATE) with no API cost beyond Phase 0. It does **not** fit any parameter to data, so every LIT/DESIGN label stays and the paper's claims are limited to what the level-free audits show. Which programme runs first is D16; this plan does not recommend one because the choice depends on the team's deadline, which is not evidence available here.

Total API spend proposed before Phase 9: ≈ $120 (the plan's $325 over-counted the L3 line; LOG §6; Claude 5 lines carry the 1.3× tokenizer factor, [edit 27 Aug]). The main grid remains outside scope; its size is set by E8.5.

---

## 16. Order, dependencies and gates

**[changed: REV-8 adopted; dependencies traced in LOG §7]**

```
Phase 0 (freeze, bugs, deck-corrections note)
   │
   ├──────────────► Phase 8 (harness fixes, statistics re-spec)  ── needs only the pilot logs; runs any time after 0
   │                     └── E8.5 variance pilot (API) after the v2.1 freeze of Phase 6 (execution-order rule)
   │
   ▼
E1.0 shared panel  ──┬──► Phase 1 (E1.1 start price ‖ E1.2–E1.6)
   (+ E3.1 GARCH     ├──► Phase 2 (E2.1 pure-FW check ‖ E2.2/E2.3 need E1.2 and E3.1)
    fits run here)   └──► Phase 3 (E3.2–E3.6; E3.2 needs E1.4's placement)
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
        Phase 4 (events, control,        Phase 5 (observables; needs D10;
          gains, calendar; own nulls)      needs Phase 1's level-free audit)
              │                               │
              └───────────────┬───────────────┘
                              ▼
                        Phase 6 (reference distributions, criteria, gates, L3)
                              ▼
                     ▶ 16A GO / NO-GO CHECKPOINT ◀
                              ▼
                        Phase 7 (θ, regret, bands, gate, baselines)
                              ▼
                        Phase 9 (LLM sensitivity grid)   ◄── Phase 8's power analysis
                              ▼
                        Phase 10 (ledger, deck, script)
```

Rules: Phases 1, 2, 3 run in parallel on the shared panel with the two stated cross-links; Phases 4 and 5 run in parallel after 3; Phase 8's code work is independent of 1–7 and its pilot waits for the Phase 6 freeze; every phase re-runs the checklist and audits on the frozen state it hands over (execution-order step-0 rule). A phase is re-opened if a later phase's evidence contradicts its decision (logged).

v2.1 acceptance: unchanged, plus "the go/no-go criterion of 16A is met, or the team has taken D17".

### 16A. Go/no-go checkpoint after Phase 6 **[changed: REV-3 adopted; thresholds derived, not chosen]**

Written now, before Phase 1 starts; not moved afterwards. Computed on the Phase-6 frozen generator at the co-primary θ values, with ≥ 100 seeds per scenario and cluster-bootstrap 95 % intervals over paths; the policies are the mandate-conditional (true-V) oracle, the **level-free** observables oracle (current-day fields plus a 20-day history, trained on disjoint seeds, no level features), the best simple level-free rule from a pre-registered family (price vs SMA50 thresholds, RSI thresholds, analyst-vs-price thresholds, each with its scale fitted on the training seeds), and the trivial policies (always-hold at centre, constant band edges, random).

- **G1 (there is information to act on).** In every scenario, MCR(true-V oracle) < MCR(observables oracle) < MCR(best trivial policy), with non-overlapping 95 % intervals between adjacent pairs. *Derivation:* this is the ordering the L5 audit already presupposes; the interval rule is the plan's own reporting standard, not a chosen margin.
- **G2 (it is not solved by a two-line rule).** The best simple rule's MCR is above the observables oracle's, with non-overlapping intervals, in at least three of four scenarios. *Derivation:* item 1's finding is that a two-line rule reached oracle level in three of four scenarios; G2 is that finding's negation on the same scenario count.
- **G3 (judgement over time, not a one-shot call).** The median number of oracle target switches per run is ≥ 2 in the three event scenarios and the share of runs with ≥ 2 switches is ≥ 0.5. *Derivation:* item 48 and review C.15 define the one-shot call as "zero or one target change per run"; ≥ 2 is the smallest count that is not a one-shot call. Known today (LOG §2): the live engine gives medians 0/0/1/2 and shares 0.23–0.27 (event scenarios), the 60-day engine 0.37–0.50, the 30-day engine 0.50–0.67 with coverage falling to 0.42 in flat — so G3 will fail unless Phase 2's FIT persistence is short or D8 changes the horizon/scoring. **[edit 27 Aug] G3 may not be met by choosing a persistence shorter than the fitted value: the persistence literature read in Phase 1–2 (Summers 1986, Poterba–Summers 1988, Balvers et al. 2000) points to half-lives of months to years, so a FIT persistence will give at most one decision per 200-day run, and a persistence shortened to pass G3 would be the tuning-to-pass the hard rules forbid. If G3 fails at the FIT persistence, the admissible responses under D17 are a longer horizon reported as a factor, per-window scoring, or restricting the paper's claim to a one-shot mandate-conflict benchmark — not a shorter half-life.**
- **G4 (the price-only reader is not the whole story).** The level-free observables oracle beats the level-free price-only oracle with non-overlapping intervals in every scenario, *and* the price-only surrogate's R²(x) lies at or below the Appendix B bound within its CI. *Derivation:* the first clause is the paper's "observables matter" claim stated as a test; the second is the leak test.

If any of G1–G4 fails, the plan stops after Phase 6 and the team takes D17: for G1/G2/G4 the options are Phase 5's field redesign or D3's environment choice; for G3 the options are D8's (a longer horizon with T reported as a factor, or per-window scoring; a shorter half-life is admissible only if it is itself inside the FIT interval — [edit 27 Aug]), each of which re-runs Phases 2 and 6 for the chosen option; if none is taken, the paper's claims are restricted to a one-shot mandate-conflict benchmark and say so. Results are reported under the pre-registered criterion in every case.

---

## 17. Decisions that only the team can make

D1–D12 unchanged in substance, with the corrected costs (D2) and the note on D12 (LOG §10). **[changed: five decisions added; for each the register gives the discriminating experiment so the team decides from results]**

- **D13.** Start-price mechanism: randomise the level / normalise the price / both (REG-1). **[edit 27 Aug]** REG-1's discriminating LLM test runs in Phase 9, so Phases 1–6 must run under a provisional mechanism; the register names B (normalise the price) by exclusion, because it is the only option under which an LLM-side magnitude effect cannot exist. The generator-side audits are identical under A, B and C, so nothing in Phases 1–6 is re-run if the Phase-9 test later prefers A or C; only the rendering changes. The team is asked to approve the provisional B now rather than discover it later.
- **D14.** What the sustained-bull control is for, and hence which definition (REG-7).
- **D15.** Sentiment's valuation loading default, after REG-10b's audit.
- **D16.** Full programme vs the minimal path first (Section 15).
- **D17.** If the 16A criterion fails: which of the D8/D3/Phase-5 options to run.

Where the plan review offered answers (D6 no date, D9 practitioner bands, D10 pay dividends, D11 common-start only, D12 0.33): recorded as one reviewer's opinion; not adopted here, because each is a preference and the register's experiments decide them.

Commit points: unchanged.

---

## Appendix A. Power-analysis formulas

- Share-type criterion: unchanged (re-derived: 418 and 109; LOG §3).
- Median/correlation criterion: unchanged formula; **[changed]** the bootstrap is the default, the 1.25 (= √(π/2)) normal approximation the exception.
- Generator-vs-real equivalence: **[changed: LOG §3]** stated as an equivalence test. With n_real ≈ 3,000 and n_gen ≥ 350 the two-sample KS test rejects equality at a true D = 0.10 with 97 % power (simulated), so non-rejection is not evidence of equivalence. The criterion is: the bootstrap 95 % upper limit of the KS distance < D0 = 0.10. Power for equivalence: with n_gen = 500 the KS distance's sampling sd is ≈ 0.02–0.03, so a true D ≤ 0.05 passes with ≈ 80 % power; a true D ≥ 0.10 fails.
- LLM arm contrasts: unchanged.

## Appendix B. The analytic level-free price-only bound for x

Model and filter unchanged. **[changed: computed, LOG §3]** Results at h = 150 d: σ_V = 0.006, s_x = 0.13 → R² 0.14 averaged over a 200-day window from the stationary prior, 0.24 on day 200, **0.40 at steady state**; with s_x = 0.165 (the third pass's reported stationary sd; not reproduced on 27 Aug, where 0.13–0.14 was measured — the 0.13 row is therefore the reference) 0.15 / 0.26 / 0.48; σ_V = 0.010 → 0.10 / 0.16 / 0.23; σ_V = 0.020 → 0.04 / 0.07 / 0.08. With the anchor (V_1 known) the bound is instead 1 − σ_V² t/s_x² ≈ 0.998 on day 1 and 0.57 on day 200 — which is what the published price-only R² of 0.79–0.90 reflected. **The plan's sentence "under the v2 parameters the bound is high because V is smooth" is withdrawn**: the level-free bound is modest (0.40) and it matches reviewer C's level-free GBT (0.40); what was high was the anchored bound. A Vuolteenaho-type σ_V lowers it further (to ≈ 0.08 at 0.02/day), which is D3's consequence with numbers. Caveats: linear-Gaussian bound; calm windows only; a nonlinear filter on t/GARCH/jump innovations can exceed it slightly, so the surrogate is compared with the bound "within its CI plus the nonlinear allowance measured on a Gaussian control run".

## Appendix C. Numbers in the current documents that will be recomputed

Unchanged list, plus **[changed]** the pilot half-life 187/188 d (→ 147 d at 200,000 steps), the stationary sd 0.128/0.13 (→ 0.13–0.14 in the 27-Aug pilots; the third pass's 0.165 is held until reproduced), the analyst sd "0.35" (→ 0.33 on benchmark days / 0.335 analytic), the GPT-5 mini price, the L3 cost, the SABCEMM chartist share (0.23, not 0.17), the Barro–Ursúa citation, the FW PDF URL.
