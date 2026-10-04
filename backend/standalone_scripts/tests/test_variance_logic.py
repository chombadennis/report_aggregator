import unittest
import os
import sys

# Add parent dir to path to import variance_logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from variance_logic import calculate_planned_date, calculate_variance, save_weekly_snapshot, get_snapshots_for_week

class TestVarianceLogic(unittest.TestCase):

    def test_calculate_planned_date(self):
        # 10 day task
        start = "2026-10-01"
        finish = "2026-10-11"
        
        # 100% complete
        dt_100 = calculate_planned_date(start, finish, 100)
        self.assertEqual(dt_100.strftime('%Y-%m-%d'), "2026-10-11")
        
        # 50% complete (5 days in)
        dt_50 = calculate_planned_date(start, finish, 50)
        self.assertEqual(dt_50.strftime('%Y-%m-%d'), "2026-10-06")

    def test_calculate_variance(self):
        # Planned to finish on 15th
        from datetime import datetime
        planned = datetime(2026, 10, 15)
        
        # Reported on 20th (5 days late -> -5)
        var_late = calculate_variance(planned, "2026-10-20")
        self.assertEqual(var_late, -5)
        
        # Reported on 10th (5 days ahead -> +5)
        var_ahead = calculate_variance(planned, "2026-10-10")
        self.assertEqual(var_ahead, 5)

if __name__ == '__main__':
    unittest.main()
