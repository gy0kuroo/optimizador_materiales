# Datos legibles en las imágenes del plan de corte

Fecha: 19 de octubre de 2026.
Estado: validado y autorizado para publicar por el usuario.

## Problema

La leyenda anterior repartía cada tipo de pieza en un bloque de cinco líneas a lo largo de toda la altura disponible, incluso cuando solo había un tipo. La letra de ocho puntos y el resumen situado sobre el borde inferior del plano dificultaban leer la imagen.

## Cambios

- Tabla compacta con número, nombre, medidas solicitadas y cantidad en ese tablero.
- Identificación de color en la celda del número, correspondiente al dibujo; se retira el código hexadecimal, innecesario para interpretar el plano.
- Texto de tabla de doce puntos, título de leyenda de quince y encabezados con fondo neutro de la paleta.
- Nombres completos distribuidos en varias líneas, midiendo su ancho para impedir que invadan otras columnas. La altura de las filas y de la figura aumenta cuando el contenido lo necesita.
- Distribución más cercana entre el dibujo y su tabla; se mantiene la proporción real del tablero.
- El resumen de piezas, área usada y desperdicio pasa al bloque de información, fuera del plano y sus ejes.
- PNG a 160 ppp frente a los 120 anteriores.

Se conservan el algoritmo, las posiciones, la numeración global, los colores por tipo, las cantidades por tablero y la conversión de unidades de la leyenda. Los metadatos de la vista vectorial web mantienen su estructura.

## Aplicación y límites

El diseño se aplica al generar imágenes nuevas mediante el renderizador, incluidos los procesos que regeneran explícitamente una imagen. Los resultados ya persistidos conservan sus imágenes y documentos existentes: esta revisión no recalcula ni sobrescribe el historial automáticamente. El visor web que dispone de geometría vectorial sigue mostrando su tabla HTML independiente.

Con muchos tipos o nombres extensos la imagen puede ser más alta para conservar el tamaño de letra. La lectura final también depende del tamaño al que se muestre o imprima el archivo.

## Validación

- Suite completa: 127 pruebas correctas.
- Nuevas comprobaciones: nombres largos dentro de sus celdas sin truncamiento, tamaño de letra, tipos presentes, cantidades y conversión a milímetros.
- Se mantienen las pruebas existentes de áreas y exportaciones, incluida el área usada en pies cuadrados.
- Inspección visual de PNG generados con un tipo de pieza (18 puertas de 40 × 40 cm) y con tres tipos (82 piezas), sin alterar datos del usuario.
