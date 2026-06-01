import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "skill-scaffolder" / "scripts" / "scaffold_skill.py"


def load_module():
    spec = importlib.util.spec_from_file_location("scaffold_skill", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ScaffoldSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_normalizes_skill_name(self):
        self.assertEqual(self.module.normalize_skill_name("My New Skill!"), "my-new-skill")

    def test_scaffolds_standard_skill_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.module.scaffold_skill(
                raw_name="Demo Skill",
                repo_root=root,
                resources={"scripts", "references"},
                create_tests=True,
            )

            skill_dir = root / "skills" / "demo-skill"
            self.assertEqual(result["skill_name"], "demo-skill")
            self.assertTrue((skill_dir / "SKILL.md").exists())
            self.assertTrue((skill_dir / "agents" / "openai.yaml").exists())
            self.assertTrue((skill_dir / "scripts").is_dir())
            self.assertTrue((skill_dir / "references").is_dir())
            self.assertFalse((skill_dir / "README.md").exists())
            self.assertTrue((root / "tests" / "demo-skill" / "test_demo_skill.py").exists())
            self.assertIn("$demo-skill", (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8"))

    def test_refuses_existing_files_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.module.scaffold_skill("demo", root, set())
            with self.assertRaises(FileExistsError):
                self.module.scaffold_skill("demo", root, set())


if __name__ == "__main__":
    unittest.main()
