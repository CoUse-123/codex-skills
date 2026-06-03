# GitHub Publish Workflow

Use this workflow when preparing this repository for GitHub publication, branch pushes, or releases.

## Preflight

1. Confirm the repository root with `pwd`.
2. Inspect status with `git status --short`.
3. Inspect changes with `git diff` and, when staged changes exist, `git diff --cached`.
4. Identify unrelated local changes and keep them out of the publish scope unless the user explicitly includes them.
5. Run:

```bash
python3 tools/run_tests.py
python3 tools/validate_skills.py
```

## Scope Confirmation

Before staging or committing, summarize:

- Files to include
- Files intentionally excluded
- Test and validation results
- Commit message proposal, if a commit was requested

If the user did not ask for a commit, stop after the summary.

## Commit

Use non-interactive git commands. Stage explicit paths instead of broad patterns when the tree has unrelated changes.

```bash
git add path/to/file path/to/dir
git status --short
git commit -m "Add concise message"
```

Do not amend, rebase, reset, or force-push unless the user explicitly asks.

## Remote

Expected GitHub repository:

```text
https://github.com/CoUse-123/codex-skills
```

Inspect remotes:

```bash
git remote -v
```

Set or correct `origin` only when the user approves:

```bash
git remote add origin https://github.com/CoUse-123/codex-skills.git
git remote set-url origin https://github.com/CoUse-123/codex-skills.git
```

## Authentication

Prefer GitHub CLI authentication:

```bash
gh auth status
gh auth login
gh auth setup-git
```

Do not echo tokens, store tokens in files, or ask the user to paste tokens into chat. Let `gh` handle browser or device-code authentication.

## Proxy Awareness

If the user's environment needs a proxy, inspect existing config before changing it:

```bash
git config --global --get http.proxy
git config --global --get https.proxy
env | grep -i proxy
```

Only set proxy values provided or approved by the user. Keep proxy changes scoped to the repository when possible:

```bash
git config http.proxy http://127.0.0.1:7890
git config https.proxy http://127.0.0.1:7890
```

## Push

Push only after the user asks:

```bash
git push -u origin <branch>
```

If push fails, capture the exact error and use `troubleshooting.md`.

## Release Notes

Draft release notes from committed changes, not from memory:

```bash
git log --oneline --decorate -n 10
git show --stat --oneline HEAD
```

Keep notes concise: added skills, tooling, tests, documentation, and known limitations.
