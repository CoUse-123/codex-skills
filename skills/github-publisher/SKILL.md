---
name: github-publisher
description: Guide safe GitHub publishing for this codex-skills repository. Use when Codex needs to prepare commits, push branches, configure or inspect remotes, handle gh authentication, account for proxy settings, draft release notes, troubleshoot push/auth/network failures, or publish repository changes without silently including unrelated files or exposing credentials.
---

# GitHub Publisher

## Overview

Publish this repository carefully through GitHub while keeping user intent, credentials, proxy settings, and unrelated local changes visible. This skill is procedural: do not commit, push, tag, or create releases unless the user explicitly asks for that action.

## Workflow

1. Read `references/publish-workflow.md` before preparing a publish operation.
2. Inspect `git status --short` and relevant diffs before staging anything.
3. Run tests and `python3 tools/validate_skills.py`.
4. Confirm the intended scope when there are unrelated or surprising changes.
5. Stage only the approved files.
6. Commit only after the user asks for a commit.
7. Push only after the user asks for a push.
8. Read `references/troubleshooting.md` when auth, proxy, remote, or push errors appear.

## Safety Rules

- Do not silently stage unrelated files.
- Do not print, store, or ask the user to paste GitHub tokens into chat.
- Do not bypass network, GitHub, branch protection, or authentication restrictions.
- Do not use destructive git commands unless the user explicitly requests them.
- Prefer `gh auth login` and `gh auth setup-git` over manual token handling.

## References

- `references/publish-workflow.md`: status, diff, test, commit, remote, auth, push, and release-note sequence.
- `references/troubleshooting.md`: proxy, auth, remote, branch, and network failure checks.
