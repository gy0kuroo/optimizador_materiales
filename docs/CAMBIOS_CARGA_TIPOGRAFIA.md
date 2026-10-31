# Carga estable de tipografía

Fecha: 31 de octubre de 2026.

## Causas

main.css importaba Barlow y JetBrains Mono desde Google Fonts con display=swap. El navegador podía mostrar una fuente provisional antes de terminar esas peticiones externas, y sustituirla posteriormente. Por separado, theme.js aplicaba el tamaño personalizado en DOMContentLoaded, después de poder haberse mostrado el tamaño normal.

## Corrección

- Se conservan las familias originales Barlow (400, 500, 600, 700 y 800) y JetBrains Mono (400 y 500), con los subconjuntos publicados por Google Fonts. No se redibujan ni modifican glifos.
- Los 21 archivos WOFF2 únicos se alojan en los estáticos de CutLess, junto con las licencias OFL y su procedencia. Tamaño total aproximado de los binarios: 285 KiB; unicode-range limita las descargas a los subconjuntos necesarios.
- fonts.css define sus variantes locales y se carga antes de main.css en las páginas basadas en base.html. Se precargan los cinco pesos latinos de Barlow desde el mismo origen. Se retira la importación externa de main.css y se actualiza su versión de caché.
- font-display: optional evita sustituir tardíamente la fuente provisional. Con caché vacía y una conexión demasiado lenta, puede mantenerse la alternativa durante esa página; no se oculta el texto ni se promete la fuente personalizada desde el primer fotograma bajo cualquier condición de red. La precarga y el alojamiento local favorecen su disponibilidad temprana.
- El script inicial de head aplica también el tamaño elegido antes de los estilos y del contenido. Usa los mismos valores que el controlador existente: 15, 16, 18 y 20 px. Prevalece el perfil autenticado; sin perfil, se utiliza la preferencia local y se contempla almacenamiento bloqueado o valores inválidos.
- No se cambian las preferencias guardadas, cálculos ni exportaciones. La vista independiente de impresión mantiene su hoja print-preview-shell.css anterior; esta corrección se aplica al inicio y demás pantallas que comparten base.html.

## Verificación

- 31 pruebas Django de presentación inicial y usuarios aprobadas sobre base de pruebas y archivos temporales.
- Tres pruebas JavaScript del script inicial aprobadas: tema y tamaño de perfil, preferencia local, sistema y almacenamiento no disponible.
- Caracteres áéíóúñÑ¿¡ disponibles en los WOFF2 latinos, comprobados mediante fontTools.
- collectstatic completo con DEBUG=False en carpeta temporal: manifiesto y todas las referencias CSS de fuentes con hash válidas. No se abre una conexión PostgreSQL.
- Las reglas locales de fuentes no requieren conexiones a Google al navegar; los enlaces de procedencia no se solicitan como recursos de la página.
- Diff sin incidencias. No se midió el primer pintado en Render ni se realizó una revisión visual en navegador de esta ampliación.

Sin commit, push ni despliegue. Se mantienen pendientes los cambios locales de presentación inicial y fondo de tableros documentados por separado.

## Publicación del bloque visual

Publicación autorizada el 31 de octubre de 2026. Verificación final conjunta: 203 pruebas Django y 14 pruebas JavaScript aprobadas; collectstatic de producción completado en carpeta temporal sin conectar a PostgreSQL. Las menciones anteriores a cambios locales describen el estado previo a esta autorización. No se ejecutan migraciones ni se cambia la configuración remota.
