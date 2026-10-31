# Comparación de alternativas del mismo trabajo — 31/10/2026

## Objetivo
Ayudar a evaluar cuánto material y costo necesita cada alternativa para las mismas piezas. Función opcional y sujeta a revisión del primer entregable.

## Implementación
- Servicio de solo lectura sobre resultados guardados, sin recalcular optimizaciones ni modificar historial.
- Comprobación de nombres, ancho, alto y cantidades acumuladas. Ignora orden de líneas, mayúsculas y espacios repetidos; convierte cm/m/mm/in/ft a cm con resolución de comparación de 0,01 cm. Se agregan cantidades de líneas equivalentes. No intercambia ancho y alto porque puede importar la orientación solicitada.
- Datos mal formados o piezas distintas: explicación y comparación informativa, sin conclusiones que recomienden una alternativa para el mismo trabajo.
- Tabla de material necesario en tableros completos, cantidad de tableros, aprovechamiento guardado, material fuera de las piezas y costo estimado.
- El material necesario es ancho × alto × cantidad de tableros en m². El material fuera de las piezas resta el área solicitada e incluye sobrante y pérdida de corte; no se presenta como sobrante reutilizable.
- Barras de material y costo con valores visibles. Cada gráfico tiene su propia escala común A/B. El gráfico de costo solo aparece con dos precios; el precio cero sigue siendo válido.
- Conclusiones separadas sobre superficie, tableros y costo. Menos tableros no se interpreta automáticamente como menos material. Se muestran cambios de tamaño, material, sierra, rotación y precios para contextualizar.
- Tabla desplegable de piezas y cantidades para entender la equivalencia o su ausencia. Selector A/B permanece visible para cambiar alternativas.

## Límites
Los nombres diferentes no se consideran equivalentes automáticamente. La resolución de 0,01 cm se utiliza para agrupar medidas en esta comparación, no modifica las dimensiones guardadas ni el algoritmo. Los costos utilizan precios y mano de obra históricos, no precios de mercado; materiales con propiedades distintas requieren evaluación del usuario. La vista no certifica calidad, veta, resistencia, cortes ejecutados ni sobrantes aprovechables. No decide una compra ni asigna un ganador universal.

## Verificación
28 pruebas de comparación y regresión aprobadas: equivalencia entre unidades/orden/agrupaciones, orientación, cantidades distintas, datos inválidos, diferencia entre cantidad y superficie de tableros, costo cero/ausente, sierra en mm y presentación. Se mantienen controles de propietario y resultados completos. Revisión visual local con datos de ejemplo en copia temporal; no se modifica Supabase. Sin commit, push ni despliegue.

Verificación final: **227 pruebas Django aprobadas** en la suite completa, con base de pruebas y archivos temporales aislados; `git diff --check` sin errores.
