# Historial: mismo visor horizontal que el resultado

Fecha: 20 de octubre de 2026. Integrado en el bloque general de reforma visual, aprobado para publicación por el usuario.

## Problema y cambio

El resultado mostraba un plano horizontal con cotas y datos separados, pero «Ampliar imagen» en el Historial abría únicamente el PNG antiguo. Ambos accesos daban una presentación distinta del mismo corte.

Ahora el visor del Historial reutiliza `cutless/includes/board-layout.html` y los datos de presentación de `preparar_contexto_resultado`, exactamente como el resultado:

- Plano horizontal con cotas, nombres, medidas originales, referencias P y sobrantes rayados.
- Tabla de piezas debajo del dibujo.
- Resumen con dona y detalles técnicos a la derecha.
- En móvil, dibujo y tabla primero; resumen y detalles después.

Se mantienen los botones de navegación, zoom, ajuste y regreso existentes. Al cambiar de tablero se actualizan juntos dibujo, tabla y datos. Abrir otra optimización o cerrar el visor cancela la solicitud pendiente y limpia el contenido anterior.

## Compatibilidad y datos

La API existente acepta el parámetro opcional `presentacion=horizontal` y devuelve los fragmentos HTML renderizados por Django en `paneles`. Sin ese parámetro, su respuesta original de imágenes y total se conserva. La consulta sigue limitada al usuario propietario.

Los nombres y otros textos se escapan mediante las plantillas de Django. El navegador recibe contenido de la misma aplicación y extrae únicamente el dibujo, la tabla y el bloque de datos del fragmento compartido.

No se modifica la distribución guardada, el algoritmo, la paleta, las fuentes ni las exportaciones. Los resultados sin coordenadas siguen utilizando su imagen original; si falla la consulta se conserva la alternativa de la miniatura, sin inventar datos.

El fondo de los visores usa la superficie del tema existente para que las cotas sigan siendo legibles en modo oscuro. Las tarjetas comparten bordes y disposición con el resultado.

## Archivos

- `cut/cutless/views/exports.py`: presentación opcional en la API protegida.
- `cut/cutless/templates/cutless/historial.html`: zonas de dibujo/tabla y resumen/detalles.
- `cut/cutless/static/cutless/js/history-board-viewer.js`: carga compartida, cambio sincronizado de tablero y zoom de SVG o imagen.
- `cut/cutless/static/cutless/css/board-landscape.css`: disposición compartida y adaptación al Historial.
- `cut/cutless/templates/cutless/resultado.html`: actualiza la versión de la hoja compartida.
- `cut/cutless/tests/test_history_horizontal.py`: compatibilidad de la API, datos sin cambios y aislamiento entre cuentas.

## Validación

Suite completa: **135 pruebas correctas**. Django sin incidencias y sintaxis JavaScript correcta. Revisión en navegador integrado con dos tableros guardados: cambio de tablero y actualización del catálogo, zoom a 125 %, ajuste a 100 %, cierre/reapertura, modo oscuro y vista móvil de 390 px sin desbordamiento horizontal de la página.

Documentación relacionada: [Visor horizontal](CAMBIOS_VISOR_HORIZONTAL.md).


## Corrección adicional: miniatura de la tarjeta

La primera revisión corrigió el visor ampliado, pero la tarjeta seguía usando el PNG vertical guardado. Ahora la miniatura se dibuja con las coordenadas del primer tablero (`resultado_extra.vistas_web["1"]`) y la misma plantilla SVG del visor, extraída a `cutless/includes/board-drawing.html`.

La vista del Historial prepara solo los elementos de la página actual, sin ejecutar el optimizador ni escribir imágenes. La miniatura incluye la orientación horizontal, cotas, referencias y colores del primer tablero. Los identificadores de los patrones SVG son distintos por optimización para evitar interferencias entre tarjetas.

Se conserva el clic que abre el visor existente. Los archivos PNG/PDF almacenados no cambian. Los resultados antiguos sin coordenadas conservan su imagen original como alternativa.

Archivos adicionales: `cut/cutless/views/historial.py`, `cut/cutless/templates/cutless/includes/board-drawing.html` y la integración de esa plantilla en `board-layout.html` y `historial.html`.

Validación tras esta corrección: **137 pruebas correctas**, incluidas miniatura horizontal sin recálculo ni cambios de datos y alternativa para resultados antiguos. Revisión visual de la tarjeta y apertura/cierre del visor desde la nueva miniatura.
