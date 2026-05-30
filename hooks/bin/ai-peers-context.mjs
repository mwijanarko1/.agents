#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const PYTHON = "/Users/mikhail/.agents/vendor/ai-peers/.venv/bin/python";
const CLI = "/Users/mikhail/.agents/vendor/ai-peers/cli.py";
const DISPATCH = "/Users/mikhail/.local/bin/ai-dispatch";
const TOOL = process.env.GUARDRAIL_TOOL || "generic";
const EVENT = process.env.GUARDRAIL_EVENT || "UserPromptSubmit";
const SESSION_KEY = process.env.AI_PEERS_SESSION_KEY || "";

function parseInput(raw) {
  if (!raw.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function promptText(input) {
  return String(input.prompt || input.message || input.text || "").trim();
}

function summarizePrompt(text) {
  const clean = text.replace(/\s+/g, " ").trim();
  if (!clean) return "";
  return clean.length <= 140 ? clean : `${clean.slice(0, 137)}...`;
}

function runCli(args) {
  const result = spawnSync(PYTHON, [CLI, ...args], {
    env: process.env,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    return null;
  }
  try {
    return JSON.parse(result.stdout);
  } catch {
    return null;
  }
}

function runDispatch(args) {
  const result = spawnSync(DISPATCH, args, {
    env: process.env,
    encoding: "utf8",
  });
  if (result.status !== 0 && !result.stdout.trim()) {
    return null;
  }
  try {
    return JSON.parse(result.stdout);
  } catch {
    return null;
  }
}

function formatContext(peer, messages) {
  const lines = [
    "<peer-messages>",
    "Unread coordination messages from other local AI sessions:",
  ];
  for (const message of messages) {
    const parts = [
      `from=${message.from_client || "unknown"}`,
      message.from_role ? `role=${message.from_role}` : "",
      message.from_cwd ? `cwd=${message.from_cwd}` : "",
      message.from_summary ? `summary=${message.from_summary}` : "",
    ].filter(Boolean);
    lines.push(`- [${message.from_peer_id}] ${parts.join(" | ")} | message=${message.body}`);
  }
  if (peer?.role === "orchestrator-reviewer") {
    lines.push("Routing policy: you are the orchestrator and reviewer. Native subagents are the first specialist layer. Use the AI bridge only when the user explicitly asks for it and names the target coding tool.");
  }
  lines.push("Treat these as fresh peer updates. Resolve conflicts before making overlapping edits.");
  lines.push("</peer-messages>");
  return lines.join("\n");
}

function formatCompletionContext(jobs) {
  const stripAnsi = (text) => String(text || "").replace(/\u001b\[[0-9;]*m/g, "");
  const lines = [
    "<delegation-completions>",
    "Completed delegated worker jobs:",
  ];
  for (const job of jobs) {
    const winner = job.winner || "none";
    const status = job.status || "unknown";
    const attempts = Array.isArray(job.attempts) ? job.attempts : [];
    const detail = attempts
      .map((attempt) => {
        const output = stripAnsi(attempt.stdout || attempt.stderr || "").replace(/\s+/g, " ").trim();
        const short = output.length > 260 ? `${output.slice(0, 257)}...` : output;
        return `${attempt.worker}[exit=${attempt.exit_code}] ${short}`;
      })
      .join(" || ");
    lines.push(`- job=${job.job_id} status=${status} winner=${winner} difficulty=${job.difficulty} route=${(job.route || []).join(",")} | ${detail}`);
  }
  lines.push("These notifications come from background delegated jobs finishing. Use them before launching overlapping follow-up work.");
  lines.push("</delegation-completions>");
  return lines.join("\n");
}

function emit(context) {
  if (!context) return;
  if (TOOL === "cursor") {
    process.stdout.write(`${JSON.stringify({ additional_context: context })}\n`);
    return;
  }
  process.stdout.write(
    `${JSON.stringify({
      hookSpecificOutput: {
        hookEventName: EVENT,
        additionalContext: context,
      },
    })}\n`,
  );
}

const raw = readFileSync(0, "utf8");
const input = parseInput(raw);

if (SESSION_KEY) {
  const text = summarizePrompt(promptText(input));
  if (text) {
    runCli(["set-summary-for", text]);
  }
  const completions = runDispatch(["poll-completions", "--session-key", SESSION_KEY, "--limit", "8"]);
  const polled = runCli(["poll", "--limit", "8"]);
  const messages = polled?.messages || [];
  const completionJobs = completions?.jobs || [];
  const parts = [];
  if (messages.length > 0) {
    parts.push(formatContext(polled.peer, messages));
  }
  if (completionJobs.length > 0) {
    parts.push(formatCompletionContext(completionJobs));
  }
  if (parts.length > 0) {
    emit(parts.join("\n\n"));
  }
}
