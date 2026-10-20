# Reforma visual integral de CutLess

Fecha: 20 de octubre de 2026. Integrado en el bloque general de reforma visual, aprobado para publicación por el usuario.

## Objetivo y límites acordados

Adaptar la presentación a la referencia de marca entregada por la profesora: superficies claras, identidad relacionada con tableros y madera, navegación despejada y un plano protagonista. La referencia se interpreta para la aplicación existente, no como una sustitución de sus funciones.

Se mantiene Barlow y la elección de tamaño de letra de cada usuario. La paleta prioritaria sigue siendo:

| Color | Uso principal |
| --- | --- |
| `#4E2D01` | Identidad y acentos nogal |
| `#7D6344` | Acentos secundarios |
| `#B7B8AB` | Neutros y superficies derivadas |
| `#4558E7` | Acción principal, selección y foco |
| `#1E287B` | Acento azul profundo |

Los fondos claros y oscuros son tonos derivados para lectura. Se conservan los colores semánticos de peligro, éxito y advertencia: eliminar sigue siendo una acción de peligro, no una acción azul o verde.

Quedan excluidas las propuestas funcionales del manual Word: nuevos formatos CSV, cambios en JSON o modelos, selección interactiva de piezas, interruptores para nombres y medidas, nuevas confirmaciones de guardado y regeneración de PDF. No se modifican el algoritmo, el margen de corte, la persistencia ni los generadores de archivos.

## Presentación compartida

- Nueva marca geométrica SVG local, inspirada en los segmentos de tablero de la referencia. Se reutiliza en navegación, login, registro, bienvenida y favicon. Es una adaptación vectorial; no reproduce la textura de madera de la imagen original.
- Navegación lateral desde 1200 px, con iconos de trazo uniforme y estado de página activa. Los grupos, destinos y permisos existentes se conservan. Ayuda y Cuenta quedan en la parte inferior; los submenús se despliegan dentro de la barra.
- En ventanas menores se utiliza la navegación superior plegable, con desplazamiento propio cuando el menú es alto.
- Una última capa CSS unifica tarjetas, encabezados, tablas, campos, pestañas, ventanas, bordes, separación y estados de foco. Se aplica a Inicio, Historial, Gestión, Análisis, Perfil, Configuración, Ayuda y administración de usuarios.
- Se conserva la lógica de acciones y las preferencias de tema y letra. El modo oscuro utiliza superficies cálidas y textos contrastados; fechas e iconos nativos siguen el esquema de color.
- Login y registro comparten una composición clara con la nueva marca y motivos geométricos. La configuración inicial mantiene sus dos pasos y preferencias.

## Inicio

En pantallas de al menos 1400 px, tablero y piezas ocupan dos columnas. Costos y el botón de cálculo permanecen junto a las piezas. En pantallas menores se apilan en el orden habitual.

Se mantienen todos los nombres de campo, identificadores, unidades, valores, formsets, validaciones y acciones originales. Nombre de pieza ocupa una fila y las medidas/cantidad se alinean en una cuadrícula adaptable. Los botones de ayuda muestran «Ayuda» y conservan nombres accesibles específicos.

## Resultado: un tablero a la vez

Esta es la modificación de interacción expresamente autorizada:

1. La página muestra «Anterior · Tablero N de total · Siguiente».
2. Cada cambio muestra juntos el dibujo, sus medidas, aprovechamiento y catálogo originales.
3. Los extremos desactivan el botón correspondiente; el indicador anuncia los cambios mediante `aria-live`.
4. Recorrer el visor ampliado y cerrarlo deja seleccionado el mismo tablero en la página.

Las tarjetas se conservan en el documento. Sin JavaScript se muestran todas como alternativa. La impresión directa del navegador vuelve a mostrar todos los tableros. El PDF, Excel, PNG y la página específica de impresión mantienen sus rutas y contenido.

El resumen superior prioriza aprovechamiento, tableros y piezas colocadas. Área y desperdicio siguen visibles. El plano aparece antes que los costos; el resumen global de tableros se consulta en un bloque desplegable. No se elimina información.

La barra de herramientas de la vista previa de impresión recibe un estilo separado, solo para pantalla. El botón «Cerrar» evita la clase de Bootstrap reservada al icono de cierre; su acción sigue siendo `window.close()`. No se modifica el formato del papel.

## Historial y formularios

Los filtros del Historial usan una cuadrícula que evita comprimir fechas y opciones; en móvil se apilan. Las miniaturas conservan proporciones dentro de un área común. Historial y Plantillas reducen columnas cuando el ancho disponible resulta insuficiente.

Los formularios de administración usan un fragmento compartido para alinear etiquetas, campos, ayudas y errores. Se siguen renderizando los campos originales de Django, incluidos los ocultos y los errores generales.

## Archivos principales

- `cut/cutless/static/cutless/css/reforma-visual.css`: capa visual compartida y adaptaciones por pantalla.
- `cut/cutless/static/cutless/css/print-preview-shell.css`: barra de impresión en pantalla.
- `cut/cutless/static/cutless/brand-symbol.svg` y `favicon.svg`: identidad vectorial.
- `cut/cutless/static/cutless/js/visual-shell.js`: estado visual de navegación.
- `cut/cutless/static/cutless/js/board-deck.js`: navegación de tableros.
- `cut/cutless/static/cutless/js/board-viewer.js`: evento de sincronización al cambiar de tablero.
- `cut/cutless/templates/cutless/includes/`: marca y presentación de campos reutilizables.
- Plantillas base, inicio, resultado, impresión y pantallas de acceso/administración: integración de la presentación.

Se añade una capa final para conservar compatibilidad con los estilos anteriores. Una futura consolidación de hojas CSS puede reducir reglas heredadas; no es necesaria para usar esta reforma.

## Verificación realizada

- Suite completa de Django: **127 pruebas correctas**, con archivos generados en un directorio temporal, separado de los datos locales.
- `manage.py check`: sin incidencias.
- Compilación de **51 plantillas** y comprobación de sintaxis de los tres scripts implicados.
- Revisión HTTP de 29 rutas autenticadas en una base temporal: respuestas correctas y datos guardados sin cambios tras consultar las pantallas.
- Prueba real de cuatro tableros: avance hasta el último, un solo tablero visible, límites desactivados y sincronización con el visor ampliado.
- Comprobación de añadir piezas y desplegar costos sin enviar una optimización.
- Revisión visual en el navegador integrado: acceso, registro, bienvenida, inicio, historial, resultado, secciones de Gestión y Análisis, Perfil, Configuración, ayuda contextual y administración. Temas claro/oscuro y muestras de ancho de 390, 768, 1024 y 1440 px; preferencia de letra grande y vista previa de letra muy grande.

Estas comprobaciones no equivalen a una validación exhaustiva de todas las combinaciones de contenido, navegadores y tamaños. La revisión del usuario y de la profesora sigue siendo necesaria para ajustar decisiones de diseño.

## Revisión sugerida

Recorrer acceso → inicio → resultado con varios tableros → historial → Gestión/Análisis → Cuenta. Comprobar la misma secuencia en oscuro y con letra grande. Confirmar especialmente la nueva distribución del inicio y el tamaño relativo del plano y su información antes de preparar commits.

## Cierre del bloque general

Este bloque incluye también el visor horizontal, las cotas, su integración en el Historial y las miniaturas horizontales. Validación final: 137 pruebas correctas. La unificación de botones solicitada después queda para el siguiente bloque y no forma parte de esta reforma.
