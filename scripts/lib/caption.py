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


def build_caption(brand: str, product_name: str, key_points: str, affiliate_link: str = "", post_type: str = "affiliate") -> str:
    points = [p.strip() for p in key_points.split(";") if p.strip()]
    points_line = " ".join(f"{p}." if not p.endswith((".", "!")) else p for p in points)
    hashtags = pick_hashtags(brand)

    if post_type == "engagement":
        # General car-culture content: no product, no affiliate link, so no
        # #ad disclosure (it would be false — nothing here is sponsored).
        hook = f"{brand} spotlight: {product_name}. 🏁"
        cta = "Follow @rgvm8 for more 🔧"
        disclosure = ""
    else:
        hook = f"New from {brand}: {product_name}. 🔧"
        cta = "Link in bio 🔗"
        disclosure = "#ad\n"

    return (
        f"{hook}\n\n"
        f"{points_line}\n\n"
        f"{cta}\n\n"
        f"{disclosure}"
        f"{' '.join(hashtags)}"
    )
