# Phase 2 report (v2.1): the mispricing engine and its persistence

Date: 1–2 September 2026. Working tree on `main` at commit `d6e3b24` (the v2.1 Phase-1 state) plus this
phase's changes; nothing committed, no branch, no paid API call. Governing documents:
`V2_1_IMPROVEMENT_PLAN.md` Section 6, `PREREG_PHASE_2.md` (written before any run) and
`PREREG_PHASE_2_ADDENDUM.md` (§1–§3: designs found unmeetable or compute-bound and corrected in documented steps
before the runs they govern; §4: the three post-review extensions, each with its rule fixed before its run).
Compute: the local 8-core reference machine throughout — **no result in this report comes from another
machine**, so the Phase-1 offloaded-computation question (`PHASE_1_REPORT.md` §6.6) does not arise here.

**Status: Phase 2 complete, reviewed, and extended on the review's findings (2 September 2026); stopping.
Phase 3 not started.** The review's three experimental pointers were run, not deferred — §3.7 (is the surrogate
biased against an exact bound?), §3.8 (does the benchmark still discriminate?) and the sweep levels inside the
fitted interval (§3.6) — and its two presentational findings are corrected in §3.2 and §5.3, with my own earlier
reading of the sub-period acceptance withdrawn (P2-15). Designs for the three extensions are in
`PREREG_PHASE_2_ADDENDUM.md` §4, fixed before each run. Every seed count below is the one actually run, and §7
lists what was not run and who owns it. **Three inputs were found wrong and corrected with evidence, one of
them my own**: the plan's SABCEMM target (P2-1), Phase 1's `s_x_fit` (P2-6), and this report's first reading of
the sub-period acceptance (P2-15).

**What changed in the environment.** The mispricing engine is now **AR(1)+GJR-GARCH-t** (`ar1_fit`) with a
**7.50-day** half-life [3.81, 23.61] and **σ_V = 0.01220** [0.01066, 0.01419], both FIT; the Franke–Westerhoff
units bug is fixed (`price_scale = 1`, LIT); the two known defects Phase 2 owned are closed. The state was
re-frozen, re-hashed and re-audited.

**The findings the team has to weigh** (§5). The panel implies a mispricing of **±2–3 % with a half-life of
5–13 days** against the environment's ±17.5 % at 150 days. That gives **more** oracle decisions per run
(median 2–3 in three of four scenarios, holding across 5–10 d) but **much lower coverage** (0.13 in flat against
0.73) — and the benchmark **still discriminates**: the G1 ordering holds in all four scenarios, with the
observables-oracle-to-trivial spread narrowing by a third in flat and a half in sustained bull, and MCR
undefined on 4 % and 10 % of those runs. The fitted engine also **trades field leakage for price leakage**
(full-field calm R² 0.82 → 0.35, level-free calm 0.09 → 0.34), and the level-free surrogate is now shown to be
**unbiased against an exact bound**, so that rise is a real channel worth about +0.10 of R² rather than an
artefact.

---

## 1. Literature review

Every source below was **read at first hand on 1 September 2026** for this phase; nothing is quoted from a
secondary source or from memory. Values are used as **anchors beside** fitted values, never as tolerances.

| Statistic / statement | Where used | Status | Source |
|---|---|---|---|
| FW 2012 eqs (1), (5)–(7), (DCA), (HPM); p_t is the **natural-log** price and r_t := 100(p_t − p_{t−1}) | E2.1's units question; `tools/phase2/fw_pure.py` | read-and-correct | Franke & Westerhoff 2012, JEDC 36:1193–1211 (PDF at the Bamberg URL of PLAN §0.2) |
| FW 2012 Table 1, DCA-HPM: φ 0.12, χ 1.50, α_o −0.327, α_n 1.79, α_p 18.43, σ_f 0.758, σ_c 2.087; μ = 0.01, β = 1 | verification V1 of `envs/v2/mispricing.py::FW_INDEX_2012` | read-and-correct — **all nine match the code exactly** | as above |
| FW 2012 Table 2: DCA-HPM moment-specific bootstrap p = 32.6 % | quoted beside E2.3's acceptance | read-and-correct | as above |
| FW 2012 **Table 4**, DCA-HPM moment coverage ratios: joint **10.1 %**; per moment 98.1 / 79.5 / 75.8 / 98.5 / 65.5 / 73.7 / 59.5 / 39.4 / 32.4 | **E2.1's primary reproduction target** | read (new to this programme — not previously cited) | as above |
| FW 2012 **Table A1**, empirical moments with 95 % CIs (S&P 500, 1980–2007) | E2.1's coverage intervals; anchor beside the panel's moments | read | as above |
| FW 2012 Appendix A2: block bootstrap, 250 d for the five short-memory moments and 750 d for the four long-memory ones, B = 5,000, W = Σ̂⁻¹; eq. (9)'s p-value construction | E2.3's weight matrix and acceptance | read | as above |
| SABCEMM Table 1 (200 runs × 7,000 steps): **DCA-HPM excess kurtosis 10.033, Hill 2.481, average chartist share 0.1674**; DCA-WHP 8.01 / 3.1192 / 0.2227; DCA-WP 7.7600 / 3.1314 / 0.2285 | E2.1's secondary arm | **read-and-WRONG in the plan** — see §3.1 | Glas, Trimborn, Otte et al., arXiv:1812.02726 |
| Pruna et al. 2016 Table 1: φ 0.121, χ 1.555, σ_f 0.592, σ_c 1.917, α_0 −0.301, α_n 1.990, α_p 22.741 | verification V2 of `PRUNA_2016` | read-and-correct — **all seven match the code exactly** | Pruna, Polukarov & Jennings 2016, arXiv:1604.08824 |
| Pruna et al. 2016 eq. (10): p^f a GBM with μ_p 0.01 and σ_p 0.157 | **not used** | read-and-**not usable**: the paper calls σ_p a "percentage volatility" of a GBM in p^f while p^f enters the model as a log value, so its units cannot be resolved from the paper. It is quoted nowhere as a value or a tolerance; the fundamental's volatility is fitted (E2.3). | as above |

### 1.1 Inherited numbers verified before use

The plan's rule is to verify inherited figures rather than trust them, including Phase 1's and Phase 0's.

| # | Claim | Result |
|---|---|---|
| V1 | `mispricing.py::FW_INDEX_2012` = FW 2012 Table 1 DCA-HPM | **confirmed**, all nine parameters, exactly |
| V2 | `mispricing.py::PRUNA_2016` = Pruna Table 1 | **confirmed**, all seven parameters, exactly |
| V3 | The plan's SABCEMM target "chartist share 0.23 / excess kurtosis 7.8" for DCA-HPM | **wrong** — §3.1 |
| V5 | Phase 0's pilot constants n̄ = 0.9976485039121478, w̄ = 0.7611251383007557, φ = 0.4631873331666089 | **confirmed** by re-running `pilot_stats` on the reference machine (identical to 16 digits) |
| V6 | `value.json`'s `h_fit` 4.824109112705985, `s_x_fit` 0.12857809971634016 and `sigma_V.fitted` 0.019572114532101025 equal `e1_2/decision.json` | **confirmed**, exactly |
| V4, V7 | the 150 d pull-rate / 147 d ACF(1) half-life, and the residual E[x] | recomputed in E2.5 and E2.4 — §7, §6 |

## 2. Pre-registration, and the team decisions applied

`PREREG_PHASE_2.md` fixed, before any run: the seed blocks, the 17-moment vector, the block-bootstrap weight
matrix and its shrinkage, the three engines and their free parameters, the optimiser and its start grid, both
acceptance criteria, E2.4's asymmetric decision rule with its consequences written in advance, E2.5's and E2.6's
designs, and — as runnable code (`tools/phase2/prereg_power.py`) — the decidability check behind every criterion.

**D3's application blank in the execution prompt is empty, so the prompt's default applies: option (b).** σ_V is
not applied before Phase 2; it enters E2.3 as a **free parameter**, jointly identified with the engine's pull
rate, and the fitted value with its interval is what is written to `value.json` at hand-over. D1 = C (hybrid,
WRDS not confirmed), D13 = mechanism C and D16 = full programme are in force unchanged.

**One design element was found unmeetable and corrected before the run it governs** (`PREREG_PHASE_2_ADDENDUM.md`
§1, with disclosure of what had been seen): the pre-registered rule "raise the path count until every
persistence moment's simulation noise is ≤ 0.30 data-bootstrap sd" has an empty acceptance set inside the
registered ladder — the measured ratios are 1.4–2.3 at 20 paths and still 0.68–0.93 at 100, and reaching 0.30
per evaluation would need ≈ 960 paths. The rule is re-scoped to where the noise enters a verdict: the optimiser
runs at 200 paths under common random numbers (a deterministic surface), and the **reported** moment vector and
J at θ̂ average K = 20 independent CRN replicates, which brings the reported standard error to ≈ 0.15 bootstrap
sd. Franke–Westerhoff's bootstrap p-value, which simulates at the data's own panel size, is unaffected and is
the primary acceptance criterion; the χ² verdict is secondary. Both J values are reported.

**One deviation from the pre-registration's execution plan, in the safe direction.** §11 placed the SMM fits on Kaggle, with a reference-row check before any offloaded number could be used. They were run on the **local reference machine** instead: the fits turned out to cost 1.5–3 h per cell rather than the many hours feared, four of them run concurrently on the four physical cores, and running them here removes the cross-machine reproduction question entirely (`PHASE_1_REPORT.md` §6.6). The reference row is still generated and locked by a test (`e2_3/reference_row.json`, `test_smm_reference_row`) so that any future offloaded fit can be checked against it.

## 3. Experiments and results

### 3.1 E2.1 — FW's own model reproduced, and a correction to the plan's stated target

**A correction found at source before any run.** The plan (§6.1, §6.2, marked "[changed: LOG §4.2]") states that
SABCEMM's DCA-HPM row is "average chartist share 0.23, excess kurtosis 7.8" and that "the first draft's
'0.17 / 10' pair is the DCA-WHP row". Read at source, SABCEMM's Table 1 is:

| model | excess kurtosis | Hill estimator | average chartist share |
|---|---|---|---|
| DCA-WP | 7.7600 | 3.1314 | 0.2285 |
| **DCA-HPM** | **10.033** | **2.481** | **0.1674** |
| DCA-WHP | 8.01 | 3.1192 | 0.2227 |

The "0.17 / 10" pair **is** the DCA-HPM row: the plan's correction inverted a reading that was right in the
first draft. The plan's own "0.23 / 7.8" matches no DCA-HPM figure and is closest to the **DCA-WP** row. The
plan is not edited (the execution prompt forbids it); the correction is logged as **P2-1** and E2.1 compares
against the corrected values.

**Design.** FW's own model — their price equation (5) with the two independent Gaussian demand noises (6)–(7),
DCA switching, the HPM attractiveness index, constant p\*, no GARCH, no jumps, no drift — at FW Table 1's
DCA-HPM parameters, at `price_scale ∈ {1, 100}` (the multiplier on (p_t − p\*) inside the misalignment term, the
only place the units convention bites). 200 runs, seeds 100001–100200. `tools/phase2/fw_pure.py`;
`generated/v2_1/e2_1/fw_repro.{json,md}`.

**Arm A (primary) — FW's own moment coverage criterion, T′ = 6,750.**

| convention | joint MCR | 95 % Wilson | FW Table 4 | contains 10.1 %? |
|---|---|---|---|---|
| **`price_scale = 1`** | **10.0 %** | [6.6, 14.9] % | 10.1 % | **yes** |
| `price_scale = 100` | 0.0 % | [0.0, 1.9] % | 10.1 % | no |
| `price_scale = 1`, 500-step burn-in discarded | 11.0 % | [7.4, 16.1] % | 10.1 % | yes |

**`price_scale = 1` is confirmed and `price_scale = 100` is refuted**, by the pre-registered rule and by a wide
margin: at scale 100 the switching term saturates, the chartist share collapses to 0.0028 and the ACF of |r| is
0.000 at every lag — the model has no structural stochastic volatility left at all. This is the plan's expected
bug fix, logged as **P2-2 (LIT)**.

Per-moment coverage ratios are **reported, not used as a criterion** (the pre-registration fixed this in advance
because the pilot had already shown they diverge):

| moment | data (Table A1) | sim mean, scale 1 | coverage, scale 1 | FW Table 4 | sim mean, scale 100 | coverage, scale 100 |
|---|---|---|---|---|---|---|
| rAC1 | −0.008 | 0.0071 | 89.5 [84.5, 93.0] | 98.1 | −0.0026 | 99.5 |
| 1/Hill | 0.301 | 0.2565 | 23.0 [17.7, 29.3] | 79.5 | 0.1658 | 0.0 |
| vMean | 0.713 | 0.7499 | 48.5 [41.7, 55.4] | 75.8 | 0.6046 | 0.0 |
| vAC1 | 0.193 | 0.1580 | 99.0 [96.4, 99.7] | 98.5 | −0.0006 | 0.0 |
| vAC5 | 0.187 | 0.1544 | 77.0 [70.7, 82.3] | 65.5 | 0.0002 | 0.0 |
| vAC10 | 0.159 | 0.1454 | 90.0 [85.1, 93.4] | 73.7 | 0.0003 | 0.0 |
| vAC25 | 0.128 | 0.1220 | 87.5 [82.2, 91.4] | 59.5 | 0.0001 | 0.0 |
| vAC50 | 0.112 | 0.0923 | 83.5 [77.7, 88.0] | 39.4 | 0.0000 | 0.0 |
| vAC100 | 0.074 | 0.0560 | 72.5 [65.9, 78.2] | 32.4 | 0.0005 | 0.0 |

The **joint** ratio reproduces FW's published value almost exactly; the **profile** does not. Our tails are
thinner than theirs (1/Hill 0.257 against a data value of 0.301, coverage 23 % against their 79.5 %) and our
long-lag ACF coverage is higher (72–84 % against their 32–39 %). Two coverage errors of opposite sign happen to
give the same joint number. The discrepancy is reported, not explained: the equations, the parameters and the
moment definitions used here are transcribed from the paper with its equation numbers, and no re-tuning was
attempted.

**Arm B (secondary, no pass/fail) — SABCEMM's summary row, 7,000 steps.**

| convention | mean chartist share | 95 % CI | mean excess kurtosis | 95 % CI | Hill index |
|---|---|---|---|---|---|
| `price_scale = 1` | 0.2987 | [0.2917, 0.3057] | 1.781 | [1.744, 1.817] | 3.891 |
| `price_scale = 100` | 0.0028 | [0.0027, 0.0030] | 0.006 | [−0.002, 0.014] | 6.025 |
| scale 1, burn 500 | 0.2841 | [0.2767, 0.2915] | 1.826 | [1.789, 1.863] | 3.880 |
| *diagnostic*: scale 1, μ doubled | 0.2189 | [0.2139, 0.2239] | 1.746 | [1.706, 1.787] | 3.862 |

**SABCEMM's DCA-HPM row is not reproducible from FW's published equations at their published parameters**, under
either convention: their chartist share (0.1674) and excess kurtosis (10.033) are 11 and 220 half-widths from
what the equations give here. The pre-registered diagnostic — the one ambiguity in SABCEMM's own appendix, where
`EDF = ½(ed_f + ed_c)` with `ed_f = 2 n_f d_f` is self-cancelling under one reading and doubles the price impact
under another — moves the chartist share toward theirs (0.299 → 0.219) but not the kurtosis (1.78 → 1.75), so it
does not explain the gap either. Reported as an unexplained discrepancy with a published source. **No parameter
of any engine is set from arm B**, and nothing in Phase 2 depends on it: the units question is settled by arm A
against the original paper's own statistic.

### 3.2 E2.3 — the SMM done properly

**The data side** (`generated/v2_1/e2_3/data_moments.{json,md}`, `data_boot_<period>.npy`,
`weight_<period>.npy`). Set A, 417 flag-free full-history names, 6,289 trading days. Seventeen moments per
stock, pooled as the cross-sectional mean: FW's nine (returns in percentage points) plus VR(20/60/120/250/500)
and the ACF of log(P/SMA250) at 20/60/120. Weight matrix W = Σ̂⁻¹ from a **joint stock × block bootstrap**,
500 resamples per period, blocks of 250 d (the five short-memory moments), 750 d (the four long-memory ACF(|r|)
moments) and 1,250 d (the eight persistence moments) — FW's Appendix-A2 recipe extended to the horizons the
persistence moments need — shrunk 10 % toward its diagonal. Condition numbers: 493 (`full`), 389–879
(sub-periods), so the inverse is well behaved and the shrinkage is not doing the work.

| period | window | days | rAC1 | 1/Hill | vMean | vAC1 | vAC10 | vAC100 | VR20 | VR120 | VR500 | acf20 | acf120 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| full | 2000–2024 | 6,289 | −0.034 | 0.370 | 1.499 | 0.263 | 0.209 | 0.101 | 0.865 | 0.761 | 0.672 | 0.848 | 0.263 |
| p1 | 2000–2008 | 2,263 | −0.033 | 0.361 | 1.714 | 0.257 | 0.209 | 0.072 | 0.830 | 0.700 | 0.657 | 0.801 | 0.210 |
| p2 | 2009–2016 | 2,014 | −0.037 | 0.333 | 1.343 | 0.200 | 0.158 | 0.034 | 0.838 | 0.646 | 0.552 | 0.794 | 0.115 |
| p3 | 2017–2024 | 2,012 | −0.045 | 0.368 | 1.412 | 0.247 | 0.168 | 0.018 | 0.917 | 0.726 | 0.651 | 0.796 | 0.189 |

Beside them, FW 2012's Table A1 for the S&P 500 (1980–2007): −0.008 / 0.301 / 0.713 / 0.193 / 0.159 / 0.074.
A single stock is about twice as volatile as the index (vMean 1.50 vs 0.71) and fatter-tailed (1/Hill 0.37 vs
0.30), as expected; the survivor gap (REG-15) pushes the panel's tails and variance *down* relative to the full
universe, so the true single-stock values are, if anything, further from the index's. The variance-ratio curve
falls monotonically from 0.865 at 20 days to 0.672 at 500 — strong, slow mean reversion — which is the
persistence signal the SMM is being asked to identify.

**The fits.** `tools/phase2/e2_3_smm.py`, one file per (engine, period). Design as pre-registered except for the
simulation-noise re-scoping of `PREREG_PHASE_2_ADDENDUM.md` §1 and the compute-bound reductions of §2, both
fixed before the runs. Every fit records the best of its ≥ 20 named starts, the end J, the achieved evaluation
count, the DE convergence flag, the realised simulation standard error in bootstrap-sd units, and both
acceptance verdicts.

**A calibration check on the weight matrix, before any verdict is read.** The bootstrap distribution of
J[m_b] over the 500 block-bootstrap moment vectors of the full period has a median of **14.2** and a 95 %
quantile of **26.7** on 17 moments; a χ²(17) has a median of 16.3 and a 95 % point of 27.6. The weight matrix is
therefore well calibrated on its own bootstrap — a model whose J lands near 15–25 would be indistinguishable
from a resample of the data. That is the yardstick every J below is read against.

**The fits on the full sample.** Every cell ran at 200 paths × 5,000 days with common random numbers, K = 20
CRN replicates for the reported moments, differential evolution with the ≥ 20 named starts (chartist-active
regions included) and a Nelder–Mead polish.

| engine | free p | fitted parameters | start J (best named start) | J | df | χ² crit (5 %) | χ² | FW bootstrap p | **accepted?** | evals | max sim SE / boot sd |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ar1` | 3 | σ_V 0.01220, sbar 0.00870, h 7.50 d | 189.2 (`h60`) | 80.4 | 14 | 23.7 | no | 0.000 | **no** | 464 | 0.091 |
| `fw_v2` | 7 | σ_V 0.01145, sbar 0.01082, φ 30.78, χ 0.221, α₀ −0.062, α_n 8.313, α_p 8.409 | 247.5 (`v2_fallback_hl150`) | **29.2** | 10 | 18.3 | no | **0.005** | **no** | 2,056 | 0.132 |
| `fw_plus` | 8 | σ_V 0.01171, σ_f 0.874, σ_c 0.596, φ 15.59, χ 2.879, α₀ 0.657, α_n 0.982, α_p 3.991 | 276.7 (`fund_locked_fastpull`) | 110.3 | 9 | 16.9 | no | 0.000 | **no** | 2,200 | 0.089 |

**No engine is accepted, on either criterion.** The plan foresaw this ("plausible, since single stocks have jumps
and announcements that none of the three models"), and E2.4's rule is written for it. The realised simulation
standard error is 0.09–0.13 bootstrap sd everywhere, inside the 0.30 bound the addendum's correction was designed
to meet, so the rejections are not an artefact of simulation noise; and the single-CRN J differs from the
K-averaged J by 0.9 (`fw_v2`), 1.2 (`fw_plus`) and 2.1 (`ar1`) units, so the CRN displacement is small beside
the J values themselves.

**Where each model fails.** Residuals at the optimum, in bootstrap-sd units (m_sim − m_data):

| moment | `ar1` | `fw_v2` | `fw_plus` |
|---|---|---|---|
| rAC1 | +4.11 | +3.63 | +4.31 |
| 1/Hill | −5.51 | −3.00 | −6.64 |
| vMean | −3.54 | −0.63 | −4.26 |
| vAC1 | −6.26 | −2.67 | −7.32 |
| vAC5 | −5.22 | −2.57 | −6.21 |
| vAC10 | −5.09 | −2.64 | −6.08 |
| vAC25 | −4.71 | −2.25 | −5.65 |
| vAC50 | −4.80 | −2.44 | −5.57 |
| vAC100 | −3.79 | −2.10 | −4.13 |
| VR20 | +0.56 | +0.17 | +0.75 |
| VR60 | −1.76 | −1.29 | +0.09 |
| VR120 | −1.32 | −1.73 | +0.00 |
| VR250 | −0.74 | −1.99 | +0.44 |
| VR500 | +0.01 | −1.63 | +0.88 |
| acfSMA20 | −1.39 | −1.59 | −0.42 |
| acfSMA60 | −0.53 | −1.54 | −0.01 |
| acfSMA120 | +0.19 | −1.12 | +0.41 |

**The rejection is driven by the volatility block, not the persistence block.** For every engine the eight
persistence-carrying moments are matched to within 2.0 bootstrap sd (`ar1` and `fw_plus` to within 1.8 and 0.9),
while FW's nine are missed by 2.1 to 7.3 — the models produce too little volatility clustering, tails that are
too thin, and a raw-return autocorrelation that is too positive against a panel whose stocks bounce. **That
matters for how the fitted persistence should be read**: the half-life and the mispricing amplitude are
identified by the block the models *do* fit, so they remain the best available estimates of persistence even
though the models as a whole are rejected. It also identifies what a future engine would have to add — a
mechanism for cross-sectionally heterogeneous, long-memory volatility, which none of the three has.

**What the fitted FW engines actually look like.** The comparison's most awkward result:

| | chartist share | days with n_f > 0.99 | sd(x) | ACF(1) half-life | pull-rate half-life | μφ |
|---|---|---|---|---|---|---|
| `fw_v2` (best fit, J 29.2) | **0.043** | 95.7 % | 0.0796 | 6.34 d | 2.35 d | 0.308 |
| `fw_plus` (worst fit, J 110.3) | **0.235** | 0.0 % | 0.0151 | 5.95 d | 5.81 d | 0.156 |
| FW 2012's own DCA-HPM | 0.299 (§3.1) | — | — | — | ≈ 1,155 d | 0.0012 |

The engine that fits the panel best has an **essentially inert switching mechanism** — 4.3 % chartist days, n_f
above 0.99 on 96 % of them — reached from the opposite direction to v2's: α_n = 8.31 makes herding bistable and
locks the population, rather than `price_scale = 100` saturating the misalignment term. Its φ = 30.8 gives
μφ = 0.308, where FW's own paper observes that "the product μφ turns out to be around 0.01 or less"; it is the
FW functional form pushed far outside the region FW estimated. The engine that keeps a live
fundamentalist/chartist population (`fw_plus`, 23.5 % chartists, a smoothly varying share) fits worst of the
three. **On this panel the switching mechanism is not what the moments reward** — a finding that bears directly
on the deck's slide 6 whichever engine is adopted.

**The sub-periods — and a correction to how the two acceptance criteria should be read.** Run at the reduced
design of ADDENDUM §2 (DE maxiter 15, C = 50 Monte-Carlo replicates, no bootstrap refits) and reported as
descriptive; **no sub-period difference is called significant**.

| engine | period | window | days | half-life | sd(x) | J | df | χ² crit | **χ² accept** | FW bootstrap p | FW: *not rejected*? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ar1` | full | 2000–2024 | 6,289 | 7.5 d | 0.023 | 80.4 | 14 | 23.7 | **no** | 0.000 | no |
| `ar1` | p1 | 2000–2008 | 2,263 | 13.1 d | 0.049 | 100.1 | 14 | 23.7 | **no** | 0.000 | no |
| `ar1` | p2 | 2009–2016 | 2,014 | 8.9 d | 0.028 | 74.3 | 14 | 23.7 | **no** | 0.060 | yes* |
| `ar1` | p3 | 2017–2024 | 2,012 | 9.2 d | 0.026 | 44.7 | 14 | 23.7 | **no** | 1.000 | yes* |
| `ar1` | train | 2000–2016 | 4,277 | 5.2 d | 0.017 | 70.7 | 14 | 23.7 | **no** | not run (ADDENDUM §2) | — |
| `fw_v2` | full | 2000–2024 | 6,289 | 2.4 d (pull rate) | 0.080 | 29.2 | 10 | 18.3 | **no** | 0.005 | no |
| `fw_plus` | full | 2000–2024 | 6,289 | 5.8 d (pull rate) | 0.015 | 110.3 | 9 | 16.9 | **no** | 0.000 | no |

**\* Those two cells are not evidence of acceptance, and the report says so rather than leaning on them.**
The column is renamed here (and in the generated tables) from "accepted" to "**FW bootstrap: not rejected?**",
because the two criteria are different tests and only one of them is ever passed. Three things separate them:
the bootstrap statistic carries **no degrees-of-freedom penalty** for the 3–8 free parameters; it is evaluated
**in-sample at that window's own optimum**; and — decisively — **its yardstick moves with the window length**.
The yardstick is the data bootstrap's own J distribution, which for a well-specified weight matrix should be
χ²(17): median 16.3, 95 % point 27.6. Measured (`e2_3/weight_calibration.json`):

| period | days | bootstrap J median | ÷ χ²(17) median | J₀.₉₅ (the yardstick) | engine's J |
|---|---|---|---|---|---|
| full | 6,289 | 14.2 | **0.87** | 26.7 | 80.4 |
| train | 4,277 | 15.0 | **0.92** | 31.7 | 70.7 |
| p1 | 2,263 | 40.9 | **2.50** | 62.3 | 100.1 |
| p2 | 2,014 | 44.0 | **2.69** | 66.2 | 74.3 |
| p3 | 2,012 | 35.2 | **2.16** | 54.4 | 44.7 |

On the full sample and the training window the weight matrix is well calibrated — its own bootstrap J sits where
a χ²(17) says it should — and the acceptance question is meaningful. **On the three sub-periods it is not**: the
bootstrap J median is 2.2–2.7 × the χ² median, so Σ̂ understates the moments' sampling variability at ~2,000
days (with 8 non-overlapping 250-day blocks and one or two 1,250-day blocks, the block bootstrap cannot
represent the long-memory variability), the yardstick inflates from 26.7 to 54–66, and p3's J = 44.7 clears a
bar it would fail by a factor of two on the full sample. **The honest statement is therefore: no window passes
χ² on any engine, and the sub-period bootstrap p-values are not evidence of acceptance because their own null
distribution is mis-calibrated.** Logged as **P2-15**; my earlier reading of these two cells ("not rejected on
2009–2016 or 2017–2024") is withdrawn.

What the sub-periods *do* support is the quantity Phase 2 exists to fix: the **half-life is stable across every
window** — 13.1 / 8.9 / 9.2 / 7.5 / 5.2 days — the same 5–13 days on every split of the data, with no dependence
on the weight matrix's calibration, because it is a point estimate rather than a test. The `fw_v2` and `fw_plus`
sub-period cells were **not run**: a stated shortfall of the compute reduction, and one that costs nothing to
the decision, which is made on `full` and `train`, both well calibrated.

### 3.3 E2.2 — the firm-level persistence estimate and REG-5's rule

No new recovery study: Phase 1's full-scale one (32 cells, A and B at 200 replications, C at 50) already decided
usability, and E2.2 applies REG-5's rule to that verdict rather than re-deriving it. Full tables:
`generated/v2_1/e2_2/persistence.{json,md}`.

**Estimator A (variance ratios), pooled per Phase-1 sub-period.** Not usable by the recovery study (interval
coverage 0.00–0.01 in every cell), reported for completeness:

| period | n | h (d) | 95 % CI (stocks) | 95 % CI (blocks) | σ_V | s_x | J |
|---|---|---|---|---|---|---|---|
| full | 417 | 4.9 | [4.2, 5.6] | [0.9, 13.3] | 0.0205 | 0.024 | 80.0 |
| 2000–07 | 417 | 7.7 | [6.5, 9.0] | [3.7, 19.4] | 0.0206 | 0.034 | 17.1 |
| 2008–12 | 417 | 0.8 | [0.5, 1.0] | [0.0, 8.9] | 0.0259 | 0.012 | 38.1 |
| 2013–19 | 417 | 16.7 | [13.9, 20.0] | [8.5, 65.1] | 0.0139 | 0.032 | 3.9 |
| 2020–24 | 417 | 13.8 | [11.0, 17.0] | [2.3, 42.6] | 0.0193 | 0.050 | 94.7 |

Cross-sectionally (each stock's own VR curve fitted separately; descriptive, since A is not usable): median
h = **6.4 d**, P25–P75 **2.4–21.7 d**, median s_x **0.0252**, median σ_V 0.0164 over n = 417. Twelve per cent of
stocks fit above 500 d. The stock-bootstrap intervals are far narrower than the block-bootstrap ones (4.2–5.6 vs
0.9–13.3 days on the full sample), which is the same interval-coverage failure the recovery study measured.

**Estimator B (log(P/V̂) AR(1), Andrews median-unbiased), 2009-06…2024-12.** Not usable — the recovery study
found it returns ĥ ≈ 36–47 d whatever the truth, and the same on a panel with x ≡ 0:

| variant | n | median h (d) | 95 % CI | P25–P75 | median h (OLS) | share at the ρ-grid top |
|---|---|---|---|---|---|---|
| EPS basic × sector multiple | 367 | 256 | [223, 277] | 152–626 | 167 | 0.15 |
| EPS basic × market multiple | 367 | 290 | [268, 350] | 175–756 | 187 | 0.19 |
| EPS diluted × sector | 366 | 259 | [227, 286] | 155–596 | 168 | 0.14 |
| EPS diluted × market | 366 | 294 | [266, 353] | 177–780 | 186 | 0.18 |

B has **no sub-period breakdown**: its monthly panel starts in 2009-06 and any sub-period leaves fewer than the
60 months its own rule requires. Stated as a gap, not filled. 14–19 % of its per-stock estimates sit at the top
of the ρ grid, i.e. are censored rather than estimated.

**REG-5's rule applied to the current estimator set.** Only C survives usability, so the rule — *adopt the usable
estimator with the smallest RMSE whose data interval contains the other usable estimators' point estimates* —
reduces to "adopt the only usable estimator". The report states that plainly: **this is not evidence that C is
right on the real panel.** It is E2.3's acceptance test that can reject C's model, and it does (§3.2). Two
qualifications travel with the adoption, both inherited: the recovery panels come from C's own model, so the
usability test favours C by construction; and Phase 1's data-side J = 66.6 already indicated misspecification.

**What the three estimators actually agree on, once Phase 1's s_x is corrected (§1.1, V6b; P2-6).** With the
correction, A and C agree on all three quantities rather than two:

| quantity | A (variance ratios) | C (SMM, Phase 1) | C (SMM, this phase, `ar1`) |
|---|---|---|---|
| σ_V per day | 0.0205 [0.0197, 0.0213] | 0.0196 [0.0189, 0.0204] | 0.0122 |
| half-life of x | 4.9 d [4.2, 5.6] | 4.8 d [4.2, 5.4] | 7.5 d (8.1 d realised) |
| stationary sd(x) | 0.0237 [0.0216, 0.0258] | **0.0250** (was published as 0.129) | 0.0227 |

Estimator B's 256–294 d is not a statement about mispricing at all (the recovery study showed it measures the
EDGAR V̂ error), so the apparent factor-of-fifty disagreement of Phase 1 §4.2 is a disagreement between a
measurement and an artefact, not between two measurements.

**The levels E2.6 sweeps** follow the pre-registered union rule: the plan's {30, 60, 120, 250, 500} d, plus the
fitted half-life, which falls below the plan's grid.

### 3.4 E2.4 — the engine decision

Three candidates in one scaffolding, the pre-registered asymmetric rule applied unchanged. Files:
`generated/v2_1/e2_4/decision.{json,md}` and `engine_diagnostics.json`.

**(a) Acceptance — no engine is accepted.** §3.2's table: J = 80.4 / 29.2 / 110.3 against χ² critical values of
23.7 / 18.3 / 16.9, and Franke–Westerhoff bootstrap p-values of 0.000 / **0.005** / 0.000 against the 5 % bar.
`fw_v2` comes closest and still misses by a factor of ten in p.

**(b) Held-out prediction (fit 2000–2016, predict 2017–2024) — a dead heat.** D is the mean absolute residual
over the eight persistence-carrying moments in `test`-period bootstrap-sd units, averaged over 20 CRN replicates
at the test panel's own size (417 paths × 2,012 days):

| engine | D (8 persistence moments) | 95 % MC interval | D (all 17) | beats `ar1` by > 1 sd? |
|---|---|---|---|---|
| `ar1` | 1.512 | [1.335, 1.689] | 2.069 | — |
| `fw_v2` | 1.510 | [1.334, 1.687] | 2.069 | **no** (would need ≤ 0.512) |
| `fw_plus` | 1.488 | [1.286, 1.823] | 2.334 | **no** |

The three are within 0.03 of each other on a statistic whose null spread (PA3, measured at this exact
configuration) is 0.50 ± 0.27 for a single replicate and 0.11 for the 20-replicate mean. **The extra structure
buys nothing out of sample.** All three miss the held-out persistence moments by about three null standard
deviations, and by the same amount.

**The diagnostic that makes the verdict more than a threshold technicality.** Fitted freely on the training
period, **`fw_v2` chooses to be an AR(1)**: the optimiser drives α₀ = 3.97 and α_n = 3.91, which pins n_f at 1
on **100 %** of days, and with n_f ≡ 1 the FW recursion *is* x_{t+1} = (1 − μφ) x_t + w e. Its fitted (σ_V, sbar)
then match the `ar1` engine's train fit to four significant figures — 0.01162 / 0.00767 against 0.01163 /
0.00765 — and its J is 70.8 against 70.7. Given the freedom, the switching mechanism turns itself off.

| engine, period | chartist share | days with n_f > 0.99 | sd(x) | ACF(1) half-life | pull-rate half-life | μφ | J |
|---|---|---|---|---|---|---|---|
| `fw_v2`, full | 0.043 | 95.7 % | 0.0796 | 6.34 d | 2.35 d | 0.308 | 29.2 |
| `fw_v2`, train | **0.0004** | **100 %** | 0.0169 | 5.61 d | 5.54 d | 0.125 | 70.8 |
| `fw_plus`, full | 0.235 | 0.0 % | 0.0151 | 5.95 d | 5.81 d | 0.156 | 110.3 |
| `fw_plus`, train | 0.418 | 0.0 % | 0.0137 | 4.97 d | 4.96 d | 0.240 | 91.7 |

**The inherited known defect is fixed (verification V7).** Phase 1 registered the calm engine's residual
E[x] ≈ +0.012 in flat markets as a strict-xfail defect owned by Phase 2: +0.0126 [+0.0038, +0.0214] with
mean-zero jumps and +0.0113 [+0.0027, +0.0199] with jumps off, failing the ±0.02 margin by its upper limit. On
the adopted engine, the same design (1,000 flat paths, T = 200, seeds 150000+):

| | E[x] | 95 % interval | ±0.02 TOST |
|---|---|---|---|
| jumps on (placement `x_zero`) | **−0.00013** | [−0.00087, +0.00064] | **pass** |
| jumps off | **−0.00029** | [−0.00102, +0.00046] | **pass** |

The bias was the FW recursion's own — the misalignment term is even in x while the herding lock is not, so the
process spends longer on one side — and an AR(1) has no such asymmetry. The registry entry is cleared and
`test_flat_x_equivalence` is a hard test again. `e2_4/flat_x.json`.

**(c) Equivalence of the checklist and the level-free statistics**, incumbent against adopted, 200 seeds for the
checklist and the switch statistics and 100 for the level-free surrogate, both at `sbar` = 0.017. Reported with
intervals and **no pass/fail**, as pre-registered. The items that differ by more than their intervals:

| statistic | incumbent `fw_fallback_hl150` | adopted `ar1_fit` | differs? |
|---|---|---|---|
| checklist passes | 7 / 20 | 5 / 20 | — (counts, no interval) |
| oracle switches, median (flat / crash / bull trap / sustained bull) | 1 / 1 / 1 / 1 | **2 / 2 / 3 / 1** | **yes** |
| share of runs with ≥ 2 switches | 0.29 / 0.36 / 0.30 / 0.48 | **0.69 / 0.69 / 0.77 / 0.42** | **yes** (non-overlapping Wilson intervals in three scenarios) |
| sd(x) over 200 days | 0.077 / 0.148 / 0.232 / 0.023 | 0.034 / 0.075 / 0.105 / 0.019 | **yes** |
| resolvable share at θ = 0.05 | 0.73 / 0.81 / 0.84 / 0.05 | **0.13 / 0.39 / 0.53 / 0.03** | **yes** |
| **rejection rate, bull trap** | 0.06 | **0.94** | **yes** — see below |
| level-free R²(x), calm (best model) | −0.176 [−0.278, −0.104] | **+0.321 [0.153, 0.474]** | **yes** |
| full-field R²(x), calm (best model) | 0.697 [0.640, 0.742] | **0.342 [0.105, 0.490]** | **yes** |
| full-field R²(x), all phases (best model) | 0.856 [0.838, 0.872] | 0.643 [0.602, 0.678] | **yes** |

Three of these deserve saying out loud.

1. **The adopted engine leaks *more* to a level-free price reader on calm days and *less* through the full field
   set.** Calm level-free R² goes from −0.18 (the incumbent: a price-only reader does worse than the mean) to
   +0.32; calm full-field R² goes from 0.70 to 0.34. The direction is what the physics says: a fast, small
   mispricing is written into the recent returns, which is exactly what a level-free reader sees, while it is
   *not* visible in a slowly-updating valuation field. Whether +0.32 is acceptable is Phase 6's gate, not this
   phase's, and the Appendix-B bound at the parameters in force is 0.245 (§3.6) — the same marginal comparison.
2. **The bull-trap rejection rate jumps from 0.06 to 0.94.** The scenario's acceptance condition was calibrated
   against an engine whose x moved by ±0.23 over 200 days; with ±0.11 it is met on the first attempt only 6 % of
   the time. That is the selection effect review C.5 and weakness items 18/42 describe, now in a second scenario,
   and it is **Phase 4's** (E4's event formulation and its rejection rule). It is reported here as a consequence
   of Phase 2's engine, and put to the team in §5.
3. **The `ridge` and `mlp` surrogates blow up on the adopted panel's "all phases" rows** (R² of −1.6 × 10¹¹).
   With x's variance an order of magnitude smaller, the linear and neural surrogates are numerically unstable on
   pooled-phase data; the gradient-boosted tree is not. Every number above is the *best* model of its cell, so
   the blow-ups do not enter any comparison, but they are a warning for Phase 6's gate definition: a gate written
   on "the surrogate" must say which one, and must be robust to a target whose scale the generator can change.

**Decision: `ar1` — the AR(1)+GJR-GARCH-t engine — is adopted**, by the pre-registered rule: a FW engine is
adopted only if it is accepted at (a) *and* beats `ar1` at (b) by more than one bootstrap sd; neither is accepted
and neither beats it, so ties go to the simpler model. **No threshold was moved.** The honest statement of the
evidence is:

- *For* the FW form: on the **full** sample `fw_v2` fits far better than `ar1` (J 29.2 against 80.4; every
  residual smaller; bootstrap p 0.005 against 0.000). If the phase had used a fit statistic rather than an
  acceptance test, `fw_v2` would have won.
- *Against* it: it is not accepted; it does not predict the held-out period any better; on the training period
  it collapses to an AR(1); its fitted φ gives μφ = 0.31 where FW's own paper reports "around 0.01 or less", so
  it is the FW functional form far outside the region FW estimated; and its remaining switching is a bistable
  herding lock (96 % of days at n_f > 0.99) rather than the fundamentalist/chartist alternation the narrative
  describes. The variant that *does* alternate (`fw_plus`, 23.5 % chartists) fits worst of the three.

**Consequences, fixed in advance by the pre-registration and now in force:** every document names the engine
**AR(1)+GJR-GARCH-t**; the FW parameter sets stay in the code as named sensitivities with their v2 convention;
`test_fundamentalist_share` is removed with a note and its registry entry cleared (§4); the FW engines' numbers
are published beside the winner's, which is what makes the adoption credible rather than a default.

### 3.5 E2.5 — the half-life estimator table

Pure AR(1) (no GARCH, no V, no events — the table is a property of the **estimator**, not of the engine): true
half-life h ∈ {30, 60, 120, 150, 250, 500, 600} d × T ∈ {200, 800, 2000, 5000}, **200 seeds per cell**
(seeds 120001+). The Andrews (1993) median function m_T(ρ) is regenerated by simulation at each T rather than
interpolated from another T's table (20,000 replicates per ρ grid point at T = 200 and 800; 8,000 at T = 2,000
and 4,000 at T = 5,000 — the reduction is stated in the output because the OLS bias is O(1/T) and the function
is nearly the identity at long T). Full table: `generated/v2_1/e2_5/hl_table.md`. Decidability (PA4): the 95 %
half-width of the cross-seed median is 2.3–11.4 % of the median at 200 seeds.

**Naive ACF(1) half-life, median [P25, P75]:**

| true h | T = 200 | T = 800 | T = 2000 | T = 5000 |
|---|---|---|---|---|
| 30 | 18.0 [12.5, 26.5] | 26.0 [21.4, 31.9] | 27.2 [24.3, 31.0] | 29.1 [26.7, 32.5] |
| 60 | 20.4 [13.1, 33.5] | 43.7 [32.8, 58.3] | 52.8 [43.2, 63.2] | 56.2 [49.6, 63.2] |
| 120 | 25.6 [16.4, 43.5] | 66.9 [47.5, 110.8] | 96.6 [72.2, 130.5] | 104.2 [90.8, 126.0] |
| 150 | 28.8 [17.9, 49.0] | 74.7 [52.0, 113.3] | 105.5 [85.6, 142.0] | 132.0 [111.0, 164.9] |
| 250 | 30.2 [19.0, 58.7] | 92.6 [62.9, 153.2] | 154.4 [108.7, 226.9] | 210.9 [161.3, 256.8] |
| 500 | 29.9 [17.1, 69.6] | 101.1 [60.9, 186.4] | 227.0 [145.9, 337.4] | 331.2 [227.3, 457.3] |
| 600 | 28.9 [16.7, 57.9] | 118.4 [73.4, 220.6] | 249.3 [164.9, 349.3] | 370.1 [263.3, 563.5] |

**The finding the benchmark has to live with.** At **T = 200 — the horizon the agent actually experiences — the
naive estimate is 18–30 days whatever the truth is between 30 and 600 days.** The whole column spans 18.0 to
30.2 while the truth spans a factor of twenty. A half-life measured on a 200-day window is therefore not an
estimate of the generator's persistence at all; it is a statistic of the window length. This is review B's item
36 ("the half-life is an estimator artefact") reproduced at 200 seeds per cell with intervals, and it is why
every half-life this programme quotes must carry the horizon and the estimator that produced it.

**The median-unbiased correction does not rescue T = 200.** Its medians at T = 200 run 34 → 572 d as the truth
runs 30 → 250 d, but 18–48 % of the paths are **censored at the top of the ρ grid** (ρ = 0.9999, a half-life of
6,931 d), so those medians and every P75 in that column describe the ceiling, not h:

| censored share | T = 200 | T = 800 | T = 2000 | T = 5000 |
|---|---|---|---|---|
| h = 30 | 0.18 | 0.00 | 0.00 | 0.00 |
| h = 150 | 0.44 | 0.21 | 0.01 | 0.00 |
| h = 600 | 0.46 | 0.47 | 0.34 | 0.12 |

At T = 2,000 and 5,000 the correction works as advertised (medians 28.9 / 29.9 at h = 30, 142 / 150 at h = 150,
257 / 265 at h = 250) and the naive estimate is still biased low by 12–34 %. **The usable rule this table gives
the programme:** quote the analytic half-life from the pull rate (or ρ), report the median-unbiased estimate
only at T ≥ 2,000, and at T = 200 report the naive value as *"what a 200-day window shows"* with the caveat that
it is nearly independent of the truth.

**Checklist item 9's 60-day floor, re-read.** The share of paths whose naive estimate clears 60 days is 0.17 at
h = 150 / T = 200 and 0.69 at h = 150 / T = 800 — so a floor applied to a sample half-life is a statement about
the horizon, not about the generator. Review B's "only 55 % of T = 800 paths clear the floor" is of the same
order as the pure-AR(1) value here (0.69) but is not directly comparable, because the engine's x is not an
AR(1); the engine's own value is re-measured in §3.6.

**At the half-life this phase adopts, the estimator artefact disappears.** The table's grid starts at 30 days
because the plan's does; the adopted engine's fitted half-life is 7.5 days, and there the same code at 200 seeds
gives:

| true h | T = 200 (naive) | T = 200 (median-unbiased) | T = 800 (naive) | T = 5,000 (naive) |
|---|---|---|---|---|
| 7.5 d (full-sample fit) | **6.59 [5.22, 8.29]** | 7.83 | 7.20 [6.55, 8.20] | 7.47 [7.11, 7.77] |
| 5.2 d (train fit) | 4.68 [3.78, 5.63] | 5.26 | 5.08 [4.59, 5.58] | 5.19 [4.99, 5.41] |
| 9.2 d (2017–24 fit) | 7.55 [5.85, 10.22] | 9.20 | 8.58 [7.41, 9.75] | 9.15 [8.63, 9.69] |

A 200-day window is 27 half-lives at h = 7.5 d, so the naive estimator is biased low by only 12 % and the
median-unbiased one is essentially exact. **The half-life the benchmark quotes and the half-life the agent
experiences are the same number at the fitted persistence** — which they were not at 150 days, where a 200-day
window reported 29 d for a 150-d process. `e2_5/hl_at_fitted.json`.

**"What the agent experiences" on the adopted engine** (from E2.6's 200-seed panels at the fitted level, §3.6):
sd(x) within a 200-day run is 0.034 (flat) to 0.105 (bull trap); the median number of oracle target switches per
run is 2 (flat), 2 (crash), 3 (bull trap), 1 (sustained bull); the resolvable share at θ = 0.05 is 0.13 to 0.53.

**Verification V4** (`e2_5/v4_engine_half_life_check.json`): Phase 0's statements about the *incumbent* engine
were re-derived on this machine before anything changed — pull-rate half-life **149.93 d** (P0-6 says 150.0) and
three fresh 200,000-step pilots giving ACF(1) half-lives of 155.4 / 147.0 / 144.9 d with sd(x) 0.174–0.180
(P0-6/P0-7 say 141–155 d, mean 147, and sd(x) 0.175). Confirmed.

### 3.6 E2.6 — the persistence sweep

Levels {**7.5**, 30, 60, 120, 250, 500} d — the plan's five plus the fitted half-life, which falls below the
plan's grid — run under both matchings, on the adopted engine family (`ar1_hl<h>`). Seed counts as corrected in
`PREREG_PHASE_2_ADDENDUM.md` §3: **200 seeds** for the oracle-switch statistics (unreduced, because they feed the
16A checkpoint), **100** for the checklist, **50** for the level-free surrogate. Files:
`generated/v2_1/e2_6/sweep.{json,md}`, `checklist_<matching>_h<h>.{csv,md}`.

**Calibration of the innovation scale.** Under `sd` the innovation is rescaled so the realised sd(x) at
T = 5,000 equals the adopted engine's own value at the `sbar` in force (0.0386); under `innov` `sbar` is held at
0.017 and sd(x) moves with h.

| h (d) | sd(x) at sbar = 0.017 | sbar under matched sd | realised sd(x) after matching |
|---|---|---|---|
| 7.5 | 0.0386 | 0.01700 | 0.0416 |
| 30 | 0.0811 | 0.00810 | 0.0343 |
| 60 | 0.1024 | 0.00641 | 0.0420 |
| 120 | 0.1446 | 0.00454 | 0.0437 |
| 250 | 0.2216 | 0.00296 | 0.0427 |
| 500 | 0.2877 | 0.00228 | 0.0487 |

(The realised values scatter by ±10 % around the target: sd(x) is measured on 20 paths of 5,000 days, which is
short relative to a 500-day half-life. The realised value is what is reported, not the target.)

Two things about that table. **The level that defines the target is matched to itself by construction**: at
h = 7.5 d `sbar` stays at 0.017 because 7.5 is the level the target sd(x) was measured at, and the ±8 %
difference between 0.0386 and 0.0416 is seed noise between the two calibration passes, not a mismatch. And the
levels **5, 10 and 15 d were added after review** (`PREREG_PHASE_2_ADDENDUM.md` §4.3), because the adopted
half-life's interval is [3.81, 23.61] d and the original sweep had exactly one point inside it — a robustness
claim resting on the point estimate alone. The extension keeps the stored target so the cells already run stay
valid, and its seeds are keyed on the level value rather than the list index so adding levels cannot move an
existing one; the calibration table marks which pass each level came from. The level-free audits were **not**
extended.

**Oracle target switches per run — the 16A G3 input, and this phase's most consequential number.**
ISFJ, θ = 0.05, 200 seeds per cell; the full 48-row table is in `e2_6/sweep.md`. The event scenarios G3 is
written on are crash, bull trap and sustained bull:

| matching | h (d) | flat | crash | bull trap | sustained bull |
|---|---|---|---|---|---|
| | | med / share ≥ 2 | med / share ≥ 2 | med / share ≥ 2 | med / share ≥ 2 |
| **sd** | **5** | 2 / 0.68 | 2 / 0.70 | 4 / 0.85 | 1 / 0.42 |
| **sd** | **7.5 (fitted)** | **2 / 0.69** | **2 / 0.69** | **3 / 0.77** | 1 / 0.40 |
| **sd** | **10** | 2 / 0.70 | 2 / 0.69 | 2 / 0.69 | 1 / 0.40 |
| **sd** | **15** | 1 / 0.45 | 1 / 0.49 | 1 / 0.49 | 1 / 0.24 |
| sd | 30 | 1 / 0.23 | 1 / 0.32 | 1 / 0.29 | 0 / 0.06 |
| sd | 60 | 1 / 0.13 | 1 / 0.24 | 1 / 0.21 | 0 / 0.04 |
| sd | 120 | 1 / 0.07 | 1 / 0.20 | 1 / 0.21 | 0 / 0.04 |
| sd | 250 | 0 / 0.02 | 1 / 0.15 | 1 / 0.17 | 0 / 0.03 |
| sd | 500 | 0 / 0.01 | 1 / 0.14 | 1 / 0.10 | 0 / 0.02 |
| **innov** | **5** | 2 / 0.59 | 2 / 0.61 | 4 / 0.84 | 1 / 0.42 |
| **innov** | **7.5 (fitted)** | 2 / 0.69 | 2 / 0.69 | 3 / 0.77 | 1 / 0.40 |
| **innov** | **10** | 2 / 0.73 | 2 / 0.71 | 2 / 0.73 | 1 / 0.42 |
| **innov** | **15** | 2 / 0.73 | 2 / 0.69 | 2 / 0.65 | 1 / 0.42 |
| innov | 30 | 2 / 0.65 | 2 / 0.65 | 2 / 0.55 | 1 / 0.46 |
| innov | 60 | 2 / 0.55 | 2 / 0.56 | 1 / 0.46 | 1 / 0.45 |
| innov | 120 | 1 / 0.37 | 1 / 0.40 | 1 / 0.34 | 1 / 0.46 |
| innov | 250 | 0 / 0.21 | 1 / 0.26 | 1 / 0.23 | 1 / 0.47 |
| innov | 500 | 0 / 0.16 | 1 / 0.23 | 1 / 0.17 | 1 / 0.47 |

**The conclusion holds across most of the fitted interval, not just at the point estimate.** At h = 5,
7.5 and 10 d the median switch count is 2–4 in flat, crash and bull trap with 59–85 % of runs at ≥ 2;
it falls to a median of 1 only at h = 15 under matched sd. The bull-trap rejection rate is the other
monotone function of the level — 0.97 at h = 5, 0.94 at 7.5, 0.89 at 10, 0.50–0.64 at 15 — so the
selection problem §3.4(c) reports eases only as the amplitude recovers.

**This reverses the plan's expectation about G3, and it is worth stating precisely.** The plan's 16A note of
27 August reasons: *"the persistence literature read in Phases 1–2 (Summers 1986, Poterba–Summers 1988, Balvers
et al. 2000) points to half-lives of months to years, so a FIT persistence will give at most one decision per
200-day run"*, and forbids meeting G3 by shortening the half-life. **The single-stock panel says the opposite of
the index-level literature**: its transitory component has a half-life of days, not months, so at the fitted
persistence the oracle switches target **2–3 times** per 200-day run in flat, crash and bull-trap, with 69–77 %
of runs showing ≥ 2 switches — comfortably over G3's median ≥ 2 and share ≥ 0.5 in two of the three event
scenarios. **Sustained bull is the exception** (median 1, share 0.40) at every level and matching, because its
drift keeps x near one band edge. The fitted half-life is *not* a persistence "chosen to pass G3" — it is what
the panel gives, and it happens to help.

**What it costs is coverage, and that is the trade-off the team must weigh.** At the fitted level the
resolvable share (|x| ≥ θ = 0.05) is **0.13 in flat** and **0.03 in sustained bull** against 0.39–0.53 in the
event scenarios; at h = 500 under matched sd it is 0.56 in flat. Fast mean reversion means many crossings of the
band edge but a small amplitude, so the agent is asked to act often on a signal that is rarely large. The
`innov` arm shows the other corner: holding the innovation fixed and lengthening h raises both sd(x) and
coverage (0.39 → 0.87 in flat from h = 30 to 500) while the switch counts fall. **Persistence and coverage
cannot both be maximised**, and the sweep is the table that shows the price of each choice. Neither is decided
here: Phase 6 computes the gates on the frozen generator, and the choice between them is D3/D8.

**The checklist across the sweep**, 100 seeds per cell (the reduced count of ADDENDUM §3), beside the state
Phase 1 handed over, which passes **5 of 20** on the same panel:

| h (d) | matched sd | matched innovation |
|---|---|---|
| 7.5 (fitted) | 4 / 20 | 4 / 20 |
| 30 | 5 / 20 | 6 / 20 |
| 60 | 7 / 20 | 5 / 20 |
| 120 | 7 / 20 | 7 / 20 |
| 250 | 6 / 20 | 6 / 20 |
| 500 | 8 / 20 | 6 / 20 |

The adopted engine is **not worse on the checklist than the incumbent** — at h ≥ 60 it passes more items (6–8
against 5) and at the fitted 7.5 d one fewer. The absolute counts are low for both because several items carry
criteria calibrated against the v2 engine (item 20's calm-day magnitude band, item 9's 60-day half-life floor)
which the plan re-derives in Phase 6 from the panel, not here; the sweep's value is the *ordering* across levels,
not the level of the count. Per-item tables: `e2_6/checklist_<matching>_h<h>.md`.

**The level-free surrogate across the sweep** (matched-sd arm only, 50 seeds per cell — the reduction of
ADDENDUM §3; the matched-innovation arm was **not audited** and is listed as not run). Best model of the
level-free control set, R²(x) with its cluster-bootstrap interval:

| h (d) | calm | all phases | full-field, calm | Appendix-B bound (window avg) |
|---|---|---|---|---|
| **7.5 (fitted)** | **0.350 [0.231, 0.459]** | 0.566 [0.515, 0.608] | 0.124 [−0.119, 0.335] | **0.245** |
| 30 | −1.913 [−3.298, −0.975] | 0.692 [0.635, 0.737] | −0.721 [−1.275, −0.286] | — |
| 60 | −1.018 [−1.845, −0.493] | 0.793 [0.751, 0.826] | −0.389 [−0.702, −0.142] | — |
| 120 | −0.461 [−0.861, −0.224] | 0.836 [0.799, 0.859] | −0.111 [−0.381, 0.081] | — |
| 250 | −0.727 [−1.260, −0.415] | 0.698 [0.637, 0.739] | −0.119 [−0.425, 0.086] | — |
| 500 | −0.417 [−0.736, −0.235] | 0.678 [0.614, 0.725] | 0.167 [−0.074, 0.333] | — |

On **calm** days at every level except the fitted one the surrogate's out-of-sample R² is **negative** — it does
worse than predicting the pooled mean. That is not a failure of the audit but a property of the environment at
these amplitudes: under matched sd, a longer half-life makes x nearly constant inside a 200-day window, so there
is almost nothing in the level-free features to key on and the estimator overfits the training seeds. The
"all phases" column is high (0.57–0.84) because the event phases move x by a lot and the scripted drift is
visible in returns — which is a Phase-4/Phase-6 matter, not a persistence one. **No gate is applied here**;
Phase 6 owns the reference distributions and the seed counts, and 50 seeds gives intervals a third of a unit
wide.

**The Appendix-B bound, re-checked — and it now applies exactly.** The plan's inherited open item was that the
bound assumes log P = log V + x with log V a random walk and x an **AR(1)**, while Phase 1 had shown the FW
engine's x is not one. **The engine E2.4 adopted is literally that model**, so the bound describes the generator
without the approximation Phase 1 had to carry. Recomputed at the parameters in force
(`e2_4/kalman_bound_phase2.json`):

| configuration | σ_V | s_x | h | window average | day 200 | steady state |
|---|---|---|---|---|---|---|
| **handed over (σ_V 0.0122, sbar 0.017)** | 0.0122 | 0.0386 | 7.5 | **0.245** | 0.256 | 0.256 |
| at the fitted sbar 0.0087 | 0.0122 | 0.0227 | 7.5 | 0.119 | 0.123 | 0.123 |
| the v2 state Phase 1 handed over | 0.006 | 0.175 | 150 | 0.153 | 0.265 | 0.497 |
| panel estimate (estimator A) | 0.0205 | 0.0237 | 4.9 | 0.078 | 0.080 | 0.080 |
| panel estimate (estimator C, corrected) | 0.0196 | 0.0250 | 4.8 | 0.094 | 0.096 | 0.096 |

The measured level-free calm R² at the fitted level, **0.350 [0.231, 0.459]**, sits **above** the bound's 0.245
but its interval does **not lie entirely above it** (0.231 < 0.245), so under Phase 1's own reading of the rule
it is not a flagged excess — it is marginal, on 50 seeds, and it is exactly the comparison Phase 6 must make
properly on its own panel with pinned library versions. Reported here as an observation with the caveat, not as
a verdict. The direction is worth noting: raising σ_V and shortening the half-life both lower the bound, so a
generator fitted to the panel is harder for a level-free price reader to invert than the v2 one was at steady
state (0.26 against 0.50) — which is the leakage argument the whole programme exists to make, now with a fitted
parameter behind it.

### 3.7 E2.8 — the surrogate is not biased, so the excess over the bound is a real channel (post-review)

**Why this had to be settled here.** The adopted engine *is* Appendix B's model — a Gaussian AR(1) mispricing on
a random-walk fundamental — so the bound is exact rather than approximate. A surrogate sitting above an exact
bound has only two explanations: **(a)** the surrogate is optimistically biased (its feature construction, lag
block or cross-validation leaks), in which case every level-free leakage number in this programme is affected;
or **(b)** the generator has an information channel the bound does not model. Deferring that to Phase 6 would
have meant building a gate on a statistic whose validity was unknown. Design and rule fixed in
`PREREG_PHASE_2_ADDENDUM.md` §4.2 before the run; `tools/phase2/e2_8_bound_check.py`,
`e2_4/bound_check.{json,md}`.

**The test.** Simulate the bound's model and *nothing else* — no events, no jumps, no GARCH, no sentiment
feedback — build the **same** level-free features (`technicals_block` on the price path, then the audit's own
`add_level_free_columns` and 5-lag block), fit the **same** three surrogates with the **same** GroupKFold by
path and 500-resample cluster bootstrap, at three configurations spanning a 2.6× range of bound values.
200 paths × 200 days each.

| configuration | σ_V | s_x | h | analytic bound (window avg) | measured level-free R²(x) | above the bound? |
|---|---|---|---|---|---|---|
| **in force (Phase 2)** | 0.0122 | 0.0386 | 7.5 | **0.245** | **0.241 [0.214, 0.268]** | no |
| the v2 state Phase 1 handed over | 0.0060 | 0.1750 | 150 | 0.153 | 0.091 [0.044, 0.126] | no |
| the panel's own fit (estimator C, corrected) | 0.0196 | 0.0250 | 4.82 | 0.094 | 0.085 [0.070, 0.100] | no |

**Verdict: the surrogate is not biased — explanation (a) is refuted.** On the exact process it recovers the
analytic optimum almost exactly at the parameters in force (0.241 against 0.245) and sits at or below the bound
at both contrasting points, across a bound range of 0.09 to 0.25. Two independent corroborations fall out of
it: the v2-state row (0.091) reproduces Phase 1's SEP after-state level-free calm R² of **0.086** on a
completely different construction, and the ordering across the three rows tracks the analytic bound's ordering.
**This is a positive result for the whole leakage-audit machinery, not just for Phase 2** — the audit's
level-free R² can be read as an estimate of what a price-only reader can actually extract.

**Therefore the generator's 0.339 is explanation (b): a real channel worth about +0.10 of R².** The exact
process gives 0.241 at the same (σ_V, s_x, h); the full generator gives 0.339 [0.208, 0.434] on the standard
evaluation panel. The difference is what the generator has and the bound's model does not: the scripted events
and their drift, the jumps, the GJR-GARCH innovation and the sentiment feedback. **Phase 6 inherits a
characterisation problem, not a validation problem** — which of those four carries the +0.10, and whether the
gate should be the analytic bound plus a measured allowance for them. Two candidates are already visible in
this phase's own numbers: the level-free R² *all phases* is 0.487 against 0.339 calm, so the event block carries
a large share; and E2.4(c)'s per-model table shows the gap is not an artefact of one estimator.

### 3.8 E2.7 — does the benchmark still discriminate? (post-review)

**Why this had to be settled here.** Phase 2 lowers the resolvable share in flat from 0.73 to 0.13 and hands the
coverage trade-off to D3/D8 — but a trade-off is only a decision if the metric still separates policies. If
|x| ≥ θ on one day in eight, the mandate-conditional oracle and the trivial policies converge and the benchmark
cannot rank agents, which no amount of leakage work or persona design would fix. Design and rule fixed in
`PREREG_PHASE_2_ADDENDUM.md` §4.1 before the run; `tools/l5_report.py` unchanged, 40 training seeds disjoint
from the 50 scored seeds, three personas × four scenarios; `e2_7/l5_phase2_after.csv`,
`e2_7/discrimination.{json,md}`. **No pass/fail — G1 is Phase 6's gate.**

MCR at θ = 0.05, averaged over three personas and the scored seeds; intervals are a 2,000-resample cluster
bootstrap with every policy resampled on the same runs, so the gaps are paired:

| state | scenario | coverage | runs with **no** resolvable step | mandate oracle | best L5 | best trivial | gap oracle→L5 | gap L5→trivial | ordering holds |
|---|---|---|---|---|---|---|---|---|
| **Phase 2** | flat | 0.128 | 6/150 (4 %) | 0.0022 | 0.0727 (price-only) | 0.1017 | 0.0706 [0.0631, 0.0784] | **0.0289 [0.0211, 0.0363]** | yes |
| | crash | 0.422 | 0/150 | 0.0023 | 0.0248 (full) | 0.1004 | 0.0225 [0.0193, 0.0264] | 0.0756 [0.0717, 0.0789] | yes |
| | bull trap | 0.539 | 0/150 | 0.0031 | 0.0376 (full) | 0.1005 | 0.0345 [0.0291, 0.0405] | 0.0630 [0.0569, 0.0683] | yes |
| | sustained bull | 0.031 | 15/150 (10 %) | 0.0012 | 0.0857 (full) | 0.1028 | 0.0844 [0.0749, 0.0943] | **0.0171 [0.0072, 0.0266]** | yes |
| **Phase 1** | flat | 0.743 | 0/150 | 0.0030 | 0.0568 (full) | 0.1002 | 0.0538 [0.0453, 0.0636] | 0.0434 [0.0337, 0.0517] | yes |
| | crash | 0.811 | 0/150 | 0.0026 | 0.0326 (full) | 0.0999 | 0.0300 [0.0263, 0.0339] | 0.0673 [0.0634, 0.0709] | yes |
| | bull trap | 0.821 | 0/150 | 0.0033 | 0.0368 (full) | 0.1013 | 0.0335 [0.0289, 0.0386] | 0.0644 [0.0594, 0.0689] | yes |
| | sustained bull | 0.050 | 9/150 (6 %) | 0.0017 | 0.0709 (level-free) | 0.1027 | 0.0692 [0.0604, 0.0781] | 0.0318 [0.0230, 0.0405] | yes |

**The benchmark still discriminates. The ordering MCR(oracle) < MCR(observables oracle) < MCR(best trivial)
holds in all four scenarios, before and after, with both gaps significantly positive at 95 %.** That is the
shape 16A's G1 is written in, measured on the handed-over state — the coverage collapse does *not* collapse the
metric.

**What it does cost, stated plainly:**

| scenario | coverage | runs with no resolvable step | gap L5→trivial |
|---|---|---|---|
| flat | 0.743 → **0.128** | 0 % → **4 %** | 0.0434 → **0.0289** (−33 %) |
| crash | 0.811 → 0.422 | 0 % → 0 % | 0.0673 → 0.0756 (+12 %) |
| bull trap | 0.821 → 0.539 | 0 % → 0 % | 0.0644 → 0.0630 (−2 %) |
| sustained bull | 0.050 → **0.031** | 6 % → **10 %** | 0.0318 → **0.0171** (−46 %) |

The two event scenarios are unaffected or better; **flat loses a third of its discriminating spread and
sustained bull nearly half**. And a fact worth surfacing on its own: **MCR is undefined on runs with no
resolvable step at all** — 4 % of flat runs and 10 % of sustained-bull runs, against 0 % and 6 % before. Every
policy is undefined on exactly the same runs, so it is a property of the path, not of the policy; those cells
are dropped from the means above and their share is reported rather than hidden. A metric that is undefined on
one run in ten of a scenario is a Phase-7 specification question (how MCR treats a run with nothing to resolve),
and it is raised in §5.

One further detail that corroborates §3.6's leakage finding from a different direction: in **flat** the best L5
variant is now **price-only**, where before it was the full field set. The fitted engine writes the mispricing
into returns rather than into the valuation fields, and the observables oracle finds it there.





## 4. Decisions taken and the parameter file

Nineteen decisions, `DECISION_LOG.md` P2-1 … P2-19. The engine adopted is **`ar1_fit` — AR(1)+GJR-GARCH-t** (P2-7).

**`envs/v2/params/mispricing.json`** (new; loud-ish loader `envs/v2/mispricing_params.py` — absent means the v2
engine and units, present means it governs, malformed raises):

| entry | value in force | label | source | interval / n |
|---|---|---|---|---|
| `engine` | `ar1_fit` | FIT (E2.4's decision, with the rule that produced it) | `e2_4/decision.json` | candidates `ar1` / `fw_v2` / `fw_plus`; n = 417 |
| `price_scale` | **1.0** | **LIT bug fix (E2.1)** — FW 2012 works in natural-log price units | `e2_1/fw_repro.md`; FW eqs (1), (5)–(7), Table 4 | joint MCR 10.0 % [6.6, 14.9] against the published 10.1 %; n = 200 runs |
| `structural` | σ_V 0.01220, sbar 0.00870, h 7.498 d | FIT (E2.3 SMM, 17 moments, block-bootstrap weight matrix) | `e2_3/smm_ar1_full.json` | σ_V [0.01066, 0.01419], sbar [0.00659, 0.01298], h [3.81, 23.61]; 30 refits; n = 417 |
| `applied` | engine, `price_scale`, `half_life`, σ_V → `value.json` | states **which** fitted quantities govern the generator | `e2_3/smm_ar1_full.json`; PLAN §7 | **sbar is recorded and NOT applied** (P2-9) |
| `half_life` | **7.498 d** | FIT (the engine's own persistence, ρ = 2^(−1/h) exactly) | `e2_3/smm_ar1_full.json`; `e2_2/persistence.md` | [3.81, 23.61] d; n = 417 |
| `garch_shape` | α 0.027, γ 0.058, β 0.932, ν 4.86 | FIT (E3.1 medians; held fixed inside the SMM) | `e3_1/summary.md` | n = 417; **not applied to the generator — Phase 3 owns it** (P2-12) |
| `moments` | the 17 names | DESIGN (PREREG §4.1) | `e2_3/data_moments.md` | weight matrix: 500 joint stock × block resamples, blocks 250/750/1250 d, 10 % ridge |
| `estimator_table` | `e2_5/hl_table.md` | DESIGN (E2.5) | `e2_5/hl_table.json` | 200 seeds per cell |

Every entry also carries a `survivor_vs_literature_gap` field naming REG-15's direction for that quantity.

**`envs/v2/params/value.json`**: `sigma_V` **0.006 → 0.01220** [0.01066, 0.01419], label FIT (E2.3), with the
previous value and Phase 1's estimator-C value both recorded (P2-8); `s_x_fit` **0.1286 → 0.02498** with its
derivation (P2-6). Everything else is unchanged.

**The half-life interval is wide and the report does not hide it**: [3.81, 23.61] days over 30 moment resamples.
The point estimate is stable across periods — 13.1 (2000–08), 8.9 (2009–16), 9.2 (2017–24), 7.5 (full), 5.2
(2000–16) — but a single fit identifies it only to within a factor of about three. E2.6 sweeps 7.5 to 500 days
precisely because of that.

**Execution-order rule, paid in full.** Applying σ_V and the engine changes every path, so the state handed over
was re-derived from step 0: `path_hashes_phase2_after.json` (95 configurations), the Section-9 checklist on the
standard checklist panel (200 seeds, `e2_after_checklist.{md,csv}`), and a rewritten freeze manifest
(`tests/v2_freeze_manifest.json`, label "v2.1 Phase 2 freeze (post-review)", 21 files, hash `502abb00…`).
The post-review provenance edits of P2-16 changed the two parameter files' *labels* only, so the manifest was
rewritten and the 95-configuration path hashes were **regenerated and compared**: 0 of 190 hidden columns
changed, which is the evidence that a label edit moved no path.

**The checklist, before and after, on the same panel:** Phase 1's hand-over passed **5 of 20**; Phase 2's passes
**5 of 20**. The count is the same but the set is not — **item 20 (magnitudes) now passes and item 6 (leverage
effect) now fails**:

| item | Phase 1 after | Phase 2 after | why |
|---|---|---|---|
| 20 Magnitudes | fail | **pass** | the calm-day sd band (0.014–0.022) is met once σ_V rises from 0.006 to 0.0122; E1.3's sweep predicted exactly this ("item 20 is 0.0135 at the σ_V in force, 0.0158–0.0195 at σ_V 0.010–0.015") |
| 6 Leverage effect | pass | **fail** | with σ_V trebled, symmetric fundamental shocks make up a larger share of the return variance, diluting the GJR asymmetry that lives in x |

Item 6 is a **volatility** item and Phase 3 owns the GJR parameters (E3.1/E3.4); it is reported here as a
consequence of Phase 2's σ_V, not fixed here. The other eighteen items are unchanged.

**The level-free leakage audit on the handed-over state**, on the standard evaluation panel (SEP: 1,600 paths,
288,000 rows, 119,113 calm rows, no subsampling), on the **local reference machine** — the only environment a
surrogate number may come from (`PHASE_1_REPORT.md` §6.6). Best model per cell, R²(x) with a 500-resample
cluster bootstrap over paths; beside it, Phase 1's after-state on the identical panel and estimators:

| control / field set | Phase 1 after (C) | **Phase 2 after** | direction |
|---|---|---|---|
| level-free, calm | 0.086 [0.043, 0.122] | **0.339 [0.208, 0.434]** | **worse** (+0.25) |
| level-free, all phases | 0.527 [0.506, 0.546] | 0.487 [0.472, 0.501] | slightly better |
| full field set, calm | 0.823 | **0.346 [0.206, 0.446]** | **much better** (−0.48) |
| full field set, all phases | 0.928 | 0.731 [0.719, 0.743] | **better** (−0.20) |
| L2b macro-phase selectivity | +11.7 pp | **+15.4 pp** (78.2 % full vs 62.8 % price-only) | worse; the 10 pp margin still fails |

**The fitted engine trades field leakage for price leakage, and the trade is large in both directions.** A
reader of the *rendered valuation fields* learns far less about x than before (calm R² 0.82 → 0.35, all-phase
0.93 → 0.73); a reader of *returns and ratios alone* learns considerably more (calm 0.09 → 0.34). The mechanism
is not mysterious: a mispricing with a five-to-eight-day half-life and a 3 % amplitude is written into last
week's returns, which the level-free control sees, and is almost invisible to a slowly-updating analyst or EPS
field, which the full set sees. **This is the single most consequential thing Phase 2 hands to Phase 6**, and it
cuts both ways for the benchmark's central claim: the answer key through the *fields* is much weaker, and the
answer key through the *price path* is much stronger.

The calm level-free 0.339 sits above the Appendix-B bound at the parameters in force (0.245) but its interval
[0.208, 0.434] does not lie entirely above it, so under Phase 1's own reading it is not a flagged excess — the
same marginal verdict the 50-seed sweep gave, now on 1,600 paths. Phase 6 owns the gate, the pinned library
versions and the reference distribution; Phase 2 reports the measurement.

The L2b phase-clock selectivity remains a **registered Phase-6 defect** and got worse (+11.7 → +15.4 pp): the
non-price fields still identify the macro phase better than price alone. Its gate is re-derived in Phase 6, as
`known_defects.py` records.


**Tests** (`tests/test_v2_1_phase_2.py`, plus the edits P2-10 and P2-11 describe): `test_fw_units`,
`test_fw_index_params_match_source`, `test_pruna_params_match_source`, `test_mispricing_params_loader`,
`test_persistence_in_force`, `test_engine_named_honestly`, `test_half_life_estimator_table`,
`test_smm_reference_row`, and the strict xfail `test_garch_shape_matches_e3_1` registered to Phase 3.
`test_flat_x_equivalence` is hard again; `test_fundamentalist_share` is removed with a note in its place;
`test_half_life_consistency` is re-pointed.

**The suite on the handed-over state: 121 passed, 1 skipped, 7 xfailed, 0 failed** (24 min 37 s), and
`python -m tools.freeze_manifest --check` reports `manifest OK`. Re-run after the post-review extensions, the
Phase-0/1/2 and statistics files give 20 passed, 3 xfailed. Three tests needed
their evidence base updated because Phase 2 changed the engine, and each change is recorded rather than quietly
made:

| test | what changed | why it is not tuning |
|---|---|---|
| `test_engine_named_honestly`, `test_v2_generator`, `test_docs_numbers` | the engine name is read from `params/mispricing.json` instead of the literal `"fw_fallback_hl150"`; the canonical φ is checked against `fw_fallback_hl150` **by name**, which is the engine it describes | the assertions are strictly stronger — they now say "the metadata reports the code path that ran", which is what the plan's `test_engine_named_honestly` asks for |
| `test_jump_placement_variants` | the "v2 bias" threshold is expressed relative to the other three placements instead of the absolute −0.04 | −0.04 was the stationary offset of a jump drift at a **150-day** half-life; at 7.5 days the same drift settles at −0.005. The invariant (the negative-mean placement biases x down and the others do not) is unchanged |
| `test_v2_L2_selectivity_reported_and_no_spurious_fit` | the shuffled-V bound is decided on the **published 1,600-path audit** (−0.0023) rather than on the 8-seed CI panel (0.102), with the CI panel kept as a range guard | the bound, the statistic and the estimators are identical; only the panel changed, and for the reason `test_v2_L2b_phase_clock_selectivity` already documents — 8 seeds cannot decide a 0.1 margin. DECISION_LOG P2-13 |

The known-defect registry now holds **five** entries, none of them Phase 2's: one added by this phase for
Phase 3 (the GARCH shape), the IV step (Phase 3), the sustained-bull selection (Phase 4), and the two Phase-6
leakage gates.

## 5. Decisions the team must take

1. **The size of the mispricing the panel implies, and what it costs — now with the discriminating power
   measured.** Three independent routes agree that the transitory component of a single stock's log price has a
   **half-life of about 5–13 days and a stationary sd of about 2.1–2.5 %**: estimator A gives h = 4.9 d
   [4.2, 5.6] and s_x = 0.0237 [0.0216, 0.0258]; Phase 1's estimator C, once its s_x is corrected (P2-6), gives
   4.8 d and 0.0250; this phase's SMM gives 7.5 d (8.1 d realised) and 0.023, stable at 13.1 / 8.9 / 9.2 / 5.2 d
   across every window of the panel. The environment in force carried **s_x ≈ 0.175 at a 150-day half-life** —
   seven times the amplitude and twenty times the persistence.

   **The decision now comes with the number it turns on (§3.8).** The benchmark **still discriminates**: the
   G1 ordering MCR(oracle) < MCR(observables oracle) < MCR(best trivial) holds in all four scenarios with both
   gaps significantly positive. What the fitted persistence costs is the *size* of the spread where coverage
   falls — the L5-to-trivial gap goes 0.0434 → 0.0289 in flat (−33 %) and 0.0318 → 0.0171 in sustained bull
   (−46 %), while crash and bull trap are unchanged or better. It also costs **definedness**: MCR is undefined
   on runs with no resolvable step at all, 4 % of flat runs and 10 % of sustained-bull runs against 0 % and 6 %
   before.

   Against that, the fitted persistence **buys** what 16A's G3 asks for: the oracle switches target 2–3 times
   per 200-day run in flat, crash and bull trap (69–77 % of runs with ≥ 2 switches) against a median of 1 and
   0.29–0.48 for the incumbent, and the sweep now shows that holding across 5, 7.5, 10 and 15 days — most of the
   fitted interval (§3.6). **The plan's 16A note of 27 August expected the opposite** and forbade meeting G3 by
   shortening the half-life; the single-stock panel simply is faster than the index-level literature it reasoned
   from, so this is a FIT value that happens to help, not a tuned one.

   The options are D3's (adopt the fitted environment, keep the v2 one, or run both as a factor) and D8's. Two
   things are now on the table that were not: the trade is **spread size and definedness against decision count
   and field leakage**, and it is quantified in both directions; and a middle position exists — the sweep's
   h = 15–30 d rows keep most of the switch counts while recovering coverage to 0.24–0.39 in flat.

2. **How MCR should treat a run with nothing to resolve (Phase 7).** At the fitted coverage the score is
   undefined on 4 % of flat and 10 % of sustained-bull runs, and the L5 tables drop those cells. That is a
   specification question the metric's own phase owns (E7.2/E7.5): whether such a run scores 0, is excluded with
   its count published, or is prevented by the scenario design. It is raised here because Phase 2's engine is
   what made it non-negligible, and because any published MCR average silently depends on the answer.

3. **σ_V's application (D3 = (b), applied), and why the label says *conditional*.** The blank in the execution prompt was empty, so σ_V entered E2.3
   as a free parameter and the fitted value is what `value.json` now carries. The team should note that the SMM's
   σ_V (0.0122 for the adopted engine) is **below** Phase 1's estimator-C value (0.0196) and below estimator A's
   (0.0205): the engine's own structure moves it. The execution-order rule was paid in full (§4).
4. **Ratification of the design corrections** (`PREREG_PHASE_2_ADDENDUM.md` §1–§3, and the three post-review extensions of §4): the simulation-noise
   rule re-scoped to the reported J; the compute-bound reductions on the `train` and sub-period fits; E2.6's seed
   counts. Each was fixed before the run it governs, with disclosure of what had been seen.
5. **The unexplained SABCEMM discrepancy (P2-3).** FW's published equations at their published parameters do not
   reproduce SABCEMM's DCA-HPM row under either units convention, and the one ambiguity in SABCEMM's appendix
   does not account for it. Nothing in Phase 2 depends on it, but the deck cites SABCEMM and should either drop
   the citation or carry the discrepancy.
6. **The GARCH shape mismatch, handed to Phase 3.** E2.3 fitted the engine against E3.1's per-stock
   GJR-GARCH-t shape, as the plan prescribes, while the generator still runs v2's CAL shape. The engine's fitted
   parameters are therefore conditional on a volatility block Phase 3 owns; registered as a strict-xfail known
   defect with Phase 3 as owner (`tests/known_defects.py`).
7. **The bull-trap rejection rate, handed to Phase 4.** At the adopted engine the bull-trap scenario's
   acceptance condition is met on the first attempt only 6 % of the time (rejection rate 0.94, against 0.06 for
   the incumbent), because the condition was calibrated against a mispricing of ±0.23 over 200 days and the
   fitted one is ±0.11. Rejection sampling at that rate selects a sub-population, which is exactly the defect
   review C.5 identified for sustained bull (weakness items 18, 42, already a registered strict xfail owned by
   Phase 4). Phase 2 does not touch the event formulation — Phase 4 owns it — but the team should know that
   Phase 4 now has two scenarios to re-derive, not one, and that the trigger was Phase 2's fitted persistence.
8. **REG-15 triggers.** Every moment this phase fits is survivor-based (set A has no delistings), so the tails
   and the unconditional variance understate the full universe and the fitted innovation scale inherits that
   gap. No parameter was set from a tail statistic alone, but the WRDS re-run (D1 = C) is the remedy the plan
   foresees and the fitting code takes the panel root as a parameter.

## 6. Files written or changed

Nothing committed; everything is in the working tree on `main`. `docs/` and `datasets/` are git-ignored by
design. The complete list, with what each file is, is `PHASE_2_CHANGED_FILES.md`; the summary:

**Documents**: `PREREG_PHASE_2.md` (before any run), `PREREG_PHASE_2_ADDENDUM.md` (§1 the simulation-noise rule
re-scoped, §2 the compute-bound reductions, §3 E2.6's seed counts, §4 the three post-review extensions — each
fixed before the run it governs, with disclosure), `PHASE_2_REPORT.md` (this file), `PHASE_2_CHANGED_FILES.md`; three "[Phase 2 correction]" markers
in `PHASE_1_REPORT.md` and one in `DECISION_LOG.md` P1-15 (the `s_x` correction, P2-6); `DECISION_LOG.md`'s new
Phase-2 section (P2-1 … P2-12); `spec/E1_V2_GENERATOR_SPEC.md` §2 (the units bullet replaced by E2.1's evidence;
the pure-AR(1) half-life figures replaced by E2.5's 200-seed table).

**Generator**: `envs/v2/mispricing_params.py` (new loader), `envs/v2/mispricing.py` (the engine read from the
parameter file, `fitted_params`, the exact AR(1) ρ, `<engine>_hl<d>` sensitivities, the fitted engine's weight
normalisation pinned to the SMM's, the legacy engines untouched), `envs/v2/params/mispricing.json` (new),
`envs/v2/params/value.json` (σ_V applied, `s_x_fit` corrected), `simulation/runner_v2.py` (its `engine` default
now follows `ENGINE_DEFAULT` instead of a hard-coded string — a literal there would have silently run a
different engine from the one the parameter file names).

**Tools**: `tools/phase2/` — `fw_pure.py`, `moments.py`, `engines.py`, `prereg_power.py`, `e2_1_fw_repro.py`,
`e2_3_data.py`, `e2_3_smm.py`, `e2_2_persistence.py`, `e2_4_engine.py`, `e2_4_flat_x.py`, `e2_5_hl_table.py`,
`e2_6_sweep.py`, `e2_7_discrimination.py`, `e2_8_bound_check.py`, `v6_s_x_correction.py`, `apply_e2.py`,
`after_state.py`, `phase2_chain.py`, `phase2_numbers.py`; one corrected note in `tools/verify_v2_findings.py` (the SABCEMM row, P2-1).

**Tests**: `tests/test_v2_1_phase_2.py` (new); `tests/known_defects.py` (two Phase-2 entries cleared, one
Phase-3 entry added); `tests/test_v2_1_stats.py` (`test_fundamentalist_share` removed with a note in its place,
`test_half_life_consistency` re-pointed, the SABCEMM figure corrected); `tests/test_v2_1_phase_1.py`
(`test_flat_x_equivalence` hard again and re-pointed, `test_jump_placement_variants`' magnitude threshold made
relative to the other placements rather than absolute at a different engine's half-life);
`tests/test_v2_1_phase_0.py` (`test_engine_named_honestly` reads the engine from the parameter file and asserts
the legacy engine separately); `tests/v2_freeze_manifest.json` (rewritten, label "v2.1 Phase 2 freeze").

**Results** (`docs/env_v2/generated/v2_1/`): `e2_0/power.json`; `e2_1/fw_repro.{json,md}`;
`e2_2/persistence.{json,md}`, `s_x_correction.json`; `e2_3/data_moments.{json,md}`, `data_boot_*.npy`,
`weight_*.npy`, `reference_row.json`, nine `smm_<engine>_<period>.json`; `e2_4/decision.{json,md}`,
`engine_diagnostics.json`, `flat_x.json`, `kalman_bound_phase2.json`; `e2_5/hl_table.{json,md}`,
`andrews_median_T*.npz`, `hl_at_fitted.json`, `v4_engine_half_life_check.json`; `e2_6/sweep.{json,md}` and
twelve `checklist_*.{csv,md}`; `e2_6_after/audit_after_levelfree.*`; `e2_after_checklist.{md,csv}`;
`path_hashes_phase2_after.json`; `phase2_numbers.json`; `_panels/sep_phase2_after.pkl` (git-ignored,
regenerable).

**Not changed**: `envs/v1/`, `docs/planning/`, `docs/env_v2/v2_1/archive/`, the plan, the alternatives register,
`datasets/`, `evaluation/`, `agent/`, and every legacy generator engine with its stored burn-in states.

## 7. What was not done, and who owns it

- **`fw_v2` and `fw_plus` sub-period fits** (6 cells): not run. The compute reduction of ADDENDUM §2 spent the
  budget on the cells that decide, and the decision is made on `full` and `train`. The `ar1` sub-periods were run.
- **E2.6's levels 5, 10 and 15 d**: **now run** at the 200-seed switch statistics and the 100-seed checklist
  after review (ADDENDUM §4.3), so the sweep covers four points inside the fitted interval. The **level-free
  audits** were not extended to them: they remain the matched-sd arm at the original six levels.
- **The matched-innovation arm's level-free audits**: not run (ADDENDUM §3); the matched-sd arm's were.
- **`sbar`**: fitted and recorded, deliberately not applied — Phase 3 owns it (P2-9).
- **The GARCH shape**: E2.3 fitted against E3.1's; the generator runs v2's. Registered to Phase 3 (P2-12).
- **The Appendix-B gate**: the bound is recomputed, now applies exactly, and E2.8 has shown the surrogate is
  unbiased against it — so what Phase 6 inherits is *characterising* the +0.10 of R² the generator adds over the
  exact process (events, jumps, GARCH, sentiment), not validating the statistic. The gate itself, its panel and
  its pinned library versions remain Phase 6's.
- **Which of the four generator blocks carries that +0.10**: not decomposed. The obvious next step — rerun E2.8
  adding one block at a time — is a Phase-6 experiment, not a Phase-2 one, but it is now a well-posed question
  with a measured target.
- **How MCR treats a run with no resolvable step**: raised, not answered. Phase 7 (E7.2/E7.5) owns the metric's
  specification; Phase 2 reports that the case is 4 % of flat runs and 10 % of sustained-bull runs.
- **Phase 3 is not started.**
