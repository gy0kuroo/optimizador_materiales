# Consistencia de colores y acciones

Fecha: 19 de octubre de 2026.
Estado: revisado y autorizado para publicar por el usuario.

## Objetivo

Mantener el mismo significado de los colores y el mismo orden de las acciones entre pantallas, para reducir dudas y errores al utilizar CutLess.

| Función | Presentación |
| --- | --- |
| Guardar, crear, calcular, buscar o continuar | Azul principal de la paleta |
| Volver, cancelar, editar, consultar o descargar | Botón neutro con borde |
| Eliminar o descartar cambios sin guardar | Rojo, con texto explícito |
| Operación completada | Verde en mensajes de éxito |

Los colores de piezas y gráficos conservan su función de identificación. Los estados y advertencias mantienen su significado propio; este bloque unifica las acciones, no modifica reglas de cálculo ni umbrales de indicadores.

## Cambios

- Se declara la función de los botones mediante `data-action` y se aplica una hoja de estilos compartida, cargada después de los estilos de las secciones.
- Se revisan los botones de Inicio, Historial, Resultado, Gestión, Análisis, Perfil, Configuración y administración, además de formularios y páginas auxiliares.
- Se retira el verde de botones de creación y descarga. Las descargas usan el estilo secundario.
- Eliminar se mantiene como última acción, a la derecha dentro de su grupo. En menús desplegables aparece al final. En espacios estrechos el grupo puede ocupar varias líneas, conservando el orden del documento y del teclado.
- Las confirmaciones destructivas usan un botón rojo y enfocan inicialmente Cancelar. Las confirmaciones normales y los avisos recuperan el estilo azul al abrirse, evitando que hereden el rojo de un diálogo anterior.
- Se mantienen controles de al menos 48 píxeles, etiquetas visibles y foco de teclado. El significado también se expresa con texto, sin depender exclusivamente del color.

## Validación

- Suite completa: 125 pruebas correctas, con archivos generados en una carpeta temporal.
- Comprobación de Django sin incidencias y compilación correcta de 49 plantillas.
- Verificación de sintaxis JavaScript y prueba aislada del diálogo: cancelar, aceptar, enfoque inicial, cambio entre rojo y azul y limpieza de eventos.
- Revisión en navegador de la lista de clientes y su pantalla de confirmación, utilizando una base de datos temporal. Se comprobó la presentación del botón Eliminar al final, después de Historial y Editar. No se ejecutaron eliminaciones.

La revisión visual realizada es representativa; queda la revisión del usuario del conjunto de pantallas y de sus preferencias de apariencia.

## Commits anteriores publicados

- `5227e27`: configuración de herramientas y apariencia en el primer acceso.
- `a540552`: lectura, ampliación y navegación de los tableros.

Ambos cambios pertenecen al mismo período de trabajo y se publicaron como commits separados. Este bloque se publica como un commit independiente de los dos anteriores.

## Ampliación: dimensiones y alineación

A partir de la diferencia detectada entre los botones de ayuda y preparación de corte del Historial, se revisaron las reglas de tamaño de los estilos compartidos y de las secciones.

Se unifican el relleno, el borde de un píxel, las esquinas de ocho píxeles y la altura mínima de los botones. La escala usa unidades relativas al tamaño de letra, con un mínimo accesible de 48 píxeles. Los grupos de cabecera, formularios y diálogos estiran sus botones a la misma altura cuando comparten una fila. El ancho depende del texto y del espacio disponible; no se fuerza un ancho idéntico que desperdicie espacio o corte etiquetas.

Los campos de una línea y los selectores usan la misma escala de altura y relleno. Las áreas de texto, casillas y controles de navegación conservan su geometría propia. No se fijan alturas máximas que puedan recortar textos al aumentar la fuente.

Se verificaron en navegador las medidas de ambos botones del encabezado del Historial y de sus filtros. Los dos botones comparten altura, relleno y radio. Se mantiene pendiente la revisión visual del usuario en las demás pantallas.

## Corrección del contraste en Resultado

La cifra de «Tableros necesarios» usaba una insignia de Bootstrap con texto blanco y una clase de acento sin definición de fondo. Esto dejaba el número blanco sobre el fondo claro de la página.

Se sustituye por un indicador informativo específico, con texto, fondo y borde declarados mediante las variables del tema. La cantidad conserva el énfasis tipográfico y ya no depende de los estilos de botones ni de la insignia de Bootstrap. Se comprobó que no quedan usos de la clase sin definición `badge-accent-primary` en las plantillas. Los indicadores principales del resultado ya declaran el color del texto con la variable del tema.

Comprobación de Django y compilación de plantillas correctas. Esta corrección forma parte del bloque de consistencia visual autorizado para publicar.

## Aclaraciones entre paréntesis

Se incorpora `text-annotation` para separar visualmente el texto principal de las aclaraciones: por ejemplo, «Imprimir (otra pestaña)». Las notas usan un peso normal, tamaño relativo ligeramente menor y el color secundario del tema. Sobre botones de fondo sólido mantienen texto blanco para conservar el contraste; se reduce el énfasis tipográfico sin usar opacidad.

Se aplica a notas de apertura en otra pestaña, indicaciones de opcionalidad, explicaciones y recuentos complementarios en las plantillas revisadas. No se transforma automáticamente cualquier paréntesis: unidades, cantidades de piezas, opciones de selectores nativos y datos introducidos por usuarios conservan su representación para evitar alterar información necesaria o insertar HTML no admitido. Las aclaraciones siguen formando parte del texto accesible del control.

Django y las 49 plantillas se validan correctamente. Revisado por el usuario y autorizado para incluir en el commit de consistencia visual.
