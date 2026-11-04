# Instalación y portabilidad: registro de comprobación

La distribución 2.0 es un ZIP con código Python y recursos web locales. La aplicación básica utiliza únicamente la biblioteca estándar de Python 3.10+; la compilación a PDF requiere una distribución LaTeX con `pdflatex`. Se ejecuta como servidor local en `127.0.0.1`.

| Sistema | Comando dentro de `GimliForge/` | Comprobación efectuada | Estado |
| --- | --- | --- | --- |
| Windows | `py GimliForge.py` | ZIP extraído en carpeta nueva; validación de ejemplo y 15 pruebas correctas con Python 3.13; uso en navegador y exportación PDF. | Verificado en este equipo. |
| macOS | `python3 GimliForge.py` | Revisión del código y ausencia de dependencias externas en la función básica. | Pendiente de ejecutar en macOS real. |
| Linux | `python3 GimliForge.py` | Revisión del código; no hay distribución WSL instalada en este equipo. | Pendiente de ejecutar en Linux real. |

El ZIP actual contiene 31 archivos, pasó la comprobación de integridad y no incluyó `projects/`, `.env` ni `.gemini-key`. Su suma SHA-256 se registra fuera del propio ZIP, para que la documentación interna no invalide el hash al regenerarlo.

La portabilidad de diseño no sustituye la ejecución en los otros dos sistemas. Antes de presentar «multiplataforma» como verificado, registrar allí versión de Python, navegador, presencia de `pdflatex`, creación de proyecto, importación, exportación y cierre limpio.
