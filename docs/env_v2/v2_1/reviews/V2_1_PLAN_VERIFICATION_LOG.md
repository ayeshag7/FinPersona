# Verification log for `V2_1_IMPROVEMENT_PLAN.md` (third, independent pass)

Date: 26 August 2026. Working tree at commit `b61fe07` plus the uncommitted docs listed in `git status` (the plan, its review, the verification prompt). Nothing in the repository was modified by this pass except the four deliverables listed in the closing note. No paid API was called. All generator runs used fresh seeds (7000–7109, 8000–8049) so that nothing here is a re-run of the plan's own seeds. Scripts and raw outputs are in the session scratchpad (`repro_table1.py/.json`, `local_experiments.py/.json`, `formulas.py`); the numbers quoted here are copied from those outputs.

Outcome codes: **OK** (reproduced / correct), **OK-with-note**, **WRONG** (with the correction), **UNVERIFIED** (what blocked it).

---

## 1. Section 0.1 / Table 1: findings reproduced with my own seeds

| Item | Plan's value (its n) | This pass (n, seeds) | Outcome |
|---|---|---|---|
| 4 flat control biased cheap | mean x −0.100, median −0.068, P(x<0) 0.70, day-1 −0.076 (30 seeds × 200 d); jumps off: −0.018, 0.50 | mean x **−0.077** (cluster SE 0.019; 50 seeds × 200 d), median −0.074, P(x<0) **0.71**, day-1 **−0.087**; jumps off (30 seeds): **+0.009**, P(x<0) 0.46. A second draw (40 seeds, 8000–8039) gave mean x −0.125 with jumps, −0.025 without. Analytic stationary mean = −(0.010·0.04)/(μ n̄ φ) = −0.0004/0.0046 ≈ −0.087 | **OK.** Path means have sd ≈ 0.13 across seeds, so 30–50-seed means scatter by ±0.02–0.04; every draw is consistent with the analytic −0.087. Phase 0's test (\|mean x\| ≤ 2 SE at 100 seeds) has SE ≈ 0.013 and will detect a bias of this size. |
| 2, 11 FW switching inert | share of days n_f > 0.99 = 0.981 (flat, 30 seeds); index set at `price_scale = 1`: n̄ = 0.827 | n_f > 0.99 on **0.975** of flat days, mean n_f 0.997 (30 seeds); index set 20,000-step pilot: n̄ = **0.9985** at scale 100, **0.8268** at scale 1; ACF(1)-implied half-life 606 d (scale 100) / 617 d (scale 1) | **OK.** The 17 % chartist share at scale 1 reproduces exactly (same deterministic pilot). See §4.2 item 3 for what that 0.17 can and cannot be compared with. |
| 68 analyst error | pooled sd(u) 0.350, median \|u\| 0.262 (30 crash paths × 460 d) | sd(u) **0.306** over the full 460-day timeline (includes the warm-up from the initial N(0, 0.15) draw), **0.330** on benchmark days only; median \|u\| 0.222 (30 crash seeds). Analytic stationary sd = 0.15·√5 = 0.335 | **OK-with-note.** The plan's 0.350 is slightly high for the 460-day window (the first ~100 days have not reached the stationary sd); the benchmark-day value 0.33 and the analytic 0.335 are the numbers to quote. |
| 46 IV phase step | mean Δlog IV at deterioration→panic +0.594 (×1.81); calm sd 0.084; z = 7.1 (30 crash seeds) | **+0.606** (×1.83); panic→stabilisation **−0.619**; calm day-to-day sd of log IV **0.086**; z = **7.06** (30 crash seeds) | **OK.** |
| 18, 42 sustained-bull selection | 17 accepted / 13 rejected first attempts, daily sd 0.0150 vs 0.0242, rejection 0.38 (30 seeds) | **32 / 18** of 50 first attempts, daily sd **0.0153 vs 0.0210**, rejection **0.36**; mean attempts 1.6 | **OK.** |
| 36 half-life estimator | sample half-life median 26 d at T = 200 (30 flat), 72 d at T = 800 (20); 55 % clear 60 d | **35 d** at T = 200 (30 flat; sd(x) within the window median 0.064), **65 d** at T = 800 (20 seeds); **60 %** clear 60 d | **OK-with-note.** The T = 200 median is very noisy (26 vs 35 d on different seed sets; review C got 14 d on calm windows); the substance — the ACF(1) estimator on 200–800-day windows cannot recover a 150-day half-life and the item-9 pass is a coin flip per path — is reproduced. |
| 1 start-price answer key | ISFJ MCR (θ 0.05, 12 seeds): rule 0.014 / 0.007 / 0.005 / 0.098 (flat / crash / bull-trap / sustained-bull); oracle 0.003; always-hold 0.11–0.14 | rule **0.022 / 0.011 / 0.007 / 0.083**; oracle 0.000 (scored directly against the same oracle, no execution lag); always-hold 0.100 (constant 0.8 = band centre, so exactly the half-width) | **OK.** The rule is within 0.01–0.02 of the oracle in three scenarios and fails only in the sustained bull. The plan's 0.003 / 0.11–0.14 come from the runner (next-day execution, cash-share drift); mine are direct, hence the small differences. |
| 71 half-life inconsistency | fallback φ = 0.463; pilot ACF(1) 0.9963 → 188 d; `fw_index` ≈ 610 d | φ = **0.4632**; the cached 20,000-step pilot (seed 12345) gives ACF(1) 0.99633 → **188.5 d**; `fw_index` 606–617 d. **New:** five independent 200,000-step pilots of the live engine give ACF(1) 0.99509–0.99550 → half-life **141–154 d (mean 147 d)**, n̄ = 0.9979, against the pull-rate half-life ln2/(μ n̄ φ) = **150.0 d** | **OK on the numbers, WRONG on the diagnosis.** The 150-vs-188 gap is sampling error of one 20,000-step pilot (SE of ACF(1) at ρ ≈ 0.995 over 18,000 steps ≈ 0.0007; the gap is 0.0010). E2.5's proposed diagnosis ("the chartist term and the weight normalisation shift the effective pull") is not supported: at 200,000 steps the two half-lives agree within 2 %. Phase 0's `test_half_life_consistency` ("agree within 25 % at 200,000 steps… fails now") would **pass** now; the plan should say so and the document fix is to replace 188 d by the long-pilot value. Also new: the stationary sd of x at the live parameters is **0.162–0.169** (200,000-step pilots), not the 0.128 (T = 800 sample sd) or 0.13 used in Appendix B. |

Generator cost: 0.171 s per 200-day crash path including observables (10 paths, after warm-up) — the plan's 0.15–0.2 s is **OK**.

## 2. Table 2 (weakness-to-phase map)

Parsed programmatically: items 1–74 are all assigned to a closing phase (none missing). Nineteen items appear in two rows outside brackets (3, 5, 7, 8, 10, 12, 20, 21, 23, 44, 45, 47, 53, 54, 60, 63, 67, 73, 74); in every case the second mention is a stated split ("input bug in 0, re-specification in 7", "list in 0, corrected in 10", "LLM-side in 9"), so the "exactly one closing phase" rule holds in substance but the table does not say which row is the closer for items 47 (Phase 3 lists it as "mania drift: 4", Phase 4 lists it plainly) and 60 (Phase 7 "next-open logging", Phase 8 "placebo matching" — two different halves of one item). **OK-with-note**: the corrected plan names the closer for 47 (Phase 4) and splits 60 explicitly.

Items a phase claims to close but whose experiments leave open:
- **Item 1 (Phase 1).** E1.1's own test (R² of x_1 on log P_1 < 0.01) is **not met by the plan's mechanism**: with V_1 ~ LogUniform(P_lo, P_hi) and sd(x_1) ≈ 0.13–0.165, R² = var(x_1)/(var(x_1)+var(log V_1)); for LogU(20, 500) that is 0.019, for LogU(15, 400) 0.019, and only a LogU(10, 1000) range reaches 0.0095. The pass rule is either failed by design or met trivially (under the review's normalise-price option P_1 ≡ 100 and R² is identically 0). Replaced in the corrected plan by an attacker-based test (level-feature attacker's R² equals the level-free attacker's within its CI). Also, as the review says, the analyst field and EPS × k reveal V_1 under either option; Phase 1 cannot claim item 1 closed until Phase 5's audit — the corrected plan says "closed for the price channel; field channels re-tested in Phase 5".
- **Item 13 (Phases 1 and 3).** E1.4's rule "E[x] in flat = 0 within 2 SE" rules out variant (c) but removing the jumps' negative mean also removes most of the kurtosis the jumps were tuned to supply: on 40 flat seeds the share of paths with excess kurtosis > 1.5 is 0.85 with the current jumps, 0.70 with mean-zero x-jumps, 0.60 with no jumps (median excess kurtosis 4.7 / 2.7 / 1.8). So closing item 4 re-opens checklist item 2 unless the jump size distribution is re-fitted (E3.2) — the coupling is stated in the corrected plan; the phase that closes 13 is Phase 3, not Phase 1.
- **Item 48 (Phase 7).** E7.2 measures switches but the fix is deferred to D8 — correctly labelled as a team decision, but the count is already known: at θ = 0.05 the ISFJ oracle target changes a median 0 (flat), 0 (crash), 1 (bull-trap), 2 (sustained-bull) times per run at the live half-life (30 seeds each); the share of runs with ≥ 2 switches is 23–27 % (flat/crash/bull) at the 150-day pull, 37–50 % at 60 d, 50–67 % at 30 d, with coverage (share of resolvable steps) falling from 0.81 to 0.42 in flat. The corrected plan carries these numbers into the go/no-go criterion.

## 3. Formulas

- Appendix A share rule: n = (z_0.95·√(p0 q0) + z_0.80·√(p1 q1))² / (p1 − p0)². Recomputed: p0 = 0.80, p1 = 0.75 → **418**; p1 = 0.70 → **109**. Plan says ≈ 420 and ≈ 110. **OK.**
- Median rule: 1.96 · 1.25 · s/√n ≤ w/5; the 1.25 is √(π/2) = 1.2533 (asymptotic efficiency of the median under normality). **OK** as an approximation; the corrected plan makes the bootstrap the default because most checklist statistics are not near-normal.
- KS rule: "with n_real ≈ 3,000 and n_gen ≥ 350, 80 % power to detect a true distance of 0.15 at α = 0.05". Simulated (2,000 replications, normal location shift giving the stated sup-distance): power at D = 0.15 is **1.00** and at D = 0.10 is **0.97**; the asymptotic critical value is c(0.05)·√((n1+n2)/(n1 n2)) = 0.077. **OK but the rule is mis-framed**: a two-sample KS test at these sizes rejects equality at D = 0.10 with 97 % power, so "not rejected" cannot serve as an equivalence criterion with bound 0.10. An equivalence test needs the *upper confidence limit* of the estimated distance to lie below 0.10 (bootstrap the KS distance; TOST-style). The corrected plan restates E6.2 and E1.5 that way.
- Appendix B Kalman bound: derived and computed. State (x_t, x_{t−1}), observation r_t = x_t − x_{t−1} + σ_V z_t (the drift μ is a known constant and drops out), x_t = ρ x_{t−1} + η_t with ρ = 2^{−1/h} and var(η) = s_x²(1 − ρ²); R² = 1 − P_filt/s_x². Results (h = 150 d):

  | σ_V/day | s_x | R² averaged over a 200-day window (stationary prior, no level) | R² at day 200 | steady state (infinite history) |
  |---|---|---|---|---|
  | 0.006 | 0.13 | 0.137 | 0.235 | **0.396** |
  | 0.006 | 0.165 | 0.150 | 0.260 | 0.477 |
  | 0.010 | 0.13 | 0.097 | 0.161 | 0.231 |
  | 0.020 | 0.13 | 0.041 | 0.065 | 0.082 |
  | 0.030 | 0.13 | 0.021 | 0.033 | 0.040 |

  With the anchor (V_1 = 100 known) the bound is instead 1 − σ_V² t / s_x²: 0.998 on day 1, 0.89 on day 50, 0.57 on day 200 — which is what the published price-only R² of 0.79–0.90 reflects.
  **WRONG in the appendix's qualitative statement**: "under the v2 parameters the bound is high because V is smooth". It is **0.40 at steady state and 0.14–0.26 inside a 200-day run** — i.e. low — and it agrees with reviewer C's level-free GBT (R² 0.40 with full history) and with the randomised-start price-only R² of 0.22–0.26. Smoothness of V raises the bound relative to a rougher V, but the absolute level is modest; what made the audits' price-only R² high was the anchor, not the smoothness. This strengthens the plan's case that the level-free reader infers x only weakly from price, and weakens the "playable from price" story, which the go/no-go checkpoint must therefore test explicitly. Caveats to state with the bound: it is the linear (Gaussian) MMSE bound; with t-shocks, GARCH and jumps a nonlinear filter can do slightly better, and event-phase scripted drifts are not in the model, so the bound applies to calm windows and the audit must compare like with like.

## 4. Citations

All three batches were read on 26 Aug 2026 by fetching the source (journal page, NBER/SSRN/arXiv/author PDF, text-extracted) — never from memory. Status: READ-AND-CORRECT / READ-AND-WRONG (with the correction) / NOT-RETRIEVABLE (no number is carried forward). Level and frequency are stated because the plan uses index-level, monthly statistics as anchors for a daily single-stock generator.

### 4.1 Batch 1: value, mispricing, persistence, estimators

| Citation as used in the plan | Status | What the source says (level, frequency, where) |
|---|---|---|
| Vuolteenaho (2002) JF 57 — "cash-flow news the larger share, positively correlated; to verify Table 3" | READ-AND-CORRECT (NBER w8240 version) | Firm level, annual panel VAR, CRSP–Compustat 1954–96. Market-adjusted returns: expected-return-news variance 0.0161 (sd 13 %), cash-flow-news variance 0.0801 (sd 28 %); ER-news share of total unexpected-return variance ≈ 0.25 (s.e. 0.10); correlation of the two news series 0.41. Equal-weighted portfolio: ER-news variance exceeds CF-news variance. |
| Cohen, Polk & Vuolteenaho (2003) JF — "75–80 % of cross-sectional B/M variance explained by future profitability at 15 years" | READ-AND-CORRECT with nuance | Firm level, annual, 1938–97. 75–80 % is profitability **plus** the 15-year persistence of B/M; profitability alone ≈ 55 %, expected returns 20–25 %. |
| Poterba & Summers (1988) JFE 22 — "transitory component sd 15–25 % at index level" | READ-AND-CORRECT | Index level, monthly, 1926–85: transitory components "standard deviation of between 15 and 25 percent and account for more than half of the variance in monthly returns"; postwar subsample shows less mean reversion. |
| Fama & French (1988) JPE — "25–45 % of 3–5-year variance predictable; weaker after 1940" | READ-AND-WRONG (range); post-1940 clause UNVERIFIED | Abstract: ≈ 40 % for small-firm portfolios, ≈ 25 % for large-firm portfolios (monthly data 1926–85). Full text available only as an image scan; the post-1940 statement was not read. |
| De Bondt & Thaler (1985) JF — "3-year reversal ≈ 25 %" | READ-AND-CORRECT | 35-stock portfolios, CRSP monthly: loser-minus-winner cumulative average residual 24.6 % at 36 months (t = 2.20); 5.4 % at 12 months. |
| Bartram & Grinblatt (2018) JFE — "average absolute mispricing and its decay over 1–36 months" | READ-AND-WRONG (attribution) | Reports the *alpha* of a convergence trade (up to 10 %/yr; 73 bp/month fresh, decaying to zero over 34 months), not an average absolute mispricing level. Reword: it gives the horizon over which the signal's return predictability decays. |
| Rhodes-Kropf, Robinson & Viswanathan (2005) JFE — "firm-specific error dispersion and persistence" | READ-AND-WRONG (attribution) | Firm level, annual 1977–2000; reports group *means* of the firm-specific error (e.g. 0.32 acquirers vs 0.03 targets), not its dispersion or autocorrelation. Do not cite for persistence. |
| Lee, Myers & Swaminathan (1999) JF — "P/V mean reversion for the Dow 30" | Existence READ; reversion speed NOT-RETRIEVABLE | Price and value modelled as cointegrated (Dow 30, 1963–96); V/P has predictive power. No half-life read (full text paywalled). |
| Frankel & Lee (1998) JAE — "V/P predicts 36-month returns" | Existence READ; spread NOT-RETRIEVABLE | Abstract confirms; the 36-month return spread was not read on any fetched page. |
| Balvers, Wu & Gilliland (2000) JF — "index half-life 3–3.5 years (panel)" | READ-AND-CORRECT | 18 national indexes 1969–96, panel relative to a world/US benchmark: "half-life of three to three and one-half years". |
| Dimson, Marsh & Staunton, UBS Yearbook 2025 — "4.3 % equity premium over bills, long-run" | READ-AND-WRONG (scope) | 4.3 % is the **world** premium vs bills **since 2000** (2000–24), annualised. The 125-year premium was not on a readable page; US 1900–2024 nominal: equities 9.7 %, bills 3.4 %. |
| Damodaran implied ERP Jan 2025 — "4.33 %" | READ-AND-CORRECT | histimpl.html, start-2025 row: 4.33 % (FCFE), T-bond 4.58 %. S&P 500 level, annual. |
| Campbell, Lettau, Malkiel & Xu (2001) JF — v2's "majority of single-stock variance is idiosyncratic" | READ-AND-CORRECT | Firm-level share of a typical stock's variance 0.724 (1962–97), 0.769 (1988–97); market 0.16, industry 0.12 (NBER w7590 Table 6). Says nothing about mispricing — the plan's criticism of the v2 rationale stands. |
| Andrews (1993) Econometrica — median-unbiased AR(1) | READ-AND-CORRECT (existence; tables via secondary) | Exactly median-unbiased estimator and exact CIs for the AR(1) coefficient under iid normal errors. |
| Marriott & Pope (1954), Kendall (1954) Biometrika — AR(1) bias | READ-AND-CORRECT (existence); formula partially | Both papers confirmed (Biometrika 41:390–402 and 403–404). The −2ρ/n form is attributed to Marriott–Pope in a secondary source; the (1+3ρ)/T form was seen attributed to later authors, not to Kendall. |
| Lo & MacKinlay (1988) RFS — variance ratio with heteroskedasticity-robust SE | READ-AND-CORRECT | NBER w2168 §2.2 (White-type robust z*); weekly index/size-portfolio returns 1962–85; note the 1990 RFS erratum. |
| Campbell, Giglio & Polk (2013) "Hard times", cited as RFS | READ-AND-WRONG (journal) | *Review of Asset Pricing Studies* 3(1):95–132. 2000–02 decline driven by discount-rate news; 2007–09 by cash-flow news. Index level, quarterly VAR. |
| Summers (1986) JF — fads model | READ-AND-CORRECT | u_t = α u_{t−1} + v_t on log price deviations; example α = 0.98 monthly, "about three years … to eliminate half of any valuation error". Index level. |
| Cochrane (2008) RFS — discount-rate news dominates at the index | READ-AND-CORRECT | CRSP VW annual 1926–2004; long-run return coefficient 1.09 vs dividend-growth 0.09. |

### 4.2 Batch 2: volatility, events, Franke–Westerhoff

| Citation as used in the plan | Status | What the source says (level, frequency, where) |
|---|---|---|
| Franke & Westerhoff (2012) JEDC 36(8):1193–1211 — units, DCA-HPM parameters, nine moments, p = 32.6 %, Bamberg PDF | READ-AND-CORRECT on the model, parameters, moments and p-value; **WRONG URL**; **no chartist share stated** | PDF at the plan's URL is 404; served at `.../vwl_wirtschaftspolitik/Team/Westerhoff/Publications/2011/JEDC_RF_FW_Fin.pdf`. Eq. (1) "with respect to the log prices p_t … r_t := 100·(p_t − p_{t−1})"; eq. (5) "p_t the (log) price … p_t = p_{t−1} + μ(n^f d^f + n^c d^c)"; eq. (6)–(7) d^f = φ(p* − p) + ε^f, d^c = χ(p_t − p_{t−1}) + ε^c; misalignment "measured by the squared deviations of p_t from p*". DCA-HPM: φ 0.12, χ 1.50, α_o −0.327, α_n 1.79, α_p 18.43, σ_f 0.758, σ_c 2.087; μ = 0.01, β = 1. Nine moments: AC(1) of returns, mean \|r\|, Hill 5 %, ACF of \|r\| at lags 1, 5, 10, 25, 50, 100. Table 2: DCA-HPM p = 32.6 %. S&P 500 daily, T = 6,866, 1980–Mar 2007. **No numeric mean chartist share anywhere in the paper.** |
| Pruna, Polukarov & Jennings (2016) arXiv:1604.08824 | READ-AND-CORRECT | Quote confirmed ("p_t is the log price … p^f_t is the fundamental log value"); fundamental follows a GBM; FW+ Table 1: φ 0.121, χ 1.555, σ_f 0.592, σ_c 1.917, α_0 −0.301, α_n 1.990, α_p 22.741, μ_p 0.01, σ_p 0.157 (the `pruna_2016` set in `mispricing.py`). Index, daily. |
| SABCEMM contest arXiv:1812.02726 — "DCA-HPM mean chartist share ≈ 0.17, excess kurtosis ≈ 10" | READ-AND-WRONG (row) | Table 1 (200 runs × 7,000 steps): **DCA-HPM: excess kurtosis 7.76, Hill 3.13, average chartist share 0.2285**; DCA-WHP: 10.03 / 2.48 / 0.1674. The plan's pair is the WHP row. Simulated output, not data. Consequence: the v2 engine's 0.173 chartist share at `price_scale = 1` (with Gaussian innovations of sd 0.016 in place of FW's structural noise) should be compared with 0.23, not 0.17; E2.1's reproduction must use FW's own noise to be comparable. |
| Platt (2020) JEDC; Grazzini & Richiardi (2015) JEDC | READ-AND-CORRECT | JEDC 113 (2020); JEDC 51:148–165 (2015). Existence only. |
| Engle (2001) JEP — "α 0.077, β 0.905 on a portfolio" | READ-AND-CORRECT | Table 3: ARCH(1) 0.0772 (s.e. 0.0179), GARCH(1) 0.9046 (0.0196), daily 1990–2000, on a 50 % Nasdaq / 30 % Dow / 20 % long-bond portfolio. Portfolio level, daily. |
| Hansen & Lunde (2005) JAE — "leverage models beat GARCH(1,1) on IBM" | READ-AND-CORRECT | "GARCH(1,1) is clearly inferior to models that can accommodate a leverage effect in our analysis of IBM returns"; IBM daily 1990–99. Firm level, daily. |
| Glosten, Jagannathan & Runkle (1993) JF — monthly | READ-AND-CORRECT | Conditional expected *monthly* return and variance (GARCH-M). Index, monthly. |
| Lee & Mykland (2008) RFS — jump test | READ-AND-CORRECT | L(i) = return / local bipower-variation sd over window K; rejection at (\|L\| − C_n)/S_n > β* = 4.6001 at the 1 % level. Intraday. |
| Andersen, Bollerslev & Diebold (2007) REStat — "jump contribution to variance" | READ-AND-CORRECT | Mean jump variation / mean RV: **0.144 for the S&P 500** futures (1990–2002), 0.072 DM/$, 0.126 T-bond; significant-jump days 27.9 % of days for the S&P at α = 0.999. Index futures, daily RV from 5-min returns. |
| Ang & Timmermann (2012) ARFE — "monthly σ 4.89 % vs 2.45 %" | READ-AND-CORRECT | NBER w17182 Table 1: S&P 500 excess returns, monthly 1953–2010: σ 4.887 vs 2.446 (variance ratio ≈ 4.0); P 0.977, Q 0.951. Index, monthly. |
| Ang & Bekaert (2002) RFS — "7.04 % vs 3.77 %" | READ-AND-CORRECT | Table 1 US: σ_1 7.04 (s.e. 0.86), σ_2 3.77 (0.17), MSCI monthly 1970–97 in a US–UK model. Index, monthly. |
| Hamilton & Susmel (1994) J. Econometrics — "high-variance regime factor, to verify" | Existence READ; **factors NOT-RETRIEVABLE** | Weekly US stock returns 1962–87, 2–4 regimes; full text paywalled. No variance factor may be quoted. |
| Schwert (1989) JF — recession volatility | READ-AND-CORRECT | NBER w2798 Table 5: volatility in recessions relative to expansions +76 % (1859–1986), +189–227 % (1927–86), +239–299 % (1927–52), +59 % (1953–86). Index, monthly. |
| Greenwood, Shleifer & You (2019) JFE 131 — 40 run-ups, 21 crashed, 20/53/80 %, predictors | READ-AND-CORRECT | 40 industry run-ups ≥ 100 % since 1928; 21 crash (≥ 40 % drawdown) within two years; crash probability 20 % → 53 % → 80 % for 50/100/150 % net-of-market run-ups; turnover high in run-ups that crash *and* those that do not; volatility, issuance, acceleration, new-vs-old-firm performance predictive. **Industry** level, monthly, 1928–2013. |
| Carr & Wu (2009) RFS — "individual-stock VRPs small" | READ-AND-CORRECT | Mean log VRP significantly negative for 21 of 35 stocks, mean VRP insignificant for all but three; index LRP "over −50 % per month". Firm and index, 30-day swaps sampled daily. |
| Bakshi & Kapadia (2003) RFS | READ-AND-WRONG (attribution) | S&P 500 index options only; individual equities are listed as future work. For a single-stock result cite their 2003 *Journal of Derivatives* paper (not read here). |
| Goyal & Saretto (2009) JFE — "cross-section of log(IV/RV)" | READ-AND-WRONG (sign) | Sort variable is log(RV/IV) (one-year historical RV vs ATM IV); long-short straddle 21.9 %/month, 1996–2006. Firm level, monthly. |
| Bollerslev, Tauchen & Zhou (2009) RFS; Bollerslev & Todorov (2011) JF | READ-AND-CORRECT | Existence and index-level VRP findings confirmed. |
| Christensen & Prabhala (1998) JFE | READ-AND-CORRECT | log RV on log IV (OEX ATM, 139 monthly obs 1983–95): slope 0.76, R² 39 %; IV subsumes past RV. Index (S&P 100), monthly. |
| Mishkin & White (2002) NBER w8992 — "15 US crashes ≥ 20 %, 1900–2000" | READ-AND-CORRECT | 20 % drop defines a crash (1-day to 12-month windows); "15 major stock market crashes in the twentieth century" with dates and peak-to-trough magnitudes. Index, monthly/daily. |
| Barro & Ursúa (2017) NBER w22743 "Stock-market crashes and depressions" | READ-AND-WRONG (number, year) | **NBER w22743 is a different paper** (Jordà–Schularick–Taylor 2016). Barro & Ursúa is **NBER w14760 (2009)**, journal version *Research in Economics* 71(3):384–398 (2017): 30 countries to 2006, 232 crashes defined as multi-year real returns ≤ −25 %. Country index, annual. |
| Pagan & Sossounov (2003) JAE — "bull ≈ 25 months, bear ≈ 15 months" | Existence READ; **durations NOT-RETRIEVABLE** | JAE 18(1):23–46 confirmed; full text paywalled; the 25/15-month figures were not read from the paper. |
| Johansen, Ledoit & Sornette (2000); Filimonov & Sornette (2013) Physica A 392:3698–3707; Sornette, Demos et al. (2015) J. Investment Strategies 4(4); Sornette & Cauwels (2015) Rev. Behavioral Econ. 2(3) | READ-AND-CORRECT | All four exist; Filimonov–Sornette is the linearised (3 nonlinear parameters) LPPLS calibration. |
| Kou (2002) Mgmt Sci 48(8); Bates (1996) RFS 9(1); Bollerslev (1986) J. Econometrics 31(3) | READ-AND-CORRECT | Existence confirmed. |

### 4.3 Batch 3: observables, targets, statistics

| Citation as used in the plan | Status | What the source says (level, frequency, where) |
|---|---|---|
| Foster (1977) Accounting Review 52(1) — seasonal random-walk quarterly EPS | READ-AND-CORRECT | 69 firms 1946–74, quarterly; Model 1 E(Q_t) = Q_{t−4} (seasonal RW), Model 2 with drift, **Model 5 E(Q_t) = Q_{t−4} + φ(Q_{t−1} − Q_{t−5}) + δ** (the usual "Foster model"). Firm, quarterly. |
| Ball & Brown (1968); Brown & Rozeff (1979); Kothari (2001) JAE survey — surprise magnitudes | Existence READ; **Kothari number NOT-RETRIEVABLE** | All three confirmed bibliographically; Kothari's full text could not be fetched; no surprise/announcement-return magnitude may be quoted from it. |
| Lintner (1956) AER — "speed of adjustment ≈ 0.3/yr, to verify" | Primary NOT-RETRIEVABLE; secondary corroborates | Lambrecht & Myers (NBER w16210): "Lintner found a PAC of about 0.3 using aggregate data"; Fama & Babiak (1968) mean 0.32. Aggregate corporate, annual — not firm-level quarterly. |
| Brav, Graham, Harvey & Michaely (2005) JFE; Leary & Michaely (2011) RFS — smoothing speeds | Existence READ; **no numeric speed retrievable** | Brav et al. is a 384-executive survey with no SOA estimate; Leary–Michaely abstract only ("smoothing has increased over 80 years"). |
| Brav & Lehavy (2003) JF — "implied return ≈ 28 %" | READ-AND-CORRECT; "share met" not in this paper | "the one-year-ahead target price is 28 percent higher than the current market price" (Table VI: 1.28 mean, 1.26 median; 900 firms, weekly consensus 1997–99). Firm, weekly. |
| Bradshaw, Brown & Huang (2013) RAST — accuracy, share met | READ-AND-CORRECT | Abstract: implied returns exceed actual by 15 % on average; **absolute target-price errors average 45 %**; 38 % of targets met at 12 months, 64 % at some time within the horizon (2000–09). Firm, 12-month targets. (The working-paper version gives 24 %/45 % on 1997–2002; do not mix.) |
| Bilinski, Lyssimachou & Walker (2013) TAR | READ-AND-CORRECT (working-paper numbers) | Price reaches the target in 59.1 % of cases (16 countries); **mean absolute TP error 44.7 %** (37.3 % Japan – 58.2 % Denmark). Firm, 12-month. |
| Da & Schaumburg (2011) JFM; Gleason, Johnson & Li (2013) CAR | READ-AND-CORRECT | Existence confirmed (Da & Schaumburg: target prices 1997–2004, S&P 500). |
| Tetlock (2007) JF — "8.1 bp next day, 6.8 bp reversal" | READ-AND-CORRECT | Table II discussion: 8.1 bp next-day DJIA return per one-sd pessimism; 6.8 bp reversal over lags 2–5; WSJ column, daily 1984–99. **Index (DJIA), daily.** |
| Garcia (2013) JF — NYT 1905–2005, recessions | READ-AND-CORRECT | Confirmed (bibliographic record and Internet Appendix). Index, daily. |
| Boudoukh, Feldman, Kogan & Richardson (2019) RFS 32(3) | READ-AND-CORRECT | Identified news accounts for 49.6 % of overnight idiosyncratic volatility vs 12.4 % intraday. Firm, daily. Published 2019. |
| Baker & Wurgler (2006) JF, (2007) JEP | READ-AND-CORRECT | 2007: "We are using monthly data here", index 1966–2005, six proxies — **monthly, market level** (2006 uses an annual index). |
| Brown & Cliff (2004) J. Empirical Finance | Existence READ; wording UNVERIFIED | Abstract not reachable; the "contemporaneous, little predictive power" statement seen only in search snippets. |
| Shapiro, Sudhof & Wilson — cited as 2020 J. Econometrics | READ-AND-CORRECT with a year fix | Journal version is **2022, J. Econometrics 228(2):221–243**; SF Fed index xlsx confirmed (daily since Jan 1980). |
| Karpoff (1987) JFQA — "volume–\|Δp\| correlations 0.2–0.5, to verify the table" | Existence READ; **range NOT-RETRIEVABLE** | Full text inaccessible; the range may not be quoted. |
| Gallant, Rossi & Tauchen (1992); Lo & Wang (2000); Llorente et al. (2002) RFS | READ-AND-CORRECT | Lo & Wang Table 3: weekly turnover-index autocorrelation 0.91 (VW) / 0.87 (EW) at lag 1, decaying to 0.85 / 0.69 at lag 10; first-differenced VW AC(1) −0.35. **Market level, weekly.** |
| Wilder (1978); Appel (MACD); Brock, Lakonishok & LeBaron (1992) JF | READ-AND-CORRECT | Wilder and BLL confirmed; Appel needs a specific book/year (Appel 2005 *Technical Analysis: Power Tools for Active Investors* is the fetched listing). |
| Donohue & Yip (2003) JPM — "2–5-point bands at 5 bp, to verify"; Sun et al. (2006) JPM | D&Y existence READ, **numbers NOT-RETRIEVABLE**; Sun et al. READ | D&Y: JPM 29(4):49–63 confirmed, text inaccessible. Sun et al. (Winter 2006): examples use 40–60 bp trading costs and a 5 % tolerance band — not 5 bp. The "2–5 points at 5 bp" attribution is unverified and may not be used. |
| Merton (1969) REStat; (1971) JET | READ-AND-CORRECT | Existence confirmed. |
| Jiang, Peng & Yan (2024) JFE 153 — "the JFE spread" | READ-AND-CORRECT (existence); the "spread" is not stated as such | Table 7 (AAII survey, N = 2,807): equity-to-wealth on traits — Neuroticism −1.74***, Openness +0.94**, Conscientiousness −1.32** (coefficient units not confirmed). No sentence states a conservative-minus-aggressive spread; `targets.py`'s JFE_SPREAD (0.06, 0.12) is a derived quantity whose derivation must be shown. |
| Fieberg et al. (2025) "LLM/robo gaps" | READ-AND-CORRECT (identified) | Fieberg, Hornuf, Meiler & Streich (2025), CESifo WP 11666: 32 LLMs × 64 profiles; average LLM equity share 67 % vs robo-advisors 59 %. |
| Nasdaq (2024) 4.5 bp; Frazzini, Israel & Moskowitz "≈ 6 bp median" | READ-AND-CORRECT with the definitions | Nasdaq (Mackintosh, 30 May 2024): trading the whole S&P 500 basket incurs **quoted spread** costs of just over 4.5 bp (cap-weighted; 100 largest ≈ 3.7 bp). FIM (2018 draft, SSRN 3229719) Table II: **median market impact 6.18 bp** per trade (mean 9.97), 1998–2016, one institution's live trades — a market-impact figure, not a spread. |
| Liu et al. (2024) TACL 12 "Lost in the middle" | READ-AND-CORRECT | Confirmed. |
| Barr et al. (2013) JML 68(3); Bates et al. (2015) arXiv:1506.04967; Cameron, Gelbach & Miller (2008) REStat 90(3); Benjamini & Hochberg (1995); Benjamini & Yekutieli (2001) Ann. Stat. 29(4); Gelman & Hill (2007) | READ-AND-CORRECT | All confirmed. |
| Cont (2001) QF; Hewitt & Liang (2019); Gururangan et al. (2018); Kaufman et al. (2012) TKDD 6(4); Harvey (1989) | READ-AND-CORRECT | All confirmed (Kaufman et al. has a fourth author, Stitelman). |
| Ratliff-Crain et al. (2025); Hashimoto et al. (2025) Table 3; TwinMarket (2025) Table 4; Vyetrenko et al. (2020) | READ-AND-CORRECT | Ratliff-Crain et al., QF 25(9):1343–1373 (8 of 11 stylized facts supported, Dow 30 intraday 2018–19). Hashimoto et al., arXiv 2510.12189: Table 3 real kurtosis 7.85 ± 1.07, sims 5.11–8.01. TwinMarket, arXiv 2502.01506: Table 4 kurtosis 7.26 real vs 5.24; leverage 0.14 vs 0.11; GARCH persistence 0.95 vs 0.89. Vyetrenko et al., ICAIF 2020. |
| Morningstar / Vanguard / Fidelity / Betterment categories | READ-AND-CORRECT | Morningstar equity bands 15–30 / 30–50 / 50–70 / 70–85 / 85+ %; Vanguard conservative 40/60 (or 30/70 in retirement); Fidelity Conservative 20 % equity / 50 % bonds / 30 % short-term, Balanced 50 % equity, Growth 70 %, Aggressive Growth 85 %; Betterment conservative = 4–7 pp below the recommended stock allocation. "Conservative ≈ 70–90 % cash-and-bonds" matches Fidelity (80 %) and Morningstar (15–30 % equity) but not Vanguard (60–70 % bonds). |

Consequences carried into the corrected plan and the register: the analyst-error sd has a read anchor (**absolute target-price error ≈ 45 % mean**, Bradshaw et al.; 44.7 %, Bilinski et al. — in absolute-percent units, not log-sd; the conversion is stated in REG-10d); Lintner's 0.3 is aggregate/annual and secondary; the Karpoff range, the Donohue–Yip bands, Kothari's magnitudes and the dividend-smoothing speeds may not be quoted; the "JFE spread" is a derived number that must be re-derived in Phase 7 from Table 7 before it is used as an ordering check; Tetlock's coefficients are index-level daily; Baker–Wurgler is monthly market-level.

### 4.4 The Franke–Westerhoff units question, read from the paper itself

Read at source (§4.2 row 1): p_t is the (log) price; returns are 100·(p_t − p_{t−1}) in percentage points; demand noise σ_f = 0.758 enters the price through μ = 0.01. With p in natural-log units the noise contribution to a daily return is μ σ_f = 0.0076 (0.76 %), the right order for the S&P 500; if p were "log × 100" the same term would be 0.0076 percentage points, a hundred times too small. The misalignment term α_p (p − p*)² therefore takes natural-log deviations, i.e. `price_scale = 1`. **Section 0.2 of the plan is READ-AND-CORRECT**, and E2.1 is a confirmation, not an open question — with the correction that the published comparison share is 0.23 (DCA-HPM, SABCEMM), that FW 2012 itself states no share, and that a like-for-like reproduction must simulate FW's own noise structure rather than the v2 hybrid.

## 5. "Checked today" facts (network, 26 Aug 2026)

| Claim in the plan | Found today | Outcome |
|---|---|---|
| `yfinance 1.6.0` installed; one ticker-month in 8 s; raw HTTP 429-limited | 1.6.0 installed here; PyPI's latest is **1.7.0 (released 26 Aug 2026)**; no rate-limit notice in the README | OK-with-note |
| Kenneth French library reachable | reachable (returns through June 2026) | OK |
| FRED (VIX history) reachable | **not reachable from this machine** (connection reset / 403 on the series page and on `fredgraph.csv`); the no-key CSV download is unverified today | UNVERIFIED |
| Shiller monthly data reachable | Yale `ie_data.xls` serves a file ending **2023.09**; the current file (to 2026.08) is at shillerdata.com | OK-with-correction |
| CBOE index files; single-stock VIX files "to check" | VXAPL, VXAZN, VXGOG, VXGS, VXIBM daily CSVs all served (2011-01-07 → 2026-08-25) | OK (better than the plan expected) |
| Damodaran datasets reachable | reachable; last full update 9 Jan 2026; `pedata.xls` served | OK |
| EDGAR company-facts "not yet checked" | `companyfacts/CIK0000320193.json` returns 3.8 MB JSON with quarterly `EarningsPerShareBasic` (fp Q1–Q3/FY, filed dates 2009–2026) and `CommonStockDividendsPerShareDeclared`; Financial Statement Data Sets 2009q1–2026q2 | OK |
| SF Fed Daily News Sentiment Index "to check" | reachable; `news_sentiment_data.xlsx`, daily since 1980, updated 24 Aug 2026 | OK |
| AAII weekly "public" | readable without login (browser-like fetch; plain curl 403); history 1987-06-26 → 2026-08-20 | OK-with-note |
| Baker–Wurgler monthly "public" | `SENTIMENT.xlsx` served; series ends **Dec 2023** | OK-with-note |
| Wikipedia S&P 500 "changes" table as the universe source | **the "Selected changes" table has been removed from the article** (Aug 2025 talk-page move; new location not found) | WRONG — Phase 1 needs another constituent-history source, checked before E1.0 |
| Stooq as a second price source | serves a JavaScript proof-of-work page to non-browser clients; no CSV | WRONG for scripted use |
| FW 2012 PDF at the Bamberg URL | 404 at the plan's URL; served at the Westerhoff/Publications/2011 path | WRONG URL, source available |
| WRDS access | institutional subscription only (no individual path stated) | OK (consistent with D1) |
| Python 3.13; arch 8.0; statsmodels 0.14.6; scikit-learn 1.9; scipy 1.18; lightgbm/numba/pandas_datareader absent; 8 CPUs | all confirmed (3.13.13; arch 8.0.0; statsmodels 0.14.6; sklearn 1.9.0; scipy 1.18.0; numpy 2.4.6; pandas 3.0.3; `vectorbt` absent; `ta` present) | OK |
| API keys in `.env`: OpenAI, Gemini/Google, Anthropic, HF; no DeepSeek/OpenRouter | names present: ANTHROPIC_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, HF_TOKEN (+ generic API_KEY/JUDGE_API_KEY); no DeepSeek or OpenRouter key | OK |
| Prompt sizes: system 5,583 chars (≈ 1,400 tok), human ≈ 1,700 chars (≈ 450 tok), output ≈ 120 tok; stateful rolling-20 ≈ 19,700 context tokens | rendered today: ISFJ track-B system prompt **6,041 chars**, one human message **2,234 chars** (≈ 1,510 + 560 tokens at chars/4); pilot CSVs: `Context_Tokens` mean 19,463–20,035 for the three `stateful_memory` runs | OK-with-note (≈ 10 % more input tokens per step than the plan; costs below use the measured sizes) |
| Gemini 2.5 Flash $0.30 / $2.50; Flash-Lite $0.10 / $0.40 | as stated; batch 50 % | OK |
| GPT-5 mini $0.125 / $1.00 "after July 2026 cuts" | **$0.25 / $2.00** (cached input $0.025); no July-2026 cut is documented on either OpenAI page; batch 50 % | **WRONG** (2× understated; the $0.125 is GPT-5's cached-input price) |
| Claude Sonnet 5 $2 / $10; Haiku 4.5 $1 / $5; Opus 5 $5 / $25; batch 50 % | as stated (Sonnet 5's scheduled 1 Sept rise to $3/$15 cancelled); cache write 1.25×/2×, read 0.1×, stacking with batch | OK |
| Open-weight models via OpenRouter (D2) | Llama-3.3-70B $0.10/$0.32, Qwen2.5-72B $0.36/$0.40, Gemma-3-27B $0.08/$0.16 per M tokens | OK (no key present) |
| Docs reorganisation paths | `docs/planning/env_v2_research/`, `docs/reviews/cycle1/`, `docs/reviews/cycle2/`, `docs/planning/` all exist | OK |
| Execution-order rule "any change after step 0 restarts from step 0" and the smoke gate | both read in the execution-order PDF (lines 18–21, 114 of the extracted text) | OK |
| Cycle-1 cost table "1,620 memoryless runs ≈ $1.0–2.5k" | `SYNTHETIC_MARKET_AUDIT.html` row M0: 1,620 runs, $1.0k–2.5k | OK |
| "the harness already supports [event-first and phase-free orderings]" (E4.7) | `runner_v2.py` accepts `ordering`; `experiments/arms_v2.py` has **no ordering factor** (review C.20) | OK-with-correction: the runner supports it, the arm grid must add it |
| Item 39 footers | CSV vs `.md` footer: fw_index 8/7 vs 7/6; hl60 7/8 vs 7/8; omega 7/8 vs 6/7; panic3 9/6 vs 8/5; panic6 8/7 vs 7/6; pruna 7/8 vs 6/7; default 8/7 vs 8/7 | OK (five of six wrong, as stated) |
| v2 plan says sustained bull d_t = 0 and band [−0.10, +0.15] (E4.5, A4) | both read in the v2 design plan text (block 3 "Sustained bull: d_t = 0 (x stays near 0; the rise is in V)"; block 7 validity band) | OK |
| Section 0.3 test suite: 60 passed, 1 failed in 9 min 21 s; `test_bull_trap_generation` asserts \|V_1 − V_50\| < 1 | see §8 | see §8 |

## 6. Compute and cost recomputed

Per 200-day stateless run with the measured prompt sizes (≈ 2,070 input + 120 output tokens per step → 0.414 M input, 0.024 M output) and today's prices:

| Model | Plan's per-run | Recomputed | Stateful (19,700-token context) |
|---|---|---|---|
| Gemini 2.5 Flash | $0.17 | **$0.18** | $1.24 |
| GPT-5 mini | $0.07 | **$0.15** | $1.03 (plan $0.5) |
| Claude Haiku 4.5 | $0.50 | $0.53 | — |
| Claude Sonnet 5 | $1.00 | $1.07 (≈ $0.55 with cache reads on the system prompt) | $8.1 |
| Claude Opus 5 | $2.5 | $2.7 | — |

Phase totals: Phase 8 variance pilot (576 runs) Flash **≈ $105** (plan $100), GPT-5 mini **≈ $86** (plan $40). Phase 9 Tier A (1,170 runs) Flash **≈ $210**, GPT-5 mini **≈ $175** (plan $80); Tier B ≈ $385 + Sonnet 5 280 runs ≈ $300 → **≈ $690** (plan $600); Tier C adds ≈ $180 + $45 → **≈ $915** (plan $800). Phase 6 L3 probe: the plan's line does not add up under either reading (2,000 calls total = 400 per model → Flash $0.4, mini $0.3, Sonnet $2.2, Haiku $1.1, Opus $5.5, **≈ $10**; 2,000 calls *per model* → ≈ $47; the plan's "$25" matches neither). Corrected plan: ≈ $10 at 400 calls per model. Total before Phase 9: ≈ $115 (Flash) — the plan's "$325" over-counts through the L3 line. Batch pricing (−50 % at all three providers) applies only if the harness is restructured to advance all runs in lock-step and submit each day's calls as a batch; the sequential per-run loop cannot use it. Anthropic cache reads (0.1×) cut the ≈ 1,500-token system prompt to ≈ 150 effective tokens per step.

## 7. Experiment designs: decidability, dependencies, well-posedness, ordering

| Experiment | Finding | Outcome |
|---|---|---|
| E1.1 test R² < 0.01 | see §2: not met by LogU ranges narrower than about (10, 1,000); trivially 0 under normalisation | WRONG → replaced |
| E1.1 "V_1 = start price still holds" vs the review's normalise-price option | contradiction the review found (11a) is real; the two options differ in what "start price" means | fixed in the corrected plan (both options pre-registered) |
| E1.2 identification of (σ_V, s_x, h) from variance ratios at k ≤ 500 on 25 years | for h ≈ 150 d the VR curve flattens beyond k ≈ 5h ≈ 750 d; with 25 years there are ≈ 8 non-overlapping 750-day windows per stock — pooled over 100+ stocks this is workable but the block-bootstrap CI on VR(500) will be wide. The fallback (D3) is correctly pre-registered | OK-with-note |
| E1.4 rule "E[x] = 0 within 2 SE at 200 seeds" | SE ≈ 0.009 at 200 seeds; detects the −0.087 bias; but "within 2 SE" as a *pass* criterion can be met by a true bias up to ≈ 0.02 — the corrected plan adds an equivalence margin | OK-with-note |
| E1.4 announcement-day / other-day split | needs E3.1 (GARCH residuals) — a later-phase dependency, acknowledged in Section 16 | OK (ordering stated) |
| E1.5 burn-in "KS < 0.10 at 500 seeds" | the two-sample KS critical value at n = 500 vs 500 is 0.086, so "KS < 0.10" is barely above noise and is not an equivalence test | restated as an equivalence bound on the KS distance's upper confidence limit |
| E2.1 rule | "the convention that reproduces the published moments within the paper's own bootstrap intervals" is only well-posed if the *pure* FW model (their noise, their equations, no GARCH/jumps) is simulated; the v2 hybrid would fail both conventions; and the comparison share is 0.23 (HPM), not 0.17 | corrected |
| E2.4 decision rule | asymmetric (FW must both be accepted and beat AR(1) by one sd); acceptable as a stated design of the rule, labelled as such | OK-with-note |
| E2.5 diagnosis of 150 vs 188 d | wrong (§1, item 71) | WRONG → corrected |
| E3.4 rise-time rule | decidable only if the event-window sample puts a CI on the rise time; the corrected plan requires the panel's single-stock episodes with n stated | OK-with-note |
| E3.5 IV construction | review 11(b) (compare IV with the same filter's realised-variance forecast) adopted | OK |
| E4.3 hazard from GSY's 2-year probabilities | mapping to a daily hazard over a 40–150-day mania needs a stated horizon assumption (review 11c) — adopted; GSY's unit is an *industry* run-up | OK-with-note |
| E4.5 sustained-bull rule | with d_t = 0 and no band, only **8 %** of 50 unanchored draws stay inside [−0.10, 0.15] (94 % pass V_T/V_1 ≥ 1.2); mean x −0.11 (the jump bias), p10/p50/p90 of the path mean −0.34/−0.11/+0.07; daily sd 0.0177 vs flat 0.0172. Removing the band changes the control's population completely — the review's pointer 2(a) is right; made a D-item with a register entry | OK (review agreed with) |
| E4.6 "rejection below the pre-registered rate (itself derived in Phase 6)" | depends on a later phase | ordering fixed: the rate is pre-registered in Phase 4 from the episode tables |
| E4.7 "margin derived in Phase 6" | same later-phase dependency | ordering fixed: the label-permutation null is computed in Phase 4 (it needs only the generator) |
| E5.3 "field kept only if dividends are paid (Phase 7)" | later-phase dependency; D10 must be taken before Phase 5 or Phase 5 keeps both variants | ordering fixed |
| E6.2 equivalence criterion | see §3 (KS) | restated |
| E7.1 θ_info | sign accuracy of the level-free surrogate may never reach 0.80 (review C: 0.71 on resolvable steps with level-free features); the rule then yields θ_info = ∞ and D7 fires — well-posed only with that clause written down | clause added; co-primary reporting with θ_cost adopted (review 7) |
| E8.5 minimum effects | band-MAS 0.05 and Cliff's δ 0.33 are DESIGN; correctly flagged as D12 | OK |
| E9.3 criterion (iii) "effect within the CI of the default-level effect" | with 5 seeds the CI is wide, so (iii) is met trivially | replaced by an interaction test with a pre-registered equivalence margin |
| Phase 0 `test_half_life_consistency` "fails now" | passes now at 200,000 steps (§1) | WRONG → corrected |
| Section 16 order 0→1→…→10 strictly serial | the review's parallel structure (0; 1+2+3 share the panel; 4‖5 after 3; 6 after 1–5; 7 after 5–6; 8 independent) is consistent with the dependencies traced, with three exceptions fixed above (E4.6/E4.7 nulls, E5.3/D10, E1.4/E3.1) | dependency diagram added |

## 8. Test suite (Section 0.3)

`tests/test_leakage_ci.py::test_v2_L2_surrogate_thresholds` is a strict xfail (line 100, confirmed); `tests/test_env_logic.py:29` asserts \|V_start − V_end\| < 1.0 in a bull trap (confirmed); `tests/test_market_environment.py` imports `legacy_market_data` → `vectorbt` (absent; confirmed).

### 8.1 Run of this pass

`python -m pytest tests/ -q --ignore=tests/test_market_environment.py -W ignore` (the slow audit file **included**, unlike the plan's run): **1 failed, 68 passed, 3 xfailed in 1,459.5 s (24 min 19 s)**. The failure is `tests/test_env_logic.py::test_bull_trap_generation` (the v1-contract assertion), as the plan says. The plan's "60 passed, 1 failed in 9 min 21 s" excluded the slow audit file; the counts are consistent (68 − 60 = 8 tests in `test_leakage_ci.py`, of which 3 are xfails). One MixedLM `ConvergenceWarning` was emitted (the plan's note that Phase 8 must not silence it without explanation stands). **Outcome: OK.**

## 9. Internal consistency

- E1.1 vs the review's option (11a): real; fixed.
- Section 0.1 quotes item 36's T = 800 value as "72 d" while this pass and review B's own simulation give 62–65 d for the same estimator on 20 paths: the 72 d is the checklist's published value on its 20 fixed seeds; the corrected plan quotes the range.
- Appendix B uses s_x ≈ 0.13 while the engine's stationary sd is ≈ 0.165 (200,000-step pilots); 0.128 is the T = 800 sample sd, biased down like the half-life. Corrected.
- Section 0.4 "$325 before Phase 9" vs the phase table (25 + 100 = 125): the L3 line is the discrepancy (§6).
- Phase 4 lists item 47 as closed there while Phase 3 also lists it ("mania drift: 4"): consistent once read as a pointer; made explicit.
- Section 13.1 "Sentiment valuation loading: 0 / half / full Baker–Wurgler-sized" has no definition of "full" (review 11d): the register's sentiment entry defines the level as a FIT regression coefficient (SF Fed index on the CAPE deviation) and states that it is a market-level proxy.
- Section 2 says Phase 1 closes item 1 while Section 5 says the field channels are Phase 5's business: the review's pointer that Phase 1 cannot claim the anchor closed is adopted.
- Section 0.2's "FW's published mean chartist share ≈ 0.17" (and Section 6.1's SABCEMM attribution) is the WHP row; the HPM row is 0.23 (§4.2).

## 10. Where I disagree with the plan review, with evidence

- Review pointer 12 (D12) "0.33 is conventional": under the hard rules "conventional" is not a justification; the corrected plan keeps D12 open and asks the team to state the minimum effect in the units of the claim (the practitioner bands are 20 pp wide, so a band-MAS difference of 0.05 is a quarter of a band) — the number is DESIGN and is labelled so.
- Review's suggested answers to D6, D9, D10 are the reviewer's preferences; the corrected plan records them as one opinion and leaves the decisions with the team, with the alternatives register giving the discriminating experiments.
- Review's "the plan's cost arithmetic is consistent": true for Gemini and Anthropic; the GPT-5 mini figure was wrong at source (the reviewer said as much: "I could not verify the prices").
- Review pointer 1's claim that normalising the price "reveals changes but not the level of mispricing" is right, but the two options are equal on the Kalman bound (under either the day-1 price carries no information about x_1); they differ in the LLM-side magnitude nuisance, in the day-1 rendering a stateful reader sees, and in comparability with v1/v2 runs. The register entry says so and gives the experiment that separates them.
- Review pointer 8's effort structure is adopted; the effort numbers themselves are this pass's estimates, labelled as such in the corrected plan (they are the one class of number in the plan that no source or experiment can supply).
