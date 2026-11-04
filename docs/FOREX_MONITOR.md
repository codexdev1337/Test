# Five-minute AI-reviewed major-FX monitor

## What it does

The GitHub Actions workflow scans eight liquid pairs every five minutes on weekdays from 06:00 through 10:55 America/Chicago:

- EUR/USD, GBP/USD, USD/JPY, USD/CHF
- AUD/USD, NZD/USD, USD/CAD
- EUR/GBP

It is a two-stage decision system:

1. **Deterministic market screen.** Fetches 1-minute candles, builds completed 5-minute/15-minute bars, rejects stale/incomplete data, checks 5m/15m trend alignment plus a slower higher-timeframe EMA proxy, RSI, ADX, candle body/close location, volatility expansion, breakout quality, extension from the trigger, and 30-minute relative currency strength across the pair set.
2. **GPT decision review.** Only if at least one setup survives the hard technical gates, GPT reviews every surviving candidate alongside the eight-pair snapshot and currency-strength context. It can select one candidate or reject every candidate with NO_TRADE. It must consider contradictory pair signals, weak trend/momentum, late entries, missing spread/news verification, and risk context.

The model is deliberately constrained: it cannot invent a trade, choose a pair that did not pass the scanner, change direction, or edit the scanner's entry, stop, and target levels. The model must return a qualitative HIGH or MEDIUM grade to trigger an alert. These grades are not probabilities and have not been calibrated to win rates.

The default model is \`gpt-6-luna\`. The workflow calls the OpenAI Responses API directly. This is a separate API integration and is billed according to API usage; a ChatGPT subscription does not include API credits.

## Enable it

The default branch already contains the scanner, model gate, workflow, and tests. To activate:

1. Create a Twelve Data account and obtain a market-data API key: https://twelvedata.com/forex
2. Create an OpenAI API key with access to the Responses API: https://platform.openai.com/api-keys
3. Open **Settings → Secrets and variables → Actions → Secrets → New repository secret**.
4. Add secret \`TWELVE_DATA_API_KEY\` with the Twelve Data key.
5. Add secret \`OPENAI_API_KEY\` with the OpenAI API key.
6. Under **Settings → Secrets and variables → Actions → Variables**, create repository variable \`FOREX_MONITOR_ENABLED\` with value \`true\`.
7. Confirm GitHub Actions is enabled. Subscribe to issue #1 for alert notifications: https://github.com/codexdev1337/Test/issues/1
8. Use **Actions → Forex major-pair monitor → Run workflow** to run the test and first scan.

Do not paste either secret into chat, source files, issue comments, or workflow YAML. Enter them only into GitHub's secret fields. The workflow is gated off until \`FOREX_MONITOR_ENABLED=true\`.

## Email alerts

The scanner sends an email only after a **new** candidate passes the deterministic filters and receives a HIGH or MEDIUM AI approval. A `NO_TRADE` decision, a scan with no candidate, or a previously emailed candidate does not generate another email. The alert is first recorded in issue #1; an email-delivery marker is stored on that issue comment so a failed SMTP attempt can be retried on a later scan.

Add these repository secrets under **Settings → Secrets and variables → Actions → Secrets**:

| Secret name | Value |
|---|---|
| `SMTP_HOST` | Your mailbox provider's SMTP server hostname |
| `SMTP_PORT` | `587` for STARTTLS or `465` for implicit TLS |
| `SMTP_USERNAME` | Full email address used to authenticate |
| `SMTP_PASSWORD` | Mailbox SMTP password or provider-issued app password |
| `ALERT_EMAIL_TO` | Address that should receive the alerts |
| `ALERT_EMAIL_FROM` | Optional sender address; defaults to `SMTP_USERNAME` |

Use a provider-issued app password where your mail provider requires one. Never put the SMTP password in a repository file or issue comment. The sender and recipient addresses are not printed to workflow logs.

### Test Gmail delivery without waiting for a trade

1. Open **Actions → Forex major-pair monitor → Run workflow**.
2. Select branch `main`.
3. Tick **Send a test email instead of scanning the market** (`email_test`).
4. Click **Run workflow**.
5. Open the run. The step **Send Gmail SMTP test email** should complete successfully and the log should say that Gmail accepted the message for delivery.
6. Check the recipient inbox and Spam folder for **TEST ONLY — Forex Monitor Gmail delivery check**.

A test run sends one clearly labelled test message and skips the live market scan. Leave the checkbox unticked for normal manual scans. Scheduled scans are unaffected and continue to email only new AI-approved candidates.


## Decision and risk rules

- 5m, 15m and slower higher-timeframe trend proxies must agree.
- A candidate must show a 12-bar 5-minute range breakout, directional candle body and close location, RSI confirmation, ADX at or above the minimum trend threshold, and a volatility expansion that is neither too weak nor excessively spiky.
- 30-minute signed pair returns are combined into a rough relative currency-strength context; the base currency must be stronger than the quote for a buy, and vice versa for a sell.
- Price must remain close to the completed breakout candle; extended moves are rejected rather than chased.
- Stop distance is 1.15 × ATR(14), with a 6-pip minimum. Targets are 1R and 2R. These are mechanical risk levels, not evidence of a profitable strategy.
- The LLM may veto all candidates. If the API key is absent, the API fails, structured output is invalid, or the model selects anything outside the candidate list, the scan fails closed and sends no trade alert.
- Alerts are deduplicated by pair, direction and breakout candle.

## Important limitations

- The candle feed does not provide the user's broker executable bid/ask spread. Spread must be checked manually before entry.
- No economic calendar or live news feed is connected. Scheduled event risk is therefore unknown and must be checked manually. The model is instructed not to invent news or claim the calendar is safe.
- The 30-minute currency-strength calculation is a rough cross-pair context signal, not an institutional currency index.
- The scanner is not backtested or forward-validated. A model's qualitative confidence is not a statistical probability of success. Record paper-trading results before risking capital.
- The workflow never connects to a broker and cannot submit or manage orders.
- GitHub documents five-minute scheduled workflows but warns that runs can be delayed or dropped during heavy load. Treat this as best-effort alerts, not hard real-time market monitoring.
- The schedule runs 60 scans per weekday. Eight time-series symbols consume approximately 480 Twelve Data credits per full weekday schedule, assuming the current one-credit-per-symbol batch pricing. Verify current account quotas and actual usage.
- At one billed Actions minute per scan, a 23-weekday month would use about 1,380 minutes. Actual usage can be higher if jobs take longer or are manually rerun.

## Operator links

- Alert thread: https://github.com/codexdev1337/Test/issues/1
- Workflow: https://github.com/codexdev1337/Test/actions/workflows/forex-major-pair-monitor.yml
- Scanner: ../forex-monitor/scan.py
- AI decision gate: ../forex-monitor/decision_engine.py
- Offline tests: ../forex-monitor/test_scan.py and ../forex-monitor/test_decision_engine.py
