# Multi-Skill Repository Folder Plan

This repository is a workspace for creating, testing, maintaining, and publishing
multiple Codex skills. The repository should keep installable skill folders lean
while placing shared project documentation, tests, and release helpers outside
the skill packages.

## Top-Level Layout

```text
.
├── README.md
├── LICENSE
├── docs/
│   └── folder-plan.md
├── skills/
│   ├── crawl-web-text/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   ├── scripts/
│   │   │   └── extract_web_text.py
│   │   └── references/
│   │       └── extraction-guidelines.md
│   ├── skill-scaffolder/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── scripts/scaffold_skill.py
│   ├── skill-validator/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── scripts/validate_skills.py
│   ├── github-publisher/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   │       ├── publish-workflow.md
│   │       └── troubleshooting.md
│   ├── pdf-text-extractor/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── scripts/extract_pdf_text.py
│   │   └── references/pdf-extraction-guidelines.md
│   └── docx-brief-maker/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── scripts/extract_docx_brief.py
│       └── references/brief-guidelines.md
├── tests/
│   ├── crawl-web-text/
│   │   ├── fixtures/
│   │   │   └── sample-page.html
│   │   └── test_extract_web_text.py
│   ├── skill-scaffolder/
│   │   └── test_scaffold_skill.py
│   ├── skill-validator/
│   │   └── test_validate_skills.py
│   ├── github-publisher/
│   │   └── test_github_publisher.py
│   ├── pdf-text-extractor/
│   │   ├── fixtures/sample.pdf
│   │   └── test_pdf_text_extractor.py
│   └── docx-brief-maker/
│       ├── fixtures/document.xml
│       └── test_docx_brief_maker.py
└── tools/
    ├── run_tests.py
    ├── validate_skills.py
    └── validate_skills.sh
```

## Directory Responsibilities

`skills/`

Store the actual Codex skills. Each direct child directory is one installable skill and should be self-contained.

`skills/<skill-name>/SKILL.md`

Define the skill trigger metadata and the concise operational workflow Codex should follow. The YAML frontmatter should include only `name` and `description`.

`skills/<skill-name>/agents/openai.yaml`

Store UI-facing metadata such as display name, short description, and default prompt.

`skills/<skill-name>/scripts/`

Store executable helper scripts that make the skill reliable and repeatable. For `crawl-web-text`, this is where the webpage text extraction CLI should live.

`skills/<skill-name>/references/`

Store deeper guidance that should be loaded only when needed. For example, `crawl-web-text` keeps extraction policy there, while `github-publisher` keeps publishing workflow and troubleshooting notes there.

`skills/<skill-name>/assets/`

Store templates, icons, sample files, or other resources that the skill uses in generated outputs. Create this directory only when a skill actually needs assets.

`tests/`

Store repository-level tests outside installable skill folders, so the published skill stays lean while the open-source project still has verification.

`tests/<skill-name>/`

Store tests that validate one skill's bundled scripts, examples, or reference-backed behavior. Tests may include fixtures and should avoid live network dependencies unless explicitly marked.

`tools/`

Store repository maintenance helpers, such as validating every skill folder before release.

`docs/`

Store project-level planning and contributor documentation. These files describe how the repository is organized, not how an individual skill operates.

## Skill Folder Standard

Every skill folder should use the skill name as its directory name and should
follow the same lowercase hyphenated naming convention as the `name` field in
`SKILL.md`.

Recommended skill structure:

```text
skills/<skill-name>/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
├── references/
└── assets/
```

Only `SKILL.md` is required. Add `agents/`, `scripts/`, `references/`, and
`assets/` only when they serve the skill directly.

Do not add README, changelog, installation guide, or development notes inside a
skill folder. Put repository-level documentation in `docs/` or the root README.

## Multi-Skill Maintenance Rules

1. Keep installable artifacts under `skills/<skill-name>/`.
2. Keep test code under `tests/<skill-name>/`.
3. Keep shared automation under `tools/`.
4. Keep planning and contributor docs under `docs/`.
5. Avoid shared runtime dependencies between skills unless a helper truly applies to multiple skills.
6. Prefer standard-library scripts where practical so copied skills remain portable.
7. Validate each skill independently before publishing.
8. Add live-network tests only as optional/manual tests; default tests should run offline.

## Adding a New Skill

1. Choose a lowercase hyphenated skill name.
2. Create `skills/<skill-name>/SKILL.md` and, when useful, `agents/openai.yaml`.
3. Add scripts and references only for reusable behavior that improves reliability.
4. Add focused tests under `tests/<skill-name>/`.
5. Update this plan only if the repository structure changes.
6. Run the skill validation and any relevant tests.

## Publishing Preparation

Before publishing or tagging a release:

1. Run `python3 tools/run_tests.py`.
2. Run `python3 tools/validate_skills.py`.
3. Review `git status --short` and `git diff`.
4. Confirm that no skill folder contains README, changelog, generated caches, or unrelated notes.
5. Keep release notes and repository-wide process docs outside individual skill folders unless they are direct bundled references for a specific skill.
