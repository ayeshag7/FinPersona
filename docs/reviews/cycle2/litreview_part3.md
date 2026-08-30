# FinPersona-Bench Cycle-2 Literature Review, Part 3 (mech_interp + gap_sweep_aug2026)

Reviewer: Cycle-2 literature reviewer (independent read; Cycle-1 report opened only after the per-paper sections below were written).
Date: 2026-08-22.

Reading protocol: every PDF was extracted page-by-page with PyMuPDF and read in full (page counts in the header of each section); the two HTML items were parsed with `html.parser` and read in full. Page numbers below refer to the PDF page index (1-based) of the file in `references/`, and `§` to the paper's own section numbering. Quotations are verbatim from the extracted text (minor hyphenation repaired).

Two target claims tested against every paper:

* **ORIGINAL** – the paper's claims as written (MSD formalisation; behaviour-vs-reasoning distinction; decoupled synthetic ground truth; three failure-mode regimes; MAS/CI/RG; model-dependence; 4.4x compounding; "re-grounding is not universally beneficial"; placebo control; Big Five/O3 ablation; injection-frequency ablation; T-calibration; LCR rationale analysis; MBTI-as-vocabulary; selective re-grounding prescription; transfer to other domains; M1–M4).
* **REFRAMED** – the narrowed Cycle-2 claim: "In a fixed synthetic market with stateless single-turn agents, appending an imperative behavioural directive at the recency position shifts trading behaviour toward cash/inaction in a content-modulated way (protective >> growth >> neutral), while a length-matched declarative placebo produces no shift; scored against opposed allocation targets this yields a 17/18 vs 16/18 split."

Cycle-2 fact used throughout: the FinPersona agents are **stateless single-turn callers** (system prompt + one observation per call; the paper's own Eq. 3, p.5: "the agent operates as a stateless predictor ... A_t ~ P_theta(A | Psi_total, O_t)"). There is therefore no accumulating context inside a run, and every "context-accumulation" / "attention decay over turns" mechanism cited by the paper has to be re-examined against that fact.

---

# PART A — references/mech_interp/ (8 items)

## 1. Li, Liu, Bashkansky, Bau, Viégas, Pfister & Wattenberg (2024) — "Measuring and Controlling Instruction (In)Stability in Language Model Dialogs" [file: `Kim_Suzgun_2024_Instruction_Instability.pdf`, 19 pp, read in full]

**(a) Citation / venue.** Kenneth Li, Tianle Liu, Naomi Bashkansky, David Bau, Fernanda Viégas, Hanspeter Pfister, Martin Wattenberg. *Published as a conference paper at COLM 2024* (p.1 header). arXiv 2402.10962 v4. Harvard + Northeastern. **The filename ("Kim_Suzgun") is wrong: no author named Kim or Suzgun appears anywhere in the paper.** The correct short form is "Li et al. (2024, COLM)", which is also how the authors' own revision plan cites it.

**(b) What it does.** Proposes a self-chat protocol: two copies of a chatbot with different system prompts (agent LM s_B, user LM s_A) talk for N=8 rounds; at each round the user turn is replaced by a probe question and a deterministic Python stability function f_B scores the reply (§3.1, p.3–4). Benchmark: 100 hand-curated system prompts in 5 categories (multi-choice, character, format, memorisation, language), 200 random pairs; models LLaMA2-chat-70B and gpt-3.5-turbo-16k (§3.3, App. D). Finding: stability degrades over rounds and the agent even adopts the *user* LM's instruction (Fig. 3A, p.5); gpt-3.5 drops ~10% (App. D, p.18). Mechanism: **attention decay** — π(t) = summed attention from the current token to system-prompt tokens, LLaMA2-7B layer 24 head 11, "within each turn, π(t) remains almost constant, but there are significant decreases across turns" (§4.2, p.7, Fig. 4, p.6); a cone-geometry theory says autoregressive continuation keeps tokens in a low-dim cone (plateau) while user tokens expand it (drop) (§5, App. A). Mitigations: **System-Prompt Repetition (SPR)** "We inject the system prompt with probability 0 <= p <= 1 before each user utterance" (§6.1, p.8), Classifier-Free Guidance, and the proposed split-softmax (Eq. 6, p.8). All three are swept on their strength hyper-parameter and plotted as stability vs **MMLU performance drop** (§6.3, p.9, Fig. 5); 16-turn conversations for this study; SPR "excels in regions with a larger number of turns" while split-softmax is better early (Fig. 6, p.10). RLHF raises attention to the system prompt but does not eliminate decay (App. C).

Verification of the Cycle-1 description: it is correct that this paper (i) is COLM 2024, (ii) runs an SPR baseline that sweeps injection probability p, and (iii) plots an MMLU capability-cost axis. The author list attributed by Cycle 1 ("Kim/Li") is wrong; it is Li et al.

**(c) Findings relevant to FinPersona (with locations).**
* SPR is precisely FinPersona's "memory re-grounding" (p=1 every step) — Li already treat per-turn re-injection of the instruction as a *baseline*, cost it in context tokens ("system prompt repetition consumes a substantial portion of the context window", p.10) and compare intermediate p values (FinPersona's Appendix H frequency ablation k ∈ {1,5,25,100,∞} is the same sweep on a different axis).
* Attention decay is **across turns only**: "The case of the language model completing its input partial sequence is technically equivalent to the agent LM generating answers for a single turn, which displays a plateau in π(t)" (§4.2, p.7). FinPersona's static arm *is* the single-turn case. Li's own mechanism therefore predicts **no attention decay** inside FinPersona's stateless prompt.
* Li measure attention to the *whole* system prompt, not to an instruction sub-span, and report one head; the authors' M1 plan adopts this measure.
* Li's theory attributes decay to out-of-distribution *user* tokens expanding the cone; FinPersona's user message is a numeric observation table that changes every step, so if anything varies it is attention as a function of observation content, not time.

**(d) ORIGINAL claims.** *Anticipates / partially anticipates*: "instructions lose influence over long interaction" (MSD informal motivation); re-injection as a remedy (SPR); frequency ablation (p-sweep); capability cost framing; model-dependence (two models). *Contradicts*: the claim that the static stateless arm suffers from context-induced decay ("as market context accumulates", abstract) — Li's plateau result says single-turn attention to the prompt does not decay. *Irrelevant to*: synthetic market, MAS/CI/RG, MBTI, 4.4x, placebo.

**(e) REFRAMED claim.** Partially anticipated in method (re-injecting the instruction immediately before generation raises compliance; SPR Fig. 6) but in a multi-turn regime with accumulating context; Li has no content-matched placebo arm and no content-modulated (protective vs growth) comparison. Does not contradict the reframed claim.

**(f) Cite?** Yes, mandatory — and the paper already cites it as "Li et al. 2024" in the revision plan but **not** in the current manuscript's reference list (checked: the current paper cites Liu et al. 2024 and Peysakhovich & Lerer 2023 for recency, not Li). Differentiation sentence: "Li et al. (2024) show that attention to a system prompt decays across dialogue turns and that repeating the system prompt before each user turn (SPR) restores compliance; our agents are stateless single-turn callers, so we do not claim cross-turn attention decay, and we use per-step directive injection as a probe of how directive content modulates an otherwise fixed prompt."

**(g) Cycle-1 check.** Cycle 1's substance is right (SPR p-sweep, MMLU axis, COLM); its author attribution "Kim/Li" is wrong and presumably inherited from the filename. Cycle 1 did not (as far as the filename-level description goes) flag that Li's within-turn plateau is directly at odds with a stateless-decay story; that is the single most important implication of this paper for FinPersona.

---

## 2. Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee & Nanda (2024) — "Refusal in Language Models Is Mediated by a Single Direction" [40 pp, read in full]

**(a)** NeurIPS 2024 (p.1 footer); arXiv 2406.11717 v3.

**(b)** 13 open chat models (Qwen 1.8–72B, Yi 6/34B, Gemma 2/7B, Llama-2 7/13/70B, Llama-3 8/70B; Table 1, p.3). Difference-in-means between harmful (128 train / 32 val) and harmless instructions at each layer and each *post-instruction* token position; select one vector by bypass/induce/KL scores (§2.3, App. C). Interventions: activation addition at one layer (Eq. 3) and **directional ablation at every layer and position** (Eq. 4, p.4). Results: ablation removes refusal (Fig. 1), addition induces it on Alpaca (Fig. 3); weight orthogonalisation is an equivalent white-box jailbreak with < 1% change on MMLU/ARC/GSM8K (Table 3, p.7; App. G). §5 (p.8–9): adversarial suffixes suppress the refusal direction at the last token (Fig. 5) and "hijack" the top-8 heads' attention from the instruction region to the suffix region, **controlled against a random suffix of the same length** (Fig. 6b). Limitations (p.10): "existence proof", "semantic meaning of these directions remains unclear".

**(c) Relevance.** (i) Template for M2/M3: contrastive diff-in-means + ablation/addition, all-layer all-position ablation, KL-based selection to avoid collateral damage. (ii) The suffix analysis is a ready-made design for FinPersona's *placebo vs mandate at the recency position*: a random length-matched suffix (Arditi's control) vs a content suffix, measured by (a) projection onto a behaviour direction at the last token and (b) attention from the last token to instruction vs suffix regions. (iii) Important caveat for M2: the extracted direction is selected by its causal effect on a *binary token-level* behaviour (refusal prefix tokens, App. B); FinPersona's target is a continuous cash fraction inside a JSON schema; the first action token (BUY/SELL/HOLD) is usable, the quantity q is not.

**(d) ORIGINAL.** Irrelevant to the behavioural claims; *anticipates methodologically* the placebo logic (random-suffix control) and the M2/M3 programme. **Note:** Arditi's system-prompt result (App. F.2, Table 7, Fig. 19: Llama-2 ASR 30.0±23.3% across 12 system prompts vs Qwen 76.7±5.9%) shows system-prompt sensitivity is strongly family-dependent — a confound for any "model-dependence of MSD" claim that treats the system-prompt mandate as equally salient across families.

**(e) REFRAMED.** Bears on it methodologically: shows that appended text at the recency position can shift both attention and the projection on a behaviour direction even when it carries no semantic content that a human would call an instruction (adversarial suffix) while *random* suffixes do not — i.e. the "length-matched placebo produces no shift" pattern has a mechanistic precedent, and the interpretation "content matters" is consistent with Arditi.

**(f) Cite?** Yes for M2/M3. Differentiation: "Following Arditi et al. (2024) we extract a difference-in-means direction from contrastive persona prompts and test it by ablation/addition; unlike refusal, our target behaviour is a continuous allocation, so we read out the first action token only."

**(g) Cycle-1 check.** Nothing specific to verify; the paper is cited by the revision plan correctly.

---

## 3. Chen, Arditi, Sleight, Evans & Lindsey (2025) — "Persona Vectors: Monitoring and Controlling Character Traits in Language Models" [63 pp, read in full]

**(a)** arXiv 2507.21509 v3 (Sep 2025), preprint; Anthropic Fellows Program / UT Austin / Anthropic.

**(b)** Automated pipeline: trait name + description → Claude 3.7 Sonnet generates 5 contrastive system-prompt pairs, 40 questions (20 extraction / 20 eval), a 0–100 judge rubric (GPT-4.1-mini judge; 94.7% human agreement, App. B.2). Vector = mean residual activation over **response tokens** with positive vs negative prompts (App. A.3 shows response-avg > prompt-last > prompt-avg for steering). Models: Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct (§3.1). Results: steering induces traits (Fig. 3); **monitoring**: projection of the last prompt token onto the vector correlates r = 0.75–0.83 with subsequent trait expression across system-prompt strengths (Fig. 4, p.5) but only 0.245–0.813 within-condition (App. C.2, Table 2, p.31); finetuning shifts correlate r = 0.76–0.97 with trait change (§4.2); inference-time vs preventative steering (§5; MMLU cost); projection-difference data screening (§6). App. J.2: steering beats negative system prompts; App. J.7.2: "preventative prompting" ≈ steering coef 0.5. App. M: SAE decomposition (BatchTopK SAEs on Qwen2.5-7B, 131k features). Limitations (§8): supervised, trait must be inducible by system prompt, single-turn question evals.

**(c) Relevance.** (i) Directly the recipe for M2 ("mandate direction"): contrast ISFJ/guardian vs ENTJ/commander prompts, average over response tokens, pick most informative layer by steering. (ii) Fig. 4 is the key counter-evidence to the "mandate loses influence" story: in a *single-turn* call, system-prompt content is strongly encoded at the last prompt token *before generation* and linearly predicts behaviour. For a stateless agent the system-prompt mandate is therefore present and readable at every step; what changes across steps is only the observation. (iii) Within-condition correlations are modest → a per-step "drift signal" from projections (revision plan: adaptive controller trigger) will be noisy. (iv) App. J.2 (steering > negative system prompt) suggests a cleaner M3 than re-injection.

**(d) ORIGINAL.** Partially anticipates "behaviour vs language dissociation" concerns? No — but it gives the standard tool. *Contradicts* (in spirit) the claim that the system prompt's behavioural instruction fades in a stateless call. Irrelevant to market/metrics.

**(e) REFRAMED.** Consistent: content of an instruction placed in the prompt shifts behaviour monotonically with its strength (Fig. 4 uses 8 graded system prompts). FinPersona's graded effect (protective >> growth >> neutral) is a coarse version of the same thing.

**(f) Cite?** Yes. Differentiation: "Chen et al. (2025) monitor trait expression from last-prompt-token projections in single-turn QA; we ask whether the same projection tracks a continuous trading allocation across market regimes and whether it mediates the directive-injection effect."

**(g) Cycle-1 check.** n/a (not a drift paper). Flag for the authors: the revision plan says "Chen et al. ... monitored the projection during generation" — Chen monitor at the *last prompt token* (before generation) and average over response tokens for extraction; fine but imprecise.

---

## 4. Hong, Troynikov & Huber (2025) — "Context Rot: How Increasing Input Tokens Impacts LLM Performance" [Chroma technical report, HTML, read in full]

**(a)** Chroma Technical Report, July 14 2025 (bibtex in page). Not peer-reviewed.

**(b)** 18 models (Claude Opus 4/Sonnet 4/3.7/3.5/Haiku 3.5, o3, GPT-4.1/mini/nano/4o/4-Turbo/3.5-Turbo, Gemini 2.5 Pro/Flash/2.0 Flash, Qwen3-235B/32B/8B). Tasks: NIAH extensions (needle–question similarity; 1 vs 4 distractors; needle–haystack similarity; shuffled vs coherent haystack; 8 input lengths × 11 positions; GPT-4.1 judge >0.99 aligned), LongMemEval (306 prompts, ~113k tokens full vs ~300 focused), Repeated Words (25–10,000 words). Findings: degradation with input length on every task; lower needle–question similarity degrades faster; distractors non-uniform; shuffled haystacks *help*; "we find no notable variation in performance for this specific NIAH task" across needle positions; Claude models abstain under ambiguity; "We also do not explain the mechanisms behind this performance degradation".

**(c) Relevance.** FinPersona's intro (p.1) cites this for "as context grows, models become worse at following their instructions". Hong measure *retrieval/QA and copy tasks at thousands to 100k+ tokens*, not instruction adherence, and the haystacks are irrelevant text. FinPersona's per-step prompt is ~1–2k tokens with no growth. So the citation supports only a generic "long inputs hurt" sentiment and cannot motivate decay in a stateless 200-call loop.

**(d) ORIGINAL.** Mis-used as motivation for MSD; irrelevant to every specific claim. **(e) REFRAMED.** Irrelevant (no growing context). **(f) Cite?** Optional, as generic background only; remove the phrase "worse at following their instructions" or re-attribute to Li/SEQUOR/Multi-IF which actually measure instruction following. **(g) Cycle-1 check.** none.

---

## 5. Liu, Lin, Hewitt, Paranjape, Bevilacqua, Petroni & Liang (2024) — "Lost in the Middle: How Language Models Use Long Contexts" [18 pp, read in full]

**(a)** TACL 12:157–173 (2024); arXiv 2307.03172 v3.

**(b)** Multi-document QA (NQ-Open, 2,655 queries; 10/20/30 docs ≈ 2k/4k/6k tokens) and synthetic KV retrieval (75/140/300 pairs, up to ~16k tokens); models MPT-30B-Instruct, LongChat-13B-16K, GPT-3.5-Turbo(-16K), Claude-1.3(-100K), GPT-4 subset, Llama-2 7/13/70B (App. E). **U-shaped curve: primacy and recency** (Fig. 1, Fig. 5, p.5); extended-context variants no better; query-aware contextualisation fixes KV retrieval but not QA (§4.2); base vs instruct both U-shaped (§4.3); "only the larger models (13B and 70B) exhibit the U-shaped performance curve ... the smallest Llama-2 models (7B) are solely recency-biased" (App. E, p.16).

**(c) Relevance.** FinPersona (§3.2, p.5 and App. B) cites Liu for placing the mandate "immediately before generation ... leverages the LLM's recency bias". Liu's result is (i) about *retrieving a fact*, not obeying an instruction; (ii) a U-shape: the **beginning** of the context (where FinPersona's system prompt and mandate already sit) is equally privileged for models ≥13B; (iii) at FinPersona's prompt lengths there is hardly a "middle". Hence Liu does not predict that a system-prompt mandate is under-weighted, and cannot by itself predict that the appended copy is more salient than the original (ContextEcho App. I, below, is the better citation for "user-turn placement beats system-prompt placement").

**(d) ORIGINAL.** Irrelevant to the market claims; cited for the recency rationale with partial mismatch. **(e) REFRAMED.** Weakly relevant: a recency-position effect exists in Liu, but the reframed claim's content modulation is orthogonal. **(f) Cite?** Keep, but reword: "Liu et al. (2024) report both primacy and recency advantages; we place the directive last so that it is the most recent span before generation." **(g) Cycle-1 check.** none.

---

## 6. Meng, Bau, Andonian & Belinkov (2022) — "Locating and Editing Factual Associations in GPT" (ROME) [35 pp, read in full]

**(a)** NeurIPS 2022; arXiv 2202.05262 v5.

**(b)** **Causal tracing**: clean run / corrupted run (Gaussian noise on subject-token embeddings, ν = 3σ) / corrupted-with-restoration of a single hidden state; average indirect effect over 1,000 facts on GPT-2 XL (also GPT-J, NeoX, GPT-2 M/L; App. B.3). Finds an early site (mid-layer MLP at the last subject token) and a late site (attention at the last token) (Fig. 2, p.3). ROME = rank-one edit of one MLP's W_proj (Eq. 2); COUNTERFACT dataset (21,919 records); comparison with FT, FT+L, KE, MEND, KN (Table 4); human eval; App. B.4: "Integrated Gradients ... does not yield the same insights" (p.17, Fig. 16); App. I: editing attention (AttnEdit) gives regurgitation not generalisation.

**(c) Relevance.** M4 in the revision plan says "Meng et al. (2022) localized effects with activation patching and direct logit attribution". **ROME uses causal tracing (activation patching) only; there is no direct logit attribution in the paper** (DLA comes from the Transformer-Circuits framework / logit-lens lineage, and is used e.g. in Templeton et al. 2024 as "attribution"). Causal tracing on FinPersona would mean: corrupt the *mandate span* tokens (noise), then restore single hidden states to see which layer/position restores the SELL/HOLD logit — feasible on open models once a clean 1-token readout exists (first token of the action enum after `"action": "` under the Pydantic schema). The quantity q (a float) is not a one-token target. ROME's noise-corruption of a named-entity span translates awkwardly to a 40-token imperative directive; Arditi's directional ablation is a cleaner lever.

**(d) ORIGINAL.** Irrelevant to behavioural claims; tool for M4. **(e) REFRAMED.** n/a. **(f) Cite?** Yes if M4 is done, but as "causal tracing / activation patching", and cite a DLA source separately. **(g) Cycle-1 check.** Not a Cycle-1 item; flag the revision plan's mis-citation.

---

## 7. Templeton et al. (2024) — "Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet" [Transformer Circuits Thread, HTML, read in full]

**(a)** Transformer Circuits Thread, 21 May 2024 (Anthropic). Not peer-reviewed.

**(b)** Sparse autoencoders with 1M/4M/34M features on the middle-layer residual stream of Claude 3 Sonnet (production finetuned model); scaling-law-guided training; features multilingual/multimodal; steering by clamping feature activation (outside observed range, "typically ... between −10 and 10" × max); safety-relevant features (code vulnerability, bias, sycophancy, deception, secrecy, "internal conflict", dialogue/assistant-persona feature whose −2× clamp sheds the persona); **attribution** (gradient of logit-difference dotted with feature vector × activation; attribution–ablation correlation ≈ 0.81 vs 0.12 for activation–ablation); comparison with few-shot difference-in-means steering vectors: "In two examples ... few-shot steering vectors were similarly effective ... In five examples ... we were able to usefully steer model outputs with features but not few-shot steering vectors"; limitations: cross-layer superposition, dictionaries incomplete (≈60% of London boroughs), shrinkage, compute.

**(c) Relevance.** The revision plan lists "SAE features (Templeton et al., 2024) instead of a single direction" as the M2 alternative. Caveats: (i) Templeton's SAEs are on a proprietary model; FinPersona's open anchors (Llama-3.1-8B, Gemma-2-9B, Qwen2.5-7B, Gemma-3-4B) would need their own SAEs (Chen et al. App. M trained BatchTopK SAEs on Qwen2.5-7B; public releases such as Gemma Scope exist but are outside this corpus). (ii) Attribution (as used in Templeton) is the DLA-style tool the M4 text actually needs (not ROME). (iii) Templeton's own "assistant persona" feature and the "few-shot steering vector vs SAE feature" comparison warn that a single diff-in-means "adherence direction" may be a blunt instrument.

**(d)–(e)** Irrelevant to the behavioural claims and to the reframed claim. **(f) Cite?** Only if an SAE analysis is actually run; otherwise drop from the mech-interp citations. **(g)** none.

---

## 8. Xiao, Tian, Chen, Han & Lewis (2024) — "Efficient Streaming Language Models with Attention Sinks" [21 pp, read in full]

**(a)** ICLR 2024; arXiv 2309.17453 v4.

**(b)** Observation: "a surprisingly large amount of attention score is allocated to the initial tokens, irrespective of their relevance" (p.2); Llama-2-7B attention maps (Fig. 2): beyond the first two layers "the model heavily attends to the initial token across all layers and heads"; replacing the first 4 tokens with "\n" restores perplexity (Table 1, p.5) → positional, not semantic; 4 sink tokens suffice (Table 2); for 4,096-token sequences "the attention scores for the first token are significantly high, often exceeding half of the total attention, except for the two bottom layers" (App. F, p.18, Fig. 12); holds for Llama-2-70B (App. G), BERT [SEP] (App. H); StreamingLLM; sink-token pretraining. App. C: accuracy collapses once the answer leaves the cache — StreamingLLM does not extend memory.

**(c) Relevance.** For M1 (attention mass on the mandate span): FinPersona's mandate lives inside the system prompt near the start of the sequence, so raw attention mass to it is inflated by the sink and should be computed **excluding the first ~4 tokens** and compared with a matched non-mandate span (the revision plan's "attention-sink control" is the right instinct; the placebo span sits at the *end*, which is not a matched control for a start-of-sequence span). Also: Xiao show that attention to initial tokens does **not** decay with distance (App. E/F) — in a stateless prompt there is no mechanism for "salience decay" of early tokens at the attention level.

**(d)–(e)** Irrelevant to behavioural claims and to the reframed claim. **(f) Cite?** Yes for M1 methodology. **(g)** none.

---

# PART B — references/gap_sweep_aug2026/ (11 items)

## 9. He, Jin, Wang, Bi et al. (Meta GenAI, 2024) — "Multi-IF: Benchmarking LLMs on Multi-Turn and Multilingual Instructions Following" [arXiv 2410.15553 v2, 23 pp, read in full]

**(a)** arXiv preprint, 13 Nov 2024 (v2); Meta GenAI.

**(b)** Expands IFEval into 4,501 three-turn conversations in 8 languages; verifiable instructions; 14 models (o1-preview/mini, GPT-4/4o, Llama 3.1 8/70/405B, Gemini 1.5 Pro/Flash, Claude 3.5 Sonnet/3 Sonnet/3 Haiku, Qwen-2.5 72B, Mistral Large 2); metric = mean of 4 accuracies; cumulative context ("the preceding turns' prompts and responses are concatenated", p.8). Results: every model degrades per turn — "o1-preview drops from 0.877 at the first turn to 0.707 at the third turn" (abstract; Table 1); Instruction Forgetting Ratio (IFR, Eq. 1) and Error Correction Ratio; "the IFR rates from turn 1 to turn 2 are generally higher than the IFR rate from turn 2 to turn 3" (§5.2, p.11); Llama scaling reduces IFR; Gemini false refusals (App. C).

**(c) Relevance.** Prior art for "instruction adherence degrades as the interaction lengthens" — but (i) multi-turn with accumulating context, (ii) instructions accumulate (each turn adds a new constraint), (iii) the drop is largest at the first transition and then flattens — i.e. *not* compounding. For FinPersona: supports the general phenomenon, but the stateless design removes both drivers (accumulated context and accumulated constraints).

**(d) ORIGINAL.** Partially anticipates "mandate adherence decays over steps" (framing only), model dependence; *mildly contradicts* the "compounds over time" emphasis (Multi-IF's degradation is front-loaded). **(e) REFRAMED.** Irrelevant (no directive re-injection, no placebo). **(f) Cite?** Yes, in related work as the verifiable multi-turn-IF precedent; differentiation: "Multi-IF measures decay across accumulating turns and constraints; our agents receive a fixed prompt per step." **(g)** Cycle-1 manifest statement ("monotonic per-turn instruction degradation; o1-preview 0.877 -> 0.707") is accurate; "monotonic" is true over 3 turns but the increments shrink.

---

## 10. Everitt, Gârbacea, Bellot, Richens, Papadatos, Campos & Shah (2025) — "Evaluating the Goal-Directedness of Large Language Models" [arXiv 2504.11844 v1, 41 pp, read in full]

**(a)** arXiv preprint 16 Apr 2025; Google DeepMind / U. Chicago / SaferAI.

**(b)** Defines capability-conditioned goal-directedness GD = (E[R_π]−E[R_π0])/(max_{π*∈Π_c}E[R_π*]−E[R_π0]) (Def. 3.1, p.3), estimating the capability ceiling from subtask performance via Monte-Carlo (Alg. 1–4). Blocksworld tasks (Information Gathering, Cognitive Effort, Plan & Execute, Combined); 8 models (Gemini 1.5 Flash/Pro, 2.0 Flash, GPT-3.5/4-turbo/4o, Claude 3.7 Sonnet/3.5 Haiku), 30 seeds × 3/4/5 blocks. Findings: no model fully goal-directed (§4.1); models take fewer measurements when estimation is part of a larger task (Fig. 4); "Goal-directedness is distinct from task performance and context length deterioration" (§4.2) — App. E steps subtasks through the same growing context and finds "context length deterioration is not the full explanation"; GD consistent across tasks (§4.3); motivational/demotivational system prompts ("Really go for it." / "your answer doesn't matter") shift performance "somewhat" but "far from" full use of capability (§4.4, Fig. 9).

**(c) Relevance.** (i) Conceptual ally for separating *propensity* from *capability* — but note that FinPersona never measures capability; Everitt's whole method is to normalise by a measured capability ceiling. (ii) App. E is evidence **against** context-accumulation as the driver of under-use of an instruction (the Gemini models do about as well with the long stepped context as with isolated subtasks). (iii) §4.4 is a precedent for "injected motivational text in the system prompt changes behaviour only partially".

**(d) ORIGINAL.** Partially anticipates "behavioural failure distinct from reasoning/capability error"; partially contradicts the context-accumulation mechanism. Irrelevant to market specifics. **(e) REFRAMED.** Weakly consistent (prompted directives shift behaviour). **(f) Cite?** Yes, for the propensity-vs-capability framing; differentiation: "Everitt et al. normalise by measured capability; we do not measure capability and therefore cannot claim a capability-independent construct without an analogous control." **(g)** Cycle-1 manifest ("distinct from task performance AND from context-length deterioration. Supports MSD ≠ capability") is accurate on the first two points; "supports MSD ≠ capability" is an over-reach — Everitt's result cuts the other way on the *mechanism* (it shows degradation that is not caused by context length).

---

## 11. Bao, Zhang, Jing, Yuan, Shi & Ye (Notre Dame, 2026) — "DRIFT-BENCH: Diagnosing Cooperative Breakdowns in LLM Agents under Input Faults via Multi-Turn Interaction" [arXiv 2602.02455 v1, 65 pp, read in full]

**(a)** Preprint, 2 Feb 2026 (ICML-style template).

**(b)** Taxonomy of input faults (intention/premise/parameter/expression, §2); tasks from AgentBench OS/DB (state-oriented, 200) and StableToolBench G1 (service-oriented, 150), oracle-filtered; 5 clarification actions; 5 GDMS user personas (Rational, Intuitive, Dependent, Avoidant, Spontaneous) for the *user simulator* (§3.3); RISE metrics; 7 agent models (GPT-5.2, GLM-4.7, Gemini-2.5-Flash, GPT-OSS-120B, Qwen3, DeepSeek-v3.2, Llama-4). Results: ≈40–50% PD in state-oriented tasks (Table 2); "Clarification Paradox" (helps white-box, hurts black-box, e.g. Gemini-2.5-Flash service-oriented collapses to ~2% with clarify, Table 8); SAR ≈29% for premise/parameter faults ("in over 70% of cases ... agents proceed with execution", p.8); Avoidant persona hardest (Table 5).

**(c) Relevance.** Essentially none: "drift" here is task drift under flawed user instructions; "persona" is the simulated *user's* decision style, not the agent's; no mandate, no re-injection, no long horizon. Its only tangential points: (i) execution bias (acting rather than deferring) as a systematic agent tendency; (ii) "Clarification-Induced Contextual Hallucination ... extra dialogue turns can introduce linguistic noise" (App. F.1.2) — a multi-turn context effect. **Name collision** with Kruthof's DriftBench (item 16) must be handled if either is cited.

**(d)/(e)** Irrelevant. **(f) Cite?** No (at most a footnote to disambiguate "DriftBench"). **(g)** Cycle-1 manifest (Tier C, "cooperative breakdown under input faults; name collision") is accurate.

---

## 12. Arghal, Chen, Dalton, Kortukov, McNamara, Nalmpantis, Nirvaan, Sarti & Giulianelli (2026) — "A Behavioural and Representational Evaluation of Goal-Directedness in Language Model Agents" [arXiv 2602.08964 v2, 18 pp, read in full]

**(a)** ICML 2026 (PMLR 306, p.1 footer); v2 29 May 2026.

**(b)** GPT-OSS-20B navigating MiniGrid (7–15 grids, 6 densities, 10 trajectories each, T=0.7); behavioural metrics vs A* optimal (accuracy, entropy, JSD); iso-difficulty transforms → no significant differences (Table 3); instrumental/implicit goals: 100% success with key-door, but a useless key attracts 75% of non-optimal moves and 17% pickups (Table 1). Representational: MLP probes decode a coarse cognitive map (~70%; linear probes 39%, "environment information is encoded non-linearly", §5.1); goal/agent localisation coarse (Manhattan < 2); **map decodability drops after reasoning** (75%→60%); actions 82.5% consistent with decoded beliefs; one-shot plan decoder; **activation patching: single-layer patches change the action 0/456 times; all-layer patching always works** (§5.2, App. F).

**(c) Relevance.** This is the precedent for exactly the "behavioural + representational" framework M1–M4 propose, and it reports two practical warnings: (i) linear probes can be weak in agentic settings (relevant to M2's single linear direction); (ii) single-layer interventions may be inert (relevant to M3 layer choice; Arditi's all-layer ablation sidesteps this). Also a precedent for *distractor-driven* deviation from the stated goal (the useless key) — behavioural "drift" caused by a salient goal-like cue rather than by forgetting, i.e. closer to KBV than to decay.

**(d) ORIGINAL.** Framework precedent for M1–M4 (so the framework itself is not novel); supports "behaviour can deviate from stated goal without capability failure". **(e)** Irrelevant. **(f) Cite?** Yes if M-series is kept: "Arghal et al. (2026) pair behavioural evaluation with probing and find single-layer patching ineffective; we therefore intervene across layers (Arditi et al.)." **(g)** Cycle-1 manifest ("framework precedent for combining behavioural eval with probing") accurate.

---

## 13. Sawant (2026) — "High-Stakes Personalization: Rethinking LLM Customization for Individual Investor Decision-Making" [arXiv 2604.04300 v1, 5 pp, read in full]

**(a)** Position paper, single author ("AI Researcher", gmail address), 5 Apr 2026, not peer-reviewed, no experiments.

**(b)** Describes INVESTMATE (living thesis, conviction deltas, drift detection, behavioural memory) and four axes: behavioural memory complexity; **thesis consistency under drift** ("A stateless LLM will generate a bearish assessment anchored to recent evidence", §4.2, p.3; "watching models latch onto recency rather than the thesis that justified a position weeks ago", §1); style–signal tension; **alignment without ground truth** (§4.4). Conviction scores that were "unconstrained LLM-generated" "drifted unpredictably" and were replaced by fixed deltas (§3.2).

**(c) Relevance.** Informal prior statement of both the problem (recency-anchored stateless generation vs a standing thesis) and the evaluation gap (no ground truth) that FinPersona attacks with a hidden fundamental value. No data.

**(d)** Anticipates the *framing* of MSD and of "decoupled ground truth" as a need; nothing quantitative. **(e)** Its "stateless ... anchored to recent evidence" remark is exactly the regime of the reframed claim and is consistent with it. **(f) Cite?** Optional one-liner in related work ("Sawant (2026) argues informally that stateless assistants anchor on recent evidence rather than standing mandates"). **(g)** Cycle-1 manifest accurate ("position paper ... single author, not peer reviewed").

---

## 14. Saxena, Pangallo, Hommes, Caccioli & del Rio-Chanona (2026) — "Machine Spirits: Speculation and Adaptation of LLM Agents in Asset Markets" [arXiv 2604.18602 v2, 46 pp, read in full]

**(a)** arXiv 29 Apr 2026 (q-fin.TR); UCL / Turin / Bank of Canada / Amsterdam / LSE / CSH.

**(b)** Recreates Hommes et al. (2008) learning-to-forecast markets: 6 agents, 50 periods, p_t = (mean forecast + ȳ)/(1+r), fundamental p_f = ȳ/r = 60 *known in principle to agents* (ȳ=3, r=5% disclosed), cap 1000; 15 LLMs (Table 1) at temperature 1, memory = 2 own prior responses; metrics RD, RDMAX, IQR, P_bubble, SPEC, BIAS (Mincer–Zarnowitz). Three groups (Table 2, p.11): bubble-formers (o3-mini, OLMO-Think, Qwen3-14B, Qwen3-32B 40%, o3), non-bubble but biased (7 models), REH-consistent (GPT-5 Mini, Gemini-2.5/3-Flash). Mixed 6-LLM market gives 50% bubbles with varied macro regimes (Fig. 2); 5×Qwen3-14B + 1 frontier: frontier switches from fundamentalist to trend-following; Gemini-3-Flash exploits (earnings 535.5 vs 320.1) and amplifies volatility (§3.3); data leakage audit (§3.4); **robustness to memory 0/2/4 and temperature 0.3/0.7/1.0 (Table 6, p.35)**; reasoning toggle on Qwen3-14B causally produces bubbles (App. B.5).

**(c) Relevance.** (i) The closest thing in my share to a *competitor* on "objective ground truth for LLM trading agents": a market with a mathematically defined fundamental value, multiple LLMs, speculative vs rational classification. Differences: the fundamental is disclosed (FinPersona hides V_t); price is endogenous to agents' forecasts (FinPersona's price is exogenous); no personas/mandates; forecasting not allocation. (ii) Robustness to the memory parameter (0 vs 2 vs 4 prior responses, Table 6) is direct evidence that in this market the amount of accumulated own-history does not change macro behaviour — consonant with a stateless-agent regime producing the same behaviour as a lightly-stateful one. (iii) Strong model dependence of market behaviour (bubble vs fundamentalist) is established at scale.

**(d) ORIGINAL.** Partially anticipates "decoupled synthetic ground truth" (known fundamental enables falsifiable evaluation of value-rationality; their SPEC/BIAS tests play the role FinPersona's RG plays) and "model-dependence"; irrelevant to MSD/re-grounding. **(e)** Irrelevant to the directive-injection claim. **(f) Cite?** Yes — in "Static Benchmarks and Subjective Simulations": "Saxena et al. (2026) evaluate 15 LLMs in Hommes-style markets with a known fundamental value and find model-specific 'machine spirits'; we instead hide the fundamental, fix the price path, and study single agents under behavioural mandates." **(g)** Cycle-1 manifest ("15 LLMs in a market with explicit fundamental value; bubbles vs fundamental coordination") accurate.

---

## 15. Ross & Lo (MIT, 2026) — "One Size Fits None: Heuristic Collapse in LLM Investment Advice" [arXiv 2604.23837 v1, 13 pp, read in full]

**(a)** Preprint 26 Apr 2026; MIT CSAIL / Sloan.

**(b)** 1,000 Latin-hypercube synthetic client profiles (age, income, savings, debt, dependents, risk tolerance, experience, timeline, education, marital status; Table 3); 20-product menu; GPT-4o, GPT-5.4 Nano/Mini/5.4; structured outputs; surrogate RF/Ridge per asset class; feature concentration FC (HHI of normalised importances, Eq. 3); HHI/Jaccard for diversification/personalisation; web-search condition; LLM-judge rationale comparison. Key finding (p.5): "recommendations follow a simple heuristic: aggressive clients receive equities, conservative clients receive bonds, **with self-reported risk tolerance accounting for 57–88% of predictive weight** and minimal integration of income" — **verified verbatim**; per-asset shares in Tables 6–9 (GPT-4o equities 88.2%, fixed income 74.4%, cash 82.4%; GPT-5.4 equities 55.3%). **Input-sensitivity criterion** (§2, p.2): "whatever the correct mapping from client profile to portfolio, it should not be well-approximated by a single input feature ... The absence of ground truth does not preclude diagnosing heuristic collapse; it only requires shifting the criterion from output accuracy to input sensitivity" — **verified**. Web search reduces FC unevenly and homogenises (Table 1); App. A.5: 89–100% of allocations are multiples of 5.

**(c) Relevance — high.** (i) Single-turn, stateless advice, like FinPersona's static arm. (ii) If LLM allocations are essentially a function of the *stated* risk tolerance, then FinPersona's MAS — which measures |cash fraction − C_ideal| where C_ideal is itself set from the persona's stated risk appetite — is measuring how faithfully a stated risk label is mapped to cash, and re-injecting a louder risk label moves the allocation toward the label's pole. Ross & Lo thus (a) support the reframed claim's "content-modulated shift" and (b) sharpen the Cycle-1/2 tautology worry about C_ideal. (iii) The input-sensitivity framing is a ready-made tool FinPersona could adopt: fit a surrogate of cash fraction on (persona label, directive present, observation features) and report the directive's share of predictive weight rather than MAS deltas. (iv) Round-number quantisation of q is relevant to any continuous allocation metric.

**(d) ORIGINAL.** Contradicts nothing numerically, but undercuts the *interpretation* of MAS as "mandate salience" (vs "risk-label mapping"); supports "behaviour dominated by a salient stated feature". **(e) REFRAMED.** Strongly consistent and partially anticipating: content (risk label) dominates allocation in stateless calls; the opposed-target split (17/18 vs 16/18) is what one expects if the directive simply pushes allocation toward the stated pole. **(f) Cite?** Yes, essential. Differentiation: "Ross & Lo (2026) show stateless allocations are dominated by stated risk tolerance; our directive-injection result is consistent with this and we therefore report the directive's contribution alongside observation features rather than treating MAS shifts as evidence of decay." **(g)** Cycle-1's "57–88% of predictive weight" and "input-sensitivity criterion" — both verified exactly (p.5 and p.2).

---

## 16. Kruthof (TUM, 2026) — "Models Recall What They Violate: Constraint Adherence in Multi-Turn LLM Ideation" (DRIFTBENCH) [arXiv 2604.28031 v2, 13 pp, read in full]

**(a)** Preprint v2, 4 May 2026; single author, TU Munich.

**(b)** 2,146 scored runs; 7 models (GPT-5.4, GPT-5.4-mini, Gemini 3.1 Pro, Gemini 3.1 Flash-Lite, Claude Sonnet 4.6, Qwen3-235B, Llama-3.3-70B); 38 briefs / 24 domains with 5–8 hard constraints and 3–5 banned moves; conditions SS / MT-Neutral / MT-Pressure / Checkpointed (Table 1); cross-family LLM judge + auditor; **restatement probe** in a forked conversation (§3.6). Findings: non-compliance 35%→54% under pressure (Fig. 1); **KBV rate 8% (GPT-5.4) to 99% (Sonnet 4.6)** (Table 3, p.6; Fig. 3) with 97.3% probe recall; "74% of drift cases showing first violations by turn 2" (§4.3); checkpointing reduces KBV only partly (Sonnet 99→87, Llama 93→92, Fig. 3); automated monitoring warnings leave KBV at 97%/89% (§4.5); robust to temperature and pressure type (§4.6); human raters find the judge under-detects violations (sensitivity 15%, §3.8); explicit alternative-explanation table (§5): "Simple forgetting: Drift ~ recall failure — No: 97% probe accuracy, KBV"; "challenges the assumption that multi-turn degradation is driven by forgetting or context loss" (p.1).

Verification of Cycle-1 numbers: "KBV 8–99%" — **verified** (Table 3). "Opposite capacity ordering" — **not a statement the paper makes**; what the paper shows is that ordering is *not* a simple capacity ordering: within OpenAI the flagship beats the mini (8% vs 16%), within Google Pro beats Flash-Lite (18% vs 76%), but the mid-tier Claude Sonnet 4.6 is worst (99%) and open-weight Qwen3-235B (55%) beats Gemini Flash-Lite; the paper says "This finding is not simply a matter of instruction-following, since GPT-5.4 receives identical pressure prompts and drifts at only 4%". If Cycle 1 meant "Sonnet is worst in Kruthof but resilient in FinPersona (Haiku worst), i.e. the ordering does not transfer", that is defensible; if it meant "capacity ordering is reversed", that is not supported.

**(c) Relevance — high.** (i) The KBV result is the single strongest prior-art attack on the *name and mechanism* "Mandate Salience Decay": constraint violation coexists with perfect recall, so violation is not forgetting. (ii) In FinPersona's stateless design the mandate is in every prompt, so "recall" is trivially available; any non-compliance is KBV by construction; a restatement probe would show 100%. (iii) Structured checkpoints/reminders only partially reduce KBV — a caution for "re-injection fixes it" generalisations (FinPersona's own ENTJ/bull-trap reversals are consonant with this). (iv) Model heterogeneity (8–99%) is at least as large as FinPersona's.

**(d) ORIGINAL.** *Contradicts* the "forgetting/decay" mechanism framing (not the numbers); *anticipates* "re-grounding not universally effective" (checkpoint/monitoring partial); *supports* model-dependence. **(e) REFRAMED.** Consistent; suggests renaming the construct to something like "directive weighting under competing signals". **(f) Cite?** Yes, essential, with the name collision footnote. Differentiation: "Kruthof (2026) shows models violate constraints they can restate; because our agents see the mandate on every call, violation in our setting is by construction a weighting failure rather than a recall failure, and we describe it accordingly." **(g)** see verification above.

---

## 17. Canaverde, Alves, Pombal, Attanasio & Martins (2026) — "SEQUOR: A Multi-Turn Benchmark for Realistic Constraint Following" [arXiv 2605.06353 v2, 33 pp, read in full]

**(a)** Preprint under review, v2 8 May 2026; IT/IST Lisbon.

**(b)** 1,446 constraints mined from lmsys-chat-1m and filtered (satisfiable, non-trivial, non-subjective, 70% thresholds); 1,400 conversations × 50 turns from 200 Persona-Hub personas; regimes Single / Tuples / Replace(5,10) / Add(5,10) / Everything (Fig. 4); judge GPT-oss-120B (93.55% on gold); 11 models (10 open + Gemini 3.1 Flash Lite); sliding window if context exceeded. Results (Table 5, p.29): average first→last-turn drop **−26% Single, −38% Tuples, −23% Replace-10, −65% Add-10, −27% Everything**; abstract's ">11%", ">40%", ">9%" figures are the best model (Gemini 3.1 Flash Lite: −10.5/−24.4/−11.5/−40/−9). **Replacement resets**: "Models tend to recover their initial performance when existing constraints are replaced with new ones ... after each replacement, subsequent turns often exhibit sharper performance declines" (§4.2, p.8); constraints in Everything are always within the last 15 turns, so "potential context-length limitations should not cause degradation in later turns" (§4.3, p.8–9).

**(c) Relevance.** (i) Long-horizon instruction decay with accumulating context, 50 turns — the cleanest precedent for "compliance erodes even for a single standing instruction" and for "re-stating the instruction restores compliance" (replacement spikes). (ii) The sharper decline after each reset is the closest published analogue of FinPersona's "injection must be at every step" (ENTJ step function, App. H). (iii) SEQUOR's observation that decay occurs even when the constraint is within the last 15 turns argues, like Kruthof, that the mechanism is not context loss.

**(d) ORIGINAL.** Partially anticipates decay-over-horizon, model dependence, and the benefit of re-statement; the magnitudes are larger than FinPersona's. **(e) REFRAMED.** Consistent (re-stated instruction at recency position restores compliance); no placebo/content control. **(f) Cite?** Yes. Differentiation: "SEQUOR shows constraint adherence decays over 50 accumulating turns and is reset by re-statement; our per-step injection in a stateless loop isolates the content effect from the context-length effect." **(g)** Cycle-1 manifest ("−11% single constraint, −40% multiple, −9% on constraint replacement") reproduces the *abstract's best-model* numbers; averages are −26/−38/−27 (and the "−9%" is the Everything regime, not a pure replacement regime, which averages −23%).

---

## 18. Cai, Zhu, Gao, Tang & Qin (2026) — "Push Your Agent: Measuring and Enforcing Quantitative Goal Persistence in Long-Horizon LLM Agents" (PushBench) [arXiv 2605.23574 v1, 17 pp, read in full]

**(a)** Preprint 22 May 2026; independent researchers / Xidian.

**(b)** QGP: keep working until a verifier confirms N distinct valid units (§3). QGP-RepoScan (36 tasks, N∈{10,25,50,100}, requests/pytest/flask) and QGP-DataOps-lite (24 backlogs, N∈{3,5,10,20}); models gpt-4.1-mini/4.1/5.4; controllers Standard / Verifier-gated / STATEQGP or UNITQGP; memory baselines Letta/MemGPT, LangGraph+Memory. Results: STATEQGP 69–78% success with 0 duplicates vs 3–31% standard (Table 1); UNITQGP 25–50% vs 0% (Fig. 2); frontier Claude Code (Sonnet 4.6) and Codex CLI (gpt-5.4) 7/9 at N=50 → 3/9 at N=100; **"Adding an explicit checklist prompt does not improve paired success"** (§9; Table 7, zero success delta).

**(c) Relevance.** (i) Long-horizon goal persistence with accumulating agent context; the horizon-scaling collapse (50→100) is a "compounding" precedent of sorts. (ii) The finding that a generic reminder prompt does nothing while externally tracked verifier state helps is a caution against reading FinPersona's re-injection as a general remedy, and a precedent for the revision plan's "adaptive controller" (external state triggering intervention). (iii) Not about personas or mandates.

**(d) ORIGINAL.** Weakly anticipates horizon-dependent degradation and "reminder ≠ fix"; irrelevant otherwise. **(e)** Tangential (checklist reminder ≠ imperative directive at recency; different regime). **(f) Cite?** Optional, for the adaptive-controller design. **(g)** Cycle-1 manifest ("count-based; horizon scaling failure 50 -> 100 artifacts") accurate.

---

## 19. Ding, Yu, Liu & Zhao (Accenture, 2026) — "ContextEcho: A Benchmark for Persona Drift in Long Agentic-Coding Sessions" [arXiv 2605.24279 v1, 28 pp, read in full]

**(a)** Preprint 22 May 2026; Center for Advanced AI, Accenture.

**(b)** Snapshot-then-probe primitive (fork at turn t, ask an off-task identity probe, discard); 25 probes in 5 categories (primary: 5 coding-self probes); 4-point assistant-register rubric by claude-sonnet-4-6 judge, cross-judged by GPT-5 (κ 0.42, ρ 0.75, App. O); **within-cell length-matched filler control** ("Lorem-ipsum-style text padded to c's character count", §2.1, Def. 1) in every cell; judge-free behavioural fingerprint (6 features → PCA) and judge-free S2 regex compliance + length ratio; 3 donated Claude Code sessions — headline 9,643 turns (12 positions, 6 compactions), plus 3,746 and 4,918 (abstract/§1 give the range "3,746–9,716 turns", body §3.1 says 9,643; both numbers appear); **23 frontier models from 10 organisations**; drift gap Δ from −0.15 to +1.00, 17/23 with |Δ|≥0.30 (Fig. 3, p.7); neither reasoning tier nor family predicts drift; compaction does not reset (Q3); **A-anchor** (~80 tokens: one-sentence identity reminder V0 + one-shot bash format demo V2) inserted as a *user turn* before the probe restores the register on all targets, including no-drift ones ("it acts as a generic prior reset or compliance amplifier rather than a drift-specific antidote", §3.2 Q4, p.8); **anchor-content ablation** V0-only / V2-only / combined / two-shot (App. G, Table 3): V0 restores probes but not format compliance, V2 the reverse; anchor size sweep (App. H); **placement: user-turn anchor beats system-prompt placement on all 4 Anthropic targets** (App. I) with the hypothesis "the model treats the recent user/assistant exchange as more behaviorally salient than the static system prompt"; persistence ≥20 turns (App. F); **mode-dependent sign flip**: in tool-free chat drift breaks S2 contracts and inflates length 0.7–31.8× (Fig. 5), in tool-using SWE-style continuation the Claude-flavoured prefix *improves* argument fidelity (+0.147 to +0.216, p<0.05; App. M); TerminalBench fresh-task null; negative-control factual probes collapse the gap on 21/22 targets (App. J); probe-framing ablation inflates the gap by 0.26 but does not create it (App. P); substrate steering on Qwen3-32B recovers the activation projection but not the judged behaviour ("the surface and the substrate decouple", App. L).

Verification of Cycle-1 items: 23 models ✓; 9,643/9,716 turns ✓ (both numbers in the paper); filler arm in every cell ✓; anchor-content ablation ✓ (App. G); sign flips by deployment mode ✓ (Q5/App. M); judge-free metrics ✓ (fingerprint + S2 regex).

**(c) Relevance — highest in my share.** ContextEcho is the closest structural analogue of FinPersona's experimental logic: (drift arm vs **length-matched filler control**) + (a short imperative **anchor** re-injected at the recency position that restores compliance) + content ablation of the anchor + cross-model panel + deployment-mode-dependent sign of the effect. The differences are the domain (identity register in coding sessions vs trading allocation), the presence of genuinely accumulating context (thousands of turns; FinPersona: none), and ContextEcho's additional judge-free surfaces. Three ContextEcho findings bear directly on FinPersona's interpretation: (i) the anchor lifts *no-drift* targets to ceiling too → an imperative reminder is a **compliance amplifier**, which is exactly the alternative explanation for FinPersona's memory-arm shift in a stateless setting where there was no decay to reverse; (ii) anchor content matters (V0 vs V2 restore different surfaces) → content-modulated effects of recency-position directives are established; (iii) user-turn placement beats system placement → FinPersona's choice of injecting into the user message is supported, and the effect is a placement/recency effect independent of any decay.

**(d) ORIGINAL.** *Anticipates*: persona/instruction drift across a panel of many models with strong model dependence; length-matched control (placebo logic); re-injection restoring compliance; content ablation of the re-injected text; "not universally beneficial" (sign flip by mode); judge-free surfaces (FinPersona's MAS/CI/RG are also judge-free — a genuine shared strength). *Does not anticipate*: finance, allocation targets, hidden fundamental, 4.4x compounding, MBTI/OCEAN. *Contradicts nothing numerically*, but its "compliance amplifier" reading is the most economical explanation of FinPersona's static-vs-memory gaps.

**(e) REFRAMED.** Largely anticipated in form (imperative reminder at recency + length-matched control + content ablation + cross-model split), not in domain. The reframed claim survives as a domain-specific instance; its novelty rests on the allocation readout and the synthetic market, not on the directive-injection logic.

**(f) Cite?** Yes, essential. Differentiation: "ContextEcho (Ding et al., 2026) shows, with a length-matched filler control, that a short user-turn anchor restores a model's trained register across 23 models and acts as a generic compliance amplifier; our placebo/memory design applies the same logic to a continuous trading allocation in a stateless loop, where the 'amplifier' reading is the null hypothesis we must reject before claiming decay."

**(g) Cycle-1 check.** All six factual items verified above. One nuance Cycle 1 should carry: ContextEcho's drift is measured under *genuinely long* contexts and still finds the anchor works on no-drift targets; the relevant lesson for FinPersona is the amplifier interpretation rather than the existence of drift.

---

# SYNTHESIS (my share only)

## Claims in my share that are fully or largely anticipated
* **Instruction/persona adherence erodes over an interaction and re-stating the instruction restores it**: Li et al. 2024 (SPR, attention decay), SEQUOR (50 turns, replacement resets), Multi-IF (3 turns), ContextEcho (anchor). Not novel.
* **Placebo / length-matched control for a re-injected text**: ContextEcho (filler arm in every cell); Arditi (random-suffix control). The logic is prior art; FinPersona's single-model, single-scenario, 15-pair placebo (App. F) is a much weaker instance.
* **Content ablation of the injected text**: ContextEcho App. G (V0/V2/combined). FinPersona's O3 "numerical-only" ablation is a variant.
* **"Re-grounding is not universally beneficial"**: ContextEcho mode-dependent sign flip; Kruthof checkpoint/monitoring partial effects; PushBench checklist null; Everitt motivational prompt partial.
* **Model dependence**: universal across Kruthof (8–99%), ContextEcho (−0.15..+1.00), SEQUOR, Machine Spirits, Multi-IF.
* **Behavioural-plus-representational framework (M-series)**: Arghal et al. (ICML 2026) is the direct precedent; Arditi/Chen supply the direction-extraction and steering recipes.
* **Objective ground-truth market for LLM agents**: Machine Spirits (known fundamental, 15 LLMs) partially anticipates; FinPersona's *hidden* fundamental with exogenous price is the residual novelty.
* **Allocation dominated by stated risk label (content modulation)**: Ross & Lo.

## Claims that remain unclaimed by papers in my share
* The specific MAS/CI/RG metric triple and the three regime scenarios (flat/crash/bull-trap) with hidden V_t.
* 4.4x compounding of a static–memory gap across quartiles (no paper in my share measures a comparable gap ratio; note Multi-IF's front-loaded decay and SEQUOR's post-reset sharper declines are the nearest data points and do not support a generic compounding law).
* MBTI/OCEAN/O3 ablation, T-calibration, LCR rationale analysis, the 17/18 vs 16/18 split itself.
* Transfer to medical/legal (only asserted as future work by Ross & Lo and Sawant).

## Direct competitors in my share
* **ContextEcho** (design logic: drift arm + length-matched control + anchor + content ablation + multi-model panel + sign-flip by mode).
* **Kruthof DriftBench** (constructs the "knows-but-violates" framing that subsumes FinPersona's stateless non-compliance and explicitly argues against the forgetting/decay reading).
* **Machine Spirits** (ground-truth market with many LLMs; different question).
* **Ross & Lo** (stateless allocation driven by the stated risk label — the mechanism behind the reframed claim).

## Findings that contradict a FinPersona result or its interpretation (name + number)
1. **"As market context accumulates ... mandates gradually lose their behavioral influence" (abstract) and Eq. 3's stateless policy are mutually exclusive.** Li et al. 2024 §4.2 (π(t) plateaus within a single turn) and Xiao et al. 2024 (attention to initial tokens persists regardless of distance) predict no attention-level decay in a fixed-length prompt; Everitt App. E shows degradation not explained by context length even when context does grow; Kruthof (97.3% recall, KBV 8–99%) shows violation without forgetting. These contradict the *mechanism*, not the measured MAS/CI/RG deltas (Table 1: −12.7%, −12.6%, +8.8%).
2. **"the gap ... grows monotonically from 1.0x in Q1 to 4.4x by Q4 ... This widening separation reflects the progressive erosion of mandate influence as context accumulates" (§4.3.2, p.8).** No context accumulates; the nearest external data (Multi-IF IFR larger at turn 1→2 than 2→3; SEQUOR post-reset sharper declines) do not support a generic compounding law; in my share the 4.4x has no external support and, given statelessness, must be a market-phase artefact (crash phase τ2 = days 81–140 spans Q2–Q3; stabilisation τ3 = Q4) rather than temporal erosion.
3. **Placebo interpretation (App. F: placebo 0.191/0.950/0.454 vs static 0.188/0.903/0.409 vs memory 0.300/0.730/0.394).** ContextEcho's finding that an imperative anchor lifts *no-drift* targets to ceiling means "memory ≫ placebo" is equally consistent with "imperative content amplifies compliance in the absence of any decay" — the paper's reading "consistent with MSD as a salience-based behavioral failure" is not the only one.
4. **Hong et al. 2025 is cited (p.1) for "as context grows, models become worse at following their instructions"**; Hong measure retrieval/copy tasks, not instruction following, and explicitly do not explain mechanism.

## What the mech-interp corpus implies for M1–M4 (given stateless single-turn agents)
* **M1 (attention to mandate span across the rollout).** Li's π(t) decay is a cross-turn phenomenon; in FinPersona's stateless prompts the system-prompt mandate sits at a fixed position in every call and Li's own result predicts a flat profile. Any "decay" curve would be a function of the observation O_t (market phase), not of elapsed time, and must be analysed as such. Xiao: exclude the first ~4 sink tokens and compare to a matched control span at the same depth; the placebo span at the prompt end is not a matched control for a start-of-prompt span. In the memory arm the mandate appears twice (system and user); report both spans. Feasible on Llama-3.1-8B/Gemma/Qwen, but FinPersona's open models are exactly the ones where the behavioural effect is weakest or reversed (Qwen2.5-7B −5.4/−59.1/−28.8%, Gemma-3-4B exception), so M0 gating is essential and a null M1 result is the most likely outcome.
* **M2 (mandate direction).** Arditi/Chen recipes transfer; the expected positive result is that a guardian-vs-commander difference-in-means direction exists and its last-prompt-token projection shifts when the directive is appended. Chen's within-condition correlations (0.25–0.81) warn the per-step signal will be noisy; Arghal's linear-probe weakness (39% vs 70%) and Templeton's few-shot-vector caveat warn a single direction may be blunt. Defining the contrast by MAS (adherent vs non-adherent rollouts) risks circularity with the cash-fraction readout.
* **M3 (causal intervention).** "Ablate early, add back late" presupposes a temporal trajectory that does not exist; the defensible version is a **mediation test**: does ablating the direction (all layers/positions, Arditi Eq. 4) abolish the memory-arm effect on the first action token / cash fraction, and does adding it reproduce the effect without the directive? Arghal's 0/456 single-layer patching result argues for multi-layer interventions; Chen App. J.3 gives the layer-incremental recipe. Split-softmax (Li) is a genuinely informative extra lever: if boosting attention to the system-prompt mandate reproduces the memory-arm shift, attention to the mandate is a mediator — that would be the first mechanistic content behind "salience".
* **M4 (attribution for the mini-model crash reversal).** ROME supplies causal tracing, not DLA; the attribution tool in the corpus is Templeton's gradient×feature attribution (or logit-lens-style DLA from elsewhere). A clean one-token readout exists (first token of the action enum), but the reversal (GPT-4o-mini −11.3%, GPT-4.1-mini −21.3%, Gemini 2.5 Flash −28.3%, Qwen2.5-7B −59.1% on crash CI) is mostly on closed models, and Qwen2.5-7B is the only open one showing it; M4 therefore hangs on one model.
* **Naming.** Given Kruthof, Chen (Fig. 4) and Li (plateau), the construct should not be called "salience decay" for a stateless agent; "directive weighting" / "knows-but-violates under competing market signals" is what the corpus supports.

---

# CYCLE-1 AGREEMENT / DISAGREEMENT LIST (opened after the above was written)


## Cycle-1 items touching my share — AGREE / DISAGREE / REFINE

Legend: **AGREE** = my full read supports Cycle 1's attribution; **DISAGREE** = not supported by the paper; **REFINE** = right in substance, wrong or incomplete in detail.

1. **"Kim/Li COLM 2024" (C1, C13, III.5, VII.1, Tier 0 citation list, position map).** REFINE. The paper is Li, Liu, Bashkansky, Bau, Viégas, Pfister & Wattenberg (COLM 2024, arXiv 2402.10962); no author named Kim (the `Kim_Suzgun` filename is wrong). Substance is correct: SPR sweeps injection probability p (§6.1), with an MMLU performance-drop axis (§6.3, Fig. 5), and SPR is treated as a baseline. C13 "FULLY ANTICIPATED" for the frequency ablation: AGREE (Li's p-sweep and FinPersona's k-sweep measure the same thing; Li additionally costs it on MMLU). Also AGREE with Cycle 1 that the current manuscript cites none of this (verified: Li et al. absent from the reference list; only Liu 2024, Hong 2025, Peysakhovich & Lerer 2023 are cited for position/recency).

2. **C1 "Formalising MSD — FULLY ANTICIPATED (… Kim/Li 'instruction drift' …)".** AGREE on the phenomenon (instruction drift over turns, Li Fig. 3); REFINE: Li's mechanism (attention decay) is explicitly cross-turn and Li show a *within-turn plateau* (§4.2, p.7) — the direct reason a stateless FinPersona cannot exhibit it. Cycle 1 makes the flatness point from the code (I.2); Li's paper makes it from the mechanism. Both agree.

3. **C2 "Behaviour distinct from reasoning — FULLY ANTICIPATED (DriftBench KBV 8–99%; Everitt …)".** AGREE. KBV 8–99% verified (Kruthof Table 3). Everitt's distinction is goal-directedness vs capability (Def. 3.1) — a related but different cut; Everitt App. E additionally shows the degradation is not explained by context length, which Cycle 1 uses in the position map ("three papers refute the mechanism") — AGREE.

4. **C3 "Decoupled synthetic ground truth — PARTIALLY ANTICIPATED (Machine Spirits p_f = 60)".** AGREE; add that Machine Spirits' fundamental is *disclosed* to agents and price is endogenous, so FinPersona's hidden-V / exogenous-price design remains the residual novelty (subject to the P/E leakage Cycle 1 found, which is a code/table point outside my literature remit).

5. **C8 "Model-dependence — FULLY ANTICIPATED (ContextEcho 23 models; DriftBench 7 models …)".** AGREE (ContextEcho Fig. 3: Δ from −0.15 to +1.00; Kruthof 8–99%; also SEQUOR, Machine Spirits, Multi-IF).

6. **C9 "Compounding / 4.4x — ANTICIPATED AND CONTRADICTED (Drift No More …)".** Cannot adjudicate Drift No More (not in my share). From my share: no paper supports a generic compounding law; Multi-IF (IFR larger at turn 1→2 than 2→3) and SEQUOR (context-independent post-reset declines) are mildly against it. Cycle 1's expanding().min() finding is a code point I did not re-run.

7. **C10 "Re-grounding not universally beneficial — PARTIALLY ANTICIPATED (ContextEcho mode-dependent sign flip; Kim/Li cost curve)".** AGREE; REFINE by adding Kruthof (checkpointing 99→87%, monitoring leaves 97%), PushBench (checklist prompt zero success delta) and Everitt §4.4 (motivational prompt only partial) as further precedents that reminders are not a general fix.

8. **C11 "Placebo control — FULLY ANTICIPATED (ContextEcho filler arm in every cell, 41,921 evals …)".** AGREE that the length-matched-filler logic is prior art (ContextEcho Def. 1, §2.1; 41,921 per-cell evaluations stated in §1) and that Arditi §5's random-suffix control is an earlier mechanistic instance. REFINE: ContextEcho's filler controls for *context length* in a ~30k-character prefix; FinPersona's placebo controls for *text at the recency position* in a short prompt. The logic is anticipated; the designs differ, and FinPersona's is the weaker (declarative vs imperative confound, which Cycle 1 Reviewer B also flags — AGREE).

9. **C12 "Big Five and O3 ablation — PARTIALLY ANTICIPATED (… Ross & Lo risk tolerance 57–88% of predictive weight)".** AGREE; "57–88%" verified verbatim (p.5) and the input-sensitivity criterion verified (p.2 §2). I would strengthen: Ross & Lo make the content-modulated cash shift and the opposed-target split *expected* for stateless allocation, which supports Reviewer B's "generic cash shift refracted through oppositely-signed targets" reading.

10. **S2 "ContextEcho reaches 9,716 turns but has no behavioural task and no ground truth".** DISAGREE in part. ContextEcho has a judge-free behavioural surface (S2 one-line-bash compliance by regex + length ratio, Fig. 5) and a SWE-Bench-style continuation scored by "argument fidelity to the ground truth" next tool call (App. M), plus TerminalBench tasks. What it lacks is a *long-horizon* task scored against a generating function; S2's claim should be narrowed to that.

11. **S4 "… broken … by DriftBench's opposite capacity ordering".** DISAGREE/REFINE. Kruthof does not establish a capacity ordering at all; within OpenAI and Google the larger variant drifts *less* (GPT-5.4 8% vs mini 16%; Gemini Pro 18% vs Flash-Lite 76%) — the same direction as FinPersona's "minis worse"; the outlier is Claude Sonnet 4.6 (99%), opposite to FinPersona's resilient Sonnet/Opus. The accurate statement is "capacity ordering does not transfer across benchmarks and is provider-specific", not "opposite".

12. **VII.1 "Nobody owns this. … ContextEcho varies deployment mode. Kim/Li vary intervention strength."** REFINE. ContextEcho *also* varies injected anchor content (App. G: identity sentence V0 vs format demo V2 vs combined vs two-shot) and finds content-specific effects on different surfaces; it does not vary content against opposed behavioural targets on one readout, so the narrow surviving claim is still unowned — but the related-work sentence must acknowledge ContextEcho's content ablation, and Ross & Lo should be cited as the reason the sign reversal is the expected outcome for stateless allocation.

13. **I.2 / Tier 4 / "Cut M1 (unrunnable as specified; twice published where runnable)".** AGREE on M1 (Li is one of the two; flat-in-time by construction; any variation tracks O_t). REFINE Tier 4 M2: "validate the adherence direction against the restatement-probe label" — in a stateless design the restatement probe will be ~100% (mandate in every prompt), so it has no variance to validate against; the probe is worth running *once* to make the KBV point (AGREE with Tier 2), but M2 needs a different validation target (e.g. per-step first-action token or cash fraction under a swapped-mandate design). On M3 the relevant null in my share is Arghal et al. (single-layer patching 0/456; all-layer works) — consistent with Cycle 1's "budget for a null"; I add that a *mediation* design (ablate direction → does the directive effect vanish?) plus Li's split-softmax lever is the only version that speaks to "salience".

14. **Revision-plan citation of Meng et al. (2022) for "activation patching and direct logit attribution".** Not raised by Cycle 1. ROME has causal tracing only; DLA is absent. Flag for the authors.

15. **Cycle-1 manifest entries (gap_sweep MANIFEST.md) for Multi-IF, Everitt, Drift-Bench ND, Arghal, Sawant, Machine Spirits, PushBench, ContextEcho.** AGREE on all factual descriptors; REFINE SEQUOR: "−11% single, −40% multiple, −9% replacement" are the abstract's best-model figures; averages across 11 models are −26% / −38% / −27% (Everything) and the "replacement" regime proper averages −23% (Table 5, p.29).

16. **Items Cycle 1 did not use from my share that strengthen its case.** (a) Chen et al. Fig. 4: system-prompt content is strongly represented at the last prompt token before generation (r = 0.75–0.83) — the mandate is not "lost" in a single call. (b) ContextEcho Q4: the anchor lifts no-drift targets to ceiling ("compliance amplifier") — the null hypothesis for the memory-arm effect. (c) ContextEcho App. I: user-turn placement beats system-prompt placement — supports the recency choice and frames the effect as placement, not decay. (d) Xiao: attention sinks require excluding initial tokens in any M1 — and attention to early tokens does not decay with distance. (e) Machine Spirits Table 6: macro behaviour robust to memory 0/2/4. (f) Hong 2025 is mis-cited in the paper's intro (it measures retrieval, not instruction following).

## Page-count confirmation (all read in full)
| Item | Pages/format | Read |
|---|---|---|
| Li et al. 2024 (file `Kim_Suzgun_...`) | 19 pp | full |
| Arditi et al. 2024 | 40 pp | full |
| Chen et al. 2025 Persona Vectors | 63 pp | full |
| Hong et al. 2025 Context Rot | HTML (~52k chars) | full |
| Liu et al. 2024 Lost in the Middle | 18 pp | full |
| Meng et al. 2022 ROME | 35 pp | full |
| Templeton et al. 2024 | HTML (~146k chars) | full |
| Xiao et al. 2024 Attention Sinks | 21 pp | full |
| 2410.15553 Multi-IF | 23 pp | full |
| 2504.11844 Everitt | 41 pp | full |
| 2602.02455 Drift-Bench (ND) | 65 pp | full |
| 2602.08964 Arghal (ICML 2026) | 18 pp | full |
| 2604.04300 Sawant | 5 pp | full |
| 2604.18602 Machine Spirits | 46 pp | full |
| 2604.23837 Ross & Lo | 13 pp | full |
| 2604.28031 Kruthof DriftBench | 13 pp | full |
| 2605.06353 SEQUOR | 33 pp | full |
| 2605.23574 PushBench | 17 pp | full |
| 2605.24279 ContextEcho | 28 pp | full |
