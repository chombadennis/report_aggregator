import json
import os
import hashlib

class Aggregator:
    def __init__(self, history_dir="history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)

    def check_duplicate(self, title):
        """Checks if a report with this exact title already exists in history."""
        if not title: return False
        for filename in os.listdir(self.history_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.history_dir, filename), "r") as f:
                    try:
                        history_data = json.load(f)
                        if history_data.get("title", "").upper() == title.upper():
                            return True
                    except: continue
        return False

    def _save_to_history(self, data, report_type):
        """Saves the final compiled JSON to history with a content-based unique ID."""
        # Create a unique ID based on the combined data content
        content_str = json.dumps(data, sort_keys=True)
        unique_id = hashlib.sha256(content_str.encode()).hexdigest()[:12]
        
        filename = f"{report_type.lower()}_{unique_id}.json"
        history_path = os.path.join(self.history_dir, filename)
        
        with open(history_path, "w") as f:
            json.dump(data, f, indent=2)
        return history_path

    async def compile_weekly_data(self, daily_reports):
        """Builds a high-fidelity Weekly summary from daily reports."""
        import re
        from datetime import datetime, timedelta
        days_map = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

        # 0. Chronological Sorting by Detected Day
        reports_by_day = [None] * 7
        for r in daily_reports:
            date_str = r.get("date", "").upper()
            day_field = r.get("day_of_week", "").upper()
            for idx, day_name in enumerate(days_map):
                if day_name in date_str or day_name in day_field:
                    reports_by_day[idx] = r
                    break

        # 0b. Date Continuity Validation
        # Parse calendar dates from reports and verify they form a consecutive sequence.
        def _parse_report_date(r):
            """Extracts a date object from report date string, e.g. '16th April 2026'."""
            if not r: return None
            raw = r.get("date", "")
            # Strip ordinal suffixes: 16th -> 16, 1st -> 1, etc.
            cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", raw, flags=re.IGNORECASE)
            for fmt in ["%A %d %B %Y", "%d %B %Y", "%A, %d %B %Y"]:
                try: return datetime.strptime(cleaned.strip(), fmt).date()
                except: continue
            return None

        present_reports = [(idx, r) for idx, r in enumerate(reports_by_day) if r is not None]
        if len(present_reports) > 1:
            prev_idx, prev_r = present_reports[0]
            prev_date = _parse_report_date(prev_r)
            for curr_idx, curr_r in present_reports[1:]:
                curr_date = _parse_report_date(curr_r)
                if prev_date and curr_date:
                    expected_date = prev_date + timedelta(days=(curr_idx - prev_idx))
                    if curr_date != expected_date:
                        day_name = days_map[curr_idx].capitalize()
                        raise ValueError(
                            f"❌ DATE CONTINUITY ERROR: The {day_name} report shows date "
                            f"'{curr_r.get('date', 'unknown')}' but based on the previous report "
                            f"it should be '{expected_date.strftime('%A %d %B %Y')}'. "
                            f"Please ensure all 7 daily reports are in order with correct dates before re-uploading."
                        )
                prev_idx, prev_r, prev_date = curr_idx, curr_r, curr_date

        # 1. Labour Matrix — Canonical order, always present, Total always last
        # These categories MUST appear in this EXACT order, even if all values are 0.
        LABOUR_CANONICAL_ORDER = [
            "Site Agent/PM",
            "Ass. Site Agent",
            "Office Attendant",
            "Office Assistant",
            "Foreman",
            "Operator",
            "Mason",
            "Electrician",
            "Painters",
            "Carpenters",
            "Steel fixers",
            "Drivers",
            "Surveyors",
            "Intern",
            "Unskilled",
            "Safety officer",
            "Store keeper",
            "Security (day&night)",
        ]

        def _find_labour_value(labour_dict, canonical_name):
            """Case-insensitive fuzzy match against parsed keys. Always returns a string, never empty."""
            key_lower = canonical_name.lower().replace(" ", "").replace("&", "and")
            for k, v in labour_dict.items():
                k_norm = k.lower().replace(" ", "").replace("&", "and")
                if k_norm == key_lower or k_norm.startswith(key_lower[:6]):
                    # Normalise: empty string or None → "0"
                    return str(v).strip() if str(v).strip() else "0"
            return "0"

        def _extract_numeric(val):
            """Pulls first integer from strings like '4(m)', '13(12m,1f)', '0'."""
            import re
            m = re.match(r"(\d+)", str(val).strip())
            return int(m.group(1)) if m else 0

        labour_matrix = {}
        for cat in LABOUR_CANONICAL_ORDER:
            day_values = []
            for r in reports_by_day:
                val = _find_labour_value(r.get("labour", {}), cat) if r else "0"
                day_values.append(val)
            labour_matrix[cat] = day_values

        # Dynamic expansion: detect any extra categories in the PDFs not in the canonical list.
        # Explicitly skip "TOTAL" and similar aggregate rows — these are computed, not categories.
        EXCLUDED_KEYS = {"total", "sub-total", "subtotal", "grand total"}
        canonical_lower = {c.lower().replace(" ", "").replace("&", "and") for c in LABOUR_CANONICAL_ORDER}
        extra_categories = []
        for r in reports_by_day:
            if not r: continue
            for k in r.get("labour", {}).keys():
                if k.strip().lower() in EXCLUDED_KEYS:
                    continue  # Skip aggregate rows — never treat TOTAL as a category
                k_norm = k.lower().replace(" ", "").replace("&", "and")
                # Only add if it doesn't match any canonical category
                if not any(k_norm == c or k_norm.startswith(c[:6]) for c in canonical_lower):
                    if k not in extra_categories:
                        extra_categories.append(k)

        for cat in extra_categories:
            day_values = []
            for r in reports_by_day:
                val = _find_labour_value(r.get("labour", {}), cat) if r else "0"
                day_values.append(val)
            labour_matrix[cat] = day_values

        # TOTAL row: sum of ALL categories (canonical + extras) per day — ALWAYS LAST
        all_cats_for_total = LABOUR_CANONICAL_ORDER + extra_categories
        total_per_day = []
        for day_idx in range(7):
            day_total = sum(
                _extract_numeric(labour_matrix[cat][day_idx])
                for cat in all_cats_for_total
            )
            total_per_day.append(str(day_total) if day_total > 0 else "0")
        labour_matrix["TOTAL"] = total_per_day

        # 2. Weather Grid
        weather_grid = []
        for i, r in enumerate(reports_by_day):
            w = r.get("weather", {}) if r else {}
            weather_grid.append({
                "day": days_map[i].capitalize(),
                "morning": w.get("morning", "-"),
                "afternoon": w.get("afternoon", "-"),
                "evening": w.get("evening", "-"),
                "condition": w.get("condition", "-")
            })

        # 3. Materials Summation — robust unit extraction with fallback from quantity string
        materials_summary = {}
        for r in reports_by_day:
            if not r: continue
            for item in r.get("materials_delivered", []):
                name = item.get("description", item.get("Description", "Unknown")).strip().upper()
                raw_qty = str(item.get("quantity", item.get("Quantity", "0")) or "0").strip()
                unit = str(item.get("units", item.get("Units", "")) or "").strip()
                try:
                    qty_parts = raw_qty.split()
                    qty = float(qty_parts[0].replace(",", ""))
                    # Fallback: pull unit from quantity string if parser left unit field empty
                    if not unit and len(qty_parts) > 1:
                        unit = qty_parts[1]
                    if name not in materials_summary:
                        materials_summary[name] = {"qty": 0.0, "unit": unit}
                    materials_summary[name]["qty"] += qty
                    # Keep the first non-empty unit seen for this material across all days
                    if not materials_summary[name]["unit"] and unit:
                        materials_summary[name]["unit"] = unit
                except: continue

        # 4. Machinery Status
        machinery_final = {}
        for r in reports_by_day:
            if not r: continue
            for m in r.get("machinery", []):
                name = m.name.upper() if hasattr(m, "name") else m.get("name", "").upper()
                qty = m.qty if hasattr(m, "qty") else m.get("qty", "0")
                status = m.status if hasattr(m, "status") else m.get("status", "Idle")
                if name not in machinery_final:
                    machinery_final[name] = {"qty": qty, "status": "Idle"}
                if status.upper() == "WORKING":
                    machinery_final[name]["status"] = "Working"

        # 5. Instructions
        compiled_instructions = []
        for r in reports_by_day:
            if r: compiled_instructions.extend(r.get("instructions", []))

        # 6. Works by Day (AI Professional Semantic Summary)
        raw_weekly_blocks = {}
        for r in reports_by_day:
            if not r: continue
            for block, tasks in r.get("building_works", {}).items():
                if block not in raw_weekly_blocks:
                    raw_weekly_blocks[block] = []
                raw_weekly_blocks[block].extend(tasks)

        works_by_day_summary = {}
        if raw_weekly_blocks:
            prompt = f"""
            Act as a highly experienced construction engineer. I am providing you with a list of tasks accomplished across a 7-day week for various building components on my site.
            
            Your job is to provide a professional-level summary of the work done during the week for EACH component.
            - Consolidate identical or semantically similar tasks so you DO NOT repeat yourself.
            - MUST write the summary as a bulleted list where each bullet point starts with the black dot character '• '.
            - If no activities were reported for a component, just output a single bullet: '• None'
            - Do NOT include dates or days of the week in the summary.
            
            Return the output as a perfect JSON object where the keys are the block names and the values are the professional summary string (with newlines separating bullets).
            Example: {{"BLOCK B4": "• Steel fixing to the raft foundation.\\n• Installation of starter columns.", "SWIMMING POOL": "• None"}}
            
            Raw Data:
            {json.dumps(raw_weekly_blocks)}
            """
            from ai_client import generate_summary_json
            try:
                works_by_day_summary = await generate_summary_json(prompt)
            except Exception as e:
                works_by_day_summary = {"Error": f"Could not generate AI summary: {e}"}

        # Calculate total visitors 
        total_visitors = 0
        for i, r in enumerate(reports_by_day):
            if not r: continue
            for v in r.get("visitors", []):
                v_str = str(v).strip()
                if not v_str: continue
                import re
                match = re.search(r'\d+', v_str)
                if match:
                    total_visitors += int(match.group())
                else:
                    total_visitors += 1
                    
        # Intelligent Security & Health and Safety Aggregation
        raw_security = [r.get("security_status", "") for r in reports_by_day if r and r.get("security_status")]
        security_issues = [s for s in raw_security if "secure" not in s.lower() and "no" not in s.lower()]
        if not security_issues:
            final_security = "The site was secure throughout the week."
        else:
            final_security = f"There were {len(security_issues)} security issues reported during the week: " + "; ".join(security_issues)

        raw_hs = [r.get("health_safety_status", "") for r in reports_by_day if r and r.get("health_safety_status")]
        hs_issues = [h for h in raw_hs if "no accident" not in h.lower() and "no incident" not in h.lower() and h.strip()]
        if not hs_issues:
            final_hs = "No accidents or incidents reported during the week."
        else:
            final_hs = f"There were {len(hs_issues)} health and safety incidents reported during the week: " + "; ".join(hs_issues)

        # Intelligent Challenges Deduplication
        raw_challenges = [c.strip() for r in reports_by_day if r for c in r.get("challenges", []) if c and str(c).strip()]
        seen = set()
        unique_challenges = []
        for c in raw_challenges:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                unique_challenges.append(c)

        if not unique_challenges:
            final_challenges = "None"
        elif len(unique_challenges) == 1:
            final_challenges = unique_challenges[0]
        else:
            final_challenges = "\n".join(f"• {c}" for c in unique_challenges)

        result = {
            "labour": labour_matrix,
            "weather": weather_grid,
            "works_by_day": works_by_day_summary,
            "materials_sum": materials_summary,
            "machinery": machinery_final,
            "instructions": compiled_instructions,
            "interns": [r.get("interns", {}) if r else {} for r in reports_by_day],
            "security": final_security,
            "health_safety": final_hs,
            "total_visitors_count": total_visitors,
            "challenges": final_challenges,
            "summary_to_date": next((r.get("summary_of_works", {}) for r in reversed(reports_by_day) if r), {}),
            "report_date": daily_reports[0].get("report_date", "6th – 12th April 2026")
        }
        self._save_to_history(result, "WEEKLY")
        return result

    def compile_monthly_data(self, weekly_results):
        """Takes 4 weekly report data objects and builds a Monthly summary."""
        monthly_blocks = {}
        for w in weekly_results:
            for block, tasks in w.get("building_works", {}).items():
                if block not in monthly_blocks: monthly_blocks[block] = []
                monthly_blocks[block].extend(tasks)
        for block in monthly_blocks:
            monthly_blocks[block] = list(dict.fromkeys(monthly_blocks[block]))

        result = {
            "weeks": weekly_results,
            "building_works": monthly_blocks,
            "general_works": list(dict.fromkeys([t for w in weekly_results for t in w.get("general_works", [])])),
            "material_tests": [test for w in weekly_results for test in w.get("material_tests", [])],
            "instructions": [inst for w in weekly_results for inst in w.get("instructions", [])]
        }

        # Save to history folder
        self._save_to_history(result, "MONTHLY")
        return result
