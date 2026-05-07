import os
import sys
import json
import pandas as pd
import numpy as np

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics import AnalyticsEngine

def draw_bar(val, max_val, width=40):
    """Simple ASCII bar chart."""
    if max_val == 0: return ""
    bar_width = int((val / max_val) * width)
    return "#" * bar_width + "-" * (width - bar_width)

def run_visual_debug(history_dir="test_history", daily_mode=False):
    print(f"SEARCH DEBUGGING TRENDS FROM: {history_dir}\n")
    
    engine = AnalyticsEngine(history_dir=history_dir)
    trends = engine.get_historical_trends()
    
    if not trends["labour_trend"]:
        print("No data found to visualize.")
        return

    # Daily Trend Visualization
    if daily_mode:
        print("DAILY LABOUR FORCE TIMELINE")
        print("-" * 60)
        daily_trends = engine.get_daily_trends()
        df_daily = pd.DataFrame(daily_trends)
        if not df_daily.empty:
            max_labour_d = df_daily["labour"].max()
            for _, row in df_daily.iterrows():
                prefix = "[W] " if row["is_weekend"] else "    "
                weather_marker = "!" if row["weather_disrupted"] else " "
                bar = draw_bar(row["labour"], max_labour_d, width=30)
                print(f"{row['date']} {prefix}{weather_marker} | {bar} {row['labour']:>3}")
        
    print("\nWEEKLY PERFORMANCE SUMMARY")
    print("-" * 60)
    trends = engine.get_historical_trends()
    df_labour = pd.DataFrame(trends["labour_trend"])
    for _, row in df_labour.iterrows():
        bar = draw_bar(row["value"], df_labour["value"].max(), width=30)
        print(f"{row['label']:<25} | {bar} {row['value']:>5}")
        
    print("\nNote: [W] = Weekend, ! = Disrupted Weather")
    return

    # Convert to DataFrame for easier analysis
    df_labour = pd.DataFrame(trends["labour_trend"])
    df_mat = pd.DataFrame(trends["material_trends"])
    df_weather = pd.DataFrame(trends["weather_impact"])
    
    # Merge on label
    df = df_labour.merge(df_mat, on="label").merge(df_weather, on="label")
    
    max_labour = df["value_x"].max()
    max_mat = df["value_y"].max()
    
    print("LABOUR FORCE TREND (Weekly Avg)")
    print("-" * 60)
    for _, row in df.iterrows():
        bar = draw_bar(row["value_x"], max_labour)
        print(f"{row['label'][:15]:<15} | {bar} {row['value_x']:>5}")
        
    print("\nLOGISTICS INTENSITY (Unique Items)")
    print("-" * 60)
    for _, row in df.iterrows():
        bar = draw_bar(row["value_y"], max_mat, width=20)
        print(f"{row['label'][:15]:<15} | {bar} {row['value_y']:>3}")

    print("\nWEATHER DISRUPTIONS (Days with Rain)")
    print("-" * 60)
    for _, row in df.iterrows():
        rain_dots = "*" * int(row["rainy_days"])
        print(f"{row['label'][:15]:<15} | {rain_dots}")

    # Correlation Analysis
    print("\nCORRELATION ANALYSIS")
    print("-" * 60)
    # Correlation between Labour (value_x) and Materials (value_y)
    corr_labour_mat = df["value_x"].corr(df["value_y"])
    print(f"Labour vs. Materials Correlation: {corr_labour_mat:.2f}")
    
    if corr_labour_mat > 0.7:
        print("➡️  Status: Strong Positive Correlation. Site activity is well-synchronized.")
    elif corr_labour_mat < 0.3:
        print("➡️  Status: Weak Correlation. Potential mismatch between supply and personnel.")
        
    # Correlation between Rain and Labour
    corr_rain_labour = df["rainy_days"].corr(df["value_x"])
    print(f"Rainy Days vs. Labour Force:    {corr_rain_labour:.2f}")
    
    # Risk Summary
    print("\nDETECTED RISKS CHRONOLOGY")
    print("-" * 60)
    for risk in trends["risk_indicators"]:
        print(f"[{risk['date']}] {risk['severity']} - {risk['risk']}")

    # Save to CSV for external tools
    output_path = os.path.join("tests", "tests_output", "trend_debug_data.csv")
    df.to_csv(output_path, index=False)
    print(f"\nDetailed data exported to: {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, default="test_history", help="Directory containing JSON reports")
    parser.add_argument("--daily", action="store_true", help="Show daily granularity")
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print(f"Directory '{args.dir}' not found.")
    else:
        run_visual_debug(history_dir=args.dir, daily_mode=args.daily)
