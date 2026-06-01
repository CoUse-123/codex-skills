---
name: crawl-web-text
description: Extract clean, source-recorded text from public webpages or saved HTML files. Use when Codex needs to crawl or fetch public web pages for textual content, convert HTML into readable text, preserve source metadata, or prepare webpage text for summarization, analysis, citation, or downstream processing while respecting robots.txt, access limits, paywalls, logins, CAPTCHA, and anti-bot restrictions.
---

# Crawl Web Text

## Overview

Extract readable text from public webpages with conservative crawling behavior and clear source records. Use the bundled script for repeatable extraction, and read `references/extraction-guidelines.md` when access boundaries, cleanup rules, or failure reporting need closer judgment.

## Workflow

1. Confirm the requested source is public and does not require login, payment, CAPTCHA, or bypassing access controls.
2. Prefer official APIs, feeds, exports, or provided files when available.
3. For live URLs, check robots.txt and use polite fetch settings.
4. Extract text with `scripts/extract_web_text.py` when a deterministic artifact is useful.
5. Preserve source metadata with the extracted text.
6. Report failures plainly when access is blocked, restricted, or technically unavailable.

## Quick Start

Extract a public webpage to Markdown:

```bash
python3 skills/crawl-web-text/scripts/extract_web_text.py --url "https://example.com/" --output page.md
```

Extract a saved HTML file without network access:

```bash
python3 skills/crawl-web-text/scripts/extract_web_text.py --input-file saved-page.html --format json
```

## Script Behavior

`scripts/extract_web_text.py`:

- accepts one `--url` or one `--input-file`;
- supports `--format markdown`, `--format json`, and `--format text`;
- refuses non-http(s) URLs and URLs with embedded credentials;
- checks robots.txt before live fetches and fails closed if the policy cannot be fetched;
- removes script, style, hidden, and non-text elements;
- records source, final URL, fetch time, HTTP status, content type, robots decision, title, character count, and word count.

## Access Rules

- Do not bypass login walls, paywalls, robots restrictions, rate limits, CAPTCHA, IP blocks, or anti-bot controls.
- Do not scrape pages that are clearly private, credentialed, or contractually restricted.
- Do not retry aggressively after 401, 403, 407, 429, or CAPTCHA-like responses.
- If the user provides saved HTML from a page they can access, extract from the file and record it as a file source.

## Reference

Read `references/extraction-guidelines.md` for detailed boundaries, polite crawling defaults, extraction quality guidance, and failure modes.
