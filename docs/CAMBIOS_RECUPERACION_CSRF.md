# Recuperación de formularios antiguos tras iniciar sesión — 31/10/2026

## Causa
Django rota el token CSRF al autenticar. Si el navegador restaura un formulario anterior mediante Atrás y lo reenvía, su token puede no coincidir con la cookie actual. Es una protección de seguridad, no necesariamente un fallo de credenciales. En desarrollo, la pantalla por defecto mostraba explicaciones técnicas en inglés.

## Medidas implementadas
- Login, registro y salida incluyen `never_cache`: encabezados privados y sin almacenamiento para evitar reutilización de respuestas antiguas.
- Login y registro detectan restauración desde bfcache con `pageshow.persisted` y navegan a la misma URL mediante GET (`location.replace`). No se utiliza `reload` para evitar repetir un POST de historial.
- `CSRF_FAILURE_VIEW` personalizado en todos los entornos: conserva HTTP 403, explica posibles causas y confirma que ese envío fue rechazado.
- Usuario autenticado: enlace GET a Inicio; usuario sin sesión: enlace GET al login para obtener un formulario nuevo.
- No se repite automáticamente ninguna operación, no se conservan contraseñas en almacenamiento y no se muestra el motivo técnico interno.
- Solicitudes AJAX/JSON reciben un error JSON 403 con mensaje y URL interna de recuperación.
- Se conservan middleware, validación de origen/token y rotación de Django. No se agrega `csrf_exempt` ni se fuerza la aceptación de formularios viejos.

## Alcance
No se bloquean las flechas del navegador. Los encabezados y la detección de bfcache reducen el uso de formularios antiguos; si se reenvía manualmente un POST previo o la cookie falta, permanece el rechazo seguro con una explicación. La pantalla ofrece una salida incluso con JavaScript desactivado. No se promete recuperar campos no enviados ni verificar que otros formularios del historial sigan vigentes.

## Verificación
Pruebas con `Client(enforce_csrf_checks=True)`: login válido y rotación, reenvío del token antiguo, token ausente, credenciales incorrectas con token válido, respuesta JSON, encabezados sin caché y redirección de usuario ya autenticado. Los rechazos mantienen 403 y no autentican solicitudes inválidas. Se prueba también con DEBUG activado que no se expongan los detalles técnicos.

Sin commit, push ni despliegue.

Resultado final: **233 pruebas Django aprobadas**, sintaxis JavaScript y formato de cambios sin errores. Pantalla y enlace GET al login comprobados en navegador local mediante una ruta temporal añadida solo en memoria al proceso de revisión; esa ruta no existe en el proyecto.
