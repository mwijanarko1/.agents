#!/usr/bin/env node
/**
 * Open a URL (or YouTube search) in Helium via Playwright.
 * Usage:
 *   node open.mjs "https://example.com"
 *   node open.mjs --search "spain vs belgium highlights"
 *   node open.mjs --youtube "spain vs belgium highlights"
 *   node open.mjs --headed --search "cats"
 * Env:
 *   HELIUM_PATH  override binary (default: /Applications/Helium.app/Contents/MacOS/Helium)
 *   HEADLESS=1   force headless
 */
import { chromium } from "playwright";
import { accessSync, constants } from "node:fs";
import { pathToFileURL } from "node:url";

const HELIUM =
  process.env.HELIUM_PATH ||
  "/Applications/Helium.app/Contents/MacOS/Helium";

function die(msg, code = 1) {
  console.error(msg);
  process.exit(code);
}

function ensureHelium() {
  try {
    accessSync(HELIUM, constants.X_OK);
  } catch {
    die(
      `Helium not found/executable at:\n  ${HELIUM}\nInstall Helium or set HELIUM_PATH.`,
    );
  }
}

function parseArgs(argv) {
  const out = {
    url: null,
    search: null,
    youtube: null,
    headed: process.env.HEADLESS !== "1",
    keepOpenMs: 0,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--search") out.search = argv[++i];
    else if (a === "--youtube") out.youtube = argv[++i];
    else if (a === "--headed") out.headed = true;
    else if (a === "--headless") out.headed = false;
    else if (a === "--keep-open") out.keepOpenMs = Number(argv[++i] || 0);
    else if (a === "--help" || a === "-h") out.help = true;
    else if (!a.startsWith("-") && !out.url) out.url = a;
    else die(`Unknown arg: ${a}`);
  }
  return out;
}

function resolveUrl({ url, search, youtube }) {
  if (youtube) {
    return `https://www.youtube.com/results?search_query=${encodeURIComponent(youtube)}`;
  }
  if (search) {
    return `https://www.google.com/search?q=${encodeURIComponent(search)}`;
  }
  if (url) return url;
  return null;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(`Usage:
  node open.mjs <url>
  node open.mjs --youtube "query"
  node open.mjs --search "query"
  node open.mjs --headed --keep-open 60000 --youtube "spain vs belgium highlights"`);
    return;
  }

  const target = resolveUrl(args);
  if (!target) die("Pass a URL, --youtube <q>, or --search <q>.");

  ensureHelium();

  const browser = await chromium.launch({
    executablePath: HELIUM,
    headless: !args.headed,
    args: ["--disable-blink-features=AutomationControlled"],
  });

  try {
    const page = await browser.newPage();
    await page.goto(target, { waitUntil: "domcontentloaded", timeout: 60_000 });
    const title = await page.title();
    console.log(JSON.stringify({ ok: true, url: page.url(), title, helium: HELIUM }, null, 2));

    if (args.keepOpenMs > 0) {
      await page.waitForTimeout(args.keepOpenMs);
    } else if (args.headed) {
      // Keep window open until user closes it or Ctrl-C.
      // ponytail: simple wait; add CDP detach if you need agent to exit while browser stays.
      await new Promise(() => {});
    }
  } finally {
    if (!args.headed || args.keepOpenMs > 0) {
      await browser.close().catch(() => {});
    }
  }
}

// Allow `node open.mjs` and `import` usage.
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((e) => die(e.stack || String(e)));
}
