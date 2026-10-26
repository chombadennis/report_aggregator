"""Tolerant weekday / shift detection for labour table headers.

Handles abbreviations (Mon, Tue, Tues, Thur, Thurs, Thr), full names, glued shift words
(MonNight), stray punctuation/newlines, and common misspellings (Wendesday, Fryday...).
"""
import re
import difflib
from typing import Optional

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_TOKENS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
_ALIASES = {
    0: ["mon", "mond", "mo"],
    1: ["tue", "tues", "tu", "tue"],
    2: ["wed", "weds", "wd"],
    3: ["thu", "thur", "thurs", "thr", "thrs", "th"],
    4: ["fri", "fr"],
    5: ["sat", "satur", "sa"],
    6: ["sun", "su"],
}
_NOISE = {"day", "days", "night", "nights", "nite", "no", "shift", "am", "pm", "d", "n", "s", "of", "the"}
_SUFFIXES = ("night", "nite", "day")


def _match_token(tok: str) -> Optional[int]:
    if len(tok) < 2:
        return None
    for idx, aliases in _ALIASES.items():
        if tok in aliases:
            return idx
    # Prefix of a full name (e.g. "wednes", "satur", "thursd")
    if len(tok) >= 3:
        pref = [i for i, n in enumerate(DAY_NAMES) if n.startswith(tok)]
        if len(pref) == 1:
            return pref[0]
    # Fuzzy match for misspellings (e.g. "wendesday", "fryday", "tuseday")
    if len(tok) >= 4:
        best_idx, best = None, 0.0
        for idx, name in enumerate(DAY_NAMES):
            r = difflib.SequenceMatcher(None, tok, name).ratio()
            if r > best:
                best_idx, best = idx, r
        if best >= 0.78:
            return best_idx
    return None


def detect_weekday(text) -> Optional[int]:
    """Returns 0..6 (Mon..Sun) if the header text names a weekday, else None."""
    if not text:
        return None
    for tok in re.findall(r"[a-z]+", str(text).lower()):
        if tok in _NOISE:
            continue
        # Strip glued shift words: "monnight" -> "mon", "thursday" stays intact (not a suffix match
        # because "day" suffix is only stripped if what remains is a valid weekday token).
        candidates = [tok]
        for suf in _SUFFIXES:
            if tok.endswith(suf) and len(tok) > len(suf):
                candidates.append(tok[: -len(suf)])
        for c in candidates:
            idx = _match_token(c)
            if idx is not None:
                return idx
    return None


def detect_shift(text) -> str:
    """'NIGHT' if header mentions night/nite (or fuzzy variants), else 'DAY'."""
    low = str(text or "").lower()
    if "night" in low or "nite" in low:
        return "NIGHT"
    for tok in re.findall(r"[a-z]+", low):
        for cand in {tok, tok[-5:], tok[:5]}:
            if len(cand) >= 4 and difflib.SequenceMatcher(None, cand, "night").ratio() >= 0.8:
                return "NIGHT"
    return "DAY"


def distinct_days(keys) -> set:
    return {d for d in (detect_weekday(k) for k in keys) if d is not None}
