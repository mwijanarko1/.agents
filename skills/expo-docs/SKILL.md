---
name: expo-docs
description: >-
  Search and consult official Expo documentation via their LLM-optimized endpoints.
  Use when working on Expo projects, EAS configuration, React Native modules,
  or when the user mentions Expo documentation.
---

# Expo Docs

A specialized workflow for accessing the most up-to-date Expo documentation using their LLM-optimized text files.

## When to Apply

Apply this skill when:
- You need official guidance on Expo SDK features, EAS Build/Submit/Update, or Expo Router.
- The user asks how to implement a specific Expo-related feature.
- You encounter an error related to Expo tools or configuration.
- You need the latest API reference for an Expo package.

## Core Documentation Endpoints

Expo provides several specialized `.txt` files for LLMs:

- **Main Index**: `https://docs.expo.dev/llms.txt` (List of all documentation pages)
- **Full Docs**: `https://docs.expo.dev/llms-full.txt` (Comprehensive documentation for Expo, Router, and Modules API)
- **EAS Docs**: `https://docs.expo.dev/llms-eas.txt` (Full documentation for Expo Application Services)
- **SDK Reference**: `https://docs.expo.dev/llms-sdk.txt` (API reference for the latest Expo SDK)

## Workflow

1.  **Identify the need**: Determine if the request is broad, EAS-specific, or SDK-specific.
2.  **Select the endpoint**:
    - Broad/Process: `llms-full.txt`
    - EAS: `llms-eas.txt`
    - SDK/API: `llms-sdk.txt`
3.  **Fetch content**: Use `WebFetch` to retrieve the relevant endpoint.
4.  **Search & Extract**: Parse the fetched content for specific instructions, code snippets, or API signatures relevant to the user's task.
5.  **Cite references**: When providing information, cite the relevant link found in the documentation to allow the user to follow up.

## Examples

**Example 1: Setting up EAS Build**
- Agent selects: `https://docs.expo.dev/llms-eas.txt`
- Agent searches for: "EAS Build setup", "eas.json configuration"

**Example 2: Using Expo Image**
- Agent selects: `https://docs.expo.dev/llms-sdk.txt`
- Agent searches for: "expo-image API", "Image component props"

## Best Practices

- Always prefer these specialized text endpoints over general web searches for Expo-specific information.
- If the target endpoint is too large to read in one go, try to identify specific page links from `llms.txt` and fetch them individually.
- Keep in mind that Expo documentation is versioned. These endpoints typically point to the latest stable version.
