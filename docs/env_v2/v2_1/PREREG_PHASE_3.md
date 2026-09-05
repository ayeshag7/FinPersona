# Pre-registration, Phase 3 (v2.1): volatility — GARCH, jumps, regime variance and implied volatility

Status: **written 2 September 2026, before any Phase-3 experiment was run.** Working tree on `main` at commit
`b563e9d` (the v2.1 Phase-2 state; `tests/v2_freeze_manifest.json` label "v2.1 Phase 2 freeze (post-review)",
`python -m tools.freeze_manifest --check` reports `manifest OK`), plus the untracked `PHASE_3_EXECUTION_PROMPT.md`.
Governing documents: `V2_1_IMPROVEMENT_PLAN.md` Section 7 (Phase 3) with Sections 1, 3, 16, 16A, 17 and
Appendices A–B; `V2_1_ALTERNATIVES_REGISTER.md` **REG-6** (whose decision rule this document restates without
change) and REG-15; `PREREG_PHASE_2.md` and `PREREG_PHASE_2_ADDENDUM.md` (the worked precedent);
`PHASE_2_REPORT.md`; `PHASE_1_REPORT.md` §4.1 (E3.1) and §4.3 (E1.4).

**Team decisions in force.** D1 = C (hybrid: fit on the free panel, publish every fitted value with its
survivor-vs-literature gap, keep the code re-runnable on WRDS by a data-path change; WRDS **not** confirmed).
D13 = mechanism **C** (`start_price_mode = "both"`). D16 = full programme. **The §5.1 blank of the Phase-2 report
(keep the fitted environment / keep v2's / both as a factor) is empty in the execution prompt, so Phase 3 proceeds
on the environment as handed over** — the `ar1_fit` engine at σ_V 0.01220, half-life 7.50 d, `sbar` 0.017 CAL —
and does not re-tune the engine to change coverage. §14 lists what in this phase would differ under the
alternative. D2 and D10 are not needed here.

Everything below — seeds, panels, estimators, window definitions, statistics, model families, decision rules,
sample sizes and what is reported when a rule is not met — is fixed here and is **not moved after any number is
seen**. If a criterion turns out to be wrong or undecidable, `PREREG_PHASE_3_ADDENDUM.md` corrects it in a
separate documented step **before** the run it governs, with disclosure of what had already been seen, and results
are reported under both rules.

---

## 0. Provenance labels, the citation rule, and what had been seen when this was written

LIT / FIT / CAL / DESIGN as the plan defines them. Every number that enters `envs/v2/params/volatility.json`,
`mispricing.json`, `value.json`, a test tolerance or a document in this phase is FIT on the stated panel, or
DESIGN with the alternatives and the discriminating experiment named, or CAL/LIT with that label. Literature
values are quoted **beside** fitted values, never as tolerances.

**Sources.** The literature this phase relies on was read by the plan's own verification pass and is carried at
the statuses the plan records (PLAN §7.1, marked "[changed: LOG §4.2]", each entry "read"): Engle 2001 (JEP;
α 0.077 / β 0.905, **portfolio** level — the report must say why this is not a per-stock anchor); Hansen & Lunde
2005 (JAE; leverage models beat GARCH(1,1) on IBM daily); Glosten, Jagannathan & Runkle 1993 (monthly);
Lee & Mykland 2008 (RFS; rejection at β* = 4.6 at 1 %, intraday); Andersen, Bollerslev & Diebold 2007 (REStat;
jump variation 14.4 % of realised variance, 27.9 % of days — **index futures**, printed beside, never tolerances);
Ang & Timmermann 2012 (monthly S&P σ 4.89 % vs 2.45 %, variance ratio ≈ 4.0); Ang & Bekaert 2002 (7.04 % vs
3.77 %, monthly); Schwert 1989 (JF; recession/expansion volatility +76 % to +227 %, index, monthly); Greenwood,
Shleifer & You 2019 (JFE; 40 run-ups, 21 crashed; volatility rises in run-ups that crash — industry, monthly);
Carr & Wu 2009 (RFS; individual-stock log VRPs negative for 21 of 35 names); Goyal & Saretto 2009 (JFE; the sort
is on log(RV/IV)); Christensen & Prabhala 1998 (JFE; log RV on log IV slope 0.76, R² 39 %, S&P 100 monthly).
**Hamilton & Susmel (1994) is flagged not retrievable and is not quoted anywhere in this phase.** Bakshi &
Kapadia 2003 is index-only and is not used for any single-stock claim. No statistic marked "(to verify)" enters
a parameter file, tolerance or slide. The report's §1 carries the citation table with these statuses.

**Disclosure of what had been seen when this document was written.** Everything published by Phases 0–2 —
including `e3_1/summary.{md,json}` and `garch_fits.csv` (the E3.1 fits this phase confirms), `e1_4/panel_split.json`
(the jump-window split), `e2_3/smm_ar1_full.json`, the Phase-2 report and its after-state audits — plus the code.
**No Phase-3 statistic has been computed.** Three derived observations made while writing this document, from
published numbers and static code reading only, are disclosed because the designs below respond to them:

1. **Arithmetic on published values** (no new data): at the handed-over σ_V = 0.01220 and ρ = 2^(−1/7.498) = 0.9118,
   the variance-accounting identity of §3.4 evaluated at E3.1's published unconditional sd 0.0218 and v2's CAL
   jump block gives sbar ≈ 0.0174 — close to the CAL 0.017 in force. No §3 rule depends on this; it is stated so
   that the identity cannot later be suspected of being reverse-engineered from the answer.
2. **Arithmetic on published values**: for a standardised t(4.86), P(|z| > 4) ≈ 0.004 per day, the same order as
   E1.4's published pooled |z| > 4 share (7,492 / 1,670,790 ≈ 0.0045 on 2009–2024). The E3.2 design below is
   built around exactly this confound (the fitted t-tail explains most raw exceedances), which is why its primary
   estimator is a mixture fit with a recovery check rather than a raw count.
3. **Static code reading**: for the AR(1) engine family, `MispricingState.weight()` returns the FW weight at the
   frozen initial population share n_f = 0.5, i.e. w ≡ (0.5·0.758 + 0.5·2.087)/1.0 = 1.4225, and `iv_block` feeds
   w²·fvar21 — so the handed-over IV level carries a constant ×1.4225² factor that is a residual of the FW
   plumbing, not a design choice. It is constant (no leak), it dies with E3.5's construction, and it is verified
   numerically in §1's V5.

---

## 1. What is inherited, what is re-derived, and what is verified before use

**Inherited and not redone.**

- **E3.1's fits exist** (run inside Phase 1 because E1.4 and E2.3 needed them): per-stock GJR-GARCH(1,1)-t on
  set A (417) and set B (155), full sample + four sub-periods, 1,000-resample stock bootstraps, residuals stored.
  Phase 3 **confirms and documents** them (§3); it does not re-run the fits.
- **E1.4's jump placement** `x_zero` and its announcement split q = 0.4345 [0.412, 0.456] (n = 7,492 jump days)
  are FIT and are **kept**; what E3.2 re-fits is the rate and the size distribution (and the tail df jointly,
  §4). `p_ann` and `lam_res` are mechanical derivations from (λ, q) and are re-derived from the new λ.
- The engine and its structural parameters (`ar1_fit`, σ_V 0.01220 [0.01066, 0.01419], h 7.498 d [3.81, 23.61],
  price_scale 1), μ_V = 0.0002281 (FIT), df_V = 5 (DESIGN), start-price mechanism C, burn-in rules (E1.5).
- The Phase-2 diagnostics and tools this phase re-runs at hand-over: `e2_7_discrimination.py`,
  `e2_8_bound_check.py`, `after_state.py`, and the SMM stack (`e2_3_smm.py`, `engines.py`, `moments.py`, the
  cached data moments and weight matrices).

**Verified before use** (the "verify inherited numbers, including mine" rule). Each check is run and its outcome
reported in `PHASE_3_REPORT.md` §1, whether or not it agrees:

| # | Inherited claim | Where it is checked |
|---|---|---|
| V1 | The E3.1 summary medians and CIs (α 0.027, γ 0.058, β 0.932, ν 4.86, persistence 0.991, uncond sd 0.0218) equal what `garch_fits.csv` gives when the medians and stock bootstrap are recomputed from the per-stock rows | recomputed by `tools/phase3/e3_1_confirm.py` |
| V2 | `e1_4/panel_split.json`'s q, window share, rates in/out, and n against the file | re-read and re-derived from `panel_residuals_split.parquet` |
| V3 | `params/mispricing.json` structural values equal `e2_3/smm_ar1_full.json`; `value.json` σ_V equals both | `tools/phase3/e3_1_confirm.py` |
| V4 | The variance identity of §3.4: the engine simulated long at the identity's sbar reproduces the target unconditional daily return sd | 200,000-step simulation at the adopted block (§3.4's own verification) |
| V5 | Disclosure 3 above: w ≡ 1.4225 on `ar1_fit` paths, and the handed-over IV level carries it | one generated path, exact equality |
| V6 | The Appendix-B bound at the parameters in force (0.245 window-average) recomputed after the refit moves (σ_V, sbar, h) | `tools/phase1/kalman_bound.py` at the new values (feeds the E3.8 decomposition) |
| V7 | E2.5's fitted-level half-life rows apply at the refit h\* (the estimator table is quoted whenever a half-life is) | `e2_5` machinery re-run at h\* if h\* moves outside 7.5 ± 1 d |

---

## 2. Seeds, panels, sample sizes (fixed; fresh — disjoint from Phases 0–2's 0–185000 and 770001–770499)

| Block | Purpose | Seeds | Size |
|---|---|---|---|
| PW3 | power / decidability pilots (§10) | 780001–780199 | as stated per PA row |
| JR | E3.2 recovery panels (§4.3) | 200001–200030 | 6 cells × 5 replicates |
| JB | E3.2 stock-bootstrap of the jump moment vector | rng 201001 | 1,000 resamples (200 refits for CIs) |
| EB | E3.3 stock-bootstrap of episode statistics | rng 202001 | 1,000 resamples |
| VM | E3.4 generator arms | crash 210000–210199 per mechanism; flat 211000–211199 | 200 seeds per arm |
| IVA | E3.5 onset audit + continuity-tolerance derivation | 220000–220199 (crash δ 0.70) | 200 seeds; 500 circular-shift permutations (rng 221001) |
| NLA | E3.5 no-look-ahead test | 250000–250019 | 20 seeds |
| SM3 | engine-refit CRN (§9) | 230001 (+13·k for CRN replicate k) | 200 paths × 5,000 d per evaluation, K = 20 |
| SB3 | engine-refit bootstrap refits | 232001–232030 | 30 refits |
| MC3 | engine-refit FW-bootstrap Monte Carlo | 233001–233200 | C = 200 replicates |
| FX3 | flat E[x] re-check at the adopted block | 240000–240999 | 1,000 flat paths (the `test_flat_x_equivalence` design) |
| JP | `test_jump_process` fixture | 251000–251499 | 500 seeds |
| SCL / SEP | after-state checklist and level-free audit | 40000–40199 / 30000–30199 (+31000) | unchanged standard panels, like-for-like with Phases 1–2 |

**Panel (unchanged, D1 = C).** `tools/phase1/panel.py::PanelSpec` with the Phase-1 exclusion rule; set A = 417
flag-free full-history names, 2000-01-03…2024-12-31, daily log returns of `Adj Close`, 6,289 trading days.
Survivorship (REG-15): set A has no delistings, so tails, drawdown depths and unconditional variance understate
the full universe; every fitted value below carries that gap, and set B (155 shorter names, fatter-tailed:
ν 4.33 vs 4.86, uncond sd 0.0243 vs 0.0218) is the direction check. E3.5's five CBOE names are mega-caps and the
report states it.

**Compute placement.** Local reference machine by default, as Phase 2 (no cross-machine reproduction question).
If any stage is offloaded to Kaggle it is simulation/optimisation only, the bundle is refreshed first (the
existing `finpersona-phase1-bundle` predates Phase 2), and `python -m tools.phase2.e2_3_smm --reference-row` is
run **on the kernel** and diffed against the committed `e2_3/reference_row.json` before any offloaded number is
used. No reported surrogate/audit number comes from any machine but the local one; `datasets/` never leaves this
machine (cached derived statistics travel instead).

---

## 3. E3.1 — confirm and document, and the reconciliation of the three volatility scales

### 3.1 What E3.1 adds (no new fits)

(i) verification V1; (ii) the adoption decision of §3.2–3.4; (iii) the sub-period story (persistence 0.946 in
2013–19 to 0.994 in 2000–07, ν 4.6–6.2 — described, no sub-period difference is called significant, since the
stock bootstrap does not model the common time dimension); (iv) the survivor gap beside the literature, with the
explicit statement that **Engle 2001's α 0.077 / β 0.905 is a portfolio-level fit** — aggregation raises α and
lowers β relative to per-stock medians, so it anchors the *order of magnitude*, not the values; (v) the
reconciliation of §3.4.

### 3.2 Adoption: the GARCH shape (α, γ, β)

**Adopted (FIT): the set-A full-sample per-stock medians** α 0.027 [0.025, 0.030], γ 0.058 [0.055, 0.061],
β 0.932 [0.928, 0.935] — the plan's own prescription (§7.2 E3.1 "adopt the median") and the shape E2.3's engine
was fitted against (closing P2-12 rather than re-opening it). Persistence 0.991 [0.991, 0.992].

**Sensitivity sets** (documented in `volatility.json`, run through Phase 6's checklist and Phase 9's grid, not
here): P25 and P75 sets built on the quantiles of **(α, γ, ν, persistence)** with β derived as
persistence − α − γ/2, so both sets are stationary by construction (the raw per-parameter P75s give
α + γ/2 + β = 1.03, a nonstationary artefact of taking marginal quantiles — stated in the file).

### 3.3 Adoption: the innovation tail ν

ν is **jointly identified with the jump block** and is adopted from E3.2's mixture fit (§4) when that fit passes
its recovery check, with the label: *"ν is the diffusive tail net of jumps; E3.1's per-stock QML median 4.86
[4.73, 5.02] is the **total** tail including jump days, and is the fallback if the mixture is not identifiable"*.
Rationale (fixed in advance): E3.1's QML fit has no jump component, so its ν absorbs whatever jumps exist; a
generator that adopted ν = 4.86 **and** an independent jump process on top would double-count tail mass — this is
exactly weakness 13's "re-opens checklist item 2".

### 3.4 Adoption: the unconditional scale `sbar`, and which of the three numbers is which

The three inherited "volatility scale" numbers are three different quantities:

| number | what it actually is |
|---|---|
| **0.0218** [0.0210, 0.0225] (E3.1) | the panel's per-stock median **unconditional daily sd of the total return** r = Δlog P (the GARCH-implied √(ω/(1−persistence)), which equals the sample sd to 4 dp on the full window) |
| **0.00870** [0.00659, 0.01298] (E2.3) | the SMM's fitted **x-innovation scale**, conditional on the engine and on a 17-moment objective the model as a whole fails (J = 80.4; the residual table shows the volatility block is what it misses — vMean −3.54 bootstrap sd — so the SMM trades volatility level against tail/ACF moments and its sbar is **not** a measurement of the panel's volatility) |
| **0.017** (v2 CAL) | the calm **x-innovation sd** in force, stipulated in v2's E1 calibration |

**Adopted rule (FIT by construction from FIT inputs): the generator's free-running unconditional daily return sd
is set equal to E3.1's 0.0218** — the plan's own prescription ("E3.1 adopts the per-stock median unconditional
sd", P2-9) — through the exact variance-accounting identity of the generator's decomposition
log P = log V + x with x an AR(1) whose innovation is the GARCH e plus the mean-zero x-jump:

    var(r) = σ_V² + (2 / (1 + ρ)) · (sbar² + λ·σ_J²)
    ⇒ sbar² = (s_A² − σ_V²) · (1 + ρ)/2 − λ·σ_J²,

with s_A = 0.0218 (E3.1 FIT), σ_V and ρ = 2^(−1/h) the engine's values **after the §9 refit**, and (λ, σ_J)
E3.2's fitted jump block. (The identity is exact for the AR(1)-with-GARCH engine because GARCH innovations are
serially uncorrelated in level; the sentiment feedback's contribution is O(b_pred²) ≈ 6·10⁻⁷, two orders below
the smallest term, and is stated.) Inside the §9 refit the same identity is imposed as a constraint, so the
final (σ_V, h, sbar) triple satisfies it exactly rather than at a stale σ_V.

- **Interval**: Monte-Carlo propagation — the 30 constrained-refit draws of (σ_V, h) (§9), the 1,000 stock-bootstrap
  draws of s_A, and the 200 refit draws of (λ, σ_J) (§4), combined by resampling; the identity's failure region
  (σ_V ≥ s_A) is reported if any draw enters it.
- **Verification V4**: the engine simulated 200,000 steps at the adopted block must reproduce s_A within the
  simulation SE; the measured value is what the report quotes.
- **Reported beside (labelled, not adopted):** (i) the calm-window mapping — sbar set so the generator's calm sd
  matches E3.3's pre-event calm daily sd (the panel's crisis-free reference), with its sd(x) and coverage
  consequences measured in the E3.4 flat arm; (ii) the SMM's 0.0087, with the unconstrained §9 sensitivity fit
  showing what the SMM would still choose when free. The semantics — the generator's free-running calm phase
  corresponds to the panel's full history, with scripted events as *additional* conditioning — is stated in the
  report, and the question "does the whole-variance multiplier double-count what the free-running GARCH already
  produces" is precisely what E3.4's rise/decay rule tests empirically.

---

## 4. E3.2 — jumps

### 4.1 Detection and description (panel side)

On E3.1's stored standardised residuals (`e3_1/residuals.parquet`, set A, full-sample fits, 2000–2024;
n ≈ 2.6 M stock-days), threshold **|z| > 4** (primary — E1.4's threshold, kept for continuity; Lee & Mykland's
β* = 4.6 at 1 % is intraday and is quoted beside, not used), with {3, 3.5, 4.5, 5, 6} reported beside:

- pooled exceedance share per day and per year, with 1,000-resample stock-bootstrap CIs;
- the **expected share under each stock's own fitted t(ν̂ᵢ)** (the no-jump null) and the **excess share**
  (observed − expected), with CIs — stated as a *lower bound* on the jump rate (the QML ν̂ absorbed jump mass, so
  the null tail is too fat) just as the raw share is an *upper bound*;
- sizes: mean, sd and negative share of the day's return r on exceedance days (in and out of announcement
  windows, 2009–2024 where EDGAR exists), with the caveat that exceedance-day returns mix diffusive and jump
  components;
- the announcement split against E1.4's q = 0.4345 (the target, kept).

ABD 2007's 14.4 % / 27.9 % are printed beside as index-level anchors, never tolerances.

### 4.2 The adoption fit (mixture: diffusive t + jumps)

**Model.** z on a day with conditional sd σ̂: z = T + (100·J/σ̂)·B, with T standardised-t(ν), B ~ Bernoulli(λ·w),
J ~ N(0, σ_J); w = q/ws inside announcement windows and (1−q)/(1−ws) outside (q = 0.4345 FIT held fixed,
ws = the panel's window share of days); σ̂ from the **empirical distribution** of the panel's fitted conditional
sds (reconstructed exactly as σ̂ₜ = (100 rₜ − 100 μ̂ᵢ)/zₜ from the stored z and the per-stock μ̂; days with
|z| < 0.01 are excluded from the σ̂ distribution only; the distribution is kept separately for window and
non-window days and binned into 200 quantile bins).

**Moments (9):** pooled exceedance shares at θ ∈ {2.5, 3, 3.5, 4, 4.5, 5, 6} on the full sample, plus the
in-window and out-of-window shares at θ = 4 on 2009–2024. Model predictions are computed semi-analytically
(20-node Gauss–Hermite over J, exact standardised-t tail, averaged over the σ̂ bins) — deterministic, no
simulation noise. **W** = the inverse of the 1,000-resample stock-bootstrap covariance of the 9-vector, shrunk
10 % toward its diagonal (the Phase-2 convention). **Free: (ν, λ, σ_J).** Optimiser: differential evolution
(bounds ν ∈ [3, 40], λ ∈ [10⁻⁵, 0.05], σ_J ∈ [0.005, 0.25], log scale for λ and σ_J) with Nelder–Mead polish.
**Intervals:** 200 refits on stock-bootstrap resamples of the moment vector (seeds JB).

**Known approximation, stated:** the model takes the σ̂ distribution as fixed although the panel's σ̂ paths were
themselves fitted on jumpy data (the QML filter absorbs part of the jumps into ω and α). The recovery check
below measures exactly this distortion end to end, which is why it gates the adoption.

### 4.3 The recovery check (gates the estimator; run before the data fit is trusted)

Simulate panels of **100 stocks × 6,289 days** from GJR-t(ν) + Bernoulli–normal jumps (E3.1's α/γ/β; per-stock
sbar drawn uniformly from the panel's uncond-sd IQR 0.0175–0.0275; window calendar = a 14.5 % share in 10-day
blocks, jumps window-weighted at q = 0.4345), **QML-refit each stock with `arch`** exactly as E3.1 did, then run
the full §4.2 estimator on the fitted residuals. Cells (ν, λ, σ_J): (5.5, 0.001, 0.05), (5.5, 0.004, 0.03),
(8, 0.004, 0.05), (6, 0.010, 0.03), (10, 0.002, 0.08), and **(5, 0, –)** — the no-jump null. 5 replicates per
cell (seeds JR).

**Usability rule (fixed):** the estimator is usable iff the median relative error over the five λ > 0 cells is
≤ 0.20 for each of ν, λ and σ_J (the programme's usability scale, PREREG_PHASE_1 §4.5), **and** in the λ = 0
cell the fitted λ's 95 % interval includes 0 in ≥ 4 of 5 replicates (no spurious jumps).

**Adoption (fixed in advance):**
- **Recovery passes →** adopt (ν, λ, σ_J) from §4.2 (FIT, with intervals): `jump_rate_x` = λ, `jump_sd` = σ_J,
  the generator's GARCH df = ν; placement stays `x_zero`; `p_ann` = λ·q/(4/252) and `lam_res` = λ·(1−q)
  re-derived mechanically (their q is E1.4's FIT).
- **Recovery fails →** fallback, same machinery with **ν pinned at E3.1's median 4.86**: fit (λ, σ_J) only, and
  the report states the double-count (jump mass is then counted once in ν and again in the jump block) as a
  documented limitation with its direction.
- Either way the observed negative share of exceedance-day returns (E1.4: 0.56–0.61) is reported beside the
  mean-zero placement as a known simplification of `x_zero` (mean-zero was chosen by E1.4's pre-registered KS
  rule and is guarded by `test_flat_x_equivalence`, which is re-run at 1,000 flat paths — seeds FX3 — under the
  new block with the same ±0.02 TOST).

### 4.4 Consequences measured, not assumed

The flat-path excess-kurtosis share (checklist item 2's statistic; E1.4 predicted 0.78 → 0.65–0.67 under
mean-zero jumps at the CAL size) is re-scored on the after-state checklist panel and reported against E1.4's
prediction. `test_jump_process` (§11) locks the adopted rate and size at 500 seeds.

---

## 5. E3.3 — phase variance multipliers from event windows

All on set A daily data (Adj Close), all statistics **median over episodes with 1,000-resample stock-bootstrap
95 % CIs** (resampling stocks with all their episodes, so cross-time clustering within a stock survives; the
episode count and stock count are stated on every number). RV(window) = mean of squared daily log returns
(uncentred). Ratios are per episode: RV(window) / RV(pre-event calm), so each stock is its own control.

### 5.1 Episode definitions (fixed)

**Drawdowns.** Per stock: running maximum of Adj Close; an episode = peak (a new running max) → trough (the
minimum before recovery to the prior peak, or the sample end); qualifying iff trough/peak − 1 ≤ −30 %. Windows
(trading days): let d\* = the day at which the trailing 20-day log return, searched over (peak, trough + 20],
is smallest; **panic** = the 20 days ending at d\*; **deterioration** = the 40 days ending at d\* − 20;
**stabilisation** = the 60 days starting at trough + 1; **pre-event calm** = the 120 days ending at peak − 1
(≥ 60 valid days required, else the episode is excluded from ratio statistics with its count stated).
Episodes whose stabilisation window is truncated by the sample end contribute no stabilisation/decay statistic
(counted). Depths are survivor-understated (REG-15) and the report says so.

**Run-ups (GSY-style).** Per stock: a top day τ with (i) P_τ ≥ 2 × min(P over (τ−504, τ]), (ii) P_τ the maximum
of P over (τ−10, τ+10), (iii) at least 252 days after the previous accepted τ of the same stock. Let s = the
argmin day of that 504-day window (the run-up start) and b\* = the day in (τ−126, τ] at which the trailing
20-day log return is largest. **mania** = the 40 days ending at b\* − 20; **blow-off** = the 20 days ending at
b\*; **post-top** = the 60 days starting at τ + 1; **pre-event calm** = the 120 days ending at s.

**Market-wide crash windows** (the plan's five): 2008-10-01…2008-12-31, 2011-07-01…2011-09-30,
2018-10-01…2018-12-31, 2020-01-01…2020-03-31, 2022-01-03…2022-06-30. Per stock and window: RV(window) /
RV(the 120 trading days ending the day before the window), cross-sectional median with stock-bootstrap CI, plus
the same ratio for the window's **peak rolling-21-day RV**. These are anchors beside the single-stock episodes
(the primary sample); 2020Q1's January dilution is inherited from the plan's window definition and stated.

### 5.2 Rise time and decay half-life (E3.4's empirical inputs; drawdown episodes)

Per qualifying drawdown episode: **onset** = the first day with P ≤ 0.9 × peak; **RV peak** = the day of maximal
rolling 21-day RV over [onset, trough + 60]; **rise time** = trading days onset → RV peak; **decay half-life** =
days from the RV peak until rolling 21-day RV first falls to ≤ RV_calm + (RV_peak − RV_calm)/2, censored at 250
days post-peak (censored share stated; the median is reported only if the censored share is < 50 %, else the
verdict of §6 is *undecidable on decay* and says so). Medians with stock-bootstrap 95 % CIs. The plan's two
index examples (2020 ≈ 10 d, 2008 ≈ 30 d) are quoted as anchors, not data. The **stress-spell duration** (days
between the first and last crossing of the half-way RV level) and the pooled share of stock-days above their
own half-way level are also recorded — they parameterise mechanism C (§6).

### 5.3 Adoption

The FIT multipliers are the medians of §5.1's ratios: m_det, m_panic, m_stab from drawdowns; m_mania, m_blow,
m_post from run-ups; sustained-bull stays 1.0 (DESIGN, review R1-D5: a volatility reduction would be a scenario
clock — unchanged and restated). Ang & Timmermann's ≈ 4.0 variance ratio and Schwert's +76 %…+227 % are printed
beside. Because the panel ratios are **total-return** variance ratios while the generator's multiplier acts on
the **x-innovation** variance (V's diffusion is unscaled by phase), the multiplier in force is derived so the
*generator-realised* total ratio matches the FIT median: first-order mapping
m_x = (m_total·s_A² − σ_V²)/(s_A² − σ_V²), then a 1-d search on the generator (200 crash seeds, the E3.4 A-arm
panel) until the realised ratio is inside the FIT median's CI; both target and realised values are recorded in
`volatility.json`. If m_total < σ_V²/s_A² for any phase (an x-multiplier below 0), that phase's multiplier
floors at m_x = the value whose realised total ratio is closest, and the shortfall is reported.

---

## 6. E3.4 — how the regime enters the variance (REG-6)

**The rule is REG-6's, restated without change:** run all three mechanisms; adopt the one whose generator-side
median **rise time** and **decay half-life** (measured with §5.2's exact estimator on generated crash paths)
both fall inside the empirical 95 % CIs of §5.2; if two qualify, the one with fewer free parameters
(A < B < C, the register's own ordering); if none does, report all three against the CIs and keep A as the
documented shortfall. **Never only the expected winner.** 200 crash seeds (δ = 0.70, VM block) per mechanism,
plus 200 flat seeds for the unconditional-sd verification (V4) and the calm-mapping sensitivity of §3.4.
Generator-side onset/rise/decay use the path's own pre-event days as the calm reference (all days before the
scripted event start; ≥ 30 required — the panel's 120-day window does not fit before a day-50 event start, and
the report states this estimator difference).

The mechanisms, all carrying §5.3's FIT multipliers and §3's adopted shape and scale:

- **A — whole-variance scaling** (v2, amendment A3): σ²ₜ = m(phaseₜ)·hₜ with the GJR recursion on the
  phase-normalised hₜ (the incumbent `scale_mode="variance"`), multipliers FIT.
- **B — ω-scaling with a FIT ramp**: ωₜ = m_ω(phaseₜ)·ω_base with m_ω ramping linearly over L_ramp days after
  each phase change (and back on exit); L_ramp FIT by grid search over {0, 5, 10, 20, 40} d minimising the
  absolute distance of the generator's median **rise time** to the empirical median (decay is then judged
  out-of-fit). At the adopted persistence 0.991 the ω route converges with a ≈ 77-day variance half-life; A3
  rejected it at persistence 0.98 for exactly this reason — the arm runs anyway, as the register requires.
- **C — fitted two-regime switching variance**: σ²ₜ = v(Rₜ)·hₜ with Rₜ ∈ {calm, stress} a Markov chain;
  v(stress)/v(calm) = m_panic (FIT §5.1); exit probability p₁₀ = 1/D̄ with D̄ = §5.2's median stress-spell
  duration (FIT); phase-conditional entry probabilities derived so the stationary expected multiplier in each
  scripted phase equals that phase's FIT m_total: p₀₁(phase) = p₁₀·s/(1−s) with s = (m_phase−1)/(m_stress−1),
  capped at 1 (panic hits the cap by construction); baseline (calm) entry from the panel's unconditional stress
  share (§5.2). The scripted phase sets **only** these probabilities; the regime draw is stochastic per day
  (a new named RNG stream, appended to the registry).

Everything is kept as an engine option behind `GJRParams.scale_mode` regardless of the outcome, as v2 did with
`omega`. The winner is re-measured once on the final applied state (the §9 refit moves σ_V and sbar slightly);
if its statistics leave the empirical CIs on the final state, that is reported and the decision re-examined in
an addendum step, not silently kept.

---

## 7. E3.5 — implied volatility without a step or a look-ahead

### 7.1 Construction (the plan's, made concrete)

    IV_t = √(252 · σ̂²_{t+1..t+21}) · (1 + π_t) · exp(ε_t)

- **σ̂²** — a GJR-GARCH(1,1) filter with **fixed** parameters (the adopted α, γ, β; ω from the §3.4 identity's
  unconditional total-return variance) run on the **observed daily log returns of P only** (burn-in included, so
  the filter is warm at day 1), forecast as the mean conditional variance over the next 21 days iterated at the
  filter's own persistence — **no phase input, no multiplier, no generator state**. Past-only by construction.
- **π_t** — FIT on the five CBOE single-stock VIX histories (VXAPL, VXAZN, VXGOG, VXGS, VXIBM; daily closes
  2011-01-07…2024-12-31, clipped to the price panel; underlying returns AAPL, AMZN, GOOG, GS, IBM from
  `datasets/01_prices`) against the same filter run on each name's returns (per-name ω from that name's sample
  unconditional variance; shape fixed at the adopted α, γ, β). π is a function of the **relative** variance
  level ℓ_t = σ̂²_{t+1..t+21}/σ̄² (the filter's forecast over its own unconditional level — scale-free, so the
  mapping transfers to the generator). Family, fixed: M0 log(1+π) = a; M1 = a + b·log ℓ; M2 = a + b·log ℓ +
  c·(log ℓ)². **Selection: leave-one-name-out CV** on the pooled regression of log IV − log √(252σ̂²_fc); adopt
  the smallest-CV family unless a smaller family is within one CV-SE (the 1-SE rule). Per-name coefficients are
  reported beside the pooled fit (mega-cap caveat stated; Carr & Wu and Christensen & Prabhala quoted beside).
- **ε_t** — the residual of the adopted regression: an AR(1) with ρ_ε and innovation sd FIT from the pooled
  residuals (per-name AR(1), median; adopt AR(1) iff the median ρ_ε's 95 % stock-bootstrap interval excludes 0,
  else iid). Drawn in the generator from a new named RNG stream (`"iv"`, appended to the registry — append-only,
  so no existing path changes), one draw per day, so IV_t's noise at day t never depends on later days.
- **Removed:** the `IV_PREMIUM_STRESS` decile trigger and the whole-path quantile (the look-ahead), the
  `sigma_V²` add-on and the `w²` factor (the filter sees total returns), and the CAL floor of 12 — the pooled
  minimum of the five CBOE histories is printed beside the generator's realised minimum as the check instead.

### 7.2 Pre-registered checks

1. **No look-ahead (code test, 20 seeds NLA):** recompute the IV field after altering the return path strictly
   after day t₀ (+1 % to every later return), same ε stream: IV on days ≤ t₀ must be **bit-identical**; repeated
   at t₀ ∈ {40, 100, 160}. This is `test_iv_no_lookahead` and it is written **before** the construction is wired
   into the generator.
2. **Onset detection in REG-6's corrected form (200 crash seeds IVA):** per day, score_IV = |Δlog IV_t| and
   score_ref = |Δlog √(252σ̂²_fc,t)| — the same filter's forecast, the legitimate-information yardstick; label 1
   on days [τ, τ+5) for the deterioration→panic transition τ, 0 on calm days. ΔAUC = AUC(IV) − AUC(ref) must
   not exceed the 95th percentile of a 500-draw circular-shift permutation null (per-path label shifts of
   U(10, T−10) days, rng 221001). Same for the calm→deterioration transition, reported.
3. **The continuity tolerance, derived not chosen:** on the same 200 IVA seeds, per seed and transition
   (deterioration→panic, panic→stabilisation): z = Δlog IV at the transition day ÷ the calm day-to-day sd of
   Δlog IV. The reference distribution is the same z computed on the filter forecast √(252σ̂²_fc). The tolerance
   is **T_z = the 95th percentile over seeds of the reference z**, per transition, written into
   `volatility.json` with its n. `test_iv_continuity` is then flipped **hard**: on the existing SIV30 fixture
   (crash seeds 17000–17029), |mean z_IV| ≤ T_z at both transitions. The derivation run's own z_IV distribution
   is published with it (the test must pass because the construction is leak-free, not because the tolerance is
   generous; if mean z_IV at 200 seeds exceeds T_z the construction is re-examined **before** the tolerance is
   ever adjusted, and any change goes through the addendum).

### 7.3 What is reported

Levels: generator calm/panic IV vs the five names' IV distributions (checklist item 13 is re-scored on the
after-state; its 25–35 / 60–100 bands are v2 CAL and Phase 6 re-derives them — reported, not gated here). The
IV–RV(realised, next 21 d) correlation and gap. L2b is expected to move (IV was the clearest phase marker) and
the after-state audit's number is handed to Phase 6.

---

## 8. E3.6 — item 73 (GARCH persistence on regime paths)

Checklist item 5's statistic (fitted α + β on path returns) computed two ways on the after-state checklist
panels: (a) **calm windows only** — maximal contiguous calm runs ≥ 100 days, fitted per run and pooled
(medians); (b) the **whole path**, as the checklist computes it. Both reported with n; no new pass rule (item 5's
[0.90, 0.995] band stays the checklist's).

---

## 9. The engine-refit question (decided and pre-registered here, before any fit)

**Decision: option (a′) — one re-launch of Phase 2's SMM on the adopted volatility block, for the adopted engine
only, with the volatility scale owned by Phase 3 rather than left free.**

- **Simulator** = `tools/phase2/engines.py` extended behind opt-in parameters (defaults preserve Phase 2's
  reference row bit-for-bit, guarded by `test_smm_reference_row`): GARCH shape = the adopted (α, γ, β, ν);
  jumps ON at E3.2's (λ, σ_J), mean-zero, as the generator runs them; **sbar eliminated as a free parameter by
  §3.4's identity**, recomputed at every (σ_V, h) evaluation (σ_V ≥ s_A returns a penalty J). **Free: (σ_V, h).**
- Everything else is Phase 2's registered design unchanged: the 17 moments, the stored weight matrix
  (`e2_3/weight_full.npy`), 200 CRN paths × 5,000 d per evaluation (seeds SM3), K = 20 reported replicates, DE
  (popsize ≥ 8p) + Nelder–Mead polish with the named-start grid restricted to its (σ_V, h) members plus the
  Phase-2 optimum, **30 bootstrap refits** (SB3) for intervals, both acceptance criteria (χ² at df = 15;
  FW bootstrap p at C = 200, seeds MC3) — reported, with no expectation of acceptance (Phase 2's J was 80.4 and
  the model class has not changed).
- **Sensitivity (reported, not adopted):** the same cell with (σ_V, sbar, h) free — Phase 2's exact
  parameterisation under the new block — so the reader sees what the SMM would still choose for sbar when free,
  and the Phase-2 → Phase-3 movement of each parameter is attributable (shape effect vs constraint effect).
- **Adopted:** the constrained fit's (σ_V\*, h\*) with refit intervals → `value.json` σ_V (label: FIT,
  conditional on the engine **and on the Phase-3 volatility block**, superseding P2-16's "expected to move
  again"); `mispricing.json` structural + half_life updated with the same conditionality; sbar\* = identity at
  (σ_V\*, ρ\*) → `volatility.json`. The engine's identity (`ar1_fit`, E2.4's decision) is **not** re-opened —
  re-contesting FW belongs to a WRDS re-run under D1 = C, and E2.4's asymmetric rule inputs (held-out dead heat,
  the switching that turns itself off) did not depend on the shape.
- **The known defect closes:** `test_garch_shape_matches_e3_1` ends the phase **passing** — the generator's
  shape equals the fitted block. If E3.2 adopts a mixture ν ≠ 4.86, the test's assertion is updated to check
  (α, γ, β) against E3.1's medians and ν against `volatility.json`'s FIT value with its provenance — an
  evidence-based strengthening logged in the report's test-edit table (the Phase-2 pattern), not a silent move.
- **Order**: the refit runs **after** E3.2 (it needs ν, λ, σ_J) and **before** E3.4/E3.5 (which run on the
  final engine), so no mechanism or IV conclusion is conditional on a stale σ_V.

---

## 10. Power and decidability (runnable: `tools/phase3/prereg_power.py`; results in `generated/v2_1/e3_0/power.json`)

Rows marked *measured* are filled by the script **before** the experiment each protects; this table is then
updated in place with the numbers and the file is not edited afterwards. (Phases 1 and 2 each lost a re-run to a
criterion whose null spread was never simulated; every rule below is checked the same way.)

| # | Criterion it protects | What is simulated / computed | Result | Consequence if the check fails |
|---|---|---|---|---|
| **PA1** | §4.3 recovery gate | the recovery grid itself (6 cells × 5 replicates, QML refits included) | *measured (e3_2/recovery.json)*: ν ±2.4 %, λ ±59 %, σ_J ±28 % → **not usable** under the 0.20 rule; the λ = 0 cell clean 5/5 | the registered fallback ran and is **degenerate** (λ → 3·10⁻¹⁴ at ν pinned 4.86); adoption corrected in ADDENDUM §3 with both arms reported |
| **PA2** | §4.2's excess-rate lower bound is decidable | the λ = 0 recovery cell's spread vs the real panel's excess CI | *measured (e3_0/power.json)*: on jump-free panels the mixture-λ **point** can spuriously reach 0.009 (2/5 replicates; CI includes 0 in 5/5); the real panel's excess CI [+0.00060, +0.00089] excludes 0 | the λ > 0 claim rests on the excess-rate CI and the announcement clustering, never on the point estimate alone — stated in the report |
| **PA3** | §6's rule can separate the mechanisms | generator pilot, 30 crash seeds on the incumbent: cross-seed sd of median rise time and decay half-life at n = 200 | *measured (e3_0/power.json)*: rise sd 37.1 d → median 95 % half-width **±6.4 d** at n = 200; decay sd 5.3 d → **±0.9 d**; 28/30 qualify; realised panic ratio 2.41 on the incumbent | if the generator-side 95 % half-width exceeds the empirical CI width, the mechanism verdict is undecidable and is reported so |
| **PA4** | §5.2's empirical CIs are usable | stock-bootstrap CI width on the median rise time at the achieved episode count (REG-6's own power note: ± ≈ 4 d at n ≥ 60) | *measured (e3_0/power.json)*: pooled n = 1,585, rise CI [107, 131]; fast-crash (ADDENDUM 2) n = 531, rise CI [29, 35] (±3 d), decay [9, 10] — both ≥ 60, and the CI widths are of the same order as PA3's generator precision, so the rule is decidable | if n < 60 or the CI spans all three mechanisms' predictions, the §6 verdict is undecidable and says so |
| **PA5** | §7.2(2)'s permutation null | the null is computed inside the audit (500 shifts); its P95 and the AUC SE at 200 seeds are reported | *measured (e3_5/audit.json)*: null P95 +0.032; AUC(ref) = 0.683 ≫ 0.5, so the comparison is not vacuous; ΔAUC −0.107 | if AUC(ref) itself is at chance (no legitimate signal), the comparison is vacuous and reported as such |
| **PA6** | §7.2(3)'s hard test at 30 seeds | SE of mean z_IV over the 30 SIV30 seeds vs T_z (from the 200-seed derivation run) | *measured*: the 200-seed per-seed z_IV sd ≈ 1.1 ⇒ SE of a 30-seed mean ≈ 0.20 ≪ T_z/2 (1.35 / 1.14 / 0.94) — decidable with a wide margin | if SE(mean z_IV) > T_z/2 the test cannot decide and the tolerance derivation is widened to more seeds in an addendum before the flip |
| **PA7** | §9's constrained fit is identified | 11-point J profiles in σ_V and h at the constrained optimum (CRN fixed), plus a 5-point σ_V slice before launch | *measured*: h has a clean interior minimum (J 116 at 22.4, rising to 139 at 14.1 and 139 at 35.5); σ_V is identified steeply from below (J 334 at 0.0092 → 116 at 0.0146) and bounded above by the identity's feasibility edge (σ_V ≥ ~0.021 makes sbar² < 0), with the refit CI [0.01275, 0.01527] interior to the feasible region | a flat profile ⇒ the parameter is reported as not identified with its interval widened to the profile's flat region |

---

## 11. Parameter file, tests, freeze

**`envs/v2/params/volatility.json`** (new), every entry `value / label / source / date / interval / n /
survivor_vs_literature_gap` plus **what the fit is conditional on** (the P2-16 discipline), following
`mispricing.json`'s pattern: `garch_shape` (α, γ, β FIT E3.1; ν FIT E3.2 or fallback), `shape_sensitivity_sets`
(P25/P75, §3.2's construction), `sbar` (FIT, §3.4's identity with inputs and MC interval), `jumps` (λ, σ_J FIT;
placement, q, p_ann, lam_res carried/derived), `phase_multipliers` (FIT medians with CIs, the m_x mapping and
realised-ratio verification), `mechanism` (E3.4's decision with all three arms' statistics), `iv` (filter spec,
premium family and coefficients, ρ_ε, sd_ε, the T_z tolerances, the CBOE minimum anchor), `item73` (both
persistence numbers). Loader `envs/v2/volatility_params.py`, **loud like `value_params.py`** (missing file
raises; `garch.py`'s defaults read from it). Every generator change is a switch with the v2 behaviour behind it
(the Phase-1/2 convention): legacy constants stay available under `scale_mode`/explicit config for the stored
sensitivities.

**Tests** (`tests/test_v2_1_phase_3.py` + edits logged in the report): `test_garch_params_in_force` (running
GJRParams == `volatility.json`, provenance present); `test_iv_no_lookahead` (§7.2(1), 20 seeds);
`test_iv_continuity` flipped **hard** with T_z (§7.2(3)) and its registry entry removed; `test_jump_process`
(realised jump rate and mean |size| within the FIT intervals at 500 seeds, seeds JP); `test_smm_reference_row`
untouched and green (the extension is opt-in); `test_flat_x_equivalence` re-verified at the new block;
`test_garch_shape_matches_e3_1` ends the phase passing (§9), its `known_defects.py` entry removed.

**Freeze and hand-over (execution-order rule, paid in full).** Applying the block changes every path:
`path_hashes_phase3_after.json` (95 configurations), the Section-9 checklist at 200 seeds on SCL, the SEP
level-free audit (1,600 paths, local reference machine only), `tools/freeze_manifest --write` label
"v2.1 Phase 3 freeze" — all via `tools/phase2/after_state.py`'s stages pointed at Phase-3 outputs. Then the two
Phase-2 diagnostics on the handed-over state: **E3.7** = `e2_7_discrimination.py` re-run (the panic multiplier
and jump size move sd(x) and coverage; MCR-undefined shares re-measured) and **E3.8** = `e2_8_bound_check.py`
extended to the block decomposition — the exact process, + GJR-t innovation, + jumps, + both, at the parameters
in force — attributing the +0.10 level-free channel Phase 2 measured, handed to Phase 6.

---

## 12. Order of execution

1. `prereg_power` PA3 pilot (30 seeds, incumbent state) and the §9 pre-launch slice — the two *measured* rows
   that can run before any panel work.
2. E3.1 confirmation (V1–V3, V5) — minutes.
3. E3.2 recovery grid (PA1/PA2; local or Kaggle after the reference-row check) → panel detection → adoption fit.
4. E3.3 episodes (panel only; parallel with 3) → multipliers, rise/decay CIs, PA4.
5. §9 engine refit (constrained + unconstrained sensitivity + 30 refits; the phase's compute bulk, ~4–8 h local
   at 3 workers) → (σ_V\*, h\*, sbar\*); V4, V6, V7.
6. E3.4 mechanisms on the refitted engine (3 × 200 crash + 200 flat seeds) → decision by REG-6's rule.
7. E3.5: CBOE premium fit → construction wired behind a switch → no-look-ahead test → onset audit → T_z.
8. E3.6 on the after-state panels.
9. `apply_e3` writes the parameter files; tests; after-state (hashes, checklist, SEP audit ≈ 2 h, freeze);
   E3.7 + E3.8; DECISION_LOG P3-\*; `PHASE_3_CHANGED_FILES.md`; `PHASE_3_REPORT.md`. Stop — Phase 4 is not begun.

## 13. What is reported if a rule is not met

- E3.2: an unusable estimator is reported unusable with the recovery table; the fallback's double-count is
  stated with direction; a λ interval containing 0 is published as such (the generator then carries the point
  estimate with the interval, not a rounded-up rate).
- E3.3: achieved episode counts, censored shares and every exclusion, not intended ones.
- E3.4: if no mechanism lands both statistics inside the CIs, all three are tabled against them and A stays with
  the shortfall documented (REG-6's own consequence); an undecidable verdict (PA3/PA4) is *undecided*, not
  resolved by preference.
- E3.5: if the onset audit fails (ΔAUC above the null P95), the IV construction is reported as still leaking,
  the failing statistic published, and the field is **not** claimed fixed — items 46/25 stay registered with the
  new evidence.
- §9: an unaccepted fit is reported unaccepted with J, df, both criteria; no moment is dropped and no weight
  matrix changed.
- Compute shortfalls never shrink a pre-registered sample silently: the reduced design is fixed in the addendum
  before the run, achieved counts are stated, undecidable verdicts stay undecided.

## 14. Not done in Phase 3 (owner), and what would differ under the open §5.1 decision

Item 13's checklist re-gating and the calm-sd band (Phase 6); the L2/L2b gates and reference distributions
(Phase 6; E3.5 is the field most likely to move L2b and the after-state number is handed over); the bull-trap
rejection rate 0.94 (Phase 4 — Phase 3 runs on it as handed over; if E3.3's multipliers move sd(x) materially,
the realised rejection rate is re-reported for Phase 4's information); MCR-undefined runs (Phase 7; re-measured
in E3.7); θ, bands, regret (Phase 7); the LLM grid on the P25/P75 sensitivity sets (Phase 9); the WRDS re-fit
(D1 = C). **If the team later chooses v2's environment or a factor design at §5.1**, the values that would
differ here are the ones conditional on (σ_V, h): the §3.4 identity's sbar, §5.3's m_x mapping, §9's outputs and
the E3.8 bound rows — the FIT shape, jumps, multipliers (as total-return ratios) and the E3.5 premium are
panel-side and carry over unchanged.
