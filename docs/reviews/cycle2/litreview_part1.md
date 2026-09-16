# Cycle 2 Literature Review — Part 1 (14 PDFs, read in full with PyMuPDF)

Reviewer: Cycle-2 literature reviewer (share 1/2). Date: 2026-08-22.
Paper under review: FinPersona-Bench (pre-extracted text `paper_current.txt`, 29 pages incl. appendices A–L).

Reading log (all pages extracted with `fitz`, every page read):

| # | File | Pages | Read |
|---|------|-------|------|
| 1 | 1904_12066_Byrd_ABIDES_Market_Simulation.pdf | 13 | full |
| 2 | 2406_00799_Abdelnabi_Task_Drift_Activations.pdf | 25 | full |
| 3 | 2505_02709_Arike_Evaluating_Goal_Drift.pdf | 36 | full |
| 4 | 2505_06120_LLMs_Get_Lost_Multi_Turn.pdf | 36 | full |
| 5 | 2507_20152_Goal_Alignment_User_Simulators_TACL.pdf | 25 | full |
| 6 | 2508_04826_PERSIST_Personality_Instability.pdf | 18 | full |
| 7 | 2509_10078_Questionnaires_Mischaracterize_LLMs.pdf | 38 | full |
| 8 | 2509_25055_AlphaSAGE_ICLR2026.pdf | 28 | full |
| 9 | 2510_07777_Drift_No_More_Context_Equilibria.pdf | 14 | full |
| 10 | 2510_12189_ABM_Financial_Market_LLMs.pdf | 20 | full |
| 11 | 2510_13586_Deflanderization_Game_Dialogue.pdf | 16 | full |
| 12 | 2512_10971_AI_Trader_Live_Benchmark.pdf | 17 | full |
| 13 | 2601_02896_Gradient_Ascent_Persona_Control.pdf | 19 | full |
| 14 | 2601_14004_Locate_Steer_Improve_Survey.pdf | 101 | full (incl. Table 5 and references) |

Two claims tested against every paper:

* **ORIGINAL** (FinPersona as written): MSD formalisation; behaviour-vs-reasoning distinction; decoupled synthetic ground truth (P_t vs hidden V_t); three failure-mode regimes; MAS/CI/RG metrics; model-dependence; 4.4x compounding in crash; "re-grounding not universally beneficial"; placebo control; Big Five / O3 ablation; injection-frequency ablation; T-calibration; LCR rationale analysis; MBTI-as-vocabulary; selective re-grounding prescription; transfer to other domains.
* **REFRAMED** (Cycle-2 narrowed claim): "In a fixed synthetic market with stateless single-turn agents, appending an imperative behavioural directive at the recency position shifts trading behaviour toward cash/inaction in a content-modulated way (protective >> growth >> neutral), while a length-matched declarative placebo produces no shift; scored against opposed allocation targets this yields a 17/18 vs 16/18 split."

One framing note that recurs below. FinPersona §3.2 (p.5) defines the static arm as "a stateless predictor ... A_t ~ P_θ(A | Ψ_total, O_t)" and the memory arm as A_t ~ P_θ(A | Ψ_total, (O_t ⊕ I(M))). Neither arm carries dialogue history; the LLM context does not grow across the 200 steps (only the indicator values in O_t change). Several papers in my share study drift in *genuinely accumulating* multi-turn contexts; their relevance to FinPersona is therefore conceptual, and in some cases they cut against FinPersona's own explanation of its effect ("mandate loses influence relative to the surrounding context as context accumulates", §1 p.1; §3.2 p.5 "context drift as immediate market observations overwhelm initial instructions").

---

## 1. Byrd, Hybinette & Balch (2019) — ABIDES: Towards High-Fidelity Market Simulation for AI Research

**(a) Citation.** D. Byrd, M. Hybinette, T. H. Balch. "ABIDES: Towards High-Fidelity Market Simulation for AI Research." arXiv:1904.12066 [cs.MA], 26 Apr 2019 (preprint; later AAMAS/WSC-adjacent). 13 pp.

**(b) Summary.** Describes an open-source agent-based discrete-event equity-market simulator: nanosecond kernel, NASDAQ ITCH/OUCH-style message protocol, configurable latency, deterministic per-agent PRNGs enabling A/B "what-if" re-simulation of historical days (§3.1, p.4). Background agents are zero-intelligence-style traders whose "central value belief at any time is a mixture of the prior belief with a noisy observation of a historical trade" (§5, p.9), inspired by the Wang & Wellman "fundamental value" construct. Case studies: reproducing intraday price paths for IBM/MSFT with 100 background agents (Fig. 4), and a market-impact study varying an impact agent's "greed" (§6, pp.10–12). No LLMs, no personas, no drift.

**(c) Findings relevant to FinPersona.** Only one: the idea of a latent "fundamental value" that agents observe noisily, and of a fully controlled simulation as the only way to get "perfect control and observation" and counterfactual A/B tests (§1, p.1; §2, p.3 "In a market field study, it is not feasible to perform controlled A/B tests"). FinPersona's §3.1 argument for a synthetic engine ("mathematically defined ground truth", p.3–4) is the same methodological argument, specialised to LLM evaluation.

**(d) ORIGINAL claims.** *Partially anticipates* "decoupled synthetic ground truth" as a market-simulation design principle (hidden value + noisy observable price goes back to ZI/Wang-Wellman, which ABIDES explicitly cites, p.9). Irrelevant to MSD, metrics, personas, re-grounding, placebo, ablations.

**(e) REFRAMED claim.** Does not bear on it (no LLMs, no directives).

**(f) Cite?** Optional but advisable in §3.1 as lineage for the synthetic-market approach: "Agent-based simulators such as ABIDES (Byrd et al., 2019) and the ZI/fundamental-value tradition they build on already separate a latent value from observed trades; we adopt the same separation but for a single LLM agent in a price-taking, single-asset setting where V_t is an exact generating function rather than an emergent quantity."

**(g) Cycle-1 check.** See agreement list at the end.

---

## 2. Abdelnabi, Fay, Cherubin, Salem, Fritz & Paverd (2025) — Get my drift? Catching LLM Task Drift with Activation Deltas

**(a) Citation.** S. Abdelnabi, A. Fay, G. Cherubin, A. Salem, M. Fritz, A. Paverd. "Get my drift? Catching LLM Task Drift with Activation Deltas." arXiv:2406.00799v6 [cs.CR], 6 Mar 2025 (Microsoft/CISPA; IEEE SaTML 2025). 25 pp.

**(b) Summary.** Defines "task drift" as an LLM deviating from the user's primary task after ingesting external data that contains injected instructions (prompt injection) (§I, p.1). Collects last-token residual activations before and after the data block and trains linear / triplet-metric probes on the *activation delta* (§IV, pp.4–5). Six open models (Phi-3 3.8B/14B, Mistral 7B, Llama-3 8B/70B, Mixtral), >500K instances, ROC-AUC ≥ 0.99 OOD (Tables II–V). Also shows distances "drift with the start of the injected instruction and continue to grow with more ingested tokens" (Fig. 7, p.10), that meta-prompts saying "do not follow instructions" reduce the delta (Table XIII, p.11), and that detection is comparable whether or not the injected task was executed (Fig. 12, p.20).

**(c) Findings relevant to FinPersona.** (i) The word "drift" here means *instruction hijack within one turn*, not slow erosion of a persona over many turns. (ii) Evidence that appended instructions in the user message strongly move the model's internal task representation (Table VI: distances 0.98–1.57 vs clean 0.18–0.55; injections "placed at the end had higher distances", §V-A-1, p.6) is mechanistic support for FinPersona's claim that appending an imperative mandate at the recency position changes behaviour, and that a non-instructional text (their "clean" blocks; FinPersona's placebo) does not.

**(d) ORIGINAL claims.** Irrelevant to MSD-as-decay, metrics, personas, compounding, ablations. *Supports* the general "instruction-at-recency-position changes behaviour" premise behind the memory arm, and FinPersona's stated future work ("mechanistic account of how mandate tokens lose influence", Conclusion p.10) could use exactly this activation-delta tooling.

**(e) REFRAMED claim.** Bears weakly and supportively: end-positioned instructions produce the largest activation shift; declarative text without instructions does not. It does not own or anticipate the trading-specific result.

**(f) Cite?** Yes, as a mechanistic pointer in Related Work / future work: "Activation-delta probes (Abdelnabi et al., 2025) show that instruction-bearing text appended at the end of a context measurably shifts an LLM's internal task representation, whereas instruction-free text does not; our placebo/memory contrast is the behavioural analogue and could be verified mechanistically with the same tooling."

---

## 3. Arike, Donoway, Bartsch & Hobbhahn (2025) — Technical Report: Evaluating Goal Drift in Language Model Agents

**(a) Citation.** R. Arike, E. Donoway, H. Bartsch, M. Hobbhahn. "Technical Report: Evaluating Goal Drift in Language Model Agents." arXiv:2505.02709v1 [cs.AI], 5 May 2025 (MATS / Apollo Research). 36 pp.

**(b) Summary.** A *simulated stock-trading environment* ("Fortuna AI, a portfolio manager at Apex Capital", §3.1, p.3) in which an agent is given a system-prompt goal (emission minimisation vs profit maximisation), then exposed over up to 30+64 quarterly time steps (>100K tokens, Table 1 p.22) to competing pressures: adversarial news/emails/distractions (setting 2), instrumental "goal switching" (setting 3), or both (setting 4). Four tool-using models (Claude 3.5 Sonnet/Haiku, GPT-4o, GPT-4o mini), 20 seeds. Behavioural metrics: GD_actions (buying the wrong cluster "or decides to save up its budget when the goal-directed action would be to invest", §3.3.1, p.4) and GD_inaction (failure to divest). Findings 1–9 (pp.5–7) and three mechanism ablations (§5, pp.7–8).

**(c) Findings relevant to FinPersona (with quotes).**
* Finding 2 (p.5): "Strong goal elicitation significantly reduces goal drift" — adding the imperative "Remember: your one and only goal is to maximize profits. Use 100% of your quarterly budget ..." (App. A.1, p.13) to the system prompt reduced drift "in all cases" (p<0.05). This is an imperative behavioural directive changing trading behaviour in a content-consistent direction.
* Finding 3–4 (p.5): model-dependence; "more capable models are more strongly influenced by elicitation strength"; "distinct drift patterns not explained by capabilities alone".
* Finding 8 (p.7): "Goal drift tends to be larger through inaction than through action" — LLM agents "privilege action over inaction"; in FinPersona terms, passivity/cash-holding is a measured failure mode.
* §5.1 token-distance hypothesis (p.7–8): replacing the instrumental phase with a length-matched single repeated token gave "substantially lower drift scores ... token distance is not a significant factor"; §5.2: drift tracks the number of in-context *examples* of the competing behaviour (pattern-matching). §E.1 (p.35): "increasing state complexity has a negligible effect".
* Finding 9 / App. D: stated goals correlate with behaviour; hybrid goals appear in drifted runs.
* Limitations (p.8–9): "our evaluation environment is not sufficiently complex to reliably measure the susceptibility to goal drift of such frontier models"; single environment.

**(d) ORIGINAL claims.**
* *Anticipates* (substantially): a controlled trading simulation for behavioural (not self-report) goal adherence over long horizons with quantified drift, model-dependence, and "drift through inaction". FinPersona's contribution 1 ("MSD as a behavioural failure distinct from reasoning errors") is pre-empted in spirit: Arike measure "goal-alignment through quantifiable actions ... not relying on potentially unfaithful self-reports" (§3.1, p.3).
* *Partially anticipates* the imperative-directive effect (strong elicitation) and the finding that it is model-dependent (Finding 3).
* *Contradicts* FinPersona's *explanation* of MSD: FinPersona attributes decay to mandate influence fading "relative to the surrounding context" as context accumulates (§1 p.1, §3.2 p.5). Arike's ablations find token distance alone does not drive drift; pattern-matching on in-context behaviour does. Since FinPersona's static agent has *no* accumulating context at all, neither mechanism is actually tested by FinPersona, and Arike's result removes the a-priori plausibility of the "distance from system prompt" story.
* Does not anticipate: decoupled hidden V_t, MAS/CI/RG, three regimes, 4.4x compounding, placebo, persona frameworks, injection frequency.

**(e) REFRAMED claim.** Bears on it directly and partially anticipates it: an imperative directive ("Remember: your one and only goal ...") shifts trading behaviour toward the mandated side in a content-consistent way across four models, in a trading simulation with a behavioural score. Differences: Arike's directive sits in the system prompt at t=0, not re-appended at the recency position each step; Arike's drift arises from adversarial/in-context pressure, whereas FinPersona's agents are stateless; no placebo; no protective-vs-growth asymmetry (though emission-min and profit-max goals are two opposed directions, and Finding 1 shows drift is "bidirectional"). The 17/18 vs 16/18 split itself is not anticipated.

**(f) Cite?** **Mandatory** (direct competitor; it is absent from FinPersona's reference list). Differentiation sentence needed: "Arike et al. (2025) measure goal drift of tool-using LLM traders under adversarial pressure and goal switching in a multi-turn, history-carrying loop and find that drift is driven by in-context pattern-matching rather than token distance, and that strong (imperative) goal elicitation reduces it; we instead study *stateless* single-step agents in a synthetic market with an exact hidden fundamental value, isolate the effect of re-appending the mandate at the recency position against a length-matched placebo, and show the direction of the effect depends on mandate content (protective vs growth)." The authors must also drop or qualify the "context accumulates / mandate loses influence relative to context" language, since their design has no accumulating context and Arike's evidence points away from distance-based decay.

---

## 4. Laban, Hayashi, Zhou & Neville (2025) — LLMs Get Lost in Multi-Turn Conversation

**(a) Citation.** P. Laban, H. Hayashi, Y. Zhou, J. Neville. "LLMs Get Lost in Multi-Turn Conversation." arXiv:2505.06120v1 [cs.CL], 9 May 2025 (Microsoft Research / Salesforce). 36 pp.

**(b) Summary.** "Sharded" simulation: 600 fully-specified instructions from six generation tasks are split into shards revealed one per turn by a GPT-4o-mini user simulator; 15 LLMs x 10 runs = 200K+ conversations (§5, p.7). Average degradation FULL→SHARDED −39% (Table 1, p.8), decomposed into −15% aptitude and +112% unreliability (§6.2, p.9). Root causes: premature answer attempts, answer bloat, "loss-in-middle-turns" (F.3, pp.23–24), verbosity. Mitigations: RECAP (final recap turn) and SNOWBALL (turn-level recap of all prior user info) recover part of the loss (Table 2, p.10: 4o 59.1 → 76.6 / 65.3; 4o-mini 50.4 → 66.5 / 61.8); lowering temperature does not fix multi-turn unreliability (Table 3, p.11).

**(c) Findings relevant to FinPersona.** (i) SNOWBALL = per-turn repetition of earlier user content is structurally the same intervention family as FinPersona's per-step re-injection; Laban show it helps "15–20%" but "still lags behind FULL or CONCAT" (§7.1, p.11). (ii) Loss-in-middle-turns (F.3): LLMs "most likely to cite either documents in the first or last turns" — an empirical basis for the recency-position premise. (iii) Their degradation is *unreliability*, not monotone decay; it appears already at 2 shards (gradual sharding, §6.3, p.10), i.e. it is not a compounding-with-length phenomenon. (iv) 15 models; no personas, no finance.

**(d) ORIGINAL claims.** *Partially anticipates* the "re-grounding by repetition" mechanism (SNOWBALL) and provides the recency/primacy attention premise. *Supports* model-dependence. *Irrelevant* to MSD formalisation, synthetic ground truth, regimes, metrics, placebo, persona frameworks. *Mildly contradicts* the "compounds over time" narrative: in a genuinely multi-turn setting degradation is present from turn 2 and is dominated by variance, not a growing offset. Note FinPersona's own temporal analysis (Fig. 3, p.8) is "averaged across models, personas, and seeds"; Laban's unreliability result suggests per-run variance should be reported before "compounding" is asserted.

**(e) REFRAMED claim.** Does not bear on it directly (no behavioural directive, no placebo), but SNOWBALL is the closest prior operationalisation of "repeat the thing each turn"; FinPersona should position its memory arm relative to it.

**(f) Cite?** Yes (FinPersona currently cites Hong et al. "Context Rot" for this point; Laban is the stronger peer-reviewed source). Differentiation: "Laban et al. (2025) show that repeating prior user information at every turn (SNOWBALL) partially repairs multi-turn degradation in generation tasks; our memory arm repeats a *behavioural mandate* rather than task content, in a stateless setting, and we find the sign of its effect depends on mandate content."

---

## 5. Mehri, Yang, Kim, Tur, Mehri & Hakkani-Tür (2026) — Goal Alignment in LLM-Based User Simulators for Conversational AI

**(a) Citation.** S. Mehri, X. Yang, T. Kim, G. Tur, S. Mehri, D. Hakkani-Tür. "Goal Alignment in LLM-Based User Simulators for Conversational AI." arXiv:2507.20152v2 [cs.CL], 8 Mar 2026 (TACL). 25 pp.

**(b) Summary.** Introduces User Goal State Tracking (UGST): a user goal is decomposed into profile / policy / task-objective / requirement / preference sub-components, each with a status updated per turn by an LLM judge (§4, pp.4–6). Baseline prompt-based simulators (Qwen-2.5-7B/72B, Llama-3.1-8B, Llama-3.3-70B, Gemma-3-27B) "struggle ... failure rates ranging 10–40%" (§1, p.3). Three-stage fix: (1) *inference-time steering* — the latest goal state is injected before every response (§5.1, Eq. 2, p.6); (2) cold-start SFT; (3) GRPO with UGST rewards. Benchmarks: τ-Bench Airline/Retail, MultiWOZ Challenge (Tables 2–3, pp.8–9). Human agreement with UGST 85.7% (Table 4).

**(c) Findings relevant to FinPersona.**
* Table 1 (p.5): failure taxonomy for goal misalignment — "Confusion" 33%, "Contradiction" 23%, etc. — a behavioural-failure taxonomy for persona/policy adherence.
* §6.3 (p.9): "Inference-time steering improves goal alignment ... up to 5.4%. However ... different models react differently ... we observe a drop in the user profile category for Qwen-2.5-7B ... or a drop in the preferences category for Gemma-27B". This is an explicit prior finding that per-turn re-injection of the goal is **not uniformly beneficial** and is model-dependent.
* App. E, Table 7 (p.23): a simpler baseline that "provides only the user goal at each turn, essentially reminding the simulator of their objective" also improves alignment, but with mixed sub-component effects (e.g. Qwen-7B profile 88.3 → 70.1 on Airline). This is the closest prior art in my share to FinPersona's memory arm (verbatim per-turn reminder of the instruction) and already shows bidirectional per-dimension effects.
* "User policy" sub-components (behavioural constraints such as "Always ask the agent to restate booking details") are the lowest-scoring category everywhere (e.g. 41–66% Airline) — behavioural directives are the hardest thing for LLMs to sustain.

**(d) ORIGINAL claims.** *Partially anticipates* (i) per-turn re-injection of the instruction as a mitigation, (ii) "re-grounding is not universally beneficial" / model-dependent, (iii) behaviour-level (not self-report) scoring of policy adherence over turns. *Does not anticipate* financial setting, hidden V_t, MAS/CI/RG, compounding, placebo, persona frameworks, frequency ablation. FinPersona cites none of this line (it cites Hakkani-Tür group only via "Drift No More" — not even that, actually; see below).

**(e) REFRAMED claim.** Bears on it partially: prior evidence that reminding an LLM of its goal every turn shifts behaviour toward the goal but with model- and dimension-specific reversals. No placebo, no imperative-vs-declarative contrast, no trading.

**(f) Cite?** Yes. Differentiation: "Mehri et al. (2026) show that re-injecting the user goal (or a tracked goal state) before every turn improves goal alignment of LLM user simulators but with model- and sub-component-dependent reversals; we observe the analogous bidirectional pattern for financial mandates and isolate the contribution of mandate *content* with a length-matched placebo."

---

## 6. Tosato et al. (2025) — PERSIST: Persistent Instability in LLM's Personality Measurements

**(a) Citation.** T. Tosato, S. Helbling, Y.-J. Mantilla-Ramos, M. Hegazy, A. Tosato, D. J. Lemay, I. Rish, G. Dumas. "Persistent Instability in LLM's Personality Measurements: Effects of Scale, Reasoning, and Conversation History." arXiv:2508.04826v3 [cs.CL], 23 Dec 2025. Accepted AAAI 2026 (AI Alignment track). 18 pp.

**(b) Summary.** 25–29 open models (1B–671B; plus Claude Sonnet 4.5/Opus 4.1 for reasoning), >2M responses to BFI-44 and SD3 (plus LLM-adapted variants) under 250 question-order permutations, 100 paraphrases, five personas, reasoning on/off, and with/without conversation history (§Methodology, p.3). Findings: question reordering alone shifts trait scores; scale gives limited stability (SD>0.3 even at 400B+); reasoning *increases* variability while lowering perplexity; persona prompts have mixed effects ("misaligned personas showing significantly higher variability"); conversation history increases variability for <50B models but decreases it for ≥50B (Table 4, p.6; Fig. 5, p.7).

**(c) Findings relevant to FinPersona.** (i) Persona prompting is effective at shifting mean trait expression but unstable (Fig. 1 right; Tables A2–A5). (ii) Temperature 0 throughout — variability persists under greedy decoding (§Implementation, p.3); FinPersona also runs T=0 and treats seeds as the only stochasticity, but PERSIST shows prompt-surface perturbations alone produce SD>0.3, which bears on FinPersona's small-n ablations (n=5 seeds, n=3 seeds). (iii) Conversation history effect is size-dependent — a concrete prior "model-dependence of history effects". (iv) Discussion (p.7): "Financial, legal and medical consultation services similarly face substantial risks, where inconsistent recommendations could have significant real-world consequences" — explicitly names finance as a downstream concern.

**(d) ORIGINAL claims.** *Partially anticipates* model-dependence of persona stability and instability under accumulating history; *supports* the premise that persona instructions are fragile. *Irrelevant* to MSD formalisation, synthetic market, metrics, compounding, placebo, frequency. *Cautions* against FinPersona's Big-Five/MBTI robustness claim: PERSIST shows persona effects measured by questionnaire are fragile to surface features; FinPersona's O1/O2/O3 comparisons rest on one model (Sonnet 4.6) for Table 6 and three models for Table 7.

**(e) REFRAMED claim.** Tangential; no directives, no trading.

**(f) Cite?** Yes, in Related Work on persona fragility (FinPersona currently cites Choi et al. 2024 "identity drift" and Mercer "Shallow Simulators"). Differentiation: "PERSIST (Tosato et al., 2025) documents instability of self-reported trait scores under prompt perturbation and conversation history; we instead score persona adherence through trading actions against an objective allocation target."

---

## 7. Song, Choi, Park, Han, Lee & Jo (2026) — Human Psychometric Questionnaires Mischaracterize LLM Behavior

**(a) Citation.** W. Song, D. Choi, Y. Park, J. Han, E.-J. Lee, Y. Jo. "Human Psychometric Questionnaires Mischaracterize LLM Behavior." arXiv:2509.10078v4 [cs.CL], 29 May 2026 (SNU). 38 pp.

**(b) Summary.** Eight open models (Gemma3 4B/27B, Qwen2.5 7B/72B, Qwen3 30B/235B MoE, GPT-OSS 20B/120B). Compares Likert self-report profiles (PVQ-40/21, BFI-44/10) with *generation-probability* profiles computed from log-probs of psychometrically validated responses to realistic user queries (Value Portrait dataset) (§3, pp.3–4). RQ1: cross-method rank agreement is low (Spearman 0.11–0.31 vs 0.74–0.77 within-method; Table 2, p.5). RQ2: intra-construct item consistency exists only on questionnaires (η² 0.49–0.53 vs ≈baseline; Table 3, p.6). RQ3: the reason is *item textual transparency* — LLMs recognise which construct a BFI/PVQ item measures with F1 .69–.83, but VP scenarios at F1 .05–.11 (Table 4, p.7). RQ4: demographic persona prompts shift questionnaire answers in human-like directions (cosine +0.60) but produce no coherent shift in generation behaviour (cosine −0.03; Table 5, p.8).

**(c) Findings relevant to FinPersona.** (i) "Persona prompts exploit this transparency" (§1, p.2) — explicit lexical cues in a prompt drive construct-consistent responses where the measurement surface is transparent; realistic decision contexts show no such shift. FinPersona's O3 result ("richer behavioral vocabulary amplifies both the benefit for aligned personas and the cost for misaligned ones", App. G p.25) and the DistilBERT persona classifier reaching 87–98% P(intended persona) under memory (App. F, L) are both consistent with lexical transparency rather than an internalised disposition: re-injecting persona words makes rationales *sound* like the persona (Song's RQ3 mechanism) without implying stable behaviour — which is exactly FinPersona's own "dissociation" observation for Qwen2.5-7B (§4.4, p.10). (ii) Supports FinPersona's decision to score *actions* (MAS on cash fraction) rather than questionnaires. (iii) Directly undercuts the MBTI-as-vocabulary defence: if personas work by vocabulary cues, the Big Five replication in App. G does not show framework-independence — it shows the same cue mechanism under a second vocabulary.

**(d) ORIGINAL claims.** *Supports* behaviour-vs-self-report scoring. *Contradicts* (conceptually) the inference FinPersona draws from the O3 ablation ("MSD being framework-independent ... the behavioral content encoded in the mandate ... drives the observed effects", App. G p.25) — Song's evidence says persona-vocabulary effects are cue-driven and do not transfer to generation behaviour in realistic contexts; FinPersona's O3 numeric-only persona removing the ENTJ penalty (−0.028 vs +0.131) is *more* consistent with Song than with a disposition account. *Irrelevant* to synthetic market, metrics, compounding, placebo mechanics, frequency.

**(e) REFRAMED claim.** Bears on the "content-modulated" part: Song predicts that the direction of the shift should follow the lexical content of the directive (protective words → cash), which is what FinPersona reports; it does not anticipate the trading result itself.

**(f) Cite?** Yes. Differentiation: "Song et al. (2026) show that persona prompts move questionnaire answers but not generation behaviour in realistic contexts because questionnaire items are lexically transparent; our action-level MAS is not transparent in that sense, but our numeric-only (O3) ablation — which removes the ENTJ over-trading penalty — indicates that much of the re-grounding effect is carried by persona vocabulary, consistent with their cue-based account."

---

## 8. Chen, Ding, Shen, Guo, Huang, Liu & Zhang (2026) — AlphaSAGE: Structure-Aware Alpha Mining via GFlowNets for Robust Exploration

**(a) Citation.** B. Chen, H. Ding, N. Shen, T. Guo, J. Huang, L. Liu, M. Zhang. "AlphaSAGE: Structure-Aware Alpha Mining via GFlowNets for Robust Exploration." ICLR 2026; arXiv:2509.25055v3 [q-fin.CP], 19 May 2026. 28 pp.

**(b) Summary.** Formulaic alpha mining: RGCN encoder on expression ASTs, GFlowNet sampler with trajectory-balance loss, composite reward = IC + structure-aware reward + novelty (Eqs. 11–16, pp.6–7), dynamic linear combination à la AlphaForge. Evaluated on CSI300/500/1000 and S&P500 2010–2024 with IC/ICIR/RIC/RICIR and AR/MDD/SR (Table 1, p.9); ablations (Table 2, p.10); sensitivity, runtime, seeds (App. E). LLM use limited to an LLM-based baseline (AlphaAgent) and "language-related assistance" (App. A).

**(c) Findings relevant to FinPersona.** Essentially none. It uses MDD as a standard portfolio-risk metric (App. D.1, p.18), which FinPersona also uses as CI; and it reports that IC-optimised signals can underperform in "short, highly stressed windows" (E.8, p.25) — a reminder that regime (crash vs calm) changes the mapping from signal to P&L, loosely consonant with FinPersona's regime-dependence.

**(d) ORIGINAL claims.** Irrelevant to all FinPersona claims.

**(e) REFRAMED claim.** Does not bear on it.

**(f) Cite?** No (it would be a weak "LLM-adjacent quant finance" citation at best). If cited, only as: "Quantitative finance work such as AlphaSAGE (Chen et al., 2026) optimises predictive signals on historical data; FinPersona does not evaluate profitability but mandate adherence."

---

## 9. Dongre, Rossi, Lai, Yoon, Hakkani-Tür & Bui (2025) — Drift No More? Context Equilibria in Multi-Turn LLM Interactions

**(a) Citation.** V. Dongre, R. A. Rossi, V. D. Lai, D. S. Yoon, D. Hakkani-Tür, T. Bui. "Drift No More? Context Equilibria in Multi-Turn LLM Interactions." arXiv:2510.07777v2 [cs.CL], 21 Nov 2025. AAAI 2026 Workshop on Personalization in the Era of Large Foundation Models. 14 pp.

**(b) Summary.** Defines context drift as turn-wise KL divergence between a test model's token distribution and a goal-consistent reference (GPT-4.1) conditioned on the same history (§3, p.2). Proposes a recurrence D_{t+1} = D_t + g_t(D_t) + η_t − δ_t with restoring force and intervention term δ_t (Eq. 1, p.3) and a contraction bound (Eq. 3). Two settings: a synthetic constrained-rewriting task with escalating conflicting instructions (8 turns; Llama-3.1-8B/70B, Qwen2-7B) and τ-Bench user simulation (retail, airline). Finds drift "stabilizes at finite levels" rather than growing unboundedly (Abstract; §6 p.4; Fig. 1 p.4) and that explicit goal reminders at turns 4 and 7 lower the equilibrium (Table 2 p.6: KL −6.5% to −11.8%, judge +16–27%; Table 3: estimated D* for Llama-8B 20.4 → 17.6, but Llama-70B 14.8 → 15.7, i.e. slightly *up*). Fig. 3 caption (p.5): "in some cases drift resumes in later turns despite interventions, reflecting model-specific susceptibility".

**(c) Findings relevant to FinPersona.**
* Prior formalisation of "drift" with an explicit equilibrium/intervention model — competes with FinPersona's MSD formalisation (which is verbal, plus metrics).
* Reminder interventions = re-grounding at sparse intervals (k=4,7 of 8–10 turns) — a prior instance of the *injection-frequency* idea, with the finding that benefits are model-specific and not monotone.
* Central empirical claim: in genuinely multi-turn settings drift does **not** compound; it reaches a noise-limited plateau. This *contradicts* FinPersona's framing of MSD as "a compounding phenomenon that widens the behavioral gap ... by 4.4x over the simulation horizon" (Conclusion, p.10) — at least as a general property of LLM drift. FinPersona's own Fig. 3 flat-market panel ("static agents remain stable through Q2 before drifting upward", p.8) and App. E T=800 run ("MSD compounding beyond T=200 rather than plateauing") are the only evidence offered for compounding; given the static agent is stateless, any growth over quarters can only come from the scenario's phase structure (τ1/τ2/τ3) or from indicator values, not from accumulating context.
* Related-work (p.2) explicitly groups Laban 2025, Abdelnabi 2024 and Mehri 2025 as "instruction drift" — the same cluster FinPersona should cite.

**(d) ORIGINAL claims.** *Partially anticipates* MSD formalisation (as a dynamical process), re-grounding as intervention, injection-frequency (sparse reminders), model-dependence and "not universally beneficial" (Llama-70B D* rises). *Contradicts* the "compounds over time" claim as a general property and supplies a competing interpretation (equilibrium). Does not anticipate finance, synthetic V_t, metrics, placebo, persona frameworks.

**(e) REFRAMED claim.** Bears partially: reminders restating the goal reduce divergence and are model-specific; no imperative/declarative contrast, no placebo, no trading.

**(f) Cite?** **Yes, required**, and FinPersona must reconcile "compounds" with "equilibrium". Suggested sentence: "Dongre et al. (2025) model multi-turn drift as a bounded stochastic process with a restoring force and show goal reminders lower but do not eliminate the equilibrium; because our agents are stateless, the quartile-wise widening we observe in the crash scenario reflects regime phase rather than accumulated context, and we make no claim about unbounded growth."

---

## 10. Hashimoto, Takayanagi, Suzuki & Izumi (2025) — Agent-Based Simulation of a Financial Market with Large Language Models

**(a) Citation.** R. Hashimoto, T. Takayanagi, M. Suzuki, K. Izumi. "Agent-Based Simulation of a Financial Market with Large Language Models." arXiv:2510.12189v1 [cs.CE], 14 Oct 2025 (Simulacra Inc. / U. Tokyo). 20 pp.

**(b) Summary.** FCLAgent: an LLM (Llama 3.1 8B in the multi-agent runs; GPT-4o, Qwen-2.5 7B added for single-turn analysis) decides *only* buy/sell direction from a text prompt containing portfolio, unrealized gain, current price, all-time high/low, trading history and order-flow imbalance; order price/volume come from the classical Chiarella–Iori FCN rule (§3.3, p.7). 1,000 agents in a PAMS limit-order-book market, 500 simulated days, fundamental price = zero-drift GBM (§4.1, p.8). Replacing 1–5 FCN agents by FCLAgents reproduces the all-time-high anomaly (β_h < 0; Table 2, p.11) while preserving stylized facts (Table 3). Single-turn experiments (Alg. 1, §6, pp.13–14, 100 trials per cell) show disposition-effect-like behaviour: net sell in gain states, net buy in loss states, modulated by the ATH/ATL reference point (Table 4, p.14); Qwen-2.5 7B behaves differently from GPT-4o/Llama in gain states.

**(c) Findings relevant to FinPersona.**
* A *single-turn, stateless* LLM trading decision elicited from a text prompt (Alg. 1) — the same call structure as FinPersona's static agent — produces systematic, context-dependent, model-dependent biases. This is prior evidence that the per-step decision distribution is shaped by prompt content and that model identity matters (Qwen differs; FinPersona also singles out Qwen2.5-7B).
* The prompt (App. A, p.16–17) contains behavioural directives ("Try to keep your portfolio balanced. If you feel you are holding a lot of stocks ... you should sell them"; "Try to keep your order volume as non-zero and not-extreme") and the authors note the resulting asset proportion stays in [0.11, 0.48] (Fig. 3, p.11) — an instance of an imperative prompt directive shaping allocation.
* A fundamental price hidden from the LLM (agents see price/ATH/ATL, not p^f_t) — the "hidden fundamental value" design in an LLM-agent market, though used for market realism rather than for scoring rationality.
* Their methodological warning (§6, p.15): "simulations may appear plausible at the aggregate level while failing to capture the underlying psychological mechanisms" — verify intended tendencies per model.

**(d) ORIGINAL claims.** *Partially anticipates* hidden fundamental value in an LLM-agent market and model-dependence of LLM trading behaviour; *supports* the decision to make LLM choose direction only with numeric mechanics handled outside the LLM (FinPersona similarly constrains to {BUY,SELL,HOLD} + quantity). Does not anticipate MSD, mandates, re-grounding, metrics, placebo.

**(e) REFRAMED claim.** Bears partially: shows that in a stateless single-turn trading prompt, imperative allocation instructions and reference-point context move buy/sell behaviour, and that effects are model-dependent (Qwen outlier). No re-injection contrast, no placebo, no persona mandates.

**(f) Cite?** Yes, in Related Work "agent-based market simulations" (FinPersona cites Yang 2025, Piao 2025, Zou 2026 there). Differentiation: "Hashimoto et al. (2025) embed LLM buy/sell intentions in a multi-agent limit-order-book market to reproduce path-dependent anomalies; we isolate a single LLM agent against an exogenous price path with an exact hidden V_t so that mandate violations can be scored without market feedback."

---

## 11. Buakhaw et al. (2025) — Deflanderization for Game Dialogue: Balancing Character Authenticity with Task Execution in LLM-based NPCs

**(a) Citation.** P. Buakhaw, K. Kerdthaisong, P. Phenhiran, P. Khlaisamniang, S. Vorathammathorn, P. Ittichaiwong, N. Yongsatianchot. "Deflanderization for Game Dialogue: Balancing Character Authenticity with Task Execution in LLM-based NPCs." arXiv:2510.13586v3 [cs.CL], 26 Oct 2025 (CPDC 2025 system report, TU_Character_lab). 16 pp.

**(b) Summary.** Competition report (Sony CPDC 2025). API track (GPT-4o-mini only): a "Deflanderization" prompt ("Respond naturally and concisely ... Avoid exaggerated roleplay ... Play this character without over-acting", App. C.4, p.12) plus removing world-setting text improves function-call accuracy (Task 1 CPDCscore 0.422 → 0.586; Table 1, p.6) and the combined score (0.510 → 0.601; Table 2). GPU track: Qwen3-14B SFT+LoRA (Table 3, p.7). Observes a trade-off: "methods that improved role-play fidelity sometimes hurt argument correctness, and vice versa" (§6, p.6). Defines "flanderization" as a character "progressively simplified over time, eventually becoming a caricature defined by a single, exaggerated trait" (§1, p.2).

**(c) Findings relevant to FinPersona.** (i) Names and operationalises the *caricature* idea that FinPersona's Caricature Index gestures at ("agents exaggerate their default behavioral tendencies", §3.3.2, p.6) — but in the opposite direction: the fix is to *suppress* persona role-play, and persona emphasis degrades task execution. This is consonant with FinPersona's ENTJ finding that re-injecting an aggressive persona mandate worsens adherence (over-trading) — an instance of persona over-acting hurting a task metric. (ii) Single model (GPT-4o-mini), no long-horizon measurement, no drift over time despite the "over time" definition.

**(d) ORIGINAL claims.** *Partially anticipates* the persona-emphasis-harms-task trade-off underlying "re-grounding is not universally beneficial" (for the aggressive persona). Irrelevant to everything else.

**(e) REFRAMED claim.** Weakly supportive: an imperative style directive ("avoid exaggerated roleplay") changes behaviour in the direction of its content; no placebo, no finance.

**(f) Cite?** Optional. If the CI is kept, cite for the term: "The 'flanderization' trade-off reported for NPC agents (Buakhaw et al., 2025), where persona emphasis degrades task execution, mirrors our finding that re-injecting an aggressive mandate increases over-trading."

---

## 12. Fan, Yang, Jiang, Zhang, Chen & Huang (2025) — AI-Trader: Benchmarking Autonomous Agents in Real-Time Financial Markets

**(a) Citation.** T. Fan, Y. Yang, Y. Jiang, Y. Zhang, Y. Chen, C. Huang. "AI-Trader: Benchmarking Autonomous Agents in Real-Time Financial Markets." arXiv:2512.10971v1 [q-fin.CP], 1 Dec 2025 (HKU). 17 pp.

**(b) Summary.** Live, tool-using (MCP) trading benchmark: Nasdaq-100 (hourly), SSE-50 (daily), 10 crypto pairs (daily); agents receive only positions, prices and tools and must search/verify information themselves (§3, pp.3–7). Six models (DeepSeek-v3.1, MiniMax-M2, Claude-3.7-Sonnet, GPT-5, Qwen3-Max, Gemini-2.5-Flash), Oct–Nov 2025. Metrics CR/Sortino/Vol/MDD (Table 1, p.9). Findings: general capability ≠ trading skill; "risk control capability is the key determinant"; cash management matters (DeepSeek held ~41% cash in the crypto crash, the only agent to beat the index, p.9); models adopt different position-sizing across markets (Table 2, p.10); "hold-to-die" passivity for Gemini (p.8); case study of a news-driven misjudgement (p.11). Basic agent prompt: "Your long-term goal is to maximize returns" (App. A, p.16).

**(c) Findings relevant to FinPersona.** (i) Strong model-dependence of trading behaviour (incl. passivity and cash-holding) under an identical goal prompt — supports FinPersona's "MSD is model-dependent" at the level of base behaviour, and shows passivity/cash is a natural default for some models (relevant to interpreting the ISFJ/flat-market "17/18" as possibly partly a cash-default effect). (ii) Historical/live data where "the correct action is debatable" — this is the limitation FinPersona uses to motivate its synthetic engine (§2, p.3). (iii) No mandates, no re-grounding, no persona, no horizon-over-time analysis.

**(d) ORIGINAL claims.** *Supports* model-dependence; *motivates* (by contrast) the decoupled synthetic ground truth. Irrelevant to MSD, metrics, compounding, placebo, ablations.

**(e) REFRAMED claim.** Does not bear on it, except as evidence that "shift toward cash/inaction" is a behaviour some models exhibit spontaneously — a confound FinPersona's per-persona baselines must absorb (the static ISFJ already sits at MAS≈0.90 cash in Table 5, leaving little room).

**(f) Cite?** Yes, in the "short-term trading returns / live benchmarks" sentence of Related Work alongside StockBench (already cited). Differentiation: "AI-Trader (Fan et al., 2025) evaluates profitability of tool-using agents in live markets; we evaluate adherence to a fixed mandate in a synthetic market with known ground truth."

---

## 13. Saini, Tang & Liu (2026) — Bridging Mechanistic Interpretability and Prompt Engineering with Gradient Ascent for Interpretable Persona Control

**(a) Citation.** H. Saini, Y. Tang, D. Liu. "Bridging Mechanistic Interpretability and Prompt Engineering with Gradient Ascent for Interpretable Persona Control." TMLR (6/2026); arXiv:2601.02896v4 [cs.LG], 26 Jun 2026. 19 pp.

**(b) Summary.** RESGA / SAEGA: build a persona steering vector (mean activation difference, or top-K SAE latents) for sycophancy / hallucination / myopic reward; run fluent gradient ascent (EPO) to discover 8-token prompts whose last-token representation points away from the persona direction (§3, pp.4–6). Llama 3.1 8B, Qwen 2.5 7B, Gemma 3 4B. Discovered prompts cut sycophancy to ≈50% (neutral) vs 70–86% zero-shot and 70–80% for a manual "Standard Prompt" (Table 1, p.8). SAEGA preserves SAE sparsity (L0 ≈ 50–60) where dense steering explodes it (Fig. 4, p.9). Discovered prompts are often incoherent; seed-initialised ones more readable (Table 3, p.11).

**(c) Findings relevant to FinPersona.** (i) Manual imperative prompts ("Answer honestly", "Let's think critically and disagree if necessary") shift behaviour only partially and inconsistently across models (Table 1: Standard Prompt 70.5/72.0/80.0) — a prior showing that natural-language directives have model-dependent, modest effects. (ii) "Prompt-based methods induce a divergence starting at early layers, allowing the steering signal to compound across depth" (App. A.2.2, p.19) — note "compound" here means across *layers*, not across turns. (iii) Token-priming via induction heads (p.10–11): prompts can work by surface token copying rather than semantics — relevant to interpreting why mandate vocabulary in the rationale rises to ≥0.98 under re-injection (FinPersona Table 12) without a proportional behavioural change.

**(d) ORIGINAL claims.** *Irrelevant* to most. *Partially relevant* to "MBTI-as-vocabulary" and to the LCR/rationale analysis (surface-token effects of appended prompts). Offers tooling for FinPersona's stated mechanistic future work.

**(e) REFRAMED claim.** Tangential: demonstrates that appended short prompts shift behaviour, with content-specificity and model-dependence, and that manual directives are weaker than optimised ones. Does not involve finance or placebo.

**(f) Cite?** Optional (future-work pointer). "Prompt-level persona control can be grounded in activation directions (Saini et al., 2026); our behavioural re-grounding effect could be examined with such tools to test whether it reflects persona-direction shifts or surface token priming."

---

## 14. Zhang et al. (2026) — Locate, Steer, and Improve: A Practical Survey of Actionable Mechanistic Interpretability in LLMs

**(a) Citation.** H. Zhang, Z. Zhang, M. Wang, Z. Su, Y. Wang, Q. Wang, S. Yuan, E. Nie, X. Duan, F. Han, Q. Xue, Z. Yu, C. Shang, X. Liang, J. Xiong, H. Shen, C. Tao, Z. Liu, S. Jin, Z. Xi, D. Zhang, S. Ananiadou, T. Gui, R. Xie, H. K.-H. So, H. Schütze, X. Huang, Q. Zhang, N. Wong. "Locate, Steer, and Improve: A Practical Survey of Actionable Mechanistic Interpretability in Large Language Models." arXiv:2601.14004v4 [cs.CL], 14 Apr 2026. 101 pp. (52 pp. body + 48 pp. Table 5 and references).

**(b) Summary.** Survey organised as Locate (magnitude analysis, causal attribution, gradient detection, probing, vocabulary projection, circuit discovery; §3) → Steer (amplitude manipulation, targeted optimisation, vector arithmetic; §4) → Improve (alignment: safety, fairness, *persona and role*; capability; efficiency; §5). Tables 2–3 compare methods; Table 4 proposes an evaluation framework; Table 5 tags >200 papers. Limitations: dense decoder-only focus, no benchmark consensus (§6, p.49–51).

**(c) Findings relevant to FinPersona.** §5.1.3 "Persona and Role" (pp.37–39) catalogues persona vectors (Chen et al. 2025d), role vectors (Potertì), NPTI personality neurons (Deng), ValueLocate, layer-wise Big-Five probing (Ju et al. 2025: personality "encoded in the middle and upper layers"), PsySET side effects (Banayeeanzade: "joy" steering reducing privacy awareness), and Bas & Novak (steering works for latent traits but not knowledge-heavy personas). §5.1.2 cites Dimino et al. (2025, ICAIF) tracing positional bias "in financial advisory tasks" to mid-to-late layers of Qwen2.5 — the one finance-specific mechanistic item. §5.2.2 "Knowledge Retention and Stability" covers context-injection conflicts and "entrainment" heads (Niu et al. 2025) — mechanisms by which recent context overrides prior instructions. Also notes (Table 3 commentary, p.33) inference-time steering is "more sensitive to prompt variation".

**(d) ORIGINAL claims.** Irrelevant to all empirical FinPersona claims. Relevant only to FinPersona's future-work sentence on mechanistic accounts and to the MBTI/Big-Five vocabulary question (persona vectors exist for Big-Five-style traits, not for MBTI types).

**(e) REFRAMED claim.** Does not bear on it.

**(f) Cite?** Optional, one sentence in Conclusion/future work; prefer citing the primary persona-vector papers it surveys (Chen et al. 2025 "Persona Vectors", Ju et al. 2025 COLM) rather than the survey.

---

# SYNTHESIS (share 1)

### A. FinPersona claims fully anticipated by papers in this share
* **Behaviour-level (action-based) measurement of goal/mandate adherence of an LLM trader over a long horizon, with model-dependence and drift-through-inaction** — Arike et al. (2025). This covers the methodological core of FinPersona's contribution 1 ("behavioral failure distinct from reasoning errors") and the general "MSD is model-dependent" claim, in a *trading* environment.
* **Per-turn re-injection of the goal as a mitigation, with model- and dimension-dependent reversals** — Mehri et al. (2026) App. E/Table 7; Dongre et al. (2025) reminders; Laban et al. (2025) SNOWBALL. "Re-grounding is not universally beneficial" is therefore not new as a proposition; what is new is the *persona-content sign flip* (protective vs growth) in a trading task.
* **"Drift" formalisation** — Dongre et al. (2025) give an explicit dynamical formalisation with an intervention term; Abdelnabi et al. (2025) formalise single-turn task drift. FinPersona's "MSD formalisation" is a verbal definition plus three metrics; the word "formalize" in the abstract overstates it relative to these.

### B. Claims that remain unclaimed by this share
* Decoupled *exact* hidden V_t used to score an LLM agent's rationality (RG) — not in this share (Hashimoto hides a fundamental price but does not score agents against it; ABIDES uses it for background agents).
* Three named regime failure modes, MAS/CI/RG as defined, the 4.4x crash quartile ratio, T-calibration, injection-frequency table (k ∈ {1,5,25,100,∞}), LCR rationale metric, Big-Five/O3 replication, length-matched placebo in a trading context.
* The specific REFRAMED result (17/18 vs 16/18 split; protective ≫ growth ≫ neutral; placebo null).

### C. Direct competitors
* **Arike et al. (2025)** — LLM trading simulation measuring goal drift behaviourally over >100K tokens, 4 models, 20 seeds, strong-vs-weak imperative elicitation, inaction drift, model-dependence, mechanism ablations. Must be cited and differentiated; it is currently absent from FinPersona's bibliography.
* **Dongre et al. (2025)** — prior formalisation of context drift and reminder interventions, with the opposite macro-conclusion (equilibrium, not compounding).
* **Mehri et al. (2026)** — prior per-turn goal re-injection with mixed effects.

### D. Findings in this share that CONTRADICT a specific FinPersona result or framing
1. **"MSD compounds over time ... 4.4x by Q4" (Abstract; §4.3.2 p.8; Conclusion p.10).** Dongre et al. find drift in genuinely multi-turn settings reaches a bounded equilibrium ("stable, noise-limited equilibria rather than runaway degradation", Abstract); Laban et al. find degradation appears at turn 2 and is dominated by variance. FinPersona's agents are stateless (A_t ~ P(A | Ψ, O_t)), so the quartile widening cannot arise from accumulated context; it is a function of scenario phase (τ1=80 deterioration, τ2=60 panic, τ3=60 stabilisation) — the 4.4x should be described as regime-dependence, not compounding.
2. **Mechanism statement: "mandate has lost influence relative to the surrounding context" / "immediate market observations overwhelm initial instructions" (§1 p.1; §3.2 p.5).** Arike et al. §5.1 show token distance from the system prompt is not what drives drift; in-context behavioural examples are. FinPersona never varies context length, so this causal language is unsupported and contradicted by the nearest prior art.
3. **"Framework-independent ... behavioral content ... rather than the psychometric instrument ... drives the observed effects" (App. G, p.25).** Song et al. (2026) show persona-prompt effects are carried by lexical cues and do not transfer to realistic generation; FinPersona's own O3 result (ENTJ penalty +0.131 → −0.028 when persona vocabulary is removed) is better explained as vocabulary-cue dependence than as framework independence.
4. **"Placebo control indicating that re-grounding works through mandate content rather than text position" (Contributions, p.2).** App. F reports Static-vs-Placebo *is* significant (p=0.041, always worse) while Static-vs-Memory is not (p=0.890) at the aggregate level, and the ISFJ row of Table 5 (0.903 static / 0.950 placebo / 0.730 memory) is labelled "MAS deviation, lower is better" yet the text says memory "improv[es] it for ISFJ (−0.173)" — the table values look like cash fractions, not deviations. Mehri et al. and Dongre et al. show that reminders have position-independent but model-dependent effects; with n=15 pairs on one model, the placebo result does not license the general claim in the contributions list. (Not a contradiction from my share per se, but the prior art's effect sizes make the one-model placebo insufficient.)
5. **Persona-stability claims rest on n=3–5 seeds at T=0.** PERSIST shows SD>0.3 on 5-point scales from question order alone even at 400B+; FinPersona's Tables 5–8 (n=5, n=3) are within this noise band and several reported effects (e.g. INTJ "range of only 0.005") are unlikely to be stable.

### E. Bearing on the REFRAMED claim (whole share)
No paper owns the REFRAMED claim. Closest partial anticipations: Arike (imperative directive moves LLM trading behaviour, model-dependently, in a trading sim); Mehri App. E (per-turn verbatim goal reminder, mixed per-dimension effects); Dongre (reminders lower divergence, model-specific); Hashimoto (stateless single-turn trading prompt with imperative allocation instructions shaping allocation; Qwen outlier); Abdelnabi (end-positioned instructions vs instruction-free text produce very different internal shifts). Song et al. predicts the content-modulation sign. None include a length-matched placebo in a trading task or the protective/growth/neutral split. The REFRAMED claim survives as novel in this share, with the caveats that (i) its "stateless" framing must be made explicit and (ii) AI-Trader and Hashimoto show that cash-holding/passivity is a spontaneous model default, so the ISFJ 17/18 should be reported alongside the static cash baseline (already ≈0.90 for Sonnet 4.6).

### F. Recommended citations from this share (priority order)
1. Arike et al. 2025 (must), 2. Dongre et al. 2025 (must), 3. Mehri et al. 2026 (should), 4. Laban et al. 2025 (should; replace/augment "Context Rot"), 5. Song et al. 2026 (should), 6. Tosato et al. 2025 PERSIST (should), 7. Hashimoto et al. 2025 (should, in ABM sentence), 8. Fan et al. 2025 AI-Trader (should, in live-benchmark sentence), 9. Abdelnabi et al. 2025 (optional, mechanistic), 10. Byrd et al. 2019 ABIDES (optional, lineage), 11. Buakhaw et al. 2025 (optional, CI term), 12. Saini et al. 2026 and 13. Zhang et al. 2026 survey (optional, future work), 14. AlphaSAGE (no).


---

# CYCLE-1 AGREEMENT / DISAGREEMENT LIST (written after the per-paper assessments above)

Read after completing the assessments: `cycle1_report.txt` (Consolidated Three-Reviewer Audit, 20 Aug 2026) including its 19-claim novelty table (C1–C19), the verification register, the competitive position map, and the error register. Only attributions that name a paper in my share are adjudicated; papers outside my share (Meta 2607.08716, Kim/Li COLM 2024, CLQT, ContextEcho, DriftBench, Menon, Kocielnik, Ross & Lo, Machine Spirits, When Attention Closes, Everitt, Jiang/Peng/Yan) are left to the other reviewer.

Independent confirmations from my own reading of the paper (made before opening Cycle 1):
* Verification-register item 1 (no accumulating context): confirmed from the paper text alone — §3.2 Eq. 3/5 ("stateless predictor"); App. B's "system prompt ... provided only once at the start of the session" is consistent only if each step is its own session. My assessments above were written on this basis.
* Verification-register item 3 (V_t recoverable from P/E): confirmed from Table 2 (p.17): "Reported P/E: Pt/EPSt where EPSt = Vt/15" ⇒ P/E = 15·Pt/Vt; Dividend Yield = (0.4·EPSt/Pt)·100 gives a second exact disclosure. The "Hidden" label in Table 2 is false as implemented.
* Verification-register item 9 (placebo range): confirmed — Table 5 ISFJ 0.950 − 0.903 = 0.047, text says 0.003–0.045. I additionally flag (synthesis D4) that Table 5 is captioned "MAS Deviation (lower is better)" yet the ISFJ row (0.903 / 0.950 / 0.730) reads like cash fractions, and the text's "improving it for ISFJ (−0.173)" only makes sense if the column is cash fraction (memory 0.730 < static 0.903 would be *worse* adherence if it were deviation). Cycle 1 did not note this labelling inconsistency.
* Verification-register item 11 (zero corpus citations): confirmed for my 14 papers by grep of the extracted paper text (Arike, Abdelnabi, Laban, Mehri, Tosato/PERSIST, Song, Hashimoto, Byrd/ABIDES, Dongre, Buakhaw, Fan/AI-Trader, Saini, Zhang survey, AlphaSAGE: 0 hits each; the two string hits for "persist"/"Song" are unrelated words/authors).

Claim-by-claim:

| Cycle-1 claim | Cycle-1 verdict & attribution (my share only) | My verdict | Agree? | Notes |
|---|---|---|---|---|
| C1 Formalising MSD | FULLY ANTICIPATED — "Arike goal drift" (+Meta, Kim/Li outside share) | Arike: *partial* (behavioural goal-drift scores, no dynamical formalisation); **Dongre: strong partial** (explicit recurrence / equilibrium model with intervention term) | Agree in substance; **Cycle 1 omitted Dongre under C1** — it is the closest formalisation in the corpus | FULLY is plausible once Meta/Kim-Li are added |
| C2 Behaviour distinct from reasoning | FULLY ANTICIPATED — no share papers cited | Song et al. (self-report vs generation dissociation) is a direct anticipation and should be listed; Arike Finding 9 shows stated goals *track* behaviour (no dissociation), so Arike should **not** be cited for C2 | Partly agree | Add Song to C2 |
| C3 Decoupled synthetic ground truth | PARTIALLY ANTICIPATED — Hashimoto, ABIDES oracle | Same | **Agree** | ABIDES's "oracle" is historical data for background agents; the hidden-value idea it inherits is Wang & Wellman's. Hashimoto hides p_f from the LLM but does not score the LLM against it — Cycle 1's "narrowly ahead on V as scoring criterion" is right, modulo the P/E leak |
| C5 MAS | PARTIALLY ANTICIPATED — Arike GD_actions | Same | **Agree** | Arike GD_actions = goal-aligned share of budget minus baseline; also counts "save up its budget" as drift (inaction), the mirror of MAS for ISFJ |
| C6 Caricature Index | NAME ANTICIPATED — Deflanderization | Same | **Agree** | Buakhaw et al. define flanderization and show persona emphasis harms task execution; they measure nothing over time. MDD is the standard risk metric in AlphaSAGE and AI-Trader too |
| C7 Rationality Gap | PARTIALLY ANTICIPATED — "ABM fundamentalist component" (Hashimoto) | Same, weaker | **Agree** (mild) | The FCN fundamentalist term is a rule-based price forecast, not a rationality score; anticipation is conceptual only |
| C8 Model-dependence | FULLY ANTICIPATED — PERSIST, Arike Finding 4 | Same; add AI-Trader (6 models; passivity/cash defaults), Hashimoto (Qwen outlier), Laban (15 models), Mehri (5 models) | **Agree** | — |
| C9 Compounding / 4.4x | ANTICIPATED AND CONTRADICTED — Drift No More | Agree on Dongre. **Nuance:** Arike Finding 6 shows drift *increasing* with instrumental-phase length in genuinely multi-turn goal-switching (driven by in-context examples, not distance), so "contradicted" is not unanimous for multi-turn settings. For FinPersona's stateless design neither applies; the 4.4x is regime-phase structure. Laban adds that degradation is present from turn 2 and variance-dominated | Agree with verdict; add nuance | Cycle 1's expanding().min() code finding is outside my remit but is consistent with the stateless design |
| C10 Re-grounding not universally beneficial | PARTIALLY ANTICIPATED — no share papers cited | **Cycle 1 missed two direct anticipations in my share:** Mehri et al. 2026 (§6.3 "different models react differently to inference-time steering"; App. E Table 7 per-turn goal reminder with category drops) and Dongre et al. 2025 (Llama-70B equilibrium rises under reminders; "drift resumes in later turns") | **Disagree on completeness** — with these the broad form is FULLY anticipated (consistent with Cycle 1's own S1 statement that the broad form "is settled") | Content-driven sign reversal remains unclaimed |
| C11 Placebo control | FULLY ANTICIPATED — incl. "Arike token-distance ablation" | Arike's ablation is a length-matched *context* filler (repeated token replacing the instrumental phase) to test the distance hypothesis, not a placebo for an appended directive; it anticipates the *logic* (length-matched content-free control) but not the 3-arm design | **Partially disagree** on the Arike attribution (over-stated); cannot adjudicate ContextEcho / When-Attention-Closes | Net verdict may still be FULLY via the other two |
| C12 Big Five & O3 ablation | PARTIALLY ANTICIPATED — Song, PERSIST | Same; Song RQ3/RQ4 (lexical transparency; persona shifts do not transfer to generation) is the key one and *undercuts* the framework-independence inference (synthesis D3) | **Agree** | — |
| C13 Injection-frequency | FULLY ANTICIPATED — Kim/Li (outside share) | From my share: Dongre (reminders at t=4,7) and Mehri (every turn) are partial anticipations of sparse vs dense reminding | Agree at least partial; cannot verify Kim/Li | — |
| C17 MBTI-as-vocabulary | ANTICIPATED and undercut — Song, PERSIST | Same | **Agree** | — |
| C18 Selective re-grounding | FULLY ANTICIPATED — Meta, CLQT (outside share) | Dongre's "design minimal interventions to keep alignment near equilibrium" is a partial anticipation | Agree at least partial | — |
| C19 Transfer to triage/legal | ANTICIPATED — Menon (outside share) | PERSIST names finance/legal/medical as deployment risks; Dongre names "safety-critical settings" as future work; neither executes it | Neutral | — |
| S2 "longest-horizon ground-truthed instrument" — "Arike approx. 30 steps; Drift No More approx. 10 turns" | — | Arike setting 2 = 30 eval steps, but settings 3/4 run up to 64 instrumental + 10 eval = 74 steps and "more than 100,000 tokens" (Table 1 p.22: 92K–115K); Dongre 8–10 turns is correct | **Minor correction**: state Arike as up to 74 steps / >100K tokens — still fewer steps than 200 stateless calls but far more tokens than FinPersona's constant-length prompts | Supports Cycle 1's "200 memoryless calls is not 200 turns" |
| Competitive map: "ABIDES citation is mis-specified; Hashimoto is the correct existence proof" | — | Agree: ABIDES has no LLM agents; Hashimoto (FCLAgent in PAMS LOB, 500 days) is the LLM-agent synthetic-market existence proof | **Agree** | — |
| Tier-0 citation list (Arike, Drift No More, Hashimoto, ABIDES, Deflanderization from my share) | — | Agree, and **add** Laban 2025, Mehri 2026, Song 2026, Tosato 2025 (PERSIST), Fan 2025 (AI-Trader), Abdelnabi 2025 — all absent from the paper and all directly relevant (synthesis F) | Agree + extend | — |

Things Cycle 1 got right that I independently corroborate from this share: the mechanism ("mandate loses influence relative to context") is unsupported by design and contradicted by the nearest prior art (Arike §5.1); Dongre's equilibrium result is uncited and cuts against "compounds"; Song/PERSIST undercut the psychometric framing; the surviving content-isolated sign reversal (17/18 vs 16/18) is not owned by any paper in my share.

Things Cycle 1 missed or under-weighted in this share: (i) Mehri et al. 2026 and Dongre 2025 as prior evidence for C10; (ii) Laban et al. 2025 SNOWBALL as the closest prior per-turn-repetition intervention and loss-in-middle-turns as the recency premise; (iii) Song et al. belongs under C2 as well as C12/C17; (iv) the Table 5 "deviation vs cash-fraction" labelling inconsistency; (v) AI-Trader and Hashimoto showing cash-holding / passivity as a spontaneous model default — a confound for reading the ISFJ 17/18 as mandate-driven rather than a generic caution shift (dovetails with Reviewer B's "uniform cash shift refracted through oppositely-signed targets").

Things Cycle 1 over-stated in this share: Arike's token-distance ablation as a full anticipation of the placebo design (C11); Arike's horizon ("approx. 30 steps").
