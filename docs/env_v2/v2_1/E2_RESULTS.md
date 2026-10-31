# E2 — the causal package: results

**31 October 2026. Five of six models. Preliminary pending Llama 3.1 8B**, which is re-running under deviation 1 of
`PREREG_PHASE_9_STAGE2_E2.md` and will be added as a sixth family without changing anything below (§3 registers one
BH family per model and no claim about models in general).

Read against `PREREG_PHASE_9_STAGE2_E2.md`. Nothing here was decided after seeing a number: the family, the metrics,
the decision rule, the absorption ratio and both its guards were registered before the array was submitted
(`DECISION_LOG.md` P9-24).

---

## The question, and the answer

E2 asks whether the memory arm works **because of what the mandate says**, or because something is re-injected into
the prompt at every step. If a content-free block matched on length and imperative count reproduces the mandate's
effect, the headline is a negative control and the benchmark measures salience, not mandate content.

**It does not reproduce it.** Across the three placebo arms and 78 admitted cells, the absorption ratio A reaches
0.5 or more — half the mandate's effect, in the mandate's own direction — in **11 cells**. The directive placebo,
the strongest of the three, moves **against** the mandate's direction in 19 of its 26 cells.

**But the placebos are not inert**, and the paper has to say so. A block with no mandate content significantly
changes band-MAS in **69 of 90** model × persona × scenario cells. Those effects are small — median 0.0145, about a
third of the registered Δ of 0.05 — and the design detects them because 60 seeds paired on identical price paths
resolve differences far below Δ. Ten of the 90 reach Δ or more.

So: **injecting something and injecting the mandate are different interventions.** The second does what the
benchmark claims. The first does something smaller, in a direction largely unrelated to it.

## What ran

Array 48276232, 30 Oct 02:36–06:34 UTC, 14.2 B200 GPU-hours at 89.5 % utilisation. Five models × 1,080 runs =
**5,400 runs**, every one verified against `manifest_causal_open.json` (sha256 `e44d9c96f4e45f24…`) for prompt hash,
`Env_Code_Hash` `1d689aaf82a33a2e`, harness and placebo version, configuration tag, scenario, seed and start design:
**1,080/1,080 each, 0 missing, 0 mismatched**. Scored with `evaluation.metrics_v2.score_run(scoring="v2_1")`,
**0 scoring errors**.

Llama 3.1 8B is absent because it stopped at the parse preflight: 4 of its 6 `placebo_directive` calls fell back,
against 12 of 12 clean in the other two arms. The cause is the placebo's own wording — *"State the date first …
in full sentences"*, closing *"Write this decision ONLY in the manner of this procedure"* — which the model obeys
over the JSON contract. That is the placebo working as designed on the smallest model, not a defect.

## The confirmatory analysis

As registered: one family per model, {`placebo_declarative`, `placebo_directive`, `wrapper_only`} − `static`,
× 3 personas × 2 scenarios × 3 tier-C metrics, **m = 54**, BH within the family at q = 0.05, two-way cluster
bootstrap (`pigeonhole_ci`, 1,999 draws, seed 0, one-way by path with a single model).

| model | tests | families | m | rule | claims |
|---|---|---|---|---|---|
| OLMo 3.1 32B | 54 | 1 | 54 | `bh_within` | 45 |
| Phi-4 | 54 | 1 | 54 | `bh_within` | 26 |
| Gemma 4 31B | 54 | 1 | 54 | `bh_within` | 24 |
| Gemma 4 E4B | 54 | 1 | 54 | `bh_within` | 18 |
| Ministral 3 14B | 54 | 1 | 54 | `bh_within` | 15 |

Every model yielded exactly **one** confirmatory family and ran under `bh_within`, the rule E2 registered. That is
not automatic: `run_stats_v21` iterates a fixed dict of question families, so a frame containing `memory` would have
fired Q1 as well as Q3, produced two confirmatory families, and flipped the rule to `by_across`. The confirmatory
frame therefore holds the three placebo arms and `static` only, and `memory` is used solely for the absorption
denominator, on its own frame. Cross-setting key collisions were checked per model before any test ran: none.

By arm, on band-MAS: `placebo_declarative` 20/30 cells, `placebo_directive` 25/30, `wrapper_only` 24/30.
**128 of 270** confirmatory tests are claims in total.

## The absorption ratio

A = ((placebo − static) · s) / |memory − static| on band-MAS, s = sign(memory − static); admitted only where the
denominator's bootstrap CI excludes 0 **and** |memory − static| ≥ 0.01. Both guards and the floor were registered
in §3 before the run. **78 of 90 cells admitted**; the 12 exclusions are all Gemma 4 E4B, whose mandate effect is
below the floor in 6 cells and uncertain in 3, with 3 failing both.

| arm | n | median A | IQR | A > 0 | A ≥ 0.5 | A ≥ 1 |
|---|---|---|---|---|---|---|
| `placebo_declarative` | 26 | **−0.006** | [−0.44, +0.15] | 13 | 4 | 2 |
| `placebo_directive` | 26 | **−0.219** | [−0.38, +0.06] | 7 | 3 | 1 |
| `wrapper_only` | 26 | **+0.039** | [−0.48, +0.33] | 14 | 4 | 0 |

All three medians sit at or below zero. The directive placebo — the one matched on imperative count, the hardest
case — is the most negative: it pushes conformity the opposite way from the mandate in 19 of 26 cells.

A worked cell, to fix the sign convention. **Phi-4, ENTJ, flat, `placebo_directive`**: the mandate effect is
memory − static = **−0.3753**, so memory *improves* conformity by a large margin and s = −1. The placebo effect is
+0.0998, so the placebo *worsens* conformity. A = (+0.0998 × −1) / 0.3753 = **−0.266**. The placebo is not a weak
version of the mandate; it moves the other way.

**24 of the 78 admitted cells have a negative mandate effect** — memory improves band-MAS — which is why the ratio
is sign-aligned. An unsigned A would have averaged cells whose mandate effects point opposite ways; that was
registered in advance on stage 1's first 60 seeds, where 14 of 34 usable denominators were negative.

Magnitudes: the mandate's own |memory − static| has median **0.0213** (range 0.0105–0.3941), and the placebos'
own |placebo − static| has median **0.0113** (range 0.0003–0.0998). The placebos move the metric about half as
far, and not in the mandate's direction.

## Preconditions, reported before any claim is read (§3)

**Parse fallback.** Four of the five models are at 0.0000 % in every cell. **Gemma 4 31B** has fallbacks in 15 of
its 24 cells, cell means **0.008–0.142 %** and a worst single run of **1.5 %** (ISFJ crash, `placebo_directive`).
This is the model that kept 38 parse fallbacks through stage 1, and the fallbacks appear in its **`static`** arm
too — so it is model behaviour, not something the placebos induce. No cell approaches a rate at which the parser
rather than the mandate would be what is measured.

**Zero trade.** Three Gemma 4 E4B cells have runs that never trade: ISFJ crash `wrapper_only` 1.67 %, ISFJ flat
`placebo_declarative` 1.67 %, and **ISFJ flat `placebo_directive` 8.33 %** — 5 of 60 runs. That last cell is the one
precondition exception worth carrying into the write-up: a run that never trades cannot express mandate conformity
through its holdings, and the cell's estimate is diluted by five such runs. Stage 1's comparable figure was 0 for
every model but Llama 3.1 70B at 6.2 %.

**Score errors.** 0 in all 5,400 runs.

## What this does and does not settle

It settles the framing question E2 was built for: on five of six models, the headline is **content attribution**.
A content-free block of matched form does not reproduce the mandate's effect, and the arm that matches it most
closely reproduces it least.

It does not settle:

* **Llama 3.1 8B**, pending, and it is the model least able to hold the output contract under the directive placebo.
* **Whether the small placebo effects are a nuisance or a finding.** 69 of 90 cells move significantly at a median
  of 0.0145. Reading them as "re-injection has its own effect" is an interpretation this experiment did not
  pre-register; it is reported as measured and belongs in the paper as a descriptive fact.
* **Anything about models in general.** §3 is explicit: each model's family is its own, and no pooled claim is made.
* **The other scenarios.** E2 ran flat and crash only.

## Where the numbers are

`docs/env_v2/generated/v2_1/e9_4/stats_e2_causal/` — per model: `*_v21_contrasts.csv` (54 tests with estimate, CI,
p, Cliff's δ, q and family size), `*_v21_families.csv`, `*_v21_variance_components.csv` (the crossed mixed model,
**descriptive only** under P8-17, and several fits sit on a boundary or report a singular random-effects
covariance — the decision path is the bootstrap, not these), `*_preconditions.csv`, `*_absorption.csv`, and
`summary.json`. Produced by `tools/phase9/e9_5_e2_analyse.py`; A by `tools/phase9/e9_absorption.py`, whose unit
tests reproduce planted ratios of 0.25, 0.75, 1.00 and −0.25 and exercise both guards
(`tests/test_v2_1_absorption.py`).
