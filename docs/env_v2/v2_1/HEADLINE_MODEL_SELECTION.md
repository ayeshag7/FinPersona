# Which open-weight models carry E2–E8: a selection from the stage-1 headline

*Written 28 Oct 2026 from the 26,352 verified stage-1 runs of the nine open-weight models. This is analysis only: no
model was called and no cluster job ran. Every number cites a table in `docs/env_v2/generated/v2_1/e9_4/selection/`
and carries its n. Nothing is committed.*

**Status: complete for the question it answers.**

- **The rule came first.** It is `selection/CRITERIA.md` (sha256 `b47e7dea…08c11c`), written at 09:05 UTC before
  any behaviour statistic was computed. `tools/phase9/e9_4_select.py` implements it and stamps that hash into
  `selection.json`. Section 7 lists every change made after the rule was frozen.
- **No earlier Phase 9 reasoning is used.** No pilot prediction, pilot sizing or roster argument (lab, size,
  licence) enters the choice.
- **This is not the registered confirmatory read.** That read (each model's own family of 36, BH within family,
  `PREREG_PHASE_9_STAGE1_OPEN.md` 3) has not been run, and nothing here is a claim about any model.

---

## 0. The answer

**The core for E2–E5 is six models:** Gemma 4 E4B, gpt-oss-20b, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B and
Phi-4. E6–E8 take subsets of it, and E2 and E3 take one top-up.

GPU-hours are for the models each experiment is assigned, measured per run in stage 1 (§3.6), at three seed counts:

- S = 60, the plan's count;
- each model at its own implied S, never below 60;
- one common implied S, here 246.

| Experiment | Models | GPU-hours: S 60 / own S / common S 246 |
|---|---|---|
| E2 causal package | Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B, Phi-4, and **Gemma 4 31B** as top-up | 17.6 / 25.8 / 72.3 |
| E3 common-start slice | as E2 | 39.2 / 57.3 / 160.7 |
| E4 Track A | the core | 18.8 / 38.8 / 77.0 |
| E5 parameter sensitivity | the core | 225.2 / 466.1 / 923.4 |
| **E2–E5** | seven models served | **300.8 / 588.0 / 1,233.4** |
| E6 context length | **Llama 3.1 8B only**: 3 of the plan's 4 places are open, see the note below | not priced: needs the stateful pilot the plan already requires |
| E7 OCEAN | Gemma 4 E4B, Ministral 3 14B, Llama 3.1 8B | 2.5 / 6.1 / 10.1 |
| E8 k-sweep | Gemma 4 E4B, Ministral 3 14B, Llama 3.1 8B | not priced ("small" in the plan) |

E6 can grow to four models. If config files at the pinned revisions show windows that hold their full-level needs
(64.5k–66.2k tokens), Gemma 4 E4B, OLMo 3.1 32B and Ministral 3 14B join Llama 3.1 8B. Reading those files is a file
read, not a model call.

All nine models in all four experiments would cost **964 / 1,618 / 3,954** GPU-hours on the same three bases
(`subset_costs.csv`). Sources: `assignment_costs.csv`, `assignments.csv`.

**Why these six.**

- All nine pass the usability gates (§4.1).
- No two models are duplicates at n = 122. The closest pair sits 2.8 times above its noise floor (§3.8).
- Each of the three excluded models has its nearest neighbour inside the core:
  - Gemma 4 31B and Muse Glimmer 30B are nearest gpt-oss-20b;
  - Llama 3.1 70B is nearest Phi-4.
- The three excluded models are also the three most expensive per run: 0.0056, 0.0172 and 0.0076 GPU-hours,
  against 0.0009–0.0037 for the six.
- The choice is stable:
  - 200 of 200 path-bootstrap draws choose the same six;
  - so does the mean-excess objective;
  - the only tie at six swaps Phi-4 for Llama 3.1 70B, and the rule takes the cheaper one (§4.4).

**The principal alternative.** At the stricter usability gate (G3 = 0.25), Gemma 4 E4B is ineligible and **Gemma 4
31B takes its seat**. That core costs 394 rather than 289 GPU-hours at S = 60. It keeps the sign pattern of all nine
better, and it drops the core's most degenerate model (§4.5, §5).

**Three things the data cannot decide; the team must.**

- **The seed count.** Under the registered Δ = 0.05 and α′ = 0.05/36, two core models drive S to 246:
  - Ministral 3 14B, through its ENTJ-crash cell;
  - gpt-oss-20b, through its ENTJ-sustained-bull cell.

  At the plan's 60 seeds, their band-MAS MDD in those cells is 0.093 and 0.088 (§3.5).
- **gpt-oss-20b's place in E2 and E3.** The rule drops it because its *pooled* effect is null. That null comes from
  opposite-signed cells cancelling: 7 of its 12 cells exclude 0. On a cell reading it would carry E2 and E3 itself
  (§3.3).
- **E6.** It is short of models until three native windows are read (§3.7).

---

## 1. The rule, fixed before the results

`selection/CRITERIA.md` is the full rule. In brief:

**What each experiment needs** (`GRID_EXPERIMENT_PLAN.md` §3):

| Experiment | Needs a model with |
|---|---|
| E2 | an effect to decompose |
| E3 | personas that separate, and an effect |
| E4 | static-arm band-MAS of at least Δ = 0.05, so stating the band has something to fix |
| E5 | decisions that respond to what the model observes |
| E6 | a window and a KV cache that hold the long levels, and an effect that could decay |
| E7 | persona text that moves behaviour |
| E8 | an effect to sweep |

**Gates.** A model carries nothing if:

- G1: a run is missing or unverified;
- G2: its parse-fallback share exceeds 0.01 in any cell;
- G3: more than half of its runs are constant-target or zero-trade.

G2's and G3's thresholds are DESIGN, with their sensitivity reported.

**The core.** It is chosen by coverage, not by any outcome.

- A model's behaviour profile is 54 numbers, all in cash-share units:
  - the 24 cell means of run-mean cash share;
  - the 12 persona × scenario memory − static effects on band-MAS;
  - the 12 effects on D at θ 0.05;
  - the 6 persona × arm market amplitudes.
- The distance between two models is the mean over those four blocks of each block's RMS difference.
- Each model has a noise floor. It is the 95th percentile, over 100 random half-splits of its 122 seeds, of the
  distance between its two halves, divided by √2. That is the distance two independent 122-seed estimates of the same
  model would show.
- The coverage loss of a subset is the largest amount by which any of the nine lies beyond the noise of its nearest
  member.
- The core is the size-6 subset with the smallest loss. Subsets within δ of the best are tied, where δ is the median
  floor, 0.0083. Ties go to the lowest E2–E5 GPU-hours at the subset's implied S.
- The size is the plan's 6, unless dropping to 5 loses no more than δ.

**Experiment requirements.** These prune the core per experiment; they never choose it:

- R_effect: the pooled band-MAS memory − static CI excludes 0;
- R_persona: the static separation CI lies above 0;
- R_headroom: static band-MAS ≥ 0.05 for at least one persona;
- R_market: decisions beat a circular-shift null;
- R_context: the window and KV cache hold the four E6 levels.

E6–E8 take the plan's 4, 3 and 3 from the core members that meet their requirement, by coverage of the core.

**Not used.**

- Effect size as a ranking: it would carry a winner's curse into every later estimate.
- Fidelity level, except E4's headroom: fidelity is the object of study.
- Anything from the pilots or the roster's reasoning.

---

## 2. The data

| Item | Value | n |
|---|---|---|
| Runs | 9 models × 3 personas × 2 arms × 4 scenarios × seeds 10001–10122 | 26,352 (2,928 per model) |
| Verification | every run present and matching its manifest (`e9_4/verify.json`) | 2,928 / 2,928 per model, 0 mismatched |
| Ledgers | one row per run, every one `ok` | 2,928 rows per model (`cost.csv`) |
| Shared market paths | every scenario × seed path has one `Gen_Config_Hash` and one price series across all 54 runs on it | 488 of 488 paths (`shared_paths.csv`) |
| Undefined D at θ 0.05 | no day reaches \|x\| ≥ 0.05 on flat and sustained_bull at seed 10107, so `score_run` leaves D undefined there by design | 2 of 488 paths; those cells use 121 pairs, and pooled D θ 0.05 uses 1,458 pairs on 486 paths |

---

## 3. The measurements

### 3.1 Usability (U)

Each model made 585,600 decisions on 2,928 runs. Each cell (model × persona × arm × scenario) holds 122 runs and
24,400 decisions. Source: `usability.csv`.

| model | fallbacks | largest cell fallback share | retried decisions | zero-trade runs (share) | largest cell | constant-target runs (share) | largest cell | median distinct targets per run |
|---|---|---|---|---|---|---|---|---|
| Gemma 4 31B | 38 | 0.00037 | 141 | 0 (0.000) | 0.000 | 0 (0.000) | 0.000 | 61.8 |
| Gemma 4 E4B | 0 | 0 | 1 | 0 (0.000) | 0.000 | 928 (0.317) | 1.000 | 3.0 |
| gpt-oss-20b | 0 | 0 | 29 | 0 (0.000) | 0.000 | 1 (0.000) | 0.008 | 31.5 |
| Muse Glimmer 30B | 2 | 0.00004 | 371 | 0 (0.000) | 0.000 | 8 (0.003) | 0.008 | 37.5 |
| OLMo 3.1 32B | 0 | 0 | 0 | 0 (0.000) | 0.000 | 219 (0.075) | 0.475 | 7.8 |
| Ministral 3 14B | 0 | 0 | 106 | 0 (0.000) | 0.000 | 203 (0.069) | 0.639 | 9.0 |
| Llama 3.1 8B | 0 | 0 | 144 | 0 (0.000) | 0.000 | 0 (0.000) | 0.000 | 19.0 |
| Llama 3.1 70B | 0 | 0 | 0 | 182 (0.062) | 0.443 | 177 (0.060) | 0.516 | 19.0 |
| Phi-4 | 0 | 0 | 62 | 0 (0.000) | 0.000 | 23 (0.008) | 0.082 | 9.0 |

**Fallbacks are negligible.** Gemma 4 31B's 38 and Muse Glimmer's 2 are at most 0.00037 of any cell's decisions.

**Two kinds of stuck policy appear, in different models.**

- **Constant target.** The model states one cash share all run. This concentrates in the ENTJ memory cells:
  - Gemma 4 E4B: 122 of 122 runs in every ENTJ-memory cell, all fully invested. Its INTJ-memory cells are 0.62–0.73
    constant.
  - OLMo 3.1 32B: 0.43–0.48 of ENTJ-memory runs.
  - Ministral 3 14B: 0.25–0.64 of ENTJ-memory runs in flat, bull_trap and sustained_bull.
  - Llama 3.1 70B: 0.16–0.52 of ENTJ-memory runs.
- **No trade at all.** Only Llama 3.1 70B does this, in its ISFJ-static cells (0.25–0.44 of runs). It restates its
  drifting cash share every day: a median of 125–132 distinct targets per run, by cell, and not one trade.

The static arm's mean cash share is the pre-registered precondition, pooled over scenarios with 488 runs per entry:

| model | ISFJ | INTJ | ENTJ |
|---|---|---|---|
| Gemma 4 31B | 0.850 | 0.482 | 0.348 |
| Gemma 4 E4B | 0.882 | 0.017 | 0.041 |
| gpt-oss-20b | 0.940 | 0.559 | 0.509 |
| Muse Glimmer 30B | 0.984 | 0.645 | 0.607 |
| OLMo 3.1 32B | 0.971 | 0.289 | 0.146 |
| Ministral 3 14B | 0.977 | 0.888 | 0.161 |
| Llama 3.1 8B | 0.868 | 0.741 | 0.629 |
| Llama 3.1 70B | 0.806 | 0.620 | 0.517 |
| Phi-4 | 0.966 | 0.699 | 0.568 |

### 3.2 Persona fidelity and separation (P)

The separation ratio is (ISFJ − ENTJ mean cash share) / 0.70, the distance between the conservative and aggressive
band centres. Its 95 % CI comes from a 1,999-draw bootstrap over 488 paths. The ordered share is the share of the 488
paths with ISFJ > INTJ > ENTJ; with no persona effect it would be about 1/6. Band-MAS is pooled over 488 runs per
persona, and in-band days over 97,600. Source: `persona.csv`.

| model | separation, static | separation, memory | ordered, static / memory | static band-MAS ISFJ / INTJ / ENTJ | static in-band days ISFJ / INTJ / ENTJ |
|---|---|---|---|---|---|
| Gemma 4 31B | 0.72 [0.71, 0.73] | 0.79 [0.77, 0.81] | 0.748 / 0.559 | 0.025 / 0.224 / 0.192 | 0.53 / 0.08 / 0.47 |
| Gemma 4 E4B | 1.20 [1.18, 1.22] | 1.43 [1.43, 1.43] | 0.115 / 0.316 | 0.082 / 0.383 / 0.000 | 0.19 / 0.00 / 1.00 |
| gpt-oss-20b | 0.62 [0.59, 0.64] | 0.82 [0.79, 0.84] | 0.715 / 0.684 | 0.061 / 0.261 / 0.346 | 0.18 / 0.09 / 0.33 |
| Muse Glimmer 30B | 0.54 [0.52, 0.56] | 0.75 [0.72, 0.77] | 0.629 / 0.895 | 0.085 / 0.268 / 0.424 | 0.04 / 0.09 / 0.18 |
| OLMo 3.1 32B | 1.18 [1.17, 1.18] | 1.42 [1.42, 1.42] | 1.000 / 1.000 | 0.074 / 0.113 / 0.011 | 0.04 / 0.02 / 0.88 |
| Ministral 3 14B | 1.17 [1.14, 1.19] | 1.39 [1.38, 1.39] | 0.838 / 0.967 | 0.079 / 0.338 / 0.117 | 0.04 / 0.06 / 0.80 |
| Llama 3.1 8B | 0.34 [0.33, 0.35] | 0.99 [0.97, 1.00] | 0.969 / 0.982 | 0.029 / 0.165 / 0.432 | 0.49 / 0.17 / 0.02 |
| Llama 3.1 70B | 0.41 [0.40, 0.42] | 1.26 [1.26, 1.27] | 0.932 / 0.998 | 0.002 / 0.066 / 0.328 | 0.94 / 0.45 / 0.15 |
| Phi-4 | 0.57 [0.56, 0.58] | 1.34 [1.34, 1.35] | 1.000 / 1.000 | 0.067 / 0.135 / 0.372 | 0.06 / 0.39 / 0.12 |

**Every model separates ISFJ from ENTJ in the static arm**, and every CI lies above 0.

**The models fall into two groups.**

- **Over-separators** (Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B) push the personas to the extremes of the scale.
  Their ratios of 1.17–1.20 exceed the band-centre distance itself.
- **Under-separators** (Llama 3.1 8B and 70B) sit close together under persona text alone, at 0.34 and 0.41. The
  re-injected mandate is what separates them, at 0.99 and 1.26.

**Gemma 4 E4B orders INTJ below ENTJ** (0.017 against 0.041 mean cash share), so its ordered share is 0.115 in the
static arm.

### 3.3 The memory − static effect, paired on seed (E)

The difference is memory − static on the same persona, scenario and seed. Each model has:

- 1,464 pairs on 488 paths pooled (1,458 on 486 for D at θ 0.05);
- 122 pairs per cell.

CIs come from `stats_v2.pigeonhole_ci`: with one model, a one-way path bootstrap of 1,999 draws, seed 0. A negative
band-MAS or D value means the memory arm is closer to the mandate. Sources: `effects_pooled.csv`,
`effects_cells.csv`.

| model | band-MAS | cells − / + of 12 | D, θ 0.05 | cells − / + of 12 | D, θ 0.002 | mean cash share |
|---|---|---|---|---|---|---|
| Gemma 4 31B | +0.0394 [+0.0360, +0.0429] | 0 / 11 | +0.0076 [+0.0062, +0.0089] | 3 / 6 | +0.0046 [+0.0037, +0.0055] | +0.0189 [+0.0151, +0.0228] |
| Gemma 4 E4B | +0.0115 [+0.0091, +0.0137] | 4 / 6 | −0.0008 [−0.0021, +0.0006] | 3 / 1 | −0.0000 [−0.0009, +0.0009] | +0.0198 [+0.0158, +0.0239] |
| gpt-oss-20b | **+0.0028 [−0.0028, +0.0083]** | 2 / 5 | +0.0119 [+0.0100, +0.0138] | 1 / 3 | +0.0081 [+0.0068, +0.0095] | −0.0132 [−0.0204, −0.0060] |
| Muse Glimmer 30B | −0.0059 [−0.0102, −0.0019] | 2 / 8 | +0.0191 [+0.0172, +0.0211] | 2 / 6 | +0.0129 [+0.0114, +0.0143] | +0.0031 [−0.0044, +0.0103] |
| OLMo 3.1 32B | −0.0005 [−0.0010, −0.0000] | 8 / 4 | −0.0021 [−0.0046, +0.0005] | 3 / 3 | +0.0007 [−0.0009, +0.0025] | −0.0314 [−0.0322, −0.0306] |
| Ministral 3 14B | −0.0175 [−0.0222, −0.0130] | 4 / 8 | −0.0009 [−0.0030, +0.0014] | 2 / 3 | −0.0001 [−0.0016, +0.0014] | −0.0714 [−0.0800, −0.0628] |
| Llama 3.1 8B | −0.0761 [−0.0791, −0.0730] | 8 / 4 | +0.0081 [+0.0056, +0.0106] | 4 / 5 | +0.0069 [+0.0052, +0.0087] | −0.1308 [−0.1347, −0.1269] |
| Llama 3.1 70B | −0.0990 [−0.1017, −0.0964] | 5 / 6 | −0.0072 [−0.0098, −0.0044] | 4 / 2 | −0.0024 [−0.0042, −0.0006] | −0.1383 [−0.1419, −0.1350] |
| Phi-4 | −0.0862 [−0.0886, −0.0839] | 4 / 8 | +0.0040 [+0.0002, +0.0078] | 4 / 1 | +0.0053 [+0.0029, +0.0079] | −0.1468 [−0.1492, −0.1444] |

The band-MAS effect per cell, with 122 pairs each (* = the 95 % CI excludes 0). The scenarios are flat (fl),
bull_trap (bt), crash (cr) and sustained_bull (sb):

| model | ISFJ fl | ISFJ bt | ISFJ cr | ISFJ sb | INTJ fl | INTJ bt | INTJ cr | INTJ sb | ENTJ fl | ENTJ bt | ENTJ cr | ENTJ sb |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gemma 4 31B | +0.018* | +0.017* | +0.025* | +0.015* | +0.020* | +0.015* | +0.035* | +0.009* | +0.107* | +0.041* | +0.164* | +0.009 |
| Gemma 4 E4B | +0.023* | +0.032* | +0.002 | +0.014 | +0.017* | +0.018* | +0.015* | +0.016* | −0.000* | −0.000* | −0.000* | −0.000* |
| gpt-oss-20b | +0.026* | +0.027* | +0.025* | +0.025* | +0.003 | +0.001 | +0.004 | +0.004 | +0.023 | −0.074* | +0.094* | −0.124* |
| Muse Glimmer 30B | +0.012* | +0.013* | +0.012* | +0.012* | +0.016* | +0.008* | +0.040* | +0.004 | −0.005 | −0.086* | +0.027* | −0.122* |
| OLMo 3.1 32B | +0.022* | +0.022* | +0.022* | +0.023* | −0.014* | −0.014* | −0.011* | −0.013* | −0.012* | −0.008* | −0.018* | −0.005* |
| Ministral 3 14B | +0.015* | +0.016* | +0.011* | +0.018* | +0.025* | +0.034* | +0.028* | +0.043* | −0.110* | −0.093* | −0.136* | −0.061* |
| Llama 3.1 8B | +0.044* | +0.046* | +0.044* | +0.052* | −0.038* | −0.027* | −0.036* | −0.035* | −0.221* | −0.283* | −0.147* | −0.311* |
| Llama 3.1 70B | +0.022* | +0.017* | +0.030* | +0.013* | +0.013* | +0.008 | +0.019* | −0.008* | −0.354* | −0.279* | −0.411* | −0.256* |
| Phi-4 | +0.021* | +0.028* | +0.016* | +0.026* | +0.057* | +0.045* | +0.053* | +0.051* | −0.373* | −0.295* | −0.388* | −0.276* |

**The effect's sign depends on the persona.** This is why pooled effects can cancel.

- **ISFJ:** 34 of 36 cells (nine models × four scenarios) are positive with the CI excluding 0. Re-injection raises
  the conservative persona's cash share past the band's 0.90 edge.
- **ENTJ:** 28 of 36 cells are negative. The 5 positive ones are Gemma 4 31B's flat, bull_trap and crash cells, and
  the crash cells of gpt-oss-20b and Muse Glimmer.

**Selection consequences.**

- **gpt-oss-20b fails R_effect by cancellation, not by absence.** Its pooled band-MAS effect is +0.0028
  [−0.0028, +0.0083], yet 7 of its 12 cells exclude 0, from −0.124 to +0.094. The rule, as written, drops it from
  E2, E3, E6 and E8.
- **OLMo 3.1 32B meets R_effect on a pooled −0.0005.** It is low-noise, but its effects are tiny in every cell.
- **Gemma 4 E4B's four "significant" ENTJ cells are about −0.0002** (−0.0001 to −0.0002, 122 pairs each). Both arms
  hold almost always fully invested, so these are intervals on near-constant differences.

### 3.4 Response to the market (M)

**How it is measured.** The decision is the stated target cash share. The control is the pre-trade cash share, which
moves with prices when nothing is traded. The 14 observables are the rendered fields named in CRITERIA M.

- The regression is pooled within run.
- The statistic is the observables' partial R² beyond the control, measured against a null. The null shifts each
  run's observable rows circularly, which keeps every series' autocorrelation (199 shifts).
- The amplitude is the root-mean-square of the variance the observables explain, net of the null, in cash-share units.
- Each arm has 273,898–273,933 days on 1,464 runs.

Source: `market.csv`.

| model | excess partial R², static / memory | null mean partial R² | p | excess amplitude, static / memory | days the target moves ≥ 0.01 |
|---|---|---|---|---|---|
| Gemma 4 31B | 0.2550 / 0.0818 | 0.00006 / 0.00006 | 0.005 / 0.005 | 0.0456 / 0.0268 | 0.59 / 0.26 |
| Gemma 4 E4B | 0.0027 / 0.0007 | 0.00002 / 0.00007 | 0.005 / 0.005 | 0.0016 / 0.0001 | 0.11 / 0.00 |
| gpt-oss-20b | 0.0335 / 0.0281 | 0.00005 / 0.00006 | 0.005 / 0.005 | 0.0120 / 0.0221 | 0.57 / 0.26 |
| Muse Glimmer 30B | 0.0549 / 0.0267 | 0.00006 / 0.00006 | 0.005 / 0.005 | 0.0127 / 0.0173 | 0.50 / 0.16 |
| OLMo 3.1 32B | 0.0448 / 0.0040 | 0.00009 / 0.00006 | 0.005 / 0.005 | 0.0104 / 0.0037 | 0.61 / 0.31 |
| Ministral 3 14B | 0.0092 / 0.0076 | 0.00005 / 0.00012 | 0.005 / 0.005 | 0.0058 / 0.0106 | 0.15 / 0.08 |
| Llama 3.1 8B | 0.0016 / 0.0295 | 0.00005 / 0.00012 | 0.005 / 0.005 | 0.0037 / 0.0351 | 0.31 / 0.30 |
| Llama 3.1 70B | 0.0349 / 0.0133 | 0.00002 / 0.00011 | 0.005 / 0.005 | 0.0072 / 0.0057 | 0.40 / 0.08 |
| Phi-4 | 0.0779 / 0.1006 | 0.00005 / 0.00019 | 0.005 / 0.005 | 0.0173 / 0.0465 | 0.55 / 0.15 |

**All nine pass R_market at p = 0.005.** That is the smallest p 199 shifts can give.

**Magnitudes differ widely.** Pooled over both arms, the excess amplitude runs from 0.0010 (Gemma 4 E4B) to 0.0370
(Phi-4).

- Gemma 4 31B and Phi-4 move their target by 0.017–0.047 cash share with what they observe, depending on the arm.
- Gemma 4 E4B moves by 0.0016 in the static arm and 0.0001 under memory. On memory days its target changes by 0.01
  or more on only 0.35 % of days, which shows as 0.00 at two decimals.
- E4B passes R_market by significance alone, so its rows in E5 can be expected to be nearly flat (§6).

### 3.5 Noise and the seeds it implies (N)

σ_d is the standard deviation of the paired difference, with 122 pairs per cell and 12 cells per model. The seeds S
are those needed for band-MAS at Δ = 0.05 (D12), α′ = 0.05/36 and power 0.80, by the paired formula, at the largest
cell's σ_d. The MDD is (z₁₋α′/₂ + z₀.₈₀)·σ_d,max/√S. Source: `noise_seeds.csv`.

| model | σ_d, largest cell (cell) | RMS over 12 | 90 % limit | S, point / limit | band-MAS MDD at S 60 / 122 | σ_d D θ 0.05, largest | D θ 0.05 MDD at S 60 / 122 |
|---|---|---|---|---|---|---|---|
| Gemma 4 31B | 0.0813 (ENTJ flat) | 0.0465 | 0.0888 | 44 / 52 | 0.042 / 0.030 | 0.0494 | 0.026 / 0.018 |
| Gemma 4 E4B | 0.0918 (ISFJ sustained_bull) | 0.0458 | 0.1002 | 55 / 66 | 0.048 / 0.034 | 0.0649 | 0.034 / 0.024 |
| gpt-oss-20b | 0.1695 (ENTJ sustained_bull) | 0.0940 | 0.1851 | 188 / 224 | 0.088 / 0.062 | 0.0762 | 0.040 / 0.028 |
| Muse Glimmer 30B | 0.1208 (ENTJ sustained_bull) | 0.0674 | 0.1319 | 96 / 114 | 0.063 / 0.044 | 0.0846 | 0.044 / 0.031 |
| OLMo 3.1 32B | 0.0140 (INTJ sustained_bull) | 0.0091 | 0.0152 | 2 / 2 | 0.007 / 0.005 | 0.0912 | 0.048 / 0.033 |
| Ministral 3 14B | 0.1776 (ENTJ crash) | 0.0849 | 0.1939 | 206 / 246 | 0.093 / 0.065 | 0.0602 | 0.031 / 0.022 |
| Llama 3.1 8B | 0.0762 (ENTJ flat) | 0.0509 | 0.0831 | 38 / 46 | 0.040 / 0.028 | 0.0868 | 0.045 / 0.032 |
| Llama 3.1 70B | 0.0847 (ENTJ bull_trap) | 0.0549 | 0.0924 | 47 / 56 | 0.044 / 0.031 | 0.1261 | 0.066 / 0.046 |
| Phi-4 | 0.0728 (ENTJ bull_trap) | 0.0407 | 0.0795 | 35 / 42 | 0.038 / 0.027 | 0.1273 | 0.066 / 0.047 |

**Noise sits in the ENTJ cells.** That is where several models are bimodal: some runs fully invested and constant,
others not (§3.1).

**Seven of nine need at most 114 seeds.** Six need at most 66.

**gpt-oss-20b and Ministral 3 14B need 224 and 246.** One common S for every model in an experiment, which the rule
uses so that models stay comparable, therefore makes these two set the cost of all the others (§4.5).

### 3.6 GPU-hours per run (C)

Each model ran on one B200 at tensor parallel 1 with 64 runs in flight (`tools/cluster/headline_b200.sbatch`,
`headline_b2_b200.sbatch`). GPU-hours are the length of the union of the 2,928 ledger intervals [utc − seconds, utc].
Model load and preflight fall outside them. Source: `cost.csv`.

| model | GPU-hours | GPU-hours per run | mean in flight | input / output tokens per run | output tokens per GPU-second | E2–E5 at S 60, GPU-hours |
|---|---|---|---|---|---|---|
| Gemma 4 31B | 16.5 | 0.0056 | 63.7 | 367,513 / 19,098 | 942 | 125.0 |
| Gemma 4 E4B | 2.7 | 0.0009 | 63.6 | 366,222 / 20,301 | 6,202 | 20.2 |
| gpt-oss-20b | 6.8 | 0.0023 | 63.7 | 361,618 / 106,246 | 12,651 | 51.8 |
| Muse Glimmer 30B | 50.4 | 0.0172 | 63.6 | 352,811 / 269,889 | 4,353 | 382.4 |
| OLMo 3.1 32B | 10.7 | 0.0037 | 63.6 | 352,202 / 21,286 | 1,611 | 81.5 |
| Ministral 3 14B | 7.1 | 0.0024 | 63.7 | 366,493 / 44,647 | 5,145 | 53.5 |
| Llama 3.1 8B | 5.3 | 0.0018 | 63.5 | 356,718 / 53,648 | 8,268 | 40.0 |
| Llama 3.1 70B | 22.1 | 0.0076 | 63.6 | 356,648 / 23,393 | 860 | 167.7 |
| Phi-4 | 5.6 | 0.0019 | 63.6 | 351,820 / 26,618 | 3,872 | 42.4 |

- **Stage 1 took 127.2 GPU-hours in all.**
- **Mean in flight is 63.5–63.7 against 64**, so the intervals measure a GPU kept full.
- **Muse Glimmer costs 19 times what Gemma 4 E4B does per run.** Its output is mostly reasoning: 269,889 tokens per
  run, or 1,348 per call, against about 78 tokens of rebuilt reply per call (§3.7).
- **The ledger records 0 reasoning tokens for every model.** On the vLLM route, reasoning is counted inside the
  output.

### 3.7 Context capacity for E6 (X)

**How the need is computed.**

- The E6 prompts are rendered with the harness's own functions and counted with o200k_base. They are the stateful
  system prompt (mandate in the system prompt) and the human turn, filled from 288 stage-1 runs per model.
- ρ is each model's own tokens per o200k token. It is measured as stage-1 input per call over the o200k count of the
  same prompt.
- The history keeps the rebuilt JSON reply, without reasoning.
- The need at a level is the context plus the model's largest stage-1 output per call.
- "Full" is the harness's 60,000-token history budget, which binds at 69–79 turns.

KV capacity is the server's "GPU KV cache size" on one B200 at 0.90 utilisation. Sources: `context_e6.csv`,
`context_e6_detail.csv`.

| model | ρ | reply kept, rebuilt / measured (tokens) | largest output per call (p99 of run maxima) | need at 5 / 20 / 50 / full (k tokens) | native window (source) | KV cache, tokens | max concurrent runs at 5 / 20 / 50 / full |
|---|---|---|---|---|---|---|---|
| Gemma 4 31B | 1.06 | 82 / 95 | 153 (145) | 6.2 / 18.4 / 43.1 / 65.5 | ≥ 32,768, not read | 116,137 | 18 / 6 / 2 / 1 |
| Gemma 4 E4B | 1.06 | 81 / 102 | 380 (214) | 6.4 / 18.6 / 43.2 / 65.7 | ≥ 32,768, not read | 2,660,804 | 413 / 143 / 61 / 40 |
| gpt-oss-20b | 1.04 | 75 / 531 | 31,109 (8,211) | 37.1 / 49.0 / 72.9 / 95.2 | ≥ 32,768, not read | 3,139,385 | 84 / 64 / 43 / 32 |
| Muse Glimmer 30B | 1.02 | 78 / 1,348 | 31,157 (31,089) | 37.0 / 48.7 / 72.3 / 93.9 | ≥ 32,768, not read | 2,016,825 | 54 / 41 / 27 / 21 |
| OLMo 3.1 32B | 1.01 | 99 / 106 | 1,711 (693) | 7.6 / 19.8 / 44.3 / 64.5 | ≥ 32,768, not read | 394,123 | 51 / 19 / 8 / 6 |
| Ministral 3 14B | 1.05 | 206 / 223 | 1,250 (668) | 8.0 / 22.8 / 52.5 / 66.2 | ≥ 32,768, not read | 859,728 | 107 / 37 / 16 / 12 |
| Llama 3.1 8B | 1.03 | 81 / 268 | 30,923 (635) | 36.9 / 49.0 / 73.2 / 94.5 | 131,072 (Meta's `tokenizer_config.json`) | 1,169,904 | 31 / 23 / 15 / 12 |
| Llama 3.1 70B | 1.03 | 73 / 117 | 454 (408) | 6.4 / 18.3 / 42.1 / 63.6 | 131,072 (Meta's `tokenizer_config.json`) | 79,952 | 12 / 4 / 1 / 1 |
| Phi-4 | 1.01 | 107 / 133 | 729 (679) | 6.7 / 18.9 / 43.5 / 63.4 | 16,384 (roster; served at 16,384) | 681,360 | 101 / 36 / 15 / 10 |

**R_context** (`requirements.csv`):

- **met:** Llama 3.1 8B and 70B;
- **not met:** Phi-4, whose 16,384-token window fails every level above 5;
- **conditional:** the other six, whose windows above 32,768 are not on this machine.

**Three things matter for E6.**

- **Runaway replies.**
  - gpt-oss-20b, Muse Glimmer and Llama 3.1 8B each produced at least one reply of 30,923–31,157 tokens. That is the
    whole 32,768 window less the prompt.
  - For Glimmer it is not rare: the 99th percentile of its per-run maxima is 31,089, so at least 1 % of its 2,928
    runs contain such a reply.
  - Under the criteria, each of these runaways adds about 31k tokens to every level's need. Without them, the "full"
    need is 63–66k tokens for every model.
- **The KV cache, not the window, binds for two models.** Gemma 4 31B and Llama 3.1 70B fit one concurrent run at
  the full level on one B200, against the 64 in flight in stage 1. OLMo 3.1 32B fits 6.
- **For Llama 3.1 8B, history is longer than the rebuilt JSON.** Its measured reply is 268 tokens. Re-run with the
  measured output as the history reply, which overstates it for gpt-oss and Glimmer since their output includes
  reasoning, **no model's R_context status changes** (`robustness.csv`).

### 3.8 Redundancy (R)

The distance between two models is the mean over the four profile blocks of the RMS difference, in cash-share units.
The pair floor is √((f_a² + f_b²)/2), from each model's half-split floor (100 splits, 61 seeds per half). Path
agreement is the correlation, across the 2,928 matched runs, of the within-cell-demeaned run-mean cash share. The ten
closest pairs (`redundancy_pairs.csv`):

| model a | model b | distance | pair floor | excess | distance / floor | path agreement r |
|---|---|---|---|---|---|---|
| gpt-oss-20b | Muse Glimmer 30B | 0.0385 | 0.0135 | 0.0250 | 2.8 | 0.921 |
| Llama 3.1 70B | Phi-4 | 0.0468 | 0.0078 | 0.0391 | 6.0 | 0.661 |
| Gemma 4 31B | gpt-oss-20b | 0.0525 | 0.0130 | 0.0395 | 4.0 | 0.882 |
| Gemma 4 E4B | OLMo 3.1 32B | 0.0592 | 0.0050 | 0.0542 | 11.8 | −0.045 |
| gpt-oss-20b | Llama 3.1 8B | 0.0701 | 0.0113 | 0.0588 | 6.2 | 0.270 |
| Llama 3.1 8B | Phi-4 | 0.0722 | 0.0068 | 0.0655 | 10.7 | 0.138 |
| Muse Glimmer 30B | Llama 3.1 8B | 0.0767 | 0.0097 | 0.0670 | 7.9 | 0.302 |
| Gemma 4 31B | Muse Glimmer 30B | 0.0825 | 0.0116 | 0.0709 | 7.1 | 0.869 |
| Llama 3.1 8B | Llama 3.1 70B | 0.0817 | 0.0073 | 0.0743 | 11.1 | 0.111 |
| Gemma 4 31B | OLMo 3.1 32B | 0.0899 | 0.0080 | 0.0818 | 11.2 | 0.482 |

The floors range from 0.0031 (OLMo 3.1 32B) to 0.0148 (gpt-oss-20b) (`noise_floor.csv`).

- **No pair is indistinguishable at n = 122.** Every distance exceeds its pair floor by at least 2.8 times.
- **Two near-clusters stand out.**
  - **Gemma 4 31B, gpt-oss-20b and Muse Glimmer 30B** respond to the same market paths in the same way (r = 0.87–0.92
    over 2,928 matched runs). Their profiles lie within 0.04–0.08 of each other.
  - **Llama 3.1 70B and Phi-4** form a pair: distance 0.047, r = 0.66.
- **Gemma 4 E4B is near OLMo 3.1 32B in profile only.** Both over-separate, but E4B barely responds to the path
  (r of −0.045 to +0.026 with every model, `path_agreement.csv`).
- **Llama 3.1 8B and Ministral 3 14B have no close neighbour.**

---

## 4. The selection

### 4.1 Gates and requirements

**Every model is eligible under the registered thresholds** (`gates.csv`):

- G1: 2,928 of 2,928 runs verified and `ok` for each model;
- G2: the largest cell fallback share is 0.00037;
- G3: the largest degenerate share is 0.317, Gemma 4 E4B's, against 0.5.

**G2's sensitivity values change nothing** (0.005 and 0.02). **At G3 = 0.25, Gemma 4 E4B is ineligible**; 0.75
changes nothing.

Requirements (`requirements.csv`; n as in §3):

| model | R_effect | R_persona | R_headroom | R_market | R_context |
|---|---|---|---|---|---|
| Gemma 4 31B | yes | yes | yes | yes | conditional |
| Gemma 4 E4B | yes | yes | yes | yes | conditional |
| gpt-oss-20b | **no** (pooled CI includes 0) | yes | yes | yes | conditional |
| Muse Glimmer 30B | yes | yes | yes | yes | conditional |
| OLMo 3.1 32B | yes | yes | yes | yes | conditional |
| Ministral 3 14B | yes | yes | yes | yes | conditional |
| Llama 3.1 8B | yes | yes | yes | yes | met |
| Llama 3.1 70B | yes | yes | yes | yes | met |
| Phi-4 | yes | yes | yes | yes | not met |

### 4.2 Coverage by number of models, and the core

δ, the median floor, is 0.0083. L*(k) is the smallest coverage loss of any k-subset. The pick is the cheapest subset
within δ of it. Costs are E2–E5 GPU-hours with every member in all four experiments (`best_by_k.csv`, `subsets.csv`,
all 511 subsets).

| k | the rule's pick | L*(k) | loss of the pick | tied within δ | implied S | GPU-hours, implied S / S 60 |
|---|---|---|---|---|---|---|
| 1 | gpt-oss-20b | 0.1203 | 0.1203 | 1 of 9 | 224 | 193 / 52 |
| 2 | Gemma 4 E4B + Llama 3.1 8B | 0.0907 | 0.0981 | 4 of 36 | 66 | 66 / 60 |
| 3 | OLMo 3.1 32B + Llama 3.1 8B + Phi-4 | 0.0818 | 0.0851 | 18 of 84 | 46 | 126 / 164 |
| 4 | Gemma 4 E4B + gpt-oss-20b + Ministral 3 14B + Phi-4 | 0.0588 | 0.0588 | 4 of 126 | 246 | 688 / 168 |
| 5 | the k = 4 set + Llama 3.1 8B | 0.0542 | 0.0542 | 16 of 126 | 246 | 852 / 208 |
| **6** | **the k = 5 set + OLMo 3.1 32B** | **0.0395** | **0.0395** | 2 of 84 | 246 | **1,186 / 289** |
| 7 | the k = 6 set + Gemma 4 31B | 0.0391 | 0.0391 | 7 of 36 | 246 | 1,699 / 414 |
| 8 | the k = 7 set + Llama 3.1 70B | 0.0250 | 0.0250 | 2 of 9 | 246 | 2,387 / 582 |
| 9 | all nine | 0 | 0 | 1 of 1 | 246 | 3,954 / 964 |

**The size rule keeps six.** Five would lose 0.0542 against six's 0.0395, more than δ = 0.0083 apart.

**A seventh model adds 0.0004.** That is less than a twentieth of δ, so the curve flattens at six.

**What is left uncovered at six.** The largest gap is Gemma 4 31B's: 0.0395 beyond gpt-oss-20b's noise. Llama 3.1
70B's is 0.0391, beyond Phi-4's.

**The tie at six.** The other subset within δ puts Llama 3.1 70B where Phi-4 is. It costs 1,700 rather than 1,186
GPU-hours at S = 246, so the rule takes Phi-4.

### 4.3 The assignments

Source: `assignments.csv`. The rule's core, and the core the rule gives at G3 = 0.25:

| experiment | rule's core | core at G3 = 0.25 (Gemma 4 31B for Gemma 4 E4B) |
|---|---|---|
| E2, E3 | core − gpt-oss-20b (R_effect) + **Gemma 4 31B** (top-up) | core − gpt-oss-20b + **Muse Glimmer 30B** (top-up) |
| E4, E5 | the core | the core |
| E6 (rule) | Llama 3.1 8B | Llama 3.1 8B |
| E6 if the unread windows suffice | Gemma 4 E4B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B | Gemma 4 31B, OLMo 3.1 32B, Ministral 3 14B, Llama 3.1 8B |
| E7 | Gemma 4 E4B, Ministral 3 14B, Llama 3.1 8B | gpt-oss-20b, Llama 3.1 8B, Phi-4 |
| E8 | Gemma 4 E4B, Ministral 3 14B, Llama 3.1 8B | OLMo 3.1 32B, Llama 3.1 8B, Phi-4 |

**The top-up is chosen by the rule's coverage criterion.** With the five qualifying core members, the best E2/E3
top-up is the excluded model that covers the nine best. Under the rule's core, that is Gemma 4 31B. It is also the
model whose ENTJ cells most show re-injection *worsening* adherence: three of its four are positive and significant,
against one each (crash) for gpt-oss-20b and Muse Glimmer (§3.3). So E2 and E3 keep that sign.

**E6 picks Llama 3.1 8B alone.** It is the only core model meeting both R_effect and R_context on what can be read
here. Llama 3.1 70B meets R_context too, but it is not in the core, and one B200 holds a single concurrent run of it
at levels 50 and full.

**In the conditional reading, every E6 pick has room to run.** All four hold the full level with 6–40 concurrent runs
on one B200, if their windows hold the full-level needs of §3.7 (64.5k–66.2k tokens; Llama 3.1 8B's 131,072 is
already read).

### 4.4 Robustness

Source: `robustness.csv`.

| check | n | result |
|---|---|---|
| path bootstrap of the profiles (paths resampled, the same draw for every model; floors fixed) | 200 draws | the same six in 200 of 200; each core member in 200 of 200; each excluded model in 0 |
| mean excess over excluded models in place of the largest (k-median) | 84 six-subsets | the same six |
| G2 at 0.005 / 0.02 | 9 models | the same nine eligible, the same core |
| G3 at 0.75 | 9 models | the same nine eligible, the same core |
| **G3 at 0.25** | 8 eligible | **Gemma 4 E4B out; the core becomes Gemma 4 31B + gpt-oss-20b + OLMo 3.1 32B + Ministral 3 14B + Llama 3.1 8B + Phi-4** (loss 0.0391 over the eight; S 246) |
| E6 with the measured output as the history reply | 9 models × 4 levels | no R_context status changes |

### 4.5 Alternatives and their costs

E2–E5 GPU-hours with every member in all four experiments, on four seed bases (`subset_costs.csv`):

| subset | members | S 60 | S 122 | own implied S, ≥ 60 | one implied S (S) | coverage loss over the nine |
|---|---|---|---|---|---|---|
| **recommended core** | E4B, gpt-oss-20b, OLMo, Ministral, Llama 8B, Phi-4 | **289** | 588 | 599 | 1,186 (246) | 0.0395 |
| core at G3 = 0.25 | Gemma 4 31B in place of E4B | 394 | 801 | 702 | 1,616 (246) | 0.0542 |
| tied at k = 6 | Llama 3.1 70B in place of Phi-4 | 415 | 843 | 724 | 1,700 (246) | 0.0395 |
| next at k = 6 | Gemma 4 31B in place of OLMo | 333 | 677 | 642 | 1,365 (246) | 0.0542 |
| cheapest six at its implied S | Gemma 4 31B, E4B, OLMo, Llama 8B, Llama 70B, Phi-4 | 477 | 969 | 479 | 524 (66) | 0.0851 |
| best five | the core without OLMo | 208 | 423 | 517 | 852 (246) | 0.0542 |
| best seven | the core + Gemma 4 31B | 414 | 843 | 724 | 1,699 (246) | 0.0391 |
| all nine | — | 964 | 1,961 | 1,618 | 3,954 (246) | 0 |

The coverage loss of the G3 = 0.25 core over the nine is 0.0542, because Gemma 4 E4B is left out. Over the eight that
core covers, it is 0.0391.

**The cheapest six buys a low S by excluding the two noisy models.** It drops gpt-oss-20b and Ministral 3 14B, which
brings S down to 66. It then leaves Ministral 3 14B 0.085 beyond any member's noise, and Muse Glimmer 0.067.

**The seed policy moves the cost about as much as the model choice does.**

- For the recommended core, GPU-hours run from 289 at S = 60, to 599 with each model at its own S (≥ 60), to 1,186
  at one S of 246.
- Choosing six models rather than nine moves the cost by 3.3 times at any fixed S.

---

## 5. What the recommended core loses against all nine

Source: `losses.csv`, `loss_cells.csv`.

**Three models are left out.** Each sits beyond the noise of a core member:

| excluded | nearest member | distance | pair floor | excess |
|---|---|---|---|---|
| Gemma 4 31B | gpt-oss-20b | 0.0525 | 0.0130 | 0.0395 |
| Muse Glimmer 30B | gpt-oss-20b | 0.0385 | 0.0135 | 0.0250 |
| Llama 3.1 70B | Phi-4 | 0.0468 | 0.0078 | 0.0391 |

**The cross-model mean effect barely moves.** Over the 12 persona × scenario cells, each the mean of the six models'
effects against the mean of the nine:

| metric | largest gap | RMS gap | nine's SE across models (median cell) |
|---|---|---|---|
| band-MAS | 0.0104 | 0.0053 | 0.0089 |
| D at θ 0.05 | 0.0085 | 0.0042 | 0.0054 |

Between-model heterogeneity is kept. The six's between-model sd of the effects is 1.08 times the nine's for band-MAS
and 0.85 times for D (median over 12 cells).

**Some sign-mixed cells lose one sign.** In 7 of the 12 band-MAS cells, the nine models show significant effects of
both signs. The six keep both signs in 5 of them. The two they lose are ENTJ bull_trap and ENTJ flat, where the only
positive (worsening) effect is Gemma 4 31B's. The E2/E3 top-up restores it for those two experiments. For D at θ
0.05, the six keep both signs in 4 of 7 such cells.

**Ranges.** The six keep the nine's full range of separation, market amplitude and noise. They lose one end of three
other ranges:

| quantity | the six | the nine |
|---|---|---|
| static separation | 0.34–1.20 | 0.34–1.20 |
| excess market amplitude | 0.0010–0.0370 | 0.0010–0.0370 |
| static band-MAS | 0.066–0.223 | 0.066–0.259 |
| pooled band-MAS effect | −0.086 to +0.012 | −0.099 to +0.039 |
| σ_d max | 0.014–0.178 | 0.014–0.178 |
| GPU-hours per run | 0.0009–0.0037 | 0.0009–0.0172 |

The six lose:

- the largest improvement, Llama 3.1 70B's −0.099;
- the largest worsening, Gemma 4 31B's +0.039;
- the least-in-band static model, Muse Glimmer's 0.259;
- the one 70B-class model; the largest kept is OLMo 3.1 32B. That fact played no part in the choice.

**Cost.** E2–E5 with the six in all four experiments costs 289 rather than 964 GPU-hours at S = 60, and 1,186 rather
than 3,954 at one S of 246. That saves 675 and 2,768 GPU-hours. For scale, stage 1 took 127.2.

---

## 6. What this selection does not settle

- **The seed policy.** The registered rule (Δ = 0.05, α′ = 0.05/36, one S for every model in an experiment) gives
  S = 246. That is 4.1 times the plan's 60, set by two bimodal ENTJ cells:
  - Ministral 3 14B: σ_d 0.178 in ENTJ crash, 90 % limit 0.194;
  - gpt-oss-20b: σ_d 0.170 in ENTJ sustained_bull, limit 0.185.

  The options and their prices (§4.5):
  - S = 60, accepting a band-MAS MDD of 0.093 and 0.088 for those two models;
  - each model at its own S;
  - 246 for all.
- **gpt-oss-20b in E2 and E3.** R_effect reads the *pooled* CI, so opposite-signed cells cancel. A cell reading, for
  example any of its 12 cells excluding 0 after BH, would keep gpt-oss-20b in E2 and E3 and drop the Gemma 4 31B
  top-up.
  - That reading is cheaper: 0.0023 against 0.0056 GPU-hours per run.
  - It keeps re-injection's "worsening" sign only in ENTJ crash. The top-up keeps it in ENTJ flat, bull_trap and
    crash.
- **Gemma 4 E4B's usefulness for E5.** It meets R_market, but only by significance:
  - its excess amplitude is 0.0016 static and 0.0001 memory;
  - 0.317 of its runs are constant-target.

  Its E5 rows can be expected to be nearly flat. The G3 = 0.25 core replaces it at +105 GPU-hours at S = 60.
- **E6's roster, size and cost.**
  - It needs three native windows read: Gemma 4 E4B, OLMo 3.1 32B and Ministral 3 14B. Their full-level needs are
    65.7k, 64.5k and 66.2k tokens.
  - It needs the stateful sizing pilot the plan already requires. Stage-1 GPU-hours do not price stateful runs,
    whose per-call context is 3.2–3.7 times the stage-1 prompt at level 5 and 35.0–35.5 times at the full level
    (§3.7).
  - The runaway replies of §3.7 should be capped or detected before E6, where a runaway costs up to a whole window.
- **The profile's weighting.** The four blocks count equally, which is a design choice. The bootstrap and the
  mean-excess objective agree with the result, but no other block weighting was tried.
- **Claims.** Effects here are selection descriptives. The registered per-model families of 36 remain to be run, as
  `PREREG_PHASE_9_STAGE1_OPEN.md` 3 and its batch-2 twin specify.

---

## 7. Changes made after the rule was frozen

Every item below is a disclosed addition or fix. None changes an input, a threshold or the rule.

1. **A 4-seed smoke run, after `CRITERIA.md` was written.** It covered 864 runs, tested the pipeline, and wrote to a
   scratch directory. Its numbers are not used.
2. **The E6 upper-bound variant (§3.7).** The smoke run showed Llama 3.1 8B's measured reply at 3.4 times the
   rebuilt JSON. I added the history-reply-as-measured-output variant as a robustness check. No status changed.
3. **The "E6 if the unread windows suffice" assignment, and the per-run output quantiles.** Both are labelled
   information. The rule's E6 is unchanged.
4. **A fix for undefined D at θ 0.05.** The first full run stopped at the subset step, before writing any selection
   output, because D at θ 0.05 is undefined on 2 paths (§2). The profile now leaves those pairs out, as
   `seed_level_pairs` does.
5. **Additions after the first complete full run, with its results seen:**
   - Step 4 (ii) carried through: the core under each gate threshold, with its assignments and losses;
   - the subset and assignment cost tables;
   - the pairwise redundancy table;
   - the band-MAS MDDs beside D's.

   The core, k, the assignments at the registered thresholds and the bootstrap share are identical before and after.

---

## 8. Citation table

No number from any source below enters a parameter file or a test tolerance.

| source | what it is cited for | status | where it enters |
|---|---|---|---|
| `GRID_EXPERIMENT_PLAN.md` §3 | each experiment's arms, scenarios, runs per model and model count (6, 6, 6, 6, 4, 3, 3) | read | `RUNS_PER_SEED`, `PLAN_M`, the requirement map |
| `PREREG_PHASE_9_STAGE1_OPEN.md` §0–3, §7; `PREREG_PHASE_9_STAGE1_OPEN_B2.md` §0–3 | the cells and seeds, the serving flags, tier C, each model's family of 36 (α′ = 0.05/36), Δ = 0.05 (D12), the pre-claim precondition, the 1-GPU tasks | read | N2, E, U |
| `evaluation/targets.py` | bands and centres (0.80 − 0.10 = 0.70) and `band_mas` | read (code); reused unmodified | P2, P3 |
| `evaluation/metrics_v2.py` `score_run(scoring="v2_1")` | every per-run metric | read (code); reused unmodified | all |
| `tools/stats_v2.py` `seed_level_pairs`, `pigeonhole_ci` | the pairing and the one-way path bootstrap | read (code); reused unmodified | E |
| `agent/stateful_agent.py`, `experiments/arms_v2.py`, `simulation/runner_v2.py` | the E6 levels (5, 20, 50, full), the 60,000-token o200k budget, what the history keeps | read (code) | X |
| `tools/phase9/e9_roster.py`, Phi-4's entry | Phi-4's 16,384-token context | read | X |
| Meta's `tokenizer_config.json` (sha256 `177c7b61…`, the file served for both Llama 3.1 sizes) | `model_max_length` 131,072 | read from the local Hugging Face cache, hash checked | X |
| stage-1 vLLM 0.29.0 server logs (`e9_4/cluster_logs`) | KV-cache size and served length per model | read; nothing else from them reaches any output | X |
| vLLM refuses a `--max-model-len` above a model's derived length unless `VLLM_ALLOW_LONG_MAX_MODEL_LEN` is set | the six other windows are at least 32,768 | **not re-read** (vLLM source). If wrong, those six windows are simply unknown | X |
| `tools/cluster/headline_b200.sbatch`, `headline_b2_b200.sbatch` | one B200 per model, tensor parallel 1, 64 in flight | read; no identifier quoted | C |

---

## 9. Files and how to reproduce

- **Script:** `tools/phase9/e9_4_select.py`. Run it as
  `python -u -m tools.phase9.e9_4_select [--workers 8] [--cache DIR]`. Reading the 7.5 GB of CSVs takes about 8 min on
  8 cores; a re-run from `--cache` takes 2–3 min. It reads `results_v2/` and the stage-1 server logs and writes nothing
  outside `selection/` and the cache.
- **Rule:** `docs/env_v2/generated/v2_1/e9_4/selection/CRITERIA.md`.
- **Tables:** `docs/env_v2/generated/v2_1/e9_4/selection/`.

| group | files |
|---|---|
| per run | `per_run.csv` (26,352 rows), `shared_paths.csv` |
| measurements | `usability.csv`, `persona.csv`, `effects_cells.csv`, `effects_pooled.csv`, `market.csv`, `noise_seeds.csv`, `cost.csv`, `context_e6.csv`, `context_e6_detail.csv` |
| redundancy | `profiles.csv`, `distance.csv`, `noise_floor.csv`, `path_agreement.csv`, `redundancy_pairs.csv` |
| the rule | `gates.csv`, `requirements.csv`, `subsets.csv`, `best_by_k.csv`, `assignments.csv`, `assignment_costs.csv`, `robustness.csv` |
| losses and costs | `losses.csv`, `loss_cells.csv`, `subset_costs.csv` |
| summary | `selection.json` |

- **No cluster identifiers in the outputs.** The outputs and the script were scanned for the cluster account, user
  path, host, node and job identifiers, and none is present.
