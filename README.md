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
```

See `docs/folder-plan.md` for the long-term repository structure.

## Skills

- `crawl-web-text`: Extract clean text from public webpages while respecting access boundaries, robots guidance, and source attribution.

## Validation

Run the current tests with:

```bash
python3 -m unittest discover -s tests/crawl-web-text -v
```

## License

No license has been selected yet.
