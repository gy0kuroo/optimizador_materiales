# Menú móvil y lupa reservada a escritorio

Fecha: 29 de octubre de 2026.

## Menú plegable

En anchos inferiores a 1200 px, abrir la navegación inmoviliza el fondo y conserva su posición. Las opciones del menú tienen su propio desplazamiento, con contención para evitar que el gesto pase al fondo. Los submenús se despliegan dentro de ese espacio. El contenido de la página queda temporalmente fuera de la interacción y del foco mediante `inert`.

Al terminar el cierre, se recuperan la posición de lectura y el estado de interacción anterior. Escape cierra el menú. Seguir un enlace o abrir la ayuda también lo cierra. Cambiar al ancho de escritorio libera el bloqueo, incluso si el menú estaba abierto. Las reglas de disposición del menú se limitan al punto de corte móvil existente.

El comportamiento se comparte mediante `mobile-navigation.js` y `mobile-navigation.css`, sin modificar rutas, opciones, permisos ni preferencias.

## Lupa: solo escritorio

La adaptación táctil inicial se retiró después de que el usuario la probara en teléfono y reportara mal funcionamiento. La solución final oculta y desactiva completamente la lupa en la vista plegable (menos de 1200 px) y en dispositivos con puntero táctil principal sin hover. Se aplica también dentro de los visores de tableros y gráficos.

En móvil se mantiene el zoom nativo del navegador con dos dedos. No se añaden restricciones de zoom a la etiqueta viewport ni se interceptan gestos táctiles.

En escritorio, con ancho normal y ratón, la lupa conserva su seguimiento del cursor. Si se reduce la ventana a vista móvil con la lupa activa, se apaga, se retira la lente y se recupera el cursor. Al volver a escritorio se muestra el botón, sin activar la ampliación automáticamente.

Abrir la navegación oculta y desactiva la lupa. Se mantienen las restricciones para confirmaciones, carga y tutoriales.

## Verificación

Sobre una copia temporal de datos y navegador con vista de **390 × 844 px**:

- Menú abierto desde una posición de 2048 px: fondo fijado con desplazamiento de -2048 px, desplazamiento de ventana bloqueado y opciones con `overflow-y: auto`.
- Al cerrar, se recuperan exactamente los 2048 px.
- La primera prueba de una ventana de lupa fija en móvil fue descartada tras la revisión en teléfono del usuario.
- Abrir el menú con la lupa activa oculta controles y lente y recupera el cursor.

Al cambiar a **1280 × 900 px**, desaparecen el bloqueo y el estado `inert`; el cuerpo vuelve a su posición normal. Se verifica que la lupa de escritorio permanece activa al enfocar el campo y conserva su comportamiento de cursor.

Pruebas automatizadas: **175 de Django aprobadas**; cuatro de navegación móvil; seis de compatibilidad de la lupa con paneles y su exclusión en móvil y tres de filas de piezas, todas aprobadas. Las seis pruebas de lupa se repitieron tras retirar la adaptación táctil. Sintaxis y diff sin incidencias. Las pruebas usan archivos y base de datos aislados de los datos reales.

La revisión inicial del menú fue mediante cambio de tamaño de navegador. La lupa móvil se eliminó después de la prueba del usuario en teléfono. No sustituye la comprobación en un teléfono físico: los gestos táctiles y el teclado virtual propios de Android/iOS quedan pendientes de esa revisión. No se afirma haber probado todos los navegadores móviles.

Se restauró el tamaño normal del navegador y se cerraron los recursos temporales. Publicación autorizada el 30 de octubre de 2026 junto con la corrección del foco en las filas de piezas.
