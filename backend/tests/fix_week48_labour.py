import sys, os, json, glob, asyncio, shutil
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from aggregator import Aggregator
from analytics import AnalyticsEngine

backend = os.path.join(os.path.dirname(__file__), '..')
os.chdir(backend)
eng = AnalyticsEngine()
import re
def pdate(s):
    c = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s or "", flags=re.I).replace(",", " ")
    for f in ("%d %B %Y", "%Y-%m-%d"):
        try: return datetime.strptime(re.sub(r"\s+", " ", c).strip(), f)
        except: pass

dailies = []
for f in glob.glob("cache/DAILY_*.json"):
    d = json.load(open(f, encoding="utf-8"))
    dt = pdate(d.get("date"))
    if dt and datetime(2026, 10, 19) <= dt <= datetime(2026, 10, 25):
        dailies.append(d)
print("dailies found:", sorted(d["date"] for d in dailies))

path = "cache/history/weekly_5aca755cf47f.json"
old = json.load(open(path, encoding="utf-8"))
new = asyncio.run(Aggregator(history_dir="cache/history_tmp").compile_weekly_data(dailies))
shutil.rmtree("cache/history_tmp", ignore_errors=True)

def show(tag, ld):
    print(tag)
    for day, cats in sorted(ld.items()):
        print("  ", day, "TOTAL =", cats.get("TOTAL"), "| trend total =",
              sum(eng._clean_val(v) for k, v in cats.items() if k != "TOTAL"))
show("OLD", old["labour_daily"])
show("NEW", new["labour_daily"])

if "--apply" in sys.argv:
    shutil.copy(path, path + ".bak")
    old["labour_daily"] = new["labour_daily"]
    old["labour"] = new["labour"]
    json.dump(old, open(path, "w", encoding="utf-8"), indent=2)
    print("APPLIED (backup at", path + ".bak)")
