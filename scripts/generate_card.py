"""Render a branded graphic card for a queue row when no real product photo
has been supplied yet. Pure local rendering, no network required.

This exists so daily posting never blocks on sourcing photography — real
photos (when you add them to assets/pending/) always win; this is the
fallback, not the goal. Engagement will generally be lower than real
product/install photos, so swap these out when you can.
"""
import random
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


def generate_caption_overlay(brand: str, product_name: str, post_type: str, output_path: str) -> None:
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


def generate_stock_chart_image(output_path: str, seed: int = None) -> None:
    """Abstract, generic market-chart graphic -- not a real index, ticker,
    or lifted stock photo, so there's no rights issue and no implication
    this represents any specific real security's actual performance.
    Candlesticks + a trend line on a grid, in the brand's color palette."""
    rng = random.Random(seed)
    img = Image.new("RGB", (REEL_WIDTH, REEL_HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    chart_top, chart_bottom = 500, 1500
    chart_left, chart_right = 60, REEL_WIDTH - 60
    grid_color = (40, 40, 44)
    for i in range(1, 6):
        y = chart_top + (chart_bottom - chart_top) * i // 6
        draw.line([(chart_left, y), (chart_right, y)], fill=grid_color, width=2)

    n = 28
    xs = [chart_left + (chart_right - chart_left) * i // (n - 1) for i in range(n)]
    value = 0.35
    values = []
    for _ in range(n):
        value += rng.uniform(-0.05, 0.085)  # gentle upward drift overall
        value = max(0.05, min(0.95, value))
        values.append(value)

    candle_w = max(6, (chart_right - chart_left) // (n * 2))
    for i, x in enumerate(xs):
        v = values[i]
        prev = values[i - 1] if i > 0 else v
        y_open = chart_bottom - int((chart_bottom - chart_top) * prev)
        y_close = chart_bottom - int((chart_bottom - chart_top) * v)
        up = y_close <= y_open
        color = (60, 170, 100) if up else ACCENT
        top, bottom = min(y_open, y_close), max(y_open, y_close)
        wick = max(3, candle_w // 3)
        draw.line([(x, top - 18), (x, bottom + 18)], fill=color, width=wick)
        draw.rectangle([(x - candle_w, top), (x + candle_w, max(bottom, top + 6))], fill=color)

    trend_points = [
        (xs[i], chart_bottom - int((chart_bottom - chart_top) * values[i]))
        for i in range(n)
    ]
    draw.line(trend_points, fill=FG, width=5, joint="curve")

    margin = 80
    draw.rectangle([(0, 0), (REEL_WIDTH, 14)], fill=ACCENT)
    label_font = _font(BOLD, 46)
    draw.text((margin, 100), "RGVM8 LIFESTYLE", font=label_font, fill=ACCENT)

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
