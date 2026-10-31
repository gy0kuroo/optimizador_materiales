"""Recursos decorativos propios en el HTML inicial, sin peticiones tardías."""
import base64
import io
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from PIL import Image

register = template.Library()
ROOT = Path(__file__).resolve().parents[1] / 'static' / 'cutless'
SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
ALLOWED = {'brand-symbol.svg', 'icons/tablero-outline.svg', 'icons/pieza.svg',
           'icons/pieza-outline.png', 'icons/ancho.svg', 'icons/alto.png',
           'icons/rotacion.svg', 'icons/margen.png', 'icons/sierra-mesa.png',
           'icons/costos.svg', 'icons/tip.svg', 'icons/info.svg'}


@lru_cache(maxsize=None)
def asset_bytes(name):
    if name not in ALLOWED:
        raise template.TemplateSyntaxError('Recurso no permitido para presentación inicial.')
    return (ROOT / name).read_bytes()


@register.simple_tag
def inline_asset(name, css_class='', size=24):
    data = asset_bytes(name)
    if name.endswith('.png'):
        return format_html('<img src="data:image/png;base64,{}" class="{}" width="{}" height="{}" alt="">',
                           png_for_display(name, int(size)), css_class, size, size)
    root = ET.fromstring(data)
    root.attrib.pop('id', None)
    root.set('class', css_class)
    root.set('width', str(size))
    root.set('height', str(size))
    root.set('aria-hidden', 'true')
    root.set('focusable', 'false')
    if name.startswith('icons/'):
        root.set('fill', 'currentColor')
    return mark_safe(ET.tostring(root, encoding='unicode'))


@lru_cache(maxsize=None)
def png_for_display(name, size):
    # Evitar incrustar originales de 512 px en cada fila para un icono de 20 px.
    with Image.open(io.BytesIO(asset_bytes(name))) as image:
        image.thumbnail((size * 2, size * 2), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format='PNG', optimize=True)
    return base64.b64encode(output.getvalue()).decode('ascii')


@lru_cache(maxsize=1)
def button_symbols():
    return {element.attrib['id']: element for element in ET.fromstring((ROOT / 'button-icons.svg').read_bytes())}


@register.simple_tag
def button_icon(name):
    symbol = button_symbols().get(name)
    if symbol is None:
        raise template.TemplateSyntaxError('Icono de acción desconocido.')
    root = ET.Element(f'{{{SVG}}}svg', {
        'class': 'button-icon', 'data-icon': name, 'aria-hidden': 'true', 'focusable': 'false',
        'viewBox': symbol.get('viewBox', '0 0 24 24'), 'width': '18', 'height': '18',
        'fill': 'none', 'stroke': 'currentColor', 'stroke-width': '1.6',
        'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    })
    root.extend(deepcopy(list(symbol)))
    return mark_safe(ET.tostring(root, encoding='unicode'))
