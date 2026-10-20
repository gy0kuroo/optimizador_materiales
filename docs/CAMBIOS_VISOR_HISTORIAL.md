# Revisión del visor de tableros del Historial

Fecha: 19 de octubre de 2026.
Estado: revisado y autorizado para publicar por el usuario.

## Problema

La miniatura del Historial abría un visor antiguo con fondo oscuro, deslizador vertical y controles de zoom distintos a los de Resultado. Ese flujo no había recibido la mejora del visor del resultado.

## Cambios

- Se sustituye la barra lateral por controles horizontales: tablero anterior/siguiente, porcentaje, reducir, ampliar y ajustar tablero.
- Se muestra un tablero a la vez, identificado por su posición y número de optimización.
- La cabecera, los botones y las superficies utilizan las variables del tema y la misma escala visual del resto de la aplicación. La imagen conserva su fondo blanco para leer el plano original.
- El zoom va del 50 % al 400 %, con pasos de 25 puntos porcentuales. Ajustar tablero restablece la vista encajada al 100 %.
- Se utiliza desplazamiento nativo en lugar de arrastrar la imagen mediante transformaciones globales.
- La lupa se integra en la barra del visor y no mantiene su bloque flotante encima del dibujo.
- Se conserva el endpoint autenticado existente para recuperar los tableros y la imagen guardada como alternativa si no hay imágenes disponibles o falla la petición. Al cerrar se cancela la carga pendiente.
- Los controles se deshabilitan mientras carga la imagen y al llegar a los extremos de navegación o ampliación. Los errores de imagen se comunican dentro del visor.

El Historial sigue mostrando las imágenes PNG almacenadas, incluidos los textos incrustados en imágenes antiguas. Este cambio no regenera esas imágenes ni modifica optimizaciones, cálculos o archivos exportados.

## Validación

- Django sin incidencias; 49 plantillas compiladas correctamente.
- Sintaxis de los scripts de visor y del JavaScript inline del Historial verificada con Node.
- Revisión en navegador con un resultado temporal: apertura desde la miniatura, imagen cargada, zoom al 125 %, ajuste al 100 %, lupa integrada en la barra y regreso al Historial.
- Se comprobó que ya no existe el deslizador vertical en el documento del visor.

Pendiente de validación adicional: navegación entre múltiples tableros, recuperación ante fallos de red, tema oscuro y pantallas pequeñas.
