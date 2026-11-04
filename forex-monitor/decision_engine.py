"""LLM review gate for deterministic FX scanner candidates."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://api.openai.com/v1/responses"
MODEL_DEFAULT = "gpt-6-luna"
SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "NZD/USD", "USD/CAD", "EUR/GBP",
]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {"type": "string", "enum": ["BUY", "SELL", "NO_TRADE"]},
        "symbol": {"type": "string", "enum": SYMBOLS + ["NONE"]},
        "candidate_id": {"type": "string"},
        "confidence": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW", "NONE"]},
        "thesis": {"type": "string"},
        "supporting_factors": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "invalidation": {"type": "string"},
        "expected_holding_minutes": {"type": "integer"},
    },
    "required": [
        "action", "symbol", "candidate_id", "confidence", "thesis",
        "supporting_factors", "risks", "invalidation", "expected_holding_minutes",
    ],
}

INSTRUCTIONS = """
You are the independent trade-selection and risk-review layer for a short-horizon
major-FX scanner. You are an analyst, not an order-execution agent.

Choose exactly one candidate from the supplied prequalified_candidates, or reject
all of them with NO_TRADE. Only use the exact candidate_id, symbol and direction
provided. Never create candidates or invent/alter prices, entries, stops, targets,
quotes, probabilities, news, economic releases, spreads or market facts.

Use judgement, not a mechanical vote:
- Consider whether 5m, 15m and 1h-proxy trends agree and whether the move is
  already extended.
- Assess breakout candle structure, momentum, ADX/trend quality, ATR regime,
  relative currency strength and whether several pairs tell a coherent story.
- Penalize conflicting USD/currency strength, stale or thin data, crowded moves,
  poor timing, weak reward/risk and contradictory higher-timeframe context.
- Prefer NO_TRADE over a marginal setup. If the candidates are poor, reject all.
- Spread and scheduled-news risk are explicitly not verified in this data. Never
  say they are safe. Name these as pre-entry human checks. No economic calendar
  or news feed is supplied; do not make up fundamental explanations.
- HIGH/MEDIUM are qualitative evidence grades, not probabilities of profit.
  Select only HIGH or MEDIUM; otherwise return NO_TRADE.
- Provide concise reasoning, concrete risks, a price-agnostic invalidation
  description, and an expected holding horizon from 1 to 60 minutes.
- Do not suggest increasing leverage. Do not issue instructions to execute trades.
""".strip()


def _request(api_key: str, model: str, context: dict[str, Any]) -> dict[str, Any]:
    body = {
        "model": model,
        "store": False,
        "max_output_tokens": 900,
        "input": [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": json.dumps(context, separators=(",", ":"))},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "fx_trade_decision",
                "strict": True,
                "schema": SCHEMA,
            }
        },
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "codexdev1337-forex-monitor/2.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            raw = response.read()
            if len(raw) > 1_000_000:
                raise RuntimeError("OpenAI decision response exceeded 1 MB.")
            payload = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(500).decode("utf-8", "replace")
        raise RuntimeError(f"OpenAI decision request failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI decision request network error: {exc.reason}") from exc

    if payload.get("status") not in (None, "completed"):
        raise RuntimeError(f"OpenAI decision did not complete: {payload.get('status')}")

    text = payload.get("output_text")
    if not isinstance(text, str):
        fragments = []
        for item in payload.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        fragments.append(str(content.get("text", "")))
        text = "\n".join(fragments)
    if not text:
        raise RuntimeError("OpenAI returned no decision text.")
    try:
        decision = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI decision did not match JSON output contract.") from exc
    if not isinstance(decision, dict):
        raise RuntimeError("OpenAI decision must be a JSON object.")
    return decision


def review(
    candidates: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    currency_strength: dict[str, float],
    scan_time_utc: str,
    api_key: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Return one model decision and enforce scanner-owned candidate/level bounds."""
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required; no rules-only fallback is allowed.")
    selected_model = (model or os.environ.get("OPENAI_MODEL") or MODEL_DEFAULT).strip()
    context = {
        "scan_time_utc": scan_time_utc,
        "currency_strength_30m_average_pct": currency_strength,
        "pair_snapshots": snapshots,
        "prequalified_candidates": candidates,
        "data_limits": {
            "broker_bid_ask_spread": "not_available",
            "scheduled_economic_news_calendar": "not_available",
            "verified_live_headlines": "not_available",
            "model_may_create_or_edit_prices": False,
            "model_may_create_candidates": False,
            "broker_execution_enabled": False,
        },
    }
    decision = _request(api_key, selected_model, context)

    action = decision.get("action")
    if action == "NO_TRADE":
        if decision.get("symbol") != "NONE" or decision.get("candidate_id") != "":
            raise RuntimeError("Invalid NO_TRADE response; rejecting model output.")
        if decision.get("confidence") != "NONE":
            raise RuntimeError("NO_TRADE must have NONE confidence.")
        if not str(decision.get("thesis", "")).strip():
            raise RuntimeError("NO_TRADE must include a reason.")
        return decision

    if action not in ("BUY", "SELL"):
        raise RuntimeError("Invalid model action; rejecting output.")
    if decision.get("confidence") not in ("HIGH", "MEDIUM"):
        raise RuntimeError("Model confidence is below alert threshold.")
    candidate = next(
        (item for item in candidates if item.get("candidate_id") == decision.get("candidate_id")),
        None,
    )
    if candidate is None:
        raise RuntimeError("Model selected a candidate not supplied by the scanner.")
    if candidate["symbol"] != decision.get("symbol") or candidate["direction"] != action:
        raise RuntimeError("Model altered candidate pair or direction.")
    if not all(str(decision.get(key, "")).strip() for key in ("thesis", "invalidation")):
        raise RuntimeError("Model omitted thesis or invalidation.")
    holding = decision.get("expected_holding_minutes")
    if not isinstance(holding, int) or not 1 <= holding <= 60:
        raise RuntimeError("Model holding horizon is outside the 1–60 minute limit.")
    if not all(isinstance(decision.get(key), list) for key in ("supporting_factors", "risks")):
        raise RuntimeError("Model omitted supporting factors or risks.")
    return decision
