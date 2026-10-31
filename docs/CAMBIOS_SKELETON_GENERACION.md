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
