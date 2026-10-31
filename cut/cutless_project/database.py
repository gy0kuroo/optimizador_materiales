"""Configuración de conexión sin abrir la base ni mostrar credenciales."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def configuracion_base_datos(base_dir, produccion=False, environ=None):
    env = os.environ if environ is None else environ
    motor = env.get('CUTLESS_DB_ENGINE', 'postgresql' if produccion else 'sqlite').strip().lower()
    if motor == 'sqlite' and not produccion:
        return {'ENGINE': 'django.db.backends.sqlite3',
                'NAME': Path(env.get('CUTLESS_DB_PATH', Path(base_dir) / 'db.sqlite3'))}
    if motor != 'postgresql':
        raise ImproperlyConfigured('CUTLESS_DB_ENGINE debe ser postgresql; sqlite solo se admite en desarrollo.')

    requeridas = ('CUTLESS_DB_NAME', 'CUTLESS_DB_USER', 'CUTLESS_DB_PASSWORD', 'CUTLESS_DB_HOST')
    faltantes = [nombre for nombre in requeridas if not env.get(nombre, '').strip()]
    if faltantes:
        raise ImproperlyConfigured('Faltan variables de PostgreSQL: ' + ', '.join(faltantes))
    try:
        puerto = int(env.get('CUTLESS_DB_PORT', '5432'))
        if not 1 <= puerto <= 65535:
            raise ValueError
    except ValueError:
        raise ImproperlyConfigured('CUTLESS_DB_PORT debe ser un puerto válido.') from None

    sslmode = env.get('CUTLESS_DB_SSLMODE', 'require').strip().lower()
    permitidos = ('require', 'verify-ca', 'verify-full') if produccion else ('disable', 'require', 'verify-ca', 'verify-full')
    if sslmode not in permitidos:
        raise ImproperlyConfigured('CUTLESS_DB_SSLMODE no es válido; producción requiere SSL.')
    opciones = {'sslmode': sslmode, 'connect_timeout': 10, 'prepare_threshold': None}
    if env.get('CUTLESS_DB_SSLROOTCERT'):
        opciones['sslrootcert'] = env['CUTLESS_DB_SSLROOTCERT']
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env['CUTLESS_DB_NAME'], 'USER': env['CUTLESS_DB_USER'],
        'PASSWORD': env['CUTLESS_DB_PASSWORD'], 'HOST': env['CUTLESS_DB_HOST'],
        'PORT': puerto, 'OPTIONS': opciones,
        'CONN_MAX_AGE': 0,
        'DISABLE_SERVER_SIDE_CURSORS': True,
    }
