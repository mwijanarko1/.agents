---
name: create-mwhs-khutbah
description: "Create and manage khutbahs on the MWHS (mwhs.org.uk) admin dashboard using a macOS native dialog for credentials and the admin API via session cookie."
argument-hint: "<action> [khutbah-args]"
---

# Create MWHS Khutbah

Manage khutbahs on mwhs.org.uk via admin API. **Mutating calls (create/delete) require explicit user confirmation first.**

## Security

- Credentials via **macOS native dialog** only — never chat/terminal/logs.
- Authenticate once with a headed browser/login helper; reuse session cookie for curl.
- Do not print the session cookie. Treat `401`/`403` as re-auth.

## Config (env / discovery)

| Variable | Purpose |
|----------|---------|
| `MWHS_PROJECT_DIR` | Checkout that has Playwright + login helper deps |
| `MWHS_LOGIN_HELPER` | Path to login script that writes the session file |
| `MWHS_SESSION_FILE` | Session cookie file (default `/tmp/alb-session.txt`) |

If unset, look for a local Sheffield-Masjids-style project cwd the user indicates. Do not hardcode personal absolute paths.

## API (base `https://www.mwhs.org.uk`)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/admin/khutbahs` | list |
| POST | `/api/admin/khutbahs/fetch-metadata` | body `{"url"}` (YouTube) |
| POST | `/api/admin/khutbahs` | create — body `title,date,youtubeUrl,speaker` |
| DELETE | `/api/admin/khutbahs/{id}` | delete |

## Workflow

1. **Session** — if `$MWHS_SESSION_FILE` missing/expired, run `$MWHS_LOGIN_HELPER` from `$MWHS_PROJECT_DIR` (headed). Confirm HTTP success before continuing.
2. **Read-only first** — list or fetch-metadata; handle non-2xx with body snippet (no cookie).
3. **Mutations** — show payload/id, get explicit confirmation, then POST/DELETE.
4. **Verify** — GET list/detail after mutation; report id + title/date.

```bash
SESSION_FILE="${MWHS_SESSION_FILE:-/tmp/alb-session.txt}"
TOKEN=$(cat "$SESSION_FILE")
SESSION="${TOKEN#admin-session=}"

curl -sS -fS "https://www.mwhs.org.uk/api/admin/khutbahs" \
  -H "Cookie: admin-session=$SESSION"
```

Use `-fS` or check status codes. Date: ISO-8601 UTC midnight. Create field is `youtubeUrl`; metadata endpoint field is `url`.
