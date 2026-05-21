# GimliForge - Generador de Informes Mediante Lenguaje Inteligente
Generador de informes de pentesting. 


Proyecto desarrollado para Máster en Ciberseguridad & IA de Evolve Academy.


Autor: Adrián Suárez Recarey.


# **Instalación y Requisitos**
# 1- Librería matplot y generación del entorno de python

python3 -m venv venv


source venv/bin/activate


pip3 install google-genai matplotlib


sudo apt install python3-matplotlib (Por si no funciona con el instalador de pip3)

# 2- Generar API Key y exportarla en el S.O utilizado
Pasos:
0. Tendrás que tener una API Key gratuita de Google para poder generar informes, sin ella la herramienta no funcionará.

**Por seguridad, nunca se debe escribir la clave directamente en el código.**

GimliForge está diseñado para leerla de forma segura desde las variables de entorno del Sistema Operativo de la persona usuaria.
1. Visitar [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Iniciar sesión con una cuenta de Google.
3. Hacer clic en el botón azul **"Create API key"** (Crear clave de API).
4. Copiar la clave generada (comenzará por `AIza...`).



**En Linux / macOS:**
`bash
export GOOGLE_API_KEY="pega_tu_clave_aqui"
`

**En Windows (PowerShell):**
`powershell
$env:GOOGLE_API_KEY="pega_tu_clave_aqui"
`

# 3- Ejecutar la herramienta
python3 GimliForge.py

**GimliForge utiliza un estándar JSON propio (GIMLI Data Standard) para garantizar la uniformidad de los informes, independientemente de la herramienta de escaneo utilizada por el auditor. Para integrar herramientas como Nessus, Burp Suite o ZAP, el flujo de trabajo requiere pasar el output nativo de estas herramientas por un script de parseo (Parser) que normalice los datos hacia el estándar GIMLI antes de su ingesta.
