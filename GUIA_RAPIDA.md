# 🚀 Guía de Instalación Rápida - CutLess

## Para usuarios nuevos

Sigue estos pasos EXACTAMENTE en orden después de descargar o clonar el proyecto:

### Paso 1: Entrar a la carpeta del proyecto

```bash
cd cut
```

### Paso 2: Crear entorno virtual (recomendado)

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

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: ⚠️ INICIALIZAR LA BASE DE DATOS (¡NO OMITIR!)

**Windows (más fácil):**
```bash
setup_project.bat
```

**Todas las plataformas:**
```bash
python setup_project.py
```

**O manualmente:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Paso 5: Ejecutar el servidor

```bash
python manage.py runserver
```

### Paso 6: Acceder a la aplicación

- 🌐 **Login:** http://127.0.0.1:8000/usuarios/login/
- 📊 **App:** http://127.0.0.1:8000/cutless/ (requiere estar logueado)

---

## Si algo falla...

### Error: "no such table: auth_user"

Significa que faltó ejecutar el paso 4. Soluciona con:

```bash
python manage.py check_database --fix
```

### Error: "No module named 'django'"

Significa que no instalaste las dependencias (paso 3). Ejecuta:

```bash
pip install -r requirements.txt
```

### Error: "No such file or directory: 'manage.py'"

Asegúrate de estar en la carpeta correcta:

```bash
cd cut  # Asegúrate de estar en esta carpeta
```

---

## 📞 Soporte Rápido

| Problema | Solución |
|----------|----------|
| BD no inicializada | `python setup_project.py` |
| Verificar estado BD | `python manage.py check_database` |
| Reparar BD | `python manage.py check_database --fix` |
| Crear usuario admin | `python manage.py createsuperuser` |

---

## ✅ Checklist post-instalación

- [ ] Entorno virtual activado
- [ ] Dependencias instaladas (`pip list` debe mostrar Django, etc.)
- [ ] Base de datos inicializada (no hay error "no such table")
- [ ] Servidor ejecutándose (`http://127.0.0.1:8000/usuarios/login/` accesible)
- [ ] Puedes loguear con las credenciales creadas

¡Listo! 🎉
