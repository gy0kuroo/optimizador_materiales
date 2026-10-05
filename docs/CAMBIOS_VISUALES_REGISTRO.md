# Rediseño del registro

Estado: aprobado visualmente por el usuario e incluido en el bloque de mejora visual de login, registro e inicio.

Se reutiliza la composición del login: fondo cuadriculado, panel Deep Walnut, detalles de tablero, formulario en superficie neutra y botón azul con hover Cobalt. La barra superior se omite en esta pantalla, como en login. En móvil se apilan los paneles.

La acción y el título son Crear cuenta; se aclara que los cuatro campos son obligatorios. Las etiquetas explican nombre de usuario, correo, contraseña y repetición. Se conservan las ayudas de Django sobre usuario y requisitos de contraseña, los errores por campo, POST, CSRF y el enlace a iniciar sesión.

El registro carga login-redesign.css y un archivo específico register-redesign.css. Se elimina de esta plantilla la carga duplicada de los CSS antiguos, que siguen disponibles para otras pantallas. El texto principal y las etiquetas usan 1.125rem; las ayudas 1rem y los campos mantienen altura mínima de 48 px. No se cambia RegistroForm ni la lógica de creación de cuenta.

GET y POST vacío correctos; cuatro campos, CSRF y errores presentes. Django check pasa. El usuario aprobó la apariencia. La revisión exhaustiva de móvil y oscuro sigue pendiente. Consulta CAMBIOS_MEJORA_VISUAL.md para la suite final.
