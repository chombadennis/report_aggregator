import sys
import os
import asyncio
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aggregator import Aggregator
from analytics import AnalyticsEngine


def _report(date, day, labour):
    return {"date": date, "day_of_week": day, "labour": labour, "weather": {},
            "materials_delivered": [], "report_date": "19TH - 25TH OCTOBER 2026"}


def _compile(reports):
    return asyncio.run(Aggregator(history_dir=os.path.join(os.path.dirname(__file__), "tests_output")).compile_weekly_data(reports))


def _tot(v):
    return AnalyticsEngine()._clean_val(v)


class TestMislabeledHeaders(unittest.TestCase):
    def test_tuesday_headed_as_monday(self):
        mon = _report("19th October 2026", "Monday", {"Mason": {"Mon- day": "5(m)", "Mon- night": "2(m)"}})
        tue = _report("20th October 2026", "Tuesday", {"Mason": {"Mon- day": "7(m)", "Mon- night": "3(m)"}})
        out = _compile([mon, tue])["labour_daily"]
        self.assertEqual(_tot(out["2026-10-19"]["Mason"]), 7)
        self.assertEqual(_tot(out["2026-10-20"]["Mason"]), 10)

    def test_wednesday_day_plus_mon_night(self):
        wed = _report("21st October 2026", "Wednesday", {"Mason": {"Day": "4(m)", "Mon- Night": "6(m)"}})
        out = _compile([wed])["labour_daily"]
        self.assertEqual(_tot(out["2026-10-21"]["Mason"]), 10)

    def test_monday_day_only_tuesday_has_monday_night(self):
        mon = _report("19th October 2026", "Monday", {"Mason": "5(m)"})
        tue = _report("20th October 2026", "Tuesday", {"Mason": {"Mon- Night": "2(m)", "Tue- Day": "7(m)"}})
        out = _compile([mon, tue])["labour_daily"]
        self.assertEqual(_tot(out["2026-10-19"]["Mason"]), 7)   # 5 day + 2 late night
        self.assertEqual(_tot(out["2026-10-20"]["Mason"]), 7)

    def test_three_columns_mon_night_tue_day_tue_night(self):
        mon = _report("19th October 2026", "Monday", {"Mason": "5(m)"})
        tue = _report("20th October 2026", "Tuesday",
                      {"Mason": {"Mon- Night": "2(m)", "Tue- Day": "7(m)", "Tue- Night": "4(m)"}})
        out = _compile([mon, tue])["labour_daily"]
        self.assertEqual(_tot(out["2026-10-19"]["Mason"]), 7)
        self.assertEqual(_tot(out["2026-10-20"]["Mason"]), 11)

    def test_trends_attribution(self):
        eng = AnalyticsEngine()
        from datetime import datetime
        parse = lambda s: datetime.strptime(s, "%Y-%m-%d")
        entries = [
            _report("2026-10-19", "Monday", {"Mason": "5(m)"}),
            _report("2026-10-20", "Tuesday",
                    {"Mason": {"Mon- Night": "2(m)", "Tue- Day": "7(m)", "Tue- Night": "4(m)"}}),
            _report("2026-10-21", "Wednesday", {"Mason": {"Day": "4(m)", "Mon- Night": "6(m)"}}),
            _report("2026-10-22", "Thursday", {"Mason": {"Mon- day": "1(m)", "Mon- night": "1(m)"}}),
        ]
        t = eng._attribute_daily_labour(entries, parse)
        self.assertEqual(t["2026-10-19"], 7)
        self.assertEqual(t["2026-10-20"], 11)
        self.assertEqual(t["2026-10-21"], 10)
        self.assertEqual(t["2026-10-22"], 2)


if __name__ == '__main__':
    unittest.main()
