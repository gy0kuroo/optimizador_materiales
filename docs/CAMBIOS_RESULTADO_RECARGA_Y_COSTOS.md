# Resultado: recarga segura y costos compactos

## Problemas corregidos
- El formulario mostraba `resultado.html` directamente como respuesta al POST. Recargar podía reenviar ese POST y crear otra optimización.
- Los costos usaban filas y bloques de gran tamaño, con un total sobredimensionado y poca separación respecto de las acciones finales.

## Cambios
- Crear, editar y el procesamiento heredado de optimización redirigen a `resultado/<id>/` después de persistir el cálculo. El navegador termina en un GET: F5/Ctrl+F5 consulta el registro existente.
- La consulta web de un resultado con coordenadas guardadas prepara SVG sin regenerar PNG ni ejecutar el algoritmo. Exportaciones y compatibilidad con resultados históricos conservan la generación de imágenes por defecto.
- Los costos se presentan con etiquetas y valores en una cuadrícula compacta. Crear presupuesto queda como acción secundaria; se conservan las condiciones y los importes originales.
- Preparar otro corte y Ver historial tienen una zona independiente, título, explicación y separación de 32 px. En móvil los botones se apilan. El primero utiliza la jerarquía primaria existente.
- El skeleton de costos y acciones utiliza la misma disposición y conserva el revelado superior a inferior.

## Verificación
- **250 pruebas Django y 14 JavaScript aprobadas**.
- Prueba de creación seguida de tres GET con cabeceras de recarga: un solo registro, mismos datos persistidos, sin recalcular ni generar PNG.
- Prueba de edición: redirige al mismo registro; datos inválidos permanecen en el formulario. Acceso de otro usuario rechazado con 404.
- Las pruebas existentes de margen, precisión dimensional, nombres y resultado siguen la redirección para comprobar el contenido final.
- Revisión visual en escritorio y a 390 px: costos y navegación separados, sin solapamiento ni desbordamiento horizontal.
- Sin cambios en fórmulas, algoritmo, dependencias o migraciones. No se utilizaron Supabase ni datos reales para las pruebas.

Para verificar después de desplegar, generar un corte nuevo y comprobar que la URL final termina en `/resultado/<id>/`. Recargar esa URL debe conservar el mismo código e historial.

## Ajuste posterior de disposición
- Costos pasa a la columna analítica, justo debajo de Detalles técnicos. Se muestra como lista de etiquetas y valores, con el total separado y Crear presupuesto como acción secundaria.
- Son importes del plan completo: se conservan las cantidades de tableros y los valores. Al cambiar de tablero se presenta la misma información de costos; no se calcula un costo por tablero nuevo.
- Se elimina el título y la explicación junto a Preparar otro corte y Ver historial. Queda una fila exclusiva de botones alineada a la derecha, apilada en móvil.
- El skeleton traslada también los costos a la columna derecha; el revelado los muestra antes del resumen plegable. La vista del historial conserva su contenido existente.
- Seis pruebas Django dirigidas al resultado, condiciones de costos y recarga, más catorce pruebas JavaScript aprobadas. Sin cambios en cálculos, guardado o exportaciones.
