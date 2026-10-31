"""Comparación de datos guardados; no ejecuta el optimizador ni escribe registros."""
from collections import Counter
from decimal import Decimal, InvalidOperation
from ..units import convertir_a_cm
from ..board_presets import descripcion_material


def piezas_normalizadas(opt):
    if opt.unidad_medida not in ('cm', 'm', 'mm', 'in', 'ft'):
        return None
    piezas = Counter()
    try:
        for linea in opt.piezas.splitlines():
            if not linea.strip():
                continue
            partes = [parte.strip() for parte in linea.split(',')]
            if len(partes) == 3:
                partes.insert(0, 'Pieza')
            if len(partes) != 4:
                return None
            nombre, ancho, alto, cantidad = partes
            w, h = Decimal(ancho), Decimal(alto)
            n = int(cantidad)
            if not nombre or not w.is_finite() or not h.is_finite() or w <= 0 or h <= 0 or n <= 0:
                return None
            w = Decimal(str(convertir_a_cm(float(w), opt.unidad_medida))).quantize(Decimal('.01'))
            h = Decimal(str(convertir_a_cm(float(h), opt.unidad_medida))).quantize(Decimal('.01'))
            if w <= 0 or h <= 0:
                return None
            piezas[(' '.join(nombre.casefold().split()), w, h)] += n
    except (ValueError, InvalidOperation, OverflowError):
        return None
    return piezas or None


def comparar_trabajos(a, b):
    pa, pb = piezas_normalizadas(a), piezas_normalizadas(b)
    equivalentes = pa is not None and pb is not None and pa == pb
    if pa is None or pb is None:
        motivo = 'No se pudo verificar el listado de piezas de alguno de los planes. Revisa sus datos antes de elegir una alternativa.'
    elif not equivalentes:
        motivo = 'Las piezas, sus medidas o cantidades son diferentes. Esta comparación es informativa: no recomienda una alternativa para el mismo trabajo.'
    else:
        motivo = 'Ambos planes solicitan las mismas piezas y cantidades, aunque cambien el orden o la unidad de medida.'

    def metricas(opt, piezas):
        area = Decimal(str(opt.ancho_tablero)) * Decimal(str(opt.alto_tablero)) * opt.num_tableros / 10000
        solicitada = sum((w * h * n for (_, w, h), n in piezas.items()), Decimal(0)) / 10000 if piezas else None
        sobrante = area - solicitada if solicitada is not None and area >= solicitada else None
        return {'sierra_mm': Decimal(str(opt.margen_corte)) * 10, 'material': area, 'piezas': solicitada, 'fuera_piezas': sobrante,
                'cantidad': sum(piezas.values()) if piezas else None, 'costo': opt.get_costo_total()}

    ma, mb = metricas(a, pa), metricas(b, pb)
    ma['material_descripcion'], mb['material_descripcion'] = descripcion_material(a), descripcion_material(b)
    diferencia_area = mb['material'] - ma['material']
    diferencia_costo = mb['costo'] - ma['costo'] if ma['costo'] is not None and mb['costo'] is not None else None
    conclusiones = []
    if equivalentes:
        if diferencia_area:
            menor = 'B' if diferencia_area < 0 else 'A'
            cantidad = f'{abs(diferencia_area):.2f}'.replace('.', ',')
            conclusiones.append(f'La alternativa {menor} necesita {cantidad} m² menos de material en tableros completos para las mismas piezas.')
        else:
            conclusiones.append('Ambas alternativas necesitan la misma superficie de material en tableros completos.')
        if a.num_tableros != b.num_tableros:
            menor = 'B' if b.num_tableros < a.num_tableros else 'A'
            conclusiones.append(f'La alternativa {menor} utiliza {abs(b.num_tableros - a.num_tableros)} tablero(s) menos. Revisa también sus tamaños: menos tableros no siempre significa menos material.')
        if diferencia_costo is not None:
            if diferencia_costo:
                menor = 'B' if diferencia_costo < 0 else 'A'
                importe = f'{abs(diferencia_costo):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
                conclusiones.append(f'La alternativa {menor} tiene un costo estimado ${importe} menor, según los precios y la mano de obra guardados.')
            else:
                conclusiones.append('El costo estimado guardado es igual en ambas alternativas.')
        else:
            conclusiones.append('No se puede comparar el costo: falta el precio en alguna alternativa. Un precio ausente no se interpreta como cero.')
    cambios = []
    if (a.ancho_tablero, a.alto_tablero) != (b.ancho_tablero, b.alto_tablero): cambios.append('tamaño del tablero')
    if ma['material_descripcion']['identidad'] != mb['material_descripcion']['identidad']:
        cambios.append('material o procedencia de su selección')
    if a.margen_corte != b.margen_corte: cambios.append('ancho de sierra')
    if a.permitir_rotacion != b.permitir_rotacion: cambios.append('permiso de rotación')
    if a.precio_tablero != b.precio_tablero: cambios.append('precio por tablero')
    if a.mano_obra != b.mano_obra: cambios.append('mano de obra')
    filas = []
    for nombre, w, h in sorted(set(pa or {}) | set(pb or {})):
        clave = (nombre, w, h)
        filas.append({'nombre': nombre, 'ancho': w, 'alto': h, 'a': (pa or {}).get(clave, 0), 'b': (pb or {}).get(clave, 0)})
    graficos = []
    for titulo, campo, unidad in [('Material necesario', 'material', 'm²'), ('Costo estimado', 'costo', 'CLP')]:
        valores = [ma[campo], mb[campo]]
        if all(v is not None and v >= 0 for v in valores):
            maximo = max(valores)
            graficos.append({'titulo': titulo, 'unidad': unidad, 'barras': [
                {'alternativa': letra, 'valor': valor, 'ancho': int(valor / maximo * 100) if maximo else 0}
                for letra, valor in zip(('A', 'B'), valores)]})
    return {'equivalentes': equivalentes, 'motivo': motivo, 'a': ma, 'b': mb,
            'diferencia_area': diferencia_area, 'diferencia_costo': diferencia_costo,
            'conclusiones': conclusiones, 'cambios': cambios, 'piezas': filas, 'graficos': graficos}
