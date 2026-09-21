"""Shared read/write for content/queue.csv."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
QUEUE_PATH = ROOT / "content" / "queue.csv"
PENDING_DIR = ROOT / "assets" / "pending"

FIELDNAMES = [
    "id", "scheduled_date", "post_type", "brand", "product_name", "key_points",
    "image_path", "affiliate_link", "status", "posted_at", "ig_media_id",
]

HEADER_COMMENT = """\
# Columns:
#   id             - unique row id, e.g. 001
#   scheduled_date - YYYY-MM-DD, earliest date this may post (posts in date then id order)
#   post_type      - "affiliate" (needs a real affiliate_link, gets #ad) or
#                     "engagement" (general car content, no link needed, no #ad —
#                     it would be false to disclose an ad on unpaid content)
#   brand          - affiliate: RW Carbon, ECS Tuning, RCW Performance, Bimmer Plug,
#                     ARM Motorsports, AutoTecknic. engagement: any real marque (BMW, Ferrari, McLaren, ...)
#   product_name   - real product/model name
#   key_points     - 1-2 short factual points, semicolon-separated. No invented specs.
#   image_path     - filename in assets/pending/, or a TODO placeholder to have a card auto-generated
#   affiliate_link - required (non-TODO) for post_type=affiliate; leave blank for engagement
#   status         - pending | posted  (leave as pending when adding a row; the bot flips it)
#   posted_at      - left blank, filled in automatically
#   ig_media_id    - left blank, filled in automatically
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
