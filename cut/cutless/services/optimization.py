import base64
import io
import logging
import os

from django.conf import settings
from django.http import FileResponse
from django.db import transaction
from django.utils import timezone

from .board_presentation import preparar_plano_horizontal

from ..models import Optimizacion, TableroOptimizacion
from ..exports.pdf import generar_pdf
from ..packing import normalizar_info_desperdicio
from ..pieces import parsear_piezas_desde_texto
from ..render import generar_grafico
from ..units import convertir_desde_cm, obtener_factor_area_desde_cm2, obtener_simbolo_area


logger = logging.getLogger(__name__)


def _media_root():
    return os.fspath(settings.MEDIA_ROOT)


def _normalizar_ruta_absoluta(ruta):
    """Convierte rutas relativas (p. ej. pdfs/archivo.pdf) en ruta absoluta bajo MEDIA_ROOT."""
    if not ruta:
        return None
    ruta = os.fspath(ruta)
    if os.path.isabs(ruta):
        return ruta
    ruta = ruta.replace('\\', '/').lstrip('/')
    if ruta.startswith('pdfs/'):
        return os.path.join(_media_root(), ruta.replace('/', os.sep))
    return os.path.join(_media_root(), ruta.replace('/', os.sep))


def _ruta_pdf_en_disco(optimizacion):
    """Devuelve la ruta absoluta del PDF si el archivo existe, o None."""
    candidatos = []

    if optimizacion.pdf:
        candidatos.append(optimizacion.pdf.name)
        try:
            candidatos.append(optimizacion.pdf.path)
        except (ValueError, NotImplementedError):
            pass

    for candidato in candidatos:
        ruta = _normalizar_ruta_absoluta(candidato)
        if ruta and os.path.isfile(ruta):
            return ruta

    return None


def _eliminar_archivos(archivos):
    """Limpieza de archivos reemplazados o creados por una operación fallida."""
    for storage, nombre in archivos:
        if not nombre:
            continue
        try:
            storage.delete(nombre)
        except Exception:
            logger.exception("No se pudo retirar el archivo %s", nombre)


def nombre_descarga_pdf(numero_lista, optimizacion):
    return f"{optimizacion.codigo}.pdf"


def nombre_descarga_png(numero_lista, optimizacion, tablero_num=None):
    suffix = f"_tablero-{tablero_num}" if tablero_num is not None else ''
    return f"{optimizacion.codigo}{suffix}.png"


def nombre_descarga_png_tablero(numero_lista, optimizacion, tablero_num):
    return nombre_descarga_png(numero_lista, optimizacion, tablero_num)


def nombre_descarga_excel(numero_lista, optimizacion):
    return f"{optimizacion.codigo}.xlsx"


def calcular_numero_lista(usuario, optimizacion_id, ordenar_por='fecha_desc'):
    """Compatibilidad con llamadas anteriores: el número ahora es la clave estable.

    La propiedad `codigo` da formato a la referencia visible. La autorización
    continúa en las vistas, que consultan cada registro por su propietario.
    """
    return optimizacion_id



def _imagen_a_base64(file_field):
    if not file_field:
        return None
    try:
        with file_field.open('rb') as archivo:
            return base64.b64encode(archivo.read()).decode('ascii')
    except (FileNotFoundError, OSError, ValueError):
        return None


def _cargar_imagenes_persistidas(optimizacion):
    """Carga imágenes guardadas; devuelve None si falta algún archivo en disco."""
    if not optimizacion.tableros.exists():
        return None
    imagenes = []
    for tablero in optimizacion.tableros.order_by('numero'):
        imagen = _imagen_a_base64(tablero.imagen)
        if not imagen:
            return None
        imagenes.append(imagen)
    return imagenes


def _info_desperdicio_desde_modelo(optimizacion):
    info_tableros = []
    vistas_web = (optimizacion.resultado_extra or {}).get('vistas_web', {})
    for tablero in optimizacion.tableros.order_by('numero'):
        info_tableros.append({
            'numero': tablero.numero,
            'area_usada': tablero.area_usada,
            'desperdicio': tablero.desperdicio,
            'porcentaje_uso': tablero.porcentaje_uso,
            'num_piezas': tablero.num_piezas,
            'vista_web': vistas_web.get(str(tablero.numero)),
        })

    extra = optimizacion.resultado_extra or {}
    return normalizar_info_desperdicio({
        'area_usada_total': optimizacion.area_usada_total or 0,
        'desperdicio_total': optimizacion.desperdicio_total or 0,
        'info_tableros': info_tableros,
        'num_tableros': len(info_tableros),
        'piezas_no_colocadas': extra.get('piezas_no_colocadas', []),
        'num_piezas_solicitadas': extra.get('num_piezas_solicitadas', 0),
        'num_piezas_colocadas': extra.get('num_piezas_colocadas', 0),
    })


def _regenerar_grafico(optimizacion):
    unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    piezas_parseadas = parsear_piezas_desde_texto(optimizacion.piezas, unidad)
    piezas = [(p['ancho_cm'], p['alto_cm'], p['cantidad']) for p in piezas_parseadas]
    nombres = [p['nombre'] for p in piezas_parseadas]
    margen = getattr(optimizacion, 'margen_corte', 0.3)
    if margen is None:
        margen = 0.3
    rotacion = getattr(optimizacion, 'permitir_rotacion', True)

    return generar_grafico(
        piezas,
        optimizacion.ancho_tablero,
        optimizacion.alto_tablero,
        'cm',
        permitir_rotacion=rotacion,
        margen_corte=margen,
        nombres_piezas=nombres or None,
    )


def persistir_resultado_optimizacion(optimizacion, imagenes_base64, info_desperdicio, aprovechamiento, numero_lista=None):
    """Reemplaza el resultado completo; conserva el anterior si la operación falla."""
    info = normalizar_info_desperdicio(info_desperdicio)
    if not imagenes_base64 or len(imagenes_base64) != len(info['info_tableros']):
        raise ValueError("Las imágenes no coinciden con los tableros del resultado.")
    # Las imágenes se validan, pero no se guardan: la geometría es el resultado durable.
    for imagen in imagenes_base64:
        base64.b64decode(imagen, validate=True)
    if any(not datos.get('vista_web') for datos in info['info_tableros']):
        raise ValueError('El resultado requiere las coordenadas de todos los tableros.')
    pk_original = optimizacion.pk
    try:
        with transaction.atomic():
            if pk_original is None:
                optimizacion.save()
                antiguos = []
            else:
                anterior = Optimizacion.objects.select_for_update().get(pk=pk_original)
                antiguos = [(campo.storage, campo.name) for campo in (anterior.imagen, anterior.pdf) if campo]
                antiguos.extend((tb.imagen.storage, tb.imagen.name) for tb in anterior.tableros.all() if tb.imagen)

            tableros = []
            for datos in info['info_tableros']:
                numero = datos['numero']
                tablero = TableroOptimizacion(
                    optimizacion=optimizacion, numero=numero,
                    area_usada=datos.get('area_usada', 0), desperdicio=datos.get('desperdicio', 0),
                    porcentaje_uso=datos.get('porcentaje_uso', 0), num_piezas=datos.get('num_piezas', 0),
                )
                tableros.append(tablero)
            optimizacion.imagen = ''
            optimizacion.pdf = ''
            optimizacion.aprovechamiento_total = aprovechamiento
            optimizacion.area_usada_total = info['area_usada_total']
            optimizacion.desperdicio_total = info['desperdicio_total']
            optimizacion.num_tableros = len(info['info_tableros'])
            optimizacion.resultado_generado = True
            optimizacion.resultado_generado_en = timezone.now()
            optimizacion.resultado_extra = {
                clave: info[clave] for clave in ('piezas_no_colocadas', 'num_piezas_solicitadas', 'num_piezas_colocadas')
            }
            optimizacion.resultado_extra['vistas_web'] = {
                str(tablero['numero']): tablero['vista_web']
                for tablero in info['info_tableros'] if tablero.get('vista_web')
            }
            optimizacion.tableros.all().delete()
            for tablero in tableros:
                tablero.save()
            optimizacion.save()
            transaction.on_commit(lambda: _eliminar_archivos(antiguos))
    except Exception:
        if pk_original is not None:
            optimizacion.refresh_from_db()
        else:
            optimizacion.pk = None
            optimizacion._state.adding = True
            optimizacion.imagen = ''
            optimizacion.pdf = ''
            optimizacion.resultado_generado = False
        raise
    return optimizacion


def obtener_resultado_optimizacion(optimizacion, numero_lista=None, persistir_si_falta=True):
    """
    Devuelve (imagenes_base64, aprovechamiento, info_desperdicio en cm²).
    Renderiza las coordenadas guardadas sin recalcular ni escribir archivos.
    Solo calcula cuando el registro aún no tiene un resultado persistido.
    """
    if optimizacion.resultado_generado and optimizacion.tableros.exists():
        info = _info_desperdicio_desde_modelo(optimizacion)
        if all(tb.get('vista_web') for tb in info['info_tableros']):
            from ..exports.board_png import generar_png_tablero
            imagenes = []
            for tb in info['info_tableros']:
                buffer = generar_png_tablero(tb['vista_web'], optimizacion.unidad_medida or 'cm',
                    optimizacion.margen_corte, tb['numero'], len(info['info_tableros']), tb,
                    codigo=optimizacion.codigo, nombre=optimizacion.nombre)
                imagenes.append(base64.b64encode(buffer.getvalue()).decode('ascii'))
                buffer.close()
            return imagenes, optimizacion.aprovechamiento_total, info
        # Compatibilidad de lectura: no recalcular resultados históricos sin coordenadas.
        imagenes = _cargar_imagenes_persistidas(optimizacion)
        if imagenes is not None:
            return imagenes, optimizacion.aprovechamiento_total, info
        raise ValueError('El resultado guardado no tiene coordenadas ni imágenes disponibles.')

    imagenes, aprovechamiento, info = _regenerar_grafico(optimizacion)
    info = normalizar_info_desperdicio(info)
    if persistir_si_falta and imagenes:
        persistir_resultado_optimizacion(
            optimizacion,
            imagenes,
            info,
            aprovechamiento,
            numero_lista=numero_lista,
        )
    return imagenes, aprovechamiento, info


def convertir_info_desperdicio_unidad(info_desperdicio, unidad, optimizacion=None):
    """Convierte áreas de cm² a la unidad del usuario."""
    info = normalizar_info_desperdicio(
        info_desperdicio,
        area_usada_total=getattr(optimizacion, 'area_usada_total', None) if optimizacion else None,
        desperdicio_total=getattr(optimizacion, 'desperdicio_total', None) if optimizacion else None,
    )
    factor_area = obtener_factor_area_desde_cm2(unidad)
    return {
        **info,
        'area_usada_total': round(info['area_usada_total'] * factor_area, 2),
        'desperdicio_total': round(info['desperdicio_total'] * factor_area, 2),
        'info_tableros': [
            {
                **tablero,
                'area_usada': round(tablero.get('area_usada', 0) * factor_area, 2),
                'desperdicio': round(tablero.get('desperdicio', 0) * factor_area, 2),
            }
            for tablero in info['info_tableros']
        ],
    }


def preparar_contexto_resultado(optimizacion, imagenes_base64, info_desperdicio, piezas_parseadas=None):
    """Construye el contexto de visualización para resultado.html."""
    unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    simbolo_area = obtener_simbolo_area(unidad)

    if piezas_parseadas is None:
        piezas_parseadas = parsear_piezas_desde_texto(optimizacion.piezas, unidad)

    piezas_con_nombre = [
        {
            'nombre': p['nombre'],
            'ancho': p['ancho'],
            'alto': p['alto'],
            'cantidad': p['cantidad'],
        }
        for p in piezas_parseadas
    ]

    info_desperdicio_mostrar = convertir_info_desperdicio_unidad(
        info_desperdicio, unidad, optimizacion,
    )
    info_tableros_convertida = info_desperdicio_mostrar['info_tableros']

    tableros_con_imagenes = []
    for imagen, info in zip(imagenes_base64, info_tableros_convertida):
        vista_web = info.get('vista_web')
        catalogo = []
        if vista_web:
            catalogo = [{**pieza,
                         'ancho': convertir_desde_cm(pieza['ancho'], unidad),
                         'alto': convertir_desde_cm(pieza['alto'], unidad),
                         'area_m2': pieza['ancho'] * pieza['alto'] * pieza['cantidad'] / 10000}
                        for pieza in vista_web['catalogo']]
        tableros_con_imagenes.append({
            'numero': info['numero'],
            'imagen': imagen,
            'info': info,
            'vista_web': vista_web,
            'catalogo': catalogo,
            'plano': preparar_plano_horizontal(vista_web, unidad, optimizacion.margen_corte),
            'desperdicio_porcentaje': max(0, 100 - info.get('porcentaje_uso', 0)),
        })

    num_tableros = len(imagenes_base64)
    precio_tablero = optimizacion.precio_tablero
    mano_obra = optimizacion.mano_obra or 0
    costo_material = None
    if precio_tablero:
        from decimal import Decimal
        costo_material = Decimal(str(num_tableros)) * precio_tablero

    return {
        'optimizacion': optimizacion,
        'imagen': imagenes_base64[0] if imagenes_base64 else None,
        'imagenes': imagenes_base64,
        'num_tableros': num_tableros,
        'piezas_con_nombre': piezas_con_nombre,
        'info_desperdicio': info_desperdicio_mostrar,
        'tableros_con_imagenes': tableros_con_imagenes,
        'unidad_medida': unidad,
        'margen_mm': optimizacion.margen_corte * 10,
        'ancho_tablero_mostrar': convertir_desde_cm(optimizacion.ancho_tablero, unidad),
        'alto_tablero_mostrar': convertir_desde_cm(optimizacion.alto_tablero, unidad),
        'simbolo_area': simbolo_area,
        'costo_total': optimizacion.get_costo_total(),
        'costo_material': costo_material,
        'precio_tablero': precio_tablero,
        'mano_obra': mano_obra,
    }


def pdf_path_para_template(optimizacion):
    """Ruta relativa al MEDIA_ROOT para enlaces /media/..."""
    if _ruta_pdf_en_disco(optimizacion):
        return optimizacion.pdf.name if optimizacion.pdf else None
    return None


def respuesta_pdf_optimizacion(optimizacion, numero_lista=None):
    """Genera el PDF en memoria a partir de la distribución guardada."""
    nombre_descarga = nombre_descarga_pdf(numero_lista, optimizacion)
    # Exportar la presentación actual también para resultados con PDF antiguo.
    # No sustituir los archivos previos ni volver a ejecutar el algoritmo.
    imagenes, _, info = obtener_resultado_optimizacion(optimizacion, numero_lista=numero_lista, persistir_si_falta=False)
    buffer = io.BytesIO()
    generar_pdf(optimizacion, imagenes, numero_lista=numero_lista,
                info_desperdicio=info, archivo_salida=buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=nombre_descarga)


def respuesta_png_tablero(optimizacion, tablero_num, numero_lista=None):
    """Exporta el plano actual, compartido por todas las rutas de descarga PNG."""
    nombre = nombre_descarga_png_tablero(numero_lista, optimizacion, tablero_num)
    imagenes, _, info = obtener_resultado_optimizacion(
        optimizacion, numero_lista=numero_lista, persistir_si_falta=False,
    )
    if tablero_num < 1 or tablero_num > len(imagenes):
        return None
    datos = next((tb for tb in info['info_tableros'] if tb['numero'] == tablero_num), {})
    vista = datos.get('vista_web')
    if vista:
        from ..exports.board_png import generar_png_tablero
        buffer = generar_png_tablero(vista, optimizacion.unidad_medida or 'cm',
            optimizacion.margen_corte, tablero_num, len(imagenes), datos, codigo=optimizacion.codigo, nombre=optimizacion.nombre)
    else:
        # Un registro histórico sin coordenadas solo permite recuperar su imagen.
        buffer = io.BytesIO(base64.b64decode(imagenes[tablero_num-1]))
    return FileResponse(buffer, as_attachment=True, filename=nombre, content_type='image/png')
