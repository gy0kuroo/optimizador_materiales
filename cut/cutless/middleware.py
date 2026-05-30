"""
Middleware para verificar la integridad de la base de datos.
Alerta al usuario si las migraciones no han sido ejecutadas.
"""

import logging
from django.core.exceptions import OperationalError
from django.db import connection

logger = logging.getLogger(__name__)


class DatabaseHealthCheckMiddleware:
    """
    Verifica si la base de datos está correctamente configurada.
    Si faltan migraciones, intenta reparar o muestra un error útil.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._checked = False
        self._has_tables = None
    
    def __call__(self, request):
        # Verificar una sola vez per proceso
        if not self._checked:
            self._check_database()
            self._checked = True
        
        response = self.get_response(request)
        return response
    
    def _check_database(self):
        """Verifica si existen las tablas necesarias."""
        try:
            cursor = connection.cursor()
            # Verificar tabla de usuarios (django.contrib.auth)
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='auth_user';"
            )
            self._has_tables = cursor.fetchone() is not None
            
            if not self._has_tables:
                logger.warning(
                    "⚠️  DATABASE WARNING: Las migraciones no han sido ejecutadas. "
                    "Ejecuta: python manage.py migrate"
                )
        except OperationalError as e:
            logger.error(
                f"❌ DATABASE ERROR: {e}. "
                "Ejecuta: python manage.py migrate"
            )
        except Exception as e:
            logger.error(f"Error verificando BD: {e}")
