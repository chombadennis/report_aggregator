import json
import os
import random
from datetime import datetime, timedelta

def generate_mock_history(output_dir="test_history"):
    os.makedirs(output_dir, exist_ok=True)
    
    start_date = datetime(2026, 3, 2) # A Monday
    
    base_labour = 40
    base_materials = 5
    
    weeks = 12
    for w in range(weeks):
        current_monday = start_date + timedelta(weeks=w)
        current_sunday = current_monday + timedelta(days=6)
        
        period_str = f"{current_monday.strftime('%d').lstrip('0')}th – {current_sunday.strftime('%d').lstrip('0')}th {current_monday.strftime('%B %Y')}"
        
        # Trends: 
        # Labour ramps up then plateaus
        if w < 6:
            labour_val = base_labour + (w * 15) + random.randint(-5, 5)
        else:
            labour_val = 120 + random.randint(-10, 10)
            
        # Materials spike during mid-phase
        mat_count = base_materials + (w * 2 if w < 6 else (12-w) * 2) + random.randint(0, 3)
        
        # Weather: More rain in April (w=4-8)
        is_rainy_season = 4 <= w <= 8
        rainy_days = random.randint(2, 5) if is_rainy_season else random.randint(0, 1)
        
        # Create JSON structure matching WeeklyReportSchema
        data = {
            "report_date": period_str,
            "labour": {
                "TOTAL": [str(labour_val + random.randint(-10, 10)) for _ in range(7)]
            },
            "weather": [],
            "materials_sum": {f"MAT_{i}": {"qty": random.randint(10, 100), "unit": "pcs"} for i in range(mat_count)},
            "challenges": "",
            "security": ""
        }
        
        # Fill weather
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            is_rainy = i < rainy_days
            data["weather"].append({
                "day": day,
                "morning": "Rainy" if is_rainy else "Sunny",
                "afternoon": "Rainy" if is_rainy and random.random() > 0.5 else "Cloudy",
                "evening": "Rainy" if is_rainy else "Clear",
                "condition": "Disrupted" if is_rainy else "Favorable"
            })
            
        # Inject challenges for specific weeks
        if w == 5:
            data["challenges"] = "Material delivery delayed due to logistics issues."
        if w == 10:
            data["challenges"] = "Work behind schedule due to labour shortage."
            
        filename = f"weekly_mock_w{w:02d}.json"
        with open(os.path.join(output_dir, filename), "w") as f:
            json.dump(data, f, indent=2)
            
    print(f"✅ Generated {weeks} weeks of mock data in '{output_dir}'")

if __name__ == "__main__":
    generate_mock_history()
