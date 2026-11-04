import unittest
from unittest.mock import patch

from decision_engine import review


CANDIDATE = {
    "candidate_id": "EUR/USD|BUY|2026-11-03T12:00:00+00:00",
    "symbol": "EUR/USD",
    "direction": "BUY",
    "entry": "1.15000",
    "stop": "1.14850",
    "target_1": "1.15150",
    "target_2": "1.15300",
}


def trade_decision(**overrides):
    result = {
        "action": "BUY",
        "symbol": "EUR/USD",
        "candidate_id": CANDIDATE["candidate_id"],
        "confidence": "MEDIUM",
        "thesis": "Aligned trends and currency strength support the breakout.",
        "supporting_factors": ["5m and 15m trend alignment"],
        "risks": ["Spread and calendar are not verified"],
        "invalidation": "Reject if the breakout level fails.",
        "expected_holding_minutes": 30,
    }
    result.update(overrides)
    return result


class DecisionGateTests(unittest.TestCase):
    @patch("decision_engine._request", return_value=trade_decision())
    def test_accepts_only_exact_prequalified_candidate(self, mocked):
        decision = review([CANDIDATE], [], {}, "2026-11-03T12:05:00+00:00", "test-key")
        self.assertEqual(decision["candidate_id"], CANDIDATE["candidate_id"])
        mocked.assert_called_once()

    @patch("decision_engine._request", return_value=trade_decision(candidate_id="invented"))
    def test_rejects_candidate_not_provided_by_scanner(self, mocked):
        with self.assertRaisesRegex(RuntimeError, "not supplied"):
            review([CANDIDATE], [], {}, "2026-11-03T12:05:00+00:00", "test-key")

    @patch("decision_engine._request", return_value=trade_decision(confidence="LOW"))
    def test_rejects_low_confidence_alert(self, mocked):
        with self.assertRaisesRegex(RuntimeError, "below alert threshold"):
            review([CANDIDATE], [], {}, "2026-11-03T12:05:00+00:00", "test-key")

    @patch("decision_engine._request", return_value=trade_decision(action="SELL"))
    def test_rejects_direction_change(self, mocked):
        with self.assertRaisesRegex(RuntimeError, "altered candidate"):
            review([CANDIDATE], [], {}, "2026-11-03T12:05:00+00:00", "test-key")

    @patch("decision_engine._request", return_value=trade_decision(
        action="NO_TRADE", symbol="NONE", candidate_id="", confidence="NONE",
        thesis="The candidates conflict across timeframes.", expected_holding_minutes=0,
    ))
    def test_model_can_veto_every_candidate(self, mocked):
        decision = review([CANDIDATE], [], {}, "2026-11-03T12:05:00+00:00", "test-key")
        self.assertEqual(decision["action"], "NO_TRADE")

    def test_requires_openai_credential(self):
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            review([CANDIDATE], [], {}, "2026-11-03T12:05:00+00:00", "")


if __name__ == "__main__":
    unittest.main()
