# Plan schema and TIMING.md

## plan.json

Paths relative to `motion/plan.json`.

```json
{
  "title": "Project title",
  "video": "work/source.mp4",
  "fps": "30/1",
  "width": 1920,
  "height": 1080,
  "density": "medium",
  "clips": [
    {
      "id": "01",
      "title": "Short clip title",
      "line": "Transcript line this covers...",
      "in": 0.3,
      "out": 6.75,
      "kind": "full",
      "file": "out/01-name_0m00s30.mp4",
      "words": [
        { "t": 0.15, "word": "shipped", "action": "pill->card" },
        { "t": 2.4, "word": "folder", "action": "open folder" }
      ]
    },
    {
      "id": "02",
      "title": "PiP panel build",
      "line": "...",
      "in": 6.75,
      "out": 22.5,
      "kind": "panel",
      "file": "out/02-name_0m06s75.webm"
    }
  ],
  "notes": [
    "Cost/time bars are illustrative (relative size only)."
  ]
}
```

| Field | Meaning |
| --- | --- |
| `kind` | `full` cutaway, `panel` transparent overlay, or omit skipped lines |
| `in` / `out` | Seconds on the source timeline |
| `file` | Rendered clip path; name includes in-tag `0m32s40` = 0:32.40 |
| `words` | Optional word anchors used while building |
| `notes` | Illustrative data and caveats |

`out` is when the clip leaves the timeline. If media is shorter, hold the last frame for the slot.

## In-point filename tag

```text
seconds = in
m = floor(seconds / 60)
s = seconds - m*60
tag = f"{m}m{int(s):02d}s{int(round((s%1)*100)):02d}"
# 32.40 -> 0m32s40
```

## TIMING.md

```markdown
# Timing - <title>

Source: `<video>` · fps `<fps>` · density `<density>`

| File | In | Out | Kind | Line | Notes |
| --- | --- | --- | --- | --- | --- |
| `01-name_0m00s30.mp4` | 0:00.30 | 0:06.75 | full | "..." | |
| `02-name_0m06s75.webm` | 0:06.75 | 0:22.50 | panel | "..." | alpha |

## Illustrative

- <list from plan.notes>

## Editor notes

Preview composites (if any) are for review only. Place clips on the source timeline at **In**; trim to **Out**. Nudge ±0.2s if SRT drift shows.
```

## Delivery checklist

- [ ] Every planned clip rendered to `motion/out/`
- [ ] `plan.json` paths match files on disk
- [ ] `TIMING.md` written
- [ ] Illustrative notes non-empty when any data was approximated
- [ ] User told preview ≠ final grade
