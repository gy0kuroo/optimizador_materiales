# Indicador de carga con el símbolo de CutLess

Fecha: 25 de octubre de 2026.

## Cambio visual

Se reemplaza el círculo giratorio genérico por el símbolo de CutLess. El logo permanece fijo y sus cinco piezas se resaltan por turno en azul, conservando los colores originales entre pasos. La secuencia recorre la pieza izquierda, superior, derecha, inferior y central; se repite cada 1,6 segundos. No representa un porcentaje de avance ni etapas reales del algoritmo.

El símbolo y el mensaje aparecen centrados directamente sobre la pantalla oscurecida y desenfocada, sin tarjeta, borde ni sombra de contenedor. Se elimina también el fondo claro del SVG, dejando únicamente las cinco piezas animadas. El texto se muestra en blanco tanto en modo claro como oscuro, conserva la tipografía existente y se adapta a pantallas pequeñas y texto grande. El SVG usa la misma geometría de piezas que `brand-symbol.svg`, sin cargar imágenes externas ni generar una marca nueva.

El logo se amplía a 1,5 veces su tamaño inicial: de 144 a 216 px de ancho. Se mantiene `max-width:100%` para que se ajuste en pantallas pequeñas; el tamaño del texto no cambia.

## Integración

- La plantilla compartida `includes/loading.html` se incorpora a `base.html` y `loading.css` define su presentación y animación.
- `mostrarIndicadorCarga` clona esta plantilla y coloca el mensaje mediante `textContent`, conservando el contenido como texto.
- Se mantiene la función `ocultarIndicadorCarga`, su retirada tras las descargas y el temporizador de seguridad existente de 15 segundos.
- Se aplica a la generación de planes y a las descargas que ya utilizaban el indicador global. Se incorpora también a la actualización de una optimización mediante el mismo evento de envío de formulario.
- Los procesos del servidor, las validaciones, los datos y los archivos descargados no cambian. No se introduce un tiempo mínimo de espera para mostrar la animación.

## Accesibilidad

El mensaje se anuncia con `role="status"`, `aria-live="polite"` y `aria-atomic="true"`. El dibujo es decorativo y se oculta a los lectores de pantalla. Con `prefers-reduced-motion: reduce` se muestra el símbolo estático y se conserva el mensaje. El indicador no se imprime.

## Verificación

- La versión inicial con tarjeta se comprobó visualmente en navegador, en modo claro y oscuro y a un ancho reducido. Posteriormente se retiraron la tarjeta y el fondo del SVG a petición del usuario; el texto pasa a blanco y se actualiza la versión de la hoja de estilos para evitar la caché anterior.
- Comprobación de las cinco piezas y sus desfases de 0; 0,32; 0,64; 0,96 y 1,28 segundos.
- Verificada la retirada automática del indicador después del temporizador existente.
- **21 pruebas de Django aprobadas**: vistas, persistencia y revisión de usabilidad. Base de datos y archivos de prueba aislados de los datos de trabajo.
- Compilación de las plantillas afectadas, sintaxis de `confirmaciones.js` y comprobación del diff sin incidencias.

La vista temporal se cerró al terminar. Versión final aprobada por el usuario: logo de 216 px, sin tarjeta ni fondo del símbolo, con texto blanco sobre la pantalla oscurecida. Se publica como mejora visual junto con su documentación; los datos locales y pendientes de otras tareas quedan fuera del commit.
