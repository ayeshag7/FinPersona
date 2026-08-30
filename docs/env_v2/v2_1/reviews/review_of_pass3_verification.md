# Review of the third-pass deliverables (verification log, corrected plan v2, alternatives register)

Reviewer: Claude (this session), 27 Aug 2026. I re-ran the new numerical claims that can be checked locally, fetched the three provider pricing pages myself, and read all four deliverables end to end. Nothing was committed; this file is the only one written.

## Verdict

The third pass did what it was asked and did it well. It can be trusted, with the six caveats below (one number I could not reproduce, one cost factor it missed, and four points about how the results should be read). The verification log is the strongest of the three documents: it reads sources instead of recalling them, marks what it could not read, corrects the plan where the plan was wrong, and is explicit about its own limits.

## What I re-ran and confirmed

| Claim in the third pass | My check (fresh seeds) | Outcome |
|---|---|---|
| Long-pilot half-life 141–154 d (five 200,000-step pilots), so the "150 vs 188 d" gap was sampling noise of one short pilot | two 200,000-step pilots (seeds 777, 778): ACF(1)-implied half-life 160 d and 142 d, pull-rate 150 d | confirmed; the E2.5 diagnosis was rightly withdrawn and Phase 0's test is rightly made hard |
| Kalman level-free bound: 0.137 / 0.235 / 0.396 (200-day mean / day 200 / steady state) at sigma_V 0.006, s_x 0.13; 0.097 / 0.161 / 0.231 at 0.010; 0.041 / 0.065 / 0.082 at 0.020 | independent steady-state Kalman filter on the (x_t, x_{t-1}) state: 0.137 / 0.235 / 0.396; 0.097 / 0.161 / 0.231; 0.041 / 0.065 / 0.082 | confirmed to three decimals; the withdrawal of Appendix B's "the bound is high because V is smooth" is correct, and this is the most important correction in the pass (the anchor, not the smoothness, made the audits' price-only R2 high) |
| Oracle target switches per run at theta 0.05: medians 0 / 0 / 1 / 2 (flat / crash / bull / sustained bull) | 20 seeds each: medians 0 / 1 / 1 / 2; share with >= 2 switches 0.25 / 0.45 / 0.30 / 0.55 | substance confirmed (a 200-day run is a one-shot call in flat and bull trap); my crash share is higher than theirs (0.45 vs 0.23–0.27), a seed-set difference that does not change the conclusion |
| Unanchored sustained bull (d_t = 0, one attempt): 8 % of draws inside the v2 x-band, path-mean x -0.11 | 40 draws with LAM_SB = 0: 7 % inside the band, median path-mean x -0.09 | confirmed; D14 is a real decision |
| Removing the jumps' negative mean lowers the flat-path kurtosis share (0.85 -> 0.70 -> 0.60 for current / mean-zero / no jumps) | 40 seeds, scipy excess kurtosis of log returns: 0.70 -> 0.55 -> 0.45 | the drop of 0.15 / 0.25 reproduces; my absolute levels are 0.15 lower, presumably a different kurtosis definition than the checklist's; the coupling between item 4 and checklist item 2 is real |
| GPT-5 mini is $0.25 / $2.00, not the plan's $0.125 / $1.00; Gemini 2.5 Flash $0.30 / $2.50; Sonnet 5 $2 / $10 (1 Sept rise cancelled), Haiku 4.5 $1 / $5, Opus 5 $5 / $25; batch 50 % at all three; Anthropic cache reads 0.1x | fetched the OpenAI, Google and Anthropic pricing pages on 27 Aug 2026: all as stated | confirmed |
| E1.1's "R2 of x_1 on log P_1 < 0.01" fails by design under a random level (0.019 at LogUniform(20, 500)) | analytic: var(log V_1) = (ln 25)^2 / 12 = 0.86, var(x_1) = 0.017–0.027 -> R2 = 0.019–0.030 | confirmed; replacing it with the attacker-based test is right |

## Caveats

1. **Stationary sd(x) of 0.162–0.169 is not reproduced.** My two 200,000-step Gaussian pilots at sd_e 0.017 give sd(x) 0.131 and 0.140, and the calibration report's own pilot gives 0.142. The third pass's 0.165 may come from a different innovation scale or from the full generator (GARCH-t plus jumps) rather than the pilot; it should show the script. The plan v2 already tabulates the bound at both 0.13 and 0.165, so nothing downstream breaks, but the sentence "the engine's stationary sd(x) is 0.165, not 0.13" (closing note item 1, plan 0.2, Appendix C) should be held until it is reproduced.

2. **Anthropic token counts are understated by about 30 %.** The pricing page states that Claude 4.7 and later models (so Sonnet 5 and Opus 5, not Haiku 4.5) use a tokenizer that produces roughly 30 % more tokens for the same text. The pass's per-run costs use chars/4 for every model, so the Sonnet 5 and Opus 5 figures ($1.07 and $2.7 per stateless run, $8.1 stateful, $300 for the Tier B Sonnet block) should be multiplied by about 1.3. The Flash and GPT-5 mini figures are unaffected. Tier B is therefore about $780, not $690.

3. **G3 of the go/no-go is pre-destined to fail at any fitted persistence, and the plan should say what that means.** The pass's own numbers show medians of 0–1 switches per 200-day run at the live 150-day pull, and the persistence literature it read (Summers 1986, Poterba–Summers 1988, Balvers et al. 2000) points to half-lives of months to years, so a FIT persistence will not be shorter. G3 will then fail, and D17 will offer "shorter half-life at matched sd" among the options. That option must not be taken to pass G3: a persistence shortened to make the checkpoint pass is exactly the tuning-to-pass the hard rules forbid. The honest resolutions are the other two (longer horizon as a factor, per-window scoring) or restricting the paper's claim to a one-shot mandate-conflict benchmark. I would write that sentence into 16A now.

4. **D13 cannot be settled until Phase 9, so Phases 1–6 run under a provisional mechanism.** The register names option B (normalise the price) as the provisional default "by exclusion", which is defensible, but the team should approve that explicitly rather than discover it later. The generator-side audits are identical under A, B and C, so nothing has to be re-run if the LLM test later prefers A or C; only the rendering changes.

5. **The effort estimate is the number to plan around.** 72–107 person-days serial, about 60–65 working days on the critical path with the parallelism in Section 16, i.e. roughly three months of one analyst's time before the main grid. The minimal path (Phase 0, start-price fix and level-free audit, FW units, field ablation, regret fix, honest deck) is 15–20 person-days. D16 (which first) is the decision that determines everything else's timing; the register is right not to pick it.

6. **Git housekeeping.** The uncommitted `.gitignore` change in the working tree ignores `docs/env_v2/reviews/`, so the verification log, the closing note, the three v2 reviews, my plan review and this file are invisible to `git status` and will not be committed by a plain `git add`. The corrected plan and the alternatives register are untracked but visible. If the reviews are meant to be kept, remove that ignore line before any commit.

## Smaller points

- FRED being unreachable is almost certainly this machine's network, not the source; CBOE's own VIX file is a fine fallback, as the pass says.
- The register's REG-4 rule is asymmetric (FW must both be accepted and beat AR(1)+GARCH by one bootstrap sd; ties go to the simpler model). That is a reasonable design of a rule and it is stated as such; the team should be aware that it is a thumb on the scale toward AR(1).
- REG-1 option D (render no level at all) is dominated on comparability grounds but is the only option that also removes the field-channel anchor (EPS x k and the analyst estimate reveal V_1 under A–C); Phase 5 has to close that channel under A–C anyway.
- The pass records my suggested answers to D6, D9, D10, D11, D12 as "one reviewer's opinion, not adopted". That is the correct treatment under the hard rules.
- Section 0.4's prompt-size correction (about 10 % more input tokens than the plan assumed) is a useful catch; combined with caveat 2 it means every Anthropic cost line should be redone once.

## What I would do next

Approve the corrected plan as the working document, with the three edits above written into it (hold the 0.165 claim, apply the 1.3x tokenizer factor to Sonnet 5 and Opus 5, add the "G3 must not be passed by shortening persistence" sentence to 16A), fix the `.gitignore` line, then take D1 (data), D13 (provisional B), D16 (full programme or minimal path) and D10 (dividends, needed before Phase 5), and start Phase 0.
