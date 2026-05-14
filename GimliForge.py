import urllib.request
import json
import os
import matplotlib.pyplot as plt
from google import genai

print("🛡️ Iniciando GimliForge v1.0...")

# 1. Autenticación Segura mediante Variables de Entorno
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("❌ Error Crítico: Variable de entorno GOOGLE_API_KEY no encontrada.")
    print("Por favor, ejecuta: export GOOGLE_API_KEY='tu_clave_aqui'")
    exit(1)

client = genai.Client(api_key=api_key)

# 2. Extracción de La Mina (Datos JSON)
url_mina = "https://raw.githubusercontent.com/GalicianHat/GimliForge/main/datos_entrada/escaner_resultados.json"
print("⛏️ Extrayendo datos de la mina (GitHub)...")
try:
    respuesta = urllib.request.urlopen(url_mina)
    datos_auditoria = json.loads(respuesta.read())
except Exception as e:
    print(f"❌ Error al descargar el JSON: {e}")
    exit(1)

# 3. Generación del Gráfico Ejecutivo
print("📊 Forjando gráfico de severidad...")
conteo_severidad = {"Crítica": 0, "Alta": 0, "Media": 0, "Baja": 0, "Informativa": 0}
for hallazgo in datos_auditoria['hallazgos']:
    sev = hallazgo['severidad']
    if sev in conteo_severidad:
        conteo_severidad[sev] += 1

etiquetas = [k for k, v in conteo_severidad.items() if v > 0]
valores = [v for v in conteo_severidad.values() if v > 0]
colores_riesgo = {'Crítica': '#8B0000', 'Alta': '#FF4500', 'Media': '#FFD700', 'Baja': '#32CD32', 'Informativa': '#87CEEB'}
colores_usados = [colores_riesgo[etiqueta] for etiqueta in etiquetas]

plt.figure(figsize=(8, 6))
plt.pie(valores, labels=etiquetas, autopct='%1.1f%%', startangle=140, colors=colores_usados, shadow=True)
plt.title('Distribución de Vulnerabilidades')
plt.savefig("grafico_severidad.png", bbox_inches='tight', dpi=300)
plt.close()

# 4. Invocación de la IA (El Enano)
print("🧠 Redactando informe técnico con IA...")
datos_texto = json.dumps(datos_auditoria, indent=2, ensure_ascii=False)
prompt = f"""
Actúa como experto auditor de Red Team. Toma estos datos y redacta en código LaTeX.
DATOS: {datos_texto}
REQUISITOS: No uses \\documentclass. Divide en tres partes separadas EXACTAMENTE por ---SECCION---
Parte 1: \\section{{Resumen Ejecutivo}} (Un párrafo).
---SECCION---
Parte 2: \\section{{Análisis de Hallazgos}} (Detalle técnico).
---SECCION---
Parte 3: \\section{{Recomendaciones}} (Lista).
"""

try:
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    partes = response.text.split('---SECCION---')
    if len(partes) != 3:
        raise ValueError("La IA no respetó el formato de 3 secciones.")
except Exception as e:
    print(f"❌ Error en la IA: {e}")
    exit(1)

# 5. Ensamblaje en la Plantilla LaTeX
print("🔨 Ensamblando el reporte final...")
plantilla_latex = r"""
\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{graphicx}

\geometry{a4paper, margin=2.5cm}

\title{\textbf{Informe Ejecutivo de Pentesting}}
\author{Adrián Suárez}
\date{\today}

\begin{document}
\maketitle
\newpage
\tableofcontents
\newpage

\section{Resumen Ejecutivo}
{{RESUMEN}}

\vspace{1cm}
\begin{figure}[h]
    \centering
    \includegraphics[width=0.6\textwidth]{grafico_severidad.png}
\end{figure}
\vspace{1cm}

{{HALLAZGOS}}

{{RECOMENDACIONES}}

\end{document}
"""

doc_final = plantilla_latex.replace("{{RESUMEN}}", partes[0].strip())
doc_final = doc_final.replace("{{HALLAZGOS}}", partes[1].strip())
doc_final = doc_final.replace("{{RECOMENDACIONES}}", partes[2].strip())

with open("informe_final.tex", "w", encoding="utf-8") as f:
    f.write(doc_final)

print("✅ ¡Proceso completado! Archivos 'informe_final.tex' y 'grafico_severidad.png' listos.")