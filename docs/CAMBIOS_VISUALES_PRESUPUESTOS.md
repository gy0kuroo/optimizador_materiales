# Presupuestos: revisión visual y claridad

Fecha: 7 de octubre de 2026. Bloque revisado y aprobado por el usuario para publicación.

## Cambios

Se renuevan lista, creación, edición, detalle y selección de optimizaciones. La búsqueda por número o cliente y el filtro de estado tienen etiquetas visibles. Editar y PDF utilizan presentación secundaria; las acciones de consulta son explícitas.

Las casillas se muestran a 24 px con etiquetas asociadas. Se elimina la indicación incorrecta de mantener Ctrl para seleccionar. El detalle conserva los totales del presupuesto y muestra los costos registrados de cero. La tabla de desglose permite desplazamiento horizontal. La ayuda señala los títulos actuales.

Se mantienen el cálculo del presupuesto, sus estados, la generación de PDF y la selección por propietario. Marcar un presupuesto como Enviado no equivale a enviar un correo; no se añade envío automático.

## Presentación compartida

La hoja `management-refinement.css` se limita a estas pantallas. Mantiene la paleta, fondos que siguen el tema claro u oscuro, texto de 1.125 rem y controles de al menos 48 px. Los encabezados no llevan línea inferior, las tablas tienen desplazamiento horizontal y las acciones muestran textos explícitos.

## Verificación

Pasaron 30 pruebas de Gestión, materiales, presupuestos, permisos y Plantillas. Incluyen apertura de listas y formularios vacíos, detalles y edición con registros, selección de optimizaciones y conversión de medidas de materiales. El usuario aprobó la revisión visual; no se han automatizado todas las combinaciones de tema, letra y ancho de ventana.

No requiere migraciones. Publicación autorizada por el usuario. Se conservan los datos locales y las protecciones de acceso existentes.
