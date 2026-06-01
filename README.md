# Codex Skills

This repository collects reusable Codex skills for building, testing, and publishing agent workflows.

## Layout

```text
skills/
  <skill-name>/
    SKILL.md
    agents/openai.yaml
    scripts/
    references/

tests/
  <skill-name>/

docs/
  folder-plan.md

tools/
  run_tests.py
  validate_skills.py
```

See `docs/folder-plan.md` for the long-term repository structure.

## Skills

- `crawl-web-text`: Extract clean text from public webpages while respecting access boundaries, robots guidance, and source attribution.
- `skill-scaffolder`: Generate standard skill folders, metadata, optional resource directories, and repository-level tests.
- `skill-validator`: Validate all repository skills offline against naming, frontmatter, metadata, script, and test-layout conventions.
- `github-publisher`: Follow a careful GitHub publishing workflow for this repository, including status checks, auth, proxy, push, and release-note troubleshooting.

## Validation

Run the current tests with:

```bash
python3 tools/run_tests.py
python3 tools/validate_skills.py
```

## License

No license has been selected yet.
