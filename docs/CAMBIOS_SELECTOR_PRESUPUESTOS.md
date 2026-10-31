# Selector compacto de presupuestos — 31/10/2026

## Cambios
Crear y editar presupuestos, y agregar planes a un presupuesto existente, comparten una tabla compacta en lugar de tarjetas grandes. Se muestran seis optimizaciones por página, con búsqueda por nombre, código o pieza, contador de seleccionadas y navegación junto al buscador. El resultado completo se consulta en otra pestaña.

La paginación y búsqueda se realizan sobre el HTML cargado: no envían el formulario ni reinician sus campos. Las casillas de otras páginas siguen perteneciendo al formulario y se envían junto con las visibles. Los filtros no desmarcan opciones. El servidor mantiene las validaciones de propietario y costos.

En editar, la fecha usa el widget de Django: se conserva también después de un error de validación. Sin JavaScript se presenta la lista completa como alternativa funcional. No se modificaron cálculos, esquema, permisos ni datos existentes.

## Alcance y verificación
23 pruebas aprobadas de revisión, presupuestos y gestión. Pruebas de renderizado de los tres flujos, selección inicial y recuperación de selecciones/fecha después de un envío inválido. Comprobación local en navegador de cambio de página y búsqueda sin perder datos. A diferencia del selector de proyectos, esta paginación no reduce la cantidad de registros transferidos desde el servidor: limita lo visible y preserva los campos sin recargas. Para historiales muy grandes puede requerirse búsqueda remota en una etapa posterior.

No se ejecutaron commits, push ni despliegues.
