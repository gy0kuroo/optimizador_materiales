# Selección de optimizaciones para proyectos — 31/10/2026

## Problema
La lista completa crecía con el historial y obligaba a desplazarse hasta el final para agregar planes.

## Cambio
- Paginación real en servidor: ocho optimizaciones por página, recientes primero y orden estable.
- Búsqueda por nombre del plan, identificador OPT o nombre de pieza.
- Contador de seleccionadas y acción de agregar antes de la tabla.
- Selección conservada mediante formularios POST al cambiar de página o buscar, sin depender de almacenamiento del navegador ni JavaScript.
- La casilla del encabezado selecciona exclusivamente los registros de la página visible.
- Buscar y paginar no asocian registros; solo «Agregar al proyecto» guarda la selección completa.
- Sin coincidencias, se conserva la búsqueda, la selección y la posibilidad de agregar lo marcado en otras páginas.
- Se mantienen las comprobaciones de propietario y de disponibilidad: solo planes sin proyecto pueden agregarse. Los identificadores manipulados no amplían permisos.
- Estilos adaptables y colores de la interfaz actual; sin cambios en el algoritmo ni en la base de datos.

## Verificación
Pruebas de paginación con diez planes, selección entre páginas, búsqueda sin resultados, conservación de selección, ausencia de guardado al navegar y asociación final de varios planes. 18 pruebas de revisión y gestión aprobadas. En navegador local, con doce registros temporales, se comprobó el paso a la segunda página conservando la selección.

Sin commits, push ni despliegue. La selección se conserva durante las acciones del formulario; abandonar la pantalla e iniciar de nuevo no guarda un borrador.

## Actualización: selector compartido en crear y editar proyecto — 05/11/2026

- Se reutiliza el parcial común `optimization-plan-selector.html` y su JavaScript de búsqueda/paginación para crear y editar proyectos. El selector de presupuestos también usa el mismo parcial; el título y los textos de ayuda se parametrizan por contexto.
- En los formularios de proyecto, búsqueda y paginación son locales al navegador, muestran seis filas por página y no envían ni reinician el resto del formulario. Todas las casillas permanecen en el DOM: las marcadas en páginas anteriores siguen contándose y se envían junto con las visibles.
- El contador muestra la selección total y, al editar, parte de las optimizaciones ya asociadas marcadas. El filtrado busca nombre, código permanente OPT y contenido de piezas; estas últimas ya no se presentan como chips.
- La tabla en proyectos usa columnas de identidad/fecha, tablero, aprovechamiento, tableros y consulta. «Ver resultado» abre otra pestaña con `rel="noopener"`; en móvil las filas pasan a tarjetas. El estado de carga mantiene la altura del bloque.
- El POST, el campo `optimizaciones`, la validación de propietario/disponibilidad y las operaciones de guardar siguen siendo los existentes. No se cambia el modelo ni los datos.

Verificación de esta actualización: pruebas de crear/editar proyecto y presupuesto aprobadas; en navegador se verificó selección entre páginas y filtros, guardado de todas las marcadas, preselección al editar y presentación móvil/intermedia. Suite de gestión, permisos y navegación: 41 pruebas aprobadas.
