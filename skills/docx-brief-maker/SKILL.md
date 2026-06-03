---
name: docx-brief-maker
description: Extract structure from Word docx files and create brief-ready Markdown or JSON with summaries, action items, suggested edits, risks, questions, source metadata, paragraphs, headings, lists, and tables. Use when Codex needs to process a user-provided Word document for meeting notes, decision briefs, review comments, structured extraction, or downstream summarization without requiring heavyweight docx dependencies.
---

# DOCX Brief Maker

## Overview

Extract `.docx` content with WordprocessingML structure, then produce a rule-based brief that Codex can refine into higher-quality summaries, action plans, or edit recommendations.

## Workflow

1. Confirm the input is a local `.docx` file supplied or approved by the user.
2. Run `scripts/extract_docx_brief.py` with `--format markdown` or `--format json`.
3. Use the structured extraction as source material for any deeper Codex summary or rewrite.
4. Keep page-layout claims modest; this script reads document XML and does not perform visual render QA.
5. When the user needs polished document editing or final DOCX generation, use a document editing workflow after the brief is created.

## Quick Start

```bash
python3 skills/docx-brief-maker/scripts/extract_docx_brief.py input.docx --format markdown --output brief.md
python3 skills/docx-brief-maker/scripts/extract_docx_brief.py input.docx --format json --output brief.json
```

## Script Behavior

`scripts/extract_docx_brief.py`:

- reads `.docx` with Python standard-library `zipfile` and XML parsing;
- extracts paragraphs, headings, list-like paragraphs, and table cell text;
- returns `summary`, `action_items`, `suggested_edits`, `risks_or_questions`, `source_metadata`, and raw extracted structure;
- produces deterministic rule-based brief fields;
- leaves complex judgment, nuanced editing, and polished writing to Codex using the extracted structure.

## Reference

Read `references/brief-guidelines.md` for brief quality rules, action-item extraction cues, risk detection, and limitations.
