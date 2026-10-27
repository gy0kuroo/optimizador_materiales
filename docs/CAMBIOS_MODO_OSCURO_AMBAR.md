# Modo oscuro: superficies cálidas y acento ámbar

Fecha: 26 de octubre de 2026.

## Alcance

Primera etapa de la paleta propuesta: únicamente el modo oscuro. El modo claro mantiene sus valores y se revisará por separado. Se conserva el mecanismo existente `data-theme`, las preferencias del perfil, la tipografía, los textos, la estructura y las funciones.

Se mantienen expresamente la escala rojo–verde animada del aprovechamiento y los colores de las piezas del tablero. No se cambian cálculos ni exportaciones.

## Cambios

- `theme-colors.css` concentra los colores oscuros y sus equivalencias con los tokens existentes (`--cl-*`, `--btn-*` y los de Bootstrap). Se retiraron los antiguos bloques de variables oscuras de `palette.css` y `reforma-visual.css` para evitar varias definiciones de esos valores. La hoja se carga al final de los estilos compartidos.
- Fondo general cálido `#1A1917`, tarjetas `#232220`, superficies internas e inputs `#2C2A27` y bordes `#3A3733`.
- Texto principal blanco hueso, títulos de pieza legibles, ayudas claras y placeholders sin reducción de opacidad.
- Botones principales ámbar con texto oscuro; secundarios oscuros. Guardar conserva verde y eliminar conserva rojo, con texto blanco en ambos casos. Enlaces informativos azules y ayudas de acción ámbar.
- Navegación y pestañas seleccionadas con tinte ámbar; el menú activo incorpora una marca interior de 3 px. Se armonizan foco, checkbox, pasos, estados deshabilitados, tablas, modales y ayudas.
- Los iconos rasterizados antiguos de los encabezados se ajustan en oscuro para evitar el café oscuro sobre fondos oscuros. Los iconos SVG de botones conservan la tinta de su variante.
- El resaltado del logo de carga utiliza el token de acento existente: ámbar en oscuro, sin cambiar su aspecto azul en claro.

No se ha hecho una sustitución indiscriminada de los colores de las imágenes, dibujos o gráficos: estos pueden representar piezas y datos, no acciones de interfaz.

## Contraste comprobado

Se calculó la luminancia relativa sRGB y la relación `(L_mayor + 0,05) / (L_menor + 0,05)`.

| Combinación | Contraste |
| --- | ---: |
| Texto principal sobre tarjeta | 12,92:1 |
| Ayudas sobre superficie interna | 7,13:1 |
| Placeholder sobre input | 5,12:1 |
| Texto oscuro sobre botón principal | 6,14:1 |
| Blanco sobre guardar | 7,03:1 |
| Blanco sobre eliminar | 8,65:1 |
| Enlace informativo sobre tarjeta | 5,34:1 |

El placeholder `#8A8578` del prompt daba 3,89:1 sobre `#2C2A27`; se ajustó a `#A19A8C` para superar 4,5:1. Estas cifras validan las combinaciones indicadas, no una certificación exhaustiva de cada texto y cada estado del producto.

## Verificación

- Copia temporal independiente de la base de datos, con usuario de prueba y modo oscuro. Los datos y preferencias del usuario real no se modificaron.
- Inspección del inicio, nuevas filas de piezas, historial, resultado, materiales, clientes, presupuestos, plantillas, estadísticas, historial de costos, comparación, perfil y configuración.
- Colores computados en navegador: botón principal `rgb(200, 135, 46)`, texto de ese botón `rgb(26, 18, 6)`, secundario e input `rgb(44, 42, 39)`, título de pieza `rgb(236, 231, 223)` y placeholder `rgb(161, 154, 140)`.
- Se contrastaron los colores de las acciones destructivas y se comprobó que la dona sigue utilizando su escala rojo–verde.
- Suite completa: **169 pruebas de Django aprobadas**, sin errores del sistema. Archivos y base de datos de prueba aislados.
- Primera etapa visual revisada y aprobada por el usuario. Las comprobaciones descritas no abarcan todas las combinaciones de hover, foco, diálogos y datos posibles.

Etapa incluida en la publicación de la paleta compartida, junto con sus pruebas y documentación.

Continuación: la segunda etapa incorpora el modo claro, los avisos y el alcance de la lupa. Se documenta en `CAMBIOS_PALETA_CLARA_AVISOS_LUPA.md`.
