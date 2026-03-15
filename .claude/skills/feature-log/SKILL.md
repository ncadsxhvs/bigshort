---
name: feature-ledger
description: Use when completing a feature, finishing a branch, or when asked to update the feature log. Also use after merging PRs, before sprint reviews, or when onboarding needs a changelog.
---

# Feature Ledger

## Overview

Keep an append-only log of implemented features by analyzing git commits since the last ledger update. Outputs `docs/FEATURE_LOG.md`.

## When to Use

- After completing a feature or bugfix branch
- Before creating a PR (to document what changed)
- After merging to main (catch up the log)
- When asked "what's been built?" or "update the feature log"
- Sprint reviews or onboarding context

**Don't use for:** In-progress work, speculative features, or planning docs.

## Process

1. **Find the cursor:** Read `docs/FEATURE_LOG.md`, extract the first commit hash → that's the last recorded commit.
   - If no file or no hash found, default to last 50 commits.

2. **Collect commits since cursor:**
   ```bash
   git log --no-merges --pretty=format:"%H|%ad|%an|%s" --date=short <cursor>..HEAD
   ```
   For each commit, also get files: `git show --name-only --pretty="" <hash>`

3. **Classify each commit:**
   - Parse Conventional Commits format first (`type(scope): message`)
   - Fallback: derive type from keywords (add/implement/new → feat; bug/fix → fix; rename/rework → refactor)
   - Derive scope from folder paths (app/api, components, lib, etc.)

4. **Group related commits** into single entries only when evidence is strong (same scope + similar message within short time window). Preserve all commit hashes.

5. **Append entries** to `docs/FEATURE_LOG.md` using the template below. Newest entries go at the top (after the header). Number entries sequentially.

## Entry Template

```markdown
## Entry N

- **Date:** YYYY-MM-DD
- **Title:** <type>(<scope>): <summary>
- **Commits:** <hash1> (<short msg>), <hash2> ...
- **What changed:**
  - ...
- **Files touched:** `path/a`, `path/b`, ...
- **Risk/Notes:** ...
- **How to verify:** ...
```

## Required Fields

Every entry MUST include all template fields. Rules:
- **Never fabricate.** If info is missing, mark as "Unknown" or "Inferred".
- **Files touched:** List top 5-15 relevant files (skip lock files unless they're the point).
- **Risk/Notes:** Flag breaking changes, migrations, new env vars, config changes. Write "None" if truly none.
- **How to verify:** Concrete steps — commands to run, pages to check, tests to execute.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Duplicate entries for rebased commits | Check if content matches an existing entry before appending |
| Missing env var warnings | Always check `git diff` for `.env` changes and flag them |
| Vague "How to verify" | Give specific commands: `npm run build`, `curl /api/health`, not "test it" |
| Logging merge commits | Use `--no-merges` flag when collecting commits |
