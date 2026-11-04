# Five-minute major-FX monitor

## What it does

A GitHub Actions workflow scans these pairs during the weekday London/New York trading window:

- EUR/USD, GBP/USD, USD/JPY, USD/CHF
- AUD/USD, NZD/USD, USD/CAD
- EUR/GBP (liquid cross-pair)

The scan schedule is every five minutes from 06:00 through 11:55 America/Chicago, Monday through Friday. It posts a comment to issue #1 only when a **new** rule-based setup passes the filters. No-trade scans remain in the Actions run logs, avoiding a notification every five minutes.

This is a conditional technical scanner, not a broker, not an execution bot, and not a validated promise of positive expectancy. It never submits orders.

## Enable it

1. Create a free Twelve Data account and obtain an API key: https://twelvedata.com/forex
2. In this private repository, open **Settings → Secrets and variables → Actions → Secrets → New repository secret**.
3. Name the secret `TWELVE_DATA_API_KEY` and paste the key into GitHub's secret field. Do not commit the key or paste it into chat.
4. Under **Settings → Secrets and variables → Actions → Variables**, create repository variable `FOREX_MONITOR_ENABLED` with value `true`.
5. Confirm GitHub Actions is enabled for the repository. The workflow file is already on the default branch.
6. Subscribe to issue #1 to receive notifications when a fresh setup is posted: https://github.com/codexdev1337/Test/issues/1
7. Use **Actions → Forex major-pair monitor → Run workflow** to test it after enabling.

Until the variable is set to `true`, scheduled runs skip the job. This prevents runner usage before the API key is installed.

## Signal logic

The scanner fetches one batch of 1-minute candles for all eight symbols and constructs completed 5-minute and 15-minute bars. A new alert requires:

- 5-minute EMA(9) / EMA(21) aligned with direction;
- 15-minute EMA(9) / EMA(21) aligned with direction;
- a close beyond the preceding 12 completed 5-minute bars' high/low;
- RSI(14) confirmation (55–72 for buys; 28–45 for sells);
- a fresh, recent candle and a latest indicative price that has not run materially away from the signal close.

Stops are 1.2 × ATR(14), with a 6-pip minimum. Targets are 1R and 1.8R. The alert includes candle timestamps and a stale-price guard. These are transparent screening rules, not a claim that the signals have been backtested or are profitable.

## Usage and reliability

- Twelve Data's Basic tier currently lists 800 API credits per day. A batch time-series request costs one credit per symbol, so eight symbols × 72 scans = about 576 credits per full weekday schedule. Check your account dashboard for actual quota and usage.
- The six-hour schedule is 72 runs per weekday. In a private repository, GitHub-hosted Actions minutes are quota-limited; on GitHub Free the published allowance is 2,000 minutes/month. At one billed minute per run, a 23-weekday month would use about 1,656 minutes, before manual reruns or runs longer than one minute.
- GitHub documents the five-minute minimum for scheduled workflows, but also warns scheduled events can be delayed during heavy load or dropped. The scanner is therefore **best-effort**, not a hard real-time five-minute service.
- FX candle closes are indicative vendor data and are not your broker's executable bid/ask. Spread, slippage, feed differences, news, and stale prices can invalidate an alert. Check the broker quote and calendar before trading.
- The workflow has issue-comment write permission only; it has no brokerage credentials and cannot place trades.

## Operator links

- Alert / notification thread: https://github.com/codexdev1337/Test/issues/1
- Workflow: https://github.com/codexdev1337/Test/actions/workflows/forex-major-pair-monitor.yml
- Scanner implementation: ../forex-monitor/scan.py
