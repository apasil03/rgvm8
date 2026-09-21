#!/usr/bin/env python3
"""Publish the next pending row in content/queue.csv to Instagram.

Requires env vars: IG_ACCESS_TOKEN, IG_BUSINESS_ID.
Images must already be publicly reachable (see docs/SETUP.md for the
GitHub Pages hosting setup) at PAGES_BASE_URL/assets/pending/<image_path>.
"""
import csv
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import caption as caption_lib  # noqa: E402
from lib import graph_api  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = ROOT / "content" / "queue.csv"

FIELDNAMES = [
    "id", "scheduled_date", "brand", "product_name", "key_points",
    "image_path", "affiliate_link", "status", "posted_at", "ig_media_id",
]


def read_queue() -> list:
    rows = []
    with QUEUE_PATH.open(newline="") as f:
        for line in f:
            if line.strip().startswith("#") or not line.strip():
                continue
            rows.append(line)
    reader = csv.DictReader(rows)
    return list(reader)


def write_queue(rows: list) -> None:
    with QUEUE_PATH.open("w", newline="") as f:
        f.write(
            "# See content/queue.csv comments (in git history / README) for column docs\n"
        )
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_BUSINESS_ID"]
    pages_base_url = os.environ["PAGES_BASE_URL"].rstrip("/")

    rows = read_queue()
    today = dt.date.today().isoformat()
    pending = [
        r for r in rows
        if r["status"] == "pending" and r["scheduled_date"] <= today
    ]
    pending.sort(key=lambda r: (r["scheduled_date"], r["id"]))

    if not pending:
        print("No pending posts due today. Nothing to do.")
        return 0

    row = pending[0]
    image_url = f"{pages_base_url}/assets/pending/{row['image_path']}"
    text = caption_lib.build_caption(
        brand=row["brand"],
        product_name=row["product_name"],
        key_points=row["key_points"],
        affiliate_link=caption_lib.add_utm(row["affiliate_link"], campaign="daily_post"),
    )

    print(f"Posting row {row['id']} ({row['brand']} - {row['product_name']})")
    container_id = graph_api.create_media_container(ig_user_id, image_url, text, token)
    graph_api.wait_until_container_ready(container_id, token)
    media_id = graph_api.publish_media(ig_user_id, container_id, token)
    print(f"Published as media {media_id}")

    for r in rows:
        if r["id"] == row["id"]:
            r["status"] = "posted"
            r["posted_at"] = dt.datetime.utcnow().isoformat()
            r["ig_media_id"] = media_id
    write_queue(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
