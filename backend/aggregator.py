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
            cleaned = cleaned.replace(",", " ").strip()
            for fmt in ["%A %d %B %Y", "%d %B %Y", "%A, %d %B %Y", "%Y-%m-%d"]:
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
            """Case-insensitive fuzzy match against parsed keys. Returns dict, string, or 0."""
            key_lower = canonical_name.lower().replace(" ", "").replace("&", "and")
            if key_lower == "intern":
                key_lower_alt = "interns"
            else:
                key_lower_alt = key_lower
            for k, v in labour_dict.items():
                k_norm = k.lower().replace(" ", "").replace("&", "and")
                if k_norm == key_lower or k_norm == key_lower_alt:
                    return v
            return "0"

        def _extract_numeric(val):
            """Pulls first integer from strings like '4(m)', '13(12m,1f)', '0'."""
            import re
            m = re.match(r"(\d+)", str(val).strip())
            return int(m.group(1)) if m else 0

        # Build day-by-day values
        def _get_shift_target(key, default_day_idx):
            key_upper = str(key).upper()
            target_day_idx = default_day_idx
            
            day_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
            for idx, d_name in enumerate(day_names):
                if d_name in key_upper:
                    target_day_idx = idx
                    break
            
            shift_type = "DAY"
            if "NIGHT" in key_upper or "NITE" in key_upper:
                shift_type = "NIGHT"
            return target_day_idx, shift_type

        # 1. Gather all categories present in the reports
        all_categories = list(LABOUR_CANONICAL_ORDER)
        EXCLUDED_KEYS = {"total", "sub-total", "subtotal", "grand total"}
        
        # Check for extra categories
        canonical_lower = {c.lower().replace(" ", "").replace("&", "and") for c in LABOUR_CANONICAL_ORDER}
        if "intern" in canonical_lower:
            canonical_lower.add("interns")
            
        for r in reports_by_day:
            if not r: continue
            for k in r.get("labour", {}).keys():
                if k.strip().lower() in EXCLUDED_KEYS:
                    continue
                k_norm = k.lower().replace(" ", "").replace("&", "and")
                if not any(k_norm == c for c in canonical_lower):
                    found = False
                    for existing in all_categories:
                        if existing.lower().replace(" ", "").replace("&", "and") == k_norm:
                            found = True
                            break
                    if not found:
                        all_categories.append(k)

        # 2. Populate temporary matrix with default "0" values
        temp_matrix = {cat: [{"Day": "0", "Night": "0"} for _ in range(7)] for cat in all_categories}

        # 3. Fill the temporary matrix from daily reports
        for day_idx in range(7):
            r = reports_by_day[day_idx]
            if not r: continue
            
            for cat in all_categories:
                val = _find_labour_value(r.get("labour", {}), cat)
                if val == "0" or not val:
                    continue
                    
                is_dict = isinstance(val, dict)
                if not is_dict and isinstance(val, str) and val.strip().startswith("{") and val.strip().endswith("}"):
                    try:
                        import ast
                        val = ast.literal_eval(val)
                        is_dict = isinstance(val, dict)
                    except:
                        pass
                        
                if is_dict:
                    is_single_value = len(val) == 1
                    for k, v in val.items():
                        target_day_idx, shift_type = _get_shift_target(k, day_idx)
                        if is_single_value:
                            target_day_idx = day_idx
                        if shift_type == "NIGHT":
                            temp_matrix[cat][target_day_idx]["Night"] = str(v).strip()
                        else:
                            temp_matrix[cat][target_day_idx]["Day"] = str(v).strip()
                else:
                    temp_matrix[cat][day_idx]["Day"] = str(val).strip()

        # 4. Convert temporary matrix to final format (collapsing Night="0" into a simple string)
        labour_matrix = {}
        for cat in all_categories:
            day_values = []
            for day_idx in range(7):
                d_val = temp_matrix[cat][day_idx]["Day"]
                n_val = temp_matrix[cat][day_idx]["Night"]
                if n_val in ("0", "", "-"):
                    day_values.append(d_val if d_val else "0")
                else:
                    day_values.append({"Day": d_val if d_val else "0", "Night": n_val})
            labour_matrix[cat] = day_values

        # 5. Compile TOTAL row: Use verbatim from daily reports mapped to days, otherwise sum
        temp_total = [{"Day": "0", "Night": "0"} for _ in range(7)]
        
        for day_idx in range(7):
            r = reports_by_day[day_idx]
            verbatim_total = r.get("labour", {}).get("TOTAL") if r else None
            if verbatim_total and str(verbatim_total).strip() != "0":
                is_dict = isinstance(verbatim_total, dict)
                if not is_dict and isinstance(verbatim_total, str) and verbatim_total.strip().startswith("{") and verbatim_total.strip().endswith("}"):
                    try:
                        import ast
                        verbatim_total = ast.literal_eval(verbatim_total)
                        is_dict = isinstance(verbatim_total, dict)
                    except:
                        pass
                
                if is_dict:
                    for k, v in verbatim_total.items():
                        target_day_idx, shift_type = _get_shift_target(k, day_idx)
                        if shift_type == "NIGHT":
                            temp_total[target_day_idx]["Night"] = str(v).strip()
                        else:
                            temp_total[target_day_idx]["Day"] = str(v).strip()
                else:
                    temp_total[day_idx]["Day"] = str(verbatim_total).strip()

        # Fallback for days missing verbatim totals: sum of category counts
        all_cats_for_total = [cat for cat in labour_matrix.keys() if cat != "TOTAL"]
        for day_idx in range(7):
            if temp_total[day_idx]["Day"] == "0" and temp_total[day_idx]["Night"] == "0":
                sum_day = 0
                sum_night = 0
                for cat in all_cats_for_total:
                    sum_day += _extract_numeric(temp_matrix[cat][day_idx]["Day"])
                    sum_night += _extract_numeric(temp_matrix[cat][day_idx]["Night"])
                temp_total[day_idx]["Day"] = str(sum_day)
                temp_total[day_idx]["Night"] = str(sum_night)

        # Convert temp_total to final format
        total_per_day = []
        for day_idx in range(7):
            d_val = temp_total[day_idx]["Day"]
            n_val = temp_total[day_idx]["Night"]
            if n_val in ("0", "", "-"):
                total_per_day.append(d_val if d_val else "0")
            else:
                total_per_day.append({"Day": d_val if d_val else "0", "Night": n_val})
        labour_matrix["TOTAL"] = total_per_day

        # Build labour_daily mapping for analytics/history database format
        labour_daily = {}
        for day_idx, r in enumerate(reports_by_day):
            if not r: continue
            date_str = r.get("date")
            parsed_dt = _parse_report_date(r)
            norm_date = parsed_dt.strftime("%Y-%m-%d") if parsed_dt else date_str
            if norm_date:
                cat_map = {}
                for cat in labour_matrix.keys():
                    cat_map[cat] = labour_matrix[cat][day_idx]
                labour_daily[norm_date] = cat_map

        # 2. Weather Grid
        import re
        def _clean_weather(val):
            val = str(val or "-").strip()
            if val == "-": return "-"
            val = re.split(r'[-–—]?\s*favour', val, flags=re.IGNORECASE)[0]
            val = re.split(r'[-–—]?\s*favor', val, flags=re.IGNORECASE)[0]
            parts = val.split('-')
            if len(parts) > 1 and len(parts[1].strip()) > 5:
                val = parts[0]
            return val.strip(' -') or "-"

        weather_grid = []
        for i, r in enumerate(reports_by_day):
            w = r.get("weather", {}) if r else {}
            weather_grid.append({
                "day": days_map[i].capitalize(),
                "morning": _clean_weather(w.get("morning", "-")),
                "afternoon": _clean_weather(w.get("afternoon", "-")),
                "evening": _clean_weather(w.get("evening", "-")),
                "condition": "Favourable for Work"
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

        # 6. Works by Day — per-day, per-component (strictly from building_works only)
        # Structure: {"Monday": {"Component A": "• task1\n• task2", ...}, "Tuesday": {...}, ...}
        FULL_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        def _tasks_to_bullets(tasks):
            """Convert a list of task strings to a '• item\n• item' bullet string."""
            if not tasks:
                return "• None"
            seen = set()
            bullets = []
            for t in tasks:
                t = str(t).strip()
                if t and t.lower() not in seen:
                    seen.add(t.lower())
                    bullets.append(f"• {t}" if not t.startswith("•") else t)
            return "\n".join(bullets) if bullets else "• None"

        works_by_day_summary = {}
        for day_idx, r in enumerate(reports_by_day):
            day_name = FULL_DAY_NAMES[day_idx]
            if not r:
                continue
            # ONLY use building_works — never touch summary_of_works here
            day_building_works = r.get("building_works", {})
            if not day_building_works:
                continue
            day_entry = {}
            for component, tasks in day_building_works.items():
                # tasks can be a list or already a bullet string from the parser
                if isinstance(tasks, list):
                    bullet_str = _tasks_to_bullets(tasks)
                elif isinstance(tasks, str):
                    # Already formatted as bullets — keep as-is
                    bullet_str = tasks.strip() if tasks.strip() else "• None"
                else:
                    bullet_str = "• None"
                day_entry[component] = bullet_str
            if day_entry:
                works_by_day_summary[day_name] = day_entry

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
            "labour_daily": labour_daily,
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
        # self._save_to_history(result, "WEEKLY")
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
