# Revisión: sesión y usabilidad

Fecha: 23/10/2026. Estado: bloque revisado y autorizado por el usuario para publicación.

## Cambios

1. **Tutorial de paneles.** Se reprodujo un icono de navegación que crecía hasta convertirse en una flecha negra. Intro.js reemplazaba las clases de sus enlaces y el SVG perdía las reglas reservadas a `.btn`. Se aplican dimensiones/trazos explícitos al icono y estilos también a `.introjs-button`. Se ajustó el encuadre de la ayuda, su ancho y los desbordamientos del elemento destacado. El primer paso apunta al nuevo resumen total. Se limpia el estado del tutorial al terminar o salir.
2. **Sesión.** El contador del navegador se renovaba con actividad, mientras que la sesión del servidor podía expirar. Un POST protegido por CSRF renueva la sesión autenticada, limitado a una solicitud cada 30 segundos o un tercio del tiempo configurado para plazos cortos. No se mantiene la sesión por un temporizador sin actividad. Continuar en el aviso renueva también el servidor y admite clics sobre su icono. La actividad se comparte entre pestañas para evitar que una inactiva cierre la sesión utilizada en otra. Una sesión ya expirada conduce a iniciar sesión de nuevo.
3. **Cambios de tablero.** Desvanecimiento de 220 ms en el resultado y en los visores del resultado/historial. Se respetan las preferencias de movimiento reducido y se mantienen sincronizados dibujo y datos.
4. **Aprovechamiento total.** Gráfico de dona al comienzo del resultado con el porcentaje global calculado. Se distingue del aprovechamiento del tablero seleccionado y se indica cuántos tableros considera.
5. **Opciones limitadas.** Los accesos internos a materiales, clientes, proyectos, presupuestos, plantillas, costos, comparación y estadísticas respetan `menu_visible`, además del menú lateral. El botón de costos del inicio sigue la misma preferencia. Ocultar herramientas no borra datos ni sustituye los controles de permisos del servidor.
6. **Errores visibles.** Los mensajes de Django de nivel error reciben el estilo de peligro correcto, mayor tamaño y separación. Permanecen hasta cerrarlos manualmente. Las páginas 404/500 tienen código y textos destacados, con acciones para recuperarse.
7. **Lupa.** La copia aislada conserva estilos calculados de tamaño, disposición, tipografía y trazos SVG; los selectores con `:root` no funcionaban igual dentro del Shadow DOM. Se conserva una fila cuando el redondeo de anchos podía hacer saltar un botón de línea solo en la copia. Se toman las dimensiones interiores de la lente para centrar el punto ampliado. Continúan el seguimiento del cursor, el uso con teclado, Escape y la integración en diálogos.

## Verificación

- **147 pruebas correctas**, incluidas las regresiones de sesión autenticada/POST, accesos ocultos y descarga PNG actualizada.
- Plantillas compiladas y sintaxis JavaScript comprobada.
- Tutorial recorrido en el resultado: iconos de 18 px y sin relleno negro.
- Lupa comprobada en una página desplazada y sobre la fila de exportaciones: iconos legibles y fila conservada.
- Exportaciones y vista de impresión documentadas en `CAMBIOS_EXPORTACIONES_Y_DUPLICACION.md`.

Las comprobaciones de navegador utilizaron un usuario y base de datos independientes. La renovación de sesión conserva el plazo configurado; no desactiva la expiración. Una prueba breve no puede excluir todas las causas externas de desconexión, como reinicios del servidor o borrado de cookies.

## Agrupación futura

### Encabezado del resultado

Se retira la línea secundaria «Optimización #… · … tableros · …% de aprovechamiento» del encabezado del resultado. La tarjeta de aprovechamiento total ya presenta el porcentaje y el número de tableros, por lo que se evita repetir ese resumen. Se conserva el título de la pantalla. Cambio de presentación, sin modificar datos ni cálculos.

Segundo commit de esta entrega: **corregir sesión y mejorar las ayudas de usabilidad**. Publicación autorizada por el usuario. Los cambios de archivos compartidos se separan por fragmentos para mantener ambos commits coherentes.
