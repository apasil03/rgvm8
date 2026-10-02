"""'True cost' breakdowns for queue rows (see content/true_cost.json).

A row with an entry in true_cost.json posts as a cost breakdown -- part
price + install labor + what that same money would grow to if invested --
instead of the plain product caption/card. That's the M8 Mindset angle
(see content/brand_voice.md): the car is the payoff of financial
discipline, so show the real math, not just the hype.

Numbers are never invented: part_price and install_hours must be filled in
by a human from the vendor's listing / install guide. A row whose entry is
still missing them is blocked from posting (prepare_post.py skips it), the
same way an affiliate row with a TODO link is.
"""
import json
from pathlib import Path

TRUE_COST_PATH = Path(__file__).resolve().parent.parent.parent / "content" / "true_cost.json"

REQUIRED_FIELDS = ("part_price", "install_hours", "price_checked")


def _load() -> dict:
    if not TRUE_COST_PATH.is_file():
        return {"assumptions": {}, "rows": {}}
    return json.loads(TRUE_COST_PATH.read_text())


def entry_for(row_id: str):
    """The raw true_cost.json entry for a row, or None if the row isn't a
    true-cost post at all."""
    return _load().get("rows", {}).get(row_id)


def missing_fields(entry: dict) -> list:
    return [f for f in REQUIRED_FIELDS if entry.get(f) in (None, "")]


def compute(row_id: str):
    """Full breakdown for a row, or None if it isn't a true-cost row.
    Raises ValueError if the row has an entry but its numbers aren't
    filled in yet -- callers should have blocked it before this point."""
    data = _load()
    entry = data.get("rows", {}).get(row_id)
    if entry is None:
        return None
    missing = missing_fields(entry)
    if missing:
        raise ValueError(f"true_cost.json row {row_id} is missing {', '.join(missing)}")

    a = data.get("assumptions", {})
    labor_rate = float(entry.get("labor_rate", a.get("labor_rate_per_hour", 150)))
    annual_return = float(a.get("annual_return", 0.07))
    years = int(a.get("years", 10))

    part_price = float(entry["part_price"])
    install_hours = float(entry["install_hours"])
    labor = round(install_hours * labor_rate)
    all_in = round(part_price + labor)
    invested = round(all_in * (1 + annual_return) ** years)

    return {
        "part_price": part_price,
        "install_hours": install_hours,
        "labor_rate": labor_rate,
        "labor": labor,
        "all_in": all_in,
        "diy_friendly": bool(entry.get("diy_friendly", False)),
        "annual_return": annual_return,
        "years": years,
        "invested": invested,
        "price_checked": entry["price_checked"],
    }


def money(value: float) -> str:
    return f"${value:,.0f}"


def hours(value: float) -> str:
    return f"{value:g} hr" if value == 1 else f"{value:g} hrs"
