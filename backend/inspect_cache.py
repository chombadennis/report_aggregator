import os
import json

cache_dir = "cache"
if os.path.exists(cache_dir):
    for f in os.listdir(cache_dir):
        if f.endswith(".json"):
            path = os.path.join(cache_dir, f)
            with open(path, "r") as jf:
                try:
                    data = json.load(jf)
                    print(f"File: {f}")
                    print(f"  Keys: {list(data.keys())}")
                    if "date" in data:
                        print(f"  Date: {data['date']}")
                    if "reporting_period" in data:
                        print(f"  Period: {data['reporting_period']}")
                except:
                    print(f"File: {f} (Error reading)")
