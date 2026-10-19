# Configuración inicial del espacio de trabajo

Fecha: 19 de octubre de 2026. Versión revisada por el usuario y aprobada para publicación.

## Recorrido

Después de iniciar sesión, una cuenta que no haya completado esta configuración abre `/usuarios/bienvenida/`.

1. Tus herramientas: Solo lo esencial mantiene Optimización e Historial. Elegir mis herramientas permite seleccionar tarjetas de Materiales, Clientes, Proyectos, Presupuestos, Plantillas, Costos, Comparar y Estadísticas, según los permisos de la cuenta.
2. Cómo quieres verlo: cuatro tamaños de letra y temas claro, oscuro o automático. La apariencia se previsualiza al cambiar; las preferencias se guardan al finalizar.

El botón Anterior conserva la selección. En pantallas pequeñas las tarjetas cambian de distribución. Las casillas tienen etiquetas completas, foco visible y un estado de selección que no depende solo del color. Las animaciones respetan la preferencia de movimiento reducido.

La configuración puede abrirse después desde Cuenta → Personalizar mi inicio. La opción Volver sin guardar aparece cuando ya fue completada. Un primer acceso ofrece Cerrar sesión como salida. Sin JavaScript, los campos se muestran juntos y siguen pudiendo enviarse al servidor.

## Persistencia y límites

Se reutilizan `tema_preferido`, `tamanio_fuente` y `preferencias_menu`. El estado de finalización se guarda en la clave interna `_inicio_completado` de ese JSON y se expone mediante la propiedad `inicio_personalizado`. Es independiente de `tutorial_completado` y no requiere una migración.

Las cuentas anteriores a esta versión también verán la configuración en su siguiente inicio de sesión si no tienen esa marca. No se modifican sus preferencias hasta que guarden. Una sesión ya abierta puede acceder desde Cuenta.

Solo se modifica la visibilidad del menú: no se borran datos, no se conceden permisos y no se bloquea el acceso autorizado por URL a una herramienta oculta. Optimización e Historial siguen disponibles. Los controles internos del optimizador, incluidos sus costos opcionales, mantienen su comportamiento existente.

El formulario valida tema, tamaño y modo antes de guardar todos los ajustes. Los campos de herramientas no autorizadas no se aceptan. Se conservan preferencias ajenas a este panel, datos de cuenta, valores de corte, notificaciones y sesión.

El tutorial de bienvenida no se superpone a este panel. El control de inactividad de la sesión sigue cargándose. El tema guardado en el perfil tiene prioridad sobre las preferencias antiguas del navegador, también al elegir Automático.

## Archivos principales

- `usuarios/forms.py`: formulario de configuración basado en las opciones existentes de menú.
- `usuarios/models.py`: propiedad de finalización, sin cambio de esquema.
- `usuarios/views.py` y `usuarios/urls.py`: vista autenticada y redirección después del login.
- `usuarios/templates/usuarios/configuracion_inicial.html`: tarjetas, pasos y vista previa.
- `usuarios/static/usuarios/css/configuracion-inicial.css`: presentación con la paleta de CutLess.
- `usuarios/static/usuarios/js/configuracion-inicial.js`: avance, recuento y vista previa sin guardar anticipadamente.
- `cutless/templates/cutless/base.html`: acceso desde Cuenta y exclusión del tutorial en este panel.
- `cutless/static/cutless/js/theme.js`: prioridad del tema de la cuenta.

## Validación

- 35 pruebas correctas: seis nuevas del inicio, pruebas existentes de usuarios y pruebas de permisos. Cubren primera redirección y no repetición tras guardar, modo esencial, personalización autorizada, preservación de otros ajustes, errores sin escritura, reapertura y protección de sesión/CSRF.
- `manage.py check`, comprobación de migraciones pendientes del código y sintaxis JavaScript: sin incidencias. No se generaron migraciones.
- Revisión en navegador con base SQLite, archivos y usuario temporales: selección de tarjetas, avance y regreso, vista previa de oscuro con letra muy grande, guardado y menú limitado a Materiales y Plantillas, manteniendo Inicio e Historial.
- Revisión de escritorio y móvil. En el ancho móvil comprobado no hubo desbordamiento horizontal. Las capturas se tomaron con datos artificiales; la base y las cuentas reales se conservaron.

El usuario aprobó la publicación de este bloque. No se ha realizado aún una prueba formal de usabilidad con el público objetivo.

## Retirada del control temporal

Tras las pruebas, se retiran el botón Reiniciar bienvenida, su ruta, su vista, sus estilos y las pruebas específicas de ese control. Cuenta → Personalizar mi inicio sigue disponible para modificar preferencias. No se reinicia ni se borra la configuración guardada de ninguna cuenta. Las seis pruebas permanentes del panel se mantienen.
