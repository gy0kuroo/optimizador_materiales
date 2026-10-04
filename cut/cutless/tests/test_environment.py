import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from cutless_project.environment import configuracion_entorno


class ConfiguracionEntornoTests(SimpleTestCase):
    def setUp(self):
        self.env = {
            'CUTLESS_ENV': 'production',
            'CUTLESS_SECRET_KEY': 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'CUTLESS_ALLOWED_HOSTS': 'cutless.example.com',
            'CUTLESS_CSRF_TRUSTED_ORIGINS': 'https://cutless.example.com',
        }

    def test_produccion_activa_seguridad(self):
        config = configuracion_entorno(Path('.'), self.env)
        self.assertFalse(config['DEBUG'])
        for opcion in ('SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'SECURE_SSL_REDIRECT'):
            self.assertTrue(config[opcion])
        self.assertEqual(config['SECURE_HSTS_SECONDS'], 3600)
        self.assertIsNone(config['SECURE_PROXY_SSL_HEADER'])
        self.assertEqual(config['ALLOWED_HOSTS'], ['cutless.example.com'])

    def test_produccion_rechaza_clave_ausente_debil_o_insegura(self):
        for clave in ('', 'corta', 'x' * 60, 'django-insecure-' + 'abcdef0123456789' * 4):
            with self.subTest(clave=clave):
                with self.assertRaises(ImproperlyConfigured):
                    configuracion_entorno(Path('.'), dict(self.env, CUTLESS_SECRET_KEY=clave))

    def test_produccion_rechaza_hosts_vacios_o_comodines(self):
        for hosts in ('', '*', '*.example.com', 'https://example.com'):
            with self.subTest(hosts=hosts):
                with self.assertRaises(ImproperlyConfigured):
                    configuracion_entorno(Path('.'), dict(self.env, CUTLESS_ALLOWED_HOSTS=hosts))

    def test_produccion_rechaza_csrf_http_o_comodin(self):
        for origen in ('http://example.com', 'https://*.example.com'):
            with self.subTest(origen=origen):
                with self.assertRaises(ImproperlyConfigured):
                    configuracion_entorno(Path('.'), dict(self.env, CUTLESS_CSRF_TRUSTED_ORIGINS=origen))

    def test_proxy_se_activa_solo_explicitamente(self):
        config = configuracion_entorno(Path('.'), dict(self.env, CUTLESS_TRUST_PROXY_HEADERS='true'))
        self.assertEqual(config['SECURE_PROXY_SSL_HEADER'], ('HTTP_X_FORWARDED_PROTO', 'https'))
        with self.assertRaises(ImproperlyConfigured):
            configuracion_entorno(Path('.'), dict(self.env, CUTLESS_TRUST_PROXY_HEADERS='talvez'))

    def test_modo_desconocido_no_cae_en_desarrollo(self):
        with self.assertRaises(ImproperlyConfigured):
            configuracion_entorno(Path('.'), dict(self.env, CUTLESS_ENV='produccion'))

    def test_clave_local_es_aleatoria_y_persistente(self):
        with tempfile.TemporaryDirectory(prefix='cutless-key-test-') as tmp:
            primero = configuracion_entorno(tmp, {})
            segundo = configuracion_entorno(tmp, {})
            self.assertEqual(primero['SECRET_KEY'], segundo['SECRET_KEY'])
            self.assertGreaterEqual(len(primero['SECRET_KEY']), 50)
            self.assertTrue(primero['DEBUG'])
            self.assertFalse(primero['SESSION_COOKIE_SECURE'])
            self.assertEqual(primero['ALLOWED_HOSTS'], ['localhost', '127.0.0.1'])
