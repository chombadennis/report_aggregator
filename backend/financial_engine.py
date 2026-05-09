import os
import json
import re
import math
from analytics import AnalyticsEngine

class FinancialEngine:
    def __init__(self, analysis_dir="analysis", contract_sum=2127050827.72):
        self.analysis_dir = analysis_dir
        self.contract_sum = contract_sum
        os.makedirs(self.analysis_dir, exist_ok=True)
        self.analytics = AnalyticsEngine(history_dir="history", monthly_dir="cache/history_monthly")

    def _parse_percent(self, val):
        """Converts '8.04%' or '8.04' to 0.0804 float"""
        if not val or str(val).lower() == "none" or str(val).lower() == "n/a":
            return 0.0
        try:
            val_float = float(str(val).replace("%", "").replace(",", "").strip())
            if math.isnan(val_float) or math.isinf(val_float):
                return 0.0
            return val_float
        except ValueError:
            return 0.0

    def compute_and_cache_financials(self):
        """Calculates revenue and slippage gap for all days and weeks."""
        
        print("Computing Financial Analytics Cache...")
        
        # 1. Daily Financials
        daily_trends = self.analytics.get_daily_trends()
        daily_financials = []
        
        import datetime
        contract_start = datetime.datetime(2025, 11, 24)
        total_contract_days = 731.0

        for d in daily_trends:
            date_str = d.get("date")
            pct_work = self._parse_percent(d.get("financial_progress"))
            
            # Mathematically calculate elapsed time
            try:
                current_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                days_elapsed = (current_date - contract_start).days + 1
                days_elapsed = max(0, min(days_elapsed, int(total_contract_days)))
                pct_time = round((days_elapsed / total_contract_days) * 100.0, 2)
            except Exception:
                pct_time = self._parse_percent(d.get("time_progress"))
            
            revenue = (pct_work / 100.0) * self.contract_sum
            slippage_gap = pct_time - pct_work
            
            daily_financials.append({
                "date": date_str,
                "pct_work": pct_work,
                "pct_time": pct_time,
                "revenue_earned": revenue,
                "slippage_gap": round(slippage_gap, 2)
            })

        # 2. Weekly Financials (Direct from Weekly JSONs)
        raw_weekly = self.analytics._get_all_data(source="weekly")
        weekly_financials = []
        seen_weeks = set()
        
        for w in raw_weekly:
            date_label = w.get("_display_date") or w.get("label", "Unknown Week")
            # Strip all non-alphanumeric characters for robust deduplication (handles en-dashes vs hyphens)
            norm_label = re.sub(r'[^a-z0-9]', '', str(date_label).lower())
            
            if norm_label in seen_weeks:
                continue
            seen_weeks.add(norm_label)
            
            pct_work = self._parse_percent(w.get("pct_work_done") or w.get("pct_work") or w.get("work_completed_percent"))
            pct_time = self._parse_percent(w.get("pct_period_elapsed") or w.get("pct_period") or w.get("time_elapsed_percent"))
            
            revenue = (pct_work / 100.0) * self.contract_sum
            slippage_gap = pct_time - pct_work
            
            # _sort_date might be a string from JSON cache, or a datetime. Convert to ISO string.
            sort_val = str(w.get("_sort_date", ""))
            
            weekly_financials.append({
                "date": date_label,
                "label": date_label,
                "pct_work": pct_work,
                "pct_time": pct_time,
                "revenue_earned": revenue,
                "slippage_gap": round(slippage_gap, 2),
                "_sort_val": sort_val
            })
            
        # Guarantee strict chronological sorting (strings in ISO format sort correctly)
        weekly_financials.sort(key=lambda x: x["_sort_val"])
        
        for w in weekly_financials:
            w.pop("_sort_val", None)
            


        # 3. Save to Analytics Cache
        output_data = {
            "contract_sum": self.contract_sum,
            "last_updated": os.popen("date").read().strip() if os.name != 'nt' else "",
            "daily_financials": daily_financials,
            "weekly_financials": weekly_financials
        }
        
        out_path = os.path.join(self.analysis_dir, "financial_trends.json")
        with open(out_path, "w") as f:
            json.dump(output_data, f, indent=2)
            
        print(f"Financial cache saved to: {out_path}")
        return output_data

if __name__ == "__main__":
    engine = FinancialEngine()
    engine.compute_and_cache_financials()
