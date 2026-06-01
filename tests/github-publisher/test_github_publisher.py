import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "github-publisher"


class GitHubPublisherTests(unittest.TestCase):
    def test_references_are_linked_from_skill(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/publish-workflow.md", skill)
        self.assertIn("references/troubleshooting.md", skill)

    def test_publish_workflow_keeps_user_in_control(self):
        workflow = (SKILL_DIR / "references" / "publish-workflow.md").read_text(encoding="utf-8")
        troubleshooting = (SKILL_DIR / "references" / "troubleshooting.md").read_text(encoding="utf-8")
        self.assertIn("Do not echo tokens", workflow)
        self.assertIn("Push only after the user asks", workflow)
        self.assertIn("Do not force-push by default", troubleshooting)


if __name__ == "__main__":
    unittest.main()
