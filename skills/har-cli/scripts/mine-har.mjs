#!/usr/bin/env node
// Summarize a HAR for CLI reverse-engineering: auth posts, cookies, APIs, HTML docs.
// Usage: node mine-har.mjs <file.har> [--json]
// Does not print cookie values or full bodies by default.

import { readFileSync } from 'node:fs'

const path = process.argv[2]
const asJson = process.argv.includes('--json')
if (!path || path === '-h' || path === '--help') {
  console.error('usage: node mine-har.mjs <file.har> [--json]')
  process.exit(1)
}

const har = JSON.parse(readFileSync(path, 'utf8'))
const entries = har?.log?.entries || []

function hdrs(headers = []) {
  const o = {}
  for (const h of headers) {
    if (!h?.name) continue
    o[h.name.toLowerCase()] = h.value
  }
  return o
}

function cookieNames(setCookieList) {
  const names = []
  for (const raw of setCookieList || []) {
    const name = String(raw).split('=')[0]?.trim()
    if (name) names.push(name)
  }
  return names
}

function summarize(e) {
  const req = e.request || {}
  const res = e.response || {}
  const rh = hdrs(req.headers)
  const sh = hdrs(res.headers)
  const setCookie = (res.headers || [])
    .filter((h) => h.name?.toLowerCase() === 'set-cookie')
    .map((h) => h.value)
  const mime = res.content?.mimeType || ''
  const post = req.postData?.text || ''
  const postPreview =
    post.length > 200 ? post.slice(0, 200).replace(/\s+/g, ' ') + '…' : post.replace(/\s+/g, ' ')

  return {
    method: req.method,
    url: req.url,
    status: res.status,
    mime,
    nextAction: rh['next-action'] || null,
    contentType: rh['content-type'] || null,
    authorization: rh.authorization ? '[present]' : null,
    reqCookie: rh.cookie ? '[present]' : null,
    setCookieNames: cookieNames(setCookie),
    postMime: req.postData?.mimeType || null,
    postPreview: postPreview || null,
    size: res.content?.size ?? (res.content?.text || '').length,
  }
}

const rows = entries.map(summarize)

const authish = rows.filter(
  (r) =>
    r.method !== 'GET' &&
    (r.nextAction ||
      /login|auth|session|signin|sign-in|token/i.test(r.url) ||
      r.setCookieNames.length > 0),
)

const htmlDocs = rows.filter(
  (r) => r.method === 'GET' && /html/i.test(r.mime || '') && r.status >= 200 && r.status < 400,
)

const jsonApis = rows.filter(
  (r) => /json/i.test(r.mime || '') && !/html/i.test(r.mime || '') && r.status >= 200 && r.status < 500,
)

const actionIds = [...new Set(rows.map((r) => r.nextAction).filter(Boolean))]

const out = {
  file: path,
  entries: rows.length,
  nextActionIds: actionIds,
  authCandidates: authish.slice(0, 40),
  htmlDocuments: htmlDocs.slice(0, 60).map((r) => ({
    status: r.status,
    url: r.url,
    size: r.size,
  })),
  jsonApis: jsonApis.slice(0, 80).map((r) => ({
    method: r.method,
    status: r.status,
    url: r.url,
    size: r.size,
  })),
}

if (asJson) {
  console.log(JSON.stringify(out, null, 2))
  process.exit(0)
}

console.log(`HAR: ${path}`)
console.log(`entries: ${rows.length}`)
if (actionIds.length) {
  console.log('\nnext-action ids:')
  for (const id of actionIds) console.log(`  ${id}`)
}
console.log(`\nauth-ish requests (${authish.length}):`)
for (const r of authish.slice(0, 25)) {
  console.log(`  ${r.status} ${r.method} ${r.url}`)
  if (r.nextAction) console.log(`    next-action: ${r.nextAction}`)
  if (r.contentType) console.log(`    content-type: ${r.contentType}`)
  if (r.setCookieNames.length) console.log(`    set-cookie: ${r.setCookieNames.join(', ')}`)
  if (r.postPreview) console.log(`    body: ${r.postPreview}`)
}
console.log(`\nHTML documents (${htmlDocs.length}):`)
for (const r of htmlDocs.slice(0, 30)) {
  console.log(`  ${r.status} ${r.url}  (${r.size}b)`)
}
console.log(`\nJSON-ish APIs (${jsonApis.length}):`)
for (const r of jsonApis.slice(0, 40)) {
  console.log(`  ${r.status} ${r.method} ${r.url}  (${r.size}b)`)
}
if (!authish.length && !jsonApis.length && !htmlDocs.length) {
  console.log('\n(no candidates — is this a full page HAR with content?)')
}
