# Independent fact-check of "FinPersona-Bench: Synthetic Environment v2" (envplan_text.txt)

Checked 22 Aug 2026 against primary sources (local PDFs under `references\`, PDFs downloaded from the web and text-extracted with PyMuPDF, repo code). Status codes: **VERIFIED**, **WRONG** (correct value given), **PARTIAL** (number right, attribution/scope needs a fix), **UNVERIFIABLE** (what was tried).

## 1. Jiang, Peng & Yan (JFE 2024) and the derived arithmetic

| Claim in document | Source checked | Status | Note |
|---|---|---|---|
| Table 1a trait means/SD/P10/P90: N 3.39/0.97/2.00/4.75; O 4.48/0.92/3.25/5.65; C 4.89/0.74/3.75/5.75; E 2.59/1.04/1.25/4.00; A 4.86/0.73/3.75/5.75 | `references\related_work_2026\Jiang_Peng_Yan_2024_JFE_Personality_Investment.pdf`, Table 1 Panel (a), p.6 (PDF p.7) | VERIFIED | All 20 numbers match exactly. |
| N = 3,325; median wealth $3.5M; 93% male; mean age 68 | Same PDF, abstract/intro (p.1-2) and Table 1a (Male 0.93, Age 68.23, Wealth 50th pct 3,500) | VERIFIED | |
| Table 7 col.1 (total equity share): A -0.46, C -1.32**, N -1.74***, E -0.33, O 0.94**, adj R2 0.05 | Same PDF, Table 7, p.11 (PDF p.12) | VERIFIED | Obs 2,807; R2 0.08. |
| Table 7 col.2 (retirement): N -2.55***, O 1.50***, C -0.66; col.3 (non-retirement) O 1.15**; col.4 (with belief/risk-aversion controls): C -1.51***, N -1.44***, O 0.95**, adj R2 0.07; "adj R2 0.05 to 0.08" | Same, Table 7 | VERIFIED | Col.3 N -0.80 (n.s.); adj R2 across cols 0.05/0.05/0.07/0.07/0.07/0.08. |
| Table 8 HILDA: N -0.56**, O 0.81*** | Same, Table 8 col.1 (one-person households), p.12 | VERIFIED | C -0.39 (n.s.), A 0.04, E 0.13; obs 5,542. |
| Table 9 GSOEP: C -2.06***, N -1.07**, E -1.16**, O 1.11*** | Same, Table 9 col.1, p.12 | VERIFIED (PARTIAL on framing) | Numbers exact, but the GSOEP dependent variable is stock-market **participation** (0/100), not equity share; the document's "replications in HILDA and GSOEP" should say so. |
| DOI 10.1016/j.jfineco.2023.103776 vs "JFE 2024" | PDF cover sheet and footer ("Journal of Financial Economics 153 (2024) 103776"; doi ...2023.103776; accepted 31 Dec 2023) | VERIFIED | Both are right: volume 153 is 2024, DOI suffix carries 2023. No change needed. |
| "One trait point is about one standard deviation" | Table 1a SDs 0.73-1.04 | VERIFIED (approx.) | |
| Derived spreads: T7c1 -4.1/+0.2/+3.3 -> 7.4 pp; c2 -5.4/+0.1/+5.4 -> 10.8; c3 -3.0/+0.2/+3.0 -> 6.0; c4 -3.6/+0.2/+2.3 -> 5.9; HILDA -1.9/0.0/+1.8 -> 3.7 | Recomputed: O1=(O3,C8,E3,A6,N8), O2=(O8,C6,E8,A2,N2), Bal=5s; linear map 2->P10, 8->P90 on the 1-6 scale; sum coef x (value - mean) | VERIFIED | Recomputed: c1 -4.09/+0.22/+3.31 (7.40); c2 -5.41/+0.09/+5.39 (10.80); c3 -3.01/+0.19/+2.97 (5.99); c4 -3.56/+0.22/+2.34 (5.90); HILDA -1.87/+0.04/+1.79 (3.66). |
| Ceiling "all five traits at P10/P90 in the favourable direction": 9.7 pp (total), 12.4 pp (retirement) | Recomputed sum |coef| x (P90-P10) | PARTIAL (inconsistent definition) | All five traits: c1 = **11.5 pp**, c2 = 12.4 pp. Significant traits only: c1 (C,N,O) = 9.7 pp, c2 (N,O) = 10.6 pp. The document mixes the two definitions (9.7 is sig-only, 12.4 is all-five). Pick one: 11.5/12.4 (all five) or 9.7/10.6 (significant only). |

## 2. Personality instruments and LLM-side claims

| Claim | Source | Status | Note |
|---|---|---|---|
| McCrae & Costa 1989 MBTI-NEO correlations E-I -.74, S-N .72, T-F .44, J-P -.49; no Neuroticism scale | J. Personality 57(1):17-40, doi 10.1111/j.1467-6494.1989.tb00759.x (paywalled); values confirmed from the Wikipedia MBTI article's reproduction of the paper's table (secondary) | VERIFIED (secondary) | Wikipedia table: -0.74, 0.72, 0.44, -0.49; MBTI measures "four of the five" dimensions. Sample 267 men, 201 women. |
| Kocielnik 2026: Big Five self-reports do not predict behaviour; best r about +0.06/+0.07, CIs cross zero; CCT-Neuroticism r +0.02 | `references\related_work_2026\2606_12730_Rethinking_Psychometric_Eval.pdf` (text lines 779-795, 835) | VERIFIED | "best-construct r_aligned across the three volitional tasks ranges +0.06 to +0.07, and every Big 5 95% CI crosses zero"; "CCT-Neuroticism, expected -, actual r_aligned = +0.02, [-0.10, +0.15]". |
| Hartley et al. 2025 (ACL Findings 2025.1085) Table 1: Openness-alpha rho 0.63*** | aclanthology.org/2025.findings-acl.1085.pdf (downloaded, extracted), Tables 1 and 2 | **WRONG** | Openness-alpha Spearman rho = **0.52***** for GPT-4o (0.41*** Claude 3 Sonnet; beta 0.44**, lambda -0.30* for GPT-4o). 0.63 does not appear anywhere in the paper. |
| Hartley: "cannot produce risk-seeking for gains" / moves parameters only inside the risk-neutral regime | Same PDF, Sec. 4.2 | VERIFIED | "we are unable to produce risk-seeking behaviours for gains or risk-averse behaviours for losses in an absolute sense ... personality prompting alone is insufficient ... in GPT-4o"; baseline models are "risk-neutral rational agents". |
| Ross & Lo 2026: risk tolerance 57-88% of predictive weight (p.5); input-sensitivity criterion (Sec. 2); GPT-4o equities 88.2%, cash 82.4% | `references\gap_sweep_aug2026\2604_23837.pdf` | VERIFIED | "self-reported risk tolerance accounting for 57-88% of predictive weight" (sentence runs p.4-5); Sec. 2 intro: "shifting the criterion from output accuracy to input sensitivity"; Appendix A.6 Table 6 (GPT-4o, no web search): Equities Risk tolerance 88.2%, Cash & Savings 82.4%. |

## 3. Franke-Westerhoff and ABM precedents

| Claim | Source | Status | Note |
|---|---|---|---|
| FW 2012 JEDC 36:1193-1211 | EconPapers/ScienceDirect record (vol. 36, issue 8, pp. 1193-1211) | VERIFIED | |
| FW DCA-HPM: phi 0.12, chi 1.50, sigma_f 0.758, sigma_c 2.087, alpha_0 -0.327, alpha_n 1.79, alpha_p 18.43, beta 1, mu 0.01 | uni-bamberg PDF (JEDC_RF_FW_Fin.pdf), Table 1 row "HPM" under DCA; text "normalize ... mu = 0.010 ... beta = 1.00" | VERIFIED | |
| Bootstrap J-test p = 32.6% | Same PDF, Table 2 and Sec. 6 ("bootstrapped a (moment-specific) p-value of 32.6%") | VERIFIED | Paper calls it a moment-specific bootstrap p-value; fine to cite as such. |
| "calibrated on S&P 500 daily 1980-2007" | Same PDF, Sec. 2: "S&P 500 stock market index with T = 6866 daily observations from January 1980 to mid-March 2007" | VERIFIED | |
| "2016 re-estimate with RW fundamental (arXiv 1604.08824): phi 0.121, chi 1.555, sigma_f 0.592, sigma_c 1.917, alpha_0 -0.301, alpha_n 1.990, alpha_p 22.741" | arxiv.org/pdf/1604.08824 Table 1 | VERIFIED (PARTIAL on attribution) | Values exact. But the paper is **Pruna, Polukarov & Jennings (Southampton) 2016**, "A new structural stochastic volatility model ..." (their "FW+" model, GBM fundamental); it is not by Franke & Westerhoff. Table 1 also lists mu_p 0.01, sigma_p 0.157. Same S&P 500 1980-2007 data. Cite as Pruna et al. 2016. |
| Hashimoto et al. 2025 Table 3: kurtosis 7.85 +/- 1.07, |r| ACF(1) 0.19, |r|-volume corr 0.46, 18 JPX stocks; GBM fundamental sigma 1e-4, p0 300 | `references\related_work_2026\2510_12189_ABM_Financial_Market_LLMs.pdf` Table 3, Sec. 4.1 | VERIFIED | Real data row: kappa 7.85 (+/-1.07), gamma(1) 0.19 (+/-0.02), rho 0.46 (+/-0.07); 18 stocks, JPX FLEX-FULL 2015-2021; "p0 = 300.00 ... geometric Brownian motion with zero drift and a volatility of 1.00 x 10^-4". |
| TwinMarket Table 4: kurtosis 7.26 real / 5.24 Twin; leverage 0.14 / 0.11; GARCH alpha+beta 0.95 (real) | arxiv.org/pdf/2502.01506 Table 4 | VERIFIED | Twin alpha+beta 0.89; real data = SSE 50 constituents. |
| Machine Spirits: p_f = 60, bubble threshold 300, leakage Sec. 3.4 | `references\gap_sweep_aug2026\2604_18602.pdf` | VERIFIED | "fundamental price of pf = y/r = 60"; bubble = price above 5x fundamental (300) for >=3 consecutive periods; Sec. 3.4 data leakage. |
| CLQT low tier 2 + 0.5 + 1 bps (App. A Table A1) | `references\related_work_2026\2606_29771_CLQT_Portfolio_Benchmark.pdf` App. A | VERIFIED | low (default): spread 2.0, commission 0.5, slippage 1.0 bps, borrow 30 bps ann., square-root impact. |
| KTD-Fin probe top-1 <= 3.0% vs 0.3% random; joint <= 1.5%; Wilson CIs | `references\related_work_2026\2605_28359_KTD_Fin_Knowing_to_Doing.pdf` (Sec. 4.3, appendix) | VERIFIED | "Top-1 ticker accuracy never exceeds 3.0% against a random baseline of 0.3%, and joint success ... never exceeds 1.5%"; "Cells receive Wilson 95% confidence intervals". |

## 4. Bubbles, sentiment, regimes

| Claim | Source | Status | Note |
|---|---|---|---|
| GSY 2019: 40 run-ups >= 100%, 21 crashed (19 did not) | NBER w23191 PDF (downloaded) | VERIFIED | "We separate the 40 episodes into 21 that crash in the subsequent two years, and 19 that do not". |
| Crash probability 20% / 53% / 80% at 50% / 100% / 150% run-ups | Same | VERIFIED | "the probability of a crash rises from 20% to 53% ... 150% ... rises to 80%" (15 US episodes at 150%). |
| "crashes predicted by rising volatility, turnover and acceleration" | Same, intro and Table 4 discussion | **PARTIAL / WRONG on turnover** | GSY: "turnover does not seem to be a characteristic that meaningfully distinguishes the price run-ups that ultimately crash" (elevated in both). Predictors: increases in volatility, issuance, acceleration, new-firm relative performance, market P/E increases. Replace "turnover" with "issuance" (or say "volume is elevated in all run-ups"). |
| "GSY: fundamentals rise in run-ups" | Same, Table 4 discussion | VERIFIED (loosely) | "all of the episodes that we study have high sales growth"; sales growth does not distinguish crashes. |
| Tetlock 2007: 1 sd pessimism -> -5.5 bp next-day DJIA, reversal days 2-5 | Columbia PDF of the JF paper, Sec. II | **WRONG** | "a one standard deviation increase in pessimism ... next day's Dow Jones returns is **8.1 basis points**"; "the magnitude of the reversal in lags 2 through 5 is **6.8 basis points**". (Negative words: 4.4 bp; Weak words: 6.0 bp; unconditional mean return 5.4 bp.) Update the sentiment spec default (b_pred "5 bp") to 8 bp or cite the range 4.4-8.1. |
| Ang & Timmermann 2012: high-vol regime mu 0.33% sigma 4.89%, low-vol mu 0.90% sigma 2.45%, P 0.977, Q 0.951 (monthly) | NBER w17182 PDF, Table 1 | VERIFIED | mu0 0.3326, sigma0 4.8867, mu1 0.8994, sigma1 2.4462, P 0.9770, Q 0.9512; monthly S&P 500 excess returns 1953:01-2010:12 (regime-switching AR(1)). |
| Pagan & Sossounov 2003: bull about 25 months, bear about 15 months | Paper paywalled (JAE 18:23-46); figures confirmed in a secondary summary (Hsu job-market paper) "duration of bear markets is about 15 months ... around 25 months for bull markets" (US monthly 1835-1997) | VERIFIED (secondary) | |
| Hamilton 1989 p11 about 0.90, p22 about 0.75 | statsmodels replication of Hamilton (1989) GNP model: p[0->0] (recession) 0.7547, p[1->0] 0.0959 => p11 0.904 | VERIFIED (secondary replication) | Matches Hamilton's published 0.9049/0.7550. |
| Ang & Bekaert 2002: bear duration about 6.9 months | RFS 15:1137-1187 PDF (Columbia), p.1149 | VERIFIED | "expected duration of the first regime is 6.9 months, while the expected duration of the second regime is 4.25 years" (Model A with equal means). |

## 5. Industry allocation bands and Merton arithmetic

| Claim | Source | Status | Note |
|---|---|---|---|
| Morningstar (Apr 2025) Conservative Allocation 15-30% equity; Moderate 50-70%; Aggressive > 85% | advisor.morningstar.com ... MorningstarCategoryClassificationUSFunds_April2025.pdf, pp.18-19 | VERIFIED | Wording is "expect volatility similar to a strategic equity exposure between 15% and 30%" etc.; Moderately Conservative 30-50, Moderately Aggressive 70-85. |
| Morningstar Target Risk indexes 20/40/60/80/95 | Morningstar Target Risk Index construction rules / index pages | VERIFIED | |
| Vanguard LifeStrategy Income 20/80; Conservative Growth 40/60; Moderate Growth 60/40; Growth 80/20 | Vanguard fund descriptions (fact sheets / prospectus text) | VERIFIED | |
| Fidelity: Short-Term 100% cash; Conservative 20% stock; Balanced 50%; Aggressive Growth 85%; Most Aggressive 100% | fidelity.com about-fidelity-model-portfolios.pdf, p.4 table | VERIFIED | Conservative 14+6, Balanced 35+15, AG 60+25, MA 70+30. The "only for fully funded short goals" gloss is the document's interpretation, not Fidelity's text. |
| Betterment: 0% stocks only at full liquidation; about 56% at retirement age; 90% for 20+ years | betterment.com/resources/asset-allocation-methodology | VERIFIED | "90% stocks (20+ years)"; "56% stocks (retirement age reached)"; 0% stocks when "time horizon reached" for major-purchase/education goals ("we expect you to fully liquidate"). |
| Wealthfront risk score 8 about 82% equity | wealthfront.com/explore/portfolios/core/classic (example at risk level 8: VTI 45 + VEA 18 + VWO 16 + VIG 3 = 82%) | VERIFIED | |
| Merton table: 4.3%/16%: gamma 2->0.84, 3->0.56, 4->0.42, 10->0.17; 6%/20%: 3->0.50, 10->0.15 | Recomputed (mu-r)/(gamma sigma^2) | VERIFIED | |
| Sec. 4.2 text: "gamma 8-10 gives 15-25%; gamma 3-4 gives 40-60%; gamma <= 2 gives >= 80%" | Recomputed over ERP {4.3, 6}% x sigma {16, 20}% | **WRONG / loose** | gamma 8-10: 11-29%; gamma 3-4: 27-78%; gamma = 2: 54-117% (84% at 4.3/16, 75% at 6/20). "gamma <= 2 gives >= 80%" is false at 6%/20% (75%) and 4.3%/20% (54%). State ">= 54% (about 75-85% at the headline pairs)". The task's own ranges (11-23, 36-78, >= 54) hold only if gamma=4 at 4.3/20 (27%) is excluded; say 27-78 for gamma 3-4. |
| Damodaran implied ERP Jan 2025 4.33% | aswathdamodaran.substack.com Data Update 2 for 2025 | VERIFIED | 8.91% expected return minus 4.58% 10-yr. |

## 6. Survey / HNWI numbers

| Claim | Source | Status | Note |
|---|---|---|---|
| Gilliam, Chatterjee & Grable 2010: +17.41 pp per SCF risk step | JFCP 21(2), Table 4 (Tobit, N = 328) via afcpe.org PDF | VERIFIED | "SCF risk 17.41*** (SE 2.97)" on risky-asset (stock) allocation; sample is university faculty/staff, not SCF households. |
| Fieberg et al. 2025 (CESifo 11666): LLM equity 67%, robo benchmark 59%; gaps 30/42/25/38 pp | ifo.de cesifo1_wp11666.pdf, Sec. 5 | VERIFIED | "equity share is 67% ... robo-advisory portfolios (59% equity ...)"; 30 pp (LLMs high vs low risk tolerance), 42 pp (robo-advisors, Table A14), 25 pp (Bhattacharya et al. 2012 algorithm), 38 pp (Foerster et al. 2017 human advisers). The document's "25 to 42 pp between extremes (Fieberg et al. 2025)" should attribute 25/38 to the cited benchmarks. |
| Schooley & Worden 1996: .982/.941/.858/.722 | FSR 5(2):87-99; journal PDF (openjournals UGA), George Fox repository and ScienceDirect all returned 403/no text | UNVERIFIABLE | Publication confirmed (1989 SCF, risky assets/wealth by risk attitude); the four ratios could not be read. |
| Capgemini HNWI cash 25-26% | Capgemini WWR 2024 (25% early 2024, down from 34%) and WWR 2025 (26%) | VERIFIED | |

## 7. Stylized facts and volatility literature

| Claim | Source | Status | Note |
|---|---|---|---|
| Cont 2001: 11 stylized facts; tail index 2-5 | Quant. Finance 1:223-236; the rice.edu copy is truncated to p.1 + references; list and the quote "tail index which is finite, higher than two and less than five for most data sets studied" confirmed via secondary (Ratliff-Crain et al. 2023 "Revisiting Cont's stylized facts") | VERIFIED (secondary) | 11 facts: absence of autocorrelations, heavy tails, gain/loss asymmetry, aggregational Gaussianity, intermittency, volatility clustering, conditional heavy tails, slow decay of |r| ACF, leverage effect, volume/volatility correlation, asymmetry in time scales. |
| Engle 2001 GARCH(1,1) typical alpha 0.05-0.10, beta 0.85-0.93 | JEP 15(4):157-168, Table 1 (portfolio 50% Nasdaq/30% Dow/20% bonds): ARCH 0.0772, GARCH 0.9046 (secondary excerpt of the paper; Wharton mirror unreachable) | VERIFIED (as a range) | Engle's own digits: 0.0772 / 0.9046, sum 0.982. |
| GJR 1993 gamma 0.10-0.21 | J. Finance 48:1779-1801 PDF (faculty.washington.edu), Table III | **WRONG attribution** | GJR use monthly CRSP 1951-1989 with a positive-shock indicator: g1 (ARCH) 0.07-0.26, asymmetry g2 -0.21 to -0.34 (Models 2-7). The 0.10-0.21 range is not in GJR; it is a generic daily-equity practitioner range. Cite as "typical daily GJR estimates" without the GJR 1993 attribution, or quote GJR's monthly numbers. |
| Hansen & Lunde 2005: for IBM, GARCH(1,1) beaten by leverage models | JAE 20:873-889 abstract | VERIFIED | "for IBM returns the GARCH(1,1) is clearly inferior to models that can accommodate a leverage effect". |

## 8. Market facts

| Claim | Source | Status | Note |
|---|---|---|---|
| S&P bear markets since 1950: 11-14 episodes, mean -30 to -34%, about 338 days | Hartford Funds / Plus500 / schultzcollins summaries of S&P data | VERIFIED (secondary) | 14 (or 11 by stricter definitions); average -30.2%, max -56.8%; average 338 days. |
| 2008: -56.8% over 517 days | Same (Oct 9 2007 - Mar 9 2009) | VERIFIED | |
| 2020: -34% in 23 trading days | Feb 19 - Mar 23 2020 = 33 calendar days = 23 trading days | VERIFIED | Many sources quote 33 (calendar) days; 23 trading days is correct. |
| 1987: S&P -20.4% in one day | Federal Reserve History / LoC | VERIFIED | |
| J.P. Morgan: 40% of Russell 3000 names >= 70% drawdown | JPM "The Agony and the Ecstasy" (2014 edition) | VERIFIED | ">40% of all companies that were ever in the Russell 3000 ... catastrophic stock price loss (70% decline from peak, not recovered)", 1980-2014. |
| Nasdaq 2000-02: -78% | Multiple (5,048 -> 1,139) | VERIFIED | |
| VIX mean 19.6, median 17.7 | FRED VIXCLS 1990-01-02 to 2026-08-20 (downloaded): mean 19.44, median 17.59 (to end-2025: 19.45/17.58) | VERIFIED (approx.) | Document digits are about 0.15 high; say "about 19.5 / 17.6" or state the window. |
| VIX records 80.86 (20 Nov 2008), 82.69 (16 Mar 2020) | macroption.com VIX all-time highs; FRED max 82.69 on 2020-03-16 | VERIFIED | |
| Mar-2020 US equity ADV +129% YoY (about 2.3x) | Cboe March 2020 volume release: Cboe's four US equities exchanges 2.7bn shares/day vs 1.18bn in Mar 2019 (+129%) | PARTIAL | The +129% figure is Cboe's own exchanges, not consolidated US ADV. Either cite it as Cboe, or use a consolidated figure (roughly 2x-2.3x). |
| Nasdaq 2024: S&P 500 bid-ask cost about 4.5 bp | Nasdaq Economic Research "Sampling the S&P 500 to minimize spreads" | VERIFIED | "just over 4.5 basis points" for trading the whole S&P 500. |
| S&P payout about 35% | S&P DJI data via FATFIRE/Digrin summaries: 35.18% recent; long-run 40-50% | VERIFIED (recent) | Say "recent about 35%; long-run 40-50%". |

## 9. Code-level claims (repo)

| Claim | File / lines | Status | Note |
|---|---|---|---|
| Phases 40/30/30% of T | `envs\synthetic_market.py` 58-61 | VERIFIED | |
| Vol recursion 0.7/0.3 |N(0,1)| floor 0.5 on 0.5-dollar noise (flat) | 161-171 | VERIFIED | |
| Flat price = V + N(0,0.5) x phi | 170-171 | VERIFIED | |
| Bull: FOMO cumsum N(1.5,0.5); blow-off cumsum N(0.5,2.5); floor 1.05 x mania entry; phase-2 floor at phase-1 exit; P >= 1 in phase 1 | 83-100 | VERIFIED | Value: phase-1 N(0.001,0.01), plateau N(0,0.002), phase-3 N(-0.0005,0.002). |
| Crash: V = 100 + linspace(0,-12) + N(0,0.5) over p1; panic RW N(-0.5,1.0); V floor 10; P = delta V + N(0,1.5), capped 0.98 V after p1, floor 1.0 | 114-143 | VERIFIED | Stabilisation RW N(0.02,0.5). |
| EPS = V/15 floor 0.01; P/E cap 200; dividend 0.4 EPS/P | 230-246 | VERIFIED | |
| SMA windows min(20, n/5) = 20, min(50, n/2) = 50 for n = 200, aliased to SMA20/SMA60 | 250-261 | VERIFIED | Prompt labels it "SMA20/60". |
| RSI simple rolling mean (Cutler); MACD 12/26 no signal; trend +/-2% | 280-291, 271-272 | VERIFIED | |
| Sentiment iid N(0,0.3); bull phases 2-3 N(0.7,0.2); crash panic N(-0.8,0.2) | 212-219 | VERIFIED | |
| Volume 1e6 (1 + 0.5 U) x linspace multipliers | 191-209 | VERIFIED | |
| IV = 15 x vol_regime | 188 | VERIFIED | |
| Obs includes MACD and dividend_yield; prompt omits them | `get_observation` 309-331 vs `agent\static_agent.py` 112-125 | VERIFIED | Prompt shows price, SMA20/60, RSI, P/E, IV, volume ratio, sentiment, cash, holdings only. |
| Agent sees 'Day-N', never T | `synthetic_market.py` 310; `static_agent.py` 112; `memory_agent.py` 81 | VERIFIED | No horizon in either template. |
| portfolio_tracker: initial_cash 10000, holdings 0, BUY = cash x pct, SELL = holdings x pct, no costs | `simulation\portfolio_tracker.py` 10-84 | VERIFIED | |
| Temperature 0.2 in code (not 0.0) | `agent\static_agent.py` 57 | VERIFIED | |

## Corrections the document must make

1. **Tetlock 2007** (Sec. 3 sentiment row and the b_pred default): -5.5 bp is wrong. Use -8.1 bp next day for 1 sd pessimism, 6.8 bp reversal over days 2-5 (4.4 / 6.0 bp for Negative / Weak words). Set the "Tetlock-sized" default to about -8 bp, or cite the 4.4-8.1 range.
2. **Hartley et al. 2025** (Sec. 4.1 and Sec. 4 sources): Openness-alpha rho is 0.52*** (GPT-4o), 0.41*** (Claude 3 Sonnet), not 0.63***.
3. **GSY 2019 predictors** (Sec. 3 bubble row): turnover does not distinguish crashing from non-crashing run-ups; list increases in volatility, issuance, acceleration (and new-firm outperformance / P/E increases).
4. **JFE ceiling** (Sec. 4.1 table): 9.7 (significant traits only) and 12.4 (all five) use different definitions; report 11.5 / 12.4 (all five) or 9.7 / 10.6 (significant only). Also state that Table 9 (GSOEP) is a participation regression, not an equity-share regression.
5. **Merton sentence** (Sec. 4.2): "gamma <= 2 gives >= 80 percent" is false on the stated grid (54-117%; 75% at 6%/20%). Rewrite as: gamma 8-10 -> 11-29%; gamma 3-4 -> 27-78%; gamma 2 -> 54-117% (about 75-85% at the headline ERP/sigma pairs). The table values are fine.
6. **arXiv 1604.08824** (Sec. 2): attribute the RW-fundamental re-estimate to Pruna, Polukarov & Jennings (2016) ("FW+"), not to Franke & Westerhoff.
7. **GJR 1993** (Sec. 3 volatility row): the "gamma 0.10 to 0.21" range is not from GJR (monthly CRSP: ARCH 0.07-0.26, asymmetry -0.21 to -0.34 with a positive-shock indicator). Either cite GJR's monthly estimates or label the range as typical daily-equity practice without the GJR attribution.
8. **Mar-2020 volume** (Sec. 3 volume row): "+129% YoY" is Cboe's four exchanges (2.7bn vs 1.18bn shares/day); say so or use a consolidated-market figure (about 2x-2.3x).
9. **VIX mean/median**: 19.6 / 17.7 -> about 19.4 / 17.6 (FRED 1990-Aug 2026); state the window.
10. **Fieberg et al. gaps**: 30 pp is LLMs, 42 pp robo-advisers, 25 pp the Bhattacharya et al. (2012) algorithm, 38 pp Foerster et al. (2017) human advisers; the document's "25 to 42 pp (Fieberg et al. 2025)" should attribute these.
11. **Schooley & Worden 1996** ratios (.982/.941/.858/.722): could not be verified (paper inaccessible); keep flagged as unverified or obtain the FSR PDF.
12. Minor: S&P payout "about 35%" is the recent value (long-run 40-50%); Fidelity's "Short-Term = 100% cash only for fully funded short goals" is an interpretation, not Fidelity text; Gilliam et al.'s 17.41 is a Tobit coefficient from N = 328 university employees, not SCF households.

Everything else checked (Jiang Tables 1a/7/8/9 and the 7.4/10.8/6.0/5.9/3.7 pp spreads, FW 2012 parameters and data, McCrae & Costa, Ross & Lo, Ang & Timmermann, Ang & Bekaert, Hamilton, Pagan & Sossounov, Hashimoto, TwinMarket, Morningstar/Vanguard/Fidelity/Betterment/Wealthfront, Capgemini, Cont, Engle, Hansen & Lunde, CLQT, KTD-Fin, Machine Spirits, Kocielnik, the market-crash facts, JPM, Nasdaq, VIX records, Nasdaq 4.5 bp, Damodaran, and all code-level claims) is verified.
