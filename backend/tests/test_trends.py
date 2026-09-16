import sys
sys.path.append('backend')
from backend.analytics import AnalyticsEngine
e = AnalyticsEngine()
trends = e.get_daily_trends()
for t in trends:
    if '09-10' in t['date'] or '09-09' in t['date']:
        print(t)
