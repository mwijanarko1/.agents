#!/usr/bin/env node
/**
 * Luma "Request to Join" for Redwood build weekends.
 * Usage:
 *   node rsvp.mjs --url URL --name NAME --email EMAIL [--fun-fact TEXT] [--headed|--headless]
 */
import { createRequire } from "node:module";
import { accessSync, constants } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PW_ROOT = join(__dirname, "../../playwright-browser/node_modules/playwright");
const require = createRequire(join(PW_ROOT, "package.json"));
const { chromium } = require(PW_ROOT);

const HELIUM =
  process.env.HELIUM_PATH ||
  "/Applications/Helium.app/Contents/MacOS/Helium";

function die(msg, code = 1) {
  console.error(msg);
  process.exit(code);
}

function parseArgs(argv) {
  const out = {
    url: null,
    name: null,
    email: null,
    funFact: "This request to join was filled in by my agent",
    headed: process.env.HEADLESS !== "1",
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--url") out.url = argv[++i];
    else if (a === "--name") out.name = argv[++i];
    else if (a === "--email") out.email = argv[++i];
    else if (a === "--fun-fact") out.funFact = argv[++i];
    else if (a === "--headed") out.headed = true;
    else if (a === "--headless") out.headed = false;
    else if (a === "--help" || a === "-h") out.help = true;
    else die(`Unknown arg: ${a}`);
  }
  return out;
}

function ensureHelium() {
  try {
    accessSync(HELIUM, constants.X_OK);
  } catch {
    die(`Helium not found/executable at:\n  ${HELIUM}\nInstall Helium or set HELIUM_PATH.`);
  }
}

function classify(body) {
  const t = body.toLowerCase();
  if (
    t.includes("registration pending") ||
    t.includes("pending approval") ||
    t.includes("request has been submitted")
  ) {
    return "pending_approval";
  }
  if (
    t.includes("you're in") ||
    t.includes("you are registered") ||
    t.includes("registration confirmed") ||
    t.includes("spot is reserved")
  ) {
    return "registered";
  }
  if (t.includes("verify token") || t.includes("wallet") && t.includes("connect")) {
    return "needs_wallet";
  }
  if (t.includes("sign in") && t.includes("your info") === false && !t.includes("name *")) {
    // weak signal only
  }
  return "unknown";
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(`Usage:
  node rsvp.mjs --url URL --name NAME --email EMAIL [--fun-fact TEXT] [--headed|--headless]`);
    return;
  }
  if (!args.url || !args.name || !args.email) {
    die("Required: --url --name --email");
  }
  ensureHelium();

  const browser = await chromium.launch({
    executablePath: HELIUM,
    headless: !args.headed,
  });
  const page = await browser.newPage();
  try {
    await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2000);

    const requestBtn = page.getByRole("button", { name: /Request to Join|Register|RSVP/i }).first();
    if (await requestBtn.count()) {
      await requestBtn.click({ timeout: 10000 });
      await page.waitForTimeout(1500);
    }

    const name = page.locator('input[name="name"]');
    const email = page.locator('input[name="email"]');
    await name.waitFor({ state: "visible", timeout: 15000 });
    await name.fill(args.name);
    await email.fill(args.email);

    const fun = page.locator('input[name="registration_answers.0.value"], textarea[name="registration_answers.0.value"]');
    if (await fun.count()) {
      await fun.first().fill(args.funFact);
    }

    // other required registration answers: fill with fun-fact fallback
    const requiredEmpty = page.locator(
      'input[name^="registration_answers"][required], textarea[name^="registration_answers"][required]',
    );
    const nReq = await requiredEmpty.count();
    for (let i = 0; i < nReq; i++) {
      const el = requiredEmpty.nth(i);
      const v = await el.inputValue().catch(() => "");
      if (!v) await el.fill(args.funFact);
    }

    const submits = page.getByRole("button", { name: /Request to Join|Submit|Register|RSVP/i });
    const sc = await submits.count();
    if (!sc) die("status: error\nNo submit button found");
    await submits.nth(sc - 1).click({ timeout: 10000 });
    await page.waitForTimeout(5000);

    const body = await page.locator("body").innerText();
    let status = classify(body);

    if (status === "unknown") {
      const stillForm = await page.locator('input[name="name"]').count();
      if (stillForm) {
        const walletish = /wallet|token ownership|connect wallet/i.test(body);
        status = walletish ? "needs_wallet" : "error";
      }
    }

    const out = {
      status,
      url: page.url(),
      name: args.name,
      email: args.email,
      funFact: args.funFact,
      bodySnippet: body.replace(/\s+/g, " ").trim().slice(0, 500),
    };
    console.log(JSON.stringify(out, null, 2));
    if (status === "pending_approval" || status === "registered") process.exit(0);
    process.exit(2);
  } finally {
    await browser.close().catch(() => {});
  }
}

main().catch((e) => die(String(e?.stack || e)));
