# Preparación de producción: Render y Supabase

Fecha: 30 de octubre de 2026.

Estado: guía de configuración pendiente de aplicar. No autoriza ni realiza un despliegue. La aplicación aún utiliza SQLite; faltan PostgreSQL, validación PostgreSQL y Linux. La adaptación de exportaciones bajo demanda corresponde al siguiente commit.

## Directorio y comandos acordados

Para evitar ambigüedades con las rutas, esta guía utiliza la raíz Git `optimizador_materiales` como directorio de trabajo. En Render, dejar Root Directory vacío. No establecerlo en `cut` con estos comandos.

Runtime: Python. Versión declarada en `.python-version`: 3.13.12. Si el servicio contiene PYTHON_VERSION, tiene prioridad y deberá coincidir o retirarse al configurar el servicio.

Build Command propuesto (Linux):

```sh
python -m pip install -r requirements.txt && python cut/manage.py collectstatic --noinput
```

Start Command propuesto (Linux):

```sh
gunicorn --chdir cut cutless_project.wsgi:application --bind 0.0.0.0:$PORT
```

PORT lo proporciona Render. No utilizar runserver en producción. No se ejecutaron estos comandos contra Render.

Las migraciones y la carga de datos no forman parte del build anterior. Se definirá un paso controlado después de preparar y respaldar la base de datos. Crear el esquema no traslada automáticamente los registros de SQLite.

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

No existe una variable DEBUG independiente consumida por esta configuración. Tampoco se interpreta DATABASE_URL actualmente: su incorporación y la conexión SSL a Supabase pertenecen a la etapa PostgreSQL.

El código no carga archivos `.env` automáticamente. `.env.example` es una referencia, no una fuente de variables para el proceso. No es necesario copiar secretos a un archivo para configurarlos en Render.

## Archivos y seguridad

WhiteNoise sirve únicamente estáticos de la aplicación recopilados en STATIC_ROOT. No utilizarlo para publicar MEDIA_ROOT ni crear un alias público para PDF e imágenes de usuarios: la ruta /media/ comprueba autenticación y propietario.

Se acordó conservar la geometría en la base y generar las exportaciones en memoria. La implementación se publicará en el siguiente commit; producción comenzará limpia.

## Comprobación antes de autorizar el despliegue

1. Retirada del seguimiento Git preparada: ver CAMBIOS_DATOS_FUERA_GIT.md. Por decisión del usuario se comenzará con datos limpios; no se migrará el histórico de prueba. Publicación autorizada junto con esta guía.
2. Implementar exportaciones bajo demanda para no depender de archivos permanentes y validarlas en Render.
3. Preparar PostgreSQL, revisar consultas exclusivas de SQLite y crear el esquema limpio mediante migraciones; sin importar el histórico de prueba.
4. Instalar y verificar dependencias y Gunicorn en Linux.
5. Ejecutar las comprobaciones Django de producción con las variables del entorno, sin mostrar secretos.
6. Validar acceso HTTPS, autenticación, formularios CSRF, estáticos, archivos privados y exportaciones en el servicio de pruebas; verificar también persistencia tras reinicio.

## Validación de esta etapa

Documento contrastado con settings.py, environment.py, requirements.txt y la documentación oficial. No se ejecutaron comandos de despliegue, migraciones ni conexiones a Supabase. No se modificaron cuentas, variables remotas ni la base local. No se crea render.yaml para evitar presentar como desplegable una configuración todavía incompleta.

Referencias:

- https://render.com/docs/deploy-django
- https://render.com/docs/web-services#port-binding
- https://render.com/docs/python-version
- https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header

Publicación autorizada el 30 de octubre de 2026; no se ejecuta el despliegue.
