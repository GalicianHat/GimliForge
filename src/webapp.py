"""Local browser interface. Binds only to loopback and stores projects as JSON."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import webbrowser
from io import BytesIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from .gimliforge import InputError, MAX_INPUT_BYTES, render_latex, validate
from .evidence import iter_images, write_images

APP_DIR = Path(__file__).parents[1]
INDEX = APP_DIR / "web" / "index.html"
STATIC_ASSETS = {
    "/forge-effects.js": ("forge-effects.js", "text/javascript; charset=utf-8"),
    "/gimli-bg.jpg": ("gimli-bg.jpg", "image/jpeg"),
    "/fonts/Cinzel-700.ttf": ("fonts/Cinzel-700.ttf", "font/ttf"),
    "/fonts/Inter-400.ttf": ("fonts/Inter-400.ttf", "font/ttf"),
    "/fonts/Inter-600.ttf": ("fonts/Inter-600.ttf", "font/ttf"),
}
ID_RE = re.compile(r"^[0-9a-f]{32}$")


class ProjectStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, identifier: str) -> Path:
        if not ID_RE.fullmatch(identifier):
            raise InputError("Identificador de proyecto no válido")
        return self.root / f"{identifier}.json"

    def list(self):
        projects = []
        for path in self.root.glob("*.json"):
            if not ID_RE.fullmatch(path.stem):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                projects.append({"id": path.stem, "cliente": data["metadata"]["cliente"],
                                 "fecha": data["metadata"]["fecha_auditoria"],
                                 "hallazgos": len(data["hallazgos"])})
            except (OSError, ValueError, KeyError, TypeError):
                continue
        return sorted(projects, key=lambda item: item["fecha"], reverse=True)

    def get(self, identifier):
        try:
            return validate(json.loads(self.path(identifier).read_text(encoding="utf-8")))
        except FileNotFoundError as exc:
            raise InputError("Proyecto no encontrado") from exc

    def save(self, data, identifier=None):
        clean = validate(data)
        identifier = identifier or uuid.uuid4().hex
        target = self.path(identifier)
        payload = json.dumps(clean, ensure_ascii=False, indent=2)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.root,
                                         prefix=".gimli-", suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            stream.write(payload)
        os.replace(temp, target)
        return identifier

    def gemini_key(self):
        try:
            return (self.root / ".gemini-key").read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return ""

    def save_gemini_key(self, key):
        if not isinstance(key, str) or not 10 <= len(key.strip()) <= 300 or any(char.isspace() for char in key):
            raise InputError("Pegue una clave API válida, sin espacios")
        target = self.root / ".gemini-key"
        descriptor, name = tempfile.mkstemp(prefix=".gemini-", dir=self.root)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(key.strip())
            os.chmod(name, 0o600)
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)


def handler_for(store: ProjectStore):
    class Handler(BaseHTTPRequestHandler):
        server_version = "GimliForge/2.0"

        def log_message(self, format, *args):
            pass

        def send_bytes(self, data: bytes, mime: str, status=200, filename=None):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, obj, status=200):
            self.send_bytes(json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

        def local_request(self):
            host = self.headers.get("Host", "")
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            return host in allowed

        def do_GET(self):
            if not self.local_request():
                return self.send_json({"error": "Host no permitido"}, 403)
            path = urlsplit(self.path).path
            try:
                if path == "/":
                    return self.send_bytes(INDEX.read_bytes(), "text/html; charset=utf-8")
                if path == "/app.js":
                    return self.send_bytes((INDEX.parent / "app.js").read_bytes(), "text/javascript; charset=utf-8")
                if path == "/style.css":
                    return self.send_bytes((INDEX.parent / "style.css").read_bytes(), "text/css; charset=utf-8")
                if path in STATIC_ASSETS:
                    filename, mime = STATIC_ASSETS[path]
                    return self.send_bytes((INDEX.parent / filename).read_bytes(), mime)
                if path == "/api/projects":
                    return self.send_json(store.list())
                if path == "/api/settings/gemini":
                    from .ai import local_api_key
                    return self.send_json({"configured": bool(store.gemini_key() or os.environ.get("GOOGLE_API_KEY")
                                                               or os.environ.get("GEMINI_API_KEY") or local_api_key())})
                match = re.fullmatch(r"/api/projects/([0-9a-f]{32})", path)
                if match:
                    return self.send_json(store.get(match.group(1)))
                match = re.fullmatch(r"/api/projects/([0-9a-f]{32})/export/(tex|pdf)", path)
                if match:
                    data = store.get(match.group(1))
                    tex = render_latex(data).encode("utf-8")
                    if match.group(2) == "tex":
                        images = list(iter_images(data["hallazgos"]))
                        if not images:
                            return self.send_bytes(tex, "application/x-tex; charset=utf-8", filename="informe_gimliforge.tex")
                        buffer = BytesIO()
                        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
                            archive.writestr("informe_gimliforge.tex", tex)
                            for name, raw in images:
                                archive.writestr(name, raw)
                        return self.send_bytes(buffer.getvalue(), "application/zip", filename="informe_gimliforge_fuentes.zip")
                    compiler = shutil.which("pdflatex")
                    if not compiler:
                        raise InputError("Para generar PDF, instale pdflatex. Guía: https://adriansr.com/gimli#pdf. El archivo LaTeX se puede descargar igualmente.")
                    with tempfile.TemporaryDirectory(prefix="gimliforge-") as tmp:
                        source = Path(tmp) / "informe.tex"
                        source.write_bytes(tex)
                        write_images(Path(tmp), data["hallazgos"])
                        for _ in range(2):
                            installer = ["-enable-installer"] if "miktex" in compiler.lower() else []
                            result = subprocess.run([compiler, *installer, "-interaction=nonstopmode", "-halt-on-error", "-output-directory", ".", source.name],
                                                    cwd=tmp, capture_output=True, timeout=180)
                            if result.returncode:
                                raise InputError("No se pudo compilar el PDF. Descargue el .tex para revisar el error.")
                        return self.send_bytes(source.with_suffix(".pdf").read_bytes(), "application/pdf", filename="informe_gimliforge.pdf")
                return self.send_json({"error": "Ruta no encontrada"}, 404)
            except (InputError, OSError, subprocess.TimeoutExpired) as exc:
                return self.send_json({"error": str(exc)}, 400)

        def do_POST(self):
            if not self.local_request():
                return self.send_json({"error": "Host no permitido"}, 403)
            origin = self.headers.get("Origin")
            if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
                return self.send_json({"error": "Origen no permitido"}, 403)
            path = urlsplit(self.path).path
            if path == "/api/settings/gemini":
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size <= 500:
                        raise InputError("La clave API no tiene un tamaño válido")
                    payload = json.loads(self.rfile.read(size).decode("utf-8"))
                    store.save_gemini_key(payload.get("key"))
                    return self.send_json({"configured": True})
                except (ValueError, UnicodeError, OSError, AttributeError) as exc:
                    return self.send_json({"error": str(exc)}, 400)
            ai_match = re.fullmatch(r"/api/projects/([0-9a-f]{32})/ai-draft", path)
            if ai_match:
                try:
                    from .ai import draft
                    return self.send_json(draft(store.get(ai_match.group(1)), api_key=store.gemini_key() or None))
                except InputError as exc:
                    return self.send_json({"error": str(exc)}, 400)
            match = re.fullmatch(r"/api/projects(?:/([0-9a-f]{32}))?", path)
            if not match:
                return self.send_json({"error": "Ruta no encontrada"}, 404)
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= MAX_INPUT_BYTES:
                    raise InputError("El JSON debe pesar entre 1 byte y 20 MB")
                data = json.loads(self.rfile.read(size).decode("utf-8"))
                identifier = match.group(1)
                if identifier and not store.path(identifier).exists():
                    raise InputError("Proyecto no encontrado")
                return self.send_json({"id": store.save(data, identifier)}, 200 if identifier else 201)
            except (ValueError, UnicodeError, OSError) as exc:
                return self.send_json({"error": str(exc)}, 400)

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="GimliForge 2.0 en el navegador")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path, default=APP_DIR / "projects")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    store = ProjectStore(args.data_dir)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(store))
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"GimliForge 2.0: {url}\nProyectos: {store.root}\nPulse Ctrl+C para cerrar.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
