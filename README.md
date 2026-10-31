# CutLess — Optimizador de cortes de tableros

Aplicación Django con optimización de cortes, rotación, margen de corte, historial, clientes, materiales, presupuestos, proyectos y exportación a PDF, Excel y PNG.

## Instalación local en Windows

Necesitas Python (entorno comprobado: 3.13), pip y Git. Desde PowerShell:

```powershell
git clone https://github.com/gy0kuroo/optimizador_materiales.git
cd optimizador_materiales
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe cut/manage.py migrate
.\.venv\Scripts\python.exe cut/manage.py check
.\.venv\Scripts\python.exe cut/manage.py createsuperuser
.\.venv\Scripts\python.exe cut/manage.py runserver
```

Si ya tienes el proyecto, abre la terminal en la carpeta que contiene este README y omite la clonación. Usar directamente el ejecutable del entorno evita activar scripts en PowerShell.

`-r` indica que pip debe leer un archivo con la lista de dependencias. `pip install requirements` busca un paquete llamado `requirements` y no instala las dependencias del proyecto. Desde la raíz usa el comando anterior; desde la carpeta `cut`, usa `python -m pip install -r requirements.txt` con el Python de tu entorno virtual. El archivo de la raíz enlaza la lista de `cut/requirements.txt`, sin duplicar versiones.

Abre [CutLess](http://127.0.0.1:8000/) o [iniciar sesión](http://127.0.0.1:8000/usuarios/login/). La aplicación está en `/cutless/` y el administrador Django en `/admin/`. Ctrl+C detiene el servidor.

`createsuperuser` solicita las credenciales que elijas; no hay contraseña predeterminada. Es opcional si ya tienes una cuenta. La base local y los resultados de prueba se excluyen del repositorio; en una instalación nueva, migrate crea las tablas sin importar los registros locales anteriores.

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
- [Ayuda: presentación y recorrido contextual](docs/CAMBIOS_VISUALES_AYUDA.md)
- [Estadísticas: presentación y claridad](docs/CAMBIOS_VISUALES_ESTADISTICAS.md)
- [Análisis: comparación y costos](docs/CAMBIOS_VISUALES_ANALISIS.md)
- [Plantillas: presentación, unidades y copias personales](docs/CAMBIOS_VISUALES_PLANTILLAS.md)
- [Presupuestos: revisión visual y claridad](docs/CAMBIOS_VISUALES_PRESUPUESTOS.md)
- [Proyectos: revisión visual y claridad](docs/CAMBIOS_VISUALES_PROYECTOS.md)
- [Clientes: revisión visual y claridad](docs/CAMBIOS_VISUALES_CLIENTES.md)
- [Materiales: revisión visual y claridad](docs/CAMBIOS_VISUALES_MATERIALES.md)

La base local y los archivos generados se excluyen del seguimiento de Git. Los commits anteriores conservan sus copias; no se reescribió el historial.

- [Instalación de dependencias desde la raíz](docs/CAMBIOS_DEPENDENCIAS.md)
- [Configuración inicial del espacio de trabajo](docs/CAMBIOS_CONFIGURACION_INICIAL.md)
- [Resultado legible y visor de tableros](docs/CAMBIOS_VISOR_TABLEROS.md)
- [Consistencia de colores y acciones](docs/CAMBIOS_CONSISTENCIA_ACCIONES.md)
- [Lupa de lectura compartida](docs/CAMBIOS_LUPA_LECTURA.md)
- [Visor del Historial: controles y armonía visual](docs/CAMBIOS_VISOR_HISTORIAL.md)
- [Leyenda compacta y legible en los planos PNG](docs/CAMBIOS_LEYENDA_PLANOS.md)

- [Reforma visual integral y navegación de tableros](docs/CAMBIOS_REFORMA_VISUAL.md)

- [Visor horizontal: disposición, cotas y correspondencia de piezas](docs/CAMBIOS_VISOR_HORIZONTAL.md)

- [Historial: mismo visor horizontal que el resultado](docs/CAMBIOS_HISTORIAL_HORIZONTAL.md)

- [Sistema compartido de botones y estados](docs/CAMBIOS_SISTEMA_BOTONES.md)

- [Paneles neutros y vista previa coherente](docs/CAMBIOS_PANELES_NEUTROS.md)

- [Revisión de exportaciones y duplicación](docs/CAMBIOS_EXPORTACIONES_Y_DUPLICACION.md)

- [Revisión de sesión y usabilidad](docs/CAMBIOS_REVISION_USABILIDAD.md)

- [Identificadores permanentes de optimización](docs/CAMBIOS_IDENTIFICADORES_PERMANENTES.md)

- [Nombres opcionales de los trabajos](docs/CAMBIOS_NOMBRES_OPTIMIZACIONES.md)

- [Corrección de precisión dimensional RNF-09 y pruebas de regresión](docs/CAMBIOS_PRECISION_DIMENSIONAL_RNF09.md)

- [Animación y escala de color del aprovechamiento](docs/CAMBIOS_ANIMACION_APROVECHAMIENTO.md)

- [Indicador de carga con el símbolo de CutLess](docs/CAMBIOS_CARGA_MARCA.md)

- [Modo oscuro: superficies cálidas y acento ámbar](docs/CAMBIOS_MODO_OSCURO_AMBAR.md)

- [Paleta clara, notificaciones y alcance de la lupa](docs/CAMBIOS_PALETA_CLARA_AVISOS_LUPA.md)

- [Jerarquía visual de eliminar y guardar](docs/CAMBIOS_JERARQUIA_ELIMINAR_GUARDAR.md)

- [Mensajes y ayuda progresiva de login y registro](docs/CAMBIOS_MENSAJES_LOGIN_REGISTRO.md)

- [Foco correcto en las filas de piezas](docs/CAMBIOS_FOCO_FILAS_PIEZAS.md)

- [Menú móvil y lupa reservada a escritorio](docs/CAMBIOS_MENU_LUPA_MOVIL.md)

- [Hosts permitidos por entorno](docs/CAMBIOS_HOSTS_ENTORNO.md)

- [Versión de Python para Render](docs/CAMBIOS_VERSION_PYTHON.md)

- [Servidor de producción y archivos estáticos](docs/CAMBIOS_SERVIDOR_ESTATICOS.md)

- [Preparación de producción: Render y Supabase](docs/PREPARACION_RENDER_SUPABASE.md)

- [Datos locales y archivos generados fuera de Git](docs/CAMBIOS_DATOS_FUERA_GIT.md)
