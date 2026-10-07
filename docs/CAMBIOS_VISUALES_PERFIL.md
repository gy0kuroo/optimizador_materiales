# Mi perfil: claridad y continuidad visual

Fecha: 2026-10-06. Estado: revisado y aprobado por el usuario para publicación en GitHub.

Validación final del bloque: 91 pruebas correctas en cutless.tests y usuarios.tests con base de pruebas y archivos temporales; Django check sin problemas. Se excluyen los cambios locales previos en base de datos, PDFs y CAMBIOS_AREAS.md.

Se sustituye la carga del CSS antiguo de perfil por profile-redesign.css, limitado a profile-page. Otras pantallas que usan perfil.css conservan sus estilos. La paleta, superficies neutras, tipografía, controles de 48 px y ayudas legibles siguen el inicio.

El título Mi perfil coincide con la navegación. Las pestañas son Preferencias y Cuenta y contraseña. Los botones distinguen Guardar preferencias, Guardar datos de cuenta y Actualizar contraseña. Se explica el cierre por inactividad sin usar timeout en el texto de sugerencias. Se conserva el enlace de cierre de sesión.

Se añaden relaciones accesibles entre pestañas y paneles y mensajes de errores generales. Cuando hay un envío de contraseña o errores de usuario/correo, se abre la pestaña correspondiente para no ocultarlos. Se conservan nombres de formularios, CSRF, confirmaciones y lógica de guardado existente.

No se modifica el esquema de datos. Los formularios separan validación y guardado de preferencias y cuenta como se describe abajo. El usuario revisó y aprobó el resultado. La revisión exhaustiva de móvil, oscuro y teclado sigue pendiente. Este bloque no renueva todavía Configuración del sistema.

Validación: la plantilla compila y pasan las cinco pruebas existentes de usuarios.tests con base temporal; Django check sin problemas. Estas pruebas no cubren exhaustivamente el guardado de las preferencias ni la apertura de pestañas en navegador.

## Corrección de guardado y tamaño de texto

### Cierre de sesión y validación de cuenta

Cerrar sesión se mueve del pie del perfil al final del menú Cuenta, separado de los ajustes. Se conserva la ruta y el comportamiento existente, incluido el cierre automático por inactividad.

El nombre de usuario ya se validaba en servidor con isalpha y límite de 15 caracteres. Se añade la misma intención de validación en navegador mediante pattern Unicode para letras y una explicación visible al fallar. El correo sigue validándose con EmailField: @ es necesario y no se bloquea. Las contraseñas conservan símbolos admitidos por Django.

En este flujo se usa el ORM y el escape automático de las plantillas, no concatenación de SQL. La admisión de un carácter en un campo no equivale a ejecución de código; no se presenta esta revisión puntual como una auditoría total. Referencia: https://docs.djangoproject.com/en/6.0/topics/security/

Dos pruebas adicionales comprueban rechazo de símbolos y cargas SQL/HTML en usuario, conservación de registros y rechazo de correo inválido, además de aceptación de un correo válido con @. Pasan las diez pruebas de usuarios.tests con base temporal; Django check correcto.

La revisión descubrió que el formulario compartido exigía nombre y correo al guardar preferencias, produciendo errores en otra pestaña. Se añaden PreferenciasPerfilForm y CuentaPerfilForm para validar exclusivamente los campos de cada apartado. La cuenta usa su propio formulario y marcador POST; un error de preferencias conserva los datos de cuenta visibles. Los otros ajustes, incluidos notificaciones y unidades, se mantienen.

Además, tamanio_fuente no figuraba en Meta.fields del formulario, por lo que no persistía. Se incluye y theme.js aplica una escala real a la raíz del documento: pequeño 15 px, normal 16 px, grande 18 px y extra grande 20 px. Las medidas rem de la interfaz se adaptan a esa escala. La preferencia guardada del perfil tiene prioridad sobre una copia antigua de localStorage al iniciar. Se actualiza la versión de caché del script.

Se añaden tres pruebas de regresión: preferencias conservan cuenta y ajustes ajenos; cuenta conserva preferencias; preferencias inválidas mantienen los campos de cuenta. Resultado final: 89 pruebas correctas en la suite completa, con base de pruebas y archivos temporales. La interacción visual en navegador queda para revisión del usuario.
