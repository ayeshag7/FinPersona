# Mechanistic interpretability against the frozen environment — brief

For the author running the M-series. 17 September 2026.

The synthetic environment is finished and frozen. You can design and run the mechanistic experiments against it
without waiting for the LLM grid, and without anyone else in the loop. This brief is the set of constraints that
are **not** discoverable from the code, plus the decisions the team has already taken so you do not have to
re-open them.

The reasoning behind every constraint here is in `docs/reviews/cycle2/`. The single most useful document is
`FinPersona-Bench_Cycle2_Verification_RedTeam_Report_Aug2026.pdf`; section 8.5 is the M-series discussion and
section 4 is the programme adjudication. `litreview_part3.md` has the per-paper mechanistic reading.

---

## 1. Verify the environment before you build anything

```
git checkout synthetic-env-grid
python -m pytest tests/test_v2_freeze.py -q          # 4 passed: the 30 frozen files match the manifest
python -m pytest tests/ -q                            # 49 passed, 2 skipped
python -m tools.path_hashes --out /tmp/ph.json        # 95 configurations hashed
```

`Env_Code_Hash` is **1d689aaf82a33a2e**. Every run row carries it. If your copy reports anything else, stop:
you are not running the environment the paper describes. The same hash is on `main`, and nothing is developed
on this branch that is not also there.

Any path you generate is bit-identical to the one anyone else generates from the same seed. That is the whole
point of the freeze, and it is what lets you work independently.

---

## 2. Running open weights: already supported, but on two different paths

**Behavioural runs** go through the real harness. `agent/llm_factory.make_llm` routes any model name prefixed
`vllm/` to an OpenAI-compatible server:

```
VLLM_BASE_URL=http://localhost:8000/v1   VLLM_API_KEY=EMPTY
python -m experiments.arms_v2 --models vllm/meta-llama/Llama-3.1-8B-Instruct \
    --personas ISFJ ENTJ --arms static memory --scenarios flat --seeds 42 123 456
```

No adapter to write. Stand up vLLM and prefix the name.

**Internals runs cannot use that path** — vLLM's HTTP API returns text, not activations. You need a second,
in-process path (HuggingFace plus `transformer_lens` or `nnsight`). Nothing for this exists in the repo yet:
no `torch`, no `transformer_lens`, no `nnsight`, no `baukit`. It is greenfield, roughly one to two weeks.

### Your acceptance criterion for that second path

**Prompt-hash equality.** The harness logs `Prompt_Hash` and `System_Prompt_Hash` on every row, from
`simulation/provenance.agent_provenance`. Your in-process path must reproduce the same hash for the same
configuration. Check it before you measure anything.

This is not bookkeeping. The objection the M-series exists to answer is "content and position are confounded".
A mechanistic result computed on a prompt that differs from the benchmark's — by a space, a field order, a
format instruction — answers a different question, and a reviewer will say so.

---

## 3. Decisions already taken — do not re-open these

### 3.1 The readout

v2's action is `TargetAllocation.target_cash_share`, a **float**. There is no single-token action enum. The
revision plan and the Cycle 2 report both assume `"action": "` followed by BUY / SELL / HOLD, which is the
**v1** `TradeDecision` schema. That assumption does not hold here.

| | Readout | Status |
|---|---|---|
| M2 direction, M3 mediation | the cash share, continuous | fine — a scalar is all a mediation test needs |
| M4 logit attribution | needs a one-token target and has none | **out of scope** unless run on `action_interface="v1"`, which exists as a factor but changes the task and would have to be declared as a deviation |

Default position: **M4 is out of scope.** It was cut in Cycle 2 anyway, triple-gated on a crash effect that
fails at model level, a mini-class pattern broken by GPT-5-mini, and an LCR mechanism with no cross-model
validity (precision 0.50, recall 0.33, r = 0.13, p = 0.60).

### 3.2 M1 is flat by construction on the stateless arms

Do not run M1 against the default arms. The mandate sits at a fixed position in every call, and the prompt is
near-constant in length across all 200 days, so attention to the mandate span has no time trend to find. Two
independent published results predict exactly this: Li et al. (COLM 2024) show attention decay is **cross-turn
with a within-turn plateau**, and Xiao et al. show attention to early tokens does **not** decay with distance.

M1 becomes meaningful only on the **stateful** arms (`context_mode` rolling / full / summary, windows 5, 20, 50),
where context genuinely accumulates. Those arms exist in `experiments/arms_v2.py` but have never been sized —
they need a pilot first. If you want M1, that pilot is the prerequisite.

If you do run it: exclude the first ~4 sink tokens, and use a **depth-matched** control span. The placebo span
sits at the end of the prompt and is not a matched control for a span near the start.

### 3.3 All-layer intervention, not single-layer

Arghal et al. (ICML 2026) found single-layer activation patching changed the agent's action **0 times out of
456**; all-layer patching works. Use Arditi et al.'s Eq. 4 directional ablation across every layer and position.

Controls, all of them: a random direction of matched norm, a self-patch, and matched pairs and seeds.

### 3.4 Known-answer validation before you touch the mandate

Reproduce a published result with your own stack first — Arditi's refusal direction on Llama-3.1-8B is the
obvious one. Every phase of this programme validated its instruments against a known answer before using them,
and the M-series is the one most exposed to "your tooling was wrong" as a rebuttal.

---

## 4. The M2 validation target, and three traps

M2 extracts a linear mandate-adherence direction (difference in means between guardian-prompted and
commander-prompted activations; Chen et al. average over **response** tokens for extraction and project at the
**last prompt token** for monitoring). It has to be validated against something behavioural. Three obvious
candidates are all wrong:

| Trap | Why it fails |
|---|---|
| **MAS** | `MAS_ISFJ` is identically `1 − mean cash` — the run-level correlation is **−1.000 exactly**. Validating a cash-predicting direction against a cash-defined metric is circular. |
| **The persona classifier** | Trained on days 1–5 rationales from **both** arms with no `Agent_Type` filter and a within-run validation split. Memory-arm rationales echo mandate vocabulary verbatim, so it is a mandate-echo detector, not a measure of persona expression. Every classifier-derived number in the paper is quarantined. |
| **The restatement probe** | On stateless arms the mandate is in **every** prompt, so restatement accuracy sits near 100% and has no variance to validate against. It is worth running **once**, to make the knows-but-violates point (Kruthof: violation coexists with 97% recall), but it cannot serve as a validation target. |

**Use the cash share, or the first action token.** Expect the per-step signal to be noisy: Chen's
within-condition correlations run 0.245 to 0.813, and Arghal found linear probes weak (39% against 70% for an
MLP), so a single direction may be blunt.

---

## 5. What you are working with

**Personas.** ISFJ (conservative, cash band 0.70–0.90), INTJ (balanced, 0.40–0.60), ENTJ (aggressive,
0.00–0.20), NONE (band-free trader), plus the OCEAN vocabulary pair O1_conservative and O2_aggressive. The
guardian-versus-commander contrast for diff-in-means is ISFJ against ENTJ.

**Arms.** `static` (persona only, no per-step block), `memory` (mandate re-injected at the recency position),
`placebo_declarative`, `placebo_directive` (imperative, delimiter and length matched), `wrapper_only` (the
"ACTIVE MEMORY REFRESH" framing with no mandate), `swapped` (the other persona's mandate). The last three are
what separate content from imperative force from position, and they are the behavioural twin of what M2/M3 ask
mechanistically.

**Scenarios.** flat, crash (discount 0.55 / 0.70 / 0.85), bull_trap, sustained_bull.

---

## 6. Obligations

**Pre-register before you look.** State the predictions in the paper, and commit to publishing the null. Cycle
2 made this a binding condition: the M-series is permitted as a post-hoc appendix precisely because it is
pre-registered and null-committed.

**Do not let a mechanistic result reach the paper before the causal package (E2) has run.** E2 — the
directive-placebo, wrapper-only and swapped-mandate arms — decides whether the behavioural effect is content or
imperative force, and therefore what the mechanism is a mechanism *of*. Cycle 2's reject tripwire is explicit:
adding M1–M4 on top of the current claims is an automatic no.

**Position the M-series as mechanistic validation of a behavioural benchmark**, not as new interpretability.
Arghal is the framework precedent; Arditi and Chen supply the recipes; Li supplies the attention measure and
the split-softmax lever. What is unclaimed is the readout — a ground-truth-scored behavioural allocation over a
long rollout — not the method.

---

## 7. One thing to agree jointly, not alone

**The anchor list.** Which open models to instrument depends on where the behavioural effect actually exists,
and Cycle 2's finding is that it is weakest or reversed in the 4–9B tier (Qwen2.5-7B harmful, Gemma-3-4B the
lone ISFJ exception). The useful anchors are 27–70B. You can establish this yourself with M0 — the behavioural
grid on open weights, which runs through the `vllm/` path and costs GPU time rather than API spend — but if you
pick anchors from your own M0 and the main grid later disagrees, the paper carries two inconsistent model sets.

Agree the anchors before committing GPU time to them.
