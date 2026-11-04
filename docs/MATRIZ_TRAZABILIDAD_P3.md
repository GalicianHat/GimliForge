# GimliForge 2.0 — matriz de trazabilidad de la práctica 3

**Estado:** matriz de trabajo contrastada con las pruebas locales P-01 a P-06 de `docs/PRUEBAS_P3.md`. Autor de la práctica 1: Adrián Suárez Recarey (trabajo individual, calificado con matrícula de honor). No se recibió una lista formal de requisitos numerados; los identificadores siguientes se derivan de la memoria final y del código de la versión 1.0. Antes de entregar, se revisarán con el producto y el vídeo definitivos.

La corrección comunicada por el autor fue favorable y señaló dos mejoras distintas: añadir fotografías o capturas como evidencia en los informes generados por GimliForge y cuidar el interlineado de la memoria académica. El segundo comentario no se refiere a la plantilla LaTeX del producto. Esta matriz documenta la versión 2.0 y sus verificaciones pendientes para la entrega.

## Requisitos derivados de la versión 1.0

| ID | Compromiso documentado en la práctica 1 | Estado actual en 2.0 | Implementación | Prueba disponible | Evidencia pendiente para la entrega |
| --- | --- | --- | --- | --- | --- |
| RF-01 | Ingesta de auditorías en JSON con `metadata` y `hallazgos`. | Implementado; se mantiene el formato antiguo. | `src/gimliforge.py`, `src/webapp.py`, `web/app.js` | `test_demo`, `test_legacy_title_and_empty`, `test_invalid_cvss_and_duplicate` | Grabar importación de un JSON válido y rechazo de uno incorrecto. |
| RF-02 | Introducción manual guiada de hallazgos. | Implementado mediante formulario web y proyectos locales. | `web/app.js`, `src/webapp.py` | P-03: formulario, guardado y reapertura en navegador; `test_create_reopen_and_export_tex`. | Capturas seleccionadas y minuto de vídeo. |
| RF-03 | Gemini 2.5 Flash redacta secciones ejecutivas a partir de los datos. | Implementado como función **opcional**; propone texto editable y el informe básico funciona sin clave. | `src/ai.py`, `src/webapp.py`, `web/app.js` | `test_ai_is_opt_in_and_requires_key`, `test_ai_draft_is_structured_and_reviewable` con respuesta simulada. | Prueba real con clave introducida por el usuario y conexión disponible; registrar límites y errores del servicio. |
| RF-04 | Dos gráficos de severidad y categorías en PNG a 300 DPI con Matplotlib. | **Modificado:** cinco gráficos vectoriales calculados en TikZ/LaTeX. La resolución DPI deja de ser pertinente para gráficos vectoriales. | `src/report.py` | P-02: PDF compilado, cinco gráficos y revisión visual; `test_full_report_keeps_evidence_and_charts`. | Mostrar los cinco gráficos y justificar el cambio de tecnología en la memoria. |
| RF-05 | Ensamblar un informe estructurado en LaTeX a partir de plantilla. | Implementado y ampliado: resumen, alcance, metodología, gráficos, inventario, detalle, mitigación y validación. | `src/report.py`, `src/gimliforge.py` | P-02: PDF de 13 páginas revisado; P-04: descarga desde navegador. | Evaluar con datos de una auditoría real autorizada y documentar límites. |
| RNF-01 | Rechazar JSON sin los nodos obligatorios. | Implementado con validación adicional de campos, CVSS, identificadores e imágenes. | `src/gimliforge.py`, `src/evidence.py` | P-06: JSON mal formado rechazado sin guardar proyecto; `test_invalid_cvss_and_duplicate`, `test_invalid_input_and_host_rejected`. | Ampliar la tabla con casos de imagen incorrecta y registrar la pantalla de error en vídeo. |
| RNF-02 | Evitar que la IA invente cifras económicas. | Control parcial: la instrucción sigue en el prompt y la respuesta se presenta para revisión humana; ninguna instrucción garantiza por sí sola la veracidad del modelo. | `src/ai.py`, `web/app.js` | `test_ai_prompt_keeps_original_constraints` | Evaluación manual de varias respuestas reales; explicar que el auditor valida el contenido. |
| RNF-03 | Mantener la estructura del informe aunque falle el texto de IA; en v1 se usaba `---SECCION---`. | **Modificado:** respuesta JSON estructurada y plantilla LaTeX controlada por la aplicación. | `src/ai.py`, `src/report.py` | `test_ai_draft_is_structured_and_reviewable`, `test_latex_escaping_and_structure` | Probar respuesta ausente o malformada y registrar el error mostrado. |
| RNF-04 | Gestionar la clave de Gemini fuera del código. | Implementado: botón local, archivo ignorado por Git y variables de entorno como alternativa. | `src/webapp.py`, `src/ai.py`, `.gitignore` | `test_image_sources_and_local_key_settings`, `test_local_key_is_read_from_ignored_env_file` | Revisar permisos del archivo y demostrar que la clave no aparece en la API ni en el repositorio. |

## Mejoras y comentarios posteriores a la práctica 1

| ID | Origen | Estado actual | Prueba disponible | Pendiente |
| --- | --- | --- | --- | --- |
| MEJ-01 | Comentario docente: añadir fotos o capturas como evidencia. | Carga de PNG/JPEG por hallazgo, leyenda, almacenamiento local e inclusión en LaTeX/PDF. | P-02: imagen incrustada en PDF; P-03: carga y persistencia con pie; pruebas automáticas de imagen. | Repetir con una captura legítima de laboratorio y mostrar el flujo en vídeo. |
| MEJ-02 | Memoria de v1: ampliar visualización. | Cinco gráficos calculados a partir de hallazgos. | `test_full_report_keeps_evidence_and_charts` | Explicar qué mide cada gráfico y qué ocurre cuando faltan datos. |
| MEJ-03 | Memoria de v1: revisar seguridad de la página. | CSP y fuentes locales preparados para `/gimli` 2.0. | Revisión local en navegador; `SEGURIDAD_GIMLI.md` en el repositorio web. | Resolver controles del portfolio completo y repetir pruebas tras publicar. |
| MEJ-04 | Objetivo de producto de la práctica 3. | Interfaz local en navegador, proyectos, PDF opcional y funcionamiento sin API. | P-03 y P-04: recorrido real en navegador; `test_create_reopen_and_export_tex`. | Instalación limpia en Windows, macOS y Linux; vídeo sin maquetas. |
| DOC-01 | Comentario docente: interlineado correcto en la memoria académica. | Pendiente de aplicar a la memoria final de la práctica 3; no implica cambiar los informes del producto. | Ninguna todavía. | Redactar la memoria con cuerpo legible e interlineado consistente; revisar todas las páginas del PDF final. La portada no llevará fecha por decisión del autor. |

## Decisión sobre el «modo de entrada forzosa»

La memoria de la práctica 1 lo situaba en el *roadmap*, no entre las funciones ya operativas: proponía aceptar únicamente JSON prevalidado y eliminar la entrada manual. La versión 2.0 conserva la entrada manual porque permite corregir y completar hallazgos antes de producir el informe, mientras que la validación estricta se aplica al guardar e importar. Esta decisión debe explicarse como cambio de dirección, sin presentar el roadmap como requisito original cumplido.

## Evidencias que faltan para cerrar la matriz

1. Numerar casos de prueba reproducibles y asociar al menos uno a cada RF/RNF.
2. Realizar instalación limpia en los tres sistemas; conservar versiones, pasos, resultados y errores.
3. Probar Gemini con una clave real puesta por el autor en la aplicación; documentar error sin conexión y respuesta malformada.
4. Preparar capturas legibles del informe y de las evidencias en imágenes.
5. Añadir a la matriz final las figuras de la memoria y el minuto exacto del vídeo para cada requisito.

**Referencia de evaluación:** el enunciado de la práctica 3 pide una memoria de 20–40 páginas (sin portada, índice y anexos), vídeo de al menos 10 minutos, repositorio de GitHub y trazabilidad entre requisito, implementación, prueba y evidencia. El autor quiere cerrar la entrega cuanto antes y no mostrar fecha en la memoria.
