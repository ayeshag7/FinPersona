# The LLM grid: what runs, at what scale, in what order

Reference note, 17 September 2026. Written after the environment was frozen and the pre-grid build landed
(`main` 40fe8be, `synthetic-env-grid` 2151cb5, `Env_Code_Hash` 1d689aaf82a33a2e).

This is a planning note, not a pre-registration. Nothing here replaces `PREREG_PHASE_9.md`; the stage-1
pre-registration with predictions stated in advance is still to be written, and is item O5 below.

---

## 1. State at the time of writing

| Item | State |
|---|---|
| Generator | Complete and frozen. 30 files under `tests/v2_freeze_manifest.json`; 0 of 95 path configurations moved in Phases 7, 8 and 9, and 0 again across the pre-grid build |
| Sizing | `docs/env_v2/generated/v2_1/e9_2/sizing.json`, `complete: true`. 12 measured configurations, plug-in sigma_d 0.0958 from DeepSeek V4 Flash, alpha' 0.00139, delta 0.05, seeds 120 (Appendix A) or 60 (paired-correct) |
| Grid tooling | `tools/phase9/e9_4_grid.py` with stages `manifest`, `verify`, `score`, `status`; `tools/phase9/e9_launch.py` drives it. Three manifests exist: headline, slice, track_a |
| Arms | 20 in `experiments/arms_v2.py`, including both placebos, wrapper-only, swapped, trader, six stateful variants and context windows 5 / 20 / 50 / full |
| Personas | ISFJ, INTJ, ENTJ, NONE, plus O1_conservative and O2_aggressive on the v2 harness |
| Grid runs | **None.** Stage 1 as first designed priced at $126,000 and was withdrawn |
| Budget | $184.73 of OpenRouter credit. No Anthropic credit. **The first-party bill is unpriced** |

Measured per-run costs, from the provider's own accounting during the Phase 9 pilots:

| Configuration | $/run |
|---|---|
| Qwen3 235B | 0.023 |
| DeepSeek V4 Flash | 0.030 |
| Claude Haiku 4.5 | 0.545 |

---

## 2. Dependencies: what is actually serial

Almost nothing. Every stage runs against the same frozen environment with its own manifest and its own cells,
so the stages do not feed each other. Earlier orderings in discussion were **interpretation** priority, not
gates.

**The four real gates:**

| Gate | Blocks | Why |
|---|---|---|
| E0 dress rehearsal | everything | the `score` stage has never scored a real grid; finding it broken after twelve parallel batches is expensive |
| `e9_runner.fingerprint()` keying fix | E4 Track A only | see section 5 |
| A stateful sizing pilot | E6 context length only | Phase 9 section 7: the stateful arms' sigma_d was never measured, so that stage has no seed count |
| Headline runs exist | the robustness table (E9.5) | the table is a reading of grid runs: one row per conclusion and generator parameter |

**Explicitly not a gate.** The causal package does not gate the headline. It decides how the headline is
written up, not what the headline collects. If the budget covers both, launch them together.

```
E0  ──┬─► E1 headline ──────────► robustness table (also needs E5)
      ├─► E2 causal package ────► decides the write-up
      ├─► E3 slice ─────────────► salience shares
      ├─► E5 sensitivity ───────┘
      ├─► E7 OCEAN
      ├─► [fingerprint fix] ────► E4 Track A
      └─► [stateful pilot] ─────► E6 context length
                                   └─► E9 mechanistic (after E2)
```

---

## 3. The experiments

Scale is quoted at **S = 60 seeds**. Both 60 and 120 are registered in `sizing.json`; 120 is Appendix A's
conservative formula, driven by the plug-in from the least-piloted model (DeepSeek, 48 pairs). Criteria (ii)
and (iii) turn on the number of models, not on seeds: (ii) holds 0.03 to 0.05 of the time at M = 6 against
0.58 to 0.63 at M = 14, while S from 19 to 93 moves either by about 0.05. **Buy models, not seeds.**

Cell arithmetic, for recomputing at other seed counts:

- headline = 3 personas x 2 arms x 4 scenarios x S
- slice = (3 personas x 3 arms x 4 scenarios x S) + (4 scenarios x S for the NONE/trader reference)

| # | Experiment | What it answers | Arms | Runs per model | Models | Depends on |
|---|---|---|---|---|---|---|
| E0 | Dress rehearsal | does the pipeline work end to end | static, memory | ~4 | 1 cheap | — |
| E1 | **Headline** | the main contrast, 3 personas x 4 scenarios | static, memory | 1,440 | all 12 | E0 |
| E2 | **Causal package** | content vs imperative force vs position | placebo_declarative, placebo_directive, wrapper_only | ~1,080 (flat + crash) | 6 | E0 |
| E3 | **Common-start slice** | the salience shares, the only design in which they are identified | static, memory, swapped, + NONE/trader | 2,400 | 6 | E0 |
| E4 | **Track A** | stated vs unstated target, the axis the corpus does not own | static, memory at track=A | 1,440 | 6 | E0 + fingerprint fix |
| E5 | **Parameter sensitivity** | the robustness table; the data-driven six at two levels each | static, memory at non-default generator levels | ~1,440 per level | 6 | E0; the table needs E1 |
| E6 | **Context length** | the decay thesis, levels 5 / 20 / 50 / full | six stateful arms | to be sized | 4 | E0 + a stateful sizing pilot |
| E7 | OCEAN vocabulary gradient | persona-text share against directive share | static, memory on O1/O2 | ~480 | 3 | E0 |
| E8 | Re-injection frequency k-sweep | — | freq arms | small | 3 | E0 |
| E9 | Mechanistic M2 / M3 | does an adherence direction mediate the effect | — (GPU, no API) | — | 1–2 open-weight | M0 coverage + E2 |

Notes on individual entries:

- **E5 is Phase 9's actual purpose.** The data-driven six are the GARCH set, sbar, mu_V, the half-life,
  sigma_V and the jump rate (E9.1). Three reviewer-named parameters fell out: the P/E dispersion, the analyst
  sd and the sentiment loading each move the scripted policies by at most 0.002.
- **E8 is a replication, not a contribution.** Li et al. (COLM 2024) already swept injection probability with
  an MMLU capability-cost axis. Run it small, cite them, do not headline it.
- **E9 stays an appendix**, pre-registered, with the null committed to publication. M1 and M4 were cut in
  Cycle 2 against the stateless architecture; M1 becomes runnable only on the stateful arms, and only if E6
  shows there is decay to instrument.

---

## 4. Build items still open

`MANIFESTS` in `tools/phase9/e9_4_grid.py` holds only `headline`, `slice` and `track_a`.

| # | Item | Size |
|---|---|---|
| M1 | A manifest stage for E2, the causal package | ~1 h, mirrors the track_a stage |
| M2 | A manifest stage for E5, the sensitivity sweep, with per-cell `env_config` for the non-default generator levels | ~2 h |
| M3 | A stateful sizing pilot before E6 | a pilot run, not code |

---

## 5. Backlog

**The `fingerprint()` keying fix, before Track A runs.**

`e9_runner.fingerprint()` builds its probe config from a synthetic cell:

```python
cfg = cfg_for(mc, {"persona": p, "arm": a, "scenario": "flat", "seed": 1}, manifest["subdir"])
```

That dict carries no `factors` key, and `cfg_for` applies factors with `kw.update(cell.get("factors") or {})`,
so the probe falls back to the `FACTOR_DEFAULTS` value `track = "B"`. The real track_a cells carry
`factors: {"track": "A"}`, which makes `system_prompt()` append `track_a_statement(persona)`. Measured prompt
hashes: `7f7a69e0550e85e5` at A against `2cf22a92f78cb5d0` at B.

The manifest therefore stores the B hash while every real run produces the A hash, and `stage_verify`'s check

```python
want_prompt = fp["prompt_hash"].get(f"{key}|{c['persona']}|{c['arm']}")
"prompt_hash": prov.get("Prompt_Hash") == want_prompt
```

is False on every track_a run. The stage still launches, because `verify_fingerprint` recomputes the
fingerprint the same way and is self-consistent; the mismatch appears only when completed runs are compared
against the manifest. So the failure is expensive rather than loud: the money is spent first, and the
provenance check then reports a false alarm on every row.

The map is keyed `f"{key}|{p}|{a}"`, which structurally assumes one prompt per configuration, persona and arm.
Track A is the first grid factor that changes the prompt, so the key needs a component for the
prompt-affecting factors and `stage_verify`'s lookup must match. About an hour, two places and a test.

**This is a latent bug that Track A exposed, not a Track A bug.** `disclose_horizon`, `cost_visible`,
`wording` and `liquidity_condition` all change the system prompt; any of them used as a grid factor hits the
same thing. Fix the keying rather than special-casing `track`.

---

## 6. Open decisions

| # | Decision | Recommendation |
|---|---|---|
| O1 | Seeds: 120 or 60 | **60.** Both registered; halves every cost above |
| O2 | Is the slice inside stage 1 | **No.** Run it after the headline; it is 2,400 runs per model against the headline's 1,440 and answers a secondary question |
| O3 | Roster size M | Buy models, not seeds |
| O4 | Budget | **Price the first-party headline from the pilot ledgers before committing anything** |
| O5 | Stage-1 pre-registration | Required before the first paid call, with predictions stated |
| O6 | alpha' family count | Re-read at the design's own count once stage 1's shape is fixed; the cached p-values allow this without re-simulating |
| O7 | Sonnet 5, Opus 5, Fable 5.1 | In only if Anthropic credit returns; their partial pilots size nothing |

---

## 7. Two things that will bite

**Money, not dependencies, is the serialiser.** E1 at 60 seeds is about $43 per cheap model and about $785 for
Haiku alone, against $184.73 remaining. E1 across all twelve configurations is not affordable on the current
balance by any arrangement.

**Parallelism is bounded by the local machine, not by the providers.** Google, OpenAI and OpenRouter are three
independent rate-limit pools, so models on different providers overlap almost for free, and the wall clock
becomes the slowest single model (Gemini 2.5 Pro at 3,240 s per run) rather than the sum. But Phase 9 recorded
that offline compute starves paid batches on the eight-core laptop, which is why its criteria sweep was timed
to finish before the pilots' first batch landed. The work is I/O-bound, so move the launcher off the laptop.

**Before any cash-shift claim**, report the parse-failure, refusal and zero-trade rates per cell and the
static-arm cash baseline. Cycle 2 made this a precondition, on the evidence of CLQT section 7.11, AI-Trader
and KTD-Fin, where hold rates that looked like choices were reliability artefacts.

---

## 8. Sequencing by decision value

If the budget arrives in pieces rather than all at once:

1. **E0**, always first.
2. **E2**, the causal package. Cheap, and it decides whether E1 is written as a content-attribution result or
   as a negative control.
3. **E1**, the headline, on as many configurations as the budget reaches.
4. Everything else fans out.
