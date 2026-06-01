---
name: skill-validator
description: Validate all Codex skills in this repository offline. Use when Codex needs to check skill folders for required SKILL.md files, strict name/description frontmatter, directory-name consistency, agents/openai.yaml basics, executable bundled scripts, absence of redundant skill-local docs, and repository-level test coverage before publishing.
---

# Skill Validator

## Overview

Validate this repository's skill folders without network access or third-party packages. Use the bundled script as the canonical checker for local work and release preparation.

## Workflow

1. Run the repository-level wrapper from the repository root.
2. Fix errors before publishing, committing, or opening a release PR.
3. Treat warnings as review prompts; convert recurring warnings into stricter checks only when the convention is settled.
4. Run unit tests after validation.

## Quick Start

```bash
python3 tools/validate_skills.py
python3 -m unittest discover -s tests -v
```

Validate one skill:

```bash
python3 skills/skill-validator/scripts/validate_skills.py --skill skill-scaffolder
```

## Checks

The validator checks:

- `SKILL.md` exists and starts with YAML frontmatter.
- Frontmatter contains only `name` and `description`.
- The skill directory name matches the `name` value.
- Skill names use lowercase letters, digits, and hyphens.
- `agents/openai.yaml` has `display_name`, `short_description`, and `default_prompt`.
- `default_prompt` mentions `$skill-name`.
- Executable scripts in `scripts/` have executable permission.
- `tests/<skill-name>/` exists.
- Skill folders do not contain README, CHANGELOG, installation guides, or generated caches.
