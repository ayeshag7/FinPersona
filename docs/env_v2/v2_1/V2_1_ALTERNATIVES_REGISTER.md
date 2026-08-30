# Alternatives register for the v2 → v2.1 plan

Date: 26–27 August 2026 (third, independent pass). Purpose: wherever `V2_1_IMPROVEMENT_PLAN.md` picks one approach that the evidence does not yet settle, this register replaces the pick with two or three concrete alternatives and the experiment that decides between them, so that the team decides from results. **This register does not choose.** Where an option is clearly dominated by evidence gathered in this pass, it says so and why, but the option stays on record.

Conventions. Every entry has the same five parts: the question; the options (mechanism, assumptions, cost, literature *read* in this pass — LOG §4 gives the status of every citation; nothing here is recalled); the discriminating experiment (seeds / horizon / statistic / decision rule / power; and what is reported if no option wins); what each option does downstream. Costs: effort is an ESTIMATE in person-days (see the corrected plan, Section 15); compute is generator time on 8 cores at 0.17 s per 200-day path; API costs use the prices read on 26 Aug 2026 (LOG §5–6). Power statements use Appendix A of the corrected plan; where power cannot be computed until the Phase-8 variance pilot exists, the entry says so. "Level-free attacker" = the review-C GBT on returns, log P/SMA20, log P/SMA50, RSI, MACD/P and lags, with no level feature.

Cross-references: LOG = `reviews/V2_1_PLAN_VERIFICATION_LOG.md`; PLAN = `V2_1_IMPROVEMENT_PLAN.md`; D-n = team decisions in PLAN Section 17.

---

## Summary table

| # | Question | Options | Discriminating experiment (statistic → rule) | Cost | Phase |
|---|---|---|---|---|---|
| 1 | Start-price answer key | A randomise level; B normalise price; C both; D no level rendered | level attacker vs level-free attacker R²(x) at 500 seeds; then a 60-run LLM magnitude test → adopt the option whose attacker gap is inside the CI *and* whose LLM magnitude effect is inside the equivalence margin | 2 pd; 5 min; ≈ $11 | 1 (LLM part 9) |
| 2 | Value process | A smooth σ_V (v2); B fitted larger σ_V; C two environments as a factor | E1.2 three-estimator fit → FIT if intervals overlap; else Kalman-bound + audit tables for A and B and the team's D3 | 4 pd; 40 min | 1 |
| 3 | Jumps | A in V at announcement dates; B mean-zero in x; C both | announcement/other-day kurtosis split on the panel vs the generator (KS upper limit) and E[x] equivalence → closest split wins | 2 pd; 20 min | 1 + 3 |
| 4 | Mispricing engine | A FW (units fixed); B AR(1)+GARCH; C FW+ (GBM fundamental) / DCA-WHP | SMM acceptance + held-out moment prediction + checklist/leakage equivalence → asymmetric rule; ties to B | 10 pd; 4 h | 2 |
| 5 | Persistence estimation | A variance ratios; B P/V̂ AR(1) with Andrews' correction; C SMM persistence moments | simulation-recovery study on synthetic panels with known h; then the three on data → adopt the estimator with the best recovery whose data CI contains the others' point estimates; else report all three | 4 pd; 1 h | 2 |
| 6 | Regime volatility and IV | A whole-variance scaling; B ω ramp; C fitted two-regime model; IV from a returns-only filter under each | rise/decay time of realised variance in single-stock episodes vs the three mechanisms (CI inclusion); IV onset audit against the same filter's RV forecast | 4 pd; 30 min | 3 |
| 7 | Sustained-bull control | A same process, no band; B band on V only; C anchored x (v2); D rendered-matched control | discrimination audit at chance + baseline-level test ("adherence moves, regret does not") + published selection statistics → the definition meeting both, given D14's purpose | 4 pd; 30 min | 4 |
| 8 | Event dynamics | A tracking gain; B shifted p* with regime pull; C scripted drift + rejection; D unscripted regime switching | script share of event-phase Δx variance, depth/duration inside the episode P10–P90, rejection ≤ pre-registered rate → lowest script share meeting both | 8 pd; 1 h | 4 |
| 9 | Calendar | A random calendar dates; B no date; C "Day-N" disclosed arm; ordering mix for time/phase separability | day-only phase classifier vs permutation null (generator); LLM phase-classifier arm (≈ 90 runs) → rendering whose classifier is at chance; ordering mix set from the null | 2 pd; 30 min; ≈ $16 | 4 (LLM part 9) |
| 10a | P/E multiple | A fixed draw, FIT-wide; B time-varying log-AR(1); C tied to a fitted cross-section | per-field-group L2 selectivity and L1 inversion share against the level-free control → lowest selectivity meeting the checklist's P/E reference band | 3 pd; 1 h | 5 |
| 10b | Sentiment | A returns-only; B returns + slow valuation link (FIT size); C survey-style AR(1) | same selectivity audit + item-12 FIT comparison with the SF Fed index → D15 | 3 pd; 1 h | 5 |
| 10c | Volume | A \|r\| only; B \|r\| + run-up turnover ratio | onset-detection AUC vs price-derived AUC; run-up turnover ratio FIT from the panel | 2 pd; 30 min | 5 |
| 10d | Analyst estimate | A LIT sd with sensitivity; B drop; C lagged smoothed price proxy | L2/L5 selectivity per option + LLM grid effect (Phase 9) → the option whose selectivity is inside the null margin and whose LLM effect is not level-dependent | 2 pd; 1 h; Phase-9 cells | 5 + 9 |
| 11 | Resolvability θ | A information; B cost; C within-run variance; D co-primary | all headline metrics re-scored at each; Phase-9 robustness table by θ → if conclusions agree, co-primary reporting; else D7 | 1 pd; 10 min | 7 |
| 12 | Regret metric | A band-violation + directional decomposition; B per-window scoring; C alternative ceiling/floor | construct-monotonicity table (E7.8) and switch counts → the scoring under which the scripted-policy sweep is monotone and the correlation with band-MAS is below the pre-registered ceiling | 3 pd; 10 min | 7 |
| 13 | Target bands | A practitioner categories; B utility-consistent from (μ, σ); C both as a factor | Merton table on the fitted (μ, σ); band-MAS ordering of the trivial policies under each; Phase-9 interaction → D9 | 2 pd; minutes | 7 (+9) |
| 14 | Checklist criteria and seeds/horizon | A pre-registered numeric thresholds; B KS-equivalence to real 200-day windows; C percentile bands; T = 200 only vs T = 200 + longer horizons | per-item size/power on synthetic known-answer panels; concordance of pass/fail across A/B/C → items where A and B/C disagree are reported under both; horizon policy fixed as T = 200 for the criterion | 5 pd; 30 min | 6 |
| 15 | Data | A free substitutes now; B pause for WRDS; C hybrid (fit now, re-fit later) | survivorship quantified on the retrievable share of the historical constituent list and the survivor-vs-literature gap for tails/drawdowns → C if the gap exceeds the fit's own CI on any Phase-3/4/6 parameter; A otherwise; B only if WRDS arrives before Phase 1 ends | 1 pd | 1 (D1) |
| 16 | LLM sensitivity grid | which six; tiers A/B/C; roster; stateful arms | rank generator parameters by their effect on the level-free oracle regret and scripted-policy band-MAS; ICC from the variance pilot decides stateful inclusion | 2 pd; ≈ $210–915 | 8 → 9 |
| 17 | Burn-in | A long burn-in (≥ 5 half-lives); B sample the initial state from a stored long-run distribution | KS-equivalence of the day-1 state to the 5,000-day state per engine → whichever meets the bound at lower cost | 1 pd; 10 min | 1 |
| 18 | Hazard horizon scaling | A cumulative hazard over the mania = GSY 2-year probability; B scaled by mania length / 2 years; C h0 FIT from the panel's own run-ups | topped share and peak P/V̂ of the panel's single-stock run-ups vs each mapping → the mapping whose topped share is inside the panel's CI | 1 pd; 20 min | 4 |

---

## 1. Removing the start-price answer key

**Question.** Which mechanism removes the day-1 anchor (V_1 = P_1 = 100) without introducing a new nuisance for the LLM or breaking comparability?

**Options.**
- **A. Randomise the level.** V_1 ~ LogUniform(P_lo, P_hi), P_1 = V_1 e^{x_1}; all price-denominated fields scale with V_1. Assumes the rendered magnitude does not itself move the LLM. Cost: 1 person-day, no compute beyond E1.6. Literature: none needed for the principle (a nuisance parameter must carry no information); the range is FIT (P5–P95 of large-cap closes). Known consequence (LOG §2): the plan's own test "R² of x_1 on log P_1 < 0.01" fails under A for any range narrower than about LogU(10, 1000) because R² = var(x_1)/(var(x_1)+var(log V_1)) ≈ 0.019 at LogU(20, 500) — the test, not the mechanism, was wrong.
- **B. Normalise the price** (plan review pointer 1). P_1 ≡ 100, V_1 = 100 e^{−x_1}; log(P_t/100) = (x_t − x_1) + (log V_t − log V_1) reveals changes, not the level. Assumes the LLM's behaviour does not depend on the price magnitude (removed by construction) but accepts that every run starts at "100", which a stateful reader can use to compute relative moves exactly (they are level-free anyway). Cost: same as A.
- **C. Both.** P_1 ≡ 100 for the hidden generator (option B) and a random rendering scale k_render ~ LogUniform applied to every price-denominated field at render time only. Separates the information question (settled by B) from the magnitude nuisance (measured by the k_render factor). Cost: 1.5 person-days (a render-time transform plus tests that ratios and returns are invariant).
- **D. Render no level at all** (returns, ratios to moving averages, P/E, yield, analyst/price ratio). Removes the channel entirely but changes the observation contract (and v1 comparability) most.

Evidence gathered: the Kalman bound (LOG §3) is identical under A–D — under every option the day-1 price carries no information about x_1 and the price history bounds R²(x) at 0.14–0.26 within 200 days (0.40 steady state). So the options do not differ in what a level-free reader can infer; they differ in (i) an LLM-side magnitude effect, (ii) comparability, (iii) how the analyst/EPS fields must be rescaled (identically for A–C).

**What would show which option is right.**
1. Generator side (Phase 1, E1.1): 500 seeds × 4 scenarios × T = 200 under A, B, C; statistic: the level-feature attacker's R²(x) minus the level-free attacker's R²(x), cluster-bootstrap 95 % CI over paths. Rule: an option passes if the CI contains 0 in every scenario (power: at 500 seeds the CI half-width on an R² difference is ≈ 0.02 from the audits' path-level variance, so a residual leak of 0.05 is detected with > 0.8 power). All three should pass; if one does not, it is out.
2. LLM side (Phase 9 cell, pre-registered now): the same 10 paths rendered under A at three magnitudes (V_1 ∈ {20, 100, 400}) and under B, for 3 personas × 2 scenarios (flat, crash δ 0.70) on Gemini 2.5 Flash, 1 replicate = 60 + 60 runs ≈ $22; statistic: band-MAS and MCR difference between magnitude levels, paired by path; rule: the magnitude effect is "absent" if its 90 % CI lies inside ± half of D12's minimum effect (equivalence); power depends on the variance pilot's σ_d (E8.5) and is computed there before the runs. If the magnitude effect is absent, A and B are equivalent and the cheaper comparability argument decides (B keeps v1/v2's "100" rendering); if present, A is out and C or B is adopted with the magnitude logged as a covariate.
3. No option wins if the LLM test is underpowered after the pilot: then B is reported as the provisional default *because it is the only option under which the magnitude effect cannot exist*, with the A-vs-B LLM test carried into the main grid as a factor. This is the one place the register names a provisional default, and it is chosen by exclusion, not preference.

**What each does downstream.** All three remove the price channel for the L2/L5 audits and make E1.6's level-free control meaningful; none closes the field channels (analyst F = V e^u, EPS × k), which Phase 5 must re-test. A changes the rendered magnitude of every v1/v2 comparison cell (the bridge cell must then use B); B keeps the rendered "100" and preserves the bridge; C adds a factor to the Phase 9 grid; D changes the observation contract and Table 2 and cannot be compared with v1 at all. The paper's "price history predicts mispricing by design" sentence is withdrawn under every option and replaced by the bound.

---

## 2. The value process

**Question.** Is V a smooth fundamental (σ_V = 0.006/day, v2's rationale), a rougher fitted fundamental (Vuolteenaho-type), or should both environments run as a factor?

**Options.**
- **A. Smooth V (v2).** Keeps the "hidden value, persistent mispricing" design; the rationale ("most single-stock variance is idiosyncratic", CLMX 2001) is wrong as stated — CLMX (read) decompose variance into market/industry/firm (0.72 firm-level), not fundamental/transitory. Cost: none. Literature undercutting it: Vuolteenaho (2002; read, annual, firm level): cash-flow-news variance 0.080 vs expected-return-news 0.016 — cash-flow news dominates firm-level annual return variance, so V cannot be "smooth" relative to returns at the annual horizon.
- **B. Fitted σ_V.** σ_V from the E1.2 decomposition (variance ratios; P/V̂ AR(1); SMM). Assumes the decomposition is identified from 25 years of daily prices (LOG §7: ≈ 8 non-overlapping 750-day windows per stock; pooled over 100+ names). Cost: inside E1.2 (3–4 person-days). Literature supporting a larger σ_V: Vuolteenaho (2002) and Cohen–Polk–Vuolteenaho (2003; read: 55 % of 15-year B/M variance is profitability). Consequence already computable (LOG §3): the level-free price-only bound falls from 0.40 (σ_V 0.006) to 0.23 (0.010) to 0.08 (0.020).
- **C. Two environments as a factor.** Run both σ_V levels through Phases 6 and 9. Cost: doubles the generator side of Phases 6 and 9 (≈ +$210 per model in Tier A). Assumes the paper can carry a two-environment story.

**What would show which option is right.** E1.2 as pre-registered: three estimators of (σ_V, s_x, h) on the panel with block-bootstrap intervals over stocks and time (block 250 d), per sub-period. Rule: if the σ_V intervals of the estimators overlap, adopt the pooled FIT (B); if they do not, report all three with the Kalman-bound and audit tables (E1.3) for σ_V ∈ {0.004, 0.006, 0.010, 0.015, 0.020} and put A vs B vs C to the team (D3) with the numbers. Power: the variance-ratio CI at k = 500 pooled over 100 stocks is ≈ ± 0.15 in VR units from the block bootstrap (to be confirmed on the panel); this translates to a σ_V interval of roughly ± 30 %, which distinguishes 0.006 from 0.012 but not 0.006 from 0.008. If no option wins (the estimators disagree *and* the team does not choose), the plan stops at the end of Phase 1 and the report shows both environments' consequences.

**Downstream.** A keeps every v2 number comparable but leaves the "smooth fundamental" claim unsupported; B changes coverage (share of resolvable steps), the Kalman bound, checklist item 20 and every audit; C doubles Phase 6/9 and forces the paper to state results per environment. The go/no-go G4 (PLAN 16A) is easier to pass under B (the observables oracle adds more over price) and harder under A.

---

## 3. Where jumps belong and how they are shaped

**Question.** Should rare jumps enter V at announcement dates, x with zero mean, or both — and with what size distribution?

**Options.**
- **A. Jumps in V at announcement dates** (quarterly, tied to the EPS surprise) plus a residual Poisson component in V. Assumes fundamental news is the source of large moves; makes the EPS field carry the jump (as in reality) — a channel Phase 5 must audit. Literature: Andersen–Bollerslev–Diebold (2007; read): jump variation is 14.4 % of S&P 500 realised variance (index futures, 1990–2002), 27.9 % of days carry a significant jump; Boudoukh et al. (2019; read): identified news explains 49.6 % of overnight idiosyncratic volatility at the firm level. Cost: 1.5 person-days (EPS-linked jump; the observables block must consume it).
- **B. Mean-zero jumps in x.** Keeps the jumps where they are, removes the −4 % mean. Assumes non-fundamental large moves (liquidity, sentiment). Cost: trivial. Known consequence (LOG §2): E[x] in flat goes from −0.08 to ≈ 0, but the flat-path share with excess kurtosis > 1.5 falls from 0.85 to 0.70 (40 seeds) — checklist item 2 is re-opened unless the jump sd is re-fitted.
- **C. Both** (announcement jumps in V, mean-zero jumps in x, sizes FIT separately from the announcement-day / other-day split).

Dominated: the current variant (negative-mean jumps in x) — it biases the control (item 4) and is excluded by the E[x] rule; recorded for completeness.

**What would show which option is right.** On the panel: standardised residuals from the per-stock GJR-GARCH fits (E3.1); the share of |z| > 4 days that are announcement days (EDGAR 8-K dates) and the kurtosis of announcement-day vs other-day residuals. Generator: the same split under A, B, C at 200 seeds. Statistic: the bootstrap 95 % upper limit of the two-sample KS distance between the panel's and the generator's announcement/other-day residual distributions, separately for each day type. Rule: adopt the option with both upper limits below 0.10 (equivalence); if more than one passes, the one with the smaller announcement-day distance; if none passes, report the distances and the kurtosis shares under each, and run C (the most flexible) through Phase 6 with the shortfall stated. Power: at 200 seeds × ≈ 3 announcement days per quarter × 3 quarters ≈ 1,800 announcement-day residuals vs ≈ 30,000 panel announcement days, the KS distance sd is ≈ 0.02, so equivalence at 0.10 has ≈ 0.8 power against a true distance of 0.05. E[x] equivalence (|E[x]| ≤ 0.02 at 200 seeds; SE ≈ 0.009) is required of every option.

**Downstream.** A makes the EPS field informative about jumps (Phase 5's onset audit must include it) and changes the analyst field's behaviour around announcements; B leaves the fields untouched but needs E3.2's size re-fit for item 2; C changes both. All three remove the control's bias, which changes the pilot's "buy the dip" reading (pilot numbers re-scored under Phase 7's new baselines). Checklist item 8 (crash asymmetry) depends on the sign asymmetry of whichever jump component remains.

---

## 4. The mispricing engine

**Question.** With the units fixed, should the calm process be the Franke–Westerhoff DCA-HPM, an honest AR(1)+GARCH, or a published FW variant whose structure matches v2's stochastic fundamental?

**Options.**
- **A. FW DCA-HPM with `price_scale = 1`,** parameters FIT by SMM (E2.3). Assumes the switching mechanism adds something at the single-stock level that return moments plus persistence moments can identify. Literature read: FW (2012) — units and parameters confirmed, index level, p = 32.6 %; SABCEMM (read): DCA-HPM average chartist share 0.23, excess kurtosis 7.8 in simulation (the plan's 0.17 / 10 is the WHP row). Known: at scale 1 with v2's Gaussian innovations the index set gives a 17 % chartist share and a ≈ 610-day half-life (LOG §1). Cost: E2.3's SMM (≈ 4 person-days, 2–3 h compute).
- **B. AR(1)+GJR-GARCH-t.** The process v2 actually runs (n_f ≈ 1); the `ar1` engine reproduces the checklist item for item (review B). Assumes no structural switching is needed for the benchmark's purposes. Cost: nothing new; the documents must say "AR(1)+GARCH". Literature: Summers (1986; read) — the fads model is exactly this (α = 0.98 monthly); Poterba–Summers (1988; read).
- **C. FW+ (Pruna, Polukarov & Jennings 2016; read)** — FW's DCA structure with a geometric-Brownian fundamental (σ_p = 0.157 in their Table 1), which is v2's own decomposition; or DCA-WHP (SABCEMM row: chartist share 0.17, kurtosis 10). Assumes the published variant's extra parameter (fundamental volatility) is estimable jointly with σ_V of Phase 1 — a coupling that must be handled by fixing σ_V from E1.2 inside the SMM. Cost: as A plus 1 person-day.

**What would show which option is right.** E2.4 as pre-registered, extended to three engines: (a) SMM acceptance (χ² at 5 % with df = moments − parameters, plus FW's bootstrap p) on the nine FW moments plus the persistence-carrying moments (VR at 20/60/120/250/500 d; ACF of log(P/SMA250) at 20/60/120), pooled over ≥ 100 stocks, block-bootstrap weight matrix stored; (b) held-out moment prediction (fit 2000–16, predict 2017–24; distance in bootstrap-sd units); (c) equivalence of the checklist and level-free leakage statistics at matched persistence and sd(x) (200 seeds; items differing by more than their CI listed). Rule (asymmetric by design, ties to the simpler model): A or C is adopted only if accepted at (a) *and* beats B at (b) by more than one bootstrap sd on the persistence-carrying moments; if both A and C qualify, the one with the smaller held-out distance; otherwise B, with A/C as sensitivities and every document naming the engine. Power: the bootstrap-sd unit makes (b) a one-sd test; with 20 paths × 5,000 days per evaluation and common random numbers the simulation noise on the persistence moments is below 0.3 sd (to be verified in the SMM diagnostics). If no engine is accepted at (a) — plausible, since single stocks have jumps and announcements that none of the three models — the report says so, B is the default by the rule, and the paper states that the calm process is a fitted AR(1)+GARCH whose persistence is FIT.

**Downstream.** A/C keep the fundamentalist/chartist narrative (slide 6) legitimately only if the fitted chartist share is non-trivial (the share is published); B removes the narrative and simplifies Phases 4 and 9 (no n_f state). Persistence sweeps (E2.6) run under whichever engine is adopted; the half-life table (E2.5) is engine-independent. Comparability: the ar1 engine reproduced the v2 checklist, so B is the *least* disruptive to v2 numbers; A at scale 1 changes the calm dynamics (17–23 % chartist days) and every v2 audit number.

---

## 5. How the mispricing persistence is estimated, and what to do if the estimators disagree

**Question.** Which estimator of the firm-level half-life h is adopted — variance ratios, the P/V̂-proxy AR(1) with Andrews' median-unbiased correction, or SMM with persistence-carrying moments — and how is a disagreement resolved?

**Options.**
- **A. Variance ratios** VR(k), k ∈ {5…500}, of daily log prices, with the closed-form VR of RW + AR(1); minimum distance. Assumes the RW + AR(1) decomposition and stationarity over 25 years; needs no fundamental proxy. Literature: Lo & MacKinlay (1988; read; robust SE); Poterba & Summers (1988; read; index-level VR evidence).
- **B. P/V̂ AR(1)** with V̂ = trailing-4Q EPS × sector-median multiple (EDGAR), monthly, Andrews (1993; read) median-unbiased correction; block bootstrap over stocks and time. Assumes V̂ is a valid fundamental proxy (measurement error in V̂ biases h *upward* if the error is persistent, downward if it is white). Literature: Andrews (1993; read); Marriott–Pope / Kendall (1954; existence read; the bias formula not read at source); Lee–Myers–Swaminathan (1999) and Frankel–Lee (1998) support the cointegration form but their speeds were not retrievable.
- **C. SMM** with the persistence-carrying moments of entry 4. Assumes the engine's form; delivers h jointly with the other parameters.

**What would show which option is right.** (1) A simulation-recovery study, pre-registered: synthetic panels (100 stocks × 25 years) from the v2.1 generator with known h ∈ {30, 60, 120, 150, 250, 500} d, σ_V ∈ {0.006, 0.012}, plus a V̂ with persistent measurement error of the size observed in EDGAR (sd of log(EPS_q/EPS_{q−4}) noise); each estimator's bias and RMSE for h, 200 replications per cell. Rule: an estimator is "usable" at a given h if its median-unbiased recovery error is < 20 % and its 95 % interval covers the truth in ≥ 90 % of replications. (2) On data: the three estimators with block-bootstrap intervals. Rule: adopt the usable estimator with the smallest RMSE whose data interval contains the other usable estimators' point estimates; if the usable estimators' intervals are disjoint, adopt none — report all three, and run the persistence sweep (E2.6) over the union of their intervals so that Phase 6 and Phase 9 show whether anything depends on the choice (the sweep, not a pick, is the resolution). Power: 200 replications per cell give the RMSE to ± 5 %; the data intervals' widths are the quantity of interest and are reported, not assumed.

**Downstream.** The adopted h sets the oracle-switch count (LOG §2: 0–1 switches per run at 150 d, ≈ 2 at 30 d), coverage, checklist item 9's criterion (re-derived in Phase 6), the Kalman bound and the go/no-go G3. If the union interval is wide (e.g. 60–500 d), G3's fate is decided by the sweep and D8, and the paper must report results at the interval's ends.

---

## 6. How regime volatility enters, and how implied volatility is built without a phase step or look-ahead

**Question.** Should the phase multiplier scale the whole conditional variance (v2, amendment A3), scale ω with a ramp (the plan's literal reading), or come from a fitted two-regime switching-variance model — and how is IV constructed so that it is not a phase marker?

**Options.**
- **A. Whole-variance scaling** σ²_t = m(phase) h_t (v2). Assumes an instantaneous regime shift. Produces the one-day IV step (z ≈ 7; LOG §1). Cost: none.
- **B. ω-scaling with a FIT ramp** (level adjusts at the GARCH persistence rate; A3 rejected it because a 15–70-day panic cannot then reach the plan's panic targets — a target that Phase 6 re-derives anyway). Cost: 1 person-day.
- **C. Fitted two-regime switching variance** (Hamilton–Susmel-type): regime variances and transition probabilities FIT on the panel's event windows, the scripted phases setting only the regime *probabilities*. Literature: Ang & Timmermann (2012; read): monthly S&P σ 4.89 vs 2.45 %, P 0.977, Q 0.951 — index, monthly, so usable only as a sanity ratio (≈ 4 in variance); Ang & Bekaert (2002; read): 7.04 vs 3.77 % monthly; Schwert (1989; read): +76 % to +227 % in recessions; **Hamilton & Susmel (1994): the factors could not be read and are not quoted.** Cost: 3 person-days.
- IV under each: IV_t = √(252 σ̂²_{t+1..t+21}) (1 + π_t) e^{ε_t}, σ̂² from a GJR-GARCH filter run on observed returns only (past-only by construction), π_t FIT from the five CBOE single-stock VIX histories (VXAPL…VXIBM, 2011–2026, available; LOG §5) against realised variance, ε_t FIT from the residual; the whole-path stress quantile removed.

**What would show which option is right.** E3.3/E3.4: from the panel's single-stock drawdowns ≥ 30 % and the market crash windows, the number of days from onset (first 10 % decline) to peak 21-day realised variance and the post-peak decay half-life, with bootstrap CIs (n = the number of episodes, stated; the plan's two index examples — 2020 ≈ 10 d, 2008 ≈ 30 d — are not a sample). Generator: the same statistics under A, B, C at 200 crash seeds. Rule: adopt the mechanism whose rise time and decay half-life both fall inside the empirical 95 % CI; if two do, the one with fewer free parameters (A < B < C); if none does, report all three against the CI and keep A as the documented shortfall. Power: with ≥ 60 single-stock episodes the CI on the median rise time is ≈ ± 4 days (bootstrap), enough to separate "instant" (A) from a 20-day ramp. IV audit (E3.5, with the review's fix): the onset-detection AUC of IV must not exceed that of the same filter's 21-day RV forecast by more than the label-permutation null's 95th percentile (200 seeds).

**Downstream.** A keeps v2's panic depth and IV levels; B lowers realised panic variance for short panics (checklist items 13 and 20 re-derived in Phase 6 will say whether that matters); C changes the variance model everywhere and adds fitted parameters with intervals. The IV construction is common to all three and removes item 46 and the look-ahead (item 25) under each.

---

## 7. The sustained-bull control

**Question.** What is the sustained-bull scenario for, and which definition serves that purpose without selecting a quiet sub-population or building a scenario clock?

**Options** (with the effect on the control's purpose):
- **A. Same mispricing process as flat, no band** (d_t = 0 as the v2 plan says; only V_T/V_1 ≥ 1.2 required). Measured (LOG §7): 8 % of unanchored draws stay inside [−0.10, 0.15]; the path-mean x has p10/p50/p90 = −0.34/−0.11/+0.07 (jump bias included); daily sd equals flat's. Purpose served: "rising value, same mispricing as flat" — a control for the *value* channel, not a no-mispricing control. Cost: trivial.
- **B. Band on V only** (V rising by a FIT threshold, no x criterion; the "no bubble" condition expressed as "no top event", i.e. the mania driver switched off). Same population as A in x; purpose identical; differs from A only in what the rejection log says.
- **C. Anchored x as in v2** (d_t = −0.15 x). A different process (half-life 4.6 d), 36–40 % rejection, recalled at 82 % from price alone. Purpose served: "value rises, no mispricing" literally, at the cost of a scenario clock. Dominated on the audit evidence (review C.5, LOG §1), recorded for completeness.
- **D. Rendered-matched control.** Same x process as flat; V rising; the *rendered* distribution of the level-free fields matched to the flat scenario by construction (no phase multiplier, same jumps), and the scenario's purpose redefined as "the mandate-conflict question when the value rises" — with the explicit statement that mispricing is present in the control and the oracle acts on it.

**What would show which option is right.** Pre-registered on 200 seeds per definition: (i) the scenario-discrimination audit on demeaned level-free returns and IV — a classifier of sustained-bull vs flat days must be at chance (accuracy ≤ the 95th percentile of a label-permutation null; the null computed in Phase 4); (ii) the published selection statistics (accepted vs rejected daily sd, ACF(1), IV — the KS upper limit < 0.10); (iii) the execution order's acceptance test at baseline level: on the control, the mandate-conditional oracle and constant-mix must have the same regret within the CI while band-MAS differs across the trivial policies ("adherence moves, regret does not") — **this test presupposes that the control has no resolvable mispricing, which only C satisfies; under A/B/D it is replaced by "the oracle's regret gap over constant-mix in the control equals its gap in flat within the CI".** Rule: the definition adopted is the one meeting (i) and (ii) that serves the purpose the team states in D14; if the team's purpose is "no mispricing", only C serves it and its clock must be published as a limitation; if the purpose is "rising value with the same mispricing", A/B/D serve it and (i)–(ii) pick among them. Power: (i) at 200 seeds × 200 days the classifier's accuracy SE is < 1 pp, so a 5 pp departure from chance is detected.

**Downstream.** A/B/D change the pilot's sustained-bull cell entirely (the oracle now acts in the control; the "observables-oracle gap is largest in sustained bull" statement is withdrawn) and remove item 42's selection; C keeps v2's numbers and keeps the clock. The go/no-go G1 must hold in the control under A/B/D (there is a right answer) but not under C (no resolvable steps; G1 is evaluated on the three event scenarios only in that case).

---

## 8. Event dynamics

**Question.** How should events move x — a tracking gain onto a scripted path (v2), a shifted perceived fundamental with a regime-specific pull, a scripted drift with rejection, or an unscripted regime-switching model without error correction?

**Options.**
- **A. Tracking gain λ** onto x* (v2; λ ∈ {0.02, 0.05, 0.10, 0.25}). No literature can exist for λ (review A). Script share of event-phase Δx variance is the diagnostic. Cost: exists.
- **B. Shifted perceived fundamental** p* → p* + log δ during the event with a regime-specific pull φ_regime FIT from the panel's crash-window decay (FW-native: an event is a change in what fundamentalists believe). Assumes the FW form is retained (entry 4 A/C); under B of entry 4 it reduces to a shifted AR(1) mean. Cost: 2 person-days.
- **C. Scripted drift with no feedback plus rejection** (depth/duration enforced by rejection sampling only; rejection rate published). Assumes the rejection rate stays below a pre-registered level (set in Phase 4 from the episode tables' coverage: the share of episodes inside the P10–P90 ranges is the natural ceiling). Cost: 1 person-day.
- **D. Unscripted regime switching without error correction**: the event is a change in the regime variance and in the fundamentalists' p* (as B) *and* in the drift of V (D_V), with no target path at all; depth and duration are outcomes. Literature: Campbell–Giglio–Polk (2013; read): 2000–02 discount-rate driven, 2007–09 cash-flow driven — supports giving events both a V and an x component. Cost: 3 person-days.

**What would show which option is right.** E4.6 extended: for each formulation at 200 crash and 200 bull seeds, (i) the script share R² of d_t on Δx in event phases (0 for D by construction), (ii) the share of paths whose peak-to-trough depth and duration fall inside the episode tables' P10–P90 (E4.1), (iii) the rejection rate against the pre-registered ceiling, (iv) checklist items 10 and 20 and the level-free leakage statistics. Rule: adopt the formulation with the lowest script share among those with (ii) ≥ the pre-registered coverage (the share of real episodes inside their own P10–P90 is 0.80 by construction of the range; the generator must reach ≥ 0.70, a DESIGN margin stated as such) and (iii) below the ceiling; if none qualifies, D5 with the table. Power: shares at 200 seeds have SE ≈ 3 pp; the 0.70 vs 0.80 distinction is resolved.

**Downstream.** A keeps every v2 crash number; B/D change the meaning of δ (from a target to a belief shift) and the delta levels must be re-expressed; C raises rejection and needs the ceiling; D removes the "scripted target path + GARCH noise" description and lets depth vary — checklist item 10 ("severity matters") becomes a statement about D_V and the belief shift, not about a target. The multi-asset extension inherits whichever formulation (per-asset draws).

---

## 9. The calendar

**Question.** How should the day be rendered (random calendar dates; no date; "Day-N" as a disclosed arm), and what ordering mix makes time and phase separable?

**Options.**
- **A. Random calendar dates** (a random start date, weekdays rendered). Assumes the LLM does not use real-world knowledge attached to dates (e.g. "March 2020"); a 2020 start would inject priors. Cost: 0.5 person-day plus a check that no date coincides with a known crash window (or a rule to exclude 1987, 2000–02, 2008–09, 2020).
- **B. No date** (no day index rendered; `days_since_eps_announcement` remains, with a randomised quarter phase). Assumes the stateless agent needs no clock; the stateful agent can count turns.
- **C. "Day-N" as a disclosed arm** (the current rendering, kept as a factor with the horizon disclosed or not).
- **Ordering mix** (any rendering): setup-first / event-first / phase-free shares and the setup range chosen so that a day-only phase classifier is at chance within each scenario.

**What would show which option is right.** Generator side (Phase 4): for each ordering mix and setup range, the day-only macro-phase classifier's accuracy per scenario vs the label-permutation null (200 seeds); rule: the mix is acceptable if accuracy ≤ null 95th percentile + 1 pp (the 1 pp is the sampling half-width at 200 seeds). LLM side (Phase 9, pre-registered now): a phase-restatement probe — the model is asked, in a side call at 20 stratified days per run, which phase it believes the market is in; 3 renderings × 2 scenarios × 15 seeds on Flash = 90 runs ≈ $16; statistic: the probe's macro-phase accuracy vs the same permutation null; rule: a rendering is "clock-free" if the probe's accuracy is at chance for a stateless agent and, for the stateful agent, no higher than the turn-count classifier's. Power: 90 runs × 20 probes = 1,800 probes; a 5 pp departure from chance is detected at > 0.9 power. If every rendering is clock-free at the generator's mix, comparability decides (C keeps v1's rendering) and D6 is the team's; if A or C leaks through the LLM (A through date priors, C through the day index), it is out.

**Downstream.** B or A breaks the v1 rendering (the bridge cell keeps C); the ordering factor enters the arm grid (PLAN E4.7) under every option and changes the population of LLM runs, which is the point (item 6). The "time vs phase" claim is identified only in the mixed population.

---

## 10. Observables that currently read the hidden state

### 10a. The P/E multiple

**Question.** Fixed draw with a FIT-wide range; time-varying log-AR(1); or a multiple tied to a fitted cross-section?

**Options.** A fixed k per seed from the FIT P10–P90 (EDGAR × prices; Damodaran industry file as cross-check) — assumes the multiple is constant over 200 days (it is not: Shiller's series shows year-scale variation), so P/E × EPS identifies V asymptotically. B a log-AR(1) k_t per seed with FIT dispersion and quarterly persistence (from the stock-level P/E panel) — assumes the persistence is estimable at quarterly frequency (≈ 68 quarters per stock in EDGAR's range; enough). C k tied to observable characteristics (sector, size) via a fitted cross-section — assumes the characteristics are rendered, which they are not; dominated unless the observation contract changes; recorded.

**Experiment.** E5.1 + E5.7(a): per-field-group L2 selectivity over the level-free control and the L1 extended inversion share, at 200 seeds, for A and B at three widths (P25–P75, P10–P90, P5–P95); rule: adopt the design with the lowest selectivity among those whose P/E cross-seed distribution is KS-equivalent (upper limit < 0.10) to the EDGAR cross-section; if both qualify, B if its selectivity is lower by more than the null margin, else A (simpler). Power: selectivity half-width ≈ 0.02 at 200 seeds.

**Downstream.** B removes the asymptotic identification of V through EPS and changes Table 2; A leaves a slow channel that the L1 extended set will find. Phase 9 sweeps the width under either.

### 10b. Sentiment

**Question.** Returns-only; returns plus a slow valuation link; or survey-style?

**Options.** A returns-only AR(1) (contemporaneous and lagged return loadings FIT on the SF Fed index vs S&P returns; Tetlock 2007 read: 8.1 bp / 6.8 bp, index daily, as the cross-check) — assumes no direct valuation link at the daily single-stock level (no read evidence for one; Baker–Wurgler is monthly, market level). B returns plus a slow valuation link whose size is FIT as the coefficient of the SF Fed index on the Shiller CAPE log-deviation (monthly, market level, with CI) — "full Baker–Wurgler-sized" is defined as that coefficient, "half" as half of it; assumes a market-level coefficient transfers to a single stock's log(P/V) (an assumption stated as DESIGN). C survey-style: an AR(1) with the weekly persistence and return loading FIT on AAII (public, 1987–2026) — assumes survey sentiment is the right construct for a "news sentiment" field.

**Experiment.** E5.5 + E5.7: for each design, (i) the item-12 statistics (AR(1), corr(s, r), the b_pred partial correlation) against the FIT values with CIs; (ii) L2 selectivity for x and V and the onset AUC; rule: adopt the design meeting (i) with the lowest (ii); B's valuation link is retained only if its selectivity increment is inside the null margin — otherwise it is reported as the labelled sensitivity. D15 records the default after the results. Power: as 10a.

**Downstream.** A/C make the field level-free by construction (`test_sentiment_level_free`); B keeps a small x channel whose size is known; the b_pred control arm's meaning is unchanged under all three.

### 10c. Volume

**Question.** |r| only, or |r| plus turnover in run-ups?

**Options.** A log-volume AR(1) + |r| elasticity + noise, all FIT on the panel (Lo & Wang 2000 read: weekly turnover AC(1) 0.91 at the market level — a sanity range, not the value). B adds a run-up turnover ratio FIT from the panel's GSY-style run-ups (GSY 2019 read: turnover is high in run-ups whether or not they crash, so the ratio is a run-up feature, not a crash predictor). The |x| loading (v2) is dominated — no read evidence links volume to mispricing — and is recorded.

**Experiment.** E5.6 + E5.7(c): onset-detection AUC of volume vs the price-derived AUC at 200 seeds under A and B; the run-up ratio's FIT with CI; rule: B if the FIT ratio's CI excludes 1 and B's onset AUC excess over price is inside the null margin; else A.

**Downstream.** Checklist item 7 (volume–|r| Spearman, AC, log-normality) is re-derived in Phase 6 from the panel under either; A1's amendment is retired.

### 10d. The analyst estimate

**Question.** Keep the field with a literature sd and sensitivity; drop it; or replace it with a lagged smoothed price proxy?

**Options.** A keep F_t = V_t e^{u_t} with a LIT sd: the read anchor is an **absolute target-price error ≈ 45 % of price at a 12-month horizon** (Bradshaw et al. 2013: 45 %; Bilinski et al. 2013: 44.7 %) — converted to a log-error sd by the pre-registered mapping E|u| = sd·√(2/π) for Gaussian u → sd ≈ 0.45·√(π/2) ≈ 0.56 if the 45 % is a mean absolute error in log terms, or the direct FIT on the two papers' error distributions if their tables give them; the horizon mismatch (a 12-month target vs a fair-value estimate) is stated, and the bracket {0.15, 0.30, 0.45} becomes {0.30, 0.45, 0.60} (the v2 0.15 is below every read value); persistence stays DESIGN (no free data). B drop the field (removes a direct V channel and the "22 % error" slide). C a lagged smoothed price proxy (F_t = SMA250 or a per-seed k × trailing EPS — an analyst who extrapolates), level-free by construction, no V channel.

**Experiment.** E5.4 + E5.7 + Phase 9: L2/L5 selectivity of the field at each sd level (A) vs C at 200 seeds; the LLM grid (Tier A includes the analyst sd as one of the six parameters) measures whether any arm contrast is level-dependent. Rule: A at a given sd is admissible if its selectivity is inside the null margin; C if its inclusion changes no arm contrast beyond the equivalence margin; B if neither holds. If no option wins (A leaks at every sd and C changes contrasts), the field is dropped and the paper says the environment has no analyst field. Power: LLM part from E8.5.

**Downstream.** A keeps Table 2 and slide 5 with a corrected number; B changes the rendered field set and every audit; C changes the field's meaning (a trend-follower's estimate) and must be described as such.

---

## 11. The resolvability threshold θ

**Question.** Should θ be derived from information (the level-free surrogate's sign accuracy), from cost break-even, from the within-run variance of x, or reported co-primary?

**Options.** A θ_info = the |x| at which the level-free observables surrogate reaches sign accuracy 0.80 — ties "correct" to what the agent can see, but moves whenever the fields or the surrogate change (review 7) and may never reach 0.80 (review C: 0.71 on resolvable steps). B θ_cost = the mispricing at which a full reallocation's expected profit over one half-life exceeds the round-trip cost at the adopted tier (5 bp per side; the cost concept — quoted spread (Nasdaq 4.5 bp, read) vs market impact (FIM median 6.18 bp, read) — is stated) — stable, but it depends on h (entry 5) and on the persona's band width. C θ_var = one within-run sd of x at T = 200 (≈ 0.05–0.06 at the live engine; LOG §1) — depends on h and T only. D co-primary A + B with C and the fixed grid as sensitivities (review 7; adopted in the corrected plan as the *reporting* rule, not as a choice of θ).

**Experiment.** E7.1: all headline metrics re-scored at θ ∈ {0.03, 0.05, 0.08, 0.12, 0.20} and at the three derived values on the pilot and the baselines (no API); Phase 9's robustness table has θ as a re-scoring dimension. Rule: if every Phase-9 conclusion's sign and significance are the same at θ_info and θ_cost, co-primary reporting stands with no choice needed; if a conclusion flips between them, D7 with the table. Power: re-scoring is exact; the conclusions' power is Phase 9's.

**Downstream.** θ sets coverage, oracle switches (G3), MCR and the L4 audit; a θ_info that is "not reached" leaves θ_cost alone as primary. The pilot's published numbers are re-scored under both.

---

## 12. The regret metric

**Question.** Decompose MCR into band violation and directional agreement; score per window; or change the ceiling/floor convention?

**Options.** A decomposition B_t + D_t (band-violation and within-band directional term) on resolvable steps, ceiling = mandate oracle (0), floor = worst trivial policy, signs in one function — the correctness fix of item 53 plus item 52's decomposition. B per-window scoring (25-day windows; the oracle's target per window; regret per window then averaged) — changes what a "decision" is and interacts with G3 (switches per window). C alternative conventions (ceiling = constant-mix as the code does now, floor = best trivial; or normalise by the trivial-policy spread) — the current code's convention is one of these and is mislabelled, not wrong.

**Experiment.** E7.8's construct-validity table: scripted policies with a swept parameter (allocation drift rate → band-MAS; value-alignment probability → the directional term; panic intensity → drawdown) must move each metric monotonically; plus the metric-correlation matrix across cells. Rule: adopt the scoring under which (i) every scripted sweep is monotone in its target metric, (ii) |corr(MCR, band-MAS)| across cells is below a pre-registered ceiling derived from the scripted sweeps (the correlation observed when the directional probability is held fixed and only the drift rate varies gives the collinearity floor; the ceiling is that floor plus the bootstrap half-width), (iii) the oracle switch count under the scoring is reported. If both A and B satisfy (i)–(ii), A (comparable with the pilot); if neither, the report shows the matrices and D8 is asked. Power: the scripted sweeps are deterministic; the correlation ceiling's half-width comes from the number of cells (≥ 48).

**Downstream.** A re-labels the pilot's norm_mcr (annotated "against constant-mix" until re-scored); B changes the pilot's numbers and G3's unit; C is a labelling choice with no effect on rankings within a cell.

---

## 13. The target bands

**Question.** Practitioner categories (the v2 bands), utility-consistent bands from the environment's own (μ, σ), or both as a factor?

**Options.** A practitioner categories: read today — Morningstar 15–30 / 30–50 / 50–70 / 70–85 / 85+ % equity; Fidelity Conservative 20 % equity, Balanced 50 %, Growth 70 %, Aggressive Growth 85 %; Vanguard conservative 40/60 (30/70 in retirement); Betterment conservative 4–7 pp below recommended. The v2 bands (cash 0.70–0.90 / 0.40–0.60 / 0.00–0.20) match Fidelity and Morningstar's conservative and balanced categories and sit above every source for "aggressive" (85 % equity ⇒ cash 0.15, inside the band). Assumes the paper's personas are categories, which is what the personas' texts say. B utility-consistent bands: Merton shares with the environment's fitted (μ, σ) after Phases 1–3, γ ∈ {2, …, 10}, dividends paid — assumes a single-stock CRRA investor is the right normative reference (the environment has σ ≈ 28 %/yr; review C.39 shows γ = 3–4 lands in the conservative band). C both as a factor in Phase 9.

**Experiment.** E7.3: the Merton table on the fitted (μ, σ) with intervals from the Phase 1–3 fits; band-MAS of the trivial policies and the pilot cells under A and B; Phase 9's arm contrasts under both (C). Rule: the scored default is A unless the Phase-9 interaction band × arm exceeds the equivalence margin — in which case D9 is put to the team with the interaction table; the JFE ordering check is run only after `targets.py`'s JFE_SPREAD is re-derived from Jiang–Peng–Yan Table 7 (read: no spread is stated there). Power: Phase 9's.

**Downstream.** B changes every MAS and MCR number and the persona-to-band map (the ISFJ band may move); A keeps them; C doubles the scoring (no API cost) and the paper's tables.

---

## 14. Checklist criteria, and the seed/horizon policy

**Question.** Pre-registered numeric thresholds (v2), equivalence to real 200-day windows (KS bound), or percentile bands from the reference distribution — and T = 200 only vs T = 200 with longer horizons reported separately?

**Options.** A the v2 numeric thresholds (many moved after the fact; review B); B KS-equivalence: the bootstrap 95 % upper limit of the two-sample KS distance between the generator's cross-seed distribution and the real 200-day-window distribution is below 0.10 (the corrected form; LOG §3: a plain KS test rejects D = 0.10 with 97 % power at these sizes, so non-rejection is not equivalence); C the P10–P90 band of the real windows with a share criterion (the generator's share inside the band ≥ 0.80 − the sampling half-width). Horizon: T = 200 as the criterion ("what the agent experiences") with T ∈ {800, 2,000} reported for the persistence and ACF-decay items only; or T = 200 only.

**Experiment.** E6.1–E6.3: (i) known-answer panels (synthetic AR/GARCH series with known properties) to measure each criterion's size and power per item; (ii) the three criteria applied to the v2.1 generator; concordance table. Rule: items where A and B/C agree are reported once; items where they disagree are reported under both with the explanation (the reviews' "structural vs mis-specified criterion" question is answered item by item); the seed count per item is the maximum required by the power rule across the criteria used. The horizon policy is not an experimental question: the benchmark runs T = 200, so the criterion is evaluated at T = 200 and the longer horizons are descriptive. Power: per item from (i).

**Downstream.** B/C retire the "nothing re-tuned" tile in favour of the reference tables; A keeps comparability with the v1/v2 checklist rows. Survivorship (entry 15) biases B/C's reference distributions toward calmer stocks; the report says so per item.

---

## 15. Data

**Question.** Fit on the free substitutes now, pause Phases 1–5 for WRDS access, or a hybrid (fit now, re-fit later)?

**Options.** A free substitutes (survivor panel from `yfinance`, EDGAR, SF Fed, Shiller, CBOE single-stock VIX, AAII; LOG §5 lists what is and is not reachable today — notably the Wikipedia constituent-changes table is gone and must be replaced, FRED was unreachable, Stooq is unusable). B pause until WRDS (institutional subscription only; timing unknown). C hybrid: A now, with the pre-registered code written so that CRSP/Compustat/OptionMetrics/IBES re-runs are a data-path change; re-fit when access arrives; both results published.

**Survivorship, quantified where possible.** (i) The share of the historical constituent list that `yfinance` still serves — computable in E1.0 (the plan's mitigation) once a constituent source exists; (ii) the difference between the survivor sample and the literature's full-universe values for the statistics survivorship affects most: crash depth (Mishkin–White 2002 read: 15 crashes ≥ 20 %; GSY 2019 read: 21 of 40 run-ups crashed ≥ 40 % within two years — industry level), tails (ABD 2007 read: 14.4 % jump share of index variance), volatility level; the survivor sample understates all three, and the size of the gap is the E1.0 deliverable, not an assumption.

**Experiment / rule.** After E1.0: if for any parameter fitted in Phases 3, 4 or 6 the survivor-vs-literature gap exceeds the fit's own 95 % interval, C is mandatory (the substitute value is published with the gap and the re-fit is scheduled); if no gap exceeds the interval, A suffices and the report says so; B only if WRDS access is confirmed to arrive before Phase 1 would end (a calendar fact the team knows and this pass does not).

**Downstream.** A/C keep the schedule; B stops everything after Phase 0 (the minimal path of PLAN Section 15 can still run). C doubles the fit reports.

---

## 16. The LLM sensitivity grid

**Question.** Which six generator parameters, which tiers, which models, and whether the stateful arms are included?

**Options.** Six parameters: (a) the reviews' six (σ_V, half-life, P/E width, analyst sd, sentiment loading, GARCH set) — the plan's choice; (b) the six with the largest standardised effect on the level-free observables-oracle regret and on the scripted policies' band-MAS in Phases 1–6 (a data-driven choice); θ is a re-scoring dimension under both. Tiers: A (two workhorses), B (+ one frontier model on six settings), C (+ ordering/calendar and sustained-bull, replicates). Models: Gemini 2.5 Flash and GPT-5 mini as workhorses (read prices: $0.18 and $0.15 per run), Claude Sonnet 5 as the frontier model ($1.07; $0.55 with cache reads); Opus 5 ($2.7) or open-weight anchors via OpenRouter (Llama-3.3-70B $0.10/$0.32 per M; no key present) as alternatives (D2). Stateful arms: excluded (7× cost) or included on the two highest-ranked parameters.

**Experiment / rule.** (i) The parameter set: pre-register (b)'s ranking rule now; after Phase 6 compute the ranks; if (a) and (b) share at least five parameters, run (a) (comparability with the reviews' list) and report the sixth of (b) as Tier C; otherwise run (b) and say why. (ii) Stateful inclusion: the variance pilot (E8.5) gives the ICC and σ_d of the stateful contrasts; include the stateful arms on two parameters only if the minimum effect (D12) is detectable at 5 seeds with ≥ 0.8 power at Tier B's cost; otherwise state the power that Tier B would have and leave the decision (D2). (iii) Tier: the tier is the team's budget decision; the register only prices them (LOG §6: ≈ $210 / $690 / $915).

**Downstream.** The grid's parameter list fixes which conclusions can be called robust; a data-driven list may omit a parameter a reviewer names (the report then shows its Phase-6 effect size as the reason).

---

## 17. Burn-in

**Question.** A long burn-in (≥ 5 half-lives for every engine, ≈ 3,000 days for `fw_index`) or an initial state sampled from a stored long-run distribution?

**Options.** A long burn-in — simple, costs generator time (≈ 15× the current 260 days for the index engine: ≈ 2.5 s per path). B stored stationary state (x, GARCH variance, n_f jointly) drawn per seed from a long pilot — fast, but the pilot becomes a hashed artefact of the freeze.

**Experiment / rule.** E1.5's equivalence test (the KS distance's bootstrap 95 % upper limit between the day-1 state and the 5,000-day state < 0.10, per engine, 500 seeds); adopt whichever meets it; if both, A for the default engine (no artefact) and B for the slow sensitivities. Power: at 500 vs 500 the KS sd is ≈ 0.03; equivalence at 0.10 has ≈ 0.8 power against a true 0.05.

**Downstream.** Only the sensitivities (`fw_index`, `pruna`) change; item 50 closes under either.

---

## 18. Hazard horizon scaling (E4.3's stated assumption)

**Question.** How are GSY's two-year, industry-level crash probabilities mapped to a daily hazard over a 40–150-day single-stock mania?

**Options.** A cumulative hazard over the mania length equals the GSY probability at the peak run-up (no time scaling); B scaled by mania length / two years; C h0 (and b) FIT directly from the panel's single-stock run-ups ≥ 100 % (E4.1), GSY used only as the industry-level cross-check.

**Experiment / rule.** The panel's run-up episodes give the empirical topped share within 200 days and the peak P/V̂ with bootstrap CIs (n stated; survivorship understates crashes — entry 15); the generator's topped share under A, B, C at 200 seeds; adopt the mapping whose topped share is inside the panel's CI; if the panel has too few run-ups (< 30) for a CI narrower than the A–B difference, report all three and keep the {0.5×, 1×, 2×} bracket as the sensitivity.

**Downstream.** The topped share is an outcome under all three (the 40–60 % target is retired); item 17's rejection rate for bull traps follows from the mapping.
