# Closing note: third-pass verification of the v2.1 improvement plan

Date: 27 August 2026 (work done 26–27 Aug). No code changed, no paid API called, nothing committed; no branches; the frozen v1 code, the original plan and the v2 design plan were not touched.

## Files written (all new; nothing else in the tree was modified)

- `docs/env_v2/v2_1/reviews/V2_1_PLAN_VERIFICATION_LOG.md` — every check of Part 1 with outcome and evidence.
- `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md` — the corrected plan with `[changed: reason]` tags, effort estimates, dependency diagram, go/no-go checkpoint (16A), five new team decisions (D13–D17).
- `docs/env_v2/v2_1/V2_1_ALTERNATIVES_REGISTER.md` — 18 alternatives entries in the fixed structure plus the summary table.
- `docs/env_v2/v2_1/reviews/V2_1_VERIFICATION_CLOSING_NOTE.md` — this note.

Note on git visibility: the uncommitted `.gitignore` change already in the working tree (not made by this pass) ignores `docs/env_v2/reviews/`, so the log and this note — like `review_of_V2_1_IMPROVEMENT_PLAN.md` and reviews A–C — exist on disk but do not appear in `git status`; the corrected plan and the register do appear as untracked. Nothing was committed.

Scratchpad only (not in the repo): `repro_table1.py/.json`, `local_experiments.py/.json`, `formulas.py`, `pytest_full.log`, text extracts of the FW 2012 PDF, the v2 design plan and the execution order, and the downloaded data/price pages used for the network checks.

## What was verified and holds

Every Table 1 finding reproduces on fresh seeds; the weakness map is complete; the share-type power formula is right; the FW units question is settled from the paper itself (`price_scale = 1`); Gemini and Anthropic prices, the batch discounts, EDGAR, SF Fed, CBOE single-stock VIX files, Damodaran, French, AAII and Baker–Wurgler are as the plan says or better; the test suite state is as described.

## What was wrong in the plan and is corrected

1. The "150 vs 188 d" half-life gap is sampling noise of one 20,000-step pilot: five 200,000-step pilots give 141–154 d against 150 d. Phase 0's test passes; E2.5's diagnosis is withdrawn. The engine's stationary sd(x) is ≈ 0.165, not 0.13.
2. Appendix B's "the bound is high because V is smooth": computed, the level-free price-only bound is 0.40 at steady state and 0.14–0.26 within a 200-day run under the v2 parameters — it matches reviewer C's level-free R² of 0.40. The anchor, not the smoothness, produced the 0.79–0.90.
3. E1.1's test "R² of x_1 on log P_1 < 0.01" fails by design under the plan's own mechanism (≈ 0.019 at LogU(20, 500)) and is trivially met under the review's alternative; replaced by an attacker-based test.
4. GPT-5 mini is $0.25 / $2.00, not $0.125 / $1.00; no July-2026 cut exists. Costs recomputed with today's prices and measured prompt sizes; the L3 probe line did not add up under any reading (≈ $10, not $25).
5. The FW 2012 PDF URL is 404 (a working Bamberg path is given); the "≈ 0.17 chartist share / kurtosis ≈ 10" pair is SABCEMM's DCA-WHP row — DCA-HPM is 0.23 / 7.8, and FW 2012 states no share.
6. Citations read-and-wrong: Barro & Ursúa is NBER w14760 (2009) / Research in Economics 2017, not w22743; Campbell–Giglio–Polk is in the Review of Asset Pricing Studies; DMS's 4.3 % is the world premium since 2000, not long-run; Fama–French's range is ≈ 25 % (large) to 40 % (small); Bartram–Grinblatt report alpha decay, not mispricing size; Rhodes-Kropf et al. report component means, not dispersion/persistence; Bakshi–Kapadia 2003 RFS is index-only; Goyal–Saretto sort on log(RV/IV); Shapiro et al. is 2022; Brav–Lehavy has no "share met" (that is Bradshaw et al.: 38 % / 64 %, absolute error 45 %).
7. Equivalence criteria stated as "KS did not reject" are not equivalence tests at these sample sizes (97 % power to reject D = 0.10); restated as upper-confidence-limit bounds.
8. Three later-phase dependencies (E4.6/E4.7 nulls from Phase 6; E5.3 on D10) are re-ordered; the arm grid has no ordering factor although E4.7 says the harness supports it (the runner does; `arms_v2.py` does not).
9. Removing the jumps' negative mean lowers the flat-path kurtosis share from 0.85 to 0.60–0.70: closing item 4 re-opens checklist item 2 unless the jump size is re-fitted (Phase 3 now closes item 13).
10. The unanchored sustained-bull control keeps only 8 % of draws inside the v2 band and has a path-mean x of −0.11: the review's pointer that E4.5 changes what the control is, is right; it is now D14 with a register entry.

## What could not be verified, and why

- FRED (VIXCLS) was unreachable from this machine (connection reset / 403); the no-key CSV claim is unverified. CBOE's own VIX file is the fallback.
- Hamilton & Susmel (1994) variance factors, Pagan & Sossounov (2003) bull/bear durations, Karpoff (1987)'s correlation table, Donohue & Yip (2003)'s bands, Kothari (2001)'s magnitudes, Lintner (1956)'s own text, the dividend-smoothing speeds in Leary & Michaely (2011), the Fama–French post-1940 clause, Lee–Myers–Swaminathan's reversion speed, Frankel–Lee's 36-month spread, the exact Marriott–Pope/Kendall bias formula, Andrews' tables (secondary only), Brown & Cliff's wording: all paywalled or image-only; none of these numbers is carried into the corrected plan.
- The Wikipedia S&P 500 constituent-changes table no longer exists; a replacement universe source was not identified in this pass and must be found before E1.0.
- Batch-API applicability: the 50 % discount exists at all three providers but requires a lock-step runner; whether the team wants that harness change was not decidable here.
- Analyst effort: the per-phase person-day figures are this pass's estimates (labelled ESTIMATE); no source or experiment can supply them.
- Power for every LLM-side discriminating experiment depends on the Phase-8 variance pilot's σ_d, which does not exist yet; the register says so in each entry.
- The reproduction of the plan's ISFJ "compare with 100" numbers used direct scoring rather than the runner (no execution lag), so the oracle's 0.003 and always-hold's 0.11–0.14 were not re-derived through the runner; the rule's oracle-level regret was.

## Decisions that remain the team's

D1 (free substitutes vs WRDS vs hybrid — register 15 gives the survivorship rule), D2 (roster and tier — priced at today's rates), D3 (value process if the decomposition is not identified — register 2), D4 (episode population), D5 (event formulation if none meets the rule — register 8), D6 (calendar rendering — register 9), D7 (θ if θ_info is not reached — register 11), D8 (the one-shot-call issue: the switch counts are already known and G3 of the go/no-go will fail at the live persistence), D9 (bands — register 13), D10 (dividends — must be taken before Phase 5), D11 (salience shares), D12 (minimum effect — "conventional" is not a justification; state it in the claim's units), and the five added: D13 (start-price mechanism — register 1), D14 (what the sustained-bull control is for — register 7), D15 (sentiment's valuation loading — register 10b), D16 (full programme vs the minimal path), D17 (what to do if the go/no-go fails). The plan review's suggested answers to D6, D9, D10, D11, D12 are recorded as one reviewer's opinion and not adopted.
