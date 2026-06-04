import os
import sys
import unittest
import datetime
import calendar
import re

# Add parent directory to sys.path to import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Change working directory to backend folder to resolve relative cache paths
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestFinancialOngoingMonth(unittest.TestCase):
    def check_is_ongoing(self, current_date, last_report_label, m_key):
        month_name, year_str = m_key.split()
        year = int(year_str)
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        month_num = month_names.index(month_name.capitalize()) + 1
        _, last_day_of_month = calendar.monthrange(year, month_num)
        
        is_past_month = (current_date.year * 12 + current_date.month) > (year * 12 + month_num)
        
        parts = re.split(r'[-–—]', last_report_label)
        last_report_end_day = None
        if len(parts) >= 2:
            end_part = parts[-1]
            day_match = re.search(r'\d+', end_part)
            if day_match:
                last_report_end_day = int(day_match.group())
        else:
            # Simple fallback parser for testing
            from parser import ReportParser
            start_dt = ReportParser()._parse_weekly_start_date(last_report_label)
            if start_dt:
                end_dt = start_dt + datetime.timedelta(days=6)
                last_report_end_day = end_dt.day

        ends_on_last_day = (last_report_end_day == last_day_of_month)
        return not (is_past_month or ends_on_last_day)

    def test_past_month_completed(self):
        """Today is June 4, 2026. May 2026 should be calendar-completed (is_ongoing = False)."""
        current_date = datetime.datetime(2026, 6, 4)
        last_report_label = "25th – 31st May 2026"
        m_key = "May 2026"
        
        is_ongoing = self.check_is_ongoing(current_date, last_report_label, m_key)
        self.assertFalse(is_ongoing) # Completed because June is past May

    def test_current_month_ends_on_last_day(self):
        """Today is May 31, 2026. Report ends on 31st. May 2026 should be completed (is_ongoing = False)."""
        current_date = datetime.datetime(2026, 5, 31)
        last_report_label = "25th – 31st May 2026"
        m_key = "May 2026"
        
        is_ongoing = self.check_is_ongoing(current_date, last_report_label, m_key)
        self.assertFalse(is_ongoing) # Completed because it ends on the 31st (last day)

    def test_current_month_ongoing(self):
        """Today is May 15, 2026. May reports do not reach 31st yet. May 2026 should be ongoing (is_ongoing = True)."""
        current_date = datetime.datetime(2026, 5, 15)
        last_report_label = "4th – 10th May 2026"
        m_key = "May 2026"
        
        is_ongoing = self.check_is_ongoing(current_date, last_report_label, m_key)
        self.assertTrue(is_ongoing) # Ongoing because we are still in May and it doesn't end on the last day

    def test_financial_engine_run(self):
        """Verify that the actual FinancialEngine compute runs successfully and has correct mathematical results."""
        from financial_engine import FinancialEngine
        engine = FinancialEngine(analysis_dir="cache/analysis_test")
        data = engine.compute_and_cache_financials()
        self.assertIn("monthly_financials", data)
        self.assertTrue(len(data["monthly_financials"]) > 0)
        
        # Verify the presence of the fields
        first_month = data["monthly_financials"][0]
        self.assertIn("revenue_earned", first_month)
        self.assertIn("slippage_gap", first_month)
        
        # Verify April 2026 values
        april = next((m for m in data["monthly_financials"] if m["month"] == "April 2026"), None)
        self.assertIsNotNone(april)
        self.assertEqual(april["start_pct"], 5.472)
        self.assertEqual(april["end_pct"], 8.22)
        self.assertEqual(april["actual_production"], 2.75)
        self.assertEqual(april["envisaged_production"], 4.69)
        self.assertEqual(april["variance"], -1.94)
        self.assertEqual(april["required_weekly"], 1.11)
        
        # Verify May 2026 values
        may = next((m for m in data["monthly_financials"] if m["month"] == "May 2026"), None)
        self.assertIsNotNone(may)
        self.assertEqual(may["start_pct"], 8.22)
        self.assertEqual(may["end_pct"], 9.64)
        self.assertEqual(may["actual_production"], 1.42)
        self.assertEqual(may["envisaged_production"], 4.93)
        self.assertEqual(may["variance"], -3.51)
        self.assertEqual(may["required_weekly"], 1.17)
        self.assertFalse(may["is_ongoing"]) # Completed month
        
        # Verify June 2026 values (ongoing/current month)
        june = next((m for m in data["monthly_financials"] if m["month"] == "June 2026"), None)
        self.assertIsNotNone(june)
        self.assertEqual(june["start_pct"], 9.64)
        self.assertEqual(june["end_pct"], 9.64)
        self.assertEqual(june["actual_production"], 0.0)
        self.assertEqual(june["envisaged_production"], 5.0)
        self.assertEqual(june["variance"], -5.0)
        self.assertEqual(june["required_weekly"], 1.17)
        self.assertTrue(june["is_ongoing"]) # Ongoing/current system month
        self.assertEqual(june["target_fixed_month_end"], 14.64)
        self.assertEqual(june["target_rolling_month_end"], 14.64)
        self.assertEqual(june["production_planned_fixed"], 5.0)
        self.assertEqual(june["production_required_rolling"], 5.0)

if __name__ == "__main__":
    unittest.main()
