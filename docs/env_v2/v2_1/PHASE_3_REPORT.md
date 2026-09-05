# Phase 3 report (v2.1): volatility — GARCH, jumps, regime variance and implied volatility

Date: 2–4 September 2026. Working tree on `main` at commit `b563e9d` (the v2.1 Phase-2 state) plus this phase's
changes; nothing committed, no branch, no paid API call. Governing documents: `V2_1_IMPROVEMENT_PLAN.md`
Section 7, `V2_1_ALTERNATIVES_REGISTER.md` REG-6 and REG-15, `PREREG_PHASE_3.md` (written before any run) and
`PREREG_PHASE_3_ADDENDUM.md` (three designs found wrong at their first measurement and corrected in
documented steps before the runs they govern, with results under both rules). Compute: the local 8-core
reference machine for everything except E3.4's pure-simulation arms, which ran on a Kaggle kernel after the
cross-machine reference row was proven there (§3.4); **no audit, L5 or surrogate number in this report comes
from another machine**.

**Status: Phase 3 complete (4 September 2026); stopping. Phase 4 not started.** The suite on the handed-over
state: **127 passed, 1 skipped, 5 xfailed, 0 failed** (50 min 37 s + the corrected docs file re-run) — the five
xfails are the three registry entries owned by Phases 4 and 6 and the two permanent v1 baselines; **both
Phase-3 known defects end the phase as hard, passing tests**. `python -m tools.freeze_manifest --check` reports
`manifest OK` (label "v2.1 Phase 3 freeze", 23 files). Compute: everything reported here comes from the local
reference machine except E3.4's pure-simulation arms, which ran on a Kaggle kernel **after** the cross-machine
reference row was proven to 6.4·10⁻¹⁶ (the first exercise of Phase 2's guard); every audit, L5 and surrogate
number is local-only.

**The findings the team has to weigh** (§5). The engine, re-identified under the fitted volatility block, is
**σ_V 0.01457, half-life 22.4 d [18.7, 32.6], sd(x) 0.068** — and on that state the benchmark discriminates
**better on both axes** than Phase 2's: flat coverage 0.128 → 0.378 with MCR defined on every flat run again,
the flat policy spread back at Phase 1's level (0.0455), crash and bull-trap improved, sustained bull still
structurally starved (coverage 0.044, 10 % undefined — REG-7/D14, Phase 4's). On leakage, measured on a
consistent (calm-trained) surrogate, the **calm level-free channel narrowed modestly rather than closing**
(R²(x) 0.421 → 0.349, sign accuracy 0.892 → 0.814 — §3.11's withdrawal of this report's first reading), while
the **event-phase channel grew** (all-phases full-field 0.731 → 0.843 — Phase 4/6's); L2b improves to +12.7 pp
(still over the 10 pp margin, Phase 6's gate), and the rendered IV adds exactly nothing to scenario
classification beyond the price path. **A level double-count is confirmed and handed on** (§3.11): the deployed
generator's unconditional daily return sd is 0.0284, **+30 %** above the 0.0218 the identity targets, because
the identity pins the generator's *calm* to the panel's *all-day* average (which is 1.28× the panel's own calm)
and the event multipliers then stack on top. Five Phase-4 hand-offs carry measured numbers: the schedule
template's rise time, the stale hazard (topped share 8 %), the ex-post blow-off label, the drift-dominated
post-top, and that level anchoring.

**What changed in the environment.** The volatility block is now **fully fitted**
(`envs/v2/params/volatility.json`, loud loader): the GJR shape is E3.1's per-stock medians (α 0.027, γ 0.058,
β 0.932) with a **jump-decomposed diffusive tail ν 6.65**; the unconditional scale is set by an **exact
variance-accounting identity** to the panel's per-stock median return sd (sbar 0.0151; v2's CAL 0.017
superseded, E2.3's 0.0087 named for the engine-conditional compromise it was); the jumps are re-fitted to
**rare and very large** (0.00058/day at σ 0.230 against v2's CAL 0.010/0.03 — fourteen times the rate at a
seventh the size, with the size scale honestly labelled weakly identified); the phase multipliers are FIT from
1,592 drawdown and 3,125 run-up episodes and calibrated **closed-loop** so the generator's realised ratios
match the panel's (panic ×7.45 total); the whole-variance mechanism survives REG-6's three-way test as its
documented-shortfall consequence; and the IV field is rebuilt as a **past-only filter of observed returns**
with a constant FIT premium and AR(1) FIT noise — the reviews' worst leak (the one-day panic step, z ≈ 7) is
**gone** (z = 0.12, hard-tested at a derived tolerance; onset ΔAUC −0.107 against a +0.032 null). The §9 refit
then re-identified the engine under the fitted block: **σ_V 0.01457, half-life 22.4 d [18.7, 32.6]**, sd(x)
0.068 — Phase 2's 7.5 d lies outside the new interval while the new 22.4 d lies inside Phase 2's own
[3.81, 23.61] (§3.7 states it symmetrically and splits the move into ≈ 9.5 d of block effect and ≈ 5.4 d of
identity constraint, at a cost of ΔJ ≈ 26), and the bull-trap rejection rate falls 0.94 → 0.13.
Both Phase-3 known defects (P2-12's GARCH shape, the IV step) end the phase as **hard, passing tests**; the
state was re-frozen, re-hashed and re-audited.

---

## 1. Literature review and the citation table

Every statistic below is carried at the status the plan's own verification pass records (PLAN §7.1, "[changed:
LOG §4.2]", each read with the correction where one was needed); none is quoted from memory, none is used as a
tolerance, and no statistic marked "(to verify)" appears in a parameter file, test tolerance or slide.
**Hamilton & Susmel (1994) is not retrievable and is not quoted anywhere in this phase** (the plan's explicit
flag). Bakshi & Kapadia (2003) is index-only and is not used for any single-stock claim.

| Statistic / statement | Where used | Status | Source |
|---|---|---|---|
| α 0.077, β 0.905 on a 50/30/20 Nasdaq/Dow/bond **portfolio**, daily 1990–2000 | §3's anchor; the report states why a portfolio fit is not a per-stock anchor (aggregation raises α, lowers β) | read (plan pass) | Engle 2001, JEP |
| leverage models beat GARCH(1,1) on IBM daily | motivates the GJR form (inherited from v2) | read (plan pass) | Hansen & Lunde 2005, JAE |
| GJR 1993 is **monthly** — not a daily γ range | provenance of the functional form only | read (plan pass) | Glosten, Jagannathan & Runkle 1993 |
| jump rejection at β\* = 4.6 at 1 %, **intraday** | quoted beside E3.2's daily threshold, not used as one | read (plan pass) | Lee & Mykland 2008, RFS |
| jump variation 14.4 % of realised variance, 27.9 % of days — **index futures** 1990–2002 | printed beside E3.2's panel numbers, never a tolerance | read (plan pass) | Andersen, Bollerslev & Diebold 2007, REStat |
| monthly S&P σ 4.89 % vs 2.45 % (variance ratio ≈ 4.0); P 0.977, Q 0.951 | sanity anchor beside E3.3's multipliers | read (plan pass) | Ang & Timmermann 2012 |
| 7.04 % vs 3.77 % monthly | same | read (plan pass) | Ang & Bekaert 2002 |
| recession/expansion volatility +76 % (1859–1986) to +227 % (1927–86), index, monthly | same | read (plan pass) | Schwert 1989, JF |
| 40 run-ups ≥ 100 %, 21 crashed; volatility rises in run-ups that crash (industry, monthly) | E3.3's run-up family; the direction check for m_mania | read (plan pass) | Greenwood, Shleifer & You 2019, JFE |
| individual-stock log VRPs negative for 21 of 35 names, mean VRPs mostly insignificant | beside E3.5's fitted premium | read (plan pass) | Carr & Wu 2009, RFS |
| the sort is on log(RV/IV) | beside E3.5 | read (plan pass) | Goyal & Saretto 2009, JFE |
| log RV on log IV slope 0.76, R² 39 %, S&P 100 **monthly** | beside E3.5's IV–RV relation | read (plan pass) | Christensen & Prabhala 1998, JFE |
| Hamilton & Susmel 1994 variance factors | **not quoted** | not retrievable (plan flag) | — |

### 1.1 Inherited numbers verified before use (PREREG §1)

| # | Claim | Result |
|---|---|---|
| V1 | E3.1's published set-A full-sample medians and CIs equal a recomputation from `garch_fits.csv` (medians + 1,000-resample stock bootstrap) | **confirmed** — all six parameters, medians exact, CI endpoints within 5·10⁻⁴ (`e3_1/confirm.json`) |
| V2 | E1.4's q = 0.4345, window share 0.1452, n = 7,492 / 1,670,790, re-derived from `panel_residuals_split.parquet` | **confirmed**, exactly |
| V3 | `mispricing.json` structural (σ_V 0.012204, sbar 0.008699, h 7.498) = `e2_3/smm_ar1_full.json` = `value.json` σ_V | **confirmed**, exactly |
| V4 | the §3.4 identity reproduces the target unconditional sd in a long simulation at the adopted block | **confirmed**: 0.021788 measured vs 0.021793 target (50 × 20,000 d, 0.04 SE; `e3_4/v4_uncond_check.json`) |
| V5 | the AR(1)-family FW weight is frozen at w ≡ 1.4225 and the handed-over IV level carries it | **confirmed**: w constant at 1.4225 on a generated path (= (0.5·0.758 + 0.5·2.087)/1); the handed-over median flat-path IV is **51.3** against 39.6 if w were 1 — a constant ×1.19 √-scale factor left over from the FW weight plumbing when Phase 2 adopted the AR(1) engine. Constant ⇒ no leak; it dies with E3.5's construction, and it explains why the handed-over IV level sits far above checklist item 13's calm band |
| V6 | the Appendix-B bound recomputed at the refit values | **confirmed** (§3.10): the bound at (σ_V\* 0.01457, s_x\* 0.068, h\* 22.4) is **0.163** window-average; the exact-process surrogate measures 0.145 [0.108, 0.176] — at/below it, so E2.8's unbiasedness verdict carries to the new block |
| V7 | E2.5's estimator-table rows at the refit h\* | **run** (h\* = 22.4 leaves 7.5 ± 1): naive T = 200 median 16.0 d [IQR 10.8, 23.0], median-unbiased 27.9; T = 5,000 21.9 / 22.4 (`e2_5/hl_at_h22.json`) |

## 2. Pre-registration, the team decisions applied, and the three addendum corrections

`PREREG_PHASE_3.md` was written before any run: seeds (all fresh, 200000+ and 780001+), the panel (set A,
unchanged), every window definition, estimator, model family, decision rule, the engine-refit decision
(§9: one constrained re-launch of Phase 2's SMM, decided **before** any fit), and the decidability table
(PA1–PA7) with the consequence of each check's failure. **The §5.1 blank of the Phase-2 report is empty in the
execution prompt, so Phase 3 proceeds on the environment as handed over** (`ar1_fit`, σ_V 0.01220, h 7.50 d,
sbar 0.017 CAL) and does not re-tune the engine to change coverage; §7 lists what would differ under the
alternative. D1 = C, D13 = mechanism C, D16 = full programme, all unchanged.

**Three pre-registered designs were found wrong at their first measurement and corrected in documented
steps before the runs they govern** (`PREREG_PHASE_3_ADDENDUM.md`, each with disclosure of exactly what had
been seen; the third — the E3.2 adoption after both registered paths failed measurably — is described with its
evidence in §3.2):

1. **The run-up "pre-event calm" window measures a post-crash trough** (§1): the 504-day argmin lands on 2003 /
   2009 / 2020 bottoms, where realised variance is at its maximum — measured, the pre-event window sits at
   **2.74× [2.57, 2.89]** the stock's unconditional level for run-ups (and 1.01 [0.98, 1.06] for drawdowns,
   which is why the drawdown windows did not need the fix). Every run-up multiplier came out below 1 against a
   reference that is not calm. Correction: the multiplier reference becomes the stock's **unconditional level**
   (median rolling 21-day RV, full sample), the semantically consistent denominator for a generator whose calm
   phase is pinned to the panel's unconditional sd (§3.4). Both variants are published side by side.
2. **The pooled ≥ 30 % drawdown population is dominated by slow multi-year declines** (§2): pooled rise time
   118 d [107, 131] against the plan's index examples of ≈ 10–30 d, and against a scripted crash that completes
   inside 110 trading days by construction — under the registered rule the rise criterion would be decided by
   Phase 4's schedule template, not by the variance mechanism REG-6 asks about. Correction: the pooled rule
   stays the **registered primary** and is reported; a **fast-crash subpopulation** (peak→trough ≤ 126 trading
   days, the threshold chosen from the generator's template length before the subpopulation's statistics were
   computed) is the registered secondary whose CIs govern the adoption; the mechanism decision is reported
   under both.

## 3. Experiments and results

### 3.1 E3.1 — confirmed, documented, and the three volatility scales named

**The fits are confirmed, not redone** (V1): recomputing the set-A full-sample medians and their 1,000-resample
stock-bootstrap CIs from `garch_fits.csv` reproduces `summary.json` exactly. In force from this phase (FIT):
**α 0.027 [0.025, 0.030], γ 0.058 [0.055, 0.061], β 0.932 [0.928, 0.935]** (persistence 0.991 [0.991, 0.992]);
ν is adopted jointly with the jumps (§3.2). The **sub-period story** is heterogeneity the single number hides:
persistence runs 0.946 (2013–19) to 0.994 (2000–07), ν 4.56–6.21, unconditional sd 0.0146 (2013–19) to 0.0242
(2008–12) — described, with no sub-period difference called significant (the stock bootstrap does not model the
common time dimension). **The survivor gap** (REG-15): set B's shorter, partly delisted names are
fatter-tailed (ν 4.33 [4.08, 4.67] vs 4.86) and more volatile (0.0243 [0.0222, 0.0263] vs 0.0218), so every
set-A value understates the full universe in the tail direction. **Engle 2001's α 0.077 / β 0.905 is a
portfolio-level fit and is not a per-stock anchor**: aggregation to a portfolio raises α and lowers β relative
to per-stock medians (the plan's sanity range, persistence 0.95–0.99 and ν 4–8, contains every set-A
full-sample median). **Shape sensitivity sets** (for Phases 6/9): built on quantiles of (α, γ, ν, persistence)
with β derived — P25 = (0.019, 0.043, 0.946, ν 4.29, pers 0.986), P75 = (0.042, 0.076, 0.916, ν 5.74,
pers 0.996) — because the raw per-parameter P75s would give persistence 1.028, a nonstationary artefact of
marginal quantiles (`e3_1/confirm.json`).

**The three "volatility scale" numbers are three different quantities, and the reconciliation is now explicit**
(PREREG §3.4): **0.0218** [0.0210, 0.0225] is the panel's per-stock median unconditional daily sd of the
**total return**; **0.00870** [0.00659, 0.01298] is E2.3's fitted **x-innovation scale**, conditional on an
engine and a 17-moment objective the model as a whole fails (its residual table misses the volatility block by
−3.5 bootstrap sd on vMean — the SMM trades volatility level against tail and ACF moments, so its sbar is not a
measurement of the panel's volatility); **0.017** is v2's CAL calm x-innovation sd. Adopted: the generator's
free-running unconditional daily return sd is **set equal to 0.0218 by the exact variance-accounting identity**
sbar² = (s_A² − σ_V²)(1 + ρ)/2 − λσ_J², every input FIT, imposed as a constraint inside the §3.7 refit so the
final triple satisfies it exactly. Both registered alternatives are reported as labelled alternatives with
their consequences: the SMM's 0.0087 in §3.7's unconstrained sensitivity, and **the calm-window mapping in
§3.11c** — which this report's first version claimed to report and did not, and which turns out to carry the
level finding of the phase (the panel's own calm is 0.0170, so this identity's full-sample anchor runs the
deployed generator +30 % hot).

### 3.2 E3.2 — jumps: what the tail actually supports

**Detection** (`e3_2/detection.{json,md}`; set-A full-sample residuals 2000–2024, n = 2,622,096 stock-days over
417 stocks, 1,000-resample stock bootstrap). The confound the design was built around is real: at |z| > 4 the
observed share is **0.00440**/day while each stock's own fitted t(ν̂) already predicts **0.00366** — the raw
exceedance count is *not* a jump rate. The excess over the t-tail is **negative at moderate thresholds**
(−0.00148 at 2.5: the QML-fitted t is *fatter* than the data in the middle tail, because its ν was dragged down
by the extreme days) and **positive and growing from 3.5 up** — +0.00074 [+0.00066, +0.00082] at 4, and at
|z| > 6 the observed share is nearly twice the t-tail's (0.00120 vs 0.00065). That crossing pattern is the
signature of a rare, large jump component on top of a *thinner* diffusive tail, and it is what the mixture fit
resolves. The announcement clustering survives at full strength (share at 4: 0.0134 in windows vs 0.0030
outside, 2009–24), and exceedance-day returns average −1.9 % with sd 12.6 % and a 57.3 % negative share
(n = 11,530) — the mean-zero placement's known simplification, restated with the E[x] guard. ABD 2007's
14.4 % / 27.9 % are index-futures anchors printed beside, not tolerances.

**The mixture fit, the recovery gate, and an adoption both registered paths failed to deliver**
(`e3_2/fit.json`, `recovery.json`, `fit_fallback.json`, `adoption.json`; ADDENDUM §3 — the decision record,
with everything that had been seen disclosed). The registered instrument — z = standardised t(ν) plus a
window-weighted Bernoulli–normal jump, fitted on nine pooled moments — returns an **interior, tightly
bracketed optimum** (ν 6.65 [6.48, 6.83], λ 0.00058 [0.00046, 0.00072], σ_J 0.230 [0.223, 0.241]) at
**J = 790**: the model as a whole is decisively rejected. Two structural reasons, both documented: the pooled
exceedance curve is bent by cross-sectional ν heterogeneity (thin middle, fat extreme — no single-ν curve can
follow it), and the announcement-window elevation (0.0134 vs 0.0030 at |z| > 4) exceeds what a
total-rate-preserving split can deliver under the curve constraint (residual −20 bootstrap sd on the in-window
moment). A hand grid confirmed every interior alternative fits worse — the optimum is real, the model class is
wrong.

**The recovery grid then rated the estimator itself**: on panels where the model IS the DGP (100 stocks ×
6,289 d, QML refits end to end, 6 cells × 5 replicates, 7,141 s), **ν recovers to ±2.4 % but λ only to ±59 %
and σ_J to ±28 %** — not usable under the registered 0.20 rule — with the λ = 0 null cell clean (5/5 CIs
include zero, though the *point* estimate can spuriously reach 0.009, which is why no claim rests on a point).
**The registered fallback (ν pinned at 4.86) then produced a degenerate corner** — λ → 3·10⁻¹⁴, J = 1455 —
because the QML *total* tail over-explains the middle of the curve (+29 sd at 2.5) and the optimiser deletes
the jumps entirely, contradicting the robustly positive extreme-tail excess. Mechanically adopting it would
have written "no jumps" into the generator because a mis-pinned nuisance parameter absorbed them.

**Adopted (ADDENDUM §3): the primary fit's own triple with recovery-informed widened intervals** —

| parameter | adopted | interval | what supports it |
|---|---|---|---|
| ν (diffusive, net of jumps) | **6.650** | [6.48, 6.83] | recovery-certified ±2.4 %; E3.1's QML median 4.86 [4.73, 5.02] is the **total** tail, recorded beside; heterogeneity direction: the typical stock is if anything thinner-tailed than the pooled 6.65 |
| λ (jumps/day) | **0.000583** | [0.00046, 0.00082] (∪ of refit CI and the excess-rate CI) | three reads agree on the rate: mixture 0.00058, excess-rate 0.00074 [0.00066, 0.00082], size-arithmetic 0.00074 — ≈ **0.15/year**; estimator-class accuracy ±59 % quoted |
| σ_J (size sd, log units) | **0.230** | [0.086, 0.241] (∪ of refit CI and the moment-arithmetic 0.086) | **weakly identified** (factor ≈ 2.7 across estimators; recovery ±28 %); the robust joint statement is *rare and very large* |

v2's CAL (0.010/day at σ 0.03 — fourteen times the rate at a seventh the size) is superseded: the panel's
excess days are not frequent 3 % moves, they are ≈ one-in-seven-years 20 %-scale single-name blowups.
`p_ann`/`lam_res` re-derived mechanically from (λ, q = 0.4345 kept). The identification problem —
separating diffusive tails from jumps at the single-name daily level needs the delisted tail and
announcement-timestamped data — is flagged for the WRDS re-run (D1 = C) in §5.

### 3.3 E3.3 — the multipliers, and two definitions the data corrected

Set A, 2000–2024, the shared estimator (`tools/phase3/episodes.py`), medians over episodes with 1,000-resample
stock-bootstrap CIs. **1,789 qualifying drawdowns** (depth ≤ −30 %; median −45 % [−46, −44]) over 417 stocks;
**3,202 run-ups** (≥ 100 % in 504 d) over 398 stocks, of which **3,125 over 394** carry a usable calm reference and enter the multipliers; the five market-wide windows on all 417.

**The addendum's two corrections, with the evidence.** The registered run-up "pre-event calm" window (120 d
ending at the 504-day argmin) sits at **2.74× [2.57, 2.89]** the stock's unconditional level — it is the tail
of the crash the run-up started from, not calm — while the drawdown pre-peak window sits at 1.01 [0.98, 1.06],
i.e. exactly the unconditional level. The reference was corrected to the per-stock unconditional level
(ADDENDUM §1) and both variants are published (`e3_3/episodes.md`). And the pooled ≥ −30 % population's rise
time (118 d [107, 131], IQR 39–316) mixes sharp crashes with multi-year declines; the fast-crash subpopulation
(span ≤ 126 d; **642 episodes / 313 stocks**) gives **rise 30 d [29, 35]** and **decay 9 d [9, 10]** — the
population the scripted crash actually models, registered as the adoption-governing secondary before its
statistics were computed (ADDENDUM §2).

**Multipliers in force (FIT, unconditional reference; the registered pre-event-window ratios beside):**

| phase | m (adopted) [95 % CI] | m (as first registered) | n episodes / stocks |
|---|---|---|---|
| deterioration | **1.37** [1.31, 1.44] | 1.16 [1.13, 1.22] | 1,592 / 412 |
| panic | **7.45** [6.86, 8.13] | 5.43 [4.95, 5.89] | 1,592 / 412 |
| stabilisation | **3.11** [2.96, 3.34] | 2.39 [2.24, 2.54] | 1,571 / 412 |
| mania | **1.18** [1.12, 1.21] | 0.46 [0.44, 0.48] | 3,125 / 394 |
| blow-off | **1.65** [1.58, 1.71] | 0.70 [0.66, 0.73] | 3,125 / 394 |
| post-top | **1.16** [1.13, 1.20] | 0.42 [0.40, 0.45] | 3,122 / 394 |

These are **total-return** variance ratios; the x-innovation multipliers the generator runs are derived by the
closed-loop calibration of §3.4. Sustained-bull stays 1.0 (DESIGN, review R1-D5 — a volatility reduction would
be a scenario clock). Beside them: Ang & Timmermann's ≈ 4.0 monthly index variance ratio and Schwert's
+76…+227 % bracket the panic/stabilisation numbers from below, as monthly index statistics should; GSY's
direction (volatility rises in run-ups) is what the corrected mania/blow-off ratios now show. The market-wide
windows land where the single-stock episodes say they should: 2008Q4 **4.58** [4.41, 4.76], 2011Q3 3.52,
2018Q4 2.26, 2020Q1 **9.20** [8.35, 9.97] (peak-21-day ratio 24.7), 2022H1 1.95 (n = 417 each). Decay
half-life 11 d [11, 12] against the unconditional half-way level (11 [10, 11] under the registered reference;
censoring 0.1 %); stress spell 64 d [56, 72]; RV21-peak/calm 8.25 [7.64, 8.94]. Survivorship: every depth and
multiplier is survivor-understated (REG-15; the delisted tail is 4.7 % recoverable), stated on the file.

### 3.4 E3.4 — the multipliers calibrated closed-loop, and REG-6's rule answered by its own fallback

**Compute provenance.** The calibration and the three mechanism arms are pure generator simulation and ran on
the Kaggle kernel `fp-p3-e34` (4 vCPU) — permitted by the offload rule **after** the cross-machine reference
row was proven on that kernel for the first time in the programme: `fp-p3-refrow` reproduces the committed
51-moment reference vector to a worst relative difference of **6.4 × 10⁻¹⁶** under different library versions
(numpy 2.0.2/scipy 1.16.3 vs the local 2.4.6/1.18.0; `e3_0/power.json`). Every audit/surrogate number in this
phase still comes from the local reference machine only.

**The closed-loop calibration** (PREREG §5.3; 3 iterations at 60 seeds, verification at 200): the x-innovation
multipliers whose generator-REALISED total-return ratios match E3.3's FIT medians. Four phases calibrate
cleanly — realised **deterioration 1.34, panic 7.54, stabilisation 3.12, mania 1.19**, each inside its target
CI (targets 1.37 / 7.45 / 3.11 / 1.18) — at in-force multipliers m_x = 1.35 / **16.17** / 5.63 / 1.35. The
panic value is worth a sentence: reproducing the panel's ×7.45 total-variance elevation takes ×16 on the
x-innovation, because σ_V (unscaled by phase, by design) dilutes the total — the first-order mapping of
PREREG 5.3 said ×10.4 and the closed loop found the GARCH's own feedback needs the rest.

**Two shortfalls the loop exposed, both structural and both documented** (`volatility.json`'s mechanism entry):
(i) **the blow-off multiplier has always been dead code** — the label is assigned *ex post*
(`events.relabel_blowoff`), so no blow-off value ever reaches the GARCH driver; v2's OMEGA_MULT 2.0 was equally
inert, which this calibration surfaced when its blow-off knob diverged 2.2 → 9.3 with the realised ratio pinned
at ≈ 1.1. Recorded at mania's value; the gap to the empirical 1.65 [1.58, 1.71] belongs to Phase 4, which owns
the event/relabel machinery. (ii) **post-top is drift-dominated**: the scripted reversal leg floors the
realised ratio at ≈ 1.59 (n = 20 bull-trap paths that reach a post-top phase, `e3_4/calibration.json`) against the target 1.16 [1.13, 1.20] whatever the innovation multiplier (driven to
0.35); the post-top drift shape is Phase 4's E4.8.

**The mechanism decision** (REG-6's rule, both mechanisms' populations, 200 crash seeds per arm, the shared
estimator):

| arm | rise (d) | decay (d) | decay censored | fast-crash CI rise [29, 35] / decay [9, 10] | pooled CI rise [107, 131] / decay [10, 11] |
|---|---|---|---|---|---|
| **A whole-variance** | 75.5 [66, 85] | 13 [12, 14] | 5 % | out / out | out / out |
| B ω + FIT ramp (20 d) | 103 [97, 109] | 11 [9.5, 12] | **35 %** | out / out | **out by 4 d** / in |
| C two-regime switching (v 16.2, p_exit 1/64) | 80 [74, 88] | 14 [13, 15] | 13 % | out / out | out / out |

**No mechanism lands the rise time inside either CI, and the reason is structural**: the generator's onset
(first −10 %) falls inside a scripted deterioration whose remaining length plus the panic's RV21 build-up is
50–90 days by the *schedule template*, while the panel's fast crashes complete onset→RV-peak in 30 [29, 35]
days. Even the instant-multiplier mechanism cannot rise faster than the schedule lets the price fall. **The
rise criterion is decided by Phase 4's event template, not by the variance mechanism** — the finding ADDENDUM
§2 anticipated for the pooled population turns out to hold for the fast-crash one too. Under REG-6's own
consequence, **A (whole-variance scaling) stays, as the documented shortfall**, with all three arms published
(B's near-miss on the pooled rise costs it a 35 % decay-censoring rate — the ω route holds variance up too
long; C rises no faster and decays slower). A3 is thereby revisited *with evidence*: the incumbent mechanism
survives not by default but because the two alternatives measurably do worse on the decay side while none can
fix a rise time the schedule owns. Handed to Phase 4 with numbers.

### 3.5 E3.5 (panel side) — the premium is a constant, and the noise is the field

The five CBOE single-stock VIX histories against the same past-only GJR filter the generator runs (shape =
E3.1 medians; per-name ω from the sample unconditional variance; 17,570 pooled days, 2011-01-07…2024-12-31;
`e3_5/premium.{json,md}`). Leave-one-name-out CV over the registered family: M0 (constant) 0.04899 ± 0.00862,
M1 (+ b·log ℓ) 0.04862, M2 (+ c·(log ℓ)²) 0.04838 — **M0 is adopted by the 1-SE rule**: the level-dependent
premium does not transfer across names (per-name slopes −0.096 to +0.041, sign-unstable), which is Carr & Wu's
single-stock finding in miniature. **log(1 + π) = −0.0224** — a premium of ≈ −2 %, i.e. the five names' IV is,
on median, almost exactly the filter's forecast. What the field carries instead is **noise**: the residual is a
strong AR(1) — ρ 0.926 (range 0.923–0.931 across names, remarkably tight), innovation sd 0.083 (0.058–0.098),
stationary sd ≈ 0.22 — the persistent wedge between a name's IV and any filter of its returns. Adopted:
π constant, ε AR(1) (ρ 0.926, sd_innov 0.083), drawn from the new day-indexed `iv` stream. The pooled minimum
IV is 5.13 (AMZN, 2024) — the anchor the generator's minimum is reported against now that the CAL floor of 12
is removed. Mega-cap caveat stated on every quote (REG-15 / plan §3).

**Leakage consequence, stated in advance of the audit:** with a constant premium, the only phase information in
the rendered IV is the filter's response to observed returns — the construction is leak-free *by design*, and
§3.6's audit measures it (ΔAUC against the same filter's forecast, permutation null).

### 3.6 E3.5 (generator side) — the step is gone, and the audits prove it against the right yardstick

The construction in force (`observables.iv_block_v21`, wired behind `volatility.json`; the v2 `iv_block`
retrievable via `iv_mode="v2"`): IV_t = √(252·fc_t)·(1+π)·e^(ε_t), fc from the past-only GJR filter on
observed returns (ω anchored at the identity's unconditional variance), π the constant −0.0224, ε the AR(1)
noise from the new day-indexed `iv` stream. The stress trigger, the whole-path quantile (weakness 25's
look-ahead), the σ_V add-on, the w² factor (which V5 showed was silently inflating the AR(1)-era IV level
×1.19) and the CAL floor are all gone.

**The audits, on 200 crash seeds** (`e3_5/audit.{json,md}`; seeds IVA 220000+):

- **The one-day step at panic onset is gone**: mean z at deterioration→panic = **+0.12** against the v2
  construction's ≈ 7 (the number that made this weakness 46) — and against the same filter's own forecast z of
  +0.14. At panic→stabilisation −0.07, at calm→deterioration −0.06. The rendered IV moves *less* at hidden
  transitions than the leak-free reference does, because its FIT noise (stationary sd ≈ 0.22) dominates its
  day-to-day movement exactly as the five CBOE names' IV does.
- **The derived tolerances** (PREREG 7.2(3)): T_z = P95 of the reference z per transition = **2.70 / 2.28 /
  1.88**, written into `volatility.json` with provenance; `test_iv_continuity` is **hard** on the SIV30 fixture
  and passes (items 46 and 25 closed; the registry entries removed). PA6: the 30-seed test statistic's SE is
  far inside T_z (the 200-seed z_IV means are 0.07–0.12 against tolerances ≈ 2).
- **The onset-detection audit in REG-6's corrected form**: pooled day-level AUC of |Δlog IV| for the 5 days
  after panic onset = **0.576** against the same filter's forecast **0.683**; ΔAUC = **−0.107** against a
  permutation-null P95 of +0.032 (500 circular shifts) — **pass, decisively**. PA5's vacuity check holds
  (AUC_ref 0.683 ≫ 0.5: there is legitimate return-borne signal, and the premium's rise through returns is not
  counted as a leak). The rendered IV is now a *noisy, slightly lagged* reader of realised conditions — which
  is what an implied-volatility field of a single name empirically is.
- `test_iv_no_lookahead` (20 seeds, three cut points, plus the wiring assertion that the environment's rendered
  IV equals the construction on its own returns with its own stream): **bit-identical prefixes — pass**.

**Consequence for L2b, measured at hand-over (§4)**: IV was the reviews' clearest phase marker; it now carries
strictly less phase information than the price path implies on its own.

### 3.7 The section-9 engine refit — the loop P2-12 registered, closed

**Design, decided and pre-registered before any fit** (PREREG §9): one re-launch of Phase 2's SMM for the
adopted engine only, on the Phase-3 volatility block — E3.1's shape and E3.2's jumps in the simulator (opt-in
extensions of `tools/phase2/engines.py`; the Phase-2 reference row is bit-identical and its test stayed green),
with **sbar eliminated as a free parameter by the §3.4 identity**, so free = (σ_V, h) at df = 15. Everything
else is Phase 2's registered design unchanged (17 moments, the stored weight matrix, 200 CRN paths × 5,000 d,
K = 20 reported replicates, DE + polish, 30 bootstrap refits, both acceptance criteria; fresh seed blocks
SM3/SB3/MC3). The engine's identity (`ar1_fit`, E2.4's decision) was not re-opened.

**The unconstrained sensitivity** — Phase 2's exact 3-free parameterisation re-run under the new block —
lands at **σ_V 0.01176, sbar 0.00991, h 16.96 d, J 93.1** (rejected, as every fit of this model class has
been). Two things it shows: the SMM, left free, *still* buys volatility-level misfit to spend on tails and ACF
(sbar 0.0099 against the identity's ≈ 0.0167 at that σ_V — the same compromise P3-2 names), and **the fitted
persistence is materially conditional on the volatility block** — h moves from Phase 2's 7.50 d [3.81, 23.61]
to ≈ 17 d when the shape and jumps change, exactly the conditionality P2-12/P2-16 warned every consumer about.

**The constrained adoption cell** (`e2_3/smm_ar1c_full_p3.json`; DE 414 evaluations from the ≥ 20 named starts,
NM polish, K = 20 CRN replicates, max simulation SE 0.082 bootstrap sd, C = 200 FW replicates, 30 refits;
4,605 s):

| | Phase 2 (old shape, sbar free) | Phase 3 unconstrained sensitivity | **Phase 3 constrained (adopted)** |
|---|---|---|---|
| σ_V | 0.01220 [0.01066, 0.01419] | 0.01176 | **0.01457 [0.01275, 0.01527]** |
| h | 7.50 d [3.81, 23.61] | 16.96 d | **22.38 d [18.75, 32.64]** |
| sbar | 0.00870 (free; not applied) | 0.00991 (free) | **0.01509 by the identity** (applied) |
| J (df) | 80.4 (14) | 93.1 (14) | 119.3 (15) |
| accepted? | no (χ², FW p 0.000) | no | **no** (χ² crit 25.0; FW p 0.000) |

**What the constraint bought, visible in the residuals**: the volatility level is now matched (vMean residual
**+0.8** bootstrap sd against Phase 2's −3.5) — the identity does exactly what P3-2 designed it to do — and the
rejection now rests where the model class genuinely fails: the long-memory clustering moments (vAC1…vAC100 at
−5.8…−2.1) and the bounce (rAC1 +4.3). **No engine of this class has ever been accepted on this panel and this
one is not either**; the parameters are, as in Phase 2, the best available under the stated class, and the
label says what they are conditional on.

**The loop's yield, and the two effects it is made of.** The engine's persistence moves from 7.5 d to
**22.4 d [18.7, 32.6]**. The phase's own two cells separate the causes and both belong in the headline: the
**block** carries it from 7.50 to 16.96 d (**≈ 9.5 d**, the unconstrained fit under the new shape and jumps)
and the **identity constraint** carries the rest, 16.96 → 22.38 (**≈ 5.4 d**). The constraint is not free:
J goes 93.06 (df 14) → 119.28 (df 15), **ΔJ ≈ 26 for one restriction**. The model is rejected either way so
this is not a valid likelihood-ratio test, but the magnitude is the honest measure of the tension between the
panel's volatility *level* and its persistence structure inside this model class, and the residual table says
exactly what was traded: **vMean −3.06 → +0.83** (the level, bought), against the **long-horizon variance
ratios** (VR120 −2.77 → −3.16, VR250 −2.60 → −3.38, VR500 −1.48 → −2.18) and **every acfSMA** (−3.97 → −4.90,
−2.96 → −4.25, −1.09 → −2.09) — the long-memory moments pay. (The clustering moments do not: every vAC
*improved* slightly, vAC1 −6.23 → −5.76 and so on, as did VR60.) This is P2-12/P2-16's conditionality made
quantitative: (σ_V, h, sbar) are jointly identified **with** the volatility block, and the hand-over that
carried "expected to move again at Phase 3" was right to. **Stated symmetrically, as it should be**: Phase 2's
7.50 d lies outside the new [18.75, 32.64], *and* the new 22.38 d lies inside Phase 2's own [3.81, 23.61] —
the two fits disagree on the point estimate and are compatible at the interval level, which is what a
conditional parameter with a wide interval looks like. The new half-life sits where three
earlier signals already pointed (estimator A's exploratory two-component preferred ≈ 40 d; the p1 sub-period
gave 13 d; the plan's original sweep grid started at 30 d). Verifications on the adopted triple: **V4** — a
50-path × 20,000-day free run reproduces the target unconditional sd to 0.02 % (0.021788 vs 0.021793,
0.04 SE); realised sd(x) = **0.0680** (up from the handed-over 0.042 — coverage consequences measured in E3.7).
**V7** — E2.5's estimator rows re-run at h\* (`e2_5/hl_at_h22.json`): a 200-day window's naive sample half-life
is **16.0 d** [IQR 10.8–23.0] against the true 22.4 (−29 % bias; median-unbiased 27.9 at T = 200, 22.4 at
T = 5,000), so "what the agent experiences" and the true persistence are the same order but no longer the same
number, and every quoted half-life carries its horizon and estimator as E2.5's rule requires.

### 3.8 E3.6, the guards, and what the new block does to the process the agent sees

**Item 73 closed** (`e3_6/item73.md`; SCL panel, 200 seeds per scenario): item 5's statistic computed both ways —
**whole path α+β = 0.975** (IQR 0.906–0.997, n = 1,820 fits) and **calm windows only 0.942** (IQR 0.703–0.988,
n = 788 contiguous runs ≥ 100 d) — both inside item 5's [0.90, 0.995]. The regime paths raise measured
persistence by ≈ 0.033, which is the number item 73 asked to have on the record.

**The E[x] guard at the new block** (FX3, 1,000 flat paths, seeds 240000+, `e3_4/flat_x_p3.json`): jumps on
**−0.0015 [−0.0037, +0.0007]**, jumps off −0.0012 [−0.0032, +0.0009] — both pass the ±0.02 TOST; the rare large
jumps are mean-zero in effect as designed, and `test_flat_x_equivalence` now guards against this measurement.

**The burn-in guard** (`e3_4/burn_in_guard.json`): the engine in force at its 750-day option-A burn-in, re-run
E1.5-style under the new block — day-1 vs day-5000 KS points x 0.050, σ² 0.067 (< 0.10) at 500 vs 1,000 paths.
The legacy sensitivity engines' Phase-1 references and stored states were sampled under v2's shape and are
**stale** under the block in force; `test_burn_in_stationary` says so and §7 assigns the regeneration.

### 3.9 E3.7 — the benchmark discriminates better, not worse, on the new block

E2.7's design re-run unchanged on the hand-over (40 training seeds disjoint from 50 scored, three personas ×
four scenarios, paired 2,000-resample cluster bootstrap; local machine; `e3_7/discrimination.{json,md}`).
**The G1 ordering holds in all four scenarios with both gaps positive at 95 %**, and the Phase-2 §5.1
trade-off improves on *both* axes:

| scenario | coverage (P2 → P3) | runs with NO resolvable step | gap L5→trivial (P2 → P3) |
|---|---|---|---|
| flat | 0.128 → **0.378** | 4 % → **0 %** | 0.0289 → **0.0455** |
| crash | 0.422 → 0.585 | 0 % → 0 % | 0.0756 → 0.0703 |
| bull trap | 0.539 → 0.637 | 0 % → 0 % | 0.0630 → 0.0749 |
| sustained bull | 0.031 → 0.044 | **10 % → 10 %** | 0.0171 → 0.0302 |

Flat recovers most of what Phase 2's fast engine cost — the spread is back at Phase 1's 0.0434-level and MCR is
defined on every flat run again. **Sustained bull remains the structural exception** (coverage 0.044, one run
in ten with nothing to resolve): its anchoring drift pins x by design, which is REG-7 / D14's scenario-purpose
question, owned by Phase 4, not a volatility matter. In flat the best L5 variant is the **full field set**
again (Phase 2's price-only flip reverses — consistent with §4's finding that the calm price channel closed).

### 3.10 E3.8 — the level-free channel decomposed, block by block

The E2.8 machinery extended to one-block-at-a-time arms at the parameters in force (200 paths × 200 days per
arm, identical features/estimators/cross-validation to the SEP audit; `e3_8/decomposition.{json,md}`):

| arm | level-free calm R²(x) [95 % CI] | Δ over exact | Gaussian bound |
|---|---|---|---|
| exact (the bound's model) | 0.145 [0.108, 0.176] | — | **0.163** |
| + GJR-t innovation | 0.145 [0.096, 0.184] | **+0.000** | 0.163 |
| + jumps (FIT λ, σ_J) | 0.192 [0.105, 0.288] | +0.047 | 0.177 |
| + GJR-t + jumps | 0.203 [0.141, 0.262] | +0.057 | 0.177 |

Three findings. **(V6)** The Appendix-B bound at the refit parameters is **0.163** and the exact-process
surrogate sits at 0.145 [0.108, 0.176] — at/below the bound, so E2.8's "the machinery is unbiased" verdict
carries to the new block. **[Corrected 5 September, P3-12]** This section first went on to say that the
generator's own calm number "sits far below any bound" and that Phase 2's "+0.10 over the exact bound" question
therefore "dissolves at the block in force". That rested on the cross-phase-trained −0.58 and is **withdrawn**:
measured on the same calm-trained footing as these arms, the full generator's level-free calm R² is
**+0.349**, which sits **above** the 0.163 bound by about +0.19 — so the question does not dissolve, it
persists at a slightly larger size than Phase 2's +0.10, and §3.11 locates it. **The GJR innovation contributes nothing** to level-free calm readability (+0.000):
conditional heteroskedasticity changes *when* returns are loud, not what they say about x. **The jump block is
the one volatility channel with a readable signature** (+0.05 in isolation, wide CI): a 20 %-scale one-day x
move is a loud event whose 22-day decay a return-reader can follow — a *legitimate* channel (the very large
non-Gaussian innovation is inside Appendix B's own caveat, and the reference line for jumpy innovations is
0.177). The reconciliation with §4's **negative** full-generator calm number is a training-regime fact worth
stating precisely: these arms are calm-only worlds, so the surrogate trains on calm data and extracts what calm
returns carry (up to ≈ 0.20); the deployed environment's surrogate trains across all phases, where the event
channel dominates, and its calm-day predictions fall below the mean-baseline. Phase 6 inherits a much simpler
characterisation than Phase 2 left it: the calm price channel is closed, the GJR block is inert as a channel,
the jump channel is small and rare, and what remains is the **event-phase channel** (all-phases full-field
0.843), which is Phase 4's/Phase 6's territory.

### 3.11 E3.9 — the post-review extensions, and one conclusion withdrawn

The report was reviewed against the artefacts after it was written (5 September 2026). Four of the review's
findings were experiments or registered deliverables rather than edits; their designs and rules were fixed in
`PREREG_PHASE_3_ADDENDUM.md` §4 **before** the runs, with disclosure that the whole report and the review had
been seen. Six further findings were miscopied or stale numbers and are corrected in place (§4's test table and
the list at the end of this section). The review's own numbers were verified against the files first; one of
its characterisations is corrected in ADDENDUM §4.4.

**(a) The calm-trained surrogate — this phase's conclusion withdrawn** (`e3_9/calm_trained.{json,md}`). The
audit's `l2_surrogate` fits on all rows and masks by phase group afterwards, so its calm R² is a
cross-phase-trained statistic. Re-fitting the same machinery — same features, same three estimators, same
GroupKFold by path, same 500-resample cluster bootstrap — on **calm rows only**, on the stored hand-over panels
of both phases, so the comparison is like-for-like:

| state | feature set | published (cross-phase-trained) | **calm-trained** |
|---|---|---|---|
| Phase 2 | level-free | +0.339 [0.208, 0.434] / sign 0.827 | **+0.421 [0.298, 0.523] / sign 0.892** |
| Phase 2 | full field set | +0.346 [0.206, 0.446] / sign 0.842 | +0.626 [0.564, 0.682] / sign 0.942 |
| **Phase 3** | level-free | −0.582 [−0.716, −0.470] / sign 0.722 | **+0.349 [0.322, 0.374] / sign 0.814** |
| **Phase 3** | full field set | +0.213 [0.141, 0.270] / sign 0.834 | +0.550 [0.518, 0.579] / sign 0.906 |

**The claim "the calm price channel is gone" is withdrawn** (P3-12). On the consistent estimator the channel
goes **0.421 → 0.349** in R² and **0.892 → 0.814** in sign accuracy: a real but modest narrowing, not a
closure. Two consequences follow. First, §3.10's reading that the Appendix-B question "dissolves" is withdrawn
too: at the block in force the bound is 0.163 and the calm-trained generator measures 0.349, so the excess is
about **+0.19** — larger than Phase 2's +0.10, not absent. Second, the decomposition now closes cleanly on one
footing: E3.8's calm-only arms reach 0.203 with the GJR innovation and jumps in place, so roughly **+0.15 of
the excess is the events-and-sentiment contribution as it shows up on calm days** (pre- and post-event calm
rows inside event scenarios), which is precisely the characterisation problem P2-18 handed to Phase 6 — now
posed on a consistent statistic and with two of its four blocks already measured.

**(b) `sbar`'s interval, a registered deliverable delivered late** (`e3_9/sbar_interval.json`). PREREG §3.4
registered a Monte-Carlo propagation over the refit draws of (σ_V, h), the 1,000 stock-bootstrap draws of s_A
and the 200 refit draws of (λ, σ_J); the phase did not produce it and `volatility.json` carried
`"interval": null` on its most-used number, with **s_A's** interval printed in that column of §4's table.
Delivered at 20,000 draws: **sbar = 0.01509 [0.01342, 0.01678]**, **0 % of draws in the identity's failure
region** (σ_V ≥ s_A never occurs). One limitation is stated on the file rather than papered over: the refit
stored per-parameter percentiles and sds rather than the 30 paired draws, so (σ_V, h) are reconstructed as
CI-clipped normals matched to the stored sd under both an independent and a perfectly rank-correlated pairing;
the two readings agree to the fourth decimal and the wider is adopted. s_A and (λ, σ_J) are resampled from
their stored draws exactly as registered.

**(c) The calm-window mapping, and a confirmed level double-count** (`e3_9/level_check.{json,md}`). PREREG §3.4
registered the calm-window mapping as an alternative to be reported beside the adopted identity; §3.1 claimed
both alternatives "are reported" but only the SMM one was. Delivered, and it settles the level question the
rise/decay rule could not:

- **The panel's own crisis-free calm daily sd is 0.0170 [0.0163, 0.0176]** (√ of the median pre-event 120-day
  `rv_calm` over 1,592 episodes / 412 stocks) against the **0.0218** full-sample unconditional the identity
  targets. **The full sample is 1.28× the panel's own calm** — it averages in the panel's crises.
- The calm-window mapping would therefore put **sbar at 0.00676** (0.45× the adopted 0.01509), giving a flat
  arm at 0.0171 daily sd. Reported, **not adopted**: the adopted anchor is the registered one.
- **The double-count is confirmed.** With events on, over the audit scenario mix (200 seeds each of flat /
  crash δ 0.70 / bull trap / sustained bull), the generator's realised pooled daily return sd is
  **0.0284 [0.0267, 0.0302]** against the 0.0218 target — an excess of **+0.0066 (+30.5 %)** against a
  bootstrap half-width of 0.0017. The mechanism is exactly as the review posed it: the identity pins the
  generator's **calm** to the panel's **all-day** average, and ADDENDUM §1 then re-bases the multipliers to that
  same all-day level, so the event variance stacks on a calm level that already contains it. V4's free-running
  check (0.021788 vs 0.021793) cannot see this, because the free run has no events; E3.4's rise/decay rule
  cannot see it either, because it is a shape test.

Per ADDENDUM §4.3 this is **reported as a defect of the level anchoring, not repaired here**: repairing it
means re-choosing the anchor (the panel's calm rather than its unconditional) and paying the whole
execution-order cascade again, which is a decision for the team — §5.8 — now with the number in hand. It is on
`volatility.json`'s `sbar` label.

**(d) What the jump size costs across its own interval** (`e3_9/jump_sensitivity.{json,md}`). σ_J is the
weakest-identified number in the block and it is not inert (it enters the identity and E3.8 attributed the only
readable volatility channel to it), so the span across the adopted interval was measured, holding λ and
re-deriving sbar from the identity at each σ_J so only the jump/diffusive split moves:

| σ_J | | sbar (identity) | jump share of x-innovation variance | level-free calm R²(x) |
|---|---|---|---|---|
| 0.086 | interval floor (moment arithmetic) | 0.01594 | 1.7 % | +0.158 [0.119, 0.196] |
| **0.230** | **adopted (mixture optimum)** | **0.01509** | **11.9 %** | **+0.176 [0.131, 0.209]** |
| 0.241 | interval ceiling | 0.01499 | 13.1 % | +0.229 [0.170, 0.279] |

**The weak identification costs less than feared**: the channel moves by **+0.018** of R² from the interval
floor to the adopted point, with heavily overlapping intervals — the jump size's uncertainty does not
materially change the leakage picture, and the review's expectation that the channel "largely disappears" at
0.086 is not what the measurement shows (0.158 against 0.176). What the run does settle is the direction of the
error, which the "weakly identified" label did not state: **the adopted 0.230 is the conservative end** — it
overstates the jump channel relative to the interval floor rather than hiding it. That sentence is now on the
parameter file.

**Six checkable errors, corrected in place.** (1) λ's interval was miscopied in three documents: the θ = 4
excess rate is **[+0.00066, +0.00082]** (0.00089 is θ = 4.5's upper limit) and the adopted union is
**[0.00046, 0.00082]** — `volatility.json` carried the right numbers throughout, the prose did not, on the one
parameter whose whole label is "weakly identified". (2) The header contradicted itself on compute provenance
one paragraph apart; the Kaggle statement is the correct one and both now say so. (3) §3.3 quoted 3,125 run-ups
over 394 stocks as the qualifying count: **3,202 over 398 qualify**, and 3,125/394 is the multiplier-usable
subset — and `volatility.json`'s `phase_multipliers.n` recorded the n of none of its own values, now replaced
by the per-family episode and stock counts. (4) Post-top's realised 1.59 is at **n = 20** paths and now carries
it, since it drives a Phase-4 hand-off. (5) `value.json`'s `h_fit` label still said the half-life in force was
150 d and that "Phase 2 reconciles them" — two phases stale, in a file this phase edited; it now records the
22.38 d in force and what superseded it. (6) `known_defects.py`'s L2b entry still quoted +11.7 pp; the audit in
force says **+12.7 pp**, with the Phase-1/2/3 series now on the entry.

## 4. Decisions taken and the parameter file

Eleven decisions, `DECISION_LOG.md` P3-1 … P3-11. **`envs/v2/params/volatility.json`** (new; loader
`envs/v2/volatility_params.py`, the mispricing_params pattern — absent → v2 CAL, present → governs, malformed →
raises — with presence enforced by `test_garch_params_in_force`):

| entry | value in force | label | source | interval / n |
|---|---|---|---|---|
| `garch_shape` | α 0.027, γ 0.058, β 0.932, **df 6.65** | FIT (E3.1 medians; df = E3.2's diffusive tail net of jumps, conditional on the jump block; E3.1's QML 4.86 = the total tail, recorded beside) | `e3_1/summary.md`; `e3_2/adoption.json` | α [0.025, 0.030], γ [0.055, 0.061], β [0.928, 0.935], df [6.48, 6.83]; n = 417 |
| `shape_sensitivity_sets` | P25 / P75 | DESIGN (quantiles of (α, γ, ν, pers), β derived — the raw P75s are nonstationary at 1.028) | `e3_1/confirm.json` | n = 417 |
| `sbar` | **0.01509** | FIT by the §3.4 identity (uncond return sd = 0.0218), conditional on (σ_V\*, h\*) and the jumps; v2's 0.017 CAL and E2.3's 0.0087 named for what they are | `e3_1/summary.md`; `e2_3/smm_ar1c_full_p3.json` | s_A [0.0210, 0.0225]; V4 to 0.02 % |
| `jumps` | rate **0.000583**/d, N(0, **0.230**), placement `x_zero`, q 0.4345 kept, p_ann/lam_res derived | FIT, WEAKLY IDENTIFIED (model rejected J 790; rate robust across three estimators; size to a factor ≈ 2.7) | `e3_2/{adoption,detection,recovery}.json` | λ [0.00046, 0.00082], σ_J [0.086, 0.241]; n = 2,622,096 stock-days |
| `phase_multipliers` | det 1.37, panic 7.45, stab 3.11, mania 1.18, blow-off 1.65, post-top 1.16 (total-return ratios) | FIT (E3.3, unconditional reference, ADDENDUM §1) | `e3_3/episodes.{json,md}` | CIs per phase; 1,592 dd / 3,125 ru episodes over 417/394 stocks |
| `mechanism` | `variance` (A), m_x = 1.35 / 16.17 / 5.63 / 1.35 / (blow-off = mania) / 0.35 | FIT decision (REG-6's fallback: none passes the rise; closed-loop calibrated; two documented shortfalls — the ex-post blow-off label and the drift-dominated post-top) | `e3_4/{decision,arms,calibration,mechanism_c}.json` | realised 1.34 / 7.54 / 3.12 / 1.19 at 200 seeds |
| `iv` | past-only filter (shape + ω = s_A²(1−pers)), π = const −0.0224, ε AR(1) (0.926, 0.083), **T_z 2.70 / 2.28 / 1.88**, no floor | FIT (five CBOE names; T_z derived from the same filter's forecast) | `e3_5/{premium,audit}.json` | ρ range [0.923, 0.931]; n = 17,570 pooled days; mega-cap caveat |
| `engine_refit` | σ_V 0.01457, h 22.38 (also → `value.json`, `mispricing.json`) | FIT (§9's constrained re-launch; conditional on this block) | `e2_3/smm_ar1c_full_p3.json` | σ_V [0.01275, 0.01527], h [18.75, 32.64]; 30 refits |

**Execution-order rule, paid in full.** The block changes every path: `path_hashes_phase3_after.json`
(95 configurations; 2,648 non-analyst hidden-column changes against Phase 2's hashes — the whole environment
moved, as it must), the Section-9 checklist at 200 seeds on SCL, the SEP level-free audit on the local
reference machine, and a rewritten freeze manifest ("v2.1 Phase 3 freeze").

**The checklist, before and after, on the same panel:** Phase 2's hand-over passed **5 of 20**; Phase 3's
passes **5 of 20 with the identical pass set** (items 1, 5, 12, 15, 20) — and substantial movement *inside*
the rows: item 13's IV **levels** are back in band (calm 32.1 %, panic 67.4 % — the w²-inflated 51 % of the
handed-over state is gone) while its corr(IV, RV21) falls to 0.23 because the FIT AR(1) noise dilutes it
exactly as the five real names' noise does (the 0.4–0.8 band is v2 CAL; the plan's own E3.5(iii) sends item 13
to Phase 6 for re-derivation from the empirical IV–RV distribution); item 2's kurtosis share falls to 54 %
(rare jumps no longer manufacture per-path kurtosis on most 200-day windows — E1.4 predicted 0.65–0.67 under
mean-zero CAL jumps, and the fitted rate is 17× rarer; the criterion is v2 CAL, re-gated in Phase 6 per
weakness 13's closing note); item 3's clustering-share falls to 42 % (the *fitted* α 0.027 has less short-window
LB power than v2's inflated 0.10 — the panel's own shape, not a calibration target); item 9 now reads
half-life 17 d at T = 800 / 10 d on 200-day windows against a true 22.4 (the estimator-bias table's exact
prediction); item 20 passes with calm σ 2.02 % — the identity's landing inside the 1.4–2.2 band. Items 14/16
come from the audit below.

**The level-free leakage audit on the handed-over state** (SEP: 1,600 paths, 288,000 rows, 119,419 calm rows,
no subsampling, local reference machine; `e3_after/audit_after_levelfree.*`; under `--control level_free` the
tables' "price_only" rows are the level-free control, as in Phases 1–2). Best model per cell beside Phase 2's
identical construction:

| control / field set | Phase 2 after | **Phase 3 after** | direction |
|---|---|---|---|
| level-free, calm — **R²** | 0.339 [0.208, 0.434] | −0.58 [−0.72, −0.47] | see the withdrawal below |
| level-free, calm — **sign accuracy** | **0.827** [0.812, 0.840] | **0.722** [0.702, 0.741] | narrower, still above the plan's 0.70 |
| level-free, all phases | 0.487 [0.472, 0.501] | 0.517 [0.503, 0.532] | ≈ unchanged |
| full field set, calm | 0.346 [0.206, 0.446] | **0.213 [0.141, 0.270]** (sign 0.834) | better (−0.13) |
| full field set, all phases | 0.731 [0.719, 0.743] | 0.843 [0.836, 0.851] | worse (+0.11) |
| L2b macro-phase selectivity | +15.4 pp | **+12.7 pp** (78.3 % full vs 65.6 % price-only) | better; the 10 pp margin still fails (registered Phase-6 defect) |

> **Withdrawal (5 September 2026, post-review; P3-12).** This report first read the negative calm R² as "the
> calm price channel is gone — there is nothing left in returns and ratios for a calm-day reader to key on".
> **That conclusion is withdrawn.** Two things in this phase's own files contradict it, both surfaced by the
> review and both confirmed by measurement (§3.11): (i) in the very same rows, **sign accuracy on resolvable
> steps is 0.722 [0.702, 0.741]** — the level-free calm reader lost the magnitude and kept the **direction**,
> above the plan's own L2 sign threshold of 0.70, and for a mandate-conformity benchmark the directional call
> is the one that matters; (ii) `l2_surrogate` fits on **all** rows and masks by phase group afterwards, so the
> published calm R² is a **cross-phase-trained** model scored on calm-only variance — a large negative number
> there is substantially a train/eval regime artefact. Re-fitting the same machinery on calm rows only
> (E3.9a) gives a level-free calm R² of **+0.349 [0.322, 0.374]** at the block in force against Phase 2's
> **+0.421** on the identical estimator. **The calm price channel narrowed modestly; it did not close.**

**What the audit rows do and do not say.** The −0.58 is real as a property of the *deployed* surrogate — the
one the audit publishes and Phase 6's gate will be written on — and it moved for a reason worth recording: with
sd(x) 0.068 the event phases move x roughly twice as far as under Phase 2, so an all-phase-trained model is
pulled further from calm-day behaviour and scores worse there. But it is not a measurement of what a calm-day
reader can extract, and this report should not have used it as one. On the consistent (calm-trained) estimator
the channel goes 0.421 → 0.349 in R² and 0.892 → 0.814 in sign accuracy: an improvement of about 0.07 R², not
a closure. What **did** rise is the **all-phases full-field** number (0.731 → 0.843): the scripted event phases
move x a lot and the fields read it — the event-phase channel, which is Phase 4/6's territory, now dominates
the leakage picture, but it does so **beside** the calm channel rather than in place of it. **The IV fix
shows up independently in two places**: L2b's selectivity improves by 2.7 pp, and the scenario-discrimination
table's price+IV accuracy equals price-only *exactly* (53.7 % = 53.7 %) — the rendered IV contributes nothing
to phase identification beyond the price path, which is E3.5's design goal measured. Sustained-bull day recall
from price alone is 34.5 % (v2's was 83 %). The L1/L2 absolute rows and their registered Phase-6 defects are
reported in the audit file unchanged in ownership.

**Freeze**: `tests/v2_freeze_manifest.json` rewritten on the handed-over state — label **"v2.1 Phase 3
freeze"**, 23 files (volatility.json and volatility_params.py now under the hash), `manifest OK`.

**Test changes, each with why it is not tuning** (the Phase-2 pattern):

| test | what changed | why it is not tuning |
|---|---|---|
| `test_garch_shape_matches_e3_1` | hard; asserts (α, γ, β) = E3.1's medians AND the shape in force = `volatility.json` (df from the mixture fit, with E3.1's total-tail ν recorded beside) | strictly stronger than the registered xfail: the shape is checked against the file that carries its provenance, and the file against E3.1; the df distinction (diffusive vs total) is the reconciliation P2-12 asked for, not a relaxation |
| `test_iv_continuity` | hard; tolerance = the DERIVED T_z per transition from `volatility.json` | the plan's own §7.4 prescription ("the 95th percentile of the realised-variance change-point statistic") — derived, not chosen; measured z is +0.12 against a bound of 2.70 |
| `test_flat_x_equivalence` | stored reference → the FX3 measurement on the block in force | same assertion, same margins; Phase 2's file describes an engine block that no longer runs |
| `test_jump_placement_variants` | a machinery probe at explicit probe values (0.01, 0.03) | at the FIT λ (17× rarer) the placement's mean offset (−0.0008) is undetectable at any affordable seed count — asserting it would be vacuous; the probe tests the placement code, which is what the test always protected |
| `test_burn_in_stationary` | stored-run assertions kept; the live guard now covers the ENGINE IN FORCE against a reference regenerated under the Phase-3 block (x 0.050, σ² 0.067 < 0.10); legacy engines' live guards removed with the staleness documented | the Phase-1 references were sampled under v2's GARCH shape; comparing them against new-shape day-1 states is a cross-block comparison, not E1.5's stationarity question; the engine that runs is guarded afresh |
| `test_docs_numbers::test_code_constants…` | the jump chain: GenConfig == `value.json` (in force) and the Phase-0 canonical numbers == the entry's recorded v2 CAL `previous` | the canonical numbers describe v2 and still do; the chain now also asserts the supersession is recorded |

The known-defect registry holds **three** entries, none of them Phase 3's: the sustained-bull selection
(Phase 4) and the two Phase-6 leakage gates. Phase 3's two entries are cleared with their tests hard and green.

## 5. Decisions the team must take

1. **The engine moved again, and the §5.1 trade-off has new numbers.** The refit under the fitted volatility
   block lands at σ_V 0.01457, **h 22.4 d [18.7, 32.6]** and sd(x) **0.068** — half-way between Phase 2's fast
   small mispricing (7.5 d, 0.042) and v2's slow large one (150 d, 0.175). Phase 2's h = 7.5 is *outside* the
   new interval: the persistence estimate is engine-block-conditional, and the block is now the fitted one.
   Two Phase-2 §5 pains ease by themselves: the **bull-trap rejection rate falls 0.94 → 0.127** (crash 0.0) at
   200 seeds, and coverage rises with sd(x) (E3.7's table at hand-over quantifies the L5 spread and the
   MCR-undefined shares). The D3/D8 choice (fitted vs v2 vs factor) should be re-read against this state, not
   Phase 2's.
2. **The jump block's honest label.** Three estimators agree the panel's excess-over-t-tail is real and rare
   (λ ≈ 0.15/yr, 0 excluded); its size is identified only to a factor ≈ 2.7 (σ_J 0.086–0.241; adopted 0.230).
   A 20 %-scale one-day move ≈ once per seven years per name is what the extreme tail supports, but the team
   should know the size rests on the weakest identification in the phase — the WRDS re-run (D1 = C) with the
   delisted tail and announcement-timestamped data is the remedy, and `test_jump_process` locks whatever value
   is in force.
3. **Four Phase-4 hand-offs with numbers.** (i) The empirical fast-crash rise time (onset → RV21 peak) is
   **30 d [29, 35]**; the generator's schedule template cannot produce it under ANY variance mechanism (best
   75.5 d) — the deterioration+panic shape, not the variance block, owns the gap. (ii) The **blow-off label is
   assigned ex post**, so its variance multiplier has been dead code since v2 — the relabel machinery needs a
   decision if blow-off is to have its empirical 1.65× variance. (iii) **Post-top is drift-dominated** (realised
   1.59× vs the empirical 1.16× whatever the innovation multiplier) — E4.8's reversal-leg shape question.
   (iv) **The bubble hazard is stale under the new x dynamics**: the topped share falls to **8 %** against its
   40–60 % target (item 11; the CAL (h0, b) = (3·10⁻⁴, 6.0) was grid-searched against the old engine), while
   the bull-trap rejection rate *improves* to 10.7 % — the hazard/g_max re-calibration is Phase 4's (weakness
   items 17, 41) and now has its trigger measured. Sustained-bull rejection stands at 32.9 % (its band vs
   sd(x) 0.068 — the registered Phase-4 defect, unchanged in ownership).
4. **Ratification of the three addendum corrections** (`PREREG_PHASE_3_ADDENDUM.md`): the run-up calm reference
   (the registered window measured a post-crash trough at 2.74× unconditional), the fast-crash secondary
   population for E3.4's adoption, and the E3.2 adoption after both registered paths failed measurably (the
   recovery gate at λ ±59 %, the fallback degenerate at λ → 3·10⁻¹⁴). Each was corrected before the run it
   governs, with the disclosure paragraphs, and reported under both rules.
5. **The legacy sensitivity engines' stored burn-in states are stale** under the Phase-3 block (sampled under
   v2's GARCH shape; `test_burn_in_stationary` documents it). Any Phase-6/9 sensitivity that runs
   `fw_fallback_hl150`/`fw_hl60`/`fw_index`/`pruna`/`ar1` must regenerate them first (the E1.5 tool does it in
   one run); the engine in force is guarded fresh (KS 0.050/0.067).
6. **Kaggle policy, upgraded from unproven to proven.** The cross-machine reference row agreed to 6.4·10⁻¹⁶
   across numpy/scipy versions, and E3.4's simulation ran on the proven kernel; the audits, L5 and every
   surrogate number stayed local. The bundle is `finpersona-phase3-bundle`; `datasets/` never left this machine.
7. **The level anchoring is a confirmed defect and the choice of anchor is the team's** (§3.11c). The
   identity pins the generator's calm to the panel's **full-sample** unconditional sd (0.0218), which is
   **1.28×** the panel's own crisis-free calm (0.0170); the event multipliers, re-based to that same all-day
   level by ADDENDUM §1, then stack on top, and the deployed generator runs **+30 %** hot (0.0284 against
   0.0218). Three options, none of them free: (a) keep the anchor and publish the +30 % as a stated property
   (no re-run; but every magnitude item and Phase 4's schedule inherit a generator whose unconditional exceeds
   its own target); (b) re-anchor to the panel's calm (sbar 0.00676 — §3.11c measured it) and pay the full
   execution-order cascade again, which also roughly halves sd(x) and undoes most of this phase's coverage
   gain; (c) keep the calm anchor for sbar but re-derive the multipliers against the panel's calm reference so
   the deployed mix lands on 0.0218. (c) is the internally consistent one and is the most work. **Phase 4
   builds the schedule on this level**, so the decision is better taken now than after.
8. **The leakage picture is not what this report first said** (§3.11a, P3-12). On a consistent calm-trained
   surrogate the calm level-free channel narrowed from 0.421 to 0.349 rather than closing, and the excess over
   the Appendix-B bound at the block in force is about **+0.19** (0.349 against 0.163) — larger than Phase 2's
   +0.10. E3.8 places ≈ 0.20 of it in the exact-process + GJR + jump stack, leaving ≈ +0.15 for events and
   sentiment on calm rows. Phase 6 inherits a **characterisation** problem, as P2-18 said — not a closed
   channel, and the report's first reading to the contrary is withdrawn.
9. **REG-15 stands on every fitted value**: set A is survivor-only, so tails, depths and multipliers are
   understated; set B's direction check (fatter, more volatile) is printed beside each; the WRDS re-fit remains
   the standing remedy.

## 6. Files written or changed

Nothing committed; everything is in the working tree on `main`. `docs/` and `datasets/` are git-ignored by
design. The complete list, with what each file is, is `PHASE_3_CHANGED_FILES.md`.

## 7. What was not done, and who owns it

- **The FW engines were not re-contested** under the new block (the §9 refit covers the adopted engine only);
  E2.4's decision stands on its own rule, and a full re-contest belongs to the WRDS re-run (D1 = C).
- **The legacy engines' stored burn-in states** were not regenerated (no Phase-3 output uses them); Phase 6/9
  regenerate before running those sensitivities (§5.5).
- **The E2.6-style persistence sweep was not re-run at the new h\*** — the levels 15/30 already bracket 22.4 in
  Phase 2's sweep (`e2_6/sweep.md` rows 15 and 30: oracle switch medians 1–2 at 0.45–0.69 share under matched
  sd; 2 at 0.55–0.69 under matched innovation), and the G3 statistics on the state in force are E3.7's/Phase 6's.
- **The blow-off relabel machinery and the post-top drift shape** — Phase 4's (E4.8), with this phase's numbers.
- **The pooled-vs-typical tail decomposition** (cross-sectional ν heterogeneity defeats a single-ν reading of
  the pooled exceedance curve) — quantified enough to adopt with wide intervals; a per-stock hierarchical fit is
  a WRDS-era improvement, noted for Phase 10's limitations section.
- **Item 2's kurtosis share re-gating** — the after-state checklist reports the item; the criterion itself is
  Phase 6's re-derivation (weakness 13's closing note).
- **MCR's undefinedness rule** — Phase 7's; the shares at the new coverage are in E3.7's table.
- **The E3.9 post-review extensions are done, not deferred** (§3.11): the calm-trained surrogate, `sbar`'s
  registered interval, the calm-window mapping with the level double-count, and the jump-size span. What they
  leave open is named in §5.7 (the anchor choice) and §5.8 (the characterisation Phase 6 owns).
- **The audit's estimator was not changed.** `l2_surrogate` still trains across phases and masks afterwards;
  E3.9a runs beside it rather than replacing it, because the published statistic is the one Phase 6's gate will
  be written on and changing it mid-programme would break every before/after row. Phase 6 should decide which
  training regime its gate uses — the pair is now measured on both states.
- **Phase 4 is not started.**
