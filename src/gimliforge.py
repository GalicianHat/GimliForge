"""GimliForge 2.0: deterministic, offline security report generation."""
from __future__ import annotations

import argparse
import html
import json
import sys
import shutil
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

SEVERITIES = ("Crítica", "Alta", "Media", "Baja", "Informativa")
COLORS = {"Crítica": "#e34b60", "Alta": "#f28b55", "Media": "#e7bc54", "Baja": "#6eaf8d", "Informativa": "#739ebd"}
MAX_INPUT_BYTES = 20_000_000


class InputError(ValueError):
    """Invalid audit input, safe to show to a user."""


def _text(value, field, limit=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise InputError(f"{field}: se requiere texto entre 1 y {limit} caracteres")
    return value.strip()


def validate(data):
    from .evidence import validate_images
    if not isinstance(data, dict):
        raise InputError("La raíz debe ser un objeto JSON")
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise InputError("Falta el objeto metadata")
    for field in ("cliente", "auditor", "fecha_auditoria"):
        _text(metadata.get(field), f"metadata.{field}", 200)
    try:
        date.fromisoformat(metadata["fecha_auditoria"])
    except ValueError as exc:
        raise InputError("metadata.fecha_auditoria debe usar AAAA-MM-DD") from exc
    findings = data.get("hallazgos")
    if not isinstance(findings, list) or len(findings) > 500:
        raise InputError("hallazgos debe ser una lista de hasta 500 elementos")
    ids = set()
    normalized = []
    for index, finding in enumerate(findings, 1):
        if not isinstance(finding, dict):
            raise InputError(f"hallazgos[{index}]: se requiere un objeto")
        identifier = _text(finding.get("id"), f"hallazgos[{index}].id", 80)
        if identifier in ids:
            raise InputError(f"ID duplicado: {identifier}")
        ids.add(identifier)
        severity = _text(finding.get("severidad"), f"hallazgos[{index}].severidad", 30)
        if severity not in SEVERITIES:
            raise InputError(f"{identifier}: severidad no reconocida")
        title = _text(finding.get("titulo", finding.get("tipo")), f"{identifier}.titulo", 200)
        description = _text(finding.get("descripcion_tecnica"), f"{identifier}.descripcion_tecnica", 5000)
        category = _text(finding.get("categoria", "Sin categorizar"), f"{identifier}.categoria", 100)
        cvss = finding.get("cvss")
        if cvss is not None and (isinstance(cvss, bool) or not isinstance(cvss, (int, float)) or not 0 <= cvss <= 10):
            raise InputError(f"{identifier}: CVSS debe estar entre 0 y 10")
        normalized.append(dict(id=identifier, titulo=title, severidad=severity, categoria=category,
                               cvss=cvss, descripcion_tecnica=description))
        for field, limit in (("recomendacion", 3000), ("activo", 200), ("evidencia", 4000),
                             ("impacto", 3000), ("reproduccion", 3000), ("referencias", 1000)):
            value = finding.get(field, "")
            if value:
                normalized[-1][field] = _text(value, f"{identifier}.{field}", limit)
            else:
                normalized[-1][field] = ""
        normalized[-1]["imagenes"] = validate_images(finding.get("imagenes"), identifier)
    for field, limit in (("alcance", 2000), ("metodologia", 2000), ("resumen_ejecutivo", 5000),
                         ("impacto_negocio", 4000), ("conclusiones", 3000)):
        value = metadata.get(field, "")
        if value:
            metadata[field] = _text(value, f"metadata.{field}", limit)
        else:
            metadata[field] = ""
    return {"metadata": metadata, "hallazgos": normalized}


def load(path):
    source = Path(path)
    if source.stat().st_size > MAX_INPUT_BYTES:
        raise InputError("El JSON supera el límite de 20 MB")
    try:
        return validate(json.loads(source.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise InputError(f"JSON inválido en línea {exc.lineno}") from exc


def render(data):
    m, findings = data["metadata"], data["hallazgos"]
    esc = html.escape
    counts = Counter(f["severidad"] for f in findings)
    cats = Counter(f["categoria"] for f in findings)
    bars = "".join(f'<div class="bar-row"><span>{esc(s)}</span><div class="track"><i style="width:{100 * counts[s] / max(1,len(findings)):.1f}%;background:{COLORS[s]}"></i></div><b>{counts[s]}</b></div>' for s in SEVERITIES)
    cat_rows = "".join(f"<li>{esc(k)} <strong>{v}</strong></li>" for k, v in cats.most_common()) or "<li>Sin hallazgos</li>"
    cards = []
    for f in findings:
        cvss = f" · CVSS {f['cvss']:.1f}" if f["cvss"] is not None else " · CVSS no informado"
        recommendation = f'<p class="recommend"><b>Recomendación:</b> {esc(f["recomendacion"])}</p>' if f["recomendacion"] else ""
        cards.append(f'<article class="finding"><div class="finding-head"><span>{esc(f["id"])} · {esc(f["categoria"])}</span><span class="severity" style="color:{COLORS[f["severidad"]]}">{esc(f["severidad"])}{esc(cvss)}</span></div><h3>{esc(f["titulo"])}</h3><p>{esc(f["descripcion_tecnica"])}</p>{recommendation}</article>')
    high = counts["Crítica"] + counts["Alta"]
    summary = (f"Se identificaron {len(findings)} hallazgos, de los cuales {high} son de severidad crítica o alta. "
               "Priorice su validación y corrección según el contexto del activo afectado. "
               "Este documento describe los datos aportados por el auditor; no verifica los hallazgos de forma autónoma.")
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Informe · {esc(m['cliente'])} · GimliForge</title>
<style> :root{{--ink:#eaf1ef;--muted:#9faeae;--line:#355052;--bg:#0b1719;--panel:#142427;--accent:#c9a768}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui, sans-serif}}main{{max-width:1040px;margin:auto;padding:48px 28px}}.top{{display:flex;justify-content:space-between;gap:20px;color:var(--accent);letter-spacing:.13em;text-transform:uppercase;font-size:12px}}h1{{font:clamp(40px,7vw,74px)/1.05 Georgia,serif;margin:70px 0 18px}}h2{{font:32px Georgia,serif;margin:0 0 20px}}h3{{margin:8px 0}}.lead{{font-size:20px;color:var(--muted);max-width:700px}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:50px 0 80px}}.meta div,.panel,.finding{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px}}small,.eyebrow{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.12em}}section{{margin:65px 0}}.grid{{display:grid;grid-template-columns:1.3fr 1fr;gap:20px}}.bar-row{{display:grid;grid-template-columns:92px 1fr 26px;align-items:center;gap:12px;margin:16px 0}}.track{{height:10px;border-radius:10px;background:#263b3d;overflow:hidden}}.track i{{display:block;height:100%}}ul{{padding-left:20px}}li{{padding:6px 0}}li strong{{float:right}}.finding{{margin:14px 0;break-inside:avoid}}.finding-head{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:13px;color:var(--muted)}}.severity{{font-weight:700}}.recommend{{border-top:1px solid var(--line);padding-top:12px}}.footer{{color:var(--muted);font-size:13px;margin-top:80px}}@media(max-width:650px){{.meta,.grid{{display:block}}.meta div,.grid .panel{{margin:12px 0}}}}@media print{{:root{{--ink:#182b2d;--muted:#52676a;--line:#d9e1e0;--bg:white;--panel:#f5f8f7}}main{{padding:0}}h1{{margin-top:100px}}.meta{{margin-bottom:120px}}section{{break-inside:avoid}}a{{color:inherit}}}}</style></head><body><main><div class="top"><span>[ GIMLIFORGE ] / Informe de auditoría</span><span>v2.0</span></div><h1>Seguridad,<br>con claridad.</h1><p class="lead">Informe de auditoría para {esc(m['cliente'])}</p><div class="meta"><div><small>Cliente</small>{esc(m['cliente'])}</div><div><small>Auditor</small>{esc(m['auditor'])}</div><div><small>Fecha</small>{esc(m['fecha_auditoria'])}</div></div><section><span class="eyebrow">01 / Resumen ejecutivo</span><h2>Panorama de riesgo</h2><p>{esc(summary)}</p></section><section><span class="eyebrow">02 / Distribución</span><h2>Los datos de un vistazo</h2><div class="grid"><div class="panel"><h3>Severidad</h3>{bars}</div><div class="panel"><h3>Categorías</h3><ul>{cat_rows}</ul></div></div></section><section><span class="eyebrow">03 / Evidencia aportada</span><h2>Hallazgos</h2>{''.join(cards) or '<p>No se registraron hallazgos.</p>'}</section><section><span class="eyebrow">04 / Hoja de ruta</span><h2>Próximos pasos</h2><p>Confirme alcance y reproducibilidad; atienda primero los hallazgos críticos y altos; registre responsables, plazos y pruebas de remediación. Revise el resto en función de la exposición real y vuelva a validar tras aplicar cambios.</p></section><p class="footer">Confidencial · Documento generado a partir de datos facilitados por el auditor. Revise el contenido antes de compartirlo.</p></main></body></html>'''


def latex_escape(value):
    """Escape untrusted plain text before inserting it into LaTeX."""
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in str(value))


def render_latex(data):
    """Render the full report; retained as the stable public API."""
    from .report import render_report
    return render_report(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description="GimliForge 2.0 · informes de auditoría offline")
    parser.add_argument("-f", "--file", required=True, help="JSON de entrada G.I.M.L.I.")
    parser.add_argument("-o", "--output", help="Ruta del informe .tex (por defecto) o .html")
    parser.add_argument("--check", action="store_true", help="Solo validar el JSON")
    parser.add_argument("--pdf", action="store_true", help="Compilar PDF con pdflatex instalado")
    args = parser.parse_args(argv)
    try:
        data = load(args.file)
        if args.check:
            print(f"JSON válido: {len(data['hallazgos'])} hallazgos")
            return 0
        output = Path(args.output) if args.output else Path("informe_gimliforge.tex")
        if output.suffix.lower() not in (".tex", ".html"):
            raise InputError("La salida debe terminar en .tex o .html")
        if args.pdf and output.suffix.lower() != ".tex":
            raise InputError("--pdf requiere una salida .tex")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_latex(data) if output.suffix.lower() == ".tex" else render(data), encoding="utf-8")
        if output.suffix.lower() == ".tex":
            from .evidence import write_images
            write_images(output.parent, data["hallazgos"])
        print(f"Informe generado: {output.resolve()}")
        if args.pdf:
            compiler = shutil.which("pdflatex")
            if not compiler:
                raise InputError("pdflatex no está instalado; el archivo .tex ya se ha generado")
            for _ in range(2):
                installer = ["-enable-installer"] if "miktex" in compiler.lower() else []
                result = subprocess.run([compiler, *installer, "-interaction=nonstopmode", "-halt-on-error", "-output-directory", ".", output.name],
                                        cwd=str(output.parent.resolve()), capture_output=True, text=True, timeout=180)
                if result.returncode:
                    raise InputError("La compilación LaTeX falló; revise el archivo .log")
            print(f"PDF generado: {output.with_suffix('.pdf').resolve()}")
        return 0
    except (InputError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

