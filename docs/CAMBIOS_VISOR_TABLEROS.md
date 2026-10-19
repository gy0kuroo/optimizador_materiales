# Resultado legible y visor de tableros

Fecha: 19 de octubre de 2026. Versión revisada por el usuario y aprobada para publicación.

## Problemas atendidos

La descripción de las piezas estaba incrustada en el PNG y resultaba pequeña al ajustar la imagen. El visor escalaba todo el contenedor, incluyendo los datos, y dependía de un control deslizante y arrastre poco evidentes. El botón Atrás del navegador podía sacar al usuario del resultado cuando intentaba cerrar la imagen.

## Presentación del resultado

- Cada tablero ocupa una tarjeta con dibujo y datos separados. Las medidas, aprovechamiento, desperdicio y cantidad de piezas se muestran como texto de la página.
- Los resultados nuevos incluyen una tabla de piezas por tablero con número, color, nombre, medidas y cantidad. Es texto HTML que respeta el tamaño de letra del usuario.
- El dibujo web utiliza SVG, ampliable sin pixelación, con la misma distribución, numeración y colores que el PNG generado. Los nombres y medidas completos permanecen en la tabla.
- La distribución y el catálogo se capturan durante la generación del gráfico y se guardan en `resultado_extra.vistas_web`, un campo JSON ya existente. Al abrir un resultado guardado no se vuelve a ejecutar el algoritmo para construir esta vista.
- Los PNG y PDF conservan su presentación de descarga. No se modifica el algoritmo de distribución ni se requiere una migración.

## Resultados anteriores

Los resultados guardados antes de este cambio pueden no tener datos vectoriales. Se conserva su imagen original y se muestra una tabla legible de las piezas solicitadas para el corte completo. Se identifica expresamente que esa lista no es el desglose por tablero.

No se reconstruyen posiciones por suposición ni se reemplazan automáticamente los resultados antiguos. Para comprobar la presentación completa del nuevo dibujo y su tabla por tablero, generar una nueva optimización.

## Controles del visor

- Abrir visor del tablero es un botón accesible por teclado.
- Los botones + y − amplían o reducen solo el dibujo, entre 50% y 400% de su tamaño ajustado.
- Ajustar tablero vuelve al 100% y al comienzo del desplazamiento.
- El área del dibujo permite desplazamiento normal, con barras o gestos táctiles. La información lateral mantiene su tamaño de lectura.
- Tablero anterior y Tablero siguiente permiten recorrer el resultado sin cerrar el visor. Los extremos desactivan el botón que no corresponde.
- En móvil la información pasa debajo del dibujo y el cuerpo del visor permite desplazarse verticalmente.
- Se mantienen la paleta y los temas claro y oscuro; el área del plano conserva fondo blanco para distinguir las piezas y sus límites.

## Navegación del navegador

Abrir el visor crea una sola entrada de historial en la misma página. Cambiar de tablero actualiza esa entrada sin añadir una por cada cambio.

- Atrás cierra el visor y conserva el resultado en pantalla.
- Adelante puede reabrir el último tablero que se estaba viendo.
- Volver al resultado y Escape cierran el visor utilizando el mismo recorrido.

La protección corresponde al visor abierto. Una vez cerrado, Atrás conserva su comportamiento habitual de navegar a la página anterior. No se bloquea la navegación general del usuario.

## Archivos

- `cut/cutless/render.py`: datos de la distribución web capturados al generar el resultado.
- `cut/cutless/services/optimization.py`: persistencia, recuperación y conversión de las medidas para la tabla.
- `cut/cutless/templates/cutless/resultado.html`: tarjetas, tablas, SVG y controles del visor.
- `cut/cutless/static/cutless/css/resultado.css`: disposición de datos y dibujo, adaptación móvil y temas.
- `cut/cutless/static/cutless/js/board-viewer.js`: ampliación, navegación entre tableros e historial.
- `cut/cutless/tests/test_visor.py` y `test_persistencia.py`: pruebas de datos, unidades, compatibilidad y lectura sin recalcular.

## Verificación

- Pasaron 125 pruebas de CutLess, usuarios y configuración inicial, ejecutadas con archivos temporales separados de los datos reales.
- Comprobación Django y sintaxis JavaScript: correctas.
- Navegador con usuario, base y resultados temporales: tabla por tablero, numeración y colores, zoom al 125%, ajuste al 100%, cambio de tablero, Atrás, Adelante, cierre explícito y Escape.
- Atrás también se comprobó después de generar un resultado desde el formulario POST: el visor se cerró y el resultado permaneció visible sin reenviar el formulario.
- Revisión visual de escritorio, móvil de 390 px y tema oscuro con letra grande. No hubo desbordamiento horizontal del visor en el ancho móvil comprobado.

La lupa global propuesta por el usuario no se implementa en este bloque; queda pendiente para revisarla después. El usuario confirmó el funcionamiento y aprobó su publicación.
