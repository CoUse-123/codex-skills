# GitHub Publishing Troubleshooting

Use this reference when GitHub publishing fails.

## Authentication Failures

Check:

```bash
gh auth status
git config --get credential.helper
git remote -v
```

Fix path:

1. Run `gh auth login`.
2. Run `gh auth setup-git`.
3. Retry the git operation.

Do not display or persist tokens in chat, files, shell history, or repository config.

## Proxy Or Network Failures

Symptoms include connection timeouts, TLS handshake failures, reset connections, or unreachable GitHub hosts.

Check:

```bash
git config --get http.proxy
git config --get https.proxy
git config --global --get http.proxy
git config --global --get https.proxy
env | grep -i proxy
```

Ask the user before changing proxy settings. Prefer repository-local git config for project-specific proxy needs.

## Remote Problems

Check:

```bash
git remote -v
git branch --show-current
```

Common fixes:

- Add `origin` when missing.
- Correct the repository URL when it points elsewhere.
- Push the current branch with `git push -u origin <branch>`.

## Rejected Pushes

Common causes:

- Remote branch has new commits.
- Branch protection blocks direct pushes.
- Authentication lacks permission.

Do not force-push by default. Fetch and inspect first:

```bash
git fetch origin
git status --short
git log --oneline --decorate --graph --max-count=20 --all
```

Ask the user before merge, rebase, force-push, or changing branch targets.

## Dirty Worktree

If unrelated files are present:

1. Name them in the status summary.
2. Stage only approved files.
3. Leave unrelated changes untouched.

Do not use `git reset --hard`, `git checkout --`, or broad cleanup commands without explicit user approval.
