# Review A: parameter provenance (independent reviewer, 23 Aug 2026)

Reviewer lens: every number must trace to a published study, then be fitted and stress-tested. "In the plan" is not provenance.

**Headline finding.** The v2 environment contains roughly 200 numeric choices. Only about a dozen are traceable to a specific published statistic (FW 2012 index parameters, Tetlock 2007 sentiment coefficients, the Nasdaq/FIM 5 bp cost, the practitioner allocation bands, Wilder/Appel indicator windows). The single planned data-fitting step, SMM re-estimation of the FW parameters on single stocks, was attempted once, returned J = 408, and was replaced by a hand-set constant (`HALF_LIFE_FALLBACK_DAYS = 150`). Roughly 25 parameters were then tuned to pass the Section 9 checklist, whose own thresholds were in several cases moved to what the generator could produce (items 9, 10, 13, 17, A1, A2, A6, A7). No parameter has a published variability/sensitivity table beyond seven single-parameter checklist re-runs, none of which is an LLM-outcome sensitivity.

Provenance key: LIT = specific published source cited for the value; PLAN = set in the plan, no external source for the number; CAL = tuned after the plan to pass a pre-registered check; ARB = no stated justification anywhere; CFG = engineering constant.

## Section 1. Full parameter table

### 1.1 Fundamental value V

| # | Parameter (value) | File:line | Controls | Prov. | What proper justification would look like | Sev. |
|---|---|---|---|---|---|---|
| 1 | `MU_V_BASE = 0.00025`/day | events.py:27; generator.py:64 | calm/crash/bull V drift (~6.5 %/yr) | PLAN (plan "long-run US price-only return 6-8 %"; no source named) | Cite Dimson-Marsh-Staunton Yearbook or Shiller data; estimate from CRSP value-weighted index ex-dividend; show 200-day results insensitive over 0-0.0005/day | LOW |
| 2 | `sigma_V = 0.006`/day | generator.py:65 | smoothness of V; drives L2 leakage and resolvability | PLAN (plan cites Campbell-Lettau-Malkiel-Xu 2001 qualitatively; research doc recommended 0.008-0.010, plan lowered to 0.006 to fix a coherence-item calculation) | CLMX 2001 give idiosyncratic vs market variance shares, not a "fundamental" vol; defensible number is the daily vol of a smoothed earnings/dividend value proxy (Vuolteenaho 2002 cash-flow-news variance, or vol of quarterly EPS x constant multiple from Compustat). Sweep 0.004-0.012 and report L2 R2, L4 coverage, checklist 20 | HIGH |
| 3 | `df_V = 5.0` (t shocks on V) | generator.py:66 | tail of V shocks | ARB (t(5) anchor is for return innovations) | Gaussian, or fit df of quarterly EPS surprises; show V-return kurtosis | LOW |
| 4 | `rho_common = 0.3` | generator.py:67; arms_v2.py:66 | cross-asset correlation | ARB (not in plan) | average pairwise correlation of large-cap daily returns (~0.3-0.5, Pollet & Wilson 2010); sweep {0.1, 0.3, 0.6} | MED |
| 5 | `asset_vol_scale = [1, 1, 0.5]` | arms_v2.py:66 | defensive asset vol | ARB | low-vol-decile to median vol ratio (Ang-Hodrick-Xing-Zhang 2006; MSCI Min-Vol ratio ~0.7-0.8); sweep | LOW |
| 6 | `start_price = 100` | generator.py:63 | scale | CFG | none | - |
| 7 | `BURN_IN = 260` | generator.py:37 | warm state | CFG | confirm stationarity at burn-in end | LOW |

### 1.2 Mispricing engine

| # | Parameter | File:line | Controls | Prov. | Proper justification | Sev. |
|---|---|---|---|---|---|---|
| 8 | FW index set (phi 0.12, chi 1.50, sigma_f 0.758, sigma_c 2.087, alpha_0 -0.327, alpha_n 1.79, alpha_p 18.43, beta 1, mu 0.01) | mispricing.py:43-54 | `fw_index` sensitivity | LIT (Franke & Westerhoff 2012 JEDC, S&P 500 1980-2007) | cite as index-level | - |
| 9 | Pruna 2016 set | mispricing.py:61-63 | `pruna` sensitivity | LIT (Pruna, Polukarov & Jennings 2016) | fine | - |
| 10 | `price_scale = 100` in the misalignment term | mispricing.py:52,167 | whether fundamentalist/chartist switching works at all | ARB, self-flagged unverified | FW 2012 use natural log price units; pilot n_bar = 0.997 vs FW's published mean chartist share ~0.17 is direct evidence the x100 saturates the logistic and kills switching, making the engine an AR(1) with a fixed weight. Verify against FW 2012; re-run pilot with price_scale = 1; re-run SMM | HIGH |
| 11 | `HALF_LIFE_FALLBACK_DAYS = 150` -> phi ~ 0.463 (live engine) | mispricing.py:38,93-109 (docstring says 90 d) | persistence, sd of calm x, L4, L2, checklist 9, flat difficulty | CAL (chosen so realised half-life clears the plan's 60 d floor; docs give 60-120, 90, 120, 150) | Poterba & Summers 1988; Fama-French 1988; Balvers-Wu-Gilliland 2000; firm-level regression of log(P/V_hat) on Compustat/CRSP across ~500 stocks, median half-life with P25/P75; sweep hl in {30, 60, 150, 300, 580} through checklist AND LLM grid | HIGH |
| 12 | `pilot_stats` (20000 steps, sd_e = 0.016) | mispricing.py:69-88 | w_bar normalisation | CFG but sd_e is the pre-calibration sbar | recompute at shipped sbar | LOW |
| 13-16 | fixed-point iterations, clip +-50, rho_ar1, REJECTED.json | mispricing.py | - | CFG / inherits #11 | re-run SMM after fixing units; add non-return moments | - |

### 1.3 Volatility

| # | Parameter | File:line | Controls | Prov. | Proper justification | Sev. |
|---|---|---|---|---|---|---|
| 17 | `alpha = 0.10` | garch.py:32 | ARCH term | CAL (plan 0.05 -> 0.10 for checklist 3/13; anchor Engle 2001 0.077, index-level) | Fit GJR-GARCH(1,1)-t per stock on CRSP large caps 2000-2024 (>= 100 names); use cross-sectional median, bracket with IQR; run `garch_strong` through the LLM grid | HIGH |
| 18 | `gamma = 0.10` | garch.py:33 | leverage | CAL (plan 0.08) | as #17 | MED |
| 19 | `beta = 0.83` | garch.py:34 | persistence 0.98 kept | CAL (plan 0.89) | as #17 | MED |
| 20 | `sbar = 0.017`/day | garch.py:35 | calm sigma; checklist 20 | CAL (plan 0.016; raised so the sample median clears item 20) | CRSP single large-cap daily vol distribution | MED |
| 21 | `df = 5.0` | garch.py:36 | tails | PLAN (df 4 tried and rejected because it broke items 3/13/20) | fitted df from #17 | MED |
| 22 | `panic_mult = 5.0` | garch.py:37 | panic variance | CAL (plan 4; set to 5 for items 13/20) | ratio of realised crisis vol to calm vol (2008-Q4, 2020-Q1, CRSP); sweep through LLM crash cells | MED |
| 23 | phase multipliers (det 1.5, stab 1.5, mania 1.5, blow-off 2, post-top 3, SB 1.0) | garch.py:26-27 | phase variance levels | PLAN (no source; SB went 1 -> 0.25 -> 1.0) | Ang & Timmermann 2012 regime vol ratios; GSY 2019; these are label-tied and are what L2b reads; sweep each and report L2b | MED |
| 24 | `scale_mode = "variance"` | garch.py:38 | multiplier mechanism | CAL (A3) | cite Hamilton & Susmel 1994 SWARCH; fit a 2-regime SWARCH | LOW |
| 25 | IV horizon 21 | garch.py:95 | IV | CFG (VIX 30 calendar days) | fine | - |
| 26 | `jump_rate = 0.010`/day | generator.py:70-71 | kurtosis (item 2) | CAL (plan "optional 0.004"; raised to 0.008 then 0.010; the published variant table's final says 0.008, and no variant with (0.010, sd 0.03) was ever run) | fit a jump-diffusion (Kou 2002 / Bates 1996) or count |r| > 4 sigma events in CRSP large caps (2-6/yr); sweep 0/0.004/0.010/0.02 | MED |
| 27 | `jump_mean = -0.04`, `jump_sd = 0.03` | generator.py:72-73 | jump size | PLAN (no source) | earnings/news-day return distribution | LOW |
| 28 | `HAZARD_H0 = 0.0015`, `HAZARD_B = 6.0` module fallbacks | generator.py:42-43 | silent default differing from calibrated 0.0003 if hazard.json missing | ARB | make it fail loudly | LOW |

### 1.4 Events, schedule, rejection

| # | Parameter | File:line | Controls | Prov. | Proper justification | Sev. |
|---|---|---|---|---|---|---|
| 29 | Setup L1 ~ U(0.25T, 0.55T) | schedule.py:83 | event onset | PLAN (anchors quoted, Ang-Timmermann, Pagan-Sossounov, are monthly and unusable at 200 days) | state as design; show LLM outcome sensitivity to onset | MED |
| 30 | Event-first setup U(5, 20) | schedule.py:85 | ordering | PLAN | design; sweep | LOW |
| 31 | `min_resolution = 10`, overflow floors | schedule.py:65,92-97 | horizon squeeze | ARB (undocumented) | state; report overflow frequency | LOW |
| 32 | Deterioration U(15, 40) d | schedule.py:89 | pre-panic | ARB (spec: "design choice") | 2007-08, 2000-01 deterioration lengths; or drop the phase | MED |
| 33 | Panic U(15, 70) d | schedule.py:90 | crash speed | PLAN (2020 = 23 d, 2008 ~ 120 d, secondary sources) | compile peak-to-trough lengths of all S&P >= 20 % declines since 1950 (Mishkin & White 2002; Pagan-Sossounov) and single-stock >= 30 % drawdowns (CRSP); fit a distribution | LOW |
| 34 | `D_V ~ U(0.10, 0.30)` | schedule.py:99 | fundamental drop | PLAN (S&P EPS -25 % 2001, -40 % 2008) | Compustat peak-to-trough EPS declines | LOW |
| 35 | delta in {0.55, 0.70, 0.85} | generator.py:61 etc. | crash severity | PLAN (changed from v1's {0.85, 0.92, 0.95} so MDD lands in the checklist band; circular with item 20) | Campbell-Shiller decomposition of historical crashes into cash-flow vs discount-rate news; deltas at P25/P50/P75 | MED |
| 36 | `delta_end ~ U(delta, 1)` | schedule.py:100 | recovery | PLAN | share of crash recovered within 6 months historically | LOW |
| 37 | front-loading (half the move in the first third) | events.py:37-43 | panic shape | PLAN | fit cumulative decline shape of 1987/2008/2020 | LOW |
| 38 | `STAB_RAMP_DAYS = 30` | events.py:31 | stabilisation | ARB (not in plan) | as #36 | LOW |
| 39 | `LAM_PANIC = 0.10`, `LAM_STAB = 0.05`, `LAM_POSTTOP = 0.10` | events.py:28-30 | how tightly x is forced onto the script | ARB | no literature for a tracking gain; report share of event-phase Delta-x variance explained by d_t vs FW/GARCH; sweep 0.02-0.25 with checklist 10/20 and LLM crash outcomes | HIGH |
| 40 | mania `g0 = 0.002`, `kappa ~ U(0.02, 0.04)` | schedule.py:104,52 | super-exponential drift | PLAN (Sornette LPPL qualitative) | fit LPPLS (Johansen-Ledoit-Sornette) to GSY's 40 run-ups or Nasdaq 1998-2000 | MED |
| 41 | `g_max = 0.012` (json) / `G_MAX = 0.02` (module) | events.py:32; hazard.json | mania cap | CAL (A5) | symptom of unanchored kappa; report share of mania days at the cap | MED |
| 42 | hazard `h0 = 3e-4`, `b = 6.0`; grid and score weights | hazard.json; calibrate_hazard.py:50-65 | P(top), peak P/V | CAL to plan targets (~50 % topped; P/V 1.6-2.5); score weights ARB | GSY 2019 Table 4 logits give b; derive h0 from horizon; peak P/V band has no source | HIGH |
| 43 | post-top U(10, 30) d, drop U(0.30, 0.50) | schedule.py:105-106 | reversal | PLAN | post-peak drawdown speed in GSY's crashing episodes | LOW |
| 44-45 | blow-off = last third; hazard evaluation | events.py | label | PLAN | state (enters L2b classes) | LOW |
| 46 | sustained-bull `mu ~ U(0.0015, 0.0025)` | schedule.py:75,80 | control drift (+35-65 %/200 d) | PLAN (back-solved to an unsourced +30-80 % band) | 200-day returns in GSY's non-crashing run-ups or top-decile winners (CRSP) | MED |
| 47 | `LAM_SB = 0.15` | events.py:33 | forces x -> 0 in the control | CAL (A4) | no literature possible; stop forcing x and report realised x, or sweep the band | HIGH |
| 48 | crash validity (min x <= -0.10, MDD >= 20 %) | generator.py:203-206 | rejection | PLAN (20 % ~ Mishkin-White; -0.10 unsourced) | keep 20 % with citation; derive -0.10 from theta | LOW |
| 49 | bull validity `max x >= 0.30` | generator.py:209 | rejection (5.7 %) | PLAN | tie to sourced peak P/V | MED |
| 50 | SB validity `x in [-0.10, 0.15]`, `V_T/V_1 >= 1.2` | generator.py:212-214 | rejection 40 % | PLAN (no source) | accepted control is a selected smoother sub-population; characterise accepted vs rejected | HIGH |
| 51 | `MAX_ATTEMPTS = 50`; rejection target < 5 % | generator.py:38 | conditioning | CFG / PLAN | state | LOW |
| 52 | jitter U(-5, 5) d | schedule.py:70 | observable clocks | PLAN | lead/lag from news/volume event studies; sweep 0/5/10 on L2b | LOW |

### 1.5 Observables

| # | Parameter | File:line | Controls | Prov. | Proper justification | Sev. |
|---|---|---|---|---|---|---|
| 54 | `EPS_NOISE_SD = 0.10` | observables.py:34 | P/E noise, leakage dial | PLAN (unverified) | dispersion of quarterly EPS around trend (Foster 1977; Compustat 10-20 %); sweep 0.05/0.10/0.20 | MED |
| 55 | `ANN_LAG = (25, 35)` | observables.py:35 | staleness | LIT-adjacent (SEC 40-day 10-Q deadline) | Compustat RDQ minus quarter end; cite | LOW |
| 56 | `K_RANGE = (14, 22)` | observables.py:36 | fair P/E prior spread, leakage | PLAN (S&P trailing P/E mean 19.4 / median 17.7; single-stock IQR "12-30 approx.") | Compustat cross-section P10-P90 ~ 10-35; U(14, 22) is far tighter than reality, which is why k*P/PE recovers V to 15 % median APE; sweep width on L1/L2 (listed as E6 sensitivity, never run) | HIGH |
| 57 | `PAYOUT = 0.35` | observables.py:37 | dividend level | LIT-adjacent | Compustat payout distribution | LOW |
| 58 | `DPS_STICKY = 0.7` | observables.py:38 | smoothing | PLAN (Lintner speed ~0.3/yr applied per quarter) | Lintner / Brav et al. 2005; convert to quarterly | LOW |
| 59 | `ANALYST_RHO = 0.95`, `ANALYST_SD = 0.15`, 5-day update | observables.py:39-41 | analyst error, leakage | PLAN (no source) | Brav & Lehavy 2003; Bradshaw-Brown-Huang 2013: target-price errors sd ~30-40 %, persistent; 0.15 is optimistic; sweep 0.15/0.30/0.45 on L2 and L5 | HIGH |
| 60 | `SENT_RHO = 0.85` | observables.py:42 | sentiment persistence | PLAN (weekly AAII anchor used daily) | daily news-sentiment AR(1) (RavenPack / Tetlock 2007) | MED |
| 61 | `SENT_B_RET = 0.25`, `SENT_EPS = 0.25` | observables.py:43-44 | corr(s, r) | PLAN (chosen to hit item 12 band; band from a level correlation misread as return correlation) | Tetlock 2007 Table II; Boudoukh et al. 2013; typically 0.1-0.3 | MED |
| 62 | sentiment offset `0.6 tanh(2x) + 0.3 tanh(ret20/0.15)` | observables.py:70 | sentiment reads x directly (main non-price leakage channel) | PLAN (no source for any constant) | Baker-Wurgler 2006/2007 magnitudes; fit s ~ log(P/V_hat); sweep the 0.6 loading on L2 selectivity | HIGH |
| 63 | `SENT_SD_REF = 0.35` | observables.py:45 | scale | ARB (undocumented) | use realised sd | LOW |
| 64 | `b_pred = 0.0008`, `b_rev = 0.0006` | generator.py:86-87 | sentiment predictiveness | LIT (Tetlock 2007) | also cite Tetlock et al. 2008 firm-level | LOW |
| 66 | `VOL_RHO = 0.65` | observables.py:48 | volume AC(1) | PLAN (approx. anchor) | fit on CRSP; Lo & Wang 2000 | LOW |
| 67 | `VOL_B_ABS_R = 0.25` | observables.py:49 | volume-|r| link | CAL-by-design (raised from 0.15 to hit item 7) | Karpoff 1987 / Gallant-Rossi-Tauchen 1992 elasticity | LOW |
| 68 | `VOL_B_ABS_X = 1.2` | observables.py:50 | volume rises with |x| (an x channel) | PLAN (no source) | sweep on L2 selectivity | MED |
| 70 | IV premium 0.20, stress 0.35 (top-decile variance), floor 12 | observables.py:52-54,152-155 | IV level and VRP | PLAN (VRP anchors are additive, index-level; 0.35, floor 12 and the decile trigger unsourced) | single-stock VRP (OptionMetrics; Bollerslev-Todorov 2011); IV is a state-based clock; sweep the quantile on L2b | MED |
| 71 | `PE_CAP = 200` | observables.py:55 | cap | ARB (v1 legacy) | data-driven P99 | LOW |
| 72 | technicals SMA 20/50, RSI 14, MACD 12/26/9, trend +-2 % | observables.py:146-171 | indicators | LIT/convention | state +-2 % as design | LOW |

### 1.6 Resolvability, targets, harness

| # | Parameter | File:line | Controls | Prov. | Proper justification | Sev. |
|---|---|---|---|---|---|---|
| 75 | theta = 0.05 (set {0.03, 0.05, 0.08}) | synthetic_market.py:39; metrics_v2.py:26 etc. | what counts as resolvable; oracle switching; MCR; coverage | PLAN, explicitly "stated, not derived" | derive from observable-implied error in x (L5 RMSE) or a cost break-even; sweep {0.03, 0.05, 0.08, 0.12} through every headline metric | HIGH |
| 76 | bands 0.70-0.90 / 0.40-0.60 / 0.00-0.20 | targets.py:11-16 | MAS, MCR, oracle, starts | LIT (Morningstar, Fidelity, Vanguard, Merton) | best-sourced; add the JFE-spread sensitivity that targets.py:35 defines but nothing uses | LOW |
| 77 | `HALF_WIDTH = 0.10` | targets.py:17 | band width | PLAN | Morningstar categories are 15-20 pp wide; show MAS ranking stability over 0.05/0.10/0.15 | LOW |
| 80 | `DEAD_BAND = 0.01` | portfolio_v2.py:26 | no-trade zone | PLAN | rebalancing-band literature (Donohue-Yip 2003: 2-5 pts at 5 bp); sweep | LOW |
| 81 | `cost_bp = 5.0` | portfolio_v2.py:69 etc. | friction | LIT | run {0, 5, 20} on LLM cells | LOW |
| 83 | temperature 0.2 | v2_agent.py:38 | sampling | CFG (paper said 0.0) | state; sensitivity 0.0/0.2/0.7 | LOW |
| 86 | trader band (0.4, 0.6) in runner vs (0, 1) in baselines/oracle | runner_v2.py:100; baselines_v2.py:69; metrics_v2.py:46 | inconsistent | ARB | trader has no band; band_mas should be NaN | MED |
| 87 | stateful window 20, budget 60000, summary every 10 with 5 raw, 120-word cap, ai[:160], chars/4 | stateful_agent.py:44-45,122-139 | context design of the decay thesis | ARB ("cheapest design") | pre-register window length as a swept factor {5, 20, 50, full}; cite Liu et al. 2024 | MED |
| 89 | grid defaults (5 seeds, 3 reps) | arms_v2.py:105-113 | experiment size | CFG (no power analysis) | power analysis from pilot between-seed variance | MED |
| 90-93 | sleeve mask 0.05; v1_rule $1 threshold; baseline windows | metrics_v2.py; baselines_v2.py | - | ARB / convention | state | LOW |

### 1.7 Audits, checklist thresholds, statistics

| # | Parameter | File:line | Controls | Prov. | Proper justification | Sev. |
|---|---|---|---|---|---|---|
| 94 | seeds 50 (checklist), 20 (T=800), 50 (audit), 60 (hazard), 12+10 (L5), 10 (multi-asset); T = 200/800 | stylized_facts.py:529; synthetic_market.py:262-319; observables_oracle.py:44 | precision of every pass/fail | CFG (plan ">= 50"; no power analysis; at n = 50 an 80 % share criterion has a +-11 pp 95 % CI) | per-item power calculation; 200+ seed final run (promised in DECISION_LOG, not done) | MED |
| 95-110 | checklist item thresholds (1: LB p>0.05 in 80 %, |ACF| < 0.15; 2: kurtosis > 1.5 in 80 %, Hill 2.5-5; 3: LB|r| p<0.01 in 80 %, ACF|r|(1) 0.1-0.4; 6: 70 %; 7: Spearman 0.2-0.5, AC 0.5-0.8, Shapiro p>0.01 majority (A1); 9: ACF >= 0.98, hl >= 60, sd 0.08-0.20 on T=800 (A2); 10: R2 > 0.7, spread >= 20 pp (A7); 11: topped 40-60 %, P/V 1.6-2.5; 12: ACF 0.7-0.9, corr 0.25-0.55; 13: IV 25-35 / 60-100, corr 0.4-0.8, IV-RV +10..+25 in panic (rewritten); 15: < 80 %; 17: < 5 %; 20: MDD -20..-65, sigma 1.4-2.2, worst day -6..-15) | stylized_facts.py:107-466 | pass/fail | PLAN; several moved to what the generator produces (9, 10, 13, 17) | replace every band with an empirical P10-P90 from a stated real-data sample (CRSP large caps on 200-day windows; OptionMetrics for IV); label tuned items as calibration | HIGH (9, 11), MED (3, 12, 13, 17, 20), LOW (others) |
| 111 | L1 `NOISE_FLOOR = 0.01`; A6 rule | leakage_audit.py:57,166-167 | inversion pass | ARB (hard-coded 1 %); A6 after raw rule failed | derive floor from sd(x) or theta; report full APE distribution | MED |
| 112 | L2 absolute thresholds (calm R2 <= 0.30, sign <= 0.70; event R2 < 0.90, MAPE >= 10 %) | leakage_audit.py:280-281 | value-leak gate (fails by construction) | PLAN "design choice"; inconsistent with blocks 1/4 | derive the price-only bound analytically from sigma_V and the x half-life; gate on selectivity vs that bound | HIGH |
| 114 | `L2B_MARGIN = 0.10` | leakage_audit.py:58 | phase-clock gate (passes at +6.6) | PLAN, "frozen after the E1 calibration run" (after the value was known) | margin relative to majority-class and price-only accuracy; label-permutation null | MED |
| 115-117 | N_LAGS 5; surrogate hyperparameters; MAX_ROWS 30000 | leakage_audit.py:59-61,180-183,382 | attacker strength | CFG (untuned attacker understates leakage) | CV hyperparameter search; 20-50 lag surrogate | LOW |
| 119 | salience WINDOW 25 d; RF 200 trees etc. | salience.py:27,61-101 | primary measurement | PLAN / CFG | stability over 10/25/50-day windows; CV the RF | MED |
| 120 | gate thresholds (KW p<0.01; Cliff's delta >= 0.47; band-hit 80 %; AUC 0.8; RF share 0.5, R2 0.5) | salience.py:151; separability_gate.py:380-403 | model inclusion | PLAN (0.47 is Romano et al. 2006 "large", uncited; others unsourced) | cite; null distribution from the O3 ceiling arm | MED |
| 121 | gate RF (300 trees, 20 reps) vs salience RF (200, 10) | separability_gate.py:71-75 | inconsistent surrogate specs | CFG | unify | LOW |
| 122 | stats: 25-day windows, 1000 bootstrap, 500 shifts, 2000 flips, BH | stats_v2.py | inference | CFG | document approximations | LOW |
| 123 | FW SMM: 10 hand-picked tickers 2000-2024, 9 return moments, 200 bootstraps, NM 150 iters, acceptance J < 50 and 20 % improvement, J-profile with 1/target^2 weights | calibrate_fw.py:41-166 | the failed estimate | ARB (survivorship-biased ticker list; acceptance rule has no statistical basis; profile uses a proxy weight) | random sample of >= 100 CRSP large caps incl. delisted; chi-square critical value (df 4, 9.49 at 5 %); store W; fix units (#10) first | MED |

### 1.8 Circular justifications (parameter <-> plan <-> checklist)

1. phi / half-life 150 <-> item 9 (thresholds raised from 20-60 d / 2-6 % to >= 60 d / 8-20 % because FW could not meet them; phi set to clear 60 d; window moved to T = 800 by A2).
2. hazard (h0, b, g_max) <-> item 11 (grid-searched to 40-60 % topped and P/V 1.6-2.5; P/V band unsourced).
3. sbar 0.017 <-> item 20.
4. panic_mult 5 <-> item 13 (IV-RV band rewritten to match the multiplicative premium).
5. alpha/gamma/beta/jump_rate <-> items 2, 3, 6, 8.
6. delta set <-> items 10 and 20.
7. LAM_SB and the SB validity band <-> item 17.
8. VOL_B_ABS_R <-> item 7.
9. sentiment 0.25/0.25/0.85 <-> item 12.
10. L2B_MARGIN 10 pp <-> item 16 (frozen after the result existed).
11. A6 (L1) and A1 (item 7) pass rules re-operationalised after failing.

## Section 2. Top 15 most consequential unjustified or weakly justified parameters

1. `price_scale = 100` in the FW misalignment term. Likely wrong units; saturates the switching so the engine is an AR(1) with a fixed weight, and makes phi invisible to return moments by construction (so the "non-identification" conclusion must be redone).
2. Calm mispricing half-life 150 d (phi 0.463). The one parameter that was supposed to be estimated is a hand constant chosen to clear a moved floor; docs give four different values.
3. `sigma_V = 0.006`. Decides that a long price average recovers V to 4 % MAPE (the structural L2 failure); cited only qualitatively.
4. theta = 0.05. Stated, not derived; defines correctness, oracle switching, MCR, coverage.
5. Error-correction gains 0.10/0.05/0.10. Unsourced tracking gains that decide how much of event dynamics is script vs process.
6. Hazard (h0, b, g_max) and the 40-60 % / P/V 1.6-2.5 targets. Targets from a 2-year industry statistic and an unsourced P/V band; score weights arbitrary.
7. Sustained-bull forcing LAM_SB = 0.15 and validity band [-0.10, 0.15]. No possible literature; 40 % rejection means a selected smooth sub-population.
8. GJR-GARCH (alpha, gamma, beta, sbar, df, panic_mult). Every value moved off the anchor to raise pass rates.
9. `K_RANGE = (14, 22)`. Far narrower than the real P/E cross-section; the leakage dial listed as an E6 sensitivity and never run.
10. `ANALYST_SD = 0.15`, rho 0.95. Optimistic versus target-price error literature (30-40 %); a near-direct V channel.
11. Sentiment offset loadings and `VOL_B_ABS_X = 1.2`. Main non-price leakage channels, unsourced.
12. L2 absolute thresholds and `L2B_MARGIN = 10 pp`. Design numbers inconsistent with blocks 1/4; margin frozen after the data existed.
13. Checklist bands used as calibration targets (items 9, 11, 13, 20).
14. Seeds/horizon (50, T = 200; 20 at T = 800; 60 hazard; 12/10 L5) with no power analysis; four items within one sd of their thresholds; the promised 200-seed run not done.
15. Stateful context window 20 / budget 60k / summary cadence as single unsourced values for the decay thesis.

## Section 3. Parameters in code not in any doc, and doc/code mismatches

Not documented: `min_resolution = 10` and overflow floors; `STAB_RAMP_DAYS = 30`; `SENT_SD_REF = 0.35`; `SIGMA_R_REF`; IV stress trigger = top decile; `PE_CAP = 200`; module hazard fallbacks (0.0015, 6.0) differing from calibrated 0.0003; `pilot_stats(sd_e = 0.016)`; `a` clip +-50; trader band (0.4, 0.6) in runner vs (0, 1) elsewhere; sleeve > 0.05 mask; v1_rule $1 threshold; random-baseline seeds; audit seed encodings; L5 train seeds 500-511 and HGB settings; all surrogate hyperparameters; two different RF specifications (salience vs gate) for one pre-registered surrogate; stateful chars/4, ai[:160], 1200-char cap, MANDATE_WORDS list; runner failure rule 10 % of T; calibrate_fw ticker list, filters, optimiser, acceptance rule, J-profile weights; calibrate_hazard score weights and grid; arms_v2 grid defaults.

Doc/code mismatches: sustained-bull variance multiplier (code 1.0; CALIBRATION_REPORT.md:9 and E1 spec line 74 still print 0.25); jump rate (code 0.010; variant table says final = 0.008; the shipped configuration was never run in the variant table); FW fallback half-life (docs say 60-120, 120, 90, 150; realised 72); G_MAX 0.02 in module vs 0.012 live; floors_and_ceilings uses the mandate oracle as ceiling for mdd and return, which the plan does not state; `targets.py:35` JFE_SPREAD exists but nothing computes the pre-registered spread comparison.

**Bottom line.** Of the parameters that matter most for the benchmark's validity (mispricing persistence and units, sigma_V, theta, the tracking gains, the hazard, the sustained-bull forcing, the leakage dials k / analyst sd / sentiment loading, the L2/L2b thresholds), none is currently fitted to data and none has a variability analysis beyond the checklist. The published sensitivities are checklist-only; no LLM-outcome sensitivity to any generator parameter exists. The single data-fitting attempt (SMM) likely failed for a unit-convention reason the team itself flagged as unverified.
