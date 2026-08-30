# Related Work Update — August 2026 (Verified New References)

**Purpose.** Deep-research sweep to refresh the FinPersona-Bench related work, covering papers released (or missed) since the April 2026 COLM submission. Every paper below was (1) found via themed literature search, (2) checked against the current paper's reference list and the revision-plan reading list to avoid duplicates, (3) **downloaded into this repo** at `references/related_work_2026/`, and (4) **read from the full extracted text** — title, authors, venue, and claims verified against the PDF itself, not just abstracts or search snippets. None of the 22 papers below appears in the post-rebuttal paper's references.

**Scope note.** Excluded by design: everything already cited in `docs/COLM_FinPersona_Bench_Post_Rebuttal.pdf`, and the mechanistic-interpretability anchors already collected in `references/mech_interp/` (Arditi 2024; Chen/Lindsey 2025 persona vectors; Li et al. 2024 instruction instability; Meng 2022 ROME; Xiao 2023 attention sinks; Templeton 2024; plus revision-plan classics Jiang/Peng/Yan 2024, ABIDES, Cont 2001).

---

## Strategic highlights (read this first)

Three of the new papers materially affect the revision plan, not just the citation list:

1. **"When Attention Closes" (Dongre et al., 2605.12922) partially does M1 already.** It tracks attention mass on system-prompt goal tokens across multi-turn interactions (their "Goal Accessibility Ratio"), shows monotonic decline in all 10 architectures tested (27–48% drop over 50 turns), causally verifies via attention-window ablation, and shows goal info persists in the residual stream (probe AUC up to 0.99) while attention access decays. The M1 experiment must cite and **differentiate** (FinPersona: 200-step economically grounded rollouts, behavioral MAS/CI outcomes, re-injection arm) rather than present attention-decay tracking as novel.
2. **"Proactive Memory Agent" (Meta AI, 2607.08716) is the closest precedent for the planned adaptive re-grounding controller.** It names "behavioral state decay" (instructions in-context stop controlling behavior), and shows *selective* injection beats always-on injection — always-on can hurt — which is exactly FinPersona's persona–scenario alignment finding generalized. Cite as convergent evidence and differentiate: their trigger is a learned memory-agent policy; the revision plan's trigger is an interpretable internal drift signal (M2 direction).
3. **"Drift No More?" (Dongre et al., 2510.07777) is the sharpest published *counter-position*.** It argues multi-turn drift settles into bounded equilibria and goal reminders reliably help (KL ↓6.5–11.8%). FinPersona's compounding-MSD and re-grounding-can-hurt findings directly complicate this — but their horizons are ≤10 turns vs. FinPersona's 200 steps. Address explicitly in related work: short-horizon equilibrium vs. long-horizon compounding under sustained directional context pressure.

Also notable: **CLQT (2606.29771)** is the closest finance-benchmark neighbor on the mandate axis (it scores per-round "mandate alignment" and "style drift"), and **Inherited Goal Drift (2603.03258)** studies goal drift in a *simulated stock-trading environment* — the nearest-neighbor paper overall. Both must be cited and differentiated.

---

## A. Behavioral drift & long-horizon degradation

### A1. LLMs Get Lost in Multi-Turn Conversation — **must-cite**
- **Laban, P., Hayashi, H., Zhou, Y., Neville, J.** — arXiv:2505.06120 (May 2025). Microsoft Research / Salesforce.
- **PDF:** `references/related_work_2026/2505_06120_LLMs_Get_Lost_Multi_Turn.pdf` · **Verified ✓**
- 200,000+ simulated conversations, 15 LLMs, six generation tasks: all models drop from ~90% single-turn to ~65% multi-turn performance (avg −39%) when instructions arrive gradually ("sharded"). Decomposition: only ~15% aptitude loss, but +112% unreliability. Per-turn restatement of prior information (SNOWBALL) recovers only ~15–20% of the loss.
- **Use:** canonical general-domain citation for context-accumulation degrading behavior; its restatement mitigations prefigure the re-injection arm, which FinPersona complicates (regime-dependent benefit).

### A2. Inherited Goal Drift: Contextual Pressure Can Undermine Agentic Goals — **must-cite (nearest neighbor)**
- **Menon, A., Saebo, M., Crosse, T., Gibson, S., Jang, E., Cruz, D.** — arXiv:2603.03258; **Lifelong Agents workshop @ ICLR 2026**.
- **PDF:** `references/related_work_2026/2603_03258_Inherited_Goal_Drift.pdf` · **Verified ✓**
- Goal drift in a *simulated stock-trading environment* (profit vs. emissions goals) on GPT-5.1, Claude-Sonnet-4.5, Gemini-2.5-Flash, Qwen3-235B, etc. Frontier models show near-zero drift under 30 steps of direct adversarial pressure, but *inherit* drift when conditioned on a weaker agent's drifted trajectory; only GPT-5.1 consistently recovers. Models often verbally identify the correct goal yet fail to act on it. Longer contexts → more drift; effects are environment-dependent.
- **Use:** closest prior work — same domain, same phenomenon class. Differentiate: discrete goal abandonment/inheritance vs. FinPersona's graded, metric-based salience decay against hidden fundamentals, with persona × regime interaction and a re-injection diagnostic. Its say/do gap independently corroborates the mandate–behavior dissociation.

### A3. Drift No More? Context Equilibria in Multi-Turn LLM Interactions — **must-cite (contrast)**
- **Dongre, V., Rossi, R.A., Lai, V.D., Yoon, D.S., Hakkani-Tür, D., Bui, T.** — arXiv:2510.07777; AAAI 2026 workshop (Personalization in the Era of Large Foundation Models).
- **PDF:** `references/related_work_2026/2510_07777_Drift_No_More_Context_Equilibria.pdf` · **Verified ✓**
- Formalizes drift as turn-wise KL to a goal-consistent reference policy and models it as a stochastic recurrence with stable fixed points. Finds drift fluctuates around finite equilibria rather than growing monotonically; goal reminders at turns 4/7 cut KL 6.5–11.8% and raise judge scores +16–27%.
- **Use:** the counter-position. FinPersona should engage directly: bounded equilibria hold at ≤10 conversational turns, whereas MSD compounds over 200 steps of directional market pressure and re-grounding's sign flips with persona–regime alignment. Their recurrence framework offers useful formal vocabulary (re-injection as intervention term whose sign FinPersona shows can be negative).

### A4. Attractor States Emerge in Multi-Turn LLM Conversations — recommended
- **Ko, T.-W., Geiping, J.** — arXiv:2606.30571 (Jun 2026). MPI-IS / ELLIS Tübingen.
- **PDF:** `references/related_work_2026/2606_30571_Attractor_States_Multi_Turn.pdf` · **Verified ✓**
- 20-turn LLM–LLM debates: self-play conversations settle into reproducible model-specific behavioral basins (basin separation > 1 for every model); assigned stances soften, reverse, or persist model-dependently; cross-model influence is asymmetric (Claude Haiku most resistant, α=0.266; GPT-4.1-nano most malleable, α=0.665).
- **Use:** independent evidence that long-run behavior drifts toward *model-intrinsic* defaults that override assigned roles — a conversational analogue of MSD's model-dependent drift profiles.

### A5. When Attention Closes: How LLMs Lose the Thread in Multi-Turn Interaction — **must-cite (M1 precedent)**
- **Dongre, V., Hsieh, J., Lai, V.D., Yoon, S., Bui, T., Hakkani-Tür, D.** — arXiv:2605.12922 (May 2026, preprint). UIUC / Adobe.
- **PDF:** `references/related_work_2026/2605_12922_When_Attention_Closes.pdf` · **Verified ✓**
- Mechanistic account of multi-turn instruction/persona loss: Goal Accessibility Ratio (attention mass from generated tokens to goal tokens) declines monotonically in all 10 architectures (pooled Kendall τ=−0.75; 27–48% decline over 50 turns); causally closing the attention channel collapses recall (Mistral 20-fact: →11.2%) and raises persona violations (0.48) above even adversarial-pressure baselines (0.35); yet goal info stays linearly decodable from the residual stream (AUC ≤0.99). "Retaining text ≠ preserving goal information."
- **Use:** the direct mechanistic precedent for M1 — supplies both the candidate mechanism for MSD (attention-channel closure on mandate tokens) and the reason re-injection works (restores accessibility). Cite prominently and position FinPersona's contribution as behavioral + economic grounding at 4× the horizon with a re-grounding intervention arm; consider adopting/adapting GAR as the M1 metric.

---

## B. Persona fragility & psychometric validity

### B1. Persistent Instability in LLM's Personality Measurements (PERSIST) — **must-cite**
- **Tosato, T., Helbling, S., Mantilla-Ramos, Y.-J., Hegazy, M., et al.** — arXiv:2508.04826; **accepted AAAI 2026 (AI Alignment track)**. Mila.
- **PDF:** `references/related_work_2026/2508_04826_PERSIST_Personality_Instability.pdf` · **Verified ✓**
- 25+ open models (1B–685B), 2M+ responses: question reordering alone shifts measured personality; even 400B+ models show per-question SD >0.3 on 5-point scales; CoT *increases* variability; conversation history increases variability for <50B models (p<0.001); LLM-adapted questionnaires equally unstable. Explicitly flags financial/legal/medical deployment risk.
- **Use:** persona-fragility pillar anchor — trait expression is intrinsically unstable under context perturbation even before market pressure; motivates FinPersona's behavioral (not questionnaire) measurement.

### B2. Rethinking Psychometric Evaluation of LLMs: When and Why Self-Reports Predict Behavior — **must-cite**
- **Kocielnik, R., Han, P., Song, P., Marmarelis, M.G., Debnath, R., Mobbs, D., Anandkumar, A., Alvarez, R.M.** — arXiv:2606.12730 (Jun 2026, preprint). Caltech/UIUC/Cambridge.
- **PDF:** `references/related_work_2026/2606_12730_Rethinking_Psychometric_Eval.pdf` · **Verified ✓**
- 11 frontier LLMs, 4 behavioral tasks (incl. risk-taking): Big Five self-reports are uniformly non-predictive of behavior (|r|≤0.07); task-anchored TPB reaches human-level within-session coherence (r=+0.40) but cross-session coherence collapses for 9/11 models; **persona prompting stabilizes self-reports without restoring behavioral coupling**.
- **Use:** direct independent support for the language–behavior dissociation (their RQ4 = FinPersona's Qwen dissociation at the measurement level); also the principled response to reviewers' MBTI-validity critique — trait vocabulary has weak behavioral validity *by design*, which is why FinPersona measures behavior.

### B3. Human Psychometric Questionnaires Mischaracterize LLM Behavior — **must-cite**
- **Song, W., Choi, D., Park, Y., Han, J., Lee, E.-J., Jo, Y.** — arXiv:2509.10078 (v4 May 2026). Seoul National University.
- **PDF:** `references/related_work_2026/2509_10078_Questionnaires_Mischaracterize_LLMs.pdf` · **Verified ✓**
- Questionnaire-derived vs. generation-derived value/personality profiles diverge (cross-method ρ≈0.11–0.31); apparent questionnaire consistency is an artifact of item textual transparency and vanishes in generation probabilities; persona prompts shift questionnaire answers toward human patterns (3–3.5× magnitude) while generation behavior shifts incoherently (cosine −0.03).
- **Use:** explains *why* re-injection can restore persona language without behavior — models pattern-match transparent persona cues in text; behavior lacks such cues. Strengthens the classifier-vs-MAS dissociation finding.

### B4. Deflanderization for Game Dialogue (CPDC 2025 report) — optional
- **Buakhaw, P., Kerdthaisong, K., Phenhiran, P., et al.** — arXiv:2510.13586 (Oct 2025). CPDC 2025 challenge system report (ranked 2nd on two tracks).
- **PDF:** `references/related_work_2026/2510_13586_Deflanderization_Game_Dialogue.pdf` · **Verified ✓** (note: shared-task report, not a full research paper — weight accordingly)
- Names "flanderization": progressive simplification of a persona into a single-trait caricature, harming task execution; suppressing exaggerated role-play improved task scores (e.g., CPDCscore 0.422→0.586).
- **Use:** a named precedent from a different domain for the Caricature Index phenomenon (surface-trait exaggeration at the expense of substantive function). Cite lightly when introducing the caricature effect.

---

## C. Financial LLM agent benchmarks & simulations

### C1. From Knowing to Doing (KTD-Fin): A Memory-Controlled Benchmark for LLM Trading Agents — **must-cite**
- **Zhu, T., Zhao, W., Sun, R., Luan, B., Lu, J., et al.** — arXiv:2605.28359 (May 2026). Tsinghua / Stepfun.
- **PDF:** `references/related_work_2026/2605_28359_KTD_Fin_Knowing_to_Doing.pdf` · **Verified ✓**
- Data-side masking (tickers + dates anonymized; de-anonymization probe: joint recovery ≤1.5%) plus Barra-style attribution on CSI300. Ticker visibility alone drives trading (memory-only mode: active trades under real names, 0.00% cash under masking); 9/10 frontier agents have *negative* stock-selection alpha despite headline returns up to +85%.
- **Use:** concrete evidence for the contamination argument in the related work — memorized priors, not observed context, drive historical-market results; natural companion citation to the synthetic-market design (masking vs. synthetic generation as two escapes from contamination).

### C2. AI-Trader: Benchmarking Autonomous Agents in Real-Time Financial Markets — recommended
- **Fan, T., Yang, Y., Jiang, Y., Zhang, Y., Chen, Y., Huang, C.** — arXiv:2512.10971 (Dec 2025). HKU.
- **PDF:** `references/related_work_2026/2512_10971_AI_Trader_Live_Benchmark.pdf` · **Verified ✓**
- Live (contamination-free by construction) trading across Nasdaq-100/SSE-50/crypto with minimal-information ReAct agents; general capability doesn't transfer (GPT-5 underperforms QQQ; no agent beats SSE-50); risk control determines robustness; documented single-source herding failure.
- **Use:** state-of-the-art live evaluation that remains returns-centric and short-horizon (~5–6 weeks) — exactly the point-in-time paradigm FinPersona distinguishes itself from; MSD is invisible at that horizon.

### C3. CLQT: Closed-Loop, Cost-Aware, Strategy-Consistent Benchmark for LLM Portfolio Agents — **must-cite (closest finance neighbor)**
- **Qu, B., Chen, M.** — arXiv:2606.29771 (v2 Aug 2026, preprint).
- **PDF:** `references/related_work_2026/2606_29771_CLQT_Portfolio_Benchmark.pdf` · **Verified ✓**
- Per-round ConsistencyScore including **mandate alignment** and style drift (with corrective warning injected below 0.7), five-axis capability scorecard, hash-chained audit. Findings: Sharpe leaders are reliability artifacts; agents' allocations systematically fail to follow their own stated analysis (best-Sharpe config had worst coherence, 0.23); no scaffolding ablation moves returns beyond noise while capability axes register the differences.
- **Use:** convergent evidence that returns cannot certify behavioral consistency and that action–reasoning decoupling is systematic. Differentiate: CLQT *enforces* consistency via an external reconciler on historical/live data; FinPersona *measures uncorrected decay* longitudinally against synthetic ground truth.

### C4. Fin-Bias: LLM Decision-Making under Human Bias in Finance — recommended
- **Hu, X., Zhao, J.** — arXiv:2605.09106 (May 2026). Rutgers / Toronto.
- **PDF:** `references/related_work_2026/2605_09106_Fin_Bias_Human_Bias_Finance.pdf` · **Verified ✓**
- 8,868 analyst reports, 18 LLMs: explicit analyst ratings raise herding to >94% for frontier models; arbitrary contradictory "fake" ratings are adopted ~30% of the time (GPT-5: 33.5%); susceptibility uncorrelated with scale.
- **Use:** mechanism-level support — contextual opinion pressure dominates independent judgment in finance and does not shrink with scale; this is the pressure that erodes mandates over the 200-day horizon. Also a clean example of the point-in-time category.

### C5. Agent-Based Simulation of a Financial Market with Large Language Models — recommended
- **Hashimoto, R., Takayanagi, T., Suzuki, M., Izumi, K.** — arXiv:2510.12189 (Oct 2025). U. Tokyo / Simulacra.
- **PDF:** `references/related_work_2026/2510_12189_ABM_Financial_Market_LLMs.pdf` · **Verified ✓**
- Hybrid FCN+LLM agents in a limit-order-book simulation over a *synthetic fundamental price*: 1–5 LLM agents among 1,000 reproduce the all-time-high anomaly within empirical range while preserving stylized facts; LLMs show disposition-effect behavior with shifting reference points (model-specific — absent in Qwen-2.5-7B).
- **Use:** methodological ally for synthetic-fundamental market design (and an ABIDES-adjacent path for the planned realism upgrade); inverse framing — their desired "realistic bias" is FinPersona's failure mode; independent evidence LLM trading is path-dependent rather than instruction-driven.

### C6. Agentic Trading: When LLM Agents Meet Financial Markets (survey) — recommended
- **Xia, Y., You, P., Wang, T., Liu, F., Qi, H., et al.** — arXiv:2605.19337 (May 2026). Shenzhen University.
- **PDF:** `references/related_work_2026/2605_19337_Agentic_Trading_Survey.pdf` · **Verified ✓**
- Audit-oriented evidence map of 77 studies (snapshot 2026-03): only 19 are closed-loop empirical; of those, 2 report time-consistent splits, 1 a transaction-cost model, 0 reach the top reproducibility tier. Explicitly warns agent rationales "are not guaranteed to be faithful to the true internal decision process."
- **Use:** survey-level positioning — the field's bottleneck is controlled, protocol-explicit closed-loop evaluation (which FinPersona provides), and its rationale-faithfulness warning independently supports the language–behavior dissociation.

---

## D. Memory mechanisms & persistent-state agents

### D1. Remember When It Matters: Proactive Memory Agent for Long-Horizon Agents — **must-cite (controller precedent)**
- **Wu, Y., Zhang, L., Zhou, Y., Wang, M., Peng, B., et al.** — arXiv:2607.08716 (Jul 2026). Meta AI.
- **PDF:** `references/related_work_2026/2607_08716_Proactive_Memory_Agent.pdf` · **Verified ✓**
- Defines **behavioral state decay**: state "may even remain within the model's context window, but no longer exerts reliable control over behavior." A memory agent decides *when* to inject reminders (silence is an explicit action): +8.3pp Terminal-Bench 2.0, +6.8pp τ²-Bench; selective injection beats always-on injection (64.3 vs 63.5 macro) and unnecessary injections can hurt; the policy is learnable (GRPO).
- **Use:** names the general failure mode MSD instantiates in finance, and independently establishes that *always-on re-injection is not optimal* — direct precedent for the planned adaptive re-grounding controller. Differentiate: their trigger is a learned policy; the revision plan proposes an interpretable internal drift-signal trigger (M2 direction).

### D2. Always-On Agents: A Survey of Persistent Memory, State, and Governance in LLM Agents — recommended
- **Ding, T., Nannapaneni, A., Liu, B., Zhang, L.** — arXiv:2606.30306 (Jun 2026). 435-work coded survey.
- **PDF:** `references/related_work_2026/2606_30306_Always_On_Agents_Survey.pdf` · **Verified ✓**
- Persistent-state framing: the literature over-studies accumulating/retrieving state (retrieve: 269 works) vs. governing it (rollback: 27/435); persistence creates "a failure class episodic evaluation is not built to see"; bigger contexts solve a reading problem, not a governance problem.
- **Use:** survey-level motivation that long-horizon, accumulated-state failures (like MSD) are systematically under-evaluated; positions FinPersona-Bench as the kind of always-on evaluation the survey calls for.

---

## E. Mechanistic interpretability (supports revision-plan M1–M4)

### E1. Tracing Persona Vectors Through LLM Pretraining — recommended
- **Moskvoretskii, V., Glandorf, D., Medina Moreira, J., Käser, T., West, R.** — arXiv:2605.13329 (May 2026, preprint). EPFL.
- **PDF:** `references/related_work_2026/2605_13329_Tracing_Persona_Vectors_Pretraining.pdf` · **Verified ✓**
- Difference-of-means persona directions form within 0.22% of pretraining tokens and transfer from early base checkpoints to fully post-trained models; post-training reshapes expression but never erases the direction; elicitation format shapes which facets a direction captures.
- **Use:** validates M2's methodology (trait directions are robust, transferable linear objects) and offers a framing hypothesis: MSD may be an *elicitation* failure (prompt loses grip) while the underlying direction persists — exactly what M2/M3 can test. Methodological detail: norm-rescaled steering coefficients for comparing interventions across contexts with different residual norms.

### E2. What Drives Representation Steering? A Mechanistic Case Study on Steering Refusal — **must-cite for M3/M4**
- **Cheng, S., Wiegreffe, S., Manocha, D.** — arXiv:2604.08524 (Apr 2026, preprint). UMD.
- **PDF:** `references/related_work_2026/2604_08524_What_Drives_Representation_Steering.pdf` · **Verified ✓**
- Multi-token activation patching for steered open-ended generation; refusal steering is localized (~10% of edges recover 85% faithfulness); DIM/learned/preference-optimized vectors use interchangeable circuits (≥90% overlap) despite low cosine similarity; **steering acts through the attention OV circuit, not QK** (freezing QK costs ~8.75%; ablating OV costs 71.75%).
- **Use:** methodological precedent for M3–M4 (causal attribution over multi-token rollouts). Important caveat for the revision plan: if MSD is attention-mass (QK) decay but the adherence direction operates via OV, M1 and M2/M3 probe partly *separable* mechanisms — worth stating explicitly in the mechanistic section design.

### E3. Locate, Steer, and Improve: A Practical Survey of Actionable Mechanistic Interpretability — recommended
- **Zhang, H., Zhang, Z., Wang, M., et al. (~30 authors)** — arXiv:2601.14004 (v4, Apr 2026). Living survey.
- **PDF:** `references/related_work_2026/2601_14004_Locate_Steer_Improve_Survey.pdf` · **Verified ✓**
- Taxonomy separating diagnostic localization (attention/magnitude analysis, patching, probing, logit lens, circuits) from causal intervention (amplitude manipulation, weight editing, vector arithmetic); mandates paired side-effect checks for interventions; notes causal localization doesn't scale beyond ~100B.
- **Use:** the single framing citation situating M1 (localize) → M2/M3 (steer) → M4 (attribute) as an instance of the survey's diagnose-then-intervene protocol; its side-effect evaluation requirement supports scoring M3 on both adherence restoration *and* collateral damage to trading competence.

### E4. Bridging Mechanistic Interpretability and Prompt Engineering with Gradient Ascent for Interpretable Persona Control — recommended
- **Saini, H., Tang, Y., Liu, D.** — arXiv:2601.02896; **published in TMLR (6/2026)**.
- **PDF:** `references/related_work_2026/2601_02896_Gradient_Ascent_Persona_Control.pdf` · **Verified ✓**
- Optimizes prompts against DIM/SAE persona directions; key caveat: dense steering-vector injection pushes activations off-manifold (SAE L0 explodes ~50→>150) while prompt-space steering stays on-manifold; steering away from a *myopic-reward* persona upweights long-horizon tokens ("Future", "Long", "Wait") in the logits.
- **Use:** design input for M3 (monitor SAE sparsity/perplexity when adding/ablating the mandate direction to avoid off-manifold artifacts); its myopic-reward result is the closest existing analogue to logit-level attribution of panic-selling vs. long-term discipline (M4 precedent).

---

## F. Deployment & governance motivation

### F1. Agent Security Meets Regulatory Reality: Autonomous-Agent Threats and Controls in Regulated Financial Systems — optional (motivation)
- **Guda Nagavenkata Srinivasa, K.M.** — arXiv 2606.29142 (2026). Single-author practitioner systematization; IEEE format. *(Caveat: contains leftover template artifacts; cite as practitioner evidence, not peer-reviewed research.)*
- **PDF:** `references/related_work_2026/2606_29142_Agent_Security_Regulatory_Reality.pdf` · **Verified ✓ (with quality caveat)**
- Maps agentic threats onto ECOA/Reg B, EU AI Act, GDPR Art. 22, FINRA 2026 guidance from a production KYC deployment. Most consequential observed failure: the agent silently operating on a superseded policy, caught only by audit — a production analog of mandate decay. FINRA 2026: firms remain responsible for agent decisions regardless of autonomy; SR 26-2 excludes generative/agentic AI from US model-risk scope.
- **Use:** introduction/ethics motivation — behavior–mandate divergence is a legally actionable failure class, and language-level compliance is insufficient (regulators require per-decision behavioral attributability).

---

## Suggested citation placement (mapping to current paper sections)

| Paper | Section of FinPersona paper | Role |
|---|---|---|
| Laban 2505.06120; Menon 2603.03258; Dongre 2510.07777; Ko 2606.30571 | §2 Behavioral Drift | motivation / nearest neighbor / contrast / support |
| Dongre 2605.12922 | §2 Behavioral Drift + §5 Future Work (M1) | mechanistic precedent — must differentiate |
| Tosato 2508.04826; Kocielnik 2606.12730; Song 2509.10078; Buakhaw 2510.13586 | §2 Persona Fragility + MBTI defense / dissociation discussion | support |
| Zhu 2605.28359; Fan 2512.10971; Qu 2606.29771; Hu 2605.09106; Hashimoto 2510.12189; Xia 2605.19337 | §2 Static Benchmarks & Subjective Simulations | contamination evidence / point-in-time contrast / closest finance neighbor / mechanism / methodology ally / survey positioning |
| Wu 2607.08716; Ding 2606.30306 | §2 Memory Mechanisms | selective-injection precedent / survey framing |
| Moskvoretskii 2605.13329; Cheng 2604.08524; Zhang 2601.14004; Saini 2601.02896 | new Mechanistic Analysis section (M1–M4) | methodology + caveats |
| Guda 2606.29142 | §1 Intro / Ethics | deployment motivation |

---

## BibTeX (verified against the PDFs)

```bibtex
@article{laban2025lost,
  title={{LLMs} Get Lost in Multi-Turn Conversation},
  author={Laban, Philippe and Hayashi, Hiroaki and Zhou, Yingbo and Neville, Jennifer},
  journal={ArXiv preprint}, volume={arXiv:2505.06120}, year={2025},
  url={https://arxiv.org/abs/2505.06120}}

@inproceedings{menon2026inherited,
  title={Inherited Goal Drift: Contextual Pressure Can Undermine Agentic Goals},
  author={Menon, Achyutha and Saebo, Magnus and Crosse, Tyler and Gibson, Spencer and Jang, Eyon and Cruz, Diogo},
  booktitle={Lifelong Agents Workshop @ ICLR 2026}, year={2026},
  url={https://arxiv.org/abs/2603.03258}}

@inproceedings{dongre2025drift,
  title={Drift No More? Context Equilibria in Multi-Turn {LLM} Interactions},
  author={Dongre, Vardhan and Rossi, Ryan A. and Lai, Viet Dac and Yoon, David Seunghyun and Hakkani-T{\"u}r, Dilek and Bui, Trung},
  booktitle={AAAI 2026 Workshop on Personalization in the Era of Large Foundation Models}, year={2026},
  url={https://arxiv.org/abs/2510.07777}}

@article{ko2026attractor,
  title={Attractor States Emerge in Multi-Turn {LLM} Conversations},
  author={Ko, Ting-Wen and Geiping, Jonas},
  journal={ArXiv preprint}, volume={arXiv:2606.30571}, year={2026},
  url={https://arxiv.org/abs/2606.30571}}

@article{dongre2026attention,
  title={When Attention Closes: How {LLMs} Lose the Thread in Multi-Turn Interaction},
  author={Dongre, Vardhan and Hsieh, Joseph and Lai, Viet Dac and Yoon, Seunghyun and Bui, Trung and Hakkani-T{\"u}r, Dilek},
  journal={ArXiv preprint}, volume={arXiv:2605.12922}, year={2026},
  url={https://arxiv.org/abs/2605.12922}}

@inproceedings{tosato2026persist,
  title={Persistent Instability in {LLM}'s Personality Measurements: Effects of Scale, Reasoning, and Conversation History},
  author={Tosato, Tommaso and Helbling, Saskia and Mantilla-Ramos, Yorguin-Jose and Hegazy, Mahmood and Tosato, Alberto and Lemay, David John and Rish, Irina and Dumas, Guillaume},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence (AI Alignment Track)}, year={2026},
  url={https://arxiv.org/abs/2508.04826}}

@article{kocielnik2026rethinking,
  title={Rethinking Psychometric Evaluation of {LLMs}: When and Why Self-Reports Predict Behavior},
  author={Kocielnik, Rafal and Han, Pengrui and Song, Peiyang and Marmarelis, Myrl G. and Debnath, Ramit and Mobbs, Dean and Anandkumar, Anima and Alvarez, R. Michael},
  journal={ArXiv preprint}, volume={arXiv:2606.12730}, year={2026},
  url={https://arxiv.org/abs/2606.12730}}

@article{song2026questionnaires,
  title={Human Psychometric Questionnaires Mischaracterize {LLM} Behavior},
  author={Song, Woojung and Choi, Dongmin and Park, Yoonah and Han, Jongwook and Lee, Eun-Ju and Jo, Yohan},
  journal={ArXiv preprint}, volume={arXiv:2509.10078}, year={2026},
  url={https://arxiv.org/abs/2509.10078}}

@article{buakhaw2025deflanderization,
  title={Deflanderization for Game Dialogue: Balancing Character Authenticity with Task Execution in {LLM}-based {NPCs}},
  author={Buakhaw, Pasin and Kerdthaisong, Kun and Phenhiran, Phuree and Khlaisamniang, Pitikorn and Vorathammathorn, Supasate and Ittichaiwong, Piyalitt and Yongsatianchot, Nutchanon},
  journal={ArXiv preprint}, volume={arXiv:2510.13586}, year={2025},
  url={https://arxiv.org/abs/2510.13586}}

@article{zhu2026knowing,
  title={From Knowing to Doing: A Memory-Controlled Benchmark for {LLM} Trading Agents on Stock Markets},
  author={Zhu, Taojie and Zhao, Wentao and Sun, Rui and Luan, Beidi and Lu, Jiacheng and Wang, Sinuo and Li, Jing and Jiang, Daxin and He, Yonghong and Bai, Zuo},
  journal={ArXiv preprint}, volume={arXiv:2605.28359}, year={2026},
  url={https://arxiv.org/abs/2605.28359}}

@article{fan2025aitrader,
  title={{AI-Trader}: Benchmarking Autonomous Agents in Real-Time Financial Markets},
  author={Fan, Tianyu and Yang, Yuhao and Jiang, Yangqin and Zhang, Yifei and Chen, Yuxuan and Huang, Chao},
  journal={ArXiv preprint}, volume={arXiv:2512.10971}, year={2025},
  url={https://arxiv.org/abs/2512.10971}}

@article{qu2026clqt,
  title={{CLQT}: A Closed-Loop, Cost-Aware, Strategy-Consistent Benchmark for Diagnostic Evaluation of {LLM} Portfolio-Management Agents},
  author={Qu, Bo and Chen, Mingguang},
  journal={ArXiv preprint}, volume={arXiv:2606.29771}, year={2026},
  url={https://arxiv.org/abs/2606.29771}}

@article{hu2026finbias,
  title={{Fin-Bias}: Comprehensive Evaluation for {LLM} Decision-Making under Human Bias in Finance Domain},
  author={Hu, Xiaoyu and Zhao, Jinman},
  journal={ArXiv preprint}, volume={arXiv:2605.09106}, year={2026},
  url={https://arxiv.org/abs/2605.09106}}

@article{hashimoto2025abm,
  title={Agent-Based Simulation of a Financial Market with Large Language Models},
  author={Hashimoto, Ryuji and Takayanagi, Takehiro and Suzuki, Masahiro and Izumi, Kiyoshi},
  journal={ArXiv preprint}, volume={arXiv:2510.12189}, year={2025},
  url={https://arxiv.org/abs/2510.12189}}

@article{xia2026agentic,
  title={Agentic Trading: When {LLM} Agents Meet Financial Markets},
  author={Xia, Yihan and You, Panpan and Wang, Taotao and Liu, Fang and Qi, Han and Wu, Xiaoxiao and Zhang, Shengli},
  journal={ArXiv preprint}, volume={arXiv:2605.19337}, year={2026},
  url={https://arxiv.org/abs/2605.19337}}

@article{wu2026remember,
  title={Remember When It Matters: Proactive Memory Agent for Long-Horizon Agents},
  author={Wu, Yifan and Zhang, Lizhu and Zhou, Yuhang and Wang, Mingyi and Peng, Bo and Li, Serena and Fan, Xiangjun and Zhao, Zhuokai},
  journal={ArXiv preprint}, volume={arXiv:2607.08716}, year={2026},
  url={https://arxiv.org/abs/2607.08716}}

@article{ding2026alwayson,
  title={Always-On Agents: A Survey of Persistent Memory, State, and Governance in {LLM} Agents},
  author={Ding, Tianyu and Nannapaneni, Aditya and Liu, Bingfan and Zhang, Ling},
  journal={ArXiv preprint}, volume={arXiv:2606.30306}, year={2026},
  url={https://arxiv.org/abs/2606.30306}}

@article{moskvoretskii2026tracing,
  title={Tracing Persona Vectors Through {LLM} Pretraining},
  author={Moskvoretskii, Viktor and Glandorf, Dominik and Medina Moreira, Jorge and K{\"a}ser, Tanja and West, Robert},
  journal={ArXiv preprint}, volume={arXiv:2605.13329}, year={2026},
  url={https://arxiv.org/abs/2605.13329}}

@article{cheng2026steering,
  title={What Drives Representation Steering? A Mechanistic Case Study on Steering Refusal},
  author={Cheng, Stephen and Wiegreffe, Sarah and Manocha, Dinesh},
  journal={ArXiv preprint}, volume={arXiv:2604.08524}, year={2026},
  url={https://arxiv.org/abs/2604.08524}}

@article{zhang2026locate,
  title={Locate, Steer, and Improve: A Practical Survey of Actionable Mechanistic Interpretability in Large Language Models},
  author={Zhang, Hengyuan and Zhang, Zhihao and Wang, Mingyang and Su, Zunhai and Wang, Yiwei and others},
  journal={ArXiv preprint}, volume={arXiv:2601.14004}, year={2026},
  url={https://arxiv.org/abs/2601.14004}}

@article{saini2026bridging,
  title={Bridging Mechanistic Interpretability and Prompt Engineering with Gradient Ascent for Interpretable Persona Control},
  author={Saini, Harshvardhan and Tang, Yiming and Liu, Dianbo},
  journal={Transactions on Machine Learning Research}, year={2026},
  url={https://arxiv.org/abs/2601.02896}}

@article{guda2026agentsecurity,
  title={Agent Security Meets Regulatory Reality: A Practitioner Systematization of Autonomous-Agent Threats and Controls in Regulated Financial Systems},
  author={Guda Nagavenkata Srinivasa, Krishna Mohan},
  journal={ArXiv preprint}, volume={arXiv:2606.29142}, year={2026},
  url={https://arxiv.org/abs/2606.29142}}
```

---

## Method & coverage notes

- **Search coverage:** nine themed sweeps (long-horizon drift; persona stability; trading benchmarks; system-prompt adherence/memory; mech-interp of persona/instructions; multi-agent market simulation; psychometric validity; finance safety/governance; role-play consistency; behavioral biases; long-term memory benchmarks), August 2026.
- **Verification:** all 22 PDFs downloaded from arXiv into `references/related_work_2026/`, full text extracted, and each paper read (title/author/venue block checked directly against the PDF; summaries grounded in the papers' own reported numbers). Two quality flags noted inline (B4 challenge report; F1 practitioner paper with template artifacts).
- **Candidates surfaced but deliberately not included** (adjacent, lower priority — retrievable if needed): PortBench (2605.27887, overlaps CLQT), FinTradeBench (2603.19225), When Agents Trade (2510.11695, overlaps AI-Trader), FinSafetyBench (2605.00706), TRIDENT (2507.21134), MemoryArena/MemoryAgentBench-class memory benchmarks, Agent Drift follow-ons already covered by cited Rath 2026.
