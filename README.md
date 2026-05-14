# GimliForge
# 🪓 Proyecto GimliForge: Red Team AI Reporter

**GimliForge** (Generador de Informes Mediante Lenguaje Inteligente) es una herramienta automatizada diseñada para agilizar el flujo de trabajo de los equipos de Red Team. Transforma los datos en bruto de escáneres de vulnerabilidades en informes ejecutivos listos para el cliente utilizando Inteligencia Artificial y LaTeX.

## 🚀 Arquitectura en 3 Fases

El proyecto está estructurado para garantizar robustez, formato inmutable y cero exposición de credenciales:

1. **La Mina (Ingesta):** Lectura e ingesta de datos estructurados estandarizados (`.json`) simulando el output de herramientas como Nessus, Burp Suite o Nmap.
2. **El Enano (Procesamiento LLM):** Integración con la API de Google Gemini (`gemini-2.5-flash`) mediante Variables de Entorno. A través de *Prompt Engineering* estricto, la IA analiza las vulnerabilidades, calcula los riesgos, genera gráficos de severidad dinámicos con Python y redacta las secciones técnicas en código LaTeX nativo.
3. **La Forja (Ensamblaje):** Inyección de las respuestas del LLM y de los gráficos en una "Plantilla Maestra" inmutable de LaTeX, garantizando una compilación perfecta y un formato corporativo (PDF) libre de alucinaciones visuales de la IA.

## 🛠️ Instalación y Uso

**1. Requisitos:**
```bash
pip3 install google-genai matplotlib
