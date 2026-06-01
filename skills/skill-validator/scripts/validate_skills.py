#!/usr/bin/env python3
"""Validate Codex skill folders in this repository without third-party packages."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
FORBIDDEN_DOC_NAMES = {
    "README.md",
    "CHANGELOG.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "NOTES.md",
}
SCRIPT_SUFFIXES = {".py", ".sh", ".bash", ".zsh"}


@dataclass
class Finding:
    level: str
    path: str
    message: str


def parse_simple_yaml(lines: list[str]) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            raise ValueError("frontmatter must be a flat mapping")
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if not key:
            raise ValueError("frontmatter key cannot be empty")
        data[key] = value
    return data


def read_frontmatter(skill_md: Path) -> tuple[dict[str, str] | None, list[str]]:
    if not skill_md.exists():
        return None, ["SKILL.md is missing"]
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ["SKILL.md must start with YAML frontmatter"]
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return None, ["SKILL.md frontmatter is not closed"]
    try:
        return parse_simple_yaml(lines[1:end]), []
    except ValueError as exc:
        return None, [str(exc)]


def parse_openai_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    in_interface = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line == "interface:":
            in_interface = True
            continue
        if raw_line and not raw_line.startswith(" "):
            in_interface = False
        if in_interface and ":" in raw_line:
            key, value = raw_line.split(":", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


def validate_skill(skill_dir: Path, repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel_skill = skill_dir.relative_to(repo_root)
    skill_md = skill_dir / "SKILL.md"
    frontmatter, errors = read_frontmatter(skill_md)
    for error in errors:
        findings.append(Finding("error", str(skill_md), error))

    if frontmatter is not None:
        keys = set(frontmatter)
        if keys != {"name", "description"}:
            findings.append(Finding("error", str(skill_md), "frontmatter must contain only name and description"))
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if name != skill_dir.name:
            findings.append(Finding("error", str(skill_md), "frontmatter name must match skill directory name"))
        if not NAME_RE.fullmatch(name):
            findings.append(Finding("error", str(skill_md), "skill name must use lowercase letters, digits, and hyphens"))
        if not description or "TODO" in description:
            findings.append(Finding("error", str(skill_md), "description must be non-empty and publication-ready"))

    agents_yaml = skill_dir / "agents" / "openai.yaml"
    if not agents_yaml.exists():
        findings.append(Finding("error", str(agents_yaml), "agents/openai.yaml is missing"))
    else:
        try:
            values = parse_openai_yaml(agents_yaml)
        except Exception as exc:
            findings.append(Finding("error", str(agents_yaml), f"could not parse agents/openai.yaml: {exc}"))
        else:
            for key in ("display_name", "short_description", "default_prompt"):
                if not values.get(key) or "TODO" in values.get(key, ""):
                    findings.append(Finding("error", str(agents_yaml), f"interface.{key} must be present and publication-ready"))
            if frontmatter is not None:
                expected = f"${frontmatter.get('name', skill_dir.name)}"
                if expected not in values.get("default_prompt", ""):
                    findings.append(Finding("error", str(agents_yaml), f"interface.default_prompt must mention {expected}"))

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.iterdir():
            if script.is_file() and script.suffix in SCRIPT_SUFFIXES:
                mode = script.stat().st_mode
                if not mode & stat.S_IXUSR:
                    findings.append(Finding("error", str(script), "script should be executable"))
                first_line = script.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
                if script.suffix in {".py", ".sh", ".bash", ".zsh"} and (not first_line or not first_line[0].startswith("#!")):
                    findings.append(Finding("warning", str(script), "script has no shebang"))

    tests_dir = repo_root / "tests" / skill_dir.name
    if not tests_dir.exists():
        findings.append(Finding("error", str(tests_dir), "repository-level tests directory is missing"))

    for path in skill_dir.rglob("*"):
        if path.name in FORBIDDEN_DOC_NAMES:
            findings.append(Finding("error", str(path), "do not put auxiliary docs inside skill folders"))
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
            findings.append(Finding("error", str(path), "generated Python cache should not be inside skill folders"))

    if not skill_dir.is_dir():
        findings.append(Finding("error", str(rel_skill), "skill path is not a directory"))
    return findings


def discover_skill_dirs(repo_root: Path) -> list[Path]:
    skills_dir = repo_root / "skills"
    if not skills_dir.exists():
        return []
    return sorted(path for path in skills_dir.iterdir() if path.is_dir())


def validate_repository(repo_root: Path, skill_name: str | None = None) -> list[Finding]:
    skill_dirs = discover_skill_dirs(repo_root)
    if skill_name:
        skill_dirs = [repo_root / "skills" / skill_name]
    findings: list[Finding] = []
    if not skill_dirs:
        findings.append(Finding("error", str(repo_root / "skills"), "no skill directories found"))
    for skill_dir in skill_dirs:
        findings.extend(validate_skill(skill_dir, repo_root))
    return findings


def print_text(findings: list[Finding]) -> None:
    if not findings:
        print("All skills passed validation.")
        return
    for finding in findings:
        print(f"{finding.level.upper()}: {finding.path}: {finding.message}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root. Defaults to current directory.")
    parser.add_argument("--skill", help="Validate only one skill name.")
    parser.add_argument("--json", action="store_true", help="Print JSON findings.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    repo_root = args.root.resolve()
    findings = validate_repository(repo_root, args.skill)
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2, ensure_ascii=False))
    else:
        print_text(findings)
    return 1 if any(item.level == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
