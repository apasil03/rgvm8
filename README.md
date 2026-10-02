# rgvm8 — Instagram automation

Automation for the @rgvm8 Instagram account: daily posting of car parts
content (RW Carbon, ECS Tuning, RCW Performance, Bimmer Plug, ARM
Motorsports, AutoTecknic) with tracked commission links, plus automatic
replies to comments on our own posts.

## What this does

- **Daily posting** (`scripts/prepare_post.py` + `scripts/publish_post.py`,
  run by `.github/workflows/daily-post.yml`): picks the next pending row
  from `content/queue.csv`, generates a branded graphic card locally if no
  real photo was supplied (`scripts/generate_card.py` — no internet
  needed), deploys it to GitHub Pages, then builds a caption in the brand
  voice (`content/brand_voice.md`), publishes it via the Instagram Graph
  API, and marks the row posted. Real photos in `assets/pending/` always
  take priority over the generated card.
- **Comment replies** (`scripts/reply_comments.py`, run by
  `.github/workflows/reply-comments.yml`): scans comments on our recent
  posts and auto-replies to safe categories (thanks/compliments,
  "where do I buy this"). Anything about fitment/compatibility or that
  doesn't match a known pattern is logged to `content/needs_review.json`
  for a human to answer — the bot never guesses whether a part fits
  someone's specific car.
- **Image hosting**: the Graph API needs a public URL for each image, so
  `assets/` is published via GitHub Pages (see `docs/SETUP.md`).

## What this deliberately does NOT do

No auto-commenting on other accounts' posts, no auto-following/unfollowing,
no engagement-pod/bot-network tactics. That's against Instagram's platform
policy and risks the account getting throttled or banned. Growth here comes
from consistent real content + fast, genuine replies — not spam.

## Setup

See `docs/SETUP.md` — you'll need a Meta Developer App, an Instagram
access token (as a GitHub secret, never committed to this repo), and to
enable GitHub Pages once.

## Adding content

Add a row to `content/queue.csv` and drop the matching image in
`assets/pending/`. See the comments at the top of that file for the
column format. Fill in real product details — the caption generator
doesn't invent specs, prices, or fitment claims.
