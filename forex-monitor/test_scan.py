import unittest
from datetime import datetime, timedelta, timezone

from scan import Bar, aggregate_minutes, atr, ema, rsi


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
