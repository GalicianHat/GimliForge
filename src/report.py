"""Auditor-controlled LaTeX report with charts computed from validated data."""
from __future__ import annotations

from collections import Counter

SEVERITIES = ("Crítica", "Alta", "Media", "Baja", "Informativa")
COLORS = ("C63542", "D77637", "D5A934", "568C69", "587C9A")


def escape(value):
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
               "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
               "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(mapping.get(char, char) for char in str(value))


def paragraph(value, fallback="No se aportó información para este apartado."):
    return escape(value.strip()) if value and value.strip() else r"\textit{" + fallback + "}"


def chart(title, labels, values, colors, width=11):
    """Create a horizontal TikZ chart from actual finding counts."""
    if not labels:
        return r"\textit{No hay datos para representar.}" + "\n"
    scale = width / max(1, max(values))
    height = len(labels) * 0.67 + 0.35
    lines = [r"\begin{center}", r"\begin{tikzpicture}[x=1cm,y=1cm]",
             rf"\node[anchor=west,font=\bfseries] at (0,{height:.2f}) {{{escape(title)}}};"]
    for index, (label, value, color) in enumerate(zip(labels, values, colors)):
        y = (len(labels) - index - 1) * .67
        lines.extend((rf"\node[anchor=east,font=\small] at (0,{y + .18:.2f}) {{{escape(label)}}};",
                      rf"\fill[black!8] (0,{y:.2f}) rectangle ({width},{y + .36:.2f});",
                      rf"\fill[chart{color}] (0,{y:.2f}) rectangle ({value * scale:.2f},{y + .36:.2f});",
                      rf"\node[anchor=west,font=\small] at ({width + .12},{y + .18:.2f}) {{{value}}};"))
    lines.extend((r"\end{tikzpicture}", r"\end{center}"))
    return "\n".join(lines) + "\n"


def finding_section(finding, index):
    from .evidence import image_name
    cvss = f"{finding['cvss']:.1f}" if finding["cvss"] is not None else "No informado"
    rows = [r"\subsection{" + escape(finding["id"] + " · " + finding["titulo"]) + "}",
            r"\begin{tabularx}{\textwidth}{@{}lXlX@{}}",
            r"\textbf{Severidad} & " + escape(finding["severidad"]) + r" & \textbf{CVSS} & " + cvss + r"\\",
            r"\textbf{Categoría} & " + escape(finding["categoria"]) + r" & \textbf{Activo} & " + paragraph(finding.get("activo"), "No indicado") + r"\\",
            r"\end{tabularx}",
            r"\subsubsection*{Descripción técnica aportada}", paragraph(finding["descripcion_tecnica"]),
            r"\vspace{0.7cm}\noindent\textcolor{CorpBlue}{\rule{\textwidth}{0.5pt}}"]
    for field, title in (("evidencia", "Evidencia registrada"), ("impacto", "Impacto y exposición"),
                         ("reproduccion", "Reproducción o validación"), ("recomendacion", "Recomendación"),
                         ("referencias", "Referencias")):
        if finding.get(field):
            rows[-1:-1] = [r"\subsubsection*{" + title + "}", paragraph(finding[field])]
        if field == "evidencia" and finding.get("imagenes"):
            rows[-1:-1] = [r"\subsubsection*{Evidencia visual aportada}"]
            for image_index, image in enumerate(finding["imagenes"], 1):
                filename = image_name(finding["id"], image_index, image["mime"])
                label = image["leyenda"] or image["nombre"] or f"Imagen {image_index}"
                rows[-1:-1] = [r"\begin{center}",
                               r"\includegraphics[width=0.9\textwidth,height=7cm,keepaspectratio]{evidencias/" + filename + "}",
                               r"\par\smallskip{\small " + escape(label) + "}", r"\end{center}"]
    missing = [title for field, title in (("evidencia", "evidencia"), ("impacto", "impacto"),
                                          ("recomendacion", "recomendación")) if not finding.get(field)]
    if missing:
        rows[-1:-1] = [r"\textit{Pendiente de completar: " + escape(", ".join(missing)) + ".}"]
    rows[-1:-1] = [
        r"\subsubsection*{Tratamiento y comprobación de cierre}",
        r"\begin{tabularx}{\textwidth}{@{}p{4.4cm}X@{}}",
        r"\textbf{Medida propuesta} & " + paragraph(finding.get("recomendacion"), "Definir la corrección con el responsable del activo") + r"\\",
        r"\textbf{Responsable y plazo} & Pendientes de asignación y aprobación por el propietario del activo.\\",
        r"\textbf{Comprobación} & " + paragraph(finding.get("reproduccion"), "Definir una prueba autorizada que confirme la corrección") + r"\\",
        r"\textbf{Evidencia de cierre} & Registrar versión o configuración corregida, resultado de la nueva prueba y fecha de revisión.\\",
        r"\end{tabularx}",
    ]
    return "\n\n".join(rows) + "\n"


def render_report(data):
    m, findings = data["metadata"], data["hallazgos"]
    counts = Counter(f["severidad"] for f in findings)
    categories = Counter(f["categoria"] for f in findings)
    scores = Counter("0–3,9" if f["cvss"] < 4 else "4–6,9" if f["cvss"] < 7 else "7–8,9" if f["cvss"] < 9 else "9–10"
                     for f in findings if f["cvss"] is not None)
    high = counts["Crítica"] + counts["Alta"]
    default_summary = (f"Se registraron {len(findings)} hallazgos en el alcance facilitado, "
                       f"de los cuales {high} tienen severidad crítica o alta. "
                       "La prioridad de tratamiento debe confirmarse con la exposición real de cada activo. "
                       "Este informe organiza la información aportada; no verifica automáticamente su exactitud.")
    severity_chart = chart("Hallazgos por severidad", SEVERITIES, [counts[s] for s in SEVERITIES], range(5))
    cat_labels = [name[:28] + "…" if len(name) > 29 else name for name, _ in categories.most_common(8)]
    cat_chart = chart("Principales categorías", cat_labels, [value for _, value in categories.most_common(8)], [5] * len(cat_labels))
    score_labels = ("0–3,9", "4–6,9", "7–8,9", "9–10")
    score_chart = chart("CVSS informado", score_labels, [scores[s] for s in score_labels], (3, 2, 1, 0))
    assets = Counter(f["activo"] or "Activo no indicado" for f in findings)
    asset_labels = [name[:22] + "…" if len(name) > 23 else name for name, _ in assets.most_common(8)]
    asset_chart = chart("Hallazgos por activo declarado", asset_labels,
                        [value for _, value in assets.most_common(8)], [5] * len(asset_labels), width=9)
    coverage_fields = (("Activo", "activo"), ("Evidencia", "evidencia"),
                       ("Impacto", "impacto"), ("Validación", "reproduccion"),
                       ("Recomendación", "recomendacion"), ("Referencias", "referencias"))
    coverage_chart = chart("Campos documentados por hallazgo", [label for label, _ in coverage_fields],
                           [sum(bool(f[field]) for f in findings) for _, field in coverage_fields],
                           [3] * len(coverage_fields))
    risk_rows = "\n".join(
        escape(f["id"]) + " & " + escape(f["titulo"]) + " & " + escape(f["severidad"]) + " & "
        + (f"{f['cvss']:.1f}" if f["cvss"] is not None else "--") + r"\\\hline"
        for f in findings
    ) or r"-- & Sin hallazgos & -- & --\\\hline"
    ordered = sorted(findings, key=lambda f: (SEVERITIES.index(f["severidad"]), -(f["cvss"] or 0)))
    roadmap = []
    for f in ordered:
        phase = "Inmediata" if f["severidad"] in ("Crítica", "Alta") else "Planificada"
        roadmap.append(r"\item \textbf{" + phase + " · " + escape(f["id"]) + "}: "
                       + paragraph(f.get("recomendacion"), "Definir medida con el responsable del activo"))
    roadmap_text = "\n".join(roadmap) if roadmap else r"\item No hay acciones asociadas a hallazgos registrados."
    findings_text = "\n".join(finding_section(f, i) for i, f in enumerate(ordered)) or "No se registraron hallazgos."
    priority_list = "\n".join(r"\item " + escape(f["id"] + " · " + f["titulo"])
                              for f in ordered if f["severidad"] in ("Crítica", "Alta"))
    if not priority_list:
        priority_list = r"\item No hay hallazgos críticos o altos en los datos facilitados."
    trace_rows = "\n".join(
        escape(f["id"]) + " & " + str(sum(bool(f[field]) for _, field in coverage_fields))
        + "/6 & " + ("Sí" if f["cvss"] is not None else "No") + " & "
        + escape(", ".join(label for label, field in coverage_fields if not f[field]) or "Ninguno")
        + r"\\\hline" for f in findings
    ) or r"-- & -- & -- & Sin hallazgos\\\hline"
    preamble = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}
\usepackage[a4paper,margin=2.5cm]{geometry}
\usepackage[table]{xcolor}
\usepackage{tikz}
\usepackage{graphicx}
\usepackage{tabularx}
\usepackage{longtable}
\usepackage{fancyhdr}
\definecolor{CorpBlue}{HTML}{1A365D}
\definecolor{chart0}{HTML}{C63542}
\definecolor{chart1}{HTML}{D77637}
\definecolor{chart2}{HTML}{D5A934}
\definecolor{chart3}{HTML}{568C69}
\definecolor{chart4}{HTML}{587C9A}
\definecolor{chart5}{HTML}{31566B}
\pagestyle{fancy}\fancyhf{}\fancyhead[L]{\texttt{[ GIMLIFORGE ]} · Informe de auditoría}\fancyhead[R]{Confidencial}\fancyfoot[C]{\thepage}
\setlength{\headheight}{15pt}
\setlength{\parskip}{0.6em}\setlength{\parindent}{0pt}
\begin{document}
\begin{titlepage}\centering\vspace*{2.8cm}
{\LARGE\bfseries\ttfamily [ GIMLIFORGE ]\par}
\vspace{0.9cm}
{\Huge\bfseries\color{CorpBlue} Informe de Auditoría de Seguridad\par}
\vspace{1cm}{\Large Versión 2.0\par}\vspace{1.5cm}
"""
    cover = (r"{\Large\textbf{Cliente:} " + escape(m["cliente"]) + r"\par}" + "\n"
             + r"{\large\textbf{Auditor:} " + escape(m["auditor"]) + r"\par}" + "\n"
             + r"{\large\textbf{Fecha:} " + escape(m["fecha_auditoria"]) + r"\par}" + "\n"
             + r"\vfill\textbf{Confidencial} · Revisar antes de compartir\end{titlepage}" + "\n"
             + r"\tableofcontents\newpage" + "\n")
    overview = (r"\section{Resumen ejecutivo}" + "\n" + paragraph(m.get("resumen_ejecutivo"), escape(default_summary)) + "\n"
                + r"\subsection{Prioridades para la revisión}" + "\n"
                + "Estos hallazgos se han señalado como críticos o altos en los datos de entrada. Su orden definitivo requiere confirmar exposición, activo y contexto:\n"
                + r"\begin{itemize}" + "\n" + priority_list + "\n" + r"\end{itemize}" + "\n")
    for field, title in (("impacto_negocio", "Impacto para el negocio"), ("conclusiones", "Conclusión preliminar")):
        if m.get(field):
            overview += r"\subsection{" + title + "}\n" + paragraph(m[field]) + "\n"
    overview += r"\section{Alcance y método}" + "\n"
    for field, title in (("alcance", "Alcance declarado"), ("metodologia", "Método empleado")):
        if m.get(field):
            overview += r"\subsection{" + title + "}\n" + paragraph(m[field]) + "\n"
    if not m.get("alcance") or not m.get("metodologia"):
        overview += r"\textit{Alcance o método pendiente de documentar por el equipo auditor.}" + "\n"
    overview += (r"\textbf{Límite de interpretación:} Los datos son aportados por el auditor. "
                 r"No se han ejecutado pruebas de seguridad durante la generación del informe." + "\n")
    dashboard = (r"\newpage\section{Cuadro de riesgo}" + "\n"
                 + f"Total de hallazgos: {len(findings)}. Críticos o altos: {high}. "
                   f"Con CVSS informado: {sum(f['cvss'] is not None for f in findings)}." + "\n"
                 + severity_chart + "\n" + cat_chart + "\n" + score_chart + "\n"
                 + r"\clearpage\subsection{Distribución por activos}" + "\n" + asset_chart + "\n"
                 + r"\subsection{Inventario de hallazgos}" + "\n"
                 + r"\begin{longtable}{|p{1.8cm}|p{8cm}|p{2cm}|p{1.3cm}|}\hline"
                   r"\textbf{ID}&\textbf{Hallazgo}&\textbf{Severidad}&\textbf{CVSS}\\\hline\endfirsthead"
                   r"\hline\textbf{ID}&\textbf{Hallazgo}&\textbf{Severidad}&\textbf{CVSS}\\\hline\endhead" + "\n"
                 + risk_rows + "\n" + r"\end{longtable}" + "\n"
                 + r"\clearpage\section{Trazabilidad y calidad de la información}" + "\n"
                 + "La cobertura siguiente indica cuántos hallazgos incluyen cada campo. No mide la veracidad ni la suficiencia de la evidencia; sirve para identificar qué debe completar el auditor antes de entregar el informe.\n"
                 + coverage_chart + "\n"
                 + r"\subsection{Campos pendientes por hallazgo}" + "\n"
                 + r"\begin{longtable}{|p{2cm}|p{2.2cm}|p{1.5cm}|p{8cm}|}\hline"
                   r"\textbf{ID}&\textbf{Campos}&\textbf{CVSS}&\textbf{Pendiente de documentar}\\\hline\endfirsthead"
                   r"\hline\textbf{ID}&\textbf{Campos}&\textbf{CVSS}&\textbf{Pendiente de documentar}\\\hline\endhead" + "\n"
                 + trace_rows + "\n" + r"\end{longtable}" + "\n")
    finish = (r"\newpage\section{Hoja de ruta de mitigación}" + "\n"
              + "Las acciones siguientes se ordenan por la severidad informada. El responsable del activo debe confirmar plazos y prioridad según contexto y exposición.\n"
              + r"\begin{enumerate}" + "\n" + roadmap_text + "\n" + r"\end{enumerate}" + "\n"
              + r"\clearpage\section{Plan de validación posterior}" + "\n"
              + "Para cada hallazgo: registrar el cambio realizado, repetir la prueba autorizada, conservar la evidencia de cierre y documentar las excepciones. Si una prueba falla, reabrir el hallazgo.\n"
              + r"\subsection{Registro de seguimiento}" + "\n"
              + "Antes de dar un hallazgo por cerrado, el equipo debe completar para cada ID el responsable, la fecha de implantación, la versión o configuración afectada y el resultado de la nueva prueba. Estos datos no se infieren del hallazgo original.\n"
              + r"\begin{longtable}{|p{2.4cm}|p{2.9cm}|p{3.9cm}|p{2.4cm}|}\hline"
                r"\textbf{ID}&\textbf{Responsable}&\textbf{Fecha de revisión}&\textbf{Resultado}\\\hline\endfirsthead"
                r"\hline\textbf{ID}&\textbf{Responsable}&\textbf{Fecha de revisión}&\textbf{Resultado}\\\hline\endhead" + "\n"
              + ("\n".join(escape(f["id"]) + r" & Pendiente & Pendiente & Pendiente\\\hline" for f in ordered)
                 or r"-- & -- & -- & --\\\hline") + "\n" + r"\end{longtable}" + "\n"
              + r"\section{Limitaciones del informe}" + "\n"
              + "GimliForge no confirma la existencia de vulnerabilidades, no calcula CVSS automáticamente y no estima pérdidas económicas. Los campos no aportados se muestran como tales y requieren revisión profesional.\n"
              + r"\appendix\section{Procedencia y revisión}" + "\n"
              + "Los datos de este documento proceden del proyecto local. Antes de entregarlo, confirme el alcance, las evidencias, las puntuaciones y las recomendaciones con el equipo auditor.\n"
              + r"\subsection{Lista de revisión antes de la entrega}" + "\n"
              + r"\begin{enumerate}" + "\n"
              + r"\item Confirmar cliente, fecha, auditor y límites del alcance." + "\n"
              + r"\item Revisar que cada evidencia procede de una prueba autorizada y no revela secretos." + "\n"
              + r"\item Confirmar severidad y puntuaciones CVSS con el contexto del activo." + "\n"
              + r"\item Validar la viabilidad de cada recomendación con sus responsables." + "\n"
              + r"\item Revisar cualquier texto propuesto por Gemini antes de entregar el documento." + "\n"
              + r"\item Documentar excepciones y aprobación final." + "\n"
              + r"\end{enumerate}" + "\n"
              + r"\end{document}" + "\n")
    return preamble + cover + overview + dashboard + r"\newpage\section{Detalle técnico de hallazgos}" + "\n" + findings_text + finish
