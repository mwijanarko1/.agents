#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const HOME = os.homedir();
const SHELLS = new Set(["sh", "bash", "zsh", "dash", "ksh"]);

function tokenize(source) {
  const commands = [];
  let tokens = [];
  let token = "";
  let quote = "";
  let connector = "";
  const flushToken = () => {
    if (token) tokens.push(token);
    token = "";
  };
  const flushCommand = (nextConnector = "") => {
    flushToken();
    if (tokens.length) commands.push({ tokens, connector });
    tokens = [];
    connector = nextConnector;
  };
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    if (quote) {
      if (char === quote) quote = "";
      else if (char === "\\" && quote === '"' && i + 1 < source.length) token += source[++i];
      else token += char;
      continue;
    }
    if (char === "'" || char === '"') {
      quote = char;
      continue;
    }
    if (char === "\\" && i + 1 < source.length) {
      if (source[i + 1] === "\n") i += 1;
      else token += source[++i];
      continue;
    }
    if (/\s/.test(char)) {
      flushToken();
      if (char === "\n") flushCommand(";");
      continue;
    }
    if (char === ";" || char === "|" || char === "&") {
      const op = source[i + 1] === char ? char + source[++i] : char;
      flushCommand(op);
      continue;
    }
    if (char === ">" || char === "<") {
      flushToken();
      const op = source[i + 1] === char ? char + source[++i] : char;
      tokens.push(op);
      continue;
    }
    token += char;
  }
  if (quote) throw new Error("unterminated shell quote");
  flushCommand();
  return commands;
}

function expand(value, variables) {
  let result = value.replace(/^~(?=\/|$)/, HOME);
  result = result.replace(/\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)/g, (_, braced, plain) => {
    const name = braced || plain;
    return variables.get(name) ?? `$${braced ? `{${name}}` : name}`;
  });
  return result;
}

function executableName(value) {
  return path.basename(value || "").toLowerCase();
}

function unwrap(tokens, variables) {
  const expanded = tokens.map((token) => expand(token, variables));
  let index = 0;
  while (/^[A-Za-z_][A-Za-z0-9_]*=/.test(expanded[index] || "")) {
    const equals = expanded[index].indexOf("=");
    variables.set(expanded[index].slice(0, equals), expanded[index].slice(equals + 1));
    index += 1;
  }
  for (;;) {
    const name = executableName(expanded[index]);
    if (!new Set(["command", "builtin", "nohup", "sudo", "env"]).has(name)) break;
    index += 1;
    const valuedOptions = name === "sudo"
      ? new Set(["-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt", "-C", "--close-from", "-T", "--command-timeout", "-D", "--chdir", "-R", "--chroot"])
      : name === "env" ? new Set(["-u", "--unset", "-C", "--chdir", "-S", "--split-string"]) : new Set();
    while ((expanded[index] || "").startsWith("-")) {
      const option = expanded[index++];
      if (valuedOptions.has(option)) index += 1;
    }
    while (/^[A-Za-z_][A-Za-z0-9_]*=/.test(expanded[index] || "")) index += 1;
  }
  return { executable: executableName(expanded[index]), args: expanded.slice(index + 1), tokens: expanded };
}

function catastrophicPath(value) {
  const clean = value.replace(/^['"]|['"]$/g, "").replace(/\/{2,}/g, "/");
  if (["/", "/*", HOME, `${HOME}/`, `${HOME}/*`, "/Users", "/Users/", "/Users/*"].includes(clean)) return true;
  return /^\/Users\/[^/]+\/?$/.test(clean);
}

function optionValue(args, longName) {
  const direct = args.find((arg) => arg.startsWith(`${longName}=`));
  if (direct) return direct.slice(longName.length + 1);
  const index = args.indexOf(longName);
  return index >= 0 ? args[index + 1] : undefined;
}

function inspectInvocation(invocation) {
  const { executable, args, tokens } = invocation;
  if (executable === "rm") {
    const targets = args.filter((arg) => arg === "-" || !arg.startsWith("-")).filter((arg) => arg !== "--");
    if (args.includes("--no-preserve-root") || targets.some(catastrophicPath)) return "catastrophic filesystem deletion";
  }
  if (/^mkfs(?:\.|$)/.test(executable)) return "filesystem formatting";
  if (executable === "dd" && args.some((arg) => /^of=\/dev\/(?:r?disk\d*|sd[a-z]\d*|nvme\d)/i.test(arg))) return "raw disk overwrite";
  if (executable === "diskutil" && /^(?:erase|partitiondisk|zerodisk|secureerase)/i.test(args[0] || "")) return "disk erasure";
  for (let i = 0; i < tokens.length - 1; i += 1) {
    if (/^>{1,2}$/.test(tokens[i]) && /^\/dev\/(?:r?disk\d*|sd[a-z]\d*|nvme\d)/i.test(tokens[i + 1])) return "raw device redirection";
  }
  if (["shutdown", "reboot", "poweroff", "halt"].includes(executable)) return "machine shutdown";
  if (executable === "kill" && args.includes("-9") && args.includes("1")) return "init process termination";
  if (executable === "chmod" && args.includes("777") && args.some(catastrophicPath)) return "root permission destruction";
  if (executable === "chown" && args.some((arg) => arg === "-R" || arg.startsWith("-R")) && args.some(catastrophicPath)) return "root ownership destruction";
  if (executable === "git") {
    const action = args[0];
    if (action === "push") {
      if (args.some((arg) => arg === "--force" || arg === "-f" || /^\+[^+]/.test(arg))) return "remote history rewrite";
      if (args.some((arg) => arg === "--delete" || arg === "-d" || /^:[A-Za-z0-9._/-]+$/.test(arg))) return "remote ref deletion";
    }
    if (action === "reflog" && args[1] === "expire" && args.some((arg) => /^--expire(?:-unreachable)?(?:=now)?$/.test(arg)) && args.includes("now")) return "immediate reflog destruction";
    if (action === "reflog" && args[1] === "expire" && args.some((arg) => /^--expire(?:-unreachable)?=now$/.test(arg))) return "immediate reflog destruction";
    if (action === "gc" && args.some((arg) => /^--prune(?:=(?:now|all))?$/.test(arg)) && args.some((arg) => arg === "now" || arg === "all" || /^--prune=(?:now|all)$/.test(arg))) return "immediate Git object pruning";
  }
  if (executable === "gh") {
    const [area, action] = args;
    if ((area === "repo" || area === "release" || area === "secret" || area === "ssh-key" || area === "gpg-key") && action === "delete") return "irreversible GitHub deletion";
    if (area === "auth" && action === "token") return "credential disclosure";
    if (area === "api" && /^(?:delete)$/i.test(optionValue(args, "--method") || optionValue(args, "-X") || "")) return "destructive GitHub API request";
    if (area === "repo" && action === "edit" && optionValue(args, "--visibility") === "public") return "repository visibility exposure";
  }
  return null;
}

function interpreterReason(executable, args) {
  const codeIndex = args.findIndex((arg) => arg === "-c" || arg === "-e");
  const code = codeIndex >= 0 ? args[codeIndex + 1] || "" : "";
  if (!code) return null;
  const target = String.raw`(?:\/|~|\$HOME|\$\{HOME\})`;
  const codeBoundary = String.raw`(?:^|[^"'A-Za-z0-9_.])`;
  if (["python", "python3"].includes(executable) && new RegExp(String.raw`${codeBoundary}(?:shutil\.rmtree|os\.(?:remove|rmdir))\s*\(\s*["']${target}["']`).test(code)) return "interpreter filesystem deletion";
  if (["node", "nodejs"].includes(executable) && new RegExp(String.raw`(?:^|[^"'A-Za-z0-9_])(?:rmSync|rmdirSync)\s*\(\s*["']${target}["']`).test(code)) return "interpreter filesystem deletion";
  if (executable === "ruby" && new RegExp(String.raw`${codeBoundary}(?:FileUtils\.)?(?:rm_rf|remove_entry_secure)\s*\(?\s*["']${target}["']`).test(code)) return "interpreter filesystem deletion";
  if (executable === "perl" && new RegExp(String.raw`${codeBoundary}(?:remove_tree|rmtree)\s*\(?\s*["']${target}["']`).test(code)) return "interpreter filesystem deletion";
  return null;
}

function nestedCommands(source) {
  const values = [];
  for (const match of source.matchAll(/\$\(([^()]*)\)|`([^`]*)`/g)) values.push(match[1] || match[2]);
  return values;
}

export function evaluateCommand(command, depth = 0) {
  if (typeof command !== "string" || !command.trim()) throw new Error("missing shell command");
  if (depth > 4) return { blocked: true, reason: "shell nesting limit exceeded" };
  const normalized = command.replace(/\\\r?\n/g, " ");
  if (/:\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:/.test(normalized)) return { blocked: true, reason: "fork bomb" };
  for (const nested of nestedCommands(normalized)) {
    const result = evaluateCommand(nested, depth + 1);
    if (result.blocked) return result;
  }
  const variables = new Map([["HOME", HOME]]);
  const commands = tokenize(normalized);
  const invocations = commands.map(({ tokens, connector }) => ({ ...unwrap(tokens, variables), connector }));
  for (const invocation of invocations) {
    const reason = inspectInvocation(invocation) || interpreterReason(invocation.executable, invocation.args);
    if (reason) return { blocked: true, reason };
    const script = invocation.executable === "eval"
      ? invocation.args.join(" ")
      : SHELLS.has(invocation.executable) && invocation.args.includes("-c")
        ? invocation.args[invocation.args.indexOf("-c") + 1]
        : "";
    if (script) {
      const result = evaluateCommand(script, depth + 1);
      if (result.blocked) return result;
    }
  }
  for (let i = 1; i < invocations.length; i += 1) {
    if (invocations[i].connector !== "|") continue;
    const pipeline = [];
    for (let j = i - 1; j >= 0 && (j === i - 1 || invocations[j + 1].connector === "|"); j -= 1) pipeline.unshift(invocations[j]);
    pipeline.push(invocations[i]);
    const sink = pipeline.at(-1);
    if (!SHELLS.has(sink.executable)) continue;
    if (pipeline.some((item) => item.executable === "curl" || item.executable === "wget")) return { blocked: true, reason: "network content piped to shell" };
    if (pipeline.some((item) => item.executable === "base64" && item.args.some((arg) => arg === "-d" || arg === "--decode"))) return { blocked: true, reason: "encoded content piped to shell" };
  }
  return { blocked: false };
}

function commandFromPayload(payload) {
  return payload?.tool_input?.command ?? payload?.toolInput?.command ?? payload?.command;
}

async function main() {
  try {
    const input = fs.readFileSync(0, "utf8");
    const payload = JSON.parse(input);
    const result = evaluateCommand(commandFromPayload(payload));
    if (!result.blocked) process.exit(0);
    process.stderr.write(`Blocked by global command guard: ${result.reason}.\n`);
    process.exit(2);
  } catch (error) {
    process.stderr.write(`Global command guard failed closed: ${error instanceof Error ? error.message : String(error)}.\n`);
    process.exit(2);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main();
