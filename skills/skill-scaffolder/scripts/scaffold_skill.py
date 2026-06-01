#!/usr/bin/env python3
"""Create a standard Codex skill skeleton in this repository."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable


VALID_RESOURCES = {"scripts", "references", "assets"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


def normalize_skill_name(value: str) -> str:
    name = value.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-{2,}", "-", name).strip("-")
    if not name or not NAME_RE.fullmatch(name):
        raise ValueError("skill name must normalize to lowercase letters, digits, and hyphens under 64 characters")
    return name


def display_name(skill_name: str) -> str:
    return " ".join(part.capitalize() for part in skill_name.split("-"))


def parse_resources(value: str | None) -> set[str]:
    if not value:
        return set()
    resources = {item.strip() for item in value.split(",") if item.strip()}
    unknown = resources - VALID_RESOURCES
    if unknown:
        raise ValueError(f"unknown resources: {', '.join(sorted(unknown))}")
    return resources


def write_new_file(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def scaffold_skill(
    raw_name: str,
    repo_root: Path,
    resources: set[str],
    create_tests: bool = True,
    force: bool = False,
) -> dict[str, object]:
    skill_name = normalize_skill_name(raw_name)
    skill_dir = repo_root / "skills" / skill_name
    test_dir = repo_root / "tests" / skill_name
    created: list[str] = []

    skill_dir.mkdir(parents=True, exist_ok=True)
    agents_dir = skill_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    skill_md = f"""---\nname: {skill_name}\ndescription: TODO: Describe what this skill does and the exact situations when Codex should use it.\n---\n\n# {display_name(skill_name)}\n\n## Overview\n\nTODO: Explain the skill in one or two concise sentences.\n\n## Workflow\n\n1. TODO: Add the first step.\n2. TODO: Add the next step.\n\n## Resources\n\nUse bundled resources only when they directly support this skill. Do not add README, CHANGELOG, installation guides, or process notes inside this skill folder.\n"""
    if write_new_file(skill_dir / "SKILL.md", skill_md, force):
        created.append(str(skill_dir / "SKILL.md"))

    openai_yaml = f"""interface:\n  display_name: "{display_name(skill_name)}"\n  short_description: "TODO: Short UI description for this skill"\n  default_prompt: "Use ${skill_name} to TODO: describe the starting task."\n"""
    if write_new_file(agents_dir / "openai.yaml", openai_yaml, force):
        created.append(str(agents_dir / "openai.yaml"))

    for resource in sorted(resources):
        resource_dir = skill_dir / resource
        resource_dir.mkdir(parents=True, exist_ok=True)
        created.append(str(resource_dir))

    if create_tests:
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / f"test_{skill_name.replace('-', '_')}.py"
        test_content = f"""import unittest\nfrom pathlib import Path\n\n\nROOT = Path(__file__).resolve().parents[2]\nSKILL_DIR = ROOT / "skills" / "{skill_name}"\n\n\nclass {''.join(part.capitalize() for part in skill_name.split('-'))}ScaffoldTests(unittest.TestCase):\n    def test_skill_files_exist(self):\n        self.assertTrue((SKILL_DIR / "SKILL.md").exists())\n        self.assertTrue((SKILL_DIR / "agents" / "openai.yaml").exists())\n\n\nif __name__ == "__main__":\n    unittest.main()\n"""
        if write_new_file(test_file, test_content, force):
            created.append(str(test_file))

    return {"skill_name": skill_name, "skill_dir": str(skill_dir), "test_dir": str(test_dir), "created": created}


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_name", help="Skill name or title to normalize.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root. Defaults to current directory.")
    parser.add_argument("--resources", help="Comma-separated optional resources: scripts,references,assets.")
    parser.add_argument("--no-tests", action="store_true", help="Do not create tests/<skill-name>/ scaffold.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated files.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    try:
        result = scaffold_skill(
            raw_name=args.skill_name,
            repo_root=args.repo_root.resolve(),
            resources=parse_resources(args.resources),
            create_tests=not args.no_tests,
            force=args.force,
        )
    except Exception as exc:
        print(f"scaffold_skill.py: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Created scaffold for {result['skill_name']}: {result['skill_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
