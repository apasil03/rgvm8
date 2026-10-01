#!/usr/bin/env python3
"""One-off diagnostic: print the account's post history (caption, engagement,
age) so real recycle candidates can be picked with real context, instead of
guessing. Run manually via the list-media workflow; not part of daily
automation.

Requires env vars: IG_ACCESS_TOKEN, IG_BUSINESS_ID.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import graph_api  # noqa: E402


def main() -> int:
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_BUSINESS_ID"]

    media = graph_api.get_media_list(ig_user_id, token, limit=50)
    media.sort(key=lambda m: m.get("timestamp", ""))

    for m in media:
        print(json.dumps({
            "id": m["id"],
            "timestamp": m.get("timestamp"),
            "media_type": m.get("media_type"),
            "media_product_type": m.get("media_product_type"),
            "like_count": m.get("like_count"),
            "comments_count": m.get("comments_count"),
            "permalink": m.get("permalink"),
            "caption": (m.get("caption") or "")[:200],
        }))
    print(f"\n{len(media)} total posts retrieved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
