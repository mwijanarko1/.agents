---
name: extract-mosque-prayer-times
description: "Extract full-year structured prayer times (adhan + iqamah) from a mosque website and seed to Convex dev AND production databases. Data must come from pure API/endpoints only — no HTML scraping, no OCR, no computed/calculated times."
argument-hint: "[mosque-url]"
---

# Extract Mosque Prayer Times

Extract a full year of prayer times from a mosque's website and add it to the Sheffield-Masjids project.

## Hard Rules

- **Valid sources**: JSON APIs, REST endpoints, CSV exports, Google Sheets published CSVs, structured WordPress plugin data, **HTML tables and rendered DOM**
- **NOT acceptable**: OCR (images/PDFs/scanned timetables), or computing/calculating times yourself using any library, formula, or astronomical calculation.
- If the site does not expose a usable data source (neither structured API nor parseable HTML), state "Cannot extract" and move on.

## Required Output Format

### 1. Monthly JSON files

Create 12 files at: `public/data/mosques/gb/{country}/{city}/{mosque-slug}/{month}.json`

Each file has this structure:

```json
{
  "month": "JANUARY",
  "prayer_times": [
    {
      "date": 1,
      "fajr": "06:26",
      "shurooq": "08:03",
      "dhuhr": "12:09",
      "asr": "13:46",
      "maghrib": "16:05",
      "isha": "17:42"
    }
    // ... all days of month
  ],
  "iqamah_times": [
    {
      "date_range": "1",
      "fajr": "07:00",
      "dhuhr": "12:30",
      "asr": "14:00",
      "maghrib": "16:10",
      "isha": "18:00"
    }
    // ... one entry per day or date range
  ],
  "jummah_iqamah": "13:15"
}
```

**Rules:**
- `prayer_times[].date` is the day-of-month number (1-31)
- All times in **24-hour format** (`HH:mm`) — e.g., `"14:30"` not `"2:30 pm"`
- Sunrise column is `shurooq`
- Asr is Mithl 1 (standard Shafi'i/Maliki/Hanbali asr time)
- `iqamah_times[].date_range` can be a single day `"1"` or a range `"1-7"`
- If iqamah is the same as adhan, still include it explicitly
- If no iqamah data is available, set all iqamah fields to `""`
- `jummah_iqamah` is the Jumu'ah congregation start time in `HH:mm` (e.g. `"13:15"`). Set to `""` if not available.

### 2. Registry update

Add the mosque to `public/data/mosques.json`:

```json
{
  "id": "mosque-slug",
  "name": "Mosque Full Name",
  "address": "Full Address, City Postcode, Country",
  "lat": 51.1234,
  "lng": -0.1234,
  "slug": "mosque-slug",
  "citySlug": "city-name",
  "cityName": "City Name",
  "countryCode": "GB",
  "countryName": "United Kingdom",
  "isHidden": false,
  "website": "https://..."
}
```

**Rules:**
- `isHidden: true` if data is incomplete (e.g. only partial year available, or placeholder data)
- `isHidden: false` only for complete, verified data
- `id` and `slug` must match and use kebab-case
- `citySlug` / `cityName` / `countryCode` / `countryName` are required for non-Sheffield mosques (Sheffield mosques with no city slug default to Sheffield)

### 3. Seed both databases

After creating files and updating the registry, seed:

```bash
# Dev
npx tsx scripts/seed-convex.ts --changed

# Production  
npx tsx scripts/seed-convex.ts --changed --prod
```

`--changed` seeds only files that differ from the last git commit — this avoids re-seeding unchanged mosques.

## Workflow

### Step 1: Investigate the website

1. Fetch the homepage and prayer times page
2. Identify the data source mechanism:
   - **Google Sheets published CSV** — look for URLs like `https://docs.google.com/spreadsheets/d/e/{id}/pub?gid={gid}&single=true&output=csv`
   - **WordPress plugin** — look for the "Daily Prayer Time for Mosques" plugin (`dpt_` JS vars, `admin-ajax.php`, REST endpoints under `wp-json/dpt/`)
   - **MasjidBox widget** — look for `data-masjidbox-widget` attributes and `REDUX_STATE` in the HTML. Note: MasjidBox typically only returns 7 days of data, not a full year.
   - **Custom JSON API** — look for `fetch()`, `axios`, or REST endpoints with JSON responses
   - **Next.js site with Google Sheets** — look for published sheet IDs in the JavaScript bundles (e.g., Newham Mosques pattern)
   
3. Check the embedded JavaScript bundles for configuration objects containing API URLs

### Step 2: Validate the data source

- If it's a **Google Sheet CSV**: download it and verify you get structured CSV with prayer time columns
- If it's a **REST API**: test the endpoint and verify it returns structured JSON
- If it's a **WordPress REST endpoint**: test `https://site.com/wp-json/...` routes
- If it's an **HTML table**: parse the table rows from the rendered HTML to extract structured data
- If none of the above work: **Cannot extract**

### Step 3: Extract and format

1. Download/query the data for the full year (all 12 months)
2. Convert times to **24-hour format** (`HH:mm`)
3. Create 12 monthly JSON files in the correct directory structure
4. Add the entry to `mosques.json`
5. Mark as `isHidden: true` if:
   - Only part of the year is available (e.g. Jan-Jun only)
   - Data is placeholder/estimated (not verified)
   - Iqamah times are missing entirely
6. Mark as `isHidden: false` only for **complete, verified** full-year data

### Step 4: Seed

```bash
npx tsx scripts/seed-convex.ts --changed      # dev
npx tsx scripts/seed-convex.ts --changed --prod # production
```

## Data Sources Reference

### Google Sheets (published CSV)
URL pattern: `https://docs.google.com/spreadsheets/d/e/{PUBLISHED_ID}/pub?gid={GID}&single=true&output=csv`
- Published IDs end in `2PACX-...`
- GIDs are numeric (can be hex like `0x3b61a911`)
- Look in JavaScript source for sheet configurations

### WordPress Daily Prayer Time for Mosques plugin
- Look for `dpt_` JavaScript variables
- Plugin stores monthly data in wp_options table
- May expose REST API at `wp-json/dpt/v1/...` (but often blocked by Mod_Security)
- Homepage typically shows only today's times in SSR HTML

### MasjidBox widget
- Identified by `data-masjidbox-widget` attribute
- Data embedded in `window.REDUX_STATE` as URL-encoded JSON
- Typically only returns **7 days** of data — **not sufficient for full year**
- Has print view at `/print` but no full-year API

### Next.js + Google Sheets (Newham Mosques pattern)
- Sheet IDs and GIDs configured in JavaScript bundles
- Registry CSV at a published sheet URL with all mosques
- Each mosque has its own `full_csv_2pacx` URL for its timetable
- Timetable columns: DATE, HIJRI, DAY, FAJR, DHUHR, 'ASR, MAGHRIB, ESHA
- Times may be in 12h format — convert to 24h
- May not include iqamah data
