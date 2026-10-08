# Materiales: revisión visual y claridad

Fecha: 7 de octubre de 2026. Bloque revisado y aprobado por el usuario para publicación.

## Cambios

Se renuevan biblioteca, creación, edición y confirmación de eliminación. Las medidas de la biblioteca se presentan explícitamente en centímetros, igual que el área en cm². Al crear o editar, el formulario usa la unidad elegida y explica el precio por tablero en pesos chilenos. El precio cero se muestra como importe registrado, en lugar de Sin precio.

El formulario convierte las medidas a centímetros al guardar y de vuelta a la unidad elegida al editar. Se rechazan medidas cero, negativas o no finitas y precios negativos. Las pruebas verifican el recorrido en metros sin escalar repetidamente.

Las plantillas de datos del sistema conservan su protección: solo los administradores pueden modificar estos materiales, y no se permite eliminar un material en uso. Los registros históricos no se reescriben ni se infieren unidades para corregir datos anteriores.

## Presentación compartida

La hoja `management-refinement.css` se limita a estas pantallas. Mantiene la paleta, fondos que siguen el tema claro u oscuro, texto de 1.125 rem y controles de al menos 48 px. Los encabezados no llevan línea inferior, las tablas tienen desplazamiento horizontal y las acciones muestran textos explícitos.

## Verificación

Pasaron 30 pruebas de Gestión, materiales, presupuestos, permisos y Plantillas. Incluyen apertura de listas y formularios vacíos, detalles y edición con registros, selección de optimizaciones y conversión de medidas de materiales. El usuario aprobó la revisión visual; no se han automatizado todas las combinaciones de tema, letra y ancho de ventana.

No requiere migraciones. Publicación autorizada por el usuario. Se conservan los datos locales y las protecciones de acceso existentes.
