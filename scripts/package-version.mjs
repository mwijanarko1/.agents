#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";

const packageName = process.argv[2];
if (!packageName) {
  console.error("Usage: package-version.mjs <package>");
  process.exit(2);
}

const require = createRequire(join(process.cwd(), "package.json"));
let directory = dirname(require.resolve(packageName));

while (directory !== dirname(directory)) {
  const manifestPath = join(directory, "package.json");
  if (existsSync(manifestPath)) {
    const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
    if (manifest.name === packageName) {
      console.log(manifest.version);
      process.exit(0);
    }
  }
  directory = dirname(directory);
}

console.error(`Could not locate package.json for ${packageName}`);
process.exit(1);
