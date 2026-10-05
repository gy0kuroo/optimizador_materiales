# Cambios visuales: inicio y navegación

Estado: revisado y aprobado por el usuario; incluido en el bloque de mejora visual de login, registro e inicio.

## Cambio

La barra superior se conserva en Deep Walnut, con borde Olive Wood y sombra más suave. Un símbolo SVG de tablero sustituye al emoji. Marca, saludo y navegación tienen menos mayúsculas y espaciado. Este cambio es compartido por las pantallas que usan la barra; login y registro la omiten.

El panel reduce la intensidad de cabeceras, bordes y tarjetas. Los iconos de secciones se conservan, con contraste adaptado a claro y oscuro. Los botones de ayuda y costos tienen tamaño y peso coherentes.

El título Plan de corte identifica la tarea; Generar plan de corte describe la acción principal. Historial conserva su nombre, rutas y significado. Los pasos numerados se presentan como orientación, no como botones.

Los textos explican unidades, corte de sierra siempre en milímetros, rotación de 90°, tipos de pieza frente a cantidad y límite de 20 tipos. El apartado Costos y datos del proyecto se identifica como opcional; sus controles explican abrir y cerrar. Los enlaces externos a la pantalla avisan que abren otra pestaña.

El selector de medidas habituales explica la entrada manual y la selección automática de material y precio cuando existe coincidencia. Este texto también alcanza las pantallas que reutilizan medidas-pred.js.

Texto general y campos: 1.125rem; ayudas: 1rem; botones: 1.0625rem; controles principales: mínimo 48 px de alto. El checkbox usa un cuadro de 24 px, con etiqueta y explicación alineadas. Los selectores tienen fondo neutro y cambian a tono de superficie al pasar el cursor; conservan foco visible para teclado. Los estilos del formulario se limitan a dashboard-page.

## Validación

El usuario revisó capturas y aprobó los refinamientos del panel. Plantillas y Django check correctos; las cinco pruebas de materiales JSON pasaron durante la revisión. Consulta [el resumen del bloque](CAMBIOS_MEJORA_VISUAL.md) para la suite final. No se realizó una auditoría completa de accesibilidad ni validación exhaustiva de móvil y oscuro en navegador.
