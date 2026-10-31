import io
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from django.db import OperationalError

from cutless_project.database import configuracion_base_datos
from cutless.middleware import DatabaseHealthCheckMiddleware
from cutless.management.commands.check_database import Command


class DatabaseConfigTests(SimpleTestCase):
    def setUp(self):
        self.env = dict(CUTLESS_DB_ENGINE='postgresql', CUTLESS_DB_NAME='postgres',
                        CUTLESS_DB_HOST='db.example.invalid', CUTLESS_DB_USER='test',
                        CUTLESS_DB_PASSWORD='test@:"/ %')

    def test_sqlite_de_desarrollo_conserva_ruta(self):
        self.assertEqual(configuracion_base_datos(Path('cut'), environ={})['NAME'], Path('cut/db.sqlite3'))
        self.assertEqual(configuracion_base_datos('.', environ={'CUTLESS_DB_PATH': 'otra.db'})['NAME'], Path('otra.db'))

    def test_postgresql_conserva_password_sin_parsear_url(self):
        config = configuracion_base_datos('.', True, self.env)
        self.assertEqual(config['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(config['PASSWORD'], self.env['CUTLESS_DB_PASSWORD'])
        self.assertEqual(config['OPTIONS']['sslmode'], 'require')
        self.assertIsNone(config['OPTIONS']['prepare_threshold'])
        self.assertTrue(config['DISABLE_SERVER_SIDE_CURSORS'])
        self.assertEqual(config['CONN_MAX_AGE'], 0)

    def test_produccion_no_cae_en_sqlite(self):
        for env in ({}, {'CUTLESS_DB_ENGINE': 'sqlite'}):
            with self.subTest(env=env), self.assertRaises(ImproperlyConfigured):
                configuracion_base_datos('.', True, env)

    def test_configuracion_incompleta_no_revela_credenciales(self):
        for nombre in ('CUTLESS_DB_NAME', 'CUTLESS_DB_USER', 'CUTLESS_DB_PASSWORD', 'CUTLESS_DB_HOST'):
            env = dict(self.env)
            del env[nombre]
            with self.assertRaises(ImproperlyConfigured) as error:
                configuracion_base_datos('.', True, env)
            self.assertNotIn(self.env['CUTLESS_DB_PASSWORD'], str(error.exception))
            self.assertIn(nombre, str(error.exception))

    def test_ssl_y_puerto_validos(self):
        config = configuracion_base_datos('.', True, dict(self.env, CUTLESS_DB_PORT='6543',
            CUTLESS_DB_SSLMODE='verify-full', CUTLESS_DB_SSLROOTCERT='/certificado.crt'))
        self.assertEqual(config['PORT'], 6543)
        self.assertEqual(config['OPTIONS']['sslrootcert'], '/certificado.crt')
        for valor in ('disable', 'prefer', 'invalido'):
            with self.assertRaises(ImproperlyConfigured):
                configuracion_base_datos('.', True, dict(self.env, CUTLESS_DB_SSLMODE=valor))
        for valor in ('0', '-1', '65536', 'texto'):
            with self.assertRaises(ImproperlyConfigured):
                configuracion_base_datos('.', True, dict(self.env, CUTLESS_DB_PORT=valor))

    def test_motor_invalido_no_se_ignora(self):
        with self.assertRaises(ImproperlyConfigured):
            configuracion_base_datos('.', environ={'CUTLESS_DB_ENGINE': 'mysql'})

    def test_backend_postgresql_carga_adaptador_sin_conectar(self):
        from django.db.utils import ConnectionHandler
        handler = ConnectionHandler({'default': configuracion_base_datos('.', True, self.env)})
        wrapper = handler['default']
        parametros = wrapper.get_connection_params()
        self.assertEqual(parametros['sslmode'], 'require')
        self.assertEqual(parametros['password'], self.env['CUTLESS_DB_PASSWORD'])
        self.assertIsNone(parametros['prepare_threshold'])
        self.assertIsNone(wrapper.connection)

    def test_comando_oculta_error_de_conexion(self):
        from django.core.management.base import CommandError
        command = Command(stdout=io.StringIO())
        with patch.object(command, 'check_tables', side_effect=OperationalError('credencial-ficticia')):
            with self.assertRaises(CommandError) as error:
                command.handle(fix=False)
        self.assertNotIn('credencial-ficticia', str(error.exception))

    def test_introspeccion_sustituye_sql_especifico(self):
        tablas = ['auth_user', 'cutless_material', 'usuarios_perfilusuario']
        with patch('cutless.middleware.connection') as db:
            db.introspection.table_names.return_value = tablas
            middleware = DatabaseHealthCheckMiddleware(lambda request: 'ok')
            self.assertEqual(middleware(None), 'ok')
            self.assertEqual(middleware(None), 'ok')
            self.assertTrue(middleware._has_tables)
            db.introspection.table_names.assert_called_once()
            db.cursor.assert_not_called()
        with patch('cutless.management.commands.check_database.connection') as db:
            db.introspection.table_names.return_value = tablas
            self.assertEqual(Command().check_tables(), [])
            db.introspection.table_names.return_value = ['auth_user']
            self.assertEqual(Command().check_tables(), ['cutless_material', 'usuarios_perfilusuario'])
            db.cursor.assert_not_called()

    def test_fallo_de_conexion_no_filtra_detalles(self):
        with patch('cutless.middleware.connection') as db:
            db.introspection.table_names.side_effect = OperationalError('credencial-ficticia')
            with self.assertLogs('cutless.middleware', level='ERROR') as logs:
                self.assertEqual(DatabaseHealthCheckMiddleware(lambda request: 'ok')(None), 'ok')
        self.assertNotIn('credencial-ficticia', ''.join(logs.output))

    def test_comando_sin_fix_no_ejecuta_migraciones(self):
        command = Command(stdout=io.StringIO())
        with patch.object(command, 'check_tables', return_value=['auth_user']), \
             patch('cutless.management.commands.check_database.call_command') as migrate:
            command.handle(fix=False)
            migrate.assert_not_called()
