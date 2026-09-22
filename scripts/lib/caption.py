"""Caption building in the @rgvm8 brand voice (see content/brand_voice.md)."""
import json
import random
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

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


def build_caption(brand: str, product_name: str, key_points: str, affiliate_link: str = "", post_type: str = "affiliate") -> str:
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
