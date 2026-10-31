# Carga progresiva y skeletons del visor del historial — 31/10/2026

## Problema
El visor solicitaba todos los tableros, generaba sus PNG en el servidor y recibía también HTML con SVG. El navegador esperaba la respuesta completa mostrando una zona vacía, aunque terminaba usando SVG.

## Implementación
- Nuevo modo compatible del endpoint existente: `?modo=visor&presentacion=horizontal&tablero=N`.
- Para resultados con geometría persistida devuelve únicamente el HTML/SVG del tablero solicitado y el total de tableros; no genera PNG, no ejecuta el algoritmo ni modifica registros.
- Los totales del plan completo se conservan al preparar un único tablero. El modo anterior de la API y las descargas PDF/PNG/Excel siguen disponibles.
- Skeletons inmediatos para dibujo, tabla, resumen y detalles; pulso suave y onda izquierda a derecha con colores del tema. Se reserva espacio sin presentar porcentajes provisionales como datos reales.
- Tras recibir la respuesta se muestra primero el dibujo; se cede un pintado del navegador antes de insertar resumen y luego detalle/tabla. No hay temporizadores para simular una espera ni solicitudes separadas por cada tarjeta.
- El aprovechamiento anima el círculo desde cero al abrir el visor y entre valores al cambiar de tablero. El texto muestra el porcentaje real. Se respeta `prefers-reduced-motion`.
- Precarga solo el siguiente tablero y reutiliza los consultados durante esa apertura. Cerrar cancela solicitudes, descarta caché y evita que respuestas antiguas sustituyan la selección actual.
- Los fallos retiran el skeleton y ofrecen reintento; una sesión no disponible ofrece acceso al login. No se usa silenciosamente una miniatura como si fuera el resultado completo.
- Los resultados antiguos sin coordenadas mantienen la lectura de compatibilidad anterior. Ese recorrido puede ser más lento; un registro sin resultado persistido conserva el comportamiento previo de generación inicial.

## Alcance
Este piloto afecta al visor ampliado del historial. El visor de resultados ya dispone del dibujo en el HTML y no hace esa consulta; su carga inicial sigue siendo otro recorrido. Los estilos de skeleton se pueden reutilizar, pero no se han aplicado indiscriminadamente a toda la aplicación. La base todavía se consulta y la geometría del plan vive en el JSON existente; no se garantiza eliminar todos los tiempos de red, consultas o arranque de Render.

## Verificación
- **244 pruebas Django aprobadas**, incluyendo consulta individual, totales, ausencia de generación PNG/reoptimización, propietario, números inválidos, skeletons y compatibilidad con la API anterior.
- Sintaxis de los scripts y `git diff --check` sin errores.
- Navegador local con una copia temporal de datos: skeletons, carga posterior, precarga y navegación. Se introdujo una demora artificial de cinco segundos mediante middleware solo en memoria para observar la espera; no forma parte del código publicado.
- Sin migraciones, dependencias nuevas ni cambios en datos de Supabase.

## Revisión en producción
Abrir una optimización desde la miniatura del historial, comprobar los placeholders y el primer tablero, recorrer siguientes/anteriores y cerrar/reabrir. Comparar el tiempo real con el anterior bajo las mismas condiciones; no interpretar la prueba local con demora artificial como medición de rendimiento de Render.
