# Estadísticas: presentación y claridad

Fecha: 7 de octubre de 2026. Bloque revisado y aprobado por el usuario para publicación.

## Cambios

- Organización en período de consulta, resumen, gráficos y hasta diez mejores resultados. Encabezado sin línea inferior y ayuda contextual con nombre descriptivo.
- Tarjetas neutras, bordes suaves, texto de 1.125 rem y botones de al menos 48 px. Estilos limitados a Estadísticas y colores que siguen el tema claro u oscuro.
- Períodos expresados como últimos 7, 30 o 365 días, coincidiendo con el filtro existente. La selección se confirma con Aplicar período; ya no recarga automáticamente.
- Exportaciones secundarias agrupadas junto al período. Se explica que resumen, gráficos y descargas corresponden al período aplicado y que cada optimización cuenta por igual en el promedio.
- Gráficos en azul y café de la paleta, sin emojis en los títulos. Las fechas del último mes muestran día y mes; las del último año, mes y año.
- Ampliar gráfico es un botón accesible por teclado, con texto siempre visible. Las imágenes conservan un fondo blanco para mantener el contraste de sus ejes en ambos temas.
- Visor con ampliación horizontal entre 50% y 300% y desplazamiento nativo. Restablecer vuelve al 100% y al comienzo de la imagen. Se reutiliza el modal y se registra una sola vez el evento del control, evitando acumulaciones al reabrir.
- Tabla con colores neutros, tipografía legible, enlace Ver resultado y unidades de pieza correspondientes a la optimización, en lugar de mostrar siempre cm.
- Se eliminan los enlaces inferiores repetidos a Inicio e Historial. El estado vacío mantiene la acción Preparar un corte.
- Ayuda actualizada para explicar el botón Aplicar período y la lista de mejores resultados.
- Corrección posterior a la revisión del usuario: la flecha del selector se repetía por un reinicio del fondo en los estilos compartidos. Se conserva la imagen al cambiar el color de fondo, se fija una única flecha a la derecha y se reserva espacio para el texto. En modo oscuro la flecha usa un tono claro. La corrección compartida también cubre foco y otros selectores con `form-select`.

## Validación

- Comprobación de Django: sin incidencias.
- Las 14 pruebas existentes de permisos pasan, incluido acceso a Estadísticas y protección de exportaciones.
- JavaScript ejecutado en Node con DOM simulado: ampliación, restablecimiento, reapertura sin eventos adicionales y manejo de un gráfico inexistente correctos.
- El usuario revisó el bloque y aprobó su publicación. No se ha comprobado automáticamente la apariencia en todas las combinaciones de tema, letra y ancho de ventana.

No cambia el cálculo de indicadores ni requiere migraciones. Se conservan los filtros por usuario y las rutas de exportación. No se modifican datos locales.
