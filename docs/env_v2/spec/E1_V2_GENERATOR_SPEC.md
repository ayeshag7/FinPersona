# E1/E2: the v2 generator as built — blocks, parameters, calibration choices, deviations

Code: `envs/synthetic_market.py` (facade, Table 2 definitions, audit helpers) and `envs/v2/` (`rng.py`, `schedule.py`,
`garch.py`, `mispricing.py`, `events.py`, `generator.py`, `observables.py`, `params/`). Plan references are to
`docs/FinPersona-Bench_Synthetic_Environment_v2_Plan_Aug2026` Sections 2.1-2.2 and 3. Every item marked **[calib]** is a
parameter choice made during E1 to meet a pre-registered Section 9 criterion; every item marked **[deviation]** departs
from the plan's literal text and is also recorded in `DECISION_LOG.md` (addendum) and `PREREGISTRATION_AMENDMENTS.md`.

## 0. Conventions
- T benchmark days (200 main grid; 800 phase-free control), 260-day burn-in (`BURN_IN`) so the FW state, GARCH state,
  trailing-4Q earnings, SMA50 and volume windows are warm at t = 1; V rescaled so V_1 = start price (100).
- Decomposition `log P_t = log V_t + x_t`; the referee's mispricing is x; resolvable iff |x| >= theta (0.03/0.05/0.08).
- Separate named RNG streams (`envs/v2/rng.py`, append-only registry of 14 components; `SeedSequence(seed,
  spawn_key=(attempt, asset+1, component))`); the global numpy RNG is never touched (fixes the v1 thread-interleaving
  defect found in E0). Rejection-sampling attempt k re-draws every stream.

## 1. Fundamental V (plan block 1)
`log V_t = log V_{t-1} + mu_t + sigma_V z_t`, z ~ t(5)/sqrt(5/3); mu_V = 0.00025/day, sigma_V = 0.006/day; crash
deterioration: log-linear drift delivering D_V ~ U(10, 30)% over L_det, then mu = 0 for the rest ("then flat");
sustained bull: mu ~ U(0.0015, 0.0025) for the whole episode; bubble: V grows at mu_V throughout (no plateau).
Multi-asset: z_i = sqrt(rho) f + sqrt(1-rho) e_i with rho = 0.3 (common factor stream, asset index -1).

## 2. Mispricing x (plan blocks 2-3, Section 2.2; decision 2)
FW DCA-HPM recursion with ONE innovation (`mispricing.py`):
`x_{t+1} = x_t + mu [n_f phi (-x_t) + n_c chi (x_t - x_{t-1})] + d_t + w_t e_t`, `n_f = 1/(1+exp(-beta a_{t-1}))`,
`a_t = alpha_0 + alpha_n (n_f - n_c) + alpha_p (s x_t)^2`, `w_t = (n_f sigma_f + n_c sigma_c) / w_bar`.
- Parameter sets: `fw_index_2012` (phi 0.12, chi 1.50, sigma_f 0.758, sigma_c 2.087, alpha_0 -0.327, alpha_n 1.79,
  alpha_p 18.43, beta 1, mu 0.01), `pruna_2016`, `ar1` (flag), and the engine that runs, **`fw_fallback_hl150`** (named in v2.1 Phase 0; before Phase 0 the
  name `fw_single` fell back to it silently — now `fw_single` loads only an ACCEPTED SMM estimate, and none exists):
  the index set with phi raised so that `mu n_bar phi = ln2 / 150` at the realised fundamentalist share n_bar (pilot
  simulation) -> phi = 0.4632, i.e. a **150-day PULL-RATE half-life** **[CAL: chosen so that checklist item 9 on
  T = 800 paths clears the plan's 60 d floor (DECISION_LOG row 2 and addendum); not an estimate; Phase 2 replaces it
  by a FIT value; bracketed by the `fw_hl60` and `fw_index` (≈ 610 d) sensitivities]**. Half-life numbers as
  established in v2.1 Phase 0 (`generated/v2_1/findings_reproduction.md`, block R13): long-pilot ACF(1) half-life
  147 d (five 200,000-step pilots, 141–155 d; the earlier 188 d was one 20,000-step pilot's sampling error);
  sample half-life −ln2/ln ACF(1) ≈ 20 d on the 200-day windows the benchmark runs (14–35 d across seed sets) and
  62–72 d on T = 800 paths — the estimator is biased down on windows shorter than a few half-lives (review B; a pure
  AR(1) with a true 150-d half-life gives 20 / 59 / 96 / 124 d at T = 200 / 800 / 2000 / 5000), so neither sample
  value is the process's half-life; stationary sd(x) 0.165 (sd_e 0.016) / 0.175 (sd_e 0.017) with the engine's
  unit-mean innovation weight — the pilot's 0.142 and the T = 800 sample's 0.128 understate it (raw weights ×0.76;
  window bias). Pilot statistics (20,000 calm steps, raw weights): n_bar = 0.998, w_bar = 0.761.
- **Units [stated interpretation]:** FW measure log price in percent (x 100); the misalignment term therefore uses
  `price_scale = 100` (`(100 x)^2`). The linear pull is unit-free (the plan's 580-day half-life calculation holds). To
  be verified against the FW 2012 PDF before the paper cites the index set as a sensitivity; the single-stock
  re-estimation is done in the same convention so the main results do not depend on it.
- `w_t` is normalised by its pilot mean (unit mean), not by equal population shares **[deviation from my own first
  implementation, not from the plan]**; with n_bar ~ 1 the weight is ~1 in calm and rises to ~2.7 on the rare
  chartist-dominated days (FW's structural stochastic volatility).

## 3. Event drivers (plan blocks 3, 5-7; decisions 3, 7)
`events.py`: scripted drift d_t with error correction `d_t = (x*_{t+1} - x*_t) + lam (x*_t - x_t)` so the realised
path tracks the scripted target x* despite the FW pull and GARCH noise (lam: panic 0.10, stabilisation 0.05, post-top
0.10).
- Crash: deterioration L_det ~ U(15, 40) d **[design choice; the plan gives L2 ~ U(15, 70) for the panic only]**, panic
  L_p ~ U(15, 70) d pulling x toward ln(delta) front-loaded (half the move in the first third), stabilisation pulling
  toward ln(delta_end), delta_end ~ U(delta, 1), over a 30-day ramp then held. delta in {0.55, 0.70, 0.85}.
- Bubble: mania drift g_t compounding at kappa ~ U(0.02, 0.04)/day from g_0 = 0.002, **capped at g_max = 0.012/day
  [calib: without a cap every run reaches P/V > 3 before the horizon and the hazard cannot produce ~50% topped seeds
  with a topped peak of 1.6-2.5; the cap is a parameter of the scripted drift, not a price clip]**; hazard top
  `h_t = h0 exp(b x_t)` with (h0, b, g_max) = (3e-4, 6.0, 0.012) from `tools/calibrate_hazard.py` (60 seeds, final
  calibration: topped 47%, topped peak P/V median 2.12 [q10 1.67, q90 2.52], un-topped peak median 1.82, top at mania
  day ~106; the score penalises early tops that the max-x >= 0.30 criterion would reject); blow-off
  = last third of the realised mania run (ex post label); post-top reversal leg -U(30, 50)% of price over U(10, 30) d,
  then post-top label (d_t = 0) to T.
- Sustained bull: d_t = -lam_sb x_t with lam_sb = 0.15 and conditional-variance multiplier 1.0 (the 0.25 used during E1
  was reverted after review R1-D5: a volatility reduction would make the control identifiable from IV alone) **[deviation:
  the plan says d_t = 0; with FW persistence and fat tails the plan's own validity band x in [-0.10, +0.15] throughout 200 days
  is violated in > 50% of draws; the anchoring makes the no-mispricing control hold; the residual rejection rate is
  published (checklist 17) and exceeds the 5% target]**.
- Schedule (`schedule.py`): setup-first L1 ~ U(0.25T, 0.55T); event-first setup U(5, 20); phase-free; +/-5 d jitter per
  observable (sentiment and volume lag x by |jitter| days; IV is a GARCH forecast and takes none).

## 4. Volatility (plan block 4)
GJR-GARCH(1,1) with standardised t(5) innovations on the x-innovation: alpha = 0.10, gamma = 0.10, beta = 0.83
**[calib: plan 0.05/0.08/0.89; top of the plan's alpha anchor, persistence 0.98 unchanged; checklist 3/6/8/13]**,
sbar = 0.017/day **[calib: plan 0.016; the sample median of calm daily sigma with t tails sits below the population
value]**, rare jumps ON (Poisson 0.010/day, N(-4%, 3%)) **[calib: plan 'optional' at 0.004; checklist 2/8]**, panic
multiplier 5 **[calib: plan 4, sensitivity 3-6]**. Variant table: `generated/e1_calibration_variants.md`;
DECISION_LOG addendum lists the open issues (items 3, 10, 17).
Phase multipliers (calm 1, deterioration 1.5, panic 4, stabilisation 1.5, mania 1.5, blow-off 2, post-top 3,
sustained-bull **1.0** — the 0.25 used during E1 was reverted after review R1-D5; this line printed 0.25 until v2.1 Phase 0) scale the WHOLE conditional variance (`scale_mode="variance"`, regime-switching variance) rather
than omega only **[deviation: under omega-only scaling the panic variance reaches its target at the GARCH persistence
rate (half-life 34 d) and a 15-70-day panic never attains the plan's own 50-100% realised-vol and -6..-15% worst-day
targets; omega-only scaling is kept as the `scale_mode="omega"` sensitivity]**.

## 5. Rejection sampling (plan block 7)
Criteria exactly as pre-registered (crash: min panic x <= -0.10 and MDD >= 20%; bull: max x >= 0.30; sustained bull:
x in [-0.10, 0.15] and V_T/V_1 >= 1.2; flat none); up to 50 attempts; attempts and reasons logged in `get_metadata()`
and in every path's meta; rates published in checklist 17.

## 6. Observables (E2; plan Section 3)
See `envs/v2/observables.py` docstring and the generated `table2_v2_from_code.md` (37 generator columns, 19 exposed,
19 rendered -- every exposed field is rendered by contract). Sentiment with the b_pred feedback is stepped inside the
generator loop; IV uses the 21-day GARCH forecast of the current state with a state-based (top-decile-variance)
premium of 0.35 instead of a label-based "panic" premium **[deviation: a label-tied premium would be a phase clock]**.
Quarterly EPS = V(quarter end)/(4k) x exp(N(0, 0.10)) so that trailing-4Q P/E = k x P/V on average (k ~ U(14, 22)).
Analyst fair value F_t = V_t exp(u_t), u an AR(1) with rho 0.95 per weekly update and stationary sd 0.15 (DESIGN; Phase 5
decides the value) — **implemented at sd 0.335 until v2.1 Phase 0 removed a sqrt(5) innovation scaling** (weakness item
68); the published 50-seed audit's analyst numbers (median error 22 %) describe the defective field.

## 7. Validation status (final E1/E2 calibration; 50 seeds per scenario, crash per delta, T = 200)
`generated/checklist_v2.md` — **8 pass / 7 fail / 5 n-a** of 20 rows (v1 baseline: 3 / 10 / 7 — v1 has 20 rows too, of which 7 are n-a because item 11's topped share and item 17 are not defined for v1); "7 n-a" for v2 was a miscount corrected in v2.1 Phase 0. **n per item**: 470 pooled paths for items 2, 3, 5, 6, 7, 12, 13, 15, 17; 100 for item 1; 150 crash paths for 8 and 10; 200 for 20; 50 bull paths for 11; items 4 and 9 use the **20 T = 800 paths** (not 50 seeds).

| # | Result | Statistic (50 seeds) | Note |
|---|---|---|---|
| 1 | PASS | LB p>0.05 in 88%; median abs ACF(1) 0.080 | |
| 2 | FAIL (margin) | kurtosis>1.5 in 79% (need 80%); Hill 3.36 | sampling margin (80% in the previous 50-seed run) |
| 3 | FAIL | LB abs-r p<0.01 in 60% (need 80%); ACF abs-r(1) 0.151 (in band) | **structural**: inside the plan's GARCH anchor with t(5) innovations the 200-day LB share tops out at ~60% (open issue 1) |
| 5 | PASS | alpha+beta 0.964 | |
| 6 | FAIL | negative in 68% (need 70%); gamma 0.044 > 0 | sampling margin |
| 7 | FAIL | Spearman 0.37, AC(1) 0.81, Shapiro p>0.01 in 49% (need 50%) | sampling margin (amendment A1) |
| 8 | PASS | skew -0.39; worst>best in 70% | |
| 9 | PASS | T=800: ACF(1) 0.9905, half-life 72 d, sd(x) 0.128 (200-day windows: 0.951 / 14 d / 0.053 reported) | amendment A2; **calibration target** (phi set for it), not an independent validation; n = 20 paths; the 72 d is the estimator-biased sample value — a pure AR(1) with the true 150-d half-life gives a median of 59 d and clears 60 d on 49 % of T = 800 paths (review B; v2.1 Phase 0) |
| 10 | FAIL | event-window MDD (A7): means -53/-43/-35% at delta 0.55/0.70/0.85, spread 18.0 pp (need 20), partial R2 0.38 (need 0.7); whole-path: 16.5 pp / 0.35 | **structural** (decision 2, 23 Aug): the plan's panic variance adds ~9 pp of drawdown noise; v1 spread was 0.5 pp |
| 11 | PASS | convex in 66%; topped 44%; topped peak P/V 2.21 | **calibration target** (hazard/cap grid-searched for it), not an independent validation |
| 12 | PASS | ACF 0.874; corr(s,r) 0.363; lagged corr -0.010 | |
| 13 | FAIL | calm IV 28.6%, panic 59.4% (need 60); corr(IV, RV) 0.39 (need 0.40); IV-RV +6.7 / +21.6 pts | sampling margin |
| 15 | PASS | day-only macro accuracy 64.8% on the mixed set (within-scenario 73.7%); corr 0.03 | |
| 17 | FAIL | rejection flat 0%, crash ~1%, bull 5.7%, sustained-bull 39.8% (variance x1.0 after review R1-D5); topped 44% | open issue 3; rates and reasons published |
| 20 | PASS | crash MDD -48%; calm sigma 1.53%; worst panic day -7.9% | |
| 4 | n/a | ACF abs-r lags 1/5/10/20/50 = 0.23/0.18/0.15/0.08/0.02 (T=800) | descriptive |
| 14 | FAIL (L2 absolute) / L1 PASS (A6) | 50 seeds (150 of 400 paths; re-run in v2.1 Phase 0 after the analyst fix): L1 best candidate k·analyst median APE 10.1% (price itself 12.4%; before the fix the analyst candidate was 22.4 % and "no formula beat price"); L2 absolute calm R2(x) 0.92, event 0.97, MAPE(V) 4.5% -- FAIL; price-only control calm R2 0.79; selectivity of non-price fields reported as exploratory (+0.13 R2 / +3.2%); shuffled-V -0.06 | A8 withdrawn as a gate after review; the earlier reading "hidden from the fields, not from price dynamics" is withdrawn (v2.1 Phase 0): the price-only strength is the fixed start price acting as an answer key (level-free R2 0.49, sign 0.74; with the start randomised the fields add +0.6 R2) — weakness items 1, 3, 5 |
| 16 | PASS | 50 seeds: macro-class accuracy full 85.2% vs price-only 78.3% (day-only 54.6%): selectivity +6.9 pp <= 10 pp; scenario-discrimination: sustained-bull days recalled 83% from price alone (reported) | a 4-class test cannot see the one-day IV step at panic onset (z = 7.7; item 46, Phase 3) |
| 18, 19 | unit tests pass (`tests/test_action_space.py`) | | |

Items 3 and 10 cannot be met without leaving the plan's parameter anchors or its own persistent-mispricing / panic-variance
targets; decisions taken 23 Aug 2026 (accept and report; A7; A8) are in `DECISION_LOG.md` (last section) for team review. The
generator is frozen at this calibration; the calibration-variant table is `generated/e1_calibration_variants.md`.
