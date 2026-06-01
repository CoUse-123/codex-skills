import importlib.util
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "skill-validator" / "scripts" / "validate_skills.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_skills", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateSkillsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def write_valid_skill(self, root: Path, name: str = "demo-skill") -> Path:
        skill_dir = root / "skills" / name
        (skill_dir / "agents").mkdir(parents=True)
        (skill_dir / "scripts").mkdir()
        (root / "tests" / name).mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Validate a demo skill for tests.\n---\n\n# Demo\n",
            encoding="utf-8",
        )
        (skill_dir / "agents" / "openai.yaml").write_text(
            f'interface:\n  display_name: "Demo Skill"\n  short_description: "Validate a demo skill"\n  default_prompt: "Use ${name} to validate a demo skill."\n',
            encoding="utf-8",
        )
        script = skill_dir / "scripts" / "demo.py"
        script.write_text("#!/usr/bin/env python3\nprint('ok')\n", encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        return skill_dir

    def test_valid_repository_has_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_valid_skill(root)
            findings = self.module.validate_repository(root)
            self.assertEqual(findings, [])

    def test_frontmatter_extra_key_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = self.write_valid_skill(root)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: Demo.\nmetadata: nope\n---\n",
                encoding="utf-8",
            )
            findings = self.module.validate_repository(root)
            self.assertTrue(any("frontmatter must contain only" in item.message for item in findings))

    def test_non_executable_script_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = self.write_valid_skill(root)
            script = skill_dir / "scripts" / "demo.py"
            script.chmod(script.stat().st_mode & ~stat.S_IXUSR)
            findings = self.module.validate_repository(root)
            self.assertTrue(any("script should be executable" in item.message for item in findings))


if __name__ == "__main__":
    unittest.main()
