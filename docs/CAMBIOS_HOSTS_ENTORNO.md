# Hosts permitidos por entorno

Fecha: 30 de octubre de 2026.

## Corrección

Se retiró la lista fija al final de settings.py que sobrescribía ALLOWED_HOSTS después de cargar configuracion_entorno. La variable CUTLESS_ALLOWED_HOSTS vuelve a determinar los hosts permitidos.

Sin configuración adicional, desarrollo admite localhost y 127.0.0.1. Para acceder desde un teléfono en la red local se debe añadir la IP actual del computador en CUTLESS_ALLOWED_HOSTS antes de iniciar el servidor. Si se envían formularios desde ese origen, revisar también CUTLESS_CSRF_TRUSTED_ORIGINS; esta corrección no modifica su configuración.

En producción se mantiene la exigencia de hosts explícitos y el rechazo de comodines. No se configura aún ningún dominio de Render ni conexión Supabase.

## Verificación

Se añade una regresión que ejecuta el archivo completo de configuración con entornos aislados: desarrollo predeterminado, IP de red explícita y dominio de producción. Esto detecta la sobrescritura que las pruebas de la función auxiliar por sí solas no detectaban. Se proporciona una clave de prueba para evitar crear archivos locales; no se consulta la base de datos.

Publicación autorizada el 30 de octubre de 2026; sin despliegue.

Resultado: ocho pruebas de configuración aprobadas y comprobación de Django sin incidencias. La primera ejecución encontró una restricción de permisos en el directorio temporal; se repitió con acceso permitido y finalizó correctamente.
