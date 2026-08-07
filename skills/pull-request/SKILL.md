---
name: pull-request
description: Create, update, or draft GitHub pull requests with an evidence-based engineering template. Use when the user asks to open a PR, improve a PR description, write a pull-request summary, or make a PR review-ready. Different from code-review skills because this packages completed work for reviewers rather than reviewing the code itself.
---

# Pull Request

Create concise, reviewable PR descriptions based on the repository's evidence and the Microsoft Engineering Playbook structure.

## Workflow

1. Read the repository's contribution guidance and PR template when present:
   - `AGENTS.md`
   - `CONTRIBUTING.md`
   - `.github/pull_request_template.md`
   - `.github/PULL_REQUEST_TEMPLATE/*`
2. Inspect the actual change:
   ```bash
   git status --short
   git diff --stat <base>...HEAD
   git diff <base>...HEAD
   git log --oneline <base>..HEAD
   ```
3. Check for an existing PR and duplicate open PRs:
   ```bash
   gh pr status
   gh pr list --state open --search '<key terms>'
   ```
4. Collect exact validation evidence. Never mark tests, lint, documentation, or compatibility checks complete unless they ran or were directly verified.
5. Write the body to a temporary Markdown file, then use `gh pr create --body-file` or `gh pr edit --body-file`. Do not pass a multiline body inline.
6. Re-read the published PR:
   ```bash
   gh pr view <number> --json title,body,url
   ```
7. Report the PR URL and any unchecked validation item.

Repository-provided templates override the default below. Preserve required headings and checklist items.

## Default PR Body

```markdown
## Description

State the problem first: what failed, who or what it affected, and why the old behavior was wrong.

Then summarize the solution and impact. Keep implementation details focused on what reviewers need to understand.

## Steps to Reproduce Bug and Validate Solution

### Reproduce

1. Give deterministic steps that show the old behavior.
2. Include the relevant environment or configuration.
3. Quote the exact error or observable failure when useful.

### Validate

1. Give commands or user steps that prove the fix.
2. State the expected result.

Remove this section for non-bug changes when it adds no value.

## PR Checklist

- [ ] I have updated the documentation accordingly.
- [ ] I have added tests to cover my changes.
- [ ] All relevant new and existing tests passed.
- [ ] My code follows the code style of this project.
- [ ] I ran lint checks with no new errors or warnings.
- [ ] I checked for other open pull requests for the same change.

Leave an item unchecked when it was not done or is not applicable; explain important unchecked items under Testing or Other Information.

## Does This Introduce a Breaking Change?

- [ ] Yes
- [ ] No

If yes, describe the impact and migration path.

## Testing

- **OS/environment:**
- **Commands/checks:**
- **Results:**
- **Scenarios covered:**

Name checks that were not run and why. Never say “all tests passed” after running only a narrow test.

## Any Relevant Logs or Outputs

Include short, decisive logs, screenshots, traces, or before/after output. Omit this section when there is no useful evidence.

## Other Information or Known Dependencies

List rollout concerns, follow-up work, dependencies, compatibility limits, or residual risks. Write `None` only when verified.
```

## Writing Rules

- Problem before solution.
- Describe behavior and impact, not a file-by-file changelog.
- Use exact commands, errors, versions, paths, and test counts.
- Link the issue/work item only when one exists; never invent an ID.
- Keep checkboxes truthful. Unchecked is better than unsupported.
- Do not claim screenshots, logs, tests, lint, or manual validation without evidence.
- Do not include secrets, credentials, internal tokens, or irrelevant raw logs.
- Use `Fixes #123` only when merging should close that issue; otherwise use `Related to #123`.
- Keep the title imperative and specific; use the repository's naming convention when present.

## Verification

Before finishing:

- compare the published body with the temporary Markdown file
- confirm the base and head branches
- confirm no unrelated files entered the diff
- confirm each checked item has evidence
- fix any mismatch and re-run `gh pr view`
