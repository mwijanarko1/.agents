# Social ad 15s playbook

Build a sound-off feed ad as a HyperFrames composition: one paused GSAP timeline, short headlines legible muted, then stills review, then H.264 MP4.

Pair with `claim-and-asset-honesty.md` (same folder) on every run. Technical contract: `hyperframes-core`. Motion: `hyperframes-animation` blueprints/rules as needed. Do not invent a separate runtime.

## Defaults

| Field | Default | Notes |
| --- | --- | --- |
| Duration | 15s | Root `data-duration="15"` |
| Aspect | 4:5 (1080x1350) | Stories/reels: 9:16 (1080x1920) |
| Audio | None (sound-off) | No VO, no BGM unless the user asks |
| Beats | 4-5 | One short headline per beat |
| Headline size | Large, muted-legible | About <= 20 chars per line at display size |

## Beat grid (start here, cut what does not fit)

| Time | Beat | Job | Typical fields |
| --- | --- | --- | --- |
| 0-2.2s | Hook | Stop the scroll. Product in use or bold outcome line. | `hook`, optional device/screen, tap |
| 2.2-5.4s | Reveal | Transformation: before to after, messy input to finished output. | `before`, `after`, labels, `benefits` |
| 5.5-8.7s | Scale | Many outputs / gallery / wall of results. | `gallery`, scale chip |
| 8.7-11.8s | Showcase + proof | 2-3 concrete cards. Real proof only, or omit. | `showcase`, `proof` (or null) |
| 11.8-15s | CTA end card | Brand color wipe, logo, CTA, optional foot line. | `cta.headline`, `cta.chip`, `cta.button`, `cta.foot` |

If a beat does not fit the product, cut or replace it in the timeline. Example: no phone step for a desktop tool. Start on the hero card. Do not force the full five beats into noise. Sometimes hook + one feature + CTA is correct for 15s (`beat-direction.md`).

## CONFIG (single content object)

Keep all brand and product content in one object at the top of the composition script (or a small `ad-config.js` the HTML loads). Rewrite fields; do not rebuild structure from zero each time.

```js
const CONFIG = {
  brand: "",
  logo: "assets/logo.png",       // light-bg version
  logoOnDark: "assets/logo-w.png",
  colors: { primary: "", accent: "", page: "#0a0a0a", ink: "#fff" },
  hook: "Line one\\n*accent words*",
  before: "assets/before.jpg",
  after: "assets/after.jpg",
  beforeLabel: "Before",
  afterLabel: "After",
  benefits: ["Fast", "Clear", "Yours"],
  gallery: ["assets/g1.jpg", "assets/g2.jpg", "assets/g3.jpg"],
  showcase: [
    { img: "assets/s1.jpg", title: "Card one", inset: null },
    { img: "assets/s2.jpg", title: "Card two", inset: "assets/s2-before.jpg" },
  ],
  proof: null, // or { hl: "4.9", sub: "from real reviews on the site" }
  cta: {
    headline: "Try *Brand*",
    chip: "Free to start",
    button: "Get started",
    foot: "",
  },
};
```

Headline markup: `*words*` = accent color; `\n` = line break. Image paths relative to the composition HTML.

## Workflow

```
- [ ] 1. Research product + destination page
- [ ] 2. Set up project + gather assets
- [ ] 3. Storyboard + copy (4-5 beats, muted)
- [ ] 4. Build composition from CONFIG + beat grid
- [ ] 5. Stills contact sheet, review, fix
- [ ] 6. Full MP4, spot-check, versioned deliver
```

### 1. Research

- Product, destination URL, audience, format (4:5 default; 9:16 for stories/reels).
- Fetch destination + homepage/pricing for facts: promise, prices, ratings, speed, free vs paid.
- Brand: colors, font, logo from site CSS/design system, capture, or user files.
- Apply `claim-and-asset-honesty.md` before writing any copy.

### 2. Project + assets

```bash
npx hyperframes init <project-dir>   # if no project yet
# capture when a live URL exists:
npx hyperframes capture <destination-url> -o ./capture
```

Stage logo(s) and hero before/after into `assets/`. Prefer user files over scraped thumbs. Portrait (~4:5) images fill hero and showcase cards best. For SaaS, messy input to finished output screenshots beat stock photos.

### 3. Storyboard

One short headline per beat. Sound-off: if you cannot read it muted at thumbnail size, rewrite. Present as a compact beat table (time, beat, on screen, copy). Skip narration/SCRIPT.md unless the user asks for sound-on.

### 4. Build

- Root size 1080x1350 (or 1080x1920). `data-duration="15"`.
- One paused timeline. Seek-safe. No `Math.random` / open-ended repeats.
- Fill CONFIG; wire beats to the grid; cut unused beats.
- For 9:16, re-space vertical positions (headlines, hero, carousel, end card).
- Cite animation blueprints/rules when a beat needs a named move (`device-surface-showcase`, `cta-morph-press`, `titlecard-reveal`, etc.).

### 5. Stills review (required before full render)

Capture fixed beat timestamps, then one contact sheet. Batch visual checks; do not attach N single frames mid-build.

```bash
npx hyperframes snapshot --at 0.3,1.9,2.7,3.8,4.9,6.6,9.8,11.5,13.6 --no-end -o ./stills
python3 ~/.agents/scripts/contact-sheet.py ./stills.jpg ./stills/*.png --columns 3 --cell 360x450
```

Read `stills.jpg`. Check: text overlap, empty gaps, leftover placeholders, labels that contradict the image, duplicate gallery tiles, legibility at thumbnail size. Fix, then re-sheet only if structure changed.

### 6. Render + deliver

```bash
npx hyperframes check
npx hyperframes render --output ./ad-4x5.mp4
ffprobe -v error -show_entries format=duration:stream=width,height,nb_frames -of csv=p=0 ./ad-4x5.mp4
```

Versioned delivery. Never overwrite an earlier version:

```bash
# pick next free vN
dest="$HOME/Downloads/<brand>-<topic>-ad-4x5-vN.mp4"
cp ./ad-4x5.mp4 "$dest"
```

For 9:16 use `-ad-9x16-vN.mp4`. Spot-check one transition frame if a handoff looked soft on the sheet. Report path, beat-by-beat copy, and honesty caveats (`claim-and-asset-honesty.md`).

## Review shape

- Default autonomous-leaning: short project, no VO. At most one clarifying question up front if product or URL is missing.
- Still run the stills gate before full render.
- Collaborative final look only when the user asked to review before export; otherwise stills sheet + render is enough after stills pass.

## Boundaries

- Not a logo sting or single stat hit: `/motion-graphics`.
- Not a 30-90s narrated launch film: `/product-launch-video`.
- Not a transparent lower-third overlay: `/motion-graphics`.
