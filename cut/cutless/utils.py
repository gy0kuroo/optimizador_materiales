"""
Fachada de compatibilidad: reexporta utilidades desde modulos especializados.

Modulos:
  - units.py    : conversiones y simbolos de medida
  - pieces.py   : parseo de piezas y mensajes al usuario
  - packing.py  : motor de corte FFD+BSSF
  - render.py   : graficos matplotlib (tableros y estadisticas)
  - exports/    : reportes PDF y Excel
  - services/   : persistencia y contexto de optimizaciones
"""

from .exports import (
    generar_excel,
    generar_excel_historial_costos,
    generar_excel_resumen_desperdicio,
    generar_pdf,
    generar_pdf_presupuesto,
    generar_pdf_resumen_desperdicio,
)
from .packing import (
    INFO_DESPERDICIO_CAMPOS,
    normalizar_info_desperdicio,
    optimizar_corte,
    pieza_cabe_en_tablero,
)
from .pieces import (
    mensaje_advertencia_piezas_no_colocadas,
    parsear_piezas_desde_texto,
)
from .render import (
    generar_grafico,
    generar_grafico_aprovechamiento,
    generar_grafico_desperdicio,
)
from .units import (
    convertir_a_cm,
    convertir_desde_cm,
    obtener_simbolo_area,
    obtener_simbolo_unidad,
)

__all__ = [
    'INFO_DESPERDICIO_CAMPOS',
    'convertir_a_cm',
    'convertir_desde_cm',
    'generar_excel',
    'generar_excel_historial_costos',
    'generar_excel_resumen_desperdicio',
    'generar_grafico',
    'generar_grafico_aprovechamiento',
    'generar_grafico_desperdicio',
    'generar_pdf',
    'generar_pdf_presupuesto',
    'generar_pdf_resumen_desperdicio',
    'mensaje_advertencia_piezas_no_colocadas',
    'normalizar_info_desperdicio',
    'obtener_simbolo_area',
    'obtener_simbolo_unidad',
    'optimizar_corte',
    'parsear_piezas_desde_texto',
    'pieza_cabe_en_tablero',
]
