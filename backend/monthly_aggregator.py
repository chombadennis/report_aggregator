import json
import os
import hashlib
import re
from datetime import datetime, timedelta
import calendar
from typing import List, Dict, Any
from schemas import WeeklyReportSchema, MonthlyReportSchema, SiteInstruction

class MonthlyAggregator:
    def __init__(self, history_dir="history_monthly"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    def _save_to_history(self, data, report_type="MONTHLY"):
        content_str = json.dumps(data, sort_keys=True)
        unique_id = hashlib.sha256(content_str.encode()).hexdigest()[:12]
        filename = f"{report_type.lower()}_{unique_id}.json"
        history_path = os.path.join(self.history_dir, filename)
        with open(history_path, "w") as f:
            json.dump(data, f, indent=2)
        return history_path

    def _parse_month_year(self, title: str):
        """Extracts month and year from 'MONTHLY REPORT (MARCH 2026)'"""
        match = re.search(r"\((.*?)\s+(\d{4})\)", title)
        if match:
            month_name = match.group(1).upper()
            year = int(match.group(2))
            try:
                month_num = datetime.strptime(month_name, "%B").month
                return month_num, year
            except:
                pass
        return None, None

    def get_expected_weeks(self, month: int, year: int):
        """Calculates the list of Monday-Sunday periods that cover the given month."""
        first_day = datetime(year, month, 1)
        # Monday of the first week (Monday is 0)
        start_monday = first_day - timedelta(days=first_day.weekday())
        
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = datetime(year, month, last_day_num)
        # Sunday of the last week
        end_sunday = last_day + timedelta(days=(6 - last_day.weekday()))
        
        weeks = []
        curr = start_monday
        while curr <= end_sunday:
            week_end = curr + timedelta(days=6)
            
            # Clip label to month boundaries
            label_start = max(curr, first_day)
            label_end = min(week_end, last_day)
            
            # Determine which day indices (0=Mon, 6=Sun) are in the month
            valid_day_indices = []
            for d in range(7):
                day_dt = curr + timedelta(days=d)
                if first_day <= day_dt <= last_day:
                    valid_day_indices.append(d)

            weeks.append({
                "start": curr,
                "end": week_end,
                "valid_days": valid_day_indices,
                "label": f"{label_start.strftime('%d').lstrip('0')}{self._get_day_suffix(label_start.day)} {label_start.strftime('%B')} – {label_end.strftime('%d').lstrip('0')}{self._get_day_suffix(label_end.day)} {label_end.strftime('%B %Y')}".upper()
            })
            curr += timedelta(days=7)
        return weeks

    def _get_day_suffix(self, day):
        if 11 <= day <= 13: return 'th'
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

    def _is_in_month(self, date_str: str, target_month: int, target_year: int):
        """
        Checks if 'Day YYYY-MM-DD' or 'YYYY-MM-DD' is within the target month/year.
        Includes a fallback for AI year hallucinations (e.g. 2023 instead of 2026).
        """
        try:
            if " " in date_str: date_str = date_str.split(" ")[-1]
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Strict Month/Year Check
            if dt.month == target_month and dt.year == target_year:
                return True
                
            # Recovery: If month matches but year is wrong, check if it's a common AI hallucination
            # We trust the target_year provided in metadata more than the AI's OCR of a single digit.
            if dt.month == target_month and (dt.year == 2023 or dt.year == 2024 or dt.year == 2025):
                # Only recover if the day also exists in the target year
                try:
                    datetime(target_year, dt.month, dt.day)
                    return True 
                except: return False
                
            return False
        except:
            return False

    def validate_chronology(self, results: List[Dict[str, Any]], target_month: int, target_year: int):
        """
        Validates that the set of uploaded reports is chronological and matches the target month.
        Returns a list of warning/error messages.
        """
        from parser import ReportParser
        parser = ReportParser() # To reuse date parsing logic
        
        valid_reports = []
        warnings = []

        for res in results:
            period = res.get("reporting_period", "")
            if not period: continue
            
            start_dt = parser._parse_weekly_start_date(period)
            if start_dt:
                valid_reports.append((start_dt, res))
            else:
                warnings.append(f"⚠️ Could not verify period for: {res.get('title', 'Unknown')}")

        # Sort by date
        valid_reports.sort(key=lambda x: x[0])

        if not valid_reports:
            return ["❌ No valid dates found in uploaded reports."]

        # Check for Month/Year mismatch
        # Allow overlap: a report is valid if it has AT LEAST ONE day in the target month
        for dt, res in valid_reports:
            end_dt = dt + timedelta(days=6)
            has_days_in_month = False
            for i in range(7):
                day = dt + timedelta(days=i)
                if day.month == target_month and day.year == target_year:
                    has_days_in_month = True
                    break
            
            if not has_days_in_month:
                warnings.append(f"🚩 Report '{res.get('title')}' ({dt.strftime('%d %b')} - {end_dt.strftime('%d %b')}) is outside target month {calendar.month_name[target_month]} {target_year}.")

        # Check for Gaps
        for i in range(len(valid_reports) - 1):
            curr_start = valid_reports[i][0]
            next_start = valid_reports[i+1][0]
            gap = (next_start - curr_start).days
            
            if gap > 7:
                missing_weeks = (gap // 7) - 1
                warnings.append(f"⚠️ Gap detected! Missing {missing_weeks} week(s) between {valid_reports[i][1].get('title')} and {valid_reports[i+1][1].get('title')}.")
            elif gap < 7:
                warnings.append(f"🔄 Overlap/Duplicate detected between {valid_reports[i][1].get('title')} and {valid_reports[i+1][1].get('title')}.")

        return warnings

        return default

    def _get_case_insensitive(self, data: Dict[str, Any], key: str, default: Any = "-"):
        """Case-insensitive dictionary lookup."""
        if not data: return default
        if key in data: return data[key]
        k_lower = key.lower()
        if not isinstance(data, dict): return default
        for k, v in data.items():
            if k.lower() == k_lower:
                return v
        return default

    def _normalize_string(self, s: str):
        """Removes all non-alphanumeric characters and converts to uppercase for robust matching."""
        if not s: return ""
        return re.sub(r'[^A-Z0-9]', '', s.upper())

    def compile_monthly_data(self, weekly_reports: List[Dict[str, Any]], metadata: Dict[str, str]):
        title = metadata.get("title", "MONTHLY REPORT")
        target_month, target_year = self._parse_month_year(title)
        
        # Calculate the 4-6 weeks that cover this month
        expected_weeks = []
        if target_month and target_year:
            expected_weeks = self.get_expected_weeks(target_month, target_year)
        
        # 1. Map available reports to the expected weeks based on dates
        # We'll use a simple approach: if any date in a report falls within the week, it's that week's data.
        weekly_data_map = {} # Week Index -> Weekly Data
        for report in weekly_reports:
            if not isinstance(report, dict): continue
            
            # Look deep into the nested dictionaries to find a date key
            found_date = None
            labour = report.get("labour_daily", {})
            weather = report.get("weather_daily", {})
            
            # Try to find a date in any of the nested keys
            sample_keys = []
            if isinstance(labour, dict):
                for sub in labour.values():
                    if isinstance(sub, dict): sample_keys.extend(sub.keys())
            
            if isinstance(weather, dict):
                sample_keys.extend(weather.keys())
            
            for key in sample_keys:
                match = re.search(r"\d{4}-\d{2}-\d{2}", str(key))
                if match:
                    found_date = datetime.strptime(match.group(0), "%Y-%m-%d")
                    break
            
            if found_date:
                for idx, week in enumerate(expected_weeks):
                    if week["start"] <= found_date <= week["end"]:
                        weekly_data_map[idx] = report
                        break

        # 2. Collect Labour/Weather week by week
        weekly_labour_matrices = []
        weekly_weather_grids = []
        weekly_periods = []
        weather_comments = []
        weekly_materials_list = []
        
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for idx, week in enumerate(expected_weeks):
            weekly_periods.append(week["label"])
            report = weekly_data_map.get(idx)
            
            if not report:
                # Missing week data
                weekly_labour_matrices.append({})
                weekly_weather_grids.append([])
                weather_comments.append("No report available for this period.")
                weekly_materials_list.append("0 categories")
                continue

            # Process Labour for this week using hardcoded categories
            # Hardcoded categories in order
            base_categories = [
                "Site Agent/PM", "Ass. Site Agent", "Office Attendant", "Office Assistant",
                "Foreman", "Operator", "Mason", "Electrician", "Plumbers", "Carpenters",
                "Steel fixers", "Drivers", "Surveyors", "Unskilled", "Safety officer",
                "Store keeper", "Security", "Painters", "Intern"
            ]
            
            # Map of normalized names to official names for better matching
            official_names = {c.upper().replace(" ", ""): c for c in base_categories}
            
            # Initialize with zeros in the correct order
            week_labour_matrix = {cat: ["0"] * 7 for cat in base_categories}
            week_labour_matrix["TOTAL"] = ["0"] * 7
            
            daily_labour = report.get("labour_daily", {})
            if isinstance(daily_labour, dict):
                for date_key, categories in daily_labour.items():
                    is_valid = self._is_in_month(date_key, target_month, target_year)
                    if not is_valid:
                        # Log the exclusion for transparency
                        # print(f"   [Boundary] Skipping data for {date_key} (Outside {calendar.month_name[target_month]} {target_year})")
                        continue
                    
                    try:
                        date_str = date_key.split(" ")[-1] if " " in date_key else date_key
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        w_idx = days_of_week.index(dt.strftime("%A"))
                        if isinstance(categories, dict):
                            for cat, val in categories.items():
                                cat_norm = cat.upper().replace(" ", "")
                                if cat_norm in official_names:
                                    official_cat = official_names[cat_norm]
                                    week_labour_matrix[official_cat][w_idx] = str(val)
                                elif cat_norm == "TOTAL":
                                    week_labour_matrix["TOTAL"][w_idx] = str(val)
                                else:
                                    # If a brand new category is found, insert it before TOTAL
                                    if cat not in week_labour_matrix:
                                        new_matrix = {}
                                        for k, v in week_labour_matrix.items():
                                            if k == "TOTAL":
                                                new_matrix[cat] = ["0"] * 7
                                            new_matrix[k] = v
                                        week_labour_matrix = new_matrix
                                    week_labour_matrix[cat][w_idx] = str(val)
                    except: pass
            
            weekly_labour_matrices.append(week_labour_matrix)

            # Process Weather for this week
            week_weather_grid = []
            daily_weather = report.get("weather_daily", {})
            # Extract date for sorting and filtering
            weather_data = []
            if isinstance(daily_weather, dict):
                for date_key, info in daily_weather.items():
                    if target_month and not self._is_in_month(date_key, target_month, target_year):
                        continue
                    date_str = date_key.split(" ")[-1] if " " in date_key else date_key
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        weather_data.append((dt, date_str, info))
                    except: pass
            
            # Sort by date
            weather_data.sort(key=lambda x: x[0])
            
            for dt, date_str, info in weather_data:
                week_weather_grid.append({
                    "day": dt.strftime("%A"),
                    "date_str": date_str,
                    "morning": self._get_case_insensitive(info, "morning"),
                    "afternoon": self._get_case_insensitive(info, "afternoon"),
                    "evening": self._get_case_insensitive(info, "evening"),
                    "condition": self._get_case_insensitive(info, "condition")
                })
            
            weekly_weather_grids.append(week_weather_grid)
            # Capture comments from weather info
            week_comments = []
            if isinstance(daily_weather, dict):
                for date_str, info in daily_weather.items():
                    if target_month and not self._is_in_month(date_str, target_month, target_year):
                        continue
                    if isinstance(info, dict):
                        c = info.get("comments", "").strip()
                        if c and c.lower() != "none":
                            week_comments.append(c)
            weather_comments.append(" • " + "\n • ".join(week_comments) if week_comments else "None")

            # Capture Materials for this specific week
            week_mat_sum = {}
            if report:
                for item in report.get("materials_delivered", []):
                    if not isinstance(item, dict): continue
                    m_name = (item.get("description") or item.get("Description") or "Unknown").upper().strip()
                    m_qty = item.get("quantity") or item.get("Quantity") or "0"
                    m_unit = item.get("unit") or item.get("units") or item.get("Unit") or ""
                    week_mat_sum[m_name] = {"qty": m_qty, "unit": m_unit}
            
            # Format a compact string for the trend tooltip
            if week_mat_sum:
                m_lines = [f"{n} ({i['qty']} {i['unit']})" for n, i in list(week_mat_sum.items())[:5]]
                m_desc = f"{len(week_mat_sum)} categories: {', '.join(m_lines)}"
            else:
                m_desc = "0 categories"
            
            weekly_materials_list.append(m_desc)

        # 2. Aggregated Sections
        latest_week = weekly_reports[-1] if weekly_reports else {}
        
        # Materials Summation
        materials_sum = {}
        # Default units provided by the user for fallback (matching is Case-Insensitive)
        default_units = {
            "BALLAST": "tons",
            "AGGREGATES": "tons",
            "FOUNDATION STONES": "ft.",
            "D8": "pcs", "T8": "pcs", "Y8": "pcs", "R8": "pcs",
            "D10": "pcs", "T10": "pcs", "Y10": "pcs", "R10": "pcs",
            "D12": "pcs", "T12": "pcs", "Y12": "pcs", "R12": "pcs",
            "D16": "pcs", "T16": "pcs", "Y16": "pcs", "R16": "pcs",
            "D20": "pcs", "T20": "pcs", "Y20": "pcs", "R20": "pcs",
            "D25": "pcs", "T25": "pcs", "Y25": "pcs", "R25": "pcs",
            "D32": "pcs", "T32": "pcs", "Y32": "pcs", "R32": "pcs",
            "REINFORCEMENT STEEL": "pcs",
            "CEMENT 32.5N": "bags",
            "CEMENT 42.5N": "bags",
            "CEMENT": "bags",
            "HARDCORE": "tippers",
            "MARINE BOARDS": "pcs",
            "RIVER SAND": "tons",
            "SAND": "tons"
        }

        for w in weekly_reports:
            if not isinstance(w, dict): continue
            for item in w.get("materials_delivered", []):
                if not isinstance(item, dict): continue
                # Try multiple case variations for description/quantity/unit
                name = (item.get("description") or item.get("Description") or "Unknown").upper().strip()
                qty_val = item.get("quantity") or item.get("Quantity") or "0"
                if qty_val is None: qty_val = "0"
                qty_str = str(qty_val).replace(",", "").strip()
                
                match = re.search(r"(\d+\.?\d*)", qty_str)
                if match:
                    try:
                        qty = float(match.group(1))
                        # Check multiple unit keys
                        unit = item.get("unit") or item.get("units") or item.get("Unit") or item.get("Units") or ""
                        
                        # If no unit field, check if it was in the quantity string
                        if not unit and " " in qty_str:
                            unit = qty_str.split(" ", 1)[1]
                        
                        # Fallback to defaults if still empty (Ultra-robust matching)
                        if not unit:
                            clean_name = self._normalize_string(name)
                            for base_name, d_unit in default_units.items():
                                if self._normalize_string(base_name) in clean_name:
                                    unit = d_unit
                                    break
                            
                        if name not in materials_sum:
                            materials_sum[name] = {"qty": 0.0, "unit": unit}
                        materials_sum[name]["qty"] += qty
                    except: pass

        # Machinery
        machinery_list = []
        all_machine_names = set()
        for w in weekly_reports:
            if not isinstance(w, dict): continue
            for m in w.get("machinery", []):
                if not isinstance(m, dict): continue
                all_machine_names.add(m.get("name", "").upper())
        
        for name in all_machine_names:
            status = "Working"
            condition = "Good"
            qty = "0"
            for w in reversed(weekly_reports):
                match = next((m for m in w.get("machinery", []) if m.get("name", "").upper() == name), None)
                if match:
                    status = match.get("status", status)
                    condition = match.get("condition", condition)
                    qty = match.get("qty", qty)
                    break
            machinery_list.append({"name": name, "qty": qty, "condition": condition, "status": status})

        # Instructions
        all_instructions = []
        seen_inst = set()
        for w in weekly_reports:
            if not isinstance(w, dict): continue
            for inst in w.get("instructions", []):
                if not isinstance(inst, dict): continue
                key = (inst.get("REF. NO"), inst.get("date"))
                if key not in seen_inst:
                    seen_inst.add(key)
                    all_instructions.append(inst)

        # Health & Safety / Security / Challenges
        def aggregate_prose(field_name):
            combined = []
            for w in weekly_reports:
                prose = w.get(field_name, "").strip()
                if prose and prose.lower() != "none":
                    combined.append(prose)
            unique = list(dict.fromkeys(combined))
            if not unique: return "None"
            return "\n".join([f"• {p}" for p in unique])

        def compile_incident_summary(prose_list, issues_list):
            summary_parts = []
            totals = {}
            for issues in issues_list:
                if isinstance(issues, dict):
                    for cat, count in issues.items():
                        totals[cat] = totals.get(cat, 0) + count
            
            if totals:
                parts = [f"{count} {cat}" for cat, count in totals.items()]
                summary_parts.append("Total incidents recorded: " + ", ".join(parts) + ".")
            
            for p in prose_list:
                if p and p.lower() != "none":
                    summary_parts.append(f"• {p}")
            
            return "\n".join(summary_parts) if summary_parts else "None"

        hs_prose = [w.get("health_safety_prose", "") for w in weekly_reports]
        hs_issues = [w.get("health_safety_issues", {}) for w in weekly_reports]
        sec_prose = [w.get("security_prose", "") for w in weekly_reports]
        sec_issues = [w.get("security_issues", {}) for w in weekly_reports]

        visitors_list = []
        for w in weekly_reports:
            prose = w.get("visitors_prose", "").strip()
            if prose:
                visitors_list.append(prose)

        result = {
            "title": title,
            "reporting_period": metadata.get("report_date", ""),
            "time_elapsed": metadata.get("time_elapsed", ""),
            "pct_period": metadata.get("pct_period", ""),
            "pct_work": metadata.get("pct_work", ""),
            "weekly_periods": weekly_periods,
            "weekly_valid_days": [w["valid_days"] for w in expected_weeks],
            "weekly_labour": weekly_labour_matrices,
            "weekly_weather": weekly_weather_grids,
            "weekly_materials": weekly_materials_list,
            "weather_comments": weather_comments,
            "summary_to_date": latest_week.get("summary_to_date", {}),
            "materials_sum": materials_sum,
            "machinery": machinery_list,
            "instructions": all_instructions,
            "health_safety": compile_incident_summary(hs_prose, hs_issues),
            "security": compile_incident_summary(sec_prose, sec_issues),
            "challenges": aggregate_prose("challenges_prose"),
            "visitors_prose": visitors_list
        }
        
        self._save_to_history(result)
        return result
