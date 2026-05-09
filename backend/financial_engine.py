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
            
            TOTAL_WEEKS = 104
            TOTAL_DAYS = 731
            IDEAL_DAILY_RATE = 100.0 / TOTAL_DAYS
            
            envisaged_pct_work = round(days_elapsed * IDEAL_DAILY_RATE, 2)
            variance = round(pct_work - envisaged_pct_work, 2)
            
            remaining_work = 100.0 - pct_work
            remaining_days = max(1, TOTAL_DAYS - days_elapsed)
            required_future_rate = round((remaining_work / remaining_days) * 7.0, 2) # Per week for consistency
            
            revenue = (pct_work / 100.0) * self.contract_sum
            slippage_gap = pct_time - pct_work
            
            daily_financials.append({
                "date": date_str,
                "pct_work": pct_work,
                "pct_time": pct_time,
                "envisaged_pct_work": envisaged_pct_work,
                "variance": variance,
                "required_future_rate": required_future_rate,
                "revenue_earned": revenue,
                "slippage_gap": round(slippage_gap, 2)
            })

        # 2. Weekly Financials (Direct from Weekly JSONs)
        raw_weekly = self.analytics._get_all_data(source="weekly")
        weekly_financials = []
        seen_weeks = set()
        
        TOTAL_WEEKS = 104 # 24 Months
        import datetime
        contract_start = datetime.datetime(2025, 11, 24)
        
        # Pre-sort and deduplicate
        raw_weekly_processed = []
        for w in raw_weekly:
            date_label = w.get("_display_date") or w.get("label", "Unknown Week")
            norm_label = re.sub(r'[^a-z0-9]', '', str(date_label).lower())
            if norm_label in seen_weeks: continue
            seen_weeks.add(norm_label)
            raw_weekly_processed.append(w)
            
        raw_weekly_processed.sort(key=lambda x: str(x.get("_sort_date", "")))
        
        prev_pct_work = 0.0
        # If we have a lot of history, we might want to estimate the first week's start % 
        # But if the first record is far into the project, 0.0 is wrong.
        # Let's try to find if there's an earlier record or use the first record's pct_work as a starting point for itself? 
        # No, the user said "100% - what we started with on 30th". 
        # For the first available week, we'll assume the start was the previous record or a baseline.
        
        for i, w in enumerate(raw_weekly_processed):
            date_label = w.get("_display_date") or w.get("label", "Unknown Week")
            pct_work = self._parse_percent(w.get("pct_work_done") or w.get("pct_work") or w.get("work_completed_percent"))
            pct_time = self._parse_percent(w.get("pct_period_elapsed") or w.get("pct_period") or w.get("time_elapsed_percent"))
            
            # Weekly Chain Logic
            weeks_elapsed = round((pct_time / 100.0) * TOTAL_WEEKS)
            remaining_weeks = max(1, TOTAL_WEEKS - (weeks_elapsed - 1)) # Including this week
            
            # For the first week in our list, if it's already at 6%, we can't assume 0% start 
            # unless it IS the first week of the project.
            # Let's look for a trend or just use the current if it's the first.
            start_pct = prev_pct_work if i > 0 else (pct_work * 0.9) # Small fallback if first
            
            weekly_actual = round(pct_work - start_pct, 2)
            weekly_envisaged = round((100.0 - start_pct) / remaining_weeks, 2)
            weekly_variance = round(weekly_actual - weekly_envisaged, 2)
            
            # Global Cumulative Recalibration
            envisaged_pct_work_cum = round(weeks_elapsed * (100.0 / TOTAL_WEEKS), 2)
            
            # Recalibrate for FUTURE (used for next week/month targets)
            rem_weeks_next = max(1, TOTAL_WEEKS - weeks_elapsed)
            required_future_rate = round((100.0 - pct_work) / rem_weeks_next, 2)
            variance_cum = round(pct_work - envisaged_pct_work_cum, 2)
            
            revenue = (pct_work / 100.0) * self.contract_sum
            slippage_gap = pct_time - pct_work
            
            weekly_financials.append({
                "date": date_label,
                "label": date_label,
                "start_pct": start_pct,
                "end_pct": pct_work,
                "weekly_actual": weekly_actual,
                "weekly_envisaged": weekly_envisaged,
                "weekly_variance": weekly_variance,
                "pct_work": pct_work,
                "pct_time": pct_time,
                "envisaged_pct_work": envisaged_pct_work_cum,
                "variance": variance_cum,
                "required_future_rate": required_future_rate,
                "revenue_earned": revenue,
                "slippage_gap": round(slippage_gap, 2)
            })
            prev_pct_work = pct_work
            
        # 3. Monthly Calibration Logic (Refined)
        monthly_financials = []
        import collections
        month_groups = collections.defaultdict(list)
        
        # We need a reference for "current" vs "completed"
        # Today is May 9th, 2026 (based on local time)
        CURRENT_MONTH_STR = "May 2026"
        
        for w in weekly_financials:
            # Extract month from label
            m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", w["label"])
            if m:
                m_key = f"{m.group(1)} {m.group(2)}"
                month_groups[m_key].append(w)
        
        sorted_months = sorted(month_groups.keys(), key=lambda k: datetime.datetime.strptime(k, "%B %Y"))
        
        for m_key in sorted_months:
            group = month_groups[m_key]
            
            # Start of month: End % of previous month OR start of first week
            # To be accurate: start_pct of first week of the month
            m_start_pct = group[0]["start_pct"]
            m_end_pct = group[-1]["end_pct"]
            m_actual = round(m_end_pct - m_start_pct, 2)
            
            # Envisaged for the month
            # Average linear target is ~0.96% per week. Month is ~4.345 weeks.
            # So month envisaged is ~4.17%.
            # Let's use the cumulative envisaged delta
            m_envisaged_start = group[0]["envisaged_pct_work"] - group[0]["weekly_envisaged"]
            m_envisaged_end = group[-1]["envisaged_pct_work"]
            m_envisaged_total = round(m_envisaged_end - m_envisaged_start, 2)
            
            is_ongoing = (m_key == CURRENT_MONTH_STR)
            
            # Recalibrated required rate (using the last week of this month)
            req_weekly = group[-1]["required_future_rate"]
            
            # Target for the END of THIS month (for ongoing tracking)
            # Calculated as (start of month) + (req_weekly_at_start * 4.345)
            # For the first month, we use baseline 0.96
            m_idx = sorted_months.index(m_key)
            prev_m_key = sorted_months[m_idx-1] if m_idx > 0 else None
            req_at_start = month_groups[prev_m_key][-1]["required_future_rate"] if prev_m_key else 0.96
            target_this_month = round(m_start_pct + (req_at_start * 4.345), 2)

            # Target for NEXT month is (current end) + (req_weekly * 4.345)
            target_next_month = round(m_end_pct + (req_weekly * 4.345), 2)
            
            monthly_financials.append({
                "month": m_key,
                "start_pct": m_start_pct,
                "end_pct": m_end_pct,
                "actual_production": m_actual,
                "envisaged_production": m_envisaged_total,
                "variance": round(m_actual - m_envisaged_total, 2),
                "is_ongoing": is_ongoing,
                "required_weekly": req_weekly,
                "target_this_month_end": target_this_month,
                "target_next_month_end": target_next_month
            })



        # 4. Save to Analytics Cache
        output_data = {
            "contract_sum": self.contract_sum,
            "last_updated": os.popen("date").read().strip() if os.name != 'nt' else "",
            "daily_financials": daily_financials,
            "weekly_financials": weekly_financials,
            "monthly_financials": monthly_financials
        }
        
        out_path = os.path.join(self.analysis_dir, "financial_trends.json")
        with open(out_path, "w") as f:
            json.dump(output_data, f, indent=2)
            
        print(f"Financial cache saved to: {out_path}")
        return output_data

if __name__ == "__main__":
    engine = FinancialEngine()
    engine.compute_and_cache_financials()
