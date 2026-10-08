# Proyectos: revisión visual y claridad

Fecha: 7 de octubre de 2026. Bloque revisado y aprobado por el usuario para publicación.

## Cambios

Se renuevan lista, creación, edición, detalle, eliminación y selección de optimizaciones. Se etiquetan los filtros y se separan visualmente las acciones de consultar, editar y eliminar. Los indicadores del detalle utilizan texto legible y colores neutros.

Se corrigen las instrucciones de selección: se usan casillas, no Ctrl. Los registros seleccionables se presentan en un área con desplazamiento vertical. La eliminación sigue requiriendo confirmación y POST.

Se corrige un fallo previo al abrir Editar proyecto: faltaba importar `Q` para construir el filtro de optimizaciones disponibles. Las pruebas recorren esa pantalla con registros.

## Presentación compartida

La hoja `management-refinement.css` se limita a estas pantallas. Mantiene la paleta, fondos que siguen el tema claro u oscuro, texto de 1.125 rem y controles de al menos 48 px. Los encabezados no llevan línea inferior, las tablas tienen desplazamiento horizontal y las acciones muestran textos explícitos.

## Verificación

Pasaron 30 pruebas de Gestión, materiales, presupuestos, permisos y Plantillas. Incluyen apertura de listas y formularios vacíos, detalles y edición con registros, selección de optimizaciones y conversión de medidas de materiales. El usuario aprobó la revisión visual; no se han automatizado todas las combinaciones de tema, letra y ancho de ventana.

No requiere migraciones. Publicación autorizada por el usuario. Se conservan los datos locales y las protecciones de acceso existentes.
