# One-time setup

Do these once before the automation can run. None of these credentials
should ever be pasted into a chat — put them straight into GitHub repo
secrets as described below.

## 1. Confirm the Instagram account type

@rgvm8 needs to be a Professional (Business or Creator) account linked to
a Facebook Page. Check: Instagram app → Settings → Account type and tools.
If it's not linked to a Page yet, do that first (Settings → linked
accounts).

## 2. Create a Meta App

1. Go to https://developers.facebook.com/apps → Create App → type
   "Business".
2. Add the **Instagram Graph API** product to the app.
3. In Business Settings for the Meta Business Portfolio that owns the
   Facebook Page, create a **System User** (Business Settings → Users →
   System Users → Add). System User tokens don't expire every 60 days
   like personal tokens do, which matters for unattended cron jobs.
4. Assign the System User access to the Facebook Page (and therefore the
   linked Instagram account) with these permissions/scopes:
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_comments`
   - `instagram_manage_insights`
   - `pages_show_list`
   - `pages_read_engagement`
5. Generate a token for the System User with those permissions
   (Business Settings → System Users → select user → Generate New Token
   → pick the app and the permissions above). Copy it somewhere safe
   temporarily — you'll paste it into a GitHub secret, not here.

## 3. Find your Instagram Business Account ID

With the token from step 2:

```
curl "https://graph.facebook.com/v21.0/me/accounts?access_token=YOUR_TOKEN"
```

Find your Page in the result, grab its `id`, then:

```
curl "https://graph.facebook.com/v21.0/YOUR_PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
```

The `instagram_business_account.id` in the response is `IG_BUSINESS_ID`.

## 4. Add GitHub repo secrets

Repo → Settings → Secrets and variables → Actions → New repository secret:

- `IG_ACCESS_TOKEN` — the System User token from step 2
- `IG_BUSINESS_ID` — the ID from step 3

## 5. Add a repo variable for the Pages URL

Same Settings page, "Variables" tab → New repository variable:

- `PAGES_BASE_URL` = `https://apasil03.github.io/rgvm8` (adjust if you
  rename the repo)

## 6. Enable GitHub Pages

Repo → Settings → Pages → Build and deployment → Source: **GitHub
Actions**. That's a one-time click — after that, `daily-post.yml` deploys
Pages itself as part of each daily run (before it calls the Graph API,
so the image is guaranteed live first). If you want to preview an image
you just added without waiting for the next scheduled run, trigger
`publish-pages.yml` manually from the Actions tab.

Note: this makes the contents of this repo reachable at the Pages URL
(not indexed/searchable, but not secret either). Don't put anything in
the repo you don't want publicly fetchable — secrets belong in GitHub
Secrets, never in files.

## 7. Add content and go

- Drop images into `assets/pending/`, commit and push (this triggers the
  Pages publish).
- Add a matching row to `content/queue.csv` with the real product name,
  factual key points, and your actual affiliate link for that brand.
- The `daily-post` workflow runs once a day and publishes the oldest
  pending row that's due. You can also trigger it manually from the
  Actions tab ("Run workflow") to test before waiting for the schedule.
- The `reply-comments` workflow runs every 30 minutes and auto-replies to
  compliments and "where do I buy" questions. Anything about fitment or
  unclear gets logged to `content/needs_review.json` for you to answer
  by hand.

## Token expiry

If you used a personal/short-lived token instead of a System User token,
it will expire (~60 days) and the workflows will start failing with an
auth error. Re-generate and update the `IG_ACCESS_TOKEN` secret when that
happens, or switch to a System User token to avoid this entirely.
