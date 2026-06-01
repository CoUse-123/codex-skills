import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "crawl-web-text" / "scripts" / "extract_web_text.py"
FIXTURE = ROOT / "tests" / "crawl-web-text" / "fixtures" / "sample-page.html"


def load_module():
    spec = importlib.util.spec_from_file_location("extract_web_text", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ExtractWebTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_extracts_visible_text_from_saved_html(self):
        html = FIXTURE.read_text(encoding="utf-8")
        source = self.module.SourceRecord(
            source=str(FIXTURE),
            source_type="file",
            fetched_at="2026-06-01T00:00:00+00:00",
        )

        result = self.module.extract_from_html(html, source)

        self.assertEqual(result.title, "Sample Public Page")
        self.assertIn("Example Heading", result.text)
        self.assertIn("This is the first paragraph.", result.text)
        self.assertIn("First item", result.text)
        self.assertNotIn("Skip this navigation", result.text)
        self.assertNotIn("ignore me", result.text)
        self.assertNotIn("hidden paragraph", result.text)
        self.assertNotIn("Invisible section", result.text)

    def test_cli_outputs_json_for_saved_html(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input-file",
                str(FIXTURE),
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(proc.stdout)
        self.assertEqual(payload["title"], "Sample Public Page")
        self.assertEqual(payload["source"]["source_type"], "file")
        self.assertGreater(payload["word_count"], 0)
        self.assertIn("Second item", payload["text"])


if __name__ == "__main__":
    unittest.main()
