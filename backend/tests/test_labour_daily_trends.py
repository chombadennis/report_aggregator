import sys
import os
import unittest
from datetime import datetime

# Adjust the path so we can import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from analytics import AnalyticsEngine

class TestLabourDailyTrends(unittest.TestCase):
    def setUp(self):
        self.history_dir = os.path.join(os.path.dirname(__file__), '..', 'cache', 'history')
        self.monthly_dir = os.path.join(os.path.dirname(__file__), '..', 'cache', 'history_monthly')
        self.analytics = AnalyticsEngine(history_dir=self.history_dir, monthly_dir=self.monthly_dir)

    def test_daily_trends_calculates_correct_totals(self):
        """Test that the daily trends properly isolate day columns to prevent inflation."""
        daily_trends = self.analytics.get_daily_trends()
        self.assertTrue(len(daily_trends) > 0, "Daily trends should not be empty")

        # Find the specific date we know the total for: 2026-09-22
        target_date = "2026-09-22"
        target_trend = next((t for t in daily_trends if t["date"] == target_date), None)
        
        self.assertIsNotNone(target_trend, f"Should find daily trend for {target_date}")
        self.assertEqual(target_trend["labour"], 166, "Labour total for 2026-09-22 should be 166, not inflated by previous day columns")

if __name__ == '__main__':
    unittest.main()
