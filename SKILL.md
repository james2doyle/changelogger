---
name: smart-package-upgrade
description: Find the CHANGELOG.md for an NPM package so that you can help guide your agent through an upgrade from one version to another
---

# Changelogger Skill

This skill helps AI coding agents assist users with npm package upgrades by
fetching and analyzing changelogs. Use it when a user wants to upgrade a
package and needs to understand breaking changes, deprecations, or migration
steps.

## Workflow

1. Run `npm outdated <package_name> --json` to get current, wanted, and latest versions
2. Run `changelogger <package_name>` to get the changelog URL
3. **If the `changelogger` command fails (command not found), STOP and ask the user how to proceed**
4. Fetch the returned URL to get changelog content
5. Analyze the changelog for changes between current and target versions
6. Provide upgrade guidance to the user

## Usage

```bash
# Get changelog URL for a single package
changelogger <package_name>

# Get changelog URLs for multiple packages
changelogger <package1> <package2> <package3>
```

The tool outputs raw GitHub URLs that can be fetched directly.

## Analyzing Changelogs

When reviewing changelog content, look for entries between the current version
and target version. Pay attention to:

- **BREAKING CHANGE** labels — require code modifications
- **Deprecation notices** — APIs that will be removed in future versions
- **Migration guides** — step-by-step upgrade instructions
- **Peer dependency changes** — may require updating related packages

## Providing Upgrade Guidance

For each relevant change, explain to the user:

1. What changed and why it matters
2. How to update their code
3. Code examples where helpful

If multiple related packages need upgrading together (e.g., `react` and
`react-dom`), suggest the correct upgrade order.

## Edge Cases

**Compare URLs**: If CHANGELOG.md is not found, the tool may return a GitHub
compare URL instead (`<repo>/compare/<current>...<wanted>`). Use this to review
commits between versions.

**Scoped packages**: Work normally — `changelogger @types/node`, `changelogger @babel/core`

**Monorepo packages**: Handled automatically — the tool finds the correct
subdirectory changelog (e.g., `@tanstack/react-query` resolves to
`packages/react-query/CHANGELOG.md`).
