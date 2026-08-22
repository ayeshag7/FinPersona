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
  alpha_p 18.43, beta 1, mu 0.01), `pruna_2016`, `ar1` (flag), and `fw_single` = `envs/v2/params/fw_single_stock.json`
  if `tools/calibrate_fw.py` has produced it, else the **documented fallback**: the index set with phi raised so that
  `mu n_bar phi = ln2 / 120` at the realised fundamentalist share n_bar (pilot simulation) -> phi = 0.579, calm
  half-life 120 d **[calib: 120 d chosen inside the plan's 60-120 d window so that the sample ACF(1) of x on long
  windows clears 0.98]**. Pilot statistics (20,000 calm steps): n_bar = 0.997, w_bar = 0.762, stationary sd(x) = 0.11.
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
- Sustained bull: d_t = -lam_sb x_t with lam_sb = 0.15 and conditional-variance multiplier 0.25 **[deviation: the plan
  says d_t = 0; with FW persistence and fat tails the plan's own validity band x in [-0.10, +0.15] throughout 200 days
  is violated in > 50% of draws; the anchoring makes the no-mispricing control hold; the residual rejection rate is
  published (checklist 17) and exceeds the 5% target]**.
- Schedule (`schedule.py`): setup-first L1 ~ U(0.25T, 0.55T); event-first setup U(5, 20); phase-free; +/-5 d jitter per
  observable (sentiment and volume lag x by |jitter| days; IV is a GARCH forecast and takes none).

## 4. Volatility (plan block 4)
GJR-GARCH(1,1) with standardised t(5) innovations on the x-innovation: alpha = 0.10, gamma = 0.10, beta = 0.83
**[calib: plan 0.05/0.08/0.89; top of the plan's alpha anchor, persistence 0.98 unchanged; checklist 3/6/8/13]**,
sbar = 0.017/day **[calib: plan 0.016; the sample median of calm daily sigma with t tails sits below the population
value]**, rare jumps ON (Poisson 0.008/day, N(-4%, 3%)) **[calib: plan 'optional' at 0.004; checklist 2/8]**, panic
multiplier 5 **[calib: plan 4, sensitivity 3-6]**. Variant table: `generated/e1_calibration_variants.md`;
DECISION_LOG addendum lists the open issues (items 3, 10, 17).
Phase multipliers (calm 1, deterioration 1.5, panic 4, stabilisation 1.5, mania 1.5, blow-off 2, post-top 3,
sustained-bull 0.25) scale the WHOLE conditional variance (`scale_mode="variance"`, regime-switching variance) rather
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

## 7. Validation status (final E1/E2 calibration; 50 seeds per scenario, crash per delta, T = 200)
`generated/checklist_v2.md` — **9 pass / 6 fail / 7 n-a** (v1 baseline: 3 / 10 / 7).

| # | Result | Statistic (50 seeds) | Note |
|---|---|---|---|
| 1 | PASS | LB p>0.05 in 88%; median abs ACF(1) 0.080 | |
| 2 | PASS | kurtosis>1.5 in 80%; Hill 3.35 | |
| 3 | FAIL | LB abs-r p<0.01 in 60% (need 80%); ACF abs-r(1) 0.151 (in band) | **structural**: inside the plan's GARCH anchor with t(5) innovations the 200-day LB share tops out at ~60% (open issue 1) |
| 5 | PASS | alpha+beta 0.964 | |
| 6 | FAIL | negative in 68% (need 70%); gamma 0.044 > 0 | sampling margin |
| 7 | FAIL | Spearman 0.37, AC(1) 0.81, Shapiro p>0.01 in 49% (need 50%) | sampling margin (amendment A1) |
| 8 | PASS | skew -0.39; worst>best in 70% | |
| 9 | PASS | T=800: ACF(1) 0.9905, half-life 72 d, sd(x) 0.128 (200-day windows: 0.951 / 14 d / 0.053 reported) | amendment A2 |
| 10 | FAIL | event-window MDD (A7): means -53/-43/-35% at delta 0.55/0.70/0.85, spread 18.0 pp (need 20), partial R2 0.38 (need 0.7); whole-path: 16.5 pp / 0.35 | **structural** (decision 2, 23 Aug): the plan's panic variance adds ~9 pp of drawdown noise; v1 spread was 0.5 pp |
| 11 | PASS | convex in 66%; topped 44%; topped peak P/V 2.21 | |
| 12 | PASS | ACF 0.874; corr(s,r) 0.363; lagged corr -0.010 | |
| 13 | FAIL | calm IV 28.6%, panic 59.4% (need 60); corr(IV, RV) 0.39 (need 0.40); IV-RV +6.7 / +21.6 pts | sampling margin |
| 15 | PASS | day-only macro accuracy 64.8% on the mixed set (within-scenario 73.7%); corr 0.03 | |
| 17 | FAIL | rejection flat 0%, crash 1.3%, bull 5.7%, sustained-bull 24.2%; topped 44% | open issue 3 |
| 20 | PASS | crash MDD -48%; calm sigma 1.53%; worst panic day -7.9% | |
| 4 | n/a | ACF abs-r lags 1/5/10/20/50 = 0.23/0.18/0.15/0.08/0.02 (T=800) | descriptive |
| 14 | PASS (A6, A8) | L1: no formula beats price itself (median APE >= 13%); L2 selectivity of non-price fields (best vs best, worst group): see audit; margins 0.20 R2 / 5 pp MAPE (A8); absolute L2 (reported): calm R2 0.93, event 0.97, MAPE 4.1% | decision 3, 23 Aug |
| 16 | PASS | L2b macro-class accuracy full 88.6% vs price-only 81.1% (day-only 51.5%): selectivity +7.5 pp <= 10 pp | |
| 18, 19 | unit tests pass (`tests/test_action_space.py`) | | |

Items 3 and 10 cannot be met without leaving the plan's parameter anchors or its own persistent-mispricing / panic-variance
targets; decisions taken 23 Aug 2026 (accept and report; A7; A8) are in `DECISION_LOG.md` (last section) for team review. The
generator is frozen at this calibration; the calibration-variant table is `generated/e1_calibration_variants.md`.
