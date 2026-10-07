# CutLess — Optimizador de cortes de tableros

Aplicación Django con optimización de cortes, rotación, margen de corte, historial, clientes, materiales, presupuestos, proyectos y exportación a PDF, Excel y PNG.

## Instalación local en Windows

Necesitas Python (entorno comprobado: 3.13), pip y Git. Desde PowerShell:

```powershell
git clone https://github.com/gy0kuroo/optimizador_materiales.git
cd optimizador_materiales
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r cut/requirements.txt
.\.venv\Scripts\python.exe cut/manage.py migrate
.\.venv\Scripts\python.exe cut/manage.py check
.\.venv\Scripts\python.exe cut/manage.py createsuperuser
.\.venv\Scripts\python.exe cut/manage.py runserver
```

Si ya tienes el proyecto, abre la terminal en la carpeta que contiene este README y omite la clonación. Usar directamente el ejecutable del entorno evita activar scripts en PowerShell.

Abre [CutLess](http://127.0.0.1:8000/) o [iniciar sesión](http://127.0.0.1:8000/usuarios/login/). La aplicación está en `/cutless/` y el administrador Django en `/admin/`. Ctrl+C detiene el servidor.

`createsuperuser` solicita las credenciales que elijas; no hay contraseña predeterminada. Es opcional si ya tienes una cuenta. El repositorio puede incluir una base histórica: migrar conserva sus registros.

Para inicializar el catálogo compartido, opcionalmente:

```powershell
.\.venv\Scripts\python.exe cut/manage.py crear_materiales_predefinidos
```

Este comando crea materiales faltantes y puede actualizar sus descripciones.

En Linux/macOS usa `python3 -m venv .venv` y sustituye `.\.venv\Scripts\python.exe` por `./.venv/bin/python`.

## Configuración

El modo predeterminado es desarrollo local. La clave se genera en `cut/.development_secret_key` y se reutiliza; no debe publicarse. Los datos locales usan `cut/db.sqlite3` y `cut/media/`.

[.env.example](.env.example) enumera las variables, pero **no se carga automáticamente**. Define las variables antes de iniciar el servidor:

```powershell
$env:CUTLESS_ENV = "development"
$env:CUTLESS_ALLOWED_HOSTS = "localhost,127.0.0.1"
.\.venv\Scripts\python.exe cut/manage.py runserver
```

La [documentación de producción](docs/CAMBIOS_PRODUCCION.md) explica HTTPS, correo, hosts, proxy y almacenamiento privado. Sin SMTP el correo se imprime en consola. No expongas `media/` como carpeta pública: sus rutas requieren autorización.

## Comprobaciones y solución de problemas

Si aparece `no such table`, detén el servidor, ejecuta `migrate` con el mismo entorno y configuración, y vuelve a iniciarlo. Conserva la base de datos.

```powershell
.\.venv\Scripts\python.exe cut/manage.py showmigrations
.\.venv\Scripts\python.exe cut/manage.py check_database
```

`showmigrations` muestra las migraciones aplicadas. `check_database` comprueba tres tablas esenciales de SQLite; no valida todo el esquema ni los datos.

Si falta una dependencia, repite la instalación con el ejecutable del entorno virtual. Para otro puerto usa `runserver 8001` y abre `http://127.0.0.1:8001/`.

## Pruebas con archivos aislados

Desde la raíz del repositorio, con el servidor detenido:

```powershell
@'
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path("cut").resolve()))
os.environ["DJANGO_SETTINGS_MODULE"] = "cutless_project.settings"
with tempfile.TemporaryDirectory(prefix="cutless-tests-") as tmp:
    os.environ["MPLCONFIGDIR"] = str(Path(tmp) / "matplotlib")
    from django.conf import settings
    settings.MEDIA_ROOT = str(Path(tmp) / "media")
    import django
    django.setup()
    from django.test.utils import get_runner
    failures = get_runner(settings)(verbosity=1).run_tests(
        ["cutless.tests", "usuarios.tests"]
    )
raise SystemExit(bool(failures))
'@ | .\.venv\Scripts\python.exe -B -
```

Django usa una base de pruebas independiente. Los archivos generados quedan en una carpeta temporal que se elimina al terminar.

## Estructura

```text
README.md
.env.example
docs/                         Documentación por cambio
cut/
├── manage.py
├── requirements.txt
├── cutless_project/          Configuración, entorno y rutas raíz
├── cutless/
│   ├── models.py
│   ├── forms/                Formularios por módulo
│   ├── views/                Vistas y acceso privado a archivos
│   ├── services/             Optimización y persistencia
│   ├── packing.py            Colocación de piezas
│   ├── pieces.py
│   ├── units.py
│   ├── render.py             Gráficos
│   ├── exports/              PDF y Excel
│   ├── management/commands/
│   ├── templates/
│   ├── static/
│   ├── migrations/
│   └── tests/
├── usuarios/                 Cuentas, perfiles y permisos
├── db.sqlite3                Datos locales
└── media/                    Archivos generados
```

El margen se introduce en milímetros: 0 permite corte sin separación; el valor predeterminado es 3 mm. Las dimensiones usan la unidad seleccionada.

## Documentación de cambios

- [Seguridad](docs/CAMBIOS_SEGURIDAD.md)
- [JSON seguro](docs/CAMBIOS_JSON_SEGURO.md)
- [Margen cero](docs/CAMBIOS_MARGEN_CERO.md)
- [Áreas](docs/CAMBIOS_AREAS.md)
- [Persistencia](docs/CAMBIOS_PERSISTENCIA.md)
- [Producción y archivos privados](docs/CAMBIOS_PRODUCCION.md)
- [Instalación](docs/CAMBIOS_INSTALACION.md)
- [Mejora visual de login, registro e inicio](docs/CAMBIOS_MEJORA_VISUAL.md)
- [Mejora visual de historial y resultado](docs/CAMBIOS_VISUALES_HISTORIAL_RESULTADO.md)
- [Reorganización de navegación](docs/CAMBIOS_NAVEGACION.md)
- [Mi perfil y preferencias](docs/CAMBIOS_VISUALES_PERFIL.md)
- [Configuración, menú personalizado y notificaciones](docs/CAMBIOS_VISUALES_CONFIGURACION.md)

Git ignora nuevos datos locales, pero los archivos ya versionados siguen en seguimiento. Su retirada y revisión del historial quedan pendientes.
