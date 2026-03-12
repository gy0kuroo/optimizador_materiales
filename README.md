# OptiCut - Optimizador de Cortes de Madera

Sistema web para optimizar el corte de tableros de madera utilizando el algoritmo First Fit Decreasing (FFD).

## Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

### 1. Clonar o copiar el proyecto

```bash
# Si tienes el proyecto en un repositorio
git clone <url-del-repositorio>
cd optimizador_materiales/opti

# O simplemente copia la carpeta 'opti' a tu nuevo PC
```

### 2. Crear un entorno virtual (recomendado)

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

Esto instalará automáticamente:
- Django 5.2.8
- matplotlib 3.9.2 (y sus dependencias como numpy)
- reportlab 4.2.5
- Pillow 11.0.0
- sqlparse 0.5.1
- tzdata 2024.2

### 4. Configurar la base de datos

```bash
# Crear las migraciones
python manage.py makemigrations

# Aplicar las migraciones
python manage.py migrate

# Crear un superusuario (opcional, para acceder al panel de administración)
python manage.py createsuperuser
```

### 5. Ejecutar el servidor de desarrollo

```bash
python manage.py runserver
```

El proyecto estará disponible en: `http://127.0.0.1:8000/`

## Estructura del Proyecto

```
opti/
├── manage.py              # Script de gestión de Django
├── requirements.txt       # Dependencias del proyecto
├── db.sqlite3            # Base de datos (se crea automáticamente)
├── opti/                 # Configuración del proyecto
│   ├── settings.py       # Configuración de Django
│   ├── urls.py          # URLs principales
│   └── wsgi.py          # Configuración WSGI
├── opticut/             # App principal (optimizador)
│   ├── models.py        # Modelos de datos
│   ├── views.py         # Vistas (lógica de negocio)
│   ├── forms.py         # Formularios
│   ├── utils.py         # Utilidades (generación de gráficos y PDFs)
│   ├── templates/       # Plantillas HTML
│   └── static/          # Archivos estáticos (CSS, JS, imágenes)
└── usuarios/            # App de usuarios
    ├── models.py        # Modelo de perfil de usuario
    ├── views.py         # Vistas de autenticación
    └── templates/       # Plantillas de login/registro
```

## Características

- ✅ Optimización de cortes usando algoritmo FFD
- ✅ Soporte para múltiples unidades (cm, m, pulgadas, pies)
- ✅ Generación de gráficos visuales de los cortes
- ✅ Exportación a PDF con todos los tableros
- ✅ Descarga de imágenes PNG individuales
- ✅ Historial de optimizaciones
- ✅ Sistema de favoritos
- ✅ Estadísticas y análisis
- ✅ Cálculo de tiempo de corte
- ✅ Sistema de tutorial interactivo
- ✅ Modo claro/oscuro

## Solución de Problemas

### Error al instalar dependencias

Si encuentras errores al instalar, asegúrate de tener:
- Python 3.8 o superior
- pip actualizado: `python -m pip install --upgrade pip`

### Error con matplotlib en Windows

Si tienes problemas con matplotlib en Windows, puede ser necesario instalar Visual C++ Redistributable:
- Descarga desde: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Error de migraciones

Si la base de datos no existe o hay errores:
```bash
# Eliminar la base de datos antigua (si existe)
rm db.sqlite3  # Linux/Mac
del db.sqlite3  # Windows

# Recrear desde cero
python manage.py makemigrations
python manage.py migrate
```

### Problemas con archivos estáticos

Si los estilos CSS no se cargan:
```bash
python manage.py collectstatic
```

## Notas Importantes

- El proyecto usa SQLite por defecto (base de datos en archivo)
- Los archivos generados (PDFs, imágenes) se guardan en la carpeta `media/`
- El `SECRET_KEY` en `settings.py` es para desarrollo. En producción, usa variables de entorno.

## Soporte

Para más información o problemas, revisa la documentación de Django: https://docs.djangoproject.com/

