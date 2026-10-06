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


MANIFESTO_HASHTAGS = "#M8Mindset #GenerationalWealth #ResponsibleOwnership #InvestConsistently #FamilyFirst"
MANIFESTO_CTA = 'Comment "investing starter guide" and I\'ll send you ours. 📩'


def build_manifesto_caption(hook: str, body_points: str, tag_handles: str = "") -> str:
    """One-off lifestyle/mindset posts (not a product pitch) -- hook and
    body paragraphs come from the queue row; the comment-to-DM CTA and
    hashtags are fixed boilerplate tied to the private-reply automation,
    not meant to vary per-post. tag_handles (semicolon-separated @handles,
    reusing the otherwise-unused brand column for this post_type) are
    credited as a separate line -- this is a video post, and the Graph
    API's tappable photo-tag (user_tags) only works on image posts, so an
    @mention in the caption is the real mechanism for crediting someone
    on a Reel."""
    paragraphs = [p.strip() for p in body_points.split(";") if p.strip()]
    body = "\n\n".join(paragraphs)
    tags = [t.strip() for t in tag_handles.split(";") if t.strip()]
    tag_section = f"Learn from some of the best voices in personal finance:\n{' '.join(tags)}\n\n" if tags else ""
    return (
        f"{hook}\n\n"
        f"{body}\n\n"
        f"{MANIFESTO_CTA}\n\n"
        f"Follow @rgvm8 for more car + mindset content.\n\n"
        f"{tag_section}"
        f"{MANIFESTO_HASHTAGS}"
    )


def build_roundup_caption(hook: str, body_points: str, brand_tags: list) -> str:
    """Multi-brand 'link in bio' post -- doesn't fit the single
    affiliate_link/brand schema build_caption() assumes, since it points
    to several real commission links at once via the bio link. Still
    needs #ad up front: the bio link it's driving clicks to is a real
    commission link, same disclosure obligation as a single-brand post."""
    paragraphs = [p.strip() for p in body_points.split(";") if p.strip()]
    body = "\n\n".join(paragraphs)
    general = pick_hashtags("", general_count=4, brand_count=0)
    hashtags = general + brand_tags
    return (
        f"#ad {hook}\n\n"
        f"{body}\n\n"
        f"Link in bio 🔗\n\n"
        f"{' '.join(hashtags)}"
    )


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
