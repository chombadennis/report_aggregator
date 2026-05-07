import os
import json
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from ai_client import generate_summary_json
from parser import ReportParser

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    def __init__(self, history_dir: str = "history", monthly_dir: str = "history_monthly"):
        self.history_dir = history_dir
        self.monthly_dir = monthly_dir

    def _clean_val(self, v: Any) -> int:
        """Extracts the first number from a string (e.g. '4(m)' -> 4)."""
        if isinstance(v, (int, float)):
            return int(v)
        m = re.search(r"\d+", str(v))
        return int(m.group(0)) if m else 0

    def get_daily_trends(self):
        all_data = self._get_all_data(source="weekly")
        monthly_data = self._get_all_data(source="monthly")
        
        daily_timeline = []
        seen_dates = set()
        
        def process_entry(entry):
            start_dt = entry.get("_sort_date")
            labour_daily = entry.get("labour_daily", {})
            weather_daily = entry.get("weather_daily", {})
            
            # CASE A: Modern Schema
            if isinstance(labour_daily, dict) and labour_daily:
                for date_key, labour_stats in labour_daily.items():
                    if date_key in seen_dates: continue
                    
                    weather_stats = {}
                    if isinstance(weather_daily, dict):
                        for w_key, w_val in weather_daily.items():
                            if date_key in w_key:
                                weather_stats = w_val
                                break
                    
                    day_total = self._clean_val(labour_stats.get("TOTAL", "0") if isinstance(labour_stats, dict) else labour_stats)
                    mat_count = len(entry.get("materials_delivered", []) or entry.get("materials_sum", {}))
                    
                    try:
                        is_weekend = datetime.strptime(date_key, "%Y-%m-%d").weekday() >= 5
                    except: is_weekend = False

                    daily_timeline.append({
                        "date": date_key,
                        "labour": day_total,
                        "materials": mat_count,
                        "weather_disrupted": 1 if "favorable" not in str(weather_stats).lower() and "-" not in str(weather_stats) else 0,
                        "is_weekend": 1 if is_weekend else 0
                    })
                    seen_dates.add(date_key)
            
            # CASE B: Legacy/Aggregated Schema
            elif "labour" in entry and isinstance(entry["labour"], dict) and start_dt:
                total_row = entry["labour"].get("TOTAL", [])
                weather_list = entry.get("weather", [])
                
                for i, val in enumerate(total_row):
                    curr_date = start_dt + timedelta(days=i)
                    date_key = curr_date.strftime("%Y-%m-%d")
                    if date_key in seen_dates: continue
                    
                    weather_stats = weather_list[i] if i < len(weather_list) else {}
                    day_total = self._clean_val(val)
                    mat_count = len(entry.get("materials_sum", {}))

                    daily_timeline.append({
                        "date": date_key,
                        "labour": day_total,
                        "materials": mat_count,
                        "weather_disrupted": 1 if "favorable" not in str(weather_stats).lower() and "-" not in str(weather_stats) else 0,
                        "is_weekend": 1 if curr_date.weekday() >= 5 else 0
                    })
                    seen_dates.add(date_key)

        # 1. PROCESS MONTHLY FIRST (Priority for the reconstructed Master timeline)
        from parser import ReportParser
        p = ReportParser()
        
        for m_entry in monthly_data:
            weekly_labour = m_entry.get("weekly_labour", [])
            weekly_weather = m_entry.get("weekly_weather", [])
            weekly_periods = m_entry.get("weekly_periods", [])
            
            for i, period in enumerate(weekly_periods):
                w_start = p._parse_weekly_start_date(period)
                if not w_start: continue
                
                w_entry = {
                    "_sort_date": w_start,
                    "labour": weekly_labour[i] if i < len(weekly_labour) else {},
                    "weather": weekly_weather[i] if i < len(weekly_weather) else [],
                    "materials_sum": m_entry.get("materials_sum", {})
                }
                process_entry(w_entry)

        # 2. PROCESS WEEKLY SECOND (Fill in any additional weeks not in the Master)
        for entry in all_data:
            process_entry(entry)
        
        daily_timeline.sort(key=lambda x: x["date"])
        return daily_timeline

    def get_correlations(self):
        """
        Calculates correlation data for heatmaps and scatter plots.
        Labour vs Materials, Labour vs Weather.
        """
        daily = self.get_daily_trends()
        if not daily: return {}
        
        import pandas as pd
        df = pd.DataFrame(daily)
        
        # Simple correlation matrix
        corr = df[["labour", "materials", "weather_disrupted"]].corr().to_dict()
        
        return {
            "matrix": corr,
            "scatter_labour_materials": df[["labour", "materials"]].to_dict(orient="records"),
            "weather_impact_data": df.groupby("weather_disrupted")["labour"].mean().to_dict()
        }

    def _get_all_data(self, source="weekly"):
        """Reads all JSON reports from history and cache for processing."""
        target_dir = self.history_dir if source == "weekly" else self.monthly_dir
        all_data = []
        
        if not os.path.exists(target_dir):
            return []

        history_files = [f for f in os.listdir(target_dir) if f.endswith('.json')]
        
        # 1. Process Cache (Weekly only)
        if source == "weekly":
            cache_dir = "cache"
            if os.path.exists(cache_dir):
                cache_files = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir) if f.startswith("WEEKLY_") and f.endswith(".json")]
                for cf in cache_files:
                    try:
                        with open(cf, "r") as f:
                            data = json.load(f)
                            if "reporting_period" in data and "_display_date" not in data:
                                data["_display_date"] = data["reporting_period"]
                                # USE GLOBAL ReportParser() DIRECTLY
                                data["_sort_date"] = ReportParser()._parse_weekly_start_date(data["reporting_period"])
                            all_data.append(data)
                    except: continue

        for f_name in history_files:
            file_path = os.path.join(target_dir, f_name)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    # Support legacy daily-reports-as-weekly
                    if source == "weekly" and "report_date" in data:
                        data["_display_date"] = data.get("report_date")
                        
                    # Calculate sort date
                    period = data.get("report_date") or data.get("reporting_period") or ""
                    
                    if source == "weekly":
                        start_dt = ReportParser()._parse_weekly_start_date(period)
                    else:
                        match = re.search(r"(\w+)\s+(\d{4})", period)
                        if match:
                            start_dt = datetime.strptime(f"01 {match.group(1)} {match.group(2)}", "%d %B %Y")
                        else:
                            start_dt = datetime.now() # Fallback

                    if start_dt:
                        data["_sort_date"] = start_dt
                        data["_display_date"] = period
                        all_data.append(data)
            except Exception as e:
                logger.error(f"Error reading {f}: {e}")
        
        all_data.sort(key=lambda x: x["_sort_date"])
        return all_data

    def get_historical_trends(self, source="weekly"):
        """Returns unique summarized data points for the trend charts."""
        # 1. Collect all raw data
        raw_weekly = self._get_all_data(source="weekly")
        raw_monthly = self._get_all_data(source="monthly")
        
        # 2. Use a dictionary to enforce uniqueness by date period
        unique_trends = {} # Key: _display_date, Value: Normalized Data

        # Process Monthly Data First (Priority for "Exact" reconstructed weeks)
        for m_entry in raw_monthly:
            weekly_periods = m_entry.get("weekly_periods", [])
            weekly_labour = m_entry.get("weekly_labour", [])
            
            for i, period in enumerate(weekly_periods):
                if not period: continue
                
                w_start = ReportParser()._parse_weekly_start_date(period)
                if not w_start: continue
                
                # Use date string as key for absolute uniqueness
                date_key = w_start.strftime("%Y-%m-%d")
                if date_key in unique_trends: continue
                
                # Extract Contractual/Financial context from Master
                # Schema: pct_work, instructions, challenges, health_safety, security
                instructions = m_entry.get("instructions", [])
                
                # Calculate personnel average for this period in the Master
                total_list = weekly_labour[i].get("TOTAL", []) if i < len(weekly_labour) else []
                vals = [self._clean_val(v) for v in total_list if self._clean_val(v) > 0]
                avg_labour = sum(vals) / len(vals) if vals else 0
                
                # 1. Precise Weather Extraction (Deep Month Sweep)
                # 1. Precise Weather Extraction (Total Month Scan)
                weather_weeks = m_entry.get("weekly_weather", [])
                
                # Flatten ALL days from ALL weeks in the Master to avoid index offsets
                all_days_in_master = []
                if isinstance(weather_weeks, list):
                    for week_list in weather_weeks:
                        if isinstance(week_list, list):
                            all_days_in_master.extend(week_list)

                rain_detected = False
                weather_notes = []
                
                # Scan every day we found in the master
                for day_log in all_days_in_master:
                    if not isinstance(day_log, dict): continue
                    
                    # We only care about days that fall within our current month/context
                    prose = " ".join([str(day_log.get(k, "")) for k in ["morning", "afternoon", "evening", "condition"]]).lower()
                    
                    if "rain" in prose or "shower" in prose:
                        # Find the date or day to make the note useful
                        d_label = day_log.get("date_str") or day_log.get("day", "Unknown Day")
                        note = f"{d_label}: {day_log.get('condition') or day_log.get('morning')}"
                        
                        # Only add to this week's trends if the date likely belongs here 
                        # (For now, we add to all weeks to ensure AI sees the disruption context)
                        rain_detected = True
                        if note not in weather_notes:
                            weather_notes.append(note)

                # 2. Descriptive Material Summary (Full Detail: Names + Qty + Units)
                m_sum = m_entry.get("materials_sum", {})
                mat_lines = [f"{n} ({i.get('qty')} {i.get('unit')})" for n, i in list(m_sum.items())[:5]]
                materials_desc = f"{len(m_sum)} categories: {', '.join(mat_lines)}" if m_sum else "0 categories"

                unique_trends[date_key] = {
                    "sort_date": w_start,
                    "label": period, 
                    "value": round(avg_labour, 1),
                    "materials": materials_desc,
                    "weather_disrupted": rain_detected,
                    "weather_comments": weather_notes,
                    "prose_summary": m_entry.get("overall_summary", ""),
                    "work_completed_percent": m_entry.get("pct_work", "0%"),
                    "time_elapsed_percent": m_entry.get("pct_period", "0%"),
                    "site_instructions": [
                        {
                            "text": si.get("instruction_issued"),
                            "date": si.get("date"),
                            "given_by": si.get("INSTRUCTIONS GIVEN BY")
                        } for si in instructions if si.get("instruction_issued")
                    ],
                    "critical_warnings": [
                        str(m_entry.get("challenges", "")),
                        str(m_entry.get("health_safety", "")),
                        str(m_entry.get("security", ""))
                    ]
                }

        # Process Weekly Data (Fill in anything not covered by the Master)
        for d in raw_weekly:
            period = d.get("_display_date", "Unknown")
            if not period: continue
            
            w_start = d.get("_sort_date", datetime.min)
            if not isinstance(w_start, datetime):
                w_start = ReportParser()._parse_weekly_start_date(period) or datetime.min
            
            date_key = w_start.strftime("%Y-%m-%d")
            if date_key in unique_trends: continue
            
            # Detect schema
            labour_data = d.get("labour_daily") or d.get("labour") or {}
            weather_data = d.get("weather_daily") or {}
            
            # Extract totals
            totals = []
            if isinstance(labour_data, dict):
                for date_key_day, day_data in labour_data.items():
                    if isinstance(day_data, dict) and "TOTAL" in day_data:
                        totals.append(self._clean_val(day_data["TOTAL"]))
            
            val = sum(totals) / len(totals) if totals else 0
            is_disrupted = any(day.get("Condition") != "Workable" for day in weather_data.values()) if isinstance(weather_data, dict) else False
            weather_comments = [day.get("Comments") for day in weather_data.values() if day.get("Comments")]
            
            unique_trends[date_key] = {
                "sort_date": w_start,
                "label": period,
                "value": round(val, 1),
                "materials": d.get("materials_count", 0),
                "weather_disrupted": is_disrupted,
                "weather_comments": weather_comments,
                "prose_summary": d.get("executive_summary", ""),
                "work_completed_percent": "N/A",
                "time_elapsed_percent": "N/A",
                "site_instructions": [],
                "critical_warnings": []
            }

        # 3. Sort chronologically and return
        sorted_trends = sorted(unique_trends.values(), key=lambda x: x["sort_date"])
        
        # Clean up for frontend
        return [
            {
                "label": t["label"], 
                "value": t["value"], 
                "materials": t["materials"],
                "weather_disrupted": t.get("weather_disrupted", False),
                "weather_comments": t.get("weather_comments", []),
                "prose_summary": t.get("prose_summary", ""),
                "financial_progress": t.get("work_completed_percent"),
                "time_progress": t.get("time_elapsed_percent"),
                "instructions": t.get("site_instructions", []),
                "warnings": t.get("critical_warnings", [])
            } for t in sorted_trends
        ]

    async def generate_ai_insights(self, trends: Dict[str, Any], contract_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced AI Insights with SWOT and detailed recommendations.
        """
        prompt = f"""
        You are a Senior Project Management Consultant for a high-value affordable housing project.
        
        Based ONLY on the following historical data (including numerical trends and qualitative site comments), provide a comprehensive analysis.
        
        PROJECT CONTEXT:
        {json.dumps(contract_context, indent=2)}
        
        HISTORICAL TRENDS & QUALITATIVE DATA (Weather Comments & Prose Summaries):
        {json.dumps(trends, indent=2)}
        
        Your analysis MUST include:
        1. FINANCIAL & PROGRESS AUDIT (CRITICAL):
           - Revenue Audit: Calculate Revenue Earned = (Contract Sum) * (% Work Completed / 100). Mention the approximate value in your summary.
           - Slippage Audit: Compare % Time Elapsed vs % Work Completed.
           - THE 10% RULE: If (% Time Elapsed - % Work Completed) > 10%, you MUST explicitly flag this as "SLUGGISH PROGRESS" or "SCHEDULE SLIPPAGE" in Weaknesses/Threats.
           - Verify if site comments (rain, material delays, slow mobilization) justify this slippage or if it indicates underlying contractor inefficiency.

        2. SWOT Analysis: Strengths, Weaknesses, Opportunities, and Threats. 
           - Use the 'prose_summary' and 'weather_comments' to explain the momentum.
           - STRICTURE: NEVER claim 'optimal' or 'clear' weather if the 'weather_comments' mention rain or disruptions.
           - Audit 'site_instructions' against their issuance dates: Did the contractor comply promptly? 
             Compare the instruction date with subsequent personnel and progress shifts.
           - Strengths (e.g., consistent labour, good weather handling)
           - Weaknesses (e.g., progress lag, supply chain gaps, low turnout)
           - Opportunities (e.g., clear weather windows, resource reallocation)
           - Threats (e.g., liquidated damages risk due to slippage, security incidents)
        
        2. STAKEHOLDER RECOMMENDATIONS:
           - TO THE CLIENT (PM): Strategic moves to protect the budget and timeline.
           - TO THE CONTRACTOR: Operational improvements to boost productivity.
        
        3. EXECUTIVE SUMMARY & VERDICT:
           - Summary of momentum.
           - Claim probability assessment.

        Return the analysis in JSON matching this schema:
        {{
            "swot": {{
                "strengths": ["string"],
                "weaknesses": ["string"],
                "opportunities": ["string"],
                "threats": ["string"]
            }},
            "recommendations": {{
                "to_client": ["string"],
                "to_contractor": ["string"]
            }},
            "executive_summary": "string",
            "critical_advice": "string",
            "claim_verdict": "string (Low/Moderate/High)"
        }}
        """
        
        try:
            result = await generate_summary_json(prompt)
            return result
        except Exception as e:
            logger.error(f"AI Insights generation failed: {e}")
            return {
                "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
                "recommendations": {"to_client": ["Error generating AI insights."], "to_contractor": []},
                "executive_summary": "Error generating insights.",
                "claim_verdict": "Unknown"
            }
