---
name: motion-broll
description: >
  Turn talking-head video plus transcript into word-timed motion-graphic B-roll
  (continuous one-shape morphs, cursor-driven UI, full cutaways or transparent
  PiP panels) as HyperFrames clips for the editor. Use when the user gives
  footage and wants motion graphics, animated B-roll, cutaways, or overlays
  timed to speech. Different from talking-head-recut (generic overlay cards),
  embedded-captions (captions only), motion-graphics (standalone short unit),
  and social-ad-15s (muted product feed ad).
---

# Motion B-roll

Local HyperFrames playbook (not a published `hyperframes skills` workflow).
Substrate is HyperFrames + GSAP, not a second motion engine.

## Load

1. `/hyperframes` if not already routed as `/motion-broll`.
2. This skill:
   - `references/playbook.md` (inspect, plan, build, stills, deliver)
   - `references/interaction-vocab.md` (speech to UI patterns)
   - `references/plan-schema.md` (`plan.json`, `TIMING.md`)
3. Domain skills as needed: `/hyperframes-core`, `/hyperframes-animation` (esp. `cursor-ui-demo`, `panel-edit-live-sync`, `dataviz-countup`), `/hyperframes-cli`, `/media-use` (transcript / word timings).
4. Honesty: `~/.agents/skills/social-ad-15s/references/claim-and-asset-honesty.md` plus the B-roll data rules in the playbook.

## Do not

- Run `npx hyperframes skills update motion-broll` (package does not exist).
- Port or depend on Barty-Bart `motion.js` as a parallel runtime.
- Invent numbers, quotes, prices, or results. Relative bars and skeleton text only until the user supplies figures.
- Skip plan approval before writing clip HTML.
- Skip stills-on-key-words before full render.
- Hard-cut inside a clip. One continuous shape morph per clip.

## Verify

- Plan table approved (or autonomous heads-up posted).
- Each clip: one shape, word-timed state changes, stills sheet clean.
- `npx hyperframes check` on compositions that are full HyperFrames projects.
- Delivery pack: clips, `TIMING.md`, `plan.json`, optional preview note.
- Illustrative data listed in the delivery note.
