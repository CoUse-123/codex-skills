#!/usr/bin/env python3
"""Extract readable text from a public webpage or saved HTML file."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib import error, parse, request, robotparser


DEFAULT_USER_AGENT = "Codex-crawl-web-text/1.0 (respectful public text extraction)"
BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "details",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}
SUPPRESSED_TAGS = {"script", "style", "noscript", "template", "svg", "canvas", "iframe", "object", "embed", "nav"}


@dataclass
class SourceRecord:
    source: str
    source_type: str
    fetched_at: str
    final_url: str | None = None
    status_code: int | None = None
    content_type: str | None = None
    robots_allowed: bool | None = None


@dataclass
class ExtractionResult:
    source: SourceRecord
    title: str | None
    text: str
    char_count: int
    word_count: int


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._title_chunks: list[str] = []
        self._suppressed: list[str] = []
        self._in_title = False

    @property
    def text(self) -> str:
        return clean_text("".join(self._chunks))

    @property
    def title(self) -> str | None:
        title = clean_text("".join(self._title_chunks))
        return title or None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag in SUPPRESSED_TAGS or self._is_hidden(attr_map):
            self._suppressed.append(tag)
            return
        if tag == "title":
            self._in_title = True
        if not self._suppressed and tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._suppressed:
            if self._suppressed[-1] == tag:
                self._suppressed.pop()
            return
        if tag == "title":
            self._in_title = False
        if tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._suppressed:
            return
        if self._in_title:
            self._title_chunks.append(data)
            return
        self._chunks.append(data)

    @staticmethod
    def _is_hidden(attrs: dict[str, str]) -> bool:
        if "hidden" in attrs or attrs.get("aria-hidden", "").lower() == "true":
            return True
        style = attrs.get("style", "").replace(" ", "").lower()
        return "display:none" in style or "visibility:hidden" in style


def clean_text(value: str) -> str:
    value = unescape(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def extract_from_html(html: str, source: SourceRecord) -> ExtractionResult:
    parser = TextExtractor()
    parser.feed(html)
    text = parser.text
    return ExtractionResult(
        source=source,
        title=parser.title,
        text=text,
        char_count=len(text),
        word_count=len(re.findall(r"\S+", text)),
    )


def fetch_public_url(url: str, user_agent: str, timeout: float, crawl_delay: float) -> tuple[bytes, SourceRecord]:
    parsed = parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are supported.")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not supported.")

    robots_allowed = check_robots(url, user_agent, timeout)
    if not robots_allowed:
        raise PermissionError(f"robots.txt does not allow fetching: {url}")

    if crawl_delay > 0:
        time.sleep(crawl_delay)

    req = request.Request(url, headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", None)
            content_type = response.headers.get("Content-Type")
            if status is not None and status >= 400:
                raise ValueError(f"HTTP request failed with status {status}.")
            data = response.read()
            record = SourceRecord(
                source=url,
                source_type="url",
                fetched_at=utc_now(),
                final_url=response.geturl(),
                status_code=status,
                content_type=content_type,
                robots_allowed=robots_allowed,
            )
            return data, record
    except error.HTTPError as exc:
        raise ValueError(f"HTTP request failed with status {exc.code}.") from exc
    except error.URLError as exc:
        raise ValueError(f"Could not fetch URL: {exc.reason}") from exc


def check_robots(url: str, user_agent: str, timeout: float) -> bool:
    parsed = parse.urlparse(url)
    robots_url = parse.urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    req = request.Request(robots_url, headers={"User-Agent": user_agent})
    parser = robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            if getattr(response, "status", 200) == 404:
                return True
            if getattr(response, "status", 200) >= 400:
                return False
            lines = response.read().decode("utf-8", errors="replace").splitlines()
            parser.parse(lines)
            return parser.can_fetch(user_agent, url)
    except error.HTTPError as exc:
        if exc.code == 404:
            return True
        return False
    except error.URLError:
        return False


def read_input_file(path: Path) -> tuple[str, SourceRecord]:
    data = path.read_bytes()
    html = decode_html(data, None)
    record = SourceRecord(source=str(path), source_type="file", fetched_at=utc_now())
    return html, record


def decode_html(data: bytes, content_type: str | None) -> str:
    charset = charset_from_content_type(content_type) or charset_from_meta(data)
    if charset:
        try:
            return data.decode(charset, errors="replace")
        except LookupError:
            pass
    return data.decode("utf-8", errors="replace")


def charset_from_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    match = re.search(r"charset=([^\s;]+)", content_type, flags=re.IGNORECASE)
    return match.group(1).strip("\"'") if match else None


def charset_from_meta(data: bytes) -> str | None:
    head = data[:4096].decode("ascii", errors="ignore")
    match = re.search(r"<meta[^>]+charset=[\"']?([A-Za-z0-9._-]+)", head, flags=re.IGNORECASE)
    return match.group(1) if match else None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def format_result(result: ExtractionResult, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(asdict(result), ensure_ascii=False, indent=2)
    if output_format == "text":
        return result.text

    lines = [
        f"# {result.title or 'Extracted Web Text'}",
        "",
        f"- Source: {result.source.source}",
        f"- Source type: {result.source.source_type}",
        f"- Fetched at: {result.source.fetched_at}",
    ]
    if result.source.final_url:
        lines.append(f"- Final URL: {result.source.final_url}")
    if result.source.status_code:
        lines.append(f"- HTTP status: {result.source.status_code}")
    if result.source.robots_allowed is not None:
        lines.append(f"- Robots allowed: {str(result.source.robots_allowed).lower()}")
    lines.extend(["", "## Text", "", result.text])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="Public http(s) webpage URL to fetch and extract.")
    source.add_argument("--input-file", type=Path, help="Saved HTML file to extract without network access.")
    parser.add_argument("--output", type=Path, help="Write output to this path instead of stdout.")
    parser.add_argument("--format", choices=("markdown", "json", "text"), default="markdown")
    parser.add_argument("--timeout", type=float, default=15.0, help="Network timeout in seconds.")
    parser.add_argument("--crawl-delay", type=float, default=1.0, help="Delay before fetching a URL after robots check.")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    try:
        if args.url:
            data, source = fetch_public_url(args.url, args.user_agent, args.timeout, args.crawl_delay)
            html = decode_html(data, source.content_type)
        else:
            html, source = read_input_file(args.input_file)

        result = extract_from_html(html, source)
        output = format_result(result, args.format)
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except Exception as exc:
        print(f"extract_web_text.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
