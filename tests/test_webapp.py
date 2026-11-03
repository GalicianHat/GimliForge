import json
import base64
import copy
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile
from io import BytesIO

from src.webapp import ProjectStore, handler_for

SAMPLE = json.loads((Path(__file__).parents[1] / "datos_entrada" / "demo.json").read_text(encoding="utf-8"))


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(ProjectStore(Path(self.temp.name))))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def test_create_reopen_and_export_tex(self):
        body = json.dumps(SAMPLE).encode()
        request = Request(self.base + "/api/projects", body, {"Content-Type": "application/json"})
        with urlopen(request) as response:
            identifier = json.load(response)["id"]
        with urlopen(self.base + "/api/projects") as response:
            self.assertEqual(len(json.load(response)), 1)
        with urlopen(self.base + f"/api/projects/{identifier}") as response:
            self.assertEqual(json.load(response)["metadata"]["cliente"], SAMPLE["metadata"]["cliente"])
        with urlopen(self.base + f"/api/projects/{identifier}/export/tex") as response:
            self.assertIn(b"\\documentclass", response.read())

    def test_invalid_input_and_host_rejected(self):
        bad = {"metadata": SAMPLE["metadata"], "hallazgos": [{"id": "X"}]}
        request = Request(self.base + "/api/projects", json.dumps(bad).encode(), {"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 400)
        request = Request(self.base + "/api/projects", headers={"Host": "evil.example"})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 403)

    def test_brand_assets_are_served_locally(self):
        for path, mime in (("/gimli-bg.jpg", "image/jpeg"),
                           ("/forge-effects.js", "text/javascript"),
                           ("/fonts/Cinzel-700.ttf", "font/ttf")):
            with self.subTest(path=path), urlopen(self.base + path) as response:
                self.assertTrue(response.headers["Content-Type"].startswith(mime))
                self.assertGreater(len(response.read()), 100)
                self.assertIn("img-src 'self'", response.headers["Content-Security-Policy"])
                self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
                self.assertEqual(response.headers["X-Frame-Options"], "DENY")
                self.assertEqual(response.headers["Cross-Origin-Resource-Policy"], "same-origin")

    def test_image_sources_and_local_key_settings(self):
        key_request = Request(self.base + "/api/settings/gemini", json.dumps({"key": "example-private-test-key"}).encode(),
                              {"Content-Type": "application/json"})
        with urlopen(key_request) as response:
            self.assertTrue(json.load(response)["configured"])
        with urlopen(self.base + "/api/settings/gemini") as response:
            status = response.read()
            self.assertIn(b'"configured": true', status)
            self.assertNotIn(b"example-private-test-key", status)
        self.assertEqual((Path(self.temp.name) / ".gemini-key").read_text(), "example-private-test-key")
        data = copy.deepcopy(SAMPLE)
        data["hallazgos"][0]["imagenes"] = [{"nombre": "captura.png", "mime": "image/png", "leyenda": "Prueba",
            "data": base64.b64encode(b"\x89PNG\r\n\x1a\nmock-image").decode()}]
        request = Request(self.base + "/api/projects", json.dumps(data).encode(), {"Content-Type": "application/json"})
        with urlopen(request) as response:
            identifier = json.load(response)["id"]
        self.assertNotIn("example-private-test-key", (Path(self.temp.name) / f"{identifier}.json").read_text())
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/.gemini-key")
        self.assertEqual(error.exception.code, 404)
        with urlopen(self.base + f"/api/projects/{identifier}/export/tex") as response:
            self.assertEqual(response.headers["Content-Type"], "application/zip")
            with ZipFile(BytesIO(response.read())) as archive:
                names = archive.namelist()
                self.assertIn("informe_gimliforge.tex", names)
                self.assertTrue(any(name.startswith("evidencias/") for name in names))
