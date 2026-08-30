# E0 summary — freeze, document, re-score (22 Aug 2026)

Exit criterion (plan Section 13): *Paper Table 2 and prompt match the code; pre-registration exists; v1 re-scored
under all metric definitions.* Status: **met**, all artefacts generated. E1 is **not started**: it waits
on the Section 13.1 sign-off (`DECISIONS_13_1.md`).

## 1. What was built
- Tag `v1-env-freeze`; byte-identical copies of the v1 generator and tracker in `envs/v1/`; SHA-256 list; guard tests.
- `tools/gen_table2.py`: Table 2 regenerated from code (20 generator columns; 16 exposed; **10 rendered**; 6
  exposed-but-never-shown: `volume`, `sentiment_MA5`, `sentiment_change`, `dividend_yield`, `trend_strength`, `MACD`;
  portfolio `cash`/`holdings_value` rendered but absent from the paper's table; `SMA60` key = 50-day average). The
  rendered prompt is published verbatim (`generated/rendered_prompt_v1_*.txt`).
- `agent/render.py`: prompt rendering factored out of the agents, verified byte-identical to the frozen v1 f-strings
  (`tests/test_render_prompt_frozen.py`), so hashes and Table 2 come from the code the agents run.
- `simulation/provenance.py` + runner wiring: every output row now carries `Env_Version`, `Gen_Config_Hash`,
  `Env_Code_Hash`, `Prompt_Hash`, `System_Prompt_Hash`, `Temperature`, `Git_Commit`.
- `evaluation/stylized_facts.py` (Section 9 checklist, generator-agnostic, ≥50 seeds) and
  `evaluation/leakage_audit.py` (Section 5 L1/L2/L2b/L4) with CI tests (`tests/test_leakage_ci.py`: v1 xfail,
  v2 must pass); `tests/test_action_space.py` (items 18/19).
- `evaluation/separability_gate.py`, `evaluation/rescore_v1.py`, `evaluation/baselines.py` and their reports.
- Docs: `IO_CONTRACT.md`, `E0_V1_GENERATOR_SPEC.md`, `PREREGISTRATION.md`, `DECISIONS_13_1.md`, this file.

## 2. t = 0 separability gate on v1 (Section 4.6) — `generated/E0_SEPARABILITY_GATE_V1.md`
2,898 run files (18 MBTI models × 150 runs, gemma-3-4b 108; 3 OCEAN models × 80), 4 parse-fallback rows excluded.
- Day-1 mean cash ISFJ / INTJ / ENTJ = **0.919 / 0.915 / 0.839** (medians all 1.000); days 1–5: 0.894 / 0.866 / 0.727.
  Red-team replication: 0.92/0.92/0.88 reported; ISFJ-vs-INTJ day-1 MWU p = 0.635 (red-team 0.356 on days 1–5).
- Pooled: KW p < 0.001 but Cliff's δ ISFJ–INTJ / INTJ–ENTJ / ISFJ–ENTJ = −0.010 / 0.109 / 0.098 (criterion ≥ 0.47);
  v2 band-hit 8.7% (ISFJ 13.7, INTJ 5.1, ENTJ 7.2; criterion ≥ 80%); v1 point-hit ISFJ 80% / INTJ 5% / ENTJ 1%;
  AUC from C₁ = 0.527 (criterion ≥ 0.8); RF persona share 0.79 but R² = 0.007 (criterion share ≥ 0.5 with R² ≥ 0.5;
  permutation-null share 0.09).
- **0 / 18 models pass the gate** in either agent type (ordering 2/18 in at least one arm; AUC 3/18; surrogate 4/18;
  band-hit 0/18). Day-1 actions: P(BUY) ISFJ 0.26, INTJ 0.24, ENTJ 0.33; P(SELL) = 0 (SELL is a no-op at 100% cash).
- OCEAN: O1 vs O2 pooled δ = 0.25, AUC 0.62 (fail); **O3 numerical-only (target stated) δ = 0.83, AUC 0.92** —
  the ceiling the plan predicts: stating the target separates personas, the persona text alone does not.

## 3. Metric re-scoring of v1 (Section 8 item 6) — `generated/E0_RESCORE_V1.md`
2,658 MBTI runs; 306 (11.5%) never trade (ISFJ-memory 36–47% per scenario).
- Resolvability at θ = 0.05: flat **0.000** (mean |x| = 0.003; 0 at θ = 0.03 too), bull_trap 0.579 (legitimate-rise
  0.000, mania 0.93, blow-off 1.00), crash 0.820. Flat RG is therefore undefined under the unresolvable-step rule
  (pre-registered casualty 2 confirmed).
- Bull-trap trivial-policy envelope replicated: buy-day-1-then-HOLD RG_v1 99.7, always-HOLD 79.8, random 67.7 (audit:
  99.7 / 79.8 / 66.9); always-BUY 20.2; momentum 91.7; V-oracle 79.8; mandate-conditional oracle 79.3.
- Pooled agent RG_v1 → RG_0.05: flat 79.4 → n/a; bull_trap 82.2 → 86.8; crash 63.8 → 63.4.
- **The plan's RG normalisation is degenerate on v1**: under the v1 HOLD rule buy-day-1-then-HOLD scores ~100 in every
  scenario, so the floor (best of always-HOLD / random / buy-and-hold) sits at or above the mandate-conditional
  ceiling in 100% of runs. "Beats k of 11" is reported instead; MAS normalisation is well defined. → E4 must define
  RG as mandate-conditional regret (plan Section 8/E4) before normalising; noted in `PREREGISTRATION.md` §6.
- Bidirectional headline under re-scoring (models where memory lowers MAS, of 18): ISFJ 16/18 (v1 point-MAS, target
  1.0 = the 100%-cash start) → **11/18** under the v2 band, 10/18 under the v2 point; ENTJ 4/18 improve (14 worsen)
  → 6/18 (12 worsen); INTJ 7/18 under both. ENTJ in bull_trap improves under memory for 12–14/18 models; the ENTJ
  "worsening" is a crash-scenario effect (17/18 v1, 13/18 band).
- **New defect**: 102 runs (25 cells, 127 distinct paths, almost all flat, every model) do not share their cell's
  price path — the global `np.random.seed` + 10-thread runner (or library drift) breaks seed reproducibility
  (`E0_V1_GENERATOR_SPEC.md` §5b). v2's per-component `Generator` streams remove the cause.

## 4. Section 9 checklist on v1 (50 seeds/scenario) — `generated/checklist_v1.md`
Pass 3 / fail 10 / n-a 7. Fails: no-linear-ACF in calm (LB p > 0.05 in 72%, |ACF1| 0.16), heavy tails (kurtosis > 1.5
in 4%), volatility clustering (LB|r| p < 0.01 in 39%), leverage, volume–volatility (Spearman 0.05; AC(1) log-volume
0.93 from the phase ramps), crash asymmetry (skew +0.01), mispricing persistence (ACF(1) of x = −0.009, sd 0.7%),
delta matters (partial R² 0.03; MDD spread 0.5 pp), bubble convexity (16% convex), sentiment (ACF 0.61 from phase
shifts; corr with r 0.08), IV realism (calm 12.5%, panic 34%, IV−RV negative). Passes: GARCH refit persistence
(spurious: 0.966 on non-clustered data with level shifts), magnitudes, mixed-set day→phase (63.6%; **within-scenario
100%**), conditioning (no rejection exists).

## 5. Section 5 leakage / phase-clock audit on v1 (30 seeds, 27,000 steps) — `generated/leakage_audit_v1.md`
- L1: `k*P/PE` with fitted k = 15.00 reproduces V with median APE 0.16% and max 0.41% (rendering rounding only);
  0% of steps above the 1% floor -> **fail** (the exact leak, audit F-1, re-measured from code).
- L2 (held-out seeds): best calm OOS R2(x) = 0.90; event R2(x) = 0.9996, MAPE(V) = 0.65% -> **fail** both thresholds.
- L2b: macro-phase accuracy full 99.8% vs price-only 94.9% (day-only 60.0%, majority 40%) -> selectivity +5.0 pp,
  inside the 10 pp margin: in v1 the PRICE path itself is a phase clock (fixed-index deterministic ramps), so the
  non-price fields add little on top; the binding v1 failures are L1/L2 and checklist 15 within scenario (100%).
- L4 (theta = 0.05): flat 0.0%, bull_trap ~58%, crash ~82% of steps resolvable (per-phase table in the report).

## 6. Pre-registration and decisions
`PREREGISTRATION.md` fixes thresholds, feature sets, windows, casualties and the spine recommendation; two casualties
are already confirmed by E0 (flat RG undefined; bull-trap arms inside the trivial envelope) and one is partly confirmed
(ISFJ side of the bidirectional headline is start-dependent). `DECISIONS_13_1.md` lists the eleven sign-offs with
recommendations; E1 waits on them.
