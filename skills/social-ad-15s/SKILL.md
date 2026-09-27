---
name: social-ad-15s
description: >
  Build a ~15s sound-off social/feed product ad (Meta, Instagram, TikTok) as a HyperFrames MP4.
  Use when the user asks for a facebook ad, instagram ad, tiktok ad, feed ad, motion ad, muted promo,
  or 15s product ad. Different from hyperframes product-launch-video (30-90s narrated) and
  motion-graphics (single short unit) because this is a multi-beat muted feed ad with fixed stills
  gate and claim honesty.
---

# Social ad 15s

Local HyperFrames playbook (not a published `hyperframes skills` workflow).

## Load

1. `/hyperframes` for routing if not already selected as `/social-ad-15s`.
2. This skill's references (canonical):
   - `references/social-ad-15s.md` (beats, CONFIG, stills, delivery)
   - `references/claim-and-asset-honesty.md` (destination-page claims, real assets only)
3. Domain skills as needed: `/hyperframes-core`, `/hyperframes-creative`, `/hyperframes-animation`, `/hyperframes-cli`, `/media-use`.

## Do not

- Run `npx hyperframes skills update social-ad-15s` (package does not exist).
- Ship fabricated proof, people, or claims absent from the destination page / user materials.
- Skip the stills contact-sheet gate before full render.
- Overwrite a previous `~/Downloads/<brand>-<topic>-ad-*-vN.mp4`.

## Verify

- `npx hyperframes check` passes.
- Stills sheet reviewed at playbook timestamps.
- `ffprobe` duration ~15s; size matches 4:5 or 9:16.
- Delivery note lists path, beat copy, honesty caveats.
