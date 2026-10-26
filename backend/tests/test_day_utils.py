import sys
import os
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from day_utils import detect_weekday, detect_shift


class TestDayUtils(unittest.TestCase):
    def test_weekday_variants(self):
        cases = {
            0: ["Mon", "MON- Day", "Monday", "Mon-\nnight", "Mond", "Monay", "MonNight", "Mon - day"],
            1: ["Tue", "Tues", "Tuesday", "Tue- day", "Tuseday", "Tuesdy", "Tu-Night"],
            2: ["Wed", "Weds", "Wednesday", "Wendesday", "Wednsday", "Wed- Night"],
            3: ["Thu", "Thur", "Thurs", "Thursday", "Thrusday", "Thr-day", "Thur- night", "Thursday -\nnight"],
            4: ["Fri", "Friday", "Fryday", "Frid", "Fri - night", "Fri-day"],
            5: ["Sat", "Saturday", "Satur", "Saterday", "Sat- day"],
            6: ["Sun", "Sunday", "Sunady", "Sun - night"],
        }
        for idx, texts in cases.items():
            for t in texts:
                self.assertEqual(detect_weekday(t), idx, t)

    def test_no_weekday(self):
        for t in ["Day", "Night", "No.-Day", "Nite", "", None, "Day shift", "Col_1", "Total"]:
            self.assertIsNone(detect_weekday(t), t)

    def test_shift(self):
        for t in ["Mon- Night", "Nite", "Thursday -\nnight", "Wed-Nigth", "Tue- NIGHT"]:
            self.assertEqual(detect_shift(t), "NIGHT", t)
        for t in ["Mon- day", "Day", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sun-Day", "Monday", "Fri"]:
            self.assertEqual(detect_shift(t), "DAY", t)


if __name__ == '__main__':
    unittest.main()
