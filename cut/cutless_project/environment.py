"""Configuración por entorno, sin secretos compartidos en el código."""
import os
import secrets
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def configuracion_entorno(base_dir, environ=None):
    env = os.environ if environ is None else environ
    modo = env.get('CUTLESS_ENV', 'development').strip().lower()
    if modo not in ('development', 'production'):
        raise ImproperlyConfigured('CUTLESS_ENV debe ser development o production.')
    produccion = modo == 'production'
    clave = env.get('CUTLESS_SECRET_KEY', '').strip()
    if produccion:
        if len(clave) < 50 or len(set(clave)) < 5 or clave.startswith('django-insecure-'):
            raise ImproperlyConfigured('Producción requiere una CUTLESS_SECRET_KEY aleatoria y de al menos 50 caracteres.')
    elif not clave:
        archivo = Path(base_dir) / '.development_secret_key'
        try:
            with archivo.open('x', encoding='utf-8') as salida:
                salida.write(secrets.token_urlsafe(64))
        except FileExistsError:
            pass
        clave = archivo.read_text(encoding='utf-8').strip()
        if not clave:
            raise ImproperlyConfigured('La clave local está vacía. Elimina .development_secret_key para regenerarla.')

    hosts = [h.strip() for h in env.get('CUTLESS_ALLOWED_HOSTS', '' if produccion else 'localhost,127.0.0.1').split(',') if h.strip()]
    if produccion and (not hosts or any('*' in h or '://' in h or '/' in h for h in hosts)):
        raise ImproperlyConfigured('Producción requiere CUTLESS_ALLOWED_HOSTS con dominios o IP explícitos, sin comodines.')
    origenes = [o.strip() for o in env.get('CUTLESS_CSRF_TRUSTED_ORIGINS', '' if produccion else 'http://localhost:8000,http://127.0.0.1:8000').split(',') if o.strip()]
    if produccion and any(not o.startswith('https://') or '*' in o for o in origenes):
        raise ImproperlyConfigured('Los orígenes CSRF de producción deben usar HTTPS y no tener comodines.')
    proxy = env.get('CUTLESS_TRUST_PROXY_HEADERS', 'false').strip().lower()
    if proxy not in ('true', 'false', '1', '0'):
        raise ImproperlyConfigured('CUTLESS_TRUST_PROXY_HEADERS debe ser true o false.')
    return {
        'CUTLESS_ENV': modo,
        'SECRET_KEY': clave,
        'DEBUG': not produccion,
        'ALLOWED_HOSTS': hosts,
        'CSRF_TRUSTED_ORIGINS': origenes,
        'SESSION_COOKIE_SECURE': produccion,
        'CSRF_COOKIE_SECURE': produccion,
        'SECURE_SSL_REDIRECT': produccion,
        'SECURE_HSTS_SECONDS': 3600 if produccion else 0,
        'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https') if proxy in ('true', '1') else None,
    }
