"""Caption building in the @rgvm8 brand voice (see content/brand_voice.md)."""
import json
import random
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from lib import true_cost as tc

CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content"


def add_utm(link: str, campaign: str) -> str:
    parsed = urlparse(link)
    params = dict(parse_qsl(parsed.query))
    params.setdefault("utm_source", "instagram")
    params.setdefault("utm_medium", "social")
    params.setdefault("utm_campaign", campaign)
    new_query = urlencode(params)
    return urlunparse(parsed._replace(query=new_query))


def pick_hashtags(brand: str, general_count: int = 4, brand_count: int = 2) -> list:
    data = json.loads((CONTENT_DIR / "hashtags.json").read_text())
    general = random.sample(data["general"], min(general_count, len(data["general"])))
    brand_tags = data["brand"].get(brand, [])
    brand_sample = random.sample(brand_tags, min(brand_count, len(brand_tags)))
    return general + brand_sample


# Save/share/tag prompts are what actually move these posts in the algorithm
# (saves and shares outrank likes) — this is how big car pages caption things,
# not just generic hype.
AFFILIATE_ENGAGEMENT_LINES = [
    "Save this for your build list 📌",
    "Tag someone who needs this in their garage 👇",
    "Rate this mod 1-10 👇",
]
ENGAGEMENT_ENGAGEMENT_LINES = [
    "Would you daily this? 👇",
    "Tag someone who'd love this 👇",
    "Drop a 🔥 if this belongs in your dream garage",
]
UGC_CALLOUT = "Got a build like this? Tag @rgvm8 to get featured 📸"
UGC_CALLOUT_CHANCE = 0.25  # occasional, not every post — keeps it from feeling like spam

RECYCLE_HOOKS = [
    "Throwback to one of our favorites 🔁",
    "Still one of the best ones we've posted 🔥",
    "In case you missed this the first time around 👀",
]
RECYCLE_ENGAGEMENT_LINES = [
    "Tag someone who needs to see this 👇",
    "Still holds up — agree? 👇",
    "Save this one if you missed it 📌",
]


def build_recycle_caption(original_caption: str) -> str:
    """'New twist' on our own old content: a throwback hook instead of a
    verbatim repost, so it doesn't just duplicate the original caption for
    anyone scrolling back. Our own content, so no rights concern -- this is
    purely about not looking like an accidental double-post."""
    first_line = (original_caption or "").strip().split("\n")[0][:150]
    hook = random.choice(RECYCLE_HOOKS)
    engagement_line = random.choice(RECYCLE_ENGAGEMENT_LINES)
    hashtags = pick_hashtags("")

    body = f"{first_line}\n\n" if first_line else ""
    return (
        f"{hook}\n\n"
        f"{body}"
        f"{engagement_line}\n"
        f"Follow @rgvm8 for more 🔧\n\n"
        f"{' '.join(hashtags)}"
    )


TRUE_COST_ENGAGEMENT_LINES = [
    "Worth it, or would you invest it? 👇",
    "Mod or market? Drop your pick 👇",
    "Save this before your next build purchase 📌",
]


def build_true_cost_caption(brand: str, product_name: str, key_points: str, cost: dict, post_type: str = "affiliate") -> str:
    """M8 Mindset post: the real all-in cost of a mod next to what the same
    money would do invested. Every number comes from true_cost.json (filled
    in by a human) or its stated assumptions -- the investing line is
    labeled hypothetical, and nothing here is advice to buy or not buy."""
    first_point = next((p.strip() for p in key_points.split(";") if p.strip()), "")
    hashtags = pick_hashtags(brand, general_count=3) + ["#m8mindset", "#financialfreedom"]

    disclosure = "#ad " if post_type == "affiliate" else ""
    hook = f"{disclosure}The true cost of the {brand} {product_name} 💸"
    labor_line = f"Install: ~{tc.hours(cost['install_hours'])} (~{tc.money(cost['labor'])} at {tc.money(cost['labor_rate'])}/hr shop rate)"
    if cost["diy_friendly"]:
        labor_line += " -- or $0 if you DIY"
    pct = f"{cost['annual_return'] * 100:g}%"
    cta = "Link in bio 🔗" if post_type == "affiliate" else "Follow @rgvm8 for more 🔧"

    return (
        f"{hook}\n\n"
        f"Part: {tc.money(cost['part_price'])}\n"
        f"{labor_line}\n"
        f"All-in: ~{tc.money(cost['all_in'])}\n\n"
        f"Same {tc.money(cost['all_in'])} invested at {pct}/yr for {cost['years']} years ≈ {tc.money(cost['invested'])}. "
        f"M8 Mindset: invest first, mod with what's left.\n\n"
        + (f"{first_point}.\n\n" if first_point else "")
        + f"{random.choice(TRUE_COST_ENGAGEMENT_LINES)}\n"
        f"{cta}\n"
        f"Plan your own build with the budget tool in bio.\n\n"
        f"Price checked {cost['price_checked']}. Investing math is hypothetical, not financial advice.\n\n"
        f"{' '.join(hashtags)}"
    )


def build_caption(brand: str, product_name: str, key_points: str, affiliate_link: str = "", post_type: str = "affiliate", row_id: str = "") -> str:
    cost = tc.compute(row_id) if row_id else None
    if cost is not None:
        return build_true_cost_caption(brand, product_name, key_points, cost, post_type)

    points = [p.strip() for p in key_points.split(";") if p.strip()]
    points_line = " ".join(f"{p}." if not p.endswith((".", "!")) else p for p in points)
    hashtags = pick_hashtags(brand)

    if post_type == "engagement":
        # General car-culture content: no product, no affiliate link, so no
        # #ad disclosure (it would be false — nothing here is sponsored).
        hook = f"{brand} spotlight: {product_name}. 🏁"
        cta = "Follow @rgvm8 for more 🔧"
        engagement_line = random.choice(ENGAGEMENT_ENGAGEMENT_LINES)
    else:
        # FTC guidance requires the disclosure to be unmissable, not hidden
        # behind Instagram's "...more" truncation (~125 chars) — so it goes
        # at the very front, not tacked on before the hashtag block.
        hook = f"#ad New from {brand}: {product_name}. 🔧"
        cta = "Link in bio 🔗"
        engagement_line = random.choice(AFFILIATE_ENGAGEMENT_LINES)

    ugc_line = f"\n{UGC_CALLOUT}\n" if random.random() < UGC_CALLOUT_CHANCE else ""

    return (
        f"{hook}\n\n"
        f"{points_line}\n\n"
        f"{engagement_line}\n"
        f"{cta}\n"
        f"{ugc_line}\n"
        f"{' '.join(hashtags)}"
    )
