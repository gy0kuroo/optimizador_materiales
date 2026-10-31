# Preparación local de PostgreSQL y despliegue

Fecha: 30 de octubre de 2026.

## Configuración sin conexión remota

database.py construye DATABASES sin abrir conexiones. Desarrollo sigue usando SQLite por defecto y respeta CUTLESS_DB_PATH. Desarrollo puede seleccionar PostgreSQL mediante CUTLESS_DB_ENGINE=postgresql.

Producción utiliza PostgreSQL y exige nombre, usuario, contraseña y host. Si faltan, se rechaza el arranque con los nombres de las variables ausentes, sin mostrar valores. No se permite usar SQLite en producción ni se cambia silenciosamente a una base local. Esto sustituye el comportamiento anterior de producción con SQLite.

| Variable | Regla |
| --- | --- |
| CUTLESS_DB_ENGINE | sqlite en desarrollo por defecto; postgresql en producción. |
| CUTLESS_DB_NAME | Nombre de la base, obtenido del panel. |
| CUTLESS_DB_USER | Usuario exacto del tipo de conexión elegido. |
| CUTLESS_DB_PASSWORD | Contraseña privada de la base. Se conserva literalmente, sin codificación URL. |
| CUTLESS_DB_HOST | Host exacto obtenido del panel. |
| CUTLESS_DB_PORT | 5432 por defecto; puerto válido entre 1 y 65535. |
| CUTLESS_DB_SSLMODE | require por defecto. Producción admite require, verify-ca o verify-full; desarrollo admite además disable para un PostgreSQL local. |
| CUTLESS_DB_SSLROOTCERT | Ruta opcional del certificado raíz para la verificación TLS. No se descarga ni configura un certificado automáticamente. |

Se eligen variables separadas para evitar errores al codificar contraseñas dentro de una URL. DATABASE_URL no es interpretada por esta implementación. .env.example documenta las nuevas variables con ejemplos comentados; no carga ni activa valores.

Se declara e instala localmente psycopg[binary] 3.3.6. Se verificó que Django carga el backend y construye sus parámetros sin abrir una conexión. No se utiliza el SDK de Supabase: Django se conecta a PostgreSQL y conserva su autenticación actual.

## Conexiones y compatibilidad

Timeout de conexión: 10 segundos. CONN_MAX_AGE=0 cierra conexiones al finalizar las peticiones; no se añade un pool propio ni se dejan conexiones persistentes ilimitadas. Se deshabilitan prepared statements y cursores de servidor para evitar incompatibilidades del pooler en modo transacción. Se recomienda comenzar con conexión directa si la red la admite o Session pooler si se necesita IPv4, copiando host y usuario del panel.

sslmode=require exige cifrado, pero no verifica la identidad del servidor. Para esa verificación se debe preparar el certificado de Supabase y configurar verify-full. Esa parte depende del proyecto real y no está validada todavía.

El middleware y check_database utilizan ahora connection.introspection.table_names() en lugar de sqlite_master. El middleware solo informa, nunca ejecuta migraciones. El comando sin --fix es de lectura; su opción previa --fix conserva el comportamiento explícito de ejecutar migraciones, pero no se utilizó. El mensaje de éxito aclara que solo verifica tres tablas esenciales, no todo el esquema.

Se omiten detalles de excepciones de conexión en estos mensajes para evitar revelar valores privados. Las pruebas comprueban que no aparece una credencial ficticia introducida en una excepción.

## Construcción preparada

build.sh, ejecutado mediante `bash build.sh` desde Render, instala dependencias, ejecuta check --deploy con errores bloqueantes y recopila estáticos. No ejecuta migraciones ni crea cuentas. Las variables de producción y base deben estar configuradas también durante el build. Se añade .gitattributes para conservar finales de línea LF en build.sh al trabajar desde Windows. El script no se ejecutó aquí: sus comprobaciones Django y collectstatic sí se verificaron por separado en Windows.

El comando de arranque acordado continúa siendo:

```sh
gunicorn --chdir cut cutless_project.wsgi:application --bind 0.0.0.0:$PORT
```

## Validaciones y límites

- Se revisaron las migraciones existentes: no se encontraron RunSQL ni RunPython específicos de SQLite. Posteriormente, el usuario ejecutó satisfactoriamente las 25 migraciones desde el entorno local contra PostgreSQL de Supabase, creando las tablas en una base limpia, sin importar SQLite.
- Disponibilidad de dependencias para CPython 3.13 / Linux x86_64: resolución y descarga temporal de 23 wheels, incluido Gunicorn. Se eliminaron al terminar la carpeta temporal. Esta comprobación no ejecuta los paquetes en Linux.
- check --deploy con configuración PostgreSQL ficticia: sin errores; permanecen los avisos W005 y W021 sobre HSTS en subdominios y preload. No se habilitan sin conocer los dominios reales.
- collectstatic completo en carpeta temporal con DEBUG=False y backend PostgreSQL seleccionado, sin conexión remota.
- Suite de aplicación ejecutada con base SQLite de pruebas y archivos temporales; **183 pruebas aprobadas**. Incluye pruebas de configuración, ausencia de fallback en producción, parámetros del adaptador, introspección y mensajes sin credenciales.
- Pruebas manuales locales con PostgreSQL de Supabase mediante Session pooler, puerto 5432 y SSL obligatorio: conexión real, migraciones, autenticación, creación y almacenamiento de optimizaciones, recuperación del historial después de cerrar sesión y descargas PDF, PNG y Excel, todas confirmadas satisfactorias por el usuario. No equivalen a una validación exhaustiva de restricciones, transacciones o concurrencia ni a pruebas de producción en Render.
- Gunicorn no se ejecutó en Windows. Pendiente arranque y revisión funcional en Linux/Render.

## Lo que requiere configurar las plataformas

1. Completado localmente: conexión a Supabase mediante variables privadas y Session pooler con SSL. Falta configurar esas variables en Render; no pegar credenciales en el chat, código o documentación.
2. SSL y conectividad comprobados localmente, con permisos suficientes para aplicar las migraciones. Revisar que las tablas de Django no queden accesibles públicamente por las API de Supabase; CutLess no necesita exponerlas al navegador por esas API.
3. Esquema limpio creado en Supabase mediante migraciones; autenticación y datos nuevos de prueba verificados desde la aplicación local. No se importó el histórico de SQLite. El catálogo adicional se inicializará si se necesita.
4. Configurar el servicio Render, hosts, CSRF, proxy HTTPS, build y arranque. Si se activa auto-deploy, hacerlo solo cuando las variables y los pasos de base estén preparados.
5. Verificar login, formularios, optimización, historial, acceso por propietario, descargas y persistencia de datos tras reinicio. Repetir rendimiento en el entorno real.
6. Configurar SMTP si se requiere recuperación de contraseñas por correo.

Referencias oficiales:

- https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://pypi.org/project/psycopg/3.3.6/

Preparación de código local documentada, sin commit ni push de este bloque. Supabase ya tiene las tablas y fue validado desde la aplicación local; el despliegue en Render y las pruebas en producción siguen pendientes.
