#!/usr/bin/env python3
"""Extract DOCX structure and generate a rule-based brief as Markdown or JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
WORD_RE = re.compile(r"\S+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
ACTION_RE = re.compile(r"\b(action|todo|next step|owner|due|follow up|follow-up)\b", re.IGNORECASE)
RISK_RE = re.compile(r"\b(risk|blocker|issue|dependency|unknown|assumption|decision needed|question)\b|\?", re.IGNORECASE)


@dataclass
class ParagraphRecord:
    index: int
    text: str
    style: str | None
    kind: str
    char_count: int
    word_count: int


@dataclass
class TableRecord:
    index: int
    rows: list[list[str]]
    char_count: int
    word_count: int


@dataclass
class BriefResult:
    source_metadata: dict[str, object]
    summary: list[str]
    action_items: list[dict[str, str | None]]
    suggested_edits: list[str]
    risks_or_questions: list[str]
    paragraphs: list[ParagraphRecord]
    tables: list[TableRecord]
    warnings: list[str]


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t\r\n]+", " ", text)
    return text.strip()


def paragraph_text(paragraph: ET.Element) -> str:
    pieces: list[str] = []
    for node in paragraph.iter():
        if node.tag == f"{{{NS['w']}}}t" and node.text:
            pieces.append(node.text)
        elif node.tag == f"{{{NS['w']}}}tab":
            pieces.append("\t")
        elif node.tag == f"{{{NS['w']}}}br":
            pieces.append("\n")
    return clean_text("".join(pieces))


def paragraph_style(paragraph: ET.Element) -> str | None:
    style = paragraph.find("./w:pPr/w:pStyle", NS)
    if style is None:
        return None
    return style.attrib.get(f"{{{NS['w']}}}val")


def is_numbered(paragraph: ET.Element) -> bool:
    return paragraph.find("./w:pPr/w:numPr", NS) is not None


def classify_paragraph(paragraph: ET.Element, style: str | None) -> str:
    normalized = (style or "").lower()
    if normalized.startswith("heading") or normalized in {"title", "subtitle"}:
        return "heading"
    if is_numbered(paragraph):
        return "list_item"
    return "paragraph"


def table_rows(table: ET.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.findall("./w:tr", NS):
        cells: list[str] = []
        for cell in row.findall("./w:tc", NS):
            cell_text = clean_text(" ".join(paragraph_text(p) for p in cell.findall(".//w:p", NS)))
            cells.append(cell_text)
        if any(cells):
            rows.append(cells)
    return rows


def extract_docx(path: Path) -> BriefResult:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".docx":
        raise ValueError("input file must have a .docx extension")

    warnings: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            document_xml = archive.read("word/document.xml")
    except KeyError as exc:
        raise ValueError("docx is missing word/document.xml") from exc
    except zipfile.BadZipFile as exc:
        raise ValueError("input is not a valid docx zip file") from exc

    root = ET.fromstring(document_xml)
    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("docx document body is missing")

    paragraphs: list[ParagraphRecord] = []
    tables: list[TableRecord] = []
    paragraph_index = 1
    table_index = 1
    for child in list(body):
        if child.tag == f"{{{NS['w']}}}p":
            text = paragraph_text(child)
            if not text:
                continue
            style = paragraph_style(child)
            kind = classify_paragraph(child, style)
            paragraphs.append(
                ParagraphRecord(
                    index=paragraph_index,
                    text=text,
                    style=style,
                    kind=kind,
                    char_count=len(text),
                    word_count=count_words(text),
                )
            )
            paragraph_index += 1
        elif child.tag == f"{{{NS['w']}}}tbl":
            rows = table_rows(child)
            if not rows:
                continue
            table_text = "\n".join(" | ".join(row) for row in rows)
            tables.append(TableRecord(index=table_index, rows=rows, char_count=len(table_text), word_count=count_words(table_text)))
            table_index += 1

    if not paragraphs and not tables:
        warnings.append("No document text was extracted.")

    result = BriefResult(
        source_metadata={
            "file_name": path.name,
            "path": str(path),
            "byte_size": path.stat().st_size,
            "paragraph_count": len(paragraphs),
            "table_count": len(tables),
            "extraction_method": "zipfile-wordprocessingml",
        },
        summary=make_summary(paragraphs, tables),
        action_items=extract_action_items(paragraphs, tables),
        suggested_edits=suggest_edits(paragraphs, tables),
        risks_or_questions=extract_risks_or_questions(paragraphs, tables),
        paragraphs=paragraphs,
        tables=tables,
        warnings=warnings,
    )
    return result


def make_summary(paragraphs: list[ParagraphRecord], tables: list[TableRecord]) -> list[str]:
    candidates = [p.text for p in paragraphs if p.kind == "heading"]
    candidates.extend(p.text for p in paragraphs if p.kind != "heading")
    summary: list[str] = []
    for candidate in candidates:
        for sentence in SENTENCE_RE.split(candidate):
            sentence = clean_text(sentence)
            if sentence and sentence not in summary:
                summary.append(sentence)
            if len(summary) >= 3:
                break
        if len(summary) >= 3:
            break
    if tables:
        summary.append(f"Document includes {len(tables)} table(s) with structured supporting details.")
    return summary[:4]


def extract_action_items(paragraphs: list[ParagraphRecord], tables: list[TableRecord]) -> list[dict[str, str | None]]:
    items: list[dict[str, str | None]] = []
    for paragraph in paragraphs:
        if ACTION_RE.search(paragraph.text):
            items.append(action_item_from_text(paragraph.text))
    for table in tables:
        if not table.rows:
            continue
        headers = [cell.lower() for cell in table.rows[0]]
        if any("action" in header or "owner" in header or "due" in header for header in headers):
            for row in table.rows[1:]:
                row_map = {headers[index]: row[index] for index in range(min(len(headers), len(row)))}
                task = first_matching(row_map, ("action", "task", "next step")) or " | ".join(row)
                owner = first_matching(row_map, ("owner", "responsible"))
                due = first_matching(row_map, ("due", "deadline", "date"))
                items.append({"task": task, "owner": owner, "due": due, "source": f"table {table.index}"})
    return dedupe_action_items(items)


def action_item_from_text(text: str) -> dict[str, str | None]:
    owner = extract_labeled_value(text, "owner")
    due = extract_labeled_value(text, "due")
    task = re.sub(r"^\s*(action|todo|next step)\s*[:\-]\s*", "", text, flags=re.IGNORECASE)
    return {"task": task, "owner": owner, "due": due, "source": "paragraph"}


def extract_labeled_value(text: str, label: str) -> str | None:
    match = re.search(rf"\b{label}\s*[:\-]\s*([^.;,\n]+)", text, flags=re.IGNORECASE)
    return clean_text(match.group(1)) if match else None


def first_matching(row_map: dict[str, str], keys: Iterable[str]) -> str | None:
    for key in keys:
        for header, value in row_map.items():
            if key in header and value:
                return value
    return None


def dedupe_action_items(items: list[dict[str, str | None]]) -> list[dict[str, str | None]]:
    seen: set[str] = set()
    deduped: list[dict[str, str | None]] = []
    for item in items:
        key = str(item.get("task", "")).lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def suggest_edits(paragraphs: list[ParagraphRecord], tables: list[TableRecord]) -> list[str]:
    suggestions: list[str] = []
    if not any(p.kind == "heading" for p in paragraphs):
        suggestions.append("Add a clear heading so the brief has an identifiable topic.")
    for paragraph in paragraphs:
        if paragraph.word_count > 80:
            suggestions.append(f"Shorten paragraph {paragraph.index}; it has {paragraph.word_count} words.")
            break
    for action in extract_action_items(paragraphs, tables):
        if not action.get("owner"):
            suggestions.append(f"Add an owner for action item: {action.get('task')}")
        if not action.get("due"):
            suggestions.append(f"Add a due date for action item: {action.get('task')}")
    for table in tables:
        if table.rows and any(not cell for row in table.rows for cell in row):
            suggestions.append(f"Fill empty cells or clarify missing values in table {table.index}.")
    return suggestions[:8]


def extract_risks_or_questions(paragraphs: list[ParagraphRecord], tables: list[TableRecord]) -> list[str]:
    findings = [p.text for p in paragraphs if RISK_RE.search(p.text)]
    for table in tables:
        for row in table.rows:
            row_text = " | ".join(row)
            if RISK_RE.search(row_text):
                findings.append(row_text)
    deduped: list[str] = []
    for finding in findings:
        if finding not in deduped:
            deduped.append(finding)
    return deduped[:10]


def result_to_json(result: BriefResult) -> str:
    return json.dumps(asdict(result), indent=2, ensure_ascii=False)


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    max_cols = max(len(row) for row in rows)
    padded = [row + [""] * (max_cols - len(row)) for row in rows]
    lines = [
        "| " + " | ".join(padded[0]) + " |",
        "| " + " | ".join(["---"] * max_cols) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in padded[1:])
    return "\n".join(lines)


def result_to_markdown(result: BriefResult) -> str:
    meta = result.source_metadata
    lines = [
        f"# DOCX Brief: {meta.get('file_name')}",
        "",
        "## Source Metadata",
        "",
        f"- File: {meta.get('file_name')}",
        f"- Paragraphs: {meta.get('paragraph_count')}",
        f"- Tables: {meta.get('table_count')}",
        f"- Extraction method: {meta.get('extraction_method')}",
        "",
        "## Summary",
        "",
    ]
    lines.extend(f"- {item}" for item in result.summary) if result.summary else lines.append("- No summary text extracted.")
    lines.extend(["", "## Action Items", ""])
    if result.action_items:
        for item in result.action_items:
            owner = item.get("owner") or "Unassigned"
            due = item.get("due") or "No due date"
            lines.append(f"- {item.get('task')} (Owner: {owner}; Due: {due})")
    else:
        lines.append("- No action items detected.")
    lines.extend(["", "## Risks Or Questions", ""])
    lines.extend(f"- {item}" for item in result.risks_or_questions) if result.risks_or_questions else lines.append("- None detected.")
    lines.extend(["", "## Suggested Edits", ""])
    lines.extend(f"- {item}" for item in result.suggested_edits) if result.suggested_edits else lines.append("- No rule-based suggestions.")
    for table in result.tables:
        lines.extend(["", f"## Table {table.index}", "", markdown_table(table.rows)])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="DOCX file to extract.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="Write output to a file instead of stdout.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    try:
        result = extract_docx(args.docx)
        output = result_to_json(result) if args.format == "json" else result_to_markdown(result)
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except Exception as exc:
        print(f"extract_docx_brief.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
