import unittest
from unittest.mock import patch

from email_alert import send_test_email, send_trade_email


CANDIDATE = {
    "symbol": "EUR/USD",
    "direction": "BUY",
    "entry": "1.15000",
    "stop": "1.14850",
    "target_1": "1.15150",
    "target_2": "1.15300",
    "risk_pips": 15.0,
    "breakout_level": "1.14980",
    "quote_time": "2026-11-03T12:05:00+00:00",
}
DECISION = {
    "confidence": "HIGH",
    "expected_holding_minutes": 20,
    "thesis": "Aligned trend and breakout structure.",
    "supporting_factors": ["5m and 15m alignment"],
    "risks": ["Spread not verified"],
    "invalidation": "Price closes back below breakout.",
}
SMTP_ENV = {
    "SMTP_HOST": "smtp.example.test",
    "SMTP_PORT": "587",
    "SMTP_USERNAME": "alerts@example.test",
    "SMTP_PASSWORD": "test-only-password",
    "ALERT_EMAIL_TO": "trader@example.test",
}


class EmailAlertTests(unittest.TestCase):
    def test_missing_configuration_is_reported_without_sending(self):
        with self.assertRaisesRegex(RuntimeError, "SMTP_HOST"):
            send_trade_email(CANDIDATE, DECISION, "test-model", "owner/repo", "1", environ={})

    @patch("email_alert.smtplib.SMTP")
    def test_starttls_delivery_contains_trade_levels_and_risk_notes(self, smtp_factory):
        smtp = smtp_factory.return_value.__enter__.return_value
        smtp.send_message.return_value = {}

        send_trade_email(
            CANDIDATE, DECISION, "test-model", "owner/repo", "1",
            run_id="123", environ=SMTP_ENV,
        )

        smtp_factory.assert_called_once_with("smtp.example.test", 587, timeout=20)
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with("alerts@example.test", "test-only-password")
        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["To"], "trader@example.test")
        self.assertIn("EUR/USD BUY", message["Subject"])
        text = message.get_content()
        self.assertIn("Indicative entry: 1.15000", text)
        self.assertIn("Stop loss: 1.14850", text)
        self.assertIn("economic calendar", text)
        self.assertIn("https://github.com/owner/repo/issues/1", text)

    @patch("email_alert.smtplib.SMTP_SSL")
    def test_port_465_uses_implicit_tls(self, smtp_factory):
        env = dict(SMTP_ENV, SMTP_PORT="465")
        smtp = smtp_factory.return_value.__enter__.return_value
        smtp.send_message.return_value = {}

        send_trade_email(CANDIDATE, DECISION, "test-model", "owner/repo", "1", environ=env)

        self.assertEqual(smtp_factory.call_args.args[:2], ("smtp.example.test", 465))
        smtp.starttls.assert_not_called()
        smtp.login.assert_called_once()

    def test_test_email_requires_configuration(self):
        with self.assertRaisesRegex(RuntimeError, "SMTP_HOST"):
            send_test_email(environ={})

    @patch("email_alert.smtplib.SMTP")
    def test_test_email_is_clearly_labelled_and_sends_no_trade_signal(self, smtp_factory):
        smtp = smtp_factory.return_value.__enter__.return_value
        smtp.send_message.return_value = {}
        env = dict(
            SMTP_ENV,
            GITHUB_REPOSITORY="owner/repo",
            GITHUB_RUN_ID="123",
            GITHUB_SERVER_URL="https://github.com",
        )

        send_test_email(environ=env)

        smtp_factory.assert_called_once_with("smtp.example.test", 587, timeout=20)
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with("alerts@example.test", "test-only-password")
        message = smtp.send_message.call_args.args[0]
        self.assertIn("TEST ONLY", message["Subject"])
        self.assertEqual(message["To"], "trader@example.test")
        body = message.get_content()
        self.assertIn("No trade was generated", body)
        self.assertIn("not a BUY or SELL alert", body)
        self.assertIn("https://github.com/owner/repo/actions/runs/123", body)


if __name__ == "__main__":
    unittest.main()
