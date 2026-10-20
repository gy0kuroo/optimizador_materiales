# Sistema compartido de botones

Fecha: 20 de octubre de 2026. Bloque revisado y aprobado por el usuario para publicación.

## Alcance

Se unifican los botones de Inicio, Historial, Gestión, Análisis, Ayuda, Cuenta, acceso/registro, bienvenida, administración, formularios, modales y vista previa de impresión. Se conservan los destinos, parámetros, nombres de campos y acciones del servidor.

Los colores son idénticos en claro y oscuro, como se solicitó. Los siete tokens están definidos únicamente en `cut/cutless/static/cutless/css/buttons.css`:

| Token | Valor | Significado |
| --- | --- | --- |
| `--btn-primary` | `#4558E7` | Avanzar y acción principal |
| `--btn-primary-dark` | `#1E287B` | Hover del primario |
| `--btn-brand` | `#4E2D01` | Texto de apoyo |
| `--btn-brand-soft` | `#7D6344` | Iconos secundarios |
| `--btn-neutral` | `#B7B8AB` | Bordes y deshabilitados |
| `--btn-success` | `#156548` | Guardar y confirmar |
| `--btn-danger` | `#8b2635` | Eliminar y acciones destructivas |

El blanco de contraste y los estados atenuados se derivan en esta misma hoja. La variante de ayuda usa una superficie neutra clara también en oscuro para mantener el mismo color y un texto legible; no incorpora una paleta alternativa por tema.

## Clases, iconos y estados

- Clases base: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-success`, `.btn-danger`, `.btn-text`, `.btn-icon` y `.btn-sm`.
- Altura normal 44 px, pequeña 34 px; radio de 11 px, texto de 14 px y peso 600. Se mantiene la familia Barlow. Los controles de solo icono conservan su nombre accesible.
- Iconos SVG locales de trazo uniforme, 18 px y separación de 8 px. Reutilización mediante `button-icons.svg`, sin nueva librería o dependencia externa.
- Sombra y transición de 150 ms; elevación de 1 px al pasar el cursor, foco visible de 3 px y estados deshabilitados sin movimiento ni sombra.
- Éxito y peligro se oscurecen con `brightness(.88)`, sin añadir colores.
- `data-action` declara el significado. `data-icon` identifica el icono. La semántica no se deduce de los textos durante la ejecución.
- Los botones dinámicos y los del recorrido de ayuda reciben el mismo sistema. Los controles de navegación y pestañas conservan sus funciones. Las superficies clicables que contienen planos o gráficos mantienen su geometría, evitando convertirlas en botones pequeños.

Se retiraron declaraciones visuales duplicadas de las hojas anteriores, conservando reglas de disposición de las pantallas y de sus campos.

## Cambios de disposición y presentación autorizados

- Guardados y confirmaciones aparecen en verde; eliminaciones y su confirmación final en rojo.
- Cancelar/volver queda a la izquierda de la acción principal en los formularios; las acciones destructivas mantienen separación visual.
- PDF, Excel e Imprimir comparten una barra: PDF es la acción azul, las otras son secundarias. «Otra pestaña» pasa del texto visible a la ayuda del enlace; se conserva `target="_blank"`.
- Descargar PNG queda en el encabezado «Distribución del tablero», a la derecha. Se retira la franja que duplicaba el número del tablero.
- Navegación compacta con flechas SVG y un solo indicador «Tablero X de N». Se conserva la navegación anterior, sus límites y la sincronización con los visores.
- Los formularios destructivos declaran `data-confirm-delete` y utilizan el diálogo compartido antes de enviar. El botón final utiliza peligro. Cancelar no envía el formulario.

## Estado de carga

`buttons.js` añade el spinner, conserva el ancho del control, marca `aria-busy`, bloquea repeticiones y restaura icono/estado al finalizar. Las descargas se integran con la función existente de descarga y mantienen sus rutas y archivos.

En formularios se espera a que terminen la validación y la serialización antes de deshabilitar el botón, para conservar los valores del envío. Volver mediante la caché del navegador restaura los controles. Los errores de descarga conservan el aviso existente y restauran el botón mediante `finally`.

## Validación

- Suite completa: **137 pruebas correctas**; comprobación de Django sin incidencias.
- Las 53 plantillas compilan y los scripts modificados pasan la comprobación de sintaxis.
- Revisión real de resultado, navegación de tableros, botones de formulario y confirmación destructiva cancelada.
- Medidas comprobadas: botones de 44 px, fuente de 14 px, iconos de 18 px; guardar en `rgb(21,101,72)` y confirmar eliminación en `rgb(139,38,53)`.
- Descarga PDF real en el entorno temporal: spinner y bloqueo visibles, ancho constante de 154,6875 px durante y después de la descarga, e icono/estado restaurados. Se añadió una demora únicamente al servidor de revisión, sin incorporarla al proyecto.
- Comparación del primario en claro y oscuro: mismo fondo `rgb(69,88,231)`, texto de contraste, fuente y altura.
- Vista móvil de 390 px sin desbordamiento horizontal de la página de resultados.

La revisión visual no cubre exhaustivamente todos los contenidos y navegadores. Los datos y archivos locales del usuario no forman parte de este bloque. Este bloque continúa la reforma general publicada en `07c64f9` y se publica con la autorización del usuario.

## Ajuste: Inicio e Historial en el menú

Se incorporan los enlaces Inicio e Historial al mismo sistema de botones secundarios del menú. La sección activa utiliza el azul primario, sin cambiar las rutas ni convertir los enlaces en controles de formulario. Comparten altura, tipografía, bordes e iconos con los demás controles de navegación.
