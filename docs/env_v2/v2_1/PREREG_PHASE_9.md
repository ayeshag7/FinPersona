# Pre-registration — Phase 9 of the v2.1 improvement plan (sensitivity through the LLM harness)

**Written 11 September 2026. No simulated rate, parameter ranking or paid batch of this phase existed when it was
written.** Plan Section 13 (E9.1–E9.5), Section 17 (D2, as re-framed by P9-1), Appendix A; register entries 1, 9 and
16; weaknesses 8, 10, 12, 20, 21, 23 (LLM side), 29.

**How this document is built.**

- A section marked **FIXED** is in final form. A rule in it that later proves wrong goes in
  `PREREG_PHASE_9_ADDENDUM.md`, stated as loudly as a confirmation.
- A section marked **OPEN** waits on a decision only the team can take: the roster, the design against the clock,
  and the reference distribution for model-level contrasts. Each OPEN section is fixed, and marked so with its date,
  **before the first paid batch.**

**What had been looked at before this was written:**

- Phase 8's result files and parameter files.
- The throughput and wall-clock tables computed from Phase 8's ledgers (`e9_0/throughput.csv`, `e9_0/wallclock.csv`).
  They are descriptive and test nothing.
- The analytic model-level power table (`e9_0/model_power.json`).
- The candidate clients, constructed with no call (`e9_0/smoke/clients.json`).
- A survey of the parameter files' in-force values, recorded intervals and override hooks.

The candidate smoke tests were running while this was written; none of their results had been read.

**Not computed when this was written:**

- no generator panel at any non-default level;
- no ranking statistic;
- no simulated size or power for any estimator of this phase;
- no σ_d for any model other than E8.5's two.

---

## 0. The state this phase starts from, the decisions that govern it, and what was found before any rule

**The frozen state:**

- the freeze manifest of 30 files and the 95-configuration path-hash fixture, 0 of 95 changed since Phase 7;
- the scoring file `evaluation/params/scoring.json`: θ co-primary (0.05 and 0.0020), scoring A;
- the inference file `experiments/params/inference.json`, read through its loud loader:
  - D12 Δ = 0.05 band-MAS;
  - the closed-form 90 % limit (P8-15);
  - 93 seeds per persona × scenario cell at R = 1 (P8-16);
  - E2's intervals decide and the crossed model is descriptive (P8-17);
  - BY across families decides (P8-10);
  - the path-level sign-flip is the only temporal null (P8-11);
- D11: a common-start slice with NONE (P8-13, P8-14).

**`envs/`, Phase 7's scoring files and every parameter file are read, never edited.** The test-tree baseline is
Phase 8's: 219 passed, 1 skipped, 4 xfailed, 0 failed.

**Team decision P9-1 (11 Sep 2026):** cost is not a constraint and robustness is not traded for money; wall-clock is
the binding constraint; paid concurrency is capped at 10–15 in-flight calls per model; no batch APIs.

**Taken by the team on 11 Sep 2026, after this document's first version and before any paid batch** (the tables
they were asked with: `e9_0/decision_tables.md`):

- **P9-2, the roster:** every candidate that passed its smoke, 13 configurations (`tools/phase9/e9_roster.py`
  `ROSTER`).
- **P9-3, the design:** a staged grid. Stage 1 is the headline static–memory contrast on every model; stage 2 is the
  generator sweep, with seeds from E9.3's criteria stage.
- **P9-4, the reference distribution:** R5 (addendum 1). The registered recommendation rule, which is unmeetable by
  construction, recommended none (addendum 3).
- **P9-5, the configuration:** provider defaults, with Flash's thinking off (P8-8).

**Not pre-empted:** D3, D5, D15, and anything Phase 10 decides.

**Found before any rule was written.** Each is reported in `PHASE_9_REPORT.md` as a correction.

1. **REG-16 (i)'s ranking cannot be read from Phase 7's files.** E7.8 swept the parameters of the *scripted
   policies* (drift rate, alignment probability, panic fraction) on the frozen generator (`e7_8/sweeps.csv`). No file
   written by Phases 1–8 carries a generator parameter's effect on the level-free observables oracle's regret or on
   the scripted policies' band-MAS. The ranking is computed here (section 1), offline, before any run.
2. **Plan 13.1's level table predates the fits of Phases 1–5.**
   - Half-life: in force 22.38 d (engine `ar1_fit`, 30-refit CI95 [18.75, 32.64]), where the plan writes 60 / FIT /
     250 d.
   - Analyst error sd: in force 0.564. It is LIT, with the bracket [0.3, 0.6] and the Phase-9 levels [0.3, 0.45, 0.6]
     recorded in `envs/v2/params/observables.json`. The plan writes 0.15 / LIT / 0.45.
   - Sentiment valuation loading: in force it is **0** (design A; D15 open), so the default of the plan's
     "0 / half / full" is its low level.
   - σ_V: its only recorded interval is a 30-refit bootstrap CI95 ([0.012750, 0.015269]); no P25/P75 exists.

   The levels are re-derived by section 1.2's rule. The plan is not edited.
3. **Phase 7's scripted policies are not reproducible across processes.** `tools/phase7/e7_panel.scripted_policies`
   keys the drift direction and the alignment draws on `abs(hash((scenario, seed, persona)))`. Python salts string
   hashes per process, and `PYTHONHASHSEED` is set nowhere in the repository. E7.8's verdicts (monotonicity) do not
   depend on the draw, but its trajectories and cell means are not reproducible. E9.1 uses the same policies keyed on
   `zlib.crc32`; Phase 7's files are not edited.
4. **REG-1's run count.** The register writes "60 + 60 runs", but its factor list is 10 paths × 3 personas ×
   2 scenarios × 4 renderings = 240 (`tools/phase9/e9_designs.py`).
5. **The execution prompt's throughput table is not reproduced.** It gives Flash 133 runs/h at effective
   concurrency 14.7 and GPT-5 mini 29/h at 12.8. It came from no repository tool. On the same ledgers
   `tools/phase9/e9_wallclock.py` gives Flash 129.0/h at 14.29 and GPT-5 mini 27.3/h at 11.84, with busy time defined
   as the union of the runs' intervals. The tool's numbers are the ones used.

---

## 1. E9.1 — the parameter list (REG-16 (i)) — FIXED

### 1.1 Candidates

The plan's six (13.1) are candidates by definition. Beside them, every generator parameter is a candidate that:

- (i) changes what the agent is shown;
- (ii) has an interval of its value in force recorded in its parameter file;
- (iii) is a scalar that a `GenConfig` field sets per run, without an `envs/` edit.

| candidate | field | in force | low / high | interval type | source |
|---|---|---|---|---|---|
| σ_V (plan) | `sigma_V` | 0.014573 | 0.012750 / 0.015269 | 30-refit CI95 (plan's P25/P75 not recorded) | `envs/v2/params/value.json` |
| half-life (plan) | `engine = ar1_fit_hl<d>`, matched sd(x) (1.3) | 22.38 d | 18.75 / 32.64 d | 30-refit CI95 (plan's 60 / 250 predate the fit) | `mispricing.json` |
| GJR-GARCH set (plan) | `garch` {alpha, gamma, beta, df} | median set | P25 set / P75 set (`nu` → `df`) | per-stock quartile sets | `volatility.json` |
| P/E multiple dispersion (plan) | `obs_overrides.multiple.width` | P10–P90 | P25–P75 / P5–P95 | stored grids | `observables.json` |
| analyst error sd (plan) | `obs_overrides.analyst.sd` | 0.564 | 0.3 / 0.6 | the recorded LIT bracket | `observables.json` |
| sentiment valuation loading (plan) | `obs_overrides.sentiment` {design B, `c_val`} | 0 (design A) | half / full `c_val` (0.5 × and 1 × 0.94993) | plan's levels on the stored FIT coefficient | `observables.json` |
| μ_V | `mu_V` | 2.281e-4 | CI endpoints | CI | `value.json` |
| jump rate | `jump_rate` | 5.83e-4 | CI endpoints | CI | `value.json` |
| jump sd | `jump_sd` | 0.2303 | CI endpoints | CI | `value.json` |
| σ̄ (GARCH unconditional sd) | `garch.sbar` | 0.015088 | CI endpoints | CI | `volatility.json` |
| blow-off growth threshold | `blowoff_g` | 0.00984 | CI endpoints | CI | `events.json` |
| EPS noise sd | `obs_overrides.eps.s_eps` | 0.1707 | CI endpoints | CI | `observables.json` |
| EPS loss probability | `obs_overrides.eps.p_loss` | 0.0975 | CI endpoints | CI | `observables.json` |
| P/E cap | `obs_overrides.eps.pe_cap` | 191.5 | CI endpoints | CI | `observables.json` |
| dividend speed | `obs_overrides.dividend.c_speed` | 0.697 | CI endpoints | CI | `observables.json` |
| dividend tau | `obs_overrides.dividend.tau` | 0.406 | CI endpoints | CI | `observables.json` |
| sentiment persistence | `obs_overrides.sentiment.rho` | 0.211 | CI endpoints | CI | `observables.json` |
| sentiment return loading | `obs_overrides.sentiment.b1` | 0.111 | CI endpoints | CI | `observables.json` |
| volume persistence | `obs_overrides.volume.rho_v` | 0.526 | CI endpoints | CI | `observables.json` |
| volume |r| loading | `obs_overrides.volume.beta_absr` | 0.203 | CI endpoints | CI | `observables.json` |
| volume noise sd | `obs_overrides.volume.sd_e` | 0.347 | CI endpoints | CI | `observables.json` |

The tool reads every value in this table from its parameter file and refuses to run if a value differs from the file.
The table's decimals are the survey's.

**Excluded, with the reason:**

- **IV noise; crash tail share; the control threshold.** No per-run hook, so an `envs/` edit would be needed.
- **Hazard h₀ and b.** The recorded interval is on the topped share, not on the parameters.
- **κ.** A DESIGN range with no data interval.
- **The schedule ranges** (det_len, panic_len, front_load, depth, rec60, post-top drop and length). They are the
  ranges schedule draws are taken from, so every path already samples them, and the grid's seeds cover them.
- **The multi-asset loading.** It acts only at N > 1, and item 29 is the 3-asset cell's (plan 13.1).
- **b_pred, df_V, burn-in, λ_panic.** No interval recorded.
- **The start-price render scale.** It changes only the rendered magnitude, and the level-free oracle and the
  scripted policies cannot see it by construction. It is REG-1's question.

### 1.2 Levels

The low and high levels are those of the table.

- **Half-life:** each level is run at matched sd(x) (1.3).
- **GARCH P25/P75 sets:** only α, γ, β and df are set; ω follows from σ̄ and the persistence, as `GJRParams` defines
  it.
- **Sentiment loading:** its default (0) is not between its levels. The effect is therefore measured against the
  default at every level (1.4), never low against high.

### 1.3 Panels

**One panel per level, plus the default.** Every panel uses:

- seeds 0–99 (`e7_panel`'s scored seeds), the same seeds at every level (common random numbers);
- 4 scenarios × 3 personas, T = 200, crash δ 0.70, `PortfolioV2` at 5 bp, start at the band centre;
- `SyntheticMarketEnv(scenario, 200, seed, config=<the level's override>)`.

**The policies:**

- the pickled Phase-6 level-free oracles, **`L5_full_level_free`** (the observables oracle) and `L5_level_free`
  beside;
- `mandate_conditional_oracle`;
- the scripted families drift / align / panic at E7.8's parameter values, keyed on `zlib.crc32` (finding 3).

**The oracles are the pickled default-trained readers, not retrained per level.** The ranking asks what a parameter
does to the difficulty a *fixed* reader faces, which is the LLM's situation: it is not retrained on each generator.
A per-level retrained oracle is a separate question, the entitled reader's ceiling. It is not run here.

**Matched sd(x) for the half-life** follows plan 13.1 by the construction of `tools/phase2/e2_6_sweep.py`
(`calibrate`, called, not copied):

- the stationary sd of x at σ̄ in force is measured on 20 flat paths of T = 5,000, jumps off, rejection off, at each
  half-life level and at the default engine;
- σ̄ is scaled by (target sd ÷ measured sd), where the target is the default engine's sd, since sd(x) is linear in
  the innovation scale;
- a confirmation pass at the rescaled σ̄ reports the matched sd;
- the calibration seeds are e2_6's (132000 / 133000 blocks), disjoint from the panel's.

*Corrected on 11 Sep 2026, after `tools/phase2/e2_6_sweep.py` was read and before any calibration ran: the first draft of this
paragraph named a pooled 4-scenario, 200-day calibration on seeds 500–539, which is not e2_6's construction.*
The rescaling moves return volatility too, so each level's sd(r) is reported beside, and the unmatched levels are run
beside as a sensitivity that does not enter the rule.

**Reference rows before any level is read:**

- (a) the default panel's `L5_full_level_free` flat MCR at θ 0.05 equals the published 0.0770 to four decimals;
- (b) the default panel's L5 policies reproduce `e6_16a/runs.csv`'s MCR row by row, as `e7_panel --stages verify`
  does, with worst |difference| ≤ 1e-12.

On the lab box, the numeric check of P6-15 is re-run first.

### 1.4 The statistic

Outcomes:

- **O1:** `L5_full_level_free`'s MCR at θ_info = 0.05;
- **O2:** the same at θ_cost = 0.0020 (co-primary, P7-4);
- **O3:** the scripted policies' band-MAS, the mean over the drift, align and panic policies at the half-width in
  force (0.10).

Each is scored by `evaluation.scoring.regret_terms_batch`.

For parameter j, level ℓ, outcome k and scenario × persona cell c:

- the paired seed differences are d_s = y(ℓ, s) − y(default, s);
- the standardised effect is e(ℓ, k, c) = |mean_s d_s| / sd_s y(default, s).

Then:

- E(ℓ, k) is the mean of e over the 12 cells;
- E(j, k) is the maximum of E(ℓ, k) over j's non-default levels;
- **the oracle effect** is E(j, oracle) = ½ [E(j, O1) + E(j, O2)];
- **the scripted effect** is E(j, scripted) = E(j, O3).

**Uncertainty, reported and not entering the rule:**

- a seed-cluster bootstrap (1,000 resamples of the 100 seeds, one resample shared by every level and outcome) gives a
  95 % interval for each E;
- the share of resamples in which each candidate is in the data-driven six.

### 1.5 The rule

- **Ranking.** The candidates are ranked on the oracle effect and, separately, on the scripted effect, with rank 1 the
  largest. The score is the sum of the two ranks.
- **The data-driven six** are the six lowest scores. Ties go first toward a parameter the reviews name (the plan's
  six), then toward the larger oracle effect.
- **If the data-driven six shares at least five parameters with the plan's six,** the plan's six are run at
  section 1.2's levels. The data-driven parameter not in the plan's list (if any) is run as a further cell.
- **Otherwise** the data-driven six are run, and the report says why.

**What the ranking does not decide:** the ranking outcomes contain no LLM. Phase 8's L3 probe found every model
following the analyst field (P8-12). A parameter that ranks low here and moves LLM behaviour in the grid is therefore
evidence about the models, not about the environment. **Stated expectation:** the analyst error sd moves the LLM
contrast more than its rank here suggests, because the scripted policies never read the analyst field and the oracle
reads it as one feature among many.

---

## 2. E9.2 — roster pilots — FIXED in its rule, OPEN in its shape

**The rule:**

- Every roster model not fully measured in Phase 8 gets a variance pilot, in the exact configuration the grid runs.
  GPT-5 mini counts as not fully measured: it has 24 pairs on one scenario.
- The pilot runs the static and memory arms, at `harness_version`/`placebo_version` v2_1.
- σ_d(R = 1) for band-MAS comes with its closed-form one-sided 90 % limit (`tools/phase8/e8_5_analyse.mls_ucl_sigma_d`, P8-15),
  and D at both θ and B are reported beside.
- **The grid's plug-in is the maximum over the roster models of each model's limit**, not a transfer ratio from one
  model (P8-16's rule, applied to measured models).
- The seed count follows Appendix A as written, at the Bonferroni α′ of the pre-registered family count, with the
  paired-correct count beside.

**The shape — FIXED 11 Sep 2026, after P9-2 and before any pilot run** (`tools/phase9/e9_2_pilot.py --stages shape`,
`e9_2/shape.json`):

- **Cells and seeds.** E8.5's 12 persona × scenario cells × (static, memory), at **R = 1**: the grid runs R = 1, and at
  R = 1 σ_d(1) is measured directly, so no replicate is needed to separate replicate from seed × arm variance for
  sizing. The pilot seeds S_p per cell are the value in {4, 8, 12, 16, 24, 32} that minimises the expected runs per
  model: the pilot's 24 S_p plus stage 1's runs at the plug-in limit.
- **Where stage 1's runs at the limit come from.** They are the run count at E8.5's reference seed count (93,
  `e8_5/transfer.json`), divided by the inflation E8.5's own limit carried (df 84), and multiplied by the
  chi-square 90 % limit's inflation df / χ²₀.₁₀(df) at the pilot's df_d = 12 S_p − 12. Ties go to the smaller S_p.
  E8.5's shape (576 runs, 96 pairs, df 84) is shown beside.
- **Seeds 3001 upward**, disjoint from E8.5's and from the grid's.
- **Which models are piloted.** Gemini 2.5 Flash (thinking off) is not: it is measured in the grid's configuration on
  the grid's four scenarios (E8.5). The exemption holds only if its static and memory prompt hashes under the grid's
  harness equal E8.5's launch manifest. Otherwise it is piloted too.
- **Every other roster model is piloted**, GPT-5 mini included (its E8.5 transfer ran on one scenario). All pilots run
  at once, at 15 workers per model.
- **The limit.** Each piloted model's band-MAS σ_d(1) takes the chi-square one-sided 90 % limit on df_d (the closed
  form at R′ = R, P8-15). Flash's is E8.5's closed-form limit at R′ = 1.
- **The plug-in** is the maximum over the 13 models. Stage 1's seeds follow Appendix A as written, at
  α′ = 0.05 / 36, with the paired-correct count beside (`e9_2/sizing.json`).
- **If a model's pilot cannot complete** (runs abandoned after three attempts), the report says so. Stage 1 does not
  start on a plug-in that lacks it.

---

## 3. E9.3 — the robustness criteria, validated on simulated data before the grid

### 3.1 Stage `refdist`: the reference distribution for a model-level arm contrast — FIXED

**Question.** In one persona × scenario cell with M models and S seeds, which reference distribution holds size for
the average memory − static contrast across models, and with what power at D12's Δ?

**Data-generating process** (`tools/phase9/e9_3_simulate.py`). The seed-level difference of model m on path s is:

d(m, s) = β + [b(m, memory) − b(m, static)] + [g(s, memory) − g(s, static)] + [h(m, s, memory) − h(m, s, static)] + [e(m, s, memory) − e(m, s, static)]

Every arm-level term is drawn with the variance of E8.5's measured band-MAS component, read from
`e8_5/components_reml_persona_path.json` and never typed:

- **g:** path × arm, shared by models;
- **h:** persona × path × arm. It is shared by models in the *shared* reading and drawn per model in the
  *model-specific* reading. Under heterogeneity, the models at GPT-5 mini's scale carry an extra model-specific term
  that makes their persona × path × arm variance the measured σ²_int ratio times Flash's. The path × arm term is
  shared by models and is not scaled, so at 2.1 × 10⁻⁵ against 4.1 × 10⁻⁴ their seed × arm variance is slightly
  below the ratio times Flash's;
- **e:** the replicate term, scaled by the replicate ratio for those models;
- **b(m, arm):** N(0, τ²/2), so the per-model arm effect has sd τ.

The path and persona × path intercepts cancel in the difference. This is Phase 8's `simulate_pp` difference, and the
vectorised construction is proven equal to the paired difference of a long frame built from the same draws
(`test_refdist_vectorised_equals_long_frame`).

**Conditions:**

- **M** ∈ {2, 3, 4, 5, 6, 8, 10, 12, 14};
- **S** ∈ {19, 47, 93};
- **τ** ∈ {0, ½ × Flash's σ_d limit, Flash's σ_d limit, √2 × 0.03}. The last is Phase 8's model × arm sd of 0.03 in
  E1's parameterisation; the limit is read from `inference.json`, and 0.03 from `e8_3/mixed_pp.json`'s conditions;
- **reading** ∈ {shared, model-specific};
- **heterogeneity** ∈ {equal, ⌊M/2⌋ models at GPT-5 mini's ratios}. The σ²_int and σ²_rep ratios on bull_trap are
  read from `e8_5/transfer.json`;
- **β** ∈ {0, Δ = 0.05}.

That is 864 conditions with 10,000 datasets each.

**The candidates:**

- **R1 normal:** z = d̄ / (s_M / √M), where s_M is the sd of the M per-model means over the S paths.
- **R2 t on M − 1 df:** the same statistic against t(M − 1).
- **R3 the two-way cluster bootstrap** by model and path (E2; `tools.stats_v2.pigeonhole_ci`'s construction,
  B = 1,999). It rejects when the percentile interval excludes 0; p is read from the same draws. It runs on the subset
  M ∈ {3, 6, 8, 12}, S ∈ {19, 93}, τ ∈ {0, √2 × 0.03}, both readings, equal heterogeneity, both β, with 1,000
  datasets each. Its vectorised form is proven equal to `pigeonhole_ci` on the same weights
  (`test_refdist_bootstrap_equals_pigeonhole`).
- **R4 two-way random-effects ANOVA on the M × S matrix:**
  - the variance is Var(d̄) = (MS_M + MS_S − MS_E) / (M S), with the numerator floored at MS_E;
  - t with Satterthwaite df on the unfloored combination, or (M − 1)(S − 1) when floored;
  - the floor's frequency is reported.

**Reported per condition and candidate:**

- size at α = 0.05 and at α′ = 0.05 / 36, with Wilson 95 % intervals;
- power at β = Δ at both;
- for R2 and R4, the median standard error over the sd of the estimates;
- for R3, the interval's coverage.

α′ is E8.5's family count. It is re-read at the design's count when section 4 is fixed, from the same cached
p-values, with nothing re-simulated.

**The bridge to Phase 8, before any new rate is read (stage `bridge`).** At M = 6, S = 19, τ = √2 × 0.03, equal
heterogeneity and β = 0, R3 is run on 2,000 datasets per reading. Its size's Wilson interval must overlap the E2 row
of `e8_3/mixed_pp.json`: shared 0.090 [0.058, 0.138], model-specific 0.135 [0.094, 0.189]. **If either does not
overlap,** this process is not Phase 8's. The stage stops, and the discrepancy is reported before `refdist` runs.

**The recommendation rule** (a recommendation; the choice is the team's):

- A candidate **holds size at M** if its size's Wilson lower limit is ≤ α at both α levels in every condition at that
  M.
- **The recommended candidate at the roster's M** is the size-holding one with the highest power at α′ at
  τ = ½ × Flash's limit, S = 93, the model-specific reading and equal heterogeneity.
- If no candidate holds size at that M, none is recommended, and the table goes to the team as it is.

**Stated expectations**, so that disconfirmation is visible:

- R1 over-rejects at small M.
- R2 holds size in the model-specific reading. In the shared reading at τ = 0 it over-rejects, because the shared
  path term moves every model's mean together and s_M cannot see it.
- R3 fails size at M ≤ 6 when τ > 0 (P8-17).
- R4 holds size where R2 fails in the shared reading, at a power cost.

### 3.2 Stage `criteria`: the sign criterion, the model-level test and the equivalence interval at the grid's shape — OPEN

**Fixed now, the questions and the construction:**

- **(i) The sign criterion.** The false "level-dependent" rate when the arm effect is the same at every level (β = Δ
  and β = ½ Δ), across the design's L non-default levels.
- **(ii) The model-level test** at every level, with the reference distribution the team chooses in 3.1, and its
  multiplicity by BY across families.
- **(iii) The equivalence criterion** (plan 13.3 (iii); D12's half, 0.025, from `inference.json` `min_effect`). The
  90 % interval of the level × arm interaction must lie within ± 0.025. Its power at a true interaction of 0, and its
  false-equivalence rate at a true interaction of 0.025, are measured under a level × arm × model sd of 0 and of
  ½ τ (DESIGN).

**OPEN:** L, S per level and M. These come from the design. The stage runs on the fixed design before the first paid
batch of E9.4. **A criterion that cannot be met at the design's shape is reported here, before the grid**, as clause
(i) of E8.4 and "the directive interval covers 0" were in Phase 8.

---

## 4. E9.4 — the grid

### 4.1 Stage 1 — FIXED 11 Sep 2026 (P9-2, P9-3, P9-4, P9-5), before any pilot or grid run

**Roster.** The 13 configurations of P9-2, each as P9-5 configures it, every row logging `Provider_Options`.

**Headline cells.**

- The static and memory arms (`experiments/arms_v2.py`);
- × ISFJ, INTJ, ENTJ;
- × flat, bull_trap, crash (δ 0.70) and sustained_bull;
- the default generator, T = 200, R = 1;
- `harness_version = placebo_version = "v2_1"`, dividends paid, start at the band centre;
- **seeds 10001 … 10000 + S**, the same seeds for every model, persona and scenario, where S is E9.2's derived count
  (`e9_2/sizing.json`).

**The D11 common-start slice (P8-13, P8-14).**

- ISFJ, INTJ, ENTJ × {static, memory, swapped}, plus the NONE `trader` arm, all at `start_design = "common"`;
- the same scenarios and seeds as the headline cells;
- **each model's batch runs it after its headline cells**, so the headline answer is not delayed.

The salience shares are computed only here, with seed-cluster bootstrap intervals that keep every copy of a seed in
one fold (P8-18). The day-1 gate's null stays NOT COMPUTABLE (P8-14).

**The confirmatory family (P8-10), and how a claim is made.**

- **Q1 | C:** memory − static × 3 personas × 4 scenario cells × tier C's three metrics (band-MAS, D at θ 0.05, D at
  θ 0.0020), so **m = 36**. D's two θ are near-duplicates (|r| 0.992), and that is stated beside the count.
- **One confirmatory family,** so BH within the family decides (`inference_params.decision_rule(1)`), and the
  Bonferroni α′ = 0.05 / 36 sizes the design.
- **The model-level test** in each cell × metric is **R5** (P9-4) on the M × S matrix of seed-level differences. Its
  p-value enters BH.
- **Descriptive only:** each model's own contrast interval (the one-way path bootstrap, which is E2 with one model),
  E1 at the better optimum (P8-17), and Cliff's δ.
- **Secondary tier S** (turnover, MDD, return) forms its own families, and nothing in it is a confirmatory claim.

**Wall-clock plan.**

- One manifest per stage, with one process per model at 15 workers, every model at once.
- Checkpointed per run, with progress and ETA lines.
- **The wall-clock spent is reported beside `e9_0/wallclock.csv`'s projection.**

**Not in stage 1**, carried to stage 2's fixing and put to the team with measured timings there:

- the context-length factor (plan 13.2). Smoked on Flash, its levels take 1.04–1.96 × a stateless smoke run
  (`e9_0/smoke/smoke_context_*.json`);
- REG-16 (ii)'s stateful arms, which have no stateful σ_d;
- REG-1, whose rendering switch for fixed start magnitudes is not built;
- REG-9, whose phase-restatement side call at stratified days is not built.

### 4.2 Stage 2 — OPEN

It is fixed after stage 1 is read and before stage 2's first paid run, and must name:

- the roster and each model's configuration (with its smoke);
- the generator settings (section 1's outcome) × personas × arms × scenarios × seeds, with the seed list;
- the context-length cells, if in the design;
- the common-start NONE slice (D11), with its cells re-derived at the seed count;
- REG-1 and REG-9 with their factor lists;
- the families and their counts;
- the wall-clock plan at 10–15 concurrent calls per model;
- the manifest per model with its fingerprint (`tools/phase9/e9_runner.py`), and `test_grid_manifest_matches_runs`.

## 5. E9.5 — the robustness table — OPEN (fixed with 3.2)

## 6. The switch this phase adds, proved inert when off

`RunConfig.provider_options` (default None). When it is set, every row carries the JSON column `Provider_Options`.
When it is not set, the log's columns and values are unchanged:

- `tests/test_v2_1_phase_9.py::test_provider_options_column_inert`;
- the Phase-8 golden record re-checked with the field declared as a Phase-9 addition: 0 differences
  (`tools/phase8/e8_0_golden.py --check`).

## 7. What this phase does not do

- It does not edit the plan, the register or anything under `archive/`.
- It does not change `envs/`, the scoring or the path-hash fixture.
- It does not use the providers' batch APIs.
- It does not raise concurrency above 15 per model.
- It does not shrink a design to fit a budget (P9-1).
