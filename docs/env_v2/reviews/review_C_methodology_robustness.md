# Review C: methodology and robustness (independent reviewer, 23 Aug 2026)

Scope: envs/v2/*, envs/synthetic_market.py, evaluation/*, simulation/*, agent/*, experiments/arms_v2.py, tools/*, tests/*, docs/env_v2/**, docs/env_research/*, the speaker script. Every numerical claim below that is not in the team's own reports was reproduced by the reviewer from the repository code (probe scripts in the reviewer's scratchpad; nothing in the repo was modified). Line numbers refer to commit b61fe07.

## Findings

### A. Generator structure

**1. The Franke-Westerhoff switching mechanism is inert: the fundamentalist share is pinned at 1 on 98-99 % of days.** `mispricing.py:52` (`price_scale = 100`), `:167-169` (`a = alpha_0 + alpha_n(n_f - n_c) + alpha_p (100 x)^2`, clamped at +-50). Measured on 10 seeds per scenario: share of days with n_f > 0.99 = 0.983 (flat), 0.987 (crash), 0.991 (bull_trap); the team's own pilot statistics record n_bar = 0.997-0.999. At x = 0.02 the attractiveness term is 73 (n_f = 1.000); with price_scale = 1 it is -0.32 (n_f = 0.42), and the index parameters then give n_bar = 0.83 instead of 0.999. In FW 2012 the price equation produces daily returns of ~0.8-2 % only if p is the natural log price, so (p* - p)^2 is in natural-log units and alpha_p = 18.43 acts on misalignments of 0.1-0.5. The spec flags the interpretation as "to be verified against the FW PDF" and never verified it. The realised dynamics are an AR(1) with pull mu*phi and a constant innovation weight: chi, alpha_0, alpha_n, alpha_p and sigma_c have no effect on any path. Slide 6 presents "the published Franke and Westerhoff model of fundamentalist and chartist traders, the share of each group shifts" as a design contribution; it is not what runs. The fw_index/pruna sensitivities and the fallback phi are all computed inside the saturated regime; the SMM non-identification is partly a consequence of the same saturation. Fix: set price_scale = 1 after checking FW 2012, re-derive phi and re-run; or drop the FW label and run the ar1 engine as the honest default. Severity HIGH.

**2. The fixed start price (V_1 = 100 in every seed) is the dominant information channel; a "compare price to 100" rule reaches oracle-level regret.** `generator.py:63,188` (V rescaled so V_1 = start_price), `synthetic_market.py:106` (default 100); runner, arms and all audits use 100. Probe (ISFJ, 12 seeds x 4 scenarios, theta 0.05): policy "cash = band-high if log(P/100) > 0.05, band-low if < -0.05, else unchanged" gives MCR 0.005 (bull_trap), 0.007 (crash), 0.014 (flat) against the true-V oracle 0.003, always-hold 0.11-0.14 and the published L5 GBT 0.02-0.045. It fails only in sustained_bull (0.098), exactly the scenario where the published L5 gap is largest. A GBT on level features gets OOS R2(x) = 0.84 (sign 0.945); on level-free features (log P/SMA20, log P/SMA50, RSI, MACD/P, returns) R2 = 0.40 (sign 0.71); with the start price randomised U(20, 500) the level-feature model collapses to R2 = 0.26. log P_t = log V_t + x_t with V_1 = 100 and sigma_V = 0.6 %/day means log(P_t/100) = x_t +- 0.085 for the whole horizon. The decision log, the L2 audit text, the strict-xfail reason and slides 23/25 attribute the L2 failure to "smooth V + persistent x, by construction". It is inferable from the level anchor, a removable implementation choice. Consequences: the environment is solved by a two-line rule for three of four scenarios; L2/L5 attackers trained across seeds exploit the anchor, so the "withheld information" numbers describe an attacker that knows V_1; the stateless LLM does not know the start price; the stateful arms do see day-1 price, an arm-dependent leak. Fix: draw start_price log-uniformly per seed and per asset, rescale EPS/analyst fields, re-run L2/L5 with a level-free price control; re-state every "by construction" sentence. Severity HIGH (top finding).

**3. Once the anchor is removed, the non-price fields leak x heavily (selectivity 0.56, not 0.11): "hidden value is hidden from the fields" is false.** Same audit code, 24 seeds, start price U(20, 500): price-only calm R2(x) = 0.217, sign 0.768, event R2 0.730, MAPE(V) 15.3 %; full field set calm R2 = 0.779, sign 0.862, event R2 0.904, MAPE(V) 10.1 %. Sources: reported_PE ~ k*P/V_bar with k ~ U(14, 22) so sd(log k) = 0.12 ~ sd(x) = 0.13 (R2 ~ 0.5 from P/E alone, predicted verbatim in envplan_coherence.md item 42); sentiment mean 0.6 tanh(2x); volume +1.2|x|; analyst F = V e^u. The published selectivity (+0.11 R2) is small only because the price-only baseline was already saturated by the anchor. Fix: widen or time-vary k; make sentiment load on returns only (Tetlock is sentiment-returns, not sentiment-mispricing); drive volume by |r| and turnover; report selectivity against a level-free price control; keep the absolute gate and report where it fails. Severity HIGH.

**4. Rare jumps enter x, not V, and give the "flat" control a persistent negative mispricing (E[x] ~ -0.10).** `generator.py:150-152,184`; pull rate mu*phi = 0.0046/day so the stationary mean is ~ -0.0004/0.0046 ~ -0.09. Measured (30 seeds): flat mean x = -0.100, median -0.068, P(x < 0) = 0.70, 74 % of resolvable flat steps undervalued; day-1 x mean -0.076; without jumps mean x = -0.018. Crash: 84 % of resolvable steps undervalued. The "no-event" control is a systematically cheap asset; the oracle says "buy" three times out of four in flat, so a persona sitting at its band-low edge beats always-hold. Persona effects on "buy the dip" behaviour are confounded with an undocumented generator bias. Fix: put jumps in V or make x-jumps mean-zero with negative skew; test E[x_1] ~ 0. Severity HIGH/MEDIUM.

**5. The sustained-bull control is a different stochastic process, and rejection sampling selects its quietest 60 %.** `events.py:33,68-70` (d_t = -0.15 x, half-life 4.6 d vs 150 d elsewhere); `generator.py:211-215` (band [-0.10, 0.15]). Measured (30 seeds): ACF1(r) -0.025 vs +0.024 flat; 20-day return sd 0.044 vs 0.080; daily sd 0.0148 vs 0.0181. First-attempt paths: 33 accepted / 27 rejected; accepted daily sd 0.0147 vs rejected 0.0240. The team's own scenario-discrimination audit recalls sustained-bull days at 82 % from price alone. R1-D5 removed the x0.25 variance multiplier for exactly this reason and the anchoring plus selection re-introduce it. Fix: same x process as flat (d_t = 0); enforce "no bubble" via V-based criteria or a wider band; publish accepted-vs-rejected volatility. Severity HIGH.

**6. The phase multiplier enters implied volatility deterministically; IV is a one-day phase-transition marker.** `garch.py:69-93` (sigma2 = m(phase) h), `:95-111` (forecast uses m(phase) for the whole horizon), `observables.py:154`. Measured (30 crash + 30 bull seeds): log-IV jump at deterioration->panic +0.62 (x1.87), panic->stabilisation -0.64, blow-off->post-top +0.33, calm->deterioration/mania +0.15; calm day-to-day sd of log IV = 0.089, so z ~ 7 at the panic transitions. `observables.py:3-5` claims every field is "NEVER of the phase label". L2b's 4-class accuracy cannot see a change-point leak. Fix: apply the multiplier to omega with a ramp, or drive IV from rolling realised variance plus noise. Severity HIGH.

**7. The IV stress-premium uses a full-path (past + future + burn-in) quantile: look-ahead.** `observables.py:152` (`thr = np.quantile(sigma2_state, 0.9)` over all 460 days). 9 % of benchmark days get a different flag under a past-only threshold; 75 % of flagged days in crash paths are panic days. Fix: expanding-window or fixed threshold. Severity MEDIUM.

**8. "Published form" holds only in calm phases; in events x is a scripted target plus noise, and the mania drift is at its cap on ~40 % of mania days.** `events.py:97-127` (error correction), FW pull at x = -0.3 is 0.00034/day vs scripted steps ~0.01/day; `events.py:152-160` (g capped at 0.012). Measured: 38 % of mania days at the cap; drift constant so exponential, not super-exponential, for most of the mania. Fix: draw kappa and mania length jointly so the cap rarely binds; test convexity on the pre-cap segment; describe the event-phase model as "scripted target path + GARCH noise". Severity MEDIUM.

**9. Burn-in (260 d) is adequate for the default engine but not for the index/pruna sensitivities** (fw_index half-life ~580 d: 0.45 half-lives, x_1 sd ~ 0.6 sigma_stat). Fix: burn-in >= 3 half-lives per engine or draw x_1 from the stationary distribution. Severity LOW/MEDIUM.

**10. Rejection sampling redraws the entire schedule per attempt; the hazard was calibrated with a rejection penalty** (`calibrate_hazard.py::score` adds 5 max(0, attempts - 1.05)). Severity LOW/MEDIUM.

**11. The blow-off label is a calendar label in un-topped runs** (`events.py:198-211`, last third of the mania run; 58 % of bull runs un-topped, blow-off starts on day 153-170). Fix: dynamic criterion, or report only for topped runs. Severity MEDIUM.

**12. Recorded bubble top is off by one step** (`events.py:141-180`; realised peak at top_day + 1, x_top understates it by ~g). Severity LOW.

**13. Two different tail processes (t5 on V, GARCH-t + Gaussian jumps on x) produce a scale-mixture return distribution; tested at a horizon with no power (see 14).** Severity LOW.

### B. Scale and horizon

**14. Checklist "fails" on items 2, 3, 6, 13 are power artefacts of 200-day windows, misdiagnosed as structural.** Same generator, 20 flat seeds: LB|r| p < 0.01 share 35 % at T = 200 vs 95 % at T = 800; kurtosis > 1.5 share 60 % vs 100 % (median 2.4 vs 9.0). A real S&P 500 200-day window would fail the same tests. Fix: per-item power analysis; report at the horizon with power >= 0.8 and separately at the benchmark horizon. Severity MEDIUM.

**15. Items 4 and 9 are evaluated at T = 800, a horizon the benchmark never runs; within a 200-day run x is nearly a constant offset and the oracle decision is one bit per run.** 200-day windows: ACF 0.951, half-life 14 d, sd 0.053 vs T = 800: 0.9905 / 72 d / 0.128. Measured (30 seeds, ISFJ): oracle target changes per run median 0 (flat), 1 (crash), 1 (bull); 77-91 % of resolvable steps sit at one band edge. "Mispricing persists so the flat market contains decisions" is true in the sense that each run has one decision (which side of the band), fixed by x_1. The benchmark measures a one-shot side call, not judgement over time. Fix: report oracle switches per run; theta relative to within-run sd; shorter x half-life or longer T. Severity MEDIUM.

**16. Item 10's partial-R2 criterion cannot be met by construction of the statistic** (3-level factor vs MDD with ~9 pp panic noise per path). A7 changed the statistic but kept an unattainable threshold. Fix: effect-size criterion (spread with CI). Severity LOW/MEDIUM.

### C. Leakage audits

**17. L1 tests only contemporaneous k x single-field inversions and passes any candidate worse than price itself** (`leakage_audit.py:129-171`). With V_1 = 100 known, k_hat = 100 PE_1/P_1 identifies the hidden multiple to ~7 %, after which trailing EPS tracks V with a lag. Fix: per-path fits, temporal inversions, multi-field regression; randomise the start price. Severity MEDIUM.

**18. The L2 "price-only" control includes the price level, so the audit attributes the anchor leak to dynamics** (`leakage_audit.py:59`, PRICE_ONLY_KEYS contains price, SMA20, SMA50). Fix: level-free control. Severity HIGH (the audit design produced the wrong narrative).

**19. L2b measures 4-class accuracy; a change-point leak of z ~ 7 in one field passes it.** Fix: onset-detection audit (predict "phase changed today"; report timing error). Severity MEDIUM.

**20. The calendar is a deterministic phase clock in the population the benchmark actually runs.** `runner_v2.py:36` (ordering = "setup_first"), no ordering factor in arms_v2, "Day-N" always rendered. Measured (40 seeds, setup_first): P(calm | day <= 50) = 1.000 for crash and bull; P(non-calm | day >= 170) = 1.000; day-only macro accuracy 80.4 % (crash), 87.2 % (bull) vs majority 40 %/54 %. Item 15's 64.8 % is computed on a mixed set (event_first, phase_free, flat) that no LLM run uses. The whole "time vs phase" strategy is only valid if the mixed orderings are run; they are not. Fix: put ordering in the grid, widen the setup range, and/or stop rendering the day index. Severity HIGH.

**21. `days_since_eps_announcement` is a second calendar** (quarter ends at fixed days 63/126/189 for every seed). Fix: random quarter phase per seed. Severity LOW/MEDIUM.

**22. The L5 "observables oracle" learns the start-price anchor across seeds** (FEATURE_KEYS includes price; fit pooled across seeds; no CIs; 10 eval seeds). Level-free GBT sign accuracy 0.71 vs 0.945 with levels. Severity MEDIUM.

**23. The "game is playable" conclusion is drawn from an attacker with information the stateless agent does not have.** Severity MEDIUM.

### D. Observables

**24. Analyst fair-value error is 0.335, not the documented 0.15 (code bug).** `observables.py:130` (rho = 0.95 applied per 5-day update AND innovation scaled by sqrt(5)). Stationary sd 0.15 sqrt(5) = 0.335; measured 0.333. Documented as 0.15 in observables.py:11, TABLE2_DEFINITIONS, the spec, slide 5. Fix: rho_weekly = 0.95^5 with innovation sd 0.15 sqrt(1 - rho_w^2), or drop the sqrt(5). Severity MEDIUM/HIGH.

**25. Sentiment is a monotone function of the hidden state with no empirical anchor, and the "Tetlock-sized" predictive component is undetectable.** `observables.py:70` (m = 0.6 tanh(2x) + 0.3 tanh(ret20/0.15)). Measured flat corr(s_{t-1}, r_t) = +0.006 vs ~ +0.047 implied by b_pred; item 12's "lagged corr equals configured b_pred" is not implemented. Tetlock 2007 links pessimism to returns; nothing cited links a sentiment index to log(P/V). The b_pred = 0 control arm is a null manipulation. Severity MEDIUM.

**26. Volume level is a direct read of |x|** (`observables.py:142-143`, +1.2|x|, stationary mean shift 3.4|x|). Karpoff-type evidence is volume-|r|, not volume-|mispricing|. Severity MEDIUM.

**27. IV is a noiseless read of the latent GARCH state; the multi-asset IV premium is inconsistent across assets** (`synthetic_market.py:152` passes unscaled sigma_V for the x0.5 asset; asset-2 IV/RV 1.06 vs asset-0 1.28). Severity LOW/MEDIUM.

**28. Quarterly EPS inverts k when V_1 is known and reveals V growth over quarters; not audited.** Severity LOW/MEDIUM.

### E. Harness and evaluation

**29. MCR is a band-adherence metric with a one-bit direction call attached; it does not measure rationality over time.** Probe: always-hold at centre 0.10-0.14, constant-edge policies 0.06-0.09, level rule 0.005-0.014, pilot Gemini 0.15-0.40 (worse than doing nothing). MCR tracks band-MAS almost one-for-one in the pilot. Fix: decompose into band violation and within-band directional agreement. Severity MEDIUM/HIGH.

**30. MCR normalisation: code and documentation disagree; the published pilot "norm_mcr" is against constant-mix, not the oracle.** `metrics_v2.py:166-198` (lower-better: ceiling = constant_mix ~ 0.10, floor = worst trivial policy) vs `tools/report_v2.py:130` and PILOT_NOTES ("ceiling = mandate-conditional oracle, floor = best trivial policy"). Pilot ISFJ static flat: mcr 0.284, norm 0.693 = (0.284 - 0.8)/(0.10 - 0.8), i.e. 1.0 means "as good as constant mix". Severity HIGH (mislabelled published numbers).

**31. Baselines are rebuilt from run metadata without n_assets, engine, b_pred or env_config** (`tools/report_v2.py:53-59`). For any non-default factor the agent and its floor/ceiling are on different paths. Severity MEDIUM.

**32. The t = 0 gate under start-at-target is ill-posed and cannot pass.** `tools/report_v2.py:116-117` passes Delta C_1 = C_1 - C_0 as C1 into the gate, which checks ordering and band membership; a persona-consistent agent that stays at its centre yields Delta C_1 ~ 0 for all personas, so KW p ~ 1, band_hit = 0 (pilot: 0.0), AUC ~ chance. Models are excluded on this gate. Fix: gate on C_1 level; or common-start only. Severity HIGH.

**33. Salience shares are not identified under start-at-target** (persona one-hot, directive label and Start_Cash_Share collinear within the memory/static arms; promised bootstrap CIs not implemented). Severity MEDIUM.

**34. Execution timing: under next_open the logged Cash_Share is pre-trade, mechanically penalising that sensitivity by a day.** Severity LOW.

**35. Stateful memory arm: the "distance to mandate" covariate is wrong and the context contains 20 mandate copies** (`stateful_agent.py:61,88,102`). Token budgets differ between stateful_static and stateful_memory by 20x the mandate length. Severity MEDIUM.

**36. Placebo length/imperative matching is asserted, not tested.** Severity LOW.

**37. Parse fallbacks enter the stateful history as the model's own prior turn.** Severity LOW.

**38. Trader band hard-coded to (0.4, 0.6) in the runner while metrics treat TRADER as band-free.** Severity LOW.

### F. Targets

**39. The cash bands are inconsistent with the environment's own risk-return, and "cash" silently absorbs bonds while dividends are shown but never paid.** The Merton table uses ERP 4.3-6 %/sigma 16-20 % (an index) whereas the environment is a single stock with sigma ~ 28 %/yr, price-only drift 6.5 % and no dividend cash flow (portfolio_v2 has no dividend accrual). With the environment's parameters gamma = 3-4 gives 21-28 % equity (cash 0.72-0.79, the conservative band), gamma = 8-10 gives 8-10 % equity (cash 0.90-0.92, outside the band). Fix: derive bands from the environment's (mu, sigma) or state plainly they are practitioner conventions; pay dividends into cash or remove the field. Severity MEDIUM.

**40. The JFE evidence does not transfer to MBTI personas, by the team's own analysis** (env_research_targets.md 1.4: MBTI omits Neuroticism; INTJ/ENTJ near-identical under JFE). Severity MEDIUM.

### G. Multi-asset

**41. All assets share the same scripted event (start, D_V, delta, kappa), so cross-asset structure is the script plus noise; vol scale and rho have no provenance; the existence-rule oracle rewards correlated noise.** Measured (crash, 10 seeds): pairwise corr of x 0.46-0.65; spread-resolvable share 0.87 from noise; all assets start at 100 (anchor inherited). Severity MEDIUM.

### H. Statistics

**42. Mixed-model specification is wrong for the design** (`stats_v2.py:119`: variance components nested within Model although seeds are crossed with models; random intercepts only although random slopes were promised; `:156` model:phase nested within run). Severity MEDIUM.

**43. Run-level bootstrap and CI-derived p-values ignore clustering by model and seed.** Severity MEDIUM.

**44. Circular-shift null with 8 windows has 7 distinct values per run.** Severity LOW.

**45. Multiplicity is controlled only within (persona, scenario, arm) across 7 metrics, not across the ~840-contrast family.** Severity MEDIUM.

**46. Salience windows (25 d) with seed-blocked CV on <= 5 seeds; no CIs.** Severity LOW/MEDIUM.

### I. Reproducibility and freezing

**47. The v2 generator is not frozen: no hash test for envs/v2/*.py or params/*.json; the provenance code hash covers only the facade** (`simulation/provenance.py:98`). Severity MEDIUM.

**48. Silent overrides and stale numbers**: hazard.json overrides HAZARD_H0/B and G_MAX (events.py:32 still says 2 %/day); fw_single silently falls back (renaming the REJECTED json would switch the engine to a ~580 d half-life); docstring "~90 d" vs constant 150 vs decision log 120 vs report phi 0.463; two documents still list sustained-bull multiplier 0.25. Severity MEDIUM.

**49. The SMM calibration tool normalised the innovation weight after simulating, so the rejected fit was computed on a mis-scaled model; the J-profile uses a diagonal proxy weight, not the bootstrap W.** Severity LOW/MEDIUM.

**50. Tests are structural, not statistical, and one is a test-that-must-fail** (strict xfail on the pre-registered gate: a green CI now requires the leak); CI audits at 8 seeds; two legacy tests are broken. Severity LOW/MEDIUM.

### J. Other

51. Unsynchronised module-level pilot cache (benign). LOW.
52. Common factor mixes two standardised t5 draws; the sum is not t5. LOW.
53. Crash V drift is 0 after deterioration, contradicting the drift anchor used elsewhere. LOW.
54. Pre-registered pieces missing from code: held-out-scenario L2 split, L3 LLM probe, bootstrap CIs on salience shares, random slopes. LOW/MEDIUM.
55. Item 5 (GARCH persistence) is fitted on regime-switching paths, inflating alpha + beta. LOW.

## Top 10 things to fix first

1. Randomise the start price per seed and re-run every audit with a level-free price control (2, 18, 22).
2. Face the field leak the anchor was hiding (3): P/E multiple range, sentiment ~ x, volume ~ |x|, analyst F ~ V.
3. Fix or rename the mispricing engine (1): price_scale, dead switching, slide-6 provenance; add ar1 to the sensitivity table.
4. Run the orderings the audits assume (20): event_first/phase_free in the grid, or stop rendering the day.
5. Remove the IV phase step and the look-ahead threshold (6, 7); add an onset-detection audit (19).
6. Repair the controls: jumps out of x so E[x] = 0 in flat (4); sustained bull on the same x process with published selection effects (5).
7. Correct the metric layer: MCR normalisation labels (30), MCR decomposition (29), the Delta C_1 gate (32), baselines on the cell's actual path (31).
8. Fix the analyst-error bug and every document quoting 0.15 (24); reconcile half-life / multiplier / g_max numbers (48).
9. Freeze v2 properly (47): hash envs/v2/** and params; statistical regression tests (E[x], sd(u), IV continuity, n_f distribution).
10. Redo the checklist with a power analysis per item (14-16); report T = 200 numbers as "what the agent experiences".

Two blunt statements: the environment as built is solvable by "is the price above or below 100" in three of four scenarios, and the one scenario where it is not is the one where the published observables-oracle gap is largest; that is the anchor leak, not "price dynamics". And the fundamentalist/chartist model in the talk is not the model in the code; the code runs an AR(1) with a constant weight and a units bug.
