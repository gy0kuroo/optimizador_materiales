# Servidor de producción y archivos estáticos

Fecha: 30 de octubre de 2026.

## Preparación

Se declaran Gunicorn 26.2.0 y WhiteNoise 6.12.0 en cut/requirements.txt. El archivo de dependencias de la raíz ya enlaza esta lista. Gunicorn tiene un marcador que excluye Windows: se instalará en el entorno Linux previsto para Render. En Windows se conserva runserver para desarrollo.

WhiteNoise se añade inmediatamente después de SecurityMiddleware. En producción, los estáticos utilizan CompressedManifestStaticFilesStorage para generar nombres con hash y versiones comprimidas. En desarrollo se conserva StaticFilesStorage. El almacenamiento de archivos privados sigue siendo FileSystemStorage; no se publican los PDF ni imágenes de usuarios mediante WhiteNoise.

Se instaló WhiteNoise localmente sin actualizar otras dependencias. No se instaló ni ejecutó Gunicorn en Windows.

## Comandos de referencia para la etapa de despliegue

Desde la raíz Git, con el entorno de producción y las dependencias ya configurados:

```sh
python cut/manage.py collectstatic --noinput
gunicorn --chdir cut cutless_project.wsgi:application --bind 0.0.0.0:$PORT
```

Son referencias para Linux/Render, no comandos ejecutados contra un servicio. La construcción y el arranque definitivos se formalizarán en la siguiente etapa. Las migraciones, la conexión PostgreSQL y la persistencia de archivos siguen pendientes.

## Validación

- Ocho pruebas existentes de configuración aprobadas; comprobaciones de Django sin incidencias.
- collectstatic completo con DEBUG=False en una carpeta temporal: manifiesto generado sin errores de referencias CSS.
- Entrega directa mediante WhiteNoise con respuesta 200 y URL con hash para CSS del tema, JavaScript de lupa, iconos SVG y CSS del administrador.
- No se consultó ni modificó la base de datos; no se utilizó cut/staticfiles como destino de la comprobación.
- Pendientes: arranque real de Gunicorn y prueba integral en Linux, carga visual en navegador y comportamiento bajo carga. La comprobación local no certifica el despliegue completo.

Referencias oficiales:

- https://whitenoise.readthedocs.io/en/stable/django.html
- https://pypi.org/project/gunicorn/26.2.0/
- https://pypi.org/project/whitenoise/6.12.0/

Publicación autorizada el 30 de octubre de 2026; sin despliegue.
