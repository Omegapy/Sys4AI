import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from memory_core import MemoryError
from memory_normalization import normalize_document, build_normalized, digest
from memory_search import search
from test_retrieval import setup_project, manifest


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.config = setup_project(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_tex_preserves_math_environments_labels_and_citations(self):
        raw = r"\section{Bound}" + "\n" + r"\begin{theorem}\label{thm:alpha} For $x>0$, $x^2\geq0$.\end{theorem}" + "\n" + r"\begin{proof}\begin{equation}\label{eq:mass} E=mc^2\end{equation}\end{proof}" + "\n" + r"See \eqref{eq:mass} and \cite{Einstein1905}."
        (self.root / "research/theorem.tex").write_text(raw)
        before = manifest(self.root)
        doc = normalize_document(self.root, "research/theorem.tex", self.config)
        self.assertEqual("".join(x["text"] for x in doc["segments"]), raw)
        result = search(self.root, "eq:mass")["results"][0]
        self.assertIn("eq:mass", result["labels"])
        self.assertIn("proof", result["environments"])
        self.assertIn("Einstein1905", result["bibliography_keys"])
        self.assertEqual(before, manifest(self.root))

    def test_html_retains_heading_and_discards_presentation(self):
        (self.root / "research/paper.html").write_text('<html><head><title>NOISE</title></head><body><nav>NAVSENTINEL</nav><h2 id="result">Result</h2><p>Conservation of angular momentum.</p><script>SECRETSCRIPT</script><div hidden>HIDDENVALUE</div></body></html>')
        result = search(self.root, "angular momentum")["results"][0]
        self.assertEqual(result["locator"], "research/paper.html#result")
        self.assertEqual(result["heading"], "Result")
        for query in ("NAVSENTINEL", "SECRETSCRIPT", "HIDDENVALUE"):
            self.assertFalse(search(self.root, query)["results"])

    def test_pdf_pages_scans_and_evidenced_companions(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest("Optional declared PyMuPDF extraction is not installed.")
        doc = pymupdf.open()
        doc.new_page().insert_text((72, 72), "Radiative pressure EQUATION-1905")
        doc.new_page()
        doc.save(self.root / "research/paper.pdf")
        doc.close()
        (self.root / "research/paper.tex").write_text(r"\section{Pressure} Radiative pressure EQUATION-1905")
        relationship = self.root / "docs/relationship.md"
        relationship.write_text("The fixture PDF was generated from the companion TeX source for this test.\n")
        self.config["corpus"]["source_groups"] = [{"id": "pressure-evidence", "paths": ["research/paper.tex", "research/paper.pdf"],
            "evidence": {"path": "docs/relationship.md", "sha256": digest(relationship.read_bytes())}}]
        (self.root / "memory.yaml").write_text(json.dumps(self.config))
        before = manifest(self.root)
        extracted = normalize_document(self.root, "research/paper.pdf", self.config)
        self.assertEqual(extracted["segments"][0]["page"], 1)
        self.assertTrue(any("Page 2" in s for s in extracted["limitations"]))
        results = search(self.root, "EQUATION-1905")["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]["representations"]), 2)
        self.assertEqual(before, manifest(self.root))
        relationship.write_text("Relationship is no longer confirmed.\n")
        with self.assertRaises(MemoryError):
            normalize_document(self.root, "research/paper.pdf", self.config)

    def test_stale_cache_is_observed_without_repair(self):
        path = self.root / "research/cache.tex"
        path.write_text(r"\section{Cache} CACHE-OLD")
        result = build_normalized(self.root, self.config)
        self.assertTrue(result["products"])
        path.write_text(r"\section{Cache} CACHE-NEW")
        before = manifest(self.root)
        found = search(self.root, "CACHE-NEW")["results"][0]
        self.assertTrue(any("stale" in s for s in found["limitations"]))
        self.assertEqual(before, manifest(self.root))


if __name__ == "__main__":
    unittest.main()
