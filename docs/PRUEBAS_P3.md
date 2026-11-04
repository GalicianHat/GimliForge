# Pruebas reproducibles de GimliForge 2.0

Estado: ejecución local en Windows los días 3 y 4 de noviembre de 2026. Datos ficticios; no se utilizó una clave de Gemini.

| ID | Procedimiento | Resultado observado | Requisitos |
| --- | --- | --- | --- |
| P-01 | Ejecutar la batería de `unittest`. | 16 pruebas correctas. | RF-01 a RF-05, RNF-01 a RNF-04 |
| P-02 | Generar LaTeX y PDF con `datos_entrada/demo_con_evidencia.json` y `--pdf`. | PDF A4 de 13 páginas, cinco gráficos vectoriales y una imagen incrustada. Se revisaron portada, gráficos, evidencia y última página. | RF-01, RF-04, RF-05, MEJ-01, MEJ-02 |
| P-03 | Crear una auditoría en el navegador local, completar un hallazgo, añadir PNG y pie, guardar, volver a la lista y reabrir. | Proyecto persistido en el equipo; al reabrir, texto, imagen y pie seguían presentes. | RF-02, MEJ-01, MEJ-04 |
| P-04 | Pulsar «Descargar PDF» en la auditoría reabierta. | Mensaje «Informe PDF descargado» y archivo `informe_gimliforge.pdf` descargado. | RF-05, MEJ-04 |
| P-05 | Extraer el ZIP 2.0 en una carpeta nueva de Windows; validar `demo.json` y ejecutar las pruebas desde esa copia. | JSON válido con dos hallazgos; 16 pruebas correctas en el paquete de revisión. ZIP íntegro y sin proyectos ni claves. | MEJ-04, RNF-04 |
| P-06 | Enviar una petición de creación desde un origen ajeno y después JSON mal formado desde el origen local. | Respuestas HTTP 403 y 400, respectivamente; la lista de proyectos permaneció vacía. Prueba automatizada ejecutada en Windows. | RNF-01, seguridad |

Comando de P-02 desde la raíz del repositorio:

```powershell
python GimliForge.py --file datos_entrada/demo_con_evidencia.json --output informe_prueba.tex --pdf
```

La evidencia de P-02 es `GimliForge-2.0-prueba-integral.pdf` en el paquete de revisión local. El PNG de prueba es sintético y no demuestra una vulnerabilidad real.

## Pendiente de verificar

- P-07: introducir una clave real de Gemini por el botón local y revisar varias propuestas y errores de red. Requiere una clave que aporte el autor; ninguna se guarda en este material.
- P-08: instalación limpia y ejecución en macOS y Linux. Este equipo solo permite comprobar Windows.
- P-09: revisar la página publicada, enlaces y cabeceras HTTP una vez que el autor autorice la publicación.
- P-10: grabar el vídeo definitivo de al menos diez minutos y anotar sus minutos en la matriz.

Estas pruebas separan resultados observados de prestaciones aún no comprobadas. No implican que los informes ficticios validen hechos de una auditoría real.
