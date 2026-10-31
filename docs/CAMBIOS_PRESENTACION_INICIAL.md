# Presentación inicial sin reconstrucción tardía del selector

Fecha: 31 de octubre de 2026.

## Causas confirmadas en el código

El contenedor de medidas habituales llegaba vacío en el HTML. medidas-pred.js creaba después su etiqueta, botón, opciones y ayuda, con esperas de inicialización. Mientras tanto, Unidad de medida aparecía más arriba; al insertarse el bloque, se desplazaba. No era necesario cargar una versión antigua del programa para que se viera esa transición.

Además, base.html siempre comenzaba con data-theme=light y aplicaba la preferencia del usuario posteriormente. Esto permitía mostrar el tema claro antes del oscuro.

## Corrección

- El servidor renderiza la estructura final de medidas habituales en una plantilla compartida incluida en inicio. El catálogo de seis opciones se obtiene del formulario, convertido a la unidad inicial, sin ceros decimales innecesarios.
- JavaScript lee las opciones ya presentes y conecta sus eventos. No vacía ni reconstruye el contenedor ni retrasa su aparición para esperar Bootstrap. Se conservan los identificadores del tutorial, selección, conversión y asociación de material/precio.
- El catálogo ya no está duplicado como una lista fija en JavaScript: los valores base se leen de los atributos del HTML.
- El perfil oscuro se incluye en el atributo inicial del documento. Un script pequeño en head resuelve tema de perfil, preferencia local o sistema antes de cargar los estilos y mostrar el contenido. El perfil autenticado prevalece, incluida su opción Automático. Se contempla almacenamiento local no disponible o valores inválidos.
- No se oculta el contenido ni se añade una pantalla de carga para disimular el cambio. No se alteran datos, algoritmos ni preferencias guardadas. El controlador habitual de tema sigue gestionando los cambios posteriores.

## Verificación

- 197 pruebas Django aprobadas, incluidas cuatro nuevas de HTML inicial, catálogo, unidad del perfil y tema.
- Dos pruebas JavaScript del tema inicial aprobadas: perfil claro/oscuro/automático, preferencias guardadas, sistema y almacenamiento bloqueado. Sintaxis y diff sin errores.
- En una copia SQLite temporal y navegador: perfil oscuro, un solo selector y seis opciones; selección de OSB rellena 122 × 244 cm; las opciones se convierten a metros y seleccionar OSB rellena 1,22 × 2,44 m sin error de validación.
- La presencia de la estructura antes de JavaScript y del tema antes de CSS se verifica en las pruebas de HTML. No se midieron fotogramas del primer pintado ni tiempos de red de Render; queda la revisión visual del usuario en su entorno habitual.
- Se cerraron la pestaña y los servidores temporales. No se utilizó Supabase ni se cambió la web publicada.

Sin commit, push ni despliegue. El cambio de fondo de tableros por tema documentado en CAMBIOS_FONDO_TABLEROS_TEMA.md continúa como otro cambio local pendiente.

## Publicación del bloque visual

Publicación autorizada el 31 de octubre de 2026. Verificación final conjunta: 203 pruebas Django y 14 pruebas JavaScript aprobadas; collectstatic de producción completado en carpeta temporal sin conectar a PostgreSQL. Las menciones anteriores a cambios locales describen el estado previo a esta autorización. No se ejecutan migraciones ni se cambia la configuración remota.
