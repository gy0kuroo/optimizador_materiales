"""
Middleware para verificar la integridad de la base de datos.
Alerta al usuario si las migraciones no han sido ejecutadas.
"""

import logging
from django.db import connection, OperationalError

logger = logging.getLogger(__name__)


class DatabaseHealthCheckMiddleware:
    """
    Verifica si la base de datos está correctamente configurada.
    Solo informa; no intenta reparar ni ejecuta migraciones.
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
            self._has_tables = 'auth_user' in connection.introspection.table_names()
            
            if not self._has_tables:
                logger.warning(
                    "⚠️  DATABASE WARNING: Las migraciones no han sido ejecutadas. "
                    "Ejecuta: python manage.py migrate"
                )
        except OperationalError:
            logger.error(
                "DATABASE ERROR: no se pudo consultar el estado de la base de datos."
            )
        except Exception:
            logger.error('Error verificando la base de datos; revisar su configuración privada.')
