# Texto e iconos presentes desde el HTML inicial

Fecha: 31 de octubre de 2026.

## Revisión

Se revisaron fotogramas del vídeo proporcionado y los mecanismos de renderizado. El ejemplo explicativo junto a Unidad de medida todavía se creaba mediante JavaScript, lo que podía desplazar los campos al incorporarse. Los iconos de Ayuda se añadían mediante buttons.js; el logo y los iconos de las secciones requerían descargar imágenes después del HTML.

## Corrección

- El ejemplo de unidad se genera desde TableroForm y se incluye en el HTML de inicio y edición. dimension-feedback.js actualiza ese elemento al cambiar la unidad, sin crearlo ni insertar una copia nueva. Los símbolos iniciales de unidad en tablero y piezas también se renderizan según el formulario.
- Los iconos de los botones de inicio se incluyen como SVG en el servidor usando las mismas figuras de button-icons.svg. Conservan su clase y data-icon; el controlador existente los reconoce y no los duplica. Los botones dinámicos de otras pantallas mantienen su comportamiento anterior.
- El logo compartido se incrusta como SVG, conservando los colores y la geometría del archivo original. Los iconos de inicio se incluyen igualmente en el HTML, sin peticiones adicionales para esos recursos.
- Los PNG decorativos se preparan en memoria a doble resolución de su tamaño de presentación para no incrustar originales grandes por cada fila. Los archivos originales no se modifican. El icono de pieza de 20 px ocupa aproximadamente 1,4 KB en base64, frente a unos 13 KB si se incrustara el original sin reducirlo.
- La biblioteca de plantillas admite únicamente una lista explícita de recursos decorativos propios. No permite leer rutas arbitrarias ni archivos de configuración.
- Se conserva el espacio de los iconos mediante dimensiones y estilos. Se actualizan las versiones del JavaScript de validación y de la hoja de refinamiento para evitar copias antiguas en caché.

No se oculta la página ni se añaden esperas de carga. No se modifican cálculos, datos ni funcionalidades de ayuda, eliminación o adición de piezas. Continúa aplicándose la política de fuentes locales y precarga documentada por separado.

## Verificación

- Suite completa: 199 pruebas Django aprobadas con base SQLite y archivos temporales.
- Ocho pruebas JavaScript aprobadas: cinco de validación y tres de tema/tamaño inicial.
- Pruebas de HTML confirman la ayuda inicial, logo SVG y dos iconos Ayuda; se comprueba también el rechazo de rutas arbitrarias.
- En navegador con copia SQLite temporal: modo oscuro, logo visible, dos botones Ayuda con un icono cada uno; añadir una pieza conserva un icono Eliminar por fila. Cambiar a metros mantiene un solo ejemplo de unidad y actualiza su texto correctamente.
- La inclusión antes de ejecutar JavaScript se verifica mediante las pruebas del HTML. No se ha medido cada fotograma del primer pintado en todos los navegadores ni en Render; queda la revisión visual del usuario.
- Pestaña y servidor temporales cerrados. Sin uso de Supabase ni modificación de datos reales. Sintaxis y diff sin incidencias.

Sin commit, push ni despliegue.

## Ajustes finales: ejemplos de entrada y lupa

Los ejemplos de ancho y alto del tablero se generan ahora desde el formulario con el mismo formato que JavaScript: «Ej.: 122», «Ej.: 244», o los valores de la unidad elegida. Se elimina la diferencia inicial «Ej:» frente a «Ej.:» y la conversión tardía del ejemplo al cargar una unidad distinta de cm. El HTML manual del inicio utiliza el atributo del campo, como ya hace edición.

El botón de lupa y sus controles incluyen sus iconos SVG en el HTML inicial. El decorador de botones los reconoce por data-icon y no los sustituye ni añade después. Se conserva la exclusión de la lupa en móvil y dentro de diálogos de confirmación; no se cambia su funcionamiento.

Verificación: 18 pruebas Django de presentación y medidas aprobadas; tres pruebas JavaScript de tema/tamaño y seis de disponibilidad de lupa aprobadas. Se añadieron regresiones para el formato inicial de los ejemplos y la presencia del icono de lupa antes de ejecutar JavaScript. Diff sin errores. No se repitió la revisión visual en navegador para este ajuste. Continúa sin commit ni despliegue.

## Historial

Se extiende el renderizado inicial de iconos a las acciones del historial: favoritos, seleccionar todos, quitar selección, preparar otro corte, búsqueda, eliminación, ver resultado, editar, duplicar, más opciones y controles del visor. Las figuras son las mismas del sprite existente; buttons.js las reconoce y no las incorpora tardíamente.

Favoritos también incluye desde el servidor su clase btn-icon y nombre accesible según el estado, evitando un ajuste posterior de su presentación. Se mantienen los atributos de estado, el cambio de favorito por AJAX y la selección múltiple. El indicador antiguo oculto se conserva por compatibilidad con el controlador existente.

Siete pruebas Django de historial aprobadas, incluidas dos nuevas: presencia de iconos en el HTML inicial y conservación/actualización del estado de favorito. Se utilizó base de pruebas y archivos temporales, sin conectar a Supabase. Diff sin errores; sin nueva revisión visual en navegador. Cambios solo locales, sin commit ni despliegue.

## Publicación del bloque visual

Publicación autorizada el 31 de octubre de 2026. Verificación final conjunta: 203 pruebas Django y 14 pruebas JavaScript aprobadas; collectstatic de producción completado en carpeta temporal sin conectar a PostgreSQL. Las menciones anteriores a cambios locales describen el estado previo a esta autorización. No se ejecutan migraciones ni se cambia la configuración remota.
