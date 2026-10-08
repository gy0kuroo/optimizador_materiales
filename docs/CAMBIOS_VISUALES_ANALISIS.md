# Análisis: comparación y costos

Fecha: 7 de octubre de 2026. Bloque revisado y aprobado por el usuario para publicación.

## Presentación compartida

Las pantallas Comparar optimizaciones e Historial de costos usan `analysis-refinement.css`, limitada a sus clases de página. Comparten la paleta, tarjetas neutras, títulos claros, texto de 1.125 rem y controles de al menos 48 px. Las tablas se desplazan horizontalmente cuando no caben; los estilos se adaptan a claro y oscuro.

Se sustituyen emojis y colores decorativos por textos explícitos y se eliminan enlaces al inicio e historial repetidos en el encabezado. La ayuda mantiene su botón y describe los controles actuales.

## Comparar optimizaciones

- Estado vacío explicativo cuando hay menos de dos registros.
- Primera y segunda optimización sustituyen a los títulos #1 y #2, que podían confundirse con identificadores reales.
- Las dimensiones siguen expresadas en centímetros y ahora se indica explícitamente.
- Se explica que las diferencias son segunda menos primera. Los cambios entre porcentajes se etiquetan como puntos porcentuales.
- Ver resultado abre cada plan de corte. Comparar otras optimizaciones permite reiniciar la selección.
- La diferencia de costos se calcula con los valores decimales en la vista; se elimina la expresión incorrecta de suma en la plantilla. También se muestran costos registrados de cero.
- Se rechaza comparar el mismo registro. Identificadores inválidos y registros ajenos vuelven al selector con un mensaje, manteniendo el filtro por propietario.

## Historial de costos

- Filtros Desde/Hasta con etiquetas asociadas, acciones Aplicar fechas y Quitar filtros.
- Exportar Excel visible junto a Ayuda cuando hay registros. El enlace conserva las fechas aplicadas.
- Tarjetas y tabla con importes legibles y sin colores que compitan con el contenido.
- Se aclara que aparecen optimizaciones con precio de tablero registrado, y que el total suma material y mano de obra. Las medidas siguen en centímetros.
- Los registros de importe cero se incluyen en el detalle, el resumen y la exportación para que el contador y los promedios correspondan a la misma colección.
- El gráfico usa azul de la paleta y orden cronológico ascendente; la tabla conserva los más recientes primero.

## Verificación

Pasaron 18 pruebas: las 14 existentes de permisos y cuatro nuevas de análisis. Cubren diferencias de costos en ambos sentidos, rechazo del mismo registro e identificadores inválidos, protección de registros ajenos y coherencia del detalle y promedio con importe cero.

El usuario revisó el bloque y aprobó su publicación. No se ha automatizado la revisión de todas las combinaciones de tema y ancho de ventana. No requiere migraciones.
