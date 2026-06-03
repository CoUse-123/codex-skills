import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "pdf-text-extractor" / "scripts" / "extract_pdf_text.py"
FIXTURE = ROOT / "tests" / "pdf-text-extractor" / "fixtures" / "sample.pdf"


def load_module():
    spec = importlib.util.spec_from_file_location("extract_pdf_text", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PdfTextExtractorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_extracts_page_text_and_table_like_rows(self):
        result = self.module.extract_pdf(FIXTURE)

        self.assertFalse(result.needs_ocr)
        self.assertEqual(result.source_metadata["page_count"], 2)
        self.assertIn("Quarterly Brief", result.pages[0].text)
        self.assertIn("Risk: vendor timeline is unknown.", result.pages[1].text)
        self.assertGreaterEqual(len(result.tables), 1)
        self.assertEqual(result.tables[0].rows[0], ["Item", "Owner", "Status"])

    def test_cli_outputs_json(self):
        proc = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(FIXTURE), "--format", "json"],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(proc.stdout)
        self.assertFalse(payload["needs_ocr"])
        self.assertEqual(payload["source_metadata"]["file_name"], "sample.pdf")
        self.assertIn("Page Two", payload["pages"][1]["text"])

    def test_reports_ocr_needed_when_no_text_layer(self):
        page = self.module.make_page(1, "")
        self.assertTrue(page.needs_ocr)


if __name__ == "__main__":
    unittest.main()
