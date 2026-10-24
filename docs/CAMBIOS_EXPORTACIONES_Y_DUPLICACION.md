# Revisión: exportaciones y duplicación

Fecha: 23/10/2026. Estado: bloque revisado y autorizado por el usuario para publicación.

## Problemas corregidos

- **Duplicar optimizaciones:** las dimensiones llegaban al formulario, pero la localización podía escribir una coma decimal en atributos `value` de campos numéricos. El navegador descartaba esos valores. Se usan valores sin localización para ancho, alto, margen y costos. Se conservan unidad, rotación, margen de sierra, material, costos, cliente y proyecto. Las piezas ya se guardan en la unidad ingresada: se retiró una segunda conversión que alteraba sus medidas al duplicar en metros, pulgadas u otras unidades.
- **PDF antiguo:** la descarga devolvía el PDF persistido, con imágenes del diseño anterior. Ahora construye la exportación actual en memoria desde el resultado disponible, sin sobrescribir archivos anteriores ni recalcular la distribución guardada.
- **Papel:** el PDF de optimización usaba A4 y la impresión A4 horizontal. Ambos pasan a carta; esto no modifica los PDF independientes de presupuestos o estadísticas.
- **Planos exportados:** cuando hay geometría disponible, el PDF dibuja un plano vectorial horizontal, con cotas, referencias P1/P2, colores, nombres, medidas originales y sobrantes rayados. La tabla aparece debajo y continúa en otra página si es necesario. Incluye aprovechamiento, piezas y desperdicio del tablero. La rotación es visual.
- **Impresión:** reutiliza los datos y el dibujo horizontal de la web; se eliminó la ejecución separada del algoritmo en blanco y negro y el filtro de escala de grises. Se solicita conservar colores al imprimir. El ajuste de color de la impresora sigue dependiendo del diálogo del navegador y del dispositivo.
- **Excel y botones de exportación:** se comprobó la descarga real y la apertura del libro. Se rechazan respuestas HTML/redirecciones de login en las descargas, para evitar guardar una página de sesión como si fuera un archivo. Los iconos reciben dimensiones y trazos explícitos; el problema de SVG grandes se describe también en el bloque de usabilidad.
- **PNG (revisión adicional):** las dos rutas de descarga devolvían directamente la imagen persistida y conservaban el diseño antiguo. Ahora usan un único exportador horizontal de alta resolución (2520 px de ancho), basado en la misma geometría de la web: cotas, nombres, referencias P1/P2, medidas originales, colores, sobrantes y tabla debajo. La altura se adapta al contenido de la tabla. Se cubren el menú del historial y el botón por tablero del resultado, incluido el HTML compartido cargado desde el historial. Los gráficos estadísticos no son planos de corte y mantienen su propia representación. No se sobrescriben imágenes guardadas ni se recalculan los cortes.

## Compatibilidad

Los resultados históricos con geometría guardada se exportan con el diseño actual. Si un resultado antiguo solo contiene imágenes y no tiene geometría, se conserva la imagen como respaldo: no se inventan posiciones ni se cambia el cálculo guardado. Las descargas siguen verificando al propietario.

No se modificaron modelos, migraciones, el algoritmo de corte ni los archivos personales del historial. La base de datos y los PDF locales que ya estaban modificados quedan fuera de este bloque.

## Verificación

- Suite completa: **147 pruebas correctas**, con base de datos de pruebas y `MEDIA_ROOT` temporal.
- Casos nuevos: duplicación en centímetros y metros, conservación del margen y rotación, impresión por el servicio compartido y accesos según preferencias.
- PDF de muestra inspeccionado visualmente: resumen y plano; páginas de **612 × 792 puntos**, tamaño carta.
- Excel descargado desde el navegador y abierto: hojas Resumen, Piezas y Resumen por Tablero.
- Vista de impresión inspeccionada con plano horizontal y colores.
- PNG inspeccionado visualmente. Pruebas de ambas rutas: imagen horizontal nueva en lugar del archivo vertical previo, resolución, tablero inexistente y aislamiento entre usuarios. Los registros históricos sin coordenadas mantienen la imagen original como respaldo, igual que el visor; no es posible reconstruir fielmente posiciones que no fueron guardadas.

## Agrupación futura

Primer commit de esta entrega: **corregir duplicación y actualizar exportaciones del plan de corte**. Los ajustes de sesión, tutorial, lupa y ayudas visuales se documentan en el segundo bloque. Se seleccionaron por separado los cambios de los archivos compartidos.


## Etiquetas adaptadas al espacio

Se unifica el criterio de etiquetas en el SVG compartido por resultado, historial e impresión, y en los exportadores PDF/PNG. Las piezas con espacio suficiente mantienen referencia, nombre y medidas. Si la descripción exigiría una letra demasiado pequeña, solo aparece una referencia P1/P2/P3 mayor y centrada. Los sobrantes estrechos conservan únicamente el rayado; las medidas siguen disponibles al pasar el cursor sobre el SVG. Las piezas conservan su información completa en la tabla y en el título emergente. El texto SVG se recorta dentro de su rectángulo y no intercepta el cursor del título.

La decisión depende de las proporciones del plano, no de los ejemplos ni de cambiar las medidas. No altera coordenadas, colores, cantidades ni cálculos. Verificado visualmente con piezas de 10 × 10, 30 × 30 y 40 × 39,96 cm. Se añadieron tres pruebas: referencia simplificada de mayor tamaño, sobrantes estrechos sin texto y SVG con detalle emergente y recorte. Suite completa: 147 pruebas correctas.
