# Forex Monitor — Zero-Subscription Market Data Research

**Research date:** 2026-11-09  
**Scope:** API and data sources with a $0 entry tier or public/open government data  
**Status:** Research decision; no provider account has been connected or integration deployed  
**Objective:** Improve signal measurement, execution realism, fundamental context and validation while avoiding new recurring market-data subscriptions.

## Executive decision

We can build a capable first research system without purchasing additional market-data subscriptions. The recommended baseline is:

1. Keep **Twelve Data Basic** as the existing five-minute, eight-pair candle source.
2. Add a **broker-specific price adapter** for executable bid/ask quotes: cTrader Open API if the intended broker supports cTrader, or OANDA v20 if the user has an eligible OANDA v20 account.
3. Use **Dukascopy historical bid/ask ticks** for offline market replay and strategy research, with the actual broker feed as the final reference for execution realism.
4. Use **official national statistical/central-bank sources** for macroeconomic releases and historical data, and **FRED/ALFRED** for US series and point-in-time vintage reconstruction.
5. Pilot **Marketaux Free** for financial news and **GDELT 2.0** as a broad, lower-confidence event/discovery feed. Use official central-bank/statistical-agency feeds as authoritative source confirmation.
6. Add **CFTC Commitments of Traders** as a weekly positioning/regime feature, not an intraday trigger.
7. Use **Massive Currencies Basic** only as an optional independent historical/day/minute-bar cross-check; its free plan does not include the real-time quote/WebSocket functionality needed to replace the live source.

This is not an institutional consolidated market-data stack. Spot FX is fragmented and OTC; each broker or vendor's prices are a view of its own liquidity sources. A broker feed is most relevant to that broker's executable prices, while an independent feed helps detect source disagreement and evaluate robustness.

## 1. Current system and free-budget fit

The current scanner requests eight symbols in one Twelve Data time-series batch and runs every five minutes during the configured weekday window.

Twelve Data currently advertises its Basic plan at $0/month with real-time Forex market data, 8 API credits/minute, 800 API credits/day and 8 trial WebSocket credits. The pricing documentation says a multi-symbol time-series call consumes one credit per symbol.

Estimated usage for the existing design:
- Eight currency pairs × one credit each = **8 credits per scan**.
- Twelve scans per hour × five hours = **60 scans/day**.
- 60 × 8 = **480 credits per full weekday schedule**.
- This fits inside the advertised 800/day budget, leaving 320 daily credits.
- It uses the full 8-credit per-minute allowance during the scan minute; there is no same-minute headroom for retries, a second endpoint, or additional pair requests.

**Decision:** Keep the current request pattern, cache anything that does not need a five-minute refresh, and do not add another per-scan endpoint to this plan without first measuring its credit weight. Confirm the exact endpoint and personal/internal-use terms in the account dashboard before production use.

Sources:
- https://twelvedata.com/pricing
- https://support.twelvedata.com/en/articles/5203360-batch-api-requests

## 2. Provider shortlist

### A. Live spot Forex quotes and candle data

#### 1. Existing Twelve Data Basic — retain as primary scanner candles

**Cost:** $0 Basic plan (current advertised terms).  
**Strengths:** It already feeds the scanner; current plan advertises real-time Forex, with 8 credits/minute and 800/day.  
**Limitations:** Eight-symbol call consumes all available credits for that minute. The free WebSocket allowance is shown as trial credits, so it should not be treated as a durable streaming service. A candle feed is not the same as executable broker bid/ask prices.  
**Use:** Continue feeding existing OHLC-based technical screening until a broker feed adapter is proven.

#### 2. cTrader Open API — first broker-feed candidate where supported

**Cost:** Spotware's published Open API terms currently say the API is free. Spotware reserves the right to change pricing.  
**Requirements:** A cTrader ID, an account with a cTrader-affiliated broker, application registration and approval, and user authorization to the relevant account.  
**Capabilities:** Real-time spot quote subscriptions with bid/ask fields; historical bars; historical tick requests; optional depth quotes. Official docs list limits of 50 non-historical requests/second/connection and 5 historical requests/second/connection.  
**Important history limit:** A historical tick request cannot exceed one week. Large responses can be truncated by a backend-specific limit, and the API supplies a hasMore flag. This makes it useful for broker-specific recent replay and live price capture, but not a turnkey bulk archive.  
**Use:** Preferred broker quote adapter if the user's actual broker provides cTrader. Capture only bid/ask, timestamp, symbol, connection status and available depth. Do not enable trade permissions; request the minimum read-only access required.

Sources:
- https://help.ctrader.com/open-api/
- https://help.ctrader.com/open-api/terms-of-use/
- https://help.ctrader.com/open-api/symbol-data/
- https://help.ctrader.com/open-api/faq/

#### 3. OANDA v20 REST/streaming API — alternative if the actual broker is OANDA

**Cost:** Demo account and API access are offered without a separate market-data subscription in the getting-started flow; a qualifying v20 practice or live account and API token are required.  
**Capabilities:** OANDA documents real-time rates for tradable instruments and historical pricing back to 2005. Its streaming endpoint sends at most four prices per second per instrument, not every underlying price change.  
**Eligibility caveat:** v20 is not available to all OANDA divisions. Verify that the user's account division is eligible before designing around it.  
**Use:** Strong option if OANDA is the actual trading venue; the OANDA practice feed can be used for integration development and its live account feed can later be used for execution-reference measurements.

Sources:
- https://developer.oanda.com/rest-live-v20/introduction/
- https://developer.oanda.com/rest-live-v20/pricing-ep/
- https://developer.oanda.com/rest-live-v20/development-guide/

#### 4. Massive Currencies Basic — optional independent historical cross-check

**Cost:** $0 Basic plan currently advertises 5 API calls/minute and two years of historical data, end-of-day data, reference data, technical indicators and minute aggregates.  
**Limitations:** Real-time Forex, quote access, snapshots and WebSockets are listed under the $49/month Starter plan, not Basic.  
**Use:** Consider for secondary historical/minute-aggregate comparisons and data-quality checks, not as a free real-time replacement for Twelve Data or broker bid/ask.

Sources:
- https://massive.com/currencies
- https://massive.com/pricing?product=currencies
- https://massive.com/docs/websocket/forex/overview

### B. Historical tick data for backtesting

#### 5. Dukascopy historical ticks via dukascopy-node — preferred free bulk-replay candidate

**Cost:** The downloader is an open-source, free Node.js CLI/library.  
**Capabilities:** It downloads historical ticks and OHLC data for many instruments, with bid and ask price fields and CSV/JSON outputs.  
**Limitations:** This is Dukascopy-source data, not the user's broker's actual executable quote stream. Availability, gaps, timestamps, instrument conventions and data-use rights should be validated before treating it as ground truth. The dukascopy-node project is a third-party downloader, not a Dukascopy-operated API client guarantee.  
**Use:** Historical strategy replay, feature research, and a second independent price path. Preserve bid and ask as separate series; do not collapse everything to midpoint.

Source:
- https://www.dukascopy-node.app/

#### 6. cTrader historical ticks — broker-specific, recent-window replay

Useful where cTrader is the actual broker. Each request is limited to seven days and a response can be capped, requiring pagination using hasMore. Use this for verifying current broker prices and recent samples, not as the only multi-year replay source.

Source:
- https://help.ctrader.com/open-api/symbol-data/

#### Excluded: HistData for current strategy validation

HistData still advertises free M1 and tick downloads, but its published update notice says its files were updated through **25 November 2022**. This makes it unsuitable as the primary source for recent or current market replay unless a specific instrument/timeframe download is independently shown to be current.

Sources:
- https://www.histdata.com/download-free-forex-historical-data/
- https://ftpsite.histdata.com/

### C. News and market sentiment

#### 7. Marketaux Free — first financial-news pilot

**Cost:** $0 tier currently advertises 100 requests/day and up to three articles per news request.  
**Capabilities:** Global financial news, metadata, currency entities as a supported entity type and entity sentiment fields/filters in its news API. The provider describes its news as instant, but does not publish a delivery SLA on the free-plan page.  
**Limitations:** Only three articles per request on Free; entity statistics/trending capabilities have plan restrictions; snippets are not full article text. We must test whether its currency entity mapping is sufficiently accurate for EUR, GBP, USD, JPY, CHF, CAD, AUD and NZD.  
**Use:** Poll at a measured cadence (for example, every 15 minutes, about 96 calls/day) and use it as a supplementary, source-attributed news feature. Do not call it for every pair on every five-minute scan. A headline is not a directionally reliable signal by itself.

Sources:
- https://www.marketaux.com/pricing
- https://www.marketaux.com/documentation
- https://www.marketaux.com/faq

#### 8. GDELT 2.0 — free global event and news-discovery layer

**Cost:** GDELT describes its database and raw files as free and open.  
**Capabilities:** Its Event and Global Knowledge Graph datasets update every 15 minutes, cover global reporting and support search/aggregation across topics, people, organizations, themes and events.  
**Limitations:** It is a broad global-media monitoring project, not a specialist FX newswire. Topic volume or automated emotion values should not be interpreted as validated currency-return sentiment. False positives, duplicated reporting, translation errors and source-quality differences are expected.  
**Use:** Detect geopolitical, conflict, central-bank and systemic-event news clusters; corroborate a Marketaux or official source item; create a "news attention shock" feature for shadow evaluation. Do not use GDELT alone to approve a trade.

Sources:
- https://gdeltproject.org/data.html
- https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

#### 9. Official central-bank and statistical-agency announcements — authoritative confirmation

Use public press-release/news pages and RSS feeds where offered by the issuing institution: Federal Reserve, ECB, Bank of England, Bank of Japan, Swiss National Bank, Bank of Canada, Reserve Bank of Australia and Reserve Bank of New Zealand; also the national statistical agencies for scheduled releases. This is free primary-source verification, but feeds are fragmented and may not provide a normalized, single API or market-consensus estimate.

**Use:** Confirm policy statements, decisions, speeches, release times and official values. Keep original publication timestamps and links.

### D. Economic data, calendars and macro history

There is no dependable free, universal API identified in this review that provides, for all eight currencies, a complete real-time economic calendar plus market consensus forecasts, actual releases, revisions, history and a trading-use SLA. We can build a strong free **official-event and actual-data layer**, but consensus coverage remains the main free-data gap.

#### 10. FRED / ALFRED — US macro and vintage history

**Cost:** Free API key registration.  
**Capabilities:** Thousands of US financial/economic series; ALFRED real-time periods and vintage dates allow retrieval of what was known at a historical date and reduce look-ahead bias. FRED documents up to 120 requests/minute before throttling.  
**Limitations:** FRED is not a complete intraday economic calendar and does not provide market consensus forecasts for every release. Its many series update at daily, weekly or monthly frequency.  
**Use:** US policy rates, Treasury yields, employment/inflation series, broad trade-weighted dollar and other macro/regime context. Use ALFRED vintages in backtests.

Sources:
- https://fred.stlouisfed.org/docs/api/fred/
- https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
- https://fred.stlouisfed.org/docs/api/fred/errors.html

#### 11. BLS Public Data API v2 — US inflation and employment

**Cost:** Free registration.  
**Limits:** The BLS FAQ currently documents 500 queries/day, up to 50 series per query, up to 20 years per query and a 50-request-per-10-second request-rate limit for registered users.  
**Use:** CPI, PPI, employment, unemployment, wages and other US labour/price series. Pair series data with the official release calendar and point-in-time publication timestamps.

Sources:
- https://www.bls.gov/developers/api_faqs.htm
- https://www.bls.gov/developers/

#### 12. Eurostat API and ECB data services — euro-area macro

Eurostat's REST API is free and updates datasets twice daily, but the API introduction says the database only contains the latest dataset version and does not document historical vintages. Use it for euro-area inflation, GDP, employment and other macro series; preserve our own downloaded release snapshots.

Sources:
- https://ec.europa.eu/eurostat/en/web/user-guides/data-browser/api-data-access/api-introduction
- https://data.ecb.europa.eu/help/api/overview

#### 13. Bank of Canada Valet — free no-key official API

**Cost:** Free; no registration or API key required.  
**Capabilities:** Exchange rates, interest rates, economic statistics and financial reports.  
**Limitation:** Its reference exchange rates are daily, not executable intraday quotes.  
**Use:** CAD macro/rate context and historical reference data, not entry prices.

Source:
- https://www.bankofcanada.ca/valet-api-how-to/

#### 14. Other national statistical/central-bank APIs

Use these official sources for the other currencies and for release-vintage validation:
- **GBP:** ONS Developer API (open, no API key documented) and Bank of England data.
- **CAD:** Statistics Canada Web Data Service and Bank of Canada Valet.
- **AUD:** Australian Bureau of Statistics Data API (free access, API keys removed in its 2024 change) and RBA data.
- **EUR:** Eurostat and ECB Data Portal.
- **USD:** BLS, BEA, FRED/ALFRED and Federal Reserve.
- **JPY / CHF / NZD:** official national statistics and central-bank release pages/data services; validate the specific API's access, update and revision rules in a small pilot before implementation.

Sources:
- https://developer.ons.gov.uk/
- https://www.statcan.gc.ca/en/developers/wds
- https://www.abs.gov.au/statistics/application-programming-interfaces-apis/data-api-user-guide
- https://www.rbnz.govt.nz/statistics
- https://www.snb.ch/en/the-snb/mandates-goals/statistics
- https://www.boj.or.jp/en/statistics/

#### Calendar policy with free data

Use official calendars to build a forward event schedule and official sources to obtain the actual release. Store event name, affected currency, scheduled timestamp, source URL, importance, release timestamp, actual, previous and revision when available. Use a manual/config-reviewed schedule as a bootstrap; automate official calendar parsing only where terms and structure permit.

Do not pretend that consensus is known when no free authoritative consensus feed is available. The initial system can implement conservative event blackouts around major releases without consensus. A quantitative "surprise" feature must remain unavailable/unknown until a valid, timestamped forecast consensus is recorded.

### E. Positioning and cross-market context

#### 15. CFTC Commitments of Traders — free weekly positioning

**Cost:** Public CFTC data; the Public Reporting Environment API is generally usable without a token if not overused.  
**Timing:** Reports are generally published Friday at 3:30 p.m. Eastern with position data from the prior Tuesday; holidays can move publication.  
**Use:** Managed-money/leveraged-fund and dealer positioning in currency futures for medium-term crowding/positioning context. Map each futures contract to the relevant FX currency and preserve report date separately from publication date.  
**Limitation:** Weekly and lagged; never treat COT as a five-minute timing signal.

Sources:
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- https://publicreporting.cftc.gov/

#### 16. Free macro cross-market proxies

Use FRED and national central-bank APIs for daily Treasury/bond yields, policy rates, broad trade-weighted USD and official commodity/economic series where available. These are useful for session/regime context and for explaining multi-hour/day backdrops, but most are too slow or delayed to validate a five-minute entry.

Do not rely on unofficial scraping of DXY, VIX, CME futures or broker websites to obtain apparently free real-time quotes. Exchange market-data rights and redistribution rules can make those sources unsuitable for automated use.

## 3. What this zero-subscription stack can and cannot deliver

### Good enough for the first research phases

- Five-minute scanning of the current eight major pairs using Twelve Data Basic.
- A broker-specific live bid/ask check if the user's broker supplies a no-extra-cost API (cTrader or OANDA, subject to account eligibility).
- Historical tick replay from Dukascopy for research and broker-specific recent tick checks where cTrader supports it.
- Official macroeconomic histories, policy rates and government release values.
- A conservative event blackout schedule.
- Broad news discovery and source-attributed news features.
- Weekly futures positioning context from CFTC.
- Independent historical OHLC comparisons using free-tier minute/daily aggregates where available.

### Not reliably available for $0 across all providers

- A universal consolidated spot-FX best bid/offer or full market depth across all liquidity venues.
- A guaranteed 24/5 feed with institutional SLA, uptime and latency guarantees.
- Full tick-level executable history for every broker and every currency pair for multiple years.
- A complete global calendar API with credible consensus, revisions and release timestamps for all eight currency blocs.
- Premium breaking-news wires with guaranteed sub-second distribution, full article licenses and deep archive.
- Exchange-licensed, real-time CME FX futures order book/volume feeds without entitlement.
- Reliable option-implied volatility, risk reversals and dealer positioning across all spot currencies.

## 4. What else is needed beyond market-data APIs?

Yes. Data is only one part of the system. The following are necessary to turn raw feeds into credible, testable alerts:

1. **Point-in-time data storage:** preserve raw values, provider, original timestamp, fetch timestamp, revision/vintage and source hash. Historical replay must use only information actually available at the time.
2. **Signal/candidate ledger:** record every candidate, rejection, AI veto, no-trade scan, feature set and model/config/prompt version—not just emailed alerts.
3. **Outcome evaluator:** replay each candidate across its stated horizon and 5/15/30/60/120-minute checkpoints; measure MFE, MAE, barrier order, expiry and net R. Mark ambiguous stop/target ordering rather than assuming the favorable result.
4. **Execution-cost model:** simulate BUY at ask and SELL at bid, then subtract spreads, fees and conservative slippage. Distinguish a generic market reference from the user's broker's executable price.
5. **Economic-event and news-risk gate:** if a source is stale, missing or unavailable, "no news" must not be inferred. Fail closed for ACTIONABLE alerts during an unverified high-impact window.
6. **Risk and portfolio engine:** detect correlated USD exposure, simultaneous positions, daily loss/drawdown and risk concentration. Signal counts cannot override risk limits.
7. **Validation and calibration:** chronological walk-forward and untouched holdout testing; compare each feature against a simple baseline; calibrate probabilities only after sufficient out-of-sample observations; do not optimize raw win rate or frequency alone.
8. **Operational reliability:** monitor scan start lag, quote freshness, request quota, data gaps, feed disconnects, email accepted/failed/ambiguous status, backups and restore.
9. **Source licensing and terms:** free access does not automatically grant rights to redistribute or republish raw feeds. Store derived features and links where appropriate, and verify intended personal/internal/non-display use for each provider.

## 5. Cost-free operating architecture

The current GitHub Actions workflow is a five-minute polling job. GitHub documents scheduled runs as best-effort, with possible delay or drops during high load. It is suitable for the bounded five-minute research scanner but not a persistent WebSocket collector.

For zero additional hosting spend:
- Keep the current GitHub Actions process for five-minute scans and notifications.
- If a persistent broker stream becomes necessary, prototype a separate collector on an always-on personal Windows machine using Task Scheduler and a supervised Python process; write to local SQLite and maintain encrypted off-device backups. This is only reliable while the machine and internet connection are on.
- Do not run a WebSocket client inside short-lived five-minute Actions jobs and call it "real-time streaming".
- Keep provider adapters separate so a broker API or free tier can be replaced without changing the signal logic.
- Keep the current scanner unchanged until shadow capture and cost-aware outcomes establish a measurable benefit.

Source:
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

## 6. Recommended integration sequence

| Stage | Integration | Mode | Why / completion criterion |
|---|---|---|---|
| **0** | Verify current Twelve Data and GitHub Actions operation | Existing production path | Establish working scan count, API usage, freshness and notification baseline |
| **1** | Add immutable signal and candidate ledger | Shadow / record-only | Capture every candidate, veto, no-trade reason, raw snapshot and version |
| **2** | Add Dukascopy historical tick importer | Offline research | Build historical replay fixtures and verify bid/ask sequence and data gaps |
| **3** | Add one broker price adapter (cTrader OR OANDA) | Read-only / demo first | Confirm live bid/ask, quote timestamp, disconnect/reconnect and symbol coverage |
| **4** | Add official macro source adapters (FRED/ALFRED, BLS, Eurostat, BoC, ONS, ABS, relevant national central banks) | Background cache | Build release-vintage-aware macro histories and calendar/event table |
| **5** | Pilot Marketaux + GDELT + official feeds | Shadow only | Check coverage, timestamps, duplicates, currency tagging, false positives and source links |
| **6** | Add CFTC COT and daily cross-market context | Background cache | Create slower positioning and risk-regime features |
| **7** | Join all evidence to outcome evaluator | Shadow only | Test incremental value of each data family; no production weighting until out-of-sample improvement is demonstrated |

## 7. Promotion and safety rules

- Do not increase scan frequency solely because another free API exists.
- Do not use a higher number of weak signals as the success metric.
- Do not authorize ACTIONABLE signals from stale/incomplete data or when a required risk feed is missing.
- Do not claim a signal probability from an LLM's qualitative grade.
- Do not use future revisions, later article updates or later timestamps in historical replay.
- Do not assume a broker/demo quote is identical to live-account execution.
- Do not use midpoint candles to claim an executable net profit.
- Do not scrape websites whose terms do not authorize automated collection.
- Do not place or manage broker orders as part of this data integration work.
- Promote a new source/feature only after measuring its data quality and incremental out-of-sample benefit.

## 8. Cost reality

The additional data subscriptions in the proposed first-pass stack can be $0, subject to free-tier quotas, eligibility, acceptable-use terms and ongoing provider policy. This does **not** make the entire Forex Monitor guaranteed to cost $0:
- The current GPT review calls the OpenAI API, which is billed separately from a ChatGPT subscription.
- An always-on hosting or database service may cost money if the local Windows collector is not used.
- Providers can change or withdraw free tiers; there are no SLA guarantees on most free plans.
- Email volume and any external storage/service quotas must be monitored.

If the goal is strict zero spend, keep the model layer optional or bounded, do not add a paid vendor, and use the existing runner plus local/available storage while recognizing the reliability trade-offs.

## 9. Final recommendation

**Recommended $0 data stack for the next implementation slice:**
- Twelve Data Basic for existing 5-minute OHLC market screening.
- cTrader Open API **or** OANDA v20 for broker-specific bid/ask, depending on the actual broker.
- Dukascopy historical bid/ask ticks for backtesting.
- FRED/ALFRED + BLS + official central-bank/statistical-agency sources for macro releases and history.
- Marketaux Free + GDELT 2.0 + official source feeds for news discovery and source confirmation.
- CFTC COT for weekly positioning.
- Massive Currencies Basic only as an optional independent bar/history comparison.

**What we should build first:** the immutable point-in-time signal/candidate ledger, historical outcome evaluator and a no-trade/health audit. Then add the broker price adapter. Calendar/news integrations should initially be shadow-only. This ordering prevents free data volume from being mistaken for predictive value.

**Open dependency:** The intended execution broker is not identified in this review. Therefore cTrader and OANDA are alternatives, not both mandatory integrations. Choose the adapter matching the actual broker; otherwise a broker quote can be useful as a reference but cannot prove the user's own execution cost.
