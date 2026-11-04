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
USER_AGENT = "codexdev1337-forex-monitor/2.0"

from decision_engine import review as ai_review


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
        "timezone": "UTC",
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


def adx(bars: list[Bar], period: int = 14) -> float:
    if len(bars) < period + 1:
        raise ValueError("not enough bars for ADX")
    true_ranges, plus_moves, minus_moves = [], [], []
    for previous, current in zip(bars[:-1], bars[1:]):
        up = current.high - previous.high
        down = previous.low - current.low
        plus_moves.append(up if up > down and up > 0 else 0.0)
        minus_moves.append(down if down > up and down > 0 else 0.0)
        true_ranges.append(max(current.high-current.low, abs(current.high-previous.close), abs(current.low-previous.close)))
    dx_values = []
    for index in range(len(true_ranges)):
        first = max(0, index-period+1)
        tr_sum = sum(true_ranges[first:index+1])
        if tr_sum <= 0:
            dx_values.append(0.0)
            continue
        plus_di = 100.0*sum(plus_moves[first:index+1])/tr_sum
        minus_di = 100.0*sum(minus_moves[first:index+1])/tr_sum
        denom = plus_di+minus_di
        dx_values.append(0.0 if denom == 0 else 100.0*abs(plus_di-minus_di)/denom)
    return sum(dx_values[-period:])/min(period,len(dx_values))


def build_currency_strength(series: dict[str, list[dict[str, str]]], now: datetime):
    parsed = {}
    contributions: dict[str, list[float]] = {}
    cutoff = now.replace(second=0, microsecond=0)
    for symbol in SYMBOLS:
        rows = [row for row in parse_rows(series[symbol.upper()]) if row[0] < cutoff]
        parsed[symbol] = rows
        if len(rows) < 31:
            continue
        base, quote = symbol.split("/")
        old_close, new_close = rows[-31][4], rows[-1][4]
        if old_close <= 0:
            continue
        move_pct = 100.0*(new_close/old_close-1.0)
        contributions.setdefault(base, []).append(move_pct)
        contributions.setdefault(quote, []).append(-move_pct)
    strengths = {currency: sum(vals)/len(vals) for currency, vals in contributions.items() if vals}
    return strengths, parsed


def analyze_symbol(symbol: str, minute_rows, now: datetime, strengths: dict[str,float]):
    base, quote = symbol.split("/")
    pip = 0.01 if symbol.endswith("JPY") else 0.0001
    snapshot: dict[str, Any] = {"symbol": symbol, "status": "insufficient_data"}
    if len(minute_rows) < 250:
        return snapshot, None
    latest_time, _, _, _, current_price = minute_rows[-1]
    age_minutes = (now-latest_time).total_seconds()/60.0
    if age_minutes > 2.5:
        snapshot.update({"status":"stale","price_time_utc":latest_time.isoformat()})
        return snapshot, None
    bars5, bars15 = aggregate_minutes(minute_rows,5), aggregate_minutes(minute_rows,15)
    if len(bars5)<35 or len(bars15)<22:
        snapshot.update({"status":"incomplete_candles"})
        return snapshot, None
    last, previous = bars5[-1], bars5[-2]
    if now-(last.start+timedelta(minutes=5))>timedelta(minutes=10):
        snapshot.update({"status":"stale_5m_candle"})
        return snapshot, None
    if now-(bars15[-1].start+timedelta(minutes=15))>timedelta(minutes=20):
        snapshot.update({"status":"stale_15m_candle"})
        return snapshot, None

    closes5, closes15 = [b.close for b in bars5], [b.close for b in bars15]
    fast5, slow5 = ema(closes5,9), ema(closes5,21)
    fast15, slow15 = ema(closes15,9), ema(closes15,21)
    fast1h, slow1h = ema(closes15,8), ema(closes15,20)
    momentum, volatility, trend_strength = rsi(closes5,14), atr(bars5,14), adx(bars5,14)
    if not math.isfinite(volatility) or volatility<=0:
        snapshot.update({"status":"flat_or_invalid"})
        return snapshot, None

    base_strength, quote_strength = strengths.get(base,0.0), strengths.get(quote,0.0)
    relative_strength = base_strength-quote_strength
    change30 = 100.0*(current_price/minute_rows[-31][4]-1.0)
    trend5 = "up" if fast5>slow5 else "down" if fast5<slow5 else "flat"
    trend15 = "up" if fast15>slow15 else "down" if fast15<slow15 else "flat"
    trend1h = "up" if fast1h>slow1h else "down" if fast1h<slow1h else "flat"
    candle_range = max(last.high-last.low,pip)
    body = abs(last.close-last.open)
    close_location = (last.close-last.low)/candle_range
    expansion = candle_range/volatility
    before, before_previous = bars5[-13:-1], bars5[-14:-2]
    breakout_high, breakout_low = max(b.high for b in before), min(b.low for b in before)
    prior_high, prior_low = max(b.high for b in before_previous), min(b.low for b in before_previous)

    snapshot = {
        "symbol":symbol,"status":"fresh","price":round_price(current_price,symbol),
        "price_time_utc":latest_time.isoformat(),"quote_age_minutes":round(age_minutes,1),
        "change_30m_pct":round(change30,4),"trend_5m":trend5,"trend_15m":trend15,
        "trend_1h_proxy":trend1h,"rsi_5m":round(momentum,1),"adx_5m":round(trend_strength,1),
        "atr_5m_pips":round(volatility/pip,1),
        "base_currency_strength_30m":round(base_strength,4),
        "quote_currency_strength_30m":round(quote_strength,4),
        "relative_strength_30m":round(relative_strength,4),
        "spread":"not_available_from_candle_feed","economic_calendar":"not_connected",
    }
    common = trend_strength>=17.0 and body>=0.40*volatility and 0.75<=expansion<=2.0
    bullish = (common and trend5==trend15==trend1h=="up" and relative_strength>0
        and 52<=momentum<=70 and last.close>last.open and close_location>=0.72
        and last.close>breakout_high+0.05*volatility and previous.close<=prior_high)
    bearish = (common and trend5==trend15==trend1h=="down" and relative_strength<0
        and 30<=momentum<=48 and last.close<last.open and close_location<=0.28
        and last.close<breakout_low-0.05*volatility and previous.close>=prior_low)
    direction, breakout = ("BUY",breakout_high) if bullish else (("SELL",breakout_low) if bearish else (None,None))
    if direction is None:
        snapshot["candidate"]=False
        return snapshot,None
    if abs(current_price-last.close)>0.30*volatility:
        snapshot.update({"candidate":False,"rejection":"price_extended"})
        return snapshot,None

    risk=max(1.15*volatility,6.0*pip)
    sign=1.0 if direction=="BUY" else -1.0
    entry=current_price
    candidate_id=f"{symbol}|{direction}|{last.start.isoformat()}"
    candidate={
        "candidate_id":candidate_id,"symbol":symbol,"direction":direction,
        "bar_time":last.start.isoformat(),"quote_time":latest_time.isoformat(),
        "entry":round_price(entry,symbol),"stop":round_price(entry-sign*risk,symbol),
        "target_1":round_price(entry+sign*risk,symbol),"target_2":round_price(entry+sign*2*risk,symbol),
        "risk_pips":round(risk/pip,1),"atr_pips":round(volatility/pip,1),
        "breakout_level":round_price(breakout,symbol),"rsi":round(momentum,1),
        "adx":round(trend_strength,1),"fast_5m":round_price(fast5,symbol),
        "slow_5m":round_price(slow5,symbol),"fast_15m":round_price(fast15,symbol),
        "slow_15m":round_price(slow15,symbol),"trend_1h_proxy":trend1h,
        "relative_strength_30m":round(relative_strength,4),
        "spread_verified":False,"news_calendar_verified":False,
    }
    snapshot.update({"candidate":True,"candidate_id":candidate_id})
    return snapshot,candidate


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


def post_ai_decision(decision, candidates, token, repo, issue, model):
    if decision.get("action")=="NO_TRADE":
        print("AI decision: NO_TRADE — "+str(decision.get("thesis","No reason supplied")))
        return False
    candidate=next(c for c in candidates if c["candidate_id"]==decision["candidate_id"])
    comments_url=f"{GITHUB_API}/repos/{repo}/issues/{issue}/comments"
    comments=github_request("GET",comments_url+"?per_page=100&direction=desc",token)
    marker=f"<!-- forex-ai-signal:{candidate['candidate_id']} -->"
    if marker in "\n".join(str(item.get("body","")) for item in comments):
        print("AI-selected candidate already reported; suppressing duplicate.")
        return False
    def bullets(values):
        if not isinstance(values,list) or not values:
            return "- Not supplied"
        return "\n".join(f"- {str(value)[:350]}" for value in values[:5])
    body="\n".join([
        "## AI-reviewed major-FX setup","",
        f"**Decision:** {candidate['symbol']} {candidate['direction']} · qualitative grade **{decision['confidence']}**",
        f"**Model:** {model} (grade is not a probability of profit)","",
        f"**Indicative entry:** {candidate['entry']}",
        f"**Stop loss:** {candidate['stop']} ({candidate['risk_pips']} pips)",
        f"**Target 1:** {candidate['target_1']} (1R)",
        f"**Target 2:** {candidate['target_2']} (2R)",
        f"**AI holding horizon:** {decision['expected_holding_minutes']} minutes","",
        f"**AI thesis:** {decision['thesis']}","",
        "**Supporting factors**",bullets(decision.get("supporting_factors")),"",
        "**Risks**",bullets(decision.get("risks")),"",
        f"**Invalidation:** {decision['invalidation']}","",
        "**Manual checks:** broker bid/ask spread and economic-news risk are not connected. Verify both and confirm the live broker quote before placing an order. Discard if price has moved away from entry or the breakout has failed.",
        "",
        "> Conditional analysis only. The AI may reject all trades. It never places orders, and no signal guarantees profit.","",marker,
    ])
    github_request("POST",comments_url,token,{"body":body})
    print(f"AI decision: selected {candidate['symbol']} {candidate['direction']} ({decision['confidence']}).")
    return True


def main() -> int:
    data_key=os.environ.get("TWELVE_DATA_API_KEY","").strip()
    openai_key=os.environ.get("OPENAI_API_KEY","").strip()
    token=os.environ.get("GITHUB_TOKEN","").strip()
    repo=os.environ.get("GITHUB_REPOSITORY","").strip()
    issue=os.environ.get("FOREX_ALERT_ISSUE","1").strip()
    model=os.environ.get("OPENAI_MODEL","gpt-6-luna").strip()
    missing=[key for key,value in (
        ("TWELVE_DATA_API_KEY",data_key),("OPENAI_API_KEY",openai_key),
        ("GITHUB_TOKEN",token),("GITHUB_REPOSITORY",repo)) if not value]
    if missing:
        raise RuntimeError("Missing required configuration: "+", ".join(missing))
    if not issue.isdigit():
        raise RuntimeError("FOREX_ALERT_ISSUE must be numeric.")

    now=datetime.now(timezone.utc)
    series=fetch_all_series(data_key)
    strengths,parsed=build_currency_strength(series,now)
    snapshots,candidates=[],[]
    for symbol in SYMBOLS:
        snapshot,candidate=analyze_symbol(symbol,parsed[symbol],now,strengths)
        snapshots.append(snapshot)
        if candidate:
            candidates.append(candidate)
    print(f"Completed market scan at {now.isoformat()}; prequalified candidates={len(candidates)}.")
    print("Currency-strength context: "+json.dumps(strengths,sort_keys=True))
    for snapshot in snapshots:
        print(json.dumps(snapshot,sort_keys=True))
    if not candidates:
        print("NO_TRADE: no pair passed deterministic multi-factor filters; AI review skipped.")
        return 0

    # Fail closed: never send indicators-only alerts if model review fails.
    decision=ai_review(candidates,snapshots,strengths,now.isoformat(),openai_key,model)
    post_ai_decision(decision,candidates,token,repo,issue,model)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Forex scanner failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
