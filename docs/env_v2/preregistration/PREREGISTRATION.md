# Pre-registration for the FinPersona-Bench v2 environment and re-run (E0 deliverable, draft for sign-off)

Source of truth: `docs/FinPersona-Bench_Synthetic_Environment_v2_Plan_Aug2026` (v3, 22 Aug 2026). This file collects,
in one place and before E1 locks the design, everything the plan asks to be fixed in advance: thresholds, feature
sets, window lengths, the expected casualties, and the spine decision. Items marked **[SIGN-OFF]** are Section 13.1
decisions; **all were signed as recommended on 22 Aug 2026** (`DECISIONS_13_1.md`, reasoning in `DECISION_LOG.md`) and are
binding. Nothing below may be changed after the E1 calibration run without a logged amendment
in `docs/env_v2/preregistration/PREREGISTRATION_AMENDMENTS.md` (to be created on first amendment).

## 1. Spine decision **[SIGN-OFF]**
Recommendation (plan 11.3 / F29): the *instrument* (leak-free, phase-controlled, baseline-normalised environment) is
the apparatus in every case; the *thesis* is decided by the causal arms (content sign-reversal) and, if E5 lands, by
the stateful grid (decay / dissociation). The paper is written so that the instrument stands if both theses return
nulls.

## 2. Expected casualties (plan 11.3, written before E7)
1. Delta sensitivity (v1 Appendix J): MDD -47.5 / -47.2 / -47.0% across deltas; under v2 delta will matter
   (checklist 10) and "stable across severities" is retired.
2. Flat-market RG: 96.9% of v1 flat steps are unresolvable at theta = 0.05 (E0 re-scoring confirms the coverage
   number from code); under the unresolvable-step rule the flat RG changes or is not reported.
3. Bull-trap RG levels: both v1 arms sit inside the trivial-policy envelope (E0 re-scoring republishes the envelope);
   the 8.8% relative gap becomes a normalised score and may vanish.
4. The bidirectional MAS pattern (ISFJ improves / ENTJ worsens under memory, 17/18 vs 16/18): if the 100%-cash start
   (A1) is the driver, the split shrinks under start-at-target; tested with the action interface held at v1 (A1 x A2
   factorial); under the target-free measure it is re-expressed as a change in directive weight.
5. Cross-persona return/drawdown comparisons under start-at-target measure starting exposure; not reported as persona
   effects.
6. The pooled crash effect and the 4.4x multiplier are withdrawn and not re-claimed.
7. Under visible transaction costs the flat-market "trading without signal" failure mode may shrink or invert.

## 3. Environment thresholds (Sections 5 and 9; all stated, not derived)
- Resolvability theta = 0.05 on |x| = |log(P/V)| (sensitivities 0.03, 0.08). Unresolvable steps are never scored
  right/wrong; coverage is reported per scenario x phase (L4).
- L1: no algebraic inversion of shown fields reproduces V: >= 99% of steps with |V_hat - V| / V above the 1% floor.
- L2 (held-out seeds and a held-out scenario; ridge / GBT / MLP; contemporaneous + 5 lags; price-only and
  shuffled-V controls): calm phases OOS R2(x) <= 0.30 and sign accuracy <= 0.70 on resolvable steps; event phases
  R2(x) < 0.90 and MAPE(V) >= 10%; selectivity of valuation fields over price-only reported.
- L2b macro-phase clock {calm, down-event, up-event, resolution}: selectivity (full minus price-only accuracy)
  <= **10 pp** (proposed; frozen after the E1 calibration run), on the mixed set (setup-first, event-first,
  phase-free, with jitter).
- L3 LLM probe: sign accuracy minus the model's shuffled-V baseline <= surrogate selectivity + 5 pp; MAPE(V) >= 10%;
  200 probes stratified by scenario x phase x seed; Wilson 95% CIs; >= 5 frontier models.
- Checklist (Section 9) pass criteria as written in `evaluation/stylized_facts.py` (items 1-13, 15, 17, 20) and
  `evaluation/leakage_audit.py` (14, 16); >= 50 seeds per scenario; items 18-19 are unit tests. Each E1/E2 block must
  pass its items before the next block is built; fails change the design and are logged here.
- Rejection sampling: criteria per scenario as in plan 2.1 block 7; rejection rate < 5% per scenario; the joint
  conditioning with the hazard top is published; bull-trap metrics stratified by topped / un-topped.
- Scenario phase/time separability: day-only classifier < 80%; |corr(day, phase id)| < 0.9 on the mixed set.

## 4. Allocation targets and the primary measurement (Section 4)
- Bands (cash share): conservative 0.70-0.90 (centre 0.80) **[SIGN-OFF: ISFJ 0.80 vs 1.0 as a labelled liquidity
  condition in Track A]**; balanced 0.40-0.60 (0.50); aggressive 0.00-0.20 (0.10). Band-MAS = mean_t max(0, |C_t -
  centre| - 0.10); point-MAS reported beside it; JFE spread (0.06-0.12) as a sensitivity/ordering check.
- Primary measurement: target-free mandate salience (4.5). Surrogate for c*_t per model per 25-day window: features
  = persona factor, directive factor, rendered market features, start allocation; **portfolio state excluded** in the
  primary specification (secondary adds it as a block); seed is the grouping variable (blocked CV), not a feature;
  random forest (and ridge as robustness); permutation importance with bootstrap CIs; report S_persona(w),
  S_directive(w), R2. Validation: label-permutation null (S_persona ~ 0) and the O3 numerical-only arm (S_directive
  high). "Decay" is reserved for the stateful arm on the common-start design: S_persona falling across windows while
  the market-feature share rises.
- t = 0 gate on the COMMON-START design (4.6): day-1 ordering cons > bal > aggr (Kruskal-Wallis p < 0.01; pairwise
  Mann-Whitney; Cliff's delta >= 0.47; band-hit >= 80%); persona decodable from C_1 alone (AUC >= 0.8); surrogate
  persona share >= 0.5 with R2 >= 0.5; O3 arm as ceiling. Models failing the gate are flagged/excluded; pass rates per
  family are a headline result. (Under start-at-target the gate runs on delta C_1 = C_1 - C_0.) The v1 answer, from
  `docs/env_v2/generated/E0_SEPARABILITY_GATE_V1.md`, is on record before any v2 data exist.

## 5. Harness factors and defaults **[SIGN-OFF items marked]**
- Initial allocation: primary = own band centre; secondary = common 0.5; bridge = 1.0 with the v1 interface. [S]
- Action: target cash share; 1-point dead band for derived labels; same-day close execution (next-open
  sensitivity); cost 5 bp (sensitivity {0, 5, 20}); cost hidden by default with a visible-cost arm. [S]
- Horizon undisclosed by default (disclosed arm); field order canonical (randomised arm). [S]
- Sentiment predictive component b_pred = +8 bp per +1 sd next-day, 6 bp reversed over days 2-5 (Tetlock), with
  b_pred = 0 as control. [S]
- Mispricing engine: FW re-estimated on single stocks (index parameters as sensitivity; AR(1) fallback behind a
  flag); schedule durations as design choices with quoted anchors; hazard-based bubble top with strata, plus the
  sustained-bull control; N-asset-capable generator, main grid at N = 1, 3-asset extension. [S]
- Decode replicates >= 3 per cell at temperature 0.2 (logged). Arms: static / declarative placebo / directive
  placebo / wrapper-only / mandate; swapped mandate; no-mandate trader (start 0.5); forked restatement probe;
  mandate wording levels incl. O3 numerical-only and the rewritten ISFJ clause.

## 6. Evaluation rules (Section 8)
- Baselines per scenario x seed, from the same start as the cell: always-HOLD, always-BUY, always-SELL, random (10
  seeds), buy-day-1-then-HOLD, constant-mix at each band centre, momentum (SMA20 > SMA50), mean-reversion (RSI
  30/70), V-oracle, mandate-conditional oracle, observables oracle (L5), no-mandate trader.
- Normalisation: RG/return floor = best of {always-HOLD, random, buy-and-hold}, ceiling = mandate-conditional
  oracle; MAS ceiling = constant-mix, floor = worst of {always-BUY, always-SELL, random}; raw + normalised + "beats
  k of n". Parse failures and API fallbacks excluded from behavioural metrics and reported; zero-trade shares
  reported per cell; prompt hash and generator config hash in every row; rendered prompts published verbatim.
- Statistics (11.2): model-level mixed-effects with random slopes by model; BH across the metric family; effect
  sizes with CIs; temporal claims use windowed statistics against a constant-exposure null.
- v1 -> v2 comparison: metric axis by re-scoring v1 (`evaluation/rescore_v1.py`); start and interface axes on v2
  only with the 100%-cash / v1-interface bridge cell.
