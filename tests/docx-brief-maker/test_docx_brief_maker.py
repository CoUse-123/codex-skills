import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "docx-brief-maker" / "scripts" / "extract_docx_brief.py"
DOCUMENT_XML = ROOT / "tests" / "docx-brief-maker" / "fixtures" / "document.xml"


def load_module():
    spec = importlib.util.spec_from_file_location("extract_docx_brief", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def create_docx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        archive.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>')
        archive.writestr("word/document.xml", DOCUMENT_XML.read_text(encoding="utf-8"))


class DocxBriefMakerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_extracts_docx_structure_and_brief_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx = Path(tmp) / "sample.docx"
            create_docx(docx)

            result = self.module.extract_docx(docx)

            self.assertEqual(result.source_metadata["paragraph_count"], 4)
            self.assertEqual(result.source_metadata["table_count"], 1)
            self.assertIn("Launch Meeting Notes", result.summary[0])
            self.assertTrue(any(item["owner"] == "Alex" for item in result.action_items))
            self.assertTrue(any(item["owner"] == "Jamie" for item in result.action_items))
            self.assertTrue(any("support staffing" in item for item in result.risks_or_questions))

    def test_cli_outputs_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx = Path(tmp) / "sample.docx"
            create_docx(docx)

            proc = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), str(docx), "--format", "json"],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(proc.stdout)
        self.assertEqual(payload["source_metadata"]["file_name"], "sample.docx")
        self.assertGreaterEqual(len(payload["action_items"]), 2)
        self.assertIn("suggested_edits", payload)


if __name__ == "__main__":
    unittest.main()
