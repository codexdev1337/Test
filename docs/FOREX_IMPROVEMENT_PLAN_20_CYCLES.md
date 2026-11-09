# Forex Monitor — 20-Cycle Improvement Research and Implementation Plan

**Review date:** 2026-11-09  
**Repository:** [codexdev1337/Test](https://github.com/codexdev1337/Test)  
**Status:** Proposed roadmap and research plan; not implemented in the production scanner  
**Review method:** 20 sequential improvement cycles. In each cycle: inspect the current system and accumulated plan; identify a concrete gap; create an implementation and validation plan; review overlap, dependencies, safety and costs across all prior plans; then update the roadmap before beginning the next cycle.

> **Method transparency:** These are 20 structured sequential engineering/research passes in this review, not 20 independent external research teams or 20 separate model conversations. The purpose is to force cumulative re-review and convergence, not to manufacture independent consensus.

## 1. Executive decision

The best next move is **measurement and execution realism before strategy expansion**. The current scanner is an eight-pair, rules-first technical screen with an LLM veto/selection layer and Gmail notifications. It is not yet an evidence-backed profitable strategy: it has no durable signal/outcome database, no historical replay/backtest harness, no broker executable bid/ask feed, no connected economic calendar or live news feed, and no calibrated probability model.

The design target is not simply the largest number of alerts. It is the highest sustainable **net risk-adjusted opportunity capture** after spread, slippage, latency and other applicable costs, subject to explicit drawdown, exposure and reliability limits. Signal frequency is a secondary objective and must not be increased by lowering quality gates until net expectancy remains positive in chronological out-of-sample and forward paper tests.

The proposed alert taxonomy separates:
- **WATCH:** an emerging setup or proximity-to-trigger notice. It is informational and is not a trade recommendation.
- **ACTIONABLE:** a fresh, cost-aware, fully validated setup with entry/stop/target, expiry and invalidation. This is the only tier that should trigger the current trade-alert email subject.
- **NO_TRADE / DATA_BLOCKED:** a recorded outcome with a reason, not a silent disappearance.

No design can guarantee profitability. The system should be allowed to abstain, and the burden of proof belongs to every new feature and strategy change.

## 2. Current repository audit

### Confirmed implementation

The default branch is **main**. The files reviewed include:
- **forex-monitor/scan.py** — requests 1-minute time series for EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, NZD/USD, USD/CAD and EUR/GBP; builds completed 5-minute and 15-minute bars; checks EMA alignment, RSI, ADX, ATR, breakout/candle structure, freshness, and a 30-minute pair-derived currency-strength measure; proposes an ATR-based stop and 1R/2R targets.
- **forex-monitor/decision_engine.py** — sends the eight-pair snapshot and surviving candidates to the OpenAI Responses API. The model can select one supplied candidate or veto all; server-side validation prevents it creating a candidate or changing its pair/direction. HIGH/MEDIUM are qualitative grades, not probabilities.
- **forex-monitor/email_alert.py** — Gmail-compatible SMTP delivery and a manual test-email path.
- **.github/workflows/forex-major-pair-monitor.yml** — weekday five-minute schedule from 06:00 through 10:55 America/Chicago; tests run before the market scan; the job is gated on FOREX_MONITOR_ENABLED=true.
- **docs/FOREX_MONITOR.md** — documents the configuration, signal rules, email, manual spread/news checks and limitations.
- Existing tests cover indicator/math primitives and decision-output validation. They are not a historical outcome evaluator, market replay, cost model or strategy validation suite.

### Material gaps observed in code and documentation

1. **No structured signal ledger or replay.** A signal is posted to GitHub issue #1 and an email-sent marker is appended. There is no durable database of every candidate, vetoed candidate, rejected candidate, feature snapshot, model/prompt/config version or subsequent market path. An issue comment is not a research-grade event store.
2. **No historical outcome record.** The issue thread contains one example GBP/USD SELL alert dated 2026-11-04, but its comment does not contain the subsequent candle/tick path or a completed outcome. Its win/loss result therefore cannot responsibly be inferred from the alert text.
3. **Indicative price is not a broker fill.** The candidate entry is based on the latest 1-minute candle close. The scanner itself marks spread as unavailable and sets spread/news verification false. It asks the recipient to verify broker bid/ask manually.
4. **No connected fundamental/news context.** The code passes an explicit unavailable-data declaration to the model. The model is instructed not to invent scheduled events or headlines.
5. **Uncalibrated AI grade.** HIGH/MEDIUM is an LLM-generated qualitative label. There is no calibration curve, Brier/log-loss evaluation, win probability or expected net-R model.
6. **Higher-timeframe proxy is not a true one-hour series.** The current so-called higher-timeframe trend proxy is calculated from 15-minute closes using EMA(8/20). This must be distinguished from a real 60-minute aggregate.
7. **Indicator implementation needs reference validation.** The current RSI and ATR use simple rolling averages, and ADX is custom-coded. These may be usable features, but they should be compared against explicitly selected reference definitions and tested against known-good values before strategy tuning.
8. **Currency strength is a rough subset estimate.** It averages signed returns from the eight scanned pairs. Pair coverage is incomplete, weights are not volatility-normalized, and related pairs are not independent observations.
9. **Notification state has a failure window.** The issue comment is created before SMTP send and the email marker is written after SMTP accepts the message. If SMTP accepts but the following GitHub marker update fails, a retry could send a duplicate. SMTP itself does not provide a general transactional exactly-once guarantee.
10. **Operations are not fully observable.** The workflow has a skip gate. The issue history records activation as pending on required secrets and the enable variable; repository secret values cannot be inspected through this review. Current activation and current email delivery therefore remain unverified here.
11. **Scheduled execution is best-effort.** GitHub can delay or drop scheduled runs under load; this repository is public, and GitHub says scheduled workflows in public repositories are disabled after 60 days without repository activity.
12. **Market-data budget is a design constraint.** Twelve Data currently lists its Basic tier at 8 API credits/minute and 800/day, and documents that a batched query still consumes one credit per symbol. The scanner requests eight symbols in one batch. At 60 weekday scans, that is approximately 480 symbol-credits/day, assuming the current endpoint weight remains one credit per symbol. The per-minute allowance is fully consumed by one eight-symbol scan, leaving no same-minute headroom for retries or additional endpoints on that tier.

### What is not being claimed

This audit does not prove whether private GitHub secrets are present, whether the latest scheduled Actions run succeeded, whether the current Gmail inbox received the last test, or whether the one historical signal was profitable. Those require current Actions-run and recipient-inbox evidence. No market strategy change is made by this plan.

## 3. Twenty sequential improvement cycles

Each cycle below adds one improvement to the accumulated design, then rechecks the whole system before the next cycle.

### Cycle 01 — Operational truth and activation observability

**Gap identified:** The workflow's enable gate can skip the scanner, while issue history says activation was pending. A green workflow page alone can be confused with a market scan that actually ran.

**Implementation plan:** Add a preflight report that distinguishes disabled, configuration-missing, tests-failed, scan-started, scan-completed-no-trade, scan-completed-with-alert and scan-failed. Validate the presence—not the contents—of required secret variables without printing values. Add a scheduled heartbeat containing run timestamp, code revision, scan count, pair coverage, API latency, and notification state. Keep secret values out of artifacts and logs.

**Whole-plan review:** This is a prerequisite to trusting every later measurement. It does not improve trade selection directly, but without operational truth missing scans look like low signal frequency and skipped scans contaminate the dataset.

**Roadmap update / gate:** FM-0 operational verification. Pass only when manual test email, manual scan, scheduled scan and failure paths each produce distinct, inspectable states without exposing secrets.

### Cycle 02 — Point-in-time market-data integrity

**Gap identified:** Candle time, fetch time, processing time, provider status and executable quote time are not represented as one explicit data-quality contract.

**Implementation plan:** Add typed market observations with provider, instrument, bid/ask or OHLC field type, provider timestamp, receipt timestamp, timezone, interval, completed/in-progress flag, source response identifier and data-quality flags. Reject missing, duplicated, out-of-order, implausible or stale observations. Store raw input snapshots or a reproducible content-addressed reference for every decision. Use UTC internally and render local timezone only for display.

**Whole-plan review:** The ledger, evaluator, news layer and backtester all require a trustworthy decision-time snapshot. A later revised data value must never silently replace what the scanner knew at alert time.

**Roadmap update / gate:** FM-1 data contracts. Replay a captured decision from its stored inputs and reproduce the same features and candidate levels.

### Cycle 03 — Immutable signal and candidate ledger

**Gap identified:** The issue thread stores alerts but not all candidates, vetoes, no-trade scans, feature values or decision versions.

**Implementation plan:** Create a versioned signal schema and durable persistence layer. Store scan ID, candidate ID, pair, direction, decision timestamp, decision-time inputs, all features, candidate/NO_TRADE outcome, rejection reasons, technical strategy version, parameter hash, source versions, model name/version, prompt/schema hash, entry/stop/targets, expiry, and eventual lifecycle events. Record **all** candidates and vetoes, not only emailed winners, to measure false positives and missed opportunities. Use append-only event history with redaction and idempotent IDs. SQLite is suitable for local research/prototyping; scheduled GitHub-hosted runners are ephemeral, so production records need a durable external database or an explicitly managed persistent artifact store. Do not rely on a local SQLite file disappearing with the runner.

**Whole-plan review:** The outcome evaluator cannot be implemented correctly before the ledger exists. The database must not become a reason to commit secrets or personal inbox details to Git.

**Roadmap update / gate:** FM-1 signal ledger. Schema migration, uniqueness, restart, concurrent-run and data-retention tests pass; the same signal cannot be inserted twice.

### Cycle 04 — Outcome replay and independent adjudication

**Gap identified:** No process measures whether a prior BUY/SELL alert moved in the suggested direction or hit targets/stops.

**Implementation plan:** Replay each immutable signal against subsequent market data at 5, 15, 20, 30, 60 and 120 minutes plus the signal's stated horizon. Record first barrier touched, time-to-event, maximum favorable excursion (MFE), maximum adverse excursion (MAE), close-to-close return, net R, expiry and whether entry was realistically reachable after alert latency. Use explicit fill rules and executable quote side. If stop and target are both touched inside one OHLC bar and the tick path is unavailable, label the result **ambiguous**; do not assume the favorable order. Report gross and net outcomes separately.

**Whole-plan review:** This is a signal-quality evaluator, not a claim about a user's real broker fill. Store simulated outcome separately from any voluntarily reported live fill. Missing historical candles remain unknown rather than being backfilled with guesses.

**Roadmap update / gate:** FM-1 outcome engine. Unit tests cover both barrier orders, gaps, expired entries, late alerts, partial targets, ambiguous bars, missing data and all supported holding horizons.

### Cycle 05 — Executable price and transaction-cost realism

**Gap identified:** A one-minute candle close is not a guaranteed executable entry. The current stops/targets omit the spread and slippage.

**Implementation plan:** Add broker- or account-specific top-of-book pricing for the intended execution venue. For BUY, simulate entry at ask and exit at bid; for SELL, entry at bid and exit at ask. Timestamp both sides, store spread in pips and relative to ATR, and measure quote age. Add conservative slippage, latency and fee assumptions, with sensitivity scenarios. Do not call a generic data-vendor mid-price an executable quote. If the selected provider cannot supply historical bid/ask data, mark historical net outcomes as estimated and keep confidence lower.

**Whole-plan review:** FX is OTC and fragmented. The BIS describes a decentralised market with multiple venues and extensive dealer internalisation; consequently, the user's broker quote is more relevant to execution-cost validation than an assumed universal consolidated price.

**Roadmap update / gate:** FM-2 execution realism. A backtest cannot be promoted unless it remains viable under realistic spread/slippage stress tests and the broker-feed mismatch is measured.

### Cycle 06 — Indicator correctness and feature-contract audit

**Gap identified:** Custom indicator formulas and the 15-minute higher-timeframe proxy need reproducible definitions. A formula mismatch can invalidate parameter comparisons.

**Implementation plan:** Select canonical definitions for EMA, Wilder RSI, Wilder ATR and Wilder ADX; add golden-vector tests against a trusted implementation and edge-case tests for flat, discontinuous and incomplete series. Build a genuine 60-minute bar series for the high-timeframe trend. Keep the old features under a versioned baseline so changes can be compared, not silently substituted. Add feature values and missing-data flags to every ledger row.

**Whole-plan review:** Do not "improve" a strategy by changing indicator formulas and thresholds simultaneously. Separate formula parity, feature ablation and threshold experiments to identify which change explains any performance delta.

**Roadmap update / gate:** FM-3 technical baseline. Reference parity tests and reproducible feature snapshots pass before any threshold retuning.

### Cycle 07 — Market-regime classification

**Gap identified:** A single breakout rule may behave differently in trend, range, volatility shock and thin-liquidity conditions.

**Implementation plan:** Add simple, interpretable regime features first: realized volatility percentile, ATR expansion/contraction, directional efficiency/trend strength, range compression, session, spread percentile and event proximity. Classify trend, range, breakout/transition, shock and low-liquidity states. Initially use regimes as reporting slices and hard data-quality/risk gates; only later test regime-specific strategy variants. A no-trade regime is a valid output.

**Whole-plan review:** A complex regime model can overfit quickly. Compare against a simple unconditional baseline and measure whether the regime label adds out-of-sample net R after costs.

**Roadmap update / gate:** FM-3 regime layer. Report performance and coverage by regime, pair and session; enable regime-dependent thresholds only when a pre-registered out-of-sample test supports them.

### Cycle 08 — Currency-strength and cross-pair structure

**Gap identified:** The current eight-pair average is a rough strength proxy; correlated pair signals may be mistaken for independent confirmations.

**Implementation plan:** Build currency strength from timestamp-aligned log returns with pair orientation handled explicitly. Use a weighted least-squares currency-factor estimate across a sufficiently connected pair universe, weighting by liquidity/data quality and normalizing volatility. Report coverage and uncertainty. Add pair-correlation and shared-currency exposure features. Keep strength confirmation independent from the same breakout return to avoid double-counting evidence.

**Whole-plan review:** Do not make the watchlist larger just to create a more convincing index. First test whether broader pair coverage improves the stability and predictive value enough to justify data credits and costs.

**Roadmap update / gate:** FM-3 currency-factor model. Sign/orientation tests, missing-pair tests, and ablation tests must pass; the measure must improve out-of-sample results net of data and trading costs.

### Cycle 09 — Economic calendar and event schedule

**Gap identified:** The scanner has no event calendar, although the model and email explicitly tell the operator to check news manually.

**Implementation plan:** Add an event interface that normalizes currency, country, event, scheduled timestamp, source, importance, forecast, prior, actual, revision, publication timestamp and update timestamp. Start with central bank decisions/speeches, inflation, employment, GDP, retail sales and PMI releases for USD, EUR, GBP, JPY, CHF, AUD, NZD and CAD. Cross-check official release calendars and a commercial consensus provider; record source freshness and provider outage status. Preserve original timezones and daylight-saving changes.

**Whole-plan review:** Official sources are authoritative for the release itself, but frequently do not supply market consensus. A forecast/consensus source is a distinct dependency and must be licensed and timestamped.

**Roadmap update / gate:** FM-4 calendar. Tests cover daylight-saving changes, moved releases, duplicate updates, cancellation, missing consensus and stale calendar data.

### Cycle 10 — Macro surprise and policy-differential features

**Gap identified:** A headline-only bullish/bearish label misses what matters most at release time: the actual result relative to expectations, revisions and the policy path.

**Implementation plan:** Compute standardized surprises such as (actual minus consensus) divided by a historical dispersion estimate, with event-specific sign conventions and separate revision surprises. Add changes in rate expectations/yield differentials, inflation/growth momentum and central-bank reaction-function context only when point-in-time data is available. Use source publication time and vintage-aware data; never use a later revised macro value in a historical replay. Retain event-specific and currency-specific features instead of one global "fundamental score."

**Whole-plan review:** The AEA research on FX announcement effects finds that macro surprises are associated with conditional exchange-rate jumps and sign/timing effects. This supports an event-surprise feature, not an assumption that the first price jump is safely tradable. Event reaction, spread widening and liquidity recovery must be tested together.

**Roadmap update / gate:** FM-4 macro layer. Point-in-time replay and revision tests pass; feature value must be incremental to technical and event-risk baselines.

### Cycle 11 — News ingestion, provenance and deduplication

**Gap identified:** No verified headline feed exists. Searching the open web during the five-minute scan would not provide a reliable, point-in-time news tape.

**Implementation plan:** Create a provider-neutral news adapter and compare candidate vendors on currency coverage, first-published timestamp, update/correction history, latency, historical backfill, source attribution, syndication detection, API quotas, cost and redistribution/licensing rights. Ingest headlines and metadata before they enter the decision process. Deduplicate syndicated headlines and preserve a canonical story ID plus source list. Maintain an outage/staleness state.

**Whole-plan review:** Do not choose a vendor on marketing claims or headline volume. A feed that is fast but lacks historical point-in-time snapshots cannot validate a news strategy. Provider choice should follow a small latency/coverage/cost pilot.

**Roadmap update / gate:** FM-4 news data. Provider scorecard and a historical availability test are signed off before purchase or production use.

### Cycle 12 — Currency-aware headline interpretation

**Gap identified:** A generic sentiment score can miss whether a story strengthens the base or quote currency, is already priced in, or has ambiguous market implications.

**Implementation plan:** Convert each story into strict structured output: affected currency/currencies, event/entity, direction for each currency, polarity, likely horizon, novelty, importance, confidence, source quality, evidence spans, event linkage and uncertainty. Distinguish fact from commentary and confirmed information from rumor. Detect duplicate/syndicated articles. Decay relevance over a learned/tested horizon. Use an LLM for extraction and summarization with a source-backed schema; never let it invent missing facts or independently authorize a trade.

**Whole-plan review:** LLM sentiment is a noisy feature, not alpha by default. Retain raw headlines, structured output, model/prompt version and evidence references to measure its incremental contribution and diagnose model drift.

**Roadmap update / gate:** FM-4 sentiment. Human-labeled sample evaluation, currency-direction confusion matrix, source attribution checks and leakage-free historical replay pass before it influences a signal score.

### Cycle 13 — Event/news risk gate and multi-source fusion

**Gap identified:** Even a correct directional headline can coincide with volatility, spread expansion or poor liquidity that makes a short-horizon entry uneconomic.

**Implementation plan:** Build a separate event-risk gate from the directional sentiment score. Use configurable pre/post release windows by currency/event class, current spread percentile, volatility shock and feed health. Make the initial policy conservative: if a high-impact release is imminent, the feed is stale, the source is unavailable or price/spread quality cannot be verified, suppress ACTIONABLE alerts and record DATA_BLOCKED. Later estimate event-specific windows using historical data. Combine technical, macro, headline, volatility and cost features without allowing a strong score in one layer to cancel a hard risk veto.

**Whole-plan review:** This resolves the tension between more signals and more safety: a WATCH alert may be issued ahead of an event, but a trade-ready email must wait for the cost/risk gate. A missing news feed must never be interpreted as "no news."

**Roadmap update / gate:** FM-4 fusion. Event-day vs non-event-day outcomes, spread behavior and false-veto rates must be reported.

### Cycle 14 — Evidence score and calibrated probability

**Gap identified:** The AI's HIGH/MEDIUM grade is not a win probability and there is no evidence that one grade outperforms another.

**Implementation plan:** Replace qualitative confidence as the ranking criterion with a transparent feature-based baseline model after sufficient labelled outcomes exist. Predict distinct outcomes: T1 before stop, T2 before stop, stop first, expiry without barrier, and expected net R over a stated horizon. Calibrate probabilities using a strictly held-out calibration set; evaluate reliability diagrams, Brier score and log loss, alongside discrimination and net utility. Show confidence intervals and sample size. Use pair/regime/session features only if they generalize. Keep a human-readable reason code.

**Whole-plan review:** A probability is only permitted after calibration and monitoring. Do not turn LLM confidence into 80% by relabeling it. Small segment samples should be pooled or suppressed rather than shown as precise-looking probabilities.

**Roadmap update / gate:** FM-5 probabilistic ranker. It must beat simple base-rate and technical baselines on untouched time periods, remain calibrated after costs and pass drift checks before its probabilities appear in emails.

### Cycle 15 — Entry selection, expiry and lifecycle management

**Gap identified:** The current breakout signal is tied to a completed bar and a current one-minute close, while the model supplies a holding horizon. The alert has no formal time-to-live or executable entry-fill lifecycle.

**Implementation plan:** Treat breakout continuation, breakout retest, pullback continuation and range reversion as separate hypotheses. Test entry at next executable quote, retest limit, pullback trigger and time-delay alternatives. Add a hard expiry, price-deviation cap, invalidation level, pending/triggered/expired/invalidated/closed status and amended-alert rules. Optimize stop/target placement in net R by volatility regime and pair; preserve a stable baseline. Do not allow the LLM to edit risk levels.

**Whole-plan review:** More frequent WATCH alerts can improve awareness without diluting the ACTIONABLE threshold. Entry improvements must be tested jointly with spread, slippage and latency, not on mid-price candles alone.

**Roadmap update / gate:** FM-5 entry engine. Every entry variant is compared out-of-sample with the next-quote baseline and must report unfilled/expired signals as well as wins and losses.

### Cycle 16 — Portfolio and correlated-exposure controls

**Gap identified:** Selecting one candidate per scan reduces simultaneous alert volume but does not prevent a later run or another pair from issuing the same underlying currency bet.

**Implementation plan:** Maintain a live paper-position/alert exposure ledger. Estimate directional currency exposure, pair correlation, common USD/JPY/EUR themes, aggregate risk and overlapping holding windows. Add configurable limits for concurrent positions, per-currency exposure, daily loss and drawdown. Avoid duplicate or contradictory alerts and prioritize by incremental portfolio value rather than isolated pair score. Keep account-specific sizing disabled until broker/account risk settings are explicitly configured.

**Whole-plan review:** A high win-rate pair strategy can still create clustered drawdowns from correlated signals. Portfolio evaluation must use synchronized outcomes and stress periods, not only isolated trade statistics.

**Roadmap update / gate:** FM-5 portfolio risk. Exposure limits, duplicate-signal tests and correlated shock scenarios pass before concurrent actionable alerts are enabled.

### Cycle 17 — Research-grade backtesting and anti-overfitting controls

**Gap identified:** No backtest, walk-forward test, untouched holdout or multiple-testing correction is implemented. Repeated tuning across pairs, indicators and windows can select noise.

**Implementation plan:** Build a reproducible event-driven replay engine. Use chronological train/validation/test periods and rolling or anchored walk-forward; purge and embargo observations whose outcome windows overlap. Maintain an untouched final holdout. Compare every feature and layer via ablation against simple baselines. Track the number of attempted variants; use Probability of Backtest Overfitting / combinatorial symmetric cross-validation and Deflated Sharpe Ratio as research diagnostics, plus block-bootstrap confidence intervals for net expectancy. Test multiple regimes and periods with realistic spreads, slippage, latency, gaps and ambiguous-bar handling.

**Whole-plan review:** No single validation statistic proves a strategy is profitable. CPCV/PBO/DSR are complements to forward chronological testing, not substitutes for a future paper-trading period. An improvement is accepted only if its benefit survives out-of-sample and cost stress tests.

**Roadmap update / gate:** FM-6 validation. Publish reproducible run config, data hashes, all trials, baseline comparison and holdout report; no production promotion on in-sample performance alone.

### Cycle 18 — Frequency, scheduling and feed architecture

**Gap identified:** The current GitHub Actions design scans at five-minute intervals and consumes a full eight credits/minute in a single eight-symbol batch on Twelve Data's Basic quota. GitHub schedules are best-effort. This architecture cannot guarantee tick-level immediacy.

**Implementation plan:** Keep the current five-minute process as a bounded baseline while measuring run start lag, duration, data age, API usage and scan-to-email latency. Stagger the cron phase away from minute zero to reduce exposure to documented GitHub high-load periods, then confirm that freshness limits still pass. Add quota reservations, provider backoff, cached reference data and one-request-per-needed-refresh behavior. For truly faster alerts, evaluate a persistent worker using a supported WebSocket or broker pricing stream; compare connection reliability, message coverage, subscription credits, hosting cost and legal data rights. Do not move to one-minute polling or 24/5 scanning until quotas and economics are proven.

**Whole-plan review:** The current schedule is correct in using an IANA timezone; GitHub now supports timezone-aware schedule entries. The reliability concern is scheduler delay/drop behavior, not the timezone field. On the current Basic Twelve Data plan, eight symbols consume eight credits for the batched call. Extra endpoints or same-minute retries need reserved headroom or a different plan/provider.

**Roadmap update / gate:** FM-6 market-data operations. Demonstrate agreed p95/p99 scan-to-email latency, quote freshness, quota headroom, reconnect behavior and monthly cost before expanding hours or pairs.

### Cycle 19 — Reliable notifications and incident handling

**Gap identified:** The current issue marker plus SMTP flow has an ambiguous retry window and lacks end-to-end delivery telemetry.

**Implementation plan:** Implement an alert outbox with deterministic alert ID, pending/attempted/SMTP-accepted/failed/ambiguous/reconciled states, attempt timestamp, provider response code and retry schedule. Set a stable Message-ID and alert ID header. Do not claim exactly-once SMTP delivery; reconcile ambiguous acceptance before retry where possible. Add dead-letter handling, email test run audit, alert latency measurement, issue-comment URL, provider outages and daily heartbeat. Separate test emails from market alerts.

**Whole-plan review:** SMTP acceptance means the server accepted responsibility for the message, not guaranteed inbox placement or human receipt. The app should distinguish generated, sent/accepted, bounced (where available) and user-acknowledged states. Notification success must never change a trade's statistical outcome.

**Roadmap update / gate:** FM-6 notification reliability. Inject SMTP timeout, provider rejection, GitHub API timeout and retry-after-acceptance failures; demonstrate that duplicates are detected/reconciled and every alert is traceable.

### Cycle 20 — Release governance and final whole-roadmap review

**Gap identified:** More components increase model, vendor, data, maintenance and false-positive risk. Without staged promotion, experiments can silently change production decisions.

**Implementation plan:** Separate baseline production, shadow experiments and paper-trading candidate versions. Version strategy config, prompts, schemas, datasets, provider adapters and releases. Require review of test results, data quality, cost, security, rollback and model drift before changing the active version. Keep a kill switch and automatic fail-closed behavior for stale prices, missing calendar/news, invalid model JSON, quota exhaustion and risk-limit breaches. Publish weekly and monthly scorecards.

**Whole-plan review:** Rechecked all 20 plans as one dependency graph. The critical path is: operational truth → point-in-time data → durable ledger → outcome evaluator → executable prices/costs → feature/regime baselines → fundamentals/news → calibrated ranking → portfolio controls → forward validation → controlled promotion. News sentiment and ML scoring must not jump ahead of measurement and execution realism.

**Roadmap update / gate:** FM-6 governance. Production promotion requires reproducible evidence, signed-off costs, calibrated performance, operational SLOs, rollback and a paper-trading release gate.

## 4. Consolidated implementation roadmap

The 20 cycles converge on the following ordered work packages. This order is intentional; downstream work depends on upstream evidence.

| Priority | Work package | Main deliverables | Exit / acceptance gate |
|---|---|---|---|
| **P0** | Operational verification and baseline | Confirm enable gate, current Actions behavior, manual SMTP test, run heartbeat, scan/latency/error baseline | A scan, a no-trade scan, a skipped run, a failed data run and an email test are distinguishable and observable |
| **P1** | Data contracts, immutable signal ledger and outcome replay | Versioned schemas; all-candidate logging; decision snapshots; outcome evaluator; MFE/MAE; expiry and ambiguity labels | Reproducible signal replay and automated outcome tests; no guessed historical outcomes |
| **P2** | Quote/execution realism | Broker bid/ask feed; spread, slippage, latency and cost model; price-source comparison | Strategy remains viable under realistic cost and stress scenarios |
| **P3** | Technical baseline and market context | Indicator reference parity; true 1h bars; regime classification; currency-factor model; pair correlation | Feature ablation demonstrates out-of-sample incremental value |
| **P4** | Fundamental and news data | Calendar adapter; consensus/surprise/revisions; licensed headline feed; currency-aware sentiment; event-risk gate | Point-in-time replay, source provenance, event-window tests and human-reviewed classification quality |
| **P5** | Ranking, entry and portfolio intelligence | Calibrated outcome model; expected net R; entry variants; expiry/lifecycle; exposure and risk controls | Beats simple baselines out-of-sample and remains calibrated after costs; portfolio limits tested |
| **P6** | Research validation and production reliability | Walk-forward/holdout/PBO/DSR reports; quota guard; scheduler/feed reliability; transactional-style outbox; dashboards; rollback | Forward paper test passes pre-registered criteria and operational SLOs before any live strategy change |

### Critical dependency graph

1. P0 provides operational truth and baseline telemetry.
2. P1 depends on P0; P2 and P3 depend on P1.
3. P4 can be developed in parallel with P2/P3, but cannot influence ACTIONABLE alerts until P1 point-in-time capture and P2 cost/quote gates exist.
4. P5 depends on labelled outcomes from P1, cost-aware data from P2, and tested features from P3/P4.
5. P6 validates every candidate before promotion and remains active as a continuous release gate.

## 5. Decision policy and success metrics

### Optimize a balanced objective

Measure both opportunity volume and economic quality. Do not optimize a raw win rate or alert count in isolation.

**Primary outcome measures**
- Net expectancy per filled simulated signal, in R, after spread/slippage/fees.
- Net R per active session/day and drawdown distribution.
- Profit factor, average win/loss, tail loss and time-to-target/stop.
- MFE, MAE and missed-entry/expiry rates.

**Signal and model quality**
- Candidate-to-ACTIONABLE conversion and false-positive rate.
- Signal count by pair, direction, hour, session, volatility regime and event class.
- Brier score, log loss and calibration/reliability diagrams for each predicted outcome, once probabilities are permitted.
- Incremental effect from technical, regime, currency-strength, calendar, news and cross-market features via ablation.

**Operational quality**
- Scan schedule lag, quote age, data completeness, API quota, processing time and p50/p95/p99 alert latency.
- Email generated, SMTP accepted, failed, ambiguous, reconciled and duplicate counts.
- News/calendar freshness and source outages.

Use confidence intervals and effective sample size. Because adjacent five-minute signals and multi-pair trades overlap, 1,000 alerts do not necessarily represent 1,000 independent market opportunities. Set promotion sample sizes based on desired confidence-interval precision and the number of independent event/regime clusters; do not use an arbitrary raw signal-count threshold.

### Hard rules

- No actionability from stale, incomplete or source-unverified prices.
- No ACTIONABLE alert when a required risk feed is missing or stale.
- No performance claims from the LLM's qualitative HIGH/MEDIUM grade.
- No historical outcome inferred from a single candle when stop/target order is ambiguous.
- No use of revised macro data or later headlines in historical decision-time replay.
- No production threshold change based solely on in-sample optimization.
- No strategy promotion unless net expectancy after costs clears a pre-registered practical threshold in untouched chronological tests and a forward paper period.
- No live broker order placement is included in this roadmap.

## 6. Provider and architecture decisions

Do not choose all providers up front. Run small, measurable pilots.

**Market prices:** Compare Twelve Data with the intended broker's own pricing interface and one independent source. Confirm historical granularity, bid/ask availability, timestamp semantics, pair coverage, rate limits, outages, licensing and historical retention. For a live alert, broker bid/ask is the relevant execution reference. Twelve Data can remain a research/secondary feed if its use rights and quotas are suitable.

**Economic events:** Prefer official release sources for publication time and actual values; use a consensus-data provider for forecast expectations. Store both and preserve the event's point-in-time revision history. ALFRED's release calendar and vintage-aware history can support US macro-data reconstruction, but it is not a complete consensus calendar for all eight FX currencies.

**News:** Compare ForexNewsAPI, FXStreet and Financial Modeling Prep as candidates only. Evaluate actual latency, original publication timestamp, update/correction history, global currency coverage, historical backfill, source quality, quota/cost and commercial/non-display/redistribution licensing. A data contract should be signed off before integrating the feed.

**Persistence:** Use SQLite for local research and deterministic test fixtures. Use a durable managed database for the scheduled/hosted process. The GitHub Actions runner's local filesystem is not a durable signal store.

**Decision logic:** Keep market-data parsing, deterministic technical candidate generation, economic/news feature extraction, event-risk gates, calibrated ranking, portfolio risk and email delivery as separate modules. The LLM may summarize source-backed news or explain why a candidate was vetoed; it must not be the sole trade selector or invent prices, probabilities, news or risk levels.

## 7. Research basis and sources

Research was used to shape hypotheses and validation controls; it does not establish that any proposed feature will be profitable on this scanner's 5-minute horizon.

1. **FX market structure and execution:** BIS, *The FX trade execution landscape through the prism of the 2025 BIS Triennial Survey* (2025). Describes the OTC, decentralised and fragmented market and dealer internalisation. This motivates account-specific bid/ask validation rather than assuming one universal executable price.  
   https://www.bis.org/publications/qr-202512/fx-trade-execution-landscape-through-prism-2025-bis-triennial-survey
2. **Macro announcement effects:** Andersen, Bollerslev, Diebold and Vega, *Micro Effects of Macro Announcements: Real-Time Price Discovery in Foreign Exchange*, American Economic Review (2003). Finds macro announcement surprises are associated with conditional mean jumps in exchange rates, with timing and sign effects.  
   https://www.aeaweb.org/articles?id=10.1257/000282803321455151
3. **Liquidity recovery after news:** Yamada and Ito, NBER Working Paper 27036 (2020), *Price Discovery and Liquidity Recovery: Forex Market Reactions to Macro Announcements*. Supports measuring price discovery and liquidity recovery jointly after macro releases.  
   https://www.nber.org/papers/w27036
4. **Technical rules are not a guarantee:** Hsu, Taylor and Wang, *Technical Trading: Is It Still Beating the Foreign Exchange Market?*, Journal of International Economics (2016). The large historical study reports profitability variation across periods, consistent with adaptive-market behavior; it is not proof for this scanner's intraday rule.  
   https://doi.org/10.1016/j.jinteco.2016.03.012
5. **Technical-analysis research pitfalls:** Park and Irwin, *What Do We Know About the Profitability of Technical Analysis?* (2007). Reviews data snooping, ex-post rule selection and transaction-cost estimation problems.  
   https://doi.org/10.1111/j.1467-6419.2007.00519.x
6. **Backtest overfitting:** Bailey, Borwein, López de Prado and Zhu, *The Probability of Backtest Overfitting* (2017). Proposes combinatorially symmetric cross-validation to estimate selection-induced backtest overfitting.  
   https://doi.org/10.21314/JCF.2016.322
7. **Selection bias and non-normality:** Bailey and López de Prado, *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality* (2014). Motivates recording the full number of trials and adjusting research conclusions for selection bias.  
   https://doi.org/10.3905/jpm.2014.40.5.094
8. **Validation method comparison:** Arian, Norouzi Mobarekeh and Seco, *Backtest overfitting in the machine learning era* (Knowledge-Based Systems, 2024). Compares out-of-sample methods under synthetic controlled conditions; useful evidence for adding PBO/DSR diagnostics, not a universal guarantee that one split technique is best.  
   https://doi.org/10.1016/j.knosys.2024.112477
9. **Probability calibration:** scikit-learn documentation on calibration curves, Brier score and log loss. A predicted probability should match observed frequencies on held-out data; a lower overall Brier score alone does not prove calibration is better.  
   https://scikit-learn.org/stable/modules/calibration.html
10. **Intraday FX seasonality:** Ito and Hashimoto, NBER Working Paper 12413 (2006). Documents intraday differences in activity, volatility and spreads, supporting pair/session-specific measurement instead of a universal time filter.  
    https://www.nber.org/papers/w12413
11. **Data cost and batching:** Twelve Data's current pricing and batch-request documentation lists Basic quota limits and states that batched requests consume credits per symbol. Recheck plan and weights before increasing scan coverage.  
    https://twelvedata.com/pricing  
    https://support.twelvedata.com/en/articles/5203360-batch-api-requests
12. **Scheduler reliability and timezone:** GitHub Actions schedule documentation states the minimum five-minute interval, timezone support and best-effort delay/drop conditions.  
    https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax  
    https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
13. **Point-in-time macro history:** St. Louis Fed ALFRED release calendar and data vintage references. Useful for tracking release schedules and avoiding revised-value look-ahead in US macro research.  
    https://alfred.stlouisfed.org/releases/calendar  
    https://fred.stlouisfed.org/docs/api/fred/

## 8. Final review outcome

The final whole-plan review found no reason to start by changing the current thresholds, broadening the pair list, increasing the scan frequency, or weighting AI/news sentiment more heavily. Those changes would make the signal stream busier before the system can measure whether the additional alerts are economically useful.

**Recommended first implementation slice:** P0 plus the first portion of P1 — verify operational status, add a durable append-only signal/candidate ledger, persist exact decision-time snapshots and versions, then build the first outcome replay evaluator. Leave the live candidate rules, alert thresholds, schedule and broker behavior unchanged during this slice.

**Promotion principle:** Only measured improvements that survive realistic costs, chronological out-of-sample validation and forward paper trading should alter ACTIONABLE notifications. The system should increase signal frequency only when the additional opportunities improve net results without violating risk and reliability limits.
