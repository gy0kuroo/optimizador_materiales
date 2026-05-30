"""Conversiones de unidades y simbolos para medidas."""

def convertir_a_cm(valor, unidad):
    """
    Convierte un valor de cualquier unidad a centímetros.
    
    Args:
        valor: Valor numérico a convertir
        unidad: Unidad de origen ('cm', 'm', 'mm', 'in', 'ft', 'pulgadas')
    
    Returns:
        Valor convertido a centímetros
    """
    # Normalizar 'pulgadas' a 'in' para compatibilidad
    if unidad == 'pulgadas':
        unidad = 'in'
    
    conversiones = {
        'cm': 1.0,           # 1 cm = 1 cm
        'm': 100.0,          # 1 m = 100 cm
        'mm': 0.1,           # 1 mm = 0.1 cm
        'in': 2.54,          # 1 pulgada = 2.54 cm
        'ft': 30.48,         # 1 pie = 30.48 cm
    }
    factor = conversiones.get(unidad, 1.0)
    return round(valor * factor, 2)

def convertir_desde_cm(valor_cm, unidad_destino):
    """
    Convierte un valor en centímetros a otra unidad.
    
    Args:
        valor_cm: Valor en centímetros
        unidad_destino: Unidad de destino ('cm', 'm', 'mm', 'in', 'ft', 'pulgadas')
    
    Returns:
        Valor convertido a la unidad destino
    """
    # Normalizar 'pulgadas' a 'in' para compatibilidad
    if unidad_destino == 'pulgadas':
        unidad_destino = 'in'
    
    conversiones = {
        'cm': 1.0,           # 1 cm = 1 cm
        'm': 0.01,           # 1 cm = 0.01 m
        'mm': 10.0,          # 1 cm = 10 mm
        'in': 1/2.54,        # 1 cm = 1/2.54 pulgadas
        'ft': 1/30.48,       # 1 cm = 1/30.48 pies
    }
    factor = conversiones.get(unidad_destino, 1.0)
    return round(valor_cm * factor, 2)

def obtener_simbolo_unidad(unidad):
    """
    Retorna el símbolo de la unidad para mostrar.
    """
    # Normalizar 'pulgadas' a 'in' para compatibilidad
    if unidad == 'pulgadas':
        unidad = 'in'
    
    simbolos = {
        'cm': 'cm',
        'm': 'm',
        'mm': 'mm',
        'in': 'in',
        'ft': 'ft',
    }
    return simbolos.get(unidad, 'cm')

def obtener_simbolo_area(unidad):
    """
    Retorna el símbolo de unidad al cuadrado para áreas.
    """
    # Normalizar 'pulgadas' a 'in' para compatibilidad
    if unidad == 'pulgadas':
        unidad = 'in'
    
    simbolos = {
        'cm': 'cm²',
        'm': 'm²',
        'mm': 'mm²',
        'in': 'in²',
        'ft': 'ft²',
    }
    return simbolos.get(unidad, 'cm²')
