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
from generate_reel import generate_reel, generate_reel_from_photo  # noqa: E402

PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png")


def resolve_media_filename(row: dict) -> str:
    """Real media you've added always wins over a generated card. Every
    post gets a music-backed Reel either way, though -- a static image
    can't carry audio on Instagram at all, so a real photo gets turned
    into a photo-backed Reel instead of posted as a plain static image."""
    candidate = queue.PENDING_DIR / row["image_path"]
    if candidate.is_file():
        if candidate.suffix.lower() not in PHOTO_EXTENSIONS:
            return row["image_path"]  # already a video -- use as-is

        reel_name = f"{row['id']}-photo-reel.mp4"
        reel_path = queue.PENDING_DIR / reel_name
        if not reel_path.is_file():
            generate_reel_from_photo(
                str(candidate), str(reel_path),
                brand=row["brand"], product_name=row["product_name"],
                post_type=row.get("post_type", "affiliate"),
            )
            print(f"Converted real photo {row['image_path']} into music-backed Reel {reel_name} for row {row['id']}.")
        return reel_name

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
        post_type = r.get("post_type", "affiliate")
        # engagement rows carry no affiliate link by design; only affiliate
        # rows need a real, confirmed link before they can go out.
        if post_type == "affiliate":
            return not r["affiliate_link"] or r["affiliate_link"].startswith("TODO")
        if post_type == "recycle":
            return not r.get("source_media_id")
        return False

    blocked = [r for r in due if is_blocked(r)]
    for r in blocked:
        print(f"Skipping row {r['id']} ({r['brand']}): affiliate_link is still a TODO placeholder.")
    postable = [r for r in due if not is_blocked(r)]

    if not postable:
        print("No postable rows due today.")
        set_output("row_id", "")
        return 0

    row = postable[0]
    if row.get("post_type") == "recycle":
        # Reuses the original post's own media live at publish time (via its
        # source_media_id) -- nothing to generate or stage here.
        print(f"Prepared row {row['id']} (recycle of {row['source_media_id']})")
    else:
        row["image_path"] = resolve_media_filename(row)
        queue.write_queue(rows)
        print(f"Prepared row {row['id']} ({row['brand']} - {row['product_name']}) with media {row['image_path']}")
    set_output("row_id", row["id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
