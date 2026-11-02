import copy
import base64
import json
import unittest
from pathlib import Path
from src.gimliforge import InputError, render, render_latex, validate
from src.ai import build_prompt, draft, local_api_key
from unittest.mock import patch
from io import BytesIO
from tempfile import TemporaryDirectory

SAMPLE = json.loads((Path(__file__).parents[1] / "datos_entrada" / "demo.json").read_text(encoding="utf-8"))

class GimliForgeTests(unittest.TestCase):
    def test_demo(self):
        report = render(validate(SAMPLE))
        self.assertIn("VULN-001", report)
        self.assertIn("VULN-002", report)

    def test_html_escaping(self):
        data = copy.deepcopy(SAMPLE)
        data["hallazgos"][0]["titulo"] = "<script>alert(1)</script>"
        report = render(validate(data))
        self.assertNotIn("<script>", report)
        self.assertIn("&lt;script&gt;", report)

    def test_latex_escaping_and_structure(self):
        data = copy.deepcopy(SAMPLE)
        data["metadata"]["cliente"] = "ACME_100% & Co"
        report = render_latex(validate(data))
        self.assertIn(r"ACME\_100\% \& Co", report)
        self.assertIn(r"\section{Detalle técnico de hallazgos}", report)
        self.assertIn("[ GIMLIFORGE ]", report)
        self.assertIn(r"\begin{tikzpicture}", report)
        self.assertEqual(report.count(r"\begin{tikzpicture}"), 5)
        self.assertIn(r"\section{Hoja de ruta de mitigación}", report)
        self.assertIn("Pendiente de completar: evidencia", report)

    def test_ai_prompt_keeps_original_constraints(self):
        prompt = build_prompt(SAMPLE)
        self.assertIn("No inventes", prompt)
        self.assertIn("cifras económicas", prompt)
        self.assertIn("No generes LaTeX", prompt)

    def test_ai_is_opt_in_and_requires_key(self):
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "", "GEMINI_API_KEY": ""}), patch("src.ai.local_api_key", return_value=""):
            with self.assertRaises(InputError):
                draft(SAMPLE)

    def test_local_key_is_read_from_ignored_env_file(self):
        with TemporaryDirectory() as directory:
            key_file = Path(directory) / ".env"
            key_file.write_text("# Local only\nGEMINI_API_KEY=example-test-key\n", encoding="utf-8")
            with patch("src.ai.KEY_FILE", key_file):
                self.assertEqual(local_api_key(), "example-test-key")

    def test_ai_draft_is_structured_and_reviewable(self):
        reply = {"candidates": [{"content": {"parts": [{"text": json.dumps({
            "resumen_ejecutivo": "Resumen a revisar",
            "impacto_negocio": "Impacto a revisar",
            "conclusiones": "Conclusiones a revisar",
            "hallazgos": [{"id": item["id"], "impacto": "Impacto propuesto", "recomendacion": "Medida propuesta"}
                          for item in SAMPLE["hallazgos"]]
        })}]}}]}
        stream = BytesIO(json.dumps(reply).encode("utf-8"))
        with patch("src.ai.urlopen", return_value=stream):
            proposal = draft(SAMPLE, api_key="fake-test-key")
        self.assertEqual(proposal["hallazgos"][0]["id"], "VULN-001")
        self.assertEqual(proposal["resumen_ejecutivo"], "Resumen a revisar")

    def test_invalid_cvss_and_duplicate(self):
        data = copy.deepcopy(SAMPLE)
        data["hallazgos"][0]["cvss"] = 11
        with self.assertRaises(InputError): validate(data)
        data = copy.deepcopy(SAMPLE)
        data["hallazgos"][1]["id"] = data["hallazgos"][0]["id"]
        with self.assertRaises(InputError): validate(data)

    def test_legacy_title_and_empty(self):
        data = copy.deepcopy(SAMPLE)
        data["hallazgos"][0]["tipo"] = data["hallazgos"][0].pop("titulo")
        self.assertEqual(len(validate(data)["hallazgos"]), 2)
        data["hallazgos"] = []
        self.assertIn("Sin hallazgos", render(validate(data)))

    def test_full_report_keeps_evidence_and_charts(self):
        source = Path(__file__).parents[1] / "datos_entrada" / "demo_extensa.json"
        report = render_latex(validate(json.loads(source.read_text(encoding="utf-8"))))
        self.assertIn("Evidencia registrada", report)
        self.assertIn("session\\_token", report)
        self.assertEqual(report.count(r"\begin{tikzpicture}"), 5)
        self.assertGreaterEqual(report.count(r"\clearpage"), 3)
        self.assertIn("Trazabilidad y calidad de la información", report)
        self.assertIn("Tratamiento y comprobación de cierre", report)

    def test_image_evidence_is_in_report_but_not_gemini_prompt(self):
        data = copy.deepcopy(SAMPLE)
        data["hallazgos"][0]["imagenes"] = [{"nombre": "captura.png", "mime": "image/png",
            "leyenda": "Evidencia de laboratorio", "data": base64.b64encode(b"\x89PNG\r\n\x1a\nmock-image").decode()}]
        clean = validate(data)
        report = render_latex(clean)
        self.assertIn(r"\includegraphics", report)
        self.assertIn("Evidencia de laboratorio", report)
        self.assertNotIn(clean["hallazgos"][0]["imagenes"][0]["data"], build_prompt(clean))
        data["hallazgos"][0]["imagenes"][0]["mime"] = "image/svg+xml"
        with self.assertRaises(InputError):
            validate(data)
