import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import { runAction } from "../hooks/lib/guardrail-core.mjs";

function makeRepo() {
  const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "ai-flow-gate-"));
  const init = spawnSync("git", ["init"], { cwd: repoRoot, encoding: "utf8" });
  assert.equal(init.status, 0, init.stderr);
  return repoRoot;
}

function submitPrompt(repoRoot, prompt) {
  return runAction("ai-flow-gate", JSON.stringify({ prompt, cwd: repoRoot }), {
    GUARDRAIL_TOOL: "codex",
    GUARDRAIL_EVENT: "UserPromptSubmit",
  });
}

function preflight(repoRoot, command = "python3 - <<'PY'\nprint('write')\nPY") {
  return runAction("codex-preflight", JSON.stringify({ command, cwd: repoRoot }), {
    GUARDRAIL_TOOL: "codex",
    GUARDRAIL_EVENT: "PreToolUse",
  });
}

function tddGate(repoRoot) {
  return runAction("tdd-gate", JSON.stringify({ cwd: repoRoot }), {
    GUARDRAIL_TOOL: "codex",
    GUARDRAIL_EVENT: "Stop",
  });
}

function stopGate(repoRoot) {
  return runAction("codex-stop", JSON.stringify({ cwd: repoRoot }), {
    GUARDRAIL_TOOL: "codex",
    GUARDRAIL_EVENT: "Stop",
  });
}

function writeEvidence(repoRoot, payload) {
  const evidencePath = path.join(repoRoot, ".git", "agent-notes", "tdd-evidence.json");
  fs.mkdirSync(path.dirname(evidencePath), { recursive: true });
  fs.writeFileSync(evidencePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function statePath(repoRoot) {
  const gitDir = spawnSync("git", ["rev-parse", "--git-dir"], { cwd: repoRoot, encoding: "utf8" }).stdout.trim();
  return path.join(repoRoot, gitDir, "agent-notes", "ai-flow-state.json");
}

function readState(repoRoot) {
  return JSON.parse(fs.readFileSync(statePath(repoRoot), "utf8"));
}

function completeBrief(repoRoot) {
  const state = readState(repoRoot);
  const brief = Object.fromEntries(state.requiredBriefFields.map((field) => [field, `${field} value`]));
  const checksumPayload = {
    mode: state.mode,
    promptHash: state.promptHash,
    brief,
  };
  state.brief = brief;
  state.briefChecksum = crypto.createHash("sha256").update(JSON.stringify(checksumPayload)).digest("hex");
  fs.writeFileSync(statePath(repoRoot), `${JSON.stringify(state, null, 2)}\n`, "utf8");
  return state;
}

{
  const repoRoot = makeRepo();
  const result = submitPrompt(repoRoot, "Add password reset");
  assert.equal(result.blocked, false);
  assert.equal(result.aiFlow.mode, "unset");
  assert.match(result.summary, /choose `\/serious` or `\/fun`/);

  const blocked = preflight(repoRoot);
  assert.equal(blocked.blocked, true);
  assert.match(blocked.reason, /choose `\/serious` or `\/fun`/);
}

{
  const repoRoot = makeRepo();
  const result = submitPrompt(repoRoot, "/serious Add password reset");
  assert.equal(result.aiFlow.mode, "serious");
  assert.equal(result.aiFlow.briefStatus, "missing");
  assert.match(result.summary, /interview/i);

  const blocked = preflight(repoRoot);
  assert.equal(blocked.blocked, true);
  assert.match(blocked.reason, /requires a completed task brief/);
}

{
  const repoRoot = makeRepo();
  submitPrompt(repoRoot, "/fun make a weird animation");
  fs.writeFileSync(path.join(repoRoot, "app.js"), "export function demo() { return 1; }\n", "utf8");

  const result = tddGate(repoRoot);
  assert.equal(result.blocked, false);
  assert.match(result.summary, /fun mode/i);
}

{
  const repoRoot = makeRepo();
  submitPrompt(repoRoot, "/serious Add password reset");
  const state = readState(repoRoot);
  state.briefStatus = "complete";
  state.completedBriefFields = state.requiredBriefFields;
  fs.writeFileSync(statePath(repoRoot), `${JSON.stringify(state, null, 2)}\n`, "utf8");

  const result = preflight(repoRoot);
  assert.equal(result.blocked, true);
  assert.match(result.reason, /requires a completed task brief/);
}

{
  const repoRoot = makeRepo();
  submitPrompt(repoRoot, "/serious Add password reset");
  completeBrief(repoRoot);

  const result = preflight(repoRoot);
  assert.equal(result.blocked, false);
}

{
  const repoRoot = makeRepo();
  submitPrompt(repoRoot, "/serious Add password reset");
  completeBrief(repoRoot);
  fs.writeFileSync(path.join(repoRoot, "app.js"), "export function demo() { return 1; }\n", "utf8");
  writeEvidence(repoRoot, {
    version: 1,
    events: [
      { stage: "red", timestamp: "2026-01-01T00:00:00Z", command: "npm test", exit_code: 1 },
      { stage: "green", timestamp: "2026-01-01T00:01:00Z", command: "npm test", exit_code: 0 },
    ],
    exceptions: [],
  });

  const result = tddGate(repoRoot);
  assert.equal(result.blocked, true);
  assert.match(result.reason, /current task/i);
}

{
  const repoRoot = makeRepo();
  const readResult = preflight(repoRoot, "sed -n '1,20p' ~/.codex/config.toml");
  assert.equal(readResult.blocked, false);

  submitPrompt(repoRoot, "/fun update config");
  const writeResult = preflight(repoRoot, "echo x > ~/.codex/config.toml");
  assert.equal(writeResult.blocked, true);
  assert.match(writeResult.reason, /protected config edit/i);
}

{
  const repoRoot = makeRepo();
  submitPrompt(repoRoot, "/fun add dependency");
  const result = preflight(repoRoot, "npx playwright test");
  assert.equal(result.blocked, false);
}

{
  const repoRoot = makeRepo();
  submitPrompt(repoRoot, "/fun start local preview");
  const result = preflight(repoRoot, "npm run dev");
  assert.equal(result.blocked, false);
}

{
  const repoRoot = makeRepo();
  submitPrompt(repoRoot, "/fun edit generated assets");
  fs.mkdirSync(path.join(repoRoot, "src", "types"), { recursive: true });
  fs.writeFileSync(path.join(repoRoot, "src", "types", "generated.ts"), "export type Generated = string;\n", "utf8");

  const result = stopGate(repoRoot);
  assert.equal(result.blocked, false);
}

console.log("ai flow gate tests passed");
