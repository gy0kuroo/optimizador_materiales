# Foco correcto en las filas de piezas

Fecha: 29 de octubre de 2026.

## Problema y corrección

Al clonar una fila, se actualizaban los nombres y los identificadores de sus campos, pero no el atributo `for` de las etiquetas. Al pulsar «Ancho», «Alto», «Cantidad» o el nombre de una pieza nueva, el navegador enfocaba el campo de la primera fila. En teléfono, ese cambio de foco desplazaba la pantalla hacia arriba.

También podían repetirse índices al eliminar una fila intermedia y añadir otra: se reducía el contador, pero las filas restantes conservaban sus índices antiguos.

`piece-formset.js` normaliza las filas visibles en orden y actualiza nombres, identificadores, etiquetas y referencias accesibles. Se utiliza en inicio y edición después de añadir o eliminar una pieza y al cargar el formulario. El contador de Django refleja la cantidad de filas presentes. La duplicación de una optimización utiliza el mismo formulario de inicio y recibe la corrección.

No se alteran los valores, las medidas, la cantidad de piezas ni el cálculo. No se anula el comportamiento nativo de las etiquetas ni se oculta el desplazamiento con JavaScript: se corrige el vínculo que provocaba el foco incorrecto.

## Verificación

- Tres pruebas JavaScript aprobadas: etiquetas de filas clonadas, eliminación intermedia seguida de alta y eliminación de la primera fila. Comprueban identificadores únicos, referencias accesibles y valores conservados.
- En navegador, sobre una copia temporal de datos: las etiquetas Ancho, Alto y Cantidad de la tercera fila enfocan `id_form-2-ancho`, `id_form-2-alto` e `id_form-2-cantidad`.
- Tras eliminar la fila intermedia y añadir otra se conservan los valores 33, 44 y 5 de la fila restante, sin IDs repetidos.
- Verificado también el foco de la tercera fila del formulario de edición.
- Doce pruebas de Django de vistas, usabilidad y precisión aprobadas con archivos y base de datos aislados.
- Sintaxis del nuevo JavaScript y diff sin incidencias.

Comando de regresión:

```powershell
node cut/cutless/tests/js/piece-formset.test.cjs
```

Los datos y la configuración locales preexistentes del usuario no se modifican. Publicación autorizada el 30 de octubre de 2026 junto con las correcciones del menú móvil y la exclusión de la lupa en móvil.
