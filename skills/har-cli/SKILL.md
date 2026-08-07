---
name: har-cli
description: "Build a shareable terminal client by reverse-engineering a website from one authenticated HAR capture. Use when the user wants a CLI for a site with no public API, says reverse-engineer from HAR, browser once then derive client, Next.js server-action login CLI, or scrape authed SSR HTML into a TUI. Different from playwright-browser/ditto-clone because the browser is only for capture — the product is a zero/low-dep CLI that replays discovered auth and reads."
---

# HAR → CLI reverse engineer

Goal: **one browser session → HAR → durable CLI** that teammates can run with their own login. No headless browser in the shipped tool.

## Hard boundaries

- Only sites/accounts the user is authorized to access.
- Never ship credentials, session cookies, or HAR files in the repo.
- Prefer **read-only** CLIs unless the user explicitly wants writes.
- Do not build exploit tooling, credential stuffing, or bypasses of access controls.
- If login uses SSO you cannot replay (Google-only, hardware key), stop and say so.

## Workflow

### 1. Capture (browser once)

1. Open DevTools → Network → check **Preserve log**.
2. Perform: load login page → submit login → hit every page the CLI should support.
3. Export **HAR** (Save all as HAR). Put it outside the repo, e.g. `/tmp/<site>-har/session.har`.
4. Optional: copy one authed page HTML snapshot per route for formatter work.

Do **not** commit the HAR.

### 2. Mine the HAR

Run the helper (or equivalent `jq`):

```bash
node ~/.agents/skills/har-cli/scripts/mine-har.mjs /tmp/<site>-har/session.har
```

Record:

| Signal | Where in HAR | Why |
|--------|----------------|-----|
| Login URL + method | first auth `POST` | CLI entry |
| Auth wire format | headers + postData | cookies / JSON / form / `next-action` |
| Session cookies | `Set-Cookie` on auth response | `session.json` |
| Data URLs | later `GET`/`POST` with cookie | pages or API |
| JSON APIs | `content-type: json` responses | prefer over HTML |
| SSR HTML only | `text/html` documents | need formatters |
| CSRF / action ids | headers like `next-action`, `x-csrf-token` | often **build-hashed** → drift risk |

**Next.js server actions (common):**

- Request header: `next-action: <hash>`
- Multipart fields often: `1_<field>`, plus `0=["$K1"]` (or similar Flight args)
- Response: RSC/text stream + `Set-Cookie` (e.g. Supabase `sb-…-auth-token`)
- Action ids **break on redeploy** — document how to refresh from DevTools

### 3. Choose the thinnest client shape

Stop at the first that works:

1. **Official API / token** already exists → use it; stop this skill.
2. **JSON XHR/fetch** same-origin with session cookie → call those endpoints.
3. **SSR HTML** only → `GET` pages with cookie, parse to text.
4. Mixed → API for lists, HTML for leftovers.

Default stack unless user asks otherwise:

- **Node 18.17+** single file (`*.mjs`), zero deps (`fetch`, `FormData`, `headers.getSetCookie`)
- Session: `~/.config/<cli-name>/session.json` mode `0600`, dir `0700`
- Auth: prompt email/password (or site’s method) — **no password argv**, no Bitwarden requirement in the product
- UX: `cli` → login if needed → arrow-key menu; also `cli <page>` one-shots
- README: install, usage, session path, **action-id refresh**, “unofficial”

### 4. Implement (minimal order)

1. `serverAction` / `login` + cookie jar merge (honor `Max-Age=0` deletions).
2. `getPage(path)` or `api(path)` with cookie; detect expired session → clear + re-login.
3. One formatter per dense page (don’t dump raw HTML).
4. Interactive `pick()` menu if multiple screens; fix redraw math (`rows = lines.length`).
5. `package.json` `bin`, MIT/license as user prefers, `.gitignore` (`*.har`, `session.json`, `.env`).

### 5. Verify

```bash
node --check <cli>.mjs
node <cli>.mjs --help
node <cli>.mjs login          # user types creds in their TTY
node <cli>.mjs <page> | head
```

Re-check after formatter changes against **live** HTML, not only the HAR snapshot.

### 6. Package for humans

- README with clone + `npm link` / symlink to `~/.local/bin`
- Note Node version (`>=18.17` if using `getSetCookie`)
- Optional agent skill **for using** the finished CLI (read-only commands) — separate from this skill
- Never publish HAR or `session.json`

## HAR mining checklist (manual)

If the script is unavailable, in the HAR JSON inspect `log.entries[]`:

```text
request.url / method
request.headers (cookie, next-action, content-type, authorization)
request.postData.text | params
response.status
response.headers (set-cookie)
response.content.mimeType + text (truncate)
```

Group entries by path. Prefer the **smallest** set of calls that reconstruct login + each page.

## Failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Login “succeeds” but no cookie | stale `next-action` / wrong content-type | re-HAR login only; update id |
| 200 HTML login page when fetching app | missing/expired cookie | `ensureAuthed`; clear session |
| Empty formatters | markup drift | re-fetch live HTML; tighten selectors |
| Multipart broken for weird passwords | hand-rolled body | use `FormData` + fetch |
| Teammate on Node 18.0–18.16 | no `getSetCookie` | engines `>=18.17` |

## Reference implementation

Pattern proven in `redwood-cli` (`redwood.mjs`): Next.js action login → cookie session → SSR HTML formatters → interactive menu. Reuse the **approach**, not the Redwood action ids.

## Anti-patterns

- Shipping Playwright/Puppeteer for everyday reads when HAR-derived `fetch` works
- Password on the command line
- Committing HAR/cookies
- One mega-regex over entire homepage instead of per-route formatters
- Building write/actions the user did not ask for
