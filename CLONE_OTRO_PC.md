# 📥 Instrucciones para Clonar en Otro PC

## Paso 1: Clonar el repositorio

```bash
git clone <URL-del-repositorio>
cd optimizador_materiales
```

## Paso 2: Entrar a la carpeta del proyecto

```bash
cd cut
```

## Paso 3: Crear y activar entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

## Paso 4: Instalar dependencias

```bash
pip install -r requirements.txt
```

## Paso 5: ⚠️ CONFIGURAR LA BASE DE DATOS (¡CRÍTICO!)

**Opción A - Script automático (RECOMENDADO):**

Windows:
```bash
setup_project.bat
```

Cualquier plataforma:
```bash
python setup_project.py
```

**Opción B - Manual:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

## Paso 6: Ejecutar el servidor

```bash
python manage.py runserver
```

✅ La aplicación estará disponible en: http://127.0.0.1:8000/usuarios/login/

---

## ✅ Checklist - Todo debe funcionar sin problemas

- [ ] Git clone completado sin errores
- [ ] Estás en la carpeta `cut/`
- [ ] Entorno virtual creado y activado
- [ ] `pip install -r requirements.txt` completado sin errores
- [ ] `python setup_project.py` ejecutado exitosamente
- [ ] Servidor iniciado en http://127.0.0.1:8000/
- [ ] Accedes a http://127.0.0.1:8000/usuarios/login/ sin errores

---

## 🔍 Verificación rápida

Si algo falla, ejecuta:

```bash
# Verificar estado de la BD
python manage.py check_database

# Reparar automáticamente
python manage.py check_database --fix

# Ver estado del proyecto
python manage.py check
```

---

## 📝 Notas importantes

- **db.sqlite3 NO se versionan** (está en .gitignore) - se crea automáticamente con `migrate`
- **La carpeta `media/`** se crea automáticamente (contiene PDFs y gráficos generados)
- **Entorno virtual (`venv/`)** NO se versionan - crear siempre en cada clon
- **Credenciales**: Crea un usuario admin con `python manage.py createsuperuser`

---

## 🚨 Si aún así hay problemas

1. Verifica que tengas Python 3.10+ instalado:
   ```bash
   python --version
   ```

2. Si ves errores de módulos, reinstala dependencias:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. Si hay conflictos de migraciones, limpia:
   ```bash
   python manage.py migrate --run-syncdb
   ```

¡Listo! 🎉
