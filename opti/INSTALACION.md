# Guía Rápida de Instalación

## Pasos para ejecutar el proyecto en un nuevo PC

### 1. Requisitos
- Python 3.8 o superior
- pip (viene con Python)

### 2. Instalación rápida

```bash
# 1. Navegar a la carpeta del proyecto
cd opti

# 2. Crear entorno virtual (recomendado)
python -m venv venv

# 3. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instalar todas las dependencias
pip install -r requirements.txt

# 5. Crear base de datos
python manage.py migrate

# 6. Ejecutar servidor
python manage.py runserver
```

### 3. Verificar instalación

Abre tu navegador en: `http://127.0.0.1:8000/`

Si ves la página de login, ¡todo está funcionando correctamente!

## Dependencias incluidas en requirements.txt

✅ **Django 5.2.8** - Framework web  
✅ **matplotlib 3.9.2** - Generación de gráficos  
✅ **reportlab 4.2.5** - Generación de PDFs  
✅ **Pillow 11.0.0** - Procesamiento de imágenes  
✅ **sqlparse 0.5.1** - Utilidades Django  
✅ **tzdata 2024.2** - Zonas horarias  

**Nota:** Las dependencias secundarias (como numpy para matplotlib) se instalan automáticamente.

## Problemas comunes

### "No se encuentra el módulo django"
- Asegúrate de haber activado el entorno virtual
- Verifica que pip instaló correctamente: `pip list`

### "Error al instalar matplotlib"
- En Windows, puede necesitar Visual C++ Redistributable
- Actualiza pip: `python -m pip install --upgrade pip`

### "No such table" o errores de base de datos
- Ejecuta: `python manage.py migrate`

