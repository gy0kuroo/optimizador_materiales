# Fondo de los tableros según el tema

Fecha: 31 de octubre de 2026.

El fondo claro del tablero SVG permanecía fijo aunque la interfaz estuviera en modo oscuro. Se identifican por clases la superficie del tablero, el rayado del sobrante y sus etiquetas para aplicar colores del tema sin modificar las piezas.

En modo oscuro, la superficie usa surface-subtle, el rayado text-secondary y las etiquetas text. En modo claro se mantienen los colores originales. Las piezas conservan sus colores y textos; no se invierte ni se filtra la imagen completa. El cambio se adapta al tema mediante CSS, sin recalcular la distribución ni guardar una versión distinta por usuario.

La plantilla SVG es compartida por resultados, miniaturas del historial y visores. Las exportaciones PDF y PNG utilizan sus generadores propios y no se modifican; la impresión mantiene explícitamente la superficie clara, incluso desde modo oscuro. Los resultados históricos que solo tengan una imagen rasterizada y carezcan de geometría no reciben este cambio: no se altera su imagen mediante filtros.

Se actualiza la versión de theme-colors.css para evitar caché antigua. Siete pruebas de historial horizontal y presentación aprobadas con base y archivos de pruebas aislados. Diff sin errores. No se realizó una nueva revisión visual en navegador para esta modificación.

Sin commit, push ni despliegue.

## Paginación desactivada en modo oscuro

Los controles Primera/Anterior en la primera página (y Siguiente/Última en la última) conservaban el fondo claro predeterminado de Bootstrap. Se añade una regla compartida para el estado disabled de la paginación: superficie tenue, texto atenuado y borde del tema activo. Se aplica tanto a span dentro de page-item.disabled como a page-link.disabled. No se modifican destinos, filtros ni el estado activo de la página.

La versión de theme-colors.css pasa a 4. Diff sin incidencias; cambio exclusivamente CSS, sin pruebas nuevas ni nueva revisión visual en navegador. Continúa local, sin commit ni despliegue.

## Publicación del bloque visual

Publicación autorizada el 31 de octubre de 2026. Verificación final conjunta: 203 pruebas Django y 14 pruebas JavaScript aprobadas; collectstatic de producción completado en carpeta temporal sin conectar a PostgreSQL. Las menciones anteriores a cambios locales describen el estado previo a esta autorización. No se ejecutan migraciones ni se cambia la configuración remota.
