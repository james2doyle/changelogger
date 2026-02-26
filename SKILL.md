# SKILL.md - Package Upgrade Workflow with Changelogger

This skill helps AI coding agents assist users with npm package upgrades by
fetching and analyzing changelogs.

## Overview

When upgrading npm packages, it's critical to review changelogs for:
- Breaking changes that require code modifications
- Deprecated APIs that should be migrated
- New features that might be useful
- Security fixes that explain the urgency

The `changelogger` CLI tool finds CHANGELOG.md URLs for npm packages.

## Prerequisites

The `changelogger` tool must be installed globally:

```bash
uv tool install changelogger
```

## Basic Usage

```bash
# Get changelog URL for a single package
changelogger <package_name>

# Get changelog URLs for multiple packages
changelogger <package1> <package2> <package3>

# Verbose mode (for debugging)
changelogger -v <package_name>
```

## Package Upgrade Workflow

### Step 1: Identify Outdated Packages

First, check which packages need upgrading:

```bash
# npm
npm outdated

# yarn
yarn outdated

# pnpm
pnpm outdated
```

This shows current version, wanted version, and latest version for each package.

### Step 2: Get Changelog URLs

For each package you plan to upgrade, fetch the changelog URL:

```bash
# Single package
changelogger lodash

# Multiple packages at once
changelogger react react-dom @types/react
```

The tool outputs raw GitHub URLs that can be fetched directly.

### Step 3: Fetch and Analyze Changelogs

Use the returned URLs to fetch changelog content. Look for entries between
the current version and the target version.

**Example workflow:**

```bash
# Get the changelog URL
changelogger next
# Output: https://raw.githubusercontent.com/vercel/next.js/refs/heads/main/CHANGELOG.md

# Fetch the changelog content
curl -s "$(changelogger next)" | head -200
```

### Step 4: Identify Breaking Changes

When analyzing changelogs, pay attention to:

1. **Version headers** - Look for the versions between current and target
2. **BREAKING CHANGE** labels - These require code modifications
3. **Deprecation notices** - APIs that will be removed in future versions
4. **Migration guides** - Step-by-step upgrade instructions
5. **Peer dependency changes** - May require updating related packages

### Step 5: Plan and Execute Upgrade

Based on changelog analysis:

1. Note all breaking changes that affect your codebase
2. Identify deprecated APIs currently in use
3. Plan code modifications before upgrading
4. Upgrade the package
5. Apply necessary code changes
6. Run tests to verify

## Integration Examples

### Batch Upgrade Analysis

```bash
# Get all outdated packages and their changelogs
npm outdated --json | jq -r 'keys[]' | xargs changelogger
```

### In CI/CD Pipelines

```bash
#!/bin/bash
# Check for breaking changes before auto-merge

PACKAGES=$(npm outdated --json | jq -r 'keys[]')
for pkg in $PACKAGES; do
    CHANGELOG_URL=$(changelogger "$pkg" 2>/dev/null)
    if [ -n "$CHANGELOG_URL" ]; then
        echo "=== $pkg ==="
        curl -s "$CHANGELOG_URL" | head -100
    fi
done
```

## AI Agent Instructions

When helping users upgrade packages:

1. **Ask for context**: Which packages? Current versions? Target versions?

2. **Fetch changelogs**: Use `changelogger <package>` to get URLs, then fetch
   the content to analyze.

3. **Summarize relevant changes**: Focus on versions between current and target.
   Highlight breaking changes prominently.

4. **Provide migration guidance**: For each breaking change, explain:
   - What changed
   - How to update the code
   - Code examples if possible

5. **Suggest upgrade order**: Some packages should be upgraded together
   (e.g., react and react-dom, or packages with peer dependencies).

6. **Verify after upgrade**: Suggest running tests and type checking.

## Handling Edge Cases

### Changelog Not Found

If `changelogger` outputs "CHANGELOG.md not found" to stderr:

1. Check the package's GitHub repository directly
2. Look for HISTORY.md, CHANGES.md, or releases page
3. Check the npm package page for release notes

### Scoped Packages

Scoped packages work normally:

```bash
changelogger @types/node
changelogger @babel/core
```

### Monorepo Packages

The tool handles monorepo packages automatically by using `npm repo` to find
the correct subdirectory:

```bash
changelogger @tanstack/react-query
# Finds: .../TanStack/query/refs/heads/main/packages/react-query/CHANGELOG.md
```

## Example Session

User: "I want to upgrade react from 17.0.2 to 18.2.0"

Agent workflow:

```bash
# Get changelog
changelogger react
# Output: https://raw.githubusercontent.com/facebook/react/refs/heads/main/CHANGELOG.md

# Fetch and review (agent fetches this URL)
# Look for entries between 17.0.2 and 18.2.0
```

Key findings to report:
- React 18 introduces concurrent rendering
- `ReactDOM.render` is deprecated, use `createRoot`
- Automatic batching is now default
- New hooks: useId, useTransition, useDeferredValue

Migration steps:
1. Update react and react-dom together
2. Replace `ReactDOM.render` with `createRoot`
3. Update TypeScript types if using TypeScript
4. Test concurrent features
