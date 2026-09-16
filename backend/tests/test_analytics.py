import sys
import os
import json
sys.path.append(os.path.abspath('backend'))
from analytics import AnalyticsEngine

e = AnalyticsEngine()
v = {"Day": "77", "Night": "48"}
print(f"Testing dict: {e._clean_val(v)}")
v2 = "Day: 77, Night: 48"
print(f"Testing string: {e._clean_val(v2)}")
