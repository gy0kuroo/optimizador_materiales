# Skeleton durante generación de optimizaciones — 31/10/2026

## Objetivo
Acompañar la espera real de cálculos grandes, como veinte tipos de 25 × 25 cm y cinco unidades de cada uno (cien piezas).

## Cambios
- Crear, duplicar y actualizar optimizaciones utilizan una pantalla de espera con la estructura del resultado: aprovechamiento total, tablero, resumen, tabla y detalles técnicos.
- Reutiliza los skeletons del visor con onda y pulso suaves, paleta claro/oscuro y adaptación a móvil. Respeta movimiento reducido.
- Muestra la cantidad de piezas y tipos solicitados, no un porcentaje de avance ni una distribución provisional.
- Conserva el POST nativo y el cálculo existente; no agrega AJAX, solicitudes repetidas, reintentos automáticos ni demoras artificiales.
- Se activa después de la validación del envío. Mientras espera, evita otra interacción con formulario/navegación de la página y bloquea un segundo envío; los campos no se deshabilitan ni se excluyen de la solicitud.
- A los veinte segundos cambia la explicación, sin retirar el skeleton ni afirmar que el servidor haya terminado. El indicador anterior se ocultaba a los quince segundos aunque el envío siguiera pendiente; esa regla no se aplica a esta nueva espera.
- Al volver mediante historial o salir de la página se limpian el estado y el temporizador, restaurando la accesibilidad previa.
- El spinner de marca de descargas y demás operaciones conserva su comportamiento.

## Diferencia con el visor
Durante una optimización nueva los datos del plan llegan juntos al terminar el cálculo. Los bloques del skeleton permanecen pendientes hasta la respuesta; no se simulan etapas ni se revelan resultados parciales inexistentes. Esto mejora la comunicación de la espera, no el tiempo de ejecución del algoritmo.

## Verificación
- **246 pruebas Django y 6 pruebas JavaScript aprobadas**.
- JavaScript: cien piezas/veinte tipos, prevención de duplicados, envío cancelado por validación, aviso de espera larga y restauración al regresar por historial.
- Navegador sobre copia temporal: caso real de veinte tipos, 25 × 25 cm y cinco unidades cada uno; el envío llega al resultado con tres tableros y cien piezas. Se capturó la pantalla de espera durante el POST.
- Para observar el diseño se añadió una pausa de cinco segundos en middleware solo en memoria del servidor temporal. No se guarda ni publica esa pausa y no se utiliza como medición de rendimiento.
- Sin migraciones, dependencias nuevas ni cambios en el algoritmo o en Supabase. Sintaxis JavaScript y `git diff --check` sin errores.

## Revisión en producción
Generar el mismo caso desde Inicio, comprobar el contador de cien piezas y que aparezca el resultado al terminar. Probar también un formulario inválido: debe mostrar la corrección sin bloquearse con un skeleton. El tiempo real depende del servidor y la carga; no se fuerza una duración mínima para que el usuario vea la animación.

## Skeleton completo y transición al resultado

Inventario revisado en `resultado.html`, `board-layout.html` y los avisos de `base.html`:

| Zona | Representación durante la espera |
| --- | --- |
| Aviso de confirmación | Barra placeholder, sin afirmar éxito antes de recibir respuesta |
| Encabezado | Título fijo, código pendiente y cinco botones placeholder |
| Aprovechamiento total | Dona, título y dos líneas pendientes |
| Distribución de las piezas | Título, subtítulo y navegación pendiente |
| Dibujo | Título, descarga PNG pendiente, cota y bloques de piezas, enlace inferior |
| Resumen del corte | Dona, seis celdas y nota pendiente |
| Detalle de piezas | Seis columnas, filas de ejemplo y nota pendiente |
| Detalles técnicos | Cinco etiquetas fijas y valores pendientes |
| Resumen de todos los tableros | Barra cerrada con título y flecha; no se dibuja su tabla interior |
| Costos | Solo si precio o mano de obra lo requieren; material, precio, mano de obra, total y presupuesto según condiciones |
| Acciones finales | Dos botones pendientes |

- Un parcial compartido mantiene la misma representación durante el POST y sobre las tarjetas reales del resultado. Los overlays iniciales se renderizan desde Django para evitar un fotograma vacío antes de ejecutar JavaScript.
- Revelado de arriba hacia abajo: aviso/encabezado, aprovechamiento, navegación, dibujo/resumen, piezas/detalles, plegable, costos y acciones. Intervalos de 85 ms y transiciones de 270 ms: menos de un segundo. En pantallas apiladas se presentan las piezas antes del resumen.
- La respuesta conserva las dimensiones reales de cada tarjeta; los placeholders son capas sin participación en el flujo. Antes de recibir los datos no se conocen las filas ni las dimensiones exactas de todas las tarjetas, por lo que el skeleton del POST usa tamaños aproximados.
- Solo se anima el primer tablero al llegar desde un envío. Abrir desde historial, navegar entre tableros, exportar e imprimir mantienen su comportamiento.
- No cambia cálculos, persistencia ni solicitudes. Respeta movimiento reducido; foco, errores de presentación y navegación restauran la visibilidad. Existe un fallback de 2,5 s si no termina de inicializarse el script.
- Los costos siguen las condiciones reales: mano de obra sin precio puede mostrar su bloque sin mostrar total; precio cero con mano de obra puede tener total. El código OPT y número de tableros permanecen pendientes hasta recibir la respuesta.

### Verificación de esta ampliación
- 247 pruebas Django aprobadas sobre base de pruebas aislada.
- 14 pruebas JavaScript: espera y duplicados, condiciones de costos, orden escritorio/móvil, duración, limpieza y movimiento reducido.
- Revisión de navegador sobre datos sintéticos, sin Supabase ni datos de usuarios. Sin nuevas dependencias ni migraciones.

## Ajuste de costos y recarga
Los placeholders de costos adoptan la cuadrícula compacta del resultado y las acciones finales incluyen su propio encabezado. El envío termina en una redirección al resultado guardado, manteniendo la marca de transición entre páginas. Detalles y pruebas en `CAMBIOS_RESULTADO_RECARGA_Y_COSTOS.md`.
