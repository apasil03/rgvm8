"""Render a branded graphic card for a queue row when no real product photo
has been supplied yet. Pure local rendering, no network required.

This exists so daily posting never blocks on sourcing photography — real
photos (when you add them to assets/pending/) always win; this is the
fallback, not the goal. Engagement will generally be lower than real
product/install photos, so swap these out when you can.
"""
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
BOLD = FONTS_DIR / "BigShoulders-Bold.ttf"
REGULAR = FONTS_DIR / "BigShoulders-Regular.ttf"

WIDTH, HEIGHT = 1080, 1350  # feed card (4:5)
REEL_WIDTH, REEL_HEIGHT = 1080, 1920  # reel background (9:16)
BG = (18, 18, 20)
ACCENT = (200, 40, 40)
FG = (240, 240, 240)
MUTED = (170, 170, 175)


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def _wrap_to_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _render(brand: str, product_name: str, key_points: str, post_type: str, width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    WIDTH, HEIGHT = width, height

    # accent stripe
    draw.rectangle([(0, 0), (WIDTH, 14)], fill=ACCENT)
    draw.rectangle([(0, HEIGHT - 14), (WIDTH, HEIGHT)], fill=ACCENT)

    margin = 80

    # brand
    brand_font = _font(BOLD, 46)
    draw.text((margin, 100), brand.upper(), font=brand_font, fill=ACCENT)

    # product name, wrapped
    name_font = _font(BOLD, 74)
    name_lines = []
    for para in textwrap.wrap(product_name, width=1):  # noop, we wrap by pixel width below
        pass
    name_lines = _wrap_to_width(draw, product_name, name_font, WIDTH - 2 * margin)
    y = 190
    for line in name_lines:
        draw.text((margin, y), line, font=name_font, fill=FG)
        y += 82

    # key points
    y += 40
    point_font = _font(REGULAR, 40)
    points = [p.strip() for p in key_points.split(";") if p.strip()]
    for point in points:
        bullet_lines = _wrap_to_width(draw, point, point_font, WIDTH - 2 * margin - 50)
        draw.ellipse([(margin, y + 14), (margin + 16, y + 30)], fill=ACCENT)
        for i, bl in enumerate(bullet_lines):
            draw.text((margin + 40, y + i * 48), bl, font=point_font, fill=MUTED)
        y += 48 * len(bullet_lines) + 24

    # footer: handle + CTA
    footer_font = _font(BOLD, 44)
    cta_font = _font(REGULAR, 34)
    footer_cta = "Follow for more" if post_type == "engagement" else "Link in bio  //  #ad"
    draw.text((margin, HEIGHT - 160), "@RGVM8", font=footer_font, fill=FG)
    draw.text((margin, HEIGHT - 100), footer_cta, font=cta_font, fill=MUTED)

    return img


def _render_true_cost(brand: str, product_name: str, cost: dict, post_type: str, width: int, height: int) -> Image.Image:
    """Cost-breakdown variant of the card for true-cost rows: part + labor
    = all-in, then what the same money would be worth invested. Numbers
    come straight from lib/true_cost.compute(), never invented here."""
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width, 14)], fill=ACCENT)
    draw.rectangle([(0, height - 14), (width, height)], fill=ACCENT)
    margin = 80
    inner = width - 2 * margin
    top = (height - HEIGHT) // 2  # centers the block on a 9:16 reel, no-op on the 4:5 card

    draw.text((margin, top + 100), "THE TRUE COST", font=_font(BOLD, 46), fill=ACCENT)
    name_font = _font(BOLD, 64)
    y = top + 180
    for line in _wrap_to_width(draw, f"{brand} {product_name}", name_font, inner)[:3]:
        draw.text((margin, y), line, font=name_font, fill=FG)
        y += 72

    # ledger: label left, amount right-aligned
    y += 50
    label_font = _font(REGULAR, 46)
    amount_font = _font(BOLD, 52)
    labor_label = f"Install ~{cost['install_hours']:g} hr @ ${cost['labor_rate']:,.0f}/hr"
    for label, amount in (("Part", cost["part_price"]), (labor_label, cost["labor"])):
        draw.text((margin, y), label, font=label_font, fill=MUTED)
        text = f"${amount:,.0f}"
        draw.text((width - margin - draw.textlength(text, font=amount_font), y - 4), text, font=amount_font, fill=FG)
        y += 78
    draw.rectangle([(margin, y), (width - margin, y + 4)], fill=MUTED)
    y += 30
    total_font = _font(BOLD, 72)
    draw.text((margin, y), "ALL-IN", font=total_font, fill=FG)
    text = f"${cost['all_in']:,.0f}"
    draw.text((width - margin - draw.textlength(text, font=total_font), y), text, font=total_font, fill=ACCENT)
    y += 140

    # the M8 Mindset comparison
    pct = f"{cost['annual_return'] * 100:g}%"
    draw.text((margin, y), f"OR INVEST IT: {pct}/YR x {cost['years']} YRS", font=_font(BOLD, 42), fill=MUTED)
    y += 60
    draw.text((margin, y), f"~${cost['invested']:,.0f}", font=_font(BOLD, 110), fill=FG)
    y += 140
    draw.text((margin, y), "Mod or market?", font=_font(REGULAR, 46), fill=MUTED)

    footer_cta = "Follow for more" if post_type == "engagement" else "Link in bio  //  #ad"
    draw.text((margin, height - 210), "@RGVM8", font=_font(BOLD, 44), fill=FG)
    draw.text((margin, height - 150), footer_cta, font=_font(REGULAR, 34), fill=MUTED)
    draw.text((margin, height - 100), f"Price checked {cost['price_checked']}. Hypothetical math, not financial advice.", font=_font(REGULAR, 28), fill=MUTED)
    return img


def generate_card(brand: str, product_name: str, key_points: str, output_path: str, post_type: str = "affiliate") -> None:
    img = _render(brand, product_name, key_points, post_type, WIDTH, HEIGHT)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=92)


def generate_reel_background(brand: str, product_name: str, key_points: str, output_path: str, post_type: str = "affiliate", cost: dict = None) -> None:
    """Same design language, rendered at 9:16 for use as a Reel background.
    True-cost rows (cost given) get the cost-breakdown layout instead."""
    if cost is not None:
        img = _render_true_cost(brand, product_name, cost, post_type, REEL_WIDTH, REEL_HEIGHT)
    else:
        img = _render(brand, product_name, key_points, post_type, REEL_WIDTH, REEL_HEIGHT)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=92)


def generate_caption_overlay(brand: str, product_name: str, post_type: str, output_path: str, subtitle: str = None) -> None:
    """Transparent bottom-bar overlay (brand/product/handle) for a real-photo
    Reel -- most viewers scroll with sound off, so the photo+music Reels
    still need on-screen text to actually carry the message. Kept to a
    bottom bar rather than the full card so it doesn't cover the photo."""
    img = Image.new("RGBA", (REEL_WIDTH, REEL_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bar_height = 420
    bar_top = REEL_HEIGHT - bar_height
    # gradient fade into a solid bar so the cut from photo to text is soft
    for i in range(120):
        alpha = int(200 * (i / 120))
        draw.line([(0, bar_top - 120 + i), (REEL_WIDTH, bar_top - 120 + i)], fill=(10, 10, 12, alpha))
    draw.rectangle([(0, bar_top), (REEL_WIDTH, REEL_HEIGHT)], fill=(10, 10, 12, 215))
    draw.rectangle([(0, bar_top), (REEL_WIDTH, bar_top + 8)], fill=(*ACCENT, 255))

    margin = 80
    brand_font = _font(BOLD, 44)
    draw.text((margin, bar_top + 40), brand.upper(), font=brand_font, fill=(*ACCENT, 255))
    if subtitle:
        # e.g. "ALL-IN ~$1,599" on true-cost rows -- right-aligned on the brand line
        sub_w = draw.textlength(subtitle, font=brand_font)
        draw.text((REEL_WIDTH - margin - sub_w, bar_top + 40), subtitle, font=brand_font, fill=(*FG, 255))

    name_font = _font(BOLD, 56)
    name_lines = _wrap_to_width(draw, product_name, name_font, REEL_WIDTH - 2 * margin)[:2]
    y = bar_top + 100
    for line in name_lines:
        draw.text((margin, y), line, font=name_font, fill=(*FG, 255))
        y += 64

    footer_font = _font(REGULAR, 34)
    footer_cta = "Follow for more" if post_type == "engagement" else "Link in bio // #ad"
    draw.text((margin, REEL_HEIGHT - 70), f"@RGVM8  //  {footer_cta}", font=footer_font, fill=(*MUTED, 255))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


if __name__ == "__main__":
    generate_card(
        "RW Carbon",
        "BMW F91/F92/F93 M8 DTM Carbon Fiber Rear Diffuser",
        "Genuine carbon fiber with clear coat finish;100% bolt-on using factory diffuser mounting points;Fits all 2019+ M8",
        "/tmp/preview_card.jpg",
    )
    print("wrote /tmp/preview_card.jpg")
