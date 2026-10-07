# Configuración del sistema: organización y guardado

Fecha: 2026-10-06. Estado: revisado y autorizado por el usuario para publicación en GitHub.

## Resultado final del bloque

Configuración renovada con guardado por pestaña, personalización del menú separada de permisos y notificaciones conectadas al backend configurado. Se corrigen validación del margen y presentación del valor cero. Validación final: 103 pruebas correctas; Django check sin problemas.

Al actualizar otra instalación, ejecutar python cut/manage.py migrate antes de iniciar la aplicación: el campo preferencias_menu requiere la migración usuarios.0003. En esta instalación ya se aplicó con respaldo previo. La base de datos, su respaldo, los PDFs locales y CAMBIOS_AREAS.md se excluyen del commit.

## Cambio visual y textos

Se conserva el nombre del apartado y se aclara que los ajustes pertenecen a la cuenta actual. Las pestañas se llaman Cortes y notificaciones y Opciones del menú. Se elimina la referencia antigua a Más opciones; las opciones se relacionan con Gestión y Análisis.

Se sustituye el CSS antiguo y el bloque de estilos incrustados por settings-redesign.css, limitado a settings-page. Paleta común, tarjetas neutras, texto de 1.125rem, controles principales de 48 px y checkboxes de 24 px. La distribución de dos columnas se apila en móvil; los selectores se resaltan al pasar el cursor y conservan foco visible.

Se explican unidad predeterminada, margen siempre en milímetros y correo opcional de avisos. El cambio no configura SMTP ni garantiza entrega de correo: conserva los canales existentes.

## Interacción y conservación de datos

Se retiran los guardados automáticos y confirmaciones por cada campo. Cada pestaña tiene su botón de guardado: Guardar ajustes de corte y avisos y Guardar opciones del menú. Al cambiar de pestaña con cambios pendientes se ofrece quedarse o descartarlos. Esta protección se aplica al cambio interno de pestañas, no a toda salida de la página.

ConfiguracionSistemaForm valida únicamente ajustes de trabajo y notificaciones. Se eliminan los campos ocultos de cuenta, lectura y sesión y el código que completaba esos valores en el POST. El servidor conserva esos datos incluso si se envían manualmente campos ajenos. Los permisos del menú mantienen su formulario y comportamiento anterior; no se altera el modelo de autorización.

## Validación

Se añaden pruebas para conservar nombre, correo, tema, tamaño y tiempo de sesión al guardar ajustes; incluyen una cuenta histórica con guion bajo y sin correo, y margen cero. También se comprueban botones y error de margen fuera de rango. La suite se ejecuta con base y archivos temporales.

Resultado: 93 pruebas correctas y Django check sin problemas.

## Revisión funcional general posterior

### Notificaciones completadas

El servicio utiliza el backend EMAIL_BACKEND configurado sin exigir EMAIL_HOST: consola en desarrollo, SMTP cuando se configure, u otro backend definido. Los errores de correo y respuestas de cero envíos se registran; no invalidan operaciones ya completadas. No se verifica entrega SMTP real.

Los cálculos y guardados explícitos de las vistas de optimización se envuelven para emitir un evento error con mensaje genérico y volver a propagar la excepción original. No se envían detalles técnicos al usuario. Los casos sin piezas colocadas mantienen su explicación obligatoria en pantalla y permiten un aviso por correo según preferencias, sin duplicar el mensaje.

Las validaciones de campos y mensajes operativos siguen visibles; no quedan ocultos por la preferencia de avisos. Se retiran los prints de depuración del servicio de notificaciones. Las regeneraciones internas ajenas a estos cálculos y guardados explícitos no se cubren por este envoltorio.

Se añaden seis pruebas: consola sin SMTP, destinatario alternativo y filtro por evento, fallo de correo registrado, canales desactivados, evento de error técnico y explicación no duplicada. Todas usan consola capturada, backend de memoria o mocks; no envían correo real.

Validación final de esta revisión: 103 pruebas correctas con base y archivos temporales; Django check sin problemas.

### Primeras correcciones y definición de personalización

### Personalización implementada

Personalizar menú guarda las preferencias en un nuevo JSONField preferencias_menu mediante la migración usuarios.0003. Los permisos puede_* siguen controlando rutas y se administran separadamente. El formulario de personalización solo muestra opciones autorizadas y solo escribe preferencias_menu; enviar campos puede_* no modifica permisos.

La barra muestra una opción si está autorizada y marcada para mostrar. La ausencia de preferencia significa mostrar; perfiles nuevos conservan sus permisos previos. Las preferencias anteriores que desactivaron permisos no se convierten automáticamente en autorizaciones: las restricciones históricas se conservan. Administradores siguen teniendo su acceso existente.

La pestaña agrupa Gestión y Análisis con casillas Mostrar en el menú. Inicio, Historial, Cuenta y Ayuda permanecen visibles. Los grupos vacíos desaparecen. Ocultar no borra datos ni impide abrir enlaces contextuales autorizados.

Se creó respaldo SQLite local cut/db.sqlite3.menu-backup-20261006 y se aplicó la migración para permitir la revisión visual. Ni la base ni su respaldo se incluirán en el commit. Resultado: 97 pruebas correctas; incluyen ocultar/restaurar grupos, acceso directo autorizado y rechazo de elevación de permisos.

Se captura InvalidOperation y se rechazan valores no finitos al validar el margen. Las entradas abc, NaN e infinitos devuelven errores de formulario y conservan el valor anterior. El inicio renderiza el valor del campo usando default_if_none, de modo que cero permanece cero y un envío inválido no lo sustituye por 3.

El usuario aclara que Opciones del menú busca reducir ruido, no restringir acceso. La dirección propuesta es separar preferencias de visibilidad de los permisos existentes, con el nombre Personalizar menú y grupos Gestión y Análisis. Ocultar una opción no debe borrar datos ni impedir acceso por enlaces contextuales. Esta separación aún no se implementa en este paso: no se amplían permisos ni se modifican las restricciones de rutas vigentes.

Se añaden dos pruebas de regresión; resultado final de suite: 95 pruebas correctas, con recursos temporales.

Se revisaron consumidores de cada ajuste y se hicieron comprobaciones sin modificar datos reales ni enviar correos. Los siguientes hallazgos iniciales se resolvieron en las correcciones descritas arriba; se conservan como explicación del problema:

1. Un margen no numérico enviado directamente al formulario provoca decimal.InvalidOperation en la limpieza manual, en vez de un error de validación. Se reprodujo con abc.
2. El margen cero se conserva en el perfil y se carga en TableroForm, pero index.html usa una condición de verdad que sustituye cero por 3 al presentar el campo.
3. Notificaciones solo llama send_mail si EMAIL_HOST está definido; con backend de consola y host vacío no hace ningún envío. Se comprobó con mocks: aviso en pantalla presente, envío de correo ausente. Con host simulado sí llama al envío y usa el destinatario configurado. No se comprobó entrega SMTP real; fail_silently y excepciones ignoradas ocultan fallos.
4. La preferencia notificar_errores tiene rama en el servicio, pero no se encontraron llamadas con tipo error en las vistas revisadas. Los errores ordinarios usan messages directamente y no obedecen a este filtro.
5. Las opciones del menú son también permisos de acceso en las rutas. El usuario puede editar sus propios indicadores; no son permisos exclusivos de administración. Administradores y superusuarios omiten la restricción de ruta aunque oculten la opción. Se debe clarificar su significado y decidir si representan personalización o autorización administrativa antes de cambiar el modelo.

Unidad y rotación se consumen en nuevos formularios; conversiones y margen cero en almacenamiento están cubiertos por pruebas. Notificaciones de optimización, presupuesto y proyecto tienen llamadas al servicio; pantalla/correo se filtran por tipo y canal. Correo alternativo vacío usa el de cuenta; si ambos están vacíos no hay destinatario. Las confirmaciones de guardado y otros mensajes operativos no pertenecen a los avisos configurables.

El guardado conserva preferencias personales y datos de cuenta según las pruebas. La advertencia de cambios pendientes cubre el cambio de pestaña; salir de la página o recargar no tiene esa protección. La interacción JavaScript no se ha probado en navegador.

Pendiente de revisión visual con el usuario y de la interacción de pestañas en navegador, móvil y oscuro. No se ha realizado una auditoría completa de accesibilidad.

Archivos: usuarios/forms.py, usuarios/views.py, usuarios/tests.py, usuarios/templates/usuarios/configuracion_sistema.html y usuarios/static/usuarios/css/settings-redesign.css.
