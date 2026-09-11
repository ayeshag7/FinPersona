# E8.2 — the cost of the context-length levels (per run and per Tier-A-shaped block of 90 runs)

From the pilot's measured growth (n = 3 stateful runs): day-1 context 1,911 provider tokens; 924.3 per retained turn under v2, 826.7 under v2_1 (the replayed block was 10.6% of a turn). The 60,000-token budget holds 80 turns under v2 (chars/4) and 77 under v2_1 (o200k). Output tokens per call: gemini-2.5-flash 106 (e8_5/smoke.json, billed usage, thinking off); gpt-5-mini 534 (e8_5/smoke.json, billed usage, provider-default thinking).

| harness | level | calls / run | input tokens / run | turns at plateau | Flash $ / run | Flash $ / 90 runs | × stateless | GPT-5 mini $ / run | GPT-5 mini $ / 90 runs |
|---|---|---|---|---|---|---|---|---|---|
| v2 | stateless | 200 | 382,200 | 0 | 0.168 | 15.08 | 1.0 | 0.309 | 27.83 |
| v2 | rolling 5 | 200 | 1,292,636 | 5 | 0.441 | 39.66 | 2.6 | 0.537 | 48.32 |
| v2 | rolling 20 | 200 | 3,885,297 | 20 | 1.219 | 109.67 | 7.3 | 1.185 | 106.65 |
| v2 | rolling 50 | 200 | 8,446,718 | 50 | 2.587 | 232.82 | 15.4 | 2.325 | 209.29 |
| v2 | full (60k) | 200 | 12,176,268 | 80 | 3.706 | 333.52 | 22.1 | 3.258 | 293.20 |
| v2 | summary (5 raw) | 220 | 1,363,682 | 5 | 0.467 | 42.06 | 2.8 | 0.576 | 51.84 |
| v2_1 | stateless | 200 | 382,200 | 0 | 0.168 | 15.08 | 1.0 | 0.309 | 27.83 |
| v2_1 | rolling 5 | 200 | 1,196,489 | 5 | 0.412 | 37.07 | 2.5 | 0.513 | 46.16 |
| v2_1 | rolling 20 | 200 | 3,515,354 | 20 | 1.108 | 99.68 | 6.6 | 1.093 | 98.33 |
| v2_1 | rolling 50 | 200 | 7,595,067 | 50 | 2.331 | 209.83 | 13.9 | 2.112 | 190.12 |
| v2_1 | full (60k) | 200 | 10,630,671 | 77 | 3.242 | 291.79 | 19.3 | 2.871 | 258.42 |
| v2_1 | summary (5 raw) | 220 | 1,267,536 | 5 | 0.438 | 39.46 | 2.6 | 0.552 | 49.68 |
