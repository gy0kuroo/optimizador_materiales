# Medidas: límites y avisos comprensibles por unidad

Fecha: 31 de octubre de 2026.

## Problema

Al ingresar medidas fuera de rango, el aviso superior pedía revisar los datos sin explicar el motivo. Las validaciones generales del tablero podían quedar fuera de los errores mostrados junto a sus campos. Además, un valor rechazado por el campo podía presentarse después como ausente. Las piezas tenían límites numéricos fijos de 0,1 a 300 sin tener en cuenta la unidad elegida: por ejemplo, se rechazaban 1000 mm aunque equivalen a 100 cm.

## Cambios

- Cada dimensión se valida y muestra su error por separado: campo, valor ingresado, unidad, motivo (demasiado alto/bajo) y rango permitido.
- El aviso superior incluye el motivo real. En piezas identifica el número de fila; no muestra únicamente una indicación genérica.
- Tablero: se mantiene el rango físico existente de 10 a 300 cm por lado. Ejemplos: 0,1 a 3 m; 100 a 3000 mm.
- Piezas: se valida el equivalente físico de 0,1 a 300 cm por lado en todas las unidades. Se corrige la aplicación de esos números como si todas las entradas fueran centímetros. No se modifican cantidad máxima, algoritmo ni ancho de sierra.
- La ayuda muestra el rango correspondiente a cm, m, mm, pulgadas o pies. Los límites mostrados en unidades con conversión no exacta se redondean hacia el interior del rango para que puedan ingresarse sin excederlo.
- Una ayuda junto al selector explica con un ejemplo cómo escribir un tablero de 122 × 244 cm en la unidad seleccionada. Los ejemplos de los campos también se actualizan. La sierra sigue expresándose siempre en mm.
- La validación en navegador se actualiza al escribir, cambiar de unidad y añadir piezas; al salir del campo o intentar enviar aparece el error junto a la entrada. El servidor conserva la validación si JavaScript está desactivado.
- Las filas nuevas no heredan los mensajes de error de la fila clonada. Se conservan valores rechazados para corregirlos y no se repiten los errores dimensionales en dos bloques dentro de una pieza.
- Aplicado a inicio, edición y formularios precargados por duplicación, con ayudas iniciales según la unidad elegida.

Ejemplo: «El ancho del tablero es demasiado alto: ingresaste 1000 m. Rango permitido: de 0,1 a 3 m por lado. Revisa el valor o la unidad seleccionada.»

## Verificación

- Suite completa: 191 pruebas Django aprobadas. Después del ajuste final de ayudas iniciales, 24 pruebas de mensajes, margen y precisión RNF-09 aprobadas.
- Dos pruebas JavaScript nuevas de rangos y mensajes por unidad, y tres de reindexación de filas, aprobadas. Sintaxis y diff sin errores.
- En navegador, sobre una copia SQLite temporal: comprobado el caso de 1000 m, su aviso junto al ancho, rango de 0,1 a 3 m y ejemplo de 1,22 × 2,44 m. Al cambiar a mm, 1000 se acepta y las ayudas pasan a la unidad correspondiente. Una fila añadida conserva IDs y ayuda correctos, sin copiar errores.
- La edición inválida conserva los datos del resultado anterior. Los mensajes inválidos no generan una optimización nueva.
- No se usó Supabase ni la base local real; se cerraron el servidor y la pestaña temporales. No se afirma haber validado esta modificación en Render o en teléfono físico.

Cambios locales con documentación. Sin commit, push ni despliegue.

## Ampliación: ancho de sierra

Se aplica la misma validación inmediata al campo de sierra en inicio, edición y duplicación. El rango visible es de 0 a 10 mm; no cambia aunque tablero y piezas estén en metros, pulgadas u otra unidad. Un valor fuera de rango establece la invalidez del campo en el navegador y bloquea el envío antes de calcular. Al salir del campo o intentar enviar, aparece el aviso junto a la entrada; al corregirlo, se retira. 0 sigue significando sin separación, y el campo vacío conserva su comportamiento anterior.

Se mantienen los validadores del servidor y se concretan sus mensajes de máximo, mínimo y número inválido. Se actualiza la versión del recurso JavaScript para evitar usar una copia en caché sin esta ampliación.

Verificación adicional: 25 pruebas Django de mensajes, margen y precisión aprobadas; tres pruebas JavaScript aprobadas. Casos de sierra: 0, 3 y 10 mm válidos; 11, -1 y texto rechazados, independientemente de la unidad del tablero. Sin uso de datos reales ni Supabase. No se repitió la revisión visual en navegador para esta ampliación.

## Ampliación: cantidad por tipo de pieza

Se mantiene el límite existente del servidor de 1 a 100 piezas iguales por tipo, sin aumentar la carga máxima admitida. Ahora se muestra el rango junto a Cantidad y se incluye este campo en la validación inmediata del navegador, también al añadir una fila. Se rechazan excesos, cero, negativos, texto y números fraccionarios antes de enviar el formulario. Los mensajes del servidor también explican el límite y la exigencia de un entero. El campo vacío conserva el valor predeterminado anterior de una pieza.

Aplicado a inicio y edición, incluyendo el formulario de duplicación. Versión JavaScript actualizada para invalidar la caché. Verificación de esta ampliación: 26 pruebas Django y cuatro pruebas JavaScript aprobadas. Casos: 1, 50 y 100 válidos; 0, -1, 101, 1246545654, 1,5 y texto inválidos. No se conectó a Supabase ni se ejecutó una optimización real. Sin commit ni despliegue.

## Corrección: iconos de error persistentes

Al corregir una entrada se vaciaba el texto del aviso, pero quedaba su elemento con clase text-danger. index.css dibuja un icono mediante ::before sobre esa clase, incluso sin contenido. Ahora se retira el elemento completo cuando el valor es válido, junto con is-invalid y el estado aria-invalid. Si se introduce otro valor incorrecto, el aviso vuelve a crearse normalmente.

La reevaluación también escucha los eventos change del formulario que emiten las medidas habituales y los materiales; no depende exclusivamente de escribir o cambiar la unidad. Se conserva el borrado de customValidity al corregir. Inicio y edición cargan la versión 4 del recurso JavaScript.

Cinco pruebas JavaScript aprobadas, incluida una regresión de aviso visible, corrección, eliminación completa del nodo y aparición de un nuevo error. Sintaxis y diff sin incidencias. Sin cambios de servidor, conexión a Supabase, commit ni despliegue en esta corrección.

## Publicación

Publicación autorizada el 31 de octubre de 2026. Verificación final: 193 pruebas Django y cinco pruebas JavaScript aprobadas. Las menciones previas a cambios locales describen el estado de cada revisión antes de esta autorización. No se ejecutaron migraciones ni se modificó la configuración de Render.
