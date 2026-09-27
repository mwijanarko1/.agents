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

3. **Vision-read** each page image with the image-capable `read` tool. Transcribe only visible table values. Quote the PNG path. Do not pass the file to tesseract as an unquoted glob; tesseract can treat a PNG signature as a filename. Prefer the vision read tool over tesseract when the image is already on disk.
4. **Map columns** → monthly JSON fields (`fajr`, `shurooq`, `dhuhr`, `asr`, optional `asr_mithl2`, `maghrib`, `isha` + `iqamah_times`). Dual Asr: Mithl1 → `asr`, Mithl2 → `asr_mithl2`.

Months from the same publisher are not a stable schema. Match day names case-insensitively (`Tue` vs `TUE`). Strip `*` affixes on dates (`*16`, `16*`). Resolve Maghrib/Isha jamaat by min/max of the last two clock times when column order flips (Maghrib 4th vs last). Do not pin a positional parser across months.
5. **Write** month files; partial years are valid. Do not invent missing days — flag gaps. `isHidden: false` unless data is placeholder/unverifiable.
6. **Verify** day counts, time order (fajr < sunrise < dhuhr < asr < maghrib < isha), and sample against the page image.

## Pairing

- Structured API/HTML extraction → `extract-mosque-prayer-times`.
- Seeding Convex/prod → that skill's confirmed seed steps (explicit confirmation for prod).
