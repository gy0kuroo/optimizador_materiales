# Revisión visual de historial y resultado

Estado: bloque autorizado por el usuario para publicación en GitHub. Cabecera del historial revisada y aprobada visualmente.

## Historial

Tras la revisión de la cabecera, se elimina su línea inferior, se agrupan las acciones a la derecha y se da al botón de ayuda fondo neutro y borde visible. En móvil las acciones se colocan debajo del título y descripción. El ajuste se limita al historial; se actualiza la versión de caché de su hoja de estilos.

Conserva su nombre, filtros, orden, favoritos y acciones existentes. Las tarjetas incorporan Ver resultado como acceso visible al plan, por encima de editar y duplicar. Se aclaran fechas, selección, filtros y acciones. El estado vacío considera también el filtro de favoritos para no sugerir que no existen registros cuando no hay coincidencias.

Filtros y tarjetas usan superficies de la paleta actual, texto general de 1.125rem y controles principales de mínimo 48 px. Los checkboxes usan 24 px para evitar deformaciones. Los selects cambian de fondo al pasar el cursor. Las acciones permiten envolver en pantallas estrechas.

## Resultado

El resumen usa tarjetas neutras y cifras destacadas, reservando colores de estado para los indicadores por tablero. Los encabezados, botones, tablas y descargas siguen la tipografía del inicio. Se reparan los colores de las barras que dependían de variables antiguas. La tabla permite desplazamiento horizontal en móvil.

Distribución de las piezas explica cómo ampliar y descargar imágenes; las descargas se agrupan bajo Guardar o imprimir el resultado. Imprimir avisa que abre otra pestaña. Las imágenes, datos, cálculos y rutas se conservan.

## Archivos y alcance

Se modifican historial.html y resultado.html y se añade history-result-refinement.css. Las reglas se limitan a review-page, history-page y result-page para no cambiar otras listas que comparten historial.css. No se modifican modelos, algoritmo, persistencia ni permisos.

## Validación

Las dos plantillas compilan. Pasaron las 86 pruebas de cutless.tests y usuarios.tests con base de pruebas y archivos temporales; Django check no informó problemas. El ajuste posterior de cabecera se revisó con el usuario y pasó git diff --check. La revisión exhaustiva de móvil, oscuro, menús y gráficos ampliados sigue pendiente. No se ha realizado una auditoría completa de accesibilidad.

Los cambios locales previos de la base de datos, PDFs y CAMBIOS_AREAS.md quedan fuera de este bloque.
