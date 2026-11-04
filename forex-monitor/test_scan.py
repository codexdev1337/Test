import unittest
from datetime import datetime, timedelta, timezone

from scan import Bar, aggregate_minutes, adx, atr, build_currency_strength, ema, rsi


class ScannerMathTests(unittest.TestCase):
    def test_aggregate_complete_five_minute_bars(self):
        start = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
        rows = []
        for offset in range(10):
            stamp = start + timedelta(minutes=offset)
            price = 1.10 + offset * 0.0001
            rows.append((stamp, price, price + 0.0002, price - 0.0001, price + 0.0001))

        bars = aggregate_minutes(rows, 5)

        self.assertEqual(len(bars), 2)
        self.assertEqual(bars[0].start, start)
        self.assertAlmostEqual(bars[0].open, rows[0][1])
        self.assertAlmostEqual(bars[0].close, rows[4][4])
        self.assertAlmostEqual(bars[0].high, max(row[2] for row in rows[:5]))
        self.assertAlmostEqual(bars[0].low, min(row[3] for row in rows[:5]))

    def test_incomplete_candle_is_ignored(self):
        start = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
        rows = []
        for offset in range(9):
            stamp = start + timedelta(minutes=offset)
            rows.append((stamp, 1.1, 1.101, 1.099, 1.1005))

        bars = aggregate_minutes(rows, 5)

        self.assertEqual(len(bars), 1)

    def test_ema_flat_series(self):
        self.assertAlmostEqual(ema([1.25] * 30, 9), 1.25)

    def test_rsi_rising_and_falling_series(self):
        rising = [float(value) for value in range(20)]
        falling = [float(20 - value) for value in range(20)]
        self.assertAlmostEqual(rsi(rising), 100.0)
        self.assertAlmostEqual(rsi(falling), 0.0)


    def test_adx_is_positive_for_directional_bars(self):
        start = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
        bars = [
            Bar(
                start + timedelta(minutes=5 * index),
                1.10 + index * 0.0001,
                1.101 + index * 0.0001,
                1.099 + index * 0.0001,
                1.1005 + index * 0.0001,
            )
            for index in range(30)
        ]
        self.assertGreater(adx(bars), 0.0)

    def test_currency_strength_signs_follow_base_and_quote(self):
        start = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
        series = {}
        for symbol in (
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
            "AUD/USD", "NZD/USD", "USD/CAD", "EUR/GBP",
        ):
            rows = []
            old_price = 1.0
            new_price = 1.0
            if symbol == "EUR/USD":
                new_price = 1.01
            elif symbol == "USD/JPY":
                old_price, new_price = 150.0, 151.5
            for index in range(31):
                price = old_price + (new_price - old_price) * index / 30
                stamp = start + timedelta(minutes=index)
                rows.append({
                    "datetime": stamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": str(price),
                    "high": str(price + 0.001),
                    "low": str(price - 0.001),
                    "close": str(price),
                })
            series[symbol] = rows

        strengths, parsed = build_currency_strength(
            series, start + timedelta(minutes=32)
        )

        self.assertGreater(strengths["EUR"], 0.0)
        self.assertLess(strengths["JPY"], 0.0)
        self.assertIn("EUR/USD", parsed)

    def test_atr_is_positive_for_nonflat_bars(self):
        start = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
        bars = [
            Bar(
                start + timedelta(minutes=5 * index),
                1.10 + index * 0.0001,
                1.101 + index * 0.0001,
                1.099 + index * 0.0001,
                1.1005 + index * 0.0001,
            )
            for index in range(20)
        ]
        self.assertGreater(atr(bars), 0.0)


if __name__ == "__main__":
    unittest.main()
