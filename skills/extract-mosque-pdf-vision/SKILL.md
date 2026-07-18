---
name: extract-mosque-pdf-vision
description: "Extract mosque prayer timetable JSON files from a user-provided PDF using a vision model. Use when the source is a PDF/image timetable and the user wants vision extraction instead of pdftotext/OCR."
argument-hint: "[pdf-path] [citySlug/mosque-slug]"
---

# Extract Mosque PDF Timetable (Vision)

Vision-read mosque timetable PDFs/images into project JSON. **No astronomical calculation, no OCR-only guessing, no invented times.**

## Workflow

1. **Target folder** — `public/data/mosques/gb/{citySlug}/{mosque-slug}/` (match existing shape / `jummah_iqamah`).
2. **Rasterize** (skip if already images):

```bash
mkdir -p tmp/pdf_vision_pages
pdftoppm -png -r 180 "<pdf-path>" tmp/pdf_vision_pages/page
# bump -r 240/300 if unreadable
```

For remote images, download with `curl` to a temp path, then vision-read.

3. **Vision-read** each page image with the image-capable `read` tool. Transcribe only visible table values.
4. **Map columns** → monthly JSON fields (`fajr`, `shurooq`, `dhuhr`, `asr`, optional `asr_mithl2`, `maghrib`, `isha` + `iqamah_times`). Dual Asr: Mithl1 → `asr`, Mithl2 → `asr_mithl2`.
5. **Write** month files; do not invent missing days — flag gaps.
6. **Verify** day counts, time order (fajr < sunrise < dhuhr < asr < maghrib < isha), and sample against the page image.

## Pairing

- Structured API/HTML year extraction → `extract-mosque-prayer-times`.
- Seeding Convex/prod → that skill's confirmed seed steps (explicit confirmation for prod).
