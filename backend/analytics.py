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
        raw_dailies = self._get_all_data(source="daily")
        
        daily_timeline = []
        seen_dates = set()
        
        def _parse_daily_date(date_str):
            import re
            from datetime import datetime
            if not date_str: return None
            cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str, flags=re.IGNORECASE)
            cleaned = cleaned.replace(",", " ").strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            formats = [
                "%A %d %B %Y",
                "%d %B %Y",
                "%A %d %b %Y",
                "%d %b %Y",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d",
            ]
            for fmt in formats:
                try: return datetime.strptime(cleaned, fmt)
                except: continue
            match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", cleaned)
            if match:
                try: return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                except: pass
            return None
        
        # PROCESS DAILY FILES DIRECTLY
        for entry in raw_dailies:
            dt = _parse_daily_date(entry.get("date", ""))
            if not dt: continue
            
            date_key = dt.strftime("%Y-%m-%d")
            if date_key in seen_dates: continue
            
            labour = entry.get("labour", {})
            total_labour = self._clean_val(labour.get("TOTAL", "0"))
            mat_count = len(entry.get("materials_delivered", []))
            
            w_stats = entry.get("weather", {})
            weather_disrupted = 1 if "favorable" not in str(w_stats).lower() and "sunny" not in str(w_stats).lower() and "-" not in str(w_stats) else 0
            
            daily_timeline.append({
                "date": date_key,
                "labour": total_labour,
                "materials": mat_count,
                "weather_disrupted": weather_disrupted,
                "is_weekend": 1 if dt.weekday() >= 5 else 0,
                "financial_progress": entry.get("pct_work_done") or "0%",
                "time_progress": entry.get("pct_period_elapsed") or entry.get("time_lapsed_weeks") or "0%"
            })
            seen_dates.add(date_key)
            
        daily_timeline.sort(key=lambda x: x["date"])
        return daily_timeline

    def get_correlations(self, financials_data=None):
        """
        Calculates correlation data for heatmaps and scatter plots.
        Uses Weekly data to match the financial reporting cycle.
        """
        raw_weekly = self._get_all_data(source="weekly")
        if not raw_weekly or not financials_data: return {}
        
        weekly_fin = financials_data.get("weekly_financials", [])
        # We need to map by normalized label to match financial_engine deduplication
        import re
        fin_map = {re.sub(r'[^a-z0-9]', '', str(w["label"]).lower()): w for w in weekly_fin}
        
        merged_data = []
        for w in raw_weekly:
            date_label = w.get("_display_date") or w.get("label", "Unknown Week")
            norm_label = re.sub(r'[^a-z0-9]', '', str(date_label).lower())
            
            fin = fin_map.get(norm_label)
            if not fin: continue
            
            # User's exact mathematical formula for Average Labour Turnover
            # Total labour that week / ((number of non zero value categories in mon+tue+...)/7)
            daily_labour = w.get("labour_daily", {})
            total_labour_week = 0
            non_zero_categories = 0
            
            for day, categories in daily_labour.items():
                if not isinstance(categories, dict): continue
                for cat_name, cat_val in categories.items():
                    val = self._clean_val(cat_val)
                    if cat_name == "TOTAL":
                        total_labour_week += val
                    else:
                        if val > 0:
                            non_zero_categories += 1
                            
            if non_zero_categories > 0:
                # The user's formula
                avg_labour = round(total_labour_week / (non_zero_categories / 7.0), 2)
            else:
                avg_labour = 0
                
            if avg_labour > 0: # Exclude dead weeks
                merged_data.append({
                    "date": date_label,
                    "labour": avg_labour,
                    "pct_work": fin["pct_work"],
                    "slippage_gap": fin["slippage_gap"]
                })
                
        if not merged_data: return {}
        
        import pandas as pd
        df = pd.DataFrame(merged_data)
        
        # Simple correlation matrix
        corr = df[["labour", "pct_work", "slippage_gap"]].corr().fillna(0).to_dict()
        
        return {
            "matrix": corr,
            "scatter_labour_slippage": df[["labour", "slippage_gap"]].to_dict(orient="records"),
            "scatter_labour_progress": df[["labour", "pct_work"]].to_dict(orient="records")
        }

    def _get_all_data(self, source="weekly"):
        """Reads all JSON reports from history and cache for processing."""
        target_dir = self.history_dir if source == "weekly" else self.monthly_dir
        all_data = []
        
        history_files = [f for f in os.listdir(target_dir) if f.endswith('.json')] if os.path.exists(target_dir) else []
        
        # 1. Process Cache (Weekly and Daily)
        if source in ["weekly", "daily"]:
            cache_dir = "cache"
            prefix = "WEEKLY_" if source == "weekly" else "DAILY_"
            if os.path.exists(cache_dir):
                cache_files = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir) if f.startswith(prefix) and f.endswith(".json")]
                for cf in cache_files:
                    try:
                        with open(cf, "r") as f:
                            data = json.load(f)
                            if source == "weekly" and "reporting_period" in data and "_display_date" not in data:
                                data["_display_date"] = data["reporting_period"]
                                # USE GLOBAL ReportParser() DIRECTLY
                                data["_sort_date"] = ReportParser()._parse_weekly_start_date(data["reporting_period"])
                                all_data.append(data)
                                logger.debug(f"Successfully read cache file {cf} (Period: {data['reporting_period']})")
                            elif source == "daily" and "date" in data:
                                all_data.append(data)
                                logger.debug(f"Successfully read cache file {cf} (Daily Date: {data['date']})")
                    except Exception as e:
                        logger.error(f"Failed to read cache file {cf}: {e}")
                        continue

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
                        logger.debug(f"Successfully read history file {file_path} (Period: {period})")
            except Exception as e:
                logger.error(f"Error reading {f_name}: {e}")
                logger.error(f"Failed to read history file {file_path}: {e}")
        
        all_data.sort(key=lambda x: x.get("_sort_date", datetime.min) if isinstance(x.get("_sort_date"), datetime) else datetime.min)
        return all_data

    def get_historical_trends(self, source="weekly"):
        """Returns unique summarized data points for the trend charts."""
        # 1. Collect all raw data
        raw_weekly = self._get_all_data(source="weekly")
        raw_monthly = self._get_all_data(source="monthly")
        
        # 2. Use a dictionary to enforce uniqueness by date period
        unique_trends = {} # Key: _display_date, Value: Normalized Data
        consumed_weekly_dates = set()

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
                if date_key in unique_trends and unique_trends[date_key].get("value", 0) > 0: continue
                
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

                # Strategy: Match the actual standalone weekly report using the parsed start date (allow 3 days variance for month boundaries)
                w_match = next((w for w in raw_weekly if w.get("_sort_date") and abs((w.get("_sort_date").date() - w_start.date()).days) <= 4), None)
                
                if w_match:
                    # Found the specific weekly JSON - extract verbatim
                    m_delivered = w_match.get("materials_delivered", [])
                    # Filter out materials with 0 quantity
                    valid_materials = [m for m in m_delivered if m.get("quantity") and str(m.get("quantity")).strip() not in ["0", "0.0", "None", "", "0 Tons", "0 kgs"]]
                    m_lines = [f"{m.get('description', 'Unknown').upper()} ({m.get('quantity', '0')})" for m in valid_materials[:5]]
                    materials_desc = f"{len(valid_materials)} categories: {', '.join(m_lines)}" if valid_materials else "0 categories"
                    # Adopt the true reporting period from the weekly file if available
                    period = w_match.get("_display_date", period)
                    if w_match.get("_sort_date"):
                        consumed_weekly_dates.add(w_match.get("_sort_date").strftime("%Y-%m-%d"))
                else:
                    # Fallback to Master data (per-week list if available)
                    m_list = m_entry.get("weekly_materials", [])
                    if i < len(m_list):
                        materials_desc = m_list[i]
                    else:
                        # Final Fallback to monthly total (Legacy)
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
                    "work_completed_percent": (w_match.get("pct_work_done") if w_match else None) or (w_match.get("work_completed_percent") if w_match else None) or m_entry.get("pct_work_done") or m_entry.get("pct_work") or "0%",
                    "time_elapsed_percent": (w_match.get("pct_period_elapsed") if w_match else None) or (w_match.get("time_elapsed_percent") if w_match else None) or m_entry.get("pct_period_elapsed") or m_entry.get("pct_period", "0%"),
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
            if date_key in unique_trends and unique_trends[date_key].get("value", 0) > 0: continue
            
            # Detect schema
            labour_data = d.get("labour_daily") or d.get("labour") or {}
            weather_data = d.get("weather_daily") or d.get("weather") or {}
            
            # Extract totals
            totals = []
            if isinstance(labour_data, dict):
                for date_key_day, day_data in labour_data.items():
                    if isinstance(day_data, dict) and "TOTAL" in day_data:
                        totals.append(self._clean_val(day_data["TOTAL"]))
                if not totals and "TOTAL" in labour_data:
                    total_list = labour_data["TOTAL"]
                    if isinstance(total_list, list):
                        totals = [self._clean_val(v) for v in total_list if self._clean_val(v) > 0]
                    elif isinstance(total_list, (str, int, float)):
                        totals = [self._clean_val(total_list)]
            elif isinstance(labour_data, list):
                for day_data in labour_data:
                    if isinstance(day_data, dict) and "TOTAL" in day_data:
                        totals.append(self._clean_val(day_data["TOTAL"]))
            
            val = sum(totals) / len(totals) if totals else 0
            
            is_disrupted = False
            weather_comments = []
            
            def _check_disrupted(day_info):
                if not isinstance(day_info, dict): return False
                cond = str(day_info.get("Condition") or day_info.get("condition") or "").lower()
                morn = str(day_info.get("morning") or "").lower()
                aft = str(day_info.get("afternoon") or "").lower()
                eve = str(day_info.get("evening") or "").lower()
                combined = f"{cond} {morn} {aft} {eve}"
                if any(x in combined for x in ["rain", "shower", "storm", "wet", "flood"]):
                    return True
                if "unfavorable" in combined or "semi-favorable" in combined or "disrupted" in combined:
                    return True
                return False

            if isinstance(weather_data, dict):
                is_disrupted = any(_check_disrupted(day) for day in weather_data.values())
                weather_comments = [
                    day.get("Comments") or day.get("Comments Given") or day.get("comments") or day.get("condition") or day.get("morning")
                    for day in weather_data.values()
                    if isinstance(day, dict) and (day.get("Comments") or day.get("Comments Given") or day.get("comments") or day.get("condition") or day.get("morning"))
                ]
            elif isinstance(weather_data, list):
                is_disrupted = any(_check_disrupted(day) for day in weather_data)
                weather_comments = [
                    day.get("Comments") or day.get("Comments Given") or day.get("comments") or day.get("condition") or day.get("morning")
                    for day in weather_data
                    if isinstance(day, dict) and (day.get("Comments") or day.get("Comments Given") or day.get("comments") or day.get("condition") or day.get("morning"))
                ]
            
            m_delivered = d.get("materials_delivered", [])
            valid_mats = [m for m in m_delivered if m.get("quantity") and str(m.get("quantity")).strip() not in ["0", "0.0", "None", "", "0 Tons", "0 kgs"]]
            m_lines = [f"{m.get('description', 'Unknown').upper()} ({m.get('quantity', '0')})" for m in valid_mats[:5]]
            materials_val = f"{len(valid_mats)} categories: {', '.join(m_lines)}" if valid_mats else "0 categories"
            if not m_delivered:
                materials_val = d.get("materials_count", 0)
                
            unique_trends[date_key] = {
                "sort_date": w_start,
                "label": period,
                "value": round(val, 1),
                "materials": materials_val,
                "weather_disrupted": is_disrupted,
                "weather_comments": weather_comments,
                "prose_summary": d.get("executive_summary", ""),
                "work_completed_percent": d.get("pct_work_done") or d.get("pct_work") or d.get("work_completed_percent") or "N/A",
                "time_elapsed_percent": d.get("pct_period_elapsed") or d.get("pct_period") or d.get("time_elapsed_percent") or "N/A",
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

    async def generate_ai_insights(self, trends: Dict[str, Any], contract_context: Dict[str, Any], financials: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced AI Insights with SWOT and detailed recommendations.
        """
        calculated_verdict = "Low" # Default fallback
        run_rate_context = "No run-rate data available."
        if financials:
            latest_fin = None
            if financials.get("weekly_financials"):
                latest_fin = financials["weekly_financials"][-1]
            elif financials.get("daily_financials"):
                latest_fin = financials["daily_financials"][-1]
                
            # Final run_rate_context for the prompt
            run_rate_context = "PROJECT MOMENTUM ANALYSIS: Focus on the Slippage Gap (%) and Recalibrated Weekly targets to assess health."

            # Calculate hard-coded verdict to force AI consistency
            slippage = latest_fin.get("slippage_gap", 0) if latest_fin else 0
            if slippage <= 10:
                calculated_verdict = "Low"
            elif slippage <= 15:
                calculated_verdict = "Moderate"
            elif slippage <= 25:
                calculated_verdict = "High"
            else:
                calculated_verdict = "Critical"

        # Load all uploaded project correspondence to enrich the AI context!
        docs_text = ""
        docs_dir = os.path.join("cache", "project_documents")
        if os.path.exists(docs_dir):
            docs_list = []
            for f_name in os.listdir(docs_dir):
                if f_name.endswith(".json"):
                    try:
                        with open(os.path.join(docs_dir, f_name), "r") as f:
                            doc_data = json.load(f)
                            docs_list.append(doc_data)
                    except:
                        continue
            if docs_list:
                docs_text = "\nPROJECT CORRESPONDENCE & KEY COMMUNICATIONS REGISTER:\n"
                for idx, doc in enumerate(docs_list):
                    docs_text += f"{idx+1}. Title: {doc.get('title')}\n"
                    docs_text += f"   Category: {doc.get('category').upper()} | Date Sent: {doc.get('date_sent')} | From: {doc.get('sender')} | To: {doc.get('recipient')}\n"
                    docs_text += f"   AI Summary: {doc.get('summary')}\n"
                    ai_a = doc.get("ai_analysis", {})
                    if ai_a:
                        docs_text += f"   Core Requests: {', '.join(ai_a.get('requests_made', []))}\n"
                        docs_text += f"   Detailed Analysis: {ai_a.get('detailed_analysis')}\n"
                        docs_text += f"   Contractual Implications: {ai_a.get('contractual_implications')}\n"
                    docs_text += "\n"

        prompt = f"""
        You are a Senior Project Management Consultant for a high-value affordable housing project.
        
        STRICT REQUIREMENT: The Contractual Exposure Level for this report is {calculated_verdict.upper()}. 
        You MUST use "{calculated_verdict}" as the value for 'claim_verdict' in your JSON response.
        
        Based ONLY on the following historical data (including numerical trends and qualitative site comments), provide a comprehensive analysis.
        
        PROJECT CONTEXT:
        {json.dumps(contract_context, indent=2)}
        
        HISTORICAL TRENDS & QUALITATIVE DATA (Weather Comments & Prose Summaries):
        {json.dumps(trends, indent=2)}
        
        PRE-CALCULATED FINANCIAL & SLIPPAGE DATA:
        {json.dumps(financials, indent=2) if financials else "No financial data available."}
        
        {run_rate_context}
        
        PROJECT CORRESPONDENCE & COMMUNICATIONS (LETTERS/REQUESTS/INSTRUCTIONS):
        {docs_text if docs_text else "No correspondence or requests uploaded yet."}
        
         Your analysis MUST include:
         
         STRICT TIMELINE & DOCUMENT CHRONOLOGY RULE:
        Whenever you reference any correspondence, claims, schedules, instructions, or Program of Works in the SWOT analysis or recommendations, you MUST ALWAYS explicitly cite the document's subject/title followed immediately by its "Date Sent" in parentheses, for example: "Letter regarding EOT No. 3 (Sent: 15th May 2026)" or "Program of Works Recovery baseline (Sent: 24th April 2026)". 
        This is critical for tracking baseline revisions, comparing old submissions against newer revisions, and reviewing how chronological timeline events mature over the life of the project. Contrasting early proposals with down-the-line revisions is essential.

        1. FINANCIAL & RECALIBRATION ANALYSIS (CRITICAL):
           - DO NOT calculate the revenue or slippage yourself. Use the exact values provided in the "PRE-CALCULATED FINANCIAL & SLIPPAGE DATA" section.
           - MONTHLY PERFORMANCE: Analyze the last completed month (e.g. April 2026). Compare the 'actual_production' vs 'envisaged_production'. Explicitly state if it was a shortfall or an achievement and by how much.
           - RECALIBRATION TARGETS: Discuss the 'required_weekly' rate for the ongoing month (e.g. May 2026). Explain why this acceleration is necessary (or why it has decreased) based on the historical chain.
           - SLIPPAGE SEVERITY LEVELS:
             * 0% - 10%: ON TRACK (Emerald). Frame as maintainable.
             * 10.1% - 15%: MODERATE SLIPPAGE (Amber). Frame as a minor divergence requiring tactical adjustment.
             * 15.1% - 25%: HIGH SLIPPAGE (Orange). Frame as a significant concern requiring a detailed catch-up plan.
             * > 25%: CRITICAL DELAY (Red). Frame as an urgent priority for executive intervention.
           - THE 10% THRESHOLD: 10% is the baseline tolerance. Only start flagging concerns when slippage exceeds this.
           - RECALIBRATION CHAIN: Reference the weekly variance (k) from the Recalibration Chain table to explain where the momentum was lost or gained.
           - TONE: Maintain a highly constructive, partner-oriented tone. Frame delays as shared challenges to be solved with the contractor. Avoid alarmist language for moderate slippage.
 
        2. SWOT Analysis: Strengths, Weaknesses, Opportunities, and Threats. 
           - Use the 'prose_summary', 'weather_comments', recalibration deltas, and the uploaded Project Correspondence/Communications to explain the momentum, risks, EOT claims, and timeline impacts.
           - STRICTURE: NEVER claim 'optimal' or 'clear' weather if the 'weather_comments' mention rain.
           - Review 'site_instructions' against their issuance dates: Did subsequent production (actual vs envisaged) improve after instructions were issued?
           - Strengths (e.g., consistent labour, recovering slippage in specific weeks)
           - Weaknesses (e.g., production shortfall in April, widening variance)
           - Opportunities (e.g., clear weather windows, catching up to the recalibrated May target)
           - Threats (e.g., liquidated damages risk, security incidents)
        
        2. STAKEHOLDER RECOMMENDATIONS:
           - TO THE CLIENT (PM): Strategic moves to protect the budget and timeline.
           - TO THE CONTRACTOR: Operational improvements to boost productivity and hit the recalibrated weekly targets.
        
        3. EXECUTIVE SUMMARY & VERDICT:
           - Summary of momentum and overall health.
           - CLAIM & RISK VERDICT (claim_verdict): 
             * IMPORTANT: Base this level ONLY on the Slippage Gap % levels below. IGNORE the "Projected Variance (Days)" or "Completion Date" when choosing this level.
             * 'Low': If slippage is <= 10%. Frame as "Manageable operational variance."
             * 'Moderate': If slippage is 10.1% - 15%. Frame as "Significant divergence requiring monitoring."
             * 'High': If slippage is 15.1% - 25%. Frame as "Critical schedule exposure."
             * 'Critical': If slippage is > 25%. Frame as "Urgent schedule recovery required."
           - CRITICAL STRICTURE: DO NOT mention the "Projected Variance" (e.g., '1209 Days LATE') or the estimated completion date (e.g., '18 Mar 2031') in the executive_summary or recommendations. These are for internal reference only. Instead, refer to the Slippage Gap %, Revenue earned, and the Recalibrated Monthly targets to describe the status.
           - Ensure the executive_summary reflects the TONE of the assigned slippage level (Constructive for Low/Moderate, Urgent for High/Critical).
.

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
            "claim_verdict": "string (Low/Moderate/High/Critical)"
        }}
        """
        
        try:
            result = await generate_summary_json(prompt)
            # FORCE OVERRIDE: The AI is sometimes stubborn; we overwrite its verdict with our hard-coded logic.
            if isinstance(result, dict):
                result["claim_verdict"] = calculated_verdict
                result["_generated_at"] = datetime.now().strftime("%d %B %Y, %I:%M %p")
                logger.info(f"✅ AI Insights generated with FORCED VERDICT: {calculated_verdict}")
            return result
        except Exception as e:
            logger.error(f"AI Insights generation failed: {e}")
            return {
                "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
                "recommendations": {"to_client": ["Error generating AI insights."], "to_contractor": []},
                "executive_summary": "Error generating insights.",
                "claim_verdict": calculated_verdict # Use the safe calculated value
            }
