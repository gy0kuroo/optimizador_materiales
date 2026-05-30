# CutLess - Optimizador de Cortes de Tableros

Sistema web Django para optimizar el corte de tableros (madera, melamina, etc.) usando el algoritmo **FFD (First Fit Decreasing)** con colocación en rectángulos libres (BSSF).

> ⚡ **¿Primera vez?** Lee [GUIA_RAPIDA.md](GUIA_RAPIDA.md) para una instalación rápida paso a paso.

## Requisitos previos

- Python 3.10 o superior (probado con 3.13)
- pip

## Instalación

### 1. Clonar o copiar el proyecto

```bash
git clone <url-del-repositorio>
cd optimizador_materiales/cut
```

### 2. Entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Dependencias principales: Django 5.2, matplotlib, reportlab, Pillow, openpyxl.

### 4. Inicializar la base de datos

⚠️ **¡IMPORTANTE!** Este paso es crítico y debe ejecutarse siempre después de instalar o clonar el proyecto.

#### Opción A: Script automático (RECOMENDADO)

```bash
python setup_project.py
```

Este script:
- ✅ Verifica si la BD está inicializada
- ✅ Ejecuta todas las migraciones
- ✅ Ofrece crear un superuser

#### Opción B: Comandos manuales

```bash
python manage.py migrate
python manage.py createsuperuser   # opcional
```

#### Verificar el estado:

```bash
# Solo verificar
python manage.py check_database

# Verificar y reparar automáticamente
python manage.py check_database --fix
```

### 5. Ejecutar el servidor

```bash
python manage.py runserver
```

- **Login:** `http://127.0.0.1:8000/usuarios/login/`
- **App principal (requiere sesión):** `http://127.0.0.1:8000/cutless/`

Las URLs antiguas `/opticut/...` redirigen a `/cutless/...`.

## Solución de Problemas

### Error: "no such table: auth_user"

Este error significa que las migraciones no se han ejecutado. Solución:

```bash
# Opción 1: Script automático
python setup_project.py

# Opción 2: Comando de reparación
python manage.py check_database --fix

# Opción 3: Migraciones manuales
python manage.py migrate
```

Luego reinicia el servidor:
```bash
python manage.py runserver
```

## Estructura del proyecto

```
cut/
├── manage.py
├── requirements.txt
├── db.sqlite3                 # SQLite (desarrollo)
├── cutless_project/         # Settings, URLs raíz, WSGI
├── cutless/                   # App principal
│   ├── models.py              # Optimizacion, TableroOptimizacion, Material, Cliente, etc.
│   ├── forms.py
│   ├── utils.py               # Algoritmo FFD, gráficos, PDF/Excel
│   ├── services/
│   │   └── optimization.py    # Persistencia y descargas de resultados
│   ├── views/                 # Vistas divididas por módulo
│   │   ├── optimization.py    # Index, resultado, editar, duplicar
│   │   ├── historial.py
│   │   ├── exports.py         # PDF, Excel, PNG
│   │   ├── analytics.py       # Estadísticas, costos
│   │   ├── materials.py
│   │   ├── clients.py
│   │   ├── budgets.py
│   │   ├── projects.py
│   │   └── plantillas.py
│   ├── templates/cutless/
│   ├── static/cutless/
│   ├── migrations/
│   └── tests.py
├── usuarios/                  # Login, registro, perfil, permisos
└── media/                     # PDFs, imágenes de tableros (generados)
```

## Características

- Optimización FFD + rectángulos libres, con rotación opcional y margen de corte (kerf)
- Unidades: cm, m, mm, pulgadas (`in`), pies
- Piezas con nombre (`nombre,ancho,alto,cantidad`) o formato legacy (`ancho,alto,cantidad`)
- Gráficos por tablero con leyenda detallada (número, nombre, medidas, cantidad, color)
- **Persistencia de resultados:** tableros, estadísticas y PDF guardados en BD/archivos
- Exportación: PDF, Excel y PNG (`optimizacion_N.ext` según número en historial)
- Historial, favoritos, estadísticas, tiempo de corte estimado
- Materiales, clientes, presupuestos, proyectos y plantillas
- Modo claro/oscuro, tutorial, notificaciones

## Tests

```bash
python manage.py test cutless.tests
```

## Solución de problemas

### Error con matplotlib en Windows

Puede requerir [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe).

### Recrear base de datos

```bash
# Windows
del db.sqlite3
python manage.py migrate
```

### Archivos estáticos en producción

```bash
python manage.py collectstatic
```

### Acceso sin sesión

Todas las rutas bajo `/cutless/` requieren login. Si accedes sin autenticarte, se redirige a `/usuarios/login/`.

## Notas

- SQLite por defecto; en producción usar PostgreSQL/MySQL y variables de entorno para `SECRET_KEY` y `DEBUG`.
- Los archivos generados viven en `media/` (`pdfs/`, `optimizaciones/tableros/`).
- Registros antiguos sin resultado persistido se regeneran al abrir el resultado o descargar.

## Documentación

- Django: https://docs.djangoproject.com/
