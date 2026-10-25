"""Plano vectorial horizontal compartido con la presentación web, sin recalcular cortes."""
from reportlab.lib.colors import HexColor
from cutless.services.board_presentation import preparar_plano_horizontal


def dibujar_tablero(c, vista, unidad, margen, numero, total, width, height, info=None, codigo=None, nombre=None):
    plano = preparar_plano_horizontal(vista, unidad, margen)
    c.setFillColor(HexColor('#1C1008'))
    c.setFont('Helvetica-Bold', 16)
    c.drawString(40, height - 45, f'{codigo} · Tablero {numero} de {total}' if codigo else f'Tablero {numero} de {total}')
    extra = 20 if nombre else 0
    if nombre:
        texto = nombre
        c.setFont('Helvetica', 11)
        while c.stringWidth(texto, 'Helvetica', 11) > width-80:
            texto = texto[:-2] + '…'
        c.drawString(40, height-65, texto)
    if info:
        c.setFont('Helvetica', 10)
        c.drawString(40, height-65-extra, f"Aprovechamiento: {info.get('porcentaje_uso', 0):.2f}% · Piezas: {info.get('num_piezas', 0)} · Desperdicio: {info.get('desperdicio', 0):.2f} cm²")
    scale = min((width - 100) / plano['ancho'], (height * .44) / plano['alto'])
    left = (width - plano['ancho'] * scale) / 2
    top = height - 100 - extra
    bottom = top - plano['alto'] * scale
    def rect(p, fill):
        c.setFillColor(HexColor(fill))
        c.setStrokeColor(HexColor('#263238'))
        c.setLineWidth(.6)
        c.rect(left+p['x']*scale, top-(p['y']+p['alto'])*scale,
               p['ancho']*scale, p['alto']*scale, fill=1, stroke=1)
    rect(dict(x=0, y=0, ancho=plano['ancho'], alto=plano['alto']), '#F4F3EE')
    c.setFillColor(HexColor('#1C1008'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(width/2, top+18, f"{plano['cota_ancho']:g} {unidad}")
    c.saveState()
    c.translate(left-20, (top+bottom)/2)
    c.rotate(90)
    c.drawCentredString(0, 0, f"{plano['cota_alto']:g} {unidad}")
    c.restoreState()
    c.setStrokeColor(HexColor('#7D6344'))
    c.line(left, top+10, left+plano['ancho']*scale, top+10)
    c.line(left-10, bottom, left-10, top)
    for resto in plano['sobrantes']:
        x = left+resto['x']*scale
        y = top-(resto['y']+resto['alto'])*scale
        w, h = resto['ancho']*scale, resto['alto']*scale
        c.saveState()
        path = c.beginPath(); path.rect(x, y, w, h)
        c.clipPath(path, stroke=0)
        c.setStrokeColor(HexColor('#B7B8AB')); c.setLineWidth(.4)
        for offset in range(-int(h), int(w)+8, 7):
            c.line(x+offset, y, x+offset+h, y+h)
        if resto['mostrar_texto'] and w > 44 and h > 24:
            c.setFillColor(HexColor('#1C1008')); c.setFont('Helvetica', 7)
            c.drawCentredString(x+w/2, y+h/2+3, 'Sobrante')
            c.drawCentredString(x+w/2, y+h/2-7, f"{resto['medida_ancho']:g} × {resto['medida_alto']:g} {unidad}")
        c.restoreState()
    for pieza in plano['piezas']:
        rect(pieza, pieza['color'])
        x, y = left+pieza['cx']*scale, top-pieza['cy']*scale
        detallado = pieza['texto_detallado']
        size = min(11, (pieza['texto'] if detallado else pieza['texto_referencia'])*scale)
        c.setFillColor(HexColor('#1C1008'))
        # En piezas muy pequeñas, la referencia conserva la relación con la tabla.
        c.setFont('Helvetica-Bold', max(4, size))
        c.drawCentredString(x, y+(size if detallado else -size*.3), f"P{pieza['numero']}")
        if detallado:
            c.setFont('Helvetica', size)
            c.drawCentredString(x, y-size*.25, pieza['nombre'])
            c.drawCentredString(x, y-size*1.5, f"{pieza['medida_ancho']:g} × {pieza['medida_alto']:g} {unidad}")
    y = bottom-35
    c.setFont('Helvetica-Bold', 12)
    c.drawString(40, y, 'Detalle de piezas')
    y -= 24
    columns = [40, 78, 260, 390, 460]
    headers = ['Ref.', 'Nombre', f'Medidas ({unidad})', 'Cantidad', 'Área (m²)']
    def encabezado(y):
        c.setFillColor(HexColor('#1C1008')); c.setFont('Helvetica-Bold', 10)
        for x, text in zip(columns, headers): c.drawString(x, y, text)
    encabezado(y)
    for pieza in vista['catalogo']:
        y -= 25
        if y < 60:
            c.showPage(); y = height-55
            encabezado(y); y -= 25
        c.setFillColor(HexColor(pieza['color'])); c.rect(40, y-2, 9, 9, fill=1, stroke=0)
        c.setFillColor(HexColor('#1C1008')); c.setFont('Helvetica', 10)
        from cutless.units import convertir_desde_cm
        values = [f"P{pieza['numero']}", pieza['nombre'],
                  f"{convertir_desde_cm(pieza['ancho'], unidad):g} × {convertir_desde_cm(pieza['alto'], unidad):g}",
                  str(pieza['cantidad']), f"{pieza['ancho']*pieza['alto']*pieza['cantidad']/10000:.3f}"]
        for x, text, limit in zip(columns, values, [30, 170, 120, 60, 80]):
            while c.stringWidth(text, 'Helvetica', 10) > limit and len(text) > 1:
                text = text[:-2] + '…'
            c.drawString(x+(12 if x == 40 else 0), y, text)
