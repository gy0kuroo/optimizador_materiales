"""Medidas habituales y procedencia del material, sin inferir especies por tamaño."""
CATALOGO = (
    ('osb-122x244', 'OSB', 122, 244), ('mdf-122x244', 'MDF', 122, 244),
    ('mdf-183x244', 'MDF', 183, 244), ('melamina-183x244', 'Melamina', 183, 244),
    ('contrachapado', 'Contrachapado', 122, 244), ('tablero-152x244', 'Tablero', 152, 244),
)


def medida_valida(clave, ancho_cm, alto_cm):
    for codigo, nombre, ancho, alto in CATALOGO:
        if codigo == clave and abs(ancho_cm - ancho) <= .01 and abs(alto_cm - alto) <= .01:
            return {'clave': codigo, 'nombre': nombre, 'ancho_cm': ancho, 'alto_cm': alto}
    return None


def descripcion_material(opt):
    if opt.material_id:
        return {'nombre': opt.material.nombre, 'origen': 'Material de biblioteca', 'identidad': ('biblioteca', opt.material_id)}
    extra = opt.resultado_extra if isinstance(opt.resultado_extra, dict) else {}
    medida = medida_valida(extra.get('medida_habitual', ''), opt.ancho_tablero, opt.alto_tablero)
    if medida:
        nombre = medida['nombre']
        return {'nombre': nombre, 'origen': 'Selección estándar; sin ficha ni precio de biblioteca', 'identidad': ('estandar', nombre.casefold())}
    habitual = any(abs(opt.ancho_tablero - w) <= .01 and abs(opt.alto_tablero - h) <= .01 for _, _, w, h in CATALOGO)
    return {'nombre': 'Tablero de medidas habituales' if habitual else 'Tablero de medidas personalizadas',
            'origen': 'Tipo de material no registrado', 'identidad': None}
