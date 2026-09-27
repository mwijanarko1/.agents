# Motion B-roll playbook

Word-timed motion-graphic clips for a creator talking-head. Each clip is **one shape that never cuts**: it morphs size, corners, and colour while content swaps; a cursor drives clicks and drags; every change lands on a spoken word.

Runtime: HyperFrames HTML + one paused GSAP timeline per clip (`hyperframes-core`). Prefer animation blueprints `cursor-ui-demo`, `panel-edit-live-sync`, `dataviz-countup`, `titlecard-reveal` when they fit. Do not install a second motion engine.

Work in `motion/` under the user's project (or a named workdir they choose).

## Defaults

| Field | Default |
| --- | --- |
| Density | Medium: 4-7 clips per minute |
| Look | Warm gray canvas `#E9E7E2`, ink `#0B0B0B`, white components, one accent (brand overrides) |
| Motion | Springs, tiny overshoot max. No bouncy template motion, particles, chrome glows, mixed icon strokes |
| Pace | One change per spoken beat, about 0.4-1.2s apart |
| Output | Editor-ready clips + `TIMING.md` + `plan.json`. Preview composite optional |

## Workflow

```
- [ ] 1. Interview (one round)
- [ ] 2. Inspect footage + word timings
- [ ] 3. Plan table; wait for approval
- [ ] 4. Build one HyperFrames clip per row
- [ ] 5. Stills on key words; fix
- [ ] 6. Render clips; write delivery pack
```

### 1. Interview

Need only what is missing:

- **Video** path (copy or ref as `motion/work/source.*`).
- **Transcript** with timestamps (SRT/VTT best). Plain text only: get word timings via `/media-use` transcribe / faster-whisper, or ask for SRT.
- **Density:** light 2-4 / medium 4-7 / heavy (most lines, short face gaps) clips per minute.
- **Look:** default palette, or brand colours/font/logo dropped in `motion/inputs/`.
- **Avoid / include:** lines to leave on face; real numbers to show; screenshots to recreate.

### 2. Inspect

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,duration -of json motion/work/source.*
# word list (SRT/VTT or media-use transcript with timings)
# optional: n evenly spaced frames for layout read
npx hyperframes snapshot   # only if source is already a HF project; else ffmpeg stills
ffmpeg -y -i motion/work/source.* -vf "fps=1/5,scale=480:-1" motion/work/contact-%03d.jpg
python3 ~/.agents/scripts/contact-sheet.py motion/work/contact.jpg motion/work/contact-*.jpg --columns 4
```

Write `motion/work/video.json` with at least: width, height, fps, duration, and layout sections:

- **full:** speaker fills the frame.
- **pip:** speaker in a box; note box approx position/size. Warn if the box moves or resizes across the piece.

Clips must match source resolution and fps. SRT word times are estimates (±0.2s).

### 3. Plan (required before code)

Show one table row per clip:

| # | In-Out | Line | Shape does X on words Y | Treatment | Why |

**Treatment (most important call, per clip):**

| Treatment | When | Notes |
| --- | --- | --- |
| **Full-frame cutaway** | Line describes something to *see* (product, process, compare, number, chapter) and speaker is full-frame | 3-10s idea length, then face back. No cutaway in the first second of the hook, or on personal/emotional/opinion lines. Leave ≥ ~2s of face between cutaways. |
| **Transparent panel** | Edit already leaves empty space (PiP, split, plain region) | `bg` transparent / alpha export. Centre in empty area; clear of speaker box at every moment. May run long (15s+) as one continuous morph. If PiP box moves, size for largest box or split the clip at the change. |
| **Nothing** | Line is about the speaker, or too close to another clip | Leave face. |

**Content rules:**

- One idea per clip. A whole PiP section can be one long clip with several states.
- Map speech onto `interaction-vocab.md` patterns.
- Show the subject's real objects (folder, terminal, file, product). Pull from the words.
- **Never invent numbers, quotes, prices, or results.** Relative bars, skeleton lines, or transcript labels only. List what is illustrative. Real figures only when the user supplies them.
- Put each state change on a word. Prefer first/last word of a cue when SRT drift matters.

Wait for approve/edit (collaborative). Autonomous: post the table as heads-up and continue only if the brief said so.

Save approved plan as `motion/plan.json` (`plan-schema.md`).

### 4. Build

One composition per clip under `motion/clips/NN-name/` or `motion/clips/NN-name.html`:

- Root size = source width x height. `data-duration` = clip length (out - in).
- **One continuous shape** (single morphing container). No hard cuts inside the clip.
- States = GSAP timeline tweens on size, radius, fill; content layers enter/exit with short blur/fade (`autoAlpha` + filter blur ok on non-clip chrome per core rules).
- Clip-local time: `t = wordTime - inPoint`.
- Cursor: optional visible cursor path with click/drag keyframes (`cursor-ui-demo` patterns).
- Full cutaway: opaque canvas bg. Panel: transparent stage; light shapes on dark footage.
- Brand overrides default palette.

```bash
# if multi-file HF project per clip:
npx hyperframes check -c motion/clips/NN-name
```

### 5. Stills on key words

For each clip, snapshot times where each state has settled, plus 1-2 mid-morph moments:

```bash
npx hyperframes snapshot -c motion/clips/NN-name --at <t1,t2,...> --no-end -o motion/work/NN-stills
python3 ~/.agents/scripts/contact-sheet.py motion/work/NN.jpg motion/work/NN-stills/*.png --columns 3
```

Read every sheet. Fix cramped, clipped, unreadable, off-word, or cursor-out-of-frame issues. Panel stills on a dark checker/black so alpha reads. Re-check once after fixes.

### 6. Render + deliver

```bash
npx hyperframes render -c motion/clips/NN-name -o motion/out/NN-name_<inTag>.mp4
# panels needing alpha: --format webm (or documented ProRes path if available)
```

Name files by timeline in-point: `0m32s40` = 0:32.40.

Write:

- `motion/plan.json` (final paths)
- `motion/out/TIMING.md` from `plan-schema.md`
- Delivery note: what is illustrative; density used; treatments summary

Optional preview (nice, not required for handoff):

- Composite clips onto source with hard cuts at in/out (`ffmpeg` overlay / concat per plan). Say plainly: preview is for review; final cut is the creator's editor.

Optional pages: simple `viewer.html` (step clips) and `compare.html` (source vs preview) if time allows; do not block delivery on them.

Versioned handoff copy when the user wants Downloads:

`~/Downloads/<title>-broll-vN/` with clips + `TIMING.md` + `plan.json`. Never overwrite prior `vN`.

## Style bans

Bouncy cartoon easing, particles, glows on UI chrome, gradients on chrome, mixed icon stroke weights, dead time, template-kit look, made-up data.

## Gotchas

- Text swap inside a morphing container needs its own enter/exit timing or old/new overlap.
- Cursor must stay in frame under camera/scale moves.
- Hold last state to clip end; composite may hold last frame if slot is longer than media.
- Match source fps on render.
