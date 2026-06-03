# PDF Extraction Guidelines

Use this reference when extraction quality, OCR limits, table handling, or dependency choice matters.

## Boundaries

- Extract from local PDF files supplied or approved by the user.
- Do not claim success when pages have no text layer.
- Do not OCR unless the user explicitly asks and OCR tooling is available.
- Do not remove page numbers or source metadata from outputs used for citation or downstream processing.
- Do not auto-install `pdfplumber`, `pypdf`, `PyPDF2`, OCR tooling, or other dependencies into the user's environment.
- Do not present the standard-library fallback as a full PDF layout parser.

## Dependency Strategy

The standard-library fallback is the default zero-dependency path for portability and offline tests. It is suitable only for simple text-layer PDFs and should not be presented as a full PDF layout parser. For production-quality extraction, complex layouts, compressed streams, and tables, prefer optional dependencies such as pdfplumber or pypdf.

- Prefer `pdfplumber` when available for production-quality extraction, complex layouts, and better table handling.
- Use `pypdf` or `PyPDF2` for ordinary embedded-text extraction when `pdfplumber` is unavailable.
- Use the standard-library fallback only for simple PDFs with a text layer and uncompressed or directly parseable content streams.
- Report optional dependency gaps clearly instead of installing dependencies automatically.
- Treat `--prefer pdfplumber`, `--require-dependency pdfplumber`, `--table-mode basic|pdfplumber`, or a separate `pdf-table-extractor` skill as future enhancement paths.

## Tables

- Treat table extraction as best-effort unless `pdfplumber` returns structured tables.
- Preserve table rows with page numbers.
- Detect simple table-like text using visible delimiters such as `|`, tabs, or repeated spacing.
- Do not overfit prose into tables. If uncertain, keep the content as text and mention the limitation.
- Complex tables are not a default zero-dependency capability.

## Scanned PDFs

If the result contains no meaningful text:

- set or report `needs_ocr`;
- say that the PDF likely has no embedded text layer;
- ask whether OCR should be attempted with available tools;
- do not fabricate page content from filenames or visible assumptions.
- make clear that OCR is outside the current default extraction path.

## Output Expectations

JSON output should include:

- `source_metadata`
- `pages`
- `tables`
- `warnings`
- `needs_ocr`

Markdown output should include:

- source metadata
- warnings
- one section per page
- tables represented as Markdown where possible
