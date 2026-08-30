# Coherence review of "Synthetic Environment v2, Research-Grounded Reimplementation Plan" (v2, 22 Aug 2026)

Scope: internal logic, arithmetic, cross-section consistency, and correctness of code claims against envs/synthetic_market.py, simulation/portfolio_tracker.py, simulation/runner.py, agent/static_agent.py, agent/memory_agent.py, agent/personas/mbti_profiles.json. Citations not checked.

Severity: BLOCKING = an implementer following the text as written would build something that contradicts another part of the plan or cannot pass the plan's own exit criteria; SHOULD-FIX = wrong or unsupported as stated, fixable locally; NIT = clarity/consistency.

## A. Arithmetic and quantitative consistency

1. **Sec 3, "Crash: panic discount delta" row — MDD formula is wrong; the numbers match a different formula.** Written: MDD ≈ (1 − delta)(1 − D_V) = −52/−40/−28 % for delta 0.60/0.75/0.90. With D_V = 0.20, (1 − delta)(1 − D_V) gives 0.32/0.20/0.08. The quoted −52/−40/−28 come from MDD = 1 − delta(1 − D_V) (1 − 0.48, 1 − 0.60, 1 − 0.72). SHOULD-FIX: replace the formula with MDD ≈ 1 − delta(1 − D_V) and state D_V = 0.20 as the illustration value.

2. **Sec 3 crash row vs checklist 20 — delta = 0.90 seeds will fail the "crash MDD −25 to −65 %" band for a third of D_V draws.** With MDD = 1 − delta(1 − D_V) and D_V ~ U(0.10, 0.30), delta = 0.90 gives MDD 19–37 %; MDD ≥ 25 % needs D_V ≥ 0.167, so ~1/3 of delta-0.90 seeds (~11 % of crash seeds) sit below the band before noise. Also the "regress MDD on delta, R² > 0.7" criterion is marginal: D_V variance (sd 0.058 × delta) plus GARCH path noise (sd ~5–8 pp) against a delta-driven sd of ~0.10 gives R² ≈ 0.6–0.8. SHOULD-FIX: either lower the band floor to ~−15 %, shrink the D_V range, use delta ∈ {0.55, 0.70, 0.85}, or pre-register partial R² of MDD on delta controlling for D_V; make the rejection criterion (item 17) consistent with whichever is chosen.

3. **Sec 3 "Crash: panic discount delta" row says panic length U(15, 60) d; Sec 2.1 Regimes block and Sec 3 "Phases" row say L2 crash U(15, 70).** NIT: pick one.

4. **Sec 3 "Crash: volatility" row — "< 40 percent by end" is unattainable given the stabilisation omega multiplier.** Base unconditional sigma 1.8 %/day = 28.6 % annualised; stabilisation omega × 2 gives unconditional sigma 2.55 %/day = 40.4 % annualised, and the GARCH path decays toward that level from above with half-life ln 0.5 / ln 0.98 ≈ 34 days. So the steady state itself violates "< 40 %", and short resolution windows (L1 up to 0.55 T plus a 70-day panic leaves ≥ 20 days) never get there. SHOULD-FIX: set stabilisation multiplier to ≤ 1.5 (≈ 35 % annualised) or change the criterion to "below 50 % by end / below panic level by ≥ 30 %".

5. **Sec 3 "Implied volatility" row and checklist 13 — "IV − RV +3 to +8 pts" cannot hold in panic with a multiplicative premium.** Panic: sigma ≈ 57 % annualised × 0.35 premium = +20 pts. Flat: 28.6 % × 0.20 = +5.7 pts (passes). SHOULD-FIX: make the band phase-specific (flat +3 to +8, panic +10 to +25) or make the premium additive.

6. **Sec 3 "Mispricing form" / checklist 9 / "Daily vol" row — the flat-market targets are jointly infeasible.** Price return r = Δlog V + Δx. With sigma_V = 0.9 %/day and total price sigma 1.8 %/day, the mispricing innovation must contribute sqrt(1.8² − 0.9²) ≈ 1.56 %/day. For AR(1) x with phi = 0.98 (half-life 34 d), stationary sd = sigma_eps / sqrt(1 − phi²) ≈ 1.56 % / 0.199 ≈ 7.8 %, outside the "sd in flat 2 to 6 percent" band; phi = 0.995 gives 16 %. Conversely, sd 2–6 % with phi 0.98 implies total price sigma 1.0–1.5 %. SHOULD-FIX: pick two of {sigma_V, total sigma, sd_x, half-life} and derive the others; e.g. sigma_V 1.2 %, sd_x 5–8 %, half-life 30–40 d, total ≈ 1.8 %. Also resolve whether the GARCH layer is *the* source of the mispricing innovation variance or an additional layer (see item 13).

7. **Checklist 9 — "phi 0.95 to 0.995" and "half-life 20 to 60 d" are not the same band.** phi 0.95 → 13.5 d; phi 0.995 → 138 d; half-life 20–60 d ↔ phi 0.966–0.989. NIT: state one criterion (half-life) and derive the phi band from it.

8. **Sec 2 FW parameters vs checklist 9 — the recommended Franke–Westerhoff calibration cannot pass the plan's own mispricing-persistence test.** In FW the fundamentalist pull on x is mu × n_f × phi ≈ 0.01 × 1 × 0.12 = 0.0012/day, i.e. phi_AR ≈ 0.9988 and half-life ≈ 580 days (FW's misalignment swings last years, consistent with Shiller/Poterba–Summers, which the plan cites with transitory sd 15–25 %). Checklist 9 demands half-life 20–60 d and sd 2–6 %. BLOCKING for E1's exit criterion ("items 1 to 6, 9 to 11 ... pass"): either (a) say explicitly that FW parameters will be re-estimated/rescaled to hit the 20–60 d band and that the published J-test provenance (Sec 2 option C, "p = 32.6 percent") therefore no longer applies, or (b) widen item 9 to the FW-implied regime (half-life 100–500 d, sd 10–25 %) and accept the consequences for flat-market resolvability (which then rises — also update L4's "flat coverage stated honestly").

9. **Sec 3 "Sustained bull" row — mu_V × 3 does not deliver "final return +30 to +80 percent".** 3 × 0.00025 × 200 d = +0.15 log (≈ +16 %), sd of log V over 200 d ≈ 0.9 % × sqrt(200) ≈ 12.7 %; P(final ≥ +30 %) ≈ 19 %. SHOULD-FIX: mu_V × 8–10 (≈ 0.002–0.0025/day) for a +50 % median, or change the band to +5 to +40 %. (Also the plan never states T; see item 41.)

10. **Sec 3 "Bubble: value" row — "V end/start in [1.0, 1.3]" fails ~35 % of seeds by construction.** With mu_V 0.00025 and sigma_V 0.9 %, log V_T ~ N(0.05, 0.127²); P(V_T < V_0) ≈ 35 %. SHOULD-FIX: test the cross-seed mean, or widen to [0.8, 1.35].

11. **Sec 3 "Bubble: run-up" row — kappa and x* are drawn independently of the mania duration, so many seeds cannot reach x* inside the mania window.** If dx/dt = kappa·x (the super-exponential-in-P reading), reaching x* = ln 2 ≈ 0.69 from x_0 ≈ 0.03 takes ln(0.69/0.03)/kappa ≈ 63–157 days for kappa ∈ [0.02, 0.05], versus mania ~ U(40, 100). If dx/dt = kappa (linear), it takes 14–35 days and is not super-exponential. SHOULD-FIX: state the functional form and derive one of {kappa, x*, mania length} from the other two.

12. **Sec 3 "Sentiment" row — sign of the predictive default contradicts the cited anchor.** Text: "1 sd of s_t moves E[r_t+1] by minus 5 bp ... per Tetlock"; the same cell says Tetlock is "1 sd pessimism gives minus 5.5 bp". s is optimism-signed (mania +0.4, panic −0.6), so +1 sd of s should move E[r_t+1] by +5 bp. SHOULD-FIX: flip the sign. Additionally the validation "corr(s_t−1, r_t) equals the configured b_pred" will fail as stated because phase means (panic −0.6 with negative returns, mania +0.4 with positive returns) induce a far larger lagged correlation than b_pred; compute it within phase / partialled on phase, or on flat runs only.

13. **Sec 2.1 blocks 2–3 and Sec 3 — three volatility sources are specified without saying how they combine.** V has sigma_V (0.9 %), the FW recursion has its own sigma(n)·eps (calibrated sigma_f 0.59, sigma_c 1.9), and "GJR-GARCH(1,1) on the price log-return" is set to unconditional 1.8 %. If the GARCH conditional sigma replaces FW's sigma(n), FW's volatility-clustering mechanism (regime switching) and calibration are discarded; if it is layered on top, total sigma ≈ sqrt(0.9² + 1.8² + FW) > 2.2 %, breaking the "1.4 to 2.2" band. BLOCKING for implementation: specify r_t = Δlog V_t + Δx_t with Δx_t's innovation = GARCH sigma_t × t(5) (and drop FW's sigma(n)), or specify GARCH only on the x-innovation, and recompute the targets in item 6.

14. **Sec 3 "Crash: volatility" says omega × 3 to 6 in panic; Sec 2.1 block 3 says 4.** NIT: one number with a sensitivity range.

15. **Sec 11.3 vs Sec 1 item 11 — the trivial-policy envelope and the "8.8 percent gap" do not match.** Sec 1: buy-one-share-then-HOLD 99.7, always-HOLD 79.8, random 66.9, reported arms 85.9 / 78.4 "inside that envelope" (66.9–99.7). Sec 11.3: "inside the trivial-policy envelope (79.8 to 99.7); the 8.8 percent gap". 78.4 is below 79.8, so it is outside the envelope as 11.3 states it, and 85.9 − 78.4 = 7.5, not 8.8. SHOULD-FIX: use the same bounds (66.9–99.7) and the same gap in both places.

16. **Sec 4.2 Merton shares — the quoted ranges hold only at one end of the stated parameter ranges.** With ERP 4.3–6 % and sigma 16–20 %: gamma 8–10 gives 11–29 % (text: 15–25); gamma 3–4 gives 27–78 % (text: 40–60); gamma = 2 gives 54–117 %, so "gamma ≤ 2 gives ≥ 80 percent" is false at ERP 4.3 %/sigma 20 % (54 %). SHOULD-FIX: state the parameter pair used (the Vanguard 6 %/17.5 % pair reproduces 20–25 / 49–65 / 98) or give ranges.

17. **Sec 4.1 vs Sec 4.4 — the JFE spread is quoted as 0.06–0.12 in 4.1 and 0.07–0.12 in 4.4.** NIT. Also the "ceiling 9.7 pp (total)" is not derivable from the stated inputs (sum of |coef| = 4.79 pp/sd; P10→P90 ≈ 2.56 sd gives 12.3 pp with all five traits, 10.2 with the three significant ones). NIT: show the arithmetic.

18. **Sec 4.1 conclusion is used as an argument against v1 but applies equally to v2.** "The paper's spread is 0.80, seven to thirteen times larger [than JFE]" — the recommended v2 spread (0.80 − 0.10 = 0.70) is six to twelve times larger. The plan does treat JFE as sensitivity only, but a reviewer will read the 7–13× line as the reason to change the targets. SHOULD-FIX: state that the objection to v1 is the 0 %-risky endpoint and the Markowitz misattribution, not the JFE magnitude, and that v2's spread is practitioner-anchored and equally far from JFE by design.

19. **Sec 3 "Volume" row — the |r| loading of 0.15 puts the Spearman target (0.2–0.5) at its lower edge in flat runs.** sd contribution 0.15 × 0.6 ≈ 0.09 vs innovation 0.30 → corr ≈ 0.2 before phase effects. NIT: use ≥ 0.25 or accept pass-by-event-scenarios only.

## B. Design logic: hybrid generator (Sec 2, 2.1, 3)

20. **Sec 2 option C / Sec 2.1 block 2 vs Sec 3 event rows — the event-phase mispricing is scripted, not FW-generated, but the plan claims FW provenance for the decoupling.** Block 2 says regimes "shift alpha_0 toward chartism (mania) or inject a fundamental shock plus chartist dominance (panic)"; the crash row then treats delta as a parameter with a closed-form MDD and the bubble row prescribes a drift kappa to a target x*. Shifting alpha_0 in FW raises chartist weight but (i) does not set a direction (chartists extrapolate whatever the last move was), (ii) with mu = 0.01 and chi = 1.5 the momentum term is 0.015 × n_c per day, far too weak to produce a +60–150 % run-up in 40–100 days, and (iii) cannot target a specific panic discount delta. So either delta and x* are outcomes (then they are not factors and rejection would be heavy), or x is driven by a scripted drift in event phases (then Sec 10's "decoupling generated by a calibrated fundamentalist-chartist process" and the novelty claim (i) overstate; FW governs only calm). BLOCKING for the design write-up: state precisely which phases are FW-dynamic and which are scripted in x, and how delta/x*/kappa are imposed (e.g. as a time-varying p* or as an additive drift on x with FW noise).

21. **Sec 2 "V independent of agent actions" — true, but the stronger assumption (P independent, zero price impact) is the one that needs stating.** Using a market-maker equation as a pure time-series model while the LLM is a price-taker is consistent, but Sec 2/10 only assert V-independence. NIT: add "P is exogenous: the agent has zero market impact; the FW 'market maker' is a generative model, not a counterparty".

22. **Sec 2.1 Regimes "drawn from a Markov chain" vs Sec 13.1 "durations as design choices ... or a fitted chain".** What is specified (fixed order calm→event→resolution with uniform durations) is a semi-Markov schedule with no transition probabilities. NIT: call it a scheduled regime sequence, or specify the chain.

23. **Sec 2.1 Regimes and Sec 3 "Bubble: run-up" — "mania U(40, 100)" and "probabilistic top P = 0.5 inside horizon" are two different top mechanisms and the plan does not reconcile them.** With T = 200, L1 ~ U(50, 110) and mania ~ U(40, 100), the mania ends in-horizon for ~98 % of seeds; un-topped seeds must therefore come from a separate Bernoulli/hazard draw, in which case the mania-duration draw does not apply to them. SHOULD-FIX: define the top as a hazard (e.g. GSY-style rising in x) or as a Bernoulli flag that suppresses the post-top leg, and say what happens to mania length in un-topped seeds.

24. **Sec 2.1 Regimes state set {calm, mania, panic, sustained bull} omits blow-off, deterioration, stabilisation, which the GARCH multipliers, sentiment means and volume shifts all use; "resolution", "stabilisation" and "post-top leg" name the same slot.** NIT: one phase taxonomy, used everywhere (also needed to define L2b's class set).

25. **Sec 3 "Phases" row — the phase/time thresholds (corr(day, phase) < 0.9; classifier from day alone < 80 %) are near what the draws produce; only the mirrored orderings break the clock.** Days 1–50 are always phase 1; late days are mostly resolution. NIT: state that the test set includes mirrored and phase-free runs, else expect marginal failure.

26. **Checklist 1 (no return autocorrelation, |ACF(1)| < 0.15 "in all scenarios") conflicts with the scripted drifts in event phases.** Super-exponential mania drift, a front-loaded panic and phase switches induce positive return ACF. SHOULD-FIX: run item 1 on flat/calm phases or on phase-demeaned returns, and say so.

27. **Checklist 4 (power-law decay of ACF|r|, b ∈ [0.2, 0.6]) is not a property of the chosen generator and is unestimable on 200-day paths.** GARCH(1,1) gives exponential decay; ACF at lags > 20 on 200 points is noise. NIT: drop, or run only on T = 800 paths and treat as descriptive.

28. **Sec 3 GJR parameters sit below the plan's own anchors** (alpha 0.04 vs 0.05–0.10; gamma 0.08 vs 0.10–0.21). NIT: justify (single-stock) or align.

## C. Initial allocation, action semantics, MAS (Secs 1, 2.1, 3, 4, 8)

29. **Sec 2.1 block 6 / Sec 3 / checklist 18 — "report MAS relative to t = 0" and "MAS at t = 0 equal across personas" are vacuous under the primary design.** Starting at the band centre makes C_0 = centre, so MAS_rel ≡ point-MAS and MAS(0) = 0 for every persona by construction. Checklist 18's first criterion tests nothing. SHOULD-FIX: make 18 a unit test that the start allocation was applied plus the "effect survives both starts" criterion; define relative MAS only for the common-0.5 design. Also 4.5 uses |C_t − C_1| while 2.1/3 use t = 0: pick one index.

30. **Sec 2.1 block 6 — the primary start design introduces a new confound the plan does not acknowledge: personas start at different equity exposure in an identical market.** ENTJ (90 % equity) and ISFJ (20 %) then have mechanically different drawdowns, returns, RG denominators and always-HOLD/buy-and-hold floors. Any cross-persona comparison of return-type metrics under the primary design is a comparison of starting exposures. SHOULD-FIX: (a) state that all baselines (always-HOLD, buy-day-1, random, floors) are computed from the same start allocation as the cell; (b) restrict cross-persona return/RG comparisons to the common-start design; (c) add this to the casualties list.

31. **Sec 8 normalisation and the "MAS floor" — under start-at-target, always-HOLD (do nothing) is near-optimal on band-MAS, so the floor equals the ceiling.** The constant-mix baseline is called an "MAS floor" (it is the ceiling: MAS = 0), and the normalisation (agent − floor)/(oracle − floor) is undefined for MAS when floor = best of {always-HOLD, ...} ≈ 0. It also means adherence rewards inaction, interacting with the flat-market "trading without signal" finding and the zero-trade degeneracy audit. SHOULD-FIX: define floor/ceiling per metric; for MAS use random or always-BUY/SELL as floor and constant-mix as ceiling; note the inaction incentive.

32. **Sec 4.6 gate under the primary design is circular.** Persona is decodable from C_1 "alone" because C_0 encodes persona; the day-1 ordering cons > bal > aggr and AUC ≥ 0.8 pass by construction. The plan notes the meaning changes but still lists the gate as pre-registered for v2 without restricting it. SHOULD-FIX: pre-register the gate on the common-start design only (or on ΔC_1 = C_1 − C_0 under the primary design).

33. **Sec 11.3 casualty "bidirectional pattern shrinks under start-at-target if A1 is the driver" is confounded with A2.** A2 (target-share action) removes the ratchet simultaneously. SHOULD-FIX: the A1 test must hold the action interface at v1 (the flag exists for this) — make the factorial A1 × A2 explicit.

34. **Sec 7 swapped-mandate and no-mandate arms — start allocation undefined.** Under "start at own target", which target does an ENTJ-personaed agent carrying the ISFJ mandate start at, and where does the no-mandate trader start? SHOULD-FIX: specify (persona target for B5; common 0.5 for B6 and as the secondary design for all).

35. **Sec 4.4 ENTJ point C_ideal "0.10 (0.20 acceptable)" conflicts with "start at the centre of its own band" and with band-MAS centred at 0.10.** NIT: fix the point at 0.10; 0.20 is the band edge.

36. **Sec 2 option D — "C_ideal becomes a band on the risky share" silently flips the convention (C_ideal is a cash share everywhere else).** NIT: keep cash-share convention or define both.

## D. Target-free salience measure (Sec 4.5) and Track B (Sec 12 D17)

37. **Sec 4.5 — the surrogate includes portfolio state, which absorbs persona over time and manufactures "decay".** Portfolio state is a function of the persona's own past actions; permutation importance of the persona dummy conditional on it falls as portfolios diverge, so S_persona(w) declining over w is expected even if the policy is time-invariant. Under the primary start design the effect is worse: window 1 has S_persona ≈ 1 by construction (start encodes persona). SHOULD-FIX: report the surrogate with and without portfolio state (or group persona + portfolio state as one importance block); run the decay analysis on the common-start design; include start allocation as an explicit feature.

38. **Sec 4.5 — seed dummies and rendered market features are collinear (seed × day determines the features), so importance splits arbitrarily between them.** SHOULD-FIX: drop seed as a feature; use seed for blocked CV.

39. **Sec 4.5 vs Sec 6 — "mandate salience decay = S_persona falling over w" is presented without the stateless-agent caveat Sec 6 makes.** For a stateless agent the decision function is identical at every t; a falling persona share can only reflect market features becoming more dispersed (event phases) or portfolio absorption (item 37). SHOULD-FIX: cross-reference Sec 6 and label the stateless-arm quantity "phase/portfolio re-weighting", reserving "decay" for the stateful arm.

40. **Sec 4.5 / E4 exit — "validated on the no-mandate trader (share near zero)" is ill-posed.** Within the no-mandate arm there is no persona dummy to have a share; pooled with persona arms, the no-mandate level is itself a dummy and may carry high importance. Also 4.5 uses a single "persona directive" factor, but the memory/swapped arms have two factors (persona text in system prompt, injected directive) — B5 is only answerable if both are in the surrogate. SHOULD-FIX: specify persona and directive as separate factors with the no-mandate trader as the reference level; validate with a label-permutation null (share ≈ 0) and O3 (share high).

41. **Sec 12 D17 — "promote Track B to primary: it is now the primary measurement".** Track B is a prompt condition (persona text only); the primary measurement in 4.5 is the target-free salience, computed in both tracks. NIT: reword.

## E. Leakage, phase clock, resolvability (Sec 5, Sec 3 earnings row, E2)

42. **Sec 5 L2 threshold (OOS R² of log(P/V) ≤ 0.30; sign accuracy ≤ 0.70 on resolvable steps) is incompatible with L4 (≥ 60 % resolvable in event phases), with "P/E informative", and with a playable fundamentalist mandate.** In event phases x ranges ±0.5–0.9; P/E = k·P/V_q with hidden k ~ U(14, 22) (sd of log k ≈ 0.12) plus 10 % EPS noise gives R² ≈ var(x)/(var(x)+0.0144+0.01) ≈ 0.8, and sign accuracy near 1 for |x| > 0.2. The analyst field F_t (u sd 0.15) gives R² ≈ 0.09/(0.09+0.0225) ≈ 0.8 on its own; to push it under 0.30 the error sd must be ≥ ~0.45, at which point F is noise. Pooled across scenarios the threshold cannot be met without removing valuation information, which makes ≥ 60 % resolvability pointless. BLOCKING for E2's exit criterion: set thresholds per scenario/phase (e.g. R² ≤ 0.30 in flat and calm; in event phases require R² < 0.9, MAPE of V ≥ 10 %, and no algebraic inversion), or define the leak test on V-level rather than on x.

43. **Sec 3 earnings row / E2 — "analyst fair value tuned to pass the L2 threshold" makes L2 a calibration target rather than a test.** SHOULD-FIX: fix F_t's error sd ex ante from the anchor (or drop F_t) and let L2 report; do not tune observables to the audit.

44. **Sec 5 L2b — "selectivity ≤ 10 pp" is in tension with the spec's label-driven phase means for sentiment (−0.6/−0.2/0/+0.4/+0.6), volume shifts and IV.** Non-price fields add phase information exactly where price is uninformative (calm vs deterioration; mania vs blow-off), and the ±5-day jitter leaves them as offset clocks. Volume is already "tied to x" (price-derived: good); sentiment and the GARCH omega multipliers are tied to the label. SHOULD-FIX: make sentiment's offset a function of x/returns rather than the phase label (or drop label-driven means), define the class set and window for L2b, and expect to report failure otherwise. Also "10 pp" is undefined without the number of classes and the price-only baseline.

45. **Sec 5 L1 — "no closed-form combination of shown fields equals V" is tested by a single V_hat without saying which inversion.** NIT: specify the best algebraic inversion (trailing EPS × k-prior, dividend × payout prior) used for V_hat.

46. **Sec 5 L4 / Sec 8 — theta "from generator noise" is never defined.** With the flat sd_x band unresolved (item 6) theta is unknown; it drives coverage, the V-oracle, and the unresolvable-step rule. SHOULD-FIX: theta = c × sd_x(flat) with c stated (e.g. 2), or a fixed 5 %.

47. **Sec 3 earnings row — trailing-4Q P/E needs four past quarters; with T ≈ 200 days (~3 quarters) the first three quarters have no trailing-4Q value unless pre-history is simulated.** NIT: specify a burn-in of ≥ 4 quarters before day 1 (also needed for SMA50/GARCH warm-up).

## F. Stateless/stateful identifiability (Secs 6, 7, 11.1, 12)

48. **Sec 7 B7 and Sec 12 B7 — "with a stateless agent the probe is near 100 percent by construction" is only true if the mandate is in the prompt.** Today the static arm's system prompt contains the persona financial extension but not the core mandate (agent/static_agent.py + mbti_profiles.json; memory_agent.py injects core_mandate); Sec 11.1 (2) itself says "today the static arm never contains it". A restatement probe on the current static arm would not be near 100 %. SHOULD-FIX: condition the statement on the mandate being present (memory arm now; all arms after 11.1(2)).

49. **Sec 6 — "the mandate sits at the same token distance on day 200 as on day 1" for the stateless agent.** Same issue: in the static arm there is no mandate; in the memory arm it is appended at the end each step. NIT: say "persona/mandate text".

50. **Sec 6 mixed model metric ~ phase + calendar_day + (1 | seed)** omits the model random effect that Sec 11.2 says is the effective unit. NIT: add (1 + phase | model).

## G. Evaluation layer and v1 factorial (Sec 8, 11.2, 13)

51. **Sec 8 item 6 / Sec 11.2 / E0 — "full factorial (metrics × environments × start designs) ... v1 runs are re-scored, not re-run".** The start-design axis cannot be applied to v1 data by re-scoring: v1 has only the 100 %-cash start. The v1 × start-at-target cells require re-running v1 (with the v1 generator and v1 interface) or are empty. Band-MAS and the target-free measure on v1 data are computable by re-scoring; start design is not. SHOULD-FIX: state the factorial as metrics × environments (re-score) plus start design × action interface on the v2 harness only, or budget a v1-generator re-run under the new start.

52. **Sec 8 — "Baselines inside the environment ... at zero API cost" includes the no-mandate trader, which is an LLM.** NIT.

53. **Sec 8 — V-oracle and mandate-conditional oracle are defined as BUY/SELL rules; with target-share actions their quantities, and what counts as a "BUY" for RG scoring of derived labels, are undefined.** SHOULD-FIX: define the oracle as a target share (0 or band edge) and define derived BUY/SELL/HOLD labels with a dead-band on Δshare.

54. **Sec 2.1 block 7 / Sec 8 costs — target-share action and costs are not connected.** Need: cost = 5 bp × |traded value|; whether "HOLD" means no trade or re-target (re-targeting daily pays costs); execution at P_t vs P_t+1 (the plan offers both, no default); cost visibility default (13.1 leaves it open). SHOULD-FIX: specify.

55. **Checklist numbering vs E1/E2 exit criteria — item 8 (gain/loss asymmetry) is in neither.** E1 lists 1–6, 9–11, 15, 17–20; E2 lists 7, 12–14, 16. NIT: add 8 to E1.

56. **Sec 1 — "Items 1 to 5 and 12 to 13 are the ones a reviewer can verify from the repository in minutes"; 14 and 15 are equally verifiable (Day-N string; mandate text).** NIT.

57. **Sec 1 item 8 wording — "the prompt omits the portfolio state it receives" reads as if the prompt lacks portfolio state; the code renders Cash and Holdings Value (static_agent.py lines 122–124), so the omission is in the paper's Table 2.** NIT: "Table 2 omits the portfolio state the prompt includes". (Other code claims in Sec 1 — line numbers, 40/30/30, 0.7/0.3 recursion, clips, 15× P/E, temperature 0.2, 6 of 16 fields — check out.)

58. **Sec 1 item 11 vs Sec 10 row "Baselines: FinPersona now none"** — the audit computed trivial-policy baselines (item 11), so "none" should read "none in the environment/paper". NIT.

59. **Sec 10 novelty (i) — "per-step ground truth that order-book simulators cannot provide for a single LLM agent" contradicts the same table's ABIDES row ("oracle").** ABIDES' exogenous oracle is per-step ground truth; what it lacks is agent-independence of the price path. SHOULD-FIX: narrow to "agent-independent price path with per-step ground truth".

60. **Sec 2 option C — "published provenance ... J-test p = 32.6 percent" is provenance for the index calibration the plan says it will not use (single-stock re-estimation or scaling).** NIT: say the provenance is for the functional form; the parameters are re-estimated.

## H. Sustained bull vs un-topped bull-trap (Secs 2.1, 3, 12 C9/E24, 13.1)

61. **The plan calls sustained bull "the clean un-topped population for C9" (12 C9, 12 E24) and in 13.1 offers "probabilistic top plus sustained-bull as the un-topped population, vs guaranteed top", while Sec 3/checklist 11 stratify bull-trap seeds into topped and un-topped.** These are different populations: un-topped bull-trap = unburst bubble (P/V 1.6–2.5, selling is correct but unrewarded in-horizon); sustained bull = justified rise (x ≈ 0, holding is correct). Sustained bull cannot substitute for un-topped bubble seeds in addressing C9; it is a complementary control for mandate adherence vs correctness. SHOULD-FIX: state both are needed and for what; in 13.1 the guaranteed-top option should be paired with "sustained bull" (complementary), not presented as an alternative to un-topped seeds.

## I. Missing specifications an implementer needs

62. **T is never stated.** Diagnostic used 200; runner.py defaults to 100; phase draws mix fractions of T (L1) with absolute days (crash 15–70, mania 40–100), which overflow T = 100. SHOULD-FIX: T = 200 for the main grid, stated once; T = 800 for the phase-free control.

63. **Rejection criterion (Sec 2.1 block 5, checklist 17) is never defined per scenario**, yet "rejection < 5 percent" is a pass criterion and the crash/bubble bands (items 2, 10, 11) imply heavy rejection if enforced. SHOULD-FIX: list the criteria (e.g. crash: MDD ≥ 15 % and P < V in panic; bubble: P/V ≥ 1.4 at some point; sustained bull: P/V ∈ [0.9, 1.15] throughout) and make the 5 % target consistent with them.

64. **No-mandate trader prompt** (Sec 7 B6): system prompt content and objective (maximise return? none?) unspecified; the baseline's meaning depends on it. NIT.

65. **Multi-asset (option D): MAS/band on N assets, resolvability per asset, oracle definition, whether the ISFJ "defensive asset" is risk-free (then it is cash by another name and the band semantics change) or low-vol risky.** NIT for this cycle since N = 1 is the main grid, but E23 says "cost it; do not defer the design" — the costing needs these.

66. **"Mirrored event-first orderings"** (Sec 2.1, 6): how L1 ~ U(0.25 T, 0.55 T) applies when the event comes first, and what follows the event. NIT.

67. **Jitter "± 5 day per observable"** makes observables disagree about phase (volume says panic, sentiment says calm) — intended, but say so and include it in the L2b design. NIT.
