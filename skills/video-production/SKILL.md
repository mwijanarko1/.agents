---
name: video-production
description: AI video production routing for conversation-driven editing (video-use), Seedance 2.0 prompt engineering (seedance), and optional HyperFrames/Remotion animation slots. Use when editing real footage, generating AI video prompts, building motion graphics, or running script→edit→render workflows.
---

# Video Production

Parent skill. Load one subskill for the current task.

| Need | Load |
|---|---|
| Edit real footage — transcribe, cut, grade, overlays, subtitles, EDL | `video-use/SKILL.md` |
| Seedance 2.0 / 即梦 video prompts — cinematic camera, multimodal @refs | `seedance/SKILL.md` |
| Motion graphics / React-template video in a slot | HyperFrames or Remotion (see `video-use/SKILL.md` animation slots) |

Paths under this folder:

```text
~/.agents/skills/video-production/video-use/SKILL.md
~/.agents/skills/video-production/seedance/SKILL.md
```

## Toolchain (full pipeline)

Typical order when building from scratch:

1. **Script / brief** — user intent in plain language
2. **Seedance** — AI-generated B-roll or cinematic clips (prompts only; generation happens on 即梦)
3. **HyperFrames / Remotion** — programmatic motion graphics and template video (lazy-install per slot)
4. **video-use** — assemble, cut, grade, subtitle, and render final output from real + generated assets

## First-time setup

Read `references/install.md` before the first video-use session. Seedance is prompt-only — no install.

## Repo locations

- `video-use` runtime: `~/.agents/vendor/video-use` (symlinked as `video-use/` here)
- Session outputs always go in `<videos_dir>/edit/`, never inside the vendor repo
