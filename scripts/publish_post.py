#!/usr/bin/env python3
"""Publish the queue row picked by prepare_post.py to Instagram.

Must run only after that row's image has actually been deployed to
GitHub Pages (the workflow deploys Pages between prepare and publish),
since the Graph API fetches the image from PAGES_BASE_URL itself.

Requires env vars: IG_ACCESS_TOKEN, IG_BUSINESS_ID, PAGES_BASE_URL, ROW_ID.
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
        print(f"Row {row_id} not found in queue.csv (did something change it between steps?)")
        return 1

    post_type = row.get("post_type", "affiliate")
    link = caption_lib.add_utm(row["affiliate_link"], campaign="daily_post") if row["affiliate_link"] else ""
    media_url = f"{pages_base_url}/assets/pending/{row['image_path']}"
    is_video = row["image_path"].lower().endswith((".mp4", ".mov"))
    text = caption_lib.build_caption(
        brand=row["brand"],
        product_name=row["product_name"],
        key_points=row["key_points"],
        affiliate_link=link,
        post_type=post_type,
    )

    print(f"Posting row {row['id']} ({row['brand']} - {row['product_name']}) using {media_url} ({'reel' if is_video else 'image'})")
    if is_video:
        container_id = graph_api.create_reels_container(ig_user_id, media_url, text, token)
        graph_api.wait_until_container_ready(container_id, token, timeout_s=300)
    else:
        container_id = graph_api.create_media_container(ig_user_id, media_url, text, token)
        graph_api.wait_until_container_ready(container_id, token)
    media_id = graph_api.publish_media(ig_user_id, container_id, token)
    print(f"Published as media {media_id}")

    row["status"] = "posted"
    row["posted_at"] = dt.datetime.utcnow().isoformat()
    row["ig_media_id"] = media_id
    queue.write_queue(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
