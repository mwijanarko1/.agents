---
name: instagram-osint
description: "Logged-out Instagram OSINT: profile metadata, comment enumeration by handle, comment/date verification. Use when asked what an Instagram account commented on, who a handle is, or whether two accounts interacted. Different from pinchtab because this is HTTP-only and needs no browser or login."
---

# Instagram OSINT (logged out)

Goal: find every public comment by a handle, plus profile metadata, with no login.

## Hard limits, state these before searching

- **Likes are not enumerable.** Instagram removed the Following activity tab in Oct 2019, and there is no per-user likes feed. Sites claiming to show someone's likes are scams. Only checkable question: does `<handle>` appear in the liker list of one specific post. That needs a logged-in session, and fails if the owner hid like counts. One live exception: if you follow the account, Reels it liked or commented on can surface in your own Friends tab (visibility controlled per account under Settings, Friends).
- **Private profiles** expose nothing beyond display name, counts, and bio.
- **Mirrors are dead:** `imginn.com`, `dumpor.io`, `picnob.com` return `bot_blocked`; `imginn.io` returns `page_not_found`. Firecrawl on instagram.com returns 403. `i.instagram.com/api/v1/users/web_profile_info/` returns 401.
- **Logged-out post pages hide roughly half the comments** and sometimes omit commenter usernames entirely.
- Photo tags never render in logged-out text, so a tag cannot be confirmed or ruled out this way.

## Step 1: profile metadata

```bash
UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
curl -sL -A "$UA" "https://www.instagram.com/<handle>/" -o /tmp/ig.html
grep -o 'og:title" content="[^"]*' /tmp/ig.html
grep -o 'og:description" content="[^"]*' /tmp/ig.html
```

`og:description` carries followers, following, posts, and the bio. Private profiles render "This profile is private" with no post data.

## Step 2: enumerate comments by handle

Search engines index Instagram comment text. The exact-quote plus site-restricted query is the only reliable enumeration method found; phrase-only queries ("mashallah", "thank you") return noise.

```bash
tinyfish search query '"<handle>" site:instagram.com/p' --pretty
tinyfish search query '"<handle>" site:instagram.com reel' --pretty
tinyfish search query '"<handle>" instagram comment' --pretty
```

Also worth running: `"<handle>" "<likely phrase from an already-found comment>"` and `"<handle>" "<probable city or organisation>"`. Both surfaced hits the plain queries missed.

Expect saturation. Once three variants return the same post list, stop. For a private handle with a few hundred following, the index is the ceiling.

## Step 3: fetch each hit and verify

Batch all hits into one call, then parse:

```bash
tinyfish fetch content get "https://www.instagram.com/p/<id1>/" "https://www.instagram.com/p/<id2>/" > /tmp/posts.json
```

```python
import json
for r in json.load(open('/tmp/posts.json'))['results']:
    t = r.get('text', '')
    print(r['url'], 'HIT' if '<handle>' in t else 'miss', len(t))
```

A hit is only confirmed when the handle appears in the rendered comment list with its text, like count, and relative age. Report the exact comment string, not a paraphrase.

Get the absolute date and the owning account from the raw page, since the fetched text often omits them:

```bash
curl -sL -A "$UA" "https://www.instagram.com/p/<id>/" -o /tmp/p.html
grep -o 'og:url" content="[^"]*' /tmp/p.html
grep -o 'og:description" content="[^"]*' /tmp/p.html
```

`og:url` gives the owning handle, `og:description` gives "N likes, M comments - <handle> on <date>".

## Step 4: report

One table: target account, post link, absolute date, exact comment text, likes. Add a line for the search method used and the ceiling hit, so the next run does not repeat dead ends.

Convert relative ages to absolute: weeks / 52 = years (199 weeks = 3 years 10 months).

## Gotchas

- Use the singular `/reel/<id>/` URL. The `/reels/` plural form redirects wrong and `/embed/captioned/` is broken.
- TinyFish Search and Fetch Content only. Agent and Browser are paid.
- Comment text on one post can differ slightly between the index snippet and the live page. Trust the live page.
