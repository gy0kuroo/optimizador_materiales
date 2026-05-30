#!/usr/bin/env python
"""
Script de inicialización del proyecto CutLess
Ejecutar: python setup_project.py
Configura todo lo necesario para ejecutar la aplicación.
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cutless_project.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.contrib.auth.models import User


def check_database():
    """Verifica si las migraciones están aplicadas."""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM auth_user LIMIT 1")
        return True
    except Exception:
        return False


def run_migrations():
    """Ejecuta todas las migraciones pendientes."""
    print("📦 Ejecutando migraciones...")
    try:
        call_command('migrate', '--run-syncdb')
        print("✅ Migraciones completadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error en migraciones: {e}")
        return False


def create_superuser():
    """Crea un superuser si no existe."""
    if User.objects.filter(username='admin').exists():
        print("ℹ️  Superuser 'admin' ya existe")
        return
    
    print("\n👤 Crear superuser (dejar en blanco para saltar):")
    try:
        call_command('createsuperuser', interactive=True)
        print("✅ Superuser creado exitosamente")
    except KeyboardInterrupt:
        print("⏭️  Creación de superuser cancelada")


def main():
    """Ejecuta el setup completo."""
    print("=" * 60)
    print("🚀 CutLess - Configuración Inicial del Proyecto")
    print("=" * 60)
    
    # Verificar si la BD ya está configurada
    print("\n📊 Verificando estado de la base de datos...")
    if check_database():
        print("✅ La base de datos ya está configurada")
        return
    
    print("⚠️  La base de datos no está configurada")
    
    # Ejecutar migraciones
    if not run_migrations():
        print("\n❌ No se pudo completar la inicialización")
        sys.exit(1)
    
    # Ofrecer crear superuser
    try:
        create_superuser()
    except Exception as e:
        print(f"⚠️  Error al crear superuser: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ¡Setup completado!")
    print("=" * 60)
    print("\n🌐 Ahora puedes ejecutar:")
    print("   python manage.py runserver")
    print("\n📍 Accede a:")
    print("   Login: http://127.0.0.1:8000/usuarios/login/")
    print("   App:   http://127.0.0.1:8000/cutless/")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
