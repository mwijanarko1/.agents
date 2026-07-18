import assert from "node:assert/strict";
import { runAction } from "../hooks/lib/guardrail-core.mjs";

function route(prompt, cwd = "/Users/mikhail") {
  return runAction("classify-prompt", JSON.stringify({ prompt, cwd }), {
    GUARDRAIL_TOOL: "codex",
    GUARDRAIL_EVENT: "UserPromptSubmit",
  }).routing;
}

function assertIncludes(items, value, label) {
  assert.ok(items.includes(value), `${label} should include ${value}; got ${items.join(", ")}`);
}

function assertExcludes(items, value, label) {
  assert.ok(!items.includes(value), `${label} should not include ${value}; got ${items.join(", ")}`);
}

{
  const result = route("Okay, implement the routing algorithm. I want to make sure that we don't waste tokens.");
  assertIncludes(result.tags, "agent-policy", "tags");
  assertIncludes(result.tags, "routing", "tags");
  assertIncludes(result.skills, "testing-strategies", "skills");
  assertExcludes(result.skills, "ai-interaction-workflow", "skills");
  assertExcludes(result.skills, "coding-standards", "skills");
  assertExcludes(result.tags, "greenfield-design", "tags");
  assertExcludes(result.skills, "frontend-design", "skills");
  assertExcludes(result.subagents, "design-engineer", "subagents");
}

{
  const result = route("What do you think about adding a YAML file for skills?");
  assertExcludes(result.skills, "ai-interaction-workflow", "skills");
  assertExcludes(result.skills, "coding-standards", "skills");
  assertExcludes(result.skills, "testing-strategies", "skills");
}

{
  const result = route("Build a Next.js settings dashboard");
  assertIncludes(result.skills, "frontend-web-development", "skills");
  assertIncludes(result.subagents, "frontend-engineer", "subagents");
  assertExcludes(result.skills, "ios-development", "skills");
  assertExcludes(result.skills, "vercel-react-native-skills", "skills");
}

{
  const result = route("Fix the Expo EAS build config");
  assertIncludes(result.skills, "vercel-react-native-skills", "skills");
  assertIncludes(result.skills, "expo-docs", "skills");
  assertIncludes(result.subagents, "mobile-engineer", "subagents");
  assertExcludes(result.skills, "frontend-web-development", "skills");
}

{
  const result = route("Create a polished landing page hero for a SaaS website");
  assertIncludes(result.skills, "frontend-web-development", "skills");
  assertIncludes(result.skills, "frontend-design", "skills");
  assertIncludes(result.subagents, "design-engineer", "subagents");
}

{
  const result = route("Redesign the existing dashboard UI");
  assertIncludes(result.skills, "frontend-design", "skills");
  assertExcludes(result.skills, "taste-skill", "skills");
  assertExcludes(result.skills, "redesign-skill", "skills");
  assertExcludes(result.skills, "soft-skill", "skills");
  assertExcludes(result.skills, "shipswift-recipes", "skills");
  assertExcludes(result.skills, "ios-simulator-browser", "skills");
}

{
  const result = route("Build a SwiftUI settings screen in Xcode");
  assertIncludes(result.skills, "ios-development", "skills");
  assertExcludes(result.skills, "shipswift-recipes", "skills");
  assertExcludes(result.skills, "add-component", "skills");
  assertExcludes(result.skills, "ios-simulator-browser", "skills");
}

{
  const result = route("Make this look like Linear");
  assert.ok(
    !result.secondarySkills.includes("design-md-gallery") ||
      result.skills.includes("frontend-design"),
    `design-md-gallery must not be emitted alone; got skills=${result.skills.join(", ")} secondary=${result.secondarySkills.join(", ")}`,
  );
}

{
  const result = route("Add auth middleware and input validation to the API route");
  assertIncludes(result.skills, "backend-architecture", "skills");
  assertIncludes(result.skills, "security-vulnerability-mitigation", "skills");
  assert.ok(
    result.subagents.includes("backend-architect") || result.subagents.includes("security-auditor"),
    `expected backend or security subagent; got ${result.subagents.join(", ")}`,
  );
}

console.log("prompt skill router tests passed");
