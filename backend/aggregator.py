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
        """Takes 7 daily reports and builds a Weekly summary."""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # 1. Labour Matrix
        all_categories = set()
        for r in daily_reports: 
            if "labour" in r: all_categories.update(r["labour"].keys())
        
        labour_matrix = {}
        for cat in sorted(all_categories):
            counts = []
            for r in daily_reports:
                counts.append(r.get("labour", {}).get(cat, "0"))
            labour_matrix[cat] = counts

        # 2. Weather Grid
        weather_grid = []
        for i, r in enumerate(daily_reports):
            w = r.get("weather", {})
            weather_grid.append({
                "day": days[i] if i < len(days) else f"Day {i+1}",
                "morning": w.get("morning", "Sunny"),
                "afternoon": w.get("afternoon", "Sunny")
            })

        # 3. Building Works
        compiled_blocks = {}
        for r in daily_reports:
            for block, tasks in r.get("building_works", {}).items():
                if block not in compiled_blocks: compiled_blocks[block] = []
                compiled_blocks[block].extend(tasks)
        for block in compiled_blocks:
            compiled_blocks[block] = list(dict.fromkeys(compiled_blocks[block]))

        result = {
            "labour": labour_matrix,
            "weather": weather_grid,
            "building_works": compiled_blocks,
            "general_works": list(dict.fromkeys([t for r in daily_reports for t in r.get("general_works", [])])),
            "material_tests": [test for r in daily_reports for test in r.get("material_tests", [])],
            "instructions": [inst for r in daily_reports for inst in r.get("instructions", [])],
            "security": daily_reports[-1].get("security", "Secure"),
            "health_safety": daily_reports[-1].get("health_safety", "No accidents")
        }

        # 4. Persistence: Save to history folder
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
