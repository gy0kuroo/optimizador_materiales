# Paleta clara, notificaciones y alcance de la lupa

Fecha: 26 de octubre de 2026.

## Paleta compartida

Se completa el modo claro con el acento cobre de la propuesta: fondo cálido, tarjetas blancas, primarios cobre con texto blanco, secundarios neutros, ayudas de acción cobre e información azul. Guardar conserva verde y eliminar conserva rojo. No cambian la tipografía, los textos, los cálculos ni los colores de piezas y de aprovechamiento.

La hoja `theme-colors.css` reúne los tokens claros y oscuros y sus equivalencias para los componentes existentes. Sustituye la hoja provisional `dark-theme.css` de la primera etapa. Los placeholders claros se ajustan a `#716857` para mantener el contraste incluso sobre superficies sutiles.

## Notificaciones

- Superficies claras de éxito, error, información y advertencia con tinta semántica oscura. En oscuro se mantiene la superficie semántica con texto hueso.
- Se elimina el borde completo de las alertas, incluida la franja lateral que aparecía gris en oscuro.
- Mensaje de 17 px sobre tamaño de raíz estándar y altura de línea de 1,6. Las notificaciones descartables reservan espacio para el botón de cierre al extremo derecho; este ya no tiene fondo blanco ni compite con el mensaje.
- No se alteran los mensajes, los tiempos de retirada ni el comportamiento de los errores.

Contrastes calculados con luminancia relativa sRGB:

| Combinación clara | Relación |
| --- | ---: |
| Aviso de éxito | 6,86:1 |
| Aviso de error | 7,96:1 |
| Aviso informativo | 8,51:1 |
| Aviso de advertencia | 6,73:1 |
| Texto blanco sobre primario cobre | 5,42:1 |
| Placeholder sobre superficie sutil | 4,59:1 |

Las cifras corresponden a estas combinaciones, no a una certificación exhaustiva de toda la interfaz.

## Lupa

Antes se trasladaban los controles a cualquier modal abierto. Ahora solo se integran en los visores de tableros del resultado y del historial, y en el visor de gráficos de análisis.

En confirmaciones de guardado o eliminación, avisos modales y otros diálogos, se ocultan los controles y se desactiva la ampliación, recuperando el cursor normal. El bloqueo cubre la apertura y el cierre completos del modal, evitando apariciones durante las transiciones. También se suspende ante tutoriales, pantallas de carga, paneles offcanvas y diálogos nativos abiertos.

Al cerrar el panel, los controles vuelven a su lugar o al visor de lectura que siga abierto. La ampliación permanece apagada hasta que el usuario la active; no reaparece encima del contenido inesperadamente.

## Verificación

- Revisión en navegador con copia temporal de base de datos y usuario de prueba: inicio claro, preferencias y resultado.
- Prueba real con lupa activa: abrir «Guardar preferencias» oculta los controles y la lente y restaura el cursor. Cancelar devuelve los controles, sin reactivar la ampliación.
- Guardado de preferencias en la copia de prueba: aviso con fondo `rgb(226, 240, 231)`, texto `rgb(21, 91, 64)` y borde izquierdo de 0 px.
- Verificado que el visor de tablero conserva la lupa integrada, y que el tutorial del resultado la oculta.
- Cuatro pruebas JavaScript nuevas cubren confirmaciones durante transiciones, visores con diálogos anidados, bloqueos de contenido y offcanvas. Se mantienen las cuatro pruebas de animación del aprovechamiento.
- Verificación adicional del aviso oscuro: texto hueso sobre fondo `rgb(32, 55, 44)`, sin borde lateral.
- **169 pruebas de Django y 8 pruebas de JavaScript aprobadas**, además de sintaxis y diff sin incidencias.
- Los datos y preferencias del usuario real no se utilizan para el guardado de prueba.

Comandos de las pruebas JavaScript:

```powershell
node cut/cutless/tests/js/magnifier-dialogs.test.cjs
node cut/cutless/tests/js/utilization.test.cjs
```

Etapa aprobada para publicación junto con sus pruebas y documentación. Se excluyen los datos locales y los pendientes de otras tareas.
