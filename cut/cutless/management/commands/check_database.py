"""
Comando Django para verificar el estado de la base de datos.
Uso: python manage.py check_database
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Verifica y repara el estado de la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Ejecuta las migraciones automáticamente si faltan'
        )

    def check_tables(self):
        """Verifica si existen las tablas necesarias."""
        cursor = connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        required_tables = ['auth_user', 'cutless_material', 'usuarios_usuarioextendido']
        missing = [t for t in required_tables if t not in table_names]
        
        return missing

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando base de datos...\n")
        
        missing = self.check_tables()
        
        if not missing:
            self.stdout.write(
                self.style.SUCCESS('✅ La base de datos está correctamente configurada')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'⚠️  Tablas faltantes: {", ".join(missing)}')
        )
        
        if options['fix']:
            self.stdout.write('🔧 Ejecutando migraciones...')
            try:
                call_command('migrate', '--run-syncdb')
                self.stdout.write(
                    self.style.SUCCESS('✅ Migraciones completadas exitosamente')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error en migraciones: {e}')
                )
        else:
            self.stdout.write('\n💡 Para reparar, ejecuta:')
            self.stdout.write(
                self.style.WARNING('   python manage.py check_database --fix')
            )
            self.stdout.write('   o')
            self.stdout.write(
                self.style.WARNING('   python manage.py migrate')
            )
