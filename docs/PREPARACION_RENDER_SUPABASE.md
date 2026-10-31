# Preparación de producción: Render y Supabase

Fecha: 30 de octubre de 2026.

Estado: guía de configuración pendiente de aplicar. No autoriza ni realiza un despliegue. Desarrollo conserva SQLite; producción exige PostgreSQL, cuya conexión ya está preparada localmente. La conexión real mediante Session pooler con SSL, las migraciones y las pruebas funcionales locales con PostgreSQL de Supabase fueron satisfactorias. Incluyeron autenticación, creación y almacenamiento de optimizaciones, recuperación del historial después de cerrar sesión y descargas PDF, PNG y Excel. Siguen pendientes el despliegue en Render y las pruebas en producción/Linux. Ver CAMBIOS_PREPARACION_POSTGRESQL.md. La lógica de exportación bajo demanda está implementada localmente; ver CAMBIOS_EXPORTACIONES_BAJO_DEMANDA.md.

## Directorio y comandos acordados

Para evitar ambigüedades con las rutas, esta guía utiliza la raíz Git `optimizador_materiales` como directorio de trabajo. En Render, dejar Root Directory vacío. No establecerlo en `cut` con estos comandos.

Runtime: Python. Versión declarada en `.python-version`: 3.13.12. Si el servicio contiene PYTHON_VERSION, tiene prioridad y deberá coincidir o retirarse al configurar el servicio.

Build Command propuesto (Linux):

```sh
bash build.sh
```

Start Command propuesto (Linux):

```sh
gunicorn --chdir cut cutless_project.wsgi:application --bind 0.0.0.0:$PORT
```

PORT lo proporciona Render. No utilizar runserver en producción. No se ejecutaron estos comandos contra Render.

Las migraciones y la carga de datos no forman parte del build anterior. El esquema nuevo ya se creó satisfactoriamente en Supabase mediante las migraciones ejecutadas desde el entorno local; no se importó el histórico de prueba. Crear el esquema no traslada automáticamente los registros de SQLite.

## Variables de entorno

Configurar los valores reales en el panel privado del servicio, no en Git ni en la documentación. Los siguientes dominios son ejemplos que deben sustituirse por el dominio real asignado.

| Variable | Configuración prevista |
| --- | --- |
| CUTLESS_ENV | `production`. Desactiva DEBUG y activa cookies seguras, HTTPS y HSTS. |
| CUTLESS_SECRET_KEY | Secreto aleatorio persistente, obligatorio en producción. No regenerarlo con cada arranque. El código exige al menos 50 caracteres y rechaza ciertos valores débiles; esto no sustituye generarlo de forma segura. |
| CUTLESS_ALLOWED_HOSTS | Por ejemplo `mi-cutless.onrender.com`, sin esquema ni ruta; varios hosts separados por comas. |
| CUTLESS_CSRF_TRUSTED_ORIGINS | Por ejemplo `https://mi-cutless.onrender.com`; varios orígenes separados por comas. |
| CUTLESS_TRUST_PROXY_HEADERS | Previsto `true` para el proxy HTTPS de Render, sujeto a confirmar que establece o sanea X-Forwarded-Proto y no existe acceso que evite ese proxy. Sin reconocimiento correcto podría haber redirecciones HTTPS repetidas. |
| CUTLESS_MEDIA_ROOT | Pendiente del almacenamiento elegido. Solo apuntar a una ruta cuya persistencia esté garantizada. |
| CUTLESS_DB_PATH | Solo afecta SQLite; no configura PostgreSQL y no será la conexión de Supabase. |
| CUTLESS_EMAIL_HOST | Servidor SMTP si se habilita el envío real de recuperación de contraseña. Sin él se usa la consola. |
| CUTLESS_EMAIL_PORT | Puerto STARTTLS del proveedor, valor predeterminado 587. |
| CUTLESS_EMAIL_HOST_USER | Identidad SMTP privada. |
| CUTLESS_EMAIL_HOST_PASSWORD | Credencial SMTP secreta. |
| CUTLESS_DEFAULT_FROM_EMAIL | Remitente autorizado por el proveedor. |

No existe una variable DEBUG independiente consumida por esta configuración. No se interpreta DATABASE_URL: se utilizan CUTLESS_DB_NAME, CUTLESS_DB_USER, CUTLESS_DB_PASSWORD, CUTLESS_DB_HOST y CUTLESS_DB_PORT. SSL es obligatorio en producción mediante CUTLESS_DB_SSLMODE, cuyo valor predeterminado es require. La tabla completa y las opciones de certificado están en CAMBIOS_PREPARACION_POSTGRESQL.md.

El código no carga archivos `.env` automáticamente. `.env.example` es una referencia, no una fuente de variables para el proceso. No es necesario copiar secretos a un archivo para configurarlos en Render.

## Archivos y seguridad

WhiteNoise sirve únicamente estáticos de la aplicación recopilados en STATIC_ROOT. No utilizarlo para publicar MEDIA_ROOT ni crear un alias público para PDF e imágenes de usuarios: la ruta /media/ comprueba autenticación y propietario.

La base de datos conservará la geometría. Las vistas de exportación generan PDF, PNG y Excel en memoria; no se necesita almacenar permanentemente esas nuevas descargas. Los campos y las rutas de archivos históricos se mantienen por compatibilidad; producción comenzará limpia.

## Comprobación antes de autorizar el despliegue

1. Retirada del seguimiento Git preparada: ver CAMBIOS_DATOS_FUERA_GIT.md. Por decisión del usuario se comenzará con datos limpios; no se migrará el histórico de prueba. Publicación autorizada junto con esta guía.
2. Exportaciones bajo demanda implementadas: las nuevas descargas no requieren archivos permanentes. Validar sus recursos y funcionamiento en Render.
3. Configuración PostgreSQL e introspección portable preparadas y probadas localmente. Conexión real y creación del esquema limpio en Supabase completadas desde el entorno local, sin importar el histórico de prueba.
4. Instalar y verificar dependencias y Gunicorn en Linux.
5. Ejecutar las comprobaciones Django de producción con las variables del entorno, sin mostrar secretos.
6. Validar acceso HTTPS, autenticación, formularios CSRF, estáticos, archivos privados y exportaciones en el servicio de pruebas; verificar también persistencia tras reinicio.

## Validación de esta etapa

Documento contrastado con settings.py, environment.py, requirements.txt y la documentación oficial. El usuario confirmó la conexión y la ejecución satisfactoria de las migraciones sobre Supabase desde el entorno local, además de las pruebas funcionales indicadas al inicio. No se ejecutaron comandos de despliegue en Render; las pruebas en producción siguen pendientes y SQLite no se migró ni alteró en este proceso. No se crea render.yaml para evitar presentar como desplegable una configuración todavía incompleta.

Referencias:

- https://render.com/docs/deploy-django
- https://render.com/docs/web-services#port-binding
- https://render.com/docs/python-version
- https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header

Publicación autorizada el 30 de octubre de 2026; no se ejecuta el despliegue.
