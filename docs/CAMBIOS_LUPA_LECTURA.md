# Lupa de lectura compartida

Fecha: 19 de octubre de 2026.
Estado: revisado y autorizado para publicar por el usuario.

## Uso

El botón «Lupa» aparece fijo en la esquina inferior derecha en las páginas con sesión iniciada que utilizan la plantilla compartida. Al activarlo aparece un recuadro centrado en el cursor, con ampliación inicial del 200 %. Los botones − y + permiten ajustar entre el 150 % y el 300 %, en pasos de 50 puntos porcentuales. Los controles se deshabilitan al alcanzar sus límites.

La lupa se desactiva pulsando nuevamente su botón o mediante Esc. Dentro de un diálogo, Esc desactiva primero la lupa y mantiene el diálogo abierto. La navegación con Tab también orienta la ampliación hacia el control enfocado. Al cambiar de página comienza desactivada; el estado no modifica las preferencias del perfil.

El recuadro sigue al cursor centrado sobre el punto señalado. Cerca de los bordes se limita su posición para que permanezca visible dentro de la ventana. Mientras la lupa está activa se oculta el puntero sobre la página; reaparece sobre los controles y al desactivarla. Es una primera versión orientada a ratón y teclado; la comodidad con pantallas táctiles queda pendiente de validación.

## Implementación

- Integración en `base.html` y archivos propios `magnifier.css` y `magnifier.js`.
- Copia visual del documento en un Shadow DOM aislado, marcada como no interactiva y oculta para lectores de pantalla. No se duplican formularios operativos ni se interceptan los clics sobre el documento real.
- Se excluyen scripts, marcos externos, contenido incrustado, la propia herramienta y regiones de avisos. Los campos de contraseña y valores ocultos no se reflejan en la copia.
- Se reproducen los valores actuales de los controles, el estado de selección y los canvas con contexto 2D. Los SVG e imágenes del tablero mantienen su representación visual.
- Actualización al cambiar contenido, escribir, desplazar o redimensionar. Los movimientos del cursor solo actualizan la posición mediante requestAnimationFrame; no reconstruyen todo el documento.
- Las animaciones se desactivan dentro de la copia para evitar que el texto vuelva a aparecer atenuado.
- Los controles se trasladan al diálogo abierto para respetar su manejo del foco, y vuelven a la página al cerrarlo.
- La herramienta no se imprime y no guarda capturas ni envía contenido a servicios externos.

La ampliación reproduce el contenido HTML de CutLess. No amplía la interfaz del navegador ni ventanas nuevas, documentos PDF externos o menús nativos desplegados por el sistema. No sustituye el control de tamaño de letra del perfil ni el zoom propio del visor.

## Validación realizada

- Comprobación de Django sin incidencias y compilación correcta de las 49 plantillas.
- Sintaxis JavaScript correcta con Node.
- Prueba en navegador con usuario, base de datos y resultado de optimización temporales: activación, ampliación de texto en Inicio, navegación mediante foco y ampliación del SVG dentro del visor del resultado.
- Aumento hasta 300 % y desactivación del botón + al llegar al límite.
- Esc cierra la lupa, oculta el recuadro y conserva abierto el visor del tablero.
- Cierre del visor y regreso de los controles a la página.

Pendiente: revisión de comodidad por el usuario, validación visual completa con tema oscuro y tamaños de letra grandes, y pruebas de uso en pantallas táctiles y páginas con contenido extenso.

## Ajuste solicitado: recuadro centrado y cursor oculto

Se retira el desplazamiento lateral del recuadro. La lupa se centra en el punto señalado y sustituye visualmente al cursor, que se mantiene visible sobre los controles de ampliación. Al desactivar mediante el botón o Esc se retira la clase que oculta el puntero y se recuperan los cursores propios de cada elemento. El recuadro conserva `pointer-events: none`, permitiendo que los clics lleguen al elemento original que se está señalando.

Se mantienen los límites de la ventana: en los extremos la caja se desplaza lo mínimo necesario para no quedar cortada, manteniendo la zona señalada en el centro del contenido ampliado.

## Solapamiento de controles en la revisión de tableros

Se reprodujo que el bloque flotante de controles e instrucciones tapaba parte de la información lateral del visor. Dentro de diálogos, los controles pasan a ocupar espacio en la barra del visor, o en su cabecera si no dispone de barra. La ayuda flotante se oculta allí, manteniendo las instrucciones accesibles. Fuera del diálogo recuperan su posición fija habitual.

La copia ampliada reserva el espacio ocupado por estos controles para conservar la distribución original sin duplicarlos en el recuadro. La lupa conserva el movimiento centrado y el cursor oculto solicitados por el usuario.

Se comprobó visualmente la integración dentro del visor con los datos laterales libres del bloque de controles. La captura posterior del usuario identificó también el visor antiguo del Historial; su actualización se documenta en CAMBIOS_VISOR_HISTORIAL.md.

También se verificó en Inicio el centrado del recuadro, cursor oculto sobre la página, cursor visible sobre los controles y restauración del cursor al desactivar mediante Esc.
