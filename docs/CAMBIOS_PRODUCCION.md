# CutLess: configuración por entorno y archivos privados, sexta etapa

Fecha: 3 de octubre de 2026.

## Objetivo

Preparar una configuración diferenciada para producción y evitar que los archivos generados se puedan descargar públicamente por su ruta. Esta etapa no despliega el proyecto ni configura un servidor real.

## Configuración por entorno

`cutless_project/environment.py` selecciona el modo mediante `CUTLESS_ENV`:

| Ajuste | development, predeterminado | production |
| --- | --- | --- |
| DEBUG | Activado | Desactivado |
| Clave secreta | Variable de entorno o clave local aleatoria | Variable de entorno obligatoria |
| Hosts | localhost y 127.0.0.1 por defecto | Lista explícita obligatoria, sin comodines |
| Cookies de sesión y CSRF | Admiten HTTP local | Solo HTTPS |
| Redirección a HTTPS | Desactivada | Activada |
| HSTS | Desactivado | 3600 segundos |

Una clave de producción debe tener al menos 50 caracteres, cinco caracteres distintos y no empezar por `django-insecure-`. Estas comprobaciones no demuestran aleatoriedad: la clave debe generarse con un generador seguro. Un modo desconocido se rechaza en lugar de activar desarrollo por accidente.

Se retiró la clave compartida del código. En desarrollo, si no se define `CUTLESS_SECRET_KEY`, se crea `cut/.development_secret_key` y se reutiliza en los siguientes arranques. Está excluida de Git. El cambio de clave invalida sesiones y enlaces firmados anteriores: puede ser necesario volver a iniciar sesión. Las cuentas y sus contraseñas no se modifican.

### Variables disponibles

| Variable | Uso |
| --- | --- |
| CUTLESS_ENV | development o production |
| CUTLESS_SECRET_KEY | Clave privada de Django |
| CUTLESS_ALLOWED_HOSTS | Hosts separados por comas, sin esquema ni puerto |
| CUTLESS_CSRF_TRUSTED_ORIGINS | Orígenes completos separados por comas; HTTPS en producción |
| CUTLESS_TRUST_PROXY_HEADERS | false por defecto; true para un proxy controlado |
| CUTLESS_DB_PATH | Ruta de SQLite; por defecto cut/db.sqlite3 |
| CUTLESS_MEDIA_ROOT | Carpeta de archivos privados; por defecto cut/media |
| CUTLESS_EMAIL_HOST | Servidor SMTP; si falta, se usa la consola |
| CUTLESS_EMAIL_PORT | Puerto SMTP, 587 por defecto |
| CUTLESS_EMAIL_HOST_USER | Usuario SMTP |
| CUTLESS_EMAIL_HOST_PASSWORD | Contraseña SMTP privada |
| CUTLESS_DEFAULT_FROM_EMAIL | Remitente del correo |

La conexión SMTP configurada usa STARTTLS. No se añade soporte para SMTP con TLS implícito en el puerto 465. Sin SMTP, los correos y enlaces de recuperación siguen apareciendo en consola; eso sirve para desarrollo, pero no entrega correo real a los usuarios.

`.env.example` documenta las variables, pero **Django no carga archivos .env automáticamente**. Configurar las variables en el entorno del proceso o mediante la plataforma de despliegue.

### Ejemplo para desarrollo en la red local

Desde la raíz del repositorio, en PowerShell, sustituyendo la IP por la del equipo:

```powershell
$env:CUTLESS_ENV = "development"
$env:CUTLESS_ALLOWED_HOSTS = "localhost,127.0.0.1,192.168.18.13"
$env:CUTLESS_CSRF_TRUSTED_ORIGINS = "http://localhost:8000,http://127.0.0.1:8000,http://192.168.18.13:8000"
python -B cut/manage.py runserver 0.0.0.0:8000
```

La IP fija anterior ya no forma parte del valor predeterminado del código. El uso local en localhost sigue funcionando sin variables adicionales.

### Preparar y comprobar un entorno de producción

Ejecutar en el entorno del servidor, sustituyendo el dominio de ejemplo:

```powershell
$env:CUTLESS_ENV = "production"
$env:CUTLESS_SECRET_KEY = python -B -c "import secrets; print(secrets.token_urlsafe(64))"
$env:CUTLESS_ALLOWED_HOSTS = "cutless.example.com"
$env:CUTLESS_CSRF_TRUSTED_ORIGINS = "https://cutless.example.com"
python -B cut/manage.py check --deploy
```

La generación anterior configura la clave solo en ese proceso de PowerShell. Guardarla de forma privada en la configuración del servidor para conservarla entre reinicios. No publicarla ni regenerarla en cada arranque. No utilizar `runserver` como servidor de producción.

`CUTLESS_TRUST_PROXY_HEADERS=true` configura `SECURE_PROXY_SSL_HEADER`. Activarlo únicamente si un proxy bajo tu control elimina la cabecera enviada por el cliente y establece correctamente `X-Forwarded-Proto`. La aplicación no debe quedar accesible por una ruta que evite ese proxy.

## Acceso privado a archivos

Se retiró el servicio público de archivos de `MEDIA_ROOT`. La ruta `/media/<archivo>` pasa siempre por Django, también con DEBUG desactivado:

- Requiere una sesión autenticada y solo admite GET o HEAD.
- Comprueba que la ruta esté dentro de MEDIA_ROOT y que el archivo corresponda a una optimización, tablero o presupuesto del usuario.
- Un usuario ajeno recibe 404, también si es superusuario. No se añade una excepción administrativa para leer archivos de otros usuarios.
- Los archivos sin referencia en la base de datos no se publican.
- Una referencia antigua compartida por distintos propietarios devuelve 404 para evitar servir un archivo de propiedad ambigua.
- Solo se sirven PDF, PNG y JPEG con su tipo de contenido, `nosniff` y caché privada sin almacenamiento.

**El servidor de producción debe enviar /media/ a Django.** No configurar un alias público de esa carpeta ni publicarla en una CDN o bucket abierto: eso evitaría las comprobaciones de propietario. Los archivos estáticos de `/static/` se gestionan por separado con collectstatic y el servidor de despliegue.

## PDF de presupuestos

Los números de presupuesto se pueden repetir entre usuarios. Sus PDF ahora usan el identificador del presupuesto y un UUID para evitar rutas compartidas. La vista guarda una referencia relativa a MEDIA_ROOT, compatible con el acceso privado.

La prueba real de exportación detectó importaciones ausentes de `Optimizacion` y `Decimal`, que se añadieron. La consulta del historial usa el propietario del presupuesto y ya no depende de que exista una primera optimización. Se comprueban presupuestos con y sin optimizaciones.

Este cambio no elimina automáticamente los PDF antiguos de presupuestos ni añade una transacción completa a esa exportación.

## Archivos afectados

- `cut/cutless_project/environment.py`, `settings.py` y `urls.py`.
- `cut/cutless/views/media.py` y `budgets.py`.
- `cut/cutless/exports/pdf.py`.
- `cut/cutless/tests/test_environment.py` y `test_media_privada.py`.
- `.gitignore`, `.env.example` y esta documentación.
- `docs/CAMBIOS_SEGURIDAD.md` y `docs/CAMBIOS_PERSISTENCIA.md`: estado actualizado.

## Validación

**86 pruebas aprobadas**, incluidas 17 nuevas: siete de configuración y diez de acceso a archivos y presupuestos. La suite completa utilizó una base de datos de pruebas y una carpeta temporal. Los hashes de la base de datos del proyecto y del PDF local de referencia permanecieron iguales.

Las pruebas cubren clave local persistente, configuración insegura rechazada, proxy optativo, acceso del propietario, bloqueo a terceros y anónimos, referencias ambiguas, rutas externas, archivos ausentes, caché, acceso sin DEBUG y PDF de presupuestos con nombres únicos y referencias relativas.

`check --deploy` se ejecutó con una clave aleatoria temporal y un dominio de ejemplo: sin errores, con los avisos `security.W005` y `security.W021`. No se habilita HSTS para todos los subdominios ni la precarga sin conocer el dominio y sus servicios. No se ocultan esos avisos.

El procedimiento de la suite aislada está en [CAMBIOS_MARGEN_CERO.md](CAMBIOS_MARGEN_CERO.md#validación). No se probó un servidor HTTPS, un proxy, SMTP ni un despliegue real.

## Git y datos existentes

Se excluyen claves locales, archivos .env privados y nuevos archivos de base de datos, media y staticfiles. `.env.example` sí se versiona. **Las exclusiones no retiran archivos que Git ya rastrea ni eliminan su historial.** La base de datos y los archivos generados antiguos continúan rastreados; no se incluyeron sus cambios locales en este bloque. Retirarlos del seguimiento y revisar el historial requiere una tarea aparte.

No hay migraciones ni dependencias nuevas. SQLite continúa siendo el motor configurado; esta etapa no migra los datos a otro motor.

## Publicación y siguiente prioridad

Crear el commit solo con los archivos de esta etapa y su documentación; conservar los cambios locales ajenos al bloque.

Después quedan actualizar las instrucciones de instalación y comprobar los formularios de clientes en modo oscuro. Antes de un despliegue real también se deben configurar el servidor, HTTPS, estáticos, SMTP y el almacenamiento privado, y revisar los archivos de datos ya versionados.

## Referencias

La separación de secretos, DEBUG, hosts, HTTPS y estáticos sigue la [guía oficial de despliegue de Django 5.2](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/). Las condiciones para confiar en la cabecera del proxy se documentan en [SECURE_PROXY_SSL_HEADER](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header).
