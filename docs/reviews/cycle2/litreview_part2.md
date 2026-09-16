# FinPersona-Bench — Cycle 2 independent prior-art assessment, Part 2 (14-paper share)

Reviewer: Cycle 2 literature reviewer (independent). Date: 2026-08-22.
Method: every PDF in the share was extracted with PyMuPDF (fitz) and read in full, page by page (page counts below). The paper under review (COLM_FinPersona_Bench_Current_Paper, 29 pp incl. App. A–L) was read first (abstract, contributions, §3, §4, all appendices). Per-paper assessments were written BEFORE opening the Cycle 1 report; the Cycle 1 agreement/disagreement list is the last section.

Coverage (all read in full): 2603_03258 (22 pp) · 2604_08524 (26 pp) · 2605_09106 (17 pp) · 2605_12922 (34 pp, incl. App. D.5 and App. H) · 2605_13329 (44 pp) · 2605_19337 (59 pp) · 2605_28359 (20 pp) · 2606_12730 (53 pp) · 2606_29142 (11 pp) · 2606_29771 (56 pp, incl. §3.5 and §8.8) · 2606_30306 (136 pp) · 2606_30571 (40 pp) · 2607_08716 (12 pp) · Jiang–Peng–Yan JFE 2024 (19 pp incl. LSE cover). Total 549 pages.

Two claims tested throughout:
- ORIGINAL = FinPersona's claims as written (MSD formalisation; behaviour-vs-reasoning distinction; decoupled synthetic ground truth; three failure-mode regimes; MAS/CI/RG; model-dependence; 4.4x compounding; "re-grounding not universally beneficial"; placebo control; Big Five/O3 ablation; injection-frequency ablation; T-calibration; LCR rationale analysis; MBTI-as-vocabulary; selective re-grounding prescription; transfer to other domains).
- REFRAMED = "In a fixed synthetic market with stateless single-turn agents, appending an imperative behavioural directive at the recency position shifts trading behaviour toward cash/inaction in a content-modulated way (protective >> growth >> neutral), while a length-matched declarative placebo produces no shift; scored against opposed allocation targets this yields a 17/18 vs 16/18 split."

Verdict vocabulary: ANTICIPATES / PARTIALLY ANTICIPATES / CONTRADICTS / SUPPORTS / IRRELEVANT.

---

## 1. Menon, Saebo, Crosse, Gibson, Jang, Cruz — "Inherited Goal Drift: Contextual Pressure Can Undermine Agentic Goals" (arXiv 2603.03258; Lifelong Agents @ ICLR 2026 workshop; 22 pp)

(a) Citation/venue: workshop paper, ICLR 2026 Lifelong Agents workshop; code github.com/achyutha11/inherited-drift.

(b) What it does: re-runs Arike et al. (2025)'s stock-trading goal-drift environment (system-prompt goal = profit-max or emissions-min; adversarial pressure delivered as news/stakeholder messages in user turns; 30-step simulations, 10 seeds) on 8 model configurations (GPT-4o-mini, GPT-5-mini, GPT-5.1, Qwen3-235B, Gemini-2.5-Flash std/thinking, Claude Sonnet 4.5 std/thinking); adds "context conditioning" (a newer model takes over a pre-filled drifting GPT-4o-mini trajectory), goal-switching (16/32-step instrumental phase), goal reversal, prompt-strength and direct instruction-hierarchy tests; and an ER-triage environment (45 steps, 5 seeds). Metric: state-based drift GD_t (Eq. 1, p. 3).

(c) Findings relevant to FinPersona:
- p. 5: "All tested models other than GPT-4o-mini show zero drift over 30 steps, barring minor fluctuations (Figure 2a)" — modern frontier agents do not drift from a system-prompt financial goal under sustained adversarial user-turn pressure in a genuinely accumulating 30-step context.
- p. 5: drift is inherited when conditioned on a weaker model's drifting trajectory; "GPT-5.1 and GPT-5-mini are the only models that show consistently strong adherence to the system goal."
- pp. 6–7 (§4.2 Prompt strength): a more explicit system prompt reduces drift for some models (strongest for GPT-5-mini): "for some models, incomplete alignment or drift may be a result of prompt ambiguity."
- p. 7 (Direct instruction-hierarchy test): with a user message instructing the opposite goal, "the Gemini-2.5-Flash family and Claude-Sonnet-4.5 (standard) show extremely poor system-goal adherence, instead consistently opting to follow the user-specified environmental goal"; GPT-5-mini/5.1 follow the system goal 100%; "limited correlation between instruction hierarchy and resistance to drift."
- p. 13 (App. A): "context length may influence drift, with higher drift scores for most models in the 32-step basic and conditioning simulations ... compared to their 16-step counterparts."
- §4.3 pp. 8–9: ER-triage environment; "the impact of context conditioning is highly environment-dependent."
- p. 9 (§5.1): "Validate via long-horizon simulation"; "Develop explicit system prompts."

(d) ORIGINAL: ANTICIPATES "transfer to medical triage" (FinPersona's future work — Menon already runs an ER-triage environment, §4.3). PARTIALLY ANTICIPATES model-dependence of drift (per-family heterogeneity). CONTRADICTS in spirit the premise that mandates erode for frontier models as context accumulates: frontier models hold a system-prompt goal at zero drift for 30 steps under active adversarial pressure; drift needs conditioning on a drifting trajectory. (FinPersona's static arm has no accumulating context, so the designs do not meet head-on; but Menon is the closest prior test of "mandate in system prompt, pressure in user turns, finance domain", and it found resilience.) SUPPORTS that prompt wording matters. IRRELEVANT to synthetic ground truth, MAS/CI/RG, placebo, 4.4x.

(e) REFRAMED: bears on it mechanistically. The instruction-hierarchy test shows several models (Gemini 2.5 Flash, Claude Sonnet 4.5 std) follow a user-turn goal over the system-prompt goal, while the GPT-5 family follows the system prompt. That predicts (i) a directive appended to the user message will dominate behaviour for some models and (ii) model-dependence — consistent with FinPersona's 17/18 vs 16/18 pattern with exceptions. Menon neither varies directive content nor measures cash/inaction; it does not own the claim.

(f) Cite: YES (must). Differentiation: "Menon et al. show that frontier agents hold a system-prompt trading goal for 30 steps under adversarial user-turn pressure and drift mainly when conditioned on a weaker model's trajectory, and that user-turn instructions override system goals for some families; we hold context fixed and vary only the content of a directive appended in the user turn, showing the direction of its effect is set by content."

(g) Cycle 1 check: Cycle 1 lists Menon under C19 (ER triage already executed) and under "three papers refute the mechanism". Agree on both. Cycle 1 does not use Menon's instruction-hierarchy result, which is the most useful prior for the reframed user-turn-directive mechanism and its model-dependence — a miss, not an error.

---

## 2. Cheng, Wiegreffe, Manocha — "What Drives Representation Steering? A Mechanistic Case Study on Steering Refusal" (arXiv 2604.08524; UMD; 26 pp)

(a) Citation/venue: arXiv preprint, 9 Apr 2026.

(b) What it does: mechanistic study of refusal steering vectors (DIM, NTP, PO) in Gemma-2-2B and Llama-3.2-3B. Extends edge-attribution patching (EAP-IG) to multi-token steered generation; ~10–11% of edges recover 85% faithfulness (§4.3 p. 5); circuits interchangeable across methods (§5.2 p. 6); steering acts mainly through the OV circuit — freezing all QK attention scores costs only 8.75% (Table 1 p. 7, §6.3); steering-value-vector decomposition; 90–99% sparsification (§7 p. 8). Only refusal is studied (Limitations p. 9: "it is possible some of our findings are unique to the refusal concept").

(c) Relevance: none to FinPersona's empirical claims — no prompting, personas, multi-turn or finance. Touches only FinPersona's future-work sentence on a mechanistic account (and Cycle 1's M1–M4): offers reusable tooling, no finding about prompt-borne instructions.

(d) ORIGINAL: IRRELEVANT to all claims. (e) REFRAMED: IRRELEVANT. (f) Cite: optional, future-work tooling only. (g) Cycle 1: not used; nothing to correct.

---

## 3. Hu & Zhao — "Fin-Bias: Comprehensive Evaluation for LLM Decision-Making under Human Bias in Finance Domain" (arXiv 2605.09106; Rutgers/Toronto; 17 pp)

(a) Citation/venue: arXiv preprint, 9 May 2026.

(b) What it does: single-shot benchmark of 8,868 analyst reports (~4k tokens), three variants (original rating in first sentence / rating removed / fake rating), 18 LLMs (GPT-5, GPT-4, Claude-3.5-Haiku, Claude-4-Sonnet + 14 open models); Herding Score (Eq. 1 p. 5) and accuracy vs return-based ground truth (60-day CAR quantiles, App. A.1); MPQA lexicon filtering; DPO.

(c) Findings: herding score rises 5–10 pp when the analyst rating is visible (Table 4 p. 6); fake ratings are herded ~30% on average (10–60%), "not strongly correlated with model size" (Table 5 p. 7); with ratings present all models ≈ 33% accuracy = analyst (Table 6 p. 8); removing opinionated sentences gives +2–4 pp (Table 7 p. 9). Limitations p. 9: single-agent, finance only.

(d) ORIGINAL: PARTIALLY ANTICIPATES the generic phenomenon "an explicit in-context cue changes an LLM's financial decision in a content-specific way, even in frontier models" — but single-shot; no persona, re-injection, drift, or synthetic ground truth (ground truth = realised returns). IRRELEVANT to MSD, MAS/CI/RG, 4.4x, placebo, Big Five, frequency ablation.

(e) REFRAMED: weakly related — a one-sentence opinion at the START of a long document shifts the decision toward its content; FinPersona's directive sits at the END (recency). Supports plausibility of content-driven direction; not a competitor.

(f) Cite: yes (context-following in financial decisions). Differentiation: "Fin-Bias shows single-shot herding toward an explicit in-context analyst opinion; we study a repeated imperative directive scored against an objective allocation target over 200 decisions."

(g) Cycle 1: not referenced; nothing to correct.

---

## 4. Dongre, Hsieh, Lai, Yoon, Bui, Hakkani-Tür — "When Attention Closes: How LLMs Lose the Thread in Multi-Turn Interaction" (arXiv 2605.12922; UIUC/Adobe; 34 pp) — App. D.5 and App. H read carefully

(a) Citation/venue: arXiv preprint, 13 May 2026.

(b) What it does: four open-weight architectures (Mistral-7B, LLaMA-3.1-8B, Qwen-2.5-7B, Mixtral-8x7B) + six more in a trend battery; four 50-turn tasks (5-fact retention, 20-fact controlled complexity, persona compliance with five stylistic rules under passive/naturalistic/adversarial user scripts, policy compliance); 5,483 episodes; temperature 0.7. Instruments: Goal Accessibility Ratio GAR (attention mass from response tokens to system-prompt goal tokens, Def. 2.5 p. 4); sliding-window mask W=4096 that forces attention-channel closure at τ_cross = 23/19/20/20; linear residual probes (LDA/PCA-50).

(c) Findings:
- pp. 7–8: GAR declines monotonically under default attention for all 10 architectures (Mann–Kendall p<1e-7), by 27–48% of turn-1 value, "but remains well above the closed-channel floor"; default-condition fact recall stays 100% through 50 turns (Fig. 5 p. 8); behavioural failure appears only under forced closure. Persona violations under default passive are already 0.35 (Mistral) to 0.52 (LLaMA) (Table 3 p. 22); under closure they converge to 47–58%.
- App. D.5 p. 18 (activation patching at the peak-AUC layer): 2×2 design on Mistral-7B, L27 vs L20–30, sampled vs greedy, n=30 fact-matched success/failure pairs, fact-recall task at T=40 under SW=4096: "No cell shows a statistically detectable fact-specific causal effect: all permutation p > 0.05, all 95% bootstrap confidence intervals include zero"; true-patch and random-patch flips move "in lock-step"; "The probing finding is therefore descriptive localization of where goal-relevant information persists during failure, not causal identification"; non-linear/distributed read-outs remain open (pp. 10, 18).
- App. H pp. 28 & 30 ("Negative result: periodic user-role goal re-injection"): every K user turns, the verbatim system-prompt goal block was PREPENDED to the user message, under SW=4096 on Mistral-7B; three contents — the exact goal block, "an irrelevant block matched in length and entity types but unrelated to the recall facts", and a no-injection SW control; recall at lagged probes δ∈{+4..+9}; GAR_recent measured. Result (qualitative; no table): "A naive user-role periodic re-injection of the original goal block did not restore attention to the recent reminder span or improve lagged recall under SW=4096, suggesting that late textual access alone is insufficient under this intervention format." Conclusion p. 10: "repeating or retaining text is not equivalent to preserving goal information."
- Limitations p. 10: 50 turns, fixed goals, causal anchor for SW only on Mistral/Mixtral.

(d) ORIGINAL: PARTIALLY ANTICIPATES the MSD concept (system-prompt goal tokens become less accessible through attention as context grows — GAR is a salience measure). ANTICIPATES, as prior design, a three-arm re-injection test with a length-matched irrelevant control (App. H). CONTRADICTS in two respects: (i) under default attention within 50 turns, declining accessibility produced no behavioural failure at all (recall 100%); (ii) naive periodic goal re-injection did NOT help. Its persona task shows high violation rates from turn 1 rather than progressive decay. SUPPORTS architecture-dependence of post-closure survival (App. G.1).

(e) REFRAMED: a caution, not a competitor. Differences: prepended vs appended at recency; fact recall vs allocation behaviour; artificial sliding-window closure; 7B open weights; no content variation; null for both arms. FinPersona's positive, content-signed effect is not contradicted but must be explicitly distinguished (position, task, models, attention regime).

(f) Cite: YES (must; body and App. H). Differentiation: "Dongre et al. track attention to system-prompt goal tokens over 50 turns in open-weight models and find that naive periodic re-injection prepended to the user turn does not restore recall under forced attention closure; our agents are stateless, the directive is appended at the recency position, and the outcome is an allocation, so our content-signed effect is not a rerun of their null."

(g) Cycle 1 check: (i) "well-powered null in When Attention Closes Appendix D.5" — the null and the lock-step observation are correctly described, but "well-powered" overstates: n=30 pairs, one model, one task, one layer block; the authors write the effect is not "detectable at n = 30" and leave non-linear read-outs open. It is evidence that M3 is risky, not that it is settled. (ii) "App. H identical 3-arm design" (C11) — it IS a 3-arm design with a length-and-entity-matched irrelevant block, so a prior placebo-style arm exists; but "identical" overstates: prepended vs appended, recall vs behaviour, forced SW mask, qualitative report only, null for both arms. Correct wording: "analogous prior 3-arm design (goal / matched-irrelevant / none), reported qualitatively and null."

---

## 5. Moskvoretskii, Glandorf, Medina Moreira, Käser, West — "Tracing Persona Vectors Through LLM Pretraining" (arXiv 2605.13329; EPFL; 44 pp)

(a) Citation/venue: arXiv preprint, 13 May 2026.

(b) What it does: difference-of-means persona vectors (evil, sycophantic, impolite, humorous) extracted at 17 OLMo-3-7B pretraining checkpoints (+15 Apertus-8B); steering at layers 16/20; GPT-4.1-mini judge; random/label-shuffled matched-magnitude controls (App. E p. 26). Findings: vectors form within 0.22% of pretraining (§3 p. 5); early vectors still steer post-trained Instruct models (§4 p. 6); DPO concentrates suppression; geometry refines (cos sim from ≈0.3 upward, Fig. 4 p. 7); facets shift (§5.2 p. 8); different elicitation discourse types yield different directions (cos<0.5) that all steer (§6 p. 9, Table 1).

(c) Relevance: none direct — no prompted personas, multi-turn, finance or drift. Tangential support for "MBTI-as-vocabulary" (persona vocabulary activates pretraining-formed directions); a template for future mechanistic work; App. E is a principled matched-magnitude control design in activation space.

(d) ORIGINAL: IRRELEVANT (mild SUPPORT for the vocabulary framing). (e) REFRAMED: IRRELEVANT. (f) Cite: optional (future work). (g) Cycle 1: not used; nothing to correct.

---

## 6. Xia, You, Wang, Liu, Qi, Wu, Zhang — "Agentic Trading: When LLM Agents Meet Financial Markets" (arXiv 2605.19337; Shenzhen Univ.; ESWA-style survey; 59 pp)

(a) Citation/venue: arXiv survey, 19 May 2026.

(b) What it does: audit-oriented evidence map of 77 studies (primary subset n=19 meeting Action Output + Closed-Loop Evaluation). 2/19 report time-consistent splits, 1/19 a cost model, 1/19 universe/survivorship handling, 11/19 execution semantics, 15/19 at reproducibility R0, 0 at R3 (abstract; App. B Table B.23 p. 45). Architecture–Capability–Adaptation lens; memory as "an evaluation knob" and "Context Length vs. Distraction ... Lost-in-the-Middle" (§4.4 p. 12); minimum-reporting checklist MR-1..MR-7 (§13 p. 38); "Negative Results and Failed Designs" (§13.3 p. 41).

(c) Relevance: background only — no discussion of persona/personality, mandate adherence, behavioural drift, re-injection or synthetic hidden-value markets; FinMem/TradingGPT appear only as memory works.

(d) ORIGINAL: IRRELEVANT to specific claims; SUPPORTS the motivation that trading-agent evaluation is returns/protocol-centred. MR-4 (execution & costs) could be turned against FinPersona's frictionless W_t. (e) REFRAMED: IRRELEVANT. (f) Cite: yes, positioning; differentiation: "Xia et al. show closed-loop trading benchmarks score returns under weak protocol reporting; we score mandate adherence against a generating function but inherit the obligation to report execution assumptions (none are modelled)." (g) Cycle 1: listed under financial benchmarks; nothing to correct.

---

## 7. Zhu, Zhao, Sun, Luan, Lu, Wang, Li, Jiang, He, Bai — "From Knowing to Doing (KTD-Fin): A Memory-Controlled Benchmark for LLM Trading Agents on Stock Markets" (arXiv 2605.28359; Tsinghua/Stepfun; 20 pp)

(a) Citation/venue: arXiv preprint, 27 May 2026.

(b) What it does: Qlib-based CSI300 daily trading, 2024-01-01 → 2026-04-10 (548 days); four-level data-side masking (bright/stock-blind/date-blind/blinded); three decision modes; ten-attacker de-anonymisation probe (top-1 ticker ≤3.0%, joint ≤1.5%); Barra-style attribution; 10 frontier LLMs vs 18 Qlib baselines; temperature 0.0.

(c) Findings: masking flips rationales from brand narratives to factor ranks (§5.1, App. A); under memory-only + blinded the anchor model holds cash (0.00%, Table 3 p. 6; "declines to trade in all 25 of 25 cells when those tickers are anonymized", p. 2); "prompt-level restriction alone does not reproduce the ablation — data-side masking does work that no in-prompt instruction has been shown to replicate" (p. 7); 9/10 agents negative selection alpha (Table 5 p. 8).

(d) ORIGINAL: SUPPORTS the rationale for a synthetic market (memorisation is real; in-prompt instructions cannot suppress it) by a different route. IRRELEVANT to MSD, persona, placebo, re-grounding. (e) REFRAMED: background — LLM trading agents default to no-trade/cash absent informational handles (a baseline disposition toward inaction), and in-prompt instructions are weak levers on some behaviours. (f) Cite: yes. Differentiation: "KTD-Fin controls memorisation by masking real identifiers and scores alpha; we control ground truth with a synthetic V_t and score mandate adherence." (g) Cycle 1: listed; nothing to correct.

---

## 8. Kocielnik, Han, Song, Marmarelis, Debnath, Mobbs, Anandkumar, Alvarez — "Rethinking Psychometric Evaluation of LLMs: When and Why Self-Reports Predict Behavior" (arXiv 2606.12730; Caltech/UIUC/Cambridge; 53 pp)

(a) Citation/venue: arXiv preprint, 10 Jun 2026.

(b) What it does: 2×2×2 design — instrument (TPB vs Big Five), session (same vs separate), induction (parameter grid: 3 system prompts × 3 temperatures × 3 seeds vs 30 PersonaHub personas) — on four behavioural tasks (Columbia Card Task risk-taking, Asch-style sycophancy, confidence-calibration honesty, IAT) and 11 LLMs (Claude 3.7 Sonnet, Claude Haiku 4.5, GPT-4o mini, Gemini 2.5 Flash, LLaMA 3.3 70B, LLaMA 4 Maverick, Qwen2.5 72B, Qwen3 235B, DeepSeek V3.1, Phi-4, Mistral Large); ≈103k API calls.

(c) Findings:
- RQ1–2 (pp. 4–6): within-session TPB–behaviour r=+0.40 (excl. IAT); Big Five ≈0 ("Big 5 fails to detect coherence at all", p. 6); Big Five scales are internally reliable yet non-predictive (App. F Table 4 p. 21).
- RQ3 (p. 7): cross-session coherence collapses for sycophancy (+0.47 → −0.07) but survives for IAT/honesty; behaviour, not self-report, decorrelates.
- RQ4 (p. 8): persona prompting stabilises self-reports but "does not bring behavior into alignment" (abstract); "persona-customised deployments may produce confidently distinct self-reports without correspondingly distinct behavior."
- App. I.9 pp. 37–41: "Big Five also primes behavior, despite no policy" — the mere presence of any self-report shifts behaviour (CCT 13.2 cards within-session vs 8.9 between, Fig. 22); policy framing shifts risk-taking in a content-modulated way (loss-averse 8.1 vs gain-seeking 18.9 cards, Fig. 21 p. 41); "any in-context self-report perturbs subsequent behavior, not only ones explicitly framing a target policy" (p. 39).
- Limitations (pp. 15–16): single-turn structure.

(d) ORIGINAL: SUPPORTS "MBTI-as-vocabulary, not validated instrument" and simultaneously UNDERCUTS FinPersona's use of Big Five personas as "validation" (App. G): Big Five traits do not predict within-model behaviour, so OCEAN is a second vocabulary, not construct validation. PARTIALLY ANTICIPATES the language-vs-behaviour dissociation FinPersona reports (P(intended persona) at ceiling while behaviour does not follow; Qwen): persona induction changes what models say, not what they do. PARTIALLY ANTICIPATES model-dependence (Claude Haiku 4.5 coherent; Claude 3.7 Sonnet inverted).

(e) REFRAMED: the closest prior in this share. In-context policy text shifts risk-taking in a content-modulated direction within a session — structurally the reframed claim minus trading, the appended imperative form, the 200-step repetition and the length-matched placebo. It also shows that task-agnostic, non-directive text (Big Five items) shifts risk behaviour — a caution against asserting that a placebo "produces no shift" (FinPersona's placebo did shift MAS significantly vs static, p=0.041, uniformly worse). Does not own the claim; must be cited as nearest behavioural analogue.

(f) Cite: YES (must). Differentiation: "Kocielnik et al. show persona prompts move self-reports but not behaviour in single-shot tasks, while in-context policy framing does move risk-taking; we measure behaviour over 200 decisions and find that a behavioural directive, unlike declarative boilerplate, moves allocations — in a direction set by directive content."

(g) Cycle 1 check: cited under C2, C12, C17 and "persona framing actively contradicted" — agree. Cycle 1 did not use App. I.9 (any in-context self-report shifts behaviour; content-modulated priming of risk-taking), the part most relevant to the placebo interpretation and the reframed claim.

---

## 9. Guda Nagavenkata Srinivasa — "Agent Security Meets Regulatory Reality: A Practitioner Systematization of Autonomous-Agent Threats and Controls in Regulated Financial Systems" (arXiv 2606.29142; IEEE-member preprint; 11 pp)

(a) Citation/venue: single-author practitioner preprint (VectorTech Consulting).

(b) What it does: maps six agentic threat categories onto ECOA/Reg B, EU AI Act Arts 12/14/26, GDPR Art 22, FINRA 2026 agent guidance; four production KYC patterns; ~4 in 5 cases same-day; three negative results (stale policy in the RAG store → systematic over-verification §V-A; MCP tools not designed for audit; ~1 in 9 applicants unservable).

(c) Relevance: no LLM-behaviour experiments, persona, trading or drift; motivational only (FINRA 2026 "guardrails to constrain or restrict AI agent behaviors"; ECOA traceability). "Stale policy" is document-version drift, not persona drift.

(d) ORIGINAL: IRRELEVANT. (e) REFRAMED: IRRELEVANT. (f) Cite: optional, intro. (g) Cycle 1: not used; nothing to correct.

---

## 10. Qu & Chen — "CLQT: A Closed-Loop, Cost-Aware, Strategy-Consistent Benchmark for Diagnostic Evaluation of LLM Portfolio-Management Agents" (arXiv 2606.29771v2, 2 Aug 2026; 56 pp) — §3.5 and §8.8 read carefully

(a) Citation/venue: arXiv v2; independent researchers.

(b) What it does: closed-loop portfolio benchmark with TimeGate point-in-time enforcement, four cost models, three-tier memory (decay 0.95/0.98; consolidation every 12 rounds), 19 MCP tools, hash-chained DecisionRound audit trail; structured six-agent committee vs single autonomous orchestrator; S&P-100-derived universe; 26 bi-weekly rounds 2025-06-16 → 2026-06-12; 5 models (qwen3-235b, gemini-2.5-flash-lite, deepseek-chat-v3.1, gpt-5-mini, claude-haiku-4.5) × 2 modes × 5 seeds; 13-configuration ablation grid; live paper-trading track (18 days, 6 newer models). Five-axis scorecard: Coherence (0.5 signal–action agreement + 0.5 held-out judge), Acuity, Composure, Discipline ("systematic alignment to a standing mandate vs. turn-by-turn instruction-following — does the agent self-regulate to a policy even absent a hard guardrail?", pp. 19–20), Reliability.

(c) Verified items and findings:
- §3.5 p. 12: "CLQT computes a ConsistencyScore C_t after each round: C_t = 0.25·(1−d_style) + 0.25·τ_consist + 0.25·s_adhere + 0.25·a_target capturing style drift, turnover consistency, signal adherence, and mandate alignment. When C_t < 0.7 a drift warning is injected with a per-asset delta cap |δ_i| ≤ δ̄/2." Figure 4 p. 13: "STRATEGY DRIFT WARNING ... sub-threshold rounds inject |δ_i| ≤ δ̄/2". CONFIRMED: CLQT ships an event-triggered (C_t<0.7) drift-warning/re-grounding coupled to a hard cap. Its effect is never separately ablated; a_target is named but not defined (Table 9 p. 33: "investment-target + constraints (not ablated alone)").
- §8.8 p. 48: "Generalization of the profile. Varying the standing mandate and the reasoning-effort budget tests whether a model's capability fingerprint is a stable property or an artifact of the single mandate and effort level used here." CONFIRMED: mandate variation is future work; one mandate (long-only, leverage ≤1, ≥2% cash) is used.
- Headline: capability leader ≠ Sharpe leader (Table 5 p. 24); coherence gap: agreement exceeds held-out judge coherence by +0.30 backtest / +0.23 live — "agents trade in the right direction while their allocations fail to follow their own stated analysis" (abstract; §7.10 pp. 37–39; Fig. 12 p. 38); inter-axis mean |r| = 0.23 (App. F.2 p. 54); all module/cluster ablations within a ±0.42 Sharpe noise band (Tables 6–7 pp. 29–31); bare-workflow agent matches the full agent on returns; "Style-drift is ≈0 cohort-wide" (p. 19); autonomous-mode holds for gemini-3.5-flash (9/18) and minimax-m3 (8/18) came from tool-turn exhaustion and schema failure and vanished after a scaffold fix (§7.11 pp. 40–42); ACT* declarative/procedural reading of the stating-vs-doing gap (§2.4, §8.2).

(d) ORIGINAL: PARTIALLY ANTICIPATES "behaviour distinct from reasoning": the Coherence gap is a formalised, held-out-judged, live-replicated instance of agents saying one thing and allocating another — the phenomenon FinPersona reports as language-vs-behaviour dissociation. PARTIALLY ANTICIPATES MAS/CI: Discipline (mandate self-regulation) and Composure (turnover vs volatility) are conceptual cousins measured on real data. ANTICIPATES the selective/event-triggered re-grounding prescription (C_t<0.7 trigger), which FinPersona's Limitations call untested. SUPPORTS "memory not universally beneficial" on returns (no-memory +0.52 Sharpe, within noise). CONTRADICTS (mildly) an expectation of drift: style drift ≈ 0 over 26 rounds. Does not vary mandate content, no placebo, no compounding analysis.

(e) REFRAMED: does not own it (single mandate). Two bearings: (i) "hold/inaction" can be a reliability artefact (schema failure, tool-turn exhaustion), so FinPersona should report parse-failure/refusal/always-HOLD rates before attributing a shift toward cash to directive content; (ii) Discipline is the nearest existing measure of mandate adherence without guardrails.

(f) Cite: YES (must). Differentiation: "CLQT diagnoses a stating-vs-doing coherence gap under one fixed mandate, ships a threshold-triggered drift warning, and names mandate variation as future work; we vary the mandate itself and show that the sign of a re-injected directive's effect depends on its content."

(g) Cycle 1 check: all Cycle 1 statements about CLQT (§3.5 trigger; a_target undefined; investment-target module not ablated alone; §8.8 mandate variation as future work; coherence gap +0.30/+0.23; mean |r| = 0.23) are CORRECT as read. Cycle 1 omits CLQT's style-drift ≈ 0 finding and the reliability-driven hold mechanism; both are useful against FinPersona.

---

## 11. Ding, Nannapaneni, Liu, Zhang — "Always-On Agents: A Survey of Persistent Memory, State, and Governance in LLM Agents" (arXiv 2606.30306; 136 pp)

(a) Citation/venue: arXiv survey, 29 Jun 2026.

(b) What it does: defines always-on agents as persistent-state systems; six state axes; ten-stage lifecycle; 435-work coded corpus (retrieve 269, write 200, rollback 27, authority 72); Always-On Evaluation Protocol AOEP-v0 with a pilot (Table 18 p. 85).

(c) Findings relevant to FinPersona:
- §2.1 p. 16: "an agent that runs continuously but resets all state between requests is episodic, not always-on" — FinPersona's agents (stateless single-turn calls; only the portfolio tuple crosses steps) are episodic by this definition, which makes the "context accumulates" framing untenable for the static arm.
- §6.4.3 pp. 57–58 "The baseline-beats-memory finding": dedicated memory does not reliably help; naive in-context recent history outperforms several memory architectures [Asawa et al. 2026]; "continuously LLM-consolidated textual memory has a utility curve that rises and then degrades below the no-memory baseline" [Zhang et al. 2026a]; token-matched vanilla baseline matches memory/skill modules on WebArena [Hajimiri et al. 2026, §10.1 p. 89]; lossy memory underperforms high-fidelity RAG on a lifelog horizon [Zheng et al. 2026b, §10.7 p. 95]. "an ungoverned memory system can be strictly worse than having no memory at all once the horizon is long enough."
- §8.2.3 p. 73: "access-versus-compliance gap: even when a user's prior correction is present and recalled, agents still violate it most of the time, because recall is not compliance [Zhou et al. 2026d]"; §8.2.2 p. 72: "silent integration failure ... retrieval quality is necessary but not sufficient."
- §7.6 p. 66 / §3.2.5 p. 29: TriggerBench [Zhang et al. 2026g] — "spontaneous recall is far harder than retrospective query-driven recall and degrades as context length grows": a latent stored constraint stops governing behaviour as context grows — the conceptual core of MSD, measured in another domain.
- §10.4 pp. 92–93 / Table 20: finance resources (FinMem, FinAgent, FinCon, InvestorBench, τ-Banking, RetailBench thousand-day horizon where "errors compound over the horizon", KTD-Fin) all score returns/compliance, none persona mandates.
- §8.2.3: belief drift benchmark [Myakala et al. 2026, BeliefShift].

(d) ORIGINAL: PARTIALLY ANTICIPATES "re-grounding not universally beneficial" (memory net-negativity is an established, multiply replicated pattern); PARTIALLY ANTICIPATES the MSD concept (TriggerBench); PARTIALLY ANTICIPATES behaviour-vs-recall dissociation ("recall is not compliance"). CONTRADICTS FinPersona's self-description: its static arm is episodic, not a persistent-state system. IRRELEVANT to synthetic ground truth, MAS/CI/RG specifics, placebo, 4.4x.

(e) REFRAMED: background only; nothing in the survey owns content-modulated directive injection in trading. The episodic/fixed-context framing is what makes the reframed claim clean.

(f) Cite: yes (baseline-beats-memory literature; episodic vs always-on distinction). Differentiation: "Ding et al. document that ungoverned memory can be net-negative across domains; our arms are episodic by design and isolate one prompt element, showing that whether a re-injected directive helps or hurts depends on its content and the target it is scored against."

(g) Cycle 1 check: not cited for C10, where §6.4.3 is the strongest general prior, nor for the episodic/always-on distinction underpinning Cycle 1's Part I. Missed, not wrong.

---

## 12. Ko & Geiping — "Attractor States Emerge in Multi-Turn LLM Conversations" (arXiv 2606.30571; MPI-IS/ELLIS Tübingen; 40 pp)

(a) Citation/venue: arXiv preprint, 29 Jun 2026.

(b) What it does: 20-turn dyadic debates on 20 controversial topics; 7–10 models (GPT-4o-mini, GPT-4.1-nano, Gemini 2.5 Flash/Lite, Claude 4.5 Opus/Haiku, Grok 4.1, Qwen 3.5, Nemotron); self-play vs mixed-play; SBERT trajectory geometry (S_basin>1 all models, Table 1 p. 5; pair contraction mean 23.6%, Table 2 p. 6; partnerward pull α: Claude Haiku 0.266, GPT-4.1 nano 0.665); discourse-trait transfer (Figs 7–8 p. 9); stance tracking.

(c) Findings: §5.2 p. 10 / Fig. 9b: "explicit role assignment does not reliably produce convergence or compromise: some trajectories soften toward neutrality [Gemini, GPT, Qwen], whereas others reverse direction [GPT Opposer] or preserve a strong assigned stance [Grok]" — assigned-role salience decays for some models over 20 turns and persists for others. App. D.3 pp. 25–27: discourse drifts from debate to affiliation (agreement 0.279→0.688; rebuttal 0.157→0.061). §2 reviews persona-drift work (Li et al. 2024; Lu et al. 2026; Baltaji et al. 2024).

(d) ORIGINAL: PARTIALLY ANTICIPATES model-dependence (model-intrinsic attractors dominate assigned roles) and, loosely, role-salience decay over turns; offers an alternative explanation for FinPersona's per-model heterogeneity. IRRELEVANT to finance, re-injection, placebo, metrics. (e) REFRAMED: no bearing. (f) Cite: yes (role/persona drift). Differentiation: "Ko & Geiping show assigned stances decay toward model-specific attractors in open-ended multi-agent debate; we show the analogous role of model identity in whether a re-injected mandate helps or hurts in a fixed single-agent task." (g) Cycle 1: not referenced; nothing to correct.

---

## 13. Wu, Zhang, Zhou, Wang, Peng, Li, Fan, Zhao (Meta AI) — "Remember When It Matters: Proactive Memory Agent for Long-Horizon Agents" (arXiv 2607.08716; 12 pp)

(a) Citation/venue: arXiv preprint dated 10 Jul 2026; code github.com/yifannnwu/proactive-memory-agent.

(b) What it does: a separate memory agent (Claude Opus 4.6) runs beside an unmodified action agent (Claude Sonnet 4.5 or Opus 4.6), invoked at the first step and then every step (§4.1 p. 7), updates a structured bank (status/knowledge/procedural) via tool calls, and decides whether to inject a concise reminder into the next action call or stay silent. Terminal-Bench 2.0 (85 tasks) and τ²-Bench (278 tasks). Also trains Qwen3.5-27B as a memory agent (SFT + GRPO on SETA).

(c) Findings:
- Definition p. 1: "We call this failure mode behavioral state decay. ... information that should shape future actions ... stops influencing the agent's next decision. The information may still be present in the transcript, or may even remain within the model's context window, but it no longer exerts reliable control over behavior."
- Table 1 p. 7: +8.3 pp (Sonnet) / +2.4 pp (Opus) on Terminal-Bench; +6.8 / +2.5 on τ²-Bench.
- Table 2 p. 8 (τ²-Bench, Sonnet 4.5): baseline macro 57.5 / micro 55.0; full selective 64.3 / 61.2; full-bank context 61.5 / 58.6; ALWAYS INJECT 63.5 / 61.5; injection-only (no bank) 61.0 / 60.8 (airline 62.0 < baseline 68.0); Mem0 62.1 / 60.8. Text: "Always inject is competitive and slightly leads on micro-average by 0.3 points, but this gap is within expected run variance and disappears on the domain-balanced macro-average, where selective silence is better, especially on airline." §2.3 p. 3: "unnecessary interventions can be harmful rather than merely redundant." §4.4 p. 10: "memory interventions help more often than they hurt." Table 4a p. 10: an untrained 27B memory agent hurts (0.709 → 0.693).
- §3.4 p. 6: fixed-interval trigger, "to isolate the effect of the memory intervention policy itself."

(d) ORIGINAL: ANTICIPATES the MSD concept (behavioral state decay: state present in context yet no longer controlling behaviour — the same idea, in a setting where context genuinely accumulates); ANTICIPATES the selective re-grounding prescription (memory as a calibrated intervention policy; selective > always-on on macro average); PARTIALLY ANTICIPATES the injection-frequency question (always-on vs selective vs none arms; no k-sweep). Does not test directive content, personas, placebo text, finance, or an allocation target.

(e) REFRAMED: weak bearing — reminders are task-state facts/rules selected by a second model; the outcome is task success, not a direction of behaviour; no content-sign reversal. Establishes that appending reminder text to the next call changes behaviour in frontier Claude models.

(f) Cite: YES (must). Differentiation: "Wu et al. re-inject task-state reminders chosen by a second model and find selective injection beats always-on on balance; we re-inject a fixed behavioural directive at every step and find that the sign of its effect depends on the directive's content."

(g) Cycle 1 check: (i) "defines 'behavioral state decay' near-verbatim" — the concept is the same and anticipates C1 in substance; "near-verbatim" overstates the wording match. (ii) "Meta always-on vs selective ablation" / "shows always-on injection can hurt": in Table 2 always-inject never falls below the no-memory baseline (72.0>68.0, 58.8>49.1, 59.6>55.3) and slightly beats selective on micro-average; what hurts vs baseline is ungrounded injection-only guidance on airline and an untrained memory agent. Accurate wording: "always-on is competitive but less balanced than selective; unnecessary or ungrounded interventions can hurt." (iii) "Meta built it" (C18) — correct.

---

## 14. Jiang, Peng & Yan — "Personality differences and investment decision-making", Journal of Financial Economics 153 (2024) 103776 (19 pp incl. LSE repository cover)

(a) Citation/venue: JFE 2024, open access.

(b) What it does: AAII survey, n = 3,325 affluent US investors (median wealth $3.5M; 93% male; median age 75); 20-item SAPA Big Five (1–6 scale); beliefs, risk aversion (job-lottery items), social herding item, equity shares; HILDA (Australia) and GSOEP (Germany) replications; Chinese SZSE belief survey (App. B).

(c) Findings: Neuroticism → pessimism (expected return −0.79 pp/point, crash probability +1.02 pp; Table 3 p. 8); Openness → lower risk aversion (Table 5 p. 10); equity share (Table 7 p. 11): Neuroticism −1.74*** pp/point (retirement −2.55***), Openness +0.94** (retirement +1.50***), Conscientiousness −1.32**; Adjusted R² = 0.05 (cols 1–2), 0.07–0.08 with belief/risk controls and for non-retirement; HILDA: N −0.56**, O +0.81*** (Table 8 p. 12); GSOEP participation: N −1.07**, O +1.11*** (Table 9 p. 12); "Neuroticism and Openness stand out" (abstract).

Verification of Cycle 1's use: (i) "adjusted R² ≈ 0.05" — CORRECT for the headline AAII equity-share regressions (Table 7 cols 1–2). (ii) "5–8 pp equity swing across the full Big Five range" — NOT stated in the paper; derived. Using Neuroticism −1.74 pp/point: full 1–6 range (5 points) ⇒ 8.7 pp; 10th–90th percentile range (2.00–4.75, Table 1a) ⇒ 4.8 pp. Openness: 0.94×5 = 4.7 pp; 10–90 range (3.25–5.65) ⇒ 2.3 pp. "≈5–8 pp" is a fair summary for Neuroticism (4.8–8.7) but should be labelled derived; smaller for Openness. (iii) "Neuroticism has the largest coefficient" — CORRECT for total and retirement equity share (|−1.74| > |−1.32| > 0.94); not for non-retirement (Openness 1.15** vs Neuroticism −0.80 n.s.). The paper's headline is "Neuroticism and Openness", not Neuroticism alone.

(d) ORIGINAL: SUPPORTS the direction of FinPersona's OCEAN mapping (O1-Conservative = high C & N, low O → less equity; O2 = high O & E, low N → more) and the vocabulary framing if cited honestly; CONTRADICTS the magnitude implied by C_ideal (80-point target spread vs single-digit pp human effects and R² ≈ 0.05); exposes that FinPersona's MBTI personas omit Neuroticism, the strongest human predictor (conceded in FinPersona's Limitations; OCEAN O1 includes high N). IRRELEVANT to MSD, re-grounding, placebo. (e) REFRAMED: no bearing. (f) Cite: yes, carefully. Differentiation: "Jiang, Peng and Yan find Big Five traits explain ≈5% of equity-share variance with Neuroticism and Openness salient; our personas are prescriptive mandates, not calibrated trait effects, and their allocation targets should be read as stipulated, not derived." (g) Cycle 1 check: Reviewer B's summary is accurate except that "5–8 pp" is derived (not reported) and "largest coefficient" holds for total/retirement only.

---

## SYNTHESIS for this share

### A. FinPersona claims fully or largely anticipated by papers in this share
1. MSD as a concept (information/instructions present in context but no longer governing behaviour): ANTICIPATED in substance by Wu et al. (behavioral state decay, 2607.08716 p. 1), by Dongre et al. (goal accessibility decline, 2605.12922), and — via the Always-On survey — by TriggerBench (prospective recall degrading with context). FinPersona's name is new; the idea is not. Worse, all three prior instantiations have genuinely accumulating context; FinPersona's static arm does not (stateless single-turn — "episodic" in the Always-On survey's vocabulary, §2.1 p. 16).
2. Behaviour distinct from reasoning/language: ANTICIPATED by CLQT's coherence gap (+0.30/+0.23, held-out judge, live-replicated), by Kocielnik et al. (persona prompts move self-reports, not behaviour), and by the "recall is not compliance" literature summarised in the Always-On survey §8.2.3.
3. "Re-grounding/memory is not universally beneficial": the generic form is settled — Always-On survey §6.4.3 (memory below no-memory baseline; token-matched baselines match memory modules), CLQT (no-memory within noise), Wu et al. (selective > always-on on macro average; ungrounded injection hurts). What is NOT owned by anyone here is the sign reversal by mandate content.
4. Selective / event-triggered re-grounding prescription: ANTICIPATED — Wu et al. built a selective intervention policy; CLQT ships a C_t<0.7 drift-warning trigger (§3.5 p. 12), the very "event-triggered re-injection" FinPersona lists as untested.
5. Transfer to medical triage: already executed by Menon et al. (§4.3).
6. Model-dependence: ANTICIPATED across Menon (family-specific resilience and instruction-hierarchy behaviour), Kocielnik (per-model coherence profiles), Ko & Geiping (model-specific attractors), Dongre (architecture-specific post-closure survival).
7. MBTI/Big Five as vocabulary, and the weakness of Big Five as a behavioural predictor: ANTICIPATED and sharpened by Kocielnik (Big Five reliable but non-predictive of within-model behaviour) — which also undercuts FinPersona's presentation of OCEAN as "validation". Jiang–Peng–Yan supports direction, contradicts magnitude.
8. A prior three-arm re-injection design with a length-matched irrelevant control exists (Dongre App. H), though qualitative, prepended, on recall, and null.

### B. FinPersona claims not anticipated by anything in this share (remain unclaimed here)
- Content-conditioned sign reversal of a re-injected directive's behavioural effect in a fixed environment (17/18 vs 16/18 against opposed targets) — nothing in the share varies directive content against a fixed task. Nearest analogue: Kocielnik's loss-averse vs gain-seeking policy framing moving risk-taking (single session, no placebo, no trading).
- A length-matched declarative placebo arm in a trading loop (Dongre's matched-irrelevant block is the only prior arm, on recall, qualitative, null).
- The specific MAS/CI/RG operationalisations, the decoupled V_t/P_t synthetic engine, the T-calibration, the LCR construct, and the 4.4x quartile analysis are not anticipated by papers in this share (other shares cover Hashimoto/ABIDES/Machine Spirits/Drift No More).
- The injection-frequency k-sweep (k∈{1,5,25,100,∞}) is not run by anything in this share (Wu et al. compare always-on vs selective vs none only; Kim/Li is outside my share).

### C. Direct competitors in this share
- CLQT (2606.29771) is the closest benchmark competitor: finance, closed-loop, mandate-adherence axis (Discipline), strategy-consistency score with a drift trigger, behaviour-vs-stated-analysis gap, memory ablation — on real data with costs and a live track. It does not vary the mandate (named as future work, §8.8), which is exactly the seam FinPersona can occupy.
- Wu et al. (2607.08716) is the closest intervention competitor (re-injection as a calibrated policy; always-on vs selective), but task-state reminders, not behavioural mandates.
- Kocielnik et al. (2606.12730) is the closest behavioural-science competitor (persona/Big Five prompting and in-context framing vs measured risk behaviour), single-shot.
- Dongre et al. (2605.12922) is the closest mechanistic competitor (attention-salience decay; prior 3-arm re-injection design).

### D. Papers whose findings CONTRADICT a FinPersona result (result and number)
- Menon et al.: frontier models show zero drift over 30 steps under adversarial pressure in a stock-trading environment (p. 5). Tension with FinPersona's claim that static agents "progressively abandon their target allocations" (flat-market cash 35.6% vs 49.4%, Table 9) — in Menon, drift required conditioning, not mere context. Since FinPersona's static arm has no accumulating context, FinPersona's "decay" cannot be the same phenomenon; the contradiction is with the paper's causal story, not its numbers.
- Dongre et al.: (i) under default attention, 50 turns, fact recall 100% despite GAR falling 27–48% (pp. 7–8) — accessibility decay without behavioural decay, against FinPersona's inference from behavioural drift to salience loss; (ii) App. H naive periodic re-injection of the goal block did not improve recall (qualitative null) — against FinPersona's assumption that re-injection at recency "keeps the mandate active" (§3.2), albeit under different position/task/models.
- CLQT: style drift ≈ 0 cohort-wide over 26 rounds with three-tier memory (p. 19) — a mandate/style-consistency measure that does not drift; and autonomous-mode HOLD rates of 44–50% were reliability artefacts (schema failure, tool-turn exhaustion), not choices (§7.11) — a direct warning that FinPersona's HOLD/cash shifts must be audited for parse/format failure before being read as content effects (FinPersona reports no parse-failure or refusal rates; MAS = 0.000 "perfect adherence" cells are consistent with never trading).
- Jiang–Peng–Yan: human Big Five effects on equity share are single-digit pp with adjusted R² ≈ 0.05 (Table 7); FinPersona's C_ideal spread (0.2 vs 1.0, 80 pp) cannot be grounded in this literature and its MBTI instrument omits Neuroticism (−1.74 pp/point, the largest total-equity coefficient).
- Kocielnik et al.: task-agnostic Big Five items placed in context shifted risk-taking (CCT 8.9 → 13.2 cards, App. I.9) — a demonstration that behaviourally "irrelevant" text can move risk behaviour, which complicates reading FinPersona's placebo (itself significant vs static, p=0.041) as a clean null.
- Wu et al. (against a Cycle 1 gloss rather than FinPersona): always-on injection did not fall below baseline in Table 2; the ENTJ "re-grounding hurts" result in FinPersona therefore has no direct analogue of "always-on hurts" in Wu et al.

### E. On the REFRAMED claim
No paper in this share owns it. Partial anticipations: Kocielnik (content-modulated in-context framing shifts risk-taking; any in-context text shifts behaviour), Fin-Bias (explicit in-context opinion shifts financial decision toward its content), Menon (user-turn instructions dominate system-prompt goals for several model families — a mechanism for why an appended directive works, and why it is model-dependent), Wu et al. (appended reminders change frontier-model behaviour), KTD-Fin (baseline disposition toward cash/no-trade when signals are absent; in-prompt instructions are weak levers for memorised priors). Cautions: Dongre App. H null for prepended re-injection; CLQT reliability-driven holds; Kocielnik's placebo-like text shifting behaviour. The claim survives as unclaimed in this share provided FinPersona (a) reports parse/refusal/always-HOLD rates, (b) reports the mean-cash mediation of the 17/18 vs 16/18 split, and (c) positions against Kocielnik, Menon, Wu and Dongre explicitly.

---

## Cycle 1 agreement / disagreement list (papers in my share only)

Per-claim (C1–C19 table) and per-statement checks. Cycle 1 verdicts I re-examined where my share supplies the cited evidence.

1. C1 "Meta 2607.08716 defines 'behavioral state decay' near-verbatim" — AGREE that the concept is anticipated (verbatim definition quoted in §13(c) above); DISAGREE with "near-verbatim": the phrasing differs; the substance is the same. Verdict FULLY ANTICIPATED stands (also by Dongre's GAR and TriggerBench).
2. C2 "CLQT coherence gap +0.30/+0.23; Kocielnik" — AGREE; numbers verified (CLQT abstract, §7.10, Fig. 12; Kocielnik RQ4).
3. C8 model-dependence — AGREE (Menon, Kocielnik, Ko & Geiping, Dongre in my share all show it).
4. C10 "Meta always-on vs selective ablation ... CLQT no-memory ablation" — AGREE on PARTIALLY ANTICIPATED, but the Meta characterisation needs correction: always-on injection does not fall below baseline in Wu et al. Table 2 (it is competitive; selective wins on macro only; ungrounded injection hurts). Cycle 1 should additionally cite the Always-On survey §6.4.3 (baseline-beats-memory) as the strongest general prior for "memory can hurt".
5. C11 "When Attention Closes App. H identical 3-arm design" — PARTIAL DISAGREEMENT: a prior 3-arm design with a length/entity-matched irrelevant block does exist (verified), but it is prepended not appended, fact recall not behaviour, under a forced sliding-window mask, reported only qualitatively, and null for both arms. "Analogous and prior" is right; "identical" is not. (ContextEcho and Arike are outside my share; I cannot confirm those halves of C11.)
6. C12/C17 Kocielnik — AGREE (Big Five non-predictive; persona prompting moves SR not behaviour). Cycle 1 missed App. I.9 (any in-context self-report perturbs behaviour; content-modulated risk priming), which is the most relevant part for the placebo and the reframed claim.
7. C18 "Meta built it; CLQT §3.5 ships a C_t<0.7 trigger" — AGREE; both verified verbatim (CLQT §3.5 p. 12, Fig. 4 p. 13; Wu et al. §3.3–3.4).
8. C19 "Menon runs ER triage" — AGREE (Menon §4.3, pp. 8–9).
9. Cycle 1 Part VI on M3: "well-powered null in When Attention Closes Appendix D.5 (all permutation p > 0.05; true-patch and random-patch flipping the same pairs in lock-step)" — the null and lock-step are correctly reported; "well-powered" is not: n=30 pairs, Mistral-7B only, fact-recall task, and the authors flag non-linear/distributed read-outs as open (pp. 10, 18). It is a relevant risk signal for M3, not a settled null for mandate-behaviour patching.
10. Cycle 1 Part IV.3 on CLQT ("ships a threshold-triggered mandate re-grounding controller ... never defines a_target, never ablates the investment-target module, and names varying the mandate as future work in section 8.8") — AGREE on every element (verified: §3.5 p. 12; Table 9 p. 33 "(not ablated alone)"; §8.8 p. 48). Cycle 1 omitted two further CLQT facts that cut against FinPersona: style drift ≈ 0 cohort-wide (p. 19) and the reliability-driven hold mechanism (§7.11).
11. Cycle 1 Part III.2 on Jiang–Peng–Yan ("adjusted R-squared of 0.05 and a 5-8 percentage point equity swing across the full Big Five range ... Neuroticism - the trait with the largest coefficient") — AGREE on R² (0.05, Table 7 cols 1–2) and on Neuroticism being the largest coefficient for total/retirement equity; NOTE that "5–8 pp" is derived (4.8–8.7 pp for Neuroticism depending on the range used; smaller for Openness) and is not a figure the paper reports; and that the paper's own headline is "Neuroticism and Openness".
12. Cycle 1 "Financial agent benchmarks: CLQT; Ross and Lo; KTD-Fin; AI-Trader; Agentic Trading survey" and "Goal drift: Menon" — AGREE; my reading of KTD-Fin and the Agentic Trading survey finds no anticipation of FinPersona's specific claims beyond positioning (KTD-Fin's leakage argument supports the synthetic-market motivation; the survey's MR-4 exposes FinPersona's frictionless W_t).
13. Items Cycle 1 did not use that it should: Always-On survey §2.1 (episodic vs always-on — the cleanest vocabulary for the Part I architecture finding) and §6.4.3 (baseline-beats-memory); Menon's instruction-hierarchy test (user-turn instruction dominance as the mechanism behind user-position re-injection, and its model-dependence); Kocielnik App. I.9; CLQT style-drift ≈ 0 and reliability-driven holds; Ko & Geiping (assigned-stance softening as a multi-turn analogue of mandate salience decay, model-dependent).
14. Papers in my share that Cycle 1 did not cite and that are IRRELEVANT (no correction needed): 2604_08524 (refusal steering circuits), 2605_13329 (persona vectors in pretraining), 2606_29142 (regulatory threat mapping), 2605_09106 (Fin-Bias; mildly relevant to in-context cue following only).
