# E0: the v1 generator, frozen and documented

**Freeze.** Git tag `v1-env-freeze` (= commit `4bcf6cd` + nothing else touching `envs/`, `simulation/`, `agent/`).
Byte-identical copies: `envs/v1/synthetic_market_v1.py` (sha256 `74c0e2b4…68b`), `envs/v1/portfolio_tracker_v1.py`
(sha256 `e98c7073…1bb`); full hash list in `docs/env_v2/generated/e0_v1_freeze_sha256.txt`; guarded by
`tests/test_provenance_and_freeze.py`. **Every v1 result CSV in `results_april/`, `results_may/`, `results_ocean/`
was produced by this code**; v1 rows carry no hash, so the freeze is the provenance.

This document states what the code does, block by block, with line references into the frozen file. It is the
"current (code)" column of the v2 plan's Section 3 table, written out. Reference: v2 plan Section 1 (15 defects).

## 1. Common structure (`_generate_market_data`, l.51-293)
- `np.random.seed(seed)` once (l.55): ONE global stream; every block consumes from it in a fixed order, so adding
  any field would change every subsequent path (plan 2.1 block 10 -> v2 uses separate streams).
- Phase lengths are fixed fractions of T for every seed: p1 = int(0.4T), p2 = int(0.3T), p3 = rest (l.59-61);
  T = 200 -> 80/60/60. Phase label from the step index only (`get_scenario_phase`, l.345-373). **Time and phase are
  confounded by construction** (defect 2).
- Price and value are in DOLLARS; mispricing is additive, not multiplicative (defects 4, 6).

## 2. Scenario blocks
### flat (l.152-171)
- V: GBM, mu = 0.0005, sigma = 0.02/day, V_0 = 100 (l.156-159).
- "GARCH-like" phi_t = 0.7 phi_{t-1} + 0.3 |N(0,1)|, floor 0.5 (l.164-168): never fed by returns; no clustering.
- P = V + N(0, 0.5) x phi_t (dollars) (l.170-171): |P-V|/V < 1% on ~97% of steps (audit F-2); bid-ask-bounce
  ACF(1) of returns (defect 4).
### bull_trap (l.65-109)
- V: log-RW with N(0.001, 0.01) in p1, N(0, 0.002) in p2 (plateau), N(-0.0005, 0.002) in p3 (l.69-79).
- P: p1 V + N(0,1) floored at 1 (l.83); p2 cumulative N(1.5, 0.5) dollar drift floored at the p1 exit (l.86-89);
  p3 cumulative N(0.5, 2.5) floored at 1.05 x mania entry (l.94-100). Clips are structural invariants (defect 7).
- phi_t: linspace 1 -> 1.5 (p2) -> 2.5 (p3), identical across seeds (l.105-109).
### crash (l.111-150)
- V: linear -12 dollars over p1 + N(0,0.5); then cumulative N(-0.5, 1.0) (p2); then N(0.02, 0.5) (p3); floor 10
  (l.114-123). Total V drop about -42% regardless of delta.
- P = delta x V + N(0, 1.5), capped at 0.98 V from p2 on, floored at 1 (l.130-143). delta in {0.85, 0.92, 0.95}
  moves MDD by <= 0.6 pp (defect 5).
- phi_t: linspace 1 -> 1.5 -> 3 -> 2, identical across seeds (l.146-150).

## 3. Observables (l.186-291)
- implied_volatility = 15 phi_t (l.188): deterministic phase clock in bull/crash.
- volume = 1e6 (1 + 0.5 U) i.i.d. x phase multipliers (bull 1, 1->3, 3->5; crash 1, 2->4, 1.5->1) (l.191-209):
  a phase clock; corr(volume, |r|) <= 0.
- news_sentiment i.i.d. N(0, 0.3); N(0.7, 0.2) from bull p2 on; N(-0.8, 0.2) in crash p2; clip [-1,1] (l.212-219):
  a phase clock; sentiment_MA5, sentiment_change derived (l.222-223).
- EPS = V/15 (floor 0.01) (l.230-231); reported_PE = P/EPS capped 200 (l.237-239); dividend_yield = 0.4 EPS/P x 100
  (l.245-246). **V = 15 P / PE exactly** (defect 1; L1 audit: median APE 0.0000).
- SMA windows: short = min(20, max(5, T//5)), long = min(50, max(10, T//2)) (l.250-251); long stored as `SMA60`
  (l.261) and rendered as "SMA20/60" -> the 50-day average (defect 8). trend_strength, trend_regime (+/-2%) (l.265-272).
- volume_ratio = volume / rolling mean over the short window (l.275-278). RSI14 = Cutler (simple means) (l.281-286).
  MACD = EMA12 - EMA26, no signal (l.289-291).

## 4. Observation / prompt / logging
See `docs/env_v2/spec/IO_CONTRACT.md` section 1 and `docs/env_v2/generated/table2_v1_from_code.md`: 20 generator columns,
16 exposed by `get_observation()`, 10 rendered.

## 5. Harness facts that are part of the v1 environment (plan diagnosis 10-15)
- 100% cash start for every run; BUY/SELL asymmetric (SELL is a no-op on day 1); same-day execution; zero cost;
  fractional shares; T undisclosed; temperature 0.2 (paper says 0); parse-fallback HOLDs logged as decisions.
- ISFJ core mandate instructs "Buy insurance (puts/hedges)" — outside {BUY, SELL, HOLD}.

## 5b. New finding from the E0 re-scoring: v1 paths are not seed-reproducible across runs
The re-scoring (`E0_RESCORE_V1.md`, section 1) checked that every run in a (scenario, seed, discount) cell carries
the same (Price, Fundamental_Value) path. It does not: 102 of 2,658 runs (25 cells, 127 distinct paths) differ from
their cell's reference path, almost all in **flat** and spread over every model (e.g. deepseek 24 flat runs with 16
distinct paths; Llama/Qwen/gemini-2.5-pro 18 flat runs sharing one alternate path), plus two gemini-2.5-pro crash
runs. The generator seeds the GLOBAL numpy RNG (`np.random.seed(seed)`, l.55) and the experiment runner builds
environments from a 10-worker `ThreadPoolExecutor`, so concurrent `_generate_market_data` calls can interleave draws
from the shared global stream; differences in the numpy version between result batches are the other candidate.
Either way the paper's "seed-reproducible" claim does not hold for these runs; the re-scoring scores each mismatching
run against baselines simulated on its own path. v2 uses per-instance `numpy.random.Generator` streams, one per
component (plan 2.1 block 10), which removes the global-state dependence.

## 6. E0 baseline measurements on this generator (regenerated from code, not from the paper)
- Section 9 checklist on 50 seeds per scenario: `docs/env_v2/generated/checklist_v1.md`.
- Section 5 leakage / phase-clock / resolvability audit on 30 seeds: `docs/env_v2/generated/leakage_audit_v1.md`.
- t = 0 separability gate on all v1 T=200 runs: `docs/env_v2/generated/E0_SEPARABILITY_GATE_V1.md`.
- Metric re-scoring of all v1 T=200 runs under v2 definitions with trivial-policy baselines:
  `docs/env_v2/generated/E0_RESCORE_V1.md`.
