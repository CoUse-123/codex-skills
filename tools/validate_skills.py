#!/usr/bin/env python3
"""Repository wrapper for the skill-validator script."""

from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "skill-validator" / "scripts" / "validate_skills.py"

if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
