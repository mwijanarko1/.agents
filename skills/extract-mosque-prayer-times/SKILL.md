---
name: extract-mosque-prayer-times
description: "Extract structured prayer times (adhan + iqamah) from a mosque website via HTTP (JSON, CSV, HTML tables) and seed to Convex. PDF/image timetables → extract-mosque-pdf-vision. Partial years OK. No computed times."
argument-hint: "[mosque-url]"
---

# Extract Mosque Prayer Times

HTTP-path extraction: JSON, CSV, and parseable HTML/DOM into Sheffield-Masjids-style monthly JSON, then optional seed. **No astronomical calculation.**

**PDF or image timetables** → load **`extract-mosque-pdf-vision`** (do not use `pdftotext` or OCR here). If the only source is PDF/image and you are not running vision now, mark **`[VISION-DEFERRED]`** and move on.

## Hard rules

- **OK (this skill):** JSON/REST, CSV, published Google Sheets CSV, structured plugin data, parseable HTML tables/DOM.
- **Not OK:** computing times via formulas/libraries; `pdftotext`/OCR on PDFs/images (use vision skill).
- If no usable HTTP source: report "Cannot extract" or vision-defer.
- **Partial years are fine** — write only published months. Do not invent missing months.
- **`isHidden`:** `true` only for placeholder or unverifiable data — not for missing months.
- **Prod seed requires explicit confirmation.** Prefer dev seed + verification first.

## Output files

`public/data/mosques/{country}/{citySlug}/{mosque-slug}/{month}.json` plus registry entry in `mosques.json`.

```json
{
  "month": "JANUARY",
  "prayer_times": [{ "date": 1, "fajr": "06:26", "shurooq": "08:03", "dhuhr": "12:09", "asr": "13:46", "maghrib": "16:05", "isha": "17:42" }],
  "iqamah_times": [{ "date_range": "1", "fajr": "07:00", "dhuhr": "12:30", "asr": "14:00", "maghrib": "16:10", "isha": "18:00" }],
  "jummah_iqamah": "13:15"
}
```

Use 24h `HH:MM`. Preserve dual Asr as `asr` + `asr_mithl2` when the source has both.

## Workflow

1. Discover data source (network tab, published CSV, MasjidBox API key, WP plugin endpoints).
2. If source is PDF/image → **`extract-mosque-pdf-vision`** (or `[VISION-DEFERRED]`).
3. Extract every published month; do not invent gaps.
4. Write monthly JSON; update registry if new mosque.
5. Validate: day counts, ordering, sample vs source.
6. **Seed dev first** with the project seed script (see `AGENTS.md` — not ad-hoc `npx` unless user allows).
7. After dev verify + **explicit confirmation**, seed prod.
8. Post-check: registry present, month files readable, seed success for the slug.

## Common sources (pointers)

- **Google Sheets published CSV** — `docs.google.com/spreadsheets/d/e/{id}/pub?...&output=csv`
- **MasjidBox** — API in ≤7-day chunks with `apikey` header; parse local `HH:MM` from timestamps
- **AthanPlus** — `timing.athanplus.com/masjid/widgets/monthly?masjid_id=…&date={year}-{month}-01`
- **WordPress DPT** — `get_monthly_timetable`; may be blocked
- See `AGENTS.md` for seed commands and Convex env

## Source traps

Write a `.py` file and run it. Pi bash rejects python heredocs and nested quotes (`unterminated shell quote`).

- **Newham / Humera**: Sheets in `_next` chunk `455-*.js` `dataSources`; jamat vs `salahBeginning` are different sheets; bare 12h afternoon +12; use `2PACX` + `gid` TSV/CSV.
- **Witton DPT**: try `http://` if HTTPS fails; GET not POST; thead-only = no month data.
- **Brand Lane IC**: single-day embed only — vision-defer if PDF/image exists.
- **HTML tables**: `Tuesday, Sep 1, 2026` date cells; iqamah in nested `<span>`; Friday rows may omit dhuhr iqamah.
- **12h times**: never assume am/pm; afternoon without marker → +12.
- **Python regex**: always `re.findall(r'...')` with quotes.

`MONTH_NAME_TO_NUM` in `scripts/seed-convex.ts` must use `Array.from(MONTH_FILES.entries())`.

## Failure handling

Non-2xx source/seed responses: stop, show status + short body, do not claim seeded. Never calculate fill-ins for missing days or months.
