#!/usr/bin/env python3
"""Five-minute, rules-based scanner for eight liquid FX pairs.

This script produces conditional analysis alerts only. It does not connect to a
broker, submit orders, or estimate a probability of profit.
"""
from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

SYMBOLS = (
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "NZD/USD", "USD/CAD", "EUR/GBP",
)
API_URL = "https://api.twelvedata.com/time_series"
GITHUB_API = "https://api.github.com"
USER_AGENT = "codexdev1337-forex-monitor/1.0"


@dataclass(frozen=True)
class Bar:
    start: datetime
    open: float
    high: float
    low: float
    close: float


def http_json(url: str, headers: dict[str, str] | None = None) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read()
            if len(raw) > 8_000_000:
                raise RuntimeError("Market-data response exceeded the 8 MB safety limit.")
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(500).decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code} from data/notification service: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Service returned invalid JSON.") from exc


def fetch_all_series(api_key: str) -> dict[str, list[dict[str, str]]]:
    params = urllib.parse.urlencode({
        "symbol": ",".join(SYMBOLS),
        "interval": "1min",
        "outputsize": "500",
        "format": "JSON",
        "apikey": api_key,
    })
    payload = http_json(f"{API_URL}?{params}")
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected market-data response shape.")
    if payload.get("status") == "error":
        raise RuntimeError(f"Market-data provider error: {payload.get('message', 'unknown error')}")

    result: dict[str, list[dict[str, str]]] = {}
    if isinstance(payload.get("values"), list):
        symbol = str(payload.get("meta", {}).get("symbol", "")).upper()
        if symbol:
            result[symbol] = payload["values"]
    else:
        for key, value in payload.items():
            if isinstance(value, dict) and isinstance(value.get("values"), list):
                result[str(key).upper()] = value["values"]

    missing = [symbol for symbol in SYMBOLS if symbol.upper() not in result]
    if missing:
        raise RuntimeError("No time-series data returned for: " + ", ".join(missing))
    return result


def parse_datetime(value: str) -> datetime:
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    # Twelve Data reports forex candle timestamps in UTC.
    return parsed.replace(tzinfo=timezone.utc)


def parse_rows(rows: list[dict[str, str]]) -> list[tuple[datetime, float, float, float, float]]:
    parsed = []
    for row in rows:
        try:
            parsed.append((
                parse_datetime(str(row["datetime"])),
                float(row["open"]), float(row["high"]),
                float(row["low"]), float(row["close"]),
            ))
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(parsed, key=lambda item: item[0])


def aggregate_minutes(
    rows: list[tuple[datetime, float, float, float, float]], interval_minutes: int
) -> list[Bar]:
    groups: dict[datetime, list[tuple[datetime, float, float, float, float]]] = {}
    for row in rows:
        stamp = row[0]
        minute = (stamp.minute // interval_minutes) * interval_minutes
        key = stamp.replace(minute=minute, second=0, microsecond=0)
        groups.setdefault(key, []).append(row)

    bars: list[Bar] = []
    for start, members in sorted(groups.items()):
        members.sort(key=lambda item: item[0])
        expected = interval_minutes
        actual_minutes = {item[0].minute for item in members}
        required_minutes = set(range(start.minute, start.minute + interval_minutes))
        if len(members) != expected or actual_minutes != required_minutes:
            continue
        if any(item[0].second != 0 for item in members):
            continue
        bars.append(Bar(
            start=start,
            open=members[0][1],
            high=max(item[2] for item in members),
            low=min(item[3] for item in members),
            close=members[-1][4],
        ))
    return bars


def ema(values: list[float], period: int) -> float:
    if len(values) < period:
        raise ValueError("not enough values for EMA")
    alpha = 2.0 / (period + 1.0)
    value = sum(values[:period]) / period
    for item in values[period:]:
        value = alpha * item + (1.0 - alpha) * value
    return value


def rsi(values: list[float], period: int = 14) -> float:
    if len(values) < period + 1:
        raise ValueError("not enough values for RSI")
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    window = changes[-period:]
    gains = sum(max(change, 0.0) for change in window) / period
    losses = sum(max(-change, 0.0) for change in window) / period
    if losses == 0:
        return 100.0
    relative_strength = gains / losses
    return 100.0 - (100.0 / (1.0 + relative_strength))


def atr(bars: list[Bar], period: int = 14) -> float:
    if len(bars) < period + 1:
        raise ValueError("not enough bars for ATR")
    ranges = []
    for previous, current in zip(bars[-period - 1:-1], bars[-period:]):
        ranges.append(max(
            current.high - current.low,
            abs(current.high - previous.close),
            abs(current.low - previous.close),
        ))
    return sum(ranges) / len(ranges)


def round_price(value: float, symbol: str) -> str:
    decimals = 3 if symbol.endswith("JPY") else 5
    return f"{value:.{decimals}f}"


def analyze_symbol(
    symbol: str,
    rows: list[dict[str, str]],
    now: datetime,
) -> dict[str, Any] | None:
    minute_rows = parse_rows(rows)
    if len(minute_rows) < 250:
        return None
    latest_time, _, _, _, current_price = minute_rows[-1]
    if (now - latest_time) > timedelta(minutes=3):
        return None

    bars_5m = aggregate_minutes(minute_rows, 5)
    bars_15m = aggregate_minutes(minute_rows, 15)
    if len(bars_5m) < 35 or len(bars_15m) < 22:
        return None

    last = bars_5m[-1]
    previous = bars_5m[-2]
    if now - (last.start + timedelta(minutes=5)) > timedelta(minutes=10):
        return None
    if now - (bars_15m[-1].start + timedelta(minutes=15)) > timedelta(minutes=20):
        return None

    closes_5m = [bar.close for bar in bars_5m]
    closes_15m = [bar.close for bar in bars_15m]
    fast_5m, slow_5m = ema(closes_5m, 9), ema(closes_5m, 21)
    fast_15m, slow_15m = ema(closes_15m, 9), ema(closes_15m, 21)
    momentum = rsi(closes_5m, 14)
    volatility = atr(bars_5m, 14)
    if not math.isfinite(volatility) or volatility <= 0:
        return None

    # Compare the latest completed 5m close with the previous 12-bar range.
    range_before = bars_5m[-13:-1]
    range_before_previous = bars_5m[-14:-2]
    if len(range_before) != 12 or len(range_before_previous) != 12:
        return None
    breakout_high = max(bar.high for bar in range_before)
    breakout_low = min(bar.low for bar in range_before)
    prior_high = max(bar.high for bar in range_before_previous)
    prior_low = min(bar.low for bar in range_before_previous)

    direction = None
    if (
        last.close > breakout_high
        and previous.close <= prior_high
        and fast_5m > slow_5m
        and fast_15m > slow_15m
        and last.close > fast_5m
        and 55.0 <= momentum <= 72.0
        and current_price >= breakout_high - 0.10 * volatility
    ):
        direction = "BUY"
    elif (
        last.close < breakout_low
        and previous.close >= prior_low
        and fast_5m < slow_5m
        and fast_15m < slow_15m
        and last.close < fast_5m
        and 28.0 <= momentum <= 45.0
        and current_price <= breakout_low + 0.10 * volatility
    ):
        direction = "SELL"

    if direction is None:
        return None

    # Avoid issuing an alert after price has already run materially away.
    if abs(current_price - last.close) > 0.35 * volatility:
        return None

    pip = 0.01 if symbol.endswith("JPY") else 0.0001
    risk = max(1.2 * volatility, 6.0 * pip)
    sign = 1.0 if direction == "BUY" else -1.0
    entry = current_price
    stop = entry - sign * risk
    target_1 = entry + sign * risk
    target_2 = entry + sign * 1.8 * risk

    return {
        "symbol": symbol,
        "direction": direction,
        "bar_time": last.start.isoformat(),
        "quote_time": latest_time.isoformat(),
        "entry": round_price(entry, symbol),
        "stop": round_price(stop, symbol),
        "target_1": round_price(target_1, symbol),
        "target_2": round_price(target_2, symbol),
        "risk_pips": round(risk / pip, 1),
        "atr_pips": round(volatility / pip, 1),
        "rsi": round(momentum, 1),
        "fast_5m": round_price(fast_5m, symbol),
        "slow_5m": round_price(slow_5m, symbol),
        "fast_15m": round_price(fast_15m, symbol),
        "slow_15m": round_price(slow_15m, symbol),
    }


def github_request(method: str, url: str, token: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(500).decode("utf-8", "replace")
        raise RuntimeError(f"GitHub notification request failed ({exc.code}): {detail}") from exc


def post_new_alerts(alerts: list[dict[str, Any]], token: str, repo: str, issue: str) -> int:
    comments_url = f"{GITHUB_API}/repos/{repo}/issues/{issue}/comments?per_page=100&direction=desc"
    comments = github_request("GET", comments_url, token)
    existing_text = "\n".join(str(item.get("body", "")) for item in comments)
    fresh = []
    for alert in alerts:
        marker = (
            f"<!-- forex-signal:{alert['symbol']}:{alert['direction']}:"
            f"{alert['bar_time']} -->"
        )
        if marker not in existing_text:
            alert["marker"] = marker
            fresh.append(alert)

    if not fresh:
        return 0

    sections = [
        "## New major-FX setup detected",
        "",
        f"Scan time: {datetime.now(timezone.utc).isoformat()}",
        "",
        "> Conditional technical alert only. This is not a probability estimate or a guaranteed trade. "
        "Prices are indicative 1-minute candle closes, not executable broker bid/ask quotes. "
        "Do not enter if your broker quote has moved materially or the setup is no longer valid.",
    ]
    for alert in fresh:
        sections.extend([
            "",
            f"### {alert['symbol']} — {alert['direction']}",
            f"- Indicative entry: **{alert['entry']}**",
            f"- Stop loss: **{alert['stop']}** ({alert['risk_pips']} pips risk)",
            f"- Target 1: **{alert['target_1']}** (1R)",
            f"- Target 2: **{alert['target_2']}** (1.8R)",
            f"- 5m RSI(14): {alert['rsi']}; 5m ATR(14): {alert['atr_pips']} pips",
            f"- 5m EMA(9/21): {alert['fast_5m']} / {alert['slow_5m']}",
            f"- 15m EMA(9/21): {alert['fast_15m']} / {alert['slow_15m']}",
            f"- Completed breakout candle: {alert['bar_time']}",
            f"- Latest indicative 1m price timestamp: {alert['quote_time']}",
            "- Validity: re-check immediately; discard if price has moved more than 0.35 × the 5m ATR from the signal candle close, or if the breakout has failed.",
            alert["marker"],
        ])
    sections.extend([
        "",
        "Position sizing is your responsibility. Keep risk small and account for spread, slippage, and scheduled news. "
        "The scanner never submits broker orders.",
    ])
    github_request("POST", comments_url.split("?")[0], token, {"body": "\n".join(sections)})
    return len(fresh)


def main() -> int:
    api_key = os.environ.get("TWELVE_DATA_API_KEY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    issue = os.environ.get("FOREX_ALERT_ISSUE", "1").strip()
    if not api_key:
        print("Inactive: configure the TWELVE_DATA_API_KEY repository secret.")
        return 0
    if not token or not repo or not issue.isdigit():
        raise RuntimeError("GitHub notification environment is incomplete.")

    now = datetime.now(timezone.utc)
    series = fetch_all_series(api_key)
    alerts = []
    for symbol in SYMBOLS:
        signal = analyze_symbol(symbol, series[symbol.upper()], now)
        if signal:
            alerts.append(signal)

    print(f"Completed major-FX scan at {now.isoformat()}.")
    for symbol in SYMBOLS:
        rows = parse_rows(series[symbol.upper()])
        if rows:
            print(f"{symbol}: indicative={rows[-1][4]} data_time={rows[-1][0].isoformat()}")
    count = post_new_alerts(alerts, token, repo, issue)
    print(f"New qualifying setups notified: {count}.")
    if alerts and count == 0:
        print("Qualifying condition was already notified for this candle; suppressed duplicate.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Forex scanner failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
