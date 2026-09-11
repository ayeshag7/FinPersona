# The pilot re-scored under the Phase-7 definitions, with the published figures beside

52 runs (Gemini 2.5 Flash, seed 42, T = 200), scored on the **logged columns only**: E7.6 found that none of the pilot's paths regenerates, so no baseline may be simulated on a path the agent never saw and **no normalised value is recomputed**. The published `norm_mcr` figures below are v2-era numbers, kept for the record and not carried forward.

theta = 0.05, half-width 0.1, start-at-target cells.

**The published arm means include the four T = 30 smoke runs** in the ISFJ and ENTJ static and memory cells (n = 4 there against n = 3 elsewhere). `MCR as published` reproduces that construction; `MCR now` is the same statistic on the T = 200 runs only.

| persona | arm | n (published / T200) | MCR as published | MCR published | MCR now (T200) | B (band violation) | D (directional) | MCR per window | oracle switches | share outside band | norm_MCR published (v2-era) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ENTJ | memory | 4 / 3 | 0.2414 | 0.26 | 0.3218 | 0.2403 | 0.0816 | 0.3145 | 0.3 | 0.305 | 0.81 |
| ENTJ | placebo_directive | 3 / 3 | 0.2695 | — | 0.2695 | 0.1986 | 0.0709 | 0.2643 | 0.3 | 0.324 | — |
| ENTJ | stateful_memory | 1 / 1 | 0.3167 | — | 0.3167 | 0.2533 | 0.0633 | 0.3050 | 0.0 | 0.317 | — |
| ENTJ | static | 4 / 3 | 0.2101 | 0.25 | 0.2743 | 0.2049 | 0.0694 | 0.2698 | 0.3 | 0.333 | 0.82 |
| ENTJ | swapped | 3 / 3 | 0.9396 | 0.94 | 0.9396 | 0.7792 | 0.1603 | 0.9385 | 0.3 | 0.998 | 0.02 |
| INTJ | memory | 3 / 3 | 0.3610 | 0.36 | 0.3610 | 0.3266 | 0.0344 | 0.3607 | 0.3 | 0.937 | 0.44 |
| INTJ | placebo_directive | 3 / 3 | 0.3937 | — | 0.3937 | 0.3766 | 0.0171 | 0.3989 | 0.3 | 0.986 | — |
| INTJ | stateful_memory | 1 / 1 | 0.3206 | — | 0.3206 | 0.2944 | 0.0262 | 0.3257 | 0.0 | 0.800 | — |
| INTJ | static | 3 / 3 | 0.3925 | 0.39 | 0.3925 | 0.3756 | 0.0168 | 0.3979 | 0.3 | 0.989 | 0.38 |
| INTJ | swapped | 3 / 3 | 0.4771 | 0.48 | 0.4771 | 0.3993 | 0.0779 | 0.4789 | 0.3 | 0.998 | 0.19 |
| ISFJ | memory | 4 / 3 | 0.2342 | 0.23 | 0.2310 | 0.0764 | 0.1545 | 0.2288 | 0.3 | 0.841 | 0.79 |
| ISFJ | placebo_directive | 3 / 3 | 0.2338 | — | 0.2338 | 0.1827 | 0.0512 | 0.2316 | 0.3 | 0.884 | — |
| ISFJ | stateful_memory | 1 / 1 | 0.2159 | — | 0.2159 | 0.0462 | 0.1697 | 0.2203 | 0.0 | 0.606 | — |
| ISFJ | static | 4 / 3 | 0.2514 | 0.23 | 0.2141 | 0.1586 | 0.0555 | 0.2098 | 0.3 | 0.874 | 0.79 |
| ISFJ | swapped | 3 / 3 | 0.5949 | 0.60 | 0.5949 | 0.5155 | 0.0794 | 0.6031 | 0.3 | 1.000 | 0.23 |

Run by run against `generated/pilot_report_per_run.csv` (the table the published note was written from): 52 runs matched, worst absolute difference in `mcr_0.05` **2.220e-16** — the Phase-7 decomposition is a decomposition of exactly the statistic that was published, not of a different one.

The 4 smoke runs (T = 30) on their own: mean MCR 0.1561, B 0.1010, D 0.0551.


## The half-width sensitivity (E7.7), theta = 0.05

| half-width | mean MCR | mean B | mean D |
|---|---|---|---|
| 0.05 | 0.3933 | 0.3568 | 0.0365 |
| 0.10 | 0.3837 | 0.3102 | 0.0735 |
| 0.15 | 0.3876 | 0.2721 | 0.1155 |

