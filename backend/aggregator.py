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

    def compile_weekly_data(self, daily_reports):
        """Builds a high-fidelity Weekly summary from daily reports."""
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

        # 1. Adaptive Labour Matrix
        all_categories = set()
        for r in reports_by_day: 
            if r and "labour" in r: all_categories.update(r["labour"].keys())
        
        labour_matrix = {}
        for cat in sorted(all_categories):
            day_values = []
            for r in reports_by_day:
                val = r.get("labour", {}).get(cat, "0") if r else "0"
                day_values.append(val)
            labour_matrix[cat] = day_values

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

        # 3. Materials Summation
        materials_summary = {}
        for r in reports_by_day:
            if not r: continue
            for item in r.get("materials_delivered", []):
                name = item.get("description", "Unknown").strip().upper()
                raw_qty = item.get("quantity", "0")
                unit = item.get("units", "")
                try:
                    qty = float(str(raw_qty).split()[0])
                    if name not in materials_summary:
                        materials_summary[name] = {"qty": 0.0, "unit": unit}
                    materials_summary[name]["qty"] += qty
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

        # 6. Building Works
        works_by_day = []
        for r in reports_by_day:
            day_text = []
            if r:
                for block, tasks in r.get("building_works", {}).items():
                    day_text.append(f"{block}: {', '.join(tasks)}")
                day_text.extend(r.get("general_works", []))
            works_by_day.append("\n".join(day_text))

        result = {
            "labour": labour_matrix,
            "weather": weather_grid,
            "works_by_day": works_by_day,
            "materials_sum": materials_summary,
            "machinery": machinery_final,
            "instructions": compiled_instructions,
            "interns": [r.get("interns", {}) if r else {} for r in reports_by_day],
            "security": [r.get("security_status", "") for r in reports_by_day if r and r.get("security_status")],
            "health_safety": [r.get("health_safety_status", "") for r in reports_by_day if r and r.get("health_safety_status")],
            "visitors": [v for r in reports_by_day if r for v in r.get("visitors", [])],
            "challenges": [c for r in reports_by_day if r for c in r.get("challenges", [])],
            "summary_to_date": reports_by_day[-1].get("summary_of_works", {}) if reports_by_day[-1] else {},
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
