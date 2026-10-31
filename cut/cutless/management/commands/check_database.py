"""
Comando Django para verificar el estado de la base de datos.
Uso: python manage.py check_database
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, DatabaseError
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
        table_names = connection.introspection.table_names()
        
        required_tables = ['auth_user', 'cutless_material', 'usuarios_perfilusuario']
        missing = [t for t in required_tables if t not in table_names]
        
        return missing

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando base de datos...\n")
        
        try:
            missing = self.check_tables()
        except DatabaseError:
            raise CommandError('No se pudo consultar la base de datos. Revisa su conexión y configuración privadas.') from None
        
        if not missing:
            self.stdout.write(
                self.style.SUCCESS('Las tres tablas esenciales existen; no se valida todo el esquema ni las migraciones pendientes.')
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
            except Exception:
                self.stdout.write(
                    self.style.ERROR('Error al ejecutar migraciones; revisar el estado y la configuración privada.')
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
