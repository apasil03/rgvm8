#!/usr/bin/env python3
"""Reply to safe categories of comments on our own recent posts.

Fitment/compatibility questions and anything ambiguous are logged to
content/needs_review.json instead of being auto-replied to — see
content/brand_voice.md for why we never guess at fitment.

Requires env vars: IG_ACCESS_TOKEN, IG_BUSINESS_ID.
"""
import json
import os
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import graph_api  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "content" / "replied_state.json"
REVIEW_PATH = ROOT / "content" / "needs_review.json"
TEMPLATES_PATH = ROOT / "content" / "reply_templates.json"

COMPLIMENT_RE = re.compile(r"\b(clean|sick|fire|love|dope|nice|awesome|beautiful|sweet)\b", re.I)
BUY_RE = re.compile(r"\b(where.*(buy|get|find)|link|price|how much|cost)\b", re.I)
FITMENT_RE = re.compile(r"\b(fit|fits|fitment|compatible|compatibility|will.*work.*(on|with)|my \w+ \d{2,4})\b", re.I)
SPAM_RE = re.compile(r"(http|www\.|dm me|check my|follow me|f4f)", re.I)


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def classify(text: str) -> str:
    if SPAM_RE.search(text):
        return "spam"
    if FITMENT_RE.search(text):
        return "fitment"
    if BUY_RE.search(text):
        return "where_to_buy"
    if COMPLIMENT_RE.search(text):
        return "compliment"
    return "unclear"


def main() -> int:
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_BUSINESS_ID"]

    templates = json.loads(TEMPLATES_PATH.read_text())
    no_auto = set(templates.get("no_auto_reply_categories", []))
    replied_ids = set(load_json(STATE_PATH, []))
    needs_review = load_json(REVIEW_PATH, [])

    media_list = graph_api.get_recent_media(ig_user_id, token, limit=20)
    new_replies = 0

    for media in media_list:
        comments = graph_api.get_comments(media["id"], token)
        for comment in comments:
            cid = comment["id"]
            if cid in replied_ids:
                continue

            category = classify(comment.get("text", ""))
            replied_ids.add(cid)

            if category in no_auto or category == "spam":
                if category != "spam":
                    needs_review.append({
                        "comment_id": cid,
                        "media_id": media["id"],
                        "permalink": media.get("permalink"),
                        "username": comment.get("username"),
                        "text": comment.get("text"),
                        "category": category,
                    })
                continue

            options = templates.get(category, [])
            if not options:
                continue
            message = random.choice(options)
            graph_api.reply_to_comment(cid, message, token)
            new_replies += 1
            print(f"Replied to {cid} ({category}): {message}")

    save_json(STATE_PATH, sorted(replied_ids))
    save_json(REVIEW_PATH, needs_review)
    print(f"Done. {new_replies} auto-replies sent, {len(needs_review)} items awaiting human review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
