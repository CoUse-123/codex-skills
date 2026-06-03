---
name: pdf-text-extractor
description: Extract text, page structure, simple tables, and metadata from PDF files into Markdown or JSON. Use when Codex needs to process a user-provided PDF for per-page text, page numbers, table-like content, summaries, citations, search indexing, downstream analysis, or to identify scanned PDFs that need OCR instead of pretending text extraction succeeded.
---

# PDF Text Extractor

## Overview

Extract PDF text with page-aware source records and clear limitations. Use the bundled script as an open-source, zero-dependency default path for portability, offline tests, and simple PDFs; use optional dependencies for stronger extraction when the environment already provides them.

The standard-library fallback is the default zero-dependency path for portability and offline tests. It is suitable only for simple text-layer PDFs and should not be presented as a full PDF layout parser. For production-quality extraction, complex layouts, compressed streams, and tables, prefer optional dependencies such as pdfplumber or pypdf.

## Workflow

1. Confirm the input is a local PDF file the user provided or approved.
2. Run `scripts/extract_pdf_text.py` with `--format markdown` or `--format json`.
3. Inspect warnings for missing text layers, scanned pages, parser limitations, or optional dependency gaps.
4. If pages have no text, report that OCR is required and do not invent content.
5. Use extracted page numbers and metadata when summarizing, quoting, or building citations.

## Quick Start

```bash
python3 skills/pdf-text-extractor/scripts/extract_pdf_text.py input.pdf --format markdown --output extracted.md
python3 skills/pdf-text-extractor/scripts/extract_pdf_text.py input.pdf --format json --output extracted.json
```

## Script Behavior

`scripts/extract_pdf_text.py`:

- records file name, byte size, parser used, dependency availability, page count, warnings, character count, and word count;
- returns each page with page number, text blocks, detected table-like rows, and per-page counts;
- uses `pdfplumber`, `pypdf`, or `PyPDF2` when already available, without installing packages automatically;
- falls back to a standard-library parser for simple text-layer PDFs with uncompressed or directly parseable content streams;
- reports `needs_ocr` when no extractable text is found.

Current default capability does not include complex PDF layout parsing, production-grade table extraction, compressed stream handling beyond optional libraries, or OCR for scanned PDFs.

## Extraction Guidance

Read `references/pdf-extraction-guidelines.md` for OCR boundaries, table handling, dependency notes, and output expectations.
