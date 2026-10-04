"""Shared read/write for content/queue.csv."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
QUEUE_PATH = ROOT / "content" / "queue.csv"
PENDING_DIR = ROOT / "assets" / "pending"

FIELDNAMES = [
    "id", "scheduled_date", "post_type", "brand", "product_name", "key_points",
    "image_path", "affiliate_link", "status", "posted_at", "ig_media_id", "source_media_id",
]

HEADER_COMMENT = """\
# Columns:
#   id             - unique row id, e.g. 001
#   scheduled_date - YYYY-MM-DD, earliest date this may post (posts in date then id order)
#   post_type      - "affiliate" (needs a real affiliate_link, gets #ad), "engagement"
#                     (general car content, no link needed, no #ad -- it would be
#                     false to disclose an ad on unpaid content), "recycle" (our
#                     own old post, resurfaced with a fresh caption -- needs
#                     source_media_id), or "manifesto" (one-off lifestyle/mindset
#                     post, not a product pitch -- product_name is the hook line,
#                     key_points are semicolon-separated body paragraphs, a fixed
#                     comment-to-DM CTA + hashtags are added automatically)
#   brand          - affiliate: RW Carbon, ECS Tuning, RCW Performance, Bimmer Plug,
#                     ARM Motorsports, AutoTecknic. engagement: any real marque (BMW, Ferrari, McLaren, ...).
#                     blank for recycle/manifesto.
#   product_name   - real product/model name. blank for recycle. the hook line for manifesto.
#   key_points     - 1-2 short factual points, semicolon-separated. No invented specs.
#                     blank for recycle. body paragraphs (semicolon-separated) for manifesto.
#   image_path     - real photo/video filename in assets/pending/, or a TODO
#                     placeholder to have a Reel auto-generated (real media always wins).
#                     unused for recycle -- it reuses the original post's own media.
#   affiliate_link - required (non-TODO) for post_type=affiliate; leave blank otherwise
#   status         - pending | posted | draft  (leave as pending when adding a row that
#                     should post on schedule; the bot flips pending -> posted. "draft"
#                     is never picked up by automation -- only a manual publish moves it)
#   posted_at      - left blank, filled in automatically
#   ig_media_id    - left blank, filled in automatically (the NEW post's id)
#   source_media_id - required for post_type=recycle: the existing IG media id
#                     to resurface (from scripts/list_media.py). blank otherwise.
"""


def read_queue() -> list:
    rows = []
    with QUEUE_PATH.open(newline="") as f:
        for line in f:
            if line.strip().startswith("#") or not line.strip():
                continue
            rows.append(line)
    reader = csv.DictReader(rows)
    parsed = list(reader)
    for row in parsed:
        if None in row or any(v is None for v in row.values()):
            raise ValueError(
                f"content/queue.csv row {row.get('id')} has the wrong number of "
                "columns — check for an unquoted comma inside a field (e.g. in "
                "key_points) shifting the rest of the row."
            )
    return parsed


def write_queue(rows: list) -> None:
    with QUEUE_PATH.open("w", newline="") as f:
        f.write(HEADER_COMMENT)
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def due_rows(rows: list, today: str) -> list:
    due = [r for r in rows if r["status"] == "pending" and r["scheduled_date"] <= today]
    due.sort(key=lambda r: (r["scheduled_date"], r["id"]))
    return due
