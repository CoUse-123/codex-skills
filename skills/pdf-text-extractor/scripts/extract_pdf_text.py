#!/usr/bin/env python3
"""Extract PDF text, page structure, and simple tables as Markdown or JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


WORD_RE = re.compile(r"\S+")


@dataclass
class TextBlock:
    text: str
    char_count: int
    word_count: int


@dataclass
class TableRecord:
    page_number: int
    rows: list[list[str]]
    source: str


@dataclass
class PageRecord:
    page_number: int
    text: str
    text_blocks: list[TextBlock]
    tables: list[TableRecord]
    char_count: int
    word_count: int
    needs_ocr: bool


@dataclass
class ExtractionResult:
    source_metadata: dict[str, object]
    pages: list[PageRecord]
    tables: list[TableRecord]
    warnings: list[str]
    needs_ocr: bool
    char_count: int
    word_count: int


def optional_dependency_status() -> dict[str, bool]:
    status = {}
    for module_name in ("pdfplumber", "pypdf", "PyPDF2"):
        try:
            __import__(module_name)
        except Exception:
            status[module_name] = False
        else:
            status[module_name] = True
    return status


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_block(text: str) -> TextBlock:
    text = clean_text(text)
    return TextBlock(text=text, char_count=len(text), word_count=count_words(text))


def make_page(page_number: int, text: str, tables: list[TableRecord] | None = None) -> PageRecord:
    text = clean_text(text)
    blocks = [make_block(block) for block in re.split(r"\n\s*\n", text) if clean_text(block)]
    table_records = tables if tables is not None else detect_tables(text, page_number)
    return PageRecord(
        page_number=page_number,
        text=text,
        text_blocks=blocks,
        tables=table_records,
        char_count=len(text),
        word_count=count_words(text),
        needs_ocr=not bool(text),
    )


def extract_pdf(path: Path) -> ExtractionResult:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("input file must have a .pdf extension")

    dependency_status = optional_dependency_status()
    warnings: list[str] = []
    pages: list[PageRecord] = []
    parser_used = "stdlib-fallback"

    if dependency_status.get("pdfplumber"):
        try:
            pages = extract_with_pdfplumber(path)
            parser_used = "pdfplumber"
        except Exception as exc:
            warnings.append(f"pdfplumber extraction failed: {exc}")

    if not pages and (dependency_status.get("pypdf") or dependency_status.get("PyPDF2")):
        try:
            pages = extract_with_pypdf(path)
            parser_used = "pypdf" if dependency_status.get("pypdf") else "PyPDF2"
        except Exception as exc:
            warnings.append(f"pypdf/PyPDF2 extraction failed: {exc}")

    if not pages:
        pages = extract_with_stdlib(path)
        if not any(page.text for page in pages):
            warnings.append("No extractable text layer found; OCR is required for scanned or image-only PDFs.")
        else:
            warnings.append(
                "Used standard-library fallback parser. This zero-dependency path is suitable only for simple text-layer PDFs; "
                "for production-quality extraction, complex layouts, compressed streams, and tables, prefer pdfplumber or pypdf."
            )

    needs_ocr = not any(page.text for page in pages)
    tables = [table for page in pages for table in page.tables]
    combined_text = "\n\n".join(page.text for page in pages if page.text)
    metadata = {
        "file_name": path.name,
        "path": str(path),
        "byte_size": path.stat().st_size,
        "page_count": len(pages),
        "parser": parser_used,
        "dependencies": dependency_status,
    }
    return ExtractionResult(
        source_metadata=metadata,
        pages=pages,
        tables=tables,
        warnings=warnings,
        needs_ocr=needs_ocr,
        char_count=len(combined_text),
        word_count=count_words(combined_text),
    )


def extract_with_pdfplumber(path: Path) -> list[PageRecord]:
    import pdfplumber  # type: ignore

    pages: list[PageRecord] = []
    with pdfplumber.open(str(path)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables: list[TableRecord] = []
            for table in page.extract_tables() or []:
                rows = [["" if cell is None else clean_text(str(cell)) for cell in row] for row in table if row]
                if rows:
                    tables.append(TableRecord(page_number=index, rows=rows, source="pdfplumber"))
            pages.append(make_page(index, text, tables or None))
    return pages


def extract_with_pypdf(path: Path) -> list[PageRecord]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        from PyPDF2 import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(make_page(index, text))
    return pages


def extract_with_stdlib(path: Path) -> list[PageRecord]:
    data = path.read_bytes()
    object_streams = read_pdf_streams(data)
    page_refs = read_page_content_refs(data)
    pages: list[PageRecord] = []

    if page_refs:
        for index, content_ids in enumerate(page_refs, start=1):
            text_parts = [extract_text_from_content_stream(object_streams.get(content_id, b"")) for content_id in content_ids]
            pages.append(make_page(index, "\n".join(part for part in text_parts if part)))
        return pages

    stream_texts = [extract_text_from_content_stream(stream) for stream in object_streams.values()]
    stream_texts = [text for text in stream_texts if text]
    if stream_texts:
        return [make_page(index, text) for index, text in enumerate(stream_texts, start=1)]

    page_count = max(1, len(re.findall(rb"/Type\s*/Page\b", data)))
    return [make_page(index, "") for index in range(1, page_count + 1)]


def read_pdf_streams(data: bytes) -> dict[int, bytes]:
    streams: dict[int, bytes] = {}
    for match in re.finditer(rb"(\d+)\s+\d+\s+obj(.*?)endobj", data, re.DOTALL):
        object_id = int(match.group(1))
        body = match.group(2)
        stream_match = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.DOTALL)
        if not stream_match:
            continue
        if b"/FlateDecode" in body:
            continue
        streams[object_id] = stream_match.group(1)
    return streams


def read_page_content_refs(data: bytes) -> list[list[int]]:
    refs: list[list[int]] = []
    page_pattern = re.compile(rb"\d+\s+\d+\s+obj(?:(?!endobj).)*?/Type\s*/Page\b(?P<body>.*?)endobj", re.DOTALL)
    for match in page_pattern.finditer(data):
        body = match.group("body")
        content_match = re.search(rb"/Contents\s+(?:\[(.*?)\]|(\d+)\s+\d+\s+R)", body, re.DOTALL)
        if not content_match:
            refs.append([])
            continue
        if content_match.group(2):
            refs.append([int(content_match.group(2))])
        else:
            refs.append([int(item) for item in re.findall(rb"(\d+)\s+\d+\s+R", content_match.group(1))])
    return refs


def extract_text_from_content_stream(stream: bytes) -> str:
    content = stream.decode("latin-1", errors="ignore")
    text_parts: list[str] = []
    for block in re.findall(r"BT(.*?)ET", content, flags=re.DOTALL):
        tokens = re.findall(r"\((?:\\.|[^\\()])*\)|<([0-9A-Fa-f\s]+)>|\[.*?\]|Tj|TJ|'|\"", block, flags=re.DOTALL)
        text_parts.extend(extract_strings_before_text_operators(block))
    return clean_text("\n".join(text_parts))


def extract_strings_before_text_operators(block: str) -> list[str]:
    results: list[str] = []
    for match in re.finditer(r"(?P<value>\((?:\\.|[^\\()])*\)|\[.*?\]|<(?P<hex>[0-9A-Fa-f\s]+)>)\s*(?:Tj|TJ|'|\")", block, flags=re.DOTALL):
        value = match.group("value")
        if value.startswith("["):
            strings = re.findall(r"\((?:\\.|[^\\()])*\)|<([0-9A-Fa-f\s]+)>", value, flags=re.DOTALL)
            literal_strings = re.findall(r"\((?:\\.|[^\\()])*\)", value, flags=re.DOTALL)
            decoded = [decode_pdf_string(item) for item in literal_strings]
            decoded.extend(decode_hex_string(item) for item in re.findall(r"<([0-9A-Fa-f\s]+)>", value))
            if decoded:
                results.append("".join(decoded))
        elif value.startswith("<"):
            results.append(decode_hex_string(match.group("hex") or ""))
        else:
            results.append(decode_pdf_string(value))
    return results


def decode_pdf_string(value: str) -> str:
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1]
    replacements = {
        r"\n": "\n",
        r"\r": "\n",
        r"\t": "\t",
        r"\b": "\b",
        r"\f": "\f",
        r"\(": "(",
        r"\)": ")",
        r"\\": "\\",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = re.sub(r"\\([0-7]{1,3})", lambda m: chr(int(m.group(1), 8)), value)
    return value


def decode_hex_string(value: str) -> str:
    compact = re.sub(r"\s+", "", value)
    if len(compact) % 2:
        compact += "0"
    try:
        raw = bytes.fromhex(compact)
    except ValueError:
        return ""
    if raw.startswith(b"\xfe\xff"):
        return raw[2:].decode("utf-16-be", errors="replace")
    return raw.decode("latin-1", errors="replace")


def detect_tables(text: str, page_number: int) -> list[TableRecord]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "|" in stripped:
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        elif "\t" in stripped:
            cells = [cell.strip() for cell in stripped.split("\t")]
        elif re.search(r"\S\s{2,}\S", stripped):
            cells = [cell.strip() for cell in re.split(r"\s{2,}", stripped)]
        else:
            continue
        if len([cell for cell in cells if cell]) >= 2:
            rows.append(cells)
    return [TableRecord(page_number=page_number, rows=rows, source="text-pattern")] if len(rows) >= 2 else []


def result_to_json(result: ExtractionResult) -> str:
    return json.dumps(asdict(result), indent=2, ensure_ascii=False)


def markdown_table(rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return ""
    max_cols = max(len(row) for row in rows)
    padded = [list(row) + [""] * (max_cols - len(row)) for row in rows]
    header = padded[0]
    separator = ["---"] * max_cols
    body = padded[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(separator) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def result_to_markdown(result: ExtractionResult) -> str:
    meta = result.source_metadata
    lines = [
        f"# PDF Text Extraction: {meta.get('file_name')}",
        "",
        "## Source Metadata",
        "",
        f"- File: {meta.get('file_name')}",
        f"- Byte size: {meta.get('byte_size')}",
        f"- Page count: {meta.get('page_count')}",
        f"- Parser: {meta.get('parser')}",
        f"- Needs OCR: {str(result.needs_ocr).lower()}",
        f"- Characters: {result.char_count}",
        f"- Words: {result.word_count}",
    ]
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    for page in result.pages:
        lines.extend(["", f"## Page {page.page_number}", ""])
        if page.text:
            lines.append(page.text)
        else:
            lines.append("_No extractable text found on this page._")
        for table_index, table in enumerate(page.tables, start=1):
            lines.extend(["", f"### Page {page.page_number} Table {table_index}", "", markdown_table(table.rows)])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF file to extract.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="Write output to a file instead of stdout.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    try:
        result = extract_pdf(args.pdf)
        output = result_to_json(result) if args.format == "json" else result_to_markdown(result)
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except Exception as exc:
        print(f"extract_pdf_text.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
