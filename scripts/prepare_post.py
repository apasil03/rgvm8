#!/usr/bin/env python3
"""Pick the next postable queue row and make sure its image exists on disk
(generating a branded card if no real photo was supplied). Does NOT call
the Instagram API and does NOT mark anything posted — that happens in
publish_post.py, after this row's image has actually been deployed to
GitHub Pages. Writes the winning row id to GITHUB_OUTPUT as `row_id`
(empty if nothing is due/postable).
"""
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import queue  # noqa: E402
from generate_reel import generate_reel  # noqa: E402


def resolve_media_filename(row: dict) -> str:
    """Real media (photo or video) you've added always wins. Otherwise
    generate a Reel — it gets far more reach than a static card, and we
    can produce it locally just as easily."""
    candidate = queue.PENDING_DIR / row["image_path"]
    if candidate.is_file():
        return row["image_path"]

    generated_name = f"{row['id']}-reel.mp4"
    generate_reel(
        brand=row["brand"],
        product_name=row["product_name"],
        key_points=row["key_points"],
        output_path=str(queue.PENDING_DIR / generated_name),
        post_type=row.get("post_type", "affiliate"),
    )
    print(f"No real media found for row {row['id']} ({row['image_path']}); generated {generated_name} instead.")
    return generated_name


def set_output(name: str, value: str) -> None:
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"{name}={value}\n")
    else:
        print(f"{name}={value}")


def main() -> int:
    rows = queue.read_queue()
    today = dt.date.today().isoformat()
    due = queue.due_rows(rows, today)

    def is_blocked(r: dict) -> bool:
        # engagement rows carry no affiliate link by design; only affiliate
        # rows need a real, confirmed link before they can go out.
        return r.get("post_type", "affiliate") == "affiliate" and (
            not r["affiliate_link"] or r["affiliate_link"].startswith("TODO")
        )

    blocked = [r for r in due if is_blocked(r)]
    for r in blocked:
        print(f"Skipping row {r['id']} ({r['brand']}): affiliate_link is still a TODO placeholder.")
    postable = [r for r in due if not is_blocked(r)]

    if not postable:
        print("No postable rows due today.")
        set_output("row_id", "")
        return 0

    row = postable[0]
    row["image_path"] = resolve_media_filename(row)
    queue.write_queue(rows)

    print(f"Prepared row {row['id']} ({row['brand']} - {row['product_name']}) with media {row['image_path']}")
    set_output("row_id", row["id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
