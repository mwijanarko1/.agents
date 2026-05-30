---
name: cartographer
description: "Map a codebase into CODEBASE_MAP with module boundaries and navigation paths."
---

# Cartographer

Create or refresh `docs/CODEBASE_MAP.md` before substantial work when no current map exists.

## Workflow

1. Inventory the workspace structure and identify the directories that matter to the current task.
2. Record the major modules, entry points, supporting assets, and cross-links between them.
3. Document where task-specific guidance lives so future work can navigate quickly.
4. Keep the map concise and maintainable. Capture structure and flow, not every implementation detail.

## Requirements

- Prefer the bundled scanner script for fast inventory.
- Verify the scanner output if the workspace root is hidden, because hidden-directory filtering can distort results if implemented incorrectly.
- Include a `last_mapped` timestamp in frontmatter.
- Update the map when the skill inventory, architecture, or workflow contracts materially change.

## Output Structure

Use this shape:

```md
---
last_mapped: 2026-03-16T00:00:00Z
---

# Codebase Map

## System Overview

## Directory Guide

## Key Workflows

## Known Risks
```
