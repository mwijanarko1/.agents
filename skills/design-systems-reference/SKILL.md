---
name: design-systems-reference
description: "Reference design systems, accessibility guidance, and component docs."
---

# Design Systems Reference

## Scope

This is a **secondary reference skill** that provides curated guidance on design system patterns, component APIs, accessibility standards, and content strategy. It should be loaded after a primary design skill (`taste-skill` or `redesign-skill`) when the task involves:

- Building or reviewing component libraries
- Implementing design system tokens
- Checking accessibility patterns
- Verifying licensing for design assets
- Reference for design system documentation structure

## When to Use

Load this skill when the user task involves:

- Creating reusable UI component libraries
- Implementing or auditing design system tokens (colors, spacing, typography)
- Building accessible form controls, dialogs, or navigation patterns
- Checking open-source licenses for design assets or icon sets
- Reference for component API design patterns
- Content/accessibility guidance for UI copy

## Primary Reference

**awesome-design-systems**: https://github.com/alexpate/awesome-design-systems

This curated collection is an index of public design systems, pattern libraries, UI libraries, and brand/content guidelines. Use it to find primary documentation from mature teams instead of treating the awesome list itself as the source of truth.

When a specific system looks relevant, open that system's own docs or source before applying guidance. The list is a map, not a quality ranking.

Use it to compare:

- **Component patterns**: APIs, state coverage, examples, and usage guidance
- **Token systems**: color roles, spacing scales, typography systems, and theming structure
- **Accessibility patterns**: ARIA usage, keyboard navigation, focus management, and contrast notes
- **Documentation structure**: how design systems explain principles, variants, and adoption
- **Content guidance**: voice, tone, error copy, and interaction language when available

## Usage Guidelines

### For Component Patterns

When building components, check this reference for:

- API conventions (props naming, slot patterns)
- Interaction patterns (loading states, error handling)
- Accessibility requirements (keyboard support, screen reader announcements)

### For Design Token Decisions

Reference for:

- Color contrast ratios (WCAG AA/AAA compliance)
- Spacing scales (4px, 8px, 16px increments)
- Typography scales and line-height ratios

### For Accessibility/Content

Check for:

- Form label patterns
- Error message placement
- Button/action text conventions
- Modal/dialog announcements

### For License Verification

When using design resources:

- Verify icon set licenses (MIT, Apache, commercial)
- Check font licensing for production use
- Validate component library licenses (MIT,ISC vs proprietary)

## Icon Preference Policy

For UI work, prefer these icon sets over defaults:

1. **Phosphor Icons** (`@phosphor-icons/react`) - Primary recommendation
2. **Hugeicons** (`@hugeicons/react` plus `@hugeicons/core-free-icons`) - Alternative modern set
3. **Tabler Icons** (`@tabler/icons-react`) - Clean, consistent set

Before importing any icon library:

1. **Check `package.json`** to see what's already installed
2. Prefer already-installed libraries to reduce dependencies
3. If none installed and a new dependency is justified, prefer Phosphor unless the product needs Hugeicons or Tabler's specific visual language
4. Avoid defaulting to Lucide without checking alternatives first
5. Use Lucide only when the project already standardizes on it or when adding a new dependency is not appropriate

**Do not assume any icon library is available.** Always verify via `package.json` before imports.

## Secondary Only

This skill is **never used alone**. It must be loaded alongside:

- `taste-skill` or `redesign-skill` (primary design mode)
- `frontend-web-development` (implementation)

Do not load this as a standalone skill for general UI tasks.
