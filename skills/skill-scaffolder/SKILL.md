---
name: skill-scaffolder
description: Create standard Codex skill skeletons inside this multi-skill repository. Use when Codex needs to add a new skill folder under the skills directory, generate SKILL.md frontmatter, agents/openai.yaml defaults, optional scripts/references/assets directories, repository-level test scaffolding, and enforce naming and no-extra-docs conventions.
---

# Skill Scaffolder

## Overview

Create lean, standard skill folders for this repository. Use `scripts/scaffold_skill.py` when a deterministic skeleton is useful, then replace placeholders with the actual skill workflow.

## Workflow

1. Normalize the skill name to lowercase hyphenated form.
2. Create files under `skills/<skill-name>/`, not at the repository root.
3. Include `SKILL.md` and `agents/openai.yaml`.
4. Add `scripts/`, `references/`, or `assets/` only when requested or clearly needed.
5. Add repository-level tests under `tests/<skill-name>/` unless the user explicitly declines tests.
6. Do not create README, CHANGELOG, installation guides, or process notes inside the skill folder.
7. Run the repository validator after scaffolding.

## Quick Start

Create a skill with scripts and references:

```bash
python3 skills/skill-scaffolder/scripts/scaffold_skill.py "My Skill" --resources scripts,references
```

Create a metadata-only skill without a test directory:

```bash
python3 skills/skill-scaffolder/scripts/scaffold_skill.py my-skill --no-tests
```

## Generated Defaults

`SKILL.md` should contain only `name` and `description` in frontmatter. Keep the body concise and replace all TODO text before publishing.

`agents/openai.yaml` should include:

- `interface.display_name`
- `interface.short_description`
- `interface.default_prompt` with an explicit `$skill-name` reference

## Validation

After scaffolding, run:

```bash
python3 tools/validate_skills.py
python3 -m unittest discover -s tests -v
```
