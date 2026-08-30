# Prompt: find and download the data for the v2.1 programme (plan step E1.0)

## Context

FinPersona-Bench's synthetic market environment is being rebuilt to v2.1 under `docs/env_v2/v2_1/V2_1_IMPROVEMENT_PLAN.md`. Phases 1–6 fit the generator's parameters to real data instead of stipulating them. The ideal sources (CRSP, Compustat, OptionMetrics, I/B/E/S) are not available, so free substitutes are used and their biases (mainly survivorship) are measured and published. Read the plan's Section 3 (data sources and biases), Section 5.2 E1.0 (the shared panel), and `v2_1/reviews/V2_1_PLAN_VERIFICATION_LOG.md` §5 (which sources were reachable on 26 Aug 2026) before starting. Team decision D1 (free data now / wait for WRDS / hybrid; rule in `V2_1_ALTERNATIVES_REGISTER.md` REG-15) depends on what you find.

Your job: **find the best available free data for each need below, download it into `datasets/` at the repo root, and document what you got.** Do not fit any parameter, do not change the generator or the plan.

## What is needed

| # | Need | Coverage | Known candidate (status 26–27 Aug 2026) |
|---|---|---|---|
| 1 | Daily adjusted prices and volume for US large caps; target ≥ 300 historical S&P 500 names, ≥ 100 with full 2000–2024 histories | 2000–2024 (2025 welcome) | Yahoo Finance via `yfinance` (reachable, rate-limited) |
| 2 | Historical S&P 500 constituents with add/remove dates (the universe for #1 and the survivorship count) | 2000–2024 | **not found yet**: the Wikipedia "changes" table was removed in Aug 2025. Ideas: an old revision of that page via the MediaWiki API; public GitHub/Kaggle constituent datasets; iShares IVV holdings history |
| 3 | Quarterly EPS (basic, diluted), dividends per share, period ends and filing dates for the names in #1 | 2009 onward | SEC EDGAR company-facts API and Financial Statement Data Sets (reachable) |
| 4 | Long-run index valuation history (price, earnings, dividends, CAPE), monthly | 1871 onward | Shiller data, current file at shillerdata.com (reachable) |
| 5 | Implied volatility: index (VIX) and single stocks | daily | CBOE history CSVs incl. VXAPL, VXAZN, VXGOG, VXGS, VXIBM (reachable); FRED `VIXCLS` was unreachable |
| 6 | Sentiment: daily news sentiment, weekly survey sentiment, monthly composite | as long as available | SF Fed Daily News Sentiment Index, AAII survey history, Baker–Wurgler index (all reachable) |
| 7 | Industry P/E and payout cross-checks; factor and risk-free series | annual / daily | Damodaran datasets, Kenneth French library (reachable) |
| 8 | A second daily price source to cross-check #1 | any overlap | **not found yet**: Stooq blocks scripts |

The candidates are starting points, not requirements. If one is unreachable, unlicensed, or thin, find another; if you find a better or richer free source for any need (more names, delisted stocks, analyst estimates, earnings-release dates, longer IV history), use it and say why. Record every attempt, including failures.

## What to do

1. Check each source before relying on it: URL, date fetched, licence or terms of use, rate limit, format, date range, row count.
2. Download everything into `datasets/<need>/` in a plain format (CSV or Parquet), with a `README.md` per folder giving the source, date, licence, schema and row counts. Keep whatever code you used under `tools/` so the download can be repeated. Add `datasets/` to `.gitignore`.
3. For #1 and #2 together: list every name in the index at any time in 2000–2024, try to obtain each, and report the share retrieved, the share with a complete history, and why the rest are missing (delisted, acquired, renamed). This feeds REG-15; report the numbers, do not decide.
4. Run basic quality checks on every series (date range, gaps, duplicates, zero or negative prices, daily returns beyond 50 %, zero volume) and report them. Do not clean or fill beyond what the source provides.
5. Write `docs/env_v2/v2_1/E1_0_DATA_REPORT.md`: per need, what was obtained (source, n, range, file) and what was not and why; survivorship numbers; quality summary; licences; open questions for the team, including whether WRDS access exists at the institution (ask, do not assume).

## Rules

- No paid data, no account sign-ups, no credentials. If a source needs a free API key (FRED, Tiingo, EODHD, ...), say so and ask the user before using it.
- Respect terms of use and rate limits; do not work around sites that block scripts.
- Do not change anything under `envs/`, `evaluation/`, `agent/`, `simulation/`, and do not edit the plan, the register, or `docs/env_v2/v2_1/archive/`.
- Git: stay on `main`, no branches; **do not commit, amend, reset, stash or push**. List every file you wrote or changed at the end.
- Report failures as failures, with evidence; never substitute a dataset silently.
