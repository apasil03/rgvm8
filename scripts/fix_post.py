#!/usr/bin/env python3
"""One-off repost: delete an already-published queue row's live Instagram
media and publish a replacement from its current (updated) image_path.

Used when a post needs a real correction after it's already live (e.g. the
source media file was regenerated to add audio) -- normal daily automation
only ever publishes a row once via publish_post.py.

Requires env vars: IG_ACCESS_TOKEN, IG_BUSINESS_ID, PAGES_BASE_URL, ROW_ID.
The row's image at image_path must already be deployed to GitHub Pages
before this runs.
"""
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import caption as caption_lib  # noqa: E402
from lib import graph_api  # noqa: E402
from lib import queue  # noqa: E402


def main() -> int:
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_BUSINESS_ID"]
    pages_base_url = os.environ["PAGES_BASE_URL"].rstrip("/")
    row_id = os.environ["ROW_ID"]

    rows = queue.read_queue()
    row = next((r for r in rows if r["id"] == row_id), None)
    if row is None:
        print(f"Row {row_id} not found in queue.csv")
        return 1
    if not row.get("ig_media_id"):
        print(f"Row {row_id} has no ig_media_id -- nothing live to replace")
        return 1

    old_media_id = row["ig_media_id"]
    if os.environ.get("SKIP_DELETE") == "true":
        print(f"Skipping delete of {old_media_id} (SKIP_DELETE=true -- assuming it was removed manually)")
    else:
        print(f"Deleting live media {old_media_id} for row {row_id}")
        graph_api.delete_media(old_media_id, token)

    link = caption_lib.add_utm(row["affiliate_link"], campaign="daily_post") if row["affiliate_link"] else ""
    media_url = f"{pages_base_url}/assets/pending/{row['image_path']}"
    is_video = row["image_path"].lower().endswith((".mp4", ".mov"))
    text = caption_lib.build_caption(
        brand=row["brand"],
        product_name=row["product_name"],
        key_points=row["key_points"],
        affiliate_link=link,
        post_type=row.get("post_type", "affiliate"),
        row_id=row["id"],
    )

    print(f"Publishing replacement for row {row_id} using {media_url}")
    if is_video:
        container_id = graph_api.create_reels_container(ig_user_id, media_url, text, token)
        graph_api.wait_until_container_ready(container_id, token, timeout_s=300)
    else:
        container_id = graph_api.create_media_container(ig_user_id, media_url, text, token)
        graph_api.wait_until_container_ready(container_id, token)
    media_id = graph_api.publish_media(ig_user_id, container_id, token)
    print(f"Published replacement as media {media_id}")

    row["posted_at"] = dt.datetime.utcnow().isoformat()
    row["ig_media_id"] = media_id
    queue.write_queue(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
