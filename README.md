# [ GIMLIFORGE ] 2.0

GimliForge convierte hallazgos de auditoría en un informe **LaTeX** revisable. La versión 2.0 se utiliza desde el navegador, pero se ejecuta en el propio equipo. Permite crear proyectos, importar JSON, editar hallazgos, guardar borradores y descargar el `.tex`. También genera PDF cuando `pdflatex` está instalado. El informe incluye resumen, alcance, metodología, cinco gráficos calculados, inventario, trazabilidad, fichas técnicas, hoja de ruta y plan de validación. La aplicación comparte imagen, colores, tipografía y efectos de forja con la página del proyecto; los recursos se sirven localmente para que funcione sin conexión.

## Instalar y abrir

Necesita **Python 3.10 o posterior** y un navegador actual. La aplicación no necesita `pip`, una cuenta ni una clave API.

1. Para probar esta versión antes de publicarla, descomprima el paquete descargado. La versión pública de GitHub todavía es la v1.
2. Abra una terminal dentro de la carpeta `GimliForge`.
3. Ejecute el comando correspondiente:

| Sistema | Comando |
| --- | --- |
| Windows | `py GimliForge.py` (o `python GimliForge.py`) |
| macOS | `python3 GimliForge.py` |
| Linux | `python3 GimliForge.py` |

Se abrirá `http://127.0.0.1:8765` en el navegador. Si no se abre solo, copie esa dirección. Para cerrar la aplicación, vuelva a la terminal y pulse **Ctrl+C**. Si el puerto está ocupado, ejecute `python GimliForge.py --port 8766` (use `py` o `python3` según el sistema).

## Primer informe en cinco pasos

1. Pulse **Nueva auditoría** o **Importar JSON**. Puede empezar con `datos_entrada/demo_con_evidencia.json` (ejemplo ficticio con imagen), `datos_entrada/demo_extensa.json`, `datos_entrada/demo.json`, `informepruebamovil.json` o `informepruebacloud.json`.
2. Complete cliente, auditor y fecha.
3. Añada y revise los hallazgos. El título, severidad y descripción son obligatorios; CVSS es opcional. Para un informe completo, rellene alcance, metodología, activo, evidencia, impacto, validación y recomendación. En **Imágenes de evidencia** puede añadir hasta cinco capturas PNG o JPEG de 3 MB por hallazgo y escribir un pie para cada una.
4. Pulse **Guardar auditoría**. Los proyectos quedan en la carpeta local `projects/`, excluida de Git.
5. Pulse **Descargar LaTeX**. Sin imágenes recibirá un `.tex`; con imágenes recibirá un ZIP que contiene el `.tex` y la carpeta `evidencias/`. Conserve juntos los archivos al editar o compilar. **Descargar PDF** incorpora las imágenes directamente en el documento.

Para **Descargar PDF**, instale TeX Live (macOS/Linux) o MiKTeX/TeX Live (Windows), asegurándose de que `pdflatex` y los paquetes `babel-spanish`, `tikz`, `tabularx`, `longtable` y `fancyhdr` estén disponibles. La aplicación mostrará un aviso si no encuentra `pdflatex`; podrá seguir descargando el `.tex`. El ejemplo ficticio `demo_extensa.json` genera 13 páginas en la comprobación local; la longitud real depende de los hallazgos y la evidencia que se aporten.

### Modo asistido con Gemini (opcional)

La versión básica genera informes, gráficos e imágenes sin cuenta ni clave. Para activar la redacción asistida sin editar archivos:

1. Obtenga una clave de la API en [Google AI Studio](https://aistudio.google.com/api-keys) con su propia cuenta. Revise las [cuotas y tarifas de Google](https://ai.google.dev/gemini-api/docs/pricing) antes de usarla; GimliForge no cobra una suscripción.
2. En GimliForge, pulse **Clave de Gemini**, pegue la clave y pulse **Guardar clave**. La aplicación mostrará si ha quedado configurada; nunca vuelve a mostrar la clave.
3. Abra una auditoría y pulse **Proponer texto con Gemini**.
4. Revise los textos propuestos en los campos editables y pulse **Guardar auditoría** solo si está conforme.

La clave se guarda en `projects/.gemini-key` en el equipo, fuera del ZIP y del repositorio. Si copia la carpeta `projects/` a otro lugar, recuerde que contiene también la clave. Como alternativa avanzada, se admiten `.env` y las variables `GEMINI_API_KEY` o `GOOGLE_API_KEY`; la clave guardada desde el botón tiene prioridad. Solo al pulsar **Proponer texto** se envían los campos de texto de la auditoría a Google: **las imágenes no se envían**. No use esta función con datos de clientes sin autorización para enviarlos al proveedor. Sin clave o sin conexión, las demás funciones siguen disponibles.

Los proyectos se guardan únicamente en el ordenador donde se ejecuta la aplicación. No hay sincronización ni recuperación automática fuera de la carpeta `projects/`: haga una copia de esa carpeta si la necesita.

## Formato de entrada

JSON UTF-8 de hasta 20 MB con `metadata` (`cliente`, `auditor`, `fecha_auditoria` en formato AAAA-MM-DD) y una lista `hallazgos`. Metadatos opcionales: `alcance`, `metodologia`, `resumen_ejecutivo`, `impacto_negocio`, `conclusiones`. Cada hallazgo lleva `id`, `titulo` (o `tipo` del formato antiguo), `severidad`, `descripcion_tecnica`; opcionalmente `categoria`, `cvss` (0–10), `activo`, `evidencia`, `impacto`, `reproduccion`, `recomendacion`, `referencias` e `imagenes`. Cada entrada de `imagenes` contiene `nombre`, `mime`, `leyenda` y `data` en Base64. Severidades válidas: Crítica, Alta, Media, Baja, Informativa. Consulte `datos_entrada/demo_con_evidencia.json`.

El importador web reconoce también el ejemplo antiguo `datos_entrada/escaner_resultados.json`, cuyos metadatos están en la raíz. Revise todos los datos importados antes de guardarlos. Los ejemplos son ficticios y se usan solo para pruebas.

## Uso desde terminal

El modo de línea de comandos sigue disponible:

```bash
python GimliForge.py --file datos_entrada/demo.json --check
python GimliForge.py --file datos_entrada/demo.json --output informe.tex
python GimliForge.py --file datos_entrada/demo.json --output informe.tex --pdf
```

La salida `.html` es opcional: `--output informe.html`. Si el JSON incluye imágenes y genera `.tex` desde la terminal, conserve la carpeta `evidencias/` que se crea junto al archivo. En Windows puede sustituir `python` por `py`; en macOS/Linux, por `python3`.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

## Seguridad y límites

El servidor escucha solo en `127.0.0.1`; no expone la aplicación a la red. Se comprueba el origen de las peticiones, el tamaño y formato del JSON, los campos obligatorios, el rango CVSS, los IDs duplicados y el tipo y tamaño de las imágenes. Los datos de entrada se escapan antes de incluirlos en LaTeX y HTML. Los proyectos pueden contener información sensible, incluidas imágenes codificadas en el JSON y una clave de Gemini: proteja su equipo y no publique `projects/` ni los informes generados. La aplicación no escanea sistemas ni comprueba que un hallazgo sea verdadero. Gemini propone texto, pero no controla la plantilla ni los gráficos. La extensión del informe depende de la evidencia aportada; los campos vacíos se señalan, no se rellenan con datos inventados.

## Estructura

- `GimliForge.py`: arranque web y modo CLI.
- `src/gimliforge.py`: validación y generación LaTeX/HTML.
- `src/report.py`: informe detallado y gráficos LaTeX.
- `src/evidence.py`: validación y exportación de imágenes de evidencia.
- `src/ai.py`: redacción asistida opcional con Gemini.
- `src/webapp.py`: servidor local y almacenamiento de proyectos.
- `web/`: interfaz del navegador.
- `web/fonts/`: tipografías Cinzel e Inter con sus licencias OFL.
- `datos_entrada/`: ejemplo de importación.
- `tests/`: pruebas del motor y del servidor.

Autor: Adrián Suárez Recarey. Licencia: MIT.

La versión 1.0 original permanece en el commit `5ef2e37feada5b71ce635aa694a9148d89f227bc` y en el archivo separado `GimliForge-1.0-codigo.zip`. La página 1.0 se conserva como `gimli-v1.html` en el repositorio web. La marca `[ GIMLIFORGE ]` procede de aquella versión.
