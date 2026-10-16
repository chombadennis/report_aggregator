"""
Normalisation of the 'MATERIALS DELIVERED TO SITE' rows.

Handles:
  * thousands separators ("2,000 pcs" -> 2000, "pcs")
  * rows broken by an earlier bad parse ("2" + ",000 pcs")
  * several items packed into a single multi-line cell (rebars per diameter)
  * all rebar spellings (rebars / reinforcement bars / steel reinforcement bars ...)
    mapped to one category, one row per diameter.
"""
import re

REBAR_BASE = "STEEL REINFORCEMENT BARS"

_REBAR_WORDS = re.compile(
    r"re-?bars?\b|reinforcement|steel\s+bars?|reinforcing|\b(?:hy|y|t|d)\s?-?\d{1,2}\b\s*(?:bars?|mm)?",
    re.IGNORECASE,
)
_DIAMETER = re.compile(r"\b(?:hy|y|t|d)\s?-?(\d{1,2})\b|\b(\d{1,2})\s?mm\b", re.IGNORECASE)
_QTY = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*([A-Za-z][A-Za-z.\-/]*)?")


def parse_number(text):
    """'2,000' -> 2000.0 ; returns None if no number."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(text or ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def is_rebar(text):
    return bool(_REBAR_WORDS.search(str(text or "")))


def _diameter(text):
    m = _DIAMETER.search(str(text or ""))
    if not m:
        return None
    return m.group(1) or m.group(2)


def _clean_name(name):
    name = re.sub(r"\s+", " ", str(name or "")).strip().upper()
    name = re.sub(r"(?<=\w)-\s+", " ", name)  # "CEMENT- 42.5N" -> "CEMENT 42.5N"
    return name or "UNKNOWN"


def rebar_name(diameter=None):
    return f"{REBAR_BASE} D{diameter}" if diameter else REBAR_BASE


def canonical_name(desc):
    """Canonical key for a single-line material description."""
    if is_rebar(desc):
        return rebar_name(_diameter(desc))
    return _clean_name(desc)


def _repair_qty_text(quantity, units):
    """Rejoin quantities split at the comma by an earlier parse ('2' + ',000 pcs')."""
    q = str(quantity or "").strip()
    u = str(units or "").strip()
    if u and re.match(r"^,\d", u):
        return f"{q}{u}"
    return f"{q} {u}".strip()


def _split_qty(qty_text):
    """Return list of (number, unit) found in a (possibly multi-value) qty string."""
    out = []
    for m in _QTY.finditer(str(qty_text or "")):
        num = parse_number(m.group(1))
        if num is not None:
            out.append((num, (m.group(2) or "").strip()))
    return out


def normalize_item(item):
    """
    Takes one raw {description, quantity, units} dict and returns a list of clean
    {description, quantity, units} dicts (quantity is a plain number string).
    """
    desc_raw = str(item.get("description", item.get("Description", "")) or "")
    qty_raw = item.get("quantity", item.get("Quantity", ""))
    units_raw = item.get("units", item.get("Units", ""))
    qty_text = _repair_qty_text(qty_raw, units_raw)

    desc_lines = [l.strip() for l in desc_raw.splitlines() if l.strip()]
    quantities = _split_qty(qty_text)
    if not desc_lines or not quantities:
        return []

    def make(desc, q):
        return {"description": desc, "quantity": f"{q[0]:g}" if q[0] != int(q[0]) else str(int(q[0])), "units": q[1]}

    # Single description line
    if len(desc_lines) == 1:
        name = canonical_name(desc_lines[0])
        return [make(name, q) for q in quantities[:1]] if len(quantities) == 1 else [make(name, q) for q in quantities]

    # Multi-line cell: header line(s) + one line per sub-item aligned with quantities.
    n = len(quantities)
    sub_lines = desc_lines[-n:] if len(desc_lines) >= n else desc_lines
    header = " ".join(desc_lines[: len(desc_lines) - len(sub_lines)])
    rebar_group = is_rebar(header) or any(is_rebar(l) for l in desc_lines)

    results = []
    for line, q in zip(sub_lines, quantities):
        if rebar_group:
            results.append(make(rebar_name(_diameter(line) or _diameter(header)), q))
        else:
            full = f"{header} {line}".strip() if header else line
            results.append(make(canonical_name(full), q))
    return results


def normalize_materials(items):
    """Normalise a list of raw material rows into a flat list of clean rows."""
    out = []
    for it in items or []:
        if hasattr(it, "model_dump"):
            it = it.model_dump()
        if not isinstance(it, dict):
            continue
        out.extend(normalize_item(it))
    return out


def sum_materials(daily_item_lists):
    """
    Aggregate several days of raw material rows -> {NAME: {"qty": float, "unit": str}}.
    Rebars are grouped together at the end, one row per diameter (ascending).
    """
    totals = {}
    for items in daily_item_lists:
        for it in normalize_materials(items):
            name = it["description"]
            qty = parse_number(it["quantity"]) or 0.0
            unit = it["units"]
            entry = totals.setdefault(name, {"qty": 0.0, "unit": unit})
            entry["qty"] += qty
            if not entry["unit"] and unit:
                entry["unit"] = unit

    for v in totals.values():
        v["qty"] = round(v["qty"], 2)
        if v["qty"] == int(v["qty"]):
            v["qty"] = int(v["qty"])

    def rebar_key(k):
        d = re.search(r"D(\d+)$", k)
        return int(d.group(1)) if d else 0

    others = {k: v for k, v in totals.items() if not k.startswith(REBAR_BASE)}
    rebars = {k: totals[k] for k in sorted((k for k in totals if k.startswith(REBAR_BASE)), key=rebar_key)}
    others.update(rebars)
    return others
