# E1.0 — Shared data panel: what was obtained, what was not

**Plan step.** `V2_1_IMPROVEMENT_PLAN.md` §5.2 E1.0 (shared panel for Phases 1–6), against
the substitutes and biases of §3, and the reachability facts of
`reviews/V2_1_PLAN_VERIFICATION_LOG.md` §5 (checked 26 Aug 2026).

**Run date.** 29 August 2026 — two automated passes plus one manual download (§0.4).
**Operator.** Automated download this session; the AAII file fetched by hand by the user.

**Scope discipline.** Data were downloaded, checked and documented. **No parameter was
fitted, no generator code touched, no plan or register text edited.** Nothing under
`envs/`, `evaluation/`, `agent/`, `simulation/` was modified. Work stayed on `main`; no
commit, branch, amend, reset, stash or push was made.

---

## 0. Headline

**All eight needs are satisfied.** Six were closed by the automated download, two more by
a retry once a network filter lifted, and the last — AAII weekly sentiment — by a person
downloading one file by hand, because the site's `robots.txt` forbids a script from
fetching it.

| # | Need | Outcome |
|---|---|---|
| 1 | Daily prices/volume, historical S&P 500 | **Obtained** — 673 names, 428 full histories; both targets beaten, but see the ticker-reuse defect in §1.3 |
| 2 | Historical constituents with add/remove dates | **Obtained** — 1,094-name universe from three independent sources (the plan recorded this as "not found yet") |
| 3 | Quarterly EPS/DPS, period ends, filing dates | **Obtained** — 819/1,094 names, 799,946 facts |
| 4 | Long-run index valuation (Shiller) | **Obtained** |
| 5 | Implied volatility | **Obtained in full** — 25 CBOE index files including **all five single-stock VIX** (§5) |
| 6 | Sentiment | **Obtained** — daily, weekly and monthly; AAII taken by manual download (§6) |
| 7 | Industry P/E, payout, factors, risk-free | **Obtained** |
| 8 | Second daily price source | **Obtained** — Nasdaq's public API, no key (§8) |

### 0.1 The first pass was blocked by this machine's DNS filter

On the first pass, a long list of finance-data hosts resolved to **`146.112.61.106`** —
the Cisco Umbrella block page of this machine's corporate DNS filter — so every client
failed the TLS handshake against them: `cdn.cboe.com`, `www.cboe.com`, `stooq.com`,
`www.aaii.com`, `api.nasdaq.com`, `www.nasdaqtrader.com`, `api.tiingo.com`, `eodhd.com`,
`data.nasdaq.com`, `finnhub.io`, `api.polygon.io`.

`curl -v https://cdn.cboe.com/...` returned `schannel: SEC_E_UNTRUSTED_ROOT ... The
certificate chain was issued by an authority that is not trusted` against that IP, while
unfiltered hosts negotiated TLS normally against their real addresses — so it was the
filter, not a TLS-interception proxy and not a client fault.

**Nothing was circumvented then, and nothing has been since.**

### 0.2 On the second pass the filter had lifted

Re-checked on request, later the same day: **every one of those hosts now resolves to a
real address.**

```
cdn.cboe.com          104.19.183.30, 104.19.184.30   clear
stooq.com             159.69.202.225, 78.47.47.99    clear
www.aaii.com          45.60.160.53                   clear
api.nasdaq.com        23.15.96.245                   clear
...                                                  (all 11 clear)
```

The retry is what closed needs #5 and #8. Two sources stayed out of reach, but for a
**different and more durable reason** — their own published rules, which no network
change affects:

| source | second-pass result |
|---|---|
| **CBOE** | **Works.** `robots.txt` disallows only `/book/` and `/*market_statistics/volume_reports/`; the `daily_prices` path is permitted. 25 index files taken (§5). |
| **Nasdaq API** | **Works.** Public JSON, no key. Closes need #8 (§8). |
| **Stooq** | **Refused.** Returns a 796-byte JavaScript proof-of-work challenge, and its `robots.txt` reads `User-agent: *` → `Disallow: /` — only Googlebot and Bingbot are allowed. Scripted access is explicitly forbidden. Not taken. |
| **AAII** | **Refused.** The HTML results page returns a JavaScript bot-challenge. The underlying file `/files/surveys/sentiment.xls` *is* served plainly (1,313,792 bytes), **but `robots.txt` has `Disallow: /files/*` for `User-agent: *`.** Not downloaded — see §6 for the legitimate route. |

`fred.stlouisfed.org` was never DNS-filtered; it is **intermittent**. Early requests timed
out (60 s, 0 bytes) on `fredgraph.csv`, `/data/VIXCLS.txt` and the series page, reproducing
the plan's 26 Aug finding; an hour later the same URLs served normally and seven series
were downloaded. Record it as *retry, do not substitute*.

Every retry attempt, including the two refusals and the reason for each, is in
`datasets/_manifests/attempts_retry_blocked.json`.

### 0.3 The last gap closed by hand

AAII's `robots.txt` forbids an automated client from fetching its survey file, and no
network change alters that. The legitimate route is a person: the user downloaded
`https://www.aaii.com/files/surveys/sentiment.xls` in a browser to
`datasets/06_sentiment/sentiment.xls`, and `tools/e1_0_data/ingest_manual.py` parsed,
quality-checked and documented it on the same footing as every automated source —
**2,041 weekly rows, 1987-06-26 → 2026-08-27** (§6.1).

With that, **every need in the E1.0 brief has data**.

### 0.4 What this means for the verification log

`V2_1_PLAN_VERIFICATION_LOG.md` §5 recorded CBOE as reachable and AAII as "readable
without login" on 26 Aug 2026. Both are now better resolved:

* **CBOE — confirmed**, and richer than §5 expected: not five single-stock files but 25
  index histories, including the VIX term structure and SKEW back to 1990.
* **AAII — the §5 note should be amended.** "Readable without login (browser-like fetch;
  plain curl 403)" describes defeating a bot-challenge with a browser-like User-Agent.
  The site's `robots.txt` disallows the data path to automated clients regardless of
  User-Agent, so **a script should not use that route** — the correct route is a manual
  download, which is what was done.
* The intermittent DNS filtering explains the 26-Aug/29-Aug discrepancy without either
  check being wrong.

---

## 1. Need #1 — Daily prices and volume

| item | value |
|---|---|
| Source | Yahoo Finance via `yfinance` 1.6.0 |
| Fetched | 29 Aug 2026 |
| Licence | Yahoo ToS: personal, non-commercial use, no redistribution. `datasets/` is git-ignored. |
| Rate limit | Unpublished; run at 40 symbols/batch, 4 threads, 2 s between batches |
| Requested range | 2000-01-01 → 2026-01-01 |
| Files | `datasets/01_prices/daily/<TICKER>.parquet`, plus `retrieval_log.csv` |

### 1.1 Coverage against the E1.0 targets

| target (plan §5.2) | achieved |
|---|---|
| ≥ 300 historical S&P 500 names | **673** |
| ≥ 100 names with full 2000–2024 histories | **428** |

Of the **1,094** tickers in the index at any time in 2000–2024, **673 (61.5 %)** returned
data and **428 (39.1 %)** cover 2000-01 through 2024-12 without truncation.

### 1.2 Survivorship — the REG-15 numbers

Split by whether the name was still in the index at the end of the window:

| group | n | retrieved | % retrieved | full 2000–2024 history |
|---|---:|---:|---:|---:|
| still in the index at 2024-12-31 | 752 | 589 | **78.3 %** | 416 |
| left the index during 2000–2024 | 342 | 84 | **24.6 %** | 12 |
| **all** | **1,094** | **673** | **61.5 %** | **428** |

**The retrieval rate for names that left the index is under a third of the rate for names
that stayed — and §1.3 shows that even the 24.6 % is mostly illusory: after the ticker-reuse
tests only 16 of the 342 (4.7 %) are genuinely the constituent.** Non-retrieval is concentrated exactly on the bankruptcies and takeovers
Phases 3, 4 and 6 need: Enron (`ENRNQ`), Lehman (`LEH`), WorldCom (`WCOM`), Compaq
(`CPQ`) and AMR (`AAMRQ`) all return "possibly delisted; no price data found".

Per-ticker detail is in `datasets/_manifests/survivorship_accounting.csv`
(`ticker`, `exit_hint`, `retrieved`, `full_history`, `n_rows`, `first`, `last`).

**Reported, not decided.** REG-15's rule needs the survivor-vs-literature gap on the
Phase-3/4/6 parameters, which only exists once those fits are run. This report supplies
the retrieval side only.

### 1.3 A defect the plan did not anticipate: ticker reuse

Yahoo serves whichever company holds a symbol **today**. Where an S&P 500 name was
delisted and its ticker later reassigned, `yfinance` returns the **new** issuer's history
under the old ticker. Verified against Yahoo's own metadata:

| ticker | S&P 500 constituent it should be | what Yahoo actually serves | venue |
|---|---|---|---|
| `CPWR` | Compuware (delisted 2014) | Ocean Thermal Energy Corporation | OTC (`OID`) |
| `COMS` | 3Com (delisted 2010) | COMSovereign Holding Corp. | Pink (`PNK`) |
| `EP` | El Paso Corp (delisted 2012) | Empire Petroleum Corporation | NYSE American |
| `CVG` | Convergys (delisted 2018) | a **mutual fund** share class | `YHD` |
| `FB` | Facebook (renamed META 2022) | ProShares S&P 500 Dynamic Daily Buffer **ETF** | `BTS` |
| `S` | Sears (delisted 2005) | SentinelOne, Inc. | NYSE |
| `LU` | Lucent (delisted 2006) | Lufax Holding Ltd | NYSE |
| `GP` | Georgia-Pacific (delisted 2005) | GreenPower Motor Company | Nasdaq (`NCM`) |

These carry the panel's worst quality readings — `CPWR` shows a **21×** one-day return and
2,846 zero-volume days; `COMS` shows prices above 236,000 from reverse splits.

#### The decisive test: a series that begins after the company left

The first pass screened on Yahoo metadata (`quoteType`, venue, extreme returns, zero
volume) and flagged 42 of 673. **That understated the problem by half.** The need-#8
cross-check (§8) exposed `GP`: an ordinary Nasdaq-listed EQUITY with no metadata anomaly
at all, whose returns simply did not match Nasdaq's — because it is GreenPower Motor, not
Georgia-Pacific.

That suggested a sharper and almost conclusive test, which needs no network access:
**does the series start after the name left the index?** A continuous history of one
company cannot begin months after that company left the S&P 500.

**64 retrieved names start more than 180 days after their index exit** — some by more than
20 years:

| ticker | left index | Yahoo series starts | gap | what the symbol is now |
|---|---|---|---:|---|
| `CHA` | 2000-06 | 2025-04-17 | 9,086 d | Chagee Holdings Limited |
| `SEG` | 2000-11 | 2024-07-30 | 8,672 d | Seaport Entertainment Group |
| `RAL` | 2001-12 | 2025-06-25 | 8,607 d | Ralliant Corporation |
| `TMC` | 2000-06 | 2021-09-10 | 7,771 d | TMC the metals company |
| `S` | 2005-03 | 2021-06-30 | 5,965 d | SentinelOne |
| `GP` | 2005-12 | 2020-08-28 | 5,384 d | GreenPower Motor |
| `LU` | 2006-11 | 2020-10-30 | 5,112 d | Lufax Holding |
| `ASO` | 2006-11 | 2020-10-02 | 5,084 d | Academy Sports and Outdoors |

Only **20 of these 64** were caught by the metadata screen. With the new test the total
flagged rises from 42 to **86 of 673 (12.8 %)**.

`datasets/_manifests/ticker_reuse_screen.csv` now carries five criteria —
`quoteType != EQUITY`, OTC/pink venue, max daily return > 100 %, zero volume on > 25 % of
days, and `starts_<N>d_after_index_exit` — plus a `days_start_after_exit` column and
Yahoo's current `longName`, so a human can adjudicate each case. **Nothing was deleted.**

#### What this does to the survivorship number

| measure of delisted coverage | value |
|---|---|
| names that left the index, 2000–2024 | 342 |
| of those, Yahoo returned *something* | 84 (24.6 %) |
| …that survives the metadata screen | 60 (17.5 %) |
| **…that survives the start-date test too** | **16 (4.7 %)** |

**Genuine coverage of the delisted tail is about 5 %, not 25 %.** The other three quarters
of the "retrieved" delisted names are different companies wearing the same ticker. This is
the sharpest number in this report for REG-15, and it makes the survivorship bias
substantially worse than plan §3 assumed.

### 1.4 Quality checks (`datasets/_manifests/quality_prices.csv`)

Every series in the panel was checked — the 673 price histories, all 25 CBOE indices, the
7 FRED series, the 5 Yahoo volatility indices, Shiller, SF Fed, Baker–Wurgler, and the 640
Nasdaq cross-check histories. **No duplicate dates and no non-positive prices anywhere**
outside what is listed below; the CBOE, FRED and cross-check panels are clean on every
check (`_manifests/quality_other.csv`). The Nasdaq cross-check panel: 640 tickers,
1,426,362 rows, 2016-08-29 → 2025-12-31, 0 duplicates, 0 non-positive closes.

Across the 673 retrieved Yahoo tickers:

| check | result |
|---|---|
| duplicate dates | **0** tickers |
| calendar gaps > 7 days | **0** tickers |
| zero or negative `Close` / `Adj Close` | **0** tickers |
| NaN `Adj Close` | 1 ticker (`CVG`, 3 rows) |
| \|daily return\| > 50 % | 69 tickers, **400** day-observations |
| zero-volume days | 75 tickers, **16,682** day-observations |

The return and volume outliers are heavily concentrated in the reused tickers of §1.3;
the rest are genuine split/crash days. **Nothing was cleaned or filled.**

---

## 2. Need #2 — Historical constituents (the plan's open item, now closed)

The plan and the verification log both record that the Wikipedia "Selected changes to the
list of S&P 500 components" table was removed from the article in Aug 2025, and that a
replacement had to be found **before** E1.0. Three independent sources were obtained.

| # | Source | Licence | Coverage | Fetched |
|---|---|---|---|---|
| A | [`fja05680/sp500`](https://github.com/fja05680/sp500) (917★) | **MIT** | point-in-time components, 1996-01-02 → 2026-06-30, plus `sp500_ticker_start_end.csv` | 29 Aug 2026 |
| B | [`hanshof/sp500_constituents`](https://github.com/hanshof/sp500_constituents) | **MIT** | daily point-in-time components, 1996-01-02 → 2025-08-23 | 29 Aug 2026 |
| C | Wikipedia **revision 1295035732** (2025-06-11) via the MediaWiki API | **CC BY-SA 4.0** | the removed changes table: **362** add/remove rows, 1994-09-30 → 2025-05-19; plus the components table **with CIKs** | 29 Aug 2026 |

Source C is the plan's own suggested route ("an old revision of that page via the
MediaWiki API") and it works: `?oldid=1295035732&action=raw` still serves the wikitext.
Its CIK column also feeds need #3.

**Derived universe.** `datasets/02_constituents/universe_2000_2024.csv` — **1,094**
distinct tickers in the index at any time between 2000-01-01 and 2024-12-31, each with
`first_seen`, `last_seen`, an `exit_hint` (`YYYY-MM` when it left), and which sources
contain it.

**A parsing trap, documented.** fja05680 appends a `-YYYYMM` exit suffix to reused or
delisted symbols (`AAMRQ-201312`). Compared naively against hanshof's bare symbols the
two sources appear to disagree badly (274/500 overlap in 2000). After stripping the
suffix they agree closely:

| date | Jaccard(A, B) |
|---|---|
| 2000-01-03 | 0.943 |
| 2005-06-30 | 0.918 |
| 2010-06-30 | 0.884 |
| 2015-06-30 | 0.924 |
| 2020-06-30 | 0.984 |
| 2024-12-31 | 0.996 |

The suffix is kept as `exit_hint` — it is evidence for the survivorship accounting, so it
was not discarded.

**Source C is verified but incomplete — use A and B for the universe.** Spot-checks
against known index events all pass: TSLA added 2020-12-21 (replacing AIV), FB added
2013-12-23, LEH removed 2008-09-16 ("Lehman Brothers filed for bankruptcy"), COIN added
2025-05-19 (replacing DFS). But the table holds only **362** rows in total and **350** in
2000–2024, against the ~20–25 index changes a year the index actually makes — it is a
*"Selected* changes" table and always was. Enron's removal, for instance, is absent. It is
therefore used as a **supplement and cross-check**, and as the source of company names for
the EDGAR CIK lookup (§3); the universe itself comes from the point-in-time reconstructions
A and B.

**Caveat to carry into the paper.** None of these is S&P Dow Jones Indices' licensed
membership file. They are community reconstructions, largely from Wikipedia history, and
inherit its errors. Their mutual agreement bounds, but does not eliminate, that risk.

---

## 3. Need #3 — Quarterly EPS, DPS, period ends and filing dates

| item | value |
|---|---|
| Source | SEC EDGAR XBRL **company facts** API, `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` |
| Licence | US government work, public domain |
| Fair access | SEC asks for a declared User-Agent and ≤ 10 req/s; this run declared one and held ≈ 3 req/s |
| Files | `datasets/03_fundamentals/by_ticker/<TICKER>.parquet` + `retrieval_log.csv` |

**Why company-facts and not the frames API.** The frames endpoint
(`/api/xbrl/frames/...`) returns all filers for one period in a single call and is much
cheaper, but its records carry only `accn, cik, entityName, loc, start, end, val` — **no
`filed` date and no `form`**. E1.0 asks for filing dates, so the per-CIK company-facts
route was used instead. The ~3.8 MB JSON per filer is streamed and discarded; only the
wanted concepts are stored.

**Concepts kept** (`us-gaap`): `EarningsPerShareBasic`, `EarningsPerShareDiluted`,
`CommonStockDividendsPerShareDeclared`, `CommonStockDividendsPerShareCashPaid`, and —
free in the same payload — `NetIncomeLoss` and `StockholdersEquity`, which support the
book-to-market and profitability references in plan §5.1 (Vuolteenaho 2002;
Cohen–Polk–Vuolteenaho 2003).

**Ticker → CIK.** `https://www.sec.gov/files/company_tickers.json` returned **HTTP 403
"Request Rate Threshold Exceeded"** on every attempt with three different User-Agents,
while `ticker.txt` on the same host served normally — a path-specific throttle, recorded
and worked around only by using the other published file. Resolution used, in order:

1. `https://www.sec.gov/include/ticker.txt` — 12,084 pairs (current registrants).
2. The CIK column of the archived Wikipedia table — 17 more.
3. `https://www.sec.gov/Archives/edgar/cik-lookup-data.txt` (40 MB, SEC's **historical**
   company-name → CIK list), matched on an exactly-normalised company name taken from the
   Wikipedia changes table — **155 of 184** otherwise-unmatched delisted names resolved.

Step 3 is the reason fundamentals coverage of delisted names is far better than price
coverage: CIK match rose from ~58 % to **870/1,094 (79.5 %)**. `cik_source` is recorded
per row so every match is auditable.

**Results.** See §9.

**Limitations.** XBRL coverage starts ≈ 2009, so earlier quarters do not exist here.
`filed` is the filing date, not the 8-K earnings-announcement date (plan §3 notes the gap
is up to two weeks); Item 2.02 8-K dates were not collected. Tag usage varies by filer and
was not harmonised.

---

## 4. Need #4 — Long-run index valuation (Shiller)

| item | value |
|---|---|
| Source | Robert J. Shiller, "Online Data", **shillerdata.com** → `ie_data.xls` |
| Licence | Public academic dataset, free with attribution |
| Rows | **1,868** monthly |
| Range | **1871.01 → 2026.08** |
| Files | `ie_data.xls` (as served), `shiller_monthly.csv` (sheet `Data`) |

Columns include `P`, `D`, `E`, `CPI`, `Rate GS10`, the real series and CAPE — the
price, earnings, dividends and CAPE the need asks for.

**Schema trap.** `Date` is a **fractional year**, not a date: `1871.01` = Jan 1871,
`2026.10` = Oct 2026. Parsing it as a date string silently collapses the column (it
produced 1,712 spurious duplicates in the first quality pass); the checker now parses it
as `YYYY.MM`.

The plan's correction is confirmed: the shillerdata.com file is current to 2026.08, where
the Yale copy ends 2023.09. `datahub_sp500_shiller_crosscheck.csv`
(github.com/datasets/s-and-p-500, PDDL) is an independent transcription of the **same**
series — it checks the parse, not the measurement.

---

## 5. Need #5 — Implied volatility (**obtained in full**)

Closed on the second pass. `datasets/05_implied_vol/cboe/` holds **25 CBOE index
histories**, as served plus a parsed Parquet each.

| item | value |
|---|---|
| Source | CBOE, `https://cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv` |
| Fetched | 29 Aug 2026 (second pass) |
| Licence | Free daily index CSVs for reference/research; CBOE permits internal research use, not redistribution. Files stay under the git-ignored `datasets/` tree. |
| `robots.txt` | disallows only `/book/` and `/*market_statistics/volume_reports/` — this path is permitted |
| Schema | `DATE` (parsed from `MM/DD/YYYY`), `OPEN`, `HIGH`, `LOW`, `CLOSE` |

### 5.1 The five single-stock VIX indices — what the plan actually asked for

| index | underlying | rows | range |
|---|---|---:|---|
| `VXAPL` | Apple | 3,929 | 2011-01-07 → 2026-08-28 |
| `VXAZN` | Amazon | 3,929 | 2011-01-07 → 2026-08-28 |
| `VXGOG` | Alphabet | 3,929 | 2011-01-07 → 2026-08-28 |
| `VXGS` | Goldman Sachs | 3,929 | 2011-01-07 → 2026-08-28 |
| `VXIBM` | IBM | 3,929 | 2011-01-07 → 2026-08-28 |

This matches the verification log's expectation (2011-01-07 →) exactly. **Phase 3's and
Phase 5's single-stock IV fit is unblocked**, with the plan's own caveat intact: five
mega-caps are not a cross-section.

### 5.2 Index IV, term structure, sector/ETF vol

| group | indices | notable range |
|---|---|---|
| index | `VIX` (9,261 rows, **1990-01-02** →), `VXN`, `VXO` (1993→2021), `VXD`, `RVX`, `VVIX` (2006→), `SKEW` (**1990** →) | VIX and SKEW both reach 1990 |
| term structure | `VIX9D`, `VIX3M`, `VIX6M` | `VIX6M` from 2008-01-02 |
| ETF / sector | `VXEEM`, `VXEWZ`, `VXSLV`, `VXGDX`, `VXXLE`, `VXTLT` (2004→), `GVZ`, `OVX`, `VPD`, `VPN` | `VXTLT` from 2004 |

`SKEW` (risk-neutral tail asymmetry, 1990→) and the 9-day/1-month/3-month/6-month term
structure were not in the plan's list and are worth having for Phase 3.

### 5.3 Also retained: Yahoo and FRED, and a three-way validation

`datasets/05_implied_vol/*.csv` (Yahoo: `VIX`, `VXN`, `VVIX`, `OVX`, `GVZ`) and
`fred/` (`VIXCLS`, `VXNCLS`, `VXOCLS`, plus rate series `DGS3MO`, `DGS10`, `DFF`, and
`SP500`) are kept from the first pass. FRED's no-key CSV endpoint was used; **no API key.**
`VXOCLS` reaches **1986-01-02**, covering the 1987 crash, which nothing else here does.

Over the **9,228** days all three cover:

| pair | identical to 0.01 | max diff | correlation |
|---|---:|---:|---|
| **CBOE vs FRED** | **100.00 %** | **0.000** | **1.00000000** |
| CBOE vs Yahoo | 99.87 % | 2.610 | 0.99999242 |
| Yahoo vs FRED | 99.87 % | 2.610 | 0.99999242 |

**Correction to the first pass.** That pass described Yahoo-vs-FRED as "two genuinely
independent retrievals". It is not: **FRED republishes CBOE's series verbatim** — 100 %
identical, correlation exactly 1. FRED is a mirror, not a second measurement. The real
validation is CBOE (authoritative) vs Yahoo (independent), and Yahoo passes: 99.87 % of
days identical to 0.01, the 9 exceptions being half-days and holidays. Use CBOE as the
reference series and treat FRED as a convenience copy.

## 6. Need #6 — Sentiment (**obtained**, all three frequencies)

| series | source | licence | rows | range | how |
|---|---|---|---:|---|---|
| **Daily** news sentiment | SF Fed (Shapiro, Sudhof & Wilson 2022, *J. Econometrics* 228) | public, cite the paper | **17,018** | 1980-01-01 → 2026-08-23 | automated |
| **Weekly** survey sentiment | **AAII Investor Sentiment Survey** | AAII copyright; free to download, **do not republish** | **2,041** | **1987-06-26 → 2026-08-27** | **manual download** |
| **Monthly** investor sentiment | Baker & Wurgler, NYU Stern | public academic, cite Baker & Wurgler (2006) | 792 rows; 702 with non-null `SENT` | `SENT` 1965-07 → 2023-12 | automated |
| Monthly/annual (`v23` workbook) | Baker & Wurgler | as above | 648 / 105 | see file | automated |

The SF Fed workbook's first sheet is `Methodology`; the series is on the sheet named
`Data`. Baker–Wurgler ends **Dec 2023**, confirming the verification log.

### 6.1 AAII — why it needed a human, and what arrived

The second pass established the position precisely:

1. `https://www.aaii.com/sentimentsurvey/sent_results` returns HTTP 200, but the body is a
   **JavaScript bot-challenge page**, not data.
2. `https://www.aaii.com/files/surveys/sentiment.xls` **is** served plainly — 1,313,792
   bytes of `application/vnd.ms-excel`, no challenge.
3. But `https://www.aaii.com/robots.txt` carries, under `User-agent: *`,
   **`Disallow: /files/*`** — one of its 73 rules.

So the file was reachable and was deliberately **not fetched by script**. `robots.txt`
binds automated clients, not people, so the user downloaded it in a browser to
`datasets/06_sentiment/sentiment.xls`, and `tools/e1_0_data/ingest_manual.py` parsed,
checked and documented it on the same footing as every automated source.

**What it contains** (`aaii_sentiment_weekly.csv`, sheet `SENTIMENT`, 2,041 rows):

| column | meaning |
|---|---|
| `Date` | survey week ending |
| `Bullish`, `Neutral`, `Bearish` | response shares, as **fractions** (0–1), not percentages |
| `Total` | the three shares summed |
| `Mov Avg` | AAII's 8-week moving average of `Bullish` |
| `Spread` | `Bullish − Bearish` |
| `Average`, `+St. Dev.`, `- St. Dev.` | long-run summary constants, **repeated on every row** |
| `High`, `Low`, `Close` | S&P 500 levels AAII bundles alongside |

**Quality.** 0 duplicate dates; median spacing exactly 7 days; a single 21-day gap at
1987-07-17, at the very start of the series. `Bullish + Neutral + Bearish` sums to 1.0
within 0.005 on **all 2,038 populated rows** — an internal consistency check the series
passes completely. The first two rows (1987-06-26, 1987-07-17) carry no survey values, so
the usable series begins **1987-07-24**. The last two rows repeat identical `High`/`Low`/
`Close`, which looks like a stale index quote in AAII's own file; it was **not** corrected.

**Licence.** AAII holds copyright in this history. It is free to download and use, but it
must not be republished — like the Yahoo, CBOE and Nasdaq data it stays inside the
git-ignored `datasets/` tree.

## 7. Need #7 — Industry P/E, payout, factors, risk-free

| source | licence | fetched | contents |
|---|---|---|---|
| Kenneth R. French Data Library | free for research; cite Fama & French | 29 Aug 2026 | daily 3-factor **incl. RF** (26,274 rows → 2026-06-30), daily 5-factor, daily momentum, monthly 3-factor, 49 industry portfolios daily |
| Aswath Damodaran datasets (Jan 2026 update) | free with attribution | 29 Aug 2026 | `pedata` (industry P/E), `divfund` (payout), `histretSP`, `betas`, `wacc`, `pbvdata` |

The daily `RF` series the plan needs is inside
`F-F_Research_Data_Factors_daily_CSV.zip`. FRED's `DGS3MO`, `DGS10` and `DFF`
(`datasets/05_implied_vol/fred/`) give independent risk-free and rate series. Damodaran workbooks have two sheets; the
figures are on **`Industry Averages`** (~104 industry rows), not the first sheet. French
CSVs carry several header lines and a second annual block after a blank line — read with
an explicit `skiprows` and stop at the blank line. Values are in **percent**.

---

## 8. Need #8 — Second daily price source (**obtained**)

Closed on the second pass, and **without an API key** — the request in the first pass to
obtain a free Alpha Vantage key is withdrawn as unnecessary.

| item | value |
|---|---|
| Source | Nasdaq's public historical-quote endpoint, `https://api.nasdaq.com/api/quote/<SYM>/historical` |
| Fetched | 29 Aug 2026 (second pass) |
| Licence / access | Public JSON endpoint, **no account, no key**. Nasdaq's site terms cover reference/research use; files stay in the git-ignored `datasets/` tree. |
| Rate limit | Not published; run at 0.5 s between requests |
| Depth | ≈ 2,349 trading days per ticker — roughly 2016-08-29 → 2025-12-31 |
| Files | `datasets/08_price_crosscheck/daily/<TICKER>.parquet` + `retrieval_log.csv` |
| Also taken | `nasdaqtraded.txt` — Nasdaq's traded-symbol directory (994 KB) with an ETF flag, which independently corroborates the reuse screen |

Prices are split-adjusted but **not** dividend-adjusted, so they cross-check Yahoo's
`Close`, not its `Adj Close`.

### 8.1 Agreement with Yahoo

`tools/e1_0_data/compare_sources.py` → `datasets/_manifests/source_agreement.csv`.

Levels alone are a poor test: the two providers apply splits retroactively at different
times, so a name can differ by exactly a factor of 2 while describing the same security.
**Daily returns are invariant to that**, so returns are the headline test and levels are
reported as a diagnostic.

Result over **640 tickers and 1,424,865 overlapping day-pairs** (mean 2,226 days each):

| statistic | value |
|---|---|
| median per-ticker **return** correlation | **1.000000** |
| median per-ticker share of days with returns within 10 bp | **100.00 %** |
| tickers with return correlation ≥ 0.999 | 620 (96.9 %) |
| tickers with return correlation ≥ 0.99 | 629 (98.3 %) |
| tickers with return correlation < 0.90 | **2** |

Level agreement is also 100 % at the median, but it is the weaker statistic: a name whose
split one provider has applied retroactively and the other has not shows a constant
factor-of-2 gap while the returns match perfectly. Read `pct_within_0.5pct` as a
corporate-actions diagnostic, not as a disagreement.

### 8.2 What the cross-check bought

1. **It validates the panel.** Yahoo and Nasdaq agree on returns to a median correlation
   of 1.000000 across ~900,000 day-pairs. The price data underlying Phases 1–6 is sound.
2. **It caught a reuse case the metadata screen missed** — `GP`, an ordinary Nasdaq-listed
   EQUITY with no anomaly except that its returns did not match. That led to the
   start-date test which raised the flagged count from 42 to 86 (§1.3). A second source
   earned its keep immediately.
3. **It does not fix survivorship.** Nasdaq's endpoint reaches back only ~9 years and, like
   Yahoo, serves the *current* holder of a symbol. Neither source restores Enron, Lehman,
   WorldCom or Compaq. The delisted tail remains the panel's structural gap, and it is the
   one thing CRSP would actually fix (Q5, Q7).

### 8.3 Sources still refused, for their own reasons

| source | why not |
|---|---|
| **Stooq** | `robots.txt`: `User-agent: *` → `Disallow: /` — only Googlebot and Bingbot are permitted. It also serves a JavaScript proof-of-work challenge to scripts. Scripted use is doubly excluded. |
| Tiingo, EODHD, Finnhub, Polygon, Marketstack | reachable after the filter lifted, but all require an account and an API key |

## 9. Final counts

### 9.1 Need #3 — EDGAR fundamentals, completed run

| outcome | n | share |
|---|---:|---:|
| facts retrieved | **819** | 74.9 % |
| no CIK could be resolved | 224 | 20.5 % |
| CIK resolved but `companyfacts` 404 (pre-XBRL filer) | 43 | 3.9 % |
| CIK resolved, none of the six concepts present | 8 | 0.7 % |
| **attempted** | **1,094** | |

**799,946** fact rows, period ends **2005-12-31 → 2026-08-02**. How the CIK was found, for
the 819 successes: `ticker.txt` 689, **SEC historical name lookup 115**, Wikipedia CIK
column 15.

Coverage by index-exit status:

| group | n | with facts | % |
|---|---:|---:|---:|
| still in the index at 2024-12-31 | 752 | 695 | **92.4 %** |
| left the index during 2000–2024 | 342 | 124 | **36.3 %** |

**Fundamentals reach delisted names better than prices do** — 36.3 % vs 24.6 % — because
EDGAR keeps a filer's history after delisting and the SEC name lookup recovers the CIK.
Phase 1 can therefore study some names for which no price series exists here.

### 9.2 Need #1 — ticker-reuse screen, final

**86 of 673 retrieved tickers (12.8 %)** carry at least one flag, across five criteria:

| flag | n |
|---|---:|
| `starts_<N>d_after_index_exit` (series begins after the name left) | **64** |
| `not_equity` (Yahoo `quoteType` ≠ EQUITY) | 22 |
| `max_daily_ret` > 100 % | 15 |
| `zero_volume` on > 25 % of days | 9 |
| `otc_venue` (OTC/pink exchange code) | 5 |

Yahoo `quoteType` across the panel: 651 EQUITY, **20 ETF**, 2 MUTUALFUND. Former
constituents whose symbols are now ETFs include `FB` (→ ProShares S&P 500 Dynamic Daily
Buffer ETF), `EMC` (→ Global X Emerging Markets), `ABI`, `GENZ`, `INFO`.

Two screen bugs were found and fixed in the course of this work, both recorded here rather
than quietly corrected:

* the first pass queried Yahoo with the raw universe ticker instead of the symbol
  `yfinance` used, mis-typing `BF.B` and `BRK.B`; re-queried as `BF-B`/`BRK-B` they are
  Brown-Forman and Berkshire Hathaway, both EQUITY, both unflagged;
* the metadata-only screen missed 44 of the 64 start-date cases — found via the need-#8
  cross-check (§1.3).

### 9.3 The panel a phase would actually use

Combining retrieval, history length and the full screen — **reported, not applied**;
Phase 1 owns the exclusion rule (Q7):

| set | n |
|---|---:|
| universe (in index at any time 2000–2024) | 1,094 |
| price series retrieved | 673 |
| retrieved **and** flag-free | **587** |
| full 2000–2024 history | 428 |
| full history **and** flag-free | **419** |
| of the 342 that left the index: retrieved | 84 |
| **of the 342 that left the index: retrieved and flag-free** | **16** |

Both E1.0 targets survive screening: **587 ≥ 300** names and **419 ≥ 100** full histories.
The delisted tail does not: **16 clean names out of 342**, i.e. **4.7 %**.

### 9.4 Need #8 — source agreement, final

Nasdaq returned data for **640 of the 673** tickers Yahoo had (95.1 %); the 33 misses are
`no_data` — symbols Nasdaq does not carry, mostly the ETF-reassigned ones.

All 640 were compared against Yahoo over **1,424,865 overlapping day-pairs**:

| statistic | value |
|---|---|
| median per-ticker return correlation | **1.000000** |
| median share of days with returns within 10 bp | **100.00 %** |
| ≥ 0.999 correlation | 620 tickers (96.9 %) |
| ≥ 0.99 | 629 (98.3 %) |
| ≥ 0.95 | 636 (99.4 %) |
| **< 0.90** | **2 tickers** |

**The two exceptions are both ticker-reuse cases, and both were independently caught by
the start-date flag:**

| ticker | return corr | index constituent | what Yahoo serves | flag |
|---|---:|---|---|---|
| `UK` | 0.732 | Union Carbide (left 2001-02) | Ucommune International | `starts_6853d_after_index_exit` |
| `GP` | 0.875 | Georgia-Pacific (left 2005-12) | GreenPower Motor | `starts_5384d_after_index_exit` |

Two independent methods — a second price source, and a date-arithmetic test — single out
exactly the same two names out of 640. That mutual confirmation is the strongest evidence
in this report that the reuse screen is measuring something real, and that the rest of the
panel's prices are trustworthy.

## 10. Licences — summary

| source | licence / terms | redistribution |
|---|---|---|
| Yahoo Finance (`yfinance`) | ToS: personal, non-commercial | **No.** `datasets/` is git-ignored |
| **CBOE** index CSVs | free daily index files for reference/research | **No.** git-ignored |
| **Nasdaq** `api.nasdaq.com` + symbol directory | public endpoint, no key; site terms cover research use | **No.** git-ignored |
| `fja05680/sp500` | MIT | yes, with notice |
| `hanshof/sp500_constituents` | MIT | yes, with notice |
| Wikipedia revision | CC BY-SA 4.0 | yes, with attribution + share-alike |
| SEC EDGAR | US public domain | yes |
| Shiller | public academic, attribution | yes, with attribution |
| datahub `s-and-p-500` | PDDL | yes |
| SF Fed news sentiment | public, cite the paper | yes, with citation |
| Baker–Wurgler | public academic, cite the paper | yes, with citation |
| **AAII** | AAII copyright; free to download and use | **No.** git-ignored |
| Kenneth French library | free for research, cite Fama & French | yes, with citation |
| Damodaran | free with attribution | yes, with attribution |

`datasets/` was added to `.gitignore`, so none of this is committed. Yahoo, CBOE and
Nasdaq restrict redistribution; the academic and government sources are publishable with
attribution.

**Two sources were not taken by script**, on their own published rules rather than any
technical obstacle. **AAII** (`robots.txt` `Disallow: /files/*`) was then obtained the
legitimate way — a person downloaded it in a browser (§6.1). **Stooq**
(`robots.txt` `Disallow: /` for every agent but Googlebot and Bingbot, §8.3) remains
excluded, and is not needed: Nasdaq closed need #8.

---

## 11. Open questions for the team

The first pass raised seven. Three were closed by the second pass (Q1, Q2, Stooq) and a
fourth by the manual download (Q4). **No data gap remains.** What is left is a set of
decisions, not blockers:

**Q3 — SEC User-Agent.** SEC's fair-access policy asks requesters to declare a contact
address. This run declared
`"FinPersona-Bench academic research (non-commercial; env v2.1 data panel)"` — a project
identifier with **no e-mail**, because sending a personal address to a third party was not
authorised. Every request succeeded. **Do you want a contact e-mail added** for future
runs?

**Q5 — WRDS access at the institution (decision D1 / REG-15).** *Still not assumed either
way.* **Does the institution hold a WRDS subscription covering CRSP, Compustat,
OptionMetrics or I/B/E/S, and if so, when could access be arranged?** REG-15 keeps option
B alive only if access arrives before Phase 1 would end — a calendar fact only the team
has. Note the second pass weakens the case for waiting: single-stock IV (the strongest
OptionMetrics argument) is now in hand for five names, and need #8 has a cross-check. What
free data still cannot supply is the **delisted price tail** — see Q7.

**Q6 — Panel location.** The task specified `datasets/` at the repo root and that is what
was built. Plan §5.2 E1.0 names `data/panel/` plus
`docs/env_v2/generated/v2_1/panel_manifest.md`. The per-folder `README.md` files and
`datasets/_manifests/` carry the manifest content. **Say the word and the panel will be
moved and the manifest written at the plan's path** — no plan text was edited.

**Q7 — Ticker reuse, and the delisted tail (§1.3, §8.2).** This is now the panel's
binding limitation, not network access. The screen flags suspects but excludes nothing;
Phase 1 must set the exclusion rule before any tail, kurtosis or drawdown statistic is
computed. Neither Yahoo nor Nasdaq restores genuinely delisted names — that gap is
structural to free data and is exactly what CRSP would fix.

### Closed during this work

* **~~Q1 — single-stock implied volatility.~~** **Closed.** All five CBOE single-stock VIX
  histories obtained, 3,929 rows each, 2011-01-07 → 2026-08-28, plus 20 further CBOE
  indices (§5). No IT allowlist request and no literature fallback needed.
* **~~Q2 — second price source / Alpha Vantage API key.~~** **Closed, and no key was
  needed.** Nasdaq's public endpoint serves ~9.3 years per ticker with no account (§8).
  The earlier request for permission to obtain a free API key is withdrawn.
* **~~Q4 — AAII weekly survey sentiment.~~** **Closed by manual download.** 2,041 weekly
  rows, 1987-06-26 → 2026-08-27, ingested and quality-checked (§6.1). All three sentiment
  frequencies the plan wanted are now in the panel.
* **~~Stooq.~~** Settled, negatively and permanently: its `robots.txt` is
  `User-agent: *` → `Disallow: /`. It is not a candidate for scripted use at all.

## 12. Reproducing this

```bash
python tools/e1_0_data/probe_reachability.py    # which hosts this machine can reach
python tools/e1_0_data/fetch_constituents.py    # need #2 -> universe_2000_2024.csv
python tools/e1_0_data/fetch_prices.py          # need #1 (reads the universe)
python tools/e1_0_data/fetch_edgar.py           # need #3
python tools/e1_0_data/fetch_files.py           # needs #4, #6, #7 + Yahoo/FRED vol
python tools/e1_0_data/fetch_cboe.py            # need #5 (CBOE, incl. single-stock VIX)
python tools/e1_0_data/fetch_crosscheck.py      # need #8 (Nasdaq; resumable)
python tools/e1_0_data/quality_checks.py        # quality + survivorship tables
python tools/e1_0_data/screen_ticker_reuse.py   # ticker-reuse screen (queries Yahoo)
python tools/e1_0_data/screen_ticker_reuse.py --recompute-flags   # re-flag, no network
python tools/e1_0_data/compare_sources.py       # need #1 vs need #8 agreement
python tools/e1_0_data/ingest_manual.py         # parse hand-downloaded files (AAII)
python tools/e1_0_data/write_readmes.py         # regenerate the per-folder READMEs
```

Run `probe_reachability.py` first from any candidate machine: it writes
`datasets/_manifests/reachability_probe.csv` and tells you in one pass what is available
there. `fetch_crosscheck.py` **resumes** — `api.nasdaq.com` can hang a connection past the
read timeout, so a run may need restarting; it keeps whatever was already written.

Every network attempt, successful or failed, is appended to
`datasets/_manifests/attempts_*.json` with a UTC timestamp, the URL, the outcome and the
detail. The two deliberate refusals (AAII, Stooq) and their `robots.txt` grounds are in
`attempts_retry_blocked.json`.

## 13. Files written or changed

**Modified (1)**

* `.gitignore` — appended `datasets/` (with a comment) so no third-party data is committed.

**Created — code (13 files, `tools/e1_0_data/`)**

| file | purpose |
|---|---|
| `common.py` | shared HTTP layer: declared User-Agent, per-host throttle, backoff, attempt log |
| `probe_reachability.py` | records which hosts this machine can reach, and how they fail |
| `fetch_constituents.py` | need #2 — three constituent sources → `universe_2000_2024.csv` |
| `fetch_prices.py` | need #1 — Yahoo daily OHLCV for every universe ticker |
| `fetch_edgar.py` | need #3 — EDGAR company-facts, three-stage CIK resolution |
| `fetch_files.py` | needs #4, #6, #7 + Yahoo/FRED volatility and rate series |
| **`fetch_cboe.py`** | need #5 — 25 CBOE index histories incl. the five single-stock VIX |
| **`fetch_crosscheck.py`** | need #8 — Nasdaq second price source (resumable) |
| `quality_checks.py` | ranges, gaps, duplicates, non-positive prices, >50 % returns, zero volume, survivorship |
| `screen_ticker_reuse.py` | five-criterion reuse screen, incl. the start-date test; `--recompute-flags` re-runs offline |
| **`compare_sources.py`** | need #1 vs need #8 agreement, on returns and levels |
| **`ingest_manual.py`** | parses, checks and documents files a person downloaded by hand (AAII) |
| `write_readmes.py` | regenerates each `datasets/<need>/README.md` from the files on disk |

**Created — documentation (1)**

* `docs/env_v2/v2_1/E1_0_DATA_REPORT.md` — this file.
  *(`docs/env_v2/v2_1/` is git-ignored by the repo's existing convention, so it is
  local-only, like the rest of the v2.1 working notes.)*

**Created — data (git-ignored, under `datasets/`)**

| path | contents |
|---|---|
| `01_prices/daily/*.parquet` | 673 ticker histories + `README.md`, `retrieval_log.csv` |
| `02_constituents/` | 3 sources, parsed Wikipedia tables, `universe_2000_2024.csv`, `README.md` |
| `03_fundamentals/by_ticker/*.parquet` | 819 filers, 799,946 facts + `README.md`, `retrieval_log.csv` |
| `04_shiller/` | `ie_data.xls`, `shiller_monthly.csv`, datahub cross-check, `README.md` |
| `05_implied_vol/` | 5 Yahoo indices, `fred/` (7 series), **`cboe/` (25 indices, 5 single-stock VIX)**, `README.md` |
| `06_sentiment/` | SF Fed daily, **AAII weekly (manual)**, Baker–Wurgler monthly (2 workbooks), `README.md` |
| `07_factors_valuation/` | 5 French ZIPs, 6 Damodaran workbooks, `README.md` |
| **`08_price_crosscheck/`** | **Nasdaq daily series + `nasdaqtraded.txt` + `README.md`, `retrieval_log.csv`** |
| `_manifests/` | `attempts_*.json` (incl. `attempts_retry_blocked.json`), `reachability_probe.csv`, `quality_prices.csv`, `quality_other.csv`, `survivorship_accounting.csv`, `ticker_reuse_screen.csv`, `source_agreement.csv` |
| `README.md` (top level) | **the panel's entry point** — folder map, cross-cutting manifests, and the three caveats to read first |

Every folder carries its own `README.md` (source, URL, licence, rate limit, schema, row
counts, caveats), regenerated from the files on disk by `write_readmes.py` — so the docs
cannot drift from the data.

**Not touched:** `envs/`, `evaluation/`, `agent/`, `simulation/`, the plan, the alternatives
register, `docs/env_v2/v2_1/archive/`. Branch `main` throughout; `HEAD` is still `04ba88c`
— no commit, amend, reset, stash or push.

---

## 14. What changed between the two passes

| | first pass | after retry + manual download |
|---|---|---|
| needs satisfied | 6 of 8 | **8 of 8** |
| single-stock IV (#5) | none | **5 indices, 3,929 rows each**, + 20 more CBOE files |
| second price source (#8) | none; needed an API key | **Nasdaq, no key**, ~2,349 days × 673 tickers |
| AAII (#6) | "network-blocked" | **`robots.txt` forbids scripted fetch** → downloaded by hand: 2,041 weekly rows, 1987–2026 |
| Stooq (#8) | "network-blocked" | **`robots.txt` `Disallow: /`** — permanently excluded |
| ticker reuse | 42 flagged (6.2 %) | **86 flagged (12.8 %)**, via the start-date test the cross-check exposed |
| delisted coverage | "24.6 %" | **4.7 %** genuinely usable |
| FRED | "unreachable" | **intermittent**; and it mirrors CBOE exactly, so it is not a second source |

The second pass did not just fill gaps — it **corrected two claims of the first**: that
Yahoo and FRED were independent (they are not), and that delisted coverage was around a
quarter (it is about a twentieth).

**The panel is complete.** Every need in the E1.0 brief now has data, quality checks, a
licence note and a reproducible fetch path. What limits Phases 1–6 is no longer
availability but **the delisted tail** (§1.3): about 5 % of names that left the index are
genuinely recoverable from free sources, and no amount of retrying changes that. It is the
one thing WRDS would fix, and it is what Q5 and Q7 are about.
