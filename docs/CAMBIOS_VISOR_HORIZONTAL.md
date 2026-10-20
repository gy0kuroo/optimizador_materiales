# Disposición horizontal del visor de corte

Fecha: 20 de octubre de 2026. Integrado en el bloque general de reforma visual, aprobado para publicación por el usuario.

## Alcance

Se reorganiza la página de resultados y su visor ampliado. No se cambian la paleta, las familias tipográficas, los botones disponibles, los cálculos del optimizador, los datos almacenados ni las exportaciones.

## Distribución

- Dos columnas de aproximadamente 65 % y 35 %: dibujo y tabla a la izquierda; resumen y detalles técnicos a la derecha, cada bloque en su tarjeta.
- Los tableros verticales se representan apaisados. Los que ya tienen el lado largo horizontal no se vuelven a girar.
- El indicador «Tablero X de N» permanece encima del plano, con sus controles existentes.
- Cotas reales: dimensión horizontal centrada sobre el tablero y dimensión vertical al costado izquierdo. Las líneas delimitan los extremos del tablero.
- En ventanas de hasta 1100 px, primero aparecen dibujo y tabla, después resumen y detalles. Las tablas anchas tienen desplazamiento dentro de su contenedor.
- El visor ampliado conserva los controles anteriores y presenta también la tabla debajo del dibujo.

## Correspondencia de los datos

Las referencias web pasan de números a `P1`, `P2`, etc. Se usa el identificador original del catálogo, compartido entre todos los tableros; por eso un tablero puede contener solo `P2`. El color se toma del mismo catálogo guardado, sin reasignarlo.

Cada pieza incluye referencia, nombre y medidas solicitadas. La transformación visual de una pieza en un tablero vertical es `(x, y, ancho, alto) → (alto_tablero − y − alto, x, alto, ancho)`. Se crea una copia de presentación; las coordenadas originales permanecen intactas. Los textos de medidas provienen del catálogo solicitado, no del rectángulo ya girado.

La tabla contiene número de fila, nombre/color, medidas en la unidad elegida, cantidad en este tablero, área en m² y referencia. El área corresponde al conjunto de piezas de esa fila: ancho × alto en cm × cantidad / 10000.

El resumen muestra el aprovechamiento del tablero en una dona, una interpretación breve y seis datos: desperdicio porcentual y superficie, piezas colocadas en total, tipos presentes en el tablero, tableros usados, ancho de sierra y permiso de giro. Una nota distingue el número de piezas de este tablero de los totales del corte. Los detalles técnicos utilizan los parámetros y la fecha guardados en la optimización.

El porcentaje de desperdicio es el complemento del aprovechamiento guardado. Las superficies existentes se mantienen en la unidad elegida; el ancho de sierra se muestra en mm. No se sustituyen datos reales por los valores de la imagen de referencia.

## Sobrantes

El rayado representa espacios geométricos sin piezas, derivados exclusivamente de sus coordenadas guardadas. Se divide el complemento en rectángulos disjuntos para poder indicar medidas reales. Una zona con forma irregular puede mostrarse como varios rectángulos.

Las franjas cuyo lado menor no supera el ancho de sierra no se anuncian como sobrantes. Esto es una distinción visual; no certifica que los espacios sean recortes recuperables ni modifica el desperdicio calculado. Las ranuras de corte siguen formando parte de los datos originales.

Los resultados antiguos sin coordenadas conservan su imagen y la lista del pedido completo, con una aclaración. No se inventa una distribución ni se vuelve a ejecutar el algoritmo para reconstruirlos.

## Archivos y verificación

- `cut/cutless/services/board_presentation.py`: transformación y complemento geométrico de presentación.
- `cut/cutless/services/optimization.py`: incorpora los datos derivados al contexto, sin persistirlos.
- `cut/cutless/templates/cutless/includes/board-layout.html`: dibujo con cotas, tabla, resumen y datos técnicos.
- `cut/cutless/templates/cutless/resultado.html`: integración y eliminación de los resúmenes duplicados de la parte superior.
- `cut/cutless/static/cutless/css/board-landscape.css`: disposición adaptable, usando los colores y fuentes del tema.
- `cut/cutless/static/cutless/js/board-viewer.js`: coloca la tabla del tablero seleccionado debajo del dibujo ampliado.
- `cut/cutless/templates/cutless/base.html`: actualiza los destinos del recorrido de ayuda existente para la nueva disposición.

Validación: **132 pruebas correctas**, incluidas cinco nuevas pruebas de orientación, conservación de medidas/datos, área del complemento, ausencia de solapes, exclusión de ranuras y compatibilidad con resultados antiguos. Django no informa incidencias y las plantillas compilan. Revisión en navegador integrado con casos de uno y dos tableros, cambio de selección, visor ampliado, temas claro/oscuro y presentación móvil de 390 px.

Las exportaciones PDF, Excel y PNG conservan su formato anterior; esta revisión cambia la presentación web.
