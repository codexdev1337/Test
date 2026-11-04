"""SMTP email delivery for AI-approved FX alerts and explicit test messages."""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr
from typing import Mapping, Any


def _smtp_settings(env: Mapping[str, str]) -> tuple[str, int, str, str, str, str]:
    required = (
        "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME",
        "SMTP_PASSWORD", "ALERT_EMAIL_TO",
    )
    missing = [name for name in required if not str(env.get(name, "")).strip()]
    if missing:
        raise RuntimeError(
            "Email alert is not configured. Add GitHub Actions secrets: "
            + ", ".join(missing)
        )

    host = str(env["SMTP_HOST"]).strip()
    try:
        port = int(str(env["SMTP_PORT"]).strip())
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be 465 (implicit TLS) or a STARTTLS port such as 587.") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("SMTP_PORT must be between 1 and 65535.")

    username = str(env["SMTP_USERNAME"]).strip()
    password = str(env["SMTP_PASSWORD"])
    recipient = parseaddr(str(env["ALERT_EMAIL_TO"]).strip())[1]
    sender_value = str(env.get("ALERT_EMAIL_FROM", "")).strip() or username
    sender = parseaddr(sender_value)[1]
    if not recipient or "@" not in recipient or not sender or "@" not in sender:
        raise RuntimeError("ALERT_EMAIL_TO and ALERT_EMAIL_FROM/SMTP_USERNAME must be valid email addresses.")
    if any(char in sender + recipient for char in "\r\n"):
        raise RuntimeError("Email addresses must not contain line breaks.")
    return host, port, username, password, sender, recipient


def _send_via_smtp(message: EmailMessage, settings: tuple[str, int, str, str, str, str]) -> None:
    host, port, username, password, sender, recipient = settings
    message["From"] = sender
    message["To"] = recipient

    context = ssl.create_default_context()
    if port == 465:
        smtp_factory = smtplib.SMTP_SSL
        smtp_kwargs = {"timeout": 20, "context": context}
    else:
        smtp_factory = smtplib.SMTP
        smtp_kwargs = {"timeout": 20}

    with smtp_factory(host, port, **smtp_kwargs) as smtp:
        if port != 465:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
        smtp.login(username, password)
        refused = smtp.send_message(message)
        if refused:
            raise RuntimeError("SMTP server refused one or more email recipients.")


def send_test_email(environ: Mapping[str, str] | None = None) -> None:
    """Send an explicitly requested, clearly labelled SMTP test email."""
    env = os.environ if environ is None else environ
    settings = _smtp_settings(env)
    run_id = str(env.get("GITHUB_RUN_ID", "")).strip()
    server_url = str(env.get("GITHUB_SERVER_URL", "https://github.com")).strip()
    repo = str(env.get("GITHUB_REPOSITORY", "")).strip()
    run_url = f"{server_url.rstrip('/')}/{repo}/actions/runs/{run_id}" if repo and run_id else "Not available"

    message = EmailMessage()
    message["Subject"] = "TEST ONLY — Forex Monitor Gmail delivery check"
    message.set_content("\n".join([
        "This is a test email from your Forex Monitor GitHub Actions workflow.",
        "",
        "It confirms that GitHub Actions successfully authenticated with your SMTP server and handed this message to Gmail for delivery.",
        "",
        "No trade was generated or recommended by this test.",
        "This is not a BUY or SELL alert.",
        "",
        f"Workflow run: {run_url}",
        "",
        "You can safely delete this test message.",
    ]))
    _send_via_smtp(message, settings)
    print("SMTP test message accepted by Gmail for delivery.")


def send_trade_email(
    candidate: dict[str, Any],
    decision: dict[str, Any],
    model: str,
    repo: str,
    issue: str,
    run_id: str = "",
    server_url: str = "https://github.com",
    environ: Mapping[str, str] | None = None,
) -> None:
    """Send one AI-approved setup via the same authenticated SMTP connection."""
    env = os.environ if environ is None else environ
    settings = _smtp_settings(env)

    symbol = str(candidate["symbol"])
    direction = str(candidate["direction"])
    confidence = str(decision["confidence"])
    subject = f"FX setup alert: {symbol} {direction} [{confidence}]"
    issue_url = f"{server_url.rstrip('/')}/{repo}/issues/{issue}"
    run_url = f"{server_url.rstrip('/')}/{repo}/actions/runs/{run_id}" if run_id else "Not available"
    supporting = decision.get("supporting_factors", [])
    risks = decision.get("risks", [])
    supporting_text = "\n".join(f"- {item}" for item in supporting) if supporting else "- Not supplied"
    risks_text = "\n".join(f"- {item}" for item in risks) if risks else "- Not supplied"

    body = "\n".join([
        "A new FX setup passed the scanner filters and the AI review gate.",
        "",
        f"Pair: {symbol}",
        f"Direction: {direction}",
        f"Qualitative grade: {confidence} (not a probability of profit)",
        f"Model: {model}",
        f"Indicative entry: {candidate['entry']}",
        f"Stop loss: {candidate['stop']} ({candidate['risk_pips']} pips)",
        f"Target 1: {candidate['target_1']} (1R)",
        f"Target 2: {candidate['target_2']} (2R)",
        f"Breakout level: {candidate.get('breakout_level', 'not supplied')}",
        f"Expected holding horizon: {decision['expected_holding_minutes']} minutes",
        f"Market quote time (UTC): {candidate.get('quote_time', 'not supplied')}",
        "",
        "AI thesis:",
        str(decision.get("thesis", "Not supplied")),
        "",
        "Supporting factors:",
        supporting_text,
        "",
        "Risks:",
        risks_text,
        "",
        "Invalidation:",
        str(decision.get("invalidation", "Not supplied")),
        "",
        "Before considering any order:",
        "- Confirm the current executable bid/ask quote and broker spread.",
        "- Check the economic calendar and breaking news; neither is connected to this scanner.",
        "- Reject the setup if price has moved materially away from the indicative entry or the breakout has failed.",
        "",
        "This is conditional market analysis, not an instruction to trade. Prices may move before this email is read. The scanner does not place or manage broker orders, and no signal guarantees profit.",
        "",
        f"GitHub alert: {issue_url}",
        f"Workflow run: {run_url}",
    ])

    message = EmailMessage()
    message["Subject"] = subject
    message.set_content(body)
    _send_via_smtp(message, settings)
