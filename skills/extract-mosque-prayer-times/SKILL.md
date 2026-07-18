---
name: extract-mosque-prayer-times
description: "Extract full-year structured prayer times (adhan + iqamah) from a mosque website and seed to Convex dev AND production databases. Sources: APIs/endpoints, CSV, and parseable HTML/DOM only — no PDF/image OCR and no computed/calculated times."
argument-hint: "[mosque-url]"
---

# Extract Mosque Prayer Times

Full-year adhan + iqamah into Sheffield-Masjids-style monthly JSON, then optional seed. **No astronomical calculation.** PDF/image sources → `extract-mosque-pdf-vision`.

## Hard rules

- **OK:** JSON/REST, CSV, published Google Sheets CSV, structured plugin data, parseable HTML tables/DOM.
- **Not OK:** computing times via formulas/libraries.
- If no usable source: report "Cannot extract" and stop.
- **Prod seed / registry mutation requires explicit confirmation.** Prefer dev seed + verification first.

## Output files

`public/data/mosques/gb/{country}/{city}/{mosque-slug}/{MONTH}.json` (12 months) plus registry entry in the project's `mosques.json` when adding a mosque.

Shape (per month):

```json
{
  "month": "JANUARY",
  "prayer_times": [{ "date": 1, "fajr": "06:26", "shurooq": "08:03", "dhuhr": "12:09", "asr": "13:46", "maghrib": "16:05", "isha": "17:42" }],
  "iqamah_times": [{ "date_range": "1", "fajr": "07:00", "dhuhr": "12:30", "asr": "14:00", "maghrib": "16:10", "isha": "18:00" }],
  "jummah_iqamah": ["13:15"]
}
```

Use 24h `HH:MM`. Preserve dual Asr as `asr` + `asr_mithl2` when the source has both.

## Workflow

1. Discover data source (network tab, published CSV, MasjidBox API key in page bundles, WP plugin endpoints).
2. Extract full year; do not invent gaps — flag missing days.
3. Write monthly JSON; update registry if new mosque.
4. Validate: day counts, ordering, sample vs source.
5. **Seed dev first** with the project's package script (e.g. `bun run seed` / `npm run seed` / `node …` — **not** ad-hoc `npx`). Check HTTP/CLI exit codes.
6. After dev verify + **explicit confirmation**, seed prod the same way.
7. Post-check: registry present, month files readable, seed command reported success for the slug.

## Common sources (pointers)

- **Google Sheets published CSV** — `docs.google.com/spreadsheets/d/e/{id}/pub?...&output=csv`
- **MasjidBox** — full-year via API in ≤7-day chunks with `apikey` header; parse local `HH:MM` from timestamps; iqamah + jumuah fields when present
- **WordPress DPT plugin** — look for `dpt_` / REST; may be blocked
- Prefer project README for seed script names and Convex env

## Failure handling

Non-2xx source/seed responses: stop, show status + short body, do not claim seeded. Never calculate fill-ins for missing days.
