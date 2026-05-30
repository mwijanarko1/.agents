import { readFileSync } from "node:fs";
import { runAction } from "./guardrail-core.mjs";

const action = process.argv[2];
const tool = process.env.GUARDRAIL_TOOL || "generic";
const event = process.env.GUARDRAIL_EVENT || "";
const stdin = readFileSync(0, "utf8");
const result = runAction(action, stdin, process.env);

function printJson(value) {
  process.stdout.write(`${JSON.stringify(value)}\n`);
}

function formatMessages(items) {
  return items.map((item) => item.message || item).join(" ");
}

if (tool === "cursor" && event === "beforeShellExecution") {
  if (result.blocked) {
    printJson({
      permission: "deny",
      user_message: result.reason || formatMessages(result.checks || result.findings || []),
      agent_message: result.reason || formatMessages(result.checks || result.findings || []),
    });
  } else {
    printJson({ permission: "allow" });
  }
  process.exit(0);
}

if (tool === "codex" && event === "PreToolUse") {
  if (result.blocked) {
    printJson({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: result.reason || formatMessages(result.checks || result.findings || []),
      },
    });
  }
  process.exit(0);
}

if (tool === "codex" && event === "Stop") {
  if (result.blocked) {
    printJson({
      continue: false,
      stopReason: result.reason || formatMessages(result.blockers || result.findings || result.checks || []),
      systemMessage: result.summary || result.reason || formatMessages(result.blockers || result.findings || result.checks || []),
    });
  } else if (result.summary || (result.advisories && result.advisories.length > 0)) {
    printJson({
      continue: true,
      systemMessage: result.summary || result.advisories.join(" "),
    });
  }
  process.exit(0);
}

if (tool === "codex" && event === "PostToolUse") {
  if (result.blocked) {
    printJson({
      hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext: result.reason || formatMessages(result.checks || result.findings || []),
      },
    });
  } else if (result.summary) {
    printJson({
      hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext: result.summary,
      },
    });
  }
  process.exit(0);
}

if (tool === "cursor" && event === "afterShellExecution") {
  if (result.summary) {
    process.stderr.write(`${result.summary}\n`);
  }
  process.exit(0);
}

if (tool === "cursor" && (event === "afterFileEdit" || event === "stop")) {
  if (result.blocked) {
    process.stderr.write(`${result.reason || formatMessages(result.blockers || result.findings || result.checks || [])}\n`);
    process.exit(2);
  }
  if (result.summary) {
    process.stderr.write(`${result.summary}\n`);
  }
  process.exit(0);
}

if ((tool === "codex" || tool === "cursor") && event === "UserPromptSubmit") {
  if (result.summary) {
    printJson({
      hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: result.summary,
      },
    });
  }
  process.exit(0);
}

if (result.blocked) {
  process.stderr.write(`${result.reason || formatMessages(result.blockers || result.findings || result.checks || [])}\n`);
  process.exit(2);
}

if (result.summary) {
  process.stdout.write(`${result.summary}\n`);
} else if (result.message && result.message !== "logged") {
  process.stdout.write(`${result.message}\n`);
}
