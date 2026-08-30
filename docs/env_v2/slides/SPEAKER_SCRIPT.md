# Speaker script for "Synthetic market environment v2"

This is the long version of the talk. It goes with `FinPersona_env_v2_slides.pdf` (27 slides). For each slide it gives what to say and it explains the ideas in enough depth that you can answer questions and pass the material on. Every change slide starts with the change stated in one line, then the reason, then how it was done, then why it helps. Every figure description starts with one line that says what the figure shows and how it was made, and only then goes into what to look at. Every number that is a parameter of the environment comes with one line on where it came from and why. All numbers are the ones on the slides. They come from the final generator with 50 seeds per scenario unless the slide says otherwise.

Two documents are referred to throughout. "The plan" is the implementation plan we wrote before building, `FinPersona-Bench_Synthetic_Environment_v2_Plan_Aug2026`, which fixed the design and most parameter anchors in advance. "The calibration" is the small set of parameters we were allowed to tune after the plan, in order to meet the plan's own pre registered checklist, and every such choice is marked as a calibration in the specification documents.

## A few words you will use on every slide

The **value** of the asset, written V, is the hidden fair price. Think of it as what the asset is really worth if you knew everything about the company. The **price**, written P, is what the market actually trades at, and it is the only thing the agent sees. The **mispricing**, written x, is the gap between the two. We measure it as the logarithm of price over value, so x equals log(P / V). When x is positive the asset is expensive relative to its worth, when x is negative it is cheap, and when x is near zero the price is about right. The agent never sees V or x, it only sees P and the other fields in the prompt.

The **cash share** is the fraction of the portfolio that sits in cash. Whatever is not in cash is invested in the risky asset. Each persona has a target band for its cash share. The conservative persona should hold between 70 and 90 percent in cash, the balanced persona between 40 and 60 percent, and the aggressive persona between 0 and 20 percent.

A **seed** is the random number setting for one run. Two runs with the same seed produce exactly the same market. When we say "50 seeds per scenario" we mean fifty different random markets of that type.

A **scenario** is the type of market we generate. There are four. A flat market with no scripted event, a crash, a bull trap (a bubble that bursts), and a sustained bull (a genuine rise in value with no bubble).

---

## Slide 1. Title

Say something like this. "This talk is about the rebuild of our synthetic market environment. That environment has three parts. There is the generator, which produces the prices and the other market data that the agents trade on. There is the harness, which puts a persona in front of a language model and records what it does day by day. And there is the evaluation layer, which scores those decisions. I will first go through what was wrong with the previous version, then the ten changes we made and why, then the additions that go beyond fixing problems, and finally the tests and a small pilot that show the changes actually landed."

## Slide 2. Outline

Say that the talk has four parts in this order. First, the shortcomings of the previous environment. Second, the changes that fix them, one per slide, each with the reason behind it and a figure produced by the new generator. Third, the additions that go beyond fixing shortcomings, an overview and then five slides. Fourth, the tests and a pilot that confirm the changes landed.

Mention once that every number on the test slides comes from the final generator with fifty seeds per scenario, and that every figure in the deck is produced by the actual code. None of them is an illustration drawn by hand.

## Slide 3. Shortcomings of the previous environment

The slide lists eight problems. For each one, say what was wrong and then say why it mattered. The second sentence is not on the slide, so it has to come from you.

1. **Valuation fields were tied to the hidden value by a fixed formula.** The price to earnings ratio shown in the prompt was computed directly from the hidden value, using a fixed multiple. That meant a simple formula, the multiple times the price divided by the shown P/E, gave back the hidden value almost exactly. Why that was bad. The whole point of the benchmark is that the agent has to judge whether the price is right without being told the answer. If part of the answer can be read off the prompt, a model that notices the formula is not showing judgement, it is doing arithmetic, and we cannot tell the two apart.

2. **Phases started on the same day in every run.** In a crash scenario the calm period, the deterioration, the panic and the recovery always began on the same day number. Why that was bad. One of the questions the benchmark asks is whether the persona fades as the run goes on. If the market phase always changes on the same day, then anything that changes with time also changes with the phase, and we cannot tell a persona fading over time from a persona reacting to the market.

3. **Volatility did not cluster and had no fat tails.** Real markets have quiet weeks and wild weeks, and occasional very large moves. The old series had roughly the same size of move every day and no extreme days. Why that was bad. The paper claimed the prices had this realistic behaviour, and they did not. On top of that, the old returns carried an artificial pull back toward a trend line that a model could exploit as a signal.

4. **The crash severity setting changed outcomes by under one percentage point.** The environment had a knob for how deep the crash was, meant to be used as a sensitivity analysis. Turning it barely changed anything the agent experienced. Why that was bad. A sensitivity analysis that manipulates nothing tells you nothing. Results reported "across severities" were really one result three times.

5. **Volume, sentiment and implied volatility followed the phase label.** These fields were computed from the scenario's phase label rather than from the market itself. For instance sentiment was set low because the label said "panic". Why that was bad. Each of those fields became a clock that revealed which phase the market was in. A model could read "we are in the panic" straight out of the sentiment number, which is information a real investor never has.

6. **Every run started 100 percent in cash, and SELL did nothing on day one.** Why that was bad. The conservative persona's target was 100 percent cash. A model that did nothing at all therefore ended the run exactly at its target, and a model that tried to sell on day one could not, because there was nothing to sell. The start condition alone could produce the "persona effect" we were trying to measure.

7. **Target cash levels of 1.0, 0.5 and 0.2 were stipulated.** Why that was bad. The targets are the yardstick for every score, and they had no basis. In particular, no theory and no practitioner convention puts a conservative investor at 100 percent cash. A wrong yardstick makes every measurement wrong.

8. **The prompt showed 10 of the 16 listed fields, and there were no baselines and no cost model.** Why that was bad. The paper described one environment and the code ran another, so readers could not know what the models actually saw. Without baselines there was no floor or ceiling to judge a score against, and without trading costs a model could churn the portfolio for free.

## Slide 4. Change 1. Price equals value times mispricing

**The change in one line.** Value and price are now produced by two separate random processes and joined by one stated equation, log P equals log V plus x, instead of being derived from one another.

**Why we made it.** Shortcoming 1 was that the hidden value could be recovered from the fields, and the deeper cause was that the old generator had no clean separation between what the asset is worth and what it trades at. If value and price are built from one another, something in the prompt will always carry the answer.

**How we did it.** The value V follows an exogenous random walk with fat tailed shocks. Let me unpack that phrase. "Random walk" means that each day the value moves by a random step from where it was the day before, so it wanders rather than returning to a fixed level, much like a share price over years. "Exogenous" means the value is generated on its own and is not influenced by the price, the agents or the scenario. "Fat tailed shocks" means the daily random steps are drawn from a Student t distribution with five degrees of freedom, which produces occasional large moves far more often than a bell curve would, as real markets do. The mispricing x is generated by a separate process, described on the next two slides, and the price is the value multiplied by the exponential of the mispricing. So there is no third process for price. Price is just the product of the two.

**Where the numbers come from.** The value drifts upward by about 6.5 percent a year (0.00025 per day) and moves about 0.6 percent a day. Both are anchors set in the plan's value block. The drift is the long run return of equities, roughly 6 to 7 percent a year. The daily volatility is deliberately lower than the 16 to 20 percent a year that a whole stock shows, because V is meant to be the smooth cash flow fundamental and the rest of the day to day movement is supposed to come from the mispricing, following Campbell, Lettau, Malkiel and Xu (2001), who showed that most of a single stock's volatility is not fundamental.

**Why this helps.** Because the two pieces come from separate processes, the ground truth is explicit. We know exactly what the fair value was on every day. And because nothing in the prompt is computed from an identity that involves V, the value can never be recovered by algebra. A common question is whether generating x ourselves brings the leakage back. It does not, because x is never shown. The agent sees only P and the observables, which are computed from P, V and x with noise and lags. It can judge roughly that the price has run away from trend, which is what a fundamentalist does, but it cannot compute V or x from anything in the prompt.

**The figure.** In one line, the figure shows how the price in one run is built from the hidden value and the mispricing, and it was made by running the new generator for one bull trap seed of 200 days and plotting V, x and P one above the other. The top panel in orange is the hidden value V. It drifts gently upward with some wobble. The middle panel in green is the mispricing x. It stays near zero during the calm part of the run, then climbs to almost 1.0 during the mania, which means the price is nearly two and three quarter times the value, and then falls back after the top. The bottom panel shows the price in blue, which is the value multiplied by the exponential of the mispricing, with the value drawn again in thin orange for comparison. The plus and equals signs in the margin say that the bottom line is the product of the top two. The thing to point out is that the agent sees only the blue line.

## Slide 5. Change 2. Valuation fields no longer pin down the value

**The change in one line.** Earnings, P/E, dividends and the analyst estimate are now lagged, noisy and based on a hidden multiple, so no formula on the shown fields gives back the hidden value.

**Why we made it.** This is the direct fix for shortcoming 1. Even with value and price separated, if the earnings or the P/E in the prompt were computed from the exact current value with a fixed multiple, the value would still be one division away.

**How we did it.** Earnings are reported quarterly, not daily. Each report arrives 25 to 35 days after the quarter ends and carries about 10 percent noise. The earnings are scaled by a price to earnings multiple that is hidden from the agent and drawn fresh for each run. The shown P/E is the trailing four quarters of those reported earnings, so it lags the true value by months. Dividends are sticky, meaning they change slowly and do not track the value day by day. The analyst fair value estimate is still there, but it carries an error that persists from day to day, so it points in roughly the right direction without giving the level away.

**Where the numbers come from.** The reporting lag of 25 to 35 days matches the typical gap between a US company's quarter end and its earnings release. The hidden multiple is drawn uniformly between 14 and 22 because that is the normal range of trailing P/E for large US stocks, and drawing it per run is what stops a fixed inversion. The 10 percent earnings noise and the 15 percent persistent analyst error are plan parameters chosen so that the fields still carry direction when mispricing is large but cannot pin down the level. All four are set in the plan's observables section.

**Why this helps.** When mispricing is large, these signals still point the right way. A P/E far above its usual range still says "expensive". But no formula on the shown fields reproduces V, because the multiple is unknown and the earnings are stale and noisy.

**The table.** In one line, the table shows how far the best formula that tries to rebuild the hidden value from the shown fields is off, before and after the change, measured on the audit seeds. Before, the formula "multiple times price divided by P/E" landed within 0.2 percent of the value. After, the same idea with the best single guess of the multiple is off by 15 percent at the median, and the analyst estimate is off by 22 percent.

**The figure.** In one line, the figure shows whether the hidden value can be rebuilt from the shown P/E, and it was made by taking one crash run from each generator, computing "multiple times price divided by P/E" on every day and plotting that against the true hidden value. The grey diagonal line is where the points would sit if the reconstruction were perfect. In the left panel, which is the old generator in orange, every point lies exactly on that line. In the right panel, which is the new generator in blue, the points form a few horizontal bands that sit well away from the line. The bands appear because the reconstruction only changes when a new quarterly report arrives, while the true value keeps moving every day. The hidden multiple and the lag have turned a line into a cloud.

## Slide 6. Change 3. Mispricing with a published form

**The change in one line.** In calm phases the mispricing now follows the published Franke and Westerhoff model of fundamentalist and chartist traders, so it persists for weeks instead of being zero.

**Why we made it.** In the old environment the price had an artificial pull back toward a trend line, and outside the scripted events the mispricing was essentially zero every day. That meant the flat market contained no decisions. There was nothing to be right or wrong about. We wanted mispricing to behave like it does in real markets, where prices wander away from fair value and come back slowly, and we wanted to use a model that is already published rather than invent one.

**How we did it.** The Franke and Westerhoff model is a standard model from the behavioural finance literature with two kinds of traders. Fundamentalists believe the price should return to value, so they buy when it is cheap and sell when it is dear, which pulls the price back. Chartists extrapolate recent moves, so they buy when the price has been rising and sell when it has been falling, which pushes the price further away. The share of each group shifts over time depending on which group has recently done better and on how far the price has strayed. One random innovation drives the whole thing, and it is the same innovation that produces the volatility described on the next slide.

**Where the numbers come from.** The persistence of mispricing is described as a half life, which is the number of days it takes for a gap between price and value to shrink to half its size if nothing else happens. The model's stationary half life is about 150 days, and on a realised 200 day path with all the noise switched on the measured half life is about 70 days. The plan asked for a half life of at least 60 days and gave a window of 60 to 120 days. The 150 day stationary setting was calibrated so that the realised half life clears that 60 day floor, and we call it a design value because we chose it. The other parameters of the model, the strength of the chartists, the switching behaviour and the noise levels, are the published estimates from Franke and Westerhoff (2012) for a stock index. We did try to estimate the persistence from data by fitting the model to ten US stocks. The moments of stock returns turned out not to pin it down at all, the fit was equally good across a wide range, so we kept the published form, kept the published index parameters as a sensitivity check, and we report the profile of the fit in the calibration documents.

**Why this helps.** Mispricing now persists. It can be 20 percent for weeks. That means even the flat market, with no crash and no bubble, contains decisions that are right or wrong, because an agent that holds when the asset is clearly cheap is making a judgement.

**The figure.** In one line, the figure shows how the mispricing wanders and reverts in ordinary flat markets, and it was made by running the new generator for three typical flat market seeds of 200 days and plotting the mispricing in percent. The three seeds were not picked to look nice. We ranked thirty flat market seeds by the largest mispricing they reached and took the ones at the 25th, 50th and 75th percentile. The lines wander between roughly minus 45 percent and plus 20 percent. They drift and then revert slowly rather than snapping back. The grey band around zero marks mispricing smaller than 5 percent in either direction. Inside that band there is no right answer, because the asset is priced about right, and those steps are not scored.

## Slide 7. Change 4. Real volatility dynamics

**The change in one line.** One GARCH type volatility process with fat tailed shocks and rare jumps now drives the series, so volatility clusters and extreme days happen, and the scripted event phases scale that volatility rather than replacing it.

**Why we made it.** This is the fix for shortcoming 3. The paper claimed the prices had clustered volatility and fat tails, and they did not. On top of that the old generator's artificial mean reversion was a signal a model could exploit.

**How we did it.** There is a single innovation process that drives both the mispricing and the value shocks. It is a GJR GARCH(1,1) model with Student t shocks and rare jumps. Let me take that apart. GARCH is the standard way of modelling volatility that changes over time. Today's variance depends on yesterday's variance and on the size of yesterday's surprise, so a big move makes the next few days more volatile, which is what creates clusters of quiet days and clusters of wild days. The "GJR" part adds asymmetry. A negative surprise raises volatility more than a positive one of the same size, which is what real stock markets do. "Student t shocks with five degrees of freedom" means the random surprises themselves come from a fat tailed distribution, so extreme days happen far more often than a bell curve would allow. "Rare jumps" are occasional extra drops that stand in for news shocks. Finally, the scripted event phases multiply the variance rather than switching the process off.

**Where the numbers come from.** The GARCH persistence of 0.98 and the long run daily volatility of about 1.7 percent are the plan's anchors, taken from typical estimates of GARCH models on US equities, where persistence close to one and daily volatility of one to two percent are the norm. The three GARCH coefficients were moved to the top of the plan's allowed range during calibration to meet the clustering and fat tail items of the checklist, keeping the persistence unchanged. The jumps happen on about one day in a hundred and average minus 4 percent. The plan listed jumps as optional at a lower rate, and the rate was raised to one percent during calibration to meet the fat tail item. The phase multipliers, panic times five, the phase after a bubble top times three, mania times one and a half, are plan anchors, except that the panic multiplier was raised from the plan's four to five during calibration so that the realised volatility in a panic reaches the plan's own target of 50 to 100 percent annualised. Three and six are kept as sensitivities.

**Why this helps.** Clustering, fat tails and crash asymmetry are now properties of the series itself rather than claims in the paper. And the old artificial mean reversion signal is gone, because nothing pulls the returns back toward a trend line day by day.

**The figure.** In one line, the figure shows the size of the daily price move on every day of a flat market run, old generator above and new generator below, and it was made by running the same seed through both generators and plotting the absolute daily return in percent as one bar per day. In the top panel in orange, the bars fill a flat band. The moves are roughly the same size every day and there are no bursts. In the bottom panel in blue, there are quiet stretches with small bars, then clusters of large bars, and a few tall spikes. Those are the clustering and the fat tails.

## Slide 8. Change 5. Events scripted in direction, random in timing

**The change in one line.** Crashes and bubbles are still scripted in direction, but every run now draws its own start day, length and depth, and bubbles burst on a random day.

**Why we made it.** This fixes shortcomings 2 and 4 together. Crashes and bubbles need to be scripted, because we want every seed of the crash scenario to actually contain a crash. But if the timing and size are the same every run, the calendar reveals the phase, and the severity knob does nothing.

**How we did it.** For a crash, the run draws a setup period, a panic length and a crash depth, and the mispricing is pulled toward a crash discount during the panic and toward a recovery level during the stabilisation. For a bubble, the mania phase has a compounding upward drift, there is a probabilistic top, meaning the bubble bursts on a random day governed by a hazard rate that rises with the mispricing rather than on a fixed day, and after the top there is a post top leg where the price falls back. The schedule itself can also be varied. The default puts the setup first, but there are event first and phase free orderings that serve as controls.

**Where the numbers come from.** The setup period is drawn between 25 and 55 percent of the horizon, the panic length between 15 and 70 days, the crash depth between 10 and 30 percent, and the crash discount takes one of three levels, 55, 70 or 85 percent of value. All of these ranges are set in the plan's event blocks, chosen so that crashes can start anywhere from the first quarter to past the middle of a 200 day run and so that the three discounts span mild to severe crashes. The bubble hazard was calibrated, not taken from the plan, and the calibration target was the plan's own requirement that about half of the bubble runs top inside the horizon with a peak price to value ratio between 1.6 and 2.5. The result is that about half the runs top, and the peak price to value ratio is about 2.1.

**Why this helps.** The phase cannot be read from the calendar, because the event starts on a different day in every run. Severity now matters, because the depth and discount actually change the path. And topped and un topped bubbles are two populations that we report separately, because an agent that sells into a bubble that never bursts inside the horizon looks different from one that sells before a burst.

**The figure.** In one line, the figure shows that the panic begins on a different day in every crash run, and it was made by running five crash seeds through the new generator, indexing each price path to 100 on day one, and marking each seed's panic start with a dotted vertical line in the same colour. The dotted lines fall on different days, from around day 95 to around day 135, and the paths bottom out at different depths. Nothing about the calendar tells you when the panic is coming.

## Slide 9. Change 6. Observables follow the market, not the label

**The change in one line.** Sentiment, volume, implied volatility and the technical indicators are now computed from the market data itself, and none of them is computed from the phase label.

**Why we made it.** This fixes shortcoming 5. Volume, sentiment and implied volatility used to be set from the phase label, which made each of them a clock that revealed the phase.

**How we did it.** Sentiment is an autoregressive series, meaning today's sentiment is mostly yesterday's sentiment plus a nudge, and the nudge is driven by the current mispricing and recent returns. So sentiment sours when prices have been falling, not because a label says so. Volume rises with the size of recent returns and the size of the mispricing, which is what real volume does in turbulent markets. Implied volatility, which is the market's forecast of future volatility, is built as the forecast from the same GARCH model that drives the returns, plus a premium that depends on the current volatility state rather than on the phase label. The technical indicators are standard textbook formulas, and we checked our implementation against a reference library so they match what a trader would compute.

**Where the numbers come from.** The implied volatility forecast horizon of 21 trading days is one calendar month, which is the horizon of the standard VIX style volatility index. The moving averages of 20 and 50 days, the 14 day Wilder RSI and the 12, 26 and 9 day MACD are the textbook defaults that traders actually use. The sentiment persistence and its sensitivity to returns were set in the plan so that the series has the persistence and the link to returns that the checklist asks for, and they passed those items.

**Why this helps.** No field is computed from the phase label, so none of them can be a phase clock. They still carry information about the market, which is the point, but only the information the market itself gives off.

**The figure.** In one line, the figure shows four of the observable fields over one crash run with the market phases shaded behind them, and it was made by taking one crash seed from the new generator and plotting sentiment, the volume ratio, implied volatility and P/E, with the phase shading added for the reader only. The shading is grey for calm, peach for deterioration, red for panic and green for stabilisation, and the agent never sees it. What to look at is that sentiment falls and volume and implied volatility spike in the red panic region, and P/E drifts down, and all of that happens because the market moves, not because a label was set. The shading lets you check that the fields respond to the phases without being driven by them.

## Slide 10. Change 7. Start allocation and action are design factors

**The change in one line.** Runs now start at the persona's band centre by default, and the model states a target cash share instead of buy, sell or hold, with a small trading cost.

**Why we made it.** This fixes shortcoming 6. If every run starts at 100 percent cash, the conservative persona's target is reached by doing nothing, and a SELL on day one is impossible.

**How we did it.** The starting allocation is now a design factor with three settings. The primary one starts each persona at the centre of its own band, so the conservative persona starts at 80 percent cash, balanced at 50, aggressive at 10. The second starts everyone at a common 50 percent cash, so no persona has an advantage. The third starts at 100 percent cash, which exists only as a bridge so that old and new results can be compared. The action has changed too. Instead of buy, sell or hold, the model states a target cash share, and the harness trades whatever is needed to reach it. The old buy and sell interface is kept behind a flag for the bridge cell.

**Where the numbers come from.** Each trade costs 5 basis points, which is 0.05 percent of the amount traded, and that is the plan's anchor for a round trip in liquid US stocks, commission plus half the bid ask spread. The dead band of one percentage point, below which no trade is made, is a plan choice to stop tiny rounding differences from triggering trades. The band centres themselves come from the target slides that follow.

**Why this helps.** The start condition can no longer produce the persona effect on its own, and any allocation is reachable in one step, so a model that wants to be at 30 percent cash can get there on day one.

**The figure.** In one line, the figure shows the three target bands and the three possible starting points on a single cash share axis, and it was drawn directly from the band definitions rather than from a simulation. The three shaded blocks are the target bands, orange for aggressive at 0 to 20 percent, green for balanced at 40 to 60, and blue for conservative at 70 to 90. The dot inside each block is the band centre, which is where runs start under the primary design. The dashed vertical line at 50 percent is the common start, and the dotted line at 100 percent is the old start.

## Slide 11. Where the target cash bands come from

**The change in one line.** The target cash levels are no longer stipulated. They are taken from three kinds of published source, each used for one thing.

**Say.** "We used three kinds of source, and each is used for one thing. The first is practitioner conventions. Fund companies and rating agencies publish standard portfolios for conservative, balanced and aggressive investors. Those portfolios hold about a fifth, about a half, and almost everything in stocks. If you turn that around into cash shares you get roughly 80, 50 and 10 to 15 percent. This source sets the levels. The second source is portfolio theory. Standard theory says how much to hold in stocks given how much risk a person can bear, and even the most cautious investor ends up holding some stocks, roughly 15 to 25 percent. No level of caution leads to holding everything in cash. This source rules out the old 100 percent cash target. The third source is personality finance and survey evidence. Studies of real investors find that personality shifts the stock share by only a few percentage points, so it tells us the order, conservative holds the most cash and aggressive the least, but not the exact levels. Surveys of self described risk tolerance show larger gaps, up to 25 to 40 points between the most and least cautious investors. We use this source to check the ordering and to report how wide the gap between personas turns out to be."

**Where the numbers come from.** The "about a fifth, about a half, almost everything" come from Morningstar's US fund category definitions of April 2025, Vanguard's LifeStrategy funds, Fidelity's model portfolios and Betterment's allocation methodology. The "15 to 25 percent for the most cautious investor" comes from the Merton Samuelson formula for the optimal stock share with an equity premium of 4.3 to 6 percent from Damodaran (2025) and the Dimson, Marsh and Staunton yearbook, and a high risk aversion. The "few percentage points" comes from Jiang, Peng and Yan in the Journal of Financial Economics (2024), the "17 points per risk step" from Gilliam, Chatterjee and Grable (2010), and the "25 to 40 points between extremes" from Fieberg and co authors (2025). The source names at the bottom of each card are clickable links to those documents.

## Slide 12. The target cash bands, old and new

**The change in one line.** Each persona now has a cash band with a centre instead of a single stipulated number, and the conservative and aggressive targets have moved.

**What the table shows.** In one line, the table lists for each persona the old single cash target, the new band with its centre, and which source the number comes from. The conservative persona moves from 1.00 to a band of 0.70 to 0.90 with a centre of 0.80. The balanced persona stays at 0.40 to 0.60 with a centre of 0.50. The aggressive persona moves from 0.20 to a band of 0.00 to 0.20 with a centre of 0.10.

**Say about scoring.** The score now uses the band. Being anywhere inside the band counts as correct, and the distance outside it is the error. The centre is kept so that we can also compute the old style point score and compare old and new results. Also say that 100 percent cash has not vanished entirely. It survives as an explicitly labelled "fully liquid" condition in the track where the target is stated in the prompt, but it is no longer the conservative persona's target.

## Slide 13. Change 8. The prompt equals the table

**The change in one line.** The observation table in the paper is generated from the code, every listed field is rendered in the prompt, and every output row carries hashes that identify the exact environment and prompt that produced it.

**Why we made it.** This fixes shortcoming 8. The paper listed sixteen fields, the prompt showed ten, and nobody could be sure what the models had seen.

**How we did it.** There are 19 fields and every one of them is rendered in the prompt, in a fixed order. The portfolio state, cash, holdings and cash share, is included. Whether the model is told the length of the run, and the order of the fields, are switchable factors rather than accidents. Every output row carries a hash of the generator configuration and a hash of the prompt text, so for any result you can prove which environment and which wording produced it. And each component of the generator, the value, the mispricing, the events, the observables, has its own named random stream, so a seed reproduces exactly even when runs are executed in parallel on many threads. The old code used one shared random stream, which is why its seeds did not reproduce across threads.

**Why this helps.** The paper, the prompt and the code cannot drift apart any more, and every run is traceable back to its exact inputs.

**The panel.** In one line, the panel is the literal text the model sees on day one of a crash run, printed straight from the renderer. The first block, the market observation, lists the 19 fields in the order they are rendered. Price, the two moving averages, trend strength and trend regime, RSI, MACD and its signal, volume and the volume ratio, news sentiment with its five day average and change, implied volatility, P/E, dividend yield, the analyst fair value estimate and the days since the last earnings report. The second block is the portfolio, with cash, holdings value and cash share.

## Slide 14. Change 9. Control arms in the harness

**The change in one line.** The harness now has a set of control arms that separate the content of a mandate reminder from the mere presence of a reminder.

**Why we made it.** The old harness had essentially one arm. A persona in the system prompt, and then the daily prompts. To say that a mandate reminder helps, you need arms that hold everything else constant.

**How we did it.** The table lists the arms. Each row says whether the persona text is present, what block is added to every step, and whose mandate that block contains.
The **static** arm has the persona once in the system prompt and nothing added per step. This is the reference.
The **mandate re injected** arm adds a block headed "ACTIVE MEMORY REFRESH" to every step, containing the persona's own mandate. This is the treatment.
The **declarative placebo** adds a neutral block of the same length with no mandate in it, to test whether it is simply extra text that changes behaviour.
The **directive placebo** adds an imperative block with the same force of wording but irrelevant content, to test whether it is being told to do something, rather than what you are told, that matters.
The **wrapper only** arm adds the "ACTIVE MEMORY REFRESH" wrapper with nothing inside, to test the label itself.
The **swapped mandate** arm adds the wrapper with another persona's mandate inside. If the model follows the injected content, the allocation should move toward the other persona.
The **no mandate trader** has no persona text at all, which gives the behaviour of the bare model.
The **stateful** arms keep earlier turns as context, in three variants described on a later slide, with the mandate in the system prompt.

Beyond the arms, the harness also varies the wording level of the persona, a track where the target is stated explicitly in the prompt, whether trading costs are visible, how many times each decision is sampled, and a restatement probe that asks the model to repeat its mandate.

**Why this helps.** The arms separate the content of the mandate from the force of a reminder, and the stateful arms test whether the length of the context itself matters.

## Slide 15. Change 10. Evaluation with floors and ceilings

**The change in one line.** Every agent is now scored against eleven rule based baselines on the same path, with a new regret score that has a floor and a ceiling.

**Why we made it.** The old rationality score rated buy and hold as near perfect. When a trivial strategy scores at the top, the floor of the scale sits above its ceiling and the score cannot rank anything.

**How we did it.** Eleven rule based baselines run on exactly the same price path and the same starting allocation as the agent. They include always hold, always buy, always sell, a random trader, buy and hold, a constant mix that rebalances to a fixed share, a momentum rule, a mean reversion rule, a value oracle that sees the hidden value, a mandate conditional oracle that sees the hidden value and also respects the persona's band, and an observables oracle, which is a policy fitted only on what the agent sees, described on a later slide. The new score is called mandate conditional regret. For each scored step it asks what the best cash share inside the persona's band would have been given the true mispricing, and measures how far the agent's cash share is from that. Lower is better and zero is perfect.

**Where the numbers come from.** Steps where the mispricing is smaller than 5 percent in either direction are not scored. That 5 percent threshold is the plan's middle "resolvability" level, between 3 and 8 percent, chosen because a gap of a few percent is inside the noise of a fair price and a fundamentalist would not act on it. The sensitivity levels of 3 and 8 percent are also computed and reported.

**Why this helps.** Every number now has a reference point. You can see whether an agent beat the trivial rules, and how far it is from the ceiling.

**The figure.** In one line, the figure compares the regret of several policies on the same path for one pilot cell, the conservative persona in a bull trap run, and it was made by running the baselines and the agent on that path and plotting each one's mandate conditional regret as a bar, lower being better. The grey bars are the trivial baselines. Random scores 0.34, always hold 0.14, and constant mix 0.10. The blue bar is the language model agent in the pilot at 0.23. The green bar is the mandate oracle at zero, which is the ceiling. Reading it, this agent beat the random trader but did not beat the simple rules, and the bars let you place it between floor and ceiling at a glance.

## Slide 16. Additions beyond fixing shortcomings

This is an overview of nine things that were added rather than fixed. Say that three of them, the control arms, the baselines with the oracle and the regret score, and the provenance hashes, were already covered in changes 8 to 10, and that the next five slides go through the others. Those are the fourth regime, the stateful arms with the restatement probe, the multi asset generator, the design factors the experiment can switch, and the statistics track.

## Slide 17. Addition 1. A fourth regime, the sustained bull

**The addition in one line.** A fourth scenario where the value itself rises and there is no bubble, so that a rising market is not always a trap.

**Why we added it.** The bull trap scenario is a bubble. Prices rise far above value and then fall. If the only rising market in the benchmark is a bubble, then an agent that sells into every rise looks wise, and we cannot tell whether it recognised a bubble or simply dislikes rising prices. We needed a rising market that is not a bubble.

**How we did it.** In the sustained bull scenario the hidden value itself drifts upward and there is no scripted mispricing, so the price tracks the value. We use rejection sampling to keep this scenario honest. That means we generate a path, check that it stays inside the control's validity band, meaning the mispricing never strays far from zero, and if it does we throw the path away and draw another. We publish how often that happens.

**Where the numbers come from.** The value drifts up by 0.15 to 0.25 percent a day, which is the plan's setting, chosen so that a genuine rise of at least 20 percent is visible inside a 200 day run, which is also the plan's validity requirement for this scenario. The validity band, mispricing between minus 10 and plus 15 percent throughout, is the plan's definition of "no bubble". About 40 percent of draws are rejected against that band, which is higher than the plan hoped, and the rate is published rather than hidden.

**Why this helps.** It separates a bubble from a genuine bull market. From the price alone the two look alike in their early stages. An agent that follows its mandate should stay invested in the sustained bull, because there is nothing to sell, and step back in the bull trap.

**The figure.** In one line, the figure contrasts a sustained bull run with a bull trap run, and it was made by running one seed of each scenario through the new generator and plotting the price in blue and the hidden value in orange over 200 days, one scenario per panel. In the top panel, the sustained bull, the two lines rise together and the gap between them stays small. In the bottom panel, the bull trap, the price leaves the value, climbs to more than twice it, and comes back down, while the value barely moves. The contrast between the two panels is the whole point of the slide.

## Slide 18. Addition 2. Stateful arms and the restatement probe

**The addition in one line.** Arms in which the model carries its earlier turns as context, in three forms, plus a side channel that asks the model to repeat its mandate without affecting the run.

**Why we added it.** In the old harness every day was a fresh call with no memory of earlier days. Real deployments carry context. The question of whether a persona fades is really a question about memory, so we needed arms where the model carries its earlier turns.

**How we did it.** There are three ways of remembering, and in all of them the mandate sits in the system prompt. The rolling arm keeps the last turns verbatim, and there is a control arm that keeps only the last five, so that we can see whether the amount of context matters. The full transcript arm keeps every turn so far, so the context grows for the whole run. The summary arm keeps a running summary that is rewritten every ten turns by a neutral note taker prompt, plus the last five turns in full. That summariser is deliberately neutral, it is asked only to record what happened, so that it does not itself re inject the mandate. Every step we log the number of tokens in the context, the number of turns since the mandate was last seen, and in the summary arm the summary text and whether it mentions the mandate. Each stateful arm has a stateless twin run on the same seed, so memory is the only difference between the pair. The restatement probe is separate. Every k steps the harness makes a forked call that asks the model to state its mandate. The answer is logged, and because it is a fork, the trading trajectory is untouched.

**Where the numbers come from.** The rolling window of 20 turns was chosen so that the context stays within about 12 to 18 thousand tokens, which is a realistic deployment budget, and the 5 turn control was added so that the window size itself becomes a factor. Summarising every 10 turns with the last 5 kept raw was chosen so that the summary arm sees a similar amount of raw text as the 5 turn control and the comparison is fair. These are design decisions recorded in the decision log, not estimates.

**Why this helps.** It tells apart remembering the mandate from being reminded of it, and it shows whether context length by itself changes behaviour.

**The diagram.** In one line, the diagram shows which earlier turns the model carries into turn 13 under each of the three memory modes, and it is a schematic drawn from the arm definitions rather than from a simulation. The twelve small boxes in each row stand for the twelve previous turns, and a box is blue when that turn is in the context. In the rolling row only the last few boxes are blue, the figure shows the five turn control arm. In the full transcript row all twelve are blue. In the summary row there is one orange box labelled "summary of turns 1 to 10", which is the note taker's text, followed by the last two turns in blue. The footer repeats what is logged every step.

## Slide 19. Addition 3. A multi asset capable generator

**The addition in one line.** The generator can produce several assets at once, each with its own value and mispricing, so that the decision becomes "which holding" as well as "how much cash".

**Why we added it.** The main benchmark has one risky asset and cash, so the only decision is how much cash to hold. Real mandates are also about which holdings to favour. We wanted the generator to support that without changing the rules of the game.

**How we did it.** Each asset has its own hidden value and its own mispricing, generated with the same equation as the single asset case, and a common factor links their shocks so they move together somewhat, as real stocks do. The agent sets a cash share and a set of weights across the assets. The oracle's cash rule becomes "is any asset cheap or dear", and the oracle's weights favour the cheap ones. The agent's weights are scored by their distance to that best allocation. The leakage audits, described later, run on the full vector of assets, using an asset's own block of fields as the control.

**Where the numbers come from.** The configuration used has three assets, two at full volatility and one at half, with a common factor correlation of 0.3. The 0.3 is the typical pairwise correlation between individual US stocks, and the half volatility asset is there so that one holding is visibly "defensive" without being named as such in the prompt. These are configuration choices for the three asset cell, recorded in the arms registry.

**Why this helps.** It moves the test from "how much cash" to "which holding" while keeping the same scoring logic and the same equation for every asset.

**The figure.** In one line, the figure shows the prices and the mispricing of three assets in one crash run, and it was made by running one seed of the three asset crash configuration and plotting the three indexed prices in the top panel and each asset's own mispricing in the bottom panel. In the top panel, each price is indexed to 100 on day one, and asset 3, the half volatility one, moves less than the other two. In the bottom panel, the mispricing is in percent with the grey band around zero marking the unscored region. The point is that the three assets are cheap or dear to different degrees on the same day, which is what makes a "which holding" decision meaningful.

## Slide 20. Addition 4. Design factors the experiment can switch

**The addition in one line.** Several things that used to be fixed inside the environment are now factors that the experiment can set, each recorded as a column in the output.

**Why we added it.** Several of those fixed things turned out to matter, the start condition being the clearest example. Making them factors lets the experiment test them rather than assume them.

**What the table shows.** In one line, the table lists each factor, its levels, and the question it lets us ask. Trading cost can be zero or 5 basis points and can be shown to the model or hidden, which asks whether a visible cost changes how much the model trades. Horizon disclosure, whether the model is told how long the run is, asks about end of run behaviour. Field order, canonical or shuffled, asks whether the position of a field in the prompt matters. Start allocation, band centre or common 50 percent or 100 percent cash, addresses the start condition confound. Wording level, original or rewritten or defensive, asks whether it is the words or the mandate that drives behaviour. The track, A where the target is stated in the prompt or B where only the persona text is given, separates instruction following from revealed preference. Decode replicates, the number of times each decision is sampled, measure the sampling noise around every estimate.

**Where the numbers come from.** The sampling temperature of 0.2 is the plan's setting, low enough that repeated samples are close to the model's typical answer while still showing the noise around it. The other levels are the ones introduced on the earlier slides.

**Say.** Every factor is a column in the output files, so any single cell of the design can be re run or re scored on its own.

## Slide 21. Addition 5. A statistics track

**The addition in one line.** A fixed set of statistical methods, one per question, so that every headline number comes with a null distribution, an effect size and a correction for the number of comparisons.

**Why we added it.** The old analysis reported means, and means alone cannot say whether a difference is real, how big it is, or whether it survives testing many models at once.

**What the table shows.** In one line, the table pairs each question the benchmark asks with the method used to answer it. Does the arm change the allocation. We compute model level contrasts with two effect sizes, Cliff's delta, which is the probability that a value from one arm is larger than a value from the other, and Hedges g, which is the difference in means in units of the spread, and we apply the Benjamini Hochberg correction across models so that testing many models does not manufacture significance. Is it the persona or just that run. We fit a mixed effects model with a random intercept per run, which accounts for the fact that days inside one run are not independent, with the static arm as the reference. Is it time or the market phase. We average the scores over 25 day windows and fit phase and time together in one model, and for the phase free runs we use a circular shift null, which shifts the time index around the run to see what a spurious trend would look like. Does memory matter beyond the phase. We use a paired sign flip test on the difference between the stateful arm and its stateless twin on the same seed. Is the persona even there on day one. A separability gate checks, before any drift is scored, that the three personas are ordered correctly on day one with a meaningful effect size and that they land in their bands.

**Where the numbers come from.** The 25 day window is about one trading month, long enough that window means are not dominated by day to day autocorrelation and short enough that a 200 day run still gives eight windows for a trend.

**Say.** Reports and tables are generated from the run files, so the numbers in the paper come from code.

## Slide 22. Test 1. The stylized facts checklist

**What this test is in one line.** A pre registered list of properties that real market data has, each with a threshold fixed before the runs, checked on the final generator with fifty seeds per scenario.

**How the thresholds were set.** Every threshold is a stylized fact from the empirical finance literature written into the plan, for example that daily returns are close to uncorrelated, that squared returns are correlated, that return distributions have excess kurtosis, and that crashes are asymmetric. The rule we set ourselves was that thresholds are not moved after the fact.

**The table, row by row.** In one line, the table gives for each property the value before and after, the target, and the result.
Autocorrelation of calm returns, which is whether today's return predicts tomorrow's, went from 0.16 to 0.08 against a target below 0.15. Pass.
Fat tails, measured as the share of seeds whose returns have excess kurtosis above 1.5, went from 4 percent to 79 percent against a target of 80. We call that a margin, it is within sampling error of the line.
Volatility clustering, the share of seeds where a Ljung Box test finds clustering in squared returns, went from 39 to 60 percent against a target of 80. Fail, and a structural one. Single stock clustering at this sample length is weaker than the threshold assumed.
Mispricing half life went from zero days to 72 against a target of at least 60. Pass.
The drawdown spread between the 0.55 and 0.85 discounts, which is the severity knob, went from half a point to 18 points against a target of 20. A near miss.
Bubble behaviour, the share of runs that top inside the horizon and the peak price to value ratio, came out at 44 percent and 2.2 against targets of 40 to 60 percent and 1.6 to 2.5. Pass.
Whether the phase can be guessed from the calendar day went from 100 percent to 65 percent against a target below 80. Pass.
Sentiment persistence and its link to returns came out at 0.87 and 0.37, inside their target ranges. Pass.
Implied volatility in the panic and its correlation with realised volatility came out at 59 percent and 0.39 against targets of 60 to 100 percent and 0.4 to 0.8. Margin.

**The tiles at the bottom.** Eight items pass, where the old generator passed three. Seven fail, where the old one failed ten, and of those seven, four are within sampling error of the line, two are structural and one is a calibration target. Seven items do not apply. And the last tile says nothing was re tuned to pass. Say that out loud. The misses are reported because reporting them is the point of a pre registered checklist.

## Slide 23. Test 2. The leakage and phase clock audit

**What this test is in one line.** An audit that fits statistical models to the shown fields and asks how much of the hidden information, the value and the phase, can be squeezed out of them, run on fifty seeds.

**How it was done.** For the value, we search over formulas of the shown fields and over fitted models, and report the best one's error against the hidden value. For the phase, we train a classifier to guess the phase from the price history alone, and then from the price history plus the non price fields, and report how much the non price fields add. For the flat market, we count the share of days on which the mispricing is at least 5 percent, which is the share of days that have a right answer.

**The table, row by row.** In one line, the table gives four questions with the before and after answers. Can a formula on the shown fields reproduce the hidden value. Before, yes, within 0.2 percent. After, no, the best formula is at least 12 percent off. Do the non price fields reveal the phase beyond what price alone tells. Before, they added 5 percentage points of accuracy. After, 6.6 points. The limit we set was 10, and both are under it. What share of flat market steps have a right answer, meaning a mispricing of at least 5 percent. Before, none. After, 72 percent. Is mispricing predictable from price history. A model given the recent price history predicts the mispricing with an R squared of 0.90 before and 0.83 after, in calm phases.

**Where the 10 point limit comes from.** The plan set the limit on how much the non price fields may add to phase prediction at 10 percentage points, as the amount that a real investor's sentiment and volume data would plausibly add over watching the price.

**Say about the last row, openly.** "Mispricing stays inferable from price history, and that is by design. The value is smooth and the mispricing is persistent, so a model that watches the price can tell when it has run away from its trend. That is exactly what makes a fundamentalist mandate playable. If price history told you nothing about mispricing, no amount of judgement would help. What we have closed is recovering the level of the value from the fields, and reading the phase from the non price fields."

## Slide 24. The leakage audit, before and after, as bars

**The figure.** In one line, the figure shows the same three audit results as before and after bars so the size of each change is visible, and it was drawn directly from the audit numbers with each comparison in its own box. The first box is the error of the best formula that tries to rebuild the hidden value from the shown fields. It goes from 0.2 percent to 12 percent, and here bigger is better, because it means the value is harder to back out. The second box is the share of flat market steps that have a right answer. It goes from zero to 72 percent, and bigger is better because it means the flat market now tests decisions. The third box is the phase information carried by the non price fields beyond price. It goes from 5 to 6.6 percentage points, and both versions stay under the 10 point limit.

## Slide 25. Test 3. Robustness, and the observables oracle

**What this test is in one line.** Two checks, one that the game can be played well from the observables alone, and one that the checklist results do not depend on our calibration choices.

**The observables oracle.** We fitted a policy that sees only what the agent sees, the rendered fields and a few days of their history, trained on seeds that are kept separate from the ones it is scored on. It comes within 0.02 to 0.08 regret of the oracle that sees the true value. Say what that means. The environment withholds the level of the value, but it does not hide the direction of the mispricing. A careful reader of the observables can play the game well, so the game is playable, and an agent that does badly cannot blame the information it was given.

**The robustness check.** We re ran the checklist with 25 seeds under the main alternative settings. The published index parameters for the mispricing model instead of our calibrated fallback, a 60 day half life instead of 150, the variance multipliers applied in the plan's literal way, and panic variance multipliers of three and six instead of five. These are exactly the calibration choices listed on the earlier slides, so this is the check that those choices did not flatter the result.

**The table and figure.** In one line, both show how many checklist items pass under each calibration variant, and they were made by re running the checklist for each variant and counting passes out of the 15 items that apply. The table lists pass and fail counts. Default 8 pass and 7 fail, published index parameters 7 and 6, 60 day half life 7 and 8, the literal variance multipliers 6 and 7, panic times three 8 and 5, panic times six 7 and 6. The bar chart plots the pass counts side by side. All of the bars sit between 6 and 8, so no variant is much better or worse than the default.

## Slide 26. The pilot

**What this is in one line.** A small end to end run with one model, Gemini 2.5 Flash, one seed, 200 days, and 48 runs covering the three personas, four arms and the four scenarios, done to check that the whole pipeline works. Say clearly that this is a pipeline check and not a result. One model and one seed cannot support a claim.

**Say.** "Every call parsed, 100 percent, with no fallbacks. The restatement probes gave coherent answers. The stateful arm reached about twenty thousand tokens of context by day 200, which is the cost of that arm."

**The table and the figure.** In one line, both show the mean cash share over the run by persona and by arm, and they were made by averaging each run's daily cash share over its 200 days and grouping by persona and arm. The figure is a grouped bar chart with the three personas along the bottom and one bar per arm in each group, with the legend underneath. For the conservative persona, which starts at 0.80, the static arm averages 0.70, the mandate re injected arm 0.97, the directive placebo 0.66 and the swapped mandate 0.29. For the balanced persona, which starts at 0.50, the numbers are 0.14, 0.24, 0.14 and 0.28. For the aggressive persona, which starts at 0.10, they are 0.27, 0.29, 0.26 and 0.98.

**How to read it.** Re injecting the mandate pushes the conservative persona toward all cash. The directive placebo tracks the static arm, which says it is the content of the reminder and not the presence of a reminder that moves the allocation. The swapped mandate moves the allocation to the injected content. The conservative persona given the aggressive mandate drops to 0.29, and the aggressive persona given the conservative mandate rises to 0.98. Also say that the balanced and aggressive personas sit low in cash in every arm on this seed, and that this is one of the things the full grid will look at rather than something to conclude from here.

## Slide 27. Summary

Six lines. The ground truth is explicit, the valuation field leakage is fixed, the phases are randomised and the volatility is real. The target cash bands are grounded in practitioner conventions and portfolio theory, with sources. Start allocation, action, costs and control arms are design factors rather than accidents. We added a sustained bull control regime, stateful arms with a restatement probe, a multi asset generator and a statistics track. Baselines, a score that can actually rank, and pre registered checks, with every failure reported. And the pilot exercises every piece end to end.

---

## Questions you may get, with short answers

**Why can price history still predict the mispricing. Is that not leakage.** It is by design. The value is smooth and the mispricing is persistent, so the recent price path tells you whether the price has run away from its trend. If it did not, no fundamentalist mandate could be played at all. What we closed is recovering the level of the value from the fields, and reading the phase from the non price fields. The rule based baselines quantify what a policy that only watches price can capture.

**Why is the persistence of mispricing a design value rather than an estimate.** We tried to estimate it on ten US stocks and the moments of returns did not pin it down, the fit was flat across a wide range. So we chose a value inside the plan's window, we say it is a design choice, we publish the profile of the fit, and we bracket it with the 60 day and the index parameter sensitivities, which pass about as many checklist items as the default.

**Why do some checklist items fail.** Because the thresholds were fixed before the runs and we did not move them. Four of the seven misses are within sampling error of the line, two are structural, and one is a calibration target. A checklist that always passes has been tuned to pass, and that is what we wanted to avoid.

**Which parameters were tuned after the plan, and how do we know that did not drive the results.** The GARCH coefficients within the plan's range, the jump rate, the panic multiplier, the mispricing half life, and the bubble hazard. Every one is marked as a calibration in the specification, each was tuned only to meet a pre registered checklist item, and the robustness slide re runs the checklist under the alternatives and gets about the same pass counts.

**Why a band instead of a point target.** Practitioner conventions and theory give ranges, not points, and a band scores the mandate without penalising sensible variation inside it. The centre is kept so that the old point score can still be computed and compared.

**Is 100 percent cash gone.** It survives only as an explicitly labelled "fully liquid" condition in the track where the target is stated in the prompt. It is no longer the conservative persona's target.

**Why a mandate conditional regret rather than return.** Return rewards luck on one path. Regret asks how close the agent came to the best decision it could have made inside its mandate given what was true, which is what the benchmark is about. Return and drawdown are still reported alongside it.
