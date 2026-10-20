# Paneles neutros y vista previa coherente

Fecha: 20 de octubre de 2026. Integrado en el bloque de botones y paneles, aprobado por el usuario para publicación.

## Criterio acordado

Las tarjetas y los modales utilizan superficies del tema, bordes neutros finos y separadores discretos. El café se reserva para la marca y pequeños detalles. El significado de guardar o eliminar se comunica mediante los botones existentes.

## Cambios

- Se retira el encabezado café del diálogo global de confirmación y su borde destacado.
- Encabezado, contenido y pie usan la superficie de tarjeta del tema; los separadores y el contorno tienen 1 px.
- El título mantiene Barlow, recupera el color de texto del tema y deja de forzarse a mayúsculas.
- Los diálogos informativos y el aviso de sesión siguen el mismo criterio. Se conservan sus mensajes, tiempos y acciones.
- La vista previa de configuración inicial representa ahora el menú lateral con la marca, Inicio e Historial. En móvil se apila con la navegación arriba.
- Las acciones representadas en la vista previa usan las clases del sistema actual, pero siguen siendo ejemplos sin interacción. No envían formularios ni navegan.
- Las muestras claro/oscuro de la configuración reflejan las superficies actuales.

No se alteran los colores semánticos de los botones, las preferencias guardadas, los cálculos ni las rutas.

## Archivos

- `cut/cutless/static/cutless/css/ui.css`: estilo base del diálogo compartido.
- `cut/cutless/static/cutless/css/reforma-visual.css`: contornos y superficies comunes.
- `cut/cutless/static/cutless/css/accessibility.css`: fondo neutro del aviso de sesión en oscuro.
- `cut/cutless/static/cutless/js/session-timeout.js`: retira únicamente la clase de fondo del encabezado del aviso.
- `cut/usuarios/static/usuarios/css/configuracion-inicial.css` y su plantilla: nueva disposición de la vista previa.
- `cut/cutless/templates/cutless/base.html`: versiones actualizadas de los recursos.

## Verificación

Django sin incidencias, sintaxis del script de sesión correcta y revisión visual del diálogo de preferencias en claro y oscuro, cancelando sin guardar. En claro, encabezado y tarjeta muestran el mismo fondo blanco; el contorno mide 1 px. Se comprobó la vista previa y su navegación representativa, manteniendo intactos los dos pasos del asistente.
