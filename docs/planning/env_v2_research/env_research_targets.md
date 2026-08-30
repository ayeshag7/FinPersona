# FinPersona-Bench — Allocation targets and persona realism

Research thread: should C_ideal (ISFJ 1.0 / INTJ 0.5 / ENTJ 0.2) be *derived* from Jiang, Peng & Yan (JFE 2024), *stipulated*, or *replaced*? Prepared 2026-08-22. All numbers carry a source; local PDFs are cited by repo path + table/page.

Current state of the paper (scratchpad/paper_current.txt, Sec. 3.3.1 lines 370-376): "Grounded in mean-variance portfolio theory (Markowitz, 1952), Cideal defines the agent's target allocation between cash and risky assets. Specifically, Cideal = 1.0 for ISFJ (capital preservation), Cideal = 0.5 for INTJ (balanced), and Cideal = 0.2 for ENTJ (growth-oriented)." Code: `experiments/run_experiments.py` CIDEAL_MAP = {ISFJ: 1.0, INTJ: 0.5, ENTJ: 0.2}; `agent/ocean_prompts.py` O1_conservative (O=3,C=8,E=3,A=6,N=8, cideal 1.0), O2_aggressive (O=8,C=6,E=8,A=2,N=2, cideal 0.2), O3 numerical-only ("Your target cash allocation is 100% (Cideal = 1.0)"). ISFJ prompt (`agent/personas/mbti_profiles.json`): "You prefer Index Funds, Bonds, and sector leaders that have survived recessions ... Buy insurance (puts/hedges)."

---

## 1. JFE 2024 coefficients and what they imply for targets

Source: Jiang, Peng & Yan (2024), *Personality differences and investment decision-making*, JFE 153, 103776, https://doi.org/10.1016/j.jfineco.2023.103776 (local: `references/related_work_2026/Jiang_Peng_Yan_2024_JFE_Personality_Investment.pdf`). AAII survey, N = 3,325, median wealth $3.5M, 93% male, mean age 68 (Table 1a, p. 6). Traits: SAPA 20-item, each trait = mean of four 1-6 items.

### 1.1 Sample descriptives (Table 1a, p. 6)

| Trait | Mean | SD | P10 | P50 | P90 |
|---|---|---|---|---|---|
| Agreeableness | 4.86 | 0.73 | 3.75 | 5.00 | 5.75 |
| Conscientiousness | 4.89 | 0.74 | 3.75 | 5.00 | 5.75 |
| Neuroticism | 3.39 | 0.97 | 2.00 | 3.50 | 4.75 |
| Extraversion | 2.59 | 1.04 | 1.25 | 2.50 | 4.00 |
| Openness | 4.48 | 0.92 | 3.25 | 4.50 | 5.65 |

One trait point is roughly one SD (SD 0.73-1.04), so the coefficients below are approximately per-SD effects.

### 1.2 Coefficients (per 1 trait point; *, **, *** = 10/5/1%)

| Outcome (table) | A | C | N | E | O | Adj. R² | N obs |
|---|---|---|---|---|---|---|---|
| Expected 1-yr stock return, pp (T3 c1) | -0.10 | 0.66*** | -0.79*** | 0.82*** | 0.04 | 0.03 | 3,325 |
| P(crash > 20%), pp (T3 c3) | -0.09 | -0.99** | 1.02*** | -1.07*** | 0.92** | 0.01 | 3,325 |
| P(rise > 20%), pp (T3 c2) | -0.34 | -0.07 | -0.21 | 1.27*** | 1.49*** | 0.04 | 3,325 |
| Risk-aversion index 1-4 (T5 c4) | 0.09*** | 0.02 | 0.03* | -0.06*** | -0.08*** | 0.04 | 3,325 |
| Equity share of financial wealth, pp, TOTAL (T7 c1) | -0.46 | -1.32** | -1.74*** | -0.33 | 0.94** | 0.05 | 2,807 |
| Equity share, RETIREMENT accounts (T7 c2) | -0.02 | -0.66 | -2.55*** | 0.14 | 1.50*** | 0.05 | 3,285 |
| Equity share, NON-RETIREMENT (T7 c3) | -0.70 | -1.00 | -0.80 | -0.05 | 1.15** | 0.07 | 3,281 |
| Equity share TOTAL + belief/RA controls (T7 c4) | -0.39 | -1.51*** | -1.44*** | -0.65 | 0.95** | 0.07 | 2,807 |
| HILDA equity share 0-100, one-person HH (T8 c1) | 0.04 | -0.39 | -0.56** | 0.13 | 0.81*** | 0.17 | 5,542 |
| HILDA equity share, decision-maker (T8 c2) | -0.17 | -0.35* | -0.46** | -0.26 | 0.63*** | 0.16 | 8,924 |
| GSOEP participation x100 (T9 c1 / c2) | 0.30 / -0.73 | -2.06*** / -1.97*** | -1.07** / -0.94*** | -1.16** / -1.11* | 1.11*** / 1.27*** | 0.15 / 0.15 | 10,250 / 10,781 |

In T7 c4 the controls themselves: expected return +0.23*** pp equity per pp, down-tail prob -0.08***, risk-aversion index -1.17*** per step (p. 11). Personality-only adj. R² for beliefs is 0.005-0.02 (T3 panel b); the 0.15-0.17 in HILDA/GSOEP includes demographics and year FE. Appendix B (Chinese SZSE survey, n ~ 17,324): personality-only adj. R² for beliefs 0.015-0.027 (Table A1).

### 1.3 Derived equity-share differences (arithmetic)

Method: Δequity(pp) = Σ_trait coef × (trait value − sample mean). Persona trait values are the paper's O1/O2 0-10 scores mapped linearly onto the AAII 1-6 scale with 2/10 → P10 and 8/10 → P90 (so 5/10 ≈ median). Mapped values: O1-conservative O 3.65, C 5.75, E 1.71, A 5.08, N 4.75; O2-aggressive O 5.65, C 5.08, E 4.00, A 3.75, N 2.00; balanced ≈ means.

| Specification | Conservative (O1) | Balanced | Aggressive (O2) | Spread aggr − cons |
|---|---|---|---|---|
| AAII total equity share (T7 c1) | -4.1 pp | +0.2 | +3.3 pp | **7.4 pp** |
| AAII retirement (T7 c2) | -5.4 | +0.1 | +5.4 | **10.8 pp** |
| AAII non-retirement (T7 c3) | -3.0 | +0.2 | +3.0 | 6.0 pp |
| AAII total with belief/RA controls (T7 c4) | -3.6 | +0.2 | +2.3 | 5.9 pp |
| HILDA one-person (T8 c1) | -1.9 | 0.0 | +1.8 | 3.7 pp |
| HILDA decision-maker (T8 c2) | -1.3 | 0.0 | +1.1 | 2.4 pp |

Bounding cases (all five traits at P10/P90 extremes in the "right" direction): T7 c1 9.7 pp, T7 c2 12.4 pp, T7 c4 8.3 pp, HILDA 3.1-4.5 pp. Neuroticism + Openness only, ±1 SD: T7 c1 5.1 pp, T7 c2 7.7 pp, HILDA 2.1-2.6 pp. Neuroticism + Openness at P10/P90: T7 c1 7.0 pp, T7 c2 10.6 pp.

Translation to cash fraction (the environment has cash vs one risky asset): if the baseline investor holds ~65% equity (Foerster et al. 2017 report 68-74% risky share for advised Canadian clients; Rossi & Utkus 2024 59% for robo clients; both as cited in Fieberg et al. 2025 p. 21), the JFE-implied targets are roughly cash ≈ 0.39-0.41 (conservative), ≈ 0.35 (balanced), ≈ 0.30-0.32 (aggressive). **JFE-implied cash spread ≈ 0.06-0.12 (upper bound ~0.12); the paper's spread is 1.0 − 0.2 = 0.80, i.e. 7-13x larger than anything the trait coefficients can generate.** Even the most generous reading (retirement accounts, all traits at deciles) gives 12 pp, not 80.

### 1.4 Why the JFE cannot be the *source* of point targets

1. Explanatory power: personality adds ≤ 2-3 pp of adjusted R² for equity share (AAII adj. R² 0.05-0.08 including demographics; personality-only for beliefs 0.005-0.02). Traits shift the *mean* allocation by single-digit pp around a ~60-70% equity centre; they do not define a target. Jiang et al. themselves frame the traits as "a useful tool for dimension reduction", not as a planning mapping (Sec. 6.1).
2. MBTI omits Neuroticism. McCrae & Costa (1989), *J. Personality* 57:17-40, https://doi.org/10.1111/j.1467-6494.1989.tb00759.x: MBTI E-I ↔ Extraversion r = −0.74, S-N ↔ Openness r = 0.72, T-F ↔ Agreeableness r = 0.44, J-P ↔ Conscientiousness r = −0.49; no MBTI scale for Neuroticism. Neuroticism is the largest AAII coefficient (−1.74 total, −2.55 retirement) and the belief channel (−0.79 pp expected return, +1.02 pp crash probability per point). An MBTI persona therefore cannot carry the JFE's main effect; the ISFJ↔"high N" link in Appendix G is an authorial stipulation, not something MBTI encodes.
3. Sign problems inside the MBTI mapping. All three personas are "J" (→ higher Conscientiousness), and Conscientiousness lowers equity share in the AAII (−1.32**, −1.51***) and GSOEP (−2.06***). ENTJ and INTJ differ only on E-I, and Extraversion is insignificant for AAII equity share (−0.33) — by the JFE, INTJ and ENTJ should hold near-identical equity shares, so the data cannot justify 0.5 vs 0.2. ISFJ (S → low Openness) is the only persona for which the JFE direction is clean, and the implied effect is a few pp, not "all cash".
4. Construct validity on the LLM side (Sec. 4): Big Five self-reports do not predict LLM risk behaviour (Kocielnik et al. 2026), and trait interventions only move GPT-4o's CPT parameters within the risk-neutral regime (Hartley et al. 2025). Deriving a behavioural target from human trait coefficients and scoring an LLM against it compounds two weak links.

Verdict for Q1: the JFE supports the **ordering** (low-O/high-N persona invests less than high-O/low-N persona) and a **spread of order 5-12 pp**; it does not support 0.2/0.5/1.0 and cannot be the source of point targets. Use it as a sensitivity/ordering check only.

---

## 2. Practitioner and regulatory conventions

| Convention | Conservative / capital preservation | Balanced / moderate | Aggressive / growth | Source |
|---|---|---|---|---|
| Morningstar US fund categories (strategic equity exposure) | Conservative Allocation **15-30%** equity; Moderately Conservative 30-50% | Moderate 50-70% | Moderately Aggressive 70-85%; Aggressive > 85% | Morningstar Category Classifications US Funds, April 2025, pp. 18-19, https://advisor.morningstar.com/Enterprise/VTC/MorningstarCategoryClassificationUSFunds_April2025.pdf |
| Morningstar Target Risk indexes | Conservative 20% equity; Mod. Conservative 40% | Moderate 60% | Mod. Aggressive 80%; Aggressive 95% | https://indexes.morningstar.com/indexes/details/morningstar-moderately-conservative-target-risk-FSUSA09PYH |
| Vanguard LifeStrategy (target-risk funds) | Income **20/80**; Conservative Growth **40/60** ("Balanced and static allocation: 40% stocks, 60% bonds") | Moderate Growth 60/40 | Growth 80/20 | Vanguard LifeStrategy Conservative Growth profile (licf.org mirror of Vanguard PDF, 2016-09-30); https://advisors.vanguard.com/investments/products/vscgx/vanguard-lifestrategy-conservative-growth-fund |
| Fidelity target asset mixes (Planning & Guidance Center) — domestic/foreign stock/bonds/short-term | Short-Term 0/0/0/**100**; Conservative 14/6/50/**30** (20% equity); Moderate w/ Income 21/9/50/20 | Moderate 28/12/45/15; Balanced 35/15/40/10 | Growth w/ Income 42/18/35/5; Growth 49/21/25/5; Aggressive Growth 60/25/15/0; Most Aggressive 70/30/0/0 | Fidelity "Detailed Methodology, Planning & Guidance Center Investment Strategy", https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/fidelity/about-fidelity-model-portfolios.pdf ; Fidelity Asset Manager 20%/50%/85% = Conservative/Balanced/Aggressive Growth mixes |
| Betterment (robo) | "Very conservative" = > 7 pp below recommended stock %; "Conservative" = 4-7 pp below; retirement-income floor 30% stocks; major-purchase goal → **0% stocks at horizon** ("near zero risk" only because "we expect you to fully liquidate your investment at the intended date") | Moderate = within 3 pp of recommendation; retirement at retirement age 56% stocks | 90% stocks for 20+ year horizons | https://www.betterment.com/resources/asset-allocation-methodology |
| Wealthfront (robo) | risk score 0.5 = lowest-volatility of 20 allocations | — | risk score 8.0 example (medium tax): US stocks 45%, foreign dev. 18%, EM 16%, dividend 3% = **82% equity**, 18% bonds | https://research.wealthfront.com/whitepapers/investment-methodology/ ; https://www.wealthfront.com/explore/portfolios/core/classic |
| Fieberg et al. 2025 (32 LLMs × 64 profiles; benchmark robo-advisors) | LLM average equity share 67%; robo-advisor benchmark 59% equity / 38% fixed income; high- vs low-risk-tolerance gap: **30 pp** (LLMs), **42 pp** (robo-advisors), 25 pp (Bhattacharya et al. 2012 algorithm), 38 pp (Foerster et al. 2017 human advisors); risky share 37%-75% across risk-aversion levels | | | CESifo WP 11666, pp. 21-25, https://www.ifo.de/DocDL/cesifo1_wp11666.pdf |
| FINRA Rule 2111 (suitability) | Investment profile must include "risk tolerance" among age, horizon, liquidity etc.; **no numeric bands prescribed** | | | https://www.finra.org/rules-guidance/rulebooks/finra-rules/2111 |
| ESMA MiFID II suitability guidelines (2023) | Para. 55: firm "will determine the client's investment risk profile, i.e. what type of investment services or financial instruments can in general be suitable for him" incl. "his risk tolerance"; **categories, not percentages** | | | ESMA35-43-3172, https://www.esma.europa.eu/sites/default/files/2023-04/ESMA35-43-3172_Guidelines_on_certain_aspects_of_the_MiFID_II_suitability_requirements.pdf |
| Merton/Samuelson optimal risky share π* = (μ−r)/(γσ²) | γ = 8-10 → **15-25%** risky (ERP 4.3-6%, σ 16-20%) | γ = 3-4 → 40-60% | γ ≤ 2 → ≥ 80% (capped at 100%) | computed; ERP 4.33% = Damodaran implied ERP 1 Jan 2025 (https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histimpl.html); 4.3% = DMS 25-yr global premium over bills, UBS Global Investment Returns Yearbook 2025; 6% & σ 17.5% = DMS 1901-2022 global equity premium over cash (Vanguard, "A framework for allocating to cash", Apr 2024, p. 3) |

Merton table (computed):

| ERP / σ | γ=1 | γ=2 | γ=3 | γ=4 | γ=5 | γ=7 | γ=10 |
|---|---|---|---|---|---|---|---|
| 4.3% / 16% | 1.68 | 0.84 | 0.56 | 0.42 | 0.34 | 0.24 | 0.17 |
| 4.3% / 20% | 1.07 | 0.54 | 0.36 | 0.27 | 0.21 | 0.15 | 0.11 |
| 6.0% / 16% | 2.34 | 1.17 | 0.78 | 0.59 | 0.47 | 0.33 | 0.23 |
| 6.0% / 20% | 1.50 | 0.75 | 0.50 | 0.37 | 0.30 | 0.21 | 0.15 |

Implication: for any finite γ and positive premium, mean-variance/Merton never yields 0% risky. **C_ideal = 1.0 is therefore *not* "grounded in Markowitz (1952)"**; it corresponds to γ → ∞ or a zero/negative equity premium. Conservative conventions cluster at **15-30% equity (cash 0.70-0.85 in a cash-vs-equity world)**; balanced at 40-60% equity; aggressive at 80-100% equity. The current 0.2 for ENTJ is at the conservative edge of "aggressive" (Fidelity Aggressive Growth 85%, Most Aggressive 100%, Morningstar Aggressive > 85%, Betterment 90%); 0.5 for INTJ is inside every "balanced" definition.

Two caveats that the paper should state: (i) practitioner bands are strategic allocations over multi-year horizons, whereas the simulation is a short trading game; (ii) the environment has no bond asset, so the conservative persona's "bonds" (named in its own prompt) must be represented by cash — which is exactly why the conservative target should be ~0.8, not 1.0.

---

## 3. Survey evidence: self-reported risk tolerance → actual allocation

SCF question (since 1983): "Which of the statements ... comes closest to the amount of financial risk that you are willing to take when you save or make investments? 1. take substantial financial risks expecting to earn substantial returns; 2. above average ...; 3. average ...; 4. not willing to take any financial risks."

| Study | Data | Finding (numbers) |
|---|---|---|
| Schooley & Worden 1996, *Financial Services Review* 5(2):87-99, Table 2 | 1989 SCF, n = 2,239 | Share of sample: substantial 3.9%, above-avg 9.1%, average 41.1%, none 45.9%. Mean risky-assets/wealth (broad definition incl. human capital and pensions): **.982 / .941 / .858 / .722** — 26 pp spread none→substantial; substantial vs above-average not significantly different (F = 33.04, p < .01). Retired households that report "no risk": .324. https://openjournals.libs.uga.edu/fsr/article/view/3795 |
| Sung & Hanna 1996 (reported in Grable & Lytton 2001, Table 3) | 1992 SCF, employed heads | substantial 4%, above-avg 15%, average 42%, **no risk 40%** |
| Grable & Lytton 2001, *J. Financial Counseling & Planning* 12(2):43-53 | two convenience samples | SCF item vs 13-item scale concurrent validity r = .54 and .44 ("modest"); collapsing to some/no risk drops r to .26 |
| Wang & Hanna 2006, Consumer Interests Annual 52, Table 5 | SCF 1992-2001 pooled, 16,952 HH | Logit of stock ownership, marginal effects vs "no risk": average **+23.4 pp**, above-average **+34.2 pp**, substantial **+24.2 pp** — non-monotonic at the top. https://www.consumerinterests.org/assets/docs/CIA/CIA2006/wanghanna_therisktoleranceandstockownershipofbusiness-owning.pdf |
| Gilliam, Chatterjee & Grable 2010, *JFCP* 21(2):30-43, Tables 4-5 | n = 328 university staff | Tobit, % of assets in stocks: SCF risk category +**17.41*** pp per step** (SE 2.97), pseudo-R² 0.08; logit cash > 50%: SCF −11.53***; 13% held no stock, 25% held no cash. https://www.afcpe.org/wp-content/uploads/2018/10/vol_21_issue_2_gilliam_chatterjee_grable.pdf |
| Jeong 2025, *Financial Planning Review*, https://doi.org/10.1002/cfp2.70007 | SCF 2004-2022 (7 waves) | 42% of households unwilling to take any risk, 38% average, 20% above-average/substantial |
| Federal Reserve, *Changes in U.S. Family Finances 2019-2022* (Oct 2023) | SCF 2022 | 58% of families hold stocks directly or indirectly (53% in 2019); direct ownership 21% (15% in 2019). https://www.federalreserve.gov/publications/october-2023-changes-in-us-family-finances-from-2019-to-2022.htm |
| Vanguard, How America Saves 2025 preview | DC-plan participants | participant-directed equity allocation > 80% (age ≤ 25) to ~45% (70+); extreme 0%/100% equity allocations fell from ~1/3 of participants to 7%. https://corporate.vanguard.com/content/corporatesite/us/en/corp/articles/sneak-peek-how-america-saves-2025.html |
| Capgemini World Wealth Report 2024/2025 | HNWI (> $1M investable) | cash & equivalents **25-26%** of HNWI portfolios (34% peak Jan 2023); equities ~18-25%. https://www.capgemini.com/insights/research-library/world-wealth-report-2025/ |
| Vanguard, "A framework for allocating to cash" (Apr 2024) | DMS 1901-2022 | equity premium over cash ≈ 6%/yr, bonds ≈ 1.6%; σ stocks 17.5%, bonds 11.3%, cash 4.5%; 100% cash is only the best allocation for a fully-funded one-year goal; "stocks are risky—and so is avoiding them". https://corporate.vanguard.com/content/dam/corp/research/pdf/a_framework_for_allocating_to_cash.pdf |
| Ross & Lo 2026, "One Size Fits None" (arXiv 2604.23837, Tables 6-9; local `references/gap_sweep_aug2026/2604_23837.pdf`) | 1,000 LHS client profiles × 4 GPT models | Risk tolerance's share of surrogate predictive weight — equities: GPT-4o 88.2%, GPT-5.4 55.3%, Mini 53.5%, Nano 68.9%; cash & savings: GPT-4o 82.4%, Mini 22.9%, Nano 36.5% (GPT-5.4 top feature = liquid assets 29.8%); text: "self-reported risk tolerance accounting for 57-88% of predictive weight" (p. 5); GPT-4o equities FC = 0.780, R² = 0.882. NB: Tables 6-9 report feature shares, not allocation levels by risk-tolerance category. |

Takeaway: in practice self-reported risk tolerance moves equity share by **~17 pp per category step / 25-42 pp between extremes** (Gilliam; Fieberg benchmarks; Wang & Hanna ownership margins), with a large "no risk" group that still holds substantial risky assets (Schooley & Worden .722). An 80-pp spread with a 100%-cash endpoint is outside every empirical distribution of self-reported conservatives, but a 0.8 / 0.5 / 0.1-0.2 cash ladder (spread 60-70 pp) is consistent with the practitioner target-risk endpoints (Income 20/80 vs Growth 80/20; Fidelity Conservative 20% vs Aggressive Growth 85%).

---

## 4. Personality → risk tolerance / trading behaviour (human and LLM)

| Paper | Sample / design | Effect size & direction |
|---|---|---|
| Filbeck, Hatfield & Horvath 2005, *J. Behavioral Finance* 6(4):170-180, https://doi.org/10.1207/s15427579jpfm0604_1 | survey; MBTI vs EUT tolerance for variance and skew | MBTI type "does explain individual ex ante EUT risk tolerance" (abstract); coefficient magnitudes not retrievable (paywalled) — treat as directional only |
| Mayfield, Perdue & Wooten 2008, *Financial Services Review* 17:219-236 | SEM on Big Five → investment intentions | Extraversion → short-term investing (+); Neuroticism and risk aversion → avoid short-term (−); Openness → long-term investing (+), not short-term |
| Durand, Newby & Sanghani 2008, *JBF* 9(4):193-208; Durand, Newby, Peggs & Siekierka 2013, *JBF* 14(2):116-133 | Australian retail investors; Big 5 + risk-taking propensity + preference for innovation | personality associated with trading, overconfidence, availability heuristic and disposition effect; small samples, directional |
| Nicholson, Soane, Fenton-O'Creevy & Willman 2005, *J. Risk Research* 8:157-176 | N = 2,041, NEO PI-R, 6-domain risk scale | risk propensity = high E & O, low N, A, C |
| Brown & Taylor 2014, *J. Economic Psychology* 45:197-212 (BHPS) | UK panel; probit/tobit | +1 SD Openness → **+2.37 pp** P(hold stocks/shares); +1 SD Extraversion → **−1.87 pp**; C and N "unimportant" for assets (White Rose eprint 82777, pp. 22-23) |
| Conlin et al. 2015, *J. Empirical Finance* 33:34-50 | Finnish NFBC1966 cohort, Cloninger TCI | Harm avoidance ↓ participation; sub-traits (excitability, extravagance, sentimentality, dependence) stronger than aggregates; robust to income/education |
| Rustichini, DeYoung, Jones & Burks 2016, *JBEE* 64:122-137 | ~1,000 trainee truckers, lab preferences + Big Five | Neuroticism and cognitive ability "explain much of risk preferences"; traits predict outcomes as well or better than elicited preferences |
| Bucciol & Zarri 2017, *JBEE* 68:1-12 (HRS) | older US adults, bivariate probit | agreeableness, anxiety, cynical hostility related to risky-asset ownership; Big Five effects largely absorbed by anxiety (as noted by Jiang et al. p. 3) |
| Oehler, Wendt, Wedlich & Horn 2018, *JBF* 19(1):30-48 | experimental asset market | more extraverted pay higher prices / buy more when overpriced; more neurotic hold **fewer risky assets**; much of effect loads on gender |
| Highhouse, Wang & Zhang 2022, *J. Research in Personality* (meta-analysis, k = 133, N = 69,125) | risk propensity vs FFM | strongest ρ = **.30 (Openness)**; FFM jointly explains **22%** of variance in risk propensity; risk propensity "largely independent" of FFM |
| Jiang, Peng & Yan 2024 (Sec. 1) | AAII, HILDA, GSOEP | N −1.7 to −2.6 pp equity / point; O +0.9 to +1.5 pp; adj. R² ≤ 0.08 |
| **LLM:** Hartley et al. 2025, ACL Findings, pp. 21068-21092, https://aclanthology.org/2025.findings-acl.1085/ (Table 1) | GPT-4o, CPT fit, Big Five level interventions | Openness ↔ gain-risk-taking α ρ = **0.63***, β 0.44**, λ −0.55***; Extraversion α 0.28*, λ −0.46***; Neuroticism α 0.01, β −0.05, λ +0.37***; Conscientiousness α −0.25 (ns), λ −0.30*; Agreeableness λ −0.68***. "Unable to produce risk-seeking behaviours for gains or risk-averse behaviours for losses in an absolute sense"; GPT-4-Turbo shows the opposite Openness sign (ω_α = −0.096 vs +0.039) |
| **LLM:** Kocielnik et al. 2026, "Rethinking Psychometric Evaluation of LLMs", arXiv 2606.12730 (local `references/related_work_2026/2606_12730_Rethinking_Psychometric_Eval.pdf`, Sec. 3.1) | 11 LLMs, 4 tasks incl. risk-taking (CCT) | Big 5 self-reports do **not** predict behaviour: best r_aligned +0.06 to +0.07, every 95% CI crosses zero; 3/88 cells p < .05 (2 in the wrong direction); CCT–Neuroticism r = +0.02 [−0.10, +0.15]; TPB r = +0.40 by contrast |

Summary: directions are stable (Openness ↑ risk, Neuroticism ↓ risk, Extraversion ↑ trading/short-termism), magnitudes are small (single-digit pp on allocation; ρ ≈ .3 on risk propensity), and in LLMs the trait-behaviour link is weak or sign-unstable. This justifies mapping personas to **ordinal risk categories with bands**, not to point targets, and validating the categories behaviourally before scoring.

---

## 5. Recommendation

### 5(a) Derive, stipulate, or replace?

**Stipulate bands anchored to practitioner target-risk conventions; report the JFE spread as a sensitivity; add a revealed-preference / input-sensitivity track.** Do not derive from JFE (Sec. 1.3-1.4: spread 5-12 pp, adj. R² ≤ 0.08, MBTI lacks Neuroticism, INTJ≈ENTJ under JFE). Do not claim Markowitz grounding for 1.0 (Sec. 2: no finite γ yields 0% risky).

Proposed target table (environment has cash vs one risky asset; "cash" = all non-equity):

| Persona | Risk category | Cash band (pass zone) | Point C_ideal (for MAS) | Justification | Sources |
|---|---|---|---|---|---|
| ISFJ / O1 | Conservative (capital preservation with some market exposure) | **0.70-0.90** | **0.80** | Conservative = 15-30% equity (Morningstar), 20% (Fidelity Conservative, Vanguard Income, Morningstar Conservative TR); Merton γ = 8-10 → 15-25%; prompt names index funds/bonds/sector leaders; Betterment uses 0% stocks only for fully-liquidated short goals | Morningstar Apr-2025 pp. 18-19; Fidelity methodology PDF; Vanguard LifeStrategy; Betterment methodology; Merton table |
| INTJ | Balanced / moderate | **0.40-0.60** | **0.50** (unchanged) | Balanced = 50/50-60/40 (Fidelity Balanced 50% stock; Vanguard Moderate Growth 60/40; Morningstar Moderate 50-70%); Merton γ = 3-4 | as above |
| ENTJ / O2 | Aggressive / growth | **0.00-0.20** | **0.10** (0.20 acceptable as upper edge) | Aggressive = ≥ 85% equity (Morningstar, Fidelity Aggressive Growth 85, Most Aggressive 100; Vanguard Growth 80/20; Betterment 90%); Merton γ ≤ 2 → ≥ 80% | as above |

Design changes that follow:
1. **Band-MAS**: MAS_band = mean_t max(0, |C_t − centre| − halfwidth). Report both band-MAS and point-MAS; the ordering of models should be robust to the choice (report Spearman ρ of model rankings under 0.8 vs 1.0 for ISFJ as the key sensitivity).
2. **Communicated-target track vs revealed-preference track.** Track A states the band in the prompt (extend the O3 idea: "keep 70-90% in cash"); adherence is then an instruction-following test. Track B gives only the persona text and measures (i) t=0 separability (5c), (ii) drift relative to the agent's own day-1 allocation ("self-anchored MAS" = mean_t |C_t − C_1|), and (iii) Ross & Lo's input-sensitivity criterion: fit a surrogate C_t ~ persona + market features + seed and report the persona directive's share of predictive weight (and R²); mandate salience decay = persona share falling over t while noise share rises. This replaces "distance to a stipulated point" with "does the directive still carry the decision", which is the criterion Ross & Lo argue is the right one when no ground-truth allocation exists (their Sec. 2: "shifting the criterion from output accuracy to input sensitivity").
3. **JFE sensitivity**: report the fraction of models whose conservative−aggressive cash gap exceeds (a) the JFE spread (≈ 0.07-0.12) and (b) the practitioner spread (≈ 0.60-0.70). A model clearing (a) but not (b) is "directionally persona-consistent"; clearing (b) is "category-consistent".

### 5(b) Should the conservative target be 100% cash?

No. Three reasons with sources: (i) the prompt itself ("prefer Index Funds, Bonds, and sector leaders"; "buy insurance (puts/hedges)") describes an invested, hedged portfolio, not a cash account; (ii) no target-risk convention or suitability framework places a conservative investor at 0% risky — conservative = 15-30% equity (Morningstar), 20% (Fidelity, Vanguard Income, Morningstar Conservative TR), and Betterment reaches 0% stocks only for fully-liquidated short-horizon goals; Vanguard's cash framework shows 100% cash is optimal only for a fully-funded one-year goal; (iii) Markowitz/Merton never yields 0% risky at finite γ. Even SCF respondents who say they will take *no* risk hold substantial risky assets (Schooley & Worden .722 broad measure). **Defensible number: 0.80 (band 0.70-0.90).** If the authors want a pure "capital-preservation" condition, relabel it explicitly (Fidelity's "Short-Term" 100% short-term mix is the only convention that matches) and keep it as an O3-style stated-target arm, not as the Big-Five "conservative" persona.

### 5(c) Validating t=0 separability before scoring drift

Pre-register and run on the flat scenario, every model × persona × ≥ 5 seeds:
1. **Day-1 allocation test**: record C_1 (after the first decision, identical market state). Require ordering cons > bal > aggr with Kruskal-Wallis p < .01 and pairwise Mann-Whitney; report Cliff's δ (target |δ| ≥ 0.47 for each adjacent pair) and the band-hit rate (share of C_1 inside the persona's band; target ≥ 80%).
2. **Persona decodability**: AUC of predicting persona from C_1 alone (and from C_1..C_3); a model whose personas are not decodable at t=0 (AUC < 0.8) has no mandate to decay and must be excluded or flagged — otherwise MSD and "never adopted the persona" are confounded.
3. **Input-sensitivity surrogate at t=0** (Ross & Lo): random forest / ridge C_1 ~ persona dummies + shuffled market features + seed; report persona's normalized importance share and FC; require persona share ≥ 0.5 with R² ≥ 0.5.
4. **Vocabulary ablation**: the O3 numerical-only arm (already in Appendix G) as the ceiling — if narrative personas under-separate relative to O3, separability is a prompt problem, not a model problem.
5. **Spread calibration**: report the observed cons−aggr gap against the JFE (0.07-0.12) and practitioner (0.60-0.70) references (5a-3).
6. Only models passing 1-3 enter the MSD/drift analysis; report pass rates per model family as a headline result (it is itself a persona-realism finding).

---

### Source list (primary)
- Jiang, Peng & Yan 2024, JFE 153:103776, doi:10.1016/j.jfineco.2023.103776 (Tables 1, 3, 5, 7, 8, 9, A1).
- Ross & Lo 2026, arXiv:2604.23837 (Sec. 2, 3.2, Tables 6-9).
- Kocielnik et al. 2026, arXiv:2606.12730 (Sec. 3.1).
- Hartley et al. 2025, ACL Findings 2025.findings-acl.1085 (Tables 1-2).
- McCrae & Costa 1989, J. Personality 57:17-40, doi:10.1111/j.1467-6494.1989.tb00759.x.
- Morningstar Category Classifications US Funds (Apr 2025) pp. 18-19; Morningstar Target Risk Index family.
- Vanguard LifeStrategy fund profiles; Vanguard "A framework for allocating to cash" (2024); Vanguard How America Saves 2025 preview.
- Fidelity Planning & Guidance Center methodology (target asset mixes); Fidelity Asset Manager funds.
- Betterment asset-allocation methodology; Wealthfront investment methodology white paper / Classic portfolio page.
- Fieberg, Hornuf, Meiler & Streich 2025, CESifo WP 11666.
- FINRA Rule 2111; ESMA35-43-3172 (2023) para. 55.
- Damodaran implied ERP (Jan 2025, 4.33%); UBS/DMS Global Investment Returns Yearbook 2025 (4.3% over bills).
- Schooley & Worden 1996, FSR 5(2):87-99; Grable & Lytton 2001, JFCP 12(2):43-53; Wang & Hanna 2006, CIA 52; Gilliam, Chatterjee & Grable 2010, JFCP 21(2):30-43; Jeong 2025, FPR doi:10.1002/cfp2.70007; Federal Reserve SCF 2022 bulletin; Capgemini World Wealth Report 2025.
- Filbeck et al. 2005; Mayfield et al. 2008; Durand et al. 2008, 2013; Nicholson et al. 2005; Brown & Taylor 2014; Conlin et al. 2015; Rustichini et al. 2016; Bucciol & Zarri 2017; Oehler et al. 2018; Highhouse, Wang & Zhang 2022.
