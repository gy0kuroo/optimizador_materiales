"""Parseo de piezas y mensajes al usuario."""
from collections import Counter

from .units import convertir_a_cm, convertir_desde_cm, obtener_simbolo_unidad

def parsear_piezas_desde_texto(texto_piezas, unidad_medida='cm'):
    """
    Parsea líneas de piezas guardadas en Optimizacion o Plantilla.

    Formatos soportados:
    - nombre,ancho,alto,cantidad
    - ancho,alto,cantidad (legacy, sin nombre)

    Returns:
        Lista de dicts con claves: nombre, ancho, alto, cantidad, ancho_cm, alto_cm
    """
    piezas = []
    if not texto_piezas:
        return piezas

    for linea in texto_piezas.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        partes = [p.strip() for p in linea.split(',')]
        try:
            if len(partes) == 4:
                nombre, ancho_s, alto_s, cant_s = partes
            elif len(partes) == 3:
                nombre = f'Pieza {len(piezas) + 1}'
                ancho_s, alto_s, cant_s = partes
            else:
                continue

            ancho = float(ancho_s)
            alto = float(alto_s)
            cantidad = int(cant_s)
            piezas.append({
                'nombre': (nombre or f'Pieza {len(piezas) + 1}').strip(),
                'ancho': ancho,
                'alto': alto,
                'cantidad': cantidad,
                'ancho_cm': convertir_a_cm(ancho, unidad_medida),
                'alto_cm': convertir_a_cm(alto, unidad_medida),
            })
        except (ValueError, TypeError):
            continue

    return piezas

def mensaje_advertencia_piezas_no_colocadas(info_desperdicio, unidad='cm'):
    """
    Mensaje para el usuario cuando hubo piezas omitidas por no caber en el tablero.
    Devuelve None si no hay piezas omitidas.
    """
    omitidas = (info_desperdicio or {}).get('piezas_no_colocadas') or []
    if not omitidas:
        return None

    solicitadas = (info_desperdicio or {}).get('num_piezas_solicitadas')
    colocadas = (info_desperdicio or {}).get('num_piezas_colocadas')
    simbolo = obtener_simbolo_unidad(unidad)
    cuenta = Counter()
    for p in omitidas:
        key = (p.get('nombre', 'Pieza'), float(p.get('ancho_cm', 0)), float(p.get('alto_cm', 0)))
        cuenta[key] += 1
    partes_desc = []
    for (nombre, aw, ah), cnt in cuenta.items():
        wu = round(convertir_desde_cm(aw, unidad), 2)
        hu = round(convertir_desde_cm(ah, unidad), 2)
        partes_desc.append(f"{nombre} ×{cnt} ({wu}×{hu} {simbolo})")
    partes_desc.sort()
    max_items = 12
    texto = "; ".join(partes_desc[:max_items])
    if len(partes_desc) > max_items:
        texto += f"; …(+{len(partes_desc) - max_items})"
    sufix = ""
    if solicitadas is not None and colocadas is not None:
        sufix = f" Piezas en el plano: {colocadas} de {solicitadas}."
    elif colocadas is not None:
        sufix = f" Piezas en el plano: {colocadas}."
    return (
        f"No se pudieron colocar {len(omitidas)} pieza(s) (dimensiones mayores que el tablero en una sola orientación válida): {texto}.{sufix}"
    )
