import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";

const DEFAULT_SCHEMA_PATHS = [
  "db/migrations/**",
  "prisma/schema.prisma",
  "supabase/migrations/**",
  "openapi/**",
];

const DEFAULT_DOCS_PATHS = [
  "openapi/**",
  "schema/**",
  "docs/**",
  "src/types/**",
  "config/**",
];

const DEFAULT_PROTECTED_FILES = [
  ".env*",
  ".git/**",
  "package-lock.json",
  "pnpm-lock.yaml",
  "yarn.lock",
  "bun.lock",
  "bun.lockb",
  "*.pem",
  "*.key",
  "secrets/**",
];

const DANGEROUS_PATTERNS = [
  { pattern: /\brm\s+-rf\b/i, reason: "Blocked destructive delete command." },
  { pattern: /\bgit\s+reset\s+--hard\b/i, reason: "Blocked hard reset command." },
  { pattern: /\bgit\s+clean\s+-fdx\b/i, reason: "Blocked destructive git clean command." },
  { pattern: /\bgit\s+push\b.*\s--force(?:-with-lease)?\b/i, reason: "Blocked force push command." },
  { pattern: /\bDROP\s+TABLE\b/i, reason: "Blocked destructive SQL command." },
  { pattern: /\bDROP\s+DATABASE\b/i, reason: "Blocked destructive SQL command." },
  { pattern: /\bcurl\b[^|;\n]*\|\s*(?:sh|bash|zsh)\b/i, reason: "Blocked pipe-to-shell installer." },
  { pattern: /\bwget\b[^|;\n]*\|\s*(?:sh|bash|zsh)\b/i, reason: "Blocked pipe-to-shell installer." },
];

const LONG_RUNNING_PATTERNS = [
  /\bnpm\s+run\s+dev\b/i,
  /\bnpm\s+run\s+start\b/i,
  /\bpnpm\s+(?:run\s+)?dev\b/i,
  /\bpnpm\s+(?:run\s+)?start\b/i,
  /\byarn\s+dev\b/i,
  /\byarn\s+start\b/i,
  /\bbun\s+(?:run\s+)?dev\b/i,
  /\bbun\s+(?:run\s+)?start\b/i,
  /\bnext\s+dev\b/i,
  /\bvite\b(?:\s|$)/i,
  /\bexpo\s+start\b/i,
  /\btsc\b[^\n]*\s--watch\b/i,
  /\bjest\b[^\n]*\s--watch\b/i,
  /\bvitest\b[^\n]*\s--watch\b/i,
  /\bngrok\b/i,
  /\bcloudflared\b[^\n]*\btunnel\b/i,
  /\bnohup\b/i,
  /(?:^|[^&])&\s*$/i,
  /\bdisown\b/i,
];

const SECRET_PATTERNS = [
  { name: "GitHub token", pattern: /\bgh[pousr]_[A-Za-z0-9]{20,}\b/g },
  { name: "OpenAI style key", pattern: /\bsk-[A-Za-z0-9_-]{16,}\b/g },
  { name: "Bearer token", pattern: /\bBearer\s+[A-Za-z0-9._-]{20,}\b/gi },
  { name: "AWS access key", pattern: /\bAKIA[0-9A-Z]{16}\b/g },
  { name: "Private key block", pattern: /-----BEGIN [A-Z ]*PRIVATE KEY-----/g },
  { name: ".env assignment", pattern: /^(?:export\s+)?[A-Z0-9_]{2,}\s*=\s*.+$/gm },
];

const MCP_WRITE_ACTIONS = new Set([
  "add",
  "approve",
  "archive",
  "assign",
  "assignee",
  "assignment",
  "close",
  "comment",
  "create",
  "delete",
  "edit",
  "execute",
  "label",
  "merge",
  "move",
  "patch",
  "publish",
  "push",
  "remove",
  "request",
  "reopen",
  "review",
  "send",
  "submit",
  "transition",
  "update",
  "upload",
  "write",
]);

const MCP_READ_ACTIONS = new Set(["fetch", "find", "get", "list", "read", "search", "show"]);
const MCP_AMBIGUOUS_WRITE_ACTIONS = new Set(["comment", "review"]);
const MCP_HOST_IDENTIFIER_KEYS = ["tool", "tool_name", "type", "server", "server_name", "name"];
const MCP_ACTION_IDENTIFIER_KEYS = ["tool", "tool_name", "action", "method", "operation", "command"];
const MCP_WRITE_PAYLOAD_KEYS = ["content", "patch", "changes"];

const TDD_TEST_COMMAND_PATTERNS = [
  /\bnpm\s+(?:run\s+)?test\b/i,
  /\bpnpm\s+(?:run\s+)?test\b/i,
  /\bbun\s+(?:run\s+)?test\b/i,
  /\byarn\s+test\b/i,
  /\bvitest\b/i,
  /\bjest\b/i,
  /\bpytest\b/i,
  /\bgo\s+test\b/i,
  /\bcargo\s+test\b/i,
  /\bswift\s+test\b/i,
  /\bxcodebuild\b[^\n]*\btest\b/i,
  /\bmvn\b[^\n]*\btest\b/i,
  /\bgradle\b[^\n]*\btest\b/i,
];

const DEFAULT_TDD_PRODUCTION_PATHS = ["src/**", "app/**", "lib/**", "server/**", "api/**"];
const DEFAULT_TDD_TEST_PATHS = ["**/*.test.*", "**/*.spec.*", "tests/**"];
const AI_FLOW_REQUIRED_BRIEF_FIELDS = [
  "goal",
  "success_criteria",
  "current_state",
  "affected_modules",
  "contracts_and_invariants",
  "ubiquitous_language",
  "risks_and_edge_cases",
  "verification_loop",
  "out_of_scope",
];
const READ_ONLY_COMMAND_PATTERNS = [
  /^\s*(?:pwd|ls|find|rg|grep|sed|cat|head|tail|wc|nl|tree)\b/i,
  /^\s*git\s+(?:status|diff|show|grep|branch|log|rev-parse|ls-files)\b/i,
  /^\s*python3?\s+[^;\n]*\s(?:--help|-h)\s*$/i,
  /^\s*node\s+[^;\n]*\s(?:--help|-h)\s*$/i,
];

function run(command, args, options = {}) {
  return spawnSync(command, args, {
    cwd: options.cwd,
    input: options.input,
    encoding: "utf8",
    env: { ...process.env, ...(options.env || {}) },
  });
}

function readStdin() {
  return fs.readFileSync(0, "utf8");
}

function safeJsonParse(value, fallback = {}) {
  try {
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function trim(value) {
  return typeof value === "string" ? value.trim() : "";
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function redactSecrets(value) {
  return SECRET_PATTERNS.reduce(
    (redacted, { name, pattern }) =>
      name === ".env assignment" ? redacted : redacted.replace(pattern, `[REDACTED ${name}]`),
    value,
  );
}

function stringValues(value, keys) {
  if (!value || typeof value !== "object") {
    return [];
  }
  return keys.map((key) => value[key]).filter((item) => typeof item === "string");
}

function mcpHostIdentifiers(input) {
  return [input, input?.tool_input, input?.arguments, input?.metadata]
    .flatMap((value) => stringValues(value, MCP_HOST_IDENTIFIER_KEYS));
}

function mcpActionIdentifiers(input) {
  return [input, input?.tool_input, input?.arguments, input?.metadata]
    .flatMap((value) => stringValues(value, MCP_ACTION_IDENTIFIER_KEYS));
}

function identifierTokens(value) {
  return value.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
}

function identifierHasWrite(value) {
  const tokens = identifierTokens(value);
  const writes = tokens.filter((token) => MCP_WRITE_ACTIONS.has(token));
  const hasRead = tokens.some((token) => MCP_READ_ACTIONS.has(token));
  return writes.some((token) => !MCP_AMBIGUOUS_WRITE_ACTIONS.has(token)) || (writes.length > 0 && !hasRead);
}

export function normalizeInput(stdinText, env = process.env) {
  const input = safeJsonParse(stdinText, {});
  const cwd = trim(
    input.cwd ||
      input.directory ||
      input.worktree ||
      input.metadata?.cwd ||
      process.cwd(),
  );
  const command = trim(
    input.tool_input?.command ||
      input.command ||
      input.arguments ||
      input.metadata?.command ||
      input.pattern ||
      "",
  );
  const filePath = trim(
    input.tool_input?.file_path ||
      input.tool_input?.path ||
      input.path ||
      input.file ||
      input.metadata?.filePath ||
      input.metadata?.file ||
      "",
  );
  const toolName = trim(input.tool_name || input.tool || input.type || env.GUARDRAIL_TOOL_NAME || "");
  return {
    raw: input,
    cwd,
    command,
    filePath,
    toolName,
    event: env.GUARDRAIL_EVENT || "",
    tool: env.GUARDRAIL_TOOL || "",
  };
}

export function findRepoRoot(cwd) {
  const result = run("git", ["rev-parse", "--show-toplevel"], { cwd });
  if (result.status !== 0) {
    return null;
  }
  return trim(result.stdout);
}

export function resolveGitDir(repoRoot) {
  const result = run("git", ["rev-parse", "--git-dir"], { cwd: repoRoot });
  if (result.status !== 0) {
    return path.join(repoRoot, ".git");
  }
  const gitDir = trim(result.stdout);
  return path.isAbsolute(gitDir) ? gitDir : path.resolve(repoRoot, gitDir);
}

function hasHead(repoRoot) {
  return run("git", ["rev-parse", "--verify", "HEAD"], { cwd: repoRoot }).status === 0;
}

function fileExists(filePath) {
  try {
    fs.accessSync(filePath, fs.constants.R_OK);
    return true;
  } catch {
    return false;
  }
}

export function loadRepoManifest(repoRoot) {
  if (!repoRoot) {
    return null;
  }
  const manifestPath = path.join(repoRoot, ".agent-hooks.json");
  if (!fileExists(manifestPath)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  } catch {
    return null;
  }
}

function statusEntries(repoRoot) {
  const result = run("git", ["status", "--porcelain=1", "-z", "--untracked-files=all"], { cwd: repoRoot });
  if (result.status !== 0) {
    return [];
  }
  const entries = [];
  const parts = result.stdout.split("\0").filter(Boolean);
  for (let index = 0; index < parts.length; index += 1) {
    const entry = parts[index];
    const code = entry.slice(0, 2);
    let file = entry.slice(3);
    if (code.startsWith("R") || code.startsWith("C")) {
      const next = parts[index + 1];
      if (next) {
        file = next;
        index += 1;
      }
    }
    if (file) {
      entries.push({ code, file });
    }
  }
  return entries;
}

export function getChangedFiles(repoRoot) {
  const entries = statusEntries(repoRoot);
  return [...new Set(entries.map((entry) => entry.file))];
}

function getUntrackedFiles(repoRoot) {
  return statusEntries(repoRoot)
    .filter((entry) => entry.code === "??")
    .map((entry) => entry.file);
}

function hasStagedDiff(repoRoot) {
  return run("git", ["diff", "--cached", "--quiet", "--"], { cwd: repoRoot }).status !== 0;
}

export function getPreferredDiff(repoRoot) {
  if (!repoRoot) {
    return "";
  }
  if (hasStagedDiff(repoRoot)) {
    return run("git", ["diff", "--cached", "--no-color", "--unified=0", "--"], {
      cwd: repoRoot,
    }).stdout;
  }
  const args = ["diff", "--no-color", "--unified=0", "--"];
  if (!hasHead(repoRoot)) {
    return run("git", args, { cwd: repoRoot }).stdout;
  }
  return run("git", args, { cwd: repoRoot }).stdout;
}

function parseAddedLines(diffText) {
  const linesByFile = new Map();
  let currentFile = null;
  for (const line of diffText.split("\n")) {
    if (line.startsWith("+++ b/")) {
      currentFile = line.slice(6);
      if (!linesByFile.has(currentFile)) {
        linesByFile.set(currentFile, []);
      }
      continue;
    }
    if (!currentFile) {
      continue;
    }
    if (line.startsWith("+") && !line.startsWith("+++")) {
      linesByFile.get(currentFile).push(line.slice(1));
    }
  }
  return linesByFile;
}

function readFile(repoRoot, relativePath) {
  const absolutePath = path.join(repoRoot, relativePath);
  if (!fileExists(absolutePath)) {
    return "";
  }
  try {
    return fs.readFileSync(absolutePath, "utf8");
  } catch {
    return "";
  }
}

function globToRegExp(globPattern) {
  const escaped = globPattern
    .replace(/[.+^${}()|[\]\\]/g, "\\$&")
    .replace(/\*\*/g, ":::DOUBLE_STAR:::")
    .replace(/\*/g, "[^/]*")
    .replace(/:::DOUBLE_STAR:::/g, ".*");
  return new RegExp(`^${escaped}$`, "i");
}

function matchesAnyGlob(target, patterns) {
  return patterns.some((pattern) => globToRegExp(pattern).test(target));
}

function isCommandExplicitlyAllowed(command) {
  return /(?:user\s+asked|explicitly\s+requested|requested by user)/i.test(command);
}

function readPackageJson(repoRoot) {
  const packageJsonPath = path.join(repoRoot, "package.json");
  if (!fileExists(packageJsonPath)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
  } catch {
    return null;
  }
}

export function detectPackageManager(repoRoot) {
  const checks = [
    { file: "bun.lockb", value: "bun" },
    { file: "bun.lock", value: "bun" },
    { file: "pnpm-lock.yaml", value: "pnpm" },
    { file: "yarn.lock", value: "yarn" },
    { file: "package-lock.json", value: "npm" },
  ];
  for (const check of checks) {
    if (fileExists(path.join(repoRoot, check.file))) {
      return check.value;
    }
  }
  return "npm";
}

function detectRepoContext(repoRootOrCwd) {
  if (!repoRootOrCwd) {
    return {
      repoRoot: null,
      packageManager: null,
      packageJson: null,
      deps: {},
      depNames: [],
      hasAppJson: false,
      hasExpoConfig: false,
      hasIosDir: false,
      hasAndroidDir: false,
      hasSwiftFiles: false,
      isExpoRepo: false,
      isReactNativeRepo: false,
      isNativeAppleRepo: false,
      isNextRepo: false,
      isViteRepo: false,
      isWebRepo: false,
      isMobileRepo: false,
    };
  }

  const repoRoot = repoRootOrCwd;
  const packageJson = readPackageJson(repoRoot);
  const deps = {
    ...(packageJson?.dependencies || {}),
    ...(packageJson?.devDependencies || {}),
  };
  const depNames = Object.keys(deps);
  const hasAppJson = fileExists(path.join(repoRoot, "app.json"));
  const hasExpoConfig =
    fileExists(path.join(repoRoot, "app.config.js")) ||
    fileExists(path.join(repoRoot, "app.config.ts"));
  const hasIosDir = fileExists(path.join(repoRoot, "ios")) && fs.statSync(path.join(repoRoot, "ios")).isDirectory();
  const hasAndroidDir = fileExists(path.join(repoRoot, "android")) && fs.statSync(path.join(repoRoot, "android")).isDirectory();
  const hasSwiftFiles = run("find", [repoRoot, "-maxdepth", "3", "-name", "*.swift"], { cwd: repoRoot }).stdout.trim().length > 0;

  const isExpoRepo = depNames.includes("expo") || hasAppJson || hasExpoConfig;
  const isReactNativeRepo =
    depNames.includes("react-native") ||
    depNames.some((dep) => dep.startsWith("@react-navigation/")) ||
    depNames.some((dep) => dep.startsWith("@expo/"));
  const isNativeAppleRepo = hasIosDir || hasSwiftFiles;
  const isNextRepo = depNames.includes("next");
  const isViteRepo = depNames.includes("vite");
  const isWebRepo =
    isNextRepo ||
    isViteRepo ||
    depNames.some((dep) => /^(astro|nuxt|svelte|remix|gatsby|@angular\/)/.test(dep));
  const isMobileRepo = isExpoRepo || isReactNativeRepo || hasIosDir || hasAndroidDir || hasSwiftFiles;

  return {
    repoRoot,
    packageManager: detectPackageManager(repoRoot),
    packageJson,
    deps,
    depNames,
    hasAppJson,
    hasExpoConfig,
    hasIosDir,
    hasAndroidDir,
    hasSwiftFiles,
    isExpoRepo,
    isReactNativeRepo,
    isNativeAppleRepo,
    isNextRepo,
    isViteRepo,
    isWebRepo,
    isMobileRepo,
  };
}

function mergeRepoContexts(primaryContext, secondaryContext) {
  if (!primaryContext.repoRoot) {
    return secondaryContext;
  }
  if (!secondaryContext.repoRoot) {
    return primaryContext;
  }

  const chooseRepoRoot =
    secondaryContext.isMobileRepo && !primaryContext.isMobileRepo
      ? secondaryContext.repoRoot
      : secondaryContext.isWebRepo && !primaryContext.isWebRepo
        ? secondaryContext.repoRoot
        : primaryContext.repoRoot;

  const depNames = unique([...primaryContext.depNames, ...secondaryContext.depNames]);

  return {
    repoRoot: chooseRepoRoot,
    packageManager: primaryContext.packageManager || secondaryContext.packageManager,
    packageJson: primaryContext.packageJson || secondaryContext.packageJson,
    deps: { ...primaryContext.deps, ...secondaryContext.deps },
    depNames,
    hasAppJson: primaryContext.hasAppJson || secondaryContext.hasAppJson,
    hasExpoConfig: primaryContext.hasExpoConfig || secondaryContext.hasExpoConfig,
    hasIosDir: primaryContext.hasIosDir || secondaryContext.hasIosDir,
    hasAndroidDir: primaryContext.hasAndroidDir || secondaryContext.hasAndroidDir,
    hasSwiftFiles: primaryContext.hasSwiftFiles || secondaryContext.hasSwiftFiles,
    isExpoRepo: primaryContext.isExpoRepo || secondaryContext.isExpoRepo,
    isReactNativeRepo: primaryContext.isReactNativeRepo || secondaryContext.isReactNativeRepo,
    isNativeAppleRepo: primaryContext.isNativeAppleRepo || secondaryContext.isNativeAppleRepo,
    isNextRepo: primaryContext.isNextRepo || secondaryContext.isNextRepo,
    isViteRepo: primaryContext.isViteRepo || secondaryContext.isViteRepo,
    isWebRepo: primaryContext.isWebRepo || secondaryContext.isWebRepo,
    isMobileRepo: primaryContext.isMobileRepo || secondaryContext.isMobileRepo,
  };
}

function loadSkillRoutingIndex() {
  const indexPath = path.join(os.homedir(), ".agents", "manifests", "skill-routing-index.json");
  if (!fileExists(indexPath)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(indexPath, "utf8"));
  } catch {
    return null;
  }
}

const IOS_ROUTING_SKILLS = [
  "ios-development",
  "swiftui-pro",
  "swiftui-ui-patterns",
  "swiftui-view-refactor",
  "swift-concurrency-pro",
  "swiftdata-pro",
  "swift-testing-pro",
  "ios-debugger-agent",
  "ios-app-intents",
  "ios-memgraph-leaks",
  "ios-ettrace-performance",
  "swiftui-performance-audit",
  "swiftui-liquid-glass",
  "ios-app-store-compliance",
];
const IOS_ROUTING_SKILL_SET = new Set(IOS_ROUTING_SKILLS);
const DESIGN_ROUTING_SKILL = "frontend-design";
const SWIFT_EDIT_PATTERN = /\.swift$|\.xcodeproj|\.xcworkspace|Package\.swift/;
const UI_COMPONENT_EDIT_PATTERN = /(?:^|\/)(?:components|app|pages)\/.*\.(?:tsx|jsx|vue|svelte)$/i;
const UI_STYLE_EDIT_PATTERN = /\.(?:css|scss)$/i;

function stripCodeBlocks(text) {
  return text.replace(/```[\s\S]*?```/g, " ");
}

function classifyPromptIntent(promptText, context) {
  const prompt = stripCodeBlocks(promptText).toLowerCase();
  const has = (pattern) => pattern.test(prompt);
  const genericBuild = has(/\b(build|create|make|add|implement|ship|scaffold|prototype|fix|change|update|redesign|refresh|revamp)\b/);
  const review = has(/\b(review|audit|code review|look over|check my code)\b/);
  const advisory = has(/\b(what do you think|how can we|should we|thinking of|do you think|worth it|proposal)\b/);
  const planning = has(/\b(plan|roadmap|approach|design an approach|implementation plan)\b/);
  const routing = has(/\b(skill routing|routing algorithm|prompt router|agent-policy|agents\.md|guardrail|hook|skills? index|front matter|frontmatter)\b/);
  const explicitWeb = has(/\b(next\.js|nextjs|react|frontend|landing page|website|web app|browser|tailwind|css|html|sitemap|robots\.txt)\b/);
  const explicitMobile = has(/\b(mobile|react native|expo|ios|android|iphone|ipad|swiftui|xcode|native app|app store|testflight|simulator|emulator|eas)\b/);
  const explicitBackend = has(/\b(api|route|server|backend|database|schema|migration|service layer|rbac|tenant|observability|middleware)\b/);
  const uiNoun = has(/\b(ui|ux|page|screen|flow|dashboard|settings|profile|landing|hero|component|layout|interface|visual|website|web app)\b/);
  const redesign = has(/\b(redesign|refresh|improve existing|upgrade interface|revamp|polish existing)\b/);
  const designReference = has(/\b(feel like|inspired by|looks like|style of|linear|notion|stripe|mintlify|cursor|framer|figma|raycast|supabase|sentry|warp)\b/);
  const designPolish = has(/\b(polish|art direction|motion polish|high-end|premium|cinematic|refined)\b/);
  const greenfieldDesign = !redesign && uiNoun && has(/\b(build|create|make|new page|new interface|landing page|greenfield|hero)\b/);
  const security = has(/\b(security|auth|authentication|authorization|input validation|xss|sql injection|secret|privacy|cookie|gdpr|ccpa)\b/);
  const seo = has(/\b(seo|schema markup|robots\.txt|sitemap|crawlability|indexation)\b/);
  const compliance = has(/\b(privacy|cookies|tracking|terms|consumer|accessibility obligations|compliance)\b/);
  const uiAudit = has(/\b(ui review|review my ui|audit design|review ux|accessibility)\b/);
  const mapping = has(/\b(map the codebase|codebase map|understand the repo|navigate this codebase)\b/);
  const behaviorChanging = genericBuild || has(/\b(bug|defect|regression|test|failing|broken)\b/);

  let mode = "advisory";
  if (review) {
    mode = "review";
  } else if (genericBuild) {
    mode = "implementation";
  } else if (planning) {
    mode = "planning";
  } else if (advisory) {
    mode = "advisory";
  }

  const domains = new Set();
  if (routing) domains.add("agent-policy");
  if (explicitWeb) domains.add("web");
  if (explicitMobile) domains.add("mobile");
  if (explicitBackend) domains.add("backend");
  if (greenfieldDesign || redesign || designReference || designPolish || uiNoun) domains.add("design");
  if (security) domains.add("security");
  if (seo) domains.add("seo");
  if (compliance) domains.add("compliance");
  if (mapping) domains.add("mapping");

  return {
    prompt,
    mode,
    domains,
    genericBuild,
    behaviorChanging,
    review,
    advisory,
    planning,
    routing,
    explicitWeb,
    explicitMobile,
    explicitBackend,
    uiNoun,
    redesign,
    designReference,
    designPolish,
    greenfieldDesign,
    security,
    seo,
    compliance,
    uiAudit,
    mapping,
    expo: has(/\b(expo|eas|metro)\b/),
    reactNative: has(/\b(react native|rn|native module)\b/),
    ios: has(/\b(swift|swiftui|ios|xcode|app store|iphone|ipad|visionos|macos)\b/),
    appStore: has(/\b(app store|submission|review guideline|store review|testflight)\b/),
    reactPerformance: has(/\b(performance|bundle|bundle size|render perf|rsc|swr|react query|react performance)\b/),
    composition: has(/\b(compound component|render prop|slot api|component api|reusable primitive|boolean prop)\b/),
    repoWeb: Boolean(context?.isWebRepo),
    repoMobile: Boolean(context?.isMobileRepo),
  };
}

function selectFoundationSkills(intent) {
  const skills = new Set();
  if (["implementation", "review", "planning"].includes(intent.mode) || intent.behaviorChanging || intent.routing) {
    skills.add("testing-strategies");
  }
  return skills;
}

function selectDomainSkills(intent, context) {
  const tags = new Set();
  const skills = new Set();
  const secondarySkills = new Set();
  const subagents = new Set();
  const notes = [];

  if (intent.routing) {
    tags.add("agent-policy");
    tags.add("routing");
  }
  if (intent.review) {
    tags.add("review");
    subagents.add("code-reviewer");
    notes.push("Default to review mode: findings first, summary second.");
  }
  if (intent.mapping) {
    tags.add("mapping");
    skills.add("cartographer");
    subagents.add("cartographer");
  }

  if (context?.repoRoot) {
    if (context.isMobileRepo && !intent.explicitWeb) {
      tags.add("repo-mobile");
      notes.push("Repo context suggests mobile; token-saving mode still requires prompt or task alignment before loading mobile skills.");
    }
    if (context.isWebRepo && !intent.explicitMobile) {
      tags.add("repo-web");
      notes.push("Repo context suggests web; token-saving mode still requires prompt or task alignment before loading web skills.");
    }
  }

  const shouldTreatAsWeb =
    intent.explicitWeb ||
    (!intent.explicitMobile && context?.isWebRepo && (intent.genericBuild || intent.uiNoun));
  if (shouldTreatAsWeb) {
    tags.add("web");
    skills.add("frontend-web-development");
    subagents.add("frontend-engineer");
  }

  if (intent.explicitBackend) {
    tags.add("backend");
    skills.add("backend-architecture");
    subagents.add("backend-architect");
  }

  if (intent.security) {
    tags.add("security");
    skills.add("security-vulnerability-mitigation");
    subagents.add("security-auditor");
  }

  if (intent.seo) {
    tags.add("seo");
    skills.add("technical-seo");
    subagents.add("compliance-seo-auditor");
  }

  if (intent.compliance) {
    tags.add("compliance");
    skills.add("website-compliance");
    subagents.add("compliance-seo-auditor");
  }

  if (intent.uiAudit) {
    tags.add("ui-audit");
    skills.add("web-design-guidelines");
    subagents.add("ui-auditor");
  }

  if ((shouldTreatAsWeb && intent.reactPerformance) || /\b(next\.js|nextjs)\b/.test(intent.prompt)) {
    tags.add("react-performance");
    skills.add("vercel-react-best-practices");
  }

  if (intent.composition) {
    tags.add("composition");
    skills.add("vercel-composition-patterns");
  }

  const shouldTreatAsMobile =
    intent.explicitMobile ||
    (!intent.explicitWeb && context?.isMobileRepo && (intent.genericBuild || intent.uiNoun));
  if (intent.ios || (shouldTreatAsMobile && context?.isNativeAppleRepo && !intent.reactNative && !intent.expo)) {
    tags.add("ios");
    skills.add("ios-development");
    subagents.add("mobile-engineer");
  }

  if (intent.appStore) {
    tags.add("app-store");
    skills.add("ios-app-store-compliance");
    subagents.add("mobile-engineer");
  }

  if (intent.reactNative || intent.expo || (shouldTreatAsMobile && (context?.isExpoRepo || context?.isReactNativeRepo))) {
    tags.add("react-native");
    skills.add("vercel-react-native-skills");
    subagents.add("mobile-engineer");
  }

  if (intent.expo) {
    tags.add("expo");
    skills.add("expo-docs");
    subagents.add("mobile-engineer");
  }

  if (intent.greenfieldDesign || intent.redesign) {
    if (intent.greenfieldDesign) {
      tags.add("greenfield-design");
    }
    if (intent.redesign) {
      tags.add("redesign");
    }
    skills.add("frontend-design");
    subagents.add("design-engineer");
  }

  if (intent.designPolish) {
    tags.add("design-polish");
    if (skills.has("frontend-design")) {
      subagents.add("design-engineer");
    }
  }

  if (intent.designReference) {
    tags.add("design-reference");
    secondarySkills.add("design-md-gallery");
    if (skills.has("frontend-design")) {
      subagents.add("design-engineer");
      notes.push("Use the DESIGN.md gallery only as a secondary reference layer after the primary design mode.");
    }
  }

  return { tags, skills, secondarySkills, subagents, notes };
}

function enforceSkillConstraints(selection, intent) {
  const hasPrimaryDesign = selection.skills.has("frontend-design");

  if (!hasPrimaryDesign) {
    if (selection.secondarySkills.delete("design-md-gallery")) {
      selection.notes.push("Token-saving mode active: omitted weak secondary design matches without a primary design task.");
    }
    selection.subagents.delete("design-engineer");
  }

  if (intent.mode === "advisory") {
    const allowed = new Set(["cartographer", "search-first", "effective-agent-skills"]);
    for (const skill of [...selection.skills]) {
      if (!allowed.has(skill) && !intent.security && !intent.seo && !intent.compliance) {
        selection.skills.delete(skill);
      }
    }
  }

  return selection;
}

function estimateRoutingCost(skills, index) {
  if (!index || !Array.isArray(index.skills)) {
    return 0;
  }
  const entries = new Map(index.skills.map((entry) => [entry.name, entry]));
  return [...skills].reduce((total, skill) => total + (entries.get(skill)?.tokens?.skill_chars || 0), 0);
}

function classifyPrompt(promptText, repoContext = null) {
  const context = repoContext || detectRepoContext(null);
  const index = loadSkillRoutingIndex();
  const intent = classifyPromptIntent(promptText, context);
  const foundationSkills = selectFoundationSkills(intent);
  const domainSelection = selectDomainSkills(intent, context);
  const skills = new Set([...foundationSkills, ...domainSelection.skills]);
  const selection = enforceSkillConstraints({
    tags: domainSelection.tags,
    skills,
    secondarySkills: domainSelection.secondarySkills,
    subagents: domainSelection.subagents,
    notes: domainSelection.notes,
  }, intent);

  if (selection.skills.size > 0 && intent.mode === "advisory") {
    selection.notes.push("Advisory prompt: skipped coding and testing skills unless a stronger trigger appears.");
  } else if (selection.skills.size > 0) {
    const estimated = estimateRoutingCost(selection.skills, index);
    if (estimated > 0 && (intent.routing || selection.tags.has("greenfield-design") || selection.tags.has("redesign"))) {
      selection.notes.push(`Token-saving mode active: selected ${selection.skills.size} skills (~${estimated} chars of skill guidance if loaded).`);
    }
  }

  return {
    repoContext: context.repoRoot
      ? {
          repoRoot: context.repoRoot,
          isWebRepo: context.isWebRepo,
          isMobileRepo: context.isMobileRepo,
          isExpoRepo: context.isExpoRepo,
          isReactNativeRepo: context.isReactNativeRepo,
          isNativeAppleRepo: context.isNativeAppleRepo,
          isNextRepo: context.isNextRepo,
          isViteRepo: context.isViteRepo,
        }
      : null,
    tags: unique([...selection.tags]),
    domains: unique([...intent.domains]),
    skills: unique([...selection.skills]),
    secondarySkills: unique([...selection.secondarySkills]),
    subagents: unique([...selection.subagents]),
    notes: unique(selection.notes),
  };
}

function formatPromptRouting(result) {
  if (result.skills.length === 0 && result.secondarySkills.length === 0 && result.subagents.length === 0) {
    return "";
  }
  const lines = [];
  lines.push("Prompt routing hint:");
  if (result.tags.length > 0) {
    lines.push(`- likely task tags: ${result.tags.join(", ")}`);
  }
  if (result.repoContext) {
    const contextFlags = [
      result.repoContext.isMobileRepo ? "mobile-repo" : "",
      result.repoContext.isExpoRepo ? "expo" : "",
      result.repoContext.isReactNativeRepo ? "react-native" : "",
      result.repoContext.isNativeAppleRepo ? "native-apple" : "",
      result.repoContext.isWebRepo ? "web-repo" : "",
      result.repoContext.isNextRepo ? "next" : "",
      result.repoContext.isViteRepo ? "vite" : "",
    ].filter(Boolean);
    if (contextFlags.length > 0) {
      lines.push(`- repo signals: ${contextFlags.join(", ")}`);
    }
  }
  if (result.skills.length > 0) {
    lines.push(`- load skills: ${result.skills.join(", ")}`);
  }
  if (result.secondarySkills.length > 0) {
    lines.push(`- secondary skills only after the primary mode: ${result.secondarySkills.join(", ")}`);
  }
  if (result.subagents.length > 0) {
    lines.push(`- delegation candidates if split work helps: ${result.subagents.join(", ")}`);
  }
  for (const note of result.notes) {
    lines.push(`- note: ${note}`);
  }
  return lines.join("\n");
}

function runRepoTask(repoRoot, task) {
  if (!task) {
    return { ok: true, command: null, stdout: "", stderr: "" };
  }
  let argv;
  if (task.runner === "command" && Array.isArray(task.argv) && task.argv.length > 0) {
    argv = task.argv;
  } else if (task.runner === "script" && task.name) {
    const packageManager = detectPackageManager(repoRoot);
    if (packageManager === "pnpm") {
      argv = ["pnpm", "run", task.name];
    } else if (packageManager === "yarn") {
      argv = ["yarn", task.name];
    } else if (packageManager === "bun") {
      argv = ["bun", "run", task.name];
    } else {
      argv = ["npm", "run", task.name, "--silent"];
    }
  } else {
    return { ok: true, command: null, stdout: "", stderr: "" };
  }
  const [command, ...args] = argv;
  const result = run(command, args, { cwd: repoRoot });
  return {
    ok: result.status === 0,
    command: argv.join(" "),
    stdout: trim(result.stdout),
    stderr: trim(result.stderr),
  };
}

function parseSections(markdownText) {
  const sections = new Map();
  if (!markdownText) {
    return sections;
  }
  let current = null;
  for (const rawLine of markdownText.split("\n")) {
    const heading = rawLine.match(/^##\s+(.+?)\s*$/);
    if (heading) {
      current = heading[1].trim().toLowerCase();
      sections.set(current, []);
      continue;
    }
    if (current) {
      sections.get(current).push(rawLine);
    }
  }
  return sections;
}

function sectionHasContent(sections, sectionName) {
  const lines = sections.get(sectionName.toLowerCase()) || [];
  const content = lines
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => line !== "- ..." && line !== "...");
  return content.length > 0;
}

function notePaths(repoRoot) {
  const gitDir = resolveGitDir(repoRoot);
  const notesDir = path.join(gitDir, "agent-notes");
  return {
    notesDir,
    prSummary: path.join(notesDir, "pr-summary.md"),
    changeNote: path.join(notesDir, "change-note.md"),
  };
}

function readNotes(repoRoot) {
  const paths = notePaths(repoRoot);
  return {
    paths,
    prSummaryText: fileExists(paths.prSummary) ? fs.readFileSync(paths.prSummary, "utf8") : "",
    changeNoteText: fileExists(paths.changeNote) ? fs.readFileSync(paths.changeNote, "utf8") : "",
  };
}

function aiFlowStatePath(repoRoot) {
  return path.join(resolveGitDir(repoRoot), "agent-notes", "ai-flow-state.json");
}

function defaultAiFlowState() {
  return {
    version: 1,
    mode: "unset",
    modeSource: "missing",
    taskId: "",
    sessionId: "",
    updatedAt: "",
    promptHash: "",
    taskIntent: "unknown",
    briefStatus: "missing",
    requiredBriefFields: AI_FLOW_REQUIRED_BRIEF_FIELDS,
    completedBriefFields: [],
    brief: {},
    briefChecksum: "",
    funModeReason: "",
    routedSkills: [],
    routedSecondarySkills: [],
    promptDomains: [],
  };
}

function readAiFlowState(repoRoot) {
  if (!repoRoot) {
    return defaultAiFlowState();
  }
  const state = readJsonOrNull(aiFlowStatePath(repoRoot)) || {};
  return {
    ...defaultAiFlowState(),
    ...state,
    requiredBriefFields: Array.isArray(state.requiredBriefFields) && state.requiredBriefFields.length > 0
      ? state.requiredBriefFields
      : AI_FLOW_REQUIRED_BRIEF_FIELDS,
    completedBriefFields: Array.isArray(state.completedBriefFields) ? state.completedBriefFields : [],
    routedSkills: Array.isArray(state.routedSkills) ? state.routedSkills : [],
    routedSecondarySkills: Array.isArray(state.routedSecondarySkills) ? state.routedSecondarySkills : [],
    promptDomains: Array.isArray(state.promptDomains) ? state.promptDomains : [],
  };
}

function writeAiFlowState(repoRoot, state) {
  const filePath = aiFlowStatePath(repoRoot);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(state, null, 2)}\n`, "utf8");
}

function hashPrompt(prompt) {
  return crypto.createHash("sha256").update(prompt || "").digest("hex");
}

function hashText(value) {
  return crypto.createHash("sha256").update(value || "").digest("hex");
}

function computeBriefChecksum(state) {
  const payload = {
    mode: state.mode,
    promptHash: state.promptHash,
    brief: state.brief || {},
  };
  return hashText(JSON.stringify(payload));
}

function computeBriefStatusFromState(state) {
  if (state.mode !== "serious") {
    return state.briefStatus || "missing";
  }
  const required = Array.isArray(state.requiredBriefFields) ? state.requiredBriefFields : AI_FLOW_REQUIRED_BRIEF_FIELDS;
  const brief = state.brief && typeof state.brief === "object" ? state.brief : {};
  const completed = required.filter((field) => typeof brief[field] === "string" && brief[field].trim() !== "");
  if (completed.length === 0) {
    return "missing";
  }
  if (completed.length < required.length) {
    return "partial";
  }
  if (!state.briefChecksum || state.briefChecksum !== computeBriefChecksum({ ...state, brief })) {
    return "partial";
  }
  return "complete";
}

function extractPromptMode(promptText) {
  const match = trim(promptText).match(/^\/(serious|fun)\b/i);
  return match ? match[1].toLowerCase() : "";
}

function stripModeCommand(promptText) {
  return trim(promptText).replace(/^\/(?:serious|fun)\b\s*/i, "");
}

function computeBriefStatus(requiredFields, completedFields) {
  const completed = new Set(completedFields);
  const count = requiredFields.filter((field) => completed.has(field)).length;
  if (count === 0) {
    return "missing";
  }
  if (count < requiredFields.length) {
    return "partial";
  }
  return "complete";
}

function formatAiFlowSummary(state) {
  if (state.mode === "unset") {
    return [
      "AI flow gate: choose `/serious` or `/fun` before implementation.",
      "`/serious` = production/interview flow with an interview and task brief before edits.",
      "`/fun` = relaxed experimentation with safety gates only.",
    ].join("\n");
  }
  if (state.mode === "fun") {
    return "AI flow gate: `/fun` mode active. Prompt-quality and TDD pressure are relaxed; safety gates remain active.";
  }
  const missing = state.requiredBriefFields.filter((field) => !state.completedBriefFields.includes(field));
  if (state.briefStatus !== "complete") {
    return [
      "AI flow gate: `/serious` mode active. Interview the user before coding and complete the task brief before edits.",
      `Missing brief fields: ${missing.join(", ")}`,
      "Ask focused questions covering goal, success criteria, current state, affected modules, contracts, glossary terms, risks, verification, and out of scope.",
    ].join("\n");
  }
  return "AI flow gate: `/serious` mode active with a completed task brief. Proceed with small verified changes.";
}

function evaluateAiFlowPrompt(repoRoot, normalized) {
  const rawPrompt = trim(normalized.raw.prompt || normalized.raw.message?.system || normalized.raw.message || "");
  const selectedMode = extractPromptMode(rawPrompt);
  const promptWithoutMode = stripModeCommand(rawPrompt);
  const context = mergeRepoContexts(
    detectRepoContext(repoRoot),
    detectRepoContext(normalized.cwd),
  );
  const intent = classifyPromptIntent(promptWithoutMode || rawPrompt, context);
  let state = readAiFlowState(repoRoot);

  if (selectedMode) {
    const promptHash = hashPrompt(rawPrompt);
    state = {
      ...defaultAiFlowState(),
      mode: selectedMode,
      modeSource: "prompt-command",
      taskId: hashText(`${selectedMode}:${promptHash}`).slice(0, 16),
      sessionId: normalized.raw.session_id || state.sessionId || "",
      updatedAt: new Date().toISOString(),
      promptHash,
      taskIntent: intent.mode,
      briefStatus: selectedMode === "fun" ? "not_required" : "missing",
      requiredBriefFields: AI_FLOW_REQUIRED_BRIEF_FIELDS,
      completedBriefFields: [],
      brief: {},
      briefChecksum: "",
      funModeReason: selectedMode === "fun" ? "User selected relaxed experimentation mode." : "",
    };
  } else if (state.mode === "serious" || state.mode === "fun") {
    state = {
      ...state,
      sessionId: normalized.raw.session_id || state.sessionId || "",
      updatedAt: new Date().toISOString(),
      promptHash: hashPrompt(rawPrompt),
      taskIntent: intent.mode,
    };
  } else {
    state = {
      ...defaultAiFlowState(),
      updatedAt: new Date().toISOString(),
      promptHash: hashPrompt(rawPrompt),
      taskIntent: intent.mode,
    };
  }

  if (state.mode === "serious") {
    state.briefStatus = computeBriefStatusFromState(state);
  }

  if (repoRoot) {
    writeAiFlowState(repoRoot, state);
  }

  return {
    blocked: false,
    aiFlow: state,
    summary: formatAiFlowSummary(state),
  };
}

function isLikelyReadOnlyCommand(command) {
  return READ_ONLY_COMMAND_PATTERNS.some((pattern) => pattern.test(command || ""));
}

function evaluateAiFlowPreflight(repoRoot, normalized) {
  if (!repoRoot || isLikelyReadOnlyCommand(normalized.command)) {
    return { blocked: false };
  }
  const state = readAiFlowState(repoRoot);
  if (state.mode === "fun") {
    return { blocked: false };
  }
  if (state.mode !== "serious") {
    return {
      blocked: true,
      reason: "AI flow gate blocked mutation: choose `/serious` or `/fun` before implementation.",
    };
  }
  if (computeBriefStatusFromState(state) !== "complete") {
    return {
      blocked: true,
      reason: "AI flow gate blocked mutation: `/serious` mode requires a completed task brief before edits. Ask focused questions and fill the missing fields first.",
    };
  }
  return { blocked: false };
}

function hasVerificationEvidence(prSections, changeSections) {
  if (sectionHasContent(prSections, "tests")) {
    return true;
  }
  if (sectionHasContent(changeSections, "verification")) {
    return true;
  }
  const authLines = changeSections.get("auth/validation") || [];
  return authLines.some((line) => /\b(test|tested|verify|verified|validated|ran)\b/i.test(line));
}

export function classifyChanges(repoRoot, manifest = null) {
  const changedFiles = getChangedFiles(repoRoot);
  const packageJson = readPackageJson(repoRoot);
  const schemaPatterns = manifest?.schema?.paths || DEFAULT_SCHEMA_PATHS;
  const docsPatterns = manifest?.docs?.paths || DEFAULT_DOCS_PATHS;
  const isWebRepo =
    manifest?.web?.enabled === true ||
    Boolean(
      packageJson &&
        Object.keys({
          ...(packageJson.dependencies || {}),
          ...(packageJson.devDependencies || {}),
        }).some((dep) => /^(next|react|vite|vue|svelte|nuxt|astro|remix|@angular\/)/.test(dep)),
    );
  const schemaFiles = changedFiles.filter((file) => matchesAnyGlob(file, schemaPatterns));
  const docsFiles = changedFiles.filter(
    (file) =>
      matchesAnyGlob(file, docsPatterns) ||
      /(?:^|\/)(openapi|schema|types?|config)(?:\/|$)/i.test(file),
  );
  const backendAuthSensitiveFiles = changedFiles.filter((file) =>
    /(?:^|\/)(app\/api|pages\/api|api|routes?|controllers?|middleware|auth|session|polic(?:y|ies)|permissions?|rbac|acl)(?:\/|$)|route\.[tj]sx?$/i.test(file),
  );
  const webComplianceFiles = isWebRepo
    ? changedFiles.filter((file) =>
        /(?:cookie|consent|analytics|tracking|checkout|form|login|signup|auth|privacy|terms|marketing|banner|modal|ui)/i.test(file),
      )
    : [];
  const sharedLogicFiles = changedFiles.filter((file) =>
    /(?:^|\/)(lib|utils|shared|core|services|hooks)(?:\/|$)/i.test(file),
  );
  return {
    changedFiles,
    schemaFiles,
    docsFiles,
    backendAuthSensitiveFiles,
    webComplianceFiles,
    sharedLogicFiles,
    isWebRepo,
  };
}

function createFinding(level, file, message) {
  return { level, file, message };
}

export function evaluateDangerousCommand(command, manifest = null) {
  const customCommands = manifest?.protect?.commands || [];
  const patterns = [
    ...DANGEROUS_PATTERNS,
    ...customCommands.map((value) => ({
      pattern: new RegExp(value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"),
      reason: `Blocked manifest-protected command: ${value}`,
    })),
  ];
  for (const entry of patterns) {
    if (entry.pattern.test(command)) {
      return { blocked: true, reason: entry.reason };
    }
  }
  return { blocked: false };
}

export function evaluateLongRunning(command) {
  if (!command || isCommandExplicitlyAllowed(command)) {
    return { blocked: false };
  }
  for (const pattern of LONG_RUNNING_PATTERNS) {
    if (pattern.test(command)) {
      return { blocked: true, reason: "Blocked long-running process start unless explicitly requested." };
    }
  }
  return { blocked: false };
}

function isFunMode(repoRoot) {
  return repoRoot ? readAiFlowState(repoRoot).mode === "fun" : false;
}

export function evaluateSupplyChainCommand(command, repoRoot = null) {
  if (!command) {
    return { blocked: false };
  }
  const state = repoRoot ? readAiFlowState(repoRoot) : defaultAiFlowState();
  if (state.mode === "fun" || state.dependencyWorkAllowed === true) {
    return { blocked: false };
  }

  // Narrow allowlist for update-agents workflow — exact known-safe version-check commands.
  // This ensures the update-agents skill can check versions without opening arbitrary npm view usage.
  // Patterns match both bare commands and the documented update-agents snippets which wrap each
  // npm view in echo "=== LABEL ===" && ... 2>/dev/null. The echo prefix and stderr redirect are
  // harmless decorations; the core constraint (exact package + version subcommand, no chaining)
  // is enforced by ^ and $ anchors and the literal package/version tokens.
  //
  // The echo label character class [A-Za-z0-9 =()\-_.]+ is intentionally restrictive:
  // it excludes $, backticks, backslashes, ;, |, &, <>, {}, [], !, #, *, ? and other
  // shell metacharacters to prevent command substitution injection via the echo prefix.
  const UPDATE_AGENTS_ALLOWLIST = [
    /^(?:echo\s+"[A-Za-z0-9 =()\-_.]+"\s*&&\s+)?npm\s+view\s+@earendil-works\/pi-coding-agent\s+version(?:\s+2>\/dev\/null)?$/i,
    /^(?:echo\s+"[A-Za-z0-9 =()\-_.]+"\s*&&\s+)?npm\s+view\s+@openai\/codex\s+version(?:\s+2>\/dev\/null)?$/i,
    /^(?:echo\s+"[A-Za-z0-9 =()\-_.]+"\s*&&\s+)?npm\s+view\s+command-code\s+version(?:\s+2>\/dev\/null)?$/i,
  ];
  if (UPDATE_AGENTS_ALLOWLIST.some((pattern) => pattern.test(command.trim()))) {
    return { blocked: false };
  }

  const patterns = [
    /\bnpx\b/i,
    /\bpnpm\s+dlx\b/i,
    /\bbunx\b/i,
    /\buvx\b/i,
    /\bnpm\s+view\b/i,
    /\bnpm\s+outdated\b/i,
    /\bpnpm\s+outdated\b/i,
    /\bbun\s+outdated\b/i,
    /\bnpm-check-updates\b/i,
    /@[Ll]atest\b/,
    /\bcurl\b[^|;\n]*\|\s*(?:sh|bash|zsh)\b/i,
  ];
  if (patterns.some((pattern) => pattern.test(command))) {
    return { blocked: true, reason: "Blocked supply-chain command unless dependency work is explicitly allowed." };
  }
  return { blocked: false };
}

export function evaluateProtectedPath(filePath, repoRoot, manifest = null) {
  if (!filePath) {
    return { blocked: false };
  }
  const relativeFile = repoRoot && path.isAbsolute(filePath) ? path.relative(repoRoot, filePath) : filePath;
  const protectedPatterns = [...DEFAULT_PROTECTED_FILES, ...(manifest?.protect?.files || [])];
  const absoluteProtected = [
    path.join(os.homedir(), ".codex", "config.toml"),
    path.join(os.homedir(), ".cursor", "cli-config.json"),
    path.join(os.homedir(), ".cursor", "mcp.json"),
    path.join(os.homedir(), ".config", "opencode", "opencode.json"),
    path.join(os.homedir(), ".codex", "auth.json"),
  ];
  if (absoluteProtected.includes(path.resolve(filePath))) {
    return { blocked: true, reason: `Blocked protected config edit: ${filePath}` };
  }
  if (
    matchesAnyGlob(relativeFile, protectedPatterns) ||
    matchesAnyGlob(filePath, protectedPatterns) ||
    matchesAnyGlob(path.basename(filePath), protectedPatterns)
  ) {
    return { blocked: true, reason: `Blocked protected file edit: ${relativeFile}` };
  }
  return { blocked: false };
}

function extractPathCandidates(command) {
  if (!command) {
    return [];
  }
  const matches = command.match(/(?:~\/|\/|\.\.?\/)[^\s"'`|;]+|(?:^|\s)(\.[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._/-]+)?)/g) || [];
  return matches
    .map((value) => value.trim())
    .map((value) => value.replace(/^['"`]|['"`]$/g, ""))
    .filter(Boolean);
}

export function evaluateProtectedPathInCommand(command, cwd, repoRoot, manifest = null) {
  if (isLikelyReadOnlyCommand(command)) {
    return { blocked: false };
  }
  const candidates = extractPathCandidates(command);
  for (const candidate of candidates) {
    const expanded = candidate.startsWith("~/")
      ? path.join(os.homedir(), candidate.slice(2))
      : path.isAbsolute(candidate)
        ? candidate
        : path.resolve(cwd, candidate);
    const result = evaluateProtectedPath(expanded, repoRoot, manifest);
    if (result.blocked) {
      return result;
    }
  }
  return { blocked: false };
}

export function scanSecrets(repoRoot) {
  const diffText = getPreferredDiff(repoRoot);
  const untrackedFiles = getUntrackedFiles(repoRoot);
  const findings = [];
  const sources = [];
  if (diffText) {
    sources.push({ file: "diff", text: diffText });
  }
  for (const relativeFile of untrackedFiles) {
    sources.push({ file: relativeFile, text: readFile(repoRoot, relativeFile) });
  }
  for (const source of sources) {
    for (const entry of SECRET_PATTERNS) {
      const matches = source.text.match(entry.pattern);
      if (!matches) {
        continue;
      }
      if (entry.name === ".env assignment" && !/\.env/i.test(source.file)) {
        continue;
      }
      findings.push(createFinding("block", source.file, `${entry.name} detected in changed content.`));
    }
  }
  return findings;
}

export function scanSecurityCode(repoRoot, classification) {
  const diffText = getPreferredDiff(repoRoot);
  const addedLinesByFile = parseAddedLines(diffText);
  for (const relativeFile of getUntrackedFiles(repoRoot)) {
    const text = readFile(repoRoot, relativeFile);
    addedLinesByFile.set(relativeFile, text.split("\n"));
  }
  const findings = [];
  for (const [relativeFile, addedLines] of addedLinesByFile.entries()) {
    const addedText = addedLines.join("\n");
    const fullText = readFile(repoRoot, relativeFile);
    if (/\bexec\s*\(/.test(addedText) || /\bspawn\s*\([^)]*,\s*\{[^}]*shell\s*:\s*true/i.test(addedText)) {
      findings.push(createFinding("block", relativeFile, "Possible shell execution injection pattern in changed code."));
    }
    if (/(?:query|execute|raw)\s*\(\s*`[^`]*\$\{/.test(addedText) || /(?:query|execute|raw)\s*\(\s*["'][^"']*\+/.test(addedText)) {
      findings.push(createFinding("block", relativeFile, "Possible SQL string concatenation in changed code."));
    }
    if (/dangerouslySetInnerHTML/.test(addedText) && !/(DOMPurify|sanitize|sanitise)/i.test(fullText)) {
      findings.push(createFinding("block", relativeFile, "Unsafe HTML rendering added without a nearby sanitizer."));
    }
    if (
      classification.backendAuthSensitiveFiles.includes(relativeFile) &&
      /(export\s+async\s+function\s+(GET|POST|PUT|PATCH|DELETE)|router\.|app\.(get|post|put|patch|delete))/i.test(addedText) &&
      !/(zod|schema|validate|auth|authorize|permission|rbac|requireAuth|requireUser|ctx\.auth|session)/i.test(fullText)
    ) {
      findings.push(createFinding("block", relativeFile, "Backend entrypoint changed without obvious validation or authorization markers."));
    }
    if (/(console\.log|logger\.(info|warn|error|debug)|log\()/.test(addedText) && /(email|password|token|secret|ssn|phone)/i.test(addedText)) {
      findings.push(createFinding("advisory", relativeFile, "Possible PII or secret-bearing log statement added."));
    }
    if (/Access-Control-Allow-Origin["']?\s*[:=]\s*["']\*["']/.test(addedText) || /cors\([^)]*origin\s*:\s*["']\*["']/.test(addedText)) {
      findings.push(createFinding("advisory", relativeFile, "Suspicious broad CORS configuration added."));
    }
  }
  return findings;
}

function resolveRelativeRepoFile(repoRoot, filePath) {
  const trimmed = trim(filePath);
  if (!trimmed) {
    return "";
  }
  if (!repoRoot) {
    return trimmed;
  }
  const absolute = path.isAbsolute(trimmed) ? trimmed : path.resolve(repoRoot, trimmed);
  const relative = path.relative(repoRoot, absolute);
  if (relative.startsWith("..")) {
    return trimmed;
  }
  return relative.split(path.sep).join("/");
}

function collectEditedFilesForRouting(repoRoot, normalized, classification) {
  const files = new Set(classification?.changedFiles || []);
  const candidates = [
    normalized.filePath,
    normalized.raw.tool_input?.file_path,
    normalized.raw.tool_input?.path,
    normalized.raw.path,
    normalized.raw.file,
    normalized.raw.metadata?.filePath,
    normalized.raw.metadata?.file,
  ];
  for (const candidate of candidates) {
    const relative = resolveRelativeRepoFile(repoRoot, candidate);
    if (relative) {
      files.add(relative);
    }
  }
  return [...files];
}

function hasLoadedRoutingSkill(routedSkills, allowedSkills) {
  return routedSkills.some((skill) => allowedSkills.has(skill));
}

function isSwiftRelatedEdit(relativeFile) {
  return SWIFT_EDIT_PATTERN.test(relativeFile);
}

function isUiRoutingEdit(relativeFile) {
  return UI_COMPONENT_EDIT_PATTERN.test(relativeFile) || UI_STYLE_EDIT_PATTERN.test(relativeFile);
}

function persistPromptRouting(repoRoot, normalized, routing) {
  if (!repoRoot || !routing) {
    return;
  }
  const state = readAiFlowState(repoRoot);
  const prompt = trim(normalized.raw.prompt || normalized.raw.message?.system || "");
  writeAiFlowState(repoRoot, {
    ...state,
    sessionId: normalized.raw.session_id || state.sessionId || "",
    updatedAt: new Date().toISOString(),
    promptHash: prompt ? hashPrompt(prompt) : state.promptHash,
    routedSkills: routing.skills || [],
    routedSecondarySkills: routing.secondarySkills || [],
    promptDomains: routing.domains || [],
  });
}

function scanSkillRouting(repoRoot, normalized, classification) {
  const findings = [];
  if (!repoRoot) {
    return findings;
  }
  const state = readAiFlowState(repoRoot);
  const routedSkills = unique([
    ...(state.routedSkills || []),
    ...(state.routedSecondarySkills || []),
  ]);
  const designIntent = (state.promptDomains || []).includes("design");
  const editedFiles = collectEditedFilesForRouting(repoRoot, normalized, classification);
  for (const relativeFile of editedFiles) {
    if (isSwiftRelatedEdit(relativeFile) && !hasLoadedRoutingSkill(routedSkills, IOS_ROUTING_SKILL_SET)) {
      findings.push(createFinding(
        "advisory",
        relativeFile,
        `skill-routing: edited .swift files without an iOS skill loaded (expected one of: ${IOS_ROUTING_SKILLS.join(", ")})`,
      ));
    }
    if (
      isUiRoutingEdit(relativeFile) &&
      designIntent &&
      !routedSkills.includes(DESIGN_ROUTING_SKILL)
    ) {
      findings.push(createFinding(
        "advisory",
        relativeFile,
        "skill-routing: edited UI file during design task without frontend-design skill loaded",
      ));
    }
  }
  return findings;
}

export function scanCodeQuality(repoRoot, classification) {
  const diffText = getPreferredDiff(repoRoot);
  const addedLinesByFile = parseAddedLines(diffText);
  for (const relativeFile of getUntrackedFiles(repoRoot)) {
    addedLinesByFile.set(relativeFile, readFile(repoRoot, relativeFile).split("\n"));
  }
  const findings = [];
  for (const [relativeFile, addedLines] of addedLinesByFile.entries()) {
    const fullText = readFile(repoRoot, relativeFile);
    const addedText = addedLines.join("\n");
    if (/export\s+(?:type\s+)?(?:const|function|class|interface|type).*\bany\b/.test(addedText) || /export\s+.*:\s*any\b/.test(addedText)) {
      findings.push(createFinding("advisory", relativeFile, "Exported `any` detected in changed TypeScript surface."));
    }
    if (/from\s+["'](?:\.\.\/){3,}/.test(addedText) || /require\(["'](?:\.\.\/){3,}/.test(addedText)) {
      findings.push(createFinding("advisory", relativeFile, "Deep relative import added."));
    }
    if (addedLines.some((line) => /\bTODO\b/.test(line) && !/TODO\([^)]+\):/.test(line))) {
      findings.push(createFinding("advisory", relativeFile, "TODO added without `TODO(name): ...` format."));
    }
    if (fullText && fullText.split("\n").length > 250) {
      findings.push(createFinding("advisory", relativeFile, "Changed file exceeds modularity threshold (~250 lines)."));
    }
    if (classification.sharedLogicFiles.includes(relativeFile) && /export\s+(?:function|const|class)/.test(fullText) && !/\/\*\*/.test(fullText)) {
      findings.push(createFinding("advisory", relativeFile, "Changed shared utility has exports without JSDoc or rationale comment."));
    }
    if (
      !/\.test\.[tj]sx?$|\.spec\.[tj]sx?$/.test(relativeFile) &&
      addedLines.some((line) => /(?:===|!==|>|<|>=|<=)\s*["'][A-Za-z][^"']+["']/.test(line) || /(?:===|!==|>|<|>=|<=)\s*\d{2,}/.test(line))
    ) {
      findings.push(createFinding("advisory", relativeFile, "Possible magic-value churn added in business logic."));
    }
  }
  return findings;
}

export function evaluateNotesAndTasks(repoRoot, manifest = null) {
  const classification = classifyChanges(repoRoot, manifest);
  const notes = readNotes(repoRoot);
  const prSections = parseSections(notes.prSummaryText);
  const changeSections = parseSections(notes.changeNoteText);
  const blockers = [];
  const advisories = [];
  if (classification.schemaFiles.length > 0 && !sectionHasContent(changeSections, "migration")) {
    blockers.push(`Schema or migration files changed without a Migration note. Create ${notes.paths.changeNote}.`);
  }
  if (classification.docsFiles.length > 0 && !sectionHasContent(changeSections, "docs")) {
    blockers.push(`Public API, type, or config files changed without a Docs note. Create ${notes.paths.changeNote}.`);
  }
  if (classification.backendAuthSensitiveFiles.length > 0 && !sectionHasContent(changeSections, "auth/validation")) {
    blockers.push(`Backend or auth-sensitive files changed without an Auth/Validation note. Create ${notes.paths.changeNote}.`);
  }
  if (
    (classification.schemaFiles.length > 0 || classification.docsFiles.length > 0) &&
    !hasVerificationEvidence(prSections, changeSections)
  ) {
    blockers.push(`Sensitive changes require verification evidence in ${notes.paths.prSummary} or ${notes.paths.changeNote}.`);
  }
  if (notes.prSummaryText) {
    if (!sectionHasContent(prSections, "behavior") || !sectionHasContent(prSections, "risks") || !sectionHasContent(prSections, "tests")) {
      blockers.push(`PR summary is incomplete in ${notes.paths.prSummary}.`);
    }
  }
  if (classification.sharedLogicFiles.length > 0 && !sectionHasContent(prSections, "tests")) {
    advisories.push("Shared logic changed without a matching test note in PR summary.");
  }
  return {
    classification,
    notes,
    blockers,
    advisories,
  };
}

export function evaluatePrGate(repoRoot, command, manifest = null) {
  if (!/\b(?:gh\s+pr\s+create|git\s+push|gitlab|hub\s+pull-request)\b/i.test(command)) {
    return { blocked: false, checks: [] };
  }
  const checks = [];
  const notesAndTasks = evaluateNotesAndTasks(repoRoot, manifest);
  for (const blocker of notesAndTasks.blockers) {
    checks.push({ level: "block", message: blocker });
  }
  const secretFindings = scanSecrets(repoRoot);
  for (const finding of secretFindings) {
    checks.push({ level: finding.level, message: `${finding.file}: ${finding.message}` });
  }
  const task = manifest?.tasks?.test || (() => {
    const packageJson = readPackageJson(repoRoot);
    if (packageJson?.scripts?.test) {
      return { runner: "script", name: "test" };
    }
    return null;
  })();
  if (task) {
    const taskResult = runRepoTask(repoRoot, task);
    checks.push({
      level: taskResult.ok ? "info" : "block",
      message: taskResult.ok
        ? `Test task passed: ${taskResult.command}`
        : `Test task failed: ${taskResult.command || "configured task"}`,
    });
  }
  const blocked = checks.some((check) => check.level === "block");
  return { blocked, checks };
}

export function evaluateMcpMutation(input, repoRoot) {
  if (!mcpHostIdentifiers(input).some((value) => /mcp|github|linear|jira/i.test(value))) {
    return { blocked: false };
  }
  const hasExplicitWrite = mcpActionIdentifiers(input).some(identifierHasWrite);
  const hasWritePayload = [input?.tool_input, input?.arguments]
    .some((value) => value && typeof value === "object" && MCP_WRITE_PAYLOAD_KEYS.some((key) => key in value));
  if (!hasExplicitWrite && !hasWritePayload) {
    return { blocked: false };
  }
  if (!repoRoot) {
    return { blocked: true, reason: "State-changing MCP action requires a repository-scoped MCP Approval note." };
  }
  const notes = readNotes(repoRoot);
  const sections = parseSections(notes.changeNoteText);
  if (!sectionHasContent(sections, "mcp approval")) {
    return {
      blocked: true,
      reason: `State-changing MCP action requires MCP Approval note in ${notes.paths.changeNote}.`,
    };
  }
  return { blocked: false };
}

export function detectRepoSummary(repoRoot, manifest = null) {
  const classification = classifyChanges(repoRoot, manifest);
  return {
    repoRoot,
    changedFiles: classification.changedFiles,
    packageManager: repoRoot ? detectPackageManager(repoRoot) : null,
    manifestFound: Boolean(manifest),
    isWebRepo: classification.isWebRepo,
    classification,
  };
}

function formatFindings(findings) {
  if (findings.length === 0) {
    return "No findings.";
  }
  return findings.map((finding) => `- [${finding.level}] ${finding.file}: ${finding.message}`).join("\n");
}

function loadAgentsPolicy() {
  const policyPath = path.join(os.homedir(), ".agents", "agent-policy.json");
  if (!fileExists(policyPath)) {
    return {};
  }
  try {
    return JSON.parse(fs.readFileSync(policyPath, "utf8"));
  } catch {
    return {};
  }
}

function commandExitCode(raw) {
  const value =
    raw.exit_code ??
    raw.tool_response?.exit_code ??
    raw.tool_response?.metadata?.exit_code ??
    raw.metadata?.exit_code ??
    raw.output?.exit_code;
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return null;
}

function isTestCommand(command) {
  return TDD_TEST_COMMAND_PATTERNS.some((pattern) => pattern.test(command || ""));
}

function tddEvidencePath(repoRoot, policy) {
  const rel = policy?.mandatory_tdd?.evidence_file || ".git/agent-notes/tdd-evidence.json";
  return path.resolve(repoRoot, rel);
}

function readJsonOrNull(filePath) {
  if (!fileExists(filePath)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function hasTddEvidence(repoRoot, policy) {
  const evidence = readJsonOrNull(tddEvidencePath(repoRoot, policy));
  if (!evidence) {
    return { ok: false, reason: "No TDD evidence file found." };
  }
  const state = readAiFlowState(repoRoot);
  const classification = classifyChanges(repoRoot, loadRepoManifest(repoRoot));
  const runtimeFiles = hasRuntimeProductionChanges(repoRoot, loadRepoManifest(repoRoot), classification);
  const changedFilesHash = hashChangedFiles(repoRoot, runtimeFiles);
  const exceptions = Array.isArray(evidence.exceptions) ? evidence.exceptions : [];
  const now = new Date().toISOString();
  const activeException = [...exceptions].reverse().find((item) => {
    if (!item || !item.active || !item.reason || !item.alternative_verification) {
      return false;
    }
    if (item.expires_at && item.expires_at < now) {
      return false;
    }
    return item.task_id === state.taskId &&
      item.prompt_hash === state.promptHash &&
      item.changed_files_hash === changedFilesHash;
  });
  if (activeException && activeException.reason && activeException.alternative_verification) {
    return { ok: true, reason: "TDD exception present with required rationale." };
  }
  const events = Array.isArray(evidence.events) ? evidence.events : [];
  const matchingEvents = events.filter((item) =>
    item.task_id === state.taskId &&
    item.prompt_hash === state.promptHash &&
    item.changed_files_hash === changedFilesHash,
  );
  if (matchingEvents.length !== events.length && matchingEvents.length === 0) {
    return { ok: false, reason: "No RED/GREEN TDD stages found for the current task and changed files." };
  }
  const red = matchingEvents.filter((item) => item.stage === "red");
  const green = matchingEvents.filter((item) => item.stage === "green");
  if (red.length === 0 || green.length === 0) {
    return { ok: false, reason: "Missing RED/GREEN TDD stages in evidence log." };
  }
  const latestRed = red[red.length - 1];
  const latestGreen = green[green.length - 1];
  if ((latestGreen.timestamp || "") < (latestRed.timestamp || "")) {
    return { ok: false, reason: "Latest GREEN stage predates latest RED stage." };
  }
  return { ok: true, reason: "RED/GREEN evidence found." };
}

function hashChangedFiles(repoRoot, files) {
  const payload = files.map((file) => {
    return {
      file,
      content: readFile(repoRoot, file),
    };
  });
  return hashText(JSON.stringify(payload));
}

function hasRuntimeProductionChanges(repoRoot, manifest, classification) {
  const tddManifest = manifest?.tdd || {};
  const productionPaths = tddManifest.productionPaths || DEFAULT_TDD_PRODUCTION_PATHS;
  const testPaths = tddManifest.testPaths || DEFAULT_TDD_TEST_PATHS;
  const changed = classification.changedFiles || [];

  const runtimeFiles = changed.filter((file) => {
    const isProduction = matchesAnyGlob(file, productionPaths) || /\.[cm]?[jt]sx?$|\.py$|\.go$|\.rs$|\.swift$|\.java$|\.kt$/.test(file);
    if (!isProduction) return false;
    const isTest = matchesAnyGlob(file, testPaths);
    return !isTest;
  });
  return runtimeFiles;
}

function evaluateTddGate(repoRoot, manifest, policy) {
  const enabled = policy?.mandatory_tdd?.enabled !== false;
  if (!enabled || !repoRoot) {
    return { blocked: false };
  }
  if (isFunMode(repoRoot)) {
    return { blocked: false, summary: "TDD gate skipped: fun mode relaxes implementation gates." };
  }
  const classification = classifyChanges(repoRoot, manifest);
  const runtimeFiles = hasRuntimeProductionChanges(repoRoot, manifest, classification);
  if (runtimeFiles.length === 0) {
    return { blocked: false, summary: "TDD gate skipped: no runtime production file changes." };
  }
  const evidenceCheck = hasTddEvidence(repoRoot, policy);
  if (!evidenceCheck.ok) {
    return {
      blocked: true,
      reason: `TDD gate blocked: ${evidenceCheck.reason} Changed runtime files: ${runtimeFiles.join(", ")}`,
    };
  }
  return { blocked: false, summary: `TDD gate passed for ${runtimeFiles.length} runtime files.` };
}

function validateAgentsChanges(repoRoot) {
  const agentsRoot = path.join(os.homedir(), ".agents");
  if (path.resolve(repoRoot) !== path.resolve(agentsRoot)) {
    return { blocked: false };
  }
  const result = run("python3", [path.join(os.homedir(), ".agents", "scripts", "validate_agent_policy.py"), "--all"], {
    cwd: repoRoot,
  });
  if (result.status !== 0) {
    return {
      blocked: true,
      reason: `Validator gate blocked:\n${trim(result.stderr || result.stdout)}`,
    };
  }
  return { blocked: false, summary: "Validator gate passed." };
}

function recordTddFromCommand(repoRoot, normalized) {
  if (!repoRoot || !normalized.command || !isTestCommand(normalized.command)) {
    return { blocked: false };
  }
  const exitCode = commandExitCode(normalized.raw);
  if (exitCode === null) {
    return { blocked: false, summary: "TDD record skipped: exit code unavailable." };
  }
  const stage = exitCode === 0 ? "record-green" : "record-red";
  const aiFlowState = readAiFlowState(repoRoot);
  const classification = classifyChanges(repoRoot, loadRepoManifest(repoRoot));
  const runtimeFiles = hasRuntimeProductionChanges(repoRoot, loadRepoManifest(repoRoot), classification);
  const changedFilesHash = hashChangedFiles(repoRoot, runtimeFiles);
  const result = run(
    "python3",
    [
      path.join(os.homedir(), ".agents", "scripts", "tdd_evidence.py"),
      stage,
      "--repo-root",
      repoRoot,
      "--command",
      normalized.command,
      "--exit-code",
      String(exitCode),
      "--task-id",
      aiFlowState.taskId || "",
      "--prompt-hash",
      aiFlowState.promptHash || "",
      "--changed-files-hash",
      changedFilesHash,
      "--test-target",
      normalized.command,
    ],
    { cwd: repoRoot },
  );
  if (result.status !== 0) {
    return { blocked: true, reason: `Failed to record TDD evidence: ${trim(result.stderr || result.stdout)}` };
  }
  return { blocked: false, summary: `TDD evidence recorded (${stage.replace("record-", "").toUpperCase()}).` };
}

function recordLearningObservation(normalized) {
  const observer = path.join(os.homedir(), ".agents", "hooks", "learning", "observe.py");
  if (!fileExists(observer)) {
    return { blocked: false };
  }
  const payload = {
    cwd: normalized.cwd,
    prompt: normalized.raw.prompt || normalized.raw.message || "",
    event: normalized.event || normalized.raw.event || "",
    tool_name: normalized.toolName || normalized.raw.tool_name || normalized.raw.tool || "",
    tool_input: normalized.raw.tool_input || {},
    tool_response: normalized.raw.tool_response || normalized.raw.output || "",
    session_id: normalized.raw.session_id || "",
    agent_id: normalized.raw.agent_id || "",
  };
  const result = run("python3", [observer], { input: JSON.stringify(payload) });
  if (result.status !== 0) {
    return { blocked: false, summary: `Learning observe warning: ${trim(result.stderr || result.stdout)}` };
  }
  return { blocked: false };
}

function scanAgentsFastQuality(repoRoot, classification) {
  const findings = [];
  const isAgentsRepo = path.resolve(repoRoot) === path.join(os.homedir(), ".agents");
  if (!isAgentsRepo) {
    return findings;
  }
  const changed = classification.changedFiles || [];
  for (const file of changed) {
    if (/^skills\/[^/]+\/SKILL\.md$/.test(file)) {
      const content = readFile(repoRoot, file);
      if (!content.trim()) {
        findings.push(createFinding("block", file, "Skill file is empty."));
      }
    }
    const text = readFile(repoRoot, file);
    if (/\/Users\/(?!mikhail\/(\.agents|\.codex|\.cursor|\.config\/opencode|\.gemini\/antigravity))/.test(text)) {
      findings.push(createFinding("block", file, "Personal path leak outside allowed canonical roots."));
    }
  }
  return findings;
}

export function runAction(action, stdinText, env = process.env) {
  const normalized = normalizeInput(stdinText, env);
  const repoRoot = findRepoRoot(normalized.cwd);
  const manifest = repoRoot ? loadRepoManifest(repoRoot) : null;
  const policy = loadAgentsPolicy();

  switch (action) {
    case "codex-preflight": {
      const checks = isFunMode(repoRoot) ? [
        evaluateAiFlowPreflight(repoRoot, normalized),
        evaluateDangerousCommand(normalized.command, manifest),
        evaluateProtectedPathInCommand(normalized.command, normalized.cwd, repoRoot, manifest),
      ] : [
        evaluateAiFlowPreflight(repoRoot, normalized),
        evaluateDangerousCommand(normalized.command, manifest),
        evaluateSupplyChainCommand(normalized.command, repoRoot),
        evaluateLongRunning(normalized.command),
        evaluateProtectedPathInCommand(normalized.command, normalized.cwd, repoRoot, manifest),
        repoRoot ? evaluatePrGate(repoRoot, normalized.command, manifest) : { blocked: false, checks: [] },
      ];
      const blockedItem = checks.find((item) => item.blocked);
      return blockedItem || { blocked: false };
    }
    case "codex-stop": {
      if (!repoRoot) {
        return { blocked: false };
      }
      const notes = evaluateNotesAndTasks(repoRoot, manifest);
      const secretFindings = scanSecrets(repoRoot);
      if (isFunMode(repoRoot)) {
        const secretBlockers = secretFindings
          .filter((item) => item.level === "block")
          .map((item) => `${item.file}: ${item.message}`);
        return {
          blocked: secretBlockers.length > 0,
          blockers: secretBlockers,
          advisories: [],
          summary: "",
        };
      }
      const securityFindings = scanSecurityCode(repoRoot, notes.classification);
      const qualityFindings = scanCodeQuality(repoRoot, notes.classification);
      const blockers = [
        ...notes.blockers,
        ...secretFindings.filter((item) => item.level === "block").map((item) => `${item.file}: ${item.message}`),
        ...securityFindings.filter((item) => item.level === "block").map((item) => `${item.file}: ${item.message}`),
      ];
      const advisories = [
        ...notes.advisories,
        ...secretFindings.filter((item) => item.level !== "block").map((item) => `${item.file}: ${item.message}`),
        ...securityFindings.filter((item) => item.level !== "block").map((item) => `${item.file}: ${item.message}`),
        ...qualityFindings.map((item) => `${item.file}: ${item.message}`),
      ];
      return {
        blocked: blockers.length > 0,
        blockers,
        advisories,
        summary: advisories.length > 0 ? advisories.join(" ") : "",
      };
    }
    case "cursor-before-shell": {
      const checks = isFunMode(repoRoot) ? [
        evaluateAiFlowPreflight(repoRoot, normalized),
        evaluateDangerousCommand(normalized.command, manifest),
        evaluateProtectedPathInCommand(normalized.command, normalized.cwd, repoRoot, manifest),
      ] : [
        evaluateAiFlowPreflight(repoRoot, normalized),
        evaluateDangerousCommand(normalized.command, manifest),
        evaluateSupplyChainCommand(normalized.command, repoRoot),
        evaluateLongRunning(normalized.command),
        evaluateProtectedPathInCommand(normalized.command, normalized.cwd, repoRoot, manifest),
        repoRoot ? evaluatePrGate(repoRoot, normalized.command, manifest) : { blocked: false, checks: [] },
      ];
      const blockedItem = checks.find((item) => item.blocked);
      return blockedItem || { blocked: false };
    }
    case "cursor-after-shell": {
      if (!repoRoot) {
        return { blocked: false, summary: "" };
      }
      if (!/\b(?:gh\s+pr\s+create|git\s+push|gitlab|hub\s+pull-request)\b/i.test(normalized.command)) {
        return { blocked: false, summary: "" };
      }
      const secretFindings = scanSecrets(repoRoot);
      return {
        blocked: secretFindings.some((item) => item.level === "block"),
        findings: secretFindings,
        summary: formatFindings(secretFindings),
      };
    }
    case "block-dangerous":
      return evaluateDangerousCommand(normalized.command, manifest);
    case "block-long-running":
      return evaluateLongRunning(normalized.command);
    case "protect-paths":
      return evaluateProtectedPath(normalized.filePath, repoRoot, manifest);
    case "log-command": {
      const logLine = JSON.stringify({
        timestamp: new Date().toISOString(),
        tool: env.GUARDRAIL_TOOL || normalized.tool || "unknown",
        event: env.GUARDRAIL_EVENT || normalized.event || "unknown",
        cwd: normalized.cwd,
        command: redactSecrets(normalized.command),
      });
      const logPath = path.join(os.homedir(), ".agents", "hooks", "logs", "commands.log");
      fs.mkdirSync(path.dirname(logPath), { recursive: true });
      fs.appendFileSync(logPath, `${logLine}\n`);
      return { blocked: false, message: "logged" };
    }
    case "secret-scan":
      return { blocked: scanSecrets(repoRoot).some((item) => item.level === "block"), findings: scanSecrets(repoRoot) };
    case "change-impact":
      return detectRepoSummary(repoRoot, manifest);
    case "security-code-scan": {
      const classification = repoRoot ? classifyChanges(repoRoot, manifest) : {
        backendAuthSensitiveFiles: [],
        changedFiles: [],
        docsFiles: [],
        isWebRepo: false,
        schemaFiles: [],
        sharedLogicFiles: [],
        webComplianceFiles: [],
      };
      const findings = repoRoot ? scanSecurityCode(repoRoot, classification) : [];
      return { blocked: findings.some((item) => item.level === "block"), findings, summary: formatFindings(findings) };
    }
    case "code-quality-scan": {
      const classification = repoRoot ? classifyChanges(repoRoot, manifest) : {
        backendAuthSensitiveFiles: [],
        changedFiles: [],
        docsFiles: [],
        isWebRepo: false,
        schemaFiles: [],
        sharedLogicFiles: [],
        webComplianceFiles: [],
      };
      const findings = repoRoot ? scanCodeQuality(repoRoot, classification) : [];
      const fastChecks = repoRoot ? scanAgentsFastQuality(repoRoot, classification) : [];
      const skillRoutingFindings = repoRoot ? scanSkillRouting(repoRoot, normalized, classification) : [];
      const combined = [...findings, ...fastChecks, ...skillRoutingFindings];
      return { blocked: combined.some((item) => item.level === "block"), findings: combined, summary: formatFindings(combined) };
    }
    case "mcp-guard":
      return evaluateMcpMutation(normalized.raw, repoRoot);
    case "repo-detect":
      return detectRepoSummary(repoRoot, manifest);
    case "ai-flow-gate":
      return evaluateAiFlowPrompt(repoRoot, normalized);
    case "classify-prompt": {
      const prompt = trim(normalized.raw.prompt || normalized.raw.message?.system || "");
      const context = mergeRepoContexts(
        detectRepoContext(repoRoot),
        detectRepoContext(normalized.cwd),
      );
      const result = classifyPrompt(prompt, context);
      persistPromptRouting(repoRoot, normalized, result);
      return {
        blocked: false,
        routing: result,
        summary: formatPromptRouting(result),
      };
    }
    case "repo-verify": {
      const notesAndTasks = repoRoot ? evaluateNotesAndTasks(repoRoot, manifest) : {
        blockers: [],
        advisories: [],
        classification: { changedFiles: [] },
      };
      return {
        blocked: notesAndTasks.blockers.length > 0,
        blockers: notesAndTasks.blockers,
        advisories: notesAndTasks.advisories,
        classification: notesAndTasks.classification,
      };
    }
    case "pr-gate":
      return repoRoot ? evaluatePrGate(repoRoot, normalized.command, manifest) : { blocked: false, checks: [] };
    case "tdd-record":
      return recordTddFromCommand(repoRoot, normalized);
    case "tdd-gate":
      return repoRoot ? evaluateTddGate(repoRoot, manifest, policy) : { blocked: false };
    case "validator-gate":
      return repoRoot ? validateAgentsChanges(repoRoot) : { blocked: false };
    case "learning-observe":
      return recordLearningObservation(normalized);
    default:
      return { blocked: false, message: `Unknown action: ${action}` };
  }
}
