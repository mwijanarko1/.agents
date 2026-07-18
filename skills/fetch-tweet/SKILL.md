---
name: fetch-tweet
description: Fetch tweet content and metadata from an X/Twitter URL.
argument-hint: "[tweet-url]"
license: MIT
metadata:
  author: OpusGameLabs
  version: "1.3.0"
  tags: [twitter, tweet, fetch, fxtwitter, social-media]
---

# Fetch Tweet

Use the fxtwitter API (JSON, no JS render, no X auth).

## URL map

| Input | API |
|-------|-----|
| `https://x.com/<user>/status/<id>` | `https://api.fxtwitter.com/<user>/status/<id>` |
| `https://twitter.com/...` / `fxtwitter.com/...` / `vxtwitter.com/...` | same API host |

## Fetch

```bash
curl -sS -fS "https://api.fxtwitter.com/<user>/status/<id>"
```

On non-2xx: report status and stop. Do not scrape `x.com` HTML as a substitute.

## Return

Author name/handle, text, date, media URLs, likes, retweets, replies, views (when present). Quote/retweet: include nested tweet summary when the payload has it.

## Notes

Reasonable use only; no bulk scraping loops unless the user explicitly owns that need.
