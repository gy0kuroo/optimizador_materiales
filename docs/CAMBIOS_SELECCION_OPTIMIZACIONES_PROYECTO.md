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
