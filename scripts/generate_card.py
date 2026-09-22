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


def generate_card(brand: str, product_name: str, key_points: str, output_path: str, post_type: str = "affiliate") -> None:
    img = _render(brand, product_name, key_points, post_type, WIDTH, HEIGHT)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=92)


def generate_reel_background(brand: str, product_name: str, key_points: str, output_path: str, post_type: str = "affiliate") -> None:
    """Same design language, rendered at 9:16 for use as a Reel background."""
    img = _render(brand, product_name, key_points, post_type, REEL_WIDTH, REEL_HEIGHT)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=92)


if __name__ == "__main__":
    generate_card(
        "RW Carbon",
        "BMW F91/F92/F93 M8 DTM Carbon Fiber Rear Diffuser",
        "Genuine carbon fiber with clear coat finish;100% bolt-on using factory diffuser mounting points;Fits all 2019+ M8",
        "/tmp/preview_card.jpg",
    )
    print("wrote /tmp/preview_card.jpg")
